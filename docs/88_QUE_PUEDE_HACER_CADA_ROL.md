---
document_id: "LOI-ROLES-88"
title: "Qué es este proyecto y qué puede hacer cada quien con él"
tags: ["entrada", "roles", "curso", "guia"]
description: "Mapa de entrada por rol: profesor, estudiante, programador, diseñador de juego y diseñador de niveles"
source: "docs/88_QUE_PUEDE_HACER_CADA_ROL.md"
date_processed: "2026-08-06"
---

# Qué es este proyecto y qué puede hacer cada quien con él

**Fecha:** 6 de agosto de 2026
**Qué es esto:** la puerta de entrada. No explica nada dos veces — cada sección
dice qué puedes hacer, con qué comando, y a qué documento ir. Las cifras están
medidas hoy, no copiadas.

---

## 1. Qué es

**Legacy of InFest es un motor de videojuego 2D en Python + pygame-ce que además
es el material de un curso.** Las dos cosas a la vez, y ése es el punto: no es un
motor con ejercicios pegados encima, es un juego real cuyo código *es* el
temario de Gráficas por Computadora, Procesamiento de Imágenes, Visión por
Computadora y Reconocimiento de Patrones.

Cuando un estudiante escribe el vuelo de un enemigo está haciendo álgebra de
vectores; cuando ajusta un filtro está haciendo convolución. Los módulos llevan
escrito a qué unidad pertenecen.

Lo que hay dentro, contado el 6 de agosto de 2026:

| | |
|---|---|
| Escenarios jugables | **16** mapas TMX |
| Especies de enemigo | **21**, como tabla de datos y no como 21 clases |
| Jefes de referencia | **3** (`boss_venado`, `boss_rey`, `boss_paburu`) |
| Tipos de objeto colocables desde Tiled | **70** |
| Pruebas automatizadas | **4.051** |
| Documentación | 96 documentos en `docs/` |
| Python | 3.11+ (CI en 3.11, 3.12 y 3.13) |

### Qué NO es

* **No es un motor AAA.** Si una mejora técnica rompe una entrega de estudiante o
  una demo de clase, la mejora está mal por buena que sea la ingeniería.
* **No es un repositorio de un solo autor.** Hay entregas de estudiantes dentro
  y no se tocan.
* **No es un proyecto donde el documento sea aspiracional.** Aquí un número
  escrito es un número medido, o no se escribe.

---

## 2. Profesor

**Puedes dar el curso completo sin preparar material desde cero, y calificar con
un comando en vez de a ojo.**

| Quiero… | Comando |
|---|---|
| Calificar el nivel de un estudiante | `python scripts/grade_stage.py assets/maps/ --json` |
| Calificar un jefe | `python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json` |
| Generar un examen del banco | `python scripts/generate_exam.py` |
| Exportar notas | `python scripts/grade_exporter.py` |
| Producir retroalimentación escrita | `python scripts/feedback_generator.py` |
| Detectar copias entre entregas | `python scripts/plagiarism_detector.py` |
| Ver la curva de dificultad de un mapa | `python scripts/difficulty_curve.py` |

Y ya escrito: **3 laboratorios** (`docs/labs/`), **4 cuestionarios**
(`docs/quizzes/`), un **banco de exámenes** (`docs/exam_bank/`), las
**rúbricas** (`docs/rubricas/`), un **temario de ejemplo**
([`78_SAMPLE_SYLLABUS.md`](78_SAMPLE_SYLLABUS.md)) y la **guía para el
ayudante** ([`79_TA_GUIDE.md`](79_TA_GUIDE.md)).

**Lo que conviene saber antes de calificar.** `grade_stage` puntúa sobre 130 y
la media de los dieciséis mapas del repositorio es **79,9 %** — o sea, la
rúbrica no regala. Y tiene un sesgo conocido y deliberado, escrito en
`KNOWN_GAPS.md` como GAP-024: el calificador mide el alcance del salto con una
fórmula **más permisiva** que el motor. Falla del lado que no suspende a nadie
injustamente, y por eso se dejó así.

---

## 3. Estudiante

**Puedes construir tu nivel, tu enemigo y tu jefe sin tocar el núcleo del
motor, y comprobar tu nota antes de entregar.**

Empieza por aquí, en este orden:

1. **Instalar:** `pip install -e ".[dev]"`, luego `python main.py`.
2. **Copiar la plantilla:** `student_templates/stage_template/` — trae un mapa
   mínimo que ya funciona, con su spawn, su checkpoint, su salida y **dos
   pendientes** de ejemplo.
3. **Ver qué puedes poner:**
   [`73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md`](73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md)
   es el inventario de todo lo disponible, verificado contra el código.
4. **Calificarte antes de entregar:**
   `python scripts/grade_stage.py mi_mapa.tmx --json`. La misma herramienta que
   usa quien te evalúa.

Para crear cosas nuevas hay una guía por cada una:
[`STAGE_CREATION.md`](STAGE_CREATION.md),
[`ENEMY_CREATION.md`](ENEMY_CREATION.md),
[`BOSS_CREATION.md`](BOSS_CREATION.md), y la completa
[`60_GUIA_COMPLETA_DEL_MOTOR.md`](60_GUIA_COMPLETA_DEL_MOTOR.md).

**Dos cosas que te protegen mientras aprendes.** Si tu enemigo lanza una
excepción, **el motor no se cae**: retira esa entidad, escribe la traza en el
registro y el nivel sigue jugándose — así un fallo tuyo no arruina la demo de
clase. Y `EnemyBase` es una plantilla con métodos obligatorios: si te falta uno,
falla al instanciar y te dice cuál, en vez de comportarse raro.

---

## 4. Programador

**Puedes leer un motor completo de tamaño abarcable, con una suite que de verdad
sujeta lo que toques.**

| Quiero… | Comando |
|---|---|
| Toda la suite | `pytest` |
| Lint (el único que bloquea un merge) | `ruff check src/engine src/framework src/stages/stage0 tests/ scripts/ tools/` |
| Tipos (sólo el alcance del trinquete) | `mypy $(grep -v '^\s*#' mypy_scope.txt)` |
| Comprobar que las pruebas prueban algo | `python scripts/mutation_check.py` |
| Buscar sistemas que nadie llama | `python scripts/check_orphan_systems.py --ci` |
| Contrastar documentación contra código | `python scripts/audit_docs_vs_code.py` |
| Medir el proyecto | `python scripts/project_stats.py` |

Arquitectura en [`03_ARCHITECTURE.md`](03_ARCHITECTURE.md), contratos en
[`22_API_CONTRACTS.md`](22_API_CONTRACTS.md), y el estado medido en
[`62_ESTADO_DEL_PROYECTO.md`](62_ESTADO_DEL_PROYECTO.md).

**Puedes extender el motor sin tocarlo:** hay un sistema de plugins con ganchos
en `plugins/`, y un fallo de un plugin queda aislado.

**Lo que te vas a encontrar y parece un defecto sin serlo.** El alcance de mypy
es un trinquete deliberado de 25 ficheros, no un olvido. `src/stages/` está
fuera del lint a propósito: es código de estudiantes y se califica con la
rúbrica, no con el linter. Y la política bilingüe es «bilingüe donde hay
lector», razonada con una medición. Antes de corregir cualquiera de las tres,
lee el comentario que la explica.

**Y una honesta:** la ruta de dibujado en GPU está medida y **no** puesta. Gana
dibujando —hasta 10× con 8.000 sprites en la tarjeta dedicada— pero el juego
dibuja unas veinte entidades por fotograma y a esa escala subirlas y bajarlas
cuesta más que dibujarlas en CPU. El razonamiento entero, y qué haría falta para
cambiarlo, está en [`87_REPORTE_DE_LO_QUE_FALTA.md`](87_REPORTE_DE_LO_QUE_FALTA.md) §20.3.

---

## 5. Diseñador de juego

**Puedes probar ideas de mecánica sin escribir el motor que las sostiene, porque
ya está.**

Lo que existe y se puede combinar: salto con *coyote time* y *buffer*, dash,
**pogo** (rebote al golpear hacia abajo), **bash** (impulso al golpear un
proyectil marcado), parada, combos con multiplicador, *hit-stop* y sacudida
direccional, sigilo con conos de visión y cuatro estados, escuadrones de
enemigos que deciden táctica en grupo, economía con tienda e inventario, árbol
de habilidades, modo *speedrun* con parciales y Boss Rush.

| Quiero… | Dónde |
|---|---|
| El diseño del juego | [`64_GAME_DESIGN_DOCUMENT.md`](64_GAME_DESIGN_DOCUMENT.md) |
| Las 21 especies y sus parámetros | [`18_ENEMY_ROSTER.md`](18_ENEMY_ROSTER.md) |
| Cómo se construye un jefe por fases | [`17_BOSS_SPEC.md`](17_BOSS_SPEC.md) |
| Niveles y jefes por diseñar | [`86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md`](86_ESPECIFICACION_DE_NIVELES_Y_JEFES.md) |
| Qué falta y qué se decidió no hacer | [`87_REPORTE_DE_LO_QUE_FALTA.md`](87_REPORTE_DE_LO_QUE_FALTA.md) |

**Los enemigos son datos, no clases.** Las 21 especies son una tabla
(`SpeciesSpec`) tendida sobre **3** clases base — `EnemyWalker` (8 especies),
`EnemyFlying` (6) y `EnemyShooter` (7)—: añadir una especie es una fila, y
ajustar el equilibrio es cambiar números.

El motor trae **8** arquetipos colocables desde Tiled, así que hay cinco
—`Archer`, `Assassin`, `Brute`, `Caster`, `Charger`— que existen, funcionan y se
pueden poner en un mapa, pero **ninguna especie del bestiario los usa como
base**. Es sitio libre para diseñar: una especie nueva sobre uno de esos cinco
es una fila en la tabla y cero código.

**Lo que este proyecto recomienda no tocar:** la gravedad y la fuerza de salto.
El arco actual es más vertical de lo que pide el manual, y cambiarlo recalibra
dieciséis mapas ya calificados. Está razonado en el §15.10 del reporte 87.

---

## 6. Diseñador de niveles

**Puedes construir un nivel entero en Tiled, verlo sin abrir el juego y saber su
nota antes de entregarlo.** Sin escribir Python.

| Quiero… | Comando |
|---|---|
| Ver mi mapa completo con su iluminación | `python scripts/preview_tmx.py mi_mapa.tmx --con-etiquetas` |
| Verlo de noche | `python scripts/preview_tmx.py mi_mapa.tmx --hora 23` |
| Ver sólo la geometría | `python scripts/preview_tmx.py mi_mapa.tmx --sin-luz` |
| Validar antes de cargar | `python scripts/validate_tmx.py mi_mapa.tmx` |
| Calificarlo | `python scripts/grade_stage.py mi_mapa.tmx --json` |

**70 tipos de objeto** se colocan desde Tiled sin tocar código: plataformas
móviles y que se hunden, cuestas de verdad, resortes, tirolesas, lianas, bloques
rompibles y empujables, zonas de agua, viento, fricción, láser y onda expansiva,
bloques al ritmo de la música, zonas de *warp*, guardias con cono de visión,
puertas con llave, cofres, disparadores de evento y de cinemática. La referencia
completa y siempre al día está en [`STAGE_CREATION.md`](STAGE_CREATION.md) — la
genera un script desde el registro real, así que no puede mentir.

**La atmósfera también es del mapa, no del programador:** luz ambiental, focos
con parpadeo, clima, estación, hora del día y ciclo día/noche son propiedades
que se escriben en Tiled.

**Y un mapa donde probarlo todo:** `assets/maps/stage_mecanicas/` es la vitrina
— cada mecánica colocada con un cartel que explica qué estás viendo. Ojo: ese
mapa **se genera** con `python tools/generate_stage_mecanicas.py`; si lo editas
a mano, el CI te lo dirá.

---

## 7. Lo que está abierto ahora mismo

Para que nadie descubra por su cuenta lo que ya se sabe:

* **El jefe Gavilán** está al 45 % de la rúbrica, y es **asignación de
  estudiante** a propósito, no deuda del motor.
* **Feedback diegético** —daño visible en el sprite, color del arma al cargar—
  no está.
* **Contorno de alto contraste**: ya cubre jugador y enemigos; faltan los iconos
  que no dependan del color.
* **La ruta de dibujado en GPU** está medida y no puesta (§20.3 del reporte 87).

La lista viva, con su medición al lado, es
[`87_REPORTE_DE_LO_QUE_FALTA.md`](87_REPORTE_DE_LO_QUE_FALTA.md).
