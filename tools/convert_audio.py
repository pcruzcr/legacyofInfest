#!/usr/bin/env python3
"""
Convert WAV audio files to OGG Vorbis for smaller asset size.
Requires: ffmpeg (system install) or pydub + ffmpeg.

Usage:
    python tools/convert_audio.py                          # convert all WAV files in assets/
    python tools/convert_audio.py --check                  # verify all existing WAV files
    python tools/convert_audio.py --input path/to/file.wav # convert a single file
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def find_ffmpeg() -> str | None:
    for candidate in ("ffmpeg", "ffmpeg.exe"):
        try:
            subprocess.run([candidate, "-version"], capture_output=True, check=False)
            return candidate
        except FileNotFoundError:
            continue
    return None


def convert_wav_to_ogg(wav_path: Path, ffmpeg: str, dry_run: bool = False) -> bool:
    ogg_path = wav_path.with_suffix(".ogg")
    if ogg_path.exists():
        return True
    if dry_run:
        print(f"  Would convert: {wav_path} -> {ogg_path}")
        return True
    result = subprocess.run(
        [ffmpeg, "-y", "-i", str(wav_path), "-codec:a", "libvorbis",
         "-qscale:a", "3", str(ogg_path)],
        capture_output=True, check=False,
    )
    if result.returncode != 0:
        print(f"  FAILED: {wav_path.name} ({result.stderr.decode(errors='ignore')[:80]})")
        return False
    size_before = wav_path.stat().st_size
    size_after = ogg_path.stat().st_size
    ratio = size_after / size_before if size_before else 0
    print(f"  OK: {wav_path.name}  {size_before//1024}KB -> {size_after//1024}KB ({ratio:.0%})")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert WAV audio to OGG Vorbis")
    parser.add_argument("--input", type=str, help="Single WAV file to convert")
    parser.add_argument("--check", action="store_true", help="Check for unconverted WAV files")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")
    args = parser.parse_args()

    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        print("ERROR: ffmpeg not found. Install ffmpeg (system package or PATH).")
        return 1

    if args.input:
        wav_path = Path(args.input)
        if not wav_path.exists() or wav_path.suffix.lower() != ".wav":
            print(f"ERROR: {args.input} is not a valid WAV file")
            return 1
        ok = convert_wav_to_ogg(wav_path, ffmpeg, args.dry_run)
        return 0 if ok else 1

    assets_dir = Path("assets")
    wav_files = sorted(assets_dir.rglob("*.wav"))
    if not wav_files:
        print(f"No WAV files found under {assets_dir}/")
        return 0

    missing_ogg = [f for f in wav_files if not f.with_suffix(".ogg").exists()]

    if args.check:
        if missing_ogg:
            print(f"Unconverted WAV files ({len(missing_ogg)}):")
            for f in missing_ogg:
                print(f"  {f.relative_to(assets_dir)}")
        else:
            print(f"All {len(wav_files)} WAV files have OGG counterparts.")
        return 0

    if missing_ogg:
        print(f"Converting {len(missing_ogg)} WAV files to OGG...")
        success = 0
        for wav in missing_ogg:
            if convert_wav_to_ogg(wav, ffmpeg, args.dry_run):
                success += 1
        print(f"Done: {success}/{len(missing_ogg)} converted.")
    else:
        print(f"All {len(wav_files)} WAV files already have OGG counterparts.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
