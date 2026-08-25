import re
from pathlib import Path

carpeta = Path("C:/Users/pcruz/github/legacyofInfest/src/engine/core")
f = carpeta / "i18n.py"
texto = f.read_text(encoding="utf-8", errors="replace")
print(f"File: {f}")
print(f"Length: {len(texto)}")

matches = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', texto))
inventory_matches = [m for m in matches if 'inventory' in m.group(1)]
print(f"Total double-quoted matches: {len(matches)}")
print(f"Inventory matches: {len(inventory_matches)}")
for m in inventory_matches:
    print(f"  Found: {m.group(1)!r}")

patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')
matches2 = list(patron.finditer(texto))
inventory_matches2 = [m for m in matches2 if 'inventory' in (m.group(1) or m.group(2) or '')]
print(f"\nFull pattern matches: {len(matches2)}")
print(f"Inventory matches (full): {len(inventory_matches2)}")
for m in inventory_matches2:
    val = m.group(1) if m.group(1) is not None else m.group(2)
    print(f"  Found: {val!r}")