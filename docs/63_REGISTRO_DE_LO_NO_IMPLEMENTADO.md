---
document_id: "LOI-PENDIENTE-63"
title: "Registro de lo prometido y no implementado"
tags: ["pendiente", "huerfanos", "deuda", "auditoria"]
source: "docs/63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md"
date_processed: "2026-08-01"
---

# Registro de lo prometido y no implementado

**Fecha:** 1 de agosto de 2026
**Se regenera con:** `python scripts/audit_docs_vs_code.py`

---

## Para qué sirve este documento

Cada documento del proyecto cita identificadores entre comillas invertidas.
Este registro recoge los que **el proyecto no tiene** y los que **tiene y nadie
usa**. Es la lista de promesas pendientes.

Existe porque este mes tres documentos resultaron ser ficción, y en los tres
casos el coste no fue el documento sino lo que se construyó encima:

* `07_STAGE0_DESIGN.md` especificaba un mapa de 240 × 14. El real mide 100 × 38.
  De esa ficción salió un generador que llevaba meses listo para borrar el
  escenario de referencia del curso.
* `03_ARCHITECTURE.md` prometía un `transitions.py` con cinco clases y cero usos.
* El README decía 1.333 pruebas en español y 640 en inglés. Había 2.020.

**Un documento que miente es peor que uno que falta.** El que falta se nota; el
que miente se cree, y alguien programa contra él.

### Lo que este registro NO dice

Que todo lo de aquí sea un defecto. Una especificación puede describir a
propósito algo que aún no existe —para eso está—. Lo que no puede es que nadie
sepa cuál de las dos cosas es. Este documento pone la etiqueta.

---

## 1. Los huérfanos: existen y nadie los usa

Comprobado con análisis de alcanzabilidad sobre todo el árbol.

| Identificador | Dónde vive | Veredicto |
|---|---|---|
| ~~`GhostData`~~ | `speedrun_mode.py` | **HECHO** (AUD-142). Enchufado: la escena graba, guarda la mejor carrera y dibuja el fantasma anterior |
| ~~`ParamPanel`~~ | `engine/scenes/param_panel.py` | **HECHO** (AUD-146). Lo usa la vista de árbol de la demo de patrones, con su rango y su aviso de cambio |
| `SceneRegistry` | citado en 25 y 28 | Falso positivo del barrido: se usa por nombre, no por símbolo |
| ~~`CameraLock`~~ | `stage_loader.py` | **HECHO** (AUD-143). Y la sospecha era buena: su `rect` se guardaba y no se leía nunca, así que **una sola zona congelaba la cámara en todo el nivel**. `boss_rey` tenía un parche escrito para rodearlo |
| `SineFlight` | vuelo senoidal | **Falso positivo, comprobado.** La usan `make_strategy` y otras dos estrategias del mismo módulo |
| `sincronizar_salud` | ECS | **Correcto que siga.** Es un hueco vacío a propósito desde F5.12: alguna entrega puede llamarlo y borrarlo les rompería el código |
| `build_gradient` | VFX | **Falso positivo, comprobado.** La llama `lighting.py` para construir el degradado de cada foco |
| ~~`crossfade_ambient`, `set_ambient_volume`~~ | `audio_manager.py` | **HECHO** (AUD-149). El bus de ambiente pasa por `set_ambient_volume`, y la escena **funde** entre ambientes al volver de una sala de jefe en vez de cortar en seco |
| ~~Audio ambiental por clima~~ | `weather_system.py` | **HECHO** (AUD-145). El mapa devuelve la ruta del fichero real; `snow` y `fog` suenan con el viento que sí existe, y `rain` y `storm` **declaran que les falta el asset** en vez de callarse |
| ~~`check_player_contact`~~ | 4 enemigos | **HECHO, y era un fallo jugable** (AUD-149). No estaba «suelto»: arquero, asesino, bruto y hechicero sobreescribían el alias **público**, y el motor llama al privado. Las flechas y los orbes no hacían daño ni se podían parar, la onda del bruto no golpeaba, el asesino dañaba estando invisible y su puñalada no hacía nada |
| `on_stage_start`, `on_player_landed`, `on_enemy_died`, `on_next_trigger_entered` | plantilla de estudiante | **Correcto que estén sin usar.** Son los ganchos que el estudiante rellena |
| `ComboDemoScene`, `LeaderboardScene`, `PipelineBuilderScene`, `ProgressScene`, `SandboxScene`, `StageWizardScene` | escenas | Falso positivo: el registro las construye por cadena (`scene_registry.py:72-82`) |
| `LoadingScene` | escenas | **Huérfana de verdad** (medido el 2026-08-05). Esta fila la daba por falso positivo junto a las seis de arriba, y no lo es: **no está en `scene_registry`**, y su única referencia en todo el repositorio es `tests/test_scene_smoke.py`. El hilo de carga y la barra de progreso están escritos y probados, y no hay forma de llegar a ellos jugando. Ver `docs/87` §15.6 |

> **Corrección (AUD-142). Tres de estas recomendaciones eran falsas, y el
> error fue mío.** La versión anterior de esta sección decía «retirar
> `SineFlight`, `sincronizar_salud` y `build_gradient`». Comprobado contra el
> código, una por una:
>
> * `SineFlight` la usan `make_strategy` y otras dos estrategias del mismo
>   fichero. Borrarla habría roto el vuelo de la mitad del bestiario.
> * `build_gradient` la llama `lighting.py`. Borrarla habría apagado los focos.
> * `sincronizar_salud` es un hueco vacío **a propósito**, documentado como
>   tal: se dejó para que las entregas que lo llamen no se rompan.
>
> El barrido marca como huérfano lo que sólo se usa dentro de su propio
> fichero, y eso no es código muerto. Es la segunda vez este mes que publico
> una recomendación sacada de su salida sin comprobarla —la primera fue
> AUD-133, los sonidos de muerte— y el aviso lleva escrito en el propio script
> desde que lo escribí.

> **Lo que enseñó la sección 1 al terminarla (AUD-149).** De sus doce filas,
> **tres eran falsos positivos**, **dos eran correctas tal cual están** —los
> ganchos del estudiante y el hueco de compatibilidad—, y **una escondía el
> fallo más jugable del mes**: cuatro enemigos con su lógica de daño en un
> método que el motor no llama.
>
> La lección no es que el barrido falle. Es que su salida son **preguntas**, y
> la respuesta a cada una hay que ir a buscarla al código. Nueve de las doce
> filas necesitaron abrir el fichero para saber de cuál de los tres tipos era.

**Acción pendiente (actualizado 2026-08-03, AUD-233).** La frase anterior decía
«ninguna», y envejeció: el barrido no se había repetido desde entonces y en esa
ventana aparecieron **tres huérfanos nuevos**, los tres encontrados a mano y no
por herramienta:

| Huérfano | Cómo se manifestaba | Resuelto en |
|---|---|---|
| `SpeedrunTimer.save()` | Nadie lo llamaba; la pantalla de récords rellenaba el hueco con **tiempos escritos a mano** | AUD-202 |
| `LeaderboardScene` | Registrada y sin ninguna entrada de menú que la abriera | AUD-202 |
| `BossRushMode` | Construido, arrancado y abandonado, con `docs/44` declarándolo «✅ Complete — scoring, health carry-over» | AUD-232 / GAP-030 |

La lección de la sección anterior —que la salida del barrido son preguntas— se
mantiene entera. Lo que faltaba era **repetir el barrido**, y que repetirlo no
dependiera de que alguien se acordara.

Desde AUD-233 lo hace `scripts/check_orphan_systems.py`, con
`tests/test_sistemas_huerfanos.py` ejecutándolo en la suite. Su puerta es
estrecha a propósito: sólo falla cuando un módulo **que un documento declara
terminado** tiene un símbolo que las pruebas ejercitan, el juego no invoca y
nadie ha clasificado todavía. Medida actual: 181 candidatos, 16 verificados como
no-defectos, 8 huérfanos reales anotados en **GAP-031**.

---

## 2. `17_BOSS_SPEC.md` — 22 patrones de ataque que ningún jefe implementa

Es el hallazgo más grande del barrido. La especificación de jefes nombra estos
patrones y **ninguno existe en el código**:

```
BODY_SLAM        DARK_FIELD       DIVE_BOMB        FEATHER_STORM
FEATHER_TOSS     FULL_FEATHER_STORM               GOLD_BURST
GOLD_RUSH        GROUND_SLAM      MASK_BEAM        MASK_FRAGMENT_STORM
ORBIT_SHRINK     PEARL_VOLLEY     RAPID_DIVE       SERPENT_CARPET
SERPENT_WAVE     SUMMON_ECHOES    VENOM_BURST      WIND_BLAST
```

Más `BossSpawn` —un tipo de objeto de Tiled que la especificación describe y
que el motor **no acepta**— y `ReyMetad`.

**Cómo leerlo con justicia.** Los cuatro jefes entregados por los estudiantes
tienen sus propios ataques, con otros nombres. La especificación describe un
diseño anterior que nadie siguió. No es que los jefes estén incompletos: es que
el documento describe otros jefes.

**HECHO (AUD-150), y con una corrección de partida: los jefes que existen son
TRES, no cuatro.** `BossVenado`, `BossRey` y `BossPaburu`. El cuarto —el
Gavilán de §5— no tiene clase, ni sprites, ni escena: sólo un hueco reservado
en el registro de escenarios y una línea en los créditos.

> **Corrección (AUD-254). El párrafo de arriba envejeció y hay que leerlo con
> fecha.** Hoy `BossGavilan` **sí existe**: `class BossGavilan(BossBase)` en
> `src/stages/stage3_4_boss_gavilan/boss_gavilan.py`, con su escena
> `Stage3_4BossGavilanScene` y su mapa de 58,7 KB. La entrega llegó después de
> escribirse esta sección.
>
> Lo que sigue siendo cierto es que **es parcial** —tiene la fase orbital y no
> los patrones que §2 lista—, que es lo que `75_BIBLIA_TECNICA.md` §21.3 dice.
> Los jefes son **cuatro**, uno de ellos a medias.
>
> Es la misma lección de AUD-142 por tercera vez: un veredicto medido caduca, y
> un documento que no se vuelve a medir pasa de ser un inventario a ser una
> creencia.

No se reescribió la especificación: se **etiquetó**, que es lo que este
registro pide. `17_BOSS_SPEC.md` abre ahora con una §0 que dice, jefe por
jefe, qué clase lo implementa, cuántas fases tiene de verdad y cuáles de sus
patrones existen; y cada apartado lleva su propio aviso. Borrar el diseño
habría sido peor: un diseño de jefe sin implementar es lo que una
especificación **debe** contener; lo que no puede es que nadie sepa cuál de
las dos cosas está leyendo.

Los 22 patrones siguen apareciendo en el barrido, y **está bien que
aparezcan**: no existen. La diferencia es que ahora el documento lo dice
primero.

`BossSpawn` sigue sin implementarse y §0 lo advierte: un estudiante que lo
escriba en Tiled recibe un aviso de tipo desconocido. Los tres jefes reales se
colocan con su tipo propio.

---

## 3. `05_ENEMY_SPEC.md` — nombres viejos, no funciones ausentes

> **Corrección (AUD-133).** La primera versión de esta sección decía que los
> enemigos «mueren en silencio» y lo llamaba «el hallazgo jugable». **Era
> falso, y el error fue mío.** El barrido encontró que los nombres
> `sfx_walker_die`, `sfx_flying_die` y `sfx_shooter_die` no existen, que es
> cierto; yo salté de ahí a «la función no existe», que no lo es.
>
> Comprobado después, eslabón por eslabón: `EnemyBase._die` **sí** emite
> sonido, `StageScene` lo traduce, y los dos ficheros están en el disco.
> `tests/test_sonido_de_muerte_llega.py` recorre la cadena entera.
>
> Es el falso positivo contra el que escribí el aviso en el propio script
> —«no entiende contexto»— y que luego no me apliqué al leer su salida. Una
> lista de hallazgos automáticos no es una lista de defectos hasta que alguien
> comprueba cada uno contra el código.

| Prometido | Estado real |
|---|---|
| `WIND_UP` | **No existe**, y es correcto: `TELEGRAPHING` cumple su función. Lo que hay que corregir es el documento |
| `detection_rect`, `patrol_origin` | Nombres viejos. Existen como `detection_range_x` y `detection_range_y` |
| `sfx_walker_die`, `sfx_flying_die`, `sfx_shooter_die` | Nombres viejos. El motor usa **dos** sonidos por tamaño —`SFX_ENEMY_DIE_SMALL` y `_LARGE`— en vez de uno por especie, que con treinta especies es mejor diseño: dos ficheros que mantener en vez de treinta |

**HECHO (AUD-150).** `05_ENEMY_SPEC.md` abre con una §0 que corrige los cinco
nombres, y los sitios donde el documento los usaba están arreglados: la
detección son dos distancias y no un rectángulo, `_patrol_origin` es privado,
y el ciclo del Charger se describe con los estados que de verdad tiene
—`TELEGRAPHING` → `CHASE` → `STUNNED`—.

Aparecieron dos más al comprobar: **`death_sfx` y `hit_sfx` tampoco son
atributos**, y nunca lo fueron. Un enemigo no guarda el nombre de su sonido:
emite un evento y la escena decide. Es mejor así — cambiar el sonido de muerte
de todo el bestiario es una línea, no treinta atributos.

El documento ya no aparece en el barrido.

---

## 4. Especificaciones que describen una API distinta de la real

> **Corrección (AUD-254). Más de la mitad de esta tabla eran falsos positivos,
> y el error fue mío otra vez.** Comprobado nombre por nombre contra el árbol
> el 4 de agosto de 2026, con `grep -rl` sobre `src/`. La versión anterior de
> esta sección decía que doce identificadores «no existen». Ocho **sí existen**:
>
> * `KERNEL_X`, `KERNEL_Y`, `umbral_alto` y `umbral_bajo` viven en
>   `src/framework/processing/edge_detection.py`. El barrido los buscó en
>   `filter_tools.py` —el módulo que da nombre al documento— y no los encontró
>   porque el pipeline de Canny se escribió aparte.
> * `label_array`, `component_sizes` y `bounding_rect` son campos de las
>   dataclases de resultado de `vision_tools.py`; `local_binary_pattern` es un
>   método del mismo módulo.
> * `_health` y `facing_direction` son atributos de `Player`
>   (`player.py:345` y `player.py:308`). Llamarlos «nombres viejos» era
>   exactamente lo contrario de la verdad.
>
> Es la tercera vez que este registro publica una recomendación sacada de la
> salida del barrido sin abrirla contra el código —AUD-133 los sonidos de
> muerte, AUD-142 `SineFlight`— y el aviso lleva escrito en el propio script
> desde el primer día: **su salida son preguntas**. Una tabla de «esto no
> existe» que se equivoca en ocho de doce no informa: manda a alguien a
> reescribir documentación correcta.

| Documento | Qué cita | Comprobado el 2026-08-04 |
|---|---|---|
| `09_HUD_SPEC.md` | `hurt_display_timer`, `reveal_count`, `Message` | **No existen.** La clase real es `MessageBox` (`ui/message_box.py:17`) |
| `04_PLAYER_SPEC.md` | `_health`, `facing_direction`, `damage_amount` | `_health` y `facing_direction` **sí existen**; sólo `damage_amount` es un nombre muerto |
| `11_FILTER_TOOLS_SPEC.md` | `KERNEL_X`, `KERNEL_Y`, `umbral_alto`, `umbral_bajo` | **Los cuatro existen**, en `edge_detection.py`. Falso positivo |
| `12_VISION_TOOLS_SPEC.md` | `label_array`, `component_sizes`, `bounding_rect`, `local_binary_pattern` | **Los cuatro existen**, en `vision_tools.py`. Falso positivo |
| `14_PROFESSOR_DELIVERABLE_MATRIX.md` | `AnimationController`, `SpriteSheet`, `OneWay_` | **No existen.** Fila correcta |
| `23_DATA_SCHEMAS.md` | esquemas de guardado con campos que ya no están | Sin volver a medir |

Lo que queda en pie: `09_HUD_SPEC.md` y `14_PROFESSOR_DELIVERABLE_MATRIX.md`
citan API que no existe, y una línea de `04_PLAYER_SPEC.md`. Son documentos
escritos antes del código y nunca revisados contra él. Ninguno rompe nada hoy;
esos tres engañan a quien los lea para programar.

---

## 5. Lo que falta de sistema, no de nombre

Esto no sale del barrido automático: sale de la auditoría de agosto
(`61_AUDITORIA_AAA_2026-08.md`) y del inventario (`62_ESTADO_DEL_PROYECTO.md`).

| Falta | Bloquea | Esfuerzo |
|---|---|---|
| ~~Reloj musical~~ | **HECHO** (AUD-137). `bpm`/`compas`/`desfase_audio` en el mapa, `patron` en los bloques, posición tomada del mezclador | — |
| ~~Buses de mezcla y ducking~~ | **HECHO** (AUD-144). Cuatro buses y la música se aparta cuando alguien habla | — |
| **Reverberación por zona** | audio | **No se puede sobre SDL.** Su mezclador no tiene efectos: haría falta convolucionar cada sonido al cargarlo o una biblioteca de DSP. Documentado en `mixer_buses.py` |
| ~~Atlas de sprites y batching~~ | **HECHO** (AUD-138), con una salvedad medida: el atlas **no** acelera el dibujado en la ruta software (2,06 → 2,35 ms). Lo que gana es carga (3×) y `blits()` (16 %) |
| **Post-procesado en GPU** | gráficos | **MEDIDO** (AUD-148), y la respuesta no era la esperada: en la máquina de medida el bloom en GPU sale **5× más lento** (8,3 ms contra 1,7 ms) porque SDL cae a software sin tarjeta. Presentar sí es barato (0,18–0,36 ms). Queda `scripts/bench_gpu_postproc.py` para medirlo donde toque y `PresentadorGPU` apagado por defecto |
| ~~Cutscenes: acciones nuevas, guiones desde TMX, no bloquear~~ | **HECHO** (AUD-136). Tipo `Cutscene`, guion en texto, escenas que no bloquean y salto que ejecuta el final | — |
| ~~Curva de dificultad medida~~ | **HECHO** (AUD-151). `scripts/difficulty_curve.py` mide once escenarios y `docs/67_CURVA_DE_DIFICULTAD.md` recoge lo que salió: el tutorial `stage0` es el nivel normal más exigente (48,8) y hay dos escalones de más del doble. Los jefes quedan exentos: un jefe *debe* ser un pico | — |
| ~~Partir `stage_scene.py`~~ | **HECHO** (AUD-152). De 1.884 a 1.405 líneas, con tres mixins de lectura en `scenes/stage_parts/`: ambiente, señales y fantasma. Separación por legibilidad, no por dependencia — las subclases de los estudiantes siguen sobreescribiendo lo mismo | — |
| ~~Mutación en CI~~ | **HECHO** (AUD-147). `scripts/mutation_check.py`, semanal y a mano; acotado a tres módulos para que el informe se lea | — |
| ~~Tipos de objeto sin usar en ningún mapa~~ | **HECHO** (AUD-153). Eran **17**, no 15: siete de escenario y diez especies del bestiario. Colocados en las salas 8 y 9 del laboratorio, con una prueba que vuelve a rojo si alguien añade un tipo y no lo coloca. Los hace alcanzables y ejercitados; **no** arregla la curva de dificultad del juego | — |

---

## 6. Mecánicas del *backlog* pendientes

De la tabla de viabilidad, lo que sigue sin hacer:

| Mecánica | Estado real | Esfuerzo |
|---|---|---|
| ~~Resortes y rebotes~~ | **HECHO** (AUD-131). Tipo `Spring`, componente y sistema | — |
| ~~Puertas cronometradas~~ | **HECHO** (AUD-132). `cierra_en`, y nunca sobre el jugador | — |
| ~~Interruptores que cambian el mundo~~ | **HECHO** (AUD-132). `abre_con` en la puerta cierra el circuito | — |
| ~~Pogo (ataque abajo que rebota)~~ | **HECHO** (AUD-134). Acertar devuelve impulso y recupera el dash aéreo | — |
| ~~Inundación que sube~~ | **HECHO** (AUD-135). `sube`, `sube_hasta` y `arranca_con` en la `HazardZone`, y el motor la dibuja | — |
| ~~Medidor de estamina~~ | **HECHO** (AUD-141). Propiedad `estamina` del mapa; **apagada por defecto** para no cambiar los quince escenarios entregados | — |
| ~~Empujar bloques~~ | **HECHO** (AUD-140). Tipo `PushBlock`, con gravedad y vuelta a su sitio al morir | — |
| ~~Vista cenital~~ | **HECHO** (AUD-129). `vista = cenital` en el TMX | — |
| ~~Bloques destructibles~~ | **HECHO** (AUD-140). Tipo `BreakableBlock`. No hizo falta mutar `collision_rects`: se suman, como las puertas cerradas | — |

**Ya implementadas** de esa misma tabla, y conviene no volver a estimarlas:
escaleras y lianas (`Vine`, `CLIMBING`), tirolesas (`Zipline`, `ZIPLINE`),
plataformas móviles **con arrastre del pasajero**, cintas transportadoras
(`Conveyor`), cono de visión (`Guard`) y patrulla sobre B-Spline.

---

## 7. Cómo mantener este registro

```bash
python scripts/audit_docs_vs_code.py          # informe legible
python scripts/audit_docs_vs_code.py --json   # para automatizar
```

El barrido tiene límites y conviene conocerlos: no entiende contexto, así que
un documento puede citar legítimamente algo que aún no existe. Lo que sí hace
es **no dejar que nadie se entere por accidente**.

Dos precauciones que ya costaron una reescritura del script:

* La primera versión marcaba `ValueError`, `None`, `BG_Far` —el nombre de una
  capa de Tiled— y `StandardScaler` de scikit-learn. 65 documentos con
  hallazgos, casi todo ruido.
* La segunda daba **964 huérfanos** porque contaba los parámetros de función:
  un parámetro sólo se usa dentro de su propia función, así que todos parecían
  muertos.

Un informe con esa proporción de falsos positivos se lee una vez y se ignora
para siempre — que es exactamente lo que pasó con las seis herramientas de
calificación que este mes hubo que arreglar por castigar trabajo correcto.

---

## Documentos relacionados

- [[62_ESTADO_DEL_PROYECTO.md|Qué hay, qué mejorar, qué falta]]
- [[61_AUDITORIA_AAA_2026-08.md|Auditoría y puntuación]]
- [[60_GUIA_COMPLETA_DEL_MOTOR.md|Manual del diseñador]]
