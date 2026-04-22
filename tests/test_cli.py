"""Smoke tests for the darksoft-gen CLI."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from darksoft_gen.builder import build
from darksoft_gen.cli import main
from darksoft_gen.romset import scan_directory


def _write_mini_romset(src: Path) -> None:
    (src / "g-s1.rom").write_bytes(b"SROM")
    (src / "g-m1.rom").write_bytes(b"M1ROM!!!")
    (src / "g-c1.rom").write_bytes(b"\x00\x01\x02\x03")
    (src / "g-c2.rom").write_bytes(b"\xA0\xA1\xA2\xA3")
    (src / "g-v1.rom").write_bytes(b"VVVV")
    (src / "g-p1.rom").write_bytes(b"PPPP")


def _expected_md5s(src: Path, fpga_bytes: bytes, out_dir: Path) -> dict[str, str]:
    """Build once to capture the artifact MD5s that the CLI will produce.

    ``scan_directory`` preserves filesystem iteration order, which is
    non-deterministic across platforms — so the crom0 MD5 depends on which
    C-ROM comes first. We run a throwaway build to observe the real MD5s,
    then throw the output away so the CLI can rebuild cleanly.
    """
    romset = scan_directory(src)
    report = build(romset, out_dir, fpga_bytes=fpga_bytes)
    md5s = {cat: art.md5 for cat, art in report.artifacts.items()}
    shutil.rmtree(out_dir)
    return md5s


def _write_stub_smdb(smdb_path: Path, game: str, md5_by_cat: dict[str, str]) -> None:
    lines = []
    for cat, md5 in md5_by_cat.items():
        lines.append(
            "\t".join(
                [
                    "0" * 64,  # sha256 not checked
                    f"Darksoft Neo Geo/games/{game}/{cat}",
                    "0" * 40,  # sha1 not checked
                    md5,
                    "00000000",
                ]
            )
        )
    smdb_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_cli_happy_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = tmp_path / "mygame"
    src.mkdir()
    _write_mini_romset(src)
    # Known-resolvable fpga key: md5("13") = c51c...
    md5s = _expected_md5s(src, fpga_bytes=b"13", out_dir=tmp_path / "_probe")

    smdb_path = tmp_path / "smdb.txt"
    _write_stub_smdb(smdb_path, game="mygame", md5_by_cat=md5s)

    exit_code = main(["--dir", str(src), "--smdb", str(smdb_path)])

    assert exit_code == 0
    out_dir = src / "export"
    assert (out_dir / "srom").exists()
    assert (out_dir / "fpga").read_bytes() == b"13"

    captured = capsys.readouterr()
    assert "Verification against SMDB" in captured.out
    assert captured.out.count("OK ") == 6


def test_cli_verify_failure_exit_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "mygame"
    src.mkdir()
    _write_mini_romset(src)
    md5s = _expected_md5s(src, fpga_bytes=b"13", out_dir=tmp_path / "_probe")
    # Corrupt the expected srom MD5 in the SMDB -> mismatch.
    md5s["srom"] = "deadbeef" * 4

    smdb_path = tmp_path / "smdb.txt"
    _write_stub_smdb(smdb_path, game="mygame", md5_by_cat=md5s)

    exit_code = main(["--dir", str(src), "--smdb", str(smdb_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "MISMATCH" in captured.out


def test_cli_unknown_game_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "not_in_smdb"
    src.mkdir()
    (src / "x-s1.rom").write_bytes(b"x")

    smdb_path = tmp_path / "smdb.txt"
    smdb_path.write_text("", encoding="utf-8")

    exit_code = main(["--dir", str(src), "--smdb", str(smdb_path)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "not found in SMDB" in err


def test_cli_no_verify_no_fpga_skips_smdb(tmp_path: Path) -> None:
    src = tmp_path / "any_name"
    src.mkdir()
    (src / "x-s1.rom").write_bytes(b"x")

    # No SMDB passed and flags disable both SMDB-dependent steps -> should succeed.
    exit_code = main(
        ["--dir", str(src), "--no-verify", "--no-fpga", "--smdb", "/nonexistent"]
    )

    assert exit_code == 0
    assert (src / "export" / "srom").read_bytes() == b"x"
    assert not (src / "export" / "fpga").exists()
