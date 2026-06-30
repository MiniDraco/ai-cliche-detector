$ErrorActionPreference = 'Stop'
$dir = 'D:\Users\gamma\Documents\Claude\Projects\ai-cliche-db'
$jsonPath = Join-Path $dir 'ai-cliche-megadb.json'
$data = Get-Content -Raw -Path $jsonPath -Encoding UTF8 | ConvertFrom-Json
$SRC = 'claudeslop'

# extract phrases from the YAML list (- "phrase") WITHOUT echoing any content
$phrases = @()
foreach ($l in (Get-Content -Path (Join-Path $dir 'build\claudeslop_raw.yaml') -Encoding UTF8)) {
  if ($l -match '^\s*-\s*"(.+)"\s*$') { $phrases += $matches[1] }
}

$entries = [System.Collections.Generic.List[object]]::new()
foreach ($e in $data.entries) { $entries.Add($e) }
function Norm($s) { (($s.ToString().ToLower() -replace '[^a-z0-9/ ]', '') -replace '\s+', ' ').Trim() }
$seen = @{}
foreach ($e in $entries) { $seen[($e.type + '|' + (Norm $e.term))] = $true }

$added = 0; $dupe = 0
foreach ($p in $phrases) {
  $t = $p.Trim()
  if ($t.Length -lt 3) { continue }
  $type = if ($t -match ' ') { 'phrase' } else { 'word' }
  $sev = if ($t -match ' ') { 'high' } else { 'medium' }
  $k = $type + '|' + (Norm $t)
  if ($seen.ContainsKey($k)) { $dupe++; continue }
  $seen[$k] = $true
  $entries.Add([PSCustomObject]@{
    term = $t; type = $type; category = 'nsfw fiction tell'; domain = 'prose'
    platforms = @('claude','chatgpt'); why = 'Claude/AI mature-fiction & RP overused phrase (claudeslop list). Filterable nsfw category.'
    example = ''; severity = $sev; sources = @($SRC); source = $SRC
  })
  $added++
}

$all = $entries.ToArray()
$byType = @{}
foreach ($e in $all) { if ($byType.ContainsKey($e.type)) { $byType[$e.type]++ } else { $byType[$e.type] = 1 } }
$data.meta.uniqueCount = $all.Count
$data.meta.rawCount = $data.meta.rawCount + $added
$data.meta.byType = [PSCustomObject]$byType
$data.entries = $all
($data | ConvertTo-Json -Depth 12) | Out-File -FilePath $jsonPath -Encoding utf8

# counts only -- never print the phrases
Write-Output ("parsed from list: " + $phrases.Count)
Write-Output ("NEW added (after dedupe): " + $added + "   dupe: " + $dupe)
Write-Output ("DB total now: " + $all.Count)
