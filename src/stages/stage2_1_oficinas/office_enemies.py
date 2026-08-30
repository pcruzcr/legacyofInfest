"""
Module: office_enemies
System: stages.stage2_1_oficinas

BruteOficinas / ChargerOficinas — variantes de Brute y Charger con sprites
propios, en lugar de los compartidos `assets/sprites/enemies/zone2/`.

Bug real encontrado jugando el nivel: `EnemyBrute.__init__` pide sus cuadros
con `self._load_zone_sprites(zone, 24, 18)` y `EnemyCharger` con
`self._load_zone_sprites(zone, 14, 12)` — pero **las tres zonas** comparten
la misma hoja `enemy_zone{N}_walk.png` de 96x12 px (`AssetLoader` lo
confirma: `zone1_walk`, `zone2_walk` y `zone3_walk` miden igual). Con
`frame_height=18` sobre una hoja de 12 px de alto,
`rows = sheet.get_height() // frame_height` da **0**: `EnemyBrute` no carga
ni un solo cuadro en ninguna zona del juego y cae al rectángulo de color
plano de `EnemyBase.draw()` — el "cuadro que tapa el mapa" que se ve al
jugar. `EnemyCharger` no falla tan fuerte (12 sí divide 12), pero 96/14 no
es entero: cada cuadro se recorta a caballo entre dos personajes dibujados
para casillas de 16 px, así que sale visualmente cortado.

Es un bug de motor compartido por las tres zonas, no algo de esta entrega,
así que el arreglo correcto no es tocar `enemy_brute.py`/`enemy_charger.py`
(afectaría a cualquier otro stage) ni las hojas compartidas de zona 2
(rompería a `Walker`, que sí carga bien de ahí). El arreglo aquí es local:
estas dos subclases cargan sus propias hojas, ya dimensionadas para lo que
sus clases base piden, desde esta misma carpeta.
"""
from __future__ import annotations

from pathlib import Path

from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_brute import EnemyBrute
from src.framework.entities.enemy_charger import EnemyCharger

_SPRITE_DIR = Path(__file__).parent / "enemy_sprites"


def _reload_sprites(entity: EnemyBrute | EnemyCharger, prefix: str) -> None:
    fw, fh = entity._sprite_fw, entity._sprite_fh
    for key, fname in (
        ("walk", f"{prefix}_walk.png"),
        ("hurt", f"{prefix}_hurt.png"),
        ("die", f"{prefix}_die.png"),
    ):
        entity._sprite_frames[key] = AssetLoader.load_sprite_sheet(
            _SPRITE_DIR / fname, fw, fh,
        )


class BruteOficinas(EnemyBrute):
    """Brute con hoja propia de 24x18/cuadro (ver módulo)."""

    def __init__(self, spawn_position, **kwargs) -> None:  # noqa: ANN001
        super().__init__(spawn_position, **kwargs)
        _reload_sprites(self, "brute_oficinas")


class ChargerOficinas(EnemyCharger):
    """Charger con hoja propia de 14x12/cuadro, alineada de verdad (ver módulo)."""

    def __init__(self, spawn_position, **kwargs) -> None:  # noqa: ANN001
        super().__init__(spawn_position, **kwargs)
        _reload_sprites(self, "charger_oficinas")
