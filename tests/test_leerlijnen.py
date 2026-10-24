import unittest

from leeravontuur.kern import leerjaren, leerlijnen


class TestLeerlijnen(unittest.TestCase):
    def test_alle_leerlijnen_geldig(self):
        namen = leerlijnen.alle()
        self.assertIn("wiskunde.eenheden.omzetten", namen)
        for naam in namen:
            with self.subTest(naam):
                data = leerlijnen.laad(naam)
                self.assertEqual(data["vaardigheid"], naam)
                for jaar in leerjaren.LEERJAREN:
                    leerlijnen.parameters(naam, jaar)  # mag geen fout geven

    def test_valideer_vindt_fouten(self):
        goed = {"vaardigheid": "x", "omschrijving": "", "doelen": [], "parameters": {"a": "int"},
                "leerlijn": {"5": {"a": 1}}}
        self.assertEqual(leerlijnen.valideer(goed), [])
        fout = dict(goed, leerlijn={"5": {"a": "1"}, "7": {"a": 1}, "6": {"b": 2}})
        fouten = leerlijnen.valideer(fout)
        self.assertTrue(any("type int" in f for f in fouten))
        self.assertTrue(any("onbekend leerjaar" in f for f in fouten))
        self.assertTrue(any("onbekende parameter" in f for f in fouten))
        self.assertTrue(any("ontbreekt" in f for f in fouten))

    def test_overerving(self):
        # m2 staat niet in de leerlijn van eenheden: dan geldt die van m1
        naam = "wiskunde.eenheden.omzetten"
        self.assertEqual(leerlijnen.parameters(naam, "m2"), leerlijnen.parameters(naam, "m1"))


class TestLeerjaren(unittest.TestCase):
    def test_niveaus_schuiven_mee(self):
        f = leerjaren.leerjaar_voor_niveau
        self.assertEqual([f("5", i) for i in range(4)], ["4", "5", "6", "m1"])
        self.assertEqual([f("6", i) for i in range(4)], ["5", "6", "m1", "m2"])
        self.assertEqual([f("3", i) for i in range(4)], ["3", "3", "4", "5"])
        self.assertEqual(f("m2", 3), "m2")

    def test_volgend(self):
        self.assertEqual(leerjaren.volgend("5"), "6")
        self.assertEqual(leerjaren.volgend("m2"), "m2")


if __name__ == "__main__":
    unittest.main()
