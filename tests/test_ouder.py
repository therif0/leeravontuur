"""Schermtests voor het ouderdeel, de pincode en de timer."""

import os
import tempfile
from pathlib import Path

from leeravontuur.kern import wachtwoord
from leeravontuur.terminal.app import App
from leeravontuur.terminal.nepscherm import NepScherm, ToetsenOp
from leeravontuur.terminal.schermen import ouder
from test_schermen import ESC, OK, Basis

WW = "geheim1"


class OuderBasis(Basis):
    def setUp(self):
        super().setUp()
        self.oude_iteraties = wachtwoord.ITERATIES
        wachtwoord.ITERATIES = 1000  # tests snel houden
        self.docs = tempfile.TemporaryDirectory()
        os.environ["LEERAVONTUUR_DOCUMENTEN"] = self.docs.name

    def tearDown(self):
        wachtwoord.ITERATIES = self.oude_iteraties
        os.environ.pop("LEERAVONTUUR_DOCUMENTEN", None)
        self.docs.cleanup()
        super().tearDown()

    def met_wachtwoord(self, *kinderen):
        o = self.opslag(*kinderen)
        o.zet_ouder_wachtwoord(wachtwoord.maak(WW))
        return o


class TestToegang(OuderBasis):
    def test_eerste_keer_wachtwoord_kiezen(self):
        o = self.opslag(("Test", "5"))
        # Wie ben jij?: 1 Test, 2 Nieuw kind, 3 Ouders
        scherm, _ = self.speel([OK, "3", *WW, OK, *WW, OK, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Ouderdeel"))
        self.assertTrue(wachtwoord.controleer(WW, o.ouder_wachtwoord()))

    def test_verschillende_wachtwoorden(self):
        o = self.opslag(("Test", "5"))
        scherm, _ = self.speel([OK, "3", *WW, OK, *"ander1", OK, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "niet gelijk"))
        self.assertIsNone(o.ouder_wachtwoord())

    def test_drie_keer_fout(self):
        o = self.met_wachtwoord(("Test", "5"))
        fout = [*"fout", OK]
        scherm, _ = self.speel([OK, "3", *fout, *fout, *fout, OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Drie keer een verkeerd wachtwoord"))
        self.assertFalse(self.ergens(scherm, "Rapporten"))

    def test_vergrendelen_na_inactiviteit(self):
        o = self.met_wachtwoord(("Test", "5"))
        oud = ouder.SLOT_SECONDEN
        ouder.SLOT_SECONDEN = 1e-9
        try:
            scherm, _ = self.speel([OK, "3", *WW, OK, ("wacht",), OK, ESC], opslag=o)
        finally:
            ouder.SLOT_SECONDEN = oud
        self.assertTrue(self.ergens(scherm, "vergrendeld"))

    def test_meteen_ouderdeel_met_argument(self):
        o = self.met_wachtwoord(("Test", "5"))
        scherm = NepScherm([OK, *WW, OK, ESC])
        app = App(scherm, o, kleuren=False)
        app.start(ouder=True)  # komt terug zonder ToetsenOp: na Esc stopt het programma
        self.assertTrue(any("Ouderdeel" in b for b in scherm.beelden))


class TestRapportenScherm(OuderBasis):
    def test_rapport_export_en_kalender(self):
        o = self.met_wachtwoord(("Test", "5"))
        # eerst als kind 3 vragen vrij oefenen
        self.speel([OK, OK, "1", "1", "1", "1", "1", OK, "1", OK, OK, "1", OK, OK, "1", OK, OK, ESC, ESC, ESC, ESC,
                    ESC, ESC], opslag=o)
        toetsen = [OK, "3", *WW, OK, "1", "1", "1", "e", OK, "k", ESC, ESC, ESC, ESC, ESC, ESC]
        scherm, _ = self.speel(toetsen, opslag=o)
        self.assertTrue(self.ergens(scherm, "SAMENVATTING"))
        self.assertTrue(self.ergens(scherm, "Vragen: 3"))
        self.assertTrue(self.ergens(scherm, "Het rapport is opgeslagen"))
        bestanden = sorted(p.suffix for p in Path(self.docs.name).iterdir())
        self.assertEqual(bestanden, [".csv", ".txt"])
        self.assertTrue(self.ergens(scherm, "Gekleurde dagen"))


class TestKinderenBeheren(OuderBasis):
    def beheer(self, o, *toetsen):
        """Ouderdeel → Kinderen → eerste kind, dan de gegeven toetsen."""
        return self.speel([OK, "3", *WW, OK, "2", "1", *toetsen, ESC, ESC, ESC, ESC, ESC], opslag=o)

    def test_leerjaar_wijzigen(self):
        o = self.met_wachtwoord(("Test", "5"))
        self.beheer(o, ("klik", 6, 10), "4")  # Leerjaar staat op rij 4 + 2*1; "4" = 6de leerjaar
        self.assertEqual(o.kinderen()[0].leerjaar, "6")

    def test_timer_verbergen(self):
        o = self.met_wachtwoord(("Test", "5"))
        self.beheer(o, ("klik", 8, 10))
        self.assertFalse(o.instellingen_van(o.kinderen()[0].id).timer_zichtbaar)

    def test_pincode_instellen_en_gebruiken(self):
        o = self.met_wachtwoord(("Test", "5"))
        self.beheer(o, ("klik", 10, 10), *"1234", OK, *"1234", OK)
        self.assertTrue(o.pincode(o.kinderen()[0].id))
        scherm, app = self.speel([OK, OK, *"9999", OK, *"1234", OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Typ je pincode"))
        self.assertTrue(self.ergens(scherm, "Niet juist"))
        self.assertEqual(app.kind.naam, "Test")

    def test_wissen_vraagt_de_naam(self):
        o = self.met_wachtwoord(("Test", "5"), ("Ander", "4"))
        # Wie ben jij?: 1 Ander, 2 Test, 3 Nieuw kind, 4 Ouders; wissen staat op rij 4 + 2*5 = 14
        self.speel([OK, "4", *WW, OK, "2", "1", ("klik", 14, 10), *"Fout", OK, OK, ("klik", 14, 10),
                    *"Ander", OK, OK, ESC, ESC, ESC, ESC], opslag=o)
        self.assertEqual([k.naam for k in o.kinderen()], ["Test"])

    def test_export_alles(self):
        o = self.met_wachtwoord(("Test", "5"))
        self.beheer(o, ("klik", 12, 10), OK)
        self.assertEqual(sorted(p.suffix for p in Path(self.docs.name).iterdir()), [".csv", ".json", ".txt"])


class TestTimer(OuderBasis):
    def vrije_vraag(self, zichtbaar):
        o = self.opslag(("Test", "5", {"timer_zichtbaar": zichtbaar}))
        scherm, _ = self.speel([OK, OK, "1", "1", "1", "1", "1", OK, "1", OK, ESC, ESC, ESC, ESC, ESC, ESC],
                               opslag=o)
        return any(" s)" in b for b in scherm.beelden)

    def test_timer_zichtbaar(self):
        self.assertTrue(self.vrije_vraag(True))

    def test_timer_verborgen(self):
        self.assertFalse(self.vrije_vraag(False))
