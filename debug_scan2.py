import sys
sys.path.insert(0, '.')
from scripts.check_translations import todos_los_literales, _RAIZ

# Check what directories are scanned
from scripts.check_translations import _DIRECTORIOS
print("_DIRECTORIOS:", _DIRECTORIOS)

from scripts.check_translations import _RAIZ as RAIZ
from pathlib import Path

# Check if src/engine/core exists
core_path = RAIZ / "src/engine/core"
print(f"src/engine/core exists: {core_path.exists()}")
print(f"i18n.py exists: {(core_path / 'i18n.py').exists()}")

# Check what files are found by rglob
from pathlib import Path
core_files = list((RAIZ / "src/engine/core").rglob("*.py"))
print(f"Files in src/engine/core: {len(core_files)}")
for f in core_files:
    print(f"  {f.name}")

# Now test the actual scanner
import re
patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')
literales = set()
carpeta = Path("C:/Users/pcruz/github/legacyofInfest/src/engine/core")
for f in sorted(carpeta.rglob("*.py")):
    texto = f.read_text(encoding="utf-8", errors="replace")
    for m in patron.finditer(texto):
        literales.add(m.group(1) if m.group(1) is not None else m.group(2))

print(f"Literales from src/engine/core: {len(literales)}")
print(f"ui.inventory_title in scan: {'ui.inventory_title' in literales}")