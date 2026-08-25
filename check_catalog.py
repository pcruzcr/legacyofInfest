import json
with open('locale/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

with open('check_catalog_out.txt', 'w', encoding='utf-8') as out:
    for k in ['Chain: Z \u2192 Z \u2192 X', 'Chain: Z Z X', 'Combo: -', 'Combo: \u2014', 'Score: {score}']:
        out.write(f'{repr(k)}: es={k in es}, en={k in en}\n')