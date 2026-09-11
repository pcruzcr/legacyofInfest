# Auditoría visual y de diseño — level design, gameplay, juice, pacing, game design y fun factor

**Fecha:** 2026-09-11 · **Alcance:** proyecto completo (34 TMX, motor, campaña) ·
**Tipo:** verificación pura, sin cambios de código. Los hallazgos usan ID `AV-xx`
(auditoría visual); los arreglos futuros reclaman su número AUD al commitear, según la
invariante 9. No se asignan AUD aquí para no colisionar con workstreams paralelos.

## Método (todo ejecutado, nada estimado a ojo)

1. **Captura visual headless** de los 34 mapas: arranque real de `StageScene` (contexto
   completo, 60 FPS, SDL dummy), teleport del jugador a spawn/oeste/este, 40 pasos de
   simulación, composición `dibujar_mundo`+`dibujar_ui` a 1280×720 → **102 PNG** revisados
   en 12 hojas de contacto (temp: `auditoria_visual/hojas/`). 34/34 mapas cargan sin
   excepción.
2. **grade_stage sobre los 34 mapas** + `validate_tmx --ci` (35/35 PASS).
3. **Cuatro barridos profundos de código** con evidencia fichero:línea: juice,
   balance/números, pacing/progresión, gaps/errores.

---

## Veredicto global (fun factor)

**El juego funciona; lo que falta no es sistema sino pulido dirigido.** El loop
moverse-combatir-lootear tiene juice completo en el momento central (golpear: 6 capas de
feedback), la cadena de campaña está bien checkpointeada en zonas 1-2, 0 assets rotos en
los TMX y el motor es sólido (35/35 validadores). Los tres problemas que más dañan la
experiencia hoy, en orden:

1. **OSCURIDAD ILEGIBLE** — la mitad de la campaña se ve casi negra (AV-01).
2. **PROGRESIÓN DE HABILIDADES ROTA POR DISEÑO** — el árbol es matemáticamente
   incompletable y la XP de campaña da para ~10 % del árbol (AV-14, AV-15).
3. **PELEAS DE JEFE DE <15 s** — el clímax de cada zona dura menos que un anuncio (AV-11).

Ninguno bloquea: todos son de contenido/valores, no de arquitectura.

---

## 1. Level design

### 1.1 Notas del calificador (grade_stage, 130 pts)

Media **79,7 %**, mediana 80,4 %. Los 13 labs de vistas cuelan 13 notas idénticas de 87
(son una plantilla); la campaña real:

| Mapa | Nota | | Mapa | Nota |
|---|---|---|---|---|
| stage0 | **130 (100 %)** | | stage2_1_oficinas | 112 (86 %) |
| stage2_2 | **130 (100 %)** | | stage1_3_las_aulas | 111 (85 %) |
| stage3_1 | **130 (100 %)** | | stage3_3_el_patio | 111 (85 %) |
| boss_paburu | **130 (100 %)** | | stage4_1 | 115 (88 %) |
| stage1_1 / 1_2 | 122 (94 %) | | boss_gavilan | 102 (79 %) |
| tutorial_hub | 122 (94 %) | | lobby_datacenter | 107 (82 %) |
| boss_venado | 117 (90 %) | | **hall (3-2)** | **89 (68 %) — el peor de campaña** |
| | | | boss_rey | 92 (71 %) (usar grade_boss) |

Avisos repetidos del calificador: 12 mapas **sin coleccionables** (5/10 automáticos) y
6 arenas sin NextTrigger (correcto para jefes, pero `hall` y `lobby` no son arenas y
tampoco declaran salida → la herramienta no puede certificar su ruta).

### 1.2 Hallazgos visuales (capturas)

| ID | Severidad | Hallazgo | Evidencia |
|---|---|---|---|
| **AV-01** | 🔴 ALTA | **Oscuridad ilegible en media campaña.** `boss_paburu`, `hall`, `stage3_1`, `stage3_3`, `stage4_1`, `stage1_3`, `tutorial_hub` y `stage0` (¡el prólogo!) se capturan casi negros: el espacio jugable no se lee. Causa compuesta: 0 objetos `LightSource` en esos TMX (verificado: 0 en hall/lobby/3-1/tutorial/stage0; la luz del jugador y de checkpoints es lo único que abre huecos) + noche/fog/interior + ambiente bajo por zona (`ambiente.py:60-95`). El jugador ve «pistas visuales claras de que faltan focos» — el propio comentario del código lo admite (`ambiente.py:60-63`) | capturas `boss_paburu__este`, `hall__spawn`, `stage4_1__*` |
| AV-02 | 🟠 MEDIA | **Salas enormes y vacías**: `lobby_datacenter` y `hub_backtracking` son planos gigantes de rejilla sin props ni mobiliario; `stage4_1` (960 tiles) es un desierto oscuro sin un enemigo; `ai_dojo`/`qa_proof` son plantillas visibles | capturas; TMX |
| AV-03 | 🟠 MEDIA | **Contraste invertido en stage1_1**: cielo pálido por niebla matinal contra terreno pajizo — el primer nivel de campaña completo es de contraste bajísimo; los bordes de plataforma se pierden | captura `stage1_1__este` |
| AV-04 | 🟠 MEDIA | **Ruido de tiles en la mitad inferior de `stage1_2_la_soda`**: franjas verticales chillonas sin lectura de material — parece colaje de tileset sin paleta unificada | captura `stage1_2__spawn` |
| AV-05 | 🟡 BAJA | **Los 13 labs son la misma sala azul oscura de rejilla** — indistinguibles entre sí salvo por el rótulo; el cenital (`stage_cenital`, `pokemon_cenital`) renderiza casi negro (¿luz no aplicada en vista cenital?) | hojas 6-9 |
| AV-06 | 🟡 BAJA | **`stage_qa_proof` se presenta como «Untitled Stage»** en el banner del nivel — un mapa de QA con nombre sin poner | captura `stage_qa_proof__spawn` |
| AV-07 | 🟡 BAJA | Rectángulo rojo no identificado en varias capturas (tutorial_hub spawn, franja superior en qa_proof/raycast/stencil/mecanicas) — revisar si es un trigger visible u objeto sin sprite | capturas |

Lectura positiva: `stage2_2`, `stage0` (zonas iluminadas) y `boss_rey`/`boss_gavilan`
sí tienen identidad visual; el prólogo enseñando de noche tiene intención, pero sin
focos el tutorial de arranque pelea contra su propio arte.

---

## 2. Gameplay (números y combate)

Coherencia verificada: los 8 multiplicadores de dificultad tienen consumidor real (no
hay multiplicador desconectado salvo `NG_PLUS_BASE`, AV-12). Números clave:
HP jugador 5 (tope 10, `settings.py:63`); daño corto/largo 0,5/1,0 (`player.py:624-645`);
combo ×3 máx en ventana 0,5 s; i-frames 2,0/1,5/1,0 s según dificultad (`difficulty.py:35-58`).

| ID | Severidad | Hallazgo | Evidencia |
|---|---|---|---|
| **AV-08** | 🔴 ALTA | **Jugador casi inmune al contacto, mortal solo por proyectiles/charger.** i-frames 1,5 s (90 frames, el estándar del género es 0,5-0,8) + cooldown de contacto enemigo 0,3 s → techo de 0,33 HP/s por roce. Con 5 HP, un walker necesita ~30 s pegándote para matarte | `difficulty.py:47`, `enemy_base.py:1035` |
| **AV-09** | 🔴 ALTA | **Charger desbalanceado**: contacto 1,5 = 30 % del HP base (único enemigo que provoca el stagger de 0,6 s, umbral ≥1,0). En HARD pega 2,25 (45 %) y en NG+2 ~2,7 (54 %): 4 toques y muerto. Además corre 250 px/s vs dash 200: no se puede escapar | `enemy_charger.py:23-24`, `player.py:876-879` |
| AV-10 | 🟠 MEDIA | **TTK de jefes irrisorio**: venado 12 HP ≈ 6-8 s, gavilán 14 ≈ 7-9 s, rey 15 ≈ 8-10 s, paburu 20 ≈ 10-15 s (i-frames de enemigo 0,5 s → ~2 golpes/s reales). Estándar del género: 60-120 s | HP en boss_*.py, derivado |
| AV-11 | 🟠 MEDIA | **Combo con escalones muertos**: `COMBO_DAMAGE_MULT[7..9]` = 3,0,3,0,3,0 — 30 % de la tabla es plano; y aéreos/especiales (daño 1,0-3,0) nunca construyen combo | `settings.py:157`, `player.py:754-760` |
| AV-12 | 🟠 MEDIA | **Valores muertos**: `NG_PLUS_BASE` (8 números) definido y no leído (`difficulty.py:169-179`); estamina del dash (coste 25, regen 35/s) nace apagada (`estamina_max=0.0`, `player.py:390`) y solo la activan mapas con propiedad `estamina` — en la mayoría del juego es código muerto | citados |
| AV-13 | 🟡 BAJA | XP mínima de 5 para enemigos fuera de tabla aplana la recompensa de los enemigos custom; el boss rinde 200 XP = 2 niveles tempranos pero <1 nivel tras el 10 | `experience.py:50-63` |

---

## 3. Juice

**Inventario: 13 sistemas auditados, 10 CABLEADOS, 2 PARCIALES, 1 AUSENTE.** El momento
«golpear enemigo» tiene 6 capas (partículas+sangre+número+hit-stop+knockback+flash tint);
«recibir daño» tiene shake direccional+flash rojo+vignette+aberración (GL). Telegrafiado
de ataques enemigos (anillo rojo pulsante) y stretch&squash del jugador: correctos.

| ID | Severidad | Hueco (top de 10) | Evidencia |
|---|---|---|---|
| **AV-14** | 🔴 ALTA | **Abrir un cofre = 0 feedback**: `EVENTO_COFRE` no tiene NI UN subscriptor — ni SFX, ni partículas, ni shake. El momento-recompensa arquetípico está muerto | `interactable_system.py:445` |
| AV-15 | 🟠 MEDIA | **Recibir daño sin hit-stop** (infligir tiene 3 niveles): asimetría que abarata el golpe recibido | `senales.py:220-248` vs `collision_system.py:282` |
| AV-16 | 🟠 MEDIA | **Curarse sin VFX**: `PLAYER_HEALED` solo lo pinta el HUD; ni partículas ni flash verde | `senales.py:95-105` |
| AV-17 | 🟠 MEDIA | **Críticos invisibles**: `is_critical` del damage number (dorado, más grande) nunca se pasa a True en todo el repo — feature implementada y muerta | `damage_numbers.py:48,62` |
| AV-18 | 🟠 MEDIA | **Slow motion ausente** como juice (solo existe `assist_slow_mo` de accesibilidad); el ultimate y la muerte del jefe piden cámara lenta; sin stinger musical en muerte de jefe/stage complete | `app.py:490-496`, `boss_base.py:531` único emisor de stinger |
| AV-19 | 🟡 BAJA | Checkpoint/fogata sin celebración (solo SFX+texto); muerte de enemigo sin shake propio; 3 capas de feedback (aberración, bloom puntual, motion blur) son no-op sin GL sin fallback CPU | `senales.py:245`, `gpu_effects.py:42` |

---

## 4. Pacing y progresión

Cadena lineal sólida (16 stages de campaña, ninguno huérfano; jefes avanzan por
`check_boss_defeat`, 4-1 por WarpZone con llave). Zonas 1-2 checkpointeadas cada 25-30
tiles. Pero:

| ID | Severidad | Hallazgo | Evidencia |
|---|---|---|---|
| **AV-20** | 🔴 ALTA | **`hall` (3-2): su único checkpoint está DESPUÉS de la salida** (spawn x=2, NextTrigger x=45, checkpoint x=56): 15 enemigos + 2 DeathPits y 0 checkpoints usables — morir = repetir todo. Anomalía sistemática: checkpoints tras el NextTrigger también en 1-1, 3-1, 2-1 y boss_paburu | `hall.tmx` |
| **AV-21** | 🔴 ALTA | **Pico de densidad injusto en 2-1**: 40 enemigos (vs 12-15 en el resto), mismo HP que la zona 1 — la dificultad sube por cantidad plana, no por curva | `stage2_1_oficinas.tmx` |
| AV-22 | 🟠 MEDIA | **El ciclo día/noche casi no se ve**: solo stage0/1-1/1-2/3-1 lo ejecutan; 1-3, 2-1, 2-2, lobby, hall, 3-3 y los 4 jefes van congelados a mediodía; stage4_1 con 3600 s nunca llega a noche pese a preceder a un jefe nocturno | TMX, `day_night.py:113` |
| AV-23 | 🟠 MEDIA | **Identidad de audio rota**: 1-1 (zona 1), lobby (zona 2) y hall (zona 3) usan `bgm_stage0`; 8 mapas presentan enemigos nuevos sin MessageTrigger | TMX |
| AV-24 | 🟠 MEDIA | **Mecánicas core enseñadas fuera de la campaña**: parry, dash, combo y ratón se enseñan solo en `tutorial_hub`, que NO está en `STAGE_ORDER` (accesible solo desde título). Nado y parry no tienen tutorial en campaña | `title_scene.py:250-279` |
| AV-25 | 🟠 MEDIA | **stage4_1 = 960 tiles / 0 enemigos / 0 NextTrigger**: travesía de 10-15 min sin oposición justo antes del clímax (gating por 3 espíritus); su propia ficha admite los tramos largos (`docs/niveles/13_STAGE_4_1.md:79-81`) | citados |
| AV-26 | 🟡 BAJA | Economía coherente pero justa: carrera limpia ≈ 385-400 monedas vs catálogo ≈ 435 — todo casi comprable en 1 pasada; sin sumideros de largo plazo | `score_system.py:78-114`, `inventory.py:108-225` |

---

## 5. Game design (progresión de habilidades)

| ID | Severidad | Hallazgo | Evidencia |
|---|---|---|---|
| **AV-27** | 🔴 ALTA | **El árbol de habilidades es matemáticamente incompletable**: cuesta 64 puntos; `NIVEL_MAXIMO=60` da 59. La sinergia Berserker (fuerza+coraza al máximo = 40 pts) excluye cualquier otra rama. Y la campaña real rinde ~2.000-2.500 XP → nivel ~7 → **~7 puntos: el jugador ve el 10 % del árbol sin farmear 183.000 XP** (nivel 60) | `skill_tree.py:79-114`, `experience.py:90` |
| AV-28 | 🟠 MEDIA | Cero coleccionables en 12 mapas (los warnings del calificador): la exploración lateral no tiene premio en media campaña | grade_stage |

---

## 6. Gaps, errores y falleras (salud del proyecto)

**Motor: 74/75 GAPs de `KNOWN_GAPS.md` cerrados con evidencia; queda abierto GAP-074**
(zoom GPU, diferido a fase R — coincide con la verificación del doc 101 #18: el zoom
software está arreglado, el uniform de GL no). `validate_tmx` 35/35. 0 referencias de
assets rotas en los 34 TMX. 0 skips injustificados en la suite (8 skipif condicionales
legítimos, con guardián que vigila).

| ID | Severidad | Hallazgo | Evidencia |
|---|---|---|---|
| AV-29 | 🔴 ALTA | **`stage2_4` es un stage fantasma**: `src/stages/stage2_4/stage2_4.py:38` apunta a `assets/maps/stage2_4/stage2_4.tmx` que NO existe — el stage no carga | citado |
| AV-30 | 🟠 MEDIA | **Validador de assets en rojo**: `validate_assets.py:555` exige `tileset_stage4_1_selva.png` (AUD-546) que no está en `assets/tilesets`; `hoja_a_tileset.py` espera otro tileset nunca commitado | citados |
| AV-31 | 🟠 MEDIA | **Ganchos de gameplay vacíos en stages de campaña**: `stage1_3_las_aulas.py:160-175` (5 TODO(student): entidades, trigger, puerta, cutscene), `lobby_datacenter.py:70-85` (4), `stage_qa_proof.py` (plantilla) — los mapas existen pero sus hooks no conectan contenido | citados |
| AV-32 | 🟠 MEDIA | **Anillo de sistemas framework muertos**: `backtracking.py` (módulo entero — el real vive en `src/stages/hub_backtracking/`), `prefab_loader.py` (0 llamantes), `RoomTransition` (1-2 usa su copia privada), `MonedaFx`, `DamageNumber` (clase, no el manager), `stencil_mask`, `TrailPoint` — inflan el código sin uso | barrido |
| AV-33 | 🟠 MEDIA | **Eventos muertos**: `SECRET_FOUND` emitido sin oyente; `SFX_BOSSES_GAVILAN_MASK_BEAM` y `SFX_BOSSES_RELIC_APPEAR` mapeados+subtitulados pero sin ningún emisor; `ACHIEVEMENT_PROGRESS` emitido sin oyente | `interactable_system.py:492`, `sonido.py:104,107` |
| AV-34 | 🟡 BAJA | **Doc drift**: `docs/42_CUTSCENE_SYSTEM.md` documenta 4 acciones de cutscene que ninguna escena instancia; `docs/52_EVENT_MAP.md:498` llama «reservado» a `ACHIEVEMENT_PROGRESS` que ya se emite y no menciona `SECRET_FOUND`; `events.py:23` dice «not yet emitted» de `PLAYER_HEALED` (tiene 3 emisores); `stage_registry.py:70-82` promete una fábrica `selector.py` que no existe | citados |
| AV-35 | 🟡 BAJA | **17 marcadores `AUD-XXX` sin rellenar** en ficheros clave (player, boss_base, enemy_base, helpers…): rompe la trazabilidad de auditorías | barrido |
| AV-36 | 🟡 BAJA | Deuda de tests conocida (docs 100/101): calibración de salto rota por AUD-827, TMX de mecánicas desincronizado, sombras TestApagadoPorDefecto, partidas pre-AUD-502 sin migración | docs 100/101 |

---

## 7. Matriz priorizada (si solo hay tiempo para diez)

| # | ID | Arreglo típico | Esfuerzo |
|---|---|---|---|
| 1 | AV-01 | Añadir `LightSource`s a los 7 mapas oscuros o subir `ambient_brightness` por zona; checklist de legibilidad en validate_tmx | M |
| 2 | AV-27 | Re-escalar curva XP o coste del árbol a la duración real de campaña (~2.500 XP) | M |
| 3 | AV-08 | i-frames 1,5→0,7 s y quitar el cooldown 0,3 s de contacto | S |
| 4 | AV-09 | Charger 1,5→0,75 de contacto y 250→200 px/s | S |
| 5 | AV-14 | SFX+partículas+flash en `EVENTO_COFRE` (subscriptores en `senales.py`) | S |
| 6 | AV-10 | HP de jefes ×2,5-3 (12-20 → 30-60) con las fases actuales | S |
| 7 | AV-20 | Mover el checkpoint de `hall` antes de x=45 (y auditar los otros 4 casos) | S |
| 8 | AV-21 | 2-1: 40→~22 enemigos o dar HP/daño propio de zona 2 | S |
| 9 | AV-29 | Crear `assets/maps/stage2_4/` o dar de baja el stage | S |
| 10 | AV-17 | Cablear críticos (prob. por golpe + `is_critical=True`) | S |

(S = horas; M = 1-2 días. Los IDs AV-02/03/04/22/23/24/25/30/31/32/33 son el segundo
turno natural; AV-05/06/07/13/18/19/26/28/34/35 el tercero.)

---

## 8. Cómo reproducir esta auditoría

```bash
# capturas (temp, fuera del repo)
python <capturador>            # 102 PNG → hojas de contacto con PIL
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python scripts/grade_stage.py assets/maps
python scripts/validate_tmx.py --ci
```

Barridos de código: grep de `LightSource(`/`apply_shake`/`trigger_hitstop`/`is_critical`
con sus llamantes; conteo de enemigos/checkpoints por TMX; curva XP vs coste de árbol.
Nada de esto modifica el árbol.
