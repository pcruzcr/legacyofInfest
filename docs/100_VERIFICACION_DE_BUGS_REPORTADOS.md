# Verificación de errores reportados — menús, lentitud, enemigos flotantes y ruido con música

**Fecha:** 2026-09-09 · **Alcance:** verificación previa a cualquier corrección, con evidencia ejecutada por lectura directa del código · **Estado:** los cuatro reportes son reales, con matices

> Último AUD usado antes de este documento: AUD-825 (`git log --oneline -1`). Este documento asigna AUD-826 a AUD-834, un número por error verificado. Cada corrección futura usa su propio número en mensaje de commit, comentario de código y documento de auditoría.

## Resumen de veredictos

| Error reportado | Veredicto | AUD | Causa real |
|---|---|---|---|
| Menús en todos los stages pegados y mal dimensionados | Real, alcance más estrecho | AUD-826 | Pausa global en `drawing_system.py`, no menús por stage |
| Juego se siente lento | Real, doble causa | AUD-827 | Diseño (90 px/s) + presupuesto 8,33 ms a 120 FPS |
| Enemigos de piso caminan en el aire y no hacen bajadas | Real, parcial | AUD-828 | Sin gravedad en base + solo `Walker` detecta borde |
| Stages con ruido más música | Real | AUD-829 | Música + ambiente simultáneos + muestra corta en loop + fuga de `stop` |
| Tirolesa stage 0 no suelta ni llega a la otra | Real, tres causas apiladas | AUD-830 | Sin cartel + radio 14 px + salida solo con flanco fresco |
| Liana ("leña") stage 0 no se puede usar | Real parcial, uso exigente | AUD-831 | Flota a 96 px del suelo; exige salto + pulso en el ápice |
| Menú principal no deja entrar a opciones | No reproducido como bloqueo; defecto real de descubrimiento | AUD-832 | Ruta funciona; 14 opciones con 4 visibles + flecha de subida muerta |
| Menús no regresan al principal | Real parcial | AUD-833 | `progress`/`unit_theory` vuelven a demos; `keybinding` pierde origen; salidas de dos niveles |
| Textos pegados sin desplazamiento en menús/demos | Real | AUD-834 | `demo_menu` 1 px de aire; `shop`/`keybinding`/`quiz`/`unit_theory`/`pattern_demo` sin clip ni scroll |

Nada se corrige en este documento. Solo se verifica, se justifica y se deja la pista para el arreglo.

---

## AUD-826: menús pegados y mal dimensionados — REAL

**Reporte:** "los menús en todos los stages están pegados y no están bien dimensionados".

**Verificación:** no existe código de menú por stage. La búsqueda de `draw_screen|MenuList|draw_panel` en `src/stages/**/*.py` devuelve cero menús. Todos los stages heredan la pausa de `StageScene`, que dibuja en un único sitio global.

**Evidencia 1 — tira de pestañas pegada al borde, tamaño fijo:**

`src/framework/stage/drawing_system.py:880-891`

```python
alto_franja = 20
ancho_pestana = settings.INTERNAL_WIDTH // len(tabs)
pygame.draw.rect(surface, (10, 10, 16), (0, 0, settings.INTERNAL_WIDTH, alto_franja))
...
surface.blit(texto, (cx - texto.get_width() // 2, 1))
```

Por qué está mal: rectángulo en `(0, 0)` y texto en `y=1`, con cero margen. La convención del proyecto es `Theme.MARGIN = 32` (`src/engine/ui/theme.py:87`) y el HUD usa `MARGEN = 24` (`hud_builder.py:58`). Alto fijo de 20 px sobre 720 px de alto interno (`settings.py:19-20`) = 2,7 % de la pantalla, sin usar `escalar()` (`theme.py:139-147`). Fuente fija `pygame.font.Font(None, 20)` (`drawing_system.py:123`), fuera del tema e ignorando `text_scale`.

**Evidencia 2 — pestaña "Menú" sin panel, espaciado fijo:**

`src/framework/stage/drawing_system.py:898-907`

```python
cx = settings.INTERNAL_WIDTH // 2
cy = settings.INTERNAL_HEIGHT // 2 - (len(opciones) * 30) // 2
surface.blit(text, (cx - text.get_width() // 2, cy + i * 30))
```

Por qué está mal: texto crudo sobre fondo liso, sin `draw_panel()` ni `draw_modal_scrim()`. Paso vertical de 30 fijo, sin escalado por resolución ni por accesibilidad.

**Por qué se ve "en todos los stages":** `stage_parts/pausa.py` es solo lógica, no dibuja. `stage_parts/dibujo.py:259-303` llama siempre al mismo `_draw_pause_panel`. Un solo código global produce síntoma idéntico en los 26 stages.

**Lo que no está roto y queda fuera del arreglo:** HUD con margen 24, pestañas embebidas Mapa/Equipo/Habilidades con `draw_screen` y margen 32, diálogo con margen 20, subtítulos con `escalar(56)`. No tocar.

---

## AUD-827: juego se siente lento — REAL con doble causa

**Reporte:** "el juego se siente lento".

**Verificación:** el `dt` está bien usado. No hay error de integración por frame. Hay dos lentitudes reales distintas.

**Lo descartado — `dt` correcto:** pasos fijos `FIXED_DT = 1.0 / TARGET_FPS` (`src/engine/core/clock.py:79`), bucle en `src/engine/core/app.py:528-531` con `pasos_fijos()`, movimiento con `velocity * dt` (`player.py:1301-1324`, `enemy_base.py:268-269`). La simulación avanza a velocidad correcta.

**Causa 1 — diseño, velocidad de marcha baja:**

`src/engine/core/settings.py:62` — `PLAYER_WALK_SPEED = 90.0`, `PLAYER_DASH_SPEED = 200.0`, resolución `1280x720` (`settings.py:19-20`).

Cruzar una pantalla a 90 px/s tarda 14,2 segundos. Si "lento" significa "el personaje anda pesado", es real y es ajuste de diseño, no caída de FPS.

**Causa 2 — rendimiento condicional, presupuesto exigente:**

`src/engine/core/settings.py:21` — `TARGET_FPS = 120` con presupuesto `FRAME_BUDGET_120 = 8.33 ms` (`settings.py:24`). El propio proyecto admite que 120 solo es sin sombras (`settings.py:26-27`) y la certificación mide `9.47 ms a 1920` (`docs/AUD-800_FINAL_CERTIFICATION.md:281`).

Cada fotograma en camino CPU ejecuta iluminación a pantalla completa (`dibujo.py:220-221`, `lighting.py:281-284` con `smoothscale` en `lighting.py:391`) más post-procesado con bloom (`post_processing.py:199-276`, el propio archivo admite costo previo de 12,08 ms). Con monitor a 60 Hz y `vsync=1`, el contador muestra 60 aunque la simulación vaya bien, lo que se lee como "lento". Si el fotograma supera el tope de 10 pasos (`clock.py:84`), se descarta tiempo y hay cámara lenta real (`clock.py:202-212`).

**Cómo confirmarlo en la máquina que reporta:** abrir consola con F11 y mirar P50/P95/P99 y FPS real con `vsync=1`.

---

## AUD-828: enemigos de piso caminan en el aire y no hacen bajadas — REAL parcial

**Reporte:** "hay enemigos de piso que caminan en el aire y no hacen las bajadas".

**Verificación:** no afecta a todos por igual. `Walker` y sus hijos invierten en el borde en vez de bajar. El resto de terrestres sale de la plataforma y sigue en el aire.

**Evidencia 1 — la base no tiene gravedad:**

`src/framework/entities/enemy_base.py:892-899`

> "Los enemigos no tienen gravedad propia: andan sobre suelo llano a la altura a la que se colocaron."

Gravedad solo en `LAUNCHED` (`enemy_base.py:1081`, `600.0 * dt`) y casos de `HURT` volador. Un enemigo que sale de su losa conserva su `position.y` para siempre. Nada lo hace caer.

**Evidencia 2 — solo `Walker` detecta borde:**

`src/framework/entities/enemy_walker.py:105-135`

```python
probe_x = self.position.x + (self.facing_direction * (self.rect.width // 2 + 2))
probe_y = self.position.y + self.rect.height + 2
has_floor = any(r.collidepoint(probe_x, probe_y) for r in all_ground)
if not has_floor: self.facing_direction *= -1
```

Es el único rayo hacia abajo en todo `enemy_*.py`. `Charger` (`enemy_charger.py:68-74`), `Brute` (`enemy_brute.py:65-81`), `Caster`, `Archer`, `Shooter`, `Assassin` y `Shielded` mueven `x` y revierten por distancia o muro, sin mirar suelo delante. Herencias como `EnemyCeibo(EnemyBrute)` propagan el defecto.

**Evidencia 3 — anclaje insuficiente para bajadas:**

`src/framework/entities/enemy_base.py:914-940` (`_mantener_en_suelo`) engancha con tolerancia de 2 a 4 px. Un escalón de bajada de una baldosa (16 px) queda fuera: ni baja ni cae, flota. Las pendientes triangulares sí se siguen (`_resolver_pendientes` + `pendientes.py:78` con margen 8,0), pero ningún mapa las usa de forma que el paso se ejecute (`enemy_base.py:165-168`), y los escalones de bloques no son objetos `Pendiente`.

**Por qué "no hacen las bajadas" incluso con `Walker`:** al no haber suelo en el punto de prueba, invierte dirección. Es correcto para no caer al vacío, pero significa literalmente que no desciende rampas de bloques ni escaleras: las lee como borde y da media vuelta.

---

## AUD-829: stages con ruido más música — REAL

**Reporte:** "hay stages que tienen ruido más la música".

**Verificación:** no es ruido aleatorio. Es música más ambiente sonando a la vez por diseño, con una muestra mala y una fuga de `stop`.

**Evidencia 1 — doble capa música más ambiente:**

`src/framework/scenes/stage_scene.py:644-656` arranca `play_music`, `src/framework/scenes/stage_scene.py:724-735` arranca ambiente por clima, `src/framework/scenes/stage_parts/simulacion.py:309-341` pone `play_ambient(ruta, volume=0.3)`. `src/engine/audio/audio_manager.py:99-114` contra `:231-251` confirma rutas distintas: música por `mixer.music`, ambiente por `Sound` en bucle. `play_music` no para el ambiente ni viceversa.

Stages que lo disparan hoy: `stage1_1.tmx:9-11` (`bgm_stage0` + `climate=fog`), `boss_paburu.tmx:9-17` (`bgm_paburu` + `fog`), `stage4_1/fases.py:67-106` con música y ambiente por fase, `stage2_1_oficinas.py:80-85` con zumbido manual más `bgm_zone2_traverse`.

**Evidencia 2 — la muestra de `fog`/`snow` suena a ruido:**

`src/framework/vfx/weather_system.py:309-318` — `fog` y `snow` apuntan al mismo fichero `sfx_environment_wind_indoor.wav`, muestra de 2,0 s en loop infinito. El propio código lo describe como defecto en `src/stages/boss_paburu/boss_paburu_scene.py:298-307`: "un soplido de dos segundos repetido eternamente se oye como un chorro raro". Volumen 0,3 a 0,35, nunca baja a cero (`environment.py:122,201-223`).

**Evidencia 3 — fuga al salir del stage:**

`src/framework/scenes/stage_scene.py:776-789` (`on_exit`) hace `audio.stop_music()` y nunca `stop_ambient()`. El stage que sí lo parchea lo admite: `src/stages/stage2_1_oficinas/stage2_1_oficinas.py:120-130` ("sin esto el zumbido seguiría sonando en el siguiente escenario"). El ambiente queda pegado al ir a menú o título, que solo manejan música.

---

## AUD-830: tirolesa del stage 0 — REAL, tres causas apiladas

**Reporte:** "nos subimos y no pudimos bajarnos ni brinca a la otra".

**Verificación:** el viaje del motor funciona en arnés (ver evidencia 4), pero el montaje es casi imposible, nadie enseña la tecla y la salida exige un flanco fresco en una ventana de 0,75 s. Además hay una sola tirolesa en el stage: "la otra" no existe. Mismo patrón de tres culpas que Paburu R18 (`src/stages/boss_paburu/PENDIENTES.md:75`), pero el stage 0 nunca recibió aquel arreglo.

**Datos del cable real:** `assets/maps/stage0/stage0.tmx` solo trae un `Zipline` (`Zipline_246` en `1488,448`, `destino_dx=80`, `destino_dy=128`, `velocidad=200.0`, sin `radio_de_enganche` ni carteles). Origen a 160 px del suelo (608). Largo 150,9 px, viaje de 0,75 s.

**Evidencia 1 — nadie enseña la tecla:** los 9 `MessageTrigger` del TMX no mencionan la tirolesa. El de zona G (`1312`: "El viento empuja. Espera a que amaine. U es el ataque definitivo.") habla de viento y de U, no de G. La liana de zona C sí tiene cartel (`400`: "Sube. Con G o Arriba te agarras a la liana."). Sin cartel, el jugador no sabe que G existe para el cable.

**Evidencia 2 — montaje en ventana de 14 px a 160 px del suelo:** el TMX no define `radio_de_enganche`, así que rige el defecto 14,0 (`src/framework/stage/stage_objetos.py:1055`, `src/framework/ecs/components.py:701`). Paburu midió que 18 px "no perdonaba nada" y lo subió a 30 (`PENDIENTES.md:75`); el stage 0 sigue en 14. El enganche exige `is_action_just_pressed` (un solo fotograma, `src/framework/scenes/stage_parts/mundo_ecs.py:217-227`) a menos de 14 px del segmento (`src/framework/ecs/systems_zonas.py:104`), con el cable colgando a 160 px del suelo: hay que saltar (~82-90 px de salto) y pulsar G justo en el ápice bajo el tramo medio del cable. Cálculo: parado bajo el tramo medio el centro queda a ~93 px del cable; en el ápice a ~11 px. Solo entra en una franja mínima del salto.

**Evidencia 3 — la salida exige flanco fresco o esperar al final:** `src/framework/entities/states/rope.py:182-196` solo sale con `jump_pressed` (flanco del fotograma, porque `is_action_pressed` es `is_action_just_pressed` en `src/engine/input/input_manager.py:265-266`) después de 0,08 s, o al llegar al final (`progreso >= 0.995`). Agacharse o abajo no sueltan: no hay rama de `crouch_held`. Si el jugador subió manteniendo una tecla o pulsa salto antes de tiempo, el flanco ya pasó y no sale hasta el final del viaje. "No pudimos bajarnos" queda justificado.

**Evidencia 4 — el viaje sí funciona en arnés (el motor no hunde):** guion ejecutado con el `Player` real y el cable real del TMX (`player.update` completo, 60 FPS): 42 fotogramas, termina en `FallingState` en `(1553, 568)` con pies en 600 (8 px sobre el suelo 608, sin enterrarse), desviación máxima del cable 11,7 px (el hundimiento de 80 px de Paburu R18 ya lo corrige AUD-820 en `src/framework/entities/player.py:1317-1330`). Salida con salto a mitad verificada: pasa a `JumpingState` con `vy=-290,7`. La gravedad no es la causa; el problema es montaje, señalización y ventana de salida.

**Evidencia 5 — "la otra" no existe:** solo hay un objeto `Zipline` en todo el TMX (comprobado por lectura completa de la capa `Objects`). Si "la otra" es la plataforma del cofre o el `NextTrigger` (`1552..1584`, justo donde termina el viaje), el viaje deja al jugador al lado; si es otra tirolesa, es contenido inexistente y el reporte describe expectativa, no regresión.

## AUD-831: liana del stage 0 ("leña") — REAL parcial, uso exigente pero no rota

**Reporte:** "la leña tampoco la pudimos usar" (se interpreta "liana": el stage 0 no tiene ningún objeto de leña, fogata o tronco usable; las `Vine_209/210` de zona C y las `VineSwing_211/212` del foso son lo único agarrable).

**Verificación:** la mecánica funciona, pero desde el suelo es inalcanzable por diseño geométrico y hay que saltar más pulsar en el ápice.

**Evidencia 1 — desde el suelo no hay solape:** `Vine_209` (`528,432,8x80`, `ancho_de_agarre=12`) termina en `y=512`; el jugador en el suelo ocupa `544..608`. `liana_alcanzable` solo ensancha en horizontal (`rect.inflate(ancho*2, 0)` en `src/framework/ecs/systems_zonas.py:65`), sin margen vertical: no hay solape posible parado. Repro en arnés: alcance desde suelo `False`, en ápice (~454) `True`.

**Evidencia 2 — el cartel sí enseña la tecla (a diferencia de la tirolesa):** mensaje en `x=400`: "Sube. Con G o Arriba te agarras a la liana." Y `mundo_ecs.py:217-222` acepta `GRAB`, `SHORT_ATTACK`, `MOVE_UP` y `JUMP`. Quien salta y pulsa en el ápice dentro de la ventana horizontal de 24-28 px se agarra; quien lo intenta desde el suelo concluye que "no se puede usar".

**Evidencia 3 — lianas de salto:** `VineSwing_211/212` (`1152` y `1232`, separadas 80 px) se agarran en el aire con pulso o proximidad (`mundo_ecs.py:197-213`) y el salto entre ellas da impulso 220 (`rope.py:281`), suficiente para 80 px. Funciona, pero el único cartel (`x=1136`) es genérico y no enseña a bombear ni el momento de soltar.

---

## AUD-832: menú principal no deja entrar a opciones — NO reproducido como bloqueo; descubrimiento defectuoso SÍ real

**Reporte:** "en el menú principal no se puede ingresar a opciones".

**Verificación:** la ruta funciona. Guion ejecutado con escenas reales: 12 pulsaciones ABAJO desde `START`, `CONFIRM` en `OPTIONS` → `OptionsScene`; `CANCEL` → `TitleScene`. La rama existe (`src/engine/scenes/title_scene.py:322-325`, `replace(OptionsScene)`) y la escena lee input y vuelve (`src/engine/scenes/options_scene.py:268-299`).

**Lo real — por qué se siente bloqueado:**

1. 14 opciones con 4 visibles (`title_scene.py:79-102`, `OPCIONES_VISIBLES=4` en `:121`). `OPTIONS` es la número 13: exige 12 ABAJO (o 2 ARRIBA con vuelta). Quien no desplaza concluye que no existe.
2. La flecha de subida está muerta: `title_scene.py:466-478` lee `self._scroll_offset`, que se fija en 0 en `:103,164` y nadie actualiza (la ventana la lleva el kit `MenuList.desplazamiento`, `:432`). La flecha de arriba no aparece nunca aunque haya opciones encima; la de abajo aparece siempre. El indicador miente y el usuario no descubre el scroll.

**Descartado:** opción sin acción, escena no registrada (no se usa esa vía aquí), excepción en `on_enter`, input no leído. La prueba `tests/test_menu_navigation.py` cubre `OPTIONS → OptionsScene` (hoy falla solo por `TUTORIAL → TutorialHub`, expectativa vieja de AUD-721, no por opciones).

## AUD-833: menús que no regresan al principal — REAL parcial

**Reporte:** "algunos menús no se regresan al menú principal".

**Verificación por escena (salida con `CANCEL`/`ESC`):**

| Escena | Destino al salir | Vuelve al principal |
|---|---|---|
| `options_scene.py:299`, `demo_menu_scene.py:211`, `load_game_scene.py:177`, `bestiary_scene.py:119`, `leaderboard_scene.py:158` | `replace(TitleScene)` | Sí |
| `progress_scene.py:122` | `replace(DemoMenuScene)` | No; además su pista dice `ESC: Back to Menu` (`:179`) y va al temario, no al menú |
| `unit_theory_scene.py:205` | `replace(DemoMenuScene)` | No (es su escena madre, pero no es el principal); en `EXAMEN`, `ESC` vuelve a `TEORIA` (`:134-138`) sin salir |
| `inventory/skill_tree/world_map` embebidas | Ignoran `CANCEL` (`inventory_scene.py:141-142`, `skill_tree_scene.py:162-163`, `world_map_scene.py:354-355`) | Por diseño AUD-533 (la pausa gestiona la salida); en `standalone` hacen `pop()` |
| `keybinding_scene.py:177` | `replace(TitleScene)` siempre | Sí, pero pierde el origen: abierta desde Opciones (`options_scene.py:287` con `replace`), `ESC` cae a Título y Opciones se pierde |

**Casos donde `CANCEL` no saca por diseño (dos niveles):** `load_game_scene.py:187-191` (aborta crear partida), `keybinding_scene.py:138-141` (aborta espera de tecla), `skill_tree_scene.py:98-101` (aborta reencarnación). Cada nivel extra de `ESC` sin pista es un "no regresa" para el jugador.

## AUD-834: textos pegados sin desplazamiento — REAL

**Reporte:** "letras o textos muy pegados, como demos educativos con muchas opciones; hacerlo desplazante".

**Evidencia 1 — `demo_menu` desplaza pero pega:** `ITEM_H=34` fijo (`demo_menu_scene.py:64`) para rótulo `MEDIUM` + descripción `SMALL` (`:360-376`, sin hueco entre líneas). A 800 px las fuentes dan ~19+14=33 px en 34 px: queda 1 px de aire y con `text_scale>1` desborda (`demo_layout.py:252-254`). Referencia de cómo se corrige: `achievement_scene.py:51-66` (AUD-187).

**Evidencia 2 — menús que dibujan todo sin `visible_rows`/clip:** `shop_scene.py:179-208` (sin `visible_rows`, sin `set_clip`), `keybinding_scene.py:188-225` (14 acciones fijas en 2 columnas, `row_h=40` sin ventana), `quiz_system.py:102-142` (caja 320x160 fija, opciones sin paginado), `unit_theory_scene.py:293-307` (opciones de examen sin ventana; solo el "porque" recorta en `:315-319`), `pattern_demo_scene.py:491-534` (paneles con `y+=10` para fuentes de 14-17 px), `load_game_scene.py:261-306` (espaciado fijo 34 px). Patrón correcto a imitar: `title`/`options`/`bestiary` con `visible_rows` + clip (`widgets.py:213-216`).

**Falso positivo:** `filter_demo_scene.py` cicla modos con `TAB`, no es lista; no le aplica "hacerlo desplazante".

---

## Pistas de arreglo (sin aplicar en este documento)

| AUD | Arreglo propuesto | Regresión correspondiente |
|---|---|---|
| AUD-826 | Tira de pestañas con `Theme.MARGIN`, alto proporcional y `theme.font()`; lista "Menú" con `draw_panel()` y paso escalado | `RENDERER → tests/test_render_*`, más pruebas de pausa |
| AUD-827 | Revisar `PLAYER_WALK_SPEED` por diseño y bajar costo por fotograma (luz, bloom) o fijar objetivo realista 60 | `RENDERER → tests/test_render_*`, `scripts/bench_sprite_batch.py` |
| AUD-828 | Gravedad o caída para terrestres fuera de suelo + detección de borde compartida + descenso de escalones de 16 px | `ENEMIES → tests/test_enemy*`, `tests/ -k "collision"` |
| AUD-829 | Sustituir muestra `wind_indoor` loopeable, bajar volumen de ambiente y añadir `stop_ambient()` en `StageScene.on_exit` | `AUDIO → tests/test_audio*`, pruebas de transición de stage |
| AUD-830 | Cartel de tirolesa en zona G + `radio_de_enganche=30` en `Zipline_246` + salida con agacharse/abajo en `TirolesaState` | `MECANICAS → tests/test_lianas_y_tirolesas.py`, recorrido stage 0 |
| AUD-831 | Bajar `Vine_209/210` al alcance con salto normal o cartel que pida saltar; nada roto en código | `MECANICAS → tests/test_lianas_y_tirolesas.py`, recorrido stage 0 |
| AUD-832 | Indicador de scroll del título con `MenuList.desplazamiento` real; valorar subir `OPCIONES_VISIBLES` o agrupar opciones | `MENU → tests/test_menu_navigation.py` |
| AUD-833 | `progress_scene` vuelve a `DemoMenu` (aclarar pista `ESC: Back to Menu`); `keybinding` recuerda origen; documentar salidas de dos niveles | `MENU → tests/test_menu_navigation.py` |
| AUD-834 | `ITEM_H` de `demo_menu` con `SPACE_S` y `text_scale`; `visible_rows`/clip en `shop`, `keybinding`, `quiz`, `unit_theory`, `pattern_demo` | `MENU → tests/test_menu_navigation.py`, pruebas de demos |

Toda modificación futura declara su `AUD-800:` / `CERT-` y ejecuta `python scripts/check_change_safety.py`, según la invariante 9.

---

## Cierre AUD-827 — ritmo a 60 FPS, marcha a 120 y rejilla de sombras cacheada

**Medición A–G (Stage0 real, 1280x720 headless):** A: 90 px/s = 14,2 s/pantalla.
B: TARGET 120, budget 8,33 ms. C: frame 15,5 ms P50 / 22,4 P95. D: lighting
5,10 ms. E: postfx 3,15 ms. F: vsync no medible headless. G: pasos 1/120
correctos. Descartado con evidencia: IO por frame (era warmup de numba, 0
opens en 60 frames estables) y `dt` mal usado.

**Cambios (decisión del dueño 2026-09-09):** `TARGET_FPS` 120→60
(`settings.py`, `clock.py`: `FIXED_DT` 1/60 = el paso que AUD-390 suponía para
los mapas; mitad de pasos de simulación por segundo; presupuesto vigente
16,67 ms) y `PLAYER_WALK_SPEED` 90→120 (10,7 s/pantalla, verificado en runtime
con `Player` real: 120 px en 60 pasos). `PLAYER_SLOPE_SLIDE_SPEED` conserva 90
(tacto de cuestas intacto; comentario sincronizado). Rejilla de sombras:
`obs_h` cacheada e invalidada en `set_obstaculos` (antes ~4,5 construcciones
por fotograma). Coyote/buffer son temporales y no cambian. Comentarios de
playtests fechados (venado B-039) se conservan como historia.

**Evidencia:** `tests/test_aud827_ritmo.py` (3, fallaban antes) y
`tests/test_luz_rejilla_cache.py` (2, una fallaba antes) pasan. Frame tras el
cambio ≈ mismo P50 (el draw domina; el ahorro está en update y en coherencia
con vsync 60 Hz).

**Tests:** ritmo 3/3, rejilla 2/2, paso_fijo, perfiles_física, player_physics,
state_machine, mecanicas_f5, lianas, combo — PASS. `ruff` limpio.
`check_change_safety.py --ci` 17/17 PASS. Fallos en corrida masiva
(rects/daño/IA/reloj-musical) reproducidos en baseline sin mis cambios o
aislados 49/49 con mis cambios → PREEXISTING/infraestructura de orden, no de
este AUD (archivos ajenos en árbol sucio: `enemy_base.py`, TMX de mecánicas).

**Deuda de diseño explícita:** con 120 px/s huir de enemigos es más fácil
(`alert_speed` 55 sin re-balancear) y los saltos llegan más lejos; si algún
salto ajustado se rompe, revalidar nivel por nivel.

**CERT:** AUD-800 PERFORMANCE (medición) + PHYSICS (paso fijo).

---

## Cierre AUD-826 — pausa dimensionada con panel del kit

**Cambio:** `src/framework/stage/drawing_system.py` conserva `_draw_pause_panel` (orden AUD-555 intacto) y delega a `src/framework/stage/pausa_dibujo.py` (nuevo): tira de 20→40 px (`SPACE_XL`), pestañas insetadas `MARGIN`, texto centrado vertical con `theme.font(FONT_SMALL)`; lista "Menú" en panel `SURFACE`/`BORDER`/`RADIUS_L` con fila elegida en `SURFACE_RAISED` y paso de métrica real + `SPACE_S`. Se eliminó la fuente fija 20 y el lienzo cacheado (el fondo ahora es `fill(Theme.BG)`). No se tocó HUD, Mapa, Equipo, Habilidades, diálogo, subtítulos, lógica ni input de pausa.

**Evidencia:** `tests/test_pausa_dimensionada.py` (2 pruebas) fallaba antes (franja 20 px, sin panel) y pasa después. Presupuesto de líneas 850/850 intacto por extracción (disciplina AUD-352).

**Tests:** `test_pausa_dimensionada` 2/2, `test_reported_ui_bugs` 15/15, `test_particion_de_drawing_system`, `test_ui_consistency`, `test_las_llamadas_de_dibujo`, `test_native_rendering` 17+3 SKIP — PASS. `ruff` limpio. `check_change_safety.py --ci` 17/17 PASS.

**CERT:** AUD-800 RENDERER (dibujado de UI de stage).
