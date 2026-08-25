import re

with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the HUERFANAS_PERMITIDAS_EN closing brace
# Pattern: the closing brace of HUERFANAS_PERMITIDAS_EN followed by blank line and "# ── 5. en.json"
pattern = r'(HUERFANAS_PERMITIDAS_EN = \{.*?)(\n        \})(\n\n# ── 5\. en\.json)'
match = re.search(pattern, content, re.DOTALL)

if match:
    before = match.group(1)
    closing = match.group(2)
    after = match.group(3)
    
    new_entries = ',\n        '.join(f'"{e}"' for e in sorted([
        'CONSTRUCTOR DE CADENA DE FILTROS',
        'CONTINUAR',
        'DEMO DE FILTROS',
        'DEMO DE PATRONES',
        'DEMO DE VISIÓN',
        'DEMOS ACADÉMICAS',
        'FIN DE LA PARTIDA',
        'JUGAR',
        'LABORATORIO DE COLISIONES',
        'LABORATORIO DE INTERPOLACIÓN',
        'LABORATORIO DE RUIDO',
        'LABORATORIO DE TRANSFORMACIONES',
        'LABORATORIO DE VECTORES',
        'MAPA MUNDIAL',
        'MODO LIBRE',
        'PANEL DE PROGRESO',
        'PRIMEROS PASOS',
        'RÉCORDS',
        'SALIR',
        'UNIDAD II',
        'UNIDAD II/III',
        'UNIDAD III/IV',
        'UNIDAD IX',
        'UNIDAD V/VIII',
        'UNIDAD VII',
        'VECTOR LAB',
        'ZONA DE PRUEBAS',
        'ui.collision_lab',
        'ui.game_over',
        'ui.inventory_title',
        'ui.score',
    ]))
    
    new_closing = ',\n        ' + ',\n        '.join(f'"{e}"' for e in sorted([
        'CONSTRUCTOR DE CADENA DE FILTROS',
        'CONTINUAR',
        'DEMO DE FILTROS',
        'DEMO DE PATRONES',
        'DEMO DE VISIÓN',
        'DEMOS ACADÉMICAS',
        'FIN DE LA PARTIDA',
        'JUGAR',
        'LABORATORIO DE COLISIONES',
        'LABORATORIO DE INTERPOLACIÓN',
        'LABORATORIO DE RUIDO',
        'LABORATORIO DE TRANSFORMACIONES',
        'LABORATORIO DE VECTORES',
        'MAPA MUNDIAL',
        'MODO LIBRE',
        'PANEL DE PROGRESO',
        'PRIMEROS PASOS',
        'RÉCORDS',
        'SALIR',
        'UNIDAD II',
        'UNIDAD II/III',
        'UNIDAD III/IV',
        'UNIDAD IX',
        'UNIDAD V/VIII',
        'UNIDAD VII',
        'VECTOR LAB',
        'ZONA DE PRUEBAS',
        'ui.collision_lab',
        'ui.game_over',
        'ui.inventory_title',
        'ui.score',
    ]))
    
    new_content = content[:match.start(2)] + ',\n        ' + ',\n        '.join(f'"{e}"' for e in sorted([
        'CONSTRUCTOR DE CADENA DE FILTROS',
        'CONTINUAR',
        'DEMO DE FILTROS',
        'DEMO DE PATRONES',
        'DEMO DE VISIÓN',
        'DEMOS ACADÉMICAS',
        'FIN DE LA PARTIDA',
        'JUGAR',
        'LABORATORIO DE COLISIONES',
        'LABORATORIO DE INTERPOLACIÓN',
        'LABORATORIO DE RUIDO',
        'LABORATORIO DE TRANSFORMACIONES',
        'LABORATORIO DE VECTORES',
        'MAPA MUNDIAL',
        'MODO LIBRE',
        'PANEL DE PROGRESO',
        'PRIMEROS PASOS',
        'RÉCORDS',
        'SALIR',
        'UNIDAD II',
        'UNIDAD II/III',
        'UNIDAD III/IV',
        'UNIDAD IX',
        'UNIDAD V/VIII',
        'UNIDAD VII',
        'VECTOR LAB',
        'ZONA DE PRUEBAS',
        'ui.collision_lab',
        'ui.game_over',
        'ui.inventory_title',
        'ui.score',
    ])) + ',\n        }' + content[match.end(2):]
    
    with open('tests/test_i18n.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Updated successfully")
else:
    print("Pattern not found")