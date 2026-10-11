from pathlib import Path

import pytest

from opod.kit import check_kit, load_kit

KITS = sorted((Path(__file__).resolve().parents[3] / "hardware" / "kits").glob("*.toml"))


def test_kits_exist():
    assert len(KITS) >= 3


@pytest.mark.parametrize("path", KITS, ids=lambda p: p.stem)
def test_kit_claims_hold(path):
    report = check_kit(load_kit(path))
    assert not report.problems, report.problems


def test_kit_cannot_override_safety_limits(tmp_path):
    src = KITS[0].read_text().replace("[power]", "[power]\nsetpoint_max = 50")
    bad = tmp_path / "bad.toml"
    bad.write_text(src)
    with pytest.raises(ValueError, match="safety limits"):
        load_kit(bad)


def test_overclaiming_kit_is_caught(tmp_path):
    src = KITS[0].read_text()
    import re

    src = re.sub(r"min_water_c = [\d.]+", "min_water_c = 14.0", src)
    bad = tmp_path / "overclaim.toml"
    bad.write_text(src)
    assert check_kit(load_kit(bad)).problems


def test_undersized_psu_is_caught(tmp_path):
    src = (Path(KITS[0]).parent / "duo-standard.toml").read_text().replace("tec_psu_w_per_zone = 280", "tec_psu_w_per_zone = 150")
    bad = tmp_path / "small_psu.toml"
    bad.write_text(src)
    assert any("PSU" in p for p in check_kit(load_kit(bad)).problems)


def test_parts_catalog_valid_and_rendered_doc_up_to_date():
    import tomllib

    from opod import render_parts

    data = tomllib.loads(render_parts.SRC.read_text())
    ids = [r["id"] for r in data["role"]]
    assert len(ids) == len(set(ids))
    for r in data["role"]:
        assert r["requirement"] and r["module"]
        for ex in r.get("example", []):
            assert ex["status"] in render_parts.BADGE
            if ex["status"] in ("datasheet", "listing"):
                assert ex["source"].startswith("https://") and ex["verified_on"], ex["name"]
    assert render_parts.DST.read_text() == render_parts.render(), "run: python -m opod.render_parts"


def _closed_loop(kit, setpoint, t_amb, occupied, t0, minutes):
    from opod.control import Inputs
    from opod.thermal import SideState, step

    p = kit.side_params()
    ctrl = kit.controller()
    s = SideState(t_water=t0, t_hot=t_amb)
    ctrl.set_target(setpoint, 0.0)
    peak_w, peak_face, peak_i = 0.0, 0.0, 0.0
    for k in range(minutes * 60):
        if k % 5 == 0:
            ctrl.heartbeat(k)
        out = ctrl.update(Inputs(s.t_water, s.t_hot, 0.5, False, True), k, 1.0)
        r = step(p, s, out.tec_current, t_amb, occupied, 1.0)
        peak_w, peak_face = max(peak_w, r.electrical_w), max(peak_face, r.t_cold_face)
        peak_i = max(peak_i, abs(out.tec_current))
    return s, peak_w, peak_face, peak_i


@pytest.mark.parametrize("path", KITS, ids=lambda p: p.stem)
def test_kit_power_stays_within_psu_on_hot_night(path):
    from opod.kit import PSU_MARGIN, TEC_DRIVER_EFFICIENCY

    kit = load_kit(path)
    for t_amb in (25.0, 30.0):
        _, peak_w, _, peak_i = _closed_loop(kit, 13.0, t_amb, True, t_amb, 60)  # full pull-down
        assert peak_i <= kit.max_tec_current_a + 1e-9
        assert peak_w / TEC_DRIVER_EFFICIENCY <= kit.tec_psu_w_per_zone * PSU_MARGIN, (t_amb, peak_w)


@pytest.mark.parametrize("path", KITS, ids=lambda p: p.stem)
def test_kit_heats_to_cap_without_tripping_cutoff(path):
    kit = load_kit(path)
    for t_amb in (16.0, 22.0):
        s, _, face, _ = _closed_loop(kit, 43.0, t_amb, False, 25.0, 120)
        assert face < 47.0  # cold-plate cutoff opens at 50 degC; keep >= 3 K margin
        assert abs(s.t_water - 43.0) < 0.2


def test_golden_vectors_up_to_date():
    from opod import golden

    assert golden.DST.read_text() == golden.build(), "run: python -m opod.golden"
    assert golden.DST_FRAMES.read_text() == golden.build_frames_txt(), "run: python -m opod.golden"
    assert golden.DST_SCHEDULE.read_text() == golden.build_schedule_txt(), "run: python -m opod.golden"


def test_firmware_board_config_matches_duo_standard_kit():
    import re

    board = (Path(__file__).resolve().parents[3] / "firmware" / "opod-pico2" / "src" / "board.rs").read_text()
    cap = float(re.search(r"MAX_TEC_CURRENT_A: f32 = ([\d.]+);", board).group(1))
    n = float(re.search(r"TECS_PER_ZONE: f32 = ([\d.]+);", board).group(1))
    kit = load_kit(Path(__file__).resolve().parents[3] / "hardware" / "kits" / "duo-standard.toml")
    assert (cap, n) == (kit.max_tec_current_a, kit.tec_per_zone), "board.rs must match the kit it is built for"


def test_dew_point_guard():
    from opod.comfort import dew_point_c, guarded_target

    assert dew_point_c(25.0, 50.0) == pytest.approx(13.86, abs=0.05)  # standard table value
    assert guarded_target(14.0, 25.0, 50.0) == pytest.approx(14.86, abs=0.05)  # raised to dew point + 1 K
    assert guarded_target(13.0, 20.0, 30.0) == 13.0  # dry room: no change
    assert guarded_target(14.0, 28.0, 90.0) == 16.0  # never raised above the guard threshold
    assert guarded_target(20.0, 25.0, 90.0) == 20.0  # warm enough: untouched
    assert guarded_target(14.0, None, 50.0) == 14.0  # no sensor: unchanged
    assert guarded_target(None, 25.0, 50.0) is None


def test_site_data_up_to_date():
    from opod import site_data

    assert site_data.DST.read_text() == site_data.build(), "run: python -m opod.site_data"
