"""Rebuild the complete binary snapshot only from digest-verified publisher assets.

Do not publish a partial refresh: all 51 manifest paths must be produced in a
fresh staging directory before a single committed executable is replaced.
Neither source validation nor this audit executes downloaded binaries.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

from security.audit_all_binaries import check_architecture

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "binary_paths.json"
DOWNLOADER = ROOT / ".github/workflows/scripts/download_binaries.py"
TOOLS = ["ffmpeg", "dovi_tool", "mkvtoolnix", "velora", "flux", "yt-dlp", "deno"]


def expected_files():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = [name for group in data.values() for name in group]
    if len(paths) != 51 or len(paths) != len(set(paths)):
        raise ValueError("Expected exactly 51 unique binary paths")
    for name in paths:
        p = PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts or len(p.parts) < 4:
            raise ValueError(f"Unsafe manifest path: {name}")
    return set(paths)


def actual_files(folder):
    return {
        p.relative_to(folder).as_posix()
        for p in folder.rglob("*")
        if p.is_file() and not p.name.endswith(".version")
    }


def verified_refresh():
    expected = expected_files()
    before = MANIFEST.read_bytes()
    spec = importlib.util.spec_from_file_location("verified_binary_downloader", DOWNLOADER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory(prefix="verified-binaries-") as stage_name:
        stage = Path(stage_name)
        downloader = module.BinaryDownloader(base_path=stage)
        downloader.run(only=TOOLS)

        # The existing downloader writes a manifest in the workspace; refuse
        # unexpected changes rather than silently publishing new paths.
        if MANIFEST.read_bytes() != before:
            MANIFEST.write_bytes(before)
            raise ValueError("Downloader modified the pinned 51-path manifest")

        actual = actual_files(stage)
        if actual != expected:
            raise ValueError(
                f"Missing staged executables: {sorted(expected - actual)}; "
                f"unexpected staged files: {sorted(actual - expected)}"
            )

        for rel in sorted(expected):
            check_architecture(stage / rel, rel)
        for tool in TOOLS:
            version_file = stage / f"{tool}.version"
            if not version_file.is_file() or not version_file.read_text().strip():
                raise ValueError(f"No version recorded for {tool}")

        # All publisher digests, paths, architecture and versions have passed
        # before touching any existing executable. Git publishes only on a
        # successful workflow run.
        for rel in sorted(expected):
            source = stage / rel
            dest = ROOT / "binaries" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            temporary = dest.with_name(dest.name + ".verified-tmp")
            shutil.copy2(source, temporary)
            os.replace(temporary, dest)
        for tool in TOOLS:
            source = stage / f"{tool}.version"
            dest = ROOT / "binaries" / f"{tool}.version"
            shutil.copy2(source, dest)

    print(f"STAGED + VERIFIED: {len(expected)} of {len(expected)} release executables")


if __name__ == "__main__":
    verified_refresh()
