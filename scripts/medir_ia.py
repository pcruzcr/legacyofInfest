#!/usr/bin/env python3
"""¿Acierta más la IA predictiva que la heurística? — AUD-368.

Por qué existe
==============

`docs/89` lleva desde su primera ronda con el hallazgo P6 abierto: *«la capa
ML no tiene métrica de acierto»*. `docs/63` lo repite. `CLAUDE.md` §3 invariante
7 fija la política —scikit-learn es opcional y sin él la IA cae a una
heurística determinista— pero **nadie había medido cuánto aporta el modelo**.

Sin esa medición, la respuesta a «¿merece la pena la capa ML?» sólo podía ser
una opinión, y el prompt maestro (`docs/69` §8, D6) es explícito: *«si propones
ML, compara contra la heurística determinista con una medición, no con una
opinión»*.

Lo que este guion mide, y lo que ese número significa
=====================================================

Mide el **acuerdo** entre lo que decide el modelo y lo que habrían decidido las
reglas, sobre estados de juego que el modelo no ha visto.

Y aquí está lo que hace que ese número se lea al revés de como parece. El
modelo **se entrena exclusivamente con la salida de las propias reglas**:
`squad_brain.py:171-180` alimenta cada ejemplo con la decisión que la
heurística acaba de tomar, «para que aprenda de una política válida en lugar
de de ruido». Es una decisión deliberada y sensata, y tiene una consecuencia
que no estaba escrita en ninguna parte:

    el techo del modelo es imitar a la heurística.

No puede ser mejor: no existe ninguna señal en el sistema que le diga que una
acción funcionó y otra no —no hay recompensa, ni resultado de combate, ni
etiqueta humana—. Así que el acuerdo con las reglas **no es una nota de
acierto: es una nota de fidelidad**, y todo lo que le falte para el 100 % es
degradación pura respecto a ejecutar las reglas directamente.

Eso convierte la pregunta de P6 en una que sí se puede contestar con un
número, y este guion la contesta.

Uso
===

    python scripts/medir_ia.py
    python scripts/medir_ia.py --estados 4000 --semilla 7
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _estados(n: int, semilla: int) -> list[dict[str, float]]:
    """Estados de combate plausibles, reproducibles.

    Los rangos salen de lo que el juego produce: distancias de 0 a 400 px
    (más allá el culling de AUD-279 ni simula al enemigo), salud normalizada y
    las dos banderas de terreno que la heurística consulta.
    """
    rnd = random.Random(semilla)
    return [
        {
            "dist": rnd.uniform(0.0, 400.0),
            "health_pct": rnd.uniform(0.0, 1.0),
            "player_health_pct": rnd.uniform(0.0, 1.0),
            "has_ranged": float(rnd.random() < 0.35),
        }
        for _ in range(n)
    ]


def _fila_de_rasgos(predictor, estado: dict[str, float]) -> list[float]:
    """Traduce un estado al vector que el modelo consume.

    Se usa `extract_features` del propio predictor —no una copia— para que la
    medición no se desincronice del sistema medido, que es el defecto que este
    repositorio ha encontrado tres veces en sus propias herramientas
    (AUD-104, AUD-106, AUD-107).
    """
    return predictor.extract_features(
        self_x=0.0, self_y=0.0,
        player_x=estado["dist"], player_y=0.0,
        player_health=estado["player_health_pct"],
        self_health=estado["health_pct"],
        player_state="idle",
        wall_ahead=False, ledge_ahead=False,
    )


def medir(n_entreno: int, n_prueba: int, semilla: int) -> dict[str, float]:
    from src.framework.entities.ai_predictor import BehaviorPredictor

    predictor = BehaviorPredictor()
    entreno = _estados(n_entreno, semilla)
    prueba = _estados(n_prueba, semilla + 1)

    # Fase 1: exactamente lo que hace el juego — las reglas deciden y su
    # decisión se le da al modelo como etiqueta.
    for estado in entreno:
        accion = predictor.get_rule_based_action(**estado)  # type: ignore[arg-type]
        predictor.add_example(
            _fila_de_rasgos(predictor, estado),
            predictor.action_index(accion),
        )

    if not predictor.is_trained:
        return {"entrenado": 0.0}

    # Fase 2: sobre estados nuevos, ¿coincide el modelo con las reglas?
    filas = [_fila_de_rasgos(predictor, e) for e in prueba]
    predichas = predictor.predict_batch(filas) or []
    esperadas = [
        predictor.get_rule_based_action(**e) for e in prueba  # type: ignore[arg-type]
    ]
    aciertos = sum(1 for p, r in zip(predichas, esperadas, strict=True) if p == r)

    discrepancias: dict[str, int] = {}
    for p, r in zip(predichas, esperadas, strict=True):
        if p != r:
            discrepancias[f"{r} -> {p}"] = discrepancias.get(f"{r} -> {p}", 0) + 1

    return {
        "entrenado": 1.0,
        "fidelidad": aciertos / len(prueba) if prueba else 0.0,
        "discrepancias": discrepancias,  # type: ignore[dict-item]
        "ejemplos": float(len(entreno)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--estados", type=int, default=2000,
                    help="estados de entrenamiento (el de prueba es la mitad)")
    ap.add_argument("--semilla", type=int, default=42)
    args = ap.parse_args()

    r = medir(args.estados, args.estados // 2, args.semilla)
    if not r.get("entrenado"):
        print("El modelo no llegó a entrenarse. Sin métrica.")
        return 1

    fidelidad = float(r["fidelidad"])
    print(f"  Ejemplos de entrenamiento : {int(r['ejemplos'])}")
    print(f"  Fidelidad a la heurística : {fidelidad:.1%}")
    print()
    print("  Cómo se lee este número:")
    print("  El modelo se entrena SÓLO con la salida de las reglas, así que su")
    print("  techo es imitarlas. Esto no es acierto: es fidelidad, y lo que le")
    print(f"  falta para el 100 % ({1 - fidelidad:.1%}) es degradación pura")
    print("  respecto a ejecutar las reglas directamente.")
    discrepancias = r.get("discrepancias") or {}
    if discrepancias:
        print("\n  Dónde se desvía (regla -> modelo):")
        for par, veces in sorted(discrepancias.items(),  # type: ignore[union-attr]
                                 key=lambda kv: -kv[1])[:8]:
            print(f"    {par:32s} {veces}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
