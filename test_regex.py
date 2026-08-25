import re

texto = '''titulo = _("ui.inventory_title")  # → "INVENTARIO" (es) / "INVENTORY" (en)'''

patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[\'\\]|\\.)*)\'')
matches = list(patron.finditer(texto))
for m in patron.finditer(texto):
    val = m.group(1) if m.group(1) is not None else m.group(2)
    if 'inventory' in val:
        print(f'Found: {val!r} at pos {m.start()}')