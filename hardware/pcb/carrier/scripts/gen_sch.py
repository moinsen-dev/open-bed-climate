"""Generate carrier.kicad_sch from design.py.

Layout style: one flat sheet, parts grouped by function block, every connected pin carries a net label (no wires),
unused pins get a no-connect flag, and PWR_FLAGs mark the externally fed rails. Netlist-exact, readable as a
reference schematic; the PDF in fab/ is rendered from it.
"""

import os
import uuid

import design
from sexp import S, Sym, dump, find, find_all, parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SHARE = os.environ.get("KICAD_SHARE", os.path.expanduser("~/Applications/KiCad.app/Contents/SharedSupport"))
NS = uuid.UUID("6f1c2a43-5b7e-4d0a-9c1e-0b5ed0c1a7e0")  # stable UUIDs keep regenerated files diff-friendly
PROJECT = "carrier"
GRID = 1.27

BLOCK_TITLES = [
    ("mcu", "Modules: Raspberry Pi Pico 2 (control MCU) + ESP32-S3-DevKitC-1 (hub), OPL UART GP0/GP1 <-> GPIO18/GPIO17"),
    ("power", "12 V input, fuse, TVS, reverse-polarity P-FET, 12->5 V buck (LM2596S-5.0), 5 V ORing, test points"),
    ("adc", "ADS1115 @0x48 (ADDR=GND) on I2C0 GP8/GP9, NTC dividers 3.3 V - 10k 0.1 % - node - NTC - GND"),
    ("rs485", "RS-485 to the DPS modules: SP3485 on UART1 GP4/GP5, DE+/RE on GP6"),
    ("inputs", "Fail-safe inputs: LEAK GP21, LEVEL GP22 (LOW = good, open wire = HIGH = fault)"),
    ("zone0", "Zone 0 drivers (GP10 relay, GP11 polarity, GP12 pump, GP13 fan, GP14 flow) and sensors"),
    ("zone1", "Zone 1 drivers (GP16 relay, GP17 polarity, GP18 pump, GP19 fan, GP20 flow) and sensors"),
    ("mech", "Mounting holes"),
    ("flags", "Power flags"),
]


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def snap(v):
    return round(round(v / GRID) * GRID, 2)


# ------------------------------------------------------------------------------------------------ library symbols
_lib_cache = {}


def lib_file(lib):
    if lib == "carrier":
        return os.path.join(ROOT, "lib", "carrier.kicad_sym")
    return os.path.join(SHARE, "symbols", lib + ".kicad_sym")


def lib_symbols(lib):
    if lib not in _lib_cache:
        with open(lib_file(lib)) as f:
            tree = parse(f.read())
        _lib_cache[lib] = {s[1]: s for s in find_all(tree, "symbol")}
    return _lib_cache[lib]


def flat_symbol(lib_id):
    """Library symbol with `extends` resolved, renamed to the 'Lib:Name' form used inside a schematic."""
    lib, name = lib_id.split(":")
    syms = lib_symbols(lib)
    sym = syms[name]
    ext = find(sym, "extends")
    if ext:
        parent = flat_symbol(lib + ":" + ext[1])
        pname = parent[1].split(":")[1]
        own_props = {p[1]: p for p in find_all(sym, "property")}
        out = [Sym("symbol"), lib_id]
        for c in parent[2:]:
            if isinstance(c, list) and c[0] == "property" and c[1] in own_props:
                out.append(own_props.pop(c[1]))
            elif isinstance(c, list) and c[0] == "symbol":
                out.append([c[0], c[1].replace(pname, name, 1)] + c[2:])
            else:
                out.append(c)
        out[2:2] = list(own_props.values())
        return out
    return [Sym("symbol"), lib_id] + sym[2:]


# The KiCad Pico symbol types both GND and AGND as power outputs; on the Pico AGND is a ground return that we tie to
# GND, so it is treated as a passive pin here (only in this embedded copy).
PIN_TYPE_OVERRIDES = {("MCU_Module:RaspberryPi_Pico", "33"): "passive"}


def apply_overrides(lib_id, sym):
    def walk(e):
        for c in e:
            if isinstance(c, list) and c:
                if c[0] == "pin" and (lib_id, find(c, "number")[1]) in PIN_TYPE_OVERRIDES:
                    c[1] = Sym(PIN_TYPE_OVERRIDES[(lib_id, find(c, "number")[1])])
                elif c[0] == "symbol":
                    walk(c)

    walk(sym)
    return sym


def pins_of(sym):
    """(number, name, type, x, y, angle) for every pin, in library coordinates (y up)."""
    out = []

    def walk(e):
        for c in e:
            if isinstance(c, list) and c:
                if c[0] == "pin":
                    at = find(c, "at")
                    out.append((find(c, "number")[1], find(c, "name")[1], str(c[1]),
                                float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0))
                elif c[0] == "symbol":
                    walk(c)

    walk(sym)
    return out


# ------------------------------------------------------------------------------------------------ placement
def label_len(net):
    return len(net) * 1.05 + 2.0


def footprint_box(part, pins):
    xs = [p[3] for p in pins] or [0]
    ys = [p[4] for p in pins] or [0]
    longest = max([label_len(part.pins.get(p[0]) or "") for p in pins] or [2])
    left = min(xs) - (longest if any(p[5] == 0 for p in pins) else 2)
    right = max(xs) + (longest if any(p[5] == 180 for p in pins) else 2)
    top = max(ys) + (longest if any(p[5] == 270 for p in pins) else 2) + 3.0  # room for the reference
    bottom = min(ys) - (longest if any(p[5] == 90 for p in pins) else 2) - 3.0
    return left, right, bottom, top


def build():
    root_uuid = uid("root")
    used_libs = {}
    for p in design.PARTS:
        used_libs.setdefault(p.lib_id, apply_overrides(p.lib_id, flat_symbol(p.lib_id)))
    used_libs.setdefault("power:PWR_FLAG", flat_symbol("power:PWR_FLAG"))

    items = []
    labels = []
    ncs = []
    texts = []

    # power flags: nets with a power input pin but no power output pin get one
    need_flag = []
    for net, members in design.nets().items():
        types = set()
        for ref, pin in members:
            part = next(x for x in design.PARTS if x.ref == ref)
            for num, _n, typ, _x, _y, _a in pins_of(used_libs[part.lib_id]):
                if num == pin:
                    types.add(typ)
        if "power_in" in types and "power_out" not in types:
            need_flag.append(net)

    sheet_w = 820.0
    x0, y = 20.0, 30.0
    blocks = [b for b, _t in BLOCK_TITLES]
    for block, title in BLOCK_TITLES:
        members = [p for p in design.PARTS if p.block == block]
        if block == "flags":
            members = [("PWR_FLAG", n) for n in need_flag]
        if not members:
            continue
        texts.append(S("text", title, S("exclude_from_sim", Sym("no")), S("at", x0, y, 0),
                       S("effects", S("font", S("size", 2.54, 2.54), S("bold", Sym("yes"))), S("justify", Sym("left"), Sym("bottom"))),
                       S("uuid", uid("title", block))))
        y += 6
        x = x0
        row_h = 0
        for m in members:
            if isinstance(m, tuple):
                lib_id, net = "power:PWR_FLAG", m[1]
                pins = pins_of(used_libs[lib_id])
                fake = design.Part("#FLG", lib_id, "PWR_FLAG", "", [("1", net)])
                part = fake
            else:
                part = m
                lib_id = part.lib_id
                pins = pins_of(used_libs[lib_id])
            l, r, b, t = footprint_box(part, pins)
            w, h = r - l, t - b
            if x + w > sheet_w - 20:
                x = x0
                y += row_h + 4
                row_h = 0
            ox, oy = snap(x - l), snap(y + t)  # symbol origin: lib (0,0) -> sheet (ox, oy); y flips
            items.append(place_symbol(part, lib_id, ox, oy, pins, root_uuid, labels, ncs, need_index=len(items)))
            x += w + 4
            row_h = max(row_h, h)
        y += row_h + 14
    assert set(blocks) >= {p.block for p in design.PARTS}, "part in unknown block"

    paper = S("paper", "User", sheet_w, snap(y + 20))
    lib = S("lib_symbols", *used_libs.values())
    sch = S("kicad_sch", S("version", 20250114), S("generator", "eeschema"), S("generator_version", "9.0"),
            S("uuid", root_uuid), paper,
            S("title_block", S("title", "Open Bed Climate - Tier 0 carrier, Rev A (UNTESTED)"), S("rev", "A"),
              S("company", "Open Bed Climate - CERN-OHL-S-2.0"),
              S("comment", 1, "Generated by hardware/pcb/carrier/scripts/gen_sch.py from design.py - do not edit by hand"),
              S("comment", 2, "Pin map: firmware/obc-pico2/src/board.rs (source of truth)")),
            lib, *(texts + ncs + labels + items),
            S("sheet_instances", S("path", "/", S("page", "1"))), S("embedded_fonts", Sym("no")))
    return sch


def place_symbol(part, lib_id, ox, oy, pins, root_uuid, labels, ncs, need_index):
    is_flag = part.ref == "#FLG"
    ref = "#FLG%02d" % need_index if is_flag else part.ref
    su = uid("sym", ref)

    def prop(k, v, dx, dy, hide=False):
        eff = S("effects", S("font", S("size", 1.27, 1.27)))
        if hide:
            eff.append(S("hide", Sym("yes")))
        return S("property", k, v, S("at", snap(ox + dx), snap(oy + dy), 0), eff)

    ys = [p[4] for p in pins] or [0]
    top = -max(ys) - 2.54
    props = [prop("Reference", ref, 0, top - 1.27, hide=is_flag), prop("Value", part.value, 0, top + 0.0 if is_flag else -min(ys) + 2.54),
             prop("Footprint", part.footprint, 0, 0, True), prop("Datasheet", "~", 0, 0, True)]
    if part.lcsc:
        props.append(prop("LCSC", part.lcsc, 0, 0, True))
    sym = S("symbol", S("lib_id", lib_id), S("at", ox, oy, 0), S("unit", 1), S("exclude_from_sim", Sym("no")),
            S("in_bom", Sym("no") if is_flag or part.ref.startswith(("H", "TP")) else Sym("yes")), S("on_board", Sym("no") if is_flag else Sym("yes")),
            S("dnp", Sym("no")), S("uuid", su), *props)
    for num, _name, _typ, px, py, ang in pins:
        sym.append(S("pin", num, S("uuid", uid("pin", ref, num))))
        ax, ay = round(ox + px, 2), round(oy - py, 2)
        net = part.pins.get(num)
        if net:
            rot = (ang + 180) % 360
            just = [Sym("left"), Sym("bottom")] if rot in (0, 90) else [Sym("right"), Sym("bottom")]
            labels.append(S("global_label", net, S("shape", Sym("passive")), S("at", ax, ay, rot),
                            S("fields_autoplaced", Sym("yes")),
                            S("effects", S("font", S("size", 1.27, 1.27)), S("justify", *just[:1])),
                            S("uuid", uid("label", ref, num))))
        else:
            ncs.append(S("no_connect", S("at", ax, ay), S("uuid", uid("nc", ref, num))))
    sym.append(S("instances", S("project", PROJECT, S("path", "/" + root_uuid, S("reference", ref), S("unit", 1)))))
    return sym


def write_lib_tables():
    """Project library tables: KiCad's stock libraries plus the project library, so ERC/DRC find every symbol and
    footprint without a user-level KiCad configuration."""
    sym_libs = sorted({p.lib_id.split(":")[0] for p in design.PARTS} | {"power"})
    fp_libs = sorted({p.footprint.split(":")[0] for p in design.PARTS})

    def table(kind, libs, var, ext):
        rows = []
        for lib in libs:
            uri = "${KIPRJMOD}/lib/carrier" + ext if lib == "carrier" else "${%s}/%s%s" % (var, lib, ext)
            rows.append('\t(lib (name "%s")(type "KiCad")(uri "%s")(options "")(descr ""))' % (lib, uri))
        return "(%s\n\t(version 7)\n%s\n)\n" % (kind, "\n".join(rows))

    with open(os.path.join(ROOT, "sym-lib-table"), "w") as f:
        f.write(table("sym_lib_table", sym_libs, "KICAD10_SYMBOL_DIR", ".kicad_sym"))
    with open(os.path.join(ROOT, "fp-lib-table"), "w") as f:
        f.write(table("fp_lib_table", fp_libs, "KICAD10_FOOTPRINT_DIR", ".pretty"))


def main():
    write_lib_tables()
    sch = build()
    with open(os.path.join(ROOT, PROJECT + ".kicad_sch"), "w") as f:
        f.write(dump(sch) + "\n")
    print("schematic written")


if __name__ == "__main__":
    main()
