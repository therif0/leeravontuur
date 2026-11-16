"""Wat een invoer-object met eigen stappen deelt (Zinsdelen, Werkwoordspelling): de tips per stap, de spiekbrief na
de laatste tip en de schakelaars die de Oefenaar volgens de `Hulp` zet. Zo maakt een nieuw object (Woordsoorten …)
geen derde kopie."""


class StappenHulp:
    eigen_tekst = True        # het object tekent zelf de vraag
    eigen_tip = True          # F1 gaat naar het object
    geen_tweede_kans = True   # het object kijkt zelf stap voor stap na (met een eigen tweede kans)
    vraag_is_zin = True       # in het rapport is de vraag de zin zelf (geen " ?" erachter)

    def begin_hulp(self):
        self.tips, self.tip_nr, self.tiptekst = 0, 0, ""
        self.tweede_kans = True     # de Oefenaar zet het volgens de Hulp (een examen later: uit)
        self.spiekbrief_aan = True  # idem: na de laatste tip opent F1 de spiekbrief (bij het kopje van de stap)
        self.aantal_tips = 2

    def geef_tip(self, tips, kop):
        """De volgende tip van deze stap; `kop` = waar de spiekbrief daarna opent."""
        self.aantal_tips = len(tips)
        self.v.data["spiek_kop"] = kop
        if self.tip_nr >= len(tips):
            self.tiptekst = "Meer tips zijn er niet. Probeer het, en lees daarna de uitleg."
            return
        self.tips += 1
        self.tiptekst = f"Tip {self.tip_nr + 1}: {tips[self.tip_nr]}"
        self.tip_nr += 1
        if self.tip_nr >= len(tips) and self.spiekbrief_aan:
            self.tiptekst += " Nog eens F1: je spiekbrief."

    @property
    def tips_op(self):
        """Alle tips van deze stap gegeven: de Oefenaar opent dan bij F1 de spiekbrief (de vaste werkwijze, #20)."""
        return self.tip_nr >= self.aantal_tips

    def spiekbrief_bekeken(self):
        """Na de spiekbrief begint het weer bij tip 1 (de vaste werkwijze)."""
        self.tips += 1
        self.tip_nr, self.tiptekst = 0, ""

    def hulp(self, o):
        return self.tiptekst

    def rijen(self):
        return []
