#!/usr/bin/env python3
"""
check_change_safety.py — Gate de seguridad ante cambios (invariante CLAUDE.md §3.9).

Toda modificación futura debe demostrar qué certificación afecta y ejecutar
automáticamente la regresión correspondiente.

Uso:
    python scripts/check_change_safety.py              # informa qué familias toca el diff actual
    python scripts/check_change_safety.py --run        # informa + ejecuta las regresiones mínimas
    python scripts/check_change_safety.py --ci         # verifica trazabilidad (commit) + ejecuta; falla si falta

Matriz autoritativa: docs/AUD-800_REGRESSION_MATRIX.md
Guía: docs/CHANGE_SAFETY_GUIDE.md
Prueba: tests/test_change_safety.py
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# ── Matriz familia → patrones → certificación → regresión ────────────────
# Orden importa: primera coincidencia gana para informar, pero si un fichero
# toca varias familias se acumulan todas en el resultado final.

MATRIZ: list[tuple[str, list[str], str, list[str]]] = [
    (
        "RENDERER",
        ["src/engine/render/**"],
        "CERT-RENDERER",
        [
            "python -m pytest tests/test_render_pipeline.py tests/test_visual_composition.py tests/test_visual_regression.py -q",  # noqa: E501
            "python scripts/validate_tmx.py --ci",
        ],
    ),
    (
        "CAMERA/STAGE",
        ["src/framework/stage/camera.py", "src/framework/stage/**"],
        "CERT-CAMERA",
        [
            "python -m pytest tests/test_camera.py -k shake -q",
            "python -m pytest tests/test_stage0_reference.py tests/test_dynamic_visual.py -q",
        ],
    ),
    (
        "HUD",
        ["src/engine/ui/hud*.py", "src/engine/core/display.py"],
        "CERT-HUD",
        [
            "python -m pytest tests/test_hud.py tests/test_visual_composition.py -k hud -q",
        ],
    ),
    (
        "PLAYER",
        ["src/framework/entities/player*.py", "src/framework/physics/**"],
        "CERT-PLAYER",
        [
            "python -m pytest tests/test_player*.py tests/test_stage0_reference.py::test_player_spawn_feet_ground -q",
        ],
    ),
    (
        "TMX",
        ["assets/maps/**.tmx", "src/framework/stage/stage_loader.py"],
        "CERT-TMX",
        [
            "python scripts/validate_tmx.py --ci",
            "python scripts/validate_stage_reference.py",
            "python scripts/grade_stage.py assets/maps/ --json",
        ],
    ),
    (
        "ENEMIES",
        ["src/framework/entities/enemy_*.py"],
        "CERT-ENEMIES",
        [
            "python -m pytest tests/test_enemy*.py -q",
            "python scripts/check_orphan_systems.py",
        ],
    ),
    (
        "BOSS",
        ["src/stages/boss_*"],
        "CERT-BOSS",
        [
            "python -m pytest tests/test_boss*.py -q",
            "python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json",
        ],
    ),
    (
        "INPUT",
        ["src/engine/input/**"],
        "CERT-INPUT",
        [
            "python -m pytest tests/test_input_manager.py tests/test_keybinding_scene.py -q",
        ],
    ),
    (
        "STATE",
        ["src/engine/scene/**", "src/engine/core/game_context.py"],
        "CERT-STATE",
        [
            "python -m pytest tests/test_game_state*.py tests/test_state_integration.py -q",
        ],
    ),
    (
        "AUDIO",
        ["src/engine/audio/**"],
        "CERT-AUDIO",
        [
            "python -m pytest tests/test_audio*.py -q",
        ],
    ),
    (
        "SAVE",
        ["src/engine/core/save*.py", "src/engine/core/user_settings.py"],
        "CERT-SAVE",
        [
            "python -m pytest tests/test_save*.py tests/test_persistence*.py -q",
        ],
    ),
    (
        "UI",
        ["src/engine/scenes/**", "src/framework/ui/**"],
        "CERT-UI",
        [
            "python -m pytest tests/test_ui*.py tests/test_accessibility.py -q",
        ],
    ),
    (
        "LOADING",
        ["src/engine/scenes/loading_scene.py"],
        "CERT-LOADING",
        [
            "python -m pytest tests/test_loading*.py -q",
        ],
    ),
    (
        "VFX",
        ["src/framework/vfx/**", "src/engine/core/gpu_effects.py"],
        "CERT-VFX",
        [
            "python -m pytest tests/test_vfx*.py tests/benchmarks/test_render_benchmark.py -q",
        ],
    ),
    (
        "LOCALIZATION",
        ["locale/**", "src/engine/core/i18n.py"],
        "CERT-LOCALIZATION",
        [
            "python scripts/check_translations.py --ci",
            "python -m pytest tests/test_documentacion_en_espanol.py -q",
        ],
    ),
    (
        "PERFORMANCE",
        ["src/engine/core/clock.py", "src/engine/render/sprite_batch.py"],
        "CERT-PERFORMANCE",
        [
            "python -m pytest tests/benchmarks/test_performance_budget.py -q",
        ],
    ),
    (
        "ASSETS",
        ["assets/**", "src/engine/utils/asset_loader.py"],
        "CERT-ASSETS",
        [
            "python scripts/validate_assets.py",
            "python -m pytest tests/test_asset*.py -q",
        ],
    ),
    (
        "DOCS",
        ["docs/**", "CLAUDE.md", "CONTRIBUTING.md", "README.md", "CHANGELOG.md", "KNOWN_GAPS.md"],
        "CERT-DOCS",
        [
            "python scripts/check_doc_symbols.py --ci",
            "python -m pytest tests/test_el_indice_maestro_cuenta_bien.py -q",
        ],
    ),
    (
        "BUILD",
        ["pyproject.toml", ".github/workflows/ci.yml", "mypy_scope.txt", "scripts/**", "tests/**"],
        "CERT-BUILD",
        [
            "python -m ruff check src/engine src/framework src/stages/stage0 tests scripts tools",
            "python -m pytest tests/test_change_safety.py -q",
        ],
    ),
]

# Prefijos aceptados en mensaje de commit para trazabilidad
PREFIJOS_TRAZABILIDAD = re.compile(r"(AUD-\d+|CERT-[A-Z\-]+|GAP-\d+):")


def _git_diff_files(base: str | None = None) -> list[str]:
    """Ficheros modificados respecto a base (o HEAD si base None)."""
    # Detecta staged + unstaged + untracked (excluye .venv/.git)
    # En CI: compara contra origin/dev o HEAD~1 si existe
    cmds: list[list[str]] = []
    if base:
        cmds.append(["git", "diff", "--name-only", base])
    else:
        # 1) cambios staged + unstaged vs HEAD
        cmds.append(["git", "diff", "--name-only", "HEAD"])
        # 2) untracked
        #  se añade después

    ficheros: set[str] = set()
    for cmd in cmds:
        try:
            out = subprocess.check_output(cmd, cwd=RAIZ, text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                line = line.strip()
                if line:
                    ficheros.add(line)
        except subprocess.CalledProcessError:
            pass

    # Untracked (no ignorados)
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=RAIZ,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        for line in out.splitlines():
            line = line.strip()
            if line:
                ficheros.add(line)
    except subprocess.CalledProcessError:
        pass

    # Fallback si HEAD no existe (repo recién iniciado)
    if not ficheros:
        try:
            out = subprocess.check_output(["git", "diff", "--name-only"], cwd=RAIZ, text=True)
            for line in out.splitlines():
                if line.strip():
                    ficheros.add(line.strip())
        except subprocess.CalledProcessError:
            pass

    return sorted(ficheros)


def _familias_para_fichero(fichero: str) -> list[tuple[str, str, list[str]]]:
    """Devuelve lista de (familia, cert, regresiones) que matchean el fichero."""
    res: list[tuple[str, str, list[str]]] = []
    for familia, patrones, cert, regresiones in MATRIZ:
        for pat in patrones:
            base = pat.removesuffix("/**") if pat.endswith("/**") else pat
            if fnmatch.fnmatch(fichero, pat) or fnmatch.fnmatch(fichero, base):
                res.append((familia, cert, regresiones))
                break
            # Soporte ** sin fnmatch recursivo perfecto: check prefix
            if pat.endswith("/**"):
                pref = pat[:-3]
                if fichero.startswith(pref + "/") or fichero == pref:
                    res.append((familia, cert, regresiones))
                    break
    return res


def mapear_ficheros(ficheros: list[str]) -> dict[str, dict]:
    """Agrupa ficheros por familia."""
    mapa: dict[str, dict] = {}
    for f in ficheros:
        # Ignora temporales y caches
        if any(x in f for x in [".venv/", ".mypy_cache/", ".ruff_cache/", ".pytest_cache/", "__pycache__/", ".git/"]):
            continue
        familias = _familias_para_fichero(f)
        for familia, cert, regresiones in familias:
            if familia not in mapa:
                mapa[familia] = {"cert": cert, "ficheros": [], "regresiones": regresiones}
            mapa[familia]["ficheros"].append(f)
    return mapa


def _commit_msg() -> str:
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=RAIZ,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out
    except subprocess.CalledProcessError:
        return ""


def verificar_trazabilidad(mapa: dict[str, dict]) -> tuple[bool, str]:
    """¿El último commit declara certificación si hay cambios en src/assets?"""
    if not mapa:
        return True, "sin familias afectadas — no exige trazabilidad"
    # Solo exige trazabilidad si hay familias que no sean DOCS puras
    familias_no_docs = {k for k in mapa if k != "DOCS"}
    if not familias_no_docs:
        return True, "solo DOCS — no exige CERT-"
    msg = _commit_msg()
    if PREFIJOS_TRAZABILIDAD.search(msg):
        return True, f"trazabilidad OK — mensaje contiene {PREFIJOS_TRAZABILIDAD.search(msg).group(0)}"
    return False, (
        "FALTA TRAZABILIDAD: hay cambios en "
        + ", ".join(sorted(familias_no_docs))
        + " pero el último commit no declara certificación.\n"
        + "  Esperado: 'AUD-800: ...' o 'CERT-RENDERER: ...' o 'GAP-NNN:' en el mensaje.\n"
        + "  Ver docs/CHANGE_SAFETY_GUIDE.md §1. Mensaje actual:\n"
        + "  ---\n"
        + msg.strip()
        + "\n  ---\n"
        + "  Sugerencia: git commit --amend -m \"AUD-800: descripción — "
        + ", ".join(sorted(mapa[k]["cert"] for k in familias_no_docs))
        + "\""
    )


def _run_one(cmd: str) -> int:
    print(f"\n$ {cmd}")
    # Necesita SDL dummy para pygame
    env = os.environ.copy()
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    env.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    # Ejecuta via shell para soportar pipes y globs de pytest
    result = subprocess.run(cmd, shell=True, cwd=RAIZ, env=env)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate de seguridad ante cambios — CLAUDE.md §3.9")
    parser.add_argument("--run", action="store_true", help="ejecuta las regresiones mínimas detectadas")
    parser.add_argument("--ci", action="store_true", help="verifica trazabilidad y ejecuta; falla si falta")
    parser.add_argument("--base", type=str, default=None, help="base git para diff (ej. origin/dev)")
    parser.add_argument("--check", action="store_true", help="solo informa, no ejecuta (alias defecto)")
    args = parser.parse_args()

    ficheros = _git_diff_files(args.base)
    if not ficheros:
        print("Sin cambios detectados (git diff vacío) — nada que verificar.")
        if args.ci:
            print("CI: PASS (sin cambios)")
        return 0

    mapa = mapear_ficheros(ficheros)

    print("=" * 72)
    print("CHANGE SAFETY — Invariante CLAUDE.md §3.9")
    print("=" * 72)
    print(f"Ficheros cambiados: {len(ficheros)}")
    for f in ficheros[:30]:
        print(f"  {f}")
    if len(ficheros) > 30:
        print(f"  ... y {len(ficheros)-30} más")
    print()

    if not mapa:
        print("Ningún fichero cae en familias certificadas — no hay regresión mínima obligatoria.")
        print("Sugerencia: si es docs/ puro, asegúrate de pasar check_doc_symbols.")
        if args.ci:
            print("CI: PASS")
        return 0

    print("Familias afectadas:")
    todas_regresiones: list[str] = []
    vistos: set[str] = set()
    for familia, info in sorted(mapa.items()):
        cert = info["cert"]
        print(f"  {familia:15} {cert:18}  ({len(info['ficheros'])} ficheros)")
        for f in info["ficheros"][:5]:
            print(f"    - {f}")
        if len(info["ficheros"]) > 5:
            print(f"    ... y {len(info['ficheros'])-5} más")
        print(f"    regresión: {info['regresiones'][0]}")
        if len(info["regresiones"]) > 1:
            for r in info["regresiones"][1:]:
                print(f"               {r}")
        for r in info["regresiones"]:
            if r not in vistos:
                todas_regresiones.append(r)
                vistos.add(r)
    print()
    print("Comandos de regresión (unión mínima):")
    for cmd in todas_regresiones:
        print(f"  {cmd}")
    print()

    # Verificar trazabilidad si --ci
    if args.ci or args.run:
        ok, msg = verificar_trazabilidad(mapa)
        print(f"Trazabilidad: {msg}")
        if not ok:
            print("\nFALLA: falta declarar certificación en el mensaje del commit.")
            print("Ver docs/CHANGE_SAFETY_GUIDE.md §1 y CLAUDE.md §3.9")
            if args.ci:
                return 2
            # En --run no bloquea, solo avisa
            print("Continuando con regresiones de todos modos (--run)...")
        else:
            print("Trazabilidad: OK")
        print()

    if args.run or args.ci:
        print("Ejecutando regresiones mínimas...")
        print("-" * 72)
        fallos = 0
        for cmd in todas_regresiones:
            rc = _run_one(cmd)
            if rc != 0:
                print(f"FALLA: {cmd} -> {rc}")
                fallos += 1
            else:
                print(f"PASS: {cmd}")
        print("-" * 72)
        if fallos:
            print(f"RESULTADO: {fallos}/{len(todas_regresiones)} regresiones FALLARON")
            return 1
        print(f"RESULTADO: {len(todas_regresiones)}/{len(todas_regresiones)} regresiones PASS")
        return 0
    else:
        print("Sugerencia: ejecuta con --run para correr automáticamente estas regresiones.")
        print("  python scripts/check_change_safety.py --run")
        return 0


if __name__ == "__main__":
    sys.exit(main())
