import unittest
from decimal import Decimal

from leeravontuur.kern import leerjaren
from leeravontuur.kern.getal import fmt, lees_getal
from leeravontuur.kern.wiskunde import eenheden as E


def omz(getal, van, naar):
    return E.Omzetting(E.CATEGORIE[van], van, naar, Decimal(getal))


class TestRekenen(unittest.TestCase):
    def test_omzettingen(self):
        gevallen = [("3.5", "km", "m", "3500"), ("250", "mg", "g", "0,25"), ("2", "t", "kg", "2000"),
                    ("4.25", "m", "cm", "425"), ("5", "mm", "m", "0,005"), ("1", "t", "mg", "1000000000"),
                    ("3500", "g", "kg", "3,5")]
        for getal, van, naar, juist in gevallen:
            with self.subTest(f"{getal} {van} -> {naar}"):
                self.assertEqual(fmt(omz(getal, van, naar).antwoord), juist)

    def test_lees_getal(self):
        self.assertEqual(lees_getal("3,5"), Decimal("3.5"))
        self.assertEqual(lees_getal("0.25"), Decimal("0.25"))
        self.assertEqual(lees_getal("3.500"), 3500)
        self.assertEqual(lees_getal("1 000"), 1000)
        self.assertEqual(lees_getal("0,25 g"), Decimal("0.25"))
        for fout in ("abc", "", "3,,5"):
            self.assertIsNone(lees_getal(fout))


class TestTabel(unittest.TestCase):
    def test_verwachte_cijfers(self):
        self.assertEqual(E.verwachte_cijfers(omz("4.25", "m", "cm")), {0: 4, -1: 2, -2: 5})
        self.assertEqual(E.verwachte_cijfers(omz("5", "mm", "m")), {0: 0, -1: 0, -2: 0, -3: 5})
        self.assertEqual(E.verwachte_cijfers(omz("3500", "m", "km")), {3: 3, 2: 5, 1: 0, 0: 0})

    def test_controleer_tabel(self):
        v = omz("4.25", "m", "cm")
        self.assertTrue(all(o is not False for o in E.controleer_tabel(v, [None, None, None, 4, 2, 5, None])))
        self.assertIs(E.controleer_tabel(v, [None, None, 0, 4, 2, 5, 0])[2], True)  # extra nul mag
        self.assertIs(E.controleer_tabel(v, [None, None, None, 4, 2, 6, None])[5], False)

    def test_aflezen(self):
        self.assertEqual(E.aflezen([4, 0, 0, 0, None, None, None, None, None, None], 0), "4,000")
        self.assertEqual(E.aflezen([None, None, None, 4, 2, 5, None], 5), "425")
        self.assertEqual(E.aflezen([None, None, None, None, None, None, 5], 3), "0,005")
        self.assertEqual(E.aflezen([None, None, None, 4, None, 5, None], 3), "4,05")
        self.assertIsNone(E.aflezen([None] * 7, 3))


class TestDiagnose(unittest.TestCase):
    def test_denkfouten(self):
        v = omz("3.5", "km", "m")  # juist: 3500
        self.assertIsNone(E.diagnose(v, Decimal(3500)))
        self.assertEqual(E.diagnose(v, Decimal("3.5"))[0], "niet_omgezet")
        self.assertEqual(E.diagnose(v, Decimal("0.0035"))[0], "verkeerde_richting")
        self.assertEqual(E.diagnose(v, Decimal(350))[0], "factor_10")
        self.assertIn("te weinig", E.diagnose(v, Decimal(350))[1])
        self.assertIn("te ver", E.diagnose(v, Decimal(35000))[1])
        self.assertIsNone(E.diagnose(v, Decimal(1234)))


class TestVragenMaken(unittest.TestCase):
    def test_per_leerjaar(self):
        alles = E.EENHEDEN[E.MASSA] + E.EENHEDEN[E.LENGTE]
        for jaar in leerjaren.LEERJAREN:
            for tabel in (False, True):
                for gekozen in (E.EENHEDEN[E.MASSA], E.EENHEDEN[E.LENGTE], alles, ["t", "mg"]):
                    for _ in range(150):
                        v = E.maak_vraag(gekozen, jaar, tabel)
                        self.assertEqual(v.antwoord, v.getal * Decimal(10) ** v.stap)
                        self.assertIn(v.van, gekozen)
                        self.assertIn(v.naar, gekozen)
                        self.assertNotEqual(v.van, v.naar)
                        if tabel:
                            self.assertTrue(E.past_in_tabel(v))
                        E.regel_uitleg(v)
                        E.tabel_uitleg(v)

    def test_grenzen_4de_leerjaar(self):
        for _ in range(300):
            v = E.maak_vraag(E.EENHEDEN[E.LENGTE], "4")
            self.assertLessEqual(abs(v.stap), 3)
            self.assertEqual(v.getal, v.getal.to_integral_value())
            self.assertEqual(v.antwoord, v.antwoord.to_integral_value())

    def test_niet_twee_keer_na_elkaar(self):
        vorige = None
        for _ in range(200):
            v = E.maak_vraag(["m", "cm"], "3", vorige=vorige)
            if vorige:
                self.assertNotEqual(v.sleutel, vorige.sleutel)
            vorige = v

    def test_spiekbrief(self):
        regels = E.spiekbrief()
        self.assertTrue(any("VOORBEELD" in t for t, _ in regels))


if __name__ == "__main__":
    unittest.main()
