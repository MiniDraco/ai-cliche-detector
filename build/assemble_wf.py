# Reusable: turn a research-workflow .output file into build/w_cycle.json for merge.
#   python assemble_wf.py <output-file> [nsfw-out.json]
# Validates template regexes (drops invalid), keeps category (nsfw split optional).
import json, re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(sys.argv[1], encoding="utf-8", errors="replace"))
if "result" in data and isinstance(data["result"], dict) and "kept" in data["result"]:
    data = data["result"]
kept = data.get("kept") or []

ALLOWED = {"word","phrase","opener","closer","template","trope"}; SEV = {"high","medium","low"}
entries, seen, bad = [], set(), 0
for k in kept:
    term = (k.get("term") or "").strip()
    typ, sev = k.get("type"), k.get("severity")
    if not term or len(term) < 3 or typ not in ALLOWED or sev not in SEV: continue
    key = (typ, re.sub(r"\s+", " ", term.lower()))
    if key in seen: continue
    seen.add(key)
    e = {"term": term, "type": typ, "severity": sev,
         "category": (k.get("category") or "research").strip(), "domain": "both",
         "why": (k.get("why") or "").strip(), "example": (k.get("example") or "").strip(),
         "platforms": [str(p).lower() for p in (k.get("platforms") or ["general"]) if p],
         "source": "research"}
    if typ == "template":
        pat = (k.get("pattern") or "").strip()
        if not pat: bad += 1; continue
        try: re.compile(pat)
        except re.error: bad += 1; continue
        e["pattern"] = pat; e["flags"] = "gi"
    entries.append(e)

json.dump({"result": {"entries": entries}}, open(os.path.join(ROOT, "build", "w_cycle.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(f"assembled {len(entries)} (dropped bad-tpl {bad}) from {len(kept)} kept")
