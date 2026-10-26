import curses
import random
import unittest
from decimal import Decimal
from fractions import Fraction
from unittest import mock

from leeravontuur.kern import leerjaren
from leeravontuur.kern.getal import GetypteBreuk, fmt_breuk, lees_breuk
from leeravontuur.kern.modellen import Breukbalk, Breukbalken, Groepjes
from leeravontuur.kern.onderwerp import Vraag
from leeravontuur.kern.wiskunde import breuken as B
from leeravontuur.terminal import modellen as M

try:
    from .test_schermen import ESC, OK, Basis, naar_spiekbrief
    from .test_schermen import naar as naar_onderwerp
except ImportError:
    from test_schermen import ESC, OK, Basis, naar_spiekbrief
    from test_schermen import naar as naar_onderwerp

F = Fraction
D = Decimal
RECHTS, OP = curses.KEY_RIGHT, curses.KEY_UP


class TestLezen(unittest.TestCase):
    def test_lees_breuk(self):
        self.assertEqual(lees_breuk("3/4"), GetypteBreuk(0, 3, 4))
        self.assertEqual(lees_breuk("1 3/4").waarde, F(7, 4))
        self.assertEqual(lees_breuk("-2/5").waarde, F(-2, 5))
        self.assertEqual(lees_breuk("5").waarde, 5)
        self.assertFalse(lees_breuk("4/6").eenvoudigst)
        for onzin in ("", "x", "3/0", "1/2/3", "3,5"):
            self.assertIsNone(lees_breuk(onzin), onzin)
        self.assertEqual(fmt_breuk(F(7, 4), gemengd=True), "1 3/4")
        self.assertEqual(fmt_breuk(F(-1, 2)), "−1/2")


class TestGeneratoren(unittest.TestCase):
    def test_alle_leerjaren(self):
        rng = random.Random(11)
        for o in B.ALLE:
            for jaar in leerjaren.LEERJAREN:
                if not o.aangeboden(jaar):
                    continue
                for _ in range(300):
                    v = o.maak(jaar, rng=rng)
                    self.assertTrue(v.sleutel.startswith(o.id + ":"))
                    self.assertIsNotNone(o.onderwerp_van_sleutel(v.sleutel))
                    self.assertTrue(o.uitleg(v))
                    o.tip(v)
                    self.controleer(o, v)
                    # het getoonde juiste antwoord wordt zelf als juist nagekeken
                    self.assertTrue(o.nakijken(v, o.lees_vraag(v, v.verwacht)), (v.tekst, v.verwacht))
                    for model in (v.model, v.model_na):
                        self.past(model)

    def past(self, model):
        if isinstance(model, Breukbalk):
            self.assertLessEqual(model.noemer, B.BALK_MAX)
        elif isinstance(model, Breukbalken):
            self.assertTrue(all(b.noemer <= B.BALK_MAX for b in model.balken))
        elif isinstance(model, Groepjes):
            self.assertLessEqual(model.groepen, 12)
            self.assertEqual(model.totaal % model.groepen, 0)

    def controleer(self, o, v):
        d = v.data
        s = d["soort"]
        if o is B.HERKENNEN:
            self.assertEqual(v.antwoord, F(d["t"], d["n"]))
        elif o is B.GELIJKWAARDIG:
            if s == "vereenvoudigen":
                self.assertEqual(v.antwoord.numerator, d["t"])
                self.assertEqual(v.antwoord, F(d["t"] * d["f"], d["n"] * d["f"]))
            elif s == "aanvullen":
                self.assertEqual(v.antwoord, d["t"] * d["f"] if d["vraag"] == "teller" else d["n"] * d["f"])
        elif o is B.VERGELIJKEN:
            x, y = F(d["a"], d["b"]), F(d["c"], d["d"])
            self.assertEqual(v.antwoord, "<" if x < y else ">" if x > y else "=")
        elif o is B.OPTELLEN:
            x, y = F(d["x"]), F(d["y"])
            self.assertEqual(v.antwoord, x + y if d["op"] == "+" else x - y)
        elif o is B.BREUK_VAN:
            if s == "van":
                self.assertEqual(v.antwoord, F(d["t"], d["n"]) * d["g"])
            else:
                x, y = F(d["x"]), F(d["y"])
                self.assertEqual(v.antwoord, x * y if s.startswith("maal") else x / y)
        elif o is B.KOMMAGETAL:
            self.assertEqual(F(v.antwoord), F(d["t"], d["n"]))

    def test_niveaus(self):
        self.assertFalse(B.OPTELLEN.aangeboden("3"))
        self.assertTrue(B.HERKENNEN.aangeboden("3"))
        rng = random.Random(2)
        soorten = {B.BREUK_VAN.maak("5", rng=rng).data["soort"] for _ in range(100)}
        self.assertEqual(soorten, {"van", "maal_nat"})


class TestDiagnose(unittest.TestCase):
    def test_tellers_en_noemers(self):
        v = Vraag(B.OPTELLEN.id, "k", "1/2 + 1/3 =", F(5, 6), invoer="breuk",
                  data={"soort": "ongelijknamig", "x": "1/2", "y": "1/3", "op": "+", "vereenvoudigd": True})
        self.assertEqual(B.OPTELLEN.diagnose(v, lees_breuk("2/5"))[0], "tellers_en_noemers")
        self.assertEqual(B.OPTELLEN.diagnose(v, lees_breuk("2/3"))[0], "niet_gelijknamig")
        self.assertIn("1/2 = 3/6 en 1/3 = 2/6", " ".join(B.OPTELLEN.uitleg(v)))

    def test_niet_vereenvoudigd(self):
        v = B.GELIJKWAARDIG.maak("5", data={"soort": "vereenvoudigen"})
        t, n = v.data["t"], v.data["n"]
        half = lees_breuk(f"{t * 2}/{n * 2}")
        self.assertFalse(B.GELIJKWAARDIG.nakijken(v, half))
        self.assertEqual(B.GELIJKWAARDIG.diagnose(v, half)[0], "niet_vereenvoudigd")
        self.assertTrue(B.GELIJKWAARDIG.nakijken(v, lees_breuk(f"{t}/{n}")))

    def test_waarde_telt_bij_herkennen(self):
        v = Vraag(B.HERKENNEN.id, "k", "", F(2, 4), invoer="breuk", data={"soort": "aflezen", "t": 2, "n": 4})
        self.assertTrue(B.HERKENNEN.nakijken(v, lees_breuk("1/2")))
        self.assertEqual(B.HERKENNEN.diagnose(v, lees_breuk("4/2"))[0], "teller_noemer_omgewisseld")
        w = Vraag(B.HERKENNEN.id, "k", "", F(3, 5), invoer="breuk", data={"soort": "aflezen", "t": 3, "n": 5})
        self.assertEqual(B.HERKENNEN.diagnose(w, lees_breuk("2/5"))[0], "ongearceerd_geteld")

    def test_vergelijken_en_van(self):
        v = Vraag(B.VERGELIJKEN.id, "k", "", ">", invoer="vergelijk", data={"a": 1, "b": 3, "c": 1, "d": 5})
        self.assertEqual(B.VERGELIJKEN.diagnose(v, "<")[0], "grotere_noemer_groter")
        w = Vraag(B.BREUK_VAN.id, "k", "", D(8), data={"soort": "van", "t": 2, "n": 3, "g": 12})
        self.assertEqual(B.BREUK_VAN.diagnose(w, D(4))[0], "alleen_gedeeld")
        z = Vraag(B.BREUK_VAN.id, "k", "", F(3, 2), invoer="breuk",
                  data={"soort": "deel_breuk", "x": "3/4", "y": "1/2"})
        self.assertEqual(B.BREUK_VAN.diagnose(z, lees_breuk("3/8"))[0], "niet_omgekeerd")
        k = Vraag(B.KOMMAGETAL.id, "k", "", D("0.75"), data={"soort": "naar_komma", "t": 3, "n": 4})
        self.assertEqual(B.KOMMAGETAL.diagnose(k, D("3.4"))[0], "breuk_als_komma")


class TestModel(unittest.TestCase):
    def test_vereenvoudig(self):
        b = Breukbalk.van(4, 8)
        self.assertEqual((b.vereenvoudig().teller, b.vereenvoudig().noemer), (2, 4))
        self.assertIsNone(Breukbalk.van(3, 5).vereenvoudig())

    def test_balk_past(self):
        for n in range(1, 21):
            grenzen = M.stuk_grenzen(n, 8)
            self.assertEqual(grenzen[-1][1], 8 + M.BALK_B)
            self.assertTrue(all(b - a >= 2 for a, b in grenzen))


def arceer_vraag():
    return Vraag(B.HERKENNEN.id, f"{B.HERKENNEN.id}:arceren:3/5", "Arceer 3/5 van de balk.", F(3, 5), invoer="balk",
                 model=Breukbalk(5), data={"soort": "arceren", "t": 3, "n": 5, "noemer_vast": True,
                                           "onderwerp": "arceren"}, verwacht_tekst="3/5")


def toon_vraag():
    return Vraag(B.GELIJKWAARDIG.id, f"{B.GELIJKWAARDIG.id}:balk:3/4:8", "Toon 3/4 met 8 stukken:", F(3, 4),
                 invoer="balk", model=Breukbalk(4), verwacht_tekst="6/8",
                 data={"soort": "balk", "t": 3, "n": 4, "f": 2, "noemer": 8, "onderwerp": "balk"})


def naar(onderwerp):
    """Wiskunde › domein › het onderwerp met dit nummer in B.ALLE › V (vrij oefenen) › Normaal."""
    return naar_onderwerp(B.ALLE[onderwerp - 1])


STOP = [ESC] * 7


class TestSchermen(Basis):
    def test_arceren_met_toetsen_en_klik(self):
        o = self.opslag(("Test", "5"))
        a, b = M.stuk_grenzen(5, 8)[2]
        with mock.patch.object(B.HERKENNEN, "maak", side_effect=[arceer_vraag(), arceer_vraag()]):
            scherm, app = self.speel([*naar(1), " ", RECHTS, " ", ("klik", 9, a + 2), OK, *STOP], opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertEqual(rij["gegeven"], "3/5")
        self.assertTrue(rij["juist"])
        self.assertTrue(self.ergens(scherm, "3/5"))

    def test_noemer_kiezen(self):
        o = self.opslag(("Test", "5"))
        toetsen = [OP] * 4 + [" ", RECHTS] * 6
        with mock.patch.object(B.GELIJKWAARDIG, "maak", side_effect=[toon_vraag(), toon_vraag()]):
            scherm, app = self.speel([*naar(2), *toetsen, OK, *STOP], opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertEqual(rij["gegeven"], "6/8")
        self.assertTrue(rij["juist"])

    def test_vereenvoudigen_met_v(self):
        o = self.opslag(("Test", "5"))
        toetsen = [OP] * 4 + [" ", RECHTS] * 4 + ["v", "v"]  # 4/8 → 2/4 → 1/2
        with mock.patch.object(B.GELIJKWAARDIG, "maak", side_effect=[toon_vraag(), toon_vraag()]):
            scherm, app = self.speel([*naar(2), *toetsen, OK, OK, *STOP], opslag=o)  # fout: tweede kans, nog eens
        self.assertTrue(self.ergens(scherm, "Samengevoegd: 4/8 = 2/4"))
        rij = o.antwoorden(app.kind.id)[0]
        self.assertEqual(rij["gegeven"], "1/2")
        self.assertFalse(rij["juist"])

    def test_getypte_breuk_niet_vereenvoudigd(self):
        o = self.opslag(("Test", "5"))
        v = Vraag(B.GELIJKWAARDIG.id, f"{B.GELIJKWAARDIG.id}:vereenvoudigen:18/24", "Vereenvoudig 18/24:", F(3, 4),
                  invoer="breuk", data={"soort": "vereenvoudigen", "t": 3, "n": 4, "f": 6, "vereenvoudigd": True,
                                        "onderwerp": "vereenvoudigen"})
        with mock.patch.object(B.GELIJKWAARDIG, "maak", side_effect=[v, v]):
            scherm, app = self.speel([*naar(2), *"xx", OK, "\b", "\b", *"6/8", OK, *"6/8", OK, *STOP], opslag=o)
        self.assertTrue(self.ergens(scherm, "Typ een breuk"))
        rij = o.antwoorden(app.kind.id)[0]
        self.assertFalse(rij["juist"])
        self.assertEqual(rij["diagnose"], "niet_vereenvoudigd")
        self.assertIn('"eerste_fout": "6/8"', rij["extra"])
        self.assertTrue(self.ergens(scherm, "kan nog eenvoudiger"))

    def test_vergelijken(self):
        o = self.opslag(("Test", "5"))
        v = Vraag(B.VERGELIJKEN.id, f"{B.VERGELIJKEN.id}:ongelijknamig:2/3?3/5", "2/3  ?  3/5", ">",
                  invoer="vergelijk", data={"soort": "ongelijknamig", "a": 2, "b": 3, "c": 3, "d": 5,
                                            "onderwerp": "ongelijknamig"},
                  model_na=B.balken_gelijknamig([F(2, 3), F(3, 5)]))
        with mock.patch.object(B.VERGELIJKEN, "maak", side_effect=[v, v]):
            scherm, app = self.speel([*naar(3), "<", OK, *STOP], opslag=o)
        self.assertFalse(o.antwoorden(app.kind.id)[0]["juist"])
        self.assertTrue(self.ergens(scherm, "10/15 en 3/5 = 9/15"))

    def test_spiekbrief(self):
        scherm, _ = self.speel([*naar_spiekbrief("Breuken en procenten", 1), ESC, ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "DE BREUKBALK"))


if __name__ == "__main__":
    unittest.main()
