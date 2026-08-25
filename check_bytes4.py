import re
from pathlib import Path

f = Path("src/engine/core/i18n.py")
raw = f.read_bytes()

idx = raw.find(b"ui.inventory_title")
if idx >= 0:
    line_start = raw.rfind(b"\n", 0, idx) + 1
    line_end = raw.find(b"\n", idx)
    if line_end == -1:
        line_end = len(raw)
    line_bytes = raw[line_start:line_end]
    
    with open("output.txt", "w", encoding="utf-8") as out:
        out.write(f"Line bytes: {line_bytes}\n")
        out.write(f"Line decoded: {line_bytes.decode('utf-8')}\n")
        
        line_text = line_bytes.decode('utf-8')
        match = re.search(r'"((?:[^"\\]|\\.)*)"', line_text)
        if match:
            out.write(f"Match on raw line: {match.group(1)!r}\n")
        else:
            out.write("No match on raw line\n")
            
        matches = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', line_text))
        out.write(f"Matches on line: {len(matches)}\n")
        for m in matches:
            if 'inventory' in m.group(1):
                out.write(f"  Found: {m.group(1)!r}\n")