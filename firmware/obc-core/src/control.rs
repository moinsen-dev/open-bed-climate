//! Per-zone temperature controller and safety supervisor. Port of `obc/control.py`.
//!
//! Time is `f64` seconds since boot (exact to well below 1 ms for centuries of uptime);
//! physics and currents are `f32`.
//!
//! The constants below are the safety limits from SAFETY.md. They are compiled in on purpose:
//! no kit file, host command or network message can change them.

pub const SETPOINT_MIN_C: f32 = 13.0;
pub const SETPOINT_MAX_C: f32 = 43.0;
pub const WATER_TRIP_HIGH_C: f32 = 45.0;
pub const WATER_TRIP_LOW_C: f32 = 8.0;
pub const HOT_FACE_TRIP_C: f32 = 75.0;
pub const HEARTBEAT_TIMEOUT_S: f32 = 10.0;
pub const MIN_FLOW_LPM: f32 = 0.15;
pub const NO_FLOW_GRACE_S: f32 = 20.0;
pub const HEAT_TAPER_END_C: f32 = 48.0;
pub const HEAT_TAPER_A_PER_K: f32 = 0.5;
pub const HEAT_TAPER_MIN_A: f32 = 1.0;
pub const POLARITY_DEADTIME_S: f32 = 2.0;
pub const POLARITY_DEADBAND_A: f32 = 0.3;
/// Absolute per-TEC ceiling regardless of kit configuration (TEC1-12706 Imax is 6.4 A).
pub const ABS_MAX_TEC_A: f32 = 6.0;

/// Fault bit set, wire-compatible with OPL (u16).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub struct Faults(pub u16);

impl Faults {
    pub const NONE: Faults = Faults(0);
    pub const WATER_OVERTEMP: u16 = 1 << 0;
    pub const WATER_UNDERTEMP: u16 = 1 << 1;
    pub const HOT_FACE_OVERTEMP: u16 = 1 << 2;
    pub const NO_FLOW: u16 = 1 << 3;
    pub const LEAK: u16 = 1 << 4;
    pub const SENSOR_INVALID: u16 = 1 << 5;
    pub const HOST_TIMEOUT: u16 = 1 << 6;
    pub const LOW_WATER: u16 = 1 << 7;
    /// Latching faults stay set until an explicit clear from the host.
    pub const LATCHING: u16 = Self::WATER_OVERTEMP | Self::HOT_FACE_OVERTEMP | Self::LEAK | Self::SENSOR_INVALID;

    pub fn any(self) -> bool {
        self.0 != 0
    }
    pub fn has(self, bit: u16) -> bool {
        self.0 & bit != 0
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Mode {
    Off = 0,
    Run = 1,
    Safe = 2,
}

#[derive(Clone, Copy, Debug)]
pub struct Pid {
    pub kp: f32,
    pub ki: f32,
    pub kd: f32,
    pub out_min: f32,
    pub out_max: f32,
    integral: f32,
    prev_err: Option<f32>,
}

impl Pid {
    pub const fn new(kp: f32, ki: f32, kd: f32, out_min: f32, out_max: f32) -> Self {
        Self { kp, ki, kd, out_min, out_max, integral: 0.0, prev_err: None }
    }

    pub fn reset(&mut self) {
        self.integral = 0.0;
        self.prev_err = None;
    }

    pub fn update(&mut self, err: f32, dt: f32) -> f32 {
        let deriv = match self.prev_err {
            Some(p) => (err - p) / dt,
            None => 0.0,
        };
        self.prev_err = Some(err);
        let candidate = self.integral + err * dt;
        let out = self.kp * err + self.ki * candidate + self.kd * deriv;
        // Conditional integration anti-windup (same rule as the Python reference).
        if (self.out_min < out && out < self.out_max)
            || (out >= self.out_max && err < 0.0)
            || (out <= self.out_min && err > 0.0)
        {
            self.integral = candidate;
        }
        let out = self.kp * err + self.ki * self.integral + self.kd * deriv;
        out.clamp(self.out_min, self.out_max)
    }
}

/// Sensor inputs for one zone. `None` temperature = open/short sensor.
#[derive(Clone, Copy, Debug)]
pub struct Inputs {
    pub t_water: Option<f32>,
    pub t_hot_face: Option<f32>,
    pub flow_lpm: f32,
    pub leak: bool,
    pub water_ok: bool,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Outputs {
    /// Per-TEC current request in A. >0 cools, <0 heats. The zone driver is set to n_tec * |current|.
    pub tec_current: f32,
    pub pump_on: bool,
    pub fan_duty: f32,
    pub mode: Mode,
    pub faults: Faults,
    /// +1 cool, -1 heat (state of the polarity relay).
    pub polarity: i8,
}

#[derive(Clone, Debug)]
pub struct ZoneController {
    i_max: f32,
    pid: Pid,
    setpoint: Option<f32>,
    faults: Faults,
    last_heartbeat: f64,
    no_flow_since: Option<f64>,
    polarity: i8,
    polarity_ready_at: f64,
}

impl ZoneController {
    /// `i_max_per_tec` comes from the kit (e.g. 4.5 A); it is clamped to `ABS_MAX_TEC_A`.
    pub fn new(i_max_per_tec: f32) -> Self {
        let cap = i_max_per_tec.clamp(0.0, ABS_MAX_TEC_A);
        Self {
            i_max: cap,
            pid: Pid::new(1.2, 0.004, 0.0, -cap, cap),
            setpoint: None,
            faults: Faults::NONE,
            last_heartbeat: 0.0,
            no_flow_since: None,
            polarity: 1,
            polarity_ready_at: 0.0,
        }
    }

    pub fn i_max(&self) -> f32 {
        self.i_max
    }
    pub fn setpoint(&self) -> Option<f32> {
        self.setpoint
    }
    pub fn faults(&self) -> Faults {
        self.faults
    }

    pub fn set_target(&mut self, setpoint_c: Option<f32>, now: f64) {
        let sp = setpoint_c.map(|c| c.clamp(SETPOINT_MIN_C, SETPOINT_MAX_C));
        if sp.is_some() && self.setpoint.is_none() {
            self.pid.reset();
        }
        self.setpoint = sp;
        self.heartbeat(now);
    }

    pub fn heartbeat(&mut self, now: f64) {
        self.last_heartbeat = now;
        self.faults.0 &= !Faults::HOST_TIMEOUT;
    }

    pub fn clear_faults(&mut self) {
        self.faults = Faults::NONE;
        self.pid.reset();
    }

    fn evaluate(&mut self, i: &Inputs, now: f64) {
        let mut f = self.faults.0 & Faults::LATCHING;
        match (i.t_water, i.t_hot_face) {
            (Some(w), Some(h)) if w.is_finite() && h.is_finite() => {
                if w > WATER_TRIP_HIGH_C {
                    f |= Faults::WATER_OVERTEMP;
                }
                if w < WATER_TRIP_LOW_C {
                    f |= Faults::WATER_UNDERTEMP;
                }
                if h > HOT_FACE_TRIP_C {
                    f |= Faults::HOT_FACE_OVERTEMP;
                }
            }
            _ => f |= Faults::SENSOR_INVALID,
        }
        if i.leak {
            f |= Faults::LEAK;
        }
        if !i.water_ok {
            f |= Faults::LOW_WATER;
        }
        if self.setpoint.is_some() && i.flow_lpm < MIN_FLOW_LPM {
            let since = *self.no_flow_since.get_or_insert(now);
            if now - since > NO_FLOW_GRACE_S as f64 {
                f |= Faults::NO_FLOW;
            }
        } else {
            self.no_flow_since = None;
        }
        if self.setpoint.is_some() && now - self.last_heartbeat > HEARTBEAT_TIMEOUT_S as f64 {
            f |= Faults::HOST_TIMEOUT;
        }
        self.faults = Faults(f);
    }

    pub fn update(&mut self, i: &Inputs, now: f64, dt: f32) -> Outputs {
        self.evaluate(i, now);
        let Some(sp) = self.setpoint else {
            return self.out(0.0, false, 0.0, Mode::Off);
        };
        if self.faults.any() {
            self.pid.reset();
            let pump = !self.faults.has(Faults::LEAK | Faults::LOW_WATER);
            return self.out(0.0, pump, if pump { 1.0 } else { 0.0 }, Mode::Safe);
        }
        let t_water = i.t_water.unwrap_or(sp); // validated in evaluate()
        if i.flow_lpm < MIN_FLOW_LPM {
            self.pid.reset();
            return self.out(0.0, true, 0.2, Mode::Run);
        }
        let err = t_water - sp;
        let raw = self.pid.update(err, dt).min(self.i_max).max(-self.heat_limit(t_water));
        let current = self.apply_polarity(raw, now);
        let fan = (libm::fabsf(current) / self.i_max).clamp(0.2, 1.0);
        self.out(current, true, fan, Mode::Run)
    }

    pub fn heat_limit(&self, t_water: f32) -> f32 {
        (HEAT_TAPER_A_PER_K * (HEAT_TAPER_END_C - t_water)).min(self.i_max).max(HEAT_TAPER_MIN_A)
    }

    fn apply_polarity(&mut self, current: f32, now: f64) -> f32 {
        if libm::fabsf(current) < POLARITY_DEADBAND_A {
            return 0.0;
        }
        let wanted: i8 = if current > 0.0 { 1 } else { -1 };
        if wanted != self.polarity {
            self.polarity = wanted;
            self.polarity_ready_at = now + POLARITY_DEADTIME_S as f64;
        }
        if now < self.polarity_ready_at {
            0.0
        } else {
            current
        }
    }

    fn out(&self, tec_current: f32, pump_on: bool, fan_duty: f32, mode: Mode) -> Outputs {
        Outputs { tec_current, pump_on, fan_duty, mode, faults: self.faults, polarity: self.polarity }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ok() -> Inputs {
        Inputs { t_water: Some(30.0), t_hot_face: Some(35.0), flow_lpm: 0.5, leak: false, water_ok: true }
    }

    #[test]
    fn cap_is_clamped_to_absolute_max() {
        assert_eq!(ZoneController::new(9.0).i_max(), ABS_MAX_TEC_A);
    }

    #[test]
    fn overtemp_latches() {
        let mut c = ZoneController::new(4.5);
        c.set_target(Some(40.0), 0.0);
        let o = c.update(&Inputs { t_water: Some(46.0), ..ok() }, 1.0, 1.0);
        assert_eq!(o.mode, Mode::Safe);
        assert_eq!(o.tec_current, 0.0);
        let o = c.update(&ok(), 2.0, 1.0);
        assert!(o.faults.has(Faults::WATER_OVERTEMP));
    }

    #[test]
    fn nan_sensor_is_invalid() {
        let mut c = ZoneController::new(4.5);
        c.set_target(Some(25.0), 0.0);
        let o = c.update(&Inputs { t_water: Some(f32::NAN), ..ok() }, 1.0, 1.0);
        assert!(o.faults.has(Faults::SENSOR_INVALID));
        assert_eq!(o.tec_current, 0.0);
    }
}
