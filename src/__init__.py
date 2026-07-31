"""
Legacy of InFest — Educational Game Engine for Computer Graphics.

La versión vive en `pyproject.toml` y **sólo** ahí (AUD-105). Aquí se lee del
paquete instalado; si el proyecto se ejecuta desde el árbol de fuentes sin
instalar —que es lo normal en un aula—, se cae a leer el propio
`pyproject.toml`.

Por qué no una constante escrita a mano
---------------------------------------
Porque entonces habría dos, y acabarían diciendo cosas distintas. Es
exactamente lo que pasó: `pyproject.toml` declaraba `2.0.0` mientras el
producto entregable era de la línea 1.x, probablemente porque alguien copió
la versión de un documento —`50_IMPROVEMENT_ROADMAP.md` lleva su propia
cabecera `Version: 4.0.0`—.

Una versión equivocada no es cosmética: un estudiante que abre una incidencia
diciendo «me pasa en la 2.0.0» describe algo que no existe, y nadie puede
reproducirlo.
"""
from __future__ import annotations

__all__ = ["__version__", "version"]


def _leer_version() -> str:
    """La versión declarada en `pyproject.toml`, esté instalado o no."""
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _version_instalada

    try:
        return _version_instalada("legacyofinfest")
    except PackageNotFoundError:
        pass

    # Ejecutando desde el árbol de fuentes sin `pip install -e .`, que es el
    # caso normal en un aula. Se lee el fichero directamente.
    import re
    from pathlib import Path

    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    try:
        texto = pyproject.read_text(encoding="utf-8")
    except OSError:
        return "0.0.0+desconocida"

    # Sólo la clave `version` de la sección `[project]`: `requires-python` y
    # las dependencias también contienen la palabra.
    seccion = texto.split("[project]", 1)[-1].split("\n[", 1)[0]
    encontrado = re.search(r'^version\s*=\s*"([^"]+)"', seccion, re.M)
    return encontrado.group(1) if encontrado else "0.0.0+desconocida"


#: Versión del producto. Línea 1.x; la 2.0.0 es la planificada en el roadmap.
__version__: str = _leer_version()


def version() -> str:
    """La versión del producto, para quien prefiera una función."""
    return __version__
