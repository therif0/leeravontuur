#!/usr/bin/env python3
"""De oude naam van de starter: start nu leeravontuur.py. Dit bestand blijft voorlopig bestaan, zodat oude
snelkoppelingen en gewoontes (python3 oefeningen.py) blijven werken."""

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "leeravontuur.py"), run_name="__main__")
