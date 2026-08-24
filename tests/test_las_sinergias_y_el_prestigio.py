"""AUD-608/609 — sinergias del árbol de habilidades y prestigio.

**AUD-608 — Sinergias.** Dos primas que se CONSIGUEN (no se compran) al
llevar dos ramas al tope, cada una con consumidor real en `Player`:

* `berserker` (fuerza 5 + coraza 5) → +20 % de daño por debajo de la
  mitad de vida (`Player.damage_multiplier`).
* `titan` (vitalidad 10 + ímpetu 4) → +0,30 s de i-frames al recibir un
  golpe (`Player.apply_damage`).

**AUD-609 — Prestigio.** `Inventory.reencarnar` reinicia experiencia y
árbol a cambio de +5 % de XP permanente; `ExperienceSystem.grant` aplica
el multiplicador.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((8, 8))


@pytest.fixture
def arbol():
    from src.engine.core.skill_tree import ArbolDeHabilidades

    ArbolDeHabilidades._reset_instance()
    a = ArbolDeHabilidades.get_instance()
    yield a
    ArbolDeHabilidades._reset_instance()


def _rangos(arbol, **kwargs) -> None:
    """Fija rangos directamente: la sinergia se CONSIGUE, no se compra."""
    arbol._rangos = dict(kwargs)


# ── AUD-608: la consulta ────────────────────────────────────────────

class TestLaConsultaDeSinergias:
    def test_sin_rangos_no_hay_nada_conseguido(self, arbol) -> None:
        assert arbol.sinergias_activas() == []
        assert not arbol.sinergia_activa("berserker")

    def test_berserker_exige_las_dos_ramas_al_tope(self, arbol) -> None:
        _rangos(arbol, fuerza=5)
        assert not arbol.sinergia_activa("berserker")
        _rangos(arbol, fuerza=5, coraza=4)
        assert not arbol.sinergia_activa("berserker")
        _rangos(arbol, fuerza=5, coraza=5)
        assert arbol.sinergia_activa("berserker")

    def test_titan_exige_vitalidad_completa_e_impetu_completo(
        self, arbol,
    ) -> None:
        _rangos(arbol, vitalidad=10)
        assert not arbol.sinergia_activa("titan")
        _rangos(arbol, vitalidad=10, impetu=4)
        assert arbol.sinergia_activa("titan")

    def test_perder_un_rango_pierde_la_sinergia(self, arbol) -> None:
        """Se consulta en caliente: cargar una partida con menos rangos
        debe desactivarla, no recordar una cache."""
        _rangos(arbol, fuerza=5, coraza=5)
        assert arbol.sinergia_activa("berserker")
        arbol._rangos["coraza"] = 3
        assert not arbol.sinergia_activa("berserker")

    def test_una_sinergia_desconocida_no_explota(self, arbol) -> None:
        assert not arbol.sinergia_activa("no_existe")


# ── AUD-608: los consumidores en el jugador ─────────────────────────

@pytest.fixture
def jugador(_video):
    from src.engine.core.event_bus import EventBus
    from src.framework.entities.player import Player

    p = Player(pygame.Vector2(0.0, 0.0), event_bus=EventBus())
    yield p


class TestBerserkerEnElJugador:
    def test_por_encima_de_mitad_de_vida_no_suma_nada(
        self, jugador, arbol,
    ) -> None:
        _rangos(arbol, fuerza=5, coraza=5)
        jugador._health = jugador.max_health
        sin = 1.0 + jugador._bonus_damage + jugador._bonus_arbol_dano
        # Con vida llena, aunque la sinergia esté conseguida, no suma:
        assert jugador.damage_multiplier == pytest.approx(sin)

    def test_por_debajo_de_mitad_de_vida_suma_veinte_por_ciento(
        self, jugador, arbol,
    ) -> None:
        _rangos(arbol, fuerza=5, coraza=5)
        jugador._health = jugador.max_health / 2.0 - 1.0
        sin = 1.0 + jugador._bonus_damage + jugador._bonus_arbol_dano
        assert jugador.damage_multiplier == pytest.approx(sin + 0.2)

    def test_sin_la_sinergia_la_vida_baja_no_cambia_nada(
        self, jugador, arbol,
    ) -> None:
        _rangos(arbol, fuerza=5)   # rama incompleta
        jugador._health = 1.0
        sin = 1.0 + jugador._bonus_damage + jugador._bonus_arbol_dano
        assert jugador.damage_multiplier == pytest.approx(sin)


class TestTitanEnElJugador:
    @staticmethod
    def _i_frames(jugador) -> float:
        jugador._invincibility_timer = 0.0
        jugador.apply_damage(1.0, (0.0, 0.0))
        return jugador._invincibility_timer

    def test_sin_sinergia_los_i_frames_son_los_de_siempre(
        self, jugador, arbol,
    ) -> None:
        _rangos(arbol, vitalidad=10)
        base = self._i_frames(jugador)
        from src.engine.core.difficulty import get_config

        assert base == pytest.approx(get_config().invincibility_duration)

    def test_con_sinergia_estiran_tres_decimas(self, jugador, arbol) -> None:
        from src.engine.core.difficulty import get_config

        _rangos(arbol, vitalidad=10, impetu=4)
        esperado = get_config().invincibility_duration + 0.3
        assert self._i_frames(jugador) == pytest.approx(esperado)


# ── AUD-609: prestigio ──────────────────────────────────────────────

@pytest.fixture
def inventario():
    from src.engine.core.inventory import Inventory

    Inventory._reset_instance()
    inv = Inventory()
    inv._items.clear()
    inv._equipped.clear()
    inv.prestigio = 0
    yield inv
    inv.prestigio = 0
    inv._items.clear()
    inv._equipped.clear()
    Inventory._reset_instance()


@pytest.fixture
def experiencia():
    from src.engine.core.experience import ExperienceSystem

    ExperienceSystem._reset_instance()
    exp = ExperienceSystem.get_instance()
    yield exp
    ExperienceSystem._reset_instance()


class TestElPrestigio:
    def test_sin_prestigio_el_multiplicador_es_identidad(
        self, inventario,
    ) -> None:
        assert inventario.get_xp_multiplier() == pytest.approx(1.0)

    def test_reencarnar_exige_el_nivel_minimo(
        self, inventario, experiencia, arbol,
    ) -> None:
        experiencia.grant(100)   # nivel 2, lejos del mínimo
        assert not inventario.reencarnar(experiencia, arbol)
        assert inventario.prestigio == 0
        assert experiencia.exp == 100

    def test_reencarnar_gana_un_punto_y_resetea_progreso(
        self, inventario, experiencia, arbol,
    ) -> None:
        from src.engine.core.experience import exp_para_nivel

        experiencia.grant(exp_para_nivel(
            inventario.NIVEL_DE_REENCARNACION) + 10)
        arbol._rangos = {"fuerza": 3}

        assert inventario.reencarnar(experiencia, arbol)
        assert inventario.prestigio == 1
        assert experiencia.exp == 0 and experiencia.puntos == 0
        assert arbol.to_dict() == {}
        assert inventario.get_xp_multiplier() == pytest.approx(1.05)

    def test_reencarnar_no_toca_objetos_ni_monedas(
        self, inventario, experiencia, arbol,
    ) -> None:
        from src.engine.core.experience import exp_para_nivel

        inventario.add_coins(500)
        inventario.collect("heart_vessel")
        experiencia.grant(exp_para_nivel(
            inventario.NIVEL_DE_REENCARNACION) + 10)

        inventario.reencarnar(experiencia, arbol)

        assert inventario.coins == 500
        assert inventario.has("heart_vessel")

    def test_el_multiplicador_llega_al_grant(
        self, inventario, experiencia,
    ) -> None:
        inventario.prestigio = 4   # +20 %
        experiencia.grant(50)
        assert experiencia.exp == 60

    def test_el_prestigio_sobrevive_al_guardado(
        self, inventario,
    ) -> None:
        inventario.prestigio = 2
        inventario.save()

        # Misma ruta de siempre: recargar desde disco.
        from src.engine.core import inventory as modulo_inventario

        modulo_inventario._INVENTORY_PATH.write_bytes(
            modulo_inventario._INVENTORY_PATH.read_bytes())
        inventario.load()
        assert inventario.prestigio == 2

    def test_un_fichero_viejo_sin_clave_deja_cero(
        self, inventario,
    ) -> None:
        import orjson

        from src.engine.core import inventory as modulo_inventario

        viejo = {"items": {"coin": 7}, "equipped": {}}
        modulo_inventario._INVENTORY_PATH.parent.mkdir(
            parents=True, exist_ok=True)
        modulo_inventario._INVENTORY_PATH.write_bytes(orjson.dumps(viejo))
        inventario.load()
        assert inventario.prestigio == 0
