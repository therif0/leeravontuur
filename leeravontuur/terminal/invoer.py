"""Wat elk invoer-object kan (rooster, staartdeling, breukbalk, zinsdelen, vraagstuk …): een rechthoek krijgen en zeggen
hoe groot het is (de bouwstenen van de schermen 1.0, werk/schermen.md).

- `x0`: de linkerkant van wat het object tekent. Zonder `plaats` is dat de vaste kolom van vroeger, zodat de gewone
  schermen niet veranderen.
- `plaats(x, breed)`: het object staat in een vak (`in_vak`): links op kolom x, hoogstens breed kolommen. In een vak
  tekent het de stijl van de vakken (bv. de cursor in de rol `invulcursor`) en laat het de tekst weg die in de rand
  hoort (`randtekst`).
- `breedte()`: zoveel kolommen vanaf x0 heeft het nodig (gemeten op wat het tekent, tijdens de vraag en erna).
- `hoogte(nagekeken)`: zoveel rijen (elk object had dat al).
- `randtekst()`: tekst voor de onderrand van het vak (bv. "typrichting ←"), of "".
"""


class _Meetvlak:
    """Een scherm dat niets tekent, alleen onthoudt hoe ver naar rechts er getekend werd."""

    def __init__(self, s=None):
        self.s, self.rechts, self.onder = s, 0, 0
        self.zones = self

    def put(self, y, x, tekst, rol=""):
        if tekst.strip():
            self.rechts = max(self.rechts, x + len(tekst.rstrip()))
            self.onder = max(self.onder, y + 1)

    def tekstvak(self, y, x, tekst, breedte, rol, actie=None):
        self.rechts = max(self.rechts, x + breedte + 2)
        self.onder = max(self.onder, y + 1)

    def voeg(self, *_):
        pass

    def cursor(self, *_):
        pass

    def bewerk(self, buf, k, *a):
        return buf

    def maat(self):
        return (100, 1000)

    def __getattr__(self, naam):  # wat een object nog vraagt (bv. of pixels kunnen): zoals het echte scherm
        if self.s is None:
            raise AttributeError(naam)
        return getattr(self.s, naam)


class Plaats:
    in_vak = False
    breed = None

    def plaats(self, x, breed):
        self.x0, self.breed, self.in_vak = x, breed, True

    def randtekst(self):
        return ""

    def teken_voor_maat(self, s, uitslag):
        """Tekenen om te meten (een object met een andere manier van tekenen geeft dit zelf)."""
        self.teken(s, 0, uitslag, False)

    def breedte(self, s=None):
        """Zoveel kolommen vanaf x0, tijdens de vraag en na het nakijken. s = het echte scherm (voor wat een object
        aan het scherm vraagt, bv. of pixels kunnen); er wordt niets op getekend."""
        return max(0, self.meet(s).rechts - self.x0)

    def meet(self, s=None, staten=(None, False)):
        """Tekent op een meetvlak (tijdens de vraag en na het nakijken) en zet daarna alles terug zoals het was."""
        meet = _Meetvlak(s)
        bewaard = dict(self.__dict__)
        try:
            for uitslag in staten:
                self.teken_voor_maat(meet, uitslag)
        finally:
            self.__dict__.clear()
            self.__dict__.update(bewaard)
        return meet
