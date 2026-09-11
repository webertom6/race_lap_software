# Prints ascii/ascii-logo.txt as a diagonal blue/white split (bottom-left -> top-right), no blend.
$root = Split-Path -Parent $PSScriptRoot
$logoPath = Join-Path $root "ascii\ascii-logo.txt"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$blue  = 0, 94, 255      # action-blue #005eff
$white = 255, 255, 255

$lines = Get-Content -Raw -Encoding UTF8 -LiteralPath $logoPath -ErrorAction Stop
$lines = $lines -split "`n" | ForEach-Object { $_.TrimEnd("`r") }
$rows = $lines.Count
$esc = [char]27

for ($row = 0; $row -lt $rows; $row++) {
    $line = $lines[$row]
    $content = $line.TrimStart(' ')
    $pad = $line.Substring(0, $line.Length - $content.Length)
    $cols = $content.Length
    $rn = $row / [Math]::Max($rows - 1, 1)

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append($pad)
    for ($col = 0; $col -lt $cols; $col++) {
        $cn = $col / [Math]::Max($cols - 1, 1)
        $c = if (($rn + $cn) -lt 1) { $blue } else { $white }
        [void]$sb.Append("$esc[1m$esc[38;2;$($c[0]);$($c[1]);$($c[2])m$($content[$col])")
    }
    [void]$sb.Append("$esc[0m")
    Write-Host $sb.ToString()
}
