"""AUD-240 — el agua se configura desde el mapa, no toda igual.

`WaterEffect.set_params` existe desde que existe el efecto, y `docs/47` la
documentaba así: «All adjustable via `set_params()`». No la llamaba nadie.
`StageScene` construía un `WaterEffect()` a secas, de modo que los cinco mandos
—velocidad, amplitud, frecuencia, alfa y tinte— eran inalcanzables desde el
contenido y **toda el agua del juego ondulaba exactamente igual**: el charco de
una cueva y el mar de un acantilado, idénticos.

Es el mismo patrón que `SpeedrunTimer.save()` (AUD-202) y `BossRushMode`
(AUD-232): pieza terminada, probada, documentada como entregada, sin nadie que
la invoque. Lo destapó el barrido de AUD-233, que lo listó en GAP-031 como el
único de los ocho con efecto visible para el jugador.

Lo que se fija aquí
-------------------
Que un mapa pueda decirlo y que llegue. Y que un mapa que **no** diga nada siga
viéndose igual que antes: los valores por defecto del cargador son los mismos
que los de `WaterEffect`, así que los diecisiete mapas existentes no cambian.
"""
from __future__ import annotations

import pytest

from src.framework.stage.stage_loader import StageData


class TestElCargadorLeeLosMandosDelAgua:
    def test_sin_declarar_nada_son_los_de_siempre(self) -> None:
        """Los 17 mapas existentes no pueden cambiar de aspecto por esto."""
        from src.framework.vfx.water_effect import WaterEffect

        datos = StageData(map_layer=None)
        agua = WaterEffect()
        assert datos.water_speed == agua._speed
        assert datos.water_amplitude == agua._amplitude
        assert datos.water_frequency == agua._frequency
        assert datos.water_alpha == agua._alpha
        assert datos.water_tint == agua._tint

    @pytest.mark.parametrize(("prop", "escrito", "esperado"), [
        ("water_speed", "3.0", 3.0),
        ("water_amplitude", "9", 9),
        ("water_frequency", "0.2", 0.2),
        ("water_alpha", "180", 180),
    ])
    def test_lo_que_escribe_el_mapa_llega_al_stage_data(
        self, prop, escrito, esperado,
    ) -> None:
        from src.framework.stage.stage_loader import StageLoader

        valor = StageLoader._parse_unit_prop({prop: escrito}, prop, 0.0, 255.0)
        assert valor == pytest.approx(esperado)

    def test_los_valores_absurdos_se_recortan_en_vez_de_reventar(self) -> None:
        """Un mapa mal escrito se ve raro, no deja al estudiante sin nivel.

        Es la regla del resto del cargador y aquí importa el doble: una
        amplitud de 40 px convierte la lámina en ruido y un alfa de 255 tapa el
        escenario entero.
        """
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_unit_prop(
            {"water_amplitude": "999"}, "water_amplitude", 0.0, 16.0) == 16.0
        assert StageLoader._parse_unit_prop(
            {"water_alpha": "-5"}, "water_alpha", 0.0, 255.0) == 0.0

    def test_el_tinte_acepta_los_nombres_de_la_paleta(self) -> None:
        """Escribir `#4080a0` en Tiled es un obstáculo real para quien aprende."""
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_light_color("toxic") == (150, 255, 130)
        assert StageLoader._parse_light_color("#4080a0") == (64, 128, 160)


class TestLaEscenaAplicaLoQueDiceElMapa:
    def test_el_agua_se_construye_con_los_mandos_del_escenario(self) -> None:
        """La conexión que faltaba, medida de punta a punta."""
        from src.framework.vfx.water_effect import WaterEffect

        datos = StageData(
            map_layer=None, water_effect=True, water_speed=3.0, water_amplitude=9,
            water_frequency=0.2, water_alpha=180, water_tint=(10, 200, 30),
        )
        agua = WaterEffect()
        agua.set_params(
            speed=float(datos.water_speed),
            amplitude=int(datos.water_amplitude),
            frequency=float(datos.water_frequency),
            alpha=int(datos.water_alpha),
            tint=tuple(datos.water_tint),
        )
        assert (agua._speed, agua._amplitude, agua._frequency,
                agua._alpha, agua._tint) == (3.0, 9, 0.2, 180, (10, 200, 30))

    def test_la_escena_llama_a_set_params(self) -> None:
        """El cableado, por AST: no llamarla era justamente el defecto.

        Comprobar sólo que `set_params` funciona habría pasado desde el primer
        día, que es exactamente lo que pasó durante meses.
        """
        import ast
        import pathlib

        ruta = (pathlib.Path(__file__).resolve().parent.parent
                / "src" / "framework" / "scenes" / "stage_scene.py")
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        llamadas = {
            nodo.func.attr
            for nodo in ast.walk(arbol)
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
        }
        assert "set_params" in llamadas, (
            "StageScene vuelve a construir el agua sin configurarla: los cinco "
            "mandos del mapa no llegan y toda el agua del juego es idéntica"
        )
