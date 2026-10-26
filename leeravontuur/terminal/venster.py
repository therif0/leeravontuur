"""Het klokvenster vanuit de terminal: start het tkinter-proces (`venster/klokvenster.py`) en praat ermee.

Lukt dat niet (geen tkinter, geen beeldscherm, het venster stopt), dan geeft `toon` False en tekent de terminal de
klok gewoon zelf. Het kind ziet nooit een fout. Toetsen en klikken in het klokvenster komen via `volgende` in
`Scherm.toets` terecht, alsof ze in de terminal gebeurden.
"""

import atexit
import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

from ..kern import foutlog

START_S = 6.0  # zo lang wachten we hoogstens op het venster (één keer per sessie)


class Klokvenster:
    OPDRACHT = ["-m", "leeravontuur.venster.klokvenster"]  # na sys.executable (een test kan iets anders starten)

    def __init__(self, plek=None, bij_plek=None):
        """plek = waar het kind het venster vorige keer zette (x, y, b, h), bij_plek(plek) = die plek bewaren."""
        self.plek, self.bij_plek = plek, bij_plek
        self.in_terminal = False  # het kind drukte F2: de klok in de terminal (tot het weer F2 drukt)
        self.proc = None
        self.kapot = None       # waarom het venster niet (meer) werkt, of None
        self.dicht = False      # het kind sloot het venster: tot de volgende klok tekent de terminal
        self.getekend = False   # in dit beeld een klok getoond? (anders verbergen we het venster)
        self.zichtbaar = False
        self.laatste = None
        self.uit = queue.Queue()
        self._klaar = threading.Event()

    # ---- het proces ----------------------------------------------------------------------------

    def _start(self):
        wortel = str(Path(__file__).resolve().parent.parent.parent)
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(p for p in (wortel, os.environ.get("PYTHONPATH")) if p),
                   LEERAVONTUUR_KLOKPLEK=json.dumps(self.plek))
        try:
            self.proc = subprocess.Popen(
                [sys.executable, *self.OPDRACHT], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1,
                env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except (OSError, ValueError) as e:
            return self._mislukt(f"kon het klokvenster niet starten ({e})")
        threading.Thread(target=self._lees, daemon=True).start()
        atexit.register(self.stop)
        if not self._klaar.wait(START_S):
            self.stop()
            return self._mislukt("het klokvenster startte niet op tijd")
        return self.kapot is None

    def _lees(self):
        uit = self.proc.stdout
        try:
            for regel in uit:
                try:
                    b = json.loads(regel)
                except ValueError:
                    continue
                if "klaar" in b:
                    self._klaar.set()
                elif "fout" in b:  # geen tkinter of geen beeldscherm: gewoon, geen fout voor het logboek
                    self._mislukt(str(b["fout"]), log=False)
                    self._klaar.set()
                else:
                    self.uit.put(b)
        except (OSError, ValueError):
            pass
        try:
            uit.close()
        except (OSError, ValueError):
            pass
        if self.kapot is None:
            self._mislukt("het klokvenster stopte")
            self.uit.put({"dicht": True})  # opnieuw tekenen: nu met de klok in de terminal
        self._klaar.set()

    def _mislukt(self, reden, log=True):
        if self.kapot is None:
            self.kapot = reden
            if log:
                foutlog.schrijf("klokvenster", extra=f"{reden} (de klok staat nu in de terminal)")
        return False

    def _stuur(self, **bericht):
        try:
            self.proc.stdin.write(json.dumps(bericht, ensure_ascii=False) + "\n")
            self.proc.stdin.flush()
            return True
        except (OSError, ValueError, AttributeError):
            return self._mislukt("het klokvenster luistert niet meer")

    def stop(self):
        p, self.proc = self.proc, None
        if p is None:
            return
        self._mislukt("gestopt", log=False)  # gewoon afgesloten: geen melding als het proces nu stopt
        try:
            if p.poll() is None:
                p.stdin.write(json.dumps({"doe": "stop"}) + "\n")
                p.stdin.flush()
        except (OSError, ValueError):
            pass
        for _ in range(2):  # lukt het sluiten niet (de pijp is al dicht), dan is de buffer nu leeg
            try:
                p.stdin.close()
                break
            except (OSError, ValueError):
                continue
        try:
            p.wait(1.5)
        except subprocess.TimeoutExpired:
            try:
                p.kill()
                p.wait(1.5)
            except (OSError, subprocess.TimeoutExpired):
                pass

    # ---- voor de schermen ----------------------------------------------------------------------

    def toon(self, minuten, tekst="", klikbaar=False, juist=None, uitslag=None, onder="", onder_rol=""):
        """Zet de klok in het venster. Geeft True als dat lukte (dan toont de terminal alleen een verwijzing)."""
        self.getekend = True
        if self.kapot or self.dicht or self.in_terminal:
            return False
        if self.proc is None and not self._start():
            return False
        stand = {"minuten": int(minuten) % 720, "tekst": tekst, "klikbaar": klikbaar,
                 "juist": None if juist is None else int(juist) % 720, "uitslag": uitslag, "onder": onder,
                 "onder_rol": onder_rol}
        if stand != self.laatste:
            naar_voren = not self.zichtbaar or self.laatste is None or self.laatste["tekst"] != tekst
            if not self._stuur(doe="toon", naar_voren=naar_voren, **stand):
                return False
            self.laatste, self.zichtbaar = stand, True
        return True

    def nieuw_beeld(self):
        self.getekend = False

    def beeld_klaar(self):
        """Na het tekenen van een scherm: geen klok meer in beeld? Dan het venster verbergen."""
        if not self.getekend:
            self.dicht = False
            if self.zichtbaar and self.proc is not None:
                self._stuur(doe="verberg")
            self.zichtbaar, self.laatste = False, None

    def toont(self):
        """Staat de klok van dit beeld in het venster? (Dan houdt de terminal zijn tekst links.)"""
        return self.getekend and self.zichtbaar and not (self.kapot or self.dicht or self.in_terminal)

    def wissel(self):
        """F2 (of een klik op de verwijzing): ziet het kind het venster niet (bv. een terminal op het volle
        scherm), dan komt de klok in de terminal; nog eens F2 = terug in het venster."""
        if self.in_terminal or self.dicht:
            self.in_terminal = self.dicht = False
        else:
            self.in_terminal = True
            if self.zichtbaar and self.proc is not None:
                self._stuur(doe="verberg")
            self.zichtbaar, self.laatste = False, None

    def volgende(self):
        """Het volgende bericht uit het venster, of None."""
        try:
            b = self.uit.get_nowait()
        except queue.Empty:
            return None
        if b.get("dicht"):
            self.dicht, self.zichtbaar, self.laatste = True, False, None
        elif "plek" in b:  # versleept: onthouden voor de volgende keer (hier, niet in de leesdraad: de databank)
            self.plek = b["plek"]
            if self.bij_plek:
                try:
                    self.bij_plek(self.plek)
                except Exception as e:  # een plek bewaren mag nooit iets stukmaken
                    foutlog.schrijf("klokvenster: plek bewaren", e)
        return b
