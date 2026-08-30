"""
Registro de handlers para objetos Tiled — Factory Registry.

Antes: `ObjetosDeTiled._process_objects` era una cadena de 27 `if/elif`
que mapeaba `obj_type` → `_handle_*`. Añadir un tipo exigía editar la clase,
rompiendo OCP, y el método medía 130 líneas.

Ahora: cada handler se registra con `@register("Type")` y el despachador
hace `registry[type](stage, obj, props)`. Añadir un tipo = nuevo módulo
con decorador, sin tocar el despachador.

Patrón: Factory Method + Registry (Open/Closed)
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

# AUD-729: Callable[..., Any] permite handlers que son @classmethod
# (reciben `cls`), que devuelven TmxObjectProblem | None (BossSpawn)
# o que aceptan `obj_type` extra (Cerradura/Buddy). El registro sólo
# mapea nombre → callable; la validación de firma es runtime.
Handler = Callable[..., Any]

_REGISTRY: dict[str, Handler] = {}


def register(*types: str) -> Callable[[Handler], Handler]:
    """Registra un handler para uno o varios `obj_type` de Tiled."""
    def decorator(fn: Handler) -> Handler:
        for t in types:
            _REGISTRY[t] = fn
        return fn
    return decorator


def get_handler(obj_type: str) -> Handler | None:
    return _REGISTRY.get(obj_type)


def all_types() -> list[str]:
    return sorted(_REGISTRY)

def _ensure_registered() -> None:
    """Fuerza el registro de handlers si aún no se hizo."""
    if _REGISTRY:
        return
    try:
        import src.framework.stage.stage_objetos  # noqa: F401
    except Exception:
        pass
