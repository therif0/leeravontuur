"""Wat de vakken rond een oefening tonen (Reeks, Vandaag, Herhaalbak, fris houden, laatst geoefend), als regels met
rollen (gouden regels 1 en 2: de kern rekent, het scherm tekent alleen). Zonder curses.

Een regel is een lijst stukken (tekst, rol); `tekst(regel)` plakt ze aan elkaar.
"""

from . import herhaling, klok, reeks

JUIST, FOUT, NU, LATER = ("✔", "goed"), ("✘", "fout"), ("◉", "accent"), ("○", "dim")


def tekst(regel):
    return "".join(t for t, _ in regel)


def bolletjes(goed, nr, totaal):
    """Een teken per vraag van de reeks: ✔ ✘ voor de beantwoorde (goed = lijst van True/False, ook de vraag die net
    nagekeken is), ◉ de vraag van nu, ○ wat nog komt."""
    uit = []
    for i in range(totaal):
        if i < len(goed):
            uit.append(JUIST if goed[i] else FOUT)
        else:
            uit.append(NU if i == nr else LATER)
    return uit


def reeks_regel(goed, nr, totaal, punten=None, op_rij=0, vrij=None):
    """De regel Reeks: de bolletjes en "vraag 3 van 10 · juist 1 van 2 · punten +5 · 3 op rij". vrij = (juist, gedaan)
    bij vrij oefenen (geen bolletjes); punten = None als de reeks geen punten geeft (een examen)."""
    if vrij is not None:
        regel, delen = [], [f"juist {vrij[0]} van {vrij[1]}"]
    else:
        regel = bolletjes(goed, nr, totaal) + [("   ", "")]
        delen = [f"vraag {nr + 1} van {totaal}"] + ([f"juist {sum(goed)} van {len(goed)}"] if goed else [])
    if punten is not None:
        delen.append(f"punten +{punten}")
    if op_rij >= 2:
        delen.append(f"{op_rij} op rij")
    return regel + [("  ·  ".join(delen), "dim")]


def vandaag_regel(opslag, kind_id):
    """'14 van 17 juist' vandaag, of [] als er vandaag nog niets geoefend werd."""
    n, j = opslag.telling(kind_id, klok.dag())
    return [(f"{j} van {n} juist", "")] if n else []


def herhaalbak_regel(opslag, kind_id):
    """Hoeveel herhaalvragen er vandaag aan de beurt zijn."""
    n = len(herhaling.aan_de_beurt(opslag, kind_id))
    return [(f"{n} {'herhaalvraag' if n == 1 else 'herhaalvragen'}", "accent" if n else "dim")]


def _dagen(n):
    return "vandaag" if n == 0 else "gisteren" if n == 1 else f"{n} dagen geleden"


def onderwerp_regels(opslag, kind_id, vaardigheid):
    """Over één onderwerp (het kaartje bij een menu): laatst geoefend, juist van de laatste antwoorden, fris houden en
    de herhaalbak. Een lijst (label, waarde, rol); [] als het nog nooit geoefend werd."""
    st = reeks.stand(opslag, kind_id, vaardigheid)
    if st is None:
        return []
    stand, dagen = st
    recent = opslag.recente_antwoorden(kind_id, vaardigheid, 10)
    juist = sum(bool(a["juist"]) for a in recent)
    regels = [("Laatst geoefend", _dagen(dagen), ""), ("Juist", f"{juist} van {len(recent)}", "")]
    if stand == herhaling.FRIS_HOUDEN:
        regels.append(("Fris houden", "nu oefenen: dat zakt anders weg", "accent"))
    elif stand == herhaling.BEHEERST:
        nog = max(0, herhaling.FRIS_DAGEN - dagen)
        regels.append(("Fris houden", f"nog {nog} {'dag' if nog == 1 else 'dagen'}", "dim"))
    bak = sum(1 for i in opslag.herhaalbak(kind_id) if i["vaardigheid"] == vaardigheid)
    if bak:
        regels.append(("Herhaalbak", f"{bak} {'vraag' if bak == 1 else 'vragen'}", "accent"))
    return regels
