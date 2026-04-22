"""Command-line entry point: ``darksoft-gen``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .builder import build
from .fpga_solver import resolve_fpga
from .romset import scan_directory
from .smdb import SmdbEntry, bundled_smdb_path, parse_smdb
from .verify import VerifyResult, verify


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="darksoft-gen",
        description="Convert a MAME/NeoRageX NeoGeo romset to the Darksoft format.",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="Source directory containing the romset (default: current directory).",
    )
    parser.add_argument(
        "--game",
        type=str,
        default=None,
        help="Game short-name (e.g. '2020bb'). Defaults to the source directory name.",
    )
    parser.add_argument(
        "--smdb",
        type=Path,
        default=None,
        help="Path to an SMDB file. Defaults to the version bundled with the package.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for generated files. Defaults to <dir>/export.",
    )
    parser.add_argument(
        "--no-fpga",
        action="store_true",
        help="Skip writing the fpga file.",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip SMDB verification of generated artifacts.",
    )
    return parser.parse_args(argv)


def _print_build_summary(artifacts: dict) -> None:
    print("Generated artifacts:")
    for cat in ("srom", "m1rom", "crom0", "vroma0", "prom", "fpga"):
        art = artifacts.get(cat)
        if art is None:
            continue
        print(f"  {cat:7s} {art.size:>10d} bytes  md5={art.md5}")


def _print_verify_report(results: list[VerifyResult]) -> bool:
    print("Verification against SMDB:")
    all_ok = True
    for r in results:
        if r.status == "ok":
            print(f"  OK       {r.category:7s} md5={r.actual_md5}")
            continue
        all_ok = False
        if r.status == "mismatch":
            print(
                f"  MISMATCH {r.category:7s} "
                f"expected={r.expected_md5} actual={r.actual_md5}"
            )
        elif r.status == "missing_in_build":
            print(f"  MISSING  {r.category:7s} expected={r.expected_md5} (not generated)")
        elif r.status == "missing_in_smdb":
            print(f"  UNKNOWN  {r.category:7s} actual={r.actual_md5} (no SMDB entry)")
    return all_ok


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``darksoft-gen`` console script.

    Returns the process exit code: 0 on success, 1 on verification
    failure or any anticipated error.
    """
    args = _parse_args(argv)

    source_dir: Path = args.dir.resolve()
    if not source_dir.is_dir():
        print(f"error: source directory does not exist: {source_dir}", file=sys.stderr)
        return 1

    game_name: str = args.game or source_dir.name
    out_dir: Path = args.out if args.out is not None else source_dir / "export"

    smdb_entries: dict[str, dict[str, SmdbEntry]] | None = None
    game_entry: dict[str, SmdbEntry] | None = None

    need_smdb = not (args.no_fpga and args.no_verify)
    if need_smdb:
        smdb_path = args.smdb if args.smdb is not None else bundled_smdb_path()
        smdb_entries = parse_smdb(smdb_path)
        game_entry = smdb_entries.get(game_name)
        if game_entry is None:
            print(
                f"error: game '{game_name}' not found in SMDB ({smdb_path}). "
                "Override with --game <name> or --no-verify --no-fpga.",
                file=sys.stderr,
            )
            return 1

    fpga_bytes: bytes | None = None
    if not args.no_fpga:
        assert game_entry is not None  # need_smdb was true
        fpga_smdb = game_entry.get("fpga")
        if fpga_smdb is None:
            print(
                f"warning: SMDB has no fpga entry for '{game_name}', skipping fpga file.",
                file=sys.stderr,
            )
        else:
            fpga_bytes = resolve_fpga(fpga_smdb.md5)
            if fpga_bytes is None:
                print(
                    f"warning: no fpga key in [0, 255] matches MD5 {fpga_smdb.md5}; "
                    "fpga file will not be written.",
                    file=sys.stderr,
                )

    print(f"Scanning: {source_dir}")
    romset = scan_directory(source_dir)
    print(f"Building for game '{game_name}' into: {out_dir}")
    report = build(romset, out_dir, fpga_bytes)
    _print_build_summary(report.artifacts)

    if args.no_verify:
        return 0

    assert game_entry is not None
    results = verify(report, game_entry)
    ok = _print_verify_report(results)
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
