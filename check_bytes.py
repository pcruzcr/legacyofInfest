with open("src/engine/core/i18n.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'inventory' in line.lower():
        print(f"Line {i}: {repr(line)}")

# Also check the exact bytes around the match
with open("src/engine/core/i18n.py", "rb") as f:
    raw = f.read()
idx = raw.find(b"ui.inventory_title")
if idx >= 0:
    context = raw[max(0, idx-60):idx+80]
    print(f"Raw context: {context}")