#!/usr/bin/env python3
"""Busca subsistemas terminados que el juego no invoca.

Por qué existe (AUD-233)
========================
Este repositorio tiene un modo de fallo propio, y se ha repetido lo bastante
como para merecer un guardián: **un subsistema se escribe entero, se prueba, se
documenta como entregado, y nadie lo llama desde el juego**. No falla ninguna
prueba —las suyas pasan, en aislamiento— y ninguna revisión de código lo ve,
porque el fichero que falta no está en el diff.

La lista de los que ya ocurrieron:

* `SoundBank` sin una sola llamada a `play_sfx` (GAP-003);
* el sistema de diálogo, completo y dibujado, que no se abría nunca porque
  `MessageTrigger` no tenía el campo que se le consultaba (AUD-127);
* `crossfade_ambient` y `set_ambient_volume`, escritas meses antes de que algo
  las usara (AUD-149);
* `check_player_contact` en cuatro enemigos: las flechas y los orbes no hacían
  daño (AUD-149);
* `SpeedrunTimer.save()`, que nadie llamaba, con una pantalla de récords que
  rellenaba el hueco con **tiempos inventados** (AUD-202);
* `BossRushMode`, construido y abandonado, con la especificación declarándolo
  «✅ Complete — scoring, health carry-over» (AUD-232).

La firma es siempre la misma: **lo ejercitan las pruebas y no lo toca el
juego**. Eso es lo que este script mide.

Qué NO es este script
---------------------
No es un detector de código muerto y su salida **no son defectos**: son
preguntas. `docs/63` lo aprendió por las malas —de doce filas de un barrido
anterior, tres eran falsos positivos y una recomendación de borrado habría
roto el vuelo de medio bestiario—. Cada nombre que sale aquí hay que ir a
verificarlo al código antes de tocar nada.

Por eso `--ci` no falla por la lista entera. Falla por lo que **aparece de
nuevo** en un módulo que algún documento declara terminado, y sólo si no está
en ninguna de las dos listas del final:

* `VERIFICADOS` — se miró y **no es un defecto** (alias por propiedad, gancho
  del estudiante, API de depuración, uso dentro del propio fichero);
* `PENDIENTES` — se miró y **sí lo es**, pero ya está anotado con su GAP.

Lo que no esté en ninguna es algo que nadie ha mirado todavía, y ésa es la
única situación que este guardián considera inaceptable.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

#: Dónde se definen los símbolos que nos interesan. `src/stages/stage0` entra
#: porque es material del motor —el escenario de referencia que los estudiantes
#: copian—; el resto de `src/stages/` es entrega de estudiante y queda fuera
#: (CLAUDE.md §3, invariante 1).
ORIGENES = (
    RAIZ / "src" / "engine",
    RAIZ / "src" / "framework",
)

#: Todo lo que se ejecuta cuando alguien juega o califica. Si un símbolo se usa
#: aquí, está conectado.
CONSUMIDORES = (
    RAIZ / "src",
    RAIZ / "scripts",
    RAIZ / "tools",
    RAIZ,  # los puntos de entrada del juego viven en la raíz
)

OMITIR = {"__pycache__", ".venv", "revisar", "student_templates"}

#: Ganchos que el motor invoca por polimorfismo. Verlos «sin llamar» no dice
#: nada: quien los llama lo hace sobre la clase base, no sobre la derivada.
GANCHOS = frozenset({
    "update", "draw", "awake", "start", "destroy", "on_enter", "on_exit",
    "on_pause", "on_resume", "process_events", "handle_event", "render",
    "reset", "enter", "exit", "to_dict", "from_dict", "setup", "tick",
    "apply", "close", "run", "clear", "main", "load", "save",
})

#: Huérfanos ya verificados a mano, con el motivo. Estar aquí **no** significa
#: «da igual»: significa «alguien abrió el fichero y decidió». Quitar una
#: entrada de aquí es reabrir la pregunta.
#:
#: Formato: nombre -> por qué no es un defecto.
VERIFICADOS: dict[str, str] = {
    # ── Alias por propiedad: el juego los llama por el atributo ──
    "set_music_volume": "lo invoca el setter de la propiedad `music_volume`, desde app.py",
    "set_sfx_volume": "lo invoca el setter de la propiedad `sfx_volume`, desde app.py",

    # ── API de depuración, de uso en pruebas por diseño (GAP-013) ──
    "subscriber_count": "introspección del EventBus para depurar; GAP-013 la pidió así",
    "subscribers_snapshot": "ídem",

    # ── Ganchos que rellena el estudiante ──
    "on_stage_start": "gancho de la plantilla de estudiante; vacío a propósito",
    "on_player_landed": "ídem",
    "on_enemy_died": "ídem",
    "on_next_trigger_entered": "ídem",
    "sincronizar_salud": "hueco de compatibilidad desde F5.12: alguna entrega lo llama",

    # ── Ayudantes extraídos para poder medirlos (AUD-187) ──
    "alto_de_fila": "extraído para que la prueba de legibilidad mida la métrica real",
    "alto_de_ficha": "ídem",
    "esta_centrado": "ídem, para la prueba de centrado de las demos",

    # ── Verificados en AUD-233: se usan dentro de su propio fichero ──
    #
    # El barrido descuenta el uso en el módulo que define el símbolo, a
    # propósito: cohesión no es conexión, y sin ese descuento cualquier función
    # auxiliar saldría «conectada» por llamarse a sí misma desde dos líneas más
    # abajo. El precio es que un símbolo público **usado sólo por su propio
    # módulo** aparece aquí, y hay que ir a mirarlo. Éstos ya se miraron:
    "stop_ambient": "lo llama `play_ambient` en audio_manager.py:172 al cambiar de ambiente",
    "set_ambient_volume": "lo llama `ajustar_bus` en el mismo fichero (fijado por AUD-149)",
    "dividir_en_lineas": "lo usa el propio dialogue_system.py:384 al dibujar el cuadro",
    "record": "lo llama `GhostData.grabar` en speedrun_mode.py:197",
    "escenarios_de_jefe": "lo llama `empezar_boss_rush` en el mismo fichero",
    "mejores_tiempos": "lo llama `LeaderboardScene.on_enter` en el mismo fichero",
}

#: Huérfanos **reales**, verificados y ya anotados donde toca. Están aquí para
#: que `--ci` no vuelva a gritar por ellos, no para darlos por buenos: cada uno
#: lleva el GAP que lo sigue. La diferencia con `VERIFICADOS` importa —aquéllos
#: no son defectos; éstos sí, y esperan una decisión de diseño.
PENDIENTES: dict[str, str] = {
    "desde_datos": "GAP-031: constructor de árbol de diálogo desde JSON, sin cargador ni contenido",
    "get_frame": "GAP-031: accesor de fotograma del fantasma; lo sustituyó `posicion_en`",
    "get_splits": "GAP-031: nadie consulta los parciales; la tabla lee el fichero",
    "reveal_all": "GAP-031: alta por lotes de la niebla; ningún escenario la usa",
    "set_params": "GAP-031: los cinco parámetros del agua no se pueden fijar desde el mapa",
    "get_entry": "GAP-031: accesor del bestiario; la pantalla itera el catálogo",
    "ajustar_bus": "GAP-031: el bus de ambiente no tiene control en Opciones",
    "play_voz": "GAP-031: bus de voz sin contenido de voz",
    # `achievements.py` lo está reescribiendo otra sesión (logros por
    # estudiante). No se juzga aquí: se mirará cuando aquello asiente.
    "AchievementDef": "en obras: logros por estudiante, sesión paralela",
    "AchievementProgress": "en obras, ídem",
    "init_instance": "en obras, ídem",
}


def _ficheros(bases) -> list[Path]:
    vistos: list[Path] = []
    for base in bases:
        if not base.exists():
            continue
        # La raíz se mira sin recorrer: sus subdirectorios ya van por su cuenta,
        # y recorrerla entera arrastraría `.venv` y las entregas de `revisar/`.
        candidatos = base.glob("*.py") if base == RAIZ else base.rglob("*.py")
        for p in sorted(candidatos):
            partes = set(p.relative_to(RAIZ).parts)
            if partes & OMITIR:
                continue
            # `src/stages/` fuera, salvo stage0.
            rel = p.relative_to(RAIZ).as_posix()
            if rel.startswith("src/stages/") and not rel.startswith("src/stages/stage0/"):
                continue
            if p.resolve() == _YO_MISMO:
                continue
            vistos.append(p)
    return vistos


#: Este mismo fichero queda fuera del barrido de referencias.
#:
#: AUD-233 — sin esto el guardián se exoneraba solo. El escáner cuenta las
#: cadenas literales a propósito (el registro de escenas construye por nombre),
#: y `VERIFICADOS` es un diccionario lleno de nombres en cadenas. Resultado
#: medido: añadir `stop_ambient` a la lista de verificados lo sacaba del informe
#: **por considerarlo conectado**, no por estar verificado. Y peor: los nombres
#: citados en la cabecera como ejemplos históricos —`play_sfx`,
#: `check_player_contact`— exoneraban a los símbolos reales del motor.
#:
#: Un guardián que aprueba porque se menciona a sí mismo no vale nada, y este
#: era del tipo que además lo hace en silencio.
_YO_MISMO = Path(__file__).resolve()


def _arbol(ruta: Path) -> ast.AST | None:
    try:
        return ast.parse(ruta.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return None


def definiciones() -> dict[str, Path]:
    """Nombre público -> el fichero que lo define, si sólo lo define uno.

    Los definidos en varios sitios se descartan: son sobrescrituras de una
    jerarquía, y ahí «quién llama a cuál» no se decide por el nombre.

    **Punto ciego conocido, y es de verdad ciego.** La regla también descarta
    funciones homónimas e independientes en módulos distintos —hay dos
    `y_de_la_descripcion`, una en `achievement_scene` y otra en
    `bestiary_scene`—, así que un huérfano con nombre repetido no sale en el
    informe. Se acepta a cambio de no inundarlo de jerarquías de clases; queda
    escrito para que nadie lea la salida como exhaustiva.
    """
    encontrados: dict[str, set[Path]] = defaultdict(set)
    for ruta in _ficheros(ORIGENES):
        arbol = _arbol(ruta)
        if arbol is None:
            continue
        for nodo in ast.walk(arbol):
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if nodo.name.startswith("_") or nodo.name in GANCHOS:
                    continue
                encontrados[nodo.name].add(ruta)
    return {n: next(iter(f)) for n, f in encontrados.items() if len(f) == 1}


def referencias(bases) -> dict[str, set[Path]]:
    """Nombre -> ficheros donde aparece usado.

    Se cuentan también las **cadenas literales**: el registro de escenas
    construye por nombre (`reg.register("leaderboard", …)`), y sin esto media
    docena de escenas legítimas saldrían como huérfanas.
    """
    refs: dict[str, set[Path]] = defaultdict(set)
    for ruta in _ficheros(bases):
        arbol = _arbol(ruta)
        if arbol is None:
            continue
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Name):
                refs[nodo.id].add(ruta)
            elif isinstance(nodo, ast.Attribute):
                refs[nodo.attr].add(ruta)
            elif isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
                refs[nodo.value].add(ruta)
    return refs


def huerfanos() -> dict[str, Path]:
    """Lo que las pruebas ejercitan y el juego no llama."""
    defs = definiciones()
    en_juego = referencias(CONSUMIDORES)
    en_pruebas = referencias((RAIZ / "tests",))

    resultado: dict[str, Path] = {}
    for nombre, origen in defs.items():
        # Usarse dentro del propio fichero no cuenta: eso es cohesión, no
        # conexión. Lo que se busca es si alguien de FUERA lo necesita.
        if {f for f in en_juego.get(nombre, set()) if f != origen}:
            continue
        if not en_pruebas.get(nombre):
            continue
        resultado[nombre] = origen
    return resultado


def modulos_declarados_completos() -> dict[str, set[str]]:
    """Módulo de `src/` -> documentos que lo citan declarándose terminado.

    Un huérfano cualquiera es una pregunta. Un huérfano **en un módulo que un
    documento oficial da por entregado** es una contradicción entre las dos
    fuentes de verdad, y ésa es la que este script vigila: el daño de AUD-202 y
    AUD-232 no fue el hueco, fue que `docs/43` y `docs/44` afirmaban que no lo
    había.
    """
    declarados: dict[str, set[str]] = defaultdict(set)
    docs = RAIZ / "docs"
    if not docs.exists():
        return declarados
    for doc in sorted(docs.glob("*.md")):
        texto = doc.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"(?:Status|Estado)\W{0,40}(?:✅|Complete|Completo)",
                         texto, re.I):
            continue
        for m in re.finditer(r"`?(src/[\w/]+\.py)`?", texto):
            declarados[m.group(1)].add(doc.name)
    return declarados


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ci", action="store_true",
                    help="salir con error si un módulo declarado completo "
                         "tiene símbolos sin invocar y sin verificar")
    ap.add_argument("--todos", action="store_true",
                    help="listar también los huérfanos de módulos que ningún "
                         "documento declara terminados (informativo)")
    args = ap.parse_args()

    encontrados = huerfanos()
    declarados = modulos_declarados_completos()

    contradicciones: dict[Path, list[str]] = defaultdict(list)
    resto: dict[Path, list[str]] = defaultdict(list)
    for nombre, ruta in encontrados.items():
        if nombre in VERIFICADOS or nombre in PENDIENTES:
            continue
        destino = (contradicciones
                   if ruta.relative_to(RAIZ).as_posix() in declarados
                   else resto)
        destino[ruta].append(nombre)

    print(f"Símbolos que las pruebas ejercitan y el juego no invoca: "
          f"{len(encontrados)}")
    print(f"  verificados, no son defectos: "
          f"{sum(1 for n in encontrados if n in VERIFICADOS)}")
    print(f"  huérfanos reales ya anotados: "
          f"{sum(1 for n in encontrados if n in PENDIENTES)}")
    print()
    print("=== En módulos que un documento declara TERMINADOS ===")
    print("    (la documentación afirma lo que el código no hace)\n")
    for ruta in sorted(contradicciones, key=lambda p: str(p)):
        rel = ruta.relative_to(RAIZ).as_posix()
        print(f"  {rel}")
        print(f"      sin invocar : {', '.join(sorted(contradicciones[ruta]))}")
        print(f"      lo declara  : {', '.join(sorted(declarados[rel]))}")
    if not contradicciones:
        print("  (ninguno)")

    if args.todos:
        print(f"\n=== Sin declaración de entrega: {sum(len(v) for v in resto.values())} "
              f"símbolos en {len(resto)} módulos ===")
        for ruta in sorted(resto, key=lambda p: str(p)):
            print(f"  {ruta.relative_to(RAIZ).as_posix()}: "
                  f"{', '.join(sorted(resto[ruta]))}")

    if args.ci and contradicciones:
        print(
            "\nHay módulos documentados como entregados cuyos símbolos no "
            "invoca nadie.\n"
            "Esto NO es una lista de defectos: es una lista de preguntas. Abre\n"
            "cada fichero y decide cuál de las tres cosas es:\n"
            "  1. falso positivo    -> añádelo a VERIFICADOS con el motivo;\n"
            "  2. correcto sin usar -> ídem (gancho de estudiante, API de depuración);\n"
            "  3. de verdad suelto  -> conéctalo, o deja de documentarlo como\n"
            "                          entregado y anótalo en KNOWN_GAPS.\n"
            "La opción que no existe es dejarlo como está y que la documentación\n"
            "siga diciendo que funciona.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
