$ErrorActionPreference = 'Stop'
$dir = 'D:\Users\gamma\Documents\Claude\Projects\ai-cliche-db'
$jsonPath = Join-Path $dir 'ai-cliche-megadb.json'
$data = Get-Content -Raw -Path $jsonPath -Encoding UTF8 | ConvertFrom-Json
$entries = [System.Collections.Generic.List[object]]::new()
foreach ($e in $data.entries) { $entries.Add($e) }

# ---- replicate workflow dedup key logic ----
function Norm($s) { (($s.ToString().ToLower() -replace '[^a-z0-9/ ]', '') -replace '\s+', ' ').Trim() }
function KeyOf($type, $term) {
  if ($type -eq 'rhyme_pair') {
    $parts = (Norm $term).Split('/') | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Sort-Object
    return 'rhyme|' + ($parts -join '/')
  }
  return $type + '|' + (Norm $term)
}
$seen = @{}
foreach ($e in $entries) { $seen[(KeyOf $e.type $e.term)] = $true }

$added = [System.Collections.Generic.List[object]]::new()
function Add-Entry($term, $type, $category, $domain, $platforms, $severity, $why, $example) {
  $k = KeyOf $type $term
  if ($seen.ContainsKey($k)) { return }
  $seen[$k] = $true
  $obj = [PSCustomObject]@{
    term = $term; type = $type; category = $category; domain = $domain
    platforms = $platforms; why = $why; example = $example; severity = $severity
    sources = @('compass-research'); source = 'compass-research'
  }
  $added.Add($obj)
}
$LY = @('suno','udio'); $BOTH = @('chatgpt','gemini','suno','udio')

# ===== CATEGORY 1 — Atmospheric / Setting =====
$atmo = @(
  @('neon','word'), @('neon lights','phrase'), @('neon cities','phrase'),
  @('shadows','word'), @('whispers','word'), @('whispering woods','phrase'), @('whispered dreams','phrase'),
  @('echoes','word'), @('echoes of','opener'), @('midnight','word'), @('twilight','word'),
  @('dusk','word'), @('dawn','word'), @('rain','word'), @('city lights','phrase'),
  @('empty streets','phrase'), @('concrete jungle','phrase'), @('smoke','word'), @('haze','word'),
  @('silence','word'), @('pulse','word'), @('glow','word'), @('electric glow','phrase'),
  @('digital glow','phrase'), @('crimson','word'), @('spectral','word')
)
$atmoHigh = 'neon','neon lights','neon cities','shadows','whispers','echoes'
foreach ($a in $atmo) {
  $sev = if ($atmoHigh -contains $a[0]) { 'high' } else { 'medium' }
  Add-Entry $a[0] $a[1] 'atmosphere/setting' 'lyrics' $LY $sev `
    "Named by the Suno community wiki, Verse Nurse and Suno Lyric Checker as a default nocturnal-urban-melancholy tell - the statistical center of pop/electronic lyric training data, so Suno and Udio reach for it constantly." ''
}

# ===== CATEGORY 2 — Abstract / Poetic =====
$abs = @('tapestry','symphony','embers','silhouette','kaleidoscope','eternal','fleeting','timeless',
  'endless','boundless','surrender','intertwined','entwined','hollow','void','grace','embrace','soar',
  'labyrinth','mosaic','beacon','crescendo','ethereal','resonance','testament','realm','delve','intricate','resonate')
$absHigh = 'tapestry','symphony','testament','delve','realm'
foreach ($w in $abs) {
  $sev = if ($absHigh -contains $w) { 'high' } else { 'medium' }
  Add-Entry $w 'word' 'abstract/poetic' 'both' $BOTH $sev `
    "Overlaps the documented ChatGPT/Gemini overused-word lists ('focal words' like delve, tapestry, realm, testament, resonate, symphony, kaleidoscope) and bleeds into 'poetic' AI lyrics; the same statistical-middle preference drives prose and lyrics. 'Tapestry' is the most notorious general AI tell." ''
}

# ===== CATEGORY 3 — Narrative / Action Tropes =====
$tropes = @(
  @('rise above','trope','high'), @('rising from the ashes','trope','high'),
  @('phoenix rising from the ashes','trope','high'), @('igniting the fire of life','phrase','medium'),
  @('breaking chains','trope','high'), @('broken chains','trope','medium'), @('chasing dreams','phrase','high'),
  @('standing tall','phrase','medium'), @('dancing in the dark','phrase','medium'),
  @('dancing in the flames','phrase','medium'), @('dancing in the moonlight','phrase','high'),
  @('shattered dreams','phrase','medium'), @('broken heart','phrase','medium'), @('burning bridges','phrase','medium'),
  @('fading away','phrase','medium'), @('endless night','phrase','medium'), @('holding shields','trope','low'),
  @('never let you go','phrase','high'), @('hold me tight','phrase','medium'), @('together forever','phrase','high'),
  @('you complete me','phrase','high'), @('heart of gold','phrase','medium'), @('burning desire','phrase','high'),
  @('under the stars','phrase','high')
)
foreach ($t in $tropes) {
  Add-Entry $t[0] $t[1] 'narrative/action trope' 'lyrics' $LY $t[2] `
    "Flagged by American Songwriter, songwriting blogs and Suno community discussion as a canonical AI uplift/empowerment trope (the Suno wiki cites 'especially rise above'; American Songwriter cites 'phoenix rising from the ashes')." ''
}

# ===== CATEGORY 4 — Overused Rhyming Pairs =====
function Add-Rhyme($term, $sev, $why) { Add-Entry $term 'rhyme_pair' 'overused rhyme pair' 'lyrics' $LY $sev $why '' }
function Add-Group($csv, $sev, $why) {
  $w = $csv -split ','
  for ($i = 0; $i -lt $w.Count; $i++) {
    for ($j = $i + 1; $j -lt $w.Count; $j++) { Add-Rhyme ($w[$i] + '/' + $w[$j]) $sev $why }
  }
}
$rhyWhy = "Community-circulated 'lazy rhyme' canon (aggregated lore + elemental end-word bank: fire, light, rain, eyes, sky, heart, soul). A dead giveaway when used as the default end-rhyme; prefer slant/internal/unrhymed."
$explicitRhymes = 'light/night','fire/desire','fire/higher','pain/rain','heart/apart','soul/control','eyes/skies','deep/sleep','town/down','all/fall','arms/harm'
foreach ($r in $explicitRhymes) {
  $sev = if ('light/night','fire/desire','pain/rain' -contains $r) { 'high' } else { 'medium' }
  Add-Rhyme $r $sev $rhyWhy
}
Add-Group 'dreams,seams,beams' 'medium' $rhyWhy
Add-Group 'cry,die,high,sky'   'medium' $rhyWhy
Add-Group 'tears,years,fears'  'medium' $rhyWhy
Add-Group 'name,flame,game'    'medium' $rhyWhy
Add-Group 'believe,leave,receive' 'low'  $rhyWhy
Add-Group 'hold,cold,gold'     'medium' $rhyWhy
Add-Group 'free,be,see,me'     'low'    $rhyWhy

# ---- merge + rewrite ----
foreach ($a in $added) { $entries.Add($a) }
$all = $entries.ToArray()
$byType = @{}
foreach ($e in $all) { if ($byType.ContainsKey($e.type)) { $byType[$e.type]++ } else { $byType[$e.type] = 1 } }

$data.meta.uniqueCount = $all.Count
$data.meta.rawCount = $data.meta.rawCount + $added.Count
$data.meta.byType = [PSCustomObject]$byType
$data.meta.builtBy = '26-agent research workflow + dedup/merge + compass-research merge'
$data.entries = $all

($data | ConvertTo-Json -Depth 12) | Out-File -FilePath $jsonPath -Encoding utf8

Write-Output ("candidates considered: " + ($atmo.Count + $abs.Count + $tropes.Count + 100))
Write-Output ("NEW entries added (after dedupe): " + $added.Count)
Write-Output ("DB total now: " + $all.Count)
Write-Output "added breakdown by type:"
$added | Group-Object type | Sort-Object Count -Descending | ForEach-Object { Write-Output ("  {0}: {1}" -f $_.Name, $_.Count) }
Write-Output "sample new terms:"
$added | Select-Object -First 14 | ForEach-Object { Write-Output ("  [" + $_.type + "] " + $_.term) }
