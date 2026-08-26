with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    "skill_parry": ItemDef(
        id="skill_parry", name="Parada",
        description="Botón de jefe: desvías los ataques",
        icon_color=(255, 200, 100), slot="skill",
    ),
}
def _migrar_inventario() -> None:'''

new = '''    "skill_parry": ItemDef(
        id="skill_parry", name="Parada",
        description="Botón de jefe: desvías los ataques",
        icon_color=(255, 200, 100), slot="skill",
    ),
    # AUD-637 — Collectible Identity: nuevos tipos de coleccionables con identidad
    #: Fragmento de reliquia — lore del mundo, se entrega en SecretRoom
    "relic_fragment": ItemDef(
        id="relic_fragment", name="Fragmento de reliquia",
        description="Un fragmento de historia olvidada. Córtalo y léelo.",
        icon_color=(220, 200, 40),
    ),
    #: Dato académico — se entrega en laboratorios/bibliotecas del juego
    "academic_data": ItemDef(
        id="academic_data", name="Dato académico",
        description="Investigación de campo: conocimiento puro, sin uso inmediato.",
        icon_color=(100, 180, 255),
    ),
    #: Token de compañero — se gana en SecretRoom y se gasta para invocar buddy
    "buddy_token": ItemDef(
        id="buddy_token", name="Token de compañero",
        description="Un llamado de ayuda. Úsalo para invocar un compañero.",
        icon_color=(200, 180, 220),
    ),
}
def _migrar_inventario() -> None:'''

content = content.replace(
    '''    "skill_parry": ItemDef(
        id="skill_parry", name="Parada",
        description="Botón de jefe: desvías los ataques",
        icon_color=(255, 200, 100), slot="skill",
    ),
}
def _migrar_inventario() -> None:''',
    new
)

with open(r'C:\Users\pcruz\github\legacyofInfest\src\engine\core\inventory.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')