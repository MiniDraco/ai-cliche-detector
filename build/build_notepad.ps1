$ErrorActionPreference = 'Stop'
$dir = 'D:\Users\gamma\Documents\Claude\Projects\ai-cliche-db'
$data = Get-Content -Raw -Path (Join-Path $dir 'ai-cliche-megadb.json') -Encoding UTF8 | ConvertFrom-Json
$entries = $data.entries
$sevMap = @{ high = 2; medium = 1; low = 0 }

function Short($s, $n) {
  $s = ($s -replace '\s+', ' ').Trim()
  if ($s.Length -gt $n) { return $s.Substring(0, $n).TrimEnd() + '...' }
  return $s
}

# --- literal match patterns (words / phrases / openers / closers / tropes) ---
$litTypes = 'word','phrase','opener','closer','trope'
$patMap = @{}   # phrase -> record (keep highest severity)
foreach ($e in $entries) {
  if ($litTypes -notcontains $e.type) { continue }
  $term = $e.term -replace '\([^)]*\)', ''        # drop parentheticals
  foreach ($part in ($term -split '/')) {
    $p = $part.Trim().Trim("'").Trim('"').Trim()
    $p = ($p -replace '\s+', ' ').Trim()
    $p = $p.TrimEnd('!','?','.',',',':')   # punctuation-suffixed tells should match bare too
    if ($p.Length -lt 3 -or $p.Length -gt 60) { continue }
    if (($p -split ' ').Count -gt 6) { continue }
    if ($p -match '[.][.][.]|…') { continue }
    if ($p -notmatch "^[A-Za-z0-9][A-Za-z0-9 ',.&!?\-]*$") { continue }
    $key = $p.ToLower()
    $sev = $sevMap[$e.type] ; $sev = $sevMap[$e.severity]
    $rec = [ordered]@{ p = $key; s = $sev; t = $e.type; w = (Short $e.why 170) }
    if (-not $patMap.ContainsKey($key) -or $patMap[$key].s -lt $sev) { $patMap[$key] = $rec }
  }
}
$patterns = $patMap.Values | Sort-Object { -$_.s }, p

# --- rhyme pairs ---
$rhyMap = @{}
foreach ($e in $entries) {
  if ($e.type -ne 'rhyme_pair') { continue }
  $words = ($e.term -replace '\([^)]*\)', '') -split '/' | ForEach-Object {
    ($_.Trim().Trim("'").Trim('"').ToLower() -replace '[^a-z]', '')
  } | Where-Object { $_.Length -ge 2 }
  if ($words.Count -lt 2) { continue }
  $a = $words[0]; $b = $words[1]
  $k = (@($a, $b) | Sort-Object) -join '/'
  if ($rhyMap.ContainsKey($k)) { continue }
  $rhyMap[$k] = [ordered]@{ a = $a; b = $b; w = (Short $e.why 150) }
}
$rhymes = $rhyMap.Values | Sort-Object a, b

# --- regex pattern-detectors (type=template) ---
$templates = [System.Collections.Generic.List[object]]::new()
foreach ($e in $entries) {
  if ($e.type -ne 'template') { continue }
  $flags = if ($e.PSObject.Properties.Name -contains 'flags' -and $e.flags) { $e.flags } else { 'gi' }
  $templates.Add([ordered]@{ term = $e.term; pattern = $e.pattern; flags = $flags; s = $sevMap[$e.severity]; w = (Short $e.why 170) })
}

$meta = [ordered]@{ uniqueCount = $data.meta.uniqueCount }

$metaJson = $meta | ConvertTo-Json -Compress
$patJson  = ConvertTo-Json -InputObject @($patterns) -Compress -Depth 4
$rhyJson  = ConvertTo-Json -InputObject @($rhymes)  -Compress -Depth 4
$tplJson  = ConvertTo-Json -InputObject @($templates) -Compress -Depth 4

function Build-Page($templateFile, $outFile) {
  $html = Get-Content -Raw -Path (Join-Path $dir $templateFile) -Encoding UTF8
  $html = $html.Replace('/*__META__*/{}', "/*data*/$metaJson")
  $html = $html.Replace('/*__PATTERNS__*/[]', "/*data*/$patJson")
  $html = $html.Replace('/*__RHYMES__*/[]', "/*data*/$rhyJson")
  $html = $html.Replace('/*__TEMPLATES__*/[]', "/*data*/$tplJson")
  $html | Out-File -FilePath (Join-Path $dir $outFile) -Encoding utf8
}
Build-Page 'build\notepad_template.html'        'apps\cliche-catcher.html'
Build-Page 'build\detector_template.html'       'apps\ai-detector.html'
Build-Page 'build\song-forensics_template.html' 'apps\song-forensics.html'
Build-Page 'build\song-compare_template.html'   'apps\song-compare.html'
Build-Page 'build\complete_template.html'        'apps\complete.html'

Write-Output "pattern detectors: $($templates.Count)"

Write-Output "patterns: $($patterns.Count)"
Write-Output "rhyme pairs: $($rhymes.Count)"
Write-Output "sample high patterns:"
$patterns | Where-Object { $_.s -eq 2 } | Select-Object -First 12 | ForEach-Object { Write-Output ("  " + $_['p']) }
Write-Output "sample rhymes:"
$rhymes | Select-Object -First 8 | ForEach-Object { Write-Output ("  " + $_.a + "/" + $_.b) }
$out = Join-Path $dir 'cliche-catcher.html'
Write-Output ("html bytes: " + (Get-Item $out).Length)
