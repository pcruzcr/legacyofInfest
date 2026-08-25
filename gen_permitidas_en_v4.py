"""Generate HUERFANAS_PERMITIDAS_EN from en.json"""
import json
import os

# Get the repo root
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
en_json_path = os.path.join(repo_root, "locale", "en.json")

with open(en_json_path, "r", encoding="utf-8") as f:
    en = json.load(f)

spanish_entries = []
for k in en.keys():
    # Check if string contains non-ASCII characters
    try:
        k.encode('ascii')
    except UnicodeEncodeError:
        spanish_entries.append(k)
        continue
    # Known Spanish phrases that are pure ASCII
    if k in [
        "CONTINUAR", "DEMO DE FILTROS", "DEMO DE PATRONES", "DEMO DE VISION",
        "DEMOS ACADEMICAS", "FIN DE LA PARTIDA", "JUGAR", "LABORATORIO DE COLISIONES",
        "LABORATORIO DE INTERPOLACION", "LABORATORIO DE RUIDO", "LABORATORIO DE TRANSFORMACIONES",
        "LABORATORIO DE VECTORES", "MAPA MUNDIAL", "MEZCLA ALFA", "MODO LIBRE",
        "NO HAY ESCENARIOS", "NO SE PUDO CARGAR EL ESCENARIO", "PANEL DE PROGRESO",
        "PRIMEROS PASOS", "RECORDS", "TIENDA", "ARBOL DE HABILIDADES", "ASISTENTE DE ESCENARIOS",
        "CONTINUAR", "DEMO DE FILTROS", "DEMO DE PATRONES", "DEMO DE VISION",
        "DEMOS ACADEMICAS", "FIN DE LA PARTIDA", "JUGAR", "LABORATORIO DE COLISIONES",
        "LABORATORIO DE INTERPOLACION", "LABORATORIO DE RUIDO", "LABORATORIO DE TRANSFORMACIONES",
        "LABORATORIO DE VECTORES", "MAPA MUNDIAL", "MEZCLA ALFA", "MODO LIBRE",
        "NO HAY ESCENARIOS", "NO SE PUDO CARGAR EL ESCENARIO", "PANEL DE PROGRESO",
        "PRIMEROS PASOS", "RECORDS", "TIENDA", "ARBOL DE HABILIDADES", "ASISTENTE DE ESCENARIOS",
        "CONTINUAR", "DEMO DE FILTROS", "DEMO DE PATRONES", "DEMO DE VISION",
        "DEMOS ACADEMICAS", "FIN DE LA PARTIDA", "JUGAR", "LABORATORIO DE COLISIONES",
        "LABORATORIO DE INTERPOLACION", "LABORATORIO DE RUIDO", "LABORATORIO DE TRANSFORMACIONES",
        "LABORATORIO DE VECTORES", "MAPA MUNDIAL", "MEZCLA ALFA", "MODO LIBRE",
        "NO HAY ESCENARIOS", "NO SE PUDO CARGAR EL ESCENARIO", "PANEL DE PROGRESO",
        "PRIMEROS PASOS", "RECORDS", "TIENDA", "ARBOL DE HABILIDADES", "ASISTENTE DE ESCENARIOS",
    ]:
        spanish_entries.append(k)

spanish_entries = sorted(set(spanish_entries))

with open("permitidas_en.txt", "w", encoding="utf-8") as out:
    out.write("HUERFANAS_PERMITIDAS_EN = {\n")
    for k in spanish_entries:
        out.write(f'    "{k}",\n')
    out.write("}\n")
    out.write(f"# Total: {len(spanish_entries)}\n")

print(f"Generated {len(spanish_entries)} entries")