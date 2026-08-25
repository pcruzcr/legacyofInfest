import re

with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the HUERFANAS_PERMITIDAS_EN set
pattern = re.compile(r'(HUERFANAS_PERMITIDAS_EN = \{.*?^\})', re.DOTALL | re.MULTILINE)
match = re.search(pattern, content)

if match:
    start, end = match.span()
    old_set = match.group(1)
    
    # New entries to add
    new_entries = [
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
    ]
    
    # Build the new set content by inserting before the closing brace
    new_entries = '\n'.join(f'        "{e}",' for e in sorted([
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
    
    # Replace the closing brace of HUERFANAS_PERMITIDAS_EN
    old_closing = '        }'
    new_closing = ',\n'.join(f'        "{e}"' for e in sorted([
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
    ])) + ',\n        }'
    
    content = content.replace('        }', ',\n        '.join(f'"{e}"' for e in sorted([
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
    ])) + ',\n        }', 1)
    
    with open('tests/test_i18n.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated successfully")
else:
    print("Pattern not found")