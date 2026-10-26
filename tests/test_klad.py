"""Het kladblad: rekenregels lezen zoals een kind ze typt, en nakijken zonder het antwoord te verklappen."""

import unittest
from fractions import Fraction

from leeravontuur.kern.klad import DEEL, MAAL, MIN, VAN, lees_regel


class TestLezen(unittest.TestCase):
    def juist(self, tekst):
        r = lees_regel(tekst)
        self.assertTrue(r.juist, f"{tekst!r}: {r.melding}")
        return r

    def fout(self, tekst):
        r = lees_regel(tekst)
        self.assertIs(r.juist, False, tekst)
        return r

    def test_maal_en_delen_zonder_speciale_tekens(self):
        for tekst in ["3x4=12", "3 X 4 = 12", "3*4=12", "3 × 4 = 12"]:
            r = self.juist(tekst)
            self.assertEqual(r.netjes, "3 × 4 = 12")
            self.assertEqual(r.schakels[0].ops, [MAAL])
        for tekst in ["12:4=3", "12 / 4 = 3", "12 ÷ 4 = 3"]:
            self.assertEqual(self.juist(tekst).netjes, "12 : 4 = 3")
        # zonder spaties is a/b een breuk (één getal): dat klopt ook, en 3/4 : 2/5 wordt (3/4) : (2/5)
        self.assertEqual(self.juist("12/4=3").netjes, "12/4 = 3")
        self.assertEqual(self.juist("3/4 : 2/5 = 15/8").uitkomst, Fraction(15, 8))
        self.assertEqual(self.juist("10 - 2,40 = 7,60").netjes, "10 − 2,40 = 7,60")

    def test_kommagetallen_en_punt(self):
        self.juist("0,75 x 3,20 = 2,40")
        self.assertEqual(self.juist("0.75 x 3.2 = 2.4").netjes, "0,75 × 3,2 = 2,4")
        self.juist("1.000 : 4 = 250")

    def test_haakjes_en_volgorde(self):
        self.juist("(3 + 5) x 2 = 16")
        self.juist("3 + 5 x 2 = 13")
        self.fout("3 + 5 x 2 = 16")

    def test_omzetten(self):
        r = self.juist("750 g = 0,75 kg")
        self.assertEqual(r.schakels[0].soort, "omzet")
        self.juist("2 m2 = 200 dm2")
        self.juist("1 l = 1 dm3")
        self.juist("2 u 15 min = 135 min")
        self.juist("2u15 = 135 min")
        self.juist("€ 3,50 = 350 cent")
        self.juist("3 m 40 cm = 340 cm")
        self.assertIn("komma", self.fout("750 g = 7,5 kg").melding)

    def test_duizendtallen_met_een_spatie(self):
        self.assertEqual(self.juist("12 x 25 000 = 300 000").netjes, "12 × 25 000 = 300 000")
        self.juist("300 000 cm = 3 km")
        self.juist("2 u 15 min = 135 min")  # (geen duizendtal)

    def test_kloktijden(self):
        self.juist("8.45 u + 15 min = 9.00 u")
        self.juist("9.45 u + 1 u 35 min = 11.20 u")
        self.juist("16.05 u - 14.30 u = 1 u 35 min")
        self.juist("16.05 u - 14.30 u = 95 min")
        self.juist("23.40 u + 35 min = 0.15 u")  # over middernacht
        self.juist("9:45 + 30 = 10:15")
        self.assertIn("60 minuten", self.fout("9.50 u + 20 min = 9.70 u").melding)
        self.assertIn("60 minuten", self.fout("9.50 + 20 = 9.70").melding)
        self.juist("8,45 u = 8 u 27 min")  # met een komma is het een kommagetal, geen kloktijd

    def test_procent_en_breuk_van(self):
        r = self.juist("25 % van 80 = 20")
        self.assertEqual((r.schakels[0].ops, r.schakels[0].operanden), ([VAN], [25, 80]))
        self.assertEqual(self.juist("3/4 van 24 = 18").netjes, "3/4 van 24 = 18")

    def test_rest(self):
        self.juist("25 : 4 = 6 rest 1")
        self.juist("25:4=6 r 1")
        self.fout("25 : 4 = 5 rest 5")

    def test_afronden(self):
        self.assertTrue(self.juist("10 : 3 = 3,33").schakels[0].afgerond)
        self.juist("10 : 3 = 3,3")
        self.fout("10 : 3 = 3,4")
        self.fout("10 : 4 = 2,6")  # 2,5 is exact: dan geen afronding

    def test_label_en_woorden(self):
        r = self.juist("kersen: 0,75 x 3,20 = 2,40")
        self.assertEqual(r.label, "kersen")
        self.assertEqual(self.juist("prijs = 0,75 x 3,20 = 2,40").label, "prijs")
        self.juist("3 zakjes x 4 snoepjes = 12 snoepjes")
        self.juist("€ 10 − € 2,40 = € 7,60")

    def test_ketting(self):
        r = self.juist("3 x 4 = 12 + 3 = 15")
        self.assertTrue(r.schakels[0].ketting)
        self.assertIn("nieuwe regel", r.melding)
        self.assertEqual(r.uitkomst, 15)

    def test_meldingen_verklappen_niets(self):
        r = self.fout("0,75 x 3,20 = 24")
        self.assertIn("komma", r.melding)
        self.assertNotIn("2,4", r.melding)
        self.assertIn("je rekende +", self.fout("5 x 3 = 8").melding)
        self.assertIn("nog eens na", self.fout("17 x 3 = 50").melding)
        self.assertIn("door 0", self.fout("12 : 0 = 3").melding)

    def test_onvolledig_of_onleesbaar(self):
        r = lees_regel("750 x 3,20")
        self.assertIsNone(r.juist)
        self.assertIn("uitkomst", r.melding)
        self.assertIn("uitkomst", lees_regel("750 x 3,20 =").melding)
        for tekst in ["", "abc ?", "= 5", "3 + = 4", "(3 + 4 = 7"]:
            r = lees_regel(tekst)
            self.assertIsNone(r.juist, tekst)
        self.assertIsNone(lees_regel("12").juist)

    def test_uitkomst_en_operanden(self):
        r = lees_regel("10 - 2,40 = 7,60")
        s = r.schakels[0]
        self.assertEqual((s.ops, s.operanden, r.uitkomst), ([MIN], [10, Fraction("2.4")], Fraction("7.6")))
        self.assertEqual(lees_regel("12 : 4 = 3").schakels[0].ops, [DEEL])


if __name__ == "__main__":
    unittest.main()
