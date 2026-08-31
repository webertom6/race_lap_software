#!/bin/bash
cd "$(dirname "$0")"
printf '\033]0;Race Lap App - close this window to stop\007'

bash "scripts/print-gradient-logo.sh"
echo ""
bash "scripts/print-rainbow-name.sh"
echo ""
echo "Offline race-timing console"
echo "This window IS the app - closing it stops the server."
echo ""
read -r -p "Press ENTER to start..." _unused

if ! command -v uv >/dev/null 2>&1; then
    echo ""
    echo "uv not found, attempting to install it..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv >/dev/null 2>&1; then
        echo ""
        echo "ERROR: could not find or install uv."
        echo "This first-time setup step needs an internet connection."
        echo "If you already have uv installed, make sure it is on your PATH, then try again."
        echo ""
        read -r -p "Press ENTER to close..." _unused
        exit 1
    fi
fi

export RACE_LAP_LAUNCHER=1
uv sync
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: uv sync failed. Check the messages above."
    read -r -p "Press ENTER to close..." _unused
    exit 1
fi

uv run app.py

echo ""
echo "The app has stopped."
read -r -p "Press ENTER to close..." _unused
