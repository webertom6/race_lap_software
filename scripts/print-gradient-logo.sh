#!/bin/bash
# Prints ascii/ascii-logo.txt with a top-to-bottom blue-to-white gradient
# (one color per row, easing via smoothstep -- matches the app's action-blue brand color).
# LC_ALL=C keeps awk byte-safe: it never inspects the multi-byte UTF-8 content,
# only re-emits it verbatim via %s, so it can't mangle it (bash `read` would).
dir="$(dirname "$0")/.."

LC_ALL=C awk '
{ lines[NR] = $0; total = NR }
END {
    top_r = 0;   top_g = 94;  top_b = 255
    bot_r = 255; bot_g = 255; bot_b = 255
    for (i = 1; i <= total; i++) {
        t = (total > 1) ? (i - 1) / (total - 1) : 0
        t = t * t * (3 - 2 * t)
        r = int(top_r + (bot_r - top_r) * t)
        g = int(top_g + (bot_g - top_g) * t)
        b = int(top_b + (bot_b - top_b) * t)
        printf "\033[1m\033[38;2;%d;%d;%dm%s\033[0m\n", r, g, b, lines[i]
    }
}
' "$dir/ascii/ascii-logo.txt"

