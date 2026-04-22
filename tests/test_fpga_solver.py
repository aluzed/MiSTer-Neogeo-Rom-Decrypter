"""Tests for the fpga index solver."""

from __future__ import annotations

import hashlib

from darksoft_gen.fpga_solver import resolve_fpga


def test_resolve_zero() -> None:
    md5 = hashlib.md5(b"0").hexdigest()
    assert resolve_fpga(md5) == b"0"


def test_resolve_known_key_13() -> None:
    # Matches the real SMDB entry for e.g. 2020bb/fpga.
    assert resolve_fpga("c51ce410c124a10e0db5e4b97fc2af39") == b"13"


def test_resolve_upper_case_input() -> None:
    md5 = hashlib.md5(b"42").hexdigest().upper()
    assert resolve_fpga(md5) == b"42"


def test_resolve_boundary_255() -> None:
    md5 = hashlib.md5(b"255").hexdigest()
    assert resolve_fpga(md5) == b"255"


def test_resolve_unknown_returns_none() -> None:
    # MD5 of a string well outside [0, 255] — must miss the lookup.
    md5 = hashlib.md5(b"not-a-valid-key").hexdigest()
    assert resolve_fpga(md5) is None

    md5 = hashlib.md5(b"9999").hexdigest()
    assert resolve_fpga(md5) is None
