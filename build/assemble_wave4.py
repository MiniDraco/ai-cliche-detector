# Phase C: turn the classification workflow output into a mergeable wave4 file.
import json, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = r"C:\Temp\claude\D--Users-gamma-Documents-Claude-Projects\f357cf07-6fc5-4cbf-9a97-7f389abe814c\tasks\w8d2kdya9.output"

raw = open(OUTPUT, encoding="utf-8", errors="replace").read().strip()
try:
    data = json.loads(raw)
except Exception:
    i, j = raw.find("{"), raw.rfind("}")
    data = json.loads(raw[i:j + 1])

if "result" in data and isinstance(data["result"], dict) and "kept" in data["result"]:
    data = data["result"]
kept = data.get("kept") or []
print("workflow kept:", len(kept), "| byType:", data.get("byType"))

ALLOWED = {"word", "phrase", "opener", "closer", "template", "trope"}
SEV = {"high", "medium", "low"}
entries, bad_tpl, dropped = [], 0, 0
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
    e = {
        "term": term, "type": typ, "severity": sev,
        "category": (k.get("category") or "census").strip(),
        "domain": "both",
        "why": (k.get("why") or "").strip(),
        "example": (k.get("example") or "").strip(),
        "platforms": [str(p).lower() for p in (k.get("platforms") or ["general"]) if p],
        "source": "wave4-census",
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

print("valid entries        :", len(entries))
print("dropped invalid/dupe :", dropped)
print("dropped bad templates:", bad_tpl)
by = {}
for e in entries:
    by[e["type"]] = by.get(e["type"], 0) + 1
print("by type              :", by)

out = os.path.join(ROOT, "build", "wave4_census.json")
json.dump({"result": {"entries": entries}}, open(out, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("wrote", out)
