"""De klok: Vlaamse woorden, vragen per leerjaar, denkfouten, de getekende wijzerklok en de wijzers zetten."""

import curses
import math
import random
import unittest
from decimal import Decimal

from leeravontuur.kern.instellingen import Instellingen
from leeravontuur.kern.modellen import Wijzerklok
from leeravontuur.kern.wiskunde import klok as K
from leeravontuur.kern.wiskunde import vraagstukken as VS
from leeravontuur.terminal import modellen as M
from leeravontuur.terminal.balk import KlokInvoer
from leeravontuur.terminal.nepscherm import NepScherm
from leeravontuur.terminal.scherm import Scherm

O = K.KLOK


def maak(jaar, soort, zaad=1):
    return O.maak_met(O.parameters(jaar), random.Random(zaad), {"soort": soort})


class TestWoorden(unittest.TestCase):
    def test_heen_en_terug(self):
        for t in range(0, 720, 5):
            self.assertEqual(K.lees_woorden(K.woorden(t)), t, K.woorden(t))

    def test_vlaamse_woorden(self):
        self.assertEqual(K.woorden(3 * 60 + 30), "half vier")
        self.assertEqual(K.woorden(3 * 60 + 25), "vijf voor half vier")
        self.assertEqual(K.woorden(3 * 60 + 40), "tien over half vier")
        self.assertEqual(K.woorden(11 * 60 + 55), "vijf voor twaalf")
        self.assertEqual(K.woorden(0), "twaalf uur")

    def test_andere_schrijfwijzen(self):
        for tekst, t in [("5 voor half 4", 205), ("twintig over drie", 200), ("3 uur", 180), ("3.25", 205),
                         ("het is kwart over drie", 195), ("half een", 30)]:
            self.assertEqual(K.lees_woorden(tekst), t, tekst)
        for tekst in ["", "banaan", "half", "vijftig over drie"]:
            self.assertIsNone(K.lees_woorden(tekst), tekst)


class TestVragen(unittest.TestCase):
    def test_elke_soort_in_elk_leerjaar(self):
        for jaar in ["3", "4", "5", "6", "m1"]:
            p = O.parameters(jaar)
            for soort in p["soorten"]:
                for zaad in range(30):
                    v = maak(jaar, soort, zaad)
                    with self.subTest(jaar=jaar, soort=soort, zaad=zaad):
                        if v.invoer == "wijzers":
                            self.assertTrue(O.nakijken(v, v.antwoord))
                        else:
                            self.assertTrue(O.nakijken(v, O.lees_vraag(v, v.verwacht)), v.verwacht)
                        self.assertIsNone(O.diagnose(v, v.antwoord))
                        self.assertTrue(O.uitleg(v))

    def test_een_wijzerklok_toont_12_uur(self):
        v = maak("5", "lezen", 3)
        self.assertTrue(O.nakijken(v, v.antwoord + 720))  # 15.15 = 3.15 op de klok

    def test_24_uur_moet_juist(self):
        v = maak("5", "24uur", 3)
        self.assertFalse(O.nakijken(v, v.antwoord - 720))
        self.assertEqual(O.diagnose(v, v.antwoord - 720)[0], "klok_24")

    def test_24_uur_vraag_is_duidelijk(self):
        """#21: "Hoe laat is het in 24 uur?" leek te vragen wat het over een dag is (dan is het hetzelfde uur)."""
        v = maak("5", "24uur", 3)
        self.assertNotIn("in 24 uur", v.tekst)
        self.assertIn("digitale klok (24-urennotatie)", v.tekst)

    def test_denkfouten(self):
        v = O.maak_met(O.parameters("5"), random.Random(1), {"soort": "lezen"})
        v.antwoord, v.data["t"] = Decimal(3 * 60 + 40), 3 * 60 + 40   # 3.40: de lange wijzer op 8, de korte bij 3
        self.assertEqual(O.diagnose(v, Decimal(8 * 60 + 15))[0], "klok_wijzers")
        self.assertEqual(O.diagnose(v, Decimal(4 * 60 + 40))[0], "klok_uur_te_ver")
        w = maak("5", "woorden_naar", 1)
        w.antwoord, w.data["t"] = Decimal(3 * 60 + 30), 3 * 60 + 30  # half vier
        self.assertEqual(O.diagnose(w, Decimal(4 * 60 + 30))[0], "klok_half")
        w.antwoord, w.data["t"] = Decimal(3 * 60 + 25), 3 * 60 + 25  # vijf voor half vier
        self.assertEqual(O.diagnose(w, Decimal(4 * 60 + 25))[0], "klok_half")
        n = maak("5", "naar_woorden", 1)
        n.antwoord, n.data["t"] = Decimal(3 * 60 + 25), 3 * 60 + 25
        fout = O.lees_vraag(n, "vijf voor half drie")
        self.assertEqual(O.diagnose(n, fout)[0], "klok_half")
        self.assertIn("vijf voor half vier", O.diagnose(n, fout)[1])
        later = maak("5", "later", 1)
        b, du = later.data["begin"], later.data["duur"]
        self.assertEqual(O.diagnose(later, Decimal(b - du))[0], "klok_richting")


class TestTekenen(unittest.TestCase):
    def test_wijzers_op_de_juiste_plek(self):
        for t in range(0, 720, 7):
            p = M.klok_pixels(Wijzerklok(t))
            uur, minuut = Wijzerklok(t).hoeken()
            r = M.KLOK_R
            for rol, hoek, afstand in (("vulling", minuut, r - 2.5), ("rand", uur, r * 0.45)):
                x = round(r + afstand * math.sin(math.radians(hoek)))
                y = round(r - afstand * math.cos(math.radians(hoek)))
                buren = {p[yy][xx] for yy in range(y - 1, y + 2) for xx in range(x - 1, x + 2)}
                self.assertIn(rol, buren, (t, rol))

    def test_past_en_ascii(self):
        for ascii_ in (False, True):
            win = NepScherm()
            inst = Instellingen()
            inst.ascii = ascii_
            s = Scherm(win, inst, kleuren=False)
            h, b = M.teken_klok(s, 9, Wijzerklok(195), 8)
            self.assertEqual((h, b), (13, 25))
            beeld = ["".join(r) for r in win.raster]
            self.assertIn("12", beeld[9])
            self.assertIn("#", "".join(beeld))   # de uurwijzer
            self.assertIn("*", "".join(beeld))   # de minutenwijzer
            if ascii_:
                self.assertTrue(all(ord(c) < 128 for c in "".join(beeld)))


class TestWijzersZetten(unittest.TestCase):
    def test_toetsen_en_klikken(self):
        v = maak("5", "zetten", 2)
        obj = KlokInvoer(v, O)
        obj.t = 180
        obj.toets(curses.KEY_RIGHT)
        obj.toets(curses.KEY_UP)
        obj.toets(ord("+"))
        self.assertEqual(obj.t, 4 * 60 + 6)
        obj.toets(("wijzer", 0, -8))  # de lange wijzer recht naar boven: een vol uur
        self.assertEqual(obj.t % 60, 0)
        obj.toets(("wijzer", 8, 0))   # naar rechts: kwart over
        self.assertEqual(obj.t % 60, 15)
        uit = obj.toets(10)
        self.assertEqual(uit[1], Decimal(obj.t))


class TestTijdInVraagstukken(unittest.TestCase):
    def test_klad_en_antwoord(self):
        o = VS.VRAAGSTUKKEN
        v = o.maak_met(o.parameters("5"), random.Random(4), {"structuur": "tijdsduur", "variant": "eind"})
        g = v.model.gegevens
        regel = f"{VS.tekst_getal(g['b'].waarde, 'klok')} + {VS.tekst_getal(g['d'].waarde, 'duur')} = {v.verwacht}"
        a = VS.analyseer_klad(v.model, [regel])
        self.assertEqual(a["status"], ["goed"], regel)
        self.assertTrue(o.nakijken(v, o.lees_vraag(v, v.verwacht.replace(" u", ""))))
        v = o.maak_met(o.parameters("5"), random.Random(4), {"structuur": "tijdsduur", "variant": "duur"})
        self.assertTrue(o.nakijken(v, o.lees_vraag(v, v.verwacht)))
        self.assertTrue(o.nakijken(v, o.lees_vraag(v, str(int(v.antwoord)))))  # in minuten mag ook


if __name__ == "__main__":
    unittest.main()
