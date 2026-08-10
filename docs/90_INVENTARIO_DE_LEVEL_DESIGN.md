---
document_id: "LOI-LEVELDESIGN-090"
title: "Legacy of InFest — Inventario de Level Design"
aliases: ["Inventario de Level Design", "Level Design Inventory"]
tags: ["level-design", "inventory", "design"]
description: "Todo lo que el motor ofrece para diseñar niveles, por categoría (audio, gameplay, mecánicas, enemigos, tiles, efectos, GPU, clima, estación, partículas, luz, sombra), y qué usar en cada nivel"
source: "docs/90_INVENTARIO_DE_LEVEL_DESIGN.md"
date_processed: "2026-08-08"
---

# Inventario de Level Design

**ID del documento:** LOI-LEVELDESIGN-090
**Versión:** 1.0.0
**Estado:** Oficial
**Compatibilidad:** Requiere `60_GUIA_COMPLETA_DEL_MOTOR.md` (LOI-GUIDE-060), `66_GUIA_DE_LEVEL_DESIGN.md` (LOI-LEVELDESIGN-066), `06_TMX_SPEC.md`, `05_ENEMY_SPEC.md`, `17_BOSS_SPEC.md`, `16_WORLD_DESIGN.md`, `22_API_CONTRACTS.md`
**Público:** estudiantes, profesorado, asistentes de código, diseñadores de nivel

> **Qué es este documento.** Un inventario de **todo lo que el motor ofrece
> para construir un nivel**, ordenado por categoría de uso (audio, gameplay,
> gamefeel, mecánicas, enemigos, tiles, efectos, GPU, clima, estación,
> partículas, luz, sombra), y una recomendación concreta de **qué usar en
> cada nivel** existente y en los que faltan zonas.
>
> **Cómo se lee.** Es el catálogo; la [[66_GUIA_DE_LEVEL_DESIGN.md|Guía de Level
> Design]] es el consejo (dificultad, dimensiones, composición de enemigos) y
> la [[60_GUIA_COMPLETA_DEL_MOTOR.md|Guía completa del motor]] es el manual de
> cada propiedad y objeto. Las cifras de este documento están verificadas
> contra el código y contra los `.tmx` de `assets/maps/`. Si una cifra
> contradice al código, el código manda (precedencia de `CLAUDE.md` §5).

---

## 1. El inventario, por categoría

### 1.1 Audio

**Música por zona** en `assets/music/`:

| Pista | Para qué |
|---|---|
| `bgm_stage0.wav` | el umbral (Stage 0) |
| `bgm_zone1_traverse.wav`, `bgm_zone2_traverse.wav`, `bgm_zone3_traverse.wav` | travesía de cada zona |
| `bgm_zone1.wav`, `bgm_zone2.wav`, `bgm_zone3.wav` | variante de zona (ambientes interiores) |
| `bgm_zone1_boss.wav`, `bgm_zone2_boss.wav`, `bgm_zone3_boss.wav` | arenas de jefe por zona |
| `bgm_boss.wav`, `bgm_final_approach.wav`, `bgm_paburu.wav` | jefes finales y tramo final |
| `bgm_title.wav`, `bgm_story.wav`, `bgm_splash.wav` | menús y narrativa |

**Cuatro buses de mezcla**: `musica`, `efectos`, `voz`, `ambiente`; el
volumen real es **maestro × bus × quien reproduce**, calculado en un solo
sitio. Si falta un fichero de audio el juego sigue: registra el aviso y calla
ese sonido (mira la consola).

**Efectos** (API del banco): `play_sfx(nombre)` desde el banco;
`play_sfx_at(nombre, x_mundo)` con panorámica izquierda/derecha;
`play_ambient(ruta)` en bucle; `crossfade_ambient(ruta, duracion)`;
`play_stinger(nombre)` golpe musical; `play_voz(nombre)` — voz que agacha la
música al 35 %.

**Ambientes en bucle ya creados** (`assets/sfx/environment/`):
`jungle_ambient`, `datacenter_hum`, `rain_ambient`, `storm_ambient`,
`wind_indoor`, `cemetery_silence`, más `thunder` (impacto de tormenta).
Cada clima enciende su ambiente solo (§1.10).

**Voz**: `sfx_voz_venado_fase1`/`fase2`/`muerte` — el patrón para jefes con
diálogo; el ducking de la música es automático (35 % en 0.15 s, vuelta en
0.5 s).

**Niveles rítmicos**: propiedades de mapa `bpm`, `compas`, `desfase_audio`
+ objetos `RhythmBlock` con `patron` (un carácter por pulso, ej. `"x.x."`).
El reloj musical (`reloj.en_ventana()`, `reloj.cuantizar(t)`,
`reloj.pulsos_cruzados`) pregunta al mezclador por dónde va la pista, así
que nunca desincroniza — ni con el tiempo bala.

**Un límite reconocido**: no hay reverberación por zona (el mezclador SDL no
tiene DSP); la decisión está documentada como no-futuro en la guía del motor
§10.

### 1.2 Gameplay

El jugador tiene **26 estados** en 7 grupos (ver `04_PLAYER_SPEC.md`): suelo
(`IDLE` `WALKING` `CROUCHING` `SLIDE`), aire (`JUMPING` `FALLING` `DASHING`
`WALL_SLIDE` `LEDGE_GRAB` `AIR_CHASE`), ataque (8 estados, incluido
`ULTIMATE`, que se carga con golpes y se lanza con `U`), `PARRY`, agarre
(`GRAB` `THROW` `CLIMBING` `ZIPLINE`), `SWIMMING`, y daño (`HURT` `DYING`).

Como diseñador **no invocas estados**: colocas objetos — `Vine`, `Zipline`,
`WaterZone`, un muro vertical de dos baldosas — y el estado ocurre.

**Coleccionables e inventario** (los colocas con `Pickup`/`Key`/`Chest`):
- **Mejoras permanentes apilables**: `heart_vessel` +1 vida máxima,
  `hollow_eye` +0.3 daño, `ancients_rib` +2 vida, `swift_feather` +10 %
  velocidad, `thorn_ring` +0.5 daño, `sunken_crown` +3 vida y +0.8 daño.
- **Prendas** (se equipan en `head`/`body`/`feet`; solo cuenta la puesta,
  AUD-207): capuchas y capas de daño o vida, botas de velocidad o vida,
  con precio en monedas (`coin`).
- **Habilidades** sueltas por jefes: `skill_double_jump` ← `BossRey`,
  `skill_dash` ← `BossVenado`, `skill_parry` ← nadie aún (la dejas tú con
  `skill_drop = "skill_parry"` en tu jefe).
- **Llaves narrativas**: `item_id` propios sin bonificación; circuito
  `Key` (`key_id`) → `LockedDoor` (mismo `key_id`), `consume_llave` para
  llaves de un solo uso.

**Candado de progresión**: `PLAYER_SKILLS_REQUIRE_UNLOCK` (default `False`:
doble salto y dash desde el primer fotograma). En `True`, la habilidad solo
llega derrotando al jefe que la suelta — verifica que ese jefe está antes del
tramo que la exige.

**Dificultad**: presets EASY / NORMAL / HARD (daño recibido, emitido y
curado distintos por preset), configurables por sesión.

**Objetivos medibles**: la rúbrica de `scripts/grade_stage.py` (130 pts)
exige 1 spawn, ≥3 coleccionables, checkpoints repartidos, un salto exigente,
capas completas, metadata y tamaño razonable. Los **10 logros** premian
combo aéreo, parry, <60 s por escenario (`speed_demon`), 5 checkpoints en
una partida (`collector`), sobrevivir con 0.5 HP y completar los 15
escenarios (`explorer`).

### 1.3 Gamefeel y gamefactor

- **Sombra de aterrizaje** (`src/framework/vfx/sombras.py`): elipse
  translúcida bajo cada criatura, crece al acercarse, fade a partir de 180 px
  de altura — el único indicador de dónde vas a caer. Automática; solo pide
  sólidos declarados.
- **Coyote frames** y dash evasivo; parry con ventana justa (10 parries =
  logro).
- **Estelas** automáticas en dash y ataques rápidos; en enemigos solo por
  encima de un umbral de velocidad (la estela significa «ataque rápido»).
- **Números de daño, efectos de impacto, flashes de daño en pantalla**,
  `screen shake` (también como orden `temblor` en cutscenes) y **tiempo
  bala** (ralentiza el mundo; la música sigue real para no desincronizar
  niveles rítmicos).
- **Dos soluciones** donde se pueda (un foso que se salta o se rodea separa
  un nivel de un pasillo) y **presentar antes de exigir** (la primera vez de
  un enemigo en tramo sin otras amenazas).

### 1.4 Mecánicas de escenario (objetos TMX)

La lista autoritativa de tipos está en `docs/STAGE_CREATION.md` (generada
desde el registro, no puede envejecer). El subconjunto que define mecánicas:

| Mecánica | Objeto(s) | Nota de diseño |
|---|---|---|
| Escalada vertical | `Vine` / `Zipline` | `CLIMBING` / `ZIPLINE` del jugador |
| Plataformas de un sentido | `Platform` | se atraviesa desde abajo |
| Viento | `WindZone` | empuje con el que el jugador puede luchar |
| Corriente de agua | `WaterZone` + `corriente_x` | convierte el nado en decisión de ruta |
| Puertas y llaves | `Key` / `LockedDoor` | `consume_llave` para un solo uso |
| Teletransporte | `WarpZone` | dentro del mismo mapa |
| Cambio de escenario | `NextTrigger` | la salida del nivel |
| Daño de zona | `HazardZone` (0.25), `DeathPit` | castigo de área |
| Rítmico | `RhythmBlock` | con `bpm` del mapa sigue al pulso |
| Sigilo | `Guard` + `Stalker` | conos cruzados (`barrido = 60`) |
| Cámara | `CameraLock` (lock_x/lock_y) | secciones verticales (2-2) |
| Eventos | `EventTrigger` | dispara un evento por nombre |
| Didáctica | `MessageTrigger` | el recurso docente: mensaje en pantalla |
| Cortes | `Cutscene` | guion de 10 órdenes; `bloquea=false` es la útil |
| Colisión | `Solid` | 1 baldosa × 2–3 de alto = obstáculo; 4+ = muro |

### 1.5 Enemigos: 37 tipos y 13 estados

- **8 arquetipos**: `Walker`, `Flying`, `Shooter`, `Archer`, `Charger`,
  `Brute`, `Caster`, `Assassin` (roles y números en la [[66_GUIA_DE_LEVEL_DESIGN.md|guía 66 §7]]).
- **22 variantes del bestiario** (garza, paloma, halcón, insecto, rata,
  cucaracha, cuaderno, cocinero, tiza, quetzal, buitre, boa, serpiente…).
  **15 no aparecen en ningún mapa del curso**: personalidad gratis para tu
  zona.
- **7 tipos de las entregas** (rata y cucaracha de la soda, estudiante y
  cuaderno del aula, jefes Gavilán/Rey/Paburu): solo existen dentro del
  paquete de su escenario. Registra los tuyos **al nivel del módulo** para
  que el previsualizador los construya.
- **13 estados** (`IDLE`…`DYING`); el que importa es `TELEGRAPHING`: sin
  aviso no es difícil, es injusto. Reglas con cicatriz: `patrol_length`
  obligatoria (sin ella se quedan clavados); `enemigo.velocity` es siempre
  (0, 0) (deducelo del desplazamiento si lo necesitas).
- **Colocación**: máximo 3 tipos por nivel; ≤8 en pantalla a la vez;
  presentar antes de exigir; un peligro a la vez; dejar siempre un carril
  seguro; los enemigos no bloquean checkpoints ni portales.

### 1.6 Jefes

`BossBase` trae: fases con umbrales (`BOSS_PHASE_CHANGED` +
invulnerabilidad de fase y tinte por fase), telegrafiado
(`attack_timing`, `telegraph_progress`), puntos débiles (`weak_point_at`,
`apply_hit_at`), parry receptivo, invocaciones (`on_summon`),
teletransporte, arena (`set_arena_bounds`). La arena no se califica con la
rúbrica de niveles; `day_length = 0` congela el sol para que la luz no
cambie a mitad de la pelea. Bullet hell denso = enjambre NumPy (medido:
2000 balas, 12.94 ms con objetos vs 0.072 ms con el enjambre). Al morir
deja el Fragmento de Reliquia + `skill_drop` si lo definiste.

### 1.7 Tiles y capas

- **19 tilesets** en `assets/tilesets/` (stage0, campus, cafeteria,
  datacenter(_ext), heredia, jungle, planicie, rectas, gavilán, oficinas,
  paburu, cemetery…). Tile base **16×16**; los niveles horizontales ponen
  el suelo en y = 480.
- **Capas**: `Terrain`, `Collision`, `Objects`, `Terrain_Detail`,
  `FG_Overlay` (+ `BG_Mid`/`BG_Far` según el caso; el Hall usa la pila de
  5 capas más compleja del juego).
- **Paleta ≤ 16 colores** (constraint SNES): el color es lenguaje — soda
  cálida, datacenter azul acero, piedra beige, cementerio verde espectral.
- La geometría está **medida** (guía 66 §1.3, `tests.playtest.jump_bench`):
  huecos de 2 baldosas cómodos; 3 = obstáculo con checkpoint cerca; 4+ = solo
  con la técnica de soltar la dirección y con ruta alternativa.

### 1.8 Efectos y post-procesado

`src/framework/vfx/` — screen-space en `post_processing.py`: **bloom** (base
permanente por zona + ráfagas por evento), **vignette** (base + de daño),
**flash**, **tint**, **motion blur** y **color grading**; además:
**refracción de agua** (`water_effect = true` + `WaterZone`), **niebla de
guerra** (`fog_of_war` con radio en px, dibujada entre el mundo y el HUD),
**estelas** (`trail_system.py`), **partículas de aire**
(`ambient_particles.py`), **clima** (`weather_system.py`), **luz**
(`lighting.py`), **sombra** (`sombras.py`), y el procesamiento de las
Unidades VII–IX (`src/framework/processing/`, Sobel, Canny, umbral) que los
jefes usan como efecto vivo (parpadeo sobel, canny en la máscara del
Gavilán).

### 1.9 GPU (OpenGL / ModernGL)

`src/engine/render/gl_pipeline.py` + `src/engine/render/shaders.py`: tubería
de pantalla completa sobre un **sprite batch** (`SpriteBatchGPU`): shaders de
**iluminación (`lighting_frag`)**, **bloom extraído+blur**, **godrays**,
**refracción**, **chromatic aberration**, **color grading**, **colorblind**,
**motion blur**, **vignette** y passthrough; `src/engine/core/gpu_effects.py`
publica la intensidad de bloom entre sistemas. Requisito de medida: el
renderer debe ser **NVIDIA/Quadro** (el pipeline avisa si no; una medición en
la integrada no vale como referencia). El GPU se mide con
`scripts/bench_sprite_batch.py`.

### 1.10 Clima

5 climas (`src/framework/vfx/weather_system.py`), cada uno con sus
partículas, overlay, viento y pista de ambiente:

| `climate` | Partículas | Overlay | Viento | Pista de ambiente |
|---|---|---|---|---|
| `clear` | 0 | 0 | — | — |
| `rain` | 60 | azulado | ±15 | `rain_ambient` |
| `snow` | 40 | blanco | ±12 | `wind_indoor` |
| `fog` | — | 80 | — | `wind_indoor` |
| `storm` | 100 + truenos | 60 | ±50–100 | `storm_ambient` (+ `thunder`) |

Se puede cambiar en runtime (`set_climate`); `storm` incluye viento lateral
que inclina la lluvia.

### 1.11 Estaciones

4 estaciones (`src/framework/stage/seasons.py`): `spring` (verde leve, clima
claro, spores), `summer` (dorado, claro, dust, factor de luz 1.08), `autumn`
(ámbar, **llueve**, hojas) y `winter` (azul pálido, **nieve**, ash). El tinte
se normaliza para teñir sin oscurecer; hay un solo resorte de brillo
(`factor_luz`). La estación **sugiere** clima y partículas si no los declaras,
pero nunca sobrescribe lo que escribas. Es propiedad del mapa: no cambia
durante la partida.

### 1.12 Partículas

- **Ambiente** (`ambient_fx`, 5 tipos + `ambient_fx_rate`): `dust`, `leaves`,
  `embers`, `spores`, `ash`. Precedencia: mapa > estación > **tabla por
  zona** (Z0 spores 14, Z1 leaves 10, Z2 embers 18, Z3 ash 22). `none`
  apaga.
- **Del clima**: la lluvia, nieve y tormenta de §1.10 (con viento que las
  inclina).
- **Estelas** (`trail_system.py`): automáticas, con umbral de velocidad de
  enemigo deliberado.
- **Impactos y daño**: automáticos del sistema de combate.

### 1.13 Luz

- Brillo ambiente: TMX → tabla por zona (`AMBIENT_BY_ZONE`:
  0.62 / 0.50 / 0.32 / 0.22) → 0.55. El suelo de noche `MIN_AMBIENTE = 0.45`
  detiene la oscuridad total, pero **no** sustituye a los focos: sin focos
  una noche no se ve.
- Objeto `Light`: `radius`, `intensity`, `color`, `flicker_amount` /
  `flicker_speed` (LED de peligro, antorchas…).
- **Receta para una noche legible**: `day_length = 420`, `ambient_light =
  0.7`, focos de `radius 140` / `intensity 0.85` cada 8–10 baldosas — 12
  focos en 100 baldosas dan 45 % de pantalla legible a medianoche (7 daban
  24 % y el nivel era injugable). Comprueba con `scripts/preview_tmx.py
  --hora 23`.
- `day_length = 0` congela el reloj (arenas de jefe); Stage 0 usa 420.
- Precedencia: `ambient_light × hora × estación + clima` (el clima suma).

### 1.14 Sombra

Elipse translúcida dinámica bajo el cuerpo y los enemigos (`sombras.py`):
crece al acercarse al suelo, desaparece por encima de 180 px de altura
(mejor que una sombra constante), busca el suelo **más alto** debajo de cada
entidad. Automático — no hay que configurar nada más que tener sólidos.
Los focos (`Light`), el bloom y los godrays hacen el resto de la
profundidad.

---

## 2. Reglas que acotan cualquier decisión

| # | Regla |
|---|---|
| 2 | baldosas es un hueco cómodo; 3 es un obstáculo; 4+ exige técnica o ruta alternativa |
| 5 | repechos de hasta 5 baldosas |
| 8 | enemigos simultáneos en pantalla, máximo |
| 3 | tipos de enemigo por escenario de estudiante, máximo |
| 16 | colores de paleta por nivel |
| 700–1200 px | distancia entre checkpoints |
| 0.45 | suelo nocturno de luz (`MIN_AMBIENTE`) |
| 12 | focos por cada 100 baldosas para una noche legible |
| 180 px | altura a la que la sombra deja de informar |
| 2× | límite de tiempo ≈ 2 × limpieza estimada del recorrido |
| 3 | checkpoints mínimo lo pide la casilla `design_pacing` (con salto exigente) |
| 1 | `Brute` por nivel, como máximo, presentado antes |

---

## 3. Qué usar en cada nivel

Recomendación concreta por nivel, calculada con el inventario de arriba y la
composición nominal de la guía 66. Los mapas marcados `[REF]` son diseño sin
`.tmx` implementado todavía.

| Nivel | Audio | Clima / hora / estación | Partículas | Luz / VFX | Enemigos recomendados | Mecánica distintiva |
|---|---|---|---|---|---|---|
| 0 Umbral | `bgm_stage0` | claro, día, summer | dust ligero | sin focos, luz 0.62 | 1 caminante | mensaje por sistema; foso con dos rutas; bloques rítmicos; viento; tirolesa |
| 1-1 Entrada | `bgm_zone1_traverse` + `jungle_ambient` | claro, mediodía, summer | leaves | parallax, bloom 0.22 | Insecto×6, Pájaro×3, Rana×2 | presentar los 3 arquetipos; sin fosos |
| 1-2 La Soda | `bgm_zone1` | interior, día, summer | dust | cocina cálida vs sala fría (tinte) | Ratón×4, Cucaracha×5, Cocinero×1 | dos pisos; `HazardZone` del mostrador |
| 1-3 Las Aulas | `bgm_zone1` | claro, autumn opcional | dust de tiza | umbral: tiza brillante vs raíces | Estudiante×5, Cuaderno×3, Tiza×2 | llave/puerta; pizarrón checkpoint |
| 1-4 Venado | `bgm_zone1_boss` + `voz_venado_*` | crepúsculo, congelado | spores | Sobel fase 2; arena | — | fase 2 de decisión; plataformas altas como refugio |
| 2-1 Oficinas | `bgm_zone2_traverse` + `datacenter_hum` | azul acero, nublado | embers 18 | Canny «cableado», LED sincro | Terciopelo×7, Venomolargo×3, Terciovolador×2 | re-baseline tras jefe |
| 2-2 Antenas | `bgm_zone2_traverse` | noche | embers | CameraLock vertical; motion blur al caer | Guardia×2, Halcón×4, Serpiente×3 | única sección vertical real del juego |
| 2-3 Lobby | `bgm_zone2` | noche, luz 0.32 | embers | focos LED flicker | variantes del datacenter | corto y denso |
| 2-4 Rey | `bgm_zone2_boss` | congelado | embers | rejas `HazardZone` | — | F1 existe (VENOM_SPIT); F2/F3 por implementar |
| 3-1 Piedra | `bgm_zone3_traverse` | atardecer | ash | altura 224 px = leer picados | Garza×4, Halcón×4, Quetzal×2 | halcones nunca pican junto a garzas |
| 3-2 Hall | `bgm_zone3` | tarde | ash | 5 capas; claraboyas | Paloma×5, Halcón×6, Buitre×2 | watershed por zonas |
| 3-3 Patio | `bgm_zone3` | **nublado** (gaussian baja la agresión) | ash | fuente que cura 0.25 | Paloma×3, Halcón×5, Quetzal×3 | decisión de curar vs huir |
| 3-4 Gavilán | `bgm_zone3_boss` + sfx del gavilán | congelado | plumas | claraboya; vigas | — (14 corazones) | una sola fase; ataques por escribir |
| 4-1 Entrada cementerio | `cemetery_silence` | niebla espiritual, fog | ash/spores | grietas pulsantes; ecos | **ninguno** (regla de oro) | actos que escalan atmósfera |
| 4-2 Paburu | `bgm_paburu` | noche | embers+ash | 4 pilares de llama | — (20 corazones) | Forma 3A/3B; `CONVERGENCE` |
| Lab mecánicas | usa `bpm`/`compas` | día | — | — | — | bloques rítmicos; viento; plataformas |

> Los jefes tienen `day_length = 0` (el sol no cambia durante la pelea) y
> `Zone`/`ZONE` coincidentes en TMX y código (AUD-264).

---

## 4. Espacios abiertos (dónde un nivel nuevo aporta valor real)

1. **[REF] 2-1 canónico, la Planicie** — receta en la guía 66 §3.4
   (serpientes pequeñas, alambre a la altura de la rodilla, calima térmica
   como tint animado). Nada de eso existe en código: territorio nuevo.
2. **Rey Terciopelo, fases 2–3** (`ReyMetad`, `BODY_SLAM`, `SERPENT_CARPET`):
   diseñadas en `17_BOSS_SPEC.md`, sin implementar.
3. **Gavilán: sin ataques** — clase al 45 % de la rúbrica, asignación de
   estudiante.
4. **`skill_parry` sin dueño** — se la puedes soltar a un jefe con
   `skill_drop = "skill_parry"`.
5. **15 bestiarios sin usar** de `docs/18_ENEMY_ROSTER.md`.

Cualquiera de estos puede cerrar la curva de dificultad de la guía 66 §1.2 y
conectarse con los logros (`collector`, `speed_demon`) sin tocar la
progresión.

---

## 5. Fuentes

- `src/framework/scenes/stage_parts/ambiente.py` — tablas por zona (luz,
  bloom, viñeta, partículas) y orden de precedencia
- `src/framework/vfx/` — clima, luz, niebla, sombra, partículas, post
- `src/framework/stage/seasons.py` — las cuatro estaciones y sus valores
- `src/engine/render/gl_pipeline.py` y `shaders.py` — la tubería de GPU
- `assets/music/`, `assets/sfx/`, `assets/tilesets/` — los recursos
- `scripts/preview_tmx.py`, `scripts/grade_stage.py`,
  `scripts/validate_tmx.py`, `scripts/check_tmx_coverage.py` — medición
- `tests/` y `python -m tests.playtest.jump_bench` — valores de geometría

## 6. Documentos relacionados

- [[60_GUIA_COMPLETA_DEL_MOTOR.md|Guía completa del motor]] — el «cómo» de cada propiedad
- [[66_GUIA_DE_LEVEL_DESIGN.md|Guía de Level Design]] — el «qué construir» de cada nivel
- [[06_TMX_SPEC.md|Especificación TMX]], [[STAGE_CREATION.md|Stage Creation]]
- [[05_ENEMY_SPEC.md|Enemigos]], [[18_ENEMY_ROSTER.md|Enemy Roster]],
  [[17_BOSS_SPEC.md|Jefes]]
- [[86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md|Niveles y jefes]],
  [[16_WORLD_DESIGN.md|World Design]]
- [[62_ESTADO_DEL_PROYECTO.md|Estado del proyecto]],
  [[87_REPORTE_DE_LO_QUE_FALTA.md|Reporte de lo que falta]]
- [[73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md|Catálogo de recursos]]