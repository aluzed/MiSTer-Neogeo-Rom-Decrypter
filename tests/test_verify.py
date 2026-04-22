"""Tests for SMDB verification."""

from __future__ import annotations

from pathlib import Path

from darksoft_gen.builder import BuildArtifact, BuildReport
from darksoft_gen.smdb import SmdbEntry
from darksoft_gen.verify import verify


def _art(md5: str) -> BuildArtifact:
    return BuildArtifact(
        path=Path("/fake"),
        size=0,
        sha256="0" * 64,
        sha1="0" * 40,
        md5=md5,
        crc32="00000000",
    )


def _smdb_entry(md5: str, category: str) -> SmdbEntry:
    return SmdbEntry(
        sha256="0" * 64,
        path=f"Darksoft Neo Geo/games/g/{category}",
        sha1="0" * 40,
        md5=md5,
        crc32="00000000",
    )


def test_verify_all_ok() -> None:
    report = BuildReport(
        out_dir=Path("/tmp"),
        artifacts={
            "srom": _art("aa"),
            "prom": _art("bb"),
        },
    )
    smdb_game = {
        "srom": _smdb_entry("aa", "srom"),
        "prom": _smdb_entry("bb", "prom"),
    }

    results = verify(report, smdb_game)

    assert [r.status for r in results] == ["ok", "ok"]
    assert {r.category for r in results} == {"srom", "prom"}


def test_verify_mismatch() -> None:
    report = BuildReport(
        out_dir=Path("/tmp"),
        artifacts={"srom": _art("aa"), "prom": _art("WRONG")},
    )
    smdb_game = {
        "srom": _smdb_entry("aa", "srom"),
        "prom": _smdb_entry("bb", "prom"),
    }

    results = verify(report, smdb_game)
    by_cat = {r.category: r for r in results}

    assert by_cat["srom"].status == "ok"
    assert by_cat["prom"].status == "mismatch"
    assert by_cat["prom"].expected_md5 == "bb"
    assert by_cat["prom"].actual_md5 == "WRONG"


def test_verify_missing_in_build() -> None:
    report = BuildReport(out_dir=Path("/tmp"), artifacts={"srom": _art("aa")})
    smdb_game = {
        "srom": _smdb_entry("aa", "srom"),
        "fpga": _smdb_entry("bb", "fpga"),
    }

    results = verify(report, smdb_game)
    by_cat = {r.category: r for r in results}

    assert by_cat["srom"].status == "ok"
    assert by_cat["fpga"].status == "missing_in_build"
    assert by_cat["fpga"].expected_md5 == "bb"
    assert by_cat["fpga"].actual_md5 is None


def test_verify_missing_in_smdb() -> None:
    report = BuildReport(
        out_dir=Path("/tmp"),
        artifacts={"srom": _art("aa"), "fpga": _art("bb")},
    )
    smdb_game = {"srom": _smdb_entry("aa", "srom")}

    results = verify(report, smdb_game)
    by_cat = {r.category: r for r in results}

    assert by_cat["srom"].status == "ok"
    assert by_cat["fpga"].status == "missing_in_smdb"
    assert by_cat["fpga"].expected_md5 is None
    assert by_cat["fpga"].actual_md5 == "bb"
