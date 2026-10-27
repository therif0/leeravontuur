# Voorstel 0.21: mockups (groep B)

Dit zijn **alleen tekeningen**: er is nog niets gebouwd. Elk beeld is 80 × 24, zoals op het scherm (de avatar
rechtsboven is vereenvoudigd). Per wens: wat er nu is, het beeld, mijn aanbeveling en wat de vader kiest
(**bouwen**, **anders** (zeg hoe) of **niet**). Daarna bouw ik 0.21 in fasen, één wens per fase.

Kies gerust in een reactie op de PR, bv. "1 bouwen, 2 anders: links in plaats van rechts, 3a bouwen …".

---

## 1. Een digitaal klokje om op te antwoorden (#21)

**Nu:** bij "Schrijf dat zoals op een digitale klok (24-urennotatie)" typ je `16.10` in een gewoon antwoordvak.

**Voorstel:** het antwoordvak wordt een digitaal klokje met grote cijfers. Het kind typt **zoals nu** (`16.10`,
`16:10` of `1610`); de cijfers verschijnen meteen op het klokje, de `:` komt vanzelf, Backspace wist het laatste
cijfer. Lege plaatsen zijn grijs (`░`). In de eenvoudige tekens (ASCII) wordt `█` een `#`.

Bezig (1, 6, 1 getypt):
```text
 Leeravontuur › Wiskunde › Tijd, geld en snelheid › De klok › Vrij oefenen

    Vrij oefenen: 3 van 5 juist                                   ▄▄▄▄▄▄▄▄▄▄
    De klok · Normaal (5de leerjaar)                             ▀▀▀▀▀▀▀▀▀▀▀▀
                                                               ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄
      Het is tien over vier 's middags. Schrijf dat zoals op   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
      een digitale klok (24-urennotatie).                        ▀▀▀▀▀▀▀▀▀▀▀▀
                                                                 ▀▀▀▀▀▀▀▀▀▀▀▀
        ┌───────────────────────────────┐                         ▀▀▀▀▀▀▀▀▀▀
        │      █  ████        █  ░░░░   │
        │      █  █     ▪     █  ░  ░   │
        │      █  ████        █  ░░░░   │
        │      █  █  █  ▪     █  ░  ░   │
        │      █  ████        █  ░░░░   │
        └───────────────────────────────┘
      Klad (Tab)
      typ hier je rekenregels: 3 x 4 = 12



      Typ zoals altijd: 16.10 of 1610 (de : komt vanzelf) · Backspace


 [Tab] naar het klad  [Enter] controleren  [?/F1] tip  [Esc] stoppen
```

Klaar:
```text
        │     █  ████        █  ████  │
        │     █  █     ▪     █  █  █  │
        │     █  ████        █  █  █  │
        │     █  █  █  ▪     █  █  █  │
        │     █  ████        █  ████  │
```

**Aanbeveling:** het klokje bij **elke** vraag waar je een tijdstip typt: de 24-urennotatie, "Hoe laat is het
35 minuten later?", "vijf voor half vier in cijfers" en de tijd-vraagstukken. De wijzerklok blijft voor aflezen en
zetten. Een tijd als `9.45` toont `09:45`.

- [ ] bouwen  - [ ] anders: …  - [ ] niet
- Alleen bij de 24-urennotatie, of bij elk tijdstip (aanbevolen)?

---

## 2. Je klad blijft staan na het nakijken (#22)

**Nu:** zodra je antwoord nagekeken is, verdwijnt je klad; je ziet alleen "Zo kan het:".

**Voorstel:** rechtsonder een kader **Jouw klad** met je regels (✔ / ✘), naast de oplossing. Waar je klad afwijkt
van de oplossing, staat een `!` met één zin uitleg (dat weet het programma al: het is dezelfde nakijker als bij
"Kijk je klad nog eens na"). Te lange regels worden ingekort met `…`; zijn er meer dan 3 regels, dan de laatste 3.
```text
 Leeravontuur › Wiskunde › Hoofdrekenen › Optellen en aftrekken › Reeks van 10
                                               Volgende lukt!
    Vraag 1 van 10    ◉ ○ ○ ○ ○ ○ ○ ○ ○ ○     Punten: 0           ▄▄▄▄▄▄▄▄▄▄
    Optellen en aftrekken · Normaal (5de leerjaar)               ▀▀▀▀▀▀▀▀▀▀▀▀
                                                               ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄
                                                               ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
      3703 − 298 =   3401                                        ▀▀▀▀▀▀▀▀▀▀▀▀
                                                                 ▀▀▀▀▀▀▀▀▀▀▀▀
                                                                  ▀▀▀▀▀▀▀▀▀▀
      ✘ Niet juist. Het juiste antwoord is 3405.  (11 s)

      Bij compenseren moest je 2 erbij tellen, je deed het omgekeerd.
      Zo kan het:
        3703 − 300 = 3403
        3403 + 2 = 3405
      Compenseren: 298 is bijna 300.
      3703 − 300 = 3403, en dan 2 erbij: 3405.
                                        ┌ Jouw klad ─────────────────────────┐
                                        │ 3703 − 300 = 3403           ✔      │
                                        │ 3403 − 2 = 3401             !      │
                                        │ ! hier moest het + 2 zijn          │
                                        └────────────────────────────────────┘

 [Enter] volgende vraag  [Esc] stoppen
```

**Aanbeveling:** bouwen zoals hierboven. Alleen als het kind klad gebruikte (anders geen kader).

- [ ] bouwen  - [ ] anders: …  - [ ] niet

---

## 3a. Spiekbrieven: minder ver klikken (#20)

**Nu:** Spiekbrieven › Wiskunde › Getallen › "1. Getallen" › de spiekbrief: 4 keuzes voor één blad.

**Voorstel:**
- Zolang er maar één vak is (Wiskunde), slaan we "Welk vak?" over. Komt Taal erbij, dan staat die keuze er vanzelf
  weer.
- Een domein met één spiekbrief opent **meteen** de spiekbrief. Bij twee (Breuken en procenten, Meten, Tijd, geld
  en snelheid) kies je daarna nog welke; de uitleg zegt welke er zijn.

Spiekbrieven › (Getallen = meteen het blad):
```text
 Leeravontuur › Spiekbrieven


    Welke spiekbrief?

       1. Getallen                 plaatswaarde, afronden, deelbaarheid
       2. Hoofdrekenen             tafels, splitsen, compenseren
       3. Cijferen                 onder elkaar, staartdeling
       4. Breuken en procenten     2 spiekbrieven: Breuken, Procenten
       5. Meten                    2: Eenheden omzetten, Oppervlakte …
       6. Tijd, geld en snelheid   2: De klok, Tijd, geld en snelheid
       7. Meetkunde                hoeken, schatkaart, schaal
       8. Vraagstukken             het stappenplan, Speurneus, schatten

    Enter = de spiekbrief (bij twee: eerst kiezen welke)








 [↑↓] kiezen  [Enter] ok  [Esc] terug
```

**Aanbeveling:** bouwen. Van 4 keuzes naar 1 (of 2).

- [ ] bouwen  - [ ] anders: …  - [ ] niet

## 3b. De spiekbrief vanuit de oefening (#20)

**Nu:** tijdens een oefening kan je de spiekbrief niet openen.

**Voorstel:** na de laatste tip zegt de tip "Nog hulp nodig? Druk nog eens ?/F1: je spiekbrief." De volgende `?`
of F1 opent de spiekbrief van dat onderwerp, meteen bij het juiste stuk. **Esc** = terug naar dezelfde vraag, met
alles wat je al typte (antwoord en klad). Daarna begint `?` weer bij tip 1. Geen aparte letter-toets: een `S`
botst met typen (klad, ja/nee, woorden).
```text
 Leeravontuur › Wiskunde › Getallen › Plaatswaarde › Vrij oefenen

    Vrij oefenen: 0 van 0 juist                                   ▄▄▄▄▄▄▄▄▄▄
    Plaatswaarde · Normaal (5de leerjaar)                        ▀▀▀▀▀▀▀▀▀▀▀▀
                                                               ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄
      Schrijf als getal: 4 D + 7 TD + 5 H + 3 T =              ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
                                                                 ▀▀▀▀▀▀▀▀▀▀▀▀
                                                                 ▀▀▀▀▀▀▀▀▀▀▀▀
                                                                  ▀▀▀▀▀▀▀▀▀▀
      Tip 3 van 3: Zet elk cijfer op zijn plaats; een plaats
      zonder cijfer krijgt een 0.
      Nog hulp nodig? Druk nog eens ?/F1: je spiekbrief.


      Kommagetal? Gebruik een komma: 0,25. Negatief? Typ een min: -5








 [Enter] controleren  [?/F1] spiekbrief  [Esc] stoppen
```

```text
 Leeravontuur › Wiskunde › Getallen › Plaatswaarde › Spiekbrief

    PLAATSWAARDE
      M  HD  TD  D  H  T  E , t  h  d
      M = miljoenen, HD = honderdduizendtallen, TD = tienduizendtallen,
      D = duizendtallen, H = honderdtallen, T = tientallen, E = eenheden,
      t = tienden, h = honderdsten, d = duizendsten
      In 3 405,7 is de 4 vierhonderd waard (4 H), de 7 zeven tienden (0,7).

    AFRONDEN
      Kijk naar het cijfer rechts: 0-4 naar beneden, 5-9 naar boven.











                                                          ▼ scroll voor meer ▼
 [↑↓] scrollen  [Esc] terug naar je vraag
```

**Aanbeveling:** bouwen. De spiekbrief telt als één tip voor de punten (net als een gewone tip).

- [ ] bouwen  - [ ] anders: …  - [ ] niet
- Telt de spiekbrief als een tip (aanbevolen), of is hij gratis?

*(3c, een voorbeeld dat stap voor stap oplicht, komt later: dat is groep C.)*

---

## 4. Plaatswaarden boven het rooster (#18)

**Nu:**
```text
 Leeravontuur › Wiskunde › Cijferen › Optellen › Vrij oefenen

    Vrij oefenen: 0 van 0 juist                                   ▄▄▄▄▄▄▄▄▄▄
    Cijferend optellen · Normaal (5de leerjaar)                  ▀▀▀▀▀▀▀▀▀▀▀▀
                                                               ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄
                                                               ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
      6662 + 4812 + 2669 =                                       ▀▀▀▀▀▀▀▀▀▀▀▀
                                                                 ▀▀▀▀▀▀▀▀▀▀▀▀
            · · · · ·                                             ▀▀▀▀▀▀▀▀▀▀
              6 6 6 2
              4 8 1 2
         +    2 6 6 9
         ────────────
                    1  uitkomst  (typrichting ←)




      Typ van rechts naar links · ↑ = onthouden-rij · Tab = volgende rij




 [Enter] klaar  [?/F1] hulp  [r] richting  [Esc] stoppen
```

**Voorstel:** toets **p** zet de plaatswaarden aan of uit: `E T H D TD HD M` boven de kolommen (en `t h d` na de
komma). De kolommen worden dan iets breder, zodat `TD` en `HD` leesbaar blijven. Rechts staat in welke kolom je
staat (die letter licht ook op). Werkt bij optellen, aftrekken en vermenigvuldigen.
```text
 Leeravontuur › Wiskunde › Cijferen › Optellen › Vrij oefenen

    Vrij oefenen: 0 van 0 juist                                   ▄▄▄▄▄▄▄▄▄▄
    Cijferend optellen · Normaal (5de leerjaar)                  ▀▀▀▀▀▀▀▀▀▀▀▀
                                                               ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄
                                                               ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
      6662 + 4812 + 2669 =                                       ▀▀▀▀▀▀▀▀▀▀▀▀
           TD  D  H  T  E  ◂ je staat bij de T (tientallen)      ▀▀▀▀▀▀▀▀▀▀▀▀
            ·  ·  ·  ·  ·                                         ▀▀▀▀▀▀▀▀▀▀
               6  6  6  2
               4  8  1  2
       +       2  6  6  9
       ─────────────────
                        3   uitkomst  (typrichting ←)




      Typ van rechts naar links · ↑ = onthouden-rij · p = plaatswaarden




 [Enter] klaar  [?/F1] hulp  [r] richting  [p] plaatswaarden  [Esc] stoppen
```

**Aanbeveling:** bouwen; standaard **uit**, en wat het kind kiest wordt per kind onthouden (zoals de typrichting).
De ouder kan het ook aanzetten in Ouders › Kinderen › Weergave.

- [ ] bouwen  - [ ] anders: …  - [ ] niet
- Standaard uit (aanbevolen) of aan? Bij Makkelijk altijd aan?

---

## 5. De plaatswaarde-tabel na een fout (opmerking bij #20)

**Nu:** bij Getallen › Plaatswaarde zegt een eerste fout alleen "Nog niet juist. Probeer nog eens."; na de tweede
fout staat de uitleg in tekst. (Klein ding gezien: "Het juiste antwoord is 74530" staat zonder spatie, de uitleg
schrijft "74 530". Dat zet ik recht.)

**Voorstel:** na de **eerste** fout zie je je eigen antwoord in de tabel (zonder het juiste te verklappen):
```text
 Leeravontuur › Wiskunde › Getallen › Plaatswaarde › Vrij oefenen

    Vrij oefenen: 0 van 0 juist                                   ▄▄▄▄▄▄▄▄▄▄
    Plaatswaarde · Normaal (5de leerjaar)                        ▀▀▀▀▀▀▀▀▀▀▀▀
                                                               ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄
      Schrijf als getal: 4 D + 7 TD + 5 H + 3 T =              ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
                                                                 ▀▀▀▀▀▀▀▀▀▀▀▀
                                                                 ▀▀▀▀▀▀▀▀▀▀▀▀
                                                                  ▀▀▀▀▀▀▀▀▀▀
      Nog niet juist. Zet elk cijfer in zijn kolom en probeer nog eens:

               │ HD │ TD │ D  │ H  │ T  │ E  │
        ───────┼────┼────┼────┼────┼────┼────┤
         jij   │    │ 4  │ 7  │ 5  │ 3  │ 0  │


      Kommagetal? Gebruik een komma: 0,25. Negatief? Typ een min: -5






 [Enter] controleren  [?/F1] tip  [Esc] stoppen
```

Na de **tweede** fout komen jouw rij en de juiste rij onder elkaar, met wat er misging (hier: TD en D gewisseld):
```text
 Leeravontuur › Wiskunde › Getallen › Plaatswaarde › Vrij oefenen
                                           Niet erg, probeer!
    Vrij oefenen: 0 van 1 juist                                   ▄▄▄▄▄▄▄▄▄▄
    Plaatswaarde · Normaal (5de leerjaar)                        ▀▀▀▀▀▀▀▀▀▀▀▀
                                                               ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄
      Schrijf als getal: 4 D + 7 TD + 5 H + 3 T =              ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
       47 530                                                    ▀▀▀▀▀▀▀▀▀▀▀▀
                                                                 ▀▀▀▀▀▀▀▀▀▀▀▀
                                                                  ▀▀▀▀▀▀▀▀▀▀
      ✘ Niet juist. Het juiste antwoord is 74 530.  (7 s)

               │ HD │ TD │ D  │ H  │ T  │ E  │
        ───────┼────┼────┼────┼────┼────┼────┤
         jij   │    │ 4  │ 7  │ 5  │ 3  │ 0  │
         juist │    │ 7  │ 4  │ 5  │ 3  │ 0  │

      Je wisselde TD en D: 7 TD = 70 000 en 4 D = 4 000.
      Een plaats zonder cijfer krijgt een 0.





 [Enter] volgende vraag  [Esc] stoppen
```

**Aanbeveling:** bouwen, bij alle plaatswaarde-vragen (ook met kommagetallen: dan `, t h d` erbij). Het herkennen
van "TD en D gewisseld" en "tientallen en tienden verwisseld" wordt een nieuwe denkfout in het rapport.

- [ ] bouwen  - [ ] anders: …  - [ ] niet

---

## Hoe het verder gaat
1. De vader kiest per wens (in de PR of in de chat).
2. Ik bouw 0.21 in fasen (één wens per fase, met tests en tmux-beelden), elke fase een eigen PR.
3. Daarna de voorstellen van groep C: cijferend vermenigvuldigen per niveau (#19), de staartdeling zelf invullen
   (#17), het logboek voor de ouder (#24) en het voorbeeld dat oplicht (#20).
