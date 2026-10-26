"""De wijzerklok als vormen (alleen data): cirkels, lijnen en tekst in een vak van `maat` × `maat` punten.

tkinter tekent ze in het klokvenster, `naar_svg` maakt er een beeld van voor de handleiding, en de tests kijken
er de wijzers mee na. Geen tkinter hier, zodat dit overal werkt.
"""

import html
import math

# kleuren van een leerklok; uur en minuten zijn blauw en oranje (ook te onderscheiden bij kleurenblindheid),
# en de uurwijzer is bovendien korter en dikker
KLEUR = {
    "plaat": "#fffdf5", "ring": "#334155", "streep": "#475569", "fijn": "#94a3b8", "cijfer": "#1e293b",
    "minuutcijfer": "#64748b", "uur": "#2563eb", "minuut": "#ea580c", "as": "#1e293b",
    "goed": "#16a34a", "fout": "#dc2626", "achtergrond": "#f1f5f9", "juist": "#16a34a",
}


def hoeken(minuten):
    """(uurhoek, minuuthoek) in graden, met de klok mee vanaf 12."""
    u, m = divmod(int(minuten) % 720, 60)
    return (u + m / 60) * 30, m * 6


def punt(cx, cy, straal, hoek):
    a = math.radians(hoek)
    return cx + straal * math.sin(a), cy - straal * math.cos(a)


def vormen(minuten, maat=320, juist=None, uitslag=None, minuutcijfers=True):
    """De klok op `minuten` (na middernacht; een wijzerklok toont 12 uur).

    juist: een tweede tijd met groene, gestreepte wijzers (zo moest het), uitslag: None, "goed" of "fout"
    (de kleur van de ring)."""
    c = maat / 2
    r = maat * 0.40
    uit = [{"soort": "cirkel", "x": c, "y": c, "r": r, "vul": KLEUR["plaat"],
            "lijn": KLEUR[uitslag] if uitslag in ("goed", "fout") else KLEUR["ring"], "dikte": maat * 0.025}]
    for m in range(60):
        groot = m % 5 == 0
        x1, y1 = punt(c, c, r * (0.86 if groot else 0.92), m * 6)
        x2, y2 = punt(c, c, r * 0.97, m * 6)
        uit.append({"soort": "lijn", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "kleur": KLEUR["streep" if groot else "fijn"], "dikte": maat * (0.012 if groot else 0.005)})
    for uur in range(1, 13):
        x, y = punt(c, c, r * 0.70, uur * 30)
        uit.append({"soort": "tekst", "x": x, "y": y, "tekst": str(uur), "grootte": maat * 0.075,
                    "kleur": KLEUR["cijfer"], "vet": True})
    if minuutcijfers:  # klein, buiten de ring: op 1 = 5 minuten, op 2 = 10 …
        for m in range(0, 60, 5):
            x, y = punt(c, c, r * 1.13, m * 6)
            uit.append({"soort": "tekst", "x": x, "y": y, "tekst": f"{m:02d}" if m < 10 else str(m),
                        "grootte": maat * 0.038, "kleur": KLEUR["minuutcijfer"], "vet": False})
    if juist is not None and int(juist) % 720 != int(minuten) % 720:
        uit += _wijzers(c, r, maat, juist, schaduw=True)
    uit += _wijzers(c, r, maat, minuten)
    uit.append({"soort": "cirkel", "x": c, "y": c, "r": maat * 0.022, "vul": KLEUR["as"], "lijn": KLEUR["as"],
                "dikte": 1})
    return uit


def _wijzers(c, r, maat, minuten, schaduw=False):
    uur, minuut = hoeken(minuten)
    uit = []
    for rol, hoek, lengte, dikte in (("uur", uur, 0.50, 0.045), ("minuut", minuut, 0.80, 0.022)):
        x1, y1 = punt(c, c, -r * 0.08, hoek)  # een stukje voorbij het midden, zoals een echte wijzer
        x2, y2 = punt(c, c, r * lengte, hoek)
        uit.append({"soort": "lijn", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "kleur": KLEUR["juist" if schaduw else rol], "dikte": maat * dikte * (0.6 if schaduw else 1),
                    "rond": not schaduw, "streep": schaduw, "rol": rol})
    return uit


def naar_svg(lijst, maat=320, boven=(), onder=(), titel=""):
    """De vormen als SVG (voor de handleiding), zoals in het klokvenster: boven de klok de vraag, eronder de
    uitslag. boven en onder zijn tekstregels: [(tekst, kleur-sleutel)]."""
    rand, regel = 30, 26
    top = regel * len(boven) + (10 if boven else 0)
    breedte, hoogte = maat + 2 * rand, top + maat + regel * len(onder) + (10 if onder else 0)
    regels = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{breedte}" height="{hoogte}" '
              f'viewBox="0 0 {breedte} {hoogte}" font-family="DejaVu Sans, Verdana, sans-serif">',
              f"<title>{html.escape(titel)}</title>" if titel else "",
              f'<rect width="{breedte}" height="{hoogte}" fill="{KLEUR["achtergrond"]}"/>']
    for i, (tekst, kleur) in enumerate(boven):
        regels.append(_svg_tekst(breedte / 2, 22 + regel * i, tekst, kleur, vet=True))
    regels.append(f'<g transform="translate({rand} {top})">')
    for v in lijst:
        if v["soort"] == "cirkel":
            regels.append(f'<circle cx="{v["x"]:.1f}" cy="{v["y"]:.1f}" r="{v["r"]:.1f}" fill="{v["vul"]}" '
                          f'stroke="{v["lijn"]}" stroke-width="{v["dikte"]:.1f}"/>')
        elif v["soort"] == "lijn":
            extra = ' stroke-linecap="round"' if v.get("rond") else ""
            extra += ' stroke-dasharray="8 6"' if v.get("streep") else ""
            regels.append(f'<line x1="{v["x1"]:.1f}" y1="{v["y1"]:.1f}" x2="{v["x2"]:.1f}" y2="{v["y2"]:.1f}" '
                          f'stroke="{v["kleur"]}" stroke-width="{v["dikte"]:.1f}"{extra}/>')
        else:
            vet = ' font-weight="bold"' if v["vet"] else ""
            regels.append(f'<text x="{v["x"]:.1f}" y="{v["y"]:.1f}" font-size="{v["grootte"]:.1f}" '
                          f'fill="{v["kleur"]}" text-anchor="middle" dominant-baseline="central"{vet}>'
                          f'{html.escape(v["tekst"])}</text>')
    regels.append("</g>")
    for i, (tekst, kleur) in enumerate(onder):
        regels.append(_svg_tekst(breedte / 2, top + maat + 16 + regel * i, tekst, kleur))
    regels.append("</svg>")
    return "\n".join(r for r in regels if r)


def _svg_tekst(x, y, tekst, kleur, vet=False):
    dik = ' font-weight="bold"' if vet else ""
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="15" text-anchor="middle"{dik} '
            f'fill="{KLEUR.get(kleur, KLEUR["cijfer"])}">{html.escape(tekst)}</text>')
