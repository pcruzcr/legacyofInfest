"""
Module: test_dependencias_que_se_usan
System: tests
Academic Unit: N/A

AUD-235 — una dependencia obligatoria que nadie importa.

`pyproject.toml` pedía `pymunk>=6.6`, y **ningún fichero de `src/` lo
importaba**. Venía de `collision_system.py`, que construía un `pymunk.Space`
con cero cuerpos y llamaba a `step()` cada fotograma para integrar un mundo
vacío. La simulación se retiró; la dependencia se quedó.

Por qué esto es un defecto y no una molestia
--------------------------------------------
pymunk es una extensión en C. Este proyecto ya se quedó **sin poder
instalarse en Python 3.13** por una rueda que no existía (AUD-173), y la
matriz de CI declara 3.11 / 3.12 / 3.13. Cada dependencia obligatoria que
nadie usa es otra rueda que puede faltar el día que salga la siguiente versión
de Python, otro compilador que puede fallar en la máquina de un estudiante, y
más megas de instalación — todo a cambio de nada.

`scripts/check_dependency_sync.py` ya vigila que `pyproject.toml` y
`requirements.txt` no se contradigan. Lo que no vigilaba nadie es que lo que
declaran **se use**. Eso es lo que hace esta prueba.

Qué NO comprueba
----------------
Los extras (`accel`, `scripting`, `audiotools`, `dev`) quedan fuera a
propósito: son opcionales por definición y el código los detecta con
`try/except ImportError`. Que `moderngl` no aparezca en un `import` de primer
nivel es exactamente lo que se espera de él.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

#: Distribución en PyPI -> módulo que se importa. Sólo las que no coinciden.
_MODULO_DE: dict[str, str] = {
    "pygame-ce": "pygame",
    "pygame-gui": "pygame_gui",
    "Pillow": "PIL",
    "opencv-python": "cv2",
    "scikit-learn": "sklearn",
    "scikit-image": "skimage",
    "PyYAML": "yaml",
    "python-dotenv": "dotenv",
}


def _dependencias_base() -> list[str]:
    """Los nombres de `[project].dependencies`, sin extras ni versiones."""
    txt = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    bloque = txt.split("dependencies = [", 1)[1].split("\n]", 1)[0]
    # Sólo las líneas que declaran un paquete: el bloque está lleno de
    # comentarios que explican por qué cada tope de versión existe.
    return re.findall(r'^\s*"([A-Za-z0-9_.\-]+)', bloque, re.M)


def _fuentes() -> dict[Path, str]:
    return {
        p: p.read_text(encoding="utf-8", errors="ignore")
        for p in (RAIZ / "src").rglob("*.py")
        if "__pycache__" not in str(p)
    }


def _quien_importa(modulo: str, fuentes: dict[Path, str]) -> list[Path]:
    """Ficheros que importan `modulo`, esté el import donde esté.

    La expresión no ancla al principio del fichero a propósito: varios
    módulos importan dentro de la función que los necesita —`vision_tools`
    trae `skimage` así— para no pagar la carga en el arranque. Un escáner que
    sólo mirase la cabecera daría por muerto lo que sí se usa.
    """
    pat = re.compile(
        rf"^\s*(?:import\s+{re.escape(modulo)}\b|from\s+{re.escape(modulo)}[\s.])",
        re.M,
    )
    return [p for p, t in fuentes.items() if pat.search(t)]


def test_toda_dependencia_obligatoria_se_importa_en_src() -> None:
    fuentes = _fuentes()
    huerfanas: list[str] = []
    for dist in _dependencias_base():
        modulo = _MODULO_DE.get(dist, dist.replace("-", "_"))
        if not _quien_importa(modulo, fuentes):
            huerfanas.append(f"{dist} (se importaría como `{modulo}`)")

    assert not huerfanas, (
        "estas dependencias son obligatorias y nadie las importa en `src/`:\n  "
        + "\n  ".join(huerfanas)
        + "\n\nO se usan, o se quitan, o se bajan a un extra opcional. Una "
        "dependencia de más es una forma más de que la instalación falle, y "
        "este repositorio ya se quedó sin Python 3.13 por eso (AUD-173).\n"
        "Si el nombre del módulo no coincide con el del paquete, añádelo a "
        "`_MODULO_DE` en este fichero."
    )


def test_el_escaner_encuentra_imports_dentro_de_funciones() -> None:
    """Si esto se rompiera, la prueba de arriba daría falsos positivos.

    `scikit-image` es el caso real: `vision_tools` lo importa dentro de tres
    funciones y en ningún sitio más.
    """
    assert _quien_importa("skimage", _fuentes()), (
        "el escáner ya no ve los imports diferidos; la prueba de arriba "
        "empezaría a pedir que se quiten dependencias que sí se usan"
    )


def test_pymunk_no_ha_vuelto() -> None:
    """El caso concreto que originó AUD-235."""
    assert "pymunk" not in _dependencias_base()
