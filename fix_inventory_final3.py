with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position of the closing brace before _migrar_inventario
idx = content.find('\n}\n\ndef _migrar_inventario')
if idx < 0:
    print('Pattern not found')
    exit(1)

print('Found at:', idx)

new_items = ''',
    # AUD-637 -- Collectible Identity: nuevos tipos de coleccionables con identidad
    #: Fragmento de reliquia -- lore del mundo, se entrega en SecretRoom
    "relic_fragment": ItemDef(
        id="relic_fragment", name="Fragmento de reliquia",
        description="Un fragmento de historia olvidada. Cortalo y leelo.",
        icon_color=(220, 200, 40),
    ),
    #: Dato académico -- se entrega en laboratorios/bibliotecas del juego
    "academic_data": ItemDef(
        id="academic_data", name="Dato académico",
        description="Investigacion de campo: conocimiento puro, sin uso inmediato.",
        icon_color=(100, 180, 255),
    ),
    #: Token de compañero -- se gana en SecretRoom y se gasta para invocar buddy
    "buddy_token": ItemDef(
        id="buddy_token", name="Token de compañero",
        description="Un llamado de ayuda. Usalo para invocar un compañero.",
        icon_color=(200, 180, 220),
    ),'''

# Find the exact position to insert - before the closing brace of _ITEM_DEFS
# The pattern is '}\n\ndef _migrar_inventario'
idx = content.find('\n}\n\ndef _migrar_inventario')
if idx < 0:
    print('Pattern not found')
    exit(1)

# Insert before the closing brace
# The pattern is '}\n\ndef _migrar_inventario'
# We need to insert before the '}' that closes the dict
# Find the actual '}' character position
insert_pos = content.rfind('}', 0, content.find('\n}\n\ndef _migrar_inventario'))

new_content = content[:idx] + ',\n' + '''
    # AUD-637 -- Collectible Identity: nuevos tipos de coleccionables con identidad
    #: Fragmento de reliquia -- lore del mundo, se entrega en SecretRoom
    "relic_fragment": ItemDef(
        id="relic_fragment", name="Fragmento de reliquia",
        description="Un fragmento de historia olvidada. Cortalo y leelo.",
        icon_color=(220, 200, 40),
    ),
    #: Dato académico -- se entrega en laboratorios/bibliotecas del juego
    "academic_data": ItemDef(
        id="academic_data", name="Dato académico",
        description="Investigacion de campo: conocimiento puro, sin uso inmediato.",
        icon_color=(100, 180, 255),
    ),
    #: Token de compañero -- se gana en SecretRoom y se gasta para invocar buddy
    "buddy_token": ItemDef(
        id="buddy_token", name="Token de compañero",
        description="Un llamado de ayuda. Usalo para invocar un compañero.",
        icon_color=(200, 180, 220),
    ),''' + content[content.find('\n}\n\ndef _migrar_inventario'):]

with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'w', encoding='utf-8') as f:
    f.write(content[:content.rfind('}', 0, content.find('\n}\n\ndef _migrar_inventario'))] + ',\n' + '''
    # AUD-637 -- Collectible Identity: nuevos tipos de coleccionables con identidad
    #: Fragmento de reliquia -- lore del mundo, se entrega en SecretRoom
    "relic_fragment": ItemDef(
        id="relic_fragment", name="Fragmento de reliquia",
        description="Un fragmento de historia olvidada. Cortalo y leelo.",
        icon_color=(220, 200, 40),
    ),
    #: Dato académico -- se entrega en laboratorios/bibliotecas del juego
    "academic_data": ItemDef(
        id="academic_data", name="Dato académico",
        description="Investigacion de campo: conocimiento puro, sin uso inmediato.",
        icon_color=(100, 180, 255),
    ),
    #: Token de compañero -- se gana en SecretRoom y se gasta para invocar buddy
    "buddy_token": ItemDef(
        id="buddy_token", name="Token de compañero",
        description="Un llamado de ayuda. Usalo para invocar un compañero.",
        icon_color=(200, 180, 220),
    ),''' + content[content.find('\n}\n\ndef _migrar_inventario'):]

with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'w', encoding='utf-8') as f:
    f.write(content[:content.rfind('}', 0, content.find('\n}\n\ndef _migrar_inventario'))] + ',\n' + '''
    # AUD-637 -- Collectible Identity: nuevos tipos de coleccionables con identidad
    #: Fragmento de reliquia -- lore del mundo, se entrega en SecretRoom
    "relic_fragment": ItemDef(
        id="relic_fragment", name="Fragmento de reliquia",
        description="Un fragmento de historia olvidada. Cortalo y leelo.",
        icon_color=(220, 200, 40),
    ),
    #: Dato académico -- se entrega en laboratorios/bibliotecas del juego
    "academic_data": ItemDef(
        id="academic_data", name="Dato académico",
        description="Investigacion de campo: conocimiento puro, sin uso inmediato.",
        icon_color=(100, 180, 255),
    ),
    #: Token de compañero -- se gana en SecretRoom y se gasta para invocar buddy
    "buddy_token": ItemDef(
        id="buddy_token", name="Token de compañero",
        description="Un llamado de ayuda. Usalo para invocar un compañero.",
        icon_color=(200, 180, 220),
    ),''' + content[content.find('\n}\n\ndef _migrar_inventario'):])

print('Done')