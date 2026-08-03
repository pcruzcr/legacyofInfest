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
| AUD-168 | MEDIA | `docs/00_SYLLABUS_ALIGNMENT_AUDIT.md`, `10_LIBRARIES_AND_DEPENDENCIES.md`, `20_ASSET_BIBLE.md` | los tres mandan ejecutar `validate_assets.py` desde `tools/`; el script vive en `scripts/` | **Corregido** |
| AUD-168 | MEDIA | `CONTRIBUTING.md` | «369 tests» (hay 2.142 funciones definidas); «Branch from `main`» (las ramas son `prod`/`pprod`/`dev`); `ruff check src/` y `mypy src/` en vez de los alcances reales del CI; sección *New Enemy* que ignora la decisión AUD-046 | **Corregido** |
| AUD-168 | MEDIA | `docs/24_TEST_PLAN.md` §12.1 y árboles | declara fixtures `reference_sprite_32x32.png` y `sample_dataset_tiny.npz` que no existen; las entradas se generan en `conftest.py` | **Corregido** |
| AUD-168 | BAJA | `docs/17_BOSS_SPEC.md` | ruta `src/stages/boss_gavilan/` → real `src/stages/stage3_4_boss_gavilan/` | **Corregido** |
| AUD-168 | BAJA | `KNOWN_GAPS.md` GAP | `game_context.py` situado en `framework/core/` → vive en `src/engine/core/game_context.py` | **Corregido** |
| AUD-168 | BAJA | `docs/30_TICKET_BACKLOG.md`, `50_IMPROVEMENT_ROADMAP.md` | tickets y tabla de migración apuntando a los dos módulos retirados, y un ejemplo que carga `stage0.tmx` desde `assets/maps/` sin su directorio | **Corregido** |
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
FAIL  00_SYLLABUS_ALIGNMENT_AUDIT.md: ['tools/validate_assets.py']
FAIL  10_LIBRARIES_AND_DEPENDENCIES.md: ['tools/validate_assets.py']
FAIL  17_BOSS_SPEC.md: ['src/stages/boss_gavilan/boss_gavilan.py']
FAIL  20_ASSET_BIBLE.md: ['tools/validate_assets.py']
FAIL  22_API_CONTRACTS.md: ['src/engine/scene/transitions.py', 'src/engine/utils/spritesheet.py']
FAIL  24_TEST_PLAN.md: ['tests/fixtures/reference_sprite_32x32.png']
FAIL  30_TICKET_BACKLOG.md: ['src/engine/scene/transitions.py', 'src/engine/utils/spritesheet.py', 'src/stages/stage0/stage0.tmx']
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
**Informe completo:** `docs/71_REVISION_DE_JUEGO.md` — aquí sólo va el resumen
y la evidencia de la corrección.

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
