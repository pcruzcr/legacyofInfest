"""
AUD-613 — todo texto visible de UI pasa por i18n (_()).

La decisión del dueño (CLAUDE.md, 2026-08-11) es español único.
Cualquier literal que el jugador vea en pantalla debe estar en locale/es.json.
"""
from __future__ import annotations

from pathlib import Path

from src.engine.core.i18n import aplanar_catalogo, cargar_del_disco

RAIZ = Path(__file__).resolve().parent.parent

# Claves canónicas que el auditoría identificó como visibles y deben estar en el catálogo
CANONICAL_KEYS_ESPERADAS: set[str] = {
    # keybinding_scene.py _ACTION_LABELS
    "ui.move_left",
    "ui.move_right",
    "ui.move_up",
    "ui.move_down",
    "ui.jump",
    "ui.crouch",
    "ui.attack_short",
    "ui.attack_long",
    "ui.dash",
    "ui.grab",
    "ui.confirm",
    "ui.cancel",
    "ui.pause",
    # vector_lab_scene.py MODE_NAMES
    "ui.vector_lab.modes.free_move",
    "ui.vector_lab.modes.chase",
    "ui.vector_lab.modes.orbit",
    "ui.vector_lab.modes.distance",
    # vector_lab_scene.py VECTOR_QUIZZES
    "ui.vector_lab.quiz.q1",
    "ui.vector_lab.quiz.q1_a",
    "ui.vector_lab.quiz.q1_b",
    "ui.vector_lab.quiz.q1_c",
    "ui.vector_lab.quiz.q1_d",
    "ui.vector_lab.quiz.q2",
    "ui.vector_lab.quiz.q2_a",
    "ui.vector_lab.quiz.q2_b",
    "ui.vector_lab.quiz.q2_c",
    "ui.vector_lab.quiz.q2_d",
    "ui.vector_lab.quiz.q3",
    "ui.vector_lab.quiz.q3_a",
    "ui.vector_lab.quiz.q3_b",
    "ui.vector_lab.quiz.q3_c",
    "ui.vector_lab.quiz.q3_d",
    "ui.vector_lab.quiz.q4",
    "ui.vector_lab.quiz.q4_a",
    "ui.vector_lab.quiz.q4_b",
    "ui.vector_lab.quiz.q4_c",
    "ui.vector_lab.quiz.q4_d",
    "ui.vector_lab.quiz.q5",
    "ui.vector_lab.quiz.q5_a",
    "ui.vector_lab.quiz.q5_b",
    "ui.vector_lab.quiz.q5_c",
    "ui.vector_lab.quiz.q5_d",
    "ui.vector_lab.quiz.q6",
    "ui.vector_lab.quiz.q6_a",
    "ui.vector_lab.quiz.q6_b",
    "ui.vector_lab.quiz.q6_c",
    "ui.vector_lab.quiz.q6_d",
    # achievements.py:513
    "ui.achievement_unlocked",
    # color_theory_scene.py MODE_NAMES
    "ui.color_theory_modes.rgb",
    "ui.color_theory_modes.hsv",
    "ui.color_theory_modes.hsl",
    "ui.color_theory_modes.cmyk",
    "ui.color_theory_modes.alpha",
    "ui.color_theory_modes.challenge",
    # color_theory_scene.py hints
    "ui.color_theory.shift_toggle",
    # combo_demo_scene.py
    "ui.combo.press_z_x",
    "ui.combo.light",
    "ui.combo.heavy",
    "ui.combo_state_machine",
    "ui.combo.chain",
    "ui.combo.window",
    "ui.combo.x",
    "ui.combo.none",
    "ui.combo.multiplier",
    # pattern_demo_scene.py MODE_NAMES
    "ui.pattern_demo.modes.inference",
    "ui.pattern_demo.modes.feature_compare",
    "ui.pattern_demo.modes.class_grid",
    "ui.pattern_demo.modes.confusion",
    "ui.pattern_demo.modes.pipeline",
    "ui.pattern_demo.modes.tree_view",
    # pattern_demo_scene.py labels
    "ui.pattern_demo.labels.source_feature_vector",
    "ui.pattern_demo.labels.nearest_training_sample",
    "ui.pattern_demo.labels.no_tree_structure",
    # vision_demo_scene.py MODE_NAMES
    "ui.vision_demo.modes.threshold",
    "ui.vision_demo.modes.otsu",
    "ui.vision_demo.modes.erode",
    "ui.vision_demo.modes.dilate",
    "ui.vision_demo.modes.open",
    "ui.vision_demo.modes.close",
    "ui.vision_demo.modes.components",
    "ui.vision_demo.modes.regions",
    "ui.vision_demo.modes.watershed",
    "ui.vision_demo.modes.features",
    # vision_demo_scene.py hint
    "ui.vision_demo.press_i_close",
    # quiz_system.py
    "ui.quiz.no_questions",
    "ui.quiz",
    "ui.score",
}


def _catalogo_plano(idioma: str) -> dict[str, str]:
    """Devuelve el catálogo aplanado para un idioma."""
    return aplanar_catalogo(cargar_del_disco(idioma))


def test_todos_los_strings_ui_estan_en_catalogo_es() -> None:
    """Cada clave canónica visible identificada debe tener entrada en es.json."""
    cat_es = _catalogo_plano("es")
    faltantes = sorted(k for k in CANONICAL_KEYS_ESPERADAS if k not in cat_es)
    assert not faltantes, (
        f"{len(faltantes)} claves canónicas visibles sin entrada en locale/es.json:\n"
        + "\n".join(f"  {s!r}" for s in faltantes)
    )


def test_todos_los_strings_ui_estan_en_catalogo_en() -> None:
    """Cada clave canónica visible debe tener traducción en en.json."""
    cat_en = _catalogo_plano("en")
    faltantes = sorted(k for k in CANONICAL_KEYS_ESPERADAS if k not in cat_en)
    assert not faltantes, (
        f"{len(faltantes)} claves canónicas visibles sin entrada en locale/en.json:\n"
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