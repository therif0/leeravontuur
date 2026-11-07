"""Het slot op Stoppen: de ouder zet het per kind aan (Ouders › Kinderen › kind › Stoppen op slot).

Staat het slot op, dan start het programma meteen bij dat kind en kan het kind alleen stoppen met de ouderpin
(4 cijfers, `Opslag.ouder_pin`). Zonder ouderpin geldt geen enkel slot: zo zit niemand ooit vast.
"""

from . import wachtwoord

PIN_ITERATIES = 100_000  # 4 cijfers zijn toch snel te raden; snel controleren is hier belangrijker


def heeft_slot(opslag, kind_id):
    """True als Stoppen voor dit kind op slot staat (en er een ouderpin is om het te openen)."""
    if not opslag.ouder_pin():
        return False
    try:
        return opslag.instellingen_van(kind_id).stoppen_slot
    except Exception:  # bv. een kind dat net gewist werd
        return False


def vergrendeld_kind(opslag):
    """Het kind waarmee het programma meteen start, of None: het laatst gekozen kind met een slot, anders het
    eerste met een slot."""
    met_slot = [k for k in opslag.kinderen() if heeft_slot(opslag, k.id)]
    laatste = opslag.algemeen("laatste_kind")
    return next((k for k in met_slot if k.id == laatste), met_slot[0] if met_slot else None)


def pin_ok(opslag, pin):
    opgeslagen = opslag.ouder_pin()
    return bool(opgeslagen and pin and wachtwoord.controleer(pin, opgeslagen))


def zet_pin(opslag, pin):
    opslag.zet_ouder_pin(wachtwoord.maak(pin, PIN_ITERATIES))


def zet_slot(opslag, kind_id, aan):
    inst = opslag.instellingen_van(kind_id)
    inst.stoppen_slot = bool(aan)
    opslag.bewaar_instellingen(kind_id, inst)


def zet_alle_sloten_af(opslag):
    """Bij het weghalen van de ouderpin: geen slot zonder pin."""
    for k in opslag.kinderen():
        if opslag.instellingen_van(k.id).stoppen_slot:
            zet_slot(opslag, k.id, False)
