"""Herhalen › Gemengd oefenen (0.24): de thema's, de reeks met Maten erin, het resultaat per thema, de ouder."""

import os
import random
import tempfile
import unittest
from unittest import mock

from leeravontuur.kern import herhaling, reeks
from leeravontuur.kern.getal import fmt
from leeravontuur.kern.sessie import Sessie
from leeravontuur.kern.wiskunde import eenheden as E
from leeravontuur.terminal.nepscherm import HangtFout, NepScherm, ToetsenOp
from leeravontuur.terminal.schermen import gemengd as G
try:
    from .test_ouder import WW, OuderBasis
    from .test_schermen import ESC, F1, OK, hm
except ImportError:  # ook zo te starten: python -m unittest discover -s tests
    from test_ouder import WW, OuderBasis
    from test_schermen import ESC, F1, OK, hm

TAFELS = "wiskunde.hoofdrekenen.tafels"
MATEN = E.OMZETTEN.id
HOOFDREKENEN = "wiskunde.hoofdrekenen"
METEN = "wiskunde.meten"
NAAR_GEMENGD = [OK, OK, hm("Herhalen"), "2"]


def geoefend(o, kind_id, *vaardigheden):
    for vid in vaardigheden:
        ses = Sessie(o, kind_id, "reeks", vid, "5")
        for i in range(12):
            ses.antwoord(f"{vid}:oud:{i}", "vraag", "1", True)
        ses.sluit()


def antwoord(rv):
    """Wat je typt voor een juist antwoord."""
    v = rv.vraag
    return fmt(v.antwoord) if rv.vaardigheid == MATEN else v.verwacht


class Basis(OuderBasis):
    def met_oefeningen(self, *vaardigheden, **inst):
        o = self.met_wachtwoord(("Lotte", "5", inst) if inst else ("Lotte", "5"))
        geoefend(o, o.kinderen()[0].id, *(vaardigheden or (TAFELS, MATEN)))
        return o

    def vast_plan(self, o, keuze, hulp=reeks.Hulp.ALLES):
        """Een plan met vaste vaardigheden (geen toeval), zodat de test de antwoorden kent."""
        random.seed(5)
        kind = o.kinderen()[0]
        return reeks.Reeksplan("gemengd", G.TITEL, "5", reeks.maak_vragen(o, kind.id, keuze, "5"), hulp)


class TestHerhalenMenu(Basis):
    def test_herhalen_is_een_menu(self):
        scherm, _ = self.speel([OK, OK, hm("Herhalen"), ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Wat wil je herhalen?"))
        self.assertTrue(self.ergens(scherm, "Mijn herhaalvragen (0)"))
        self.assertTrue(self.ergens(scherm, "door elkaar, zodat je niets vergeet"))
        self.assertTrue(self.ergens(scherm, "herhaalvragen en gemengd oefenen"))  # de uitleg in het hoofdmenu

    def test_zonder_iets_geoefend(self):
        scherm, _ = self.speel([*NAAR_GEMENGD, OK, OK, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Welke thema's oefen je door elkaar?"))
        self.assertTrue(self.ergens(scherm, "nog niet geoefend"))
        self.assertTrue(self.ergens(scherm, "In deze thema's heb je nog niets geoefend."))


class TestDeReeks(Basis):
    def test_twintig_vragen_met_het_thema_erbij(self):
        o = self.met_oefeningen()
        scherm, _ = self.speel([*NAAR_GEMENGD, OK], opslag=o)
        self.assertTrue(self.ergens(scherm, "Vraag 1 van 20"))
        self.assertTrue(any("Hoofdrekenen · Tafels" in b or "Meten · Maten" in b for b in scherm.beelden))
        self.assertTrue(self.ergens(scherm, "Leeravontuur › Herhalen › Gemengd oefenen"))
        for b in scherm.beelden:
            for regel in b.splitlines():
                self.assertLessEqual(len(regel), 80)

    def speel_vast(self, o, keuze, toetsen):
        plan = self.vast_plan(o, keuze)
        with mock.patch.object(reeks, "gemengd_plan", return_value=plan):
            return self.speel([*NAAR_GEMENGD, OK, *toetsen], opslag=o), plan

    def test_maten_in_de_reeks_en_het_resultaat_per_thema(self):
        o = self.met_oefeningen()
        keuze = [(HOOFDREKENEN, TAFELS), (METEN, MATEN), (HOOFDREKENEN, TAFELS)]
        plan = self.vast_plan(o, keuze)
        a, b, _ = (antwoord(rv) for rv in plan.vragen)
        with mock.patch.object(reeks, "gemengd_plan", return_value=plan):
            (scherm, app), _ = self.speel([*NAAR_GEMENGD, OK, *a, OK, OK, *b, OK, OK, *"0", OK, *"0", OK, OK,
                                            ESC, ESC, ESC], opslag=o), plan
        self.assertTrue(self.ergens(scherm, "Meten · Maten"))
        self.assertTrue(self.ergens(scherm, "Per thema: Hoofdrekenen 1/2 · Meten 1/1"))
        kind = o.kinderen()[0]
        maten = o.recente_antwoorden(kind.id, MATEN, 5)
        self.assertEqual(maten[0]["modus"], "gemengd")  # onder Maten bewaard, uit de gemengde sessie
        self.assertTrue(maten[0]["juist"])
        self.assertEqual(len(herhaling.aan_de_beurt(o, kind.id)), 0)  # pas morgen
        self.assertTrue(app.laatste_oefening().get("af"))
        self.assertEqual(app.voorstel()[0], "gemengd oefenen · 20 vragen")

    def test_fouten_opnieuw_ook_met_maten(self):
        o = self.met_oefeningen()
        plan = self.vast_plan(o, [(METEN, MATEN)])
        juist = antwoord(plan.vragen[0])
        with mock.patch.object(reeks, "gemengd_plan", return_value=plan):
            scherm, _ = self.speel([*NAAR_GEMENGD, OK, *"0", OK, OK, "f", *juist, OK, OK, ESC, ESC, ESC], opslag=o)
        self.assertTrue(self.ergens(scherm, "Gemengd oefenen › Fouten opnieuw"))
        self.assertTrue(self.ergens(scherm, f"Juist is: {juist} {plan.vragen[0].vraag.naar}"))

    def test_de_keuze_van_het_kind_wordt_bewaard(self):
        o = self.met_oefeningen()
        # Hoofdrekenen is de tweede regel: A = alles uit, dan Hoofdrekenen aan
        scherm, app = self.speel([*NAAR_GEMENGD, "a", "j", " ", OK, ESC, ESC, ESC, ESC], opslag=o)
        self.assertEqual(o.instellingen_van(o.kinderen()[0].id).gemengd_themas, [HOOFDREKENEN])
        self.assertTrue(self.ergens(scherm, "Hoofdrekenen · Tafels"))
        scherm, _ = self.speel([*NAAR_GEMENGD, "a", "a", OK], opslag=o)  # A = alles aan, nog eens = uit; leeg kan niet
        self.assertTrue(self.ergens(scherm, "Kies minstens één thema."))


class TestDeOuderKiest(Basis):
    def test_vast_geen_afvinklijst(self):
        o = self.met_oefeningen(gemengd_ouder={"stand": reeks.VAST, "themas": [METEN]})
        scherm, _ = self.speel([*NAAR_GEMENGD, OK], opslag=o)
        self.assertFalse(self.ergens(scherm, "Welke thema's oefen je door elkaar?"))
        self.assertTrue(self.ergens(scherm, "Vandaag oefen je: Meten."))
        self.assertTrue(self.ergens(scherm, "Je ouder koos deze thema's."))
        self.assertTrue(self.ergens(scherm, "Meten · Maten"))

    def test_een_keer_vervalt_na_het_resultaat(self):
        o = self.met_oefeningen(gemengd_ouder={"stand": reeks.EEN_KEER, "themas": [METEN]})
        kind = o.kinderen()[0]
        plan = self.vast_plan(o, [(METEN, MATEN)])
        with mock.patch.object(reeks, "gemengd_plan", return_value=plan):
            self.speel([*NAAR_GEMENGD, OK, ESC, OK], opslag=o)  # gestopt zonder antwoord: blijft
            self.assertEqual(reeks.ouder_keuze(o.instellingen_van(kind.id))[0], reeks.EEN_KEER)
            self.speel([*NAAR_GEMENGD, OK, *antwoord(plan.vragen[0]), OK, OK, ESC, ESC], opslag=o)
        self.assertEqual(reeks.ouder_keuze(o.instellingen_van(kind.id))[0], reeks.KIND)

    def test_in_het_ouderdeel(self):
        o = self.met_oefeningen()
        kind = o.kinderen()[0]
        # Kinderen › Lotte › Gemengd oefenen (rij 10) › Vast › A (alles uit) › Meten (5de regel) aan › kiezen
        scherm, _ = self.speel([OK, "3", *WW, OK, "3", "1", ("klik", 10, 10), "2", "a", *["j"] * 4, " ", OK,
                                ESC, ESC, ESC, ESC], opslag=o)
        self.assertEqual(o.instellingen_van(kind.id).gemengd_ouder, {"stand": reeks.VAST, "themas": [METEN]})
        self.assertTrue(self.ergens(scherm, "Elke keer oefent Lotte: Meten."))
        self.assertTrue(self.ergens(scherm, "vast: Meten"))
        # terug naar: het kind kiest
        self.speel([OK, "3", *WW, OK, "3", "1", ("klik", 10, 10), "1", ESC, ESC, ESC, ESC], opslag=o)
        self.assertEqual(reeks.ouder_keuze(o.instellingen_van(kind.id))[0], reeks.KIND)


class TestZonderHulp(Basis):
    """Hulp.EXAMEN (voor de examens later): nu al getest, zodat het examen op een geteste basis bouwt."""

    def test_geen_tip_geen_tweede_kans_geen_uitleg_geen_herhaalbak_geen_punten(self):
        o = self.met_oefeningen()
        kind = o.kinderen()[0]
        plan = self.vast_plan(o, [(HOOFDREKENEN, TAFELS), (METEN, MATEN)], hulp=reeks.Hulp.EXAMEN)
        voor = o.punten_saldo(kind.id)
        with mock.patch.object(reeks, "gemengd_plan", return_value=plan):
            scherm, _ = self.speel([*NAAR_GEMENGD, OK, F1, *"0", OK, OK, *antwoord(plan.vragen[1]), OK, OK,
                                    ESC, ESC, ESC], opslag=o)
        self.assertFalse(self.ergens(scherm, "Tip"))
        self.assertFalse(self.ergens(scherm, "[F1]"))
        self.assertFalse(self.ergens(scherm, "Probeer nog eens"))  # geen tweede kans
        self.assertFalse(self.ergens(scherm, "✘ Niet juist"))
        self.assertTrue(self.ergens(scherm, "Je antwoord is bewaard."))
        self.assertEqual(herhaling.aan_de_beurt(o, kind.id), [])
        self.assertEqual(o.punten_saldo(kind.id), voor)
        self.assertEqual(len(o.recente_antwoorden(kind.id, TAFELS, 50)), 13)  # het antwoord is wel bewaard


class TestGerichteAap(Basis):
    """Willekeurig drukken in Gemengd oefenen: geen fout en niets mag blijven hangen."""

    def test_aapjes_in_gemengd_oefenen(self):
        from leeravontuur.terminal.app import App
        try:
            from .test_stabiliteit import TestAapjes
        except ImportError:
            from test_stabiliteit import TestAapjes
        rondes = int(os.environ.get("LEERAVONTUUR_AAP_RONDES", "1"))
        with mock.patch.dict(os.environ, {"LEERAVONTUUR_DEBUG": "1"}):
            for seed in range(4 * rondes):
                rng = random.Random(500 + seed)
                map_ = tempfile.TemporaryDirectory()  # elke ronde een eigen databank (niet de keuzes van de vorige)
                self.addCleanup(map_.cleanup)
                os.environ["LEERAVONTUUR_DATA"] = map_.name
                o = self.met_oefeningen("wiskunde.vraagstukken.oplossen", TAFELS, MATEN, "wiskunde.cijferen.delen",
                                        "wiskunde.breuken.herkennen")
                stappen = [*NAAR_GEMENGD, OK] + [e for e in TestAapjes.gebeurtenissen(self, rng, 400) if e != ESC]
                scherm = NepScherm(stappen + [ESC] * 10)
                try:
                    App(scherm, o, kleuren=False).start()
                except (ToetsenOp, SystemExit):
                    pass
                except HangtFout as e:
                    self.fail(f"seed {seed}: het programma hangt ({e})\n{scherm.tekst()}")
                except Exception as e:  # noqa: BLE001
                    raise AssertionError(f"seed {seed}: {type(e).__name__}: {e}\n{scherm.tekst()}") from e
                self.assertTrue(any("van 20" in b for b in scherm.beelden), seed)


if __name__ == "__main__":
    unittest.main()
