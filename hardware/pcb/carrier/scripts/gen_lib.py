"""Generate the project library: ESP32-S3-DevKitC-1 symbol and socket footprint.

Pin order from Espressif's ESP32-S3-DevKitC-1 v1.1 user guide (J1/J3 tables). Row spacing 22.86 mm and pitch 2.54 mm
measured from Espressif's dimension DXF (DXF_ESP32-S3-DevKitC-1_V1.1_20220429): pads at x = 1.27 / 24.13 mm,
J1 pin 1 (3V3) at the antenna end, J1 pin 22 / J3 pin 22 next to the USB connectors. Board 25.4 mm wide.
"""

import os

from design import ESP_PIN_NAMES
from sexp import S, Sym, dump

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "lib")


def font(size=1.27):
    return S("effects", S("font", S("size", size, size)))


def esp_symbol():
    pins = []
    # J1 on the left (pins 1-22 top to bottom), J3 on the right (pins 23-44 top to bottom)
    for i, name in enumerate(ESP_PIN_NAMES):
        left = i < 22
        row = i if left else i - 22
        x = -15.24 if left else 15.24
        y = 26.67 - row * 2.54
        if name == "3V3":
            etype = "power_out" if i == 0 else "passive"  # one driver per net for ERC; pin 2 is the same rail
        elif name == "5V":
            etype = "power_in"
        elif name == "GND":
            etype = "power_in"
        else:
            etype = "bidirectional"
        pins.append(S("pin", Sym(etype), Sym("line"), S("at", x, round(y, 2), 0 if left else 180), S("length", 3.81),
                      S("name", name, font()), S("number", str(i + 1), font())))
    body = S("symbol", "ESP32-S3-DevKitC-1_0_1",
             S("rectangle", S("start", -11.43, 29.21), S("end", 11.43, -29.21),
               S("stroke", S("width", 0.254), S("type", Sym("default"))), S("fill", S("type", Sym("background")))))
    unit = S("symbol", "ESP32-S3-DevKitC-1_1_1", *pins)

    def prop(k, v, y, hide=False):
        eff = font()
        if hide:
            eff.append(S("hide", Sym("yes")))
        return S("property", k, v, S("at", 0, y, 0), eff)

    return S("symbol", "ESP32-S3-DevKitC-1", S("exclude_from_sim", Sym("no")), S("in_bom", Sym("yes")),
             S("on_board", Sym("yes")),
             prop("Reference", "U", 31.75), prop("Value", "ESP32-S3-DevKitC-1", -31.75),
             prop("Footprint", "carrier:ESP32-S3-DevKitC-1_Socket", -34.29, True),
             prop("Datasheet", "https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html", -36.83, True),
             prop("Description", "ESP32-S3-DevKitC-1 (v1.0/v1.1) on 2x22 sockets, J1 = pins 1-22, J3 = pins 23-44", -39.37, True),
             body, unit)


def socket_footprint(name, descr, pads, outline, texts):
    """Module on female headers. Courtyard = the socket rows only: low SMD parts may sit under the module (it is
    8.5 mm above the board). The module outline is on F.Fab and its ends on the silkscreen."""

    def line(layer, a, b, w=0.12):
        return S("fp_line", S("start", a[0], a[1]), S("end", b[0], b[1]), S("stroke", S("width", w), S("type", Sym("solid"))),
                 S("layer", layer))

    def rect(layer, x0, y0, x1, y1, w):
        return [line(layer, (x0, y0), (x1, y0), w), line(layer, (x1, y0), (x1, y1), w),
                line(layer, (x1, y1), (x0, y1), w), line(layer, (x0, y1), (x0, y0), w)]

    items = []
    for num, x, y in pads:
        shape = Sym("rect") if num == 1 else Sym("circle")
        items.append(S("pad", str(num), Sym("thru_hole"), shape, S("at", x, round(y, 2)), S("size", 1.7, 1.7),
                       S("drill", 1.0), S("layers", "*.Cu", "*.Mask")))
    gfx = rect("F.Fab", *outline, w=0.1)
    for col in sorted({x for _n, x, _y in pads}):
        ys = [y for _n, x, y in pads if x == col]
        gfx += rect("F.CrtYd", col - 1.5, min(ys) - 1.5, col + 1.5, max(ys) + 1.5, 0.05)
        gfx += rect("F.SilkS", col - 1.4, min(ys) - 1.4, col + 1.4, max(ys) + 1.4, 0.12)
    ff = S("effects", S("font", S("size", 1, 1), S("thickness", 0.15)))
    txt = [S("fp_text", Sym("user"), t, S("at", x, y), S("layer", "F.SilkS"), ff) for t, x, y in texts]
    cx = (outline[0] + outline[2]) / 2
    props = [S("property", "Reference", "REF**", S("at", cx, (outline[1] + outline[3]) / 2 - 2), S("layer", "F.SilkS"), ff),
             S("property", "Value", name, S("at", cx, (outline[1] + outline[3]) / 2 + 2), S("layer", "F.Fab"), ff)]
    return S("footprint", name, S("version", 20241229), S("generator", "obc_carrier"), S("layer", "F.Cu"),
             S("descr", descr), S("attr", Sym("through_hole")), *(props + txt + gfx + items))


def esp_footprint():
    """Origin = J1 pin 1, module long axis along +Y, USB end at +Y. Pads 1-22 = J1, 23-44 = J3."""
    pads = [(i + 1, 0.0 if i < 22 else 22.86, (i if i < 22 else i - 22) * 2.54) for i in range(44)]
    return socket_footprint("ESP32-S3-DevKitC-1_Socket",
                            "ESP32-S3-DevKitC-1 on two 1x22 2.54 mm female headers, rows 22.86 mm apart (Espressif DXF v1.1)",
                            pads, (-1.27, -10.2, 24.13, 59.6), [("ANTENNA", 11.43, -6.0), ("USB", 11.43, 57.5)])


def pico_footprint():
    """Raspberry Pi Pico 2 on two 1x20 female headers (same pad positions as KiCad's RaspberryPi_Pico_Common_THT):
    pins 1-20 down the left row, 21-40 up the right row, pin 1 at the USB end."""
    pads = [(i, 0.0, (i - 1) * 2.54) for i in range(1, 21)] + [(i, 17.78, 48.26 - (i - 21) * 2.54) for i in range(21, 41)]
    return socket_footprint("RaspberryPi_Pico2_Socket", "Raspberry Pi Pico 2 on two 1x20 2.54 mm female headers",
                            pads, (-1.61, -2.6, 19.39, 49.63), [("USB", 8.89, -1.0)])


def main():
    os.makedirs(os.path.join(LIB, "carrier.pretty"), exist_ok=True)
    lib = S("kicad_symbol_lib", S("version", 20241209), S("generator", "obc_carrier"), S("generator_version", "1.0"), esp_symbol())
    with open(os.path.join(LIB, "carrier.kicad_sym"), "w") as f:
        f.write(dump(lib) + "\n")
    for fp in (esp_footprint(), pico_footprint()):
        with open(os.path.join(LIB, "carrier.pretty", fp[1] + ".kicad_mod"), "w") as f:
            f.write(dump(fp) + "\n")
    print("library written")


if __name__ == "__main__":
    main()
