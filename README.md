# Leeravontuur

**Een gratis leerprogramma van Solve It Now. Iedereen moet kunnen leren.**

Leeravontuur is een leerprogramma in de terminal voor kinderen in Vlaanderen. Het werkt op Windows, macOS en Linux,
is licht en kan ook met de muis bediend worden. Het groeit stap voor stap uit tot rekenen, taal en Frans
(zie [het plan](docs/plan.md)).

**Wat er nu in zit (versie 0.15, bèta):**
- **Eenheden omzetten:** lengte (km … mm), massa (t … mg), inhoud (hl … ml), oppervlakte (km² … mm², ha, a,
  ca; vanaf het 5de leerjaar) en volume (m³, dm³, cm³ en de liter; vanaf het 6de), of alles **door elkaar**
  - **Vrij oefenen:** zoveel vragen als je wil, met een tip (`?`) en uitleg na elk antwoord.
  - **Reeks van 10:** daarna je score en uitleg bij elke fout. Het programma herkent typische denkfouten,
    bv. *"je schoof de komma de verkeerde kant op"*.
  - **Tabel-oefening:** je vult de eenhedentabel in, één cijfer per vakje.
    - Met `Tab`, de pijltjes of een **muisklik** ga je naar een vakje.
    - Met `,` (of een klik op de rand tussen twee vakjes) zet je zelf de komma, en je ziet meteen wat je afleest.
    - Met `r` draai je de typrichting om.
    - Bij oppervlakte heeft elke eenheid 2 vakjes, bij volume 3; ha, a, ca en de liters staan eronder.
  - **Spiekbrief** met uitleg en voorbeelden.
- **Hoofdrekenen:** maal- en deeltafels, optellen en aftrekken, × en : met 10/100/1000, verdubbelen en halveren
  - elke uitleg toont een strategie stap voor stap (compenseren, splitsen, × 9 = × 10 − 1 …)
  - herkent denkfouten (bv. *"bij compenseren moest je 1 aftrekken, je deed het omgekeerd"*)
  - vanaf het 1ste middelbaar ook met negatieve getallen
- **Getallen:** plaatswaarde (E, T, H … t, h, d), afronden, deelbaarheid (kenmerken, delers; vanaf het 6de
  ook priemgetallen, ggd en kgv) en de **getallenlijn**:
  - aflezen bij een pijl, sprongen (plus = naar rechts, min = naar links), een thermometer met negatieve getallen
  - **aanduiden**: zet de pijl met `←` `→` of een muisklik op het juiste streepje; ligt het getal tussen twee
    streepjes, dan **zoom je in** met `+` of het scrollwiel (en terug met `−`)
- **Cijferen** onder elkaar in een rooster: optellen, aftrekken en vermenigvuldigen (ook met 2 cijfers en
  kommagetallen)
  - je typt van rechts naar links; bovenaan is een **onthouden-rij**; `Tab` gaat naar de volgende rij
  - met `?` krijg je **hulp bij het vakje** waar je staat (bv. *"7 + 5 = 12: schrijf 2 en onthoud 1"*)
  - herkent denkfouten: onthouden vergeten, de kleinste van de grootste afgetrokken, de tweede rij niet
    opgeschoven, de komma op de verkeerde plaats
  - **staartdeling stap voor stap**: deel, vermenigvuldig, trek af, haal neer; de staartdeling groeit mee
- **Breuken** met de **breukbalk**: de noemer bepaalt in hoeveel stukken de balk verdeeld is (`↑` `↓`), met
  `←` `→` en spatie (of een klik) arceer je stukken, met `v` voeg je stukken samen (vereenvoudigen)
  - herkennen en arceren, gelijkwaardige breuken en vereenvoudigen, vergelijken (`<` `>` `=`), optellen en
    aftrekken (gelijknamig maken), een breuk van een getal (bolletjes in groepjes), × en :, breuk ↔ kommagetal
  - herkent denkfouten: tellers én noemers opgeteld (1/2 + 1/3 = 2/5), niet volledig vereenvoudigd,
    "grotere noemer = grotere breuk", teller en noemer omgewisseld …
  - na een fout tonen balken onder elkaar waarom (bv. 1/2 = 3/6 en 1/3 = 2/6)
- **Procenten** (vanaf het 5de leerjaar):
  - het **honderdveld**: aflezen en zelf kleuren (spatie, `r` voor een hele rij, of met de muis)
  - procent ↔ breuk ↔ kommagetal, procent van een getal met de **procentstrook** en een slimme strategie
    (*"10 % = 8, dus 20 % = 16"*), en vanaf het 6de **korting en btw** (in het 1ste middelbaar ook stijging en daling)
  - herkent denkfouten: het percentage als antwoord, alleen de korting berekend, de korting opgeteld …
- **Tijd, geld en snelheid:**
  - **de klok**: een echte wijzerklok in een eigen venster (of in de terminal) lezen en de wijzers zetten, tijden in woorden ("vijf voor half vier"), 24 uur,
    later en vroeger; herkent o.a. "half vier gelezen als 4.30"
  - tijd: u, min en s omrekenen, *"135 min = ? u ? min"* (typ `2 u 15 min`), tijdsduur en aankomstuur
    (typ `11.15`); herkent *"je rekende met 100 in plaats van 60"*
  - geld: euro en cent, wisselgeld, wat je samen betaalt
  - snelheid (vanaf het 6de): afstand = snelheid × tijd, en km/u ↔ m/s in het 1ste middelbaar
- **Meetkunde:**
  - oppervlakte en omtrek op een **cm²-rooster** (tel de vakjes en de randjes; ook halve vakjes bij een driehoek)
  - **formules** voor rechthoek, vierkant, driehoek, parallellogram, trapezium, cirkel en het volume van balk en
    kubus, met de formule ingevuld in de uitleg
  - **hoeken** benoemen bij een tekening of een aantal graden, de derde hoek van een driehoek (6de)
  - **schatkaart**: lees de coördinaat af (`C4`) of zet een kruisje met de pijltjes of de muis; in het 1ste
    middelbaar een assenstelsel met negatieve getallen
  - **schaal** (6de): 1 : 1000, van de kaart naar het echt en terug
- **Vraagstukken:**
  - verhaaltjes in **4 stappen**: lees (gegevens aanduiden, kiezen wat er gevraagd wordt), plan, reken in het
    **klad** (typ `0,75 x 3,20 = 2,40`; elke regel wordt nagekeken) en controleer (kan het kloppen?)
  - meteen antwoorden mag; fout = één tweede kans met een hulpje; tips met `?`, nooit het antwoord
  - een verhaalmachine mengt rekenstructuren met werelden (bakker, metselaar, boer …): duizenden verhalen,
    soms met een overbodig gegeven of een omgekeerde vraag
  - herkent denkfouten: een andere bewerking, gestopt na een tussenstap, niet omgezet, een overbodig gegeven …
  - **Speurneus**: zoek de fout in het klad van een ander kind, en zeg waarom
  - **schatten en controleren**: ongeveer hoeveel? Kan dat antwoord kloppen?
  - ook met tijd: hoe lang duurt de film, hoe laat komt de trein aan? Het klad kent kloktijden (`9.45 u + 35 min`)
- **Snelrekenen** (hoofdmenu): 60 seconden zoveel mogelijk, of 20 sommen om het snelst, met een klok die
  meeloopt, records (+25 punten) en een overzicht van je laatste rondes. Zet de ouder de timer uit, dan is
  er alleen "20 sommen" zonder klok.
- **Niveaus volgens het leerjaar:**
  - Makkelijk = een jaar lager, Normaal = eigen leerjaar, Moeilijk = een jaar hoger, Heel moeilijk = twee jaar hoger.
  - Het leerjaar stel je in bij **Opties**. Volgend schooljaar schuift alles mee.
- **Herhalen en slim kiezen:**
  - na elke reeks (en na vrij oefenen): **fouten opnieuw** (dezelfde vragen) of **gelijkaardige vragen** (nieuwe getallen)
  - een **herhaalbak**: wat fout ging, komt de volgende dagen terug met nieuwe getallen (na 1, 3 en 7 dagen);
    na 3 keer juist is het beheerst
  - vragen die het kind de laatste 30 dagen al kreeg, komen niet opnieuw; wat vaak fout gaat, komt vaker
  - **▶ Verder** in het hoofdmenu: eerst de herhaalvragen, anders verder met de vorige oefening
- **Punten en een avatar:**
  - punten voor elk juist antwoord (meer op een moeilijker niveau), bonussen voor 5 op rij, een reeks zonder fout
    en een onderwerp dat beheerst is; een vraag die al eens juist was, levert niets meer op
  - een **pixel-avatar** (een blokje à la Geometry Dash) staat in het hoofdmenu en naast de oefeningen, en reageert:
    blij, trots, denken, oeps … met een kort tekstje ("Psst… Tel de kolommen!")
  - zonder kleuren of in ASCII-modus wordt het een tekstgezichtje zoals `[^_^]`
  - ouders zien het puntenlogboek en kunnen bonuspunten geven
- **De winkel** (Mijn avatar → Winkel): een 30-tal items (vormen, kleuren, ogen, oren, haar, hoeden, accessoires)
  - eerst passen ("zo zie je eruit"), dan kopen met punten
  - bij elke aankoop een **rekenvraag**: *"Je hebt 200 punten, dit kost 70. Hoeveel heb je over?"*,
    vanaf het 5de leerjaar soms met korting (procenten); te weinig punten → *"hoeveel moet je nog sparen?"*
  - fout → *"Ben je zeker?"* en nog één kans; nog eens fout → een mini-lesje en een ludieke straf die de ouder kiest
    (standaard: *"de koerier is verdwaald, je pakje komt na 10 juiste antwoorden"*)
  - een **kast** om te wisselen wat je draagt, en combinaties om te bewaren
- **Een account per kind:** bij de start kies je wie er oefent ("Wie ben jij?"). Elk kind heeft eigen
  instellingen, en elk antwoord wordt bewaard (ook "vandaag al … vragen geoefend" blijft na een herstart).
- **Ouderdeel** (achter een wachtwoord; via "Wie ben jij?" → Ouders, of `--ouder`):
  - **rapporten** per dag, week, maand, schooljaar of zelf gekozen periode: score, tijd, per dag, per onderwerp,
    meest gemaakte denkfouten en de laatste fouten met het juiste antwoord
  - een **kalender** met de dagen waarop geoefend werd
  - **export** naar CSV (Excel/LibreOffice) en TXT, in de map Documenten/Leeravontuur
  - **kinderen beheren:** naam, leerjaar, timer zichtbaar of niet, pincode, alle gegevens exporteren, alles wissen
  - het ouderdeel sluit vanzelf na 10 minuten zonder toets
- **Opties (voor het kind):** naam, kleuren (ook voor **kleurenblindheid**), hoog contrast, eenvoudige tekens, muis en typrichting.

## Installeren en starten

Je hebt **Python 3.10 of nieuwer** nodig.

### Linux (bv. Fedora)
Python staat er meestal al op.
```bash
git clone https://github.com/therif0/leeravontuur.git
cd leeravontuur
python3 oefeningen.py
```
Een snelkoppeling in het startmenu maken (eenmalig): `python3 oefeningen.py --snelkoppeling`

### macOS
Installeer Python via [python.org](https://www.python.org/downloads/) (of `brew install python`) en doe daarna in de Terminal:
```bash
git clone https://github.com/therif0/leeravontuur.git
cd leeravontuur
python3 oefeningen.py
```

### Windows
1. Installeer Python via [python.org](https://www.python.org/downloads/) of de Microsoft Store.
2. Open **Windows Terminal** (aanbevolen; het gewone opdrachtvenster werkt ook) en doe:
```bat
git clone https://github.com/therif0/leeravontuur.git
cd leeravontuur
py -m pip install -r requirements.txt
py oefeningen.py
```
`requirements.txt` installeert op Windows één klein pakket (`windows-curses`). Op Linux en macOS installeert het niets.

Het venster moet minstens **80×24** tekens groot zijn.

De wijzerklok (bij **De klok**) verschijnt in een eigen venster met tkinter, dat bij Python hoort. Op Linux moet je
dat soms apart installeren: `sudo apt install python3-tk` (Ubuntu, Debian) of `sudo dnf install python3-tkinter`
(Fedora); op macOS met Homebrew: `brew install python-tk`. Zonder tkinter tekent de terminal de klok zelf.

### Bijwerken
```bash
git pull
```

## Handleiding
De volledige handleiding met schermafdrukken staat in [docs/handleiding](docs/handleiding/README.md): elk onderdeel,
elke optie, wat er per leerjaar aan bod komt, de herkende denkfouten, het ouderdeel en alle startargumenten.

## Na een nieuwe versie
- Wat er nieuw is: [CHANGELOG.md](CHANGELOG.md).
- Een korte testlijst voor de ouder (± 15 minuten): [docs/testlijst.md](docs/testlijst.md).
- Iets leuk, moeilijk of kapot? In het hoofdmenu staat **Zeg het ons**; de ouder leest het in het ouderdeel bij
  **Opmerkingen** (het bestand `feedback.txt` in de gegevensmap). Er wordt niets verstuurd.

## Opties bij het starten
| Argument | Wat het doet |
|---|---|
| `--kleurenblind` | kleuren voor rood-groen-kleurenblindheid (blauw = juist, oranje = fout); `--kleurenblind blauw-geel` voor blauw-geel |
| `--contrast` | hoog contrast (zwart-wit) |
| `--geen-kleur` | geen kleuren |
| `--ascii` | alleen eenvoudige tekens (voor oude terminals) |
| `--ouder` | meteen naar het ouderdeel |
| `--geen-muis` | muis uit, zodat je tekst gewoon kunt selecteren (met de muis aan lukt dat meestal met Shift ingedrukt) |
| `--versie` | versie tonen |
| `--fouten` | de laatste onverwachte fouten tonen (uit `fouten.log`, om door te sturen als er iets misloopt) |
| `--test` | de automatische tests uitvoeren |

Alles kan ook in het menu **Opties**; dat wordt bewaard.

## Ouderwachtwoord vergeten?
```bash
python3 oefeningen.py --wachtwoord-vergeten
```
Dat wist alleen het wachtwoord; de gegevens van de kinderen blijven bewaard. Het wachtwoord is een slot tegen
nieuwsgierige kinderen, geen echte beveiliging: wie aan de computer kan, kan het omzeilen. Wil je het echt
afschermen, geef je kind dan een eigen gebruikersaccount op de computer.

## Waar staan de gegevens?
| Systeem | Map |
|---|---|
| Windows | `%APPDATA%\Leeravontuur` |
| macOS | `~/Library/Application Support/Leeravontuur` |
| Linux | `~/.local/share/leeravontuur` |

Daar staat het bestand `leeravontuur.db` met de kinderen, hun instellingen en elk antwoord (met datum en
antwoordtijd). Er worden geen gegevens verstuurd: alles blijft op de computer.

**Reservekopieën en fouten:**
- In de submap `reserve` staat elke dag een kopie (de laatste 7 dagen; ververst bij het afsluiten), en een kopie
  van vóór elke grote update van het programma.
- Raakt `leeravontuur.db` toch beschadigd, dan zet het programma zelf de nieuwste goede kopie terug (en zegt het
  dat). Het beschadigde bestand blijft staan als `leeravontuur.db.beschadigd-…`.
- Zelf een kopie terugzetten: sluit het programma en kopieer een bestand uit `reserve` naar `leeravontuur.db`.
- Loopt er iets onverwachts mis, dan komt het kind terug in het menu en wordt de fout bewaard in `fouten.log`
  (bekijk met `--fouten`). Het programma twee keer tegelijk openen geeft eerst een waarschuwing.

## Voor ontwikkelaars
- Structuur en afspraken: [CLAUDE.md](CLAUDE.md). Het volledige plan: [docs/plan.md](docs/plan.md).
- Tests: `python3 -m unittest discover -s tests`. Ze draaien ook automatisch op Windows, macOS en Linux (GitHub Actions).

## Licentie
[CC BY-NC-SA 4.0](LICENSE): gratis gebruiken, delen en aanpassen, met vermelding van Solve It Now,
niet commercieel, en aanpassingen onder dezelfde licentie.
