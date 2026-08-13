"""Módulo: tactica_por_reglas
Sistema: framework.entities
Unidad Académica: Unidad IX — Reconocimiento de patrones

Heurística determinista que decide la táctica de un enemigo sin tocar
scikit-learn.

Por qué existe (AUD-456)
-----------------------
La heurística vivía como método de `BehaviorPredictor`, y `BehaviorPredictor`
vive en un módulo que importa scikit-learn entero (medido: 2,3-3,3 s). El
`SquadBrain` la usaba como política de reserva, pero para llamarla tenía que
importar el módulo, de modo que la reserva no era gratis: sin el modelo, el
primer lote de decisiones seguía pagando la carga de sklearn a mitad de
partida (el tirón que AUD-088 movió a la pantalla de inicio volvía a aparecer
en el flujo `--stage`, que se la salta).

Aquí la heurística no depende de sklearn: el motor puede decidir por reglas
mientras la IA se carga en segundo plano, o para siempre si sklearn no está
instalado — el comportamiento determinista que el README promete como reserva.
`BehaviorPredictor.get_rule_based_action` delega aquí para que la API pública
no cambie de sitio.
"""

from __future__ import annotations


def accion_por_distancia(
    dist: float,
    health_pct: float,
    player_health_pct: float,
    has_ranged: bool = False,
) -> str:
    """La política de reserva, en lógica pura.

    Las reglas están calibradas para leer distancias familiares: cuerpo a
    cuerpo («attack_melee»), alcance medio («charge» / «attack_ranged») y
    lejanía («approach»), con el retroceso («evade» / «retreat») reservado a
    la presión del enemigo herido o del jugador a punto de caer.
    """
    if health_pct < 0.3 and dist < 60:
        return "evade"
    if dist < 40:
        return "attack_melee" if not has_ranged else "retreat"
    if dist < 120 and has_ranged:
        return "attack_ranged"
    if dist < 120:
        return "charge"
    if player_health_pct < 0.3 and dist < 150:
        return "attack_melee"
    if dist > 200:
        return "approach"
    return "circle"