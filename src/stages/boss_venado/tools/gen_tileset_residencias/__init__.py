"""Generador del tileset de la arena Residencias al Crepusculo.

AUD-345 — este paquete sustituye al archivo dios ``gen_tileset_residencias.py``
(2364 lineas: 266 pintores de tiles + registro + composicion) por un paquete
por tema: ``core`` (registro y helpers), ``cielo``, ``terreno``, ``edificios``,
``plaza`` (los pintores, verbatim) y ``composicion`` (atlas, contact sheet y
``main``). El orden de importacion de los temas ES el orden de registro de
``TILES``, y ese orden es el layout del atlas: no reordenar estos imports.
"""
from __future__ import annotations

# isort: off
# El orden de importacion de los temas ES el orden de registro de TILES, y ese
# orden es el layout del atlas: isort lo reordena alfabeticamente y rompe el
# contrato (lo cazo dos veces en AUD-345: el test dorado del atlas falla).
from . import cielo  # noqa: F401  (el import registra los tiles)
from . import terreno  # noqa: F401
from . import edificios  # noqa: F401
from . import plaza  # noqa: F401
# isort: on
from .composicion import (  # noqa: F401
    CONTACT_DIR,
    CONTACT_PNG,
    GAME_ROOT,
    LAB_ROOT,
    OUT_PNG,
    _build_contact_sheet,
    _compose_atlas,
    main,
)
from .core import (  # noqa: F401
    BLACK,
    COLS,
    NAME_TO_INDEX,
    TILE,
    TILES,
    DrawFn,
    _register,
    register_block,
    tile,
)
