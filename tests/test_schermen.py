"""Schermtests zonder echte terminal: toetsen, muisklikken en het scrollwiel via NepScherm."""

import curses
import os
import tempfile
import unittest

from leeravontuur.kern import instellingen
from leeravontuur.terminal.app import App
from leeravontuur.terminal.nepscherm import NepScherm, ToetsenOp
from leeravontuur.terminal.schermen.eenheden import TABEL_X, TABEL_Y

ESC = "\x1b"
OK = "\n"


class Basis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.oud = os.environ.get("LEERAVONTUUR_DATA")
        os.environ["LEERAVONTUUR_DATA"] = self.tmp.name

    def tearDown(self):
        if self.oud is None:
            os.environ.pop("LEERAVONTUUR_DATA", None)
        else:
            os.environ["LEERAVONTUUR_DATA"] = self.oud
        self.tmp.cleanup()

    def speel(self, toetsen, **inst):
        """Speelt de toetsen af. Geeft (nepscherm, app). Stopt netjes als de toetsen op zijn."""
        scherm = NepScherm(toetsen)
        app = App(scherm, instellingen.Instellingen(**inst), kleuren=False)
        try:
            app.start()
        except ToetsenOp:
            pass
        return scherm, app

    def ergens(self, scherm, tekst):
        return any(tekst in b for b in scherm.beelden)


class TestStart(Basis):
    def test_startscherm_en_naam(self):
        scherm, app = self.speel([OK, *"Imrane", OK, ESC])
        self.assertTrue(self.ergens(scherm, "Solve It Now"))
        self.assertTrue(self.ergens(scherm, "Hallo Imrane!"))
        self.assertEqual(instellingen.laad().naam, "Imrane")

    def test_ascii(self):
        scherm, _ = self.speel([OK, ESC], naam="Test", ascii=True)
        for beeld in scherm.beelden:
            self.assertTrue(all(ord(c) < 128 for c in beeld), beeld)


class TestReeks(Basis):
    def test_reeks_van_tien_met_rapport(self):
        antwoorden = ["1", OK, OK] * 10
        toetsen = [OK, "1", "1", "1", "2", "2", OK, *antwoorden, ESC, ESC, ESC, ESC, ESC]
        scherm, app = self.speel(toetsen, naam="Test")
        self.assertEqual(app.stat["vragen"], 10)
        self.assertTrue(self.ergens(scherm, "Je score:"))
        self.assertTrue(self.ergens(scherm, "Leeravontuur › Leren › Wiskunde › Eenheden"))

    def test_vrij_oefenen_tip(self):
        toetsen = [OK, "1", "1", "1", "1", "1", OK, "?", ESC, ESC, ESC, ESC, ESC]
        scherm, _ = self.speel(toetsen, naam="Test")
        self.assertTrue(self.ergens(scherm, "Tip:"))


class TestMuis(Basis):
    def test_tabel_klikken_en_komma(self):
        rij = TABEL_Y + 3
        cel_m = TABEL_X + 1 + 3 * 6          # 4de kolom: m
        rand_m = cel_m + 5                   # de rand rechts van m = komma achter m
        toetsen = [OK, "1", "1", "1", "3", "2", OK,
                   ("klik", rij, cel_m + 2), "4", ("klik", rij, rand_m),
                   ESC, ESC, ESC, ESC, ESC]
        scherm, _ = self.speel(toetsen, naam="Test")
        self.assertTrue(self.ergens(scherm, "Aflezen met de komma achter m: 4 m"))

    def test_menu_en_opties_klikken(self):
        # hoofdmenu: Opties staat op rij 5 + 2*2 = 9; in Opties staat Kleuren op rij 4 + 2*2 = 8
        toetsen = [OK, ("klik", 9, 10), ("klik", 8, 10), ESC, ESC]
        scherm, app = self.speel(toetsen, naam="Test")
        self.assertEqual(app.inst.thema, "rood-groen")
        self.assertEqual(instellingen.laad().thema, "rood-groen")

    def test_knop_in_voetbalk(self):
        toetsen = [OK, "1"]
        scherm, _ = self.speel(toetsen, naam="Test")
        y, x = scherm.zoek("[Esc]")
        scherm2, app = self.speel([OK, "1", ("klik", y, x + 1), ESC], naam="Test")
        # na de klik op [Esc] staan we terug in het hoofdmenu
        self.assertIn("Wat wil je doen?", scherm2.beelden[-1])

    def test_broodkruimel_terug_naar_hoofdmenu(self):
        toetsen = [OK, "1", "1", "1", ("klik", 0, 2), ESC]
        scherm, _ = self.speel(toetsen, naam="Test")
        self.assertIn("Wat wil je doen?", scherm.beelden[-1])

    def test_scrollwiel_in_spiekbrief(self):
        toetsen = [OK, "2", "1", ("wiel", 1), ("wiel", 1), ("wiel", 1), ("wiel", 1), ("wiel", 1),
                   ("wiel", 1), ("wiel", 1), ("wiel", 1), ESC, ESC, ESC]
        scherm, _ = self.speel(toetsen, naam="Test")
        self.assertTrue(self.ergens(scherm, "VOORBEELD"))


class TestTypen(Basis):
    def test_accenten_typen(self):
        scherm, app = self.speel([OK, *"Zoë", OK, ESC])
        self.assertEqual(app.inst.naam, "Zoë")

    def test_te_klein_venster(self):
        scherm = NepScherm([OK], hoogte=20, breedte=60)
        app = App(scherm, instellingen.Instellingen(naam="Test"), kleuren=False)
        with self.assertRaises(ToetsenOp):
            app.start()
        self.assertTrue(any("te klein" in b for b in scherm.beelden))


if __name__ == "__main__":
    unittest.main()
