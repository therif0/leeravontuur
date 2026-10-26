"""De menu's van het leerplan: Vak → Domein → Onderwerp + toets, en de Spiekbrieven.

Alles komt uit terminal/curriculum; hier staan geen namen van vakken, domeinen of onderwerpen. Een modus is een
toets op het gemarkeerde onderwerp, nooit een menu: na de toets komt hoogstens de bestaande keuze "Hoe moeilijk?"."""

from . import curriculum as CU
from .scherm import TerugNaar


def modi_voor(app, onderwerp):
    """De modi die dit kind nu kan kiezen: 60 seconden alleen als de ouder de timer zichtbaar liet."""
    return {m: f for m, f in onderwerp.modi.items() if m != "60s" or app.inst.timer_zichtbaar}


def enter_modus(modi):
    return next((m for m in CU.ENTER if m in modi), next(iter(modi)))


def toetsen_voor(app, onderwerp):
    """[(toets, knoptekst)] voor de voetregel: Enter, V, S, T, Z, H (alleen wat dit onderwerp heeft)."""
    modi = modi_voor(app, onderwerp)
    uit = [("Enter", CU.MODI[enter_modus(modi)])]
    if "vrij" in modi:
        uit.append((CU.TOETS["vrij"], CU.MODI["vrij"]))
    if onderwerp.spiek:
        uit.append((CU.SPIEK_TOETS, "spiekbrief"))
    uit += [(CU.TOETS[m], CU.MODI[m]) for m in ("60s", "20sommen", "tabel") if m in modi]
    return uit


def start(app, onderwerp, toets, kr):
    """Wat er gebeurt na een toets op een onderwerp (kr eindigt op het onderwerp)."""
    if toets == CU.SPIEK_TOETS:
        onderwerp.spiek.toon(app, kr + ["Spiekbrief"])
        return
    modi = modi_voor(app, onderwerp)
    modus = enter_modus(modi) if toets == "Enter" else next(m for m, t in CU.TOETS.items() if t == toets)
    modi[modus](app, kr)


def kort(tekst, breedte):
    """Inkorten op een woordgrens (met …) zodat de grijze uitleg niet midden in een woord stopt."""
    if len(tekst) <= breedte:
        return tekst
    return tekst[:max(0, breedte - 1)].rsplit(" ", 1)[0].rstrip(",") + "…"


def opties_met_uitleg(app, items):
    """[(label, uitleg)] met de uitleg ingekort tot wat naast de labels past (zoals Scherm.menu ze zet)."""
    breed = max(len(x.label) for x in items)
    plaats = app.s.maat()[1] - (13 + breed) - 1  # " n. " + label + " " vanaf kolom 6, uitleg 2 verder
    return [(x.label, kort(x.uitleg, plaats)) for x in items]


def _menu(app, kr, vraag, items, open_item):
    """Een gewoon keuzemenu (vak of domein) dat na een keuze op dezelfde plek terugkomt."""
    sel = 0
    while True:
        try:
            k = app.s.menu(kr, vraag, opties_met_uitleg(app, items), start=sel)
            if k is None:
                return
            sel = k
            open_item(items[k], kr + [items[k].label])
        except TerugNaar as t:
            if t.niveau < len(kr) - 1:
                raise


def vak(app, vak_, kr):
    """Hoofdmenu › Vak: de domeinen."""
    _menu(app, kr + [vak_.label], "Welk onderwerp?", vak_.domeinen, lambda d, kr_: domein(app, d, kr_))


def domein(app, domein_, kr):
    """Vak › Domein: de onderwerpen, met per onderwerp de toetsen in de voetregel."""
    sel = 0
    while True:
        try:
            onderwerpen = domein_.onderwerpen
            k = app.s.menu(kr, f"{domein_.label}: wat wil je oefenen?",
                           opties_met_uitleg(app, onderwerpen), start=sel,
                           toetsen=[toetsen_voor(app, o) for o in onderwerpen])
            if k is None:
                return
            sel, toets = k
            start(app, onderwerpen[sel], toets, kr + [onderwerpen[sel].label])
        except TerugNaar as t:
            if t.niveau < len(kr) - 1:
                raise


def spiekbrieven(app, kr):
    """Hoofdmenu › Spiekbrieven › Vak › Domein › de spiekbrieven van dat domein (elke één keer)."""
    _menu(app, kr, "Welk vak?", CU.VAKKEN, lambda v, kr_: _menu(
        app, kr_, "Welk onderwerp?", v.domeinen, lambda d, kr2: _spiek_lijst(app, d, kr2)))


def _spiek_lijst(app, domein_, kr):
    brieven = list({o.spiek.titel: o.spiek for o in domein_.onderwerpen if o.spiek}.values())
    sel = 0
    while True:
        try:
            k = app.s.menu(kr, "Welke spiekbrief?", [(b.titel, "") for b in brieven], start=sel)
            if k is None:
                return
            sel = k
            brieven[k].toon(app, kr + [brieven[k].titel])
        except TerugNaar as t:
            if t.niveau < len(kr) - 1:
                raise
