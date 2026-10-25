"""Een slotbestand, zodat het programma merkt dat het al openstaat (twee keer open = kans op verloren antwoorden).

Het slot is een tekstbestand met het procesnummer. Een slot van een programma dat niet meer draait (bv. na een
stroompanne) telt niet: dat wordt gewoon overgenomen.
"""

import atexit
import os
import sys

from . import klok
from .paden import data_map

BESTAND = "leeravontuur.lock"


def _draait(pid):
    """Draait het proces met dit nummer nog?"""
    if pid <= 0:
        return False
    if sys.platform == "win32":  # os.kill zou het proces op Windows beëindigen: vraag het aan Windows
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return False
            try:
                code = ctypes.c_ulong()
                return bool(k32.GetExitCodeProcess(h, ctypes.byref(code))) and code.value == 259  # STILL_ACTIVE
            finally:
                k32.CloseHandle(h)
        except Exception:
            return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def bezet(map_=None):
    """Tekst over het programma dat al openstaat (bv. 'sinds 14:02'), of None als het vrij is."""
    pad = (map_ or data_map()) / BESTAND
    try:
        pid, _, sinds = pad.read_text(encoding="utf-8").partition(" ")
        pid = int(pid)
    except (OSError, ValueError):
        return None
    if pid == os.getpid() or not _draait(pid):
        return None
    return f"sinds {sinds.strip()[11:16]}" if len(sinds.strip()) >= 16 else "al een tijdje"


def neem(map_=None):
    """Zet het slot (en ruim het op bij het afsluiten). Mag nooit crashen."""
    pad = (map_ or data_map()) / BESTAND
    try:
        pad.parent.mkdir(parents=True, exist_ok=True)
        pad.write_text(f"{os.getpid()} {klok.iso()}", encoding="utf-8")
    except OSError:
        return
    atexit.register(geef_vrij, map_)


def geef_vrij(map_=None):
    pad = (map_ or data_map()) / BESTAND
    try:
        pid = int(pad.read_text(encoding="utf-8").split(" ", 1)[0])
        if pid == os.getpid():
            pad.unlink()
    except (OSError, ValueError):
        pass
