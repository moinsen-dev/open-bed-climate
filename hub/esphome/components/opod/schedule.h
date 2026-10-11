// Night schedule: a user-owned curve of (minutes after bedtime, °C) points plus a wake ramp.
// Header-only port of software/opod/src/opod/schedule.py, host-tested against vectors that the
// Python reference generates (test/schedule.txt). No ESPHome dependency.
#pragma once

#include <cmath>
#include <cstddef>

namespace openpod {
namespace schedule {

static const size_t MAX_POINTS = 16;
static const int DAY_MIN = 24 * 60;

struct Point {
  float minute;  // minutes after bedtime
  float c;       // water setpoint, °C
};

struct Schedule {
  Point points[MAX_POINTS];
  size_t n{0};
  float wake_ramp_min{30.0f};
  float wake_target_c{32.0f};

  bool add(float minute, float c) {
    if (this->n >= MAX_POINTS)
      return false;
    this->points[this->n++] = Point{minute, c};
    return true;
  }

  // Linear interpolation between points, held at both ends.
  float base(float minute) const {
    if (this->n == 0)
      return NAN;
    if (minute <= this->points[0].minute)
      return this->points[0].c;
    for (size_t i = 1; i < this->n; i++) {
      const Point &a = this->points[i - 1], &b = this->points[i];
      if (minute <= b.minute)
        return a.c + (b.c - a.c) * (minute - a.minute) / (b.minute - a.minute);
    }
    return this->points[this->n - 1].c;
  }

  // Setpoint `minute` after bedtime. wake_minute NaN = no wake time. Returns NaN once past wake (zone off).
  float setpoint(float minute, float wake_minute) const {
    if (!std::isnan(wake_minute)) {
      if (minute >= wake_minute)
        return NAN;
      float ramp_start = wake_minute - this->wake_ramp_min;
      if (minute > ramp_start) {
        float b = this->base(ramp_start);
        return b + (this->wake_target_c - b) * (minute - ramp_start) / this->wake_ramp_min;
      }
    }
    return this->base(minute);
  }
};

// Minutes from a start time of day to the next wake time of day (both minutes since midnight), in 1..1440.
inline int wake_offset_min(int start_min_of_day, int wake_min_of_day) {
  int d = ((wake_min_of_day - start_min_of_day) % DAY_MIN + DAY_MIN) % DAY_MIN;
  return d == 0 ? DAY_MIN : d;
}

}  // namespace schedule
}  // namespace openpod
