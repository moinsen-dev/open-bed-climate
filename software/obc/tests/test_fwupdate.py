import pytest

from obc import fwupdate as F
from obc import protocol as P

SLOT = F.FwSlot(0x20_0000, 0x10_0000)


def test_crc32_reference_value():
    assert F.crc32(b"123456789") == 0xCBF43926
    assert F.crc32(b"6789", F.crc32(b"12345")) == 0xCBF43926


def flash_transfer(img, lose_status_every=0):
    """Drive a session against a simulated flash; returns the slot contents."""
    flash = bytearray(b"\x00" * SLOT.size)  # not erased: every byte written must have been erased first
    erased = set()
    u = F.FwUpdate()
    assert u.begin(F.fw_begin(len(img), F.crc32(img), F.version_word(0, 2, 0)), SLOT, True) == F.FwResult.OK
    for k, off in enumerate(range(0, len(img), F.CHUNK_MAX)):
        payload = F.fw_chunk(off, img[off : off + F.CHUNK_MAX])
        for _ in range(2 if lose_status_every and k % lose_status_every == 0 else 1):
            r, plan = u.chunk(payload)
            assert r == F.FwResult.OK
            if plan:
                for s in range(plan.erase_from, plan.erase_to, F.SECTOR):
                    flash[s - SLOT.offset : s - SLOT.offset + F.SECTOR] = b"\xff" * F.SECTOR
                    erased.add(s)
                data = payload[4:]
                a = plan.addr - SLOT.offset
                assert all((SLOT.offset + (a + i) // F.SECTOR * F.SECTOR) in erased for i in range(len(data)))
                flash[a : a + len(data)] = data
                assert u.written(payload, True) == F.FwResult.OK
    assert u.end() == F.FwResult.OK and u.state == F.FwState.DONE
    return bytes(flash[: len(img)])


@pytest.mark.parametrize("n", [1, 255, 256, 4096, 4097, 70_001])
def test_transfer_writes_exact_image_and_erases_before_writing(n):
    img = bytes((i * 7 + 3) % 251 for i in range(n))
    assert flash_transfer(img) == img
    assert flash_transfer(img, lose_status_every=3) == img  # resends are harmless


def test_refuses_while_a_zone_is_on_and_without_partitions():
    u = F.FwUpdate()
    assert u.begin(F.fw_begin(10, 0, 0), SLOT, zones_idle=False) == F.FwResult.BUSY
    assert u.begin(F.fw_begin(10, 0, 0), None, zones_idle=True) == F.FwResult.NO_PARTITIONS
    assert not u.active


def test_status_frame_roundtrip():
    st = F.FwStatus(9, 1, 0, 4096, F.version_word(1, 2, 3))
    f = P.decode(P.encode(P.Frame(3, P.MsgType.FW_STATUS, st.pack())))
    assert F.FwStatus.unpack(f.payload) == st
    assert F.version_word(1, 2, 3) == 0x01020003
