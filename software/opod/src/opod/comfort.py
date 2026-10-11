"""Hub-side comfort/safety guards that need room sensors (the control MCU has none).

Dew-point guard (docs/design/02-electrical-safety.md, "Condensation"): when cooling below
GUARD_BELOW_C, never request water colder than dew point + MARGIN_K, so the mat and lines
don't sweat into the bed. Reference for hub/esphome/components/opod/guard.h.
"""

from __future__ import annotations

import math

GUARD_BELOW_C = 16.0
MARGIN_K = 1.0
_A, _B = 17.62, 243.12  # Magnus coefficients (water, -45..60 degC)


def dew_point_c(t_c: float, rh_pct: float) -> float:
    g = math.log(rh_pct / 100.0) + _A * t_c / (_B + t_c)
    return _B * g / (_A - g)


def guarded_target(target_c: float | None, room_c: float | None, rh_pct: float | None) -> float | None:
    """Effective setpoint to send. Unchanged when off, warm enough, or room sensors unavailable."""
    if target_c is None or target_c >= GUARD_BELOW_C or room_c is None or rh_pct is None:
        return target_c
    if not (0.0 < rh_pct <= 100.0) or math.isnan(room_c):
        return target_c
    return max(target_c, min(GUARD_BELOW_C, dew_point_c(room_c, rh_pct) + MARGIN_K))
