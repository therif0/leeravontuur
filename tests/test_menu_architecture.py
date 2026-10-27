"""Bewaakt de vaste menustructuur: het leerplan (terminal/curriculum) is de enige bron van de menu's.
Deze tests nooit afzwakken of overslaan om een wijziging te laten slagen; vraag het eerst aan de vader."""

import ast
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from leeravontuur.kern import vaardigheden
from leeravontuur.kern.instellingen import Instellingen
from leeravontuur.kern.opslag import Opslag
from leeravontuur.terminal import curriculum as CU
from leeravontuur.terminal.app import App
from leeravontuur.terminal.nepscherm import NepScherm, ToetsenOp

PAKKET = Path(__file__).resolve().parent.parent / "leeravontuur"
OK = "\n"
# het hoofdmenu: vaste keuzes, vaste volgorde (de vakken uit het leerplan op de derde plaats)
HOOFDMENU = ["▶ Verder", "Herhalen", *[v.label for v in CU.VAKKEN], "Spiekbrieven", "Mijn avatar", "Zeg het ons",
             "Wissel van kind", "Stoppen"]
MENUMODULES = ["terminal/app.py", "terminal/navigatie.py", "terminal/scherm.py"]

# Alles wat vandaag in de databank als vaardigheid bewaard wordt (sessies, antwoorden, herhaalbak).
BEWAARD = {
    "wiskunde.eenheden.omzetten",
    "wiskunde.getallen.plaatswaarde", "wiskunde.getallen.afronden", "wiskunde.getallen.deelbaarheid",
    "wiskunde.getallen.getallenlijn",
    "wiskunde.hoofdrekenen.tafels", "wiskunde.hoofdrekenen.plusmin", "wiskunde.hoofdrekenen.maaldeel10",
    "wiskunde.hoofdrekenen.dubbelhelft", "wiskunde.hoofdrekenen.splitsen",
    "wiskunde.cijferen.optellen", "wiskunde.cijferen.aftrekken", "wiskunde.cijferen.vermenigvuldigen",
    "wiskunde.cijferen.delen",
    "wiskunde.breuken.herkennen", "wiskunde.breuken.gelijkwaardig", "wiskunde.breuken.vergelijken",
    "wiskunde.breuken.optellen", "wiskunde.breuken.van", "wiskunde.breuken.kommagetal",
    "wiskunde.procenten.honderdveld", "wiskunde.procenten.omzetten", "wiskunde.procenten.van",
    "wiskunde.procenten.korting",
    "wiskunde.eenheden.tijd", "wiskunde.eenheden.geld", "wiskunde.eenheden.snelheid", "wiskunde.eenheden.klok",
    "wiskunde.meetkunde.rooster", "wiskunde.meetkunde.formules", "wiskunde.meetkunde.hoeken",
    "wiskunde.meetkunde.coordinaten", "wiskunde.meetkunde.schaal",
    "wiskunde.vraagstukken.oplossen", "wiskunde.vraagstukken.speurneus", "wiskunde.vraagstukken.schatten",
    "snelrekenen.tafels", "snelrekenen.plusmin", "snelrekenen.gemengd",
}


class TestRegistry(unittest.TestCase):
    def test_ids_uniek_en_goed_gevormd(self):
        ids = [o.id for o in CU.onderwerpen()]
        self.assertEqual(len(ids), len(set(ids)))
        for vak in CU.VAKKEN:
            for d in vak.domeinen:
                self.assertTrue(d.id.startswith(vak.id + "."), d.id)
                for o in d.onderwerpen:
                    with self.subTest(o.id):
                        self.assertRegex(o.id, r"^[a-z]+\.[a-z_]+\.[a-z0-9_]+$")
                        self.assertTrue(o.id.startswith(d.id + "."))

    def test_elk_onderwerp_heeft_modi(self):
        for o in CU.onderwerpen():
            with self.subTest(o.id):
                self.assertTrue(o.modi)
                for naam, start in o.modi.items():
                    self.assertIn(naam, CU.MODI)
                    self.assertTrue(callable(start))

    def test_spiekbrieven(self):
        for o in CU.onderwerpen():
            if o.spiek is not None:
                with self.subTest(o.id):
                    self.assertTrue(o.spiek.titel.strip())
                    self.assertTrue(callable(o.spiek.toon))

    def test_zelfde_titel_zelfde_spiekbrief(self):
        """Spiekbrieven › domein toont elke titel één keer: onderwerpen met dezelfde titel tonen dus dezelfde
        spiekbrief (anders zou er een wegvallen of een spiekbrief van een ander domein verschijnen)."""
        from leeravontuur.kern import catalogus
        inhoud = {}
        for o in CU.onderwerpen():
            if o.spiek is not None:
                args = getattr(o.spiek.toon, "args", ())
                tekst = repr(catalogus.ONDERWERPEN[args[0]].spiekbrief()) if args else repr(o.spiek.toon)
                inhoud.setdefault(o.spiek.titel, set()).add(tekst)
        for titel, teksten in inhoud.items():
            with self.subTest(titel):
                self.assertEqual(len(teksten), 1)

    def test_niets_bewaard_zonder_onderwerp(self):
        opslag = {i for o in CU.onderwerpen() for i in o.opslag}
        self.assertEqual(opslag, BEWAARD)

    def test_elke_vaardigheid_staat_in_het_menu(self):
        """Een nieuw onderwerp in de kern moet ook in het leerplan (anders kan het kind er niet bij)."""
        opslag = {i for o in CU.onderwerpen() for i in o.opslag}
        self.assertLessEqual(set(vaardigheden.REGISTER), opslag)

    def test_hoogstens_tien_per_menu(self):
        """Met de cijfertoetsen 1–9 en 0 kies je hoogstens 10 keuzes."""
        self.assertLessEqual(len(CU.VAKKEN), CU.MAX_PER_MENU)
        for vak in CU.VAKKEN:
            self.assertLessEqual(len(vak.domeinen), CU.MAX_PER_MENU, vak.id)
            for d in vak.domeinen:
                self.assertLessEqual(len(d.onderwerpen), CU.MAX_PER_MENU, d.id)

    def test_altijd_iets_te_starten(self):
        """Ook als de ouder de timer verbergt (geen 60 seconden) heeft elk onderwerp nog een modus voor Enter."""
        for o in CU.onderwerpen():
            with self.subTest(o.id):
                self.assertTrue(set(o.modi) - {"60s"})

    def test_toetsen_botsen_niet(self):
        """De lettertoetsen zijn verschillende kleine letters en botsen niet met de menutoetsen (j k q, cijfers)."""
        letters = [*CU.TOETS.values(), CU.SPIEK_TOETS]
        self.assertEqual(len(letters), len(set(letters)))
        for t in letters:
            with self.subTest(t):
                self.assertRegex(t, r"^[a-z]$")
                self.assertNotIn(t, "jkq")
        self.assertEqual(set(CU.TOETS), set(CU.MODI) - {"reeks"})

    def test_labels_uniek_per_menu(self):
        for vak in CU.VAKKEN:
            self.assertEqual(len({d.label for d in vak.domeinen}), len(vak.domeinen))
            for d in vak.domeinen:
                self.assertEqual(len({o.label for o in d.onderwerpen}), len(d.onderwerpen), d.id)


class TestModiStarten(unittest.TestCase):
    """Elke modus en spiekbrief opent echt het bestaande scherm (zonder fout)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.oud = os.environ.get("LEERAVONTUUR_DATA")
        os.environ["LEERAVONTUUR_DATA"] = self.tmp.name
        self.opslag = Opslag.open()
        self.kind = self.opslag.nieuw_kind("Test", "5", Instellingen())

    def tearDown(self):
        self.opslag.sluit()
        if self.oud is None:
            os.environ.pop("LEERAVONTUUR_DATA", None)
        else:
            os.environ["LEERAVONTUUR_DATA"] = self.oud
        self.tmp.cleanup()

    def start(self, f, toetsen):
        scherm = NepScherm(toetsen)
        app = App(scherm, self.opslag, None, kleuren=False)
        app.s.klokvenster = None
        app.activeer(self.kind)
        try:
            f(app, ["Leeravontuur", "Test"])
        except ToetsenOp:
            pass
        return scherm.beelden

    def test_elke_modus(self):
        for o in CU.onderwerpen():
            for naam, f in o.modi.items():
                with self.subTest(o.id, modus=naam):
                    beelden = self.start(f, ["2"])  # Normaal, of de eerste stap van de oefening
                    if naam in ("60s", "20sommen"):
                        self.assertIn(CU.MODI[naam], beelden[0])
                    elif o.id.endswith("zelf_kiezen"):
                        self.assertIn("Duid minstens 2 eenheden", beelden[0])
                    else:
                        self.assertIn("Hoe moeilijk?", beelden[0])

    def test_elke_spiekbrief(self):
        for o in CU.onderwerpen():
            if o.spiek:
                with self.subTest(o.id):
                    beeld = self.start(o.spiek.toon, [])[-1]
                    self.assertGreater(len([r for r in beeld.splitlines() if r.strip()]), 5)


class TestNavigatie(TestModiStarten):
    def speel(self, toetsen, voorrang=None):
        self.opslag.zet_algemeen("laatste_kind", self.kind.id)
        scherm = NepScherm(toetsen)
        self.scherm = scherm
        app = App(scherm, self.opslag, voorrang, kleuren=False)
        app.s.klokvenster = None
        with mock.patch.dict(os.environ, {"LEERAVONTUUR_DEBUG": "1"}):  # geen vangnet: stoppen waar de toetsen op zijn
            try:
                app.start()
            except ToetsenOp:
                pass
        self.app = app
        return scherm.beelden

    def test_hoofdmenu_vaste_volgorde(self):
        beeld = next(b for b in self.speel([OK, OK]) if "Wat wil je doen?" in b)
        keuzes = [m.group(1) for r in beeld.splitlines() if (m := re.match(r"^\s+\d\. (.+?)(?: \(\d+\))?(?:  |$)", r))]
        self.assertEqual(keuzes, HOOFDMENU)

    def test_elk_onderwerp_in_drie_keuzes(self):
        """Hoofdmenu → Vak → Domein → Onderwerp: drie keuzes (met cijfers), dan start de oefening (Enter)."""
        for vi, vak in enumerate(CU.VAKKEN):
            for di, d in enumerate(vak.domeinen):
                for oi, o in enumerate(d.onderwerpen):
                    with self.subTest(o.id):
                        keuzes = [str(HOOFDMENU.index(vak.label) + 1), str(di + 1), str((oi + 1) % 10)]
                        beeld = self.speel([OK, OK, *keuzes])[-1]
                        self.assertIn(o.label, self.app.s.kruimel)  # de volledige broodkruimel
                        self.assertTrue(any(t in beeld for t in ("Hoe moeilijk?", "Duid minstens", "Som 1 van",
                                                                   "Nog ")), beeld)

    def test_terug_op_hetzelfde_onderwerp(self):
        """Na een spiekbrief (of oefening) staat dezelfde keuze nog gemarkeerd: de voetregel is die van dat onderwerp."""
        import curses
        hr = next(d for d in CU.domeinen() if d.id == "wiskunde.hoofdrekenen")
        i = next(i for i, o in enumerate(hr.onderwerpen) if "60s" not in o.modi)  # een onderwerp zonder T
        beelden = self.speel([OK, OK, str(HOOFDMENU.index("Wiskunde") + 1), str(CU.VAKKEN[0].domeinen.index(hr) + 1),
                              *[curses.KEY_DOWN] * i, "s", "\x1b"])
        self.assertNotIn("[T]", beelden[-1].splitlines()[-1])
        self.assertIn("wat wil je oefenen?", beelden[-1])

    def test_verder_met_een_oefening_van_versie_019(self):
        """Een vorige oefening zoals 0.19.0 ze bewaarde (met het oude domein 'Procenten') start via het leerplan."""
        import json
        self.opslag.zet_algemeen(f"laatste_oefening:{self.kind.id}", json.dumps(
            {"onderwerp": "oefenaar", "vaardigheid": "wiskunde.procenten.van", "vorm": "vrij", "niveau": 1,
             "domein": "Procenten"}))
        beelden = self.speel([OK, OK, "1"])
        self.assertTrue(any("▶ Verder          procent van een getal" in b for b in beelden))
        self.assertIn("Breuken en procenten", self.app.s.kruimel)
        self.assertIn("Procent van een getal", self.app.s.kruimel)

    def test_spiekbrieven_kort(self):
        """#20: zolang er één vak is, geen "Welk vak?"; een domein met één spiekbrief opent die meteen, bij meer staat
        in de uitleg welke er zijn."""
        spiek = str(HOOFDMENU.index("Spiekbrieven") + 1)
        beeld = self.speel([OK, OK, spiek])[-1]
        self.assertIn("Welke spiekbrief?", beeld)
        self.assertIn("1. Getallen", beeld)
        self.assertIn("2 spiekbrieven: Breuken, Procenten", beeld)
        getallen = next(i for i, d in enumerate(CU.VAKKEN[0].domeinen, 1) if d.id == "wiskunde.getallen")
        beeld = self.speel([OK, OK, spiek, str(getallen)])[-1]
        self.assertIn("PLAATSWAARDE", beeld)
        self.assertEqual(self.app.s.kruimel[-2:], ["Spiekbrieven", "Getallen"])

    def test_gedeelde_spiekbrief_een_keer(self):
        meten = next(i for i, d in enumerate(CU.VAKKEN[0].domeinen, 1) if d.id == "wiskunde.meten")
        beeld = self.speel([OK, OK, str(HOOFDMENU.index("Spiekbrieven") + 1), str(meten)])[-1]
        self.assertEqual(beeld.count("Eenheden omzetten"), 1)
        self.assertIn("2. Oppervlakte en formules", beeld)
        self.assertNotIn("3. ", beeld)

    def naar_hoofdrekenen(self):
        hr = next(i for i, d in enumerate(CU.VAKKEN[0].domeinen, 1) if d.id == "wiskunde.hoofdrekenen")
        return [OK, OK, str(HOOFDMENU.index("Wiskunde") + 1), str(hr)]

    def test_voetregel_klikbaar_in_het_echte_menu(self):
        """Een klik op "[V] vrij" in de voetregel doet hetzelfde als de toets V."""
        self.speel(self.naar_hoofdrekenen())
        y, x = self.scherm.zoek("[V] vrij")
        beelden = self.speel([*self.naar_hoofdrekenen(), ("klik", y, x + 1)])
        self.assertIn("Hoe moeilijk?", beelden[-1])
        self.assertEqual(self.app.s.kruimel[-1], "Vrij oefenen")

    def test_voetregel_in_eenvoudige_tekens(self):
        """Met --ascii alleen gewone tekens, ook in de labels (×) en de voetregel van het onderwerpenmenu."""
        beelden = self.speel(self.naar_hoofdrekenen(), voorrang={"ascii": True})
        self.assertIn("[Enter] reeks  [V] vrij", beelden[-1].splitlines()[-1])
        self.assertIn("x en : met 10, 100, 1000", beelden[-1])
        for beeld in beelden:
            self.assertTrue(all(ord(c) < 128 for c in beeld), beeld)

    def test_broodkruimel_uit_elke_soort_oefening(self):
        """Een klik op de broodkruimel midden in een oefening (gewone reeks, maten, snelrekenen) gaat naar dat niveau."""
        import curses
        for oid, toets in [("wiskunde.hoofdrekenen.tafels", "\n"), ("wiskunde.meten.lengte", "v"),
                           ("wiskunde.hoofdrekenen.gemengd", "\n")]:
            o = CU.zoek(oid)
            d = CU.domein_van(o)
            i = d.onderwerpen.index(o)
            naar = [OK, OK, str(HOOFDMENU.index("Wiskunde") + 1), str(CU.VAKKEN[0].domeinen.index(d) + 1),
                    *[curses.KEY_DOWN] * i, toets, *([OK] if "reeks" in o.modi else [])]
            kop = self.speel(naar)[-1].splitlines()[0]
            for woord, verwacht in [("Leeravontuur", "Wat wil je doen?"), ("Wiskunde", "Welk onderwerp?"),
                                    (d.label, "wat wil je oefenen?")]:
                with self.subTest(oid, niveau=woord):
                    beeld = self.speel([*naar, ("klik", 0, kop.index(woord) + 1)])[-1]
                    self.assertIn(verwacht, beeld)

    def test_geen_namen_in_de_menumodules(self):
        """Namen van vakken, domeinen en onderwerpen staan alleen in het leerplan (terminal/curriculum)."""
        namen = {v.label for v in CU.VAKKEN} | {d.label for d in CU.domeinen()} | {o.label for o in CU.onderwerpen()}
        for pad in MENUMODULES:
            with self.subTest(pad):
                boom = ast.parse((PAKKET / pad).read_text(encoding="utf-8"))
                teksten = {n.value for n in ast.walk(boom) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
                self.assertEqual(teksten & namen, set())


if __name__ == "__main__":
    unittest.main()
