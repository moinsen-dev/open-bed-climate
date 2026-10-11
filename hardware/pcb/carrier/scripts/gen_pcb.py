"""Generate carrier.kicad_pcb (placement, nets, outline, silkscreen, net classes) from design.py.

Run with KiCad's Python (it imports pcbnew). Board coordinates: (0, 0) = top-left corner of the 100 x 100 mm board,
y down; the board sits at OFFSET on the KiCad page. Routing is done afterwards by route.py (Freerouting).
"""

import json
import os

import pcbnew

import design
import gen_sch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SHARE = gen_sch.SHARE
OFFSET = (100.0, 50.0)
W = H = 100.0
PCB = os.environ.get("CARRIER_PCB_OUT", os.path.join(ROOT, "carrier.kicad_pcb"))


def mm(x, y):
    return pcbnew.VECTOR2I_MM(OFFSET[0] + x, OFFSET[1] + y)


def fp_path(fpid):
    lib, name = fpid.split(":")
    if lib == "carrier":
        return os.path.join(ROOT, "lib", "carrier.pretty"), name
    return os.path.join(SHARE, "footprints", lib + ".pretty"), name


# ------------------------------------------------------------------------------------------------ board & parts
board = pcbnew.CreateEmptyBoard()
nets = {}
for n in design.nets():
    ni = pcbnew.NETINFO_ITEM(board, n)
    board.Add(ni)
    nets[n] = ni

# Unconnected pins: KiCad names them unconnected-(REF-PIN-PadN) when it updates a board from the schematic;
# using the same names keeps the schematic-parity DRC clean.
PIN_NAMES = {}
for part in design.PARTS:
    sym = gen_sch.apply_overrides(part.lib_id, gen_sch.flat_symbol(part.lib_id))
    PIN_NAMES[part.ref] = {num: name for num, name, _t, _x, _y, _a in gen_sch.pins_of(sym)}


def nc_net(part, num):
    name = PIN_NAMES[part.ref].get(num, "")
    label = "%s-%s-Pad%s" % (part.ref, name, num) if name and name != "~" else "%s-Pad%s" % (part.ref, num)
    n = "unconnected-(%s)" % label.replace("/", "{slash}")
    if n not in nets:
        nets[n] = pcbnew.NETINFO_ITEM(board, n)
        board.Add(nets[n])
    return nets[n]


# MSOP-10: KiCad's pads are 0.35 mm wide (0.15 mm gaps); TI's DGS land pattern uses 0.30 mm, which gives 0.2 mm gaps
# and keeps one 0.2 mm clearance for the whole board.
FINE_PITCH = ("Package_SO:MSOP-10_3x3mm_P0.5mm",)

FP = {}
for part in design.PARTS:
    libdir, name = fp_path(part.footprint)
    fp = pcbnew.FootprintLoad(libdir, name)
    assert fp is not None, part.footprint
    fp.SetFPID(pcbnew.LIB_ID(part.footprint.split(":")[0], name))
    fp.SetReference(part.ref)
    fp.SetValue(part.value)
    fp.SetPath(pcbnew.KIID_PATH("/" + gen_sch.uid("sym", part.ref)))
    if part.lcsc:
        fp.SetField("LCSC", part.lcsc)
        fp.GetField("LCSC").SetVisible(False)
    if part.jlc or part.ref.startswith("H"):  # SMD refs live on the assembly drawing (F.Fab), not on the silkscreen
        fp.Reference().SetVisible(False)
    else:
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    for pad in fp.Pads():
        num = pad.GetNumber()
        if num in part.pins and part.pins[num]:
            pad.SetNet(nets[part.pins[num]])
        elif num in part.pins:
            pad.SetNet(nc_net(part, num))
        if part.footprint in FINE_PITCH:
            sz = pad.GetSize()
            if sz.x < sz.y:
                pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.30), sz.y))
            else:
                pad.SetSize(pcbnew.VECTOR2I(sz.x, pcbnew.FromMM(0.30)))
    board.Add(fp)
    FP[part.ref] = fp

BY_VALUE = {}
for part in design.PARTS:
    BY_VALUE.setdefault(part.value, []).append(part.ref)


def ref_of(value):
    refs = BY_VALUE[value]
    assert len(refs) == 1, (value, refs)
    return refs[0]


def place(ref, x, y, rot=0.0):
    fp = FP[ref]
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(mm(x, y))


def crt(ref, margin=0.0):
    """Courtyard bbox of a placed footprint in board coordinates: (x0, y0, x1, y1)."""
    fp = FP[ref]
    fp.BuildCourtyardCaches()
    poly = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = poly.BBox() if poly.OutlineCount() else fp.GetBoundingBox(False)
    x0 = pcbnew.ToMM(bb.GetX()) - OFFSET[0]
    y0 = pcbnew.ToMM(bb.GetY()) - OFFSET[1]
    return (x0 - margin, y0 - margin, x0 + pcbnew.ToMM(bb.GetWidth()) + margin, y0 + pcbnew.ToMM(bb.GetHeight()) + margin)


# ------------------------------------------------------------------------------------------------ silkscreen
def text(s, x, y, size=1.0, rot=0.0, layer=pcbnew.F_SilkS, bold=False, thick=None):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(mm(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
    t.SetTextThickness(pcbnew.FromMM(thick or max(0.15, size * 0.15)))
    t.SetTextAngleDegrees(rot)
    t.SetBold(bold)
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)
    return t


def pin_labels(ref, labels, side):
    """Short per-pin labels next to a terminal (side: 'below', 'above', 'left')."""
    fp = FP[ref]
    for pad in fp.Pads():
        lab = labels.get(pad.GetNumber())
        if not lab:
            continue
        px = pcbnew.ToMM(pad.GetPosition().x) - OFFSET[0]
        py = pcbnew.ToMM(pad.GetPosition().y) - OFFSET[1]
        x0, y0, x1, y1 = crt(ref)
        if side == "below":
            text(lab, px, y1 + 0.75, 0.8)
        elif side == "above":
            text(lab, px, y0 - 0.75, 0.8)
        else:
            text(lab, x0 - 0.75, py, 0.8, rot=90)


# ------------------------------------------------------------------------------------------------ placement
occupied = []  # (x0, y0, x1, y1) keep-outs for the packer
UNPLACED = []


def occupy(ref, margin=0.25):
    occupied.append(crt(ref, margin))


def overlaps(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def cell_layout(cols, margin):
    """Columns of refs, stacked vertically within a column, columns side by side. Returns (w, h, [(ref, dx, dy)])
    where dx/dy move each footprint from its origin to its slot."""
    out, x, h = [], 0.0, 0.0
    for col in cols:
        y, cw = 0.0, 0.0
        for ref in col:
            place(ref, 0, 0, 0.0)
            bx0, by0, bx1, by1 = crt(ref, margin)
            out.append((ref, x - bx0, y - by0))
            y += by1 - by0
            cw = max(cw, bx1 - bx0)
        x += cw
        h = max(h, y)
    return x, h, out


def pack(items, region, step=0.25, margin=0.25, rot=0.0, fallback=None):
    """Greedy packer: first free spot in row-major order (rows top to bottom) inside region (x0, y0, x1, y1),
    then in the fallback region. An item is a ref, or a cell = list of columns of refs (kept together)."""
    rx0, ry0, rx1, ry1 = region
    for item in items:
        if isinstance(item, list):
            w, h, slots = cell_layout(item, margin)
        else:
            if fallback and not fits(item, region, step, margin, rot):
                pack([item], fallback, step, margin, rot)
                continue
            place(item, 0, 0, rot)
            bx0, by0, bx1, by1 = crt(item, margin)
            w, h, slots = bx1 - bx0, by1 - by0, [(item, -bx0, -by0)]
        done = False
        y = ry0
        while y + h <= ry1 + 1e-6 and not done:
            x = rx0
            while x + w <= rx1 + 1e-6:
                cand = (x, y, x + w, y + h)
                if not any(overlaps(cand, o) for o in occupied):
                    for ref, dx, dy in slots:
                        place(ref, x + dx, y + dy, FP[ref].GetOrientationDegrees() if isinstance(item, list) else rot)
                    occupied.append(cand)
                    done = True
                    break
                x += step
            y += step
        if not done:  # park it off-board so the layout can be inspected; the run fails at the end
            for ref, _dx, _dy in slots:
                UNPLACED.append(ref)
                place(ref, 110.0 + 12 * (len(UNPLACED) % 4), 10.0 * (len(UNPLACED) // 4), rot)


def fits(ref, region, step, margin, rot):
    place(ref, 0, 0, rot)
    bx0, by0, bx1, by1 = crt(ref, margin)
    w, h = bx1 - bx0, by1 - by0
    y = region[1]
    while y + h <= region[3] + 1e-6:
        x = region[0]
        while x + w <= region[2] + 1e-6:
            if not any(overlaps((x, y, x + w, y + h), o) for o in occupied):
                return True
            x += step
        y += step
    return False


def edge_row(values, edge, start, gap=0.3):
    """Terminals along an edge, wire entry facing out. Returns the refs in placement order."""
    refs = [ref_of(v) for v in values]
    cursor = start
    for ref in refs:
        if edge == "top":
            rot = 180.0
        elif edge == "bottom":
            rot = 0.0
        else:  # right
            rot = 90.0
        place(ref, 0, 0, rot)
        x0, y0, x1, y1 = crt(ref)
        if edge == "top":
            dx, dy = cursor - x0, 0.4 - y0  # front (wire entry) flush with the edge
            cursor += (x1 - x0) + gap
        elif edge == "bottom":
            dx, dy = cursor - x0, (H - 0.4) - y1
            cursor += (x1 - x0) + gap
        else:
            dx, dy = (W - 0.4) - x1, cursor - y0
            cursor += (y1 - y0) + gap
        place(ref, dx, dy, rot)
        occupy(ref, 0.2)
    return refs


def zone_values(z):
    return ["Z%d CUTOFF LOOP" % z, "Z%d ZONE RELAY COIL" % z, "Z%d POL A" % z, "Z%d POL B" % z, "Z%d PUMP" % z,
            "Z%d FAN" % z, "Z%d FLOW +5V GND SIG" % z, "Z%d NTC WATER" % z, "Z%d NTC HOT" % z]


TERM_PINS = {  # pin labels per terminal kind
    "CUTOFF LOOP": ({"1": "12V", "2": "RET"}, "CUTOFF LOOP"),
    "ZONE RELAY COIL": ({"1": "+", "2": "-"}, "ZONE RLY"),
    "POL A": ({"1": "+", "2": "-"}, "POL A"),
    "POL B": ({"1": "+", "2": "-"}, "POL B"),
    "PUMP": ({"1": "+", "2": "-"}, "PUMP"),
    "FAN": ({"1": "+", "2": "-"}, "FAN"),
    "FLOW +5V GND SIG": ({"1": "5V", "2": "G", "3": "S"}, "FLOW"),
    "NTC WATER": ({"1": "N", "2": "G"}, "NTC WTR"),
    "NTC HOT": ({"1": "N", "2": "G"}, "NTC HOT"),
}

# Edge terminals
top = edge_row(zone_values(0), "top", 0.6)
bottom = edge_row(zone_values(1), "bottom", 0.6)
right = edge_row(["RS485 A B GND", "LEAK +12V GND SIG", "LEVEL +5V GND SIG"], "right", 11.9)
right += edge_row(["12V IN", "STAR GND"], "right", 55.0)
jack = ref_of("12V IN 5.5x2.5 (Solo only, <=5 A)")
place(jack, 0, 0, 180.0)
x0, y0, x1, y1 = crt(jack)
place(jack, (W - 0.2) - x1, crt(right[-1])[3] + 0.4 - y0, 180.0)
occupy(jack, 0.2)

# Modules, USB ends at the left edge
# Socketed modules sit 8.5 mm above the board: low SMD parts may go between their pin rows (unplug the module to
# probe them). Only the socket rows themselves (plus the USB plug overhang at the left edge) are kept clear.
place(design.ESP.ref, 60.4, 22.4, 270.0)
place(design.PICO.ref, 3.6, 70.6, 90.0)
for ref in (design.ESP.ref, design.PICO.ref):
    for pad in FP[ref].Pads():
        px = pcbnew.ToMM(pad.GetPosition().x) - OFFSET[0]
        py = pcbnew.ToMM(pad.GetPosition().y) - OFFSET[1]
        occupied.append((px - 1.6, py - 1.6, px + 1.6, py + 1.6))
occupied.append((0.0, 20.6, 6.0, 47.2))  # ESP32 USB end
occupied.append((0.0, 50.0, 3.0, 73.0))  # Pico USB end
ESP_ANTENNA = (61.6, 20.5, 71.2, 47.4)  # copper keep-out under the WROOM antenna (both layers)

# Mounting holes (M3)
holes = [r for r in FP if r.startswith("H")]
for ref, (x, y) in zip(sorted(holes), [(4.0, 16.4), (66.4, 16.4), (4.0, 83.8), (58.2, 51.4)]):
    place(ref, x, y)
    occupy(ref, 0.3)

# Silk labels for the terminals (before packing, so the packer keeps them clear)
for ref in top + bottom:
    v = FP[ref].GetValue()
    kind = v[3:]
    pins, name = TERM_PINS[kind]
    x0, y0, x1, y1 = crt(ref)
    if ref in top:
        pin_labels(ref, pins, "below")
        text("Z0 " + name, (x0 + x1) / 2, y1 + 1.85, 0.8)
        occupied.append((x0, y1, x1, y1 + 2.5))
    else:
        pin_labels(ref, pins, "above")
        text("Z1 " + name, (x0 + x1) / 2, y0 - 1.85, 0.8)
        occupied.append((x0, y0 - 2.5, x1, y0))
RIGHT_PINS = {"RS485 A B GND": ({"1": "A", "2": "B", "3": "G"}, "RS-485"),
              "LEAK +12V GND SIG": ({"1": "12V", "2": "G", "3": "S"}, "LEAK"),
              "LEVEL +5V GND SIG": ({"1": "5V", "2": "G", "3": "S"}, "LEVEL"),
              "12V IN": ({"1": "+12V", "2": "GND"}, "12V IN"),
              "STAR GND": ({"1": "GND", "2": "GND"}, "STAR GND")}
for ref in right:
    pins, name = RIGHT_PINS[FP[ref].GetValue()]
    pin_labels(ref, pins, "left")
    x0, y0, x1, y1 = crt(ref)
    text(name, x0 - 1.9, (y0 + y1) / 2, 0.8, rot=90)
    occupied.append((x0 - 2.6, y0, x0, y1))
text("12V 5.5x2.5", crt(jack)[0] - 1.2, (crt(jack)[1] + crt(jack)[3]) / 2, 0.8, rot=90)
occupied.append(ESP_ANTENNA)


# ------------------------------------------------------------------------------------------------ packing groups
def refs_in(block, prefix=None, exclude=()):
    return [p.ref for p in design.PARTS if p.block == block and (prefix is None or p.ref.startswith(prefix))
            and p.ref not in exclude and p.ref not in top + bottom + right and p.ref != jack]


def ordered(block):
    """Block parts in design order (drivers stay together), terminals/modules/holes excluded."""
    return [r for r in refs_in(block) if not r.startswith(("J", "U1", "U2", "H")) or r.startswith(("JP",))]


hub_i2c = ref_of("I2C HUB SHT45 (3V3 GND SDA SCL)")
pico_i2c = ref_of("I2C PICO (3V3 GND SDA SCL)")

# zone 0 strip between the top terminals and the ESP32; zone 1 strip between the Pico and the bottom terminals
def with_net(net, block="power"):
    return [p.ref for p in design.PARTS if p.block == block and net in p.pins.values() and p.ref.startswith(("D", "C"))
            and len(p.pins) == 2]


def on_net(net, prefixes):
    return [p.ref for p in design.PARTS if net in p.pins.values() and p.ref.startswith(prefixes) and p.ref in FP
            and not p.ref.startswith("J")]


def cells(block):
    """Functional cells of a block: each driver channel (gate R, pull-down, MOSFET, flyback diodes), each protected
    input (series R, pull-up, clamp, cap) and each NTC channel (divider R, RC) stays together; the rest are singles."""
    out, used = [], set()
    for p in design.PARTS:
        if p.block != block:
            continue
        for net in p.pins.values():
            if not net:
                continue
            if net.endswith("_G") and p.ref.startswith("Q"):
                gate, drain = net, p.pins["3"]
                rs = on_net(gate, ("R",))
                out.append([rs, [p.ref]])
                used.update(rs + [p.ref])
            elif p.ref.startswith("D") and p.lib_id == "Diode:BAT54S" and net not in ("GND", "+3V3"):
                rs = [r for r in on_net(net, ("R",))]
                cs = [c for c in on_net(net, ("C",))]
                out.append([rs, [p.ref]] + ([cs] if cs else []))
                used.update(rs + [p.ref] + cs)
            elif net.startswith("ADS_AIN") and p.ref.startswith("C"):
                (r1k,) = [r for r in on_net(net, ("R",))]
                node = [n for n in design.PARTS if n.ref == r1k][0].pins
                node = node["1"] if node["2"] == net else node["2"]
                rdiv = [r for r in on_net(node, ("R",)) if r != r1k]
                out.append([rdiv + [r1k], [p.ref]])
                used.update(rdiv + [r1k, p.ref])
    singles = [r for r in ordered(block) if r not in used and r not in flybacks(block)]
    return out + singles


def flybacks(block):
    """Flyback diodes of a zone: they carry 12 V and the coil/motor current, so they sit in the strip between the
    module and the terminal row (12 V traces can't pass between socket pins)."""
    return [p.ref for p in design.PARTS if p.block == block and p.ref.startswith("D") and p.lib_id == "Device:D_Schottky"]


esp_feed = with_net("ESP_5V")
pico_feed = with_net("VSYS") + with_net("+3V3")
pack(flybacks("zone0"), (6.0, 14.6, 61.4, 20.4))
pack([r for r in ordered("mcu") if r != hub_i2c] + esp_feed + cells("zone0"), (6.0, 14.6, 61.4, 44.6))
pack([pico_i2c], (8.0, 74.0, 54.0, 85.0), rot=90.0)
pack(flybacks("zone1"), (3.4, 72.6, 55.0, 85.7))
pack(pico_feed + cells("zone1") + cells("inputs"), (3.4, 54.0, 55.0, 85.7))
# ADC + RS-485 in the right column next to the NTC/RS-485 terminals
tps_right = [ref_of("TP 3V3"), ref_of("TP GND")]
pack([hub_i2c], (71.6, 13.6, 86.0, 47.6), rot=90.0)  # signal-only: its traces may pass between socket pins
pack(ordered("rs485") + cells("adc") + tps_right, (71.6, 13.6, 86.0, 47.6))
# power section: right of the Pico, next to the 12 V inputs
def area(ref):
    place(ref, 0, 0)
    x0, y0, x1, y1 = crt(ref)
    return (x1 - x0) * (y1 - y0)


def put(value, x, y, rot=0.0):
    """Place by courtyard top-left corner (board coordinates)."""
    ref = ref_of(value)
    place(ref, 0, 0, rot)
    x0, y0, _x1, _y1 = crt(ref)
    place(ref, x - x0, y - y0, rot)
    occupy(ref, 0.2)
    return ref


# power path, hand-placed: fuse + TVS (row A), buck IC + P-FET + catch diode (row B), inductor + bulk caps (row C)
big = [put("5A mini blade", 62.2, 48.2), put("SMBJ15A", 79.2, 49.0),
       put("LM2596S-5.0", 55.0, 56.0), put("AOD4185", 72.6, 56.0, 90.0), put("SS54", 80.6, 56.0, 90.0),
       put("33uH 4A", 55.0, 68.4), put("100u 35V", 69.4, 68.4, 90.0), put("220u 16V", 77.4, 68.4, 90.0)]
pack(sorted([r for r in ordered("power") if r not in esp_feed + pico_feed + big + tps_right], key=area, reverse=True),
     (54.6, 48.0, 86.0, 86.0), fallback=(71.6, 13.6, 86.0, 47.6))

# ------------------------------------------------------------------------------------------------ keep-out, outline
def rule_area(name, box, layers):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for layer in layers:
        ls.AddLayer(layer)
    z.SetLayerSet(ls)
    x0, y0, x1, y1 = box
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(mm(x, y))
    board.Add(z)


rule_area("ESP32 antenna keep-out", ESP_ANTENNA, (pcbnew.F_Cu, pcbnew.B_Cu))

rect = pcbnew.PCB_SHAPE(board)
rect.SetShape(pcbnew.SHAPE_T_RECT)
rect.SetStart(mm(0, 0))
rect.SetEnd(mm(W, H))
rect.SetLayer(pcbnew.Edge_Cuts)
rect.SetWidth(pcbnew.FromMM(0.1))
board.Add(rect)

# back-side notes, inside the pad-free area between the ESP32 socket rows
text("OPEN BED CLIMATE - Tier 0 carrier", 33.7, 26.2, 1.5, layer=pcbnew.B_SilkS, bold=True)
text("Rev A - UNTESTED - review before use", 33.7, 28.8, 1.2, layer=pcbnew.B_SilkS, bold=True)
for i, line in enumerate([
    "CERN-OHL-S-2.0 - hardware/pcb/carrier",
    "Signals + 12 V aux only. TEC path (24 V, DPS,",
    "20 A fuse, relays, TECs) stays OFF this board.",
    "STAR GND: one wire to the star point at the DPS.",
    "12 V in: 5 A (1 oz Cu), 7.5 A only with 2 oz.",
    "Zone relay coil fed ONLY via its CUTOFF LOOP.",
    "Fail-off: 4.7k gate pull-downs (RP2350-E9).",
    "Inputs: open wire = HIGH = fault. Pins: board.rs",
]):
    text(line, 33.7, 31.4 + i * 1.75, 1.0, layer=pcbnew.B_SilkS)
text("OPEN BED CLIMATE carrier  Rev A - UNTESTED", 27.0, 49.1, 1.1, bold=True)

# design rules (JLCPCB 2-layer standard: 0.127 mm track/space; we keep margin)
ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(0.15)
ds.m_TrackMinWidth = pcbnew.FromMM(0.2)
ds.m_ViasMinSize = pcbnew.FromMM(0.6)
ds.m_MinThroughDrill = pcbnew.FromMM(0.3)
ds.m_ViasMinAnnularWidth = pcbnew.FromMM(0.15)
ds.m_CopperEdgeClearance = pcbnew.FromMM(0.3)
ds.m_HoleClearance = pcbnew.FromMM(0.25)
ds.m_HoleToHoleMin = pcbnew.FromMM(0.5)
ds.m_SilkClearance = pcbnew.FromMM(0.0)

pcbnew.SaveBoard(PCB, board)

# ------------------------------------------------------------------------------------------------ project file
NETCLASSES = [
    {"name": "Default", "clearance": 0.2, "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3},
    {"name": "Power", "clearance": 0.3, "track_width": 1.5, "via_diameter": 1.0, "via_drill": 0.6},
    {"name": "Load", "clearance": 0.25, "track_width": 0.8, "via_diameter": 0.8, "via_drill": 0.4},
]
base = {"bus_width": 12, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0,
        "microvia_diameter": 0.3, "microvia_drill": 0.1, "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647,
        "schematic_color": "rgba(0, 0, 0, 0.000)", "tuning_profile": "", "wire_width": 6}
classes = []
for i, nc in enumerate(NETCLASSES):
    d = dict(base)
    d.update(nc)
    d["priority"] = 2147483647 if nc["name"] == "Default" else i
    classes.append(d)
patterns = [{"netclass": "Power", "pattern": n} for n in sorted(design.POWER_NETS)] + \
           [{"netclass": "Load", "pattern": n} for n in sorted(design.LOAD_NETS)]
pro_path = os.path.join(ROOT, "carrier.kicad_pro")
pro = json.load(open(pro_path)) if os.path.exists(pro_path) else {}
pro.setdefault("meta", {"filename": "carrier.kicad_pro", "version": 3})
pro.pop("sheets", None)
pro["net_settings"] = {"classes": classes, "meta": {"version": 4}, "net_colors": None,
                       "netclass_assignments": None, "netclass_patterns": patterns}
bd = pro.setdefault("board", {}).setdefault("design_settings", {})
bd["rules"] = {"min_clearance": 0.15, "min_track_width": 0.2, "min_via_diameter": 0.6, "min_through_hole_diameter": 0.3,
               "min_via_annular_width": 0.15, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.25,
               "min_hole_to_hole": 0.5, "min_silk_clearance": 0.0, "min_text_height": 0.8, "min_text_thickness": 0.12,
               "solder_mask_to_copper_clearance": 0.0, "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1,
               "min_resolved_spokes": 1, "allow_blind_buried_vias": False, "allow_microvias": False}
bd["rule_severities"] = {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore",
                         "silk_overlap": "warning", "silk_over_copper": "warning", "text_height": "warning"}
with open(pro_path, "w") as f:
    json.dump(pro, f, indent=2)
    f.write("\n")
print("board written: %d footprints" % len(FP))
if UNPLACED:
    raise SystemExit("no room for: " + " ".join(UNPLACED))
