# Darksoft Neogeo Rom generator for MiSTer-FPGA by Aluzed

Convert a **decrypted NeoRageX** NeoGeo romset into the Darksoft format
expected by the MiSTer FPGA NeoGeo core.

Originally written by **Aluzed** in 2020 as a single-file script
(`generator.py`). This repository now ships a packaged CLI, `darksoft-gen`,
that produces bit-identical output files *and* auto-resolves the `fpga` key
plus verifies every artifact against the Darksoft SMDB.

## Install

Requires Python 3.10 or newer.

With [pipx](https://pypa.github.io/pipx/) (recommended — isolates deps):

```
pipx install git+https://github.com/aluzed/MiSTer-Neogeo-Rom-Decrypter
```

Or with [uv](https://docs.astral.sh/uv/):

```
uv tool install git+https://github.com/aluzed/MiSTer-Neogeo-Rom-Decrypter
```

Or from a local clone:

```
git clone https://github.com/aluzed/MiSTer-Neogeo-Rom-Decrypter
pipx install ./MiSTer-Neogeo-Rom-Decrypter
```

## Quickstart

1. Unzip a decrypted NeoRageX romset into a folder named after the Darksoft
   short-name of the game (e.g. `2020bb/`, `mslug/`, `aof3/` — see
   `romset.sample.xml` for the full list).
2. `cd` into that folder.
3. Run `darksoft-gen`.

```
cd 2020bb
darksoft-gen
```

Output lands in `./export/` and contains the six files the Darksoft flash cart
expects: `srom`, `m1rom`, `crom0`, `vroma0`, `prom`, `fpga`. Copy the directory
(renamed to the game short-name) to your MiSTer SD card under
`NeoGeo/games/<short-name>/`, and add the corresponding line from
`romset.sample.xml` to your `romset.xml`.

### Sample session

```
$ cd 2020bb
$ darksoft-gen
Scanning: /home/you/neogeo/2020bb
Building for game '2020bb' into: /home/you/neogeo/2020bb/export
Generated artifacts:
  srom          131072 bytes  md5=455d71dffa67694d9ae7629e77ea37c6
  m1rom         131072 bytes  md5=293ea5de05ef9d43264bd676aed68711
  crom0        8388608 bytes  md5=b30cd4e6b0bb0732e1b7b8f70105cf7a
  vroma0       2097152 bytes  md5=38f3a1e7e6c2bc6b46103e3e3c5a20de
  prom         2097152 bytes  md5=b056f384deb2fb20af12dd0a56246bf6
  fpga               2 bytes  md5=c51ce410c124a10e0db5e4b97fc2af39
Verification against SMDB:
  OK       srom    md5=455d71dffa67694d9ae7629e77ea37c6
  OK       m1rom   md5=293ea5de05ef9d43264bd676aed68711
  OK       crom0   md5=b30cd4e6b0bb0732e1b7b8f70105cf7a
  OK       vroma0  md5=38f3a1e7e6c2bc6b46103e3e3c5a20de
  OK       prom    md5=b056f384deb2fb20af12dd0a56246bf6
  OK       fpga    md5=c51ce410c124a10e0db5e4b97fc2af39
```

Exit code is `0` when every artifact matches the SMDB, `1` otherwise.

## What's new vs. the 2020 script

* **Auto-resolved `fpga` file.** The `fpga` file is an ASCII decimal key
  (e.g. `b"13"`) whose MD5 is declared in the Darksoft SMDB. The original
  required users to reverse-lookup that MD5 on an external website. The CLI
  now brute-forces the `[0, 255]` search space locally and writes the file
  for you. Use `--no-fpga` to opt out.
* **Post-build verification.** Every generated artifact is MD5-compared
  against the bundled `Darksoft Neo Geo SMDB.txt`. A mismatch exits non-zero
  — turning the tool into a test bench: if the hashes match but a game is
  broken in-core, it's a core bug rather than a conversion bug. Use
  `--no-verify` to opt out.
* **Proper CLI.** Argument parsing via `argparse`; no more editing
  `sys.argv[1]` in the script or dropping `generator.py` inside the romset
  folder.
* **Installable package.** `pipx install ...` instead of copying a script.
  The SMDB is bundled inside the wheel.

## Options

```
darksoft-gen [--dir PATH] [--game NAME] [--smdb PATH] [--out PATH]
             [--no-fpga] [--no-verify]
```

| Flag          | Default                        | Meaning                                                         |
|---------------|--------------------------------|-----------------------------------------------------------------|
| `--dir`       | current working directory      | Source folder holding the MAME / NeoRageX romset.               |
| `--game`      | basename of `--dir`            | Darksoft short-name, used for SMDB lookup and `fpga` resolution.|
| `--smdb`      | bundled SMDB                   | Override to use a newer or patched SMDB file.                   |
| `--out`       | `<dir>/export`                 | Destination for the six generated artifacts.                    |
| `--no-fpga`   | off                            | Skip writing the `fpga` file.                                   |
| `--no-verify` | off                            | Skip the SMDB comparison step.                                  |

Detected ROM filename conventions (from the original 2020 regex):

* NeoRageX: `<game>.s1`, `<game>.p1`, `<game>.c2`, ... — **tested, known
  to work.**
* MAME:     `<game>-s1.rom`, `<game>_p1.bin`, `<game>-c2.rom`, ... — the
  regex also matches this layout, but the MAME → Darksoft path has not
  been validated end-to-end. Use at your own risk.

## As a library

The package is importable too, in case you want to plug pieces into another
tool:

```python
from pathlib import Path
from darksoft_gen import (
    scan_directory, build, verify,
    parse_smdb, bundled_smdb_path, resolve_fpga,
)

romset = scan_directory(Path("./2020bb"))
entries = parse_smdb(bundled_smdb_path())
fpga = resolve_fpga(entries["2020bb"]["fpga"].md5)
report = build(romset, Path("./2020bb/export"), fpga_bytes=fpga)
for result in verify(report, entries["2020bb"]):
    print(result)
```

## Caveats

Not 100% of the Darksoft romset is playable yet — some games still don't
boot even with correctly-hashed artifacts. Those are core-side issues
rather than conversion issues (the verification step makes that
distinction explicit).

## Result

![Me playing](https://raw.githubusercontent.com/aluzed/MiSTer-Neogeo-Rom-Decrypter/master/preview.jpg)
