import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from leeravontuur.kern import instellingen, klok
from leeravontuur.kern.instellingen import Instellingen
from leeravontuur.kern.opslag import MIGRATIES, Opslag
from leeravontuur.kern.sessie import Sessie

CET = timezone(timedelta(hours=1))


class TestSchema(unittest.TestCase):
    def test_migraties(self):
        with tempfile.TemporaryDirectory() as tmp:
            pad = Path(tmp) / "test.db"
            o = Opslag(pad)
            self.assertEqual(o.versie, len(MIGRATIES))
            kind = o.nieuw_kind("Imrane", "5")
            o.sluit()
            o2 = Opslag(pad)  # opnieuw openen verandert niets
            self.assertEqual(o2.versie, len(MIGRATIES))
            self.assertEqual(o2.kinderen(), [kind])
            o2.sluit()


class TestKinderen(unittest.TestCase):
    def setUp(self):
        self.o = Opslag()

    def test_nieuw_kind_en_instellingen(self):
        a = self.o.nieuw_kind("Imrane", "5")
        b = self.o.nieuw_kind("Amira", "3")
        self.assertNotEqual(a.id, b.id)
        self.assertEqual([k.naam for k in self.o.kinderen()], ["Amira", "Imrane"])  # op naam
        inst = self.o.instellingen_van(a.id)
        self.assertEqual((inst.naam, inst.leerjaar, inst.thema), ("Imrane", "5", "standaard"))
        inst.thema, inst.muis, inst.leerjaar = "rood-groen", False, "6"
        self.o.bewaar_instellingen(a.id, inst)
        terug = self.o.instellingen_van(a.id)
        self.assertEqual((terug.thema, terug.muis, terug.leerjaar), ("rood-groen", False, "6"))
        self.assertEqual(self.o.kind(a.id).leerjaar, "6")
        self.assertEqual(self.o.instellingen_van(b.id).thema, "standaard")  # het andere kind niet

    def test_algemeen(self):
        self.assertIsNone(self.o.algemeen("laatste_kind"))
        self.o.zet_algemeen("laatste_kind", "abc")
        self.o.zet_algemeen("laatste_kind", "def")
        self.assertEqual(self.o.algemeen("laatste_kind"), "def")


class TestAntwoorden(unittest.TestCase):
    def setUp(self):
        self.o = Opslag()
        self.kind = self.o.nieuw_kind("Imrane", "5")

    def tearDown(self):
        klok.zet(None)

    def bewaar(self, juist):
        s = self.o.start_sessie(self.kind.id, "reeks", "wiskunde.eenheden.omzetten", "5")
        self.o.bewaar_antwoord(s, self.kind.id, "wiskunde.eenheden.omzetten", "5", "reeks",
                               "sleutel", "1 m = ? cm", "100", juist, tijd_ms=1200)

    def test_telling_per_dag(self):
        klok.zet(datetime(2026, 10, 23, 20, 0, tzinfo=CET))
        self.bewaar(True)
        klok.zet(datetime(2026, 10, 24, 9, 0, tzinfo=CET))
        self.bewaar(True)
        self.bewaar(False)
        self.assertEqual(self.o.telling(self.kind.id, "2026-10-24"), (2, 1))
        self.assertEqual(self.o.telling(self.kind.id, "2026-10-23"), (1, 1))
        self.assertEqual(self.o.telling(self.kind.id, "2026-10-01", "2026-10-31"), (3, 2))

    def test_alleen_toevoegen(self):
        self.bewaar(True)
        with self.assertRaises(sqlite3.Error):
            self.o.con.execute("UPDATE antwoorden SET juist = 0")

    def test_onbekend_kind_geweigerd(self):
        s = self.o.start_sessie(self.kind.id, "reeks", "x", "5")
        with self.assertRaises(sqlite3.IntegrityError):
            self.o.bewaar_antwoord(s, "bestaat-niet", "x", "5", "reeks", "k", "v", "g", True)

    def test_sessie(self):
        with Sessie(self.o, self.kind.id, "vrij", "wiskunde.eenheden.omzetten", "5") as ses:
            ses.vraag_getoond()
            ses.antwoord("k1", "1 m = ? cm", "100", True, extra={"komma_ok": True})
            ses.vraag_getoond()
            ses.antwoord("k2", "1 cm = ? m", "100", False, diagnose="verkeerde_richting", hulp=True)
        rijen = self.o.antwoorden(self.kind.id)
        self.assertEqual(len(rijen), 2)
        self.assertGreaterEqual(rijen[0]["tijd_ms"], 0)
        self.assertEqual(json.loads(rijen[0]["extra"]), {"komma_ok": True})
        self.assertEqual((rijen[1]["diagnose"], rijen[1]["hulp"], rijen[1]["juist"]), ("verkeerde_richting", 1, 0))
        self.assertIsNotNone(self.o.sessies(self.kind.id)[0]["einde"])


class TestOpenen(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.oud = os.environ.get("LEERAVONTUUR_DATA")
        os.environ["LEERAVONTUUR_DATA"] = self.tmp.name

    def tearDown(self):
        if self.oud is None:
            os.environ.pop("LEERAVONTUUR_DATA", None)
        else:
            os.environ["LEERAVONTUUR_DATA"] = self.oud
        self.tmp.cleanup()

    def test_overzetten_uit_fase_1(self):
        json_pad = instellingen.pad()
        json_pad.write_text(json.dumps({"naam": "Imrane", "leerjaar": "5", "thema": "contrast",
                                        "typrichting": -1}), encoding="utf-8")
        o = Opslag.open()
        kinderen = o.kinderen()
        self.assertEqual([k.naam for k in kinderen], ["Imrane"])
        inst = o.instellingen_van(kinderen[0].id)
        self.assertEqual((inst.thema, inst.typrichting), ("contrast", -1))
        self.assertEqual(o.algemeen("laatste_kind"), kinderen[0].id)
        self.assertFalse(json_pad.exists())
        self.assertTrue(json_pad.with_name("instellingen.json.oud").exists())
        o.sluit()
        o2 = Opslag.open()  # niet nog eens overzetten
        self.assertEqual(len(o2.kinderen()), 1)
        o2.sluit()

    @unittest.skipIf(sys.platform == "win32", "bestandsrechten werken anders op Windows")
    def test_terugval_naar_geheugen(self):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("als root kan je overal schrijven")
        map_ = Path(self.tmp.name) / "alleen-lezen"
        map_.mkdir()
        map_.chmod(0o500)
        try:
            o = Opslag.open(map_ / "sub" / "leeravontuur.db")
            self.assertIsNotNone(o.probleem)
            kind = o.nieuw_kind("Test", "5")  # werkt gewoon, maar in het geheugen
            self.assertEqual(o.kinderen(), [kind])
        finally:
            map_.chmod(0o700)

    def test_onbruikbaar_bestand_gaat_opzij(self):
        pad = Path(self.tmp.name) / "kapot.db"
        pad.write_text("dit is geen databank", encoding="utf-8")
        o = Opslag.open(pad)
        self.assertIn("geen reservekopie", o.probleem)
        self.assertEqual(o.pad, str(pad))  # een nieuwe databank, die wel bewaart
        self.assertEqual(len(list(Path(self.tmp.name).glob("kapot.db.beschadigd-*"))), 1)
        o.sluit()


if __name__ == "__main__":
    unittest.main()
