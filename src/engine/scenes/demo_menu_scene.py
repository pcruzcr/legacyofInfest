"""
DemoMenuScene — el temario, unidad por unidad, con lo que está abierto y lo que no.

AUD-095 — qué cambió y por qué
==============================
Esto era una lista plana de diecisiete tuplas. De ella salía el orden, el
nombre y la clave de la escena, y nada más. Las consecuencias, todas
observables jugando:

- **Las diez demos estaban abiertas desde el primer minuto.** Un estudiante
  podía entrar en reconocimiento de patrones (Unidad IX) sin haber visto un
  vector, no entender nada, y concluir que la asignatura era imposible.
- **No había ni rastro de las matemáticas.** La escena dibujaba una Bézier;
  de dónde sale el polinomio de Bernstein, en ningún sitio.
- **El cuestionario no contaba para nada.** Se abría con Q, se contestaba y
  se olvidaba al salir de la escena.

Ahora el menú se construye desde `framework.academic.curriculum`, que es la
fuente única del temario, y consulta a `SesionAcademica` qué tiene aprobado
el estudiante. Una unidad bloqueada se ve —con su nombre y su candado— pero
no se abre: esconderla dejaría al estudiante sin saber qué le espera, y el
temario completo a la vista es parte de la información del curso.

Las herramientas que no son del temario —cajón de arena, constructor de
tuberías, tablas de récords, asistente de escenarios— nunca se bloquean.
No se evalúan, y cerrarlas sólo estorbaría.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_Y,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_ERROR,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_MEDIUM,
    FONT_SMALL,
    TOP_BAR_H,
    draw_bottom_bar,
    draw_top_bar,
)
from src.engine.scenes.scene_registry import get_registry
from src.engine.utils.asset_loader import AssetLoader
from src.framework.academic.curriculum import PLAN
from src.framework.academic.progress import ACIERTOS_PARA_APROBAR, PREGUNTAS_POR_UNIDAD
from src.framework.academic.sesion import SesionAcademica

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


ITEM_H = 34
VISIBLE_Y_START = TOP_BAR_H + 30
VISIBLE_Y_END = BOTTOM_BAR_Y - 26
VISIBLE_ITEMS = max(1, (VISIBLE_Y_END - VISIBLE_Y_START) // ITEM_H)

#: Color de una unidad que todavía no se puede abrir.
COLOR_BLOQUEADO = (96, 96, 110)
#: Color de una unidad ya aprobada.
COLOR_APROBADO = (110, 205, 140)


class Entrada:
    """Una fila del menú.

    `unidad_id` vacío significa «esto no es del temario»: una herramienta
    suelta, que nunca se bloquea.
    """

    __slots__ = ("clave", "descripcion", "rotulo", "unidad_id")

    def __init__(self, rotulo: str, descripcion: str, clave: str, unidad_id: str = "") -> None:
        self.rotulo = rotulo
        self.descripcion = descripcion
        self.clave = clave
        self.unidad_id = unidad_id


def _construir_entradas() -> list[Entrada]:
    """El menú, derivado del temario y no escrito a mano.

    Antes había una lista literal con los nombres de las unidades repetidos.
    Añadir una unidad obligaba a tocar dos sitios y era cuestión de tiempo
    que se desincronizaran. Ahora el temario manda.
    """
    entradas = [
        Entrada(f"Unidad {u.numero} · {u.titulo}", u.resumen, u.escena, u.id)
        for u in PLAN
    ]
    entradas += [
        Entrada("Máquina de combos", "Estados y escalado de daño", "combo"),
        Entrada("Progreso", "Tu avance por el temario", "progress"),
        Entrada("Récords", "Contrarreloj y desafío de jefes", "leaderboard"),
        Entrada("Constructor de tuberías", "Encadena filtros visualmente", "pipeline"),
        Entrada("Cajón de arena", "Sin restricciones", "sandbox"),
        Entrada("Asistente de escenarios", "Cómo montar tu stage", "wizard"),
    ]
    return entradas


class DemoMenuScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._entradas: list[Entrada] = _construir_entradas()
        self._selected: int = 0
        self._scroll_offset: int = 0
        self._error_msg: str = ""
        self._error_timer: float = 0.0
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM,
        )
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL,
        )

    # -- consulta del progreso -------------------------------------
    @property
    def _sesion(self) -> SesionAcademica:
        return SesionAcademica.instancia()

    def esta_bloqueada(self, entrada: Entrada) -> bool:
        """¿Está cerrada esta fila?

        Público porque es exactamente lo que comprueban las pruebas: que el
        menú no deje entrar donde el progreso dice que no.
        """
        if not entrada.unidad_id:
            return False
        return not self._sesion.progreso.esta_desbloqueada(entrada.unidad_id)

    def on_enter(self) -> None:
        # Se reconstruye al entrar porque el progreso puede haber cambiado
        # mientras el estudiante estaba dentro de una demo.
        self._entradas = _construir_entradas()
        self._selected = self._primera_abierta()
        self._ajustar_scroll()
        self._error_msg = ""
        self._error_timer = 0.0
        self.context.scene_manager.transition.start_fade_in(0.5)

    def _primera_abierta(self) -> int:
        """Empieza el cursor por donde le toca seguir al estudiante."""
        actual = self._sesion.progreso.unidad_actual()
        if actual:
            for i, e in enumerate(self._entradas):
                if e.unidad_id == actual and not self.esta_bloqueada(e):
                    return i
        return 0

    def on_exit(self) -> None:
        pass

    def _max_scroll(self) -> int:
        return max(0, len(self._entradas) - VISIBLE_ITEMS)

    def _ajustar_scroll(self) -> None:
        if self._selected < self._scroll_offset:
            self._scroll_offset = self._selected
        elif self._selected >= self._scroll_offset + VISIBLE_ITEMS:
            self._scroll_offset = self._selected - VISIBLE_ITEMS + 1
        self._scroll_offset = max(0, min(self._scroll_offset, self._max_scroll()))

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._error_timer > 0:
            self._error_timer -= dt
            if self._error_timer <= 0:
                self._error_msg = ""

        prev = self._selected
        if im.is_raw_key_pressed(pygame.K_DOWN):
            self._selected = min(self._selected + 1, len(self._entradas) - 1)
        if im.is_raw_key_pressed(pygame.K_UP):
            self._selected = max(self._selected - 1, 0)
        if self._selected != prev:
            self._ajustar_scroll()
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)

        if im.is_action_just_pressed(Action.CONFIRM):
            self._abrir(self._entradas[self._selected])

        # T — teoría y examen de la unidad seleccionada.
        #
        # Va en una tecla aparte y no en un submenú porque son las dos únicas
        # cosas que se pueden hacer con una unidad, y un submenú de dos
        # opciones es un clic de más en cada visita.
        if im.is_raw_key_pressed(pygame.K_t):
            self._abrir_teoria(self._entradas[self._selected])

        # I — identificarse. AUD-098: sin esta puerta, el progreso académico
        # se guardaba y nadie podía volver a él nunca.
        if im.is_raw_key_pressed(pygame.K_i):
            from src.engine.scenes.student_login_scene import StudentLoginScene
            self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)
            self.context.scene_manager.replace(StudentLoginScene(self.context))

        if im.is_action_just_pressed(Action.CANCEL):
            self.context.event_bus.emit(Events.SFX_MENU_CANCEL)
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))

    def _abrir_teoria(self, entrada: Entrada) -> None:
        """Abre la teoría y el examen de una unidad.

        Se permite **aunque la unidad esté bloqueada**: leer por adelantado
        no rompe nada, y es la única forma de aprobar una unidad, que es lo
        que abre la siguiente. Bloquear el examen de la unidad bloqueada
        dejaría al estudiante sin manera de avanzar.
        """
        if not entrada.unidad_id:
            self._error_msg = "Esta herramienta no es del temario: no tiene teoría."
            self._error_timer = 2.5
            return
        from src.engine.scenes.unit_theory_scene import UnitTheoryScene
        self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)
        self.context.scene_manager.push(UnitTheoryScene(self.context, entrada.unidad_id))

    def _abrir(self, entrada: Entrada) -> None:
        if self.esta_bloqueada(entrada):
            self.context.event_bus.emit(Events.SFX_MENU_CANCEL)
            self._error_msg = (
                f"Bloqueada: aprueba antes la unidad anterior con "
                f"{ACIERTOS_PARA_APROBAR} de {PREGUNTAS_POR_UNIDAD}. Pulsa T para su teoría."
            )
            self._error_timer = 3.0
            return

        self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)
        registry = get_registry()
        try:
            escena = registry.build(entrada.clave, self.context)
        except (ImportError, RuntimeError, ValueError) as e:
            logger.warning("demo_menu: no se pudo construir '%s': %s", entrada.clave, e)
            self._error_msg = f"No se pudo abrir '{entrada.clave}': {e}"
            self._error_timer = 3.0
            return

        if escena is None:
            self._error_msg = f"No se pudo abrir '{entrada.clave}' — ¿faltan recursos?"
            self._error_timer = 3.0
            return
        self.context.scene_manager.push(self._con_precarga(entrada.clave, escena))

    #: AUD-288 — demos cuya apertura hay que precargar, y con qué.
    #:
    #: Sólo una, y medida: abrir `pattern` **congelaba el juego 2,8 s** —3,5 la
    #: primera vez de la sesión— porque `obtener_modelo()` importa scikit-learn
    #: y carga o entrena el modelo en el hilo del dibujado. Tres segundos de
    #: pantalla negra en la demo que el profesor abre delante de la clase.
    #:
    #: La segunda llamada tarda 2 ms: lo caro es el import, y basta con hacerlo
    #: una vez fuera del hilo principal. El resto de las demos abren en menos de
    #: 10 ms y no entran aquí — con el umbral de `LoadingScene` tampoco pasaría
    #: nada si entraran, pero un diccionario que enumera lo que de verdad cuesta
    #: dice más que uno que las lista todas.
    _PRECARGAS: dict[str, tuple[str, str]] = {
        "pattern": ("el modelo de la Unidad IX",
                    "src.framework.processing.reference_model"),
    }

    def _con_precarga(self, clave: str, escena):
        """Envuelve la escena en una pantalla de carga si su apertura es lenta.

        Devuelve la escena tal cual cuando no hay nada que precargar, así que el
        camino normal no cambia en absoluto.
        """
        precarga = self._PRECARGAS.get(clave)
        if precarga is None:
            return escena

        etiqueta, modulo = precarga

        def _calentar() -> None:
            # Se hace en el hilo trabajador y **no toca pygame**: importar
            # scikit-learn y cargar un modelo es CPU pura. Tocar superficies
            # desde aquí sería la forma de convertir una mejora en un fallo
            # intermitente imposible de reproducir.
            import importlib

            importlib.import_module(modulo).obtener_modelo()

        from src.engine.scenes.loading_scene import LoadingScene, LoadTask

        return LoadingScene(
            self.context, next_scene=escena,
            tasks=[LoadTask(etiqueta, _calentar)],
        )

    # -- dibujado --------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "DEMOSTRACIONES ACADÉMICAS", "TEMARIO")

        self._dibujar_resumen(surface)

        fin = min(self._scroll_offset + VISIBLE_ITEMS, len(self._entradas))
        for i in range(self._scroll_offset, fin):
            self._dibujar_fila(surface, i)

        if self._error_msg:
            err = self._font_small.render(self._error_msg, True, COLOR_ERROR)
            surface.blit(err, ((settings.INTERNAL_WIDTH - err.get_width()) // 2,
                               BOTTOM_BAR_Y - 24))

        draw_bottom_bar(
            surface,
            "↑↓: Navegar  |  ENTER: Demo  |  T: Teoría y examen  |  "
            "I: Identificarse  |  ESC: Título",
        )

    def _dibujar_resumen(self, surface: pygame.Surface) -> None:
        """Una línea con quién eres y cuánto llevas."""
        progreso = self._sesion.progreso
        aprobadas = len(progreso.unidades_aprobadas())
        quien = progreso.correo or "sin identificar — pulsa I para guardar tu progreso"
        texto = f"{quien}   ·   {aprobadas}/{len(PLAN)} unidades aprobadas"
        render = self._font_small.render(texto, True, COLOR_ACCENT)
        surface.blit(render, (16, TOP_BAR_H + 6))

    def _dibujar_fila(self, surface: pygame.Surface, i: int) -> None:
        entrada = self._entradas[i]
        idx = i - self._scroll_offset
        y = VISIBLE_Y_START + idx * ITEM_H
        seleccionada = i == self._selected
        bloqueada = self.esta_bloqueada(entrada)
        aprobada = bool(entrada.unidad_id) and self._sesion.progreso.esta_aprobada(entrada.unidad_id)

        if seleccionada:
            pygame.draw.rect(
                surface, (40, 40, 80),
                pygame.Rect(8, y - 3, settings.INTERNAL_WIDTH - 16, ITEM_H - 2),
                border_radius=3,
            )
            pygame.draw.rect(
                surface, COLOR_HIGHLIGHT if not bloqueada else COLOR_BLOQUEADO,
                pygame.Rect(8, y - 3, 3, ITEM_H - 2), border_radius=1,
            )

        if bloqueada:
            color = COLOR_BLOQUEADO
        elif aprobada:
            color = COLOR_APROBADO
        elif seleccionada:
            color = COLOR_HIGHLIGHT
        else:
            color = COLOR_TEXT

        marca = "🔒 " if bloqueada else ("✔ " if aprobada else "  ")
        rotulo = self._font_medium.render(f"{marca}{entrada.rotulo}", True, color)
        surface.blit(rotulo, (20, y))

        # La nota va a la derecha, alineada, para que se lea en columna.
        if entrada.unidad_id:
            progreso = self._sesion.progreso
            if progreso.intentos(entrada.unidad_id):
                nota = f"{progreso.aciertos(entrada.unidad_id)}/{PREGUNTAS_POR_UNIDAD}"
            else:
                nota = "—"
            render_nota = self._font_small.render(nota, True, color)
            surface.blit(render_nota,
                         (settings.INTERNAL_WIDTH - render_nota.get_width() - 20, y + 2))

        desc_color = (150, 150, 165) if not bloqueada else (80, 80, 92)
        desc = self._font_small.render(entrada.descripcion, True, desc_color)
        surface.blit(desc, (34, y + rotulo.get_height()))
