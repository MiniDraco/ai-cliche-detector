# Turn the research-workflow output into a mergeable wave5 file.
import json, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = r"C:\Temp\claude\D--Users-gamma-Documents-Claude-Projects\f357cf07-6fc5-4cbf-9a97-7f389abe814c\tasks\wtmqen3sq.output"

raw = open(OUTPUT, encoding="utf-8", errors="replace").read().strip()
data = json.loads(raw)
if "result" in data and isinstance(data["result"], dict) and "kept" in data["result"]:
    data = data["result"]
kept = data.get("kept") or []
print("workflow kept:", len(kept), "| byType:", data.get("byType"))

ALLOWED = {"word", "phrase", "opener", "closer", "template", "trope"}
SEV = {"high", "medium", "low"}
entries, bad_tpl, dropped, nsfw_n = [], 0, 0, 0
seen = set()
for k in kept:
    term = (k.get("term") or "").strip()
    typ = k.get("type"); sev = k.get("severity")
    if not term or len(term) < 3 or typ not in ALLOWED or sev not in SEV:
        dropped += 1; continue
    key = (typ, re.sub(r"\s+", " ", term.lower()))
    if key in seen:
        continue
    seen.add(key)
    cat = (k.get("category") or "wave5-research").strip()
    is_nsfw = cat.lower() == "nsfw fiction tell"
    if is_nsfw:
        cat = "nsfw fiction tell"; nsfw_n += 1
    e = {
        "term": term, "type": typ, "severity": sev, "category": cat,
        "domain": "both",
        "why": (k.get("why") or "").strip(),
        "example": (k.get("example") or "").strip(),
        "platforms": [str(p).lower() for p in (k.get("platforms") or ["general"]) if p],
        "source": "wave5-research",
    }
    if typ == "template":
        pat = (k.get("pattern") or "").strip()
        if not pat:
            bad_tpl += 1; continue
        try:
            re.compile(pat)
        except re.error:
            bad_tpl += 1; continue
        e["pattern"] = pat
        e["flags"] = "gi"
    entries.append(e)

by = {}
for e in entries:
    by[e["type"]] = by.get(e["type"], 0) + 1
print("valid entries        :", len(entries), "| nsfw (full-only):", nsfw_n)
print("dropped invalid/dupe :", dropped, "| dropped bad templates:", bad_tpl)
print("by type              :", by)

out = os.path.join(ROOT, "build", "wave5_research.json")
json.dump({"result": {"entries": entries}}, open(out, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("wrote", out)
