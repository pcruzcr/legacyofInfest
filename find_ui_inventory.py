import re
with open('reconstruir_catalogos.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('ui.inventory_title')
if idx >= 0:
    with open('find_result.txt', 'w', encoding='utf-8') as f:
        f.write(content[max(0,idx-50):idx+100])
    print('FOUND')
else:
    with open('find_result.txt', 'w', encoding='utf-8') as f:
        f.write('NOT FOUND')
    print('NOT FOUND')