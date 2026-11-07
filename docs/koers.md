# De koers: waar we naartoe gaan

Eén pagina om altijd in de juiste richting te werken. De details staan in [plan.md](plan.md), wat er nu openstaat in
[todo.md](todo.md). De vader beslist; deze pagina wordt bijgestuurd op het einde van elke periode.

## Het doel
**Twee doelen, even zwaar, om beurten:**
- 🧒 **de zoon:** wat hij dit schooljaar nodig heeft, en dat hij niet vergeet wat hij al kan;
- 🌍 **het product:** een gratis leerprogramma dat ook andere Vlaamse kinderen kunnen gebruiken (Taal, Frans,
  coach, publicatie).

Elke periode hieronder dient vooral één van de twee. Zo krijgt elk doel zijn beurt.

**Niet vergeten.** Wat een kind niet traint, vergeet het. Daarom is **gemengd oefenen** de basis van wat komt:
korte reeksen met vragen uit alle (of gekozen) onderwerpen, met meer gewicht voor wat lang niet geoefend werd.

## De vaste datum
**1 september 2027:** het 6de leerjaar. Dan schuiven de niveaus mee ("Heel moeilijk" = 2de middelbaar) en moet de
schooljaarwissel werken. Die datum verschuift niet; al de rest kan schuiven.

## De periodes
| Periode | Voor | Wat |
|---|---|---|
| tot november 2026 | 🧒 | ✔ 0.23.2 het slot op Stoppen → ✔ 0.24.0 Gemengd oefenen (ook "fris houden" in het rapport) → **wiskunde bevroren**: daarna alleen nog fouten die het kind merkt |
| nu → Pasen 2027 | 🌍 | **Taal** (het plan: [taal.md](taal.md)): eerst **zinsontleding en woordsoorten** (de vader, 7/11), dan **werkwoordspelling**, met de woordenlijsten |
| Pasen → juni 2027 | 🧒 | **Examens** (de ouder stelt samen, het kind maakt het zonder hulp), klaar vóór de examens van juni · **rekenpuzzels** ("lolly + lolly = ijsje …") |
| juni → 1 juli 2027 | 🧒 | **Dagtaak / vakantiewerk**: elke dag een taak van 30 à 60 minuten met pauzes en een gekozen rustdag; gemengd met spelletjes (woordzoeker, foutenzoeker, rekenpuzzels) en **begrijpend lezen** (een tekst met meerkeuzevragen) |
| juli → 1 september 2027 | 🌍 🧒 | **Schooljaarwissel + leerlijnen tot 2de middelbaar** (de vaste datum) · wiskunde v2 uit de feedback van het jaar (schuift na september als het krap wordt) |
| later | 🌍 | Taal 2–4 (spelling, zinsontleding, woordenschat en lezen), dictee, Frans, coach, Avontuur, handleidingproject, publicatie |

## De bouwstenen (waarom deze volgorde)
**Gemengd oefenen → Examens → Dagtaak.** Elke stap bouwt op de vorige:
- Elk onderwerp geeft op dezelfde manier een nieuwe vraag (`Onderwerp.maak(jaar)`, alle onderwerpen in
  `kern/catalogus.py`), en één oefenscherm speelt een gemengde lijst (`Oefenaar.speel`, zoals Herhalen al doet).
- Een **examen** = een gemengde reeks uit gekozen onderwerpen, zonder hulp, met het resultaat bewaard.
- Een **dagtaak** = een gemengde reeks + een spelletje + een leestekst, elke dag, met een kalender.
- Nog nodig: Maten (de eenhedentabel) in het gedeelde oefenscherm, schakelaars "zonder hulp" (geen tips, geen
  tweede kans) en een plaats in de databank voor examens (een migratie).

## De regel voor nieuwe ideeën
1. **Een fout die het kind merkt** → meteen (een eigen branch en PR).
2. **Past in de huidige periode** → in de rij.
3. **Al de rest** → geparkeerd in [todo.md](todo.md).

Op het einde van elke periode kijken we samen naar deze pagina en de parkeerlijst, en sturen we bij.
