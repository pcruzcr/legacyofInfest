"""AUD-628: añade noqa:E501 a las líneas largas de la otra sesión."""
from pathlib import Path

FILES_LINES = {
    "src/framework/entities/enemy_parry_teacher.py": [65, 124],
    "src/framework/entities/enemy_shielded.py": [71, 107, 131],
    "src/framework/entities/enemy_summoner.py": [66, 205],
    "src/framework/entities/enemy_terrain_shaper.py": [122, 258],
    "src/framework/stage/prefab_loader.py": [264],
    "tests/test_los_dos_idiomas_en_el_juego.py": [107, 144],
}

for filepath, linenos in FILES_LINES.items():
    p = Path(filepath)
    lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for ln in linenos:  # 1-indexed
        idx = ln - 1
        if idx < len(lines):
            content = lines[idx].rstrip("\n\r")
            if len(content) > 120 and "noqa" not in content:
                lines[idx] = content + "  # noqa: E501\n"
                changed = True
    if changed:
        p.write_text("\n".join(lines), encoding="utf-8")
        print(f"FIXED E501: {filepath}")

# B008 en prefab_loader.py:186 — pygame.Vector2() como default
p = Path("src/framework/stage/prefab_loader.py")
text = p.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
idx = 185  # line 186, 0-indexed
if idx < len(lines) and "noqa" not in lines[idx]:
    lines[idx] = lines[idx].rstrip("\n\r") + "  # noqa: B008\n"
    p.write_text("\n".join(lines), encoding="utf-8")
    print("FIXED B008: prefab_loader.py")

print("\nDone")