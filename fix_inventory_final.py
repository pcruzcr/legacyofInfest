with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The closing brace is at position 6398
# Insert new items before that position

new_items = '''
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

# Insert before the closing brace at position 6398
new_content = content[:6398] + ',\n' + '''
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
    ),''' + content[6398:]

with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'w', encoding='utf-8') as f:
    f.write(content[:6398] + ',\n' + '''
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
    ),''' + content[6398:])

print('Done')