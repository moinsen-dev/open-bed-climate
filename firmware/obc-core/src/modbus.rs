//! Modbus RTU master frames for DPS-class programmable buck modules (Tier 0 TEC drivers).
//!
//! The register map below is the commonly documented DPS-series layout. Vendors change maps between
//! models and firmware versions (Riden RD60xx uses a different map), so **verify it against your
//! unit's protocol document** and adjust `DpsMap`. The firmware reads back the setpoints after writing.

/// CRC-16/MODBUS (poly 0xA001 reflected, init 0xFFFF). Transmitted low byte first.
pub fn crc16_modbus(data: &[u8]) -> u16 {
    let mut crc: u16 = 0xFFFF;
    for &b in data {
        crc ^= b as u16;
        for _ in 0..8 {
            crc = if crc & 1 != 0 { (crc >> 1) ^ 0xA001 } else { crc >> 1 };
        }
    }
    crc
}

/// Function 0x06: write single holding register. 8-byte frame.
pub fn write_single(addr: u8, reg: u16, value: u16) -> [u8; 8] {
    let mut f = [addr, 0x06, (reg >> 8) as u8, reg as u8, (value >> 8) as u8, value as u8, 0, 0];
    let c = crc16_modbus(&f[..6]);
    f[6] = c as u8;
    f[7] = (c >> 8) as u8;
    f
}

/// Function 0x03: read `count` holding registers. 8-byte frame.
pub fn read_holding(addr: u8, reg: u16, count: u16) -> [u8; 8] {
    let mut f = [addr, 0x03, (reg >> 8) as u8, reg as u8, (count >> 8) as u8, count as u8, 0, 0];
    let c = crc16_modbus(&f[..6]);
    f[6] = c as u8;
    f[7] = (c >> 8) as u8;
    f
}

#[derive(Debug, PartialEq, Eq)]
pub enum ModbusError {
    Short,
    Crc,
    Exception(u8),
    Unexpected,
}

/// Parse a 0x03 response into `out` registers; returns the number of registers.
pub fn parse_read_response(addr: u8, resp: &[u8], out: &mut [u16]) -> Result<usize, ModbusError> {
    if resp.len() < 5 {
        return Err(ModbusError::Short);
    }
    let n = resp.len();
    let crc = u16::from_le_bytes([resp[n - 2], resp[n - 1]]);
    if crc != crc16_modbus(&resp[..n - 2]) {
        return Err(ModbusError::Crc);
    }
    if resp[0] != addr {
        return Err(ModbusError::Unexpected);
    }
    if resp[1] == 0x83 {
        return Err(ModbusError::Exception(resp[2]));
    }
    if resp[1] != 0x03 {
        return Err(ModbusError::Unexpected);
    }
    let bytes = resp[2] as usize;
    if bytes % 2 != 0 || 3 + bytes + 2 != n || bytes / 2 > out.len() {
        return Err(ModbusError::Short);
    }
    for (k, o) in out.iter_mut().take(bytes / 2).enumerate() {
        *o = u16::from_be_bytes([resp[3 + 2 * k], resp[4 + 2 * k]]);
    }
    Ok(bytes / 2)
}

/// Register map + scaling of a DPS-class module.
#[derive(Clone, Copy, Debug)]
pub struct DpsMap {
    pub u_set: u16,
    pub i_set: u16,
    pub u_out: u16,
    pub i_out: u16,
    pub on_off: u16,
    /// Register units per volt / per amp (e.g. 100 = 0.01 V resolution).
    pub u_scale: f32,
    pub i_scale: f32,
}

/// Commonly documented DPS50xx layout (DPS5020: 0.01 V, 0.01 A). VERIFY for your unit.
pub const DPS5020: DpsMap =
    DpsMap { u_set: 0x0000, i_set: 0x0001, u_out: 0x0002, i_out: 0x0003, on_off: 0x0009, u_scale: 100.0, i_scale: 100.0 };

/// What the zone driver must send to realise a zone current. TECs are current-driven: the voltage
/// setpoint is only a ceiling, kept below the TEC Vmax (14.4 V) so a wrong current setting cannot
/// overdrive them.
pub const TEC_VOLTAGE_CEILING_V: f32 = 14.0;

pub fn zone_setpoint_frames(addr: u8, map: &DpsMap, zone_current_a: f32) -> [[u8; 8]; 3] {
    let amps = zone_current_a.max(0.0);
    let i_reg = libm::roundf(amps * map.i_scale) as u16;
    let u_reg = libm::roundf(TEC_VOLTAGE_CEILING_V * map.u_scale) as u16;
    [
        write_single(addr, map.u_set, u_reg),
        write_single(addr, map.i_set, i_reg),
        write_single(addr, map.on_off, (amps > 0.0) as u16),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn crc_known_vector() {
        // Classic example: read 1 register at 0 from slave 1 -> CRC bytes 84 0A.
        assert_eq!(read_holding(1, 0, 1), [0x01, 0x03, 0x00, 0x00, 0x00, 0x01, 0x84, 0x0A]);
    }

    #[test]
    fn zone_frames_scale_and_cap_voltage() {
        let f = zone_setpoint_frames(1, &DPS5020, 18.0);
        assert_eq!(&f[0][2..6], &[0x00, 0x00, 0x05, 0x78]); // 14.00 V ceiling
        assert_eq!(&f[1][2..6], &[0x00, 0x01, 0x07, 0x08]); // 18.00 A
        assert_eq!(&f[2][2..6], &[0x00, 0x09, 0x00, 0x01]); // output on
        let off = zone_setpoint_frames(1, &DPS5020, 0.0);
        assert_eq!(&off[2][4..6], &[0x00, 0x00]);
    }

    #[test]
    fn parse_response() {
        let mut r = vec![0x01, 0x03, 0x04, 0x05, 0x78, 0x07, 0x08];
        let c = crc16_modbus(&r);
        r.extend_from_slice(&c.to_le_bytes());
        let mut regs = [0u16; 2];
        assert_eq!(parse_read_response(1, &r, &mut regs), Ok(2));
        assert_eq!(regs, [1400, 1800]);
        r[4] ^= 1;
        assert_eq!(parse_read_response(1, &r, &mut regs), Err(ModbusError::Crc));
    }
}
