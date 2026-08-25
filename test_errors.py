from pathlib import Path
import re

f = Path("src/engine/core/i18n.py")

# Test with errors="replace"
texto_replace = f.read_text(encoding="utf-8", errors="replace")
patron = re.compile(r'"((?:[^"\\]|\\.)*)"')
matches_replace = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', texto_replace))
inv_replace = [m for m in matches_replace if 'inventory' in m.group(1)]
print(f"With errors=replace: {len(inv_replace)} matches")

# Test without errors parameter
texto_normal = f.read_text(encoding="utf-8")
matches_normal = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', texto_normal))
inv_normal = [m for m in matches_normal if 'inventory' in m.group(1)]
print(f"Without errors=replace: {len(inv_normal)} matches")
for m in inv_normal:
    print(f"  Found: {m.group(1)!r}")

# Check what errors="replace" does to the arrow character
arrow = "\u2192"
print(f"Arrow char: {arrow!r}")
print(f"Arrow bytes: {arrow.encode('utf-8')}")
arrow_replaced = arrow.encode('utf-8', errors='replace').decode('utf-8')
print(f"Arrow with replace: {arrow_replaced!r}")
print(f"Arrow replaced bytes: {arrow_replaced.encode('utf-8')}")