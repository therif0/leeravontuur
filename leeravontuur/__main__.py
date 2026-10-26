"""Leeravontuur starten: python3 -m leeravontuur (of python3 oefeningen.py)."""

import argparse
import os
import shutil
import sys
from pathlib import Path

os.environ.setdefault("ESCDELAY", "25")  # Esc meteen laten reageren (moet vóór curses starten)

from . import LICENTIE, MAKER, MOTTO, NAAM, VERSIE  # noqa: E402


def maak_parser():
    p = argparse.ArgumentParser(
        prog="oefeningen.py",
        description=f"{NAAM}: een gratis leerprogramma van {MAKER}. {MOTTO}.")
    p.add_argument("--kleurenblind", nargs="?", const="rood-groen", choices=["rood-groen", "blauw-geel"],
                   help="kleuren voor kleurenblindheid (standaard: rood-groen)")
    p.add_argument("--contrast", action="store_true", help="hoog contrast (zwart-wit)")
    p.add_argument("--geen-kleur", action="store_true", help="geen kleuren gebruiken")
    p.add_argument("--ascii", action="store_true", help="alleen eenvoudige tekens (voor oude terminals)")
    p.add_argument("--geen-muis", action="store_true", help="muis uitzetten (tekst selecteren werkt dan gewoon)")
    p.add_argument("--zonder-klokvenster", action="store_true",
                   help="de wijzerklok in de terminal tekenen, niet in een eigen venster")
    p.add_argument("--ouder", action="store_true", help="meteen naar het ouderdeel (rapporten, kinderen)")
    p.add_argument("--wachtwoord-vergeten", action="store_true",
                   help="het ouderwachtwoord wissen (de gegevens van de kinderen blijven bewaard)")
    p.add_argument("--snelkoppeling", action="store_true", help="menu-snelkoppeling maken (Linux)")
    p.add_argument("--fouten", action="store_true", help="de laatste fouten uit het foutenlogboek tonen")
    p.add_argument("--debug", action="store_true", help="bij een fout meteen stoppen met de volledige melding")
    p.add_argument("--test", action="store_true", help="de automatische tests uitvoeren")
    p.add_argument("--versie", action="store_true", help="versie tonen")
    return p


def lees_argumenten(argv):
    return maak_parser().parse_args(argv)


def snelkoppeling():
    if not sys.platform.startswith("linux"):
        print("Een menu-snelkoppeling maken kan voorlopig alleen op Linux.")
        return 1
    starter = Path(__file__).resolve().parent.parent / "oefeningen.py"
    starter.chmod(starter.stat().st_mode | 0o111)
    if shutil.which("konsole"):
        exec_regel, terminal = f'konsole --hide-menubar -e python3 "{starter}"', "false"
    else:
        exec_regel, terminal = f'python3 "{starter}"', "true"
    map_ = Path.home() / ".local" / "share" / "applications"
    map_.mkdir(parents=True, exist_ok=True)
    oud = map_ / "eenheden-oefenen.desktop"
    if oud.exists():
        oud.unlink()
    bestand = map_ / "leeravontuur.desktop"
    bestand.write_text(
        "[Desktop Entry]\nType=Application\nName=Leeravontuur\n"
        f"Comment=Gratis leerprogramma van {MAKER}\n"
        f"Exec={exec_regel}\nTerminal={terminal}\nIcon=accessories-calculator\n"
        "Categories=Education;\n", encoding="utf-8")
    print(f"Snelkoppeling gemaakt: {bestand}")
    print("Je vindt 'Leeravontuur' nu in het startmenu (bij Onderwijs/Education).")
    return 0


def wachtwoord_vergeten():
    from .kern.opslag import Opslag
    opslag = Opslag.open()
    if not opslag.ouder_wachtwoord():
        print("Er is nog geen ouderwachtwoord ingesteld.")
        return 0
    antwoord = input("Typ JA om het ouderwachtwoord te wissen (de gegevens blijven bewaard): ")
    if antwoord.strip().upper() != "JA":
        print("Er is niets veranderd.")
        return 1
    opslag.zet_ouder_wachtwoord(None)
    opslag.sluit()
    print("Het ouderwachtwoord is gewist. Bij de volgende keer in het ouderdeel kies je een nieuw.")
    return 0


def toon_fouten():
    from .kern import foutlog
    meldingen = foutlog.meldingen()
    if not meldingen:
        print("Er staan geen fouten in het logboek. Prima!")
        return 0
    for m in meldingen[-3:]:
        print(m)
        print()
    print(f"{len(meldingen)} {'melding' if len(meldingen) == 1 else 'meldingen'} in {foutlog.pad()}")
    print("Je kunt dit bestand doorsturen als er iets misloopt.")
    return 0


def draai_tests():
    import unittest
    map_ = Path(__file__).resolve().parent.parent / "tests"
    if not map_.is_dir():
        print("De testmap is niet meegeleverd.")
        return 1
    suite = unittest.defaultTestLoader.discover(str(map_), top_level_dir=str(map_.parent))
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if res.wasSuccessful() else 1


def main(argv=None):
    args = lees_argumenten(sys.argv[1:] if argv is None else argv)
    if args.versie:
        print(f"{NAAM} {VERSIE} · een gratis leerprogramma van {MAKER} · {LICENTIE}")
        return 0
    if args.test:
        return draai_tests()
    if args.snelkoppeling:
        return snelkoppeling()
    if args.wachtwoord_vergeten:
        return wachtwoord_vergeten()
    if args.fouten:
        return toon_fouten()
    if args.debug:
        os.environ["LEERAVONTUUR_DEBUG"] = "1"
    if os.environ.get("LEERAVONTUUR_ZAAD"):  # altijd dezelfde vragen (voor de schermafdrukken in de handleiding)
        import random
        random.seed(os.environ["LEERAVONTUUR_ZAAD"])

    import curses
    import locale

    from .kern import foutlog
    from .kern.opslag import Opslag
    from .terminal.app import App

    # argumenten gaan voor op de bewaarde instellingen (maar worden niet bewaard)
    voorrang = {}
    if args.kleurenblind:
        voorrang["thema"] = args.kleurenblind
    if args.contrast:
        voorrang["thema"] = "contrast"
    if args.geen_kleur:
        voorrang["thema"] = "geen-kleur"
    if args.ascii:
        voorrang["ascii"] = True
    if args.geen_muis:
        voorrang["muis"] = False
    if args.zonder_klokvenster:
        voorrang["klokvenster"] = False

    from .kern import slot
    al_open = slot.bezet()
    if al_open:
        print(f"{NAAM} staat al open ({al_open}).")
        print("Twee keer tegelijk openen kan antwoorden doen verloren gaan.")
        try:
            antwoord = input("Toch starten? Typ j en Enter (anders stopt het): ") if sys.stdin.isatty() else "j"
        except EOFError:
            antwoord = ""
        if antwoord.strip().lower() not in ("j", "ja"):
            return 0
    slot.neem()
    opslag = Opslag.open()
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:  # een onbekende taalinstelling: dan gewoon zonder
        pass
    houder = {}

    def draai(win):
        houder["app"] = app = App(win, opslag, voorrang)
        app.start(ouder=args.ouder)

    mislukt = None
    try:
        curses.wrapper(draai)
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:  # laatste vangnet: geen Python-melding voor het kind, wel een logboek
        if args.debug:
            raise
        foutlog.schrijf("buiten het menu", e)
        mislukt = e
    app = houder.get("app")
    if app:
        app.zet_klokvenster(False)
    groet = "Tot de volgende keer!"
    if app and app.kind:
        groet = f"Tot de volgende keer, {app.kind.naam}!"
        n, j = app.vandaag()
        if n:
            groet += f" Vandaag: {j} van {n} juist."
    opslag.sluit()
    print(groet)
    if mislukt is not None:
        print("Oei, er ging iets mis en het programma moest stoppen. Je antwoorden zijn bewaard.")
        print(f"De fout staat in {foutlog.pad()} (bekijk ze met --fouten).")
    if opslag.probleem:
        print(opslag.probleem)
    print(f"{NAAM} · een gratis leerprogramma van {MAKER}")
    return 1 if mislukt is not None else 0


if __name__ == "__main__":
    sys.exit(main())
