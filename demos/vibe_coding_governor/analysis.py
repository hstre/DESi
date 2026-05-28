"""Deterministic structural analysis of the app sources (AST-based, no execution).

`extract_state(sources)` parses each Python source and returns a structural state:
routes (+ whether each is auth-decorated), SQL `execute` call styles (parameterized
vs string-built), secret-logging calls, migrations (+ determinism), declared vs
referenced data columns, modules, and the architectural frame categories present.

This is structural, not behavioural: it sees that a route HAS an `@require_auth`
decorator, not whether that decorator is implemented correctly (see the honest
negatives in the report). Pure + deterministic: identical sources -> identical state.
"""
from __future__ import annotations

import ast

AUTH_DECORATORS = frozenset({"require_auth", "login_required", "admin_required"})
LOG_FUNCS = frozenset({"debug", "info", "warning", "error", "exception", "critical", "log", "print"})
SECRET_NAMES = frozenset({"password", "passwd", "pw", "secret", "token", "api_key", "apikey", "pwd"})
HASH_FUNCS = frozenset({"generate_password_hash", "check_password_hash", "hash", "sha256",
                        "pbkdf2_hmac", "bcrypt", "hashpw"})
# tokens whose value is decided at migration time, not deterministically pinned
NONDET_TOKENS = ("datetime('now')", "current_timestamp", "random()", "randomblob",
                 "uuid", "now()", "strftime('%s','now')")
KNOWN_DATA_COLUMNS = frozenset({"id", "title", "tag", "due_date", "priority", "archived",
                                "username", "pw_hash", "created_at", "user_id", "done"})
PUBLIC_ROUTES = frozenset({"/", "/health", "/login"})
SUBSYSTEM_CATEGORIES = frozenset({"admin", "notifications", "plugins"})


def _called_name(node: ast.AST):
    f = node.func if isinstance(node, ast.Call) else node
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return None


def _decorator_name(dec: ast.AST):
    if isinstance(dec, ast.Call):
        return _called_name(dec.func)
    if isinstance(dec, ast.Attribute):
        return dec.attr
    if isinstance(dec, ast.Name):
        return dec.id
    return None


def _route_decorator(dec: ast.AST):
    """If `dec` is an @x.route(...) call, return (path, methods); else None."""
    if isinstance(dec, ast.Call) and _called_name(dec.func) == "route":
        path = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else None
        methods = ["GET"]
        for kw in dec.keywords:
            if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                methods = sorted(e.value for e in kw.value.elts if isinstance(e, ast.Constant))
        return path, methods
    return None


def _category(path: str, module: str) -> str:
    p = path or ""
    if module == "admin.py" or p.startswith("/admin"):
        return "admin"
    if module == "notifications.py" or p.startswith("/notify"):
        return "notifications"
    if module == "plugins.py" or p.startswith("/plugin"):
        return "plugins"
    if p in PUBLIC_ROUTES:
        return "public"
    return "core"


def _sql_static_text(arg: ast.AST) -> str:
    """Best-effort static SQL text: a constant string, or the concatenation of all
    constant string parts inside an f-string / BinOp / .format() build."""
    if arg is None:
        return ""
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    parts = [c.value for c in ast.walk(arg) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
    return " ".join(parts)


def _is_raw_sql(arg: ast.AST) -> bool:
    """True if the SQL is built by string interpolation rather than a pinned literal."""
    if arg is None:
        return False
    if isinstance(arg, ast.JoinedStr):                      # f-string
        return True
    if isinstance(arg, ast.BinOp) and isinstance(arg.op, (ast.Mod, ast.Add)):  # "%s"%x / "a"+x
        return any(isinstance(n, ast.Constant) and isinstance(n.value, str) for n in ast.walk(arg))
    if isinstance(arg, ast.Call) and _called_name(arg) == "format":            # "...".format(x)
        return True
    return False


def _names_in(node: ast.AST) -> set:
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
                and isinstance(n.slice.value, str):
            out.add(n.slice.value)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


def _analyze_module(filename: str, source: str, state: dict) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        state["parse_errors"].append(filename)
        return
    for node in ast.walk(tree):
        # routes
        if isinstance(node, ast.FunctionDef):
            path = methods = None
            has_auth = False
            for dec in node.decorator_list:
                rd = _route_decorator(dec)
                if rd is not None:
                    path, methods = rd
                if _decorator_name(dec) in AUTH_DECORATORS:
                    has_auth = True
            if path is not None:
                state["routes"].append({"path": path, "methods": methods or ["GET"],
                                        "auth": has_auth, "func": node.name,
                                        "category": _category(path, filename), "module": filename})
        # execute() calls
        if isinstance(node, ast.Call) and _called_name(node) == "execute":
            arg0 = node.args[0] if node.args else None
            sql = _sql_static_text(arg0)
            low = sql.lower()
            writes_pw = (("pw_hash" in low or "password" in low)
                         and ("insert" in low or "update" in low))
            hashed = any(isinstance(d, ast.Call) and _called_name(d) in HASH_FUNCS
                         for d in ast.walk(node))
            state["executes"].append({"raw": _is_raw_sql(arg0), "sql": sql,
                                      "writes_password": writes_pw, "hashed": hashed,
                                      "module": filename})
        # logging / print of secrets
        if isinstance(node, ast.Call) and _called_name(node) in LOG_FUNCS:
            refs = _names_in(node)
            leaked = sorted(refs & SECRET_NAMES)
            if leaked:
                state["secret_logs"].append({"func": _called_name(node), "names": leaked,
                                             "module": filename})
        # MIGRATIONS list
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "MIGRATIONS" \
                        and isinstance(node.value, ast.List):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Tuple) and len(elt.elts) == 2 \
                                and isinstance(elt.elts[0], ast.Constant) \
                                and isinstance(elt.elts[1], ast.Constant):
                            ver, sql = elt.elts[0].value, elt.elts[1].value
                            low = sql.lower()
                            nondet = any(tok in low for tok in NONDET_TOKENS)
                            state["migrations"].append({"version": ver, "sql": sql,
                                                        "nondeterministic": nondet})


def _declared_columns(migrations) -> set:
    cols = set()
    for m in migrations:
        low = m["sql"].lower()
        if "create table" in low:
            inside = m["sql"][m["sql"].find("(") + 1: m["sql"].rfind(")")]
            for coldef in inside.split(","):
                tok = coldef.strip().split()
                if tok and tok[0].lower() in KNOWN_DATA_COLUMNS:
                    cols.add(tok[0].lower())
        if "add column" in low:
            after = low.split("add column", 1)[1].strip().split()
            if after and after[0] in KNOWN_DATA_COLUMNS:
                cols.add(after[0])
    return cols


def extract_state(sources: dict) -> dict:
    state = {"routes": [], "executes": [], "secret_logs": [], "migrations": [],
             "parse_errors": [], "modules": sorted(sources)}
    for fn in sorted(sources):
        if fn.endswith(".py"):
            _analyze_module(fn, sources[fn], state)
    state["routes"].sort(key=lambda r: (r["path"], r["func"]))
    state["migrations"].sort(key=lambda m: m["version"])
    declared = _declared_columns(state["migrations"])
    referenced = set()
    for e in state["executes"]:
        low = e["sql"].lower()
        referenced |= {c for c in KNOWN_DATA_COLUMNS if c in low.split() or (" " + c + " ") in (" " + low + " ")}
    # data columns referenced but never declared (heuristic; ignores table scoping)
    state["declared_columns"] = sorted(declared)
    state["referenced_columns"] = sorted(referenced)
    state["undeclared_referenced"] = sorted(referenced - declared)
    state["frame_categories"] = sorted({r["category"] for r in state["routes"]}
                                       | {_category("", m) for m in state["modules"]
                                          if m in ("admin.py", "notifications.py", "plugins.py")})
    # compact, order-stable structural signature (used in the replay-hash payload)
    state["signature"] = {
        "modules": state["modules"],
        "routes": [[r["path"], tuple(r["methods"]), r["auth"]] for r in state["routes"]],
        "frame_categories": state["frame_categories"],
        "declared_columns": state["declared_columns"],
        "n_raw_sql": sum(1 for e in state["executes"] if e["raw"]),
        "n_secret_logs": len(state["secret_logs"]),
        "n_migrations": len(state["migrations"]),
    }
    return state
