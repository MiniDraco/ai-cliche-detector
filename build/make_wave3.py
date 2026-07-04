# Author + validate the wave-3 curated tells, then emit build/wave3_curated.json
# Sources: mass_search campaigns -> Wikipedia "Signs of AI writing", the ammil.industries
# Vale ruleset, and 2025-2026 detector-vendor word blacklists. All entries are SFW.
import json, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

entries = [
  # ---- A. ChatGPT web-tool citation PASTE artifacts (near-proof of pasted raw output) ----
  {"term": "contentReference[oaicite] citation artifact", "type": "template",
   "category": "paste artifact", "domain": "both", "severity": "high",
   "pattern": r"contentReference\[oaicite:\d+\]|\[oaicite:\d+\]", "flags": "gi",
   "why": "ChatGPT web-search leaves a 'contentReference[oaicite:N]{index=N}' citation stub in its answer; if it survives into pasted text it is near-proof the passage was copied straight out of ChatGPT unedited.",
   "example": "The market grew 40% :contentReference[oaicite:3]{index=3}.",
   "platforms": ["chatgpt"], "source": "wave3-vale"},

  {"term": "ChatGPT turn0search / turn0news citation token", "type": "template",
   "category": "paste artifact", "domain": "both", "severity": "high",
   "pattern": r"\bturn\d+(?:search|news|view|forecast|image|academia|finance|product)\d+\b", "flags": "gi",
   "why": "Internal source IDs (turn0search1, turn0news5) that ChatGPT's browsing tool emits around citations. They are meaningless to a reader and only appear when raw browsing output is pasted verbatim.",
   "example": "according to recent reports turn0search2 the figure is higher",
   "platforms": ["chatgpt"], "source": "wave3-vale"},

  # ---- B. Knowledge-cutoff / model-voice temporal leaks (near-proof unedited LLM) ----
  {"term": "knowledge-cutoff self-reference", "type": "template",
   "category": "assistant voice leak", "domain": "prose", "severity": "high",
   "pattern": r"\b(?:as of|up to|until) my (?:last )?(?:knowledge|training) (?:update|cutoff|cut-?off)\b|my (?:knowledge|training) (?:cutoff|cut-?off|data) (?:is|goes|extends|only goes|was last|ends)", "flags": "gi",
   "why": "The model narrating its own training boundary ('as of my last knowledge update', 'my training data goes up to ...'). A human author has no knowledge cutoff; this is an unedited assistant voice leaking through.",
   "example": "As of my last knowledge update in early 2023, the policy had not changed.",
   "platforms": ["chatgpt", "claude", "gemini"], "source": "wave3-vale"},

  {"term": "no real-time / cannot browse disclaimer", "type": "template",
   "category": "assistant voice leak", "domain": "prose", "severity": "high",
   "pattern": r"\bI (?:do not|don'?t) have (?:access to )?real-?time\b|\bI (?:cannot|can'?t) (?:browse|access) the internet\b", "flags": "gi",
   "why": "Assistant hedge about lacking live data or web access. Never something a human writer says about their own article; a direct leak of the chatbot persona.",
   "example": "I don't have access to real-time data, but as of my last update...",
   "platforms": ["chatgpt", "claude", "gemini"], "source": "wave3-vale"},

  {"term": "as a large language model", "type": "phrase",
   "category": "assistant voice leak", "domain": "prose", "severity": "high",
   "why": "Self-identification as an LLM. Alongside 'As an AI language model', the single most unambiguous tell of unedited chatbot output.",
   "example": "As a large language model, I can help you draft this.",
   "platforms": ["chatgpt", "claude", "gemini"], "source": "wave3-vale"},

  {"term": "Here is the revised / rewritten version", "type": "template",
   "category": "assistant voice leak", "domain": "prose", "severity": "high",
   "pattern": r"\bhere(?:\s|')?s? (?:is|are) the (?:revised|rewritten|updated|polished|improved) (?:version|text|draft|paragraph|copy)\b", "flags": "gi",
   "why": "Editing-handoff preamble the model prepends when returning a rewrite. If it appears in a finished piece, the author pasted the assistant's wrapper along with the content.",
   "example": "Here is the revised version of your introduction:",
   "platforms": ["chatgpt", "claude", "gemini"], "source": "wave3-vale"},

  # ---- C. Structural / editorializing formulas (Wikipedia: Signs of AI writing) ----
  {"term": "formulaic AI section headers", "type": "template",
   "category": "prose structure", "domain": "prose", "severity": "medium",
   "pattern": r"^\s{0,3}#{0,4}\s*(?:Future Outlook|Challenges and Legacy|Key Takeaways|Final Thoughts|In Summary|Conclusion and Next Steps|The Road Ahead)\s*:?\s*$", "flags": "gim",
   "why": "Wikipedia documents these boilerplate section titles as an AI structural tell; the model resolves any topic into the same optimistic outline scaffolding.",
   "example": "## Future Outlook",
   "platforms": ["chatgpt", "gemini", "claude"], "source": "wave3-wikipedia"},

  {"term": "summarizing present-participle tail", "type": "template",
   "category": "prose structure", "domain": "prose", "severity": "medium",
   "pattern": r",\s+(?:highlighting|underscoring|emphasizing|showcasing|reflecting|symbolizing|ensuring|cementing|solidifying|reinforcing|paving the way|shaping|marking)\b[^.?!\n]{0,70}[.?!]", "flags": "gi",
   "why": "Wikipedia's 'present participle endings' tell: the real clause is followed by a floating '-ing' summary that editorializes its own significance ('..., underscoring the importance of ...'). A hallmark of generated wrap-up prose.",
   "example": "The bridge opened in 1932, cementing the city as a regional hub.",
   "platforms": ["chatgpt", "gemini", "claude"], "source": "wave3-wikipedia"},

  {"term": "leaves an indelible mark", "type": "phrase",
   "category": "editorializing", "domain": "both", "severity": "medium",
   "why": "Wikipedia-listed puffery closer: something 'leaves an indelible mark' on something else. Vague significance-assertion with no concrete detail.",
   "example": "Her work left an indelible mark on the genre.",
   "platforms": ["chatgpt", "gemini", "claude"], "source": "wave3-wikipedia"},

  {"term": "beacon of hope", "type": "phrase",
   "category": "prestige metaphor", "domain": "both", "severity": "medium",
   "why": "Decorative prestige-metaphor collocation ('a beacon of hope/innovation'). Near-poetic register that reads as generated filler in neutral prose.",
   "example": "The clinic became a beacon of hope for the community.",
   "platforms": ["chatgpt", "gemini", "claude"], "source": "wave3-wikipedia"},

  # ---- D. Newer 2025-2026 detector-blacklist terms not yet in DB ----
  {"term": "demystify", "type": "word",
   "category": "intro verb", "domain": "prose", "severity": "low",
   "why": "2026 detector-blacklist intro verb ('let us demystify X'). A packaging word the model reaches for to frame explainer content.",
   "example": "In this guide we demystify tax brackets.",
   "platforms": ["chatgpt", "gemini"], "source": "wave3-detectorlists"},

  {"term": "paradigm shift", "type": "phrase",
   "category": "buzzword", "domain": "prose", "severity": "medium",
   "why": "Corporate-hype collocation on every 2025-2026 AI-word blacklist; the model overstates ordinary change as a 'paradigm shift'.",
   "example": "This represents a paradigm shift in how we work.",
   "platforms": ["chatgpt", "gemini"], "source": "wave3-detectorlists"},
]

# --- validate every template regex compiles (Python) ---
bad = []
for e in entries:
    if e["type"] == "template":
        try:
            re.compile(e["pattern"])
        except re.error as ex:
            bad.append((e["term"], str(ex)))
if bad:
    print("BAD REGEX:")
    for t, m in bad:
        print("  ", t, "->", m)
    raise SystemExit(1)

ntpl = sum(1 for e in entries if e["type"] == "template")
print("all", ntpl, "template regexes compile OK")
print("total wave3 entries:", len(entries))

out = {"result": {"entries": entries}}
p = os.path.join(ROOT, "build", "wave3_curated.json")
with open(p, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("wrote", p)
