#!/usr/bin/env python3
"""Throwaway: merge Claude's prose (prose/<path>.json) with AST facts into the committed map."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import facts as F

PROSE = Path(__file__).parent / "prose"
ORDER = {
    "python": ["schema", "path", "kind", "layer", "lines", "source_sha256", "purpose", "details", "module_docstring", "imports", "imported_by",
               "module_calls", "constants", "registries", "classes", "functions"],
    "json": ["schema", "path", "kind", "layer", "lines", "source_sha256", "purpose", "details", "keys", "shape", "read_by", "field_notes"],
    "markdown": ["schema", "path", "kind", "layer", "lines", "source_sha256", "purpose", "details", "summary", "headings", "links", "referenced_by", "words"],
    "script": ["schema", "path", "kind", "layer", "lines", "source_sha256", "purpose", "details"],
}
ORDER["test"], ORDER["config"] = ORDER["python"], ORDER["script"]


def _scalar(v):
    return v is None or isinstance(v, (str, int, float, bool))


def _flat(v):
    if _scalar(v):
        return True
    if isinstance(v, list):
        return all(_scalar(x) for x in v)
    if isinstance(v, dict):
        return all(_scalar(x) or (isinstance(x, list) and all(_scalar(y) for y in x)) for x in v.values())
    return False


def dump(v, ind=0):
    """Readable JSON: short flat lists and flat objects stay on one line, everything else is indented by one space."""
    pad = " " * (ind + 1)
    if _scalar(v):
        return json.dumps(v, ensure_ascii=False)
    one = json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        if not v:
            return "[]"
        if _flat(v) and len(one) + ind <= 110 and all(_scalar(x) for x in v):
            return one
        return "[\n" + ",\n".join(pad + dump(x, ind + 1) for x in v) + "\n" + " " * ind + "]"
    if not v:
        return "{}"
    if _flat(v) and len(one) + ind <= 110:
        return one
    return "{\n" + ",\n".join(pad + json.dumps(k, ensure_ascii=False) + ": " + dump(x, ind + 1) for k, x in v.items()) + "\n" + " " * ind + "}"


def out_path(path):
    return F.OUT / (path + ".json")


def merge(path):
    f = F.file_facts(path)
    pf = PROSE / (path + ".json")
    if not pf.exists():
        return [f"{path}: no prose file"]
    pr = json.loads(pf.read_text(encoding="utf-8"))
    err = []
    for k in ("purpose", "details"):
        if not str(pr.get(k, "")).strip():
            err.append(f"{path}: missing {k}")
        f[k] = pr.get(k, "")
    k = f["kind"]
    if k in ("python", "test"):
        fx, cx, kx = pr.get("functions", {}), pr.get("classes", {}), pr.get("constants", {})
        seen_f, seen_c = set(), set()
        def put(entries):
            for e in entries:
                seen_f.add(e["qualname"])
                e["explanation"] = fx.get(e["qualname"], "")
                if not e["explanation"].strip():
                    err.append(f"{path}: missing function {e['qualname']}")
        put(f["functions"])
        for c in f["classes"]:
            seen_c.add(c["qualname"])
            c["explanation"] = cx.get(c["qualname"], "")
            if not c["explanation"].strip():
                err.append(f"{path}: missing class {c['qualname']}")
            put(c["methods"])
        for c in f["constants"]:
            c["explanation"] = kx.get(c["name"], "")
        err += [f"{path}: unknown function key {x}" for x in fx if x not in seen_f]
        err += [f"{path}: unknown class key {x}" for x in cx if x not in seen_c]
        err += [f"{path}: unknown constant key {x}" for x in kx if x not in {c['name'] for c in f['constants']}]
        f["registries"] = pr.get("registries", [])
    elif k == "markdown":
        f["summary"] = pr.get("summary", "")
        if not f["summary"].strip():
            err.append(f"{path}: missing summary")
    elif k == "json":
        f["read_by"] = sorted(set(f["read_by"]) | set(pr.get("read_by_extra", [])))
        f["field_notes"] = [{"key": a, "explanation": b} for a, b in pr.get("fields", {}).items()]
    if err:
        return err
    order = ORDER[k]
    final = {key: f[key] for key in order}
    assert set(final) == set(f), (path, set(f) ^ set(final))
    op = out_path(path)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(dump(final) + "\n", encoding="utf-8")
    return []


if __name__ == "__main__":
    F.load_all()
    args = sys.argv[1:]
    todo = F.explained(F.tracked())
    if args == ["status"]:
        have = [p for p in todo if (PROSE / (p + ".json")).exists()]
        done = [p for p in todo if out_path(p).exists()]
        print(f"explained files: {len(todo)}  prose written: {len(have)}  merged: {len(done)}")
        miss = [p for p in todo if p not in done]
        by = {}
        for p in miss:
            by.setdefault(F.layer_of(p), []).append(p)
        for lay, ps in by.items():
            print(f"  not merged [{lay}]: {len(ps)}")
        sys.exit(0)
    paths = todo if args == ["all"] else [a for a in args if not a.startswith("--")]
    if args and args[0] == "ready":
        paths = [p for p in todo if (PROSE / (p + ".json")).exists()]
    bad = 0
    for p in paths:
        e = merge(p)
        for line in e:
            print("ERROR", line)
        bad += bool(e)
    print(f"merged {len(paths) - bad} of {len(paths)}")
