with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact pattern
idx = content.find('}\n\ndef _migrar_inventario')
if idx >= 0:
    print('Found at:', idx)
    print(repr(content[idx-50:idx+50]))
else:
    print('Not found with that pattern')
    # Try alternatives
    for pattern in ['}\n\ndef _migrar', '}\n\ndef _migrar', '}\n\ndef _migrar', '}\n\ndef _migrar']:
        idx = content.find(pattern)
        if idx >= 0:
            print(f'Found pattern "{pattern}" at:', idx)
            print(repr(content[idx-50:idx+50]))
            break
    else:
        print('Not found')