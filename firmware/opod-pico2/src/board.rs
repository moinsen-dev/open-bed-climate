//! Tier 0 board configuration: pin map, bus addresses, sensor calibration and kit limits.
//!
//! Wiring is documented in hardware/WIRING.md. Everything a builder may change for their kit lives
//! here; the safety limits do NOT (they are constants in opod-core::control).
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
//! All relay/pump/fan outputs start LOW = off, and every driver input needs an external 10 kΩ
//! pull-down, so a crashed or unflashed MCU never energises a TEC. Don't rely on the RP2350's
//! internal pull-downs (erratum E9).

use opod_core::modbus::{DpsMap, DPS5020};
use opod_core::ntc::Ntc;

pub const ZONES: usize = 2;

/// Per-TEC current cap from the kit file (`max_tec_current_a`), e.g. Duo Standard = 4.5 A.
pub const MAX_TEC_CURRENT_A: f32 = 4.5;
/// TECs per zone from the kit file (`tec_per_zone`). The driver is set to TECS_PER_ZONE * current.
pub const TECS_PER_ZONE: f32 = 4.0;

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
