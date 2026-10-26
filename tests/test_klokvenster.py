"""Het klokvenster: de vormen van de klok, het praten met het proces, en terugvallen als er geen venster kan."""

import curses
import math
import os
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

from leeravontuur.terminal.scherm import Scherm
from leeravontuur.terminal.venster import Klokvenster
from leeravontuur.venster import klokbeeld as K
from leeravontuur.venster import klokvenster as KV

# een nep-venster: zegt klaar, en antwoordt op elke 'toon' met een Enter en een klik
NEP = """
import json, sys
print(json.dumps({"klaar": True}), flush=True)
for regel in sys.stdin:
    b = json.loads(regel)
    if b.get("doe") == "toon":
        print(json.dumps({"toets": "Enter"}), flush=True)
        print(json.dumps({"klik": [12.5, -3]}), flush=True)
    if b.get("doe") == "stop":
        break
"""


def hoek(v):
    return math.degrees(math.atan2(v["x2"] - v["x1"], -(v["y2"] - v["y1"]))) % 360


class TestKlokbeeld(unittest.TestCase):
    def test_wijzers_op_de_juiste_plek(self):
        for t in range(0, 720, 7):
            wijzers = {v["rol"]: v for v in K.vormen(t) if v.get("rol") and not v["streep"]}
            uur, minuut = K.hoeken(t)
            self.assertAlmostEqual(hoek(wijzers["uur"]), uur % 360, delta=0.5)
            self.assertAlmostEqual(hoek(wijzers["minuut"]), minuut % 360, delta=0.5)
            lengte = {r: math.hypot(v["x2"] - v["x1"], v["y2"] - v["y1"]) for r, v in wijzers.items()}
            self.assertLess(lengte["uur"], lengte["minuut"])  # de korte wijzer is het uur
            self.assertGreater(wijzers["uur"]["dikte"], wijzers["minuut"]["dikte"])  # en dikker

    def test_alle_cijfers_en_minuten(self):
        teksten = {v["tekst"] for v in K.vormen(0) if v["soort"] == "tekst"}
        self.assertTrue({str(u) for u in range(1, 13)} <= teksten)
        self.assertTrue({"05", "30", "55"} <= teksten)

    def test_zo_moest_het(self):
        self.assertFalse(any(v.get("streep") for v in K.vormen(100, juist=100)))
        groen = [v for v in K.vormen(100, juist=460, uitslag="fout") if v.get("streep")]
        self.assertEqual(len(groen), 2)
        self.assertTrue(all(v["kleur"] == K.KLEUR["juist"] for v in groen))
        self.assertEqual(K.vormen(100, uitslag="fout")[0]["lijn"], K.KLEUR["fout"])

    def test_svg(self):
        svg = K.naar_svg(K.vormen(205, juist=460, uitslag="fout"), onder=[("✘ zo moest het", "fout")], titel="x")
        boom = ET.fromstring(svg)
        self.assertTrue(boom.tag.endswith("svg"))


class TestPlek(unittest.TestCase):
    """Het venster mag de oefening nooit bedekken."""

    def test_rechtsboven_nooit_over_de_tekst(self):
        # het ergste geval: een terminal van 80 kolommen over het hele scherm; de tekst blijft links van kolom 60
        for breed, hoog in ((1024, 600), (1280, 720), (1366, 728), (1920, 1040), (2560, 1400), (3840, 2100)):
            x, y, b, h = KV.kies_plek((0, 0, breed, hoog))
            with self.subTest(breed=breed):
                self.assertGreaterEqual(x, breed * 60 / 80 - 1)
                self.assertLessEqual(x + b, breed)
                self.assertLessEqual(y + h, hoog)

    def test_naast_de_terminal(self):
        werk = (0, 0, 1920, 1040)
        x, y, b, h = KV.kies_plek(werk, terminal=(100, 200, 900, 700))
        self.assertGreaterEqual(x, 900)  # rechts ernaast
        self.assertEqual(y, 200)
        x, y, b, h = KV.kies_plek(werk, terminal=(1000, 100, 1900, 700))
        self.assertLessEqual(x + b, 1000)  # rechts is geen plaats: links ernaast
        x, y, b, h = KV.kies_plek(werk, terminal=(0, 0, 1920, 1040))
        self.assertGreaterEqual(x, 1920 * 0.75 - 1)  # volle scherm: rechtsboven

    def test_bewaarde_plek(self):
        werk = (0, 0, 1920, 1040)
        self.assertEqual(KV.kies_plek(werk, bewaard=[10, 20, 300, 390]), (10, 20, 300, 390))
        # niet (meer) op het scherm, of rommel: dan de gewone plek
        for raar in ([1800, 20, 300, 390], [10, 900, 300, 390], "x", [1, 2], [None, 1, 2, 3]):
            self.assertEqual(KV.kies_plek(werk, bewaard=raar), KV.kies_plek(werk), raar)

    def test_geometrie(self):
        self.assertEqual(KV.lees_geometrie("320x416+1030+16"), (1030, 16, 320, 416))
        self.assertEqual(KV.lees_geometrie("300x400+-8+-30"), (-8, -30, 300, 400))
        self.assertIsNone(KV.lees_geometrie("rommel"))


class TestToetsenUitHetVenster(unittest.TestCase):
    def test_vertaling(self):
        van = Scherm._van_venster
        self.assertEqual(van({"toets": "Enter"}), 10)
        self.assertEqual(van({"toets": "Escape"}), 27)
        self.assertEqual(van({"toets": "Left"}), curses.KEY_LEFT)
        self.assertEqual(van({"toets": "BackSpace"}), curses.KEY_BACKSPACE)
        self.assertEqual(van({"toets": "a"}), "a")
        self.assertEqual(van({"klik": [3, -4]}), ("wijzer", 3.0, -4.0))
        self.assertEqual(van({"dicht": True}), curses.KEY_RESIZE)
        for raar in (None, {}, {"toets": "F13"}, {"toets": 5}, {"klik": "x"}, {"klik": [1]}, {"iets": 1}):
            self.assertIsNone(van(raar), raar)


class TestBeheerder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        patch = mock.patch.dict(os.environ, {"LEERAVONTUUR_DATA": self.tmp.name})
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(self.tmp.cleanup)

    def wacht_op(self, kv, n, s=5.0):
        uit, eind = [], time.time() + s
        while len(uit) < n and time.time() < eind:
            b = kv.volgende()
            if b is None:
                time.sleep(0.02)
            else:
                uit.append(b)
        return uit

    def test_praten_met_het_proces(self):
        kv = Klokvenster()
        kv.OPDRACHT = ["-c", NEP]
        self.addCleanup(kv.stop)
        self.assertTrue(kv.toon(205, "Hoe laat is het?"))
        self.assertTrue(kv.toon(205, "Hoe laat is het?"))  # niets veranderd: niets opnieuw sturen
        berichten = self.wacht_op(kv, 2)
        self.assertEqual(berichten, [{"toets": "Enter"}, {"klik": [12.5, -3]}])
        self.assertEqual(self.wacht_op(kv, 1, 0.3), [])
        kv.nieuw_beeld()
        kv.beeld_klaar()  # geen klok meer in beeld: verbergen
        self.assertFalse(kv.zichtbaar)
        p = kv.proc
        kv.stop()
        self.assertIsNotNone(p.poll())  # het proces is gestopt

    def test_proces_stopt_dan_klok_in_de_terminal(self):
        kv = Klokvenster()
        kv.OPDRACHT = ["-c", "import json; print(json.dumps({'klaar': True}), flush=True)"]
        self.addCleanup(kv.stop)
        kv.toon(205)
        self.assertEqual(self.wacht_op(kv, 1), [{"dicht": True}])  # opnieuw tekenen …
        self.assertFalse(kv.toon(205))  # … met de klok in de terminal

    def test_geen_start(self):
        kv = Klokvenster()
        kv.OPDRACHT = ["-c", "import json; print(json.dumps({'fout': 'geen tkinter'}), flush=True)"]
        self.addCleanup(kv.stop)
        self.assertFalse(kv.toon(205))
        self.assertEqual(kv.kapot, "geen tkinter")
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "fouten.log")))  # gewoon, geen fout

    @unittest.skipUnless(sys.platform.startswith("linux"), "zonder beeldscherm proberen kan alleen op Linux")
    def test_het_echte_venster_zonder_beeldscherm(self):
        with mock.patch.dict(os.environ, {"DISPLAY": "", "WAYLAND_DISPLAY": ""}):
            kv = Klokvenster()
            self.addCleanup(kv.stop)
            self.assertFalse(kv.toon(205))  # geen tkinter of geen beeldscherm: de terminal tekent de klok
            self.assertTrue(kv.kapot)


if __name__ == "__main__":
    unittest.main()
