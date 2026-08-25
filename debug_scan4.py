import re
from pathlib import Path

patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')

literales = set()
carpeta = Path("C:/Users/pcruz/github/legacyofInfest/src/engine/core")
for f in sorted(carpeta.rglob("*.py")):
    texto = f.read_text(encoding="utf-8", errors="replace")
    for m in patron.finditer(texto):
        literales.add(m.group(1) if m.group(1) is not None else m.group(2))

with open("scan_results.txt", "w", encoding="utf-8") as out:
    out.write(f"Total literales: {len(literales)}\n")
    out.write(f"ui.inventory_title in set: {'ui.inventory_title' in literales}\n\n")

    # Check i18n.py specifically
    texto = Path("src/engine/core/i18n.py").read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', texto):
        val = m.group(1)
        if 'inventory' in val:
            out.write(f"Found: {val!r}\n")