#include "obc.h"

#include "esphome/core/hal.h"
#include "esphome/core/log.h"

#include <cmath>

namespace esphome {
namespace obc {

static const char *const TAG = "obc";
static const uint32_t HEARTBEAT_MS = 1000;
static const uint32_t RESEND_MS = 10000;
static const uint32_t LINK_TIMEOUT_MS = 5000;
// Temperature range the MCU accepts; the MCU clamps anyway, this only shapes the UI.
static const float MIN_C = 13.0f;
static const float MAX_C = 43.0f;

// ---- hub ----------------------------------------------------------------------------------

void ObcHub::setup() { this->publish_link_lost_(); }

void ObcHub::loop() {
  opl::Frame f{};
  uint8_t b;
  while (this->available() && this->read_byte(&b)) {
    if (this->decoder_.push(b, f))
      this->handle_frame_(f);
  }

  const uint32_t now = millis();
  if (now - this->last_heartbeat_ms_ >= HEARTBEAT_MS) {
    this->last_heartbeat_ms_ = now;
    this->send_(opl::HEARTBEAT, nullptr, 0);
  }
  if (now - this->last_resend_ms_ >= RESEND_MS) {
    this->last_resend_ms_ = now;
    for (int z = 0; z < ZONES; z++)
      if (this->climates_[z] != nullptr)
        this->send_target_(z);
  }
  if (this->link_ok_ && now - this->last_telemetry_ms_ > LINK_TIMEOUT_MS) {
    ESP_LOGW(TAG, "No telemetry from the control board for %u ms", (unsigned) LINK_TIMEOUT_MS);
    this->publish_link_lost_();
  }
}

void ObcHub::dump_config() {
  ESP_LOGCONFIG(TAG, "Open Bed Climate hub (OPL v%u)", opl::VERSION);
  ESP_LOGCONFIG(TAG, "  decode errors: %u", (unsigned) this->decoder_.errors);
  this->check_uart_settings(460800);
}

void ObcHub::send_(uint8_t type, const uint8_t *payload, size_t len) {
  uint8_t wire[64];  // hub->MCU frames are tiny
  size_t n = opl::encode(this->seq_++, type, payload, len, wire, sizeof(wire));
  if (n > 0)
    this->write_array(wire, n);
}

void ObcHub::send_target_(int zone) {
  float room_t = this->room_t_ != nullptr ? this->room_t_->state : NAN;
  float room_rh = this->room_rh_ != nullptr ? this->room_rh_->state : NAN;
  float target = guard::guarded_target(this->desired_[zone], room_t, room_rh);
  if (target != this->desired_[zone])
    ESP_LOGI(TAG, "Zone %d: %.1f °C raised to %.1f °C (dew-point guard)", zone, this->desired_[zone], target);
  uint8_t p[4];
  opl::set_target_payload((uint8_t) zone, target, p);
  this->send_(opl::SET_TARGET, p, sizeof(p));
}

void ObcHub::set_desired(int zone, float target_c) {
  if (zone < 0 || zone >= ZONES)
    return;
  this->desired_[zone] = target_c;
  this->send_target_(zone);
}

void ObcHub::prime() {
  ESP_LOGI(TAG, "Priming requested");
  this->send_(opl::PRIME, nullptr, 0);
}

void ObcHub::clear_faults(int zone) {
  // A latched fault (over-temperature, leak, sensor) is only cleared by this explicit user action.
  ESP_LOGW(TAG, "Clear faults requested for zone %d", zone);
  uint8_t p[1] = {(uint8_t) zone};
  this->send_(opl::CLEAR_FAULTS, p, 1);
}

void ObcHub::handle_frame_(const opl::Frame &f) {
  switch (f.type) {
    case opl::TELEMETRY: {
      opl::Telemetry t{};
      if (opl::parse_telemetry(f.payload, f.len, t)) {
        this->last_telemetry_ms_ = millis();
        if (!this->link_ok_) {
          ESP_LOGI(TAG, "Control board link up");
          this->link_ok_ = true;
          if (this->link_ != nullptr)
            this->link_->publish_state(true);
        }
        this->publish_telemetry_(t);
      }
      break;
    }
    case opl::FAULT:
      if (f.len == 3)
        ESP_LOGW(TAG, "Zone %u faults 0x%04X", f.payload[0], f.payload[1] | (f.payload[2] << 8));
      break;
    case opl::ACK:
      if (f.len == 2 && f.payload[1] != 0)
        ESP_LOGW(TAG, "Control board rejected command seq %u (status %u)", f.payload[0], f.payload[1]);
      break;
    default:
      break;
  }
}

void ObcHub::publish_telemetry_(const opl::Telemetry &t) {
  for (int z = 0; z < ZONES; z++) {
    const opl::SideTelemetry &s = t.sides[z];
    if (this->climates_[z] != nullptr)
      this->climates_[z]->on_telemetry(s);
    if (this->water_[z] != nullptr)
      this->water_[z]->publish_state(s.t_water);
    if (this->hot_[z] != nullptr)
      this->hot_[z]->publish_state(s.t_hot_face);
    if (this->tec_[z] != nullptr)
      this->tec_[z]->publish_state(s.tec_a);
    if (this->flow_[z] != nullptr)
      this->flow_[z]->publish_state(s.flow_lpm);
    if (this->fault_code_[z] != nullptr)
      this->fault_code_[z]->publish_state(s.faults);
    if (this->fault_[z] != nullptr)
      this->fault_[z]->publish_state(s.faults != 0);
  }
}

void ObcHub::publish_link_lost_() {
  this->link_ok_ = false;
  if (this->link_ != nullptr)
    this->link_->publish_state(false);
  for (int z = 0; z < ZONES; z++) {
    if (this->climates_[z] != nullptr)
      this->climates_[z]->on_link_lost();
    // Without telemetry we cannot know the state: report a problem rather than "no fault".
    if (this->fault_[z] != nullptr)
      this->fault_[z]->publish_state(true);
  }
}

// ---- climate ------------------------------------------------------------------------------

void ObcClimate::setup() {
  auto restore = this->restore_state_();
  if (restore.has_value()) {
    restore->apply(this);
  } else {
    this->mode = climate::CLIMATE_MODE_OFF;
    this->target_temperature = 24.0f;
  }
  this->push_desired_();
}

void ObcClimate::dump_config() { LOG_CLIMATE("", "Open Bed Climate zone", this); }

climate::ClimateTraits ObcClimate::traits() {
  auto traits = climate::ClimateTraits();
  traits.add_feature_flags(climate::CLIMATE_SUPPORTS_CURRENT_TEMPERATURE | climate::CLIMATE_SUPPORTS_ACTION);
  traits.add_supported_mode(climate::CLIMATE_MODE_OFF);
  traits.add_supported_mode(climate::CLIMATE_MODE_HEAT_COOL);
  traits.set_visual_min_temperature(MIN_C);
  traits.set_visual_max_temperature(MAX_C);
  traits.set_visual_temperature_step(0.5f);
  return traits;
}

void ObcClimate::control(const climate::ClimateCall &call) {
  if (this->program_ != nullptr && this->program_->state) {
    ESP_LOGI(TAG, "Manual change: night program for zone %d ends", this->zone_);
    this->program_->turn_off();
  }
  if (call.get_mode().has_value())
    this->mode = *call.get_mode();
  if (call.get_target_temperature().has_value())
    this->target_temperature = clamp(*call.get_target_temperature(), MIN_C, MAX_C);
  this->push_desired_();
  this->publish_state();
}

void ObcClimate::push_desired_() {
  if (this->hub_ == nullptr)
    return;
  bool on = this->mode != climate::CLIMATE_MODE_OFF;
  this->hub_->set_desired(this->zone_, on ? this->target_temperature : NAN);
}

void ObcClimate::apply_program_target(float target_c) {
  if (std::isnan(target_c)) {
    this->mode = climate::CLIMATE_MODE_OFF;
  } else {
    this->mode = climate::CLIMATE_MODE_HEAT_COOL;
    this->target_temperature = clamp(target_c, MIN_C, MAX_C);
  }
  this->push_desired_();
  this->publish_state();
}

void ObcClimate::on_telemetry(const opl::SideTelemetry &s) {
  climate::ClimateAction action;
  if (s.mode != 1 || this->mode == climate::CLIMATE_MODE_OFF)
    action = climate::CLIMATE_ACTION_OFF;  // off, or safe state after a fault
  else if (s.tec_a > 0.05f)
    action = climate::CLIMATE_ACTION_COOLING;
  else if (s.tec_a < -0.05f)
    action = climate::CLIMATE_ACTION_HEATING;
  else
    action = climate::CLIMATE_ACTION_IDLE;
  // Telemetry arrives at 2 Hz; only publish real changes to keep Home Assistant traffic low.
  bool changed = action != this->action || std::isnan(this->current_temperature) != std::isnan(s.t_water) ||
                 std::fabs(this->current_temperature - s.t_water) >= 0.05f;
  this->current_temperature = s.t_water;
  this->action = action;
  if (changed)
    this->publish_state();
}

void ObcClimate::on_link_lost() {
  this->current_temperature = NAN;
  this->action = climate::CLIMATE_ACTION_OFF;
  this->publish_state();
}

// ---- night program ------------------------------------------------------------------------

static const uint32_t PROGRAM_TICK_MS = 30000;
// A program that is still "running" after this long was forgotten; stop it rather than run forever.
static const uint32_t PROGRAM_MAX_S = 16 * 3600;

void ObcProgram::setup() {
  this->pref_ = global_preferences->make_preference<Saved>(this->get_preference_hash());
  if (!this->pref_.load(&this->saved_))
    this->saved_ = Saved{0, -1};
  this->publish_state(this->saved_.start != 0);
  this->set_interval("program", PROGRAM_TICK_MS, [this]() { this->tick_(); });
}

void ObcProgram::dump_config() {
  LOG_SWITCH("", "Open Bed Climate night program", this);
  for (size_t i = 0; i < this->schedule_.n; i++)
    ESP_LOGCONFIG(TAG, "  +%.0f min: %.1f °C", this->schedule_.points[i].minute, this->schedule_.points[i].c);
  ESP_LOGCONFIG(TAG, "  wake ramp: %.0f min to %.1f °C (%s)", this->schedule_.wake_ramp_min,
                this->schedule_.wake_target_c, this->wake_ != nullptr ? "wake time entity set" : "no wake time");
}

void ObcProgram::write_state(bool state) {
  if (!state) {
    this->stop_();
    return;
  }
  ESPTime now = this->time_->now();
  if (!now.is_valid()) {
    ESP_LOGW(TAG, "Night program needs a valid time; not started");
    this->publish_state(false);
    return;
  }
  int32_t wake = -1;
  if (this->wake_ != nullptr && this->wake_->has_state())
    wake = sched::wake_offset_min(now.hour * 60 + now.minute, this->wake_->hour * 60 + this->wake_->minute);
  this->saved_ = Saved{(uint32_t) now.timestamp, wake};
  this->pref_.save(&this->saved_);
  ESP_LOGI(TAG, "Night program started, wake in %d min", (int) wake);
  this->publish_state(true);
  this->tick_();
}

void ObcProgram::tick_() {
  if (this->saved_.start == 0)
    return;
  ESPTime now = this->time_->now();
  if (!now.is_valid())
    return;  // keep the last target until the clock is back
  uint32_t elapsed = (uint32_t) now.timestamp - this->saved_.start;
  if ((int64_t) now.timestamp < (int64_t) this->saved_.start || elapsed > PROGRAM_MAX_S) {
    ESP_LOGW(TAG, "Night program expired");
    this->stop_();
    return;
  }
  float wake = this->saved_.wake_minute < 0 ? NAN : (float) this->saved_.wake_minute;
  float target = this->schedule_.setpoint(elapsed / 60.0f, wake);
  this->climate_->apply_program_target(target);
  if (std::isnan(target)) {
    ESP_LOGI(TAG, "Wake time reached: zone off, night program done");
    this->stop_();
  }
}

void ObcProgram::stop_() {
  this->saved_ = Saved{0, -1};
  this->pref_.save(&this->saved_);
  this->publish_state(false);
}

}  // namespace obc
}  // namespace esphome
