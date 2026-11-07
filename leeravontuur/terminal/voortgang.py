"""De voortgang bovenaan een reeks ("Vraag 3 van 20  ● ● ◉ ○ …  Punten: 2"), voor elk oefenscherm dezelfde."""


def teken(s, y, nr, totaal, resultaten, soort):
    """Een bolletje per vraag (bij meer dan 10 vragen dichter bij elkaar, zodat het altijd past)."""
    s.put(y, 4, f"Vraag {nr + 1} van {totaal}", "bold")
    stap = 2 if totaal <= 10 else 1
    for i in range(min(totaal, 20)):
        if i < len(resultaten):
            ch, rol = "●", "goed" if resultaten[i]["goed"] else "fout"
        else:
            ch, rol = ("◉", "accent") if i == nr else ("○", "dim")
        s.put(y, 22 + stap * i, ch, rol)
    s.put(y, 46, f"Punten: {sum(r['goed'] for r in resultaten)}", "bold")
    s.put(y + 1, 4, soort, "dim")
