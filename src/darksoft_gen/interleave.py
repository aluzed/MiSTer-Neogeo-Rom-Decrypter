"""Pure interleaving primitives for Darksoft CROM generation.

The Darksoft CROM format expects pairs of individual C-ROM files to be
interleaved 2 bytes at a time (c1/c2, c3/c4, ...) and the resulting
pair-blocks concatenated.
See the original `generator.py` (functions `join_crom0` and `split_per2`) for
the historical implementation this module reproduces behavior-identically.
"""

from __future__ import annotations

from pathlib import Path

_CHUNK = 2


def interleave_pair(file_a: Path, file_b: Path) -> bytes:
    """Interleave two files 2 bytes at a time.

    Reads 2 bytes from ``file_a`` then 2 bytes from ``file_b`` in a loop,
    appending to the output, until either file reaches EOF. If either read
    returns fewer than 2 bytes, iteration stops without writing that round's
    partial chunks — matching the behavior of the original ``join_crom0``.

    Args:
        file_a: First file of the pair (even-indexed C-ROM).
        file_b: Second file of the pair (odd-indexed C-ROM).

    Returns:
        The interleaved bytes: ``a[0:2] + b[0:2] + a[2:4] + b[2:4] + ...``.
    """
    out = bytearray()
    with file_a.open("rb") as fa, file_b.open("rb") as fb:
        while True:
            chunk_a = fa.read(_CHUNK)
            chunk_b = fb.read(_CHUNK)
            if len(chunk_a) < _CHUNK or len(chunk_b) < _CHUNK:
                break
            out += chunk_a
            out += chunk_b
    return bytes(out)


def interleave_pairs(files: list[Path]) -> bytes:
    """Interleave a list of files by consecutive pairs and concatenate.

    Files are paired in list order: ``(files[0], files[1])``,
    ``(files[2], files[3])``, and so on. Each pair is fed through
    :func:`interleave_pair`, and the pair outputs are concatenated.

    Iso-behavior with the original ``split_per2``:
      * An odd-length list silently drops the trailing unpaired file.
      * An empty list returns ``b""``.
      * A single-file list returns ``b""`` (no pair formed).

    Args:
        files: Ordered list of file paths to pair and interleave.

    Returns:
        The concatenated interleaved output for all formed pairs.
    """
    out = bytearray()
    for i in range(0, len(files) - 1, 2):
        out += interleave_pair(files[i], files[i + 1])
    return bytes(out)
