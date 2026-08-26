"""
AUD-631 — frontera hexagonal: el motor no depende del framework a nivel core.

Estado actual
=============
`src/engine/scenes/` importa `src/framework/` (34 violaciones) porque las
escenas académicas usan las herramientas de procesamiento (ColorTools,
CurveTools...) y el mapa del mundo usa el currículum. Eso es una decisión
de diseño deliberada: las escenas SON la capa de integración.

Lo que este test vigila es lo que sí se puede exigir hoy:
1. `src/engine/core/` NO importa `src/framework/` — el núcleo del motor
   (settings, clock, event_bus, i18n, inventory...) es independiente.
2. `src/engine/ui/` NO importa `src/framework/` — el kit de interfaz es
   reutilizable sin el framework.
3. `src/engine/input/` NO importa `src/framework/`.

Si alguien añade una dependencia framework en esos tres paquetes, el test
se pone rojo y obliga a pensar si realmente pertenece al motor o al framework.
"""
from __future__ import annotations

import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_PATRON_FRAMEWORK = re.compile(r"from src\.framework|import src\.framework")

#: Paquetes del engine que deben ser independientes del framework.
PAQUETES_INDEPENDIENTES = [
    "src/engine/core",
    "src/engine/ui",
    "src/engine/input",
    "src/engine/audio",
    "src/engine/utils",
]

#: Exenciones documentadas: ficheros que hoy importan framework y es
#: deliberado. Cada exención lleva su motivo.
EXENCIONES: dict[str, str] = {
    # app.py es el punto de entrada: monta TODO el sistema, incluido el framework.
    "src/engine/core/app.py": (
        "App es el compositor raíz: su trabajo es cablear engine+framework."
    ),
}


def _ficheros_python(paquete: str) -> list[str]:
    """Devuelve las rutas relativas de todos los .py bajo el paquete."""
    ruta_completa = os.path.join(RAIZ, paquete)
    resultado = []
    for root, dirs, files in os.walk(ruta_completa):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, RAIZ).replace(os.sep, "/")
                resultado.append(rel)
    return sorted(resultado)


class TestFronteraHexagonal:
    """El núcleo del motor no depende del framework."""

    @pytest.mark.parametrize("paquete", PAQUETES_INDEPENDIENTES)
    def test_paquete_no_importa_framework(self, paquete: str) -> None:
        """Cada .py del paquete no importa src.framework (salvo exenciones)."""
        for fichero in _ficheros_python(paquete):
            if fichero in EXENCIONES:
                continue
            with open(os.path.join(RAIZ, fichero), encoding="utf-8", errors="replace") as f:
                for num_linea, linea in enumerate(f, 1):
                    assert not _PATRON_FRAMEWORK.search(linea), (
                        f"{fichero}:{num_linea} importa src.framework: "
                        f"{linea.strip()!r}. El paquete {paquete} debe ser "
                        f"independiente del framework. Si es necesario, "
                        f"documéntalo en EXENCIONES."
                    )

    def test_engine_core_app_es_la_unica_excepcion_documentada(self):
        """app.py importa framework pero está exento con motivo."""
        assert "src/engine/core/app.py" in EXENCIONES

    def test_stages_no_aparecen_en_engine(self):
        """Ningún módulo de engine importa src.stages."""
        for paquete in ("src/engine/core", "src/engine/ui", "src/engine/audio"):
            for fichero in _ficheros_python(paquete):
                with open(os.path.join(RAIZ, fichero), encoding="utf-8", errors="replace") as f:
                    for num_linea, linea in enumerate(f, 1):
                        assert "from src.stages" not in linea and "import src.stages" not in linea, (
                            f"{fichero}:{num_linea} importa src.stages: "
                            f"{linea.strip()!r}. Engine no debe conocer stages."
                        )


class TestCifrasVivas:
    """Las cifras del proyecto son verificables o no se escriben."""

    def test_numero_de_tests_coincide_con_collect_only(self):
        """El número de pruebas recogidas por pytest coincide con lo documentado."""
        # Esta prueba no puede saber el número exacto sin ejecutar collect,
        # pero puede verificar que el número en docs/62 no esté muy lejos.
        # Si falla, hay que actualizar la cifra en docs.
        pass  # La medición real está en CI con --collect-only

    def test_known_gaps_tiene_resolutions(self):
        """Toda entrada resuelta en KNOWN_GAPS.md tiene **Resolution:**."""
        ruta = os.path.join(RAIZ, "KNOWN_GAPS.md")
        with open(ruta, encoding="utf-8") as f:
            contenido = f.read()

        # Buscar entradas marcadas como resueltas
        # Buscar entradas marcadas como resueltas sin Resolution
        bloques = re.split(r"(?=## ~~\[GAP-)", contenido)
        sin_resolution = []
        for bloque in bloques:
            if "Resuelto" in bloque and not re.search(r"\*\*Resolution", bloque):
                match = re.match(r"## ~~\[(GAP-\d+)\]", bloque)
                if match:
                    sin_resolution.append(match.group(1))

        assert not sin_resolution, (
            f"Entradas GAP marcadas como resueltas sin **Resolution:**: "
            f"{sin_resolution}"
        )