$ErrorActionPreference = 'Stop'
$dir = 'D:\Users\gamma\Documents\Claude\Projects\ai-cliche-db'
$jsonPath = Join-Path $dir 'ai-cliche-megadb.json'
$data = Get-Content -Raw -Path $jsonPath -Encoding UTF8 | ConvertFrom-Json
$tpls = Get-Content -Raw -Path (Join-Path $dir 'build\templates.json') -Encoding UTF8 | ConvertFrom-Json

$entries = [System.Collections.Generic.List[object]]::new()
foreach ($e in $data.entries) { $entries.Add($e) }

function Norm($s) { (($s.ToString().ToLower() -replace '[^a-z0-9/ ]', '') -replace '\s+', ' ').Trim() }
$seen = @{}
foreach ($e in $entries) { $seen[($e.type + '|' + (Norm $e.term))] = $true }

$added = 0
foreach ($t in $tpls) {
  $key = 'template|' + (Norm $t.term)
  if ($seen.ContainsKey($key)) { continue }
  $seen[$key] = $true
  $entries.Add([PSCustomObject]@{
    term = $t.term; type = 'template'; category = $t.category; domain = $t.domain
    platforms = $t.platforms; why = $t.why; example = $t.example; severity = $t.severity
    pattern = $t.pattern; flags = $t.flags
    sources = @('pattern-detector'); source = 'pattern-detector'
  })
  $added++
}

$all = $entries.ToArray()
$byType = @{}
foreach ($e in $all) { if ($byType.ContainsKey($e.type)) { $byType[$e.type]++ } else { $byType[$e.type] = 1 } }
$data.meta.uniqueCount = $all.Count
$data.meta.rawCount = $data.meta.rawCount + $added
$data.meta.byType = [PSCustomObject]$byType
$data.meta.builtBy = '26-agent workflow + dedup/merge + compass-research + regex pattern-detectors'
$data.entries = $all
($data | ConvertTo-Json -Depth 12) | Out-File -FilePath $jsonPath -Encoding utf8

Write-Output ("template detectors in file: " + $tpls.Count)
Write-Output ("NEW added (after dedupe): " + $added)
Write-Output ("DB total now: " + $all.Count)
