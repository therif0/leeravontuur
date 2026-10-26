import csv
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from leeravontuur.kern import klok, rapporten, wachtwoord
from leeravontuur.kern.opslag import Opslag
from leeravontuur.terminal import curriculum

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


class TestIndeling(unittest.TestCase):
    """Het rapport per vak › domein › onderwerp (uit het leerplan); snelrekenen apart onder zijn onderwerp."""
    T, PM, DH, E = ("wiskunde.hoofdrekenen.tafels", "wiskunde.hoofdrekenen.plusmin", "wiskunde.hoofdrekenen.dubbelhelft",
                    "wiskunde.eenheden.omzetten")

    def setUp(self):
        self.o = Opslag()
        self.kind = self.o.nieuw_kind("Imrane", "5")
        klok.zet(datetime(2026, 10, 20, 15, 0, tzinfo=CET))
        # (sessie: modus, vaardigheid) -> antwoorden (vaardigheid van de vraag, juist)
        for modus, sessie, antwoorden in [
                ("reeks", self.T, [(self.T, 1), (self.T, 1), (self.T, 0)]),
                ("snel60", "snelrekenen.tafels", [(self.T, 1)] * 4),
                ("snel20", "snelrekenen.gemengd", [(self.T, 1), (self.PM, 0), (self.DH, 1)]),
                ("vrij", self.PM, [(self.PM, 1), (self.PM, 0)]),
                ("reeks", self.E, [(self.E, 1), (self.E, 0)])]:
            s = self.o.start_sessie(self.kind.id, modus, sessie, "5")
            for i, (v, juist) in enumerate(antwoorden):
                self.o.bewaar_antwoord(s, self.kind.id, v, "5", modus, f"{sessie}{i}", f"vraag {i}", "1", juist,
                                       None if juist else "fout_x", 2000, verwacht="2")
        klok.zet(None)
        self.r = rapporten.maak_rapport(self.o, self.kind, rapporten.Periode(date(2026, 10, 1), date(2026, 10, 31), "m"))

    def deel(self, regels, kop):
        """De regels van één deel (tot de volgende kop: een regel die niet inspringt)."""
        tekst = [t for t, _ in regels]
        i = tekst.index(kop)
        j = next((k for k in range(i + 1, len(tekst)) if tekst[k] and not tekst[k].startswith(" ")), len(tekst))
        return tekst[i:j]

    def test_zelfde_cijfers(self):
        plat, ingedeeld = rapporten.regels(self.r), rapporten.regels(self.r, curriculum.indeling())
        voor = [t for t, _ in plat][:[t for t, _ in plat].index("PER ONDERWERP")]
        self.assertEqual(voor, [t for t, _ in ingedeeld][:len(voor)])  # samenvatting en per dag
        self.assertIn("  Vragen: 14    Juist: 10 (71 %)", voor)
        for kop in ("MEEST GEMAAKTE DENKFOUTEN", "LAATSTE FOUTEN"):
            self.assertEqual(self.deel(plat, kop), self.deel(ingedeeld, kop))
        # per onderwerp samen = alle antwoorden; vroeger per vaardigheid van de vraag, nu per bron
        self.assertEqual(sum(pv["aantal"] for pv in self.r.per_vaardigheid.values()), 14)
        self.assertEqual({b: pv["aantal"] for b, pv in self.r.per_vaardigheid.items()},
                         {self.T: 3, "snelrekenen.tafels": 4, "snelrekenen.gemengd": 3, self.PM: 2, self.E: 2})

    def test_snelrekenen_apart_onder_zijn_onderwerp(self):
        tekst = self.deel(rapporten.regels(self.r, curriculum.indeling()), "PER ONDERWERP")
        self.assertEqual(tekst[1], "  Wiskunde › Hoofdrekenen")
        i = tekst.index("    Tafels: 3 vragen, 67 % juist, gemiddeld 2 s")
        self.assertEqual(tekst[i + 1], "      reeks van 10 3")
        self.assertEqual(tekst[i + 2], "    Tafels, snelrekenen: 4 sommen, 100 % juist, gemiddeld 2 s")
        self.assertEqual(tekst[i + 3], "      60 seconden 4")
        self.assertIn("    Gemengd, snelrekenen: 3 sommen, 67 % juist, gemiddeld 2 s", tekst)
        self.assertIn("    Optellen en aftrekken: 2 vragen, 50 % juist, gemiddeld 2 s", tekst)
        self.assertFalse(any("Verdubbelen" in t for t in tekst))  # zijn som hoort bij Gemengd
        self.assertLess(tekst.index("  Wiskunde › Hoofdrekenen"), tekst.index("  Wiskunde › Meten"))
        self.assertIn("    Maten: 2 vragen, 50 % juist, gemiddeld 2 s", tekst)
        status = self.deel(rapporten.regels(self.r, curriculum.indeling()), "STATUS PER VAARDIGHEID (alle tijd)")
        self.assertIn("  Wiskunde › Getallen", status)
        self.assertTrue(any(t.startswith("    Tafels: ") for t in status))

    def test_per_onderwerp_past_in_de_lezer(self):
        """PER ONDERWERP: elke regel past in de lezer (72 tekens), ook met de langste namen en grote getallen."""
        from collections import Counter
        r = rapporten.Rapport(self.kind, self.r.periode, [], aantal=999, juist=999, tijd_ms=999 * 99000,
                              per_dag={"2026-10-20": [999, 999]})
        for bron in curriculum.indeling():
            modi = Counter({"snel60": 500, "snel20": 499} if bron.startswith("snelrekenen.") else
                           {"reeks": 500, "vrij": 300, "tabel": 199})
            r.per_vaardigheid[bron] = {"aantal": 999, "juist": 999, "tijd_ms": 999 * 99000, "modi": modi}
        regels = [t for t, _ in rapporten.regels(r, curriculum.indeling())]
        for tekst in regels:
            self.assertLessEqual(len(tekst), 72, tekst)
        self.assertIn("    Optellen en aftrekken, snelrekenen: 999 sommen, 100 % juist", regels)
        self.assertEqual(sum("gemiddeld 99 s" in t for t in regels), len(r.per_vaardigheid))  # nooit weggevallen

    def test_export_zelfde_kolommen_plus_vak_en_domein(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_pad, txt_pad = rapporten.exporteer(self.r, tmp, curriculum.indeling())
            with open(csv_pad, encoding="utf-8-sig", newline="") as f:
                rijen = list(csv.reader(f, delimiter=";"))
            self.assertIn("Wiskunde › Hoofdrekenen", txt_pad.read_text(encoding="utf-8"))
        self.assertEqual(rijen[0], ["tijdstip", "onderwerp", "leerjaar", "manier", "vraag", "antwoord",
                                    "juist antwoord", "juist", "denkfout", "tijd (s)", "tip gebruikt", "vak", "domein"])
        # een som uit snelrekenen Gemengd (plus en min): de oude kolommen zoals vroeger, dan vak en domein
        rij = next(r for r in rijen[1:] if r[3] == "snel20" and r[1] == "Optellen en aftrekken")
        self.assertEqual(rij[2:], ["5de leerjaar", "snel20", "vraag 1", "1", "2", "nee", "fout_x", "2,0", "nee",
                                   "Wiskunde", "Hoofdrekenen"])
        rij = next(r for r in rijen[1:] if r[1] == "Eenheden omzetten")
        self.assertEqual(rij[-2:], ["Wiskunde", "Meten"])
        self.assertEqual(len(rijen), 1 + 14)


if __name__ == "__main__":
    unittest.main()
