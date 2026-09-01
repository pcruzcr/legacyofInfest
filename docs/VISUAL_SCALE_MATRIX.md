# VISUAL SCALE MATRIX — AUD-756 Fase 19

**Fecha:** 2026-09-01 · **Unidad:** `1 tile =16×16` · **Referencia:** Player `40×64` = `2.5×4` tiles

> `Expected` inferido de `tileset` + `TMX` + `spritesheets` + `GDD 4` (64_GDD). `UNSPECIFIED` donde no hay especificación y se justifica corrección solo si outlier.

| Element | Native px | Tiles | Reference | Expected | Status |
|---|---|---|---|---|---|
| **PLAYER** | `40×64` | `2.5×4` | `GDD 4` player 40×64 | `40×64` | PASS |
| Walker | `24×28` | `1.5×1.75` | `0.6× player H` | `24-32×28` | PASS |
| Brute | `32×32` | `2×2` | `0.8× player` | `32×32` | PASS |
| Charger | `28×24` | `1.75×1.5` | `0.7× player` | `28×24` | PASS |
| Flying | `20×14` | `1.25×0.87` | `0.5× player` | `20×14` | PASS |
| Archer | `24×28` | `1.5×1.75` | `walker` | — | PASS |
| Shielded | `28×24` | `1.75×1.5` | `charger` | — | PASS |
| Boss Venado | `128×96` | `8×6` | `3.2× player` `GDD boss 128` | `128×96` | PASS |
| Boss Rey | `96×96` | `6×6` | `2.4× player` | `96×96` | PASS |
| Boss Paburu | `64×96` | `4×6` | `1.6× player` `+ columnas 16×48` | `64×96` | PASS |
| Door | `32×48` | `2×3` | `0.75× player H` | `32×48` | PASS |
| Platform | `w×16` | `w/16×1` | `1 tile alto` | `w×16` | PASS |
| Chest | `32×24` | `2×1.5` | `0.8× player` | `32×24` | PASS |
| Pickup coin | `16×16` | `1×1` | `1 tile` | `16×16` | PASS |
| Tree ceibo | `64×96` | `4×6` | `1.6× player` | `64×96` | PASS |
| Rock | `32×32` | `2×2` | `0.5× player` | `32×32` | PASS |
| Torch | `radius 80` | `5` | `GDD light 80` | `80` | PASS |
| Background far | `1280×720` | `80×45` | `1 pantalla` | `1280×720` | PASS |
| Background mid 2× | `2560×720` | `160×45` | `2 pantallas` parallax | `2560×720` | PASS |
| Background near 3× | `3840×720` | `240×45` | `3 pantallas` | `3840×720` | PASS |
| HUD health bar | `96×16` | `6×1` | `MARGEN 24` | `96×16` | PASS |
| HUD icon | `16×16` | `1×1` | `ESCALA 3.0` | `16×16` | PASS |
| Boss bar | `400×24` | `25×1.5` | `GDD 400` | `400×24` | PASS |
| Minimap | `192×192` | `12×12` | `hud_builder 192` | `192×192` | PASS |
| Dialog | `1024×180` | `64×11` | `BOTTOM 24` | `1024×180` | PASS |

**Outliers:** Ninguno >`3×` player salvo Boss Venado `3.2×` intencional (arena `5280×720` = `4.1` pantallas, boss `128` cabe con cámara `80` tiles + `zoom` cinemático `1.25` en revelación, ver `72` `test_el_zoom_de_camara`).

**Pixel perfect:** `nearest` para tiles/sprites, `smoothscale` solo HUD icons `16` (no gameplay).
