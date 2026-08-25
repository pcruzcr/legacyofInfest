import json
with open('locale/es.json', 'r', encoding='utf-8') as f:
    es = json.load(f)
with open('locale/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

# Check what the code actually uses
# From keybinding_scene.py: "Chain: Z → Z → X" (Unicode arrow)
# From combo_demo_scene.py: "Combo: —" (em dash)
# From quiz_system.py: "  {current}/{total}  |  Score: {score}" (full string)

# Check exact presence
with open('check_exact.txt', 'w', encoding='utf-8') as out:
    for k in ['Chain: Z \u2192 Z \u2192 X', 'Combo: \u2014', '  {current}/{total}  |  Score: {score}']:
        out.write(f'{repr(k)}: es={k in es}, en={k in en}\n')