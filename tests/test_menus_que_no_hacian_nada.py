"""
Opciones, dificultad, bestiario y mapa del mundo — AUD-154 y AUD-155.

Cuatro pantallas que se dibujaban bien y no hacían nada. El patrón es el mismo
de siempre en este proyecto —código correcto que nadie alcanza— pero aquí llega
hasta el jugador: son las cuatro que se tocan desde el menú.

Lo que se encontró, comprobado ejecutándolo antes de tocar nada
---------------------------------------------------------------
1. **Ningún control de OPCIONES funcionaba.** La pantalla miraba
   `event.type == pygame.USEREVENT` y luego `event.user_type`, que es la API de
   pygame_gui **0.5**; el proyecto usa 0.6.14, donde cada evento tiene su
   propio tipo. `UI_BUTTON_PRESSED` es 32866 y `USEREVENT` es 32865, así que la
   condición era falsa siempre y el cuerpo entero del método no corría. Efecto:
   VOLVER y ATAJOS DE TECLADO muertos —la pantalla de teclas, inalcanzable—, y
   `_dirty` nunca a `True`, luego **nada se guardaba**.
2. **Dos botones de accesibilidad sin rama.** Movimiento reducido y
   pulsar/mantener se añadieron en AUD-126 y nadie les escribió el `if`.
3. **Dos de los ocho mandos de la dificultad no llegaban al juego.**
   `parry_window` y `combo_window` estaban en los tres presets y nadie los
   leía: todo el mundo jugaba con las constantes de siempre.
4. **El bestiario no registraba nada.** `StageScene` hacía
   `if hasattr(enemy, "enemy_id")` y ninguna clase de enemigo define ese
   atributo. La pantalla filtra por `encountered`, así que salía vacía siempre.
5. **El mapa del mundo apuntaba a cuatro mapas que no existen** y no incluía
   ninguno de los once escenarios de los estudiantes.

Estas pruebas van por el camino del jugador: eventos reales de pygame_gui,
partidas reales, y el registro de escenarios de verdad.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture
def contexto(_video):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=EventBus(),
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


@pytest.fixture
def opciones(contexto):
    from src.engine.scenes.options_scene import OptionsScene

    escena = OptionsScene(contexto)
    contexto.scene_manager.push(escena)
    escena.on_enter()
    return escena


def _enfocar(escena, clave: str) -> None:
    """Pone el foco en la fila de un ajuste, por su clave."""
    for i, item in enumerate(escena._menu.items):
        if item.value == clave:
            escena._menu.index = i
            return
    raise AssertionError(f"no hay fila para {clave!r} en Opciones")


class TestLosBotonesDeOpcionesLlegan:
    """AUD-452 — las mismas garantías, con el kit del juego.

    Estas pruebas nacieron en AUD-154, cuando se descubrió que los eventos de
    `pygame_gui` no llegaban y **nada de lo que el jugador elegía se
    guardaba**. La pantalla ya no usa `pygame_gui`, pero lo que protegen sigue
    valiendo palabra por palabra: que VOLVER salga, que CONTROLES sea
    alcanzable, que los interruptores conmuten y que lo elegido se persista.
    Sólo cambia por dónde se toca.
    """

    def test_volver_sale_de_la_pantalla(self, contexto, opciones) -> None:
        _enfocar(opciones, "VOLVER")
        opciones._activar()
        assert type(contexto.scene_manager.current).__name__ == "TitleScene", (
            "la fila VOLVER no lleva a ninguna parte"
        )

    def test_atajos_de_teclado_es_alcanzable(self, contexto, opciones) -> None:
        """Era la única puerta a la pantalla de teclas, y estaba tapiada."""
        _enfocar(opciones, "CONTROLES")
        opciones._activar()
        assert type(contexto.scene_manager.current).__name__ == "KeybindingScene"

    @pytest.mark.parametrize("clave", [
        "subtitles_enabled", "reduced_motion", "hold_to_press",
        "contorno_de_enemigos",
    ])
    def test_los_interruptores_cambian(self, opciones, clave) -> None:
        _enfocar(opciones, clave)
        antes = opciones.valor_de(clave)
        opciones.cambiar_valor(+1)
        assert opciones.valor_de(clave) is not antes

    def test_el_idioma_cambia(self, opciones) -> None:
        _enfocar(opciones, "language")
        antes = opciones.valor_de("language")
        opciones.cambiar_valor(+1)
        assert opciones.valor_de("language") != antes
        # Se deja como estaba: `set_idioma` es global y contaminaría el resto.
        opciones.cambiar_valor(-1)


class TestLoQueSeEligeSeGuarda:
    """AUD-154 — `_dirty` no se ponía nunca y `_save_config()` no corría jamás.

    AUD-452 quitó el problema de raíz en vez de vigilarlo: ya no hay un
    «pendiente de guardar» que pueda quedarse a medias, porque cada cambio
    escribe en las preferencias en el acto. Lo que se comprueba, entonces, es
    lo que de verdad importaba: que el ajuste llegue a `user_settings`.
    """

    def test_mover_el_volumen_llega_a_las_preferencias(self, opciones) -> None:
        from src.engine.core import user_settings

        _enfocar(opciones, "music_volume")
        antes = float(user_settings.get().music_volume)
        opciones.cambiar_valor(+1)
        assert float(user_settings.get().music_volume) != antes

    def test_cambiar_la_dificultad_tambien(self, opciones) -> None:
        from src.engine.core import user_settings

        _enfocar(opciones, "difficulty")
        antes = user_settings.get().difficulty
        opciones.cambiar_valor(+1)
        assert user_settings.get().difficulty != antes, (
            "elegir dificultad no se guardaba: duraba la sesión y se perdía "
            "al cerrar el juego"
        )

    def test_elegir_la_dificultad_la_aplica_al_momento(self, opciones) -> None:
        """Antes se aplicaba en `on_exit`; ahora, al elegirla.

        Es mejor sitio: salir de la pantalla por un camino que no pasara por
        ahí —un fallo, un cambio de escena desde otro sitio— dejaba la
        dificultad elegida sin aplicar.
        """
        from src.engine.core.difficulty import Difficulty, get_difficulty, set_difficulty

        _enfocar(opciones, "difficulty")
        try:
            for _ in range(len(("easy", "normal", "hard"))):
                opciones.cambiar_valor(+1)
                if opciones.valor_de("difficulty") == "hard":
                    break
            assert get_difficulty() is Difficulty.HARD
        finally:
            set_difficulty(Difficulty.NORMAL)


class TestLosOchoMandosDeLaDificultadLlegan:
    """Que un preset declare un número no significa que alguien lo lea."""

    @pytest.fixture(autouse=True)
    def _normal(self):
        from src.engine.core.difficulty import Difficulty, set_difficulty

        yield
        set_difficulty(Difficulty.NORMAL)

    def _jugador(self):
        from src.framework.entities.player import Player

        jugador = Player(pygame.Vector2(100, 100))
        jugador._invincibility_timer = 0.0
        return jugador

    def _con(self, dificultad):
        from src.engine.core.difficulty import Difficulty, set_difficulty

        set_difficulty(Difficulty[dificultad])

    def test_el_dano_recibido_escala(self, _video) -> None:
        vidas = {}
        for nivel in ("EASY", "HARD"):
            self._con(nivel)
            jugador = self._jugador()
            jugador._event_bus = _BusMudo()
            jugador.apply_damage(1.0, (0.0, 0.0))
            vidas[nivel] = jugador.current_health
        assert vidas["EASY"] > vidas["HARD"]

    def test_la_curacion_escala(self, _video) -> None:
        curado = {}
        for nivel in ("EASY", "HARD"):
            self._con(nivel)
            jugador = self._jugador()
            jugador._health = 1.0
            jugador.heal(1.0)
            curado[nivel] = jugador.current_health
        assert curado["EASY"] > curado["HARD"]

    def test_la_vida_del_enemigo_escala(self, _video) -> None:
        from src.framework.entities.enemy_walker import EnemyWalker

        vidas = {}
        for nivel in ("EASY", "HARD"):
            self._con(nivel)
            vidas[nivel] = EnemyWalker(pygame.Vector2(0, 0)).max_health
        assert vidas["EASY"] < vidas["HARD"]

    def test_la_ventana_de_parry_escala(self, _video) -> None:
        """AUD-154 — era una constante `_PARRY_DURATION = 0.2` y los tres
        presets declaraban su `parry_window` para nadie."""
        from src.framework.entities.states.ability import ParryState

        ventanas = {}
        for nivel in ("EASY", "HARD"):
            self._con(nivel)
            jugador = self._jugador()
            jugador._event_bus = _BusMudo()
            ParryState().enter(jugador)
            ventanas[nivel] = jugador._parry_window
        assert ventanas["EASY"] > ventanas["HARD"], (
            f"la ventana de parry no cambia con la dificultad: {ventanas}"
        )

    def test_la_ventana_de_combo_escala(self, _video) -> None:
        """El otro mando desconectado: se usaba `settings.COMBO_WINDOW`."""
        from src.engine.core.difficulty import get_config

        ventanas = {}
        for nivel in ("EASY", "HARD"):
            self._con(nivel)
            ventanas[nivel] = get_config().combo_window
        assert ventanas["EASY"] > ventanas["HARD"]

        import inspect

        from src.framework.entities.states import helpers

        fuente = inspect.getsource(helpers)
        assert "combo_window" in fuente, (
            "`helpers` sigue usando `settings.COMBO_WINDOW`: el preset no "
            "llega al juego"
        )


class _BusMudo:
    def emit(self, *_a, **_k) -> None:
        pass

    def subscribe(self, *_a, **_k) -> None:
        pass


class TestElBestiarioSeLlena:
    """No se comprueba que `record_kill` funcione: se juega y se mira."""

    @pytest.fixture
    def bestiario_limpio(self, _video):
        from src.framework.entities.bestiary import Bestiary

        Bestiary._instance = None
        yield Bestiary.get_instance()
        Bestiary._instance = None

    def test_el_id_sale_del_tipo_cuando_la_entidad_no_lo_declara(
            self, bestiario_limpio) -> None:
        from src.framework.entities.bestiary import Bestiary
        from src.framework.entities.enemy_walker import EnemyWalker

        assert Bestiary.id_de(EnemyWalker(pygame.Vector2(0, 0))) == "walker"

    def test_las_especies_traen_su_propio_id(self, bestiario_limpio) -> None:
        """Veintiuna especies comparten tres clases base: sin `enemy_id` el
        bestiario contaría a todas como el mismo bicho."""
        from src.framework.entities import entity_factory
        from src.framework.entities.bestiary import Bestiary
        from src.framework.entities.bestiary_registry import SPECIES
        from src.framework.stage.stage_loader import StageLoader

        entity_factory.ensure_registered()
        fabrica = StageLoader._entity_registry["WalkerInsect"]
        bicho = fabrica(pygame.Vector2(0, 0))
        assert Bestiary.id_de(bicho) == "WalkerInsect"
        assert "WalkerInsect" in SPECIES

    def test_conoce_las_especies_del_registro(self, bestiario_limpio) -> None:
        from src.framework.entities.bestiary_registry import SPECIES

        ids = {e.enemy_id for e in bestiario_limpio.get_all_entries()}
        faltan = set(SPECIES) - ids
        assert faltan == set(), (
            f"el bestiario no conoce {sorted(faltan)}: matarlas no se anotaría"
        )

    def test_un_enemigo_desconocido_no_se_descarta_en_silencio(
            self, bestiario_limpio) -> None:
        """Antes `record_kill` hacía `if entry:` y salía callado. Un enemigo
        propio de un estudiante no aparecía nunca y no había forma de saberlo.
        """
        bestiario_limpio.record_kill("BichoDeUnEstudiante")
        entrada = bestiario_limpio.get_entry("BichoDeUnEstudiante")
        assert entrada is not None and entrada.kills == 1

    def test_entrar_en_un_escenario_apunta_lo_que_hay(
            self, contexto, bestiario_limpio) -> None:
        from src.framework.entities import entity_factory
        from src.stages.stage0.stage0 import Stage0

        entity_factory.ensure_registered()
        escena = Stage0(contexto)
        contexto.scene_manager.push(escena)
        escena.awake()
        escena.start()
        escena.on_enter()

        vistos = [e.enemy_id for e in bestiario_limpio.get_all_entries()
                  if e.encountered]
        assert len(vistos) >= 5, (
            f"stage0 tiene ocho arquetipos y el bestiario apuntó {vistos}"
        )

    def test_la_escena_lo_guarda_y_lo_carga(self) -> None:
        import inspect

        from src.framework.scenes import stage_scene

        fuente = inspect.getsource(stage_scene)
        assert "_bestiary.save()" in fuente, (
            "`save()` estaba escrito y nadie lo llamaba: el bestiario no "
            "sobrevivía a cerrar el juego"
        )
        assert "_bestiary.load()" in fuente


class TestElMapaDelMundoTieneLosEscenariosDeVerdad:
    def _nodos(self):
        from src.engine.scenes.world_map_scene import construir_nodos

        return construir_nodos()

    def test_hay_un_nodo_por_escenario_descubierto(self, _video) -> None:
        from src.engine.core.stage_registry import discover_stages

        assert len(self._nodos()) == len(discover_stages())

    def test_estan_los_escenarios_de_los_estudiantes(self, _video) -> None:
        """Los once niveles entregados no aparecían en el mapa del mundo."""
        nombres = " ".join(n["name"].lower() for n in self._nodos())
        for trozo in ("soda", "aulas", "lobby", "patio", "hall"):
            assert trozo in nombres, f"falta «{trozo}» en el mapa del mundo"

    def test_cada_nodo_sabe_abrir_algo(self, _video) -> None:
        """Cuatro de los cinco nodos anteriores apuntaban a mapas inexistentes
        y pulsar Enter no hacía nada ni decía nada."""
        from pathlib import Path

        from src.engine.core import settings

        for nodo in self._nodos():
            clase = nodo.get("scene")
            if clase is not None:
                continue
            ruta = Path(settings.ASSETS_DIR / "maps" / nodo["id"]
                        / f"{nodo['id']}.tmx")
            assert ruta.exists(), (
                f"«{nodo['id']}» no tiene ni escena ni mapa: es un nodo muerto"
            )

    def test_se_abre_la_clase_del_escenario_y_no_un_stagescene_generico(
            self, _video) -> None:
        """La clase es la que registra los tipos propios de cada entrega.

        Con un `StageScene` genérico el mapa cargaría y sus enemigos no.
        """
        from src.framework.scenes.stage_scene import StageScene

        propias = [n for n in self._nodos()
                   if n["scene"] is not None and n["scene"] is not StageScene]
        assert len(propias) == len(self._nodos())

    def test_terminar_un_nivel_abre_el_siguiente(self, contexto) -> None:
        """La regla anterior comparaba diccionarios contra cadenas y era
        siempre falsa, así que el mapa no progresaba nunca."""
        from src.engine.scenes.world_map_scene import STAGE_NODES, WorldMapScene

        escena = WorldMapScene(contexto)
        escena._save_data = _PartidaCon([STAGE_NODES[0]["id"]])
        escena._build_nodes()
        assert escena._nodes[0]["completed"] is True
        assert escena._nodes[1]["unlocked"] is True, (
            "terminar el primer nivel no abría el segundo"
        )
        assert escena._nodes[2]["unlocked"] is False, (
            "se abren todos de golpe: el mapa deja de ser una progresión"
        )

    def test_sin_partida_solo_esta_abierto_el_primero(self, contexto) -> None:
        from src.engine.scenes.world_map_scene import WorldMapScene

        escena = WorldMapScene(contexto)
        escena._save_data = None
        escena._build_nodes()
        assert escena._nodes[0]["unlocked"] is True
        assert not any(n["unlocked"] for n in escena._nodes[1:])

    def test_entrar_en_un_nodo_bloqueado_no_hace_nada(self, contexto) -> None:
        from src.engine.scenes.world_map_scene import WorldMapScene

        escena = WorldMapScene(contexto)
        contexto.scene_manager.push(escena)
        escena._save_data = None
        escena._build_nodes()
        assert escena._entrar(escena._nodes[-1]) is False

    def test_entrar_en_el_primero_lo_abre(self, contexto) -> None:
        from src.engine.scenes.world_map_scene import WorldMapScene

        escena = WorldMapScene(contexto)
        contexto.scene_manager.push(escena)
        escena._save_data = None
        escena._build_nodes()
        assert escena._entrar(escena._nodes[0]) is True
        assert type(contexto.scene_manager.current).__name__ != "WorldMapScene"


class _PartidaCon:
    def __init__(self, completados: list[str]) -> None:
        self.completed_stages = completados


class TestLaPantallaDeProgresoNoSeLoInventa:
    """Tres de las cinco barras eran ficción: 100 % fijo o 0 fijo."""

    def test_el_bestiario_no_sale_lleno_de_salida(self, contexto) -> None:
        from src.engine.scenes.progress_scene import ProgressScene
        from src.framework.entities.bestiary import Bestiary

        Bestiary._instance = None
        try:
            datos = ProgressScene(contexto)._get_progress()
            vistas, total = datos["bestiary"]
            assert total > 0
            assert vistas == 0, (
                f"un bestiario recién creado marca {vistas}/{total}: la barra "
                f"decía 21/21 pasara lo que pasara"
            )
        finally:
            Bestiary._instance = None

    def test_los_escenarios_salen_de_la_partida(self, contexto) -> None:
        from src.engine.scenes.progress_scene import ProgressScene

        escena = ProgressScene(contexto)
        escena._escenarios_completados = lambda: ["stage0", "boss_venado"]
        datos = escena._get_progress()
        assert datos["stage"][0] == 2, "la barra de escenarios estaba fija en 0"
        assert datos["boss"][0] == 1
