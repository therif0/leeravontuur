"""Taal T1.1: de zin, de haakjes, de woordenlijst, de zinnenmachine en de zinsontleding (kern, zonder schermen)."""

import random
import unittest

from leeravontuur.kern import leerlijnen
from leeravontuur.kern.leerjaren import LEERJAREN
from leeravontuur.kern.taal import zinnenmachine as M
from leeravontuur.kern.taal import zinsontleding as Z
from leeravontuur.kern.taal import zinnen as ZN
from leeravontuur.kern.taal.zinnen import GEZEGDE, WOORDSOORTEN, ZINSDELEN, ZinFout, controleer, lees_haakjes

LIJN = "taal.zinsontleding"


def zin(tekst):
    return lees_haakjes(tekst, M.soort_van)


def breedte(z):
    """Zoals op het scherm: 7 kolommen inspringen, de woorden met 2 spaties ertussen (een leesteken tegen het woord)."""
    return 7 + ZN.breedte(z)


def posities(z, tekst):
    """De posities van de woorden 'tekst' (na elkaar) in de zin."""
    woorden = tekst.split()
    for i in range(len(z.woorden)):
        if [w.tekst for w in z.woorden[i:i + len(woorden)]] == woorden:
            return tuple(range(i, i + len(woorden)))
    raise AssertionError(f"{tekst!r} staat niet in {z.tekst!r}")


class TestHaakjes(unittest.TestCase):
    def test_lezen(self):
        z = zin("[bwb Morgen] [pv geeft] [o oma] [mv haar kleinzoon] [lv een fiets].")
        self.assertEqual(z.tekst, "Morgen geeft oma haar kleinzoon een fiets.")
        self.assertEqual(z.deel("mv").tekst(z), "haar kleinzoon")
        self.assertEqual([w.soort for w in z.woorden], ["bijw", "ww", "zn", "vnw", "zn", "lidw", "zn", "lt"])
        self.assertEqual(z.deel("wwg").posities, (1,))  # geen gezegde geschreven: het wwg is de pv

    def test_gezegde_in_stukken(self):
        z = zin("[o Oma] [pv,wwg heeft] [lv een fiets] [wwg gekocht].")
        self.assertEqual(z.deel("wwg").tekst(z), "heeft gekocht")
        self.assertEqual(z.haakjes(), "[o Oma] [pv,wwg heeft] [lv een fiets] [wwg gekocht].")

    def test_woordsoort_meegeven(self):
        z = zin("[o Jan/zn] [pv fietst/ww].")
        self.assertEqual([w.soort for w in z.woorden], ["zn", "ww", "lt"])

    def test_fouten_in_gewone_taal(self):
        for tekst, melding in (("[o De juf geeft een boek.", "ontbreekt een ]"),
                               ("[xx De juf] [pv geeft].", "geen zinsdeel"),
                               ("[o De juf] [pv geeft] [lv een boek] en [pv leest].", "alleen pv en o"),
                               ("[o De juf] [pv geeft] | en [pv leest].", "precies één onderwerp"),
                               ("[o De juf] [pv geeft] | een boek.", "eigen persoonsvorm"),
                               ("[o De juf] geeft.", "geen persoonsvorm"),
                               ("[o De juf] [pv geeft] een boek.", "hoort bij geen enkel zinsdeel"),
                               ("[o De juf] [pv geeft/xyz].", "geen woordsoort"),
                               ("[o De juf] [pv geeft] [lv ].", "heeft geen woorden"),
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
            self.assertTrue(set(ww["o"]) <= set(L["onderwerpen"]), ww["inf"])
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
                    z = M.maak(zb, random.Random(seed), p["tijden"], p["max_woorden"], p["zonder_lv"])
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
            z = M.maak("o_pv_mv_lv", random.Random(seed))
            ww = werkwoorden[z.data["ww"]]
            g = 0 if z.data["getal"] == "ev" else 1
            self.assertEqual(z.deel("pv").tekst(z), ww[z.data["tijd"]][g], z.tekst)
            z = M.maak("o_pv_lv_vd", random.Random(seed))
            hulp = L["hulpwerkwoorden"][werkwoorden[z.data["ww"]]["hulp"]]
            self.assertEqual(z.deel("pv").tekst(z), hulp[z.data["tijd"]][0 if z.data["getal"] == "ev" else 1])
            self.assertEqual(z.woorden[-2].tekst, werkwoorden[z.data["ww"]]["vd"])

    def test_bijvoeglijk_naamwoord_met_of_zonder_e(self):
        gezien = set()
        for seed in range(400):
            z = M.maak("o_pv_lv", random.Random(seed))
            lv = [w.tekst for w in z.woorden if z.label_van(z.woorden.index(w)) == "lv"]
            if len(lv) == 3 and lv[0] == "een":
                gezien.add(" ".join(lv))
        self.assertIn("een groot raam", gezien | {"een groot raam"})
        for groep in gezien:
            self.assertNotRegex(groep, r"^een (grote|mooie|nieuwe|dikke) (boek|raam|kaartje|huis|paard)$")

    def test_geen_weggelaten_lv_op_makkelijk_en_normaal(self):
        """"Oma at." alleen op Moeilijk en hoger (de vader, 7/11): op Makkelijk en Normaal krijgt een zin zonder lv
        alleen een werkwoord dat nooit een lv heeft (slapen, lachen …)."""
        werkwoorden = {w["inf"]: w for w in M.lijst()["werkwoorden"]}
        for jaar in ("3", "4", "5"):
            self.assertFalse(leerlijnen.parameters(LIJN, jaar)["zonder_lv"], jaar)
        self.assertTrue(leerlijnen.parameters(LIJN, "6")["zonder_lv"])
        gezien = set()
        for seed in range(200):
            z = M.maak("o_pv", random.Random(seed), lv_weglaten=False)
            self.assertNotIn("lv", werkwoorden[z.data["ww"]], z.tekst)
            gezien.add(z.data["ww"])
        self.assertGreater(len(gezien), 5)
        weg = {M.maak("o_pv", random.Random(s)).data["ww"] for s in range(300)}
        self.assertTrue(weg & {"eten", "lezen", "tekenen"})  # op Moeilijk mag het wel

    def test_tijd_en_bepaling_passen(self):
        for seed in range(200):
            z = M.maak("bwb_pv_o_lv", random.Random(seed))
            if z.woorden[0].tekst == "Gisteren":
                self.assertEqual(z.data["tijd"], "vt", z.tekst)
            if z.woorden[0].tekst == "Morgen":
                self.assertEqual(z.data["tijd"], "tt", z.tekst)


class TestStappenEnNakijken(unittest.TestCase):
    def test_stappen_per_leerjaar(self):
        z = M.maak("o_pv_lv_vd", random.Random(1))
        self.assertEqual(Z.stappen(z, leerlijnen.parameters(LIJN, "4")["delen"]), ["pv", "o"])
        self.assertEqual(Z.stappen(z, leerlijnen.parameters(LIJN, "5")["delen"]), ["pv", "o", "lv", "mv"])
        self.assertEqual(Z.stappen(z, leerlijnen.parameters(LIJN, "6")["delen"]), ["pv", "o", "wwg", "lv", "mv", "bwb"])
        z = M.maak("o_pv_nwg", random.Random(1))
        self.assertIn("nwg", Z.stappen(z, leerlijnen.parameters(LIJN, "6")["delen"]))

    def test_juist_en_er_is_er_geen(self):
        z = zin("[o De juf] [pv leest] [lv een boek].")
        self.assertTrue(Z.nakijken(z, "pv", (2,)))
        self.assertTrue(Z.nakijken(z, "lv", (3, 4)))
        self.assertTrue(Z.nakijken(z, "mv", None))  # er is geen mv: N
        self.assertFalse(Z.nakijken(z, "lv", None))

    def test_de_denkfouten(self):
        z = zin("[bwb Morgen] [pv geeft] [o oma] [mv haar kleinzoon] [lv een fiets].")
        gevallen = [("pv", (0,), "zo_pv_eerste"),
                    ("pv", posities(z, "oma"), "zo_pv_geen_ww"),
                    ("pv", posities(z, "geeft oma"), "zo_groep_te_groot"),
                    ("o", posities(z, "een fiets"), "zo_o_lv"),
                    ("lv", posities(z, "oma"), "zo_o_lv"),
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
        z = zin("[o Oma] [pv,wwg heeft] [lv een fiets] [wwg gekocht].")
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
        z = zin("[bwb Morgen] [pv geeft] [o oma] [mv haar kleinzoon] [lv een fiets].")
        self.assertEqual(Z.vraag_naar(z, "lv"), "Wat geeft oma?")
        self.assertEqual(Z.vraag_naar(z, "mv"), "Aan wie geeft oma een fiets?")
        self.assertEqual(Z.uitleg(z, "lv"), "Wat geeft oma? → ‘een fiets’. Dat is het lijdend voorwerp.")
        z = zin("[o Lotte] [pv,wwg heeft] [lv de juf] [wwg geholpen].")
        self.assertEqual(Z.vraag_naar(z, "o"), "Wie of wat heeft geholpen?")
        self.assertEqual(Z.uitleg(z, "mv"), "Deze zin heeft geen meewerkend voorwerp.")
        z = M.maak("o_pv_lv", random.Random(3))  # papa, oma … krijgen midden in de vraag een kleine letter
        if not z.data["eerste"][:1].isupper():
            self.assertNotIn(z.woorden[0].tekst, Z.vraag_naar(z, "lv"))

    def test_vrij_kleuren(self):
        z = zin("[o Oma] [pv,wwg heeft] [mv de kinderen] [lv een taart] [wwg gebakken].")
        markering = {0: "o", 1: "pv", 2: "mv", 3: "mv", 4: "lv", 5: "lv", 6: "wwg"}
        uit = Z.nakijken_vrij(z, ["pv", "o", "wwg", "lv", "mv"], markering)
        self.assertTrue(all(juist for juist, _ in uit.values()), uit)  # de pv hoort vanzelf bij het wwg
        markering[2] = markering[3] = "lv"
        uit = Z.nakijken_vrij(z, ["pv", "o", "lv", "mv"], markering)
        self.assertFalse(uit["lv"][0])
        self.assertEqual(uit["mv"][1][0], "zo_vergeten")

    def test_in_zinsdelen_verdelen(self):
        z = zin("[bwb Morgen] [pv geeft] [o oma] [mv haar kleinzoon] [lv een fiets].")
        self.assertEqual(Z.verdeling(z), [(0,), (1,), (2,), (3, 4), (5, 6)])
        self.assertEqual(Z.nakijken_verdeling(z, [(0,), (1,), (2,), (3, 4), (5, 6)]), (True, []))
        self.assertEqual(Z.nakijken_verdeling(z, [(0,), (1, 2), (3, 4), (5, 6)]), (False, [(1, 2)]))
        z = zin("[o Oma] [pv,wwg heeft] [lv een fiets] [wwg gekocht].")
        self.assertEqual(Z.verdeling(z), [(0,), (1,), (2, 3), (4,)])


class TestNagekekenZinnen(unittest.TestCase):
    """0.25.1: de met de hand geschreven zinnen (inhoud/taal/zinnen.json)."""

    def test_elke_zin_is_volledig_ontleed_en_past(self):
        from leeravontuur.kern.taal import nagekeken as N
        self.assertGreaterEqual(sum(len(N.zinnen(j)) for j in N.JAREN), 40)
        for jaar in N.JAREN:
            self.assertGreaterEqual(len(N.zinnen(jaar)), 10, jaar)
            for z in N.zinnen(jaar):
                self.assertFalse(z.samengesteld, z.tekst)
                self.assertEqual(controleer(z), [], z.haakjes())
                self.assertLessEqual(ZN.breedte(z), ZN.BREEDTE, z.tekst)
                self.assertTrue(z.tekst[0].isupper() and z.tekst[-1] in ".?", z.tekst)
                self.assertIn(z.data["tijd"], ("tt", "vt"), z.tekst)
                self.assertTrue(z.data["pv_andere_tijd"], z.tekst)  # voor de tijdproef
                self.assertTrue(z.deel("o"), z.tekst)
                if z.deel("mv"):
                    self.assertIn(z.data["mv_vz"], ("aan", "voor"), z.tekst)
                for label in ("pv", "o", "lv", "mv"):  # de vraag van school lukt bij elke zin
                    if z.deel(label):
                        self.assertTrue(Z.vraag_naar(z, label).endswith("?"), z.tekst)
                        self.assertIn("‘", Z.uitleg(z, label))

    def test_het_leerjaar_van_de_zin_heeft_wat_er_gevraagd_wordt(self):
        from leeravontuur.kern.taal import nagekeken as N
        self.assertTrue(all(not z.deel("nwg") and len(z.alle("bwb")) <= 2 for z in N.zinnen("4")))
        self.assertTrue(any(z.deel("mv") for z in N.zinnen("5")))
        self.assertTrue(any(z.deel("nwg") for z in N.zinnen("6")))
        for z in N.zinnen("4"):  # Makkelijk verdeelt de zin eerst: elk stuk is één zinsdeel
            juist, fout = Z.nakijken_verdeling(z, Z.verdeling(z))
            self.assertTrue(juist, z.tekst)

    def test_zinnen_met_twee_persoonsvormen(self):
        from leeravontuur.kern.taal import nagekeken as N
        self.assertGreaterEqual(len(N.twee()), 20)
        for z in N.twee():
            self.assertTrue(z.samengesteld, z.tekst)
            self.assertEqual(controleer(z), [], z.haakjes())
            self.assertLessEqual(ZN.breedte(z), ZN.BREEDTE, z.tekst)
            paren = ZN.deelzinnen(z)
            self.assertEqual(len(paren), 2, z.tekst)
            self.assertTrue(all(o for _, o in paren), z.tekst)
            self.assertEqual(zin(z.haakjes()).haakjes(), z.haakjes())

    def test_een_reeks_mengt_de_lijst_en_de_machine(self):
        o = Z.ZINSONTLEDING
        for jaar, soorten in (("3", {"machine"}), ("4", {"machine", "nagekeken"}), ("5", {"machine", "nagekeken"}),
                              ("6", {"machine", "nagekeken", "twee"})):
            gezien = set()
            for seed in range(200):
                v = o.maak(jaar, rng=random.Random(seed))
                zb = v.data["zinsbouw"]
                gezien.add("twee" if zb.startswith("twee") else zb if zb == Z.NAGEKEKEN else "machine")
                self.assertEqual(o.onderwerp_van_sleutel(v.sleutel), zb)
                if v.model.samengesteld:
                    self.assertEqual((v.data["delen"], v.data["verdelen"], v.data["stap_voor_stap"]),
                                     (["pv", "o"], False, True))
            self.assertEqual(gezien, soorten, jaar)

    def test_herhalen_geeft_dezelfde_soort_zin(self):
        o = Z.ZINSONTLEDING
        for zb in (Z.NAGEKEKEN, Z.TWEE_LIJST, "twee_dat"):
            v = o.maak("6", data={"zinsbouw": zb}, rng=random.Random(1))
            self.assertEqual(v.data["zinsbouw"], zb)
            w = o.maak_herhaling(o.herhaal_data(v), "6", vermijd={v.sleutel})
            self.assertEqual(w.data["zinsbouw"], zb)
            self.assertNotEqual(w.sleutel, v.sleutel)
        v = o.maak("4", data={"zinsbouw": "twee_dat"}, rng=random.Random(1))  # niet in het 4de: een gewone zin
        self.assertFalse(v.model.samengesteld)


class TestTweePersoonsvormen(unittest.TestCase):
    """0.25.1: een zin met meer dan één pv (alleen pv en o), de stappen en de denkfouten."""
    GROOT = "[o Grootvader] [pv vertelt] | dat [o de kist] onder de grond [pv ligt]."
    EMMA = "[o Emma] [pv leest] de brief en [pv krijgt] een idee."

    def test_de_haakjes(self):
        z = zin(self.GROOT)
        self.assertTrue(z.samengesteld)
        self.assertEqual(ZN.deelzinnen(z), [(1, (0,)), (8, (3, 4))])
        self.assertEqual(z.haakjes(), self.GROOT)
        e = zin(self.EMMA)  # zonder |: de twee pv's delen het onderwerp
        self.assertEqual(ZN.deelzinnen(e), [(1, (0,)), (5, (0,))])
        self.assertEqual(e.haakjes(), self.EMMA)

    def test_de_stappen_en_het_nakijken(self):
        z = zin(self.GROOT)
        self.assertEqual(Z.stappen(z, ["pv", "o", "lv", "mv"]), ["pv", "o1", "o2"])
        self.assertEqual((Z.soort("o2"), Z.soort("o"), Z.soort("pv")), ("o", "o", "pv"))
        self.assertTrue(Z.nakijken(z, "pv", (8, 1)))
        self.assertFalse(Z.nakijken(z, "pv", (1,)))
        self.assertTrue(Z.nakijken(z, "o1", (0,)))
        self.assertTrue(Z.nakijken(z, "o2", (3, 4)))
        self.assertEqual(Z.samenvatting(z, ["pv", "o"]), "pv vertelt · o grootvader | pv ligt · o de kist")
        self.assertEqual(Z.naam_van_stap(z, "o2"), "o bij ‘ligt’")
        self.assertEqual(Z.kort(z, "pv", (1, 8)), "vertelt, ligt")

    def test_de_denkfouten(self):
        z = zin(self.GROOT)
        self.assertEqual(Z.diagnose(z, "pv", (1,))[0], "zo_pv_een_vergeten")
        self.assertIn("twee persoonsvormen", Z.diagnose(z, "pv", (8,))[1])
        self.assertEqual(Z.diagnose(z, "pv", (1, 5, 8))[0], "zo_pv_geen_ww")  # onder
        self.assertEqual(Z.diagnose(z, "pv", (1, 4, 8))[0], "zo_pv_te_veel")  # kist (staat niet in de woordenlijst)
        self.assertEqual(Z.diagnose(z, "o2", (0,))[0], "zo_o_andere_pv")
        self.assertIn("wie of wat ligt?", Z.diagnose(z, "o2", (0,))[1])
        self.assertEqual(Z.diagnose(z, "o2", (4,))[0], "zo_groep_te_klein")
        self.assertEqual(Z.diagnose(z, "o2", (3, 4, 5))[0], "zo_groep_te_groot")
        self.assertIsNone(Z.diagnose(z, "o2", (3, 4)))
        staan = zin("[o Noor] [pv blijft] staan/ww en [pv kijkt] rond.")
        self.assertEqual(Z.diagnose(staan, "pv", (1, 2, 4))[0], "zo_pv_ander_ww")
        self.assertIsNone(Z.diagnose(zin(self.EMMA), "o2", (0,)))  # hetzelfde onderwerp: juist

    def test_tips_en_uitleg(self):
        z = zin(self.GROOT)
        for label in Z.stappen(z, ["pv", "o"]):
            tips = Z.tips(z, label)
            self.assertEqual(len(tips), 2)
            for woord in ("Grootvader", "kist") if label != "pv" else ("vertelt", "ligt"):
                self.assertNotIn(woord, " ".join(tips), label)  # de tip zegt het antwoord niet
        self.assertIn("‘vertelt’ en ‘ligt’", Z.uitleg(z, "pv"))
        self.assertIn("Wie of wat ligt? → ‘de kist’", Z.uitleg(z, "o2"))

    def test_vrij_kleuren(self):
        z = zin(self.GROOT)
        goed = {1: "pv", 8: "pv", 0: "o", 3: "o", 4: "o"}
        self.assertTrue(all(juist for juist, _ in Z.nakijken_vrij(z, ["pv", "o"], goed).values()))
        een = Z.nakijken_vrij(z, ["pv", "o"], {1: "pv", 0: "o", 3: "o", 4: "o"})
        self.assertEqual((een["pv"][0], een["pv"][1][0]), (False, "zo_pv_een_vergeten"))
        half = Z.nakijken_vrij(z, ["pv", "o"], {1: "pv", 8: "pv", 0: "o", 4: "o"})
        self.assertEqual((half["o1"][0], half["o2"][0]), (True, False))

    def test_de_machine(self):
        for zb in M.SAMENGESTELD:
            for seed in range(60):
                z = M.maak_samengesteld(zb, random.Random(seed))
                self.assertEqual(controleer(z), [], z.haakjes())
                self.assertLessEqual(ZN.breedte(z), ZN.BREEDTE, z.tekst)
                paren = ZN.deelzinnen(z)
                self.assertEqual(len(paren), 2, z.tekst)
                self.assertEqual(paren[0][1] == paren[1][1], zb == "twee_samen", z.haakjes())
                self.assertTrue(all(w.soort in WOORDSOORTEN for w in z.woorden if not w.leesteken), z.haakjes())
                self.assertEqual(zin(z.haakjes()).haakjes(), z.haakjes())
                self.assertTrue(z.tekst[0].isupper() and z.tekst.endswith("."), z.tekst)
                self.assertEqual(z.tekst.count(","), 1 if zb == "twee_terwijl_voor" else 0, z.tekst)

    def test_een_gewone_zin_verandert_niet(self):
        z = zin("[o De juf] [pv leest] [lv een boek].")
        self.assertFalse(z.samengesteld)
        self.assertEqual(Z.stappen(z, ["pv", "o", "lv", "mv"]), ["pv", "o", "lv", "mv"])
        self.assertEqual(ZN.breedte(z), len("De  juf  leest  een  boek."))


if __name__ == "__main__":
    unittest.main()
