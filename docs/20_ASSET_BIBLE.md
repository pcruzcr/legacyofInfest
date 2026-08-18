---
document_id: "LOI-ASSET-020"
title: "Legacy of InFest — Biblia de recursos"
aliases: ["Biblia de recursos", "Asset Bible"]
tags: ["asset", "recursos", "arte", "audio"]
description: "Cada recurso visual/de audio, su ruta, dimensiones y paleta"
source: "docs/20_ASSET_BIBLE.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Biblia de recursos

**ID del documento:** LOI-ASSET-020
**Versión:** 1.1.0
**Estado:** Oficial
**Compatibilidad:** Requiere `16_WORLD_DESIGN.md`, `17_BOSS_SPEC.md`, `18_ENEMY_ROSTER.md`
**Audiencia:** Profesor, estudiantes, artistas, asistentes de programación con IA

> **AUD-455.** Traduce el documento (tenía el cuerpo completo en inglés y un
> resumen condensado en español duplicado al final, con datos que no
> coincidían entre sí). Corrige dos discrepancias reales entre ambas
> versiones, en favor de la que coincide con el código:
> - **Resolución interna:** el cuerpo en inglés decía «800×600 internal
>   render» y el resumen en español decía «320x224» — son
>   `INTERNAL_WIDTH`/`INTERNAL_HEIGHT` de `settings.py` (ver
>   `22_API_CONTRACTS.md` §2.1), y valen **800×600**. El 320×224 es la
>   resolución antigua, ya retirada (ver los commits recientes AUD-450 a
>   AUD-454 sobre la maquetación fija a 320×224).
> - **Fotogramas de animación del jugador:** el cuerpo en inglés decía
>   `player_jump.png` 4 fotogramas, `player_fall.png` 3, `player_crouch.png`
>   3; el resumen en español decía 3, 2 y 2. Verificado contra
>   `PLAYER_ANIM_MAP` en `src/framework/entities/player.py`: gana el
>   resumen — **3, 2 y 2** son los valores reales.
>
> **AUD-455 (2026-08-13).** §3 (árbol de directorios) listaba `assets/music/`
> con extensión `.ogg`, contradiciendo a §11 unas líneas más abajo, que ya
> documentaba correctamente que las pistas se guardan como **`.wav`** hoy.
> Confirmado contra `stage_scene.py`: la carga real intenta `.wav` primero y
> sólo cae a `.ogg` si el `.wav` no existe. Corregido el árbol de §3 para que
> coincida con §11 y con el código.

---

## 1. Visión general

Este documento define cada recurso visual y de audio que necesita Legacy of InFest. Es la referencia autoritativa para artistas, estudiantes que crean recursos propios, y asistentes de programación con IA que generan código de carga de recursos.

Cada recurso listado aquí tiene ruta, formato, dimensiones, restricciones de paleta y contexto de uso definidos. Los recursos que no aparecen aquí, o bien los crean los estudiantes (en `student_assets/`), o bien los genera en tiempo de ejecución la tubería de procesamiento.

---

## 2. Estándares globales de recursos

### 2.1 Estándares visuales

| Propiedad | Estándar |
|---|---|
| Formato de píxel | PNG con canal alfa (RGBA) |
| Profundidad de color | 8 bits por canal |
| Restricción de paleta | Máximo 16 colores por hoja de sprites |
| Paleta global | Máximo 256 colores en todo el juego |
| Tamaño de píxel | 1:1 — sin renderizado de subpíxeles |
| Anti-aliasing | Nunca |
| Transparencia | Binaria (totalmente transparente u opaca) O alfa suave (sólo para efectos) |
| Resolución interna | Todos los recursos se diseñan para el render interno de 800×600 |

### 2.2 Formato de hoja de sprites

Todos los sprites animados son **hojas de sprites horizontales**: fotogramas dispuestos de izquierda a derecha, mismo ancho, origen en la esquina superior izquierda.

```
[Fotograma 0][Fotograma 1][Fotograma 2][Fotograma 3]...
```

Ancho de la hoja = ancho_fotograma × número_fotogramas
Alto de la hoja = alto_fotograma (una sola fila — sin hojas multifila)

### 2.3 Formato de baldosas (tiles)

| Propiedad | Estándar |
|---|---|
| Tamaño de baldosa | 16×16 píxeles |
| Disposición de hoja | Cuadrícula por filas |
| Máximo de baldosas por conjunto | 256 |
| Dimensiones de hoja | 128×128 px (cuadrícula de 8×8 baldosas) |

### 2.4 Estándares de audio

| Propiedad | Música | SFX |
|---|---|---|
| Formato | OGG Vorbis | WAV u OGG |
| Frecuencia de muestreo | 44100 Hz | 22050 Hz |
| Profundidad de bits | 16 bits | 16 bits |
| Canales | Estéreo | Mono |
| Punto de bucle | Obligatorio en BGM | N/D |
| Normalización de volumen | Pico -12 dBFS | Pico -6 dBFS |

---

## 3. Estructura de directorios

```
assets/
├── sprites/
│   ├── player/
│   ├── enemies/
│   │   ├── zone1/
│   │   ├── zone2/
│   │   └── zone3/
│   ├── bosses/
│   └── shared/
│       ├── torch_anim.png
│       ├── fountain_anim.png
│       └── spirit_echo_overlay.png
├── tilesets/
│   ├── tileset_stage0.png
│   ├── tileset_jungle_stone.png
│   ├── tileset_cafeteria.png
│   ├── tileset_aulas.png
│   ├── tileset_datacenter.png
│   ├── tileset_heredia_stone.png
│   ├── tileset_heredia_interior.png
│   └── tileset_cemetery.png
├── backgrounds/
│   ├── stage0/
│   ├── zone1/
│   ├── zone2/
│   ├── zone3/
│   └── final/
├── ui/
│   ├── portrait_normal.png
│   ├── portrait_hurt.png
│   ├── portrait_critical.png
│   ├── portrait_dead.png
│   ├── banner_top.png
│   ├── banner_bottom.png
│   ├── hud_frame.png
│   ├── message_arrow.png
│   ├── menu_arrow.png
│   ├── heart_sparkle.png
│   └── relics/
│       ├── relic_pepita.png
│       ├── relic_perla.png
│       ├── relic_fragment1.png
│       ├── relic_fragment2.png
│       └── relic_fragment3.png
├── fonts/
│   ├── hud_digits.png
│   ├── message_font.png
│   ├── banner_large.png
│   ├── banner_medium.png
│   ├── gameover_font.png
│   └── menu_font.png
├── music/                       # .wav hoy en disco; StageScene cae a .ogg si el .wav no existe (§11)
│   ├── bgm_splash.wav
│   ├── bgm_title.wav
│   ├── bgm_story.wav
│   ├── bgm_stage0.wav
│   ├── bgm_zone1_traverse.wav
│   ├── bgm_zone1_boss.wav
│   ├── bgm_zone2_traverse.wav
│   ├── bgm_zone2_boss.wav
│   ├── bgm_zone3_traverse.wav
│   ├── bgm_zone3_boss.wav
│   ├── bgm_final_approach.wav
│   └── bgm_paburu.wav
└── sfx/
    ├── player/
    ├── enemies/
    ├── bosses/
    ├── ui/
    └── environment/
```

---

## 4. Sprites del jugador

Todos los sprites del jugador están en `assets/sprites/player/`.
Tamaño de fotograma: **32×32 píxeles** en todas las animaciones.

| Fichero | Fotogramas | FPS | Bucle | Estado |
|---|---|---|---|---|
| `player_idle.png` | 4 | 8 | Sí | IDLE |
| `player_walk.png` | 8 | 12 | Sí | WALKING |
| `player_jump.png` | 3 | 12 | No (mantiene el último) | JUMPING |
| `player_fall.png` | 2 | 8 | Sí | FALLING |
| `player_crouch.png` | 2 | 8 | No (mantiene el último) | CROUCHING |
| `player_short_attack.png` | 6 | 18 | No | SHORT_ATTACK |
| `player_long_attack.png` | 10 | 16 | No | LONG_ATTACK |
| `player_hurt.png` | 4 | 12 | No | HURT |
| `player_die.png` | 8 | 10 | No | DYING |
| `player_swim.png` | 4 | 10 | Sí | SWIMMING |

`player_swim.png` (AUD-525) alterna una patada abierta con la silueta
cerrada del salto — antes `SWIMMING` reutilizaba `player_jump.png` sin
variación entre fotogramas, así que nadar se veía como quedarse de pie
clavado bajo el agua.

**Paleta:**
El jugador (protagonista encapuchado) usa una paleta restringida de exactamente 12 colores:
- 3 tonos de sombra de capucha (gris azulado oscuro, medio, gris claro)
- 2 tonos de piel (canela cálida, sombra)
- 2 tonos de tela (azul marino oscuro, medio)
- 2 tonos de cuerda/cinturón (marrón, marrón oscuro)
- 1 brillo de ojos (dorado pálido — visible sólo en escenas muy oscuras)
- 1 negro puro (contorno)
- 1 transparente puro

---

## 5. Sprites de enemigos

Los sprites de enemigos usan nombres genéricos por zona. Las variantes
temáticas por zona son aspiracionales; los sprites que existen en disco se
comparten entre todos los tipos de enemigo de una zona y usan el prefijo del
tipo concreto (`walker`, `fly`, `shoot`).

### 5.1 Walker (universal)

Ubicación: `assets/sprites/enemies/`

| Fichero | Enemigo | Tamaño de fotograma | Fotogramas | FPS | Bucle |
|---|---|---|---|---|---|
| `enemy_walker_walk.png` | Walker | 20×16 | 6 | 10 | Sí |

### 5.2 Enemigos con sprite por zona

Ubicación: `assets/sprites/enemies/zoneN/`

| Fichero | Enemigo | Fotogramas | FPS |
|---|---|---|---|
| `enemy_zoneN_walk.png` | Walker de zona | 6 | 10 |
| `enemy_zoneN_hurt.png` | Cualquiera (daño) | 3 | 12 |
| `enemy_zoneN_die.png` | Cualquiera (muerte) | 5 | 8 |
| `enemy_fly_zoneN.png` | Volador de zona | 4 | 12 |
| `enemy_shoot_zoneN.png` | Disparador de zona | 4 | 6 |

Donde `N` es el número de zona (1–3). Todos los sprites usan tamaño de
fotograma 16×16 (marcador de posición; el tamaño real depende del reemplazo
temático).

---

## 6. Sprites de jefes

Ubicación: `assets/sprites/bosses/`

### 6.1 El Venado Sagrado

Tamaño de fotograma: 48×48 px

| Fichero | Fotogramas | FPS | Bucle | Estado |
|---|---|---|---|---|
| `boss_venado_drift.png` | 6 | 8 | Sí | ✅ |
| `boss_venado_stomp.png` | 8 | 12 | No | ✅ |
| `boss_venado_charge.png` | 6 | 14 | No | ✅ |
| `boss_venado_frenzy_drift.png` | 6 | 14 | Sí | ✅ |
| `boss_venado_vine.png` | 10 | 12 | No | ✅ |
| `boss_venado_hurt.png` | 4 | 12 | No | ✅ |
| `boss_venado_death.png` | 12 | 8 | No | ✅ |
| `boss_venado_skull.png` | 1 | — | — | ⚠️ Marcador de posición |
| `boss_venado_proyectil_vine.png` | 4 | 10 | Sí | ⚠️ Marcador de posición |

**Notas de paleta:** blanco hueso (`#E8DCC8`), musgo oscuro (`#2D4A1E`), musgo medio (`#4A7832`), tierra (`#6B4423`), crema hongo (`#C8B896`), negro escarabajo (`#0A0A0A`), tostado raíz (`#8C6E3C`), sombra (`#1A1A2E`) + transparente.

### 6.2 El Rey Terciopelo

Tamaño de fotograma Fase 1: 40×56 px. Sub-jefe (Fase 2): 24×28 px.

| Fichero | Fotogramas | FPS | Bucle | Estado |
|---|---|---|---|---|
| `boss_rey_walk.png` | 8 | 10 | Sí | ✅ |
| `boss_rey_spit.png` | 6 | 12 | No | ✅ |
| `boss_rey_split.png` | 8 | 10 | Sí | ✅ |
| `boss_rey_metad_walk.png` | 6 | 12 | Sí | ⚠️ Marcador de posición |
| `boss_rey_merge.png` | 6 | 8 | No | ✅ |
| `boss_rey_rampage.png` | 8 | 16 | Sí | ✅ |
| `boss_rey_hurt.png` | 4 | 12 | No | ✅ |
| `boss_rey_death.png` | 14 | 8 | No | ✅ |
| `boss_rey_venom_glob.png` | 3 | 8 | Sí | ⚠️ Marcador de posición |

**Notas de paleta:** terciopelo tostado (`#C8A264`), terciopelo oscuro (`#4A3218`), terciopelo medio (`#8C6432`), gris descomposición (`#7D7D7D`), gris oscuro descomposición (`#3C3C3C`), verde veneno (`#32A050`), verde veneno brillante (`#50C878`), sombra (`#0A0A14`).

### 6.3 El Gavilán Camionero Mascarero

Tamaño de fotograma: 56×40 px (ancho — envergadura)

| Fichero | Fotogramas | FPS | Bucle | Estado |
|---|---|---|---|---|
| `boss_gavilan_glide.png` | 8 | 10 | Sí | ✅ |
| `boss_gavilan_dive.png` | 6 | 16 | No | ✅ |
| `boss_gavilan_hover.png` | 4 | 8 | Sí | ✅ |
| `boss_gavilan_storm.png` | 8 | 12 | No | ✅ |
| `boss_gavilan_masked.png` | 6 | 14 | Sí | ✅ |
| `boss_gavilan_hurt.png` | 4 | 12 | No | ✅ |
| `boss_gavilan_death.png` | 16 | 8 | No | ✅ |
| `boss_gavilan_mask_frag.png` | 4 | 12 | No | ⚠️ Marcador de posición |
| `boss_gavilan_feather.png` | 3 | 10 | Sí | ⚠️ Marcador de posición |

**Notas de paleta:** marrón halcón (`#8C5A28`), tostado halcón (`#C88C3C`), blanco halcón (`#E8DCC8`), oro máscara (`#D4A017`), oro oscuro máscara (`#8C6800`), verde azulado máscara (`#1E6B6B`), naranja rojizo máscara (`#D45A00`), brillo de ojos (`#50FF50`), negro sombra (`#0A0A0A`).

### 6.4 El Gran Chamán Paburu

Varios tamaños de fotograma según la forma.

| Fichero | Forma | Tamaño de fotograma | Fotogramas | FPS | Bucle | Estado |
|---|---|---|---|---|---|---|
| `boss_paburu_stone.png` | 1 | 64×64 | 4 | 6 | Sí | ✅ |
| `boss_paburu_stone_slam.png` | 1 | 64×64 | 8 | 12 | No | ✅ |
| `boss_paburu_stone_crack.png` | 1→2 | 64×64 | 8 | 8 | No | ⚠️ Marcador de posición |
| `boss_paburu_mask.png` | 2 | 56×72 | 6 | 10 | Sí | ✅ |
| `boss_paburu_mask_wave.png` | 2 | 56×72 | 8 | 12 | No | ⚠️ Marcador de posición |
| `boss_paburu_gold.png` | 3A | 32×32 | 6 | 14 | Sí | ✅ |
| `boss_paburu_black.png` | 3B | 32×32 | 6 | 14 | Sí | ✅ |
| `boss_paburu_relic_atk.png` | 3A/B | 32×32 | 10 | 14 | No | ⚠️ Marcador de posición |
| `boss_paburu_spirit.png` | 4 | 64×80 | 8 | 10 | Sí | ✅ |
| `boss_paburu_spirit_surge.png` | 4 | 64×80 | 12 | 14 | No | ⚠️ Marcador de posición |
| `boss_paburu_hurt.png` | Todas | 64×64 | 4 | 12 | No | ✅ |
| `boss_paburu_transcend.png` | Muerte | 64×64 | 20 | 8 | No | ⚠️ Marcador de posición |
| `boss_paburu_stone_proyectil.png` | Forma 1 | 8×8 | 3 | 8 | Sí | ⚠️ Marcador de posición |
| `boss_paburu_gold_orb.png` | Forma 3A | 6×6 | 3 | 12 | Sí | ⚠️ Marcador de posición |
| `boss_paburu_black_orb.png` | Forma 3B | 6×6 | 3 | 12 | Sí | ⚠️ Marcador de posición |

**Notas de paleta — Forma 1 (Piedra):** verde piedra (`#3C6432`), verde piedra medio (`#5A8C50`), verde piedra claro (`#8CB496`), sombra de talla (`#1E3C1E`), brillo de ojos verde (`#50FF50`), acento musgo (`#2D5A28`), contorno (`#0A0A0A`).

**Notas de paleta — Forma 2 (Espectral):** verde espectral brillante (`#50FF78`), verde espectral medio (`#28C850`), verde espectral oscuro (`#0A6428`), verde azulado máscara (`#1E8C8C`), oro máscara (`#D4A017`), blanco espíritu (`#E8FFE8`), negro vacío (`#000000`), blanco brillo (`#FFFFFF`).

**Notas de paleta — Forma 3A (Oro):** oro brillante (`#FFD700`), oro medio (`#C8A800`), oro oscuro (`#8C7000`), sombra oro (`#3C3200`), blanco energía (`#FFFFF0`), negro contorno (`#1A1000`).

**Notas de paleta — Forma 3B (Perla):** negro perla (`#0A0A14`), brillo oscuro perla (`#1E1E3C`), medio perla (`#3C3C64`), brillo perla (`#7878A0`), centro vacío (`#000000`), contorno (`#5A5A8C`).

---

## 7. Tilesets

Ubicación: `assets/tilesets/`

| Fichero | Se usa en | Tema | Tamaño |
|---|---|---|---|
| `tileset_stage0.png` | Stage 0 | Corredor de piedra neutral | 1024×1024 |
| `tileset_jungle_stone.png` | Zona 1, escenarios 1-1, 1-4 | Jungla de montaña con piedra | 128×128 |
| `tileset_cafeteria.png` | Zona 1, escenario 1-2 | Cafetería interior, piso ajedrezado | 128×128 |
| `tileset_aulas.png` | Zona 1, escenario 1-3 | Interior de aula, madera y yeso | 128×128 |
| `tileset_planicie.png` | Zona 2, escenario 2-1 | Llanura agrícola abierta | 128×128 |
| `tileset_datacenter_ext.png` | Zona 2, escenario 2-2 | Exterior de concreto, antenas | 128×128 |
| `tileset_datacenter.png` | Zona 2, escenarios 2-3, 2-4 | Piso de acero, mamparas de vidrio, servidores | 128×128 |
| `tileset_heredia_stone.png` | Zona 3, escenarios 3-1, 3-4 | Sendero de piedra y arquitectura de bungaló | 128×128 |
| `tileset_heredia_interior.png` | Zona 3, escenarios 3-2, 3-3 | Salón interior, patio | 128×128 |
| `tileset_cemetery.png` | Zona Final | Lápidas, tallas ceremoniales | 128×128 |

### 7.1 Categorías de baldosas del tileset

Cada tileset debe contener baldosas organizadas en las siguientes categorías (columnas):

| Columna | Categoría | Descripción |
|---|---|---|
| 0–1 | Suelo sólido | Superficie principal transitable |
| 2–3 | Pared sólida | Paredes izquierda y derecha |
| 4–5 | Borde de plataforma | Borde izquierdo/derecho de plataformas |
| 6 | Techo de plataforma | Superficie de plataforma de un solo sentido |
| 7 | Esquina sólida | Esquinas interiores |
| 8–9 | Superposición decorativa | Baldosas decorativas no sólidas |
| 10–11 | Relleno de fondo | Se usa en las capas BG |
| 12–15 | Especial/Entorno | Específico de zona (enredaderas, servidores, antenas, tumbas) |

---

## 8. Capas de fondo

Ubicación: `assets/backgrounds/`

Cada escenario necesita tres capas de fondo, con nombre `bg_<zona>_far.png`, `bg_<zona>_mid.png` y `bg_<zona>_near.png`. Las dimensiones deben igualar o superar el ancho del mapa del escenario × 224px. El conjunto de Stage 0 es la excepción, a 800×600 (la resolución interna del juego).

### 8.1 Stage 0

| Fichero | Capa | Tamaño | Parallax |
|---|---|---|---|
| `stage0/bg_stage0_far.png` | BG_Far | 800×600 | 0.15× |
| `stage0/bg_stage0_mid.png` | BG_Mid | 800×600 | 0.40× |
| `stage0/bg_stage0_near.png` | BG_Near | 800×600 | 0.70× |

Cada zona usa un único conjunto de fondo genérico que carga `StageLoader`
con el patrón `bg_{zone}_{layer}.png` (p. ej. `bg_zone1_far.png`). Las
variantes temáticas de fondo (cafetería, aulas, planicie, etc.) son
aspiracionales; todos los escenarios de una zona comparten hoy el mismo
fondo genérico.

### 8.2 Zona 1

| Fichero | Capa | Tamaño |
|---|---|---|
| `zone1/bg_zone1_far.png` | BG_Far | 320×224 |
| `zone1/bg_zone1_mid.png` | BG_Mid | 640×224 |
| `zone1/bg_zone1_near.png` | BG_Near | 960×224 |

### 8.3 Zona 2

| Fichero | Capa | Tamaño |
|---|---|---|
| `zone2/bg_zone2_far.png` | BG_Far | 320×224 |
| `zone2/bg_zone2_mid.png` | BG_Mid | 640×224 |
| `zone2/bg_zone2_near.png` | BG_Near | 960×224 |

### 8.4 Zona 3

| Fichero | Capa | Tamaño |
|---|---|---|
| `zone3/bg_zone3_far.png` | BG_Far | 320×224 |
| `zone3/bg_zone3_mid.png` | BG_Mid | 640×224 |
| `zone3/bg_zone3_near.png` | BG_Near | 960×224 |

### 8.5 Zona Final

| Fichero | Capa | Tamaño |
|---|---|---|
| `final/bg_final_far.png` | BG_Far | 320×224 |
| `final/bg_final_mid.png` | BG_Mid | 640×224 |
| `final/bg_final_near.png` | BG_Near | 960×224 |

**Paleta de fondo del cementerio:** negro púrpura profundo (`#0A0014`), piedra de cementerio (`#4A4A5A`), brillo verde espíritu (`#28C850`), luz de luna pálida (`#C8D4C8`), tierra oscura (`#1E1410`).

---

## 9. Sprites de UI

Ubicación: `assets/ui/`

| Fichero | Tamaño | Descripción |
|---|---|---|
| `portrait_normal.png` | 32×32 | Retrato del jugador — neutral |
| `portrait_hurt.png` | 32×32 | Retrato del jugador — expresión de dolor |
| `portrait_critical.png` | 32×32 | Retrato del jugador — salud crítica |
| `portrait_dead.png` | 32×32 | Retrato del jugador — fallecido |
| `banner_top.png` | 320×24 | Mitad superior del banner de entrada de escenario |
| `banner_bottom.png` | 320×24 | Mitad inferior del banner de entrada de escenario |
| `hud_frame.png` | 36×36 | Marco de retrato (9-slice) |
| `message_arrow.png` | 5×7 | Flecha animada de confirmar (2 fotogramas) |
| `menu_arrow.png` | 5×8 | Flecha de selección de menú |
| `heart_sparkle.png` | 8×8 | Brillo de restauración de corazón (4 fotogramas, 12 FPS) |
| `heart_full.png` | 14×8 | Corazón lleno |
| `heart_three_quarter.png` | 14×8 | Corazón tres cuartos |
| `heart_half.png` | 14×8 | Corazón medio |
| `heart_quarter.png` | 14×8 | Corazón un cuarto |
| `heart_empty.png` | 14×8 | Contorno de corazón vacío |
| `relic_pepita.png` | 8×6 | Icono de HUD de la pepita de oro (animado, 3 fotogramas) |
| `relic_perla.png` | 7×7 | Icono de HUD de la perla negra (animado, 3 fotogramas) |
| `relic_fragment1.png` | 12×12 | Fragmento de reliquia 1 (cornamenta) — Zona 1 superada |
| `relic_fragment2.png` | 12×12 | Fragmento de reliquia 2 (espiral) — Zona 2 superada |
| `relic_fragment3.png` | 12×12 | Fragmento de reliquia 3 (máscara) — Zona 3 superada |

---

## 10. Fuentes

Ubicación: `assets/fonts/`

Todas las fuentes son hojas de sprites de mapa de bits (horizontales, una fila por conjunto de caracteres).

| Fichero | Tamaño de carácter | Conjunto de caracteres | Uso |
|---|---|---|---|
| `hud_digits.png` | 6×8 | `0-9 : ` (12 caracteres) | Cronómetro del HUD |
| `message_font.png` | 5×7 | ASCII imprimible (96 caracteres) | Mensajes de tutorial |
| `banner_large.png` | 10×14 | A-Z 0-9 espacio (37 caracteres) | Número de escenario en el banner |
| `banner_medium.png` | 6×9 | A-Z a-z 0-9 espacio .:- (66 caracteres) | Nombre de escenario en el banner |
| `gameover_font.png` | 12×16 | A-Z espacio (27 caracteres) | Texto de GAME OVER |
| `menu_font.png` | 6×9 | ASCII imprimible (96 caracteres) | Opciones de menú |

---

## 11. Pistas de música

Ubicación: `assets/music/`

Todas las pistas se guardan como **WAV** (no OGG). `stage_scene.py`, del motor,
carga la música vía `assets/music/{bgm_track}.wav`. La conversión a OGG queda
pendiente hasta la tubería de recursos final.

| Fichero | Se usa en | Ambiente | Bucle |
|---|---|---|---|
| `bgm_splash.wav` | Pantalla de presentación | Ambiental, breve | No |
| `bgm_title.wav` | Pantalla de título | Heroico, acogedor | Sí |
| `bgm_story.wav` | Pantallas de historia 1-3 | Atmosférico, misterioso | Sí |
| `bgm_stage0.wav` | Stage 0 | Tenso, instructivo | Sí |
| `bgm_zone1_traverse.wav` | Escenarios de Zona 1 | Percusión de jungla, tensión húmeda | Sí |
| `bgm_zone1_boss.wav` | Escenario 1-4 (Venado) | Espíritu de bosque, ritmo ancestral | Sí |
| `bgm_zone2_traverse.wav` | Escenarios de Zona 2 | Zumbido electrónico, industrial | Sí |
| `bgm_zone2_boss.wav` | Escenario 2-4 (Rey) | Susurro colectivo, metálico | Sí |
| `bgm_zone3_traverse.wav` | Escenarios de Zona 3 | Aéreo, tensión de cacería | Sí |
| `bgm_zone3_boss.wav` | Escenario 3-4 (Gavilán) | Aleteo, ceremonial | Sí |
| `bgm_final_approach.wav` | Escenario 4-1 | Silencio puntuado por tambores rituales | Sí |
| `bgm_paburu.wav` | Escenario 4-2 | Pista adaptativa de cuatro partes (una sección por forma) | Sí |

**`bgm_paburu.wav` — nota adaptativa:** esta pista tiene un punto de bucle que `AudioManager` avanza manualmente en cada evento `BOSS_PHASE_CHANGED` de Paburu. La pista tiene cuatro secciones internamente consistentes, cada una con bucle independiente. El método `AudioManager.advance_music_section()` (específico de Paburu) salta al punto de bucle de la siguiente sección.

---

## 12. Efectos de sonido

Ubicación: `assets/sfx/`

### 12.1 SFX del jugador

| Fichero | Disparador |
|---|---|
| `player/sfx_player_jump.wav` | Acción de saltar |
| `player/sfx_player_land.wav` | Aterrizaje tras una caída |
| `player/sfx_player_short_attack.wav` | Golpe de ataque corto |
| `player/sfx_player_long_attack.wav` | Golpe de ataque largo |
| `player/sfx_player_hit_connect.wav` | El ataque del jugador conecta con un enemigo |
| `player/sfx_player_hurt.wav` | El jugador recibe daño |
| `player/sfx_player_die.wav` | Muerte del jugador |
| `player/sfx_player_crouch.wav` | Inicio de agacharse |

### 12.2 SFX de enemigos

Todas las rutas relativas a `assets/sfx/enemies/`.

| Fichero | Disparador |
|---|---|
| `sfx_enemies_hit.wav` | Cualquier enemigo recibe daño |
| `sfx_enemies_die_small.wav` | Enemigos pequeños (salud ≤ 1.0) |
| `sfx_enemies_die_large.wav` | Enemigos grandes (salud ≥ 2.0) |
| `sfx_enemies_projectile_fire.wav` | Se dispara cualquier proyectil |
| `sfx_enemies_projectile_hit_wall.wav` | El proyectil golpea terreno |

### 12.3 SFX de jefes

Todas las rutas relativas a `assets/sfx/bosses/`.

| Fichero | Disparador |
|---|---|
| `sfx_bosses_venado_stomp.wav` | Pisotón del Venado |
| `sfx_bosses_venado_charge.wav` | Embestida del Venado |
| `sfx_bosses_venado_vine.wav` | Lanzamiento de enredadera del Venado |
| `sfx_bosses_rey_spit.wav` | Escupitajo de veneno del Rey |
| `sfx_bosses_rey_split.wav` | División del Rey en Fase 2 |
| `sfx_bosses_gavilan_dive.wav` | Picado del Gavilán |
| `sfx_bosses_gavilan_mask_beam.wav` | Rayo de máscara del Gavilán |
| `sfx_bosses_paburu_eye_beam.wav` | Rayo de ojo de Paburu (Forma 1) |
| `sfx_bosses_paburu_wave.wav` | Onda de espíritu de Paburu (Forma 2) |
| `sfx_bosses_phase_change.wav` | Cualquier transición de fase de jefe |
| `sfx_bosses_relic_appear.wav` | Aparece un fragmento de reliquia tras el jefe |

<!-- cita-historica -->
Faltan SFX de jefe aspiracionales (aún no están en disco): `sfx_venado_die`, `sfx_rey_die`, `sfx_gavilan_die`, `sfx_paburu_gold_rush`, `sfx_paburu_pull`, `sfx_paburu_convergence`, `sfx_paburu_transcend`.
<!-- /cita-historica -->

### 12.4 SFX de UI

Todas las rutas relativas a `assets/sfx/ui/`.

| Fichero | Disparador |
|---|---|
| `sfx_ui_menu_move.wav` | Navegación del cursor de menú |
| `sfx_ui_menu_confirm.wav` | Confirmar selección de menú |
| `sfx_ui_menu_cancel.wav` | Retroceder en el menú |
| `sfx_ui_checkpoint.wav` | Checkpoint activado |
| `sfx_ui_stage_banner.wav` | Entrada deslizante del banner de escenario |
| `sfx_ui_game_over.wav` | Pantalla de Game Over |
| `sfx_ui_heart_restore.wav` | Animación de relleno de corazón |
| `sfx_ui_stage_complete.wav` | Escenario completado |

### 12.5 SFX de entorno

Todas las rutas relativas a `assets/sfx/environment/`.

| Fichero | Disparador |
|---|---|
| `sfx_environment_jungle_ambient.wav` | Bucle ambiental de Zona 1 |
| `sfx_environment_datacenter_hum.wav` | Bucle ambiental de Zona 2 |
| `sfx_environment_wind_indoor.wav` | Bucle ambiental de Zona 3 |
| `sfx_environment_cemetery_silence.wav` | Ambiente de Zona Final (mínimo) |
| `sfx_environment_screen_shake.wav` | Eventos de sacudida de pantalla |
| `sfx_environment_hazard_zone.wav` | Tictac de daño de zona de peligro |
| `sfx_environment_one_way_platform.wav` | Aterrizar en plataforma de un solo sentido |

---

## 13. Sprites compartidos

Ubicación: `assets/sprites/shared/`

| Fichero | Tamaño | Fotogramas | FPS | Descripción |
|---|---|---|---|---|
| `torch_anim.png` | 8×16 | 4 | 8 | Animación de llama de antorcha |
| `fountain_anim.png` | 24×24 | 6 | 10 | Animación de agua de fuente (Zona 3-3) — ⚠️ Marcador de posición |
| `spirit_echo_overlay.png` | 1×1 | 1 | — | Superposición de tinte alfa para ecos de espíritu — ⚠️ Marcador de posición |

> **AUD-523.** `checkpoint.png` (el poste con farol) se retiró: el
> checkpoint se dibuja con un haz de luz (`LightSource`,
> `src/framework/stage/checkpoint.py`) en los 26 escenarios, no con un
> sprite fijo.

---

## 14. Directrices de recursos para estudiantes

Los estudiantes que añaden recursos a `student_assets/` deben cumplir todos los estándares de la Sección 2. Además:

| Regla | Requisito |
|---|---|
| Validación de paleta | Ejecutar `scripts/validate_assets.py` sobre cada sprite nuevo antes de hacer commit |
| Convención de nombres | Seguir el mismo patrón de nombres que el tipo de recurso |
| No modificar `assets/` | Los estudiantes sólo añaden a `student_assets/` |
| Formato de fichero | Sólo PNG para lo visual; WAV u OGG para audio |
| Máximo de recursos nuevos por escenario | 20 hojas de sprites, 5 pistas de música, 15 ficheros de SFX |
| Paleta de color | Máximo 16 colores por hoja de sprites; debe ser compatible con la paleta visual de la zona |

---

## 15. Referencia de carga de recursos

Todos los recursos se cargan a través de `AssetLoader`. Lo siguiente muestra el patrón de carga canónico para cada tipo de recurso:

```python
# Carga de imagen:
surface = AssetLoader.load_image(ASSETS_DIR / "sprites" / "player" / "player_idle.png")

# Carga de hoja de sprites:
sheet = AssetLoader.load_sprite_sheet(
    ASSETS_DIR / "sprites" / "player" / "player_walk.png",
    frame_width=32,
    frame_height=32,
)

# Carga de sonido:
sound = AssetLoader.load_sound(ASSETS_DIR / "sfx" / "player" / "sfx_player_jump.wav")

# Carga de fondo (imagen directa):
bg_far = AssetLoader.load_image(ASSETS_DIR / "backgrounds" / "zone1" / "bg_zone1_far.png")

# Carga de imagen de UI:
heart = AssetLoader.load_image(ASSETS_DIR / "ui" / "heart_full.png")
```

Los estudiantes usan la misma API de `AssetLoader` para sus propios recursos:
```python
# Carga de recurso de estudiante:
custom_sprite = AssetLoader.load_image(STUDENT_TEMPLATES_DIR.parent / "student_assets" / "sprites" / "my_enemy.png")
```

---
## 🔗 Documentos relacionados

- [[06_TMX_SPEC.md|Especificación de TMX]]
- [[07_STAGE0_DESIGN.md|Diseño de Stage 0]]
- [[16_WORLD_DESIGN.md|Diseño del mundo]]
