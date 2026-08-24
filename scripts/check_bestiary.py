"""
check_bestiary.py — valida `data/bestiary.json`.

Por qué (AUD-199)
-----------------
Los textos de las fichas clásicas del bestiario vivían en `bestiary.py`. Al
pasarlos a un fichero de datos hay que vigilar que ese fichero no se pudra en
silencio: un id mal escrito hace que la especie no se muestre nunca, y una
`hp` en cero rompe la ficha. Este script comprueba la forma del catálogo.

Uso:
    python scripts/check_bestiary.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
_FICHERO = _RAIZ / "data" / "bestiary.json"

#: Los nueve arquetipos clásicos que el motor espera encontrar.
CLASICOS = {
    "walker", "flying", "shooter", "charger", "archer",
    "brute", "caster", "assassin", "boss_venado",
}


def validar() -> int:
    problemas = 0

    if not _FICHERO.exists():
        print(f"[FALTA] {_FICHERO}")
        return 1
    try:
        datos = json.loads(_FICHERO.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[ROTO ] {_FICHERO}: {e}")
        return 1

    especies = datos.get("species", []) if isinstance(datos, dict) else None
    if not isinstance(especies, list):
        print("[ERROR] «species» no es una lista")
        problemas += 1
        especies = []
    if not especies:
        print("[ERROR] el catálogo del bestiario está vacío")
        problemas += 1

    for i, especie in enumerate(especies):
        if not isinstance(especie, dict):
            print(f"[ERROR] la especie {i} no es un objeto")
            problemas += 1
            continue
        etiqueta = especie.get("id", f"#{i}")
        for campo in ("id", "name", "description"):
            valor = especie.get(campo)
            if not isinstance(valor, str) or not valor.strip():
                print(f"[ERROR] «{etiqueta}» sin «{campo}» no vacío")
                problemas += 1
        hp = especie.get("hp", 0)
        if not isinstance(hp, (int, float)) or hp <= 0:
            print(f"[ERROR] «{etiqueta}» con «hp» no positiva")
            problemas += 1
        dano = especie.get("damage", 0)
        if not isinstance(dano, (int, float)) or dano < 0:
            print(f"[ERROR] «{etiqueta}» con «damage» negativo")
            problemas += 1

    ids = [e.get("id") for e in especies if isinstance(e, dict)]
    duplicados = {i for i in ids if ids.count(i) > 1}
    if duplicados:
        print(f"[ERROR] ids duplicados: {sorted(duplicados)}")
        problemas += 1
    faltan = sorted(CLASICOS - set(ids))
    if faltan:
        print(f"[ERROR] faltan arquetipos clásicos: {faltan}")
        problemas += 1

    print(f"{len(especies)} fichas definidas.")
    if problemas:
        print(f"{problemas} problema(s) en {_FICHERO.name}")
        return 1
    print("Catálogo del bestiario en orden.")
    return 0


def main() -> int:
    argparse.ArgumentParser(description="Valida data/bestiary.json")
    return validar()


if __name__ == "__main__":
    sys.exit(main())