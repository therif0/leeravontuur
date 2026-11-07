# Leeravontuur: to-do (stand 7/11, na 0.23.1)

De richting en de volgorde staan in [koers.md](koers.md). Nieuwe ideeën: een fout die het kind merkt = meteen; past
in de huidige periode = in de rij; al de rest = hier geparkeerd.

## Voor de vader
- [ ] Tags + releases maken, tekst uit CHANGELOG: op GitHub is de laatste tag 0.20.2, dus nog 0.20.3 tot en met
      0.23.0 (en 0.23.1 na het samenvoegen).
- [ ] 0.22.0, 0.23.0 en 0.23.1 testen met `docs/testlijst.md` (op een kopie, `LEERAVONTUUR_DATA`).
- [ ] Issues #24 (logboek) en #18 (plaatswaarden) sluiten als ze goed zijn (gebouwd in 0.22.0 en 0.21.4).

## Volgende bouwstap (pas na akkoord)
- [x] 0.23.1: het appelvraagstuk (wat overblijft na twee delen) + "waar komt dit getal vandaan?" in het klad
- [ ] 0.23.2: slot op Stoppen (het plan staat hieronder)
  - ouderpin 4 cijfers ("Wachtwoord en ouderpin"), per kind "Stoppen op slot" (ook vooraf), 🔒 in de lijst
  - slotscherm met pin; herstart meteen bij dat kind; Ctrl-C genegeerd; openen via `--ouder`
- [ ] Gemengd oefenen: eerst een inventaris en een voorstel (wat het kind ziet, hoe er gekozen wordt, de status
      "fris houden" in het rapport, Maten in het gedeelde oefenscherm); bouwen na akkoord. Daarna wiskunde bevriezen.

## Geparkeerd: vragen voor later
- [ ] Dagtaak: ook in schoolweken, in een lichtere vorm (bv. 15 minuten), om de gewoonte te bouwen? Of alleen in de
      vakanties?
- [ ] Begrijpend lezen: wie schrijft de leesteksten? (Claude schrijft, de ouders kijken na; of teksten van school)

## Geparkeerd: wiskunde v2 (met feedback, na de bevriezing)
- [ ] Groep C wacht: #19 (QoL vermenigvuldigen), #20c (spiekbrieven, rest), #17 (staartdeling)
- [ ] Geparkeerd (`docs/werkwijzen.md`): Ctrl-C, Enter op het resultaat, toets q, Maten volgens de vaste werkwijze,
      lange voetregels, de tip bij "Hoe laat kom je aan?"
- [ ] Handleidingproject (volledige test + handleiding kind, ouder, coach; schermafdrukken tonen nog 0.19)
- [ ] Hoofdmenu: nog plaats voor 1 keuze; Gemengd, Examens, Dagtaak, Frans en Avontuur komen eraan = eerst samen een
      oplossing kiezen (vóór Gemengd oefenen)

---

## Plan voor 0.23.2: het slot op Stoppen
Kinderen mogen niet zomaar van account wisselen, dus kan de ouder per kind een **slot op Stoppen** zetten, dat alleen
open gaat met een **ouderpin van 4 cijfers**. Staat het slot op, dan start het programma meteen bij dat kind en doet
Ctrl-C niets.

1. **Ouderpin** (4 cijfers, `kern/wachtwoord.maak` met `PIN_ITERATIES`, in `opslag.algemeen("ouder_pin")`):
   in het ouderdeel wordt "Wachtwoord wijzigen" → "Wachtwoord en ouderpin".
2. **Per kind** (`Instellingen.stoppen_slot: bool = False`, in de JSON: geen migratie): Ouders › Kinderen › kind ›
   "Stoppen op slot". Bij het aanzetten zonder ouderpin wordt eerst de pin gevraagd.
3. **Het slotscherm**: Stoppen of Esc met het slot op → "Stoppen staat op slot. Vraag een ouder of leerkracht."
   + de ouderpin (`Scherm.invoer`, verborgen, cijfers). Juist → het titelscherm; Esc → terug naar het hoofdmenu;
   3× fout → terug.
4. **Herstarten**: staat het slot op bij een kind, dan start het programma meteen bij dat kind (geen titelscherm,
   geen "Wie ben jij?"; bij meer kinderen met een slot: het laatst gekozen kind daarvan). De ouder komt erin met
   `--ouder` (het startargument bestaat al) of via het slotscherm.
5. **De ouder beslist vooraf of achteraf**: in het ouderdeel, ook via `--ouder`, kan de ouder
   - het slot **openen** (uitzetten) voor een kind dat vastzit;
   - het slot **vooraf** aanzetten voor een bepaald kind, ook als dat kind nu niet aan het oefenen is (bv. later om
     een examen voor te bereiden). Bij de volgende start gaat het programma dan meteen naar dat kind.

   Dat is dezelfde instelling ("Stoppen op slot" bij Ouders › Kinderen › kind), en in de lijst van de kinderen staat
   bij elk kind "🔒 op slot" (in de eenvoudige tekens: "[slot]").
6. **Ctrl-C** doet niets zolang een kind met slot actief is (`signal.SIGINT` genegeerd, ook op Windows). Het
   venster sluiten kan het programma niet tegenhouden: daarom start het opnieuw bij hetzelfde kind.
7. Tests (slotscherm, pin juist/fout/Esc, herstart bij het kind, vooraf op slot zetten en via `--ouder` openen,
   🔒 in de lijst), testlijst, CHANGELOG, VERSIE 0.23.2. Het 🔒-teken (of een ander) komt in `terminal/tekens.py`.

**Nakijken:** volledige suite + lange aapjestest (de aap mag niet vastlopen in het slotscherm: een test met slot
aan); tmux 80×24 op een kopie van de gegevens: slot aan bij de ouder, Stoppen → pin, herstart → meteen het kind,
Ctrl-C, en het slot openen met `--ouder`. Een PR, CI groen, melden en stoppen.
