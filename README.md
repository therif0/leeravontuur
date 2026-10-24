# Leeravontuur

**Een gratis leerprogramma van Solve It Now. Iedereen moet kunnen leren.**

Leeravontuur is een leerprogramma in de terminal voor kinderen in Vlaanderen. Het werkt op Windows, macOS en Linux,
is licht en kan ook met de muis bediend worden. Het groeit stap voor stap uit tot rekenen, taal en Frans
(zie [het plan](docs/plan.md)).

**Wat er nu in zit (versie 0.6):**
- **Eenheden omzetten:** lengte (km … mm) en massa (t … mg)
  - **Vrij oefenen:** zoveel vragen als je wil, met een tip (`?`) en uitleg na elk antwoord.
  - **Reeks van 10:** daarna je score en uitleg bij elke fout. Het programma herkent typische denkfouten,
    bv. *"je schoof de komma de verkeerde kant op"*.
  - **Tabel-oefening:** je vult de eenhedentabel in, één cijfer per vakje.
    - Met `Tab`, de pijltjes of een **muisklik** ga je naar een vakje.
    - Met `,` (of een klik op de rand tussen twee vakjes) zet je zelf de komma, en je ziet meteen wat je afleest.
    - Met `r` draai je de typrichting om.
  - **Spiekbrief** met uitleg en voorbeelden.
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
git clone https://github.com/therif0/oefeningenImrane.git
cd oefeningenImrane
python3 oefeningen.py
```
Een snelkoppeling in het startmenu maken (eenmalig): `python3 oefeningen.py --snelkoppeling`

### macOS
Installeer Python via [python.org](https://www.python.org/downloads/) (of `brew install python`) en doe daarna in de Terminal:
```bash
git clone https://github.com/therif0/oefeningenImrane.git
cd oefeningenImrane
python3 oefeningen.py
```

### Windows
1. Installeer Python via [python.org](https://www.python.org/downloads/) of de Microsoft Store.
2. Open **Windows Terminal** (aanbevolen; het gewone opdrachtvenster werkt ook) en doe:
```bat
git clone https://github.com/therif0/oefeningenImrane.git
cd oefeningenImrane
py -m pip install -r requirements.txt
py oefeningen.py
```
`requirements.txt` installeert op Windows één klein pakket (`windows-curses`). Op Linux en macOS installeert het niets.

Het venster moet minstens **80×24** tekens groot zijn.

### Bijwerken
```bash
git pull
```

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

## Voor ontwikkelaars
- Structuur en afspraken: [CLAUDE.md](CLAUDE.md). Het volledige plan: [docs/plan.md](docs/plan.md).
- Tests: `python3 -m unittest discover -s tests`. Ze draaien ook automatisch op Windows, macOS en Linux (GitHub Actions).

## Licentie
[CC BY-NC-SA 4.0](LICENSE): gratis gebruiken, delen en aanpassen, met vermelding van Solve It Now,
niet commercieel, en aanpassingen onder dezelfde licentie.
