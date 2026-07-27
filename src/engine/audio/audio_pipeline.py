from __future__ import annotations

import io
import struct
from pathlib import Path
from typing import Any

import numpy as np


class AudioPipeline:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self._cache_dir = cache_dir
        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_pydub(self):
        try:
            from pydub import AudioSegment
            from pydub.effects import compress_dynamic_range, normalize
            return AudioSegment, normalize, compress_dynamic_range
        except ImportError as exc:
            raise ImportError(
                "pydub is required for AudioPipeline. "
                "Install it with: pip install 'legacyofinfest[audiotools]'"
            ) from exc

    def load_as_wav(self, path: Path, target_sr: int = 44100) -> bytes:
        AudioSegment, normalize, compress_dynamic_range = self._get_pydub()
        cache_key = f"{path.stem}_{target_sr}hz.wav"
        cached = self._load_cached(cache_key)
        if cached is not None:
            return cached
        seg = AudioSegment.from_file(str(path))
        seg = self._normalize(seg, target_sr, normalize, compress_dynamic_range)
        buf = io.BytesIO()
        seg.export(buf, format="wav")
        raw = buf.getvalue()
        self._save_cache(cache_key, raw)
        return raw

    def load_as_pcm(self, path: Path, target_sr: int = 44100) -> np.ndarray:
        AudioSegment, normalize, compress_dynamic_range = self._get_pydub()
        seg = AudioSegment.from_file(str(path))
        seg = self._normalize(seg, target_sr, normalize, compress_dynamic_range)
        samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
        samples /= 2 ** (seg.sample_width * 8 - 1)
        if seg.channels == 2:
            samples = samples.reshape(-1, 2).mean(axis=1)
        return samples

    def generate_sfx_variants(
        self, path: Path, output_dir: Path, variants: list[dict[str, Any]],
    ) -> list[Path]:
        AudioSegment, _normalize, _compress_dynamic_range = self._get_pydub()
        seg = AudioSegment.from_file(str(path))
        generated: list[Path] = []
        for v in variants:
            name = v.get("name", path.stem)
            variant = seg
            if "pitch_shift_semitones" in v:
                variant = variant._spawn(
                    variant.raw_data,
                    overrides={
                        "frame_rate": int(variant.frame_rate * (2 ** (v["pitch_shift_semitones"] / 12.0))),
                    },
                )
            if "reverb_decay" in v:
                variant = self._apply_reverb(variant, v["reverb_decay"])
            if "low_pass_hz" in v:
                variant = variant.low_pass_filter(v["low_pass_hz"])
            if "high_pass_hz" in v:
                variant = variant.high_pass_filter(v["high_pass_hz"])
            out = output_dir / f"{name}.wav"
            variant.export(str(out), format="wav")
            generated.append(out)
        return generated

    def convert_batch(
        self, src_dir: Path, dst_dir: Path, src_ext: str = ".wav", dst_ext: str = ".ogg",
        bitrate: str = "64k",
    ) -> list[Path]:
        AudioSegment, _normalize, _compress_dynamic_range = self._get_pydub()
        dst_dir.mkdir(parents=True, exist_ok=True)
        converted: list[Path] = []
        for f in src_dir.rglob(f"*{src_ext}"):
            seg = AudioSegment.from_file(str(f))
            out = dst_dir / f.relative_to(src_dir).with_suffix(dst_ext)
            out.parent.mkdir(parents=True, exist_ok=True)
            seg.export(str(out), format=dst_ext.replace(".", ""), bitrate=bitrate)
            converted.append(out)
        return converted

    def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):
        seg = seg.set_frame_rate(target_sr).set_channels(1)
        seg = normalize(seg)
        seg = compress_dynamic_range(seg, threshold=-20.0, ratio=4.0)
        return seg

    def _apply_reverb(self, seg, decay: float = 0.3):
        samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
        delay_ms = 50
        delay_samples = int(seg.frame_rate * delay_ms / 1000)
        wet = np.zeros_like(samples)
        wet[delay_samples:] = samples[:-delay_samples] * decay
        mixed = (samples + wet).astype(np.int16)
        return seg._spawn(struct.pack(f"<{len(mixed)}h", *mixed))

    def _load_cached(self, name: str) -> bytes | None:
        if self._cache_dir is None:
            return None
        path = self._cache_dir / name
        return path.read_bytes() if path.exists() else None

    def _save_cache(self, name: str, data: bytes) -> None:
        if self._cache_dir is not None:
            (self._cache_dir / name).write_bytes(data)
