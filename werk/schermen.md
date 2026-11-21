# Schermen 1.0: vakken zoals btop

**Status:** in overleg (21/11/2026) · beta voor Cijferen op de branch `beta-schermen-cijferen`

## Waarom
De vader (21/11): het scherm wordt slecht benut, vooral rechts onder het maatje. Op een groter venster blijft alles
linksboven in 80×24 staan. De vraag loopt over in de rest van de tekst, de tips zijn onduidelijk, het klad is één
regel ("typ hier je rekenregels") en je ziet niet hoeveel plaats er is. Voorbeeld: **btop**, met duidelijke vakken
en de titel in de rand. Het moet sober blijven, maar het mag een echte verbouwing worden: een betere 1.0.

## Gekozen
- 21/11: btop als voorbeeld: vakken met een titel in de rand, sober, één taak per vak.
- 21/11: het klad krijgt een betere plaats.

## Het voorstel (80×24, het kleinste scherm)
- **Vaste vakken**, links 60 breed en rechts 20 breed:
  - links: **Vraag**, **Klad** (of Antwoord), **Tip**;
  - rechts: **Maatje**, en daaronder **Reeks** of **Stappen**.
- **De tip staat altijd op dezelfde plaats**, met "Tip 1 van 3 ●○○" in de rand. Na de laatste tip komt de spiekbrief.
- **Het klad** is een vak met genummerde regels. Na een fout staan **jouw klad** (✔ ✘ !) en **Zo kan het** naast
  elkaar, en de uitleg krijgt een eigen vak, "Wat ging er mis?".
- **Toetsen** staan in de rand van het vak waar ze bij horen (Tab bij Klad, F1 bij Tip) en ook onderaan.
- **Op een groter venster** worden de vakken groter: het klad krijgt meer regels en de rechterkolom wordt breder.
  Tot nu toe blijft alles linksboven staan.
- **Een menu** krijgt ook vakken: de lijst, een kaartje over het gekozen onderwerp en de toetsen.

1 · Rekenen: de vraag, het klad en de tip elk in een eigen vak
```
 Wiskunde › Hoofdrekenen › Optellen en aftrekken                         ★ 2520
╭─┤ Vraag 2 van 10 ├───────────────────────────┤ Normaal ├─╮╭─┤ Maatje ├───────╮
│                                                          ││      ▄▄▄▄▄▄      │
│  7248 + 1365 = ┃          ┃                              ││     ▀▀▀▀▀▀▀▀▄▄▄  │
│                                                          ││   ▄▀▀▀▀▀▀▀▀▀▀▄   │
│  Kommagetal? 0,25 · Negatief? -5                         ││ ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄ │
│                                                          ││ ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ │
╰──────────────────────────────────────────────────────────╯│   ▀▀▀▀▀▀▀▀▀▀▀▀▄  │
╭─┤ Klad ├─────────────────────────────────────────────────╮│   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀ │
│   1  7248 + 1000 = 8248                                  ││      ▀▀▀▀▀▀  ▀▀  │
│   2  8248 + 300 = 8548                                   ││    Ik denk mee   │
│   3  ▌                                                   │╰──────────────────╯
│   4                                                      │╭─┤ Reeks ├────────╮
│   5                                                      ││ ✘◉○○○○○○○○  1/10 │
│   6                                                      ││                  │
│   7                                                      ││ juist    0 van 1 │
╰──────────────────────────────────────────────────┤ Tab ├─╯│ punten   +0      │
╭─┤ Tip 1 van 3  ●○○ ├─────────────────────────────────────╮│ tijd      1:40   │
│  Splits het tweede getal: 1365 = 1000 + 300 + 65.        ││                  │
│  Tel de stukken één voor één op.                         ││ Vandaag          │
│                                                          ││ 14 van 17 juist  │
│  Na tip 3: de spiekbrief.                                ││                  │
╰──────────────────────────────────────────┤ F1 volgende ├─╯╰──────────────────╯
 Enter controleren · Tab klad · F1 tip · Esc stoppen
```

2 · Na een fout: jouw klad naast "Zo kan het", de uitleg apart
```
 Wiskunde › Hoofdrekenen › Optellen en aftrekken                         ★ 2520
╭─┤ Vraag 1 van 10 ├───────────────────────────┤ Normaal ├─╮╭─┤ Maatje ├───────╮
│                                                          ││      ▄▄▄▄▄▄      │
│  5056 − 3025 = ┃ 1931     ┃                              ││     ▀▀▀▀▀▀▀▀▄▄▄  │
│                                                          ││   ▄▀▀▀▀▀▀▀▀▀▀▄   │
│  ✘ Niet juist. Het juiste antwoord is 2031.  (6 s)       ││ ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄ │
│                                                          ││ ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ │
╰──────────────────────────────────────────────────────────╯│   ▀▀▀▀▀▀▀▀▀▀▀▀▄  │
╭─┤ Jouw klad ├─────────────╮ ╭─┤ Zo kan het ├─────────────╮│   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀ │
│ 5056 − 3000 = 2056  ✔     │ │ 5056 − 3000 = 2056         ││      ▀▀▀▀▀▀  ▀▀  │
│ 2056 − 20 = 1936    ✘     │ │ 2056 − 20 = 2036           ││  Volgende lukt!  │
│ 1936 − 5 = 1931     !     │ │ 2036 − 5 = 2031            │╰──────────────────╯
│                           │ │                            │╭─┤ Reeks ├────────╮
│                           │ │                            ││ ✘○○○○○○○○○  1/10 │
╰───────────────────────────╯ ╰────────────────────────────╯│                  │
╭─┤ Wat ging er mis? ├─────────────────────────────────────╮│ juist    0 van 1 │
│  ! Regel 2: 2056 − 20 is 2036, niet 1936.                ││ punten   +0      │
│    Je zit er precies 100 naast: kijk naar de             ││ tijd      0:06   │
│    honderdtallen.                                        ││                  │
│                                                          ││ Herhaalbak       │
│  Splitsen: 3025 = 3000 + 20 + 5.                         ││ +1 vraag         │
│                                                          ││                  │
╰──────────────────────────────────────────────────────────╯╰──────────────────╯
 Enter volgende vraag · S spiekbrief · Esc stoppen
```

3 · Zinsdelen: de stappen rechts, de tip altijd op dezelfde plaats
```
 Taal › Zinsontleding › Zinsdelen                                        ★ 2520
╭─┤ Vraag 3 van 10 ├───────────────────────────┤ Normaal ├─╮╭─┤ Maatje ├───────╮
│  Stap 2 van 4: zoek het onderwerp (o).                   ││      ▄▄▄▄▄▄      │
│                                                          ││     ▀▀▀▀▀▀▀▀▄▄▄  │
│  Op  zondag  toont  papa  vier  goede  rapporten.        ││   ▄▀▀▀▀▀▀▀▀▀▀▄   │
│              ▀▀▀▀▀                                       ││ ▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄ │
│               pv                                         ││ ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀ │
│                                                          ││   ▀▀▀▀▀▀▀▀▀▀▀▀▄  │
│  pv toont    o …    lv …    mv …                         ││   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀ │
╰──────────────────────────────────────────────────────────╯│      ▀▀▀▀▀▀  ▀▀  │
╭─┤ Antwoord ├─────────────────────────────────────────────╮│    Goed bezig    │
│  ✘ Nog niet juist. Je tweede kans.                       │╰──────────────────╯
│                                                          │╭─┤ Stappen ├──────╮
│  ←→ woord · Spatie = erbij · Enter = dit is het o        ││ ✔ 1  pv  toont   │
│                                                          ││ ▸ 2  o           │
│                                                          ││   3  lv          │
╰──────────────────────────────────────────────────────────╯│   4  mv          │
╭─┤ Tip ├──────────────────────────────────────────────────╮│                  │
│  Nog geen tip gevraagd.                                  ││ Reeks            │
│  F1 = tip 1 van 2, daarna de spiekbrief.                 ││ ✔✘◉○○○○○○○  3/10 │
│                                                          ││ punten +12       │
│                                                          ││                  │
╰───────────────────────────────────────────────────┤ F1 ├─╯╰──────────────────╯
 Spatie erbij · Enter kies · F1 tip · Tab vrij kleuren · Esc stoppen
```

4 · Menu: de lijst, een kaartje over het onderwerp en de toetsen
```
 Wiskunde › Getallen                                                     ★ 2520
╭─┤ Getallen: wat wil je oefenen? ├────────────────────────────────────────────╮
│                                                                              │
│   1  Plaatswaarde   wat is elk cijfer waard? (E, T, H … t, h)                │
│                                                                              │
│   2  Getallenlijn   aflezen, aanduiden, sprongen, thermometer                │
│                                                                              │
│ ▸ 3  Afronden       op tientallen, honderdtallen … en tienden                │
│                                                                              │
│   4  Deelbaarheid   kenmerken, delers, priemgetallen, ggd, kgv               │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─┤ Afronden ├──────────────────────────────────╮ ╭─┤ Kies ├───────────────────╮
│  Laatst geoefend   3 dagen geleden            │ │ Enter  reeks van 10        │
│  Juist             ▓▓▓▓▓▓▓▓░░  8 van 10       │ │ V      vrij oefenen        │
│  Herhaalbak        2 vragen                   │ │ S      spiekbrief          │
│  Fris houden       nog 4 dagen                │ │                            │
│                                               │ │ Esc    terug               │
│  Moeilijk voor jou                            │ │                            │
│    op tienden afronden (3 keer fout)          │ │                            │
│                                               │ │                            │
│                                               │ │                            │
╰───────────────────────────────────────────────╯ ╰────────────────────────────╯

```

## Beta: Cijferen (21/11, de vader: "een branch voor alleen cijferen, de huidige schermen niet aanpassen")
- Starten: `LEERAVONTUUR_BETA=1 python3 leeravontuur.py`, dan Wiskunde › Cijferen (alle vier, reeks en vrij).
  Zonder die variabele is alles zoals in `main`.
- `terminal/vak.py` (een vak met de titel in de rand) en `terminal/beta.py` (`BetaOefenaar`: alleen een vraag met
  een rooster of een staartdeling wordt anders getekend; nakijken en bewaren zoals altijd). Het rooster en de
  staartdeling zelf zijn niet veranderd: ze tekenen in het vak via `InVak` (verschoven en afgeknipt).
- Vakken: Vraag (met de typrichting in de rand), Tip (F1 in de rand; na het nakijken "Wat ging er mis?" of "Goed!"),
  Maatje, Reeks (✔ ✘ per vraag, punten, op rij). Op een groter scherm wordt het vak breder; Tip blijft hoogstens 8
  rijen.
- Tests: `tests/test_beta.py` (elk rooster en elke staartdeling in elk leerjaar past in het vak).

## Wat het makkelijk maakt (architectuur)
- Eén onderdeel **`terminal/vak.py`** tekent een vak (rand, titel, toetsen in de rand, klikzone) met de rollen van
  het thema. In ASCII-modus komt er `+-|` in de plaats (`tekens.py`).
- Eén **indeling** voor de Oefenaar (welk vak waar, volgens de grootte van het scherm). De invoer-objecten (rooster,
  zinsdelen, werkwoord, vraagstuk …) tekenen in het vak dat ze krijgen, niet meer op vaste rijen en kolommen.
- Wat er in Reeks, Stappen en het menukaartje staat, komt uit de kern als regels met rollen (gouden regel 1 en 2).
  Wat er al is: de reeks, de punten, vandaag, de herhaalbak, fris houden, laatst geoefend en het percentage juist.
  Nieuw: "Moeilijk voor jou" (de denkfouten per onderwerp tellen).

## Open vragen (met de aanbeveling van Claude)
1. **Welke grootte heeft het venster van de zoon?** Het voorstel werkt op 80×24 en groeit mee. Aanbeveling: het
   echte venster meten (een kleine regel in het logboek bij het starten).
2. **Het klokvenster en de grote modellen** (klok, getallenlijn, schatkaart, rooster): die passen niet altijd in een
   vak van 60 breed. Aanbeveling: zo'n model krijgt het hele linkervak (Vraag + Klad), en het klad schuift dan onder
   het model, zoals nu.
3. **Rustig of uitgebreid?** Aanbeveling: rustig = alleen Vraag, Klad en Tip, met het maatje klein. Een keuze per kind
   bij Weergave.
4. **Wat staat er in het vak Tip vóór F1?** Aanbeveling: alleen "F1 = tip 1 van 3". De tip zelf komt nooit vanzelf
   (de getrapte tips blijven zoals ze zijn).
5. **Volgorde tegenover T2 Woordsoorten.** Aanbeveling: eerst de schermen (1.0), want T2 krijgt dan meteen de nieuwe
   vakken en hoeft niet twee keer gebouwd te worden. Maar dat verschuift Taal in `docs/koers.md`.
6. **Hoofdmenu en titelscherm in vakken?** Dat valt onder "een verandering aan het hoofdmenu", dus apart te kiezen.

## Fasen (een schets, pas vast als alles gekozen is)
0. Inventaris: elk scherm en elk invoer-object met zijn vaste rijen en kolommen, om af te vinken.
1. `vak.py` + de indeling + de Oefenaar met gewone vragen (Vraag, Klad, Tip, Maatje, Reeks).
2. De invoer-objecten in een vak: rooster, staartdeling, modellen, balk, klok, zinsdelen, werkwoord, vraagstuk.
3. Na een fout: jouw klad naast Zo kan het, en het vak "Wat ging er mis?".
4. Menu's met een kaartje; Eenheden, spiekbrieven, rapport en ouderdeel.
5. Groter venster: de vakken groeien mee.
