//! Open Bed Climate control firmware for the Raspberry Pi Pico 2 (RP2350), Tier 0 board.
//!
//! Responsibilities (and nothing else): read temperatures, flow, leak and level; run the
//! opod-core zone controller + safety supervisor; drive the TEC drivers (Modbus), relays, pumps
//! and fans; talk OPL to the hub. The hub can only request setpoints.
//!
//! Fail-safe principles:
//! - every output starts LOW (off); the zone relay (TEC power path) is only on in Mode::Run
//! - TEC driver sequencing (opod-core::driver): zone relay closes only on a confirmed driver state;
//!   3 failed transactions -> zone relay open; polarity relay only after a ~0 A read-back
//! - at most one Modbus transaction per zone per cycle: worst case ~2 x 110 ms + ~40 ms sensors,
//!   well inside the 1 s hardware watchdog
//! - inputs are fail-safe: an open wire reads as leak / low water
#![no_std]
#![no_main]

mod ads1115;
mod board;

use core::sync::atomic::{AtomicU32, Ordering};

use defmt::{info, warn};
use embassy_executor::Spawner;
use embassy_futures::select::{select3, Either3};
use embassy_rp::block::ImageDef;
use embassy_rp::gpio::{Input, Level, Output, Pull};
use embassy_rp::i2c::{self, I2c};
use embassy_rp::peripherals::{I2C0, UART0, UART1};
use embassy_rp::uart::{self, BufferedInterruptHandler, BufferedUart, BufferedUartRx, BufferedUartTx};
use embassy_rp::watchdog::Watchdog;
use embassy_rp::bind_interrupts;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
use embassy_sync::channel::Channel;
use embassy_sync::signal::Signal;
use embassy_time::{with_timeout, Duration, Instant, Ticker, Timer};
use embedded_io_async::{Read, Write};
use opod_core::control::{Inputs, Mode, Outputs, ZoneController};
use opod_core::driver::{Action, ZoneDriver};
use opod_core::modbus;
use opod_core::protocol::{self, msg, SideTelemetry, Telemetry, MAX_BODY, MAX_WIRE, TELEMETRY_LEN};
use static_cell::StaticCell;
use {defmt_rtt as _, panic_probe as _};

use crate::ads1115::Ads1115;
use crate::board::*;

#[unsafe(link_section = ".start_block")]
#[used]
pub static IMAGE_DEF: ImageDef = ImageDef::secure_exe();

bind_interrupts!(struct Irqs {
    UART0_IRQ => BufferedInterruptHandler<UART0>;
    UART1_IRQ => BufferedInterruptHandler<UART1>;
    I2C0_IRQ => i2c::InterruptHandler<I2C0>;
});

/// Firmware-only fault bit (not produced by the reference model): TEC driver not responding.
const FAULT_DRIVER_COMM: u16 = 1 << 8;

enum HostCmd {
    Heartbeat,
    SetTarget { side: u8, c: Option<f32> },
    ClearFaults { side: u8 },
    Prime,
}

static CMDS: Channel<CriticalSectionRawMutex, HostCmd, 8> = Channel::new();
static ACKS: Channel<CriticalSectionRawMutex, (u8, u8), 8> = Channel::new();
static FAULTS: Channel<CriticalSectionRawMutex, (u8, u16), 4> = Channel::new();
static TELEMETRY: Signal<CriticalSectionRawMutex, Telemetry> = Signal::new();
static FLOW_PULSES: [AtomicU32; ZONES] = [AtomicU32::new(0), AtomicU32::new(0)];

// ---- hub link (OPL over UART0) -------------------------------------------------------

#[embassy_executor::task]
async fn hub_rx(mut rx: BufferedUartRx) {
    let mut dec = protocol::StreamDecoder::default();
    let mut byte = [0u8; 1];
    let mut scratch = [0u8; MAX_BODY];
    loop {
        if rx.read_exact(&mut byte).await.is_err() {
            continue;
        }
        let Some(n) = dec.push(byte[0]) else { continue };
        let mut raw = [0u8; MAX_WIRE];
        raw[..n].copy_from_slice(&dec.raw()[..n]);
        let Ok(f) = protocol::decode(&raw[..n], &mut scratch) else {
            dec.errors += 1;
            continue;
        };
        let (cmd, ok) = match f.typ {
            msg::HEARTBEAT => (Some(HostCmd::Heartbeat), true),
            msg::SET_TARGET => match protocol::parse_set_target(f.payload) {
                Ok((side, c)) if (side as usize) < ACTIVE_ZONES => (Some(HostCmd::SetTarget { side, c }), true),
                // A zone this kit doesn't have is always off: "off" is a no-op, anything else is rejected.
                Ok((side, c)) if (side as usize) < ZONES => (None, c.is_none()),
                _ => (None, false),
            },
            msg::CLEAR_FAULTS => match f.payload.first() {
                Some(&side) if (side as usize) < ACTIVE_ZONES => (Some(HostCmd::ClearFaults { side }), true),
                Some(&side) if (side as usize) < ZONES => (None, true), // inert zone: no faults to clear
                _ => (None, false),
            },
            msg::PRIME => (Some(HostCmd::Prime), true),
            _ => (None, false),
        };
        if let Some(c) = cmd {
            CMDS.send(c).await;
        }
        if f.typ != msg::HEARTBEAT {
            let _ = ACKS.try_send((f.seq, if ok { 0 } else { 1 }));
        }
    }
}

#[embassy_executor::task]
async fn hub_tx(mut tx: BufferedUartTx) {
    let mut seq: u8 = 0;
    let mut wire = [0u8; MAX_WIRE];
    loop {
        let n = match select3(TELEMETRY.wait(), FAULTS.receive(), ACKS.receive()).await {
            Either3::First(t) => {
                let mut p = [0u8; TELEMETRY_LEN];
                t.pack(&mut p);
                protocol::encode(seq, msg::TELEMETRY, &p, &mut wire)
            }
            Either3::Second((side, f)) => protocol::encode(seq, msg::FAULT, &protocol::fault_payload(side, f), &mut wire),
            Either3::Third((acked, status)) => {
                protocol::encode(seq, msg::ACK, &protocol::ack_payload(acked, status), &mut wire)
            }
        };
        seq = seq.wrapping_add(1);
        if let Ok(n) = n {
            let _ = tx.write_all(&wire[..n]).await;
        }
    }
}

#[embassy_executor::task(pool_size = 2)]
async fn flow_counter(mut pin: Input<'static>, zone: usize) {
    loop {
        pin.wait_for_rising_edge().await;
        FLOW_PULSES[zone].fetch_add(1, Ordering::Relaxed);
    }
}

// ---- TEC driver bus (Modbus RTU over UART1 + RS-485) ----------------------------------

struct ModbusBus {
    uart: BufferedUart,
    de: Output<'static>,
}

impl ModbusBus {
    async fn transact(&mut self, req: &[u8; 8], resp: &mut [u8]) -> Result<(), ()> {
        // Drop stale bytes (e.g. a late reply to a request that already timed out), or every later
        // reply would be read one frame behind and comms would never recover.
        let mut junk = [0u8; 16];
        while let Ok(Ok(n)) = with_timeout(Duration::from_micros(200), self.uart.read(&mut junk)).await {
            if n == 0 {
                break;
            }
        }
        self.de.set_high();
        self.uart.write_all(req).await.map_err(|_| ())?;
        self.uart.flush().await.map_err(|_| ())?;
        // flush() only waits for the software buffer; wait until the last stop bit has left the
        // shift register before releasing the RS-485 driver (else the CRC byte is cut off).
        let t0 = Instant::now();
        while self.uart.busy() && t0.elapsed() < Duration::from_millis(5) {
            Timer::after_micros(50).await;
        }
        self.de.set_low();
        match with_timeout(Duration::from_millis(100), self.uart.read_exact(resp)).await {
            Ok(Ok(())) => Ok(()),
            _ => Err(()),
        }
    }

    /// Write one register; the slave echoes the request.
    async fn write(&mut self, req: &[u8; 8]) -> Result<(), ()> {
        let mut echo = [0u8; 8];
        self.transact(req, &mut echo).await?;
        if &echo == req { Ok(()) } else { Err(()) }
    }

    async fn read_output_current(&mut self, addr: u8) -> Result<f32, ()> {
        let req = modbus::read_holding(addr, DPS_MAP.i_out, 1);
        let mut resp = [0u8; 7];
        self.transact(&req, &mut resp).await?;
        let mut reg = [0u16; 1];
        modbus::parse_read_response(addr, &resp, &mut reg).map_err(|_| ())?;
        Ok(reg[0] as f32 / DPS_MAP.i_scale)
    }

    /// Execute one driver action. Worst case is a single timed-out transaction (~110 ms).
    async fn execute(&mut self, addr: u8, a: Action) -> (bool, Option<f32>) {
        let reg = |r: u16, v: u16| modbus::write_single(addr, r, v);
        match a {
            Action::None => (true, None),
            Action::SetOutput(on) => (self.write(&reg(DPS_MAP.on_off, on as u16)).await.is_ok(), None),
            Action::SetVoltageCeiling => {
                let v = (modbus::TEC_VOLTAGE_CEILING_V * DPS_MAP.u_scale) as u16;
                (self.write(&reg(DPS_MAP.u_set, v)).await.is_ok(), None)
            }
            Action::SetCurrent(amps) => {
                let v = (amps * DPS_MAP.i_scale + 0.5) as u16;
                (self.write(&reg(DPS_MAP.i_set, v)).await.is_ok(), None)
            }
            Action::ReadCurrent => match self.read_output_current(addr).await {
                Ok(i) => (true, Some(i)),
                Err(()) => (false, None),
            },
        }
    }
}

// ---- one zone's outputs ----------------------------------------------------------------

struct ZoneIo {
    zone_relay: Output<'static>,
    polarity_relay: Output<'static>,
    pump: Output<'static>,
    fan: Output<'static>,
    driver: ZoneDriver,
}

impl ZoneIo {
    /// Apply controller outputs: at most one bus transaction, then set relays. Returns driver health.
    async fn apply(&mut self, zone: usize, out: &Outputs, prime: bool, bus: &mut ModbusBus, now: f64) -> bool {
        let run = out.mode == Mode::Run;
        let zone_amps = abs(out.tec_current) * TECS_PER_ZONE;
        let action = self.driver.next(zone_amps, out.polarity, run, now);
        let (ok, read) = bus.execute(DPS_ADDR[zone], action).await;
        self.driver.done(action, ok, read, now);

        // Zone relay = hardware TEC power path. Closed only when the driver state is fully confirmed.
        let tec_path = self.driver.tec_path(zone_amps, run);
        self.zone_relay.set_level(if tec_path { Level::High } else { Level::Low });
        self.polarity_relay.set_level(if self.driver.relay_polarity() < 0 { Level::High } else { Level::Low });
        self.pump.set_level(if out.pump_on || prime { Level::High } else { Level::Low });
        self.fan.set_level(if out.fan_duty > 0.0 || prime { Level::High } else { Level::Low });
        self.driver.driver_ok()
    }
}

fn abs(x: f32) -> f32 {
    if x < 0.0 { -x } else { x }
}

fn ntc_from_volts(ntc: &opod_core::ntc::Ntc, v: f32) -> Option<f32> {
    if !(v > 0.01 && v < NTC_DIVIDER_V - 0.01) {
        return None; // short or open
    }
    ntc.celsius_from_ohm(NTC_FIXED_OHM * v / (NTC_DIVIDER_V - v))
}

// ---- main loop -------------------------------------------------------------------------

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let p = embassy_rp::init(Default::default());

    // Outputs first, all off.
    let mut zones = [
        ZoneIo {
            zone_relay: Output::new(p.PIN_10, Level::Low),
            polarity_relay: Output::new(p.PIN_11, Level::Low),
            pump: Output::new(p.PIN_12, Level::Low),
            fan: Output::new(p.PIN_13, Level::Low),
            driver: ZoneDriver::default(),
        },
        ZoneIo {
            zone_relay: Output::new(p.PIN_16, Level::Low),
            polarity_relay: Output::new(p.PIN_17, Level::Low),
            pump: Output::new(p.PIN_18, Level::Low),
            fan: Output::new(p.PIN_19, Level::Low),
            driver: ZoneDriver::default(),
        },
    ];
    // Fail-safe input polarity: an open or broken wire must read as a fault. Fit external 10 kΩ
    // pull-ups as well (do not rely on internal pulls; see RP2350 erratum E9).
    let leak_pin = Input::new(p.PIN_21, Pull::Up); // sensor holds LOW while dry; HIGH = leak or open wire
    let level_pin = Input::new(p.PIN_22, Pull::Up); // sensor holds LOW while level is OK; HIGH = low or open

    let mut watchdog = Watchdog::new(p.WATCHDOG);
    watchdog.start(Duration::from_secs(1));

    // Hub link.
    static HUB_TX_BUF: StaticCell<[u8; 256]> = StaticCell::new();
    static HUB_RX_BUF: StaticCell<[u8; 256]> = StaticCell::new();
    let mut hub_cfg = uart::Config::default();
    hub_cfg.baudrate = HUB_BAUD;
    let hub = BufferedUart::new(
        p.UART0,
        p.PIN_0,
        p.PIN_1,
        Irqs,
        HUB_TX_BUF.init([0; 256]),
        HUB_RX_BUF.init([0; 256]),
        hub_cfg,
    );
    let (hub_tx_half, hub_rx_half) = hub.split();
    spawner.spawn(hub_rx(hub_rx_half).unwrap());
    spawner.spawn(hub_tx(hub_tx_half).unwrap());

    // TEC driver bus.
    static MB_TX_BUF: StaticCell<[u8; 64]> = StaticCell::new();
    static MB_RX_BUF: StaticCell<[u8; 64]> = StaticCell::new();
    let mut mb_cfg = uart::Config::default();
    mb_cfg.baudrate = MODBUS_BAUD;
    let mut bus = ModbusBus {
        uart: BufferedUart::new(
            p.UART1,
            p.PIN_4,
            p.PIN_5,
            Irqs,
            MB_TX_BUF.init([0; 64]),
            MB_RX_BUF.init([0; 64]),
            mb_cfg,
        ),
        de: Output::new(p.PIN_6, Level::Low),
    };

    // Sensors.
    let i2c = I2c::new_async(p.I2C0, p.PIN_9, p.PIN_8, Irqs, i2c::Config::default());
    let mut adc = Ads1115::new(i2c, ADS1115_ADDR);
    spawner.spawn(flow_counter(Input::new(p.PIN_14, Pull::Up), 0).unwrap());
    if ACTIVE_ZONES > 1 {
        spawner.spawn(flow_counter(Input::new(p.PIN_20, Pull::Up), 1).unwrap());
    }

    let mut ctrl = [ZoneController::new(MAX_TEC_CURRENT_A), ZoneController::new(MAX_TEC_CURRENT_A)];
    let mut flow_lpm = [0.0f32; ZONES];
    let mut last_pulses = [0u32; ZONES];
    let mut flow_window_start = Instant::now();
    let mut last_faults = [0u16; ZONES];
    let mut prime_until = Instant::from_ticks(0);
    let mut tick: u32 = 0;
    let mut last_i = Instant::now();
    let mut ticker = Ticker::every(Duration::from_millis(100));
    info!(
        "open bed climate control up, kit {}, {} zone(s), cap {} A/TEC x {}",
        KIT, ACTIVE_ZONES, MAX_TEC_CURRENT_A, TECS_PER_ZONE
    );

    loop {
        ticker.next().await;
        let now_i = Instant::now();
        // f64 seconds: exact enough for centuries of uptime (f32 would degrade within weeks).
        let now = now_i.as_micros() as f64 / 1e6;
        tick = tick.wrapping_add(1);
        // Real elapsed time: sensor and Modbus I/O can stretch a cycle beyond 100 ms.
        let dt = ((now_i - last_i).as_micros() as f32 / 1e6).clamp(0.05, 1.0);
        last_i = now_i;

        while let Ok(cmd) = CMDS.try_receive() {
            match cmd {
                HostCmd::Heartbeat => ctrl.iter_mut().for_each(|c| c.heartbeat(now)),
                HostCmd::SetTarget { side, c } => ctrl[side as usize].set_target(c, now),
                HostCmd::ClearFaults { side } => ctrl[side as usize].clear_faults(),
                HostCmd::Prime => prime_until = now_i + Duration::from_secs(PRIME_SECONDS),
            }
        }

        // Flow over a measured window (>= 1 s). Dividing by the real elapsed time matters: a stretched
        // window would over-read flow and could hide a stalled pump from the flow interlock.
        let window = (now_i - flow_window_start).as_micros() as f32 / 1e6;
        if window >= 1.0 {
            for z in 0..ZONES {
                let p = FLOW_PULSES[z].load(Ordering::Relaxed);
                flow_lpm[z] = p.wrapping_sub(last_pulses[z]) as f32 / window / FLOW_HZ_PER_LPM;
                last_pulses[z] = p;
            }
            flow_window_start = now_i;
        }

        let leak = leak_pin.is_high();
        let water_ok = level_pin.is_low();
        let priming = now_i < prime_until && !leak && water_ok;
        let mut sides = [SideTelemetry {
            t_water: protocol::INVALID_CENTI,
            t_hot_face: protocol::INVALID_CENTI,
            target: protocol::INVALID_CENTI,
            tec_ma: 0,
            flow_mlpm: 0,
            fan_pct: 0,
            mode: 0,
            faults: 0,
        }; ZONES];

        // Only the kit's zones run. An inert zone's outputs stay LOW from init, its driver is never addressed,
        // it reports no faults, and its telemetry side keeps the default above (mode 0, invalid temperatures).
        for z in 0..ACTIVE_ZONES {
            let (ch_w, ch_h) = NTC_CHANNELS[z];
            let (cal_w, cal_h) = &NTC_CAL[z];
            let t_water = adc.read_volts(ch_w).await.ok().and_then(|v| ntc_from_volts(cal_w, v));
            let t_hot = adc.read_volts(ch_h).await.ok().and_then(|v| ntc_from_volts(cal_h, v));
            let inputs = Inputs { t_water, t_hot_face: t_hot, flow_lpm: flow_lpm[z], leak, water_ok };
            let out = ctrl[z].update(&inputs, now, dt);
            let driver_ok = zones[z].apply(z, &out, priming, &mut bus, now).await;

            let mut faults = out.faults.0;
            if !driver_ok {
                faults |= FAULT_DRIVER_COMM;
            }
            if faults != last_faults[z] {
                warn!("zone {} faults {:#06x}", z, faults);
                let _ = FAULTS.try_send((z as u8, faults));
                last_faults[z] = faults;
            }
            sides[z] = SideTelemetry {
                t_water: protocol::centi(t_water),
                t_hot_face: protocol::centi(t_hot),
                target: protocol::centi(ctrl[z].setpoint()),
                tec_ma: (out.tec_current * 1000.0) as i16,
                flow_mlpm: (flow_lpm[z] * 1000.0) as u16,
                fan_pct: (out.fan_duty * 100.0) as u8,
                mode: out.mode as u8,
                faults,
            };
        }

        if tick % 5 == 0 {
            TELEMETRY.signal(Telemetry {
                uptime_ms: now_i.as_millis() as u32,
                t_ambient: protocol::INVALID_CENTI, // room sensor lives on the hub
                water_level_pct: if water_ok { 100 } else { 0 },
                sides,
            });
        }

        watchdog.feed(Duration::from_secs(1));
    }
}
