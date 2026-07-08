# Collapse loose duplicates in the full DB: at most ONE entry per compact-normalized
# term (ignoring type). Keeps the most useful survivor (template/pattern > higher
# severity > richer why). Rewrites ai-cliche-megadb.json (the full working copy) and
# updates meta counts. Run before the final sanitize/rebuild.
import json, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "ai-cliche-megadb.json")

def compact(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())
SEV = {"high": 3, "medium": 2, "low": 1}
def score(e):
    return (1 if e.get("pattern") else 0, SEV.get(e.get("severity"), 0), len(e.get("why") or ""))

data = json.load(open(DB, encoding="utf-8-sig"))
E = data["entries"]
# preserve rhyme_pair entries untouched (their "term" is an A/B pair, compact would over-merge)
best = {}
order = []
kept_special = []
for e in E:
    if e.get("type") == "rhyme_pair":
        kept_special.append(e); continue
    k = compact(e.get("term", ""))
    if not k:
        kept_special.append(e); continue
    if k not in best:
        best[k] = e; order.append(k)
    else:
        if score(e) > score(best[k]):
            best[k] = e

collapsed = [best[k] for k in order] + kept_special
removed = len(E) - len(collapsed)
byType = {}
for e in collapsed: byType[e.get("type", "?")] = byType.get(e.get("type", "?"), 0) + 1
data["entries"] = collapsed
if "meta" in data:
    data["meta"]["uniqueCount"] = len(collapsed)
    data["meta"]["byType"] = byType
with open(DB, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("removed loose dupes:", removed)
print("DB entries now     :", len(collapsed))
print("byType             :", json.dumps(byType))
