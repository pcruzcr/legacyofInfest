"""AUD-252 — el modo daltónico se perdía en cuanto se encendía la GPU.

El defecto
==========
`colorblind_frag` está escrito, compilado y enchufado a una pasada
(`gl_pipeline.py:785`), y esa pasada sólo se ejecuta si
`config.colorblind_mode > 0`. Medido: **nadie escribía nunca ese campo**. Se
quedaba en su valor por defecto —0, «off»— así que el sombreador estaba escrito
y jamás se ejecutaba, y el jugador que había elegido `deuteranopia` en Opciones
veía el juego sin corregir en cuanto la máquina tenía tarjeta.

`70_INFORME_DE_AUDITORIA_VIVO.md` (iteración 12) lo dejó «anotado». Esto lo
conecta.

Por qué se sincroniza cada fotograma y no sólo al arrancar
----------------------------------------------------------
Porque Opciones cambia la preferencia en caliente. La ruta de CPU ya lo hace
así —lee el ajuste cuando dibuja—, y hacer que la de GPU sólo lo leyera al
crear el contexto habría dejado un modo daltónico que exige reiniciar el juego,
que es media corrección.

El contrato del entero
----------------------
`shaders.py:393` declara `0=off, 1=protanopia, 2=deuteranopia, 3=tritanopia`, y
`user_settings.COLORBLIND_MODES` es exactamente esa tupla en ese orden. La
prueba fija esa correspondencia: si alguien añade un modo a la mitad de la
tupla sin tocar el sombreador, esto se pone rojo.
"""
from __future__ import annotations

import pytest

from src.engine.core import user_settings
from src.engine.core.user_settings import COLORBLIND_MODES


class TestElContratoDelEntero:
    def test_la_tupla_y_el_sombreador_dicen_lo_mismo(self) -> None:
        assert COLORBLIND_MODES == ("off", "protanopia", "deuteranopia", "tritanopia")

    def test_apagado_es_el_cero_que_salta_la_pasada(self) -> None:
        assert COLORBLIND_MODES.index("off") == 0


class TestLoQueLeeLaGpu:
    @pytest.mark.parametrize(
        ("modo", "esperado"),
        [("off", 0), ("protanopia", 1), ("deuteranopia", 2), ("tritanopia", 3)],
    )
    def test_la_preferencia_del_jugador_llega_a_la_configuracion_gl(
        self, modo: str, esperado: int,
    ) -> None:
        from src.engine.core.app import modo_daltonico_gl

        ajustes = user_settings.UserSettings()
        ajustes.colorblind_mode = modo

        assert modo_daltonico_gl(ajustes) == esperado

    def test_un_modo_desconocido_no_rompe_el_dibujado(self) -> None:
        """Prefiere no corregir antes que reventar el fotograma.

        `UserSettings.__post_init__` ya cae a «off» ante un valor raro, pero
        esta función la pueden llamar con un objeto construido a mano —una
        prueba, una entrega— y quedarse sin pantalla por un ajuste mal escrito
        sería peor que no corregir el color.
        """
        from src.engine.core.app import modo_daltonico_gl

        class _Raro:
            colorblind_mode = "no_existe"

        assert modo_daltonico_gl(_Raro()) == 0

    def test_sin_ajustes_tampoco_rompe(self) -> None:
        from src.engine.core.app import modo_daltonico_gl

        assert modo_daltonico_gl(None) == 0


class TestLaComprobacionQueLoHabriaEvitado:
    """Que `colorblind_mode` tenga quien lo escriba en `src/`, no sólo quien lo lea."""

    def test_alguien_escribe_el_campo_en_produccion(self) -> None:
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1] / "src"
        escrituras = [
            p for p in raiz.rglob("*.py")
            if "colorblind_mode =" in p.read_text(encoding="utf-8")
            and p.name != "gl_pipeline.py"        # ahí sólo está la declaración
            and p.name != "user_settings.py"      # ahí vive la preferencia
        ]
        assert escrituras, (
            "config.colorblind_mode se lee en la pasada de GL y nadie lo "
            "escribe: el sombreador no se ejecuta nunca."
        )
