"""Kit configurations: what a builder may customise, checked against the thermal model.

A kit file (hardware/kits/*.toml) describes one build: zones, TECs, heat rejection,
sensing option and power budget, plus the performance it *claims*. `check_kit`
recomputes the claims with `opod.thermal` so a customised kit can't silently
promise more than its hardware delivers.

Safety limits (setpoint range, trip points, flow interlock) are deliberately NOT
configurable here. They live as constants in `opod.control` and in hardware
cutoffs; see SAFETY.md.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

from .control import Pid, SideController
from .thermal import SideParams, steady_state, tec_operating_point

ALLOWED_TOP = {"kit", "thermal", "sensing", "power", "claims"}
FORBIDDEN_KEYS = {
    "setpoint_min",
    "setpoint_max",
    "water_trip_high",
    "water_trip_low",
    "hot_face_trip",
    "min_flow",
    "heartbeat_timeout",
}
SENSING_OPTIONS = {"none", "load_cells", "pneumatic", "piezo_grid"}
TIERS = {0, 1}
# Non-TEC loads per zone (pump, fans) and shared (controller, hub, sensing), in W.
ZONE_OVERHEAD_W = 25.0
SHARED_OVERHEAD_W = 15.0
PSU_MARGIN = 0.8  # continuous load must stay <= 80 % of PSU rating
TEC_DRIVER_EFFICIENCY = 0.9  # programmable buck / TEC driver
MAX_TEC_CURRENT_A = 6.0  # below the TEC module's 6.4 A Imax


@dataclass(frozen=True)
class Kit:
    name: str
    tier: int
    zones: int
    tec_per_zone: int
    heatsink_k_per_w: float
    max_tec_current_a: float  # per TEC; firmware current cap (lower = less power, slightly less cooling)
    sensing: str
    tec_psu_w_per_zone: float  # TEC supply per zone (one IEC-inlet brick per zone, or a share of one big PSU)
    aux_psu_w: float  # pumps, fans, controller, hub
    claim_min_water_c: float  # sleeper in bed, 25 degC room
    claim_max_water_c: float  # empty bed, 18 degC room

    def side_params(self) -> SideParams:
        return replace(SideParams(), n_tec=self.tec_per_zone, heatsink_r=self.heatsink_k_per_w)

    def controller(self) -> SideController:
        """Controller configured for this kit. The per-TEC current cap becomes the firmware limit
        (the TEC driver's own current limit is set to tec_per_zone * cap; see 04-firmware-protocol.md)."""
        cap = self.max_tec_current_a
        return SideController(i_max=cap, pid=Pid(kp=1.2, ki=0.004, kd=0.0, out_min=-cap, out_max=cap))

    @property
    def zone_current_limit_a(self) -> float:
        return self.tec_per_zone * self.max_tec_current_a


def _walk_keys(d: dict, prefix: str = "") -> list[str]:
    keys = []
    for k, v in d.items():
        keys.append(k)
        if isinstance(v, dict):
            keys += _walk_keys(v, prefix + k + ".")
    return keys


def load_kit(path: Path) -> Kit:
    raw = tomllib.loads(path.read_text())
    unknown = set(raw) - ALLOWED_TOP
    if unknown:
        raise ValueError(f"{path.name}: unknown sections {sorted(unknown)}")
    bad = FORBIDDEN_KEYS & set(_walk_keys(raw))
    if bad:
        raise ValueError(f"{path.name}: safety limits are not configurable per kit: {sorted(bad)}")
    k, t, s, p, c = raw["kit"], raw["thermal"], raw["sensing"], raw["power"], raw["claims"]
    kit = Kit(
        name=k["name"],
        tier=int(k["tier"]),
        zones=int(k["zones"]),
        tec_per_zone=int(t["tec_per_zone"]),
        heatsink_k_per_w=float(t["heatsink_k_per_w"]),
        max_tec_current_a=float(t["max_tec_current_a"]),
        sensing=s["option"],
        tec_psu_w_per_zone=float(p["tec_psu_w_per_zone"]),
        aux_psu_w=float(p["aux_psu_w"]),
        claim_min_water_c=float(c["min_water_c"]),
        claim_max_water_c=float(c["max_water_c"]),
    )
    if kit.tier not in TIERS:
        raise ValueError(f"{path.name}: tier must be one of {TIERS}")
    if kit.zones not in (1, 2):
        raise ValueError(f"{path.name}: zones must be 1 or 2")
    if not 1 <= kit.tec_per_zone <= 6:
        raise ValueError(f"{path.name}: tec_per_zone out of range")
    if not 1.0 <= kit.max_tec_current_a <= MAX_TEC_CURRENT_A:
        raise ValueError(f"{path.name}: max_tec_current_a must be 1..{MAX_TEC_CURRENT_A}")
    if kit.sensing not in SENSING_OPTIONS:
        raise ValueError(f"{path.name}: sensing must be one of {sorted(SENSING_OPTIONS)}")
    return kit


@dataclass(frozen=True)
class KitReport:
    min_water_c: float
    max_water_c: float
    tec_input_w_per_zone: float
    aux_w: float
    problems: tuple[str, ...]


def coldest_water(kit: Kit, t_ambient: float) -> tuple[float, float]:
    """Coldest reachable water (degC) with a sleeper in bed at `t_ambient`, sweeping TEC current up to the
    kit's cap, and the TEC electrical power (W per zone, before driver losses) at that point."""
    p = kit.side_params()
    best_t, best_power = 99.0, 0.0
    i = 1.0
    while i <= kit.max_tec_current_a + 1e-9:
        s = steady_state(p, i, t_ambient, occupied=True, hours=4)
        if s.t_water < best_t:
            best_t = s.t_water
            best_power = tec_operating_point(p, i, s.t_water, s.t_hot)[1]
        i += 0.5
    return best_t, best_power


def check_kit(kit: Kit) -> KitReport:
    p = kit.side_params()
    # Coldest reachable water with a sleeper at 25 degC.
    best_t, best_power = coldest_water(kit, 25.0)
    hot = steady_state(p, -min(3.0, kit.max_tec_current_a), 18.0, occupied=False, hours=4).t_water
    tec_in = best_power / TEC_DRIVER_EFFICIENCY
    aux = kit.zones * ZONE_OVERHEAD_W + SHARED_OVERHEAD_W
    problems = []
    if best_t > kit.claim_min_water_c + 0.1:
        problems.append(f"claims {kit.claim_min_water_c} degC min, model gives {best_t:.1f}")
    if min(hot, 43.0) < kit.claim_max_water_c - 0.1:
        problems.append(f"claims {kit.claim_max_water_c} degC max, model gives {hot:.1f}")
    if kit.claim_max_water_c > 43.0:
        problems.append("max water claim above the 43 degC safety cap")
    if tec_in > kit.tec_psu_w_per_zone * PSU_MARGIN:
        problems.append(f"TEC input {tec_in:.0f} W/zone exceeds {PSU_MARGIN:.0%} of {kit.tec_psu_w_per_zone:.0f} W PSU")
    if aux > kit.aux_psu_w * PSU_MARGIN:
        problems.append(f"aux load {aux:.0f} W exceeds {PSU_MARGIN:.0%} of {kit.aux_psu_w:.0f} W aux PSU")
    return KitReport(best_t, hot, tec_in, aux, tuple(problems))
