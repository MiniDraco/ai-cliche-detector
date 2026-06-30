# Run AFTER the installer is built. Swaps the canonical DB to the sanitized (NSFW-removed)
# version so the public repo's browsable source carries no explicit content.
# The full DB is preserved as ai-cliche-megadb.full.json (gitignored) and lives on inside the exe.
import json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the ai-cliche-db folder
DB = os.path.join(ROOT, 'ai-cliche-megadb.json')
FULL = os.path.join(ROOT, 'ai-cliche-megadb.full.json')

data = json.load(open(DB, encoding='utf-8-sig'))
full = data['entries']

# preserve the full DB locally (for the exe / your own use) if not already backed up
if not os.path.exists(FULL):
    shutil.copy2(DB, FULL)

clean = [e for e in full if e.get('category') != 'nsfw fiction tell']
data['entries'] = clean
if 'meta' in data:
    data['meta']['uniqueCount'] = len(clean)
    data['meta']['note'] = 'Public build: the NSFW-detection category is excluded here; it remains in the local/full build and inside the installer.'

# write WITHOUT a BOM so it is clean UTF-8 for git/other readers
with open(DB, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

print('full :', len(full))
print('clean:', len(clean), '(removed', len(full) - len(clean), 'nsfw)')
print('backed up full ->', os.path.basename(FULL))
print('NOW run: build/build_db.ps1, build/build_notepad.ps1, build/export_all.py  to regenerate clean csv/md/apps/exports')
