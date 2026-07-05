# Phase A: pre-filter the exhaustive census (2755 mentions) down to candidate NEW tells.
# Conservative noise-strip + dedupe vs the current DB. Ambiguous items are KEPT for
# the LLM classification stage (better to over-keep here than drop a real tell).
import json, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = r"C:\Users\gamma\mass-search\the-complete-master-list-of-every-word-phrase-op.json"
DB = os.path.join(ROOT, "ai-cliche-megadb.json")

def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9/ ]", "", str(s).lower())).strip()
def compact(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

# ---- clean a raw census 'item' string to a bare term ----------------------
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿←-⇿⬀-⯿]")
def clean(s):
    s = s.strip()
    s = EMOJI.sub("", s).strip()
    s = s.strip('"“”‘’\'')           # surrounding quotes (straight/curly)
    s = re.sub(r"\s*\((?:overused[^)]*|used without[^)]*|vague[^)]*|when [^)]*|metaphoric[^)]*|British[^)]*|not specific[^)]*)\)\s*$", "", s, flags=re.I)
    s = s.rstrip(" .…")                              # trailing dots / ellipsis
    s = re.sub(r"\s+", " ", s).strip('"“”‘’\' ')
    return s.strip()

# ---- high-confidence NOISE (drop) -----------------------------------------
NAV = {"about","blog","pricing","prices","contact","overview","resources","summary",
 "home","login","sign up","get started","license","contributors","related pages",
 "recommended for you","others also viewed","your cart","your cart is empty","section name",
 "featured work","careers","post","how to cite","related pages","related rubric metrics",
 "instagram","linkedin","youtube","x.com","x-twitter","twitter","facebook","telegram","reddit",
 "espanol","deutsch","francais","portugues","english","english english","pricing","feature",
 "best for","privacy-first","overview","technology","user experience","science","writing",
 "marketing","sales","finance","leadership","education","consulting","engineering","design",
 "innovation","economics","networking","negotiation","communication","productivity","career",
 "recruitment hr","customer experience","real estate","ecommerce","retail merchandising",
 "supply chain management","future of work","employee experience","workplace trends",
 "fundraising","project management","organizational culture","event planning","artificial intelligence",
 "training development","business strategy","hospitality tourism","change management","corporate social responsibility",
 "soft skills emotional intelligence","summarize with ai","resources","craft","nouns","adjectives and adverbs",
 "empty action verbs","buzzword descriptors","action constructions","sentence shells","overview",
 "the full rubric","sub-criteria","example score","common failure mode","what good looks like",
 "detection details","structural architecture","the structural test","ai detection","summary",
 "how to check your writing","how to cite","contact","license","contributors","none","none.",
 "you dream it","get our weekly ai digest","chatgpt","gptzero","seo","saas","ai detection algorithms",
 "reddit","r/sunoai","r/udio","r/sillytavernai","r/localllama","ai detection","overview"}

CRED = re.compile(r"\b(MBA|MSc|PhD|MAPM|CMBE|FHEA|CFA|CPA|Ph\.?D|M\.?D|Esq)\b")
TENURE = re.compile(r"\b\d+\s*(y|yr|mo)\b", re.I)
SOCIAL_META = re.compile(r"\b(followers?|comments?|report this|recommended by)\b", re.I)
URLISH = re.compile(r"(https?://|www\.|@|\.com\b|\.io\b|\.org\b)", re.I)
LISTICLE = re.compile(r"^\d+[\s.)]")                      # "10 AI-Powered Remote Jobs..."
AUTHORY = re.compile(r"^[A-Z][a-z]+ [A-Z][a-z.]+( [A-Z][a-z.]+)?$")  # "Dr. Sarah Chen" / "Harry Cook"
HAS_PLACEHOLDER = re.compile(r"\[[^\]]+\]|\bX\b.*\bY\b|/")

def is_noise(term):
    t = term.strip()
    if not t or len(t) < 3: return True
    low = norm(t)
    if low in NAV: return True
    if EMOJI.search(term): return True
    if URLISH.search(t): return True
    if SOCIAL_META.search(t): return True
    if TENURE.search(t) and len(t.split()) <= 4: return True
    if CRED.search(t): return True
    if LISTICLE.match(t): return True
    if AUTHORY.match(t) and not any(w[0].islower() for w in t.split()): return True
    # long strings that are not templates/openers -> almost always article titles / UI
    is_opener = t.endswith("...") or "…" in term or low.split()[0] in {
        "in","to","let","as","when","with","this","the","it","there","by","before","said","viewed","put","one"}
    if len(t) > 52 and not HAS_PLACEHOLDER.search(t) and not is_opener: return True
    if len(t.split()) > 9 and not HAS_PLACEHOLDER.search(t): return True   # sentence-length titles
    # pure Title-Case multiword with >4 words and no lowercase connective -> heading/title
    words = t.split()
    if len(words) >= 4 and all(w[0].isupper() or not w[0].isalpha() for w in words) and not HAS_PLACEHOLDER.search(t):
        return True
    return False

# ---- load DB, build dedupe sets -------------------------------------------
db = json.load(open(DB, encoding="utf-8-sig"))
existing_norm, existing_compact = set(), set()
for e in db["entries"]:
    term = e.get("term", "")
    for part in re.split(r"\s*/\s*", term):               # split slash-variants
        part = re.sub(r"\([^)]*\)", "", part)
        existing_norm.add(norm(part))
        existing_compact.add(compact(part))
    existing_norm.add(norm(term)); existing_compact.add(compact(term))

# ---- run ------------------------------------------------------------------
items = json.load(open(CENSUS, encoding="utf-8"))["items"]
cands, seen = [], set()
n_noise = n_dupe = n_blank = 0
for it in items:
    raw = it.get("item", "")
    term = clean(raw)
    if not term or len(term) < 3:
        n_blank += 1; continue
    if is_noise(term):
        n_noise += 1; continue
    nkey = norm(term)
    if nkey in existing_norm or compact(term) in existing_compact:
        n_dupe += 1; continue
    if nkey in seen:
        continue
    seen.add(nkey)
    cands.append({"term": term, "sources": it.get("sources", 1)})

cands.sort(key=lambda c: (-c["sources"], c["term"].lower()))
out = os.path.join(ROOT, "build", "census_candidates.json")
json.dump(cands, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("census items       :", len(items))
print("dropped blank/short:", n_blank)
print("dropped noise      :", n_noise)
print("dropped DB-dupes   :", n_dupe)
print("CANDIDATES (new)   :", len(cands))
print("wrote", out)
print("\n--- sample candidates (highest source-count first) ---")
for c in cands[:40]:
    print(f"  ({c['sources']})  {c['term']}")
