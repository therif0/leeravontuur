"""Een invoer-object zegt zelf hoe de Oefenaar het behandelt (geen lijsten per soort in de Oefenaar)."""

import unittest
from types import SimpleNamespace

from leeravontuur.terminal import oefenaar as OE
from leeravontuur.terminal.stappenhulp import StappenHulp


class TestInvoerObjecten(unittest.TestCase):
    def test_geen_tweede_kans_zoals_voor_de_opkuis(self):
        self.assertEqual(OE.GEEN_TWEEDE_KANS, {"janee", "vergelijk", "keuze", "rooster", "staart", "vraagstuk",
                                               "speur", "zinsdelen", "werkwoord"})

    def test_vraagtekst(self):
        def v(tekst, invoer):
            return SimpleNamespace(tekst=tekst, invoer=invoer)
        self.assertEqual(OE.vraagtekst(v("7 × 8 =", "getal")), "7 × 8 = ?")
        self.assertEqual(OE.vraagtekst(v("Hoeveel kost het?", "vraagstuk")), "Hoeveel kost het?")
        self.assertEqual(OE.vraagtekst(v("De juf geeft een boek.", "zinsdelen")), "De juf geeft een boek.")
        self.assertEqual(OE.vraagtekst(v("Gisteren ___ Noor.", "werkwoord")), "Gisteren ___ Noor.")

    def test_stappenhulp_tips_en_spiekbrief(self):
        h = StappenHulp()
        h.v = SimpleNamespace(data={})
        h.begin_hulp()
        h.geef_tip(["eerst dit", "dan dat"], "KOP")
        self.assertEqual((h.tiptekst, h.tips_op, h.v.data["spiek_kop"]), ("Tip 1: eerst dit", False, "KOP"))
        h.geef_tip(["eerst dit", "dan dat"], "KOP")
        self.assertTrue(h.tiptekst.endswith("Nog eens F1: je spiekbrief.") and h.tips_op)
        h.spiekbrief_bekeken()
        self.assertEqual((h.tip_nr, h.tiptekst, h.tips), (0, "", 3))
        h.spiekbrief_aan = False
        h.geef_tip(["enige tip"], "KOP")
        self.assertEqual(h.tiptekst, "Tip 1: enige tip")
        h.geef_tip(["enige tip"], "KOP")
        self.assertTrue(h.tiptekst.startswith("Meer tips zijn er niet"))


if __name__ == "__main__":
    unittest.main()
