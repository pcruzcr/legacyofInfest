"""La economía del escenario: qué deja cada enemigo al morir.

Extraído de `SenalesDeEscenario` (stage_parts/senales.py) en 2026-08-20 para
bajar ese mixin a su presupuesto sin cambiar una línea de lógica. No es una
«señal» del bus: vivir ahi era histórico, no conceptual — el botín lo deja
quien recoge el `ENEMY_DIED`, pero es la economía, no el sonido/efecto.

Es un mixin de lectura, igual que los demás: no se instancia solo, depende
de los atributos de la escena (`_interactables`).
"""
from __future__ import annotations

from typing import Any

import pygame


class EconomiaDeEscenario:
    """Colocación del botín de los enemigos muertos.

    Espera de la escena: `_interactables`.
    """

    #: Lado del recogible de monedas, en píxeles. Del tamaño de una baldosa
    #: para que se vea y se coja al pasar sin tener que buscarlo.
    _BOTIN_TAM: int = 16

    def _soltar_botin(self, entity_id: str, pos: Any, skill: str = "") -> None:
        """Deja el botín donde murió el enemigo: monedas y, si lo declara, su
        habilidad (AUD-218, AUD-238).

        La cantidad de monedas la decide `score_system.coins_for()`, que es
        donde vive la tabla por tipo — la misma lectura de `entity_id` que usa
        la puntuación, para no tener dos formas de decir «esto es un jefe».
        """
        interactables = getattr(self, "_interactables", None)
        if interactables is None:
            return
        from src.engine.core.score_system import coins_for
        from src.framework.stage.interactables import Recogible

        lado = self._BOTIN_TAM
        cx = int(float(pos[0]))
        cy = int(float(pos[1]))
        interactables.soltar_botin(entity_id, Recogible(
            rect=pygame.Rect(cx - lado // 2, cy - lado // 2, lado, lado),
            item_id="coin",
            automatico=True,
            cantidad=coins_for(entity_id),
        ))
        # AUD-238: la reliquia del jefe, **además** de las monedas y no en su
        # lugar. AUD-263: pueden ser varias, separadas por coma, y se colocan en
        # fila para que no queden una encima de otra.
        #
        # Se descarta lo que no está en el catálogo: un jefe de una entrega con
        # `skill_drop = "skill_volar"` dejaría en el suelo algo que `collect()`
        # rechaza, y el jugador lo cogería sin que pasara nada.
        from src.engine.core.inventory import get_inventory
        for n, nombre in enumerate(s for s in skill.split(",") if s):
            if get_inventory().get_def(nombre) is not None:
                interactables.recogibles.append(Recogible(
                    rect=pygame.Rect(cx + lado * (n + 1), cy - lado // 2, lado, lado),
                    item_id=nombre,
                    automatico=True,
                ))