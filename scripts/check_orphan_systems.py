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

# AUD-254: imprime `✅`, que no existe en cp1252 —la codificación por defecto
# de la consola de Windows—. Sin esto el guardián de huérfanos muere con
# `UnicodeEncodeError` **a mitad del trabajo**, que es el modo de fallo exacto
# que AUD-177 documentó para `mutation_check.py`.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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
    # ── Uso dentro del propio fichero ────────────────────────────
    "personalizar": (
        "AUD-291: la llama `_paginas_de_texto` en su mismo módulo, al dibujar "
        "cada diálogo. El barrido sólo ve usos desde fuera del fichero"
    ),

    # ── API pública del kit, ofrecida a las escenas de estudiantes ──
    "start_wipe": (
        "AUD-454: es uno de los cuatro modos que `48_SCREEN_TRANSITIONS.md` §3 "
        "declara como API del gestor de transiciones, junto a `start_slide` y "
        "`start_circle`. Ninguna pantalla del juego base lo usa —todas hacen "
        "fundido— y eso no lo convierte en código muerto: el kit existe para "
        "que una escena de estudiante elija su transición, igual que elige su "
        "paleta. Quien lo adopte será el primero, y por eso hay pruebas que lo "
        "ejercitan. Si algún día se decide que el juego base debe usarlo, la "
        "decisión es de diseño y no de limpieza"
    ),

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

    # ── Paginación del diálogo (AUD-269) ──
    #
    # `confirmar()` la llama el propio `update()` cuando el jugador pulsa, y es
    # pública porque la escena y las pruebas necesitan **el mismo camino** que
    # la tecla: tener dos formas de avanzar un diálogo es cómo se acaba con una
    # que pagina y otra que no. `paginas` y `pagina_actual` las lee el dibujado
    # para el indicador `[ENTER] 1/3`, y son propiedades para que un guionista
    # pueda comprobar desde una prueba que su texto cabe donde cree.
    "confirmar": "la llama update() al pulsar; pública para que escena y pruebas usen el mismo camino",
    "paginas": "la lee el indicador del propio cuadro; pública para poder medir un guion desde una prueba",
    "pagina_actual": "ídem",

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
    # Éstos cuatro no lo estaban: los llamaba nadie y al lado había una copia
    # de su lógica. AUD-245 los conectó haciendo que el duplicado delegue.
    "ajustar_bus": "lo llaman `set_music_volume` y `set_sfx_volume`, que antes lo reimplementaban",
    "get_entry": "lo llama `_asegurar`, que hacía la misma consulta a mano",
    "get_frame": "lo llama `posicion_en`, que indexaba la lista de fotogramas a mano",
    "get_splits": "lo llama `save`, que volcaba la lista viva en vez de una copia",

    # ── API publicada a los autores de escenarios (AUD-245) ──
    #
    # Punto ciego estructural del barrido, no de estos símbolos: `src/stages/`
    # queda fuera de ORIGENES y de CONSUMIDORES por la invariante 1 de
    # CLAUDE.md, así que **toda API que el motor publica para que la use un
    # escenario aparecerá siempre como huérfana**. El motor no la llama porque
    # no le toca llamarla.
    #
    # El criterio para entrar aquí es verificable y estrecho: que un documento
    # de la especificación la publique en su tabla de API. No vale «alguien
    # podría usarla».
    "reveal_all": "docs/46 §API la publica para que un escenario revele zonas en lote",
    "play_voz": "GAP-031 resuelto (AUD-263): llamante en boss_venado.py:732; src/stages/ fuera del barrido",

    # AUD-366 — los tres de logros, mirados uno a uno.
    "AchievementDef": (
        "AUD-366: es el tipo de dato del propio módulo — lo construye "
        "`_cargar_definiciones`, lo anota `_defs` y lo devuelve `achievements()`. "
        "El barrido lo ve suelto por su regla de cohesión, no por estar suelto"
    ),
    "AchievementProgress": "AUD-366: ídem; lo construye `register` y lo valida `load`",
    "init_instance": (
        "AUD-366: seam de pruebas a propósito (test_guia_del_motor.py:74). No "
        "debe tener llamante de producción: cambiar de estudiante se resuelve "
        "con `load()`, que reinicia sobre la MISMA instancia (AUD-200)"
    ),

    # AUD-364 — el triaje de la sección «sólo los re-exporta su paquete», hecho
    # una vez para que la sección quede como lo que es: un cable trampa. Cada
    # línea dice por qué NO es un defecto; si alguna deja de ser cierta, se
    # borra y el símbolo vuelve a salir.
    #
    # Los estados del jugador: cada uno lo instancia un módulo hermano dentro
    # de su propio fichero (`grounded.py:68`, `wall.py:30`, `airborne.py:211`,
    # `ability.py`), que el detector ignora por su regla de cohesión. Son
    # estados vivos que el jugador alcanza jugando.
    "WalkingState": "AUD-364: la instancia grounded.py en su propio fichero",
    "SlideState": "AUD-364: ídem, grounded.py",
    "CrouchingState": "AUD-364: ídem, grounded.py",
    "AirborneState": "AUD-364: ídem, airborne.py",
    "AirChaseState": "AUD-364: ídem, airborne.py",
    "AerialSlamState": "AUD-364: ídem, airborne.py:211",
    "LedgeGrabState": "AUD-364: ídem, wall.py:31",
    "ThrowState": "AUD-364: ídem, ability.py",
    "ChargeReleaseState": "AUD-364: ídem, ability.py",
    "Contacto": (
        "AUD-364: es el tipo de retorno de los cinco pasos de resolucion.py, "
        "citado en cada firma del módulo"
    ),
    "unidad_de_escena": "AUD-364: lo consume la sesión académica por nombre de escena",
    "siguiente_unidad": "AUD-364: ídem",
    # `resolver_movimiento` sí estaba sin llamantes de producción, y ése fue
    # AUD-355. Se conserva como **fachada de composición** —la que docs/87 §27
    # fase 2 documenta para entidades y modos nuevos— y ya no es peligrosa: la
    # verja de datos hostiles vive en `_verja`, compartida por los cinco pasos,
    # así que la fachada no puede divergir de lo que usa el jugador.
    "resolver_movimiento": (
        "AUD-355/364: fachada de composición documentada (docs/87 §27 fase 2); "
        "la verja compartida vive en _verja, no aquí, así que no puede divergir"
    ),
}

#: Huérfanos **reales**, verificados y ya anotados donde toca. Están aquí para
#: que `--ci` no vuelva a gritar por ellos, no para darlos por buenos: cada uno
#: lleva el GAP que lo sigue. La diferencia con `VERIFICADOS` importa —aquéllos
#: no son defectos; éstos sí, y esperan una decisión de diseño.
PENDIENTES: dict[str, str] = {
    # AUD-366 — vacío, y eso es un resultado. Los tres símbolos que vivían aquí
    # desde AUD-233 (`AchievementDef`, `AchievementProgress`, `init_instance`)
    # se miraron uno a uno y ninguno era la pregunta que parecía; el detalle,
    # con su motivo, está arriba en VERIFICADOS.
    #
    # Que esté vacío NO significa que no quede deuda: significa que no queda
    # deuda **de esta clase**. Un huérfano nuevo aparece aquí en cuanto alguien
    # escriba un subsistema y se olvide de enchufarlo, que es exactamente para
    # lo que se escribió este guardián.
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


def solo_reexportados() -> dict[str, Path]:
    """Símbolos cuyo único consumidor de producción es un `__init__.py`.

    AUD-364 — el punto ciego que dejó pasar AUD-355, cerrado con una regla
    **estrecha**. La verja de datos hostiles de AUD-344 se escribió dentro de
    `resolver_movimiento`, que no llama ninguna entidad del juego; el detector
    la dio por conectada porque `framework/physics/__init__.py` la re-exporta,
    y una re-exportación no es un consumidor: es una puerta.

    Por qué esta regla y no la evidente, con la medición delante
    ------------------------------------------------------------
    Se probaron las dos alternativas anchas antes de escribir ésta, y las dos
    salen peor que no hacer nada:

    * **«no contar los `__init__.py` como consumidores»** → 212 huérfanos pasan
      a 224, y **once de los doce nuevos son falsos positivos**: `WalkingState`,
      `LedgeGrabState` y compañía son estados vivos que sus módulos hermanos
      instancian, sólo que dentro del mismo fichero.
    * **«un import no es un uso»** → 212 pasan a 268, y **cincuenta y seis de
      los cincuenta y seis nuevos son falsos**: `Events`, `Action`,
      `PhysicsProfile` o `VisionTools` se usan por **atributo**
      (`Events.SFX_PLAYER_JUMP`), no por llamada, así que la regla los da por
      muertos. Distinguir uso de mención de verdad exige resolver ámbitos, o
      sea reescribir el analizador, no parchear una condición.

    Un guardián ruidoso se desactiva —el razonamiento de AUD-106 aplicado a
    otro sitio—, así que esto no entra en `--ci` ni en el recuento de
    huérfanos: es una sección **informativa** de doce entradas que un humano
    tría una vez. Doce preguntas al año son manejables; cincuenta y seis
    respuestas equivocadas, no.
    """
    defs = definiciones()
    en_juego = referencias(CONSUMIDORES)
    resultado: dict[str, Path] = {}
    for nombre, origen in defs.items():
        fuera = {f for f in en_juego.get(nombre, set()) if f != origen}
        if not fuera:
            continue          # ya sale como huérfano por la vía normal
        if all(f.name == "__init__.py" for f in fuera):
            resultado[nombre] = origen
    return resultado


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

    # AUD-364 — informativa, nunca bloqueante. Ver `solo_reexportados`.
    puerta = {n: r for n, r in solo_reexportados().items()
              if n not in VERIFICADOS and n not in PENDIENTES}
    print("\n=== Sólo los re-exporta su paquete ===")
    print("    (nadie más los toca en producción: mira si tienen llamante\n"
          "     de verdad o si son una puerta a un cuarto vacío — AUD-355)\n")
    for nombre, ruta in sorted(puerta.items(), key=lambda kv: (str(kv[1]), kv[0])):
        print(f"  {ruta.relative_to(RAIZ).as_posix():52s} {nombre}")
    if not puerta:
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
