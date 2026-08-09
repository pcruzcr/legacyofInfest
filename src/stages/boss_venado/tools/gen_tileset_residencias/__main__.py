"""Entrada ``python -m src.stages.boss_venado.tools.gen_tileset_residencias``.

AUD-345 — el flujo de autor que documentaba el archivo original se ejecuta con
``python -m``; ``__main__`` solo llama a ``main`` (los registros ya corrieron al
importar el paquete).
"""
from __future__ import annotations

from .composicion import main

if __name__ == "__main__":
    main()
