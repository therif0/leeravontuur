"""Stabiliteit: geen crashes en geen verloren gegevens.

- elke vraaggenerator in elk leerjaar, ook met vreemde antwoorden
- herhalingen over leerjaren heen (een fout uit Moeilijk komt terug op het eigen leerjaar)
- toetsen: een pijltje mag nooit als teken in een antwoord belanden
- de databank: reservekopieën, een beschadigd bestand, een vergrendelde databank
- het vangnet: een fout in een scherm brengt je terug naar het menu (met een logboek)
- een "aapjestest": duizenden willekeurige toetsen, klikken en venstergroottes door de hele app
"""

import curses
import os
import random
import sqlite3
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from leeravontuur.kern import catalogus, foutlog, klok, leerjaren, verhaal
from leeravontuur.kern.wiskunde import vraagstukken
from leeravontuur.kern.instellingen import Instellingen
from leeravontuur.kern.opslag import MIGRATIES, Opslag
from leeravontuur.kern.onderwerp import Vraag
from leeravontuur.terminal.app import App
from leeravontuur.terminal.nepscherm import HangtFout, NepScherm, ToetsenOp
from leeravontuur.terminal.scherm import Scherm, teken_van

try:
    from .test_schermen import ESC, OK, Basis, hm
except ImportError:
    from test_schermen import ESC, OK, Basis, hm

VREEMD = ["", " ", "abc", "-5", "0", "999999999", "1/2", "1 1/2", "3/0", "ja", "nee", "<", "=", "12,5", "€ 3",
          "35 %", "−0,001", "x/y", "9" * 30]


class TempData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.oud = os.environ.get("LEERAVONTUUR_DATA")
        os.environ["LEERAVONTUUR_DATA"] = self.tmp.name

    def tearDown(self):
        klok.zet(None)
        if self.oud is None:
            os.environ.pop("LEERAVONTUUR_DATA", None)
        else:
            os.environ["LEERAVONTUUR_DATA"] = self.oud
        self.tmp.cleanup()


class TestGeneratoren(TempData):
    def test_elk_onderwerp_elk_leerjaar(self):
        rng = random.Random(42)
        for oid, o in catalogus.ONDERWERPEN.items():
            for jaar in leerjaren.LEERJAREN:
                for _ in range(40):
                    begin = time.monotonic()
                    v = o.maak(jaar, rng=rng)  # ook in een leerjaar waar het onderwerp niet bestaat
                    self.assertLess(time.monotonic() - begin, 1.0, f"{oid} {jaar} is te traag")
                    self.assertIsInstance(v, Vraag)
                    if v.invoer in ("vraagstuk", "speur", "keuze"):  # een verhaal: hoogstens 4 regels in het kader
                        model = v.model if v.invoer == "vraagstuk" else v.model.verhaal
                        self.assertLessEqual(len(verhaal.regels(model.zinnen, vraagstukken.BREEDTE)),
                                             vraagstukken.REGELS, v.tekst)
                    else:
                        self.assertLessEqual(len(v.tekst), 108, v.tekst)  # past op 2 regels
                    if v.invoer != "veld":
                        self.assertTrue(o.nakijken(v, o.lees_vraag(v, v.verwacht)), (oid, v.tekst, v.verwacht))
                    o.uitleg(v)
                    o.tip(v)
                    groep = o.onderwerp_van_sleutel(v.sleutel)  # gebruikt voor de gewichten van een reeks
                    if o.aangeboden(jaar):
                        o.maak(jaar, rng=rng, gewichten={groep: 3.0, "iets anders": 1.0})
                    for tekst in VREEMD:
                        getal = o.lees_vraag(v, tekst)
                        o.nakijken(v, getal)
                        o.diagnose(v, getal)

    def test_herhaling_over_leerjaren_heen(self):
        rng = random.Random(7)
        for oid, o in catalogus.ONDERWERPEN.items():
            for bron in leerjaren.LEERJAREN:
                if not o.aangeboden(bron):
                    continue
                for _ in range(15):
                    data = o.herhaal_data(o.maak(bron, rng=rng))
                    for doel in leerjaren.LEERJAREN:
                        w = o.maak(doel, data=data)  # zonder vangnet: dit mag gewoon niet mislukken
                        o.uitleg(w)

    def test_herhaling_met_vreemde_data(self):
        for oid, o in catalogus.ONDERWERPEN.items():
            v = o.maak_herhaling({"soort": "bestaat-niet", "k": "x", "deler": None, "onderwerp": 3}, "5")
            self.assertIsInstance(v, Vraag, oid)
        self.assertGreater(foutlog.aantal(), 0)  # de vreemde data staat in het logboek


class TestToetsen(unittest.TestCase):
    def test_functietoetsen_typen_niets(self):
        for k in range(curses.KEY_MIN, curses.KEY_MAX + 1):
            if k in (curses.KEY_BACKSPACE,):
                continue
            self.assertEqual(Scherm.bewerk("12", k), "12", k)
        self.assertEqual(Scherm.bewerk("c", ("teken", "œ")), "cœ")
        self.assertEqual(teken_van(curses.KEY_LEFT), None)
        self.assertEqual(teken_van(ord("é")), "é")

    def test_teken_met_toetscode_wordt_teken(self):
        s = Scherm(NepScherm(["Ą"]), Instellingen(), kleuren=False)
        self.assertEqual(s.toets(), ("teken", "Ą"))


class TestDatabank(TempData):
    def pad(self):
        return Path(self.tmp.name) / "leeravontuur.db"

    def test_dagkopie_en_opruimen(self):
        begin = datetime(2026, 10, 1, 9, 0).astimezone()
        for dag in range(10):
            klok.zet(begin + timedelta(days=dag))
            o = Opslag.open(self.pad())
            o.sluit()
        kopieen = sorted(p.name for p in (Path(self.tmp.name) / "reserve").glob("leeravontuur-????-??-??.db"))
        self.assertEqual(len(kopieen), 7)
        self.assertEqual(kopieen[-1], "leeravontuur-2026-10-10.db")

    def test_beschadigd_bestand_krijgt_de_reservekopie(self):
        o = Opslag.open(self.pad())  # de eerste kopie van vandaag is nog leeg …
        kind = o.nieuw_kind("Imrane", "5")
        o.sluit()  # … maar bij het afsluiten wordt ze ververst
        self.pad().write_bytes(b"kapot" * 100)
        o = Opslag.open(self.pad())
        self.assertIn("reservekopie", o.probleem)
        self.assertEqual([k.naam for k in o.kinderen()], ["Imrane"])
        self.assertEqual(o.kinderen()[0].id, kind.id)
        self.assertTrue(list(Path(self.tmp.name).glob("leeravontuur.db.beschadigd-*")))
        o.sluit()

    def test_kopie_voor_migratie(self):
        con = sqlite3.connect(str(self.pad()))
        con.execute("CREATE TABLE schema (versie INTEGER NOT NULL)")
        con.execute("INSERT INTO schema VALUES (1)")
        con.executescript(MIGRATIES[0])
        con.commit()
        con.close()
        o = Opslag(self.pad())
        self.assertEqual(o.versie, len(MIGRATIES))
        self.assertTrue((Path(self.tmp.name) / "reserve" / f"leeravontuur-voor-v{len(MIGRATIES)}.db").exists())
        o.sluit()

    def test_vergrendelde_databank_crasht_niet(self):
        o = Opslag.open(self.pad())
        kind = o.nieuw_kind("Test", "5")
        o.con.execute("PRAGMA busy_timeout = 50")
        ander = sqlite3.connect(str(self.pad()), timeout=0.05)
        ander.execute("BEGIN EXCLUSIVE")
        try:
            self.assertEqual(o.telling(kind.id, klok.dag()), (0, 0))
            self.assertEqual(o.kinderen(), [])
            self.assertEqual(o.punten_saldo(kind.id), 0)
            self.assertFalse(o.bewaar_antwoord(None, kind.id, "x", "5", "vrij", "k", "v", "1", True))
            self.assertIsNotNone(o.probleem)
        finally:
            ander.rollback()
            ander.close()
        self.assertEqual(o.kinderen(), [kind])  # daarna werkt alles weer
        o.sluit()

    def test_beschadigde_json(self):
        o = Opslag.open(self.pad())
        kind = o.nieuw_kind("Test", "5")
        o._schrijf("UPDATE instellingen SET data = '{kapot' WHERE kind_id = ?", (kind.id,))
        o._schrijf("INSERT INTO avatar (kind_id, config, gewijzigd) VALUES (?, 'nee{', '')", (kind.id,))
        self.assertEqual(o.instellingen_van(kind.id).naam, "Test")
        self.assertIsNone(o.avatar(kind.id))
        o.sluit()


class TestVangnet(Basis):
    def test_fout_in_een_scherm_gaat_terug_naar_het_menu(self):
        from leeravontuur.terminal.oefenaar import Oefenaar
        o = self.opslag(("Test", "5"))
        with mock.patch.object(Oefenaar, "spiekbrief", side_effect=RuntimeError("expres")):
            scherm, app = self.speel([OK, OK, hm("Spiekbrieven"), "2", OK, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Oei, er ging iets mis."))
        self.assertIn("RuntimeError: expres", foutlog.meldingen()[-1])
        self.assertIn("Spiekbrieven", foutlog.meldingen()[-1])  # waar het gebeurde
        laatste = [b for b in scherm.beelden if "Wat wil je doen?" in b]
        self.assertTrue(laatste)  # terug in het hoofdmenu

    def test_sessie_wordt_gesloten(self):
        from leeravontuur.terminal.oefenaar import Oefenaar
        o = self.opslag(("Test", "5"))
        with mock.patch.object(Oefenaar, "stel_vraag", side_effect=RuntimeError("expres")):
            self.speel([OK, OK, hm("Leren & oefenen"), "1", "2", "1", "1", OK, OK, ESC, ESC, ESC], opslag=o)
        sessies = o.sessies(o.kinderen()[0].id)
        self.assertEqual(len(sessies), 1)
        self.assertIsNotNone(sessies[0]["einde"])

    def test_drie_keer_snel_dan_toch_stoppen(self):
        with mock.patch.object(App, "spiekbrieven", side_effect=RuntimeError("expres")):
            with self.assertRaises(RuntimeError):
                self.speel([OK, OK, *[hm("Spiekbrieven"), OK] * 3, ESC])


class TestAapjes(Basis):
    """Willekeurige toetsen en klikken door de hele app. Er mag nooit een fout komen, en niets mag blijven hangen."""
    STAPPEN = int(os.environ.get("LEERAVONTUUR_AAP", "700"))
    SEEDS = range(int(os.environ.get("LEERAVONTUUR_AAP_SEEDS", "12")))

    def gebeurtenissen(self, rng, n):
        toetsen = list("0123456789") * 3 + list("abcdefghijklmnopqrstuvwxyz") + list(" ?+-,/<>=r") + \
            [OK] * 8 + [ESC] * 2 + ["\t", "\b", "Ą", "œ", "é"] + \
            [curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_UP, curses.KEY_DOWN] * 4 + \
            [curses.KEY_BACKSPACE, curses.KEY_DC, curses.KEY_HOME, curses.KEY_F1]
        uit = []
        for _ in range(n):
            r = rng.random()
            if r < 0.15:
                uit.append(("klik", rng.randrange(24), rng.randrange(80)))
            elif r < 0.17:
                uit.append(("wiel", rng.choice([-1, 1])))
            elif r < 0.18:
                uit.append(("grootte", *rng.choice([(24, 80), (30, 100), (20, 70), (24, 80)])))
            elif r < 0.19:
                uit.append(("wacht",))
            else:
                uit.append(rng.choice(toetsen))
        return uit

    def test_aapjes(self):
        with mock.patch.dict(os.environ, {"LEERAVONTUUR_DEBUG": "1"}):  # geen vangnet: elke fout moet boven komen
            for seed in self.SEEDS:
                rng = random.Random(seed)
                opslag = self.opslag(("Aap", rng.choice(["3", "4", "5", "6", "m1"])))
                scherm = NepScherm(self.gebeurtenissen(rng, self.STAPPEN))
                while True:
                    app = App(scherm, opslag, kleuren=False)
                    try:
                        app.start()
                    except (ToetsenOp, SystemExit):
                        pass
                    except HangtFout as e:
                        self.fail(f"seed {seed}: het programma hangt ({e})\n{scherm.tekst()}")
                    except Exception as e:  # noqa: BLE001
                        raise AssertionError(f"seed {seed}: {type(e).__name__}: {e}\n{scherm.tekst()}") from e
                    if not scherm.toetsen:
                        break
                    scherm.h, scherm.w = 24, 80  # opnieuw starten, zoals een kind dat het programma weer opent

    def test_gerichte_aapjes_in_elke_oefening(self):
        """Naar elke oefening (elk onderwerp, vrij oefenen en een reeks) en daar willekeurig drukken en klikken."""
        self.bereikt = 0
        domeinen = App.domeinen(None)
        rondes = int(os.environ.get("LEERAVONTUUR_AAP_RONDES", "1"))
        with mock.patch.dict(os.environ, {"LEERAVONTUUR_DEBUG": "1"}):
            for ronde in range(rondes):
                self.gericht(domeinen, random.Random(99 + ronde))
        aantal = sum(2 * 2 for _, _, o, _ in domeinen for _ in (o or [None]))
        self.assertGreater(self.bereikt, 0.9 * aantal * rondes, "de aapjes kwamen niet in de oefeningen")

    def gericht(self, domeinen, rng):
        from leeravontuur.terminal import app as app_mod
        for d, (naam, _, onderwerpen, _) in enumerate(domeinen, 1):
            for i in range(1, len(onderwerpen or [None]) + 1):
                for vorm in ("1", "2"):  # vrij oefenen, reeks
                    for niveau in (OK, "4"):  # Normaal, Heel moeilijk
                        stappen = [OK, OK, hm("Leren & oefenen"), "1", str(d)]
                        if onderwerpen is None:
                            stappen += [vorm, niveau]  # Eenheden: eigen menu (vorm, dan niveau)
                        else:
                            stappen += ([str(i)] if len(onderwerpen) > 1 else []) + [vorm, niveau]
                        stappen += [e for e in self.gebeurtenissen(rng, 160) if e != ESC] + [ESC] * 8
                        opslag = self.opslag(("Aap", "5"))
                        scherm = NepScherm(stappen)
                        try:
                            app_mod.App(scherm, opslag, kleuren=False).start()
                        except (ToetsenOp, SystemExit):
                            pass
                        except HangtFout as e:
                            self.fail(f"{naam} {i} {vorm}: het programma hangt ({e})\n{scherm.tekst()}")
                        except Exception as e:  # noqa: BLE001
                            raise AssertionError(f"{naam} {i} {vorm}: {type(e).__name__}: {e}\n"
                                                 f"{scherm.tekst()}") from e
                        self.bereikt += any("Vrij oefenen:" in bl or "Vraag 1 van" in bl for bl in scherm.beelden)


if __name__ == "__main__":
    unittest.main()
