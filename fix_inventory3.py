with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact pattern
idx = content.find('},\n\ndef _migrar_inventario')
if idx >= 0:
    print('Found at:', idx)
    print(repr(content[idx-100:idx+50]))
else:
    print('Pattern not found, searching...')
    for m in __import__('re').finditer(r'\}\s*\n\s*def _migrar_inventario', content):
        print('Found at:', m.start())
        print(repr(content[m.start()-100:m.end()+50])