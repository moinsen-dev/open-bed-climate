//! Per-zone fan and pump PWM duty. Port of `obc/cooling.py` (see there for the behaviour).
//!
//! Runs after `ZoneController::update` and turns its coarse requests (`fan_duty`, `pump_on`, `mode`) into duties:
//! fan = max(request, hot-face curve) with on/off and falling-edge hysteresis, a minimum duty and a 100 % kick on
//! every start; optional tach-based stall detection (`tec_allowed` drops); pump at full speed while priming,
//! starting, in SAFE mode and whenever flow is below the interlock threshold, else the configured run duty, and
//! zero on a leak or low water.

use crate::control::{Mode, MIN_FLOW_LPM};

pub const FAN_MIN_DUTY: f32 = 0.25;
pub const FAN_KICK_S: f64 = 1.0;
pub const FAN_T_ON_C: f32 = 35.0;
pub const FAN_T_OFF_C: f32 = 32.0;
pub const FAN_T_FULL_C: f32 = 55.0;
pub const FAN_HYST_K: f32 = 2.0;
pub const FAN_STALL_RPM: f32 = 300.0;
pub const FAN_STALL_GRACE_S: f64 = 3.0;
pub const FAN_STALL_S: f64 = 5.0;
pub const PUMP_START_S: f64 = 5.0;
pub const PUMP_BOOST_HOLD_S: f64 = 30.0;
pub const PUMP_MIN_DUTY: f32 = 0.5;

/// Temperature demand (0..1) for an *on* fan: FAN_MIN_DUTY at FAN_T_OFF_C, 100 % at FAN_T_FULL_C.
pub fn fan_curve(t_hot_c: f32) -> f32 {
    let frac = ((t_hot_c - FAN_T_OFF_C) / (FAN_T_FULL_C - FAN_T_OFF_C)).clamp(0.0, 1.0);
    FAN_MIN_DUTY + (1.0 - FAN_MIN_DUTY) * frac
}

#[derive(Clone, Copy, Debug)]
pub struct CoolingInputs {
    pub mode: Mode,
    /// `Outputs::fan_duty` from the zone controller.
    pub fan_request: f32,
    /// `Outputs::pump_on` from the zone controller.
    pub pump_request: bool,
    pub t_hot_face: Option<f32>,
    pub flow_lpm: f32,
    pub leak: bool,
    pub water_ok: bool,
    /// PRIME command active.
    pub priming: bool,
    /// `None` = no tach signal (the Tier 0 carrier has none).
    pub tach_rpm: Option<f32>,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CoolingOutputs {
    pub fan_duty: f32,
    pub pump_duty: f32,
    pub fan_stalled: bool,
    /// False cuts the zone's TEC path.
    pub tec_allowed: bool,
}

#[derive(Clone, Debug)]
pub struct Cooling {
    pump_run_duty: f32,
    duty: f32,
    temp_on: bool,
    out_prev: f32,
    kick_until: f64,
    started_at: f64,
    low_since: Option<f64>,
    stalled: bool,
    pump_since: Option<f64>,
    boost_until: f64,
}

impl Cooling {
    pub const fn new(pump_run_duty: f32) -> Self {
        Self {
            pump_run_duty,
            duty: 0.0,
            temp_on: false,
            out_prev: 0.0,
            kick_until: 0.0,
            started_at: 0.0,
            low_since: None,
            stalled: false,
            pump_since: None,
            boost_until: 0.0,
        }
    }

    pub fn update(&mut self, i: &CoolingInputs, now: f64) -> CoolingOutputs {
        let fan_duty = self.fan(i, now);
        let pump_duty = self.pump(i, now);
        CoolingOutputs { fan_duty, pump_duty, fan_stalled: self.stalled, tec_allowed: !self.stalled }
    }

    fn fan(&mut self, i: &CoolingInputs, now: f64) -> f32 {
        let req = i.fan_request.clamp(0.0, 1.0);
        let (up, down) = match i.t_hot_face {
            None => {
                // No hot-face reading: never let the curve hold the fan down while anything asks for it.
                self.temp_on = false;
                let d = if req > 0.0 { 1.0 } else { 0.0 };
                (d, d)
            }
            Some(t) => {
                if t > FAN_T_ON_C {
                    self.temp_on = true;
                } else if t < FAN_T_OFF_C {
                    self.temp_on = false;
                }
                let curve = |x: f32| if self.temp_on { fan_curve(x) } else { 0.0 };
                (req.max(curve(t)), req.max(curve(t + FAN_HYST_K)))
            }
        };
        if up > self.duty {
            self.duty = up;
        } else if down < self.duty {
            self.duty = down;
        }
        if self.duty > 0.0 && self.duty < FAN_MIN_DUTY {
            self.duty = FAN_MIN_DUTY;
        }
        if self.duty > 0.0 && self.out_prev == 0.0 {
            self.kick_until = now + FAN_KICK_S;
            self.started_at = now;
        }
        let out = if self.duty > 0.0 && now < self.kick_until { 1.0 } else { self.duty };
        self.stall(i.tach_rpm, out, now);
        self.out_prev = out;
        out
    }

    fn stall(&mut self, tach_rpm: Option<f32>, out: f32, now: f64) {
        let Some(rpm) = tach_rpm.filter(|_| out > 0.0) else {
            self.low_since = None;
            self.stalled = false;
            return;
        };
        if now - self.started_at < FAN_STALL_GRACE_S {
            self.low_since = None; // still spinning up (stalled was cleared when the fan was off)
            return;
        }
        if rpm < FAN_STALL_RPM {
            let since = *self.low_since.get_or_insert(now);
            if now - since >= FAN_STALL_S {
                self.stalled = true;
            }
        } else {
            self.low_since = None;
            self.stalled = false;
        }
    }

    fn pump(&mut self, i: &CoolingInputs, now: f64) -> f32 {
        if i.leak || !i.water_ok || !(i.pump_request || i.priming) {
            self.pump_since = None;
            self.boost_until = 0.0;
            return 0.0;
        }
        let since = *self.pump_since.get_or_insert(now);
        if i.pump_request && i.flow_lpm < MIN_FLOW_LPM {
            // Waiting for flow (interlock) or flow lost: push as hard as possible, and stay there for a while.
            self.boost_until = now + PUMP_BOOST_HOLD_S;
        }
        if i.priming || i.mode == Mode::Safe || now - since < PUMP_START_S || now < self.boost_until {
            1.0
        } else {
            self.pump_run_duty.clamp(PUMP_MIN_DUTY, 1.0)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ci() -> CoolingInputs {
        CoolingInputs {
            mode: Mode::Run,
            fan_request: 0.2,
            pump_request: true,
            t_hot_face: Some(30.0),
            flow_lpm: 0.5,
            leak: false,
            water_ok: true,
            priming: false,
            tach_rpm: None,
        }
    }

    #[test]
    fn fan_kicks_then_holds_min_duty() {
        let mut c = Cooling::new(1.0);
        assert_eq!(c.update(&ci(), 0.0).fan_duty, 1.0);
        assert_eq!(c.update(&ci(), FAN_KICK_S + 0.1).fan_duty, FAN_MIN_DUTY);
    }

    #[test]
    fn pump_off_on_leak_even_when_priming() {
        let mut c = Cooling::new(1.0);
        let o = c.update(&CoolingInputs { mode: Mode::Safe, leak: true, priming: true, ..ci() }, 0.0);
        assert_eq!(o.pump_duty, 0.0);
        let o = c.update(&CoolingInputs { mode: Mode::Safe, water_ok: false, priming: true, ..ci() }, 1.0);
        assert_eq!(o.pump_duty, 0.0);
    }

    #[test]
    fn no_tach_never_stalls() {
        let mut c = Cooling::new(1.0);
        for k in 0..100 {
            assert!(c.update(&ci(), k as f64 * 0.5).tec_allowed);
        }
    }
}
