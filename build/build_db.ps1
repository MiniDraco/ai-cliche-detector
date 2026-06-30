$ErrorActionPreference = 'Stop'
$outDir = 'D:\Users\gamma\Documents\Claude\Projects\ai-cliche-db'
# Canonical store = ai-cliche-megadb.json (built by workflow, extended by add_compass.ps1).
# This script only RE-EMITS the CSV + Markdown views from it; it never rewrites the JSON.
$data = Get-Content -Raw -Path (Join-Path $outDir 'ai-cliche-megadb.json') -Encoding UTF8 | ConvertFrom-Json
$r = $data.meta
$entries = $data.entries

# --- Flat CSV ---
$entries | Select-Object `
  @{n='term';e={$_.term}}, `
  @{n='type';e={$_.type}}, `
  @{n='domain';e={$_.domain}}, `
  @{n='category';e={$_.category}}, `
  @{n='severity';e={$_.severity}}, `
  @{n='platforms';e={($_.platforms) -join '; '}}, `
  @{n='why';e={$_.why}}, `
  @{n='example';e={$_.example}}, `
  @{n='pattern';e={$_.pattern}}, `
  @{n='sources';e={($_.sources) -join '; '}} |
  Export-Csv -Path (Join-Path $outDir 'ai-cliche-megadb.csv') -NoTypeInformation -Encoding utf8

# --- 3. Grouped Markdown ---
$sevRank = @{ high = 3; medium = 2; low = 1 }
$domainOrder = @{ lyrics = 0; both = 1; prose = 2 }
$sb = New-Object System.Text.StringBuilder
$null = $sb.AppendLine('# THE AI CLICHE MEGA-DATABASE')
$null = $sb.AppendLine('')
$null = $sb.AppendLine("**$($r.uniqueCount) unique entries** (deduped from $($r.rawCount) raw findings by a 26-agent research sweep).")
$null = $sb.AppendLine('Every entry is a community-flagged "dead giveaway" of AI-generated text or lyrics across ChatGPT, Gemini, Suno, and Udio.')
$null = $sb.AppendLine('')
$null = $sb.AppendLine('Companion file: `AI-CLICHE-BANLIST.md` (the curated, paste-ready directive). This file is the full searchable catalog.')
$null = $sb.AppendLine('')
$typeLine = ($r.byType.PSObject.Properties | ForEach-Object { "$($_.Name): $($_.Value)" }) -join ' | '
$null = $sb.AppendLine("**By type:** $typeLine")
$null = $sb.AppendLine('')
$null = $sb.AppendLine('Severity: EMOJIHIGH high = instant tell, EMOJIMED medium, EMOJILOW low. Domain: **lyrics** (Suno/Udio), **prose** (ChatGPT/Gemini), **both**.')
$null = $sb.AppendLine('')
$null = $sb.AppendLine('---')
$null = $sb.AppendLine('')

$sevIcon = @{ high = 'EMOJIHIGH'; medium = 'EMOJIMED'; low = 'EMOJILOW' }
$dash = [char]0x2014

$grouped = $entries | Group-Object domain | Sort-Object { $domainOrder[$_.Name] }
foreach ($dom in $grouped) {
  $null = $sb.AppendLine("# DOMAIN: $($dom.Name.ToUpper())  ($($dom.Count))")
  $null = $sb.AppendLine('')
  $cats = $dom.Group | Group-Object category | Sort-Object Name
  foreach ($cat in $cats) {
    $null = $sb.AppendLine("## $($cat.Name)  ($($cat.Count))")
    $null = $sb.AppendLine('')
    $rows = $cat.Group | Sort-Object @{e={ - $sevRank[$_.severity] }}, term
    foreach ($e in $rows) {
      $icon = $sevIcon[$e.severity]
      $why = ($e.why -replace '\s+', ' ').Trim()
      $line = "- $icon **$($e.term)** _($($e.type))_ $dash $why"
      if ($e.example) { $line += "  _e.g._ ""$($e.example)""" }
      $null = $sb.AppendLine($line)
    }
    $null = $sb.AppendLine('')
  }
}
$md = $sb.ToString()
$md = $md.Replace('EMOJIHIGH', [char]::ConvertFromUtf32(0x1F534)).Replace('EMOJIMED', [char]::ConvertFromUtf32(0x1F7E0)).Replace('EMOJILOW', [char]::ConvertFromUtf32(0x1F7E1))
$md | Out-File -FilePath (Join-Path $outDir 'AI-CLICHE-MEGADB.md') -Encoding utf8

Write-Output "JSON entries: $($entries.Count)"
Write-Output "CSV rows: $($entries.Count)"
Write-Output ("MD bytes: " + $md.Length)
Get-ChildItem $outDir | Select-Object Name, Length | Format-Table -AutoSize | Out-String | Write-Output
