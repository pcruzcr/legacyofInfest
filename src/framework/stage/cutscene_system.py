"""
Module: cutscene_system
System: framework.stage
Academic Unit: N/A
Description: Scripted cutscene system supporting camera moves, dialogue,
animations, and scene transitions.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import pygame

from src.engine.core import settings

logger = logging.getLogger(__name__)


class CutsceneAction:
    """Base class for cutscene actions."""

    def start(self) -> None:
        ...

    def update(self, dt: float) -> bool:
        """Returns True when complete."""
        return True

    def draw(self, surface: pygame.Surface) -> None:
        ...

    def terminar(self) -> None:
        """Deja el mundo como si la acción se hubiera visto entera.

        AUD-136 — la mitad de «saltar» que casi nadie implementa.

        Saltar una escena no puede significar «no ejecutarla»: si la escena
        movía al jugador hasta la puerta, saltarla lo dejaría plantado delante
        de una puerta que ya está abierta, y el nivel se rompe. Saltar
        significa **ir al final**, no cancelar.

        Por defecto se resuelve avanzando una hora de golpe, que basta para
        todo lo que tenga duración. Lo que espera a una tecla o a otro sistema
        lo sobrescribe.
        """
        self.update(3600.0)


class WaitAction(CutsceneAction):
    """Wait for a duration in seconds."""

    def __init__(self, duration: float) -> None:
        self._duration = duration
        self._elapsed = 0.0

    def start(self) -> None:
        self._elapsed = 0.0

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        return self._elapsed >= self._duration


class FadeAction(CutsceneAction):
    """Fade in or out."""

    def __init__(self, duration: float, fade_in: bool = True) -> None:
        self._duration = duration
        self._fade_in = fade_in
        self._elapsed = 0.0
        self._surface = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        )
        self._surface.fill((0, 0, 0))

    def start(self) -> None:
        self._elapsed = 0.0

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        return self._elapsed >= self._duration

    def draw(self, surface: pygame.Surface) -> None:
        # AUD-111 — un fundido a negro tiene que **acabar** en negro.
        #
        # Esto era `if self._elapsed >= self._duration: return`, y con eso el
        # fotograma siguiente al final de un fundido a negro se dibujaba con
        # alfa cero: la pantalla, que llevaba medio segundo oscureciéndose,
        # volvía de golpe a plena luz durante un fotograma antes del corte.
        #
        # Es un destello de 16 ms. No rompe nada, no lo detecta ninguna prueba
        # de construcción, y es exactamente lo que un fundido existe para
        # evitar. Lo encontró la primera prueba que se escribió contra esta
        # clase.
        #
        # Al terminar, un fundido de entrada desaparece —la escena ya está
        # visible— y uno de salida se queda opaco hasta que alguien lo retire.
        if self._elapsed >= self._duration:
            if self._fade_in:
                return
            self._surface.set_alpha(255)
            surface.blit(self._surface, (0, 0))
            return
        progress = self._elapsed / self._duration
        alpha = int((1.0 - progress) * 255) if self._fade_in else int(progress * 255)
        self._surface.set_alpha(max(0, min(255, alpha)))
        surface.blit(self._surface, (0, 0))


class CameraMoveAction(CutsceneAction):
    """Move camera to target position."""

    def __init__(self, target_x: float, target_y: float, duration: float,
                 camera: Any) -> None:
        self._tx = target_x
        self._ty = target_y
        self._duration = duration
        self._camera = camera
        self._elapsed = 0.0
        self._start_x = 0.0
        self._start_y = 0.0

    def start(self) -> None:
        self._elapsed = 0.0
        if self._camera:
            self._start_x = self._camera.offset.x
            self._start_y = self._camera.offset.y

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        if self._camera:
            t = min(1.0, self._elapsed / self._duration)
            self._camera.offset.x = self._start_x + (self._tx - self._start_x) * t
            self._camera.offset.y = self._start_y + (self._ty - self._start_y) * t
        return self._elapsed >= self._duration


class DialogueAction(CutsceneAction):
    """Show dialogue text box."""

    def __init__(self, text: str, duration: float = 0.0,
                 speaker: str = "") -> None:
        self._text = text
        self._duration = duration
        self._speaker = speaker
        self._elapsed = 0.0
        self._completed = False
        self._font = pygame.font.Font(None, 14)
        self._box_surf = pygame.Surface((settings.INTERNAL_WIDTH - 40, 60), pygame.SRCALPHA)
        self._box_surf.fill((0, 0, 0, 200))
        self._hint_surf = self._font.render("[ENTER]", True, (140, 140, 150))
        self._prev_speaker = None
        self._prev_text = None
        self._speaker_surf = None
        self._text_surf = None

    def start(self) -> None:
        self._elapsed = 0.0
        self._completed = False

    def update(self, dt: float) -> bool:
        im = pygame.key.get_just_pressed()
        if self._duration > 0:
            self._elapsed += dt
            if self._elapsed >= self._duration:
                return True
            return False
        if im and (pygame.K_RETURN in im or pygame.K_SPACE in im):
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        if self._speaker != self._prev_speaker or self._text != self._prev_text:
            self._prev_speaker = self._speaker
            self._prev_text = self._text
            if self._speaker:
                self._speaker_surf = self._font.render(self._speaker, True, (255, 220, 150))
            else:
                self._speaker_surf = None
            self._text_surf = self._font.render(self._text, True, (220, 220, 220))
        surface.blit(self._box_surf, (20, settings.INTERNAL_HEIGHT - 80))
        if self._speaker and self._speaker_surf:
            surface.blit(self._speaker_surf, (30, settings.INTERNAL_HEIGHT - 75))
        if self._text_surf:
            surface.blit(self._text_surf, (30, settings.INTERNAL_HEIGHT - 55))
        surface.blit(self._hint_surf, (settings.INTERNAL_WIDTH - 60, settings.INTERNAL_HEIGHT - 30))


# ══════════════════════════════════════════════════════════════
# AUD-136 — D3: acciones nuevas
#
# Las cuatro que había —esperar, fundir, mover la cámara y un cuadro de
# texto propio— sirven para una intro y para nada más. Una escena narrativa
# necesita que ALGUIEN HAGA ALGO: que un personaje camine, que suene algo,
# que el mundo cambie. Estas son ésas.
# ══════════════════════════════════════════════════════════════


class MoverEntidadAction(CutsceneAction):
    """Lleva una entidad de donde está a un punto del mapa.

    Es la acción que convierte una intro en una escena: sin ella, los
    personajes están donde el mapa los dejó y la cámara pasea sobre estatuas.

    Mueve la posición **directamente**, sin física, y eso es a propósito: el
    director congela el juego mientras corre una escena que bloquea, así que
    la gravedad no está tirando de nadie. Intentar hacerlo con velocidades
    dejaría el resultado a merced de las colisiones del mapa, y una escena
    tiene que acabar exactamente donde el guion dice.
    """

    def __init__(self, entidad: Any, destino_x: float, destino_y: float | None,
                 duracion: float) -> None:
        self._entidad = entidad
        self._dx = float(destino_x)
        self._dy = destino_y
        self._duracion = max(0.001, float(duracion))
        self._t = 0.0
        self._ox = 0.0
        self._oy = 0.0

    def start(self) -> None:
        self._t = 0.0
        pos = getattr(self._entidad, "position", None)
        if pos is not None:
            self._ox, self._oy = float(pos.x), float(pos.y)

    def _colocar(self, x: float, y: float) -> None:
        pos = getattr(self._entidad, "position", None)
        if pos is None:
            return
        pos.x, pos.y = x, y
        rect = getattr(self._entidad, "rect", None)
        if rect is not None:
            rect.center = (int(x), int(y))
        # Mirar hacia donde se camina. Un personaje que cruza la sala de
        # espaldas se lee como un fallo de animación, no como una decisión.
        if self._dx != self._ox and hasattr(self._entidad, "facing_right"):
            self._entidad.facing_right = self._dx > self._ox

    def update(self, dt: float) -> bool:
        self._t += dt
        t = min(1.0, self._t / self._duracion)
        destino_y = self._oy if self._dy is None else self._dy
        self._colocar(
            self._ox + (self._dx - self._ox) * t,
            self._oy + (destino_y - self._oy) * t,
        )
        return self._t >= self._duracion


class EventoAction(CutsceneAction):
    """Emite un evento del bus. Termina en el mismo fotograma.

    Es la acción que abre el sistema: con ella un guion puede abrir una
    puerta, arrancar una inundación o disparar cualquier cosa que escuche el
    bus, sin que el motor tenga que conocer una acción por cada mecánica.
    """

    def __init__(self, bus: Any, evento: str, **datos: Any) -> None:
        self._bus = bus
        self._evento = evento
        self._datos = datos
        self._emitido = False

    def start(self) -> None:
        self._emitido = False
        if self._bus is not None and self._evento:
            self._bus.emit(self._evento, **self._datos)
            self._emitido = True

    def update(self, dt: float) -> bool:
        return True

    def terminar(self) -> None:
        """Al saltar, el evento se emite igual.

        Ésta es la razón de que `terminar()` exista. Si saltar una escena se
        comiera el evento que abre la puerta, saltar dejaría el nivel sin
        salida — y el jugador que salta es precisamente el que ya se lo sabe.

        Pero sólo si **aún no** se emitió: cuando el guion ya pasó por la
        acción, su `start()` disparó el evento, y saltar otra vez no puede
        volver a dispararlo — el mundo ya reaccionó.
        """
        if not self._emitido:
            self.start()


class SonidoAction(CutsceneAction):
    """Pide un sonido por el bus y sigue. No espera a que acabe."""

    def __init__(self, bus: Any, evento: str) -> None:
        self._bus = bus
        self._evento = evento

    def start(self) -> None:
        if self._bus is not None and self._evento:
            self._bus.emit(self._evento)

    def update(self, dt: float) -> bool:
        return True

    def terminar(self) -> None:
        # Al saltar NO suena: un efecto de sonido que se dispara cuando ya no
        # se ve lo que lo causaba es ruido.
        return


class TemblorAction(CutsceneAction):
    """Sacude la cámara. Respeta «movimiento reducido» de accesibilidad."""

    def __init__(self, camara: Any, duracion: float = 0.4,
                 intensidad: float = 6.0) -> None:
        self._camara = camara
        self._duracion = max(0.0, float(duracion))
        self._intensidad = max(0.0, float(intensidad))

    def start(self) -> None:
        if self._camara is None:
            return
        # AUD-143 — el método se llama `apply_shake`, no `shake`.
        #
        # Esta acción llamaba a `shake()`, que **no existe en `Camera`**, así
        # que la orden `temblor` de los guiones no sacudía nada: el `getattr`
        # devolvía `None` y se salía en silencio. La prueba pasaba porque usé
        # una cámara de mentira con un método `shake` que me inventé — un
        # doble que no se parecía al objeto real, exactamente el fallo que
        # este proyecto ya había cometido con `InputManager`.
        #
        # Se prueban los dos nombres porque un escenario puede traer su propia
        # cámara; y si no hay ninguno, ahora se registra un aviso en vez de
        # callar.
        for nombre in ("apply_shake", "shake"):
            sacudir = getattr(self._camara, nombre, None)
            if callable(sacudir):
                sacudir(self._intensidad, self._duracion) if nombre == "apply_shake" \
                    else sacudir(self._duracion, self._intensidad)
                return
        logger.warning(
            "la cámara de este escenario no sabe sacudirse: «temblor» no hará nada")

    def update(self, dt: float) -> bool:
        return True


class EsperarEventoAction(CutsceneAction):
    """Se queda esperando a que alguien emita un evento.

    Con un tope de segundos, siempre. Una escena que espera para siempre a un
    evento que no llega deja el juego colgado con el jugador sin control, y
    eso no es un fallo de guion: es un fallo del motor por permitirlo.
    """

    def __init__(self, bus: Any, evento: str, tope: float = 10.0) -> None:
        self._bus = bus
        self._evento = evento
        self._tope = max(0.1, float(tope))
        self._t = 0.0
        self._llego = False

    def _al_llegar(self, **_datos: Any) -> None:
        self._llego = True

    def start(self) -> None:
        self._t = 0.0
        self._llego = False
        if self._bus is not None and self._evento:
            self._bus.subscribe(self._evento, self._al_llegar)

    def update(self, dt: float) -> bool:
        self._t += dt
        return self._llego or self._t >= self._tope

    def terminar(self) -> None:
        self._llego = True


class DialogoArbolAction(CutsceneAction):
    """Abre un árbol del sistema de diálogo y espera a que se cierre.

    Reutiliza el sistema bueno —retratos, ramas, velocidad de texto,
    autoajuste (AUD-127/128)— en vez del cuadro de texto propio que trae
    `DialogueAction`, que no sabe hacer nada de eso.
    """

    def __init__(self, dialogo: Any, arbol_id: str) -> None:
        self._dialogo = dialogo
        self._arbol_id = arbol_id
        self._abierto = False

    def start(self) -> None:
        self._abierto = False
        if self._dialogo is None:
            return
        abrir = getattr(self._dialogo, "start_tree", None) or getattr(
            self._dialogo, "iniciar", None)
        if callable(abrir):
            abrir(self._arbol_id)
            self._abierto = True

    def update(self, dt: float) -> bool:
        if not self._abierto or self._dialogo is None:
            return True
        return not getattr(self._dialogo, "is_active", False)

    def terminar(self) -> None:
        cerrar = getattr(self._dialogo, "close", None) or getattr(
            self._dialogo, "cerrar", None)
        if callable(cerrar):
            cerrar()
        self._abierto = False


class AccionParalela(CutsceneAction):
    """Varias acciones a la vez. Termina cuando termina la última.

    Sin esto, un guion sólo puede contar una cosa cada vez: la cámara viaja,
    LUEGO el personaje camina, LUEGO suena el trueno. Todo lo que hace que
    una escena parezca escrita por alguien pasa **a la vez**.
    """

    def __init__(self, acciones: list[CutsceneAction]) -> None:
        self._acciones = list(acciones)
        self._vivas: list[CutsceneAction] = []

    def start(self) -> None:
        self._vivas = list(self._acciones)
        for accion in self._vivas:
            accion.start()

    def update(self, dt: float) -> bool:
        self._vivas = [a for a in self._vivas if not a.update(dt)]
        return not self._vivas

    def draw(self, surface: pygame.Surface) -> None:
        for accion in self._vivas:
            accion.draw(surface)

    def terminar(self) -> None:
        for accion in self._vivas:
            accion.terminar()
        self._vivas = []


class CutsceneScript:
    """A list of actions that play sequentially."""

    def __init__(self, actions: list[CutsceneAction] | None = None, *,
                 bloquea: bool = True, saltable: bool = True,
                 bandas: bool = False) -> None:
        self._actions: list[CutsceneAction] = actions or []
        self._index: int = 0
        self._active: bool = False
        self._callback: Callable[[], None] | None = None
        #: AUD-136 — si `False`, el juego sigue corriendo por debajo.
        #:
        #: Casi todo lo que un escenario quiere contar no merece quitarle el
        #: mando al jugador: un compañero que grita algo desde una cornisa, una
        #: puerta que se abre al fondo. Bloquear por defecto convertía cada
        #: detalle narrativo en una interrupción, y la respuesta del jugador a
        #: la tercera interrupción es saltárselas todas sin leerlas.
        self.bloquea = bool(bloquea)
        self.saltable = bool(saltable)
        #: Bandas negras arriba y abajo mientras dure. Sólo tienen sentido si
        #: bloquea: son la señal de «esto no lo controlas tú».
        self.bandas = bool(bandas)
        self._alto_banda = 0.0

    def add_action(self, action: CutsceneAction) -> None:
        self._actions.append(action)

    def start(self, callback: Callable[[], None] | None = None) -> None:
        self._index = 0
        self._active = True
        self._callback = callback
        if self._actions:
            self._actions[0].start()

    def saltar(self) -> None:
        """Va al final ejecutando el efecto de todo lo que quedaba.

        AUD-136. Saltar **no** es cancelar. Si el guion movía al jugador hasta
        la puerta y abría la puerta, saltarlo tiene que dejar al jugador en la
        puerta y la puerta abierta; si no, quien se salta la escena —que es
        quien ya se la sabe, en su segunda partida— se queda encerrado.

        Un botón de saltar que rompe la partida es peor que no tenerlo.
        """
        if not self._active:
            return
        for accion in self._actions[self._index:]:
            accion.terminar()
        self._index = len(self._actions)
        self._active = False
        if self._callback:
            self._callback()

    def update(self, dt: float) -> None:
        if self.bandas:
            objetivo = 24.0 if self._active else 0.0
            paso = 120.0 * dt
            if self._alto_banda < objetivo:
                self._alto_banda = min(objetivo, self._alto_banda + paso)
            elif self._alto_banda > objetivo:
                self._alto_banda = max(objetivo, self._alto_banda - paso)
        if not self._active or self._index >= len(self._actions):
            return
        if self._actions[self._index].update(dt):
            self._index += 1
            if self._index < len(self._actions):
                self._actions[self._index].start()
            else:
                self._active = False
                if self._callback:
                    self._callback()

    def draw(self, surface: pygame.Surface) -> None:
        """Render only the action currently playing.

        AUD-040: this used to loop over *every remaining* action::

            for i in range(self._index, len(self._actions)):
                self._actions[i].draw(surface)

        A pending action has ``_elapsed == 0``, and ``FadeAction.draw`` maps
        elapsed 0 on a fade-*in* to alpha 255 — fully opaque black. So any
        script containing a later fade-in painted the screen solid black from
        its very first frame, for the script's entire duration.

        That is precisely the reported symptom: launching a stage showed a black
        screen for ~2 s before the world appeared. The stage was rendering
        correctly the whole time, underneath an opaque overlay belonging to a
        step that had not started yet.

        A cutscene is a sequence, not a stack: exactly one step is on screen at
        a time.
        """
        if self._alto_banda > 0.0:
            self._dibujar_bandas(surface)
        if not self._active or not (0 <= self._index < len(self._actions)):
            return
        self._actions[self._index].draw(surface)

    def _dibujar_bandas(self, surface: pygame.Surface) -> None:
        alto = int(self._alto_banda)
        ancho = surface.get_width()
        surface.fill((0, 0, 0), pygame.Rect(0, 0, ancho, alto))
        surface.fill(
            (0, 0, 0),
            pygame.Rect(0, surface.get_height() - alto, ancho, alto),
        )

    @property
    def active(self) -> bool:
        return self._active

    @property
    def terminada(self) -> bool:
        """Acabó del todo: ni corriendo ni con bandas por recoger."""
        return not self._active and self._alto_banda <= 0.0