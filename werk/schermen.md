# Schermen 1.0: vakken zoals btop

**Status:** klaar voor actie (22/11/2026): alle vragen beantwoord, de fasen hieronder. Beta voor Cijferen op de
branch `beta-schermen-cijferen`; de inventaris (fase 0) staat in [schermen-inventaris.md](schermen-inventaris.md).

## Waarom
De vader (21/11): het scherm wordt slecht benut, vooral rechts onder het maatje. Op een groter venster blijft alles
linksboven in 80×24 staan. De vraag loopt over in de rest van de tekst, de tips zijn onduidelijk, het klad is één
regel ("typ hier je rekenregels") en je ziet niet hoeveel plaats er is. Voorbeeld: **btop**, met duidelijke vakken
en de titel in de rand. Het moet sober blijven, maar het mag een echte verbouwing worden: een betere 1.0.

## Gekozen
- 21/11: btop als voorbeeld: vakken met een titel in de rand, sober, één taak per vak.
- 21/11: het klad krijgt een betere plaats.
- 22/11 (na de eerste test van de beta, een schermafdruk met "KLAD?" en "SPIEKBRIEFJE?" in de lege plaatsen): de
  **spiekbrief staat altijd open** waar er plaats is, met het stuk van de vraag in het licht; in een examen niet.

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
- 22/11: **Klad** naast het rooster waar er minstens 24 kolommen over zijn (hoogstens 44 breed): Tab of een klik = naar
  het klad, Tab of Enter op een lege regel = terug. Elke regel krijgt ✔ ✘ (klopt de rekenregel?), niet tegenover
  een oplossing; het klad gaat mee met het antwoord (`extra["klad"]`). Keuze van Claude, nog te bevestigen.
  **Spiekbrief** onderaan als er minstens 5 rijen over zijn (op 80×24 meestal niet). "deel → maal → min → neer"
  staat nu in de rand van het vak Vraag.
- 22/11, tweede ronde (de vader, met een schermafdruk): **Reeks bovenaan** onder de broodkruimel (een vak vanaf 30
  rijen, anders één regel); de vraag valt op door **meer lucht** rond + − × : = (groter typen kan niet in een terminal,
  de vader: dan laten vallen); het **klad is een kolom van boven tot onder** naast Vraag, Tip en Spiekbrief (hoogstens
  34 breed); de **spiekbrief scrollt** (PgUp, PgDn, het scrollwiel, of een klik op PgUp/PgDn in de rand); het maatje
  heeft de rechterkolom.
- **Eén werkwijze voor alle oefeningen** (de vader: geen K, die typen ze in woorden): **Tab = het klad** en terug,
  zoals overal. In het rooster deed Tab "volgende rij": in de beta doet ↓ dat nu (de volgende rij, rechts
  beginnen). Zonder plaats voor het klad blijft Tab "volgende rij". De voetregel laat [r] weg als het klad er is
  (r staat in de rand), zodat [Esc] stoppen altijd past.
- 22/11, de vraag (de vader, na schetsen in de chat; groter typen kan niet, grote blokcijfers "zijn niet mooi"): de
  vraag in **oranje op een donkergrijze band** (256 kleuren: 208 op 236), 3 rijen hoog vanaf 30 rijen (anders 1),
  één spatie van de rand; het rooster **rustiger** (de cijfers gewoon, niet vet); de **cursor donkergeel** (178);
  **twee lege rijen** onder "uitkomst". Rollen `b_vraag`, `b_band`, `b_cursor` in `terminal/thema.py`, met een eigen
  waarde per thema (kleurenblind: wit op grijs, want oranje is daar "fout"; hoog contrast: zwart op wit; zonder
  kleur: omgekeerd).
- **Uitrollen** (de vader, 22/11): als hij goedkeurt wat hij ziet, krijgt **elke oefening** deze vraag (band, kleuren,
  cursor). Daarvoor komt eerst de inventaris (fase 0) van alle schermen en invoer-objecten.
- Tests: `tests/test_beta.py` (elk rooster en elke staartdeling in elk leerjaar past in het vak).

## Wat het makkelijk maakt (architectuur)
- Eén onderdeel **`terminal/vak.py`** tekent een vak (rand, titel, toetsen in de rand, klikzone) met de rollen van
  het thema. In ASCII-modus komt er `+-|` in de plaats (`tekens.py`).
- Eén **indeling** voor de Oefenaar (welk vak waar, volgens de grootte van het scherm). De invoer-objecten (rooster,
  zinsdelen, werkwoord, vraagstuk …) tekenen in het vak dat ze krijgen, niet meer op vaste rijen en kolommen.
- Wat er in Reeks, Stappen en het menukaartje staat, komt uit de kern als regels met rollen (gouden regel 1 en 2).
  Wat er al is: de reeks, de punten, vandaag, de herhaalbak, fris houden, laatst geoefend en het percentage juist.
  Nieuw: "Moeilijk voor jou" (de denkfouten per onderwerp tellen).

## Gekozen over de uitrol (23/11, de vader)
- **De uitrol gaat per kind, niet alles tegelijk** (voorstel van Claude, de vader akkoord): een schakelaar bij de ouder
  zet de nieuwe schermen voor één kind aan of uit, zodat de vader zijn zoon kan overzetten wanneer hij klaar is en
  meteen kan terugzetten. De details staan bij fase 7b.

## Gekozen na de inventaris (22/11, de vader)
De details en de nummers staan in [schermen-inventaris.md](schermen-inventaris.md) (*Open vragen*).
- **Eén werkwijze** voor alle oefeningen: Vraag, Klad (Tab), Tip (F1), dan de spiekbrief.
- **Klad:** blijft uit waar het vandaag uit staat (het klad kijkt rekenregels na, als een rekenmachine). Waar er geen
  klad is, valt de kolom weg. **Cijferen krijgt geen klad-kolom** (die in de beta was een test van de indeling).
  Tab houdt zijn betekenis op schermen zonder klad (zinsdelen, werkwoord, rooster).
- **Vraagstuk:** het verhaal in het Vraag-vak, de stappen in een vak **Stappen** rechts, geen eigen klad meer (stap 3
  gebruikt de klad-kolom), tips in het vak Tip; **de pijltjes** = naar een andere stap (↓ voorbij het laatste in een
  stap = volgende stap, ↑ bovenaan = vorige); klikken werkt overal.
- **Grote modellen** (getallenlijn, breukbalk, groepjes, klok, schatkaart …): de volle breedte links; Tip eronder.
- **Tip-vak vóór F1:** alleen "F1 = tip 1 van n"; een tip komt nooit vanzelf. Objecten met eigen tips geven de tekst,
  het vak Tip toont ze.
- **Na een fout:** "Zo kan het" alleen waar de kern een voorbeeld heeft; anders alleen "Wat ging er mis?".
- **Spiekbrief:** open waar er plaats is; op 80×24 opent F1 na de laatste tip hem over het hele scherm (zoals nu);
  in een examen krijgt de vraag de vrije plaats.
- **Rustig (F3):** een schakelaar van het kind: alleen Vraag, Antwoord en Klad; alle toetsen blijven werken; F1 geeft
  toch een tip (even); onthouden per kind.
- **Groot scherm:** de zoon heeft 1920×1080, vaak in een tty (ongeveer 240×67). De vakken groeien **tot ongeveer
  120×40** en staan dan in het midden. De ondergrens blijft 80×24. **In de tty niets veranderen** (werkt perfect).
- **Klokvenster open:** de rechterkolom (maatje) valt weg.
- **Kleuren (de band, de rand):** voorzichtig, **per soort vraag een eigen ontwerp** waar het nodig is (bij Snelrekenen
  niet echt, bij een vraagstuk helemaal anders). Eerst een schets, dan bouwen. De `b_`-rollen worden gewone rollen.
- **Eenheden** gaat eerst op in de Oefenaar (een opruimstap; het kind ziet niets).
- **Menu's:** op 80×24 zonder lege regels tussen de items; lege regels vanaf 30 rijen.
- **Snelrekenen:** vakken Vraag, Tijd en Reeks; geen klad.
- **Ouderdeel, kinderkeuze, winkel, slot, oeps, opmerkingen:** als laatste, alleen een kader rond wat er is.
- **Hoofdmenu en titelscherm:** later en apart (een verandering aan het hoofdmenu).
- **Beta → iedereen:** per domein achter de schakelaar `LEERAVONTUUR_BETA`; de oude weg gaat weg als heel Wiskunde over
  is (dan weer één codepad).
- **Geen instelling "uitgebreid"** naast Rustig; **T2** nog niet (`docs/koers.md` blijft).

## Fasen (klaar voor actie)
Elke fase = een eigen branch (op de vorige gestapeld) met een pull request naar `main` en een eigen versie (vanaf
0.27.0). Bewijs per fase: de volledige suite + de aapjestest, de schermen in tmux op **80×24, 120×40 en 240×67**, in
ASCII-modus en in elk thema, één keer in een echte tty, en een vergelijking met de vorige versie op een kopie van
echte gegevens. De schakelaar `LEERAVONTUUR_BETA=1` blijft tot fase 8: zonder is alles zoals in `main`.
**Stoppen en vragen bij:** een migratie van de databank, het hoofdmenu, iets tegen een keuze hierboven, een test die
niet netjes op te lossen is, en bij elke **schets** (★).

0. ✔ **Inventaris** (22/11): [schermen-inventaris.md](schermen-inventaris.md).
1. ✔ **Opruimen vooraf (het kind ziet niets)** (0.27.0, branch `schermen-1-opruimen`):
   - Eenheden in de Oefenaar: de tabel wordt een invoer-object; `schermen/eenheden.py` verdwijnt grotendeels.
   - De klad-kolom uit de Cijferen-beta halen.
   - Bewijs: dezelfde schermen en dezelfde bewaarde antwoorden als vóór de stap.
2. ✔ **Bouwstenen** (0.28.0, branch `schermen-2-bouwstenen`):
   - `vak.py` (focus, scrollen, ASCII); één **indeling** (welk vak waar, van 80×24 tot 120×40, daarboven in het
     midden; klokvenster).
   - Elk invoer-object krijgt een rechthoek en zegt zijn breedte, hoogte en randtekst: `InVak`, `Meter`,
     `VERSCHUIF` en `KORTER` uit de beta verdwijnen.
   - Rollen: `b_vraag`/`b_band`/`b_cursor` worden gewone rollen in elk thema (ook de gekochte schermkleuren).
   - Kern: de regels met rollen voor Reeks, Vandaag, Herhaalbak, fris houden, laatst geoefend.
   - Tests: elk object en elk model past in zijn vak op elke grootte; klikken in tests via de zone van een actie, niet
     via (y, x).
3. **De Oefenaar met gewone vragen** (Hoofdrekenen, Breuken en procenten, Meten met Eenheden, Tijd/geld/snelheid,
   Getallen zonder model):
   - Vraag (band), Klad-kolom (alleen waar er klad is), Tip ("Tip 1 van n"), Maatje, Reeks bovenaan, spiekbrief open
     waar er plaats is; vrij oefenen, examen, tweede kans.
   - Na een fout: jouw klad, "Zo kan het" (waar de kern het heeft), "Wat ging er mis?".
   - **Rustig (F3)**, onthouden per kind (als dat een migratie vraagt: stoppen).
4. **Modellen en invoer-objecten:** getallenlijn (en aanduiden met zoom), breukbalk, cm²-veld, schatkaart, klok
   (wijzers, digitaal klokje, klokvenster), groepjes, strook, figuur, hoek: volle breedte links. Cijferen (rooster,
   staartdeling) op de nieuwe bouwstenen.
5. **Vraagstukken** (★ eerst een schets van het ontwerp, ook de kleuren): het verhaal, Stappen rechts, de klad-kolom,
   de pijltjes, tips in Tip; Speurneus en Schatten en controleren.
6. **Taal:** Zinsdelen (scherm 3); Werkwoordspelling (★ eerst een schets: kofschip, bron, gevonden). Tab blijft.
7. **Rond de oefening:**
   - Menu's met een kaartje (scherm 4; nieuw in de kern: "Moeilijk voor jou").
   - Spiekbrieven, Gemengd en Herhalen.
   - Snelrekenen (Vraag, Tijd, Reeks).
   - Het einde van een reeks (★ eerst een schets).
7b. **De schakelaar "Nieuwe schermen"** (per kind, voor de uitrol):
   - `Instellingen.nieuwe_schermen` (standaard uit), te zetten door de ouder bij Ouders › Kinderen › kind ›
     **Weergave**. `LEERAVONTUUR_BETA=1` blijft bestaan om te testen en geeft altijd de nieuwe schermen.
   - Dezelfde codepaden als de beta: de schakelaar kiest alleen welke weg het scherm neemt.
   - Instellingen staan per kind in de JSON, dus waarschijnlijk **geen migratie**. Vraagt het toch een migratie:
     **stoppen en vragen**.
   - Open vragen voor de vader: de naam in het menu ("Nieuwe schermen"?); alleen per kind, of ook per domein; alleen
     de ouder mag hem omzetten (aanbeveling: ja, het kind kiest dit niet zelf).
8. **Beta → iedereen:**
   - **Pas als de vader zijn zoon een tijd op de nieuwe schermen liet oefenen en akkoord geeft**: de schakelaar
     (`nieuwe_schermen` en `LEERAVONTUUR_BETA`) en de oude weg verdwijnen (één codepad).
   - Een kader rond ouderdeel, kinderkeuze, winkel, slot, oeps en opmerkingen.
   - Documenten: `docs/architectuur.md` (schermen: vakken en indeling), CLAUDE.md ("past in 80×24 en groeit mee"),
     `docs/testlijst.md`, CHANGELOG, README.
   - Het hoofdmenu en het titelscherm blijven buiten dit plan (vraag 6).
