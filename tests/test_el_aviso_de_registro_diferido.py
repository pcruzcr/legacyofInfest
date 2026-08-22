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

Epílogo (AUD-591)
=================
`stage1_1` registraba dentro de `__init__` y era el único caso activo de todo
el repositorio. AUD-591 movió su registro a nivel de módulo —lo que el propio
aviso ordena— y de paso retiró dos registros huérfanos ("Skitter"/"Bat") que
quedaron en sus pruebas cuando el TMX cambió de tipos. Hoy ningún mapa del
motor dispara este aviso; la clase de abajo lo ejercita con un paquete
sintético para que el texto siga cubierto, y la última clase vigila que
`stage1_1` no recaiga.
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


# ──────────────────────────────────────────────────────────────────────
# El paquete sintético: un escenario que registra en los dos sitios.
#
# `_tipos_registrados_por_el_estudiante` deriva el paquete del nombre del
# directorio del mapa (`assets/maps/<nombre>/` ↔ `src/stages/<nombre>/`) y
# resuelve rutas contra `_PROJECT_ROOT`, así que basta con montar ese árbol
# en tmp_path y apuntar la constante del módulo allí. No se ejecuta código
# ajeno: el escaneo es puro AST.
# ──────────────────────────────────────────────────────────────────────
_ENTIDAD_TARDIA = '''\
from src.framework.stage.stage_loader import StageLoader


class RataDeLaboratorio:
    pass


class RataTemprana:
    pass


StageLoader.register_entity("RataTemprana", RataTemprana)


def registrar_tarde() -> None:
    StageLoader.register_entity("RataTardia", RataDeLaboratorio)
'''


@pytest.fixture
def escenario_tardio(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from scripts import validate_tmx as v

    paquete = tmp_path / "src" / "stages" / "demo_tardio"
    paquete.mkdir(parents=True)
    (paquete / "entidad.py").write_text(_ENTIDAD_TARDIA, encoding="utf-8")
    mapa = tmp_path / "assets" / "maps" / "demo_tardio"
    mapa.mkdir(parents=True)
    tmx = mapa / "demo_tardio.tmx"
    tmx.write_text("<map/>", encoding="utf-8")
    monkeypatch.setattr(v, "_PROJECT_ROOT", tmp_path)
    return tmx


def _avisos_del_escenario_sintetico(tmx: Path) -> list[str]:
    from scripts import validate_tmx as v

    v._tipos_registrados_por_el_estudiante(tmx)
    return list(v._warnings)


class TestElAvisoDiceLaVerdad:
    def test_avisa_del_registro_dentro_de_funcion(
        self, escenario_tardio: Path
    ) -> None:
        diferidos = [
            a for a in _avisos_del_escenario_sintetico(escenario_tardio)
            if a.startswith("registro dentro de una función")
        ]
        assert diferidos, (
            "el paquete sintético registra RataTardia dentro de una función "
            "y el validador no dijo nada"
        )

    def test_nombra_al_diferido_y_calla_al_de_modulo(
        self, escenario_tardio: Path
    ) -> None:
        """El aviso señala a `RataTardia`, no a `RataTemprana`.

        Si nombrara a los dos, «registra a nivel de módulo» sería imposible
        de seguir: el estudiante movería el registro y seguiría viendo el
        aviso.
        """
        diferidos = [
            a for a in _avisos_del_escenario_sintetico(escenario_tardio)
            if a.startswith("registro dentro de una función")
        ]
        assert any("RataTardia" in a for a in diferidos)
        assert not any("RataTemprana" in a for a in diferidos)

    def test_explica_que_saldra_otra_clase(
        self, escenario_tardio: Path
    ) -> None:
        """AUD-418 — decir «no se construirán» era falso: se construyen con
        otra clase. El aviso tiene que explicar eso."""
        diferidos = [
            a for a in _avisos_del_escenario_sintetico(escenario_tardio)
            if a.startswith("registro dentro de una función")
        ]
        assert any("otra clase" in a or "bestiario" in a for a in diferidos), (
            f"el aviso no explica qué sale en su lugar: {diferidos}"
        )

    def test_receta_la_cura(
        self, escenario_tardio: Path
    ) -> None:
        assert any(
            "Registra a nivel de módulo" in a
            for a in _avisos_del_escenario_sintetico(escenario_tardio)
        ), "el aviso diagnostica pero no receta"


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


class TestNadieRegistraDentroDeUnaFuncion:
    """AUD-591 — el trinquete: ningún mapa del motor registra diferido.

    Hasta este lote, `stage1_1` era el único caso activo y sus avisos se
    toleraban como «el caso conocido». Con su registro movido a nivel de
    módulo, el repositorio entero queda limpio y puede permitirse lo que
    antes no: prohibirlo. Si esta prueba falla, alguien acaba de introducir
    un registro que el previsualizador y el calificador no verán.
    """

    def test_stage1_1_registra_a_nivel_de_modulo(self) -> None:
        diferidos = [
            a for a in _avisos(STAGE1_1)
            if a.startswith("registro dentro de una función")
        ]
        assert not diferidos, (
            f"stage1_1 volvió a registrar dentro de una función: {diferidos}"
        )

    def test_ningun_mapa_del_motor_registra_diferido(self) -> None:
        sucios: dict[str, list[str]] = {}
        for mapa in sorted((_RAIZ / "assets" / "maps").rglob("*.tmx")):
            diferidos = [
                a for a in _avisos(mapa)
                if a.startswith("registro dentro de una función")
            ]
            if diferidos:
                sucios[mapa.parent.name] = diferidos
        assert not sucios, f"mapas con registro diferido: {sucios}"
