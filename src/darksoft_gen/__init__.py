"""Convert decrypted NeoRageX NeoGeo romsets into the Darksoft format."""

from .builder import BuildArtifact, BuildReport, build
from .fpga_solver import resolve_fpga
from .romset import RomSet, scan_directory
from .smdb import SmdbEntry, bundled_smdb_path, parse_smdb
from .verify import VerifyResult, verify

__version__ = "0.1.0"

__all__ = [
    "BuildArtifact",
    "BuildReport",
    "RomSet",
    "SmdbEntry",
    "VerifyResult",
    "__version__",
    "build",
    "bundled_smdb_path",
    "parse_smdb",
    "resolve_fpga",
    "scan_directory",
    "verify",
]
