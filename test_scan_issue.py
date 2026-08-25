import re

# Test with errors=replace (as done in todos_los_literales)
with open("src/engine/core/i18n.py", "r", encoding="utf-8", errors="replace") as f:
    texto = f.read()

patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')
matches = list(patron.finditer(texto))

inventory_matches = []
for m in matches:
    val = m.group(1) if m.group(1) is not None else m.group(2)
    if 'inventory' in val:
        print(f"Found with errors=replace: {val!r}")

# Test without errors=replace
with open("src/engine/core/i18n.py", "r", encoding="utf-8") as f:
    texto2 = f.read()

matches2 = list(re.finditer(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'', texto2))
inventory_matches = [m for m in matches2 if 'inventory' in (m.group(1) or m.group(2) or '')]
print(f"Without errors=replace: {len(inventory_matches)} matches")
for m in inventory_matches:
    val = m.group(1) if m.group(1) is not None else m.group(2)
    print(f"  Found: {val!r}")