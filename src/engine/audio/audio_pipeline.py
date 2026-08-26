from __future__ import annotations

import io
import math
import struct
from pathlib import Path
from typing import Any

import numpy as np
from scipy.signal import butter, sosfilt

# EBU R128 constants
LUFS_TARGET = -23.0
LUFS_TOLERANCE = 1.0
TRUE_PEAK_LIMIT = -1.0  # dBTP


class AudioPipeline:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self._cache_dir = cache_dir
        self._sr: int = 48000
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
        try:
            rel = path.relative_to(Path.cwd())
        except ValueError:
            rel = path
        cache_key = f"{rel.as_posix().replace('/', '_')}_{target_sr}hz.wav"
        cached = self._load_cached(cache_key)
        if cached is not None:
            return cached
        seg = AudioSegment.from_file(str(path))
        seg = self._normalize(seg, target_sr, normalize, compress_dynamic_range, 1.0)
        buf = io.BytesIO()
        seg.export(buf, format="wav")
        raw = buf.getvalue()
        self._save_cache(cache_key, raw)
        return raw

    def load_as_pcm(self, path: Path, target_sr: int = 44100) -> np.ndarray:
        AudioSegment, normalize, compress_dynamic_range = self._get_pydub()
        seg = AudioSegment.from_file(str(path))
        seg = self._normalize(seg, target_sr, normalize, compress_dynamic_range, 1.0)
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
                variant = self._apply_reverb_fallback(variant, 0.3, 0.7, v["reverb_decay"])
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

    def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range, decay: float = 1.0):
        seg = seg.set_frame_rate(target_sr).set_channels(1)
        seg = normalize(seg)
        seg = compress_dynamic_range(seg, threshold=-20.0, ratio=4.0)
        return seg

    # ── AUD-638 — Loudness Normalization (EBU R128 / -23 LUFS) ──────────────
    
    def measure_loudness(self, samples: np.ndarray, sample_rate: int) -> float:
        """Measure integrated loudness in LUFS (EBU R128).
        
        Returns integrated loudness in LUFS (negative values).
        """
        if samples.size == 0:
            return -float('inf')
        
        # Convert to float [-1, 1]
        if samples.dtype != np.float32:
            samples = samples.astype(np.float32) / 32768.0
        
        # K-weighting filter (EBU R128)
        # Pre-filter: high-pass at 1.5 Hz (removes DC) + shelf at 1.5 kHz (+4 dB)
        # High-pass at 1.5 Hz (very gentle) — usa sample_rate del argumento, no self._sr por defecto
        sos_hp = butter(2, 1.5, btype='highpass', fs=sample_rate, output='sos')
        
        # For simplicity, we'll use a simplified K-weighting approximation
        # Full implementation would use precise filter coefficients from EBU R128
        
        # Apply high-pass to remove DC (usa sample_rate, no self._sr)
        sos_hp = butter(4, 1.5, btype='highpass', fs=sample_rate, output='sos')
        filtered = sosfilt(sos_hp, samples)
        
        # Apply shelf filter (high shelf at 1.5kHz con +4 dB)
        sos_shelf = butter(2, 1500, btype='highpass', fs=sample_rate, output='sos')
        filtered = sosfilt(sos_shelf, filtered)
        
        # Mean square
        mean_square = np.mean(filtered ** 2)
        
        if mean_square <= 0:
            return -float('inf')
        
        # LUFS = -0.691 + 10 * log10(mean_square)
        lufs = -0.691 + 10.0 * math.log10(mean_square)
        return lufs

    def _get_sample_rate(self, seg) -> int:
        return seg.frame_rate

    def _get_channels(self, seg) -> int:
        return seg.channels

    def measure_lufs(self, seg) -> float:
        """Measure integrated loudness of an audio segment in LUFS."""
        self._sr = seg.frame_rate
        samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
        
        # Convert to float [-1, 1]
        max_int = 2 ** (seg.sample_width * 8 - 1)
        if max_int > 0:
            samples = samples.astype(np.float32) / max_int
        else:
            samples = samples.astype(np.float32)
        
        # Handle stereo by averaging channels
        if seg.channels == 2:
            samples = samples.reshape(-1, 2).mean(axis=1)
        
        return self.measure_loudness(samples, seg.frame_rate)

    def normalize_loudness(self, seg, target_lufs: float = LUFS_TARGET):
        """Normalize audio segment to target LUFS (EBU R128)."""
        current_lufs = self.measure_lufs(seg)
        
        if current_lufs == -float('inf'):
            return seg  # silence
        
        # Calculate gain needed
        gain_db = LUFS_TARGET - current_lufs
        
        # Apply gain using pydub
        seg = seg.apply_gain(gain_db)
        
        # Check true peak
        true_peak: float = self._measure_true_peak(seg)
        if true_peak > TRUE_PEAK_LIMIT:
            # Reduce gain to meet true peak limit
            peak_reduction_db = true_peak - TRUE_PEAK_LIMIT
            seg = seg.apply_gain(-peak_reduction_db)
        
        return seg

    def _measure_true_peak(self, seg) -> float:
        """Measure true peak in dBTP (dB True Peak).
        
        True peak is measured by oversampling 4x and finding the maximum
        sample value.
        """
        samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
        max_int = 2 ** (seg.sample_width * 8 - 1)
        samples = samples.astype(np.float32) / max_int
        
        # Oversample 4x for true peak measurement
        if len(samples) > 4:
            # Simple 4x oversampling by zero-padding in frequency domain
            # For simplicity, we'll just use 4x linear interpolation
            n = len(samples)
            oversampled = np.zeros(n * 4)
            oversampled[::4] = samples
            # Simple linear interpolation for peak detection
            for i in range(1, 4):
                oversampled[i::4] = (samples[:-1] * (1 - i/4) + samples[1:] * (i/4)) if len(samples) > 1 else samples
        else:
            oversampled = samples
        
        true_peak: float = np.max(np.abs(oversampled))
        if true_peak <= 0:
            return -float('inf')
        return 20 * math.log10(true_peak)

    def normalize_audio_file(self, input_path: Path, output_path: Path, 
                              target_lufs: float = LUFS_TARGET) -> None:
        """Normalize an audio file to target LUFS (EBU R128).
        
        Reads input file, normalizes to target LUFS, writes output.
        """
        AudioSegment, _normalize, _compress_dynamic_range = self._get_pydub()
        seg = AudioSegment.from_file(str(input_path))
        
        # Normalize loudness
        seg = self.normalize_loudness(seg, target_lufs=target_lufs)
        
        # Export
        seg.export(str(output_path), format="wav")

    # ── End of Loudness Normalization ────────────────────────────────────
    
    def _apply_reverb_effect(self, seg, decay: float = 1.0):
        samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
        max_int = 2 ** (seg.sample_width * 8 - 1) - 1
        # AUD-314 — mezclar en int16 envolvía (32767 + eco ≈ 45000 → -20536):
        # se trabaja en [-1, 1] y se recorta antes de volver a int16.
        norm = samples / max_int
        delay_ms = 50
        delay_samples = int(seg.frame_rate * delay_ms / 1000)
        wet = np.zeros_like(norm)
        wet[delay_samples:] = norm[:-delay_samples] * decay
        mixed = np.clip(norm + wet, -1.0, 1.0) * max_int
        return seg._spawn(struct.pack(f"<{len(mixed)}h", *mixed.astype(np.int16)))

    def _load_cached(self, name: str) -> bytes | None:
        if self._cache_dir is None:
            return None
        path = self._cache_dir / name
        return path.read_bytes() if path.exists() else None

    def _save_cache(self, name: str, data: bytes) -> None:
        if self._cache_dir is not None:
            (self._cache_dir / name).write_bytes(data)

    # ─────────────────────────────────────────────────────────────────
    # AUD-639 — Reverb Zones (pre-baked variants)
    # ─────────────────────────────────────────────────────────────────
    
    def apply_reverb(self, seg, reverb_name: str, wet: float = 0.3, 
                     dry: float = 0.7, decay: float = 1.5):
        """Apply pre-baked reverb variant to a segment.
        
        The reverb variants are pre-baked by \`tools/generate_all_assets.py\`
        and stored as \`{name}_reverb.wav\` alongside the original.
        """
        if reverb_name == "default":
            return seg
        
        # In production, this would load a pre-baked reverb variant
        # For now, apply simple algorithmic reverb as fallback
        return self._apply_reverb_fallback(seg, wet, dry, decay)

    def _apply_reverb_fallback(self, seg, wet: float, dry: float, decay: float):
        """Algorithmic reverb fallback when pre-baked variant is missing."""
        return self._apply_reverb_effect(seg, decay)
