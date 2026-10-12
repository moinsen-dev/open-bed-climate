import pytest

from obc import shopping
from obc.kit import load_kit

SOLO = shopping.SHOP_DIR / "solo-starter.toml"

# Roles in parts.toml that the Solo Starter shopping list deliberately does not cover:
# - bcg_sensing: biometrics are optional for prototype 0 (the bed must first heat/cool safely).
# - vibration_motor, adjustable_base: add-ons, not part of any kit's core build.
NOT_IN_SOLO_STARTER = {"bcg_sensing", "vibration_motor", "adjustable_base"}


def test_shopping_lists_exist():
    assert SOLO in shopping.lists()


@pytest.mark.parametrize("path", shopping.lists(), ids=lambda p: p.stem)
def test_list_valid_and_rendered_doc_up_to_date(path):
    sl = shopping.load(path)
    assert sl.items and sl.checked_on and sl.currency == "EUR"
    assert path.with_suffix(".md").read_text() == shopping.render(path), "run: python -m obc.shopping"


def test_quantities_match_kit():
    sl = shopping.load(SOLO)
    kit = load_kit(shopping.KITS_DIR / f"{sl.kit}.toml")
    tecs = kit.zones * kit.tec_per_zone
    assert sl.units("tec_module") == tecs
    assert sl.units("cold_plate") == tecs
    assert sl.units("heatsink") == tecs
    assert sl.units("thermal_cutoff") >= 2 * tecs  # one 50 degC per cold plate + one 80 degC per heatsink
    assert sl.units("tec_psu") == kit.zones
    assert sl.units("tec_drive") == kit.zones
    assert sl.units("aux_psu") == 1


def test_every_needed_role_is_covered():
    sl = shopping.load(SOLO)
    needed = set(shopping.role_modules()) - NOT_IN_SOLO_STARTER
    bought = {i.role for i in sl.items if i.qty > 0 and i.stage != "tool"}
    assert needed <= bought, f"missing roles: {sorted(needed - bought)}"


def test_totals_add_up_and_exclude_tools():
    sl = shopping.load(SOLO)
    assert sl.total == pytest.approx(sl.subtotal("bench") + sl.subtotal("bed"))
    assert all(i.qty == 0 for i in sl.items if i.stage == "tool")
    assert sl.subtotal("bench") > 0 and sl.subtotal("bed") > 0


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
