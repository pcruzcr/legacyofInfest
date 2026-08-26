with open(r'C:\Users\pcruz\github\legacyofInfest\src\framework\entities\enemy_terrain_shaper.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: move from __future__ import annotations to top
old = '''import logging

logger = logging.getLogger(__name__)
"""
Module: enemy_terrain_shaper
System: framework.entities
Academic Unit: Unit IV (Terrain, Puzzles), Unit V (Materials)

Description: Enemy that creates/destroys terrain — PushBlock, BreakableBlock, HazardZone.
AUD-633 — arquetipo: modificador de terreno, puzzle dinámico.
"""

from __future__ import annotations'''

new = '''from __future__ import annotations

import logging

logger = logging.getLogger(__name__)
"""
Module: enemy_terrain_shaper
System: framework.entities
Academic Unit: Unit IV (Terrain, Puzzles), Unit V (Materials)

Description: Enemy that creates/destroys terrain — PushBlock, BreakableBlock, HazardZone.
AUD-633 — arquetipo: modificador de terreno, puzzle dinámico.
"""

from __future__ import annotations'''

content = content.replace(old, new)

with open(r'C:\Users\pcruz\github\legacyofInfest\src\framework\entities\enemy_terrain_shaper.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed')