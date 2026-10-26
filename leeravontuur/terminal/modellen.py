"""Visuele modellen tekenen (de data komt uit kern/modellen.py).

De getallenlijn neemt 4 rijen in:  y   tekstjes bij markeringen ("start", "nu")
                                   y+1 pijlen ▼ (aflezen, markeringen, de pijl van het kind)
                                   y+2 de lijn met streepjes (en de vulling van een thermometer)
                                   y+3 de getallen onder de streepjes
"""

import math
from decimal import Decimal

from ..kern.getal import fmt
from ..kern.modellen import (Breukbalk, Breukbalken, Figuur, Getallenlijn, Groepjes, Hoek, Honderdveld, Kaart,
                             Procentstrook, Wijzerklok)
from . import thema

HOOGTE = 4


def posities(lijn, x0=4, breedte=72):
    """x-positie van elk streepje."""
    n = max(1, len(lijn.streepjes()) - 1)
    sp = max(1, breedte // n)
    return [x0 + i * sp for i in range(n + 1)], sp


def teken_getallenlijn(s, y, lijn, cursor=None, cursor_rol="cursor", goed_bij=None, actie=None, x0=4,
                       breedte=72):
    """Tekent de lijn. cursor = index van het streepje met de pijl van het kind.
    goed_bij = waarde die als juist getoond wordt (na het nakijken).
    actie(i) = klikactie voor streepje i (dan wordt elk streepje klikbaar)."""
    streepjes = lijn.streepjes()
    xs, sp = posities(lijn, x0, breedte)
    links, rechts = xs[0] - 2, xs[-1] + 2
    # de lijn
    vul_tot = None
    if lijn.vulling is not None:
        vul_tot = xs[streepjes.index(lijn.dichtst(lijn.vulling))]
    for x in range(links, rechts + 1):
        if vul_tot is not None and xs[0] <= x <= vul_tot:
            s.put(y + 2, x, "━", "fout")
        else:
            s.put(y + 2, x, "─", "dim")
    s.put(y + 2, rechts + 1, "▶", "dim")
    for i, (x, w) in enumerate(zip(xs, streepjes)):
        gelabeld = i % max(1, lijn.label_elke) == 0 or i == len(xs) - 1
        if vul_tot is not None and x <= vul_tot:
            s.put(y + 2, x, "╋", "fout")
        else:
            s.put(y + 2, x, "┼", "bold" if gelabeld else "")
        if gelabeld:
            tekst = fmt(w)
            s.put(y + 3, max(0, x - len(tekst) // 2), tekst, "bold")
    if lijn.eenheid:
        s.put(y + 3, rechts + 2, lijn.eenheid, "bold")
    # markeringen en pijlen
    for waarde, tekst in lijn.markeringen.items():
        if lijn.van <= waarde <= lijn.tot:
            x = xs[streepjes.index(lijn.dichtst(waarde))]
            s.put(y, max(0, x - len(tekst) // 2), tekst, "accent2")
            s.put(y + 1, x, "▼", "accent2")
    if lijn.pijl is not None:
        s.put(y + 1, xs[streepjes.index(lijn.dichtst(lijn.pijl))], "▼", "accent")
    if goed_bij is not None and lijn.van <= goed_bij <= lijn.tot and goed_bij in streepjes:
        x = xs[streepjes.index(goed_bij)]
        s.put(y, max(0, x - 3), "juist", "goed")
        s.put(y + 1, x, "▼", "goed")
    if cursor is not None:
        s.put(y + 1, xs[cursor], "▼", cursor_rol)
    if actie is not None:
        for i, x in enumerate(xs):
            s.zones.voeg(y + 1, x - sp // 2, 3, max(1, sp), actie(i))
    return xs


# ---- breuken ---------------------------------------------------------------------------------------------

BALK_B = 52  # breedte van een breukbalk (rechts blijft plaats voor het label en het maatje)


def stuk_grenzen(noemer, x0, breedte=BALK_B):
    """[(x_begin, x_eind)] per stuk; x_begin is de scheidingslijn links van het stuk."""
    return [(x0 + i * breedte // noemer, x0 + (i + 1) * breedte // noemer) for i in range(noemer)]


def teken_balk(s, y, noemer, gearceerd, x0=8, label="", actie=None, hoogte=2):
    """Een breukbalk van `hoogte` rijen. Gearceerd = █, wit = ░, │ tussen de stukken. Geeft de rechterrand."""
    grenzen = stuk_grenzen(noemer, x0)
    for rij in range(hoogte):
        for i, (a, b) in enumerate(grenzen):
            s.put(y + rij, a, "│", "dim")
            vol = i in gearceerd
            s.put(y + rij, a + 1, ("█" if vol else "░") * max(0, b - a - 1), "accent2" if vol else "dim")
        s.put(y + rij, grenzen[-1][1], "│", "dim")
    if actie is not None:
        for i, (a, b) in enumerate(grenzen):
            s.zones.voeg(y, a + 1, hoogte, max(1, b - a - 1), actie(i))
    rechts = grenzen[-1][1]
    if label:
        s.put(y, rechts + 2, label, "bold")
    return rechts


def teken_groepjes(s, y, g, x0=8, breedte=68):
    """Bolletjes in groepjes: (●●●●) (●●●●) (○○○○). Geeft (hoogte, breedte)."""
    per = g.totaal // g.groepen
    # tot 12 per groepje: bolletjes; meer: een getal per groepje (of ? zolang de vraag loopt)
    inhoud = "●" * per if per <= 12 else (f" {per} " if g.gekleurd else " ? ")
    x, yy, rechts = x0, y, x0
    for i in range(g.groepen):
        stuk = len(inhoud) + 3
        if x + stuk > x0 + breedte:
            x, yy = x0, yy + 1
        gekleurd = i < g.gekleurd
        s.put(yy, x, "(", "dim")
        s.put(yy, x + 1, inhoud, "goed" if gekleurd else ("bold" if not g.gekleurd else "dim"))
        s.put(yy, x + 1 + len(inhoud), ")", "dim")
        x += stuk
        rechts = max(rechts, x)
    return yy - y + 1, rechts - x0


def teken_model(s, y, model, x0=8, uitslag=None, tekst=""):
    """Tekent een model uit kern/modellen.py. Geeft (hoogte, breedte). uitslag (True/False/None, na het nakijken)
    en tekst (de vraag) gebruikt alleen de klok, voor het klokvenster."""
    if isinstance(model, Breukbalk):
        rechts = teken_balk(s, y, model.noemer, model.gearceerd, x0, model.label)
        return 2, rechts - x0 + 2 + len(model.label)
    if isinstance(model, Breukbalken):
        rechts = x0
        for i, balk in enumerate(model.balken):
            rechts = max(rechts, teken_balk(s, y + 2 * i, balk.noemer, balk.gearceerd, x0, balk.label, hoogte=1)
                         + 2 + len(balk.label))
        return 2 * len(model.balken) - 1, rechts - x0
    if isinstance(model, Groepjes):
        return teken_groepjes(s, y, model, x0)
    if isinstance(model, Getallenlijn):
        teken_getallenlijn(s, y + 1, model)
        return 5, 76
    if isinstance(model, Honderdveld):
        return teken_veld(s, y, model.gekleurd)
    if isinstance(model, Procentstrook):
        return teken_strook(s, y, model, x0)
    if isinstance(model, Figuur):
        return teken_figuur(s, y, model, x0)
    if isinstance(model, Kaart):
        return teken_kaart(s, y, model, x0)
    if isinstance(model, Hoek):
        return teken_hoek(s, y, model.graden, x0)
    if isinstance(model, Wijzerklok):
        return teken_klok(s, y, model, x0, uitslag=uitslag, tekst=tekst)
    return 0, 0


# ---- procenten -----------------------------------------------------------------------------------------

def teken_veld(s, y, gekleurd, x0=10, cursor=None, actie=None, rij_actie=None):
    """Het honderdveld: 10 rijen van 10 vakjes (elk 2 tekens breed). Geeft (hoogte, breedte)."""
    for r in range(10):
        if rij_actie is not None:
            s.put(y + r, x0 - 2, "▶", "dim")
            s.zones.voeg(y + r, x0 - 2, 1, 1, rij_actie(r))
        for c in range(10):
            i = r * 10 + c
            vol = i in gekleurd
            rol = "cursor" if cursor == i else ("accent2" if vol else "dim")
            s.put(y + r, x0 + 2 * c, "■" if vol else "□", rol)  # met een spatie ertussen: telbaar
            if actie is not None:
                s.zones.voeg(y + r, x0 + 2 * c, 1, 2, actie(i))
    return 10, 20 + (x0 - 8)


STROOK_B = 50


def teken_strook(s, y, strook, x0=8):
    """Procentstrook: 0 % … 100 % boven 0 … totaal, met een pijl bij het gevraagde percentage."""
    def x(p):
        return x0 + int(Decimal(p) * STROOK_B / 100)
    xp = x(strook.procent)
    s.put(y, xp, f"▼ {fmt(strook.procent)} %", "accent")
    for xx in range(x0, x0 + STROOK_B + 1):
        s.put(y + 1, xx, "█" if xx <= xp else "░", "accent2" if xx <= xp else "dim")
    for p in (0, 25, 50, 75, 100):
        tekst = f"{p} %"
        s.put(y + 2, min(x(p), x0 + STROOK_B - len(tekst) + 1) if p else x0, tekst, "dim")
    eenheid = f" {strook.eenheid}" if strook.eenheid else ""
    s.put(y + 3, x0, "0", "bold")
    totaal = fmt(strook.totaal) + eenheid
    s.put(y + 3, x0 + STROOK_B - len(totaal) + 1, totaal, "bold")
    if strook.toon_deel:
        deel = fmt(strook.totaal * strook.procent / 100) + eenheid
        if x0 + 2 < xp - len(deel) // 2 and xp + len(deel) < x0 + STROOK_B - len(totaal):
            s.put(y + 3, xp - len(deel) // 2, deel, "goed")
    return 4, STROOK_B + 8


# ---- meetkunde -----------------------------------------------------------------------------------------

VAK_B = 4  # een vakje van het cm²-rooster: 3 tekens binnenin + de lijn


def figuur_pixels(fig):
    """Het cm²-rooster als pixels (elk vakje 4 × 4: 1 pixel lijn en 3 × 3 vulling, dus vierkant).
    Geeft een raster van pixelrollen: None, "lijn", "vulling" of "rand" (de omtrek, als fig.rand)."""
    def gekleurd(r, k):
        return (r, k) in fig.vakjes

    hoog, breed = 4 * fig.rijen + 1, 4 * fig.kolommen + 1
    p = [["lijn" if y % 4 == 0 or x % 4 == 0 else None for x in range(breed)] for y in range(hoog)]
    for r in range(fig.rijen):
        for k in range(fig.kolommen):
            for i in range(3):
                for j in range(3):
                    # een half vakje: de driehoek linksonder (rij 1: 1 pixel, rij 2: 2, rij 3: 3)
                    if gekleurd(r, k) or ((r, k) in fig.halve and j <= i):
                        p[4 * r + 1 + i][4 * k + 1 + j] = "vulling"
    if fig.rand:
        for r in range(fig.rijen + 1):
            for k in range(fig.kolommen + 1):
                if k < fig.kolommen and gekleurd(r - 1, k) != gekleurd(r, k):  # randje boven vakje (r, k)
                    for x in range(4 * k, 4 * k + 5):
                        p[4 * r][x] = "rand"
                if r < fig.rijen and gekleurd(r, k - 1) != gekleurd(r, k):  # randje links van vakje (r, k)
                    for y in range(4 * r, 4 * r + 5):
                        p[y][4 * k] = "rand"
    return p


def kan_pixels_rooster(s):
    """Kan het rooster met gekleurde halfblokken (anders: met lijntekens)?"""
    inst = getattr(s, "inst", None)
    return (getattr(s, "kleuren", False) and not getattr(s, "ascii", True) and inst is not None
            and inst.thema != "geen-kleur" and thema.pixels_mogelijk()
            and thema.rol_pixel("lijn", "vulling", inst.thema) != 0)


def teken_figuur(s, y, fig, x0=8):
    """Een figuur op een rooster; elk vakje = 1 cm², een echt vierkant. Met fig.rand wordt de omtrek aangeduid.
    Geeft (hoogte, breedte)."""
    if not kan_pixels_rooster(s):
        return teken_figuur_tekens(s, y, fig, x0)
    naam = s.inst.thema
    p = figuur_pixels(fig)
    for t in range((len(p) + 1) // 2):
        boven, onder = p[2 * t], p[2 * t + 1] if 2 * t + 1 < len(p) else [None] * len(p[0])
        for x, (b, o) in enumerate(zip(boven, onder)):
            if b is None and o is None:
                continue
            if b == o:
                s.put(y + t, x0 + x, "█", thema.rol_pixel(b, None, naam))
            elif b is None:
                s.put(y + t, x0 + x, "▄", thema.rol_pixel(o, None, naam))
            else:
                s.put(y + t, x0 + x, "▀", thema.rol_pixel(b, o, naam))
    hoogte = (len(p) + 1) // 2
    # de legende (2 regels): hetzelfde vierkantje en driehoekje van 3 × 3 pixels als in het rooster
    vul = thema.rol_pixel("vulling", None, naam)
    s.put(y + hoogte, x0, "███", vul)
    s.put(y + hoogte + 1, x0, "▀▀▀", vul)
    s.put(y + hoogte, x0 + 4, "= 1 cm²", "dim")
    breed = 11
    if fig.halve:
        s.put(y + hoogte, x0 + 15, "█▄", vul)
        s.put(y + hoogte + 1, x0 + 15, "▀▀▀", vul)
        s.put(y + hoogte, x0 + 19, "= een half vakje", "dim")
        breed = 35
    return hoogte + 2, max(len(p[0]), breed)


def teken_figuur_tekens(s, y, fig, x0=8):
    """Terugval zonder kleuren of in ASCII-modus: het rooster met lijntekens."""
    def gekleurd(r, k):
        return (r, k) in fig.vakjes

    for r in range(fig.rijen + 1):
        for k in range(fig.kolommen + 1):
            s.put(y + 2 * r, x0 + VAK_B * k, "┼", "dim")
            if k < fig.kolommen:  # horizontaal randje boven vakje (r, k)
                rand = fig.rand and gekleurd(r - 1, k) != gekleurd(r, k)
                s.put(y + 2 * r, x0 + VAK_B * k + 1, "━━━" if rand else "───", "accent" if rand else "dim")
            if r < fig.rijen:  # verticaal randje links van vakje (r, k)
                rand = fig.rand and gekleurd(r, k - 1) != gekleurd(r, k)
                s.put(y + 2 * r + 1, x0 + VAK_B * k, "┃" if rand else "│", "accent" if rand else "dim")
                if (r, k) in fig.vakjes:
                    s.put(y + 2 * r + 1, x0 + VAK_B * k + 1, "███", "accent2")
                elif (r, k) in fig.halve:
                    s.put(y + 2 * r + 1, x0 + VAK_B * k + 1, "▒▒▒", "accent2")
    hoogte = 2 * fig.rijen + 1
    legende = "███ = 1 cm²" + ("   ▒▒▒ = een half vakje" if fig.halve else "")
    s.put(y + hoogte, x0, legende, "dim")
    s.put(y + hoogte, x0, "███", "accent2")
    if fig.halve:
        s.put(y + hoogte, x0 + legende.index("▒"), "▒▒▒", "accent2")
    return hoogte + 1, max(VAK_B * fig.kolommen + 1, len(legende))


KAART_B = 3  # breedte van een kolom op de schatkaart


def kaart_plaats(kaart, x, y, y0, x0=8):
    """(rij, kolom) op het scherm van punt (x, y) van de kaart."""
    return y0 + kaart.ys()[::-1].index(y), x0 + 3 + KAART_B * kaart.xs().index(x) + 1


def teken_kaart(s, y0, kaart, x0=8, cursor=None, actie=None):
    """De schatkaart (kolommen A, B … onderaan, rij 1 onderaan) of een assenstelsel. cursor = (x, y) van het kind,
    actie(x, y) = klikactie per punt. Geeft (hoogte, breedte)."""
    xs, ys = kaart.xs(), kaart.ys()
    for i, yy in enumerate(ys[::-1]):
        rij = y0 + i
        s.put(rij, x0, f"{fmt_getal(yy):>2}", "bold")
        for xx in xs:
            _, kol = kaart_plaats(kaart, xx, yy, y0, x0)
            if kaart.assen and yy == 0:
                s.put(rij, kol - 1, "───", "dim")
            teken = "┼" if kaart.assen and xx == 0 and yy == 0 else (
                "│" if kaart.assen and xx == 0 else ("─" if kaart.assen and yy == 0 else "·"))
            s.put(rij, kol, teken, "dim")
            if (xx, yy) in kaart.punten:
                punt = kaart.punten[(xx, yy)]
                teken, rol = punt if isinstance(punt, tuple) else (punt, "accent")
                s.put(rij, kol, teken, rol)
            if cursor == (xx, yy):
                s.put(rij, kol - 1, "[", "cursor")
                s.put(rij, kol + 1, "]", "cursor")
            if actie is not None:
                s.zones.voeg(rij, kol - 1, 1, KAART_B, actie(xx, yy))
    onder = y0 + len(ys)
    for xx in xs:
        _, kol = kaart_plaats(kaart, xx, ys[0], y0, x0)
        tekst = kaart.naam(xx, 1)[0] if not kaart.assen else fmt_getal(xx)
        s.put(onder, kol - (len(tekst) - 1), tekst, "bold")
    return len(ys) + 1, 3 + KAART_B * len(xs) + 1


def fmt_getal(n):
    return f"−{-n}" if n < 0 else str(n)


HOEK_R = 6  # lengte van een been, in rijen


def hoek_teken(graden):
    """Het lijnteken voor een been onder deze hoek."""
    if graden < 20 or graden > 160:
        return "─"
    if graden < 70:
        return "╱"
    if graden <= 110:
        return "│"
    return "╲"


def teken_hoek(s, y, graden, x0=8):
    """Een hoek: het ene been naar rechts, het andere onder `graden` (tegen de klok in). Geeft (hoogte, breedte).
    Het schuine been krijgt één lijnteken per rij; bij een vlakke hoek verbindt '_' de tekens."""
    hoekpunt_y, hoekpunt_x = y + HOEK_R, x0 + 2 * HOEK_R + 4
    s.put(hoekpunt_y, hoekpunt_x + 1, "─" * (2 * HOEK_R + 4), "bold")
    if graden in (0, 180):
        if graden == 180:
            s.put(hoekpunt_y, hoekpunt_x - 2 * HOEK_R - 4, "─" * (2 * HOEK_R + 4), "bold")
    else:
        teken = hoek_teken(graden)
        stap = 2 / math.tan(math.radians(graden)) if graden != 90 else 0  # kolommen per rij (een teken is 2× zo hoog)
        lengte = 2 * HOEK_R + 4  # het schuine been mag niet verder dan het rechte
        rijen = HOEK_R if abs(stap) * HOEK_R <= lengte else max(1, int(lengte / abs(stap)))
        vorige = hoekpunt_x
        for r in range(1, rijen + 1):
            kol = hoekpunt_x + max(-lengte, min(lengte, round(r * stap)))
            if abs(kol - vorige) > 1:  # vlakke hoek: de tussenruimte verbinden
                van, tot = sorted((vorige, kol))
                s.put(hoekpunt_y - r, van + 1, "_" * (tot - van - 1), "bold")
            s.put(hoekpunt_y - r, kol, teken, "bold")
            vorige = kol
    s.put(hoekpunt_y, hoekpunt_x, "●", "accent")
    return HOEK_R + 1, 4 * HOEK_R + 9


# ---- de wijzerklok -------------------------------------------------------------------------------------------

KLOK_R = 10  # straal in pixels: de wijzerplaat is 21 × 21 pixels = 21 tekens breed en 11 rijen hoog


def klok_pixels(klok, r=KLOK_R):
    """De wijzerklok als pixels: None, "lijn" (rand en streepjes), "rand" (de korte uurwijzer, dik) of
    "vulling" (de lange minutenwijzer)."""
    n = 2 * r + 1
    p = [[None] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            if abs(math.hypot(x - r, y - r) - r) < 0.5:
                p[y][x] = "lijn"
    for uur in range(12):
        a = math.radians(uur * 30)
        p[round(r - (r - 1.4) * math.cos(a))][round(r + (r - 1.4) * math.sin(a))] = "lijn"
    if klok.wijzers:
        uur_hoek, min_hoek = klok.hoeken()
        # eerst de uurwijzer, dan de minutenwijzer erbovenop (zoals bij een echte klok)
        for rol, hoek, lengte, dik in (("rand", uur_hoek, r * 0.55, True), ("vulling", min_hoek, r - 2, False)):
            a = math.radians(hoek)
            stap = 0.0
            while stap <= lengte:
                x, y = r + stap * math.sin(a), r - stap * math.cos(a)
                plekken = [(round(x), round(y))]
                if dik:  # aan beide kanten een pixel erbij, loodrecht op de wijzer
                    plekken += [(round(x + k * math.cos(a)), round(y + k * math.sin(a))) for k in (-0.8, 0.8)]
                for px, py in plekken:
                    if 0 <= px < n and 0 <= py < n:
                        p[py][px] = rol
                stap += 0.25
    return p


def teken_pixels(s, y, x0, p):
    """Een raster van pixelrollen tekenen met ▀/▄-halfblokken (2 pixels per teken). Geeft het aantal rijen."""
    naam = s.inst.thema
    for t in range((len(p) + 1) // 2):
        boven, onder = p[2 * t], p[2 * t + 1] if 2 * t + 1 < len(p) else [None] * len(p[0])
        for x, (b, o) in enumerate(zip(boven, onder)):
            if b is None and o is None:
                continue
            if b == o:
                s.put(y + t, x0 + x, "█", thema.rol_pixel(b, None, naam))
            elif b is None:
                s.put(y + t, x0 + x, "▄", thema.rol_pixel(o, None, naam))
            else:
                s.put(y + t, x0 + x, "▀", thema.rol_pixel(b, o, naam))
    return (len(p) + 1) // 2


VENSTER_TEKST = "De klok staat in een eigen venster."
VENSTER_HULP = "Zie je hem niet? Druk F2: dan komt hij hier."


def teken_klok(s, y, klok, x0=8, actie=None, uitslag=None, juist=None, tekst=""):
    """Een ronde wijzerklok. Staat er een klokvenster open (terminal/venster.py), dan komt de klok daar en
    tekent de terminal alleen een verwijzing: geeft dan (2, breedte). Anders een klok met 12, 3, 6 en 9
    erbuiten: (13, 25). Met actie(dx, dy) is elk vakje van de wijzerplaat klikbaar (dx, dy in pixels vanaf het
    midden). uitslag (True/False/None) en juist (zo moest het) zijn voor het venster, tekst = de vraag."""
    venster = getattr(s, "klokvenster", None)
    if venster is not None:
        onder, rol = "", ""
        if uitslag is True:
            onder, rol = "✔ Juist!", "goed"
        elif uitslag is False:
            onder, rol = ("✘ De groene wijzers tonen hoe het moest." if juist is not None else
                          "✘ Niet juist. De uitleg staat in het andere venster."), "fout"
        if venster.toon(klok.minuten, tekst, klikbaar=actie is not None, juist=juist,
                        uitslag={True: "goed", False: "fout"}.get(uitslag), onder=onder, onder_rol=rol):
            s.put(y, x0, "◷ " + VENSTER_TEKST, "accent")
            s.put(y + 1, x0 + 2, VENSTER_HULP, "dim")
            s.zones.voeg(y, x0, 2, len(VENSTER_HULP) + 2, ("klokvenster",))
            return 2, len(VENSTER_HULP) + 2
    r = KLOK_R
    p = klok_pixels(klok)
    xk = x0 + 2  # de wijzerplaat (met links plaats voor de 9)
    s.put(y, xk + r - 1, "12", "bold")
    s.put(y + 1 + r // 2, x0, "9", "bold")
    s.put(y + 1 + r // 2, xk + 2 * r + 2, "3", "bold")
    s.put(y + 2 + r, xk + r, "6", "bold")
    if kan_pixels_rooster(s):
        teken_pixels(s, y + 1, xk, p)
    else:  # met tekens: # = de korte uurwijzer, * = de lange minutenwijzer
        for t in range((len(p) + 1) // 2):
            for x in range(len(p[0])):
                cel = {p[2 * t][x], p[2 * t + 1][x] if 2 * t + 1 < len(p) else None}
                teken = "#" if "rand" in cel else "*" if "vulling" in cel else "." if "lijn" in cel else None
                if teken:
                    s.put(y + 1 + t, xk + x, teken, "accent" if teken == "#" else "bold" if teken == "*" else "dim")
    s.put(y + 1 + r // 2, xk + r, "o" if not kan_pixels_rooster(s) else "●", "bold")
    if actie:
        for t in range(r + 1):
            for x in range(2 * r + 1):
                s.zones.voeg(y + 1 + t, xk + x, 1, 1, actie(x - r, 2 * t - r))
    return 2 * r // 2 + 3, 2 * r + 5
