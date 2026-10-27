#!/usr/bin/env python3
"""Leeravontuur starten: python3 leeravontuur.py   (hulp: python3 leeravontuur.py --help)

Een gratis leerprogramma van Solve It Now. Iedereen moet kunnen leren.
"""

import sys

if sys.version_info < (3, 10):
    print("Leeravontuur heeft Python 3.10 of nieuwer nodig.")
    print(f"Je hebt nu Python {sys.version.split()[0]}. Installeer een nieuwere versie via https://www.python.org")
    sys.exit(1)

try:
    import curses  # noqa: F401
except ImportError:
    print("Er ontbreekt nog één onderdeel om het scherm te tekenen (curses).")
    if sys.platform == "win32":
        print("Doe eerst (één keer):   py -m pip install -r requirements.txt")
    else:
        print("Doe eerst (één keer):   python3 -m pip install -r requirements.txt")
    sys.exit(1)

from leeravontuur.__main__ import main  # noqa: E402

sys.exit(main())
