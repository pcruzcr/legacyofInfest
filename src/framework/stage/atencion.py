"""Atención del jugador: dónde está, hacia dónde mira y cuánto lleva quieto.

Por qué existe (AUD-492, GAP-065 §13 eslabón F4)
=================================================
La revisión de diseño del 4-1 describe seis eslabones en la relación
jugador↔escenario. Cinco están construidos en algún grado; el cuarto —«el
escenario parece observar al jugador»— es el único que **no existía en
absoluto**, y el GAP-065 lo dice con esas palabras: no hay ningún código que
lea la posición, la dirección o el tiempo de quietud del jugador para decidir
un evento. Los gritos y las sombras del Gavilán corrían en temporizadores
aleatorios, ciegos a lo que hacía el jugador; el escenario no observaba a
nadie, sólo lo parecía por casualidad temporal.

Un temporizador aleatorio y un escenario que observa producen la misma
secuencia de eventos vista desde fuera. La diferencia está en si el evento
guarda alguna relación con lo que el jugador acababa de hacer — y ésa es
justamente la relación que el jugador detecta a la tercera vez.

Por qué en el framework y no en `stages/stage4_1/`
--------------------------------------------------
El plan de resolución del GAP-062 lo pide explícitamente: *«una detección de
quietud reutilizable (útil también para otras fases del terror psicológico
del proyecto, no sólo ésta)»*. Un escenario que quiera reaccionar a que el
jugador se detenga o mire hacia otro lado no debería tener que reimplementar
el conteo.

Qué NO hace
-----------
No dispara nada por su cuenta ni conoce ningún evento: sólo mide. Quién
decide qué ocurre cuando el jugador lleva cuatro segundos quieto es el
escenario, que es donde vive esa decisión de diseño.
"""
from __future__ import annotations

from typing import Any, ClassVar, Final

import pygame

#: Cuántos píxeles de mundo puede moverse el jugador entre dos fotogramas y
#: seguir contando como quieto. No es cero: la física de este motor deja al
#: jugador con una velocidad residual mínima apoyado en el suelo (y una
#: `ZonaDeViento` lo empuja de verdad, ver `components.ZonaDeViento`), así
#: que exigir un delta exactamente nulo haría que «quieto» no ocurriera
#: nunca sobre terreno con viento — el defecto silencioso de medir la
#: quietud con `== 0`.
TOLERANCIA_DE_QUIETUD_PX: Final[float] = 1.5


class Atencion:
    """Lo que el escenario sabe de la atención del jugador.

    Se alimenta con `observar()` una vez por fotograma y responde tres
    preguntas: cuánto lleva quieto, hacia dónde mira, y qué hay a su
    espalda.
    """

    #: Con menos de esto no se considera que el jugador «se detuvo»: es el
    #: tiempo que tarda cualquiera en soltar la tecla para leer un cartel.
    #: Sin un mínimo, cada pausa involuntaria del jugador contaría.
    QUIETUD_MINIMA_S: ClassVar[float] = 0.75

    def __init__(self) -> None:
        #: Segundos que el jugador lleva sin moverse. Se reinicia a 0 en
        #: cuanto se mueve, no se decrementa: «llevo quieto N segundos» es
        #: una racha, no un depósito que se vacía poco a poco.
        self.quietud: float = 0.0
        #: -1 mira a la izquierda, +1 a la derecha. Copia de
        #: `Player.facing_direction`, para que quien consulte la atención no
        #: tenga que conocer la entidad del jugador.
        self.direccion: int = 1
        #: Centro del jugador en coordenadas de mundo.
        self.posicion: pygame.Vector2 = pygame.Vector2()
        #: Cuánto lleva mirando hacia el mismo lado. Un jugador que gira
        #: sobre sí mismo está buscando algo; uno que lleva diez segundos
        #: mirando a la derecha, avanzando.
        self.tiempo_mirando: float = 0.0
        self._posicion_previa: pygame.Vector2 | None = None

    # ── Medición ──────────────────────────────────────────────

    def observar(self, jugador: Any, dt: float) -> None:
        """Actualiza la medida con el estado del jugador en este fotograma.

        Tolera un jugador `None` (el escenario todavía no lo creó) sin
        romper y sin acumular quietud falsa: si no hay a quién observar, no
        hay atención que medir.
        """
        if jugador is None:
            self.reiniciar()
            return

        centro = pygame.Vector2(jugador.rect.center)
        if self._posicion_previa is None:
            # Primer fotograma: no hay delta con el que comparar. Se toma
            # como referencia y se espera al siguiente — contar este como
            # «quieto» daría por detenido a quien acaba de entrar corriendo.
            self._posicion_previa = centro
        elif centro.distance_to(self._posicion_previa) <= TOLERANCIA_DE_QUIETUD_PX:
            self.quietud += dt
            self._posicion_previa = centro
        else:
            self.quietud = 0.0
            self._posicion_previa = centro

        direccion = int(getattr(jugador, "facing_direction", 1) or 1)
        if direccion == self.direccion:
            self.tiempo_mirando += dt
        else:
            self.direccion = direccion
            self.tiempo_mirando = 0.0
        self.posicion = centro

    def reiniciar(self) -> None:
        """Olvida la racha. Al cambiar de fase o de escenario: la quietud
        acumulada mirando otra cosa no dice nada de ésta."""
        self.quietud = 0.0
        self.tiempo_mirando = 0.0
        self._posicion_previa = None

    # ── Preguntas ─────────────────────────────────────────────

    def esta_quieto(self, segundos: float) -> bool:
        """¿Lleva al menos `segundos` sin moverse?

        Nunca responde que sí por debajo de `QUIETUD_MINIMA_S`, aunque se
        le pida un umbral más corto: por debajo de eso no es una decisión
        del jugador, es el tiempo entre dos pasos.
        """
        return self.quietud >= max(segundos, self.QUIETUD_MINIMA_S)

    def mira_hacia(self, x_de_mundo: float) -> bool:
        """¿El jugador está de cara a ese punto del mundo?

        Un punto exactamente sobre el jugador cuenta como mirado: no hay
        espalda a distancia cero.
        """
        delta = x_de_mundo - self.posicion.x
        if delta == 0.0:
            return True
        return (delta > 0.0) == (self.direccion > 0)

    def a_su_espalda(self, distancia: float) -> float:
        """La coordenada de mundo que queda `distancia` píxeles detrás.

        Ésta es la que convierte la medida en diseño: un sonido colocado
        aquí ocurre, por construcción, donde el jugador **no** está
        mirando.
        """
        return self.posicion.x - self.direccion * abs(distancia)
