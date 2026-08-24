"""AUD-378 — el guardián de cobertura TMX tenía un punto ciego del 65%.

El defecto
==========
`scripts/check_tmx_coverage.py` existe para responder una pregunta concreta, y
su propio docstring la enuncia: *«una característica que el motor lee del TMX
pero que ningún mapa declara es, en la práctica, una característica que no
existe»*.

Vigilaba **18** propiedades. `StageLoader` lee **35**. Diecisiete quedaban
fuera de su vista, entre ellas `sombras_proyectadas`, `fog_of_war`, `god_rays`,
`water_effect`, `tiempo_bala` y `estamina`. Y aun así el informe terminaba con
«Todas las propiedades de mapa están demostradas en algún mapa».

Por eso nadie supo que **ningún mapa enciende las sombras proyectadas** —
construidas, medidas y probadas desde AUD-278—: el guardián escrito para
decirlo no las estaba mirando.

Por qué se le escapaban
=======================
La prueba que decía contrastar la lista contra el cargador
(`test_student_guidance.py`) comprueba **una sola dirección**: que lo declarado
exista en `StageData`. Nunca que lo que el cargador lee esté declarado. Un
guardián con la comprobación en un solo sentido no puede enterarse jamás de una
propiedad que el motor gane después, que es justo lo que pasó.

Es el patrón de esta fase con una vuelta de tuerca: lo construido-y-no-leído
era **el propio detector de cosas construidas-y-no-leídas**.

Qué fija esta prueba
====================
El sentido que faltaba, y con AST en vez de expresiones regulares — la regex
está descartada por el docstring del propio guion, porque mezclaba propiedades
de mapa con las de objeto. Hoy eso ya no es ambiguo: AUD-350 se llevó los 19
manejadores `_handle_*` a `stage_objetos.py`, así que lo que queda en
`stage_loader.py` es nivel de mapa.
"""
from __future__ import annotations

import ast
import inspect

import pytest

from scripts.check_tmx_coverage import (
    ALIAS_DE_PROPIEDAD,
    PROPIEDADES_DE_OBJETO,
    PROPIEDADES_DEL_MOTOR,
    PROPIEDADES_MAPA,
)


def _leidas_por_el_cargador() -> set[str]:
    """Las propiedades de mapa que `stage_loader.py` lee, por AST.

    Cuatro formas, y las cuatro se usan en el fichero — mirar sólo
    `props.get(...)` se dejaba nueve fuera::

        props.get("X")                     # la común
        tmx_data.properties.get("X")       # los fondos
        cls._parse_unit_prop(props, "X")   # las acotadas a un rango
        "X" in props                       # las que sólo miran si están
    """
    from src.framework.stage import stage_loader

    arbol = ast.parse(inspect.getsource(stage_loader))
    nombres: set[str] = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if (n.func.attr == "get" and n.args
                    and isinstance(n.args[0], ast.Constant)
                    and isinstance(n.args[0].value, str)):
                objetivo = n.func.value
                es_props = (
                    (isinstance(objetivo, ast.Name) and objetivo.id == "props")
                    or (isinstance(objetivo, ast.Attribute)
                        and objetivo.attr == "properties")
                )
                if es_props:
                    nombres.add(n.args[0].value)
            elif n.func.attr == "_parse_unit_prop" and len(n.args) >= 2:
                if isinstance(n.args[1], ast.Constant) and isinstance(
                        n.args[1].value, str):
                    nombres.add(n.args[1].value)
        elif isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(
                n.ops[0], ast.In):
            derecha = n.comparators[0]
            if (isinstance(derecha, ast.Name) and derecha.id == "props"
                    and isinstance(n.left, ast.Constant)
                    and isinstance(n.left.value, str)):
                nombres.add(n.left.value)
    return nombres


def _canonica(nombre: str) -> str:
    return ALIAS_DE_PROPIEDAD.get(nombre, nombre)


class TestElSentidoQueFaltaba:
    def test_todo_lo_que_lee_el_cargador_esta_vigilado(self):
        """La dirección que no existía, y que dejó 17 propiedades a oscuras."""
        leidas = {_canonica(p) for p in _leidas_por_el_cargador()
                  if p not in PROPIEDADES_DE_OBJETO}
        vigiladas = set(PROPIEDADES_DEL_MOTOR)
        sin_vigilar = sorted(leidas - vigiladas)
        assert not sin_vigilar, (
            f"el cargador lee {len(sin_vigilar)} propiedades que el guardián no "
            f"mira, así que nunca dirá si algún mapa las usa: {sin_vigilar}"
        )

    def test_no_se_vigila_lo_que_nadie_lee(self):
        """El otro sentido: una propiedad retirada del motor y no de la lista.

        Sin esto la lista crece y nunca encoge, y el informe acaba pidiendo
        cobertura de características que ya no existen.
        """
        leidas = {_canonica(p) for p in _leidas_por_el_cargador()
                  if p not in PROPIEDADES_DE_OBJETO}
        fantasmas = sorted(set(PROPIEDADES_DEL_MOTOR) - leidas)
        assert not fantasmas, (
            f"el guardián vigila propiedades que el cargador ya no lee: "
            f"{fantasmas}"
        )

    def test_la_lista_de_ensenanza_es_un_subconjunto(self):
        """`PROPIEDADES_MAPA` mide otra cosa, y tiene que seguir siendo real.

        Es la cobertura del mapa de referencia —lo pedagógico, «¿lo enseña
        stage0?»— y no puede pedir una propiedad que el motor no lea.
        """
        sobran = sorted(set(PROPIEDADES_MAPA) - set(PROPIEDADES_DEL_MOTOR))
        assert not sobran, (
            f"la lista de enseñanza pide propiedades que el motor no lee: "
            f"{sobran}"
        )


def test_todas_las_propiedades_las_demuestra_algun_mapa():
    """El cable trampa de GAP-052 — AUD-384.

    Cerrado el punto ciego (AUD-378) resultó que **diecisiete** propiedades no
    las declaraba ningún mapa, entre ellas un modo de juego entero. Se fueron
    cerrando en tres lotes —AUD-380, AUD-383 y AUD-384— hasta cero.

    Esta prueba impide que se vuelva a abrir en silencio, que es como se abrió:
    una propiedad nueva del cargador entra sin que nadie note que ningún mapa
    la enseña, y la característica existe sin que ningún estudiante pueda
    descubrirla. Ahora, añadir una propiedad al motor obliga a decidir —en el
    mismo lote— dónde se demuestra.

    Es deliberadamente estricta y no un porcentaje: el criterio del dueño es
    que el cableado existe *para que los estudiantes lo usen*, y con ese
    criterio «casi todas» no significa nada.
    """
    from pathlib import Path

    from scripts.check_tmx_coverage import analizar

    raiz = Path(__file__).resolve().parent.parent
    cubiertas: set[str] = set()
    for mapa in (raiz / "assets" / "maps").rglob("*.tmx"):
        cubiertas |= analizar(mapa)["del_motor_usadas"]

    sin_demostrar = sorted(set(PROPIEDADES_DEL_MOTOR) - cubiertas)
    assert not sin_demostrar, (
        f"{len(sin_demostrar)} propiedades que el motor lee y ningún mapa "
        f"declara: {sin_demostrar}. Una característica que ningún mapa "
        "demuestra no la descubre ningún estudiante — decide en este mismo "
        "lote en qué mapa se enseña, o documenta por qué no en GAP-052"
    )


class TestLosAlias:
    """`camara`/`camera` y `vista`/`view` son la misma característica.

    Mismo caso que `ALTERNATIVAS` con `BossSpawn` (AUD-366): contarlas por
    separado da una cobertura peor de lo que es y manda a alguien a perseguir
    un hueco que no existe. `stage_loader.py` las lee con un `or` — la
    castellana primero — así que declarar cualquiera de las dos basta.
    """

    @pytest.mark.parametrize("alias,canonica", sorted(ALIAS_DE_PROPIEDAD.items()))
    def test_el_alias_apunta_a_algo_real(self, alias, canonica):
        assert canonica in PROPIEDADES_DEL_MOTOR
        assert alias not in PROPIEDADES_DEL_MOTOR, (
            f"{alias!r} es grafía alternativa de {canonica!r} y no debe contar "
            "como característica aparte"
        )
