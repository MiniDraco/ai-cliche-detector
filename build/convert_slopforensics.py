# Convert sam-paech/slop-forensics data into DB entries -> build/wave2_sf.json
# - canonical cross-model lists (words/bigrams/trigrams) -> platforms ['shared']
# - per-model profiles (38 creative + 10 essay models) -> DISTINCTIVE terms tagged to that model
#   (terms shared across many models are skipped per-model; the canonical list covers them)
import json, os, re, collections

B = os.path.dirname(os.path.abspath(__file__))
def load(n): return json.load(open(os.path.join(B, n), encoding='utf-8'))

STOP = set('''the a an and or but of to in on at for with is am are was were be been being it its it's this that these
those as so if then than out up down off over under into from by no not all any some just now here there when where
what who how why can could would should may might must will shall do does did done have has had having i you he she
we they me him her them my your his their our us said say says asked was were like felt feel felt look looked'''.split())
BAD_WORD = STOP | {'chapter','story','writing','character','narrator'}

def okword(w):
    w = w.lower().strip()
    return len(w) >= 4 and w not in BAD_WORD and re.fullmatch(r"[a-z][a-z'\-]+", w or '') is not None

def fam(model):
    m = model.lower()
    tags = []
    short = m.split('/')[-1]
    tags.append(short)
    if 'claude' in m: tags.append('claude')
    if 'gpt' in m or 'chatgpt' in m or 'openai/' in m: tags.append('chatgpt')
    if 'gemini' in m or 'gemma' in m or 'google/' in m: tags.append('gemini' if 'gemini' in m else 'gemma')
    if 'llama' in m: tags.append('llama')
    if 'mistral' in m: tags.append('mistral')
    if 'deepseek' in m: tags.append('deepseek')
    if 'qwen' in m or 'qwq' in m: tags.append('qwen')
    if 'grok' in m or 'x-ai' in m: tags.append('grok')
    if 'glm' in m or 'z-ai' in m: tags.append('glm')
    if 'command' in m or 'cohere' in m: tags.append('command-r')
    if 'reka' in m: tags.append('reka')
    if 'liquid' in m or 'lfm' in m: tags.append('liquid')
    if any(x in m for x in ('darkest-muse','ifable','starshine','glitter')): tags.append('rp-finetunes')
    return sorted(set(tags))

entries = []
seen = set()
def add(term, typ, cat, plats, why, sev, domain='both'):
    k = typ + '|' + re.sub(r'\s+',' ', re.sub(r"[^a-z0-9/ ]",'', term.lower())).strip()
    if not k.split('|')[1] or k in seen: return
    seen.add(k)
    entries.append({'term': term, 'type': typ, 'category': cat, 'domain': domain,
                    'platforms': plats, 'why': why, 'severity': sev, 'source': 'wave2:slop-forensics'})

# ---------- canonical cross-model lists ----------
for w_ in load('sf_slop_list.json'):
    w = w_[0] if isinstance(w_, list) else w_
    if okword(w):
        add(w, 'word', 'slop-forensics canonical', ['shared'],
            'Over-represented across many LLMs vs human baseline (slop-forensics canonical word list).', 'medium')
canon_bi = [x[0] if isinstance(x, list) else x for x in load('sf_slop_list_bigrams.json')]
canon_tri = [x[0] if isinstance(x, list) else x for x in load('sf_slop_list_trigrams.json')]
for ph in canon_bi + canon_tri:
    if all(t not in STOP for t in ph.split()) or len(ph.split()) > 2:
        add(ph, 'phrase', 'slop-forensics collocation', ['shared'],
            'Cross-model repetitive collocation (slop-forensics; stopwords stripped — words may appear with function words between).', 'low')

# ---------- per-model profiles ----------
profiles = {}
cre = load('sf_creative_profiles.json')
for model, p in cre.items(): profiles[model] = p
for f in os.listdir(B):
    if f.startswith('sf_essay__') and f.endswith('.json'):
        model = f[len('sf_essay__'):-len('.json')].replace('__','/')
        try:
            d = load(f)
            profiles[model] = d.get('slop_profile', d) if isinstance(d, dict) else {}
        except Exception: pass

# count how many models feature each word in their top-200 (to find DISTINCTIVE vs shared)
word_models = collections.Counter()
per_model_top = {}
for model, p in profiles.items():
    tw = p.get('top_repetitive_words') or []
    tops = [(x.get('word'), x.get('score', 0)) for x in tw if isinstance(x, dict)][:200]
    per_model_top[model] = tops
    for w, _ in tops:
        if w: word_models[w.lower()] += 1

N = max(1, len(profiles))
for model, tops in per_model_top.items():
    plats = fam(model)
    short = model.split('/')[-1]
    kept = 0
    for w, score in tops:
        if kept >= 25: break
        if not w or not okword(w): continue
        share = word_models[w.lower()]
        if share >= 6:   # shared slop — canonical list territory, don't tag per-model
            continue
        sev = 'high' if score >= 500 and share <= 2 else 'medium'
        add(w, 'word', 'model-distinctive slop', plats,
            f'Statistically over-represented in {short} output vs human baseline (slop-forensics profile, score {int(score)}; appears in {share}/{N} model top-lists).',
            sev)
        kept += 1
    # per-model bigrams/trigrams (verbatim-looking only: all content words)
    for key, cap in (('top_bigrams', 12), ('top_trigrams', 8)):
        kept2 = 0
        for x in (profiles[model].get(key) or []):
            if kept2 >= cap: break
            ph = (x.get('ngram') or x.get('bigram') or x.get('trigram') or x.get('word') or '') if isinstance(x, dict) else str(x[0] if isinstance(x, list) else x)
            ph = ph.strip().lower()
            toks = ph.split()
            if len(toks) < 2 or any(t in STOP for t in toks): continue
            add(ph, 'phrase', 'model-distinctive collocation', plats,
                f'Top repetitive n-gram in {short} output (slop-forensics).', 'low')
            kept2 += 1

out = os.path.join(B, 'wave2_sf.json')
json.dump({'entries': entries}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
by = collections.Counter(e['type'] for e in entries)
print('models profiled:', len(profiles))
print('entries emitted:', len(entries), dict(by))
