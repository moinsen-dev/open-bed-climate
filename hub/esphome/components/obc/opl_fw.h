// OPL firmware update, hub side: UF2 -> flat image, and the sender state machine that streams it to the Pico 2.
// Header-only, no ESPHome dependency, host-tested in test/test_opl.cpp against a simulated MCU.
// Protocol: docs/design/04-firmware-protocol.md (Firmware update). MCU side: firmware/obc-core/src/fwupdate.rs.
//
// Stop-and-wait: exactly one FW frame in flight, and the hub sends NOTHING else (no heartbeat, no targets) until its
// FW_STATUS arrives, because the MCU masks interrupts while it erases/programs flash. Every frame is retried on timeout.
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>

#include "opl.h"

namespace openbed {
namespace opl {

static const size_t FW_CHUNK_MAX = 256;
static const uint32_t UF2_FAMILY_RP2350_ARM_S = 0xe48bff59;
static const uint32_t PICO_FLASH_BASE = 0x10000000;

enum FwState : uint8_t { FW_IDLE = 0, FW_RECEIVING = 1, FW_DONE = 2 };
enum FwResult : uint8_t {
  FW_OK = 0,
  FW_BUSY = 1,
  FW_NO_SESSION = 2,
  FW_TOO_LARGE = 3,
  FW_BAD_OFFSET = 4,
  FW_BAD_CRC = 5,
  FW_FLASH_ERROR = 6,
  FW_BAD_PAYLOAD = 7,
  FW_NO_PARTITIONS = 8,
  FW_INCOMPLETE = 9,
};

// CRC-32/ISO-HDLC (zlib), chainable. crc32("123456789") == 0xCBF43926.
inline uint32_t crc32(const uint8_t *data, size_t len, uint32_t crc = 0) {
  crc = ~crc;
  for (size_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (int b = 0; b < 8; b++)
      crc = (crc & 1) ? (crc >> 1) ^ 0xEDB88320u : crc >> 1;
  }
  return ~crc;
}

struct FwStatus {
  uint8_t acked_seq;
  uint8_t state;
  uint8_t result;
  uint32_t next_offset;
  uint32_t running_version;
};

inline bool parse_fw_status(const uint8_t *p, size_t len, FwStatus &s) {
  if (len != 11)
    return false;
  s = FwStatus{p[0], p[1], p[2], rd_u32(p + 3), rd_u32(p + 7)};
  return true;
}

// Flatten a Pico 2 release UF2 (rp2350-arm-s blocks at 0x10000000.., plus the RP2350-E10 "absolute" block, which is
// skipped) into `out`. Gaps are filled with 0xFF (erased flash). Returns the image size, 0 if malformed or too big.
inline size_t uf2_to_image(const uint8_t *uf2, size_t len, uint8_t *out, size_t cap) {
  if (len == 0 || len % 512)
    return 0;
  size_t size = 0;
  for (size_t o = 0; o < len; o += 512) {
    const uint8_t *b = uf2 + o;
    if (rd_u32(b) != 0x0A324655 || rd_u32(b + 4) != 0x9E5D5157 || rd_u32(b + 508) != 0x0AB16F30)
      return 0;
    uint32_t flags = rd_u32(b + 8), addr = rd_u32(b + 12), n = rd_u32(b + 16), family = rd_u32(b + 28);
    if (!(flags & 0x2000) || family != UF2_FAMILY_RP2350_ARM_S)
      continue;  // not our family (e.g. the E10 absolute block)
    if (n > 476 || addr < PICO_FLASH_BASE || addr - PICO_FLASH_BASE + n > cap)
      return 0;
    size_t at = addr - PICO_FLASH_BASE;
    if (at > size)
      std::memset(out + size, 0xFF, at - size);
    std::memcpy(out + at, b + 32, n);
    if (at + n > size)
      size = at + n;
  }
  return size;
}

// Image version word as stored in the Pico's IMAGE_DEF: 0xMMmmPPPP.
inline uint32_t fw_version_word(uint8_t major, uint8_t minor, uint16_t patch) {
  return ((uint32_t) major << 24) | ((uint32_t) minor << 16) | patch;
}

// Version from the image's IMAGE_DEF block (RP2350 block in the first 4 KiB: 0xffffded3, items, 0xab123579).
// Returns 0 if the image carries no VERSION item.
inline uint32_t image_version(const uint8_t *img, size_t size) {
  size_t lim = size < 4096 ? size : 4096;
  for (size_t o = 0; o + 8 <= lim; o += 4) {
    if (rd_u32(img + o) != 0xffffded3)
      continue;
    size_t i = o + 4;
    while (i + 4 <= lim) {
      uint32_t w = rd_u32(img + i);
      uint8_t type = w & 0xFF;
      if (type == 0xFF)
        break;  // BLOCK_LAST
      uint32_t words = (type & 0x40) ? ((w >> 8) & 0xFF) : ((w >> 8) & 0xFFFF);  // 1-byte / 2-byte size items
      if (words == 0)
        break;
      if (type == 0x48 && i + 8 <= lim)  // VERSION: next word is major << 16 | minor
        return rd_u32(img + i + 4);
      i += 4 * words;
    }
  }
  return 0;
}

class FwSender {
 public:
  enum Phase : uint8_t { IDLE, QUERY, BEGIN, SEND, END, CONFIRM, DONE, FAILED };
  static const uint32_t TIMEOUT_MS = 2000;  // > worst-case sector erase (~400 ms) + program + UART
  static const int MAX_RETRIES = 5;
  static const uint32_t BUSY_RETRY_MS = 500;
  static const int BUSY_RETRIES = 20;  // zones were just switched off: the MCU sees it within one 100 ms cycle
  static const uint32_t CONFIRM_DELAY_MS = 8000;  // reboot + boot + a few control cycles

  // Refuses (returns false, phase FAILED) during the night program unless forced: the Pico has no wall clock, so
  // this guard lives on the hub. The caller must have switched every zone off (the MCU refuses otherwise).
  bool start(const uint8_t *image, size_t size, uint32_t version, bool night_active, bool force) {
    *this = FwSender();
    if (night_active && !force)
      return this->fail_("refused: night program running (use force)");
    if (size == 0)
      return this->fail_("empty image");
    this->image_ = image;
    this->size_ = size;
    this->crc_ = crc32(image, size);
    this->version_ = version;
    this->phase_ = QUERY;  // learn the running version first, so CONFIRM can tell a real switch from a rollback
    return true;
  }

  // Next frame to send, if any. The caller sends it with the given `type`/payload and reports the seq via sent().
  bool poll(uint32_t now, uint8_t &type, uint8_t *payload, size_t &len) {
    if (this->abort_pending_) {
      this->abort_pending_ = false;
      type = FW_ABORT;
      len = 0;
      return true;
    }
    if (this->in_flight_) {
      if (now - this->sent_at_ < TIMEOUT_MS)
        return false;
      if (++this->retries_ > MAX_RETRIES) {
        bool open = this->phase_ == SEND || this->phase_ == END;
        this->fail_("no answer from the MCU");
        this->abort_pending_ = open;  // best effort: release the MCU's session so the zones can run again
        return false;
      }
      this->in_flight_ = false;  // resend below
    }
    if ((int32_t) (now - this->not_before_) < 0)
      return false;
    switch (this->phase_) {
      case QUERY:
      case CONFIRM:
        type = FW_QUERY;
        len = 0;
        break;
      case BEGIN:
        type = FW_BEGIN;
        wr_u32(payload, (uint32_t) this->size_);
        wr_u32(payload + 4, this->crc_);
        wr_u32(payload + 8, this->version_);
        len = 12;
        break;
      case SEND: {
        size_t n = this->size_ - this->offset_;
        if (n > FW_CHUNK_MAX)
          n = FW_CHUNK_MAX;
        type = FW_CHUNK;
        wr_u32(payload, this->offset_);
        std::memcpy(payload + 4, this->image_ + this->offset_, n);
        len = 4 + n;
        break;
      }
      case END:
        type = FW_END;
        len = 0;
        break;
      default:
        return false;
    }
    return true;
  }

  void sent(uint8_t seq, uint32_t now) {
    this->seq_ = seq;
    this->sent_at_ = now;
    this->in_flight_ = true;
  }

  void on_status(const FwStatus &st, uint32_t now) {
    if (!this->in_flight_ || st.acked_seq != this->seq_)
      return;  // stale answer to a frame we already gave up on
    this->in_flight_ = false;
    this->retries_ = 0;
    switch (this->phase_) {
      case QUERY:
        this->old_version_ = st.running_version;
        this->phase_ = BEGIN;
        break;
      case BEGIN:
        if (st.result == FW_OK && st.state == FW_RECEIVING) {
          this->offset_ = 0;
          this->phase_ = SEND;
        } else if (st.result == FW_BUSY && ++this->busy_retries_ <= BUSY_RETRIES) {
          this->not_before_ = now + BUSY_RETRY_MS;
        } else {
          this->fail_result_("FW_BEGIN refused", st.result);
        }
        break;
      case SEND:
      case END:
        if (this->phase_ == END && (st.state == FW_DONE || (st.state == FW_IDLE && st.result == FW_NO_SESSION))) {
          // DONE, or our resent FW_END reached the new image after the reboot (the first answer got lost).
          this->phase_ = CONFIRM;
          this->not_before_ = now + (st.state == FW_DONE ? CONFIRM_DELAY_MS : 0);
          this->retries_ = -MAX_RETRIES;  // the MCU is rebooting: allow more silence
        } else if (st.state == FW_RECEIVING && (st.result == FW_OK || st.result == FW_BAD_OFFSET ||
                                                st.result == FW_INCOMPLETE)) {
          this->offset_ = st.next_offset;  // progress, or resync to where the MCU is
          this->phase_ = this->offset_ >= this->size_ ? END : SEND;
        } else {
          this->fail_result_("transfer failed", st.result);
          this->abort_pending_ = st.state == FW_RECEIVING;
        }
        break;
      case CONFIRM:
        this->running_version_ = st.running_version;
        if (st.running_version == this->version_) {
          this->phase_ = DONE;
          // Same version as before the update: the switch can't be told apart from a rollback.
          this->verified_ = this->version_ != this->old_version_;
          this->error_ = "";
        } else {
          this->fail_("the MCU still runs the previous image (trial boot failed and rolled back?)");
        }
        break;
      default:
        break;
    }
  }

  Phase phase() const { return this->phase_; }
  // Zones must stay off and the hub must send nothing but FW frames while this is true.
  bool active() const {
    return this->phase_ == QUERY || this->phase_ == BEGIN || this->phase_ == SEND || this->phase_ == END ||
           this->abort_pending_;
  }
  bool busy() const { return this->active() || this->phase_ == CONFIRM; }
  size_t progress() const { return this->offset_; }
  size_t size() const { return this->size_; }
  uint8_t last_result() const { return this->result_; }
  uint32_t running_version() const { return this->running_version_; }
  // DONE and the MCU reports a different version than before: the new image really runs.
  bool verified() const { return this->phase_ == DONE && this->verified_; }
  const char *error() const { return this->error_; }

 protected:
  bool fail_(const char *why) {
    this->phase_ = FAILED;
    this->error_ = why;
    return false;
  }
  void fail_result_(const char *why, uint8_t result) {
    this->result_ = result;
    this->fail_(why);
  }

  const uint8_t *image_{nullptr};
  size_t size_{0};
  uint32_t crc_{0};
  uint32_t version_{0};
  uint32_t offset_{0};
  Phase phase_{IDLE};
  bool in_flight_{false};
  bool abort_pending_{false};
  uint8_t seq_{0};
  uint32_t sent_at_{0};
  uint32_t not_before_{0};
  int retries_{0};
  int busy_retries_{0};
  uint8_t result_{FW_OK};
  uint32_t running_version_{0};
  uint32_t old_version_{0};
  bool verified_{false};
  const char *error_{""};
};

}  // namespace opl
}  // namespace openbed
