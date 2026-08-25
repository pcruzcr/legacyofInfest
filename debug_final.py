import re
from pathlib import Path

# Exact replication of todos_los_literales scanner
patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')
literales = set()

carpeta = Path("C:/Users/pcruz/github/legacyofInfest/src/engine/core")
for f in sorted(carpeta.rglob("*.py")):
    print(f"Scanning: {f.name}")
    texto = f.read_text(encoding="utf-8", errors="replace")
    for m in patron.finditer(texto):
        val = m.group(1) if m.group(1) is not None else m.group(2)
        if 'inventory' in val:
            print(f"  Found in {f.name}: {val!r}")

# Also check if the file is being read correctly
f = Path("C:/Users/pcruz/github/legacyofInfest/src/engine/core/i18n.py")
texto = f.read_text(encoding="utf-8", errors="replace")
print(f"File read length: {len(texto)}")
matches = list(re.finditer(r'"((?:[^"\\]|\\.)*)"', texto))
inventory_matches = [m for m in matches if 'inventory' in m.group(1)]
print(f"Direct read inventory matches: {len(inventory_matches)}")
for m in matches:
    if 'inventory' in m.group(1):
        print(f"  Found: {m.group(1)!r}")