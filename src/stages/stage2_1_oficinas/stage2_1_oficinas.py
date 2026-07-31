"""
Module: stage2_1_oficinas
System: src.stages.stage2_1_oficinas
Description: Zona 2 (Distrito Central) - Oficinas.
Escenario horizontal de recorrido y combate contra guardias a pie
(Walker / Charger / Brute). Sin jefe.
"""
from __future__ import annotations

from pathlib import Path

from src.framework.scenes.stage_scene import StageScene


class Stage21Oficinas(StageScene):
    # AUD-106 — ruta corregida al integrar la entrega.
    #
    # El mapa estaba junto al código. La convención del proyecto es
    # `assets/maps/<nombre>/<nombre>.tmx`, que es donde lo buscan el
    # validador, el calificador y el previsualizador. Duplicar el TMX en
    # dos sitios habría garantizado que algún día divergieran.
    TMX_PATH: Path = Path("assets/maps/stage2_1_oficinas/stage2_1_oficinas.tmx")
    ZONE: int = 2
