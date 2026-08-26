import re

with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the pattern
matches = list(re.finditer(r'\}\s*\n\s*def _migrar_inventario', content))
if matches:
    for m in matches:
        print('Found at:', m.start())
        start = max(0, m.start() - 100)
        end = m.end() + 50
        print(repr(content[m.start():m.end()+50]))
else:
    print('Pattern not found')
    # Try alternative search
    for m in re.finditer(r'\}\s*\n\s*def _migrar_inventario', content):
        print('Found alt at:', m.start())
        print(repr(content[m.start()-100:m.end()+50]))