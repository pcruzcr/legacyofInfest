from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import plugins, settings
from src.engine.core.achievements import AchievementSystem
from src.engine.core.events import Events
from src.engine.core.experience import ExperienceSystem
from src.engine.core.inventory import get_inventory
from src.engine.core.score_system import ScoreSystem
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.hud import HUD
from src.engine.ui.message_box import MessageBox
from src.engine.ui.minimap import Minimap
from src.engine.ui.screen_banner import ScreenBanner
from src.engine.ui.subtitle_overlay import SubtitleOverlay
from src.engine.utils.asset_loader import AssetLoader
from src.framework.audio.dynamic_music import DynamicMusicSystem, resolver_pista_de_musica
from src.framework.ecs import systems as ecs_systems
from src.framework.ecs.scheduler import Planificador
from src.framework.ecs.world import World
from src.framework.entities.bestiary import Bestiary
from src.framework.entities.boss_base import BossBase
from src.framework.entities.enemy_base import EnemyBase
from src.framework.entities.player import Player
from src.framework.entities.squad_brain import SquadBrain
from src.framework.scenes.stage_builder import StageBuilder
from src.framework.scenes.stage_facade import StageFacade
from src.framework.scenes.stage_parts.actualizaciones import ActualizacionesDeEscenario
from src.framework.scenes.stage_parts.ambiente import MezclaDeAmbiente
from src.framework.scenes.stage_parts.arco import ArcoDelJugador
from src.framework.scenes.stage_parts.cinematicas import CinematicasDeEscenario
from src.framework.scenes.stage_parts.diagnostico import DiagnosticoDeEscenario
from src.framework.scenes.stage_parts.dibujo import DibujoDeEscenario
from src.framework.scenes.stage_parts.economia import EconomiaDeEscenario
from src.framework.scenes.stage_parts.fantasma import FantasmaDeCarrera
from src.framework.scenes.stage_parts.mundo_ecs import MundoDelEscenario
from src.framework.scenes.stage_parts.pausa import PausaDeEscenario
from src.framework.scenes.stage_parts.rush import ConduccionDelBossRush
from src.framework.scenes.stage_parts.senales import SenalesDeEscenario
from src.framework.scenes.stage_parts.simulacion import SimulacionDeEscenario
from src.framework.scenes.stage_parts.sonido import SonidoDeEscenario
from src.framework.stage import culling
from src.framework.stage.camera import Camera
from src.framework.stage.collision_system import CollisionSystem
from src.framework.stage.combat_manager import CombatManager
from src.framework.stage.drawing_system import DrawingSystem
from src.framework.stage.hazard_system import HazardSystem
from src.framework.stage.interactable_system import InteractableSystem
from src.framework.stage.level_mechanics import (
    ControlDeNado,
    ScrollForzado,
    TiempoBala,
)
from src.framework.stage.objetivos import SistemaDeObjetivos
from src.framework.stage.progression_system import ProgressionSystem
from src.framework.stage.speedrun_mode import SpeedrunTimer, registrar_marca
from src.framework.stage.stage_loader import StageLoader
from src.framework.ui.dialogue_system import DialogueSystem
from src.framework.ui.learning_overlay import LearningOverlay
from src.framework.ui.tutorial_overlay import TutorialOverlay
from src.framework.vfx import pulso
from src.framework.vfx.ambient_particles import AmbientParticleSystem
from src.framework.vfx.damage_numbers import DamageNumberManager
from src.framework.vfx.lighting import LightSource, LightSystem
from src.framework.vfx.particle_system import ParticleSystem
from src.framework.vfx.post_processing import PostProcessing
from src.framework.vfx.trail_system import TrailSystem
from src.framework.vfx.weather_system import WeatherSystem

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.framework.stage.checkpoint import Checkpoint
    from src.framework.stage.stage_loader import StageData


def _arena_del_jefe(stage_data: StageData, cuerpo: pygame.Rect) -> pygame.Rect:
    """El cuadrilátero de combate del jefe (AUD-605).

    Gana la primera `ArenaZone` que contenga el centro del jefe. Sin
    ninguna, mapa completo — el comportamiento histórico que AUD-061
    introdujo y que seguía siendo lo único disponible desde Tiled.
    """
    for zona in stage_data.zonas_arena:
        if zona.collidepoint(cuerpo.center):
            return zona
    return pygame.Rect(0, 0, *stage_data.map_pixel_size)


class StageScene(MezclaDeAmbiente, SimulacionDeEscenario,
                 SenalesDeEscenario, SonidoDeEscenario,
                 EconomiaDeEscenario,
                 DiagnosticoDeEscenario, CinematicasDeEscenario,
                 ArcoDelJugador, MundoDelEscenario, ActualizacionesDeEscenario, DibujoDeEscenario,
                 FantasmaDeCarrera, ConduccionDelBossRush, PausaDeEscenario, BaseScene):
    """El escenario jugable: carga un TMX y lo hace jugar.

    AUD-152 - los tres primeros padres son **mixins de lectura**, no capas de
    arquitectura: sólo mueven texto que antes vivía aquí. Ver
    `stage_parts/__init__.py` para el razonamiento completo. El orden importa
    para el MRO en un solo sentido: `BaseScene` va al final, así que cualquier
    método que un mixin y la base compartan lo gana el mixin, que es lo que
    ocurría cuando el método estaba escrito en esta clase.
    """

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
        # Facade para clientes que no necesitan conocer la red interna (Facade)
        self.facade = StageFacade(self)
        # Builder para construcción por pasos (Builder)
        self._builder = StageBuilder(context, resolved)
        self._builder.attach_scene(self)
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
        # AUD-555 — el menú de pausa dejó de ser una lista vertical que
        # empuja una escena por opción (AUD-533/549/550) y pasó a ser un
        # panel con pestañas al estilo Ocarina of Time: "Equipo",
        # "Habilidades" y "Mapa" son consultas embebidas (`PausaDeEscenario`,
        # `stage_parts/pausa.py`); "Menú" es la lista corta de acciones
        # (Tienda/Guardar y salir/Salir al título) que antes vivían sueltas
        # en `_pause_options`. Los tres atributos `_pausa_*` con instancia
        # sólo existen mientras `_paused` es `True` — `None` el resto del
        # tiempo, para no arrastrar tres escenas vivas durante toda la
        # partida.
        self._pausa_tab: int = 0
        self._pausa_menu_seleccion: int = 0
        self._pausa_equipo: BaseScene | None = None
        self._pausa_habilidades: BaseScene | None = None
        self._pausa_mapa: BaseScene | None = None
        self._debug: bool = False
        #: AUD-289 — entidades que se retiraron por lanzar en `update()`.
        #:
        #: Pública porque es un dato del nivel que el estudiante tiene que poder
        #: ver: la consola de F11 la enseña. Se acumula por nombre de clase y no
        #: por instancia, que es como se lee («el WalkerX vuelve a fallar»).
        self.entidades_retiradas: list[str] = []
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
        #: AUD-400 — los objetivos del escenario (GAP-047).
        #:
        #: Se construye aquí, con la escena, y no al poblar el mundo: el bus
        #: guarda referencias **débiles**, así que el sistema tiene que vivir
        #: tanto como la suscripción tiene que durar. Un mapa que no declara
        #: objetivos deja esto vacío, y un sistema vacío da `todo_hecho` — que
        #: es lo que mantiene intactos los diecisiete mapas anteriores.
        self._objetivos = SistemaDeObjetivos(context.event_bus)
        # AUD-136 (D3) — el director de escenas. Se construye al cargar el
        # escenario; `_escenas_vistas` vive en la ESCENA y no en el director
        # para que sobreviva a las muertes: recargar el mapa crea objetos
        # nuevos, y sin esta memoria la introducción se repetiría en cada
        # intento.
        self._cutscenes: Any | None = None
        self._escenas_vistas: set[str] = set()
        #: AUD-140 — se reconstruye por escenario, como los interactuables.
        self._bloques: Any | None = None
        # AUD-137 (F6) — el reloj musical. `None` salvo que el mapa declare
        # `bpm`: un escenario que no es rítmico no paga nada por esto.
        self._reloj_musical: Any | None = None
        # F5 — el mundo ECS del escenario: viento, plataformas móviles, láseres,
        # agua, guardias y acosadores. Uno por escena y no global, para que dos
        # escenarios cargados a la vez —el juego y una previsualización— no se
        # mezclen. La lección del modo de vídeo global de pygame salió cara una
        # vez y no se repite.
        self._mundo: World = World()
        self._planificador: Planificador = self._construir_planificador()
        # AUD-111 — niebla de guerra y efecto de agua. `None` mientras el
        # escenario no los pida: los dos pintan una capa del tamaño de la
        # pantalla cada fotograma, y cobrárselo a los catorce escenarios que no
        # los usan sería pagar por nada.
        self._niebla = None
        self._agua_vfx = None
        # P0 — caché de unión de agua O(n) → O(1) si no cambia (id + rect.topleft)
        self._agua_union_cache: pygame.Rect | None = None
        self._agua_version: tuple[tuple[int, tuple[int, int]], ...] | None = None
        self._nado = ControlDeNado()
        self._tiempo_bala = TiempoBala()
        self._scroll_forzado = ScrollForzado()
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
        # AUD-219 — GAP-029, conexión 2 de 4. `ScoreSystem` estaba escrito
        # entero y nadie lo construía: sin instancia no hay suscripción a
        # `ENEMY_DIED`, y matar enemigos no sumaba un punto. Va junto a los
        # logros y el bestiario porque es el mismo tipo de dato —progreso del
        # jugador— y necesita lo mismo: el bus de *esta* escena.
        self._score = ScoreSystem.get_instance()
        self._score.bind_bus(self.context.event_bus)
        # AUD-267 — y exactamente lo mismo le pasaba a la experiencia.
        #
        # AUD-249 construyó `ExperienceSystem` entero —tabla por tipo, curva de
        # nivel, puntos de habilidad— y **nadie lo construía**: medido con
        # `grep -rn "ExperienceSystem" src/` fuera de su módulo, cero. Sin
        # instancia no hay suscripción a `ENEMY_DIED`, así que matar enemigos
        # no daba un solo punto de experiencia. Es la tercera vez que este
        # mismo patrón aparece en la misma línea de código: logros, puntuación
        # y ahora experiencia.
        self._experiencia = ExperienceSystem.get_instance()
        self._experiencia.bind_bus(self.context.event_bus)
        self._bestiary = Bestiary.get_instance()
        # AUD-154 — el bestiario tenía `save()` y `load()` escritos y nadie los
        # llamaba, así que ni siquiera lo poco que hubiera registrado habría
        # sobrevivido a cerrar el juego. Va junto a los logros porque es la
        # misma clase de dato: progreso del jugador, no de la partida.
        self._bestiary.load()
        self._speedrun = SpeedrunTimer()
        # AUD-142 — el fantasma. `GhostData` estaba escrita entera y no la
        # usaba nadie: ni se grababa ni se reproducía. `_fantasma` es la
        # carrera de ahora; `_fantasma_previo`, la mejor guardada.
        self._fantasma: Any | None = None
        self._fantasma_previo: Any | None = None
        self._dialogue = DialogueSystem(self.context)
        self._arboles_de_dialogo: dict[str, Any] = {}
        self._player_spawned: bool = False
        self._damage_taken_this_stage: float = 0.0
        self._stage_start_time: float = 0.0
        self._sfx_handlers: dict[str, Callable[..., None]] = {}
        self._vfx_handlers: dict[str, Callable[..., None]] = {}

    def on_stage_start(self) -> None:
        if "move" not in self._tutorial_shown:
            self._tutorial.show("move", duration=6.0)
            self._tutorial_shown.add("move")


    def on_player_landed(self) -> None:
        if "landed" not in self._tutorial_shown and hasattr(self, '_player') and self._player is not None:
            if abs(self._player.velocity.x) > 0:
                self._tutorial.show("attack", duration=5.0)
                self._tutorial_shown.add("landed")

    def on_enemy_died(self, enemy: EnemyBase) -> None:
        # AUD-154 — era `if hasattr(enemy, "enemy_id")`, y ninguna clase de
        # enemigo define ese atributo, así que el bestiario no se llenaba
        # nunca. `Bestiary.id_de` lo deduce del tipo cuando la entidad no lo
        # declara, que es el caso de los ocho arquetipos del motor.
        self._bestiary.record_kill(Bestiary.id_de(enemy))
        if "enemy_kill" not in self._tutorial_shown:
            self._tutorial.show("advanced", duration=5.0)
            self._tutorial_shown.add("enemy_kill")

    def on_next_trigger_entered(self) -> None:
        if "checkpoint" not in self._tutorial_shown:
            self._tutorial.show("checkpoint", duration=3.0)
            self._tutorial_shown.add("checkpoint")

    def on_debug_toggle(self, enabled: bool) -> None:
        ...

    def dibujar_fondo(self, surface: pygame.Surface,
                      offset: pygame.Vector2) -> None:
        """Pintura propia del escenario, **detrás** del mapa de baldosas.

        AUD-162 — el gancho que faltaba. Sobreescribiendo `draw()` un escenario
        podía pintar encima de todo, pero no detrás: lo primero que hace
        `DrawingSystem.draw` es `surface.fill(BG_COLOR)`, así que todo lo
        pintado antes de llamar a `super()` se borraba.

        Se llama después de las capas de parallax y antes del mapa, con el
        desplazamiento de la cámara ya calculado. No hace nada por defecto.
        """

    @property
    def stage_key(self) -> str:
        """La identidad de este escenario, una sola para todo el juego.

        AUD-156 — había dos y no coincidían. La clase declara `STAGE_ID` y el
        TMX declara `stage_id`, y el motor usaba **el del mapa** para el evento
        de escenario completado y para el logro de explorador, mientras el mapa
        del mundo usaba **el de la clase**. Dos escenarios divergían:

        * `lobby_datacenter` — su TMX se quedó con el `stage_id` de la
          plantilla, `stage_template`. El alumno lo declaró bien en su clase;
        * `stage2_1_oficinas` — su clase no declara `STAGE_ID`, así que ese
          lado quedaba vacío.

        En los dos, terminar el nivel apuntaba un identificador que el mapa del
        mundo no reconocía, de modo que el nodo **no se marcaba nunca como
        completado** y, con la progresión en cadena, bloqueaba todo lo que
        viniera detrás.

        Gana la clase porque es la que el estudiante controla desde Python y la
        que ya usan el registro de escenarios y el mapa del mundo; el TMX queda
        de respaldo para un mapa suelto sin escena propia.
        """
        de_la_clase = getattr(type(self), "STAGE_ID", "")
        if de_la_clase:
            return str(de_la_clase)
        data = getattr(self, "_stage_data", None)
        return str(getattr(data, "stage_id", "") or "")

    def _aplicar_exencion_de_habilidades(self) -> None:
        """¿Este escenario regala las mecánicas de jefe? — AUD-294.

        Dos caminos para eximir, y los dos existen por lo mismo: los mapas
        entregados no se tocan. La lista de `settings` los exime desde el motor;
        la propiedad `habilidades_libres` es para un mapa **nuevo** que quiera
        jugarse suelto y prefiera decirlo en su propio fichero.

        Lo que se escribe aquí es el `False`: el jugador nace libre (ver
        `Player.__init__`) y es **la escena** la que le pone el candado cuando
        el mapa no está exento. Así, un jugador construido fuera de un
        escenario se comporta como antes de AUD-294.
        """
        if self._player is None:
            return
        identidades = {self.stage_key,
                       str(getattr(self._stage_data, "stage_id", "") or "")}
        por_lista = bool(identidades & settings.ESCENARIOS_CON_HABILIDADES_LIBRES)
        por_mapa = bool(getattr(self._stage_data, "habilidades_libres", False))
        self._player._habilidades_libres = por_lista or por_mapa

    def _aplicar_partida_pendiente(self) -> None:
        """Coloca al jugador donde lo dejó la partida guardada, si es aquí.

        Se acepta el identificador de la clase **y** el del TMX porque hay
        partidas grabadas con el segundo: rechazarlas dejaría al jugador al
        principio del nivel sin decirle por qué.
        """
        pending = self.context.pending_load
        if pending is None:
            return
        identidades = {self.stage_key,
                       str(getattr(self._stage_data, "stage_id", "") or "")}
        identidades.discard("")
        if pending.stage_id not in identidades:
            return

        destino = pygame.Vector2(pending.checkpoint_x, pending.checkpoint_y)
        self._player.set_spawn(destino)
        self._player.set_health(pending.health)
        # AUD-292 — y la experiencia. `exp_total` se guardaba desde AUD-267 y
        # **nadie la volvía a leer**: cargar una partida devolvía al jugador a
        # nivel 1 con sus puntos de habilidad a cero, que es la misma familia de
        # defecto que aquel cerró por el otro extremo.
        #
        # Aquí y no sólo en `LoadGameScene` porque a un escenario se puede
        # llegar con una partida pendiente por más de un camino —el mapa del
        # mundo, `--stage`, la cadena de niveles—, y la experiencia tiene que
        # ser la misma llegue por donde llegue.
        estado = dict(getattr(pending, "exp_estado", {}) or {})
        if not estado and pending.exp_total:
            estado = {"exp": int(pending.exp_total)}
        if estado:
            ExperienceSystem.get_instance().from_dict(estado)
        self._checkpoint_position = destino
        self._restaurar_banderas(self.context, pending)
        self.context.pending_load = None

    @staticmethod
    def _restaurar_banderas(context: Any, pending: Any) -> None:
        """Devuelve al contexto las banderas de mundo de la partida (AUD-251).

        Estático y con el contexto por parámetro para que se pueda comprobar
        sin levantar un escenario entero: el defecto que cierra es de
        cableado, y una prueba que necesita un TMX para verlo no se escribe.
        """
        banderas = getattr(pending, "zone_flags", None)
        if banderas:
            context.banderas.update(banderas)

    def on_enter(self) -> None:
        # AUD-025: claim a cache scope so that leaving this scene does not throw
        # away assets a scene paused beneath us is still using.
        AssetLoader.enter_scope()
        self._subtitles.rearm()
        data = StageLoader.load(self._tmx_path)
        if data is None:
            raise RuntimeError(f"StageScene: failed to load stage from {self._tmx_path}")
        # AUD-658 — guarda explícita: StageLoader puede devolver None en casos
        # de TMX corrupto ya reportados vía report.ok; el raise de arriba hace
        # que _stage_data y _player nunca queden en estado parcial.
        assert data is not None
        self._stage_data = data
        spawn = self._stage_data.spawn_point
        assert spawn is not None, "spawn_point no puede ser None tras load exitoso"
        self._player = Player(spawn, event_bus=self.context.event_bus)
        # AUD-658 — invariante: on_enter siempre deja _player no-None
        assert self._player is not None
        if hasattr(self._stage_data, "gravity_multiplier"):
            self._player.gravity_multiplier = self._stage_data.gravity_multiplier
        # AUD-129 — la vista del escenario llega al jugador.
        #
        # Se escribe directamente y no con `hasattr` a propósito: `vista` tiene
        # valor por defecto en `StageData`, así que siempre existe. Un
        # `getattr(..., "lateral")` aquí sería justo el patrón que dejó el
        # sistema de diálogo sin abrirse durante meses (AUD-127) — si algún día
        # alguien renombra el campo, quiero un `AttributeError` ruidoso, no un
        # escenario que calla y se juega en la vista equivocada.
        self._player.vista_cenital = self._stage_data.vista == "cenital"
        # AUD-141 — la estamina, si este escenario la pide. Por el mismo
        # camino que la vista: una propiedad del mapa que la escena traslada
        # al jugador al cargar.
        self._player.activar_estamina(getattr(self._stage_data, "estamina", 0.0))
        # AUD-260 — y el tiempo bala por el mismo camino. `0` lo deja apagado,
        # que es lo que declaran los dieciséis mapas entregados.
        self._tiempo_bala = TiempoBala(
            reserva_maxima=float(getattr(self._stage_data, "tiempo_bala", 0.0)))
        # AUD-261 — la vida con la que se llega, si esto es un Boss Rush.
        self._aplicar_salud_arrastrada()
        # AUD-143 — modo de cámara del escenario.
        self._camera.modo = getattr(self._stage_data, "camara", "seguir")

        # AUD-022: relic stat bonuses were fully implemented and never applied.
        self._player.apply_relic_bonuses(get_inventory())

        self._achievements.mark_explorer(self.stage_key)

        self._camera = Camera()
        self._camera.follow(self._player)
        self._camera.set_map_size(*self._stage_data.map_pixel_size)

        # Builder delega el cableado de enemigos (Builder + Facade)
        self._builder.build_enemies(self._stage_data, self._player)

        self._checkpoints = list(self._stage_data.checkpoints)
        for cp in self._checkpoints:
            cp.set_event_bus(self.context.event_bus)
        self._checkpoint_position = None
        # AUD-156 — la partida guardada se aplica AQUÍ, después del reinicio.
        #
        # Estaba treinta y ocho líneas más arriba, y la línea de encima
        # —`self._checkpoint_position = None`— borraba justo lo que acababa de
        # poner. Efecto, medido en los quince escenarios: cargar una partida
        # devolvía al jugador al principio del nivel, y morir después lo
        # devolvía otra vez al principio en vez de a su checkpoint.
        #
        # Que ahora vaya después de `apply_relic_bonuses()` también importa:
        # esa llamada sube el máximo de vida y **regala la diferencia** como
        # vida actual, así que fijar la salud guardada antes la dejaría
        # inflada. No conseguí reproducirlo con las reliquias que existen hoy
        # —ninguna de las que probé sube el máximo—, pero el orden correcto es
        # éste y no depende de qué reliquias haya mañana.
        self._aplicar_exencion_de_habilidades()
        self._aplicar_partida_pendiente()
        # AUD-296 — aquí y no antes: un plugin que reciba el escenario lo
        # quiere **ya cargado**, con sus entidades y su jugador colocado.
        plugins.get_gestor().disparar(
            "escenario_cargado", escena=self, stage=self._stage_data)
        self._stage_complete = False
        self._game_over = False
        self._pending_game_over = False
        self._was_grounded = False
        self.context.scene_manager.transition.start_fade_in(0.5)
        self._collision.reset()
        self._squad.reset()
        # AUD-135: con el escenario, para que la inundación vuelva a su altura.
        # Sin esto, morir ahogado dejaría el agua arriba y el reintento sería
        # imposible: el fallo clásico de las mecánicas con estado.
        self._hazards.reset(self._stage_data)
        if self._bloques is not None:
            # AUD-140: un bloque empujado a un foso deja el nivel sin solución,
            # y el jugador no tiene forma de saber que ya no se puede pasar.
            self._bloques.reiniciar()
        if self._cutscenes is not None:
            self._cutscenes.reset()
        # F4.1: el sistema se reconstruye por escenario. Reutilizar el anterior
        # arrastraría el llavero y las puertas ya abiertas al siguiente nivel.
        self._interactables = InteractableSystem(
            recogibles=self._stage_data.recogibles,
            cerraduras=self._stage_data.cerraduras,
            cofres=self._stage_data.cofres,
            disparadores=self._stage_data.disparadores,
            bus=self.context.event_bus,
            warps=self._stage_data.warps,
            placas=getattr(self._stage_data, "placas", None),
        )
        self._montar_director_de_escenas()
        # AUD-140 — bloques empujables y destructibles del mapa.
        from src.framework.stage.bloques import SistemaDeBloques
        self._bloques = SistemaDeBloques(
            empujables=self._stage_data.empujables,
            destructibles=self._stage_data.destructibles,
            bus=self.context.event_bus,
        )
        # AUD-616 — delegar orquestación de combate al CombatManager
        self._combat = CombatManager(self._collision, self._bloques)
        self._configurar_vfx_opcionales()
        # AUD-400 — los objetivos que declara el mapa (GAP-047). Se dan de alta
        # aquí, con el resto del contenido del TMX, para que el sistema esté
        # escuchando antes de que el jugador pueda matar o recoger nada.
        for objetivo in getattr(self._stage_data, "objetivos", ()):
            self._objetivos.declarar(objetivo)
        self._poblar_mundo_ecs()
        # AUD-139 — el reloj musical va DESPUÉS de poblar el mundo.
        #
        # Estaba antes, y `_poblar_mundo_ecs` construye un `World` nuevo: el
        # recurso «reloj_musical» se ponía en un mundo que se tiraba a la
        # basura tres líneas después. Los bloques con `patron` habrían buscado
        # el reloj, no lo habrían encontrado y habrían seguido contando
        # segundos, en silencio y sin fallar.
        #
        # Es el mismo defecto que llevo todo el mes corrigiendo en código
        # ajeno —una pieza correcta que no llega a quien la necesita— y esta
        # vez era mío. No lo cazó ninguna prueba: las mías montaban el mundo a
        # mano. Lo cazó leer el orden de arranque.
        self._montar_reloj_musical()
        self._progression.reset()

        if self._stage_data.bgm_track:
            audio = self.audio
            if audio is not None:
                # AUD-485 — prefiere el `.ogg` de AUD-484 sobre el `.wav`
                # original; ver el docstring de `resolver_pista_de_musica`
                # para por qué el orden contrario ya no protege nada. Si
                # ninguno existe, se intenta igual con `.wav` para que
                # `AudioManager.play_music` deje su aviso de siempre en vez
                # de fallar en silencio.
                bgm_path = resolver_pista_de_musica(self._stage_data.bgm_track)
                if bgm_path is None:
                    bgm_path = settings.ASSETS_DIR / "music" / f"{self._stage_data.bgm_track}.wav"
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
        # AUD-499 — el hueco lo manda el HUD, que es quien conoce la franja
        # entera. Antes el minimapa se colocaba solo en el borde derecho y
        # caía justo encima del cronómetro.
        if self._hud is not None:
            self._minimap.colocar(self._hud.minimap_rect())
        self._minimap.set_map_size(*self._stage_data.map_pixel_size)

        # Speedrun timer
        self._cargar_los_arboles_de_dialogo()
        self._speedrun.start()
        self._speedrun.start_stage(self._stage_data.stage_id)
        self._preparar_fantasma()

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
            # AUD-145 — el ambiente del clima ya suena.
            #
            # Esto construía `assets/sfx/ambient/<clave>.wav`, y esa carpeta no
            # existe: el `.exists()` daba falso siempre y el clima era mudo en
            # silencio. Ahora el sistema de clima devuelve la ruta del fichero
            # real, y cuando un clima no tiene sonido se dice en el registro
            # en vez de callarse.
            self._aplicar_ambiente_del_clima()
            if self._weather.falta_su_ambiente():
                logging.getLogger(__name__).warning(
                    "el clima %r no tiene sonido ambiente todavía: falta el "
                    "fichero en assets/sfx/environment/", climate,
                )

        self._setup_lighting()
        self._setup_post_processing()
        self._setup_ambient_particles()
        self._setup_day_night()
        self._vfx_handlers.clear()
        self._sfx_handlers.clear()
        try:
            self._subscribe_event_handlers()
            self._suscribir_boss_rush()
        except Exception:
            self._unsubscribe_all_handlers()
            raise
        for sl in self._stage_lights:
            self._lighting.add_light(sl)
        # AUD-278 — la geometría que tapa la luz, si el mapa lo pide. Sin la
        # propiedad, la lista va vacía y el sistema de luz se comporta
        # exactamente como antes: una antorcha detrás de un muro sigue
        # iluminando a través, que es lo que hacen los dieciséis mapas
        # entregados y lo que sus autores calificaron.
        if getattr(self._stage_data, "sombras_proyectadas", False):
            self._lighting.set_obstaculos(self._stage_data.collision_rects)

    # ── El ambiente vive en `stage_parts/ambiente.py` ─────────────
    #
    # AUD-152: luz, bloom, viñeta, partículas, estación y hora, con su regla
    # de precedencia común (TMX > zona > motor). Se movió el texto tal cual:
    # los nombres y el comportamiento son los mismos, y una subclase que
    # sobreescriba `_setup_lighting` sigue funcionando.

    # ── Las señales viven en `stage_parts/senales.py` ─────────────
    #
    # AUD-152: `_subscribe_event_handlers`, `_unsubscribe_all_handlers`,
    # `_make_sfx_handler` y los dos reproductores de sonido.

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
        self._bestiary.save()
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
            # AUD-502 — `set_spawn` es la única puerta sancionada para
            # recolocar al jugador: deja `position` y `rect` de acuerdo y
            # pone velocidad e inercia a cero. Las dos líneas que había aquí
            # se la saltaban y aplicaban dos convenciones a la vez —esquina
            # en `position`, centro en `rect`—, y ganaba la esquina en el
            # siguiente fotograma (`_update_rect_size` reescribe `rect.x/y`
            # desde `position`), con los pies media caja por debajo del
            # suelo.
            self._player.set_spawn(pygame.Vector2(cp))
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
        # AUD-136 (D3) — las escenas van ANTES del juego y pueden pararlo.
        #
        # Una escena que bloquea congela al jugador y a los enemigos, pero no
        # el resto: la cámara del guion tiene que poder moverse, el clima
        # sigue, el diálogo se actualiza. Por eso esto no es una vuelta
        # temprana sino una condición sobre las dos llamadas de juego.
        en_escena = self._actualizar_escenas(dt)
        if not self._game_over and not en_escena:
            self._update_gameplay(dt)
        if not self._game_over and not en_escena:
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
        # AUD-296 — al final del fotograma, con el mundo ya resuelto: un plugin
        # que lea posiciones las quiere definitivas, no a medio integrar.
        plugins.get_gestor().disparar("escenario_actualizado", escena=self, dt=dt)

    def _handle_input(self) -> None:
        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.PAUSE):
            self._paused = not self._paused
            # AUD-022: HUD.pause_timer / resume_timer existed and were never
            # called, so on a timed stage the countdown kept draining while the
            # player sat in the pause menu — pausing cost you the run. Music
            # likewise kept playing over the pause screen.
            self._set_paused_side_effects(self._paused)
            # AUD-555 — el panel con pestañas se construye al entrar en
            # pausa y se destruye al salir (`PausaDeEscenario`); Cancelar
            # desde dentro del panel lo cierra por su cuenta
            # (`_handle_pause_input`), así que esto sólo cubre abrir/
            # cerrar con la propia tecla de pausa.
            if self._paused:
                self._abrir_panel_de_pausa()
            else:
                self._cerrar_panel_de_pausa()
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

    # AUD-555 — `_handle_pause_input` (navegación de pestañas, Cancelar) y
    # la apertura de Equipo/Habilidades/Mapa como consultas embebidas viven
    # ahora en `PausaDeEscenario` (`stage_parts/pausa.py`): son el panel de
    # pausa, no el resto de la escena. Sólo `_abrir_tienda` se queda aquí
    # — la Tienda sigue siendo una escena empujada de verdad, no una
    # pestaña embebida, y `PausaDeEscenario` la llama por su nombre.

    def _abrir_tienda(self) -> None:
        """AUD-550 — empuja `ShopScene` de verdad (no una pestaña
        embebida, ver `PausaDeEscenario`): `ShopScene` sale con `pop()`,
        así que empujarla aquí devuelve a la partida pausada, no al
        título."""
        from src.engine.scenes.shop_scene import ShopScene
        self.context.scene_manager.push(ShopScene(self.context))

    def _check_player_death(self) -> None:
        if self._player.current_health <= 0 and not self._game_over:
            self._kill_player()

    # ── AUD-111 — VFX opcionales declarados en el TMX ──────────


    def _publicar_o_dibujar_el_agua(self, surface) -> None:
        """El agua la pinta el sombreador si hay GL, y `WaterEffect` si no.

        AUD-216 — no son el mismo efecto y por eso se elige uno: `WaterEffect`
        superpone líneas senoidales *encima* de la escena, y el sombreador
        deforma lo que se ve *a través* del agua, que es lo que el primero
        imitaba. Dibujar los dos sumaría una superposición sobre una
        refracción, que es el defecto que AUD-222 acaba de quitar del bloom.

        AUD-623 — la región se publica desde las zonas de agua ECS reales,
        no la pantalla entera. Se calcula la unión de todas las `ZonaDeAgua`
        visibles en cámara y se publica su envolvente.

        P0 — caché O(n) → O(1): guarda `self._agua_union_cache` (unión en mundo)
        y `self._agua_version` (tupla de `id` + `rect.topleft` por zona) y
        recalcula sólo si `len(ZonaDeAgua)` o algún `rect` cambia.
        """
        from src.engine.core import gpu_effects
        from src.framework.ecs.components import ZonaDeAgua

        if gpu_effects.WATER in gpu_effects.effects_on_gpu():
            # Versión que cambia si hay más/menos agua o si alguna se movió
            # Spec: usa `id` + `rect.topleft`; incluimos tamaño implícitamente
            # via rect copy, pero la clave es topleft como pide el enunciado.
            version: tuple[tuple[int, tuple[int, int]], ...] = tuple(
                (id(agua), (agua.rect.x, agua.rect.y)) for _, agua in self._mundo.cada(ZonaDeAgua)
            )
            world_union: pygame.Rect | None
            if self._agua_version != version:
                # Recalcula unión en mundo O(n) — sólo cuando cambia el agua
                world_union = None
                for _, agua in self._mundo.cada(ZonaDeAgua):
                    if agua.rect.width <= 0 or agua.rect.height <= 0:
                        continue
                    if world_union is None:
                        world_union = agua.rect.copy()
                    else:
                        world_union = world_union.union(agua.rect)
                self._agua_union_cache = world_union
                self._agua_version = version
            else:
                world_union = self._agua_union_cache

            if world_union is not None:
                # Lleva la unión del mundo a pantalla O(1) — clamp y publish
                rect_pantalla = world_union.move(-int(self._camera.offset.x), -int(self._camera.offset.y))
                # Culling si totalmente fuera de pantalla (evita publish innecesario)
                if rect_pantalla.right <= 0 or rect_pantalla.left >= settings.INTERNAL_WIDTH:
                    return
                if rect_pantalla.bottom <= 0 or rect_pantalla.top >= settings.INTERNAL_HEIGHT:
                    return
                rect_pantalla.clamp_ip(pygame.Rect(0, 0, settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
                gpu_effects.publish_water_region(
                    (rect_pantalla.left, rect_pantalla.top, rect_pantalla.width, rect_pantalla.height),
                )
        else:
            self._agua_vfx.draw(surface, self._camera.offset)


    # ── F5.14 — lianas y tirolesas ─────────────────────────────

    # ── F5 — el mundo ECS del escenario ────────────────────────


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
        # AUD-260 — el tiempo bala, si este escenario lo pide. Va con el `dt`
        # **sin escalar** por la misma razón que el hit-stop de arriba: con el
        # escalado, la reserva duraría más cuanto más lenta fuera la cámara
        # lenta, que es un bucle de realimentación absurdo.
        if self._tiempo_bala.reserva_maxima > 0.0:
            self._tiempo_bala.update(
                unscaled_dt,
                im.is_action_held(Action.BULLET_TIME),
                clock,
            )
        # AUD-261 — el cronómetro del combate de Boss Rush. Con el `dt` sin
        # escalar por la misma razón: el tiempo bala no puede regalar
        # puntuación por ralentizar el mundo.
        modo_rush = self._boss_rush_activo()
        if modo_rush is not None:
            modo_rush.registrar_tiempo(unscaled_dt)
        try:
            # F4.1 — una puerta cerrada bloquea el paso; al abrirse deja de
            # hacerlo. Se suma aquí en vez de mutar `stage.collision_rects`,
            # que es la lista que construye el cargador y leen varios sistemas:
            # cambiarla para simular un estado es el atajo que después nadie
            # sabe deshacer.
            cerradas = self._interactables.rects_solidos()
            # AUD-349 — los sólidos con que los bloques empujan y caen se
            # componían DOS veces por fotograma (empujar y caer, cada uno con
            # `stage.collision_rects + cerradas`). En stage 4-1, cuyo mapa son
            # miles de rectángulos, eso son dos copias O(n) por frame de pura
            # churn. Se compone una vez y se comparte la misma lista: `caer`
            # y `empujar` sólo la leen y mutan los rectángulos que contiene,
            # nunca la estructura.
            con_cerradas = (stage.collision_rects + cerradas
                            if cerradas else stage.collision_rects)
            # AUD-140: los bloques entran en la lista de sólidos por el mismo
            # camino que las puertas cerradas, sumando y sin mutar la lista
            # del cargador.
            extra = cerradas + (self._bloques.rects_solidos()
                                if self._bloques is not None else [])
            solidos = stage.collision_rects + extra if extra else stage.collision_rects
            if self._bloques is not None:
                # Empujar va ANTES de que el jugador resuelva su colisión: si
                # fuera después, el jugador ya estaría metido en el bloque y
                # el motor lo expulsaría antes de que el bloque se apartase.
                direccion = 0
                if im is not None:
                    if im.is_action_held(Action.MOVE_RIGHT):
                        direccion = 1
                    elif im.is_action_held(Action.MOVE_LEFT):
                        direccion = -1
                if player is not None and player.is_grounded:
                    self._bloques.empujar(player.rect, direccion, dt,
                                          con_cerradas)
                self._bloques.caer(dt, con_cerradas)

            # AUD-XXX — placas de presión: usan la misma lista de solidos
            # ``con_cerradas`` que los bloques (no duplican composición) y se
            # evalúan DESPUÉS de que los bloques se hayan movido, para que el
            # peso del fotograma ya esté en su sitio definitivo. Si una placa
            # abre una puerta, se recompone ``solidos`` para que el jugador la
            # note en este mismo fotograma (sin 1 frame de retardo).
            if getattr(self._interactables, "placas", None) is not None:
                try:
                    bloques_para_placa = (
                        self._bloques.empujables if self._bloques is not None else []
                    )
                    if player is not None:
                        self._interactables.actualizar_placas(
                            bloques_para_placa, player.rect,
                        )
                        # Recompone cerradas/solidos si alguna puerta cambió.
                        nuevas_cerradas = self._interactables.rects_solidos()
                        if len(nuevas_cerradas) != len(cerradas) or nuevas_cerradas != cerradas:
                            cerradas = nuevas_cerradas
                            con_cerradas = (
                                stage.collision_rects + cerradas
                                if cerradas else stage.collision_rects
                            )
                            extra = cerradas + (
                                self._bloques.rects_solidos()
                                if self._bloques is not None else []
                            )
                            solidos = (
                                stage.collision_rects + extra if extra else stage.collision_rects
                            )
                except Exception:
                    logging.getLogger(__name__).warning(
                        "placas: fallo al actualizar", exc_info=True,
                    )

            # F5.3–F5.6 — las mecánicas nuevas corren ANTES que el jugador.
            #
            # El orden importa y es el motivo de que esto esté aquí y no en
            # `_update_vfx`: las plataformas tienen que haberse movido y haber
            # arrastrado a su pasajero antes de que el jugador resuelva sus
            # colisiones. Al revés, el pasajero pasaría un fotograma hundido en
            # la plataforma y saldría expulsado al siguiente. El orden completo,
            # con su porqué, está en `framework/ecs/scheduler.py`.
            # AUD-119 — la maquinaria del nivel usa `dt_mundo`, no `dt`.
            #
            # `dt` incluye el hit-stop, así que los 50 ms de congelación de
            # cada golpe también paraban los bloques rítmicos, los láseres y
            # las plataformas móviles. Eso es un exploit —golpear a un enemigo
            # junto a un láser lo detenía— y, en un nivel a compás, una
            # desincronización que se acumula y que nada corrige.
            #
            # `dt_mundo` sí respeta la cámara lenta: ralentizar el mundo es lo
            # que la cámara lenta *es*. Lo que no debe mover el reloj del
            # escenario es un efecto de presentación de 50 ms.
            dt_mundo = getattr(clock, "dt_mundo", dt) if clock is not None else dt
            self._planificador.ejecutar(self._mundo, dt_mundo)
            moviles = ecs_systems.rects_solidos(self._mundo)
            if moviles:
                solidos = solidos + moviles
            # AUD-508 — un `Solido` dinámico con `atravesable_desde_abajo=True`
            # (una `MovingPlatform` marcada así en Tiled, o cualquier
            # `SinkingPlatform` al reaparecer) va a `one_way_rects`, no a
            # `solidos`: antes `rects_solidos` los devolvía todos juntos y el
            # dato se perdía, así que nunca se podía saltar a través de ellos.
            atravesables = ecs_systems.rects_atravesables_desde_abajo(self._mundo)
            one_way_rects = (
                stage.one_way_rects + atravesables if atravesables
                else stage.one_way_rects
            )

            player.update(dt, solidos, im, one_way_rects=one_way_rects,
                          pendientes=stage.pendientes)
            self._nado.update(dt, player, self._mundo, self.context.event_bus)
            # AUD-599 — GAP-072.1: el medio le dice al nado hacia dónde va
            # el agua. `SwimmingState` usa este vector como objetivo del
            # arrastre neutral; en tierra firme vale cero y no hace nada.
            player.corriente_medio = self._nado.corriente_medio
            self._actualizar_agarres(player, im)
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
            # AUD-279 — la zona activa: el encuadre más 400 px por lado.
            #
            # Se calcula una vez por fotograma y no una vez por enemigo, que es
            # el error obvio en un bucle como este: `zona_activa` construye un
            # `Rect` y leer `settings` no es gratis multiplicado por doscientos.
            zona = culling.zona_activa(self._camera.offset)
            for enemy in enemies:
                # Lejos de la cámara no se simula (jefes y quien tenga algo
                # volando quedan exentos; ver `framework/stage/culling.py`).
                # `set_player_ref` sí se hace siempre: es una asignación, y
                # dejarla fuera haría que un enemigo que vuelve a entrar en la
                # zona apuntase durante un fotograma a la posición vieja.
                enemy.set_player_ref(player.rect)
                if not culling.se_simula(enemy, zona):
                    continue
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
                # AUD-289 — y si la entidad revienta, revienta ella sola.
                try:
                    enemy._check_player_contact(player)
                    enemy.update(dt)
                except Exception:
                    self._retirar_entidad_rota(enemy)
            # AUD-140 — el golpe rompe bloques ANTES de resolverse contra los
            # enemigos, porque `process_attack` consume la caja al conectar:
            # después, un ataque que hubiera tocado enemigo y bloque a la vez
            # dejaría el bloque intacto sin que nadie entendiera por qué.
            #
            # Suena `SFX_HIT_CONNECT`, que es el sonido de que un golpe
            # acertó. No hay un sonido de «bloque roto» y no voy a inventar
            # un nombre para un fichero que no existe: eso es exactamente lo
            # que llevaba `05_ENEMY_SPEC.md` prometiendo (AUD-133).
            self._combat.process_attack(dt, player, stage, self._camera, clock)
        finally:
            # AUD-498 — el descuento del hit-stop ya NO se hace aquí.
            #
            # Vivía en este `finally` con el delta sin escalar, que era
            # correcto por sí solo (AUD-001) y aun así insuficiente: `App`
            # simula en pasos fijos y `pasos_fijos()` consume el delta
            # **escalado**, así que con `time_scale` a 0.0 —lo que pone el
            # propio hit-stop— no llega ni un paso, este método no se ejecuta
            # y el freno no lo suelta nadie. Un delta bueno no sirve de nada
            # si a la función no la llama nadie.
            #
            # Ahora lo lleva `actualizar_en_tiempo_real`, que corre una vez
            # por fotograma con el reloj real, igual que ya hacían las
            # transiciones. Aquí sólo queda registrar el factor del fotograma
            # en curso, sin descontar tiempo.
            self._combat.aplicar_factor_hitstop(clock)

    def actualizar_en_tiempo_real(self, dt_sin_escalar: float) -> None:
        """El hit-stop se descuenta aqui, con el reloj real (AUD-498).

        Fuera del acumulador de pasos fijos a proposito: es el unico sitio
        que sigue corriendo cuando `time_scale` vale 0.0, que es justo lo que
        el hit-stop provoca. Ver el `finally` de `_update_combat` para la
        cadena completa.
        """
        self._combat.update_hitstop(dt_sin_escalar, self.context.clock)

    def _update_camera_map(self, dt: float) -> None:
        stage = self._stage_data
        self._camera.update(dt)
        # AUD-425 — el latido de la cámara, después de `update` y antes de que
        # el mapa lea el `offset`.
        #
        # Se suma al offset ya resuelto en vez de dárselo a la cámara como
        # objetivo: el suavizado de `follow` se comería un empujón de 1,5 px
        # antes de que se viera, que es justo la clase de sistema correcto que
        # no llega a ninguna parte. Sin `bpm` en el mapa no hay reloj y esto
        # suma cero.
        self._camera.offset.y += pulso.offset_de_camara(
            getattr(self, "_reloj_musical", None))
        if stage.map_layer is not None and hasattr(stage.map_layer, '_map_layer'):
            stage.map_layer._map_layer.view_rect = pygame.Rect(
                self._camera.offset.x, self._camera.offset.y,
                settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT,
            )
        self._camera.set_camera_locks(stage.camera_locks)
        cp_pos = self._progression.process_checkpoints(
            self._player, stage, self._checkpoints, self._hud,
            stage_key=self.stage_key,
        )
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
            # AUD-202 — el tiempo se persiste, no sólo se enseña un segundo.
            # `save()` existía desde el primer día sin que nadie lo llamara, así
            # que la pantalla de récords no tenía qué leer y enseñaba tiempos
            # escritos a mano.
            #
            # AUD-231 — pero `save()` era la llamada equivocada. Vuelca la
            # carrera actual, y `on_enter` acaba de vaciar los parciales con
            # `start()`, así que escribía una sola marca encima de todas las
            # anteriores: la tabla sólo podía enseñar el último nivel jugado.
            # `registrar_marca` acumula, y sólo pisa una marca cuando mejora.
            registrar_marca(stage.stage_id, self._speedrun.global_time)
            self._guardar_fantasma_si_es_mejor()
            # AUD-022: the speedrun timer ran the whole stage and then threw the
            # result away — get_formatted_time() and get_splits() had no callers,
            # so the player never saw their time. Surface it on completion.
            if self._banner is not None:
                self._banner.play(
                    "STAGE_COMPLETE",
                    f"CLEAR  {self._speedrun.get_formatted_time()}",
                )
            # AUD-261 — si esto es un combate del Boss Rush, se acredita antes
            # de anunciar el escenario completado: `STAGE_COMPLETE` hace
            # avanzar la cola del `SceneManager`, y acreditar después dejaría
            # el arrastre de vida escrito cuando el combate siguiente ya ha
            # empezado. Es GAP-030, cerrado.
            self._acreditar_boss_rush()
            self.context.event_bus.emit(Events.STAGE_COMPLETE,
                                        stage_id=self.stage_key)

    # ── El fantasma vive en `stage_parts/fantasma.py` ─────────────
    #
    # AUD-152: grabar, cargar, guardar y dibujar la mejor carrera.

    def _montar_reloj_musical(self) -> None:
        """AUD-137 — el compás del escenario, si lo tiene.

        Se le da el gestor de audio como fuente: la posición sale del
        mezclador y no de sumar fotogramas. Sumando fotogramas, el nivel y la
        canción llevan relojes distintos y a los cinco minutos van medio
        compás desfasados — la razón por la que hasta ahora no se podía hacer
        un nivel rítmico de verdad.
        """
        from src.engine.audio.music_clock import RelojMusical

        stage = self._stage_data
        if stage is None or getattr(stage, "bpm", 0.0) <= 0.0:
            self._reloj_musical = None
            self._mundo.poner_recurso("reloj_musical", None)
            return
        self._reloj_musical = RelojMusical(
            bpm=stage.bpm,
            compas=getattr(stage, "compas", 4),
            desfase=getattr(stage, "desfase_audio", 0.0),
            fuente=self.audio,
        )
        self._mundo.poner_recurso("reloj_musical", self._reloj_musical)

    #: Colores de los bloques. Planos y no sprites por lo mismo que los
    #: interactuables: el motor no puede suponer qué arte tiene cada
    #: escenario, y un rectángulo del color correcto siempre se ve.
    _COLOR_EMPUJABLE = (150, 120, 85)
    _COLOR_DESTRUCTIBLE = (120, 115, 110)

    def _dibujar_bloques(self, surface: pygame.Surface) -> None:
        """Los bloques se dibujan, y no es opcional.

        Un empujable se mueve, así que las baldosas no pueden representarlo; un
        destructible desaparece. Si el motor no los pinta, el jugador ve un
        muro invisible que a veces cede — que es como se lee un fallo.
        """
        offset = self._camera.offset
        bloques = self._bloques
        if bloques is None:
            return
        for bloque in bloques.empujables:
            r = bloque.rect.move(-int(offset.x), -int(offset.y))
            pygame.draw.rect(surface, self._COLOR_EMPUJABLE, r)
            pygame.draw.rect(surface, (95, 75, 50), r, 2)
        for roto in bloques.destructibles:
            if roto.roto:
                continue
            r = roto.rect.move(-int(offset.x), -int(offset.y))
            pygame.draw.rect(surface, self._COLOR_DESTRUCTIBLE, r)
            # Las grietas cuentan cuánto le queda. Sin ellas, golpear un
            # bloque de tres golpes no da ninguna señal de estar avanzando y
            # el jugador se va antes del tercero.
            for i in range(roto._recibidos):
                y = r.top + (i + 1) * r.height // (max(1, roto.golpes) + 1)
                pygame.draw.line(surface, (60, 55, 50), (r.left + 2, y),
                                 (r.right - 2, y), 1)


    #: Velocidad, en px/s, a partir de la cual un enemigo deja estela.
    #:
    #: F1.4: el sistema de estelas sólo lo usaba el jugador, así que la
    #: embestida de un jefe —el movimiento más rápido y más peligroso del
    #: juego— no dejaba rastro. La estela no es decoración en ese caso: es la
    #: información que permite leer de dónde viene el ataque.
    ENEMY_TRAIL_SPEED = 180.0


    def _save_and_quit(self) -> None:
        if self._stage_data is not None and self._player is not None:
            self.context.event_bus.emit(
                Events.SAVE_REQUESTED,
                stage_id=self.stage_key,
                stage_index=self.context.scene_manager.stage_index,
                # AUD-502 — misma convención de esquina superior izquierda
                # que `ProgressionSystem.process_checkpoints`, no el centro.
                checkpoint_x=self._player.rect.x,
                checkpoint_y=self._player.rect.y,
                health=self._player.current_health,
                # AUD-439 — el máximo real del jugador, no la constante.
                max_health=float(self._player.max_health),
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
