import json

with open('locale/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)

# Valores originales en mayúsculas que el título muestra (test_i18n los fija)
correcciones = {
    'ui.start': 'JUGAR',
    'ui.world_map': 'MAPA MUNDIAL',
    'ui.inventory_title': 'INVENTARIO',
    'ui.skill_tree_title': '\u00c1RBOL DE HABILIDADES',
    'ui.shop': 'TIENDA',
    'ui.bestiary': 'BESTIARIO',
    'ui.achievements': 'LOGROS',
    'ui.records': 'R\u00c9CORDS',
    'ui.academic_demos': 'DEMOS ACAD\u00c9MICAS',
    'ui.options': 'OPCIONES',
    'ui.quit': 'SALIR',
    'ui.continue': 'CONTINUAR',
}
for k, v in correcciones.items():
    es[k] = v

with open('locale/es.json', 'w', encoding='utf-8') as f:
    json.dump(es, f, ensure_ascii=False, indent=2)
print('Valores de menú restaurados a mayúsculas originales')