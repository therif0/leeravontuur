"""Het kladblad: overal hetzelfde (in een vraagstuk en in elke rekenoefening van de Oefenaar).

Het kind typt rekenregels zoals op papier (`91 : 7 = 70 : 7 + 21 : 7 = 10 + 3 = 13`, `3 x 2,15 = 6,45`); Enter kijkt
een regel meteen na (✔ klopt, ✘ rekenfout, · niets na te kijken) met een melding die het antwoord niet verklapt.
Backspace op een lege regel haalt de vorige terug; een klik op een regel ook. Het nakijken zit in kern/klad.py.
"""

from ..kern.klad import lees_regel
from .scherm import BACKSPACE, ENTER

KLAD_TEKENS = set("0123456789,.+-−*xX×:/()=%€ ") | set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ²³")
LEEG = "typ hier je rekenregels: 3 x 4 = 12"
LEEG_ENTER = "leeg"  # Enter op een lege regel: het scherm gaat verder (bv. naar het antwoord)


class Kladblad:
    def __init__(self):
        self.regels = []  # (getypte tekst, KladRegel)
        self.buf = ""
        self.melding, self.melding_rol = "", ""

    @property
    def gelezen(self):
        return [r for _, r in self.regels]

    @property
    def teksten(self):
        return [t for t, _ in self.regels]

    def teken(self, s, y, x, breed, hoogte, actief, leeg_actie=None):
        """Tekent het klad: de laatste regels, en (actief) de regel waarin het kind typt. Geeft de cursorplek of None.
        hoogte = aantal rijen (met de typregel); elke regel is klikbaar (("klad", nr)), net als de lege regel
        (leeg_actie)."""
        zicht = self.regels[-(hoogte - 1):] if hoogte > 1 and len(self.regels) >= hoogte else self.regels
        eerste_nr = len(self.regels) - len(zicht)
        for i, (tekst, regel) in enumerate(zicht):
            s.put(y + i, x, (regel.netjes or tekst)[:breed - 4], "")
            teken, rol = {True: ("✔", "goed"), False: ("✘", "fout")}.get(regel.juist, ("·", "dim"))
            s.put(y + i, x + breed - 2, teken, rol)
            s.zones.voeg(y + i, x, 1, breed, ("klad", eerste_nr + i))
        yy = y + len(zicht)
        if actief:
            s.put(yy, x, self.buf + " " * (breed - 4 - len(self.buf)), "veld")
            return yy, x + len(self.buf)
        if not self.regels:
            s.put(yy, x, LEEG[:breed - 2], "dim")
            if leeg_actie is not None:
                s.zones.voeg(yy, x, 1, breed - 4, leeg_actie)
        return None

    def toets(self, k, ch, breed=54):
        """Een toets in het klad. Geeft LEEG_ENTER bij Enter op een lege regel, anders None."""
        if k in BACKSPACE:
            if self.buf:
                self.buf = self.buf[:-1]
            elif self.regels:
                self.buf = self.regels.pop()[0]
            return None
        if k in ENTER:
            if not self.buf.strip():
                return LEEG_ENTER
            regel = lees_regel(self.buf)
            self.regels.append((self.buf, regel))
            self.buf = ""
            if regel.juist:
                self.melding, self.melding_rol = "✔ Deze regel klopt." + (f" {regel.melding}" if regel.melding
                                                                          else ""), "goed"
            elif regel.juist is False:
                self.melding, self.melding_rol = f"✘ {regel.melding}", "fout"
            else:
                self.melding, self.melding_rol = (f"! {regel.melding or 'Schrijf een bewerking met = en de uitkomst.'}",
                                                  "accent")
            return None
        if ch and ch in KLAD_TEKENS and len(self.buf) < breed - 6:
            self.buf += ch
        return None

    def haal_terug(self, nr):
        """Een klik op een regel: terug in de typregel (als die leeg is)."""
        if not self.buf and 0 <= nr < len(self.regels):
            self.buf = self.regels.pop(nr)[0]
