import json
with open('locale/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

with open('check_cadena_out.txt', 'w', encoding='utf-8') as out:
    for k in list(en.keys()):
        if 'Cadena' in k or 'Cadena' in k or 'Chain' in k:
            out.write(f'en: {repr(k)} -> {repr(en[k])}\n')
    for k in list(es.keys()):
        if 'Cadena' in k or 'Chain' in k:
            out.write(f'es: {repr(k)} -> {repr(es[k])}\n')