"""Schermtests zonder echte terminal: toetsen, muisklikken en het scrollwiel via NepScherm."""

import curses
import os
import tempfile
import unittest

from leeravontuur.kern.instellingen import Instellingen
from leeravontuur.kern.opslag import Opslag
from leeravontuur.terminal import curriculum as CU
from leeravontuur.terminal.app import App
from leeravontuur.terminal.nepscherm import NepKlokvenster, NepScherm, ToetsenOp
from leeravontuur.terminal.scherm import Scherm
from leeravontuur.terminal.schermen.eenheden import TABEL_X, TABEL_Y

ESC = "\x1b"
OK = "\n"
F1 = curses.KEY_F1  # de hulp-toets (tip, hulp, spiekbrief); ? typt gewoon een vraagteken (0.21.7)

# keuzes in het hoofdmenu (als toets), in groepen (0.23): Verder, Herhalen · VAKKEN · JIJ · FEEDBACK · Stoppen
HOOFDMENU = ["▶ Verder", "Herhalen", *[v.label for v in CU.VAKKEN], *[label for label, _ in CU.BINNENKORT],
             "Leerstof", "Mijn avatar", "Winkel", "Zeg het ons", "Stoppen"]
# de rijen op het scherm (met de kopjes VAKKEN, JIJ, FEEDBACK en de lege regels ertussen)
HOOFDMENU_RIJEN = [5, 6, *range(9, 9 + len(CU.VAKKEN) + len(CU.BINNENKORT) + 1)]
HOOFDMENU_RIJEN += [HOOFDMENU_RIJEN[-1] + 3, HOOFDMENU_RIJEN[-1] + 4, HOOFDMENU_RIJEN[-1] + 7, HOOFDMENU_RIJEN[-1] + 9]


def hm(keuze):
    """De toets voor een keuze in het hoofdmenu (de 10de keuze heeft toets 0)."""
    return str((HOOFDMENU.index(keuze) + 1) % 10)


def hm_rij(keuze):
    """De schermrij van een keuze in het hoofdmenu (voor een muisklik)."""
    return HOOFDMENU_RIJEN[HOOFDMENU.index(keuze)]


def menu_onderwerp(o):
    """Het onderwerp in het leerplan: een menu-id, of een onderwerp uit de kern (gevonden via opslag)."""
    return CU.zoek(o) if isinstance(o, str) else CU.van_opslag(o.id)[0]


def naar(o, toets="v", niveau=OK, start=(OK, OK)):
    """Van het startscherm tot de oefening: Vak › Domein › Onderwerp + toets (v vrij, Enter reeks …),
    dan Normaal in "Hoe moeilijk?" (niveau=None: geen niveaukeuze, bv. snelrekenen of zelf kiezen)."""
    m = menu_onderwerp(o)
    d = CU.domein_van(m)
    v = CU.vak_van(d)
    i = d.onderwerpen.index(m)
    keuze = [str((i + 1) % 10)] if toets == "Enter" else [*[curses.KEY_DOWN] * i, toets]
    return [*start, hm(v.label), str(v.domeinen.index(d) + 1), *keuze, *([niveau] if niveau else [])]


def na_het_kader(scherm):
    """Het eerste beeld na het (laatste) kader "Wil je stoppen?" (#33)."""
    i = max(i for i, b in enumerate(scherm.beelden) if "Wil je stoppen" in b)
    return next(b for b in scherm.beelden[i + 1:] if "Wil je stoppen" not in b)


def plek(scherm, tekst):
    """(rij, kolom) van tekst in het laatste beeld waarin hij staat (ook als het scherm daarna nog veranderde)."""
    for beeld in reversed(scherm.beelden):
        for y, regel in enumerate(beeld.splitlines()):
            if tekst in regel:
                return y, regel.index(tekst)
    raise AssertionError(f"{tekst!r} niet op het scherm")


def naar_spiekbrief(domein, nr=1):
    """Hoofdmenu › Leerstof › domein (label): heeft het domein één spiekbrief, dan staat die meteen open;
    anders de nr-de (#20: "Welk vak?" valt weg zolang er één vak is)."""
    v = CU.VAKKEN[0]
    d = next(x for x in v.domeinen if x.label == domein)
    i = [x for x in v.domeinen if any(o.spiek for o in x.onderwerpen)].index(d) + 1
    titels = {o.spiek.titel for o in d.onderwerpen if o.spiek}
    return [OK, OK, hm("Leerstof"), str(i)] + ([str(nr)] if len(titels) > 1 else [])


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
        except (ToetsenOp, SystemExit):  # SystemExit: Esc op het titelscherm sluit het programma
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
        """Wisselen gaat via Stoppen → het titelscherm → Wie ben jij? (0.23: geen "Wissel van kind" meer)."""
        o = self.opslag(("Amira", "3", {"thema": "rood-groen"}), ("Imrane", "5"))
        scherm, app = self.speel([OK, "1", hm("Stoppen"), OK, "2"], opslag=o)  # Amira, dan Imrane
        self.assertTrue(self.ergens(scherm, "Hallo Amira!"))
        self.assertEqual(app.kind.naam, "Imrane")
        self.assertEqual(app.inst.thema, "standaard")
        self.assertEqual(app.inst.leerjaar, "5")

    def test_ascii(self):
        scherm, _ = self.speel([OK, OK, ESC], voorrang={"ascii": True})
        for beeld in scherm.beelden:
            self.assertTrue(all(ord(c) < 128 for c in beeld), beeld)

    def test_schermkleuren_kiezen_bewaart_ze(self):
        """Gestart met --contrast; in Mijn avatar › Schermkleuren zelf iets kiezen: dat wordt wel bewaard."""
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([OK, OK, hm("Mijn avatar"), "L", "2", ESC, ESC], opslag=o,
                                 voorrang={"thema": "contrast"})
        self.assertTrue(self.ergens(scherm, "Welke kleuren wil je op het scherm?"))
        self.assertEqual(o.instellingen_van(app.kind.id).thema, "rood-groen")
        self.assertEqual(app.inst.thema, "rood-groen")
        self.assertNotIn("thema", app.voorrang)


class TestReeks(Basis):
    def test_reeks_van_tien_wordt_bewaard(self):
        o = self.opslag(("Test", "5"))
        antwoorden = ["1", OK, OK] * 10
        toetsen = [*naar("wiskunde.meten.lengte", "Enter"), *antwoorden, ESC, ESC, ESC, ESC, ESC]
        scherm, app = self.speel(toetsen, opslag=o)
        self.assertTrue(self.ergens(scherm, "Je score:"))
        self.assertTrue(self.ergens(scherm, "Leeravontuur › Wiskunde › Meten › Lengte (m)"))
        rijen = o.antwoorden(app.kind.id)
        self.assertEqual(len(rijen), 10)
        self.assertTrue(all(r["tijd_ms"] >= 0 and r["modus"] == "reeks" and r["gegeven"] == "1" for r in rijen))
        self.assertTrue(all(r["vaardigheid"] == "wiskunde.eenheden.omzetten" for r in rijen))
        sessies = o.sessies(app.kind.id)
        self.assertEqual(len(sessies), 1)
        self.assertIsNotNone(sessies[0]["einde"])
        self.assertEqual(app.vandaag()[0], 10)
        # na een herstart staat de telling van vandaag er nog
        scherm2, _ = self.speel([OK, OK], opslag=o)
        self.assertTrue(self.ergens(scherm2, "Vandaag: 0/10 juist"))  # in de titelbalk

    def test_zelf_kiezen_met_het_toetsenbord(self):
        # Meten → Maten zelf kiezen (V): met → naar de 5de kolom (volume), m³ en dm³ aanvinken
        toetsen = [*naar("wiskunde.meten.maten_zelf_kiezen", niveau=None), *[curses.KEY_RIGHT] * 4, " ", curses.KEY_DOWN, " ", OK, "3",
                   ESC, ESC, ESC, ESC, ESC, ESC]
        scherm, _ = self.speel(toetsen)
        self.assertTrue(self.ergens(scherm, "[x] m³"))
        self.assertTrue(self.ergens(scherm, "[x] dm³"))
        self.assertTrue(self.ergens(scherm, "dm³  =") or self.ergens(scherm, "m³  ="))

    def test_vrij_oefenen_tip(self):
        o = self.opslag(("Test", "5"))
        toetsen = [*naar("wiskunde.meten.massa"), F1, "5", OK, ESC, ESC, ESC, ESC, ESC]
        scherm, app = self.speel(toetsen, opslag=o)
        self.assertTrue(self.ergens(scherm, "Tip:"))
        rijen = o.antwoorden(app.kind.id)
        self.assertEqual((len(rijen), rijen[0]["hulp"], rijen[0]["modus"]), (1, 1, "vrij"))

    def test_niveau_dat_nog_niet_bestaat(self):
        """#27: Snelheid bestaat pas vanaf het 6de. Voor een kind van het 5de staat "Hoe moeilijk?" op Moeilijk
        (Enter werkt meteen); Makkelijk kiezen zegt waarom het niet gaat en zet de keuze op Moeilijk."""
        from leeravontuur.kern.onderwerp import ONDERWERPEN
        snel = ONDERWERPEN["wiskunde.eenheden.snelheid"]
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*naar(snel, toets="Enter", niveau=None), OK,
                                  ESC, ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Snelheid · Moeilijk (6de leerjaar)"))
        self.assertTrue(self.ergens(scherm, "pas vanaf het 6de leerjaar"))
        scherm, app = self.speel([*naar(snel, toets="Enter", niveau=None), "1", OK,
                                  ESC, ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Dit oefen je pas vanaf het 6de leerjaar. Kies Moeilijk."))
        self.assertTrue(self.ergens(scherm, "Snelheid · Moeilijk (6de leerjaar)"))

    def test_esc_bij_maten_vraagt_eerst(self):
        """#33: ook bij Maten (vrij en de tabel-oefening)."""
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*naar("wiskunde.meten.massa"), ESC, OK, ESC, curses.KEY_LEFT, OK], opslag=o)
        self.assertTrue(self.ergens(scherm, "Wil je stoppen met deze vraag?"))
        self.assertEqual(o.antwoorden(app.kind.id), [])
        scherm, _ = self.speel([*naar("wiskunde.meten.lengte", "h"), "4", ESC, OK])
        self.assertTrue(self.ergens(scherm, "Wil je stoppen met deze vraag?"))
        self.assertNotIn("Wil je stoppen", scherm.beelden[-1])  # Nee: de tabel staat er weer
        # en ook de broodkruimel (#33 opnieuw), vrij en in de tabel
        for stappen in ([*naar("wiskunde.meten.massa"), "5"], [*naar("wiskunde.meten.lengte", "h"), "4"]):
            scherm, app = self.speel([*stappen, ("klik", 0, 17), OK], opslag=o)
            self.assertTrue(self.ergens(scherm, "Wil je stoppen met deze vraag?"))
            self.assertNotIn("Welk onderwerp?", na_het_kader(scherm))

    def test_f1_is_ook_een_tip(self):
        """#14: F1 geeft een tip (eigen scherm van de maten); ? doet niets meer (0.21.7)."""
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*naar("wiskunde.meten.massa"), curses.KEY_F1, "5", OK, ESC, ESC, ESC, ESC, ESC],
                                 opslag=o)
        self.assertTrue(self.ergens(scherm, "Tip:"))
        self.assertTrue(self.ergens(scherm, "[F1] tip"))
        self.assertEqual(o.antwoorden(app.kind.id)[0]["hulp"], 1)


class TestMuis(Basis):
    def test_tabel_klikken_en_komma(self):
        rij = TABEL_Y + 3
        cel_m = TABEL_X + 1 + 3 * 6          # 4de kolom: m
        rand_m = cel_m + 5                   # de rand rechts van m = komma achter m
        toetsen = [*naar("wiskunde.meten.lengte", "h"),
                   ("klik", rij, cel_m + 2), "4", ("klik", rij, rand_m),
                   ESC, ESC, ESC, ESC, ESC]
        scherm, _ = self.speel(toetsen)
        self.assertTrue(self.ergens(scherm, "Aflezen met de komma achter m: 4 m"))

    def test_schermkleuren_met_de_muis(self):
        """Hoofdmenu › Mijn avatar (klik) › klik op de regel [L] schermkleuren › klik op het 2de thema."""
        o = self.opslag(("Test", "5"))
        scherm, _ = self.speel([OK, OK, ("klik", hm_rij("Mijn avatar"), 10)], opslag=o)
        y, x = plek(scherm, "[L] schermkleuren:")
        toetsen = [OK, OK, ("klik", hm_rij("Mijn avatar"), 10), ("klik", y, x + 3), ("klik", 7, 10), ESC, ESC]
        scherm, app = self.speel(toetsen, opslag=o)
        self.assertEqual(app.inst.thema, "rood-groen")
        self.assertEqual(o.instellingen_van(app.kind.id).thema, "rood-groen")
        self.assertTrue(self.ergens(scherm, "Leeravontuur › Mijn avatar › Schermkleuren"))
        self.assertTrue(self.ergens(scherm, "✔ nu"))

    def test_voetbalk_van_mijn_avatar(self):
        scherm, _ = self.speel([OK, OK, hm("Mijn avatar")])
        y, x = plek(scherm, "[L] schermkleuren  ")
        self.assertEqual(y, 23)  # in de voetregel
        scherm, _ = self.speel([OK, OK, hm("Mijn avatar"), ("klik", y, x + 1), ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Welke kleuren wil je op het scherm?"))

    def test_knop_in_voetbalk(self):
        scherm, _ = self.speel([OK, OK, hm("Wiskunde")])
        y, x = scherm.zoek("[Esc]")
        scherm2, _ = self.speel([OK, OK, hm("Wiskunde"), ("klik", y, x + 1)])
        # na de klik op [Esc] staan we terug in het hoofdmenu
        self.assertIn("Wat wil je doen?", scherm2.beelden[-1])

    def verder_klaar(self, af):
        """Een kind met een vorige oefening (af of niet) en een herhaalvraag die vandaag aan de beurt is."""
        import json
        from leeravontuur.kern.wiskunde import hoofdrekenen as H
        o = self.opslag(("Test", "5"))
        kind = o.kinderen()[0]
        o.zet_algemeen(f"laatste_oefening:{kind.id}", json.dumps(
            {"onderwerp": "oefenaar", "vaardigheid": H.TAFELS.id, "vorm": "reeks", "niveau": 1,
             "domein": "Hoofdrekenen", "af": af}))
        o.herhaal_zet(kind.id, H.TAFELS.id, "tafel 7", {"onderwerp": "tafel 7", "tafel": 7}, 1, "2000-01-01")
        return o

    def test_verder_na_een_afgewerkte_oefening(self):
        """0.23: was de vorige oefening af en staan er herhaalvragen klaar, dan vraagt Verder eerst, met Verder
        gekozen (Enter = verder met de oefening, ← Enter = eerst herhalen)."""
        o = self.verder_klaar(af=True)
        scherm, _ = self.speel([OK, OK, hm("▶ Verder"), OK], opslag=o)
        self.assertTrue(self.ergens(scherm, "Je vorige oefening is af. Goed zo!"))
        self.assertTrue(self.ergens(scherm, "[ Eerst herhalen ]   [ Verder ]"))
        def erna(scherm):
            i = max(i for i, b in enumerate(scherm.beelden) if "Je vorige oefening is af" in b)
            return next(b for b in scherm.beelden[i + 1:] if "Je vorige oefening is af" not in b).split("\n")[0]
        self.assertIn("Reeks van 10", erna(scherm))
        self.open[-1].sluit()
        self.open.pop()
        self.tearDown()
        self.setUp()  # nieuwe gegevens: de reeks hierboven is opnieuw begonnen (dus niet meer af)
        scherm, _ = self.speel([OK, OK, hm("▶ Verder"), curses.KEY_LEFT, OK], opslag=self.verder_klaar(af=True))
        self.assertIn("Herhalen", erna(scherm))

    def test_verder_zonder_kader_als_de_oefening_niet_af_was(self):
        o = self.verder_klaar(af=False)
        scherm, _ = self.speel([OK, OK, hm("▶ Verder")], opslag=o)
        self.assertFalse(self.ergens(scherm, "Je vorige oefening is af"))
        self.assertTrue(self.ergens(scherm, "Reeks van 10"))

    def test_een_volle_reeks_is_af(self):
        """Een reeks tot het resultaat = af; vrij oefenen nooit (dat bepaalt of Verder eerst herhalen voorstelt)."""
        from leeravontuur.terminal.app import App
        o = self.verder_klaar(af=False)
        scherm, app = self.speel([*naar("wiskunde.meten.massa", "Enter"), *[k for _ in range(10) for k in ("1", OK, OK)]],
                                 opslag=o)
        self.assertTrue(app.laatste_oefening().get("af"))
        scherm, app = self.speel([*naar("wiskunde.meten.massa"), "1", OK, OK], opslag=o)
        self.assertFalse(app.laatste_oefening().get("af"))

    def test_stoppen_en_esc_naar_het_titelscherm(self):
        """0.23: Stoppen en Esc in het hoofdmenu brengen je naar het titelscherm (zonder kader). Daar is Enter =
        "Wie ben jij?" en Esc = het programma sluiten."""
        for stoppen in (hm("Stoppen"), ESC):
            with self.subTest(stoppen=stoppen):
                scherm, _ = self.speel([OK, OK, stoppen, OK, ESC, ESC, "x"])
                self.assertFalse(self.ergens(scherm, "Wil je stoppen"))
                titel = [i for i, b in enumerate(scherm.beelden) if "Druk op een toets om te beginnen" in b]
                self.assertGreaterEqual(len(titel), 3)  # bij de start, na Stoppen, na Esc in "Wie ben jij?"
                self.assertIn("Wie ben jij?", scherm.beelden[titel[1] + 1])
                self.assertEqual(scherm.toetsen, ["x"])  # Esc op het titelscherm: het programma stopte

    def test_hoofdmenu_in_groepen(self):
        """0.23: kopjes VAKKEN, JIJ, FEEDBACK; Taal staat grijs (↑↓ slaan het over, 4 = "Taal komt binnenkort.");
        Winkel en Leerstof rechtstreeks."""
        scherm, _ = self.speel([OK, OK])
        menu = next(b for b in scherm.beelden if "Wat wil je doen?" in b).split("\n")
        for kop, rij in (("VAKKEN", 8), ("JIJ", 13), ("FEEDBACK", 17)):
            self.assertEqual(menu[rij][:40].strip(), kop)  # (rechts staan de avatar en de punten)
        self.assertEqual(len(menu), 24)
        self.assertTrue(menu[20].strip().startswith("9. Stoppen"))
        scherm, _ = self.speel([OK, OK, hm("Taal")])
        self.assertTrue(self.ergens(scherm, "Taal komt binnenkort."))
        scherm, app = self.speel([OK, OK, *[curses.KEY_DOWN] * 3, OK])  # Verder, Herhalen, Wiskunde, (Taal), Leerstof
        self.assertTrue(self.ergens(scherm, "Leeravontuur › Leerstof"))
        scherm, _ = self.speel([OK, OK, hm("Winkel")])
        self.assertTrue(self.ergens(scherm, "Leeravontuur › Winkel"))

    def test_broodkruimel_terug_naar_hoofdmenu(self):
        scherm, _ = self.speel([OK, OK, hm("Wiskunde"), "1", ("klik", 0, 2)])
        self.assertIn("Wat wil je doen?", scherm.beelden[-1])

    def test_scrollwiel_in_spiekbrief(self):
        scherm, _ = self.speel([*naar_spiekbrief("Meten"), *[("wiel", 1)] * 8, ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "VOORBEELD"))


class TestVraagstuk(Basis):
    """Wiskunde › Vraagstukken › Oplossen › V (vrij oefenen), met een vast vraagstuk."""

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
        return naar("wiskunde.vraagstukken.oplossen")

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
        toetsen = [*self.start(), F1, F1, "a", *self.antwoord(fout), OK]
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
        scherm, app = self.speel([*naar("wiskunde.vraagstukken.speurneus"), "0", OK, ESC, ESC, ESC, ESC, ESC], opslag=o)
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
        scherm, _ = self.speel([*naar("wiskunde.vraagstukken.schatten_controleren")], opslag=o)
        beeld = next(b for b in reversed(scherm.beelden) if "a) " in b).split("\n")
        y = next(i for i, regel in enumerate(beeld) if "a) " in regel)
        scherm, app = self.speel([*naar("wiskunde.vraagstukken.schatten_controleren"), ("klik", y, 8), ESC, ESC, ESC, ESC, ESC],
                                 opslag=o)
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual(rij["vaardigheid"], "wiskunde.vraagstukken.schatten")
        self.assertTrue(rij["gegeven"].startswith("a)"))


class TestKlok(Basis):
    """Wiskunde › Tijd, geld en snelheid › De klok › V (vrij oefenen), met een vaste vraag."""
    START = naar("wiskunde.tijd_geld_snelheid.klok")

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

    def vast(self, o, v):
        from unittest import mock
        patch = mock.patch.object(o, "maak", return_value=v)
        patch.start()
        self.addCleanup(patch.stop)
        return naar(o)

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

    def test_tab_zonder_enter_houdt_de_regel(self):
        """#22: een klad-regel getypt zonder Enter en dan Tab: de regel blijft staan (nagekeken), niet weg."""
        o = self.opslag(("Test", "5"))
        toetsen = [*self.plusmin(), TAB, *"47 + 100 = 147", TAB]
        scherm, app = self.speel(toetsen, opslag=o)
        laatste = next(b for b in reversed(scherm.beelden) if "47 + 99 =" in b)
        self.assertIn("47 + 100 = 147", laatste)
        self.assertIn("Klad (Tab)", laatste)  # de focus staat weer op het antwoord
        self.assertNotIn("typ hier je rekenregels", laatste)
        scherm, app = self.speel(toetsen + [*"146", OK, ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertIn('"klad": ["47 + 100 = 147"]', o.antwoorden(app.kind.id)[-1]["extra"])

    def test_na_de_tips_de_spiekbrief(self):
        """#20: na de laatste tip opent nog eens ? de spiekbrief (bij het juiste kopje); Esc = terug naar dezelfde vraag
        (niets kwijt); daarna begint ? weer bij tip 1. De spiekbrief telt als een tip."""
        import random
        from leeravontuur.kern.wiskunde import hoofdrekenen as H
        v = next(v for v in (H.TAFELS.maak_met(H.TAFELS.parameters("5"), random.Random(z)) for z in range(50))
                 if v.antwoord >= 10 and v.tekst.count("×") == 1 and not v.tekst.startswith("-"))
        antwoord = str(v.antwoord)
        o = self.opslag(("Test", "5"))
        aantal = max(1, len(H.TAFELS.tips(v)) + bool(H.TAFELS.klad_voor(v)))
        toetsen = [*self.vast(H.TAFELS, v), antwoord[0], *[F1] * aantal]
        scherm, _ = self.speel(toetsen, opslag=o)
        self.assertIn("[F1] spiekbrief", next(b for b in reversed(scherm.beelden) if v.tekst in b))
        scherm, app = self.speel([*toetsen, F1, ESC, F1, *antwoord[1:], OK], opslag=o)
        brief = next(b for b in scherm.beelden if "› Spiekbrief" in b)
        self.assertIn("TAFELS", [r.strip() for r in brief.split("\n")[2:5]], brief)  # meteen bij het kopje
        self.assertIn("[Esc] terug naar je vraag", brief)
        terug = scherm.beelden[scherm.beelden.index(brief) + 1]
        self.assertIn(v.tekst, terug)
        self.assertTrue(self.ergens(scherm, "Tip 1 van") or self.ergens(scherm, "Tip:"))
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual((rij["gegeven"], rij["juist"]), (antwoord, 1))  # het eerste cijfer bleef staan
        self.assertIn(f'"tips": {aantal + 2}', rij["extra"])            # de spiekbrief telt als een tip

    def test_spiekbrief_na_de_tips_overal(self):
        """#20: rooster (? twee keer op hetzelfde vakje), vraagstuk (na de 4 tips) en Maten (na de tip)."""
        from leeravontuur.kern.onderwerp import ONDERWERPEN
        for o, n, kop in ((ONDERWERPEN["wiskunde.cijferen.optellen"], 2, "OPTELLEN"),
                          (ONDERWERPEN["wiskunde.vraagstukken.oplossen"], 5, "EEN VRAAGSTUK IN 4 STAPPEN")):
            with self.subTest(o.id):
                scherm, _ = self.speel([*naar(o), *[F1] * n, ESC])
                brief = next(b for b in scherm.beelden if "› Spiekbrief" in b)
                self.assertIn(kop, [r.strip() for r in brief.split("\n")[2:5]])
                self.assertFalse(any("› Spiekbrief" in b for b in scherm.beelden[:scherm.beelden.index(brief)]))
        scherm, _ = self.speel([*naar("wiskunde.meten.massa"), F1, F1, ESC])
        self.assertTrue(self.ergens(scherm, "Nog hulp nodig? Druk nog eens F1: je spiekbrief."))
        brief = next(b for b in scherm.beelden if "› Spiekbrief" in b)
        self.assertIn("[Esc] terug naar je vraag", brief)

    def test_elk_spiekkopje_bestaat(self):
        """Het kopje waar de spiekbrief opent (Onderwerp.kop_op_spiekbrief) staat echt op de spiekbrief."""
        import random
        from leeravontuur.kern.onderwerp import ONDERWERPEN
        for o in ONDERWERPEN.values():
            koppen = [t for t, _ in (o.spiekbrief() or [])]
            for z in range(15):
                v = o.maak(o.jaar_voor("5"), rng=random.Random(z))
                kop = o.kop_op_spiekbrief(v)
                if kop is not None:
                    with self.subTest(o=o.id, kop=kop):
                        self.assertIn(kop, koppen)

    def test_esc_vraagt_eerst_en_nee_houdt_alles(self):
        """#33: Esc midden in een vraag vraagt eerst "Wil je stoppen?"; Nee (gekozen) houdt antwoord en klad."""
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.plusmin(), TAB, *"47 + 100 = 147", OK, TAB, *"14", ESC, OK, *"6", OK],
                                 opslag=o)
        self.assertTrue(self.ergens(scherm, "Wil je stoppen met deze vraag?"))
        self.assertTrue(self.ergens(scherm, "[ Nee, verder ]"))
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual((rij["gegeven"], rij["juist"]), ("146", 1))
        self.assertIn('"klad": ["47 + 100 = 147"]', rij["extra"])

    def test_esc_esc_blijft_en_links_enter_stopt(self):
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.plusmin(), *"14", ESC, ESC, "6", OK], opslag=o)
        na = na_het_kader(scherm)
        self.assertIn("47 + 99 =", na)
        self.assertEqual(o.antwoorden(app.kind.id)[-1]["gegeven"], "146")  # verder getypt: 14 + 6
        scherm, app = self.speel([*self.plusmin(), *"14", ESC, curses.KEY_LEFT, OK], opslag=o)
        self.assertEqual(len(o.antwoorden(app.kind.id)), 1)  # niets bijgekomen
        self.assertIn("Hoofdrekenen: wat wil je oefenen?", na_het_kader(scherm))

    def test_esc_klik_op_ja(self):
        scherm, _ = self.speel([*self.plusmin(), ESC])
        y, x = plek(scherm, "[ Ja, stoppen ]")
        scherm, _ = self.speel([*self.plusmin(), ESC, ("klik", y, x + 2)])
        self.assertIn("Hoofdrekenen: wat wil je oefenen?", na_het_kader(scherm))

    KRUIMEL_WISKUNDE = ("klik", 0, 17)  # " Leeravontuur › Wiskunde › …": "Wiskunde" begint in kolom 16

    def test_kruimel_vraagt_eerst_en_nee_houdt_alles(self):
        """#33 (opnieuw): een klik op de broodkruimel midden in een vraag vraagt ook eerst "Wil je stoppen?"."""
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.plusmin(), TAB, *"47 + 100 = 147", OK, TAB, *"14", self.KRUIMEL_WISKUNDE,
                                  OK, *"6", OK], opslag=o)
        self.assertTrue(self.ergens(scherm, "Wil je stoppen met deze vraag?"))
        self.assertIn("47 + 99 =", na_het_kader(scherm))
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual((rij["gegeven"], rij["juist"]), ("146", 1))
        self.assertIn('"klad": ["47 + 100 = 147"]', rij["extra"])

    def test_kruimel_ja_gaat_naar_dat_menu(self):
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.plusmin(), *"14", self.KRUIMEL_WISKUNDE, curses.KEY_LEFT, OK], opslag=o)
        self.assertIn("Welk onderwerp?", na_het_kader(scherm))
        self.assertEqual(o.antwoorden(app.kind.id), [])

    def test_kruimel_vanuit_de_spiekbrief_in_een_vraag(self):
        """In de spiekbrief vanuit een vraag: de broodkruimel vraagt eerst; Esc gaat gewoon terug naar de vraag."""
        scherm, _ = self.speel([*self.plusmin(), *"14", *[F1] * 4, self.KRUIMEL_WISKUNDE, OK])
        self.assertTrue(self.ergens(scherm, "Wil je stoppen met deze vraag?"))
        self.assertIn("› Spiekbrief", na_het_kader(scherm))  # Nee: terug in de spiekbrief
        scherm, _ = self.speel([*self.plusmin(), *"14", *[F1] * 4, ESC])
        self.assertFalse(self.ergens(scherm, "Wil je stoppen"))
        brief = max(i for i, b in enumerate(scherm.beelden) if "› Spiekbrief" in b)
        self.assertIn("47 + 99 =", scherm.beelden[brief + 1])  # Esc: meteen terug naar de vraag

    def test_kruimel_na_het_nakijken_meteen(self):
        scherm, _ = self.speel([*self.plusmin(), *"146", OK, self.KRUIMEL_WISKUNDE])
        self.assertFalse(self.ergens(scherm, "Wil je stoppen"))
        self.assertTrue(self.ergens(scherm, "Welk onderwerp?"))

    def test_gestopte_reeks_toont_het_resultaat(self):
        """Werkwijzen fase 2: een reeks die je halverwege stopt, toont het resultaat van wat al gedaan is."""
        from leeravontuur.kern.wiskunde import hoofdrekenen as H
        self.plusmin()  # zet de vraag vast
        reeks = naar(H.PLUSMIN, toets="Enter")
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*reeks, *"146", OK, OK, *"140", OK, *"140", OK, OK,
                                  ESC, curses.KEY_LEFT, OK], opslag=o)
        resultaat = next(b for b in scherm.beelden if "› Resultaat" in b)
        self.assertIn("Je stopte na 2 van de 10 vragen.", resultaat)
        self.assertIn("Je score: 1 / 2", resultaat)
        self.assertIn("[F] fouten opnieuw", resultaat)
        self.assertIn("★ Je verdiende", resultaat)  # de punten van wat al gedaan is
        # meteen gestopt (nog niets beantwoord): gewoon terug naar het menu
        scherm, _ = self.speel([*reeks, ESC, curses.KEY_LEFT, OK], opslag=o)
        self.assertFalse(self.ergens(scherm, "› Resultaat"))
        self.assertIn("Hoofdrekenen: wat wil je oefenen?", na_het_kader(scherm))

    def test_gestopte_reeks_bij_maten(self):
        scherm, _ = self.speel([*naar("wiskunde.meten.massa", toets="Enter"), "1", OK, OK,
                                ESC, curses.KEY_LEFT, OK])
        resultaat = next(b for b in scherm.beelden if "› Resultaat" in b)
        self.assertIn("Je stopte na 1 van de 10 vragen.", resultaat)
        self.assertIn("Je score: 0 / 1", resultaat)

    def test_esc_na_het_nakijken_stopt_meteen(self):
        scherm, _ = self.speel([*self.plusmin(), *"146", OK, ESC])
        self.assertFalse(self.ergens(scherm, "Wil je stoppen"))
        self.assertTrue(self.ergens(scherm, "Hoofdrekenen: wat wil je oefenen?"))

    def test_klad_blijft_staan_na_het_nakijken(self):
        """#22: na het nakijken staat je klad in een kader "Jouw klad", met ! op de regel waar het misging."""
        scherm, _ = self.speel([*self.plusmin(), TAB, *"47 + 100 = 147", OK, *"147 + 1 = 148", OK, TAB,
                                *"148", OK, *"148", OK])
        beeld = next(b for b in reversed(scherm.beelden) if "Zo kan het" in b)
        self.assertIn("Jouw klad", beeld)
        regel = next(r for r in beeld.split("\n") if "147 + 1 = 148" in r)
        self.assertIn("!", regel)
        self.assertIn("Dat zie je in je klad, regel 2 (!).", beeld)

    def test_klad_kader_ook_bij_juist_en_niet_zonder_klad(self):
        scherm, _ = self.speel([*self.plusmin(), TAB, *"47 + 100 = 147", OK, *"147 - 1 = 146", OK, TAB, *"146", OK])
        beeld = next(b for b in reversed(scherm.beelden) if "Jouw klad" in b)
        self.assertIn("✔", next(r for r in beeld.split("\n") if "│ 2 147 − 1 = 146" in r))
        scherm, _ = self.speel([*self.plusmin(), *"146", OK])
        self.assertFalse(self.ergens(scherm, "Jouw klad"))

    def test_klad_kader_past_overal(self):
        """Na twee foute antwoorden met 6 klad-regels: het kader staat heel (niets schrijft erover), binnen 80 × 24."""
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
                if v is None or v.invoer in INVOER_OBJECTEN or v.invoer == "janee":
                    continue
                with self.subTest(oid=oid, jaar=jaar, vraag=v.tekst):
                    from unittest import mock
                    with mock.patch.object(o, "maak", return_value=v):
                        regels = [k for _ in range(6) for k in [*"12 + 3 = 15", OK]]
                        fout = "1" if v.invoer != "breuk" else "1/7"
                        toetsen = [*naar(o)] + ([] if o.klad_voor(v) == "verplicht" else [TAB])
                        scherm, _ = self.speel([*toetsen, *regels, TAB, *fout, OK, *fout, OK])
                    beeld = next((b for b in reversed(scherm.beelden) if "Niet juist" in b), None)
                    if beeld is None:  # bv. "verplicht" klad dat dit klad niet aanvaardt: geen nakijken
                        continue
                    rijen = beeld.split("\n")
                    self.assertEqual(len(rijen), 24)
                    self.assertTrue(rijen[-1].startswith(" [Enter]"), rijen[-1])
                    boven = [i for i, r in enumerate(rijen) if "┌ Jouw klad" in r]
                    if not boven:
                        continue  # geen plaats (bv. naast de wijzerklok): dan geen kader
                    y, x = boven[0], rijen[boven[0]].index("┌")
                    breed = rijen[y].index("┐") - x + 1
                    for r in rijen[y + 1:y + 4]:
                        self.assertEqual((r[x], r[x + breed - 1]), ("│", "│"), r)
                    self.assertEqual(rijen[y + 4][x:x + breed], "└" + "─" * (breed - 2) + "┘")

    def test_hoofdmenu_uitleg_stopt_voor_de_avatar(self):
        """De uitleg in het hoofdmenu liep onder de avatar door ("vraagst▄"); nu stopt ze ervoor (met … als het moet)."""
        from leeravontuur.terminal import avatar as AV
        o = self.opslag(("Test", "5"))
        scherm, app = self.speel([*self.plusmin(), *"146", OK, ESC, ESC, ESC, ESC], opslag=o)
        menu = next(b for b in reversed(scherm.beelden) if "▶ Verder" in b).split("\n")
        tot = 80 - AV.BREEDTE - 3
        for regel in menu[5:13]:
            self.assertEqual(regel[tot:tot + 2].strip(), "", regel)
        self.assertTrue(any("rekenen, meten en meetkunde" in r for r in menu))
        self.assertTrue(any("kast en schermkleuren" in r for r in menu))

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
        scherm, _ = self.speel([*self.plusmin(), F1, F1, F1, ESC, ESC, ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Tip 1 van 3: Maak er eerst een rond getal van"))
        self.assertTrue(self.ergens(scherm, "Tip 2 van 3: Begin je klad zo: 47 + 100 = …"))
        self.assertTrue(self.ergens(scherm, "Tip 3 van 3: schrijf je eerste stap in het klad"))

    def test_tips_draaien_rond(self):
        """#15: na de laatste tip (en de spiekbrief, #20) begint ? opnieuw bij de eerste."""
        scherm, _ = self.speel([*self.plusmin(), F1, F1, F1, F1, ESC, F1])
        tips = [b for b in scherm.beelden if "Tip " in b]
        self.assertIn("Tip 1 van 3: Maak er eerst een rond getal van", tips[-1].replace("\n", " "))

    def test_f1_geeft_de_volgende_tip(self):
        """#14: F1 geeft de volgende tip, ook in het klad (en typt daar niets)."""
        scherm, _ = self.speel([*self.plusmin(), curses.KEY_F1, TAB, curses.KEY_F1, ESC, ESC, ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Tip 2 van 3"))
        self.assertTrue(self.ergens(scherm, "[F1] tip"))

    def test_vraagteken_in_het_klad_is_gewoon_een_teken(self):
        """0.21.7: het kind schrijft ? in zijn klad als vraag aan zichzelf: geen tip, geen ✘ of !."""
        scherm, _ = self.speel([*self.plusmin(), TAB, *"47 + 99 = ?", OK, ESC, ESC, ESC, ESC, ESC])
        self.assertFalse(self.ergens(scherm, "Tip 1 van 3"))
        laatste = next(b for b in reversed(scherm.beelden) if "47 + 99 = ?" in b)
        self.assertIn("Een vraag voor jezelf. Reken ze uit op een volgende regel.", laatste)
        self.assertNotIn("Dit kan ik niet lezen", laatste)
        scherm, _ = self.speel([*self.plusmin(), *"14?", ESC, ESC, ESC])  # in het antwoordvak: niets
        self.assertFalse(self.ergens(scherm, "Tip 1 van 3"))

    def test_tip_terwijl_je_in_het_klad_typt(self):
        """#15: F1 midden in een klad-regel geeft een tip, en de regel blijft staan."""
        scherm, _ = self.speel([*self.plusmin(), TAB, *"47 + 1", F1, ESC, ESC, ESC, ESC, ESC])
        laatste = next(b for b in reversed(scherm.beelden) if "47 + 1" in b)
        self.assertIn("Tip 1 van 3", laatste)

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
                        toetsen = [*naar(o)] + ([] if o.klad_voor(v) == "verplicht" else [TAB])
                        scherm, _ = self.speel([*toetsen, *regels, F1, F1, F1])
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


PAD = {"/": 458, "Enter": 459, "Ctrl+Enter": 460, "Alt+Enter": 461, ".": 462, "*": 463, "-": 464, "+": 465}


class TestNumeriekKlavier(Basis):
    """Het numeriek klavier op Windows (#11): PDCurses geeft eigen codes voor / * - + . en Enter."""
    vast, plusmin = TestWerkwijze.vast, TestWerkwijze.plusmin

    def setUp(self):
        super().setUp()
        from unittest import mock
        from leeravontuur.terminal import scherm
        patch = mock.patch.object(scherm, "KLAVIER", scherm.KLAVIER_PDCURSES)  # zoals op Windows
        patch.start()
        self.addCleanup(patch.stop)

    def toetsen(self, codes):
        s = Scherm(NepScherm(codes), Instellingen(), kleuren=False)
        return [s.toets() for _ in codes]

    def test_tekens_en_enter(self):
        from leeravontuur.terminal.scherm import ENTER, teken_van
        uit = self.toetsen([PAD[t] for t in "/*-+."])
        self.assertEqual([teken_van(k) for k in uit], list("/*-+."))
        for k in self.toetsen([PAD["Enter"], PAD["Ctrl+Enter"], PAD["Alt+Enter"]]):
            self.assertIn(k, ENTER)

    def test_menu_en_klad_met_het_numeriek_klavier(self):
        """Enter van het klavier kiest in de menu's; + en - komen in het klad; Enter kijkt het antwoord na."""
        o = self.opslag(("Test", "5"))
        toetsen = [*self.plusmin()]
        toetsen[:2] = [PAD["Enter"], PAD["Enter"]]  # startscherm en "Wie ben jij?"
        toetsen += [TAB, *"47 ", PAD["+"], *" 100 = 147", PAD["Enter"], *"147 ", PAD["-"], *" 1 = 146",
                    PAD["Enter"], TAB, *"146", PAD["Enter"]]
        scherm, app = self.speel(toetsen + [ESC] * 5, opslag=o)
        self.assertTrue(self.ergens(scherm, "147 − 1 = 146"))
        rij = o.antwoorden(app.kind.id)[-1]
        self.assertEqual(rij["juist"], 1)
        self.assertIn('"klad_ok": true', rij["extra"])

    def test_elders_ongewijzigd(self):
        """Op Linux en macOS (ncurses) blijven die codes wat ze zijn."""
        from unittest import mock
        from leeravontuur.terminal import scherm
        with mock.patch.object(scherm, "KLAVIER", {}):
            self.assertEqual(self.toetsen([463, 459]), [463, 459])

    def test_linux_op_naam(self):
        """ncurses: het klavier in toepassingsmodus geeft extra toetsen (code boven KEY_MAX) met een naam."""
        from unittest import mock
        from leeravontuur.terminal import scherm
        from leeravontuur.terminal.scherm import teken_van
        namen = {583: b"kpADD", 585: b"kpDIV", 587: b"kpMUL", 588: b"kpSUB", 586: b"kpDOT", 600: b"kRIT5"}
        with mock.patch.object(scherm, "KLAVIER", {}), \
                mock.patch.object(scherm.curses, "keyname", side_effect=lambda k: namen[k]):
            uit = self.toetsen([583, 585, 587, 588, 586, 600])
        self.assertEqual([teken_van(k) for k in uit[:5]], list("+/*-."))
        self.assertEqual(uit[5], 600)  # een andere extra toets (Ctrl+pijl) blijft wat hij is


class TestMenuToetsen(unittest.TestCase):
    """Het menu met lettertoetsen per keuze (de onderwerpenlijst): de aanroeper bepaalt de toetsen."""

    OPTIES = [("Tafels", ""), ("Gemengd", ""), ("Hoeken", "")]
    TOETSEN = [[("Enter", "reeks"), ("v", "vrij"), ("s", "spiekbrief"), ("t", "60 s"), ("z", "20 sommen")],
               [("Enter", "20 sommen"), ("z", "20 sommen")],   # bv. zonder zichtbare timer
               [("Enter", "reeks"), ("v", "vrij"), ("s", "spiekbrief")]]

    def menu(self, toetsen, met_toetsen=True, **inst):
        win = NepScherm(toetsen)
        s = Scherm(win, Instellingen(**inst), kleuren=False)
        try:
            return s.menu(["Leeravontuur", "Hoofdrekenen"], "Wat wil je oefenen?", self.OPTIES,
                          toetsen=self.TOETSEN if met_toetsen else None), win
        except (ToetsenOp, SystemExit):  # SystemExit: Esc op het titelscherm sluit het programma
            return "op", win

    def test_hoofdletter_en_kleine_letter(self):
        self.assertEqual(self.menu(["v"])[0], (0, "v"))
        self.assertEqual(self.menu(["V"])[0], (0, "v"))
        self.assertEqual(self.menu(["j", "Z"])[0], (1, "z"))

    def test_letter_die_niet_geldt_doet_niets(self):
        self.assertEqual(self.menu(["j", "v"])[0], "op")      # Gemengd heeft geen V
        self.assertEqual(self.menu(["h", "x", "\n"])[0], (0, "Enter"))

    def test_enter_cijfer_en_klik_zijn_enter(self):
        self.assertEqual(self.menu(["\n"])[0], (0, "Enter"))
        self.assertEqual(self.menu(["3"])[0], (2, "Enter"))
        self.assertEqual(self.menu([("klik", 7, 10)])[0], (1, "Enter"))

    def test_voetregel_volgt_de_markering_en_is_klikbaar(self):
        _, win = self.menu(["j"])
        voet = [b.splitlines()[-1] for b in win.beelden]
        self.assertIn("[V] vrij", voet[0])
        self.assertIn("[T] 60 s", voet[0])
        self.assertNotIn("[V]", voet[1])
        self.assertIn("[Enter] 20 sommen", voet[1])
        x = voet[0].index("[V]") + 1
        self.assertEqual(self.menu([("klik", 23, x)])[0], (0, "v"))

    def test_langste_voetregel_past_met_esc(self):
        _, win = self.menu([])
        voet = win.beelden[0].splitlines()[-1]
        for knop in ("[Enter] reeks", "[V] vrij", "[S] spiekbrief", "[T] 60 s", "[Z] 20 sommen", "[Esc] terug"):
            self.assertIn(knop, voet)
        self.assertLessEqual(len(voet.rstrip()), 79)

    def test_eenvoudige_tekens(self):
        _, win = self.menu([], ascii=True)
        self.assertTrue(all(ord(c) < 128 for c in win.beelden[0]))

    def test_zonder_toetsen_zoals_vroeger(self):
        self.assertEqual(self.menu(["2"], met_toetsen=False)[0], 1)
        self.assertEqual(self.menu(["v"], met_toetsen=False)[0], "op")
        _, win = self.menu([], met_toetsen=False)
        self.assertIn("[↑↓] kiezen", win.beelden[0].splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
