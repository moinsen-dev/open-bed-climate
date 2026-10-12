"""Per-zone heat-rejection fan and pump duty: the reference behaviour for the firmware's PWM outputs.

Runs after `SideController.update` and turns its coarse requests (`fan_duty`, `pump_on`, `mode`) into PWM duties:

- Fan: the larger of the controller's request (follows TEC power) and a hot-face temperature curve. The curve has
  on/off hysteresis (so heat soak after a TEC stop still gets cooled away) and a falling-edge hysteresis band (no
  hunting around a set point). Any non-zero duty is at least `FAN_MIN_DUTY`; every start is kicked at 100 %.
- Fan stall: only with a tach signal. A fan reading below `FAN_STALL_RPM` for `FAN_STALL_S` (after a spin-up grace)
  is stalled, and `tec_allowed` drops so the TEC path is cut. The Tier 0 carrier has no tach input, so the firmware
  passes `None` and relies on the hot-face trip and the bimetal cutoffs.
- Pump: full speed while priming, for `PUMP_START_S` after every start, in SAFE mode, and whenever flow is below the
  interlock threshold (then held at full for `PUMP_BOOST_HOLD_S`); otherwise the configured run duty. Zero on a leak or
  low water, whatever is requested. The flow interlock and the NO_FLOW fault stay in `SideController`.

No allocation, no clocks except the `now` passed in, so it ports 1:1 to Rust (firmware/obc-core/src/cooling.rs).
"""

from __future__ import annotations

from dataclasses import dataclass

from .control import MIN_FLOW_LPM, Mode

FAN_MIN_DUTY = 0.25  # below this, typical 12 V fans stall
FAN_KICK_S = 1.0  # full duty for this long on every start
FAN_T_ON_C = 35.0  # hot face: the fan starts above this even without TEC power (heat soak)...
FAN_T_OFF_C = 32.0  # ...and the temperature demand ends below this
FAN_T_FULL_C = 55.0  # temperature demand reaches 100 % here (hot-face trip is 75 degC)
FAN_HYST_K = 2.0  # the duty only falls once the hot face has cooled this much below the rising curve
FAN_STALL_RPM = 300.0
FAN_STALL_GRACE_S = 3.0  # spin-up time after a start before the tach is judged
FAN_STALL_S = 5.0  # below FAN_STALL_RPM this long = stalled
PUMP_START_S = 5.0  # full speed after every start (spin-up, pushes air out)
PUMP_BOOST_HOLD_S = 30.0  # after flow was low, stay at full speed this long before going back to the run duty
PUMP_MIN_DUTY = 0.5  # lowest run duty accepted from the board config


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def fan_curve(t_hot_c: float) -> float:
    """Temperature demand (0..1) for an *on* fan: FAN_MIN_DUTY at FAN_T_OFF_C, 100 % at FAN_T_FULL_C."""
    frac = _clamp((t_hot_c - FAN_T_OFF_C) / (FAN_T_FULL_C - FAN_T_OFF_C), 0.0, 1.0)
    return FAN_MIN_DUTY + (1.0 - FAN_MIN_DUTY) * frac


@dataclass
class CoolingInputs:
    mode: Mode
    fan_request: float  # SideController.fan_duty
    pump_request: bool  # SideController.pump_on
    t_hot_face: float | None
    flow_lpm: float
    leak: bool
    water_ok: bool
    priming: bool = False  # PRIME command active
    tach_rpm: float | None = None  # None = no tach signal


@dataclass
class CoolingOutputs:
    fan_duty: float  # 0..1
    pump_duty: float  # 0..1
    fan_stalled: bool
    tec_allowed: bool  # False cuts the zone's TEC path


@dataclass
class Cooling:
    pump_run_duty: float = 1.0
    # fan state
    duty: float = 0.0  # curve/request duty before the kick
    temp_on: bool = False
    out_prev: float = 0.0
    kick_until: float = 0.0
    started_at: float = 0.0
    low_since: float | None = None
    stalled: bool = False
    # pump state
    pump_since: float | None = None
    boost_until: float = 0.0

    def update(self, i: CoolingInputs, now: float) -> CoolingOutputs:
        fan = self._fan(i, now)
        pump = self._pump(i, now)
        return CoolingOutputs(fan, pump, self.stalled, not self.stalled)

    def _fan(self, i: CoolingInputs, now: float) -> float:
        req = _clamp(i.fan_request, 0.0, 1.0)
        if i.t_hot_face is None:
            # No hot-face reading: never let the curve hold the fan down while anything asks for it.
            self.temp_on = False
            up = down = 1.0 if req > 0.0 else 0.0
        else:
            if i.t_hot_face > FAN_T_ON_C:
                self.temp_on = True
            elif i.t_hot_face < FAN_T_OFF_C:
                self.temp_on = False
            up = max(req, fan_curve(i.t_hot_face) if self.temp_on else 0.0)
            down = max(req, fan_curve(i.t_hot_face + FAN_HYST_K) if self.temp_on else 0.0)
        if up > self.duty:
            self.duty = up
        elif down < self.duty:
            self.duty = down
        if 0.0 < self.duty < FAN_MIN_DUTY:
            self.duty = FAN_MIN_DUTY
        if self.duty > 0.0 and self.out_prev == 0.0:
            self.kick_until = now + FAN_KICK_S
            self.started_at = now
        out = 1.0 if (self.duty > 0.0 and now < self.kick_until) else self.duty
        self._stall(i.tach_rpm, out, now)
        self.out_prev = out
        return out

    def _stall(self, tach_rpm: float | None, out: float, now: float) -> None:
        if tach_rpm is None or out == 0.0:
            self.low_since = None
            self.stalled = False
            return
        if now - self.started_at < FAN_STALL_GRACE_S:
            self.low_since = None  # still spinning up (stalled was cleared when the fan was off)
            return
        if tach_rpm < FAN_STALL_RPM:
            if self.low_since is None:
                self.low_since = now
            if now - self.low_since >= FAN_STALL_S:
                self.stalled = True
        else:
            self.low_since = None
            self.stalled = False

    def _pump(self, i: CoolingInputs, now: float) -> float:
        if i.leak or not i.water_ok or not (i.pump_request or i.priming):
            self.pump_since = None
            self.boost_until = 0.0
            return 0.0
        if self.pump_since is None:
            self.pump_since = now
        if i.pump_request and i.flow_lpm < MIN_FLOW_LPM:
            # Waiting for flow (interlock) or flow lost: push as hard as possible, and stay there for a while.
            self.boost_until = now + PUMP_BOOST_HOLD_S
        if i.priming or i.mode == Mode.SAFE or now - self.pump_since < PUMP_START_S or now < self.boost_until:
            return 1.0
        return _clamp(self.pump_run_duty, PUMP_MIN_DUTY, 1.0)
