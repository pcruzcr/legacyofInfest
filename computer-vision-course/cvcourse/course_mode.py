"""
Modo taller: abrir las Unidades VII, VIII y IX el primer día. Hueco H5.

El problema
-----------
El temario del motor es una **cadena lineal de desbloqueo**: para abrir una
unidad hay que haber aprobado la anterior con 4 aciertos de 5
(`framework/academic/progress.py`, `esta_desbloqueada`). Es una decisión
deliberada y bien razonada para el curso de once clases — evita que alguien
entre en reconocimiento de patrones sin haber visto un vector.

Pero este taller **empieza** en la Unidad VII. Un estudiante que abre el menú
de demostraciones el día 1 se encuentra `filter`, `vision` y `pattern`
cerradas, con siete unidades de por medio. El laboratorio del motor de la
Clase 1 no arrancaría.

La solución, y por qué es aceptable
------------------------------------
Se usa un **perfil de progreso aparte**. `SesionAcademica` acepta el directorio
donde guarda las notas (`reiniciar(directorio)`, API pública que ya usan las
pruebas del motor) y `registrar_examen` también es pública. El taller crea su
propio directorio y siembra ahí las unidades previas como aprobadas.

Dos propiedades hacen que esto no sea un truco sucio:

1. **No se toca `progress.py` ni ningún fichero del motor.** Todo pasa por API
   pública. El curso de once clases sigue funcionando exactamente igual.
2. **No se falsifica el expediente de nadie.** Los ficheros del curso normal
   viven en otro directorio y no se leen ni se escriben aquí. El perfil del
   taller es un artefacto del taller, y así hay que decirlo en clase: «estas
   unidades están abiertas porque este módulo empieza aquí», no «este
   estudiante aprobó siete cuestionarios».

El correo por defecto lo deja evidente: `taller@…`, no el de nadie.

Por qué se abre una unidad por vez y no las tres de golpe
----------------------------------------------------------
La primera versión de este módulo abría VII, VIII y IX el día 1. Su propia
prueba la tumbó, y el fallo resultó ser de diseño y no de código: la cadena de
desbloqueo es *transitiva*, así que abrir la Unidad IX exige dar por aprobadas
la VII y la VIII — es decir, **las tres unidades que este taller evalúa**. Sus
cuestionarios se habrían quedado en decorado.

De modo que se abre por tramos, uno por clase:

* Clase 1 → `activar()`                       abre la VII.
* Clase 3 → `abrir("vision")`                 abre la VIII.
* Clase 4 → `abrir("patrones")`               abre la IX.

Así el estudiante contesta el cuestionario de cada unidad cuando toca —que es
la evaluación de estas cinco clases— y el profesor conserva la llave para
seguir adelante si alguien se atasca. La cadena del motor se respeta en vez de
esquivarse.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = [
    "CORREO_DEL_TALLER",
    "DIRECTORIO_DE_PERFILES",
    "PRIMERA_UNIDAD",
    "UNIDADES_DEL_TALLER",
    "abrir",
    "activar",
    "esta_activo",
    "unidades_abiertas",
]

#: Las tres unidades que cubre el taller, con la clave de su escena de
#: demostración en `scene_registry`.
UNIDADES_DEL_TALLER: dict[str, str] = {
    "imagen": "filter",     # Unidad VII  — Procesamiento digital de imagen
    "vision": "vision",     # Unidad VIII — Segmentación y análisis
    "patrones": "pattern",  # Unidad IX   — Reconocimiento de patrones
}

#: La unidad con la que arranca el taller (Clase 1).
PRIMERA_UNIDAD = "imagen"

#: Correo del perfil. Deliberadamente impersonal: este progreso no es de nadie.
CORREO_DEL_TALLER = "taller@vision.curso"


def _raiz_del_curso() -> Path:
    return Path(__file__).resolve().parent.parent


#: Dónde viven las notas del taller. **No** es el directorio del curso normal.
DIRECTORIO_DE_PERFILES: Path = _raiz_del_curso() / "profiles"


def _sembrar_hasta(sesion, unidad_destino: str) -> tuple[str, ...]:
    """Aprueba todo lo **estrictamente anterior** a `unidad_destino`.

    Devuelve las unidades sembradas. La propia `unidad_destino` no se toca: se
    abre su puerta, no se le pone la nota.
    """
    from src.framework.academic.curriculum import ids_de_unidades
    from src.framework.academic.progress import PREGUNTAS_POR_UNIDAD

    todas = ids_de_unidades()
    if unidad_destino not in todas:
        raise ValueError(
            f"{unidad_destino!r} no está en el temario del motor. "
            f"Unidades del taller: {sorted(UNIDADES_DEL_TALLER)}"
        )

    previas = todas[: todas.index(unidad_destino)]
    for id_unidad in previas:
        # Idempotente: el progreso guarda el mejor intento, no el último, así
        # que volver a sembrar no degrada nada ni duplica notas.
        sesion.registrar_examen(id_unidad, PREGUNTAS_POR_UNIDAD)
    return previas


def activar(
    correo: str = CORREO_DEL_TALLER,
    directorio: Path | None = None,
    hasta: str = PRIMERA_UNIDAD,
):
    """Arranca el perfil del taller y abre hasta `hasta`. Devuelve la sesión.

    Por defecto abre la Unidad VII, que es con la que empieza la Clase 1. Las
    otras dos se abren con `abrir()` cuando llega su clase — ver la cabecera
    del módulo para el porqué.
    """
    from cvcourse.engine_bridge import _asegurar_importable, hay_motor

    if not hay_motor():
        raise RuntimeError(
            "el modo taller necesita el repositorio del motor; "
            "los notebooks sin motor no lo usan"
        )

    _asegurar_importable()

    from src.framework.academic.sesion import SesionAcademica

    destino = Path(directorio) if directorio is not None else DIRECTORIO_DE_PERFILES
    destino.mkdir(parents=True, exist_ok=True)

    sesion = SesionAcademica.reiniciar(destino)
    # `recordar=False` es imprescindible. Con el valor por defecto, `entrar`
    # deja el correo en los ajustes del juego para reanudar la sesión en el
    # siguiente arranque — y entonces el estudiante abriría el curso normal
    # identificado como el perfil del taller. El aislamiento del que depende
    # todo este módulo se perdería justo por ahí.
    if not sesion.entrar(correo, recordar=False):
        raise ValueError(f"el motor no acepta {correo!r} como correo de estudiante")

    previas = _sembrar_hasta(sesion, hasta)
    logger.info(
        "modo taller activo en %s: %d unidades sembradas, abierta '%s'",
        destino, len(previas), hasta,
    )
    return sesion


def abrir(unidad: str):
    """Abre otra unidad del taller sobre la sesión ya activa.

    Se usa al empezar la Clase 3 (``abrir("vision")``) y la Clase 4
    (``abrir("patrones")``). Es también la llave del profesor cuando alguien no
    aprueba el cuestionario y no puede quedarse fuera del laboratorio.
    """
    from cvcourse.engine_bridge import _asegurar_importable

    _asegurar_importable()
    from src.framework.academic.sesion import SesionAcademica

    sesion = SesionAcademica.instancia()
    if not sesion.identificado:
        raise RuntimeError("no hay sesión de taller activa: llama antes a activar()")

    _sembrar_hasta(sesion, unidad)
    logger.info("modo taller: abierta la unidad '%s'", unidad)
    return sesion


def unidades_abiertas() -> tuple[str, ...]:
    """Las unidades que la sesión activa puede abrir ahora mismo."""
    from cvcourse.engine_bridge import _asegurar_importable

    _asegurar_importable()
    from src.framework.academic.sesion import SesionAcademica

    return SesionAcademica.instancia().progreso.unidades_desbloqueadas()


def esta_activo() -> bool:
    """¿Está abierta la primera unidad del taller?

    Se comprueba el efecto —qué puede abrir el estudiante— y no una bandera
    interna. Una bandera puede quedarse en `True` mientras el progreso dice
    otra cosa; esto no puede mentir.
    """
    try:
        return PRIMERA_UNIDAD in unidades_abiertas()
    except (ImportError, RuntimeError):
        return False
