#!/bin/sh
# Leeravontuur starten op Linux: ./leeravontuur-linux.sh (of dubbelklik en kies "uitvoeren in terminal").
cd "$(dirname "$0")" || exit 1
exec python3 leeravontuur.py "$@"
