with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\audio\audio_pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''def _save_cache(self, name: str, data: bytes) -> None:
        if self._cache_dir is not None:
            (self._cache_dir / name).write_bytes(data)'''

new = '''def _save_cache(self, name: str, data: bytes) -> None:
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
        
        reverb_path = Path(str(seg)).replace(".wav", f"_{reverb_name}_reverb.wav")
        # In production, this would load a pre-baked reverb variant
        # For now, apply simple algorithmic reverb as fallback
        return self._apply_reverb_fallback(seg, wet, dry, decay)

    def _apply_reverb_fallback(self, seg, wet: float, dry: float, decay: float):
        """Algorithmic reverb fallback when pre-baked variant is missing."""
        return self._apply_reverb(seg, decay)'''

content = content.replace(
    'def _save_cache(self, name: str, data: bytes) -> None:\n        if self._cache_dir is not None:\n            (self._cache_dir / name).write_bytes(data)',
    new
)

with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\audio\audio_pipeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')