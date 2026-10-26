"""Het klokvenster: een echte wijzerklok in een eigen venster (tkinter), naast de terminal.

Draait als eigen proces (`python -m leeravontuur.venster.klokvenster`), zodat tkinter en curses elkaar niet storen
en een probleem met het venster het programma nooit doet vastlopen. Praten gaat met JSON-regels:

  binnen (stdin):  {"doe": "toon", "minuten": 205, "tekst": "Hoe laat is het?", "klikbaar": false,
                    "juist": null, "uitslag": null, "onder": "", "naar_voren": true}
                   {"doe": "verberg"}   {"doe": "stop"}
  buiten (stdout): {"klaar": true} of {"fout": "…"} bij het starten,
                   {"toets": "Enter"} (toetsen in dit venster gaan naar het programma),
                   {"klik": [dx, dy]} (waar de lange wijzer moet staan, tegenover het midden),
                   {"dicht": true} (het kind sloot het venster: het programma toont de klok dan zelf)
"""

import json
import math
import queue
import sys
import threading

from leeravontuur.venster.klokbeeld import KLEUR, vormen

TITEL = "Leeravontuur · de klok"
TOETSEN = {"Return": "Enter", "KP_Enter": "Enter", "Escape": "Escape", "Left": "Left", "Right": "Right",
           "Up": "Up", "Down": "Down", "BackSpace": "BackSpace", "Tab": "Tab", "Delete": "BackSpace"}


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


class Venster:
    def __init__(self, tk):
        self.tk = tk
        self.root = tk.Tk()
        self.root.title(TITEL)
        self.root.configure(bg=KLEUR["achtergrond"])
        self.root.minsize(260, 320)
        self.stand = {"minuten": 0, "tekst": "", "klikbaar": False}
        self.laatste_minuut = None
        self.vraag = tk.Label(self.root, text="", font=("Helvetica", 15, "bold"), bg=KLEUR["achtergrond"],
                              fg=KLEUR["cijfer"], wraplength=340, justify="center")
        self.vraag.pack(side="top", fill="x", padx=10, pady=(10, 0))
        self.doek = tk.Canvas(self.root, width=360, height=360, bg=KLEUR["achtergrond"], highlightthickness=0)
        self.doek.pack(side="top", fill="both", expand=True)
        self.onder = tk.Label(self.root, text="", font=("Helvetica", 13), bg=KLEUR["achtergrond"],
                              fg=KLEUR["cijfer"], wraplength=340, justify="center")
        self.onder.pack(side="top", fill="x", padx=10, pady=(0, 10))
        self.root.protocol("WM_DELETE_WINDOW", self.dicht)
        self.root.bind("<Key>", self.toets)
        self.doek.bind("<Button-1>", self.klik)
        self.doek.bind("<B1-Motion>", self.klik)
        self.doek.bind("<Configure>", lambda e: self.teken())
        b, h = 380, 460
        x = max(0, self.root.winfo_screenwidth() - b - 40)
        self.root.geometry(f"{b}x{h}+{x}+60")  # rechtsboven, weg van het midden van de terminal
        self.root.withdraw()

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
            breed = max(200, self.root.winfo_width() - 40)
            self.vraag.configure(wraplength=breed)
            self.onder.configure(wraplength=breed)
            if self.root.state() != "normal" or b.get("naar_voren"):
                self.root.deiconify()
                self.root.lift()
                try:  # even bovenop, zodat het venster niet achter de terminal verdwijnt
                    self.root.attributes("-topmost", True)
                    self.root.after(400, lambda: self.root.attributes("-topmost", False))
                except self.tk.TclError:
                    pass
            self.teken()
        return True

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
