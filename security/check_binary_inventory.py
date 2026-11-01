"""Write or verify SHA-256 checksums for every committed binary payload.

The checksum manifest is a local snapshot, not an independent vendor signature.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BINARIES = ROOT / "binaries"
OUTPUT = ROOT / "security" / "SHA256SUMS.txt"


def calculate():
    mapping = json.loads((ROOT / "binary_paths.json").read_text(encoding="utf-8"))
    paths = [entry for entries in mapping.values() for entry in entries]
    if len(paths) != 51 or len(paths) != len(set(paths)):
        raise ValueError("Manifest must contain exactly 51 unique paths")
    expected = set(paths)
    actual = {
        f.relative_to(BINARIES).as_posix()
        for f in BINARIES.rglob("*")
        if f.is_file() and not f.name.endswith(".version")
    }
    if expected != actual:
        raise ValueError(
            f"Manifest mismatch: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )

    lines = []
    for relative in sorted(paths):
        p = PurePosixPath(relative)
        if p.is_absolute() or ".." in p.parts or len(p.parts) < 4:
            raise ValueError(f"Unsafe manifest path: {relative}")
        file = BINARIES / relative
        if not file.is_file() or file.is_symlink():
            raise ValueError(f"Not a regular file: {relative}")
        h = hashlib.sha256()
        with file.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
        lines.append(f"{h.hexdigest()}  binaries/{relative}\n")
    return "".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    contents = calculate()
    if args.write:
        OUTPUT.write_text(contents, encoding="utf-8")
        print("Wrote verified 51-file SHA-256 snapshot")
    else:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != contents:
            raise SystemExit("SHA-256 snapshot missing or does not match tracked binaries")
        print("PASS: 51 tracked binary SHA-256 values match the snapshot")
