import json
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

to_remove = []
for k in list(en.keys()):
    if 'Cadena' in k:
        to_remove.append(k)

for k in to_remove:
    if k in en:
        del en[k]

with open('locale/en.json', 'w', encoding='utf-8') as f:
    json.dump(en, f, ensure_ascii=False, indent=2)

with open('remove_log2.txt', 'w', encoding='utf-8') as out:
    for k in to_remove:
        out.write(f'Removed: {repr(k)}\n')

print('Done')