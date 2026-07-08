# Generic per-cycle processor for the 20k push.
#   python process_campaign.py <slug>
# Reads a mass_search campaign (census OR deep-read), pulls candidate tell strings
# from whichever fields exist (items / facts / records[].digest.facts), applies the
# deterministic noise-strip + DB-dedup, and appends unique candidates to a running
# pool at build/pool_candidates.json (so several campaigns accumulate before a
# classify pass). Prints a stats line.
import json, re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = r"C:\Users\gamma\mass-search"
DB = os.path.join(ROOT, "ai-cliche-megadb.json")
POOL = os.path.join(ROOT, "build", "pool_candidates.json")

def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9/ ]", "", str(s).lower())).strip()
def compact(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿]")
def clean(s):
    s = str(s).strip()
    s = EMOJI.sub("", s).strip()
    s = s.strip('"“”‘’\'')
    s = re.sub(r"\s*\((?:overused[^)]*|used without[^)]*|vague[^)]*|when [^)]*|metaphoric[^)]*|British[^)]*|not specific[^)]*|e\.g\.[^)]*)\)\s*$", "", s, flags=re.I)
    s = s.rstrip(" .…")
    return re.sub(r"\s+", " ", s).strip('"“”‘’\' ')

NAV = set("about blog pricing prices contact overview resources summary home login license contributors post craft nouns technology science writing marketing sales finance leadership education consulting engineering design innovation economics networking communication productivity career instagram linkedin youtube facebook twitter telegram reddit espanol deutsch francais portugues english feature".split())
CRED = re.compile(r"\b(MBA|MSc|PhD|MAPM|CMBE|FHEA|CFA|CPA|Ph\.?D|M\.?D|Esq)\b")
TENURE = re.compile(r"\b\d+\s*(y|yr|mo)\b", re.I)
SOCIAL = re.compile(r"\b(followers?|comments?|report this|recommended by|read more|subscribe|sign up|log in)\b", re.I)
URLISH = re.compile(r"(https?://|www\.|@|\.com\b|\.io\b|\.org\b)", re.I)
LISTICLE = re.compile(r"^\d+[\s.)]")
ARTICLE = re.compile(r"^(how|why|what|is|are|does|do|when|where|can|should|top|the best|\d+\s+\w+)\b", re.I)
AUTHORY = re.compile(r"^(Dr\.?\s+)?[A-Z][a-z]+ [A-Z][a-z.]+( [A-Z][a-z.]+)?$")
PLACEHOLDER = re.compile(r"\[[^\]]+\]|<[^>]+>|\bX\b.*\bY\b|/")

def is_noise(t):
    if not t or len(t) < 3 or len(t) > 70: return True
    low = norm(t)
    if low in NAV: return True
    if EMOJI.search(t) or URLISH.search(t) or SOCIAL.search(t): return True
    if CRED.search(t) or LISTICLE.match(t): return True
    if TENURE.search(t) and len(t.split()) <= 4: return True
    if AUTHORY.match(t) and not any(w[0].islower() for w in t.split() if w): return True
    is_opener = t.endswith("...") or "…" in t or low.split()[0] in {
        "in","to","let","as","when","with","this","the","it","there","by","before","said","viewed","put","one","every","a","an","from","whether","not","no"}
    if ARTICLE.match(t) and not is_opener and len(t.split()) > 3: return True
    if len(t) > 55 and not PLACEHOLDER.search(t) and not is_opener: return True
    if len(t.split()) > 10 and not PLACEHOLDER.search(t): return True
    words = t.split()
    if len(words) >= 5 and all((w[0].isupper() or not w[0].isalpha()) for w in words if w) and not PLACEHOLDER.search(t):
        return True
    return False

def gather_strings(camp):
    """Pull candidate strings from any campaign shape."""
    out = []
    for it in (camp.get("items") or []):
        if isinstance(it, dict) and it.get("item"): out.append(it["item"])
        elif isinstance(it, str): out.append(it)
    # deep-read / normal campaigns: facts are the verbatim list items or distilled facts
    for f in (camp.get("facts") or []):
        if isinstance(f, dict) and f.get("fact"): out.append(f["fact"])
        elif isinstance(f, str): out.append(f)
    for rec in (camp.get("records") or []):
        d = rec.get("digest") or {}
        for f in (d.get("facts") or []):
            if f: out.append(str(f))
    return out

def main(slug):
    camp = json.load(open(os.path.join(OUTDIR, slug + ".json"), encoding="utf-8"))
    strings = gather_strings(camp)

    db = json.load(open(DB, encoding="utf-8-sig"))
    ex_norm, ex_compact = set(), set()
    for e in db["entries"]:
        for part in re.split(r"\s*/\s*", e.get("term", "")):
            part = re.sub(r"\([^)]*\)", "", part)
            ex_norm.add(norm(part)); ex_compact.add(compact(part))

    pool = []
    if os.path.exists(POOL):
        pool = json.load(open(POOL, encoding="utf-8"))
    seen = {norm(c["term"]) for c in pool}

    added = n_noise = n_dupe = 0
    for raw in strings:
        term = clean(raw)
        if not term or len(term) < 3:
            continue
        # a "fact" may be a whole sentence -> only keep short, tell-shaped strings
        if len(term.split()) > 9 and not PLACEHOLDER.search(term):
            continue
        if is_noise(term):
            n_noise += 1; continue
        nk = norm(term)
        if nk in ex_norm or compact(term) in ex_compact:
            n_dupe += 1; continue
        if nk in seen:
            continue
        seen.add(nk)
        pool.append({"term": term, "slug": slug})
        added += 1

    json.dump(pool, open(POOL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[{slug}] strings={len(strings)} +added={added} noise={n_noise} dbdupe={n_dupe} | POOL now={len(pool)}")

if __name__ == "__main__":
    main(sys.argv[1])
