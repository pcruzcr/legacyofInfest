import re
from pathlib import Path

f = Path("src/engine/core/i18n.py")

# Read with errors="replace" (as done in todos_los_literales)
texto_replace = f.read_text(encoding="utf-8", errors="replace")
patron = re.compile(r'"((?:[^"\\]|\\.)*)"')
matches_replace = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', texto_replace))
inv_replace = [m for m in matches_replace if 'inventory' in m.group(1)]
print(f"With errors=replace: {len(inv_replace)} matches")
for m in inv_replace:
    print(f"  Found: {m.group(1)!r}")

# Test without errors parameter
texto_normal = Path("src/engine/core/i18n.py").read_text(encoding="utf-8")
matches_normal = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', texto_normal))
inv_normal = [m for m in matches_normal if 'inventory' in m.group(1)]
print(f"Without errors=replace: {len(inv_normal)} matches")
for m in inv_normal:
    print(f"  Found: {m.group(1)!r}")