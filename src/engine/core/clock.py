"""
Module: clock
System: engine.core
Academic Unit: N/A
Description: Wrapper around pygame.time.Clock providing delta time
scaled by a time_scale factor.

Two deltas are exposed every frame:

``dt``        — scaled by ``time_scale``. Drives gameplay simulation, so
                slow-motion and hit-stop affect it.
``unscaled_dt`` — the real elapsed wall-clock time, unaffected by
                ``time_scale``. Drives anything that must keep running while
                the simulation is slowed or frozen: the hit-stop timer itself,
                UI animation, transitions and pause menus.
``dt_mundo``  — scaled by everything **except** the hit-stop freeze. Drives
                the level's clockwork: rhythm blocks, lasers, moving
                platforms. See AUD-119 below.

BUGFIX (AUD-001): systems that *end* a freeze must never be driven by the
scaled delta. Previously ``time_scale`` was set to 0.0 during hit-stop, which
made ``dt`` 0.0, which meant the hit-stop countdown decremented by 0.0 and
therefore never expired — the game locked up permanently on the first landed
hit. ``unscaled_dt`` exists so that class of self-deadlock is impossible.

AUD-118 — dos dueños para un solo número
=========================================
``time_scale`` era un ``float`` público que **dos** sistemas escribían sin
saber el uno del otro: el hit-stop del sistema de colisiones y la cámara lenta
de `TiempoBala`. Cada uno restauraba «1.0» al terminar, que es la suposición
de que nadie más había tocado el reloj.

Medido: con la cámara lenta activa a 0,35, golpear a un enemigo daba
``0.35 → 0.0 → 1.0``. El fotograma siguiente volvía a 0,35, así que el jugador
veía **un fotograma a velocidad completa en mitad de la cámara lenta**, justo
en el instante del impacto — el peor momento posible para un tirón.

Los dos comentarios que ya había en el código sobre «quién es el dueño de
``time_scale``» son la señal de que el problema se había mordido dos veces y
se había parcheado las dos. La cura no es un tercer parche: es que deje de
haber un dueño. Ahora cada efecto registra su factor **con su nombre** y la
escala efectiva es el producto. Componer es asociativo y nadie pisa a nadie.

AUD-119 — el hit-stop congelaba la maquinaria del nivel
========================================================
El planificador ECS recibía el ``dt`` escalado, así que los 50 ms de hit-stop
de cada golpe también paraban los bloques rítmicos, los láseres y las
plataformas móviles. Dos consecuencias:

* **Exploit.** Golpear a un enemigo junto a un láser detenía el láser.
* **Desincronización acumulada.** En un nivel a compás, cada golpe atrasa la
  maquinaria respecto a la música y nada lo corrige nunca.

El hit-stop es un efecto de *presentación* —congela a los implicados en el
golpe para darle peso—, no un cambio en el tiempo del mundo. La cámara lenta
sí es un cambio en el tiempo del mundo, y por eso ``dt_mundo`` la respeta y
al hit-stop no.
"""
from __future__ import annotations

from collections import deque

import pygame

from src.engine.core import settings

# Longest simulation step we will ever report. Protects the fixed-ish
# integrators in the player/enemy state machines from tunnelling through
# geometry after a stall (breakpoint, window drag, GC pause, disk hitch).
MAX_FRAME_TIME: float = 0.05  # 20 FPS floor

#: AUD-390 — el paso de simulación. Cierra GAP-036.
#:
#: Es `1/TARGET_FPS` y no otro número, y la elección es la clave del lote. Los
#: dieciséis mapas están medidos contra los **72 px** de salto que se alcanzan
#: a 60 fps; con este paso, a 60 fps la integración es **idéntica** a la del
#: `dt` variable de antes —un paso por fotograma, del mismo tamaño— y ningún
#: mapa cambia. Cualquier otro valor habría obligado a re-calibrar de verdad.
#:
#: Lo que sí cambia es el fotograma lento. Antes, un tirón se integraba de una
#: vez con un `dt` grande, y la altura del salto bajaba con él:
#:
#:     120 fps -> 88,67 px | 60 fps -> 87,11 | 30 fps -> 84,00 | 20 fps -> 81,00
#:
#: O sea que **el juego se jugaba distinto según la máquina**, y un obstáculo
#: ajustado al límite era franqueable o no según el equipo. Ahora ese mismo
#: tirón se reparte en varios pasos de `FIXED_DT` y el resultado converge al
#: que los mapas suponen.
FIXED_DT: float = 1.0 / settings.TARGET_FPS

#: Tope de pasos por fotograma, contra la espiral de la muerte: si simular
#: cuesta más que el tiempo simulado, el acumulador crece sin fin y el juego se
#: congela intentando alcanzarse a sí mismo. Con 5 pasos se cubre un tirón de
#: 83 ms —más que el `MAX_FRAME_TIME` de 50— y por encima de eso se prefiere
#: ir a cámara lenta antes que dejar de responder.
MAX_PASOS_POR_FOTOGRAMA: int = 5

#: Cuántos fotogramas guarda el historial para los cuantiles de F11 (AUD-346).
#: 180 a 60 FPS son 3 segundos: bastante para separar el tropezón de la
#: tendencia, y poco para que la memoria no sea parte de la medición.
FOTOGRAMAS_EN_EL_HISTORIAL: int = 180

#: Nombre de la fuente del hit-stop. `dt_mundo` la ignora a propósito.
FUENTE_HITSTOP: str = "hitstop"

#: Fuente que usa el asignador directo `clock.time_scale = x`, que se conserva
#: porque las 26 clases de escenario de los estudiantes lo escriben así.
FUENTE_MANUAL: str = "manual"


class DeltaClock:
    """Delta time en segundos, escalado por la composición de efectos activos."""

    def __init__(self) -> None:
        self._clock = pygame.time.Clock()
        self._escalas: dict[str, float] = {}
        #: AUD-390 — tiempo pendiente de simular, entre 0 y FIXED_DT.
        self._acumulado: float = 0.0
        self._dt: float = 0.0
        self._unscaled_dt: float = 0.0
        self._dt_mundo: float = 0.0
        # AUD-346 — los milisegundos reales de los últimos fotogramas, para
        # los cuantiles de la consola (F11). El deque recorta solo.
        self._historial: deque[float] = deque(
            maxlen=FOTOGRAMAS_EN_EL_HISTORIAL)

    # ── Composición de escalas ────────────────────────────────────────

    def escalar(self, fuente: str, valor: float) -> None:
        """Registra que `fuente` quiere el tiempo a `valor`.

        Varias fuentes se **multiplican**. Cámara lenta a 0,35 más hit-stop a
        0,0 da 0,0; al soltar el hit-stop vuelve a 0,35 y no a 1,0, que es el
        defecto que esto corrige.
        """
        self._escalas[fuente] = max(0.0, float(valor))

    def restaurar(self, fuente: str) -> None:
        """Retira el factor de `fuente`. Retirar lo que no está no es error."""
        self._escalas.pop(fuente, None)

    def _producto(self, excluir: str | None = None) -> float:
        total = 1.0
        for nombre, valor in self._escalas.items():
            if nombre != excluir:
                total *= valor
        return total

    @property
    def time_scale(self) -> float:
        """La escala efectiva: el producto de todos los efectos activos."""
        return self._producto()

    @time_scale.setter
    def time_scale(self, valor: float) -> None:
        """Compatibilidad con `clock.time_scale = x`.

        Asignar 1.0 **retira** la fuente manual en vez de registrar un factor
        neutro, para que el diccionario no crezca con entradas inertes y para
        que `escalas_activas()` diga la verdad en el depurador.
        """
        if valor == 1.0:
            self.restaurar(FUENTE_MANUAL)
        else:
            self.escalar(FUENTE_MANUAL, valor)

    def escalas_activas(self) -> dict[str, float]:
        """Copia de lo que hay ahora mismo. Para depurar y para las pruebas."""
        return dict(self._escalas)

    # ── Fotograma ─────────────────────────────────────────────────────

    def tick(self) -> float:
        """Avanza un fotograma y devuelve el delta *escalado*."""
        raw_dt = min(self._clock.tick(settings.TARGET_FPS) / 1000.0, MAX_FRAME_TIME)
        self._unscaled_dt = raw_dt
        self._dt = raw_dt * self.time_scale
        self._dt_mundo = raw_dt * self._producto(excluir=FUENTE_HITSTOP)
        # AUD-346 — se guarda lo **real**, no lo escalado: la pregunta de la
        # consola es «cuánto duró el fotograma», no «a qué velocidad iba el
        # mundo» (la cámara lenta la contaría como un fotograma rápido).
        self._historial.append(raw_dt * 1000.0)
        return self._dt

    def pasos_fijos(self, dt: float | None = None):
        """Los pasos de simulación que toca dar para el tiempo transcurrido.

        AUD-390 — el acumulador. Devuelve `FIXED_DT` tantas veces como quepa en
        el tiempo acumulado, **guardando el sobrante** para el fotograma
        siguiente. Sin guardarlo, a 120 fps la mitad de los fotogramas no
        simularían y el juego iría a la mitad de velocidad.

        Con `dt` a `None` usa el del último `tick()`, que es lo que hace el
        bucle; se puede pasar uno para las pruebas.

        Se consume el escalado (`self.dt`) y no el real, porque la cámara lenta
        y el hit-stop tienen que seguir funcionando: ralentizar el mundo es dar
        **menos** pasos por segundo real, no pasos más cortos — pasos más
        cortos volverían a hacer la física dependiente del reloj, que es
        justamente lo que este cambio quita.

        El tope corta la espiral de la muerte. Cuando se alcanza, el tiempo
        sobrante se **tira**: conservarlo dejaría una deuda que el fotograma
        siguiente tampoco puede pagar, y el juego se quedaría clavado
        intentando alcanzarse a sí mismo. Se prefiere ir a cámara lenta antes
        que dejar de responder.
        """
        self._acumulado += self._dt if dt is None else float(dt)
        dados = 0
        while self._acumulado >= FIXED_DT and dados < MAX_PASOS_POR_FOTOGRAMA:
            self._acumulado -= FIXED_DT
            dados += 1
            yield FIXED_DT
        if dados >= MAX_PASOS_POR_FOTOGRAMA:
            self._acumulado = 0.0

    def historial_ms(self) -> tuple[float, ...]:
        """Los milisegundos reales de los últimos fotogramas (AUD-346)."""
        return tuple(self._historial)

    def estadisticas(self) -> dict[str, float]:
        """P50/P95/P99/media/peor del historial. Vacío si aún no hay nada."""
        from src.engine.core.estadisticas import cuantiles
        return cuantiles(self._historial)

    @property
    def dt(self) -> float:
        """Delta escalado del fotograma actual (lo que devolvió `tick`)."""
        return self._dt

    @property
    def unscaled_dt(self) -> float:
        """Tiempo real del fotograma, ignorando toda escala.

        Para los temporizadores cuyo trabajo es *restaurar* el flujo normal.
        """
        return self._unscaled_dt

    @property
    def dt_mundo(self) -> float:
        """Delta para la maquinaria del nivel: respeta la cámara lenta, no el hit-stop.

        Bloques rítmicos, láseres, plataformas móviles y cintas. Un efecto de
        presentación de 50 ms no debe mover el reloj del escenario.
        """
        return self._dt_mundo

    @property
    def fps(self) -> float:
        """Fotogramas por segundo actuales."""
        return self._clock.get_fps()
