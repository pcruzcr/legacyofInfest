import json

with open('locale/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

# Spanish strings missing translations
# Add to es.json (identity) and en.json (translation)
missing = {
    'Ajustes del jugador': 'Player settings',
    'CONTROLES': 'CONTROLS',
    'Cambiar': 'Change',
    'Comprar / vender': 'Buy / sell',
    'MAPA DEL MUNDO': 'WORLD MAP',
    'Objetos recogidos': 'Items collected',
}

for es_key, en_val in missing.items():
    # Add to es.json (identity)
    es[es_key] = es_key
    # Add to en.json (translation)
    en[es_key] = en_val

with open('locale/es.json', 'w', encoding='utf-8') as f:
    json.dump(es, f, ensure_ascii=False, indent=2)
with open('locale/en.json', 'w', encoding='utf-8') as f:
    json.dump(en, f, ensure_ascii=False, indent=2)

print('Added missing translations')