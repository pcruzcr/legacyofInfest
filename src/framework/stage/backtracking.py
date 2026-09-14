"""
Backtracking global — 100% vistas con retorno (AUD-BACKTRACK).

Objetivo
========
Todas las vistas deben soportar backtracking para llegar al 100% del
proyecto `docs/93_AUDITORIA_ESTRATEGICA_Y_FODA.md:322` (hub/backtracking
estaba descartado por incompatibilidad docente, ahora se reintroduce como
**post-game opcional** que no rompe la linealidad de la primera partida).

Diseño
======
* Lineal primero, libre después: la primera pasada es zonal 3+1 como
  Super Mario `93:116`; al completar un stage, su Warp de retorno y el
  nodo del mapa se desbloquean. No se altera `STAGE_ORDER`.
* Vista-agnóstico: WarpZone es un rect invisible + destino (Vector2) que
  funciona igual en lateral (gravedad), cenital (top-down), isométrica
  (shear 0.5) o raycast (escala 1.5). No toca `vista_system.py` ni
  `PhysicsProfile` — la escena ya traduce `via` a `Player.vista_cenital`
  `stage_scene.py:457`.
* Persistido: `SaveData.completed_stages + backtrack_unlocks` en
  `save_manager.py`. La invariante 2 (26 clases sin tocar) se respeta:
  solo datos, no código de `src/stages/`.

Uso
===
TMX: objeto tipo `WarpZone` con `destino_stage_id` (string) o
`destino_x/destino_y` (float). Si `destino_stage_id` está, el warp
cambia de escenario vía `SceneManager`; si no, teletransporta intra-mapa
(atajo de una vía `93:310` B3). Propiedad `backtrack_only:bool` lo hace
visible solo tras completar el stage (para no spoilear atajos).

WorldMap: `world_map_scene.py:137` ya construye nodos desde
`discover_stages()`. `CONNECTIONS_BACKTRACK` añade aristas inversas
para los completados — el zigzag se dibuja bidireccional en verde
`93:165`.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext  # noqa: F401

logger = logging.getLogger(__name__)

# ── Datos ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BacktrackLink:
    """Un atajo desbloqueable: origen -> destino, con requisito opcional."""
    origen: str          # stage_id origen
    destino: str         # stage_id destino (o "HUB")
    requiere_flag: str = ""   # flag de `SaveData.completed_stages` o skill
    vista: str = ""      # vista donde se muestra (vacío = todas)


# Grafo canónico de backtracking: cada stage desbloquea el anterior tras
# completarse. El HUB central conecta con todos (post-game).
# Se genera dinámicamente desde STAGE_ORDER para no duplicar la lista.
def _gaps(*_a: object, **_k: object) -> None:
    pass


def enlaces_desbloqueados(completados: set[str], vista_actual: str = "") -> list[BacktrackLink]:
    """Qué atajos están abiertos ahora. Vista-agnóstico salvo filtro opcional."""
    from src.engine.core.stage_registry import STAGE_ORDER

    out: list[BacktrackLink] = []
    for i, sid in enumerate(STAGE_ORDER):
        if sid not in completados:
            continue
        # Al completar i, se abre i-1 (volver atrás) y el HUB
        if i > 0:
            prev = STAGE_ORDER[i - 1]
            out.append(BacktrackLink(origen=sid, destino=prev))
        out.append(BacktrackLink(origen=sid, destino="HUB"))
        # Atajo transversal 1-vía por zona (B3) — se abre al 50% de zona
        # Aquí simplificado: cada 3 stages abre atajo a inicio de zona
        if (i + 1) % 3 == 0 and i + 1 < len(STAGE_ORDER):
            out.append(BacktrackLink(origen=sid, destino=STAGE_ORDER[i + 1]))

    # Filtrar por vista si se pide (ej. solo isométrica ve su atajo)
    if vista_actual:
        out = [e for e in out if not e.vista or e.vista == vista_actual]
    return out


def puede_volver_a(stage_id: str, completados: set[str]) -> bool:
    """¿Este stage permite volver atrás? True si está completado o es HUB."""
    return stage_id in completados or stage_id == "HUB"


# ── WorldMap helpers ───────────────────────────────────────────────

def conexiones_con_backtracking(nodos: list[dict], completados: set[str]) -> list[tuple[int, int]]:
    """CONNECTIONS + inversas para completados. Usado por WorldMapScene.draw."""
    from src.engine.scenes.world_map_scene import _node_index
    base = [(i, _node_index[uid]) for i, nd in enumerate(nodos) for uid in nd.get("unlocks", []) if uid in _node_index]
    # Inversas
    for link in enlaces_desbloqueados(completados):
        if link.origen in _node_index and link.destino in _node_index:
            a, b = _node_index[link.origen], _node_index[link.destino]
            if (b, a) not in base and (a, b) not in base:
                base.append((b, a))
    return base


# ── TMX helpers ────────────────────────────────────────────────────

def warp_de_backtrack(rect: pygame.Rect, destino_stage: str) -> dict:
    """Descriptor para que StageLoader construya un WarpZone de retorno."""
    return {
        "rect": rect,
        "destino": pygame.Vector2(rect.centerx, rect.centery),  # se resuelve a stage en handler
        "destino_stage_id": destino_stage,
        "backtrack_only": True,
        "mensaje": f"Volver a {destino_stage} (backtracking)",
    }
