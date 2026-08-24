"""AUD-602/603/604/605/606/607 — los cinco defectos del motor que la
campaña de playtesting reportó contra los jefes y el cierre de nivel.

Cada clase corresponde a un punto del informe; el número AUD es el del
arreglo en este repositorio:

* **AUD-602** — la señal de «nivel completado» se re-emitía cada frame
  tras la victoria (1.255 emisiones medidas en un episodio).
* **AUD-603** — el golpe aéreo (y todo ataque especial posterior al corto
  y al largo) conectaba con daño 0.0.
* **AUD-605** — los límites de arena que el motor entrega al jefe eran el
  mapa completo; ahora un `ArenaZone` del TMX declara el cuadrilátero real.
* **AUD-606** — la escala de fase agrandaba el cuerpo pero no las cajas;
  opt-in vía `cajas_siguen_al_cuerpo`, activado en el jefe de referencia.
* **AUD-607** — el tinte de transición pintaba un cuadrado translúcido y
  mutaba la superficie cacheada del sprite; ahora tinte por silueta sobre
  copia.
"""
from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest


@pytest.fixture(scope="module", autouse=True)
def _video() -> None:
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((8, 8))


# ── AUD-602: una sola emisión del cierre ────────────────────────────

class TestElCierreDelNivelDisparaUnaVez:
    def _progresion(self):
        from src.framework.stage.progression_system import ProgressionSystem

        return ProgressionSystem(context=None)

    def test_tras_el_agotamiento_solo_hay_un_true(self) -> None:
        p = self._progresion()
        p._stage_complete = True
        p._complete_timer = 2.9

        resultados = [p.update_complete_timer(1.0) for _ in range(20)]

        assert sum(1 for r in resultados if r) == 1, (
            "el cierre del nivel se anunció más de una vez: la escena "
            "re-emite STAGE_COMPLETE por cada True"
        )
        # Y a partir de ahí, nunca más — ni siquiera con dt grande.
        for _ in range(50):
            assert p.update_complete_timer(10.0) is False

    def test_el_reset_devuelve_el_candado_a_cero(self) -> None:
        p = self._progresion()
        p._stage_complete = True
        p._complete_timer = 0.0
        assert p.update_complete_timer(0.016) is True
        assert p.update_complete_timer(0.016) is False

        p.reset()

        p._stage_complete = True
        p._complete_timer = 0.0
        assert p.update_complete_timer(0.016) is True


# ── AUD-603: los ataques especiales hacen daño ──────────────────────

class TestLosAtaquesEspecialesHacenDanio:
    @staticmethod
    def _jugador():
        from src.engine.core.event_bus import EventBus
        from src.framework.entities.player import Player

        return Player(pygame.Vector2(0.0, 0.0), event_bus=EventBus())

    def _danio_en_estado(self, estado, damage_mult=1.0) -> float:
        jugador = self._jugador()
        jugador._state_instance = estado
        jugador._active_hitbox = pygame.Rect(0, 0, 10, 10)
        jugador._damage_mult = damage_mult
        return jugador.current_attack_damage

    def test_el_golpe_aereo_ya_no_es_cero(self) -> None:
        from src.framework.entities.player import PlayerState
        from src.framework.entities.states.airborne import AerialAttackState

        danio = self._danio_en_estado(AerialAttackState())

        assert danio > 0.0, (
            "AERIAL_ATTACK levanta hitbox y consume el golpe, pero "
            f"current_attack_damage devolvió {danio}: mecánica inerte"
        )
        # Misma peso que el corto: comparte caja y sprite.
        corto = self._danio_en_estado(
            SimpleNamespace(state_enum=PlayerState.SHORT_ATTACK))
        assert danio == pytest.approx(corto)

    def test_el_remate_aereo_pesa_como_el_largo(self) -> None:
        from src.framework.entities.player import PlayerState
        from src.framework.entities.states.airborne import AerialSlamState

        slam = self._danio_en_estado(AerialSlamState())
        largo = self._danio_en_estado(
            SimpleNamespace(state_enum=PlayerState.LONG_ATTACK))

        assert slam > 0.0
        assert slam == pytest.approx(largo)

    def test_el_ataque_de_dash_esta_entre_ligero_y_pesado(self) -> None:
        from src.framework.entities.states.attack import DashAttackState

        dash = self._danio_en_estado(DashAttackState())

        assert 0.5 < dash < 1.0

    def test_el_ultimate_por_fin_multiplica(self) -> None:
        """`UltimateState` fijaba `_damage_mult = 3.0`… sobre base 0."""
        from src.framework.entities.player import PlayerState

        danio = self._danio_en_estado(
            SimpleNamespace(state_enum=PlayerState.ULTIMATE),
            damage_mult=3.0,
        )

        assert danio == pytest.approx(3.0)

    def test_la_carga_libera_su_multiplicador(self) -> None:
        from src.framework.entities.player import PlayerState

        danio = self._danio_en_estado(
            SimpleNamespace(state_enum=PlayerState.CHARGE_RELEASE),
            damage_mult=1.5,
        )

        assert danio == pytest.approx(1.5)

    def test_el_agarre_sigue_sin_danir(self) -> None:
        """Un agarre sujeta; no golpea. Que siga en 0 es diseño, no descuido."""
        from src.framework.entities.states.ability import GrabState

        danio = self._danio_en_estado(GrabState())

        assert danio == 0.0


# ── AUD-605: la arena llega del TMX, no del tamaño del mapa ─────────

class TestLaArenaDelJefeVieneDelMapa:
    def test_el_tipo_esta_en_el_catalogo(self) -> None:
        from src.framework.stage.tmx_diagnostics import BUILTIN_OBJECT_TYPES

        assert "ArenaZone" in BUILTIN_OBJECT_TYPES

    def test_el_cargador_acepta_el_rectangulo(self) -> None:
        from src.framework.stage.stage_data import StageData
        from src.framework.stage.stage_objetos import ObjetosDeTiled

        obj = SimpleNamespace(x=2480.0, y=64.0, width=784.0, height=480.0)
        stage = StageData.__new__(StageData)
        stage.zonas_arena = []
        ObjetosDeTiled._handle_zona_arena(stage, obj)

        assert stage.zonas_arena == [
            pygame.Rect(2480, 64, 784, 480)]

    def test_un_punto_no_es_una_arena(self) -> None:
        from src.framework.stage.stage_data import StageData
        from src.framework.stage.stage_objetos import ObjetosDeTiled

        obj = SimpleNamespace(x=100.0, y=100.0, width=0.0, height=32.0)
        stage = StageData.__new__(StageData)
        stage.zonas_arena = []
        ObjetosDeTiled._handle_zona_arena(stage, obj)

        assert stage.zonas_arena == []

    def test_gana_la_zona_que_contiene_al_jefe(self) -> None:
        from src.framework.scenes.stage_scene import _arena_del_jefe
        from src.framework.stage.stage_data import StageData

        stage = StageData.__new__(StageData)
        stage.map_pixel_size = (3280, 608)
        stage.zonas_arena = [
            pygame.Rect(0, 0, 800, 608),
            pygame.Rect(2480, 0, 784, 608),
        ]
        cuerpo = pygame.Rect(2820, 300, 48, 48)

        assert _arena_del_jefe(stage, cuerpo) == pygame.Rect(
            2480, 0, 784, 608)

    def test_sin_zonas_se_conserva_el_mapa_completo(self) -> None:
        """El comportamiento histórico es el respaldo: los mapas viejos no
        declaran arenas y deben seguir jugándose igual."""
        from src.framework.scenes.stage_scene import _arena_del_jefe
        from src.framework.stage.stage_data import StageData

        stage = StageData.__new__(StageData)
        stage.map_pixel_size = (3280, 608)
        stage.zonas_arena = []
        cuerpo = pygame.Rect(2820, 300, 48, 48)

        assert _arena_del_jefe(stage, cuerpo) == pygame.Rect(
            0, 0, 3280, 608)


# ── AUD-606: la escala alcanza a las cajas ──────────────────────────

def _clase_jefe(base, sigue: bool):
    class Jefe(base):
        cajas_siguen_al_cuerpo = sigue

        def _get_animation_key(self) -> str:
            return "drift"

        def _patrol_behavior(self, dt: float) -> None:
            pass

        def _alert_behavior(self, dt: float) -> None:
            pass

        def _build_hitbox(self) -> pygame.Rect:
            return pygame.Rect(6, 4, 36, 44)

        def _build_hurtbox(self) -> pygame.Rect:
            return pygame.Rect(9, 4, 30, 40)

    return Jefe


@pytest.fixture
def event_bus():
    from src.engine.core.event_bus import EventBus

    return EventBus()


class TestLasCajasSiguenAlCuerpoEscalado:
    def _jefe(self, event_bus, sigue: bool):
        from src.framework.entities.boss_base import BossBase, BossPhase

        cls = _clase_jefe(BossBase, sigue)
        jefe = cls(pygame.Vector2(100, 100), max_health=12.0)
        jefe.set_event_bus(event_bus)
        jefe.set_phases([
            BossPhase(phase_index=0, health_threshold=1.0,
                      attack_patterns=[]),
            BossPhase(phase_index=1, health_threshold=0.5,
                      attack_patterns=[], escala=2.0),
        ])
        return jefe

    def test_con_la_bandera_las_cajas_escalan_con_el_cuerpo(
        self, event_bus,
    ) -> None:
        jefe = self._jefe(event_bus, sigue=True)
        base_w = jefe.rect.width
        local_hurt = jefe._build_hurtbox()
        local_hit = jefe._build_hitbox()

        jefe._finish_phase_transition()   # escala ×2 declarada en la fase
        jefe._update_rects()

        assert jefe.rect.width == base_w * 2   # el cuerpo creció…
        s = jefe._escala_viva()
        assert s == pytest.approx(2.0)
        # …y las cajas con él, escalado puro (offset y tamaño).
        assert jefe.hurtbox.width == round(local_hurt.width * s)
        assert jefe.hitbox.width == round(local_hit.width * s)

    def test_los_margenes_de_la_caja_se_mantienen_proporcionales(
        self, event_bus,
    ) -> None:
        """El dibujo centra el sprite en el rect vivo, así que el pixel
        `p` del sprite base cae en `p * escala`: los márgenes de la caja
        tienen que crecer igual que la silueta."""
        jefe = self._jefe(event_bus, sigue=True)
        base_h = jefe.rect.height
        local = jefe._build_hurtbox()

        jefe._finish_phase_transition()
        jefe._update_rects()

        s = 2.0
        assert jefe.hurtbox.x - jefe.rect.x == round(local.x * s)
        margen_inferior_local = base_h - (local.y + local.height)
        assert jefe.rect.bottom - jefe.hurtbox.bottom == \
            round(margen_inferior_local * s)

    def test_sin_la_bandera_nada_cambia_para_los_que_compensan_a_mano(
        self, event_bus,
    ) -> None:
        """`boss_paburu` deriva sus cajas del rect vivo: escalarlas otra vez
        sería doble escala. El comportamiento por defecto los preserva."""
        jefe = self._jefe(event_bus, sigue=False)
        jefe._finish_phase_transition()
        jefe._update_rects()

        local = jefe._build_hurtbox()
        # El gancho no tocó nada: la caja mundial es el local tal cual
        # sumado a la posición, aunque el cuerpo haya crecido.
        assert jefe.hurtbox.width == local.width
        assert jefe.hurtbox.x == int(jefe.position.x) + local.x

    def test_los_puntos_debiles_se_espejan_con_el_facing(
        self, event_bus,
    ) -> None:
        from src.framework.entities.boss_kit import WeakPoint

        jefe = self._jefe(event_bus, sigue=True)
        punto = WeakPoint(offset=(30, 10), size=(8, 8))

        derecha = punto.rect_for(jefe.rect)
        jefe.facing_direction = -1
        izquierda = punto.rect_for(jefe.rect, facing=-1)

        assert derecha.x == jefe.rect.x + 30
        # Espejo dentro del cuerpo: ancho − offset − tamaño.
        assert izquierda.x == jefe.rect.x + jefe.rect.width - 30 - 8

    def test_el_jefe_de_referencia_declara_la_bandera(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado

        assert BossVenado.cajas_siguen_al_cuerpo is True


# ── AUD-607: tinte por silueta, cache intacta ───────────────────────

class TestElTinteDeTransicionEsPorSilueta:
    def _jefe_con_sprite(self, event_bus):
        from src.framework.entities.boss_base import BossBase

        cls = _clase_jefe(BossBase, sigue=False)
        jefe = cls(pygame.Vector2(0, 0), max_health=12.0)
        jefe.set_event_bus(event_bus)

        lienzo = pygame.Surface((16, 16), pygame.SRCALPHA)
        lienzo.fill((255, 0, 0, 255))                       # silueta entera…
        lienzo.fill((0, 0, 0, 0), (0, 0, 4, 4))             # …con esquina hueca
        jefe._sprite_frames["drift"] = [lienzo]
        return jefe, lienzo

    def test_draw_no_muta_la_cache(self, event_bus) -> None:
        jefe, lienzo = self._jefe_con_sprite(event_bus)
        antes = tuple(lienzo.get_at((8, 8)))

        destino = pygame.Surface((32, 32))
        jefe.is_transitioning = True
        jefe.draw(destino, pygame.Vector2(0, 0))

        despues = tuple(lienzo.get_at((8, 8)))
        assert despues == antes, (
            "draw mutó la superficie cacheada: el tinte se acumula en la "
            "cache y sobrevive al final de la transición"
        )

    def test_el_tinte_respeta_la_silueta(self, event_bus) -> None:
        jefe, _lienzo = self._jefe_con_sprite(event_bus)
        destino = pygame.Surface((32, 32))
        destino.fill((0, 0, 0))

        jefe.is_transitioning = True
        jefe.draw(destino, pygame.Vector2(0, 0))

        # El sprite (16×16) se pinta al fondo del rect: cuerpo y hueco se
        # muestrean DENTRO de la zona que ocupa el sprite.
        cuerpo = destino.get_at((8, 20))
        assert cuerpo.r >= 200 and cuerpo.g >= 80
        # La esquina transparente del lienzo sigue siendo fondo: sin cuadrado.
        hueco = destino.get_at((1, 13))
        assert hueco.r < 50 and hueco.g < 50
