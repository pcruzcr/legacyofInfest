import re
from pathlib import Path

f = Path("src/engine/core/i18n.py")
texto = f.read_text(encoding="utf-8")

# Print all matches that contain 'invent' or 'titul'
patron = re.compile(r'"((?:[^"\\]|\\.)*)"')
matches = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', texto))
print(f"Total matches: {len(matches)}")
for m in matches:
    val = m.group(1)
    if 'invent' in val.lower() or 'titul' in val.lower():
        print(f"Found: {val!r}")