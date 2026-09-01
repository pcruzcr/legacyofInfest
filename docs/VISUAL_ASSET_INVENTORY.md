# VISUAL ASSET INVENTORY — AUD-756 Fase 2

**Fecha:** 2026-09-01 · **Inventario completo de elementos visuales por espacio de coordenadas**

> Fuente: `src/framework/entities/*.py`, `src/engine/ui/*`, `assets/backgrounds/*.png` (Pillow), `assets/maps/*.tmx` (pytmx), `src/framework/stage/*`

---

## WORLD (tiles, terrain, plataformas — `WORLD SPACE`)

| Elemento | Archivo / TMX layer | Tamaño px | Tiles | Espacio | Nota |
|---|---|---|---|---|---|
| Tile base | `settings.TILE_SIZE 16` `TMX tilewidth 16` | `16×16` | `1×1` | WORLD | Unidad nativa |
| Terrain solid | `Collision` `Solid` | rect variable `w%16==0` `h%16==0` | `w/16 × h/16` | WORLD | `stage.collision_rects` |
| Platform one-way | `Collision` `Platform` | `w×16` | `w/16 ×1` | WORLD | `one_way_rects` |
| Slope | `Pendientes` `tileset` | `16×16` diag | `1×1` | WORLD | `pendientes.py` |
| Door | `interactables Cerradura` | `32×48` | `2×3` | WORLD | `src/framework/stage/interactables.py:19` |
| Ladder | `Tile layer + Liana` | `16×48` | `1×3` | WORLD | `src/framework/ecs/components Liana` |
| Hazard lava | `HazardZone` | `rect` `32×16` | `2×1` | WORLD | `_draw_zonas_de_dano` 165,45,35 |
| Breakable | `destructibles` | `16×16` | `1×1` | WORLD | `bloques` |
| Foreground overlay | `FG_Overlay` TMX `alpha 0.65` | `1280×720` | `80×45` | WORLD (alpha) | `informe_stage4_1b` |
| Background far | `assets/backgrounds/bg_*_far.png` | `1280×720` `2560×720` `3840×720` | `80×45` `160×45` `240×45` | WORLD parallax | `draw_background` wrap |

**WORLD total:** `80×45 =3600` tiles visibles, `~1280×720` px.

---

## ENTITIES (player, enemigos, bosses — `WORLD SPACE` → `CAMERA`)

| Entidad | Fuente | Sprite px | Tiles | Pivot | Hitbox / Collision | Espacio |
|---|---|---|---|---|---|---|
| **Player** | `player.py:421` `40×64` `hurtbox 20×28/18` | `40×64` | `2.5×4` | `rect midbottom` (pies) | `rect 40×64` / `hurtbox 20×28` offset 4 | WORLD |
| Walker | `enemy_walker.py` `24×28` | `24×28` | `1.5×1.75` | `midbottom` | `rect 24×28` | WORLD |
| Brute | `enemy_brute.py` `32×32` | `32×32` | `2×2` | `midbottom` | `rect 32×32` | WORLD |
| Charger | `enemy_charger.py` `28×24` | `28×24` | `1.75×1.5` | `midbottom` | `rect 28×24` | WORLD |
| Flying | `enemy_flying.py` `20×14` | `20×14` | `1.25×0.87` | `center` | `rect 20×14` | WORLD |
| Archer | `enemy_archer.py` `24×28` | `24×28` | `1.5×1.75` | `midbottom` | `rect` | WORLD |
| Caster | `enemy_caster.py` `24×32` | `24×32` | `1.5×2` | `midbottom` | `rect` | WORLD |
| Shielded | `enemy_shielded.py` `28×24` | `28×24` | `1.75×1.5` | `midbottom` | `rect 28×24` `shield 8×(h-4)` | WORLD |
| Boss Venado | `boss_venado.py` `128×96` `+ aura 140×140` | `128×96` | `8×6` | `midbottom` | `rect 128×96` `weakpoint 16×16` | WORLD |
| Boss Rey | `boss_rey.py` `96×96` | `96×96` | `6×6` | `midbottom` | `rect 96×96` | WORLD |
| Boss Paburu | `boss_paburu.py` `64×96` `+ columnas 16×48` | `64×96` | `4×6` | `midbottom` | `rect 64×96` | WORLD |
| Projectile | `projectile 8×8` | `8×8` | `0.5×0.5` | `center` | `8×8` | WORLD |
| Pickup coin | `recogibles` `16×16` | `16×16` | `1×1` | `center` | `16×16` | WORLD |
| Chest | `Cofre` `32×24` | `32×24` | `2×1.5` | `midbottom` | `32×24` | WORLD |

**Referencia Player:** `40×64` = `2.5×4` tiles. Todos los enemigos `0.8–2.0×` player altura, bosses `1.5–2.0×` player (Venado 1.5×, Paburu 1.0× + columnas). No outliers >3× salvo boss arena (12 tiles) intencional.

---

## ENVIRONMENT (árboles, rocas, luces — `WORLD` + `ATMOSPHERIC`)

| Elemento | Tamaño px | Tiles | Tipo parllax | Archivo |
|---|---|---|---|---|
| Tree ceibo | `64×96` | `4×6` | `WORLD` | `tileset_planicie.png` |
| Rock | `32×32` | `2×2` | `WORLD` | `tileset_jungle_stone.png` |
| Cementery cross | `16×32` | `1×2` | `WORLD` | `stage4_1` |
| Torch light | `radius 80` `color 255,220,180` | `5 tiles` | `LIGHT` `flicker` | `LightSystem` |
| Fog | `1280×720` overlay `alpha 0.35` | `80×45` | `ATMOSPHERIC` | `FogOfWar` |
| Particle leaf | `4×4` | `0.25×0.25` | `ATMOSPHERIC` `parallax 0.6` | `AmbientParticleSystem` |
| Wind zone | `rect` `160×720` | `10×45` | `WORLD` `friction 0.85` | `simulacion.py` |

---

## UI (HUD, menús — `UI SPACE` `1280×720` independiente de cámara)

| Elemento | Tamaño px | Tiles eq | Anchor | Espacio | Archivo |
|---|---|---|---|---|---|
| Retrato | `96×96` circular | `6×6` | `TOP_LEFT 24,24` | UI | `hud_builder.py:58` |
| Health bar | `96×16` | `6×1` | `TOP_LEFT 24,138` | UI | `hud.py` |
| Stamina bar | `96×16` | `6×1` | `TOP_LEFT stack` | UI | `hud.py` |
| Score/coins | `560×64` region | `35×4` | `TOP_CENTER cx-280` | UI | `hud_builder` |
| Timer `160×44` | `10×2.75` | `TOP_CENTER cx-260` | UI | `hud_builder` |
| Minimap | `192×192` circ | `12×12` | `TOP_RIGHT 24` | UI | `hud_builder` |
| Boss bar | `400×24` | `25×1.5` | `TOP_CENTER y=100` | UI | `hud.py` |
| Subtitle | `max 1024×48` | `64×3` | `BOTTOM_CENTER 24` | UI | `subtitle_overlay` |
| Dialog | `max 1024×180` | `64×11` | `BOTTOM_CENTER` | UI | `dialogue_system` |
| Inventory 3×3 grid | `480×360` | `30×22.5` | `CENTER` | UI | `scenes/inventory` |
| Pause tabs | `1280×20` | `80×1.25` | `TOP` | UI | `drawing_system` |
| Debug overlay | `1280×720` `alpha 180` | `80×45` | `SCREEN` | UI | `debug_overlay.py` |
| World map | `800×600` `escalado` | `50×37.5` | `CENTER` | UI | `world_map_scene` |

**UI total:** `0` elementos usan `camera.offset`; `grep hud.*camera` 0. `MARGEN 24` safe area `32` interna.

---

## Resumen espacios

- **WORLD:** `3600` tiles, `~40` entidades simultáneas, `1.2` densidad decorativa por viewport (`LEVEL_VISUAL_MATRIX`).
- **CAMERA:** `80×45` visibles, `24×24` decor por viewport promedio.
- **UI:** `192+96` HUD + `560` score — `~15%` viewport, dentro `safe 24`.
- **DISPLAY:** `letterbox` único, `nearest` world, `linear` light/bloom.
