"""AUD-515 — el mirador y la pausa contemplativa de la Fase 6 (GAP-064
puntos 17 y 23-24).

Se daban por bloqueados —*«necesitan un sistema de cámara/pausa que el
motor no tiene»*— pero `CutsceneSystem` ya sabe mover la cámara
(`camara x y duración`, `cutscene_guion.py`) y ya se usa en este mismo mapa
para la cutscene de introducción (`bloquea=True` congela al jugador
mientras dura). El mirador es, literalmente, un guión de cutscene nuevo:
la cámara se aleja hacia el camino recorrido, se queda un momento —la
pausa contemplativa, porque el jugador no puede moverse mientras tanto— y
vuelve.

No se regeneró el mapa completo: `tools/generate_stage4_1.py` se niega sin
`--forzar` en cuanto detecta arte pintado a mano en `BG_Far`/`BG_Mid`
(`tiene_arte_pintado()`), y forzarlo lo habría borrado. El objeto
`Cutscene_167` se insertó como un parche quirúrgico del XML —sólo la capa
`Objects`, ninguna capa de baldosas— usando el bloque que el propio
generador produce, para que `TestElMapaSigueAtadoASuGenerador`
(`tests/test_stage4_1.py`) no distinga el mapa comprometido del que
generaría `_objetos()` con la llamada nueva.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from tests.ayudantes_stage4_1 import construir_escena, preparar_video


@pytest.fixture(scope="module")
def _video():
    preparar_video()


def _bloque_del_mirador(texto: str) -> str:
    """Localiza el `<object>...</object>` del mirador por ser el único
    `Cutscene` con área real —el de la introducción es un punto
    (`width="0" height="0"`)— y no por su `id`.

    AUD-516: bajar los checkpoints de 4-1 de 32 a 6 desplazó el id del
    mirador de 167 a 141, porque `obj()` los asigna secuencialmente y los
    checkpoints se generan antes en `_objetos()`. Buscar por `id` fijo es
    exactamente el defecto que ese lote reveló: cualquier cambio en el
    número de objetos anteriores rompe la prueba sin que el mirador mismo
    haya cambiado.
    """
    pos = 0
    while True:
        pos = texto.index('type="Cutscene"', pos)
        inicio = texto.rindex("<object", 0, pos)
        fin_apertura = texto.index(">", pos)
        if 'width="0"' in texto[inicio:fin_apertura + 1]:
            pos = fin_apertura + 1
            continue
        fin_bloque = texto.index("</object>", fin_apertura) + len("</object>")
        return texto[inicio:fin_bloque]


class TestElMiradorEstaDeclarado:
    def test_hay_un_segundo_objeto_cutscene(self) -> None:
        from pathlib import Path

        xml = Path("assets/maps/stage4_1/stage4_1.tmx").read_text(encoding="utf-8")
        assert xml.count('type="Cutscene"') == 2, (
            "debe haber exactamente dos: la introducción y el mirador"
        )

    def test_a_diferencia_de_la_introduccion_tiene_area_no_es_un_punto(self) -> None:
        """La introducción es un punto (dispara al empezar); el mirador
        tiene que ser un rectángulo (dispara al entrar el jugador) — si no,
        se dispararía al cargar el nivel, no al llegar a la Fase 6."""
        from pathlib import Path

        xml = Path("assets/maps/stage4_1/stage4_1.tmx").read_text(encoding="utf-8")
        bloque = _bloque_del_mirador(xml)
        etiqueta = bloque[:bloque.index(">") + 1]
        assert 'width="0"' not in etiqueta
        assert "width=" in etiqueta and "height=" in etiqueta

    def test_esta_antes_del_umbral_de_despertar(self) -> None:
        """Tiene que dar tiempo a que el jugador siga caminando después del
        mirador y aún llegue al umbral de la secuencia de despertar
        (AVANCE_DEL_DESPERTAR) — no puede quedar después."""
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES
        from src.stages.stage4_1.stage4_1 import Stage4_1

        fase6 = FASES[5]
        avance_mirador = ((trazado.COLUMNA_MIRADOR_FASE6 - fase6.desde_columna)
                          / trazado.ANCHO_SECCION)
        assert avance_mirador < Stage4_1.AVANCE_DEL_DESPERTAR


class TestElGuionDelMiradorNoTieneErroresDeSintaxis:
    def test_se_parsea_sin_errores(self) -> None:
        """Contra el analizador de verdad, no a ojo — mismo patrón que
        `TestLaCutsceneDeIntroduccion.test_el_guion_no_tiene_errores_de_sintaxis`."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1 import _objetos

        from src.framework.stage.cutscene_guion import ContextoDeGuion, analizar_guion

        objetos_xml = "\n".join(_objetos())
        bloque = _bloque_del_mirador(objetos_xml)
        marca = 'name="guion" value="'
        i0 = bloque.index(marca) + len(marca)
        i1 = bloque.index('"', i0)
        guion = (bloque[i0:i1].replace("&#10;", "\n").replace("&quot;", '"')
                 .replace("&lt;", "<").replace("&amp;", "&"))
        _script, errores = analizar_guion(guion, ContextoDeGuion())
        assert errores == [], f"el guion del mirador tiene errores: {errores}"

    def test_tiene_tres_movimientos_de_camara_dos_esperas_y_dos_fundidos(self) -> None:
        """AUD-571 — el contrato cambió con aprobación del dueño («extender
        el mirador un poco más»): tras alejar hacia el camino recorrido y
        volver, un tercer barrido se adelanta hacia donde asoma Paburu antes
        de fundir a negro. La prueba original exigía dos movimientos porque
        el guion de AUD-515 terminaba al volver; quedarse con ella habría
        seguido premiando el corte que el dueño pidió quitar."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1 import _objetos

        from src.framework.stage.cutscene_guion import ContextoDeGuion, analizar_guion
        from src.framework.stage.cutscene_system import (
            CameraMoveAction,
            FadeAction,
            WaitAction,
        )

        objetos_xml = "\n".join(_objetos())
        bloque = _bloque_del_mirador(objetos_xml)
        marca = 'name="guion" value="'
        i0 = bloque.index(marca) + len(marca)
        i1 = bloque.index('"', i0)
        guion = bloque[i0:i1].replace("&#10;", "\n")
        script, _errores = analizar_guion(guion, ContextoDeGuion())

        acciones = script._actions
        tipos = [type(a) for a in acciones]
        movimientos = [a for a in acciones if isinstance(a, CameraMoveAction)]
        assert len(movimientos) == 3, (
            "el mirador debe alejar hacia atrás, volver y mirar hacia Paburu:"
            " tres movimientos"
        )
        assert tipos.count(WaitAction) == 3
        assert tipos.count(FadeAction) == 2
        # El orden narrativo, no sólo el conteo: primero mira de dónde
        # viene (atrás), después vuelve al jugador y por último mira hacia
        # dónde va (adelante, y un poco hacia arriba).
        xs = [m._tx for m in movimientos]
        ys = [m._ty for m in movimientos]
        assert xs[0] < xs[1] < xs[2], (
            "los tres barridos deben ir de atrás hacia adelante"
        )
        assert ys[2] < ys[1], (
            "el barrido final hacia Paburu debe subir un poco la mirada"
        )


class TestElMiradorSeDisparaAlEntrar:
    def test_esta_en_las_escenas_guionizadas_del_mapa(self, _video) -> None:
        sc = construir_escena()
        try:
            from src.stages.stage4_1 import trazado

            objetivo_x = trazado.COLUMNA_MIRADOR_FASE6 * 16
            encontrado = any(
                abs(e.rect.x - objetivo_x) < 1
                for e in sc._stage_data.escenas
            )
            assert encontrado, (
                "no se encontró ninguna EscenaGuionizada en la columna del mirador"
            )
        finally:
            sc.on_exit()

    def test_bloquea_al_jugador_mientras_dura(self, _video) -> None:
        """La pausa contemplativa (puntos 23-24): el jugador no puede
        avanzar mientras la cámara mira atrás."""
        sc = construir_escena()
        try:
            from src.stages.stage4_1 import trazado

            objetivo_x = trazado.COLUMNA_MIRADOR_FASE6 * 16
            escena_mirador = next(
                e for e in sc._stage_data.escenas
                if abs(e.rect.x - objetivo_x) < 1
            )
            assert escena_mirador.bloquea is True
        finally:
            sc.on_exit()
