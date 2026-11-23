"""Een vak met een rand en een titel in de rand, zoals btop: de bouwsteen van de schermen 1.0 (werk/schermen.md).

Alleen weergave: wat er in het vak staat, tekent het scherm zelf binnen de rand (`indeling.Rechthoek.binnen`).
- `teken`: de rand, de titel (links boven), een tekst rechts boven, een toets in de onderrand (klikbaar, dezelfde actie
  als de toets). Het vak waar het kind typt (`focus`), krijgt de rand in de rol `rand_focus`.
- `lijst`: regels met rollen in een vak, vanaf regel `top`, afgeknipt op de breedte; met `scroll_rand` komen ▲ ▼ en
  "PgUp PgDn" (klikbaar) in de onderrand als niet alles past.
In ASCII-modus worden de randtekens + - | (`terminal/tekens.py`).
"""

import curses

SCROLL_TEKST = "PgUp PgDn"


def label(s, y, x, tekst, rol="bold", rand="rand"):
    """┤ tekst ├ in een rand; geeft de breedte."""
    s.put(y, x, "┤ ", rand)
    s.put(y, x + 2, tekst, rol)
    s.put(y, x + 2 + len(tekst), " ├", rand)
    return len(tekst) + 4


def teken(s, y, x, h, w, titel="", rechts="", onder="", actie=None, focus=False, rand=None):
    """De rand van (y, x) tot (y + h - 1, x + w - 1). titel = links in de bovenrand, rechts = rechts in de bovenrand
    (valt weg als het niet past), onder = een toets rechts in de onderrand, klikbaar met actie (dezelfde als de toets)."""
    if h < 2 or w < 4:
        return
    rand = rand or ("rand_focus" if focus else "rand")
    s.put(y, x, "╭" + "─" * (w - 2) + "╮", rand)
    for r in range(y + 1, y + h - 1):
        s.put(r, x, "│", rand)
        s.put(r, x + w - 1, "│", rand)
    s.put(y + h - 1, x, "╰" + "─" * (w - 2) + "╯", rand)
    bezet = x + 2 + (label(s, y, x + 2, titel[:w - 8], rand=rand) if titel else 0)
    if rechts and bezet + len(rechts) + 6 <= x + w - 2:
        label(s, y, x + w - 6 - len(rechts), rechts, "dim", rand)
    if onder:
        ox = x + w - 6 - len(onder)
        label(s, y + h - 1, ox, onder, "knop", rand)
        if actie is not None:
            s.zones.voeg(y + h - 1, ox, 1, len(onder) + 4, actie)


def lijst(s, y, x, h, w, regels, top=0):
    """Regels (tekst, rol) in een vlak van h rijen en w kolommen, vanaf regel top (begrensd zodat het vlak vol staat).
    Geeft (top, meer_boven, meer_onder)."""
    top = max(0, min(len(regels) - h, top))
    for i, (tekst, rol) in enumerate(regels[top:top + h]):
        s.put(y + i, x, tekst[:w], rol)
    return top, top > 0, top + h < len(regels)


def scroll_rand(s, y, x, h, w, boven, onder, rand="rand"):
    """▲ ▼ PgUp PgDn rechts in de onderrand van een vak (y, x, h, w); PgUp en PgDn zijn klikbaar (dezelfde actie als
    de toets). Alleen tekenen als er iets te scrollen is."""
    tekst = f"{'▲' if boven else ' '}{'▼' if onder else ' '} {SCROLL_TEKST}"
    ox = x + w - 6 - len(tekst)
    label(s, y + h - 1, ox, tekst, "knop", rand)
    s.zones.voeg(y + h - 1, ox + 5, 1, 4, curses.KEY_PPAGE)
    s.zones.voeg(y + h - 1, ox + 10, 1, 4, curses.KEY_NPAGE)


def scroll_stap(k, top, plaats):
    """De nieuwe top na een toets (PgUp, PgDn) of het scrollwiel (("scroll", ±1)), of None als het geen scrolltoets is."""
    if k == curses.KEY_PPAGE:
        return top - (plaats - 1)
    if k == curses.KEY_NPAGE:
        return top + (plaats - 1)
    if isinstance(k, tuple) and k[0] == "scroll":
        return top + 3 * k[1]
    return None
