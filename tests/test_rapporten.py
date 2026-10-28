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


class TestLogboek(unittest.TestCase):
    """#24: het logboek voor de ouder: elk antwoord met de vraag, en een vraag terug in de herhaalbak."""

    def setUp(self):
        from leeravontuur.kern.sessie import Sessie
        self.o = Opslag()
        self.kind = self.o.nieuw_kind("Imrane", "5")
        ses = Sessie(self.o, self.kind.id, "reeks", "wiskunde.hoofdrekenen.tafels", "5")
        for i, (vraag, gegeven, juist) in enumerate([("7 × 8 = ?", "54", False), ("6 × 9 = ?", "54", True)]):
            klok.zet(datetime(2026, 10, 24, 18, i, tzinfo=CET))
            ses.vraag_getoond()
            ses.antwoord(f"wiskunde.hoofdrekenen.tafels:t7:{i}", vraag, gegeven, juist,
                         "tafel_te_weinig" if not juist else None, extra={"klad": ["7 × 7 = 49", "49 + 5 = 54"]},
                         verwacht="56" if not juist else "54")
        ses.sluit()
        s = self.o.start_sessie(self.kind.id, "vrij", "wiskunde.eenheden.omzetten", "5")
        klok.zet(datetime(2026, 10, 24, 18, 5, tzinfo=CET))
        self.o.bewaar_antwoord(s, self.kind.id, "wiskunde.eenheden.omzetten", "5", "vrij",
                               "wiskunde.eenheden.omzetten:ha>m²:9,7", "9,7 ha = ? m²", "9700", False, None, 3000,
                               verwacht="97 000")
        self.o.bewaar_antwoord(s, self.kind.id, "wiskunde.meetkunde.rooster", "5", "vrij",
                               "wiskunde.meetkunde.rooster:omtrek:x", "Hoe groot is de omtrek van de figuur? ?", "1",
                               False, None, 3000)
        klok.zet(None)

    def test_vraag_kort(self):
        self.assertEqual(rapporten.vraag_kort("7 × 8 = ?", "54"), "7 × 8 = 54")
        self.assertEqual(rapporten.vraag_kort("Hoe groot is de omtrek? ?", "1"), "Hoe groot is de omtrek? → 1")
        self.assertEqual(rapporten.vraag_kort("9,7 ha = ? m²", "9700"), "9,7 ha = ? m² → 9700")

    def test_antwoorden_nieuwste_eerst(self):
        lijst = rapporten.antwoorden_lijst(self.o, self.kind.id)
        self.assertEqual([a["vraag"] for a in lijst], ["Hoe groot is de omtrek van de figuur?", "9,7 ha = ? m²",
                                                         "6 × 9 = ?", "7 × 8 = ?"])
        fout = lijst[-1]
        self.assertEqual((fout["wanneer"], fout["juist"], fout["gegeven"], fout["verwacht"]),
                         ("24/10 18:00", False, "54", "56"))
        self.assertEqual(fout["klad"], ["7 × 7 = 49", "49 + 5 = 54"])
        self.assertEqual(fout["naam"], "Maal- en deeltafels")

    def test_punten_met_de_vraag(self):
        regels = [t for t, _ in rapporten.punten_regels(self.o, self.kind.id)]
        self.assertTrue(any("juist antwoord · 6 × 9 = 54" in r for r in regels), regels)
        self.assertTrue(all(len(r) <= rapporten.LEZER for r in regels))

    def test_in_de_herhaalbak(self):
        from leeravontuur.kern import catalogus
        a = rapporten.antwoorden_lijst(self.o, self.kind.id)[-1]
        self.assertFalse(rapporten.in_herhaalbak(self.o, self.kind.id, a["vaardigheid"], a["sleutel"]))
        for a in rapporten.antwoorden_lijst(self.o, self.kind.id):
            with self.subTest(a["sleutel"]):  # (de twee tafelvragen hebben hetzelfde onderwerp: tafel 7)
                self.assertTrue(rapporten.zet_in_herhaalbak(self.o, self.kind.id, a["vaardigheid"], a["sleutel"]))
                self.assertTrue(rapporten.in_herhaalbak(self.o, self.kind.id, a["vaardigheid"], a["sleutel"]))
        bak = self.o.herhaalbak(self.kind.id)
        self.assertEqual({i["vaardigheid"] for i in bak}, {"wiskunde.hoofdrekenen.tafels",
                                                           "wiskunde.eenheden.omzetten", "wiskunde.meetkunde.rooster"})
        # en er komt echt een gelijkaardige vraag van (nooit een crash)
        from leeravontuur.kern.wiskunde import eenheden as E
        for i in bak:
            if i["vaardigheid"] == E.OMZETTEN.id:
                v = E.maak_herhaling(i["data"], "5")
                self.assertEqual((v.van, v.naar), ("ha", "m²"))
            else:
                self.assertIsNotNone(catalogus.ONDERWERPEN[i["vaardigheid"]].maak_herhaling(i["data"], "5"))


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

    def test_status_snelrekenen_apart(self):
        """De gewone status telt alleen de gewone oefeningen; snelrekenen heeft een eigen regel onder zijn onderwerp."""
        status = {v.id: (st, n, pct) for v, st, n, _, pct in self.r.status}
        self.assertEqual(status[self.T], ("bezig", 3, 67))   # vroeger 8: de 4 + 1 snelsommen telden mee
        self.assertEqual(status[self.PM], ("bezig", 2, 50))  # zonder de som uit Gemengd
        self.assertEqual(status[self.DH], ("nog niet gezien", 0, 0))  # zijn enige som was in Gemengd
        self.assertEqual({i: (st, n, pct) for i, st, n, _, pct in self.r.snelstatus},
                         {"snelrekenen.tafels": ("bezig", 4, 100), "snelrekenen.gemengd": ("bezig", 3, 67)})
        tekst = self.deel(rapporten.regels(self.r, curriculum.indeling()), "STATUS PER VAARDIGHEID (alle tijd)")
        i = tekst.index("    Tafels: bezig")
        self.assertEqual(tekst[i + 1:i + 4], ["      3 vragen · laatst 20/10/2026 · laatste 20: 67 % juist",
                                              "    Tafels, snelrekenen: bezig",
                                              "      4 sommen · laatst 20/10/2026 · laatste 20: 100 % juist"])
        self.assertIn("    Gemengd, snelrekenen: bezig", tekst)
        self.assertFalse(any("Plus en min, snelrekenen" in t or "Optellen en aftrekken, snelrekenen" in t
                             for t in tekst))  # nog geen snelronde plus en min: geen regel
        plat = self.deel(rapporten.regels(self.r), "STATUS PER VAARDIGHEID (alle tijd)")
        self.assertIn("  Snelrekenen: Tafels: bezig · 4 sommen · laatst 20/10/2026 · laatste 20: 100 % juist", plat)

    def test_status_een_snelle_ronde_verandert_de_gewone_status_niet(self):
        klok.zet(datetime(2026, 10, 21, 15, 0, tzinfo=CET))
        s = self.o.start_sessie(self.kind.id, "snel60", "snelrekenen.tafels", "5")
        for i in range(30):  # een gehaaste ronde: veel fout
            self.o.bewaar_antwoord(s, self.kind.id, self.T, "5", "snel60", f"haast{i}", "vraag", "1", i % 2,
                                   None, 1000, verwacht="2")
        klok.zet(None)
        r = rapporten.maak_rapport(self.o, self.kind, self.r.periode)
        self.assertEqual([rij[1:] for rij in r.status], [rij[1:] for rij in self.r.status])
        self.assertEqual({i: (n, pct) for i, _, n, _, pct in r.snelstatus}["snelrekenen.tafels"], (34, 50))

    def test_status_zonder_snelrekenen_geen_extra_regel(self):
        o = Opslag()
        kind = o.nieuw_kind("Amira", "5")
        s = o.start_sessie(kind.id, "reeks", self.T, "5")
        o.bewaar_antwoord(s, kind.id, self.T, "5", "reeks", "t1", "vraag", "1", 1, None, 2000, verwacht="1")
        r = rapporten.maak_rapport(o, kind, self.r.periode)
        self.assertEqual(r.snelstatus, [])
        self.assertFalse(any("snelrekenen" in t.lower() for t, _ in rapporten.regels(r, curriculum.indeling())))

    def test_status_past_in_de_lezer(self):
        """STATUS: elke regel past in de lezer (72 tekens), ook met de langste namen en veel antwoorden."""
        dag = date(2026, 10, 20)
        r = rapporten.Rapport(self.kind, self.r.periode, [])
        from leeravontuur.kern import vaardigheden
        r.status = [(v, "nog niet gezien" if i % 3 == 0 else "beheerst", 200, dag, 100)
                    for i, v in enumerate(vaardigheden.REGISTER.values())]
        r.snelstatus = [(f"snelrekenen.{s}", "beheerst", 200, dag, 100) for s in ("tafels", "plusmin", "gemengd")]
        regels = [t for t, _ in rapporten.regels(r, curriculum.indeling())]
        for tekst in regels:
            self.assertLessEqual(len(tekst), 72, tekst)
        self.assertEqual(sum("200 sommen" in t for t in regels), 3)

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
