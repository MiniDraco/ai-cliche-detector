$ErrorActionPreference = 'Stop'
$dir = 'D:\Users\gamma\Documents\Claude\Projects\ai-cliche-db'
$jsonPath = Join-Path $dir 'ai-cliche-megadb.json'
$data = Get-Content -Raw -Path $jsonPath -Encoding UTF8 | ConvertFrom-Json
$slop = Get-Content -Raw -Path (Join-Path $dir 'build\antislop_raw.json') -Encoding UTF8 | ConvertFrom-Json
$SRC = 'antislop'

$entries = [System.Collections.Generic.List[object]]::new()
foreach ($e in $data.entries) { $entries.Add($e) }
function Norm($s) { (($s.ToString().ToLower() -replace '[^a-z0-9/ ]', '') -replace '\s+', ' ').Trim() }
$seen = @{}
foreach ($e in $entries) { $seen[($e.type + '|' + (Norm $e.term))] = $true }

# character names models fixate on (tag them distinctly)
$names = @('elara','elysia','kael','lyra','seraphina','aeris','thorne','elias','isolde','anya','sylvana','eldoria','aetheria','whisperwind')

$added = 0; $skipped = 0
foreach ($row in $slop) {
  $term = [string]$row[0]
  $prob = [double]$row[1]
  $t = $term.Trim()
  if ($t.Length -lt 3) { $skipped++; continue }
  if ($t -notmatch "^[A-Za-z0-9][A-Za-z0-9 ',\-]*$") { $skipped++; continue }
  $multiword = $t -match ' '
  $type = if ($multiword) { 'phrase' } else { 'word' }
  $isName = $names -contains $t.ToLower()
  $sev = if ($isName) { 'medium' }
         elseif ($multiword) { 'high' }
         elseif ($prob -le 0.1) { 'high' }
         elseif ($prob -le 0.5) { 'medium' }
         else { 'low' }
  $cat = if ($isName) { 'antislop: fixated character name' } else { 'antislop (open-model slop)' }
  $k = $type + '|' + (Norm $t)
  if ($seen.ContainsKey($k)) { $skipped++; continue }
  $seen[$k] = $true
  $entries.Add([PSCustomObject]@{
    term = $t; type = $type; category = $cat; domain = 'both'
    platforms = @('chatgpt','gemini','suno','udio','claude'); why = "Over-represented in LLM output vs human writing (EQ-Bench antislop list, suppression $([math]::Round($prob,3))). Open-model slop that distills into most fine-tunes/wrappers."
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
Write-Output ("antislop entries in file: " + $slop.Count)
Write-Output ("NEW added (after dedupe): " + $added + "   skipped/dupe: " + $skipped)
Write-Output ("DB total now: " + $all.Count)
