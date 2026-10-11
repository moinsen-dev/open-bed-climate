//! Minimal ADS1115 driver: single-shot, single-ended reads at ±4.096 V full scale.

use embassy_rp::i2c::{Async, Error, I2c};
use embassy_rp::peripherals::I2C0;
use embassy_time::Timer;

const REG_CONVERSION: u8 = 0x00;
const REG_CONFIG: u8 = 0x01;
const FULL_SCALE_V: f32 = 4.096;

pub struct Ads1115<'d> {
    i2c: I2c<'d, I2C0, Async>,
    addr: u8,
}

impl<'d> Ads1115<'d> {
    pub fn new(i2c: I2c<'d, I2C0, Async>, addr: u8) -> Self {
        Self { i2c, addr }
    }

    /// Read single-ended channel 0..=3 in volts.
    pub async fn read_volts(&mut self, ch: u8) -> Result<f32, Error> {
        // OS=1 start | MUX=100+ch (AINx vs GND) | PGA=001 (±4.096 V) | MODE=1 single-shot | DR=100 (128 SPS) | comparator off
        let cfg: u16 = 0x8000 | (((4 + (ch as u16 & 3)) << 12) as u16) | (1 << 9) | (1 << 8) | (4 << 5) | 0b11;
        self.i2c.write_async(self.addr as u16, [REG_CONFIG, (cfg >> 8) as u8, cfg as u8]).await?;
        Timer::after_millis(9).await; // 1/128 s conversion + margin
        let mut buf = [0u8; 2];
        self.i2c.write_read_async(self.addr as u16, [REG_CONVERSION], &mut buf).await?;
        let raw = i16::from_be_bytes(buf);
        Ok(raw as f32 * FULL_SCALE_V / 32768.0)
    }
}
