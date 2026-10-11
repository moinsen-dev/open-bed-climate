// Hub-side dew-point guard. Reference: software/opod/src/opod/comfort.py (keep in sync; tested in test/test_opl.cpp).
#pragma once

#include <cmath>

namespace openpod {
namespace guard {

static const float GUARD_BELOW_C = 16.0f;
static const float MARGIN_K = 1.0f;

inline float dew_point_c(float t_c, float rh_pct) {
  const float a = 17.62f, b = 243.12f;
  float g = std::log(rh_pct / 100.0f) + a * t_c / (b + t_c);
  return b * g / (a - g);
}

/// Effective setpoint (NaN = off stays NaN). Unchanged if warm enough or room sensors are unavailable.
inline float guarded_target(float target_c, float room_c, float rh_pct) {
  if (std::isnan(target_c) || target_c >= GUARD_BELOW_C || std::isnan(room_c) || std::isnan(rh_pct))
    return target_c;
  if (!(rh_pct > 0.0f && rh_pct <= 100.0f))
    return target_c;
  float floor_c = std::fmin(GUARD_BELOW_C, dew_point_c(room_c, rh_pct) + MARGIN_K);
  return std::fmax(target_c, floor_c);
}

}  // namespace guard
}  // namespace openpod
