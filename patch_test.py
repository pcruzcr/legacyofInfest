import re

with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the HUERFANAS_PERMITIDAS set and add missing entries
# The set ends with "        }" before "        datos ="

# Missing entries for Spanish (es)
es_missing = {
    'ui.collision_lab', 'ui.game_over', 'ui.inventory_title', 'ui.score',
    'UNIT II', 'VECTOR LAB',
}

# Missing entries for English (en) - these are the Spanish values that appear in en.json as inverse mappings
en_missing = {
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
}

with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the HUERFANAS_PERMITIDAS set and add missing entries
# The set ends with "        }" before "        datos ="

# First, add the missing entries to the existing set
# We'll replace the closing brace with the new entries + closing brace

new_entries = ',\n            '.join(f'"{e}"' for e in sorted([
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

# Read the file
with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the HUERFANAS_PERMITIDAS set closing brace
idx = content.find('HUERFANAS_PERMITIDAS = {')
if idx >= 0:
    # Find the closing brace of the set
    brace_count = 0
    in_string = False
    escape = False
    start_idx = content.find('HUERFANAS_PERMITIDAS = {')
    for i in range(start_idx, len(content)):
        c = content[i]
        if not escape and c == '"' and not in_string:
            in_string = not in_string
        elif not escape and c == '\\':
            escape = True
        else:
            escape = False
        if not in_string:
            if c == '{':
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
    
    if end_pos:
        # Insert new entries before the closing brace
        new_entries_str = ',\n            '.join(f'"{e}"' for e in sorted([
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
        
        new_content = content[:end_pos] + ',\n            ' + ',\n            '.join(f'"{e}"' for e in sorted([
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
        ])) + ',\n            }' + content[end_pos:]
        
        with open('tests/test_i18n.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Updated successfully")
    else:
        print("Closing brace not found")
else:
    print("HUERFANAS_PERMITIDAS not found")