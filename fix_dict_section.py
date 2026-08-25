import re

with open('reconstruir_catalogos.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the CASTELLANO_A_INGLES dict
pattern = re.compile(r'# ── 4\. Coberturas castellanas visibles → inglés ───────────────────.*?(?=# ── 5\. en\.json)', re.DOTALL)

new_section = '''# ── 4. Coberturas castellanas visibles → inglés ───────────────────
# Éstas SÍ son inversas del round-trip cuando la castellana es valor de
# una pareja heredada; y a la vez cubren AUD-307 y cadenas visibles.
CASTELLANO_A_INGLES = {
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

'''

new_content = re.sub(
    r'# ── 4\. Coberturas castellanas visibles → inglés ───────────────────.*?(?=# ── 5\. en\.json)',
    new_section,
    content,
    flags=re.DOTALL
)

with open('reconstruir_catalogos.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done')