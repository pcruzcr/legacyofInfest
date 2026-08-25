with open('scripts/check_translations.py', 'rb') as f:
    content = f.read()
lines = content.splitlines()
for i, line in enumerate(lines[118:130], 119):
    print(f'{i+1}: indent={len(line) - len(line.lstrip())}, starts with tab: {line.startswith(b"\t")}')