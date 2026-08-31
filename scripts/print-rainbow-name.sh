#!/bin/bash
# Prints ascii/ascii-name.txt with a smooth ANSI true-color rainbow gradient per character.
dir="$(dirname "$0")/.."
while IFS= read -r line || [ -n "$line" ]; do
    printf '%s\n' "$line" | awk '{
        len = length($0)
        pi = 3.14159265
        for (i = 1; i <= len; i++) {
            ch = substr($0, i, 1)
            t = (i - 1) / (len > 1 ? len : 1)
            r = int(180 + (0.5 + 0.5 * sin(2 * pi * t + 0.0)) * 75)
            g = int(180 + (0.5 + 0.5 * sin(2 * pi * t - 2.094)) * 75)
            b = int(180 + (0.5 + 0.5 * sin(2 * pi * t - 4.189)) * 75)
            printf "\033[1m\033[38;2;%d;%d;%dm%s", r, g, b, ch
        }
        printf "\033[0m\n"
    }'
done < "$dir/ascii/ascii-name.txt"
