import sys

with open('C:/Users/pcruz/github/legacyofInfest/tools/pixel_asset_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []
inserted = False

for i, line in enumerate(lines):
    new_lines.append(line)
    if not inserted and line.strip() == '# ── CONSTANTS ─────────────────────────────────────────────────────':
        new_lines.append('')
        new_lines.append('# ── NEW MODULE IMPORTS ──────────────────────────────────────────────')
        new_lines.append('from sprite_atlas import SpriteAtlas, export_godot_spriteframes, export_texturepacker')
        new_lines.append('from directional_sprites import DirectionalSpriteGenerator, generate_walk_cycle')
        new_lines.append('from animation_tween import (create_smooth_animation, create_smooth_walk_cycle, ')
        new_lines.append('                              create_attack_animation, interpolate_images)')
        new_lines.append('from animation_tween import EASING_FUNCTIONS')
        new_lines.append('from sprite_postprocess import (chroma_key_remove, extract_frames_from_sheet, ')
        new_lines.append('                                 align_frames, slice_prop_pack)')
        new_lines.append('from atlas_packer import SpriteAtlas, export_godot_spriteframes, export_texturepacker')
        new_lines.append('')
        inserted = True

# Replace the docstring
content = '\n'.join(new_lines)
content = content.replace(
    '''"""
Pixel Art Asset Generator - Legacy of InFest
NVG/Castlevania style, 16-bit color, procedural generation with fixed palettes.
Generates all game assets from code with style-consistency guarantees.
"""''',
    '''"""
Pixel Art Asset Generator - Legacy of InFest
NVG/Castlevania style, 16-bit color, procedural generation with fixed palettes.
Generates all game assets from code with style-consistency guarantees.

NEW FEATURES (AUD-612):
- Sprite Atlas + Manifest.json (TexturePacker, Godot, Unity compatible)
- Multi-directional sprites (S/N/E/W) 
- Animation tweening/interpolation (easing functions)
- Chroma-key + frame extraction (post-processing)
- MaxRects atlas packing (MaxRects bin packing)
- Procedural walk cycles
- Export: Godot SpriteFrames, Unity SpriteAtlas, TexturePacker, Aseprite
- Curation webview (optional, for frame curation)
"""''')

with open('tools/pixel_asset_generator.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines) if inserted else content)

print('Done')