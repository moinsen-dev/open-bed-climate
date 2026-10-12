"""Write obc-hub-factory.local.yaml: the factory config built from this checkout's components.

obc-hub-factory.yaml pulls the `obc` component from GitHub (main), because that is what an adopted device
builds from. A release must ship the components of the tagged commit, so CI compiles this local variant:

    python3 factory_local.py v0.1.0 && esphome compile obc-hub-factory.local.yaml
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
version = sys.argv[1] if len(sys.argv) > 1 else "dev"
src = (HERE / "obc-hub-factory.yaml").read_text()
out, n = re.subn(
    r"type: git\n(\s+)url: \S+\n\s+ref: \S+\n\s+path: hub/esphome/components\n",
    r"type: local\n\1path: components\n",
    src,
)
out, m = re.subn(r"(\n    version: )\S+\n", rf"\g<1>{version}\n", out)
if (n, m) != (1, 1):
    sys.exit("factory_local.py: obc-hub-factory.yaml no longer has the expected external_components/version block")
(HERE / "obc-hub-factory.local.yaml").write_text(out)
print(f"wrote obc-hub-factory.local.yaml (local components, version {version})")
