"""Tests for the Darksoft artifact builder."""

from __future__ import annotations

import hashlib
from pathlib import Path

from darksoft_gen.builder import build
from darksoft_gen.interleave import interleave_pair
from darksoft_gen.romset import scan_directory


def _mk(directory: Path, name: str, data: bytes) -> None:
    (directory / name).write_bytes(data)


def test_build_end_to_end_mame_style(tmp_path: Path) -> None:
    src = tmp_path / "romset"
    src.mkdir()
    _mk(src, "g-s1.rom", b"SSSS")
    _mk(src, "g-m1.rom", b"MMMMMMMM")
    _mk(src, "g-c1.rom", b"\x00\x01\x02\x03")
    _mk(src, "g-c2.rom", b"\xA0\xA1\xA2\xA3")
    _mk(src, "g-v1.rom", b"V1V1")
    _mk(src, "g-v2.rom", b"V2V2")
    _mk(src, "g-p1.rom", b"PROG")
    _mk(src, "g-p2.rom", b"RAM!")
    _mk(src, "readme.txt", b"ignore me")

    romset = scan_directory(src)
    # Force deterministic ordering: scan_directory preserves FS order, which
    # is non-deterministic across platforms. Production behavior is iso with
    # the original (FS-order); for this end-to-end test we sort explicitly.
    romset.c_files[:] = sorted(romset.c_files)
    romset.v_files[:] = sorted(romset.v_files)
    romset.p_files[:] = sorted(romset.p_files)

    report = build(romset, tmp_path / "out", fpga_bytes=b"42")

    assert report.out_dir == tmp_path / "out"
    assert set(report.artifacts) == {"srom", "m1rom", "crom0", "vroma0", "prom", "fpga"}
    assert (tmp_path / "out" / "srom").read_bytes() == b"SSSS"
    assert (tmp_path / "out" / "m1rom").read_bytes() == b"MMMMMMMM"
    assert (tmp_path / "out" / "crom0").read_bytes() == interleave_pair(
        src / "g-c1.rom", src / "g-c2.rom"
    )
    assert (tmp_path / "out" / "vroma0").read_bytes() == b"V1V1V2V2"
    assert (tmp_path / "out" / "prom").read_bytes() == b"PROGRAM!"
    assert (tmp_path / "out" / "fpga").read_bytes() == b"42"

    # Hashes in report match the written file content.
    srom_data = b"SSSS"
    assert report.artifacts["srom"].md5 == hashlib.md5(srom_data).hexdigest()
    assert report.artifacts["srom"].size == len(srom_data)


def test_build_prom_order_p_then_sp(tmp_path: Path) -> None:
    # MAME-style to avoid the NeoRageX SP double-count quirk.
    src = tmp_path / "romset"
    src.mkdir()
    _mk(src, "g-p1.rom", b"AAAA")
    _mk(src, "g-p2.rom", b"BBBB")
    _mk(src, "g-sp1.rom", b"CCCC")
    _mk(src, "g-sp2.rom", b"DDDD")

    romset = scan_directory(src)
    # Force deterministic ordering regardless of FS walk order.
    romset.p_files[:] = sorted(romset.p_files)
    romset.sp_files[:] = sorted(romset.sp_files)

    report = build(romset, tmp_path / "out", fpga_bytes=None)

    assert (tmp_path / "out" / "prom").read_bytes() == b"AAAABBBBCCCCDDDD"
    assert "fpga" not in report.artifacts


def test_build_skips_missing_categories(tmp_path: Path) -> None:
    src = tmp_path / "romset"
    src.mkdir()
    _mk(src, "g-s1.rom", b"only srom")

    romset = scan_directory(src)
    report = build(romset, tmp_path / "out", fpga_bytes=None)

    assert set(report.artifacts) == {"srom"}
    out = tmp_path / "out"
    assert (out / "srom").exists()
    for missing in ("m1rom", "crom0", "vroma0", "prom", "fpga"):
        assert not (out / missing).exists()


def test_build_no_fpga_when_none(tmp_path: Path) -> None:
    src = tmp_path / "romset"
    src.mkdir()
    _mk(src, "g-s1.rom", b"x")

    report = build(scan_directory(src), tmp_path / "out", fpga_bytes=None)

    assert "fpga" not in report.artifacts
    assert not (tmp_path / "out" / "fpga").exists()


def test_build_writes_fpga_when_provided(tmp_path: Path) -> None:
    src = tmp_path / "romset"
    src.mkdir()

    report = build(scan_directory(src), tmp_path / "out", fpga_bytes=b"13")

    assert (tmp_path / "out" / "fpga").read_bytes() == b"13"
    assert report.artifacts["fpga"].md5 == hashlib.md5(b"13").hexdigest()


def test_build_clears_existing_out_dir(tmp_path: Path) -> None:
    src = tmp_path / "romset"
    src.mkdir()
    _mk(src, "g-s1.rom", b"fresh")

    out = tmp_path / "out"
    out.mkdir()
    (out / "stale.bin").write_bytes(b"leftover")
    (out / "sub").mkdir()
    (out / "sub" / "nested").write_bytes(b"deep leftover")

    build(scan_directory(src), out, fpga_bytes=None)

    assert not (out / "stale.bin").exists()
    assert not (out / "sub").exists()
    assert (out / "srom").read_bytes() == b"fresh"


def test_build_crom_two_pairs(tmp_path: Path) -> None:
    src = tmp_path / "romset"
    src.mkdir()
    _mk(src, "g-c1.rom", b"\x00\x01\x02\x03")
    _mk(src, "g-c2.rom", b"\xA0\xA1\xA2\xA3")
    _mk(src, "g-c3.rom", b"\x10\x11\x12\x13")
    _mk(src, "g-c4.rom", b"\xB0\xB1\xB2\xB3")

    romset = scan_directory(src)
    romset.c_files[:] = sorted(romset.c_files)

    build(romset, tmp_path / "out", fpga_bytes=None)

    expected = interleave_pair(src / "g-c1.rom", src / "g-c2.rom") + interleave_pair(
        src / "g-c3.rom", src / "g-c4.rom"
    )
    assert (tmp_path / "out" / "crom0").read_bytes() == expected
