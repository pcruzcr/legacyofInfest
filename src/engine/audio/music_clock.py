"""
Module: music_clock
System: engine.audio
Academic Unit: N/A
Description: AUD-137 (F6) — el reloj musical: pulsos, compases, posición de
pista y compensación de latencia.

Por qué el juego no podía tener niveles rítmicos
=================================================
Se puede hacer un bloque que aparezca cada segundo. Lo que no se puede hacer
sin esto es que ese bloque aparezca **con la música**, y ésa es toda la
diferencia entre *Mega Man 2* y *Super Mario Bros. Wonder*.

El motivo es aritmético y se llama deriva. Un bloque que suma `dt` cada
fotograma cuenta su propio tiempo; la música cuenta el suyo, marcado por el
reloj de la tarjeta de sonido. Los dos relojes no van al mismo ritmo —ni
siquiera en la misma máquina—, así que al minuto de partida el bloque y el
compás llevan cien milisegundos de diferencia, que es más de lo que el oído
tolera. A los cinco minutos, medio compás.

La solución no es afinar el `dt`: es **dejar de contar**. La posición se
pregunta a quien reproduce la música, y todo lo demás se deriva de ahí.

Tres decisiones que hacen que esto sirva
-----------------------------------------
1. **La fuente es el audio, no el fotograma.** Con el mezclador parado
   —pruebas, un servidor sin tarjeta— se cae a acumular tiempo real, porque un
   reloj que se niega a funcionar sin altavoces no se puede probar.
2. **Tiempo REAL, nunca escalado.** El tiempo bala ralentiza el mundo; la
   música sigue sonando igual. Alimentar esto con el `dt` escalado haría que
   una ralentización desincronizara el nivel entero, y es exactamente el
   defecto que AUD-118/119 quitó del reloj del juego.
3. **La latencia se compensa y se puede calibrar.** Entre que el motor manda
   un sonido y el jugador lo oye pasan decenas de milisegundos, y varían con
   los cascos, el sistema y el mezclador. Sin un desfase ajustable, «a compás»
   significa cosas distintas en cada ordenador.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

#: Ventana por defecto para considerar que algo va «a compás», en segundos.
#:
#: 90 ms a cada lado. No es un número redondo por gusto: por debajo de unos
#: 50 ms el jugador no puede acertar de forma fiable ni con buen oído, y por
#: encima de 120 ms deja de sentirse rítmico y se siente permisivo. Los juegos
#: del género se mueven en esa banda.
VENTANA_POR_DEFECTO: float = 0.09


class RelojMusical:
    """Convierte la posición de la música en pulsos y compases.

    Uso típico::

        reloj = RelojMusical(bpm=128, compas=4)
        reloj.update(unscaled_dt)
        if reloj.pulsos_cruzados:
            ...algo pasa en cada pulso...
    """

    def __init__(self, bpm: float = 120.0, compas: int = 4,
                 desfase: float = 0.0, fuente: Any = None) -> None:
        self.bpm = max(1.0, float(bpm))
        self.compas = max(1, int(compas))
        #: Segundos que se restan a la posición para compensar la latencia.
        #: Positivo = el juego va por delante del sonido que se oye.
        self.desfase = float(desfase)
        #: Quien sabe por dónde va la música. Debe tener `posicion_musica()`
        #: en segundos, o devolver `None` si no lo sabe.
        self.fuente = fuente

        self._posicion = 0.0
        self._acumulado = 0.0
        self._pulso_anterior = -1
        self._pulsos_cruzados = 0
        self._corriendo = True
        #: Lo último que contestó la fuente, y cuánto tiempo lleva contestando
        #: lo mismo. Ver `_preguntar_al_audio` y `SEGUNDOS_DE_ATASCO`.
        self._ultima_cruda: float | None = None
        self._atascado: float = 0.0

    #: Cuánto puede repetir la fuente la misma posición antes de dejar de
    #: creerla (AUD-250).
    #:
    #: `posicion_musica()` devuelve `None` cuando no hay música, y de ese caso
    #: el reloj ya se defendía. Lo que no estaba previsto es que **conteste y no
    #: avance**: `pygame.mixer.music.get_pos()` devuelve 0 para siempre con el
    #: controlador `dummy`, y también cuando el mezclador se queda colgado. El
    #: reloj se creía ese 0, se quedaba clavado en el pulso 0 y **todos los
    #: bloques rítmicos del juego se quedaban sólidos para siempre** — los tres
    #: de `stage0` incluidos.
    #:
    #: Un cuarto de segundo es más de lo que tarda cualquier pista real en mover
    #: su posición, y lo bastante corto para que el nivel arranque a tiempo.
    SEGUNDOS_DE_ATASCO = 0.25

    # ── configuración ────────────────────────────────────────────
    @property
    def segundos_por_pulso(self) -> float:
        return 60.0 / self.bpm

    @property
    def segundos_por_compas(self) -> float:
        return self.segundos_por_pulso * self.compas

    def reiniciar(self) -> None:
        self._posicion = 0.0
        self._acumulado = 0.0
        self._pulso_anterior = -1
        self._pulsos_cruzados = 0

    def alinear(self, posicion: float) -> None:
        """Fija la posición a mano. Para cuando la pista cambia o da la vuelta."""
        self._acumulado = max(0.0, float(posicion))
        self._posicion = self._acumulado
        self._pulso_anterior = int(self._posicion / self.segundos_por_pulso)
        self._pulsos_cruzados = 0

    # ── ciclo ─────────────────────────────────────────────────────
    def update(self, unscaled_dt: float) -> None:
        """Avanza el reloj. **Con `dt` sin escalar**, siempre.

        Si se le pasa el `dt` del juego, una ralentización desincroniza el
        nivel entero: los bloques van al ralentí y la música no.
        """
        paso = max(0.0, float(unscaled_dt))
        self._acumulado += paso
        cruda = self._preguntar_al_audio()

        # AUD-250 — una fuente que contesta siempre lo mismo no está diciendo
        # por dónde va la música: está atascada. Con `SDL_AUDIODRIVER=dummy`
        # `get_pos()` devuelve 0 para siempre, y el reloj se lo creía.
        if cruda is not None and cruda == self._ultima_cruda:
            self._atascado += paso
            if self._atascado >= self.SEGUNDOS_DE_ATASCO:
                cruda = None
        else:
            self._atascado = 0.0
        if cruda is not None:
            self._ultima_cruda = cruda

        if cruda is None:
            cruda = self._acumulado
        else:
            # Mantener el acumulado cerca del audio evita un salto brusco el
            # día que el mezclador deje de contestar a mitad de partida.
            self._acumulado = cruda

        nueva = max(0.0, cruda - self.desfase)
        anterior = self._posicion
        self._posicion = nueva

        pulso_ahora = int(nueva / self.segundos_por_pulso)
        if nueva < anterior:
            # La pista dio la vuelta o alguien la reinició: no se pueden
            # contar pulsos hacia atrás.
            self._pulsos_cruzados = 0
            self._pulso_anterior = pulso_ahora
            return
        # `_pulso_anterior` empieza en -1 a propósito: así el primer `update`
        # cruza el pulso 0 y el primer tiempo del nivel también suena. Si
        # empezara en 0, el compás inicial se perdería y nadie sabría por qué.
        self._pulsos_cruzados = max(0, pulso_ahora - self._pulso_anterior)
        self._pulso_anterior = pulso_ahora

    def _preguntar_al_audio(self) -> float | None:
        fuente = self.fuente
        if fuente is None:
            return None
        preguntar = getattr(fuente, "posicion_musica", None)
        if not callable(preguntar):
            return None
        try:
            valor = preguntar()
        except Exception:  # pragma: no cover - una fuente rota no para el juego
            logger.debug("la fuente de música falló al dar su posición",
                         exc_info=True)
            return None
        if valor is None or valor < 0:
            return None
        return float(valor)

    # ── lectura ───────────────────────────────────────────────────
    @property
    def posicion(self) -> float:
        """Segundos de pista, ya compensados."""
        return self._posicion

    @property
    def pulso(self) -> float:
        """Posición en pulsos, con decimales."""
        return self._posicion / self.segundos_por_pulso

    @property
    def pulso_actual(self) -> int:
        return int(self.pulso)

    @property
    def compas_actual(self) -> int:
        return self.pulso_actual // self.compas

    @property
    def pulso_en_compas(self) -> int:
        """0 en el primer tiempo del compás. El 0 es el que se acentúa."""
        return self.pulso_actual % self.compas

    @property
    def fraccion(self) -> float:
        """Cuánto se lleva recorrido del pulso actual, de 0 a 1."""
        return self.pulso - self.pulso_actual

    @property
    def pulsos_cruzados(self) -> int:
        """Cuántos pulsos empezaron en el último `update`.

        Es un contador y no un booleano por lo mismo que AUD-116: con un
        fotograma largo —una carga, un punto de interrupción— pueden pasar dos
        pulsos de golpe, y un booleano se comería el segundo.
        """
        return self._pulsos_cruzados

    @property
    def acaba_de_empezar_compas(self) -> bool:
        return self._pulsos_cruzados > 0 and self.pulso_en_compas == 0

    # ── ayuda para el diseño ──────────────────────────────────────
    def tiempo_hasta_el_proximo_pulso(self) -> float:
        return (1.0 - self.fraccion) * self.segundos_por_pulso

    def distancia_al_pulso(self) -> float:
        """Segundos hasta el pulso más cercano, hacia delante o hacia atrás.

        Los dos lados cuentan: llegar 40 ms tarde y llegar 40 ms pronto suenan
        igual de bien, y un juego que sólo perdonara una de las dos direcciones
        castigaría exactamente a quien se está anticipando a la música.
        """
        spp = self.segundos_por_pulso
        desde = self.fraccion * spp
        return min(desde, spp - desde)

    def en_ventana(self, tolerancia: float = VENTANA_POR_DEFECTO) -> bool:
        """`True` si ahora mismo se está «a compás».

        Es lo que convierte un salto en un salto rítmico: el juego no exige el
        instante exacto —nadie acierta el instante exacto— sino una ventana.
        """
        return self.distancia_al_pulso() <= max(0.0, tolerancia)

    def cuantizar(self, segundos: float) -> float:
        """Redondea un instante al pulso más cercano.

        Sirve para programar cosas: «que la puerta se abra en el próximo
        pulso» en vez de «dentro de 0,3 s», que es lo que suena mal.
        """
        pulsos = round(segundos / self.segundos_por_pulso)
        return pulsos * self.segundos_por_pulso

    def presente_en_patron(self, patron: str, desfase_pulsos: float = 0.0) -> bool:
        """Lee un patrón de compás: `"x.x."` es sí, no, sí, no.

        Es la forma más corta que hay de escribir un ritmo en una propiedad de
        Tiled, y se lee de un vistazo — que es más de lo que puede decirse de
        dos números en segundos.

        `desfase_pulsos` corre el patrón para esta pieza en concreto (AUD-250).
        Sin él, **todos los bloques que comparten patrón aparecen y desaparecen
        a la vez**, que es un semáforo y no un ritmo: el `desfase` que el TMX ya
        aceptaba sólo se usaba en el modo por segundos y se perdía en cuanto se
        escribía un `patron`. Cinco losas escalonadas para que bajando persigas
        la que acaba de aparecer debajo salían las cinco en el mismo pulso.
        """
        limpio = [c for c in str(patron) if c in "x.Xo0-"]
        if not limpio:
            return True
        indice = int(self.pulso_actual + desfase_pulsos) % len(limpio)
        return limpio[indice] in "xXo"
