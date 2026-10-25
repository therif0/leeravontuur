"""De handleiding (docs/handleiding) volgt het programma: elk onderwerp en elk startargument staat erin, elke
verwijzing klopt en de automatische stukken (tabellen per leerjaar, denkfouten, spiekbrieven) zijn bijgewerkt.
Rood? Draai `python3 docs/tools/handleiding.py` en vul de handleiding aan."""

import importlib.util
import re
import unittest
from pathlib import Path

from leeravontuur.__main__ import maak_parser
from leeravontuur.kern import catalogus  # noqa: F401  (alle onderwerpen laden)
from leeravontuur.kern.onderwerp import ONDERWERPEN

WORTEL = Path(__file__).resolve().parent.parent
MAP = WORTEL / "docs" / "handleiding"


def laad_script():
    spec = importlib.util.spec_from_file_location("handleiding_script", WORTEL / "docs" / "tools" / "handleiding.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(MAP.is_dir(), "de handleiding is niet meegeleverd")
class TestHandleiding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paginas = {p: p.read_text(encoding="utf-8") for p in MAP.rglob("*.md")}
        cls.alles = "\n".join(cls.paginas.values())

    def test_elk_onderwerp_staat_erin(self):
        for o in ONDERWERPEN.values():
            with self.subTest(o.id):
                self.assertTrue(o.naam in self.alles, f"'{o.naam}' staat nergens in de handleiding")
                self.assertTrue(f"auto:leerlijn {o.id} " in self.alles, f"geen tabel per leerjaar voor {o.id}")
                self.assertTrue(f"auto:denkfouten {o.id} " in self.alles, f"geen denkfouten voor {o.id}")

    def test_elk_startargument_staat_erin(self):
        tekst = self.paginas[MAP / "startargumenten.md"]
        for a in maak_parser()._actions:
            for naam in a.option_strings:
                if naam not in ("-h",):
                    self.assertTrue(naam in tekst, f"{naam} staat niet in startargumenten.md")

    def test_verwijzingen_kloppen(self):
        for pad, tekst in self.paginas.items():
            for doel in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", tekst):
                if doel.startswith("http"):
                    continue
                with self.subTest(f"{pad.relative_to(MAP)} → {doel}"):
                    self.assertTrue((pad.parent / doel).exists(), f"{doel} bestaat niet")

    def test_automatische_stukken_zijn_bijgewerkt(self):
        script = laad_script()
        for pad, tekst in self.paginas.items():
            with self.subTest(str(pad.relative_to(MAP))):
                self.assertEqual(script.vul_in(tekst), tekst,
                                 "niet bijgewerkt: draai python3 docs/tools/handleiding.py")


if __name__ == "__main__":
    unittest.main()
