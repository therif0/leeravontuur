"""De beta van de schermen 1.0 (werk/schermen.md): Cijferen in vakken, alleen met LEERAVONTUUR_BETA=1."""

import os
import unittest

from leeravontuur.kern.onderwerp import ONDERWERPEN
from leeravontuur.terminal import beta
from leeravontuur.terminal import curriculum as CU
from leeravontuur.terminal.oefenaar import Oefenaar

from test_schermen import OK, Basis, naar

TAB = 9


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


class TestScherm(Basis):
    def test_staartdeling_in_vakken_en_bewaard(self):
        o = ONDERWERPEN["wiskunde.cijferen.delen"]
        with MetBeta("1"):
            scherm, app = self.speel([*naar(o, "Enter"), *["0", OK] * 40])
        beeld = next(b for b in scherm.beelden if "Vraag 1 van 10" in b)
        self.assertIn("╭─┤ Vraag 1 van 10 ├", beeld)
        self.assertIn("┤ Tip ├", beeld)
        self.assertTrue(beeld.splitlines()[1].startswith(" Reeks "))  # 24 rijen: de reeks is één regel bovenaan
        self.assertTrue(all(len(r) <= 80 for r in beeld.splitlines()))
        self.assertTrue(self.ergens(scherm, "┤ Wat ging er mis? ├") or self.ergens(scherm, "┤ Uitleg ├")
                        or self.ergens(scherm, "┤ Goed! ├"))
        rij = app.opslag.antwoorden(app.kind.id)[0]
        self.assertEqual(rij["vaardigheid"], o.id)

    def test_geen_klad_bij_cijferen_tab_is_volgende_rij(self):
        """De vader 22/11: Cijferen krijgt geen klad-kolom (het rooster is het rekenwerk); Tab houdt in het rooster zijn
        betekenis (volgende rij)."""
        o = ONDERWERPEN["wiskunde.cijferen.vermenigvuldigen"]
        with MetBeta("1"):
            scherm, _ = self.speel([*naar(o, "Enter"), TAB], hoogte=40, breedte=120)
        self.assertFalse(self.ergens(scherm, "┤ Klad ├"))
        self.assertFalse(self.ergens(scherm, "[Tab] klad"))
        self.assertTrue(self.ergens(scherm, "Tab = volgende rij"))

    def test_spiekbrief_onderaan_op_een_groot_scherm_niet_in_een_examen(self):
        from leeravontuur.kern.reeks import Hulp
        o = ONDERWERPEN["wiskunde.cijferen.optellen"]
        with MetBeta("1"):
            scherm, _ = self.speel([*naar(o, "Enter")], hoogte=46, breedte=150)
        beeld = next(b for b in scherm.beelden if "Vraag 1 van 10" in b)
        self.assertIn("┤ Spiekbrief ├", beeld)
        self.assertIn("▸ OPTELLEN", beeld)
        self.assertFalse(Hulp.EXAMEN.spiekbrief)  # in een examen: geen spiekbrief (spiek = ... and hulp.spiekbrief)

    def test_spiekbrief_scrollt(self):
        """Past de spiekbrief niet: PgDn en het scrollwiel tonen de rest."""
        import curses
        o = ONDERWERPEN["wiskunde.cijferen.vermenigvuldigen"]
        with MetBeta("1"):
            scherm, _ = self.speel([*naar(o, "Enter"), curses.KEY_NPAGE, ("wiel", 1)], hoogte=34, breedte=110)
        beelden = [b for b in scherm.beelden if "┤ Spiekbrief ├" in b]
        self.assertIn("PgUp PgDn", beelden[0])
        self.assertIn("▸ VERMENIGVULDIGEN", beelden[0])
        self.assertNotIn("▸ VERMENIGVULDIGEN", beelden[-1])
        self.assertTrue(all("[Esc] stoppen" in b for b in beelden))

    def test_zonder_beta_het_gewone_scherm(self):
        o = ONDERWERPEN["wiskunde.cijferen.delen"]
        with MetBeta(None):
            scherm, _ = self.speel([*naar(o, "Enter")])
        self.assertFalse(self.ergens(scherm, "╭─┤"))
        self.assertTrue(self.ergens(scherm, "Vraag 1 van 10"))


if __name__ == "__main__":
    unittest.main()
