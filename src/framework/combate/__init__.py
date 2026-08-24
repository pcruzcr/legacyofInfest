"""Reglas de combate compartidas — AUD-387.

De momento sólo los canales de daño (`dano`). El paquete existe porque lo que
viene después —efectos temporales, armadura— es la misma familia de reglas, y
tenerlas colgando de `stage/collision_system.py` las ataría al módulo que
arbitra hitboxes, que es otra cosa.
"""
from src.framework.combate import dano

__all__ = ["dano"]
