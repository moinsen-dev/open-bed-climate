"""Check a Pico 2 firmware UF2 before it is published.

Usage: python3 check_uf2.py FILE.uf2 [...]

Every block must be a valid UF2 block. The image must be for RP2350 Arm Secure (family 0xe48bff59) and start at
the beginning of flash (0x10000000). It must lead with the RP2350-E10 workaround: one "absolute" block (family
0xe48bff57) at 0x10ffff00, which the bootrom discards, so the image is written where it belongs.
"""

import struct
import sys

MAGIC_START0, MAGIC_START1, MAGIC_END = 0x0A324655, 0x9E5D5157, 0x0AB16F30
FLAG_FAMILY_ID = 0x00002000
RP2350_ARM_S = 0xE48BFF59
ABSOLUTE = 0xE48BFF57
E10_ADDR = 0x10FFFF00
FLASH_START, FLASH_END = 0x10000000, 0x10400000  # Pico 2: 4 MB


def check(path):
    data = open(path, "rb").read()
    if not data or len(data) % 512:
        return [f"size {len(data)} is not a multiple of 512"]
    blocks = [struct.unpack_from("<8I", data, o) + struct.unpack_from("<I", data, o + 508) for o in range(0, len(data), 512)]
    problems = []
    for k, (m0, m1, flags, addr, size, _no, _n, fam, mend) in enumerate(blocks):
        if (m0, m1, mend) != (MAGIC_START0, MAGIC_START1, MAGIC_END):
            problems.append(f"block {k}: bad magic")
        if not flags & FLAG_FAMILY_ID:
            problems.append(f"block {k}: no family id")
        if size != 256:
            problems.append(f"block {k}: payload {size} bytes (expected 256)")
    first, image = blocks[0], blocks[1:]
    if (first[7], first[3]) != (ABSOLUTE, E10_ADDR):
        problems.append(f"first block is not the RP2350-E10 absolute block (family {first[7]:#x} at {first[3]:#x})")
    if not image:
        return problems + ["no image blocks"]
    fams = {b[7] for b in image}
    if fams != {RP2350_ARM_S}:
        problems.append("image family " + ", ".join(f"{f:#x}" for f in sorted(fams)) + f" (expected {RP2350_ARM_S:#x} RP2350-ARM-S)")
    addrs = [b[3] for b in image]
    if min(addrs) != FLASH_START or max(addrs) + 256 > FLASH_END:
        problems.append(f"image spans {min(addrs):#x}..{max(addrs) + 256:#x}, expected to start at {FLASH_START:#x} inside flash")
    if len(set(addrs)) != len(addrs):
        problems.append("duplicate block addresses")
    seq = [(b[5], b[6]) for b in image]
    if [s[0] for s in seq] != list(range(len(image))) or {s[1] for s in seq} != {len(image)}:
        problems.append("image block numbers are not 0..n-1 of n")
    return problems


if __name__ == "__main__":
    bad = False
    for path in sys.argv[1:]:
        problems = check(path)
        bad |= bool(problems)
        print(f"{path}: " + ("OK" if not problems else "FAIL\n  " + "\n  ".join(problems)))
    sys.exit(1 if bad or len(sys.argv) < 2 else 0)
