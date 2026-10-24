"""Laadt alle vaardigheden, zodat het register (kern/vaardigheden.py) volledig is."""

from . import vaardigheden
from .wiskunde import eenheden  # noqa: F401  (registreert zich bij het importeren)


def naam(vaardigheid_id):
    v = vaardigheden.REGISTER.get(vaardigheid_id)
    return v.naam if v else vaardigheid_id


def denkfout(code):
    return vaardigheden.DENKFOUTEN.get(code, code)
