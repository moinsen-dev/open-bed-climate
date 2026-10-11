"""Model numbers for the website: kit checks and coldest water by room temperature.

Usage: python -m opod.site_data   (writes website/src/data/model.json; a pytest checks it is up to date)

The website never re-implements the thermal model. It reads this JSON at build time.
Values are rounded (0.1 degC, 1 W) so float noise never makes the file stale.
"""

from __future__ import annotations

import json
from pathlib import Path

from .control import SETPOINT_MAX_C, SETPOINT_MIN_C
from .kit import TEC_DRIVER_EFFICIENCY, check_kit, coldest_water, load_kit
from .schedule import DEFAULT

ROOT = Path(__file__).resolve().parents[4]
KITS_DIR = ROOT / "hardware" / "kits"
DST = ROOT / "website" / "src" / "data" / "model.json"
ROOMS_C = (20.0, 25.0, 28.0, 30.0)


def _r1(x: float) -> float:
    return round(x, 1)


def _kit_entry(path: Path) -> dict:
    kit = load_kit(path)
    report = check_kit(kit)
    rooms = []
    for room in ROOMS_C:
        t, w = coldest_water(kit, room)
        rooms.append({"room_c": _r1(room), "water_c": _r1(t), "tec_input_w": round(w / TEC_DRIVER_EFFICIENCY)})
    return {
        "name": kit.name,
        "check": {
            "min_water_c": _r1(report.min_water_c),
            "max_water_c": _r1(min(report.max_water_c, SETPOINT_MAX_C)),
            "tec_input_w_per_zone": round(report.tec_input_w_per_zone),
            "aux_w": round(report.aux_w),
            "zone_current_limit_a": _r1(kit.zone_current_limit_a),
            "problems": list(report.problems),
        },
        "coldest_by_room": rooms,
    }


def build() -> str:
    data = {
        "generated_by": "python -m opod.site_data (do not edit)",
        "limits": {"setpoint_min_c": SETPOINT_MIN_C, "setpoint_max_c": SETPOINT_MAX_C},
        "schedule_default": {
            "points": [[m, c] for m, c in DEFAULT.points],
            "wake_ramp_min": DEFAULT.wake_ramp_min,
            "wake_target_c": DEFAULT.wake_target_c,
        },
        "kits": {p.stem: _kit_entry(p) for p in sorted(KITS_DIR.glob("*.toml"))},
    }
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(build())
    print(f"wrote {DST}")
