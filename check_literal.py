import re
from pathlib import Path

texto = Path('src/engine/core/i18n.py').read_text(encoding='utf-8')
patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')
matches = list(patron.finditer(texto))
for m in patron.finditer(texto):
    val = m.group(1) if m.group(1) is not None else m.group(2)
    if 'inventory' in val:
        print(f'Found: {val!r} at pos {m.start()}')