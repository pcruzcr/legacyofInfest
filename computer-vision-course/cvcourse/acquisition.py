"""
Adquisición: de dónde sale una imagen. El hueco H1 del análisis.

El problema que resuelve
------------------------
La Clase 1 tiene que enseñar que una imagen puede venir de una cámara, de un
fichero, de un vídeo o del propio motor, y que el código de proceso **no
debería enterarse** de cuál fue. Pero el mismo laboratorio tiene que correr en
cuatro sitios distintos:

* el portátil del profesor, con cámara;
* el del estudiante, casi siempre sin cámara;
* Google Colab, sin cámara y a menudo sin el repositorio del motor;
* la integración continua, sin cámara, sin pantalla y sin nada.

Un guion que llame a ``cv2.VideoCapture(0)`` directamente funciona en el primer
sitio y falla en los otros tres. Ese es el motivo de que aquí haya una
abstracción y no dos líneas de OpenCV: la diferencia entre un laboratorio que
funciona en las treinta máquinas del aula y uno que funciona en la del profesor.

El convenio de color, dicho una sola vez
-----------------------------------------
**Todas** las fuentes devuelven RGB en (alto, ancho, 3), uint8. OpenCV lee y
escribe BGR; la conversión se hace aquí, una vez, y el resto del curso no
vuelve a pensar en ello. Un estudiante que mezcle los dos convenios obtiene
imágenes azuladas y un histograma con los canales cambiados: no falla, miente.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

__all__ = [
    "Fuente",
    "FuenteArchivo",
    "FuenteCamara",
    "FuenteCarpeta",
    "FuenteMotor",
    "FuenteSintetica",
    "FuenteVideo",
    "mejor_fuente_disponible",
]

_EXTENSIONES = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")


def _bgr_a_rgb(imagen: np.ndarray) -> np.ndarray:
    """BGR → RGB sin depender de OpenCV para algo tan simple como invertir un eje."""
    if imagen.ndim == 2:
        return imagen
    return np.ascontiguousarray(imagen[:, :, ::-1])


class Fuente(ABC):
    """Una procedencia de imágenes. Se lee con `leer()` hasta que devuelve None.

    Es iterable y sirve como gestor de contexto, así que el patrón del curso es
    siempre el mismo, venga la imagen de donde venga::

        with abrir_lo_que_sea() as fuente:
            for imagen in fuente:
                procesar(imagen)
    """

    #: Nombre legible. Se imprime en las figuras para que el estudiante sepa
    #: qué está mirando cuando el material degradó a otra fuente.
    nombre: str = "fuente"

    @abstractmethod
    def leer(self) -> np.ndarray | None:
        """Siguiente imagen RGB (alto, ancho, 3) uint8, o None si se acabó."""

    def cerrar(self) -> None:
        """Libera lo que haya que liberar.

        No es abstracto a propósito: la mayoría de las fuentes —fichero,
        carpeta, motor, sintética— no tienen nada que cerrar, y obligarlas a
        escribir un `pass` sólo añadiría ruido a las cinco subclases. Las dos
        que sí sostienen un recurso del sistema, `FuenteVideo` y
        `FuenteCamara`, lo redefinen.
        """
        return None

    def __iter__(self):
        while True:
            imagen = self.leer()
            if imagen is None:
                return
            yield imagen

    def __enter__(self):
        return self

    def __exit__(self, *_excepcion: object) -> None:
        self.cerrar()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.nombre!r}>"


class FuenteArchivo(Fuente):
    """Una sola imagen de disco. La fuente más simple, y la que siempre funciona."""

    def __init__(self, ruta: str | Path, repeticiones: int = 1) -> None:
        self.ruta = Path(ruta)
        if not self.ruta.exists():
            raise FileNotFoundError(f"no existe la imagen: {self.ruta}")
        self.nombre = f"archivo:{self.ruta.name}"
        self._restantes = repeticiones
        self._cache: np.ndarray | None = None

    def leer(self) -> np.ndarray | None:
        if self._restantes <= 0:
            return None
        self._restantes -= 1
        if self._cache is None:
            import cv2

            crudo = cv2.imread(str(self.ruta), cv2.IMREAD_COLOR)
            if crudo is None:
                raise OSError(f"OpenCV no pudo leer {self.ruta}")
            self._cache = _bgr_a_rgb(crudo)
        return self._cache.copy()


class FuenteCarpeta(Fuente):
    """Todas las imágenes de una carpeta, en orden alfabético.

    El orden importa: `glob` no lo garantiza, y un laboratorio en el que «la
    tercera imagen» es distinta en cada máquina no se puede corregir.
    """

    def __init__(self, carpeta: str | Path, recursivo: bool = False) -> None:
        self.carpeta = Path(carpeta)
        if not self.carpeta.is_dir():
            raise NotADirectoryError(f"no es una carpeta: {self.carpeta}")
        patron = "**/*" if recursivo else "*"
        self.rutas = sorted(
            p for p in self.carpeta.glob(patron) if p.suffix.lower() in _EXTENSIONES
        )
        self.nombre = f"carpeta:{self.carpeta.name} ({len(self.rutas)} imágenes)"
        self._i = 0

    def leer(self) -> np.ndarray | None:
        while self._i < len(self.rutas):
            ruta = self.rutas[self._i]
            self._i += 1
            import cv2

            crudo = cv2.imread(str(ruta), cv2.IMREAD_COLOR)
            if crudo is None:
                # Un PNG corrupto entre doscientos no puede tumbar el
                # laboratorio entero; se avisa y se sigue.
                logger.warning("acquisition: no se pudo leer %s, se omite", ruta)
                continue
            return _bgr_a_rgb(crudo)
        return None


class FuenteVideo(Fuente):
    """Fotogramas de un fichero de vídeo.

    Es la sustituta natural de la cámara cuando no hay cámara: mismo flujo
    temporal, misma API, resultados reproducibles.
    """

    def __init__(self, ruta: str | Path, maximo: int | None = None) -> None:
        import cv2

        self.ruta = Path(ruta)
        if not self.ruta.exists():
            raise FileNotFoundError(f"no existe el vídeo: {self.ruta}")
        self._captura = cv2.VideoCapture(str(self.ruta))
        if not self._captura.isOpened():
            raise OSError(f"OpenCV no pudo abrir el vídeo {self.ruta}")
        self.nombre = f"video:{self.ruta.name}"
        self._maximo = maximo
        self._leidos = 0

    def leer(self) -> np.ndarray | None:
        if self._maximo is not None and self._leidos >= self._maximo:
            return None
        hay, fotograma = self._captura.read()
        if not hay:
            return None
        self._leidos += 1
        return _bgr_a_rgb(fotograma)

    def cerrar(self) -> None:
        self._captura.release()


class FuenteCamara(Fuente):
    """Webcam. La única fuente que puede no existir en la máquina.

    `disponible()` es un método de clase para poder preguntarlo **sin**
    construir la fuente: abrir un dispositivo que no está cuesta segundos en
    Windows y deja avisos de DirectShow por la consola, que en clase parecen
    errores del material.
    """

    def __init__(self, indice: int = 0, calentamiento: int = 5) -> None:
        import cv2

        self._captura = cv2.VideoCapture(indice)
        if not self._captura.isOpened():
            self._captura.release()
            raise OSError(
                f"no hay cámara en el índice {indice}. "
                f"Usa FuenteVideo o FuenteCarpeta, o mira mejor_fuente_disponible()."
            )
        self.nombre = f"camara:{indice}"
        # Las webcams devuelven fotogramas negros o mal expuestos hasta que el
        # autoexposición converge. Descartarlos evita que la Clase 1 arranque
        # analizando el histograma de una imagen negra.
        for _ in range(calentamiento):
            self._captura.read()

    @classmethod
    def disponible(cls, indice: int = 0) -> bool:
        try:
            import cv2
        except ImportError:
            return False
        captura = cv2.VideoCapture(indice)
        try:
            return bool(captura.isOpened())
        finally:
            captura.release()

    def leer(self) -> np.ndarray | None:
        hay, fotograma = self._captura.read()
        if not hay:
            return None
        return _bgr_a_rgb(fotograma)

    def cerrar(self) -> None:
        self._captura.release()


class FuenteMotor(Fuente):
    """Imágenes del videojuego: recursos de `assets/` o fotogramas capturados.

    Con `escena` se capturan fotogramas reales del motor en marcha (cierra el
    hueco H2); sin ella, se recorren los PNG de una categoría de `assets/`.
    """

    def __init__(
        self,
        categoria: str = "sprites",
        escena: str | None = None,
        maximo: int = 10,
        tamano: tuple[int, int] | None = None,
    ) -> None:
        from cvcourse import engine_bridge

        if not engine_bridge.hay_motor():
            raise RuntimeError(
                "FuenteMotor necesita el repositorio del motor. "
                "En Colab sin repositorio, usa FuenteSintetica."
            )

        self._imagenes: list[np.ndarray]
        if escena is not None:
            self._imagenes = engine_bridge.capturar_escena(escena, fotogramas=maximo)
            self.nombre = f"motor:escena:{escena}"
        else:
            rutas = engine_bridge.recursos(categoria)[:maximo]
            self._imagenes = [engine_bridge.cargar_imagen(r, tamano) for r in rutas]
            self.nombre = f"motor:{categoria} ({len(self._imagenes)} imágenes)"
        self._i = 0

    def leer(self) -> np.ndarray | None:
        if self._i >= len(self._imagenes):
            return None
        imagen = self._imagenes[self._i]
        self._i += 1
        return imagen.copy()


class FuenteSintetica(Fuente):
    """Piezas generadas. El último recurso, y el que nunca falla.

    Existe para que un notebook en Colab sin repositorio, sin cámara y sin
    datos siga siendo ejecutable de principio a fin. Un material docente que
    sólo funciona con la máquina bien preparada no es material docente.
    """

    def __init__(self, n: int = 10, tamano: int = 128, semilla: int = 0) -> None:
        from cvcourse.synthetic import lote_de_piezas

        imagenes, self.verdades = lote_de_piezas(n=n, tamano=tamano, semilla=semilla)
        # Se replican a 3 canales para cumplir el contrato de `Fuente` (RGB).
        self._imagenes = [np.repeat(i[:, :, None], 3, axis=2) for i in imagenes]
        self.nombre = f"sintetica ({n} piezas, semilla={semilla})"
        self._i = 0

    def leer(self) -> np.ndarray | None:
        if self._i >= len(self._imagenes):
            return None
        imagen = self._imagenes[self._i]
        self._i += 1
        return imagen.copy()


def mejor_fuente_disponible(
    preferencias: tuple[str, ...] = ("camara", "motor", "sintetica"),
    **opciones: object,
) -> Fuente:
    """Devuelve la primera fuente de la lista que se pueda abrir de verdad.

    Es la función que hace que el mismo notebook corra en el aula, en Colab y
    en CI. Degrada en silencio pero **deja constancia**: `fuente.nombre` dice
    siempre qué acabó usándose, y el material lo imprime en las figuras. Una
    degradación invisible sería peor que un fallo: el estudiante creería estar
    analizando su webcam mientras mira piezas sintéticas.
    """
    constructores = {
        "camara": lambda: FuenteCamara(int(opciones.get("indice", 0))),  # type: ignore[call-overload]
        "motor": lambda: FuenteMotor(str(opciones.get("categoria", "sprites"))),
        "sintetica": lambda: FuenteSintetica(int(opciones.get("n", 10))),  # type: ignore[call-overload]
    }

    desconocidas = set(preferencias) - set(constructores)
    if desconocidas:
        raise ValueError(
            f"preferencias desconocidas: {sorted(desconocidas)}. "
            f"Usa: {sorted(constructores)}"
        )

    for clave in preferencias:
        if clave == "camara" and not FuenteCamara.disponible(int(opciones.get("indice", 0))):  # type: ignore[call-overload]
            logger.info("acquisition: no hay cámara, se prueba la siguiente fuente")
            continue
        try:
            return constructores[clave]()
        except (OSError, RuntimeError, ImportError) as error:
            logger.info("acquisition: %s no disponible (%s)", clave, error)

    # `sintetica` no depende de nada externo, así que llegar aquí significa que
    # ni siquiera se pidió. Se dice, en vez de devolver None y fallar luego.
    raise RuntimeError(
        f"ninguna de las fuentes {preferencias} pudo abrirse. "
        f"Añade 'sintetica' a las preferencias: no depende de nada."
    )
