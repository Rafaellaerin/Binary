# Binary

Pre-built third-party binaries used by the AstraeLabs tools: FFmpeg/FFprobe, dovi_tool, MKVToolNix, Velora, Flux, yt-dlp and Deno.

## Layout

- `binaries/<os>/<arch>/<tool>/` – executables (`windows`, `linux`, `darwin` × `x64`, `arm64`, ...); FFmpeg is stored with Git LFS.
- `binaries/<tool>.version` – version of each tool currently committed.
- `binary_paths.json` – manifest of every published binary path.

## Updating

A weekly workflow (`Update binaries`) picks up new upstream versions automatically; it can also be started by hand from **Actions**. Every download is checked against a pinned SHA-256 or the digest published by the upstream release, otherwise nothing is committed. See [security/README.md](security/README.md) for the policy and how to approve a new release.

## Integrity and provenance

- `security/trusted_source_hashes.json` pins SHA-256 for 39 versioned publisher release assets, including yt-dlp 2026.10.26. Moving release tags are checked against publisher-provided asset digests at download time.
- `security/SHA256SUMS.txt` records the individual SHA-256 of all 51 committed executables. After cloning, run `git lfs pull` and `python security/check_binary_inventory.py --check` to detect local changes.
- The complete verified refresh on 2026-11-01 re-downloaded every expected path, validated source digests and executable formats, and compared immutable release contents before committing. See `security/README.md` and GitHub Actions history.

SHA-256 equality confirms byte identity to a reference, not absence of malware. FFmpeg executables are builds distributed by BtbN/FFmpeg-Builds (not binaries published by the FFmpeg core project).

## License

See [LICENSE](LICENSE).
