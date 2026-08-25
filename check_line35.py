import re
from pathlib import Path

f = Path("src/engine/core/i18n.py")
texto = f.read_text(encoding="utf-8")
lines = texto.splitlines()

with open("line35_output.txt", "w", encoding="utf-8") as out:
    for i, line in enumerate(lines, 1):
        if 'inventory' in line:
            out.write(f"Line {i}: {repr(line)}\n")
    
    line35 = lines[34]
    out.write(f"\nLine 35 raw: {repr(lines[34])}\n")
    out.write(f"Line 35 bytes: {lines[34].encode('utf-8')}\n")

    # Test regex on this specific line
    patron = re.compile(r'"((?:[^"\\]|\\.)*)"')
    match = re.search(r'"((?:[^"\\]|\\.)*)"', lines[34])
    if match:
        out.write(f"Match: {match.group(1)!r}\n")
    else:
        out.write("No match on line 35\n")