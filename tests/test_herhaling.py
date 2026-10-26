import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest import mock

from leeravontuur.kern import herhaling, klok, selectie
from leeravontuur.kern.opslag import Opslag
from leeravontuur.kern.wiskunde import eenheden as E

try:
    from .test_schermen import ESC, OK, Basis, hm, naar
except ImportError:
    from test_schermen import ESC, OK, Basis, hm, naar

CET = timezone(timedelta(hours=1))
DAG = datetime(2026, 10, 24, 15, 0, tzinfo=CET)
ID = E.OMZETTEN.id


class TestHerhaalbak(unittest.TestCase):
    def setUp(self):
        self.o = Opslag()
        self.kind = self.o.nieuw_kind("Imrane", "5")
        klok.zet(DAG)

    def tearDown(self):
        klok.zet(None)

    def ga_naar(self, dagen):
        klok.zet(DAG + timedelta(days=dagen))

    def test_leitner(self):
        herhaling.fout(self.o, self.kind.id, ID, "km>m", {"van": "km", "naar": "m"})
        self.assertEqual(herhaling.aan_de_beurt(self.o, self.kind.id), [])  # pas morgen
        self.ga_naar(1)
        [item] = herhaling.aan_de_beurt(self.o, self.kind.id)
        self.assertEqual(item["bak"], 1)
        self.assertFalse(herhaling.juist(self.o, item))  # bak 2, over 3 dagen
        self.ga_naar(3)
        self.assertEqual(herhaling.aan_de_beurt(self.o, self.kind.id), [])
        self.ga_naar(4)
        [item] = herhaling.aan_de_beurt(self.o, self.kind.id)
        self.assertEqual(item["bak"], 2)
        herhaling.juist(self.o, item)  # bak 3, over 7 dagen
        self.ga_naar(11)
        [item] = herhaling.aan_de_beurt(self.o, self.kind.id)
        self.assertTrue(herhaling.juist(self.o, item))  # na de laatste bak: beheerst
        self.assertEqual(self.o.herhaalbak(self.kind.id), [])

    def test_fout_begint_opnieuw(self):
        herhaling.fout(self.o, self.kind.id, ID, "km>m", {})
        self.ga_naar(1)
        herhaling.juist(self.o, herhaling.aan_de_beurt(self.o, self.kind.id)[0])
        herhaling.fout(self.o, self.kind.id, ID, "km>m", {})  # nog eens fout
        [item] = self.o.herhaalbak(self.kind.id)
        self.assertEqual(item["bak"], 1)
        self.assertEqual(len(self.o.herhaalbak(self.kind.id)), 1)  # geen dubbel

    def test_status(self):
        self.assertEqual(herhaling.status([]), herhaling.NIET_GEZIEN)
        self.assertEqual(herhaling.status([{"juist": 1}] * 5), herhaling.BEZIG)
        self.assertEqual(herhaling.status([{"juist": 1}] * 10 + [{"juist": 0}] * 2), herhaling.BEHEERST)  # 83 %
        self.assertEqual(herhaling.status([{"juist": 1}] * 9 + [{"juist": 0}] * 3), herhaling.BEZIG)  # 75 %
        self.assertEqual(herhaling.status([{"juist": 0}] * 6 + [{"juist": 1}] * 14), herhaling.BEZIG)


class TestSelectie(unittest.TestCase):
    def test_gewichten(self):
        antw = [{"sleutel": f"{ID}:km>m:1", "juist": 0}] * 3 + [{"sleutel": f"{ID}:m>cm:1", "juist": 1}] * 3
        w = selectie.gewichten(antw, E.onderwerp_van_sleutel, ["km>m", "m>cm", "g>kg"])
        self.assertEqual(w["km>m"], 4.0)
        self.assertEqual(w["m>cm"], 1.0)
        self.assertEqual(w["g>kg"], 1.5)

    def test_vermijden(self):
        vermijd = set()
        for _ in range(60):
            v = E.maak_vraag(E.EENHEDEN[E.LENGTE], "6", vermijd=vermijd)
            self.assertNotIn(v.sleutel, vermijd)
            vermijd.add(v.sleutel)

    def test_paar_en_gewichten(self):
        for _ in range(30):
            v = E.maak_vraag(E.EENHEDEN[E.LENGTE], "5", paar=("km", "m"))
            self.assertEqual((v.van, v.naar), ("km", "m"))
        veel = [E.maak_vraag(["m", "cm"], "5", gewichten={"m>cm": 50.0, "cm>m": 1.0}) for _ in range(200)]
        self.assertGreater(sum(v.van == "m" for v in veel), 150)

    def test_onderwerp_van_sleutel(self):
        v = E.Omzetting(E.LENGTE, "km", "m", Decimal("3.5"))
        self.assertEqual(E.onderwerp_van_sleutel(v.sleutel), "km>m")
        self.assertIsNone(E.onderwerp_van_sleutel("iets:anders"))


class TestSchermen(Basis):
    def test_fouten_opnieuw_na_reeks(self):
        o = self.opslag(("Test", "5"))
        reeks = ["1", OK, OK] * 10  # waarschijnlijk (bijna) alles fout
        scherm, app = self.speel([*naar("wiskunde.meten.lengte", "Enter"), *reeks, "f", *(["1", OK, OK] * 10),
                                  ESC, ESC, ESC, ESC, ESC, ESC], opslag=o)
        rijen = o.antwoorden(app.kind.id)
        fout_in_reeks = sum(1 for r in rijen if r["modus"] == "reeks" and not r["juist"])
        opnieuw = [r for r in rijen if r["modus"] == "fouten_opnieuw"]
        self.assertEqual(len(opnieuw), fout_in_reeks)
        self.assertTrue(self.ergens(scherm, "Fouten opnieuw"))
        # elke fout zit nu in de herhaalbak
        self.assertGreaterEqual(len(o.herhaalbak(app.kind.id)), 1)

    def test_herhalen_en_verder(self):
        o = self.opslag(("Test", "5"))
        kind = o.kinderen()[0]
        klok.zet(datetime.now().astimezone() - timedelta(days=1))
        herhaling.fout(o, kind.id, ID, "km>m", {"van": "km", "naar": "m", "tabel": False})
        klok.zet(None)
        vast = E.Omzetting(E.LENGTE, "km", "m", Decimal(2))
        with mock.patch.object(E, "maak_herhaling", return_value=vast):
            scherm, app = self.speel([OK, OK, hm("Herhalen"), *"2000", OK, OK, OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Herhalen (1)"))
        self.assertTrue(self.ergens(scherm, "eerst je 1 herhaalvragen"))
        self.assertTrue(self.ergens(scherm, "Je herhaalde 1 vraag: 1 juist."))
        [item] = o.herhaalbak(kind.id)
        self.assertEqual(item["bak"], 2)

    def test_verder_hervat_vorige_oefening(self):
        o = self.opslag(("Test", "5"))
        self.speel([*naar("wiskunde.meten.lengte", "Enter"), ESC, ESC, ESC, ESC, ESC], opslag=o)
        scherm, _ = self.speel([OK, OK, "1", ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "eenheden · reeks van 10 · lengte"))
        self.assertTrue(self.ergens(scherm, "Vraag 1 van 10"))


if __name__ == "__main__":
    unittest.main()
