# AI Cliché Detection Suite

**Spot AI-written text and lyrics — offline, on your own machine.** A suite of tools backed by a 2,000+ entry database of AI "tells" (overused words, phrases, rhyme-pairs, tropes, and pattern-detectors), plus an optional local language model for the deep signals.

> Estimators, not proof. These measure style patterns that *correlate* with AI writing — they can't know who wrote anything. Polished or non-native human writing can read high; carefully edited AI can read low. Treat every result as a lead, not a verdict.

---

## ⬇️ Download & run (no setup)

**[➡️ Download the installer from Releases](../../releases/latest)** — run it, and you're done. The local model is **built in**, so even the deep "Binoculars" perplexity signals work out of the box. No Python, no GPU, no internet required.

Don't want to install anything? The tools are plain HTML — you can also just open `apps/complete.html` in any browser (it runs on the database + stylometry; the bundled model only kicks in with the installer).

---

## The tools

Open the app and you get a launcher with:

| Tool | What it does |
|---|---|
| **Complete** | Everything on one paste — verdict, all signals, cliché list, and borrowed-line check, in tabs. The daily driver. |
| **Song Compare** | Paste many songs, tag known `#human` / `#ai` anchors + suspects, and rank everyone against the two bands. |
| **Song Forensics** | Deep provenance of one song: AI-likelihood, paraphrase-proof structure, "vocabulator"/humanizer detection, rewrite/multi-source. |
| **AI Detector** | Transparent multi-signal estimator for prose. Shows every signal it uses. |
| **Cliché Catcher** | Live highlighter + fix suggestions — a writing aid. |
| **Lyric Check** | Flags *borrowed* lines (real songs that read as human) with one-click searches to confirm. |

## What makes it different

- **It shows its work.** Every signal is on the table — cliché density, sentence burstiness, rhyme/meter regularity, image-grounding, and (with the model) Binoculars cross-perplexity. No black-box percentage.
- **Built to survive "humanizers."** The structural and grounding signals don't care if you swap clichés for fancy synonyms — they read the skeleton, not the paint.
- **Catches stolen *and* generated.** Most detectors only flag AI-*generated* text; this also flags *borrowed* lyrics that read as human because they are.

## The database

The full catalog ships in six formats under `exports/` — `.csv`, `.json`, `.db` (SQLite, indexed + a `canonical_tells` view), `.xlsx`, `.txt`, and a printable `.pdf`. Sources include a large research sweep, Wikipedia's *Signs of AI writing*, the EQ-Bench antislop list, and per-platform fingerprints.

## Build from source

```
# the web tools regenerate from the database:
build/build_db.ps1        # re-emit CSV + Markdown
build/build_notepad.ps1   # inject the DB into the apps
# the desktop app:
cd desktop && npm install && npm start          # run
cd desktop && npm install && npm run dist       # build the installer
```

## License

MIT.
