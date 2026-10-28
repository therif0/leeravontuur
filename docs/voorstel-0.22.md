# Voorstel 0.22: mockups (groep C)

Dit zijn **alleen tekeningen**: er is nog niets gebouwd. Elk beeld is 80 × 24, zoals op het scherm (de avatar
rechtsboven is weggelaten waar hij in de weg zou zitten). Per wens: wat er nu is, het beeld, mijn aanbeveling en
wat de vader kiest (**bouwen**, **anders** (zeg hoe) of **niet**). Daarna bouw ik in fasen, één wens per fase en
per PR.

Kies gerust in een reactie op de PR, bv. "1 bouwen, 2 anders: …, 3 bouwen, 4 later".

---

## 1. Het logboek voor de ouder (#24)

**Nu:** Ouders › Punten › kind toont alleen de punten en een reden. Wat de vraag was en wat het kind antwoordde,
staat er niet bij:
```text
 Leeravontuur › Ouders › Punten › Imrane

    Imrane heeft 30 punten.

    LAATSTE WIJZIGINGEN
      25/10 16:49    +10  juist antwoord
      25/10 16:26    +20  juist antwoord
```

**Voorstel A: in Punten de vraag erbij** (wat bij elk punt hoort):
```text
 Leeravontuur › Ouders › Punten › Imrane

    Imrane heeft 30 punten.

    LAATSTE WIJZIGINGEN
      25/10 16:49    +10  juist antwoord · Omtrek: rechthoek op het rooster
      25/10 16:26    +20  juist antwoord · 9,7 ha = 97 000 m²
      24/10 18:02    +10  juist antwoord · 7 × 8 = 56
      24/10 17:58     +5  3 juist op rij
      24/10 17:40    -40  winkel: rode pet













 [B] bonus geven  [Esc] terug
```

**Voorstel B: een nieuw scherm "Antwoorden"** in het ouderdeel (alle antwoorden, ook de foute, die geen punten
geven). Met ↑↓ kies je een antwoord; **Enter** toont de details, **H** steekt de vraag in de herhaalbak (het kind
krijgt ze morgen terug, met nieuwe getallen):
```text
 Leeravontuur › Ouders › Antwoorden › Imrane

    Laatste antwoorden van Imrane (nieuwste eerst)             [D] per dag

    25/10 18:50  ✘  Meetkunde · Oppervlakte   jij: 1          juist: 12 cm²
    25/10 18:40  ✘  Meetkunde · Omtrek        jij: 1          juist: 16 cm
    25/10 16:59  ✘  Meetkunde · Hoeken        jij: stomp      juist: scherp
  ▸ 24/10 18:02  ✘  Tafels · 7 × 8            jij: 54         juist: 56
    24/10 17:58  ✔  Tafels · 6 × 9            jij: 54
    24/10 17:41  ✔  Breuken · 1/2 + 1/4       jij: 3/4
    24/10 17:39  ✘  Maten · 9,7 ha = ? m²     jij: 9700       juist: 97 000
    …











 [↑↓] kiezen  [Enter] details  [H] in de herhaalbak  [Esc] terug
```
Details van één antwoord:
```text
 Leeravontuur › Ouders › Antwoorden › Imrane › 24/10 18:02

    Tafels · Normaal (5de leerjaar) · reeks van 10

    Vraag:    7 × 8 = ?
    Jij:      54          ✘   (juist: 56)
    Denkfout: één tafel te weinig (7 × 8 = 7 × 7 + 7)
    Tijd:     9 seconden, met 1 tip

    Klad:
      7 × 7 = 49     ✔
      49 + 5 = 54    ✘

    In de herhaalbak: nee                       [H] steek ze in de herhaalbak









 [H] in de herhaalbak  [Esc] terug
```
Na **H**: "✔ Deze vraag komt morgen terug bij Herhalen (met nieuwe getallen)."

Goed om te weten:
- Bij een vraag met een tekening (een figuur, een klok, een hoek) bewaart het programma de tekening niet: de ouder
  ziet de vraag in woorden en het antwoord.
- Klein foutje gezien: zo'n vraag staat bewaard als "Hoe groot is de omtrek van de figuur? ?" (twee vraagtekens).
  Dat zet ik recht in dezelfde fase.

**Aanbeveling:** A én B. A is klein. B is wat de ouder echt nodig heeft: alle antwoorden, ook de foute, en met H
gericht laten herhalen. Het ouderdeel krijgt dan 7 keuzes in plaats van 6 (Rapporten, **Antwoorden**, Kinderen,
Punten, Wachtwoord wijzigen, Opmerkingen, Sluiten; het maximum is 10).

- [ ] A bouwen  - [ ] B bouwen  - [ ] anders: …  - [ ] niet
- "Per dag" (D) erbij, of gewoon de lijst (nieuwste eerst)?

---

## 2. Cijferend vermenigvuldigen per niveau (#19)

**Nu:** elk niveau werkt hetzelfde: het kind vult rij 1, rij 2 en de uitkomst vrij in, en pas op het einde wordt
alles nagekeken. Makkelijk is voor een kind van het 5de de leerlijn van het 4de (3 cijfers × 2 cijfers).

**Voorstel per niveau:**
- **Makkelijk:** alleen × **één** cijfer (dus geen tientallen-rij). Gaat het kind van de onthouden-rij naar de
  uitkomst, dan wordt de onthouden-rij nagekeken. Een fout cijfer daar wordt rood met **!**: een redeneringsfout,
  nog geen fout antwoord.
- **Normaal:** 2 rijen. Rij 2 begint vanzelf met een **0** onder de E en de cursor staat bij de T (het
  "opschuiven"). Bovenaan staat de zin "Eerst × de eenheden, dan × de tientallen, dan tel je de twee rijen op."
  De rijen worden pas nagekeken als het kind op **?** drukt: zit er een fout in een rij, dan zegt de hulp waar.
- **Moeilijk en Heel moeilijk:** zoals nu, zelf nadenken. Geen 0 vanzelf, geen controle onderweg.

Makkelijk, de onthouden-rij nagekeken bij het naar de uitkomst gaan:
```text
 Leeravontuur › Wiskunde › Cijferen › Vermenigvuldigen › Reeks van 10

    Vraag 1 van 10    ◉ ○ ○ ○ ○ ○ ○ ○ ○ ○     Punten: 0
    Cijferend vermenigvuldigen · Makkelijk (4de leerjaar)

      955 × 6 =

            · 3 2 ·
              9 5 5
         ×        6
         ──────────
                    0   uitkomst  (typrichting ←)

      ! Kijk naar je onthouden-rij: boven de T moet een 3 staan, niet 2
        (5 × 6 = 30: schrijf 0 en onthoud 3).

      Typ van rechts naar links · ↑ = onthouden-rij · Tab = volgende rij






 [Enter] klaar  [?/F1] hulp  [r] richting  [p] E T H  [Esc] stoppen
```
(de 2 in de onthouden-rij staat in het rood met een !; de 3 boven de H is goed)

Normaal, rij 2 met de 0 en de zin bovenaan; `?` na het wisselen van rij:
```text
 Leeravontuur › Wiskunde › Cijferen › Vermenigvuldigen › Reeks van 10

    Vraag 1 van 10    ◉ ○ ○ ○ ○ ○ ○ ○ ○ ○     Punten: 0
    Cijferend vermenigvuldigen · Normaal (5de leerjaar)

      171 × 92 =         Eerst × de eenheden (2), dan × de tientallen (9),
                         dan tel je de twee rijen op.
            · · · · ·
                1 7 1
         ×        9 2
         ────────────
                2 4 2  rij 1  (171 × 2)
              ▮ 9 0    rij 2  (171 × 90: de 0 staat er al)
         + ──────────
                       uitkomst

      ! In rij 1 zit een redeneringsfout: kolom H. 1 × 2 = 2, plus de 1
        die je onthield (van 7 × 2 = 14) = 3.

      Typ van rechts naar links · ↑ = onthouden-rij · Tab = volgende rij



 [Enter] klaar  [?/F1] hulp  [r] richting  [p] E T H  [Esc] stoppen
```
(▮ = waar het kind typt; de 0 van rij 2 staat er vanzelf, in het grijs)

**Aanbeveling:** bouwen zoals hierboven. Daarvoor moet de leerlijn van het **4de** leerjaar × één cijfer worden
(nu × 2 cijfers), anders blijft Makkelijk voor een kind van het 5de toch 2 rijen hebben. Dat is ook wat de vader in
#19 schrijft: in Makkelijk geen vermenigvuldiging met een tiental.

- [ ] bouwen  - [ ] anders: …  - [ ] niet
- De 0 in rij 2 vanzelf bij Normaal (aanbevolen), of moet het kind ze zelf typen?
- De leerlijn van het 4de naar × 1 cijfer (aanbevolen)? Dat verandert ook wat een kind van het 4de krijgt.

---

## 3. Een voorbeeld dat oplicht (#20, deel c)

**Nu:** na de tips komt de spiekbrief (0.21.3). Die toont regels, geen voorbeeld dat je stap voor stap ziet
gebeuren.

**Voorstel:** een knop **[V] voorbeeld** in de spiekbrief vanuit een vraag, en na een fout ("Zo kan het:"). Je ziet
een **gelijkaardige** vraag (andere getallen, niet die van het kind), stap voor stap. Bij elke stap licht op wat je
gebruikt, en **Enter** = volgende stap. Na de laatste stap ga je terug naar je vraag (of naar de uitleg).

Stap 1 van 3 (compenseren):
```text
 Leeravontuur › Wiskunde › Hoofdrekenen › Optellen en aftrekken › Voorbeeld

    Zo reken je het: een voorbeeld                            stap 1 van 3

      36 + 98 = ?

      98 is bijna 100.
      Tel eerst 100 erbij:   36 + 100 = 136
                            ‾‾‾‾‾‾‾‾‾‾














 [Enter] volgende stap  [Esc] terug naar je vraag
```
Stap 3 van 3:
```text
 Leeravontuur › Wiskunde › Hoofdrekenen › Optellen en aftrekken › Voorbeeld

    Zo reken je het: een voorbeeld                            stap 3 van 3

      36 + 98 = ?

      98 is bijna 100.
      Tel eerst 100 erbij:   36 + 100 = 136
      Je telde 2 te veel:   136 − 2   = 134
      Dus:                   36 + 98  = 134   ✔
                                        ‾‾‾


      Nu jij! Druk Enter: je gaat terug naar je vraag.









 [Enter] terug naar je vraag  [Esc] terug naar je vraag
```
Bij cijferen licht de kolom op waar je rekent (zoals de hulp per vakje nu al de cijfers laat oplichten):
```text
 Leeravontuur › Wiskunde › Cijferen › Optellen › Voorbeeld

    Zo reken je het: een voorbeeld                            stap 2 van 4

            · · 1 ·
              5 4 7
         +    2 8 6
         ──────────
                  3
                ▔
      Kolom T: 4 + 8 = 12, plus de 1 die je onthield = 13.
      Schrijf 3 en onthoud 1 (bovenaan in de kolom links).











 [Enter] volgende stap  [Esc] terug naar je vraag
```
(▔ en ‾ tonen hier wat oplicht: op het scherm is dat een kleur, met in de eenvoudige tekens een ^ eronder)

**Aanbeveling:** bouwen, in twee fasen:
1. Cijferen (+ − ×), het rooster, want de hulp per kolom bestaat al.
2. Hoofdrekenen (compenseren, splitsen), uit de klad-regels van de oplossing, die ook al bestaan.

Andere onderwerpen volgen als het bevalt. Een voorbeeld telt niet als een tip voor de punten (het kind rekent zijn
eigen vraag nog zelf).

- [ ] bouwen  - [ ] anders: …  - [ ] niet
- Telt het voorbeeld als een tip (minder punten), of gratis (aanbevolen)?

---

## 4. De staartdeling: zelf de weg zoeken (#17)

**Nu:** het programma vraagt elke stap ("Stap 1: Hoeveel keer gaat 35 in 75?", "Stap 2: 2 × 35 = ?" …). Dat is
goed om te leren, maar het kind hoeft niet zelf te bedenken wat de volgende stap is:
```text
          7 5 4 5  │ 35
        − 7 0      ├─────
          ───      │ 2
            5      │

      Stap 4: Haal de 4 neer. Welk getal krijg je?      deel → maal → min → neer
```

**Voorstel per niveau:**
- **Makkelijk:** de stappen, zoals nu.
- **Normaal:** het kind vult de staartdeling **zelf** in, zoals op papier. Met de pijltjes of Tab ga je naar een
  vakje (het quotiënt rechts, het product, het verschil, het cijfer dat je neerhaalt) en je typt erin. **?** =
  hulp bij dat vakje ("Hoeveel keer gaat 35 in 75?"). **Enter** = nakijken: elke regel krijgt ✔ of ✘, en een
  fout krijgt één tweede kans.
- **Moeilijk en Heel moeilijk:** idem, maar zonder de grijze wenk "deel → maal → min → neer" en met de hulp pas
  na een fout.

Normaal, halverwege (het kind schreef 2 en 70, en staat nu bij het verschil):
```text
 Leeravontuur › Wiskunde › Cijferen › Staartdeling › Reeks van 10

    Vraag 1 van 10    ◉ ○ ○ ○ ○ ○ ○ ○ ○ ○     Punten: 0
    Staartdeling · Normaal (5de leerjaar)

      7545 : 35 =

          7 5 4 5  │ 35
        − 7 0      ├─────
          ───      │ 2 ▢ ▢
          ▮ ▢ ▢    │
        − ▢ ▢ ▢
          ───
            ▢ ▢

      Je staat bij: het verschil (75 − 70)          deel → maal → min → neer
      Pijltjes of Tab = naar een ander vakje · ? = hulp · Enter = nakijken






 [←→↑↓ Tab] vakje  [?/F1] hulp  [Enter] nakijken  [Esc] stoppen
```
(▢ = een leeg vakje, ▮ = waar het kind typt. Het programma tekent de vakjes die nodig zijn, zoals een
werkblad; het kind beslist zelf in welke volgorde het ze invult.)

Na Enter, met een fout in het product:
```text
          7 5 4 5  │ 35
        − 7 0      ├─────
          ───      │ 2 1 5
            5 4    │
        − 3 5      ✔
          ───
          1 9 5
        − 1 7 0    ✘  5 × 35 = 175, niet 170
          ───
            2 5    !  hierdoor klopt de rest niet: 195 − 175 = 20

      ✘ Bijna! Kijk naar de regel met ✘ en probeer nog eens (tweede kans).
```

**Aanbeveling:** bouwen, maar als **laatste** van groep C. Het is het grootste werk: een nieuw invoerscherm, het
nakijken per regel en de vakjes voor kommagetallen. Eerst een fase met alleen Normaal en natuurlijke getallen,
dan kommagetallen en Moeilijk.

- [ ] bouwen  - [ ] anders: …  - [ ] niet
- Mag het kind de vakjes in elke volgorde invullen (aanbevolen, zoals op papier), of altijd van boven naar onder?

---

## Volgorde (aanbevolen)

1. **0.22.0 — het logboek (#24):** A en B, plus de twee vraagtekens. Klein en meteen nuttig voor de ouder.
2. **0.22.1 — vermenigvuldigen per niveau (#19):** plus de leerlijn van het 4de, als de vader dat kiest.
3. **0.22.2 en 0.22.3 — het voorbeeld dat oplicht (#20c):** eerst cijferen, dan hoofdrekenen.
4. **0.23 — de staartdeling zelf invullen (#17):** in twee fasen.

Elke fase: een eigen PR met tests, de lange aapjestest en beelden in tmux, en daarna stoppen tot de vader akkoord
geeft.
