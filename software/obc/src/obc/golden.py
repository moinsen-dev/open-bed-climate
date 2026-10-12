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

from . import fwupdate as F
from . import protocol as P
from .control import Inputs, SideController
from .control import Mode, Pid
from .cooling import Cooling, CoolingInputs
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


def cooling_scripted(name, pump_run_duty, script):
    """script: list of (t, CoolingInputs-kwargs); each step's inputs carry over to the next."""
    c = Cooling(pump_run_duty=pump_run_duty)
    kw = dict(mode=Mode.OFF, fan_request=0.0, pump_request=False, t_hot_face=28.3, flow_lpm=0.0, leak=False, water_ok=True)
    steps = []
    for t, change in script:
        kw.update(change)
        i = CoolingInputs(**kw)
        o = c.update(i, t)
        # Row: [t, [mode, fan_request, pump_request, t_hot_face, flow_lpm, leak, water_ok, priming, tach_rpm],
        #          [fan_duty, pump_duty, fan_stalled, tec_allowed]]
        steps.append(
            [
                t,
                [i.mode.value, i.fan_request, int(i.pump_request), i.t_hot_face, i.flow_lpm, int(i.leak), int(i.water_ok), int(i.priming), i.tach_rpm],
                [round(o.fan_duty, 5), round(o.pump_duty, 5), int(o.fan_stalled), int(o.tec_allowed)],
            ]
        )
    return {"name": name, "pump_run_duty": pump_run_duty, "steps": steps}


def cooling_scenarios():
    run = dict(mode=Mode.RUN, pump_request=True)
    # Temperatures stay clear of the curve/hysteresis thresholds so f32 (Rust) and f64 (Python) take the same branches.
    yield cooling_scripted(
        "fan_curve_and_pump_modes",
        0.8,
        [
            (0.0, {}),  # all off
            (0.5, {**run, "fan_request": 0.2, "t_hot_face": 30.1}),  # start: kick + pump start, no flow yet
            (1.0, {}),
            (2.0, {}),  # kick over: request 0.2 -> min duty
            (3.0, {"flow_lpm": 0.5}),  # flow: interlock releases, boost hold runs to 32 s
            (10.0, {"fan_request": 0.6, "t_hot_face": 41.7}),
            (20.0, {"t_hot_face": 52.3}),  # curve above request
            (25.0, {"t_hot_face": 51.1}),  # inside the hysteresis band: hold
            (31.5, {"t_hot_face": 47.6}),  # below the band: falls
            (32.5, {}),  # boost hold over: pump run duty
            (40.0, {"flow_lpm": 0.1}),  # flow lost: pump full again, held
            (41.0, {"flow_lpm": 0.5}),
            (69.5, {}),  # still held: the boost from t=40 lasts until t=70
            (70.5, {}),
            (80.0, {"mode": Mode.OFF, "fan_request": 0.0, "pump_request": False, "t_hot_face": 40.3}),  # heat soak run-on
            (90.0, {"t_hot_face": 33.4}),
            (100.0, {"t_hot_face": 31.2}),  # below FAN_T_OFF_C: off
            (110.0, {"t_hot_face": 33.9}),  # between off and on thresholds: stays off
            (120.0, {"t_hot_face": 36.2}),  # above FAN_T_ON_C: kick, then curve
            (120.5, {}),
            (121.5, {}),
            (130.0, {"mode": Mode.SAFE, "leak": True, "t_hot_face": 30.4}),  # leak: pump off whatever is requested
            (131.0, {"leak": False, "priming": True}),  # priming: full
            (132.0, {"leak": True}),  # priming but leak: off
            (133.0, {"leak": False, "water_ok": False}),  # priming but low water: off
            (134.0, {"water_ok": True, "priming": False, "pump_request": True, "fan_request": 1.0}),  # SAFE: full
            (150.0, {"t_hot_face": None, "fan_request": 0.2, "mode": Mode.RUN}),  # no hot-face reading: fan full
            (151.0, {"t_hot_face": None, "fan_request": 0.0, "mode": Mode.OFF, "pump_request": False}),
        ],
    )
    yield cooling_scripted(
        "fan_stall_with_tach",
        0.4,  # below PUMP_MIN_DUTY: clamped
        [
            (0.0, {**run, "fan_request": 0.5, "t_hot_face": 30.2, "flow_lpm": 0.5, "tach_rpm": 0.0}),
            (2.0, {}),  # spin-up grace
            (3.5, {}),  # grace over, low since 3.5
            (6.0, {}),
            (8.75, {}),  # 5 s low: stalled, TECs cut
            (9.0, {"tach_rpm": 1400.0}),  # spinning again: clears
            (12.0, {"tach_rpm": 250.0}),
            (16.5, {"tach_rpm": 900.0}),  # recovered before 5 s
            (20.0, {"tach_rpm": 100.0}),
            (26.0, {}),  # stalled
            (27.0, {"mode": Mode.OFF, "fan_request": 0.0, "pump_request": False}),  # fan off: clears
            (30.0, {**run, "fan_request": 0.3, "tach_rpm": 0.0}),  # restart: grace again
            (32.5, {}),
        ],
    )


def _image(n: int) -> bytes:
    x, out = 7, bytearray()
    for _ in range(n):
        x = (1103515245 * x + 12345) % (1 << 31)
        out.append((x >> 16) & 0xFF)
    return bytes(out)


def fw_scripted(name, slot, script):
    """script: list of events; each recorded with the session's answer (result, state, next_offset[, write plan])."""
    u = F.FwUpdate()
    steps = []
    for ev in script:
        kind = ev[0]
        if kind == "begin":
            _, size, crc, version, idle = ev
            r = u.begin(F.fw_begin(size, crc, version), slot, idle)
            row = [kind, size, crc, version, int(idle)]
        elif kind == "begin_raw":  # malformed payload
            r = u.begin(bytes.fromhex(ev[1]), slot, True)
            row = [kind, ev[1]]
        elif kind == "chunk":
            _, offset, data, flash_ok = ev
            payload = F.fw_chunk(offset, data)
            r, plan = u.chunk(payload)
            if plan is not None:
                r = u.written(payload, flash_ok)
            row = [kind, offset, data.hex(), int(flash_ok), None if plan is None else [plan.erase_from, plan.erase_to, plan.addr]]
        elif kind == "end":
            r = u.end()
            row = [kind]
        elif kind == "abort":
            u.abort()
            r = F.FwResult.OK
            row = [kind]
        else:
            raise ValueError(kind)
        steps.append([row, [int(r), int(u.state), u.next_offset]])
    return {"name": name, "slot": None if slot is None else [slot.offset, slot.size], "steps": steps}


def fw_scenarios():
    slot = F.FwSlot(0x0020_0000, 0x0010_0000)  # e.g. partition B at 2 MiB, 1 MiB
    img = _image(9000)
    crc = F.crc32(img)
    ver = F.version_word(0, 2, 0)
    chunks = [(o, img[o : o + 256]) for o in range(0, len(img), 256)]
    script = [["begin", len(img), crc, ver, False], ["begin", len(img), crc, ver, True], ["chunk", 256, chunks[1][1], True]]
    for k, (o, d) in enumerate(chunks):
        script.append(["chunk", o, d, True])
        if k == 3:
            script.append(["chunk", o, d, True])  # resend after a lost status: OK, nothing written
            script.append(["end"])  # too early
    script.append(["chunk", 1000, img[1000:1100], True])  # fully behind next_offset: treated as a resend (no-op)
    script.append(["end"])
    script.append(["end"])  # resend
    yield fw_scripted("full_transfer", slot, script)

    yield fw_scripted(
        "errors",
        slot,
        [
            ["chunk", 0, img[:16], True],  # no session
            ["end"],
            ["begin", slot.size + 1, 0, ver, True],  # too large
            ["begin_raw", "0102"],
            ["begin", 300, F.crc32(img[:300]), ver, True],
            ["chunk", 200, img[200:300], True],  # not at next_offset
            ["chunk", 0, img[:256] + b"\x00", True],  # too long
            ["chunk", 0, img[:256], True],
            ["chunk", 256, img[256:356], True],  # past the end of the image
            ["chunk", 256, img[256:300], False],  # flash error: session dropped
            ["begin", 300, F.crc32(img[:300]) ^ 1, ver, True],
            ["chunk", 0, img[:256], True],
            ["chunk", 256, img[256:300], True],
            ["end"],  # bad crc: session dropped
            ["begin", 300, 0, ver, True],
            ["abort"],
            ["chunk", 0, img[:256], True],
        ],
    )
    yield fw_scripted("no_partition_table", None, [["begin", 300, 0, ver, True]])


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
        P.Frame(11, P.MsgType.FW_BEGIN, F.fw_begin(9000, 0xCBF43926, F.version_word(0, 2, 0))),
        P.Frame(12, P.MsgType.FW_CHUNK, F.fw_chunk(0x1100, _image(256))),
        P.Frame(13, P.MsgType.FW_END),
        P.Frame(14, P.MsgType.FW_ABORT),
        P.Frame(15, P.MsgType.FW_QUERY),
        P.Frame(16, P.MsgType.FW_STATUS, F.FwStatus(12, 1, 4, 0x1100, F.version_word(0, 1, 3)).pack()),
    ]
    return [{"seq": f.seq, "type": int(f.type), "payload": f.payload.hex(), "wire": P.encode(f).hex()} for f in frames]


def build() -> str:
    data = {"generator": "python -m obc.golden", "scenarios": list(scenarios()), "cooling": list(cooling_scenarios()),
        "fwupdate": list(fw_scenarios()),
        "frames": protocol_vectors()}
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
