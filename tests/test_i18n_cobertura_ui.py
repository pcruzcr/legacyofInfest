"""
AUD-613 — todo texto visible de UI pasa por i18n (_()).

La decisión del dueño (CLAUDE.md, 2026-08-11) es español único.
Cualquier literal que el jugador vea en pantalla debe estar en locale/es.json.
"""
from __future__ import annotations

import re
from pathlib import Path

from src.engine.core.i18n import cargar_del_disco

RAIZ = Path(__file__).resolve().parent.parent

# Strings que el auditoría identificó como visibles y sin _()
STRINGS_ESPERADOS: set[str] = {
    # keybinding_scene.py _ACTION_LABELS
    "Move Left",
    "Move Right",
    "Move Up",
    "Move Down",
    "Jump",
    "Crouch",
    "Attack (Short)",
    "Attack (Long)",
    "Dash",
    "Grab",
    "Confirm",
    "Cancel",
    "Pause",
    # vector_lab_scene.py MODE_NAMES
    "FREE MOVE",
    "CHASE (normalized)",
    "ORBIT (dot product)",
    "DISTANCE CHECK",
    # vector_lab_scene.py VECTOR_QUIZZES
    "What does Vector2.normalize() return?",
    "A zero vector",
    "A unit vector (length=1)",
    "The vector scaled by 2",
    "The vector's angle",
    "What is the dot product of two perpendicular vectors?",
    "1",
    "0",
    "Their product",
    "Undefined",
    "What curve uses 4 control points?",
    "Linear",
    "Quadratic Bezier",
    "Cubic Bezier",
    "Catmull-Rom",
    "What does distance() between two points return?",
    "The straight-line length",
    "The X difference",
    "The Y difference",
    "The sum of coordinates",
    "What does a normalized vector represent?",
    "Magnitude only",
    "Direction only",
    "Position only",
    "Speed only",
    "What is cos(90 degrees)?",
    "-1",
    "0.5",
    # achievements.py:513
    "Achievement Unlocked: {name}",
    # color_theory_scene.py MODE_NAMES
    "RGB EXPLORER",
    "HSV EXPLORER",
    "HSL EXPLORER",
    "CMYK EXPLORER",
    "ALPHA BLEND",
    "CHALLENGE",
    # color_theory_scene.py hints
    "SHIFT to toggle step-by-step algorithm",
    # combo_demo_scene.py
    "Press Z (light) or X (heavy)",
    "Light",
    "Heavy",
    "COMBO STATE MACHINE",
    "Chain: Z \u2192 Z \u2192 X",
    "Combo window",
    "Combo: x{count}",
    "Combo: \u2014",
    "Multiplier: {mult}x",
    # pattern_demo_scene.py MODE_NAMES
    "INFERENCE",
    "FEATURE_COMPARE",
    "CLASS_GRID",
    "CONFUSION",
    "PIPELINE",
    "TREE_VIEW",
    # pattern_demo_scene.py labels
    "Source Feature Vector:",
    "Nearest Training Sample:",
    "No tree structure available for this model",
    # vision_demo_scene.py MODE_NAMES
    "THRESHOLD",
    "OTSU",
    "ERODE",
    "DILATE",
    "OPEN",
    "CLOSE",
    "COMPONENTS",
    "REGIONS",
    "WATERSHED",
    "FEATURES",
    # vision_demo_scene.py hint
    "Press I to close intermediate view",
    # quiz_system.py
    "No questions loaded",
    "QUIZ",
    "  {current}/{total}  |  Score: {score}",
}


def _literales_en_archivo(ruta: Path) -> set[str]:
    """Extrae literales de cadena simples de un archivo Python."""
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    # Busca "..." o '...' que no sean f-strings ni docstrings
    patron = re.compile(r'(?<!f)"((?:[^"\\]|\\.)*)"|(?<!f)\'((?:[^\'\\]|\\.)*)\'')
    literales = set()
    for m in patron.finditer(texto):
        val = m.group(1) if m.group(1) is not None else m.group(2)
        if val and not val.startswith(("{", "%", " ", "\n")) and len(val) > 1:
            literales.add(val)
    return literales


def test_todos_los_strings_ui_estan_en_catalogo_es() -> None:
    """Cada string visible identificado debe tener entrada en es.json."""
    cat_es = cargar_del_disco("es")
    faltantes = sorted(s for s in STRINGS_ESPERADOS if s not in cat_es)
    assert not faltantes, (
        f"{len(faltantes)} strings visibles sin entrada en locale/es.json:\n"
        + "\n".join(f"  {s!r}" for s in faltantes)
    )


def test_todos_los_strings_ui_estan_en_catalogo_en() -> None:
    """Cada string visible debe tener traducción en en.json."""
    cat_en = cargar_del_disco("en")
    faltantes = sorted(s for s in STRINGS_ESPERADOS if s not in cat_en)
    assert not faltantes, (
        f"{len(faltantes)} strings visibles sin entrada en locale/en.json:\n"
        + "\n".join(f"  {s!r}" for s in faltantes)
    )


def test_los_8_archivos_auditados_importan_i18n() -> None:
    """Cada uno de los 8 archivos auditados debe importar _ de i18n."""
    archivos = [
        "src/engine/scenes/keybinding_scene.py",
        "src/engine/scenes/vector_lab_scene.py",
        "src/engine/core/achievements.py",
        "src/engine/scenes/color_theory_scene.py",
        "src/engine/scenes/combo_demo_scene.py",
        "src/engine/scenes/pattern_demo_scene.py",
        "src/engine/scenes/vision_demo_scene.py",
        "src/engine/scenes/quiz_system.py",
    ]
    for rel in archivos:
        ruta = RAIZ / rel
        assert ruta.exists(), f"{rel} no existe"
        texto = ruta.read_text(encoding="utf-8")
        assert "from src.engine.core.i18n import _" in texto, (
            f"{rel} no importa _ de i18n"
        )