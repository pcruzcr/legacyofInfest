"""
Las tres reglas de capas de `03_ARCHITECTURE.md` §3.1, comprobadas.

AUD-101
=======
La sección decía: «*Cross-layer imports (going upward) are prohibited*». Se
midió contra el código y estaba incumplida **27 veces**. Las 27 eran
legítimas: `engine/scenes/` es la capa de aplicación —ahí viven los
laboratorios académicos, que enseñan algoritmos de `framework/processing/`— y
`engine/core/app.py` es la raíz de composición, cuyo trabajo es precisamente
conocer todas las piezas.

Una regla que se incumple veintisiete veces sin que pase nada no es una
regla: es una frase decorativa. Y lo peor de una regla así no es que se
incumpla, sino que nadie distingue ya una infracción real de las veintisiete
toleradas.

Lo que sí era cierto —y nadie había comprobado— es que el **núcleo** del motor
y las funciones de procesamiento están perfectamente limpios. Eso es lo que
tiene valor y es lo que se vigila aquí.

Por qué estas tres y no más
---------------------------
Cada una protege algo concreto que se pierde si se rompe:

- **L1** es lo que permite leer y reutilizar el motor sin arrastrar el juego.
- **L2** es lo que permite ejecutar la convolución, Sobel, Otsu o HOG desde un
  cuaderno, sin arrancar pygame. Es la unidad de trabajo del curso.
- **L3** es lo que permite entregar y corregir cada escenario por separado.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"

#: La raíz de composición: el único sitio que conoce todas las piezas a la vez,
#: porque su trabajo es cablearlas.
RAIZ_DE_COMPOSICION = "src/engine/core/app.py"

#: La capa de aplicación. No es el núcleo del motor: son las pantallas, y los
#: laboratorios académicos que enseñan lo que vive en `framework/processing`.
CAPA_DE_APLICACION = "src/engine/scenes/"

#: Dependencias toleradas de `framework`/`engine` hacia `stages` (regla L4).
#:
#: `entity_factory.ensure_registered()` da de alta al Venado en el registro de
#: entidades, y para eso lo importa. Se tolera porque el Venado es el **jefe de
#: referencia** que mantiene el equipo docente y del que copian los alumnos, no
#: una entrega. `tutorial_hub` es el **hub de tutorial jugable** (AUD-721) que
#: el menú principal empuja como escena; vive en `stages/` por ser contenido
#: de referencia, no entrega de estudiante, y por eso `engine/scenes` lo importa
#: de forma diferida dentro de la función.
#:
#: Añadir algo aquí es afirmar «esto es material del curso, no contenido de un
#: estudiante», y hay que justificarlo también en `03_ARCHITECTURE.md` §3.1.
EXCEPCION_L4: frozenset[str] = frozenset({
    "src.stages.boss_venado.boss_venado",
    "src.stages.tutorial_hub.tutorial_hub",
})


def _modulos_importados(fichero: pathlib.Path) -> set[str]:
    """Todos los módulos que un fichero importa, incluidos los diferidos.

    Se usa `ast` y no expresiones regulares porque medio proyecto importa
    dentro de funciones para romper ciclos, y un `grep` de líneas que empiezan
    por `import` se los saltaría precisamente donde más interesan.
    """
    # `utf-8-sig` y no `utf-8`: los editores de Windows escriben una marca BOM
    # al principio del fichero, y `ast.parse` la rechaza con «invalid
    # non-printable character U+FEFF». Una entrega del curso llegó así y tumbó
    # esta prueba, el validador de TMX y el calificador de jefes a la vez. El
    # fichero era correcto; lo que no toleraba la marca eran las herramientas.
    try:
        arbol = ast.parse(fichero.read_text(encoding="utf-8-sig"))
    except SyntaxError as e:  # pragma: no cover - sería un fallo de sintaxis real
        pytest.fail(f"{fichero} no se puede analizar: {e}")

    modulos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module)
        elif isinstance(nodo, ast.Import):
            modulos.update(alias.name for alias in nodo.names)
    return modulos


def _ficheros(subruta: str) -> list[pathlib.Path]:
    return [
        f for f in (SRC / subruta).rglob("*.py") if "__pycache__" not in str(f)
    ]


def _relativo(f: pathlib.Path) -> str:
    return f.relative_to(RAIZ).as_posix()


def test_L1_el_nucleo_del_motor_no_conoce_el_framework() -> None:
    """El motor se puede leer y reutilizar sin arrastrar el juego.

    Excluye la raíz de composición y la capa de aplicación, que son
    excepciones nombradas en `03_ARCHITECTURE.md` §3.1 y no descuidos.
    """
    infracciones = []
    for fichero in _ficheros("engine"):
        relativo = _relativo(fichero)
        if relativo == RAIZ_DE_COMPOSICION or relativo.startswith(CAPA_DE_APLICACION):
            continue
        for modulo in _modulos_importados(fichero):
            if modulo.startswith("src.framework"):
                infracciones.append(f"{relativo} -> {modulo}")

    assert not infracciones, (
        "el núcleo del motor ha empezado a depender del framework:\n  "
        + "\n  ".join(sorted(infracciones))
        + "\n\nSi la dependencia es legítima, la pieza probablemente pertenece "
          "a engine/scenes/ (capa de aplicación) y no al núcleo."
    )


def test_L2_el_procesamiento_no_necesita_el_motor() -> None:
    """Convolución, Sobel, Otsu y HOG se ejecutan sin arrancar pygame.

    Es la unidad de trabajo del curso: el estudiante tiene que poder llamar a
    estas funciones desde un cuaderno para comparar su resultado con el que
    calculó a mano.
    """
    infracciones = [
        f"{_relativo(f)} -> {m}"
        for f in _ficheros("framework/processing")
        for m in _modulos_importados(f)
        if m.startswith("src.engine")
    ]
    assert not infracciones, (
        "framework/processing ha empezado a depender del motor:\n  "
        + "\n  ".join(sorted(infracciones))
    )


def test_L2_el_procesamiento_si_puede_importarse_a_si_mismo() -> None:
    """La regla anterior decía «ni engine ni framework», y era demasiado.

    Tres módulos del paquete importan a sus vecinos —`reference_model` usa
    `pattern_recognition_tools`, que usa `vision_tools`— y eso es cohesión
    normal, no una fuga de capas. Se comprueba que sigue siendo posible para
    que nadie «arregle» esto leyendo la regla vieja.
    """
    internos = [
        m
        for f in _ficheros("framework/processing")
        for m in _modulos_importados(f)
        if m.startswith("src.framework.processing")
    ]
    assert internos, (
        "ningún módulo de processing importa a otro; si se han separado a "
        "propósito, actualiza esta prueba y §3.1"
    )


def test_L3_los_escenarios_estan_aislados() -> None:
    """Cada `stages/stageN` es entregable y corregible por separado."""
    infracciones = []
    for fichero in _ficheros("stages"):
        partes = fichero.relative_to(SRC / "stages").parts
        if len(partes) < 2:
            continue
        propio = partes[0]
        for modulo in _modulos_importados(fichero):
            if modulo.startswith("src.stages") and f".{propio}" not in modulo:
                infracciones.append(f"{_relativo(fichero)} -> {modulo}")

    assert not infracciones, (
        "un escenario importa de otro; dejarían de poder entregarse por "
        "separado:\n  " + "\n  ".join(sorted(infracciones))
    )


def test_L4_el_motor_no_depende_del_contenido() -> None:
    """AUD-172 — `engine/` y `framework/` no importan de `stages/`.

    `stages/` es contenido, y en su mayor parte entregas de estudiantes. Una
    dependencia en este sentido invierte la relación: un paquete que falta o
    que no importa deja de romper *un nivel* y pasa a romper el juego entero,
    porque `ensure_registered()` corre antes de cargar cualquier mapa.

    La comprobación no existía. La única infracción del árbol —el jefe de
    referencia— llevaba ahí sin declararse, indistinguible de un descuido.
    """
    infracciones = [
        f"{_relativo(f)} -> {m}"
        for carpeta in ("engine", "framework")
        for f in _ficheros(carpeta)
        for m in _modulos_importados(f)
        if m.startswith("src.stages") and m not in EXCEPCION_L4
    ]
    assert not infracciones, (
        "el motor ha empezado a depender de un escenario concreto:\n  "
        + "\n  ".join(sorted(infracciones))
        + "\n\nSi es contenido de referencia del curso, decláralo en "
          "EXCEPCION_L4 y en 03_ARCHITECTURE.md §3.1, con el porqué. Si no, "
          "la pieza pertenece a framework/ y no a stages/."
    )


def test_las_excepciones_nombradas_siguen_existiendo() -> None:
    """Si desaparecen, la exclusión de L1 se vuelve una puerta abierta sin dueño."""
    assert (RAIZ / RAIZ_DE_COMPOSICION).is_file()
    assert (RAIZ / CAPA_DE_APLICACION).is_dir()

    for modulo in EXCEPCION_L4:
        ruta = SRC.parent / (modulo.replace(".", "/") + ".py")
        assert ruta.is_file(), (
            f"EXCEPCION_L4 nombra `{modulo}` y no existe. Una excepción a una "
            f"regla de capas que apunta a la nada es una puerta abierta sin "
            f"dueño: retírala de la lista"
        )

    infractores = [
        _relativo(f)
        for carpeta in ("engine", "framework")
        for f in _ficheros(carpeta)
        if _modulos_importados(f) & EXCEPCION_L4
    ]
    assert infractores, (
        "ya nadie usa la excepción de L4; retírala de EXCEPCION_L4 y de "
        "03_ARCHITECTURE.md §3.1 en vez de dejar la puerta abierta"
    )


def test_la_documentacion_describe_estas_mismas_reglas() -> None:
    """La sección §3.1 y esta prueba no pueden separarse.

    Es el fallo que originó AUD-101: la prosa decía una cosa, el código hacía
    otra, y nada las comparaba.
    """
    texto = (RAIZ / "docs" / "03_ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "tests/test_layering.py" in texto, (
        "§3.1 ya no dice quién comprueba sus reglas"
    )
    for etiqueta in ("**L1**", "**L2**", "**L3**", "**L4**"):
        assert etiqueta in texto, f"§3.1 ya no enuncia la regla {etiqueta}"
