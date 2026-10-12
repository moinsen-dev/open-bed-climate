"""The carrier PCB (hardware/pcb/carrier) must wire the MCUs exactly as the firmware and the hub expect.

Parses the committed carrier.kicad_pcb as plain text (no KiCad needed) and checks it against
firmware/obc-pico2/src/board.rs (pin map, ADS1115 address, NTC channels) and hub/esphome/obc-hub-common.yaml
(OPL UART pins), plus the two hardware safety properties: every driver gate has a pull-down of 8.2 kOhm or less
(RP2350-E9), and each zone relay coil is fed only through its CUTOFF LOOP.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PCB = ROOT / "hardware" / "pcb" / "carrier" / "carrier.kicad_pcb"
BOARD_RS = ROOT / "firmware" / "obc-pico2" / "src" / "board.rs"
HUB_YAML = ROOT / "hub" / "esphome" / "obc-hub-common.yaml"

# Raspberry Pi Pico / Pico 2 pinout (datasheet): GPn -> header pin
PICO_PIN = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 11: 15, 12: 16, 13: 17, 14: 19,
            15: 20, 16: 21, 17: 22, 18: 24, 19: 25, 20: 26, 21: 27, 22: 29, 26: 31, 27: 32, 28: 34}
# ESP32-S3-DevKitC-1 (Espressif user guide): J1 = pads 1-22, J3 = pads 23-44 on the carrier footprint
ESP_J1 = [None, None, None, 4, 5, 6, 7, 15, 16, 17, 18, 8, 3, 46, 9, 10, 11, 12, 13, 14, None, None]
ESP_J3 = [None, 43, 44, 1, 2, 42, 41, 40, 39, 38, 37, 36, 35, 0, 45, 48, 47, 21, 20, 19, None, None]
ESP_PAD = {gpio: i + 1 for i, gpio in enumerate(ESP_J1 + ESP_J3) if gpio is not None}


# ------------------------------------------------------------------------------------------------ PCB parsing
def _sexpr(text):
    stack = [[]]
    for m in re.finditer(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text):
        tok = m.group(0)
        if tok == "(":
            stack.append([])
        elif tok == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(tok[1:-1] if tok.startswith('"') else tok)
    return stack[0][0]


class Board:
    def __init__(self, path):
        tree = _sexpr(path.read_text())
        self.fps = {}  # ref -> {"lib", "value", "pads": {num: net}}
        for fp in (c for c in tree if isinstance(c, list) and c and c[0] == "footprint"):
            props = {c[1]: c[2] for c in fp if isinstance(c, list) and c and c[0] == "property"}
            pads = {}
            for pad in (c for c in fp if isinstance(c, list) and c and c[0] == "pad"):
                net = next((c for c in pad if isinstance(c, list) and c and c[0] == "net"), None)
                pads.setdefault(pad[1], net[-1] if net else None)
            self.fps[props["Reference"]] = {"lib": fp[1], "value": props.get("Value", ""), "pads": pads}
        self.nets = {}
        for ref, fp in self.fps.items():
            for num, net in fp["pads"].items():
                if net:
                    self.nets.setdefault(net, set()).add((ref, num))

    def one(self, lib):
        refs = [r for r, f in self.fps.items() if f["lib"] == lib]
        assert len(refs) == 1, (lib, refs)
        return refs[0]

    def by_value(self, value):
        refs = [r for r, f in self.fps.items() if f["value"] == value]
        assert len(refs) == 1, (value, refs)
        return refs[0]

    def net(self, ref, pad):
        return self.fps[ref]["pads"][str(pad)]

    def members(self, net):
        return self.nets.get(net, set())

    def through_resistor(self, net):
        """Nets reached from `net` through one 2-pad resistor."""
        out = set()
        for ref, pad in self.members(net):
            if ref.startswith("R") and len(self.fps[ref]["pads"]) == 2:
                out.add(self.net(ref, "2" if pad == "1" else "1"))
        return out

    def resistors_to(self, net, other):
        """Values (ohms) of resistors between `net` and `other`."""
        vals = []
        for ref, pad in self.members(net):
            if ref.startswith("R") and self.net(ref, "2" if pad == "1" else "1") == other:
                vals.append(ohms(self.fps[ref]["value"]))
        return vals


def ohms(value):
    m = re.match(r"([\d.]+)\s*([kKmM]?)", value)
    mult = {"": 1, "k": 1e3, "K": 1e3, "m": 1e6, "M": 1e6}[m.group(2)]
    return float(m.group(1)) * mult


@pytest.fixture(scope="module")
def board():
    return Board(PCB)


@pytest.fixture(scope="module")
def pico(board):
    return board.one("carrier:RaspberryPi_Pico2_Socket")


@pytest.fixture(scope="module")
def esp(board):
    return board.one("carrier:ESP32-S3-DevKitC-1_Socket")


def gp_net(board, pico, gp):
    return board.net(pico, PICO_PIN[gp])


# ------------------------------------------------------------------------------------------------ board.rs parsing
def board_rs_table():
    """Function -> list of GPn from the pin-map table in board.rs (including 'DE/RE on GPn' in the notes)."""
    rows = {}
    for line in BOARD_RS.read_text().splitlines():
        if not line.startswith("//! |") or "Pico 2 pin" in line or "---" in line:
            continue
        cells = [c.strip() for c in line[4:].strip().strip("|").split("|")]
        rows[cells[0]] = [int(g) for g in re.findall(r"GP(\d+)", " ".join(cells[1:]))]
    return rows


def row(prefix):
    rows = [v for k, v in board_rs_table().items() if k.startswith(prefix)]
    assert len(rows) == 1, prefix
    return rows[0]


def test_board_rs_table_parses():
    t = board_rs_table()
    assert len(t) >= 7, t


def test_opl_uart_matches_hub_yaml(board, pico, esp):
    tx, rx = row("OPL to hub")
    yaml = HUB_YAML.read_text()
    hub_tx = int(re.search(r"tx_pin:\s*GPIO(\d+)", yaml).group(1))
    hub_rx = int(re.search(r"rx_pin:\s*GPIO(\d+)", yaml).group(1))
    assert (esp, str(ESP_PAD[hub_rx])) in board.members(gp_net(board, pico, tx)), "Pico TX must reach the hub's rx_pin"
    assert (esp, str(ESP_PAD[hub_tx])) in board.members(gp_net(board, pico, rx)), "hub tx_pin must reach Pico RX"


def test_modbus_rs485(board, pico):
    tx, rx, de = row("Modbus to TEC drivers")
    u = board.by_value("SP3485EN")
    assert (u, "4") in board.members(gp_net(board, pico, tx))  # DI
    assert (u, "1") in board.members(gp_net(board, pico, rx))  # RO
    assert {(u, "2"), (u, "3")} <= board.members(gp_net(board, pico, de))  # /RE + DE
    assert any(v <= 100e3 for v in board.resistors_to(gp_net(board, pico, de), "GND")), "DE must default to receive"


def test_ads1115_bus_and_address(board, pico):
    sda, scl = row("I2C0 SDA/SCL")
    u = board.by_value("ADS1115IDGSR")
    assert (u, "9") in board.members(gp_net(board, pico, sda))
    assert (u, "10") in board.members(gp_net(board, pico, scl))
    addr = int(re.search(r"ADS1115_ADDR: u8 = (0x[0-9a-fA-F]+)", BOARD_RS.read_text()).group(1), 16)
    addr_pin = {"GND": 0x48, "+3V3": 0x49, "I2C_SDA": 0x4A, "I2C_SCL": 0x4B}[board.net(u, 1)]
    assert addr_pin == addr


def test_ntc_channels(board):
    m = re.search(r"NTC_CHANNELS: \[\(u8, u8\); ZONES\] = \[(.*?)\];", BOARD_RS.read_text())
    channels = [tuple(int(x) for x in p) for p in re.findall(r"\((\d+), (\d+)\)", m.group(1))]
    u = board.by_value("ADS1115IDGSR")
    for z, chans in enumerate(channels):
        for ch, kind in zip(chans, ("WATER", "HOT")):
            ain = board.net(u, 4 + ch)
            (node,) = board.through_resistor(ain) - {"GND"}
            term = board.by_value("Z%d NTC %s" % (z, kind))
            assert board.net(term, 1) == node and board.net(term, 2) == "GND"
            assert board.resistors_to(node, "+3V3") == [10e3], "3.3 V -> 10k -> node -> NTC -> GND (board.rs)"


@pytest.mark.parametrize("zone", [0, 1])
def test_zone_outputs_and_flow(board, pico, zone):
    relay, pol, pump, fan, flow = row("Zone %d:" % zone)
    terminals = {relay: ["Z%d ZONE RELAY COIL"], pol: ["Z%d POL A", "Z%d POL B"], pump: ["Z%d PUMP"], fan: ["Z%d FAN"]}
    for gp, names in terminals.items():
        (gate,) = board.through_resistor(gp_net(board, pico, gp))
        (q,) = [r for r, p in board.members(gate) if r.startswith("Q") and p == "1"]
        assert board.fps[q]["value"] == "AO3400A" and board.net(q, 2) == "GND"
        drain = board.net(q, 3)
        for name in names:
            assert board.net(board.by_value(name % zone), 2) == drain, (gp, name)
    (flow_in,) = board.through_resistor(gp_net(board, pico, flow)) - {"+3V3"}
    assert board.net(board.by_value("Z%d FLOW +5V GND SIG" % zone), 3) == flow_in


@pytest.mark.parametrize("prefix,terminal", [("Leak sensor", "LEAK +12V GND SIG"), ("Water level", "LEVEL +5V GND SIG")])
def test_fail_safe_inputs(board, pico, prefix, terminal):
    (gp,) = row(prefix)
    net = gp_net(board, pico, gp)
    assert board.resistors_to(net, "+3V3") == [10e3], "10k pull-up: open wire reads HIGH = fault"
    (sig,) = board.through_resistor(net) - {"+3V3"}
    assert board.net(board.by_value(terminal), 3) == sig


def test_every_gate_has_e9_pull_down(board):
    gates = [board.net(r, 1) for r, f in board.fps.items() if f["value"] == "AO3400A"]
    assert len(gates) == 8
    for g in gates:
        assert any(v <= 8.2e3 for v in board.resistors_to(g, "GND")), g


@pytest.mark.parametrize("zone", [0, 1])
def test_zone_relay_coil_only_through_cutoff_loop(board, zone):
    loop = board.by_value("Z%d CUTOFF LOOP" % zone)
    coil = board.by_value("Z%d ZONE RELAY COIL" % zone)
    assert board.net(loop, 1) == "+12V"
    coil_p = board.net(coil, 1)
    assert coil_p == board.net(loop, 2) and coil_p != "+12V"
    others = {(r, p) for r, p in board.members(coil_p)} - {(loop, "2"), (coil, "1")}
    # only the flyback diode across the coil (cathode on coil+, anode on the driver side)
    assert len(others) == 1
    (d, pad) = others.pop()
    assert d.startswith("D") and pad == "1" and board.net(d, 2) == board.net(coil, 2)
