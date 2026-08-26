#!/usr/bin/env python3
"""Find calls to _normalize"""
with open('src/engine/audio/audio_pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
for m in re.finditer(r'_normalize\(', content):
    start = max(0, m.start() - 80)
    end = min(len(content), m.end() + 80)
    print(f'Call at {m.start()}:')
    print(content[m.start()-80:m.end()+80])
    print('---')
print("Done")