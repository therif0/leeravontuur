"""Bewaakt de vaste menustructuur: het leerplan (terminal/curriculum) is de enige bron van de menu's.
Deze tests nooit afzwakken of overslaan om een wijziging te laten slagen; vraag het eerst aan de vader."""

import os
import tempfile
import unittest

from leeravontuur.kern import vaardigheden
from leeravontuur.kern.instellingen import Instellingen
from leeravontuur.kern.opslag import Opslag
from leeravontuur.terminal import curriculum as CU
from leeravontuur.terminal.app import App
from leeravontuur.terminal.nepscherm import NepScherm, ToetsenOp

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


if __name__ == "__main__":
    unittest.main()
