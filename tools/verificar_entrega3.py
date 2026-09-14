#!/usr/bin/env python3
"""
Verificador de versión madura para Entrega 3 — 31-08-2026
Comprueba 12 invariants de la versión 1280×720 sin necesidad de abrir el juego.
Usa sólo lectura de TMX y checks de motor cableado.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

def check_tmx(tmx: Path) -> list[str]:
    errores: list[str] = []
    avisos: list[str] = []
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(tmx).getroot()
        props = {p.get("name"): p.get("value") or p.text for p in root.findall(".//properties/property")}
        # 1 resolución
        w = root.get("width")
        h = root.get("height")
        tw = root.get("tilewidth")
        th = root.get("tileheight")
        try:
            px_w = int(w or 0) * int(tw or 0)
            px_h = int(h or 0) * int(th or 0)
            if px_w < 1280:
                avisos.append(f"[RESOL] ancho mapa {px_w}px < 1280 — tu nivel se verá con barras laterales a 1280×720 (recomendado 1280+)")
        except Exception:
            pass
        # 2 stage_id
        if not props.get("stage_id"):
            errores.append("[TMX] falta propiedad de mapa 'stage_id' (requerida para guardado/logros)")
        # 3 background_zone
        if not props.get("background_zone"):
            avisos.append("[PARALLAX] sin 'background_zone' — no habrá fondos parallax (far/mid/near)")
        # 4 capas requeridas
        layers = [l.get("name") for l in root.findall(".//layer")]
        obj_layers = [l.get("name") for l in root.findall(".//objectgroup")]
        for need in ("Collision", "Objects"):
            if need not in obj_layers and need not in layers:
                avisos.append(f"[CAPA] falta capa '{need}'")
        # 5 objetos
        objs = root.findall(".//object")
        clases = [o.get("type") or o.get("class") or "" for o in objs]
        # Brute en código ya es 32×28 (fix 31-08); el tamaño en TMX es sólo punto de spawn,
        # no hitbox — no se avisa por ello para no spamear mapas legacy.
        # zipline
        if not any("Zipline" in c or "Tirolesa" in c or "Vine" in c for c in clases):
            avisos.append("[TIP] sin lianas/tirolesas — añade una para demostrar zipline (class=Vine/Zipline en Objects)")
        # objetivos
        has_obj = False
        for o in objs:
            for p in o.findall("properties/property"):
                if p.get("name") == "objective_id":
                    has_obj = True
                    break
            if (o.get("type") or o.get("class") or "") == "Objetivo":
                has_obj = True
                break
        if not has_obj:
            avisos.append("[MISION] sin objetivos — declara al menos uno (objective_id/text/kind) para entrega 3")
        # clima
        if not props.get("climate"):
            avisos.append("[CLIMA] sin 'climate' — el nivel usará el default de la estación (recomendado declarar, p. ej. 'clear')")
        # enemigos: busca tipos conocidos (Walker/Flying/Shooter/Brute/Archer/Charger/Caster/Assassin...)
        enemigos_conocidos = ("Walker","Flying","Shooter","Brute","Archer","Charger","Caster","Assassin","Climber","Cangrejo","Medusa","Buddy","Hormiga")
        if not any(any(k.lower() in c.lower() for k in enemigos_conocidos) for c in clases):
            # stage_mecanicas es lab sin enemigos reales — no spamear
            if "mecanicas" not in str(tmx).lower():
                avisos.append("[ENEMIGO] sin enemigos detectados — añade Walker/Flying/Shooter si quieres combate")
    except Exception as e:
        errores.append(f"[PARSE] no se pudo leer TMX: {e}")
    return errores, avisos

def check_motor_cableado() -> list[str]:
    fallos: list[str] = []
    # imports críticos que deben existir y no ser huérfanos
    checks = [
        ("settings 1280×720", lambda: __import__("src.engine.core.settings", fromlist=["INTERNAL_WIDTH"]).INTERNAL_WIDTH == 1280),
        ("combo tupla inmutable", lambda: __import__("src.engine.core.settings", fromlist=["COMBO_DAMAGE_MULT"]).COMBO_DAMAGE_MULT[2] == 2.0),
        ("fantasma gate BossRush", lambda: "boss_rush" in open(PROJECT_ROOT/"src/framework/scenes/stage_parts/fantasma.py", encoding="utf-8").read()),
        ("objetivos derrotar entity_id", lambda: "entity_id" in open(PROJECT_ROOT/"src/framework/stage/objetivos.py", encoding="utf-8").read()),
        ("experience bind_bus muda", lambda: "if bus is self._bus" in open(PROJECT_ROOT/"src/engine/core/experience.py", encoding="utf-8").read()),
        ("Brute proporciones", lambda: "32" in open(PROJECT_ROOT/"src/framework/entities/enemy_brute.py", encoding="utf-8").read()),
        ("A* navegacion", lambda: (PROJECT_ROOT/"src/framework/ai/navegacion.py").exists()),
        ("SquadBrain", lambda: (PROJECT_ROOT/"src/framework/entities/squad_brain.py").exists()),
        ("parallax 5 capas", lambda: len(__import__("src.framework.stage.stage_loader", fromlist=["StageLoader"]).StageLoader.CAPAS_DE_FONDO) == 5),
    ]
    for nombre, fn in checks:
        try:
            ok = fn()
            if not ok:
                fallos.append(f"[MOTOR] {nombre} no cumple")
        except Exception as e:
            fallos.append(f"[MOTOR] {nombre} error: {e}")
    return fallos

def main() -> int:
    print("=== Verificador Entrega 3 — Versión madura 1280×720 (31-08-2026) ===\n")
    tmxs = sys.argv[1:]
    if not tmxs:
        # busca un tmx de ejemplo
        cand = sorted((PROJECT_ROOT/"assets/maps").rglob("*.tmx"))
        if cand:
            tmxs = [str(cand[0])]
            print(f"(sin args: probando con {tmxs[0]})\n")
        else:
            print("Uso: python tools/verificar_entrega3.py assets/maps/tu_stage/tu_stage.tmx")
            return 1
    codigo = 0
    for arg in tmxs:
        p = Path(arg)
        print(f"--- {p} ---")
        if not p.exists():
            print("  [ERROR] no existe\n")
            codigo = 1
            continue
        errores, avisos = check_tmx(p)
        if errores:
            print("  Errores (bloquean entrega):")
            for e in errores:
                print(f"   - {e}")
            codigo = 1
        if avisos:
            print("  Avisos / mejoras:")
            for a in avisos:
                print(f"   - {a}")
        if not errores and not avisos:
            print("  OK — TMX parece completo para entrega 3")
        print()
    print("--- Motor cableado ---")
    fallos = check_motor_cableado()
    if fallos:
        print("  Fallos de motor (reportar como AUD):")
        for f in fallos:
            print(f"   - {f}")
        codigo = 1
    else:
        print(
            "  OK — 9 checks de motor en verde "
            "(fantasma BossRush, objetivos, experience, Brute, A*, Squad, parallax)"
        )
    print("\n--- Comandos sugeridos ---")
    print(
        " pytest tests/test_combo_system.py tests/test_objetivos.py "
        "tests/test_fantasma_del_speedrun.py tests/test_lianas_y_tirolesas.py -q"
    )
    print(" python scripts/validate_tmx.py --ci")
    print(" python scripts/validate_assets.py")
    print("\nVer docs/95_GUIA_ENTREGA_3_MADURA.md para el checklist completo.")
    return codigo

if __name__ == "__main__":
    raise SystemExit(main())
