"""Waar het programma zijn gegevens bewaart, per besturingssysteem."""

import os
import sys
from pathlib import Path


def data_map():
    """De map voor instellingen en (later) de databank. LEERAVONTUUR_DATA gaat voor (handig voor tests)."""
    eigen = os.environ.get("LEERAVONTUUR_DATA")
    if eigen:
        return Path(eigen)
    if sys.platform == "win32":
        basis = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(basis) / "Leeravontuur"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Leeravontuur"
    basis = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(basis) / "leeravontuur"


def documenten_map():
    """Waar exports komen: de map Documenten van de gebruiker (+ submap Leeravontuur).

    LEERAVONTUUR_DOCUMENTEN gaat voor (handig voor tests). Op Linux volgen we ~/.config/user-dirs.dirs,
    zodat een Nederlandstalig systeem 'Documenten' krijgt.
    """
    eigen = os.environ.get("LEERAVONTUUR_DOCUMENTEN")
    if eigen:
        return Path(eigen)
    thuis = Path.home()
    kandidaten = []
    if sys.platform.startswith("linux"):
        try:
            for regel in (thuis / ".config" / "user-dirs.dirs").read_text(encoding="utf-8").splitlines():
                if regel.startswith("XDG_DOCUMENTS_DIR="):
                    waarde = regel.split("=", 1)[1].strip().strip('"').replace("$HOME", str(thuis))
                    kandidaten.append(Path(waarde))
        except OSError:
            pass
    kandidaten += [thuis / "Documents", thuis / "Documenten"]
    for k in kandidaten:
        if k.is_dir():
            return k / "Leeravontuur"
    return thuis / "Leeravontuur"
