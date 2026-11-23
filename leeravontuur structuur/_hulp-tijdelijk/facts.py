#!/usr/bin/env python3
"""Throwaway helper (not committed): AST facts for the 'leeravontuur structuur' map."""
import ast, builtins, hashlib, json, re, subprocess, sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/home/user/oefeningenimrane")
OUT = REPO / "leeravontuur structuur"
SKIP = (".svg", ".png")
BUILTIN_NAMES = set(dir(builtins))
BUILTIN_METHODS = set()
for _t in (str, bytes, bytearray, list, dict, set, frozenset, tuple, int, float, complex, bool, object):
    BUILTIN_METHODS |= set(dir(_t))
SCHEMA = "leeravontuur-structuur/1"


def tracked():
    return subprocess.check_output(["git", "-C", str(REPO), "ls-files"], text=True).splitlines()


def explained(paths):
    return [p for p in paths if not p.endswith(SKIP) and p != "LICENSE"]


def kind_of(p):
    if p.endswith(".py"):
        return "test" if p.startswith("tests/") else "python"
    return {"json": "json", "md": "markdown", "sh": "script", "bat": "script", "command": "script"}.get(p.rsplit(".", 1)[-1], "config")


def layer_of(p):
    for pre, lay in (("leeravontuur/kern/", "kern"), ("leeravontuur/terminal/", "terminal"), ("leeravontuur/venster/", "venster"),
                     ("leeravontuur/inhoud/", "inhoud"), ("tests/", "tests"), ("docs/", "docs"), ("werk/", "werk"), (".github/", "ci")):
        if p.startswith(pre):
            return lay
    return "package" if p.startswith("leeravontuur/") else "root"


def short(node, n=60):
    try:
        s = ast.unparse(node)
    except Exception:
        s = "?"
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def modname(path):
    if "/" not in path:
        return "<script>:" + path
    parts = path[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


MODS, BYPATH = {}, {}
METHODS_BY_NAME = defaultdict(list)


class Func:
    def __init__(self, mod, node, qual, kind, owner, parent):
        self.mod, self.node, self.qual, self.kind, self.owner, self.parent = mod, node, qual, kind, owner, parent
        self.local_defs = {}
        self.calls = []       # (ast.Call, lineno)
        self.res = {}         # target -> set(lines)
        self.unres = {}       # expr -> [set(lines), candidates, count]
        self.ext = set()
        self.dyn = []
        self.called_by = defaultdict(set)


def defs_in(body):
    out = {}
    for st in body:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[st.name] = st
        else:
            for fld in ("body", "orelse", "finalbody"):
                out.update(defs_in(getattr(st, fld, []) or []))
            for h in getattr(st, "handlers", []) or []:
                out.update(defs_in(h.body))
    return out


class Mod:
    def __init__(self, path):
        self.path = path
        self.src = (REPO / path).read_text(encoding="utf-8")
        self.sha = hashlib.sha256(self.src.encode("utf-8")).hexdigest()
        self.tree = ast.parse(self.src)
        self.nlines = len(self.src.splitlines())
        self.modname = modname(path)
        self.is_pkg = path.endswith("__init__.py")
        self.alias, self.imports = {}, []
        self.top, self.classes = {}, {}
        self.funcs, self.class_list, self.constants = [], [], []
        self.module_scope = Func(self, None, "<module>", "module", None, None)
        self.class_scopes = {}
        self.collect_imports()
        self.collect()

    def collect_imports(self):
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    name = a.asname or a.name.split(".")[0]
                    self.alias[name] = ("module", a.name if a.asname else a.name.split(".")[0])
                    self.imports.append({"module": a.name, "names": [], "alias": a.asname, "line": n.lineno})
            elif isinstance(n, ast.ImportFrom):
                base = self.abs_module(n)
                if base is None:
                    continue
                self.imports.append({"module": base, "names": [a.name for a in n.names], "alias": None, "line": n.lineno})
                for a in n.names:
                    self.alias[a.asname or a.name] = ("from", base, a.name)

    def abs_module(self, n):
        if n.level == 0:
            return n.module
        if ":" in self.modname:
            return None
        pkg = self.modname if self.is_pkg else self.modname.rsplit(".", 1)[0]
        parts = pkg.split(".")
        parts = parts[: len(parts) - (n.level - 1)]
        return ".".join(parts + ([n.module] if n.module else []))

    def collect(self):
        for st in self.tree.body:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.top[st.name] = "function"
            elif isinstance(st, ast.ClassDef):
                self.top[st.name] = "class"
        C = self

        class V(ast.NodeVisitor):
            def __init__(s):
                s.stack = []   # items: ("class", qualname) | ("func", Func)

            def scope(s):
                for kind, item in reversed(s.stack):
                    if kind == "func":
                        return item
                    return C.class_scope(item)
                return C.module_scope

            def owner(s):
                for kind, item in reversed(s.stack):
                    if kind == "class":
                        return item
                return None

            def qual(s, name):
                names = [i if k == "class" else i.node.name for k, i in s.stack]
                return ".".join(names + [name])

            def visit_FunctionDef(s, node):
                for d in node.decorator_list:
                    s.visit(d)
                for d in node.args.defaults + [x for x in node.args.kw_defaults if x]:
                    s.visit(d)
                top = s.stack[-1] if s.stack else None
                parent = next((i for k, i in reversed(s.stack) if k == "func"), None)
                if top and top[0] == "class":
                    kind = "method"
                    decs = [short(d) for d in node.decorator_list]
                    if "property" in decs or any(x.endswith(".setter") for x in decs):
                        kind = "property"
                    elif "staticmethod" in decs:
                        kind = "staticmethod"
                    elif "classmethod" in decs:
                        kind = "classmethod"
                elif top and top[0] == "func":
                    kind = "nested"
                else:
                    kind = "function"
                f = Func(C, node, s.qual(node.name), kind, s.owner(), parent)
                f.local_defs = {n: f.qual + "." + n for n in defs_in(node.body)}
                C.funcs.append(f)
                s.stack.append(("func", f))
                for st in node.body:
                    s.visit(st)
                s.stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_ClassDef(s, node):
                for d in node.decorator_list + node.bases + [k.value for k in node.keywords]:
                    s.visit(d)
                qual = s.qual(node.name)
                C.class_list.append((qual, node))
                C.classes[node.name] = {"qual": qual, "bases": node.bases, "methods": {n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}}
                s.stack.append(("class", qual))
                for st in node.body:
                    s.visit(st)
                s.stack.pop()

            def visit_Call(s, node):
                s.scope().calls.append((node, node.lineno))
                s.generic_visit(node)

        V().visit(self.tree)
        for st in self.tree.body:
            targets = []
            if isinstance(st, ast.Assign):
                targets, val = st.targets, st.value
            elif isinstance(st, ast.AnnAssign) and st.value is not None:
                targets, val = [st.target], st.value
            else:
                continue
            for t in targets:
                for nm in ([t] if isinstance(t, ast.Name) else [e for e in getattr(t, "elts", []) if isinstance(e, ast.Name)]):
                    self.constants.append({"name": nm.id, "line": st.lineno, "value_type": type(val).__name__, "value_preview": short(val, 70)})

    def class_scope(self, qual):
        if qual not in self.class_scopes:
            self.class_scopes[qual] = Func(self, None, "<class " + qual + ">", "class-body", qual, None)
        return self.class_scopes[qual]


def load_all():
    for p in tracked():
        if p.endswith(".py"):
            m = Mod(p)
            BYPATH[p] = m
            MODS[m.modname] = m
    for m in BYPATH.values():
        for f in m.funcs:
            if f.kind in ("method", "property", "classmethod", "staticmethod") and not m.path.startswith("tests/"):
                METHODS_BY_NAME[f.node.name].append(m.path + "::" + f.qual)
    for m in BYPATH.values():
        for sc in [m.module_scope] + list(m.class_scopes.values()) + m.funcs:
            resolve_scope(m, sc)
    for m in BYPATH.values():
        for i in m.imports:
            for tgt in import_targets(i):
                if tgt != m.path:
                    IMPORTED_BY[tgt].add(m.path)
    for m in BYPATH.values():
        for sc in [m.module_scope] + list(m.class_scopes.values()) + m.funcs:
            for t, lines in sc.res.items():
                T = target_owner(t)
                if T is not None:
                    T.called_by[m.path + "::" + sc.qual].update(lines)


FUNC_INDEX = {}


def target_owner(t):
    if not FUNC_INDEX:
        for m in BYPATH.values():
            for f in m.funcs:
                FUNC_INDEX[m.path + "::" + f.qual] = f
            for q, node in m.class_list:
                FUNC_INDEX.setdefault(m.path + "::" + q, ClassRef(m, q, node))
    return FUNC_INDEX.get(t)


class ClassRef:
    def __init__(self, m, q, node):
        self.mod, self.qual, self.node = m, q, node
        self.called_by = defaultdict(set)


def lookup(mname, name, depth=0):
    m = MODS.get(mname)
    if not m or depth > 3:
        return None
    if name in m.top:
        return (m.path, name, m.top[name])
    a = m.alias.get(name)
    if a and a[0] == "from":
        return lookup(a[1], a[2], depth + 1)
    return None


def ctor(path, cname):
    return find_method(path, cname, "__init__") or f"{path}::{BYPATH[path].classes[cname]['qual']}"


def find_method(path, cname, attr, seen=None):
    seen = seen or set()
    if (path, cname) in seen:
        return None
    seen.add((path, cname))
    m = BYPATH.get(path)
    c = m.classes.get(cname) if m else None
    if not c:
        return None
    if attr in c["methods"]:
        return f"{path}::{c['qual']}.{attr}"
    for b in c["bases"]:
        r = class_of(m, b)
        if r:
            t = find_method(r[0], r[1], attr, seen)
            if t:
                return t
    return None


def chain_of(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return parts[::-1]
    return None


def class_of(m, node):
    ch = chain_of(node) if isinstance(node, ast.Attribute) else ([node.id] if isinstance(node, ast.Name) else None)
    if not ch:
        return None
    if len(ch) == 1:
        if ch[0] in m.classes:
            return (m.path, ch[0])
        a = m.alias.get(ch[0])
        if a and a[0] == "from":
            r = lookup(a[1], a[2])
            if r and r[2] == "class":
                return (r[0], r[1])
        return None
    a = m.alias.get(ch[0])
    mn = None
    if a and a[0] == "module":
        mn = a[1]
    elif a and a[0] == "from" and f"{a[1]}.{a[2]}" in MODS:
        mn = f"{a[1]}.{a[2]}"
    if mn:
        for p in ch[1:-1]:
            if f"{mn}.{p}" in MODS:
                mn = f"{mn}.{p}"
        r = lookup(mn, ch[-1])
        if r and r[2] == "class":
            return (r[0], r[1])
    return None


def chain_local(sc, name):
    f = sc
    while f is not None:
        if name in f.local_defs:
            return f.local_defs[name]
        f = f.parent
    return None


def add_res(sc, t, ln):
    sc.res.setdefault(t, set()).add(ln)


def resolve_scope(m, sc):
    for node, ln in sc.calls:
        try:
            resolve_call(m, sc, node, ln)
        except Exception as e:  # never let the helper crash the whole run
            sc.unres.setdefault("<error " + type(e).__name__ + ">", [set(), [], 0])[0].add(ln)


def resolve_call(m, sc, node, ln):
    f = node.func
    if isinstance(f, ast.Name):
        n = f.id
        loc = chain_local(sc, n)
        if loc:
            return add_res(sc, f"{m.path}::{loc}", ln)
        if n in m.top:
            return add_res(sc, ctor(m.path, n) if m.top[n] == "class" else f"{m.path}::{n}", ln)
        a = m.alias.get(n)
        if a and a[0] == "from":
            r = lookup(a[1], a[2])
            if r:
                return add_res(sc, ctor(r[0], r[1]) if r[2] == "class" else f"{r[0]}::{r[1]}", ln)
            sc.ext.add(f"{a[1]}.{a[2]}")
            return
        if a:
            sc.ext.add(a[1])
            return
        if n in BUILTIN_NAMES:
            sc.ext.add(n)
            return
        u = sc.unres.setdefault(n, [set(), [], 0])
        u[0].add(ln)
        return
    if isinstance(f, ast.Subscript):
        sc.dyn.append({"kind": "subscript-call", "line": ln, "expr": short(f, 70)})
        return
    if isinstance(f, ast.Call):
        if isinstance(f.func, ast.Name) and f.func.id == "getattr" and not (len(f.args) > 1 and isinstance(f.args[1], ast.Constant)):
            sc.dyn.append({"kind": "getattr", "line": ln, "expr": short(f, 70)})
        else:
            u = sc.unres.setdefault(short(f, 40), [set(), [], 0])
            u[0].add(ln)
        return
    if not isinstance(f, ast.Attribute):
        return
    attr, v = f.attr, f.value
    if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "super" and sc.owner:
        cn = sc.owner.split(".")[-1]
        c = m.classes.get(cn)
        if c:
            for b in c["bases"]:
                r = class_of(m, b)
                t = find_method(r[0], r[1], attr) if r else None
                if t:
                    return add_res(sc, t, ln)
    ch = chain_of(f)
    if ch:
        first = ch[0]
        if first in ("self", "cls") and sc.owner and len(ch) == 2:
            cn = sc.owner.split(".")[-1]
            t = find_method(m.path, cn, attr)
            if t:
                return add_res(sc, t, ln)
        elif first in m.top and m.top[first] == "class" and len(ch) == 2:
            t = find_method(m.path, first, attr)
            if t:
                return add_res(sc, t, ln)
        elif first in m.alias:
            a = m.alias[first]
            mn = None
            if a[0] == "module":
                mn = a[1]
            elif a[0] == "from" and f"{a[1]}.{a[2]}" in MODS:
                mn = f"{a[1]}.{a[2]}"
            elif a[0] == "from":
                r = lookup(a[1], a[2])
                if r and r[2] == "class" and len(ch) == 2:
                    t = find_method(r[0], r[1], attr)
                    if t:
                        return add_res(sc, t, ln)
                elif r is None:
                    sc.ext.add(".".join([a[1], a[2]] + ch[1:]))
                    return
            if mn:
                known = mn in MODS or any(k.startswith(mn + ".") for k in MODS)
                if known:
                    cur = mn
                    for p in ch[1:-1]:
                        if f"{cur}.{p}" in MODS:
                            cur = f"{cur}.{p}"
                        else:
                            r = lookup(cur, p)
                            if r and r[2] == "class":
                                t = find_method(r[0], r[1], attr)
                                if t:
                                    return add_res(sc, t, ln)
                            cur = None
                            break
                    if cur:
                        r = lookup(cur, attr)
                        if r:
                            return add_res(sc, ctor(r[0], r[1]) if r[2] == "class" else f"{r[0]}::{r[1]}", ln)
                else:
                    sc.ext.add(".".join(ch))
                    return
    if attr in BUILTIN_METHODS:
        return
    cands = METHODS_BY_NAME.get(attr, [])
    if not cands:
        sc.ext.add("." + attr)
        return
    u = sc.unres.setdefault(short(f, 60), [set(), [], 0])
    u[0].add(ln)
    u[1], u[2] = (cands if len(cands) <= 6 else []), len(cands)


# ------------------------------------------------------------------ rendering
def doc1(node):
    d = ast.get_docstring(node)
    if not d:
        return ""
    d = " ".join(d.split("\n\n")[0].split())
    return d if len(d) <= 240 else d[:239] + "…"


def params_of(a):
    def p(arg, d, kind):
        return {"name": arg.arg, "kind": kind, "default": short(d, 40) if d is not None else None,
                "annotation": short(arg.annotation, 40) if arg.annotation is not None else None}
    pos = a.posonlyargs + a.args
    defs = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)
    out = [p(x, d, "positional") for x, d in zip(pos, defs)]
    if a.vararg:
        out.append(p(a.vararg, None, "vararg"))
    out += [p(x, d, "keyword-only") for x, d in zip(a.kwonlyargs, a.kw_defaults)]
    if a.kwarg:
        out.append(p(a.kwarg, None, "kwarg"))
    return out


def calls_block(sc):
    return {
        "calls": [{"target": t, "lines": sorted(l)} for t, l in sorted(sc.res.items())],
        "unresolved_calls": [{"expr": e, "lines": sorted(v[0]), "candidates": v[1], "candidates_count": v[2]} for e, v in sorted(sc.unres.items())],
        "external_calls": sorted(sc.ext),
        "dynamic": sc.dyn,
    }


def func_entry(m, f):
    n = f.node
    d = {"name": n.name, "qualname": f.qual, "kind": f.kind, "lines": [n.lineno, n.end_lineno],
         "params": params_of(n.args), "returns": short(n.returns, 40) if n.returns is not None else None,
         "decorators": [short(x, 40) for x in n.decorator_list], "docstring": doc1(n), "explanation": ""}
    d.update(calls_block(f))
    d["called_by"] = [{"caller": c, "lines": sorted(l)} for c, l in sorted(f.called_by.items())]
    return d


def class_entry(m, qual, node):
    attrs = []
    for st in node.body:
        if isinstance(st, ast.Assign):
            for t in st.targets:
                if isinstance(t, ast.Name):
                    attrs.append({"name": t.id, "line": st.lineno, "scope": "class", "value_preview": short(st.value, 60)})
        elif isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
            attrs.append({"name": st.target.id, "line": st.lineno, "scope": "class", "value_preview": short(st.value, 60) if st.value else None})
    seen = set()
    for st in node.body:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for x in ast.walk(st):
                tg = []
                if isinstance(x, ast.Assign):
                    tg = x.targets
                elif isinstance(x, (ast.AugAssign, ast.AnnAssign)):
                    tg = [x.target]
                for t in tg:
                    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self" and t.attr not in seen:
                        seen.add(t.attr)
                        attrs.append({"name": t.attr, "line": x.lineno, "scope": "instance", "value_preview": None})
    ref = target_owner(m.path + "::" + qual)
    inst = defaultdict(set)
    for k, v in (ref.called_by.items() if ref else []):
        inst[k].update(v)
    c = BYPATH[m.path].classes.get(node.name)
    if c and "__init__" in c["methods"]:
        ini = target_owner(f"{m.path}::{c['qual']}.__init__")
        for k, v in (ini.called_by.items() if ini else []):
            inst[k].update(v)
    return {"name": node.name, "qualname": qual, "lines": [node.lineno, node.end_lineno], "bases": [short(b, 40) for b in node.bases],
            "decorators": [short(x, 40) for x in node.decorator_list], "docstring": doc1(node), "explanation": "",
            "attributes": attrs, "instantiated_by": [{"caller": c2, "lines": sorted(l)} for c2, l in sorted(inst.items())],
            "methods": []}


IMPORTED_BY = defaultdict(set)


def import_targets(i):
    out = []
    mod = i["module"]
    if mod in MODS:
        out.append(MODS[mod].path)
    for n in i["names"]:
        if f"{mod}.{n}" in MODS:
            out.append(MODS[f"{mod}.{n}"].path)
    return sorted(set(out))


def py_facts(path):
    m = BYPATH[path]
    entry = {"imports": [], "imported_by": [], "module_docstring": doc1(m.tree), "module_calls": [],
             "constants": m.constants, "classes": [], "functions": [], "registries": []}
    for i in m.imports:
        entry["imports"].append({**i, "resolves_to": import_targets(i), "internal": bool(import_targets(i))})
    entry["imported_by"] = sorted(IMPORTED_BY.get(path, []))
    scopes = [m.module_scope] + list(m.class_scopes.values())
    for sc in scopes:
        b = calls_block(sc)
        if b["calls"] or b["unresolved_calls"] or b["dynamic"] or b["external_calls"]:
            entry["module_calls"].append({"scope": "module" if sc.kind == "module" else sc.qual, **b})
    cls_by_qual = {}
    for qual, node in m.class_list:
        ce = class_entry(m, qual, node)
        cls_by_qual[qual] = ce
        entry["classes"].append(ce)
    for f in m.funcs:
        fe = func_entry(m, f)
        owner = f.owner
        (cls_by_qual[owner]["methods"] if owner in cls_by_qual and f.kind != "function" else entry["functions"]).append(fe)
    return entry


def md_facts(path):
    src = (REPO / path).read_text(encoding="utf-8")
    heads, fence = [], False
    for i, line in enumerate(src.splitlines(), 1):
        if line.strip().startswith("```"):
            fence = not fence
        elif not fence:
            mm = re.match(r"(#{1,6})\s+(.*\S)", line)
            if mm:
                heads.append({"level": len(mm.group(1)), "text": mm.group(2), "line": i})
    links = []
    for mm in re.finditer(r"\[([^\]]*)\]\(([^)\s]+)\)", src):
        t = mm.group(2)
        links.append({"text": mm.group(1)[:60], "target": t, "internal": not re.match(r"[a-z]+://|mailto:", t)})
    base = path.rsplit("/", 1)[-1]
    refs = []
    for q in tracked():
        if q == path or q.endswith(SKIP) or not q.endswith((".md", ".py")):
            continue
        txt = (REPO / q).read_text(encoding="utf-8", errors="ignore")
        if path in txt or ("/" in path and base in txt and q.endswith(".md") and q.rsplit("/", 1)[0] == path.rsplit("/", 1)[0]) or ("/" not in path and base in txt):
            refs.append(q)
    return {"headings": heads, "links": links, "referenced_by": refs, "words": len(src.split()), "summary": ""}


def shape(v, depth=0):
    if isinstance(v, dict):
        if depth >= 5:
            return {"$object": len(v)}
        sh = {k: shape(x, depth + 1) for k, x in v.items()}
        if len(sh) > 3:
            vals = list({json.dumps(s, sort_keys=True) for s in sh.values()})
            if len(vals) == 1:
                return {"$keys": list(sh.keys())[:8] + (["…"] if len(sh) > 8 else []), "$count": len(sh), "$values": next(iter(sh.values()))}
        return sh
    if isinstance(v, list):
        if not v:
            return {"$list": 0}
        shs = {json.dumps(shape(x, depth + 1), sort_keys=True) for x in v}
        return {"$list": len(v), "$items": json.loads(next(iter(shs))) if len(shs) == 1 else "mixed"}
    return {str: "string", bool: "boolean", int: "number", float: "number", type(None): "null"}.get(type(v), "other")


def json_facts(path):
    data = json.loads((REPO / path).read_text(encoding="utf-8"))
    base = path.rsplit("/", 1)[-1]
    read_by = []
    for p, m in BYPATH.items():
        if base in m.src or path in m.src:
            read_by.append(p)
    return {"keys": list(data.keys()) if isinstance(data, dict) else [], "shape": shape(data), "read_by": read_by}


def file_facts(path):
    k = kind_of(path)
    src = (REPO / path).read_bytes()
    text = src.decode("utf-8", errors="replace")
    base = {"schema": SCHEMA, "path": path, "kind": k, "layer": layer_of(path), "lines": len(text.splitlines()),
            "source_sha256": hashlib.sha256(src).hexdigest(), "purpose": "", "details": ""}
    if k in ("python", "test"):
        base.update(py_facts(path))
    elif k == "markdown":
        base.update(md_facts(path))
    elif k == "json":
        base.update(json_facts(path))
    return base


def listing(path):
    f = file_facts(path)
    print(f"{path}  [{f['kind']}/{f['layer']}] {f['lines']} lines")
    for c in f.get("constants", []):
        print(f"  const {c['name']} L{c['line']} {c['value_type']}")
    def pf(fn, ind):
        ps = ",".join(p["name"] for p in fn["params"])
        print(f"{ind}{fn['qualname']} [{fn['kind']}] L{fn['lines'][0]}-{fn['lines'][1]} ({ps}) calls={len(fn['calls'])} unres={len(fn['unresolved_calls'])} by={len(fn['called_by'])}")
    for fn in f.get("functions", []):
        pf(fn, "  def ")
    for c in f.get("classes", []):
        print(f"  class {c['qualname']} L{c['lines'][0]}-{c['lines'][1]} ({', '.join(c['bases'])})")
        for fn in c["methods"]:
            pf(fn, "    ")


if __name__ == "__main__":
    load_all()
    if len(sys.argv) > 2 and sys.argv[1] == "list":
        for p in sys.argv[2:]:
            listing(p)
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        nf = nc = res = unres = ext = dyn = 0
        for m in BYPATH.values():
            for f in m.funcs:
                nf += 1; res += len(f.res); unres += len(f.unres); ext += len(f.ext); dyn += len(f.dyn)
            nc += len(m.class_list)
        print(dict(files=len(BYPATH), functions=nf, classes=nc, resolved_targets=res, unresolved=unres, external=ext, dynamic=dyn))
