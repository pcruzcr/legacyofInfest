"""
Module: mixer_buses
System: engine.audio
Academic Unit: N/A
Description: AUD-144 — buses de mezcla y *ducking*: agachar la música cuando
alguien habla.

Qué es un bus y por qué hacía falta
====================================
Hasta ahora había dos volúmenes —música y efectos— y todo lo demás colgaba de
uno de los dos. Con eso no se puede resolver el problema básico de la mezcla
de un juego: **que la voz se oiga**. Subir la voz la deja gritando en las
escenas tranquilas; bajar la música la deja inaudible en las de acción.

Un bus es un grupo de sonidos con su propio volumen, y el volumen que se
aplica a un sonido es el producto de tres cosas:

    volumen final = maestro × bus × el que pida quien lo reproduce

Los cuatro buses no son un capricho de arquitectura: son las cuatro cosas que
compiten por la atención del jugador, y cada una necesita ceder ante otra en
algún momento.

El *ducking*, o por qué esto se nota
-------------------------------------
Cuando el bus de voz suena, el de música baja al 35 % en 0,15 s y vuelve en
0,5 s. Es el truco más viejo de la radio y sigue siendo el que más se nota:
sin él, el jugador **sube el volumen para oír el diálogo** y luego se lleva
un susto con el siguiente golpe.

Las dos constantes están elegidas, no puestas al azar:

* **Bajar rápido (0,15 s)**: si la música tarda en apartarse, se come la
  primera palabra, que suele ser la que dice de quién es la frase.
* **Volver despacio (0,5 s)**: subir de golpe al terminar de hablar suena a
  fallo técnico. Volviendo despacio, nadie nota que hubo un *duck*, que es la
  señal de que está bien hecho.

Lo que NO se puede hacer en pygame, dicho sin adornos
------------------------------------------------------
**Reverberación por zona no.** El mezclador de SDL no tiene efectos: reproduce
muestras y las suma. Una reverberación de verdad exige convolucionar cada
sonido con la respuesta al impulso de la sala, y eso hay que hacerlo o bien
sobre la muestra al cargarla —dos copias de cada sonido, una seca y otra por
zona— o bien con una biblioteca de DSP externa.

Prometer «reverberación por zona» encima de este mezclador sería exactamente
el tipo de afirmación que este mes ha habido que corregir dos veces. Aquí
está lo que sí hay: buses y *ducking*, medibles y probados.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

#: Los cuatro grupos que compiten por la atención del jugador.
BUS_MUSICA: str = "musica"
BUS_EFECTOS: str = "efectos"
BUS_VOZ: str = "voz"
BUS_AMBIENTE: str = "ambiente"

BUSES: tuple[str, ...] = (BUS_MUSICA, BUS_EFECTOS, BUS_VOZ, BUS_AMBIENTE)

#: Volúmenes de partida. La música por debajo de los efectos a propósito: un
#: golpe tiene que oírse por encima de la canción o el combate se vuelve sordo.
POR_DEFECTO: dict[str, float] = {
    BUS_MUSICA: 0.7,
    BUS_EFECTOS: 1.0,
    BUS_VOZ: 1.0,
    BUS_AMBIENTE: 0.5,
}

#: Cuánto baja la música mientras alguien habla.
DUCK_NIVEL: float = 0.35

#: Cuánto baja la música bajo un efecto **crítico** (AUD-284): un 30 %.
#:
#: Mucho más suave que el de la voz, y por una razón: bajo una línea de diálogo
#: la música estorba y hay que apartarla; bajo la muerte de un jefe la música
#: **es parte del momento** y apagarla lo desinfla. Lo que se busca aquí es
#: espacio para que el golpe se oiga entero, no silencio.
DUCK_NIVEL_EFECTO: float = 0.70

#: Cuánto dura el hueco que abre un efecto crítico.
#:
#: Un segundo: lo que tarda en apagarse la cola de un sonido grande. Con menos,
#: la música vuelve encima del propio efecto que motivó apartarla.
DUCK_EFECTO_SEGUNDOS: float = 1.0
#: Segundos en bajar. Corto: si tarda, se come la primera palabra.
DUCK_ATAQUE: float = 0.15
#: Segundos en volver. Largo: subir de golpe suena a fallo técnico.
DUCK_RECUPERACION: float = 0.5


class Mezclador:
    """Volúmenes por bus, con *ducking* de la música bajo la voz."""

    def __init__(self) -> None:
        self._volumenes: dict[str, float] = dict(POR_DEFECTO)
        self._maestro: float = 1.0
        self._silencio: bool = False
        #: 1.0 = música a su volumen; DUCK_NIVEL = agachada del todo.
        self._duck: float = 1.0
        self._duck_pedido: bool = False
        self._duck_restante: float = 0.0
        #: AUD-284 — hasta dónde baja el duck vivo. Voz 0,35; efecto 0,70.
        self._duck_nivel: float = DUCK_NIVEL
        #: AUD-310 — la petición persistente (diálogo) vive aparte de la
        #: temporizada. Antes ambas compartían `_duck_pedido`, y la expiración
        #: del temporizador de un efecto crítico soltaba también el duck que el
        #: diálogo había pedido sin duración: la música volvía a pleno volumen
        #: a mitad de la línea de voz.
        self._duck_persistente: bool = False
        self._duck_nivel_persistente: float = DUCK_NIVEL

    # ── volúmenes ─────────────────────────────────────────────────
    def volumen_de(self, bus: str) -> float:
        return self._volumenes.get(bus, 1.0)

    def ajustar(self, bus: str, volumen: float) -> None:
        if bus not in self._volumenes:
            logger.warning("bus de audio desconocido: %r", bus)
            return
        self._volumenes[bus] = max(0.0, min(1.0, float(volumen)))

    @property
    def maestro(self) -> float:
        return self._maestro

    @maestro.setter
    def maestro(self, valor: float) -> None:
        self._maestro = max(0.0, min(1.0, float(valor)))

    @property
    def silencio(self) -> bool:
        return self._silencio

    @silencio.setter
    def silencio(self, valor: bool) -> None:
        self._silencio = bool(valor)

    def ganancia(self, bus: str, volumen_pedido: float = 1.0) -> float:
        """El volumen que hay que darle a un sonido de ese bus, de 0 a 1.

        Es el único sitio donde se multiplican las tres cosas. Que sea uno
        solo es lo que permite que el *ducking* y el silencio se apliquen a
        todo sin que cada llamada tenga que acordarse.
        """
        if self._silencio:
            return 0.0
        ganancia = self._maestro * self.volumen_de(bus) * max(0.0, volumen_pedido)
        if bus == BUS_MUSICA:
            ganancia *= self._duck
        return max(0.0, min(1.0, ganancia))

    # ── ducking ───────────────────────────────────────────────────
    def agachar_musica(self, segundos: float = 0.0,
                       nivel: float = DUCK_NIVEL) -> None:
        """Pide que la música se aparte, y cuánto.

        Con `segundos` se mantiene ese tiempo y se suelta sola: es lo que usa
        una línea de diálogo, que sabe lo que dura. Sin argumento se queda
        agachada hasta que alguien llame a `soltar_musica`, para lo que no
        tiene duración conocida.

        AUD-284 — `nivel` existe porque no todo lo que aparta la música la
        aparta igual. Una voz necesita silencio (0,35); un efecto crítico sólo
        necesita hueco (0,70). **Gana siempre el más profundo** mientras los dos
        estén vivos: si la muerte de un jefe subiera la música por encima de la
        línea de diálogo que está sonando, el diálogo se perdería, y quien pide
        silencio tiene más que perder que quien pide sitio.
        """
        nivel = max(0.0, min(1.0, float(nivel)))
        if segundos > 0.0:
            self._duck_nivel = min(self._duck_nivel, nivel) if self._duck_pedido else nivel
            self._duck_pedido = True
            self._duck_restante = max(self._duck_restante, float(segundos))
        else:
            # AUD-310 — petición persistente: guarda su propio nivel para poder
            # restaurarlo cuando expire un duck temporizado pedido encima.
            self._duck_nivel_persistente = (
                min(self._duck_nivel_persistente, nivel)
                if self._duck_persistente else nivel
            )
            self._duck_nivel = min(self._duck_nivel, nivel) if self._duck_pedido else nivel
            self._duck_persistente = True
            self._duck_pedido = True

    def soltar_musica(self) -> None:
        self._duck_pedido = False
        self._duck_persistente = False
        self._duck_restante = 0.0
        self._duck_nivel = DUCK_NIVEL

    @property
    def musica_agachada(self) -> bool:
        return self._duck < 0.999

    @property
    def factor_de_duck(self) -> float:
        return self._duck

    def update(self, dt: float) -> None:
        """Mueve el *duck* hacia donde toque. Con `dt` real, no escalado.

        El tiempo bala ralentiza el mundo; la mezcla no se ralentiza con él.
        """
        if dt <= 0.0:
            return
        if self._duck_restante > 0.0:
            self._duck_restante -= dt
            if self._duck_restante <= 0.0:
                # AUD-310 — expirar un temporizado no libera una petición
                # persistente: si el diálogo sigue abierto, se restaura su
                # nivel; si no, la música vuelve arriba del todo.
                self._duck_restante = 0.0
                if self._duck_persistente:
                    self._duck_nivel = self._duck_nivel_persistente
                else:
                    self._duck_pedido = False
                    self._duck_nivel = DUCK_NIVEL

        objetivo = self._duck_nivel if self._duck_pedido else 1.0
        if self._duck == objetivo:
            return
        # Bajar y subir a velocidades distintas: es lo que hace que el duck
        # no se note. Con la misma velocidad en ambos sentidos se oye el
        # bombeo, que es el defecto clásico de un compresor mal ajustado.
        #
        # AUD-284 — el paso se calcula sobre el recorrido **más profundo** y no
        # sobre el de este duck en concreto. Si se normalizara por su propio
        # recorrido, un duck superficial tardaría lo mismo que uno profundo en
        # llegar, o sea que iría mucho más lento: dos efectos idénticos sonarían
        # distinto según lo hondo que bajen.
        duracion = DUCK_ATAQUE if objetivo < self._duck else DUCK_RECUPERACION
        paso = (1.0 - DUCK_NIVEL) * dt / max(0.01, duracion)
        if objetivo < self._duck:
            self._duck = max(objetivo, self._duck - paso)
        else:
            self._duck = min(objetivo, self._duck + paso)
