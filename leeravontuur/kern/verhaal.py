"""Sjablonen invullen tot zinnen met aanduidbare gegevens en sleutelwoorden (voor vraagstukken).

Een sjabloon is bv. `{wie} koopt {a ding} {waar}. *{elk:ding}* kost {p}.`:
  {wie}, {waar} …   een woord of zinsdeel uit de context
  {p}               een gegeven (een Gegeven): wordt een aanduidbaar stuk ('€ 3,20')
  {a ding}          een gegeven met het woord erbij: '1 broodje', '3 broodjes'
  {ding.enk/mv}     enkelvoud of meervoud; {de:ding}, {elk:ding}, {een:ding} met het juiste lidwoord
  {?}               de plaats van het invulvak in een antwoordzin
  *…*               een sleutelwoord (licht op bij de eerste tip)
Een woord is een dict {"enk", "mv", "lw"}; in de JSON-bestanden staat het als 'enkelvoud|meervoud|lidwoord'.
"""

import re

from .modellen import Gegeven, Stuk

VAK = "{?}"


def woord(spec):
    """'broodje|broodjes|het' → {'enk': 'broodje', 'mv': 'broodjes', 'lw': 'het'}."""
    enk, mv, lw = (spec.split("|") + ["", ""])[:3]
    return {"enk": enk, "mv": mv or enk, "lw": lw or "de"}


def _vorm(w, vorm):
    if vorm == "enk":
        return w["enk"]
    if vorm == "mv":
        return w["mv"]
    if vorm == "de":
        return f"{w['lw']} {w['enk']}"
    if vorm == "elk":
        return ("elk " if w["lw"] == "het" else "elke ") + w["enk"]
    if vorm == "een":
        return "een " + w["enk"]
    raise KeyError(vorm)


class SjabloonFout(KeyError):
    pass


def vul(sjabloon, ctx, hoofd=True):
    """Sjabloon → lijst van Stukken (met hoofd: de eerste letter van de zin wordt een hoofdletter)."""
    stukken, sleutel = [], False
    for deel in re.split(r"(\{[^{}]+\}|\*)", sjabloon):
        if not deel:
            continue
        if deel == "*":
            sleutel = not sleutel
            continue
        if not (deel.startswith("{") and deel.endswith("}")):
            stukken.append(Stuk(deel, sleutel=sleutel))
            continue
        naam = deel[1:-1]
        if naam == "?":
            stukken.append(Stuk(VAK))
            continue
        try:
            if " " in naam:  # {a ding}: een gegeven met het woord erbij
                gid, wid = naam.split(" ", 1)
                g, w = ctx[gid], ctx[wid]
                stukken.append(Stuk(g.tekst, gegeven=g.id, sleutel=sleutel))
                stukken.append(Stuk(" " + (w["enk"] if g.waarde == 1 else w["mv"]), sleutel=sleutel))
            elif ":" in naam:
                vorm, wid = naam.split(":", 1)
                stukken.append(Stuk(_vorm(ctx[wid], vorm), sleutel=sleutel))
            elif "." in naam:
                wid, vorm = naam.split(".", 1)
                stukken.append(Stuk(_vorm(ctx[wid], vorm), sleutel=sleutel))
            else:
                w = ctx[naam]
                if isinstance(w, Gegeven):
                    stukken.append(Stuk(w.tekst, gegeven=w.id, sleutel=sleutel))
                else:
                    stukken.append(Stuk(str(w), sleutel=sleutel))
        except KeyError as e:
            raise SjabloonFout(f"{naam} in '{sjabloon}'") from e
    return hoofdletter(stukken) if hoofd else stukken


def hoofdletter(stukken):
    """De eerste letter een hoofdletter ('s morgens → 's Morgens)."""
    for i, s in enumerate(stukken):
        t = s.tekst
        if not t.strip() or t == VAK:
            if t == VAK:
                return stukken
            continue
        j = 3 if t.startswith("'s ") else 0
        while j < len(t) and not t[j].isalpha():
            if t[j].isdigit():
                return stukken
            j += 1
        if j < len(t):
            stukken[i] = Stuk(t[:j] + t[j].upper() + t[j + 1:], s.gegeven, s.sleutel)
        return stukken
    return stukken


def tekst(stukken):
    return "".join(s.tekst for s in stukken)


def vul_tekst(sjabloon, ctx, hoofd=False):
    """Een sjabloon als gewone tekst (sleutelwoorden zonder sterretjes)."""
    return tekst(vul(sjabloon, ctx, hoofd))


def woorden(zinnen):
    """Zinnen (lijsten van Stukken) → woorden: elk woord is een lijst van (tekst, gegeven, sleutel).

    Een gegeven blijft één woord ('€ 3,20'); een leesteken plakt aan het woord ervoor."""
    uit, nieuw = [], True
    for zin in zinnen:
        nieuw = True
        for s in zin:
            if s.gegeven:
                if nieuw or not uit:
                    uit.append([])
                uit[-1].append((s.tekst, s.gegeven, s.sleutel))
                nieuw = False
                continue
            for i, stuk in enumerate(re.split(r"(\s+)", s.tekst)):
                if not stuk:
                    continue
                if stuk.isspace():
                    nieuw = True
                    continue
                if nieuw or not uit:
                    uit.append([])
                uit[-1].append((stuk, None, s.sleutel))
                nieuw = False
        nieuw = True
    return uit


def regels(zinnen, breedte):
    """Zinnen in regels van hoogstens `breedte` tekens. Elke regel = een lijst van woorden (zie woorden())."""
    uit, regel, lengte = [], [], 0
    for w in woorden(zinnen):
        n = sum(len(t) for t, _, _ in w)
        if regel and lengte + 1 + n > breedte:
            uit.append(regel)
            regel, lengte = [], 0
        lengte += n + (1 if regel else 0)
        regel.append(w)
    if regel:
        uit.append(regel)
    return uit
