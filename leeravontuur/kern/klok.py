"""De tijd van het programma. Tests kunnen ze vastzetten met zet()."""

from datetime import datetime

_vast = None


def nu():
    """Nu, in de lokale tijdzone."""
    return _vast if _vast is not None else datetime.now().astimezone()


def zet(tijdstip):
    """Zet de klok vast (voor tests); None maakt ze weer gewoon."""
    global _vast
    _vast = tijdstip


def iso(tijdstip=None):
    return (tijdstip or nu()).isoformat(timespec="seconds")


def dag(tijdstip=None):
    """De lokale datum als 'JJJJ-MM-DD'."""
    return (tijdstip or nu()).date().isoformat()
