# Prints ascii/ascii-logo.txt using UTF-8, since cmd.exe's `type` command
# garbles the Braille-art logo even with `chcp 65001` set (a cmd.exe quirk,
# not a font issue -- PowerShell's own UTF-8 read/write renders it correctly).
$root = Split-Path -Parent $PSScriptRoot
$logoPath = Join-Path $root "ascii\ascii-logo.txt"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Get-Content -Raw -Encoding UTF8 -LiteralPath $logoPath | Write-Host -NoNewline
