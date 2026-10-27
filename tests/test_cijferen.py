import curses
import random
import unittest
from decimal import Decimal
from unittest import mock

from leeravontuur.kern import leerjaren
from leeravontuur.kern.getal import fmt, lees_getal
from leeravontuur.kern.instellingen import Instellingen
from leeravontuur.kern.modellen import Rooster, Staartdeling
from leeravontuur.kern.onderwerp import Vraag
from leeravontuur.kern.wiskunde import cijferen as C
from leeravontuur.terminal.nepscherm import NepScherm
from leeravontuur.terminal.rooster import MAATJE_ONDER, MAATJE_X, RoosterInvoer
from leeravontuur.terminal.scherm import Scherm

try:
    from .test_schermen import ESC, OK, Basis, naar_spiekbrief
    from .test_schermen import naar as naar_onderwerp
except ImportError:
    from test_schermen import ESC, OK, Basis, naar_spiekbrief
    from test_schermen import naar as naar_onderwerp

D = Decimal
TAB, RECHTS = "\t", curses.KEY_RIGHT


class TestGeneratoren(unittest.TestCase):
    def test_alle_leerjaren(self):
        rng = random.Random(5)
        for o in C.ALLE:
            for jaar in leerjaren.LEERJAREN:
                if not o.aangeboden(jaar):
                    continue
                for _ in range(250):
                    v = o.maak(jaar, rng=rng)
                    self.assertTrue(v.sleutel.startswith(o.id + ":"))
                    self.assertIsNotNone(o.onderwerp_van_sleutel(v.sleutel))
                    self.assertTrue(o.uitleg(v))
                    o.diagnose(v, v.antwoord + 1)
                    if v.invoer == "rooster":
                        self.controleer_rooster(o, v)
                    else:
                        self.controleer_staart(v)

    def controleer_rooster(self, o, v):
        r = v.model
        self.assertEqual(lees_getal(r.verwacht[-1]), v.antwoord)
        self.assertLessEqual(RoosterInvoer.X0 + 2 * r.breedte + 30, 80, v.tekst)  # + ruimte voor "uitkomst"
        for tekst in r.gegeven + ([] if r.komma_zelf else [r.verwacht[-1]]):
            cellen, _ = r.plaats(tekst)
            self.assertTrue(all(0 <= c < r.breedte for c in cellen), (v.tekst, tekst))
        if r.komma_zelf:
            a, b = (D(x) for x in (v.data["a"], v.data["b"]))
            self.assertEqual(v.antwoord, a * b)
            for rij, tekst in zip(r.invul[:-1], r.verwacht[:-1]):
                self.assertLessEqual(len(tekst), r.breedte)
            self.assertEqual(sum(int(t) for t in r.verwacht[:-1]) if len(r.invul) > 1 else None,
                             int((a * b).scaleb(C._decimalen(a) + C._decimalen(b))) if len(r.invul) > 1 else None)
        for kol in range(r.breedte):
            for rij in range(-1, len(r.invul)):
                self.assertTrue(o.kolom_hulp(v, rij, kol))

    def controleer_staart(self, v):
        m = v.model
        d = v.data
        deeltal = D(d["deeltal"])
        self.assertEqual(v.antwoord * d["deler"] + d["rest"], deeltal, v.tekst)
        self.assertLess(d["rest"], d["deler"])
        for i in range(len(m.stappen) + 1):
            regels, _ = m.beeld(i)
            self.assertTrue(all(len(r) < 40 for r in regels))
        _, quotient = m.beeld(len(m.stappen))
        self.assertEqual(lees_getal(quotient), v.antwoord)

    def test_herhaling(self):
        v = C.AFTREKKEN.maak("5", data={"soort": "komma"})
        self.assertIn(",", v.tekst)
        data = C.AFTREKKEN.herhaal_data(v)
        self.assertEqual(data["onderwerp"], "kommagetallen")
        self.assertFalse(C.DELEN.aangeboden("3"))


class TestDiagnose(unittest.TestCase):
    def rooster_vraag(self, o, **kw):
        return o.maak("5", data=kw)

    def test_onthouden_vergeten(self):
        v = Vraag(C.OPTELLEN.id, "k", "47 + 35 =", D(82), data={"termen": ["47", "35"]})
        self.assertEqual(C.OPTELLEN.diagnose(v, D(72))[0], "onthouden_vergeten")
        v = Vraag(C.OPTELLEN.id, "k", "", D(1110), data={"termen": ["555", "555"]})
        self.assertEqual(C.OPTELLEN.diagnose(v, D(1100))[0], "onthouden_vergeten")  # alleen de T vergeten

    def test_aftrekken(self):
        v = Vraag(C.AFTREKKEN.id, "k", "523 − 187 =", D(336), data={"a": "523", "b": "187"})
        self.assertEqual(C.AFTREKKEN.diagnose(v, D(464))[0], "kleinste_van_grootste")
        self.assertEqual(C.AFTREKKEN.diagnose(v, D(446))[0], "lenen_vergeten")
        v.model = Rooster("−", ["523", "187"], 3)
        self.assertIn("3 − 7 kan niet", C.AFTREKKEN.kolom_hulp(v, 0, 2))
        self.assertIn("de 2 werd 1", C.AFTREKKEN.kolom_hulp(v, 0, 1))

    def test_vermenigvuldigen(self):
        v = Vraag(C.VERMENIGVULDIGEN.id, "k", "23 × 45 =", D(1035), data={"a": "23", "b": "45"},
                  model=Rooster("×", ["23", "45"], 4, 0, ["rij 1", "rij 2", "uitkomst"], komma_zelf=True))
        self.assertEqual(C.VERMENIGVULDIGEN.diagnose(v, D(207))[0], "niet_opgeschoven")
        self.assertIn("Schrijf hier een 0", C.VERMENIGVULDIGEN.kolom_hulp(v, 1, 3))
        self.assertIn("3 × 5 = 15: schrijf 5, onthoud 1", C.VERMENIGVULDIGEN.kolom_hulp(v, 0, 3))
        w = Vraag(C.VERMENIGVULDIGEN.id, "k", "2,3 × 4,5 =", D("10.35"), data={"a": "2.3", "b": "4.5"})
        self.assertEqual(C.VERMENIGVULDIGEN.diagnose(w, D("103.5"))[0], "komma_product")

    def test_staart_fouten(self):
        g, st, q, r = C.staart_stappen(D(452), 7, 0)
        self.assertEqual((q, r), (64, 4))
        self.assertEqual(C.staart_fout(st[0], 7, 7)[0], "staart_te_veel")
        self.assertEqual(C.staart_fout(st[0], 5, 7)[0], "staart_te_weinig")
        g, st, q, r = C.staart_stappen(D("49.4"), 4, 2)
        self.assertEqual((g, q, r), ("49,40", D("12.35"), 0))
        self.assertTrue(any(s.komma_ervoor for s in st))
        g, st, q, r = C.staart_stappen(D(1236), 12, 0)
        self.assertEqual(q, 103)  # met een 0 in het quotiënt


class TestRooster(unittest.TestCase):
    def test_lees(self):
        r = Rooster("+", ["12,5", "3,25"], 4, 2)
        self.assertEqual(r.lees({0: "1", 1: "5", 2: "7", 3: "5"}), ("15,75", None))
        self.assertIsNone(r.lees({0: "1", 2: "7", 3: "5"})[0])        # gat
        self.assertIsNone(r.lees({0: "1"})[0])                        # eenheden ontbreken
        self.assertEqual(r.lees({1: "5"}), ("5", None))
        r = Rooster("×", ["2,5", "3"], 3, 0, komma_zelf=True)
        self.assertEqual(r.lees({1: "7", 2: "5"}, komma=1), ("7,5", None))
        self.assertEqual(r.plaats("2,5"), ({1: "2", 2: "5"}, 1))

    def test_onthouden_blijft_in_de_kolom(self):
        """#16: een cijfer in de onthouden-rij schuift niet op; ↓ gaat terug naar dezelfde kolom eronder."""
        ri = RoosterInvoer(optel_vraag(), C.OPTELLEN)
        for k in (ord("2"), curses.KEY_UP, ord("1"), curses.KEY_DOWN, ord("3")):
            ri.toets(k)
        self.assertEqual(ri.onth, {2: "1"})
        self.assertEqual(ri.cellen[0], {3: "2", 2: "3"})

    def test_onthouden_en_terug_naar_dezelfde_rij(self):
        """#16: in rij 2 van een vermenigvuldiging getypt, naar de onthouden-rij en met ↓ terug naar rij 2."""
        ri = RoosterInvoer(maal_vraag(), C.VERMENIGVULDIGEN)
        ri.rij, ri.kol = 1, 3
        for k in (ord("0"), curses.KEY_UP, curses.KEY_UP, ord("1"), curses.KEY_DOWN):
            ri.toets(k)
        self.assertEqual((ri.rij, ri.kol, ri.onth), (1, 2, {2: "1"}))


class TestPlaatswaarden(unittest.TestCase):
    """#18: p zet E T H … boven de kolommen."""

    def teken(self, ri):
        s = Scherm(NepScherm(), Instellingen(), False)
        ri.teken(s, 8)
        return s, s.win.tekst().splitlines()

    def test_elke_kolom_heeft_een_naam(self):
        """Elk rooster (+, −, × zonder komma) in elk leerjaar: elke kolom heeft een plaatswaarde."""
        rng = random.Random(18)
        for o in (C.OPTELLEN, C.AFTREKKEN, C.VERMENIGVULDIGEN):
            for jaar in leerjaren.LEERJAREN:
                if not o.aangeboden(jaar):
                    continue
                for _ in range(60):
                    r = o.maak(jaar, rng=rng).model
                    if r.plaatswaarden_kloppen():
                        with self.subTest(o=o.id, jaar=jaar, gegeven=r.gegeven):
                            self.assertTrue(all(r.plaats_naam(c) for c in range(r.breedte)))
                    else:
                        self.assertTrue(r.komma_zelf and any("," in g for g in r.gegeven))

    def test_namen(self):
        r = Rooster("+", ["12,5", "3,25"], 5, 2)
        self.assertEqual([r.plaats_naam(c)[0] for c in range(5)], ["H", "T", "E", "t", "h"])
        self.assertEqual(r.plaats_naam(1), ("T", "tientallen"))
        self.assertIsNone(Rooster("×", ["2,5", "3"], 3, 0, komma_zelf=True).plaats_naam(2))

    def test_aan_en_uit(self):
        ri = RoosterInvoer(optel_vraag(), C.OPTELLEN)
        _, regels = self.teken(ri)
        self.assertNotIn("H  T  E", regels[7])
        ri.toets(ord("p"))
        self.assertTrue(ri.plaatswaarden)
        s, regels = self.teken(ri)
        self.assertIn("D  H  T  E  ◂ je staat bij de E (eenheden)", regels[7])
        self.assertEqual(regels[8].index("·") + 3, regels[8].index("·", regels[8].index("·") + 1))  # breder
        ri.toets(ord("4"))  # een cijfer: je staat nu bij de T
        _, regels = self.teken(ri)
        self.assertIn("◂ je staat bij de T (tientallen)", regels[7])
        ri.toets(ord("P"))
        self.assertFalse(ri.plaatswaarden)
        self.assertIn("Plaatswaarden uit", ri.melding)

    def test_klik_met_plaatswaarden(self):
        """Met de bredere kolommen kiest een klik nog altijd het juiste vakje."""
        ri = RoosterInvoer(optel_vraag(), C.OPTELLEN)
        ri.plaatswaarden = True
        s, regels = self.teken(ri)
        y = 8 + 1 + 2 + 1  # onthouden, 2 getallen, de streep: de uitkomst
        self.assertEqual(s.zones.zoek(y, ri.x(1)), ("cel", 0, 1))
        self.assertEqual(ri.x(1) - ri.x(0), 3)

    def test_maal_met_komma(self):
        v = Vraag(C.VERMENIGVULDIGEN.id, "x", "2,5 × 3 =", D("7.5"), invoer="rooster",
                  model=Rooster("×", ["2,5", "3"], 3, 0, ["uitkomst"], ["7,5"], komma_zelf=True))
        ri = RoosterInvoer(v, C.VERMENIGVULDIGEN)
        self.assertNotIn("p", [k[0] for k in ri.knoppen()])
        ri.toets(ord("p"))
        self.assertIn("Bij × met een komma", ri.melding)
        ri.plaatswaarden = True  # ook als het kind ze aan heeft: hier geen letters
        _, regels = self.teken(ri)
        self.assertNotIn("E", regels[7])
        self.assertEqual(ri.x(1) - ri.x(0), 2)

    def test_past_overal(self):
        """Het breedste rooster in elk leerjaar, met plaatswaarden: binnen 80 tekens, niet over het maatje, en de
        voetregel past."""
        rng = random.Random(81)
        for o in (C.OPTELLEN, C.AFTREKKEN, C.VERMENIGVULDIGEN):
            for jaar in leerjaren.LEERJAREN:
                if not o.aangeboden(jaar):
                    continue
                v = max((o.maak(jaar, rng=rng) for _ in range(60)), key=lambda v: v.model.breedte)
                ri = RoosterInvoer(v, o)
                ri.plaatswaarden = True
                for kol in range(v.model.breedte):
                    ri.kol = kol
                    with self.subTest(o=o.id, jaar=jaar, kol=kol):
                        _, regels = self.teken(ri)
                        self.assertIn("uitkomst  (typrichting ←)", "\n".join(regels))  # niet afgeknipt
                        for y, regel in enumerate(regels[:MAATJE_ONDER + 1]):
                            self.assertLessEqual(len(regel), MAATJE_X, (y, regel))
                voet = "  ".join(f"[{t}] {u}" for t, u, _ in ri.knoppen())
                self.assertLessEqual(len(voet) + 1, 80, voet)


def staart_vraag():
    g, st, q, r = C.staart_stappen(D(452), 7, 0)
    return Vraag(C.DELEN.id, f"{C.DELEN.id}:452:7", "452 : 7 =", q, invoer="staart", model=Staartdeling(g, 7, st, r),
                 data={"deeltal": "452", "deler": 7, "dec": 0, "rest": r, "soort": "rest", "onderwerp": "met rest"},
                 verwacht_tekst="64 rest 4")


def optel_vraag():
    return Vraag(C.OPTELLEN.id, f"{C.OPTELLEN.id}:347+85", "347 + 85 =", D(432), invoer="rooster",
                 model=Rooster("+", ["347", "85"], 4, 0, verwacht=["432"]),
                 data={"op": "+", "termen": ["347", "85"], "soort": "natuurlijk", "onderwerp": "natuurlijke getallen"})


def maal_vraag():
    return Vraag(C.VERMENIGVULDIGEN.id, f"{C.VERMENIGVULDIGEN.id}:23x45", "23 × 45 =", D(1035), invoer="rooster",
                 model=Rooster("×", ["23", "45"], 4, 0, ["rij 1", "rij 2", "uitkomst"], ["115", "920", "1035"],
                               komma_zelf=True),
                 data={"op": "×", "a": "23", "b": "45", "soort": "natuurlijk", "onderwerp": "× 2 cijfers"})


def naar(onderwerp):
    """Wiskunde › domein › het onderwerp met dit nummer in C.ALLE › V (vrij oefenen) › Normaal."""
    return naar_onderwerp(C.ALLE[onderwerp - 1])


STOP = [ESC] * 7


class TestSchermen(Basis):
    def test_optellen_in_rooster(self):
        o = self.opslag(("Test", "5"))
        with mock.patch.object(C.OPTELLEN, "maak", side_effect=[optel_vraag(), optel_vraag()]):
            scherm, app = self.speel([*naar(1), "?", *"234", OK, *STOP], opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertTrue(rij["juist"])
        self.assertEqual(rij["gegeven"], "432")
        self.assertTrue(rij["hulp"])
        self.assertTrue(self.ergens(scherm, "Kolom E: 7 + 5 = 12: schrijf 2"))

    def test_onthouden_vergeten_en_onthoudrij(self):
        o = self.opslag(("Test", "5"))
        # eerst een 1 in de onthouden-rij (↑, ←, 1), dan terug naar de uitkomst en 422 typen
        with mock.patch.object(C.OPTELLEN, "maak", side_effect=[optel_vraag(), optel_vraag()]):
            scherm, app = self.speel([*naar(1), curses.KEY_UP, curses.KEY_LEFT, "1", curses.KEY_DOWN, RECHTS, RECHTS,
                                      *"224", OK, *STOP], opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertFalse(rij["juist"])
        self.assertEqual(rij["diagnose"], "onthouden_vergeten")

    def test_leeg_vakje(self):
        o = self.opslag(("Test", "5"))
        with mock.patch.object(C.OPTELLEN, "maak", side_effect=[optel_vraag(), optel_vraag()]):
            scherm, app = self.speel([*naar(1), "2", " ", "4", OK, *STOP], opslag=o)
        self.assertTrue(self.ergens(scherm, "leeg vakje"))
        self.assertEqual(o.antwoorden(app.kind.id), [])

    def test_vermenigvuldigen_met_rijen_en_klik(self):
        o = self.opslag(("Test", "5"))
        x0 = RoosterInvoer.X0
        # rij 1 = 115, Tab, rij 2 = 920, Tab, uitkomst 1035 (de laatste via een klik op het vakje rechts)
        with mock.patch.object(C.VERMENIGVULDIGEN, "maak", side_effect=[maal_vraag(), maal_vraag()]):
            scherm, app = self.speel([*naar(3), *"511", TAB, *"029", ("klik", 15, x0 + 6), *"5301", OK, *STOP],
                                     opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertEqual(rij["gegeven"], "1035")
        self.assertTrue(rij["juist"])

    def test_komma_zelf_zetten(self):
        o = self.opslag(("Test", "5"))
        v = Vraag(C.VERMENIGVULDIGEN.id, f"{C.VERMENIGVULDIGEN.id}:2,5x3", "2,5 × 3 =", D("7.5"), invoer="rooster",
                  model=Rooster("×", ["2,5", "3"], 3, 0, ["uitkomst"], ["7,5"], komma_zelf=True),
                  data={"op": "×", "a": "2.5", "b": "3", "soort": "komma", "onderwerp": "kommagetallen"})
        with mock.patch.object(C.VERMENIGVULDIGEN, "maak", side_effect=[v, v]):
            scherm, app = self.speel([*naar(3), *"57", RECHTS, ",", OK, *STOP], opslag=o)
        self.assertEqual(o.antwoorden(app.kind.id)[0]["gegeven"], "7,5")

    def test_staartdeling(self):
        o = self.opslag(("Test", "5"))
        stappen = ["6", "42", "3", "32", "4", "28", "4"]
        toetsen = [t for st in stappen for t in (*st, OK)]
        with mock.patch.object(C.DELEN, "maak", side_effect=[staart_vraag(), staart_vraag()]):
            scherm, app = self.speel([*naar(4), *toetsen, *STOP], opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertTrue(rij["juist"])
        self.assertEqual(rij["gegeven"], "64 rest 4")
        self.assertTrue(self.ergens(scherm, "Hoeveel keer gaat 7 in 45?"))
        self.assertTrue(self.ergens(scherm, "Haal de 2 neer"))

    def test_staartdeling_met_fout(self):
        o = self.opslag(("Test", "5"))
        stappen = ["7", "6", "42", "3", "32", "4", "28", "4"]  # eerst 7 (te veel), daarna juist
        toetsen = [t for st in stappen for t in (*st, OK)]
        with mock.patch.object(C.DELEN, "maak", side_effect=[staart_vraag(), staart_vraag()]):
            scherm, app = self.speel([*naar(4), *toetsen, *STOP], opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertFalse(rij["juist"])
        self.assertEqual(rij["diagnose"], "staart_te_veel")
        self.assertTrue(self.ergens(scherm, "7 × 7 = 49, dat is meer dan 45"))

    def test_plaatswaarden_onthouden(self):
        """#18: p bij de eerste vraag; de volgende vraag en een nieuwe start hebben ze ook (per kind bewaard)."""
        o = self.opslag(("Test", "5"))
        with mock.patch.object(C.OPTELLEN, "maak", side_effect=[optel_vraag()] * 3):
            scherm, app = self.speel([*naar(1), "p", *"234", OK, OK, ESC], opslag=o)
        self.assertTrue(o.instellingen_van(app.kind.id).plaatswaarden)
        vragen = [b for b in scherm.beelden if "347 + 85" in b and "Plaatswaarden aan" not in b]
        self.assertIn("◂ je staat bij de E (eenheden)", vragen[-1])  # de tweede vraag: meteen aan
        with mock.patch.object(C.OPTELLEN, "maak", side_effect=[optel_vraag()] * 2):
            scherm, _ = self.speel([*naar(1), ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "D  H  T  E  ◂ je staat bij de E"))

    def test_spiekbrief(self):
        scherm, _ = self.speel([*naar_spiekbrief("Cijferen"), ESC, ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "STAARTDELING"))


if __name__ == "__main__":
    unittest.main()
