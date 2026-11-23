"""De bouwstenen van de schermen 1.0 (werk/schermen.md, fase 2): de indeling, en elk invoer-object en elk model past in
zijn vak, op elke grootte (80×24, 120×40 en 240×67: de tty van de zoon)."""

import random
import unittest

from leeravontuur.kern import catalogus  # noqa: F401 (alle onderwerpen)
from leeravontuur.kern import overzicht as OZ
from leeravontuur.kern.leerjaren import LEERJAREN
from leeravontuur.kern.onderwerp import ONDERWERPEN
from leeravontuur.kern.wiskunde import eenheden as E
from leeravontuur.terminal import indeling as I
from leeravontuur.terminal import modellen as M
from leeravontuur.terminal.oefenaar import INVOER

GROOTTES = [(24, 80), (30, 100), (40, 120), (67, 240)]
ZADEN = range(6)


def vragen():
    """Een paar vragen van elk onderwerp in elk leerjaar (en Maten: gewoon en in de tabel)."""
    uit = []
    for o in ONDERWERPEN.values():
        for jaar in LEERJAREN:
            if o.aangeboden(jaar):
                uit += [(o, o.maak(jaar, rng=random.Random(z))) for z in ZADEN]
    for tabel in (False, True):
        m = E.Maten(tabel=tabel)
        random.seed(tabel)
        uit += [(m, m.maak(j)) for j in ("4", "5", "6") for _ in ZADEN]
    return uit


VRAGEN = vragen()


class Opnemer:
    """Een nepscherm dat onthoudt waar er getekend werd."""

    def __init__(self):
        self.puts = []
        self.zones = self

    def put(self, y, x, tekst, rol=""):
        if tekst.strip():
            self.puts.append((y, x, x + len(tekst.rstrip()), tekst))

    def tekstvak(self, y, x, tekst, breedte, rol, actie=None):
        self.puts.append((y, x, x + breedte + 2, "[vak]"))

    def voeg(self, *_):
        pass

    def cursor(self, *_):
        pass

    def bewerk(self, buf, k, *a):
        return buf

    def maat(self):
        return (24, 80)

    def __getattr__(self, naam):
        raise AttributeError(naam)


class TestIndeling(unittest.TestCase):
    def test_elk_vak_binnen_het_scherm_en_niets_overlapt(self):
        for h, w in GROOTTES:
            for maatje in (True, False):
                with self.subTest(h=h, w=w, maatje=maatje):
                    ind = I.oefenscherm(h, w, maatje=maatje)
                    vakken = [r for r in (ind.reeks, ind.links, ind.maatje) if r]
                    for r in vakken:
                        self.assertGreaterEqual(r.y, 1)
                        self.assertLessEqual(r.onder, h - 1)
                        self.assertGreaterEqual(r.x, 0)
                        self.assertLessEqual(r.rechts, w)
                    for a in vakken:
                        for b in vakken:
                            if a is not b:
                                self.assertFalse(a.x < b.rechts and b.x < a.rechts and a.y < b.onder and b.y < a.onder,
                                                 (a, b))

    def test_groeit_tot_120_bij_40_en_staat_dan_in_het_midden(self):
        self.assertEqual(I.blok(24, 80), I.Rechthoek(1, 0, 22, 80))
        self.assertEqual(I.blok(40, 120), I.Rechthoek(1, 0, 38, 120))
        b = I.blok(67, 240)
        self.assertEqual((b.h, b.w), (38, 120))
        self.assertEqual((b.x, b.y), (60, 1 + (65 - 38) // 2))

    def test_reeks_een_vak_vanaf_30_rijen(self):
        self.assertFalse(I.oefenscherm(24, 80).groot)
        self.assertEqual(I.oefenscherm(24, 80).reeks.h, 1)
        self.assertTrue(I.oefenscherm(30, 100).groot)
        self.assertEqual(I.oefenscherm(30, 100).reeks.h, 3)

    def test_klokvenster_open_geen_maatje_maar_de_kolom_blijft_vrij(self):
        met, open_ = I.oefenscherm(24, 80), I.oefenscherm(24, 80, klokvenster=True)
        self.assertIsNone(open_.maatje)
        self.assertEqual(open_.links.w, met.links.w)  # daar staat het venster

    def test_klad_alleen_als_er_plaats_is(self):
        self.assertIsNone(I.oefenscherm(24, 80, klad=True, vraag_b=50).klad)
        ind = I.oefenscherm(40, 120, klad=True)
        self.assertEqual(ind.klad.w, I.KLAD_MAX)
        self.assertEqual(ind.links.rechts, ind.klad.x)

    def test_verdeel_tip_en_spiekbrief(self):
        links = I.oefenscherm(40, 120).links
        vraag, tip, spiek = I.verdeel(links, 12)
        self.assertEqual((vraag.onder, tip.h, tip.onder), (tip.y, I.TIP_H, spiek.y))
        self.assertEqual(spiek.onder, links.onder)
        self.assertIsNone(I.verdeel(links, 12, spiek=False)[2])  # een examen: geen spiekbrief
        klein = I.oefenscherm(24, 80).links
        self.assertIsNone(I.verdeel(klein, 15)[2])  # 80×24: geen plaats, F1 opent hem over het hele scherm


class TestPast(unittest.TestCase):
    def plaats(self, obj, h, w):
        """Zoals de beta: links in het vak Vraag, en de volle breedte (zonder maatje) als het te breed is."""
        ind = I.oefenscherm(h, w)
        b = ind.links.binnen
        obj.plaats(b.x, b.w)
        if obj.breedte() > b.w:
            ind = I.oefenscherm(h, w, maatje=False)
            b = ind.links.binnen
            obj.plaats(b.x, b.w)
        return ind, b

    def test_elk_invoer_object_past_in_zijn_vak(self):
        """Wat het object echt tekent, blijft binnen de breedte van het vak, tijdens de vraag en na het nakijken; en
        het past in de hoogte van de kolom (de objecten met een eigen scherm, Maten: tijdens de vraag; de uitleg na het
        nakijken komt in fase 3 in het vak eronder)."""
        gezien = set()
        for o, v in VRAGEN:
            if v.invoer not in INVOER:
                continue
            gezien.add(v.invoer)
            for pw in (False, True):
                obj = INVOER[v.invoer](v, o)
                if hasattr(obj, "plaatswaarden"):
                    obj.plaatswaarden = pw
                for h, w in GROOTTES:
                    ind, b = self.plaats(obj, h, w)
                    eigen = getattr(obj, "eigen_scherm", False)
                    if eigen:
                        obj.y0 = ind.links.y + 1
                    s = Opnemer()
                    staten = (None,) if eigen else (None, False)
                    obj.meet()  # meten mag niets veranderen
                    for uitslag in staten:
                        obj.teken_voor_maat(s, uitslag)
                    with self.subTest(invoer=v.invoer, o=o.id, sleutel=v.sleutel, pw=pw, h=h, w=w):
                        links = min(x for _, x, _, _ in s.puts)
                        rechts = max(r for _, _, r, _ in s.puts)
                        self.assertGreaterEqual(links, b.x)
                        self.assertLessEqual(rechts, b.x + b.w, [p for p in s.puts if p[2] > b.x + b.w][:2])
                        hoog = obj.hoogte(False)
                        self.assertLessEqual(hoog, b.h, v.invoer)
        self.assertGreaterEqual(gezien, set(INVOER) - {"speur", "keuze"} | {"rooster", "staart", "tabel"})

    def test_cijferen_past_met_de_vraag_de_tip_en_de_rand(self):
        """De beta (rooster en staartdeling): de band, het object, de melding en het vak Tip passen ook in de hoogte."""
        for o, v in VRAGEN:
            if v.invoer not in ("rooster", "staart"):
                continue
            for pw in (False, True):
                obj = INVOER[v.invoer](v, o)
                if hasattr(obj, "plaatswaarden"):
                    obj.plaatswaarden = pw
                for h, w in GROOTTES:
                    ind, b = self.plaats(obj, h, w)
                    vraag_h = 1 + (1 + 2 * ind.groot) + 1 + obj.hoogte() + 1 + 1 + 1  # band, lege rij, melding, rand
                    with self.subTest(o=o.id, sleutel=v.sleutel, pw=pw, h=h, w=w):
                        self.assertLessEqual(vraag_h + 3, ind.links.h)  # + het vak Tip (3 rijen)

    def test_elk_model_past_in_het_vak(self):
        for o, v in VRAGEN:
            for model in {id(m): m for m in (v.model, getattr(v, "model_na", None)) if m is not None}.values():
                for h, w in GROOTTES:
                    ind = I.oefenscherm(h, w, maatje=False)  # een groot model krijgt de volle breedte (vraag 2)
                    b = ind.links.binnen
                    s = Opnemer()
                    try:
                        M.teken_model(s, 0, model, x0=b.x, tekst=v.tekst, breedte=b.w)
                    except AttributeError:  # een model dat pixels wil: zonder pixels getekend
                        continue
                    if not s.puts:
                        continue
                    with self.subTest(model=type(model).__name__, o=o.id, h=h, w=w):
                        self.assertGreaterEqual(min(x for _, x, _, _ in s.puts), b.x)
                        self.assertLessEqual(max(r for _, _, r, _ in s.puts), b.x + b.w)


class TestOverzicht(unittest.TestCase):
    def test_reeks_regel(self):
        regel = OZ.reeks_regel([True, False], 2, 10, punten=5, op_rij=0)
        self.assertEqual(OZ.tekst(regel), "✔✘◉○○○○○○○   vraag 3 van 10  ·  juist 1 van 2  ·  punten +5")
        self.assertEqual(regel[0], ("✔", "goed"))
        self.assertEqual(regel[1], ("✘", "fout"))
        self.assertIn("3 op rij", OZ.tekst(OZ.reeks_regel([True] * 3, 3, 10, op_rij=3)))
        self.assertEqual(OZ.tekst(OZ.reeks_regel([], 0, 10, vrij=(2, 3))), "juist 2 van 3")  # geen punten: een examen

    def test_elk_teken_met_een_symbool(self):
        """Juist en fout hebben ook een symbool (er is een kleurenblind thema)."""
        self.assertEqual({t for t, _ in OZ.bolletjes([True, False], 2, 4)}, {"✔", "✘", "◉", "○"})


if __name__ == "__main__":
    unittest.main()
