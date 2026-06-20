# Legacy of InFest — Known Gaps

## [GAP-001] Pillow version pin adjusted for Python 3.14 compatibility

- **File:** `requirements.txt`
- **Phase:** 0
- **Reason:** The documented pin `Pillow~=10.4` (from `23_DATA_SCHEMAS.md` §9) does not provide prebuilt wheels for Python 3.14. Pillow 10.4 fails to build from source on Windows because the `zlib` C dependency is not present in the build environment. Changed to `Pillow~=12.2`, which provides prebuilt `cp314` wheels.
- **Resolution plan:** When `23_DATA_SCHEMAS.md` §9 is next revised, update the pin table to reflect the working Python 3.14 version. The `~=12.2` pin is functionally equivalent (compatible-release constraint, same semantics).

<!--
Use this exact format for each future entry:

## [GAP-XXX] <short title>

- **File:** `src/path/to/file.py`
- **Phase:** <roadmap phase number where this was deferred>
- **Reason:** <why this is intentionally incomplete>
- **Resolution plan:** <when/how this gets resolved, or "N/A — out of scope">
-->