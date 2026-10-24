"""Klikzones: elk scherm legt tijdens het tekenen vast waar je kunt klikken.

Een klik wordt zo dezelfde actie als de bijhorende toets. Muis en toetsenbord delen dus
dezelfde logica.
"""


class Klikzones:
    def __init__(self):
        self.zones = []

    def wis(self):
        self.zones = []

    def voeg(self, y, x, hoogte, breedte, actie):
        if hoogte > 0 and breedte > 0:
            self.zones.append((y, x, hoogte, breedte, actie))

    def zoek(self, y, x):
        """De actie op deze plek (de laatst getekende zone wint), of None."""
        for zy, zx, h, b, actie in reversed(self.zones):
            if zy <= y < zy + h and zx <= x < zx + b:
                return actie
        return None
