"""Autoroute carrier.kicad_pcb with Freerouting, then add the GND pours and fill them.

Run with KiCad's Python:  route.py <freerouting.jar> [java]
Freerouting 1.9.0 runs on Java 17. Net classes (widths/clearances) come from carrier.kicad_pro via the DSN file.
"""

import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PCB = os.path.join(ROOT, "carrier.kicad_pcb")
BUILD = os.path.join(ROOT, "build")
OFFSET = (100.0, 50.0)


def mm(x, y):
    return pcbnew.VECTOR2I_MM(OFFSET[0] + x, OFFSET[1] + y)


def stitch(board, gnd, pitch=3.0, keep=0.75):
    """GND vias on a grid wherever both GND pours are solid around the via (ties the two planes together and
    joins pour islands)."""
    zones = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "GND"]
    import math
    ring = [(keep * math.cos(a * math.pi / 4), keep * math.sin(a * math.pi / 4)) for a in range(8)] + [(0, 0)]
    holes = [(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)) for f in board.GetFootprints()
             for p in f.Pads() if p.HasHole()] + [(pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y))
                                                   for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    n = 0
    y = 1.5
    while y < 99:
        x = 1.5
        while x < 99:
            cx, cy = OFFSET[0] + x, OFFSET[1] + y
            ok = all(z.HitTestFilledArea(z.GetLayer(), pcbnew.VECTOR2I_MM(cx + dx, cy + dy))
                     for z in zones for dx, dy in ring)
            if ok and all((hx - cx) ** 2 + (hy - cy) ** 2 > 1.2 ** 2 for hx, hy in holes):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I_MM(cx, cy))
                v.SetWidth(pcbnew.FromMM(0.6))
                v.SetDrill(pcbnew.FromMM(0.3))
                v.SetNet(gnd)
                board.Add(v)
                holes.append((cx, cy))
                n += 1
            x += pitch
        y += pitch
    return n


def pad_vias(board, gnd):
    """A GND via next to every SMD GND pad on F.Cu, inside the poured area of both layers, so every top pour piece
    reaches the bottom ground plane."""
    import math
    zones = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "GND"]
    ring = [(0.7 * math.cos(a * math.pi / 4), 0.7 * math.sin(a * math.pi / 4)) for a in range(8)] + [(0, 0)]
    holes = [(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)) for f in board.GetFootprints()
             for p in f.Pads() if p.HasHole()] + [(pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y))
                                                   for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    n = 0
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != "GND" or p.HasHole():
                continue
            px, py = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
            if any((hx - px) ** 2 + (hy - py) ** 2 < 2.5 ** 2 for hx, hy in holes):
                continue  # a via/hole is already close
            done = False
            for r in (1.2, 1.5, 1.8, 2.2):
                for k in range(16):
                    cx, cy = px + r * math.cos(k * math.pi / 8), py + r * math.sin(k * math.pi / 8)
                    if all(z.HitTestFilledArea(z.GetLayer(), pcbnew.VECTOR2I_MM(cx + dx, cy + dy))
                           for z in zones for dx, dy in ring) and \
                            all((hx - cx) ** 2 + (hy - cy) ** 2 > 1.2 ** 2 for hx, hy in holes):
                        v = pcbnew.PCB_VIA(board)
                        v.SetPosition(pcbnew.VECTOR2I_MM(cx, cy))
                        v.SetWidth(pcbnew.FromMM(0.6))
                        v.SetDrill(pcbnew.FromMM(0.3))
                        v.SetNet(gnd)
                        board.Add(v)
                        holes.append((cx, cy))
                        n += 1
                        done = True
                        break
                if done:
                    break
    return n


def fragment_vias(board, gnd):
    """Every piece of the top GND pour gets at least one via to the bottom plane."""
    import math
    zones = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "GND"]
    top = [z for z in zones if z.GetLayer() == pcbnew.F_Cu][0]
    vias = [t.GetPosition() for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND"]
    pads = [p.GetPosition() for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == "GND" and p.HasHole()]
    holes = [(pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)) for p in
             [f2.GetPosition() for f in board.GetFootprints() for f2 in f.Pads() if f2.HasHole()] +
             [t.GetPosition() for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]]
    ring = [(0.7 * math.cos(a * math.pi / 4), 0.7 * math.sin(a * math.pi / 4)) for a in range(8)] + [(0, 0)]
    polys = top.GetFilledPolysList(pcbnew.F_Cu)
    n = 0
    for i in range(polys.OutlineCount()):
        outline = polys.Outline(i)
        if any(polys.Contains(v, i) for v in vias + pads):
            continue
        bb = outline.BBox()
        x0, y0 = pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY())
        x1, y1 = x0 + pcbnew.ToMM(bb.GetWidth()), y0 + pcbnew.ToMM(bb.GetHeight())
        y, placed = y0, False
        while y <= y1 and not placed:
            x = x0
            while x <= x1 and not placed:
                if all(z.HitTestFilledArea(z.GetLayer(), pcbnew.VECTOR2I_MM(x + dx, y + dy))
                       for z in zones for dx, dy in ring) and \
                        all((hx - x) ** 2 + (hy - y) ** 2 > 1.2 ** 2 for hx, hy in holes):
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pcbnew.VECTOR2I_MM(x, y))
                    v.SetWidth(pcbnew.FromMM(0.6))
                    v.SetDrill(pcbnew.FromMM(0.3))
                    v.SetNet(gnd)
                    board.Add(v)
                    holes.append((x, y))
                    placed = True
                    n += 1
                x += 0.25
            y += 0.25
    return n


def main():
    jar = sys.argv[1]
    java = sys.argv[2] if len(sys.argv) > 2 else "java"
    os.makedirs(BUILD, exist_ok=True)
    board = pcbnew.LoadBoard(PCB)
    dsn = os.path.join(BUILD, "carrier.dsn")
    ses = os.path.join(BUILD, "carrier.ses")
    assert pcbnew.ExportSpecctraDSN(board, dsn), "DSN export failed"
    for attempt in range(3):  # later passes start from the routed board and only add what is missing
        if os.path.exists(ses):
            os.remove(ses)
        with open(os.path.join(BUILD, "freerouting.log"), "a" if attempt else "w") as log:
            subprocess.check_call([java, "-jar", jar, "-de", dsn, "-do", ses, "-mp", "100", "-l", "en"], stdout=log,
                                  stderr=subprocess.STDOUT)
        assert pcbnew.ImportSpecctraSES(board, ses), "SES import failed"
        conn = board.GetConnectivity()
        conn.RecalculateRatsnest()
        missing = conn.GetUnconnectedCount(False)
        print("freerouting pass %d: %d unrouted" % (attempt + 1, missing))
        if not missing:
            break
        if attempt == 2:
            # last resort for the few links left in the crowded under-module areas: route them narrower
            ns = board.GetDesignSettings().m_NetSettings
            for name, width in (("Power", 0.8), ("Load", 0.5)):
                ns.GetNetClassByName(name).SetTrackWidth(pcbnew.FromMM(width))
            assert pcbnew.ExportSpecctraDSN(board, dsn), "DSN export failed"
            os.remove(ses)
            with open(os.path.join(BUILD, "freerouting.log"), "a") as log:
                subprocess.check_call([java, "-jar", jar, "-de", dsn, "-do", ses, "-mp", "50", "-l", "en"], stdout=log,
                                      stderr=subprocess.STDOUT)
            assert pcbnew.ImportSpecctraSES(board, ses), "SES import failed"
            conn = board.GetConnectivity()
            conn.RecalculateRatsnest()
            print("narrow fallback pass: %d unrouted" % conn.GetUnconnectedCount(False))
            break
        assert pcbnew.ExportSpecctraDSN(board, dsn), "DSN export failed"

    # GND pours on both layers (thermal reliefs on pads); the bottom one is the main ground plane
    gnd = board.FindNet("GND")
    for layer, prio in ((pcbnew.B_Cu, 0), (pcbnew.F_Cu, 0)):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetZoneName("GND %s" % board.GetLayerName(layer))
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(pcbnew.FromMM(0.3))
        z.SetMinThickness(pcbnew.FromMM(0.25))
        z.SetThermalReliefGap(pcbnew.FromMM(0.4))
        z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.5))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline()
        o.NewOutline()
        for x, y in ((0.2, 0.2), (99.8, 0.2), (99.8, 99.8), (0.2, 99.8)):
            o.Append(mm(x, y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("pad vias:", pad_vias(board, gnd))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("stitching vias:", stitch(board, gnd))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("pour-piece vias:", fragment_vias(board, gnd))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("routed and filled")


if __name__ == "__main__":
    main()
