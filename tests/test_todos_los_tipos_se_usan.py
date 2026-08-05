"""
Ningún tipo de objeto se queda sin usar — AUD-153.

El fallo, en su forma más barata
=================================
Diecisiete tipos que el cargador reconoce no aparecían en **ningún** TMX del
juego: siete de escenario —`Key`, `Door`, `Cage`, `EventTrigger`, `Spring`,
`FrictionZone`, `ShockwaveZone`, `Cutscene`— y diez especies del bestiario.

No era código roto. Era código que nadie recorre, que en este proyecto es la
misma familia que la iluminación que no iluminaba y el nado inalcanzable, sólo
que un paso antes: el camino existe y no hay nadie andándolo. Una regresión en
`_handle_cerradura` no la habría visto nadie hasta que un estudiante pusiera su
primera puerta en Tiled y no funcionara — el peor momento para descubrirlo.

Lo que estas pruebas defienden
-------------------------------
1. **Que la lista siga en cero.** Añadir un tipo al cargador sin colocarlo en
   ningún mapa vuelve a poner esta prueba en rojo.
2. **Que colocarlo signifique que se construye.** Un `type=` en el XML no es
   una entidad: hay que cargar el mapa y contar lo que salió.
3. **Que la sala 8 se pueda resolver.** Una puerta sin llave delante convierte
   el laboratorio en un pasillo sin salida.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pygame
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

LAB = RAIZ / "assets" / "maps" / "stage_mecanicas" / "stage_mecanicas.tmx"

#: Tipos que el motor reconoce a propósito y que **no** se espera ver en un
#: mapa del juego. Cada uno con su motivo escrito: una excepción con nombre se
#: puede revisar, un silencio no.
SIN_MAPA_A_PROPOSITO: dict[str, str] = {
    "BossSpawn": (
        "AUD-259. Sólo tiene sentido en un mapa de jefe, y los tres que hay "
        "son entregas de estudiantes que ya colocan el suyo con su tipo "
        "propio: añadirlo duplicaría el jefe. Y el laboratorio —el mapa donde "
        "se coloca todo lo demás— no tiene jefe, así que meter uno sería "
        "enseñar la mecánica equivocada. Lo ejercita "
        "tests/test_boss_spawn_desde_tiled.py de punta a punta."
    ),
}


def _tipos_usados_en_los_mapas() -> set[str]:
    usados: set[str] = set()
    for tmx in (RAIZ / "assets" / "maps").rglob("*.tmx"):
        texto = tmx.read_text(encoding="utf-8", errors="replace")
        for trozo in re.finditer(r"<object\b[^>]*", texto):
            tipo = re.search(r'\s(?:type|class)="([^"]+)"', trozo.group(0))
            if tipo:
                usados.add(tipo.group(1))
    return usados


def _tipos_del_motor() -> set[str]:
    from check_tmx_coverage import tipos_del_motor

    return tipos_del_motor()


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture(scope="module")
def laboratorio(_video):
    from src.framework.entities import entity_factory
    from src.framework.stage.stage_loader import StageLoader

    entity_factory.ensure_registered()
    return StageLoader.load(LAB)


class TestNoQuedanTiposHuerfanos:
    def test_todo_tipo_conocido_aparece_en_algun_mapa(self, _video) -> None:
        huerfanos = sorted(
            _tipos_del_motor() - _tipos_usados_en_los_mapas()
            - set(SIN_MAPA_A_PROPOSITO))
        assert huerfanos == [], (
            f"{len(huerfanos)} tipos que el cargador reconoce y ningún mapa "
            f"coloca: {huerfanos}. O se colocan en el laboratorio "
            f"(`tools/generate_stage_mecanicas.py`) o se justifican en "
            f"SIN_MAPA_A_PROPOSITO con su motivo"
        )

    def test_ningun_mapa_usa_un_tipo_que_el_motor_no_conozca(self, _video) -> None:
        """El error contrario: un `type` mal escrito en Tiled.

        Se comprueba sólo contra el laboratorio y stage0 —los dos mapas del
        profesor—: los escenarios de los estudiantes registran sus propios
        tipos desde su paquete y aquí no están importados, así que acusarlos
        sería un falso positivo.
        """
        conocidos = _tipos_del_motor()
        for nombre in ("stage_mecanicas", "stage0"):
            ruta = RAIZ / "assets" / "maps" / nombre / f"{nombre}.tmx"
            texto = ruta.read_text(encoding="utf-8", errors="replace")
            usados = {
                m.group(1)
                for trozo in re.finditer(r"<object\b[^>]*", texto)
                if (m := re.search(r'\s(?:type|class)="([^"]+)"', trozo.group(0)))
            }
            assert usados <= conocidos, (
                f"{nombre}.tmx usa tipos que el motor no conoce: "
                f"{sorted(usados - conocidos)}"
            )


class TestElLaboratorioLosConstruyeDeVerdad:
    """Un `type=` en el XML no es una entidad. Hay que cargar y contar."""

    #: Las diez especies que no aparecían en ningún mapa.
    FAUNA = (
        "WalkerInsect", "WalkerRaton", "FlyingCucaracha", "WalkerEstudiante",
        "FlyingNotebook", "ShooterTiza", "ShooterCocinero", "WalkerTerciopelo",
        "FlyingTerciovolador", "ShooterVenomoLargo",
    )

    def test_las_diez_especies_llegan_a_ser_entidades(self, laboratorio) -> None:
        assert len(laboratorio.entity_list) >= len(self.FAUNA), (
            f"el mapa declara {len(self.FAUNA)} especies nuevas y el cargador "
            f"construyó {len(laboratorio.entity_list)} entidades en total"
        )

    def test_hay_de_los_tres_arquetipos(self, laboratorio) -> None:
        clases = {type(e).__name__ for e in laboratorio.entity_list}
        assert {"EnemyWalker", "EnemyFlying", "EnemyShooter"} <= clases

    def test_la_puerta_y_la_jaula_existen_y_son_distintas(self, laboratorio) -> None:
        clases = {c.clase for c in laboratorio.cerraduras}
        assert clases == {"puerta", "jaula"}, (
            f"se esperaban las dos cerraduras del laboratorio y hay {clases}"
        )

    def test_el_resorte_y_las_dos_zonas_se_construyeron(self, laboratorio) -> None:
        nombres = {type(c).__name__
                   for grupo in laboratorio.componentes for c in grupo}
        assert "Resorte" in nombres
        assert "ZonaDeFriccion" in nombres
        assert "ZonaLetalTemporizada" in nombres

    def test_el_disparador_emite_el_evento_que_abre_la_jaula(self, laboratorio) -> None:
        eventos = {d.evento for d in laboratorio.disparadores}
        jaula = next(c for c in laboratorio.cerraduras if c.clase == "jaula")
        assert jaula.abre_con_evento in eventos, (
            f"la jaula espera «{jaula.abre_con_evento}» y los disparadores del "
            f"mapa emiten {sorted(eventos)}: no se abriría nunca"
        )


class TestLaSalaOchoSePuedeResolver:
    """Una puerta cerrada sin su llave delante es un pasillo sin salida."""

    def test_la_puerta_tiene_su_llave_en_el_mapa(self, laboratorio) -> None:
        # El recogible guarda `item_id`, no `key_id`: `Key` es un alias de
        # `Pickup` y el cargador acepta las dos propiedades para nombrarlo.
        puerta = next(c for c in laboratorio.cerraduras if c.clase == "puerta")
        llaves = {r.item_id for r in laboratorio.recogibles if r.item_id}
        assert puerta.key_id in llaves, (
            f"la puerta pide «{puerta.key_id}» y el mapa reparte {sorted(llaves)}"
        )

    def test_la_llave_esta_antes_que_la_puerta(self, laboratorio) -> None:
        puerta = next(c for c in laboratorio.cerraduras if c.clase == "puerta")
        llave = next(r for r in laboratorio.recogibles
                     if r.item_id == puerta.key_id)
        assert llave.rect.x < puerta.rect.x, (
            "la llave está detrás de la puerta que abre"
        )


class TestElGuionDeLaEscenaSobreviveAlXML:
    """AUD-153 — el salto de línea, y por qué casi se pierde.

    Un XML normaliza los espacios en blanco dentro de un valor de atributo, así
    que un `\\n` literal se lee como un espacio. El guion llegaba al motor como
    **una sola línea** y —esto es lo grave— `analizar_guion` no daba ni un
    error: se quedaba con la primera orden y descartaba las otras dos en
    silencio. Comprobado antes de arreglarlo.
    """

    def test_el_guion_conserva_sus_lineas(self, laboratorio) -> None:
        guion = laboratorio.escenas[0].guion
        assert len(guion.splitlines()) >= 3, (
            f"el guion llegó aplanado: {guion!r}"
        )

    def test_y_se_analiza_sin_errores(self, laboratorio) -> None:
        from src.framework.stage.camera import Camera
        from src.framework.stage.cutscene_guion import (
            ContextoDeGuion,
            analizar_guion,
        )

        class _Bus:
            def emit(self, *_a, **_k) -> None:
                pass

        guion, errores = analizar_guion(
            laboratorio.escenas[0].guion,
            ContextoDeGuion(camara=Camera(), bus=_Bus()),
        )
        assert errores == []
        assert len(guion._actions) >= 2, (
            "el analizador aceptó el guion y produjo menos acciones de las "
            "escritas: es exactamente el fallo silencioso del aplanado"
        )


class TestElMapaSigueAtadoASuGenerador:
    """Editar el TMX a mano y no el generador deja los dos divergiendo."""

    def test_el_tmx_es_el_que_produce_el_script(self) -> None:
        sys.path.insert(0, str(RAIZ / "tools"))
        from generate_stage_mecanicas import generar

        assert LAB.read_text(encoding="utf-8") == generar(), (
            "stage_mecanicas.tmx no coincide con su generador: ejecuta "
            "`python tools/generate_stage_mecanicas.py`"
        )
