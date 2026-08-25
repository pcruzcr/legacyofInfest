import re
from pathlib import Path

# Replicate the exact scanner from todos_los_literales
patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')

literales = set()
carpeta = Path("C:/Users/pcruz/github/legacyofInfest/src/engine/core")
for f in sorted(carpeta.rglob("*.py")):
    texto = f.read_text(encoding="utf-8", errors="replace")
    for m in patron.finditer(texto):
        literales.add(m.group(1) if m.group(1) is not None else m.group(2))

print(f"Total literales: {len(literales)}")
print(f"ui.inventory_title in set: {'ui.inventory_title' in literales}")

# Check specifically for i18n.py
texto = Path("src/engine/core/i18n.py").read_text(encoding="utf-8", errors="replace")
for m in re.finditer(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'', texto):
    val = m.group(1) if m.group(1) is not None else m.group(2)
    if 'inventory' in val:
        print(f"Found: {val!r}")

# Also check if the file is being read with errors="replace"
with open("src/engine/core/i18n.py", "r", encoding="utf-8", errors="replace") as f:
    texto = f.read()
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', texto):
        val = m.group(1)
        if 'inventory' in val:
            print(f"Direct read - Found: {val!r}")