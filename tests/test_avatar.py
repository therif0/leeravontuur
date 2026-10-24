import itertools
import re
import unittest
from decimal import Decimal
from unittest import mock

from leeravontuur.kern import avatar as A
from leeravontuur.kern import punten as P
from leeravontuur.kern.opslag import Opslag
from leeravontuur.kern.sessie import Sessie
from leeravontuur.kern.wiskunde import eenheden as E

try:
    from .test_schermen import ESC, OK, Basis, hm
except ImportError:
    from test_schermen import ESC, OK, Basis, hm

KLEUR = re.compile(r"#[0-9a-f]{6}")


class TestAvatar(unittest.TestCase):
    def test_alle_combinaties(self):
        d = A.onderdelen()
        lagen = [list(d["vormen"]), list(d["ogen"]), list(d["oren"]), [None, *d["haar"]], [None, *d["hoed"]],
                 [None, *d["accessoire"]]]
        for vorm, ogen, oren, haar, hoed, acc in itertools.product(*lagen):
            config = {"vorm": vorm, "ogen": ogen, "oren": oren, "haar": haar, "hoed": hoed, "accessoire": acc}
            raster = A.teken(config)
            self.assertEqual(len(raster), 16)
            for rij in raster:
                self.assertEqual(len(rij), 16)
                for k in rij:
                    self.assertTrue(k is None or KLEUR.fullmatch(k), k)

    def test_gezicht_op_het_lijf(self):
        """Ogen, neus en mond moeten bij elke vorm op het lijf staan (de ankers kloppen)."""
        d = A.onderdelen()
        for vorm, v in d["vormen"].items():
            lijf = {(y, x) for y, rij in enumerate(v["pixels"]) for x, ch in enumerate(rij) if ch != "."}
            a = v["ankers"]
            stukken = [(d["ogen"]["gewoon"]["pixels"], a["ogen"][0], a["ogen"][1]),
                       (d["ogen"]["gewoon"]["pixels"], a["ogen"][0], a["ogen"][2]),
                       (d["neus"], *a["neus"])]
            stukken += [(u["mond"], *a["mond"]) for u in d["uitdrukkingen"].values()]
            for patroon, y, x in stukken:
                for dy, rij in enumerate(patroon):
                    for dx, ch in enumerate(rij):
                        if ch != ".":
                            self.assertIn((y + dy, x + dx), lijf, f"{vorm}: pixel naast het lijf")

    def test_uitdrukkingen_verschillen(self):
        beelden = {u: A.teken({}, u) for u in A.onderdelen()["uitdrukkingen"]}
        self.assertNotEqual(beelden["blij"], beelden["oeps"])
        self.assertNotEqual(beelden["normaal"], beelden["trots"])
        for u in beelden:
            self.assertIn(u, A.TEKSTGEZICHT)

    def test_geldig(self):
        c = A.geldig({"vorm": "bestaat-niet", "kleur": "rood", "hoed": "kroon"})
        self.assertEqual((c["vorm"], c["kleur"], c["hoed"]), ("vierkant", "rood", "kroon"))
        self.assertEqual(A.geldig(None), A.STANDAARD)

    def test_reactie(self):
        self.assertEqual(A.reactie(True, 5)[0], "trots")
        self.assertEqual(A.reactie(True, 2)[0], "blij")
        self.assertIn("kolommen", A.reactie(False, diagnose="factor_10")[1])
        self.assertEqual(A.reactie(False)[0], "aanmoedigend")


class TestPunten(unittest.TestCase):
    def test_regels(self):
        self.assertEqual(P.voor_antwoord(True, "5", "5", "reeks", False)[0], 10)
        self.assertEqual(P.voor_antwoord(True, "5", "4", "reeks", False)[0], 5)
        self.assertEqual(P.voor_antwoord(True, "5", "m1", "reeks", False)[0], 20)
        self.assertEqual(P.voor_antwoord(True, "5", "6", "fouten_opnieuw", False)[0], 7)
        self.assertEqual(P.voor_antwoord(True, "5", "5", "reeks", True)[0], 0)  # al eens juist
        self.assertEqual(P.voor_antwoord(False, "5", "5", "reeks", False)[0], 0)
        self.assertEqual(P.voor_antwoord(True, "5", "5", "tabel", False, {"cijfers_ok": True, "komma_ok": True})[0],
                         15)

    def test_sessie_en_op_rij(self):
        o = Opslag()
        kind = o.nieuw_kind("Test", "5")
        with Sessie(o, kind.id, "reeks", "x", "5", eigen_leerjaar="5") as ses:
            for i in range(5):
                ses.antwoord(f"k{i}", "v", "g", True)
            self.assertEqual(ses.laatste_punten, 20)  # 10 + bonus 5 op rij
            ses.antwoord("k0", "v", "g", True)       # al eens juist: niets
            self.assertEqual(ses.laatste_punten, 0)
        self.assertEqual(o.punten_saldo(kind.id), 60)
        self.assertIn("5 juist op rij", [p["reden"] for p in o.punten_log(kind.id)])


class TestSchermen(Basis):
    def test_perfecte_reeks_met_punten(self):
        o = self.opslag(("Test", "5"))
        vragen = [E.Omzetting(E.LENGTE, "m", "cm", Decimal(i)) for i in range(1, 11)]
        antwoorden = []
        for i in range(1, 11):
            antwoorden += [*str(i * 100), OK, OK]
        with mock.patch.object(E, "maak_vraag", side_effect=vragen):
            scherm, app = self.speel([OK, OK, hm("Leren & oefenen"), "1", "1", "2", "2", OK, *antwoorden,
                                      ESC, ESC, ESC, ESC, ESC], opslag=o)
        # 10 x 10 + 2 x 10 (5 en 10 op rij) + 20 (geen fout)
        self.assertEqual(o.punten_saldo(app.kind.id), 140)
        self.assertTrue(self.ergens(scherm, "Je verdiende 140 punten"))
        self.assertTrue(self.ergens(scherm, "+10 punten"))
        self.assertTrue(self.ergens(scherm, "[^o^]"))  # trots na 5 op rij (tekstgezicht zonder kleuren)

    def test_mijn_avatar(self):
        scherm, _ = self.speel([OK, OK, hm("Mijn avatar"), curses_rechts(), ESC, ESC])
        self.assertTrue(self.ergens(scherm, "[W] naar de winkel"))
        self.assertTrue(self.ergens(scherm, "punten"))
        self.assertTrue(self.ergens(scherm, "Gezichtje: blij"))
        self.assertTrue(self.ergens(scherm, "Gezichtje: trots"))

    def test_avatar_uit(self):
        o = self.opslag(("Test", "5", {"avatar": False}))
        scherm, _ = self.speel([OK, OK, ESC], opslag=o)
        self.assertFalse(self.ergens(scherm, "★"))


def curses_rechts():
    import curses
    return curses.KEY_RIGHT


if __name__ == "__main__":
    unittest.main()
