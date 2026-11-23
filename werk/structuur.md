# Leeravontuur structuur: een kaart van de hele code

**Status:** gebouwd, wacht op het nakijken door de vader (23/11/2026, "actie" van de vader). Branch `structuur`, één pull request, geen versie.

## Waarom
De vader wil de code van Claude tot in detail kunnen nakijken: elk bestand, elke klasse, elke functie en wie wie
aanroept, in een vaste structuur, zonder dat hij iets hoeft te vragen of in te vullen.

## Gekozen (de vader, 23/11)
- Een map **`leeravontuur structuur/`** in de repo (met een spatie, zoals gevraagd) met voor **elk bestand een
  JSON-tegenhanger** op dezelfde plaats: `<pad>.json` (bv. `leeravontuur/kern/klad.py.json`).
- **Claude schrijft alle uitleg zelf, met de hand, in één keer.** Niet: een script dat de uitleg maakt.
- **Alle bestanden behalve de afbeeldingen** (132 svg, 1 png) en LICENSE: 227 bestanden. De afbeeldingen staan in
  `index.json` als "gegenereerd, niet uitgelegd".
- **Engels** (de sleutels ook). Dit is een uitzondering op "documenten in het Vlaams": de kaart is voor Claude en voor
  wie de code nakijkt.
- **Geen onderhoudsscript en geen test**: de kaart wordt opnieuw gemaakt als de vader het vraagt.

## Hoe
- De **feiten** (regelnummers, parameters, wie wie aanroept) haalt een wegwerphulpje uit de syntaxisboom van elk
  bestand, zodat ze niet uit het geheugen getypt worden. Het hulpje staat niet in de repo. De **uitleg** schrijft
  Claude na het lezen van de code.
- Een aanroep via een tabel of `getattr` kan niet gevolgd worden: die staan in `dynamic-dispatch.json`.
- De standaard staat in `schema.json`; hoe je de kaart leest in `leeravontuur structuur/README.md`.

## Fasen (een tussentijdse commit per laag)
1. De opzet: schema, README, dit bestand, een regel in CLAUDE.md.
2. `kern/` (46) · 3. `terminal/` en `venster/` (41) · 4. de scripts in de root, `docs/tools`, `tests/` (37)
· 5. `inhoud/` (49) en de markdown (38) en de scripts en config.
6. `index.json`, `dynamic-dispatch.json`, een controle (elk bestand heeft een tegenhanger, elk JSON-bestand klopt met
   het schema, elke functie en klasse staat erin, elk doel van een aanroep bestaat), de pull request.

## Grenzen
De uitleg is Claude's lezing van de code en kan fouten bevatten: de vader kijkt na. De kaart beschrijft `main` op het
moment van de commit waarvan ze gemaakt is.

## Gecontroleerd
Een controle (niet in de repo, op verzoek van de vader geen onderhoudsscript) bewees: elk van de 227 bestanden heeft een
tegenhanger; elke tegenhanger klopt met `schema.json`; elke functie, methode en klasse uit de syntaxisboom staat erin
met de juiste regels; elke aanroep verwijst naar iets dat bestaat en heeft zijn spiegel (`called_by`); de sha256 van elk
bestand klopt met het bestand op `main` (6f33a3b). Tien willekeurige functies zijn met de hand naast de code gelegd; drie
uitleggen van tests werden daarna scherper gemaakt.

## Gevonden tijdens het in kaart brengen (niets aangepast, de vader beslist)
1. `kern/selectie.py` `kies()` wordt nergens aangeroepen (dode code).
2. `kern/wiskunde/cijferen.py` `_Cijferen.tip` zegt "Druk ? ... voor hulp bij die kolom", maar de hulptoets is F1
   (`terminal/rooster.py`): een kind kan een verkeerde tekst zien.
3. `kern/wiskunde/hoofdrekenen.py` `_plaats(n, k)` gebruikt de parameter `n` niet.
4. Dubbel werk: `getallen.PLAATSEN` en `modellen.PLAATSEN` (andere vorm); `cijferen._decimalen` en `getal.decimalen`; de
   methode `spiekbrief` staat in elke onderwerpklasse van een bestand.
5. `kern/wiskunde/vraagstukken.py` `stel_samen` heeft een parameter `zin_keuze` die niet gelezen wordt.
6. `terminal/scherm.py` en `terminal/indeling.py` hebben elk hun eigen `MIN_B`/`MIN_H` (80 × 24).
7. `README.md` zegt nog "versie 0.20, bèta" (de versie is 0.28.0).
8. `terminal/schermen/winkel.py` `AvatarSchermen.melding` heeft een parameter `gezicht` die niet gebruikt wordt.
