"""Prueba del gate de seguridad ante cambios — CLAUDE.md §3.9."""

import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "check_change_safety.py"
MATRIZ = RAIZ / "docs" / "AUD-800_REGRESSION_MATRIX.md"
GUIA = RAIZ / "docs" / "CHANGE_SAFETY_GUIDE.md"
CLAUDE = RAIZ / "CLAUDE.md"


def test_script_existe_y_es_ejecutable():
    assert SCRIPT.exists(), "scripts/check_change_safety.py no existe"
    # Debe parsear sin error con --help
    out = subprocess.check_output([sys.executable, str(SCRIPT), "--help"], text=True)
    assert "CHANGE SAFETY" in out or "change" in out.lower()


def test_matriz_existe_y_tiene_cert():
    assert MATRIZ.exists()
    txt = MATRIZ.read_text(encoding="utf-8")
    assert "CERT-RENDERER" in txt
    assert "CERT-HUD" in txt
    assert "scripts/check_change_safety.py" in txt


def test_guia_existe_y_describe_invariante():
    assert GUIA.exists()
    txt = GUIA.read_text(encoding="utf-8")
    assert "Toda modificación futura debe demostrar qué certificación afecta" in txt
    assert "CERT-HUD" in txt
    assert "check_change_safety.py" in txt


def test_claude_contiene_invariante_9():
    txt = CLAUDE.read_text(encoding="utf-8")
    assert "Toda modificación futura debe demostrar qué certificación afecta" in txt
    assert "AUD-800_REGRESSION_MATRIX.md" in txt
    assert "CHANGE_SAFETY_GUIDE.md" in txt
    assert "check_change_safety.py" in txt


def test_script_mapea_hud():
    # Simula mapeo: hud.py debe dar CERT-HUD
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_change_safety", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]

    mapa = mod.mapear_ficheros(["src/engine/ui/hud.py"])
    assert "HUD" in mapa
    assert mapa["HUD"]["cert"] == "CERT-HUD"
    assert any("test_hud" in c for c in mapa["HUD"]["regresiones"])


def test_script_mapea_renderer():
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_change_safety2", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]

    mapa = mod.mapear_ficheros(["src/engine/render/gl_pipeline.py"])
    assert "RENDERER" in mapa
    assert mapa["RENDERER"]["cert"] == "CERT-RENDERER"


def test_script_sin_cambios_no_falla():
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_change_safety3", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]

    ok, msg = mod.verificar_trazabilidad({})
    assert ok
    assert "sin familias" in msg.lower() or "sin" in msg.lower()


def test_ci_no_exige_docs_puro():
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_change_safety4", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]

    mapa = mod.mapear_ficheros(["docs/CHANGE_SAFETY_GUIDE.md"])
    # DOCS puro no exige trazabilidad según verificar_trazabilidad
    ok, _ = mod.verificar_trazabilidad(mapa)
    assert ok
