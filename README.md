# AI Cliché Detection Suite

**Spot AI-written text and lyrics — offline, on your own machine.** A suite of tools backed by a 22,000+ entry database of AI "tells" — overused words, phrases, rhyme-pairs, tropes, mad-lib pattern-detectors, *typographic* giveaways (the glyphs a human typist doesn't produce), and *meta-discourse* register (how AI frames its own commentary) — plus an optional local language model for the deep signals.

> Estimators, not proof. These measure style patterns that *correlate* with AI writing — they can't know who wrote anything. Polished or non-native human writing can read high; carefully edited AI can read low. Treat every result as a lead, not a verdict.

---

## ▶️ Try it live (no download)

**[Open the live demo →](https://minidraco.github.io/ai-cliche-detector/)** — runs right in your browser on the database + stylometry. Nothing to install. *(The deep local-model signals only run in the desktop download below.)*

## ⬇️ Download the desktop app (model built in)

**[➡️ Download the portable build from Releases](../../releases/latest)** → unzip it anywhere → run **`AI Cliche Detection Suite.exe`**. That's it. The local model is **bundled inside**, so even the deep "Binoculars" perplexity signals work out of the box — **no Python, no GPU, no internet** required.

> It's a *portable* build (a folder you unzip and run), not an installer — so there's nothing to install or uninstall, just unzip and double-click.

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
- **Catches paste artifacts.** Near-proof tells that only appear in un-edited chatbot output — ChatGPT web-citation stubs (`contentReference[oaicite:…]`, `turn0search…`), knowledge-cutoff self-references, and "as a large language model" leaks.
- **More than a wordlist.** Layers a humanizer can't easily strip: *structural* mad-lib templates (`not X, but Y`), *typographic* tells (the `—`, `…`, curly quotes, non-breaking spaces, and stray markdown a human typing into a plain field never makes), and *register* tells (AI frames a caveat as "one caveat worth stating" where a human says "quick heads up"). Especially strong on lyrics typed straight into Suno/Udio.

## The database

The full catalog ships in six formats under `exports/` — `.csv`, `.json`, `.db` (SQLite, indexed + a `canonical_tells` view), `.xlsx`, `.txt`, and a printable `.pdf`. It's built from **~20 multi-domain census sweeps** (marketing, corporate, legal/medical, news, social, real-estate, recipe, fitness, travel, poetry, email/copywriting, and the fantasy/romance/sci-fi/horror/mystery fiction genres), per-model slop-forensics profiles for 44+ models (Claude 3.5/3.7, GPT-3.5→4.5, Gemini, Llama 2→4, DeepSeek V3/R1, Qwen, Grok, GLM, Mistral, Command-A…), a large **Claude-specific set** (filter `platforms: ["claude"]`), Wikipedia's *Signs of AI writing*, the ammil.industries Vale AI-writing ruleset, 2025–2026 detector-vendor blacklists, the EQ-Bench antislop list, and curated **typographic-glyph** and **meta-discourse-register** detectors. Every entry is a distinct term (deduped).

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
