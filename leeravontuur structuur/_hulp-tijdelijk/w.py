import json
from pathlib import Path
PROSE = Path(__file__).parent / "prose"
def W(path, purpose, details, f=None, c=None, k=None, r=None, **extra):
    d = {"purpose": purpose, "details": details}
    if f: d["functions"] = f
    if c: d["classes"] = c
    if k: d["constants"] = k
    if r: d["registries"] = r
    d.update(extra)
    p = PROSE / (path + ".json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
