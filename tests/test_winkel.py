import curses
import random
import unittest
from unittest import mock

from leeravontuur.kern import avatar as A
from leeravontuur.kern import winkel as W
from leeravontuur.kern.opslag import Opslag

try:
    from .test_schermen import ESC, OK, Basis, hm
except ImportError:
    from test_schermen import ESC, OK, Basis, hm


class TestCatalogus(unittest.TestCase):
    def test_alles_bestaat(self):
        items = W.catalogus()
        self.assertGreaterEqual(len([i for i in items if i.prijs]), 25)
        for i in items:
            self.assertIn(i.sleutel, A.opties(i.laag), i)
        self.assertEqual(W.zoek("hoed", "kroon").prijs, 300)
        self.assertTrue(all(i.prijs == 0 for i in W.catalogus("vorm") if i.sleutel == "vierkant"))


class TestChallenge(unittest.TestCase):
    def test_aftrekken_in_het_4de(self):
        rng = random.Random(1)
        for _ in range(50):
            ch = W.challenge(200, 70, "4", rng)
            self.assertEqual((ch.antwoord, ch.betalen), (130, 70))
            self.assertIn("200 − 70", ch.lesje[0])

    def test_korting_vanaf_het_5de(self):
        rng = random.Random(2)
        gezien = set()
        for _ in range(100):
            ch = W.challenge(250, 120, "5", rng)
            self.assertEqual(ch.antwoord, 250 - ch.betalen)
            self.assertLessEqual(ch.betalen, 120)
            if "korting" in ch.vraag:
                gezien.add(ch.betalen)
                self.assertTrue(any("%" in r for r in ch.lesje))
        self.assertTrue(gezien)
        self.assertTrue(gezien <= {108, 96, 90, 60})  # 10, 20, 25 of 50 % van 120

    def test_sparen(self):
        ch = W.spaar_vraag(50, 300)
        self.assertEqual(ch.antwoord, 250)


class TestKopen(unittest.TestCase):
    def setUp(self):
        self.o = Opslag()
        self.kind = self.o.nieuw_kind("Test", "5")
        self.o.punten_bij(self.kind.id, 500, "test")
        self.kroon = W.zoek("hoed", "kroon")

    def juist_antwoorden(self, n, tijd_ms=0):
        s = self.o.start_sessie(self.kind.id, "reeks", "x", "5")
        for i in range(n):
            self.o.bewaar_antwoord(s, self.kind.id, "x", "5", "reeks", f"k{i}", "v", "g", True, tijd_ms=tijd_ms)

    def test_juist_meteen_in_de_kast(self):
        self.assertIsNone(W.koop(self.o, self.kind.id, self.kroon, 300, True))
        self.assertEqual(self.o.punten_saldo(self.kind.id), 200)
        self.assertIn(("hoed", "kroon"), W.in_kast(self.o, self.kind.id))
        self.assertTrue(W.draag(self.o, self.kind.id, "hoed", "kroon"))
        self.assertEqual(A.geldig(self.o.avatar(self.kind.id))["hoed"], "kroon")
        self.assertTrue(W.draag(self.o, self.kind.id, "hoed", None))  # hoed af

    def test_pakje_onderweg(self):
        lev = W.koop(self.o, self.kind.id, self.kroon, 300, False, "pakje")
        self.assertEqual(lev["soort"], "pakje")
        self.assertNotIn(("hoed", "kroon"), W.in_kast(self.o, self.kind.id))
        self.assertFalse(W.draag(self.o, self.kind.id, "hoed", "kroon"))
        self.juist_antwoorden(9)
        self.assertEqual(W.lever_pakjes(self.o, self.kind.id), [])
        self.juist_antwoorden(1)
        self.assertEqual(W.lever_pakjes(self.o, self.kind.id), [self.kroon])
        self.assertIn(("hoed", "kroon"), W.in_kast(self.o, self.kind.id))

    def test_pakje_na_oefentijd(self):
        W.koop(self.o, self.kind.id, self.kroon, 300, False, "tijd")
        self.juist_antwoorden(10, tijd_ms=60_000)  # 10 minuten
        self.assertEqual(W.lever_pakjes(self.o, self.kind.id), [])
        self.juist_antwoorden(5, tijd_ms=60_000)
        self.assertEqual(W.lever_pakjes(self.o, self.kind.id), [self.kroon])

    def test_verzendkosten(self):
        W.koop(self.o, self.kind.id, self.kroon, 300, False, "kosten")
        self.assertEqual(self.o.punten_saldo(self.kind.id), 500 - 300 - W.VERZENDKOSTEN)
        self.assertIn(("hoed", "kroon"), W.in_kast(self.o, self.kind.id))


class TestWinkelSchermen(Basis):
    def met_punten(self, punten, **opties):
        o = self.opslag(("Test", "5", opties))
        o.punten_bij(o.kinderen()[0].id, punten, "test")
        return o

    def naar_kleuren(self):
        # hoofdmenu → Mijn avatar → [W] winkel → 2 Kleuren → ↓ naar Groen
        return [OK, OK, hm("Mijn avatar"), "w", "2", curses.KEY_DOWN, OK]

    def test_kopen_met_juiste_som(self):
        o = self.met_punten(200)
        ch = W.Challenge("Je hebt 200 punten. Dit kost 30 punten. Hoeveel heb je over?", 170, 30, ["200 − 30"])
        with mock.patch.object(W, "challenge", return_value=ch):
            scherm, app = self.speel([*self.naar_kleuren(), *"170", OK, "1", ESC, ESC, ESC, ESC], opslag=o)
        self.assertEqual(o.punten_saldo(app.kind.id), 170)
        self.assertEqual(A.geldig(o.avatar(app.kind.id))["kleur"], "groen")
        self.assertTrue(self.ergens(scherm, "Goed gerekend!"))

    def test_ben_je_zeker_en_pakje(self):
        o = self.met_punten(200)
        ch = W.Challenge("Hoeveel heb je over?", 170, 30, ["200 − 30 = 170"])
        with mock.patch.object(W, "challenge", return_value=ch):
            scherm, app = self.speel([*self.naar_kleuren(), *"160", OK, *"180", OK, OK, ESC, ESC, ESC,
                                      ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Ben je zeker?"))
        self.assertTrue(self.ergens(scherm, "de koerier is verdwaald"))
        self.assertNotIn(("kleur", "groen"), W.in_kast(o, app.kind.id))
        self.assertEqual(len(W.onderweg(o, app.kind.id)), 1)
        self.assertEqual(o.punten_saldo(app.kind.id), 170)

    def test_te_weinig_punten(self):
        o = self.met_punten(10)
        scherm, app = self.speel([*self.naar_kleuren(), *"20", OK, OK, ESC, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Dat is nog te duur"))
        self.assertTrue(self.ergens(scherm, "Juist! Nog 20 punten sparen"))
        self.assertEqual(o.punten_saldo(app.kind.id), 10)

    def test_kast_en_combinatie(self):
        o = self.met_punten(0)
        kind = o.kinderen()[0]
        W.koop(o, kind.id, W.zoek("kleur", "groen"), 0, True)
        # kast: ↓ naar Kleuren, → wisselt naar de volgende kleur in de kast
        scherm, app = self.speel([OK, OK, hm("Mijn avatar"), "k", curses.KEY_DOWN, curses.KEY_RIGHT, "b",
                                  *"School", OK, ESC, ESC, ESC], opslag=o)
        self.assertEqual(A.geldig(o.avatar(kind.id))["kleur"], "groen")
        self.assertEqual([x["naam"] for x in o.outfits(kind.id)], ["School"])


if __name__ == "__main__":
    unittest.main()
