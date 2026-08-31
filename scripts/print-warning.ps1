# Prints the "don't click" caution text in bold alert-red (matches DESIGN.md's alert-red #e11d22).
$esc = [char]27
$r = 225; $g = 29; $b = 34
Write-Host "$esc[1m$esc[38;2;$r;$g;${b}mDon't click inside this window while it's running -$esc[0m"
Write-Host "$esc[1m$esc[38;2;$r;$g;${b}mit can pause the app (press Enter if it looks frozen).$esc[0m"
