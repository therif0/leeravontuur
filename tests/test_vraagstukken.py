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
from leeravontuur.terminal.vraagstuk import KeuzeInvoer, SpeurInvoer, VraagstukInvoer

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

    def test_nieuwe_structuren(self):
        v = maak("5", "tegels", "tegels", 3)
        g = v.model.gegevens
        self.assertEqual(O.diagnose(v, 2 * (g["l"].waarde + g["b"].waarde) * g["n"].waarde)[0], "vs_omtrek")
        v = maak("5", "lint", "stukken", 3)
        g = v.model.gegevens
        self.assertEqual(O.diagnose(v, g["m"].waarde / g["c"].waarde)[0], "vs_omzetten")
        v = maak("6", "schaal", "echt", 3)
        self.assertEqual(O.diagnose(v, v.model.stappen[0].uitkomst)[0], "vs_omzetten")  # de cm niet omgezet
        v = maak("5", "gemiddelde", "drie", 3)
        self.assertEqual(O.diagnose(v, v.model.stappen[0].uitkomst)[0], "vs_tussenstap")
        v = maak("6", "snelheid", "minuten", 3)
        g = v.model.gegevens
        self.assertEqual(O.diagnose(v, g["t"].waarde * g["v"].waarde)[0], "vs_omzetten")
        v = maak("5", "per_stuk", "drie", 3)
        self.assertEqual(O.diagnose(v, v.model.stappen[0].uitkomst)[0], "vs_tussenstap")

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


class TestWatOverblijft(unittest.TestCase):
    """samen/rest: een totaal min twee delen (het appelvraagstuk: 4620 appels, 2320 rood, 1680 groen, hoeveel rot?)."""

    def test_de_juiste_wegen(self):
        for zaad in range(30):
            m = maak("5", "samen", "rest", zaad).model
            t, a, b = (m.gegevens[k].waarde for k in "tab")
            r_ = t - a - b
            with self.subTest(zaad=zaad):
                self.assertEqual(m.stappen[-1].uitkomst, r_)
                for klad in ([f"{a} + {b} = {a + b}", f"{t} - {a + b} = {r_}"],
                             [f"{t} - {a} - {b} = {r_}"],
                             [f"{t} - {a} = {t - a}", f"{t - a} - {b} = {r_}"]):
                    uit = VS.analyseer_klad(m, klad)
                    self.assertIsNone(uit["eerste"], klad)
                    self.assertTrue(uit["compleet"], klad)

    def test_de_twee_delen_van_elkaar_aftrekken(self):
        for zaad in range(30):
            m = maak("5", "samen", "rest", zaad).model
            a, b = m.gegevens["a"].waarde, m.gegevens["b"].waarde
            with self.subTest(zaad=zaad):
                self.assertGreater(a, b)
                uit = VS.analyseer_klad(m, [f"{a} - {b} = {a - b}"])
                self.assertEqual(uit["eerste"][:2], (1, "vs_min_ipv_plus"))
                self.assertIn("samen", uit["eerste"][2])

    def test_een_deel_vergeten(self):
        v = maak("5", "samen", "rest", 4)
        t, a, b = (v.model.gegevens[k].waarde for k in "tab")
        self.assertEqual(O.diagnose(v, t - a)[0], "vs_stap_vergeten")
        self.assertEqual(O.diagnose(v, a + b)[0], "vs_tussenstap")

    def test_de_antwoordzin_past(self):
        from leeravontuur.terminal.vraagstuk import KOP
        for jaar in ("4", "5", "6", "m1"):
            for zaad in range(40):
                voor, na = maak(jaar, "samen", "rest", zaad).model.antwoordzin
                self.assertLessEqual(KOP + len(voor) + 12 + len(na), 80, (voor, na))  # 12 = het antwoordvak

    def test_alleen_met_een_derde_moment(self):
        derde = {i["rest"][1] for w in VS.WERELDEN["werelden"] for i in w.get("tel", []) if "rest" in i}
        self.assertGreaterEqual(len(derde), 4)
        for zaad in range(40):
            v = maak("6", "samen", "rest", zaad)
            self.assertTrue(any(v.model.gevraagd.endswith(m) for m in derde), v.model.gevraagd)


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
            self.obj.toets(curses.KEY_F1)
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
            self.obj.toets(curses.KEY_F1)
            self.assertNotIn(r(self.v.antwoord), self.obj.tiptekst)

    def test_een_getal_typen_gaat_naar_het_klad(self):
        self.obj.toets(ord("3"))
        self.assertEqual((self.obj.fase, self.obj.buf), (2, "3"))

    def test_tijdstip_als_op_een_digitaal_klokje(self):
        """#21: een tijdstip als antwoord staat er als 14:5_ (de : komt vanzelf); een letter kan er niet in."""
        v = maak("5", "tijdsduur", "eind")
        obj = VraagstukInvoer(v, O)
        obj.toets(ord("a"))  # meteen naar Controle
        for c in "145x":
            obj.toets(ord(c))
        self.assertEqual(obj.antw, "145")
        from leeravontuur.terminal.nepscherm import NepScherm
        from leeravontuur.terminal.scherm import Scherm
        from leeravontuur.kern.instellingen import Instellingen
        win = NepScherm([])
        obj.teken(Scherm(win, Instellingen()), 4)
        self.assertIn(" 1:45 ", win.tekst())  # 145 = 1.45 (zo leest het programma het ook)
        obj.toets(ord("5"))
        win = NepScherm([])
        obj.teken(Scherm(win, Instellingen()), 4)
        self.assertIn("14:55", win.tekst())
        uit = obj.toets(10)
        self.assertEqual(uit[1], v.antwoord)

    def test_tab_uit_het_klad_houdt_de_regel(self):
        """#22: een klad-regel zonder Enter en dan Tab (naar Controle): de regel staat in het klad, nagekeken."""
        self.typ("3 x 4 = 12")
        self.obj.toets(9)
        self.assertEqual((self.obj.fase, self.obj.buf), (3, ""))
        self.assertEqual(self.obj.kb.teksten, ["3 x 4 = 12"])
        self.assertIn("klopt", self.obj.melding)


class TestSpeurneus(unittest.TestCase):
    def test_elke_soort_fout(self):
        soorten = set()
        for jaar in ["4", "5", "6", "m1"]:
            for zaad in range(60):
                v = VS.SPEURNEUS.maak(jaar, rng=random.Random(zaad))
                m = v.model
                soorten.add(v.data["soort"])
                with self.subTest(jaar=jaar, zaad=zaad):
                    self.assertEqual(len(m.regels), len([r for r in m.regels if r]))
                    if m.fout:
                        self.assertTrue(1 <= m.fout <= len(m.regels))
                        self.assertEqual(len(set(m.redenen)), 3)
                        self.assertEqual(v.antwoord, f"{m.fout}{'abc'[m.reden]}")
                        # de foute regel is echt anders dan de juiste oplossing (of het antwoord is fout)
                        juist = [st.reken for st in m.verhaal.stappen]
                        self.assertTrue(m.fout > len(juist) or m.regels[m.fout - 1] != juist[m.fout - 1])
                    else:
                        self.assertEqual((v.antwoord, len(m.redenen)), ("0", 3))
                    self.assertIsNone(VS.SPEURNEUS.diagnose(v, v.antwoord))
        self.assertEqual(soorten, {"alles_juist", "rekenfout", "denkfout"})

    def test_rekenfout_klopt_echt_niet(self):
        from leeravontuur.kern.klad import lees_regel
        for zaad in range(80):
            v = VS.SPEURNEUS.maak("5", rng=random.Random(zaad))
            if v.data["soort"] == "rekenfout":
                self.assertIs(lees_regel(v.model.regels[v.model.fout - 1]).juist, False)
            elif v.data["soort"] == "alles_juist":
                for regel in v.model.regels[:-1]:
                    self.assertTrue(lees_regel(regel).juist, regel)

    def test_diagnose(self):
        v = next(v for v in (VS.SPEURNEUS.maak("5", rng=random.Random(z)) for z in range(50)) if v.model.fout)
        m = v.model
        self.assertEqual(VS.SPEURNEUS.diagnose(v, "0")[0], "vs_speur_gemist")
        andere = 1 if m.fout != 1 else 2
        self.assertEqual(VS.SPEURNEUS.diagnose(v, f"{andere}a")[0], "vs_speur_regel")
        fout_reden = "abc"[(m.reden + 1) % 3]
        self.assertEqual(VS.SPEURNEUS.diagnose(v, f"{m.fout}{fout_reden}")[0], "vs_speur_reden")

    def test_invoer(self):
        v = next(v for v in (VS.SPEURNEUS.maak("5", rng=random.Random(z)) for z in range(50)) if v.model.fout)
        obj = SpeurInvoer(v, VS.SPEURNEUS)
        self.assertIsNone(obj.toets(ord(str(v.model.fout))))
        uit = obj.toets(ord("abc"[v.model.reden]))
        self.assertEqual(uit[1], v.antwoord)


class TestSchatten(unittest.TestCase):
    def test_schatten(self):
        self.assertEqual(VS.schat(Decimal("336")), Decimal("300"))
        self.assertEqual(VS.schat(Decimal("7.40")), Decimal("7"))
        self.assertEqual(VS.schat(Decimal("0.73")), Decimal("0.7"))
        for jaar in ["3", "4", "5", "6", "m1"]:
            for zaad in range(60):
                v = VS.SCHATTEN.maak(jaar, rng=random.Random(zaad))
                m = v.model
                with self.subTest(jaar=jaar, zaad=zaad):
                    self.assertEqual(len(set(m.opties)), len(m.opties))
                    self.assertEqual(v.antwoord, "abc"[m.juist])
                    if v.data["soort"] == "kan" and m.juist == 1:  # nee: het getoonde antwoord kan echt niet
                        self.assertIn("Kan dat kloppen", m.vraag)

    def test_invoer(self):
        v = VS.SCHATTEN.maak("5", rng=random.Random(2))
        obj = KeuzeInvoer(v, VS.SCHATTEN)
        obj.toets(curses.KEY_F1)
        self.assertTrue(obj.tip_aan)
        uit = obj.toets(ord(v.antwoord))
        self.assertEqual(uit[1], v.antwoord)
        self.assertEqual(obj.extra, {"tips": 1})


if __name__ == "__main__":
    unittest.main()
