import re
from pathlib import Path

f = Path("src/engine/core/i18n.py")
texto = f.read_text(encoding="utf-8")
patron = re.compile(r'"((?:[^"\\]|\\.)*)"')
matches = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', texto))
print(f"Total matches: {len(matches)}")
for m in matches:
    if 'inventory' in m.group(1):
        print(f"Found: {m.group(1)!r}")