import curses
import random
import unittest
from decimal import Decimal
from unittest import mock

from leeravontuur.kern import leerjaren
from leeravontuur.kern.onderwerp import Vraag
from leeravontuur.kern.wiskunde import grootheden as T

try:
    from .test_schermen import ESC, OK, Basis, hm
except ImportError:
    from test_schermen import ESC, OK, Basis, hm

D = Decimal


class TestLezen(unittest.TestCase):
    def test_duur(self):
        for tekst, minuten in [("2 u 15 min", 135), ("2u15", 135), ("2 uur", 120), ("45 min", 45), ("45", 45),
                               ("1 u 5", 65), ("3 uur 20 minuten", 200)]:
            self.assertEqual(T.lees_duur(tekst), minuten, tekst)
        for fout in ("", "abc", "135 min", "2 u 75 min", "u"):
            self.assertIsNone(T.lees_duur(fout), fout)

    def test_klok(self):
        for tekst, minuten in [("11.15 u", 675), ("11:15", 675), ("11 u 15", 675), ("11u15", 675), ("9.05", 545),
                               ("11 u", 660), ("8", 480)]:
            self.assertEqual(T.lees_klok(tekst), minuten, tekst)
        for fout in ("", "11.75", "25.00", "abc", "11.5"):
            self.assertIsNone(T.lees_klok(fout), fout)

    def test_teksten(self):
        self.assertEqual(T.duur_tekst(95), "1 u 35 min")
        self.assertEqual(T.duur_tekst(120), "2 u")
        self.assertEqual(T.duur_tekst(45), "45 min")
        self.assertEqual(T.klok_tekst(545), "9.05 u")
        self.assertEqual(T.GELD.lees("€ 7,65"), D("7.65"))


class TestGeneratoren(unittest.TestCase):
    def test_alle_leerjaren(self):
        rng = random.Random(15)
        for o in T.ALLE:
            for jaar in leerjaren.LEERJAREN:
                if not o.aangeboden(jaar):
                    continue
                for _ in range(300):
                    v = o.maak(jaar, rng=rng)
                    self.assertTrue(v.sleutel.startswith(o.id + ":"))
                    self.assertIsNotNone(o.onderwerp_van_sleutel(v.sleutel))
                    self.assertTrue(o.uitleg(v))
                    o.tip(v)
                    self.assertTrue(o.nakijken(v, o.lees_vraag(v, v.verwacht)), (v.tekst, v.verwacht))
                    self.assertIsNone(o.diagnose(v, v.antwoord))

    def test_niveaus(self):
        self.assertTrue(T.TIJD.aangeboden("3"))
        self.assertFalse(T.SNELHEID.aangeboden("5"))
        self.assertTrue(T.SNELHEID.aangeboden("6"))
        for _ in range(100):  # km/u ↔ m/s pas in het 1ste middelbaar
            self.assertNotEqual(T.SNELHEID.maak("6").data["soort"], "omzetten")

    def test_spiekbrief_past(self):
        for t, _ in T.SPIEKBRIEF:
            self.assertLessEqual(len(t), 78, t)


class TestDiagnose(unittest.TestCase):
    def test_tijd(self):
        v = Vraag(T.TIJD.id, "k", "", D(135), data={"soort": "gemengd_naar", "u": 2, "m": 15})
        self.assertEqual(T.TIJD.diagnose(v, D(215))[0], "tijd_met_100")
        w = Vraag(T.TIJD.id, "k", "", D(135), invoer="duur", data={"soort": "naar_gemengd", "u": 2, "m": 15})
        self.assertEqual(T.TIJD.diagnose(w, T.lees_duur("1 u 35 min"))[0], "tijd_met_100")
        o = Vraag(T.TIJD.id, "k", "", D(180), data={"soort": "omrekenen", "i": 0, "n": 3, "richting": "naar_klein"})
        self.assertEqual(T.TIJD.diagnose(o, D(300))[0], "tijd_met_100")
        self.assertEqual(T.TIJD.diagnose(o, D(3) / 60)[0], "tijd_verkeerde_kant")
        # 8.45 u tot 10.20 u = 95 min; wie aftrekt als kommagetallen krijgt 1020 − 845 = 175
        du = Vraag(T.TIJD.id, "k", "", D(95), data={"soort": "duur", "begin": 525, "duur": 95})
        self.assertEqual(T.TIJD.diagnose(du, D(175))[0], "tijd_met_100")
        self.assertIn("8.45 u tot 9.00 u is 15 min", T.TIJD.uitleg(du)[0])
        # 9.40 u + 1 u 35 min = 11.15 u; zonder het extra uur: 10.15 u
        e = Vraag(T.TIJD.id, "k", "", D(675), invoer="klok", data={"soort": "eindtijd", "begin": 580, "duur": 95})
        self.assertEqual(T.TIJD.diagnose(e, T.lees_klok("10.15"))[0], "tijd_uur_vergeten")

    def test_geld_en_snelheid(self):
        v = Vraag(T.GELD.id, "k", "", D(345), data={"soort": "euro_naar_cent", "cent": 345})
        self.assertEqual(T.GELD.diagnose(v, D("34.5"))[0], "geld_komma")
        w = Vraag(T.GELD.id, "k", "", D("7.65"), data={"soort": "wisselgeld", "prijs": "12.35", "briefje": 20})
        self.assertEqual(T.GELD.diagnose(w, D("32.35"))[0], "wisselgeld_opgeteld")
        s = Vraag(T.SNELHEID.id, "k", "", D(9), data={"soort": "afstand", "v": 18, "min": 30, "km": "9"})
        self.assertEqual(T.SNELHEID.diagnose(s, D(540))[0], "snelheid_minuten")
        self.assertEqual(T.SNELHEID.diagnose(s, D(36))[0], "snelheid_bewerking")
        self.assertIn("30 min = 0,5 u", T.SNELHEID.uitleg(s)[1])
        m = Vraag(T.SNELHEID.id, "k", "", D(10), data={"soort": "omzetten", "richting": "naar_ms", "kmu": "36", "ms": 10})
        self.assertEqual(T.SNELHEID.diagnose(m, D("129.6"))[0], "snelheid_3_6")


def gemengd():
    return Vraag(T.TIJD.id, f"{T.TIJD.id}:naar_gemengd:135", "135 min = ? u ? min", D(135), invoer="duur",
                 data={"soort": "naar_gemengd", "onderwerp": "naar_gemengd", "u": 2, "m": 15},
                 verwacht_tekst="2 u 15 min")


def naar(onderwerp):
    """Wiskunde → Tijd, geld en snelheid → onderwerp → Vrij oefenen → Normaal."""
    return [OK, OK, hm("Leren & oefenen"), "1", "7", str(onderwerp), "1", OK]


STOP = [ESC] * 7


class TestSchermen(Basis):
    def test_uren_en_minuten_typen(self):
        o = self.opslag(("Test", "5"))
        with mock.patch.object(T.TIJD, "maak", side_effect=[gemengd(), gemengd()]):
            scherm, app = self.speel([*naar(1), *"135", OK, *[curses.KEY_BACKSPACE] * 3, *"2 u 15 min", OK, *STOP],
                                     opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertEqual(rij["gegeven"], "2 u 15 min")
        self.assertTrue(rij["juist"])
        self.assertTrue(self.ergens(scherm, "Minuten: hoogstens 59"))  # '135' alleen is geen antwoord

    def test_spiekbrief(self):
        scherm, _ = self.speel([OK, OK, hm("Spiekbrieven"), "7", ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Een uur heeft 60 minuten"))


if __name__ == "__main__":
    unittest.main()
