"""AUD-419 — el previsualizador dibuja lo que el análisis ya sabía.

Por qué esto y no un editor visual propio
=========================================
Tiled ya resuelve **colocar**: capas, objetos, propiedades. Lo que no puede
saber es si un salto se cruza, porque eso depende de la gravedad y del impulso
del jugador — números que viven en `settings.py`, no en el editor.

Ahí estaba la brecha, y no era falta de editor sino de **realimentación**:
`level_metrics.analyse_stage` detecta desde AUD-049 los huecos imposibles, los
exigentes, los repechos y los recogibles inalcanzables, **con coordenadas**, y
los escupía como texto. «Hueco imposible en (1520, 384)» no se traduce a un
sitio del mapa sin contar baldosas a mano.

`--diagnostico` lo pinta encima: rojo lo que rompe el nivel, ámbar lo que sólo
lo endurece. La distinción no es decorativa — un hueco exigente es información
de diseño, no un defecto, y pintarlo igual que uno imposible enseñaría a quitar
los saltos difíciles, que es lo contrario de lo que se quiere.

El defecto que apareció al probarlo
===================================
`_aplicar_luz` calculaba el brillo con `max(0.30, ambiente * factores)`: suelo
sin techo. `LightSystem.render_map` multiplica `ambient_color` canal a canal
por ese brillo, así que en cuanto el producto pasa de 1 el color se sale de
[0, 255] y pygame rechaza la llamada entera.

No era rebuscado: basta `ambient_light = 1.0`, valor legal y el que trae la
plantilla nueva. El previsualizador se negaba a dibujar el nivel y remitía a
`validate_tmx.py` — que lo daba por bueno con razón, porque el mapa no tenía
nada malo. Una herramienta culpando al fichero de su propio fallo.
"""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

_RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = _RAIZ / "student_templates" / "stage_template" / "stage_template.tmx"
STAGE0 = _RAIZ / "assets" / "maps" / "stage0" / "stage0.tmx"


@pytest.fixture(autouse=True)
def _video():
    if not pygame.display.get_init():
        pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((640, 480))


class TestElBrilloSeAcota:
    """El defecto: un mapa legal reventaba la herramienta."""

    def test_un_mapa_con_ambient_light_maximo_se_dibuja(self) -> None:
        from scripts.preview_tmx import construir_vista

        lienzo, _stage, (ancho, alto), _diag = construir_vista(PLANTILLA)
        assert ancho > 0 and alto > 0
        assert lienzo is not None

    def test_tambien_con_una_hora_que_aclara(self) -> None:
        """El brillo sale de `ambiente * factor_hora * factor_estación`.

        Con `ambient_light=1.0` y un mediodía, el producto es el que se
        desbordaba. Se prueba la hora explícita porque es el multiplicador que
        más sube.
        """
        from scripts.preview_tmx import construir_vista

        lienzo, _stage, _tam, _diag = construir_vista(PLANTILLA, hora=12.0)
        assert lienzo is not None

    def test_el_valor_por_defecto_sigue_dibujando(self) -> None:
        from scripts.preview_tmx import construir_vista

        lienzo, _stage, _tam, _diag = construir_vista(STAGE0)
        assert lienzo is not None


class TestElCalcoDeDiagnostico:
    def test_sin_la_bandera_no_hay_diagnostico(self) -> None:
        """No se paga el análisis si no se pide."""
        from scripts.preview_tmx import construir_vista

        _l, _s, _t, diagnostico = construir_vista(STAGE0, con_diagnostico=False)
        assert diagnostico == []

    def test_con_la_bandera_informa(self) -> None:
        from scripts.preview_tmx import construir_vista

        _l, _s, _t, diagnostico = construir_vista(STAGE0, con_diagnostico=True)
        assert diagnostico, "se pidió el diagnóstico y no devolvió nada"
        texto = "\n".join(diagnostico)
        for esperado in ("huecos imposibles", "la salida se alcanza"):
            assert esperado in texto

    def test_dice_los_numeros_del_salto(self) -> None:
        """Sin ellos, el rojo y el ámbar no significan nada.

        Que un hueco sea «exigente» sólo se entiende sabiendo que el salto
        cruza 86 px y que lo cómodo acaba en 68.
        """
        from scripts.preview_tmx import construir_vista

        _l, _s, _t, diagnostico = construir_vista(STAGE0, con_diagnostico=True)
        assert any("el salto cruza" in line for line in diagnostico)

    def test_marca_el_hueco_exigente_de_la_plantilla(self) -> None:
        """La plantilla trae un hueco de 80 px puesto a propósito (AUD-417)."""
        from scripts.preview_tmx import construir_vista

        _l, _s, _t, diagnostico = construir_vista(PLANTILLA, con_diagnostico=True)
        assert any("exigentes: 1" in line for line in diagnostico), (
            f"no se detectó el hueco exigente de la plantilla: {diagnostico}"
        )

    def test_pinta_de_verdad_sobre_el_lienzo(self, tmp_path: Path) -> None:
        """El calco tiene que **verse**, no sólo calcularse.

        Se compara el lienzo con y sin diagnóstico: si son idénticos, el
        análisis corrió y no dibujó nada — que es el modo de fallo de esta
        casa, código correcto que no llega a ninguna parte.
        """
        from scripts.preview_tmx import construir_vista

        limpio, _s, _t, _d = construir_vista(PLANTILLA, con_diagnostico=False)
        marcado, _s2, _t2, _d2 = construir_vista(PLANTILLA, con_diagnostico=True)
        assert pygame.image.tobytes(limpio, "RGB") != \
            pygame.image.tobytes(marcado, "RGB"), (
            "el lienzo con diagnóstico es idéntico al de sin: no se pintó nada"
        )


# Aquí había una prueba —«un mapa roto no se dibuja a medias»— que copiaba
# `stage0` a `tmp_path`, le quitaba la capa `Collision` y esperaba un
# `FrameworkUsageError`. **No comprobaba eso.** La copia deja el TMX fuera de
# su directorio, así que la ruta relativa del tileset (`../../assets/...`) deja
# de resolver y pytmx aborta con `FileNotFoundError` mucho antes de que nadie
# mire las capas. Pasaba con `pytest.raises(Exception)` por el motivo
# equivocado, y ruff lo señaló con B017.
#
# Se retira en vez de arreglarse: lo que pretendía comprobar —que un mapa sin
# `Collision` se rechaza— ya lo cubre `test_stage_loader.py` sobre el cargador,
# que es donde vive la regla. Una prueba que pasa por un motivo distinto del
# que dice es peor que no tenerla; es la lección que más veces ha salido en
# esta fase.
