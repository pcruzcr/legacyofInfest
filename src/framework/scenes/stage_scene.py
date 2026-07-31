from __future__ import annotations

import random
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.engine.core.achievements import AchievementSystem
from src.engine.core.events import Events
from src.engine.core.inventory import get_inventory
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.hud import HUD
from src.engine.ui.message_box import MessageBox
from src.engine.ui.minimap import Minimap
from src.engine.ui.screen_banner import ScreenBanner
from src.engine.ui.subtitle_overlay import SubtitleOverlay
from src.engine.utils.asset_loader import AssetLoader
from src.framework.audio.dynamic_music import DynamicMusicSystem
from src.framework.entities.bestiary import Bestiary
from src.framework.entities.boss_base import BossBase
from src.framework.entities.enemy_base import EnemyBase
from src.framework.entities.player import Player
from src.framework.entities.squad_brain import SquadBrain
from src.framework.stage.camera import Camera
from src.framework.stage.collision_system import CollisionSystem
from src.framework.stage.drawing_system import DrawingSystem
from src.framework.stage.hazard_system import HazardSystem
from src.framework.stage.interactable_system import InteractableSystem
from src.framework.stage.progression_system import ProgressionSystem
from src.framework.stage.speedrun_mode import SpeedrunTimer
from src.framework.stage.stage_loader import StageLoader
from src.framework.ui.dialogue_system import DialogueSystem
from src.framework.ui.learning_overlay import LearningOverlay
from src.framework.ui.tutorial_overlay import TutorialOverlay
from src.framework.vfx.ambient_particles import AmbientParticleSystem
from src.framework.vfx.damage_numbers import DamageNumberManager
from src.framework.vfx.hit_effects import HitEffects
from src.framework.vfx.lighting import LightSource, LightSystem
from src.framework.vfx.particle_system import ParticleSystem
from src.framework.vfx.post_processing import PostProcessing
from src.framework.vfx.trail_system import TrailSystem
from src.framework.vfx.weather_system import WeatherSystem

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.framework.stage.checkpoint import Checkpoint
    from src.framework.stage.stage_loader import StageData


class StageScene(BaseScene):
    TMX_PATH: Path | None = None

    def __init__(self, context: GameContext, tmx_path: Path | None = None) -> None:
        resolved = tmx_path if tmx_path is not None else self.TMX_PATH
        if resolved is None:
            raise TypeError(
                f"{type(self).__name__}.__init__ missing required 'tmx_path'. "
                f"Set TMX_PATH on the class or pass tmx_path=..."
            )
        self._tutorial_shown: set[str] = set()
        super().__init__(context)
        self._tmx_path = resolved
        self._stage_data: StageData | None = None
        self._player: Player | None = None
        self._camera: Camera = Camera()
        self._hud: HUD | None = None
        self._msg_box: MessageBox | None = None
        self._banner: ScreenBanner | None = None
        self._checkpoints: list[Checkpoint] = []
        self._checkpoint_reached: int | None = None
        self._checkpoint_position: pygame.Vector2 | None = None
        self._stage_complete: bool = False
        self._game_over: bool = False
        self._paused: bool = False
        self._pause_selected: int = 0
        self._pause_options: list[str] = ["Resume", "Save & Quit", "Quit to Title"]
        self._debug: bool = False
        self._was_grounded: bool = False
        self._pending_game_over: bool = False

        self._collision = CollisionSystem(context)
        # AUD-050: decisiones tácticas por lotes a 4 Hz. Consulta el predictor
        # sklearn una sola vez por ciclo para todos los enemigos; llamarlo por
        # enemigo y fotograma costaba 17 ms — el presupuesto completo.
        self._squad = SquadBrain()
        self._hazards = HazardSystem(context)
        # F4.1 — recogibles, cerraduras, cofres y disparadores.
        self._interactables = InteractableSystem(bus=context.event_bus)
        self._progression = ProgressionSystem(context)
        self._drawing = DrawingSystem()
        self._particle_system = ParticleSystem()
        self._damage_numbers = DamageNumberManager()
        self._post_processing = PostProcessing()
        self._ambient_particles = AmbientParticleSystem()
        self._weather = WeatherSystem()
        self._trail_system = TrailSystem()
        self._enemy_trail_system = TrailSystem()
        #: Última x conocida de cada entidad, para deducir su velocidad.
        self._enemy_prev_x: dict[int, float] = {}
        self._lighting = LightSystem(ambient_brightness=0.7)
        self._player_light: LightSource | None = None
        self._stage_lights: list[LightSource] = []
        audio_mgr = self.context.audio_manager if hasattr(self.context, 'audio_manager') else None
        self._dynamic_music = DynamicMusicSystem(audio_mgr) if audio_mgr is not None else None
        self._tutorial = TutorialOverlay()
        self._learning = LearningOverlay()
        self._minimap = Minimap()
        # AUD-036: captions for non-speech audio, active when the player has
        # enabled subtitles. Retained here so the bus's weak refs stay alive.
        self._subtitles = SubtitleOverlay(self.context.event_bus)
        self._achievements = AchievementSystem.get_instance()
        # AUD-019: hand the achievement system the same bus this scene uses,
        # instead of it reaching for a module-level default.
        self._achievements.bind_bus(self.context.event_bus)
        self._achievements.load()
        self._bestiary = Bestiary.get_instance()
        self._speedrun = SpeedrunTimer()
        self._dialogue = DialogueSystem(self.context)
        self._player_spawned: bool = False
        self._damage_taken_this_stage: float = 0.0
        self._stage_start_time: float = 0.0
        self._sfx_handlers: dict[str, Callable[..., None]] = {}
        self._vfx_handlers: dict[str, Callable[..., None]] = {}

    def on_stage_start(self) -> None:
        if "move" not in self._tutorial_shown:
            self._tutorial.show("move", duration=6.0)
            self._tutorial_shown.add("move")

    def _actualizar_arco(self, dt: float, player: object, im: object, stage: object) -> None:
        """F4.2 — disparo a distancia.

        El arma no conoce la escena ni la escena decide su munición: el arco
        informa de qué flecha tocó a quién y aquí se aplica el daño, porque
        quién puede dañar a quién es una regla del escenario y no del arma.
        """
        arco = getattr(player, "arco", None)
        if arco is None:
            return

        arco.update(dt)
        if im is not None and im.is_action_just_pressed(Action.RANGED_ATTACK):
            origen = pygame.Vector2(player.rect.centerx, player.rect.centery)
            if arco.disparar(origen, player.facing) is not None:
                self.context.event_bus.emit(Events.SFX_PLAYER_SHORT_ATTACK)

        # Una flecha que da en la pared se para; si no, atraviesa el nivel.
        arco.choca_con_muros(stage.collision_rects)

        enemigos = [e for e in stage.entity_list if hasattr(e, "apply_hit")]
        for flecha, objetivo in arco.impactos_contra(enemigos):
            objetivo.apply_hit(flecha.damage, (flecha.rect.centerx, flecha.rect.centery))
            self._damage_numbers.add(
                flecha.rect.centerx, flecha.rect.top, str(round(flecha.damage, 1)),
            )

    def on_player_landed(self) -> None:
        if "landed" not in self._tutorial_shown and hasattr(self, '_player') and self._player is not None:
            if abs(self._player.velocity.x) > 0:
                self._tutorial.show("attack", duration=5.0)
                self._tutorial_shown.add("landed")

    def on_enemy_died(self, enemy: EnemyBase) -> None:
        if hasattr(enemy, "enemy_id"):
            self._bestiary.record_kill(enemy.enemy_id)
        if "enemy_kill" not in self._tutorial_shown:
            self._tutorial.show("advanced", duration=5.0)
            self._tutorial_shown.add("enemy_kill")

    def on_next_trigger_entered(self) -> None:
        if "checkpoint" not in self._tutorial_shown:
            self._tutorial.show("checkpoint", duration=3.0)
            self._tutorial_shown.add("checkpoint")

    def on_debug_toggle(self, enabled: bool) -> None:
        ...

    def on_enter(self) -> None:
        # AUD-025: claim a cache scope so that leaving this scene does not throw
        # away assets a scene paused beneath us is still using.
        AssetLoader.enter_scope()
        self._subtitles.rearm()
        data = StageLoader.load(self._tmx_path)
        if data is None:
            raise RuntimeError(f"StageScene: failed to load stage from {self._tmx_path}")
        self._stage_data = data
        spawn = self._stage_data.spawn_point
        self._player = Player(spawn, event_bus=self.context.event_bus)
        if hasattr(self._stage_data, "gravity_multiplier"):
            self._player.gravity_multiplier = self._stage_data.gravity_multiplier

        pending = self.context.pending_load
        if pending is not None and pending.stage_id == self._stage_data.stage_id:
            self._player.set_spawn(pygame.Vector2(pending.checkpoint_x, pending.checkpoint_y))
            self._player.set_health(pending.health)
            self._checkpoint_position = pygame.Vector2(pending.checkpoint_x, pending.checkpoint_y)
            self.context.pending_load = None

        # AUD-022: relic stat bonuses were fully implemented and never applied.
        self._player.apply_relic_bonuses(get_inventory())

        self._achievements.mark_explorer(self._stage_data.stage_id)

        self._camera = Camera()
        self._camera.follow(self._player)
        self._camera.set_map_size(*self._stage_data.map_pixel_size)

        for enemy in self._stage_data.entity_list:
            if hasattr(enemy, "set_event_bus"):
                enemy.set_event_bus(self.context.event_bus)
            elif not getattr(enemy, "_event_bus", None):
                enemy._event_bus = self.context.event_bus
            if hasattr(enemy, "set_player_ref"):
                enemy.set_player_ref(self._player.rect)
            if hasattr(enemy, "set_collision_rects"):
                enemy.set_collision_rects(
                    self._stage_data.collision_rects,
                    one_way=self._stage_data.one_way_rects,
                )
            if isinstance(enemy, BossBase):
                # AUD-061: el jefe necesita saber dónde acaba su arena, y la
                # escena es quien conoce el tamaño del mapa. `BossVenado` la
                # tenía escrita a mano como ARENA_W = 320 mientras su mapa mide
                # 640: peleaba en la mitad izquierda y una embestida podía
                # sacarlo del escenario, dejando el combate sin poder ganarse.
                enemy.set_arena_bounds(
                    pygame.Rect(0, 0, *self._stage_data.map_pixel_size),
                )
            if hasattr(enemy, "enemy_id"):
                self._bestiary.record_encounter(enemy.enemy_id)

        self._checkpoints = list(self._stage_data.checkpoints)
        for cp in self._checkpoints:
            cp.set_event_bus(self.context.event_bus)
        self._checkpoint_position = None
        self._stage_complete = False
        self._game_over = False
        self._pending_game_over = False
        self._was_grounded = False
        self.context.scene_manager.transition.start_fade_in(0.5)
        self._collision.reset()
        self._squad.reset()
        self._hazards.reset()
        # F4.1: el sistema se reconstruye por escenario. Reutilizar el anterior
        # arrastraría el llavero y las puertas ya abiertas al siguiente nivel.
        self._interactables = InteractableSystem(
            recogibles=self._stage_data.recogibles,
            cerraduras=self._stage_data.cerraduras,
            cofres=self._stage_data.cofres,
            disparadores=self._stage_data.disparadores,
            bus=self.context.event_bus,
        )
        self._progression.reset()

        if self._stage_data.bgm_track:
            audio = self.audio
            if audio is not None:
                bgm_path = settings.ASSETS_DIR / "music" / f"{self._stage_data.bgm_track}.wav"
                if not bgm_path.exists():
                    bgm_path = settings.ASSETS_DIR / "music" / f"{self._stage_data.bgm_track}.ogg"
                audio.play_music(bgm_path)
            if self._dynamic_music is not None:
                zone = self._stage_data.zone  # BUG-075 FIX: ya no usa getattr con default 0
                self._dynamic_music.set_zone(zone, self._stage_data.bgm_track)

        self._msg_box = MessageBox(self.context.event_bus)
        self._banner = ScreenBanner()
        if self._stage_data.stage_name:
            self._banner.play(self._stage_data.stage_id, self._stage_data.stage_name)
            self.context.event_bus.emit(Events.SFX_STAGE_BANNER)

        # AUD-072: `on_enter` se vuelve a llamar en cada reaparición, y cada
        # llamada creaba un HUD nuevo **sin destruir el anterior**. El viejo
        # seguía suscrito al bus hasta que el recolector se lo llevaba, momento
        # en el que el bus avisaba:
        #
        #   EventBus: dropping collected subscriber _on_stage_complete
        #
        # Es el aviso que aparecía en consola al jugar. No rompía nada —el bus
        # poda las suscripciones muertas— pero cada muerte del jugador dejaba un
        # HUD escuchando eventos y dibujando en ningún sitio.
        if self._hud is not None:
            self._hud.destroy()
        self._hud = HUD(self.context.event_bus)
        if self._stage_data.time_limit > 0:
            self._hud.start_timer(self._stage_data.time_limit)
        else:
            self._hud.start_timer()

        self.on_stage_start()

        # Init minimap with stage size
        self._minimap.set_map_size(*self._stage_data.map_pixel_size)

        # Speedrun timer
        self._speedrun.start()
        self._speedrun.start_stage(self._stage_data.stage_id)

        # Track stage start for achievement timing
        self._player_spawned = True
        self._damage_taken_this_stage = 0.0
        self._last_player_health = self._player.current_health
        self._stage_data.map_layer._map_layer.view_rect = pygame.Rect(
            self._camera.offset.x,
            self._camera.offset.y,
            settings.INTERNAL_WIDTH,
            settings.INTERNAL_HEIGHT,
        )
        self._stage_start_time = 0.0

        # Subscribe achievement system
        self._achievements.subscribe_events()

        self._particle_system.clear()
        self._damage_numbers.clear()
        self._tutorial.show("move", duration=6.0)
        self._ambient_particles.clear()
        self._trail_system.clear()
        self._enemy_trail_system.clear()
        self._enemy_prev_x.clear()
        self._weather.clear()
        self._setup_season()
        climate = self._clima_efectivo()
        self._weather.set_climate(climate)
        if climate:
            audio_key = self._weather.get_ambient_audio_key()
            if audio_key and self.context.audio is not None:
                ambient_path = settings.ASSETS_DIR / "sfx" / "ambient" / f"{audio_key}.wav"
                if ambient_path.exists():
                    self.context.audio.play_ambient(ambient_path, volume=0.3)

        self._setup_lighting()
        self._setup_post_processing()
        self._setup_ambient_particles()
        self._setup_day_night()
        self._vfx_handlers.clear()
        self._sfx_handlers.clear()
        try:
            self._subscribe_event_handlers()
        except Exception:
            self._unsubscribe_all_handlers()
            raise
        for sl in self._stage_lights:
            self._lighting.add_light(sl)

    #: Brillo ambiente por zona cuando el TMX no declara `ambient_light`.
    #:
    #: F1.1 — antes esto era una cadena `if/elif` que además creaba las luces
    #: con coordenadas fijas escritas en el motor. Un estudiante que
    #: construyera su escenario en Tiled heredaba las dos luces del zone 0, en
    #: (80, 80) y (240, 80), estuviera ahí su nivel o no. Ahora las luces se
    #: colocan en el mapa y esta tabla sólo decide **cuánta oscuridad** hay si
    #: nadie lo dijo.
    #:
    #: El zone 0 valía 1.0 —sin oscurecer—, así que todo el sistema de
    #: iluminación era invisible en el único escenario terminado del juego.
    AMBIENT_BY_ZONE: dict[int, float] = {
        0: 0.62,   # prólogo: exterior nublado, se ve todo pero la luz se nota
        1: 0.50,
        2: 0.32,
        3: 0.22,
    }
    AMBIENT_DEFAULT: float = 0.55

    def _setup_lighting(self) -> None:
        """Prepara la iluminación del escenario a partir del TMX.

        Orden de precedencia, del más específico al más general:

        1. `ambient_light` en las propiedades del mapa.
        2. `AMBIENT_BY_ZONE[zone]`.
        3. `AMBIENT_DEFAULT`.

        Los focos vienen siempre del mapa (objetos de tipo `Light` en la capa
        `Objects`). Si el mapa no declara ninguno, el escenario queda iluminado
        sólo por la luz que acompaña al jugador, que es un resultado legítimo
        y además una pista visual clara de que faltan focos.
        """
        self._lighting.clear()
        self._player_light = None

        # BUG-075: si el TMX no declara zona, cae al atributo ZONE de la escena.
        zone = self._stage_data.zone
        if zone is None:
            zone = getattr(self, "ZONE", 0)

        declarado = getattr(self._stage_data, "ambient_light", None)
        if declarado is not None:
            self._lighting.ambient_brightness = declarado
        else:
            self._lighting.ambient_brightness = self.AMBIENT_BY_ZONE.get(
                zone, self.AMBIENT_DEFAULT)

        self._stage_lights = [
            LightSource(
                position=pygame.Vector2(*spec.position),
                radius=spec.radius,
                color=spec.color,
                intensity=spec.intensity,
                flicker=spec.flicker,
                flicker_speed=spec.flicker_speed,
                flicker_amount=spec.flicker_amount,
            )
            for spec in getattr(self._stage_data, "lights", [])
        ]

    #: Bloom permanente por zona cuando el TMX no declara `bloom`.
    #:
    #: F1.2 — el bloom existía y sólo se encendía en ráfagas de 0,15 a 0,6 s al
    #: recoger un objeto o cambiar de fase el jefe. El resto del tiempo, cero.
    #: Un halo permanente y suave es lo que hace que la iluminación de F1.1 se
    #: lea como luz y no como manchas.
    BLOOM_BY_ZONE: dict[int, float] = {
        0: 0.18,   # prólogo: bruma tenue
        1: 0.22,
        2: 0.30,   # zonas de fuego: el halo hace el trabajo
        3: 0.35,
    }
    BLOOM_DEFAULT: float = 0.20

    #: Viñeta por zona. Sube al bajar la luz ambiente: cuanto más oscuro el
    #: nivel, más cerrado el encuadre.
    VIGNETTE_BY_ZONE: dict[int, float] = {0: 0.30, 1: 0.36, 2: 0.44, 3: 0.50}
    VIGNETTE_DEFAULT: float = 0.35

    def _setup_post_processing(self) -> None:
        """Fija bloom y viñeta del escenario a partir del TMX.

        Misma precedencia que la iluminación: propiedad del mapa, luego tabla
        por zona, luego valor por defecto. Así un estudiante puede escribir
        `bloom = 0.4` en Tiled y verlo, sin tocar una línea de Python.
        """
        zone = self._stage_data.zone
        if zone is None:
            zone = getattr(self, "ZONE", 0)

        bloom = getattr(self._stage_data, "bloom", None)
        if bloom is None:
            bloom = self.BLOOM_BY_ZONE.get(zone, self.BLOOM_DEFAULT)
        self._post_processing.set_base_bloom(bloom)

        vineta = getattr(self._stage_data, "vignette", None)
        if vineta is None:
            vineta = self.VIGNETTE_BY_ZONE.get(zone, self.VIGNETTE_DEFAULT)
        self._post_processing.set_vignette(vineta)

    #: Partículas de ambiente por zona: (tipo, partículas por segundo).
    #:
    #: F1.3 — `AmbientParticleSystem.set_effect` no la llamaba nadie, así que
    #: el ritmo se quedaba en cero toda la partida. Medido en Stage 0 tras tres
    #: segundos de juego: 0 partículas. El sistema existía, se actualizaba y se
    #: dibujaba; no tenía nada que dibujar.
    AMBIENT_FX_BY_ZONE: dict[int, tuple[str, float]] = {
        0: ("spores", 14.0),   # prólogo: bosque infestado
        1: ("leaves", 10.0),
        2: ("embers", 18.0),
        3: ("ash", 22.0),
    }
    AMBIENT_FX_DEFAULT: tuple[str, float] = ("dust", 8.0)

    def _setup_ambient_particles(self) -> None:
        """Enciende las partículas de ambiente del escenario.

        Misma precedencia que la luz y el post-procesado: propiedad del mapa
        (`ambient_fx`, `ambient_fx_rate`), luego tabla por zona, luego valor por
        defecto. Un `ambient_fx` de `none` en el TMX apaga el efecto de forma
        explícita, que es distinto de no declararlo.
        """
        zone = self._stage_data.zone
        if zone is None:
            zone = getattr(self, "ZONE", 0)

        tipo = getattr(self._stage_data, "ambient_fx", "")
        ritmo = getattr(self._stage_data, "ambient_fx_rate", None)
        if not tipo:
            # Precedencia: mapa > estación > zona. La estación va antes que la
            # zona porque es una decisión explícita del autor del mapa y la
            # tabla por zona es sólo un respaldo del motor.
            if getattr(self._stage_data, "season", ""):
                tipo, ritmo_estacion = self._estacion.particulas
            else:
                tipo, ritmo_estacion = self.AMBIENT_FX_BY_ZONE.get(
                    zone, self.AMBIENT_FX_DEFAULT)
            if ritmo is None:
                ritmo = ritmo_estacion
        elif ritmo is None:
            ritmo = self.AMBIENT_FX_DEFAULT[1]

        self._ambient_particles.set_effect(tipo, ritmo)

    def _clima_efectivo(self) -> str:
        """Qué clima usa el escenario: el del mapa, o el que sugiere la estación.

        F2.2 — el orden importa y por eso vive en un método propio. Un autor
        que escribe `climate = fog` en un mapa de otoño quiere niebla, no la
        lluvia que trae la estación. La estación **sugiere**; no manda.

        Está extraído en vez de en línea dentro de `on_enter` porque una regla
        de precedencia que sólo se puede probar recargando un TMX entero se
        acaba probando de mentira: la primera versión de su prueba
        reimplementaba la regla en el propio test y por tanto no podía fallar.
        """
        declarado = getattr(self._stage_data, "climate", "")
        return declarado or self._estacion.clima

    def _setup_season(self) -> None:
        """Resuelve la estación del escenario. Ver `framework.stage.seasons`."""
        from src.framework.stage.seasons import estacion

        self._estacion = estacion(getattr(self._stage_data, "season", ""))

    def _setup_day_night(self) -> None:
        """Arranca el reloj del escenario a partir del TMX.

        F2.1: sin `day_length` el reloj queda congelado en su hora inicial y el
        escenario se comporta exactamente como antes de esta fase. Es
        deliberado: un prólogo de tres minutos no gana nada con un ciclo, y
        obligar a todos los mapas a tener uno sería imponer una decisión de
        diseño desde el motor.
        """
        from src.framework.stage.day_night import RelojDeMundo

        hora = getattr(self._stage_data, "start_hour", None)
        if hora is None:
            hora = self.HORA_POR_DEFECTO
        self._reloj = RelojDeMundo(
            hora_inicial=hora,
            duracion_dia=getattr(self._stage_data, "day_length", 0.0) or 0.0,
        )
        # Se guardan los valores base del escenario porque el ciclo los
        # **modula**: si se sobrescribieran, cada fotograma partiría del
        # resultado del anterior y la luz se iría a cero en unos segundos.
        self._ambiente_base = self._lighting.ambient_brightness
        self._bloom_base_escenario = self._post_processing._bloom_base
        self._aplicar_hora()

    #: Hora que se usa cuando el mapa no declara `start_hour`. Mediodía, es
    #: decir, el factor de ambiente 1.0: un escenario que no pide ciclo se ve
    #: exactamente con el `ambient_light` que escribió su autor.
    HORA_POR_DEFECTO = 12.0

    #: Suelo de luz ambiente aplicada. Por debajo de esto el nivel deja de ser
    #: jugable.
    #:
    #: F2.1: el ciclo **multiplica** el ambiente del escenario, así que los dos
    #: factores se componen. Medido en Stage 0, que declara `ambient_light`
    #: 0,70: a medianoche el factor 0,35 daba un ambiente aplicado de 0,245 y
    #: un brillo de pantalla de 12,7 sobre 255. El jugador no ve los enemigos.
    #: Una noche realista que impide jugar es un defecto, no una decisión
    #: artística: la hora se comunica con el color, que sí cambia por completo.
    MIN_AMBIENTE = 0.45

    def _aplicar_hora(self) -> None:
        """Traduce la hora actual, y la estación, a luz ambiente y bloom."""
        from src.framework.stage.seasons import aplicar_tinte

        luz = self._reloj.luz()
        self._lighting.ambient_brightness = max(
            self.MIN_AMBIENTE,
            self._ambiente_base * luz.factor_ambiente * self._estacion.factor_luz,
        )
        self._post_processing.set_base_bloom(
            self._bloom_base_escenario + luz.bloom_extra)
        # El tinte de la hora se aplica como color de la luz ambiente, y la
        # estación lo modula. Los dos son multiplicadores, así que se componen
        # sin que ninguno tenga que conocer al otro: a mediodía en verano el
        # resultado es casi blanco, y de madrugada en invierno, azul doble.
        self._lighting.ambient_color = aplicar_tinte(luz.color, self._estacion)

    def _subscribe_event_handlers(self) -> None:
        def _on_enemy_died(**data: Any) -> None:
            pos = data.get("position", (0, 0))
            self._particle_system.get_emitter("death").emit(
                float(pos[0]), float(pos[1]), HitEffects.DEATH,
            )

        def _on_hit_connect(**data: Any) -> None:
            pos = data.get("pos", [0, 0])
            dmg = data.get("damage", 1.0)
            self._particle_system.get_emitter("hits").emit(
                pos[0], pos[1], HitEffects.get_for_damage(dmg),
            )
            self._damage_numbers.add(pos[0], pos[1], str(int(dmg)))

        def _on_enemy_hit(**data: Any) -> None:
            pos = data.get("pos", [0, 0])
            dmg = data.get("damage", 1.0)
            self._particle_system.get_emitter("blood").emit(
                pos[0], pos[1], HitEffects.get_blood_for_damage(dmg),
            )
            self._camera.apply_shake(amplitude=1.5, duration=0.06)

        def _on_player_damaged(**data: Any) -> None:
            src = data.get("source", (0, 0))
            self._particle_system.get_emitter("blood").emit(
                float(src[0]), float(src[1]), HitEffects.BLOOD_BIG,
            )
            self._camera.apply_shake(amplitude=2.0, duration=0.1)
            self._post_processing.flash((255, 50, 50), alpha=180, duration=0.15)
            health_pct = self._player.current_health / max(settings.PLAYER_MAX_HEALTH, 1)
            self._post_processing.set_damage_vignette(max(0, 0.5 - health_pct * 0.5))

        def _on_vfx_parry(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("parry").emit(
                float(pos[0]), float(pos[1]), HitEffects.PARRY,
            )
            self._camera.apply_shake(amplitude=3.0, duration=0.15)
            self._post_processing.flash((100, 200, 255), alpha=120, duration=0.1)
            self._post_processing.set_bloom(0.3, duration=0.15)

        def _on_vfx_charge(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("charge").emit(
                float(pos[0]), float(pos[1]), HitEffects.CHARGE_GLOW,
            )

        def _on_vfx_slam(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("slam").emit(
                float(pos[0]), float(pos[1]), HitEffects.SPARK_BIG,
            )
            self._camera.apply_shake(amplitude=4.0, duration=0.2)

        def _on_vfx_ultimate(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("parry").emit(
                float(pos[0]), float(pos[1]), HitEffects.SPARK_BIG,
            )
            self._post_processing.set_bloom(0.8, duration=0.6)
            self._post_processing.flash((255, 255, 255), alpha=255, duration=0.15)
            self._camera.apply_shake(amplitude=5.0, duration=0.4)

        self.context.event_bus.subscribe(Events.SFX_HIT_CONNECT, _on_hit_connect)
        self._vfx_handlers[Events.SFX_HIT_CONNECT] = _on_hit_connect
        self.context.event_bus.subscribe(Events.SFX_ENEMY_HIT, _on_enemy_hit)
        self._vfx_handlers[Events.SFX_ENEMY_HIT] = _on_enemy_hit
        self.context.event_bus.subscribe(Events.ENEMY_DIED, _on_enemy_died)
        self._vfx_handlers[Events.ENEMY_DIED] = _on_enemy_died

        def _on_player_died(**data: Any) -> None:
            pos = data.get("pos", [0, 0])
            self._particle_system.get_emitter("death").emit(
                float(pos[0]), float(pos[1]), HitEffects.get_blood_for_damage(10),
            )
            for _ in range(3):
                self._particle_system.get_emitter("death").emit(
                    float(pos[0]) + random.uniform(-8, 8),
                    float(pos[1]) + random.uniform(-8, 8),
                    HitEffects.get_blood_for_damage(5),
                )
            self._camera.apply_shake(amplitude=8.0, duration=0.5)
            self._post_processing.flash((255, 0, 0), alpha=180, duration=0.3)

        self.context.event_bus.subscribe(Events.PLAYER_DAMAGED, _on_player_damaged)
        self._vfx_handlers[Events.PLAYER_DAMAGED] = _on_player_damaged
        self.context.event_bus.subscribe(Events.PLAYER_DIED, _on_player_died)
        self._vfx_handlers[Events.PLAYER_DIED] = _on_player_died
        self.context.event_bus.subscribe(Events.VFX_PARRY, _on_vfx_parry)
        self._vfx_handlers[Events.VFX_PARRY] = _on_vfx_parry
        self.context.event_bus.subscribe(Events.VFX_CHARGE, _on_vfx_charge)
        self._vfx_handlers[Events.VFX_CHARGE] = _on_vfx_charge
        self.context.event_bus.subscribe(Events.VFX_SLAM, _on_vfx_slam)
        self._vfx_handlers[Events.VFX_SLAM] = _on_vfx_slam
        self.context.event_bus.subscribe(Events.VFX_ULTIMATE, _on_vfx_ultimate)
        self._vfx_handlers[Events.VFX_ULTIMATE] = _on_vfx_ultimate

        def _on_vfx_bubble(**data: Any) -> None:
            pos = data.get("pos", (0, 0))
            self._particle_system.get_emitter("bubble").emit(
                float(pos[0]), float(pos[1]), HitEffects.BUBBLE,
            )
        self.context.event_bus.subscribe(Events.VFX_BUBBLE, _on_vfx_bubble)
        self._vfx_handlers[Events.VFX_BUBBLE] = _on_vfx_bubble

        def _on_music_stinger(**data: Any) -> None:
            name = data.get("name", "stinger_boss_phase")
            vol = data.get("volume", 0.8)
            # BUG-057: Null guard for audio
            if self.audio is not None:
                self.audio.play_stinger(name, volume=vol)
        self.context.event_bus.subscribe(Events.MUSIC_STINGER, _on_music_stinger)
        self._vfx_handlers[Events.MUSIC_STINGER] = _on_music_stinger

        sfx_map = {
            Events.SFX_PLAYER_JUMP: "sfx_player_jump",
            Events.SFX_PLAYER_LAND: "sfx_player_land",
            Events.SFX_PLAYER_SHORT_ATTACK: "sfx_player_short_attack",
            Events.SFX_PLAYER_LONG_ATTACK: "sfx_player_long_attack",
            Events.SFX_PLAYER_HURT: "sfx_player_hurt",
            Events.SFX_PLAYER_DIE: "sfx_player_die",
            Events.SFX_HIT_CONNECT: "sfx_player_hit_connect",
            Events.SFX_ENEMY_HIT: "sfx_enemies_hit",
            Events.SFX_ENEMY_DIE_SMALL: "sfx_enemies_die_small",
            Events.SFX_ENEMY_DIE_LARGE: "sfx_enemies_die_large",
            Events.SFX_PROJECTILE_FIRE: "sfx_enemies_projectile_fire",
            Events.SFX_CHECKPOINT: "sfx_ui_checkpoint",
            Events.SFX_STAGE_BANNER: "sfx_ui_stage_banner",
            Events.SFX_STAGE_COMPLETE: "sfx_ui_stage_complete",
            Events.SFX_HAZARD_ZONE: "sfx_environment_hazard_zone",
            Events.SFX_PLAYER_FOOTSTEP: "sfx_step",
            Events.SFX_MENU_HOVER: "sfx_select",
            Events.SFX_MENU_CONFIRM: "sfx_select",
            Events.SFX_MENU_CANCEL: "sfx_ui_menu_cancel",
            Events.SFX_PLAYER_PARRY: "sfx_parry",
            Events.SFX_PLAYER_CROUCH: "sfx_player_crouch",
            Events.SFX_PLAYER_HEAL: "sfx_ui_heart_restore",
            Events.SFX_BOSS_HIT: "sfx_boss_hit",
            Events.SFX_UI_GAME_OVER: "sfx_ui_game_over",
            Events.SFX_ENVIRONMENT_SCREEN_SHAKE: "sfx_environment_screen_shake",
            Events.SFX_ENVIRONMENT_ONE_WAY_PLATFORM: "sfx_environment_one_way_platform",
            Events.SFX_BOSS_PHASE_CHANGE: "sfx_bosses_phase_change",
            Events.SFX_ENEMIES_PROJECTILE_HIT_WALL: "sfx_enemies_projectile_hit_wall",
            Events.SFX_BOSSES_GAVILAN_DIVE: "sfx_bosses_gavilan_dive",
            Events.SFX_BOSSES_GAVILAN_MASK_BEAM: "sfx_bosses_gavilan_mask_beam",
            Events.SFX_BOSSES_PABURU_EYE_BEAM: "sfx_bosses_paburu_eye_beam",
            Events.SFX_BOSSES_PABURU_WAVE: "sfx_bosses_paburu_wave",
            Events.SFX_BOSSES_RELIC_APPEAR: "sfx_bosses_relic_appear",
            Events.SFX_BOSSES_REY_SPIT: "sfx_bosses_rey_spit",
            Events.SFX_BOSSES_REY_SPLIT: "sfx_bosses_rey_split",
            Events.SFX_BOSSES_VENADO_CHARGE: "sfx_bosses_venado_charge",
            Events.SFX_BOSSES_VENADO_STOMP: "sfx_bosses_venado_stomp",
            Events.SFX_BOSSES_VENADO_VINE: "sfx_bosses_venado_vine",
        }
        for evt, sname in sfx_map.items():
            handler = self._make_sfx_handler(sname)
            self.context.event_bus.subscribe(evt, handler)
            # Retained here so the bus's weak reference stays alive.
            self._sfx_handlers[evt] = handler

        # SAVE_REQUESTED handler — persists game on checkpoint / save & quit
        def _on_save_requested(**data: Any) -> None:
            sm = self.context.save_manager
            if sm is not None:
                sm.auto_save(
                    stage_id=data.get("stage_id", ""),
                    stage_index=data.get("stage_index", 0),
                    checkpoint_x=data.get("checkpoint_x", 0),
                    checkpoint_y=data.get("checkpoint_y", 0),
                    health=data.get("health", 100),
                    max_health=data.get("max_health", 100),
                )
        self.context.event_bus.subscribe(Events.SAVE_REQUESTED, _on_save_requested)
        self._vfx_handlers[Events.SAVE_REQUESTED] = _on_save_requested

    def _make_sfx_handler(self, sound_name: str) -> Callable[..., None]:
        """Build an event handler that plays ``sound_name``.

        AUD-032: this was previously a closure factory defined *inside* the loop
        that used it, with the inner function and the loop variable sharing the
        name ``handler``. It worked, but it tripped B023 and required a careful
        read to see that it did — the exact shape that hides a real late-binding
        bug the next time someone edits it. A named method takes the sound as a
        parameter, so the binding is explicit and unmistakable.
        """
        def handler(**data: Any) -> None:
            volume = 1.0
            if "damage" in data:
                # Slight random variation so repeated hits do not sound robotic.
                volume = 0.8 + random.random() * 0.4
            pos = data.get("pos")
            if pos is not None:
                self._play_sfx_spatial(sound_name, pos[0], volume=volume)
            else:
                self._play_sfx_named(sound_name, volume=volume)
        return handler

    def _unsubscribe_all_handlers(self) -> None:
        for evt, handler in self._sfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._sfx_handlers.clear()
        for evt, handler in self._vfx_handlers.items():
            self.context.event_bus.unsubscribe(evt, handler)
        self._vfx_handlers.clear()

    def _play_sfx_named(self, name: str, volume: float = 1.0) -> None:
        audio = self.audio
        if audio is not None:
            audio.play_sfx(name, volume=volume)

    def _play_sfx_spatial(self, name: str, world_x: float, volume: float = 1.0) -> None:
        audio = self.audio
        if audio is not None:
            screen_center_x = self._camera.offset.x + settings.INTERNAL_WIDTH / 2
            audio.play_sfx_at(name, world_x, screen_center_x, volume=volume)

    def on_exit(self) -> None:
        if self.context.clock is not None:
            self.context.clock.time_scale = 1.0
        self._unsubscribe_all_handlers()
        if self._hud is not None:
            self._hud.destroy()
            self._hud = None
        if self._msg_box is not None:
            self._msg_box.destroy()
            self._msg_box = None
        self._dialogue.end_dialogue()
        audio = self.audio
        if audio is not None:
            audio.stop_music()
        self._subtitles.destroy()
        self._achievements.save()
        self._achievements.unsubscribe_events()
        # AUD-025: release our scope rather than wiping the shared cache. The
        # cache is only actually dropped once no scene is using it.
        AssetLoader.leave_scope()
        self._stage_data = None
        self._player = None

    def respawn(self) -> None:
        if self.context.clock is not None:
            self.context.clock.time_scale = 1.0
        self._game_over = False
        saved_time = self._hud.current_time if self._hud is not None else 0.0
        saved_time_limit = self._hud.time_limit if self._hud is not None else 0
        cp = self._checkpoint_position
        if self._hud is not None:
            self._hud.destroy()
            self._hud = None
        if self._msg_box is not None:
            self._msg_box.destroy()
            self._msg_box = None
        self._unsubscribe_all_handlers()
        # The achievement subscriptions are re-armed by on_enter(); drop them
        # first so respawning does not accumulate duplicate registrations.
        self._achievements.unsubscribe_events()
        # respawn() re-runs on_enter(), which claims another cache scope. Release
        # ours first so the reference count stays balanced across deaths
        # (otherwise the count only ever grows and the cache is never freed).
        AssetLoader.leave_scope()
        self.on_enter()
        if self._hud is None:
            raise RuntimeError("respawn: HUD not initialized by on_enter")
        self._hud.current_time = saved_time
        self._hud.is_countdown = saved_time_limit > 0
        if cp is not None:
            self._player.position = pygame.Vector2(cp)
            self._player.rect.center = (int(cp.x), int(cp.y))
        self._player._invincibility_timer = 2.0
        self._post_processing.flash((255, 255, 255), alpha=255, duration=0.3)
        self.context.scene_manager.transition.start_fade_in(0.5)

    # ── Subsystem update dispatch ──────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._stage_data is None or self._player is None:
            return
        self._dt = dt
        self._handle_input()
        if self._paused:
            self._handle_pause_input()
            return
        self._check_player_death()
        if not self._game_over:
            self._update_gameplay(dt)
        if not self._game_over:
            self._update_camera_map(dt)
        if not self._game_over and not self._progression.stage_complete:
            self._update_audio(dt)
            self._update_hud_ui(dt)
            self._update_vfx(dt)
            self._update_lighting(dt)
            self._update_tracking(dt)
            self._update_timers(dt)
            self._update_minimap()
            self._update_trail(dt)
        if self._hud and self._hud.current_time <= 0 and self._hud.is_countdown and not self._game_over:
            self._kill_player()

    def _handle_input(self) -> None:
        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.PAUSE):
            self._paused = not self._paused
            self._pause_selected = 0
            # AUD-022: HUD.pause_timer / resume_timer existed and were never
            # called, so on a timed stage the countdown kept draining while the
            # player sat in the pause menu — pausing cost you the run. Music
            # likewise kept playing over the pause screen.
            self._set_paused_side_effects(self._paused)
        if im.is_action_just_pressed(Action.TOGGLE_MUTE):
            audio = self.audio
            if audio is not None:
                audio.toggle_mute()
                self._subtitles.push(
                    "[Audio muted]" if audio.is_muted else "[Audio unmuted]",
                )
        if im.is_action_just_pressed(Action.OPEN_BESTIARY):
            from src.engine.scenes.bestiary_scene import BestiaryScene
            self.context.scene_manager.push(BestiaryScene(self.context))
        if im.is_raw_key_pressed(pygame.K_F1):
            self._debug = not self._debug
            self.on_debug_toggle(self._debug)
        for learn_action in (Action.LEARN_MATH, Action.LEARN_PHYSICS,
                             Action.LEARN_COLLISION, Action.LEARN_FSM,
                             Action.LEARN_RENDER, Action.LEARN_AUDIO,
                             Action.LEARN_PERF, Action.LEARN_CONTROLS,
                             Action.LEARN_HELP):
            if im.is_action_just_pressed(learn_action):
                self._learning.toggle(learn_action)
                break

    def _set_paused_side_effects(self, paused: bool) -> None:
        """Suspend or resume everything that must not advance during a pause."""
        if self._hud is not None:
            if paused:
                self._hud.pause_timer()
            else:
                self._hud.resume_timer()
        audio = self.audio
        if audio is not None:
            if paused:
                audio.pause_music()
            else:
                audio.resume_music()

    def _handle_pause_input(self) -> None:
        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._pause_selected = (self._pause_selected + 1) % len(self._pause_options)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._pause_selected = (self._pause_selected - 1) % len(self._pause_options)
        if im.is_action_just_pressed(Action.CANCEL):
            self._paused = False
            self._set_paused_side_effects(False)
        if im.is_action_just_pressed(Action.CONFIRM):
            choice = self._pause_options[self._pause_selected]
            if choice == "Resume":
                self._paused = False
            elif choice == "Save & Quit":
                self._save_and_quit()
            elif choice == "Quit to Title":
                self._quit_to_title()

    def _check_player_death(self) -> None:
        if self._player.current_health <= 0 and not self._game_over:
            self._kill_player()

    def _update_gameplay(self, dt: float) -> None:
        player = self._player
        stage = self._stage_data
        im = self.input
        clock = self.context.clock
        # Hit-stop must be driven by REAL elapsed time. Driving it with the
        # scaled `dt` is self-referential — time_scale goes to 0, dt goes to
        # 0, and the countdown can never drain, freezing the game forever on
        # the first landed hit (AUD-001). Fall back to dt only when the
        # context has no clock (headless tests).
        unscaled_dt = getattr(clock, "unscaled_dt", dt) if clock is not None else dt
        try:
            # F4.1 — una puerta cerrada bloquea el paso; al abrirse deja de
            # hacerlo. Se suma aquí en vez de mutar `stage.collision_rects`,
            # que es la lista que construye el cargador y leen varios sistemas:
            # cambiarla para simular un estado es el atajo que después nadie
            # sabe deshacer.
            cerradas = self._interactables.rects_solidos()
            solidos = stage.collision_rects + cerradas if cerradas else stage.collision_rects
            player.update(dt, solidos, im, one_way_rects=stage.one_way_rects)
            self._interactables.update(
                dt, player.rect,
                usar=bool(im and im.is_action_just_pressed(Action.GRAB)),
            )
            self._actualizar_arco(dt, player, im, stage)
            if player.combo_active and player.combo_count > 0:
                self._achievements.mark_air_assault(getattr(player, "_combo_air_hits", 0))
                self._achievements.mark_combo_king(player.combo_count)
            if player.is_grounded and not self._was_grounded:
                self.on_player_landed()
            self._was_grounded = player.is_grounded
            enemies: list[EnemyBase] = []
            for entity in stage.entity_list:
                if not isinstance(entity, EnemyBase):
                    continue
                if entity.is_alive:
                    enemies.append(entity)
                elif getattr(entity, "_was_alive", True):
                    entity._was_alive = False
                    self._squad.forget(entity)
                    self.on_enemy_died(entity)

            # AUD-053: los jefes crean esbirros pero no conocen la escena —
            # que una entidad se inserte a sí misma en el mundo invierte la
            # dirección de dependencia. La escena los recoge aquí.
            for entity in enemies:
                if isinstance(entity, BossBase):
                    for minion in entity.take_summons():
                        minion.set_event_bus(self.context.event_bus)
                        if self._player is not None:
                            minion.set_player_ref(self._player.rect)
                        if hasattr(minion, "set_collision_rects"):
                            minion.set_collision_rects(
                                stage.collision_rects,
                                one_way=stage.one_way_rects,
                            )
                        stage.entity_list.append(minion)

            # Táctica de escuadra: barata de consultar, cara de recalcular, así
            # que se recalcula a baja cadencia y los enemigos sólo leen.
            self._squad.update(dt, player, enemies)
            for enemy in enemies:
                enemy.tactic = self._squad.decision_for(enemy).action

            # AUD-060: **esto faltaba y ningún enemigo del juego se movía.**
            #
            # La llamada vivía en `CollisionSystem.update_enemies`. Al reescribir
            # el sistema de colisiones durante la auditoría la convertí en un
            # no-op, con un docstring que afirmaba «el movimiento lo integra
            # EnemyBase.update, aquí no hay nada que sincronizar». La primera
            # mitad era cierta; la segunda no, porque **nadie más llamaba a
            # `EnemyBase.update`**. Razoné sobre lo que el método debía hacer en
            # lugar de comprobar quién dependía de él.
            #
            # El efecto: todos los enemigos y el jefe quedaron inmóviles e
            # invulnerables —sus fotogramas de invencibilidad tampoco corrían—,
            # y nada lo detectó porque cada subsistema se probaba aislado y las
            # pruebas de humo sólo exigían que la escena no lanzara excepciones.
            #
            # Vive aquí, y no en el sistema de colisiones, porque decidir a
            # quién se actualiza cada fotograma es responsabilidad de la escena;
            # el sistema de colisiones debería tratar sólo de colisiones.
            for enemy in enemies:
                enemy.set_player_ref(player.rect)
                # El contacto se comprueba ANTES de actualizar, como hacía el
                # bucle original. El orden importa: `_check_player_contact`
                # resuelve el daño con las posiciones del fotograma que el
                # jugador acaba de ver, no con las del siguiente.
                #
                # AUD-062: esta llamada también se perdió con `update_enemies`,
                # y su ausencia era aún menos visible que la de `update`. No
                # sólo se apagaba el daño por contacto: `_check_player_contact`
                # es donde cada subclase resuelve **sus proyectiles** — las
                # flechas del Archer, las bolas del Caster, las lianas y
                # esporas del Venado, su pisotón y su barrido. El jefe entero
                # era inofensivo: podías quedarte quieto delante de él
                # indefinidamente.
                enemy._check_player_contact(player)
                enemy.update(dt)
            self._collision.process_attack(dt, player, stage, self._camera, clock)
        finally:
            # update_hitstop owns time_scale entirely: it restores 1.0 as soon
            # as the freeze expires, so no separate restore step is needed.
            self._collision.update_hitstop(unscaled_dt, clock)

    def _update_camera_map(self, dt: float) -> None:
        stage = self._stage_data
        self._camera.update(dt)
        if stage.map_layer is not None and hasattr(stage.map_layer, '_map_layer'):
            stage.map_layer._map_layer.view_rect = pygame.Rect(
                self._camera.offset.x, self._camera.offset.y,
                settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT,
            )
        self._camera.set_camera_locks(stage.camera_locks)
        cp_pos = self._progression.process_checkpoints(self._player, stage, self._checkpoints, self._hud)
        if cp_pos is not None:
            self._checkpoint_position = cp_pos
        if self._progression.check_next_trigger(self._player, stage):
            self.on_next_trigger_entered()
            self._banner.play("STAGE_COMPLETE", "STAGE COMPLETE")
            self.context.event_bus.emit(Events.SFX_STAGE_COMPLETE)
        elif self._progression.check_boss_defeat(stage):
            self._banner.play("STAGE_COMPLETE", "STAGE COMPLETE")
            self.context.event_bus.emit(Events.SFX_STAGE_COMPLETE)
        if self._progression.update_complete_timer(dt):
            if self._damage_taken_this_stage <= 0.001:
                self._achievements.mark_untouchable()
            if self._stage_start_time < 60.0:
                self._achievements.mark_speed_demon()
            self._speedrun.split(stage.stage_id)
            self._speedrun.stop()
            # AUD-022: the speedrun timer ran the whole stage and then threw the
            # result away — get_formatted_time() and get_splits() had no callers,
            # so the player never saw their time. Surface it on completion.
            if self._banner is not None:
                self._banner.play(
                    "STAGE_COMPLETE",
                    f"CLEAR  {self._speedrun.get_formatted_time()}",
                )
            self.context.event_bus.emit(Events.STAGE_COMPLETE, stage_id=stage.stage_id)

    def _update_audio(self, dt: float) -> None:
        if self._dynamic_music is None:
            return
        stage = self._stage_data
        has_boss = any(isinstance(e, BossBase) and e.is_alive for e in stage.entity_list)
        has_enemies = any(isinstance(e, EnemyBase) and e.is_alive for e in stage.entity_list)
        intensity = self._dynamic_music.detect_intensity_from_state(has_boss, has_enemies)
        self._dynamic_music.set_intensity(intensity)

    def _update_hud_ui(self, dt: float) -> None:
        stage = self._stage_data
        im = self.input
        if self._hud:
            boss_found = False
            for entity in stage.entity_list:
                if isinstance(entity, BossBase) and entity.is_alive:
                    self._hud.set_boss_hud(
                        entity.boss_name, entity.current_health,
                        entity.phase_max_health,
                        getattr(entity, "current_phase", 0) + 1,
                        getattr(entity, "phase_count", 1),
                    )
                    boss_found = True
                    break
            if not boss_found:
                self._hud.clear_boss_hud()
            self._hud.set_combo_count(self._player.combo_count)
            self._hud.set_special_meter(self._player.special_meter, self._player.special_meter_max)
            self._hud.update(dt)
        self._subtitles.update(dt)
        if self._msg_box:
            self._msg_box.update(dt)
            if self._msg_box.is_dismiss_on_confirm and im.is_action_just_pressed(Action.CONFIRM):
                self._msg_box.hide()
        if self._banner:
            self._banner.update(dt)

    def _update_vfx(self, dt: float) -> None:
        self._speedrun.update(dt)
        self._hazards.update(dt, self._player, self._stage_data)
        self._tutorial.update(dt, self.input)
        self._particle_system.update(dt)
        self._damage_numbers.update(dt)
        self._post_processing.update(dt)
        self._ambient_particles.update(dt, self._camera.offset)
        if not self._reloj.congelado:
            self._reloj.update(dt)
            self._aplicar_hora()
        self._weather.update(dt, self._camera.offset)
        self._dialogue.update(dt)

    def _update_lighting(self, dt: float) -> None:
        stage = self._stage_data
        if self._player is None:
            return
        combat = any(isinstance(e, EnemyBase) and e.is_alive for e in stage.entity_list)
        if self._player_light is None:
            self._player_light = self._lighting.get_player_light(self._player.position, combat)
            self._lighting.add_light(self._player_light)
        else:
            self._player_light.position = self._player.position
            self._player_light.intensity = 0.9 if combat else 0.6
            self._player_light.radius = 100 if combat else 60
        self._lighting.update(dt, self._camera.offset)

    def _update_tracking(self, dt: float) -> None:
        self._achievements.update_notifications(dt)
        get_inventory().update_notifications(dt)
        if not self._player_spawned or self._player is None:
            return
        self._stage_start_time += dt
        old_health = self._last_player_health
        if old_health > self._player.current_health:
            self._damage_taken_this_stage += old_health - self._player.current_health
        self._last_player_health = self._player.current_health
        if self._player.current_health <= 0.5 and self._player.current_health > 0:
            self._achievements.mark_survived_low_health()

    def _update_timers(self, dt: float) -> None:
        if self._progression.stage_complete:
            if self._hud:
                self._hud.clear_boss_hud()
            if self._msg_box:
                self._msg_box.update(dt)
            if self._banner:
                self._banner.update(dt)

    def _update_minimap(self) -> None:
        if self._player is None or self._stage_data is None:
            return
        stage = self._stage_data
        enemy_positions = [
            (e.position.x, e.position.y)
            for e in stage.entity_list
            if isinstance(e, EnemyBase) and e.is_alive
        ]
        boss_positions = [
            (e.position.x, e.position.y)
            for e in stage.entity_list
            if isinstance(e, BossBase) and e.is_alive
        ]
        cp_positions = [(cp.rect.centerx, cp.rect.centery) for cp in self._checkpoints]
        activated = {i for i, cp in enumerate(self._checkpoints) if cp.is_activated}
        self._minimap.update(
            player_pos=(self._player.position.x, self._player.position.y),
            player_dir=self._player.facing_direction,
            enemy_positions=enemy_positions,
            boss_positions=boss_positions,
            checkpoint_positions=cp_positions,
            activated_checkpoints=activated,
        )
        explore_rect = pygame.Rect(
            self._player.rect.centerx - 80, self._player.rect.centery - 60, 160, 120,
        )
        self._minimap.explore_rect(explore_rect)

    #: Velocidad, en px/s, a partir de la cual un enemigo deja estela.
    #:
    #: F1.4: el sistema de estelas sólo lo usaba el jugador, así que la
    #: embestida de un jefe —el movimiento más rápido y más peligroso del
    #: juego— no dejaba rastro. La estela no es decoración en ese caso: es la
    #: información que permite leer de dónde viene el ataque.
    ENEMY_TRAIL_SPEED = 180.0

    def _update_trail(self, dt: float) -> None:
        if self._player is not None:
            is_dashing = getattr(self._player, "_dash_timer", 0) > 0
            is_moving = abs(self._player.velocity.x) > 50
            if is_dashing or (is_moving and not self._player.is_grounded):
                self._trail_system.capture(self._player)
        self._trail_system.update(dt)

        self._capture_enemy_trails(dt)
        self._enemy_trail_system.update(dt)

    def _capture_enemy_trails(self, dt: float) -> None:
        """Estela para los enemigos que se mueven rápido, jefes incluidos.

        Se usa un `TrailSystem` aparte del jugador a propósito: los dos
        comparten un único temporizador de intervalo, así que meterlos en el
        mismo sistema haría que el jugador y el jefe se robaran capturas y
        ninguno de los dos dejara una estela continua.

        La velocidad se deduce del desplazamiento entre fotogramas porque los
        enemigos **no tienen atributo `velocity`**: a diferencia del jugador,
        mueven `position` directamente. El primer intento comprobaba
        `entity.velocity` y por tanto nunca capturaba nada, lo que habría
        pasado por una característica que "no se nota".
        """
        if self._stage_data is None or dt <= 0:
            return
        mas_rapido = None
        mejor_velocidad = self.ENEMY_TRAIL_SPEED
        for entity in self._stage_data.entity_list:
            if entity.rect is None or not getattr(entity, "visible", True):
                continue
            anterior = self._enemy_prev_x.get(id(entity))
            self._enemy_prev_x[id(entity)] = entity.position.x
            if anterior is None:
                continue
            velocidad = abs(entity.position.x - anterior) / dt
            if velocidad > mejor_velocidad:
                mejor_velocidad = velocidad
                mas_rapido = entity

        if mas_rapido is None:
            return
        # Rojo tenue: se distingue del azul del jugador de un vistazo, que es
        # lo que hace falta cuando las dos estelas se cruzan.
        self._enemy_trail_system.capture_at(
            mas_rapido.position.x, mas_rapido.position.y,
            (mas_rapido.rect.width, mas_rapido.rect.height),
            (255, 90, 70, 110),
        )

    def _save_and_quit(self) -> None:
        if self._stage_data is not None and self._player is not None:
            self.context.event_bus.emit(
                Events.SAVE_REQUESTED,
                stage_id=self._stage_data.stage_id,
                stage_index=self.context.scene_manager.stage_index,
                checkpoint_x=self._player.rect.centerx,
                checkpoint_y=self._player.rect.centery,
                health=self._player.current_health,
                max_health=settings.PLAYER_MAX_HEALTH,
            )
        self._quit_to_title()

    def _quit_to_title(self) -> None:
        from src.engine.scenes.title_scene import TitleScene
        self.context.scene_manager.replace(TitleScene(self.context))

    def _kill_player(self) -> None:
        self._game_over = True
        self.context.event_bus.emit(Events.PLAYER_DIED)
        # AUD-064: la pantalla de game over aparecía en silencio.
        self.context.event_bus.emit(Events.SFX_UI_GAME_OVER)
        from src.engine.scenes.game_over_scene import GameOverScene
        self.context.scene_manager.push(GameOverScene(self.context, self))

    def draw(self, surface: pygame.Surface) -> None:
        if self._stage_data is None or self._player is None:
            return
        from src.framework.stage.drawing_system import DrawContext
        ctx = DrawContext(
            surface=surface,
            stage=self._stage_data,
            player=self._player,
            checkpoints=self._checkpoints,
            camera=self._camera,
            hud=self._hud,
            msg_box=self._msg_box,
            banner=self._banner,
            paused=self._paused,
            debug=self._debug,
            pause_selected=self._pause_selected,
            pause_options=self._pause_options,
            particle_system=self._particle_system,
            damage_numbers=self._damage_numbers,
            ambient_particles=self._ambient_particles,
            weather_system=self._weather,
            trail_system=self._trail_system,
            enemy_trail_system=self._enemy_trail_system,
            interactables=self._interactables,
            tutorial_overlay=self._tutorial,
            learning_overlay=self._learning,
            dialogue_system=self._dialogue,
        )
        self._drawing.draw(ctx)
        self._lighting.render(surface, self._camera.offset)
        self._post_processing.apply(surface)
        # AUD-090: la interfaz va DESPUÉS de la luz y del post-procesado. Antes
        # se pintaba dentro de `_drawing.draw` y el ambiente la multiplicaba:
        # medido, el HUD perdía el 58 % de su brillo y el indicador de combo
        # desaparecía por completo.
        self._drawing.draw_ui(ctx)
        self._minimap.draw(surface)
        # Captions render after post-processing so the colourblind filter does
        # not wash out text that exists precisely for accessibility (AUD-036).
        self._subtitles.draw(surface)
        self._achievements.draw_notifications(surface)
        get_inventory().draw_notifications(surface)
