import re
from pathlib import Path

f = Path("src/engine/core/i18n.py")
texto = f.read_text(encoding="utf-8")

# Exact pattern from todos_los_literales
patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')
matches = list(patron.finditer(texto))
inv_matches = [m for m in matches if 'inventory' in (m.group(1) or m.group(2) or '')]
print(f"Full scanner pattern: {len(inv_matches)} matches")
for m in matches:
    val = m.group(1) if m.group(1) is not None else m.group(2)
    if 'inventory' in val:
        print(f"  Found: {val!r}")

# Also test the double-quote only pattern
matches2 = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', texto))
inv2 = [m for m in matches if 'inventory' in m.group(1)]
print(f"\nDouble-quote only: {len(inv2)} matches")
for m in inv2:
    print(f"  Found: {m.group(1)!r}")