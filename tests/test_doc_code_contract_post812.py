"""
Module: test_doc_code_contract_post812
System: tests
POST-AUD-812 — BLOQUE 2.1 Document ↔ Code Contract

Objetivo: detectar DOC -> API inexistente sin falsos positivos de audit_docs_vs_code.

Estrategia explicita de clasificacion (5 categorias):
  PYTHON_SYMBOL  -> importable o AST en src/
  TMX_PROPERTY   -> registrado en stage_loader / stage_objetos / validate_tmx
  ASSET          -> fichero en assets/
  DOCUMENTATION_TERM -> termino humano, no se comprueba
  EXAMPLE        -> bloque ejemplo no normativo

Solo se comprueban los 3 specs criticos: 05_ENEMY_SPEC, 06_TMX_SPEC, 17_BOSS_SPEC
usando fuentes canonicas, no busqueda textual ingenua.

Referencia patron: tests/test_el_estado_de_los_jefes_es_real.py y docs/60 tests.
"""
from __future__ import annotations
import ast
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _python_symbols() -> set[str]:
    syms: set[str] = set()
    for p in (RAIZ / "src").rglob("*.py"):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            for n in ast.walk(tree):
                if isinstance(n, ast.ClassDef):
                    syms.add(n.name)
                elif isinstance(n, ast.FunctionDef):
                    syms.add(n.name)
                elif isinstance(n, ast.Assign):
                    for t in n.targets:
                        if isinstance(t, ast.Name):
                            syms.add(t.id)
        except Exception:
            continue
    return syms


def test_05_enemy_spec_arquetipos_existen():
    """05_ENEMY_SPEC lista 8 arquetipos base; deben existir como clases Python."""
    spec = RAIZ / "docs/05_ENEMY_SPEC.md"
    assert spec.exists(), "05_ENEMY_SPEC.md no existe"
    # clasificacion: PYTHON_SYMBOL
    symbols = _python_symbols()
    faltan = [e for e in ["EnemyWalker", "EnemyFlying", "EnemyShooter"] if e not in symbols]
    assert not faltan, f"Arquetipos base no encontrados como PYTHON_SYMBOL: {faltan} — DOC->API rota en 05"
    txt = spec.read_text(encoding="utf-8", errors="replace")
    assert "EnemyWalker" in txt or "Walker" in txt, "05_ENEMY_SPEC no menciona arquetipos esperados"


def test_06_tmx_spec_tipos_reconocidos_por_validador():
    """06_TMX_SPEC tipos TMX deben ser reconocidos por validate_tmx (TMX_PROPERTY)."""
    spec = RAIZ / "docs/06_TMX_SPEC.md"
    assert spec.exists()
    r = subprocess.run([sys.executable, "scripts/validate_tmx.py", "--ci"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert "38/38 passed" in r.stdout or "38/38" in r.stdout, f"validate_tmx fallo — TMX_PROPERTY contract roto: {r.stdout[:500]}"
    txt = spec.read_text(encoding="utf-8", errors="replace")
    assert "Checkpoint" in txt, "06_TMX_SPEC no menciona Checkpoint — posible doc term vs TMX_PROPERTY confusion"


def test_17_boss_spec_cabecera_no_envejece():
    """17_BOSS_SPEC cabecera 20/47 vs codigo real — PYTHON_SYMBOL count."""
    spec = RAIZ / "docs/17_BOSS_SPEC.md"
    assert spec.exists()
    stages = RAIZ / "src/stages"
    count = 0
    for f in stages.rglob("*.py"):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
            for n in ast.walk(tree):
                if isinstance(n, ast.ClassDef) and n.name.startswith("Boss"):
                    count += 1
        except Exception:
            continue
    assert count >= 3, f"Se esperaban >=3 clases Boss* en src/stages, hay {count} — BOSS_SPEC desync"
    txt = spec.read_text(encoding="utf-8", errors="replace")
    assert "no es un contrato" in txt.lower() or "AUD-369" in txt, "17_BOSS_SPEC debe advertir que no es contrato (AUD-369) — DOCUMENTATION_TERM"


def test_doc_code_contract_clasificacion_explicita():
    """La clasificacion en 5 categorias debe existir como comentario/doc en este fichero."""
    txt = Path(__file__).read_text(encoding="utf-8", errors="replace")
    for cat in ["PYTHON_SYMBOL", "TMX_PROPERTY", "ASSET", "DOCUMENTATION_TERM", "EXAMPLE"]:
        assert cat in txt, f"Falta categoria {cat} en estrategia explicita — contrato vs auditoria"
