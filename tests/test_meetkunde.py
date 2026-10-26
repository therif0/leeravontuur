import random
import unittest
from decimal import Decimal
from unittest import mock

from leeravontuur.kern import leerjaren
from leeravontuur.kern.modellen import Figuur, Kaart
from leeravontuur.kern.onderwerp import Vraag
from leeravontuur.kern.wiskunde import meetkunde as MK
from leeravontuur.terminal import modellen as TM

try:
    from .test_schermen import ESC, OK, Basis, hm
except ImportError:
    from test_schermen import ESC, OK, Basis, hm

D = Decimal


class TestModellen(unittest.TestCase):
    def test_figuur(self):
        l_vorm = Figuur(5, 8, {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)})
        self.assertEqual(l_vorm.oppervlakte(), 5)
        self.assertEqual(l_vorm.omtrek(), 12)
        self.assertEqual(l_vorm.binnenranden(), 4)
        driehoek = Figuur(5, 8, {(1, 0), (2, 0), (2, 1)}, {(0, 0), (1, 1), (2, 2)})
        self.assertEqual(driehoek.oppervlakte(), D("4.5"))

    def test_kaart(self):
        k = Kaart(8, 8)
        self.assertEqual(k.naam(3, 4), "C4")
        self.assertEqual(MK.lees_coord(k, "c 4"), (3, 4))
        self.assertEqual(MK.lees_coord(k, "(C, 4)"), (3, 4))
        self.assertIsNone(MK.lees_coord(k, "K4"))
        a = Kaart(assen=5)
        self.assertEqual(a.naam(3, -2), "(3, −2)")
        self.assertEqual(MK.lees_coord(a, "(3, -2)"), (3, -2))
        self.assertEqual(MK.lees_coord(a, "3 −2"), (3, -2))
        self.assertIsNone(MK.lees_coord(a, "(7, 1)"))

    def test_rooster_vakjes_zijn_vierkant(self):
        fig = Figuur(2, 3, {(0, 0)}, {(1, 1)})
        p = TM.figuur_pixels(fig)
        self.assertEqual((len(p), len(p[0])), (4 * 2 + 1, 4 * 3 + 1))
        # een heel vakje: 3 × 3 pixels vulling, omringd door lijnen
        self.assertTrue(all(p[1 + i][1 + j] == "vulling" for i in range(3) for j in range(3)))
        self.assertTrue(all(p[0][x] == "lijn" and p[4][x] == "lijn" for x in range(5)))
        self.assertTrue(all(p[y][0] == "lijn" and p[y][4] == "lijn" for y in range(5)))
        # een half vakje: de driehoek linksonder, 6 van de 9 pixels
        half = [[p[5 + i][5 + j] == "vulling" for j in range(3)] for i in range(3)]
        self.assertEqual(half, [[True, False, False], [True, True, False], [True, True, True]])
        # een leeg vakje blijft leeg
        self.assertTrue(all(p[1 + i][9 + j] is None for i in range(3) for j in range(3)))

    def test_rand_ligt_op_de_omtrek(self):
        fig = Figuur(5, 8, {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}, rand=True)
        p = TM.figuur_pixels(fig)
        # elk randje van 1 cm = de 3 pixels tussen twee hoekpunten
        randjes = sum(all(p[y][x + d] == "rand" for d in (1, 2, 3)) for y in range(0, len(p), 4)
                      for x in range(0, len(p[0]) - 1, 4))
        randjes += sum(all(p[y + d][x] == "rand" for d in (1, 2, 3)) for y in range(0, len(p) - 1, 4)
                       for x in range(0, len(p[0]), 4))
        self.assertEqual(randjes, fig.omtrek())

    def test_hoek_tekening_past(self):
        class S:
            def __init__(self):
                self.punten = []

            def put(self, y, x, tekst, rol=""):
                self.punten += [(y, x + i) for i in range(len(tekst))]
        for graden in range(0, 181, 5):
            s = S()
            h, b = TM.teken_hoek(s, 9, graden, 8)
            self.assertTrue(all(9 <= y < 9 + h and 0 <= x < 8 + b for y, x in s.punten), graden)


class TestGeneratoren(unittest.TestCase):
    def test_alle_leerjaren(self):
        rng = random.Random(22)
        for o in MK.ALLE:
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
                    if isinstance(v.model, Figuur):
                        self.assertTrue(all(0 <= r < v.model.rijen and 0 <= k < v.model.kolommen
                                            for r, k in v.model.vakjes | v.model.halve))
                        self.assertEqual(v.model.oppervlakte() if v.data["soort"] == "oppervlakte"
                                         else v.model.omtrek(), v.antwoord)

    def test_niveaus(self):
        self.assertTrue(MK.ROOSTER.aangeboden("3"))
        self.assertFalse(MK.SCHAAL.aangeboden("5"))
        self.assertTrue(MK.SCHAAL.aangeboden("6"))
        for _ in range(100):
            self.assertNotIn(MK.FORMULES.maak("5").data["soort"], ("cirkel_opp", "balk_volume"))

    def test_spiekbrief_past(self):
        for t, _ in MK.SPIEKBRIEF:
            self.assertLessEqual(len(t), 78, t)


class TestDiagnose(unittest.TestCase):
    def test_rooster(self):
        fig = Figuur(5, 8, {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)})
        v = Vraag(MK.ROOSTER.id, "k", "", D(12), model=fig,
                  data={"soort": "omtrek", "vol": 5, "half": 0, "omtrek": 12, "binnen": 4})
        self.assertEqual(MK.ROOSTER.diagnose(v, D(5))[0], "omtrek_oppervlakte")
        self.assertEqual(MK.ROOSTER.diagnose(v, D(16))[0], "binnenranden")
        w = Vraag(MK.ROOSTER.id, "k", "", D("4.5"), data={"soort": "oppervlakte", "vol": 3, "half": 3})
        self.assertEqual(MK.ROOSTER.diagnose(w, D(6))[0], "halve_als_hele")
        self.assertEqual(MK.ROOSTER.diagnose(w, D(3))[0], "halve_vergeten")

    def test_formules(self):
        v = Vraag(MK.FORMULES.id, "k", "", D(12), data={"soort": "driehoek_opp", "b": "6", "h": "4"})
        self.assertEqual(MK.FORMULES.diagnose(v, D(24))[0], "deel_door_2_vergeten")
        self.assertIn("6 × 4 : 2 = 12", MK.FORMULES.uitleg(v)[0])
        r = Vraag(MK.FORMULES.id, "k", "", D(28), data={"soort": "rechthoek_opp", "l": "7", "b": "4"})
        self.assertEqual(MK.FORMULES.diagnose(r, D(22))[0], "omtrek_ipv_opp")
        o = Vraag(MK.FORMULES.id, "k", "", D(22), data={"soort": "rechthoek_omtrek", "l": "7", "b": "4"})
        self.assertEqual(MK.FORMULES.diagnose(o, D(28))[0], "opp_ipv_omtrek")
        self.assertEqual(MK.FORMULES.diagnose(o, D(11))[0], "maar_2_zijden")
        c = Vraag(MK.FORMULES.id, "k", "", D("12.56"), data={"soort": "cirkel_omtrek", "r": "2", "diameter": True})
        self.assertEqual(MK.FORMULES.diagnose(c, D("25.12"))[0], "straal_diameter")
        self.assertIn("4 : 2 = 2", MK.FORMULES.uitleg(c)[0])

    def test_hoeken(self):
        v = Vraag(MK.HOEKEN.id, "k", "", "stomp", invoer="woord", data={"soort": "graden", "graden": 120})
        self.assertEqual(MK.HOEKEN.lees_vraag(v, "Scherpe hoek"), "scherp")
        self.assertEqual(MK.HOEKEN.lees_vraag(v, "volle"), "vol")
        self.assertIsNone(MK.HOEKEN.lees_vraag(v, "spits"))
        self.assertEqual(MK.HOEKEN.diagnose(v, "scherp")[0], "stomp_scherp")
        self.assertIn("stompe hoek", " ".join(MK.HOEKEN.uitleg(v)))
        d = Vraag(MK.HOEKEN.id, "k", "", D(60), data={"soort": "driehoek", "a": 50, "b": 70})
        self.assertEqual(MK.HOEKEN.diagnose(d, D(240))[0], "hoekensom")

    def test_coordinaten_en_schaal(self):
        v = Vraag(MK.COORDINATEN.id, "k", "", "B3", model=Kaart(8, 8), data={"soort": "aflezen", "x": 2, "y": 3})
        self.assertEqual(MK.COORDINATEN.diagnose(v, "C2")[0], "coord_omgewisseld")
        self.assertEqual(MK.COORDINATEN.diagnose(v, "B6")[0], "rij_van_boven")
        a = Vraag(MK.COORDINATEN.id, "k", "", "(3, −2)", model=Kaart(assen=5),
                  data={"soort": "assen_aflezen", "x": 3, "y": -2})
        self.assertEqual(MK.COORDINATEN.diagnose(a, "(−2, 3)")[0], "coord_omgewisseld")
        s = Vraag(MK.SCHAAL.id, "k", "", D(30), data={"soort": "naar_echt", "schaal": 1000, "cm": 3, "eenheid": "m",
                                                     "per": 100})
        self.assertEqual(MK.SCHAAL.diagnose(s, D(3000))[0], "schaal_niet_omgezet")
        self.assertIn("3 × 1000 = 3000 cm = 30 m", MK.SCHAAL.uitleg(s)[1])
        z = Vraag(MK.SCHAAL.id, "k", "", D(5000), data={"soort": "schaal_zoeken", "schaal": 5000, "cm": 4,
                                                       "eenheid": "m", "per": 100})
        self.assertEqual(MK.SCHAAL.lees("1 : 5000"), 5000)
        self.assertEqual(MK.SCHAAL.diagnose(z, D(50))[0], "schaal_niet_omgezet")


def kruis_vraag():
    return Vraag(MK.COORDINATEN.id, f"{MK.COORDINATEN.id}:aanduiden:B3", "Zet een kruisje op B3.", "B3",
                 invoer="coord", model=Kaart(8, 8), data={"soort": "aanduiden", "onderwerp": "aanduiden", "x": 2, "y": 3})


def naar(onderwerp):
    """Wiskunde → Meetkunde → onderwerp → Vrij oefenen → Normaal."""
    return [OK, OK, hm("Leren & oefenen"), "1", "8", str(onderwerp), "1", OK]


STOP = [ESC] * 7


class TestSchermen(Basis):
    def test_kruisje_met_een_klik(self):
        o = self.opslag(("Test", "5"))
        y, x = TM.kaart_plaats(Kaart(8, 8), 3, 2, 9)  # C2: kolom en rij omgewisseld
        with mock.patch.object(MK.COORDINATEN, "maak", side_effect=[kruis_vraag(), kruis_vraag()]):
            scherm, app = self.speel([*naar(4), ("klik", y, x), ("klik", y, x), *STOP], opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertEqual(rij["gegeven"], "C2")
        self.assertFalse(rij["juist"])
        self.assertEqual(rij["diagnose"], "coord_omgewisseld")

    def test_kruisje_met_pijltjes(self):
        import curses
        o = self.opslag(("Test", "5"))
        # de cursor begint in het midden (E5); naar B3 = 3 × links, 2 × omlaag
        toetsen = [curses.KEY_LEFT] * 3 + [curses.KEY_DOWN] * 2
        with mock.patch.object(MK.COORDINATEN, "maak", side_effect=[kruis_vraag(), kruis_vraag()]):
            scherm, app = self.speel([*naar(4), *toetsen, OK, *STOP], opslag=o)
        self.assertTrue(o.antwoorden(app.kind.id)[0]["juist"])

    def test_figuur_op_het_scherm(self):
        o = self.opslag(("Test", "5"))
        fig = Figuur(5, 8, {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)})
        v = Vraag(MK.ROOSTER.id, f"{MK.ROOSTER.id}:omtrek:L:x", "Hoe groot is de omtrek van de figuur?", D(12),
                  eenheid="cm", model=fig, model_na=Figuur(5, 8, fig.vakjes, rand=True),
                  data={"soort": "omtrek", "vorm": "L", "onderwerp": "omtrek", "vol": 5, "half": 0, "omtrek": 12,
                        "binnen": 4})
        with mock.patch.object(MK.ROOSTER, "maak", side_effect=[v, v]):
            scherm, app = self.speel([*naar(1), *"5", OK, *"5", OK, *STOP], opslag=o)
        self.assertEqual(o.antwoorden(app.kind.id)[0]["diagnose"], "omtrek_oppervlakte")
        self.assertTrue(self.ergens(scherm, "███ = 1 cm²"))
        self.assertTrue(self.ergens(scherm, "━━━"))  # na het nakijken: de omtrek aangeduid

    def test_spiekbrief(self):
        scherm, _ = self.speel([OK, OK, hm("Spiekbrieven"), "8", ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "FORMULES"))


if __name__ == "__main__":
    unittest.main()
