"""kern/reeks.py: de gemengde reeks (Gemengd oefenen nu, de examens later)."""

import random
import unittest
from collections import Counter
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from leeravontuur.kern import herhaling, klok, reeks
from leeravontuur.kern.instellingen import Instellingen
from leeravontuur.kern.opslag import Opslag
from leeravontuur.kern.sessie import Sessie
from leeravontuur.kern.wiskunde import eenheden as E

CET = timezone(timedelta(hours=1))
DAG = datetime(2026, 11, 7, 15, 0, tzinfo=CET)

TAFELS = "wiskunde.hoofdrekenen.tafels"
PLUSMIN = "wiskunde.hoofdrekenen.plusmin"
BREUK_HERKENNEN = "wiskunde.breuken.herkennen"
VRAAGSTUK = "wiskunde.vraagstukken.oplossen"
STAART = "wiskunde.cijferen.delen"
MATEN = E.OMZETTEN.id


class Basis(unittest.TestCase):
    def setUp(self):
        self.o = Opslag()
        self.kind = self.o.nieuw_kind("Lotte", "5")
        klok.zet(DAG)

    def tearDown(self):
        klok.zet(None)

    def geoefend(self, vaardigheid, n=20, juist=True, dagen_geleden=0, modus="reeks"):
        """n antwoorden op deze vaardigheid, zoveel dagen geleden."""
        klok.zet(DAG - timedelta(days=dagen_geleden))
        ses = Sessie(self.o, self.kind.id, modus, vaardigheid, "5")
        for i in range(n):
            ses.antwoord(f"{vaardigheid}:{dagen_geleden}:{i}", "vraag", "1", juist)
        klok.zet(DAG)


class TestStand(Basis):
    def test_standen(self):
        self.assertIsNone(reeks.stand(self.o, self.kind.id, TAFELS))
        self.geoefend(TAFELS, dagen_geleden=3)
        self.assertEqual(reeks.stand(self.o, self.kind.id, TAFELS), (herhaling.BEHEERST, 3))
        self.geoefend(PLUSMIN, dagen_geleden=reeks.FRIS_DAGEN)
        self.assertEqual(reeks.stand(self.o, self.kind.id, PLUSMIN), (reeks.FRIS, reeks.FRIS_DAGEN))
        self.geoefend(BREUK_HERKENNEN, n=5, juist=False, dagen_geleden=30)  # niet beheerst: bezig, nooit fris
        self.assertEqual(reeks.stand(self.o, self.kind.id, BREUK_HERKENNEN)[0], herhaling.BEZIG)

    def test_snelrekenen_telt_niet(self):
        self.geoefend(TAFELS, modus="snel60")
        self.assertIsNone(reeks.stand(self.o, self.kind.id, TAFELS))


class TestFrisInHetRapport(Basis):
    def test_status_per_vaardigheid(self):
        from leeravontuur.kern import rapporten
        self.geoefend(TAFELS, dagen_geleden=reeks.FRIS_DAGEN)
        self.geoefend(PLUSMIN, dagen_geleden=reeks.FRIS_DAGEN - 1)
        r = rapporten.maak_rapport(self.o, self.kind, rapporten.periodes()[0])
        stand = {v.id: st for v, st, *_ in r.status}
        self.assertEqual(stand[TAFELS], herhaling.FRIS_HOUDEN)
        self.assertEqual(stand[PLUSMIN], herhaling.BEHEERST)
        regels = rapporten.regels(r)
        fris = [(t, rol) for t, rol in regels if "fris houden" in t]
        self.assertEqual(len(fris), 1)
        self.assertEqual(fris[0][1], "accent")


class TestKiezen(Basis):
    THEMAS = {"wiskunde.hoofdrekenen": (PLUSMIN, TAFELS), "wiskunde.breuken": (BREUK_HERKENNEN,),
              "wiskunde.meten": (MATEN,), "wiskunde.vraagstukken": (VRAAGSTUK,), "wiskunde.cijferen": (STAART,)}

    def test_alleen_wat_al_geoefend_werd(self):
        self.assertEqual(reeks.kies_onderwerpen(self.o, self.kind.id, self.THEMAS), [])
        self.geoefend(TAFELS)
        keuze = reeks.kies_onderwerpen(self.o, self.kind.id, self.THEMAS, rng=random.Random(1))
        self.assertEqual(len(keuze), reeks.GEMENGD_AANTAL)
        self.assertEqual({v for _, v in keuze}, {TAFELS})

    def test_fris_houden_komt_het_vaakst(self):
        self.geoefend(TAFELS, dagen_geleden=1)  # beheerst en recent
        self.geoefend(PLUSMIN, dagen_geleden=40)  # fris houden
        tel = Counter()
        for seed in range(30):
            tel.update(v for _, v in reeks.kies_onderwerpen(self.o, self.kind.id, self.THEMAS,
                                                            rng=random.Random(seed)))
        self.assertGreater(tel[PLUSMIN], tel[TAFELS])
        self.assertGreater(tel[TAFELS], 0)  # beheerst komt ook nog, maar minder

    def test_niet_te_veel_na_elkaar_en_lang(self):
        for vid in (PLUSMIN, BREUK_HERKENNEN, MATEN, VRAAGSTUK, STAART):
            self.geoefend(vid, dagen_geleden=20)
        for seed in range(40):
            keuze = reeks.kies_onderwerpen(self.o, self.kind.id, self.THEMAS, rng=random.Random(seed))
            self.assertLessEqual(sum(reeks.is_lang(v) for _, v in keuze), reeks.MAX_LANG)
            themas = [t for t, _ in keuze]
            for i in range(len(themas) - reeks.MAX_NA_ELKAAR):
                self.assertGreater(len(set(themas[i:i + reeks.MAX_NA_ELKAAR + 1])), 1, (seed, themas))

    def test_deterministisch_met_een_vaste_seed(self):
        for vid in (PLUSMIN, TAFELS, BREUK_HERKENNEN):
            self.geoefend(vid)
        a = reeks.kies_onderwerpen(self.o, self.kind.id, self.THEMAS, rng=random.Random(7))
        b = reeks.kies_onderwerpen(self.o, self.kind.id, self.THEMAS, rng=random.Random(7))
        self.assertEqual(a, b)

    def test_onbekende_vaardigheid_doet_niet_mee(self):
        self.geoefend(TAFELS)
        keuze = reeks.kies_onderwerpen(self.o, self.kind.id, {"x": ("bestaat.niet", TAFELS)})
        self.assertEqual({v for _, v in keuze}, {TAFELS})


class TestPlan(Basis):
    def test_vragen_ook_maten_en_een_vraagstuk(self):
        themas = TestKiezen.THEMAS
        for vid in (TAFELS, MATEN, VRAAGSTUK):
            self.geoefend(vid)
        plan = reeks.gemengd_plan(self.o, self.kind.id, themas, "5", rng=random.Random(3))
        self.assertEqual(plan.soort, "gemengd")
        self.assertEqual(plan.hulp, reeks.Hulp.ALLES)
        self.assertEqual(len(plan.vragen), reeks.GEMENGD_AANTAL)
        for rv in plan.vragen:
            self.assertIn(rv.vaardigheid, themas[rv.thema])
            self.assertTrue(rv.vraag.sleutel)
        sleutels = [rv.vraag.sleutel for rv in plan.vragen]
        self.assertGreater(len(set(sleutels)), len(sleutels) // 2)  # zo weinig mogelijk dezelfde vraag
        self.assertIn(MATEN, {rv.vaardigheid for rv in plan.vragen})

    def test_niets_geoefend_geen_plan(self):
        self.assertIsNone(reeks.gemengd_plan(self.o, self.kind.id, TestKiezen.THEMAS, "5"))

    def test_hulp_voor_een_examen(self):
        ex = reeks.Hulp.EXAMEN
        self.assertFalse(any((ex.tips, ex.tweede_kans, ex.spiekbrief, ex.uitleg_na, ex.herhaalbak, ex.punten)))
        self.assertTrue(all((reeks.Hulp.ALLES.tips, reeks.Hulp.ALLES.tweede_kans, reeks.Hulp.ALLES.uitleg_na)))


class TestElkOnderwerp(Basis):
    def test_elke_vaardigheid_van_het_leerplan_in_elk_leerjaar(self):
        """Elk onderwerp met een reeks in het leerplan geeft in een gemengde reeks een vraag, in elk leerjaar."""
        from leeravontuur.kern.leerjaren import LEERJAREN
        from leeravontuur.terminal import curriculum as CU
        ids = {vid for v in CU.VAKKEN for d in v.domeinen for o in d.onderwerpen if "reeks" in o.modi
               for vid in o.opslag}
        self.assertIn(MATEN, ids)
        for vid in sorted(ids):
            if vid.startswith("snelrekenen."):  # de sessies van snelrekenen: die doen niet mee
                self.assertFalse(reeks.bestaat(vid), vid)
                continue
            self.assertTrue(reeks.bestaat(vid), vid)
            for jaar in LEERJAREN:
                v = reeks.maak_vraag(self.o, self.kind.id, vid, jaar, set())
                self.assertTrue(v.sleutel, (vid, jaar))


class TestUitslag(unittest.TestCase):
    def test_per_thema(self):
        a, b, c = (reeks.Reeksvraag(t, "v", None) for t in ("breuken", "meten", "breuken"))
        u = reeks.Uitslag.van([(a, True, 1000), (b, False, 2000), (c, False, 500)])
        self.assertEqual((u.goed, u.totaal, u.tijd_ms), (1, 3, 3500))
        self.assertEqual(u.per_thema, {"breuken": [1, 2], "meten": [0, 1]})
        self.assertEqual(list(u.per_thema), ["breuken", "meten"])
        self.assertEqual(u.fouten, [b, c])


class TestWieKiest(unittest.TestCase):
    ALLE = ["wiskunde.getallen", "wiskunde.breuken", "wiskunde.meten"]

    def test_het_kind_kiest(self):
        inst = Instellingen()
        self.assertEqual(reeks.themas_voor_reeks(inst, self.ALLE), (self.ALLE, True))  # standaard: alles
        inst.gemengd_themas = ["wiskunde.meten", "wiskunde.breuken"]
        self.assertEqual(reeks.themas_voor_reeks(inst, self.ALLE), (["wiskunde.breuken", "wiskunde.meten"], True))
        inst.gemengd_themas = ["weg"]  # een thema dat niet meer bestaat: dan alles
        self.assertEqual(reeks.themas_voor_reeks(inst, self.ALLE), (self.ALLE, True))

    def test_vast(self):
        inst = Instellingen(gemengd_themas=["wiskunde.getallen"],
                            gemengd_ouder={"stand": reeks.VAST, "themas": ["wiskunde.meten"]})
        self.assertEqual(reeks.themas_voor_reeks(inst, self.ALLE), (["wiskunde.meten"], False))
        self.assertIs(reeks.na_reeks(inst), inst)  # vast blijft

    def test_een_keer_vervalt_na_de_reeks(self):
        inst = Instellingen(gemengd_ouder={"stand": reeks.EEN_KEER, "themas": ["wiskunde.breuken"]})
        self.assertEqual(reeks.themas_voor_reeks(inst, self.ALLE), (["wiskunde.breuken"], False))
        na = reeks.na_reeks(inst)
        self.assertEqual(reeks.themas_voor_reeks(na, self.ALLE), (self.ALLE, True))
        self.assertEqual(inst.gemengd_ouder["stand"], reeks.EEN_KEER)  # het origineel blijft onaangeroerd

    def test_ongeldige_keuze_van_de_ouder(self):
        for fout in ({"stand": "raar", "themas": ["wiskunde.meten"]}, {"stand": reeks.VAST, "themas": []},
                     {"stand": reeks.VAST, "themas": ["weg"]}, {"stand": reeks.VAST, "themas": "x"}, "x"):
            inst = replace(Instellingen(), gemengd_ouder=fout)
            self.assertEqual(reeks.themas_voor_reeks(inst, self.ALLE), (self.ALLE, True), fout)

    def test_bewaard_en_gecontroleerd(self):
        o = Opslag()
        kind = o.nieuw_kind("Lotte", "5")
        inst = o.instellingen_van(kind.id)
        inst.gemengd_themas = ["wiskunde.meten"]
        inst.gemengd_ouder = {"stand": reeks.EEN_KEER, "themas": ["wiskunde.breuken"]}
        o.bewaar_instellingen(kind.id, inst)
        terug = o.instellingen_van(kind.id)
        self.assertEqual((terug.gemengd_themas, terug.gemengd_ouder), (inst.gemengd_themas, inst.gemengd_ouder))
        slecht = Instellingen(gemengd_themas="meten", gemengd_ouder=[1]).gecontroleerd()
        self.assertIsNone(slecht.gemengd_themas)
        self.assertEqual(slecht.gemengd_ouder, {"stand": reeks.KIND, "themas": []})


if __name__ == "__main__":
    unittest.main()
