//! NTC thermistor conversion (beta model) with plausibility limits.
//!
//! Inline G1/4 sensors rarely publish B-value/tolerance: calibrate per sensor (ice bath + warm bath)
//! and store `r25`/`beta` in the board config.

#[derive(Clone, Copy, Debug)]
pub struct Ntc {
    pub r25_ohm: f32,
    pub beta: f32,
}

/// Divider: Vref -- R_fixed -- ADC node -- NTC -- GND.
#[derive(Clone, Copy, Debug)]
pub struct Divider {
    pub r_fixed_ohm: f32,
    pub adc_max: u16,
}

/// Readings outside this window are treated as sensor faults (open/short), never as temperatures.
pub const PLAUSIBLE_MIN_C: f32 = -10.0;
pub const PLAUSIBLE_MAX_C: f32 = 100.0;

impl Ntc {
    pub const GENERIC_10K: Ntc = Ntc { r25_ohm: 10_000.0, beta: 3435.0 };

    pub fn celsius_from_ohm(&self, r: f32) -> Option<f32> {
        if !(r.is_finite() && r > 0.0) {
            return None;
        }
        let inv_t = 1.0 / 298.15 + libm::logf(r / self.r25_ohm) / self.beta;
        let c = 1.0 / inv_t - 273.15;
        (PLAUSIBLE_MIN_C..=PLAUSIBLE_MAX_C).contains(&c).then_some(c)
    }

    pub fn celsius_from_adc(&self, d: &Divider, raw: u16) -> Option<f32> {
        // Open sensor -> raw at full scale; short -> raw ~0. Both rejected by the plausibility window.
        if raw == 0 || raw >= d.adc_max {
            return None;
        }
        let r = d.r_fixed_ohm * raw as f32 / (d.adc_max - raw) as f32;
        self.celsius_from_ohm(r)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn nominal_points() {
        let n = Ntc::GENERIC_10K;
        assert!((n.celsius_from_ohm(10_000.0).unwrap() - 25.0).abs() < 0.01);
        let d = Divider { r_fixed_ohm: 10_000.0, adc_max: 4095 };
        assert!((n.celsius_from_adc(&d, 2047).unwrap() - 25.0).abs() < 0.1);
        assert_eq!(n.celsius_from_adc(&d, 0), None);
        assert_eq!(n.celsius_from_adc(&d, 4095), None);
        assert_eq!(n.celsius_from_ohm(10.0), None); // implausibly hot = short
    }
}
