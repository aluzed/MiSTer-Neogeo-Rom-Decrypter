"""Tests for romset detection.

Fixtures are created as empty files in ``tmp_path`` — only filenames matter
for classification. List comparisons use ``sorted()`` because filesystem
iteration order is not deterministic across platforms, but the membership
of each category is.
"""

from __future__ import annotations

from pathlib import Path

from darksoft_gen.romset import scan_directory


def _touch(directory: Path, *names: str) -> None:
    for name in names:
        (directory / name).write_bytes(b"")


def test_scan_mame_style(tmp_path: Path) -> None:
    _touch(
        tmp_path,
        "foo-s1.rom",
        "foo-m1.rom",
        "foo-p1.rom",
        "foo-p2.rom",
        "foo-c1.rom",
        "foo-c2.rom",
        "foo-v1.rom",
        "preview.jpg",
        "readme.txt",
    )

    rs = scan_directory(tmp_path)

    assert rs.directory == tmp_path
    assert rs.s_rom == "foo-s1.rom"
    assert rs.m1_rom == "foo-m1.rom"
    assert sorted(rs.p_files) == ["foo-p1.rom", "foo-p2.rom"]
    assert sorted(rs.c_files) == ["foo-c1.rom", "foo-c2.rom"]
    assert sorted(rs.v_files) == ["foo-v1.rom"]
    assert rs.sp_files == []


def test_scan_neoragex_style(tmp_path: Path) -> None:
    _touch(
        tmp_path,
        "foo.s1",
        "foo.m1",
        "foo.p1",
        "foo.c1",
        "foo.c2",
        "foo.v1",
    )

    rs = scan_directory(tmp_path)

    assert rs.s_rom == "foo.s1"
    assert rs.m1_rom == "foo.m1"
    assert sorted(rs.p_files) == ["foo.p1"]
    assert sorted(rs.c_files) == ["foo.c1", "foo.c2"]
    assert sorted(rs.v_files) == ["foo.v1"]
    assert rs.sp_files == []


def test_scan_with_mame_sp(tmp_path: Path) -> None:
    # MAME-style SP: no double-count, the P2 regex [-_]p\d.(rom|bin)$
    # does not match "foo-sp1.rom".
    _touch(tmp_path, "foo-p1.rom", "foo-sp1.rom")

    rs = scan_directory(tmp_path)

    assert sorted(rs.p_files) == ["foo-p1.rom"]
    assert sorted(rs.sp_files) == ["foo-sp1.rom"]


def test_scan_neoragex_sp_quirk(tmp_path: Path) -> None:
    # Locks the known iso-behavior quirk: the P pattern ".p\d$" has an
    # unescaped dot, so "foo.sp1" matches it as well (the '.' consumes 's').
    # Downstream the builder will write SP bytes twice into the prom in this
    # rare NeoRageX+SP case. See romset.py module docstring for context.
    _touch(tmp_path, "foo.p1", "foo.sp1")

    rs = scan_directory(tmp_path)

    assert sorted(rs.p_files) == ["foo.p1", "foo.sp1"]
    assert sorted(rs.sp_files) == ["foo.sp1"]


def test_scan_empty_directory(tmp_path: Path) -> None:
    rs = scan_directory(tmp_path)

    assert rs.directory == tmp_path
    assert rs.s_rom is None
    assert rs.m1_rom is None
    assert rs.p_files == []
    assert rs.c_files == []
    assert rs.v_files == []
    assert rs.sp_files == []


def test_scan_ignores_subdirectories(tmp_path: Path) -> None:
    # Root: one M1 file. Subdir: one S file — must be ignored (single-level).
    _touch(tmp_path, "bar.m1")
    sub = tmp_path / "sub"
    sub.mkdir()
    _touch(sub, "foo.s1")

    rs = scan_directory(tmp_path)

    assert rs.m1_rom == "bar.m1"
    assert rs.s_rom is None
    assert rs.p_files == []
    assert rs.c_files == []
    assert rs.v_files == []
    assert rs.sp_files == []
