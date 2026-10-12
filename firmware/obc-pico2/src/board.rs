//! Tier 0 board configuration: pin map, bus addresses, sensor calibration and kit limits.
//!
//! Wiring is documented in hardware/WIRING.md. Everything a builder may change for their kit lives
//! here (the kit limits are selected with a Cargo feature, see below); the safety limits do NOT (they are
//! constants in obc-core::control).
//!
//! | Function                     | Pico 2 pin | Notes                                            |
//! |------------------------------|------------|--------------------------------------------------|
//! | OPL to hub (UART0 TX/RX)     | GP0 / GP1  | 460800 baud, 3.3 V, to the ESP32-S3 hub          |
//! | Modbus to TEC drivers (UART1)| GP4 / GP5  | via RS-485 transceiver; DE/RE on GP6             |
//! | I2C0 SDA/SCL (ADS1115)       | GP8 / GP9  | NTC dividers on ADS1115 @0x48                    |
//! | Zone 0: zone relay / polarity / pump / fan / flow | GP10 / GP11 / GP12 / GP13 / GP14 | |
//! | Zone 1: zone relay / polarity / pump / fan / flow | GP16 / GP17 / GP18 / GP19 / GP20 | |
//! | Leak sensor                  | GP21       | LOW = dry; HIGH = leak or open wire (10k pull-up)|
//! | Water level                  | GP22       | LOW = OK;  HIGH = low or open wire (10k pull-up) |
//!
//! All relay/pump/fan outputs start LOW = off, and every driver input needs an external 4.7 kΩ
//! pull-down (≤ 8.2 kΩ per erratum E9), so a crashed or unflashed MCU never energises a TEC.
//! Don't rely on the RP2350's internal pull-downs (erratum E9).

use obc_core::modbus::{DpsMap, DPS5020};
use obc_core::ntc::Ntc;

/// Zone slots on the Tier 0 board (pins, ADS channels, Modbus addresses) and sides in the OPL protocol.
pub const ZONES: usize = 2;

// Kit limits, one block per kit, selected with a Cargo feature (default: Duo Standard). Each block mirrors its
// hardware/kits/<kit>.toml: `zones`, `tec_per_zone`, `max_tec_current_a` (checked by software/obc/tests/test_kits.py).
// Build for another kit: cargo build --release --no-default-features --features kit-solo-starter
#[cfg(feature = "kit-solo-starter")]
mod kit {
    pub const KIT: &str = "solo-starter";
    pub const ACTIVE_ZONES: usize = 1;
    pub const TECS_PER_ZONE: f32 = 3.0;
    pub const MAX_TEC_CURRENT_A: f32 = 5.0;
}
#[cfg(feature = "kit-duo-standard")]
mod kit {
    pub const KIT: &str = "duo-standard";
    pub const ACTIVE_ZONES: usize = 2;
    pub const TECS_PER_ZONE: f32 = 4.0;
    pub const MAX_TEC_CURRENT_A: f32 = 4.5;
}
#[cfg(feature = "kit-duo-reference")]
mod kit {
    pub const KIT: &str = "duo-reference";
    pub const ACTIVE_ZONES: usize = 2;
    pub const TECS_PER_ZONE: f32 = 4.0;
    pub const MAX_TEC_CURRENT_A: f32 = 5.0;
}
#[cfg(not(any(feature = "kit-solo-starter", feature = "kit-duo-standard", feature = "kit-duo-reference")))]
compile_error!("select a kit: --features kit-solo-starter | kit-duo-standard | kit-duo-reference");
#[cfg(any(
    all(feature = "kit-solo-starter", feature = "kit-duo-standard"),
    all(feature = "kit-solo-starter", feature = "kit-duo-reference"),
    all(feature = "kit-duo-standard", feature = "kit-duo-reference"),
))]
compile_error!("select exactly one kit feature (use --no-default-features with a non-default kit)");

/// Kit id (hardware/kits/<KIT>.toml).
pub use kit::KIT;
/// Zones the kit uses. Zone slots >= ACTIVE_ZONES are inert: outputs held LOW, no Modbus traffic, no faults,
/// telemetry mode 0 (off) with invalid temperatures, and any non-off target is rejected.
pub use kit::ACTIVE_ZONES;
/// TECs per zone (`tec_per_zone`). The driver is set to TECS_PER_ZONE * current.
pub use kit::TECS_PER_ZONE;
/// Per-TEC current cap (`max_tec_current_a`).
pub use kit::MAX_TEC_CURRENT_A;
const _: () = assert!(ACTIVE_ZONES >= 1 && ACTIVE_ZONES <= ZONES);

pub const HUB_BAUD: u32 = 460_800;
pub const MODBUS_BAUD: u32 = 9_600;
/// Modbus slave address of each zone's TEC driver.
pub const DPS_ADDR: [u8; ZONES] = [1, 2];
/// Register map of the TEC drivers. VERIFY against your module's protocol document.
pub const DPS_MAP: DpsMap = DPS5020;

pub const ADS1115_ADDR: u8 = 0x48;
/// ADS1115 channel per zone: (water temperature NTC, TEC hot-face NTC).
pub const NTC_CHANNELS: [(u8, u8); ZONES] = [(0, 1), (2, 3)];
/// NTC divider: 3.3 V -- R_FIXED -- node (to ADS) -- NTC -- GND.
pub const NTC_DIVIDER_V: f32 = 3.3;
pub const NTC_FIXED_OHM: f32 = 10_000.0;
/// Per-sensor calibration (r25, beta). Calibrate each inline sensor; see hardware/PARTS.md (temp_sensors).
pub const NTC_CAL: [(Ntc, Ntc); ZONES] = [(Ntc::GENERIC_10K, Ntc::GENERIC_10K), (Ntc::GENERIC_10K, Ntc::GENERIC_10K)];

/// Flow sensor pulse frequency per L/min (YF-S401 class is ~98 Hz per L/min; verify for your sensor).
pub const FLOW_HZ_PER_LPM: f32 = 98.0;

/// Pump-only priming duration after a PRIME command.
pub const PRIME_SECONDS: u64 = 60;

/// Pump and fan PWM frequency (power PWM of the low-side switches; the carrier routes no 4-pin PWM signal wire).
pub const PWM_HZ: u32 = 25_000;
/// Pump duty in normal running (obc-core::cooling runs it at 100 % while priming, starting, in SAFE and whenever flow
/// is low, and clamps this to >= 50 %). Lower = quieter; check on your loop that flow stays well above 0.15 L/min.
pub const PUMP_RUN_DUTY: f32 = 0.8;
