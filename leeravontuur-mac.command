#!/bin/sh
# Leeravontuur starten op macOS: dubbelklik op dit bestand (de eerste keer eventueel: rechtsklik > Open).
cd "$(dirname "$0")" || exit 1
exec python3 leeravontuur.py "$@"
