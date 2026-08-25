"""Migra literales antiguos a claves canónicas en las escenas restantes (AUD-618)."""
from pathlib import Path

REEMPLAZOS = {
    "src/engine/scenes/color_theory_scene.py": [
        ('_("SHIFT to toggle step-by-step algorithm")',
         '_("ui.color_theory.shift_toggle")'),
    ],
    "src/engine/scenes/combo_demo_scene.py": [
        ('self._hit_log = [_("Press Z (light) or X (heavy)"]',
         'self._hit_log = [_("ui.combo.press_z_x")]'),
        ('label = _("Light") if atk_type == "SHORT" else _("Heavy")',
         'label = _("ui.combo.light") if atk_type == "SHORT" else _("ui.combo.heavy")'),
        ('draw_top_bar(surface, _("COMBO STATE MACHINE"), "Demo")',
         'draw_top_bar(surface, _("ui.combo_state_machine"), _("ui.demo"))'),
        ('title = self._font_medium.render(_("Chain: Z \u2192 Z \u2192 X"), True, COLOR_HIGHLIGHT)',
         'title = self._font_medium.render(_("ui.combo.chain"), True, COLOR_HIGHLIGHT)'),
        ('label = self._font_small.render(_("Combo window"), True, COLOR_TEXT)',
         'label = self._font_small.render(_("ui.combo.window"), True, COLOR_TEXT)'),
        ('count_str = _("Combo: x{count}").format(count=self._combo_count)',
         'count_str = _("ui.combo.x").format(count=self._combo_count)'),
        ('count_str = _("Combo: \u2014")',
         'count_str = _("ui.combo.none")'),
        ('mult_txt = self._font_medium.render(_("Multiplier: {mult}x").format(mult=mult), True, COLOR_ACCENT)',
         'mult_txt = self._font_medium.render(_("ui.combo.multiplier").format(mult=mult), True, COLOR_ACCENT)'),
        ('draw_bottom_bar(surface, _("Z: Light | X: Heavy | ESC: Back"))',
         'draw_bottom_bar(surface, _("ui.hints.light_heavy"))'),
    ],
    "src/engine/scenes/pattern_demo_scene.py": [
        ('MODE_NAMES = [\n    _("INFERENCE"),\n    _("FEATURE_COMPARE"),\n    _("CLASS_GRID"),\n    _("CONFUSION"),\n    _("PIPELINE"),\n    _("TREE_VIEW"),\n]',
         'MODE_NAMES = [\n    _("ui.pattern_demo.modes.inference"),\n    _("ui.pattern_demo.modes.feature_compare"),\n    _("ui.pattern_demo.modes.class_grid"),\n    _("ui.pattern_demo.modes.confusion"),\n    _("ui.pattern_demo.modes.pipeline"),\n    _("ui.pattern_demo.modes.tree_view"),\n]'),
        ('src_label = self._font_small.render(_("Source Feature Vector:"), True, COLOR_ACCENT)',
         'src_label = self._font_small.render(_("ui.pattern_demo.labels.source_feature_vector"), True, COLOR_ACCENT)'),
        ('nrst_label = self._font_small.render(_("Nearest Training Sample:"), True, COLOR_ACCENT)',
         'nrst_label = self._font_small.render(_("ui.pattern_demo.labels.nearest_training_sample"), True, COLOR_ACCENT)'),
        ('msg = self._font_small.render(_("No tree structure available for this model"), True, COLOR_TEXT)',
         'msg = self._font_small.render(_("ui.pattern_demo.labels.no_tree_structure"), True, COLOR_TEXT)'),
    ],
    "src/engine/scenes/vision_demo_scene.py": [
        ('MODE_NAMES = [\n    _("THRESHOLD"),\n    _("OTSU"),\n    _("ERODE"),\n    _("DILATE"),\n    _("OPEN"),\n    _("CLOSE"),\n    _("COMPONENTS"),\n    _("REGIONS"),\n    _("WATERSHED"),\n    _("FEATURES"),\n]',
         'MODE_NAMES = [\n    _("ui.vision_demo.modes.threshold"),\n    _("ui.vision_demo.modes.otsu"),\n    _("ui.vision_demo.modes.erode"),\n    _("ui.vision_demo.modes.dilate"),\n    _("ui.vision_demo.modes.open"),\n    _("ui.vision_demo.modes.close"),\n    _("ui.vision_demo.modes.components"),\n    _("ui.vision_demo.modes.regions"),\n    _("ui.vision_demo.modes.watershed"),\n    _("ui.vision_demo.modes.features"),\n]'),
        ('hint = self._font_overlay_small.render(_("Press I to close intermediate view"), True, (100, 100, 140))',
         'hint = self._font_overlay_small.render(_("ui.vision_demo.press_i_close"), True, (100, 100, 140))'),
    ],
    "src/engine/scenes/quiz_system.py": [
        ('"question": _("No questions loaded"),',
         '"question": _("ui.quiz.no_questions"),'),
        ('title = self._font_answer.render(_("QUIZ"), True, COLOR_HIGHLIGHT)',
         'title = self._font_answer.render(_("ui.quiz"), True, COLOR_HIGHLIGHT)'),
    ],
}

for relativo, pares in REEMPLAZOS.items():
    ruta = Path(relativo)
    if not ruta.exists():
        print(f"NO EXISTE: {relativo}")
        continue
    contenido = ruta.read_text(encoding="utf-8")
    total = 0
    for viejo, nuevo in pares:
        n = contenido.count(viejo)
        if n:
            contenido = contenido.replace(viejo, nuevo)
            total += n
        else:
            print(f"  no encontrado en {ruta.name}: {viejo[:60]}...")
    ruta.write_text(contenido, encoding="utf-8")
    print(f"{ruta.name}: {total} reemplazos")
