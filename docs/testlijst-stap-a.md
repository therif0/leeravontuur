# Testlijst stap A: de nieuwe menu's (vóór versie 0.20.0)

Deze lijst is voor de vader, om stap A zelf te proberen vóór de laatste fase (A6: handleiding, schermafdrukken,
uitbrengen). Vink af wat klopt en schrijf erbij wat niet klopt of wat Imrane ervan vindt.

**Let op:** de handleiding en de schermafdrukken tonen nog de oude menu's. Die worden bijgewerkt in A6.

## 0. Klaarzetten (op een kopie van de gegevens)

Zo verandert er niets aan de echte gegevens van Imrane. Sluit eerst Leeravontuur.

1. De versie van stap A ophalen (in de map van het programma):

   ```
   git fetch
   git checkout refactor/menustructuur-a
   ```

2. Een kopie maken van de gegevens en het programma met die kopie starten.

   **Windows (PowerShell):**
   ```
   Copy-Item -Recurse "$env:APPDATA\Leeravontuur" "$env:USERPROFILE\Leeravontuur-test"
   $env:LEERAVONTUUR_DATA = "$env:USERPROFILE\Leeravontuur-test"
   python oefeningen.py
   ```
   (In het gewone opdrachtvenster: `set LEERAVONTUUR_DATA=%USERPROFILE%\Leeravontuur-test`.)

   **macOS:**
   ```
   cp -R ~/Library/Application\ Support/Leeravontuur ~/Leeravontuur-test
   LEERAVONTUUR_DATA=~/Leeravontuur-test python3 oefeningen.py
   ```

   **Linux:**
   ```
   cp -R ~/.local/share/leeravontuur ~/Leeravontuur-test
   LEERAVONTUUR_DATA=~/Leeravontuur-test python3 oefeningen.py
   ```

   Zet `LEERAVONTUUR_DATA` telkens opnieuw als je een nieuw venster opent. Zonder die regel gebruikt het programma
   de echte gegevens.

3. Klaar met testen? Terug naar de gewone versie: `git checkout main`. De kopie (`Leeravontuur-test`) mag je weggooien.

## 1. Het hoofdmenu

- [ ] De volgorde is: ▶ Verder · Herhalen (n) · Wiskunde · Spiekbrieven · Mijn avatar · Zeg het ons ·
      Wissel van kind · Stoppen.
- [ ] Er staat geen "Leren & oefenen", geen "Snelrekenen" en geen "Opties" meer.
- [ ] Rechts staan de avatar en de punten zoals vroeger.

## 2. Wiskunde

- [ ] Wiskunde (3) toont 8 domeinen: Getallen · Hoofdrekenen · Cijferen · Breuken en procenten · Meten ·
      Tijd, geld en snelheid · Meetkunde · Vraagstukken.
- [ ] Breuken en procenten heeft 10 onderwerpen; toets **0** kiest het tiende (Korting en btw).
- [ ] Meten heeft 9 onderwerpen: de zeven maten (Lengte (m) … Maten zelf kiezen), Oppervlakte en omtrek, Formules.

## 3. De toetsen op een onderwerp

Ga naar Wiskunde › Hoofdrekenen en loop met ↑↓ door de onderwerpen.

- [ ] Onderaan (de voetregel) staan alleen de toetsen die bij het gemarkeerde onderwerp horen. Bij Tafels:
      `[Enter] reeks  [V] vrij  [S] spiekbrief  [T] 60 s  [Z] 20 sommen  [Esc] terug`.
- [ ] **Enter** (of het cijfer, of een klik op het onderwerp) start een reeks van 10, eerst met "Hoe moeilijk?".
- [ ] **V** start vrij oefenen, **S** toont de spiekbrief.
- [ ] Het werkt ook als hoofdletter (Shift), en met een kleine letter.
- [ ] Een letter die er niet bij hoort (bv. H bij Tafels, of X) doet niets.
- [ ] Na de oefening of de spiekbrief sta je terug in dezelfde lijst, op hetzelfde onderwerp.
- [ ] Een **klik op een knop in de voetregel** (bv. `[V] vrij`) doet hetzelfde als de toets.
- [ ] Een klik op de **broodkruimel** bovenaan (bv. op "Wiskunde") midden in een oefening brengt je naar dat menu.

## 4. Snelrekenen (nu in Hoofdrekenen)

- [ ] Tafels en Optellen en aftrekken: **T** = 60 seconden, **Z** = 20 sommen. De records van vroeger staan er nog.
- [ ] Gemengd (laatste onderwerp): Enter = 60 seconden; T en Z werken ook.
- [ ] Zet in Ouders › Kinderen › Imrane "Timer zichtbaar voor het kind" op **nee**. Daarna:
  - [ ] staat er bij geen enkel onderwerp nog `[T]`;
  - [ ] start Enter bij Gemengd 20 sommen.

  Zet de timer daarna terug zoals hij was.

## 5. Meten

- [ ] Eerst kies je de maat (bv. Lengte (m)), dan de toets: Enter reeks, V vrij, **H tabel-oefening**,
      S spiekbrief (hoe werkt omzetten?).
- [ ] Maten zelf kiezen: na de toets duid je eerst de eenheden aan (zoals vroeger).

## 6. Spiekbrieven (hoofdmenu)

- [ ] Spiekbrieven › Wiskunde › een domein › de spiekbrieven van dat domein (Meten: Eenheden omzetten en Meetkunde).

## 7. Verder en Herhalen (met zijn echte, gekopieerde gegevens)

- [ ] ▶ Verder stelt hetzelfde voor als in 0.19.0: eerst de herhaalvragen, anders zijn vorige oefening.
- [ ] Verder start die oefening ook echt.
- [ ] Herhalen (n) toont hetzelfde aantal als vroeger en werkt zoals vroeger.

## 8. Mijn avatar › Schermkleuren

- [ ] In Mijn avatar staat `[L] schermkleuren` in de voetregel, plus een klikbare regel
      "[L] schermkleuren: kies andere kleuren".
- [ ] L (of de klik) opent "Schermkleuren". Bij het huidige thema staat "✔ nu".
- [ ] Elk van de 5 thema's werkt meteen en blijft bewaard na het herstarten.
- [ ] Winkel (W), kast (K) en het gezichtje (←→) werken zoals vroeger.

## 9. Ouders › Kinderen › kind › Weergave

- [ ] Onder Leerjaar staat **Weergave**, met: Eenvoudige tekens, Muis, Typrichting in tabellen, Avatar, Animaties,
      Klok in een eigen venster.
- [ ] Elke instelling verandert met Enter (of een klik) en geldt meteen voor dat kind. Probeer bv.:
  - [ ] de muis uit;
  - [ ] de avatar uit;
  - [ ] de klok in de terminal.
- [ ] Ze geldt alleen voor dat kind (als er meer kinderen zijn).
- [ ] Naam, leerjaar, pincode, timer, winkel en wissen werken zoals vroeger.

## 10. Rapporten en export

- [ ] Het rapport staat per vak en domein (bv. "Wiskunde › Hoofdrekenen"), met de namen uit het menu. De maten
      staan samen onder "Maten".
- [ ] Snelrekenen staat **apart** onder zijn onderwerp ("Tafels, snelrekenen: … sommen"), niet meer meegeteld bij
      de gewone reeksen. Gemengd staat bij Gemengd.
- [ ] De samenvatting bovenaan (vragen, juist, dagen) is dezelfde als in 0.19.0.
- [ ] Exporteren (E): de CSV opent in Excel en heeft dezelfde kolommen als vroeger, met achteraan **vak** en
      **domein**.

## 11. Startargumenten en het klokvenster

- [ ] `--ascii`: alles in gewone tekens, ook de voetregel en de labels (× wordt x).
- [ ] `--kleurenblind`: de kleuren zijn anders. Kiest Imrane zelf een thema in Schermkleuren, dan wordt dat bewaard.
- [ ] `--ouder`: na het startscherm meteen het ouderdeel.
- [ ] Tijd, geld en snelheid › De klok: het klokvenster komt naast de terminal (op zijn ene scherm), en F2 zet de
      klok in de terminal en weer terug.

## 12. Wat Imrane ervan vindt

- Vindt hij zijn weg? Wat zoekt hij?
- Gebruikt hij de letters, de cijfers of de muis?
- Opmerkingen:
