"""AUD-418 — el aviso describía mal lo que pasa, y callaba lo peor.

El defecto
==========
`validate_tmx.py` avisa desde AUD-106 cuando un escenario registra sus tipos
**dentro de una función**, porque esa línea no se ejecuta al importar el
módulo. El texto decía:

    Al jugar funciona, pero el previsualizador y las herramientas que abren el
    mapa suelto **no podrán construir esos objetos**.

Y no es verdad. Medido sobre `stage1_1`, que declara 6 `Walker`, 3 `FlyingBird`
y 2 `ShooterFrog`::

    preview_tmx.py  ->  entidades: 11
    StageLoader     ->  EnemyWalker x6, EnemyFlying x3, EnemyShooter x2

Los construye. **Con otra clase.** `FlyingBird` y `ShooterFrog` también son
especies del bestiario del motor —una factoría que produce un `EnemyFlying` o
un `EnemyShooter` parametrizado—, así que cuando el registro del estudiante no
llega a ejecutarse, el nombre lo resuelve el bestiario y sale un pájaro
genérico en lugar del `CanopyBird` con vuelo senoidal que el estudiante
escribió.

Eso es peor que no construir nada: un hueco se ve; un enemigo que parece el
tuyo y no lo es, no. Es el patrón de AUD-056 —«stage0 cargaba con cinco de sus
enemigos descartados en silencio»— con una vuelta de tuerca, porque aquí ni
siquiera falta nadie.

Lo que faltaba avisar
=====================
La **colisión de nombres**. Medido sobre los once tipos que registran los
escenarios: dos chocan con el bestiario (`FlyingBird` y `ShooterFrog`, los dos
en `stage1_1`) y nueve no. Cuando choca, el comportamiento depende de si una
función llegó a ejecutarse, y eso no se puede diagnosticar mirando el mapa.
"""
from __future__ import annotations

from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parent.parent
STAGE1_1 = _RAIZ / "assets" / "maps" / "stage1_1" / "stage1_1.tmx"


def _avisos(ruta: Path) -> list[str]:
    from scripts import validate_tmx as v

    v.validate_tmx(ruta)
    return list(v._warnings)


class TestElAvisoDiceLaVerdad:
    def test_no_dice_que_no_se_construyen(self) -> None:
        """La frase falsa. Se construyen — con otra clase."""
        diferidos = [a for a in _avisos(STAGE1_1) if "dentro de una función" in a]
        assert diferidos, "stage1_1 registra dentro de funciones; el aviso debe salir"
        assert not any("no podrán construir esos objetos" in a for a in diferidos), (
            "el aviso sigue diciendo que las herramientas no construirán esos "
            "objetos. Medido: las construye, con la clase del bestiario. Un "
            "hueco se ve; un enemigo que parece el tuyo y no lo es, no"
        )

    def test_explica_que_saldra_otra_clase(self) -> None:
        diferidos = [a for a in _avisos(STAGE1_1) if "dentro de una función" in a]
        assert any("bestiario" in a or "otra clase" in a or "genéric" in a
                   for a in diferidos), (
            f"el aviso no explica qué sale en su lugar: {diferidos}"
        )


class TestLaColisionDeNombres:
    def test_avisa_de_los_nombres_que_ya_usa_el_bestiario(self) -> None:
        """`FlyingBird` y `ShooterFrog` existen en el bestiario del motor."""
        choques = [a for a in _avisos(STAGE1_1) if "bestiario" in a]
        assert choques, (
            "stage1_1 registra FlyingBird y ShooterFrog, que el bestiario del "
            "motor ya define, y nada lo dice"
        )

    @pytest.mark.parametrize("nombre", ["FlyingBird", "ShooterFrog"])
    def test_nombra_el_tipo_que_choca(self, nombre: str) -> None:
        assert any(nombre in a for a in _avisos(STAGE1_1) if "bestiario" in a)

    def test_un_mapa_sin_colisiones_no_avisa(self) -> None:
        """`stage1_3_las_aulas` registra a nivel de módulo y con nombres propios.

        Sin este lado, «avisar siempre» pasaría las pruebas de arriba.
        """
        mapa = _RAIZ / "assets" / "maps" / "stage1_3_las_aulas" / "stage1_3_las_aulas.tmx"
        assert not [a for a in _avisos(mapa) if "bestiario" in a]


def test_los_mapas_del_motor_no_chocan_con_su_propio_bestiario() -> None:
    """El cable trampa: los mapas del equipo docente son la referencia.

    Si uno de ellos empieza a registrar un tipo con el nombre de una especie
    del bestiario, el ejemplo que copian los estudiantes pasa a enseñar
    justamente lo que este aviso persigue.
    """
    from scripts import validate_tmx as v

    sucios: dict[str, list[str]] = {}
    for mapa in sorted((_RAIZ / "assets" / "maps").rglob("*.tmx")):
        if mapa.parent.name == "stage1_1":
            continue  # el caso conocido, con su aviso; ver el docstring
        v.validate_tmx(mapa)
        choques = [a for a in v._warnings if "bestiario" in a]
        if choques:
            sucios[mapa.parent.name] = choques
    assert not sucios, f"mapas del motor con colisión de nombres: {sucios}"
