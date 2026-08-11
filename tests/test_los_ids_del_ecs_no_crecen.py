"""AUD-394 — GAP-041 decía que los ids del ECS crecen sin techo. Medido: no.

Lo que decía el hueco
=====================
    `crear()` incrementa un contador monótono y `aplicar_bajas()` no devuelve
    el id al saco, así que un escenario que cree y destruya mucho —balas,
    partículas— hace crecer el espacio de ids sin techo.

Y su plan: *«reciclar ids es media hora y no rompe nada»*. Pero `world.py:70`
dice lo contrario, y lo dice como decisión deliberada:

    Un identificador **nunca se reutiliza**. Reciclarlos ahorra memoria y
    produce el peor error de esta arquitectura: un sistema guarda el id 7, el
    7 muere, nace otro 7 distinto y el sistema opera sobre el nuevo creyendo
    que es el viejo.

Uno de los dos estaba mal. Medido, el equivocado era el hueco, y por tres
motivos independientes —basta uno—:

1. **Las balas no entran en el mundo de la escena.** `adoptar_en` es lo único
   que mete una `BaseEntity` en él, y se llama desde exactamente dos sitios,
   los dos dentro de `_poblar_mundo_ecs`, al montar. Ninguno en tiempo de
   ejecución. Un `Projectile` nace en el mundo **privado** que `BaseEntity`
   se construye para sí (`bridge.py:66`), donde su id es siempre 1.
2. **El contador se reinicia en cada montaje.** `_poblar_mundo_ecs` hace
   `self._mundo = World()`, así que ni siquiera acumula entre respawns.
3. **El consumo por montaje es diminuto.** Medido sobre los 17 mapas: 37 ids
   en el peor (`stage_mecanicas`), 1 en el más vacío.

Con 37 ids por montaje, agotar los enteros pequeños de CPython exigiría del
orden de 29 millones de cargas de escenario. El hueco describe un problema que
esta arquitectura no puede tener.

Qué fija esta prueba
====================
No se toca `world.py`: la decisión de no reciclar se queda, y ahora tiene la
medición que la respalda en vez de sólo el argumento. Lo que se fija son las
**tres condiciones que la sostienen**, porque las tres se pueden romper sin
querer — sobre todo la primera: el día que alguien quiera que el viento empuje
a los proyectiles, `adoptar_en` en runtime es la forma obvia de conseguirlo, y
ahí sí empezaría el crecimiento que el hueco describe. Que salte una prueba es
más barato que volver a medir esto dentro de seis meses.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pygame
import pytest

from src.framework.ecs.world import World

_RAIZ = Path(__file__).resolve().parent.parent

#: Cota con holgura. El peor mapa medido consume 37; esto salta si un mapa
#: nuevo se va a un orden de magnitud distinto, no por añadir un enemigo.
TECHO_DE_IDS_POR_MONTAJE = 200


def _init_pygame_display() -> None:
    if not pygame.display.get_init():
        pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))


class TestElContadorNoAcumula:
    def test_un_mundo_nuevo_empieza_por_uno(self) -> None:
        """La base de todo: el contador es del `World`, no global."""
        primero = World()
        for _ in range(500):
            primero.crear()
        assert World().crear() == 1, (
            "el contador de ids se comparte entre mundos; si fuera así, sí "
            "crecería sin techo a lo largo de una partida"
        )

    def test_montar_la_escena_construye_un_mundo_nuevo(self) -> None:
        """Por AST: `_poblar_mundo_ecs` asigna un `World()` recién hecho.

        Si un día se reutilizara el mundo entre montajes —por ahorrarse la
        reconstrucción en el respawn, que es la optimización tentadora— el
        contador pasaría a acumular a lo largo de la partida y el punto 2 de
        esta prueba dejaría de ser cierto.
        """
        from src.framework.scenes.stage_parts import mundo_ecs

        arbol = ast.parse(inspect.getsource(mundo_ecs))
        funciones = [n for n in ast.walk(arbol)
                     if isinstance(n, ast.FunctionDef)
                     and n.name == "_poblar_mundo_ecs"]
        assert funciones, "no existe `_poblar_mundo_ecs`"

        construye = [
            n for n in ast.walk(funciones[0])
            if isinstance(n, ast.Assign)
            and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name)
            and n.value.func.id == "World"
        ]
        assert construye, (
            "`_poblar_mundo_ecs` ya no construye un `World` nuevo: el contador "
            "de ids pasa a acumular entre montajes y respawns"
        )


def test_nadie_adopta_entidades_fuera_del_montaje() -> None:
    """El cable trampa que de verdad importa.

    `adoptar_en` es la única puerta al mundo de la escena. Mientras sólo se
    llame al montar, ninguna entidad creada en tiempo de ejecución —balas,
    orbes, partículas— consume un id de ese mundo, que es justo lo que el
    hueco daba por hecho que pasaba.

    Se comprueba por AST y sobre todo `src/`, no por texto: `adoptar_en` es un
    nombre suficientemente raro como para que un `grep` valga, pero lo que hay
    que contar son **llamadas**, y una mención en un docstring no lo es.
    """
    permitidos = {"mundo_ecs.py"}
    infractores: list[str] = []

    for fichero in (_RAIZ / "src").rglob("*.py"):
        if "__pycache__" in fichero.parts:
            continue
        try:
            arbol = ast.parse(fichero.read_text(encoding="utf-8-sig"))
        except (OSError, SyntaxError):
            continue
        for nodo in ast.walk(arbol):
            if (isinstance(nodo, ast.Call)
                    and isinstance(nodo.func, ast.Attribute)
                    and nodo.func.attr == "adoptar_en"
                    and fichero.name not in permitidos):
                infractores.append(f"{fichero.relative_to(_RAIZ)}:{nodo.lineno}")

    assert not infractores, (
        "hay llamadas a `adoptar_en` fuera del montaje de la escena: "
        f"{infractores}. Si se adoptan entidades en tiempo de ejecución, el "
        "mundo de la escena empieza a consumir un id por cada bala y GAP-041 "
        "pasa a ser cierto — hay que volver a medirlo antes de seguir"
    )


@pytest.mark.parametrize(
    "mapa",
    sorted((_RAIZ / "assets" / "maps").rglob("*.tmx")),
    ids=lambda p: p.parent.name,
)
def test_ningun_mapa_consume_demasiados_ids_al_montar(mapa: Path) -> None:
    """La cota medida, mapa a mapa. El peor hoy es `stage_mecanicas` con 37."""
    _init_pygame_display()
    from src.framework.entities import entity_factory
    from src.framework.stage.stage_loader import StageLoader

    entity_factory.ensure_registered()
    datos = StageLoader.load(mapa)
    # Lo que `_poblar_mundo_ecs` mete en el mundo: un grupo de componentes por
    # mecánica del TMX, una entidad por enemigo, y el jugador.
    consumidos = (len(getattr(datos, "componentes", []) or [])
                  + len(getattr(datos, "entity_list", []) or [])
                  + 1)
    assert consumidos <= TECHO_DE_IDS_POR_MONTAJE, (
        f"{mapa.parent.name} consume {consumidos} ids al montar. No es un "
        "fallo por sí solo, pero la medición que cerró GAP-041 daba 37 como "
        "peor caso: si esto se dispara, hay que rehacer aquella cuenta"
    )
