import json
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

# Find keys containing "Puntuaci" or "current"
for k in list(en.keys()):
    if 'Puntuaci' in k or 'current' in k:
        print(f'Found: {repr(k)}')

# Delete them
for k in list(en.keys()):
    if 'Puntuaci' in k or 'current' in k:
        del en[k]
        print('Deleted: ' + repr(k))

with open('locale/en.json', 'w', encoding='utf-8') as f:
    json.dump(en, f, ensure_ascii=False, indent=2)

print('Done')