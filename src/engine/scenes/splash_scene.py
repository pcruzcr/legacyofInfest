from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import BOTTOM_BAR_Y
from src.engine.scenes.title_scene import TitleScene
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

logger = logging.getLogger(__name__)


class SplashScene(BaseScene):
    """Game startup splash screen."""

    SPLASH_TIME = 3.0

    # AUD-082: hay que dejar pasar un fotograma antes de compilar el núcleo de
    # partículas. Si se hiciera en `on_enter`, la ventana se quedaría en negro
    # medio segundo antes de mostrar el logo: habríamos movido el tirón, no
    # escondido.
    _WARMUP_AFTER_FRAMES = 2

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._timer = 0.0
        self._fading_out: bool = False
        self._frames_shown = 0
        self._warmed_up = False
        self._warmup_index = 0
        assets = settings.ASSETS_DIR / "splash"

        self._background = AssetLoader.load_image(
            assets / "bck1.png",
            size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )

        raw_logo = AssetLoader.load_image(assets / "logo.png")
        max_logo_w = settings.INTERNAL_WIDTH - 40
        max_logo_h = 90
        lw, lh = raw_logo.get_size()
        scale = min(max_logo_w / lw, max_logo_h / lh, 1.0)
        self._logo = AssetLoader.load_image(
            assets / "logo.png",
            size=(int(lw * scale), int(lh * scale)),
        )
        self._logo_shadow = self._logo.copy()
        self._logo_shadow.fill((0, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)

        self._music = assets / "bck.wav"

        self._font_game = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", 14,
        )
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", 10,
        )

    def on_enter(self) -> None:
        self._timer = 0.0
        audio = self.audio
        if audio is not None:
            audio.play_music(self._music, loops=0)

    def on_exit(self) -> None:
        audio = self.audio
        if audio is not None:
            audio.stop_music()

    def update(self, dt: float) -> None:
        if self._fading_out:
            if self.context.scene_manager.transition.finished:
                self.context.scene_manager.replace(TitleScene(self.context))
            return
        self._timer += dt
        self._warm_up_particles()
        if self._timer >= self.SPLASH_TIME:
            self.context.scene_manager.transition.start_fade_out(0.5)
            self._fading_out = True

    @staticmethod
    def _precalentar_particulas() -> None:
        """Compila el núcleo JIT que actualiza las partículas.

        AUD-082: `numba.njit` compila en la primera llamada, y esa llamada caía
        en el primer fotograma con partículas — la pantalla de título. Medido
        allí: mediana de 0,70 ms y **un fotograma de 376 ms**.
        """
        from src.framework.vfx.particle_system import warmup

        warmup()

    @staticmethod
    def _precalentar_ia() -> None:
        """Carga scikit-learn antes de que lo pida un enemigo.

        AUD-088: `squad_brain` importa `ai_predictor` la primera vez que
        consulta al predictor, y ese import arrastra scikit-learn entero.
        Medido en Stage 0: un tirón de **2,3 s en el fotograma 16**, ya dentro
        de la partida y con enemigos en pantalla. Peor que el de la pantalla de
        título, porque aquí el jugador está intentando moverse.

        scikit-learn es opcional: sin él la IA cae a su heurística, así que un
        `ImportError` no es un fallo.
        """
        try:
            from src.framework.entities import ai_predictor  # noqa: F401
        except ImportError:
            pass

    #: Un paso por fotograma. Ejecutarlos todos de golpe sumaba 3,4 s de
    #: congelación —más que la propia pantalla de inicio— y el logo se quedaba
    #: quieto de una vez. Repartidos, entre uno y otro se dibuja un fotograma y
    #: el fundido sigue avanzando.
    _WARMUP_STEPS = ("_precalentar_particulas", "_precalentar_ia")

    def _warm_up_particles(self) -> None:
        """Ejecuta un paso de precalentamiento por fotograma.

        La pantalla de inicio dura 3 s, no es interactiva y su `update` no hace
        nada más que contar el tiempo. Es el único sitio del arranque donde
        medio segundo no se nota, y por eso se paga aquí lo que de otro modo se
        pagaría a mitad de partida.

        No se hace en `on_enter` a propósito: eso retrasaría el primer
        fotograma y el jugador vería una ventana negra en vez del logo.
        """
        import time

        self._frames_shown += 1
        if self._warmed_up or self._frames_shown < self._WARMUP_AFTER_FRAMES:
            return

        paso = self._WARMUP_STEPS[self._warmup_index]
        t0 = time.perf_counter()
        getattr(self, paso)()
        coste = time.perf_counter() - t0
        if coste > 0.05:
            logger.info(
                "arranque: %s tardó %.0f ms durante la pantalla de inicio",
                paso.removeprefix("_precalentar_"), coste * 1000,
            )

        self._warmup_index += 1
        if self._warmup_index >= len(self._WARMUP_STEPS):
            self._warmed_up = True

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))

        logo_rect = self._logo.get_rect(
            center=(settings.INTERNAL_WIDTH // 2, settings.INTERNAL_HEIGHT // 2 - 35),
        )

        surface.blit(self._logo_shadow, (logo_rect.x + 3, logo_rect.y + 3))
        surface.blit(self._logo, logo_rect)

        loading = self._font_game.render("Cargando...", True, (255, 255, 255))
        lr = loading.get_rect(center=(settings.INTERNAL_WIDTH // 2, BOTTOM_BAR_Y - 36))
        loading.set_alpha(int(min(self._timer / self.SPLASH_TIME, 1.0) * 255))
        surface.blit(loading, lr)

        progress = min(self._timer / self.SPLASH_TIME, 1.0)
        BAR_W, BAR_H = 170, 6
        bar_rect = pygame.Rect(
            (settings.INTERNAL_WIDTH - BAR_W) // 2, BOTTOM_BAR_Y - 18,
            BAR_W, BAR_H,
        )
        pygame.draw.rect(surface, (45, 45, 45), bar_rect, border_radius=3)
        pygame.draw.rect(
            surface, (255, 210, 0),
            (bar_rect.x, bar_rect.y, int(progress * BAR_W), BAR_H),
            border_radius=3,
        )

        version = self._font_small.render("Prototype v0.1", True, (180, 180, 180))
        surface.blit(version, (6, BOTTOM_BAR_Y - 8))

        self.context.scene_manager.transition.draw(surface)

        cr = self._font_small.render("© 2026 Legacy of InFest", True, (180, 180, 180))
        surface.blit(cr, (settings.INTERNAL_WIDTH - cr.get_width() - 6, BOTTOM_BAR_Y - 8))

