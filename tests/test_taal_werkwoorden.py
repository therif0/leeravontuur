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
ONDERWERPEN = (TT, VT)
JAREN = ("4", "5", "6")
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
        self.assertRegex(zin("fietsen", "tt", "hij", "inversie").zin, r"^(Vandaag|Nu|Elke dag) ___ .*\.$")
        vraag = zin("fietsen", "tt", "jij_inv", "vraag")
        self.assertRegex(vraag.zin, r"^___ jij .*\?$")
        self.assertTrue(vraag.vol().startswith("Fiets jij"))  # ingevuld: met een hoofdletter
        self.assertRegex(zin("fietsen", "vt", "hij").zin, r"(gisteren|vorige week|toen)")
        self.assertIsNone(W.maak_zin(W.ww("branden"), "tt", random.Random(1), ["ik"], ["gewoon"]))  # het vuur brandt

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
                self.assertGreaterEqual(len(o.kandidaten(p)), 30, (o.id, jaar))
                for seed in range(150):
                    v = o.maak(jaar, rng=random.Random(seed))
                    z = v.model
                    self.assertLessEqual(len(v.tekst), W.BREED, v.tekst)
                    self.assertEqual(v.antwoord, W.vorm_van(z.ww, o.vorm, z.persoon), v.tekst)
                    self.assertTrue(o.nakijken(v, o.lees_vraag(v, v.verwacht)), v.tekst)
                    self.assertIn(z.persoon, p["personen"], v.tekst)
                    self.assertIn(W.stamsoort(z.ww), p["stammen"], v.tekst)
                    self.assertIn(z.ww["niveau"], p["niveaus"], v.tekst)
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
                            self.assertIn(st.kop, koppen, (o.id, st.naam))
                            self.assertTrue(st.uitleg)
                            if st.soort == "keuze":
                                self.assertTrue(0 <= st.juist < len(st.opties) <= 4)
                            else:
                                self.assertTrue(st.juist and all(st.juist))
                    self.assertIn(z.antwoord, o.uitleg(v)[-1])
                    self.assertIn(o.kop_op_spiekbrief(v), koppen)

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


FIETS = W.WwZin("Gisteren", "Noor in het park.", "fietsen", "vt", "hij", "Noor", "fietste", "inversie")
WORD = W.WwZin("", "jij snel moe?", "worden", "tt", "jij_inv", "jij", "word", "vraag")
FIETS_JUIST = ["1", *"fiets", OK, "j", *"fietste", OK]


def vaste_zin(z):
    """Elke vraag is deze zin (zodat de test weet welke toetsen juist zijn)."""
    return mock.patch.object(W, "maak_zin", side_effect=lambda *a, **k: z)


class TestHetScherm(Basis):
    def speel_zin(self, z, toetsen, niveau=OK, **opties):
        o = TT if z.vorm == "tt" else VT
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
            for seed in range(6 * rondes):
                rng = random.Random(1200 + seed)
                o, niveau = ONDERWERPEN[seed % 2], "123"[seed % 3]
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
