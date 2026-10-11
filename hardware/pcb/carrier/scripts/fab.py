"""Fabrication outputs for JLCPCB (and AISLER / PCBWay): Gerbers + drill (zipped), JLC BOM + CPL, full BOM,
schematic PDF, assembly drawing, ERC/DRC reports, SVG + 3D renders. Runs kicad-cli; plain Python 3.

    python3 scripts/fab.py
"""

import csv
import os
import shutil
import subprocess
import zipfile
from collections import OrderedDict

import design

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
FAB = os.path.join(ROOT, "fab")
CLI = os.environ.get("KICAD_CLI", os.path.expanduser("~/Applications/KiCad.app/Contents/MacOS/kicad-cli"))
SCH = os.path.join(ROOT, "carrier.kicad_sch")
PCB = os.path.join(ROOT, "carrier.kicad_pcb")
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"


def cli(*args):
    out = subprocess.run([CLI] + list(args), capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("kicad-cli %s failed:\n%s%s" % (" ".join(args), out.stdout, out.stderr))
    return out.stdout


def main():
    if os.path.isdir(FAB):
        shutil.rmtree(FAB)
    gerb = os.path.join(FAB, "gerbers")
    os.makedirs(gerb)
    os.makedirs(os.path.join(FAB, "reports"))
    os.makedirs(os.path.join(FAB, "renders"))

    # checks first: ERC (errors fail the build), DRC with schematic parity
    cli("sch", "erc", "--severity-all", "--exit-code-violations", "-o", os.path.join(FAB, "reports", "erc.rpt"), SCH)
    cli("pcb", "drc", "--severity-error", "--schematic-parity", "--exit-code-violations",
        "-o", os.path.join(FAB, "reports", "drc-errors.rpt"), PCB)
    try:
        cli("pcb", "drc", "--severity-all", "--schematic-parity", "-o", os.path.join(FAB, "reports", "drc-all.rpt"), PCB)
    except SystemExit:
        pass

    # Gerbers + Excellon drill (Protel extensions; JLC/AISLER/PCBWay all accept this set)
    cli("pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask", "-o", gerb + os.sep, PCB)
    cli("pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map",
        "--map-format", "pdf", "-o", gerb + os.sep, PCB)
    with zipfile.ZipFile(os.path.join(FAB, "carrier-rev-a-gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(gerb)):
            if not f.endswith(".pdf"):
                z.write(os.path.join(gerb, f), f)

    # Pick and place: kicad-cli -> JLC CPL columns (THT/hand-soldered parts are excluded via the footprint attribute)
    pos = os.path.join(FAB, "reports", "pos-kicad.csv")
    cli("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", "-o", pos, PCB)
    jlc_refs = {p.ref for p in design.PARTS if p.jlc}
    with open(pos) as f, open(os.path.join(FAB, "jlc-cpl.csv"), "w", newline="") as out:
        w = csv.writer(out)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in csv.DictReader(f):
            if r["Ref"] in jlc_refs:
                w.writerow([r["Ref"], r["PosX"] + "mm", r["PosY"] + "mm",
                            "Top" if r["Side"] == "top" else "Bottom", r["Rot"]])

    # BOMs: JLC (SMD parts they place) and the full list (incl. hand-soldered THT parts)
    groups = OrderedDict()
    for p in design.PARTS:
        groups.setdefault((p.value, p.footprint.split(":")[1], p.lcsc, p.jlc, p.note), []).append(p.ref)
    with open(os.path.join(FAB, "jlc-bom.csv"), "w", newline="") as out:
        w = csv.writer(out)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (value, fp, lcsc, jlc, _note), refs in groups.items():
            if jlc:
                w.writerow([value, ",".join(refs), fp, lcsc])
    with open(os.path.join(FAB, "bom-full.csv"), "w", newline="") as out:
        w = csv.writer(out)
        w.writerow(["Qty", "Value", "Designators", "Footprint", "LCSC", "LCSC verified", "Assembly", "Note"])
        for (value, fp, lcsc, jlc, note), refs in groups.items():
            if fp.startswith("MountingHole"):
                continue
            w.writerow([len(refs), value, ",".join(refs), fp, lcsc, "yes" if lcsc in design.VERIFIED_LCSC else ("" if not lcsc else "check"),
                        "JLC SMT" if jlc else "hand-solder / THT", note])

    # Documentation: schematic PDF, netlist, assembly drawing, SVGs and 3D renders
    cli("sch", "export", "pdf", "-o", os.path.join(FAB, "carrier-schematic.pdf"), SCH)
    cli("sch", "export", "netlist", "--format", "kicadsexpr", "-o", os.path.join(FAB, "carrier.net"), SCH)
    cli("pcb", "export", "pdf", "--layers", "F.Fab,Edge.Cuts", "--mode-single", "--include-border-title",
        "-o", os.path.join(FAB, "carrier-assembly-top.pdf"), PCB)
    r = os.path.join(FAB, "renders")
    cli("pcb", "export", "svg", "--layers", "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts", "--mode-single", "--page-size-mode", "2",
        "--exclude-drawing-sheet", "-o", os.path.join(r, "top-layers.svg"), PCB)
    cli("pcb", "export", "svg", "--layers", "B.Cu,B.Silkscreen,B.Mask,Edge.Cuts", "--mode-single", "--page-size-mode", "2",
        "--exclude-drawing-sheet", "--mirror", "-o", os.path.join(r, "bottom-layers.svg"), PCB)
    for side in ("top", "bottom"):
        cli("pcb", "render", "--side", side, "--quality", "high", "-w", "1600", "-h", "1600", "--background", "opaque",
            "-o", os.path.join(r, "render-%s.png" % side), PCB)
    cli("pcb", "render", "--side", "top", "--quality", "high", "-w", "1800", "-h", "1300", "--background", "opaque",
        "--perspective", "--rotate", "-35,0,-20", "--zoom", "0.9", "-o", os.path.join(r, "render-3d.png"), PCB)
    print("fab outputs in", FAB)


if __name__ == "__main__":
    main()
