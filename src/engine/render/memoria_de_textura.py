"""Cuánta memoria de textura hay viva, y si deja de bajar — AUD-397.

Cierra la mitad que le faltaba a `GAP-049`. La entrada decía:

    Hay medición de **tiempo** por todas partes […] y ninguna de **recursos**:
    nadie cuenta llamadas de dibujo por fotograma, ni cuánta memoria de textura
    hay viva, ni detecta que una superficie no se libera.

Las llamadas de dibujo se cerraron en AUD-377. Esto es lo otro.

Por qué es un módulo aparte y no dos atributos en `GLRenderer`
==============================================================
Porque así se puede **probar sin GPU**. `gl_pipeline.py` necesita un contexto
ModernGL para casi todo, y en CI no hay ninguno: cualquier medición que viviera
dentro de esa clase sería código que nadie ejecuta hasta que alguien abra el
juego en una máquina con tarjeta — exactamente la clase de instrumentación que
se rompe sin que nadie se entere, y que es lo que este hueco pedía evitar.

Aquí no se toca OpenGL. Se registran objetos que declaran `size` y
`components`, y eso lo cumple una textura de ModernGL igual que un doble de
tres líneas.

Qué cuenta como fuga
====================
No «hay mucha memoria»: eso depende del nivel y de la resolución, y un umbral
absoluto sería un número inventado. Lo que delata una fuga es la **forma** de
la serie: memoria que sube y nunca baja a lo largo de muchos fotogramas del
mismo escenario. `parece_fuga()` responde a eso y nada más.
"""
from __future__ import annotations

from typing import Any, Protocol

__all__ = ["MemoriaDeTexturas", "TexturaMedible", "bytes_de"]


class TexturaMedible(Protocol):
    """Lo mínimo para poder pesar una textura.

    Lo cumple `moderngl.Texture` sin adaptador. Se declara como `Protocol` para
    no importar ModernGL aquí: este módulo tiene que poder importarse en una
    máquina sin OpenGL, que es donde corre la suite.
    """

    size: tuple[int, int]
    components: int


#: Bytes por componente de los tipos que usa la tubería. `f1` es un byte sin
#: signo por canal, que es lo que pide `_subir` y lo que llevan los adjuntos de
#: color de los framebuffers.
_BYTES_POR_DTYPE: dict[str, int] = {"f1": 1, "f2": 2, "f4": 4, "u1": 1, "i1": 1}


def bytes_de(textura: Any, dtype: str = "f1") -> int:
    """Cuánto ocupa una textura, en bytes.

    Ancho × alto × componentes × bytes-por-componente. No incluye *mipmaps*
    —la tubería no genera ninguno— y ése es el motivo de que la cuenta sea
    exacta y no una estimación: el día que se generen, esto miente y hay que
    volver aquí.
    """
    ancho, alto = textura.size
    componentes = getattr(textura, "components", 4)
    return ancho * alto * componentes * _BYTES_POR_DTYPE.get(dtype, 1)


class MemoriaDeTexturas:
    """Registro de las texturas vivas y de su peso.

    Se lleva a mano —`registrar` al crear, `soltar` al liberar— y no con
    referencias débiles a propósito: lo que interesa medir es exactamente el
    par crear/liberar que escribe la tubería, y una textura que el recolector
    de Python barra sin que nadie llamara a `release()` **es** la fuga que hay
    que ver, no un caso que haya que disimular.
    """

    __slots__ = ("_historial", "_pico", "_vivas")

    #: Cuántos fotogramas de historial se guardan para juzgar la tendencia.
    #: Diez segundos a 60 Hz: por debajo, una carga de nivel se confunde con
    #: una fuga; por encima, el aviso llega tarde para servir de algo.
    VENTANA = 600

    def __init__(self) -> None:
        #: textura -> bytes.
        #:
        #: La primera versión indexaba por `id()`, y estaba mal: CPython
        #: **reutiliza** los identificadores de los objetos que recolecta, así
        #: que cinco texturas creadas y soltadas en un bucle se contaban como
        #: tres. Lo cazó `test_cuenta_las_texturas_vivas` en la primera
        #: ejecución, y es un defecto que en producción habría dado un contador
        #: que subestima justo cuando más rota hay — que es cuando se mira.
        #:
        #: Guardar el objeto mantiene una referencia fuerte, y eso es
        #: deliberado: una textura que el recolector se lleve sin que nadie
        #: llamara a `release()` **es** la fuga que hay que ver. En el camino
        #: sano `soltar` la quita y no queda nada.
        self._vivas: dict[Any, int] = {}
        self._pico: int = 0
        self._historial: list[int] = []

    # -- registro ---------------------------------------------------
    def registrar(self, textura: Any, dtype: str = "f1") -> None:
        """Da de alta una textura recién creada."""
        self._vivas[textura] = bytes_de(textura, dtype)
        self._pico = max(self._pico, self.bytes_vivos)

    def soltar(self, textura: Any) -> None:
        """Da de baja una textura liberada. Soltar dos veces no estalla."""
        self._vivas.pop(textura, None)

    def olvidar_todo(self) -> None:
        """Tras destruir el contexto entero: todas las texturas se fueron."""
        self._vivas.clear()
        self._historial.clear()
        self._pico = 0

    # -- lectura ----------------------------------------------------
    @property
    def bytes_vivos(self) -> int:
        return sum(self._vivas.values())

    @property
    def texturas_vivas(self) -> int:
        return len(self._vivas)

    @property
    def pico_de_bytes(self) -> int:
        """El máximo alcanzado. Es la cifra que decide si algo cabe en una
        tarjeta modesta — la instantánea de ahora mismo no dice nada."""
        return self._pico

    def anotar_fotograma(self) -> None:
        """Guarda la marca de este fotograma, para juzgar la tendencia."""
        self._historial.append(self.bytes_vivos)
        if len(self._historial) > self.VENTANA:
            del self._historial[: len(self._historial) - self.VENTANA]

    def parece_fuga(self, minimo_de_fotogramas: int = 120) -> bool:
        """¿La memoria sube y no baja nunca?

        Deliberadamente **no** hay umbral absoluto de bytes: cuánta memoria es
        «mucha» depende del nivel y de la resolución, y cualquier número que
        pusiera aquí sería inventado. Lo que delata una fuga es la forma de la
        serie, no su altura.

        Se pide un mínimo de fotogramas porque los primeros de un escenario
        **siempre** suben —se están subiendo las texturas del nivel— y llamar
        fuga a eso sería un aviso que se aprende a ignorar, que es peor que no
        avisar.
        """
        if len(self._historial) < minimo_de_fotogramas:
            return False
        primero, ultimo = self._historial[0], self._historial[-1]
        if ultimo <= primero:
            return False
        # Monótona no decreciente: ni una sola devolución de memoria en toda la
        # ventana. Una tubería sana suelta y vuelve a reservar al cambiar de
        # tamaño, así que algún escalón hacia abajo aparece siempre.
        # `strict=False` y no `True`: las dos vistas se desplazan una posición
        # a propósito, así que tienen longitudes distintas por construcción.
        return all(b >= a for a, b in zip(
            self._historial, self._historial[1:], strict=False))

    def resumen(self) -> str:
        """Una línea para el panel de depuración."""
        mib = self.bytes_vivos / (1024 * 1024)
        pico = self._pico / (1024 * 1024)
        return f"{mib:.1f} MiB en {self.texturas_vivas} texturas (pico {pico:.1f})"
