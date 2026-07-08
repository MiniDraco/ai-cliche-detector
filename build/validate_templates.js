// Scan the full DB, drop any template whose regex is invalid in a real browser JS
// engine (the apps build these with new RegExp). Rewrites the DB in place and
// updates meta counts. Run before the final rebuild/push.
const fs = require('fs');
const path = require('path');
const DB = path.join(__dirname, '..', 'ai-cliche-megadb.json');

let raw = fs.readFileSync(DB, 'utf8');
if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1); // strip BOM if present
const data = JSON.parse(raw);
const entries = data.entries;

let bad = 0;
const kept = [];
for (const e of entries) {
  if (e.type === 'template') {
    try {
      new RegExp(e.pattern, e.flags || 'gi');
    } catch (err) {
      bad++;
      continue; // drop invalid template
    }
  }
  kept.push(e);
}

const byType = {};
for (const e of kept) byType[e.type] = (byType[e.type] || 0) + 1;
data.entries = kept;
if (data.meta) {
  data.meta.uniqueCount = kept.length;
  data.meta.byType = byType;
}
fs.writeFileSync(DB, JSON.stringify(data, null, 1), 'utf8');
console.log('dropped invalid-JS templates:', bad);
console.log('DB entries now:', kept.length);
console.log('byType:', JSON.stringify(byType));
