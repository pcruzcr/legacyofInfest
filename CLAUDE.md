# CLAUDE.md — reglas permanentes del repositorio

Este archivo lo carga Claude Code al empezar cada sesión. No es un prompt de
tarea: es lo que hay que saber **antes** de tocar nada. El prompt de trabajo
vive en `docs/69_PROMPT_AUDITORIA_MAESTRO.md`.

---

## 1. Qué es este proyecto

**Legacy of InFest** es un motor de videojuego 2D en Python + pygame-ce que
además es **material docente** de un curso de Gráficas por Computadora,
Procesamiento de Imágenes, Visión por Computadora y Reconocimiento de Patrones.

Esa doble naturaleza manda sobre cualquier decisión técnica:

| Es | No es |
|---|---|
| Un motor educativo con laboratorios por unidad | Un motor AAA comercial |
| Un repositorio del que copian ~26 entregas de estudiantes | Un repo con un solo autor |
| Un proyecto donde el doc es contrato verificable | Un proyecto donde el doc es aspiracional |

Si una mejora técnica rompe una entrega de estudiante o una demo de clase,
**la mejora está mal**, por buena que sea la ingeniería.

---

## 2. Comandos reales

El toolchain vive en el `.venv` de Windows del repositorio. Estos son los
comandos que **de verdad** ejecuta CI (`.github/workflows/ci.yml`); no inventes
otros.

```powershell
# Instalación completa (la única recomendada)
pip install -e ".[dev]"

# Pruebas
pytest                                   # suite completa
pytest tests/test_player_physics.py -v   # un archivo
pytest tests/ -k "collision"             # por patrón

# Lint — ruff es el ÚNICO linter que bloquea un merge
ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/

# Tipos — sólo el alcance del trinquete, nunca src/ entero
mypy $(grep -v '^\s*#' mypy_scope.txt | grep -v '^\s*$')

# Validadores que CI corre y que fallan de verdad
python scripts/check_dependency_sync.py
python scripts/check_translations.py --ci
python scripts/check_tmx_coverage.py --ci
python scripts/generate_tmx_reference.py --check
python scripts/validate_assets.py
python scripts/validate_tmx.py --ci
python scripts/grade_stage.py assets/maps/ --json
python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json
```

Variables de entorno obligatorias en cualquier entorno sin pantalla:

```
SDL_VIDEODRIVER=dummy
SDL_AUDIODRIVER=dummy
PYGAME_HIDE_SUPPORT_PROMPT=1
```

**GPU: se mide siempre con la tarjeta NVIDIA (Quadro M2200).** Windows elige
la tarjeta por aplicación, no SDL ni ModernGL; `python.exe` ya está dado de
alta para la Quadro, y `GLRenderer` y `scripts/bench_sprite_batch.py` avisan
en voz alta si el renderer no es NVIDIA (`GL_RENDERER`). Si un aviso aparece,
asignar `python.exe` a la Quadro (Panel de control de NVIDIA → Configuración
de programa, o Windows → Pantalla → Gráficos → Alto rendimiento) y re-medir;
una medición de GPU tomada en la integrada no vale como referencia.

**Python >= 3.11.** CI corre la matriz 3.11 / 3.12 / 3.13.

---

## 3. Invariantes — romper cualquiera de estas es un fallo, no un trade-off

> **ANULACIÓN PARCIAL POR DECISIÓN DEL DUEÑO (2026-08-07, reversible).**
> Las invariantes 1 y 2 — `src/stages/` intocable y las 26 clases de
> escenario funcionando sin tocar una línea — quedan **suspendidas**: el
> motor y el framework evolucionan libres para servir contextos y modos de
> juego distintos, aunque eso rompa entregas existentes, y el contenido
> (niveles y jefes de referencia) se reconstruirá después para lucir las
> características nuevas. Véase `docs/87_REPORTE_DE_LO_QUE_FALTA.md` §27
> (el plan completo) y la fila AUD-333. La regla de `revisar/` (invariante
> 3) NO está anulada. Si esta anulación se revierte, las invariantes 1 y 2
> vuelven a su redacción original.

1. **`src/stages/` es código de estudiantes.** No se refactoriza, no se
   relintea, no se "moderniza". Está fuera del alcance de ruff (salvo
   `stage0`), fuera de mypy y fuera de cualquier reescritura. Se califica con
   la rúbrica, no con el linter. Excepción: `src/stages/stage0` y los jefes de
   referencia (`boss_venado`), que son el material que los estudiantes copian.
   *(SUSPENDIDA 2026-08-07 — ver nota de arriba.)*
2. **Las 26 clases de escenario existentes deben seguir funcionando sin tocar
   una línea.** Fue la restricción explícita del ECS y sigue vigente.
   *(SUSPENDIDA 2026-08-07 — ver nota de arriba.)*
3. **`revisar/` son entregas de estudiantes.** No se abre, no se modifica, no
   se audita como si fuera código del motor.
4. **`KNOWN_GAPS.md` no se borra nunca.** Una entrada resuelta se marca
   `~~[GAP-NNN] ...~~ *(Resuelto)*` y se le añade `**Resolution:**`. Formato en
   `docs/23_DATA_SCHEMAS.md` §8.
5. **La política bilingüe es "bilingüe donde hay lector", no por decreto.**
   Obligatorio en dos idiomas: `README.md`/`README.en.md` y los informes de
   auditoría publicables. El material de curso va en español. Traducir los 67
   documentos duplicaría la superficie de desincronización — la decisión está
   razonada en `tests/test_documentacion_bilingue.py`.
6. **Los números en la documentación son verificables o no se escriben.**
   El recuento de pruebas del README lo comprueba una prueba. Si cambias la
   suite, actualiza el número.
7. **scikit-learn es opcional en runtime.** Sin él la IA cae a heurística
   determinista. No lo conviertas en dependencia dura ni metas ML donde una
   máquina de estados determinista rinde igual o mejor.
8. **`.flake8` refleja a ruff, no compite con él.** Las reglas se cambian en
   `pyproject.toml`.

---

## 4. Convenciones

**Identificadores de hallazgo.** Todo defecto encontrado y corregido lleva un
`AUD-NNN` correlativo (el último usado va por AUD-335; compruébalo con
`git log --oneline -1` antes de asignar uno). Se cita en:
el mensaje de commit, el comentario del código que explica *por qué* existe el
arreglo, y el documento de auditoría correspondiente. Los huecos conocidos y no
resueltos van como `GAP-NNN` en `KNOWN_GAPS.md`.

**Mensajes de commit.** `AUD-NNN: qué se arregló, en lenguaje llano`.
Ejemplo real: `AUD-156: cargar una partida devolvía al principio del nivel`.

**Comentarios.** Este repo documenta el *porqué*, no el *qué*. Un comentario
que repite el código sobra; un comentario que explica qué falló y por qué la
solución es esa, se queda. Sigue ese registro.

**Ramas.** `prod`, `pprod`, `dev`. No existe `main` — `CONTRIBUTING.md` ya lo
dice así desde AUD-168.

**Documentos.** Numerados `NN_NOMBRE.md` en `docs/`, indexados en la tabla
autoritativa de `docs/00_MASTER_INDEX.md`. Un documento nuevo sin fila en el
índice está mal puesto.

---

## 5. Fuentes de verdad, por orden de precedencia

Cuando dos fuentes se contradicen, gana la de más arriba:

1. **El código y las pruebas que pasan.** Es lo único que se ejecuta.
2. `docs/62_ESTADO_DEL_PROYECTO.md` — inventario medido de qué existe.
3. `docs/63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` y `KNOWN_GAPS.md` — qué falta.
4. `docs/03_ARCHITECTURE.md`, `22_API_CONTRACTS.md`, `23_DATA_SCHEMAS.md`.
5. Especificaciones de dominio (`04_PLAYER_SPEC`, `05_ENEMY_SPEC`,
   `17_BOSS_SPEC`, `18_ENEMY_ROSTER`…).
6. Documentos de diseño y roadmap.

Si el código contradice a un documento, **el resultado no es "arreglar el
código"** por defecto: es decidir cuál de los dos está mal, y arreglar ese.

---

## 6. Cómo se trabaja aquí

- **Nada se declara arreglado sin evidencia ejecutada.** Salida de comando
  pegada, o no cuenta.
- **Ningún cambio sin prueba que falle antes y pase después.** Si no se puede
  escribir esa prueba, se dice por qué.
- **Una prueba que nunca falla no es una prueba.** `scripts/mutation_check.py`
  existe justamente para eso.
- **Lotes pequeños.** Un `AUD-NNN` por commit, verificable por separado.
- **Si falta contexto, se pregunta.** Este repo tiene decisiones deliberadas
  que parecen defectos desde fuera (el trinquete de mypy, el lint parcial de
  `src/stages`, la política bilingüe). Antes de "corregir" una de ellas, lee el
  comentario que la explica.
