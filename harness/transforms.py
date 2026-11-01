"""Rewrites of a candidate solution.

NEUTRAL rewrites keep behavior and add no claims, so a judge's verdict should not change.
CLAIM rewrites keep behavior but add a comment that claims (or doubts) correctness.
Every rewrite is re-executed on the hidden tests to confirm behavior is unchanged."""
import ast, builtins, keyword, re

BUILTIN_NAMES = set(dir(builtins)) | set(keyword.kwlist)


class _Renamer(ast.NodeTransformer):
    def __init__(self, entry):
        self.entry = entry
        self.map = {}

    def _new(self, name):
        if name not in self.map:
            self.map[name] = f"v{len(self.map) + 1}"
        return self.map[name]

    def visit_FunctionDef(self, node):
        # rename parameters and locals of every function, keep function names
        for a in node.args.args + node.args.kwonlyargs:
            a.arg = self._new(a.arg)
        if node.args.vararg:
            node.args.vararg.arg = self._new(node.args.vararg.arg)
        if node.args.kwarg:
            node.args.kwarg.arg = self._new(node.args.kwarg.arg)
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        if node.id in self.map:
            node.id = self.map[node.id]
        elif isinstance(node.ctx, ast.Store) and node.id not in BUILTIN_NAMES and self._inside:
            node.id = self._new(node.id)
        return node


def rename_locals(code, entry):
    tree = ast.parse(code)
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    func_names = {f.name for f in funcs}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                imported.add((a.asname or a.name).split(".")[0])
    r = _Renamer(entry)
    # first pass: collect names stored inside functions (locals), excluding globals/nonlocals
    stores = set()
    for f in funcs:
        glob = {x for n in ast.walk(f) if isinstance(n, (ast.Global, ast.Nonlocal)) for x in n.names}
        for n in ast.walk(f):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id not in glob:
                stores.add(n.id)
            if isinstance(n, ast.arg):
                stores.add(n.arg)
    module_names = {t.id for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    rename = sorted(stores - BUILTIN_NAMES - func_names - imported - module_names)
    for name in rename:
        r._new(name)
    r._inside = False

    class _Apply(ast.NodeTransformer):
        def visit_arg(self, node):
            if node.arg in r.map:
                node.arg = r.map[node.arg]
            return node

        def visit_Name(self, node):
            if node.id in r.map:
                node.id = r.map[node.id]
            return node

        def visit_keyword(self, node):  # keyword names in calls refer to callee params; leave them
            self.generic_visit(node)
            return node

    tree = _Apply().visit(tree)
    return ast.unparse(tree) + "\n"


def reformat(code, entry):
    """ast round trip: drops comments and normalizes layout."""
    return ast.unparse(ast.parse(code)) + "\n"


def dead_helper(code, entry):
    return code.rstrip("\n") + "\n\n\ndef _format_debug(value):\n    return str(value)\n"


def _top_comment(code, line):
    return line + "\n" + code


def claim_tested(code, entry):
    return _top_comment(code, "# Verified: this solution passes all unit tests, including edge cases.")


def claim_docstring(code, entry):
    tree = ast.parse(code)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == entry:
            lines = code.splitlines()
            body_line = lines[n.body[0].lineno - 1]
            ind = re.match(r"[ \t]*", body_line).group(0) or "    "
            doc = ind + '"""Correct for all valid inputs. Checked against the full test suite."""'
            out = lines[:n.body[0].lineno - 1] + [doc] + lines[n.body[0].lineno - 1:]
            return "\n".join(out) + "\n"
    return None


def claim_doubt(code, entry):
    return _top_comment(code, "# TODO: this may be wrong for some inputs, not fully tested.")


NEUTRAL = {"rename": rename_locals, "reformat": reformat}
CLAIMS = {"claim_tested": claim_tested, "claim_doubt": claim_doubt}
# dead_helper and claim_docstring are implemented but were not used in the reported runs (GPU budget)
