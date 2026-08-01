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
| `GhostData` | `speedrun_mode.py` | **Decidir.** Graba la posición del jugador para el fantasma del modo speedrun. Ni se graba ni se reproduce: falta el consumidor |
| `ParamPanel` | `engine/scenes/param_panel.py` | **Decidir.** Widget de parámetros para las demos; ninguna demo lo instancia |
| `SceneRegistry` | citado en 25 y 28 | Falso positivo del barrido: se usa por nombre, no por símbolo |
| `CameraLock` | `stage_loader.py` | Se usa **sólo dentro del fichero que lo define**. Funciona; conviene mirar si la escena debería leerlo |
| `SineFlight` | vuelo senoidal | El comportamiento existe en `EnemyFlying`; la clase suelta no la usa nadie |
| `sincronizar_salud` | ECS | Quedó sin usar al pasar `Salud` a componente-vista (F5) |
| `build_gradient` | VFX | Sin usos |
| `crossfade_ambient`, `set_ambient_volume` | `audio_manager.py` | API de audio escrita y nunca llamada |
| `check_player_contact` | `enemy_archer.py` | El resto de enemigos usa `_check_player_contact`; éste quedó público y suelto |
| `on_stage_start`, `on_player_landed`, `on_enemy_died`, `on_next_trigger_entered` | plantilla de estudiante | **Correcto que estén sin usar.** Son los ganchos que el estudiante rellena |
| `ComboDemoScene`, `LeaderboardScene`, `LoadingScene`, `PipelineBuilderScene`, `ProgressScene`, `SandboxScene`, `StageWizardScene` | escenas | Falso positivo: el registro las construye por cadena |

**Acción recomendada:** decidir sobre `GhostData` y `ParamPanel` —o se enchufan
o se van—, y retirar `SineFlight`, `sincronizar_salud` y `build_gradient`.

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

**Acción recomendada:** reescribir §5 de `17_BOSS_SPEC.md` contra los cuatro
jefes que existen, como se hizo con `07_STAGE0_DESIGN.md`. Y decidir si
`BossSpawn` se implementa o se retira de la especificación: hoy un estudiante
que lo escriba en Tiled recibe un aviso de tipo desconocido.

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

**Acción:** reescribir la especificación contra el código. No hay nada que
implementar aquí.

---

## 4. Especificaciones que describen una API distinta de la real

| Documento | Qué cita y no existe |
|---|---|
| `09_HUD_SPEC.md` | `hurt_display_timer`, `reveal_count`, `Message` |
| `04_PLAYER_SPEC.md` | `_health`, `facing_direction`, `damage_amount` (nombres viejos) |
| `11_FILTER_TOOLS_SPEC.md` | `KERNEL_X`, `KERNEL_Y`, `umbral_alto`, `umbral_bajo` |
| `12_VISION_TOOLS_SPEC.md` | `label_array`, `component_sizes`, `bounding_rect`, `local_binary_pattern` |
| `14_PROFESSOR_DELIVERABLE_MATRIX.md` | `AnimationController`, `SpriteSheet`, `OneWay_` |
| `23_DATA_SCHEMAS.md` | esquemas de guardado con campos que ya no están |

Son documentos escritos antes del código y nunca revisados contra él. Ninguno
rompe nada hoy; todos engañan a quien los lea para programar.

---

## 5. Lo que falta de sistema, no de nombre

Esto no sale del barrido automático: sale de la auditoría de agosto
(`61_AUDITORIA_AAA_2026-08.md`) y del inventario (`62_ESTADO_DEL_PROYECTO.md`).

| Falta | Bloquea | Esfuerzo |
|---|---|---|
| **Reloj musical** (BPM, compás, posición de pista, latencia) | los niveles rítmicos y la nota de audio | 2–3 semanas |
| **Buses de mezcla, ducking, reverberación por zona** | audio | 1 semana |
| **Atlas de sprites y batching** | gráficos y rendimiento | 1 semana |
| **Post-procesado en GPU** (la tubería existe y no se usa para esto) | gráficos y rendimiento | 1 semana |
| **Cutscenes: acciones nuevas, guiones desde TMX, no bloquear** | narrativa | 3–4 días |
| **Curva de dificultad medida** de los 15 escenarios | diseño | 3 días |
| **Partir `stage_scene.py`** (1.549 líneas) | mantenibilidad | 1 semana |
| **Mutación y resistencia en CI** | QA | 3 días |
| **15 tipos de objeto sin usar en ningún mapa**, 10 de ellos enemigos | contenido | 2 días |

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
| Medidor de estamina | Falta; el patrón está resuelto en `special_meter` | 4 h |
| Empujar bloques | No existe | 1 día |
| ~~Vista cenital~~ | **HECHO** (AUD-129). `vista = cenital` en el TMX | — |
| Bloques destructibles | Requiere `collision_rects` mutable en caliente | 1 día |

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
