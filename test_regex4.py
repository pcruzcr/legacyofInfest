import re

# Test with a simple string first
line35 = '    titulo = _("ui.inventory_title")  # \u2192 "INVENTARIO" (es) / "INVENTORY" (en)'
patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')
match = patron.search(line35)
with open("regex_test.txt", "w", encoding="utf-8") as out:
    if match:
        out.write(f"Match on test line: {match.group(1) or match.group(2)!r}\n")
    else:
        out.write("No match on test line\n")

    # Try the simpler regex
    match2 = re.search(r'"((?:[^"\\]|\\.)*)"', line35)
    if match2:
        out.write(f"Simple regex match: {match2.group(1)!r}\n")
    else:
        out.write("No match with simple regex\n")

    # Test on actual file content
    with open("src/engine/core/i18n.py", "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    line35_actual = lines[34]
    out.write(f"Actual line 35: {repr(line35_actual)}\n")

    match3 = re.search(r'"((?:[^"\\]|\\.)*)"', line35_actual)
    if match3:
        out.write(f"Match on actual line: {match3.group(1)!r}\n")
    else:
        out.write("No match on actual line 35\n")