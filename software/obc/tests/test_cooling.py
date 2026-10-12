from obc.control import MIN_FLOW_LPM, Inputs, Mode, SideController
from obc.cooling import (
    FAN_KICK_S,
    FAN_MIN_DUTY,
    FAN_STALL_GRACE_S,
    FAN_STALL_S,
    PUMP_BOOST_HOLD_S,
    PUMP_START_S,
    Cooling,
    CoolingInputs,
)


def ci(**kw):
    base = dict(mode=Mode.RUN, fan_request=0.2, pump_request=True, t_hot_face=30.0, flow_lpm=0.5, leak=False, water_ok=True)
    return CoolingInputs(**{**base, **kw})


def test_fan_kicks_then_holds_min_duty():
    c = Cooling()
    assert c.update(ci(), 0.0).fan_duty == 1.0
    assert c.update(ci(), FAN_KICK_S + 0.1).fan_duty == FAN_MIN_DUTY  # request 0.2 is below the fan's minimum


def test_fan_runs_on_after_tec_stop_until_hot_face_cools():
    c = Cooling()
    c.update(ci(fan_request=0.8, t_hot_face=45.0), 0.0)
    off = dict(mode=Mode.OFF, fan_request=0.0, pump_request=False)
    assert c.update(ci(**off, t_hot_face=45.0), 10.0).fan_duty > 0.5
    assert c.update(ci(**off, t_hot_face=33.0), 20.0).fan_duty >= FAN_MIN_DUTY
    assert c.update(ci(**off, t_hot_face=31.0), 30.0).fan_duty == 0.0


def test_fan_hysteresis_holds_inside_band():
    c = Cooling()
    c.update(ci(fan_request=0.0, t_hot_face=50.0), 0.0)
    d = c.update(ci(fan_request=0.0, t_hot_face=50.0), 5.0).fan_duty
    assert c.update(ci(fan_request=0.0, t_hot_face=49.0), 6.0).fan_duty == d  # 1 K down: inside the 2 K band
    assert c.update(ci(fan_request=0.0, t_hot_face=46.0), 7.0).fan_duty < d


def test_fan_stall_cuts_tecs_only_with_tach():
    c = Cooling()
    t = 0.0
    while t < FAN_STALL_GRACE_S + FAN_STALL_S + 1:
        o = c.update(ci(tach_rpm=0.0), t)
        t += 0.5
    assert o.fan_stalled and not o.tec_allowed
    assert c.update(ci(tach_rpm=1500.0), t).tec_allowed
    # no tach signal: never stalled
    c = Cooling()
    assert all(c.update(ci(), k * 0.5).tec_allowed for k in range(100))


def test_pump_full_while_priming_starting_waiting_for_flow_and_safe():
    c = Cooling(pump_run_duty=0.6)
    assert c.update(ci(flow_lpm=0.0), 0.0).pump_duty == 1.0  # start + no flow
    assert c.update(ci(), 1.0).pump_duty == 1.0  # boost hold after waiting for flow
    assert c.update(ci(), PUMP_BOOST_HOLD_S + 0.5).pump_duty == 0.6
    assert c.update(ci(flow_lpm=MIN_FLOW_LPM / 2), 40.0).pump_duty == 1.0  # flow lost
    assert c.update(ci(mode=Mode.SAFE), 40.0 + PUMP_BOOST_HOLD_S + 1).pump_duty == 1.0
    c = Cooling(pump_run_duty=0.6)
    assert c.update(ci(mode=Mode.OFF, pump_request=False, priming=True), 0.0).pump_duty == 1.0
    assert c.update(ci(), PUMP_START_S - 0.1).pump_duty == 1.0


def test_pump_off_on_leak_or_low_water_whatever_is_requested():
    c = Cooling()
    for kw in (dict(leak=True), dict(water_ok=False), dict(leak=True, priming=True), dict(water_ok=False, priming=True)):
        assert c.update(ci(mode=Mode.SAFE, **kw), 0.0).pump_duty == 0.0


def test_flow_fault_still_cuts_tecs_with_pump_pwm():
    # Reduced pump duty must not weaken the interlock: the supervisor still trips NO_FLOW and cuts TEC current.
    ctrl, cool = SideController(i_max=4.5), Cooling(pump_run_duty=0.5)
    ctrl.set_target(20.0, 0.0)
    for k in range(40):
        ctrl.heartbeat(k)
        out = ctrl.update(Inputs(30.0, 35.0, 0.0, False, True), k, 1.0)
        co = cool.update(CoolingInputs(out.mode, out.fan_duty, out.pump_on, 35.0, 0.0, False, True), k)
    assert out.mode == Mode.SAFE and out.tec_current == 0.0
    assert co.pump_duty == 1.0
