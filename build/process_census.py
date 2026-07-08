# Fast, reliable census -> mergeable-entries processor (no LLM classify).
#   python process_census.py <slug> [domain-label]
# Reads a census <slug>.json 'items', aggressively strips noise, dedups vs the
# current DB, assigns type/severity/pattern deterministically, and writes
# build/w_cycle.json ready for merge_wave2.py. Prints a stats line.
import json, re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = r"C:\Users\gamma\mass-search"
DB = os.path.join(ROOT, "ai-cliche-megadb.json")

def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9/ ]", "", str(s).lower())).strip()
def compact(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿]")
def clean(s):
    s = str(s).strip()
    s = EMOJI.sub("", s).strip().strip('"“”‘’\'')
    s = re.sub(r"\s*\((?:overused[^)]*|used[^)]*|vague[^)]*|when [^)]*|metaphor[^)]*|British[^)]*|not specific[^)]*|e\.g\.[^)]*|i\.e\.[^)]*)\)\s*$", "", s, flags=re.I)
    s = s.rstrip(" .…:;,")
    return re.sub(r"\s+", " ", s).strip('"“”‘’\' ')

NAV = set("about blog pricing prices contact overview resources summary home login license contributors post craft nouns adjectives verbs technology science writing marketing sales finance leadership education consulting engineering design innovation economics networking communication productivity career instagram linkedin youtube facebook twitter telegram reddit tiktok pinterest espanol deutsch francais portugues english italiano feature features faq faqs terms privacy cookies newsletter search menu share comments reply follow subscribe download".split())
CRED = re.compile(r"\b(MBA|MSc|PhD|MAPM|CMBE|FHEA|CFA|CPA|Ph\.?D|M\.?D|Esq|BSc|MA|MD)\b")
TENURE = re.compile(r"\b\d+\s*(y|yr|yrs|mo|mos)\b", re.I)
SOCIAL = re.compile(r"\b(followers?|comments?|report this|recommended by|read more|posted by|min read|likes?|shares?|views?)\b", re.I)
URLISH = re.compile(r"(https?://|www\.|@|\.com\b|\.io\b|\.org\b|\.net\b)", re.I)
LISTICLE = re.compile(r"^\d+[\s.):]")
ARTICLE = re.compile(r"^(how|why|what|is|are|does|do|when|where|can|should|could|would|will|top|the best|best|guide to|introducing|meet )\b", re.I)
AUTHORY = re.compile(r"^(Dr\.?\s+|Mr\.?\s+|Ms\.?\s+|Prof\.?\s+)?[A-Z][a-z]+ [A-Z][a-z.]+( [A-Z][a-z.]+)?$")
TITLECASE = re.compile(r"[A-Z]")
PLACE = re.compile(r"[\[\]<>]|\bX\b.{0,30}\bY\b|/")
OPENER_W = {"in","to","let","as","when","with","this","the","it","there","by","before","said","viewed","put","one","every","a","an","from","whether","not","no","imagine","picture","consider","think"}

def is_noise(t):
    if not t or len(t) < 3 or len(t) > 64: return True
    low = norm(t)
    if not low or low in NAV: return True
    if EMOJI.search(t) or URLISH.search(t) or SOCIAL.search(t): return True
    if CRED.search(t) or LISTICLE.match(t): return True
    if TENURE.search(t) and len(t.split()) <= 4: return True
    if AUTHORY.match(t) and not any(w and w[0].islower() for w in t.split()): return True
    is_opener = t.endswith("...") or "…" in t or low.split()[0] in OPENER_W
    if ARTICLE.match(t) and not is_opener and len(t.split()) > 3: return True
    if len(t) > 52 and not PLACE.search(t) and not is_opener: return True
    if len(t.split()) > 9 and not PLACE.search(t): return True
    words = [w for w in t.split() if w]
    # Title-Case heading of 4+ words with no lowercase connective -> page heading
    if len(words) >= 4 and all((w[0].isupper() or not w[0].isalpha()) for w in words) and not PLACE.search(t):
        return True
    if low in {"none","n a","na","tbd","xxx","lorem ipsum","click here","learn more","get started","sign in"}: return True
    return False

def placeholder_to_regex(t):
    """[a/b/c] -> (?:a|b|c); [noun]/<x> -> \\w+; returns (regex, ok)."""
    parts, i, out = [], 0, ""
    tmp = re.sub(r"[\[<]([^\]>]+)[\]>]", lambda m: "\x00" + m.group(1) + "\x01", t)
    def repl(seg):
        if "/" in seg and " " not in seg:      # a/b/c enumeration
            alts = [re.escape(x.strip()) for x in seg.split("/") if x.strip()]
            return "(?:" + "|".join(alts) + ")"
        return r"\w+"                            # [noun] placeholder
    res = ""
    for chunk in re.split(r"\x00|\x01", tmp):
        if chunk in (t,):
            pass
    # simpler: iterate bracketed groups
    res = re.escape(t)
    # unescape our sentinels handling: rebuild from original
    def build(s):
        o = ""
        j = 0
        while j < len(s):
            c = s[j]
            if c in "[<":
                close = "]" if c == "[" else ">"
                k = s.find(close, j)
                if k == -1:
                    o += re.escape(c); j += 1; continue
                o += repl(s[j+1:k]); j = k + 1
            else:
                o += re.escape(c); j += 1
        return o
    rx = build(t)
    rx = rx.replace(r"\ ", r"\s+")
    try:
        re.compile(rx); return rx, True
    except re.error:
        return None, False

def classify(t):
    words = [w for w in t.split() if w]
    if PLACE.search(t):
        rx, ok = placeholder_to_regex(t)
        if ok:
            return "template", "medium", rx
        t2 = re.sub(r"[\[\]<>]", "", t)          # strip brackets -> phrase
        t = re.sub(r"\s+", " ", t2).strip()
        words = t.split()
    low0 = t.lower().split()[0] if words else ""
    if t.endswith("...") or "…" in t or (low0 in OPENER_W and len(words) >= 3):
        return "opener", "medium", None
    if len(words) == 1:
        return "word", "low", None
    return "phrase", ("medium" if len(words) >= 3 else "low"), None

def main(slug, domain=None):
    camp = json.load(open(os.path.join(OUTDIR, slug + ".json"), encoding="utf-8"))
    items = camp.get("items") or []
    domain = domain or slug.replace("every-", "").replace("-", " ")[:40]
    is_lyric = any(w in slug for w in ("lyric", "song", "suno", "udio", "rhyme", "chorus"))
    plats = ["suno", "udio"] if is_lyric else ["general"]

    db = json.load(open(DB, encoding="utf-8-sig"))
    ex_norm, ex_compact = set(), set()
    for e in db["entries"]:
        for part in re.split(r"\s*/\s*", e.get("term", "")):
            part = re.sub(r"\([^)]*\)", "", part)
            ex_norm.add(norm(part)); ex_compact.add(compact(part))

    entries, seen = [], set()
    n_noise = n_dupe = 0
    for it in items:
        raw = it.get("item") if isinstance(it, dict) else it
        term = clean(raw)
        if is_noise(term):
            n_noise += 1; continue
        nk = norm(term)
        if nk in ex_norm or compact(term) in ex_compact:
            n_dupe += 1; continue
        if nk in seen: continue
        seen.add(nk)
        typ, sev, pat = classify(term)
        term2 = re.sub(r"[\[\]<>]", "", term).strip() if typ != "template" else term
        e = {"term": term2, "type": typ, "severity": sev,
             "category": f"{domain} census", "domain": "both",
             "why": f"Overused AI term catalogued from the '{domain}' census sweep (source count {it.get('sources',1) if isinstance(it,dict) else 1}).",
             "example": "", "platforms": plats, "source": f"census:{slug}"}
        if typ == "template":
            e["pattern"] = pat; e["flags"] = "gi"
        entries.append(e)

    json.dump({"result": {"entries": entries}}, open(os.path.join(ROOT, "build", "w_cycle.json"), "w", encoding="utf-8"), ensure_ascii=False)
    by = {}
    for e in entries: by[e["type"]] = by.get(e["type"], 0) + 1
    print(f"[{slug}] items={len(items)} -> entries={len(entries)} (noise={n_noise} dbdupe={n_dupe}) types={by}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
