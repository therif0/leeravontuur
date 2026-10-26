"""Schermtests zonder echte terminal: toetsen, muisklikken en het scrollwiel via NepScherm."""

import curses
import os
import tempfile
import unittest

from leeravontuur.kern.instellingen import Instellingen
from leeravontuur.kern.opslag import Opslag
from leeravontuur.terminal.app import App
from leeravontuur.terminal.nepscherm import NepKlokvenster, NepScherm, ToetsenOp
from leeravontuur.terminal.schermen.eenheden import TABEL_X, TABEL_Y

ESC = "\x1b"
OK = "\n"

# keuzes in het hoofdmenu (als toets)
HOOFDMENU = ["▶ Verder", "Leren & oefenen", "Snelrekenen", "Herhalen", "Mijn avatar", "Spiekbrieven", "Opties",
             "Wissel van kind", "Zeg het ons", "Stoppen"]


def hm(keuze):
    """De toets voor een keuze in het hoofdmenu (de 10de keuze heeft toets 0)."""
    return str((HOOFDMENU.index(keuze) + 1) % 10)


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

    def speel(self, toetsen, opslag=None, voorrang=None, klokvenster=None, **scherm_opties):
        """Speelt de toetsen af. Geeft (nepscherm, app). Stopt netjes als de toetsen op zijn.
        klokvenster: een NepKlokvenster (anders tekent de terminal de klok, zoals zonder beeldscherm)."""
        scherm = NepScherm(toetsen, **scherm_opties)
        app = App(scherm, opslag or self.opslag(("Test", "5")), voorrang, kleuren=False)
        app.s.klokvenster = klokvenster
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

    def test_zelf_kiezen_met_het_toetsenbord(self):
        # Eenheden → Vrij oefenen → Zelf kiezen: met → naar de 5de kolom (volume), m³ en dm³ aanvinken
        toetsen = [OK, OK, "2", "1", "1", "1", "7", *[curses.KEY_RIGHT] * 4, " ", curses.KEY_DOWN, " ", OK, "3",
                   ESC, ESC, ESC, ESC, ESC, ESC]
        scherm, _ = self.speel(toetsen)
        self.assertTrue(self.ergens(scherm, "[x] m³"))
        self.assertTrue(self.ergens(scherm, "[x] dm³"))
        self.assertTrue(self.ergens(scherm, "dm³  =") or self.ergens(scherm, "m³  ="))

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


class TestVraagstuk(Basis):
    """Leren › Wiskunde › Vraagstukken › Vrij oefenen, met een vast vraagstuk."""

    def setUp(self):
        super().setUp()
        import random
        from unittest import mock
        from leeravontuur.kern.wiskunde import vraagstukken as VS
        o = VS.VRAAGSTUKKEN
        self.v = o.maak_met(o.parameters("5"), random.Random(8), {"structuur": "wisselgeld", "variant": "meer"})
        patch = mock.patch.object(o, "maak", return_value=self.v)
        patch.start()
        self.addCleanup(patch.stop)

    def start(self):
        return [OK, OK, "2", "1", "9", "1", "1", "2"]  # Vraagstukken → Vraagstukken oplossen → Vrij → Normaal

    def antwoord(self, x):
        return list(str(x).replace(".", ","))

    def test_meteen_juist(self):
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.start(), "a", *self.antwoord(self.v.antwoord), OK, ESC, ESC, ESC, ESC, ESC],
                                 opslag=o)
        self.assertTrue(self.ergens(scherm, "Het verhaal"))
        self.assertTrue(self.ergens(scherm, "Oplossing:"))
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual((rij["juist"], rij["vaardigheid"]), (1, "wiskunde.vraagstukken.oplossen"))
        self.assertIn('"tips": 0', rij["extra"])
        self.assertEqual(o.punten_saldo(app.kind.id), 25)  # 2 × 10 + 5 zonder tip

    def test_tweede_kans_en_tips(self):
        o = self.opslag(("Test", "5"))
        fout = self.v.model.stappen[0].uitkomst  # de tussenuitkomst
        toetsen = [*self.start(), "?", "?", "a", *self.antwoord(fout), OK]
        scherm, _ = self.speel(toetsen + [ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "nog niet klaar"))
        self.assertTrue(self.ergens(scherm, "Tip 2: gevraagd is het wisselgeld"))
        toetsen += [9, 9, 9, *self.antwoord(self.v.antwoord), OK]
        scherm, app = self.speel(toetsen + [ESC, ESC, ESC, ESC, ESC], opslag=o)
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual(rij["juist"], 1)
        self.assertIn('"tips": 2', rij["extra"])
        self.assertEqual(rij["hulp"], 1)
        self.assertEqual(o.punten_saldo(app.kind.id), 5)  # (2 × 10) : 2 − 2 × 3 = 4 → minstens 5
        self.assertEqual(len(o.herhaalbak(app.kind.id)), 1)  # pas na een tweede kans: herhalen

    def test_aanduiden_met_de_muis_en_ascii(self):
        scherm, _ = self.speel([*self.start()], voorrang={"ascii": True})
        beeld = next(b for b in scherm.beelden if "Het verhaal" in b).split("\n")
        y = next(i for i, regel in enumerate(beeld) if "koopt" in regel)
        x = beeld[y].index("koopt") + len("koopt ")
        scherm, _ = self.speel([*self.start(), ("klik", y, x), ESC, ESC, ESC, ESC], voorrang={"ascii": True})
        self.assertTrue(self.ergens(scherm, "het aantal"))
        for beeld in scherm.beelden:
            self.assertTrue(all(ord(c) < 128 for c in beeld), beeld)


class TestSpeurneusEnSchatten(Basis):
    def test_speurneus(self):
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([OK, OK, "2", "1", "9", "2", "1", "2", "0", OK, ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "loste het zo op"))
        self.assertTrue(self.ergens(scherm, "Alles is juist!"))
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual((rij["vaardigheid"], rij["gegeven"]), ("wiskunde.vraagstukken.speurneus", "alles is juist"))

    def test_schatten_met_de_muis(self):
        import random
        from unittest import mock
        from leeravontuur.kern.wiskunde import vraagstukken as VS
        v = VS.SCHATTEN.maak("5", rng=random.Random(3))
        patch = mock.patch.object(VS.SCHATTEN, "maak", return_value=v)
        patch.start()
        self.addCleanup(patch.stop)
        o = self.opslag(("Test", "5"))
        scherm, _ = self.speel([OK, OK, "2", "1", "9", "3", "1", "2"], opslag=o)
        beeld = next(b for b in reversed(scherm.beelden) if "a) " in b).split("\n")
        y = next(i for i, regel in enumerate(beeld) if "a) " in regel)
        scherm, app = self.speel([OK, OK, "2", "1", "9", "3", "1", "2", ("klik", y, 8), ESC, ESC, ESC, ESC, ESC],
                                 opslag=o)
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual(rij["vaardigheid"], "wiskunde.vraagstukken.schatten")
        self.assertTrue(rij["gegeven"].startswith("a)"))


class TestKlok(Basis):
    """Leren › Wiskunde › Tijd, geld en snelheid › De klok › Vrij oefenen, met een vaste vraag."""
    START = [OK, OK, "2", "1", "7", "4", "1", "2"]

    def vaste_vraag(self, soort, t):
        import random
        from decimal import Decimal
        from unittest import mock
        from leeravontuur.kern.modellen import Wijzerklok
        from leeravontuur.kern.wiskunde import klok as K
        v = K.KLOK.maak_met(K.KLOK.parameters("5"), random.Random(1), {"soort": soort, "t": t})
        if v.data.get("t") != t:  # de soort kiest zelf een tijd: zet ze vast
            v.data["t"], v.antwoord = t, Decimal(t)
            v.verwacht_tekst = K.woorden(t) if soort == "naar_woorden" else K.klok12(t)
            if isinstance(v.model, Wijzerklok) and soort != "zetten":
                v.model = Wijzerklok(t)
        patch = mock.patch.object(K.KLOK, "maak", return_value=v)
        patch.start()
        self.addCleanup(patch.stop)
        return v

    def test_lezen_ook_in_ascii(self):
        self.vaste_vraag("lezen", 3 * 60 + 25)
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.START, *"3.25", OK, ESC, ESC, ESC, ESC, ESC], opslag=o,
                                 voorrang={"ascii": True})
        self.assertTrue(self.ergens(scherm, "Hoe laat"))
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual((rij["vaardigheid"], rij["juist"]), ("wiskunde.eenheden.klok", 1))
        for beeld in scherm.beelden:
            self.assertTrue(all(ord(c) < 128 for c in beeld), beeld)

    def test_half_vier_is_geen_half_vijf(self):
        v = self.vaste_vraag("woorden_naar", 3 * 60 + 30)
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.START, *"4.30", OK, *"4.30", OK, ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Half vier is een half uur"))  # het hulpje bij de tweede kans
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual((rij["juist"], rij["diagnose"], rij["gegeven"]), (0, "klok_half", "4.30"), v.tekst)
        self.assertIn('"eerste_fout": "4.30"', rij["extra"])

    def test_in_woorden(self):
        self.vaste_vraag("naar_woorden", 3 * 60 + 25)
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.START, *"vijf voor half vier", OK, ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertEqual(o.antwoorden(app.kind.id)[-1]["juist"], 1)

    def test_wijzers_zetten(self):
        v = self.vaste_vraag("zetten", 7 * 60 + 40)
        stappen = (int(v.antwoord) - int(v.model.minuten)) % 720
        toetsen = [ord("+")] * (stappen // 60) + [curses.KEY_RIGHT] * (stappen % 60)
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.START, *toetsen, OK, ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertEqual(o.antwoorden(app.kind.id)[-1]["juist"], 1)
        beeld = next(b for b in scherm.beelden if "Zet de klok" in b).split("\n")
        self.assertIn("[Enter]", beeld[-1])  # de hint staat niet over de knoppen


class TestKlokvenster(TestKlok):
    """De klok in een eigen venster (zonder echt proces): de terminal verwijst ernaar, klikken en toetsen uit het
    venster komen in de oefening, en zonder klok in beeld verdwijnt het venster."""

    def test_lezen_in_het_venster(self):
        self.vaste_vraag("lezen", 3 * 60 + 25)
        o = self.opslag(("Test", "5"))
        kv = NepKlokvenster([{"toets": "3"}, {"toets": "."}, {"toets": "2"}, {"toets": "5"}, {"toets": "Enter"}])
        scherm, app = self.speel([*self.START, ("wacht",), ("wacht",), ("wacht",), ("wacht",), ("wacht",),
                                  ("wacht",), ("wacht",), ESC, ESC, ESC, ESC, ESC], opslag=o, klokvenster=kv)
        self.assertTrue(self.ergens(scherm, "De klok staat in een eigen venster"))
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual((rij["gegeven"], rij["juist"]), ("3.25", 1))
        getoond = [b for b in kv.gekregen if b.get("doe") == "toon"]
        self.assertEqual(getoond[0]["minuten"], 205)
        self.assertEqual(getoond[0]["tekst"], "Hoe laat is het op de klok?")
        self.assertEqual(getoond[-1]["uitslag"], "goed")
        self.assertEqual(kv.gekregen[-1], {"doe": "verberg"})  # terug in het menu: het venster weg

    def test_wijzers_zetten_met_een_klik_in_het_venster(self):
        v = self.vaste_vraag("zetten", 7 * 60)
        o = self.opslag(("Test", "5"))
        # de lange wijzer recht naar boven, Enter (fout? dan een tweede kans: nog eens Enter)
        kv = NepKlokvenster([{"klik": [0, -80]}, {"toets": "Enter"}, {"toets": "Enter"}])
        scherm, app = self.speel([*self.START, ("wacht",), ("wacht",), ("wacht",), ("wacht",), ESC, ESC, ESC, ESC, ESC],
                                 opslag=o, klokvenster=kv)
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertTrue(rij["gegeven"].endswith(".00 u") or rij["gegeven"].endswith(".00"), rij["gegeven"])
        toon = [b for b in kv.gekregen if b.get("doe") == "toon"]
        self.assertTrue(toon[0]["klikbaar"])
        if not rij["juist"]:  # het uur stond anders: dan tonen groene wijzers hoe het moest
            self.assertEqual(toon[-1]["juist"], int(v.antwoord) % 720)

    def test_venster_gesloten_dan_klok_in_de_terminal(self):
        self.vaste_vraag("lezen", 3 * 60 + 25)
        kv = NepKlokvenster([{"dicht": True}])
        scherm, _ = self.speel([*self.START, ("wacht",), ("wacht",), ESC, ESC, ESC, ESC], klokvenster=kv)
        laatste = next(b for b in reversed(scherm.beelden) if "Hoe laat is het" in b)
        self.assertNotIn("klokvenster", laatste)
        self.assertIn("12", laatste)  # de wijzerplaat in de terminal

    def test_f2_klok_in_de_terminal_en_terug(self):
        self.vaste_vraag("lezen", 3 * 60 + 25)
        kv = NepKlokvenster()
        scherm, _ = self.speel([*self.START, curses.KEY_F2, ESC, ESC, ESC, ESC], klokvenster=kv)
        vragen = [b for b in scherm.beelden if "Hoe laat is het" in b]
        self.assertIn("Zie je hem niet? Druk F2", vragen[0])
        self.assertNotIn("eigen venster", vragen[-1])  # nu de klok in de terminal
        self.assertIn({"doe": "verberg"}, kv.gekregen)
        self.assertTrue(kv.in_terminal)  # en dat blijft zo, ook bij de volgende vraag
        kv = NepKlokvenster()
        scherm, _ = self.speel([*self.START, curses.KEY_F2, curses.KEY_F2, ESC, ESC, ESC, ESC], klokvenster=kv)
        self.assertIn("eigen venster", [b for b in scherm.beelden if "Hoe laat is het" in b][-1])  # terug

    def test_tekst_blijft_links_van_het_venster(self):
        self.vaste_vraag("later", 8 * 60 + 50)
        kv = NepKlokvenster()
        scherm, _ = self.speel([*self.START, *"1.00", OK, *"1.00", OK, ESC, ESC, ESC, ESC], klokvenster=kv)
        nagekeken = next(b for b in scherm.beelden if "Niet juist" in b)
        beeld = nagekeken.split("\n")
        for regel in beeld[11:23]:  # onder het oefenmaatje: de feedback en de uitleg
            self.assertLessEqual(len(regel.rstrip()), 60, regel)

    def test_versleepte_plek_onthouden(self):
        o = self.opslag(("Test", "5"))
        bewaard = []
        kv = NepKlokvenster([{"plek": [10, 20, 300, 390]}])
        kv.bij_plek = bewaard.append
        self.vaste_vraag("lezen", 3 * 60 + 25)
        self.speel([*self.START, ("wacht",), ("wacht",), ESC, ESC, ESC, ESC], opslag=o, klokvenster=kv)
        self.assertEqual(bewaard, [[10, 20, 300, 390]])


class TestWerkwijze(Basis):
    """De vaste werkwijze in elke oefening: klad met Tab, getrapte tips, een tweede kans en "Zo kan het:"."""

    def naar(self, o):
        """De toetsen tot vrij oefenen op Normaal in onderwerp o (gezocht in de domeinen van Wiskunde)."""
        scherm = NepScherm([])
        app = App(scherm, self.opslag(), kleuren=False)
        for i, (_, _, onderwerpen, _) in enumerate(app.domeinen(), 1):
            if onderwerpen and o in onderwerpen:
                stap = [str(onderwerpen.index(o) + 1)] if len(onderwerpen) > 1 else []
                return [OK, OK, "2", "1", str(i % 10), *stap, "1", "2"]
        raise AssertionError(o.id)

    def vast(self, o, v):
        from unittest import mock
        patch = mock.patch.object(o, "maak", return_value=v)
        patch.start()
        self.addCleanup(patch.stop)
        return self.naar(o)

    def plusmin(self):
        from decimal import Decimal
        from leeravontuur.kern.onderwerp import Vraag
        from leeravontuur.kern.wiskunde import hoofdrekenen as H
        v = Vraag(H.PLUSMIN.id, f"{H.PLUSMIN.id}:plus compenseren:47+99", "47 + 99 =", Decimal(146),
                  data={"a": "47", "b": "99", "op": "+", "strategie": "compenseren", "rond": 100, "verschil": 1,
                        "schaal": 1, "onderwerp": "plus compenseren"})
        return self.vast(H.PLUSMIN, v)

    def test_klad_met_tab_en_dan_antwoorden(self):
        o = self.opslag(("Test", "5"))
        toetsen = [*self.plusmin(), TAB, *"47 + 100 = 147", OK, *"147 - 1 = 146", OK, TAB, *"146", OK]
        scherm, app = self.speel(toetsen + [ESC] * 5, opslag=o)
        self.assertTrue(self.ergens(scherm, "▸ Klad"))
        self.assertTrue(self.ergens(scherm, "147 − 1 = 146"))  # netjes, met ✔
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual(rij["juist"], 1)
        self.assertIn('"klad_ok": true', rij["extra"])
        self.assertEqual(o.punten_saldo(app.kind.id), 12)  # 10 + 2 voor een juist klad

    def test_lege_regel_in_het_klad_gaat_terug_naar_het_antwoord(self):
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.plusmin(), TAB, OK, *"146", OK, ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertEqual(o.antwoorden(app.kind.id)[-1]["gegeven"], "146")

    def test_tweede_kans_halve_punten_en_herhaalbak(self):
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.plusmin(), *"148", OK, *"146", OK, ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Bij compenseren moest je 1 aftrekken"))  # het hulpje
        self.assertTrue(self.ergens(scherm, "Maak eens"))  # … klad (Tab): de regel loopt door
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual((rij["juist"], len(o.antwoorden(app.kind.id))), (1, 1))  # één antwoord, juist
        self.assertIn('"eerste_fout": "148"', rij["extra"])
        self.assertEqual(o.punten_saldo(app.kind.id), 5)  # de helft
        self.assertEqual(len(o.herhaalbak(app.kind.id)), 1)

    def test_twee_keer_fout_zo_kan_het(self):
        scherm, _ = self.speel([*self.plusmin(), *"148", OK, *"148", OK, ESC, ESC, ESC, ESC, ESC])
        beeld = next(b for b in scherm.beelden if "Zo kan het:" in b)
        self.assertIn("47 + 100 = 147", beeld)
        self.assertIn("147 − 1 = 146", beeld)

    def test_tips_getrapt(self):
        scherm, _ = self.speel([*self.plusmin(), "?", "?", "?", ESC, ESC, ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Tip 1: Maak er eerst een rond getal van"))
        self.assertTrue(self.ergens(scherm, "Tip 2: Begin je klad zo: 47 + 100 = …"))
        self.assertTrue(self.ergens(scherm, "Tip 3: schrijf je eerste stap in het klad"))

    def test_klik_op_het_klad(self):
        toetsen = self.plusmin()
        scherm, _ = self.speel(toetsen)
        beeld = next(b for b in scherm.beelden if "Klad (Tab)" in b).split("\n")
        y = next(i for i, r in enumerate(beeld) if "Klad (Tab)" in r)
        scherm, _ = self.speel([*toetsen, ("klik", y, beeld[y].index("Klad") + 1), *"1 + 1 = 2", OK])
        self.assertTrue(self.ergens(scherm, "✔ Deze regel klopt."))

    def test_ja_nee_zonder_tweede_kans(self):
        from decimal import Decimal
        from leeravontuur.kern.onderwerp import Vraag
        from leeravontuur.kern.wiskunde import getallen as G
        v = Vraag(G.DEELBAARHEID.id, f"{G.DEELBAARHEID.id}:deelbaar:4677:3", "Is 4 677 deelbaar door 3? (ja of nee)",
                  "ja", data={"soort": "deelbaar", "onderwerp": "deelbaar door 3", "deler": 3, "n": 4677},
                  invoer="janee")
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.vast(G.DEELBAARHEID, v), *"nee", OK, ESC, ESC, ESC, ESC, ESC], opslag=o)
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual(rij["juist"], 0)  # meteen nagekeken: bij ja of nee is een tweede kans raden
        self.assertTrue(self.ergens(scherm, "Niet juist"))

    def test_splitsen_eerst_het_klad(self):
        from decimal import Decimal
        from leeravontuur.kern.onderwerp import Vraag
        from leeravontuur.kern.wiskunde import hoofdrekenen as H
        v = Vraag(H.SPLITSEN.id, f"{H.SPLITSEN.id}:deel_splitsen:91:7", "91 : 7 =", Decimal(13),
                  data={"soort": "deel_splitsen", "a": "91", "f": "7", "op": ":", "delen": ["70", "21"],
                        "onderwerp": "deel_splitsen"})
        o = self.opslag(("Test", "5"))
        toetsen = [*self.vast(H.SPLITSEN, v), TAB, *"13", OK]  # het klad staat open: Tab = naar het antwoord
        scherm, app = self.speel(toetsen + [ESC] * 5, opslag=o)
        self.assertTrue(self.ergens(scherm, "Laat in je klad zien hoe je splitst"))
        self.assertEqual(o.antwoorden(app.kind.id), [])  # telt niet als poging
        toetsen += [*"70 : 7 = 10", OK, *"21 : 7 = 3", OK, TAB, OK]
        scherm, app = self.speel(toetsen + [ESC] * 5, opslag=o)
        self.assertEqual(o.antwoorden(app.kind.id)[-1]["juist"], 1)

    def test_elk_rekenonderwerp_past_met_het_klad_open(self):
        """In elk leerjaar: 6 klad-regels en 3 tips, en alles blijft binnen 80 × 24 (de knoppen blijven zichtbaar)."""
        import random
        from leeravontuur.kern.leerjaren import LEERJAREN
        from leeravontuur.kern.onderwerp import ONDERWERPEN
        for oid, o in ONDERWERPEN.items():
            if not o.klad:
                continue
            for jaar in LEERJAREN[:-1]:
                if not o.aangeboden(jaar):
                    continue
                v = next((v for v in (o.maak(jaar, rng=random.Random(z)) for z in range(40)) if o.klad_voor(v)), None)
                if v is None or v.invoer in INVOER_OBJECTEN:
                    continue
                with self.subTest(oid=oid, jaar=jaar, vraag=v.tekst):
                    from unittest import mock
                    with mock.patch.object(o, "maak", return_value=v):
                        regels = [k for _ in range(6) for k in [*"12 + 3 = 15", OK]]
                        toetsen = [*self.naar(o)] + ([] if o.klad_voor(v) == "verplicht" else [TAB])
                        scherm, _ = self.speel([*toetsen, *regels, "?", "?", "?"])
                    beeld = next(b for b in reversed(scherm.beelden) if "Klad" in b).split("\n")
                    self.assertEqual(len(beeld), 24)
                    self.assertTrue(beeld[-1].startswith(" [Tab]"), beeld[-1])
                    tip = next(i for i, r in enumerate(beeld) if "Tip 3" in r)
                    self.assertLess(tip, 23)


TAB = 9
INVOER_OBJECTEN = {"rooster", "staart", "vraagstuk", "speur", "keuze", "balk", "veld", "coord", "wijzers", "lijn"}


class TestTypen(Basis):
    def test_broodkruimel_bij_een_nieuw_kind(self):
        """Een klik op "Wie ben jij?" terwijl je je naam typt: terug naar de keuze, nooit een fout."""
        scherm, app = self.speel([OK, ("klik", 0, 16), ("klik", 0, 2), *"Zoë", OK, OK, ESC], opslag=self.opslag())
        self.assertTrue(self.ergens(scherm, "Hallo! Hoe heet je?"))
        self.assertEqual(app.kind.naam, "Zoë")

    def test_accenten_typen(self):
        scherm, app = self.speel([OK, *"Zoë", OK, OK, ESC], opslag=self.opslag())
        self.assertEqual(app.kind.naam, "Zoë")

    def test_te_klein_venster(self):
        scherm, _ = self.speel([OK], hoogte=20, breedte=60)
        self.assertTrue(self.ergens(scherm, "te klein"))


if __name__ == "__main__":
    unittest.main()
