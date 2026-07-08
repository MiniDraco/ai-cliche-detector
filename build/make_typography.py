# Curated "typography / typing-habit" tells: glyphs and formatting a human typing
# into a plain field (e.g. Suno's lyric box) doesn't produce, but pasted AI text
# carries. Mostly template detectors (regex) so the highlighter actually flags them.
import json, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def T(term, pattern, sev, why, example, flags="gi", cat="typography / typing habit", dom="both", plats=None):
    return {"term": term, "type": "template", "severity": sev, "category": cat, "domain": dom,
            "why": why, "example": example, "platforms": plats or ["general"],
            "pattern": pattern, "flags": flags, "source": "typography-curated"}
def R(term, sev, why, example, typ="trope", cat="typography / typing habit", dom="both"):
    return {"term": term, "type": typ, "severity": sev, "category": cat, "domain": dom,
            "why": why, "example": example, "platforms": ["general"], "source": "typography-curated"}

entries = [
  # ---- glyph detectors: proper typography a raw typist doesn't produce ----
  T("… (ellipsis character, U+2026)", "…", "high",
    "AI/word-processor output uses the single ellipsis glyph; a human typing in a plain field types three periods '...'. Strong tell in lyrics or chat.",
    "waiting in the dark…"),
  T("— (em dash, U+2014)", "—", "medium",
    "AI reaches for the true em dash far more than a human typist, who types '-' or '--'. Em dash present in a plain-text field (lyrics box, comment) is a typography tell.",
    "I wanted to stay — but the road called"),
  T("– (en dash, U+2013)", "–", "medium",
    "AI uses a proper en dash for ranges ('2020–2024'); a human typist types a hyphen. Its presence signals generated/pasted text.",
    "the 2019–2023 era"),
  T("curly double quotes (“ ”, U+201C/D)", "[\\u201C\\u201D]", "high",
    "Smart/curly double quotes appear in AI and word-processor output; a human typing raw types straight quotes \". A near-proof tell in a plain-text field like a lyric box.",
    "he said \\u201cnever again\\u201d"),
  T("curly apostrophe / single quotes (‘ ’, U+2018/9)", "[\\u2018\\u2019]", "high",
    "Smart apostrophes/single quotes ('don\\u2019t') come from AI/word-processors; a raw typist types the straight apostrophe. Strong tell in lyrics and chat.",
    "don\\u2019t look back"),
  T("non-breaking space (U+00A0)", "\\u00A0", "high",
    "A non-breaking space is invisible but only appears in copied HTML / AI output — a human keyboard produces a normal space. Near-proof of paste.",
    "10\\u00A0kg"),
  T("bullet glyph (•, U+2022)", "•", "medium",
    "The bullet character in running text signals AI/markdown list output rather than hand-typed prose.",
    "• first point"),
  T("arrow glyph (→ ← ⇒)", "[\\u2190\\u2192\\u2194\\u21D2\\u21D0]", "medium",
    "AI uses arrow glyphs ('X → Y') where a human types '->' or writes it out. A typography tell.",
    "input → output"),
  T("checkmark / cross glyphs (✓ ✔ ✅ ❌)", "[\\u2713\\u2714\\u2705\\u274C\\u2717]", "high",
    "Check/cross emoji-glyphs in text are an AI list/formatting habit; humans rarely type them inline.",
    "\\u2705 done  \\u274C skipped"),
  T("multiplication sign in dimensions (×)", "\\d\\s*×\\s*\\d", "medium",
    "AI writes dimensions with the true multiplication sign ('1920×1080'); a human types the letter 'x'.",
    "1920×1080"),
  T("primes / smart quotes for feet-inches (′ ″)", "[\\u2032\\u2033]", "medium",
    "AI uses prime glyphs for measurements where a typist uses straight ' and \".",
    "6\\u2032\\u2033 tall"),
  T("trademark/copyright glyphs inline (™ ® ©)", "[\\u2122\\u00AE\\u00A9]", "low",
    "Inline ™/®/© in casual text is a copy-paste / AI formatting habit rather than hand typing.",
    "BrandName\\u2122 is great"),

  # ---- markdown artifacts that survive into a finished piece = pasted from AI ----
  T("markdown bold in body text (**text**)", "\\*\\*[^*\\n]{1,60}\\*\\*", "high",
    "Double-asterisk bold is markdown; if it appears in a finished piece or a plain-text field the author pasted AI output without cleaning the formatting.",
    "This is **really** important"),
  T("markdown bold lead-in with colon (**Word:**)", "\\*\\*[^*\\n]{1,40}:\\*\\*", "high",
    "AI's signature bolded-term-then-colon list item; a strong structural + typography tell.",
    "**Pros:** cheaper and faster"),
  T("markdown header hashes (## Heading)", "^#{1,6}\\s+\\S", "high",
    "Leading # header syntax in body text or a lyric field is un-rendered markdown pasted straight from AI.",
    "## Key Takeaways", "gim"),
  T("inline code backticks (`code`)", "`[^`\\n]{1,40}`", "medium",
    "Backtick inline-code markdown surviving into prose/lyrics signals pasted AI/markdown output.",
    "run `npm install` first"),
  T("markdown horizontal rule (--- / ***)", "^\\s*(?:---|\\*\\*\\*|___)\\s*$", "high",
    "A markdown horizontal-rule line is un-rendered AI formatting pasted verbatim.",
    "---", "gim"),
  T("bracketed placeholder left in (e.g. [Name], [insert])", "\\[(?:name|insert[^\\]]*|your [^\\]]*|company|date|topic|x)\\]", "high",
    "A template placeholder the author forgot to fill — proof the text came from an AI/template, not hand-written.",
    "Dear [Name], thank you for [insert reason]"),

  # ---- described habits (no reliable single-glyph regex) ----
  R("no typos, doubled letters, or keyboard slips", "medium",
    "AI text is free of the transpositions, doubled letters, missed spaces and autocorrect artifacts a human typist produces over any real length. Flawlessness itself is a soft tell.",
    "A 300-word passage with zero typos, homophone errors, or stray keystrokes."),
  R("internally consistent straight-OR-curly quotes (never mixed)", "low",
    "AI is perfectly consistent (all curly or all straight); humans mix straight and curly quotes within one text, especially when editing.",
    "Every quote in the piece is curly; not one straight quote slipped in."),
  R("exactly one space after every period", "low",
    "AI never double-spaces after periods and never leaves a stray double space; spacing is machine-perfect.",
    "Uniform single spacing after every sentence, no exceptions."),
  R("perfect capitalization and terminal punctuation", "low",
    "Every sentence starts capitalized and ends with punctuation; no lowercase-i, no missing end marks a casual typist leaves.",
    "No 'i' for 'I', every line properly capped and closed."),
  R("Title Case Headings", "low",
    "AI capitalizes headings in Title Case ('How To Get Started'); casual human writing uses sentence case or lowercase.",
    "How To Improve Your Writing"),
  R("emoji as section bullets or headers", "medium",
    "AI decorates lists/sections with a leading emoji per item ('🚀 Fast', '💡 Smart') — a formatting habit rare in hand-typed prose.",
    "🚀 Speed  💡 Ideas  🔒 Security"),
  R("uniform double-newline paragraph spacing", "low",
    "AI separates every paragraph with an identical blank line; human drafts have irregular spacing.",
    "Every paragraph separated by exactly one blank line throughout."),
  R("straight apostrophe auto-converted in contractions", "medium",
    "Contractions render with the curly apostrophe (don\\u2019t, it\\u2019s) rather than the straight one a raw typist produces.",
    "can\\u2019t, won\\u2019t, they\\u2019re — all curly"),
]

bad = []
for e in entries:
    if e["type"] == "template":
        try: re.compile(e["pattern"])
        except re.error as ex: bad.append((e["term"], str(ex)))
if bad:
    print("BAD REGEX:"); [print(" ", t, m) for t, m in bad]; raise SystemExit(1)

out = os.path.join(ROOT, "build", "wave_typography.json")
json.dump({"result": {"entries": entries}}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
ntpl = sum(1 for e in entries if e["type"] == "template")
print(f"typography entries: {len(entries)} ({ntpl} template detectors, {len(entries)-ntpl} tropes) — all regex compile OK")
print("wrote", out)
