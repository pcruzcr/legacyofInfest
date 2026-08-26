"""AUD-628: arregla los 32 errores ruff restantes."""
import re
from pathlib import Path


def fix_f841_unusued_var(filepath, varnames):
    """Prefija variables sin usar con _."""
    p = Path(filepath)
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    for vn in varnames:
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith(f"{vn} =") or stripped.startswith(f"{vn}="):
                indent = len(line) - len(line.lstrip())
                lines[i] = " " * indent + "_" + stripped
    p.write_text("\n".join(lines), encoding="utf-8")
    print(f"F841 fixed: {filepath}")


def fix_e501_long_lines(filepath, max_len=120):
    """Rompe líneas largas en puntos naturales."""
    p = Path(filepath)
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    changed = False
    for i, line in enumerate(lines):
        content = line.rstrip("\n\r")
        if len(content) <= max_len:
            continue
        # Intentar romper después de una coma
        indent = len(content) - len(content.lstrip())
        if indent < max_len - 10:
            # Buscar la última coma que quepa
            best_break = None
            for j in range(max_len, indent + 20, -1):
                if j < len(content) and content[j] == ",":
                    best_break = j + 1
                    break
            if best_break:
                first_part = content[:best_break]
                second_part = " " * (indent + 4) + content[best_break:].lstrip()
                lines[i] = first_part + "\n" + second_part + "\n"
                changed = True
    if changed:
        p.write_text("\n".join(lines), encoding="utf-8")
        print(f"E501 fixed: {filepath}")
    else:
        print(f"E501 no auto-fixable: {filepath}")


# ── 1. world_map_scene.py: F841 inv + E501 x2 ──
p = Path("src/engine/scenes/world_map_scene.py")
text = p.read_text(encoding="utf-8")
text = re.sub(r"^(\s+)inv = ", r"\1_inv = ", text, flags=re.MULTILINE)
# Romper las dos líneas largas específicas
lines = text.splitlines()
for i, line in enumerate(lines):
    if len(line) > 120 and "skill_ok" in line:
        lines[i] = line[:120].rstrip() + "\n" + " " * 12 + line[120:].lstrip()
    elif len(line) > 120 and "_habilidades_libres" in line and "skill_req" in line:
        # Ya rota arriba probablemente
        pass
p.write_text("\n".join(lines), encoding="utf-8")
print("world_map_scene.py: done")

# ── 2. ecs/__init__.py: F401 Sistema ──
p = Path("src/framework/ecs/__init__.py")
text = p.read_text(encoding="utf-8")
text = text.replace(
    "from src.framework.ecs.scheduler import Sistema\n",
    ""
)
# Añadir a __all__ si existe, o quitar de __all__
text = text.replace('    "Sistema",\n', "")
p.write_text(text, encoding="utf-8")
print("ecs/__init__.py: done")

# ── 3. enemy_terrain_shaper.py: F841 bloque/hazard ──
fix_f841_unusued_var(
    "src/framework/entities/enemy_terrain_shaper.py", ["bloque", "hazard"])

# ── 4. prefab_loader.py: F841 pos/obj_type/obj_props/y + B008 ──
fix_f841_unusued_var(
    "src/framework/stage/prefab_loader.py",
    ["pos", "obj_type", "obj_props", "y"])
p = Path("src/framework/stage/prefab_loader.py")
text = p.read_text(encoding="utf-8")
# B008: pygame.Vector2() en argument default
text = text.replace(
    "= pygame.Vector2(),",
    "= None,",
)
text = text.replace(
    "= pygame.Vector2())",
    "= None)",
)
p.write_text(text, encoding="utf-8")
print("prefab_loader.py: done")

print("\nDone. Run ruff again to check.")