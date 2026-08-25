import json
with open('locale/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

for k in ['Subir rango', 'Aceptar', 'Cancelar', 'Confirmar', 'Elegir', 'IDENTIFICACIÓN', 'ESTUDIANTE', 'EXPERIENCIA', 'ÁRBOL DE HABILIDADES']:
    print(f'{k!r}: es={k in es}, en={k in en}')
    if k in es:
        print(f'  es[{k!r}] = {repr(es[k])}')
    if k in en:
        print(f'  en[{k!r}] = {repr(en[k])}')