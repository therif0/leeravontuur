# Problemen oplossen

[← terug naar de inhoud](README.md)

Leeravontuur is gemaakt om nooit werk te verliezen: elk antwoord wordt meteen bewaard en er zijn elke dag
reservekopieën. Hier staat waar alles staat en wat je doet als er toch iets misloopt.

## Waar staan de gegevens?

Alles staat in één **gegevensmap** op de computer. Er wordt niets verstuurd.

| Systeem | Gegevensmap |
|---|---|
| Windows | `%APPDATA%\Leeravontuur` (bv. `C:\Users\<naam>\AppData\Roaming\Leeravontuur`) |
| macOS | `~/Library/Application Support/Leeravontuur` |
| Linux | `~/.local/share/leeravontuur` |

Met de omgevingsvariabele `LEERAVONTUUR_DATA` kies je een andere map (zie [Startargumenten](startargumenten.md)).

| In de gegevensmap | Wat het is |
|---|---|
| `leeravontuur.db` | De databank: kinderen, instellingen, alle antwoorden, punten, avatar, herhaalbak. |
| `reserve/` | Reservekopieën van de databank (zie hieronder). |
| `fouten.log` | Het foutenlogboek. |
| `feedback.txt` | De opmerkingen uit [Zeg het ons](zeg-het-ons.md). |
| `leeravontuur.lock` | Het slotbestand zolang het programma openstaat. |

Geëxporteerde rapporten komen in **Documenten/Leeravontuur** (zie [het ouderdeel](ouderdeel.md#rapporten)).

**Naar een andere computer?** Kopieer de hele gegevensmap naar dezelfde plaats op de nieuwe computer (terwijl het
programma gesloten is).

## Reservekopieën en automatisch herstel

- Elke dag wordt er een reservekopie gemaakt in `reserve/` (ververst als je het programma sluit). De kopieën van de
  laatste **7 dagen** blijven bewaard; de oudste verdwijnen vanzelf.
- Vóór elke nieuwe versie van de databank (na een update) komt er ook een kopie (de laatste 3 blijven).
- Is de databank **beschadigd** (bv. na een stroompanne), dan zet het programma het kapotte bestand opzij
  (`leeravontuur.db.beschadigd-…`) en zet het **vanzelf** de nieuwste goede reservekopie terug. Bij het starten
  meldt het dat. Je verliest dan hoogstens wat er na die kopie geoefend werd.
- Lukt bewaren helemaal niet (bv. een volle schijf), dan blijft het programma werken en meldt het in het hoofdmenu:
  "Je vooruitgang wordt nu niet bewaard".

## "Leeravontuur staat al open"

Twee keer tegelijk openen kan antwoorden doen verloren gaan. Daarom zie je dan in de terminal:

```text
Leeravontuur staat al open (sinds …).
Twee keer tegelijk openen kan antwoorden doen verloren gaan.
Toch starten? Typ j en Enter (anders stopt het):
```

Kijk of er nog een venster met Leeravontuur openstaat en sluit het. Is de computer gecrasht en staat het programma
zeker niet meer open? Typ `j`: een oud slot van een programma dat niet meer draait, neemt het programma gewoon over.

## "Oei, er ging iets mis"

Gaat er in een scherm toch iets fout, dan ziet het kind een vriendelijke melding en gaat het terug naar het
hoofdmenu. **De punten en antwoorden zijn bewaard.** De fout komt in het foutenlogboek.

### Het foutenlogboek

- `python3 oefeningen.py --fouten` toont de laatste 3 fouten en waar het bestand staat.
- Het ouderdeel meldt onderaan als er fouten in het logboek staan.
- Stuur het bestand `fouten.log` door aan wie het programma maakt; dan kan de fout opgelost worden.
- Om een fout zelf te zoeken: start met `--debug`; dan stopt het programma met de volledige melding.

## Het wachtwoord van het ouderdeel vergeten

`python3 oefeningen.py --wachtwoord-vergeten`, dan `JA` typen. Het wachtwoord is gewist; de gegevens van de
kinderen blijven. De volgende keer in het ouderdeel kies je een nieuw. Een vergeten **pincode** van een kind haal je
weg in het ouderdeel → Kinderen → Pincode.

## Het scherm ziet er raar uit

| Wat je ziet | Oplossing |
|---|---|
| "Het venster is te klein" | Maak het terminalvenster groter: minstens 80 × 24 tekens. |
| Vreemde tekens in plaats van lijnen of symbolen | Opties → Eenvoudige tekens → aan, of start met `--ascii`. |
| Kleuren zijn moeilijk te onderscheiden | Opties → Kleuren (kleurenblind, hoog contrast). |
| Klikken doet rare dingen, of je wil tekst kopiëren | Opties → Muis → uit, of start met `--geen-muis`. |
| Bij De klok verschijnt er geen klokvenster | Op Linux heeft Python soms het pakket voor vensters niet: `sudo apt install python3-tk` (Ubuntu, Debian) of `sudo dnf install python3-tkinter` (Fedora); op macOS met Homebrew `brew install python-tk`. Via ssh of zonder bureaublad kan het niet; dan tekent de terminal de klok zelf. |
| Het klokvenster is niet te zien (terminal op volledig scherm) | Druk `F2`: de klok komt in de terminal. Of zet de terminal niet op volledig scherm maar gemaximaliseerd: dan blijft het klokvenster rechtsboven zichtbaar. |
| Het klokvenster staat op een onhandige plek | Sleep het weg: de volgende keer komt het weer op die plek. |
| `Esc` reageert traag | Een terminal kan `Esc` even laten wachten; het programma zet dat zelf kort. Werkt het toch traag, gebruik dan de knoppen onderaan. |

## Nog iets anders?

Gebruik **Zeg het ons** in het programma, of geef de opmerking door aan wie het programma maakt, samen met
`fouten.log` en de versie (`python3 oefeningen.py --versie`).
