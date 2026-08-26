#!/usr/bin/env python3
with open('src/engine/audio/audio_pipeline.py', 'rb') as f:
    content = f.read()

idx = 10491
func_start = content.rfind(b'def ', 0, idx)
func_line_start = content.rfind(b'\n', 0, idx) + 1
func_sig = content[func_start:content.find(b'\n', idx)]
print(f'Function signature: {content[func_start:content.find(b"\n", idx)]}')

body_start = content.find(b':', idx) + 1
body_end = idx + 500
body = content[func_start:func_start + 500]
print('Function body (first 500 chars):')
print(body[:500].decode('utf-8', errors='replace'))