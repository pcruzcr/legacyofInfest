---
document_id: "LOI-INFORME-70"
title: "Informe de auditoría vivo"
tags: ["auditoria", "estado", "medicion"]
source: "docs/70_INFORME_DE_AUDITORIA_VIVO.md"
date_processed: "2026-08-02"
---

# Informe de auditoría vivo

Protocolo: `docs/69_PROMPT_AUDITORIA_MAESTRO.md`.
Aquí sólo van datos medidos. Lo que no se pudo medir se dice, no se estima.

---

## Iteración 1 — 2026-08-02 — Dominio D2 (consistencia doc ↔ código)

**Commit auditado:** `409a613` (rama `dev`, con 7 ficheros modificados sin
confirmar en el árbol de trabajo al empezar).

### Gates ejecutados

| Gate | Resultado | Nota |
|---|---|---|
| `ruff check …` | **NO EJECUTADO** | el entorno de auditoría no tenía acceso a PyPI; ruff no se pudo instalar |
| `mypy` (trinquete) | **NO EJECUTADO** | ídem |
| `pytest tests/` | **NO EJECUTADO** | ídem; además el intérprete disponible era 3.10 y el proyecto exige ≥ 3.11 |
| Validadores `scripts/*` | **NO EJECUTADO** | ídem |
| Parseo AST de `src/**/*.py` | ✅ **279 / 279 módulos** sin error de sintaxis | ejecutado con `ast.parse` (stdlib) |
| Grafo de importaciones internas | ✅ **0 imports** a módulos `src.*` inexistentes | ejecutado con `ast` (stdlib) |
| Parseo AST de `tests/**/test_*.py` | ✅ **121 ficheros**, 2.142 funciones `test_*`, 0 errores | ejecutado con `ast` (stdlib) |
| Guardián nuevo de rutas documentales | ✅ rojo → verde | ver abajo |

**Consecuencia honesta:** todo hallazgo de esta iteración es **estático**. Nada
de lo que sigue depende de ejecutar el juego, y nada de lo que sigue confirma
que la suite pase. La suite hay que correrla en la máquina con el `.venv`.

### Recuentos medidos

| Cosa | Medido | Cómo |
|---|---|---|
| Módulos en `src/` | 279 | `pathlib.glob` + `ast` |
| Ficheros `test_*.py` | 121 (122 tras esta iteración) | ídem |
| Funciones `test_*` definidas | 2.142 (2.147 tras esta iteración) | `ast`, sin contar expansión de `parametrize` |
| Documentos en `docs/*.md` | 93 | `pathlib.glob` |
| Rutas de repo citadas en la documentación | 296 distintas | regex + comprobación de existencia |
| GAPs abiertos en `KNOWN_GAPS.md` | 13 abiertos / 6 resueltos | recuento de encabezados |

### Hallazgos

| ID | Severidad | Archivo | Síntoma | Estado |
|---|---|---|---|---|
| AUD-168 | ALTA | `docs/22_API_CONTRACTS.md` §5.2, §5.3, §6.3 | contrato de API que documenta `AssetLoader.load_spritesheet → SpriteSheet`, un módulo `utils/spritesheet.py` y cuatro clases `*Transition` en `scene/transitions.py`. Los dos módulos se retiraron en AUD-098 y AUD-111; el método real es `load_sprite_sheet → list[pygame.Surface]` | **Corregido** |
| AUD-168 | ALTA | `docs/48_SCREEN_TRANSITIONS.md` §1, §5 | describe una arquitectura de dos capas y da `199 lines` para un fichero que no existe | **Corregido** |
| AUD-168 | MEDIA | `docs/22_API_CONTRACTS.md` §6.4 | firmas divergentes: doc `start_wipe(direction="left_to_right", duration=0.5)`, real `start_wipe(direction="left", duration=0.4, old_surface=None)`; doc `start_circle(expand=…)`, real `expanding=…` | **Corregido** |
| AUD-168 | MEDIA | `10_LIBRARIES_AND_DEPENDENCIES.md`, `20_ASSET_BIBLE.md` | los dos mandan ejecutar `validate_assets.py` desde `tools/`; el script vive en `scripts/` | **Corregido** |
| AUD-168 | MEDIA | `CONTRIBUTING.md` | «369 tests» (hay 2.142 funciones definidas); «Branch from `main`» (las ramas son `prod`/`pprod`/`dev`); `ruff check src/` y `mypy src/` en vez de los alcances reales del CI; sección *New Enemy* que ignora la decisión AUD-046 | **Corregido** |
| AUD-168 | MEDIA | el antiguo `24_TEST_PLAN` (§12.1, retirado con la fusión de docs) y sus árboles | declara fixtures `reference_sprite_32x32.png` y `sample_dataset_tiny.npz` que no existen; las entradas se generan en `conftest.py` | **Corregido** |
| AUD-168 | BAJA | `docs/17_BOSS_SPEC.md` | ruta `src/stages/boss_gavilan/` → real `src/stages/stage3_4_boss_gavilan/` | **Corregido** |
| AUD-168 | BAJA | `KNOWN_GAPS.md` GAP | `game_context.py` situado en `framework/core/` → vive en `src/engine/core/game_context.py` | **Corregido** |
| AUD-168 | BAJA | tickets del `80_TICKET_BACKLOG` y tabla del `50_IMPROVEMENT_ROADMAP` (retirados) | tickets y tabla de migración apuntando a los dos módulos retirados, y un ejemplo que carga `stage0.tmx` desde `assets/maps/` sin su directorio | **Corregido** |
| AUD-169 | MEDIA | `docs/00_MASTER_INDEX.md` §2 | la «lista autoritativa» no mencionaba 13 documentos; la fila 68 apuntaba a un documento de `niveles/` | **Corregido** |

### Corrección estructural

Se añadió `tests/test_rutas_de_los_documentos.py`, que hace imposible repetir
esta clase de defecto:

- toda ruta de repositorio citada en `docs/*.md`, `README*`, `CONTRIBUTING.md`,
  `KNOWN_GAPS.md` y `CLAUDE.md` tiene que existir;
- los ejemplos didácticos (`assets/maps/tu_stage.tmx`…) se declaran uno a uno
  en `MARCADORES_DE_POSICION`, y una prueba avisa si alguno se materializa o
  deja de citarse;
- los módulos retirados citados como historia se declaran en
  `MODULOS_RETIRADOS`, y una prueba avisa si vuelven a existir;
- todo `docs/*.md` tiene que aparecer en `00_MASTER_INDEX.md`.

**Evidencia rojo → verde** (ejecutado con un runner de stdlib equivalente,
porque `pytest` no era instalable en el entorno de auditoría):

```text
ANTES
FAIL  77_SYLLABUS_ALIGNMENT_AUDIT.md: ['tools/validate_assets.py']
FAIL  10_LIBRARIES_AND_DEPENDENCIES.md: ['tools/validate_assets.py']
FAIL  17_BOSS_SPEC.md: ['src/stages/boss_gavilan/boss_gavilan.py']
FAIL  20_ASSET_BIBLE.md: ['tools/validate_assets.py']
FAIL  22_API_CONTRACTS.md: ['src/engine/scene/transitions.py', 'src/engine/utils/spritesheet.py']
FAIL  24_TEST_PLAN.md: ['tests/fixtures/reference_sprite_32x32.png']
FAIL  80_TICKET_BACKLOG.md: ['src/engine/scene/transitions.py', 'src/engine/utils/spritesheet.py', 'src/stages/stage0/stage0.tmx']
FAIL  48_SCREEN_TRANSITIONS.md: ['src/engine/scene/transitions.py']
FAIL  50_IMPROVEMENT_ROADMAP.md: ['assets/maps/stage0.tmx', 'src/engine/scene/transitions.py']
FAIL  59_STAGE_0_REGENERADO.md: ['src/engine/scene/transitions.py']
FAIL  KNOWN_GAPS.md: ['src/framework/core/game_context.py']
FAIL  indice maestro incompleto: [11 documentos]
FALLOS: 12
```

```text
DESPUÉS
---
FALLOS: 0
```

### Verificación posterior a los cambios

| Comprobación | Resultado |
|---|---|
| Parseo AST de `src/**/*.py` | 279 / 279, 0 errores |
| Imports internos `src.*` | 0 rotos |
| Parseo AST de `tests/**/test_*.py` | 122 ficheros, 2.147 funciones, 0 errores |
| Guardián de rutas documentales | 0 fallos |
| `docs/*.md` fuera del índice maestro | 0 |
| Longitud de línea del fichero nuevo | máx. ≤ 120 (regla `line-length` de ruff) |
| Orden de imports del fichero nuevo | stdlib → terceros, conforme a la regla `I` |
| Otras pruebas que leen los documentos tocados | `test_toolchain_consistency.py` sólo comprueba que el CI contenga `ruff check`; `test_architecture_doc_matches_tree.py` lee `03_ARCHITECTURE.md`, no modificado. Ninguna regresión esperada — **no ejecutadas** |

### Lo que NO se verificó, y por qué

- **Que la suite pase.** No se pudo instalar `pytest` ni las dependencias.
- **Que `ruff` y `mypy` sigan verdes** tras añadir el fichero de prueba nuevo.
- **Que el juego arranque.** Requiere pygame.
- **Rutas `docs/…` citadas dentro de la documentación.** El guardián cubre
  `src/`, `scripts/`, `tools/`, `tests/`, `assets/`, `locale/`, `data/`,
  `colab/`, `exams/` y `web/`, pero no los enlaces entre documentos. Es el
  siguiente incremento natural de esta prueba.

### Pendiente de decisión humana

- `docs/00_MASTER_INDEX.md` tiene **números de documento duplicados** (28, 29,
  30-34, 52, 67 los usan dos ficheros distintos). No se tocó: renumerar rompe
  todas las referencias cruzadas del curso. Decisión de quien mantiene el
  temario.
- `CONTRIBUTING.md` está ahora mezclado en inglés y español. Coherente con la
  política de «bilingüe donde hay lector», pero conviene decidir si este
  documento se pasa entero a español.

### Nota de numeración

Los hallazgos de esta iteración se registraron primero como AUD-164/165 y se
renumeraron a **AUD-168/169**: mientras se auditaba, la rama `dev` recibió
cuatro commits (`ebfdacc`…`dbb78cc`) que ya usaban 164-167.

---

## Iteración 2 — 2026-08-02 — Dominio D4 (corrección del código)

**Commit auditado:** `dbb78cc`.
**Alcance:** los 446 ficheros Python del árbol — `src/` (279), `tests/` (129),
`scripts/` (24), `tools/` (13) y `main.py`.

### Qué se ejecutó

Sigue sin haber PyPI ni intérprete ≥ 3.11 en el entorno de auditoría, así que
`pytest`, `ruff` y `mypy` **siguen sin ejecutarse** (GAP-020). Lo que sí se
hizo, con la biblioteca estándar:

| Comprobación | Herramienta | Resultado |
|---|---|---|
| Sintaxis de los 446 ficheros | `ast.parse` | **0 errores** |
| Importaciones internas `src.*` a módulos inexistentes | `ast` | **0** |
| Regla L1 (núcleo del motor ↛ framework) | `ast` | **0 infracciones** |
| Regla L2 (`framework/processing` ↛ engine) | `ast` | **0 infracciones** |
| Regla L3 (escenario ↛ escenario) | `ast` | **0 infracciones** |
| `engine/` → `stages/` | `ast` | **0 infracciones** |
| `framework/` → `stages/` | `ast` | **1 infracción** → AUD-172 |
| Ciclos de importación (nivel de módulo, sin `TYPE_CHECKING` ni diferidos) | Tarjan sobre el grafo | **0 ciclos** |
| `except:` desnudo | `ast` | **0** en todo el árbol |
| `except …: pass` silencioso | `ast` | 32; 5 en motor/framework, revisados uno a uno |
| Funciones redefinidas en el mismo ámbito (F811) | `ast`, descontando `@property`/`@x.setter` | **1 real** → AUD-170 |
| Defaults mutables (B006) | `ast` | **0** |
| `is` contra literal (F632), `== None`, `assert` sobre tupla, claves duplicadas | `ast` | **0** |
| Imports muertos (F401) | `ast` | 2, ambos sondas de disponibilidad con `# noqa: F401` — correctos |

**Lo que esto dice del código:** la base está sana. Cero errores de sintaxis,
cero ciclos de importación reales, cero `except:` desnudos, cero defaults
mutables y las tres reglas de capas documentadas se cumplen sin excepciones.
Los ciclos aparentes —cuatro, uno de 25 módulos— están **todos** rotos con
importaciones diferidas o bajo `TYPE_CHECKING`, que es la forma correcta.

### Hallazgos

| ID | Severidad | Archivo | Síntoma | Estado |
|---|---|---|---|---|
| AUD-170 | BLOQUEANTE | `scripts/mutation_check.py:177` y `:242` | `_pruebas_pasan` definida **dos veces** con firmas distintas (3 y 2 parámetros). La segunda gana; la primera era código inalcanzable. `scripts/` está en el alcance de `ruff`, así que **F811 pone el lint del CI en rojo** | **Corregido** |
| AUD-171 | ALTA | `src/framework/stage/speedrun_mode.py` (`SpeedrunTimer.load`, `GhostData.load`) | dos `except (FileNotFoundError, JSONDecodeError): pass` — la forma exacta que AUD-100 condenó — y, peor, un JSON **válido con otra forma** no estaba cubierto | **Corregido** |
| AUD-172 | MEDIA | `src/framework/entities/entity_factory.py:59` | el framework importa `stages.boss_venado`; ninguna regla de capas cubría el sentido `framework → stages`, así que la dependencia era indistinguible de un descuido | **Corregido** (declarada + regla L4 nueva) |

### AUD-171 en detalle — por qué era ALTA y no MEDIA

El `except` sólo nombraba `JSONDecodeError`, o sea «esto no es JSON». No cubría
«esto es JSON perfectamente válido, con otra forma», que es lo que produce una
versión anterior del fichero, un disco que se llenó a mitad de escritura o
alguien que lo editó a mano. Comportamiento medido **antes** del arreglo:

```text
SpeedrunTimer.load
  basura   -> sin excepcion, silencio total
  lista    -> AttributeError: 'list' object has no attribute 'get'   <-- SIN CAPTURAR
  numero   -> AttributeError: 'int' object has no attribute 'get'    <-- SIN CAPTURAR
  cadena   -> AttributeError: 'str' object has no attribute 'get'    <-- SIN CAPTURAR
  null     -> AttributeError: 'NoneType' object has no attribute 'get'  <-- SIN CAPTURAR

GhostData.load
  dict     -> frame_count={'a': 1}  get_frame(0) lanza KeyError: 0   <-- SIN CAPTURAR
  cadena   -> frame_count=6         get_frame(0)='c'
  numero   -> frame_count=7         get_frame(0) lanza TypeError    <-- SIN CAPTURAR
```

La línea que más importa es la del medio: con una cadena dentro del fichero, el
fantasma **no fallaba, mentía** — `frame_count` devolvía la longitud de la
cadena y `get_frame(0)` una letra.

Después del arreglo, los mismos catorce casos:

```text
SpeedrunTimer.load — basura, lista, numero, cadena, null, tipos-malos
  todos: sin excepcion, valores por defecto, aviso WARNING nombrando la ruta
  fichero que no existe: silencio (es lo normal la primera partida)
  fichero correcto: carga 12.5 y su split

GhostData.load — basura, dict, cadena, numero, lista-no-dicts
  todos: fantasma vacio, get_frame(0) is None, aviso WARNING
  grabacion correcta: 2 fotogramas, get_frame(1) correcto
```

Prueba nueva: `tests/test_speedrun_datos_hostiles.py` (12 casos).

### Correcciones estructurales

1. **Regla L4** en `tests/test_layering.py`: ni `engine/` ni `framework/`
   importan de `stages/`. La única dependencia real —el jefe de referencia— se
   declara en `EXCEPCION_L4` y en `03_ARCHITECTURE.md` §3.1. Dos pruebas más
   impiden que la exención se pudra: una falla si el módulo nombrado deja de
   existir, otra si ya nadie lo importa.
   Verificado en rojo vaciando `EXCEPCION_L4`:
   `src/framework/entities/entity_factory.py -> src.stages.boss_venado.boss_venado`.
2. **`docs/03_ARCHITECTURE.md` §3.1** pasa de tres reglas a cuatro. La prueba
   `test_la_documentacion_describe_estas_mismas_reglas` ya exige que la tabla y
   el código no se separen, y ahora incluye L4.

### Verificación posterior

| Comprobación | Resultado |
|---|---|
| Las 7 pruebas de `test_layering.py` (L1-L4 + excepciones + doc) | **7 PASA** — ejecutadas con un runner de stdlib |
| L4 con `EXCEPCION_L4` vacía | **ROJO**, nombra la infracción correcta |
| `speedrun_mode` nuevo, 14 entradas hostiles | **todas OK**, casos buenos siguen cargando |
| `mutation_check.py`: duplicados de nivel de módulo | **0** |
| AST de los 4 ficheros tocados | ok; ninguna línea > 120 columnas |
| Guardián de rutas documentales tras tocar `03_ARCHITECTURE.md` | 0 fallos |

### Lo que sigue sin verificarse

Lo mismo que en la iteración 1, más:

- **Que `ruff` esté verde ahora.** AUD-170 era una infracción F811 real; puede
  haber otras que un analizador propio no reproduce (ruff implementa cientos de
  reglas y esta auditoría comprobó una docena).
- **Que las 12 pruebas nuevas de speedrun pasen bajo `pytest`.** Su lógica se
  verificó con un doble de `orjson` sobre la implementación real, no con
  `pytest`.
- **`src/stages/`**: 279 módulos analizados incluyen los escenarios, pero por
  la invariante 1 de `CLAUDE.md` los hallazgos ahí no se corrigen. El único de
  esa carpeta fue una comparación de una variable consigo misma; se deja para
  la corrección con rúbrica.

---

## Iteración 3 — 2026-08-02 — Dominio D1 (dependencias y arranque)

**Alcance:** las 15 dependencias base, los 5 extras y sus tres manifiestos
(`pyproject.toml`, `requirements.txt`, `requirements.lock`), contrastados
contra los imports reales de los 446 ficheros y contra la matriz del CI.

### Qué se ejecutó

| Comprobación | Resultado |
|---|---|
| Imports de terceros en el árbol ↔ dependencias declaradas | **0 sin declarar**. Los 7 que aparecían son módulos del propio repo importados por las pruebas, más `tomllib` (stdlib en 3.11+) y su respaldo guardado `tomli` |
| Dependencias declaradas que nadie importa | 5, todas correctas: `ruff`, `nuitka`, `pytest-cov`, `pytest-benchmark` y `pytest-mock` se usan por CLI o por *fixture*, no por `import` |
| Extras opcionales con guarda | `numba`, `moderngl`, `lupa`, `pydub`, `sklearn`: **todos** con `try/except ImportError` y camino de reserva |
| APIs retiradas por numpy 2.0 (`np.float_`, `np.NaN`, `np.in1d`, `np.trapz`, `np.product`, `np.row_stack`…) | **0 apariciones** |
| Módulos retirados en Python 3.12/3.13 (`distutils`, `imp`, `cgi`, `telnetlib`, `pkg_resources`…) | **0** |
| APIs deprecadas (`datetime.utcnow`, `locale.getdefaultlocale`, `ast.Str/Num`, `typing.ByteString`) | **0** |
| `filterwarnings` de pytest | 2 supresiones, ambas justificadas por escrito. Los avisos **no** son errores, así que una deprecación no tumba la suite |
| Matriz del CI ↔ `requires-python` | **contradicción** → AUD-173 |

### Hallazgo

| ID | Severidad | Archivo | Síntoma | Estado |
|---|---|---|---|---|
| AUD-173 | BLOQUEANTE | `pyproject.toml`, `requirements.txt`, `requirements.lock` | `numpy>=1.26,<2` con una matriz de CI que incluye Python 3.13. La última numpy 1.x es la 1.26.4 y sus ruedas llegan a 3.12; en 3.13 no existe ninguna, así que `pip install -e ".[dev]"` intenta compilar numpy desde el código fuente y falla. **Un tercio de la matriz no podía ni instalar el proyecto** | **Corregido** |

**De dónde venía el tope.** De `numba`, que es un extra **opcional**: numba
0.60 exige `numpy<2.1`. Un acelerador que el juego no necesita estaba fijando
el suelo de todo el proyecto. numba 0.62 (septiembre de 2025) soporta numpy 2.3.

**Qué se cambió:**

| | Antes | Ahora | Por qué |
|---|---|---|---|
| `numpy` (base) | `>=1.26,<2` | `>=1.26` | el tope hacía imposible 3.13; el árbol no usa ninguna API que numpy 2 retirara |
| `matplotlib` (base) | `>=3.8` | `>=3.10` | 3.8 es anterior a numpy 2 y no resuelve con él; 3.10 es la línea que ya fijaba el lock |
| `numba` (extra `accel`) | `>=0.60` | `>=0.62` | 0.60 arrastraba el `numpy<2.1` que originó todo |
| `requirements.lock` | cabecera afirmando «resolvable on Python 3.10-3.13» | la afirmación corregida + instrucción de regenerar | era falsa; los pines **no se tocaron a mano**, porque hand-editar este fichero es lo que produjo el lock imposible de AUD-008 → GAP-022 |

### Corrección estructural

`tests/test_dependencias_coherentes.py`, sin red y sin instalar nada:

1. La matriz del CI y `requires-python` tienen que decir lo mismo, en los dos
   sentidos: nada por debajo del suelo, y el suelo se ejecuta de verdad.
2. **Ningún tope superior en las dependencias base sin razón escrita** en
   `TOPES_JUSTIFICADOS`. Es la regla que faltaba: `numpy<2` llevaba meses sin
   dueño, y un tope sin porqué nadie se atreve a quitarlo.
3. `requirements.txt` y `pyproject.toml` comparten **rangos**, no sólo
   nombres. `scripts/check_dependency_sync.py` sólo compara nombres, así que
   una divergencia de versiones pasaba el CI en verde.

**Rojo → verde:** con `numpy>=1.26,<2` restaurado, la regla 2 falla nombrando
exactamente el especificador culpable; con el árbol actual, las 7 pruebas pasan.

### Lo que sigue sin poder verificarse aquí

**No se instaló nada, y no se pudo.** El entorno de auditoría no tiene acceso a
PyPI (`403 Forbidden` en el proxy) y su intérprete es 3.10. La verificación de
esta iteración es documental y estática: manifiestos, imports y matriz.

Lo que hay que ejecutar en la máquina con el `.venv`, en este orden:

```powershell
# 1. Reinstalar con los rangos corregidos
pip install -e ".[dev]" --upgrade

# 2. Confirmar que numpy ya no está capado
python -c "import numpy; print(numpy.__version__)"

# 3. Los gates completos
pytest tests/ --tb=short
ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/
mypy (Get-Content mypy_scope.txt | Where-Object { $_ -notmatch '^\s*(#|$)' })
python scripts/check_dependency_sync.py

# 4. Regenerar el lock (GAP-022)
pip install pip-tools
pip-compile --output-file=requirements.lock pyproject.toml

# 5. Extras opcionales, sólo si se quieren
pip install -e ".[accel]"       # numba + ModernGL
pip install -e ".[scripting]"   # lupa
pip install -e ".[audiotools]"  # pydub
```

El paso 1 es el que de verdad prueba AUD-173: si `numpy` sube de 1.26.4, el
tope estaba de más y el 3.13 del CI vuelve a ser instalable.

### Siguiente iteración

D3 — honestidad de las pruebas: ejecutar `scripts/mutation_check.py` (ahora que
ya no tiene la función duplicada) y buscar pruebas que no fallen ante una
mutación del código que dicen cubrir.

---

## Iteración 4 — 2026-08-02 — Dominio D1 (gates ejecutados de verdad)

**Commit auditado:** `dbb78cc`, con el árbol de trabajo de las iteraciones 1-3.
**Lo que cambia respecto a las tres anteriores:** esta se hizo en la máquina del
repositorio, con su `.venv` y acceso a PyPI. **Los doce gates se ejecutaron.**
Eso cierra GAP-020 y, de paso, demuestra el argumento que las tres iteraciones
anteriores venían anotando: los tres defectos de abajo son invisibles al
análisis estático, y sólo aparecen cuando los comandos corren.

### Gates ejecutados

| Gate | Resultado |
|---|---|
| `pip install -e ".[dev]"` | ✅ instala |
| `ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/` | ✅ `All checks passed!` |
| `mypy` sobre `mypy_scope.txt` | ✅ `Success: no issues found in 18 source files` |
| `pytest tests/` | ✅ **2.910 pasan**, 1 omitida, 0 fallos (2.913 recogidas al cerrar la iteración) |
| `scripts/check_dependency_sync.py` | ✅ `OK 15 dependencies agree` |
| `scripts/check_translations.py --ci` | ✅ `Catálogos en orden` |
| `scripts/check_tmx_coverage.py --ci` | ✅ cobertura de propiedades y de Light al 100 % |
| `scripts/generate_tmx_reference.py --check` | ✅ `docs/STAGE_CREATION.md: al día` |
| `scripts/validate_assets.py` | ✅ 0 errores, 0 avisos |
| `scripts/validate_tmx.py --ci` | ✅ 17/17 |
| `scripts/grade_stage.py assets/maps/ --json` | ✅ 17 calificados, media **78,7 %** |
| `scripts/grade_boss.py … boss_venado.py --json` | ✅ **100,0 %** |

El intérprete de esta máquina es **3.14.6**, por encima de la matriz declarada
(3.11/3.12/3.13). Que la suite pase en 3.14 es información extra, no sustituye
a la matriz: lo que el CI ejecuta sigue sin verificarse aquí.

### Hallazgos

| ID | Severidad | Archivo | Síntoma | Estado |
|---|---|---|---|---|
| AUD-174 | BLOQUEANTE | `pyproject.toml`, `.github/workflows/ci.yml:69` | el paso «Type-check the ratcheted scope» ejecuta `mypy`, pero `mypy` **no está en ningún extra** y el workflow instala exactamente `pip install -e ".[dev]"`. El paso termina en `command not found` (código 127) | **Corregido** |
| AUD-175 | ALTA | `tests/test_audit_regressions.py:497` | `test_build_backend_is_importable` importaba `setuptools` en el intérprete de las pruebas. Es una dependencia **de construcción**, que PEP 517 aísla, y desde Python 3.12 `ensurepip` ya no la incluye: la prueba fallaba sobre un árbol correcto | **Corregido** |
| AUD-176 | ALTA | `pyproject.toml:69`, `requirements.txt:35` | `Pillow>=10.0` permitía instalar 12.2.0, que acumula **diez vulnerabilidades publicadas** (PYSEC-2026-2253..2257, 3451..3454, 3493..3496), todas corregidas en 12.3.0 | **Corregido** |
| AUD-177 | ALTA | 9 ficheros de `scripts/` y `tools/` | imprimen `→`, `↔`, `←` y emoji. La consola de Windows usa **cp1252**, que no los tiene: el proceso muere con `UnicodeEncodeError` **a media faena** | **Corregido** |
| AUD-178 | MEDIA | `tools/generate_demo_stage0.py:327` | el cartel del nivel de demostración decía «⟨U+FFFD⟩Saltos verticales!»: un `¡` perdido al guardar el fichero con otra codificación | **Corregido** |
| AUD-179 | BAJA | `mypy_scope.txt:23` | el comentario del trinquete nombraba, como red de seguridad que impide que la lista encoja, un fichero de prueba **que no existe**. La prueba sí existe —`tests/test_puertas_de_calidad.py`—, con otro nombre. Lo cazó el guardián de la iteración 1 al ampliarlo a este fichero | **Corregido** |
| AUD-180 | MEDIA | `scripts/mutation_check.py:297,309` | tras la pasada de mutación, `git status` marcaba los **tres módulos críticos** como modificados y `git diff` salía vacío: `write_text` sin `newline` traduce cada `\n` al separador del sistema, así que restaurar el original los reescribía en CRLF | **Corregido** |
| — | BAJA | `README.md:14`, `README.en.md:19` | «2.713 pruebas» con 2.872 reales (6 % de desvío, tolerancia 5 %). Es la invariante 6 funcionando: lo detectó `test_documentacion_bilingue.py`, no una revisión | **Corregido** |

### AUD-174 en detalle — por qué es BLOQUEANTE y no MEDIA

No es «falta una dependencia». Es que **el gate no se ejecutaba desde que se
creó**. AUD-124 puso mypy en marcha en enero, escribió `mypy_scope.txt` con su
razonamiento del trinquete, añadió `tests/test_puertas_de_calidad.py` para que
la lista no encogiera y documentó el comando en `CLAUDE.md` §2. Todo eso es
cierto salvo la parte que importa: el paso moría antes de comprobar una línea.

Un gate que falla ruidosamente se arregla. Éste **aparecía** en el workflow, en
`CLAUDE.md` y en `CONTRIBUTING.md`, así que nadie volvió a mirarlo. Es el mismo
modo de fallo que AUD-010 —un CI que nunca se había ejecutado— repetido dentro
de un CI que sí se ejecuta.

Al instalarlo y correrlo por fin: `Success: no issues found in 18 source files`.
El trinquete estaba limpio; lo que faltaba era el comprobador.

### AUD-177 en detalle — el reverso exacto de AUD-166

`scripts/mutation_check.py --ci`, ejecutado en esta máquina:

```text
Comprobación de mutación - ¿se enterarían las pruebas?

  src/engine/audio/mixer_buses.py  (tests/test_buses_de_audio.py)
Traceback (most recent call last):
  File "scripts/mutation_check.py", line 310, in medir
    print(f"    muere {descripcion}", flush=True)
UnicodeEncodeError: 'charmap' codec can't encode character '→'
```

Murió en el primer módulo. AUD-166 arregló esta misma herramienta porque
devolvía rutas con separador de Windows y **se rompía en Linux**; ahora resulta
que también se rompía en Windows, por la codificación. Código que sólo se
ejecuta en un sistema acumula supuestos sobre él, en las dos direcciones.

CI corre en Ubuntu, donde la salida es UTF-8, así que allí nunca falló. Pero
`CLAUDE.md` §2 dice que el toolchain vive en el `.venv` de Windows: la
herramienta se rompía justo en la máquina para la que está escrita.

El barrido con `ast` sobre los literales de cadena de `scripts/` y `tools/` dio
**9 ficheros** afectados, no uno: `bench_gpu_postproc`, `difficulty_curve`,
`mutation_check`, `obsidianize`, `validate_tmx`, `generate_demo_stage0`,
`generate_stage4_1`, `generate_stage_mecanicas` y `pixel_asset_generator`.

### Correcciones estructurales

1. **`tests/test_toolchain_consistency.py`** — clase `TestCIToolsAreInstallable`:
   toda herramienta que el workflow invoca por línea de comandos tiene que estar
   declarada en `pyproject.toml` o instalarse en el propio workflow. La regla se
   escribió como lista **negra** de comandos de shell, no blanca de herramientas,
   para que una herramienta nueva se detecte sola.
2. **`tests/test_dependencias_coherentes.py`** — `SUELOS_POR_SEGURIDAD`, gemelo
   de `TOPES_JUSTIFICADOS`: un suelo de versión con su razón escrita. Hacía
   falta porque `pip-audit` corre con `continue-on-error` (AUD-125) y sólo mira
   lo instalado hoy; nada impedía que el manifiesto siguiera permitiendo la
   versión vulnerable mañana.
3. **`tests/test_salida_de_consola.py`** (nuevo) — todo script con un literal
   fuera de cp1252 tiene que fijar su salida a UTF-8, y ningún fichero de texto
   del repositorio puede guardar U+FFFD.
4. **`scripts/mutation_check.py`** — la escritura de módulos pasa por una
   función nombrada, `escribir_fuente`, que no traduce finales de línea.
   `tests/test_mutacion.py` la prueba sin lanzar subprocesos, respetando la
   decisión que ese fichero ya documenta, y comprueba además que los tres
   módulos objetivo siguen guardados en LF.

### AUD-180 — cómo apareció

No lo buscaba nadie: salió de mirar `git status` después de ejecutar el gate de
mutación. Tres ficheros que esta auditoría no había tocado figuraban como
modificados, y `git diff` no mostraba **ni una línea**. La herramienta que mide
la calidad de las pruebas estaba ensuciando el árbol de trabajo cada vez que se
ejecutaba, sobre los tres módulos que más se miran.

La prueba que lo fija sólo puede ponerse roja en Windows —es donde `os.linesep`
es CRLF— y así está escrito en su docstring, para que nadie lea un verde en
Linux como una comprobación que no es.

### Verificación

| Comprobación | Rojo antes | Verde después |
|---|---|---|
| `TestCIToolsAreInstallable` (2 pruebas) | ✅ `assert 'mypy' in {…}` falla | ✅ 11 pasan |
| `test_build_backend_…` con el string de AUD-007 reintroducido | ✅ nombra el backend falso | ✅ 3 pasan |
| `TestLosSuelosDeSeguridad` con `Pillow>=10.0` | ✅ `assert (10, 0) >= (12, 3, 0)` | ✅ 38 pasan |
| `test_salida_de_consola.py` | ✅ 10 fallos (9 scripts + U+FFFD) | ✅ 38 pasan |
| `pip-audit` | 20 avisos en 1 paquete | **0 en 92 paquetes** |
| `ruff` tras tocar 12 ficheros | — | ✅ `All checks passed!` |

### Limpieza del árbol

`git ls-files` filtrado por extensiones de artefacto: **cero** ficheros basura
rastreados. Lo que sobraba era caché local, toda regenerable y ya ignorada:
`.mypy_cache` (75 MB), `tests/benchmarks/.mypy_cache` (41 MB), `tests/output`
(6,2 MB), `.pytest_cache`, `.ruff_cache`, y **859 `.pyc` en 56 directorios**
`__pycache__` —411 de ellos de un intérprete 3.10 que ya no es el del `.venv`—.
Borrado: ~123 MB. `.gitignore` ya cubría todo; no hizo falta tocarlo.

**No se borró, y necesita decisión humana:**

- `src/stages/stage1_2_la_soda/*.bak` (3) y
  `assets/maps/stage1_2_la_soda/stage1_2_la_soda.tmx.bak`. Son copias de
  seguridad de una entrega de estudiante, no están en git y borrarlas es
  irreversible. La invariante 1 de `CLAUDE.md` protege esa carpeta.
- `legacyOfINfest/.smart-env/` en la raíz: directorio huérfano de un plugin de
  Obsidian, con el nombre del repositorio mal escrito.

### Lo que sigue sin verificarse

- **La matriz real del CI.** Aquí sólo se ejecutó 3.14; el CI corre 3.11/3.12/
  3.13 y ninguna de las tres se probó en esta máquina.
- **`requirements.lock`** sigue sin regenerar, y ahora con dos pines caducos en
  vez de uno (`numpy==1.26.4` y `Pillow==12.2.0`). Ver GAP-022: no se regeneró
  desde 3.14 a propósito, porque `pip-compile` ata el lock al intérprete que lo
  genera y cambiaría un lock imposible en 3.13 por otro imposible en 3.11.
- **Que el juego arranque.** No se lanzó `python main.py`; esta iteración fue de
  gates, no de comportamiento en pantalla.

### Evidencia de AUD-177: la misma orden, después

`scripts/mutation_check.py --ci`, forzando `PYTHONIOENCODING=cp1252` para
reproducir la consola de Windows. Ya no muere: **termina y da su veredicto**,
en 279 s.

```text
========================================================
  [BAJO]  56.0 %  src/engine/audio/mixer_buses.py
  [OK ]  72.0 %  src/engine/audio/music_clock.py
  [BAJO]  56.0 %  src/framework/stage/bloques.py
```

### Lo primero que dijo el gate al poder ejecutarse: D3

Con la herramienta arreglada, el dominio D3 —honestidad de las pruebas— tiene
por fin una medición en vez de una intención: **22 mutantes vivos** en dos de
los tres módulos críticos. Cada uno es un cambio en el código que la suite no
detecta. Los dos peores patrones son reconocibles:

- **Constantes que nadie comprueba.** `0.5 → 0`, `0.35 → 0`, `0.15 → 0` en
  `mixer_buses.py` (líneas 71-77): se puede poner a cero el volumen de tres
  buses de audio y ninguna prueba se entera.
- **Fronteras `<` frente a `<=`.** Ocho mutantes de comparación entre los dos
  módulos. Es el error clásico de un píxel o un fotograma de más, y es
  exactamente lo que una prueba de límites debería fijar.

No se corrigió aquí: son 22 pruebas por escribir, es el dominio siguiente y el
prompt maestro (§5) prohíbe abrir dos frentes en una iteración. Queda como
**GAP-023** con la lista completa.

### Siguiente iteración

D3, con la lista de GAP-023 delante: escribir las pruebas que maten esos 22
mutantes, empezando por las tres constantes de volumen, que son las que dejan
pasar un fallo audible.

---

## Iteración 5 — 2026-08-02 — Dominio D3 (honestidad de las pruebas)

**Alcance:** los 22 mutantes vivos de GAP-023, en `src/engine/audio/
mixer_buses.py` y `src/framework/stage/bloques.py`.
**Hallazgo:** AUD-181.

### Resultado medido

| Módulo | Antes | Después |
|---|---|---|
| `src/engine/audio/mixer_buses.py` | `[BAJO]` 56,0 % (14/25) | **`[OK ]` 88,0 %** (22/25) |
| `src/framework/stage/bloques.py` | `[BAJO]` 56,0 % (14/25) | **`[OK ]` 96,0 %** (24/25) |
| `src/engine/audio/music_clock.py` | `[OK ]` 72,0 % | `[OK ]` 72,0 % (sin tocar) |

26 pruebas nuevas. 18 mutantes muertos; los **4 restantes son equivalentes**, y
eso se demostró en vez de suponerse (más abajo).

### Lo que de verdad estaba roto: dos pruebas que pasaban por la razón equivocada

Las constantes sin comprobar eran lo llamativo, pero lo grave era otra cosa.
`test_no_se_empuja_a_traves_de_una_pared` y
`test_un_bloque_no_empuja_a_otro_a_traves` dicen en su nombre que un bloque
empujado no atraviesa un sólido. Ninguna de las dos lo comprobaba.

En ambas, el jugador se queda quieto en su sitio mientras el bloque se aleja.
`_toca_de_lado` exige contacto lateral, así que en cuanto el bloque avanza unos
píxeles el contacto se pierde y **el bloque se para solo**, mucho antes de
llegar a la pared. La aserción final —«el bloque no está dentro de la
pared»— se cumplía porque el bloque nunca llegó a acercarse.

Consecuencia: las tres ramas de `_chocaria` que impiden atravesar una pared,
otro empujable o un destructible entero **no se ejecutaban en ninguna prueba**.
Se podían invertir las tres (`return True` → `return False`) y la suite seguía
verde. Un bloque atravesando la pared del nivel es un soft lock: se pierde el
objeto que hacía falta para abrir el paso.

El arreglo en la prueba es una línea —`jugador.right = bloque.rect.left` dentro
del bucle, que es lo que hace la resolución de colisión real cuando se camina
contra un sólido— y con ella las tres ramas se ejecutan y las tres mutaciones
mueren.

### Lo demás que se destapó

| Mutación | Qué significaba que sobreviviera |
|---|---|
| `mixer_buses.py:71,75,77` — `0.5 → 0`, `0.35 → 0`, `0.15 → 0` | se podía dejar mudo el bus de ambiente y anular el *ducking*; las pruebas comprobaban `0.0 <= x <= 1.0`, que también se cumple con el altavoz apagado |
| `mixer_buses.py:91` — `_duck_pedido = False → True` | la música arrancaba agachándose sola sin que nadie hablara, y sin nadie que la soltara |
| `mixer_buses.py:168` — `<= 0` → `< 0` | el contador de *duck* se quedaba clavado en 0,0 y la música no volvía nunca |
| `mixer_buses.py:178` — `1.0 - DUCK_NIVEL` → `+` | el *duck* bajaba al doble de velocidad que la declarada |
| `bloques.py:146` — `or` → `and` | un `dt` negativo arrastraba el bloque en sentido contrario |
| `bloques.py:171` — tres mutantes sobre `+ 2` y `>=` | la tolerancia de solape vertical: rozar el canto de un bloque pasaba a contar como empujarlo |
| `bloques.py:210` — `int(_vy * dt)` → `/` | 700 píxeles de caída **en un fotograma**; como `caer` avanza de píxel en píxel hasta chocar, ni la prueba de «no atraviesa el suelo» se enteraba |
| `bloques.py:106` — `return False` → `True` | golpear un bloque ya roto volvía a declararlo roto; `sistema.golpear` devuelve 0 en ambos casos, así que la prueba que existía no los distinguía |

### Los 4 mutantes equivalentes, demostrados

Un mutante equivalente cambia el texto del código sin cambiar lo que hace.
Escribirle una prueba obliga a afirmar algo falso, así que aquí se documentan.
Cada uno se comprobó **ejecutando el original y el mutante en paralelo** sobre
secuencias aleatorias de llamadas y comparando la salida paso a paso:

| Mutante | Por qué no cambia nada | Evidencia |
|---|---|---|
| `mixer_buses.py:144` `>` → `>=` | la rama de más sólo corre con `segundos == 0`, y hace `max(_duck_restante, 0.0)`; sólo importaría con el contador negativo, y un contador negativo ya está inerte porque el descuento corre bajo `if _duck_restante > 0.0` | **0 / 20.000** secuencias con salida pública distinta |
| `mixer_buses.py:164` `<=` → `<` | con `dt == 0` el cuerpo se ejecuta pero cada paso es nulo: no descuenta nada y el paso del *duck* vale `… * 0 / duracion` = 0 | **0 / 4.000**, comparando incluso el estado interno |
| `mixer_buses.py:177` `<` → `<=` | las dos formas sólo difieren cuando los valores son iguales, y tres líneas antes hay un `if self._duck == objetivo: return` que ya se llevó ese caso | la rama instrumentada: la igualdad se da **0 veces** |
| `bloques.py:204` `<=` → `<` | con `dt == 0` la velocidad crece `GRAVEDAD_BLOQUE * 0` y los píxeles a recorrer son `int(_vy * 0)` = 0, que sale por el `continue` | **0 / 5.000** secuencias sembradas de ceros, comparando posición, velocidad y posición en coma flotante |

El razonamiento vive también en los docstrings de `TestLoQueLaMutacionDestapo`
de los dos ficheros de prueba, que es donde mirará quien vuelva a ver el
porcentaje por debajo de 100 y quiera perseguirlo.

### Una trampa que conviene no repetir

La primera versión de `test_bajar_tarda_lo_que_dice_el_ataque` comparaba el
tiempo medido contra `DUCK_ATAQUE`. El mutante que pone esa constante a 0
**sobrevivía**: la prueba lee la misma constante que el mutante cambia, así
que el listón se mueve con el defecto. Una prueba que se calibra sola no
comprueba nada. Ahora la ventana es absoluta —entre 0,05 s y 0,30 s, que es
donde el *duck* no se oye como un corte— y la coherencia con la constante se
comprueba aparte.

Lo mismo pasó con la frontera de `mixer_buses.py:168`: la primera versión
avanzaba 50 pasos de 0,01 s, y 50 sumas en coma flotante no aterrizan en el
cero exacto que es justo donde `<= 0` y `< 0` difieren. Con un solo
`update(0.5)` sobre los 0,5 s pedidos, el mutante muere.

### Gates tras los cambios

| Gate | Resultado |
|---|---|
| `ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/` | ✅ `All checks passed!` |
| `mypy` (trinquete de `mypy_scope.txt`) | ✅ `Success: no issues found in 18 source files` |
| `python scripts/mutation_check.py --ci` | ✅ los tres módulos en `[OK ]` |

### Siguiente iteración

D5 — estados y sensación del jugador: la máquina de estados de
`player_states/`, *coyote time*, *input buffering*, cancelación e i-frames. Es
el primer dominio de comportamiento, y `mutation_check.py` ya tiene sitio para
un cuarto objetivo si conviene medirlo igual.

---

## Iteración 6 — 2026-08-02 — Dominios D5–D9 (juego y material del estudiante)

**Alcance:** mecánicas, gameplay, *funfactor*, level design y el inventario
completo de lo que un estudiante puede declarar en un TMX.
**Hallazgo:** AUD-182.
**Informe completo:** la revisión de juego se fusionó en este informe; aquí
va el resumen y la evidencia de la corrección.

### Inventario medido

| Cosa | Cuántas | Fuente |
|---|---|---|
| Estados del jugador | 25 concretos (+3 base) | `entities/states/`, 9 módulos |
| Estados de IA de enemigo | 13 | `EnemyState` |
| Arquetipos / especies | 8 / 21 | `entity_factory`, `bestiary_registry` |
| Tipos estructurales TMX | 35 | `BUILTIN_OBJECT_TYPES` |
| Total declarable en `Objects` | 65 | verificado por prueba |
| Mapas calificados | 17, media **78,7 %** | `grade_stage.py --json` |
| `boss_venado` | **100 %** | `grade_boss.py` |

### AUD-182 — la guía publicaba 22 de 35 tipos vacíos

`docs/STAGE_CREATION.md` es lo que lee un estudiante para construir su nivel.
Su tabla de tipos la genera un script y el CI la vigila con `--check`, y aun
así **22 de los 35 tipos estructurales salían como `| — | — |`**: sin
geometría y sin propiedades. Entre ellos `Spring`, `MovingPlatform`,
`Conveyor`, `Guard`, `Zipline`, `Door`, `Chest` y `Light` — casi todo lo que
convierte un mapa en un nivel.

La causa está en una línea: `structural.get(name, ("—", "—"))`. El diccionario
escrito a mano tenía 12 entradas y los tipos son 35, así que el resto se
publicaba en blanco. Una fila vacía no se lee como «esto está sin documentar»,
se lee como «esto no acepta propiedades» — cuando `MovingPlatform` acepta
cuatro y `Guard` cinco.

**Por qué el gate no lo detectaba.** `--check` compara el documento contra la
salida del generador. Si el generador emite `—`, un documento con `—` está «al
día»: verificaba coherencia con una tabla incompleta. Es el tercer caso de la
misma familia en esta auditoría —AUD-170, GAP-023 y ahora éste—: una
comprobación que se cumple sola.

**Evidencia rojo → verde**

```text
ANTES (tests/test_referencia_tmx.py, sobre el doc publicado)
FAILED ...::test_ningun_tipo_se_publica_sin_propiedades[Conveyor]
FAILED ...::test_ningun_tipo_se_publica_sin_propiedades[MovingPlatform]
FAILED ...::test_ningun_tipo_se_publica_sin_propiedades[Guard]
FAILED ...::test_ningun_tipo_se_publica_sin_propiedades[Zipline]
        … 44 failed, 27 passed
```

```text
DESPUÉS (tras completar `structural` y regenerar)
71 passed in 0.96s
docs\STAGE_CREATION.md: al día
```

La prueba nueva exige que todo tipo aceptado se publique con geometría y con
propiedades; un tipo que legítimamente no acepte ninguna —`DeathPit`,
`NextTrigger`, `PlayerSpawn`— debe declararse en `SIN_PROPIEDADES` con su
motivo escrito, y otra prueba avisa si esa lista se pudre. El generador además
aborta si encuentra un tipo sin documentar, para que el fallo no dependa sólo
de la prueba.

### Lo que se midió y **no** se tocó

Cinco hallazgos reales que no se corrigen porque tocarlos cambia el diseño del
juego o la nota de un estudiante — §9 del protocolo manda parar y preguntar:

| Hallazgo | Medición | Por qué no se toca |
|---|---|---|
| El salto sube más de lo que avanza | 5,64 vs 5,34 baldosas; 0,95 s en el aire | recalibra los 17 mapas y afecta a entregas ya calificadas |
| La rúbrica penaliza usar las mecánicas del motor | `stage_mecanicas.tmx` saca 0/12 en «completable» con 11 objetos de movilidad que el analizador no modela | `grade_stage.py` es la herramienta de calificación |
| 3.048 px sin checkpoint | `stage2_1_oficinas`, 6× el máximo | entrega de estudiante (invariante 1) |
| 13 saltos imposibles | `stage1_2_la_soda` | ídem |
| Los tres jefes, por debajo de la curva | 12,4 · 13,4 · 16,8 frente a 30,2 de media | cambia el diseño del juego |

El segundo es el que más conviene decidir: el analizador de alcanzabilidad
declara su propia limitación en el docstring —«no modela dash, salto de pared
ni plataformas móviles»— y aun así su veredicto vale 12 puntos de la nota. Un
alumno que resuelva un tramo con un resorte es penalizado por usar el motor.

### Gates tras los cambios

| Gate | Resultado |
|---|---|
| `ruff check` | ✅ `All checks passed!` |
| `pytest` de los guardianes documentales | ✅ 183 pasan |
| `generate_tmx_reference.py --check` | ✅ al día |
| `check_tmx_coverage.py --ci` | ✅ cobertura correcta |

### Siguiente iteración

D7 — jefes, con `grade_boss.py` sobre los cuatro y no sólo sobre el de
referencia: `boss_venado` saca 100 %, y los otros tres no se han calificado
nunca con esa rúbrica.

---

## Iteración 7 — 2026-08-02 — Escenas, limpieza y saneo de KNOWN_GAPS

**Hallazgos:** AUD-183 (cadena de niveles sin prueba), AUD-184 (once GAPs
resueltos que seguían figurando como abiertos).

### Escenas: se verificaron ejecutándolas, no leyéndolas

| Qué | Resultado |
|---|---|
| Menú principal | **10 de 10 opciones** llevan a su escena: `CONTINUE`→LoadGame, `START`→Story, `TUTORIAL`, `WORLD MAP`, `INVENTORY`, `BESTIARY`, `ACHIEVEMENTS`, `ACADEMIC DEMOS`, `OPTIONS`; `QUIT` no se ejercitó para no cerrar el proceso |
| Game over | arranca, actualiza y dibuja; `continue` llama a `respawn()` **una vez** y devuelve al escenario |
| Créditos | el rodillo avanza, se marca terminado solo a los **50,0 s**, y confirmar lleva a `TitleScene`. Saltarlos a media también funciona: el primer toque los marca terminados, el segundo vuelve al título |
| Transiciones | **los 16 escenarios** de `STAGE_ORDER` se encadenan en orden y el último abre los créditos |
| Arnés de humo existente | 208 pruebas en verde sobre las 45 escenas |

**No se encontró ninguna escena rota.** Los dos «fallos» que aparecieron
durante la revisión eran del arnés de verificación, no del juego, y conviene
dejarlos escritos porque los dos son fáciles de repetir:

1. **`emit()` no dispara nada.** `EventBus.emit` **encola**; quien invoca a los
   suscriptores es `dispatch()`, una vez por fotograma. Emitir
   `STAGE_COMPLETE` sin despachar no avanza de nivel — y una prueba que lo
   olvide comprueba el silencio y pasa por la razón equivocada. Es deliberado:
   da orden de fotograma predecible y hace imposible un bucle infinito de
   emisiones.
2. **Los créditos «no terminaban».** Terminan a los 50 s y **esperan** a que el
   jugador confirme. El bucle de prueba no pulsaba nada.

### AUD-183 — la cadena completa no tenía prueba

`test_scene_manager.py` prueba la cola con dos escenas de mentira y
`test_scene_smoke.py` arranca cada escenario por separado. Entre las dos no
había ninguna que recorriera los 16 en orden hasta los créditos: cada pieza
probada, el recorrido completo no. Un identificador mal escrito en
`STAGE_ORDER` deja el juego sin final —`discover_stages()` se salta en silencio
lo que no encuentra— y ninguna prueba lo veía.

`tests/test_cadena_de_niveles.py` (4 casos) recorre la cadena real emitiendo
`STAGE_COMPLETE` y despachando, con un fotograma de `update`+`draw` en cada
escenario. Una quinta comprobación fija el contrato del bus, que ya costó
tiempo una vez.

### AUD-184 — KNOWN_GAPS: once entradas resueltas seguían abiertas

De **15 GAPs abiertos**, once tenían su `Resolution:` escrita —el arreglo hecho
y descrito— y seguían sin tachar. El documento estaba dando una imagen de deuda
casi cuatro veces mayor que la real.

Cada uno se verificó contra el código antes de marcarlo, y la evidencia quedó
en la entrada:

| GAP | Evidencia medida |
|---|---|
| 004 | `stage0.tmx` **sí** declara `background_zone` |
| 005 | `_resolve_collision` aplica resolución por ejes separados con `prev_bottom` |
| 006 | un `Player` recién construido expone `_pending_jump` y `_pending_jump_timer` |
| 007 | `stage_loader.py:907` → `Vector2(obj.x, obj.y - 32)` |
| 008 | `09_HUD_SPEC.md` documenta TTF; no queda `hud_digits.png` |
| 009 | ni el código ni el spec mencionan ya la Y=196 |
| 010 | código y contrato declaran los dos `class Action(Enum)` |
| 011 | el contrato documenta `load_all`, `load`, `play`, `get` |
| 012 | el contrato documenta `load_image` con su firma completa |
| 016 | `game_context.py` mide **67 líneas**, no «400+», y recibe sus managers por constructor |
| 017 | `AssetLoader.get_instance()` ya no existe; la clase es instanciable |

**GAP-015 se deja abierto a propósito.** La descomposición sí ocurrió —los
subsistemas viven en `src/framework/stage/` y `StageScene` los compone por
mixins, con prueba de MRO— pero el fichero mide **1.490 líneas** frente a las
«1.200+» que denunciaba el gap. La partición pasó y el monolito siguió
creciendo. Marcarlo resuelto sería falsear la medición.

**Quedan 4 abiertos** (de 15): GAP-002 (heurística bajo vigilancia), GAP-015
(arriba), GAP-021 (renumerar documentos, decisión del temario) y GAP-022
(regenerar el lock, que exige un intérprete 3.11 — en esta máquina sólo hay
3.14).

### Limpieza

Los **8 ficheros de respaldo** se eliminaron con autorización explícita: 4
estaban rastreados en git (recuperables por historial) y 4 sólo en disco, los
cuatro con contenido distinto del original. Se guardó copia en el directorio
temporal de la sesión antes de borrar.

```text
assets/maps/stage1_1/stage1_1.RESPALDO.tmx          (rastreado, lo calificaba grade_stage)
assets/maps/stage1_2_la_soda/stage1_2_la_soda.tmx.bak2   (rastreado)
src/stages/stage1_2_la_soda/README.md.bak2          (rastreado)
src/stages/stage1_2_la_soda/entities.py.bak2        (rastreado)
+ 4 .bak sólo en disco
```

Con el `RESPALDO.tmx` fuera, `grade_stage.py` deja de calificar un respaldo
como si fuera un nivel del juego.

---

## Iteración 8 — 2026-08-02 — Calibración del salto y duplicación de documentos

**Hallazgos:** AUD-204 (el calificador mide el salto con una fórmula que el
motor no cumple → GAP-024), AUD-205 (cinco documentos contenían su propio
cuerpo dos veces).

### AUD-204 — 3 baldosas, no 5,34

`JumpEnvelope.from_settings()` calcula el alcance del salto con el tiro
parabólico y `grade_stage.py` califica con ese número. Nadie había comprobado
que coincidiera con el motor. Se construyó un banco que **ejecuta** al `Player`
real sobre huecos sintéticos (`tests/playtest/jump_bench.py`, reproducible con
`python -m tests.playtest.jump_bench`):

| Hueco | Manteniendo la dirección | Soltando la dirección |
|---|---|---|
| 2 baldosas (32 px) | sí, 39 % de los despegues | sí, holgado |
| 3 baldosas (48 px) | sí, **8 %** | sí, 94 % |
| 4 baldosas (64 px) | **no** | sí, 61 % |
| 5 baldosas (80 px) | **no** | sí, 27 % |
| 6 baldosas (96 px) | no | no |

Dos supuestos de la fórmula son falsos. `AirborneState` fija
`velocity.x = walk_speed * 0.5` mientras haya dirección pulsada, así que la
envolvente analítica (5,34 baldosas) describe una técnica experta —soltar la
dirección en el aire conserva los 90 px/s del suelo— y no la natural, que llega
a 3. Y `max_gap_with_air_jump` duplica el alcance a 10,69 baldosas apoyándose en
un salto aéreo que **no está conectado**: en el aire la pulsación sólo se guarda
en `_pending_jump` para gastarla al aterrizar.

El daño cae del lado que no avisa: `classify_gap` etiqueta «cómodo» un hueco de
4 baldosas que es imposible con entrada natural. El alcance vertical sí
concuerda (5,64 teóricas / 5 medidas): el error es sólo horizontal.

**No se cambió la física ni el calificador.** Apretar la envolvente rebajaría la
nota de geometría de entregas ya calificadas, así que la decisión quedó
registrada como GAP-024 y se tomó la salida acordada: documentar la técnica en
`66_GUIA_DE_LEVEL_DESIGN.md` §1.3 y `04_PLAYER_SPEC.md` §4.1–4.2.
`tests/test_calibracion_del_salto.py` fija los tres techos y falla si alguien
toca `GRAVITY` o `PLAYER_JUMP_FORCE` — comprobado por mutación: 800→700 y
800→900, y −380→−420, los tres hacen fallar la suite.

### AUD-205 — cinco documentos duplicados, y ya estaban divergiendo

La pasada que añade el cuerpo traducido tras `--- Traducción al Español ---`
corrió sobre documentos **ya escritos en español**. Sin nada que traducir, emitió
una copia casi idéntica.

Medido sobre los 54 documentos con separador, los dos grupos no se solapan:

| Grupo | Similitud entre mitades | Cuántos |
|---|---|---|
| Duplicados accidentales (español arriba y abajo) | 88,6 % – 96,2 % | 5 |
| Bilingües legítimos (inglés arriba, español abajo) | 0 % – 24,8 % | 49 |

Los cinco: `35_USER_MANUAL`, `36_STUDENT_MANUAL`, `37_DEMO_QUICK_GUIDE`,
`38_STAGE_BOSS_GUIDE` y `Obsidian_Home`.

Lo que confirma que el riesgo era real y no teórico: **las dos copias ya habían
empezado a separarse**. La mitad de abajo de `36` decía «Tus assignments» y la
de arriba «Tus assignment»; y la de arriba de `37` tenía dos ideogramas chinos
—`método de` seguido de U+7279 y U+5F81, «características» en chino— donde la de
abajo decía «características». Por eso no se
truncó por el separador sin más: se portaron las correcciones de la mitad que se
borraba, y se adoptaron sus etiquetas de metadatos en español.

`tests/test_documentos_sin_duplicar.py` lo vigila con tres reglas. Hacen falta
las tres: la del H1 repetido no ve `Obsidian_Home`, porque ahí la pasada **sí**
tradujo el titular y sólo duplicó el cuerpo. Sin el arreglo fallan 10 casos; con
él, en verde.

---

## Iteración 9 — 2026-08-02 — Lo que se veía al jugar

Origen: informe de quien jugó la compilación —«no vemos el boss rush ni el
speedrun, y el texto dentro del juego está muy pequeño». Los tres son ciertos y
ninguno era el que parecía.

**Hallazgos:** AUD-201 (Boss Rush entraba y dejaba la pantalla en negro),
AUD-202 (el speedrun no existía para el jugador), AUD-203 (el kit de interfaz
usaba la tipografía más pequeña disponible).

### AUD-201 — el modo arrancaba bien y no se veía nada

`BOSS RUSH` **sí** estaba en el menú desde AUD-191, en la posición 7 de 11, y
las once opciones caben en pantalla (`_max_visible = 13`). El pareo de
escenarios también funciona: los cuatro jefes se encuentran en orden.

Lo que fallaba era el orden de dos líneas. Las otras diez opciones arrancan el
fundido y **luego** cambian de pantalla; ésta entraba al jefe primero y pedía el
fundido de salida después, así que el fundido de entrada que dispara `replace()`
llegaba antes y lo pisaba el de salida.

No es un parpadeo. `TransitionManager.update` deja el velo en alfa **255** al
terminar un fundido de salida, y `draw` lo pinta siempre que el alfa sea mayor
que cero, mire o no si la transición sigue activa. Medido, dos segundos después
de elegir la opción:

| Opción | Alfa final del velo |
|---|---|
| BESTIARY (referencia) | 0 — se ve |
| BOSS RUSH (antes) | **255 — negro opaco** |
| BOSS RUSH (después) | 0 |

El jefe se cargaba, corría y sonaba debajo de una pantalla negra permanente.

### AUD-202 — el cronómetro llevaba años midiendo para nadie

Aquí no había una puerta que abrir: faltaba la cadena entera.

| Eslabón | Estado medido |
|---|---|
| `SpeedrunTimer` corre en cada escenario | ✅ ya funcionaba |
| Alguien llama a `SpeedrunTimer.save()` | ❌ **nadie**, en todo `src/` |
| `LeaderboardScene` lee la partida | ❌ tiempos escritos a mano en el código |
| Alguna opción de menú lleva a esa pantalla | ❌ ninguna |

El segundo es el grave. La pantalla mostraba «Stage 0: 1:23.45» y «Boss Venado:
0:45.12» como literales, mientras su propia cabecera prometía *«Reads from save
data»*. Un jugador recién instalado veía récords que nunca hizo. Un marcador que
enseña cifras falsas es peor que no tener marcador: enseña a no fiarse del resto
de lo que el juego afirma.

Los cuatro eslabones quedan cerrados: se guarda al terminar el escenario (sin
cortar la partida si el disco falla), la tabla lee `saves/speedrun.json` y enseña
`--:--.--` donde no hay marca, hay opción `RECORDS` en el título, y salir de ahí
vuelve al título en vez de al menú de demos académicas.

### AUD-203 — `FONT_BODY = 20` no eran 20 px

La queja era comparativa —el texto del juego «ni se nota» al lado del de
Opciones— y esa comparación era la pista. Opciones es la única pantalla dibujada
con `pygame_gui`; el resto usa `theme.font()`, que construía
`pygame.font.Font(None, size)`: la tipografía por defecto de pygame, que entrega
mucha menos tinta por punto pedido que cualquier TTF.

Alto de tinta real de «Salud», a escala 1.0x:

| Constante | Por defecto (antes) | `game.ttf` (ahora) |
|---|---|---|
| `FONT_TINY` (15) | 7 px | 9 px |
| `FONT_BODY` (20) | **9 px** | **12 px** |
| `FONT_TITLE` (38) | 19 px | 21 px |

Los 9 px del cuerpo competían con los **12 px** que `pygame_gui` dibuja pidiendo
14. La pantalla de Opciones tenía la letra un tercio más alta que el resto del
juego pidiendo un tamaño casi la mitad.

La solución no fue subir las constantes —eso descuadra maquetas— sino usar
`game.ttf`, la tipografía propia que la pantalla de título ya usaba por su
cuenta: el kit era el que iba por libre. Cierra el hueco y además **ocupa menos
ancho** (−16 % en «CONTINUAR PARTIDA»), así que no desborda nada.

Ganancia medida, a las dos escalas que importan:

| Escala | `FONT_BODY` antes | después |
|---|---|---|
| 1.0x | 9 px | 12 px (+33 %) |
| 2.0x | 20 px | 23 px (+15 %) |

### Dos cosas que aparecieron por el camino

**La máquina de quien jugó tiene `text_scale = 2.0`**, el máximo de
accesibilidad. Importa para leer los números de arriba —lo que se ve ahí es la
columna de 2.0x— y destapó algo peor: `escalar_texto()` lee la configuración del
jugador y `conftest.py` **no la aísla**, así que la suite mide distinto según el
`config.json` de quien la ejecuta. La primera versión de estas pruebas pasó sin
comprobar nada por eso; ahora fijan la escala a mano.

**Dos pruebas fijaban lo que no importaba.**
`test_demo_scenes` exigía `labels.index("ACADEMIC DEMOS") == 6`, una posición
absoluta que se rompía con cada opción nueva del menú: con BOSS RUSH pasó a 7 y
con RECORDS a 8. Ahora comprueba el orden relativo, que es lo que se quería
decir. Y `test_ui_consistency` reclamaba `boss_rush_entry.py` como escena sin
migrar: vive en `scenes/` pero son dos funciones que no dibujan un píxel.

---

## Iteración 10 — 2026-08-02 — El parry conectado al aturdimiento

### AUD-206 — dos mitades escritas que no se hablaban

`EnemyState.STUNNED` entró en AUD-051 con todo lo necesario: la rama de la
máquina de estados, el temporizador, la salida a `RECOVER` y cinco pruebas en
`test_enemy_state_machine.py`. `EnemyBase.stun()` estaba igual de completo.

Lo que se midió antes de tocar nada:

| Pieza | Estado real |
|---|---|
| `EnemyBase.stun()` | 0 llamantes en producción — sólo lo invocaban las pruebas |
| `STUNNED` leído por el motor | 1 sitio (`boss_base.py:362`), y sólo para consultarlo |
| Parry del jugador | ponía al enemigo en `HURT` 0,3 s |

`HURT` es el estado en el que cae un enemigo con un golpe normal, y sale de él
directo a `ALERT`. Es decir: parar —la acción que exige acertar una ventana de
0,2 s— devolvía exactamente lo mismo que apartarse, y encima más caro. El
combate premiaba esquivar y nunca leer, que es justo lo contrario de lo que el
docstring del propio enum promete: «`STUNNED` — aturdido por una parada o un
golpe pesado. Recompensa la defensa activa en lugar de premiar sólo esquivar».

Es el mismo patrón que AUD-149 y AUD-127: dos piezas correctas, probadas por
separado, y ningún camino que vaya de una a la otra. **Una prueba que llama a
`stun()` a mano no descubre que nadie la llama.** Por eso las pruebas nuevas
entran por `_check_player_contact`, que es lo que ejecuta `StageScene`.

**El cambio.** El bloque de parry llama a `self.stun(self.PARRY_STUN_DURATION)`
en vez de asignar `HURT`. Se añade la constante de clase
`PARRY_STUN_DURATION = 0.9` —holgadamente por encima de los 0,3 s de antes, o
no cambiaría nada para quien juega— que cada subclase puede subir para los
pesados y bajar para los ágiles. El empuje y el tinte del golpe se conservan.

Se extiende a los tres enemigos a distancia (`archer`, `caster`, `shooter`):
desviar el proyectil lo borraba y nada más, y el que disparaba volvía a
disparar. Aturdirlo es la única recompensa con sentido contra un enemigo al que
no alcanzas — da el hueco para acercarse.

De paso, `LAUNCHED` se suma a la guarda de `stun()`. Estaba duplicada en el
bloque de parry y ahí no alcanzaba a quien llamase a `stun()` desde una entrega;
un enemigo por los aires tiene su propia rama con gravedad y meterlo en
`STUNNED` lo dejaba congelado a media altura.

**Fuera de alcance a propósito:** `stage1_1/entities/jungle_frog.py` y
`stage1_2_la_soda/entities.py` tienen su propio bloque de parry y siguen sin
aturdir. Son entregas de estudiantes (invariante 1) y no se tocan.

### Gates tras los cambios

```
pytest tests/test_parada_que_aturde.py -q         → 7 passed
pytest tests/test_enemy_state_machine.py
       tests/test_flechas_y_punalada.py
       tests/test_boss_encounter.py -q            → 110 passed
ruff check <los 5 ficheros tocados>               → All checks passed
mypy <los 4 módulos de src tocados>               → no issues found
```

Las 4 pruebas que fijan el comportamiento nuevo fallaban antes del cambio; las
3 de control (contacto sin parry, cadáver, `LAUNCHED`) pasaban ya y siguen
pasando.

### AUD-207 — la ropa daba su bonificación guardada en la mochila

`engine.core.inventory` ya distinguía dos familias de objetos por el campo
`slot`, y `equip()` / `unequip()` / `get_equipped()` estaban escritos. Pero
`get_total_hp_bonus()` y sus dos hermanas recorrían `_items` entero
multiplicando por la cantidad, **sin leer `_equipped` ni una vez**. Cuatro
consecuencias, medidas antes de tocar nada:

| Lo que hacías | Lo que pasaba |
|---|---|
| Comprar una prenda | Ya dabas su bonificación sin ponértela |
| Comprar las dos capuchas | Sumaban las dos, pese a compartir `slot="head"` |
| Comprar la misma prenda dos veces | Valía el doble |
| Vender una prenda equipada | Te quedabas la bonificación: `sell()` borraba de `_items` y no tocaba `_equipped` |

`equip()` era decorativo: escribía en un diccionario que nadie leía. Y sin
hueco que obligue a elegir, la tienda vende números en vez de ropa — la única
estrategia posible es comprarlo todo.

**El cambio.** Las tres funciones pasan por un `_sumar_bonus()` común que trata
las familias como el catálogo ya decía que eran:

* **mejoras permanentes** (`slot is None`): apilan por cantidad, igual que
  antes. Los niveles están diseñados contando con que dos vasijas son +2.
* **ropa**: cuenta una vez y sólo si está en `_equipped`.
* **habilidades** (`slot="skill"`): no dan estadísticas; `equip()` ya las
  rechazaba.

Y se cierran los tres caminos por los que se conservaba una bonificación sin la
prenda, todos del mismo tipo —`_equipped` sobreviviendo a la desaparición del
objeto— y todos inofensivos mientras nadie leyera ese diccionario:

1. `sell()` desequipa al irse la última copia (con dos, te queda una).
2. `load()` sólo restaura prendas que de verdad están en `items`; un
   `inventory.json` editado a mano no regala nada.
3. Las dos ramas `except` de `load()` vacían también `_equipped`: «empezar de
   cero» incluye lo que se lleva puesto.

**De paso, un gate en rojo.** `test_guia_del_motor::test_menciona_cada_objeto_del_inventario`
llevaba fallando desde que el catálogo creció de 6 a 16 objetos:
`60_GUIA_COMPLETA_DEL_MOTOR.md` §11 seguía publicando «Seis objetos definidos»
y la tabla vieja. Ahora documenta las tres familias, la regla de equipamiento y
—explícitamente— qué parte **no** está cableada todavía, para que nadie diseñe
un nivel contando con una tienda que aún no existe.

### Gates tras los cambios

```
pytest tests/test_ropa_que_hay_que_ponerse.py -q     → 14 passed
pytest tests/test_inventario_recoleccion.py
       tests/test_gameplay_integration.py -q         → 44 passed (con el anterior)
pytest tests/test_guia_del_motor.py -q               → 22 passed (estaba en rojo)
ruff check inventory.py + la prueba nueva            → All checks passed
mypy src/engine/core/inventory.py                    → no issues found
```

6 de las 14 pruebas fallaban antes del cambio. Las de la clase
`TestLasMejorasDelMapaSiguenIgual` son el control: fijan que las mejoras
recogidas en el nivel siguen apilando sin equiparse, que es lo que no podía
romperse.

---

## Iteración 11 — 2026-08-03 — La economía, enchufada (GAP-029, resuelto)

El patrón de esta iteración es el de siempre en este proyecto, y ya van diez:
**piezas correctas, probadas por separado, sin ningún camino que vaya de una a
la otra.** El modelo de datos de la economía estaba entero —`coin`,
`add_coins`, `buy`, `sell`, `equip`, `has_skill`, `ScoreSystem`— y medido sobre
`src/`, fuera de `inventory.py`, tenía **cero llamantes**.

Cinco lotes cierran las cuatro conexiones que faltaban.

### AUD-218 — nadie soltaba una sola moneda

`EnemyBase._die()` emitía `ENEMY_DIED`; la escena lo escuchaba **sólo para
lanzar partículas**. El saldo del jugador no podía subir jugando: la única
forma de tener monedas era editar `data/inventory.json` a mano.

El circuito completo, que es como se prueba y no pieza a pieza:

```
_die() → ENEMY_DIED → SenalesDeEscenario._on_enemy_died
→ Recogible("coin") en el suelo → InteractableSystem._recoger()
→ EVENTO_RECOGIDO → _on_item_picked → Inventory.collect("coin", n)
```

Tres piezas nuevas, todas pequeñas:

* `Recogible.cantidad` (por defecto **1**, así que ninguna de las 26 entregas
  cambia). Permite una bolsa de monedas sin poner veinte objetos en el suelo:
  veinte recogibles por jefe cuestan colisiones cada fotograma y tapan el sitio
  donde murió.
* `score_system.coins_for()`, que comparte con los puntos la lectura del
  `entity_id` (`_tipo_de()`) para que no haya **dos maneras distintas de decir
  «esto es un jefe»**. Un peón da 2 y un jefe 25: con la ropa entre 30 y 50, la
  primera prenda sale a una docena de enemigos.
* `InteractableSystem.soltar_botin()`, que descarta el cadáver que ya pagó. El
  estado vive con el mundo, no en el mixin de señales, porque se va con el
  escenario.

`Inventory.collect()` avisa **una vez** por recogida y no una por unidad: una
bolsa de diez encolaba diez notificaciones de tres segundos y tapaba la
pantalla medio minuto.

### AUD-219 — el marcador que el documento no declaraba

`ScoreSystem` estaba escrito entero y nadie lo instanciaba. Sin instancia no
hay suscripción, así que matar enemigos no sumaba un punto.

**Y la docstring del módulo mentía.** Decía que «el HUD documentaba un slot de
score en `09_HUD_SPEC.md`». Comprobado con `grep`: **cero apariciones**. La
especificación no tenía ninguna región de puntuación, así que el módulo no
cerraba un hueco documentado sino uno real y sin declarar. La afirmación se
había propagado a `KNOWN_GAPS.md`; las dos están corregidas.

El orden importa y por eso se hizo así: primero la región en el contrato
(`09_HUD_SPEC.md` §2.1, `| Score | 124 | 2 | 128 | 14 |`), después el dibujo, y
una prueba que comprueba que **lo que se pinta cabe en lo que el doc promete**.
El doc es lo que los estudiantes leen para colocar su propia interfaz.

`bind_bus()` sigue el patrón de `AchievementSystem`: rebindear **muda** la
suscripción en vez de añadirla. Sin eso, cada muerte sumaría el doble en cuanto
el jugador pasara de un nivel al siguiente.

El HUD enseña puntos **y** monedas juntos: los puntos dicen cómo va la partida,
las monedas si ya alcanza para comprar. El saldo se lee del inventario y no se
guarda aparte — las monedas *son* el objeto `coin`, y duplicar el número
acabaría con los dos desincronizados en cuanto la tienda cobre algo.

> **Divergencia anotada, no arreglada:** `09_HUD_SPEC.md` §2.1 y `hud.py` ya no
> coincidían antes de esto —el doc pone los corazones en Y=20 y el código los
> dibuja en Y=6—. Es anterior a AUD-219 y queda fuera de este lote; la prueba
> de solape se escribió contra la geometría **real** del HUD justamente porque
> comprobarlo contra la tabla del doc no diría nada sobre lo que se ve.

### AUD-220 — comprar ropa dejaba al jugador peor que antes

AUD-207 convirtió una bonificación automática en una que exige una acción —
equiparse. **Esa acción no existía en ninguna pantalla.** `Inventory.equip()`
seguía sin un solo llamante en la interfaz, así que la única forma de ponerse
algo era una consola de Python, y comprar una prenda era pagar por nada.

`InventoryScene` ahora equipa y desequipa con `CONFIRM`. Antes `CONFIRM`
**salía de la pantalla**, además de `CANCEL`: un atajo redundante que ocupaba
la única tecla natural para «ponerse esto». Lo puesto se marca con borde y
etiqueta, porque un hueco invisible no deja saber si ya llevas la capucha o si
pulsaste y no pasó nada. Las monedas dejan de ocupar casilla —son el saldo, no
un objeto que mirar— y pasan a la cabecera.

Un detalle que costó dos intentos: el saldo **no** se puede meter en el
subtítulo. `draw_screen` traduce la cadena entera, así que un f-string con el
número dentro no coincide con ninguna entrada del catálogo y dejaría la
pantalla sin traducir. Lo destapó `test_i18n`, que detectó la entrada huérfana
`Objetos recogidos` en `en.json`. Y el literal de `_()` tiene que ir suelto, no
anidado en un f-string: `check_translations` no lo ve ahí dentro.

### AUD-221 — la tienda

`buy()` y `sell()` estaban probados por unidad desde AUD-207 y sin llamante.
`src/engine/scenes/shop_scene.py`, entrada `SHOP` en el menú del título, junto
a `INVENTORY` porque son las dos mitades de lo mismo: aquí se compra y allí se
pone.

Decisiones:

* **Entrada de menú, no mercader en el mapa.** Un interactuable nuevo obligaría
  a tocar el cargador de TMX, la rúbrica del calificador y las 26 entregas. La
  pantalla no cambia nada de lo que ya funciona.
* **Izquierda y derecha alternan comprar/vender.** Arriba y abajo ya recorren
  la lista y `CONFIRM` actúa en el modo activo: no hace falta una tecla nueva
  que rebindear en las opciones y documentar.
* **La lista sale de `_ITEM_DEFS`**, no de una copia a mano. Una prueba
  compara el conjunto contra el catálogo. Escribirla a mano es exactamente
  como la guía del motor acabó publicando seis objetos cuando ya había
  dieciséis.
* **Quien mueve el saldo sigue siendo el inventario.** La tienda no resta
  monedas: llama a `buy()`, que comprueba y devuelve `False` si no alcanza. Esa
  es la comprobación que evita el saldo negativo, y se prueba con las veinte
  pulsaciones seguidas del caso del aula.

### Un número que se corrigió al escribir esto

La primera versión de esta iteración decía «18 passed» de
`test_ropa_que_hay_que_ponerse.py`. Son **14**. Invariante 6: se ejecutó y se
corrigió antes de dejarlo escrito.

### Gates tras los cambios

```
pytest (14 ficheros: los 6 nuevos + vecinos + gates)  → 247 passed (×2 pasadas)
ruff check <alcance de CI>                            → All checks passed
mypy <mypy_scope.txt>                                 → no issues found in 20 source files
python scripts/check_translations.py --ci             → Catálogos en orden
```

**Por qué no hay aquí un número de la suite completa.** Se ejecutó tres veces y
dio tres conjuntos de fallos distintos con el mismo código. La causa se midió,
no se supuso: `find -newermt '-20 minutes'` mostró `app.py`, `gl_pipeline.py`,
`shaders.py`, `drawing_system.py` y `stage_loader.py` modificados durante la
propia ejecución, **ninguno tocado por esta iteración**. Otra sesión estaba
escribiendo en el repositorio en paralelo. La prueba que lo delata es
`test_la_interfaz_se_dibuja_despues_del_post_procesado`: es una comprobación de
`inspect.getsource` que no depende de píxeles ni de orden, y falló en una
pasada y pasó en la siguiente.

Lo que sí se puede afirmar: las 247 pruebas de la superficie tocada pasan de
forma determinista en dos pasadas seguidas, y los tres gates de CI están en
verde. Un número honesto de la suite completa exige un árbol quieto.

Se cerraron por el camino tres gates que sí estaban rojos:
`test_architecture_doc_matches_tree` (faltaban `score_system.py`,
`shop_scene.py` y `boss_rush_entry.py` en el árbol de `03_ARCHITECTURE.md`),
`test_guia_del_motor` y el único error de `ruff` del repositorio.

`test_particion_de_stage_scene` sigue rojo y merece una nota: `stage_scene.py`
estaba en 1.695 líneas en el último commit, ya 195 por encima del presupuesto
de 1.500. Esta iteración le añade 12 (medido con `git diff --numstat`).
**No se subió el presupuesto** —el propio mensaje del test lo prohíbe—;
extraer otro grupo cohesivo a `stage_parts/` es un lote aparte, y ese fichero
tiene trabajo en paralelo encima.

Los otros fallos observados y no atribuibles a esta iteración:
`test_logros_por_estudiante` ×3 y `test_teaching_tools`, que ya estaban rojos
al empezar (comprobado con `git stash` en la iteración 10).

### Numeración: dos colisiones reales

`CLAUDE.md` §4 dice que el último `AUD-NNN` se comprueba con
`git log --oneline -1`. **Da un número ya ocupado**: el último commit era
AUD-196 y el árbol de trabajo llegaba a AUD-205, y horas después a AUD-217 por
trabajo en paralelo de stage4_1. Lo mismo pasó con `GAP-027`, que esta
iteración y AUD-225 tomaron a la vez; se renumeró **el de aquí** a `GAP-029`
—siete ficheros propios— para no tocar los ajenos en vuelo.

### AUD-238 — las habilidades de jefe, y la invariante que decidió el diseño

`skill_double_jump`, `skill_dash` y `skill_parry` llevaban en el catálogo desde
el principio, con `slot="skill"` y `has_skill()` para consultarlas. **Nadie las
concedía y nadie las consultaba**: el doble salto lo gobierna
`settings.PLAYER_AIR_JUMPS` y el dash `_can_dash`, disponibles desde el primer
fotograma del primer nivel. Tres entradas de catálogo que no significaban nada.

Este lote es el único de la iteración donde cablear las dos mitades **habría
sido un error**. La invariante 2 de `CLAUDE.md` dice que las 26 entregas siguen
funcionando sin tocar una línea; condicionar el doble salto sin más convierte
en imposible cualquier salto que un estudiante diseñara contando con él. Un
nivel entregado, corregido y aprobado dejaría de poder completarse. Eso no es
cerrar un hueco: es romper veintiséis entregas.

Así que se parte en dos mitades con riesgos distintos:

| | Riesgo | Decisión |
|---|---|---|
| **Soltar** la habilidad | Ninguno: un recogible más en el suelo | Activo ya |
| **Exigirla** | Rompe niveles existentes | `PLAYER_SKILLS_REQUIRE_UNLOCK = False` por defecto |

Con el candado apagado, `_tiene_habilidad()` devuelve `True` **sin tocar el
inventario**. No es que se consulte y salga que sí: es que no se consulta. Esa
distinción es la prueba `TestConElCandadoApagadoNadaCambia`, que es la que no
puede ponerse en rojo nunca.

Con el candado encendido nunca se bloquean el salto desde el suelo ni los
fotogramas de coyote — el coyote es el salto normal llegando tarde, no un salto
aéreo, y bloquearlo dejaría al jugador sin poder subir un escalón.

**La trampa que la prueba destapó.** La primera versión dejaba
`skill_drop = ""` en los cuatro jefes. Con eso, encender el candado volvía el
dash **inalcanzable para siempre**: mecánica borrada, no progresión. Lo pilló
`test_hay_un_jefe_para_cada_habilidad_condicionada`, escrita justo para eso.
`BossVenado` concede `skill_dash` y `BossRey` `skill_double_jump`, una línea
cada uno — y son el material que los estudiantes copian, así que el ejemplo
está donde lo van a leer.

De paso, un hallazgo de alcance: **`discover_stages()` no llega a todos los
jefes.** Registra escenarios, y `BossVenado` vive en un módulo que sólo se
importa al cargar su escena, así que un recorrido por `__subclasses__()` tras
`discover_stages()` ve tres de cuatro. La prueba recorre el árbol de ficheros;
es el mismo problema que AUD-144 arregló en la guía del motor.

### Dos cosas del entorno, no del código

**`mypy` reventó con un `INTERNAL ERROR`** —`AssertionError: Cannot find
component '_ufunc_config' for 'numpy.core._ufunc_config._ErrFunc'`—. Es la
caché incremental de `.mypy_cache` guardada contra una numpy 1.x; `numpy.core`
pasó a `numpy._core` en 2.x. Se borra la caché y vuelve a pasar. No es un
defecto del proyecto, pero conviene saberlo antes de perder media hora.

**Los dos únicos errores de `ruff` que quedan** en el alcance de CI están en
`src/engine/render/gl_pipeline.py` (`w` y `h` asignadas y sin usar), fichero de
la sesión en paralelo y no tocado aquí.

### Siguiente iteración

`GAP-029` queda cerrado. Lo que sigue abierto y anotado:

* `test_particion_de_stage_scene` — `stage_scene.py` a 1.707 líneas contra un
  presupuesto de 1.500. Extraer un grupo cohesivo a `stage_parts/`.
* `skill_parry` no la suelta nadie, y es deliberado: parar no está
  condicionado, lo aprende el jugador. Queda en el catálogo para quien quiera
  usarla en su jefe.
* Los recogibles se dibujan todos del mismo color: una moneda de oro y una
  llave son idénticas en pantalla. `DrawingSystem._draw_interactables` podría
  usar el `icon_color` que el catálogo ya define para cada objeto.
* `EnemyCharger` lleva su propio aturdimiento con un booleano `_is_stunned` y
  reutiliza `self._stun_timer`, el mismo atributo que usa la rama `STUNNED` de
  la base (AUD-206). Parar a un charger a media embestida la reanuda al salir;
  es anterior a esta auditoría, pero con 0,9 s de aturdimiento se nota más.

---

## Iteración 12 — 2026-08-03 — La tubería de GPU no hacía nada

Ocho hallazgos alrededor del renderizado. El orden en que se cuentan no es el
orden en que aparecieron: **AUD-223 se encontró el último y explica a los
demás**, así que va primero.

La lección de la iteración cabe en una frase: *todo el post-procesado en GPU
estaba probado y ninguna prueba lo ejecutaba*. Las pruebas usan
`SDL_VIDEODRIVER=dummy`, que no da contexto OpenGL, así que verificaban el
cableado en Python y jamás un píxel. Nada de esto se vio hasta ejecutar la
tubería contra una tarjeta de verdad.

### AUD-223 — todas las pasadas ejecutaban el sombreador de copia

`_create_quad` construía **un** `VertexArray` atado a `_passthrough_prog`:

```python
self._quad_vao = ctx.vertex_array(self._passthrough_prog, ...)
```

y `_run_shader_pass(program, ...)` fijaba los uniformes de `program` —el del
bloom, el de la viñeta, el de la iluminación— para después dibujar
`self._quad_vao`. En moderngl **el programa vive dentro del VertexArray**: es
el que se ejecuta al llamar a `render()`, y el argumento `program` no influía
en nada.

Medido en la máquina de auditoría (Intel HD Graphics 530, OpenGL 4.6, contexto
real): encendiendo bloom, iluminación, viñeta, aberración cromática, refracción
o rayos, la imagen final salía **byte a byte idéntica** a no encender ninguno.
Diferencia media 0,000, pico 0. El coste sí se pagaba —una pasada de pantalla
completa por efecto—; el efecto no llegaba nunca.

No se notó porque los mismos efectos existen por CPU en
`framework/vfx/post_processing.py` y ésos sí se dibujaban: la pantalla se veía
correcta y lo que la tarjeta aportaba era exactamente nada.

Arreglo: un VAO por programa, cacheado, compartiendo los mismos búferes.
`destroy()` los libera todos, no sólo uno.

La prueba (`test_cada_pasada_ejecuta_su_shader.py`) no mide píxeles —en CI no
hay GPU— sino la causa: **cada pasada dibuja con el VAO de su propio
programa**. Comprobación de mutación: devolviendo la línea a
`self._quad_vao.render(...)`, 2 de 5 pruebas caen.

### AUD-224 — el bloom de la GPU era invisible

Con las pasadas ya ejecutándose, el bloom del sombreador resultó ser 30 veces
más débil que el de CPU y **no responder a la intensidad**. Dos causas: el
kernel difuminaba a ±4 píxeles (el de CPU esparce el halo reduciendo y
ampliando la imagen), y el umbral se aplicaba *después* de difuminar, que es el
orden que destruye el halo — la media de un vecindario que mezcla una lámpara
con el fondo cae por debajo del umbral justo donde el halo tiene que estar.

Diferencia media contra la escena sin bloom, a intensidad 0,25 / 0,50 / 0,80:

| | 0,25 | 0,50 | 0,80 |
|---|---|---|---|
| CPU | 5,44 | 7,01 | 8,81 |
| GPU antes | 0,21 | 0,23 | 0,25 |
| GPU después | 1,79 | 3,38 | 5,28 |

Esto importaba más de lo que parece: **AUD-222 apaga el bloom de CPU porque «lo
hace la GPU»**. Sin AUD-223 y AUD-224, ese cambio le habría quitado el bloom al
juego en toda máquina con tarjeta, en silencio.

### AUD-222 — el post-procesado se aplicaba dos veces

`App` arranca con `use_gl=True` y `StageScene.draw` llamaba a
`PostProcessing.apply(surface)` **sin mirar si había GL**, para después subir
esa misma superficie al `GLRenderer`. La viñeta se dibujaba dos veces y el
bloom se calculaba por CPU para que el sombreador lo repitiera.

El reparto vive en `engine/core/gpu_effects.py` y lo fija la raíz de
composición, que es la única que sabe si el contexto GL se creó de verdad.
`PostProcessing` está en `framework/` y no puede preguntar por `App` ni
importar `moderngl` sin romper las reglas de capas que vigila
`test_layering.py`.

Sólo se delega lo que las dos tuberías hacen igual. Se comprobó pasada por
pasada: **destello y tinte** no tienen sombreador; **corrección de color** y
**desenfoque de movimiento** existen en los dos lados pero no son el mismo
efecto; **daltonismo** tiene `colorblind_frag` escrito y nadie le pasa nunca el
modo del jugador —`GLRenderConfig.colorblind_mode` vale 0 y `App` no lo toca—,
así que el sombreador está escrito y jamás se ejecuta. Queda anotado.

La viñeta se apaga en la GPU y no al revés: la de CPU **crece cuando al jugador
le queda poca vida**, y la configuración de GL es estática.

Medido tras AUD-224, con la configuración real del juego:

```
bloom en GPU                     0,19 ms
bloom en CPU                     2,71 ms
ahorro al delegar               +2,6 ms/fotograma  (15 % del presupuesto)
camino GL completo               7,96 ms  -> cabe en 16,67
```

Ese 15 % es la cifra que la propuesta V2 afirmaba sin medir. Ahora está medida.

### AUD-213 — la niebla de guerra recortaba agujeros de borde duro

La máscara era un círculo sólido a alfa 255 restado del velo: el agujero
pasaba de revelado a opaco en un píxel. Y el constructor aceptaba `hardness`,
lo guardaba, y **ningún sitio del repositorio lo leía**: un contrato anunciado
en la firma y en `docs/46_FOG_OF_WAR.md` que el módulo no cumplía.

Ahora la máscara es un disco degradado con caída *smoothstep* y `hardness`
decide dónde empieza la caída. La técnica se copió de
`LightSource.build_gradient`, que ya construía exactamente ese disco.

### AUD-214 — el dibujado de partículas leía numpy partícula a partícula

`update` llevaba desde AUD-006b siendo SoA con numpy, pero `draw` hacía lo
contrario: cinco accesos escalares, tres conversiones y dos comparaciones por
partícula. Con 2.008 partículas vivas: **8,02 ms**, la mitad del fotograma.
Filtrando y convirtiendo los arrays de una pasada y bajándolos a listas de
Python: **3,11 ms** (2,6x). Con 508 partículas, 1,97 -> 0,56 ms (3,5x).

La prueba compara contra la implementación anterior copiada literalmente, y
exige **los mismos bytes**, no un parecido. `Surface.blits()` —la vía obvia— se
descartó midiendo: sólo 4 % mejor con 508 partículas, peor con 2.008, y además
mezcla en vez de escribir, así que pierde el alfa sobre destinos `SRCALPHA`.

### AUD-215 — aberración cromática en los impactos

Pasada nueva: desplaza R y B en direcciones opuestas, radialmente desde el
centro. Va después del bloom y la iluminación y antes de la viñeta, el
daltonismo y el desenfoque; cada una de esas cinco posiciones está razonada en
el propio `render()`.

Cableada de punta a punta: al recibir daño, `stage_parts/senales.py` pide el
golpe por `gpu_effects`, `App` lo recoge y lo deja decaer exponencialmente.
La fuerza sube cuanta menos vida queda — la misma señal que ya dan la viñeta
de daño y la sacudida, en un canal que el jugador lee sin mirar la barra.

### AUD-216 — refracción real bajo el agua

`WaterEffect` no refractaba nada: dibujaba líneas horizontales teñidas cuya X
oscila con un seno, encima de la escena. El fondo que se ve a través del agua
no se distorsionaba, porque nada leía los píxeles de debajo.

La pasada nueva desplaza la coordenada de muestreo dentro de una región, con
desvanecido en los bordes. El riesgo real estaba en las coordenadas: la escena
se sube con `pygame.image.tostring(..., True)`, o sea volteada, así que el
borde superior del rectángulo de pygame es el valor **mayor** de v. Esa
conversión (`region_to_gl_uv`) es lógica pura y tiene nueve pruebas propias.

Con GL, el sombreador **sustituye** a `WaterEffect` en vez de sumarse: dibujar
los dos sería la duplicación que AUD-222 acaba de quitar del bloom.

### AUD-226 — rayos de luz volumétricos

Dispersión radial sobre el mapa de luz que la tubería ya recibía. Van después
de la iluminación a propósito: `lighting_frag` es multiplicativo, así que todo
lo que se sume antes queda aniquilado justo donde un rayo tiene que verse, que
es la sombra.

De paso se sacó la subida del mapa de luz fuera del `if` de la iluminación:
los rayos leen el mismo mapa, y dejarla dentro obligaba a subirlo dos veces por
fotograma (1,9 MB extra por el bus, ~115 MB/s a 60 fps) o a que los rayos sólo
funcionaran con la iluminación encendida.

El foco lo elige la escena, no la tubería: ésta sólo ve una textura de luz ya
compuesta, con los focos mezclados. `StageScene` publica la luz **más fuerte
que esté en pantalla**, ponderando intensidad y radio. Se activa con la
propiedad de mapa `god_rays`.

### Gates tras los cambios

```
pytest (suite completa)                   -> 3324 passed, 6 failed, 4 skipped
pytest (los ficheros de esta iteración)   -> 124 passed
ruff check <alcance de CI>                -> All checks passed
mypy <mypy_scope.txt>                     -> no issues found in 20 source files
scripts/check_tmx_coverage.py --ci        -> Cobertura correcta
scripts/generate_tmx_reference.py --check -> al día
```

Verificación en GPU real, que es la que faltaba y la que encontró todo:

```
GL_RENDERER   Intel(R) HD Graphics 530      GL_VERSION  4.6.0
diez programas compilan
las seis pasadas modifican la imagen (antes: ninguna)
```

**Los 6 fallos restantes son ajenos a esta iteración**:
`test_logros_por_estudiante` x3, `test_particion_de_stage_scene`
(`stage_scene.py` sigue por encima del presupuesto) y `test_vista_cenital` x2,
que pasan en aislado y no los provocan los ficheros de aquí — se comprobó
ejecutándolos delante.

### AUD-229 — subir el fotograma costaba más que dibujarlo

Con la tubería ya funcionando de verdad se pudo medir el reparto real del
tiempo, y el mayor consumidor no era ningún efecto: era **entregarle la imagen
a la tarjeta**. Cada fotograma se hacía
`pygame.image.tostring(superficie, "RGBA", True)` —una pasada por los 480.000
píxeles en Python para reordenar canales y voltear— y el `bytes` resultante
obligaba a moderngl a copiarlo otra vez:

```
pygame.image.tostring(RGBA, flip=True)    3,458 ms
texture.write(bytes)                      7,517 ms
texture.write(memoryview de la surface)   0,200 ms
```

Escribir el búfer de la superficie no convierte ni copia. A cambio los píxeles
llegan como los guarda pygame, y las tres diferencias las arregla `upload_frag`
en la pasada de copia que ya existía: el volteo, el orden de canales y el alfa.

El alfa fue lo que costó encontrar. Una `Surface` sin `SRCALPHA` —la superficie
interna del juego lo es— tiene la máscara de alfa a cero, así que su cuarto
byte vale 0. `tostring` lo reponía a 255 al convertir; el búfer crudo no. Con
`GL_BLEND` activo y `SRC_ALPHA, ONE_MINUS_SRC_ALPHA`, un fragmento con alfa 0
**no escribe nada**: la pantalla salía entera del color de limpieza, sin un
solo error en consola. Lo destapó una prueba de identidad —subir y bajar sin
efectos tiene que devolver la misma imagen—, que ahora vive en el guion de
verificación en GPU.

El orden de canales se **detecta** de las máscaras de la superficie; si el
formato no es uno de los dos conocidos se vuelve a `tostring`. Equivocarse aquí
no da un error, da los colores cambiados.

De paso, la textura del mapa de luz dejó de crearse y soltarse en cada
fotograma (0,46 ms, 27 ms por segundo a 60 fps en reservar memoria que ya se
tenía), y se recuperó `_light_fbo`, que se ataba y se limpiaba para nada: la
pasada siguiente escribía en otro FBO y deshacía el `use()` una línea después.

### AUD-230 — el bloom se difuminaba a resolución completa

AUD-224 ensanchó el kernel del bloom para que se viera, y eso lo hizo caro:
**3,39 ms**, más que los 2,26 ms del bloom por CPU al que sustituye. O sea que
delegarlo pasó a salir perdiendo.

Se hace ahora en el FBO de media resolución que la tubería **ya reservaba y no
usaba nunca** (`_bloom_fbo`, creado desde el primer día). A un cuarto de
píxeles el mismo kernel cuesta un cuarto, y el halo sale más suave gratis: al
recomponer, el filtrado bilineal lo interpola de vuelta a tamaño completo, que
es justamente lo que hace la tubería de CPU con `smoothscale`.

Medido: **3,39 → 1,70 ms**, con el mismo aspecto (1,72 / 3,24 / 5,10 de
diferencia media frente a 1,79 / 3,38 / 5,28 antes, a intensidad
0,25 / 0,50 / 0,80). Delegar el bloom vuelve a ser ganancia.

### Rendimiento, de punta a punta

| | antes | después | |
|---|---|---|---|
| Subir el fotograma | 10,98 ms | **0,20 ms** | AUD-229 |
| Bloom en GPU | 3,39 ms | **1,70 ms** | AUD-230 |
| **Camino GL con la configuración real** | 7,96 ms | **3,76 ms** | 2,1× |
| Todas las pasadas encendidas | 25,80 ms | **15,32 ms** | 1,7× |

### Gates finales de la iteración

```
pytest (suite completa)                   -> 3368 passed, 4 failed, 4 skipped
ruff check <alcance de CI>                -> All checks passed
mypy <mypy_scope.txt>                     -> no issues found in 20 source files
scripts/check_tmx_coverage.py --ci        -> Cobertura correcta
scripts/generate_tmx_reference.py --check -> al día
scripts/check_translations.py --ci        -> Catálogos en orden
```

En GPU real (Intel HD 530, OpenGL 4.6): identidad exacta sin efectos
(diferencia 0,000), y las seis pasadas modifican la imagen.

**Los 4 fallos restantes son ajenos**: `test_logros_por_estudiante` ×3 y
`test_particion_de_stage_scene`, que viene de que `stage_scene.py` sigue por
encima del presupuesto de 1.500 líneas por trabajo en paralelo.

La referencia consolidada de todo esto —cadena de pasadas, reparto CPU/GPU,
costes y cómo un escenario enciende cada efecto— es
`docs/74_TUBERIA_DE_GPU.md`.

### Numeración: la tercera colisión seguida

`CLAUDE.md` §4 vuelve a quedarse corto. Esta iteración tuvo que renumerar
**cinco veces**: 197–202 -> 212–217, luego 212 -> 222 (lo tomó
`drawing_system`), 218 -> 223 y 219 -> 224 (los tomaron `inventory` y
`score_system`), y finalmente 217 -> 226 porque el informe ya citaba ese número
para stage4_1.

La causa es estructural, no un descuido: `git log -1` sólo ve lo commiteado, y
aquí hay varios frentes con trabajo sin commitear que ya consumen números. El
procedimiento que funciona es escanear el árbol entero —commiteado o no— y
tomar el primero libre por encima del máximo.

---

## Iteración 12 — continuación — 2026-08-03 — Los dos cabos sueltos de la 11

Los dos salieron anotados al final de la iteración anterior. Ninguno es grande;
los dos son consecuencia directa de lo que aquella iteración cambió.

### AUD-234 — todos los recogibles se veían iguales

`DrawingSystem._draw_interactables` pintaba **todos** los recogibles con el
mismo `_COLOR_RECOGIBLE = (240, 210, 90)`. Una moneda de oro, una llave roja y
una vasija de corazón eran tres rectángulos idénticos en pantalla.

No era estético: desde AUD-218 los enemigos sueltan monedas, así que el suelo
de un nivel se llena de recogibles y el jugador ya no puede saber de un vistazo
si eso de ahí es la llave que le falta o el cambio de matar a un esbirro.
AUD-238 lo empeoró — la reliquia del jefe cae junto a las monedas, del mismo
color que ellas.

El dato **ya existía**: `ItemDef.icon_color` lleva desde el principio en el
catálogo, con un dorado para `coin` y un rojo para `heart_vessel`, y sólo lo
leía el aviso de recogida. Otra vez el patrón del proyecto: el dato estaba,
quien lo necesitaba estaba, y no había camino entre los dos.

Un `item_id` libre —el que invente un estudiante— no está en el catálogo y
conserva el color de siempre. Ese es el control de la prueba: **ninguno de los
niveles entregados cambia de aspecto.**

### AUD-239 — parar una embestida sólo la aplazaba

`EnemyCharger` y `EnemyWalker` llevan su propia máquina de ataque en banderas
(`_is_charging`, `_is_winding_up`), y `stun()` sólo cambiaba el estado de la
base. Al salir del aturdimiento, `_alert_behavior` se encontraba
`_is_charging = True` y **reanudaba la misma embestida** — contra el jugador
que se había acercado a castigar durante los 0,9 s.

Ya pasaba antes de AUD-206: con los 0,3 s de `HURT` el parpadeo era corto y se
confundía con un empujón. Con la ventana larga el enemigo se queda quieto, el
jugador entra a pegar, y entonces arranca. **Es peor que no aturdir**: enseña
que parar es una trampa.

El arreglo es un gancho, `EnemyBase._cancelar_ataque_en_curso()`, que `stun()`
llama tras la guarda. Vacío por defecto; lo sobreescriben los dos enemigos que
guardan «estoy atacando» fuera de `EnemyState`. Es un gancho y no un `stun()`
sobreescrito en cada subclase porque así queda documentado para las entregas:
si tu enemigo lleva banderas propias, límpialas ahí.

**El segundo defecto, más silencioso.** `EnemyCharger.__init__` declaraba
`self._stun_timer`, **el mismo nombre que usa `EnemyBase` para la rama
`STUNNED`**. Dos dueños para una variable: la base la descuenta en su rama y el
charger en `_alert_behavior`. No chocaban porque hasta AUD-206 nadie llamaba a
`stun()` en producción — una colisión latente que sólo se activó al conectar el
parry. Renombrada a `_recuperacion_timer`, que es lo que de verdad es: su
exposición tras embestir, no un aturdimiento.

### Gates

```
pytest (los 4 ficheros nuevos + vecinos)  → 55 passed
pytest -k "charger or walker or enemy or interact or drawing or stage0" → 237 passed
ruff <ficheros tocados>                   → All checks passed
```

---

## Iteración 13 — 2026-08-03 — Barrido de mecánicas: qué funciona de verdad

Esta iteración no arregla un defecto encontrado por casualidad: **busca** el
modo de fallo del repositorio de forma sistemática, con la herramienta que
AUD-233 escribió justo para eso (`scripts/check_orphan_systems.py --todos`) más
verificación manual candidato a candidato. El script avisa de que su salida
«son preguntas, no defectos», y así se trató: de 180 símbolos señalados, la
inmensa mayoría son utilidades y material docente que el juego no tiene por qué
llamar. Dos preguntas resultaron ser defectos.

### AUD-243 — parar el ataque de un jefe no hacía nada

La cadena estaba entera y desconectada **por arriba**:

```
BossAttack(parriable=True) → AttackScheduler.se_puede_desviar
→ AttackScheduler.desviar() → BossBase.recibir_parry() → ???
```

`recibir_parry()` se describe a sí misma como «el punto de entrada de la
mecánica» y no tenía **un solo llamante en todo el repositorio**: ni en
producción ni en pruebas. Medido con `grep -rn "recibir_parry"`: una línea, su
propia definición. `parriable`, `aturde_al_parry` y `se_puede_desviar` se
probaban por unidad y no cambiaban nada en ningún jefe.

Es el mismo defecto que AUD-206 arregló para los enemigos normales, en la mitad
de los jefes. Se conecta con un gancho —`EnemyBase._aturdimiento_por_parry()`,
que `BossBase` sobreescribe— para no meter conocimiento de jefes en la clase
base. La prueba incluye **la comprobación que lo habría evitado**: que
`recibir_parry` tenga llamante en `src/`, no sólo en `tests/`.

### GAP-032 — cinco de siete mecánicas de F5 no las invoca nadie

La fase 5 de la migración ECS (documento retirado en la fusión) listaba siete
mecánicas bajo el epígrafe «Y en código:». Medidas una por una:

| Mecánica | ¿La usa el juego? |
|---|---|
| Parry del jefe | Sí, desde AUD-243 |
| Fase invulnerable | Sí (`boss_base.py:208`) |
| Tiempo bala | **No** — se construye y no se vuelve a tocar |
| Scroll forzado | **No** — ni `arrancar()`, ni `update()`, ni `se_quedo_atras()` |
| Bullet hell | **No** — 0 usos fuera de su módulo |
| Escalado de fase | **No** — `escala_de_fase` sólo se define |
| Teletransporte | **No** — 0 usos |

El caso más claro es `ScrollForzado`. Su docstring explica con detalle por qué
el borde mata en vez de empujar —«el nivel dijo *sígueme* y no lo seguiste»— y
ese borde no mata a nadie, porque la cámara nunca se mueve sola.

**No se cablearon aquí, y es una decisión.** Cada una necesita una decisión de
diseño, no sólo conectarla: quién enciende el scroll y el tiempo bala (una
propiedad TMX o un `Disparador`, y eso toca `06_TMX_SPEC.md`, que es contrato
para las 26 entregas), y qué jefe usa el enjambre, el teletransporte y el
escalado. Lo que **sí** era urgente es que el documento dejara de decir «y en
código» sobre cosas que no ocurren: lleva ahora la tabla de arriba y el aviso
de no diseñar contando con las cinco que faltan.

### Validación completa

```
pytest (suite completa)              → 3439 passed, 4 failed, 4 skipped
scripts/grade_stage.py assets/maps/  → 16 mapas, media 79,8 %
scripts/grade_boss.py boss_venado    → exit 0
los 6 validadores de CI              → exit 0 los seis
mypy <mypy_scope.txt>                → no issues found in 20 source files
```

**Los 4 fallos, atribuidos uno por uno y ninguno de esta iteración:**

* `test_particion_de_stage_scene` — `stage_scene.py` va por 1.923 líneas contra
  un presupuesto de 1.500. Al empezar la sesión estaba en 1.695; de las 423 de
  exceso, 12 son de la iteración 11 y ~216 las ha añadido el trabajo en
  paralelo mientras corría esto.
* `test_salida_de_consola[check_orphan_systems.py]` — el guardián de AUD-233 no
  fija su salida de consola; es del otro frente (última vez tocado en AUD-245).
* `test_teaching_tools` — `preview_tmx.py` no menciona «estación» en su
  resumen. Anterior a esta sesión.
* `test_reported_ui_bugs::test_la_interfaz_se_dibuja_despues_del_post_procesado`
  — **pasa en aislado**. Es una comprobación de `inspect.getsource` sobre
  ficheros que el otro frente está reescribiendo en caliente.

Los 2 errores de `ruff` que quedan (`numpy` sin usar) están en
`tests/test_stage4_1.py`, sin commitear y del otro frente.

---

## Iteración 14 — 2026-08-06 — D1–D9 (barrido completo de dominios)

**Commit auditado:** `a82a2ee` (último AUD: 303). Árbol de trabajo con la
limpieza staged de 36 documentos de `docs/` (sin commitear), la biblia técnica
`75_BIBLIA_TECNICA.md` nueva y el índice maestro actualizado.

### Gates ejecutados (todos en la máquina con el `.venv`, Python 3.14.6, SDL dummy)

| Gate | Resultado | Salida resumida |
|---|---|---|
| `ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/` | **ROJO → VERDE (AUD-304)** | `LOG004 .exception()` fuera de handler en `stage_parts/diagnostico.py:71` → corregido → `All checks passed!` |
| `mypy` (trinquete `mypy_scope.txt`) | ✅ VERDE | `Success: no issues found in 25 source files` |
| `scripts/check_dependency_sync.py` | ✅ VERDE | `OK 14 dependencies agree across pyproject.toml and requirements.txt` |
| `scripts/check_translations.py --ci` | ✅ VERDE | `Catálogos en orden` (38 es / 82 en; 40 cadenas sin entrada, correcto si el original ya está en ese idioma) |
| `scripts/check_tmx_coverage.py --ci` | ✅ VERDE | `Cobertura correcta`; nota: `BossSpawn` es el único de 70 tipos que ningún mapa usa |
| `scripts/generate_tmx_reference.py --check` | ✅ VERDE | `STAGE_CREATION.md: al día` |
| `scripts/validate_assets.py` | ✅ VERDE | `0 errors, 0 warning(s)` |
| `scripts/validate_tmx.py --ci` | ✅ VERDE | `17/17 passed` |
| `scripts/grade_stage.py assets/maps/ --json` | ✅ VERDE | 16 mapas, media **79,9 %**, 0 errors (peor dato de diseño: `stage2_1_oficinas` sin ningún checkpoint, 3048 px) |
| `scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json` | ✅ VERDE | 1 jefe, **100 %**, 0 errors |
| `pytest tests/` (suite completa) | **NO VERIFICADO** | abortado por el usuario a los pocos segundos; se corrió subconjunto en su lugar: `189 passed, 3860 deselected` en 23 s |
| smoke `python main.py` (renderer dummy) | ✅ VERDE | `SMOKE OK`; warning de OpenGL esperado con el driver dummy (cae al renderer no-rápido, no rompe el arranque) |

### Hallazgos

| ID | Dominio | Severidad | Estado | Resumen |
|---|---|---|---|---|
| AUD-304 | D1 | BLOQUEANTE | **CERRADO** | `LOG004` en `diagnostico.py:71`: `.exception()` fuera de un handler según ruff. Falso positivo estático: el único llamante es un `except Exception:` (`stage_scene.py:1038`). Fix: `# noqa: LOG004` con comentario AUD. Prueba: el propio gate (rojo → verde). |
| AUD-305 | D2 | ALTA | **CERRADO** | `docs/70_INFORME_DE_AUDITORIA_VIVO.md` estaba retirado (borrado staged en la limpieza de 36 docs) pero el contrato vigente del prompt 69 §7 ordena mantenerlo, y `KNOWN_GAPS.md` (líneas 33 y 96), `74_TUBERIA_DE_GPU.md` (iteración 12), `75_BIBLIA_TECNICA.md` y dos tests lo citan. Causa raíz: la limpieza retiró el informe sin reconciliar el contrato que lo exige. Decisión (consulta al usuario): **restaurar desde git y continuar**. Fix: `git restore --staged --worktree`, este informe de vuelta, fila añadida al índice maestro. |
| AUD-306 | D2 | BAJA | **CERRADO** | Encabezado «Iteración 12» duplicado en este informe (la segunda sección es la continuación de la 11). Renombrado a «Iteración 12 — continuación». |
| AUD-307 | D2 | ALTA | **CERRADO** | `docs/22_API_CONTRACTS.md` documentaba APIs que no existen o con nombre/ruta vieja. Verificado con un comprobador AST (temp): **50 de 381 símbolos** citados no existían. Corregidas 13 entradas: funciones de módulo de `event_bus` que no existen; `DynamicMusicSystem` (vive en `framework/audio/dynamic_music.py`, movido a §4.3 y sin `sfx_volume`/`is_muted`); `HUD.bind_player` → API real (17 métodos); `MessageBox.is_active` → `is_visible`; `Checkpoint.is_active` → `is_activated`; `FrameworkUsageError` (en `framework/__init__.py`); extractores `extract_*` de `PatternRecognitionTools` que no existen (viven en VisionTools); rutas de los 7 lab scenes; `SceneRegistry.list_scenes/register_demo_scenes` (método vs función de módulo); `GameContext` (en §2.5); `DebugOverlay.toggle/update/is_active` → `visible/handle_input`; `draw_panel_label`; `SourceSurfaceManager.next/current/...` → `cycle/current_source/...`; `ErrorDisplay.show` → `set_error`; bloque boss duplicado con `_begin_phase_transition` (real: `_start/_finish_phase_transition`) y `BossVenado` en la ruta correcta; numeración de secciones duplicada (2.6, 17.1, 18, 19) renumerada. Prueba: comprobador AST sobre el doc — **rojo (50 fallos) → verde (374 símbolos, todos existen)**. Riesgo: el doc es la fuente de verdad de firmas; los cambios la alinean con el código ejecutado. |
| AUD-308 | D3 | MEDIA | **CERRADO** | `test_coyote_time_expires` y `test_coyote_time_allows_late_jump` fijan el contador a mano y sólo comprueban la comparación: nadie defendía el **avance** (`_coyote_counter += dt * 60.0`). Una mutación que congelaba el contador pasaba la suite. Fix: `test_coyote_counter_avanza_con_el_tiempo` y `test_coyote_time_expira_por_acumulacion` en `tests/test_player_physics.py`. Prueba: mutante línea 958 muere con las nuevas pruebas (24 % → 32 % de defensa global del módulo). |
| AUD-309 | D3 | MEDIA | **CERRADO** | La fórmula de `max_health` (base + reliquias + árbol, tope `CORAZONES_MAXIMOS`) no la defendía nadie: `Add → Sub` pasaba la suite. Fix: `test_max_health_suma_los_bonus` y `test_max_health_respeta_el_tope` en `tests/test_player_damage.py`. Prueba: mutante línea 374 muere con las nuevas pruebas. |
| GAP-033 | D3 | — | **CERRADO** | El módulo `player.py` quedaba en **32 %** de defensa por mutación: 17 supervivientes, los valiosos sin ninguna prueba (daño ofensivo línea 480, `draw()` completo, `ledge grab`, SFX de aterrizaje) y el de `heal` indistinguible bajo `heal_mult=1.0`. Fix: 9 pruebas nuevas en `tests/test_player_damage.py` (guarda `and` → `or` del golpe, combo `*`→`/` y multiplicadores de `current_attack_damage` bajo HARD + bonus, `heal` bajo HARD, `_hitbox_consumed`) y 6 de `draw()` en `tests/test_player_physics.py` (cámara, rectángulo, sprite centrado `// 2`, parpadeo, color HURT, más `test_aterrizar_en_suelo_emite_sfx_land`). El `ledge grab` ya no vive en `player.py` (AUD-334 lo movió a `resolucion.py`). Prueba: **unión de ambos suites = 44 %** (11/25 muertes; 28 % física, 20 % daño por separado); supervivientes restantes todos benignos (constantes de animación, guard numéricos, `__setattr__`, bit `_hitbox_consumed` redundante). Detalle en `KNOWN_GAPS.md`. |
| D4 | D4 | — | **SIN HALLAZGOS** | Barrido de `except Exception:` en `src/engine` y `src/framework`: los 21 tienen log con traza, re-raise con limpieza o comentario que explica el porqué (patrón AUD-289). `check_orphan_systems.py`: 209 símbolos ejercitados, 25 verificados no-defectos, 4 huérfanos reales **ya anotados** (GAP-032), ningún módulo «declarado terminado» que mienta. Sin TODO/FIXME reales fuera de `src/stages/`. |
| D5 | D5 | — | **SIN HALLAZGOS** | Estados y sensación: GAP-024 (calibración del salto) resuelto por decisión; 60 tests de legibilidad/calibración/máquina de estados pasan; coyote y buffer ahora defendidos (AUD-308). |
| D6 | D6 | — | **SIN HALLAZGOS** | 229 tests de enemigos/IA pasan (state machine, SquadBrain, doble tabla TMX↔código, guardia que busca). |
| D7 | D7 | — | **SIN HALLAZGOS** | 266 tests de jefes pasan (boss_base, encounter, grader, rush, fase, parry); `grade_boss` del venado: **100 %**, 0 errors. GAP-030 resuelto. |
| D8 | D8 | — | **MEDICIONES, SIN CORRECCIÓN** | `grade_stage`: 16 mapas, media **79,9 %**. Perfectos: `stage0` (100 %) y `stage2_2` (100 %). Peores datos de diseño: `stage2_1_oficinas` **0 checkpoints en 200×38** (3048 px sin punto de guardado), `stage1_3_las_aulas` repecho de 544 px imposible de saltar, `stage_mecanicas` 944 px sin checkpoint + 3 plataformas aisladas, `stage4_1` sin enemigos (¿vertical deliberado?). Las arenas de jefe puntúan bajo en `design_completable` por diseño (el propio grader advierte que no aplica). Cambiar un TMX toca entregas: **queda como decisión de diseño, no se toca sin orden**. |
| D9 | D9 | — | **PROPUESTA (no ejecutada)** | Presentación: la tubería GPU (`74_TUBERIA_DE_GPU.md`) sigue apagada por defecto (fallback software); los sprites de Stage0 no coinciden con `07_STAGE0_DESIGN.md` (240×14 vs 100×38). Ambas requieren decisión humana antes de tocar nada. |

### Recuento de pruebas

- Suite completa: **NO MEDIDO** en esta iteración (abortada por el usuario).
- Subconjunto `-k "rutas or diagnostico or stage_scene or app"`: 189 passed / 0 failed / 0 skipped, 3860 deselected, 23,01 s.
- Subconjunto `-k "player or coyote or heal or mutation"`: 165 passed / 0 failed, 3891 deselected, 36,20 s (incluye los 6 tests nuevos de AUD-308/309).
- `tests/test_player_physics.py` + `tests/test_player_damage.py` + `tests/test_player_hurtbox.py` + `tests/test_audit_regressions.py`: **98 passed** (GAP-033, 16 pruebas nuevas: daño ofensivo, combo, heal bajo HARD, hitbox consumida, draw por píxel en ambas ramas y SFX de aterrizaje).
- Subconjuntos orientados a D5 (estados/sensación), D6 (enemigos/IA) y D7
  (jefes): **60 / 229 / 266 passed**, 0 failed cada uno.
- `mutation_check.py --ci` (conjunto por defecto): 84,0 % / 72,0 % / 96,0 %, 240 s — OK.
- `mutation_check.py --objetivo player.py --pruebas <suite jugador>`: **24 % → 32 %** tras AUD-308/309; **44 % (11/25)** con la unión de la física + daño tras GAP-033.

### GAPs

- Nuevos: GAP-033 (defensa por mutación del módulo jugador, 17 supervivientes clasificados).
- Cerrados: GAP-033 (unión de suites **44 %**, ningún superviviente valioso).

### Dominios de §8

- Cubiertos: D1 (gates y arranque), D2 (consistencia doc ↔ código: índice
  maestro, rutas citadas en docs — 96 refs a scripts/tools, todas existen —
  y contraste AST de `22_API_CONTRACTS.md` contra firmas reales), D3
  (honestidad de las pruebas: mutación por defecto OK; defensa del jugador
  medida y mejorada de 24 % a 32 %), D4 (barrido de `except` y huérfanos),
  D5 (estados y sensación), D6 (enemigos e IA), D7 (jefes) y D8 (niveles:
  mediciones `grade_stage` completas, sin tocar TMX).
- Pendientes de decisión humana: D9 (propuestas de presentación registradas,
  sin ejecutar).

### Lo que NO se pudo verificar y por qué

- `pytest tests/` completo: abortado por el usuario (duración); se sustituyó por subconjunto orientado al cambio.
- Matriz 3.11/3.12/3.13 de CI: esta máquina sólo tiene 3.14.6; la matriz sólo la corre CI.
- Jugabilidad real (renderer, sonido): driver dummy en este entorno sin pantalla.

---

## Iteración 15 — 2026-08-09 — D1 y D4: los gates que decían protegernos

**Commit auditado:** `3902137` (último AUD del log: 352). Árbol de trabajo con
las tres frentes sin commitear que el propio `docs/89` §18.7 ya señalaba como
el riesgo de proceso más urgente (AUD-343…352 + este lote).

**Cómo empezó.** Se pidió una auditoría multidisciplinar completa con el prompt
genérico —el mismo que `docs/69` §Parte 1 analiza y descarta—. Se ejecutó el
prompt calibrado de `docs/69` §Parte 2 en su lugar, en el orden de dominios de
§8. Los dos primeros gates de D1 destaparon el hallazgo bloqueante, así que la
iteración se quedó en D1, D3 y D4 y no bajó a D5-D9.

### Gates ejecutados (máquina con el `.venv`, Python 3.14.6, SDL dummy)

| Gate | Resultado | Salida resumida |
|---|---|---|
| `ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/` | **ROJO → VERDE (AUD-353)** | `RUF100 Unused noqa (non-enabled: LOG004)` en `stage_parts/diagnostico.py:74` → `All checks passed!` |
| `mypy` (trinquete `mypy_scope.txt`) | ✅ VERDE | `Success: no issues found in 26 source files` |
| `scripts/check_dependency_sync.py` | ✅ VERDE | `OK 14 dependencies agree across pyproject.toml and requirements.txt` |
| `scripts/check_translations.py --ci` | ✅ VERDE | `Catálogos en orden` (48 es / 82 en) |
| `scripts/check_tmx_coverage.py --ci` | ✅ VERDE | `Cobertura correcta`; `BossSpawn` sigue siendo el único de 70 tipos sin mapa |
| `scripts/generate_tmx_reference.py --check` | ✅ VERDE | `STAGE_CREATION.md: al día` |
| `scripts/validate_assets.py` | ✅ VERDE | `0 errors, 0 warning(s)` |
| `scripts/validate_tmx.py --ci` | ✅ VERDE | `17/17 passed` |
| `scripts/check_orphan_systems.py` | ✅ VERDE | 3 huérfanos reales ya anotados; ningún módulo «declarado terminado» que mienta |
| `scripts/grade_stage.py assets/maps/ --json` | ✅ VERDE (con nota, AUD-356) | 16 mapas, media **79,9 %** — sin deriva desde la iteración 14. El `--json` **no era JSON**: ver AUD-356 |
| `scripts/grade_boss.py … --json` | ✅ VERDE (ídem) | 1 jefe, **100 %** |
| `pytest tests/` (suite completa) | ✅ VERDE | **4.335 passed, 7 skipped**, 489 s (línea base, antes de tocar nada) |

### Hallazgos

| ID | Dominio | Severidad | Estado | Resumen |
|---|---|---|---|---|
| AUD-353 | D1 | **BLOQUEANTE** | **CERRADO** | El gate de lint del CI estaba **rojo en `dev`** y nadie lo sabía. `AUD-304` añadió `# noqa: LOG004` a `diagnostico.py:74` cuando ruff marcaba esa línea; ruff movió LOG004 a *preview*, y con la regla apagada la directiva pasó a ser `RUF100`. Nada del fichero cambió: cambió el linter. Causa raíz doble — (a) la supresión caducó, (b) `ruff>=0.6` no tiene tope, así que la definición de «verde» del proyecto la fija quien publique río arriba. Fix: quitar la directiva conservando el comentario que explica por qué `.exception()` es correcto ahí, y `test_ruff_esta_limpio_en_el_alcance_del_ci`, que **ejecuta** ruff sobre el alcance **leído de `ci.yml`** (leído, no copiado: una lista propia se desincroniza). Las tres pruebas que ya existían sólo miraban que la orden siguiera escrita — la misma familia de AUD-124 con mypy. Prueba: roja con el fallo real pegado → verde. Riesgo: si LOG004 vuelve a activarse, el sitio para reponer la supresión queda señalado en el código. La causa (b) queda en **GAP-034**. |
| AUD-354 | D4 | ALTA | **CERRADO** | `App._draw` liga `escena` **dentro** del `if stack_size > 0` y lo lee ochenta líneas después, ya fuera, en la rama de GPU que compone la interfaz de AUD-343: con la pila vacía y la tarjeta activa es un `UnboundLocalError`. La pila se vacía porque `SceneManager.pop` no tiene suelo (`game_over_scene.py:70`, `combo_demo_scene.py:106`) y `run()` no vuelve a mirarla entre `update` y `_draw`. `run()` atrapa la excepción y llama a `_fallback_to_title()`: el jugador ve el título aparecer solo; diez fotogramas así y `MAX_CONSECUTIVE_FRAME_ERRORS` aborta el juego. **No lo veía nadie porque en CI `_use_gl` es siempre `False`** — el mismo modo de fallo que AUD-343, código que sólo corre en la máquina del jugador. Fix: ligar `escena: BaseScene | None = None` antes del `if`. Prueba: `tests/test_el_fotograma_sin_escena.py` (3 casos: pila vacía, escena de GPU, escena de CPU), con el cableado GL montado a mano. Riesgo: ninguno para las rutas existentes — los otros dos casos fijan que el overlay de AUD-343 sigue llegando igual. |
| AUD-355 | D4 | ALTA | **CERRADO** | La verja de datos hostiles de **AUD-344** se escribió dentro de `resolver_movimiento`… **a la que no llama ninguna entidad del juego**: sólo aparece en su módulo, en el `__all__` del paquete y en los tests. El jugador compone los pasos a mano (`player.py:1077, 1085, 1125, 1159`), y es `resolver_eje_x` quien hace el `pygame.Rect(int(estado.posicion.x), …)` que revienta con NaN. O sea: protección escrita, probada, en verde, y el fotograma del jugador exactamente igual de frágil que antes. Fix: la comprobación pasa a `_verja()` y la aplican `resolver_eje_x`, `resolver_eje_y`, `resolver_cuestas` y `resolver_repisas`; `resolver_movimiento` la comparte y conserva su salida temprana con `dt <= 0`. `dt` no finito o negativo → `0.0`, sin salir del paso: con `dt` cero no se integra nada, pero la resolución sí corre, y eso es lo que saca a quien ya está incrustado en un tile. Prueba: 8 casos nuevos en `tests/test_resolucion_data_hostil.py`, **rojos con `ValueError: cannot convert float NaN to integer` en las cuatro funciones** → verdes. Riesgo: cuatro `math.isfinite` por paso y fotograma; `test_physics_1000_entities` no se mueve (32,2 ms frente a 34,4 ms de la línea base). |
| AUD-356 | D1 | MEDIA | **CERRADO** | `grade_stage.py --json` y `grade_boss.py --json` imprimían el documento **y detrás el resumen humano**, por la misma salida estándar: `… --json \| jq` falla con *Extra data*, igual que `json.loads`. Las dos órdenes están listadas como gates de CI en `CLAUDE.md` §2 y en `docs/69` §3, y «pasaban» porque lo que se mira es el código de salida. Fix: con `--json`, el resumen va a **stderr** — no se calla, porque calificar a mano las 26 entregas usa esa media. Prueba: `tests/test_los_calificadores_hablan_json.py` (6 casos: parseo, el resumen sigue existiendo, y sin `--json` nada cambia de sitio). |
| GAP-035 | D3 | — | **ABIERTO** | `check_orphan_systems.py` no podía ver lo de AUD-355: exonera un símbolo en cuanto lo referencia otro fichero de producción, y el `__init__.py` del paquete que lo re-exporta cuenta como tal. El arreglo evidente se **midió** antes de descartarlo: no contar los `__init__.py` da 212 → 224 huérfanos, y **once de los doce nuevos son falsos positivos** (estados vivos que sus módulos hermanos instancian con import diferido, `Contacto` como tipo de retorno). Once por uno es ruido, y un guardián ruidoso se desactiva. La regla correcta —«un import no es una llamada»— exige mirar `ast.Call`, o sea reescribir el analizador. |

### Recuento de pruebas

- Línea base, antes de tocar nada: **4.335 passed, 7 skipped**, 489 s.
- Regresión final, con los cuatro arreglos dentro: **4.353 passed, 7 skipped, 0 failed**, 372 s.
- `pytest --collect-only -q`: **4.342** recogidas antes de esta iteración (el README declara 4.301 → 0,9 % de desvío, dentro del 5 % que tolera `test_documentacion_bilingue.py`; con las 18 nuevas sube a 1,3 %, sigue dentro y por eso el README no se toca — lo está editando otra frente).
- Pruebas nuevas de esta iteración: **18** (1 de AUD-353, 3 de AUD-354, 8 de AUD-355, 6 de AUD-356). 4.335 + 18 = 4.353, sin ninguna prueba existente rota.
- Lote dirigido tras los arreglos (`-k "player or fisica or physics or pendiente or cuesta or repisa or colision or collision or stage_scene or app or resolucion"`): **453 passed**, 3.901 deselected, 42,7 s.

### GAPs

- Nuevos: **GAP-034** (la versión de ruff que define «verde» no está fijada; mitigado por AUD-353, causa abierta) y **GAP-035** (punto ciego del detector de huérfanos, con la medición de por qué el arreglo obvio no vale).
- Cerrados: ninguno.

### Dominios de §8

- Cubiertos: **D1** (gates: los doce ejecutados, uno rojo encontrado y cerrado) y **D4** (corrección del código: un defecto de alcance de nombre y otro de *destino* de un arreglo, ambos en código que CI no puede ejecutar). **D3** parcialmente: se auditó la honestidad de los **gates**, no la de la suite.
- Pendientes: D2 (consistencia doc ↔ código, no re-verificada en esta iteración), D5-D9.

### Lo que NO se pudo verificar y por qué

- **La ruta de GPU de verdad.** El arreglo de AUD-354 se verifica con el cableado montado a mano; en esta sesión no se levantó un contexto GL real sobre la Quadro. Un `render()` con overlay sobre hardware sigue sin medirse.
- **Matriz 3.11/3.12/3.13.** Esta máquina sólo tiene 3.14.6. La cadena de fallo de AUD-353 es, además, específica de la versión instalada: lo que aquí sale rojo con ruff 0.15.20 puede salir verde con otra, que es justamente GAP-034.
- **Jugabilidad, mezcla de audio y presentación (D9).** Driver dummy, sin pantalla ni salida de sonido.
- **`mutation_check.py`.** No se ejecutó; la defensa por mutación sigue siendo la medida en la iteración 14.

### Continuación — plan de cierre y lote 1 (mismo día)

Por encargo del dueño, la iteración siguió hacia el **cierre**: reunir todo lo
abierto, medido, y arrancar el plan. Resultado en
`docs/91_PLAN_DE_CIERRE.md` (con fila en el índice maestro): 38 ítems en cinco
bloques (herramientas, documentación, motor, contenido y la última
característica), ocho lotes en orden, y cinco preguntas que sólo puede
responder el dueño. El inventario sale de comandos, no de memoria: cada bloque
lleva el suyo.

| ID | Dominio | Severidad | Estado | Resumen |
|---|---|---|---|---|
| AUD-357 | D3 | MEDIA | **CERRADO** | La suite dejaba **20 `DeprecationWarning` por ejecución** (`pygame.image.tostring`, obsoleta desde pygame 2.3) en `gl_pipeline.py:552` y `bench_sprite_batch.py:166`. Veinte avisos en verde son peores que uno en rojo: un resumen que siempre dice lo mismo enseña a no leerlo, y el aviso número veintiuno pasa entre ellos. `pyproject.toml` exige `pygame-ce>=2.5`, así que `tobytes` existe en toda instalación soportada y no hace falta compatibilidad. Prueba: `tests/test_sin_avisos_de_obsolescencia.py`, roja con las dos llamadas exactas → verde; el guardián mira **llamadas** por AST, no menciones, porque varios docstrings citan `tostring` a propósito contando la medición de AUD-229. Efecto lateral encontrado al verificar: el comentario de AUD-353 contenía la palabra mágica `noqa` en prosa y ruff avisaba de que la frase no era un código de regla — reescrito; el lint queda con **0 avisos**, no sólo con código de salida 0. |
| AUD-358 | E1 | — | **PARCIAL** | `EnvironmentState` (`src/framework/world/environment.py`): el contrato inmutable del ambiente del fotograma, el primer medio del lote 5. Entregado **antes** que `WorldSimulation` a propósito: un contrato escrito después del productor acaba teniendo la forma del productor. 22 pruebas fijan las cuatro propiedades que lo hacen utilizable — es un valor (congelado, comparable, sin pygame), `neutro()` es la identidad (permite conectarlo sin tocar un escenario), lo derivado se deriva una vez (`suelo_mojado`, `factor_friccion`, `es_de_noche`, `luz_lunar`) y está acotado (la tormenta más cerrada deja el juego jugable, misma decisión que `MIN_AMBIENTE` con la noche). El guardián `test_architecture_doc_matches_tree` cazó el paquete a medias en cuanto apareció, que es exactamente su trabajo. |

| AUD-358 | E1 | — | **CERRADO (núcleo)** | `WorldSimulation` (`src/framework/world/simulation.py`): el productor de `EnvironmentState`. Compone reloj, calendario, estación, astronomía y clima en una foto por fotograma. **No reimplementa nada**: `RelojDeMundo` (con su curva de 9 paradas medida en Stage 0) y `Estacion` siguen siendo la fuente de verdad, y la tabla `CLIMAS` deriva la visibilidad del `overlay_alpha` que el sistema de clima ya pintaba, en vez de declarar un número nuevo — un hecho, una fuente. Añade lo que faltaba: calendario por vuelta del reloj, altura solar (armónico), las **cinco bandas del día** (día + los tres crepúsculos + noche, porque un consumidor que sólo distinga día/noche no puede pintar la diferencia entre las 18:20 y las 19:00), fase lunar por periodo sinódico real (29,530588 d, el de verdad: es material del curso) y `forzar()`, la válvula con la que un nivel narrativo rompe el realismo sin dejar el mundo incoherente. 26 pruebas; la que hace conectable el sistema es `test_la_luz_compuesta_es_la_misma_que_calcula_la_escena_hoy`, que replica verbatim la cuenta de `stage_parts/ambiente.py::_aplicar_hora` sobre 7 horas × 4 estaciones: si se pone roja, enchufar la simulación deja de ser una refactorización. Catálogo de fenómenos y prioridades en `docs/92_CATALOGO_DE_FENOMENOS.md`. **Pendiente del lote 5:** el cableado en `ambiente.py` y el hilo de fricción hasta el jugador. |

**Recuento tras la continuación:** **4.377 passed, 7 skipped** (+48 de
AUD-357/358 sin volver a pasar la suite completa: los ficheros nuevos y los
guardianes de documentación y arquitectura sí, en verde). El único fallo
de la pasada completa —`test_stage4_1::test_con_la_vision_puesta_tambien`— es
contaminación de carga y no una regresión: esa ejecución tardó **9.051 s** en
vez de los 372 s habituales (la máquina estaba saturada con otras sesiones) y
el fichero entero pasa en aislado (84 passed, 34 s). Es, de paso, la evidencia
que justifica el ítem **A6** del plan: una prueba de milisegundos que depende
de la carga de la máquina no es un gate fiable.

### Lote de cierre de agosto (2026-08-11) — AUD-407..412

| ID | Dominio | Severidad | Estado | Resumen |
|---|---|---|---|---|
| AUD-407 | D5 | MEDIA | **CERRADO** | El stub de `Mando` de `test_lianas_y_tirolesas.py` no implementaba `pulsada_en_buffer`, y el motor llama a ese método desde la rama de lianas: la prueba de una mecánica completa quedaba roja por el doble de pruebas, no por la mecánica. |
| AUD-408 | D1 | **BLOQUEANTE** | **CERRADO** | La causa abierta de GAP-034 se cierra con la salida que el propio hueco describía: `pyproject.toml` fija `ruff==0.16.1` (la versión que ya corría en el `.venv`). LOG004 se estabilizó en 0.16.0, así que el `# noqa` de `diagnostico.py:86` vuelve a tener la regla que lo justifica y deja de poder caducar por deriva río arriba. Verificado: `ruff check` sobre el alcance del CI en verde, y `test_ruff_esta_limpio_en_el_alcance_del_ci` ejecuta ahora **la versión fijada**. |
| AUD-409 | D7 | MEDIA | **CERRADO** | `docs/04_PLAYER_SPEC.md` seguía citando `_pending_jump`, eliminado en AUD-373: el contrato describía una máquina de estados que ya no existe. Reescrito contra `pulsada_en_buffer`/`consumir_buffer`, y `check_doc_symbols.py --ci` (que impone la cita histórica con resolución) verifica en verde. |
| AUD-410 | D3 | MEDIA | **CERRADO** | El destello del rayo (`weather_system.py`) compraba una superficie nueva en cada fotograma de la tormenta y la liberaba con `surface.fill` al mismo tiempo que la sombreaba, encima de la tabla periódica de `gl_pipeline` que ya cachea sus destellos. Caché perezosa por tamaño (mismo patrón que `_destello_alfa`), medida con una prueba que cuenta superficies vivas. |
| AUD-411 | D2 | MEDIA | **CERRADO** | `audio_manager.crossfade_ambient` capturaba `pygame.error` pero el fallo real de un ambiente ausente llega como `FileNotFoundError` (o `OSError`) desde la carga: un ambiente que faltaba tumbaba el crossfade, y encima se apoderaba de los `assert` del test de stinger colindante en la primera pasada. Catch ampliado a `(pygame.error, FileNotFoundError, OSError)`, con su prueba roja→verde y los asserts devueltos a su test. |
| AUD-412 | D7 | MEDIA | **CERRADO** | El inventario medido (`docs/62`) no tenía guardián y **trece afirmaciones habían envejecido**: 62 tipos cuando el motor acepta 78 (39 integrados + 37 del registro con escenarios + `Solid`/`Platform`), 479→1.100 líneas de `gl_pipeline`, 1.549→1.245 de `stage_scene`, 1.608→4.751 pruebas, la cita a la auditoría 61 (retirada en la purga) y más; mismo trabajo en `docs/63` y `docs/87` y en `README.en.md`. Nuevo `tests/test_el_inventario_cuenta_bien.py` mide las cuentas del cargador (con el desglose 69/71/76/78; el registro base de 69 sólo existe en intérprete limpio, así que sale de un subproceso como en `generate_tmx_reference.py`) y que el inventario no cite a la auditoría retirada. |

**Recuento tras el lote:** **4.753 passed, 3 skipped** en pasada completa
(5:54 en esta máquina, con el fallo de contaminación de carga ausente), sin
regresiones. El aviso único es de pydub (no hay ffmpeg en esta máquina),
preexistente y ajeno a estos cambios. **GAP-034 queda cerrado** con su
`**Resolution:**` en `KNOWN_GAPS.md` (la marca *(Resuelto)* del encabezado
llevaba meses sin resolución escrita, que es el formato que exige
`docs/23_DATA_SCHEMAS.md` §8). Se respetó el árbol en vuelo de la sesión
anterior: `docs/60`, `gpu_effects.py` y `memoria_de_textura.py` (AUD-404)
quedan fuera de estos commits, y `computer-vision-course/` sigue sin trackear.

> **Nota de la sesión paralela (2026-08-11).** Ese trabajo en vuelo acabó
> commiteado como **AUD-413**, no como AUD-404: cuando se cerró, el correlativo
> ya iba por 412, y numerar hacia atrás habría dejado un `AUD-404` posterior a
> un `AUD-412`. El número que citaba el párrafo de arriba era el que llevaban
> los comentarios del árbol sin commitear, no un lote publicado.

---

## Iteración 16 — 2026-08-11 — Lo que sólo se ve corriendo la suite entera

| ID | Dominio | Sev. | Estado | Qué era |
|---|---|---|---|---|
| AUD-413 | D6 | **ALTA** | **CERRADO** | `bytes_de()` (AUD-397) desempaquetaba `textura.size` a pelo y reventaba con el renderer de mentira de `test_aberracion_cromatica`: el `size` de un doble no es un par de enteros. **Nueve pruebas rojas** — la instrumentación de recursos se llevaba por delante justo lo que instrumentaba. Un contador no puede tumbar el fotograma que mide (misma regla que `App` con `medidas_de_depuracion`). En el mismo lote: `publish_color_matrix` (AUD-401) **prometía en su docstring** que un menú no hereda el tinte del nivel anterior y no estaba enganchada ni a `reset()` ni a `begin_frame()` — cuyo propio docstring avisa de esto—; y `docs/60` no documentaba el tipo `Objective` (AUD-400) ni había subido su recuento de 77 a 78 tipos. |
| AUD-414 | D7 | MEDIA | **CERRADO** | Tres afirmaciones de la documentación contradecían al código, verificadas abriendo el fichero: `docs/62` §C1 decía «Nada del motor está atado a la música […] no hay concepto de BPM, compás ni posición de la pista» (falso desde AUD-137: `music_clock.py` son 280 líneas; comprobada fila a fila la tabla, **cinco de seis piezas hechas** y la sexta —pulso visual— realmente ausente, que ahora se dice en vez de esconderse entre cinco falsos); `docs/62` §C1 Audio decía «sin buses de mezcla, sin *ducking*» (los hay desde AUD-144; lo que sí falta es reverberación por zona, y **no por coste**: SDL no tiene efectos en su mezclador); y `docs/87` §27.1 daba *normal mapping* por «Pendiente» mientras §28.1 del **mismo documento** lo daba por hecho (AUD-340). Además `stage1_2_la_soda` declaraba `climate=""`: el motor ya cae a `clear`, así que explicitarlo es cero cambio y un aviso menos (los avisos de TMX bajan de 6 a 4). |
| AUD-415 | D1 | **ALTA** | **CERRADO** | La fixture `_motor` de `test_el_inventario_cuenta_bien` (AUD-412) hacía `clear()` del registro de entidades y reponía el estado **anterior** a su propio `discover_stages()`. Eso no se deshace: los módulos de escenario ya importados no repiten su `register_entity` de nivel de módulo (AUD-144), así que el registro se quedaba en los 30 integrados y perdía los 7 tipos de las entregas. Efecto: `test_guia_del_motor` medía **71 tipos donde el juego ve 78** y fallaba o no según qué otras pruebas hubieran cargado un mapa antes. Un guardián de cifras cuyo resultado depende del orden de ejecución no vigila nada. Se quita el `clear()`; `update()` sin vaciar conserva lo descubierto y repone lo ajeno, que es lo que su docstring ya decía que hacía. Verificado en los dos órdenes. |

**Recuento tras el lote:** **4.730 passed, 7 skipped, 1 failed** en pasada
completa, corrida en ocho trozos. El único fallo es
`test_puertas_de_calidad::test_ruff_esta_limpio_en_el_alcance_del_ci`, y **no
es un defecto**: el `.venv` local tiene `ruff 0.15.20` y el repo pinea
`0.16.1`, donde `LOG004` sí existe y el `noqa` de `diagnostico.py:93` es
correcto. Quitarlo pondría el lint local en verde y **rompería CI** — es
exactamente el ajuste que cerró AUD-408.

**Lo que enseñó esta iteración, y es lo que hay que llevarse.** Los tres lotes
salieron de correr la suite **entera**; los lotes dirigidos de AUD-397, 400 y
401 estaban todos en verde cuando se commitearon. AUD-415 explica por qué:
`test_guia_del_motor` pasaba o fallaba según el conjunto en que se ejecutara,
así que verificarlo en aislado no probaba nada. No era falta de cobertura —la
prueba existía y era correcta—, era un guardián que **se contaminaba a sí
mismo**.

**Y una lección de operación, que costó 3,5 horas.** La suite lanzada en
segundo plano con `| tail -N` **se cuelga**: `tail` no consume hasta el final,
el buffer del pipe se llena y pytest se bloquea escribiendo. Los síntomas
engañan —fichero de salida en 0 bytes, proceso vivo, 326 s de CPU acumulados en
3,5 h de reloj, o sea parado—. Los mismos 133 ficheros pasaron en **4 min 12 s**
partidos en cuartos y corridos en primer plano. No hay `pytest-timeout`
instalado, así que no se puede acotar por prueba: la única defensa es partir y
no canalizar.

---

## Iteración 17 — 2026-08-11 — Las herramientas del estudiante

| ID | Dominio | Sev. | Estado | Qué era |
|---|---|---|---|---|
| AUD-416 | D7 | **ALTA** | **CERRADO** | Las dos herramientas del estudiante no coincidían: `validate_tmx.REQUIRED_MAP_PROPS = [stage_id, stage_name, bgm_track]` frente a `grade_stage.REQUIRED_GRADE_PROPS = [author, stage_id, stage_name]`. **`author` puntúa en la rúbrica y el validador no la pedía**, así que un mapa sin ella salía `[OK]` y perdía 3 de los 10 puntos de metadata sin que nada lo dijera. Es AUD-058 girado: aquella vez el validador aprobaba lo que el *motor* rechazaba; aquí, lo que la *rúbrica* penaliza — que para quien está siendo calificado es lo mismo. Avisa y no suspende (`author` no impide jugar; rechazar un mapa jugable sería AUD-106), y la lista se **importa** de `grade_stage` en vez de copiarse, por lo mismo que AUD-392. |
| AUD-417 | D7 | **ALTA** | **CERRADO** | `stage_template.tmx`, el fichero que copian los veintiséis en la primera clase, sacaba **84/130 = 64,6 %** en la rúbrica del propio curso: sin enemigos, sin coleccionables, sin `climate`, sin `author`, un checkpoint y ningún salto exigente. Regenerado desde cero con `tools/generate_stage_template.py` como **catálogo** —un ejemplar de cada tipo: tres arquetipos de enemigo, coleccionable, luz, mensaje, zona de daño, objetivo, pendientes, plataforma de un sentido— y un hueco de 5 baldosas. Los 80 px están medidos con `JumpEnvelope`: el salto normal cruza 85,5 y lo «cómodo» acaba en 68,4, así que cae en *exigente* y se cruza sin salto aéreo. |

**Lo que corrigió una prueba, y es la parte que importa.** La primera versión de
la plantilla llegó a **130/130** poniendo tres coleccionables y tres puntos de
control, y `test_teaching_tools` saltó: *«stage0 saca 100 % y la plantilla vacía
100 %: la rúbrica no distingue trabajo hecho de trabajo sin hacer»*. Tenía
razón. Se perseguía la nota en vez del objetivo: la plantilla existe para
**demostrar** cada tipo, no para **llenar** la rúbrica. Bajada a un
coleccionable y dos checkpoints queda en **92,3 %**, con `stage0` por encima en
100 % y el margen donde tiene que estar.

El TMX pasa a **generarse**, como `stage_mecanicas` desde AUD-153: un defecto
aquí se multiplica por veintiséis antes de que nadie lo ejecute.
`tests/test_la_plantilla_del_estudiante.py` comprueba que el fichero y su
generador siguen de acuerdo. El validador cazó el primer bug del generador en
la primera ejecución —faltaba la coma al final de cada fila del CSV, 945 tiles
de 960—, que es exactamente para lo que está.

**`stage0` se midió y NO se tocó.** Se planteó regenerarlo también. Medido:
**130/130** en la rúbrica, **18/18** propiedades de mapa, **6/6** propiedades de
`Light`, 27 tipos de objeto distintos y 61 objetos. No hay métrica del
repositorio que pueda mejorar, y a cambio se arriesgaban las **71 pruebas** que
lo citan y la curva de dificultad que AUD-151 calibró. Reescribir lo que ya
está al máximo es trabajo con riesgo alto y ganancia cero — la decisión queda
anotada aquí para que no haya que volver a medirlo.

---

## Iteración 18 - 2026-08-23 - D1/D2/D3 (gates, consistencia, honestidad de las pruebas)

**Commit auditado:** `b4b68b0` (rama `feature/stage4_1-cementerio-sagrado`,
árbol limpio salvo volcados `.txt` sin seguimiento).

### Gates ejecutados

| Gate | Resultado | Nota |
|---|---|---|
| `pytest tests/` | 6.172 recolectadas: **6.149 pasan / 4 fallan / 19 omitidas**, 1.061 s | los 4 fallos se analizan abajo |
| `ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/` | verde | |
| `mypy` (trinquete) | verde, 51 ficheros | |
| `check_dependency_sync.py` | verde, 13 dependencias de acuerdo | |
| `check_translations.py --ci` | verde (44 entradas es / 87 en) | |
| `check_tmx_coverage.py --ci` | verde; referencia stage0 al 100 % | reporta `ArenaZone` y `BossSpawn` sin mapa, con salida informativa |
| `generate_tmx_reference.py --check` | verde (`STAGE_CREATION.md` al día) | |
| `validate_assets.py` | verde, 0 errores | |
| `validate_tmx.py --ci` | 22/22 pasan, aviso en `stage1_1` (especies registradas dentro de función; AUD-591 dejó trinquete repo-wide, el aviso persiste por diseño) | |
| `grade_stage.py assets/maps/ --json` | 21 mapas, media **78,9 %** | |
| `grade_boss.py ... --json` | **100 %** | |

### Hallazgos

| ID | Dominio | Sev. | Estado | Qué era |
|---|---|---|---|---|
| AUD-611 | D2 | BLOQUEANTE | **CERRADO** | `inventory.py` traía `id="sunk_crown"` dentro de la clave `"sunken_crown"`: arrastre del commit e482f29 (AUD-608/609), cuyo diff además borró comentarios decorativos. La clave, el recogible de `stage0` y cuatro documentos dicen `sunken_crown`; `restaurar()` descarta ids no reconocidos, así que el id falso era una corona que desaparecería al cargar. Restaurado el id; roja: `test_el_catalogo_esta_en_espanol::test_los_identificadores_no_se_traducen`; verdes: ese fichero más `test_aud_559` y `test_el_inventario_cuenta_bien` (51 pasan). |
| AUD-612 | D2 | BLOQUEANTE | **CERRADO** | AUD-605/606 añadió `ArenaZone` al cargador y quedó huérfana: ningún TMX la coloca y `SIN_MAPA_A_PROPOSITO` (`test_todos_los_tipos_se_usan.py`) no la justificaba, así que el trinquete de AUD-153 se puso rojo con cada suite completa. Mismo tratamiento que `BossSpawn`: justificación escrita (los cuatro mapas de jefe usan su tipo directo o retiraron el marcador a propósito; el laboratorio no tiene jefe), ejercicio punta a punta en `test_lo_reportado_por_el_playtesting.py`. No va en `ALTERNATIVAS` del script de cobertura: ahí sólo caben grafías alternativas de otro tipo, y `ArenaZone` es un tipo real sin mapa por decisión. |
| AUD-613 | D3 | ALTA | **CERRADO** | `test_con_canal_libre_si_queda_activo` dependía de que el mezclador global tuviera un canal libre: otra prueba con un ambiente en bucle sin parar agotaba los canales y en suite completa `find_channel()` devolvía `None` → `_ambient_active False` → roja intermitente (pasaba en aislamiento). El canal libre se declara ahora igual que su gemelo declara `None`: `Channel(0)` parado e inyectado vía `monkeypatch`. La prueba mide la honestidad de `_ambient_active`, no los canales heredados. |
| AUD-614 | D2 | BAJA | **CERRADO** | `CLAUDE.md` decía «el último usado va por AUD-335»: trescientos números por detrás de la realidad y podrido por construcción. Retirado el número duro; queda la orden que siempre fue la fuente de verdad (`git log --oneline -1`). |

### Lo que NO se pudo verificar

- El cuarto fallo de la primera corrida,
  `test_rutas_de_los_documentos[94_CIERRE_DE_GAPS_Y_PLAN_POR_FASES.md]`,
  pasó en aislamiento y las once rutas que cita el doc 94 existen.
- La re-corrida de regresión trajo **7 fallos distintos** que en aislamiento
  pasan (83/84 al releerlos juntos), y la causa quedó identificada con
  evidencia de sistema de ficheros: **hay un proceso de desarrollo concurrente
  sobre este mismo árbol**. Entre las dos corridas apareció un módulo nuevo
  `text_panel.py` bajo `engine/ui/` (creado 21:17, modificado 21:37) y una
  prueba nueva de «cuadros», ambos sin seguimiento, junto con cambios en
  `message_box.py`, `theme.py` y el sistema de diálogos — ninguno de esta
  auditoría. (Las rutas van a medias a propósito: citarlas completas pondría
  este informe a merced del frente ajeno que las está moviendo.) Los síntomas
  cuadran: el parpadeo inicial (pytest recolectó 0 pruebas; minutos después,
  374 ficheros), el `test_ruff_esta_limpio` interno en rojo mientras el ruff
  externo pasa, y el árbol de `03_ARCHITECTURE.md` que aún no menciona el
  módulo nuevo del otro frente de trabajo. Ese último es deuda del lote
  concurrente, no de éste: añadir aquí a mano el árbol del módulo ajeno
  pisaría cómo decida documentarlo quien lo está escribiendo.
- Estado honesto de cierre: los cuatro hallazgos AUD-611…AUD-614 están
  corregidos con sus verdes pegados, y los tres defectos deterministas de la
  primera corrida no reaparecen en la segunda. Lo que queda en rojo pertenece
  al frente concurrente y se re-verificará cuando ese árbol se estabilice.


