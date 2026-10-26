"""De vaste werkwijze bewaken: elk onderwerp met klad kent zijn oplossing in klad-regels, en de tips verklappen niets."""

import random
import re
import unittest
from fractions import Fraction

from leeravontuur.kern import catalogus  # noqa: F401  (registreert alle onderwerpen)
from leeravontuur.kern.getal import fmt
from leeravontuur.kern.klad import lees_regel
from leeravontuur.kern.leerjaren import LEERJAREN
from leeravontuur.kern.onderwerp import ONDERWERPEN

ZADEN = 30
# onderwerpen waarin gerekend wordt: die moeten een klad hebben (de vaste werkwijze)
MET_KLAD = {"wiskunde.hoofdrekenen.splitsen", "wiskunde.hoofdrekenen.plusmin", "wiskunde.hoofdrekenen.dubbelhelft",
            "wiskunde.hoofdrekenen.tafels", "wiskunde.procenten.van", "wiskunde.procenten.korting",
            "wiskunde.breuken.van", "wiskunde.breuken.optellen", "wiskunde.eenheden.tijd", "wiskunde.eenheden.geld",
            "wiskunde.eenheden.snelheid", "wiskunde.eenheden.klok", "wiskunde.meetkunde.formules",
            "wiskunde.meetkunde.schaal"}


def vragen(o):
    for jaar in LEERJAREN:
        if not o.aangeboden(jaar):
            continue
        for zaad in range(ZADEN):
            yield jaar, zaad, o.maak(jaar, rng=random.Random(zaad))


def als_getal(x):
    if isinstance(x, Fraction):
        return x
    return Fraction(str(x))


class TestWerkwijze(unittest.TestCase):
    def test_elk_rekenonderwerp_heeft_klad(self):
        for oid in MET_KLAD:
            self.assertIn(ONDERWERPEN[oid].klad, ("ja", "verplicht"), oid)

    def test_oplossing_klopt_en_eindigt_op_het_antwoord(self):
        for oid, o in ONDERWERPEN.items():
            for jaar, zaad, v in vragen(o):
                if not o.klad_voor(v):
                    continue
                with self.subTest(oid=oid, jaar=jaar, zaad=zaad, vraag=v.tekst):
                    opl = o.oplossing(v)
                    self.assertTrue(opl and opl.stappen, "geen oplossing")
                    for st in opl.stappen:
                        r = lees_regel(st.reken)
                        self.assertTrue(r.juist, f"{st.reken}: {r.melding}")
                    self.assertEqual(lees_regel(opl.stappen[-1].reken).uitkomst % (1440 if v.invoer == "klok" else 10 ** 9),
                                     als_getal(v.antwoord) % (1440 if v.invoer == "klok" else 10 ** 9),
                                     opl.stappen[-1].reken)

    def test_tips_verklappen_het_antwoord_niet(self):
        for oid, o in ONDERWERPEN.items():
            for jaar, zaad, v in vragen(o):
                if not o.klad_voor(v):
                    continue
                antwoord = v.verwacht.split(" ")[0] if v.invoer in ("klok", "duur") else fmt(v.antwoord) \
                    if not isinstance(v.antwoord, Fraction) else None
                if not antwoord or re.search(rf"(?<![\d,./]){re.escape(antwoord)}(?![\d,/])", v.tekst):
                    continue  # het antwoord staat al in de vraag (bv. een omzetting terug)
                with self.subTest(oid=oid, jaar=jaar, zaad=zaad, vraag=v.tekst):
                    # de tip uit de oplossing (het begin van het klad) mag de uitkomst niet tonen; de vaste tips
                    # (bv. "een uur heeft 60 minuten") zijn algemeen en schreven we zelf
                    for tip in (t for t in o.tips(v) if t.startswith("Begin je klad zo:")):
                        getoond = tip.split("=", 1)[1]  # wat na de eerste = staat: de tussenstappen
                        self.assertNotRegex(getoond, rf"(?<![\d,./]){re.escape(antwoord)}(?![\d,/])", tip)

    def test_splitsen_vraagt_eerst_een_splitsing(self):
        o = ONDERWERPEN["wiskunde.hoofdrekenen.splitsen"]
        for jaar, zaad, v in vragen(o):
            with self.subTest(jaar=jaar, zaad=zaad, vraag=v.tekst):
                self.assertFalse(o.klad_klaar(v, [])[0])
                self.assertFalse(o.klad_klaar(v, [lees_regel(f"{v.tekst} {fmt(v.antwoord)}")])[0])
                self.assertTrue(o.klad_klaar(v, [lees_regel(st.reken) for st in o.oplossing(v).stappen])[0])


if __name__ == "__main__":
    unittest.main()
