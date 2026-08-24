"""La IA con scikit-learn debe ser útil, barata y determinista (AUD-050).

Contexto
--------
`ai_predictor.BehaviorPredictor` llevaba todo el proyecto completo y sin un solo
llamante. La auditoría lo listó como código muerto, pero medirlo explicó por qué
nadie lo había conectado:

    inferencia individual        : 1,89 ms
    9 enemigos por fotograma     : 17,05 ms = 102% del presupuesto a 60 fps
    30 enemigos                  : 56,8 ms = 341%

Conectarlo de la forma obvia no habría añadido inteligencia, habría destruido el
framerate. `SquadBrain` lo hace viable con dos medidas — un lote en vez de N
llamadas, y cadencia de 4 Hz en vez de cada fotograma — y baja el coste
amortizado a 0,10 ms (0,61%).

Estas pruebas fijan las tres propiedades que hacen la función utilizable:
**presupuesto**, **determinismo** y **degradación honesta**.
"""
from __future__ import annotations

import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

FRAME_BUDGET_MS = 1000.0 / 60.0


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield


@pytest.fixture
def player(display):
    from src.engine.core.event_bus import EventBus
    from src.framework.entities.player import Player

    return Player(pygame.Vector2(400, 300), event_bus=EventBus())


def _enemies(count: int):
    from src.framework.entities.enemy_walker import EnemyWalker

    return [EnemyWalker(pygame.Vector2(100 + i * 20, 300)) for i in range(count)]


def _warmed_brain(player, enemies, cycles: int = 150):
    """Un cerebro con el modelo ya entrenado por la política de reglas."""
    from src.framework.entities.squad_brain import SquadBrain

    brain = SquadBrain()
    brain.reset()
    for _ in range(cycles):
        brain.update(1 / 60, player, enemies)
    return brain


# ── presupuesto de fotograma ─────────────────────────────────────


class TestFrameBudget:
    @pytest.mark.parametrize("count", [9, 30])
    def test_stays_within_budget(self, count: int, player, display) -> None:
        """El coste amortizado debe quedar muy por debajo del fotograma.

        Umbral al 5%: la medición da ~0,6-0,9%, así que hay un orden de magnitud
        de margen. Si esto falla es porque alguien volvió a llamar al predictor
        por enemigo y por fotograma, que es exactamente el fallo que dejaba la
        función inservible.
        """
        enemies = _enemies(count)
        brain = _warmed_brain(player, enemies)

        iterations = 400
        start = time.perf_counter()
        for _ in range(iterations):
            brain.update(1 / 60, player, enemies)
        per_frame = (time.perf_counter() - start) / iterations * 1000

        share = per_frame / FRAME_BUDGET_MS
        assert share < 0.05, (
            f"la IA de escuadra cuesta {per_frame:.3f} ms/fotograma con {count} "
            f"enemigos = {share * 100:.1f}% del presupuesto. Sospecha una "
            f"inferencia por entidad en lugar de predict_batch()."
        )

    def test_batch_beats_individual_calls(self, player, display) -> None:
        """Justifica el diseño: el lote debe ser medibemente más rápido.

        Si algún día sklearn deja de tener sobrecarga por invocación, este test
        falla y la complejidad del lote deja de estar justificada — momento de
        simplificar en lugar de conservar una optimización sin razón.
        """
        from src.framework.entities.ai_predictor import get_predictor

        enemies = _enemies(12)
        _warmed_brain(player, enemies)
        predictor = get_predictor()
        if not predictor.is_trained:
            pytest.skip("el modelo no llegó a entrenarse")

        rows = [[0.1] * 10 for _ in range(12)]

        start = time.perf_counter()
        for _ in range(30):
            predictor.predict_batch(rows)
        batched = time.perf_counter() - start

        start = time.perf_counter()
        for _ in range(30):
            for row in rows:
                predictor.predict(row)
        individual = time.perf_counter() - start

        assert batched < individual, (
            f"el lote ({batched * 1000:.1f} ms) no fue más rápido que las "
            f"llamadas individuales ({individual * 1000:.1f} ms)"
        )


# ── determinismo ─────────────────────────────────────────────────


class TestDeterminism:
    def test_predict_is_deterministic(self, display) -> None:
        """El mismo estado debe dar la misma acción.

        `predict` elegía entre KNN y árbol con `random.random() < 0.6`, así que
        el mismo estado de juego producía acciones distintas. Eso hace la IA
        imposible de depurar y no produce variedad interesante, sólo
        incoherencia: el enemigo cambia de plan sin que nada haya cambiado.
        """
        from src.framework.entities.ai_predictor import BehaviorPredictor

        predictor = BehaviorPredictor()
        for i in range(40):
            predictor.add_example([i / 40] * 10, i % 4)

        row = [0.3] * 10
        results = {predictor.predict(row) for _ in range(25)}
        assert len(results) == 1, (
            f"la misma entrada dio {len(results)} acciones distintas: {results}"
        )

    def test_batch_matches_individual(self, display) -> None:
        """El lote y la llamada individual deben coincidir.

        Si divergen, optimizar por lotes cambió el comportamiento del juego — una
        optimización que altera la semántica es un bug, no una optimización.
        """
        from src.framework.entities.ai_predictor import BehaviorPredictor

        predictor = BehaviorPredictor()
        for i in range(40):
            predictor.add_example([i / 40] * 10, i % 4)

        rows = [[0.2] * 10, [0.5] * 10, [0.8] * 10]
        batched = predictor.predict_batch(rows)
        assert batched is not None

        individual = [
            predictor.action_names[predictor.predict(r) % len(predictor.action_names)]
            for r in rows
        ]
        assert batched == individual, (
            f"lote {batched} != individual {individual}"
        )


# ── degradación honesta ──────────────────────────────────────────


class TestGracefulDegradation:
    def test_untrained_model_returns_none_not_noise(self, display) -> None:
        """Sin entrenar debe admitirlo, no inventar.

        Devolver una acción aleatoria disfrazada de predicción es peor que
        devolver None: el llamante no puede distinguir "el modelo opina esto" de
        "no hay modelo", y la política de reserva nunca se activa.
        """
        from src.framework.entities.ai_predictor import BehaviorPredictor

        fresh = BehaviorPredictor()
        assert fresh.predict_batch([[0.0] * 10]) is None
        assert fresh.predict([0.0] * 10) == -1

    def test_falls_back_to_rules_before_training(self, player, display) -> None:
        from src.framework.entities.squad_brain import SquadBrain

        enemies = _enemies(4)
        brain = SquadBrain()
        brain.reset()
        # Un único ciclo: el modelo no puede estar entrenado todavía.
        brain.update(1.0, player, enemies)

        decisions = [brain.decision_for(e) for e in enemies]
        assert any(d.source == "rules" for d in decisions), (
            "ninguna decisión vino de las reglas en el primer ciclo"
        )

    def test_every_action_is_a_known_name(self, player, display) -> None:
        """El enemigo debe recibir una acción que sepa obedecer."""
        from src.framework.entities.ai_predictor import get_predictor

        enemies = _enemies(10)
        brain = _warmed_brain(player, enemies)
        valid = set(get_predictor().action_names)

        for enemy in enemies:
            action = brain.decision_for(enemy).action
            assert action in valid, f"acción desconocida {action!r}"

    def test_no_player_does_not_crash(self, display) -> None:
        from src.framework.entities.squad_brain import SquadBrain

        brain = SquadBrain()
        brain.update(1.0, None, _enemies(3))  # no debe lanzar

    def test_dead_enemies_are_forgotten(self, player, display) -> None:
        """Sin esto el diccionario de decisiones crece sin límite."""
        from src.framework.entities.squad_brain import SquadBrain

        enemies = _enemies(5)
        brain = SquadBrain()
        for _ in range(20):
            brain.update(1 / 60, player, enemies)
        tracked = brain.stats["enemigos_seguidos"]

        for enemy in enemies:
            brain.forget(enemy)
        assert brain.stats["enemigos_seguidos"] < tracked


# ── la táctica llega al comportamiento ───────────────────────────


class TestTacticIsObeyed:
    """El modelo debe cambiar lo que el enemigo hace, no sólo un atributo.

    Es la comprobación que faltaba en todo el proyecto: `consume_hitbox`,
    `add_stage`, `pause_timer` — todos existían, todos estaban "conectados" en
    apariencia, y ninguno afectaba al juego.
    """

    @staticmethod
    def _walker_with(tactic: str, display):
        from src.framework.entities.enemy_base import EnemyState
        from src.framework.entities.enemy_walker import EnemyWalker

        enemy = EnemyWalker(pygame.Vector2(200.0, 300.0))
        enemy.state = EnemyState.ALERT
        enemy.tactic = tactic
        enemy.facing_direction = 1
        enemy._player_ref = pygame.Rect(400, 300, 20, 32)
        enemy._charge_cooldown = 99.0  # aísla la táctica de la carga
        return enemy

    def test_default_tactic_advances(self, display) -> None:
        enemy = self._walker_with("approach", display)
        start = enemy.position.x
        for _ in range(30):
            enemy._alert_behavior(1 / 60)
        assert enemy.position.x > start, "'approach' no avanzó"

    def test_retreat_moves_away(self, display) -> None:
        enemy = self._walker_with("retreat", display)
        start = enemy.position.x
        for _ in range(30):
            enemy._alert_behavior(1 / 60)
        assert enemy.position.x < start, (
            "'retreat' no retrocedió: el predictor puede emitir esa acción y "
            "el enemigo la ignora, así que el modelo está conectado a la nada"
        )

    def test_wait_holds_position(self, display) -> None:
        enemy = self._walker_with("wait", display)
        start = enemy.position.x
        for _ in range(30):
            enemy._alert_behavior(1 / 60)
        assert enemy.position.x == pytest.approx(start, abs=0.5)

    def test_retreat_keeps_facing_the_player(self, display) -> None:
        """Retroceder de espaldas se lee como despiste, no como retirada."""
        enemy = self._walker_with("retreat", display)
        for _ in range(30):
            enemy._alert_behavior(1 / 60)
        assert enemy.facing_direction == 1, (
            "el enemigo se dio la vuelta al retroceder"
        )

    def test_charge_is_faster_than_approach(self, display) -> None:
        distances = {}
        for tactic in ("approach", "charge"):
            enemy = self._walker_with(tactic, display)
            start = enemy.position.x
            for _ in range(30):
                enemy._alert_behavior(1 / 60)
            distances[tactic] = abs(enemy.position.x - start)

        assert distances["charge"] > distances["approach"], (
            f"'charge' no fue más rápido que 'approach': {distances}"
        )

    def test_circle_is_slower_than_approach(self, display) -> None:
        distances = {}
        for tactic in ("approach", "circle"):
            enemy = self._walker_with(tactic, display)
            start = enemy.position.x
            for _ in range(30):
                enemy._alert_behavior(1 / 60)
            distances[tactic] = abs(enemy.position.x - start)

        assert distances["circle"] < distances["approach"], (
            f"'circle' no cedió espacio: {distances}"
        )

    def test_unknown_tactic_behaves_like_approach(self, display) -> None:
        """Una acción nueva del modelo no debe congelar al enemigo."""
        enemy = self._walker_with("tactica_inexistente", display)
        start = enemy.position.x
        for _ in range(30):
            enemy._alert_behavior(1 / 60)
        assert enemy.position.x > start


def test_enemies_default_to_a_safe_tactic(display) -> None:
    """Un enemigo creado sin SquadBrain debe comportarse como antes.

    Importa para las plantillas de alumno y para los tests existentes: añadir el
    cerebro de escuadra no debe cambiar el comportamiento de un enemigo suelto.
    """
    from src.framework.entities.enemy_walker import EnemyWalker

    assert EnemyWalker(pygame.Vector2(0, 0)).tactic == "approach"
