#pragma once

#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/components/button/button.h"
#include "esphome/components/climate/climate.h"
#include "esphome/components/datetime/time_entity.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/switch/switch.h"
#include "esphome/components/time/real_time_clock.h"
#include "esphome/components/uart/uart.h"
#include "esphome/core/component.h"

#include "guard.h"
#include "opl.h"
#include "schedule.h"

namespace esphome {
namespace obc {

// The protocol and guard headers live in the top-level ::openbed namespace (no ESPHome dependency).
namespace opl = ::openbed::opl;
namespace guard = ::openbed::guard;
namespace sched = ::openbed::schedule;

static const int ZONES = 2;

class ObcClimate;
class ObcProgram;

/// Hub side of the Open Peltier Link: talks to the control MCU (Pico 2). It can only REQUEST setpoints;
/// all limits and safety logic live in the MCU firmware.
class ObcHub : public Component, public uart::UARTDevice {
 public:
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

  /// NaN = zone off. Sent immediately and re-sent every 10 s (recovers an MCU reboot).
  void set_desired(int zone, float target_c);
  void prime();
  void clear_faults(int zone);

  void register_climate(int zone, ObcClimate *c) { this->climates_[zone] = c; }
  void set_water_temperature_sensor(int zone, sensor::Sensor *s) { this->water_[zone] = s; }
  void set_hot_face_temperature_sensor(int zone, sensor::Sensor *s) { this->hot_[zone] = s; }
  void set_tec_current_sensor(int zone, sensor::Sensor *s) { this->tec_[zone] = s; }
  void set_flow_sensor(int zone, sensor::Sensor *s) { this->flow_[zone] = s; }
  void set_fault_code_sensor(int zone, sensor::Sensor *s) { this->fault_code_[zone] = s; }
  void set_fault_binary_sensor(int zone, binary_sensor::BinarySensor *s) { this->fault_[zone] = s; }
  void set_link_binary_sensor(binary_sensor::BinarySensor *s) { this->link_ = s; }
  /// Optional room sensors for the dew-point guard (cooling below 16 °C never goes under dew point + 1 K).
  void set_room_temperature_sensor(sensor::Sensor *s) { this->room_t_ = s; }
  void set_room_humidity_sensor(sensor::Sensor *s) { this->room_rh_ = s; }

 protected:
  void send_(uint8_t type, const uint8_t *payload, size_t len);
  void send_target_(int zone);
  void handle_frame_(const opl::Frame &f);
  void publish_telemetry_(const opl::Telemetry &t);
  void publish_link_lost_();

  opl::StreamDecoder decoder_;
  uint8_t seq_{0};
  float desired_[ZONES]{NAN, NAN};
  uint32_t last_heartbeat_ms_{0};
  uint32_t last_resend_ms_{0};
  uint32_t last_telemetry_ms_{0};
  bool link_ok_{false};

  ObcClimate *climates_[ZONES]{};
  sensor::Sensor *water_[ZONES]{};
  sensor::Sensor *hot_[ZONES]{};
  sensor::Sensor *tec_[ZONES]{};
  sensor::Sensor *flow_[ZONES]{};
  sensor::Sensor *fault_code_[ZONES]{};
  binary_sensor::BinarySensor *fault_[ZONES]{};
  binary_sensor::BinarySensor *link_{nullptr};
  sensor::Sensor *room_t_{nullptr};
  sensor::Sensor *room_rh_{nullptr};
};

/// One bed zone as a Home Assistant climate entity (modes: off / heat_cool).
class ObcClimate : public climate::Climate, public Component {
 public:
  void set_parent(ObcHub *hub, int zone) {
    this->hub_ = hub;
    this->zone_ = zone;
  }
  void setup() override;
  void dump_config() override;
  /// Called by the hub with fresh telemetry for this zone.
  void on_telemetry(const opl::SideTelemetry &s);
  void on_link_lost();
  /// Night program for this zone; a manual change in Home Assistant ends it.
  void set_program(ObcProgram *p) { this->program_ = p; }
  /// Target from the night program. NaN = turn the zone off (past wake time).
  void apply_program_target(float target_c);

 protected:
  climate::ClimateTraits traits() override;
  void control(const climate::ClimateCall &call) override;
  void push_desired_();

  ObcHub *hub_{nullptr};
  ObcProgram *program_{nullptr};
  int zone_{0};
};

/// Night program switch: runs the zone's schedule curve on the hub, without Home Assistant.
/// On = bedtime now. With a wake time entity the curve ends in a warm ramp and the zone turns off at
/// wake time. The start time is kept in flash, so the program survives a hub reboot.
class ObcProgram : public switch_::Switch, public Component {
 public:
  void set_climate(ObcClimate *c) { this->climate_ = c; }
  void set_time(time::RealTimeClock *t) { this->time_ = t; }
  void set_wake_time(datetime::TimeEntity *w) { this->wake_ = w; }
  void add_point(float minute, float c) { this->schedule_.add(minute, c); }
  void set_wake_ramp(float minutes, float target_c) {
    this->schedule_.wake_ramp_min = minutes;
    this->schedule_.wake_target_c = target_c;
  }
  void setup() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::LATE; }

 protected:
  struct Saved {
    uint32_t start;        // epoch seconds, 0 = not running
    int32_t wake_minute;   // minutes after start, -1 = no wake time
  };
  void write_state(bool state) override;
  void tick_();
  void stop_();

  sched::Schedule schedule_;
  ObcClimate *climate_{nullptr};
  time::RealTimeClock *time_{nullptr};
  datetime::TimeEntity *wake_{nullptr};
  ESPPreferenceObject pref_;
  Saved saved_{0, -1};
};

class ObcPrimeButton : public button::Button, public Component {
 public:
  void set_hub(ObcHub *hub) { this->hub_ = hub; }

 protected:
  void press_action() override { this->hub_->prime(); }
  ObcHub *hub_{nullptr};
};

class ObcClearFaultsButton : public button::Button, public Component {
 public:
  void set_parent(ObcHub *hub, int zone) {
    this->hub_ = hub;
    this->zone_ = zone;
  }

 protected:
  void press_action() override { this->hub_->clear_faults(this->zone_); }
  ObcHub *hub_{nullptr};
  int zone_{0};
};

}  // namespace obc
}  // namespace esphome
