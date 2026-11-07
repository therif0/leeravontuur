"""Taal T1.1: de zin, de haakjes, de woordenlijst, de zinnenmachine en de zinsontleding (kern, zonder schermen)."""

import random
import unittest

from leeravontuur.kern import leerlijnen
from leeravontuur.kern.leerjaren import LEERJAREN
from leeravontuur.kern.taal import zinnenmachine as M
from leeravontuur.kern.taal import zinsontleding as Z
from leeravontuur.kern.taal.zinnen import GEZEGDE, WOORDSOORTEN, ZINSDELEN, ZinFout, controleer, lees_haakjes

LIJN = "taal.zinsontleding"


def zin(tekst):
    return lees_haakjes(tekst, M.soort_van)


def breedte(z):
    """Zoals op het scherm: 7 kolommen inspringen, de woorden met 2 spaties ertussen."""
    return 7 + sum(len(w.tekst) for w in z.woorden) + 2 * (len(z.woorden) - 1)


def posities(z, tekst):
    """De posities van de woorden 'tekst' (na elkaar) in de zin."""
    woorden = tekst.split()
    for i in range(len(z.woorden)):
        if [w.tekst for w in z.woorden[i:i + len(woorden)]] == woorden:
            return tuple(range(i, i + len(woorden)))
    raise AssertionError(f"{tekst!r} staat niet in {z.tekst!r}")


class TestHaakjes(unittest.TestCase):
    def test_lezen(self):
        z = zin("[bwb Morgen] [pv geeft] [ow oma] [mv haar kleinzoon] [lv een fiets].")
        self.assertEqual(z.tekst, "Morgen geeft oma haar kleinzoon een fiets.")
        self.assertEqual(z.deel("mv").tekst(z), "haar kleinzoon")
        self.assertEqual([w.soort for w in z.woorden], ["bijw", "ww", "zn", "vnw", "zn", "lidw", "zn", "lt"])
        self.assertEqual(z.deel("wwg").posities, (1,))  # geen gezegde geschreven: het wwg is de pv

    def test_gezegde_in_stukken(self):
        z = zin("[ow Oma] [pv,wwg heeft] [lv een fiets] [wwg gekocht].")
        self.assertEqual(z.deel("wwg").tekst(z), "heeft gekocht")
        self.assertEqual(z.haakjes(), "[ow Oma] [pv,wwg heeft] [lv een fiets] [wwg gekocht].")

    def test_woordsoort_meegeven(self):
        z = zin("[ow Jan/zn] [pv fietst/ww].")
        self.assertEqual([w.soort for w in z.woorden], ["zn", "ww", "lt"])

    def test_fouten_in_gewone_taal(self):
        for tekst, melding in (("[ow De juf geeft een boek.", "ontbreekt een ]"),
                               ("[xx De juf] [pv geeft].", "geen zinsdeel"),
                               ("[ow De juf] [pv geeft] [pv leest].", "precies één persoonsvorm"),
                               ("[ow De juf] geeft.", "geen persoonsvorm"),
                               ("[ow De juf] [pv geeft] een boek.", "hoort bij geen enkel zinsdeel"),
                               ("[ow De juf] [pv geeft/xyz].", "geen woordsoort"),
                               ("[ow De juf] [pv geeft] [lv ].", "heeft geen woorden"),
                               ("", "leeg")):
            with self.assertRaises(ZinFout, msg=tekst) as fout:
                zin(tekst)
            self.assertIn(melding, str(fout.exception), tekst)


class TestWoordenlijst(unittest.TestCase):
    def test_de_lijst_klopt(self):
        L = M.lijst()
        for ww in L["werkwoorden"]:
            self.assertEqual(len(ww["tt"]), 2, ww["inf"])
            self.assertEqual(len(ww["vt"]), 2, ww["inf"])
            self.assertIn(ww["hulp"], L["hulpwerkwoorden"], ww["inf"])
            self.assertTrue(set(ww["ow"]) <= set(L["onderwerpen"]), ww["inf"])
            for cat in ww.get("lv", []):
                self.assertTrue(cat == "personen" or cat in L["dingen"], (ww["inf"], cat))
            self.assertTrue(ww["tt"][1] == ww["inf"], ww["inf"])  # tt meervoud = de infinitief (wij geven)
        for cat, dingen in L["dingen"].items():
            for d in dingen:
                self.assertIn(d["lidw"], ("de", "het"), d["zn"])
                for b in d["bn"]:
                    self.assertIn(b, L["bn"], d["zn"])
        for items in L["onderwerpen"].values():
            for item in items:
                self.assertIn(item["getal"], ("ev", "mv"))
        for tekst in [*L["meewerkend"], *L["personen_lv"], *L["naamwoordelijk"],
                      *(b["tekst"] for b in L["bepalingen"])]:
            for w in M.groep(tekst):
                self.assertIn(w.soort, WOORDSOORTEN, tekst)

    def test_meewerkend_voorwerp_begint_niet_met_een_naam(self):
        """'mijn zus Noor' leest als één onderwerp: een mv begint met een lidwoord of voornaamwoord."""
        for tekst in M.lijst()["meewerkend"]:
            self.assertIn(M.groep(tekst)[0].soort, ("lidw", "vnw"), tekst)


class TestZinnenmachine(unittest.TestCase):
    def test_elke_zinsbouw_in_elk_leerjaar(self):
        for jaar in LEERJAREN:
            p = leerlijnen.parameters(LIJN, jaar)
            for zb in p["zinsbouw"]:
                for seed in range(40):
                    z = M.maak(zb, random.Random(seed), p["tijden"], p["max_woorden"])
                    self.assertLessEqual(sum(not w.leesteken for w in z.woorden), p["max_woorden"], z.tekst)
                    self.assertEqual(controleer(z), [], (jaar, zb, z.haakjes()))
                    self.assertTrue(all(w.soort in WOORDSOORTEN for w in z.woorden if not w.leesteken),
                                    z.haakjes())
                    self.assertEqual(zin(z.haakjes()).haakjes(), z.haakjes())  # terug en weer in haakjes
                    self.assertLessEqual(breedte(z), 78, z.tekst)  # past op het scherm
                    self.assertTrue(z.tekst[0].isupper() and z.tekst[-1] in ".?", z.tekst)

    def test_de_pv_past_bij_het_onderwerp_en_de_tijd(self):
        L = M.lijst()
        werkwoorden = {w["inf"]: w for w in L["werkwoorden"]}
        for seed in range(200):
            z = M.maak("ow_pv_mv_lv", random.Random(seed))
            ww = werkwoorden[z.data["ww"]]
            g = 0 if z.data["getal"] == "ev" else 1
            self.assertEqual(z.deel("pv").tekst(z), ww[z.data["tijd"]][g], z.tekst)
            z = M.maak("ow_pv_lv_vd", random.Random(seed))
            hulp = L["hulpwerkwoorden"][werkwoorden[z.data["ww"]]["hulp"]]
            self.assertEqual(z.deel("pv").tekst(z), hulp[z.data["tijd"]][0 if z.data["getal"] == "ev" else 1])
            self.assertEqual(z.woorden[-2].tekst, werkwoorden[z.data["ww"]]["vd"])

    def test_bijvoeglijk_naamwoord_met_of_zonder_e(self):
        gezien = set()
        for seed in range(400):
            z = M.maak("ow_pv_lv", random.Random(seed))
            lv = [w.tekst for w in z.woorden if z.label_van(z.woorden.index(w)) == "lv"]
            if len(lv) == 3 and lv[0] == "een":
                gezien.add(" ".join(lv))
        self.assertIn("een groot raam", gezien | {"een groot raam"})
        for groep in gezien:
            self.assertNotRegex(groep, r"^een (grote|mooie|nieuwe|dikke) (boek|raam|kaartje|huis|paard)$")

    def test_tijd_en_bepaling_passen(self):
        for seed in range(200):
            z = M.maak("bwb_pv_ow_lv", random.Random(seed))
            if z.woorden[0].tekst == "Gisteren":
                self.assertEqual(z.data["tijd"], "vt", z.tekst)
            if z.woorden[0].tekst == "Morgen":
                self.assertEqual(z.data["tijd"], "tt", z.tekst)


class TestStappenEnNakijken(unittest.TestCase):
    def test_stappen_per_leerjaar(self):
        z = M.maak("ow_pv_lv_vd", random.Random(1))
        self.assertEqual(Z.stappen(z, leerlijnen.parameters(LIJN, "4")["delen"]), ["pv", "ow"])
        self.assertEqual(Z.stappen(z, leerlijnen.parameters(LIJN, "5")["delen"]), ["pv", "ow", "lv", "mv"])
        self.assertEqual(Z.stappen(z, leerlijnen.parameters(LIJN, "6")["delen"]), ["pv", "ow", "wwg", "lv", "mv", "bwb"])
        z = M.maak("ow_pv_nwg", random.Random(1))
        self.assertIn("nwg", Z.stappen(z, leerlijnen.parameters(LIJN, "6")["delen"]))

    def test_juist_en_er_is_er_geen(self):
        z = zin("[ow De juf] [pv leest] [lv een boek].")
        self.assertTrue(Z.nakijken(z, "pv", (2,)))
        self.assertTrue(Z.nakijken(z, "lv", (3, 4)))
        self.assertTrue(Z.nakijken(z, "mv", None))  # er is geen mv: N
        self.assertFalse(Z.nakijken(z, "lv", None))

    def test_de_denkfouten(self):
        z = zin("[bwb Morgen] [pv geeft] [ow oma] [mv haar kleinzoon] [lv een fiets].")
        gevallen = [("pv", (0,), "zo_pv_eerste"),
                    ("pv", posities(z, "oma"), "zo_pv_geen_ww"),
                    ("pv", posities(z, "geeft oma"), "zo_groep_te_groot"),
                    ("ow", posities(z, "een fiets"), "zo_ow_lv"),
                    ("lv", posities(z, "oma"), "zo_ow_lv"),
                    ("lv", posities(z, "haar kleinzoon"), "zo_lv_mv"),
                    ("mv", posities(z, "een fiets"), "zo_lv_mv"),
                    ("mv", posities(z, "kleinzoon"), "zo_groep_te_klein"),
                    ("lv", posities(z, "kleinzoon een fiets"), "zo_groep_te_groot"),
                    ("mv", None, "zo_vergeten")]
        for label, gekozen, code in gevallen:
            d = Z.diagnose(z, label, gekozen)
            self.assertIsNotNone(d, (label, gekozen))
            self.assertEqual(d[0], code, (label, gekozen, d))
            self.assertIn(code, Z.DENKFOUTEN)
        z = zin("[ow Oma] [pv,wwg heeft] [lv een fiets] [wwg gekocht].")
        self.assertEqual(Z.diagnose(z, "pv", posities(z, "gekocht"))[0], "zo_pv_ander_ww")
        self.assertEqual(Z.diagnose(z, "mv", posities(z, "een fiets"))[0], "zo_vergeten")  # er is geen mv
        self.assertIsNone(Z.diagnose(z, "mv", None))

    def test_de_tips_zeggen_het_antwoord_niet(self):
        for seed in range(100):
            z = M.maak(random.Random(seed).choice(M.ZINSBOUW), random.Random(seed))
            for label in Z.stappen(z, list(ZINSDELEN)):
                antwoord = Z.verwacht(z, label)
                if not antwoord or label in GEZEGDE or label == "bwb":
                    continue
                tekst = " ".join(z.woorden[p].tekst for p in antwoord).lower()
                for tip in Z.tips(z, label):
                    self.assertNotIn(f" {tekst} ", f" {tip.lower().rstrip('?.')} ", (label, z.tekst, tip))

    def test_de_uitleg_en_de_vraag_van_school(self):
        z = zin("[bwb Morgen] [pv geeft] [ow oma] [mv haar kleinzoon] [lv een fiets].")
        self.assertEqual(Z.vraag_naar(z, "lv"), "Wat geeft oma?")
        self.assertEqual(Z.vraag_naar(z, "mv"), "Aan wie geeft oma een fiets?")
        self.assertEqual(Z.uitleg(z, "lv"), "Wat geeft oma? → *een fiets*. Dat is het lijdend voorwerp.")
        z = zin("[ow Lotte] [pv,wwg heeft] [lv de juf] [wwg geholpen].")
        self.assertEqual(Z.vraag_naar(z, "ow"), "Wie of wat heeft geholpen?")
        self.assertEqual(Z.uitleg(z, "mv"), "Deze zin heeft geen meewerkend voorwerp.")
        z = M.maak("ow_pv_lv", random.Random(3))  # papa, oma … krijgen midden in de vraag een kleine letter
        if not z.data["eerste"][:1].isupper():
            self.assertNotIn(z.woorden[0].tekst, Z.vraag_naar(z, "lv"))

    def test_vrij_kleuren(self):
        z = zin("[ow Oma] [pv,wwg heeft] [mv de kinderen] [lv een taart] [wwg gebakken].")
        markering = {0: "ow", 1: "pv", 2: "mv", 3: "mv", 4: "lv", 5: "lv", 6: "wwg"}
        uit = Z.nakijken_vrij(z, ["pv", "ow", "wwg", "lv", "mv"], markering)
        self.assertTrue(all(juist for juist, _ in uit.values()), uit)  # de pv hoort vanzelf bij het wwg
        markering[2] = markering[3] = "lv"
        uit = Z.nakijken_vrij(z, ["pv", "ow", "lv", "mv"], markering)
        self.assertFalse(uit["lv"][0])
        self.assertEqual(uit["mv"][1][0], "zo_vergeten")

    def test_in_zinsdelen_verdelen(self):
        z = zin("[bwb Morgen] [pv geeft] [ow oma] [mv haar kleinzoon] [lv een fiets].")
        self.assertEqual(Z.verdeling(z), [(0,), (1,), (2,), (3, 4), (5, 6)])
        self.assertEqual(Z.nakijken_verdeling(z, [(0,), (1,), (2,), (3, 4), (5, 6)]), (True, []))
        self.assertEqual(Z.nakijken_verdeling(z, [(0,), (1, 2), (3, 4), (5, 6)]), (False, [(1, 2)]))
        z = zin("[ow Oma] [pv,wwg heeft] [lv een fiets] [wwg gekocht].")
        self.assertEqual(Z.verdeling(z), [(0,), (1,), (2, 3), (4,)])


if __name__ == "__main__":
    unittest.main()
