"""AUD-628: añade imports faltantes a los 8 enemigos nuevos de Phase 3-4."""
from pathlib import Path

ENEMIGOS = [
    "enemy_climber.py", "enemy_flying_bomber.py", "enemy_ice_skater.py",
    "enemy_parry_teacher.py", "enemy_shielded.py", "enemy_summoner.py",
    "enemy_swimmer.py", "enemy_terrain_shaper.py",
]

VIEJO = "from src.framework.entities.enemy_base import EnemyBase"
NUEVO = (
    "import logging\n"
    "\n"
    "from src.engine.utils.asset_loader import AssetLoader\n"
    "from src.framework.entities.enemy_base import EnemyBase\n"
    "\n"
    "logger = logging.getLogger(__name__)"
)

for nombre in ENEMIGOS:
    ruta = Path("src/framework/entities") / nombre
    if not ruta.exists():
        print(f"NO EXISTE: {nombre}")
        continue
    contenido = ruta.read_text(encoding="utf-8")
    if VIEJO in contenido:
        nuevo_contenido = contenido.replace(VIEJO, NUEVO, 1)
        ruta.write_text(nuevo_contenido, encoding="utf-8")
        print(f"FIXED: {nombre}")
    elif "AssetLoader" not in contenido:
        print(f"SKIP (no usa): {nombre}")
    else:
        print(f"YA TIENE: {nombre}")