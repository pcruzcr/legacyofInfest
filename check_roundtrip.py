import json
with open('locale/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

# Find English->Spanish entries in es.json that have reverse in en.json
with open('roundtrip_check.txt', 'w', encoding='utf-8') as out:
    for original, castellano in es.items():
        if castellano in en:
            vuelta = en[castellano]
            if vuelta != original:
                out.write(f'MISMATCH: es[{repr(original)}]={repr(castellano)}, en[{repr(castellano)}]={repr(en[castellano])}, expected {repr(original)}\n')
            else:
                out.write(f'OK: es[{repr(original)}]={repr(castellano)}, en[{repr(castellano)}]={repr(en[castellano])}\n')