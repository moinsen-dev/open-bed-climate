"""Lumped thermal model of one bed side: TEC bank -> water loop -> cover/body.

Used for sizing (how many TECs, how much heatsink) and to test the controller
against a plant before any hardware exists. Parameters are first-order
estimates; replace them with measured values once a prototype exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field

WATER_CP = 4186.0  # J/(kg*K)
K0 = 273.15


@dataclass(frozen=True)
class TecModule:
    """Lumped TEC model. Defaults: TEC1-12706 fitted to its datasheet maxima (see from_datasheet)."""

    seebeck: float = 0.04533  # V/K, module total
    resistance: float = 1.7825  # ohm
    conductance: float = 0.4674  # W/K
    i_max: float = 6.4  # A

    @classmethod
    def from_datasheet(cls, q_max: float, dt_max: float, v_max: float, i_max: float, t_hot_c: float = 25.0) -> "TecModule":
        """Fit S, R, K so the model reproduces the datasheet's own Qmax (dT=0), dTmax (Q=0) and Vmax (at dTmax),
        all at Imax and the given hot-side temperature. Three linear equations, solved in closed form."""
        th = t_hot_c + K0
        tc = th - dt_max
        # Qmax:  S*I*Th - I^2 R/2 = q_max        Vmax:  S*dTmax + I*R = v_max
        # -> R = (v_max - S*dt_max)/I  substituted into the Qmax equation:
        s = (q_max + 0.5 * i_max * v_max) / (i_max * th + 0.5 * i_max * dt_max)
        r = (v_max - s * dt_max) / i_max
        k = (s * i_max * tc - 0.5 * i_max**2 * r) / dt_max  # dTmax: Q = 0
        return cls(seebeck=s, resistance=r, conductance=k, i_max=i_max)

    def cold_side_heat(self, current: float, t_cold_c: float, t_hot_c: float) -> float:
        """Heat pumped out of the cold side [W]. Negative current = heating mode."""
        tc = t_cold_c + K0
        dt = t_hot_c - t_cold_c
        return self.seebeck * current * tc - 0.5 * current**2 * self.resistance - self.conductance * dt

    def voltage(self, current: float, t_cold_c: float, t_hot_c: float) -> float:
        return self.seebeck * (t_hot_c - t_cold_c) + current * self.resistance

    def power(self, current: float, t_cold_c: float, t_hot_c: float) -> float:
        return abs(self.voltage(current, t_cold_c, t_hot_c) * current)


@dataclass(frozen=True)
class SideParams:
    n_tec: int = 3
    tec: TecModule = field(default_factory=TecModule)
    loop_water_kg: float = 1.2  # water in cover channels + tubing + cold plate share
    loop_extra_heat_cap: float = 800.0  # J/K, cold plates, cover material
    ua_body: float = 6.0  # W/K, body/mattress surface <-> water channels (person in bed)
    ua_ambient: float = 2.5  # W/K, tubing + cover <-> room
    ua_cold_plate: float = 12.0  # W/K per TEC, water <-> TEC cold face (cold plate + paste)
    heatsink_r: float = 0.11  # K/W, hot face bank -> ambient per side (fans on)
    pump_heat_w: float = 3.0  # pump losses end up in the water

    @property
    def heat_capacity(self) -> float:
        return self.loop_water_kg * WATER_CP + self.loop_extra_heat_cap


@dataclass
class SideState:
    t_water: float  # degC
    t_hot: float  # degC, TEC hot face / heatsink


@dataclass(frozen=True)
class StepResult:
    q_water_removed: float  # W, net heat pumped out of the water by TECs (negative = added)
    electrical_w: float
    t_cold_face: float


def tec_operating_point(p: SideParams, current: float, t_water: float, t_hot: float) -> tuple[float, float, float]:
    """Solve the cold-face temperature where cold-plate conduction matches TEC heat pumping.

    Returns (q_from_water_total_W, electrical_total_W, t_cold_face_C).
    """
    lo, hi = t_water - 80.0, t_water + 80.0
    t_cold = t_water
    for _ in range(80):  # bisection on f(tc) = q_tec(tc) - ua*(t_water - tc)
        t_cold = 0.5 * (lo + hi)
        f = p.tec.cold_side_heat(current, t_cold, t_hot) - p.ua_cold_plate * (t_water - t_cold)
        # f increases with t_cold
        if f > 0:
            hi = t_cold
        else:
            lo = t_cold
    q_one = p.ua_cold_plate * (t_water - t_cold)
    return q_one * p.n_tec, p.tec.power(current, t_cold, t_hot) * p.n_tec, t_cold


def step(
    p: SideParams,
    s: SideState,
    current: float,
    t_ambient: float,
    occupied: bool,
    dt: float,
    t_skin: float = 34.0,
) -> StepResult:
    """Advance one side by dt seconds. current >0 cools the water, <0 heats it."""
    current = max(-p.tec.i_max, min(p.tec.i_max, current))
    q_tec, p_el, t_cold = tec_operating_point(p, current, s.t_water, s.t_hot)
    q_body = p.ua_body * (t_skin - s.t_water) if occupied else 0.0
    q_amb = p.ua_ambient * (t_ambient - s.t_water)
    s.t_water += dt * (q_body + q_amb + p.pump_heat_w - q_tec) / p.heat_capacity

    # Hot side: heat rejected = pumped heat + electrical input; heatsink is quasi-static (small mass vs loop)
    q_reject = q_tec + p_el
    s.t_hot = t_ambient + q_reject * p.heatsink_r
    return StepResult(q_tec, p_el, t_cold)


def steady_state(p: SideParams, current: float, t_ambient: float, occupied: bool = True, hours: float = 6.0) -> SideState:
    s = SideState(t_water=t_ambient, t_hot=t_ambient)
    for _ in range(int(hours * 3600 / 5)):
        step(p, s, current, t_ambient, occupied, 5.0)
    return s
