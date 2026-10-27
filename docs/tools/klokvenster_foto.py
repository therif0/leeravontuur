"""Een echte schermafdruk van het klokvenster naast een terminal op het hele scherm (voor de handleiding).

Linux, met Xvfb, openbox, xterm, xdotool en ImageMagick (import, convert), en een Python met tkinter:
    python3 docs/tools/klokvenster_foto.py [python-met-tkinter]
Maakt docs/handleiding/beelden/klokvenster-scherm.png.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent.parent
BEELD = WORTEL / "docs" / "handleiding" / "beelden" / "klokvenster-scherm.png"
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main(python):
    from schermafdrukken import maak_voorbeeld

    nodig = ["Xvfb", "openbox", "xterm", "xdotool", "import", "convert"]
    if any(shutil.which(p) is None for p in nodig):
        print("Nodig:", ", ".join(nodig))
        return 1
    scherm = ":93"
    env = dict(os.environ, DISPLAY=scherm)
    data = Path(tempfile.mkdtemp(prefix="leeravontuur-foto-"))
    maak_voorbeeld(data)
    xvfb = subprocess.Popen(["Xvfb", scherm, "-screen", "0", "1366x768x24"], stderr=subprocess.DEVNULL)
    time.sleep(1)
    wm = subprocess.Popen(["openbox"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    term = subprocess.Popen(
        ["xterm", "-maximized", "-bg", "#1e1e1e", "-fg", "#d4d4d4", "-fa", "DejaVu Sans Mono", "-fs", "11",
         "-title", "terminal", "-e",
         f"cd {WORTEL} && {python} leeravontuur.py"],
        env=dict(env, LEERAVONTUUR_DATA=str(data), LEERAVONTUUR_ZAAD="klokvenster-scherm"))
    try:
        time.sleep(3)
        for t in ["Return", "Return", "2", "1", "7", "4", "1", "2"]:  # Imrane → Wiskunde → De klok → vrij, normaal
            subprocess.run(["xdotool", "key", t], env=env)
            time.sleep(0.6)
        time.sleep(2.5)
        ruw = data / "scherm.png"
        subprocess.run(["import", "-display", scherm, "-window", "root", str(ruw)], env=env, check=True)
        subprocess.run(["convert", str(ruw), "-resize", "70%", "+dither", "-colors", "96", str(BEELD)], check=True)
        print("  ", BEELD.relative_to(WORTEL))
    finally:
        term.terminate()
        wm.terminate()
        xvfb.terminate()
        shutil.rmtree(data, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else sys.executable))
