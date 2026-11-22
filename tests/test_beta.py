"""De beta van de schermen 1.0 (werk/schermen.md): Cijferen in vakken, alleen met LEERAVONTUUR_BETA=1."""

import os
import random
import unittest

from leeravontuur.kern.leerjaren import LEERJAREN
from leeravontuur.kern.onderwerp import ONDERWERPEN
from leeravontuur.terminal import beta
from leeravontuur.terminal import curriculum as CU
from leeravontuur.terminal.oefenaar import INVOER, Oefenaar

from test_schermen import OK, Basis, naar

TAB = 9

CIJFEREN = [o for o in ONDERWERPEN.values() if o.id.startswith("wiskunde.cijferen.")]


class MetBeta:
    def __init__(self, waarde):
        self.waarde = waarde

    def __enter__(self):
        self.oud = os.environ.get("LEERAVONTUUR_BETA")
        if self.waarde is None:
            os.environ.pop("LEERAVONTUUR_BETA", None)
        else:
            os.environ["LEERAVONTUUR_BETA"] = self.waarde

    def __exit__(self, *_):
        if self.oud is None:
            os.environ.pop("LEERAVONTUUR_BETA", None)
        else:
            os.environ["LEERAVONTUUR_BETA"] = self.oud


class TestKeuze(unittest.TestCase):
    def test_alleen_cijferen_en_alleen_als_ze_aan_staat(self):
        with MetBeta(None):
            self.assertIs(beta.oefenaar_klasse("Cijferen"), Oefenaar)
        with MetBeta("1"):
            self.assertIs(beta.oefenaar_klasse("Cijferen"), beta.BetaOefenaar)
            for d in CU.VAKKEN[0].domeinen:
                if d.label != "Cijferen":
                    self.assertIs(beta.oefenaar_klasse(d.label), Oefenaar)


class Opnemer:
    """Een nepscherm dat elke put onthoudt (om na te kijken dat niets buiten het vak valt)."""

    def __init__(self):
        self.puts = []
        self.zones = self

    def put(self, y, x, tekst, rol=""):
        self.puts.append((y, x, tekst))

    def voeg(self, *_):
        pass

    def tekstvak(self, y, x, tekst, breedte, rol, actie=None):
        self.puts.append((y, x, " " * (breedte + 2)))


class TestPast(unittest.TestCase):
    def test_elk_rooster_en_elke_staartdeling_past_in_het_vak(self):
        """Elk leerjaar, met en zonder plaatswaarden: niets wordt afgeknipt aan de rand van het vak (80×24)."""
        links = 80 - beta.RECHTS
        for o in CIJFEREN:
            for jaar in LEERJAREN:
                if not o.aangeboden(jaar):
                    continue
                for zaad in range(25):
                    v = o.maak(jaar, rng=random.Random(zaad))
                    for pw in (False, True):
                        obj = INVOER[v.invoer](v, o)
                        obj.plaatswaarden = pw
                        s = Opnemer()
                        obj.teken(beta.InVak(s, beta.VERSCHUIF[v.invoer], 2, links - 2), 5, None, False)
                        for y, x, tekst in s.puts:
                            with self.subTest(o=o.id, jaar=jaar, zaad=zaad, tekst=tekst):
                                self.assertGreaterEqual(x, 2)
                                self.assertLessEqual(x + len(tekst.rstrip()), links - 2)
                        self.assertLessEqual(5 + obj.hoogte() + 2 + 3, 23, (o.id, jaar))  # + hint + vak Tip


class TestScherm(Basis):
    def test_staartdeling_in_vakken_en_bewaard(self):
        o = ONDERWERPEN["wiskunde.cijferen.delen"]
        with MetBeta("1"):
            scherm, app = self.speel([*naar(o, "Enter"), *["0", OK] * 40])
        beeld = next(b for b in scherm.beelden if "Vraag 1 van 10" in b)
        self.assertIn("╭─┤ Vraag 1 van 10 ├", beeld)
        self.assertIn("┤ Tip ├", beeld)
        self.assertIn("┤ Reeks ├", beeld)
        self.assertTrue(all(len(r) <= 80 for r in beeld.splitlines()))
        self.assertTrue(self.ergens(scherm, "┤ Wat ging er mis? ├") or self.ergens(scherm, "┤ Uitleg ├")
                        or self.ergens(scherm, "┤ Goed! ├"))
        rij = app.opslag.antwoorden(app.kind.id)[0]
        self.assertEqual(rij["vaardigheid"], o.id)

    def test_klad_naast_het_rooster_wordt_bewaard(self):
        """Vermenigvuldigen past in 80×24 met een klad ernaast: K = naar het klad, Tab = terug; het klad gaat mee
        met het antwoord (extra["klad"])."""
        o = ONDERWERPEN["wiskunde.cijferen.vermenigvuldigen"]
        with MetBeta("1"):
            scherm, app = self.speel([*naar(o, "Enter"), "k", *"2 x 3 = 6", OK, TAB, OK])
        self.assertTrue(self.ergens(scherm, "┤ ▸ Klad ├"))
        self.assertTrue(self.ergens(scherm, "[K] klad"))
        rij = app.opslag.antwoorden(app.kind.id)
        self.assertEqual(rij, [])  # Enter met een leeg rooster: nog niets nagekeken
        self.assertIn("2 × 3 = 6", [b for b in scherm.beelden if "▸ Klad" in b][-1])

    def test_spiekbrief_onderaan_op_een_groot_scherm_niet_in_een_examen(self):
        from leeravontuur.kern.reeks import Hulp
        o = ONDERWERPEN["wiskunde.cijferen.optellen"]
        with MetBeta("1"):
            scherm, _ = self.speel([*naar(o, "Enter")], hoogte=46, breedte=150)
        beeld = next(b for b in scherm.beelden if "Vraag 1 van 10" in b)
        self.assertIn("┤ Spiekbrief ├", beeld)
        self.assertIn("▸ OPTELLEN", beeld)
        self.assertFalse(Hulp.EXAMEN.spiekbrief)  # in een examen: geen spiekbrief (spiek = ... and hulp.spiekbrief)

    def test_zonder_beta_het_gewone_scherm(self):
        o = ONDERWERPEN["wiskunde.cijferen.delen"]
        with MetBeta(None):
            scherm, _ = self.speel([*naar(o, "Enter")])
        self.assertFalse(self.ergens(scherm, "╭─┤"))
        self.assertTrue(self.ergens(scherm, "Vraag 1 van 10"))


if __name__ == "__main__":
    unittest.main()
