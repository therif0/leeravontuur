"""Tests voor CI: zoals `python -m unittest discover -s tests`, maar fouten verschijnen ook als annotaties.

Zo zijn fouten te lezen via de GitHub-API, ook zonder toegang tot de volledige logbestanden.
"""

import os
import sys
import unittest
from pathlib import Path

MAP = Path(__file__).resolve().parent
sys.path.insert(0, str(MAP.parent))


def annotatie(titel, tekst):
    tekst = tekst.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::error title={titel}::{tekst}")


def main():
    suite = unittest.defaultTestLoader.discover(str(MAP), top_level_dir=str(MAP.parent))
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    if os.environ.get("GITHUB_ACTIONS"):
        for test, uitleg in res.errors + res.failures:
            annotatie(str(test)[:200], uitleg[-3000:])
    return 0 if res.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
