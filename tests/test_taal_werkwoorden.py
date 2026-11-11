"""Taal T3 (0.26): Werkwoordspelling. De werkwoordenlijst tegenover de regels, de zin met het gat, het denkschema in
stappen, de denkfouten, en het scherm (stappen, Tab, tweede kans, de spiekbrief)."""

import curses
import os
import random
import unittest
from unittest import mock

from leeravontuur.kern import leerlijnen
from leeravontuur.kern.reeks import Hulp
from leeravontuur.kern.taal import werkwoorden as W
from leeravontuur.terminal import werkwoord as WS
from leeravontuur.terminal.nepscherm import HangtFout
try:
    from .test_schermen import ESC, F1, OK, Basis, naar
except ImportError:  # ook zo te starten: python -m unittest discover -s tests
    from test_schermen import ESC, F1, OK, Basis, naar

TAB = "\t"
TT, VT = W.TEGENWOORDIGE_TIJD, W.VERLEDEN_TIJD_ZWAK
STERK, VD, NAAR = W.VERLEDEN_TIJD_STERK, W.VOLTOOID_DEELWOORD, W.ZET_IN_DE_VERLEDEN_TIJD
ONDERWERPEN = (TT, VT, STERK, VD, NAAR)
JAREN = ("4", "5", "6", "m1")
VOORVOEGSELS = ("be", "ge", "ver", "ont", "her")


def zin(inf, vorm, persoon, patroon="gewoon"):
    """Een zin voor dit werkwoord met deze persoon (en dit patroon)."""
    rng = random.Random(1)
    for _ in range(50):
        z = W.maak_zin(W.ww(inf), vorm, rng, [persoon], [patroon])
        if z is not None:
            return z
    raise AssertionError(f"geen zin voor {inf} {vorm} {persoon} {patroon}")


class TestDeLijst(unittest.TestCase):
    """Elke vorm staat uitgeschreven; wat een regel volgt, rekent de test na (een tikfout in de lijst wordt rood)."""

    def test_de_velden(self):
        lijst = W.lijst()
        self.assertGreaterEqual(len(lijst), 110)
        self.assertEqual(len({w["inf"] for w in lijst}), len(lijst))  # geen werkwoord twee keer
        for w in lijst:
            inf = w["inf"]
            self.assertEqual((len(w["tt"]), len(w["vt"])), (4, 2), inf)
            self.assertEqual(w["tt"][3], inf, inf)
            self.assertIn(w["hulp"], ("hebben", "zijn"), inf)
            self.assertIn(w["niveau"], (1, 2, 3), inf)
            self.assertIn(w["vt_soort"], ("zwak", "sterk"), inf)
            self.assertIn(w["vd_soort"], ("zwak", "sterk"), inf)
            self.assertGreaterEqual(len(w["rest"]), 2, inf)
            for rest in w["rest"]:  # (zijn/haar past niet bij elk onderwerp)
                self.assertFalse({"zijn", "haar", "hun"} & set(rest.split()), (inf, rest))
            self.assertEqual(w["vd"].startswith("ge"), w["ge"] or inf.startswith("ge"), inf)
            if not w["ge"]:
                self.assertTrue(inf.startswith(VOORVOEGSELS), inf)
            for o, persoon in w.get("o", ()):
                self.assertIn(persoon, ("hij", "mv"), inf)
            for vorm in [w["stam"], *w["tt"], *w["vt"], w["vd"], *w.get("ook", ())]:
                self.assertTrue(vorm.isalpha() and vorm.islower(), (inf, vorm))

    def test_de_tegenwoordige_tijd_volgt_de_regel(self):
        anders = {w["inf"] for w in W.lijst() if w["tt"] != W.regel_tt(w)}
        self.assertEqual(anders, {"gaan", "staan", "slaan", "zijn", "hebben"})
        for w in W.lijst():
            self.assertEqual(w["tt"][0], w["stam"], w["inf"])  # de stam is de ik-vorm
            self.assertFalse(w["stam"][-1] in "vz", w["inf"])
            self.assertFalse(len(w["stam"]) > 1 and w["stam"][-1] == w["stam"][-2] and w["stam"][-1] not in "aeou",
                             w["inf"])

    def test_elke_zwakke_vorm_volgt_t_kofschip(self):
        zwak = [w for w in W.lijst() if w["vt_soort"] == "zwak"]
        self.assertGreaterEqual(len(zwak), 60)
        for w in zwak:
            self.assertEqual(w["vt"], W.regel_vt(w), w["inf"])
        for w in W.lijst():
            if w["vd_soort"] == "zwak" and w["vt_soort"] == "zwak":
                self.assertEqual(w["vd"], W.regel_vd(w), w["inf"])

    def test_een_sterk_werkwoord_volgt_de_regel_niet(self):
        for w in W.lijst():
            if w["vt_soort"] == "sterk":
                self.assertNotEqual(w["vt"], W.regel_vt(w), w["inf"])
                self.assertEqual(w["vt"][1][-2:] in ("en",) or w["vt"][1].endswith("n"), True, w["inf"])

    def test_de_regels(self):
        for inf, lt, kof in (("werken", "k", True), ("lachen", "ch", True), ("leven", "v", False),
                             ("reizen", "z", False), ("praten", "t", True), ("antwoorden", "d", False),
                             ("fietsen", "s", True), ("spelen", "l", False), ("hopen", "p", True)):
            self.assertEqual((W.letter(inf), W.in_kofschip(inf)), (lt, kof), inf)
        self.assertEqual([W.stamsoort(W.ww(i)) for i in ("werken", "praten", "worden", "leven", "reizen")],
                         ["gewoon", "t", "d", "vz", "vz"])
        self.assertEqual(W.regel_vt(W.ww("praten")), ["praatte", "praatten"])
        self.assertEqual(W.regel_vt(W.ww("verhuizen")), ["verhuisde", "verhuisden"])
        self.assertEqual([W.regel_vd(W.ww(i)) for i in ("werken", "leven", "praten", "vertellen", "antwoorden")],
                         ["gewerkt", "geleefd", "gepraat", "verteld", "geantwoord"])


class TestDeZin(unittest.TestCase):
    def test_de_vorm_past_bij_de_persoon(self):
        for persoon, vorm in (("ik", "word"), ("jij", "wordt"), ("jij_inv", "word"), ("hij", "wordt"),
                              ("mv", "worden")):
            patroon = "inversie" if persoon == "jij_inv" else "gewoon"
            z = zin("worden", "tt", persoon, patroon)
            self.assertEqual(z.antwoord, vorm, z.tekst)
            self.assertIn(W.GAT, z.zin)
            self.assertTrue(z.tekst.endswith("(worden)"))
        self.assertEqual(zin("werken", "vt", "hij").antwoord, "werkte")
        self.assertEqual(zin("werken", "vt", "mv").antwoord, "werkten")
        self.assertEqual(zin("zijn", "tt", "jij_inv", "vraag").antwoord, "ben")

    def test_de_drie_patronen(self):
        self.assertRegex(zin("fietsen", "tt", "hij", "gewoon").zin, r"^[A-Z].* ___ .*\.$")
        self.assertRegex(zin("fietsen", "tt", "hij", "inversie").zin, r"^(Vandaag|Nu|Soms) ___ .*\.$")
        vraag = zin("fietsen", "tt", "jij_inv", "vraag")
        self.assertRegex(vraag.zin, r"^___ jij .*\?$")
        self.assertTrue(vraag.vol().startswith("Fiets jij"))  # ingevuld: met een hoofdletter
        self.assertRegex(zin("fietsen", "vt", "hij").zin, r"(gisteren|vorige week|toen)")
        self.assertIsNone(W.maak_zin(W.ww("branden"), "tt", random.Random(1), ["ik"], ["gewoon"]))  # het vuur brandt

    def test_het_onderwerp_staat_niet_ook_achteraan(self):
        rng = random.Random(4)
        for inf, o in (("voetballen", "de buren"), ("bedanken", "de juf"), ("luisteren", "de juf")):
            for _ in range(200):
                z = W.maak_zin(W.ww(inf), "tt", rng)
                self.assertFalse(z.o == o and z.vol().lower().count(o) > 1, z.vol())

    def test_nakijken(self):
        z = zin("rijden", "tt", "ik")
        self.assertTrue(all(W.nakijken(z, t) for t in ("rijd", "Rijd ", "rij")))  # rij mag ook
        self.assertFalse(W.nakijken(z, "rijdt"))
        self.assertFalse(W.nakijken(zin("rijden", "tt", "hij"), "rij"))
        self.assertFalse(W.nakijken(z, ""))


class TestStappenEnDenkfouten(unittest.TestCase):
    def test_het_denkschema(self):
        z = zin("worden", "tt", "jij_inv", "inversie")
        stappen = W.stappen(z)
        self.assertEqual([s.naam for s in stappen], ["wie", "stam", "regel", "vorm"])
        self.assertEqual((stappen[0].juist, stappen[1].juist, stappen[2].juist), (1, ("word",), 0))
        self.assertIn("achter het werkwoord", stappen[2].uitleg)
        z = zin("leven", "vt", "mv")
        stappen = W.stappen(z)
        self.assertEqual([s.naam for s in stappen], ["getal", "stam", "kofschip", "vorm"])
        self.assertEqual((stappen[0].juist, stappen[1].juist, stappen[2].juist, stappen[2].kofschip),
                         (1, ("leef",), 1, "v"))
        self.assertIn("‘lev’", stappen[2].sub)
        self.assertEqual([s.naam for s in W.stappen(z, False)], ["vorm"])
        for inf, vorm in (("werken", "tt"), ("fietsen", "vt"), ("leven", "vt"), ("praten", "tt"), ("antwoorden", "vt")):
            for persoon in ("ik", "hij", "mv"):  # een tip zegt nooit de stam of de vorm
                z = zin(inf, vorm, persoon)
                for st in W.stappen(z):
                    woorden = " ".join(st.tips).replace("‘", " ").replace("’", " ").split()
                    geheim = {z.antwoord, z.ww["stam"]} - {inf}  # (het hele werkwoord staat in de vraag zelf)
                    self.assertFalse(geheim & set(woorden), (inf, st.naam, st.tips))
        self.assertEqual([s.naam for s in W.stappen(zin("zijn", "tt", "hij"))], ["vorm"])  # onregelmatig: geen regel

    def test_de_stappen_nakijken(self):
        stappen = W.stappen(zin("lopen", "tt", "hij"))
        self.assertTrue(W.nakijken_stap(stappen[0], 2) and not W.nakijken_stap(stappen[0], 0))
        self.assertTrue(W.nakijken_stap(stappen[1], " Loop ") and not W.nakijken_stap(stappen[1], "lop"))
        self.assertEqual(W.diagnose_stap(zin("lopen", "tt", "hij"), stappen[1], "lop")[0], "ws_stam_klinker")
        z = zin("pakken", "vt", "hij")
        self.assertEqual(W.diagnose_stap(z, W.stappen(z)[1], "pakk")[0], "ws_stam_dubbel")
        z = zin("leven", "vt", "hij")
        self.assertEqual(W.diagnose_stap(z, W.stappen(z)[1], "leev")[0], "ws_stam_vz")
        self.assertEqual(W.diagnose_stap(z, W.stappen(z)[2], 0)[0], "ws_kofschip_vz")
        z = zin("worden", "tt", "jij_inv", "vraag")
        self.assertEqual(W.diagnose_stap(z, W.stappen(z)[2], 1)[0], "ws_inversie")
        self.assertIsNone(W.diagnose_stap(z, W.stappen(z)[2], 0))

    def test_de_denkfouten_in_de_vorm(self):
        for inf, vorm, persoon, patroon, getypt, code in (
                ("worden", "tt", "hij", "gewoon", "word", "ws_t_vergeten"),
                ("worden", "tt", "hij", "gewoon", "wort", "ws_t_vergeten"),
                ("worden", "tt", "jij_inv", "vraag", "wordt", "ws_inversie"),
                ("worden", "tt", "ik", "gewoon", "wordt", "ws_t_te_veel"),
                ("werken", "tt", "hij", "gewoon", "werk", "ws_t_vergeten"),
                ("praten", "tt", "hij", "gewoon", "praatt", "ws_dubbele_t"),
                ("werken", "tt", "hij", "gewoon", "werken", "ws_getal"),
                ("werken", "tt", "mv", "gewoon", "werkt", "ws_getal"),
                ("leven", "tt", "hij", "gewoon", "leevt", "ws_stam_vz"),
                ("lopen", "tt", "hij", "gewoon", "lopt", "ws_stam_klinker"),
                ("werken", "tt", "hij", "gewoon", "werkte", "ws_tijd"),
                ("werken", "vt", "hij", "gewoon", "werkde", "ws_kofschip"),
                ("spelen", "vt", "hij", "gewoon", "speelte", "ws_kofschip"),
                ("leven", "vt", "hij", "gewoon", "leefte", "ws_kofschip_vz"),
                ("leven", "vt", "hij", "gewoon", "leevde", "ws_stam_vz"),
                ("reizen", "vt", "hij", "gewoon", "reizde", "ws_stam_vz"),
                ("praten", "vt", "hij", "gewoon", "praate", "ws_dubbel"),
                ("antwoorden", "vt", "mv", "gewoon", "antwoorden", "ws_dubbel"),
                ("maken", "vt", "hij", "gewoon", "makte", "ws_stam_klinker"),
                ("pakken", "vt", "hij", "gewoon", "pakkte", "ws_stam_dubbel"),
                ("werken", "vt", "hij", "gewoon", "werkten", "ws_getal"),
                ("werken", "vt", "mv", "gewoon", "werkte", "ws_getal"),
                ("werken", "vt", "hij", "gewoon", "werkt", "ws_tijd")):
            z = zin(inf, vorm, persoon, patroon)
            d = W.diagnose_vorm(z, getypt)
            self.assertIsNotNone(d, (inf, getypt))
            self.assertEqual(d[0], code, (inf, getypt, d))
            self.assertIn(code, W.DENKFOUTEN)
            self.assertNotIn(z.antwoord, d[1].split(), (inf, getypt, d[1]))  # de hint zegt het antwoord niet
        self.assertIsNone(W.diagnose_vorm(zin("werken", "tt", "hij"), "werkt"))
        self.assertIsNone(W.diagnose_vorm(zin("werken", "tt", "hij"), "xyz"))

    def test_de_uitleg(self):
        regels = W.uitleg(zin("praten", "vt", "hij"))
        self.assertIn("De stam van ‘praten’ is ‘praat’", regels[1])
        self.assertTrue(any("allebei" in r for r in regels))
        self.assertIn("praatte", regels[-1])
        self.assertIn("geen tweede t", " ".join(W.uitleg(zin("praten", "tt", "hij"))))
        self.assertIn("onregelmatig", W.uitleg(zin("zijn", "tt", "hij"))[0])


class TestElkOnderwerpInElkLeerjaar(unittest.TestCase):
    def test_de_vragen(self):
        for o in ONDERWERPEN:
            koppen = {tekst for tekst, rol in o.spiekbrief() if rol == "accent"}
            for jaar in JAREN:
                p = leerlijnen.parameters(o.id, jaar)
                self.assertGreaterEqual(len(o.kandidaten(p)), 25, (o.id, jaar))
                for seed in range(150):
                    v = o.maak(jaar, rng=random.Random(seed))
                    z = v.model
                    self.assertLessEqual(len(v.tekst), W.BREED, v.tekst)
                    self.assertEqual(v.antwoord, W.vorm_van(z.ww, z.vorm, z.persoon), v.tekst)
                    self.assertTrue(o.nakijken(v, o.lees_vraag(v, v.verwacht)), v.tekst)
                    self.assertIn(z.ww, o.kandidaten(p), v.tekst)
                    self.assertEqual(z.omzetten, o is NAAR, v.tekst)
                    if not p.get("homofoon"):
                        self.assertEqual(z.vorm, o.vorm, v.tekst)
                        self.assertIn(z.persoon, p["personen"], v.tekst)
                    self.assertEqual(o.onderwerp_van_sleutel(v.sleutel), v.data["onderwerp"])
                    self.assertTrue(v.zin_past if hasattr(v, "zin_past") else z.vol().count(W.GAT) == 0)
                    for volledig in (True, False):
                        stappen = W.stappen(z, volledig)
                        self.assertEqual(stappen[-1].naam, "vorm")
                        for i, st in enumerate(stappen):
                            kop = st.vraag if len(stappen) == 1 else f"Stap {i + 1} van {len(stappen)}: {st.vraag}"
                            self.assertLessEqual(len(kop), WS.OPDRACHT_BREED, kop)
                            self.assertLessEqual(len(st.sub), WS.OPDRACHT_BREED, st.sub)
                            self.assertEqual(len(st.tips), 2, st.naam)
                            v.data["spiek_kop"] = st.kop  # (dat doet het scherm bij F1)
                            self.assertIn(o.kop_op_spiekbrief(v), koppen, (o.id, st.naam))
                            self.assertTrue(st.uitleg)
                            if st.soort == "keuze":
                                self.assertTrue(0 <= st.juist < len(st.opties) <= 4)
                            elif st.soort == "woord":
                                self.assertEqual(z.bron.split()[st.juist].lower(), z.bron_vorm)
                            else:
                                self.assertTrue(st.juist and all(st.juist))
                    self.assertIn(z.antwoord, o.uitleg(v)[-1])

    def test_de_leerlijn(self):
        makkelijk = [TT.maak("4", rng=random.Random(s)).model for s in range(80)]
        self.assertTrue(all(z.persoon in ("ik", "hij", "mv") and z.patroon == "gewoon" for z in makkelijk))
        normaal = [TT.maak("5", rng=random.Random(s)).model for s in range(300)]
        self.assertEqual({z.persoon for z in normaal}, set(W.PERSONEN))
        self.assertEqual({W.stamsoort(z.ww) for z in normaal}, {"gewoon", "d", "t", "vz"})
        self.assertTrue(any(z.inf in ("zijn", "hebben") for z in normaal))
        self.assertTrue(all(z.inf not in ("gaan", "staan", "slaan") for z in normaal))
        self.assertTrue(TT.maak("5").data["stap_voor_stap"] and not TT.maak("6").data["stap_voor_stap"])
        self.assertEqual({W.stamsoort(VT.maak("5", rng=random.Random(s)).model.ww) for s in range(80)}, {"gewoon"})
        moeilijk = [VT.maak("6", rng=random.Random(s)).model for s in range(300)]
        self.assertEqual({W.stamsoort(z.ww) for z in moeilijk}, {"gewoon", "d", "t", "vz"})
        self.assertTrue(all(z.ww["vt_soort"] == "zwak" for z in moeilijk))

    def test_herhalen_geeft_hetzelfde_groepje(self):
        for o, groep in ((TT, "jij_inv/d"), (VT, "mv/gewoon")):
            for seed in range(20):
                v = o.maak("5", data={"onderwerp": groep}, rng=random.Random(seed))
                self.assertEqual(v.data["onderwerp"], groep, v.tekst)
            w = o.maak_herhaling(o.herhaal_data(v), "5", vermijd={v.sleutel})
            self.assertEqual(w.data["onderwerp"], groep)
        v = TT.maak("4", data={"onderwerp": "jij_inv/d"}, rng=random.Random(1))  # niet in het 4de: een gewone vraag
        self.assertEqual(W.stamsoort(v.model.ww), "gewoon")

    def test_de_spiekbrieven_passen(self):
        for o in ONDERWERPEN:
            self.assertTrue(o.spiekbrief())
            for tekst, _ in o.spiekbrief():
                self.assertLessEqual(len(tekst), 72, tekst)


class TestSterkEnVoltooidDeelwoord(unittest.TestCase):
    """0.26.1: de verleden tijd van sterke werkwoorden, het voltooid deelwoord, en verhuist of verhuisd."""

    def test_de_zin_met_het_voltooid_deelwoord(self):
        z = zin("fietsen", "vd", "hij")
        self.assertRegex(z.zin, r"^[A-Z].* heeft (gisteren|vorige week|daarnet) .* ___\.$")
        self.assertEqual((z.antwoord, z.vol().endswith("gefietst.")), ("gefietst", True))
        self.assertRegex(zin("vallen", "vd", "jij_inv", "vraag").zin, r"^Ben jij .* ___\?$")
        self.assertRegex(zin("vallen", "vd", "mv", "inversie").zin, r"^(Gisteren|Vorige week|Daarnet) zijn .* ___\.$")
        self.assertIn("vroeger", zin("wonen", "vd", "hij").zin)
        for w in W.lijst():  # geen woord dat aan het voltooid deelwoord vast geschreven wordt (opengehouden)
            for rest in w["rest"]:
                woorden = ["", *rest.split()]
                los = woorden[-1] in ("open", "vast", "weg", "buiten", "uit", "op", "af", "mee", "thuis", "los")
                self.assertFalse(los and woorden[-2] not in ("de", "het") and w["inf"] != "zijn", (w["inf"], rest))

    def test_de_stappen(self):
        self.assertEqual([s.naam for s in W.stappen(zin("lopen", "vt", "hij"))], ["getal", "vorm"])
        self.assertEqual([s.naam for s in W.stappen(zin("lopen", "vd", "hij"))], ["vorm"])
        stappen = W.stappen(zin("leven", "vd", "hij"))
        self.assertEqual([s.naam for s in stappen], ["stam", "kofschip", "vorm"])
        self.assertEqual((stappen[1].juist, stappen[1].opties[1], stappen[1].kofschip), (1, "nee: op het einde een d", "v"))
        self.assertEqual(W.kort(zin("werken", "vd", "hij"), W.stappen(zin("werken", "vd", "hij"))[1]), "'t kofschip: t")
        self.assertEqual(W.rijtje(W.ww("lopen")), "lopen – liep – gelopen")
        tips = W.stappen(zin("lopen", "vt", "hij"))[-1].tips
        self.assertIn("gelopen", tips[1])  # een stukje van het rijtje, niet het antwoord
        self.assertNotIn("liep", " ".join(tips))

    def test_de_denkfouten(self):
        for inf, vorm, persoon, getypt, code in (
                ("lopen", "vt", "hij", "loopte", "ws_sterk_zwak"),
                ("geven", "vt", "mv", "geefden", "ws_sterk_zwak"),
                ("lopen", "vt", "hij", "liepen", "ws_getal"),
                ("lopen", "vt", "mv", "liep", "ws_getal"),
                ("lopen", "vt", "hij", "loopt", "ws_tijd"),
                ("lopen", "vt", "hij", "gelopen", "ws_tijd"),
                ("werken", "vd", "hij", "gewerkd", "ws_vd_dt"),
                ("spelen", "vd", "hij", "gespeelt", "ws_vd_dt"),
                ("spelen", "vd", "hij", "speeld", "ws_vd_ge"),
                ("werken", "vd", "hij", "werkte", "ws_tijd"),
                ("vertellen", "vd", "hij", "geverteld", "ws_vd_ge_te_veel"),
                ("lopen", "vd", "hij", "geloopt", "ws_sterk_zwak"),
                ("bakken", "vd", "hij", "gebakt", "ws_sterk_zwak"),
                ("lopen", "vd", "hij", "liep", "ws_tijd"),
                ("praten", "vd", "hij", "gepraatt", "ws_dubbele_t"),
                ("leven", "vd", "hij", "geleevd", "ws_stam_vz"),
                ("maken", "vd", "hij", "gemakt", "ws_stam_klinker"),
                ("verhuizen", "vd", "hij", "verhuist", "ws_homofoon"),
                ("verhuizen", "tt", "hij", "verhuisd", "ws_homofoon")):
            z = zin(inf, vorm, persoon)
            d = W.diagnose_vorm(z, getypt)
            self.assertIsNotNone(d, (inf, getypt))
            self.assertEqual(d[0], code, (inf, getypt, d))
            self.assertIn(code, W.DENKFOUTEN)
            self.assertNotIn(z.antwoord, d[1].replace("‘", " ").replace("’", " ").split(), (inf, getypt, d[1]))
        self.assertIsNone(W.diagnose_vorm(zin("lopen", "vt", "hij"), "liep"))

    def test_de_uitleg(self):
        self.assertIn("lopen – liep – gelopen", W.uitleg(zin("lopen", "vt", "mv"))[0])
        self.assertIn("liepen", W.uitleg(zin("lopen", "vt", "mv"))[-1])
        self.assertTrue(any("geen ge-" in r for r in W.uitleg(zin("vertellen", "vd", "hij"))))
        self.assertTrue(any("geen tweede t" in r for r in W.uitleg(zin("praten", "vd", "hij"))))
        self.assertFalse(any("tweede" in r for r in W.uitleg(zin("werken", "vd", "hij"))))

    def test_de_leerlijn(self):
        makkelijk = [VD.maak("4", rng=random.Random(s)).model.ww for s in range(80)]
        self.assertTrue(all(w["vd_soort"] == "zwak" and w["ge"] and w["niveau"] == 1 for w in makkelijk))
        normaal = [VD.maak("5", rng=random.Random(s)).model.ww for s in range(300)]
        self.assertEqual({w["vd_soort"] for w in normaal}, {"zwak", "sterk"})
        self.assertTrue(all(w["ge"] for w in normaal))
        self.assertTrue(all(w["niveau"] == 1 for w in normaal if w["vd_soort"] == "sterk"))
        moeilijk = [VD.maak("6", rng=random.Random(s)).model.ww for s in range(300)]
        self.assertTrue(any(not w["ge"] for w in moeilijk))
        self.assertTrue(all(z.ww["vt_soort"] == "sterk" and z.ww["niveau"] == 1 and not z.meervoud
                            for z in (STERK.maak("4", rng=random.Random(s)).model for s in range(80))))
        self.assertTrue(STERK.maak("5").data["stap_voor_stap"] and not STERK.maak("6").data["stap_voor_stap"])

    def test_een_sterk_werkwoord_komt_terug_in_een_andere_zin(self):
        for o, groep in ((STERK, "ev/lopen"), (VD, "vd/geven")):
            v = o.maak("5", data={"onderwerp": groep}, rng=random.Random(1))
            self.assertEqual((v.model.inf, v.data["onderwerp"]), (groep.split("/")[1], groep))
            anders = {o.maak_herhaling(o.herhaal_data(v), "5", vermijd={v.sleutel}).tekst for _ in range(10)}
            self.assertTrue(anders - {v.tekst})
        v = VD.maak("5", data={"onderwerp": "vd/t"}, rng=random.Random(1))
        self.assertEqual(W.stamsoort(v.model.ww), "t")

    def test_verhuist_of_verhuisd_op_heel_moeilijk(self):
        self.assertEqual({w["inf"] for w in W.lijst() if W.homofoon(w)},
                         {"betalen", "vertellen", "herhalen", "verdienen", "veranderen", "gebeuren", "verhuizen",
                          "beloven", "geloven"})
        vragen = [TT.maak("m1", rng=random.Random(s)) for s in range(300)]
        paar = [v for v in vragen if W.homofoon(v.model.ww) and v.model.persoon in ("jij", "hij")]
        self.assertTrue(90 <= len(paar) <= 160, len(paar))  # ongeveer 4 van de 10
        self.assertEqual({v.model.vorm for v in paar}, {"tt", "vd"})
        for v in paar:
            self.assertEqual(v.antwoord[-1], "d" if v.model.vorm == "vd" else "t", v.tekst)
        self.assertTrue(all(v.model.vorm == "tt" for v in (TT.maak("6", rng=random.Random(s)) for s in range(100))))
        vd = next(v for v in paar if v.model.vorm == "vd")
        self.assertEqual(TT.maak_herhaling(TT.herhaal_data(vd), "m1").model.vorm, "vd")
        self.assertEqual(TT.maak_herhaling(TT.herhaal_data(vd), "5").model.vorm, "tt")  # niet in het 5de


class TestZetInDeVerledenTijd(unittest.TestCase):
    """0.26.2: een zin in de tegenwoordige tijd; de pv zoeken en in de verleden tijd zetten."""

    def omzet(self, inf, persoon, patroon="gewoon"):
        rng = random.Random(1)
        return next(z for z in (W.maak_zin(W.ww(inf), "vt", rng, [persoon], [patroon], True) for _ in range(50)) if z)

    def test_de_zin(self):
        z = self.omzet("fietsen", "hij")
        self.assertTrue(z.omzetten)
        self.assertRegex(z.bron, r"^[A-Z].* fietst (in het park|met de buren)\.$")
        self.assertEqual((z.bron_vorm, z.antwoord, z.bron.split()[z.pv_plek]), ("fietst", "fietste", "fietst"))
        self.assertEqual(z.tekst, z.bron + " → verleden tijd")
        self.assertTrue(z.vol().replace("fietste", "fietst") == z.bron)  # alleen de pv verandert
        for woord in (*W.TT_WOORDEN, *W.VT_WOORDEN):  # geen tijdwoord dat maar in één tijd past
            self.assertNotIn(woord, z.bron.lower().split())
        inv = self.omzet("lopen", "mv", "inversie")
        self.assertEqual((inv.bron.split()[inv.pv_plek], inv.antwoord), ("lopen", "liepen"))
        vraag = self.omzet("worden", "jij_inv", "vraag")
        self.assertEqual((vraag.pv_plek, vraag.bron.split()[0], vraag.antwoord), (0, "Word", "werd"))
        self.assertTrue(vraag.vol().startswith("Werd jij"))

    def test_de_stappen(self):
        z = self.omzet("fietsen", "hij")
        stappen = W.stappen(z)
        self.assertEqual([(s.naam, s.soort) for s in stappen], [("pv", "woord"), ("soort", "keuze"), ("vorm", "typ")])
        self.assertEqual((stappen[0].juist, stappen[1].juist), (z.pv_plek, 0))
        self.assertTrue(W.nakijken_stap(stappen[0], z.pv_plek) and not W.nakijken_stap(stappen[0], 0))
        self.assertEqual(W.diagnose_stap(z, stappen[0], 0)[0], "ws_pv")
        self.assertEqual(W.diagnose_stap(z, stappen[1], 1)[0], "ws_soort")
        self.assertEqual((W.kort(z, stappen[0]), W.kort(z, stappen[1])), ("pv: fietst", "zwak"))
        sterk = self.omzet("lopen", "hij")
        self.assertEqual(W.stappen(sterk)[1].juist, 1)
        self.assertIn("lopen – liep – gelopen", W.stappen(sterk)[1].uitleg)
        self.assertEqual([s.naam for s in W.stappen(z, False)], ["vorm"])
        self.assertNotIn("(van", W.stappen(self.omzet("lopen", "mv"))[0].uitleg)  # de pv is het hele werkwoord

    def test_de_denkfouten_en_de_uitleg(self):
        z = self.omzet("fietsen", "hij")
        self.assertEqual(W.diagnose_vorm(z, "fietst"), ("ws_tijd", W._NOG_TT))
        self.assertEqual(W.diagnose_vorm(z, "fietsde")[0], "ws_kofschip")
        self.assertEqual(W.diagnose_vorm(self.omzet("lopen", "hij"), "loopte")[0], "ws_sterk_zwak")
        self.assertEqual(W.diagnose_vorm(self.omzet("lopen", "hij"), "loopt")[0], "ws_tijd")
        regels = W.uitleg(z)
        self.assertIn("De persoonsvorm is ‘fietst’ (van ‘fietsen’).", regels[0])
        self.assertTrue(any("‘fiets’ + te" in r for r in regels))
        self.assertIn("fietste", regels[-1])
        self.assertTrue(any("lopen – liep – gelopen" in r for r in W.uitleg(self.omzet("lopen", "hij"))))

    def test_de_leerlijn(self):
        makkelijk = [NAAR.maak("4", rng=random.Random(s)).model for s in range(80)]
        self.assertTrue(all(z.ww["vt_soort"] == "zwak" and z.patroon == "gewoon" for z in makkelijk))
        normaal = [NAAR.maak("5", rng=random.Random(s)) for s in range(300)]
        sterk = sum(v.model.ww["vt_soort"] == "sterk" for v in normaal)
        self.assertTrue(110 <= sterk <= 190, sterk)  # ongeveer even vaak zwak als sterk
        self.assertEqual({v.data["onderwerp"].split("/")[0] for v in normaal}, {"zwak", "sterk"})
        self.assertTrue(NAAR.maak("5").data["stap_voor_stap"] and not NAAR.maak("6").data["stap_voor_stap"])
        for groep in ("sterk/lopen", "zwak/t"):
            v = NAAR.maak("5", data={"onderwerp": groep}, rng=random.Random(1))
            self.assertEqual(v.data["onderwerp"], groep)
            self.assertEqual(NAAR.maak_herhaling(NAAR.herhaal_data(v), "5", vermijd={v.sleutel}).data["onderwerp"], groep)
        v = NAAR.maak("4", data={"onderwerp": "sterk/lopen"}, rng=random.Random(1))  # niet in het 4de: een zwak ww
        self.assertEqual(v.model.ww["vt_soort"], "zwak")


FIETS = W.WwZin("Gisteren", "Noor in het park.", "fietsen", "vt", "hij", "Noor", "fietste", "inversie")
WORD = W.WwZin("", "jij snel moe?", "worden", "tt", "jij_inv", "jij", "word", "vraag")
LIEP = W.WwZin("Gisteren", "Noor in het park.", "lopen", "vt", "hij", "Noor", "liep", "inversie")
NU = W.WwZin("Daarna", "Noor in het park.", "fietsen", "vt", "hij", "Noor", "fietste", "inversie", True)
GEFIETST = W.WwZin("Noor heeft gisteren in het park", ".", "fietsen", "vd", "hij", "Noor", "gefietst", "gewoon")
FIETS_JUIST = ["1", *"fiets", OK, "j", *"fietste", OK]


def vaste_zin(z):
    """Elke vraag is deze zin (zodat de test weet welke toetsen juist zijn)."""
    return mock.patch.object(W, "maak_zin", side_effect=lambda *a, **k: z)


class TestHetScherm(Basis):
    def speel_zin(self, z, toetsen, niveau=OK, **opties):
        o = NAAR if z.omzetten else TT if z.vorm == "tt" else VD if z.vorm == "vd" else \
            STERK if z.ww["vt_soort"] == "sterk" else VT
        with vaste_zin(z):
            return self.speel([*naar(o.id, "Enter", niveau=niveau), *toetsen], **opties)

    def antwoord(self, app, o=VT):
        return app.opslag.recente_antwoorden(app.kind.id, o.id, 5)[0]

    def test_alles_meteen_juist(self):
        scherm, app = self.speel_zin(FIETS, [*FIETS_JUIST, ESC, ESC])
        for tekst in ("Stap 1 van 4: Is het onderwerp één, of meer dan één?", "Gisteren ___ Noor in het park.",
                      "(fietsen)", "✔ Het onderwerp is ‘Noor’: één.", "Stap 2 van 4: Typ de stam",
                      "✔ De stam van ‘fietsen’ is ‘fiets’.", "Stap 3 van 4: Zit de s in 't kofschip?",
                      "Zonder -en: ‘fiets’.", "'t  k o f s c h i p", "Stap 4 van 4: Typ nu de vorm in de zin.",
                      "✔ één · stam: fiets · 't kofschip: -te", "De zin met de juiste vorm:",
                      "Gisteren fietste Noor in het park.", "Meteen juist!"):
            self.assertTrue(self.ergens(scherm, tekst), tekst)
        a = self.antwoord(app)
        self.assertTrue(a["juist"])
        self.assertEqual(a["gegeven"], "fietste")
        self.assertEqual(a["vraag"], "Gisteren ___ Noor in het park. (fietsen)")
        for b in scherm.beelden:
            for regel in b.splitlines():
                self.assertLessEqual(len(regel), 80, regel)

    def test_fout_in_de_vorm_dan_tweede_kans(self):
        toetsen = ["1", *"fiets", OK, "j", *"fietsde", OK, "\b", "\b", *"te", OK, ESC, ESC]
        scherm, app = self.speel_zin(FIETS, toetsen)
        self.assertTrue(self.ergens(scherm, "✘ Kijk naar de letter vóór -en: zit de s in 't kofschip?"))
        self.assertTrue(self.ergens(scherm, "Juist, met een tweede kans bij: de vorm."))
        a = self.antwoord(app)
        self.assertTrue(a["juist"])
        self.assertIn('"eerste_fout": "vorm"', a["extra"])
        self.assertEqual(len(app.opslag.herhaalbak(app.kind.id)), 1)  # telt als fout om te herhalen

    def test_twee_keer_fout_dan_het_antwoord(self):
        scherm, app = self.speel_zin(FIETS, ["1", *"fiets", OK, "j", *"fietsde", OK, OK, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "✘ Niet juist. Het juiste antwoord is fietste."))
        self.assertTrue(self.ergens(scherm, "Zo vind je de vorm:"))
        self.assertTrue(self.ergens(scherm, "‘fiets’ eindigt op s: die zit wel in 't kofschip, dus -te."))
        a = self.antwoord(app)
        self.assertFalse(a["juist"])
        self.assertEqual((a["gegeven"], a["diagnose"]), ("fietsde", "ws_kofschip"))

    def test_een_stap_fout_dan_tweede_kans_en_dan_de_uitleg(self):
        # de stam: fietsen (fout), fietss (fout) → de uitleg en verder
        toetsen = ["1", *"fietsen", OK, "\b", "\b", "s", OK, "j", *"fietste", OK, ESC, ESC]
        scherm, app = self.speel_zin(FIETS, toetsen)
        self.assertTrue(self.ergens(scherm, "✘ Dat is het hele werkwoord. De stam is de ik-vorm: ik …"))
        self.assertTrue(self.ergens(scherm, "✘ De stam van ‘fietsen’ is ‘fiets’."))
        self.assertTrue(self.ergens(scherm, "Juist, met een tweede kans bij: de stam."))
        self.assertTrue(self.antwoord(app)["juist"])  # de vorm zelf was juist

    def test_de_keuze_met_pijlen_enter_en_de_muis(self):
        # stap 1 met ↓↑ en Enter; stap 3 met een klik op "ja" (rij 12)
        toetsen = [curses.KEY_DOWN, curses.KEY_UP, OK, *"fiets", OK, ("klik", 12, 10), *"fietste", OK, ESC, ESC]
        scherm, _ = self.speel_zin(FIETS, toetsen)
        self.assertTrue(self.ergens(scherm, "Meteen juist!"))

    def test_tab_meteen_typen_en_terug(self):
        scherm, _ = self.speel_zin(FIETS, [TAB, *"fietste", OK, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Typ de juiste vorm van ‘fietsen’."))
        self.assertTrue(self.ergens(scherm, "Meteen juist!"))
        scherm, _ = self.speel_zin(FIETS, ["1", TAB, TAB, ESC, ESC, ESC])
        terug = scherm.beelden[max(i for i, b in enumerate(scherm.beelden) if "Typ de juiste vorm" in b) + 1:]
        self.assertTrue(any("Stap 2 van 4" in b and "✔ één" in b for b in terug))  # wat gevonden was, blijft

    def test_f1_tips_en_dan_de_spiekbrief_bij_de_stap(self):
        scherm, _ = self.speel_zin(FIETS, ["1", *"fiets", OK, F1, F1, F1, ESC, F1, ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Tip 1: Neem het werkwoord zonder -en"))
        tip2 = next(b for b in scherm.beelden if "Tip 2:" in b)
        self.assertIn("Nog eens F1: je spiekbrief.", " ".join(tip2.split()))
        brief = next(b for b in scherm.beelden if "› Spiekbrief" in b)
        self.assertIn("'T KOFSCHIP", brief)
        self.assertIn("[Esc] terug naar je vraag", brief)

    def test_s_in_het_menu_opent_de_spiekbrief(self):
        stappen = naar(VT.id, "Enter", niveau=None)[:-1]  # tot in het menu van Werkwoordspelling
        scherm, _ = self.speel([*stappen, curses.KEY_DOWN, "s", ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Verleden tijd van zwakke werkwoorden: 't kofschip"))

    def test_moeilijk_typt_meteen(self):
        scherm, _ = self.speel_zin(FIETS, [TAB, *"fietste", OK, ESC, ESC], niveau="3")
        self.assertTrue(self.ergens(scherm, "Typ de juiste vorm van ‘fietsen’."))
        self.assertFalse(self.ergens(scherm, "Stap 1 van"))
        self.assertFalse(self.ergens(scherm, "[Tab]"))
        self.assertTrue(self.ergens(scherm, "Meteen juist!"))

    def test_tegenwoordige_tijd_jij_achter_het_werkwoord(self):
        scherm, app = self.speel_zin(WORD, ["2", *"word", OK, "2", "1", *"word", OK, ESC, ESC])
        for tekst in ("Stap 1 van 4: Wie doet het?", "___ jij snel moe?", "Stap 3 van 4: Wat schrijf je?",
                      "✘ Kijk waar ‘jij’ staat: voor of achter het werkwoord?",
                      "✔ Jij staat achter het werkwoord: alleen de stam, zonder t.", "Word jij snel moe?",
                      "Juist, met een tweede kans bij: de regel."):
            self.assertTrue(self.ergens(scherm, tekst), tekst)
        self.assertTrue(self.antwoord(app, TT)["juist"])

    def test_een_sterk_werkwoord(self):
        scherm, app = self.speel_zin(LIEP, ["1", *"loopte", OK, F1, F1, *["\b"] * 6, *"liep", OK, ESC, ESC])
        for tekst in ("Stap 1 van 2: Is het onderwerp één, of meer dan één?", "Stap 2 van 2: Typ nu de vorm in de zin.",
                      "✘ ‘lopen’ is een sterk werkwoord: in de verleden tijd verandert de klank.",
                      "Tip 2: Een stukje van het rijtje: het voltooid deelwoord is ‘gelopen’.",
                      "Gisteren liep Noor in het park.", "Juist, met een tweede kans bij: de vorm."):
            self.assertTrue(self.ergens(scherm, tekst), tekst)
        self.assertFalse(self.ergens(scherm, "'t  k o f s c h i p"))  # geen kofschip bij een sterk werkwoord
        self.assertTrue(self.antwoord(app, STERK)["juist"])

    def test_het_voltooid_deelwoord(self):
        scherm, app = self.speel_zin(GEFIETST, [*"fiets", OK, "j", *"gefietst", OK, ESC, ESC])
        for tekst in ("Noor heeft gisteren in het park ___.", "Stap 2 van 3: Zit de s in 't kofschip?",
                      "ja: op het einde een t", "✔ stam: fiets · 't kofschip: t",
                      "Noor heeft gisteren in het park gefietst.", "Meteen juist!"):
            self.assertTrue(self.ergens(scherm, tekst), tekst)
        self.assertEqual(self.antwoord(app, VD)["gegeven"], "gefietst")

    def test_zet_in_de_verleden_tijd(self):
        # Daarna fietst Noor in het park.: de pv is het tweede woord (→), zwak (1), fietste
        scherm, app = self.speel_zin(NU, [OK, curses.KEY_RIGHT, OK, "2", "1", *"fietst", OK, *"e", OK, ESC, ESC])
        for tekst in ("Stap 1 van 3: Zoek de persoonsvorm.", "Daarna fietst Noor in het park.",
                      "✘ Dat is niet de persoonsvorm.", "✔ De persoonsvorm is ‘fietst’ (van ‘fietsen’).",
                      "Stap 2 van 3: Is ‘fietsen’ zwak of sterk?", "✘ Zeg het hardop met ‘gisteren’",
                      "✔ ‘fietsen’ is zwak: de klank blijft (fietsen – fietste).",
                      "Stap 3 van 3: Typ de persoonsvorm in de verleden tijd.", "Verleden tijd:",
                      "✔ pv: fietst · zwak", "✘ Dat is nog de tegenwoordige tijd.", "De zin in de verleden tijd:",
                      "Daarna fietste Noor in het park.",
                      "Juist, met een tweede kans bij: de persoonsvorm, zwak of sterk,"):
            self.assertTrue(self.ergens(scherm, tekst), tekst)
        self.assertFalse(self.ergens(scherm, "(fietsen)  "))  # het werkwoord staat er niet bij: dat zoek je zelf
        a = self.antwoord(app, NAAR)
        self.assertEqual((a["gegeven"], bool(a["juist"]), a["vraag"]),
                         ("fietste", True, "Daarna fietst Noor in het park. → verleden tijd"))

    def test_zet_in_de_verleden_tijd_met_de_muis_en_tab(self):
        # de woorden op rij 10: Daarna x=7, fietst x=14
        scherm, _ = self.speel_zin(NU, [("klik", 10, 15), "1", *"fietste", OK, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Meteen juist!"))
        scherm, _ = self.speel_zin(NU, [TAB, *"fietste", OK, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Typ de persoonsvorm in de verleden tijd."))
        self.assertFalse(self.ergens(scherm, "Stap 2 van 3"))
        self.assertTrue(self.ergens(scherm, "Meteen juist!"))

    def test_de_spiekbrief_met_de_rijtjes(self):
        stappen = naar(STERK.id, "Enter", niveau=None)[:-1]
        i = [o.id for o in ONDERWERPEN].index(STERK.id)
        scherm, _ = self.speel([*stappen, *[curses.KEY_DOWN] * i, "s", ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Sterke werkwoorden: de klank verandert"))
        self.assertTrue(self.ergens(scherm, "lopen – liep – gelopen"))

    def test_cijfers_en_tekens_typ_je_niet(self):
        scherm, _ = self.speel_zin(FIETS, [TAB, "1", "?", OK, *"fietste", OK, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Typ eerst het woord."))
        self.assertTrue(self.ergens(scherm, "Meteen juist!"))

    def test_zonder_kleur_en_eenvoudige_tekens(self):
        scherm, _ = self.speel_zin(FIETS, [*FIETS_JUIST, ESC, ESC], voorrang={"ascii": True, "thema": "geen-kleur"})
        self.assertTrue(self.ergens(scherm, "Meteen juist!"))
        self.assertTrue(all(ord(c) < 128 for b in scherm.beelden for c in b))


class TestZonderHulp(unittest.TestCase):
    """Hulp.EXAMEN (later): de Oefenaar zet tweede_kans uit; dan is één fout meteen het einde van de vraag."""

    def test_een_fout_is_fout(self):
        with vaste_zin(FIETS):
            v = VT.maak("5")
        obj = WS.WerkwoordInvoer(v, VT)
        obj.tweede_kans = Hulp.EXAMEN.tweede_kans
        self.assertIsNone(obj.toets(ord("2")))  # stap 1 fout: meteen de uitleg en verder
        self.assertEqual((obj.stap, obj.mislukt), (1, ["getal"]))
        obj.wissel()
        for ch in "fietsde":
            obj.toets(ord(ch))
        self.assertEqual(obj.toets(10), ("fietsde", "fietsde"))
        self.assertEqual(obj.extra["eerste_fout"], "getal")


class TestGerichteAap(Basis):
    """Willekeurig drukken in de werkwoordmachine op elk niveau: geen fout en niets mag blijven hangen. Ook in de
    lange aapjestest (LEERAVONTUUR_AAP_RONDES)."""

    def test_aapjes_in_de_werkwoordmachine(self):
        try:
            from .test_stabiliteit import TestAapjes
        except ImportError:
            from test_stabiliteit import TestAapjes
        rondes = int(os.environ.get("LEERAVONTUUR_AAP_RONDES", "1"))
        with mock.patch.dict(os.environ, {"LEERAVONTUUR_DEBUG": "1"}):
            for seed in range(8 * rondes):
                rng = random.Random(1200 + seed)
                o, niveau = ONDERWERPEN[seed % len(ONDERWERPEN)], "1234"[seed % 3 + seed % 2]
                toetsen = [e for e in TestAapjes.gebeurtenissen(self, rng, 400) if e != ESC]
                try:
                    scherm, _ = self.speel([*naar(o.id, "Enter", niveau=niveau), *toetsen, *[ESC] * 10])
                except HangtFout as e:
                    self.fail(f"seed {seed}: het programma hangt ({e})")
                except Exception as e:  # noqa: BLE001
                    raise AssertionError(f"seed {seed} ({o.id}, niveau {niveau}): {type(e).__name__}: {e}") from e
                self.assertTrue(self.ergens(scherm, "Vraag 1 van 10"), seed)


if __name__ == "__main__":
    unittest.main()
