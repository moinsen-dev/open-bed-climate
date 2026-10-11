"""Open Bed Climate Tier 0 carrier, Rev A: the netlist as code (single source of truth).

Every part lists its symbol, footprint, value, LCSC number and the net on each pin. gen_sch.py turns this into
the KiCad schematic, gen_pcb.py into the board. The Pico pin map follows firmware/opod-pico2/src/board.rs;
software/opod/tests/test_carrier_pcb.py checks the generated board against board.rs and the hub YAML.

Runs on Python 3.9 (KiCad's bundled interpreter): no match statements, no `X | Y` type unions.
"""

from collections import OrderedDict

# ---------------------------------------------------------------------------------------------------------------
# Library parts
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
SMA = "Diode_SMD:D_SMA"
TB508_2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"
TB35_2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal"
TB35_3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal"
HDR4 = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
HDR2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
TP = "TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm"

# LCSC numbers. VERIFIED = seen on an LCSC/JLCPCB product page while designing Rev A (2026-10-11).
# The others are the usual JLC basic-library numbers; JLC's BOM matcher shows the real part, check it there.
LCSC = {
    "10k": "C25804",  # verified
    "100n": "C14663",  # verified
    "AO3400A": "C20917",  # verified
    "SS34": "C8678",  # verified
    "ADS1115IDGSR": "C37593",  # verified
    "SP3485EN": "C8963",  # verified
    "LM2596S-5.0": "C116713",  # verified (TI)
    "SMBJ15A": "C699013",  # verified (Yangjie)
    "BAT54S": "C916425",  # verified (JSMSEMI)
    "4.7k": "C23162",
    "1k": "C21190",
    "220": "C22962",
    "120": "C22787",
    "10u": "C15850",
    "22u": "C45783",
    "LED_R": "C2286",
}
VERIFIED_LCSC = {"C25804", "C14663", "C20917", "C8678", "C37593", "C8963", "C116713", "C699013", "C916425"}


class Part(object):
    def __init__(self, ref, lib_id, value, footprint, pins, lcsc="", jlc=True, block="", note=""):
        self.ref = ref
        self.lib_id = lib_id
        self.value = value
        self.footprint = footprint
        self.pins = OrderedDict(pins)  # pin number (str) -> net name, or None for no-connect
        self.lcsc = lcsc
        self.jlc = jlc  # True: SMD part for JLC assembly; False: hand-soldered / THT, not in the CPL
        self.block = block
        self.note = note


PARTS = []
_counters = {}


def _ref(prefix):
    _counters[prefix] = _counters.get(prefix, 0) + 1
    return "%s%d" % (prefix, _counters[prefix])


def add(prefix, lib_id, value, footprint, pins, **kw):
    p = Part(_ref(prefix), lib_id, value, footprint, [(str(k), v) for k, v in pins], **kw)
    PARTS.append(p)
    return p


def R(value, a, b, block, lcsc_key=None, fp=R0603, lcsc=None):
    return add("R", "Device:R", value, fp, [(1, a), (2, b)], lcsc=lcsc or LCSC.get(lcsc_key or value, ""), block=block)


def C(value, a, b, block, fp=C0603, lcsc_key=None):
    return add("C", "Device:C", value, fp, [(1, a), (2, b)], lcsc=LCSC.get(lcsc_key or value, ""), block=block)


def terminal(value, nets, block, pitch=5.08):
    n = len(nets)
    if pitch == 5.08:
        fp = TB508_2 if n == 2 else "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal"
    else:
        fp = TB35_2 if n == 2 else TB35_3
    return add("J", "Connector:Screw_Terminal_01x%02d" % n, value, fp, list(enumerate(nets, 1)), jlc=False, block=block)


# ---------------------------------------------------------------------------------------------------------------
# Pico 2 (socketed on 2x 1x20 female headers; the footprint has the Pico's 40 castellation/THT positions)
PICO_GP = {  # Pico 2 GPIO -> net. Mirrors board.rs; checked by test_carrier_pcb.py
    0: "OPL_TX", 1: "OPL_RX",
    4: "MB_TX", 5: "MB_RX", 6: "MB_DE",
    8: "I2C_SDA", 9: "I2C_SCL",
    10: "Z0_RELAY", 11: "Z0_POL", 12: "Z0_PUMP", 13: "Z0_FAN", 14: "Z0_FLOW",
    16: "Z1_RELAY", 17: "Z1_POL", 18: "Z1_PUMP", 19: "Z1_FAN", 20: "Z1_FLOW",
    21: "LEAK", 22: "LEVEL",
}
PICO_PIN_OF_GP = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 11: 15, 12: 16, 13: 17,
                  14: 19, 15: 20, 16: 21, 17: 22, 18: 24, 19: 25, 20: 26, 21: 27, 22: 29, 26: 31, 27: 32, 28: 34}
_pico = OrderedDict((str(i), None) for i in range(1, 41))
for gp, net in PICO_GP.items():
    _pico[str(PICO_PIN_OF_GP[gp])] = net
for gnd in (3, 8, 13, 18, 23, 28, 33, 38):
    _pico[str(gnd)] = "GND"
_pico["36"] = "+3V3"  # 3V3 OUT: the Pico's regulator feeds the ADS, NTC dividers, RS-485 and pull-ups
_pico["39"] = "VSYS"  # fed from +5V through a Schottky (the Pico has its own VBUS->VSYS diode)
PICO = add("U", "MCU_Module:RaspberryPi_Pico", "Raspberry Pi Pico 2", "carrier:RaspberryPi_Pico2_Socket",
           list(_pico.items()), jlc=False, block="mcu",
           note="Socket: 2x 1x20 female header 2.54 mm (hand-soldered), Pico 2 with male headers plugs in")

# ESP32-S3-DevKitC-1 hub (socketed, 2x 1x22 female headers, rows 22.86 mm apart). Pads 1-22 = J1, 23-44 = J3.
ESP_J1 = ["3V3", "3V3", "RST", "GPIO4", "GPIO5", "GPIO6", "GPIO7", "GPIO15", "GPIO16", "GPIO17", "GPIO18",
          "GPIO8", "GPIO3", "GPIO46", "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13", "GPIO14", "5V", "GND"]
ESP_J3 = ["GND", "TX", "RX", "GPIO1", "GPIO2", "GPIO42", "GPIO41", "GPIO40", "GPIO39", "GPIO38", "GPIO37",
          "GPIO36", "GPIO35", "GPIO0", "GPIO45", "GPIO48", "GPIO47", "GPIO21", "GPIO20", "GPIO19", "GND", "GND"]
ESP_PIN_NAMES = ESP_J1 + ESP_J3
ESP_NETS = {"GPIO18": "OPL_TX", "GPIO17": "OPL_RX",  # hub rx_pin GPIO18 <- Pico GP0, tx_pin GPIO17 -> Pico GP1
            "GPIO8": "HUB_SDA", "GPIO9": "HUB_SCL",  # hub I2C for the room SHT45 (add an i2c: block to the hub YAML)
            "5V": "ESP_5V", "3V3": "ESP_3V3", "GND": "GND"}
ESP = add("U", "carrier:ESP32-S3-DevKitC-1", "ESP32-S3-DevKitC-1", "carrier:ESP32-S3-DevKitC-1_Socket",
          [(i + 1, ESP_NETS.get(n)) for i, n in enumerate(ESP_PIN_NAMES)], jlc=False, block="mcu",
          note="Socket: 2x 1x22 female header 2.54 mm (hand-soldered)")

# ---------------------------------------------------------------------------------------------------------------
# 12 V input: barrel jack || screw terminal -> mini blade fuse -> TVS crowbar -> 2x P-FET reverse protection
add("J", "Connector:Barrel_Jack_Switch", "12V IN 5.5x2.5 (Solo only, <=5 A)", "Connector_BarrelJack:BarrelJack_Horizontal",
    [(1, "+12V_IN"), (2, "GND"), (3, None)], jlc=False, block="power")
terminal("12V IN", ["+12V_IN", "GND"], "power")
terminal("STAR GND", ["GND", "GND"], "power")
add("F", "Device:Fuse", "5A mini blade", "Fuse:Fuseholder_Blade_Mini_Keystone_3568", [(1, "+12V_IN"), (2, "+12V_F")],
    jlc=False, block="power", note="Keystone 3568 holder + ATM mini blade fuse: 5 A on 1 oz copper, 7.5 A only on 2 oz")
add("D", "Device:D_Zener", "SMBJ15A", "Diode_SMD:D_SMB", [(1, "+12V_F"), (2, "GND")], lcsc=LCSC["SMBJ15A"], block="power",
    note="TVS: clamps transients; a 24 V brick plugged in by mistake makes it conduct and blows the fuse")
add("Q", "Transistor_FET:Q_PMOS_GDS", "AOD4185", "Package_TO_SOT_SMD:TO-252-2",
    [(1, "RPP_G"), (2, "+12V_F"), (3, "+12V")], block="power",
    note="Reverse-polarity P-FET, -40 V, <= 15 mOhm, TO-252: ~0.7 W at 7 A on its copper. LCSC number to pick")
add("D", "Device:D_Zener", "BZT52C12", "Diode_SMD:D_SOD-123", [(1, "+12V"), (2, "RPP_G")], block="power",
    note="Gate clamp, V_GS <= 12 V")
R("10k", "RPP_G", "GND", "power")
C("100n", "+12V", "GND", "power")

# 12 V -> 5 V buck, 3 A (LM2596S-5.0, fixed output)
add("U", "Regulator_Switching:LM2596S-5", "LM2596S-5.0", "Package_TO_SOT_SMD:TO-263-5_TabPin3",
    [(1, "+12V"), (2, "BUCK_SW"), (3, "GND"), (4, "+5V"), (5, "GND")], lcsc=LCSC["LM2596S-5.0"], block="power")
add("C", "Device:C_Polarized", "100u 35V", "Capacitor_SMD:CP_Elec_6.3x7.7", [(1, "+12V"), (2, "GND")], block="power",
    note="Bulk input cap, aluminium electrolytic low ESR; LCSC number to pick")
C("10u", "+12V", "GND", "power", fp=C0805)  # 2x 10 uF ceramic carry the input ripple current
C("10u", "+12V", "GND", "power", fp=C0805)
add("D", "Device:D_Schottky", "SS54", "Diode_SMD:D_SMC", [(1, "BUCK_SW"), (2, "GND")], block="power",
    note="Catch diode 5 A 40 V; LCSC number to pick")
add("L", "Device:L", "33uH 4A", "Inductor_SMD:L_12x12mm_H8mm", [(1, "BUCK_SW"), (2, "+5V")], block="power",
    note="Shielded power inductor, I_sat >= 4 A; LCSC number to pick")
add("C", "Device:C_Polarized", "220u 16V", "Capacitor_SMD:CP_Elec_6.3x7.7", [(1, "+5V"), (2, "GND")], block="power",
    note="Output cap, needs some ESR (LM2596 is voltage-mode); LCSC number to pick")
C("22u", "+5V", "GND", "power", fp=C0805)
R("1k", "+5V", "LED_PWR", "power")
add("D", "Device:LED", "PWR 5V", "LED_SMD:LED_0603_1608Metric", [(1, "GND"), (2, "LED_PWR")], lcsc=LCSC["LED_R"], block="power")

# 5 V ORing: board 5 V reaches each module through a Schottky, so it never back-feeds a USB port behind it
add("D", "Device:D_Schottky", "SS34", SMA, [(1, "VSYS"), (2, "+5V")], lcsc=LCSC["SS34"], block="power")
add("D", "Device:D_Schottky", "SS34", SMA, [(1, "ESP_5V"), (2, "+5V")], lcsc=LCSC["SS34"], block="power")
C("10u", "+3V3", "GND", "power", fp=C0805)

for v, net in (("TP 12V", "+12V"), ("TP 5V", "+5V"), ("TP 3V3", "+3V3"), ("TP GND", "GND")):
    add("TP", "Connector:TestPoint", v, TP, [(1, net)], jlc=False, block="power")

# ---------------------------------------------------------------------------------------------------------------
# ADS1115 @ 0x48 (ADDR -> GND) and four NTC dividers: 3.3 V -> 10k 0.1 % -> node -> NTC -> GND, 1k/100n RC to the ADS
NTC_CHANNELS = [(0, 1), (2, 3)]  # board.rs NTC_CHANNELS: (water, hot side) per zone
add("U", "Analog_ADC:ADS1115IDGS", "ADS1115IDGSR", "Package_SO:MSOP-10_3x3mm_P0.5mm",
    [(1, "GND"), (2, None), (3, "GND"), (4, "ADS_AIN0"), (5, "ADS_AIN1"), (6, "ADS_AIN2"), (7, "ADS_AIN3"),
     (8, "+3V3"), (9, "I2C_SDA"), (10, "I2C_SCL")], lcsc=LCSC["ADS1115IDGSR"], block="adc")
C("100n", "+3V3", "GND", "adc")
R("4.7k", "I2C_SDA", "+3V3", "adc")
R("4.7k", "I2C_SCL", "+3V3", "adc")
for z, (water, hot) in enumerate(NTC_CHANNELS):
    for ch, kind in ((water, "WATER"), (hot, "HOT")):
        node = "Z%d_NTC_%s" % (z, kind[0])
        R("10k 0.1%", "+3V3", node, "adc", lcsc="")  # precision divider resistor, see README
        R("1k", node, "ADS_AIN%d" % ch, "adc")
        C("100n", "ADS_AIN%d" % ch, "GND", "adc")
        terminal("Z%d NTC %s" % (z, kind), [node, "GND"], "zone%d" % z, pitch=3.5)
add("J", "Connector_Generic:Conn_01x04", "I2C PICO (3V3 GND SDA SCL)", HDR4,
    [(1, "+3V3"), (2, "GND"), (3, "I2C_SDA"), (4, "I2C_SCL")], jlc=False, block="adc")

# Hub I2C header (room SHT45), on the ESP32's own 3.3 V
add("J", "Connector_Generic:Conn_01x04", "I2C HUB SHT45 (3V3 GND SDA SCL)", HDR4,
    [(1, "ESP_3V3"), (2, "GND"), (3, "HUB_SDA"), (4, "HUB_SCL")], jlc=False, block="mcu")
R("4.7k", "HUB_SDA", "ESP_3V3", "mcu")
R("4.7k", "HUB_SCL", "ESP_3V3", "mcu")

# ---------------------------------------------------------------------------------------------------------------
# RS-485 (Modbus to the DPS modules): SP3485EN on UART1, DE+/RE on GP6 (pulled low = receive)
add("U", "Interface_UART:SP3485EN", "SP3485EN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    [(1, "MB_RX"), (2, "MB_DE"), (3, "MB_DE"), (4, "MB_TX"), (5, "GND"), (6, "RS485_A"), (7, "RS485_B"), (8, "+3V3")],
    lcsc=LCSC["SP3485EN"], block="rs485")
C("100n", "+3V3", "GND", "rs485")
R("10k", "MB_DE", "GND", "rs485")
R("120", "RS485_A", "RS485_TERM", "rs485")
add("JP", "Jumper:Jumper_2_Open", "TERM 120R", HDR2, [(1, "RS485_TERM"), (2, "RS485_B")], jlc=False, block="rs485",
    note="Fit a jumper only if this end of the bus has no other termination")
terminal("RS485 A B GND", ["RS485_A", "RS485_B", "GND"], "rs485", pitch=3.5)

# ---------------------------------------------------------------------------------------------------------------
# Fail-safe inputs: 1k series, BAT54S clamp to 3.3 V/GND, 10k pull-up at the GPIO. Open wire = HIGH = fault.
def protected_input(gpio_net, in_net, block, cap=None):
    R("1k", in_net, gpio_net, block)
    R("10k", gpio_net, "+3V3", block)
    add("D", "Diode:BAT54S", "BAT54S", SOT23, [(1, "GND"), (2, "+3V3"), (3, gpio_net)], lcsc=LCSC["BAT54S"], block=block)
    if cap:
        C(cap, gpio_net, "GND", block)


protected_input("LEAK", "LEAK_IN", "inputs", cap="100n")
terminal("LEAK +12V GND SIG", ["+12V", "GND", "LEAK_IN"], "inputs", pitch=3.5)
protected_input("LEVEL", "LEVEL_IN", "inputs", cap="100n")
terminal("LEVEL +5V GND SIG", ["+5V", "GND", "LEVEL_IN"], "inputs", pitch=3.5)

# ---------------------------------------------------------------------------------------------------------------
# Zone drivers: AO3400A low side, 220R gate resistor, 4.7k gate pull-down (RP2350-E9: <= 8.2k), SS34 flyback
def driver(z, func):
    gpio = "Z%d_%s" % (z, func)
    gate = gpio + "_G"
    drain = gpio + "_D"
    R("220", gpio, gate, "zone%d" % z)
    R("4.7k", gate, "GND", "zone%d" % z)
    add("Q", "Transistor_FET:AO3400A", "AO3400A", SOT23, [(1, gate), (2, "GND"), (3, drain)],
        lcsc=LCSC["AO3400A"], block="zone%d" % z)
    return drain


def flyback(cathode, anode, z):
    add("D", "Device:D_Schottky", "SS34", SMA, [(1, cathode), (2, anode)], lcsc=LCSC["SS34"], block="zone%d" % z)


for z in range(2):
    # Zone relay: +12V -> CUTOFF LOOP (all bimetal cutoffs in series, off-board) -> coil+ -> coil -> MOSFET.
    # The flyback sits across the coil itself (cathode on coil+), so an opening cutoff never has to break the coil's
    # stored energy as an arc.
    d = driver(z, "RELAY")
    coil_p = "Z%d_COIL_P" % z
    terminal("Z%d CUTOFF LOOP" % z, ["+12V", coil_p], "zone%d" % z)
    terminal("Z%d ZONE RELAY COIL" % z, [coil_p, d], "zone%d" % z)
    flyback(coil_p, d, z)
    # Polarity: two coil outputs on one MOSFET (2x SPDT automotive relays, or use POL A alone for one DPDT relay)
    d = driver(z, "POL")
    terminal("Z%d POL A" % z, ["+12V", d], "zone%d" % z)
    terminal("Z%d POL B" % z, ["+12V", d], "zone%d" % z)
    flyback("+12V", d, z)
    flyback("+12V", d, z)
    d = driver(z, "PUMP")
    terminal("Z%d PUMP" % z, ["+12V", d], "zone%d" % z)
    flyback("+12V", d, z)
    d = driver(z, "FAN")
    terminal("Z%d FAN" % z, ["+12V", d], "zone%d" % z)
    flyback("+12V", d, z)
    # Flow sensor (5 V hall sensor, open collector or 5 V push-pull): protected like the fail-safe inputs
    protected_input("Z%d_FLOW" % z, "Z%d_FLOW_IN" % z, "zone%d" % z)
    terminal("Z%d FLOW +5V GND SIG" % z, ["+5V", "GND", "Z%d_FLOW_IN" % z], "zone%d" % z, pitch=3.5)

for i in range(4):
    add("H", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", [], jlc=False, block="mech")

# Net classes for routing (width mm). Everything else: signal 0.25 mm.
POWER_NETS = {"+12V_IN", "+12V_F", "+12V"}  # GND: default class, plus pours on both layers
LOAD_NETS = {"+5V", "BUCK_SW", "VSYS", "ESP_5V"} | {"Z%d_%s_D" % (z, f) for z in range(2) for f in ("RELAY", "POL", "PUMP", "FAN")} \
    | {"Z%d_COIL_P" % z for z in range(2)}


def nets():
    out = OrderedDict()
    for p in PARTS:
        for pin, n in p.pins.items():
            if n:
                out.setdefault(n, []).append((p.ref, pin))
    return out


if __name__ == "__main__":
    ns = nets()
    print("%d parts, %d nets" % (len(PARTS), len(ns)))
    for n, pins in ns.items():
        if len(pins) < 2:
            print("single-pin net:", n, pins)
