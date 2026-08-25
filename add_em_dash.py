import sys
with open('reconstruir_catalogos.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add em dash handling
content = content.replace(
    '"Cualquier tecla": "Any key",\n\n# ',
    '"Cualquier tecla": "Any key",\n    "—": "—",\n\n# '
)

with open('reconstruir_catalogos.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')