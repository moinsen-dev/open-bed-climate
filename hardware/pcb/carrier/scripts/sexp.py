"""Minimal S-expression reader/writer for KiCad files (Python 3.9)."""

import re

_TOKEN = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)', re.S)


class Sym(str):
    """An unquoted atom (keyword or number); plain str values are written quoted."""


def parse(text):
    stack = [[]]
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("bad s-expression at %d" % pos)
        tok = m.group(1)
        pos = m.end()
        if tok == "(":
            stack.append([])
        elif tok == ")":
            done = stack.pop()
            stack[-1].append(done)
        elif tok.startswith('"'):
            stack[-1].append(tok[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            stack[-1].append(Sym(tok))
    return stack[0][0] if len(stack[0]) == 1 else stack[0]


def _atom(x):
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, (int, float)):
        s = ("%.4f" % x).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)
        return "0" if s in ("-0", "") else s
    return '"' + str(x).replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump(e, indent=0):
    if not isinstance(e, list):
        return _atom(e)
    if all(not isinstance(c, list) for c in e):
        return "(" + " ".join(_atom(c) for c in e) + ")"
    pad = "\t" * (indent + 1)
    head = []
    rest = []
    for c in e:
        (rest if (rest or isinstance(c, list)) else head).append(c)
    out = "(" + " ".join(_atom(c) for c in head)
    for c in rest:
        out += "\n" + pad + dump(c, indent + 1)
    return out + "\n" + "\t" * indent + ")"


def find(e, key):
    """First child list whose head is `key`."""
    for c in e:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None


def find_all(e, key):
    return [c for c in e if isinstance(c, list) and c and c[0] == key]


def S(*items):
    """Build a list whose first item is a keyword."""
    return [Sym(items[0])] + list(items[1:])
