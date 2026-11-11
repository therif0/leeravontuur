"""Taal T1.2: de zinsontleder op het scherm (stap voor stap, Tab, vrij kleuren, verdelen, de muis, de tweede kans)."""

import curses
import os
import random
import unittest
from unittest import mock

from leeravontuur.kern.taal import zinnenmachine as M
from leeravontuur.kern.taal.zinnen import lees_haakjes
from leeravontuur.terminal.nepscherm import HangtFout
from leeravontuur.terminal.zinsdelen import ZinsdelenInvoer
try:
    from .test_schermen import ESC, F1, OK, Basis, naar
except ImportError:  # ook zo te starten: python -m unittest discover -s tests
    from test_schermen import ESC, F1, OK, Basis, naar

L, R = curses.KEY_LEFT, curses.KEY_RIGHT
SP, TAB = " ", "\t"
ONDERWERP = "taal.zinsontleding.zinsdelen"
OMA = "[bwb Morgen] [pv geeft] [o oma] [mv haar kleinzoon] [lv een fiets]."
JUF = "[o De juf] [pv leest] [lv een boek]."
# Normaal, stap voor stap: pv (geeft), o (oma), lv (een fiets), mv (haar kleinzoon); de cursor begint telkens vooraan
OMA_JUIST = [R, OK, R, R, OK, *[R] * 5, SP, OK, *[R] * 3, SP, OK]


def vaste_zin(haakjes):
    """Elke vraag is deze zin (zodat de test weet welke toetsen juist zijn)."""
    from leeravontuur.kern.taal.zinsontleding import Zinsontleding
    return mock.patch.object(Zinsontleding, "maak_zin", side_effect=lambda *a, **k: lees_haakjes(haakjes, M.soort_van))


class TestStapVoorStap(Basis):
    def speel_zin(self, haakjes, toetsen, niveau=OK, **opties):
        with vaste_zin(haakjes):
            return self.speel([*naar(ONDERWERP, "Enter", niveau=niveau), *toetsen], **opties)

    def test_alles_meteen_juist(self):
        scherm, app = self.speel_zin(OMA, [*OMA_JUIST, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Stap 1 van 4: Zoek de persoonsvorm (pv)."))
        self.assertTrue(self.ergens(scherm, "Stap 3 van 4: Is er een lijdend voorwerp (lv)?"))
        self.assertTrue(self.ergens(scherm, "✔ pv: geeft."))
        self.assertTrue(self.ergens(scherm, "Elk zinsdeel juist, meteen!"))
        self.assertTrue(self.ergens(scherm, "Vraag 1 van 10"))
        antwoorden = app.opslag.recente_antwoorden(app.kind.id, "taal.zinsontleding", 5)
        self.assertEqual(len(antwoorden), 1)
        self.assertTrue(antwoorden[0]["juist"])
        for b in scherm.beelden:
            for regel in b.splitlines():
                self.assertLessEqual(len(regel), 80, regel)

    def test_fout_tip_en_tweede_kans(self):
        # pv: eerst Morgen (fout), dan een tip, dan juist; de rest juist
        scherm, app = self.speel_zin(OMA, [OK, F1, F1, R, OK, *OMA_JUIST[2:], ESC, ESC])
        self.assertTrue(self.ergens(scherm, "De pv staat niet altijd vooraan"))
        self.assertTrue(self.ergens(scherm, "Tip 1: Maak er een vraag van"))
        self.assertTrue(self.ergens(scherm, "Tip 2: De tijdproef"))
        self.assertTrue(self.ergens(scherm, "Juist, met een tweede kans bij: pv."))
        a = app.opslag.recente_antwoorden(app.kind.id, "taal.zinsontleding", 5)[0]
        self.assertTrue(a["juist"])
        self.assertTrue(a["hulp"])  # met tips
        self.assertIn('"eerste_fout": "pv"', a["extra"])  # telt als fout om te herhalen (zoals een vraagstuk)
        self.assertEqual(len(app.opslag.herhaalbak(app.kind.id)), 1)

    def test_na_de_tips_de_spiekbrief_bij_de_stap(self):
        """F1, F1: de twee tips (de tweede zegt "Nog eens F1: je spiekbrief."), F1: de spiekbrief bij het kopje van
        de stap; Esc = terug naar de vraag, en daarna begint het weer bij tip 1."""
        scherm, _ = self.speel_zin(OMA, [R, OK, F1, F1, F1, ESC, F1, ESC, ESC, ESC])
        tip2 = next(b for b in scherm.beelden if "Tip 2:" in b)
        self.assertIn("spiekbrief.", " ".join(tip2.split()))  # de tip staat over twee regels
        self.assertIn("Nog eens F1: je spiekbrief.", " ".join(tip2.split()))
        brief = next(b for b in scherm.beelden if "› Spiekbrief" in b)
        self.assertIn("HET ONDERWERP (o)", "\n".join(brief.splitlines()[:5]))  # geopend bij de stap van het o
        self.assertIn("[Esc] terug naar je vraag", brief)
        na = scherm.beelden[scherm.beelden.index(brief) + 1:]
        self.assertTrue(any("Stap 2 van 4" in b for b in na))
        self.assertTrue(any("Tip 1:" in b for b in na))

    def test_s_in_het_menu_opent_de_spiekbrief(self):
        from leeravontuur.terminal import curriculum as CU
        stappen = naar(ONDERWERP, "Enter", niveau=None)[:-1]  # tot in het menu van Zinsontleding
        scherm, _ = self.speel([*stappen, "s", ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Zinsontleding: zo vind je de zinsdelen"))
        self.assertTrue(CU.zoek(ONDERWERP).spiek)

    def test_twee_keer_fout_dan_de_uitleg(self):
        scherm, app = self.speel_zin(OMA, [OK, OK, ESC, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "✘ De pv is ‘geeft’."))
        self.assertTrue(self.ergens(scherm, "Stap 2 van 4"))

    def test_n_als_er_geen_mv_is(self):
        scherm, app = self.speel_zin(JUF, [R, R, OK, SP, OK, R, R, R, SP, OK, "n", ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Is er een meewerkend voorwerp (mv)?"))
        self.assertTrue(self.ergens(scherm, "Elk zinsdeel juist, meteen!"))

    def test_met_de_muis(self):
        # De juf leest een boek: de woorden op rij 10 (De x=7, juf 11, leest 16, een 23, boek 28)
        scherm, _ = self.speel_zin(JUF, [("klik", 10, 17), OK, ("klik", 10, 7), ("klik", 10, 11), OK, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "✔ pv: leest."))
        self.assertTrue(self.ergens(scherm, "✔ o: de juf."))  # een klik op het woord ernaast = de groep groter

    def test_tab_vrij_kleuren(self):
        # Tab, dan kleuren: geeft = P, oma = O, haar kleinzoon = M, een fiets = L, Enter
        toetsen = [TAB, R, "p", R, "o", R, SP, "m", R, SP, "l", OK, ESC, ESC]
        scherm, _ = self.speel_zin(OMA, toetsen)
        self.assertTrue(self.ergens(scherm, "Kleur de zinsdelen."))
        self.assertTrue(self.ergens(scherm, "Elk zinsdeel juist, meteen!"))

    def test_tab_terug_naar_de_stappen(self):
        scherm, _ = self.speel_zin(OMA, [R, OK, TAB, TAB, ESC, ESC, ESC])
        vrij = next(i for i, b in enumerate(scherm.beelden) if "Kleur de zinsdelen." in b)
        self.assertTrue(any("Stap 2 van 4" in b for b in scherm.beelden[vrij:]))  # terug, en de pv blijft gevonden

    def test_vrij_kleuren_fout_dan_tweede_kans(self):
        toetsen = [TAB, R, "p", R, "o", R, SP, "l", R, SP, "m", OK]  # lv en mv verwisseld
        scherm, _ = self.speel_zin(OMA, [*toetsen, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Nog niet alles juist: kijk nog eens naar lv, mv"))

    def test_makkelijk_eerst_verdelen(self):
        # 4de leerjaar: De juf | leest | een boek, dan pv en o
        toetsen = [R, SP, R, SP, OK, R, R, OK, SP, OK, ESC, ESC]
        scherm, _ = self.speel_zin(JUF, toetsen, niveau="1")
        self.assertTrue(self.ergens(scherm, "Stap 1 van 3: Verdeel de zin in zinsdelen."))
        self.assertTrue(self.ergens(scherm, "✔ Zo is de zin goed verdeeld."))
        self.assertTrue(self.ergens(scherm, "Elk zinsdeel juist, meteen!"))

    def test_moeilijk_meteen_vrij_kleuren(self):
        scherm, _ = self.speel_zin(OMA, [ESC, ESC], niveau="3")
        self.assertTrue(self.ergens(scherm, "Kleur de zinsdelen."))
        self.assertFalse(self.ergens(scherm, "Stap 1 van"))

    def test_zonder_kleur_en_eenvoudige_tekens(self):
        scherm, _ = self.speel_zin(OMA, [*OMA_JUIST[:5], ESC, ESC], voorrang={"ascii": True, "thema": "geen-kleur"})
        self.assertTrue(self.ergens(scherm, "pv"))
        self.assertTrue(all(ord(c) < 128 for b in scherm.beelden for c in b))


GROOT = "[o Grootvader] [pv vertelt] | dat [o de kist] onder de grond [pv ligt]."
EMMA = "[o Emma] [pv leest] de brief en [pv krijgt] een idee."
# alle pv's (vertelt, ligt), dan het onderwerp bij elke pv (Grootvader; de kist)
GROOT_JUIST = [R, SP, *[R] * 7, SP, OK, OK, *[R] * 3, SP, OK]


class TestTweePersoonsvormen(Basis):
    """0.25.1: een zin met meer dan één pv (alleen op Moeilijk): alle pv's, dan het onderwerp bij elke pv."""

    def speel_zin(self, haakjes, toetsen, **opties):
        with vaste_zin(haakjes):
            return self.speel([*naar(ONDERWERP, "Enter", niveau="3"), *toetsen], **opties)

    def test_alles_meteen_juist(self):
        scherm, app = self.speel_zin(GROOT, [*GROOT_JUIST, ESC, ESC])
        for tekst in ("Stap 1 van 3: Zoek alle persoonsvormen (2).", "✔ pv: vertelt, ligt.",
                      "Stap 2 van 3: Zoek het onderwerp bij ‘vertelt’.", "✔ o bij ‘vertelt’: grootvader.",
                      "Stap 3 van 3: Zoek het onderwerp bij ‘ligt’.", "Elk zinsdeel juist, meteen!"):
            self.assertTrue(self.ergens(scherm, tekst), tekst)
        self.assertTrue(app.opslag.recente_antwoorden(app.kind.id, "taal.zinsontleding", 5)[0]["juist"])
        for b in scherm.beelden:
            for regel in b.splitlines():
                self.assertLessEqual(len(regel), 80, regel)

    def test_een_pv_vergeten_dan_tweede_kans(self):
        scherm, app = self.speel_zin(GROOT, [R, SP, OK, *[R] * 7, SP, OK, OK, *[R] * 3, SP, OK, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Deze zin heeft twee persoonsvormen."))
        self.assertTrue(self.ergens(scherm, "Juist, met een tweede kans bij: pv."))
        self.assertIn('"eerste_fout": "pv"', app.opslag.recente_antwoorden(app.kind.id, "taal.zinsontleding", 5)[0]["extra"])

    def test_enter_zonder_iets_aan_te_duiden_is_geen_fout(self):
        scherm, _ = self.speel_zin(GROOT, [OK, *GROOT_JUIST, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Duid eerst elke persoonsvorm aan met Spatie."))
        self.assertTrue(self.ergens(scherm, "Elk zinsdeel juist, meteen!"))

    def test_het_onderwerp_van_de_andere_pv(self):
        # bij ‘ligt’ kiest het kind Grootvader (het onderwerp bij ‘vertelt’)
        scherm, _ = self.speel_zin(GROOT, [*GROOT_JUIST[:12], OK, OK, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Dat is het onderwerp bij ‘vertelt’."))
        self.assertTrue(self.ergens(scherm, "Niet gevonden: o. Lees de uitleg."))  # na de tweede fout

    def test_twee_pvs_met_een_onderwerp(self):
        # Emma leest … en krijgt …: Emma is het onderwerp bij de twee pv's
        scherm, _ = self.speel_zin(EMMA, [R, SP, *[R] * 4, SP, OK, OK, OK, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Zoek het onderwerp bij ‘krijgt’."))
        self.assertTrue(self.ergens(scherm, "Elk zinsdeel juist, meteen!"))

    def test_met_de_muis(self):
        # de woorden op rij 10: Grootvader x=7, vertelt 19, dat 28, de 33, kist 37, onder 43, de 50, grond 54, ligt 61
        klikken = [("klik", 10, 20), ("klik", 10, 62), OK, ("klik", 10, 8), OK, ("klik", 10, 33), ("klik", 10, 38), OK]
        scherm, _ = self.speel_zin(GROOT, [*klikken, ESC, ESC])
        self.assertTrue(self.ergens(scherm, "Elk zinsdeel juist, meteen!"))

    def test_tab_vrij_kleuren(self):
        toetsen = [TAB, "o", R, "p", *[R] * 2, SP, "o", *[R] * 4, "p", OK, ESC, ESC]
        scherm, _ = self.speel_zin(GROOT, toetsen)
        self.assertTrue(self.ergens(scherm, "Kleur alle persoonsvormen en hun onderwerp."))
        self.assertTrue(self.ergens(scherm, "Elk zinsdeel juist, meteen!"))

    def test_het_leesteken_staat_tegen_het_woord(self):
        scherm, _ = self.speel_zin(GROOT, [ESC, ESC])
        self.assertTrue(self.ergens(scherm, "grond  ligt."))

    def test_f1_opent_de_spiekbrief_bij_twee_persoonsvormen(self):
        scherm, _ = self.speel_zin(GROOT, [F1, F1, F1, ESC, ESC, ESC])
        brief = next(b for b in scherm.beelden if "› Spiekbrief" in b)
        self.assertIn("ZINNEN MET TWEE PERSOONSVORMEN", brief)

    def test_zonder_kleur_en_eenvoudige_tekens(self):
        scherm, _ = self.speel_zin(GROOT, [*GROOT_JUIST, ESC, ESC], voorrang={"ascii": True, "thema": "geen-kleur"})
        self.assertTrue(all(ord(c) < 128 for b in scherm.beelden for c in b))


class TestGerichteAap(Basis):
    """Willekeurig drukken in de zinsontleder op elk niveau (ook de nagekeken zinnen en de zinnen met twee pv's):
    geen fout en niets mag blijven hangen. Ook in de lange aapjestest (LEERAVONTUUR_AAP_RONDES)."""

    def test_aapjes_in_de_zinsontleder(self):
        try:
            from .test_stabiliteit import TestAapjes
        except ImportError:
            from test_stabiliteit import TestAapjes
        rondes = int(os.environ.get("LEERAVONTUUR_AAP_RONDES", "1"))
        with mock.patch.dict(os.environ, {"LEERAVONTUUR_DEBUG": "1"}):
            for seed in range(6 * rondes):
                rng = random.Random(900 + seed)
                niveau = "123"[seed % 3]
                toetsen = [e for e in TestAapjes.gebeurtenissen(self, rng, 400) if e != ESC]
                try:
                    scherm, _ = self.speel([*naar(ONDERWERP, "Enter", niveau=niveau), *toetsen, *[ESC] * 10])
                except HangtFout as e:
                    self.fail(f"seed {seed}: het programma hangt ({e})")
                except Exception as e:  # noqa: BLE001
                    raise AssertionError(f"seed {seed} (niveau {niveau}): {type(e).__name__}: {e}") from e
                self.assertTrue(self.ergens(scherm, "Vraag 1 van 10"), seed)


class TestDeTekstPast(unittest.TestCase):
    def test_hints_en_legende_passen(self):
        """De hint staat op kolom 6 (de Oefenaar), dus hoogstens 72 tekens; de legende naast het maatje 56."""
        from leeravontuur.kern import catalogus
        from leeravontuur.terminal import zinsdelen as ZD
        o = catalogus.ONDERWERPEN["taal.zinsontleding"]
        for jaar in ("4", "5", "6"):
            for seed in range(20):
                import random
                v = o.maak(jaar, rng=random.Random(seed))
                obj = ZinsdelenInvoer(v, o)
                for label in obj.stappen:
                    obj.stap = obj.stappen.index(label)
                    for vrij in (False, True):
                        obj.vrij = vrij
                        self.assertLessEqual(len(obj.hint_tekst()), 72, (jaar, label, obj.hint_tekst()))
                    if label != ZD.VERDELEN:
                        self.assertLessEqual(len(f"Stap 1 van 3: {obj.vraag()}"), ZD.OPDRACHT_BREED, obj.vraag())
                namen = " · ".join(f"{l.upper()} {ZD.LETTERS[l]}" for l in ZD.LETTERS if ZD.LETTERS[l] in obj.gevraagd)
                self.assertLessEqual(len(namen), ZD.OPDRACHT_BREED)


class TestZonderTweedeKans(unittest.TestCase):
    """Hulp.EXAMEN (later): de Oefenaar zet tweede_kans uit; dan is één fout meteen het juiste antwoord."""

    def test_meteen_de_uitleg(self):
        from leeravontuur.kern import catalogus
        o = catalogus.ONDERWERPEN["taal.zinsontleding"]
        with vaste_zin(OMA):
            v = o.maak("5")
        obj = ZinsdelenInvoer(v, o)
        obj.tweede_kans = False
        obj.toets(10)  # Enter: Morgen als pv
        self.assertIn("De pv is ‘geeft’", obj.melding)
        self.assertEqual(obj.label, "o")
        self.assertEqual(obj.mislukt, ["pv"])


if __name__ == "__main__":
    unittest.main()
