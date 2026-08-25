import json
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

# Remove Spanish reverse mappings
to_remove = [
    '  {current}/{total}  |  Puntuaci\u00f3n: {score}',
    'Cadena: Z \u2192 Z \u2192 X',
    'Combo: \u2014',
    'Logro desbloqueado: {name}',
    'Cancelar',
    'Confirmar',
    'Subir rango',
]

for k in to_remove:
    if k in en:
        del en[k]
        print('Removed: ' + k)

with open('locale/en.json', 'w', encoding='utf-8') as f:
    json.dump(en, f, ensure_ascii=False, indent=2)

print('Done')