import curses
import random
import unittest
from decimal import ROUND_HALF_UP, Decimal
from unittest import mock

from leeravontuur.kern import leerjaren
from leeravontuur.kern.modellen import Getallenlijn, lijn_rond
from leeravontuur.kern.onderwerp import Vraag
from leeravontuur.kern.wiskunde import getallen as G
from leeravontuur.terminal import modellen as M

try:
    from .test_schermen import ESC, OK, Basis, hm
except ImportError:
    from test_schermen import ESC, OK, Basis, hm

D = Decimal
LINKS, RECHTS = curses.KEY_LEFT, curses.KEY_RIGHT


def bereikbaar(lijn, waarde, minste):
    """Kan je waarde aanduiden door (eventueel herhaald) in te zoomen?"""
    while True:
        if waarde in lijn.streepjes():
            return True
        if not lijn.kan_inzoomen(minste) or not lijn.van <= waarde <= lijn.tot:
            return False
        lijn = lijn.inzoomen(lijn.van + (waarde - lijn.van) // lijn.stap * lijn.stap)


class TestGeneratoren(unittest.TestCase):
    def test_alle_leerjaren(self):
        rng = random.Random(9)
        for o in G.ALLE:
            for jaar in leerjaren.LEERJAREN:
                if not o.aangeboden(jaar):
                    continue
                for _ in range(300):
                    v = o.maak(jaar, rng=rng)
                    self.assertTrue(v.sleutel.startswith(o.id + ":"))
                    self.assertTrue(o.uitleg(v))
                    o.tip(v)
                    o.diagnose(v, v.antwoord if isinstance(v.antwoord, str) else v.antwoord + 1)
                    self.assertIsNotNone(o.onderwerp_van_sleutel(v.sleutel), v.sleutel)
                    self.controleer(o, v)

    def controleer(self, o, v):
        d = v.data
        if o is G.PLAATSWAARDE:
            g = D(d["getal"])
            cijfer = int(abs(g).scaleb(-d["k"])) % 10
            if d["soort"] == "cijfer":
                self.assertEqual(v.antwoord, cijfer)
            elif d["soort"] == "waarde":
                self.assertEqual(v.antwoord, D(cijfer).scaleb(d["k"]))
            else:
                self.assertEqual(v.antwoord, sum(D(c).scaleb(k) for k, c in d["delen"]))
        elif o is G.AFRONDEN:
            g, k = D(d["getal"]), d["k"]
            self.assertEqual(v.antwoord, (g / D(10) ** k).quantize(D(1), rounding=ROUND_HALF_UP) * D(10) ** k)
        elif o is G.DEELBAARHEID and d["soort"] == "deelbaar":
            self.assertEqual(v.antwoord, "ja" if d["n"] % d["deler"] == 0 else "nee")
            self.assertEqual(v.invoer, "janee")
        elif o is G.GETALLENLIJN:
            lijn = v.model
            self.assertIsInstance(lijn, Getallenlijn)
            self.assertLessEqual(len(lijn.streepjes()), 31)
            if d["soort"] == "aflezen":
                self.assertEqual(lijn.pijl, v.antwoord)
                self.assertIn(v.antwoord, lijn.streepjes())
            elif d["soort"] == "aanduiden":
                self.assertEqual(v.invoer, "lijn")
                self.assertTrue(bereikbaar(lijn, v.antwoord, D(d["minste"])), v.tekst)
            elif d["soort"] == "sprong":
                self.assertEqual(v.antwoord, d["a"] + d["sprong"])
                self.assertTrue(lijn.van <= d["a"] <= lijn.tot and lijn.van <= v.antwoord <= lijn.tot)
            else:
                self.assertEqual(v.antwoord, d["nu"] + d["verschil"])

    def test_negatief_pas_vanaf_5(self):
        rng = random.Random(2)
        for _ in range(200):
            v = G.GETALLENLIJN.maak("4", rng=rng)
            self.assertGreaterEqual(v.model.van, 0)
            self.assertNotEqual(v.data["soort"], "temperatuur")
        self.assertTrue(any(G.GETALLENLIJN.maak("5", rng=rng).model.van < 0 for _ in range(200)))

    def test_ggd_kgv_pas_vanaf_6(self):
        rng = random.Random(3)
        self.assertFalse({G.DEELBAARHEID.maak("5", rng=rng).data["soort"] for _ in range(200)} & {"ggd", "kgv", "priem"})
        self.assertTrue({G.DEELBAARHEID.maak("6", rng=rng).data["soort"] for _ in range(200)} >= {"ggd", "kgv", "priem"})

    def test_herhaling_behoudt_soort(self):
        v = G.DEELBAARHEID.maak("5", data={"soort": "deelbaar", "deler": 9})
        data = G.DEELBAARHEID.herhaal_data(v)
        self.assertEqual(data["onderwerp"], "deelbaar door 9")
        for _ in range(20):
            self.assertEqual(G.DEELBAARHEID.maak_herhaling(data, "5").data["deler"], 9)


class TestDiagnose(unittest.TestCase):
    def test_plaatswaarde(self):
        v = G.PLAATSWAARDE.maak("5", data={"soort": "waarde"})
        k, g = v.data["k"], D(v.data["getal"])
        cijfer = D(int(g.scaleb(-k)) % 10)
        if k != 0:
            self.assertEqual(G.PLAATSWAARDE.diagnose(v, cijfer)[0], "cijfer_ipv_waarde")

    def test_afronden(self):
        v = Vraag(G.AFRONDEN.id, "k", "Rond 3 467 af op honderdtallen:", D(3500), data={"getal": "3467", "k": 2})
        self.assertEqual(G.AFRONDEN.diagnose(v, D(3400))[0], "afgekapt")
        self.assertEqual(G.AFRONDEN.diagnose(v, D(3470))[0], "verkeerde_plaats_afronden")
        self.assertIn("6 is 5 of meer", " ".join(G.AFRONDEN.uitleg(v)))

    def test_deelbaarheid_uitleg(self):
        v = Vraag(G.DEELBAARHEID.id, "k", "Is 2 853 deelbaar door 9?", "ja", invoer="janee",
                  data={"soort": "deelbaar", "deler": 9, "n": 2853})
        self.assertIn("2 + 8 + 5 + 3 = 18", " ".join(G.DEELBAARHEID.uitleg(v)))
        self.assertEqual(G.DEELBAARHEID.diagnose(v, "nee")[0], "kenmerk")
        self.assertEqual(G.DEELBAARHEID.lees_vraag(v, " Neen "), "nee")
        self.assertEqual(G.DEELBAARHEID.lees_vraag(v, "j"), "ja")
        self.assertIsNone(G.DEELBAARHEID.lees_vraag(v, "misschien"))

    def test_getallenlijn(self):
        v = G.GETALLENLIJN.maak("5", data={"soort": "sprong"})
        self.assertEqual(G.GETALLENLIJN.diagnose(v, D(v.data["a"] - v.data["sprong"]))[0], "sprong_verkeerde_kant")
        w = Vraag(G.GETALLENLIJN.id, "k", "Duid 23,7 aan", D("23.7"), invoer="lijn", model=lijn_rond(20, 30, 1),
                  data={"soort": "aanduiden", "stap": "1", "fijn": "0.1", "minste": "0.1"})
        self.assertEqual(G.GETALLENLIJN.diagnose(w, D(24))[0], "niet_ingezoomd")
        self.assertEqual(G.GETALLENLIJN.diagnose(w, D("23.8"))[0], "streepje_ernaast")


class TestModel(unittest.TestCase):
    def test_inzoomen(self):
        lijn = lijn_rond(20, 30, 1, label_elke=5)
        self.assertEqual(len(lijn.streepjes()), 11)
        z = lijn.inzoomen(D(23))
        self.assertEqual((z.van, z.tot, z.stap), (23, 24, D("0.1")))
        self.assertIn(D("23.7"), z.streepjes())
        self.assertFalse(z.kan_inzoomen(D("0.1")))
        self.assertTrue(z.kan_inzoomen(D("0.01")))
        self.assertEqual(lijn.dichtst(D("23.4")), 23)

    def test_posities_passen_in_80(self):
        for lijn in (lijn_rond(20, 30, 1), lijn_rond(-15, 15, 1), lijn_rond(-5, 20, 1)):
            xs, _ = M.posities(lijn)
            self.assertLessEqual(xs[-1] + 4, 79)


def aanduid_vraag():
    return Vraag(G.GETALLENLIJN.id, f"{G.GETALLENLIJN.id}:aanduiden:23.7", "Duid 23,7 aan op de getallenlijn.",
                 D("23.7"), invoer="lijn", model=lijn_rond(20, 30, 1, label_elke=5),
                 data={"soort": "aanduiden", "stap": "1", "fijn": "0.1", "minste": "0.1", "onderwerp": "aanduiden"})


# Wiskunde (1) → Getallen (3) → Getallenlijn (4) → Vrij oefenen (1) → Normaal (Enter)
NAAR_LIJN = [OK, OK, hm("Leren & oefenen"), "1", "3", "4", "1", OK]


class TestSchermen(Basis):
    def test_aanduiden_met_inzoomen(self):
        o = self.opslag(("Test", "5"))
        with mock.patch.object(G.GETALLENLIJN, "maak", side_effect=[aanduid_vraag(), aanduid_vraag()]):
            scherm, app = self.speel([*NAAR_LIJN, RECHTS, RECHTS, RECHTS, "+", *[RECHTS] * 7, OK, ESC, ESC, ESC,
                                      ESC, ESC, ESC], opslag=o)
        rijen = o.antwoorden(app.kind.id)
        self.assertEqual(len(rijen), 1)
        self.assertTrue(rijen[0]["juist"])
        self.assertEqual(rijen[0]["gegeven"], "23,7")
        self.assertTrue(self.ergens(scherm, "Ingezoomd (1×): tussen 23 en 24"))
        self.assertTrue(self.ergens(scherm, "✔"))

    def test_klikken_en_niet_ingezoomd(self):
        o = self.opslag(("Test", "5"))
        xs, _ = M.posities(lijn_rond(20, 30, 1))
        with mock.patch.object(G.GETALLENLIJN, "maak", side_effect=[aanduid_vraag(), aanduid_vraag()]):
            scherm, app = self.speel([*NAAR_LIJN, ("klik", 10, xs[4]), OK, OK, ESC, ESC, ESC, ESC, ESC, ESC], opslag=o)
        rijen = o.antwoorden(app.kind.id)
        self.assertEqual(rijen[0]["gegeven"], "24")
        self.assertFalse(rijen[0]["juist"])
        self.assertEqual(rijen[0]["diagnose"], "niet_ingezoomd")
        self.assertTrue(self.ergens(scherm, "Zoom in met +"))

    def test_uitzoomen(self):
        o = self.opslag(("Test", "5"))
        with mock.patch.object(G.GETALLENLIJN, "maak", side_effect=[aanduid_vraag(), aanduid_vraag()]):
            scherm, app = self.speel([*NAAR_LIJN, RECHTS, RECHTS, "+", "-", RECHTS, OK, OK, ESC, ESC, ESC, ESC, ESC, ESC],
                                     opslag=o)
        self.assertEqual(o.antwoorden(app.kind.id)[0]["gegeven"], "23")

    def test_ja_nee(self):
        o = self.opslag(("Test", "5"))
        vragen = [Vraag(G.DEELBAARHEID.id, f"{G.DEELBAARHEID.id}:deelbaar:9:{n}", f"Is {n} deelbaar door 9? (ja of nee)",
                        "ja" if n % 9 == 0 else "nee", invoer="janee",
                        data={"soort": "deelbaar", "deler": 9, "n": n, "onderwerp": "deelbaar door 9"})
                  for n in (2853, 2854, 18)]
        with mock.patch.object(G.DEELBAARHEID, "maak", side_effect=vragen):
            scherm, app = self.speel([OK, OK, hm("Leren & oefenen"), "1", "3", "3", "1", OK, *"misschien", OK,
                                      *"\b" * 9, *"ja", OK, OK, *"ja", OK, OK, ESC, ESC, ESC, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Typ ja of nee."))
        rijen = o.antwoorden(app.kind.id)
        self.assertEqual([r["juist"] for r in rijen], [1, 0])
        self.assertEqual(rijen[1]["diagnose"], "kenmerk")
        self.assertTrue(self.ergens(scherm, "Juist is: nee") or self.ergens(scherm, "juiste antwoord is nee"))

    def test_spiekbrief(self):
        scherm, _ = self.speel([OK, OK, hm("Spiekbrieven"), "3", ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "DEELBAAR DOOR"))


if __name__ == "__main__":
    unittest.main()
