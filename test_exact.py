import re

with open("src/engine/core/i18n.py", "r", encoding="utf-8") as f:
    texto = f.read()

# Test the exact line
line35 = '    titulo = _("ui.inventory_title")  # \u2192 "INVENTARIO" (es) / "INVENTORY" (en)'
print(f"Test line: {repr(line35)}")

# Test regex on this line
patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')
match = patron.search(line35)
if match:
    print(f"Match on test line: {match.group(1) or match.group(2)!r}")
else:
    print("No match on test line")

# Try the simpler regex
match2 = re.search(r'"((?:[^"\\]|\\.)*)"', line35)
if match2:
    print(f"Simple regex match: {match2.group(1)!r}")
else:
    print("No match with simple regex")

# Test on actual file content
with open("src/engine/core/i18n.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find line 35
lines = content.splitlines()
line35_actual = lines[34]
print(f"\nActual line 35: {repr(line35_actual)}")

match3 = re.search(r'"((?:[^"\\]|\\.)*)"', line35_actual)
if match3:
    print(f"Match on actual line: {match3.group(1)!r}")
else:
    print("No match on actual line 35")