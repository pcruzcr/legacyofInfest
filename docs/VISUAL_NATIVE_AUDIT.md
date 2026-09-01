# VISUAL NATIVE AUDIT — AUD Final

**Fecha:** 2026-09-01 · **Grid nativa:** `1280×720` `80×45` `16×16` · **FROZEN:** `AUD-754..760` PASS

## 1. Unidad espacial real

```
Internal Resolution: 1280×720
Tile Size: 16×16
World Units: px (1 world px = 1 pixel interno)
Pixel Units: px (1:1 internal)
Camera Units: px (offset 1280×720)
Sprite Units: px (40×64 player)
HUD Units: px lógico 1280×720 (design 320×240 ×3.0)
Object Units: px world
Background Units: px world (parallax factor)
Parallax Units: factor 0.06/0.15/0.35/0.60
```

Relación matemática:

```
WORLD (tile*16) → CAMERA (world - offset) → VIEWPORT (1280×720 1:1) → DISPLAY (letterbox)
WORLD → OBJECT (x,y top-left px)
WORLD → SPRITE (rect top-left, feet midbottom)
VIEWPORT → HUD (anchor 1280×720 MARGEN 24)
```

No nuevas unidades necesarias.

## 2. Verificación

- `80*16=1280` `45*16=720` `settings.INTERNAL` `src/engine/core/settings.py:12`
- `TILE 16` `CULLING 1280` `ESCALA 3.0` `min(4.0,3.0)`
- `WORLD→CAMERA` `src/framework/stage/camera.py:299` `world - offset`
- `WORLD→OBJECT` `src/framework/stage/stage_loader.py:688` `Rect(obj.x, ...)`
- `WORLD→SPRITE` `player.py:421` `Rect(position,40,64)` `feet midbottom`
- `VIEWPORT→HUD` `hud_builder.py:37` `anchor TOP_LEFT 24,24`
- `WORLD→BACKGROUND` `draw_background` `shift_x=offset.x*factor%w`

## 3. Inventario

Ver `docs/VISUAL_ASSET_INVENTORY.md:1` 22 tipos `WORLD` `ENTITIES` `ENV` `UI`.

## 4. Estado

`NATIVE VISUAL` PASS — relación consistente `WORLD 16 → VIEWPORT 1280 → DISPLAY letterbox` sin `scale` intermedio.
