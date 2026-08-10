---
document_id: "LOI-PLAN-91"
title: "Plan de cierre — todo lo abierto, medido, y en qué orden se cierra"
tags: ["plan", "auditoria", "gaps", "cierre", "worldsimulation"]
source: "docs/91_PLAN_DE_CIERRE.md"
date_processed: "2026-08-09"
---

# Plan de cierre

**Fecha:** 9 de agosto de 2026
**Commit base:** `3902137` (+ árbol de trabajo con AUD-343…356 sin commitear)
**Encargo:** juntar *todos* los gaps, huecos, errores, avisos y defectos
abiertos, y arrancar el plan de corrección. `WorldSimulation` es la última
característica que se añade; después, sólo cierre.

---

## 0. Qué promete este plan, y qué no

Conviene decirlo antes de la primera tabla, porque cambia cómo se lee todo lo
demás.

**«Que no existan más gaps» no es un estado alcanzable.** Un `GAP-NNN` en este
repositorio no es un defecto: es *una decisión pendiente que se ha escrito en
vez de olvidarse*. Mientras el proyecto se use —26 entregas al año, una
biblioteca que publica versiones nuevas, un curso que cambia— van a seguir
apareciendo. Un repositorio con cero GAPs no es uno sin deuda: es uno que ha
dejado de anotarla. GAP-034 es la prueba: nació **sin que nadie tocara el
código**, sólo porque `ruff` publicó una versión.

Lo que sí es alcanzable, verificable y es lo que este plan persigue:

> **Todo ítem abierto está (a) cerrado con su prueba, (b) convertido en una
> decisión escrita y fechada del dueño, o (c) protegido por una invariante que
> dice por qué no se toca. Ninguno queda en «ya lo miraremos».**

Y una condición de parada que sí se puede comprobar con un comando:

```
KNOWN_GAPS.md sin entradas abiertas que no sean decisiones del dueño
docs/89 §6 sin filas P sin resolver
scripts/grade_stage.py sin `errors` (los `warnings` de diseño son otra cosa)
scripts/check_orphan_systems.py --ci verde y sin PENDIENTES sin fecha
los 12 gates verdes, ejecutados
```

---

## 1. Inventario completo, medido

Nada de esta sección sale de la memoria. Cada bloque lleva el comando que lo
produce, para que se pueda re-medir el día que se lea.

### 1.1 De dónde sale cada cosa

| Fuente | Comando | Qué aporta |
|---|---|---|
| `KNOWN_GAPS.md` | `grep "^## " KNOWN_GAPS.md \| grep -v Resuelto` | 3 entradas abiertas |
| `docs/89` §6 | lectura | 6 hallazgos P sin cerrar |
| `docs/63` | lectura | especificaciones que citan API inexistente |
| `docs/87` §27 | lectura | plan del dueño: fases 1-6 **hechas**, 7 suspendida |
| Calificador de niveles | `scripts/grade_stage.py assets/maps/ --json` | 4 errores + 48 avisos en 16 mapas |
| Cobertura TMX | `scripts/check_tmx_coverage.py --ci` | 1 tipo de objeto de 70 sin colocar |
| Huérfanos | `scripts/check_orphan_systems.py` | 3 símbolos reales sin consumidor |
| Suite | `pytest tests/ -q` | 4.353 pasan, 7 omitidas, 20 avisos |
| Trinquete de tipos | `cat mypy_scope.txt` | 2 paquetes de 22 bajo mypy |
| Esta auditoría | `docs/70` iteración 15 | AUD-353…356 + GAP-034/035 |

### 1.2 El inventario

**Leyenda de decisión:** 🔧 se cierra · 🧑‍⚖️ decide el dueño · 🛡️ protegido por
invariante · 📐 es contenido (entregas de estudiantes)

#### A — Herramientas, gates y proceso

| # | Ítem | Evidencia | Decisión |
|---|---|---|---|
| A1 | **GAP-034** — `ruff>=0.6` sin tope: la definición de «verde» la fija quien publique río arriba | El gate estuvo rojo en `dev` sin que cambiara una línea (AUD-353) | 🧑‍⚖️ política de dependencias |
| A2 | **GAP-035** — el detector de huérfanos exonera todo lo que re-exporta un `__init__.py` | Medido: el parche barato da 11 falsos positivos de 12 | 🔧 reescribir sobre `ast.Call` |
| A3 | **P2** — anotación `"state": str` incorrecta en `speedrun_mode.py:249` | `docs/89` §6 | 🔧 trivial |
| A4 | Trinquete mypy: **2 paquetes de 22** (`src/engine/core`, `src/engine/input`) | `mypy_scope.txt` | 🔧 por lotes, un paquete por commit |
| A5 | `mutation_check` acotado a **3 módulos** | `docs/89` §16 fila 14 | 🔧 ampliar a física y resolutor |
| A6 | Sin gate de **tiempo de suite** (hoy 6-8 min y creciendo) | medido: 372 s, 489 s | 🔧 presupuesto con umbral |
| A7 | `computer-vision-course/` (8,2 MB, con su propio `tests/`) sin seguir **y sin ignorar** | `git status --porcelain` | 🧑‍⚖️ ignorar o sacar del árbol |
| A8 | **Cuatro frentes de trabajo sin commitear** (AUD-343…356) | `git diff --stat`: 21 ficheros + 12 nuevos | 🔧 partir en commits por AUD |

#### B — Documentación

| # | Ítem | Evidencia | Decisión |
|---|---|---|---|
| B1 | **P3** — recuento de documentos contradictorio | `00_MASTER_INDEX.md:13,27` | 🔧 |
| B2 | `09_HUD_SPEC.md` cita `hurt_display_timer`, `reveal_count`, `Message`: **no existen** | `docs/63` §4 | 🔧 corregir el doc |
| B3 | `04_PLAYER_SPEC.md` cita `damage_amount`: nombre muerto | `docs/63` §4 | 🔧 |
| B4 | `14_PROFESSOR_DELIVERABLE_MATRIX.md` cita `AnimationController`, `SpriteSheet`, `OneWay_`: no existen | `docs/63` §4 | 🔧 |
| B5 | `05_ENEMY_SPEC.md` — `WIND_UP`, `detection_rect`, `patrol_origin`, `sfx_*_die`: nombres viejos | `docs/63` §3 | 🔧 |
| B6 | `23_DATA_SCHEMAS.md` — esquemas de guardado «sin volver a medir» desde 2026-08-04 | `docs/63` §4 | 🔧 comprobador AST, como AUD-307 |
| B7 | `17_BOSS_SPEC.md` — **22 patrones de ataque** que ningún jefe implementa | `docs/63` §2 | 🧑‍⚖️ ¿spec o catálogo aspiracional? |
| B8 | Recuento de pruebas del README tras las 18 nuevas (4.301 declaradas / 4.360 reales) | dentro del 5 % que tolera la prueba | 🔧 al commitear |

#### C — Motor y código

| # | Ítem | Evidencia | Decisión |
|---|---|---|---|
| C1 | Un efecto **crítico** puede atenuarse a cero mientras la música se agacha | `audio_manager.py:289` + AUD-348 | 🧑‍⚖️ mezcla; fix propuesto: suelo de atenuación |
| C2 | **P4 / GAP-024** — salto aéreo documentado y sin conectar, congelado por prueba a propósito | `KNOWN_GAPS.md` | 🛡️ decisión docente tomada |
| C3 | **P6** — la IA predictiva no tiene métrica de acierto | `docs/63` | 🔧 medir contra la heurística |
| C4 | 3 huérfanos reales: `AchievementDef`, `AchievementProgress`, `init_instance` | `check_orphan_systems.py` | 🔧 conectar o retirar |
| C5 | `BossSpawn`: 1 de 70 tipos TMX que ningún mapa usa | `check_tmx_coverage.py --ci` | 🔧 colocarlo en el laboratorio |
| C6 | Reverberación por zona | **Imposible sobre el mezclador de SDL** (`mixer_buses.py`) | 🛡️ decisión cerrada; documentar como NO SE HARÁ |
| C7 | `pygame.image.tostring` obsoleto desde pygame 2.3 — **20 avisos** por suite | `gl_pipeline.py:552` | 🔧 migrar a `tobytes` |
| C8 | 7 pruebas omitidas sin clasificar de una en una | `pytest -rs` | 🔧 una línea de motivo por skip |

#### D — Contenido de niveles (48 avisos + 4 errores del calificador)

| # | Ítem | Cuántos | Decisión |
|---|---|---|---|
| D1 | `author` ausente en los metadatos | **12 de 16 mapas** | 🔧 es una propiedad TMX; el aviso más repetido y el más barato |
| D2 | Mapas sin **ningún** checkpoint | 4 | 📐 / 🧑‍⚖️ |
| D3 | Hueco entre checkpoints > 600 px (peor: **3.048 px**) | 6 | 📐 |
| D4 | Repechos que el jugador no puede saltar (304-544 px) | 5 | 📐 |
| D5 | Plataformas sin ruta desde el spawn | 8, en 6 mapas | 📐 |
| D6 | «Ningún salto pone a prueba al jugador» | 4 | 📐 |
| D7 | **GAP-018** — el contenido lo hacen los estudiantes | — | 🛡️ `docs/87` §27 fase 7, suspendida por el dueño |

#### E — La última característica

| # | Ítem | Estado |
|---|---|---|
| E1 | **`WorldSimulation` + `EnvironmentState`** | `environment.py` escrito; falta la simulación, el cableado y las pruebas |

---

## 2. Lo que ya NO está abierto, y conviene no volver a abrirlo

Para que nadie relea `docs/63` y crea que hay más trabajo del que hay:

- **Las fases 1-6 del plan del dueño están hechas** (`docs/87` §27): perfil de
  física por contexto, resolutor compartido, física ampliada, SpriteBatch,
  GPU con normal mapping, y 2.5D. La fase 7 (contenido) la suspendió el dueño.
- **Los seis pedidos de 2026-08-07** están hechos o ya existían (guardado
  unificado, árbol de habilidades, niebla animada, normal mapping,
  `ambient_light`, sombras proyectadas).
- La mayoría de las filas de `docs/63` §1 son **falsos positivos comprobados**
  o **HECHO**. Sólo quedan las cuatro de C4/C5.

---

## 3. El plan, por lotes

Un lote por commit, en este orden. El orden no es por dificultad: es porque
cada lote deja el suelo firme para el siguiente. **No se empieza un lote con
el anterior en rojo.**

### Lote 0 — Poner en el registro lo que ya está hecho *(bloqueante)*

Partir el árbol en commits por `AUD-NNN`: AUD-343…352 (las tres frentes
previas) y AUD-353…356 (esta auditoría). **Va primero** porque cuatro
conjuntos de trabajo mezclados hacen que cualquier fallo de los lotes
siguientes sea imposible de atribuir, y porque `docs/89` §18.7 ya lo señaló
como el riesgo de proceso número uno.

*Hecho cuando:* `git status` limpio y la suite verde en un árbol recién
clonado del commit.

### Lote 1 — Que los gates se comprueben a sí mismos (A2, A3, A6, C7, C8)

El lote más rentable, y el que esta auditoría demostró que hacía falta:
AUD-353 y AUD-356 fueron el mismo defecto en dos sitios.

- A2: `check_orphan_systems.py` sobre `ast.Call`, con los 12 candidatos
  triados uno a uno (11 ya están clasificados en GAP-035).
- A3: la anotación de `speedrun_mode.py:249`.
- A6: presupuesto de tiempo de suite, con umbral y aviso.
- C7: `tostring` → `tobytes`; se van los 20 avisos por ejecución.
- C8: un motivo escrito por cada uno de los 7 skips.

*Hecho cuando:* 0 avisos en la suite, `--ci` del detector verde, y una prueba
que falla si la suite pasa de N minutos.

### Lote 2 — Documentación contra el código (B1…B6, B8)

El patrón ya está probado: AUD-307 pasó `22_API_CONTRACTS.md` de 50 símbolos
inexistentes a 0 con un comprobador AST. Se reutiliza tal cual para
`09_HUD_SPEC`, `04_PLAYER_SPEC`, `05_ENEMY_SPEC`, `14_PROFESSOR_…` y
`23_DATA_SCHEMAS`.

*Hecho cuando:* el comprobador AST cubre los cinco documentos y sale verde, y
está en CI para que no vuelvan a divergir.

### Lote 3 — Huérfanos y cobertura (C4, C5, C3)

Conectar o retirar `AchievementDef`/`AchievementProgress`/`init_instance`;
colocar `BossSpawn` (queda **70 de 70** tipos ejercitados); y medir la IA
predictiva contra su heurística, que es lo que P6 lleva pidiendo — con una
medición, no con una opinión.

### Lote 4 — El aviso barato del contenido (D1)

`author` en los 12 mapas: 12 propiedades TMX, −12 avisos del calificador. Lo
demás de la sección D **no se toca**: es contenido, y el contenido es de los
estudiantes (D7 / GAP-018 / `docs/87` §27 fase 7).

### Lote 5 — `WorldSimulation` (E1) — la última característica

Alcance **cerrado** por adelantado, para que no se convierta en un lote sin
fondo. Lo que entra:

```
WorldSimulation
    ├── tiempo      (RelojDeMundo — ya existe, se reutiliza)
    ├── calendario  (contador de días: nuevo, 20 líneas)
    ├── estación    (Estacion — ya existe, se reutiliza)
    ├── clima       (WeatherSystem — ya existe; la simulación lo manda)
    └── astronomía  (altura solar y fase lunar: dos fórmulas cerradas)
            ↓
      EnvironmentState  ← YA ESCRITO (environment.py)
            ↓
    ┌───────┼────────────────┐
  RENDER   AUDIO         GAMEPLAY
  luz      ambiente      fricción con suelo mojado
  bloom    (clave ya      (el hilo que convierte el
  tinte     existe)        ambiente en jugabilidad)
```

Lo que **no** entra, y por qué: nubes volumétricas, fenómenos ópticos, halos,
eclipses y estrellas dibujadas son *contenido visual*, no arquitectura. La
tesis del diseño —«el ambiente deja de ser decoración»— se demuestra con **un**
hilo completo (lluvia → humedad → fricción → control) y no mejora por añadir
trece efectos más. Si después se quieren, entran como consumidores del estado,
sin tocar la simulación: que eso sea posible es exactamente lo que este lote
entrega.

*Hecho cuando:* `_aplicar_hora` no toca `_lighting` ni `_post_processing`
directamente sino que aplica un `EnvironmentState`; el resultado en Stage 0 es
**idéntico** al de hoy (regresión fijada por las pruebas existentes); y una
prueba demuestra que con tormenta el jugador frena más despacio que con cielo
despejado, sin que el jugador conozca el clima.

### Lote 6 — Las decisiones del dueño (A1, A7, B7, C1, D2)

No son trabajo: son cinco preguntas. Se juntan en un solo sitio para que se
respondan de una vez, y cada respuesta se escribe fechada en `KNOWN_GAPS.md`.
Están en §4.

### Lote 7 — Ampliación del trinquete (A4, A5)

Lo último a propósito: ampliar `mypy_scope.txt` y `mutation_check` sobre una
base ya estable rinde; hacerlo antes obliga a re-anotar todo lo que los lotes
1-5 tocan.

---

## 4. Las cinco preguntas que sólo puede responder el dueño

Ninguna se puede decidir desde el código. Cada una lleva la recomendación y su
coste.

| # | Pregunta | Recomendación |
|---|---|---|
| A1 | ¿Se fija la versión de las herramientas de lint, con actualización manual y revisable? | **Sí.** Coste: un commit al mes. A cambio, el CI deja de poder ponerse rojo solo |
| A7 | `computer-vision-course/` (8,2 MB): ¿`.gitignore`, o fuera del árbol? | **`.gitignore`** si va a seguir ahí; si es otro proyecto, sacarlo. Hoy un `git add -A` lo mete en la historia para siempre |
| B7 | `17_BOSS_SPEC.md`: 22 patrones que ningún jefe implementa. ¿Es una **especificación** (y falta trabajo) o un **catálogo de ideas** (y hay que renombrarlo)? | **Catálogo.** El jefe de referencia saca 100/100 con la rúbrica actual; una spec que nadie cumple envejece a mentira |
| C1 | Un sonido crítico (muerte de jefe, logro, cambio de fase) ¿puede quedar mudo por distancia? | **No.** Suelo de atenuación en la ruta crítica; el número lo pone quien mezcla |
| D2 | Cuatro mapas sin ningún checkpoint: ¿lo arregla el motor, o es nota del alumno? | **Nota del alumno.** El calificador ya lo penaliza, que es el mecanismo correcto |

---

## 5. Cómo se sabrá que está cerrado

```bash
# los doce gates, de verdad
ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/
mypy $(grep -v '^\s*#' mypy_scope.txt | grep -v '^\s*$')
pytest tests/ -q                       # sin avisos, y bajo el presupuesto de tiempo
python scripts/check_orphan_systems.py --ci
python scripts/check_tmx_coverage.py --ci      # 70/70 tipos
python scripts/grade_stage.py assets/maps/ --json | jq '[.[].errors] | flatten | length'   # 0
```

Y una condición que no es un comando: **`KNOWN_GAPS.md` sin ninguna entrada
abierta que no sea una decisión fechada del dueño.** Ése es el final de este
plan. No «cero gaps para siempre» — eso no existe — sino cero gaps *sin
dueño*.

---

## Documentos relacionados

- `CLAUDE.md` — invariantes; §3 lleva la anulación parcial del dueño
- `docs/69_PROMPT_AUDITORIA_MAESTRO.md` — el proceso que produce estos hallazgos
- `docs/70_INFORME_DE_AUDITORIA_VIVO.md` — iteración 15: de dónde salen A1, A2, C1
- `docs/87_REPORTE_DE_LO_QUE_FALTA.md` §27 — el plan del dueño, fases 1-6 hechas
- `docs/89_AUDITORIA_MULTIDISCIPLINAR.md` §6, §18, §19 — los hallazgos P y las tres rondas
- `KNOWN_GAPS.md` — GAP-018, GAP-034, GAP-035
