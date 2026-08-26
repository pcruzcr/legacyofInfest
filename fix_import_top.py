import re

with open(r'C:\Users\pcruz\github\legacyofInfest\src\framework\entities\enemy_terrain_shaper.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ensure __future__ import is at the very top
if not content.startswith('from __future__ import annotations'):
    # Remove any existing __future__ import
    content = re.sub(r'from __future__ import annotations\s*\n', '', content)
    # Add at the very top
    content = 'from __future__ import annotations\n\n' + content
    
    with open(r'C:\Users\pcruz\github\legacyofInfest\src\framework\entities\enemy_terrain_shaper.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed: moved __future__ import to top')
else:
    print('Already at top')