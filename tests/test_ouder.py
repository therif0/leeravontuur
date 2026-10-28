"""Schermtests voor het ouderdeel, de pincode en de timer."""

import os
import tempfile
from pathlib import Path

from leeravontuur.kern import wachtwoord
from leeravontuur.terminal.app import App
from leeravontuur.terminal.nepscherm import NepScherm, ToetsenOp
from leeravontuur.terminal.schermen import ouder
try:
    from .test_schermen import ESC, HOOFDMENU, OK, Basis, hm, naar
except ImportError:  # ook zo te starten: python -m unittest discover -s tests
    from test_schermen import ESC, HOOFDMENU, OK, Basis, hm, naar

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
        self.speel([*naar("wiskunde.meten.massa"), "1", OK, OK, "1", OK, OK, "1", OK, OK, ESC, ESC, ESC, ESC,
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
        return self.speel([OK, "3", *WW, OK, "3", "1", *toetsen, ESC, ESC, ESC, ESC, ESC], opslag=o)

    def test_leerjaar_wijzigen(self):
        o = self.met_wachtwoord(("Test", "5"))
        self.beheer(o, ("klik", 6, 10), "4")  # Leerjaar staat op rij 4 + 2*1; "4" = 6de leerjaar
        self.assertEqual(o.kinderen()[0].leerjaar, "6")

    def test_timer_verbergen(self):
        o = self.met_wachtwoord(("Test", "5"))
        self.beheer(o, ("klik", 10, 10))
        self.assertFalse(o.instellingen_van(o.kinderen()[0].id).timer_zichtbaar)

    def test_pincode_instellen_en_gebruiken(self):
        o = self.met_wachtwoord(("Test", "5"))
        self.beheer(o, ("klik", 12, 10), *"1234", OK, *"1234", OK)
        self.assertTrue(o.pincode(o.kinderen()[0].id))
        scherm, app = self.speel([OK, OK, *"9999", OK, *"1234", OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Typ je pincode"))
        self.assertTrue(self.ergens(scherm, "Niet juist"))
        self.assertEqual(app.kind.naam, "Test")

    def test_wissen_vraagt_de_naam(self):
        o = self.met_wachtwoord(("Test", "5"), ("Ander", "4"))
        # Wie ben jij?: 1 Ander, 2 Test, 3 Nieuw kind, 4 Ouders; wissen staat op rij 4 + 2*7 = 18
        self.speel([OK, "4", *WW, OK, "3", "1", ("klik", 18, 10), *"Fout", OK, OK, ("klik", 18, 10),
                    *"Ander", OK, OK, ESC, ESC, ESC, ESC], opslag=o)
        self.assertEqual([k.naam for k in o.kinderen()], ["Test"])

    def test_export_alles(self):
        o = self.met_wachtwoord(("Test", "5"))
        self.beheer(o, ("klik", 16, 10), OK)
        self.assertEqual(sorted(p.suffix for p in Path(self.docs.name).iterdir()), [".csv", ".json", ".txt"])


class TestWeergave(OuderBasis):
    """Ouders › Kinderen › kind › Weergave (rij 4 + 2*2 = 8): de instellingen die vroeger in Opties stonden.
    In de lijst: Eenvoudige tekens rij 4, Muis 6, Typrichting 8, Avatar 10, Animaties 12, Klokvenster 14,
    Plaatswaarden 16."""

    def weergave(self, o, *klikken, start=(OK, "3"), voorrang=None):
        toetsen = [*start, *WW, OK, "3", "1", ("klik", 8, 10), *[("klik", y, 10) for y in klikken],
                   ESC, ESC, ESC, ESC, ESC, ESC]
        return self.speel(toetsen, opslag=o, voorrang=voorrang)

    def test_avatar_en_animaties_uitzetten(self):
        o = self.met_wachtwoord(("Test", "5"))
        scherm, _ = self.weergave(o, 10, 12)
        inst = o.instellingen_van(o.kinderen()[0].id)
        self.assertEqual((inst.avatar, inst.animaties), (False, False))
        self.assertTrue(self.ergens(scherm, "Weergave voor Test"))
        self.assertTrue(self.ergens(scherm, "Klok in een eigen venster"))

    def test_plaatswaarden_aanzetten(self):
        """#18: de ouder zet de plaatswaarden bij cijferen aan (standaard uit)."""
        o = self.met_wachtwoord(("Test", "5"))
        self.assertFalse(o.instellingen_van(o.kinderen()[0].id).plaatswaarden)
        scherm, _ = self.weergave(o, 16)
        self.assertTrue(o.instellingen_van(o.kinderen()[0].id).plaatswaarden)
        self.assertTrue(self.ergens(scherm, "Plaatswaarden bij cijferen"))
        self.assertTrue(self.ergens(scherm, "aan (E T H … boven de kolommen)"))

    def test_alleen_voor_dat_kind(self):
        o = self.met_wachtwoord(("Ander", "4"), ("Test", "5"))
        self.weergave(o, 6, 8, 14, start=(OK, "4"))  # Wie ben jij?: 1 Ander, 2 Test, 3 Nieuw kind, 4 Ouders
        ander, test = (o.instellingen_van(k.id) for k in o.kinderen())
        self.assertEqual((ander.muis, ander.typrichting, ander.klokvenster), (False, -1, False))
        self.assertEqual((test.muis, test.typrichting, test.klokvenster), (True, 1, True))

    def test_startargument_wordt_niet_bewaard(self):
        """Gestart met --contrast; in Weergave de muis uitzetten: de muis wordt bewaard, het contrast niet."""
        o = self.met_wachtwoord(("Test", "5"))
        scherm, app = self.weergave(o, 6, voorrang={"thema": "contrast"})
        bewaard = o.instellingen_van(o.kinderen()[0].id)
        self.assertEqual(bewaard.thema, "standaard")
        self.assertFalse(bewaard.muis)
        self.assertEqual(app.inst.thema, "contrast")

    def test_ascii_startargument_blijft_voorgaan(self):
        """Met --ascii gestart, het actieve kind krijgt in Weergave 'Eenvoudige tekens uit': het scherm blijft ASCII."""
        o = self.met_wachtwoord(("Test", "5"))
        scherm, app = self.weergave(o, 4, 4, start=(OK, OK, hm("Stoppen"), OK, "3"), voorrang={"ascii": True})
        self.assertIs(o.instellingen_van(app.kind.id).ascii, False)
        self.assertTrue(app.inst.ascii)
        for beeld in scherm.beelden:
            self.assertTrue(all(ord(c) < 128 for c in beeld), beeld)


class TestTimer(OuderBasis):
    def vrije_vraag(self, zichtbaar):
        o = self.opslag(("Test", "5", {"timer_zichtbaar": zichtbaar}))
        scherm, _ = self.speel([*naar("wiskunde.meten.massa"), "1", OK, ESC, ESC, ESC, ESC, ESC, ESC],
                               opslag=o)
        return any(" s)" in b for b in scherm.beelden)

    def test_timer_zichtbaar(self):
        self.assertTrue(self.vrije_vraag(True))

    def test_timer_verborgen(self):
        self.assertFalse(self.vrije_vraag(False))


class TestZegHetOns(OuderBasis):
    def test_opmerking_bewaren_en_lezen(self):
        from leeravontuur.kern import feedback
        o = self.met_wachtwoord(("Imrane", "5"))
        tekst = "De breuken zijn leuk, maar 7/8 vs. 5/6 is moeilijk!"
        scherm, _ = self.speel([OK, OK, hm("Zeg het ons"), *tekst, OK, OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Bedankt!"))
        lijst = feedback.lees()
        self.assertEqual([(m["naam"], m["tekst"]) for m in lijst], [("Imrane", tekst)])
        # in het ouderdeel: Wie ben jij? → 3 Ouders, wachtwoord, 6 Opmerkingen
        scherm, _ = self.speel([OK, "3", *WW, OK, "6", ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Opmerkingen (1)"))
        self.assertTrue(self.ergens(scherm, "7/8 vs. 5/6"))

    def test_leeg_bewaart_niets_en_stoppen_met_een_cijfer(self):
        from leeravontuur.kern import feedback
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([OK, OK, hm("Zeg het ons"), OK, hm("Stoppen"), ESC, "x"], opslag=o)
        self.assertEqual(feedback.lees(), [])
        self.assertEqual(hm("Stoppen"), str(len(HOOFDMENU) % 10))  # de laatste keuze
        self.assertEqual(scherm.toetsen, ["x"])  # Stoppen → titelscherm, Esc: gestopt (x niet meer gelezen)


class TestAntwoorden(OuderBasis):
    """#24: Ouders › Antwoorden › kind: elke vraag met het antwoord; Enter = details, H = in de herhaalbak."""

    def met_antwoorden(self):
        from leeravontuur.kern.sessie import Sessie
        o = self.met_wachtwoord(("Test", "5"))
        kind = o.kinderen()[0]
        with Sessie(o, kind.id, "reeks", "wiskunde.hoofdrekenen.tafels", "5") as ses:
            for i, (gegeven, juist) in enumerate([("56", True), ("54", False)]):
                ses.vraag_getoond()
                ses.antwoord(f"wiskunde.hoofdrekenen.tafels:t7:{i}", "7 × 8 = ?", gegeven, juist,
                             None if juist else "tafel_te_weinig", verwacht="56")
        return o, kind

    def test_lijst_details_en_herhaalbak(self):
        o, kind = self.met_antwoorden()
        scherm, _ = self.speel([OK, "3", *WW, OK, "2", "1", "h", OK, "h", ESC, ESC, ESC, ESC, ESC], opslag=o)
        lijst = next(b for b in scherm.beelden if "Laatste antwoorden van Test" in b)
        self.assertIn("✘  Maal- en deeltafels · 7 × 8 = 54  (juist: 56)", lijst)
        self.assertIn("✔  Maal- en deeltafels · 7 × 8 = 56", lijst)
        self.assertTrue(self.ergens(scherm, "✔ Deze vraag komt morgen terug bij Herhalen (met nieuwe getallen)."))
        details = next(b for b in scherm.beelden if "Vraag:     7 × 8 = ?" in b)
        self.assertIn("✘  (juist: 56)", details)
        self.assertIn("In de herhaalbak: ja", details)
        self.assertTrue(self.ergens(scherm, "Deze soort vraag staat al in de herhaalbak."))
        self.assertEqual([i["vaardigheid"] for i in o.herhaalbak(kind.id)], ["wiskunde.hoofdrekenen.tafels"])

    def test_punten_tonen_de_vraag(self):
        o, _ = self.met_antwoorden()
        scherm, _ = self.speel([OK, "3", *WW, OK, "4", "1", ESC, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "juist antwoord · 7 × 8 = 56"))

    def test_zonder_antwoorden(self):
        o = self.met_wachtwoord(("Test", "5"))
        scherm, _ = self.speel([OK, "3", *WW, OK, "2", "1", "h", OK, ESC, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Nog geen antwoorden."))
