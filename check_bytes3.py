import re
from pathlib import Path

f = Path("src/engine/core/i18n.py")
raw = f.read_bytes()

# Find the exact line with inventory
idx = raw.find(b"ui.inventory_title")
if idx >= 0:
    # Get the line
    line_start = raw.rfind(b"\n", 0, idx) + 1
    line_end = raw.find(b"\n", idx)
    if line_end == -1:
        line_end = len(raw)
    line_bytes = raw[line_start:line_end]
    print(f"Line bytes: {line_bytes}")
    print(f"Line decoded: {line_bytes.decode('utf-8')}")
    
    # Test regex on this exact line
    line_text = line_bytes.decode('utf-8')
    match = re.search(r'"((?:[^"\\]|\\.)*)"', line_text)
    if match:
        print(f"Match on raw line: {match.group(1)!r}")
    else:
        print("No match on raw line")
        
    # Also check the full text
    text = raw.decode('utf-8')
    matches = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', line_text))
    print(f"Matches on line: {len(matches)}")
    for m in matches:
        if 'inventory' in m.group(1):
            print(f"  Found: {m.group(1)!r}")