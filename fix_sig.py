#!/usr/bin/env python3
"""Fix _normalize function signature to add decay parameter."""
import re

with open('src/engine/audio/audio_pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix function signature
old_sig = 'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):'
new_sig = 'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range, decay: float = 1.0):'

if 'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):' in content:
    content = content.replace(
        'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):',
        'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range, decay: float = 1.0):'
    )
    print("Fixed function signature")
else:
    print("Function signature not found in expected format")

with open('src/engine/audio/audio_pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):' in content:
    content = content.replace(
        'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):',
        'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range, decay: float = 1.0):'
    )
    print("Fixed function signature")
else:
    print("Function signature not found in expected format")

with open('src/engine/audio/audio_pipeline.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")