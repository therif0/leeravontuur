"""Schermtests zonder echte terminal: toetsen, muisklikken en het scrollwiel via NepScherm."""

import os
import tempfile
import unittest

from leeravontuur.kern.instellingen import Instellingen
from leeravontuur.kern.opslag import Opslag
from leeravontuur.terminal.app import App
from leeravontuur.terminal.nepscherm import NepScherm, ToetsenOp
from leeravontuur.terminal.schermen.eenheden import TABEL_X, TABEL_Y

ESC = "\x1b"
OK = "\n"

# keuzes in het hoofdmenu (als toets)
HOOFDMENU = ["▶ Verder", "Leren & oefenen", "Herhalen", "Mijn avatar", "Spiekbrieven", "Opties",
             "Wissel van kind", "Stoppen"]


def hm(keuze):
    """De toets voor een keuze in het hoofdmenu."""
    return str(HOOFDMENU.index(keuze) + 1)


def hm_rij(keuze):
    """De schermrij van een keuze in het hoofdmenu (voor een muisklik)."""
    return 5 + HOOFDMENU.index(keuze) * (2 if 5 + 2 * len(HOOFDMENU) < 20 else 1)


class Basis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.oud = os.environ.get("LEERAVONTUUR_DATA")
        os.environ["LEERAVONTUUR_DATA"] = self.tmp.name
        self.open = []

    def tearDown(self):
        for o in self.open:
            o.sluit()
        if self.oud is None:
            os.environ.pop("LEERAVONTUUR_DATA", None)
        else:
            os.environ["LEERAVONTUUR_DATA"] = self.oud
        self.tmp.cleanup()

    def opslag(self, *kinderen):
        """Databank in de tijdelijke map met de gevraagde kinderen: (naam, leerjaar[, {opties}])."""
        o = Opslag.open()
        self.open.append(o)
        for naam, jaar, *opties in kinderen:
            kind = o.nieuw_kind(naam, jaar, Instellingen(**(opties[0] if opties else {})))
            if o.algemeen("laatste_kind") is None:
                o.zet_algemeen("laatste_kind", kind.id)
        return o

    def speel(self, toetsen, opslag=None, voorrang=None, **scherm_opties):
        """Speelt de toetsen af. Geeft (nepscherm, app). Stopt netjes als de toetsen op zijn."""
        scherm = NepScherm(toetsen, **scherm_opties)
        app = App(scherm, opslag or self.opslag(("Test", "5")), voorrang, kleuren=False)
        try:
            app.start()
        except ToetsenOp:
            pass
        return scherm, app

    def ergens(self, scherm, tekst):
        return any(tekst in b for b in scherm.beelden)


class TestStart(Basis):
    def test_eerste_start_maakt_kind(self):
        o = self.opslag()
        scherm, app = self.speel([OK, *"Imrane", OK, OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Solve It Now"))
        self.assertTrue(self.ergens(scherm, "Hallo Imrane!"))
        kinderen = o.kinderen()
        self.assertEqual([(k.naam, k.leerjaar) for k in kinderen], [("Imrane", "5")])
        self.assertEqual(o.algemeen("laatste_kind"), kinderen[0].id)

    def test_tweede_start_kiest_laatste_kind(self):
        o = self.opslag(("Amira", "3"), ("Imrane", "5"))
        o.zet_algemeen("laatste_kind", next(k.id for k in o.kinderen() if k.naam == "Imrane"))
        scherm, app = self.speel([OK, OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Wie ben jij?"))
        self.assertEqual(app.kind.naam, "Imrane")

    def test_dubbele_naam(self):
        o = self.opslag(("Imrane", "5"))
        scherm, _ = self.speel([OK, "2", *"imrane", OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Er is al iemand die imrane heet"))

    def test_wissel_van_kind_met_eigen_instellingen(self):
        o = self.opslag(("Amira", "3", {"thema": "rood-groen"}), ("Imrane", "5"))
        scherm, app = self.speel([OK, "1", hm("Wissel van kind"), "2", ESC], opslag=o)  # Amira, dan wisselen naar Imrane
        self.assertTrue(self.ergens(scherm, "Hallo Amira!"))
        self.assertEqual(app.kind.naam, "Imrane")
        self.assertEqual(app.inst.thema, "standaard")
        self.assertEqual(app.inst.leerjaar, "5")

    def test_ascii(self):
        scherm, _ = self.speel([OK, OK, ESC], voorrang={"ascii": True})
        for beeld in scherm.beelden:
            self.assertTrue(all(ord(c) < 128 for c in beeld), beeld)

    def test_startargument_wordt_niet_bewaard(self):
        o = self.opslag(("Test", "5"))
        # gestart met --contrast; in Opties de muis uitzetten (rij 3 + 2*4 = 11)
        scherm, app = self.speel([OK, OK, hm("Opties"), ("klik", 11, 10), ESC, ESC], opslag=o,
                                 voorrang={"thema": "contrast"})
        bewaard = o.instellingen_van(app.kind.id)
        self.assertEqual(bewaard.thema, "standaard")
        self.assertFalse(bewaard.muis)
        self.assertEqual(app.inst.thema, "contrast")


class TestReeks(Basis):
    def test_reeks_van_tien_wordt_bewaard(self):
        o = self.opslag(("Test", "5"))
        antwoorden = ["1", OK, OK] * 10
        toetsen = [OK, OK, "2", "1", "1", "2", "2", OK, *antwoorden, ESC, ESC, ESC, ESC, ESC]
        scherm, app = self.speel(toetsen, opslag=o)
        self.assertTrue(self.ergens(scherm, "Je score:"))
        self.assertTrue(self.ergens(scherm, "Leeravontuur › Leren › Wiskunde › Eenheden"))
        rijen = o.antwoorden(app.kind.id)
        self.assertEqual(len(rijen), 10)
        self.assertTrue(all(r["tijd_ms"] >= 0 and r["modus"] == "reeks" and r["gegeven"] == "1" for r in rijen))
        self.assertTrue(all(r["vaardigheid"] == "wiskunde.eenheden.omzetten" for r in rijen))
        sessies = o.sessies(app.kind.id)
        self.assertEqual(len(sessies), 1)
        self.assertIsNotNone(sessies[0]["einde"])
        self.assertEqual(app.vandaag()[0], 10)
        # na een herstart staat de telling van vandaag er nog
        scherm2, _ = self.speel([OK, OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm2, "Vandaag al 10 vragen geoefend"))

    def test_vrij_oefenen_tip(self):
        o = self.opslag(("Test", "5"))
        toetsen = [OK, OK, "2", "1", "1", "1", "1", OK, "?", "5", OK, ESC, ESC, ESC, ESC, ESC]
        scherm, app = self.speel(toetsen, opslag=o)
        self.assertTrue(self.ergens(scherm, "Tip:"))
        rijen = o.antwoorden(app.kind.id)
        self.assertEqual((len(rijen), rijen[0]["hulp"], rijen[0]["modus"]), (1, 1, "vrij"))


class TestMuis(Basis):
    def test_tabel_klikken_en_komma(self):
        rij = TABEL_Y + 3
        cel_m = TABEL_X + 1 + 3 * 6          # 4de kolom: m
        rand_m = cel_m + 5                   # de rand rechts van m = komma achter m
        toetsen = [OK, OK, "2", "1", "1", "3", "2", OK,
                   ("klik", rij, cel_m + 2), "4", ("klik", rij, rand_m),
                   ESC, ESC, ESC, ESC, ESC]
        scherm, _ = self.speel(toetsen)
        self.assertTrue(self.ergens(scherm, "Aflezen met de komma achter m: 4 m"))

    def test_menu_en_opties_klikken(self):
        # in Opties staat Kleuren op rij 3 + 2*2 = 7
        o = self.opslag(("Test", "5"))
        toetsen = [OK, OK, ("klik", hm_rij("Opties"), 10), ("klik", 7, 10), ESC, ESC]
        scherm, app = self.speel(toetsen, opslag=o)
        self.assertEqual(app.inst.thema, "rood-groen")
        self.assertEqual(o.instellingen_van(app.kind.id).thema, "rood-groen")

    def test_avatar_en_animaties_uitzetten(self):
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([OK, OK, hm("Opties"), ("klik", 15, 10), ("klik", 17, 10), ESC, ESC], opslag=o)
        inst = o.instellingen_van(app.kind.id)
        self.assertEqual((inst.avatar, inst.animaties), (False, False))
        self.assertTrue(self.ergens(scherm, "Animaties"))

    def test_knop_in_voetbalk(self):
        scherm, _ = self.speel([OK, OK, "2"])
        y, x = scherm.zoek("[Esc]")
        scherm2, _ = self.speel([OK, OK, "2", ("klik", y, x + 1), ESC])
        # na de klik op [Esc] staan we terug in het hoofdmenu
        self.assertIn("Wat wil je doen?", scherm2.beelden[-1])

    def test_broodkruimel_terug_naar_hoofdmenu(self):
        scherm, _ = self.speel([OK, OK, "2", "1", "1", ("klik", 0, 2), ESC])
        self.assertIn("Wat wil je doen?", scherm.beelden[-1])

    def test_scrollwiel_in_spiekbrief(self):
        scherm, _ = self.speel([OK, OK, hm("Spiekbrieven"), "1", *[("wiel", 1)] * 8, ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "VOORBEELD"))


class TestTypen(Basis):
    def test_accenten_typen(self):
        scherm, app = self.speel([OK, *"Zoë", OK, OK, ESC], opslag=self.opslag())
        self.assertEqual(app.kind.naam, "Zoë")

    def test_te_klein_venster(self):
        scherm, _ = self.speel([OK], hoogte=20, breedte=60)
        self.assertTrue(self.ergens(scherm, "te klein"))


if __name__ == "__main__":
    unittest.main()
