//! OPL (Open Peltier Link) framing and payloads. Port of `obc/protocol.py`; spec in
//! docs/design/04-firmware-protocol.md. Fixed-size buffers, no allocation.

pub const VERSION: u8 = 1;
/// Largest body (header + payload + crc) we accept. Sensor blocks are ~920 B.
pub const MAX_BODY: usize = 1024;
/// Worst-case COBS overhead: 1 byte per 254 + 1, plus the 0x00 delimiter.
pub const MAX_WIRE: usize = MAX_BODY + MAX_BODY / 254 + 2;

pub mod msg {
    pub const HEARTBEAT: u8 = 0x01;
    pub const SET_TARGET: u8 = 0x10;
    pub const CLEAR_FAULTS: u8 = 0x11;
    pub const PRIME: u8 = 0x12;
    pub const TELEMETRY: u8 = 0x80;
    pub const FAULT: u8 = 0x81;
    pub const SENSOR_BLOCK: u8 = 0x90;
    pub const ACK: u8 = 0xF0;
}

#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum Error {
    TooLong,
    ZeroInFrame,
    Truncated,
    TooShort,
    BadCrc,
    BadVersion,
    BadPayload,
}

/// CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF).
pub fn crc16_ccitt_false(data: &[u8]) -> u16 {
    let mut crc: u16 = 0xFFFF;
    for &b in data {
        crc ^= (b as u16) << 8;
        for _ in 0..8 {
            crc = if crc & 0x8000 != 0 { (crc << 1) ^ 0x1021 } else { crc << 1 };
        }
    }
    crc
}

/// COBS-encode `data` into `out`; returns the number of bytes written (no trailing 0x00).
pub fn cobs_encode(data: &[u8], out: &mut [u8]) -> Result<usize, Error> {
    let mut code_idx = 0usize;
    let mut w = 1usize;
    let mut code: u8 = 1;
    let put = |out: &mut [u8], i: usize, v: u8| -> Result<(), Error> {
        *out.get_mut(i).ok_or(Error::TooLong)? = v;
        Ok(())
    };
    for &b in data {
        if b == 0 {
            put(out, code_idx, code)?;
            code_idx = w;
            w += 1;
            code = 1;
        } else {
            put(out, w, b)?;
            w += 1;
            code += 1;
            if code == 0xFF {
                put(out, code_idx, code)?;
                code_idx = w;
                w += 1;
                code = 1;
            }
        }
    }
    put(out, code_idx, code)?;
    Ok(w)
}

/// COBS-decode `data` (without delimiter) into `out`; returns the decoded length.
pub fn cobs_decode(data: &[u8], out: &mut [u8]) -> Result<usize, Error> {
    let mut r = 0usize;
    let mut w = 0usize;
    while r < data.len() {
        let code = data[r];
        if code == 0 {
            return Err(Error::ZeroInFrame);
        }
        let end = r + code as usize;
        if end > data.len() {
            return Err(Error::Truncated);
        }
        for &b in &data[r + 1..end] {
            *out.get_mut(w).ok_or(Error::TooLong)? = b;
            w += 1;
        }
        r = end;
        if code < 0xFF && r < data.len() {
            *out.get_mut(w).ok_or(Error::TooLong)? = 0;
            w += 1;
        }
    }
    Ok(w)
}

/// Encode a frame (header + payload + crc, COBS, 0x00) into `out`. Returns the wire length.
pub fn encode(seq: u8, typ: u8, payload: &[u8], out: &mut [u8]) -> Result<usize, Error> {
    let n = 3 + payload.len() + 2;
    if n > MAX_BODY {
        return Err(Error::TooLong);
    }
    let mut body = [0u8; MAX_BODY];
    body[0] = VERSION;
    body[1] = seq;
    body[2] = typ;
    body[3..3 + payload.len()].copy_from_slice(payload);
    let crc = crc16_ccitt_false(&body[..n - 2]);
    body[n - 2..n].copy_from_slice(&crc.to_le_bytes());
    let w = cobs_encode(&body[..n], out)?;
    *out.get_mut(w).ok_or(Error::TooLong)? = 0;
    Ok(w + 1)
}

/// A decoded frame borrowing its payload from the decoder's buffer.
#[derive(Debug, PartialEq, Eq)]
pub struct Frame<'a> {
    pub seq: u8,
    pub typ: u8,
    pub payload: &'a [u8],
}

/// Decode one COBS frame (delimiter stripped) into `scratch`.
pub fn decode<'a>(wire: &[u8], scratch: &'a mut [u8; MAX_BODY]) -> Result<Frame<'a>, Error> {
    let n = cobs_decode(wire, scratch)?;
    if n < 5 {
        return Err(Error::TooShort);
    }
    let crc = u16::from_le_bytes([scratch[n - 2], scratch[n - 1]]);
    if crc != crc16_ccitt_false(&scratch[..n - 2]) {
        return Err(Error::BadCrc);
    }
    if scratch[0] != VERSION {
        return Err(Error::BadVersion);
    }
    Ok(Frame { seq: scratch[1], typ: scratch[2], payload: &scratch[3..n - 2] })
}

/// Byte-wise stream decoder for a UART. Call `push` per received byte; when it returns
/// `Some(len)`, the raw COBS frame is in `raw()[..len]`, ready for `decode`.
pub struct StreamDecoder {
    buf: [u8; MAX_WIRE],
    len: usize,
    overflow: bool,
    pub errors: u32,
}

impl Default for StreamDecoder {
    fn default() -> Self {
        Self { buf: [0; MAX_WIRE], len: 0, overflow: false, errors: 0 }
    }
}

impl StreamDecoder {
    pub fn push(&mut self, b: u8) -> Option<usize> {
        if b == 0 {
            let n = self.len;
            let bad = self.overflow;
            self.len = 0;
            self.overflow = false;
            if bad {
                self.errors += 1;
                return None;
            }
            return if n > 0 { Some(n) } else { None };
        }
        if self.len < self.buf.len() {
            self.buf[self.len] = b;
            self.len += 1;
        } else {
            self.overflow = true;
        }
        None
    }

    pub fn raw(&self) -> &[u8] {
        &self.buf
    }
}

// ---- typed payloads ------------------------------------------------------------------

pub const INVALID_CENTI: i16 = i16::MIN;

pub fn centi(c: Option<f32>) -> i16 {
    match c {
        Some(v) if v.is_finite() => libm::roundf(v * 100.0).clamp(-32767.0, 32767.0) as i16,
        _ => INVALID_CENTI,
    }
}

/// SET_TARGET payload: side:u8 enable:u8 centi_c:i16 -> (side, Some(degC) | None)
pub fn parse_set_target(p: &[u8]) -> Result<(u8, Option<f32>), Error> {
    if p.len() != 4 {
        return Err(Error::BadPayload);
    }
    let c = i16::from_le_bytes([p[2], p[3]]);
    Ok((p[0], if p[1] != 0 { Some(c as f32 / 100.0) } else { None }))
}

pub fn set_target(side: u8, centi_c: Option<i16>, out: &mut [u8; 4]) {
    out[0] = side;
    out[1] = centi_c.is_some() as u8;
    out[2..4].copy_from_slice(&centi_c.unwrap_or(0).to_le_bytes());
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct SideTelemetry {
    pub t_water: i16,
    pub t_hot_face: i16,
    pub target: i16,
    pub tec_ma: i16,
    pub flow_mlpm: u16,
    pub fan_pct: u8,
    pub mode: u8,
    pub faults: u16,
}

pub const SIDE_TELEMETRY_LEN: usize = 14;
pub const TELEMETRY_LEN: usize = 7 + 2 * SIDE_TELEMETRY_LEN;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Telemetry {
    pub uptime_ms: u32,
    pub t_ambient: i16,
    pub water_level_pct: u8,
    pub sides: [SideTelemetry; 2],
}

impl Telemetry {
    pub fn pack(&self, out: &mut [u8; TELEMETRY_LEN]) {
        out[0..4].copy_from_slice(&self.uptime_ms.to_le_bytes());
        out[4..6].copy_from_slice(&self.t_ambient.to_le_bytes());
        out[6] = self.water_level_pct;
        for (k, s) in self.sides.iter().enumerate() {
            let o = 7 + k * SIDE_TELEMETRY_LEN;
            out[o..o + 2].copy_from_slice(&s.t_water.to_le_bytes());
            out[o + 2..o + 4].copy_from_slice(&s.t_hot_face.to_le_bytes());
            out[o + 4..o + 6].copy_from_slice(&s.target.to_le_bytes());
            out[o + 6..o + 8].copy_from_slice(&s.tec_ma.to_le_bytes());
            out[o + 8..o + 10].copy_from_slice(&s.flow_mlpm.to_le_bytes());
            out[o + 10] = s.fan_pct;
            out[o + 11] = s.mode;
            out[o + 12..o + 14].copy_from_slice(&s.faults.to_le_bytes());
        }
    }
}

pub fn fault_payload(side: u8, faults: u16) -> [u8; 3] {
    let f = faults.to_le_bytes();
    [side, f[0], f[1]]
}

pub fn ack_payload(acked_seq: u8, status: u8) -> [u8; 2] {
    [acked_seq, status]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn crc_reference() {
        assert_eq!(crc16_ccitt_false(b"123456789"), 0x29B1);
    }

    #[test]
    fn cobs_roundtrip_edge_lengths() {
        let mut seed: u32 = 1;
        let mut rnd = || {
            seed = seed.wrapping_mul(1_103_515_245).wrapping_add(12345);
            (seed >> 16) as u8
        };
        for n in [0usize, 1, 253, 254, 255, 600] {
            for _ in 0..20 {
                let data: Vec<u8> = (0..n).map(|_| if rnd() % 3 == 0 { 0 } else { rnd() }).collect();
                let mut enc = [0u8; 700];
                let m = cobs_encode(&data, &mut enc).unwrap();
                assert!(!enc[..m].contains(&0));
                let mut dec = [0u8; 700];
                let k = cobs_decode(&enc[..m], &mut dec).unwrap();
                assert_eq!(&dec[..k], &data[..]);
            }
        }
    }

    #[test]
    fn stream_resyncs_after_corruption() {
        let mut a = [0u8; 32];
        let na = encode(1, msg::HEARTBEAT, &[], &mut a).unwrap();
        a[2] ^= 0x40;
        let mut b = [0u8; 32];
        let nb = encode(2, msg::HEARTBEAT, &[], &mut b).unwrap();
        let mut d = StreamDecoder::default();
        let mut seqs = vec![];
        for &x in a[..na].iter().chain(b[..nb].iter()) {
            if let Some(n) = d.push(x) {
                let raw: Vec<u8> = d.raw()[..n].to_vec();
                let mut s = [0u8; MAX_BODY];
                match decode(&raw, &mut s) {
                    Ok(f) => seqs.push(f.seq),
                    Err(_) => d.errors += 1,
                }
            }
        }
        assert_eq!(seqs, vec![2]);
        assert_eq!(d.errors, 1);
    }
}
