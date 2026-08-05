from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.audio.audio_manager import AudioManager
from src.engine.core import gpu_effects, settings, user_settings
from src.engine.core.clock import DeltaClock
from src.engine.core.difficulty import Difficulty, set_difficulty
from src.engine.core.event_bus import EventBus
from src.engine.core.game_context import GameContext
from src.engine.core.registro import configurar_registro
from src.engine.core.save_manager import SaveManager
from src.engine.input.input_manager import InputManager
from src.engine.scene.scene_manager import SceneManager
from src.framework import FrameworkUsageError

if TYPE_CHECKING:
    from src.engine.render import GLRenderer

logger = logging.getLogger(__name__)


def modo_daltonico_gl(ajustes: object | None) -> int:
    """Traduce la preferencia del jugador al entero que espera el sombreador.

    AUD-252 — el eslabón que faltaba. `colorblind_frag` estaba escrito,
    compilado y enchufado a su pasada, y esa pasada sólo corre si
    `config.colorblind_mode > 0`. Nadie escribía nunca ese campo: se quedaba en
    0 y el sombreador no se ejecutaba jamás, así que elegir `deuteranopia` en
    Opciones no hacía nada en cuanto la máquina tenía tarjeta.

    El contrato es el orden de `COLORBLIND_MODES`, que es el mismo que declara
    `shaders.py` (`0=off, 1=protanopia, 2=deuteranopia, 3=tritanopia`).

    Un valor que no esté en la tupla devuelve 0 en vez de reventar: quedarse
    sin corrección de color es malo, quedarse sin fotograma es peor.
    """
    modo = getattr(ajustes, "colorblind_mode", "off")
    try:
        return user_settings.COLORBLIND_MODES.index(str(modo))
    except ValueError:
        return 0


class App:
    def __init__(self, use_gl: bool = True, depurar: bool = False) -> None:
        self.depurar = depurar
        self._use_gl = use_gl
        # AUD-124 — sin anotación, mypy infiere el tipo `None` y toda
        # llamada posterior a `self._gl_renderer.init(...)` es un error.
        # `GLRenderer` sólo se importa para comprobar tipos: importarlo
        # en tiempo de ejecución arrastraría moderngl aunque el juego
        # arranque sin GL, que es el caso que este atributo existe para
        # soportar.
        self._gl_renderer: GLRenderer | None = None
        self._init_pygame()
        self._init_subsystems()

    def _init_pygame(self) -> None:
        pygame.init()
        pygame.display.set_caption("Legacy of InFest")

        if self._use_gl:
            try:
                import moderngl  # noqa: F401
                pygame.display.set_mode(
                    (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
                    pygame.OPENGL | pygame.DOUBLEBUF,
                )
                self._init_gl()
            # `(ImportError, pygame.error, Exception)` was redundant — Exception
            # subsumes both — and swallowed genuine GL bugs as "not available".
            # We still fall back on any failure, but say what actually broke.
            except ImportError:
                logger.info("ModernGL not installed — using software rendering")
                self._use_gl = False
            except Exception:
                logger.warning(
                    "GL context creation failed — falling back to software rendering",
                    exc_info=True,
                )
                self._use_gl = False

        if not self._use_gl:
            # SCALED lets SDL letterbox/upscale the window for us, so the
            # display surface stays at the internal resolution and _draw() can
            # blit 1:1. See _draw() for why DISPLAY_SCALE is not applied here.
            pygame.display.set_mode(
                (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
                pygame.SCALED,
            )

        # AUD-012: an unguarded mixer.init() aborts startup on any machine with
        # no audio device — headless CI, a locked ALSA device, a VM without a
        # sound card, or a user who has muted output at the driver level. A
        # game must not refuse to launch because it cannot make noise.
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=8, buffer=512)
        except pygame.error:
            logger.warning(
                "No audio device available — continuing without sound", exc_info=True,
            )

        self.internal_surface = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )
        self._scaled_surface: pygame.Surface | None = None
        self._last_scale: int = 0
        self.clock = DeltaClock()
        self.running: bool = False

    def _init_gl(self) -> None:
        try:
            from src.engine.render import GLRenderConfig, GLRenderer
            cfg = GLRenderConfig()
            self._gl_renderer = GLRenderer(cfg)
            self._gl_renderer.init(pygame.display.get_surface())
        except Exception as e:
            logger.warning("GL initialization failed: %s", e)
            self._use_gl = False
            return
        # AUD-222 — el reparto se declara aquí y en ningún otro sitio: ésta es
        # la única función del árbol que sabe a la vez que el contexto GL se
        # creó **de verdad** y qué pasadas trae encendidas la configuración.
        # Va después del `init`, no antes, porque hasta que éste no vuelve sin
        # excepción no hay tarjeta que se haga cargo de nada; declararlo antes
        # dejaría a la CPU sin dibujar el bloom en una máquina que acaba de
        # caerse al camino software.
        gpu_effects.set_effects_on_gpu(cfg.cpu_effects_taken_over())

    def _init_subsystems(self) -> None:
        # AUD-268 — lo primero de todo: sin esto, Python usa su manejador de
        # último recurso y los 134 `logger.warning` del árbol salen por la
        # consola mientras el jugador juega. Van a un fichero junto a las
        # partidas; `--debug` los devuelve a la pantalla.
        configurar_registro(depurar=self.depurar)
        self.event_bus = EventBus()

        # AUD-283 — la consola de depuración, que existía sin que nadie la
        # abriera. Vive en `App` y no en `StageScene` porque sirve igual en un
        # menú, en un laboratorio y en un nivel: lo que mide —FPS, coste del
        # fotograma, cola de eventos— es del motor, no del escenario.
        from src.engine.scenes.debug_overlay import DebugOverlay
        self.debug_overlay = DebugOverlay(self.event_bus)

        # AUD-036: load persisted player preferences before anything reads them,
        # and apply the ones other subsystems own (volumes, difficulty). The
        # options screen previously wrote these to disk and nothing loaded them
        # back, so accessibility settings could never take effect.
        self.user_settings = user_settings.UserSettings.load()
        user_settings.set_settings(self.user_settings)
        # F3.1: el idioma se aplica aquí, antes de construir ninguna escena.
        # Si se hiciera más tarde, las pantallas ya creadas se quedarían con
        # el texto del idioma anterior hasta recrearse.
        from src.engine.core.i18n import set_idioma
        set_idioma(self.user_settings.language)

        self.input_manager = InputManager()
        self.audio_manager = AudioManager()
        self.save_manager = SaveManager()

        self.audio_manager.music_volume = self.user_settings.music_volume
        self.audio_manager.sfx_volume = self.user_settings.sfx_volume
        for difficulty in Difficulty:
            if difficulty.value == self.user_settings.difficulty:
                set_difficulty(difficulty)
                break

        self.context = GameContext(
            input_manager=self.input_manager,
            audio_manager=self.audio_manager,
            scene_manager=None,
            event_bus=self.event_bus,
            clock=self.clock,
            save_manager=self.save_manager,
        )

        # AUD-018: App is the composition root, so it — not the scene manager —
        # is where knowledge of concrete scene classes belongs. Injecting these
        # keeps engine.scene free of any import into engine.scenes.
        from src.engine.scenes.end_credits_scene import EndCreditsScene
        from src.engine.scenes.title_scene import TitleScene

        self.scene_manager = SceneManager(
            self.context,
            title_factory=TitleScene,
            credits_factory=EndCreditsScene,
        )
        self.context.scene_manager = self.scene_manager

        from src.framework.entities.entity_factory import ensure_registered
        ensure_registered()
        from src.engine.scenes.scene_registry import register_demo_scenes
        register_demo_scenes()

        # AUD-098: reanudar al estudiante que se identificó la última vez.
        #
        # Sin esto, el progreso académico se guardaba y **nadie volvía a
        # leerlo nunca**: se podían aprobar cinco unidades, cerrar el juego, y
        # encontrarse el temario entero bloqueado otra vez con las notas
        # intactas en el disco pero inalcanzables.
        #
        # Falla en silencio a propósito. Si el fichero de progreso está roto o
        # el disco no deja leer, se sigue como anónimo: perder unas notas de
        # prácticas es malo, que el juego no arranque el día de la entrega es
        # peor.
        from src.framework.academic.sesion import SesionAcademica
        try:
            SesionAcademica.instancia().reanudar()
        except OSError:
            logger.warning("no se pudo reanudar la sesión académica", exc_info=True)

        from src.engine.scenes.splash_scene import SplashScene
        self.scene_manager.push(SplashScene(self.context))

    # Consecutive frames that may fail before we stop trying to recover.
    # Without a ceiling, a scene that raises on every update spins the loop at
    # full speed forever, writing a stack trace per frame until the disk fills
    # (AUD-015) — the player sees a frozen window and no way out.
    MAX_CONSECUTIVE_FRAME_ERRORS = 10

    def run(self) -> None:
        self.running = True
        consecutive_errors = 0
        while self.running and self.context.running:
            dt = self.clock.tick()
            self._process_events()
            self.event_bus.dispatch()
            # AUD-144 — la mezcla avanza con tiempo REAL, aquí y no dentro de
            # una escena: el *ducking* tiene que seguir moviéndose en el menú
            # de pausa y durante una ralentización, o la música se quedaría
            # agachada esperando a que el mundo vuelva a correr.
            self.audio_manager.update(getattr(self.clock, "unscaled_dt", dt))

            frame_failed = False
            try:
                self.scene_manager.update(dt)
                self.scene_manager.transition.update(dt)
            except FrameworkUsageError as exc:
                # AUD-055: un mapa mal formado no es un fallo del motor, es un
                # dato que el estudiante necesita leer. Volver al título en
                # silencio esconde precisamente el mensaje que explica qué
                # arreglar.
                logger.error("Stage load failed:\n%s", exc)
                frame_failed = True
                self._show_usage_error(exc)
            except Exception:
                logger.exception("Unhandled exception in scene update")
                frame_failed = True
                self._fallback_to_title()
            else:
                try:
                    self._draw(dt)
                except Exception:
                    logger.exception("Unhandled exception in scene draw")
                    frame_failed = True
                    self._fallback_to_title()

            if frame_failed:
                consecutive_errors += 1
                if consecutive_errors >= self.MAX_CONSECUTIVE_FRAME_ERRORS:
                    logger.critical(
                        "Aborting: %d consecutive frame failures — the fallback "
                        "scene is failing too, so recovery is not possible.",
                        consecutive_errors,
                    )
                    self.running = False
            else:
                consecutive_errors = 0

            if not self._use_gl:
                pygame.display.flip()
        self._shutdown()

    def _process_events(self) -> None:
        events = pygame.event.get()
        has_quit = False
        for e in events:
            if e.type == pygame.QUIT:
                has_quit = True
        self.input_manager.pump(events)
        # AUD-283 — la consola se lee aquí, antes que la escena, y a propósito:
        # una escena modal —el menú de pausa, un diálogo— consume sus teclas y
        # dejaría la consola sin poder abrirse justo cuando hace falta mirarla.
        self.debug_overlay.handle_input(self.input_manager)
        if has_quit:
            self.running = False
            return
        if self.scene_manager.stack_size > 0:
            self.scene_manager.current.process_events(events)

    def _draw(self, dt: float = 0.0) -> None:
        # AUD-222 — se olvida lo publicado en el fotograma anterior *antes* de
        # que dibuje nadie. Los menús no ejecutan post-procesado, así que sin
        # este borrón la pantalla de título heredaría el bloom del nivel del
        # que se acaba de salir y seguiría brillando hasta entrar en otro.
        gpu_effects.begin_frame()
        self.internal_surface.fill(settings.BG_COLOR)
        if self.scene_manager.stack_size > 0:
            self.scene_manager.current.draw(self.internal_surface)
        self.scene_manager.transition.draw(self.internal_surface)

        # AUD-283 — la consola, encima de la escena y debajo del post-procesado.
        #
        # Debajo a propósito: si se pintara después del camino GL, el bloom y la
        # aberración cromática no la tocarían y se leería como una capa ajena al
        # juego. Pasando por las mismas pasadas se ve lo que el jugador ve, que
        # es justamente lo que hay que depurar.
        if self.debug_overlay.visible:
            medidas: dict = {}
            if self.scene_manager.stack_size > 0:
                try:
                    medidas = dict(
                        self.scene_manager.current.medidas_de_depuracion())
                except Exception:
                    # Una escena de estudiante que falle al contarse no puede
                    # tumbar el fotograma: la consola es una herramienta, no
                    # parte del juego.
                    logger.exception("medidas_de_depuracion falló")
                    medidas = {"medidas": "error (ver el registro)"}
            self.debug_overlay.draw(
                self.internal_surface, self.clock.fps, medidas)

        if self._use_gl and self._gl_renderer:
            # La escena acaba de decir cuánto bloom quiere mientras dibujaba;
            # se recoge aquí, ya con todas las capas dentro, y antes de que la
            # pasada lo lea.
            self._gl_renderer.config.bloom_intensity = gpu_effects.published_bloom()
            # AUD-215 — el golpe que pidió la escena al recibir daño, y el
            # decaimiento. El impulso se recoge (y se borra) aquí; mantenerlo
            # vivo mientras se apaga es cosa del renderizador, que es quien
            # sabe cuánto tiempo ha pasado.
            impulso = gpu_effects.consume_chromatic_aberration()
            if impulso > 0.0:
                self._gl_renderer.trigger_chromatic_aberration(impulso)
            self._gl_renderer.update_chromatic_aberration(dt)
            # AUD-216 — la región de agua que la escena acaba de publicar.
            # `None` apaga la pasada, que es lo que pasa en los menús y en los
            # catorce escenarios sin agua.
            self._gl_renderer.set_refraction_region(
                gpu_effects.published_water_region(), dt,
            )
            # AUD-226 — los rayos: foco y fuerza, o apagados. El foco lo
            # decide la escena porque es la única que sabe qué luz manda.
            rayos = gpu_effects.published_god_rays()
            cfg = self._gl_renderer.config
            # AUD-252 — la accesibilidad se sincroniza aquí, cada fotograma,
            # porque Opciones la cambia en caliente: leerla sólo al crear el
            # contexto habría dejado un modo daltónico que exige reiniciar.
            # Es una comparación de enteros; la pasada sólo se monta si > 0.
            cfg.colorblind_mode = modo_daltonico_gl(
                getattr(self, "user_settings", None))
            cfg.godray_enabled = rayos is not None
            if rayos is not None:
                cfg.godray_origin, cfg.godray_exposure = rayos
            self._gl_renderer.render(self.internal_surface, self._current_light_surface())
        else:
            # AUD-013: this used to upscale internal_surface by
            # settings.DISPLAY_SCALE and blit the result at (0, 0). The display
            # surface, however, is created at the *internal* resolution, so with
            # LOI_DISPLAY_SCALE=2 the game rendered an 1600x1200 image into an
            # 800x600 window: everything but the top-left quadrant was clipped
            # away, and two full-screen scale operations were paid every frame
            # for the privilege. pygame.SCALED already asks SDL to upscale the
            # window for us on the GPU, so the correct blit is 1:1.
            pygame.display.get_surface().blit(self.internal_surface, (0, 0))

    def _current_light_surface(self) -> pygame.Surface | None:
        """The active scene's lighting buffer, if it exposes one.

        Scenes opt in by implementing ``light_surface``; the previous code
        reached through two layers of privates
        (``scene._lighting._surface``), which coupled the application shell to
        the internals of a specific VFX class.
        """
        if self.scene_manager.stack_size == 0:
            return None
        scene = self.scene_manager.current
        surface = getattr(scene, "light_surface", None)
        if isinstance(surface, pygame.Surface):
            return surface
        # Backward compatibility with scenes that have not adopted the
        # property yet.
        lighting = getattr(scene, "_lighting", None)
        legacy = getattr(lighting, "_surface", None)
        return legacy if isinstance(legacy, pygame.Surface) else None

    def _show_usage_error(self, exc: Exception) -> None:
        """Muestra en pantalla un error de uso del framework.

        Se recurre al título sólo si la propia pantalla de error falla: dejar
        al estudiante sin nada que leer es el estado que este método existe
        para evitar, así que conviene degradar en un único paso y no en dos.
        """
        from src.engine.scenes.stage_error_scene import StageErrorScene

        failed_scene = None
        if self.scene_manager.stack_size > 0:
            failed_scene = type(self.scene_manager.current)

        try:
            self.context.scene_manager.replace(
                StageErrorScene(
                    self.context, str(exc),
                    retry=self._retry_factory(failed_scene),
                ),
            )
        except Exception:
            logger.exception("Error scene failed; falling back to title")
            self._fallback_to_title()

    def _retry_factory(self, scene_cls: type | None):
        """Reintento que vuelve a construir la escena que falló, o `None`.

        Devolver `None` cuando no se puede reconstruir es deliberado: la
        pantalla de error oculta la tecla `R` si no hay reintento posible, y
        una tecla anunciada que no hace nada es peor que una tecla ausente.
        """
        if scene_cls is None:
            return None

        def _retry() -> None:
            try:
                self.context.scene_manager.replace(scene_cls(self.context))
            except FrameworkUsageError as exc:
                # El mapa sigue mal, o está mal de otra forma. Se vuelve a
                # mostrar el informe en lugar de dejar escapar la excepción:
                # `process_events` corre fuera del try del bucle principal, así
                # que sin esto el reintento cerraría el juego.
                logger.error("Stage reload failed:\n%s", exc)
                self._show_usage_error(exc)
            except Exception:
                logger.exception("Stage reload failed unexpectedly")
                self._fallback_to_title()

        return _retry

    def _fallback_to_title(self) -> None:
        from src.engine.scenes.title_scene import TitleScene
        try:
            self.context.scene_manager.replace(TitleScene(self.context))
        except Exception:
            logger.exception("Fallback to title also failed")
            self.running = False

    def _shutdown(self) -> None:
        if self._gl_renderer:
            self._gl_renderer.destroy()
        self.context.quit()
        self.scene_manager.cleanup()
        pygame.quit()
