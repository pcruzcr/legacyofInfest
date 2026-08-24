"""
grade_boss.py — Auto-grade student boss Python files.

Evaluates:
  - Boss class inherits from BossBase
  - Phase transitions implemented (at least 2 phases)
  - Attack patterns defined (at least 2)
  - Events connected (PLAYER_DAMAGED, etc.)
  - HP thresholds for phase changes
  - Telegraph state exists (wind-up before attacks)
  - Hurt/Damage states implemented
  - Boss has unique name and appearance config

Usage:
    python scripts/grade_boss.py path/to/student_boss.py
    python scripts/grade_boss.py --dir submissions/boss1/
    python scripts/grade_boss.py --json submissions/boss1/boss.py
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts._cli_paths import display_path  # noqa: E402  (tras ajustar sys.path)

RUBRIC: dict[str, int] = {
    "inherits_bossbase": 10,
    "phase_transitions": 15,
    "attack_patterns": 15,
    "hp_thresholds": 10,
    "telegraph_state": 10,
    "hurt_damage_states": 10,
    "event_connections": 10,
    "boss_name_config": 10,
    "imports_valid": 5,
    "class_structure": 5,
}


def _define_un_jefe(fichero: Path) -> bool:
    """¿Este `.py` declara una subclase de `BossBase`?

    Usa **la misma regla** que la categoría `inherits_bossbase` de la rúbrica:
    una clase de primer nivel con `BossBase` entre sus bases. Si divergieran,
    el filtro dejaría pasar ficheros que después sacan 0, o descartaría jefes
    que la rúbrica sí reconoce, y ninguna de las dos cosas se notaría hasta que
    a alguien le saliera una nota rara.
    """
    try:
        arbol = ast.parse(fichero.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, SyntaxError):
        # Un fichero que ni siquiera compila sí interesa calificarlo: el
        # informe dirá que no se pudo leer, que es información útil.
        return True
    return any(
        isinstance(n, ast.ClassDef)
        and any(isinstance(b, ast.Name) and b.id == "BossBase" for b in n.bases)
        for n in ast.iter_child_nodes(arbol)
    )


def _llamadas_a(tree: ast.AST, nombre: str) -> list[ast.Call]:
    """Todas las llamadas a una función o método con ese nombre."""
    encontradas = []
    for nodo in ast.walk(tree):
        if not isinstance(nodo, ast.Call):
            continue
        f = nodo.func
        if isinstance(f, ast.Name) and f.id == nombre:
            encontradas.append(nodo)
        elif isinstance(f, ast.Attribute) and f.attr == nombre:
            encontradas.append(nodo)
    return encontradas


def _umbrales_en_fases(tree: ast.AST) -> int:
    """Cuántos `BossPhase(health_threshold=...)` declara el jefe.

    Es la forma que el framework espera, y la que usa el jefe de referencia
    (AUD-104).
    """
    total = 0
    for llamada in _llamadas_a(tree, "BossPhase"):
        for kw in llamada.keywords:
            if kw.arg == "health_threshold":
                total += 1
    return total


def _ataques_declarados_en_fases(tree: ast.AST) -> list[str]:
    """Nombres de ataque declarados dentro de `BossPhase(attacks=[...])`."""
    nombres: list[str] = []
    for llamada in _llamadas_a(tree, "BossPhase"):
        for kw in llamada.keywords:
            if kw.arg not in ("attacks", "attack_names", "ataques"):
                continue
            if isinstance(kw.value, (ast.List, ast.Tuple)):
                nombres += [
                    e.value for e in kw.value.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                ]
    return nombres


def grade_boss(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "file": str(path),
        "score": 0,
        "max_score": sum(RUBRIC.values()),
        "categories": {},
        "errors": [],
        "warnings": [],
    }

    if not path.exists():
        result["errors"].append("File not found")
        result["percentage"] = 0.0
        return result
    if path.suffix != ".py":
        result["errors"].append(f"Not a .py file (got {path.suffix})")

    try:
        with open(path, encoding="utf-8-sig") as f:
            source = f.read()
    except Exception as e:
        result["errors"].append(f"Cannot read file: {e}")
        result["percentage"] = 0.0
        return result

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        result["errors"].append(f"Syntax error: {e}")
        result["percentage"] = 0.0
        return result

    # Imports valid
    has_correct_imports = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names = [n.name for n in node.names]
            if "BossBase" in names:
                has_correct_imports = True
    if has_correct_imports:
        result["categories"]["imports_valid"] = {"score": RUBRIC["imports_valid"], "max": RUBRIC["imports_valid"], "msg": "Imports BossBase"}
    else:
        result["categories"]["imports_valid"] = {"score": 0, "max": RUBRIC["imports_valid"], "msg": "Missing BossBase import"}
        result["warnings"].append("Add 'from src.framework.entities.boss_base import BossBase'")

    # Find boss class
    boss_class: ast.ClassDef | None = None
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            bases = [b.id if isinstance(b, ast.Name) else "" for b in node.bases]
            if "BossBase" in bases:
                boss_class = node
                break

    if boss_class is None:
        result["categories"]["inherits_bossbase"] = {"score": 0, "max": RUBRIC["inherits_bossbase"], "msg": "No class inherits BossBase"}
        result["errors"].append("Create a class that inherits from BossBase")
        result["percentage"] = 0.0
        return result
    result["categories"]["inherits_bossbase"] = {"score": RUBRIC["inherits_bossbase"], "max": RUBRIC["inherits_bossbase"], "msg": f"Class '{boss_class.name}' inherits BossBase"}

    # Boss name config  # BUG-079 FIX: también acepta set_boss_name()
    has_boss_config = False
    for node in ast.walk(boss_class):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr == "boss_name":
                    has_boss_config = True
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "set_boss_name":
                has_boss_config = True
    if has_boss_config:
        result["categories"]["boss_name_config"] = {"score": RUBRIC["boss_name_config"], "max": RUBRIC["boss_name_config"], "msg": "Has boss_name config"}
    else:
        result["categories"]["boss_name_config"] = {"score": 5, "max": RUBRIC["boss_name_config"], "msg": "No explicit boss_name found"}

    # Find methods
    methods: dict[str, ast.FunctionDef] = {}
    for node in ast.iter_child_nodes(boss_class):
        if isinstance(node, ast.FunctionDef):
            methods[node.name] = node

    # Phase transitions (look for phase-related methods or state changes)
    phase_methods = [n for n in methods if "phase" in n.lower() or "phase" in n.lower()]
    state_transitions = 0
    for _name, func in methods.items():
        for node in ast.walk(func):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                doc = node.value.value
                if isinstance(doc, str) and "phase" in doc.lower():
                    state_transitions += 1
            if isinstance(node, ast.Attribute) and node.attr == "change_state":
                state_transitions += 1
    total_phase_indicators = len(phase_methods) + state_transitions
    if total_phase_indicators >= 2:
        result["categories"]["phase_transitions"] = {"score": RUBRIC["phase_transitions"], "max": RUBRIC["phase_transitions"], "msg": f"{total_phase_indicators} phase indicator(s)"}
    elif total_phase_indicators == 1:
        result["categories"]["phase_transitions"] = {"score": 8, "max": RUBRIC["phase_transitions"], "msg": "Only 1 phase indicator (need >=2)"}
        result["warnings"].append("Add a second phase (e.g. phase2 method or change_state call)")
    else:
        result["categories"]["phase_transitions"] = {"score": 0, "max": RUBRIC["phase_transitions"], "msg": "No phase transitions detected"}

    # Attack patterns
    #
    # AUD-104: antes esto buscaba métodos cuyo nombre contuviera "attack" o
    # "pattern". El framework NO usa esa convención: el jefe de referencia
    # llama a sus ataques `_do_stomp`, `_do_charge`, `_do_vine_toss`. El
    # único método que casaba era `on_attack_fired`, así que un jefe con
    # cuatro ataques se calificaba como si tuviera uno.
    #
    # Se cuenta ahora también el prefijo `_do_`, que es el que usa el
    # framework, y los ataques declarados en `BossPhase(attacks=[...])`.
    attack_methods = [
        n for n in methods
        if "attack" in n.lower() or "pattern" in n.lower() or n.startswith("_do_")
    ]
    attack_methods += _ataques_declarados_en_fases(tree)
    if len(attack_methods) >= 2:
        result["categories"]["attack_patterns"] = {"score": RUBRIC["attack_patterns"], "max": RUBRIC["attack_patterns"], "msg": f"{len(attack_methods)} attack method(s)"}
    elif len(attack_methods) == 1:
        result["categories"]["attack_patterns"] = {"score": 8, "max": RUBRIC["attack_patterns"], "msg": "Only 1 attack pattern (need >=2)"}
    else:
        result["categories"]["attack_patterns"] = {"score": 0, "max": RUBRIC["attack_patterns"], "msg": "No attack patterns found"}

    # HP thresholds
    hp_thresholds = 0
    for _name, func in methods.items():
        for node in ast.walk(func):
            if isinstance(node, ast.Compare):
                for c in [node.left, node.comparators]:
                    if isinstance(c, ast.Attribute) and "hp" in c.attr.lower():
                        hp_thresholds += 1
                    elif isinstance(c, ast.Name) and c.id == "self":
                        hp_thresholds += 1
            if isinstance(node, ast.If):
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute) and "hp" in child.attr.lower():
                        hp_thresholds += 1
    # AUD-104: la forma correcta de declarar umbrales en este framework es
    # `BossPhase(health_threshold=...)` dentro de `set_phases`, no un `if`
    # comparando contra `self.hp`. El jefe de referencia declara dos y
    # sacaba 0/10 porque el calificador sólo miraba comparaciones sueltas.
    hp_thresholds += _umbrales_en_fases(tree)

    if hp_thresholds >= 2:
        result["categories"]["hp_thresholds"] = {"score": RUBRIC["hp_thresholds"], "max": RUBRIC["hp_thresholds"], "msg": f"{hp_thresholds} HP threshold check(s)"}
    elif hp_thresholds == 1:
        result["categories"]["hp_thresholds"] = {"score": 5, "max": RUBRIC["hp_thresholds"], "msg": "Only 1 HP threshold (need >=2 for 2 phases)"}
    else:
        result["categories"]["hp_thresholds"] = {"score": 0, "max": RUBRIC["hp_thresholds"], "msg": "No HP threshold checks"}

    # Telegraph state
    # AUD-104: `telegraph_progress` y la duración del telegrafiado los
    # aporta `BossBase`. Un jefe que lo usa —o que declara un tiempo de
    # aviso en sus fases— está telegrafiando, aunque no escriba la palabra.
    has_telegraph = (
        "telegraph" in methods
        or "telegraph" in source.lower()
        or "windup" in source.lower()
        or "wind_up" in source.lower()
        or "aviso" in source.lower()
    )
    if has_telegraph:
        result["categories"]["telegraph_state"] = {"score": RUBRIC["telegraph_state"], "max": RUBRIC["telegraph_state"], "msg": "telegraph state/method found"}
    else:
        result["categories"]["telegraph_state"] = {"score": 0, "max": RUBRIC["telegraph_state"], "msg": "No telegraph state"}
        result["warnings"].append("Add a telegraph/wind-up state before attacks")

    # Respuesta al daño
    #
    # AUD-104: esto exigía un método llamado `take_damage` o `hurt`. **Esos
    # nombres no existen en el framework**: la API real es `apply_hit` y
    # `apply_hit_at`, las dos en `BossBase`. Ningún jefe correcto pasaba
    # este criterio, y el que lo pasara sería porque se había escrito su
    # propio sistema de daño en vez de usar el del motor — justo la lección
    # contraria a la que enseña la asignatura.
    #
    # Lo que sí es una decisión de diseño del estudiante es **cómo responde**
    # el jefe al daño: puntos débiles, hurtbox propia, animación de dolor, o
    # una extensión de `apply_hit`.
    respuestas = [
        nombre for nombre in (
            "apply_hit", "apply_hit_at", "take_damage", "hurt", "damage",
            "on_hit", "_build_hurtbox",
        ) if nombre in methods
    ]
    if "weak_points" in source or "add_weak_point" in source:
        respuestas.append("weak_points")
    if respuestas:
        result["categories"]["hurt_damage_states"] = {
            "score": RUBRIC["hurt_damage_states"], "max": RUBRIC["hurt_damage_states"],
            "msg": f"responde al daño: {', '.join(sorted(set(respuestas)))}",
        }
    else:
        result["categories"]["hurt_damage_states"] = {
            "score": 0, "max": RUBRIC["hurt_damage_states"],
            "msg": "el jefe no define ninguna respuesta al daño",
        }
        result["errors"].append(
            "Declara puntos débiles (`self.weak_points`), una hurtbox "
            "(`_build_hurtbox`) o extiende `apply_hit`. La API de daño del "
            "framework es `apply_hit` / `apply_hit_at`, no `take_damage`."
        )

    # Event connections
    event_refs = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and "emit" in func.attr.lower():
                event_refs += 1
            if isinstance(func, ast.Attribute) and "subscribe" in func.attr.lower():
                event_refs += 1
            if isinstance(func, ast.Attribute) and "publish" in func.attr.lower():
                event_refs += 1
    if event_refs >= 2:
        result["categories"]["event_connections"] = {"score": RUBRIC["event_connections"], "max": RUBRIC["event_connections"], "msg": f"{event_refs} event interaction(s)"}
    elif event_refs == 1:
        result["categories"]["event_connections"] = {"score": 5, "max": RUBRIC["event_connections"], "msg": "Only 1 event reference"}
    else:
        result["categories"]["event_connections"] = {"score": 0, "max": RUBRIC["event_connections"], "msg": "No event connections"}

    # Class structure
    method_count = len(methods)
    if method_count >= 5:
        result["categories"]["class_structure"] = {"score": RUBRIC["class_structure"], "max": RUBRIC["class_structure"], "msg": f"{method_count} methods"}
    elif method_count >= 3:
        result["categories"]["class_structure"] = {"score": 3, "max": RUBRIC["class_structure"], "msg": f"Only {method_count} methods"}
    else:
        result["categories"]["class_structure"] = {"score": 0, "max": RUBRIC["class_structure"], "msg": f"Only {method_count} methods (need >=5)"}

    total = sum(c["score"] for c in result["categories"].values())
    result["score"] = total
    result["max_score"] = sum(RUBRIC.values())
    result["percentage"] = round(total / result["max_score"] * 100, 1)
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Grade student boss Python files")
    parser.add_argument("paths", nargs="+", help="Python files or directories")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--dir", help="Scan directory for .py files")
    # AUD-370 — `--minimo` existe porque estos dos guiones **nunca podían
    # fallar**. El paso de CI que califica el material de referencia lleva
    # escrito desde AUD-104 que «si su nota baja, es que el calificador o el
    # jefe han dejado de estar de acuerdo, y eso hay que verlo antes de un
    # día de entrega» — y nadie miraba el número: el guion salía con 0 tanto
    # con 100/100 como con 40/100. Es el mismo defecto que AUD-353 (gate
    # comprobado por estar escrito) y AUD-356 (`--json` que nadie parseaba),
    # en un tercer sitio.
    #
    # Sin la bandera no cambia nada, y eso importa: calificar la entrega de
    # un estudiante **debe** salir con éxito aunque saque 40, porque el 40 es
    # el resultado, no un error de la herramienta.
    parser.add_argument("--minimo", type=float, default=None,
                        help="nota mínima exigida (0-100). Sin esto el guion informa y siempre sale con éxito, que es lo correcto al calificar a un estudiante y lo contrario de lo que CI necesita del material de referencia")
    args = parser.parse_args()

    py_files: list[Path] = []
    if args.dir:
        d = Path(args.dir)
        if d.exists():
            py_files.extend(d.rglob("*.py"))
    for p_str in args.paths:
        p = Path(p_str)
        if p.is_dir():
            py_files.extend(p.rglob("*.py"))
        elif p.exists():
            py_files.append(p)

    if not py_files:
        print("No Python files found.")
        return 1

    # AUD-104: no se califican los ficheros que no son un jefe.
    #
    # `grade_boss.py student_templates/boss_template/*.py` calificaba también
    # el `__init__.py` del paquete, le daba 0/100 y hundía la media a la
    # mitad. Un profesor pasando el calificador sobre `submissions/*/` el día
    # de la entrega habría visto una media falsa por cada paquete entregado.
    #
    # Se excluye también la clase base del framework: calificar `BossBase`
    # —que no hereda de sí misma y no declara fases— da 0/100 y no significa
    # nada. El CI lo hacía en cada ejecución.
    py_files = [
        f for f in set(py_files)
        if f.name != "__init__.py"
        and "__pycache__" not in f.parts
        and f.name != "boss_base.py"
    ]

    # AUD-107 — al recorrer un directorio, sólo son candidatos los ficheros que
    # **definen un jefe**.
    #
    # AUD-104 quitó `__init__.py` y `boss_base.py`, y con eso bastaba mientras
    # se calificaban plantillas. Sobre las entregas reales no basta ni de lejos:
    # `grade_boss.py src/stages/boss_paburu` calificaba los siete módulos del
    # paquete —la escena, la arena, los sprites, la introducción, los
    # guardianes— y le ponía 0/100 a cada uno por «no hereda de BossBase».
    # El jefe sacaba buena nota y la media impresa era **14,3 %**.
    #
    # Peor aún con boss_venado, que trae utilidades y pruebas: catorce ficheros
    # calificados, media 7,1 %, cuando su jefe saca 100. Un profesor que mire
    # la última línea suspende a quien organizó bien su código, que es
    # justamente lo que el curso pide.
    #
    # Un fichero sin subclase de `BossBase` no es un jefe mal hecho: no es un
    # jefe. Se excluye en vez de puntuarlo. Nombrar un fichero suelto sigue
    # calificándolo tal cual, para poder diagnosticar «¿por qué no lo detecta?».
    if any(Path(p).is_dir() for p in args.paths) or args.dir:
        candidatos = [f for f in py_files if _define_un_jefe(f)]
        if not candidatos:
            print("No se encontró ninguna clase que herede de BossBase en las "
                  "rutas indicadas.")
            print("Si esperabas que la hubiera, revisa que la clase declare "
                  "`class MiJefe(BossBase)`.")
            return 1
        py_files = candidatos

    if not py_files:
        print("No hay ficheros de jefe que calificar "
              "(se excluyen __init__.py y la clase base del framework).")
        return 1

    all_results: list[dict[str, Any]] = []
    for pyf in sorted(py_files):
        r = grade_boss(pyf)
        all_results.append(r)
        if not args.json:
            rel = display_path(pyf, _PROJECT_ROOT)
            print(f"\n{'='*50}")
            print(f"  {rel}")
            print(f"{'='*50}")
            for cat, data in sorted(r["categories"].items()):
                status = "[PASS]" if data["score"] >= data["max"] else "[WARN] " if data["score"] > 0 else "[FAIL]"
                print(f"  {status} {cat}: {data['score']}/{data['max']} — {data['msg']}")
            for err in r["errors"]:
                print(f"  [FAIL] ERROR: {err}")
            for w in r["warnings"]:
                print(f"  [WARN]  WARN: {w}")
            print(f"\n  GRADE: {r['score']}/{r['max_score']} ({r['percentage']}%)")

    if args.json:
        print(json.dumps(all_results, indent=2))

    # AUD-356 — mismo arreglo que en `grade_stage.py`, y por el mismo motivo:
    # el resumen humano detrás del documento hacía que `--json` no produjera
    # JSON parseable. Con la bandera puesta, el resumen va a stderr.
    resumen = sys.stderr if args.json else sys.stdout
    avg = sum(r["percentage"] for r in all_results) / len(all_results) if all_results else 0
    print(f"\n{'='*50}", file=resumen)
    print(f"  Total graded: {len(all_results)}", file=resumen)
    print(f"  Average grade: {avg:.1f}%", file=resumen)
    print(f"{'='*50}", file=resumen)

    if args.minimo is not None and avg < args.minimo:
        print(f"  [FAIL] media {avg:.1f} % por debajo del mínimo exigido "
              f"({args.minimo:.1f} %).", file=resumen)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
