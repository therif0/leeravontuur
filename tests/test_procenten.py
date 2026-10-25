import curses
import random
import unittest
from decimal import Decimal
from fractions import Fraction
from unittest import mock

from leeravontuur.kern import leerjaren
from leeravontuur.kern.getal import lees_breuk
from leeravontuur.kern.modellen import Honderdveld, Procentstrook
from leeravontuur.kern.onderwerp import Vraag
from leeravontuur.kern.wiskunde import procenten as P

try:
    from .test_schermen import ESC, OK, Basis, hm
except ImportError:
    from test_schermen import ESC, OK, Basis, hm

D = Decimal
F = Fraction
RECHTS, NEER = curses.KEY_RIGHT, curses.KEY_DOWN


class TestGeneratoren(unittest.TestCase):
    def test_alle_leerjaren(self):
        rng = random.Random(8)
        for o in P.ALLE:
            for jaar in leerjaren.LEERJAREN:
                if not o.aangeboden(jaar):
                    continue
                for _ in range(300):
                    v = o.maak(jaar, rng=rng)
                    self.assertTrue(v.sleutel.startswith(o.id + ":"))
                    self.assertIsNotNone(o.onderwerp_van_sleutel(v.sleutel))
                    self.assertTrue(o.uitleg(v))
                    o.tip(v)
                    if v.invoer != "veld":
                        self.assertTrue(o.nakijken(v, o.lees_vraag(v, v.verwacht)), (v.tekst, v.verwacht))
                    self.controleer(o, v)

    def controleer(self, o, v):
        d = v.data
        s = d["soort"]
        if o is P.VELD:
            self.assertEqual(v.antwoord, d["pct"])
            if s == "aflezen":
                self.assertEqual(len(v.model.gekleurd), d["pct"])
            if s == "kleuren_breuk":
                self.assertEqual(F(d["pct"], 100), F(d["t"], d["n"]))
        elif o is P.OMZETTEN:
            pct = D(d["pct"])
            self.assertEqual(F(pct) / 100, F(d["t"], d["n"]))
        elif o is P.PROCENT_VAN:
            deel = D(d["totaal"]) * d["pct"] / 100
            self.assertEqual(deel, deel.to_integral_value())  # mooie getallen
            self.assertEqual(v.antwoord, d["pct"] if s == "welk_procent" else deel)
        elif o is P.KORTING:
            if s == "korting":
                self.assertEqual(v.antwoord, D(d["prijs"]) * (100 - d["pct"]) / 100)
            elif s == "btw":
                self.assertEqual(v.antwoord, D(d["prijs"]) * (100 + d["pct"]) / 100)
            else:
                self.assertEqual(abs(D(d["nieuw"]) - d["oud"]) * 100 / d["oud"], v.antwoord)

    def test_niveaus(self):
        self.assertFalse(P.VELD.aangeboden("4"))
        self.assertTrue(P.VELD.aangeboden("5"))
        self.assertFalse(P.KORTING.aangeboden("5"))
        self.assertTrue(P.KORTING.aangeboden("6"))

    def test_geld(self):
        self.assertEqual(P.geld(D("8.4")), "8,40")
        self.assertEqual(P.geld(D(53)), "53")


class TestDiagnose(unittest.TestCase):
    def test_procent_van(self):
        v = Vraag(P.PROCENT_VAN.id, "k", "20 % van 80 =", D(16), data={"soort": "van", "pct": 20, "totaal": 80})
        self.assertEqual(P.PROCENT_VAN.diagnose(v, D(20))[0], "procent_als_antwoord")
        self.assertEqual(P.PROCENT_VAN.diagnose(v, D(4))[0], "gedeeld_door_procent")
        self.assertEqual(P.PROCENT_VAN.diagnose(v, D(64))[0], "rest_berekend")
        self.assertIn("10 % = 80 : 10 = 8, dus 20 % = 2 × 8 = 16", P.PROCENT_VAN.uitleg(v)[0])

    def test_korting_en_btw(self):
        v = Vraag(P.KORTING.id, "k", "", D(180), data={"soort": "korting", "pct": 25, "prijs": 240})
        self.assertEqual(P.KORTING.diagnose(v, D(60))[0], "alleen_korting")
        self.assertEqual(P.KORTING.diagnose(v, D(300))[0], "korting_opgeteld")
        w = Vraag(P.KORTING.id, "k", "", D("48.4"), data={"soort": "btw", "pct": 21, "prijs": 40})
        self.assertEqual(P.KORTING.diagnose(w, D(40))[0], "btw_vergeten")
        self.assertIn("€ 8,40 btw", " ".join(P.KORTING.uitleg(w)))
        z = Vraag(P.KORTING.id, "k", "", D(25), data={"soort": "stijging", "pct": 25, "oud": 40, "nieuw": "50"})
        self.assertEqual(P.KORTING.diagnose(z, D(20))[0], "verkeerd_grondgetal")

    def test_veld_en_omzetten(self):
        v = Vraag(P.VELD.id, "k", "", D(35), data={"soort": "aflezen", "pct": 35})
        self.assertEqual(P.VELD.diagnose(v, D(65))[0], "wit_geteld")
        self.assertEqual(P.VELD.diagnose(v, D("0.35"))[0], "kommagetal_ipv_procent")
        self.assertEqual(P.VELD.lees("35 %"), 35)
        self.assertEqual(P.KORTING.lees("€ 12,50"), D("12.5"))
        w = Vraag(P.OMZETTEN.id, "k", "", D(40), data={"soort": "komma_naar_procent", "t": 2, "n": 5, "pct": "40"})
        self.assertEqual(P.OMZETTEN.diagnose(w, D("0.4"))[0], "komma_procent")
        b = Vraag(P.OMZETTEN.id, "k", "", F(1, 4), invoer="breuk",
                  data={"soort": "procent_naar_breuk", "t": 1, "n": 4, "pct": "25", "vereenvoudigd": True})
        self.assertFalse(P.OMZETTEN.nakijken(b, lees_breuk("25/100")))
        self.assertEqual(P.OMZETTEN.diagnose(b, lees_breuk("25/100"))[0], "niet_vereenvoudigd")


def kleur_vraag():
    return Vraag(P.VELD.id, f"{P.VELD.id}:kleuren:35", "Kleur 35 % van het honderdveld.", D(35), invoer="veld",
                 model=Honderdveld(), data={"soort": "kleuren", "pct": 35, "onderwerp": "kleuren"},
                 verwacht_tekst="35 vakjes")


def naar(onderwerp):
    """Wiskunde → Procenten → onderwerp → Vrij oefenen → Normaal."""
    return [OK, OK, hm("Leren & oefenen"), "1", "6", str(onderwerp), "1", OK]


STOP = [ESC] * 7


class TestSchermen(Basis):
    def test_honderdveld_kleuren(self):
        o = self.opslag(("Test", "5"))
        # 3 volle rijen (r), dan 3 vakjes met spatie en 2 met een klik → 35
        toetsen = ["r", NEER, "r", NEER, "r", NEER, " ", RECHTS, " ", RECHTS, " ", ("klik", 12, 16), ("klik", 12, 18)]
        with mock.patch.object(P.VELD, "maak", side_effect=[kleur_vraag(), kleur_vraag()]):
            scherm, app = self.speel([*naar(1), *toetsen, OK, *STOP], opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertEqual(rij["gegeven"], "35 %")
        self.assertTrue(rij["juist"])
        self.assertTrue(self.ergens(scherm, "35 van de 100"))

    def test_rij_met_klik_en_weer_leeg(self):
        o = self.opslag(("Test", "5"))
        toetsen = [("klik", 9, 8), ("klik", 10, 8), ("klik", 10, 8)]  # rij 1 vol, rij 2 vol en weer leeg
        with mock.patch.object(P.VELD, "maak", side_effect=[kleur_vraag(), kleur_vraag()]):
            scherm, app = self.speel([*naar(1), *toetsen, OK, *STOP], opslag=o)
        self.assertEqual(o.antwoorden(app.kind.id)[0]["gegeven"], "10 %")

    def test_procent_van_met_strook(self):
        o = self.opslag(("Test", "5"))
        v = Vraag(P.PROCENT_VAN.id, f"{P.PROCENT_VAN.id}:van:20:80", "20 % van 80 =", D(16),
                  data={"soort": "van", "pct": 20, "totaal": 80, "onderwerp": "van"},
                  model=Procentstrook(D(80), D(20)), model_na=Procentstrook(D(80), D(20), toon_deel=True))
        with mock.patch.object(P.PROCENT_VAN, "maak", side_effect=[v, v]):
            scherm, app = self.speel([*naar(3), *"20", OK, *STOP], opslag=o)
        rij = o.antwoorden(app.kind.id)[0]
        self.assertEqual(rij["diagnose"], "procent_als_antwoord")
        self.assertTrue(self.ergens(scherm, "▼ 20 %"))
        self.assertTrue(self.ergens(scherm, "100 %"))

    def test_spiekbrief(self):
        scherm, _ = self.speel([OK, OK, hm("Spiekbrieven"), "6", ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "PROCENT = PER HONDERD"))


if __name__ == "__main__":
    unittest.main()
