"""Tests for the pure interleaving primitives.

Every test writes its mini-ROM fixtures into ``tmp_path`` so the expected
bytes can be inspected directly in the test source — no committed binary
fixtures, no golden files.
"""

from __future__ import annotations

from pathlib import Path

from darksoft_gen.interleave import interleave_pair, interleave_pairs


def _write(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


def test_pair_basic(tmp_path: Path) -> None:
    a = _write(tmp_path / "c1", bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]))
    b = _write(tmp_path / "c2", bytes([0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7]))

    expected = bytes(
        [
            0x00, 0x01, 0xA0, 0xA1,
            0x02, 0x03, 0xA2, 0xA3,
            0x04, 0x05, 0xA4, 0xA5,
            0x06, 0x07, 0xA6, 0xA7,
        ]
    )
    assert interleave_pair(a, b) == expected


def test_pair_two_bytes(tmp_path: Path) -> None:
    a = _write(tmp_path / "c1", bytes([0x11, 0x22]))
    b = _write(tmp_path / "c2", bytes([0xAA, 0xBB]))

    assert interleave_pair(a, b) == bytes([0x11, 0x22, 0xAA, 0xBB])


def test_pair_unequal_size(tmp_path: Path) -> None:
    # 8 bytes vs 4 bytes: stop once the shorter file is exhausted.
    a = _write(tmp_path / "c1", bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]))
    b = _write(tmp_path / "c2", bytes([0xA0, 0xA1, 0xA2, 0xA3]))

    expected = bytes(
        [
            0x00, 0x01, 0xA0, 0xA1,
            0x02, 0x03, 0xA2, 0xA3,
        ]
    )
    assert interleave_pair(a, b) == expected


def test_pair_odd_trailing_byte(tmp_path: Path) -> None:
    # 3 bytes each: we can only form one full 2-byte chunk per file.
    # The trailing single byte of each file is dropped (read(2) returns 1 byte,
    # which is < CHUNK, so the loop stops before writing anything for that round).
    a = _write(tmp_path / "c1", bytes([0x00, 0x01, 0x02]))
    b = _write(tmp_path / "c2", bytes([0xA0, 0xA1, 0xA2]))

    assert interleave_pair(a, b) == bytes([0x00, 0x01, 0xA0, 0xA1])


def test_pairs_four_files(tmp_path: Path) -> None:
    c1 = _write(tmp_path / "c1", bytes([0x00, 0x01, 0x02, 0x03]))
    c2 = _write(tmp_path / "c2", bytes([0xA0, 0xA1, 0xA2, 0xA3]))
    c3 = _write(tmp_path / "c3", bytes([0x10, 0x11, 0x12, 0x13]))
    c4 = _write(tmp_path / "c4", bytes([0xB0, 0xB1, 0xB2, 0xB3]))

    expected = bytes(
        [
            # pair (c1, c2)
            0x00, 0x01, 0xA0, 0xA1,
            0x02, 0x03, 0xA2, 0xA3,
            # pair (c3, c4)
            0x10, 0x11, 0xB0, 0xB1,
            0x12, 0x13, 0xB2, 0xB3,
        ]
    )
    assert interleave_pairs([c1, c2, c3, c4]) == expected


def test_pairs_odd_count(tmp_path: Path) -> None:
    # Three files: only one pair can be formed, the trailing file is dropped
    # (iso-behavior with the original split_per2).
    c1 = _write(tmp_path / "c1", bytes([0x00, 0x01, 0x02, 0x03]))
    c2 = _write(tmp_path / "c2", bytes([0xA0, 0xA1, 0xA2, 0xA3]))
    c3 = _write(tmp_path / "c3", bytes([0xDE, 0xAD, 0xBE, 0xEF]))

    expected = bytes(
        [
            0x00, 0x01, 0xA0, 0xA1,
            0x02, 0x03, 0xA2, 0xA3,
        ]
    )
    assert interleave_pairs([c1, c2, c3]) == expected


def test_pairs_empty_list() -> None:
    assert interleave_pairs([]) == b""


def test_pairs_single_file(tmp_path: Path) -> None:
    c1 = _write(tmp_path / "c1", bytes([0x01, 0x02, 0x03, 0x04]))

    assert interleave_pairs([c1]) == b""
