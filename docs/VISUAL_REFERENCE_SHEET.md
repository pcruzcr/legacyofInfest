# VISUAL REFERENCE SHEET — AUD-758 Fase 22

**Fecha:** 2026-09-01 · **Grid nativa:** `1280×720` `80×45` `16×16` · **Player ref:** `40×64` `2.5×4`

> Registro consolidado de `native px`, `tiles`, `visual role`, `reference`, `status`. Fuente: `src/framework/entities/*.py`, `assets/backgrounds/*.png` (Pillow), `assets/maps/*.tmx`, `src/engine/ui/*`.

| Element | Native px `w×h` | Tiles `w×h` | Visual role | Reference | Status |
|---|---|---|---|---|---|
| **Player** | `40×64` | `2.5×4` | `PRIMARY` `3.1% W` `8.9% H` | `GDD 4` `player.py:421` | PASS |
| Walker | `24×28` | `1.5×1.75` | `0.60× player H` `enemy` | `enemy_walker.py` | PASS |
| Brute | `32×32` | `2×2` | `0.50× player` | `enemy_brute.py` | PASS |
| Charger | `28×24` | `1.75×1.5` | `0.38× player` | `enemy_charger.py` | PASS |
| Flying | `20×14` | `1.25×0.87` | `0.22× player` `air` | `enemy_flying.py` | PASS |
| Archer | `24×28` | `1.5×1.75` | `walker` | `enemy_archer.py` | PASS |
| Boss Venado | `128×96` | `8×6` | `3.2× player` `arena 4.1× vp` | `boss_venado.py` | PASS |
| Boss Rey | `96×96` | `6×6` | `2.4× player` | `boss_rey.py` | PASS |
| Boss Paburu | `64×96` | `4×6` | `1.5× player` `vertical 1312` | `boss_paburu.py` `col 16×48` | PASS |
| Door | `32×48` | `2×3` | `0.75× player H` `exit` | `interactables Cerradura` | PASS |
| Platform | `w×16` | `w/16×1` | `1 tile H` `walkable` | `TMX Platform` | PASS |
| Chest | `32×24` | `2×1.5` | `0.38× player` `pickup` | `Cofre` | PASS |
| Tree ceibo | `64×96` | `4×6` | `1.0× player` `env` | `tileset_planicie` | PASS |
| Rock | `32×32` | `2×2` | `0.5× player` | `tileset` | PASS |
| Torch light | `r 80` | `5` | `atmospheric` | `LightSystem` | PASS |
| Background far | `1280×720` | `80×45` | `STATIC` `1 screen` | `bg_*_far.png 1280` | PASS |
| Background mid `2×` | `2560×720` | `160×45` | `PARALLAX 0.35` `2 screens` | `bg_*_mid.png 2560` | PASS |
| Background near `3×` | `3840×720` | `240×45` | `PARALLAX 0.60` `3 screens` | `bg_*_near.png 3840` | PASS |
| HUD health | `96×16` | `6×1` | `TOP_LEFT` `MARGEN 24` | `hud_builder 96` | PASS |
| HUD minimap | `192×192` | `12×12` | `TOP_RIGHT` `circ` | `hud_builder 192` | PASS |
| Boss bar | `400×24` | `25×1.5` | `TOP_CENTER y 100` | `hud.py` | PASS |
| Dialog | `1024×180` | `64×11` | `BOTTOM_CENTER 24` | `dialogue_system` | PASS |

**Pixel-art consistency:** `nearest` para `tiles/sprites` `16×16` (ver `drawing_system.py:836` `scale` nearest), `linear` solo `lightmap/bloom` (baja frecuencia) — `grep smoothscale` solo `hud/icons` y `2.5D` depth `836` permitido.

**Cross-level consistency:** `Walker 24×28` en `stage0` `stage1_1` `stage4_1` idéntico; `Door 32×48` todas; `Platform 16` todos; `HUD 96×16` todas.

**Status:** 22/22 `PASS` — escala intencional, no outliers.
