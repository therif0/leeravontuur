# oefeningenImrane

Een terminalprogramma om eenheden te leren omzetten:

- **Massa:** t, kg, hg, dag, g, dg, cg, mg
- **Lengte:** km, hm, dam, m, dm, cm, mm

Het is één bestand (`oefeningen.py`) en gebruikt alleen Python 3. Dat staat standaard op Fedora, dus je hoeft niets te installeren.

## Starten

```bash
git clone https://github.com/therif0/oefeningenImrane.git
cd oefeningenImrane
python3 oefeningen.py
```

Of maak het bestand uitvoerbaar en start het rechtstreeks:

```bash
chmod +x oefeningen.py
./oefeningen.py
```

Het venster moet minstens 80×24 tekens groot zijn. Een gewoon Konsole-venster is groot genoeg.

### Snelkoppeling in het startmenu (optioneel)

```bash
python3 oefeningen.py --snelkoppeling
```

Daarna staat **Eenheden oefenen** in het startmenu (bij Onderwijs). Het opent in Konsole.

## Wat zit erin?

1. **Vrij oefenen**: zoveel vragen als je wil. Met `?` krijg je een tip, en na elk antwoord zie je de volledige uitleg.
2. **Reeks van 10**: 10 vragen. Daarna krijg je je score en de uitleg bij elke fout.
3. **Tabel-oefening**: de som staat bovenaan. Je vult de eenhedentabel in, één cijfer per vakje (met `Tab` ga je naar het volgende vakje), en daarna typ je je antwoord. Bij het nakijken worden de vakjes groen of rood en zie je de juiste tabel eronder.
4. **Spiekbrief**: hoe de tabel werkt, met voorbeelden.

Je kiest altijd eerst welke eenheden je oefent (massa, lengte, allebei of zelf aanduiden) en hoe moeilijk het mag zijn (makkelijk, normaal of moeilijk).

Kommagetallen typ je met een komma, bijvoorbeeld `0,25`.

## Zelftest

```bash
python3 oefeningen.py --test
```
