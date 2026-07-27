"""
Module: squad_brain
System: framework.entities
Academic Unit: Unit IX — Reconocimiento de patrones aplicado

Toma de decisiones táctica para todos los enemigos de una escena, por lotes.

Por qué existe (AUD-050)
------------------------
`ai_predictor.BehaviorPredictor` estaba completo y sin un solo llamante. La
razón por la que nunca se conectó se descubre al medirlo:

    inferencia individual        : 1,89 ms por llamada
    con 9 enemigos por fotograma : 17,05 ms = 102% del presupuesto a 60 fps
    con 30 enemigos              : 56,8 ms = 341% del presupuesto

Es decir, llamar al predictor una vez por enemigo y por fotograma **consume el
fotograma entero**. Conectarlo de forma ingenua no habría añadido inteligencia:
habría convertido el juego en una presentación de diapositivas. El módulo no
estaba sin usar por olvido, estaba sin usar porque su forma de uso obvia es
inviable.

Dos medidas lo arreglan, y las dos son mejores también en términos de diseño:

**1. Un lote en vez de N llamadas.** sklearn está vectorizado; el coste está
dominado por la sobrecarga por invocación, no por el número de filas::

    N enemigos   1-por-1     en lote    mejora
             9   11,87 ms    1,82 ms       7x
            30   41,73 ms    2,57 ms      16x
           100  138,98 ms    8,97 ms      15x

**2. Cadencia baja en vez de cada fotograma.** Un enemigo que reconsidera su
estrategia 60 veces por segundo no es más inteligente, es más errático — cambia
de opinión antes de que el jugador pueda leer su intención, que es justo lo
contrario de lo que hace buena a la IA de un juego de acción. Reevaluar a 4 Hz
deja el coste amortizado en ~0,12 ms por fotograma (0,7% del presupuesto) y
produce enemigos cuyas decisiones se pueden *leer*.

Las decisiones se escalonan entre enemigos para que el lote no coincida todo en
el mismo fotograma con otro trabajo pesado.

Determinismo
------------
`BehaviorPredictor.predict` mezclaba KNN y árbol con `random.random() < 0.6`,
lo que hace que el mismo estado de juego produzca acciones distintas y vuelve
la IA imposible de probar y de depurar. Aquí se consulta el predictor a través
de una ruta determinista y la variedad se introduce donde corresponde: en los
parámetros del comportamiento, no en qué modelo responde.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.framework.entities.enemy_base import EnemyBase
    from src.framework.entities.player import Player


#: Veces por segundo que un enemigo reconsidera su táctica.
DECISION_HZ: float = 4.0
#: Enemigos por encima de los cuales se degrada a reglas deterministas. Medido:
#: el lote de 100 cuesta 8,97 ms, que ya no cabe con margen.
MAX_BATCH: int = 48


@dataclass
class Decision:
    """Lo que un enemigo ha decidido hacer, y por qué."""

    action: str = "approach"
    source: str = "rules"      # "rules" | "model"
    age: float = 0.0

    def __str__(self) -> str:  # útil en el overlay de debug
        return f"{self.action} ({self.source})"


@dataclass
class SquadBrain:
    """Decide tácticas para un grupo de enemigos, por lotes y a baja cadencia.

    Una instancia por escena. `StageScene` la crea y la actualiza; los enemigos
    consultan `decision_for(enemy)`, que es una lectura de diccionario, no una
    inferencia.
    """

    decision_hz: float = DECISION_HZ
    _decisions: dict[int, Decision] = field(default_factory=dict)
    _timer: float = 0.0
    _telemetry_frames: int = 0
    _model_calls: int = 0
    _rule_calls: int = 0

    # ── ciclo de vida ──────────────────────────────────────────

    def reset(self) -> None:
        self._decisions.clear()
        self._timer = 0.0
        self._telemetry_frames = 0
        self._model_calls = 0
        self._rule_calls = 0

    def forget(self, enemy: EnemyBase) -> None:
        """Descarta la decisión de un enemigo muerto o retirado."""
        self._decisions.pop(id(enemy), None)

    # ── consulta (barata: la usan los enemigos cada fotograma) ──

    def decision_for(self, enemy: EnemyBase) -> Decision:
        """La táctica vigente de este enemigo. No infiere nada."""
        return self._decisions.get(id(enemy), Decision())

    # ── actualización (cara: se ejecuta a `decision_hz`) ────────

    def update(
        self,
        dt: float,
        player: Player | None,
        enemies: list[EnemyBase],
    ) -> None:
        """Avanza el reloj y recalcula el lote cuando toca."""
        for decision in self._decisions.values():
            decision.age += dt

        self._timer += dt
        interval = 1.0 / max(self.decision_hz, 0.1)
        if self._timer < interval:
            return
        self._timer -= interval

        if player is None:
            return

        alive = [e for e in enemies if getattr(e, "is_alive", False)]
        if not alive:
            return

        # Escalonado: sólo el subconjunto que le toca este ciclo. Reparte el
        # coste y evita que todos los enemigos cambien de idea a la vez, lo que
        # se lee como un ejército telepático.
        slot = self._telemetry_frames % 2
        batch = [e for i, e in enumerate(alive) if i % 2 == slot]
        self._telemetry_frames += 1

        if not batch:
            return

        if len(batch) > MAX_BATCH:
            # Demasiados enemigos para inferir con margen: reglas para todos.
            # Degradar es correcto — un framerate estable vale más que una
            # táctica marginalmente mejor.
            for enemy in batch:
                self._decisions[id(enemy)] = self._rule_decision(enemy, player)
            return

        self._decide_batch(batch, player)

    def _decide_batch(self, batch: list[EnemyBase], player: Player) -> None:
        """Una sola llamada al modelo para todo el lote."""
        from src.framework.entities.ai_predictor import get_predictor

        predictor = get_predictor()
        features = [self._features(e, player) for e in batch]

        actions = predictor.predict_batch(features)
        if actions is None:
            # Modelo sin entrenar todavía: reglas, y alimentamos el modelo con
            # lo que las reglas deciden para que aprenda de una política válida
            # en lugar de de ruido.
            for enemy, feature_row in zip(batch, features, strict=True):
                decision = self._rule_decision(enemy, player)
                self._decisions[id(enemy)] = decision
                predictor.add_example(
                    feature_row, predictor.action_index(decision.action),
                )
                self._rule_calls += 1
            return

        for enemy, action in zip(batch, actions, strict=True):
            self._decisions[id(enemy)] = Decision(action=action, source="model")
            self._model_calls += 1

    # ── extracción de características ───────────────────────────

    @staticmethod
    def _features(enemy: EnemyBase, player: Player) -> list[float]:
        from src.framework.entities.ai_predictor import get_predictor

        return get_predictor().extract_features(
            self_x=float(enemy.position.x), self_y=float(enemy.position.y),
            player_x=float(player.position.x), player_y=float(player.position.y),
            player_health=float(player.current_health),
            self_health=float(getattr(enemy, "current_health", 1.0)),
            player_state=str(getattr(player, "state", "")),
            wall_ahead=bool(getattr(enemy, "_wall_ahead", False)),
            ledge_ahead=bool(getattr(enemy, "_ledge_ahead", False)),
        )

    @staticmethod
    def _rule_decision(enemy: EnemyBase, player: Player) -> Decision:
        """Política determinista de reserva.

        Es también la política que entrena al modelo: aprender de reglas
        sensatas converge mucho más rápido que aprender de acciones aleatorias, y
        además garantiza que el peor caso del modelo sea "se comporta como las
        reglas" en lugar de "se comporta al azar".
        """
        from src.framework.entities.ai_predictor import get_predictor

        dx = float(player.position.x) - float(enemy.position.x)
        dy = float(player.position.y) - float(enemy.position.y)
        dist = (dx * dx + dy * dy) ** 0.5

        max_hp = float(getattr(enemy, "max_health", 1.0)) or 1.0
        hp_pct = float(getattr(enemy, "current_health", max_hp)) / max_hp
        player_max = float(getattr(player, "max_health", 5.0)) or 5.0
        player_pct = float(player.current_health) / player_max
        has_ranged = hasattr(enemy, "fire_rate") or hasattr(enemy, "_projectiles")

        action = get_predictor().get_rule_based_action(
            dist=dist, health_pct=hp_pct,
            player_health_pct=player_pct, has_ranged=has_ranged,
        )
        return Decision(action=action, source="rules")

    # ── introspección para el overlay de debug y los tests ─────

    @property
    def stats(self) -> dict[str, float]:
        total = self._model_calls + self._rule_calls
        return {
            "decisiones": float(total),
            "por_modelo": float(self._model_calls),
            "por_reglas": float(self._rule_calls),
            "fraccion_modelo": (self._model_calls / total) if total else 0.0,
            "enemigos_seguidos": float(len(self._decisions)),
        }
