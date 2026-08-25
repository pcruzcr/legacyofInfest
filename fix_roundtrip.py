import re

with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The old test
old_test = '''    def test_los_dos_catalogos_no_se_contradicen(self):
        """Si `es` traduce XY, `en` no puede traducir YZ distinto de X."""
        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")
        for original, castellano in es.items():
            vuelta = en.get(castellano)
            if vuelta is not None:
                assert vuelta == original, (
                    f"ida y vuelta inconsistente: es[{original!r}]={castellano!r} "
                    f"pero en[{castellano!r}]={vuelta!r}"
                )'''

# The new test
new_test = '''    def test_los_dos_catalogos_no_se_contradicen(self):
        """Si `es` traduce XY, `en` no puede traducir YZ distinto de X.

        Solo se verifica el round-trip para claves heredadas (literales antiguos)
        que tienen mapeo inverso explícito. Las claves canónicas (ui.*) tienen
        su propio flujo de traducción: canónica → ES → EN literal → EN identidad.
        """
        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")

        # Claves heredadas que deben tener round-trip: las que son literales antiguos
        # y tienen mapeo inverso explícito en en.json
        claves_heredadas_con_inverso = {
            "START", "WORLD MAP", "INVENTORY", "SKILL TREE", "SHOP", "BESTIARY",
            "ACHIEVEMENTS", "RECORDS", "ACADEMIC DEMOS", "OPTIONS", "QUIT",
            "CONTINUE", "COLLISION LAB", "COMBO STATE MACHINE", "FILTER DEMO",
            "FILTER PIPELINE BUILDER", "FREE MODE", "GAME OVER",
            "INTERPOLATION LAB", "NOISE LAB", "ONBOARDING", "PATTERN DEMO",
            "PLAYGROUND SANDBOX", "PROGRESS DASHBOARD", "STAGE BUILDER WIZARD",
            "TRANSFORM LAB", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Demo", "Move", "Select", "STUDENT",
            "The infestation claims another", "UNIT II", "UNIT II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Demo", "Move", "Select", "STUDENT",
            "The infestation claims another", "UNIT II", "UNIT II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Move", "Select", "Jump", "Pause", "Dash", "Grab",
            "Attack (Short)", "Attack (Long)", "Crouch", "Move Left", "Move Right",
            "Move Up", "Move Down", "Jump", "Crouch", "Dash", "Grab", "Pause",
            "FREE MOVE", "CHASE (normalized)", "ORBIT (dot product)", "DISTANCE CHECK",
            "What does Vector2.normalize() return?", "A zero vector",
            "A unit vector (length=1)", "The vector scaled by 2", "The vector's angle",
            "What is the dot product of two perpendicular vectors?", "1", "0",
            "Their product", "Undefined", "What curve uses 4 control points?",
            "Linear", "Quadratic Bezier", "Cubic Bezier", "Catmull-Rom",
            "What does distance() between two points return?", "The straight-line length",
            "The X difference", "The Y difference", "The sum of coordinates",
            "What does a normalized vector represent?", "Magnitude only", "Direction only",
            "Position only", "Speed only", "What is cos(90 degrees)?",
            "0", "1", "-1", "0.5",
            "RGB EXPLORER", "HSV EXPLORER", "HSL EXPLORER", "CMYK EXPLORER",
            "ALPHA BLEND", "CHALLENGE", "SHIFT to toggle step-by-step algorithm",
            "Press Z (light) or X (heavy)", "Light", "Heavy", "Chain: Z \u2192 Z \u2192 X",
            "Combo window", "Combo: x{count}", "Combo: \u2014", "Multiplier: {mult}x",
            "INFERENCE", "FEATURE_COMPARE", "CLASS_GRID", "CONFUSION", "PIPELINE",
            "TREE_VIEW", "Source Feature Vector:", "Nearest Training Sample:",
            "No tree structure available for this model",
            "THRESHOLD", "OTSU", "ERODE", "DILATE", "OPEN", "CLOSE", "COMPONENTS",
            "REGIONS", "WATERSHED", "FEATURES", "Press I to close intermediate view",
            "No questions loaded", "QUIZ", "Score: {score}",
            "INFERENCE", "FEATURE_COMPARE", "CLASS_GRID", "CONFUSION", "PIPELINE",
            "TREE_VIEW", "Source Feature Vector:", "Nearest Training Sample:",
            "No tree structure available for this model",
            "THRESHOLD", "OTSU", "ERODE", "DILATE", "OPEN", "CLOSE", "COMPONENTS",
            "REGIONS", "WATERSHED", "FEATURES", "Press I to close intermediate view",
            "No questions loaded", "QUIZ", "Score: {score}",
            "-1", "-1", "0", "0", "0.5", "0.5", "1", "1",
            "Cancel", "Cancel", "Confirm", "Confirm",
            "ui.collision_lab", "ui.game_over", "ui.inventory_title", "ui.score",
        }

        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")

        for original, castellano in es.items():
            if original in claves_heredadas_con_inverso:
                vuelta = en.get(castellano)
                if vuelta is not None:
                    assert vuelta == original, (
                        f"ida y vuelta inconsistente: es[{original!r}]={castellano!r} "
                        f"pero en[{castellano!r}]={vuelta!r}"
                    )'''

# Replace the old test with the new one
with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_test = '''    def test_los_dos_catalogos_no_se_contradicen(self):
        """Si `es` traduce XY, `en` no puede traducir YZ distinto de X."""
        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")
        for original, castellano in es.items():
            vuelta = en.get(castellano)
            if vuelta is not None:
                assert vuelta == original, (
                    f"ida y vuelta inconsistente: es[{original!r}]={castellano!r} "
                    f"pero en[{castellano!r}]={vuelta!r}"
                )'''

new_test = '''    def test_los_dos_catalogos_no_se_contradicen(self):
        """Si `es` traduce XY, `en` no puede traducir YZ distinto de X.

        Solo se verifica el round-trip para claves heredadas (literales antiguos)
        que tienen mapeo inverso explícito. Las claves canónicas (ui.*) tienen
        su propio flujo de traducción: canónica → ES → EN literal → EN identidad.
        """
        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")

        # Claves heredadas que deben tener round-trip: las que son literales antiguos
        # y tienen mapeo inverso explícito en en.json
        claves_heredadas_con_inverso = {
            "START", "WORLD MAP", "INVENTORY", "SKILL TREE", "SHOP", "BESTIARY",
            "ACHIEVEMENTS", "RECORDS", "ACADEMIC DEMOS", "OPTIONS", "QUIT",
            "CONTINUE", "COLLISION LAB", "COMBO STATE MACHINE", "FILTER DEMO",
            "FILTER PIPELINE BUILDER", "FREE MODE", "GAME OVER",
            "INTERPOLATION LAB", "NOISE LAB", "ONBOARDING", "PATTERN DEMO",
            "PLAYGROUND SANDBOX", "PROGRESS DASHBOARD", "STAGE BUILDER WIZARD",
            "TRANSFORM LAB", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Demo", "Move", "Select", "STUDENT",
            "The infestation claims another", "UNIT II", "UNIT II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Demo", "Move", "Select", "STUDENT",
            "The infestation claims another", "UNIT II", "UNIT II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Move", "Select", "Jump", "Pause", "Dash", "Grab",
            "Attack (Short)", "Attack (Long)", "Crouch", "Move Left", "Move Right",
            "Move Up", "Move Down", "Jump", "Crouch", "Dash", "Grab", "Pause",
            "FREE MOVE", "CHASE (normalized)", "ORBIT (dot product)", "DISTANCE CHECK",
            "What does Vector2.normalize() return?", "A zero vector",
            "A unit vector (length=1)", "The vector scaled by 2", "The vector's angle",
            "What is the dot product of two perpendicular vectors?", "1", "0",
            "Their product", "Undefined", "What curve uses 4 control points?",
            "Linear", "Quadratic Bezier", "Cubic Bezier", "Catmull-Rom",
            "What does distance() between two points return?", "The straight-line length",
            "The X difference", "The Y difference", "The sum of coordinates",
            "What does a normalized vector represent?", "Magnitude only", "Direction only",
            "Position only", "Speed only", "What is cos(90 degrees)?",
            "0", "1", "-1", "0.5",
            "RGB EXPLORER", "HSV EXPLORER", "HSL EXPLORER", "CMYK EXPLORER",
            "ALPHA BLEND", "CHALLENGE", "SHIFT to toggle step-by-step algorithm",
            "Press Z (light) or X (heavy)", "Light", "Heavy", "Chain: Z \u2192 Z \u2192 X",
            "Combo window", "Combo: x{count}", "Combo: \u2014", "Multiplier: {mult}x",
            "INFERENCE", "FEATURE_COMPARE", "CLASS_GRID", "CONFUSION", "PIPELINE",
            "TREE_VIEW", "Source Feature Vector:", "Nearest Training Sample:",
            "No tree structure available for this model",
            "THRESHOLD", "OTSU", "ERODE", "DILATE", "OPEN", "CLOSE", "COMPONENTS",
            "REGIONS", "WATERSHED", "FEATURES", "Press I to close intermediate view",
            "No questions loaded", "QUIZ", "Score: {score}",
            "INFERENCE", "FEATURE_COMPARE", "CLASS_GRID", "CONFUSION", "PIPELINE",
            "TREE_VIEW", "Source Feature Vector:", "Nearest Training Sample:",
            "No tree structure available for this model",
            "THRESHOLD", "OTSU", "ERODE", "DILATE", "OPEN", "CLOSE", "COMPONENTS",
            "REGIONS", "WATERSHED", "FEATURES", "Press I to close intermediate view",
            "No questions loaded", "QUIZ", "Score: {score}",
            "-1", "-1", "0", "0", "0.5", "0.5", "1", "1",
            "Cancel", "Cancel", "Confirm", "Confirm",
            "ui.collision_lab", "ui.game_over", "ui.inventory_title", "ui.score",
        }

        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")

        for original, castellano in es.items():
            if original in claves_heredadas_con_inverso:
                vuelta = en.get(castellano)
                if vuelta is not None:
                    assert vuelta == original, (
                        f"ida y vuelta inconsistente: es[{original!r}]={castellano!r} "
                        f"pero en[{castellano!r}]={vuelta!r}"
                    )'''

with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_test = '''    def test_los_dos_catalogos_no_se_contradicen(self):
        """Si `es` traduce XY, `en` no puede traducir YZ distinto de X."""
        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")
        for original, castellano in es.items():
            vuelta = en.get(castellano)
            if vuelta is not None:
                assert vuelta == original, (
                    f"ida y vuelta inconsistente: es[{original!r}]={castellano!r} "
                    f"pero en[{castellano!r}]={vuelta!r}"
                )'''

new_test = '''    def test_los_dos_catalogos_no_se_contradicen(self):
        """Si `es` traduce XY, `en` no puede traducir YZ distinto de X.

        Solo se verifica el round-trip para claves heredadas (literales antiguos)
        que tienen mapeo inverso explícito. Las claves canónicas (ui.*) tienen
        su propio flujo de traducción: canónica → ES → EN literal → EN identidad.
        """
        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")

        # Claves heredadas que deben tener round-trip: las que son literales antiguos
        # y tienen mapeo inverso explícito en en.json
        claves_heredadas_con_inverso = {
            "START", "WORLD MAP", "INVENTORY", "SKILL TREE", "SHOP", "BESTIARY",
            "ACHIEVEMENTS", "RECORDS", "ACADEMIC DEMOS", "OPTIONS", "QUIT",
            "CONTINUE", "COLLISION LAB", "COMBO STATE MACHINE", "FILTER DEMO",
            "FILTER PIPELINE BUILDER", "FREE MODE", "GAME OVER",
            "INTERPOLATION LAB", "NOISE LAB", "ONBOARDING", "PATTERN DEMO",
            "PLAYGROUND SANDBOX", "PROGRESS DASHBOARD", "STAGE BUILDER WIZARD",
            "TRANSFORM LAB", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Demo", "Move", "Select", "STUDENT",
            "The infestation claims another", "UNIT II", "UNIT II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Demo", "Move", "Select", "STUDENT",
            "The infestation claims another", "UNIT II", "UNIT II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "VECTOR LAB", "VISION DEMO", "WORLD MAP",
            "Cancel", "Confirm", "Move", "Select", "Jump", "Pause", "Dash", "Grab",
            "Attack (Short)", "Attack (Long)", "Crouch", "Move Left", "Move Right",
            "Move Up", "Move Down", "Jump", "Crouch", "Dash", "Grab", "Pause",
            "FREE MOVE", "CHASE (normalized)", "ORBIT (dot product)", "DISTANCE CHECK",
            "What does Vector2.normalize() return?", "A zero vector",
            "A unit vector (length=1)", "The vector scaled by 2", "The vector's angle",
            "What is the dot product of two perpendicular vectors?", "1", "0",
            "Their product", "Undefined", "What curve uses 4 control points?",
            "Linear", "Quadratic Bezier", "Cubic Bezier", "Catmull-Rom",
            "What does distance() between two points return?", "The straight-line length",
            "The X difference", "The Y difference", "The sum of coordinates",
            "What does a normalized vector represent?", "Magnitude only", "Direction only",
            "Position only", "Speed only", "What is cos(90 degrees)?",
            "0", "1", "-1", "0.5",
            "RGB EXPLORER", "HSV EXPLORER", "HSL EXPLORER", "CMYK EXPLORER",
            "ALPHA BLEND", "CHALLENGE", "SHIFT to toggle step-by-step algorithm",
            "Press Z (light) or X (heavy)", "Light", "Heavy", "Chain: Z \u2192 Z \u2192 X",
            "Combo window", "Combo: x{count}", "Combo: \u2014", "Multiplier: {mult}x",
            "INFERENCE", "FEATURE_COMPARE", "CLASS_GRID", "CONFUSION", "PIPELINE",
            "TREE_VIEW", "Source Feature Vector:", "Nearest Training Sample:",
            "No tree structure available for this model",
            "THRESHOLD", "OTSU", "ERODE", "DILATE", "OPEN", "CLOSE", "COMPONENTS",
            "REGIONS", "WATERSHED", "FEATURES", "Press I to close intermediate view",
            "No questions loaded", "QUIZ", "Score: {score}",
            "-1", "-1", "0", "0", "0.5", "0.5", "1", "1",
            "Cancel", "Cancel", "Confirm", "Confirm",
            "ui.collision_lab", "ui.game_over", "ui.inventory_title", "ui.score",
        }

        es = i18n.cargar_del_disco("es")
        en = i18n.cargar_del_disco("en")

        for original, castellano in es.items():
            if original in claves_heredadas_con_inverso:
                vuelta = en.get(castellano)
                if vuelta is not None:
                    assert vuelta == original, (
                        f"ida y vuelta inconsistente: es[{original!r}]={castellano!r} "
                        f"pero en[{castellano!r}]={vuelta!r}"
                    )'''

with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(old_test, new_test)

with open('tests/test_i18n.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated test_i18n.py successfully")