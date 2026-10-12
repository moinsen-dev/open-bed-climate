"""Golden vectors: reference traces from the Python model that the Rust firmware must reproduce.

Usage: python -m obc.golden   (writes firmware/obc-core/tests/vectors/golden.json)

Each scenario drives `SideController` step by step (closed loop against the thermal plant where it
matters), records the inputs, host events and outputs, and the Rust test replays the same inputs and
events and compares the outputs. Protocol vectors pin exact wire bytes.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from . import protocol as P
from .control import Inputs, SideController
from .control import Pid
from .thermal import SideParams, SideState, step

ROOT = Path(__file__).resolve().parents[4]
DST = ROOT / "firmware" / "obc-core" / "tests" / "vectors" / "golden.json"
# Plain-text frame vectors for the C++ hub component test (no JSON parser needed there).
DST_FRAMES = ROOT / "hub" / "esphome" / "components" / "obc" / "test" / "frames.txt"
# Night-schedule vectors for the hub's C++ port (schedule.h).
DST_SCHEDULE = ROOT / "hub" / "esphome" / "components" / "obc" / "test" / "schedule.txt"
PLANT = replace(SideParams(), n_tec=4, heatsink_r=0.07)


def _ctrl(i_max: float) -> SideController:
    return SideController(i_max=i_max, pid=Pid(kp=1.2, ki=0.004, kd=0.0, out_min=-i_max, out_max=i_max))


def _rec(steps, t, dt, inp: Inputs, events, out):
    # Compact row: [t, dt, events, [t_water, t_hot_face, flow_lpm, leak, water_ok],
    #               [tec_current, pump_on, fan_duty, mode, faults, polarity]]
    steps.append(
        [
            t,
            dt,
            events,
            [inp.t_water, inp.t_hot_face, inp.flow_lpm, int(inp.leak), int(inp.water_ok)],
            [round(out.tec_current, 5), int(out.pump_on), round(out.fan_duty, 4), out.mode.value, int(out.faults), out.polarity],
        ]
    )


def _dts(mode: str, n: int):
    if mode == "1s":
        return [1.0] * n
    if mode == "100ms":
        return [0.1] * n
    # "jitter": 0.1..0.4 s, deterministic (LCG), rounded to whole ms like the firmware's clock
    x, out = 12345, []
    for _ in range(n):
        x = (1103515245 * x + 12345) % (1 << 31)
        out.append(round(0.1 + 0.3 * x / (1 << 31), 3))
    return out


def closed_loop(name, i_max, setpoint, t0, t_amb, occupied, minutes, setpoint_change=None, timing="1s", t_offset=0.0):
    c = _ctrl(i_max)
    s = SideState(t_water=t0, t_hot=t_amb)
    steps = []
    t = t_offset
    last_hb = -1e9
    changed = False
    n_steps = int(minutes * 60 / {"1s": 1.0, "100ms": 0.1, "jitter": 0.25}[timing])
    for k, dt in enumerate(_dts(timing, n_steps)):
        ev = []
        if k == 0:
            c.set_target(setpoint, t)
            ev.append(["set_target", setpoint])
        if setpoint_change and not changed and t - t_offset >= setpoint_change[0]:
            c.set_target(setpoint_change[1], t)
            ev.append(["set_target", setpoint_change[1]])
            changed = True
        if t - last_hb >= 5.0:
            c.heartbeat(t)
            ev.append(["heartbeat"])
            last_hb = t
        inp = Inputs(round(s.t_water, 4), round(s.t_hot, 4), 0.5, False, True)  # sensor resolution
        out = c.update(inp, t, dt)
        _rec(steps, round(t, 3), dt, inp, ev, out)
        step(PLANT, s, out.tec_current, t_amb, occupied, dt)
        t = round(t + dt, 3)
    return {"name": name, "i_max": i_max, "steps": steps}


def scripted(name, i_max, script):
    """script: list of (t, events, Inputs-kwargs)."""
    c = _ctrl(i_max)
    steps = []
    base = dict(t_water=30.0, t_hot_face=35.0, flow_lpm=0.5, leak=False, water_ok=True)
    for t, events, kw in script:
        for ev in events:
            if ev[0] == "set_target":
                c.set_target(ev[1], t)
            elif ev[0] == "heartbeat":
                c.heartbeat(t)
            elif ev[0] == "clear_faults":
                c.clear_faults()
        inp = Inputs(**{**base, **kw})
        out = c.update(inp, t, 1.0)
        _rec(steps, t, 1.0, inp, [list(e) for e in events], out)
    return {"name": name, "i_max": i_max, "steps": steps}


def scenarios():
    yield closed_loop("cool_pulldown_occupied", 4.5, 21.0, 28.0, 25.0, True, 20)
    yield closed_loop("heat_to_cap_tapered", 5.0, 43.0, 25.0, 16.0, False, 12)
    yield closed_loop("cool_then_heat_polarity", 4.5, 22.0, 26.0, 25.0, True, 10, setpoint_change=(300, 38.0))
    # The firmware's real cadence: 10 Hz, and jittered 0.1-0.4 s cycles (slow sensor/Modbus I/O).
    yield closed_loop("cool_10hz", 4.5, 21.0, 27.0, 25.0, True, 3, timing="100ms")
    yield closed_loop("polarity_jittered_dt", 4.5, 22.0, 24.0, 25.0, True, 4, setpoint_change=(120, 36.0), timing="jitter")
    # One year of uptime: absolute timestamps must not degrade timing (time is f64 seconds).
    yield closed_loop("one_year_uptime", 4.5, 22.0, 26.0, 25.0, True, 4, setpoint_change=(120, 38.0), t_offset=31_536_000.0)
    hb = ["heartbeat"]
    yield scripted(
        "faults_and_recovery",
        4.5,
        [
            (0.0, [["set_target", 40.0]], {}),
            (1.0, [hb], {"t_water": 46.0}),  # overtemp, latches
            (2.0, [hb], {}),
            (3.0, [hb, ["clear_faults"]], {}),
            (4.0, [hb], {"leak": True}),  # pump off
            (5.0, [hb, ["clear_faults"]], {}),
            (6.0, [hb], {"t_water": None}),  # sensor invalid
            (7.0, [hb, ["clear_faults"]], {"flow_lpm": 0.0}),  # interlock, no fault yet
            (20.0, [hb], {"flow_lpm": 0.0}),
            (28.0, [hb], {"flow_lpm": 0.0}),  # > 20 s without flow -> NO_FLOW
            (29.0, [hb], {}),  # flow back: NO_FLOW self-heals
            (45.0, [], {}),  # no heartbeat for 16 s -> HOST_TIMEOUT
            (46.0, [hb], {"water_ok": False}),  # low water: pump off
            (47.0, [hb, ["set_target", None]], {"t_water": None}),  # off side stays off, still reports
        ],
    )
    yield scripted(
        "setpoint_clamping",
        6.0,
        [(0.0, [["set_target", 60.0]], {"t_water": 40.0}), (1.0, [["set_target", 2.0]], {"t_water": 40.0})],
    )


def protocol_vectors():
    sb = P.SensorBlock(1, 5000, 500, tuple(tuple(i * c - 300 for c in range(9)) for i in range(3)), (100, 200, 300))
    side = P.SideTelemetry(2150, 4010, 2100, 3200, 480, 55, 1, 0)
    tel = P.Telemetry(123456, 2300, 87, (side, replace(side, faults=0x0011, mode=2)))
    frames = [
        P.Frame(0, P.MsgType.HEARTBEAT),
        P.Frame(7, P.MsgType.SET_TARGET, P.set_target(1, 2150)),
        P.Frame(8, P.MsgType.SET_TARGET, P.set_target(0, None)),
        P.Frame(9, P.MsgType.TELEMETRY, tel.pack()),
        P.Frame(10, P.MsgType.FAULT, bytes([1, 0x11, 0x00])),
        P.Frame(255, P.MsgType.SENSOR_BLOCK, sb.pack()),
    ]
    return [{"seq": f.seq, "type": int(f.type), "payload": f.payload.hex(), "wire": P.encode(f).hex()} for f in frames]


def build() -> str:
    data = {"generator": "python -m obc.golden", "scenarios": list(scenarios()), "frames": protocol_vectors()}
    return json.dumps(data, separators=(",", ":")) + "\n"


def build_frames_txt() -> str:
    lines = ["# seq type payload_hex wire_hex   (generated by python -m obc.golden)"]
    for f in protocol_vectors():
        lines.append(f"{f['seq']} {f['type']} {f['payload'] or '-'} {f['wire']}")
    return "\n".join(lines) + "\n"


def build_schedule_txt() -> str:
    from .schedule import DEFAULT, Schedule, wake_offset

    custom = Schedule(points=((0, 22.0), (60, 16.0), (240, 18.5)), wake_ramp_min=20.0, wake_target_c=35.0)
    lines = [
        "# Generated by: python -m obc.golden  (do not edit)",
        "# P <minute> <degC>... = schedule points; R <ramp_min> <wake_c>; S <minute> <wake|-> <expected|off>",
        "# W <start_min_of_day> <wake_min_of_day> <offset>",
    ]
    for sch in (DEFAULT, custom):
        lines.append("P " + " ".join(f"{m:g} {c:g}" for m, c in sch.points))
        lines.append(f"R {sch.wake_ramp_min:g} {sch.wake_target_c:g}")
        for wake in (None, 450.0, 200.0):
            for k in range(0, 121):
                minute = k * 4.25
                sp = sch.setpoint(minute, wake)
                w = "-" if wake is None else f"{wake:g}"
                lines.append(f"S {minute:g} {w} " + ("off" if sp is None else f"{sp:.4f}"))
    for start, wake in ((1380, 420), (420, 1380), (0, 0), (1439, 0), (600, 601)):
        lines.append(f"W {start} {wake} {wake_offset(start, wake)}")
    return "\n".join(lines) + "\n"


def main() -> None:
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(build())
    DST_FRAMES.parent.mkdir(parents=True, exist_ok=True)
    DST_FRAMES.write_text(build_frames_txt())
    DST_SCHEDULE.write_text(build_schedule_txt())
    print(f"wrote {DST.relative_to(ROOT)} ({DST.stat().st_size // 1024} KiB) and {DST_FRAMES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
