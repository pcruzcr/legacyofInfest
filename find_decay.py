#!/usr/bin/env python3
with open('src/engine/audio/audio_pipeline.py', 'rb') as f:
    content = f.read()

idx = content.find(b'decay')
while idx != -1:
    if idx > 2500 and idx < 2600:
        print(f'Found decay at byte {idx}')
        # Find function start
        func_start = content.rfind(b'def ', 0, idx)
        if func_start >= 0:
            func_line_start = content.rfind(b'\n', 0, idx) + 1
            func_sig = content[func_start:content.find(b'\n', func_start)]
            print(f'Function: {content[func_start:content.find(b"\n", func_start)]}')
        break
    idx = content.find(b'decay', idx + 1)