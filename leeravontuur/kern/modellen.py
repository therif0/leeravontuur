"""Visuele modellen als gewone data. De terminal (of later een GUI) tekent ze.

Getallenlijn: van..tot met streepjes om de `stap`, een pijl (aflezen) en markeringen (sprongen).
Een getallenlijn kan inzoomen: het stuk tussen twee streepjes wordt de nieuwe lijn met 10 keer kleinere stappen.
"""

from dataclasses import dataclass, field, replace
from decimal import Decimal


@dataclass
class Getallenlijn:
    van: Decimal
    tot: Decimal
    stap: Decimal
    label_elke: int = 1              # elk hoeveelste streepje een getal krijgt
    pijl: Decimal | None = None      # een pijl die het kind moet aflezen
    markeringen: dict = field(default_factory=dict)  # waarde -> korte tekst (bv. "start")
    eenheid: str = ""                # bv. "°C" (thermometer)
    vulling: Decimal | None = None   # thermometer: gekleurd tot hier

    def streepjes(self):
        uit, x = [], self.van
        while x <= self.tot:
            uit.append(x)
            x += self.stap
        return uit

    def inzoomen(self, rond):
        """Het stuk [rond, rond + stap] wordt de nieuwe lijn, met stappen 10 keer kleiner."""
        nieuwe = self.stap / 10
        return replace(self, van=rond, tot=rond + self.stap, stap=nieuwe, label_elke=5, pijl=None,
                       markeringen={})

    def kan_inzoomen(self, minste_stap):
        return self.stap / 10 >= minste_stap

    def dichtst(self, waarde):
        """Het streepje dat het dichtst bij waarde ligt."""
        return min(self.streepjes(), key=lambda s: abs(s - waarde))


def lijn_rond(van, tot, stap, **kw):
    return Getallenlijn(Decimal(van), Decimal(tot), Decimal(stap), **kw)
