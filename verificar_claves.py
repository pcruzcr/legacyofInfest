"""Verifica que las 8 escenas auditadas ya no usen literales antiguos (AUD-618)."""
from pathlib import Path
import re

ARCHIVOS = [
    "src/engine/scenes/keybinding_scene.py",
    "src/engine/scenes/vector_lab_scene.py",
    "src/engine/core/achievements.py",
    "src/engine/scenes/color_theory_scene.py",
    "src/engine/scenes/combo_demo_scene.py",
    "src/engine/scenes/pattern_demo_scene.py",
    "src/engine/scenes/vision_demo_scene.py",
    "src/engine/scenes/quiz_system.py",
]

# Clave canónica: empieza por ui. y sólo tiene [a-z0-9_.]
PATRON_CLAVE = re.compile(r'_\("([a-z0-9_.]+)"\)')
# Literal con espacios/mayúsculas = sospechoso de ser texto visible viejo
PATRON_VIEJO = re.compile(r'_\("([^"]*[A-Z][^"]*)"\)')

salida = []
for rel in ARCHIVOS:
    ruta = Path(rel)
    contenido = ruta.read_text(encoding="utf-8")
    claves = PATRON_CLAVE.findall(contenido)
    viejos = PATRON_VIEJO.findall(contenido)
    salida.append(f"{ruta.name}: {len(claves)} claves canónicas, {len(viejos)} literales viejos")
    for v in viejos:
        salida.append(f"  VIEJO: _({v!r})")

Path("verificacion_claves.txt").write_text("\n".join(salida), encoding="utf-8")
print("\n".join(salida))
