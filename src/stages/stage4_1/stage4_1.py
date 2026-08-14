"""
Module: stage4_1
System: src.stages.stage4_1
Academic Unit: V (color y gradación) + VII (clima y partículas)

NIVEL 4-1 — EL CEMENTERIO SAGRADO

La idea, en una frase: **el cementerio cambia de piel con el jugador**. Cada
fase tiene su propia gradación de color, su propio clima, y un espíritu que
testifica y asciende. Reemplaza al diseño anterior de La Cegua (AUD-462: ver
`docs/niveles/13_STAGE_4_1.md` §0) heredando la forma de pozo que ya se
demostró que funciona jugada (AUD-225).

Lo que este escenario NO tiene, y por qué
==========================================
**Cero enemigos.** Sigue siendo la regla de oro (`docs/niveles/
13_STAGE_4_1.md`). Las siluetas de Venado, Rey Terciopelo y Gavilán —ver
`siluetas.py`, que no cambió: ya dibujaba exactamente estos tres— son
contornos sin colisión, sin IA y sin salud: testifican, no atacan.

Lo que sí tiene
================
* **Seis fases** (`fases.py`), leídas de la fila del jugador. Cada una trae
  su gradación de color, su clima y —si le toca— su espíritu, su loma, su
  silencio o su ciclo de luna.
* **Gradación de color interpolada**: se pasa de la gradación de la fase
  anterior a la de la actual a lo largo del propio tramo
  (`PostProcessing.set_color_grading`, una matriz 3×3 real), para que el
  cambio se vea progresivo y nunca se corte en seco.
* **Un relámpago-linterna en la Fase 3** (El Rey Terciopelo): la tormenta del
  guion, reusando el mismo mecanismo del diseño anterior.
* **Un camera shake único, en la Fase 4** (El Gavilán): el silencio súbito
  que pide el guion, con una sola sacudida fuerte y breve.
* **Un ciclo de luna en la Fase 5** (La Planicie de los Muertos): la luz
  ambiente oscila en vez de quedarse fija — la escena se ve y se pierde.
* **Grietas que se iluminan al paso en la Fase 6** (El Camino hacia Paburu):
  un rastro momentáneo, no una barra de progreso que se acumula.
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
from src.stages.stage4_1 import siluetas, trazado
from src.stages.stage4_1.fases import FASES, Fase, Gradacion, fase_en

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.framework.vfx.lighting import LightSource


#: La matriz identidad: cada canal de salida es el mismo canal de entrada.
#: Es lo que representa `gradacion=None` — "color pleno" — cuando hace falta
#: interpolar hacia o desde ella.
_IDENTIDAD: tuple[int, ...] = (255, 0, 0, 0, 255, 0, 0, 0, 255)


class Stage4_1(StageScene):
    """4-1 — El Cementerio Sagrado."""

    STAGE_ID: str = "stage4_1"
    STAGE_NAME: str = "4-1  EL CEMENTERIO SAGRADO"
    ZONE: int = 4
    BGM_TRACK: str = "bgm_final_approach"
    TMX_PATH = "assets/maps/stage4_1/stage4_1.tmx"

    # ── Relámpagos (Fase 3) ───────────────────────────────────
    DURACION_DEL_RAYO = 0.35
    FUERZA_DEL_RAYO = 0.5

    # ── El silencio y el shake (Fase 4) ────────────────────────
    #: A qué fracción del tramo ocurre el silencio. A mitad: ni al entrar
    #: (se leería como parte de la transición) ni al salir (se confundiría
    #: con la Fase 5).
    AVANCE_DEL_SILENCIO = 0.5
    DURACION_DEL_SHAKE = 0.45
    AMPLITUD_DEL_SHAKE = 14.0

    # ── El ciclo de luna (Fase 5) ──────────────────────────────
    PERIODO_DE_LA_LUNA = 6.0
    AMBIENTE_MIN_LUNA = 0.06
    AMBIENTE_MAX_LUNA = 0.48

    # ── Las grietas que se iluminan al paso (Fase 6) ───────────
    DISTANCIA_DE_GRIETA = 40.0
    SUBIDA_DE_GRIETA = 0.25
    BAJADA_DE_GRIETA = 1.6
    INTENSIDAD_MAX_GRIETA = 0.9

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        #: Índice de la fase actual, 0 a 5. Empieza fuera de rango para que
        #: el primer `update` **siempre** aplique la Fase 1 — con 0 aquí, la
        #: Fase 1 nunca se aplicaría (el fallo de «se inicializa a lo mismo
        #: que se compara», invisible sin comentarlo).
        self._fase_actual: int = -1
        self._tiempo: float = 0.0
        #: La gradación y el tinte de la fase anterior: de aquí interpola la
        #: gradación de la fase actual a lo largo del tramo.
        self._gradacion_previa: Gradacion = None
        self._tinte_previo: tuple[tuple[int, int, int], float] | None = None
        self._rayo: float = 0.0
        self._proximo_rayo: float = 0.0
        self._shake_disparado: bool = False
        #: Las luces de las grietas de la Fase 6 — apagadas de fábrica en el
        #: TMX, encendidas por proximidad y no permanentes.
        self._grietas: list[LightSource] = []
        self._intensidad_grieta: dict[int, float] = {}

    # ── Ciclo de vida ─────────────────────────────────────────

    def _setup_lighting(self) -> None:
        """Captura las luces de las grietas de la Fase 6.

        Se engancha aquí y no en `on_stage_start` por el mismo motivo que ya
        documentó el diseño anterior: `_stage_lights` todavía está vacía
        cuando corre `on_stage_start`, y `_setup_lighting` es el método que
        **crea** esa lista.

        Todas las luces del mapa son grietas —este TMX no tiene ninguna
        otra—, así que la lista entera vale tal cual, en el mismo orden en
        que las escribió `trazado.grietas_de_pisada()` y el generador.
        """
        super()._setup_lighting()
        self._grietas = list(self._stage_lights)
        self._intensidad_grieta.clear()

    # ── Actualización ─────────────────────────────────────────

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._player is None or self._stage_data is None:
            return
        self._tiempo += dt
        self._actualizar_fase()
        self._actualizar_gradacion()
        self._actualizar_ambiente_de_fase()
        self._actualizar_rayos(dt)
        self._actualizar_silencio_y_shake()
        self._actualizar_grietas(dt)

    @property
    def fase(self) -> Fase:
        """La fase en la que está el jugador ahora mismo.

        Se mira la **fila**, no la columna: el 4-1 es un pozo, se desciende.
        """
        if self._player is None:
            return FASES[0]
        return fase_en(self._player.rect.centery / settings.TILE_SIZE)

    def _avance_en_fase(self, fase: Fase) -> float:
        """0 al entrar en la fase, 1 al salir. Para interpolar."""
        if self._player is None:
            return 0.0
        recorrido = (self._player.rect.centery / settings.TILE_SIZE
                     - fase.desde_fila)
        return max(0.0, min(1.0, recorrido / trazado.ALTO_FASE))

    def _actualizar_fase(self) -> None:
        """Aplica la fase nueva, si el jugador cambió de tramo.

        Sólo se aplica **al cambiar**: llamar a `set_climate` en cada
        fotograma vaciaría el emisor de la tormenta sesenta veces por
        segundo y no se vería llover.
        """
        fase = self.fase
        if fase.numero - 1 == self._fase_actual:
            return
        anterior = FASES[self._fase_actual] if self._fase_actual >= 0 else fase
        self._gradacion_previa = anterior.gradacion
        self._tinte_previo = anterior.tinte
        self._fase_actual = fase.numero - 1

        self._cambiar_clima(fase.clima)
        self._ambient_particles.set_effect(*fase.particulas)
        # El ambiente de la fase pasa a ser la base sobre la que el ciclo
        # día/noche modula. Se escribe en `_ambiente_base` y no en el
        # sistema de luz directamente: si se escribiera directo,
        # `_aplicar_hora` lo pisaría en el siguiente fotograma.
        self._ambiente_base = fase.ambiente
        self._aplicar_hora()
        self._proximo_rayo = self._espera_entre_rayos()
        if fase.numero == 4:
            self._shake_disparado = False
        if self._banner is not None and fase.numero > 1:
            self._banner.play(f"FASE {fase.numero}", fase.nombre)

    # ── Gradación de color (Unidad V) ──────────────────────────

    @staticmethod
    def _lerp_gradacion(a: Gradacion, b: Gradacion, t: float) -> tuple[int, ...]:
        ga = a if a is not None else _IDENTIDAD
        gb = b if b is not None else _IDENTIDAD
        return tuple(round(ga[i] + (gb[i] - ga[i]) * t) for i in range(9))

    def _actualizar_gradacion(self) -> None:
        """Interpola de la gradación anterior a la de esta fase.

        Se interpola por **avance dentro del tramo**, no por tiempo — igual
        que el diseño anterior interpolaba la posición de la luna entre
        actos: el cambio se ve al caminar, no al esperar quieto.
        """
        fase = self.fase
        t = self._avance_en_fase(fase)
        if self._gradacion_previa is None and fase.gradacion is None:
            self._post_processing.clear_color_grading()
        else:
            self._post_processing.set_color_grading(
                *self._lerp_gradacion(self._gradacion_previa, fase.gradacion, t))

        # El tinte vintage de la Fase 4, entrando y saliendo con la misma
        # curva que la gradación — son dos sistemas separados en
        # `PostProcessing` y cada uno se interpola con su propio alfa.
        alfa_previa = self._tinte_previo[1] if self._tinte_previo is not None else 0.0
        if fase.tinte is not None:
            color, alfa_objetivo = fase.tinte
            alfa = alfa_previa + (alfa_objetivo - alfa_previa) * t
        else:
            color = self._tinte_previo[0] if self._tinte_previo is not None else (0, 0, 0)
            alfa = alfa_previa * (1.0 - t)
        if alfa <= 0.001:
            self._post_processing.clear_tint()
        else:
            self._post_processing.set_tint(color, alfa)

    def _actualizar_ambiente_de_fase(self) -> None:
        """El ciclo de luna de la Fase 5: la luz ambiente oscila.

        Las demás fases dejan `_ambiente_base` tal como lo puso
        `_actualizar_fase` — sólo la Planicie de los Muertos lo mueve cada
        fotograma.
        """
        fase = self.fase
        if not fase.luna_intermitente:
            return
        ciclo = 0.5 + 0.5 * math.sin(self._tiempo * (math.tau / self.PERIODO_DE_LA_LUNA))
        self._ambiente_base = (self.AMBIENTE_MIN_LUNA
                                + (self.AMBIENTE_MAX_LUNA - self.AMBIENTE_MIN_LUNA) * ciclo)
        self._aplicar_hora()

    # ── El relámpago de la Fase 3 ──────────────────────────────

    def _espera_entre_rayos(self) -> float:
        por_minuto = self.fase.rayos_por_minuto
        if por_minuto <= 0.0:
            return math.inf
        return random.uniform(0.5, 1.5) * (60.0 / por_minuto)

    def _actualizar_rayos(self, dt: float) -> None:
        if self._rayo > 0.0:
            self._rayo = max(0.0, self._rayo - dt)
            fuerza = (self._rayo / self.DURACION_DEL_RAYO) ** 2
            self._lighting.ambient_brightness = min(
                1.0, self.fase.ambiente + self.FUERZA_DEL_RAYO * fuerza)
            return
        if self.fase.rayos_por_minuto <= 0.0:
            return
        self._proximo_rayo -= dt
        if self._proximo_rayo <= 0.0:
            self._rayo = self.DURACION_DEL_RAYO
            self._proximo_rayo = self._espera_entre_rayos()
            self._play_sfx_named("sfx_environment_screen_shake", volume=0.4)

    # ── El silencio súbito y el shake (Fase 4) ─────────────────

    def _actualizar_silencio_y_shake(self) -> None:
        """A mitad de la Fase 4, el clima calla de golpe y sacude la cámara.

        Una sola vez por visita a la fase (`_shake_disparado`, que
        `_actualizar_fase` reinicia al entrar). Sin causa visible: es la
        sensación de que algo acaba de pasar sin que el jugador lo viera.
        """
        fase = self.fase
        if not fase.shake_de_silencio or self._shake_disparado:
            return
        if self._avance_en_fase(fase) < self.AVANCE_DEL_SILENCIO:
            return
        self._shake_disparado = True
        self._cambiar_clima("clear")
        self._ambient_particles.set_effect("", 0.0)
        self._camera.apply_shake(amplitude=self.AMPLITUD_DEL_SHAKE,
                                 duration=self.DURACION_DEL_SHAKE)
        self._play_sfx_named("sfx_environment_cemetery_silence", volume=0.5)

    # ── Las grietas de la Fase 6 ────────────────────────────────

    def _actualizar_grietas(self, dt: float) -> None:
        """Se encienden por proximidad y se apagan solas: un rastro, no una
        barra de progreso acumulada (a diferencia de los braseros del diseño
        anterior)."""
        if self._player is None or not self._grietas:
            return
        centro = pygame.Vector2(self._player.rect.center)
        for i, luz in enumerate(self._grietas):
            actual = self._intensidad_grieta.get(i, 0.0)
            if centro.distance_to(luz.position) <= self.DISTANCIA_DE_GRIETA:
                actual = min(1.0, actual + dt / self.SUBIDA_DE_GRIETA)
            else:
                actual = max(0.0, actual - dt / self.BAJADA_DE_GRIETA)
            self._intensidad_grieta[i] = actual
            luz.intensity = actual * self.INTENSIDAD_MAX_GRIETA

    # ── Dibujo ────────────────────────────────────────────────

    def dibujar_fondo(self, surface: pygame.Surface,
                      offset: pygame.Vector2) -> None:
        """El espíritu de la fase, detrás del mapa — igual que el diseño
        anterior pintaba sus siluetas: son recuerdos, no primer plano."""
        self._dibujar_espiritu(surface, offset)

    @staticmethod
    def _fundido_del_espiritu(avance: float) -> float:
        """0 al entrar y al salir de la fase, 1 en medio.

        Entra en el primer 15 % del tramo y se desvanece —**asciende**— en
        el último 15 %. El 70 % del centro es donde testifica, quieto salvo
        por el vaivén.
        """
        entra = min(1.0, avance / 0.15)
        sale = min(1.0, (1.0 - avance) / 0.15)
        return min(entra, sale)

    def _dibujar_espiritu(self, surface: pygame.Surface,
                          offset: pygame.Vector2) -> None:
        fase = self.fase
        if fase.espiritu is None:
            return
        _nombre, forma = siluetas.ESPIRITUS[fase.espiritu]
        avance = self._avance_en_fase(fase)
        fundido = self._fundido_del_espiritu(avance)
        if fundido <= 0.0:
            return
        # Asciende de verdad en el último tramo: sube por la pantalla en vez
        # de sólo desvanecerse en el sitio.
        ascenso = max(0.0, (avance - 0.85) / 0.15) * 90.0
        vaiven = math.sin(self._tiempo * 0.35) * 6.0
        x = int(settings.INTERNAL_WIDTH * 0.62
                - offset.x * 0.12) % (settings.INTERNAL_WIDTH + 260) - 130
        alto = 120
        y = int(230 + vaiven - ascenso)
        alfa = int(150 * fundido)
        siluetas.dibujar_contorno(
            surface, forma, x, y, int(alto * 0.9), alto,
            siluetas.VERDE_ESPECTRAL, alfa,
        )
