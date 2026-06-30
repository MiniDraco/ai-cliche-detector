$ErrorActionPreference = 'Stop'
$dir = 'D:\Users\gamma\Documents\Claude\Projects\ai-cliche-db'
$jsonPath = Join-Path $dir 'ai-cliche-megadb.json'
$data = Get-Content -Raw -Path $jsonPath -Encoding UTF8 | ConvertFrom-Json
$extra = Get-Content -Raw -Path (Join-Path $dir 'build\platform_tells.json') -Encoding UTF8 | ConvertFrom-Json
$SRC = 'platform-tells'

$entries = [System.Collections.Generic.List[object]]::new()
foreach ($e in $data.entries) { $entries.Add($e) }
function Norm($s) { (($s.ToString().ToLower() -replace '[^a-z0-9/ ]', '') -replace '\s+', ' ').Trim() }
function Plats($e, $d) {
  if ($e.PSObject.Properties.Name -contains 'platform' -and $e.platform) { return @($e.platform) }
  if ($d -eq 'lyrics') { return @('suno','udio') } elseif ($d -eq 'prose') { return @('chatgpt','gemini','claude') } else { return @('chatgpt','gemini','suno','udio') }
}
$seen = @{}
foreach ($e in $entries) { $seen[($e.type + '|' + (Norm $e.term))] = $true }
$added = @{ template = 0; literal = 0 }

foreach ($t in $extra.templates) {
  $k = 'template|' + (Norm $t.term); if ($seen.ContainsKey($k)) { continue }; $seen[$k] = $true
  $flags = if ($t.PSObject.Properties.Name -contains 'flags' -and $t.flags) { $t.flags } else { 'gi' }
  $entries.Add([PSCustomObject]@{ term=$t.term; type='template'; category=$t.category; domain=$t.domain; platforms=(Plats $t $t.domain); why=$t.why; example=''; severity=$t.severity; pattern=$t.pattern; flags=$flags; sources=@($SRC); source=$SRC })
  $added.template++
}
foreach ($l in $extra.literals) {
  $k = $l.type + '|' + (Norm $l.term); if ($seen.ContainsKey($k)) { continue }; $seen[$k] = $true
  $entries.Add([PSCustomObject]@{ term=$l.term; type=$l.type; category=$l.category; domain=$l.domain; platforms=(Plats $l $l.domain); why=$l.why; example=''; severity=$l.severity; sources=@($SRC); source=$SRC })
  $added.literal++
}

$all = $entries.ToArray()
$byType = @{}
foreach ($e in $all) { if ($byType.ContainsKey($e.type)) { $byType[$e.type]++ } else { $byType[$e.type] = 1 } }
$tot = $added.template + $added.literal
$data.meta.uniqueCount = $all.Count
$data.meta.rawCount = $data.meta.rawCount + $tot
$data.meta.byType = [PSCustomObject]$byType
$data.entries = $all
($data | ConvertTo-Json -Depth 12) | Out-File -FilePath $jsonPath -Encoding utf8
Write-Output ("NEW added (after dedupe): templates {0}, literals {1} = {2}" -f $added.template, $added.literal, $tot)
Write-Output ("DB total now: " + $all.Count)
