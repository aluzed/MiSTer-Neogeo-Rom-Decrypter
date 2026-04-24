"""Tests for the SMDB parser."""

from __future__ import annotations

from pathlib import Path

from darksoft_gen.smdb import SmdbEntry, bundled_smdb_path, parse_smdb


def test_parse_minimal(tmp_path: Path) -> None:
    smdb = tmp_path / "mini.smdb"
    smdb.write_text(
        "\t".join(["aa" * 32, "Darksoft Neo Geo/games/foo/fpga", "11" * 20, "22" * 16, "deadbeef"])
        + "\n"
        + "\t".join(["bb" * 32, "Darksoft Neo Geo/games/foo/srom", "33" * 20, "44" * 16, "cafebabe"])
        + "\n"
        + "\t".join(["cc" * 32, "Darksoft Neo Geo/games/bar/prom", "55" * 20, "66" * 16, "12345678"])
        + "\n",
        encoding="utf-8",
    )

    entries = parse_smdb(smdb)

    assert set(entries.keys()) == {"foo", "bar"}
    assert set(entries["foo"].keys()) == {"fpga", "srom"}
    assert entries["foo"]["fpga"] == SmdbEntry(
        sha256="aa" * 32,
        path="Darksoft Neo Geo/games/foo/fpga",
        sha1="11" * 20,
        md5="22" * 16,
        crc32="deadbeef",
    )
    assert entries["bar"]["prom"].crc32 == "12345678"


def test_parse_skips_malformed_and_non_games(tmp_path: Path) -> None:
    smdb = tmp_path / "mixed.smdb"
    smdb.write_text(
        "\n"  # blank line
        + "garbage without tabs\n"  # wrong field count
        + "\t".join(["aa" * 32, "Darksoft Neo Geo/bios/something", "11" * 20, "22" * 16, "de"]) + "\n"  # non-/games/ path
        + "\t".join(["bb" * 32, "Darksoft Neo Geo/games/foo/unknown_cat", "33" * 20, "44" * 16, "ca"]) + "\n"  # bad category
        + "\t".join(["cc" * 32, "Darksoft Neo Geo/games/ok/fpga", "55" * 20, "66" * 16, "12"]) + "\n"  # valid
        + "\t".join(["dd" * 32, "Darksoft Neo Geo/games/too/deep/path/fpga", "77" * 20, "88" * 16, "ef"]) + "\n",  # too many segments
        encoding="utf-8",
    )

    entries = parse_smdb(smdb)

    assert set(entries.keys()) == {"ok"}
    assert set(entries["ok"].keys()) == {"fpga"}


def test_parse_real_smdb_smoke() -> None:
    smdb_path = bundled_smdb_path()
    assert smdb_path.exists(), f"bundled SMDB missing: {smdb_path}"

    entries = parse_smdb(smdb_path)

    assert "2020bb" in entries
    game = entries["2020bb"]
    assert set(game.keys()) == {"srom", "m1rom", "crom0", "vroma0", "prom", "fpga"}
    assert game["fpga"].md5 == "c51ce410c124a10e0db5e4b97fc2af39"
    assert game["crom0"].sha256 == (
        "100e92506f6631efb9f19a77f46aae3d679b2c9529a7977227050d891d9dbf07"
    )
