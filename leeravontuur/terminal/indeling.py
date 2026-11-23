"""De indeling van de schermen met vakken (werk/schermen.md): welk vak waar staat, volgens de grootte van het scherm.

Eén plaats voor alle maten, zodat geen enkel scherm zelf kolommen telt:
- van 80×24 (de ondergrens) groeien de vakken mee tot GRENS_B × GRENS_H; op een groter scherm (bv. de tty, 240×67)
  blijft het blok zo groot en staat het in het midden (de vader 22/11);
- bovenaan de reeks (een vak vanaf GROOT_H rijen, anders één regel), links Vraag, Tip en Spiekbrief, ernaast het klad
  (alleen waar er een klad is), rechts het maatje;
- met het klokvenster open blijft de kolom van het maatje leeg: daar staat het venster (vraag 21).
De rijen 0 (de broodkruimel) en h - 1 (de toetsen) horen bij het hele scherm.
"""

from dataclasses import dataclass

MIN_B, MIN_H = 80, 24
GRENS_B, GRENS_H = 120, 40
GROOT_H = 30                 # vanaf zoveel rijen: de reeks in een vak en een band van 3 rijen rond de vraag
MAATJE_B, MAATJE_H = 20, 11  # de kolom van het maatje; zijn vak: 8 rijen pixels, het tekstje en de rand
KLAD_MIN, KLAD_MAX = 24, 34  # de kolom van het klad: zoveel kolommen moeten over zijn, en hoogstens zo breed
TIP_H, UITLEG_H = 6, 14      # het vak Tip (tijdens de vraag) en de uitleg (na het nakijken): hoogstens zo hoog
SPIEK_MIN = 4                # de spiekbrief komt onderaan als er zoveel rijen over zijn
BINNEN_X = 3                 # tekst in een vak: de rand, dan twee spaties


@dataclass(frozen=True)
class Rechthoek:
    y: int
    x: int
    h: int
    w: int

    @property
    def binnen(self):
        """Waar de tekst in het vak komt: binnen de rand, met twee spaties links en rechts."""
        return Rechthoek(self.y + 1, self.x + BINNEN_X, max(0, self.h - 2), max(0, self.w - 2 * BINNEN_X))

    @property
    def onder(self):
        return self.y + self.h

    @property
    def rechts(self):
        return self.x + self.w


@dataclass(frozen=True)
class Oefenscherm:
    blok: Rechthoek             # alles tussen de broodkruimel en de toetsen (in het midden op een groot scherm)
    groot: bool                 # genoeg rijen voor een vak Reeks en een band van 3 rijen
    reeks: Rechthoek            # het vak (of de ene regel) Reeks
    links: Rechthoek            # de kolom voor Vraag, Tip en Spiekbrief
    klad: Rechthoek | None      # de kolom van het klad (None: geen klad)
    maatje: Rechthoek | None    # de kolom van het maatje (None: geen maatje, of het klokvenster staat daar)


def blok(h, w):
    """Het blok tussen de broodkruimel en de toetsen: hoogstens GRENS_B × GRENS_H, in het midden."""
    bh, bw = min(h, GRENS_H) - 2, min(w, GRENS_B)
    return Rechthoek(1 + (h - 2 - bh) // 2, (w - bw) // 2, bh, bw)


def oefenscherm(h, w, maatje=True, klokvenster=False, klad=False, vraag_b=36):
    """De vakken van een oefenscherm. maatje = het kind wil zijn avatar zien; klokvenster = het klokvenster staat open
    (dan blijft de kolom van het maatje leeg); klad = deze vraag heeft een klad; vraag_b = zo breed moet het vak Vraag
    minstens zijn (het klad krijgt wat overblijft, KLAD_MIN tot KLAD_MAX)."""
    b = blok(h, w)
    groot = h >= GROOT_H
    rechts = MAATJE_B if maatje or klokvenster else 0
    reeks = Rechthoek(b.y, b.x, 3 if groot else 1, b.w - rechts)
    onder = reeks.onder
    hoog = b.onder - onder
    links_b = b.w - rechts
    klad_r = None
    if klad and links_b - vraag_b >= KLAD_MIN:
        kb = min(KLAD_MAX, links_b - vraag_b)
        klad_r = Rechthoek(onder, b.x + links_b - kb, hoog, kb)
        links_b -= kb
    m = Rechthoek(b.y, b.x + b.w - MAATJE_B, b.h, MAATJE_B) if maatje and not klokvenster else None
    return Oefenscherm(b, groot, reeks, Rechthoek(onder, b.x, hoog, links_b), klad_r, m)


def verdeel(links, vraag_h, bezig=True, spiek=True):
    """De kolom links: Vraag (vraag_h rijen, met de rand), daaronder Tip (of de uitleg na het nakijken) en, als er
    plaats is, de Spiekbrief tot onderaan. Geeft (vraag, tip, spiek of None)."""
    vraag = Rechthoek(links.y, links.x, vraag_h, links.w)
    rest = links.onder - vraag.onder
    th = min(rest, TIP_H if bezig else UITLEG_H)
    if not spiek:  # geen spiekbrief (een examen): een groot scherm krijgt geen groot leeg vak
        th = min(rest, 8 if bezig else UITLEG_H)
    elif rest - th < SPIEK_MIN:  # te weinig plaats: de tip krijgt 3 rijen, de spiekbrief de rest
        th = max(3, rest - SPIEK_MIN) if rest >= 3 + SPIEK_MIN else rest
    tip = Rechthoek(vraag.onder, links.x, th, links.w)
    sh = links.onder - tip.onder
    sp = Rechthoek(tip.onder, links.x, sh, links.w) if spiek and sh >= SPIEK_MIN else None
    return vraag, tip, sp
