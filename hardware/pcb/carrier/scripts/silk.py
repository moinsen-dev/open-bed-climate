"""Post-route silkscreen pass (silk only, no copper changes). Run with KiCad's Python after route.py.

- connector / test point / module references move to F.Fab (assembly drawing), so they no longer sit on the pin labels
- test points get their rail name, the I2C headers their pin order, JP1 its function
- the NTC terminals next to the barrel jack (whose body hides their front labels) get labels on the back as well
"""

import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.abspath(os.path.join(HERE, "..", "carrier.kicad_pcb"))

LABELS = {"TP 12V": "TP 12V", "TP 5V": "TP 5V", "TP 3V3": "TP 3V3", "TP GND": "TP GND",  # unique strings: the
          # idempotent cleanup below removes texts by content, and bare "12V"/"GND" are also terminal pin labels
          "I2C PICO (3V3 GND SDA SCL)": "PICO I2C: 3V3 G SDA SCL", "I2C HUB SHT45 (3V3 GND SDA SCL)": "HUB I2C: 3V3 G SDA SCL",
          "TERM 120R": "120R TERM"}
BACK = {"Z1 NTC WATER": "Z1 NTC WTR: N G", "Z1 NTC HOT": "Z1 NTC HOT: N G"}


def boxes(board, fps):
    """Front obstacles: pads, courtyards, silk texts and silk graphics (in IU)."""
    out = []
    for f in fps:
        for p in f.Pads():
            out.append(p.GetBoundingBox())
        f.BuildCourtyardCaches()
        cy = f.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount():
            out.append(cy.BBox())
        for item in list(f.GraphicalItems()) + [f.Reference(), f.Value()]:
            if item.GetLayer() == pcbnew.F_SilkS:
                out.append(item.GetBoundingBox())
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.F_SilkS:
            out.append(d.GetBoundingBox())
    return out


def add_text(board, s, pos, size, layer=pcbnew.F_SilkS, rot=0.0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(pos)
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
    t.SetTextThickness(pcbnew.FromMM(0.15))
    t.SetTextAngleDegrees(rot)
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)
    return t


def place_free(board, s, fp, obstacles, size=1.0):
    """Put a label next to a footprint where it touches nothing; try sizes 1.0 then 0.8 mm."""
    bb = fp.GetBoundingBox(False)
    cx, cy = bb.GetCenter().x, bb.GetCenter().y
    edge = board.GetBoardEdgesBoundingBox()
    for sz in (size, 0.8):
        gap = pcbnew.FromMM(sz * 0.9)
        cands = [(cx, bb.GetTop() - gap, 0.0), (cx, bb.GetBottom() + gap, 0.0),
                 (bb.GetLeft() - gap, cy, 90.0), (bb.GetRight() + gap, cy, 90.0)]
        for x, y, rot in cands:
            t = add_text(board, s, pcbnew.VECTOR2I(int(x), int(y)), sz, rot=rot)
            tb = t.GetBoundingBox()
            if edge.Contains(tb) and not any(tb.Intersects(o) for o in obstacles):
                obstacles.append(tb)
                return t
            board.Remove(t)
    # nothing free: fall back to above the part at 0.8 mm (DRC reports it as a silk warning)
    t = add_text(board, s, pcbnew.VECTOR2I(int(cx), int(bb.GetTop() - pcbnew.FromMM(0.8))), 0.8)
    obstacles.append(t.GetBoundingBox())
    return t


def main():
    board = pcbnew.LoadBoard(PCB)
    fps = list(board.GetFootprints())
    # idempotent: drop labels from an earlier run of this pass
    ours = set(LABELS.values()) | set(BACK.values())
    stale = [d for d in board.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetText() in ours]
    for d in stale:
        board.Remove(d)
    for f in fps:
        if f.GetReference().startswith(("J", "JP", "TP", "U1", "U2")):
            f.Reference().SetLayer(pcbnew.F_Fab)
    obstacles = boxes(board, fps)
    for f in fps:
        v = f.GetValue()
        if v in LABELS:
            place_free(board, LABELS[v], f, obstacles)
        if v in BACK:
            bb = f.GetBoundingBox(False)
            add_text(board, BACK[v], pcbnew.VECTOR2I(bb.GetCenter().x, bb.GetTop() - pcbnew.FromMM(1.2)), 0.8,
                     layer=pcbnew.B_SilkS)
    pcbnew.SaveBoard(PCB, board)
    print("silkscreen pass done")


if __name__ == "__main__":
    main()
