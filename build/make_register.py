# Curated "AI meta-discourse / speech register" tells: the formal, structured way
# AI frames caveats, transitions, acknowledgments and offers, where a human uses
# casual phrasing for the same intent. Each 'why' names the human equivalent so the
# tools teach the contrast. Phrases <=6 words become live literal matchers; longer
# framings are templates so they still fire.
import json, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def P(term, sev, why, example, typ="phrase", cat="meta-discourse register", plats=None):
    return {"term": term, "type": typ, "severity": sev, "category": cat, "domain": "prose",
            "why": why, "example": example, "platforms": plats or ["general"], "source": "register-curated"}
def T(term, pattern, sev, why, example, flags="gi", cat="meta-discourse register"):
    return {"term": term, "type": "template", "severity": sev, "category": cat, "domain": "prose",
            "why": why, "example": example, "platforms": ["general"], "pattern": pattern, "flags": flags,
            "source": "register-curated"}

entries = [
  # ---- caveat / qualification framing (the give-away class) ----
  P("One caveat worth stating", "high", "AI's formal caveat frame; a human says 'quick heads up' or 'I should mention'.", "One caveat worth stating: results vary."),
  P("A quick caveat", "medium", "Softened AI caveat opener; a human just says 'but' or 'that said'.", "A quick caveat before we start."),
  P("It bears mentioning", "high", "Stiff AI qualifier; a human says 'worth saying' or just states it.", "It bears mentioning that costs rose."),
  P("It bears repeating", "medium", "Formal AI emphasis frame; a human says 'again,' or 'like I said'.", "It bears repeating: back up your data."),
  P("A word of caution", "medium", "AI's cautionary preamble; a human says 'careful though' or 'heads up'.", "A word of caution before you proceed."),
  P("worth flagging", "medium", "AI hedge-flag; a human says 'just so you know' or 'FYI'.", "One thing worth flagging here."),
  P("That's not to say", "medium", "AI's both-sides concession frame; a human says 'but that doesn't mean'.", "That's not to say it's perfect."),
  P("It's worth emphasizing", "medium", "AI emphasis frame; a human says 'the main thing is'.", "It's worth emphasizing this point."),
  P("It's important to remember", "medium", "AI reminder frame; a human says 'just remember' or 'don't forget'.", "It's important to remember the basics."),
  P("For what it's worth", "low", "AI's hedged-opinion frame; common in humans too but AI overuses it to soften.", "For what it's worth, I'd wait."),
  T("one/a caveat: framing", "\\b(?:one|a|another|the one) caveat\\b", "high", "Any 'caveat' framing is a strong AI meta-discourse tell; a casual human rarely labels a caveat as such.", "The one caveat: it needs power."),

  # ---- meta-commentary / self-narration ----
  P("In other words", "medium", "AI restates itself formally; a human says 'basically' or 'so'.", "In other words, it failed."),
  P("To put it another way", "medium", "AI's re-framing device; a human says 'or,' or 'basically'.", "To put it another way, slow down."),
  P("At a high level", "medium", "AI's abstraction frame; a human says 'basically' or 'broadly'.", "At a high level, it works like this."),
  P("Let me be clear", "medium", "AI emphasis opener; a human says 'look,' or 'honestly'.", "Let me be clear about this.", "opener"),
  P("Here's the deal", "medium", "AI's casual-frame attempt; overused as a transition into an explanation.", "Here's the deal with pricing."),
  P("The reality is", "medium", "AI truth-frame; a human says 'honestly' or just states it.", "The reality is it costs more."),
  P("The truth is", "medium", "AI's revelatory frame; a human says 'honestly' or 'look'.", "The truth is nobody knows."),
  T("this raises the question", "\\b(?:which|this|that) raises the question\\b", "medium", "AI's rhetorical pivot; a human just asks the question.", "Which raises the question: why bother?"),
  P("That brings us to", "medium", "AI's guided-tour transition; a human says 'so,' or 'next'.", "That brings us to pricing."),
  P("The key takeaway here", "medium", "AI's summary label; a human just says the point.", "The key takeaway here is simple."),
  P("The key thing to understand", "medium", "AI's teaching frame; a human says 'the main thing is'.", "The key thing to understand is timing."),
  P("The good news is", "low", "AI's balanced good/bad frame; overused as an upbeat pivot.", "The good news is it's fixable."),
  P("The bad news is", "low", "Paired AI pivot with 'the good news is'.", "The bad news is it's slow."),
  T("there are a few things", "\\bthere are (?:a few|several|some|a number of|a couple of) (?:things|factors|reasons|points|considerations)\\b", "medium", "AI's list-preamble; a human just lists them or says 'a couple things'.", "There are a few things to consider."),

  # ---- acknowledgment framing (assistant register) ----
  T("you raise a good/important point", "\\byou (?:raise|make) (?:a|an) (?:good|great|valid|important|fair|excellent) point\\b", "high", "Sycophantic assistant acknowledgment; a human says 'true' or 'fair'.", "You raise a good point about cost."),
  P("That's a fair point", "medium", "AI's validating acknowledgment; a human says 'fair' or 'true'.", "That's a fair point."),
  P("Great catch", "medium", "Assistant-style praise of the reader; rare in ordinary prose.", "Great catch on that bug."),

  # ---- hedged offers / recommendations (AI-formal vs human-casual) ----
  P("You might consider", "medium", "AI's deferential suggestion; a human says 'you could try' or 'maybe'.", "You might consider a smaller size."),
  P("It may be worth", "medium", "AI hedged recommendation; a human says 'might be worth' or 'try'.", "It may be worth checking first."),
  P("One approach would be", "medium", "AI's optioning frame; a human says 'you could' or 'one way'.", "One approach would be to cache it."),
  P("I would recommend", "medium", "Formal AI rec; a human says 'I'd go with' or 'I'd say'.", "I would recommend the annual plan."),
  P("I'd suggest", "low", "Softened AI rec; common but AI-leaning in formal contexts.", "I'd suggest starting small."),
  P("It's generally advisable", "medium", "Stiff AI advice register; a human says 'usually best to'.", "It's generally advisable to test first."),
  P("I'd be happy to", "medium", "Assistant-service register; a human says 'sure' or 'happy to'.", "I'd be happy to walk you through it."),
  T("please do not hesitate to", "\\bplease (?:do not|don'?t) hesitate to\\b", "high", "Boilerplate customer-service AI closer; a human says 'just ask' or 'lmk'.", "Please don't hesitate to reach out."),
  T("should you have any questions", "\\bshould you (?:have|require) any (?:questions|concerns|further)\\b", "high", "Ultra-formal AI service register; a human says 'any questions, ask'.", "Should you have any questions, contact us."),

  # ---- formal-register substitutions (AI form vs casual human) ----
  P("in order to", "low", "AI's padded infinitive; a human just writes 'to'.", "In order to save time, batch it."),
  P("a number of", "low", "AI's vague quantifier; a human says 'some' or 'several'.", "A number of factors apply."),
  P("prior to", "low", "AI's Latinate 'before'; a human says 'before'.", "Prior to launch, we tested."),
  P("in the event that", "medium", "AI's legalistic 'if'; a human says 'if'.", "In the event that it fails, retry."),
  P("at this point in time", "medium", "AI padding for 'now'; a human says 'now' or 'right now'.", "At this point in time, we can't."),
  P("due to the fact that", "medium", "AI padding for 'because'; a human says 'because' or 'since'.", "Due to the fact that it rained, we stopped."),
]

bad = []
for e in entries:
    if e["type"] == "template":
        try: re.compile(e["pattern"])
        except re.error as ex: bad.append((e["term"], str(ex)))
if bad:
    print("BAD REGEX:"); [print(" ", t, m) for t, m in bad]; raise SystemExit(1)

out = os.path.join(ROOT, "build", "wave_register.json")
json.dump({"result": {"entries": entries}}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
byt = {}
for e in entries: byt[e["type"]] = byt.get(e["type"], 0) + 1
print(f"register entries: {len(entries)} {byt} — regex OK")
print("wrote", out)
