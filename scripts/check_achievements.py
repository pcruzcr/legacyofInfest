"""
check_achievements.py — valida `data/achievements.json`.

Por qué (AUD-197)
-----------------
Las definiciones de logros vivían escritas a mano en `achievements.py`: un
`target` en cero, una descripción truncada por un tipeño o un id duplicado se
notaban sólo cuando un estudiante preguntaba por qué faltaba un logro. Ahora
las definiciones son un fichero de datos, y este script es lo que las vacuna
*antes* de que lleguen a la pantalla.

Comprueba que el fichero sea JSON válido, que cada entrada tenga los campos
obligatorios, que los ids sean únicos, que los objetivos sean positivos y que
estén presentes todos los logros que el motor referencia por id.

Uso:
    python scripts/check_achievements.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
_FICHERO = _RAIZ / "data" / "achievements.json"

#: Logros que src/engine/core/achievements.py referencia por id en las
#: llamadas a `progress` y a los `mark_*`. Si uno falta en el catálogo, el
#: logro existe para el jugador pero no se puede desbloquear nunca.
REQUERIDOS = {
    "first_blood", "exterminator", "untouchable", "parry_master",
    "air_assault", "speed_demon", "collector", "survivor",
    "combo_king", "explorer",
}

CAMPOS_TEXTO = ("id", "name", "description")


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

    entradas = datos.get("achievements", []) if isinstance(datos, dict) else None
    if not isinstance(entradas, list):
        print("[ERROR] «achievements» no es una lista")
        problemas += 1
        entradas = []
    if not entradas:
        print("[ERROR] el catálogo de logros está vacío")
        problemas += 1

    for i, entrada in enumerate(entradas):
        if not isinstance(entrada, dict):
            print(f"[ERROR] la entrada {i} no es un objeto")
            problemas += 1
            continue
        etiqueta = entrada.get("id", f"#{i}")
        for campo in CAMPOS_TEXTO:
            valor = entrada.get(campo)
            if not isinstance(valor, str) or not valor.strip():
                print(f"[ERROR] «{etiqueta}» sin «{campo}» no vacío")
                problemas += 1
        objetivo = entrada.get("target", 1)
        if not isinstance(objetivo, int) or objetivo < 1:
            print(f"[ERROR] «{etiqueta}» con «target» no positivo")
            problemas += 1
        oculto = entrada.get("hidden", False)
        if not isinstance(oculto, bool):
            print(f"[ERROR] «{etiqueta}» con «hidden» que no es booleano")
            problemas += 1

    ids = [e.get("id") for e in entradas if isinstance(e, dict)]
    duplicados = {i for i in ids if ids.count(i) > 1}
    if duplicados:
        print(f"[ERROR] ids duplicados: {sorted(duplicados)}")
        problemas += 1
    faltan = sorted(REQUERIDOS - set(ids))
    if faltan:
        print(f"[ERROR] el motor referencia logros ausentes del catálogo: {faltan}")
        problemas += 1

    ocultas = sum(1 for e in entradas if isinstance(e, dict) and e.get("hidden"))
    print(f"{len(entradas)} logros definidos, {ocultas} secretos.")
    if problemas:
        print(f"{problemas} problema(s) en {_FICHERO.name}")
        return 1
    print("Catálogo de logros en orden.")
    return 0


def main() -> int:
    argparse.ArgumentParser(description="Valida data/achievements.json")
    return validar()


if __name__ == "__main__":
    sys.exit(main())