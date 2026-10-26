"""Het klokvenster: een echte wijzerklok in een eigen venster (tkinter), naast de terminal.

Draait als eigen proces (`python -m leeravontuur.venster.klokvenster`), zodat tkinter en curses elkaar niet storen
en een probleem met het venster het programma nooit doet vastlopen. Praten gaat met JSON-regels:

  binnen (stdin):  {"doe": "toon", "minuten": 205, "tekst": "Hoe laat is het?", "klikbaar": false,
                    "juist": null, "uitslag": null, "onder": "", "naar_voren": true}
                   {"doe": "verberg"}   {"doe": "stop"}
  buiten (stdout): {"klaar": true} of {"fout": "…"} bij het starten,
                   {"toets": "Enter"} (toetsen in dit venster gaan naar het programma),
                   {"klik": [dx, dy]} (waar de lange wijzer moet staan, tegenover het midden),
                   {"plek": [x, y, b, h]} (het kind of de ouder versleepte het venster: volgende keer weer daar),
                   {"dicht": true} (het kind sloot het venster: het programma toont de klok dan zelf)

Het venster moet de oefening nooit in de weg zitten: het blijft bovenop zolang er een klok in beeld is (en
verdwijnt daarna), neemt de toetsen niet over (Windows), en komt naast de terminal of rechtsboven, nooit breder
dan een kwart van het scherm. De terminal houdt dan zijn tekst links (terminal/oefenaar.py, LINKS).
Een bewaarde plek (LEERAVONTUUR_KLOKPLEK, JSON) gaat voor.
"""

import json
import math
import os
import queue
import re
import sys
import threading

from leeravontuur.venster.klokbeeld import KLEUR, vormen

TITEL = "Leeravontuur · de klok"
TOETSEN = {"Return": "Enter", "KP_Enter": "Enter", "Escape": "Escape", "Left": "Left", "Right": "Right",
           "Up": "Up", "Down": "Down", "BackSpace": "BackSpace", "Tab": "Tab", "Delete": "BackSpace"}
MARGE = 16
BREED, MIN_BREED = 320, 220


def zeg(**bericht):
    try:
        sys.stdout.write(json.dumps(bericht, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    except (OSError, ValueError):  # het programma is weg
        raise SystemExit(0)


def lees(binnen):
    """Leest de opdrachten (in een eigen draad, want tkinter kan niet op een pijp wachten op Windows)."""
    for regel in sys.stdin:
        try:
            binnen.put(json.loads(regel))
        except ValueError:
            continue
    binnen.put({"doe": "stop"})


def maat_voor(werk):
    """(breedte, hoogte) van het venster: hoogstens een kwart van het scherm breed."""
    x0, y0, x1, y1 = werk
    b = int(max(MIN_BREED, min(BREED, (x1 - x0) * 0.25 - MARGE)))
    return b, int(min(b * 1.3, (y1 - y0) - 2 * MARGE))


def kies_plek(werk, terminal=None, bewaard=None):
    """Waar het venster komt: (x, y, breedte, hoogte). werk = het bruikbare deel van het scherm (x0, y0, x1, y1),
    terminal = waar de terminal staat (als we dat weten), bewaard = een plek die het kind zelf koos."""
    x0, y0, x1, y1 = werk
    if bewaard:
        try:
            bx, by, bb, bh = (int(v) for v in bewaard)
        except (TypeError, ValueError):
            bx = None
        # helemaal op het scherm (het scherm kan kleiner zijn dan vorige keer)? dan daar
        if bx is not None and bb >= MIN_BREED // 2 and x0 <= bx and bx + bb <= x1 and y0 <= by and by + bh <= y1:
            return bx, by, bb, bh
    b, h = maat_voor(werk)
    if terminal:
        tx0, ty0, tx1, ty1 = terminal
        y = max(y0 + MARGE, min(ty0, y1 - h - MARGE))
        if x1 - tx1 >= b + MARGE:  # rechts naast de terminal is plaats
            return tx1 + MARGE // 2, y, b, h
        if tx0 - x0 >= b + MARGE:  # of links
            return tx0 - b - MARGE // 2, y, b, h
    # de terminal vult (bijna) het scherm: rechtsboven, waar de oefening niets toont
    return x1 - b - MARGE, y0 + MARGE, b, h


def monitor_van(scherm, punt):
    """Met meer monitors ziet tkinter één breed scherm. Welk stuk is de monitor waar `punt` (bv. de muis) staat?
    Is het scherm veel breder dan hoog, dan schatten we het aantal monitors (naast elkaar, 16:9 of 16:10).
    Geeft (x0, y0, x1, y1) van die monitor, of het hele scherm."""
    x0, y0, x1, y1 = scherm
    breed, hoog = x1 - x0, y1 - y0
    if hoog <= 0 or breed / hoog <= 2.0:  # één scherm (ook 21:9 ultrabreed)
        return scherm
    aantal = max(1, round(breed / (hoog * 16 / 9)))
    stuk = breed / aantal
    px = min(max(punt[0], x0), x1 - 1) if punt else x0
    i = int((px - x0) // stuk)
    return int(x0 + i * stuk), y0, int(x0 + (i + 1) * stuk), y1


def lees_geometrie(tekst):
    """'320x416+1030+16' (zoals tkinter het geeft en terug wil) → (x, y, breedte, hoogte), of None."""
    m = re.fullmatch(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", str(tekst).strip())
    if not m:
        return None
    b, h, x, y = (int(v) for v in m.groups())
    return x, y, b, h


class Windows:
    """Wat tkinter op Windows niet zelf kan: weten waar de terminal staat, en tonen zonder de toetsen af te nemen."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.c, self.w = ctypes, wintypes
        self.user32 = ctypes.windll.user32
        self.terminal = self.user32.GetForegroundWindow()  # bij het starten: het terminalvenster van het kind

    def _rect(self, hwnd):
        r = self.w.RECT()
        if not hwnd or not self.user32.GetWindowRect(hwnd, self.c.byref(r)):
            return None
        return r.left, r.top, r.right, r.bottom

    def werk(self):
        """Het werkgebied (zonder taakbalk) van de monitor waar de terminal staat."""
        c, w = self.c, self.w

        class MONITORINFO(c.Structure):
            _fields_ = [("cbSize", w.DWORD), ("rcMonitor", w.RECT), ("rcWork", w.RECT), ("dwFlags", w.DWORD)]

        if self.terminal:
            monitor = self.user32.MonitorFromWindow(self.terminal, 2)  # MONITOR_DEFAULTTONEAREST
            info = MONITORINFO()
            info.cbSize = c.sizeof(MONITORINFO)
            if monitor and self.user32.GetMonitorInfoW(monitor, c.byref(info)):
                r = info.rcWork
                return r.left, r.top, r.right, r.bottom
        r = w.RECT()
        if self.user32.SystemParametersInfoW(0x0030, 0, c.byref(r), 0):  # SPI_GETWORKAREA (het hoofdscherm)
            return r.left, r.top, r.right, r.bottom
        return None

    def terminal_plek(self):
        return self._rect(self.terminal)

    def geen_focus(self, root):
        """Het venster neemt nooit de toetsen over (WS_EX_NOACTIVATE); klikken op de wijzers werkt wel."""
        hwnd = int(root.wm_frame(), 16)
        stijl = self.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
        self.user32.SetWindowLongW(hwnd, -20, stijl | 0x08000000)  # WS_EX_NOACTIVATE

    def terug_naar_terminal(self):
        if self.terminal:
            self.user32.SetForegroundWindow(self.terminal)


class Venster:
    def __init__(self, tk):
        self.tk = tk
        try:
            self.win = Windows() if sys.platform == "win32" else None
        except Exception:  # nooit stoppen om een extraatje
            self.win = None
        self.root = tk.Tk()
        self.root.title(TITEL)
        self.root.configure(bg=KLEUR["achtergrond"])
        self.root.minsize(MIN_BREED, int(MIN_BREED * 1.2))
        try:
            self.bewaard = json.loads(os.environ.get("LEERAVONTUUR_KLOKPLEK") or "null")
        except ValueError:
            self.bewaard = None
        self.geplaatst = False
        self.eigen = None  # de plek die het programma zelf zette (die hoeven we niet te bewaren)
        self.stand = {"minuten": 0, "tekst": "", "klikbaar": False}
        self.laatste_minuut = None
        self.vraag = tk.Label(self.root, text="", font=("Helvetica", 14, "bold"), bg=KLEUR["achtergrond"],
                              fg=KLEUR["cijfer"], wraplength=BREED - 20, justify="center")
        self.vraag.pack(side="top", fill="x", padx=8, pady=(8, 0))
        self.doek = tk.Canvas(self.root, width=BREED, height=BREED, bg=KLEUR["achtergrond"], highlightthickness=0)
        self.doek.pack(side="top", fill="both", expand=True)
        self.onder = tk.Label(self.root, text="", font=("Helvetica", 12), bg=KLEUR["achtergrond"],
                              fg=KLEUR["cijfer"], wraplength=BREED - 20, justify="center")
        self.onder.pack(side="top", fill="x", padx=8, pady=(0, 8))
        self.root.protocol("WM_DELETE_WINDOW", self.dicht)
        self.root.bind("<Key>", self.toets)
        self.root.bind("<Configure>", self.verplaatst)
        self.doek.bind("<Button-1>", self.klik)
        self.doek.bind("<B1-Motion>", self.klik)
        self.doek.bind("<Configure>", lambda e: self.teken())
        if sys.platform.startswith("linux"):
            try:  # een hulpvenster dat de toetsen niet afneemt: ze blijven bij de terminal (klikken werkt wel)
                self.root.wm_attributes("-type", "utility")
                self.root.wm_focusmodel("active")
            except tk.TclError:
                pass
        self.root.withdraw()
        if self.win:
            try:
                self.root.update_idletasks()
                self.win.geen_focus(self.root)
            except Exception:
                pass

    # ---- waar het venster staat --------------------------------------------------------------------

    def werkgebied(self):
        if self.win:
            try:
                w = self.win.werk()
                if w:
                    return w
            except Exception:
                pass
        # elders: de monitor waar de muis staat (daar werkt het kind), met bovenaan plaats voor een menubalk
        scherm = (0, 30 if sys.platform == "darwin" else 0, self.root.winfo_screenwidth(),
                  self.root.winfo_screenheight())
        try:
            muis = self.root.winfo_pointerxy()
        except self.tk.TclError:
            muis = None
        return monitor_van(scherm, muis)

    def plaats(self):
        terminal = None
        if self.win:
            try:
                terminal = self.win.terminal_plek()
            except Exception:
                terminal = None
        x, y, b, h = kies_plek(self.werkgebied(), terminal, self.bewaard)
        self.eigen = (x, y, b, h)
        self.root.geometry(f"{b}x{h}+{x}+{y}")
        self.vraag.configure(wraplength=b - 20)
        self.onder.configure(wraplength=b - 20)

    def verplaatst(self, e):
        """Het kind of de ouder sleepte het venster ergens anders heen: dat onthouden (even wachten tot het stil staat)."""
        if e.widget is not self.root or self.root.state() != "normal":
            return
        if getattr(self, "_wacht", None):
            self.root.after_cancel(self._wacht)
        self._wacht = self.root.after(700, self.bewaar_plek)

    def bewaar_plek(self):
        self._wacht = None
        try:
            plek = lees_geometrie(self.root.wm_geometry())
        except self.tk.TclError:
            return
        if plek is None:
            return
        if self.eigen and all(abs(a - b) <= 40 for a, b in zip(plek, self.eigen)):
            return  # nog (ongeveer) waar het programma het zette: de randen van het venster tellen niet
        self.eigen = self.bewaard = plek
        self.vraag.configure(wraplength=plek[2] - 20)
        self.onder.configure(wraplength=plek[2] - 20)
        zeg(plek=list(plek))

    # ---- tekenen -------------------------------------------------------------------------------

    def maat(self):
        return max(120, min(self.doek.winfo_width(), self.doek.winfo_height()))

    def teken(self):
        d, st = self.doek, self.stand
        d.delete("all")
        maat = self.maat()
        dx = (d.winfo_width() - maat) / 2
        dy = (d.winfo_height() - maat) / 2
        for v in vormen(st["minuten"], maat, st.get("juist"), st.get("uitslag")):
            if v["soort"] == "cirkel":
                d.create_oval(dx + v["x"] - v["r"], dy + v["y"] - v["r"], dx + v["x"] + v["r"],
                              dy + v["y"] + v["r"], fill=v["vul"], outline=v["lijn"], width=v["dikte"])
            elif v["soort"] == "lijn":
                d.create_line(dx + v["x1"], dy + v["y1"], dx + v["x2"], dy + v["y2"], fill=v["kleur"],
                              width=v["dikte"], capstyle="round" if v.get("rond") else "butt",
                              dash=(8, 6) if v.get("streep") else ())
            else:
                d.create_text(dx + v["x"], dy + v["y"], text=v["tekst"], fill=v["kleur"],
                              font=("Helvetica", -max(8, round(v["grootte"])), "bold" if v["vet"] else "normal"))
        self.vraag.configure(text=st.get("tekst", ""))
        rol = st.get("onder_rol") or ""
        self.onder.configure(text=st.get("onder", ""), fg=KLEUR.get(rol, KLEUR["cijfer"]))

    # ---- opdrachten ----------------------------------------------------------------------------

    def doe(self, b):
        soort = b.get("doe")
        if soort == "stop":
            self.root.destroy()
            return False
        if soort == "verberg":
            self.root.withdraw()
        elif soort == "toon":
            self.stand = b
            self.laatste_minuut = None
            if self.root.state() != "normal":
                if not self.geplaatst or not self.bewaard:  # telkens naast de terminal (die kan verschoven zijn)
                    self.plaats()
                    self.geplaatst = True
                self.root.deiconify()
                self.bovenop()
            elif b.get("naar_voren"):
                self.bovenop()
            self.teken()
        return True

    def bovenop(self):
        """Bovenop blijven zolang er een klok in beeld is: zo verdwijnt het niet achter de terminal."""
        try:
            self.root.attributes("-topmost", True)
        except self.tk.TclError:
            pass
        self.root.lift()
        if self.win:  # de toetsen blijven bij de terminal
            try:
                self.root.after(50, self.win.terug_naar_terminal)
            except Exception:
                pass

    # ---- het kind --------------------------------------------------------------------------------

    def toets(self, e):
        naam = TOETSEN.get(e.keysym)
        if naam:
            zeg(toets=naam)
        elif e.char and len(e.char) == 1 and e.char.isprintable():
            zeg(toets=e.char)

    def klik(self, e):
        if not self.stand.get("klikbaar"):
            return
        maat = self.maat()
        cx = (self.doek.winfo_width() - maat) / 2 + maat / 2
        cy = (self.doek.winfo_height() - maat) / 2 + maat / 2
        dx, dy = e.x - cx, e.y - cy
        if math.hypot(dx, dy) < maat * 0.04:
            return
        minuut = round(math.degrees(math.atan2(dx, -dy)) % 360 / 6) % 60
        if minuut != self.laatste_minuut:  # bij slepen: alleen als de wijzer echt verspringt
            self.laatste_minuut = minuut
            zeg(klik=[round(dx, 1), round(dy, 1)])

    def dicht(self):
        self.root.withdraw()
        zeg(dicht=True)


def main():
    try:
        import tkinter as tk
    except ImportError as e:  # bv. Linux zonder het pakket python3-tk
        zeg(fout=f"geen tkinter ({e})")
        return 1
    try:
        venster = Venster(tk)
    except Exception as e:  # bv. geen beeldscherm (ssh, CI)
        zeg(fout=f"geen venster mogelijk ({e})")
        return 1
    binnen = queue.Queue()
    threading.Thread(target=lees, args=(binnen,), daemon=True).start()

    def pomp():
        try:
            while True:
                if not venster.doe(binnen.get_nowait()):
                    return
        except queue.Empty:
            pass
        venster.root.after(30, pomp)

    zeg(klaar=True)
    venster.root.after(30, pomp)
    venster.root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
