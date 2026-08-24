"""
Progreso académico de un estudiante: qué unidades ha aprobado y cuáles puede abrir.

AUD-095
=======
El cuestionario ya existía, pero no registraba nada: se abría con Q, se
contestaba y se olvidaba al cerrar la escena. Y las diez demos estaban
disponibles desde el primer minuto, así que un estudiante podía abrir
reconocimiento de patrones sin haber visto un vector.

Este módulo pone las dos piezas que faltaban: **un resultado que persiste** y
**una cadena de desbloqueo**.

Decisiones
----------
- *Encadenado, no en árbol.* Para abrir una unidad hay que haber aprobado la
  anterior. El temario es lineal y no tiene sentido inventar un grafo de
  prerrequisitos que nadie va a mantener. Si algún día deja de serlo,
  `esta_desbloqueada` es el único sitio que cambia.
- *La primera unidad siempre abierta.* Si no, un estudiante nuevo se
  encuentra un menú entero bloqueado y ninguna forma de empezar.
- *Se guarda el mejor intento, no el último.* Un estudiante que aprueba y
  vuelve a entrar a repasar no debería poder desaprobar por curiosear.
- *Identificado por el correo de la universidad.* Es lo que el profesor tiene
  en su lista de clase; cualquier otro identificador obligaría a mantener una
  tabla de equivalencias. El correo se normaliza —minúsculas, sin espacios—
  para que `Juan.Perez@UNI.EDU` y `juan.perez@uni.edu` sean el mismo
  estudiante.
- *Un fichero JSON por estudiante.* Legible, revisable y fácil de recoger.
  Aquí no se usa pickle porque estos ficheros los van a intercambiar treinta
  personas y abrir un `.pkl` ajeno ejecuta código arbitrario.

  Para ser exacto: pickle **no** está retirado del proyecto entero. Sigue
  vivo, vía `joblib`, en el modelo de referencia de la Unidad IX
  (`framework/processing/reference_model.py`), donde carga un `.pkl` que
  genera la propia máquina y que avisa por registro al deserializar. Esa
  excepción está acotada y documentada; lo que AUD-035 retiró fue el pickle
  de las partidas guardadas, que sí viajan entre alumnos.
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.framework.academic.curriculum import PLAN, ids_de_unidades, unidad

logger = logging.getLogger(__name__)

#: Cuántas preguntas tiene el examen de cada unidad.
PREGUNTAS_POR_UNIDAD: int = 5
#: Cuántas hay que acertar para aprobar y desbloquear la siguiente.
#:
#: Cuatro de cinco es el 80 %. Con tres de cinco (60 %) se aprueba acertando
#: al azar más a menudo de lo aceptable: con cuatro opciones por pregunta la
#: probabilidad de colar 3 de 5 a ciegas es del 10,4 %, y la de colar 4 de 5
#: baja al 1,6 %.
ACIERTOS_PARA_APROBAR: int = 4

#: Versión del formato del fichero de progreso. Si cambia la forma de los
#: datos, sube esto y añade la migración en `_migrar`.
VERSION: int = 1

_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class ResultadoIntento:
    """Lo que devuelve registrar un examen."""

    unidad_id: str
    aciertos: int
    total: int
    aprobado: bool
    #: `True` si este intento es el que ha aprobado la unidad por primera vez.
    recien_aprobada: bool
    #: La unidad que se acaba de abrir, si la hay.
    desbloqueada: str | None


def _normalizar_correo(correo: str) -> str:
    return correo.strip().lower()


def es_correo_valido(correo: str) -> bool:
    """Comprobación mínima de forma. No verifica que exista."""
    return bool(_CORREO.match(_normalizar_correo(correo)))


#: Largo máximo del apodo. Cabe en la franja de diálogo a escala 2,0 sin
#: recortar la frase que lo rodea, que es el límite que importa.
APODO_MAX: int = 16


def _limpiar_apodo(apodo: str) -> str:
    """Recorta y quita lo que rompería un cuadro de diálogo.

    Se filtran los saltos de línea y los caracteres de control: un apodo con
    un `
` parte la frase en dos y deja media línea colgando, y eso no se
    diagnostica mirando el diálogo — se diagnostica mirando el JSON.
    """
    limpio = "".join(c for c in str(apodo) if c.isprintable())
    return limpio.strip()[:APODO_MAX]


def nombre_de_fichero(correo: str) -> str:
    """Nombre de fichero seguro derivado del correo.

    El correo puede traer puntos, guiones y —en algunos dominios— acentos.
    Se translitera a ASCII y se sustituye todo lo que no sea alfanumérico por
    un guion bajo, de modo que nunca se pueda salir del directorio ni chocar
    con un nombre reservado del sistema de ficheros.
    """
    plano = unicodedata.normalize("NFKD", _normalizar_correo(correo))
    plano = plano.encode("ascii", "ignore").decode("ascii")
    seguro = re.sub(r"[^a-z0-9]+", "_", plano).strip("_")
    return f"{seguro or 'anonimo'}.json"


class ProgresoAcademico:
    """Las notas de un estudiante y qué puede abrir con ellas."""

    def __init__(self, correo: str = "", apodo: str = "") -> None:
        self.correo: str = _normalizar_correo(correo)
        #: Cómo quiere que le llamen — AUD-291.
        #:
        #: El correo identifica; el apodo es lo que se lee. Son cosas distintas
        #: y por eso son dos campos: un diálogo que te llame
        #: «a01234567@tec.mx» no es personalización, es una fuga de dato
        #: personal proyectada en la pantalla de un aula.
        self.apodo: str = _limpiar_apodo(apodo)
        #: unidad -> mejor número de aciertos conseguido.
        self._mejor: dict[str, int] = {}
        #: unidad -> cuántas veces lo ha intentado. Le sirve al profesor para
        #: distinguir «lo entendió» de «lo acabó adivinando al sexto intento».
        self._intentos: dict[str, int] = {}

    # -- consulta --------------------------------------------------
    def aciertos(self, id_unidad: str) -> int:
        return self._mejor.get(id_unidad, 0)

    def intentos(self, id_unidad: str) -> int:
        return self._intentos.get(id_unidad, 0)

    def esta_aprobada(self, id_unidad: str) -> bool:
        return self.aciertos(id_unidad) >= ACIERTOS_PARA_APROBAR

    def esta_desbloqueada(self, id_unidad: str) -> bool:
        """¿Puede abrir esta unidad?

        La primera siempre; el resto, si la anterior está aprobada. Una
        unidad ya aprobada sigue abierta: se puede volver a repasar.
        """
        ids = ids_de_unidades()
        if id_unidad not in ids:
            # Lo que no está en el temario —cajón de arena, tablas de
            # récords, constructor de tuberías— no se bloquea nunca.
            return True
        i = ids.index(id_unidad)
        if i == 0:
            return True
        return self.esta_aprobada(ids[i - 1])

    def unidades_desbloqueadas(self) -> tuple[str, ...]:
        return tuple(i for i in ids_de_unidades() if self.esta_desbloqueada(i))

    def unidades_aprobadas(self) -> tuple[str, ...]:
        return tuple(i for i in ids_de_unidades() if self.esta_aprobada(i))

    def porcentaje(self) -> float:
        """Fracción del temario aprobada, de 0 a 1."""
        if not PLAN:
            return 0.0
        return len(self.unidades_aprobadas()) / len(PLAN)

    def unidad_actual(self) -> str | None:
        """La primera sin aprobar: por donde le toca seguir."""
        for i in ids_de_unidades():
            if not self.esta_aprobada(i):
                return i
        return None

    # -- registro --------------------------------------------------
    def registrar_intento(self, id_unidad: str, aciertos: int, total: int = PREGUNTAS_POR_UNIDAD) -> ResultadoIntento:
        """Anota un examen y devuelve qué ha cambiado.

        Se guarda el **mejor** intento, no el último: repasar una unidad ya
        aprobada y fallar por ir deprisa no puede quitarle el aprobado ni
        volver a cerrar la unidad siguiente, que ya estaría a medias.
        """
        if unidad(id_unidad) is None:
            msg = f"no existe la unidad {id_unidad!r}"
            raise ValueError(msg)
        if total <= 0:
            msg = f"un examen no puede tener {total} preguntas"
            raise ValueError(msg)
        aciertos = max(0, min(aciertos, total))

        estaba_aprobada = self.esta_aprobada(id_unidad)
        self._intentos[id_unidad] = self._intentos.get(id_unidad, 0) + 1
        self._mejor[id_unidad] = max(self._mejor.get(id_unidad, 0), aciertos)

        aprobado = aciertos >= ACIERTOS_PARA_APROBAR
        recien = aprobado and not estaba_aprobada

        desbloqueada: str | None = None
        if recien:
            ids = ids_de_unidades()
            i = ids.index(id_unidad) + 1
            if i < len(ids):
                desbloqueada = ids[i]

        return ResultadoIntento(
            unidad_id=id_unidad,
            aciertos=aciertos,
            total=total,
            aprobado=aprobado,
            recien_aprobada=recien,
            desbloqueada=desbloqueada,
        )

    # -- persistencia ----------------------------------------------
    def a_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "correo": self.correo,
            "apodo": self.apodo,
            "mejor": dict(self._mejor),
            "intentos": dict(self._intentos),
        }

    @classmethod
    def desde_dict(cls, datos: dict[str, Any]) -> ProgresoAcademico:
        datos = _migrar(datos)
        progreso = cls(str(datos.get("correo", "")), str(datos.get("apodo", "")))
        conocidas = set(ids_de_unidades())
        for clave, valor in dict(datos.get("mejor", {})).items():
            # Se descarta lo que ya no está en el temario en vez de arrastrarlo:
            # si una unidad desaparece, su nota no debe seguir contando para el
            # porcentaje ni desbloquear nada.
            if clave in conocidas:
                progreso._mejor[clave] = max(0, int(valor))
        for clave, valor in dict(datos.get("intentos", {})).items():
            if clave in conocidas:
                progreso._intentos[clave] = max(0, int(valor))
        return progreso

    def guardar(self, directorio: Path) -> Path:
        directorio.mkdir(parents=True, exist_ok=True)
        destino = directorio / nombre_de_fichero(self.correo)
        # Se escribe a un temporal y se renombra: si el proceso muere a mitad
        # —o el estudiante cierra el portátil— el fichero anterior sigue
        # entero en vez de quedar truncado.
        temporal = destino.with_suffix(".json.tmp")
        temporal.write_text(
            json.dumps(self.a_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporal.replace(destino)
        return destino

    @classmethod
    def cargar(cls, directorio: Path, correo: str) -> ProgresoAcademico:
        """Lee el progreso de ese correo; si no hay fichero, empieza de cero.

        Un fichero ilegible **no** hace caer el juego: se registra el aviso y
        se devuelve un progreso vacío. Perder las notas de un examen de
        prácticas es malo; que treinta portátiles no arranquen el día de la
        entrega, peor.
        """
        ruta = directorio / nombre_de_fichero(correo)
        if not ruta.is_file():
            return cls(correo)
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            logger.warning("progreso académico ilegible en %s: %s", ruta, e)
            return cls(correo)
        if not isinstance(datos, dict):
            logger.warning("progreso académico con forma inesperada en %s", ruta)
            return cls(correo)
        progreso = cls.desde_dict(datos)
        if not progreso.correo:
            progreso.correo = _normalizar_correo(correo)
        return progreso


def _migrar(datos: dict[str, Any]) -> dict[str, Any]:
    """Lleva un fichero de una versión antigua a la actual.

    Hoy sólo existe la versión 1, así que no hay nada que hacer. La función
    existe igualmente para que la primera migración sea añadir un bloque aquí
    y no rediseñar la carga entera, que es como se pierden datos de verdad.
    """
    version = int(datos.get("version", 0) or 0)
    if version > VERSION:
        logger.warning(
            "progreso académico de una versión más nueva (%s > %s); "
            "se lee lo que se entienda", version, VERSION,
        )
    return datos
