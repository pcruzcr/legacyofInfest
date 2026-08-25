import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

texto = Path("src/engine/core/i18n.py").read_text(encoding="utf-8")
patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')
lits = {m.group(1) if m.group(1) is not None else m.group(2) for m in patron.finditer(texto)}
print("ui.* en i18n.py:", sorted(l for l in lits if l.startswith("ui.")))

from scripts.check_translations import todos_los_literales, _DIRECTORIOS
lit = todos_los_literales()
print("total literales:", len(lit))
print("directorios escaneados:", _DIRECTORIOS)