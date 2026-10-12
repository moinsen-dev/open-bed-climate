// OPL (Open Peltier Link) for the hub side: framing + payloads. Header-only, no ESPHome dependency,
// so it is host-tested (test/test_opl.cpp) against the same golden frames as Python and Rust.
// Spec: docs/design/04-firmware-protocol.md
#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace openbed {
namespace opl {

static const uint8_t VERSION = 1;
static const size_t MAX_BODY = 1024;
static const size_t MAX_WIRE = MAX_BODY + MAX_BODY / 254 + 2;
static const int16_t INVALID_CENTI = INT16_MIN;

enum MsgType : uint8_t {
  HEARTBEAT = 0x01,
  SET_TARGET = 0x10,
  CLEAR_FAULTS = 0x11,
  PRIME = 0x12,
  FW_BEGIN = 0x20,  // size:u32 crc32:u32 version:u32 (firmware update, see opl_fw.h)
  FW_CHUNK = 0x21,  // offset:u32 data[1..256]
  FW_END = 0x22,
  FW_ABORT = 0x23,
  FW_QUERY = 0x24,
  TELEMETRY = 0x80,
  FAULT = 0x81,
  FW_STATUS = 0x82,  // acked_seq:u8 state:u8 result:u8 next_offset:u32 running_version:u32
  SENSOR_BLOCK = 0x90,
  ACK = 0xF0,
};

// Fault bits (u16), see 04-firmware-protocol.md.
enum FaultBit : uint16_t {
  WATER_OVERTEMP = 1 << 0,
  WATER_UNDERTEMP = 1 << 1,
  HOT_FACE_OVERTEMP = 1 << 2,
  NO_FLOW = 1 << 3,
  LEAK = 1 << 4,
  SENSOR_INVALID = 1 << 5,
  HOST_TIMEOUT = 1 << 6,
  LOW_WATER = 1 << 7,
  DRIVER_COMM = 1 << 8,
  FAN_STALL = 1 << 9,
};

inline uint16_t crc16_ccitt_false(const uint8_t *data, size_t len) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < len; i++) {
    crc ^= (uint16_t) data[i] << 8;
    for (int b = 0; b < 8; b++)
      crc = (crc & 0x8000) ? (uint16_t) ((crc << 1) ^ 0x1021) : (uint16_t) (crc << 1);
  }
  return crc;
}

// COBS encode; returns bytes written (no delimiter) or 0 if `out` is too small.
inline size_t cobs_encode(const uint8_t *data, size_t len, uint8_t *out, size_t cap) {
  size_t code_idx = 0, w = 1;
  uint8_t code = 1;
  if (cap == 0)
    return 0;
  for (size_t i = 0; i < len; i++) {
    if (data[i] == 0) {
      out[code_idx] = code;
      code_idx = w++;
      code = 1;
    } else {
      if (w >= cap)
        return 0;
      out[w++] = data[i];
      if (++code == 0xFF) {
        out[code_idx] = code;
        code_idx = w++;
        code = 1;
      }
    }
    if (w > cap)
      return 0;
  }
  out[code_idx] = code;
  return w;
}

// COBS decode; returns decoded length or -1 on malformed input / overflow.
inline int cobs_decode(const uint8_t *data, size_t len, uint8_t *out, size_t cap) {
  size_t r = 0, w = 0;
  while (r < len) {
    uint8_t code = data[r];
    if (code == 0 || r + code > len)
      return -1;
    for (size_t i = r + 1; i < r + code; i++) {
      if (w >= cap)
        return -1;
      out[w++] = data[i];
    }
    r += code;
    if (code < 0xFF && r < len) {
      if (w >= cap)
        return -1;
      out[w++] = 0;
    }
  }
  return (int) w;
}

// Encode a full frame including the trailing 0x00. Returns wire length, 0 on error.
inline size_t encode(uint8_t seq, uint8_t type, const uint8_t *payload, size_t plen, uint8_t *out, size_t cap) {
  uint8_t body[MAX_BODY];
  size_t n = 3 + plen + 2;
  if (n > MAX_BODY)
    return 0;
  body[0] = VERSION;
  body[1] = seq;
  body[2] = type;
  if (plen)
    std::memcpy(body + 3, payload, plen);
  uint16_t crc = crc16_ccitt_false(body, n - 2);
  body[n - 2] = crc & 0xFF;
  body[n - 1] = crc >> 8;
  size_t w = cobs_encode(body, n, out, cap);
  if (w == 0 || w >= cap)
    return 0;
  out[w] = 0;
  return w + 1;
}

struct Frame {
  uint8_t seq;
  uint8_t type;
  const uint8_t *payload;
  size_t len;
};

// Byte-wise decoder: feed bytes, returns true when `frame` holds a valid frame (payload points
// into the decoder's buffer and stays valid until the next push()).
class StreamDecoder {
 public:
  uint32_t errors{0};

  bool push(uint8_t b, Frame &frame) {
    if (b != 0) {
      if (len_ < sizeof(raw_))
        raw_[len_++] = b;
      else
        overflow_ = true;
      return false;
    }
    size_t n = len_;
    bool bad = overflow_;
    len_ = 0;
    overflow_ = false;
    if (n == 0)
      return false;
    int m = bad ? -1 : cobs_decode(raw_, n, body_, sizeof(body_));
    if (m < 5) {
      errors++;
      return false;
    }
    uint16_t crc = body_[m - 2] | (body_[m - 1] << 8);
    if (crc != crc16_ccitt_false(body_, m - 2) || body_[0] != VERSION) {
      errors++;
      return false;
    }
    frame = Frame{body_[1], body_[2], body_ + 3, (size_t) m - 5};
    return true;
  }

 private:
  uint8_t raw_[MAX_WIRE];
  uint8_t body_[MAX_BODY];
  size_t len_{0};
  bool overflow_{false};
};

inline int16_t rd_i16(const uint8_t *p) { return (int16_t) (p[0] | (p[1] << 8)); }
inline uint16_t rd_u16(const uint8_t *p) { return (uint16_t) (p[0] | (p[1] << 8)); }
inline uint32_t rd_u32(const uint8_t *p) {
  return (uint32_t) p[0] | ((uint32_t) p[1] << 8) | ((uint32_t) p[2] << 16) | ((uint32_t) p[3] << 24);
}
inline void wr_u32(uint8_t *p, uint32_t v) {
  for (int i = 0; i < 4; i++)
    p[i] = (uint8_t) (v >> (8 * i));
}

inline float centi_to_c(int16_t v) { return v == INVALID_CENTI ? NAN : v / 100.0f; }

// SET_TARGET payload: side:u8 enable:u8 centi_c:i16. NaN target = zone off.
inline void set_target_payload(uint8_t side, float target_c, uint8_t out[4]) {
  bool on = !std::isnan(target_c);
  int16_t c = on ? (int16_t) std::lround(target_c * 100.0f) : 0;
  out[0] = side;
  out[1] = on ? 1 : 0;
  out[2] = c & 0xFF;
  out[3] = (c >> 8) & 0xFF;
}

struct SideTelemetry {
  float t_water;     // degC, NaN = invalid
  float t_hot_face;  // degC
  float target;      // degC, NaN = off
  float tec_a;       // per-TEC current, >0 cooling
  float flow_lpm;
  uint8_t fan_pct;
  uint8_t mode;  // 0 off, 1 run, 2 safe
  uint16_t faults;
};

struct Telemetry {
  uint32_t uptime_ms;
  float t_ambient;
  uint8_t water_level_pct;
  SideTelemetry sides[2];
};

static const size_t TELEMETRY_LEN = 7 + 2 * 14;

inline bool parse_telemetry(const uint8_t *p, size_t len, Telemetry &t) {
  if (len != TELEMETRY_LEN)
    return false;
  t.uptime_ms = (uint32_t) p[0] | (p[1] << 8) | (p[2] << 16) | ((uint32_t) p[3] << 24);
  t.t_ambient = centi_to_c(rd_i16(p + 4));
  t.water_level_pct = p[6];
  for (int k = 0; k < 2; k++) {
    const uint8_t *s = p + 7 + 14 * k;
    SideTelemetry &o = t.sides[k];
    o.t_water = centi_to_c(rd_i16(s));
    o.t_hot_face = centi_to_c(rd_i16(s + 2));
    o.target = centi_to_c(rd_i16(s + 4));
    o.tec_a = rd_i16(s + 6) / 1000.0f;
    o.flow_lpm = rd_u16(s + 8) / 1000.0f;
    o.fan_pct = s[10];
    o.mode = s[11];
    o.faults = rd_u16(s + 12);
  }
  return true;
}

}  // namespace opl
}  // namespace openbed
