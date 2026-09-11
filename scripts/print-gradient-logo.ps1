# Prints ascii/ascii-logo.txt with a top-to-bottom blue-to-white gradient
# (one color per row, easing via smoothstep -- matches the app's action-blue brand color).
$root = Split-Path -Parent $PSScriptRoot
$logoPath = Join-Path $root "ascii\ascii-logo.txt"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$topR = 0;   $topG = 94;  $topB = 255   # action-blue #005eff
$botR = 255; $botG = 255; $botB = 255   # white #ffffff

$lines = Get-Content -Raw -Encoding UTF8 -LiteralPath $logoPath -ErrorAction Stop
$lines = $lines -split "`n" | ForEach-Object { $_.TrimEnd("`r") }
$total = $lines.Count
$esc = [char]27

for ($i = 0; $i -lt $total; $i++) {
    $t = $i / [Math]::Max($total - 1, 1)
    $t = $t * $t * (3 - 2 * $t)   # smoothstep ease
    $r = [int]($topR + ($botR - $topR) * $t)
    $g = [int]($topG + ($botG - $topG) * $t)
    $b = [int]($topB + ($botB - $topB) * $t)
    Write-Host "$esc[1m$esc[38;2;$r;$g;${b}m$($lines[$i])$esc[0m"
}
