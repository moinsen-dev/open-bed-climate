//! Sequencing for one zone's TEC driver (DPS-class module on Modbus) and its relays.
//!
//! Pure state machine: the firmware asks `next()` for at most ONE bus transaction per control
//! cycle, performs it, and reports the result with `done()`. This bounds the loop time (watchdog)
//! and keeps the sequencing host-testable.
//!
//! Rules:
//! - the polarity relay switches only after the driver output is OFF and reads back < 0.1 A
//! - the voltage ceiling is written once, then re-verified every 60 s (survives a driver reset)
//! - the current setpoint is written only on change (deadband); increases at most once per second
//!   (bus load, EEPROM wear on modules that persist setpoints), decreases immediately
//! - the output is enabled only while the driver holds a setpoint no higher than requested
//! - the output enable is written only on transitions
//! - 3 failed transactions in a row = driver fault: the TEC path (zone relay) must open

pub const CURRENT_DEADBAND_A: f32 = 0.2;
pub const CURRENT_MIN_INTERVAL_S: f64 = 1.0;
pub const VOLTAGE_REVERIFY_S: f64 = 60.0;
pub const ZERO_CURRENT_A: f32 = 0.1;
pub const MAX_FAILURES: u8 = 3;

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Action {
    None,
    /// Write the output enable register.
    SetOutput(bool),
    /// Read the measured output current (for the polarity interlock).
    ReadCurrent,
    /// Write the voltage ceiling (`modbus::TEC_VOLTAGE_CEILING_V`).
    SetVoltageCeiling,
    /// Write the zone current setpoint in A (n_tec * per-TEC current).
    SetCurrent(f32),
}

#[derive(Clone, Debug)]
pub struct ZoneDriver {
    relay_polarity: i8,
    wanted_polarity: i8,
    output_on: Option<bool>, // None = unknown (boot, or a failed write)
    current_set: Option<f32>,
    current_set_at: f64,
    voltage_set_at: Option<f64>,
    failures: u8,
}

impl Default for ZoneDriver {
    fn default() -> Self {
        Self {
            relay_polarity: 1,
            wanted_polarity: 1,
            output_on: None,
            current_set: None,
            current_set_at: f64::NEG_INFINITY,
            voltage_set_at: None,
            failures: 0,
        }
    }
}

impl ZoneDriver {
    /// Decide the next bus transaction. `zone_amps` >= 0 is the requested zone current,
    /// `polarity` the controller's relay state, `run` whether the controller is in Mode::Run.
    pub fn next(&mut self, zone_amps: f32, polarity: i8, run: bool, now: f64) -> Action {
        self.wanted_polarity = polarity;
        if polarity != self.relay_polarity {
            return if self.output_on != Some(false) { Action::SetOutput(false) } else { Action::ReadCurrent };
        }
        if !run || zone_amps <= 0.0 {
            return if self.output_on != Some(false) { Action::SetOutput(false) } else { Action::None };
        }
        if self.voltage_set_at.is_none_or(|t| now - t >= VOLTAGE_REVERIFY_S) {
            return Action::SetVoltageCeiling;
        }
        match self.current_set {
            // Unknown setpoint, or a decrease: write immediately (lowering current is always safe).
            None => return Action::SetCurrent(zone_amps),
            Some(c) if c - zone_amps > CURRENT_DEADBAND_A => return Action::SetCurrent(zone_amps),
            // Increases are rate-limited.
            Some(c) if zone_amps - c > CURRENT_DEADBAND_A && now - self.current_set_at >= CURRENT_MIN_INTERVAL_S => {
                return Action::SetCurrent(zone_amps);
            }
            _ => {}
        }
        // Enable only when the driver holds a setpoint no higher than requested (+ deadband).
        let setpoint_fits = self.current_set.is_some_and(|c| c <= zone_amps + CURRENT_DEADBAND_A);
        if self.output_on != Some(true) && setpoint_fits {
            return Action::SetOutput(true);
        }
        Action::None
    }

    /// Report the outcome of the action returned by `next()`. `read_amps` is the measured current for
    /// `ReadCurrent`, `None` if the transaction failed.
    pub fn done(&mut self, action: Action, ok: bool, read_amps: Option<f32>, now: f64) {
        if action == Action::None {
            return;
        }
        if !ok {
            self.failures = self.failures.saturating_add(1);
            match action {
                Action::SetOutput(_) => self.output_on = None,
                Action::SetCurrent(_) => self.current_set = None,
                Action::SetVoltageCeiling => self.voltage_set_at = None,
                _ => {}
            }
            return;
        }
        self.failures = 0;
        match action {
            Action::SetOutput(on) => self.output_on = Some(on),
            Action::ReadCurrent => {
                if matches!(read_amps, Some(a) if a < ZERO_CURRENT_A) {
                    self.relay_polarity = self.wanted_polarity;
                    self.current_set = None; // force a fresh setpoint before re-enabling
                }
            }
            Action::SetVoltageCeiling => self.voltage_set_at = Some(now),
            Action::SetCurrent(a) => {
                self.current_set = Some(a);
                self.current_set_at = now;
            }
            Action::None => {}
        }
    }

    /// State the polarity relay GPIO must have (+1 cool / -1 heat).
    pub fn relay_polarity(&self) -> i8 {
        self.relay_polarity
    }

    pub fn driver_ok(&self) -> bool {
        self.failures < MAX_FAILURES
    }

    /// Whether the zone relay (hardware TEC power path) may be closed.
    pub fn tec_path(&self, zone_amps: f32, run: bool) -> bool {
        run && zone_amps > 0.0
            && self.driver_ok()
            && self.output_on == Some(true)
            && self.relay_polarity == self.wanted_polarity
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Drive the state machine with a perfect bus until it is idle; returns the action log.
    fn settle(d: &mut ZoneDriver, amps: f32, pol: i8, run: bool, now: &mut f64, measured: f32) -> Vec<Action> {
        let mut log = vec![];
        for _ in 0..10 {
            let a = d.next(amps, pol, run, *now);
            if a == Action::None {
                break;
            }
            let read = if a == Action::ReadCurrent { Some(measured) } else { None };
            d.done(a, true, read, *now);
            log.push(a);
            *now += 0.1;
        }
        log
    }

    #[test]
    fn boot_sequence_then_idle() {
        let mut d = ZoneDriver::default();
        let mut t = 0.0;
        let log = settle(&mut d, 18.0, 1, true, &mut t, 0.0);
        assert_eq!(log, vec![Action::SetVoltageCeiling, Action::SetCurrent(18.0), Action::SetOutput(true)]);
        assert!(d.tec_path(18.0, true));
    }

    #[test]
    fn small_changes_are_not_written_and_rate_is_limited() {
        let mut d = ZoneDriver::default();
        let mut t = 0.0;
        settle(&mut d, 18.0, 1, true, &mut t, 0.0);
        assert_eq!(d.next(18.1, 1, true, t), Action::None, "inside deadband");
        assert_eq!(d.next(19.0, 1, true, t), Action::None, "increase rate-limited: < 1 s since last write");
        assert_eq!(d.next(19.0, 1, true, t + 1.0), Action::SetCurrent(19.0));
        assert_eq!(d.next(17.0, 1, true, t), Action::SetCurrent(17.0), "decreases are immediate");
    }

    #[test]
    fn polarity_switches_only_after_zero_current_readback() {
        let mut d = ZoneDriver::default();
        let mut t = 0.0;
        settle(&mut d, 18.0, 1, true, &mut t, 0.0);
        // Heat requested: output off first, then read-back.
        assert_eq!(d.next(10.0, -1, true, t), Action::SetOutput(false));
        d.done(Action::SetOutput(false), true, None, t);
        assert!(!d.tec_path(10.0, true));
        assert_eq!(d.next(10.0, -1, true, t), Action::ReadCurrent);
        d.done(Action::ReadCurrent, true, Some(2.5), t); // still flowing: must NOT switch
        assert_eq!(d.relay_polarity(), 1);
        d.done(Action::ReadCurrent, true, Some(0.02), t);
        assert_eq!(d.relay_polarity(), -1);
        let log = settle(&mut d, 10.0, -1, true, &mut t, 0.0);
        assert_eq!(log, vec![Action::SetCurrent(10.0), Action::SetOutput(true)]);
        assert!(d.tec_path(10.0, true));
    }

    #[test]
    fn failures_open_the_tec_path_and_recover() {
        let mut d = ZoneDriver::default();
        let mut t = 0.0;
        settle(&mut d, 18.0, 1, true, &mut t, 0.0);
        for _ in 0..3 {
            d.done(Action::SetCurrent(17.0), false, None, t);
        }
        assert!(!d.driver_ok());
        assert!(!d.tec_path(18.0, true));
        settle(&mut d, 18.0, 1, true, &mut t, 0.0);
        assert!(d.driver_ok() && d.tec_path(18.0, true));
    }

    #[test]
    fn voltage_ceiling_is_reverified() {
        let mut d = ZoneDriver::default();
        let mut t = 0.0;
        settle(&mut d, 18.0, 1, true, &mut t, 0.0);
        assert_eq!(d.next(18.0, 1, true, t + 61.0), Action::SetVoltageCeiling);
    }

    #[test]
    fn never_enables_with_a_stale_higher_setpoint() {
        let mut d = ZoneDriver::default();
        let mut t = 0.0;
        settle(&mut d, 18.0, 1, true, &mut t, 0.0);
        settle(&mut d, 0.0, 1, false, &mut t, 0.0); // output off, driver still holds 18 A
        let a = d.next(5.0, 1, true, t);
        assert_eq!(a, Action::SetCurrent(5.0), "lower the setpoint before enabling");
    }

    #[test]
    fn stop_turns_output_off_once() {
        let mut d = ZoneDriver::default();
        let mut t = 0.0;
        settle(&mut d, 18.0, 1, true, &mut t, 0.0);
        let log = settle(&mut d, 0.0, 1, false, &mut t, 0.0);
        assert_eq!(log, vec![Action::SetOutput(false)]);
    }
}
