"""Bewaakt de afspraken uit CLAUDE.md: kern zonder curses, kleuren alleen via het thema."""

import re
import unittest
from pathlib import Path

from leeravontuur.terminal import tekens, thema

PAKKET = Path(__file__).resolve().parent.parent / "leeravontuur"


class TestArchitectuur(unittest.TestCase):
    def test_kern_zonder_curses(self):
        for pad in (PAKKET / "kern").rglob("*.py"):
            with self.subTest(pad.name):
                self.assertNotRegex(pad.read_text(encoding="utf-8"), r"^\s*(import|from)\s+curses",
                                    "de kern mag curses niet gebruiken")

    def test_tkinter_alleen_in_een_eigen_venster(self):
        """tkinter draait in een eigen proces (venster/); de terminal start het alleen, de kern kent het niet."""
        for pad in PAKKET.rglob("*.py"):
            tekst = pad.read_text(encoding="utf-8")
            with self.subTest(pad.name):
                if pad.parent.name != "venster":
                    self.assertNotRegex(tekst, r"^\s*(import|from)\s+tkinter", "tkinter alleen in venster/")
                else:
                    self.assertNotRegex(tekst, r"^\s*(import|from)\s+(curses|\.\.terminal)", "venster/ zonder curses")
                if pad.parent.name == "kern":
                    self.assertNotRegex(tekst, r"^\s*from\s+\.\.venster", "de kern kent de vensters niet")

    def test_kleuren_alleen_in_thema(self):
        for pad in (PAKKET / "terminal").rglob("*.py"):
            if pad.name == "thema.py":
                continue
            with self.subTest(pad.name):
                tekst = pad.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"color_pair|COLOR_|init_pair", tekst),
                                  "gebruik een rol uit thema.py in plaats van een kleur")


class TestThemas(unittest.TestCase):
    def test_elk_palet_heeft_alle_kleurrollen(self):
        kleurrollen = set(thema.ROLLEN) - {"bold", "dim", "veld"}
        for naam, palet in thema.PALETTEN.items():
            with self.subTest(naam):
                self.assertEqual(set(palet), kleurrollen)

    def test_zonder_kleur_alle_rollen(self):
        attrs = thema.maak("standaard", kleuren=False)
        for rol in thema.ROLLEN:
            self.assertIn(rol, attrs)

    def test_ascii_een_op_een(self):
        for teken, vervanging in tekens._ASCII.items():
            self.assertEqual(len(vervanging), 1, teken)
            self.assertLess(ord(vervanging), 128)

    def test_elk_speciaal_teken_heeft_een_ascii_vervanging(self):
        """Alle niet-ASCII-tekens in de code en de inhoud worden in ASCII-modus 1 gewoon teken (geen '?')."""
        wortel = Path(__file__).resolve().parent.parent / "leeravontuur"
        gevonden = set()
        for pad in [*wortel.rglob("*.py"), *wortel.rglob("*.json")]:
            gevonden |= {c for c in pad.read_text(encoding="utf-8") if ord(c) >= 128}
        for c in sorted(gevonden):
            vervanging = tekens.naar_ascii(c)
            self.assertEqual(len(vervanging), 1, c)
            self.assertNotEqual(vervanging, "?", f"geen ASCII-vervanging voor {c!r} (voeg toe in terminal/tekens.py)")


if __name__ == "__main__":
    unittest.main()
