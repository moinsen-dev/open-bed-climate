"""Night temperature schedule: user-defined curve -> water setpoint at a given time.

A schedule is a list of (minutes_after_bedtime, setpoint_c) points; setpoints are
linearly interpolated and held at the ends. A wake ramp warms the bed before the
alarm. This replaces a vendor "autopilot" with an explicit, user-owned curve;
adaptive tuning can later rewrite the points from sleep data.
"""

from __future__ import annotations

from dataclasses import dataclass

from .control import SETPOINT_MAX_C, SETPOINT_MIN_C


@dataclass(frozen=True)
class Schedule:
    points: tuple[tuple[float, float], ...]  # (minute offset from bedtime, degC), sorted
    wake_ramp_min: float = 30.0
    wake_target_c: float = 32.0

    def __post_init__(self) -> None:
        if not self.points:
            raise ValueError("schedule needs at least one point")
        mins = [m for m, _ in self.points]
        if mins != sorted(mins):
            raise ValueError("points must be sorted by time")
        for _, c in self.points:
            if not SETPOINT_MIN_C <= c <= SETPOINT_MAX_C:
                raise ValueError(f"setpoint {c} outside {SETPOINT_MIN_C}..{SETPOINT_MAX_C}")

    def base(self, minute: float) -> float:
        pts = self.points
        if minute <= pts[0][0]:
            return pts[0][1]
        for (m0, c0), (m1, c1) in zip(pts, pts[1:]):
            if minute <= m1:
                return c0 + (c1 - c0) * (minute - m0) / (m1 - m0)
        return pts[-1][1]

    def setpoint(self, minute: float, wake_minute: float | None = None) -> float | None:
        """Setpoint for `minute` after bedtime; None once past the wake time (side turns off)."""
        if wake_minute is not None:
            if minute >= wake_minute:
                return None
            ramp_start = wake_minute - self.wake_ramp_min
            if minute > ramp_start:
                b = self.base(ramp_start)
                frac = (minute - ramp_start) / self.wake_ramp_min
                return b + (self.wake_target_c - b) * frac
        return self.base(minute)


def wake_offset(start_min_of_day: int, wake_min_of_day: int) -> int:
    """Minutes from a start time of day to the next wake time of day (minutes since midnight), in 1..1440."""
    d = (wake_min_of_day - start_min_of_day) % 1440
    return d or 1440


# Sensible starting curve: cool for sleep onset, coolest in early deep sleep, ease warmer toward morning.
DEFAULT = Schedule(points=((0, 24.0), (30, 21.0), (120, 20.0), (300, 23.0), (420, 25.0)))
