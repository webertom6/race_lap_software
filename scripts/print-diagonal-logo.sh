#!/bin/bash
# Prints ascii/ascii-logo.txt as a diagonal blue/white split (bottom-left -> top-right), no blend.
# LC_ALL=C keeps awk byte-safe; each braille char is a fixed 3-byte UTF-8 sequence
# once the leading ASCII space padding is stripped, so chunking by 3 bytes is safe.
dir="$(dirname "$0")/.."

LC_ALL=C awk '
{ lines[NR] = $0; total = NR }
END {
    blue_r = 0;   blue_g = 94;  blue_b = 255
    white_r = 255; white_g = 255; white_b = 255
    rows = total
    for (row = 1; row <= rows; row++) {
        line = lines[row]
        pad = 0
        while (substr(line, pad + 1, 1) == " ") pad++
        content = substr(line, pad + 1)
        cols = length(content) / 3
        out = substr(line, 1, pad)
        rn = (rows > 1) ? (row - 1) / (rows - 1) : 0
        for (col = 0; col < cols; col++) {
            ch = substr(content, col * 3 + 1, 3)
            cn = (cols > 1) ? col / (cols - 1) : 0
            if (rn + cn < 1) { r = blue_r; g = blue_g; b = blue_b }
            else { r = white_r; g = white_g; b = white_b }
            out = out sprintf("\033[1m\033[38;2;%d;%d;%dm%s", r, g, b, ch)
        }
        printf "%s\033[0m\n", out
    }
}
' "$dir/ascii/ascii-logo.txt"
