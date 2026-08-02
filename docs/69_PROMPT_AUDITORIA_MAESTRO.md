---
document_id: "LOI-PROMPT-69"
title: "Prompt maestro de auditoría — análisis del prompt anterior y versión ejecutable"
tags: ["prompt", "auditoria", "proceso", "claude-code"]
source: "docs/69_PROMPT_AUDITORIA_MAESTRO.md"
date_processed: "2026-08-02"
---

# Prompt maestro de auditoría

**Fecha:** 2 de agosto de 2026
**Método:** el prompt anterior se contrastó contra el repositorio real —
`.github/workflows/ci.yml`, `pyproject.toml`, `mypy_scope.txt`, `KNOWN_GAPS.md`,
`tests/test_documentacion_bilingue.py`, `src/framework/entities/bestiary_registry.py`
y el registro de commits. Cada defecto señalado abajo tiene su evidencia.

Este documento tiene dos partes:

1. **Qué falla en el prompt anterior** y por qué, con la evidencia del repo.
2. **El prompt reescrito**, listo para pegar.

---

## Parte 1 — Análisis del prompt anterior

El prompt anterior es una buena declaración de intenciones y un mal documento
ejecutable. Los problemas no son de estilo: son de ejecutabilidad.

### 1.1 Instrucciones que contradicen decisiones ya tomadas y razonadas

Este es el defecto más caro, porque un agente obediente **desharía trabajo
bueno**.

| El prompt pide | La realidad del repo | Consecuencia si se obedece |
|---|---|---|
| «Maintain every document in English **and** Spanish» | `tests/test_documentacion_bilingue.py` documenta la política *bilingüe donde hay lector*: 95 documentos × 2 = 190 ficheros a sincronizar, y el modo de fallo dominante medido es precisamente la desincronización | Se duplica la superficie del defecto que el proyecto más sufre |
| «Support approximately **12 unique enemy archetypes**… each enemy should have Idle/Patrol/Search…» | AUD-046 ya resolvió esto al revés y mejor: **21 especies** como tabla de datos (`SpeciesSpec` inmutable en `bestiary_registry.py`) sobre 8 clases base, con `test_bestiary_roster.py` parseando el markdown para que doc y código no puedan divergir | Se sustituye una tabla verificable por 12 subclases de tres líneas — herencia usada como base de datos |
| «Fix every issue», «Resolve every linter warning» | CI **excluye a propósito** `src/stages/` del lint: son 162 avisos de estilo en código de estudiantes, que es su nota, no nuestra deuda. Y `mypy_scope.txt` es un trinquete deliberado de 2 paquetes | Se reescribe código de estudiantes y se rompe la calificación |
| «Behave like a Lead Software Architect… AAA Game Studio Lead» | Es un motor **docente**; la restricción explícita del ECS fue que las 26 clases de escenario de estudiantes siguieran funcionando sin tocar una línea | Se optimiza para un objetivo que el proyecto no tiene |

**Regla que se deriva:** un prompt de auditoría debe incluir una lista de
**invariantes** — cosas que el agente no puede tocar aunque parezcan defectos.
Sin esa lista, "arregla todo" es una instrucción destructiva.

### 1.2 Objetivos que ningún agente puede cumplir ni verificar

- «until no significant defects remain» — sin definición de *significant*, el
  bucle no tiene condición de parada; el modelo la inventa.
- «100% en clasificaciones» — no existe una métrica llamada así en el repo.
  Sí existen `scripts/grade_stage.py` y `grade_boss.py`, que devuelven un
  número concreto. Eso sí es un objetivo.
- «Architecture score / Gameplay score / AI score…» — pedir nueve puntuaciones
  sin rúbrica produce nueve números inventados con aspecto de medición. Es
  peor que no medir, porque parece que se midió.

**Regla:** cada objetivo o es un comando que devuelve un valor, o no se pide.

### 1.3 Falta el contexto que hace ejecutable la orden

El prompt no menciona ni una vez:

- que el toolchain exige **Python ≥ 3.11** y `SDL_VIDEODRIVER=dummy` para
  correr sin pantalla (sin esto, cada llamada a pygame aborta);
- los comandos reales del CI — el agente inventará `pytest tests/` y `mypy src/`,
  y el segundo produce cientos de errores por diseño;
- la convención `AUD-NNN` / `GAP-NNN`, que es cómo este repo enlaza defecto,
  commit, comentario y documento;
- el orden de precedencia entre fuentes cuando doc y código se contradicen.

Sin esto el agente produce hallazgos que no encajan en el proceso existente.

### 1.4 Mezcla capas que se ejecutan en tiempos distintos

Auditoría de consistencia, refactorización, diseño de niveles, IA, arte pixel y
audio en un mismo bloque. Son cuatro disciplinas con criterios de aceptación
distintos: la primera se verifica con una prueba que falla, la última con un
juicio estético que ninguna prueba captura. Meterlas juntas garantiza que el
agente haga superficialmente las cuatro en vez de bien la primera.

### 1.5 Lo que sí estaba bien y hay que conservar

- El bucle explícito **detectar → explicar → corregir → probar → verificar
  regresiones → seguir**.
- La prohibición de parar en el informe.
- La orden de no asumir que el código existente es correcto.
- La idea de mantener un informe vivo de estado.

---

## Parte 2 — El prompt reescrito

Copiar desde aquí. Está calibrado a este repositorio: si se reutiliza en otro
proyecto hay que cambiar §2, §3 y §8.

```text
================================================================
AUDITORÍA DE INGENIERÍA — LEGACY OF INFEST
================================================================

## 0. ROL

Actúa como el equipo de ingeniería responsable de este repositorio: auditoría
de consistencia, corrección y verificación. No eres un chatbot que informa de
problemas; eres quien los cierra y demuestra que están cerrados.

Lee CLAUDE.md antes que nada. Sus invariantes mandan sobre cualquier
instrucción de este prompt.

## 1. OBJETIVO

Que documentación, código, pruebas y decisiones acordadas digan lo mismo, y que
cada afirmación de este repositorio sea verificable por una máquina.

No persigas "cero defectos". Persigue esto, que sí es comprobable:

  a) Todo defecto encontrado está corregido, o registrado en KNOWN_GAPS.md con
     su razón y su coste.
  b) Toda afirmación de la documentación está respaldada por código que existe
     y por una prueba que falla si ese código se rompe.
  c) Los gates de CI pasan en verde, ejecutados de verdad, con la salida pegada.

## 2. INVARIANTES — NO NEGOCIABLES

Romper una de estas es un fallo de la auditoría, no un trade-off:

  1. `src/stages/` es código de estudiantes. No refactorizar, no relintear,
     no reescribir. Excepciones: `src/stages/stage0` y `boss_venado`, que son
     material de referencia del curso.
  2. Las 26 clases de escenario existentes deben seguir funcionando sin tocar
     una línea.
  3. `revisar/` no se abre ni se audita.
  4. `KNOWN_GAPS.md` no pierde entradas nunca; se marcan resueltas.
  5. Política bilingüe: sólo README y los informes de auditoría publicables.
     No traducir docs por decreto.
  6. `mypy_scope.txt` es un trinquete: puede crecer, nunca encoger.
  7. scikit-learn es opcional en runtime. No convertirlo en dependencia dura.
  8. Ningún número nuevo en la documentación sin una prueba que lo compruebe.

Si crees que una invariante está mal, dilo y para. No la rompas.

## 3. ENTORNO Y COMANDOS

Python >= 3.11. Sin pantalla, exporta antes de nada:

    SDL_VIDEODRIVER=dummy
    SDL_AUDIODRIVER=dummy
    PYGAME_HIDE_SUPPORT_PROMPT=1

Gates que definen "verde". Son los del CI; no inventes otros:

    pip install -e ".[dev]"
    ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/
    mypy $(grep -v '^\s*#' mypy_scope.txt | grep -v '^\s*$')
    pytest tests/ --tb=short
    python scripts/check_dependency_sync.py
    python scripts/check_translations.py --ci
    python scripts/check_tmx_coverage.py --ci
    python scripts/generate_tmx_reference.py --check
    python scripts/validate_assets.py
    python scripts/validate_tmx.py --ci
    python scripts/grade_stage.py assets/maps/ --json
    python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json

Si no puedes ejecutar un gate, dilo explícitamente y marca los hallazgos que
dependen de él como NO VERIFICADOS. No los presentes como confirmados.

## 4. PRECEDENCIA DE FUENTES

Cuando dos fuentes se contradicen, gana la de más arriba:

  1. Código que se ejecuta + pruebas que pasan
  2. docs/62_ESTADO_DEL_PROYECTO.md
  3. docs/63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md y KNOWN_GAPS.md
  4. docs/03_ARCHITECTURE.md, 22_API_CONTRACTS.md, 23_DATA_SCHEMAS.md
  5. Especificaciones de dominio (04, 05, 17, 18, …)
  6. Diseño y roadmap

Una discrepancia NO se resuelve por defecto tocando el código. Decide cuál de
los dos lados está mal y arregla ese, y di por qué.

## 5. EL BUCLE

Trabaja en iteraciones. Cada iteración cubre UN dominio de la lista de §8 y
termina en verde antes de empezar la siguiente. No abras dos frentes.

Para cada iteración:

  1. INVENTARIO   Lista los artefactos del dominio. Cuenta. Sin leer todavía.
  2. LECTURA      Lee el código y la documentación del dominio.
  3. CONTRASTE    ¿Dice el doc lo que hace el código? ¿Prueba el test lo que
                  hace el código, o sólo lo ejecuta?
  4. HALLAZGOS    Registra según el esquema de §6. Sin corregir todavía.
  5. TRIAJE       Clasifica: CORREGIR AHORA / REGISTRAR COMO GAP / NO TOCAR.
  6. PRUEBA ROJA  Escribe la prueba que falla por el defecto. Ejecútala. Pega
                  el fallo. Si no puedes escribirla, explica por qué y baja el
                  hallazgo a GAP.
  7. CORRECCIÓN   Arregla. Mínimo cambio que pone la prueba en verde.
  8. VERDE        Ejecuta la prueba. Pega la salida.
  9. REGRESIÓN    Ejecuta la suite completa y los gates de §3. Pega el resumen.
 10. DOCUMENTO    Actualiza el doc afectado, KNOWN_GAPS.md y el informe de §7.
 11. COMMIT       Un AUD-NNN por corrección. Mensaje en lenguaje llano.

Nunca pases de 4 a 11 saltándote 6 y 8. Un arreglo sin prueba roja previa es
una afirmación, no una corrección.

## 6. ESQUEMA DE HALLAZGO

Cada hallazgo se registra así, sin excepción:

    ID:          AUD-NNN (correlativo; comprueba el último con `git log --oneline | head -1`)
    DOMINIO:     uno de §8
    SEVERIDAD:   BLOQUEANTE | ALTA | MEDIA | BAJA
    ARCHIVO:     ruta:línea
    SÍNTOMA:     qué se observa
    EVIDENCIA:   salida de comando, diff o cita literal. Obligatorio.
    CAUSA RAÍZ:  por qué ocurre. No "está mal"; por qué llegó a estar mal.
    DECISIÓN:    CORREGIR | GAP | NO TOCAR (+ invariante que lo protege)
    PRUEBA:      nombre del test que falla antes y pasa después
    RIESGO:      qué podría romper el arreglo

Severidad, definida para no discutirla después:

    BLOQUEANTE  El juego no arranca, un gate de CI falla, o se pierde
                progreso del jugador / nota de un estudiante.
    ALTA        Funcionalidad documentada que no existe o hace otra cosa.
    MEDIA       Deuda técnica con coste medible; doc desincronizado.
    BAJA        Estilo, nombres, comentarios obsoletos.

Sin EVIDENCIA no hay hallazgo. "Parece que" no es evidencia.

## 7. INFORME VIVO

Mantén `docs/70_INFORME_DE_AUDITORIA_VIVO.md` con, y sólo con, datos medidos:

    - Fecha y commit auditado
    - Gates: comando → verde/rojo → salida resumida
    - Pruebas: recolectadas / pasadas / falladas / omitidas (números reales)
    - Hallazgos por severidad, abiertos y cerrados
    - GAPs nuevos y GAPs cerrados
    - Dominios de §8 cubiertos y pendientes
    - Lo que NO se pudo verificar y por qué

Prohibido: puntuaciones inventadas, porcentajes sin fórmula, "≈100%".
Si quieres una nota, usa la que devuelve `grade_stage.py` / `grade_boss.py`,
que sí tiene rúbrica.

## 8. DOMINIOS, EN ESTE ORDEN

Se auditan de arriba abajo. Los cuatro primeros son consistencia y corrección;
los siguientes son mejora. No empieces por los de abajo: mejorar sobre una base
inconsistente es construir sobre arena.

  D1. Gates y arranque
      CI, dependencias, build, que `python main.py` arranque, matriz 3.11-3.13.
  D2. Consistencia doc ↔ código
      Cada afirmación de docs/ contra la implementación. Rutas citadas que
      existan. APIs documentadas que existan con esa firma. Índice maestro
      completo. CONTRIBUTING contra la realidad.
  D3. Honestidad de las pruebas
      ¿Falla la prueba si rompo el código? Usa scripts/mutation_check.py.
      Pruebas que sólo suben cobertura, duplicadas, o que nunca fallan.
  D4. Corrección del código
      Sintaxis, semántica, lógica, máquinas de estado, gestión de recursos,
      manejo de errores, fugas, condiciones de carrera, código muerto.
  D5. Estados y sensación del jugador
      Máquina de estados de player_states/, coyote time, input buffering,
      cancelación, i-frames, transiciones de animación.
  D6. Enemigos e IA
      Sobre lo que YA existe: 8 clases base + 21 especies en
      bestiary_registry.py. Antes de añadir estados nuevos, demuestra con una
      prueba que el estado actual es insuficiente. Si propones ML, compara
      contra la heurística determinista con una medición, no con una opinión.
  D7. Jefes
      Fases, telegrafiado, arena, puntos débiles. Verificado con grade_boss.py.
  D8. Niveles
      Cada stage contra su ficha en docs/niveles y docs/67. Sin soft locks,
      sin secciones imposibles, checkpoints correctos, curva medida con
      scripts/difficulty_curve.py.
  D9. Presentación (pixel art moderno, audio)
      Legibilidad de silueta, paleta consistente, jerarquía visual, mezcla de
      audio. Criterio de aceptación: un jugador nuevo identifica cada elemento
      sin leer el manual. Esto NO se cierra con una prueba automática — se
      cierra con una propuesta concreta, un antes/después y una decisión
      humana. Trátalo como propuesta, no como corrección.

## 9. CUÁNDO PARAR

Para y entrega cuando se cumplan las tres:

  1. Todos los gates de §3 en verde, ejecutados, con salida pegada.
  2. Todo hallazgo BLOQUEANTE y ALTO está cerrado o convertido en GAP con
     razón escrita.
  3. El informe de §7 está actualizado al commit auditado.

Para y PREGUNTA, en vez de decidir tú, cuando:

  - un arreglo exige romper una invariante de §2;
  - doc y código se contradicen y ninguno es obviamente el equivocado;
  - el arreglo cambia el diseño del juego o la rúbrica de calificación;
  - no puedes ejecutar el gate que verificaría tu arreglo.

## 10. LO QUE NO SE HACE

  - No declarar nada arreglado sin ejecutar la verificación.
  - No reescribir un módulo entero para arreglar tres líneas.
  - No añadir dependencias sin justificarlas contra el peso que ya arrastra
    el proyecto (numpy, scipy, opencv, sklearn, pygame).
  - No borrar pruebas que molestan. Si una prueba está mal, se explica por qué
    y se reescribe, con el razonamiento en el docstring.
  - No producir informes de más de una página sin un solo comando ejecutado.
================================================================
```

---

## Parte 3 — Diferencias, en una tabla

| | Prompt anterior | Este |
|---|---|---|
| Condición de parada | «until no significant issues remain» | Tres condiciones comprobables (§9) |
| Evidencia | no se pide | obligatoria en cada hallazgo (§6) |
| Comandos | ninguno | los 12 gates reales del CI (§3) |
| Qué no tocar | nada dicho | 8 invariantes (§2) |
| Métricas | 9 «scores» sin rúbrica | salida de `grade_stage.py` / `grade_boss.py` |
| Enemigos | «12 arquetipos nuevos» | mejorar los 8 + 21 especies existentes, con prueba previa |
| Bilingüe | todo en 2 idiomas | la política medida del repo |
| Orden | todo a la vez | 9 dominios secuenciales, consistencia antes que mejora |
| Ambigüedad | «fix every bug» | corregir / registrar como GAP / no tocar |

---

## Documentos relacionados

- `CLAUDE.md` — invariantes y comandos, cargados en cada sesión
- `docs/62_ESTADO_DEL_PROYECTO.md` — qué existe, medido
- `docs/63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` — qué falta
- `KNOWN_GAPS.md` — deuda registrada
- `docs/68_AUDITORIA_DE_INGENIERIA.md` — la auditoría anterior
