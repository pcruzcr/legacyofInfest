"""
Mecánicas de nivel que la escena conduce: agua, tiempo bala y scroll forzado.

F5.5 y F5.6 — por qué estas tres no son sistemas ECS
=====================================================
El resto de la fase 5 vive en `framework/ecs/systems.py` porque opera sobre
componentes y no le importa quién los tenga. Estas tres son distintas: las tres
tocan algo de lo que **hay uno solo** —el jugador, el reloj, la cámara— y
convertir un singular en una consulta de componentes es ceremonia sin ganancia.

La regla que se sigue en este motor, dicha corta: **si el sistema opera sobre
«todos los que…», va en ECS; si opera sobre «el», va aquí.**
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pygame

from src.framework.ecs.components import ZonaDeAgua
from src.framework.ecs.systems import en_agua

#: Nombre con el que la cámara lenta registra su factor en el reloj (AUD-118).
FUENTE_TIEMPO_BALA: str = "tiempo_bala"

if TYPE_CHECKING:
    from src.engine.core.clock import Clock
    from src.framework.ecs.world import World
    from src.framework.entities.player import Player
    from src.framework.stage.camera import Camera

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# F5.6 — el agua, y el estado que llevaba un mes inalcanzable
# ══════════════════════════════════════════════════════════════


@dataclass(slots=True)
class ControlDeNado:
    """Mete y saca al jugador del agua, y le lleva la cuenta del aire.

    **El hallazgo que esto cierra.** `SwimmingState` estaba escrito, completo y
    probado, y un análisis del árbol de sintaxis sobre todo `src/` demostró que
    tenía **cero transiciones de entrada**: no había un solo
    `_change_state_instance(SwimmingState())` en el proyecto. Nadie podía nadar.

    Y la documentación ya lo sabía. `docs/45_SWIMMING_SPEC.md`, línea 59, desde
    el 14 de julio::

        Missing: No dedicated water zone detection; depends on stage collision
        system to trigger state change

    Es el cuarto sistema de este tipo en un mes —la iluminación que no iluminaba
    un píxel, las trece demos que dibujaban en una esquina, el ultimate cuyo
    medidor nadie incrementaba— y siempre la misma forma: código correcto,
    probado en aislamiento, al que no llega ningún camino desde el juego.

    El oxígeno
    ----------
    Tres de los cuatro niveles acuáticos del dossier giran sobre la cuenta
    atrás: Sonic (Labyrinth), Sonic 2 (Chemical Plant) y SMB3 (Water Land). Sin
    ella el agua es sólo un sitio donde te mueves raro; con ella es un reloj, y
    un reloj convierte la exploración en decisión.
    """

    #: Segundos de aire. Sonic daba treinta antes de la primera advertencia.
    aire_maximo: float = 30.0
    aire: float = 30.0
    #: Daño por segundo al quedarse sin aire. No mata al instante: da tiempo a
    #: llegar a la superficie, que es la diferencia entre tensión y castigo.
    dano_por_segundo: float = 1.0
    #: Segundos restantes a partir de los cuales avisar. Aviso pronto y claro:
    #: ahogarse sin haber podido saberlo no enseña nada.
    umbral_aviso: float = 10.0
    _estaba_dentro: bool = False
    _acumulado_dano: float = 0.0

    @property
    def sin_aire(self) -> bool:
        return self.aire <= 0.0

    @property
    def avisando(self) -> bool:
        return 0.0 < self.aire <= self.umbral_aviso

    def update(self, dt: float, jugador: Player, mundo: World, bus=None) -> None:
        """Un fotograma. Devuelve nada; cambia el estado del jugador si toca."""
        agua: ZonaDeAgua | None = en_agua(mundo, jugador.rect)
        dentro = agua is not None

        if dentro and not self._estaba_dentro:
            self._entrar(jugador, bus)
        elif not dentro and self._estaba_dentro:
            self._salir(jugador)
        self._estaba_dentro = dentro

        if dentro:
            self.aire = max(0.0, self.aire - dt)
            if self.sin_aire:
                # Se acumula y se aplica por unidades enteras. Restar una
                # fracción por fotograma haría que la vida bajara en decimales
                # que la interfaz redondea, y el jugador vería la barra quieta
                # mientras se muere.
                self._acumulado_dano += self.dano_por_segundo * dt
                if self._acumulado_dano >= 1.0:
                    entero = int(self._acumulado_dano)
                    self._acumulado_dano -= entero
                    jugador.apply_damage(
                        float(entero), (jugador.rect.centerx, jugador.rect.top),
                    )
        else:
            # Se recupera deprisa: el castigo es quedarse dentro, no salir.
            self.aire = min(self.aire_maximo, self.aire + dt * 8.0)
            self._acumulado_dano = 0.0

    @staticmethod
    def _entrar(jugador: Player, bus) -> None:
        from src.framework.entities.states import SwimmingState

        actual = getattr(jugador, "_state_instance", None)
        if isinstance(actual, SwimmingState):
            return
        jugador._change_state_instance(SwimmingState())
        if bus is not None:
            from src.engine.core.events import Events

            bus.emit(Events.VFX_BUBBLE, pos=(jugador.position.x, jugador.position.y))

    @staticmethod
    def _salir(jugador: Player) -> None:
        from src.framework.entities.states import FallingState, SwimmingState

        if isinstance(getattr(jugador, "_state_instance", None), SwimmingState):
            jugador._change_state_instance(FallingState())


# ══════════════════════════════════════════════════════════════
# F5.5 — tiempo bala
# ══════════════════════════════════════════════════════════════


@dataclass(slots=True)
class TiempoBala:
    """Ralentiza la simulación mientras dure la reserva. Max Payne, Katana ZERO.

    Es la mecánica más barata de las tres revisiones y la más vistosa. `Clock`
    ya separa el `dt` escalado del real desde que se implementó el *hit-stop*::

        self._dt = raw_dt * self.time_scale

    Esa separación es exactamente la que el tiempo bala necesita: el juego se
    ralentiza y la interfaz no, así que el menú de pausa y los contadores siguen
    a velocidad normal. Sin ella habría que tocar veinte sitios; con ella, uno.

    La reserva, y por qué no un enfriamiento
    -----------------------------------------
    Con enfriamiento, el jugador aprende a pulsarlo cada vez que se recarga y
    deja de ser una decisión. Con una reserva que se gasta y se recupera
    despacio, cada uso es «¿ahora o guardo para lo siguiente?», que es lo que
    hace interesante la mecánica en Max Payne.
    """

    escala: float = 0.35
    reserva_maxima: float = 3.0
    #: `None` significa «llena». Escribir `TiempoBala(reserva_maxima=0.5)` y que
    #: la reserva se quedara en los 3,0 de por defecto sería una trampa: el
    #: objeto arrancaría con seis veces más reserva de la que dice tener como
    #: máximo. Lo detectó la primera prueba que se escribió contra esta clase.
    reserva: float | None = None
    #: Segundos de reserva que se recuperan por segundo real sin usarla.
    recarga: float = 0.4
    #: Segundos de espera tras agotarla antes de empezar a recargar. Evita el
    #: parpadeo de encender y apagar cuando queda una décima.
    espera_tras_agotar: float = 1.0
    _activo: bool = False
    _espera: float = 0.0
    _yo_lo_baje: bool = False

    def __post_init__(self) -> None:
        if self.reserva is None:
            self.reserva = self.reserva_maxima

    @property
    def activo(self) -> bool:
        return self._activo

    @property
    def fraccion(self) -> float:
        """0→1 para la barra del HUD."""
        return self.reserva / self.reserva_maxima if self.reserva_maxima else 0.0

    def update(self, dt_real: float, quiere: bool, reloj: Clock | None) -> None:
        """`dt_real` en segundos **sin escalar**.

        Con el `dt` escalado la reserva duraría más cuanto más lenta fuera la
        cámara lenta, que es un bucle de realimentación absurdo: activarla la
        haría durar más y a 0,1× sería casi infinita.
        """
        if quiere and self.reserva > 0.0 and self._espera <= 0.0:
            self._activo = True
            self.reserva = max(0.0, self.reserva - dt_real)
            if self.reserva <= 0.0:
                self._espera = self.espera_tras_agotar
        else:
            self._activo = False
            if self._espera > 0.0:
                self._espera = max(0.0, self._espera - dt_real)
            else:
                self.reserva = min(self.reserva_maxima, self.reserva + self.recarga * dt_real)

        if reloj is None:
            return

        # AUD-118 — el reloj compone; esta clase sólo declara su factor.
        #
        # Antes esto recordaba «yo bajé el reloj» para no pisar al hit-stop.
        # Funcionaba a medias: el hit-stop, al expirar, escribía 1.0 sin
        # preguntar, y la cámara lenta se recuperaba un fotograma tarde. El
        # parche del recuerdo tapaba la mitad del problema que el parche del
        # hit-stop dejaba abierta, que es la señal de que el problema estaba en
        # que un solo número tuviera dos dueños.
        #
        # `getattr` conserva los dobles de reloj de las entregas de
        # estudiantes, que sólo tienen el atributo `time_scale`.
        registrar = getattr(reloj, "escalar", None)
        retirar = getattr(reloj, "restaurar", None)
        if registrar is None or retirar is None:
            if self._activo:
                reloj.time_scale = self.escala
                self._yo_lo_baje = True
            elif getattr(self, "_yo_lo_baje", False):
                reloj.time_scale = 1.0
                self._yo_lo_baje = False
            return
        if self._activo:
            registrar(FUENTE_TIEMPO_BALA, self.escala)
        else:
            retirar(FUENTE_TIEMPO_BALA)


# ══════════════════════════════════════════════════════════════
# F5.5 — scroll forzado
# ══════════════════════════════════════════════════════════════


@dataclass(slots=True)
class ScrollForzado:
    """La cámara avanza sola y el borde de atrás mata.

    SMB3 (Airship), Cuphead (los *run & gun*), Ori (la huida del Ginso Tree),
    Celeste (las pantallas de persecución), Terraria (Wall of Flesh).

    Por qué el borde mata en vez de empujar
    ----------------------------------------
    Empujar parece más amable y es peor: el jugador queda aplastado contra la
    geometría, atraviesa paredes o se queda atascado en un saliente sin poder
    hacer nada mientras la cámara sigue. Matar es honesto —el nivel dijo
    «sígueme» y no lo seguiste— y el reintento es inmediato porque hay
    checkpoints.

    `margen_de_gracia` existe porque sin él la muerte ocurre cuando el sprite
    aún se ve, y eso se lee como injusticia aunque sea correcto.
    """

    velocidad: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(40.0, 0.0))
    activo: bool = False
    #: Píxeles que se puede rebasar el borde antes de morir.
    margen_de_gracia: float = 24.0
    #: Se detiene al llegar aquí. `None` = hasta el final del mapa.
    parar_en_x: float | None = None
    #: Rectángulo que lo enciende al pisarlo (AUD-249). `None` = lo arranca
    #: alguien por código.
    #:
    #: Sin esto la mecánica **no se podía usar desde Tiled**: estaba escrita,
    #: probada y sin ninguna forma de encenderla que no fuera escribir Python,
    #: así que ningún alumno podía hacer un nivel de persecución. `StageScene`
    #: la construía y no la tocaba nunca (`GAP-032`).
    disparador: pygame.Rect | None = None
    _origen: pygame.Vector2 | None = None

    def arrancar(self, camara: Camera) -> None:
        self.activo = True
        self._origen = pygame.Vector2(camara.offset)

    def update(self, dt: float, camara: Camera) -> None:
        if not self.activo:
            return
        camara.offset += self.velocidad * dt
        if self.parar_en_x is not None and camara.offset.x >= self.parar_en_x:
            camara.offset.x = self.parar_en_x
            self.activo = False

    def se_quedo_atras(self, jugador_rect: pygame.Rect, camara: Camera) -> bool:
        """¿El jugador quedó por detrás del borde, con su margen?"""
        if not self.activo:
            return False
        return jugador_rect.right < camara.offset.x - self.margen_de_gracia
