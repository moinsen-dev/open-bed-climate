import random
from dataclasses import replace

import pytest

from opod import protocol as P
from opod.control import Fault, Inputs, Mode, SideController
from opod.schedule import DEFAULT, Schedule
from opod.thermal import SideParams, SideState, TecModule, step, steady_state, tec_operating_point

DESIGN = replace(SideParams(), n_tec=4, heatsink_r=0.07)  # Duo kits


# ---- thermal sizing ------------------------------------------------------


def test_tec_model_reproduces_datasheet_maxima():
    # TEC1-12706 datasheet (25 degC hot side): Qmax 50 W, dTmax 66 K, Vmax 14.4 V at Imax 6.4 A
    t = TecModule()
    assert t.cold_side_heat(6.4, 25.0, 25.0) == pytest.approx(50.0, rel=0.05)
    assert t.cold_side_heat(6.4, 25.0 - 66.0, 25.0) == pytest.approx(0.0, abs=50 * 0.05)
    assert t.voltage(6.4, 25.0 - 66.0, 25.0) == pytest.approx(14.4, rel=0.05)
    fitted = TecModule.from_datasheet(50, 66, 14.4, 6.4)
    assert fitted.seebeck == pytest.approx(t.seebeck, rel=1e-3)
    assert fitted.resistance == pytest.approx(t.resistance, rel=1e-3)
    assert fitted.conductance == pytest.approx(t.conductance, rel=1e-3)


def test_design_reaches_19c_with_sleeper_in_25c_room():
    s = steady_state(DESIGN, 4.5, 25.0, occupied=True, hours=4)
    assert s.t_water <= 18.8


def test_design_can_heat_to_max_setpoint():
    s = steady_state(DESIGN, -3.0, 18.0, occupied=False, hours=4)
    assert s.t_water >= 43.0


# ---- closed loop ---------------------------------------------------------


def run_loop(ctrl, setpoint, minutes, t_amb=25.0, occupied=True, flow=0.5, leak=False, t0=20.0, heartbeat=True):
    s = SideState(t_water=t0, t_hot=t_amb)
    ctrl.set_target(setpoint, 0.0)
    out = None
    dt = 1.0
    for k in range(int(minutes * 60)):
        now = k * dt
        if heartbeat and k % 5 == 0:
            ctrl.heartbeat(now)
        out = ctrl.update(Inputs(s.t_water, s.t_hot, flow, leak, True), now, dt)
        step(DESIGN, s, out.tec_current, t_amb, occupied, dt)
    return s, out


def test_tracks_cool_setpoint_without_large_overshoot():
    ctrl = SideController()
    s = SideState(t_water=28.0, t_hot=25.0)
    ctrl.set_target(21.0, 0.0)
    low = 99.0
    for k in range(90 * 60):
        if k % 5 == 0:
            ctrl.heartbeat(k)
        out = ctrl.update(Inputs(s.t_water, s.t_hot, 0.5, False, True), k, 1.0)
        step(DESIGN, s, out.tec_current, 25.0, True, 1.0)
        low = min(low, s.t_water)
    assert out.mode is Mode.RUN
    assert abs(s.t_water - 21.0) < 0.3
    assert low > 20.0, "undershoot below setpoint must stay < 1 K"


def test_heating_to_cap_keeps_tec_face_below_hardware_cutoff():
    # Cold-plate bimetal opens at 50 degC (02-electrical-safety.md); keep >= 3 K margin.
    for t_amb in (16.0, 22.0):
        ctrl = SideController(i_max=5.0)
        s = SideState(t_water=25.0, t_hot=t_amb)
        ctrl.set_target(43.0, 0.0)
        face = 0.0
        for k in range(2 * 3600):
            if k % 5 == 0:
                ctrl.heartbeat(k)
            out = ctrl.update(Inputs(s.t_water, s.t_hot, 0.5, False, True), k, 1.0)
            face = max(face, step(DESIGN, s, out.tec_current, t_amb, False, 1.0).t_cold_face)
        assert face < 47.0
        assert abs(s.t_water - 43.0) < 0.2


def test_tracks_warm_setpoint():
    ctrl = SideController()
    s, out = run_loop(ctrl, 38.0, 90, t0=25.0, t_amb=20.0, occupied=False)
    assert abs(s.t_water - 38.0) < 0.3


def test_overshoot_bounded():
    ctrl = SideController()
    s = SideState(t_water=25.0, t_hot=25.0)
    ctrl.set_target(35.0, 0.0)
    peak = 0.0
    for k in range(3600):
        if k % 5 == 0:
            ctrl.heartbeat(k)
        out = ctrl.update(Inputs(s.t_water, s.t_hot, 0.5, False, True), k, 1.0)
        step(DESIGN, s, out.tec_current, 22.0, False, 1.0)
        peak = max(peak, s.t_water)
    assert peak < 36.0


def test_setpoint_is_clamped():
    ctrl = SideController()
    ctrl.set_target(60.0, 0.0)
    assert ctrl.setpoint == 43.0
    ctrl.set_target(2.0, 0.0)
    assert ctrl.setpoint == 13.0


# ---- safety --------------------------------------------------------------


def ok_inputs(**kw):
    base = dict(t_water=30.0, t_hot_face=35.0, flow_lpm=0.5, leak=False, water_ok=True)
    base.update(kw)
    return Inputs(**base)


def test_overtemp_trips_and_latches():
    c = SideController()
    c.set_target(40.0, 0)
    out = c.update(ok_inputs(t_water=46.0), 1, 1)
    assert out.mode is Mode.SAFE and out.tec_current == 0 and Fault.WATER_OVERTEMP in out.faults
    out = c.update(ok_inputs(t_water=30.0), 2, 1)
    assert Fault.WATER_OVERTEMP in out.faults, "must latch until cleared"
    c.clear_faults()
    assert c.update(ok_inputs(), 3, 1).mode is Mode.RUN


def test_leak_stops_pump():
    c = SideController()
    c.set_target(25.0, 0)
    out = c.update(ok_inputs(leak=True), 1, 1)
    assert out.tec_current == 0 and not out.pump_on


def test_sensor_failure_is_safe():
    c = SideController()
    c.set_target(25.0, 0)
    out = c.update(ok_inputs(t_water=None), 1, 1)
    assert out.tec_current == 0 and Fault.SENSOR_INVALID in out.faults


def test_no_flow_after_grace():
    c = SideController()
    c.set_target(25.0, 0)
    out = c.update(ok_inputs(flow_lpm=0.0), 5, 1)
    assert out.mode is Mode.RUN and out.pump_on and out.tec_current == 0, "flow interlock during spin-up"
    c.heartbeat(30)
    out = c.update(ok_inputs(flow_lpm=0.0), 30, 1)
    assert Fault.NO_FLOW in out.faults and out.tec_current == 0


def test_host_timeout_goes_safe_and_recovers():
    c = SideController()
    c.set_target(25.0, 0)
    out = c.update(ok_inputs(), 11, 1)
    assert Fault.HOST_TIMEOUT in out.faults and out.tec_current == 0
    c.heartbeat(12)
    assert c.update(ok_inputs(), 12, 1).mode is Mode.RUN


def test_off_side_draws_nothing():
    out = SideController().update(ok_inputs(), 0, 1)
    assert out.mode is Mode.OFF and out.tec_current == 0 and not out.pump_on


def test_off_side_with_fault_stays_off_but_reports():
    out = SideController().update(ok_inputs(t_water=None), 0, 1)
    assert out.mode is Mode.OFF and not out.pump_on and Fault.SENSOR_INVALID in out.faults


# ---- protocol ------------------------------------------------------------


def test_cobs_roundtrip_random():
    rng = random.Random(1)
    for n in [0, 1, 253, 254, 255, 600]:
        for _ in range(20):
            data = bytes(rng.choice([0, 0, rng.randrange(256)]) for _ in range(n))
            enc = P.cobs_encode(data)
            assert 0 not in enc
            assert P.cobs_decode(enc) == data


def test_crc_reference_value():
    assert P.crc16_ccitt_false(b"123456789") == 0x29B1


def test_frame_roundtrip_and_stream():
    frames = [P.Frame(i, P.MsgType.SET_TARGET, P.set_target(i % 2, 2150)) for i in range(5)]
    wire = b"".join(P.encode(f) for f in frames)
    dec = P.StreamDecoder()
    got = []
    for i in range(0, len(wire), 3):  # arbitrary chunking
        got += dec.feed(wire[i : i + 3])
    assert got == frames
    assert P.parse_set_target(got[1].payload) == (1, 2150)


def test_corrupt_frame_dropped_stream_resyncs():
    a = bytearray(P.encode(P.Frame(1, P.MsgType.HEARTBEAT)))
    a[2] ^= 0x40
    b = P.encode(P.Frame(2, P.MsgType.HEARTBEAT))
    dec = P.StreamDecoder()
    got = dec.feed(bytes(a) + b)
    assert [f.seq for f in got] == [2] and dec.errors == 1


def test_telemetry_and_sensor_block_roundtrip():
    side = P.SideTelemetry(2150, 4010, 2100, 3200, 480, 55, 1, 0)
    t = P.Telemetry(123456, 2300, 87, (side, side))
    assert P.Telemetry.unpack(t.pack()) == t
    # Real layout: 9 piezo channels x 50 samples + 3 capacitive values per side, 10 frames/s/side.
    sb = P.SensorBlock(1, 5000, 500, tuple(tuple(i * c - 300 for c in range(9)) for i in range(50)), (100, 200, 300))
    assert P.SensorBlock.unpack(sb.pack()) == sb
    wire_len = len(P.encode(P.Frame(0, P.MsgType.SENSOR_BLOCK, sb.pack())))
    bits_per_s = wire_len * 10 * 2 * 10  # bytes * frames/s * sides * 10 bits/UART byte
    assert bits_per_s / 921600 < 0.25


# ---- schedule ------------------------------------------------------------


def test_schedule_interpolates_and_ramps():
    assert DEFAULT.setpoint(0) == 24.0
    assert DEFAULT.setpoint(15) == pytest.approx(22.5)
    assert DEFAULT.setpoint(1000) == 25.0
    wake = 450
    assert DEFAULT.setpoint(wake - 31, wake) == pytest.approx(DEFAULT.base(wake - 31))
    assert DEFAULT.setpoint(wake - 0.001, wake) == pytest.approx(32.0, abs=0.01)
    assert DEFAULT.setpoint(wake, wake) is None


def test_schedule_rejects_unsafe_points():
    with pytest.raises(ValueError):
        Schedule(points=((0, 50.0),))


def test_polarity_change_has_zero_current_dead_time():
    c = SideController()
    c.set_target(20.0, 0)  # cooling: water 30 > 20
    out = c.update(ok_inputs(t_water=30.0), 0.5, 1)
    assert out.tec_current > 0 and out.polarity == 1
    c.set_target(40.0, 1.0)  # now heating is requested
    c.heartbeat(1.0)
    out = c.update(ok_inputs(t_water=30.0), 1.0, 1)
    assert out.tec_current == 0 and out.polarity == -1, "relay switches only at zero current"
    out = c.update(ok_inputs(t_water=30.0), 2.5, 1)
    assert out.tec_current == 0, "still inside dead time"
    out = c.update(ok_inputs(t_water=30.0), 3.5, 1)
    assert out.tec_current < 0 and out.polarity == -1


def test_polarity_relay_does_not_chatter_near_passive_equilibrium():
    # Setpoint close to where the occupied bed settles on its own: the hardest case for the cool/heat relay.
    p0 = steady_state(DESIGN, 0.0, 25.0, occupied=True, hours=6).t_water
    ctrl = SideController(i_max=4.5)
    s = SideState(t_water=p0, t_hot=25.0)
    ctrl.set_target(p0, 0.0)
    flips, last = 0, ctrl.polarity
    for k in range(8 * 3600):
        if k % 5 == 0:
            ctrl.heartbeat(k)
        out = ctrl.update(Inputs(s.t_water, s.t_hot, 0.5, False, True), k, 1.0)
        step(DESIGN, s, out.tec_current, 25.0, True, 1.0)
        if ctrl.polarity != last:
            flips, last = flips + 1, ctrl.polarity
    assert flips <= 8 * 3, f"{flips} relay flips in 8 h"
