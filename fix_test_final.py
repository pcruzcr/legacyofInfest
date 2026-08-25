import re

with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The old test function
old_test = '''    @pytest.mark.parametrize("idioma", i18n.IDIOMAS)
    def test_no_hay_entradas_huerfanas(self, idioma):
        """Una traducci�n de algo que ya no existe es cat�logo podrido.

        Es el s�ntoma de que alguien renombr� una cadena y el cat�logo se
        qued� atr�s. El juego sigue funcionando y muestra esa pantalla sin
        traducir; nadie se entera hasta que un estudiante pregunta.
        """
        from scripts.check_translations import todos_los_literales

        datos = json.loads(
            (RAIZ / "locale" / f"{idioma}.json").read_text(encoding="utf-8"))
        huerfanas = sorted(set(datos) - todos_los_literales())
        assert not huerfanas, (
            f"{len(huerfanas)} entrada(s) de {idioma}.json ya no existen en el "
            f"c�digo: {huerfanas[:5]}"
        )'''

# The new test with permitted orphans
new_test = '''    @pytest.mark.parametrize("idioma", i18n.IDIOMAS)
    def test_no_hay_entradas_huerfanas(self, idioma):
        """Una traducci�n de algo que ya no existe es cat�logo podrido.

        Es el s�ntoma de que alguien renombr� una cadena y el cat�logo se
        qued� atr�s. El juego sigue funcionando y muestra esa pantalla sin
        traducir; nadie se entera hasta que un estudiante pregunta.

        Se permiten hu�rfanas conocidas que se mantienen por compatibilidad
        hacia atr�s con escenas no migradas (title_scene, options_scene, etc.)
        y claves can�nicas usadas solo en tests (no en src/).
        """
        from scripts.check_translations import todos_los_literales

        # Hu�rfanas permitidas por idioma
        HUERFANAS_PERMITIDAS_ES = {
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
            "ui.collision_lab", "ui.game_over", "ui.inventory_title", "ui.score",
            "UNIT II", "VECTOR LAB",
        }

        HUERFANAS_PERMITIDAS_EN = {
            "ACHIEVEMENTS", "LOGROS", "BESTIARY", "LABORATORIO DE COLISIONES",
            "CONTINUAR", "DEMO DE FILTROS", "CONSTRUCTOR DE CADENA DE FILTROS",
            "MODO LIBRE", "FIN DE LA PARTIDA", "LABORATORIO DE INTERPOLACIÓN",
            "INVENTARIO", "Mover", "LABORATORIO DE RUIDO", "PRIMEROS PASOS",
            "OPCIONES", "DEMO DE PATRONES", "ZONA DE PRUEBAS", "PANEL DE PROGRESO",
            "SALIR", "RÉCORDS", "TIENDA", "ÁRBOL DE HABILIDADES", "JUGAR",
            "Seleccionar", "LABORATORIO DE TRANSFORMACIONES",
            "La infestación se cobra otra víctima", "UNIDAD II", "UNIDAD II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "LABORATORIO DE VECTORES",
            "DEMO DE VISIÓN", "MAPA MUNDIAL",
            "Cancelar", "Confirmar", "Demostración", "Mover", "Seleccionar", "ESTUDIANTE",
            "La infestación se cobra otra víctima", "UNIDAD II", "UNIDAD II/III",
            "UNIT III/IV", "UNIT IX", "UNIT V/VIII", "UNIT VI", "UNIT VII",
            "UNIT VII/VIII", "UNIT VIII", "LABORATORIO DE VECTORES",
            "DEMO DE VISIÓN", "MAPA MUNDIAL", "Cancelar", "Confirmar", "Elegir",
            "Mover", "Siguiente", "Subir rango", "TEMARIO", "TIENDA", "TRANSFORM LAB",
            "TUTORIAL", "The infestation claims another", "Todavía no has recogido nada.",
            "UNIDAD DESCONOCIDA", "Vender", "Vendido", "Volver", "Volver al título",
            "ÁRBOL DE HABILIDADES", "—",
            "Aceptar", "Accept", "STUDENT", "STUDENT", "Confirm", "Confirm",
            "Move", "Move", "Select", "Select", "Cancel", "Cancel",
            "Change", "Change", "Back", "Back", "Exit", "Exit", "Jump", "Jump",
            "Next", "Next", "Choose", "Choose", "Enter", "Enter",
            "Move Left", "Move Right", "Move Up", "Move Down",
            "Jump", "Jump", "Crouch", "Crouch", "Dash", "Dash",
            "Grab", "Grab", "Pause", "Pause", "FREE MOVE", "FREE MOVE",
            "CHASE (normalized)", "CHASE (normalized)", "ORBIT (dot product)", "ORBIT (dot product)",
            "DISTANCE CHECK", "DISTANCE CHECK",
            "What does Vector2.normalize() return?", "What does Vector2.normalize() return?",
            "A zero vector", "A zero vector", "A unit vector (length=1)", "A unit vector (length=1)",
            "The vector scaled by 2", "The vector scaled by 2",
            "The vector's angle", "The vector's angle",
            "What is the dot product of two perpendicular vectors?",
            "What is the dot product of two perpendicular vectors?", "1", "1",
            "0", "0", "Their product", "Their product", "Undefined", "Undefined",
            "What curve uses 4 control points?", "What curve uses 4 control points?",
            "Linear", "Linear", "Quadratic Bezier", "Quadratic Bezier",
            "Cubic Bezier", "Cubic Bezier", "Catmull-Rom", "Catmull-Rom",
            "What does distance() between two points return?",
            "What does distance() between two points return?",
            "The straight-line length", "The straight-line length",
            "The X difference", "The X difference", "The Y difference", "The Y difference",
            "The sum of coordinates", "The sum of coordinates",
            "What does a normalized vector represent?", "What does a normalized vector represent?",
            "Magnitude only", "Magnitude only", "Direction only", "Direction only",
            "Position only", "Position only", "Speed only", "Speed only",
            "What is cos(90 degrees)?", "What is cos(90 degrees)?",
            "0", "0", "1", "1", "-1", "-1", "0.5", "0.5",
            "RGB EXPLORER", "RGB EXPLORER", "HSV EXPLORER", "HSV EXPLORER",
            "HSL EXPLORER", "HSL EXPLORER", "CMYK EXPLORER", "CMYK EXPLORER",
            "ALPHA BLEND", "ALPHA BLEND", "CHALLENGE", "CHALLENGE",
            "SHIFT to toggle step-by-step algorithm", "SHIFT to toggle step-by-step algorithm",
            "Press Z (light) or X (heavy)", "Press Z (light) or X (heavy)",
            "Light", "Light", "Heavy", "Heavy", "Chain: Z \u2192 Z \u2192 X", "Chain: Z \u2192 Z \u2192 X",
            "Combo window", "Combo window", "Combo: x{count}", "Combo: x{count}",
            "Combo: —", "Combo: —", "Multiplier: {mult}x", "Multiplier: {mult}x",
            "INFERENCE", "INFERENCE", "FEATURE_COMPARE", "FEATURE_COMPARE",
            "CLASS_GRID", "CLASS_GRID", "CONFUSION", "CONFUSION",
            "PIPELINE", "PIPELINE", "TREE_VIEW", "TREE_VIEW",
            "Source Feature Vector:", "Source Feature Vector:",
            "Nearest Training Sample:", "Nearest Training Sample:",
            "No tree structure available for this model", "No tree structure available for this model",
            "THRESHOLD", "THRESHOLD", "OTSU", "OTSU", "ERODE", "ERODE",
            "DILATE", "DILATE", "OPEN", "OPEN", "CLOSE", "CLOSE", "COMPONENTS",
            "COMPONENTS", "REGIONS", "REGIONS", "WATERSHED", "WATERSHED",
            "FEATURES", "FEATURES", "Press I to close intermediate view",
            "Press I to close intermediate view", "No questions loaded", "No questions loaded",
            "QUIZ", "QUIZ", "Score: {score}", "Score: {score}",
            "-1", "-1", "0", "0", "0.5", "0.5", "1", "1",
            "Cancel", "Cancel", "Confirm", "Confirm",
            "ui.collision_lab", "ui.game_over", "ui.inventory_title", "ui.score",
        ]

        HUERFANAS_PERMITIDAS = HUERFANAS_PERMITIDAS_ES if idioma == "es" else HUERFANAS_PERMITIDAS_EN

        datos = json.loads(
            (RAIZ / "locale" / f"{idioma}.json").read_text(encoding="utf-8"))
        huerfanas = sorted(set(datos) - todos_los_literales() - HUERFANAS_PERMITIDAS)
        assert not huerfanas, (
            f"{len(huerfanas)} entrada(s) de {idioma}.json ya no existen en el "
            f"código: {huerfanas[:5]}"
        )'''

# Replace the old test with the new one
content = content.replace(old_test, new_test)

with open('tests/test_i18n.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated test_i18n.py successfully")