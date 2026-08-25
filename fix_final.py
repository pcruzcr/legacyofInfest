import json

with open('locale/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

# 1. Add "Subir rango" to both catalogs
es['Subir rango'] = 'Subir rango'
en['Subir rango'] = 'Rank up'

# 2. Remove Spanish identity entries from en.json (keep only English identity + 6 AUD-307 Spanish->English)
# Spanish identity keys in es.json that have translations in en:
spanish_identity_in_en = [
    'Aceptar',
    'Cancelar',
    'Confirmar',
    'IDENTIFICACIÓN',
    'ÁRBOL DE HABILIDADES',
]

for k in spanish_identity_in_en:
    if k in en:
        del en[k]
        print(f'Removed from en.json: {k}')

# 3. Ensure the 6 AUD-307 strings are in en.json with translations
aud_307 = {
    'ESTUDIANTE': 'STUDENT',
    'EXPERIENCIA': 'EXPERIENCE',
    'Elegir': 'Choose',
    'IDENTIFICACIÓN': 'SIGN IN',
    'Subir rango': 'Rank up',
    'ÁRBOL DE HABILIDADES': 'SKILL TREE',
}
for k, v in aud_307.items():
    en[k] = v
    # Also ensure they're in es.json (identity for Spanish)
    if k not in es:
        es[k] = k

# Also ensure English identity for all English keys in es.json
for k in list(es.keys()):
    if not any(c in k for c in 'áéíóúÁÉÍÓÚÑñ'):
        if k not in en:
            en[k] = k

with open('locale/es.json', 'w', encoding='utf-8') as f:
    json.dump(es, f, ensure_ascii=False, indent=2)
with open('locale/en.json', 'w', encoding='utf-8') as f:
    json.dump(en, f, ensure_ascii=False, indent=2)

print('Fixed catalogs')