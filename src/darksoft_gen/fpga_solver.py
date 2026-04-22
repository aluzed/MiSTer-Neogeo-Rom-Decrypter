"""Resolve the bytes of the Darksoft ``fpga`` file from its expected MD5.

An ``fpga`` file is simply the ASCII decimal representation of a small
integer — the "starting index key". For example the content ``"13"`` has
MD5 ``c51ce410c124a10e0db5e4b97fc2af39``.

Historically users reverse-looked up the MD5 online (see the project's
README). This module replaces that step with a local lookup built once at
import time over the range ``[0, 255]``, which covers every key observed
in the Darksoft SMDB.
"""

from __future__ import annotations

import hashlib

_MAX_KEY = 255

_MD5_TO_BYTES: dict[str, bytes] = {}
for _n in range(_MAX_KEY + 1):
    _content = str(_n).encode("ascii")
    _MD5_TO_BYTES[hashlib.md5(_content).hexdigest()] = _content
del _n, _content


def resolve_fpga(target_md5: str) -> bytes | None:
    """Return the fpga file bytes whose MD5 equals ``target_md5``.

    Args:
        target_md5: Lowercase hex MD5 digest (as stored in the SMDB).

    Returns:
        The ASCII bytes to write into the ``fpga`` file, or ``None`` if no
        integer in ``[0, 255]`` hashes to ``target_md5`` (the current
        assumed search space).
    """
    return _MD5_TO_BYTES.get(target_md5.lower())
