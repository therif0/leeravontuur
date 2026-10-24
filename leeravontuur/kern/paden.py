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
