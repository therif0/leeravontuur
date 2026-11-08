"""Taal T1.2: de zinsontleder op het scherm (stap voor stap, Tab, vrij kleuren, verdelen, de muis, de tweede kans)."""

import curses
import unittest
from unittest import mock

from leeravontuur.kern.taal import zinnenmachine as M
from leeravontuur.kern.taal.zinnen import lees_haakjes
from leeravontuur.terminal.zinsdelen import ZinsdelenInvoer
try:
    from .test_schermen import ESC, F1, OK, Basis, naar
except ImportError:  # ook zo te starten: python -m unittest discover -s tests
    from test_schermen import ESC, F1, OK, Basis, naar

L, R = curses.KEY_LEFT, curses.KEY_RIGHT
SP, TAB = " ", "\t"
ONDERWERP = "taal.zinsontleding.zinsdelen"
OMA = "[bwb Morgen] [pv geeft] [ow oma] [mv haar kleinzoon] [lv een fiets]."
JUF = "[ow De juf] [pv leest] [lv een boek]."
# Normaal, stap voor stap: pv (geeft), ow (oma), lv (een fiets), mv (haar kleinzoon); de cursor begint telkens vooraan
OMA_JUIST = [R, OK, R, R, OK, *[R] * 5, SP, OK, *[R] * 3, SP, OK]


def vaste_zin(haakjes):
    """De zinnenmachine geeft altijd deze zin (zodat de test weet welke toetsen juist zijn)."""
    return mock.patch.object(M, "maak", side_effect=lambda *a, **k: lees_haakjes(haakjes, M.soort_van))


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
        self.assertTrue(self.ergens(scherm, "✔ ow: de juf."))  # een klik op het woord ernaast = de groep groter

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
        # 4de leerjaar: De juf | leest | een boek, dan pv en ow
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
        self.assertEqual(obj.label, "ow")
        self.assertEqual(obj.mislukt, ["pv"])


if __name__ == "__main__":
    unittest.main()
