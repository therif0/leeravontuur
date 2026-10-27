import curses
import random
import re
import unittest
from decimal import Decimal
from itertools import count
from unittest import mock

from leeravontuur.kern import herhaling, leerjaren
from leeravontuur.kern import snelrekenen as SR
from leeravontuur.kern.getal import lees_getal
from leeravontuur.kern.onderwerp import Vraag
from leeravontuur.kern.wiskunde import hoofdrekenen as H
from leeravontuur.terminal.schermen.snelrekenen import Snelrekenen

try:
    from .test_schermen import ESC, OK, Basis, hm, naar
except ImportError:
    from test_schermen import ESC, OK, Basis, hm, naar


def reken(tekst):
    """'7 × 8 =' → 56 (om de generator na te rekenen)."""
    expr = tekst.rstrip(" =").replace("−", "-").replace("×", "*").replace(":", "/").replace(",", ".")
    getallen = [Decimal(g) for g in re.findall(r"-?\d+(?:\.\d+)?", expr)]
    op = re.search(r"\s([+\-*/])\s", expr).group(1)
    a, b = getallen
    return {"+": a + b, "-": a - b, "*": a * b, "/": a / b}[op]


class TestGeneratoren(unittest.TestCase):
    def test_alle_leerjaren(self):
        rng = random.Random(3)
        for o in H.ALLE:
            for jaar in leerjaren.LEERJAREN:
                if not o.aangeboden(jaar):
                    continue
                for _ in range(400):
                    v = o.maak(jaar, rng=rng)
                    if o is not H.DUBBELHELFT:
                        self.assertEqual(reken(v.tekst), v.antwoord, v.tekst)
                    else:
                        g = Decimal(v.data["getal"])
                        self.assertEqual(v.antwoord, g * 2 if v.data["soort"] == "dubbel" else g / 2)
                    self.assertTrue(o.uitleg(v))
                    o.tip(v)
                    o.diagnose(v, v.antwoord + 1)
                    self.assertTrue(v.sleutel.startswith(o.id + ":"))

    def test_niveaus(self):
        rng = random.Random(4)
        for _ in range(200):
            v = H.PLUSMIN.maak("4", rng=rng)
            self.assertEqual(v.antwoord, v.antwoord.to_integral_value())
            self.assertGreaterEqual(v.antwoord, 0)
        self.assertTrue(any(H.PLUSMIN.maak("m1", rng=rng).antwoord < 0 for _ in range(300)))
        self.assertFalse(H.MAALDEEL10.aangeboden("3"))

    def test_herhaling_behoudt_de_tafel(self):
        v = H.TAFELS.maak("5", data={"tafel": 7})
        data = H.TAFELS.herhaal_data(v)
        self.assertEqual(data["onderwerp"], "tafel 7")
        for _ in range(20):
            self.assertEqual(H.TAFELS.maak_herhaling(data, "5").data["tafel"], 7)
        self.assertEqual(H.TAFELS.onderwerp_van_sleutel(v.sleutel), "tafel 7")


class TestDiagnose(unittest.TestCase):
    def vraag(self, o, **data):
        return o.maak("5", data=data)

    def test_tafels(self):
        v = Vraag(H.TAFELS.id, "k", "7 × 6 =", Decimal(42),
                  data={"a": 7, "b": 6, "delen": False, "veelvoud": False, "tafel": 7})
        self.assertEqual(H.TAFELS.diagnose(v, Decimal(13))[0], "plus_ipv_maal")
        self.assertEqual(H.TAFELS.diagnose(v, Decimal(49))[0], "buurtafel")
        self.assertIsNone(H.TAFELS.diagnose(v, Decimal(42)))
        self.assertIn("Ken je 7 × 5 = 35", " ".join(H.TAFELS.uitleg(v)))
        w = Vraag(H.TAFELS.id, "k", "7 × 8 =", Decimal(56),
                  data={"a": 7, "b": 8, "delen": False, "veelvoud": False, "tafel": 7})
        self.assertIn("7 → 14 → 28 → 56", " ".join(H.TAFELS.uitleg(w)))

    def test_plusmin(self):
        v = Vraag(H.PLUSMIN.id, "k", "47 + 99 =", Decimal(146),
                  data={"a": "47", "b": "99", "op": "+", "strategie": "compenseren", "rond": 100, "verschil": 1,
                        "schaal": 1})
        self.assertEqual(H.PLUSMIN.diagnose(v, Decimal(148))[0], "compenseren_verkeerd")
        self.assertEqual(H.PLUSMIN.diagnose(v, Decimal(-52))[0], "verkeerde_bewerking")
        self.assertEqual(H.PLUSMIN.diagnose(v, Decimal(136))[0], "onthouden")
        self.assertIn("47 + 100 = 147", " ".join(H.PLUSMIN.uitleg(v)))

    def test_maaldeel10_en_dubbel(self):
        v = Vraag(H.MAALDEEL10.id, "k", "3,5 × 100 =", Decimal(350), data={"getal": "3.5", "m": "100", "op": "×"})
        self.assertEqual(H.MAALDEEL10.diagnose(v, Decimal("0.035"))[0], "verkeerde_richting_10")
        self.assertEqual(H.MAALDEEL10.diagnose(v, Decimal(35))[0], "plaatsen_10")
        w = Vraag(H.DUBBELHELFT.id, "k", "Het dubbel van 36 =", Decimal(72), data={"getal": "36", "soort": "dubbel"})
        self.assertEqual(H.DUBBELHELFT.diagnose(w, Decimal(18))[0], "helft_dubbel")

    def test_negatief_lezen(self):
        self.assertEqual(lees_getal("-12"), -12)
        self.assertEqual(lees_getal("−3,5"), Decimal("-3.5"))
        self.assertIsNone(lees_getal("-"))


class TestSchermen(Basis):
    def test_reeks_tafels(self):
        o = self.opslag(("Test", "5"))
        vragen = [Vraag(H.TAFELS.id, f"{H.TAFELS.id}:t7:7x{i}", f"7 × {i} =", Decimal(7 * i),
                        data={"a": 7, "b": i, "delen": False, "veelvoud": False, "tafel": 7, "onderwerp": "tafel 7"})
                  for i in range(1, 11)]
        antwoorden = []
        for i in range(1, 11):
            antwoorden += [*str(7 * i), OK, OK] if i != 6 else [*"41", OK, *"41", OK, OK]  # fout: tweede kans
        with mock.patch.object(H.TAFELS, "maak", side_effect=vragen):
            scherm, app = self.speel([*naar(H.TAFELS, "Enter"), *antwoorden,
                                      ESC, ESC, ESC, ESC, ESC, ESC], opslag=o)
        rijen = o.antwoorden(app.kind.id)
        self.assertEqual(len(rijen), 10)
        self.assertEqual(sum(r["juist"] for r in rijen), 9)
        self.assertTrue(all(r["vaardigheid"] == H.TAFELS.id for r in rijen))
        self.assertTrue(self.ergens(scherm, "Je score: 9 / 10"))
        self.assertTrue(self.ergens(scherm, "Ken je 7 × 5 = 35"))
        self.assertEqual([i["onderwerp"] for i in o.herhaalbak(app.kind.id)], ["tafel 7"])

    def test_snelrekenen_20_sommen(self):
        o = self.opslag(("Test", "5"))
        vast = Vraag(H.TAFELS.id, f"{H.TAFELS.id}:t2:2x3", "2 × 3 =", Decimal(6), data={})
        with mock.patch.object(SR, "vraag", return_value=(H.TAFELS, vast)):
            scherm, app = self.speel([*naar(H.TAFELS, "z", niveau=None), *(["6", OK] * 20), OK, ESC, ESC, ESC],
                                     opslag=o)
        self.assertTrue(self.ergens(scherm, "Juist: 20 van 20"))
        self.assertTrue(self.ergens(scherm, "eerste snelrekenronde van vandaag"))
        self.assertEqual(SR.record(o, app.kind.id, "snel20", "tafels")["juist"], 20)

    def test_snelrekenen_60_seconden_met_klok(self):
        o = self.opslag(("Test", "5"))
        tikken = count(0, 7)  # elke keer dat de klok gelezen wordt: 7 seconden later
        vast = Vraag(H.TAFELS.id, f"{H.TAFELS.id}:t2:2x3", "2 × 3 =", Decimal(6), data={})
        with mock.patch.object(Snelrekenen, "klok", side_effect=lambda: next(tikken)), \
                mock.patch.object(SR, "vraag", return_value=(H.TAFELS, vast)):
            scherm, app = self.speel([*naar(H.TAFELS, "t", niveau=None), ("wacht",), "6", OK, ("wacht",),
                                      *[("wacht",)] * 12, OK, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Nog "))
        self.assertTrue(self.ergens(scherm, "Juist: 1 van 1"))

    def test_snelrekenen_esc_vraagt_eerst(self):
        """#33: Esc tijdens een ronde: eerst "Wil je stoppen met deze ronde?" (Nee = verder, ← + Enter = stoppen)."""
        o = self.opslag(("Test", "5"))
        vast = Vraag(H.TAFELS.id, f"{H.TAFELS.id}:t2:2x3", "2 × 3 =", Decimal(6), data={})
        with mock.patch.object(SR, "vraag", return_value=(H.TAFELS, vast)):
            scherm, app = self.speel([*naar(H.TAFELS, "z", niveau=None), "6", OK, ESC, OK, "6", OK,
                                      ESC, curses.KEY_LEFT, OK, OK, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Wil je stoppen met deze ronde?"))
        self.assertTrue(self.ergens(scherm, "De klok staat stil tot je kiest."))
        self.assertTrue(self.ergens(scherm, "Juist: 2 van 2"))

    def test_snelrekenen_kruimel_vraagt_eerst_en_toont_de_uitslag(self):
        """#33 (opnieuw): de broodkruimel tijdens een ronde vraagt eerst; na Ja eerst de uitslag, dan het menu."""
        o = self.opslag(("Test", "5"))
        vast = Vraag(H.TAFELS.id, f"{H.TAFELS.id}:t2:2x3", "2 × 3 =", Decimal(6), data={})
        with mock.patch.object(SR, "vraag", return_value=(H.TAFELS, vast)):
            scherm, app = self.speel([*naar(H.TAFELS, "z", niveau=None), "6", OK, ("klik", 0, 17),
                                      curses.KEY_LEFT, OK, OK], opslag=o)
        self.assertTrue(self.ergens(scherm, "Wil je stoppen met deze ronde?"))
        uitslag = next(i for i, b in enumerate(scherm.beelden) if "Juist: 1 van 1" in b)
        self.assertTrue(any("Welk onderwerp?" in b for b in scherm.beelden[uitslag:]))

    def test_zonder_timer_alleen_20_sommen(self):
        o = self.opslag(("Test", "5", {"timer_zichtbaar": False}))
        # op Tafels doet T niets en staat er geen [T] 60 s; Gemengd start met Enter 20 sommen
        scherm, _ = self.speel([*naar(H.TAFELS, "t", niveau=None), ESC, ESC, ESC], opslag=o)
        self.assertFalse(self.ergens(scherm, "[T]"))
        self.assertFalse(self.ergens(scherm, "60 seconden"))
        scherm, _ = self.speel([*naar("wiskunde.hoofdrekenen.gemengd", "Enter", niveau=None),
                                ESC, curses.KEY_LEFT, OK, ESC, ESC], opslag=o)  # Esc + ← + Enter = stoppen (#33)
        self.assertTrue(self.ergens(scherm, "[Enter] 20 sommen"))
        self.assertTrue(self.ergens(scherm, "Som 1 van 20"))

    def test_herhalen_tafel(self):
        o = self.opslag(("Test", "5"))
        kind = o.kinderen()[0]
        o.herhaal_zet(kind.id, H.TAFELS.id, "tafel 7", {"onderwerp": "tafel 7", "tafel": 7}, 1, "2000-01-01")
        vast = Vraag(H.TAFELS.id, "k", "7 × 3 =", Decimal(21), data={"a": 7, "b": 3, "delen": False,
                                                                     "veelvoud": False, "tafel": 7})
        with mock.patch.object(H.TAFELS, "maak_herhaling", return_value=vast):
            scherm, _ = self.speel([OK, OK, hm("Herhalen"), *"21", OK, OK, OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Je herhaalde 1 vraag: 1 juist."))
        self.assertEqual(o.herhaalbak(kind.id)[0]["bak"], 2)
        self.assertEqual(len(herhaling.aan_de_beurt(o, kind.id)), 0)


if __name__ == "__main__":
    unittest.main()
