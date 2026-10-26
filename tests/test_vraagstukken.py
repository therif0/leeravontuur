"""Vraagstukken: de verhaalmachine, de foute paden, het klad en het scherm met de 4 stappen."""

import curses
import random
import re
import unittest
from decimal import Decimal
from fractions import Fraction

from leeravontuur.kern import punten as P
from leeravontuur.kern import verhaal as V
from leeravontuur.kern.wiskunde import vraagstukken as VS
from leeravontuur.terminal.vraagstuk import VraagstukInvoer

O = VS.VRAAGSTUKKEN
JAREN = ["3", "4", "5", "6", "m1"]


def maak(jaar, structuur, variant, zaad=1):
    return O.maak_met(O.parameters(jaar), random.Random(zaad), {"structuur": structuur, "variant": variant})


def r(x):
    return str(x).replace(".", ",")


class TestVerhaalmachine(unittest.TestCase):
    def test_elke_structuur_in_elk_leerjaar(self):
        for jaar in JAREN:
            p = O.parameters(jaar)
            for keuze in p["structuren"]:
                s, var = keuze.split("/")
                for zaad in range(40):
                    v = maak(jaar, s, var, zaad)
                    m = v.model
                    with self.subTest(jaar=jaar, keuze=keuze, zaad=zaad):
                        self.assertEqual(v.data["structuur"], s)
                        self.assertNotRegex(v.tekst, r"[{}@*]", "een sjabloon is niet ingevuld")
                        self.assertNotRegex(v.tekst, r"\b(m m|min min|km km|g g)\b")
                        self.assertLessEqual(len(V.regels(m.zinnen, VS.BREEDTE)), VS.REGELS)
                        self.assertGreater(v.antwoord, 0)
                        self.assertTrue(v.tekst.endswith("?"))
                        lo, hi, _ = m.controle
                        self.assertTrue((lo is None or v.antwoord >= lo) and (hi is None or v.antwoord <= hi))
                        self.assertIn(m.gevraagd, m.opties)
                        self.assertEqual(len(set(m.opties)), len(m.opties))
                        # elk gegeven staat in het verhaal, de uitkomst is mooi (hoogstens 2 cijfers na de komma)
                        ids = {st.gegeven for z in m.zinnen for st in z if st.gegeven}
                        self.assertEqual(ids, set(m.gegevens))
                        self.assertIsNotNone(VS.mooi(v.antwoord))
                        self.assertIsNone(O.diagnose(v, v.antwoord))
                        self.assertTrue(O.nakijken(v, O.lees_vraag(v, v.verwacht)))

    def test_veel_verschillende_verhalen(self):
        p = O.parameters("5")
        rng = random.Random(3)
        sleutels = {O.maak_met(p, rng).sleutel for _ in range(500)}
        self.assertGreater(len(sleutels), 480)
        teksten = {re.sub(r"\d+([,.]\d+)?", "#", O.maak_met(p, rng).tekst) for _ in range(500)}
        self.assertGreater(len(teksten), 250, "ook zonder de getallen moeten de verhalen verschillen")

    def test_herhaling_houdt_de_structuur_en_wisselt_de_wereld(self):
        v = maak("5", "groepen", "totaal", 4)
        werelden = set()
        for i in range(30):
            w = O.maak_herhaling(O.herhaal_data(v), "5")
            self.assertEqual((w.data["structuur"], w.data["variant"]), ("groepen", "totaal"))
            werelden.add(w.sleutel.split(":")[2])
        self.assertGreater(len(werelden), 4)
        self.assertEqual(O.onderwerp_van_sleutel(v.sleutel), "groepen")
        self.assertIsNone(O.onderwerp_van_sleutel("iets:anders"))

    def test_meervoud_en_hoofdletters(self):
        ctx = {"ding": V.woord("broodje|broodjes|het"), "houder": V.woord("plaat|platen|de"), "wie": "de bakker",
               "a": VS.Gegeven("a", Decimal(1), "1", ""), "b": VS.Gegeven("b", Decimal(3), "3", ""),
               "m1": "'s morgens"}
        self.assertEqual(V.vul_tekst("{wie} bakt {a ding} en {b ding}.", ctx, True),
                         "De bakker bakt 1 broodje en 3 broodjes.")
        self.assertEqual(V.vul_tekst("{elk:ding} en {elk:houder}", ctx), "elk broodje en elke plaat")
        self.assertEqual(V.vul_tekst("{m1} bakt {wie}.", ctx, True), "'s Morgens bakt de bakker.")
        stukken = V.vul("*Elke* {houder.enk} kost {b}.", ctx)
        self.assertTrue(stukken[0].sleutel)
        self.assertEqual([s.gegeven for s in stukken if s.gegeven], ["b"])

    def test_omtrek_is_nooit_gelijk_aan_de_oppervlakte(self):
        for zaad in range(300):
            v = maak("5", "omtrek", "gewoon", zaad)
            g = v.model.gegevens
            self.assertNotEqual(v.antwoord, g["l"].waarde * g["b"].waarde)


class TestFoutePaden(unittest.TestCase):
    def test_wisselgeld(self):
        v = maak("5", "wisselgeld", "meer", 8)
        g, st = v.model.gegevens, v.model.stappen
        a, p, b = g["a"].waarde, g["p"].waarde, g["b"].waarde
        self.assertEqual(O.diagnose(v, st[0].uitkomst)[0], "vs_tussenstap")
        self.assertEqual(O.diagnose(v, b - p)[0], "vs_stap_vergeten")
        self.assertEqual(O.diagnose(v, b + a * p)[0], "vs_plus_ipv_min")
        self.assertEqual(O.diagnose(v, v.antwoord * 10)[0], "vs_komma")
        self.assertEqual(O.diagnose(v, b + 50)[0], "vs_kan_niet")

    def test_per_kg_omzetten_vergeten(self):
        v = maak("6", "per_kg", "gewoon", 5)
        g = v.model.gegevens
        d = O.diagnose(v, g["m"].waarde * g["k"].waarde)
        self.assertEqual(d[0], "vs_omzetten")
        self.assertIn("om te zetten naar kg", d[1])

    def test_minder_is_hier_optellen(self):
        v = maak("5", "verschil", "minder", 2)
        g = v.model.gegevens
        self.assertEqual(O.diagnose(v, g["a"].waarde - g["d"].waarde)[0], "vs_signaalwoord")

    def test_rest_en_naar_boven(self):
        v = maak("4", "rest", "nodig", 3)
        self.assertEqual(O.diagnose(v, v.antwoord - 1)[0], "vs_tussenstap")
        v = maak("3", "rest", "volle", 3)
        self.assertEqual(O.diagnose(v, v.antwoord + 1)[0], "vs_niet_vol")

    def test_korting_procent_als_euro(self):
        for zaad in range(20):
            v = maak("5", "korting", "gewoon", zaad)
            g = v.model.gegevens
            if g["P"].waarde - g["k"].waarde != v.antwoord:
                self.assertEqual(O.diagnose(v, g["P"].waarde - g["k"].waarde)[0], "vs_procent_euro")
                return
        self.fail("geen voorbeeld gevonden")

    def test_overbodig_gegeven(self):
        for zaad in range(200):
            v = maak("6", "groepen", "per", zaad)
            o = [x for x in v.model.gegevens.values() if not x.nodig]
            if o and o[0].eenheid == "":
                t = v.model.gegevens["t"].waarde
                if t % o[0].waarde == 0 and t / o[0].waarde != v.antwoord:
                    self.assertEqual(O.diagnose(v, t / o[0].waarde)[0], "vs_overbodig")
                    return
        self.fail("geen voorbeeld met een overbodig gegeven")

    def test_codes_hebben_een_omschrijving(self):
        for jaar in JAREN:
            for keuze in O.parameters(jaar)["structuren"]:
                v = maak(jaar, *keuze.split("/"))
                for pad in v.model.paden:
                    self.assertIn(pad[0], VS.DENKFOUTEN)


class TestKlad(unittest.TestCase):
    def setUp(self):
        self.v = maak("6", "per_kg", "wissel", 5)
        self.m = self.v.model
        g, st = self.m.gegevens, self.m.stappen
        self.gram, self.kg, self.k, self.b = g["m"].waarde, st[0].uitkomst, g["k"].waarde, g["b"].waarde
        self.st = st

    def test_juist_klad(self):
        a = VS.analyseer_klad(self.m, [f"{self.gram} g = {r(self.kg)} kg",
                                       f"{r(self.kg)} x {r(self.k)} = {r(self.st[1].uitkomst)}",
                                       f"{self.b} - {r(self.st[1].uitkomst)} = {r(self.st[2].uitkomst)}"])
        self.assertEqual(a["status"], ["goed", "goed", "goed"])
        self.assertIsNone(a["eerste"])
        self.assertTrue(a["compleet"])

    def test_denkfout_in_het_klad(self):
        a = VS.analyseer_klad(self.m, [f"{self.gram} x {r(self.k)} = {r(self.gram * self.k)}"])
        self.assertEqual((a["status"], a["eerste"][:2]), (["denk"], (1, "vs_omzetten")))
        a = VS.analyseer_klad(self.m, [f"{r(self.kg)} + {r(self.k)} = {r(self.kg + self.k)}"])
        self.assertEqual(a["eerste"][1], "vs_plus_ipv_maal")

    def test_rekenfout_in_het_klad(self):
        a = VS.analyseer_klad(self.m, [f"{self.gram} g = {r(self.kg)} kg",
                                       f"{r(self.kg)} x {r(self.k)} = {r(self.st[1].uitkomst * 10)}"])
        self.assertEqual(a["status"], ["goed", "reken"])
        self.assertEqual(a["eerste"][:2], (2, "vs_rekenfout"))
        self.assertIn("komma", a["eerste"][2])

    def test_een_andere_juiste_weg_is_geen_fout(self):
        v = maak("5", "omtrek", "gewoon", 2)
        l, b = v.model.gegevens["l"].waarde, v.model.gegevens["b"].waarde
        a = VS.analyseer_klad(v.model, [f"{l} + {b} + {l} + {b} = {2 * (l + b)}"])
        self.assertIsNone(a["eerste"])
        self.assertTrue(a["compleet"])


class TestPunten(unittest.TestCase):
    def test_punten_voor_een_vraagstuk(self):
        basis = {"vraagstuk": 1, "tips": 0, "eerste_fout": None, "klad_ok": False}
        p = lambda **kw: P.voor_antwoord(True, "5", "5", "vrij", False, {**basis, **kw})[0]
        self.assertEqual(p(), 20 + P.BONUS_ZONDER_TIP)
        self.assertEqual(p(klad_ok=True), 20 + P.BONUS_ZONDER_TIP + P.BONUS_KLAD)
        self.assertEqual(p(tips=2), 20 - 2 * P.TIP_KOST)
        self.assertEqual(p(tips=4, eerste_fout="7"), 5)
        self.assertEqual(p(eerste_fout="7"), 10 + P.BONUS_ZONDER_TIP)
        self.assertEqual(P.voor_antwoord(False, "5", "5", "vrij", False, basis)[0], 0)


class TestInvoer(unittest.TestCase):
    """Het invoer-object zonder scherm: toetsen in, toestand eruit."""

    def setUp(self):
        self.v = maak("5", "wisselgeld", "meer", 8)
        self.obj = VraagstukInvoer(self.v, O)

    def typ(self, tekst):
        uit = None
        for c in tekst:
            uit = self.obj.toets(10 if c == "\n" else ord(c))
        return uit

    def test_meteen_juist_antwoorden(self):
        self.obj.toets(ord("a"))
        uit = self.typ(r(self.v.antwoord) + "\n")
        self.assertEqual(uit[1], self.v.antwoord)
        self.assertEqual(self.obj.extra["tips"], 0)
        self.assertIsNone(self.obj.extra["eerste_fout"])

    def test_fout_geeft_een_tweede_kans_met_klad(self):
        self.obj.toets(ord("a"))
        self.assertIsNone(self.typ(r(self.v.model.stappen[0].uitkomst) + "\n"))  # de tussenuitkomst
        self.assertIn("nog niet klaar", self.obj.melding)
        self.assertIn("klad", self.obj.melding)
        self.assertEqual(self.obj.fase, 0)
        self.obj.toets(9)
        self.obj.toets(9)  # Tab, Tab: naar het klad
        st = self.v.model.stappen
        g = self.v.model.gegevens
        self.typ(f"{g['a'].waarde} x {r(g['p'].waarde)} = {r(st[0].uitkomst)}\n")
        self.typ(f"{g['b'].waarde} - {r(st[0].uitkomst)} = {r(st[1].uitkomst)}\n\n")
        uit = self.typ(r(self.v.antwoord) + "\n")
        self.assertEqual(uit[1], self.v.antwoord)
        self.assertTrue(self.obj.extra["klad_ok"])
        self.assertEqual(self.obj.extra["eerste_fout"], r(st[0].uitkomst))

    def test_tweede_keer_fout_is_definitief(self):
        self.obj.toets(ord("a"))
        self.typ("1\n")
        self.obj.toets(9)
        self.obj.toets(9)
        self.obj.toets(9)  # naar Controle
        uit = self.typ("2\n")
        self.assertEqual(uit[0], "2")

    def test_tips_en_aanduiden(self):
        for _ in range(5):
            self.obj.toets(ord("?"))
        self.assertEqual(self.obj.tips, 4)
        self.assertIn("Meer tips zijn er niet", self.obj.tiptekst)
        nodig = [k for k, g in self.v.model.gegevens.items() if g.nodig]
        for gid in nodig:
            self.obj.toets(("gegeven", gid))
        self.assertEqual(set(self.obj.aangeduid), set(nodig))
        self.obj.toets(curses.KEY_DOWN)
        juist = self.v.model.opties.index(self.v.model.gevraagd)
        for _ in range(juist):
            self.obj.toets(curses.KEY_RIGHT)
        self.obj.toets(ord(" "))
        self.assertTrue(self.obj.gevraagd_eerst)

    def test_tip_verklapt_de_uitkomst_niet(self):
        for _ in range(4):
            self.obj.toets(ord("?"))
            self.assertNotIn(r(self.v.antwoord), self.obj.tiptekst)

    def test_een_getal_typen_gaat_naar_het_klad(self):
        self.obj.toets(ord("3"))
        self.assertEqual((self.obj.fase, self.obj.buf), (2, "3"))


if __name__ == "__main__":
    unittest.main()
