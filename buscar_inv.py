from pathlib import Path
import re

out = []
for py in list(Path('src/engine').rglob('*.py')) + list(Path('src/framework').rglob('*.py')):
    for i, line in enumerate(py.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        if 'ui.inventory' in line:
            out.append(f'{py}:{i}: {line.strip()[:120]}')

Path('busca_inventory.txt').write_text('\n'.join(out), encoding='utf-8')
print(len(out), 'coincidencias')