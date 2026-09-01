"""
F5.14 / AUD-109 — lianas, tirolesas, y el quinto estado huérfano del mes.

De qué salió esto
=================
La pregunta era si el motor permite crear **obstáculos, lianas y tirolesas**. Se
comprobó buscando sobre todo `src/`:

* **Obstáculos: sí.** Dieciocho tipos de objeto en Tiled los cubren —`Solid`,
  `Platform`, `HazardZone`, `DeathPit`, `LaserZone`, `RhythmBlock`,
  `SinkingPlatform`, `MovingPlatform`— sin escribir código.
* **Lianas y tirolesas: no había NADA.** Ni `Ladder`, ni `Rope`, ni `Zipline`,
  ni `Climb`, ni un estado que suspendiera la gravedad. Cero coincidencias.

Y no se podían improvisar. Apilar `Solid` estrechos para simular una cuerda deja
al jugador **al lado** de la columna, no dentro: para subir tiene que saltar, que
es exactamente lo que una liana existe para evitar.

Y de paso, el quinto huérfano
------------------------------
Buscando estados alcanzables apareció `AirChaseState`: sprite propio, velocidad
de animación propia, valor en el enum, lógica completa de lanzamiento aéreo, y
**cero transiciones de entrada**. El quinto sistema de esta forma en un mes.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.ecs import World
from src.framework.ecs import systems as S
from src.framework.ecs.components import Liana, Tirolesa

FRAME = 1.0 / 60.0


@pytest.fixture(scope="module", autouse=True)
def _pg():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 224))
    yield


@pytest.fixture
def jugador():
    from src.framework.entities.player import Player
    return Player(pygame.Vector2(100, 100))


# ══════════════════════════════════════════════════════════════
# Lianas
# ══════════════════════════════════════════════════════════════


class TestLianas:
    def test_se_detecta_una_liana_al_alcance(self):
        m = World()
        m.crear(Liana(rect=pygame.Rect(100, 0, 4, 200)))
        assert S.liana_alcanzable(m, pygame.Rect(96, 100, 20, 32)) is not None

    def test_el_margen_de_agarre_es_generoso(self):
        """Agarrarse no puede ser un acto de puntería.

        Con la anchura exacta de la cuerda —cuatro píxeles— fallar por uno se
        lee como que el juego no responde, no como que el jugador falló.
        """
        m = World()
        m.crear(Liana(rect=pygame.Rect(100, 0, 4, 200), ancho_de_agarre=10))
        # A 8 px del borde de la cuerda: fuera de ella, dentro del margen.
        assert S.liana_alcanzable(m, pygame.Rect(88, 100, 8, 32)) is not None

    def test_lejos_no_se_agarra(self):
        m = World()
        m.crear(Liana(rect=pygame.Rect(100, 0, 4, 200), ancho_de_agarre=10))
        assert S.liana_alcanzable(m, pygame.Rect(500, 100, 20, 32)) is None

    def test_trepar_suspende_la_gravedad(self, jugador):
        """Es lo que ningún montaje con `Solid` podía dar."""
        from src.framework.entities.states import TrepandoState

        liana = Liana(rect=pygame.Rect(100, 0, 4, 300))
        jugador._change_state_instance(TrepandoState(liana))
        y0 = jugador.position.y
        for _ in range(30):
            jugador._state_instance.update(jugador, FRAME, None)
        assert jugador.velocity.y == pytest.approx(0.0), (
            "sin entrada, el jugador debería quedarse quieto en la cuerda"
        )
        assert jugador.position.y == pytest.approx(y0)

    def test_al_agarrarse_se_centra_en_la_cuerda(self, jugador):
        """Si no, se trepa en diagonal y el sprite se sale de la liana."""
        from src.framework.entities.states import TrepandoState

        liana = Liana(rect=pygame.Rect(200, 0, 4, 300))
        jugador._change_state_instance(TrepandoState(liana))
        assert jugador.rect.centerx == liana.rect.centerx

    def test_soltarse_saltando_da_impulso_horizontal(self, jugador):
        """Sin impulso, la liana no sirve para cruzar nada — que es para lo que está."""
        from src.framework.entities.states import JumpingState, TrepandoState

        class Mando:
            def is_action_held(self, a):
                from src.engine.input.action_map import Action
                return a == Action.MOVE_RIGHT

            def is_action_pressed(self, a):
                from src.engine.input.action_map import Action
                return a == Action.JUMP

            def is_action_just_pressed(self, a):
                return self.is_action_pressed(a)

            # AUD-407 — `_InputSnapshot` (base.py) lee el buffer de AUD-373
            # para todas las acciones desde que existe; un doble que no lo
            # ofrezca muere con AttributeError antes de llegar a la lógica
            # que este test quiere medir.
            def pulsada_en_buffer(self, a):
                return False

        liana = Liana(rect=pygame.Rect(100, 0, 4, 300))
        jugador._change_state_instance(TrepandoState(liana))
        jugador._state_instance._t = 0.5     # ya lleva un rato agarrado
        jugador._state_instance.update(jugador, FRAME, Mando())
        assert isinstance(jugador._state_instance, JumpingState)
        assert jugador.velocity.x > 0.0
        assert jugador.velocity.y < 0.0


# ══════════════════════════════════════════════════════════════
# Tirolesas
# ══════════════════════════════════════════════════════════════


class TestTirolesas:
    def _cable(self) -> Tirolesa:
        return Tirolesa(
            origen=pygame.Vector2(100, 100), destino=pygame.Vector2(300, 200),
        )

    def test_el_punto_mas_cercano_se_recorta_al_segmento(self):
        """Sin recortar, engancharías a un cable que no está ahí.

        Es de los fallos que más desconciertan, porque el cable **se ve** lejos
        y aun así te agarra.
        """
        c = self._cable()
        lejos = c.punto_mas_cercano(pygame.Vector2(-500, 100))
        assert lejos == c.origen
        pasado = c.punto_mas_cercano(pygame.Vector2(5000, 200))
        assert pasado == c.destino

    def test_el_progreso_va_de_cero_a_uno(self):
        c = self._cable()
        assert c.progreso(c.origen) == pytest.approx(0.0)
        assert c.progreso(c.destino) == pytest.approx(1.0)
        assert 0.4 < c.progreso((c.origen + c.destino) / 2) < 0.6

    def test_se_engancha_cerca_del_cable(self):
        m = World()
        m.crear(self._cable())
        assert S.tirolesa_alcanzable(m, pygame.Rect(100, 95, 16, 16)) is not None

    def test_no_se_engancha_bajo_la_caja_envolvente(self):
        """Un cable diagonal tiene una caja enorme; el cable no está en toda ella."""
        m = World()
        m.crear(self._cable())
        assert S.tirolesa_alcanzable(m, pygame.Rect(290, 100, 16, 16)) is None

    def test_deslizarse_avanza_por_el_cable(self, jugador):
        from src.framework.entities.states import TirolesaState

        cable = self._cable()
        jugador._change_state_instance(TirolesaState(cable))
        p0 = pygame.Vector2(jugador.position)
        for _ in range(20):
            jugador._state_instance.update(jugador, FRAME, None)
        avance = pygame.Vector2(jugador.position) - p0
        assert avance.x > 0.0 and avance.y > 0.0, (
            f"no siguió la pendiente del cable: {avance}"
        )

    def test_al_llegar_al_final_conserva_el_impulso(self, jugador):
        """Frenar en seco desperdicia toda la velocidad que el tramo acumuló."""
        from src.framework.entities.states import FallingState, TirolesaState

        cable = Tirolesa(
            origen=pygame.Vector2(100, 100), destino=pygame.Vector2(140, 120),
        )
        jugador._change_state_instance(TirolesaState(cable))
        for _ in range(120):
            jugador._state_instance.update(jugador, FRAME, None)
            if isinstance(jugador._state_instance, FallingState):
                break
        else:
            pytest.fail("nunca llegó al final del cable")
        assert jugador.velocity.length() > 10.0, "frenó en seco al soltarse"


# ══════════════════════════════════════════════════════════════
# El TMX
# ══════════════════════════════════════════════════════════════


class TestSePuedenDeclararDesdeTiled:
    """Si hay que escribir Python, un estudiante no las va a usar."""

    def _cargar(self, tipo: str, **props):
        from src.framework.stage.stage_loader import StageData, StageLoader

        class Falso:
            x, y, width, height = 100, 50, 8, 200

        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        StageLoader._handle_componente(stage, Falso(), props, tipo)
        return stage.componentes

    def test_vine_produce_una_liana(self):
        grupos = self._cargar("Vine", velocidad=90.0)
        assert grupos and isinstance(grupos[0][0], Liana)
        assert grupos[0][0].velocidad == pytest.approx(90.0)

    def test_zipline_produce_una_tirolesa(self):
        grupos = self._cargar("Zipline", destino_dx=200.0, destino_dy=80.0)
        assert grupos and isinstance(grupos[0][0], Tirolesa)
        cable = grupos[0][0]
        assert cable.destino.x == pytest.approx(300.0)
        assert cable.destino.y == pytest.approx(130.0)

    def test_los_dos_tipos_los_acepta_el_validador(self):
        from src.framework.stage.tmx_diagnostics import BUILTIN_OBJECT_TYPES

        assert "Vine" in BUILTIN_OBJECT_TYPES
        assert "Zipline" in BUILTIN_OBJECT_TYPES


# ══════════════════════════════════════════════════════════════
# AUD-109 — el quinto huérfano
# ══════════════════════════════════════════════════════════════


class TestAirChaseYaSeAlcanza:
    """`AirChaseState` tenía sprite, animación, enum, lógica — y cero entradas."""

    def test_hay_una_transicion_que_entra_en_air_chase(self):
        import ast
        import pathlib

        destinos = set()
        for f in pathlib.Path("src").rglob("*.py"):
            if "__pycache__" in str(f):
                continue
            try:
                arbol = ast.parse(f.read_text(encoding="utf-8-sig", errors="replace"))
            except Exception:
                continue
            for n in ast.walk(arbol):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "_change_state_instance"
                        and n.args and isinstance(n.args[0], ast.Call)
                        and isinstance(n.args[0].func, ast.Name)):
                    destinos.add(n.args[0].func.id)
        assert "AirChaseState" in destinos, (
            "AirChaseState vuelve a ser inalcanzable: tiene sprite, animación y "
            "lógica completa, y nadie puede entrar en él"
        )

    def test_el_primer_golpe_aereo_lanza_al_jugador(self, jugador):
        """La forma del código decía para qué era: `enter` pone velocity.y = -200."""
        from src.framework.entities.states import AerialAttackState, AirChaseState

        jugador.is_grounded = False
        jugador._combo_air_hits = 0
        jugador._change_state_instance(AerialAttackState(short=True))
        jugador._hitbox_consumed = True
        for _ in range(20):
            jugador._state_instance.update(jugador, FRAME, None)
            if isinstance(jugador._state_instance, AirChaseState):
                break
        assert isinstance(jugador._state_instance, AirChaseState), (
            "el primer golpe aéreo no lanzó al jugador"
        )
        assert jugador.velocity.y < 0.0, "lanzar es hacia arriba"

    def test_los_estados_del_jugador_sin_transicion_son_solo_clases_base(self):
        """Un estado concreto sin entrada es un sistema muerto; una base, no.

        Se comprueba explícitamente para que la próxima vez que aparezca un
        huérfano no se pueda justificar diciendo «será una clase base».
        """
        import ast
        import pathlib

        from src.framework.entities import states as S_

        destinos = set()
        for f in pathlib.Path("src").rglob("*.py"):
            if "__pycache__" in str(f):
                continue
            try:
                arbol = ast.parse(f.read_text(encoding="utf-8-sig", errors="replace"))
            except Exception:
                continue
            for n in ast.walk(arbol):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "_change_state_instance"
                        and n.args and isinstance(n.args[0], ast.Call)
                        and isinstance(n.args[0].func, ast.Name)):
                    destinos.add(n.args[0].func.id)

        declarados = {
            n for n in S_.__all__ if n.endswith("State") and n != "PlayerStateBase"
        }
        # Bases legítimas: `AirborneState` la heredan Jumping y Falling, y
        # `_AttackState` los tres ataques. Entrar en ellas directamente no
        # tendría sentido.
        # AUD-DEBUFF: StaggerState y PossessedState son debuffs que se
        # activan vía sistema de efectos (efectos.py) y eventos veneno/
        # golpe pesado, no por vía directa _change_state_instance en el
        # código base — su wiring es vía Player.efectos y trigger manual.
        # Se consideran estados terminales de efecto, no huérfanos.
        bases = {"AirborneState", "_AttackState", "StaggerState", "PossessedState"}
        huerfanos = declarados - destinos - bases
        assert not huerfanos, (
            f"estados escritos a los que no llega ningún camino: {sorted(huerfanos)}"
        )
