# Merge a wave-2 workflow result file into the canonical DB.
#   usage: python merge_wave2.py <workflow-output-file.json>
# - dedups on type|norm(term) against the existing DB
# - on DUPLICATE: unions the new platform tags into the existing entry (accuracy win:
#   shared tells gain per-model attribution) and upgrades severity if higher
# - on NEW: validates + inserts with source preserved
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'ai-cliche-megadb.json')

ALLOWED_TYPES = {'word','phrase','rhyme_pair','trope','opener','closer','structure','template'}
SEV = {'high','medium','low'}
SEV_RANK = {'high':3,'medium':2,'low':1}
# ultra-common single words that would cause false positives — never admit as bare 'word'
BLOCK = {'key','real','core','important','modern','use','help','also','very','many','new','good','great',
         'like','just','thing','things','world','today','people','make','way','well','best','more'}

def norm(s):
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9/ ]','',str(s).lower())).strip()

def main(path):
    data = json.load(open(DB, encoding='utf-8-sig'))
    entries = data['entries']
    idx = {}
    for e in entries:
        idx[(e.get('type','') + '|' + norm(e.get('term','')))] = e

    wf = json.load(open(path, encoding='utf-8-sig'))
    new = wf.get('result', wf).get('entries', [])

    added = dupes = enriched = skipped = 0
    for e in new:
        term = (e.get('term') or '').strip()
        typ = e.get('type'); sev = e.get('severity')
        if not term or len(term) < 3 or typ not in ALLOWED_TYPES or sev not in SEV:
            skipped += 1; continue
        if typ == 'word' and norm(term) in BLOCK:
            skipped += 1; continue
        plats = sorted({str(p).lower() for p in (e.get('platforms') or []) if p})
        k = typ + '|' + norm(term)
        if k in idx:
            ex = idx[k]; dupes += 1
            old = set(ex.get('platforms') or [])
            merged = sorted(old | set(plats))
            if merged != sorted(old):
                ex['platforms'] = merged; enriched += 1
            if SEV_RANK.get(sev,0) > SEV_RANK.get(ex.get('severity'),0):
                ex['severity'] = sev
            continue
        rec = {
            'term': term, 'type': typ, 'category': e.get('category') or 'wave2',
            'domain': e.get('domain') or 'both', 'platforms': plats or ['shared'],
            'why': (e.get('why') or '').strip(), 'example': e.get('example') or '',
            'severity': sev, 'sources': [e.get('source') or 'wave2'], 'source': e.get('source') or 'wave2',
        }
        if typ == 'template':
            if not e.get('pattern'): skipped += 1; continue
            rec['pattern'] = e['pattern']; rec['flags'] = e.get('flags') or 'gi'
        entries.append(rec); idx[k] = rec; added += 1

    by_type = {}
    for e in entries: by_type[e.get('type','?')] = by_type.get(e.get('type','?'),0)+1
    if 'meta' in data:
        data['meta']['uniqueCount'] = len(entries)
        data['meta']['rawCount'] = data['meta'].get('rawCount', len(entries)) + added
        data['meta']['byType'] = by_type
    data['entries'] = entries
    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('wave2 incoming :', len(new))
    print('added NEW      :', added)
    print('dupes (skipped):', dupes, '| platform-enriched existing:', enriched)
    print('invalid/blocked:', skipped)
    print('DB total now   :', len(entries))

if __name__ == '__main__':
    main(sys.argv[1])
