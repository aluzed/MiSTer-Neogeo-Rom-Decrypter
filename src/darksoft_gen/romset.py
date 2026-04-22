"""Romset detection: discover ROM files in a directory and classify them.

Replicates the file-detection logic of the original ``generator.py`` —
specifically the two-loop scan inside ``convert_roms``, with the same regex
patterns applied in the same order.

Supported naming conventions:
  * MAME-style:     ``<name>-s1.rom``, ``<name>_p1.bin``, ``<name>-c2.rom`` ...
  * NeoRageX-style: ``<name>.s1``, ``<name>.p1``, ``<name>.c2`` ...

Iso-behavior quirks preserved from the original (do not "fix" these without
coordination — see project memory "iso-behavior"):

  * Regex dots are unescaped (``.p\\d$`` not ``\\.p\\d$``): the ``.`` matches
    any character. In practice harmless on real romsets except for one case:
    on a NeoRageX-style file ``foo.sp1``, the P-regex ``.p\\d$`` also matches
    (the ``.`` consumes the ``s``), so the file ends up in BOTH ``p_files``
    and ``sp_files``. The downstream builder concatenates ``p_files`` then
    ``sp_files`` for the prom, so SP bytes are written twice in that setup.
    The MAME-style equivalent does not trigger it because the P2 anchor
    ``[-_]p\\d.(rom|bin)$`` requires a ``[-_]`` prefix that ``foo-sp1.rom``
    doesn't provide.

  * Anchors are asymmetric: the S-rom MAME pattern has no ``$`` anchor
    (``[-_]s1.(rom|bin)``), all others do. Preserved verbatim.

  * Directory scan is single-level (equivalent to the original
    ``for (...) in walk: break``). Subdirectories are ignored.

  * File order is filesystem order (no ``sorted()``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Regex patterns — copied verbatim from generator.py. Do not "clean up"
# (unescaped dots, missing anchors) without an explicit behavior-change decision.
_S_PATTERNS = (re.compile(r".s1$"), re.compile(r"[-_]s1.(rom|bin)"))
_M1_PATTERNS = (re.compile(r".m1$"), re.compile(r"[-_]m1.(rom|bin)$"))
_P_PATTERNS = (re.compile(r".p\d$"), re.compile(r"[-_]p\d.(rom|bin)$"))
_C_PATTERNS = (re.compile(r"[-_]c\d.(rom|bin)$"), re.compile(r".c\d$"))
_V_PATTERNS = (re.compile(r".v\d$"), re.compile(r"[-_]v\d.(rom|bin)$"))
_SP_PATTERNS = (re.compile(r".sp\d$"), re.compile(r"[-_]sp\d.(rom|bin)$"))


@dataclass
class RomSet:
    """Classified ROM files discovered in a directory.

    Attributes:
        directory: The source directory that was scanned.
        s_rom: Filename of the S-rom, or ``None`` if none found.
        m1_rom: Filename of the M1-rom, or ``None`` if none found.
        p_files: P-rom filenames in filesystem-discovery order.
        c_files: C-rom filenames in filesystem-discovery order.
        v_files: V-rom filenames in filesystem-discovery order.
        sp_files: SP-rom filenames in filesystem-discovery order. Stored
            separately from ``p_files`` for clarity; the builder is
            responsible for concatenating ``p_files`` then ``sp_files``
            when assembling the prom (matching the original's behavior).
    """

    directory: Path
    s_rom: str | None = None
    m1_rom: str | None = None
    p_files: list[str] = field(default_factory=list)
    c_files: list[str] = field(default_factory=list)
    v_files: list[str] = field(default_factory=list)
    sp_files: list[str] = field(default_factory=list)


def _matches_any(filename: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(p.search(filename) for p in patterns)


def scan_directory(path: Path) -> RomSet:
    """Scan a directory (non-recursively) and classify ROM files.

    Reproduces the two-loop scan from the original ``convert_roms``:
      1. First loop assigns ``s_rom`` / ``m1_rom`` (last match wins) and
         appends to ``p_files`` / ``c_files`` / ``v_files``.
      2. Second loop appends SP files to ``sp_files``.

    Args:
        path: Directory to scan. Only its immediate children are inspected.

    Returns:
        A populated :class:`RomSet`. Missing categories are empty lists /
        ``None``.
    """
    romset = RomSet(directory=path)

    filenames: list[str] = []
    for entry in path.iterdir():
        if entry.is_file():
            filenames.append(entry.name)

    # First pass: S / M1 / P / C / V
    for filename in filenames:
        if _matches_any(filename, _S_PATTERNS):
            romset.s_rom = filename

        if _matches_any(filename, _M1_PATTERNS):
            romset.m1_rom = filename

        if _matches_any(filename, _P_PATTERNS):
            romset.p_files.append(filename)

        if _matches_any(filename, _C_PATTERNS):
            romset.c_files.append(filename)

        if _matches_any(filename, _V_PATTERNS):
            romset.v_files.append(filename)

    # Second pass: SP (separate, as in the original)
    for filename in filenames:
        if _matches_any(filename, _SP_PATTERNS):
            romset.sp_files.append(filename)

    return romset
