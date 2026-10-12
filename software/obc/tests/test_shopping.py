import re

import pytest
from test_kits import FIRMWARE, _board_kit_blocks

from obc import shopping
from obc.kit import load_kit

SOLO = shopping.SHOP_DIR / "solo-starter.toml"
LISTS = shopping.lists()

# Roles in parts.toml that no shopping list covers yet:
# - bcg_sensing: biometrics are optional for prototype 0 (the bed must first heat/cool safely), and the firmware reads
#   none of the three options yet. The Duo Reference piezo grid also needs the cover sensor board, which doesn't exist.
# - vibration_motor, adjustable_base: add-ons, not part of any kit's core build.
NOT_BOUGHT = {"bcg_sensing", "vibration_motor", "adjustable_base"}

# What board.rs drives per active zone: zone relay, polarity, pump, fan (GP10-13 / GP16-19), each on a low-side driver.
DRIVERS_PER_ZONE = 4


def _kit(sl):
    return load_kit(shopping.KITS_DIR / f"{sl.kit}.toml")


def _units(sl, role, pattern):
    """Units on the lines of `role` whose name matches `pattern` (a role mixes item types, e.g. temp_sensors)."""
    return sum(i.units for i in sl.items if i.role == role and re.search(pattern, i.name))


def _carrier(sl):
    return _units(sl, "pcb", r"carrier PCB")


def test_shopping_lists_exist():
    assert SOLO in shopping.lists()


@pytest.mark.parametrize("path", shopping.lists(), ids=lambda p: p.stem)
def test_list_valid_and_rendered_doc_up_to_date(path):
    sl = shopping.load(path)
    assert sl.items and sl.checked_on and sl.currency == "EUR"
    assert path.with_suffix(".md").read_text() == shopping.render(path), "run: python -m obc.shopping"


def test_every_kit_has_a_list():
    assert {p.stem for p in LISTS} == {p.stem for p in shopping.KITS_DIR.glob("*.toml")}


@pytest.mark.parametrize("path", LISTS, ids=lambda p: p.stem)
def test_quantities_match_kit(path):
    sl = shopping.load(path)
    kit = _kit(sl)
    tecs = kit.zones * kit.tec_per_zone
    assert sl.units("tec_module") == tecs
    assert sl.units("cold_plate") == tecs
    assert sl.units("heatsink") == tecs
    assert sl.units("thermal_cutoff") >= 2 * tecs  # one 50 degC per cold plate + one 80 degC per heatsink
    assert _units(sl, "thermal_cutoff", r"50 C") == tecs and _units(sl, "thermal_cutoff", r"80 C") == tecs
    assert sl.units("tec_drive") == kit.zones
    assert sl.units("pump") == kit.zones
    assert sl.units("flow_sensor") == kit.zones
    assert _units(sl, "reservoir", r" reservoir \(") == _units(sl, "reservoir", r"capacitive level sensor") == kit.zones
    assert sl.units("aux_psu") == 1
    assert _units(sl, "polarity_relay", r"^Automotive relay") == 3 * kit.zones  # zone relay + 2 SPDT polarity
    assert _units(sl, "polarity_relay", r"fuse holder") == kit.zones
    assert _units(sl, "quick_disconnect", r"female") == _units(sl, "quick_disconnect", r"\bmale,") == 2 * kit.zones


@pytest.mark.parametrize("path", LISTS, ids=lambda p: p.stem)
def test_tec_supply_matches_kit(path):
    sl = shopping.load(path)
    kit = _kit(sl)
    supplies = [i for i in sl.items if i.role == "tec_psu" and i.name.startswith("Mean Well")]
    volts_amps = [re.search(r"(\d+) V / ([\d.]+) A", i.name).groups() for i in supplies]
    watts = sum(i.units * float(v) * float(a) for i, (v, a) in zip(supplies, volts_amps))
    if kit.tier == 0:
        assert sum(i.units for i in supplies) == kit.zones, "Tier 0: one certified desktop supply per zone"
        assert all(re.search(r"IEC C14, desktop", i.name) for i in supplies)
    else:
        assert sum(i.units for i in supplies) == 1, "Tier 1: one supply inside the closed power module"
        assert any(re.search(r"qualified electrician", i.name) for i in sl.items if i.role == "tec_psu")
    assert watts >= kit.zones * kit.tec_psu_w_per_zone


@pytest.mark.parametrize("path", LISTS, ids=lambda p: p.stem)
def test_sensors_and_drivers_match_firmware(path):
    """Counts follow what board.rs reads for this kit's feature, not what parts.toml would like one day."""
    sl = shopping.load(path)
    zones, _, _ = _board_kit_blocks()[sl.kit]
    board = (FIRMWARE / "src" / "board.rs").read_text()
    channels = re.search(r"NTC_CHANNELS: \[\(u8, u8\); ZONES\] = \[(.*?)\];", board).group(1)
    used = [int(c) for pair in re.findall(r"\((\d+), (\d+)\)", channels)[:zones] for c in pair]
    carrier = _carrier(sl)
    assert carrier in (0, 1)
    ads = _units(sl, "temp_sensors", r"ADS1115") + carrier  # the carrier has one ADS1115 @ 0x48
    assert ads == 1, "board.rs reads one ADS1115 (ADS1115_ADDR)"
    assert max(used) < 4 * ads
    assert _units(sl, "temp_sensors", r"G1/4, 10k NTC") == zones  # water NTC per zone (ch0 / ch2)
    assert _units(sl, "temp_sensors", r"NTC epoxy bead") >= zones  # hot-face NTC per zone (ch1 / ch3)
    if not carrier:
        assert _units(sl, "temp_sensors", r"0\.1 %") >= len(used)  # one divider reference per NTC
        assert 4 * _units(sl, "consumable", r"4-channel .*MOSFET") >= DRIVERS_PER_ZONE * zones
    rs485 = _units(sl, "consumable", r"RS485")
    assert rs485 == zones + (0 if carrier else 1), "one adapter per DPS, plus the Pico end unless the carrier's SP3485 does it"
    assert _units(sl, "leak_sensor", r"Sensor WLD Relay") == 1  # GP21
    level_inputs = 1  # GP22
    assert _units(sl, "reservoir", r"capacitive level sensor") <= level_inputs or _units(sl, "reservoir", r"OR gate") >= 1, (
        "more level sensors than board.rs inputs: combine them (OR gate) into GP22"
    )


@pytest.mark.parametrize("path", LISTS, ids=lambda p: p.stem)
def test_every_needed_role_is_covered(path):
    sl = shopping.load(path)
    needed = set(shopping.role_modules()) - NOT_BOUGHT
    bought = {i.role for i in sl.items if i.qty > 0 and i.stage != "tool"}
    assert needed <= bought, f"missing roles: {sorted(needed - bought)}"


@pytest.mark.parametrize("path", LISTS, ids=lambda p: p.stem)
def test_totals_add_up_and_exclude_tools(path):
    sl = shopping.load(path)
    assert sl.total == pytest.approx(sl.subtotal("bench") + sl.subtotal("bed"))
    assert all(i.qty == 0 for i in sl.items if i.stage == "tool")
    assert sl.subtotal("bench") > 0 and sl.subtotal("bed") > 0


def test_duo_lists_cost_more_than_solo():
    totals = {p.stem: shopping.load(p).total for p in LISTS}
    assert totals["solo-starter"] < totals["duo-standard"]
    assert totals["solo-starter"] < totals["duo-reference"]


@pytest.mark.parametrize(
    "old,new,match",
    [
        ('role = "tec_psu"', 'role = "flux_capacitor"', "unknown role"),
        ("qty = 1\n", "qty = -1\n", "qty"),
        ('url = "https://www.reichelt.de/de/de/shop/produkt/tischnetzteil', 'url = "http://www.reichelt.de/de/de/shop/produkt/tischnetzteil', "https"),
        ('stage = "bench"', 'stage = "garage"', "stage"),
        ('status = "listing"', 'status = "rumour"', "status"),
    ],
)
def test_invalid_lists_are_rejected(tmp_path, old, new, match):
    src = SOLO.read_text()
    assert old in src
    bad = tmp_path / "solo-starter.toml"
    bad.write_text(src.replace(old, new, 1))
    with pytest.raises(ValueError, match=match):
        shopping.load(bad)
