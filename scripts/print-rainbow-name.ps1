# Prints ascii/ascii-name.txt with a smooth ANSI true-color rainbow gradient per character.
$root = Split-Path -Parent $PSScriptRoot
$namePath = Join-Path $root "ascii\ascii-name.txt"
$esc = [char]27
$pi = [Math]::PI

foreach ($line in Get-Content -LiteralPath $namePath) {
    $len = $line.Length
    if ($len -eq 0) {
        Write-Host ""
        continue
    }
    $sb = New-Object System.Text.StringBuilder
    for ($i = 0; $i -lt $len; $i++) {
        $t = $i / [Math]::Max($len, 1)
        $r = [int](180 + (0.5 + 0.5 * [Math]::Sin(2 * $pi * $t + 0.0)) * 75)
        $g = [int](180 + (0.5 + 0.5 * [Math]::Sin(2 * $pi * $t - 2.094)) * 75)
        $b = [int](180 + (0.5 + 0.5 * [Math]::Sin(2 * $pi * $t - 4.189)) * 75)
        [void]$sb.Append("$esc[1m$esc[38;2;$r;$g;${b}m$($line[$i])")
    }
    [void]$sb.Append("$esc[0m")
    Write-Host $sb.ToString()
}
