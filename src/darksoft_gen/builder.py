"""Build the six Darksoft artifacts from a :class:`RomSet`.

This module is a side-effect orchestrator: it writes files under
``out_dir`` and returns a :class:`BuildReport` describing what was
produced and the hashes of each artifact.

Iso-behavior rules preserved from the original ``convert_roms``:
  * ``prom`` concatenates ``p_files`` **then** ``sp_files`` in that order.
  * ``crom0`` interleaves C-ROM pairs 2 bytes at a time.
  * When a category is empty, its output file is not written at all.
  * ``srom`` / ``m1rom`` are raw copies of the source file.

Deliberate deviations:
  * ``out_dir`` is cleared via :func:`shutil.rmtree` (instead of the
    original's recursive glob-remove) — same net effect, simpler code.
  * The ``fpga`` artifact is new (the original tool didn't create it;
    users had to reverse-lookup an MD5 online). Pass ``fpga_bytes=None``
    to opt out.
"""

from __future__ import annotations

import hashlib
import shutil
import zlib
from dataclasses import dataclass
from pathlib import Path

from .interleave import interleave_pairs
from .romset import RomSet


@dataclass(frozen=True)
class BuildArtifact:
    """One generated output file with its hashes."""

    path: Path
    size: int
    sha256: str
    sha1: str
    md5: str
    crc32: str


@dataclass(frozen=True)
class BuildReport:
    """Outcome of a :func:`build` call."""

    out_dir: Path
    artifacts: dict[str, BuildArtifact]


def _hash_bytes(data: bytes) -> tuple[str, str, str, str]:
    return (
        hashlib.sha256(data).hexdigest(),
        hashlib.sha1(data).hexdigest(),
        hashlib.md5(data).hexdigest(),
        f"{zlib.crc32(data) & 0xFFFFFFFF:08x}",
    )


def _write_artifact(out_dir: Path, name: str, data: bytes) -> BuildArtifact:
    path = out_dir / name
    path.write_bytes(data)
    sha256, sha1, md5, crc32 = _hash_bytes(data)
    return BuildArtifact(
        path=path,
        size=len(data),
        sha256=sha256,
        sha1=sha1,
        md5=md5,
        crc32=crc32,
    )


def _read_concat(romset_dir: Path, filenames: list[str]) -> bytes:
    out = bytearray()
    for name in filenames:
        out += (romset_dir / name).read_bytes()
    return bytes(out)


def build(romset: RomSet, out_dir: Path, fpga_bytes: bytes | None) -> BuildReport:
    """Produce the Darksoft artifact set from ``romset``.

    Args:
        romset: Classified ROM files from :func:`scan_directory`.
        out_dir: Destination directory. Cleared if it already exists.
        fpga_bytes: The resolved ``fpga`` file contents (see
            :func:`darksoft_gen.fpga_solver.resolve_fpga`). Pass ``None``
            to skip writing the ``fpga`` artifact.

    Returns:
        A :class:`BuildReport` mapping category names
        (``srom``, ``m1rom``, ``crom0``, ``vroma0``, ``prom``, ``fpga``)
        to :class:`BuildArtifact`. Categories with no source files are
        absent from the mapping.
    """
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    artifacts: dict[str, BuildArtifact] = {}

    if romset.s_rom is not None:
        data = (romset.directory / romset.s_rom).read_bytes()
        artifacts["srom"] = _write_artifact(out_dir, "srom", data)

    if romset.m1_rom is not None:
        data = (romset.directory / romset.m1_rom).read_bytes()
        artifacts["m1rom"] = _write_artifact(out_dir, "m1rom", data)

    if romset.c_files:
        pairs = [romset.directory / name for name in romset.c_files]
        data = interleave_pairs(pairs)
        if data:
            artifacts["crom0"] = _write_artifact(out_dir, "crom0", data)

    if romset.v_files:
        data = _read_concat(romset.directory, romset.v_files)
        artifacts["vroma0"] = _write_artifact(out_dir, "vroma0", data)

    # prom = p_files then sp_files, iso with the original's two-loop append.
    prom_sources = romset.p_files + romset.sp_files
    if prom_sources:
        data = _read_concat(romset.directory, prom_sources)
        artifacts["prom"] = _write_artifact(out_dir, "prom", data)

    if fpga_bytes is not None:
        artifacts["fpga"] = _write_artifact(out_dir, "fpga", fpga_bytes)

    return BuildReport(out_dir=out_dir, artifacts=artifacts)
