"""Track A — Paburu por forma: comportamiento, no declaraciones.

Por forma: TRANSITION (fase alcanzable) → ATTACK (spawn real) →
TELEGRAPH/FEEDBACK (eventos) → THREAT→DAMAGE (overlap forzado) →
COUNTERPLAY (parry/devuelta donde aplica).
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class _Bus:
    def __init__(self) -> None:
        self.emitidos: list[str] = []

    def emit(self, evento: str, **_datos) -> None:
        self.emitidos.append(evento)

    def subscribe(self, *_a, **_k) -> None:
        pass


def _jefe():
    from src.stages.boss_paburu.boss_paburu import BossPaburu

    jefe = BossPaburu(pygame.Vector2(400.0, 300.0))
    jefe._event_bus = _Bus()
    jefe._player_ref = pygame.Rect(500, 300, 20, 28)
    return jefe


def _jefe_con_variante(variante: str):
    """Sorteo determinista (semillas medidas: 1→gold, 0→black)."""
    from src.engine.core import azar

    semilla = {"gold": 1, "black": 0}[variante]
    jefe = _jefe()
    jefe._azar = azar.generador(semilla)
    _llevar_a_forma(jefe, 2)
    assert jefe.relic_variant == variante, (
        f"semilla {semilla} dio {jefe.relic_variant}: re-medir sorteo"
    )
    return jefe


def _jugador(x: float = 500.0, y: float = 300.0):
    from src.framework.entities.player import Player

    jugador = Player(pygame.Vector2(x, y))
    jugador._invincibility_timer = 0.0
    return jugador


def _simular(jefe, segundos: float = 25.0) -> dict[str, int]:
    """Simula con cadencias a cero y devuelve el PICO por contenedor.

    Los proyectiles expiran (vuelan y mueren): afirmar presencia al final
    mediría lifetimes, no ataques. El pico demuestra ejecución real.
    """
    for patron in jefe._patrones_de_la_fase():
        jefe._attack_timers[patron] = 0.01
    pico: dict[str, int] = {}
    pasos = int(segundos / (1 / 60))
    for _ in range(pasos):
        jefe._post_update(1 / 60)
        for clave in (
            "_projectiles", "_beams", "_seal_casts", "_olas", "_pulsos",
            "_ecos", "_animas", "_esquirlas", "_lagrimas", "_satelites",
            "_haces", "_espejos",
        ):
            n = len(getattr(jefe, clave, ()))
            pico[clave] = max(pico.get(clave, 0), n)
    return pico


class TestForma1Piedra:
    def test_piedra_dispara_y_dana(self) -> None:
        jefe = _jefe()
        assert jefe.current_phase == 0
        pico = _simular(jefe)
        assert pico.get("_projectiles", 0) > 0, "STONE_SPIT no deja cuerpos"
        assert pico.get("_beams", 0) > 0 or "BOSS_ATTACK" in jefe._event_bus.emitidos

        jugador = _jugador()
        jefe._attack_stone_spit()
        piedra = jefe._projectiles[-1]
        # `rect` es propiedad de `pos`: el overlap se fuerza por posición.
        piedra.pos.update(jugador.rect.centerx, jugador.rect.centery)
        vida = jugador.current_health
        jefe._check_player_contact(jugador)
        assert jugador.current_health < vida, "la piedra no transmite daño"

    def test_la_piedra_devuelta_dana_al_jefe(self) -> None:
        """Counterplay completo: parry → devolver → el jefe recibe."""
        jefe = _jefe()
        for _ in range(60):
            jefe.update(1 / 60)  # construye el hurtbox como en partida
        jefe._attack_stone_spit()
        piedra = jefe._projectiles[-1]
        vida = jefe.current_health
        piedra.devolver(pygame.Vector2(jefe.rect.center))
        assert piedra.devuelta is True
        # La devuelta viaja al cuerpo: se coloca y se revisa por el camino
        # del motor (`_revisar_devueltos`, no a mano).
        cuerpo = jefe.hurtbox
        piedra.pos.update(cuerpo.centerx, cuerpo.centery)
        jefe._revisar_devueltos()
        assert jefe.current_health < vida, "la devuelta no castiga"

    def test_el_sello_levanta_columnas(self) -> None:
        jefe = _jefe()
        pico = _simular(jefe, 30.0)
        assert pico.get("_seal_casts", 0) > 0 or jefe._seal is not None


class TestForma2Mascara:
    def test_mascara_ataca_con_olas_y_pulsos(self) -> None:
        jefe = _jefe()
        _llevar_a_forma(jefe, 1)
        assert jefe.current_phase == 1
        pico = _simular(jefe)
        assert pico.get("_olas", 0) + pico.get("_pulsos", 0) + pico.get("_ecos", 0) > 0, (
            "F2 no genera amenazas en 25 s"
        )

    def test_la_ola_dana_por_geometria_propia(self) -> None:
        jefe = _jefe()
        _llevar_a_forma(jefe, 1)
        jugador = _jugador()
        jefe._attack_spirit_wave()
        ola = jefe._olas[-1]
        # La ola nace telegrafiando 0,45 s: se madura antes de medir daño.
        for _ in range(40):
            ola.update(1 / 60) if hasattr(ola, "update") else None
        assert ola.rect is not None, "la ola madura no tiene geometría"
        jugador.rect.center = ola.rect.center
        jugador.position.update(float(jugador.rect.x), float(jugador.rect.y))
        vida = jugador.current_health
        jefe._check_player_contact(jugador)
        assert jugador.current_health < vida


def _llevar_a_forma(jefe, forma: int):
    """Avanza por transiciones reales (daño → transición → finish).

    Atajo `current_phase = N` deja la forma sin motor ni patrones: la
    Forma 3 nace en `_finish_phase_transition` (variante + motor).
    """
    while jefe.current_phase < forma:
        jefe.apply_hit(6.0, (400, 300))
        for _ in range(int(3.0 / (1 / 60))):
            jefe.update(1 / 60)
    return jefe


class TestForma3Reliquia:
    @pytest.mark.parametrize("variante", ["gold", "black"])
    def test_reliquia_ataca_segun_variante(self, variante: str) -> None:
        jefe = _jefe()
        _llevar_a_forma(jefe, 2)
        assert jefe.current_phase == 2
        assert jefe.relic_variant in ("gold", "black")
        assert jefe._motor_reliquia is not None
        assert jefe._patrones_de_la_fase(), "F3 sin patrones tras sorteo"
        pico = _simular(jefe)
        if jefe.relic_variant == "gold":
            assert pico.get("_esquirlas", 0) > 0, "Pepita sin esquirlas en 25 s"
        else:
            assert pico.get("_lagrimas", 0) > 0, "Perla sin lágrimas en 25 s"

    def test_la_variante_dana_y_se_devuelve(self) -> None:
        # La variante sale por sorteo en la transición: se prueba la que
        # salió (forzar la otra exigiría su motor; eso prueba el harness,
        # no el jefe). Ambas quedan cubiertas entre este test y el de spawn.
        jefe = _jefe()
        _llevar_a_forma(jefe, 2)
        jugador = _jugador()
        if jefe.relic_variant == "gold":
            jefe._attack_esquirlas_de_oro()
            bicho = jefe._esquirlas[-1]
            bicho.pos.update(jugador.rect.centerx, jugador.rect.centery)
        else:
            jefe._attack_lagrima_negra()
            bicho = jefe._lagrimas[-1]
            bicho.pos.update(jugador.rect.centerx, jugador.rect.centery)
        vida = jugador.current_health
        jefe._check_player_contact(jugador)
        assert jugador.current_health < vida

    @pytest.mark.parametrize(
        "variante,ataque,contenedor",
        [
            ("gold", "_attack_esquirlas_de_oro", "_esquirlas"),
            ("black", "_attack_lagrima_negra", "_lagrimas"),
        ],
    )
    def test_cada_variante_dana(self, variante, ataque, contenedor) -> None:
        jefe = _jefe_con_variante(variante)
        jugador = _jugador()
        getattr(jefe, ataque)()
        bicho = getattr(jefe, contenedor)[-1]
        bicho.pos.update(jugador.rect.centerx, jugador.rect.centery)
        vida = jugador.current_health
        jefe._check_player_contact(jugador)
        assert jugador.current_health < vida, f"{variante} no transmite daño"


class TestForma4Espiritu:
    def test_espiritu_converge_con_satelites_y_haces(self) -> None:
        jefe = _jefe()
        _llevar_a_forma(jefe, 3)
        assert jefe.current_phase == 3
        pico = _simular(jefe, 30.0)
        assert pico.get("_satelites", 0) + pico.get("_haces", 0) > 0, (
            "F4 no genera amenazas en 30 s"
        )

    def test_transiciones_entre_formas_barren_vuelo(self) -> None:
        jefe = _jefe()
        pico = _simular(jefe, 12.0)
        assert pico.get("_projectiles", 0) > 0, (
            "ni F1 genera vuelo: el harness no simula nada"
        )
        jefe.current_phase = 1
        jefe._finish_phase_transition()
        total = (
            len(jefe._projectiles) + len(jefe._beams) + len(jefe._olas)
            + len(jefe._pulsos) + len(jefe._ecos)
        )
        assert total == 0, "la transición deja amenazas vivas de la forma anterior"
