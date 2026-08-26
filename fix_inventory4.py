with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact closing brace of _ITEM_DEFS
idx = content.find('},\n\ndef _migrar_inventario')
if idx >= 0:
    print('Found at:', idx)
    # The issue is that there's an extra } after the closing brace
    # We need to find the exact structure
    # Look at the context
    print(repr(content[idx-200:idx+50]))
else:
    # Try to find the exact pattern
    import re
    for m in __import__('re').finditer(r'\}\s*\n\s*def _migrar_inventario', content):
        print('Found at:', m.start())
        print(repr(content[m.start()-100:m.end()+50])