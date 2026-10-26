import csv
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from leeravontuur.kern import klok, rapporten, wachtwoord
from leeravontuur.kern.opslag import Opslag

CET = timezone(timedelta(hours=1))


class TestWachtwoord(unittest.TestCase):
    def test_maken_en_controleren(self):
        h = wachtwoord.maak("geheim", iteraties=1000)
        self.assertTrue(h.startswith("pbkdf2_sha256$1000$"))
        self.assertTrue(wachtwoord.controleer("geheim", h))
        self.assertFalse(wachtwoord.controleer("Geheim", h))
        self.assertNotEqual(h, wachtwoord.maak("geheim", iteraties=1000))  # andere salt
        self.assertTrue(wachtwoord.verouderd(h))  # minder iteraties dan nu de standaard
        self.assertFalse(wachtwoord.controleer("x", "onzin"))
        self.assertTrue(wachtwoord.verouderd("onzin"))


class TestDatums(unittest.TestCase):
    def test_lees_datum(self):
        v = date(2026, 10, 24)
        self.assertEqual(rapporten.lees_datum("24/10/2026"), date(2026, 10, 24))
        self.assertEqual(rapporten.lees_datum("1-9-26"), date(2026, 9, 1))
        self.assertEqual(rapporten.lees_datum("3/10", v), date(2026, 10, 3))
        self.assertEqual(rapporten.lees_datum("2026-10-05"), date(2026, 10, 5))
        self.assertIsNone(rapporten.lees_datum("31/02/2026"))
        self.assertIsNone(rapporten.lees_datum("morgen"))

    def test_periodes(self):
        p = {x.naam: x for x in rapporten.periodes(date(2026, 10, 24))}  # een zaterdag
        self.assertEqual(p["deze week"].van, date(2026, 10, 19))
        self.assertEqual(p["deze maand"].van, date(2026, 10, 1))
        self.assertEqual(p["dit schooljaar"].van, date(2026, 9, 1))
        self.assertEqual(rapporten.periodes(date(2027, 2, 3))[4].van, date(2026, 9, 1))


class TestRapport(unittest.TestCase):
    def setUp(self):
        self.o = Opslag()
        self.kind = self.o.nieuw_kind("Imrane", "5")
        s = self.o.start_sessie(self.kind.id, "reeks", "wiskunde.eenheden.omzetten", "5")
        for dag, juist, diagnose in [(20, True, None), (20, False, "verkeerde_richting"), (22, True, None),
                                     (22, False, "verkeerde_richting"), (22, False, "factor_10"), (30, True, None)]:
            klok.zet(datetime(2026, 10, dag, 15, 0, tzinfo=CET))
            self.o.bewaar_antwoord(s, self.kind.id, "wiskunde.eenheden.omzetten", "5", "reeks", f"k{dag}",
                                   "1 m = ? cm", "100" if juist else "0,01", juist, diagnose, 4000,
                                   verwacht="100 cm")
        klok.zet(None)
        self.assertIsNone(self.o.probleem)

    def test_cijfers(self):
        r = rapporten.maak_rapport(self.o, self.kind, rapporten.Periode(date(2026, 10, 19), date(2026, 10, 25), "week"))
        self.assertEqual((r.aantal, r.juist, r.procent), (5, 2, 40))
        self.assertEqual(r.per_dag, {"2026-10-20": [2, 1], "2026-10-22": [3, 1]})
        self.assertEqual(r.denkfouten.most_common(1)[0], ("verkeerde_richting", 2))
        tekst = "\n".join(t for t, _ in rapporten.regels(r))
        self.assertIn("Vragen: 5    Juist: 2 (40 %)", tekst)
        self.assertIn("2× de komma de verkeerde kant op geschoven", tekst)
        self.assertIn("Eenheden omzetten: 5 vragen", tekst)
        self.assertIn("(juist: 100 cm)", tekst)

    def test_vraagstukken(self):
        s = self.o.start_sessie(self.kind.id, "vrij", "wiskunde.vraagstukken.oplossen", "5")
        klok.zet(datetime(2026, 10, 21, 15, 0, tzinfo=CET))
        for juist, extra, d in [(True, {"vraagstuk": 1, "tips": 0, "eerste_fout": None, "klad": [], "klad_ok": False}, None),
                                (True, {"vraagstuk": 1, "tips": 2, "eerste_fout": "24", "klad": ["3 x 8 = 24"],
                                        "klad_ok": True}, None),
                                (False, {"vraagstuk": 1, "tips": 1, "eerste_fout": "5", "klad": ["750 x 3 = 2250"],
                                         "klad_ok": False, "klad_fout": "vs_omzetten"}, "vs_tussenstap")]:
            self.o.bewaar_antwoord(s, self.kind.id, "wiskunde.vraagstukken.oplossen", "5", "vrij", "v", "verhaal",
                                   "1", juist, d, 30000, bool(extra["tips"]), extra, "€ 2")
        klok.zet(None)
        r = rapporten.maak_rapport(self.o, self.kind, rapporten.Periode(date(2026, 10, 21), date(2026, 10, 21), "x"))
        tekst = "\n".join(t for t, _ in rapporten.regels(r))
        self.assertIn("gemiddeld 1 tips per vraagstuk · juist zonder tip: 1 · meteen juist: 1 · met klad: 2 "
                      "(helemaal juist: 1)", tekst)
        self.assertIn("1× niet (goed) omgezet naar de juiste eenheid", tekst)
        self.assertIn("1× gestopt na een tussenstap", tekst)

    def test_leeg(self):
        r = rapporten.maak_rapport(self.o, self.kind, rapporten.Periode(date(2026, 1, 1), date(2026, 1, 2), "x"))
        self.assertTrue(any("nog niet geoefend" in t for t, _ in rapporten.regels(r)))
        self.assertTrue(any("Eenheden omzetten: bezig" in t for t, _ in rapporten.regels(r)))

    def test_kalender(self):
        dagen = rapporten.kalender(self.o, self.kind.id, 2026, 10)
        self.assertEqual(dagen, {20: [2, 1], 22: [3, 1], 30: [1, 1]})
        regels = rapporten.kalender_regels(2026, 10, dagen)
        self.assertEqual(regels[0][0], "Oktober 2026")
        self.assertTrue(any(kleur for _, kleur in regels))

    def test_export(self):
        r = rapporten.maak_rapport(self.o, self.kind, rapporten.Periode(date(2026, 10, 1), date(2026, 10, 31), "maand"))
        with tempfile.TemporaryDirectory() as tmp:
            csv_pad, txt_pad = rapporten.exporteer(r, Path(tmp) / "sub")
            self.assertTrue(csv_pad.read_bytes().startswith(b"\xef\xbb\xbf"))  # BOM voor Excel
            with open(csv_pad, encoding="utf-8-sig", newline="") as f:
                rijen = list(csv.reader(f, delimiter=";"))
            self.assertEqual(len(rijen), 1 + 6)
            self.assertEqual(rijen[1][6], "100 cm")
            self.assertEqual(rijen[1][9], "4,0")
            self.assertIn("Rapport van Imrane", txt_pad.read_text(encoding="utf-8"))
            json_pad = rapporten.exporteer_alles(self.o, self.kind, tmp)
            self.assertIn('"antwoorden"', json_pad.read_text(encoding="utf-8"))

    def test_wissen(self):
        self.o.zet_algemeen("laatste_kind", self.kind.id)
        self.o.verwijder_kind(self.kind.id)
        self.assertEqual(self.o.kinderen(), [])
        self.assertEqual(self.o.antwoorden(self.kind.id), [])
        self.assertIsNone(self.o.algemeen("laatste_kind"))


if __name__ == "__main__":
    unittest.main()
