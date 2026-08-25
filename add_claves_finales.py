import json

with open('locale/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

nuevas = {
    'ui.quiz.progress': ('  {current}/{total}  |  Score: {score}',
                         '  {current}/{total}  |  Puntuaci\u00f3n: {score}'),
    'ui.vector_lab.status.mode': ('Mode: {mode}', 'Modo: {mode}'),
}

for clave, (valor_en, valor_es) in nuevas.items():
    es[clave] = valor_es
    en[clave] = valor_en

with open('locale/es.json', 'w', encoding='utf-8') as f:
    json.dump(es, f, ensure_ascii=False, indent=2)
with open('locale/en.json', 'w', encoding='utf-8') as f:
    json.dump(en, f, ensure_ascii=False, indent=2)

print('Claves añadidas:', ', '.join(nuevas))