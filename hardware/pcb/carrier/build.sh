#!/usr/bin/env bash
# Regenerate the carrier PCB from scripts/design.py: library -> schematic (ERC) -> board -> Freerouting -> fab outputs.
# Needs KiCad 10 (kicad-cli + its bundled Python) and Freerouting 1.9.0 on Java 17
# (freerouting-1.9.0.jar from https://github.com/freerouting/freerouting/releases/tag/v1.9.0).
#   FREEROUTING_JAR=/path/to/freerouting-1.9.0.jar JAVA=/opt/homebrew/opt/openjdk@17/bin/java ./build.sh
set -euo pipefail
cd "$(dirname "$0")"
KICAD_APP=${KICAD_APP:-$HOME/Applications/KiCad.app}
KPY="$KICAD_APP/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
export KICAD_CLI=${KICAD_CLI:-$KICAD_APP/Contents/MacOS/kicad-cli}
: "${FREEROUTING_JAR:?set FREEROUTING_JAR to freerouting-1.9.0.jar}"
JAVA=${JAVA:-java}

python3 scripts/gen_lib.py
python3 scripts/gen_sch.py
"$KPY" scripts/gen_pcb.py
"$KPY" scripts/route.py "$FREEROUTING_JAR" "$JAVA"
"$KPY" scripts/silk.py
python3 scripts/fab.py
