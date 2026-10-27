# Werkwijzen: inventaris (stap 1)

Aanleiding: #33 kwam terug. Een klik op de broodkruimel midden in een vraag verlaat de oefening zonder te vragen.
De vader vroeg een klein project om de werkwijzen (de wegen door het programma) na te kijken.
Dit is **stap 1: de inventaris**. Er is nog niets veranderd. Per scherm staat hieronder:
- hoe je erin komt;
- elke manier om eruit te gaan;
- wat er bewaard wordt en wat verloren gaat;
- waar je daarna terechtkomt.

Gevonden in de code (versie 0.21.4) en nagekeken met een scan over alle oefeningen.

Tekens: **✔** in orde · **✘** probleem (een kind merkt het) · **?** een keuze voor de vader.

---

## 1. Eén vraag verlaten (vóór het nakijken)

De vraag is nog niet nagekeken. Wat het kind getypt heeft (antwoord en klad) is nog nergens bewaard.

| Uitgang | Oefenaar (alle onderwerpen) | Maten (vrij, reeks, tabel) | Snelrekenen (60 s, 20 sommen) |
|---|---|---|---|
| **Esc** | ✔ kader "Wil je stoppen?" (#33) | ✔ kader | ✔ kader, de klok staat stil |
| **Klik op de broodkruimel** | ✘ meteen weg, zonder vraag | ✘ meteen weg | ✘ meteen weg, **zonder uitslag en zonder bonus/record** |
| **Kruimel in de spiekbrief vanuit een vraag** | ✘ meteen weg (Esc gaat wel netjes terug naar de vraag) | ✘ idem | (geen spiekbrief) |
| **Ctrl-C** | ? het programma stopt meteen | ? idem | ? idem |
| **Het venster sluiten** (kruisje) | ✔ wat al nagekeken is, staat in de databank | ✔ idem | ✔ idem |
| **Het klokvenster sluiten** of F2 | ✔ de klok komt in de terminal, de vraag blijft | – | – |
| **Een fout in het programma** (vangnet) | ✔ "Oei, er ging iets mis", terug naar het hoofdmenu | ✔ idem | ✔ idem |

- [ ] **De oorzaak van ✘:** de vraag "Wil je stoppen?" hangt aan de **Esc-toets**, apart in 4 schermen
  (`terminal/oefenaar.py`, 2× `schermen/eenheden.py`, `schermen/snelrekenen.py`).
  Een klik op de broodkruimel komt daar niet langs. `Scherm.toets` gooit meteen `TerugNaar`, en de menu's vangen
  die op. Elk nieuw oefenscherm moet het kader ook opnieuw zelf inbouwen.
- [ ] **Ctrl-C** (`__main__.py`): het programma stopt zonder vraag. Niets nagekeken gaat verloren, wel wat er getypt
  stond. **?** Ook hier het kader?

## 2. Na het nakijken, en tussen de vragen

| Wat | Nu | |
|---|---|---|
| Esc na het nakijken, **vrij oefenen** | stopt meteen, daarna "Je had 2 fouten. Nog eens proberen?" | ✔ |
| Esc na het nakijken, **in een reeks** (bv. vraag 5 van 10) | stopt de hele reeks meteen: **geen resultaat, geen uitleg bij de fouten, geen "fouten opnieuw"** | ✘ |
| Esc (bevestigd) midden in een reeks | idem: de antwoorden zijn bewaard, maar het kind ziet geen resultaat | ✘ |
| Enter op het **Resultaat** van een reeks | start meteen een **nieuwe reeks** van 10 | ? |
| Esc op het Resultaat | terug naar het menu, op hetzelfde onderwerp | ✔ |
| Herhalen: weg via de broodkruimel | geen samenvatting ("x juist, y komen morgen terug") | ✘ (klein) |
| Vrij oefenen: weg via de broodkruimel | de vraag "Je had 2 fouten, nog eens?" valt weg | ✘ (klein) |

- [ ] **?** Een onderbroken reeks toont het resultaat van wat al gedaan is ("Je stopte na 5 vragen: 4 juist", met
  de uitleg bij de fout en F = fouten opnieuw). Of blijft het zoals nu (meteen naar het menu)?
- [ ] **?** Enter op het resultaat: zo laten (snel verder oefenen), of moet "nieuwe reeks" een eigen toets krijgen
  (N, zoals nu al kan), met Enter = terug naar het menu?

## 3. Waar je terechtkomt

| Van | Naar | |
|---|---|---|
| Een oefening, gestart uit een menu | terug in het domeinmenu, **op hetzelfde onderwerp** | ✔ |
| Een oefening, gestart met **▶ Verder** | terug in het hoofdmenu | ✔ (zo gekozen) |
| Klik op de broodkruimel | het menu dat je aanklikt | ✔ (maar zie §1) |
| Spiekbrief vanuit een vraag, Esc | terug naar dezelfde vraag, alles staat er nog | ✔ |
| Spiekbrief uit het menu (S), Esc | terug op hetzelfde onderwerp | ✔ |
| **Esc in het hoofdmenu** | **het programma stopt meteen** ("Tot de volgende keer") | ✘ |
| Esc op het startscherm of in "Wie ben jij?" | het programma stopt | ✔ (er is nog niets begonnen) |
| Ouderdeel, 10 minuten niets gedaan | "vergrendeld", terug naar "Wie ben jij?" | ✔ |

- [ ] **Esc in het hoofdmenu:** een kind dat een paar keer te veel Esc drukt (om "terug" te gaan), zit plots buiten
  het programma. Dat overkwam mij ook bij het testen in tmux. **?** Een kader "Wil je stoppen met Leeravontuur?"
  (Nee gekozen), net als bij een vraag?

## 4. Dezelfde werkwijze overal? (lees, klad, antwoord)

De afspraak (CLAUDE.md) is dat elke oefening op dezelfde manier werkt: klad (`Tab`), `?` = tips en daarna de
spiekbrief, één tweede kans, "Zo kan het:" en Esc met een kader.

| | Klad | `?` tips → spiekbrief | Tweede kans | "Zo kan het:" + jouw klad |
|---|---|---|---|---|
| Oefenaar: vrij en reeks | ✔ | ✔ | ✔ (niet bij ja/nee, keuze …: zo bedoeld) | ✔ |
| Vraagstukken (4 stappen) | ✔ | ✔ (4 tips) | ✔ | ✔ |
| Maten, vrij oefenen | ✘ geen | ✔ | ✘ geen | ✔ de regel en de tabel (zonder klad) |
| Maten, reeks van 10 | ✘ geen | ✘ **geen tip** (geen `?` in de voetregel) | ✘ geen | ✔ de regel (kort) |
| Maten, tabel-oefening | (de tabel is het klad) | ✘ geen | ✘ geen | ✔ de juiste tabel |
| Snelrekenen | – | – (snelheid: zo bedoeld) | – | – |

- [ ] **?** Maten heeft nog een eigen scherm (vanwege de tabel) en volgt de vaste werkwijze maar half. Gelijk
  trekken met de Oefenaar is een **groter werk** (een eigen fase, later). Klein en meteen kan: `?` ook in de reeks.

## 5. Voetregels die niet passen (scan over elke oefening)

Een knop die niet in 80 tekens past, valt **helemaal weg**. Bij al deze voetregels valt daardoor **[Esc] stoppen**
weg. Esc werkt nog wel, maar het kind ziet de knop niet.

| Waar | Lengte (max 78) | Sinds |
|---|---|---|
| Vraagstuk, stap 1 Lees: `[Tab] volgende stap [Spatie] aanduiden [?/F1] tip (4 over) [Enter] ok [Esc] stoppen` | 87 | al lang |
| Vraagstuk, "Gevraagd" kiezen (`[Spatie] kiezen`) | 84 | al lang |
| Getallenlijn na de laatste tip (`… [Enter] hier! [?/F1] spiekbrief [Esc] stoppen`) | 85 | **0.21.3 (mijn fout)** |
| Klad met focus na de laatste tip (`[Tab] naar je antwoord [Enter] regel nakijken [?/F1] spiekbrief …`) | 80 | **0.21.3 (mijn fout)** |

- [ ] Inkorten, en **een test die elke voetregel nakijkt** (de scan als test), zodat dit niet meer terugkomt.

## 6. Kleine dingen die erbij horen

- [ ] De toets **q** werkt als "terug" in sommige schermen (spiekbrief, winkel, kast), in andere niet. Dat is geen
  probleem, wel ongelijk. **?** Overal weg, of overal (behalve waar je typt)?
- [ ] Maten-tabel: de knop heet `[Esc] stop`, elders overal `[Esc] stoppen`.
- [ ] Tijd, "Hoe laat kom je aan?": de tip zegt "tel eerst de uren", de uitwerking doet eerst de minuten (al eerder
  gemeld).

---

## Voorstel: de fasen

**Fase 1: één bewaker voor "weggaan" (#33, opnieuw)**
- Een oefenscherm meldt zich bij `Scherm` als *bezig* zolang de vraag niet nagekeken is.
  `Scherm.toets` vangt dan **elke** uitgang op met hetzelfde kader: Esc, een klik op de broodkruimel, ook vanuit de
  spiekbrief, en later elke nieuwe uitgang.
- De 4 losse Esc-controles verdwijnen. Een nieuw oefenscherm is vanzelf beschermd.
- Snelrekenen via de kruimel geeft dan ook de uitslag en de bonus.
- In dezelfde fase: de voetregels van §5 (met de test).
- Tests die elke uitgang uit elke soort oefening proberen.

**Fase 2: de keuzes van de vader uit §1–§3** (alleen wat hij kiest)
- Esc in het hoofdmenu → kader.
- Ctrl-C → kader.
- Het resultaat van een onderbroken reeks.
- Enter op het resultaat.
- De kleine dingen van §6.

**Later, een eigen project: Maten volgens de vaste werkwijze** (§4: klad, tips in de reeks, tweede kans). Pas na
een voorstel met mockups.

## Wat de vader koos (27/10)

1. **Fase 1: bouwen.** Esc is de natuurlijke manier om te stoppen. De te lange voetregels (§5) **blijven zoals ze
   zijn**: als `[Esc] stoppen` er niet bij past, is dat geen probleem.
2. **Esc in het hoofdmenu: eerst vragen** (fase 2).
3. Ctrl-C: **geparkeerd**.
4. **Een onderbroken reeks: het resultaat tonen** van wat gedaan is (fase 2).
5. Enter op het resultaat: **geparkeerd**.
6. De toets q: **geparkeerd**.
7. Maten (`?` in de reeks, de vaste werkwijze): **geparkeerd**.
