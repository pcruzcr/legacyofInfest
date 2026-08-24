"""La física por contexto (AUD-333) y el resolutor de mundo (AUD-334).

Todo lo que toca la física de locomoción vive en `perfil.py` — el perfil es
el dato que un contexto o modo de juego declara y los integradores lo
consumen — y la resolución de colisión entera vive en `resolucion.py`,
como pasos puros que cualquier entidad compone con `resolver_movimiento`.
"""

from src.framework.physics.resolucion import (
    Contacto,
    EstadoDeMovimiento,
    resolver_movimiento,
)

__all__ = [
    "Contacto",
    "EstadoDeMovimiento",
    "resolver_movimiento",
]
