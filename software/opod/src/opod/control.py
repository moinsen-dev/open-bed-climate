"""Per-side temperature controller and safety supervisor.

This is the reference behaviour for the real-time MCU firmware. The supervisor
is written so it can be ported 1:1 to C/Rust: no allocation, no clocks except
the `now` passed in.
"""

from __future__ import annotations

import math

from dataclasses import dataclass, field
from enum import Enum, IntFlag

# Comfort range exposed to users (matches the industry-typical 13..43 degC range).
SETPOINT_MIN_C = 13.0
SETPOINT_MAX_C = 43.0
# Hard limits enforced in firmware, independent of setpoint. A thermal cutoff
# in hardware (bimetal on the cold plate, see 02-electrical-safety.md) backs these up.
WATER_TRIP_HIGH_C = 45.0
WATER_TRIP_LOW_C = 8.0
HOT_FACE_TRIP_C = 75.0
HEARTBEAT_TIMEOUT_S = 10.0
MIN_FLOW_LPM = 0.15
# Heating current taper: full current far below the cap, ramping down to a holding current near it.
HEAT_TAPER_END_C = 48.0
HEAT_TAPER_A_PER_K = 0.5
HEAT_TAPER_MIN_A = 1.0
# Polarity (cool/heat) is switched by a relay in Tier 0. The relay may only switch with zero current:
# current is held at 0 for this long around every polarity change. Small requests are dropped to avoid chatter.
POLARITY_DEADTIME_S = 2.0
POLARITY_DEADBAND_A = 0.3


class Fault(IntFlag):
    NONE = 0
    WATER_OVERTEMP = 1 << 0
    WATER_UNDERTEMP = 1 << 1
    HOT_FACE_OVERTEMP = 1 << 2
    NO_FLOW = 1 << 3
    LEAK = 1 << 4
    SENSOR_INVALID = 1 << 5
    HOST_TIMEOUT = 1 << 6
    LOW_WATER = 1 << 7


# Faults that latch until an explicit clear from the host. Others self-heal.
LATCHING = Fault.WATER_OVERTEMP | Fault.HOT_FACE_OVERTEMP | Fault.LEAK | Fault.SENSOR_INVALID


class Mode(Enum):
    OFF = 0
    RUN = 1
    SAFE = 2  # TECs off, pump on to dissipate residual heat (unless leak)


@dataclass
class Pid:
    kp: float
    ki: float
    kd: float
    out_min: float
    out_max: float
    integral: float = 0.0
    prev_err: float | None = None

    def reset(self) -> None:
        self.integral = 0.0
        self.prev_err = None

    def update(self, err: float, dt: float) -> float:
        deriv = 0.0 if self.prev_err is None else (err - self.prev_err) / dt
        self.prev_err = err
        candidate = self.integral + err * dt
        out = self.kp * err + self.ki * candidate + self.kd * deriv
        # Conditional integration anti-windup: only integrate when not saturating further.
        if self.out_min < out < self.out_max or (out >= self.out_max and err < 0) or (out <= self.out_min and err > 0):
            self.integral = candidate
        out = self.kp * err + self.ki * self.integral + self.kd * deriv
        return max(self.out_min, min(self.out_max, out))


@dataclass
class Inputs:
    t_water: float | None  # None = sensor open/short
    t_hot_face: float | None
    flow_lpm: float
    leak: bool
    water_ok: bool


@dataclass
class Outputs:
    tec_current: float  # A, >0 cool, <0 heat
    pump_on: bool
    fan_duty: float  # 0..1
    mode: Mode
    faults: Fault
    polarity: int = 1  # state of the cool/heat relay: +1 cool, -1 heat (always reported)


@dataclass
class SideController:
    i_max: float = 6.0
    pid: Pid = field(default_factory=lambda: Pid(kp=1.2, ki=0.004, kd=0.0, out_min=-6.0, out_max=6.0))
    setpoint: float | None = None  # None = side off
    faults: Fault = Fault.NONE
    last_heartbeat: float = 0.0
    no_flow_since: float | None = None
    started_at: float | None = None
    polarity: int = 1
    polarity_ready_at: float = 0.0

    def set_target(self, setpoint_c: float | None, now: float) -> None:
        if setpoint_c is not None:
            setpoint_c = max(SETPOINT_MIN_C, min(SETPOINT_MAX_C, setpoint_c))
            if self.setpoint is None:
                self.started_at = now
                self.pid.reset()
        self.setpoint = setpoint_c
        self.heartbeat(now)

    def heartbeat(self, now: float) -> None:
        self.last_heartbeat = now
        self.faults &= ~Fault.HOST_TIMEOUT

    def clear_faults(self) -> None:
        self.faults = Fault.NONE
        self.pid.reset()

    def _evaluate(self, i: Inputs, now: float) -> None:
        f = self.faults & LATCHING  # keep latched ones
        if i.t_water is None or i.t_hot_face is None or not (math.isfinite(i.t_water) and math.isfinite(i.t_hot_face)):
            f |= Fault.SENSOR_INVALID
        else:
            if i.t_water > WATER_TRIP_HIGH_C:
                f |= Fault.WATER_OVERTEMP
            if i.t_water < WATER_TRIP_LOW_C:
                f |= Fault.WATER_UNDERTEMP
            if i.t_hot_face > HOT_FACE_TRIP_C:
                f |= Fault.HOT_FACE_OVERTEMP
        if i.leak:
            f |= Fault.LEAK
        if not i.water_ok:
            f |= Fault.LOW_WATER
        # Flow is only expected while running; allow a 20 s spin-up / priming grace period.
        if self.setpoint is not None and i.flow_lpm < MIN_FLOW_LPM:
            if self.no_flow_since is None:
                self.no_flow_since = now
            if now - self.no_flow_since > 20.0:
                f |= Fault.NO_FLOW
        else:
            self.no_flow_since = None
        if self.setpoint is not None and now - self.last_heartbeat > HEARTBEAT_TIMEOUT_S:
            f |= Fault.HOST_TIMEOUT
        self.faults = f

    def update(self, i: Inputs, now: float, dt: float) -> Outputs:
        self._evaluate(i, now)
        if self.setpoint is None:
            # An off side stays fully off; faults are still reported to the host.
            return Outputs(0.0, False, 0.0, Mode.OFF, self.faults, self.polarity)
        if self.faults:
            self.pid.reset()
            # Keep circulating to spread residual heat, unless water is escaping or missing.
            pump = not (self.faults & (Fault.LEAK | Fault.LOW_WATER))
            return Outputs(0.0, pump, 1.0 if pump else 0.0, Mode.SAFE, self.faults, self.polarity)
        assert i.t_water is not None and i.t_hot_face is not None
        if i.flow_lpm < MIN_FLOW_LPM:
            # Flow interlock: pump spins up / primes first; TECs never run into a dry or stagnant cold plate.
            self.pid.reset()
            return Outputs(0.0, True, 0.2, Mode.RUN, self.faults, self.polarity)
        err = i.t_water - self.setpoint  # positive = too warm = cool harder
        current = max(-self.heat_limit(i.t_water), min(self.i_max, self.pid.update(err, dt)))
        current = self._apply_polarity(current, now)
        # Fans follow the heat-rejection side; in heating mode the "hot" face is the cold one.
        fan = min(1.0, max(0.2, abs(current) / self.i_max))
        return Outputs(current, True, fan, Mode.RUN, self.faults, self.polarity)

    def _apply_polarity(self, current: float, now: float) -> float:
        if abs(current) < POLARITY_DEADBAND_A:
            return 0.0
        wanted = 1 if current > 0 else -1
        if wanted != self.polarity:
            # Zero current first, switch the relay, then wait before driving again.
            self.polarity = wanted
            self.polarity_ready_at = now + POLARITY_DEADTIME_S
        if now < self.polarity_ready_at:
            return 0.0
        return current

    def heat_limit(self, t_water: float) -> float:
        """Max heating current: tapers near the top of the range so the TEC water-side face
        stays below the hardware cutoff (see 02-electrical-safety.md)."""
        return max(HEAT_TAPER_MIN_A, min(self.i_max, HEAT_TAPER_A_PER_K * (HEAT_TAPER_END_C - t_water)))
