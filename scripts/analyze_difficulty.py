"""
AUD-647 — analyze_difficulty.py: telemetría de curva de dificultad.

Sin datos de partida, genera una plantilla vacía para que el diseñador
la rellene. Con datos (saves/*.json), agrega muertes, tiempo y reintentos.

Uso:
    python scripts/analyze_difficulty.py
    python scripts/analyze_difficulty.py --saves=saves/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def analizar_saves(saves_dir: Path) -> list[dict]:
    """Lee los ficheros de guardado y extrae métricas de dificultad."""
    registros = []
    for fichero in sorted(saves_dir.glob("*.json")):
        try:
            data = json.loads(fichero.read_text(encoding="utf-8"))
            registro = {
                "fichero": fichero.name,
                "escenario": data.get("stage_id", "?"),
                "muertes": data.get("deaths", data.get("muertes", 0)),
                "tiempo_segundos": data.get("time", data.get("tiempo", 0)),
                "reintentos": data.get("retries", 0),
            }
            registros.append(registro)
        except (json.JSONDecodeError, KeyError):
            pass
    return registros


def generar_plantilla() -> str:
    """Genera una plantilla vacía para el diseñador."""
    return """
# Análisis de curva de dificultad
# ================================
# No hay datos de partida en saves/. Generando plantilla:
#
# | Escenario | Muertes esperadas | Tiempo objetivo | Reintentos máx |
# |-----------|------------------|-----------------|----------------|
# | stage0    | 0-2              | 10 min          | 3              |
# | stage1_1  | 2-5              | 15 min          | 5              |
# | ...       | ...              | ...             | ...            |
#
# Para recopilar datos reales, jugar el juego y exportar saves/.
"""


def generar_informe(registros: list[dict]) -> str:
    """Genera un informe con las métricas agregadas."""
    if not registros:
        return generar_plantilla()

    lineas = [
        "# Análisis de curva de dificultad",
        "",
        f"Ficheros analizados: {len(registros)}",
        "",
        "| Fichero | Escenario | Muertes | Tiempo (s) | Reintentos |",
        "|---------|-----------|---------|------------|------------|",
    ]
    for r in registros:
        lineas.append(
            f"| {r['fichero']} | {r['escenario']} "
            f"| {r['muertes']} | {r['tiempo_segundos']} | {r['reintentos']} |"
        )

    # Agregados
    total_muertes = sum(r["muertes"] for r in registros)
    total_tiempo = sum(r["tiempo_segundos"] for r in registros)
    max_reintentos = max((r["reintentos"] for r in registros), default=0)

    lineas.extend([
        "",
        f"Total muertes: {total_muertes}",
        f"Tiempo total: {total_tiempo}s",
        f"Max reintentos: {max_reintentos}",
    ])

    return "\n".join(lineas) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analiza curva de dificultad")
    parser.add_argument("--saves", type=Path, default=RAIZ / "saves",
                        help="Directorio de partidas guardadas")
    args = parser.parse_args()

    registros = analizar_saves(args.saves)
    informe = generar_informe(registros)
    print(informe)
    return 0


if __name__ == "__main__":
    sys.exit(main())