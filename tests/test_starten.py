"""Starten: leeravontuur.py, de oude naam oefeningen.py en een dubbelklik-bestand per systeem."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

from leeravontuur import VERSIE

WORTEL = Path(__file__).resolve().parent.parent
STARTBESTANDEN = {"win32": "leeravontuur-win.bat", "darwin": "leeravontuur-mac.command",
                  "linux": "leeravontuur-linux.sh"}


def versie(opdracht):
    """De uitvoer van `<opdracht> --versie`, gestart vanuit een andere map (zoals een dubbelklik of snelkoppeling)."""
    uit = subprocess.run([*opdracht, "--versie"], cwd=Path.home(), capture_output=True, timeout=60,
                         stdin=subprocess.DEVNULL,  # een 'pause' in het .bat-bestand wacht dan niet
                         env={**os.environ, "PYTHONIOENCODING": "utf-8"}, encoding="utf-8", errors="replace")
    return uit.stdout


class TestStarten(unittest.TestCase):
    def test_leeravontuur_py(self):
        self.assertIn(f"Leeravontuur {VERSIE}", versie([sys.executable, str(WORTEL / "leeravontuur.py")]))

    def test_oude_naam_werkt_nog(self):
        self.assertIn(f"Leeravontuur {VERSIE}", versie([sys.executable, str(WORTEL / "oefeningen.py")]))

    def test_elk_startbestand_bestaat_en_start_leeravontuur_py(self):
        for naam in STARTBESTANDEN.values():
            with self.subTest(naam):
                self.assertIn("leeravontuur.py", (WORTEL / naam).read_text(encoding="ascii"))

    def test_regeleinden(self):
        """Windows wil CRLF in een .bat, macOS en Linux LF (anders start het script niet)."""
        bat = (WORTEL / STARTBESTANDEN["win32"]).read_bytes()
        self.assertEqual(bat.count(b"\n"), bat.count(b"\r\n"))
        for naam in (STARTBESTANDEN["darwin"], STARTBESTANDEN["linux"]):
            with self.subTest(naam):
                tekst = (WORTEL / naam).read_bytes()
                self.assertNotIn(b"\r", tekst)
                self.assertTrue(tekst.startswith(b"#!/bin/sh\n"))

    @unittest.skipIf(sys.platform == "win32", "uitvoerbaar-bit bestaat niet op Windows")
    def test_uitvoerbaar(self):
        for naam in (STARTBESTANDEN["darwin"], STARTBESTANDEN["linux"]):
            with self.subTest(naam):
                self.assertTrue(os.access(WORTEL / naam, os.X_OK))

    def test_startbestand_van_dit_systeem(self):
        naam = STARTBESTANDEN.get("linux" if sys.platform.startswith("linux") else sys.platform)
        if naam is None:
            self.skipTest(f"geen startbestand voor {sys.platform}")
        pad = str(WORTEL / naam)
        opdracht = ["cmd", "/c", pad] if sys.platform == "win32" else [pad]
        uit = versie(opdracht)
        # op Windows kiest `py` misschien een andere Python dan die van de tests (zonder windows-curses): dan meldt
        # leeravontuur.py dat curses ontbreekt. Ook dat bewijst dat het .bat-bestand Python vond en het juiste
        # bestand startte.
        self.assertTrue(f"Leeravontuur {VERSIE}" in uit or (sys.platform == "win32" and "(curses)" in uit), uit)


if __name__ == "__main__":
    unittest.main()
