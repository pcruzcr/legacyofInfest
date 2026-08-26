#!/usr/bin/env python3
"""Fix the _normalize function to add decay parameter."""
import re

with open('src/engine/audio/audio_pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the _normalize function definition
idx = content.find('def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):')
if idx == -1:
    idx = content.find('def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):')

if idx == -1:
    idx = content.find('def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):')

if idx == -1:
    print("Could not find _normalize function")
    exit(1)

# Find the function signature end
func_start = content.rfind('def ', 0, idx)
func_line_start = content.rfind('\n', 0, idx) + 1
func_sig = content[func_start:content.find('\n', idx)]
print(f'Function signature: {content[func_start:content.find(b"\n", idx)]}')

# Find the function body end
class_start = content.find('class ')
class_end = content.find('\nclass ', idx + 1)
if class_end == -1:
    class_end = len(content)

# The function body is between the signature and the next method or end of class
func_body_start = content.find(':', idx) + 1
class_end = content.find('\nclass ', idx + 1)
if class_end == -1:
    class_end = len(content)

func_body = content[func_start:class_end]

# The issue: the function uses 'decay' but it's not a parameter
# We need to add 'decay: float = 1.0' (or similar default) to the function signature

# Find the function signature line
func_def_start = content.rfind('def _normalize', 0, idx)
func_line_end = content.find('\n', idx)
func_sig = content[func_start:idx+1]

print(f'Current signature: {content[func_start:idx+1]}')

# The function signature needs to add decay parameter
# Current: def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):
# Should be: def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range, decay: float = 1.0):

old_sig = 'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):'
new_sig = 'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range, decay: float = 1.0):'

new_content = content[:idx] + content[idx:].replace(
    'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range):',
    'def _normalize(self, seg, target_sr: int, normalize, compress_dynamic_range, decay: float = 1.0):',
    1
)

# Also need to update the calls to _normalize to pass decay parameter
# Check calls to _normalize
import re
for m in re.finditer(r'_normalize\(', content):
    call_start = max(0, m.start() - 50)
    call_end = min(len(content), m.end() + 50)
    call_text = content[m.start()-50:m.end()+50]
    if 'target_sr' in content[m.start():m.end()+50] and 'decay' not in content[m.start():m.end()+50]:
        print(f'Call at {m.start()}: needs decay parameter')

print("Done analyzing")