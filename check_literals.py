import re
import os

patron = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')
targets = ['Chain: Z Z X', 'Combo: -', 'Score: {score}', 'ACHIEVEMENT UNLOCKED: {name}', 'CANCEL', 'CONFIRM', 'SUBIR RANGO']

for root, dirs, files in os.walk('src/engine/scenes'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as fp:
                    content = fp.read()
                for m in patron.finditer(content):
                    val = m.group(1) if m.group(1) is not None else m.group(2)
                    for t in targets:
                        if t in val:
                            print(f'FOUND in {path}: {val!r}')
            except Exception as e:
                print(f'Error reading {path}: {e}')

# Also check src/engine/core
for root, dirs, files in os.walk('src/engine/core'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as fp:
                    content = fp.read()
                for m in patron.finditer(content):
                    val = m.group(1) if m.group(1) is not None else m.group(2)
                    for t in targets:
                        if t in val:
                            print(f'FOUND in {path}: {val!r}')
            except Exception as e:
                print(f'Error reading {path}: {e}')