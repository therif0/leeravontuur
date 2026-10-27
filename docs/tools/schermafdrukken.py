"""Maakt de schermafdrukken voor de handleiding (docs/handleiding/beelden/*.svg).

Het echte programma draait in tmux (80 × 24) met een voorbeeldkind en een vast zaad (LEERAVONTUUR_ZAAD), zodat
elke keer dezelfde vragen verschijnen. Het scherm (tmux capture-pane -e) wordt een SVG-beeld: alleen tekst en
rechthoeken, klein in git en GitHub toont het in Markdown.

Gebruik (vanuit de map van het programma, tmux nodig):
    python3 docs/tools/schermafdrukken.py              alle beelden
    python3 docs/tools/schermafdrukken.py eenheden     alleen de beelden waarvan de naam zo begint
"""

import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

WORTEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORTEL))
BEELDEN = WORTEL / "docs" / "handleiding" / "beelden"
BREED, HOOG = 80, 24
SESSIE = "handleiding"

# ---- ANSI → SVG ------------------------------------------------------------------------------------------

BASIS = ["#000000", "#cd3131", "#0dbc79", "#e5e510", "#2472c8", "#bc3fbc", "#11a8cd", "#e5e5e5",
         "#666666", "#f14c4c", "#23d18b", "#f5f543", "#3b8eea", "#d670d6", "#29b8db", "#ffffff"]
VOOR, ACHTER = "#d4d4d4", "#1e1e1e"  # de standaardkleuren van de terminal
CW, CH, LETTER = 9, 18, 15           # breedte en hoogte van een teken, lettergrootte
RAND = 8


def kleur256(n):
    if n < 16:
        return BASIS[n]
    if n < 232:
        n -= 16
        r, g, b = n // 36, (n // 6) % 6, n % 6
        f = lambda v: 0 if v == 0 else 55 + v * 40  # noqa: E731
        return f"#{f(r):02x}{f(g):02x}{f(b):02x}"
    v = 8 + (n - 232) * 10
    return f"#{v:02x}{v:02x}{v:02x}"


def lees_ansi(tekst, breed=BREED, hoog=HOOG):
    """Het scherm als raster van cellen (teken, voorgrond, achtergrond, vet, dim, onderlijnd)."""
    leeg = (" ", None, None, False, False, False)
    raster = [[leeg] * breed for _ in range(hoog)]
    st = dict(fg=None, bg=None, vet=False, dim=False, ul=False, om=False)
    for y, regel in enumerate(tekst.split("\n")[:hoog]):
        x = 0
        for deel in re.split(r"(\x1b\[[0-9;:]*m)", regel):
            m = re.fullmatch(r"\x1b\[([0-9;:]*)m", deel)
            if m:
                codes = [int(c) if c else 0 for c in re.split("[;:]", m.group(1))] or [0]
                i = 0
                while i < len(codes):
                    c = codes[i]
                    if c == 0:
                        st = dict(fg=None, bg=None, vet=False, dim=False, ul=False, om=False)
                    elif c == 1:
                        st["vet"] = True
                    elif c == 2:
                        st["dim"] = True
                    elif c == 4:
                        st["ul"] = True
                    elif c == 7:
                        st["om"] = True
                    elif c == 22:
                        st["vet"] = st["dim"] = False
                    elif c == 24:
                        st["ul"] = False
                    elif c == 27:
                        st["om"] = False
                    elif 30 <= c <= 37 or 90 <= c <= 97:
                        st["fg"] = BASIS[c - 30 if c < 90 else c - 82]
                    elif 40 <= c <= 47 or 100 <= c <= 107:
                        st["bg"] = BASIS[c - 40 if c < 100 else c - 92]
                    elif c == 39:
                        st["fg"] = None
                    elif c == 49:
                        st["bg"] = None
                    elif c in (38, 48) and i + 1 < len(codes):
                        doel = "fg" if c == 38 else "bg"
                        if codes[i + 1] == 5 and i + 2 < len(codes):
                            st[doel] = kleur256(codes[i + 2])
                            i += 2
                        elif codes[i + 1] == 2 and i + 4 < len(codes):
                            st[doel] = "#%02x%02x%02x" % tuple(codes[i + 2:i + 5])
                            i += 4
                    i += 1
                continue
            for ch in deel:
                if x < breed:
                    fg, bg = st["fg"], st["bg"]
                    if st["om"]:
                        fg, bg = bg or ACHTER, fg or VOOR
                    raster[y][x] = (ch, fg, bg, st["vet"], st["dim"], st["ul"])
                x += 1
    return raster


BLOKKEN = {"█": (0, 1), "▀": (0, 0.5), "▄": (0.5, 1)}  # teken: (van, tot) als deel van de hoogte


def naar_svg(raster, titel=""):
    w, h = len(raster[0]) * CW + 2 * RAND, len(raster) * CH + 2 * RAND
    uit = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'role="img" aria-label="{html.escape(titel)}">',
           f'<rect width="{w}" height="{h}" rx="6" fill="{ACHTER}"/>',
           f'<g font-family="DejaVu Sans Mono, Menlo, Consolas, monospace" font-size="{LETTER}">']
    for y, rij in enumerate(raster):
        top = RAND + y * CH
        x = 0
        while x < len(rij):  # achtergronden, samengevoegd per stuk met dezelfde kleur
            bg = rij[x][2]
            eind = x
            while eind < len(rij) and rij[eind][2] == bg:
                eind += 1
            if bg:
                uit.append(f'<rect x="{RAND + x * CW}" y="{top}" width="{(eind - x) * CW}" height="{CH}" fill="{bg}"/>')
            x = eind
        for x, (ch, fg, *_rest) in enumerate(rij):  # blokjes (de pixel-avatar) als rechthoeken
            if ch in BLOKKEN:
                van, tot = BLOKKEN[ch]
                uit.append(f'<rect x="{RAND + x * CW}" y="{top + van * CH:g}" width="{CW}" '
                           f'height="{(tot - van) * CH:g}" fill="{fg or VOOR}"/>')
        x = 0
        while x < len(rij):  # tekst, per stuk met dezelfde stijl
            stijl = rij[x][1:2] + rij[x][3:]
            eind = x
            while eind < len(rij) and rij[eind][1:2] + rij[eind][3:] == stijl and rij[eind][0] not in BLOKKEN:
                eind += 1
            if eind == x:
                x += 1
                continue
            stuk = "".join(c[0] for c in rij[x:eind])
            if stuk.strip():
                fg, vet, dim, ul = stijl
                attr = f' fill="{fg or VOOR}"'
                attr += ' font-weight="bold"' if vet else ""
                attr += ' opacity="0.6"' if dim else ""
                attr += ' text-decoration="underline"' if ul else ""
                uit.append(f'<text x="{RAND + x * CW}" y="{top + CH - 5}" textLength="{(eind - x) * CW}" '
                           f'lengthAdjust="spacingAndGlyphs" xml:space="preserve"{attr}>{html.escape(stuk)}</text>')
            x = eind
    uit.append("</g></svg>")
    return "\n".join(uit) + "\n"


# ---- het voorbeeldkind -------------------------------------------------------------------------------------

def maak_voorbeeld(map_):
    """Een databank met Imrane (5de leerjaar), een ouderwachtwoord ('ouder') en drie weken oefengeschiedenis."""
    import random
    from datetime import datetime, timedelta

    os.environ["LEERAVONTUUR_DATA"] = str(map_)
    from leeravontuur.kern import avatar, catalogus, feedback, herhaling, klok, sessie, wachtwoord  # noqa: F401
    from leeravontuur.kern.onderwerp import ONDERWERPEN
    from leeravontuur.kern.opslag import Opslag
    from leeravontuur.kern.sessie import Sessie

    rng = random.Random(5)

    class Stopwatch:  # elke vraag duurt 3 à 15 seconden (anders staat er 0 s in het rapport)
        t = 0.0

        @classmethod
        def monotonic(cls):
            cls.t += rng.uniform(1.5, 7.5)
            return cls.t
    echte_tijd, sessie.time = sessie.time, Stopwatch
    opslag = Opslag.open()
    opslag.zet_ouder_wachtwoord(wachtwoord.maak("ouder"))
    kind = opslag.nieuw_kind("Imrane", "5")
    vandaag = datetime.now().astimezone().replace(hour=16, minute=0, second=0, microsecond=0)
    onderwerpen = [o for o in ONDERWERPEN.values() if o.aangeboden("5")]
    for dagen in range(21, 0, -1):
        if rng.random() < 0.3:
            continue
        klok.zet(vandaag - timedelta(days=dagen))
        for o in rng.sample(onderwerpen, 2):
            ses = Sessie(opslag, kind.id, "reeks", o.id, "5")
            for _ in range(10):
                v = o.maak("5", rng=rng)
                juist = rng.random() < 0.8
                ses.vraag_getoond()
                gegeven = v.verwacht if juist else "0"
                ses.antwoord(v.sleutel, v.tekst + " ?", gegeven, juist, verwacht=v.verwacht)
                if not juist:
                    herhaling.fout(opslag, kind.id, o.id, o.onderwerp(v), o.herhaal_data(v))
            ses.sluit()
    klok.zet(None)
    sessie.time = echte_tijd
    opslag.punten_bij(kind.id, 250, "bonus van de ouders: goed rapport")
    # wat gekocht, een pakje onderweg, een bewaarde combinatie en een opmerking
    for laag, sleutel, prijs in [("vorm", "rond", 60), ("kleur", "groen", 30), ("hoed", "pet", 90),
                                 ("accessoire", "zakhorloge", 130)]:
        opslag.zet_bezit(kind.id, laag, sleutel, prijs, True)
        opslag.punten_bij(kind.id, -prijs, f"gekocht: {sleutel}")
    opslag.zet_bezit(kind.id, "ogen", "ster", 120, False, {"soort": "pakje", "nodig": 10}, False)
    opslag.punten_bij(kind.id, -120, "gekocht: Sterogen")
    kleren = {**avatar.STANDAARD, "vorm": "rond", "kleur": "groen", "hoed": "pet", "accessoire": "zakhorloge"}
    opslag.bewaar_avatar(kind.id, kleren)
    opslag.bewaar_outfit(kind.id, "Op uitstap", kleren)
    feedback.bewaar("Imrane", "De schatkaart is leuk! Mag er ook een kaart met eilanden komen?", "hoofdmenu")
    opslag.sluit()


# ---- tmux ------------------------------------------------------------------------------------------------

def tmux(*args, uitvoer=False):
    r = subprocess.run(["tmux", *args], capture_output=True, text=True)
    return r.stdout if uitvoer else None


def scherm(kleur=False):
    return tmux("capture-pane", "-p", *(["-e"] if kleur else []), "-t", SESSIE, uitvoer=True) or ""


def rustig(max_s=3.0):
    """Wacht tot het scherm niet meer verandert."""
    vorige, eind = None, time.time() + max_s
    while time.time() < eind:
        nu = scherm(kleur=True)
        if nu == vorige:
            return
        vorige = nu
        time.sleep(0.15)


class Draai:
    """Eén keer het programma starten en er toetsen naar sturen."""

    def __init__(self, voorbeeld, zaad, argumenten=(), kind=True):
        self.map = Path("/tmp/leeravontuur")
        shutil.rmtree(self.map, ignore_errors=True)
        shutil.copytree(voorbeeld, self.map)
        tmux("kill-session", "-t", SESSIE)
        omgeving = (f"LEERAVONTUUR_DATA={self.map} LEERAVONTUUR_ZAAD={zaad} LEERAVONTUUR_KLOKVENSTER=0 ESCDELAY=300 "
                    f"LEERAVONTUUR_DOCUMENTEN={self.map / 'Documenten'}")
        opdracht = f"cd {WORTEL} && {omgeving} {sys.executable} leeravontuur.py {' '.join(argumenten)}"
        tmux("new-session", "-d", "-s", SESSIE, "-x", str(BREED), "-y", str(HOOG), opdracht)
        self.wacht("Leeravontuur")
        if kind:  # startscherm → Imrane
            self.toets("Enter")
            self.wacht("Wie ben jij?")
            self.toets("1")
            self.wacht("Wat wil je doen?")

    def toets(self, *toetsen):
        for t in toetsen:
            if isinstance(t, tuple) and t[0] == "klik":  # (klik, rij, kolom), vanaf 0
                tmux("send-keys", "-t", SESSIE, "-l", f"\x1b[<0;{t[2] + 1};{t[1] + 1}M")
            elif isinstance(t, tuple) and t[0] == "tekst":
                tmux("send-keys", "-t", SESSIE, "-l", t[1])
            else:
                tmux("send-keys", "-t", SESSIE, t)
            time.sleep(0.2)
            rustig()

    def wacht(self, patroon, max_s=6.0):
        eind = time.time() + max_s
        while time.time() < eind:
            if re.search(patroon, scherm()):
                rustig()
                return True
            time.sleep(0.1)
        raise RuntimeError(f"'{patroon}' verscheen niet op het scherm:\n{scherm()}")

    def zoek(self, patroon, opnieuw, keer=40):
        """Herhaal de toetsen `opnieuw` tot het patroon op het scherm staat (een bepaald soort vraag)."""
        for _ in range(keer):
            if re.search(patroon, scherm()):
                return
            self.toets(*opnieuw)
        raise RuntimeError(f"'{patroon}' niet gevonden na {keer} pogingen:\n{scherm()}")

    def plek(self, woord):
        """(rij, kolom) van een woord op het scherm."""
        for y, regel in enumerate(scherm().split("\n")):
            x = regel.find(woord)
            if x >= 0:
                return y, x
        raise RuntimeError(f"'{woord}' staat niet op het scherm")

    def foto(self, naam, titel=""):
        rustig()
        BEELDEN.mkdir(parents=True, exist_ok=True)
        (BEELDEN / f"{naam}.svg").write_text(naar_svg(lees_ansi(scherm(kleur=True)), titel or naam), encoding="utf-8")
        print("  ", naam)

    def stop(self):
        tmux("kill-session", "-t", SESSIE)
        shutil.rmtree(self.map, ignore_errors=True)


def main(filters):
    from scenarios import SCENARIOS  # de lijst met beelden (docs/tools/scenarios.py)

    if not shutil.which("tmux"):
        print("tmux is nodig om de schermafdrukken te maken.")
        return 1
    voorbeeld = Path(tempfile.mkdtemp(prefix="leeravontuur-voorbeeld-"))
    maak_voorbeeld(voorbeeld)
    fouten = 0
    for naam, (f, opties) in SCENARIOS.items():
        if filters and not any(naam.startswith(x) for x in filters):
            continue
        d = Draai(voorbeeld, naam, opties.get("argumenten", ()), opties.get("kind", True))
        try:
            f(d)
        except RuntimeError as e:
            fouten += 1
            print(f"!! {naam}: {e}")
        finally:
            d.stop()
    shutil.rmtree(voorbeeld, ignore_errors=True)
    return 1 if fouten else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
