"""Darksoft SMDB parser.

The SMDB (``Darksoft Neo Geo SMDB.txt``) ships one record per tab-separated
line:

    <sha256>\\t<path>\\t<sha1>\\t<md5>\\t<crc32>

where ``<path>`` is the virtual path inside the Darksoft pack, of the form::

    Darksoft Neo Geo/games/<game>/<category>

with ``<category>`` one of ``srom``, ``m1rom``, ``crom0``, ``vroma0``,
``prom``, ``fpga``. Lines that don't match this schema are silently ignored
(the SMDB also contains top-level files like ``/bios/...`` that we don't
consume here).
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import as_file, files
from pathlib import Path

_PATH_PREFIX = "Darksoft Neo Geo/games/"
_CATEGORIES = frozenset({"srom", "m1rom", "crom0", "vroma0", "prom", "fpga"})


def bundled_smdb_path() -> Path:
    """Path to the SMDB shipped inside the package.

    The SMDB is installed under ``darksoft_gen/data/smdb.txt``. For editable
    installs this resolves to the source tree; for wheel installs it
    resolves to the extracted package dir.
    """
    resource = files("darksoft_gen").joinpath("data/smdb.txt")
    with as_file(resource) as p:
        return Path(p)


@dataclass(frozen=True)
class SmdbEntry:
    """One hash record from the SMDB."""

    sha256: str
    path: str
    sha1: str
    md5: str
    crc32: str


def parse_smdb(path: Path) -> dict[str, dict[str, SmdbEntry]]:
    """Parse an SMDB file into a ``{game: {category: SmdbEntry}}`` mapping.

    Args:
        path: Path to the ``Darksoft Neo Geo SMDB.txt`` file.

    Returns:
        A nested dict keyed by game short-name then by category. Lines that
        don't match the ``Darksoft Neo Geo/games/<game>/<category>`` schema
        — or don't have 5 tab-separated fields — are skipped.
    """
    result: dict[str, dict[str, SmdbEntry]] = {}

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) != 5:
                continue

            sha256, vpath, sha1, md5, crc32 = parts

            if not vpath.startswith(_PATH_PREFIX):
                continue

            tail = vpath[len(_PATH_PREFIX):]
            segments = tail.split("/")
            if len(segments) != 2:
                continue

            game, category = segments
            if category not in _CATEGORIES:
                continue

            result.setdefault(game, {})[category] = SmdbEntry(
                sha256=sha256,
                path=vpath,
                sha1=sha1,
                md5=md5,
                crc32=crc32,
            )

    return result
