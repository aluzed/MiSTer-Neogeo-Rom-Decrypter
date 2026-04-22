"""Verify a :class:`BuildReport` against an SMDB game entry.

Compares MD5 of each built artifact to the expected MD5 declared in the
Darksoft SMDB. MD5 is chosen because ROM databases (no-intro, Redump,
and most ROM management tools) commonly index by MD5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .builder import BuildReport
from .smdb import SmdbEntry

VerifyStatus = Literal["ok", "mismatch", "missing_in_build", "missing_in_smdb"]


@dataclass(frozen=True)
class VerifyResult:
    """Outcome for one category after verification.

    ``missing_in_build`` means the SMDB declares the category but the
    build didn't produce it (e.g. no S-ROM source files in the romset).
    ``missing_in_smdb`` means the build produced a file whose category
    doesn't appear in the SMDB entry for this game — unexpected unless
    the SMDB is truncated.
    """

    category: str
    status: VerifyStatus
    expected_md5: str | None
    actual_md5: str | None


def verify(
    report: BuildReport, smdb_game: dict[str, SmdbEntry]
) -> list[VerifyResult]:
    """Compare every category mentioned by either side.

    Args:
        report: The build output.
        smdb_game: The SMDB mapping for one game (e.g.
            ``parse_smdb(...)["2020bb"]``).

    Returns:
        One :class:`VerifyResult` per category across the union of
        ``report.artifacts`` and ``smdb_game``.
    """
    categories = sorted(set(report.artifacts) | set(smdb_game))
    results: list[VerifyResult] = []

    for cat in categories:
        artifact = report.artifacts.get(cat)
        smdb_entry = smdb_game.get(cat)

        if artifact is None:
            results.append(
                VerifyResult(
                    category=cat,
                    status="missing_in_build",
                    expected_md5=smdb_entry.md5 if smdb_entry else None,
                    actual_md5=None,
                )
            )
            continue

        if smdb_entry is None:
            results.append(
                VerifyResult(
                    category=cat,
                    status="missing_in_smdb",
                    expected_md5=None,
                    actual_md5=artifact.md5,
                )
            )
            continue

        status: VerifyStatus = "ok" if artifact.md5 == smdb_entry.md5 else "mismatch"
        results.append(
            VerifyResult(
                category=cat,
                status=status,
                expected_md5=smdb_entry.md5,
                actual_md5=artifact.md5,
            )
        )

    return results
