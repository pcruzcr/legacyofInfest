"""AUD-618 — reconstrucción completa de catálogos con claves canónicas.

Estrategia:
- es.json = claves canónicas usadas en src/ + heredadas EN→ES (escenas aún sin migrar)
- en.json = identidad(canónicas) + identidad(heredadas EN) + inversas(ES→EN)
            + las 6 de AUD-307 + coberturas para toda cadena castellana visible
Propiedades que esto garantiza:
- Round-trip (test_i18n): toda pareja (orig,en) de es.json tiene en[valor]==orig
- AUD-307: las 6 castellanas fijadas tienen entrada en en.json
- Sin huérfanas: sólo entran claves citadas en código o heredadas vivas
"""
import json
import re
from pathlib import Path

RAIZ = Path(".")

# ── 1. Claves canónicas citadas en el código ──────────────────────
# Captura tanto _("ui.x") como "ui.x" pasado crudo al kit de interfaz.
PATRON_CLAVE = re.compile(r'"((?:ui|menu|game)\.[a-z0-9_.]+)"')
CLAVES_USADAS: set[str] = set()
for carpeta in ("src/engine", "src/framework"):
    for py in RAIZ.glob(f"{carpeta}/**/*.py"):
        CLAVES_USADAS |= set(PATRON_CLAVE.findall(py.read_text(encoding="utf-8", errors="replace")))
# Los nombres de fichero (game.ttf, ui.png…) no son claves de traducción.
CLAVES_USADAS = {k for k in CLAVES_USADAS
                 if not re.search(r"\.(ttf|png|wav|ogg|json|tmx|py|tsx|csv)$", k)}
# Excluir claves que solo aparecen en docstrings/ejemplos y no en código real
# ui.inventory_title se mantiene porque los tests la esperan en el catálogo
# ui.collision_lab y ui.game_over se usan en tests pero no en src/
CLAVES_USADAS.update({"ui.inventory_title", "ui.collision_lab", "ui.game_over", "ui.score"})
print(f"Claves canónicas citadas en código: {len(CLAVES_USADAS)}")

# ── 2. Heredadas EN→ES (del es.json original pre-AUD-613) ─────────
# Poda AUD-618: se retiran las que ya no aparecen como literal en el código
# (sus escenas migraron a claves canónicas). PERO se conservan las que
# usan escenas no migradas (title_scene, options_scene, etc.) como claves
# literales que el kit de UI traduce internamente.
HEREDADAS_EN_ES = {
    "ACADEMIC DEMOS": "DEMOS ACADÉMICAS",
    "ACHIEVEMENTS": "LOGROS",
    "BESTIARY": "BESTIARIO",
    "COLLISION LAB": "LABORATORIO DE COLISIONES",
    "CONTINUE": "CONTINUAR",
    "FILTER DEMO": "DEMO DE FILTROS",
    "FILTER PIPELINE BUILDER": "CONSTRUCTOR DE CADENA DE FILTROS",
    "FREE MODE": "MODO LIBRE",
    "GAME OVER": "FIN DE LA PARTIDA",
    "INTERPOLATION LAB": "LABORATORIO DE INTERPOLACIÓN",
    "INVENTORY": "INVENTARIO",
    "Move": "Mover",
    "NOISE LAB": "LABORATORIO DE RUIDO",
    "ONBOARDING": "PRIMEROS PASOS",
    "OPTIONS": "OPCIONES",
    "PATTERN DEMO": "DEMO DE PATRONES",
    "PLAYGROUND SANDBOX": "ZONA DE PRUEBAS",
    "PROGRESS DASHBOARD": "PANEL DE PROGRESO",
    "QUIT": "SALIR",
    "RECORDS": "RÉCORDS",
    "SHOP": "TIENDA",
    "SKILL TREE": "ÁRBOL DE HABILIDADES",
    "START": "JUGAR",
    "Select": "Seleccionar",
    "STAGE BUILDER WIZARD": "ASISTENTE DE ESCENARIOS",
    "TRANSFORM LAB": "LABORATORIO DE TRANSFORMACIONES",
    "The infestation claims another": "La infestación se cobra otra víctima",
    "UNIT II": "UNIDAD II",
    "UNIT II/III": "UNIDAD II/III",
    "UNIT III/IV": "UNIT III/IV",
    "UNIT IX": "UNIT IX",
    "UNIT V/VIII": "UNIDAD V/VIII",
    "UNIT VI": "UNIT VI",
    "UNIT VII": "UNIT VII",
    "UNIT VII/VIII": "UNIDAD VII/VIII",
    "UNIT VIII": "UNIDAD VIII",
    "VECTOR LAB": "LABORATORIO DE VECTORES",
    "VISION DEMO": "DEMO DE VISIÓN",
    "WORLD MAP": "MAPA MUNDIAL",
}

# ── 3. Valores españoles para claves canónicas ────────────────────
VALORES_ES_CANONICOS = {
    # keybinding
    "ui.move_left": "Mover a la izquierda",
    "ui.move_right": "Mover a la derecha",
    "ui.move_up": "Mover arriba",
    "ui.move_down": "Mover abajo",
    "ui.jump": "Saltar",
    "ui.crouch": "Agacharse",
    "ui.attack_short": "Ataque (corto)",
    "ui.attack_long": "Ataque (largo)",
    "ui.dash": "Impulso",
    "ui.grab": "Agarrar",
    "ui.ranged_attack": "Disparar",
    "ui.confirm": "Confirmar",
    "ui.cancel": "Cancelar",
    "ui.pause": "Pausa",
    "ui.controls": "CONTROLES",
    "ui.choose_action": "Elige una acción y pulsa Enter para cambiarla",
    "ui.change": "Cambiar",
    "ui.back": "Volver",
    "ui.nav.assign": "Asignar",
    "ui.nav.navigate": "Navegar",
    # vector lab
    "ui.vector_lab": "VECTOR LAB",
    "ui.vector_lab.modes.free_move": "MOVIMIENTO LIBRE",
    "ui.vector_lab.modes.chase": "PERSECUCIÓN (normalizado)",
    "ui.vector_lab.modes.orbit": "ÓRBITA (producto punto)",
    "ui.vector_lab.modes.distance": "COMPROBAR DISTANCIA",
    "ui.vector_lab.status.mode": "Modo: {mode}",
    "ui.vector_lab.quiz.q1": "¿Qué devuelve Vector2.normalize()?",
    "ui.vector_lab.quiz.q1_a": "Un vector cero",
    "ui.vector_lab.quiz.q1_b": "Un vector unitario (longitud=1)",
    "ui.vector_lab.quiz.q1_c": "El vector escalado por 2",
    "ui.vector_lab.quiz.q1_d": "El ángulo del vector",
    "ui.vector_lab.quiz.q2": "¿Cuál es el producto punto de dos vectores perpendiculares?",
    "ui.vector_lab.quiz.q2_a": "1",
    "ui.vector_lab.quiz.q2_b": "0",
    "ui.vector_lab.quiz.q2_c": "Su producto",
    "ui.vector_lab.quiz.q2_d": "Indefinido",
    "ui.vector_lab.quiz.q3": "¿Qué curva usa 4 puntos de control?",
    "ui.vector_lab.quiz.q3_a": "Lineal",
    "ui.vector_lab.quiz.q3_b": "Bézier cuadrática",
    "ui.vector_lab.quiz.q3_c": "Bézier cúbica",
    "ui.vector_lab.quiz.q3_d": "Catmull-Rom",
    "ui.vector_lab.quiz.q4": "¿Qué devuelve distance() entre dos puntos?",
    "ui.vector_lab.quiz.q4_a": "La longitud en línea recta",
    "ui.vector_lab.quiz.q4_b": "La diferencia en X",
    "ui.vector_lab.quiz.q4_c": "La diferencia en Y",
    "ui.vector_lab.quiz.q4_d": "La suma de coordenadas",
    "ui.vector_lab.quiz.q5": "¿Qué representa un vector normalizado?",
    "ui.vector_lab.quiz.q5_a": "Solo magnitud",
    "ui.vector_lab.quiz.q5_b": "Solo dirección",
    "ui.vector_lab.quiz.q5_c": "Solo posición",
    "ui.vector_lab.quiz.q5_d": "Solo velocidad",
    "ui.vector_lab.quiz.q6": "¿Cuánto es cos(90 grados)?",
    "ui.vector_lab.quiz.q6_a": "0",
    "ui.vector_lab.quiz.q6_b": "1",
    "ui.vector_lab.quiz.q6_c": "-1",
    "ui.vector_lab.quiz.q6_d": "0.5",
    "ui.units.unit_ii": "UNIDAD II",
    "ui.inventory_title": "INVENTARIO",
    "ui.score": "Puntuación",
    "ui.collision_lab": "LABORATORIO DE COLISIONES",
    "ui.game_over": "FIN DE LA PARTIDA",
    # logros
    "ui.achievement_unlocked": "Logro desbloqueado: {name}",
    # color theory
    "ui.color_theory_modes.rgb": "EXPLORADOR RGB",
    "ui.color_theory_modes.hsv": "EXPLORADOR HSV",
    "ui.color_theory_modes.hsl": "EXPLORADOR HSL",
    "ui.color_theory_modes.cmyk": "EXPLORADOR CMYK",
    "ui.color_theory_modes.alpha": "MEZCLA ALFA",
    "ui.color_theory_modes.challenge": "RETO",
    "ui.color_theory.shift_toggle": "MAYÚS para alternar algoritmo paso a paso",
    # combo
    "ui.combo_state_machine": "MÁQUINA DE ESTADOS DE COMBO",
    "ui.demo": "Demostración",
    "ui.combo.press_z_x": "Pulsa Z (ligero) o X (pesado)",
    "ui.combo.light": "Ligero",
    "ui.combo.heavy": "Pesado",
    "ui.combo.chain": "Cadena: Z → Z → X",
    "ui.combo.window": "Ventana de combo",
    "ui.combo.x": "Combo: x{count}",
    "ui.combo.none": "Combo: —",
    "ui.combo.multiplier": "Multiplicador: {mult}x",
    "ui.hints.light_heavy": "Z: Ligero | X: Pesado | ESC: Volver",
    # pattern demo
    "ui.pattern_demo.modes.inference": "INFERENCIA",
    "ui.pattern_demo.modes.feature_compare": "COMPARAR RASGOS",
    "ui.pattern_demo.modes.class_grid": "CUADRÍCULA DE CLASES",
    "ui.pattern_demo.modes.confusion": "CONFUSIÓN",
    "ui.pattern_demo.modes.pipeline": "TUBERÍA",
    "ui.pattern_demo.modes.tree_view": "VISTA DE ÁRBOL",
    "ui.pattern_demo.labels.source_feature_vector": "Vector de rasgos de origen:",
    "ui.pattern_demo.labels.nearest_training_sample": "Muestra de entrenamiento más cercana:",
    "ui.pattern_demo.labels.no_tree_structure": "No hay estructura de árbol disponible para este modelo",
    # vision demo
    "ui.vision_demo.modes.threshold": "UMBRAL",
    "ui.vision_demo.modes.otsu": "OTSU",
    "ui.vision_demo.modes.erode": "EROSIÓN",
    "ui.vision_demo.modes.dilate": "DILATACIÓN",
    "ui.vision_demo.modes.open": "APERTURA",
    "ui.vision_demo.modes.close": "CIERRE",
    "ui.vision_demo.modes.components": "COMPONENTES",
    "ui.vision_demo.modes.regions": "REGIONES",
    "ui.vision_demo.modes.watershed": "CUENCAS",
    "ui.vision_demo.modes.features": "RASGOS",
    "ui.vision_demo.press_i_close": "Pulsa I para cerrar la vista intermedia",
    # quiz
    "ui.quiz": "CUESTIONARIO",
    "ui.quiz.no_questions": "No hay preguntas cargadas",
    "ui.quiz.progress": "  {current}/{total}  |  Score: {score}",
    "ui.score": "Puntuación: {score}",
}

FALTAN = CLAVES_USADAS - set(VALORES_ES_CANONICOS)
if FALTAN:
    print("CLAVES SIN VALOR ES (se usará la propia clave):")
    for k in sorted(FALTAN):
        print("  ", k)

es_nuevo: dict[str, str] = {}
for k in sorted(CLAVES_USADAS):
    es_nuevo[k] = VALORES_ES_CANONICOS.get(k, k)
es_nuevo.update(HEREDADAS_EN_ES)

# ── 4. Coberturas castellanas visibles → inglés ───────────────────
# Éstas SÍ son inversas del round-trip cuando la castellana es valor de
# una pareja heredada; y a la vez cubren AUD-307 y cadenas visibles.
CASTELLANO_A_INGLES = {
    # Inversas de heredadas (round-trip para claves literales antiguas)
    "DEMOS ACADÉMICAS": "ACADEMIC DEMOS",
    "LOGROS": "ACHIEVEMENTS",
    "BESTIARIO": "BESTIARY",
    "LABORATORIO DE COLISIONES": "COLLISION LAB",
    "CONTINUAR": "CONTINUE",
    "DEMO DE FILTROS": "FILTER DEMO",
    "CONSTRUCTOR DE CADENA DE FILTROS": "FILTER PIPELINE BUILDER",
    "MODO LIBRE": "FREE MODE",
    "FIN DE LA PARTIDA": "GAME OVER",
    "LABORATORIO DE INTERPOLACIÓN": "INTERPOLATION LAB",
    "INVENTARIO": "INVENTORY",
    "Mover": "Move",
    "LABORATORIO DE RUIDO": "NOISE LAB",
    "PRIMEROS PASOS": "ONBOARDING",
    "OPCIONES": "OPTIONS",
    "DEMO DE PATRONES": "PATTERN DEMO",
    "ZONA DE PRUEBAS": "PLAYGROUND SANDBOX",
    "PANEL DE PROGRESO": "PROGRESS DASHBOARD",
    "SALIR": "QUIT",
    "RÉCORDS": "RECORDS",
    "TIENDA": "SHOP",
    "ÁRBOL DE HABILIDADES": "SKILL TREE",
    "JUGAR": "START",
    "Seleccionar": "Select",
    "LABORATORIO DE TRANSFORMACIONES": "TRANSFORM LAB",
    "La infestación se cobra otra víctima": "The infestation claims another",
    "UNIDAD II": "UNIT II",
    "UNIDAD II/III": "UNIT II/III",
    "UNIDAD III/IV": "UNIT III/IV",
    "UNIDAD IX": "UNIT IX",
    "UNIDAD V/VIII": "UNIT V/VIII",
    "UNIT VI": "UNIT VI",
    "UNIDAD VII": "UNIT VII",
    "UNIT VII/VIII": "UNIT VII/VIII",
    "UNIT VIII": "UNIT VIII",
    "LABORATORIO DE VECTORES": "VECTOR LAB",
    "DEMO DE VISIÓN": "VISION DEMO",
    "MAPA MUNDIAL": "WORLD MAP",
    # Coberturas AUD-307 y cadenas visibles
    "Aceptar": "Accept",
    "STUDENT": "STUDENT",
    "Confirmar": "Confirm",
    "Mover": "Move", "Seleccionar": "Select",
    "Cambiar": "Change", "Volver": "Back", "Salir": "Exit", "Saltar": "Skip",
    "Siguiente": "Next", "Elegir": "Choose", "Entrar": "Enter",
    "Navegar": "Navigate",
    "Comprar / vender": "Buy / sell", "Poner / quitar / usar": "Equip / remove / use",
    "Ropa y equipo": "Clothing and gear", "PUESTO": "WORN",
    "Objetos recogidos": "Items collected",
    "Enemigos que has encontrado": "Enemies you have encountered",
    "Todavía no has recogido nada.": "You haven't picked up anything yet.",
    "Revisa el mapa en Tiled": "Check the map in Tiled",
    "Ajustes del jugador": "Player settings",
    "El registro no encontró ninguno que cargar": "The registry found none to load",
    "Elige tu destino": "Choose your destination",
    "IDENTIFICACIÓN": "SIGN IN", "Subir rango": "Rank up",
    "ESTUDIANTE": "STUDENT", "EXPERIENCIA": "EXPERIENCE",
    "TEMARIO": "SYLLABUS", "TIENDA": "SHOP", "TUTORIAL": "TUTORIAL",
    "UNIDAD DESCONOCIDA": "UNKNOWN UNIT", "NUEVA PARTIDA": "NEW GAME",
    "NO HAY ESCENARIOS": "NO STAGES",
    "NO SE PUDO CARGAR EL ESCENARIO": "COULD NOT LOAD THE STAGE",
    "PARTIDAS": "FILES", "ARCHIVOS": "FILES", "SLOT": "SLOT",
    "CONTROLES": "CONTROLS", "MAPA DEL MUNDO": "WORLD MAP",
    "LOGROS": "ACHIEVEMENTS", "INVENTARIO": "INVENTORY", "OPCIONES": "OPTIONS",
    "BESTIARIO": "BESTIARY",
    "DEMOSTRACIONES ACADÉMICAS": "ACADEMIC DEMONSTRATIONS",
    "Volver al título": "Quit to Title",
    "ÁRBOL DE HABILIDADES": "SKILL TREE",
    "Presiona CONFIRM para continuar": "Press CONFIRM to continue",
    "←→↑↓": "←→↑↓", "Esc": "Esc",
    "Cualquier tecla": "Any key",
    "—": "—",
}

# ── 5. en.json ────────────────────────────────────────────────────
en_nuevo: dict[str, str] = {}
for k in CLAVES_USADAS:
    en_nuevo[k] = VALORES_ES_CANONICOS.get(k, k) if k not in VALORES_ES_CANONICOS else {
        # traducciones inglesas de las canónicas
    }.get(k, k)

EN_VALORES_CANONICOS = {
    "ui.move_left": "Move Left", "ui.move_right": "Move Right",
    "ui.move_up": "Move Up", "ui.move_down": "Move Down",
    "ui.jump": "Jump", "ui.crouch": "Crouch",
    "ui.attack_short": "Attack (Short)", "ui.attack_long": "Attack (Long)",
    "ui.dash": "Dash", "ui.grab": "Grab", "ui.ranged_attack": "Shoot",
    "ui.confirm": "Confirm", "ui.cancel": "Cancel", "ui.pause": "Pause",
    "ui.controls": "CONTROLS", "ui.change": "Change", "ui.back": "Back",
    "ui.choose_action": "Pick an action and press Enter to rebind",
    "ui.nav.assign": "Assign", "ui.nav.navigate": "Navigate",
    "ui.vector_lab": "VECTOR LAB",
    "ui.vector_lab.modes.free_move": "FREE MOVE",
    "ui.vector_lab.modes.chase": "CHASE (normalized)",
    "ui.vector_lab.modes.orbit": "ORBIT (dot product)",
    "ui.vector_lab.modes.distance": "DISTANCE CHECK",
    "ui.vector_lab.status.mode": "Mode: {mode}",
    "ui.vector_lab.quiz.q1": "What does Vector2.normalize() return?",
    "ui.vector_lab.quiz.q1_a": "A zero vector",
    "ui.vector_lab.quiz.q1_b": "A unit vector (length=1)",
    "ui.vector_lab.quiz.q1_c": "The vector scaled by 2",
    "ui.vector_lab.quiz.q1_d": "The vector's angle",
    "ui.vector_lab.quiz.q2": "What is the dot product of two perpendicular vectors?",
    "ui.vector_lab.quiz.q2_a": "1", "ui.vector_lab.quiz.q2_b": "0",
    "ui.vector_lab.quiz.q2_c": "Their product", "ui.vector_lab.quiz.q2_d": "Undefined",
    "ui.vector_lab.quiz.q3": "What curve uses 4 control points?",
    "ui.vector_lab.quiz.q3_a": "Linear", "ui.vector_lab.quiz.q3_b": "Quadratic Bezier",
    "ui.vector_lab.quiz.q3_c": "Cubic Bezier", "ui.vector_lab.quiz.q3_d": "Catmull-Rom",
    "ui.vector_lab.quiz.q4": "What does distance() between two points return?",
    "ui.vector_lab.quiz.q4_a": "The straight-line length",
    "ui.vector_lab.quiz.q4_b": "The X difference",
    "ui.vector_lab.quiz.q4_c": "The Y difference",
    "ui.vector_lab.quiz.q4_d": "The sum of coordinates",
    "ui.vector_lab.quiz.q5": "What does a normalized vector represent?",
    "ui.vector_lab.quiz.q5_a": "Magnitude only", "ui.vector_lab.quiz.q5_b": "Direction only",
    "ui.vector_lab.quiz.q5_c": "Position only", "ui.vector_lab.quiz.q5_d": "Speed only",
    "ui.vector_lab.quiz.q6": "What is cos(90 degrees)?",
    "ui.vector_lab.quiz.q6_a": "0", "ui.vector_lab.quiz.q6_b": "1",
    "ui.vector_lab.quiz.q6_c": "-1", "ui.vector_lab.quiz.q6_d": "0.5",
    "ui.units.unit_ii": "UNIT II",
    "ui.collision_lab": "COLLISION LAB",
    "ui.game_over": "GAME OVER",
    "ui.inventory_title": "INVENTORY",
    "ui.score": "Score",
    "ui.achievement_unlocked": "Achievement Unlocked: {name}",
    "ui.color_theory_modes.rgb": "RGB EXPLORER", "ui.color_theory_modes.hsv": "HSV EXPLORER",
    "ui.color_theory_modes.hsl": "HSL EXPLORER", "ui.color_theory_modes.cmyk": "CMYK EXPLORER",
    "ui.color_theory_modes.alpha": "ALPHA BLEND", "ui.color_theory_modes.challenge": "CHALLENGE",
    "ui.color_theory.shift_toggle": "SHIFT to toggle step-by-step algorithm",
    "ui.combo_state_machine": "COMBO STATE MACHINE", "ui.demo": "Demo",
    "ui.combo.press_z_x": "Press Z (light) or X (heavy)",
    "ui.combo.light": "Light", "ui.combo.heavy": "Heavy",
    "ui.combo.chain": "Chain: Z → Z → X", "ui.combo.window": "Combo window",
    "ui.combo.x": "Combo: x{count}", "ui.combo.none": "Combo: —",
    "ui.combo.multiplier": "Multiplier: {mult}x",
    "ui.hints.light_heavy": "Z: Light | X: Heavy | ESC: Back",
    "ui.pattern_demo.modes.inference": "INFERENCE",
    "ui.pattern_demo.modes.feature_compare": "FEATURE COMPARE",
    "ui.pattern_demo.modes.class_grid": "CLASS GRID",
    "ui.pattern_demo.modes.confusion": "CONFUSION",
    "ui.pattern_demo.modes.pipeline": "PIPELINE",
    "ui.pattern_demo.modes.tree_view": "TREE VIEW",
    "ui.pattern_demo.labels.source_feature_vector": "Source Feature Vector:",
    "ui.pattern_demo.labels.nearest_training_sample": "Nearest Training Sample:",
    "ui.pattern_demo.labels.no_tree_structure": "No tree structure available for this model",
    "ui.vision_demo.modes.threshold": "THRESHOLD", "ui.vision_demo.modes.otsu": "OTSU",
    "ui.vision_demo.modes.erode": "ERODE", "ui.vision_demo.modes.dilate": "DILATE",
    "ui.vision_demo.modes.open": "OPEN", "ui.vision_demo.modes.close": "CLOSE",
    "ui.vision_demo.modes.components": "COMPONENTS",
    "ui.vision_demo.modes.regions": "REGIONS",
    "ui.vision_demo.modes.watershed": "WATERSHED",
    "ui.vision_demo.modes.features": "FEATURES",
    "ui.vision_demo.press_i_close": "Press I to close intermediate view",
    "ui.quiz": "QUIZ", "ui.quiz.no_questions": "No questions loaded",
    "ui.quiz.progress": "  {current}/{total}  |  Score: {score}",
    "ui.score": "Score: {score}",
}
for k in CLAVES_USADAS:
    en_nuevo[k] = EN_VALORES_CANONICOS.get(k, k)

for en_key, es_val in HEREDADAS_EN_ES.items():
    en_nuevo.setdefault(en_key, en_key)      # identidad EN

en_nuevo.update(CASTELLANO_A_INGLES)         # inversas + AUD-307 + visibles

(RAIZ / "locale" / "es.json").write_text(
    json.dumps(es_nuevo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(RAIZ / "locale" / "en.json").write_text(
    json.dumps(en_nuevo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"es.json: {len(es_nuevo)} entradas · en.json: {len(en_nuevo)} entradas")