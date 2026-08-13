"""AUD-456 — `squad_brain` decide por reglas cuando la IA no está lista.

AUD-088 pagó la carga de scikit-learn en la pantalla de inicio, pero el flujo
`--stage` / `--boss` de `main.py` la entierra sin actualizarla, así que el
import volvía a caer en el primer lote de `SquadBrain`, a medio segundo de
partida: un congelamiento de 2-3 s justo cuando un enemigo está encima. AUD-456
hace que el lote use la heurística de `tactica_por_reglas` (sin scikit-learn)
mientras la carga no se ha hecho — y para siempre si sklearn no está
instalado, que es la reserva que el README promete.

La parte de la precarga —cómo y cuándo se carga el predictor— la vigila
`test_precarga_ia.py` (AUD-457).

Lo que se fija aquí
-------------------
1. Que sin la IA lista el lote use reglas, sin excepciones.
2. Que si sklearn falta del todo, el juego no retira enemigos: reglas.
3. Que la heurística extraída produce exactamente lo que producía
   `get_rule_based_action`.
"""
from __future__ import annotations

import sys
import time

import pygame
import pytest

from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.entities.precarga_ia import ia_lista, precargar_ia
from src.framework.entities.squad_brain import SquadBrain


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


class _JugadorStub:
    def __init__(self) -> None:
        self.position = pygame.Vector2(300.0, 448.0)
        self.current_health = 5.0
        self.max_health = 5.0
        self.state = "IDLE"


def _sklearn_disponible() -> bool:
    try:
        import sklearn  # noqa: F401

        return True
    except ImportError:
        return False


class TestSquadConIaNoLista:
    def test_usa_reglas_sin_importar_sklearn(self, monkeypatch) -> None:
        from src.framework.entities import precarga_ia

        monkeypatch.setattr(precarga_ia, "ia_lista", lambda: False)
        brain = SquadBrain()
        enemigo = EnemyWalker(pygame.Vector2(288.0, 452.0))
        brain.update(0.26, _JugadorStub(), [enemigo])
        decision = brain.decision_for(enemigo)
        assert decision.source == "rules"
        # Walker a 12 px de distancia, sano: cuerpo a cuerpo.
        assert decision.action == "attack_melee"

    def test_si_sklearn_falta_no_se_retira_al_enemigo(self, monkeypatch) -> None:
        """El ImportError de la carga no debe subir hasta la escena."""
        from src.framework.entities import precarga_ia

        monkeypatch.setattr(precarga_ia, "ia_lista", lambda: True)
        # sys.modules[nombre] = None hace que el import lance ImportError,
        # simulando un sklearn ausente sin desinstalar nada.
        clave = "src.framework.entities.ai_predictor"
        previo = sys.modules.pop(clave, None)
        try:
            brain = SquadBrain()
            enemigo = EnemyWalker(pygame.Vector2(288.0, 452.0))
            brain.update(0.26, _JugadorStub(), [enemigo])
            decision = brain.decision_for(enemigo)
            assert decision.source == "rules"
        finally:
            if previo is not None:
                sys.modules[clave] = previo

    def test_con_ia_lista_el_flujo_del_modelo_sigue_intacto(self) -> None:
        if not _sklearn_disponible():
            pytest.skip("scikit-learn no está instalado; la IA usa su heurística")
        from src.framework.entities import precarga_ia

        if not precarga_ia.ia_lista():
            precargar_ia()
            for _ in range(300):
                if ia_lista():
                    break
                time.sleep(0.1)
        brain = SquadBrain()
        enemigo = EnemyWalker(pygame.Vector2(288.0, 452.0))
        # Cada update (0.26 s) dispara un lote; al décimo el modelo se entrena
        # y las decisiones pasan a salir del predictor: el flujo del modelo
        # sigue conectado después del cambio de AUD-456.
        for _ in range(120):
            brain.update(0.26, _JugadorStub(), [enemigo])
            if brain.decision_for(enemigo).source == "model":
                return
        pytest.fail("el modelo nunca pasó a decidir; el flujo quedó roto")


class TestLaHeuristicaExtraidaEsLaMisma:
    def test_tabla_de_casos_equivale_al_predictor(self) -> None:
        from src.framework.entities.ai_predictor import BehaviorPredictor
        from src.framework.entities.tactica_por_reglas import accion_por_distancia

        predictor = BehaviorPredictor()
        casos = [
            (30.0, 0.2, 0.5, False),   # herido y cerca: evade
            (30.0, 0.8, 0.5, False),   # cuerpo a cuerpo
            (30.0, 0.8, 0.5, True),    # cuerpo a cuerpo con alcance: retreat
            (90.0, 0.8, 0.5, True),    # alcance medio con alcance: ranged
            (90.0, 0.8, 0.5, False),   # alcance medio: charge
            (130.0, 0.8, 0.1, False),  # jugador a punto de caer: ataca
            (300.0, 0.8, 0.5, False),  # lejos: approach
            (150.0, 0.8, 0.5, False),  # ni cerca ni lejos: circle
        ]
        for dist, hp, php, ranged in casos:
            esperado = predictor.get_rule_based_action(dist, hp, php, ranged)
            obtenido = accion_por_distancia(dist, hp, php, ranged)
            assert obtenido == esperado, (
                f"heurística divergió para dist={dist} hp={hp} php={php} "
                f"ranged={ranged}: {obtenido} != {esperado}"
            )
