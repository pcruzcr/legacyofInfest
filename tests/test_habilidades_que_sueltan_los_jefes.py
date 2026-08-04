"""Los jefes sueltan habilidades, y el motor puede exigirlas — AUD-238.

El hueco (GAP-029, conexión 4 de 4, la última)
=============================================
`skill_double_jump`, `skill_dash` y `skill_parry` llevaban en el catálogo de
`engine.core.inventory` desde el principio, con `slot="skill"` y su
`has_skill()` para consultarlas. Medido: **nadie las concedía y nadie las
consultaba**. El doble salto lo gobierna `settings.PLAYER_AIR_JUMPS` y el dash
`_can_dash`, los dos disponibles desde el primer fotograma del primer nivel.

Eran tres entradas de catálogo que no significaban nada.

La decisión que manda sobre este lote
-------------------------------------
La invariante 2 de `CLAUDE.md` dice que **las 26 clases de escenario existentes
deben seguir funcionando sin tocar una línea**. Condicionar el doble salto sin
más convertiría en imposible cualquier salto que un estudiante diseñara
contando con él: un nivel entregado, corregido y aprobado dejaría de poder
completarse. Eso no es cerrar un hueco, es romper veintiséis entregas.

Así que el lote se parte en dos mitades con riesgos distintos:

* **Soltar la habilidad es aditivo.** Un jefe deja un recogible más en el
  suelo. Ningún nivel existente cambia.
* **Exigirla nace apagada.** `settings.PLAYER_SKILLS_REQUIRE_UNLOCK = False`
  por defecto: `_can_jump` y `_can_dash` se comportan exactamente como hoy. Un
  escenario nuevo que quiera progresión la enciende y entonces —y sólo
  entonces— el inventario decide.

Las pruebas de `TestConElCandadoApagadoNadaCambia` son el control de esa
promesa, y son las que no pueden ponerse en rojo nunca.
"""
from __future__ import annotations

import types
from unittest.mock import MagicMock

import pygame
import pytest

from src.engine.core import inventory as inv_mod
from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.core.inventory import get_inventory
from src.framework.scenes.stage_parts.senales import SenalesDeEscenario
from src.framework.stage.interactable_system import InteractableSystem

DT = 1.0 / 60.0


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


@pytest.fixture(autouse=True)
def _inventario_aislado(tmp_path, monkeypatch):
    monkeypatch.setattr(inv_mod, "_INVENTORY_PATH", tmp_path / "inventory.json")
    inv = get_inventory()
    inv._items.clear()
    inv._equipped.clear()
    yield inv
    inv._items.clear()
    inv._equipped.clear()


def _escena():
    """La escena mínima que `SenalesDeEscenario` necesita para suscribirse."""
    bus = EventBus()
    interactables = InteractableSystem(bus=bus)

    escena = MagicMock()
    escena.context = types.SimpleNamespace(event_bus=bus, save_manager=None)
    escena.audio = None
    escena._interactables = interactables
    escena._vfx_handlers = {}
    escena._sfx_handlers = {}
    escena._particle_system.get_emitter.return_value.emit = MagicMock()
    escena._damage_numbers.add = MagicMock()
    escena._camera.offset = MagicMock()
    escena._camera.apply_shake = MagicMock()
    escena._post_processing.flash = MagicMock()
    escena._post_processing.set_damage_vignette = MagicMock()
    escena._post_processing.set_bloom = MagicMock()
    escena._BOTIN_TAM = SenalesDeEscenario._BOTIN_TAM
    escena._soltar_botin = SenalesDeEscenario._soltar_botin.__get__(escena)
    escena._make_sfx_handler = SenalesDeEscenario._make_sfx_handler.__get__(escena)
    escena._play_sfx_named = SenalesDeEscenario._play_sfx_named.__get__(escena)
    escena._play_sfx_spatial = SenalesDeEscenario._play_sfx_spatial.__get__(escena)

    SenalesDeEscenario._subscribe_event_handlers(escena)
    return escena, interactables, bus


def _muere(bus, entity_id: str, skill: str = "", pos=(100.0, 200.0)) -> None:
    bus.emit(
        Events.ENEMY_DIED, entity_id=entity_id, position=pos, skill_drop=skill,
    )
    bus.dispatch()


class TestElJefeSueltaLaHabilidad:
    def test_declara_su_botin_de_habilidad(self) -> None:
        """`BossBase.skill_drop` existe y por defecto no suelta nada.

        Vacío por defecto a propósito: los cuatro jefes del repositorio y los
        que escriban los estudiantes siguen comportándose igual mientras nadie
        lo rellene.
        """
        from src.framework.entities.boss_base import BossBase

        assert BossBase.skill_drop == ""

    def test_la_muerte_lleva_la_habilidad_en_el_evento(self) -> None:
        """`_die()` la publica; sin eso la escena no sabría qué conceder."""
        import inspect

        from src.framework.entities.enemy_base import EnemyBase
        fuente = inspect.getsource(EnemyBase._die)
        assert "skill_drop" in fuente

    def test_al_morir_deja_la_habilidad_en_el_suelo(self) -> None:
        _, interactables, bus = _escena()

        _muere(bus, "BossVenado_1", skill="skill_dash")

        sueltos = [r.item_id for r in interactables.recogibles]
        assert "skill_dash" in sueltos, (
            "el jefe murió y la habilidad no apareció: las tres entradas de "
            "`skill_*` del catálogo seguían sin que nadie las concediera"
        )

    def test_tambien_deja_las_monedas(self) -> None:
        """La habilidad no puede sustituir al botín normal del jefe."""
        _, interactables, bus = _escena()

        _muere(bus, "BossVenado_1", skill="skill_dash")

        sueltos = [r.item_id for r in interactables.recogibles]
        assert "coin" in sueltos and "skill_dash" in sueltos

    def test_un_enemigo_normal_no_suelta_habilidades(self) -> None:
        _, interactables, bus = _escena()

        _muere(bus, "EnemyWalker_1")

        assert [r.item_id for r in interactables.recogibles] == ["coin"]

    def test_recogerla_la_mete_en_el_inventario(self, _inventario_aislado) -> None:
        inv = _inventario_aislado
        _, interactables, bus = _escena()
        _muere(bus, "BossVenado_1", skill="skill_dash", pos=(100.0, 200.0))

        interactables.update(DT, pygame.Rect(80, 180, 40, 48))
        bus.dispatch()

        assert inv.has_skill("skill_dash")

    def test_una_habilidad_inventada_no_entra(self) -> None:
        """Un jefe de una entrega con un `skill_drop` que no existe."""
        _, interactables, bus = _escena()

        _muere(bus, "BossDeUnaEntrega_1", skill="skill_volar")

        sueltos = [r.item_id for r in interactables.recogibles]
        assert "skill_volar" not in sueltos, (
            "se dejó en el suelo un objeto que `collect()` rechazaría: el "
            "jugador lo cogería y no pasaría nada"
        )


class TestConElCandadoApagadoNadaCambia:
    """El control que protege las 26 entregas. No puede ponerse en rojo.

    Con `PLAYER_SKILLS_REQUIRE_UNLOCK = False` —el valor por defecto— el
    inventario **no se consulta**: un jugador sin ninguna habilidad salta y
    corre exactamente igual que antes de AUD-238.
    """

    def _jugador(self):
        from src.framework.entities.player import Player

        jugador = Player(pygame.Vector2(100, 100))
        jugador.is_grounded = False
        jugador._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
        jugador._air_jumps_used = 0
        return jugador

    def test_el_valor_por_defecto_es_apagado(self) -> None:
        assert settings.PLAYER_SKILLS_REQUIRE_UNLOCK is False, (
            "encenderlo por defecto convierte en imposibles los saltos que "
            "las entregas diseñaron contando con el doble salto"
        )

    def test_sin_habilidad_el_doble_salto_sigue_disponible(
        self, _inventario_aislado,
    ) -> None:
        from src.framework.entities.states.helpers import _can_jump

        jugador = self._jugador()
        assert _can_jump(jugador) is True

    def test_sin_habilidad_el_dash_sigue_disponible(
        self, _inventario_aislado,
    ) -> None:
        from src.framework.entities.states.helpers import _can_dash

        jugador = self._jugador()
        jugador.is_grounded = True
        jugador._dash_cooldown = 0.0
        assert _can_dash(jugador, MagicMock()) is True


class TestElCandadoNoDejaElJuegoSinSalida:
    """La trampa que este lote no puede dejar montada.

    Con el candado encendido, una habilidad que **ningún jefe suelta** es una
    habilidad imposible de conseguir. Si el dash está condicionado y nadie lo
    concede, el jugador no lo tendrá nunca: no es progresión, es una mecánica
    borrada. Las dos mitades tienen que configurarse juntas, y esta prueba lo
    exige en vez de confiar en que alguien lo recuerde.
    """

    #: Las que `helpers._can_jump` / `_can_dash` condicionan de verdad.
    CONDICIONADAS = ("skill_double_jump", "skill_dash")

    def _jefes(self) -> list[type]:
        import importlib
        import pathlib

        from src.framework.entities.boss_base import BossBase

        # `discover_stages()` **no** llega a todos los jefes: registra
        # escenarios, y `BossVenado` vive en un módulo que sólo se importa
        # cuando su escena se carga. Contarlos por el árbol de ficheros es lo
        # que hace que esta prueba vea el catálogo entero y no el trozo que
        # otra prueba dejó importado antes — el mismo problema que AUD-144
        # arregló en la guía del motor.
        raiz = pathlib.Path(__file__).resolve().parent.parent
        for ruta in sorted((raiz / "src" / "stages").glob("*/boss_*.py")):
            if ruta.stem.endswith("_scene"):
                continue
            importlib.import_module(
                f"src.stages.{ruta.parent.name}.{ruta.stem}",
            )

        def _descendientes(cls):
            for sub in cls.__subclasses__():
                yield sub
                yield from _descendientes(sub)

        return list(_descendientes(BossBase))

    def test_hay_un_jefe_para_cada_habilidad_condicionada(self) -> None:
        sueltan = {getattr(j, "skill_drop", "") for j in self._jefes()}
        faltan = [s for s in self.CONDICIONADAS if s not in sueltan]

        assert not faltan, (
            f"{faltan} se pueden condicionar y ningún jefe las suelta: con "
            "PLAYER_SKILLS_REQUIRE_UNLOCK encendido serían inalcanzables"
        )

    def test_lo_que_sueltan_los_jefes_existe_en_el_catalogo(self) -> None:
        from src.engine.core.inventory import _ITEM_DEFS

        inventados = sorted({
            s for j in self._jefes()
            if (s := getattr(j, "skill_drop", "")) and s not in _ITEM_DEFS
        })
        assert not inventados, (
            f"jefes que sueltan objetos que no existen: {inventados}"
        )


class TestConElCandadoEncendidoElInventarioDecide:
    """Lo que un escenario nuevo puede pedir si lo enciende a propósito."""

    @pytest.fixture(autouse=True)
    def _con_candado(self, monkeypatch):
        monkeypatch.setattr(settings, "PLAYER_SKILLS_REQUIRE_UNLOCK", True)

    def _jugador_en_el_aire(self):
        from src.framework.entities.player import Player

        jugador = Player(pygame.Vector2(100, 100))
        jugador.is_grounded = False
        jugador._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
        jugador._air_jumps_used = 0
        return jugador

    def test_sin_la_habilidad_no_hay_doble_salto(self, _inventario_aislado) -> None:
        from src.framework.entities.states.helpers import _can_jump

        assert _can_jump(self._jugador_en_el_aire()) is False

    def test_con_la_habilidad_si(self, _inventario_aislado) -> None:
        from src.framework.entities.states.helpers import _can_jump

        _inventario_aislado.collect("skill_double_jump")
        assert _can_jump(self._jugador_en_el_aire()) is True

    def test_el_salto_desde_el_suelo_nunca_se_bloquea(
        self, _inventario_aislado,
    ) -> None:
        """Sin habilidad se pierde el salto **doble**, no el de andar.

        Bloquear el salto normal dejaría al jugador incapaz de subir un
        escalón, que no es progresión sino un juego roto.
        """
        from src.framework.entities.states.helpers import _can_jump

        jugador = self._jugador_en_el_aire()
        jugador.is_grounded = True
        assert _can_jump(jugador) is True

    def test_el_coyote_tampoco_se_bloquea(self, _inventario_aislado) -> None:
        """Los fotogramas de gracia al salir de una plataforma son el salto
        normal llegando tarde, no un salto aéreo."""
        from src.framework.entities.states.helpers import _can_jump

        jugador = self._jugador_en_el_aire()
        jugador._coyote_counter = 0
        assert _can_jump(jugador) is True

    def test_sin_la_habilidad_no_hay_dash(self, _inventario_aislado) -> None:
        from src.framework.entities.player import Player
        from src.framework.entities.states.helpers import _can_dash
        jugador = Player(pygame.Vector2(100, 100))
        jugador.is_grounded = True
        jugador._dash_cooldown = 0.0
        assert _can_dash(jugador, MagicMock()) is False

    def test_con_la_habilidad_el_dash_vuelve(self, _inventario_aislado) -> None:
        from src.framework.entities.player import Player
        from src.framework.entities.states.helpers import _can_dash
        _inventario_aislado.collect("skill_dash")
        jugador = Player(pygame.Vector2(100, 100))
        jugador.is_grounded = True
        jugador._dash_cooldown = 0.0
        assert _can_dash(jugador, MagicMock()) is True
