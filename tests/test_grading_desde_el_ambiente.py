"""AUD-401 — la corrección de color, alimentada por el ambiente. GAP-051.

Qué pasaba
==========
La pasada de *color grading* existe en `gl_pipeline.py` desde hace tiempo:
sombreador compilado, uniforme `colorMatrix`, y su rama en el post-procesado.
Lo que tenía era una matriz **fija en el config**:

    color_matrix: tuple[float, ...] = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

La identidad. Nadie la cambiaba nunca, así que el efecto estaba construido,
compilado, ejecutándose y multiplicando por uno. Es el tercero de los tres
consumidores que `GAP-051` marca 🔴, y el más barato de los tres porque no
necesitaba dato nuevo: la hora, la estación y la niebla ya estaban calculadas y
no llegaban a la imagen final.

Por qué se publica en vez de escribir el renderer
=================================================
Una escena **no puede alcanzarlo**. `GameContext` expone `usar_gl` y no el
objeto, y su comentario dice por qué: «una escena con la ruta de GPU no se
pregunta "¿hay renderer?" (no puede importarlo sin arrastrar ModernGL)». El
primer intento de este lote hizo justamente eso —`getattr(self.context,
"gl_renderer", None)`— y habría sido una función que nunca hace nada, porque
ese atributo no existe. El canal correcto es `gpu_effects`, el mismo del bloom.
"""
from __future__ import annotations

import pytest

from src.framework.world.environment import EnvironmentState


def _matriz(**kwargs) -> tuple[float, ...]:
    return EnvironmentState(**kwargs).matriz_de_color


class TestLaMatriz:
    def test_tiene_nueve_numeros(self) -> None:
        """El uniforme del sombreador es una `mat3`."""
        assert len(_matriz()) == 9

    def test_la_luz_blanca_y_el_aire_limpio_dan_la_identidad(self) -> None:
        """Un mediodía despejado no debe teñir nada.

        Es la prueba que impide que este lote cambie el aspecto de los mapas
        que no querían tinte: si el caso neutro no sale identidad, todos los
        escenarios se ven distintos desde hoy.
        """
        m = _matriz(color_ambiente=(255, 255, 255), visibilidad=1.0)
        assert m == pytest.approx((1, 0, 0, 0, 1, 0, 0, 0, 1), abs=1e-6)

    def test_un_tinte_calido_sube_el_rojo_sobre_el_azul(self) -> None:
        m = _matriz(color_ambiente=(255, 200, 150), visibilidad=1.0)
        assert m[0] > m[8], "el atardecer no está calentando la imagen"

    def test_un_tinte_frio_sube_el_azul_sobre_el_rojo(self) -> None:
        m = _matriz(color_ambiente=(150, 180, 255), visibilidad=1.0)
        assert m[8] > m[0]

    def test_el_tinte_no_cambia_el_brillo(self) -> None:
        """Normalizada al canal más alto, a propósito.

        El brillo ya lo lleva `factor_ambiente`; si el grading lo aplicara
        también, el atardecer oscurecería dos veces.
        """
        m = _matriz(color_ambiente=(120, 90, 60), visibilidad=1.0)
        assert max(m) == pytest.approx(1.0)

    def test_la_poca_visibilidad_desatura(self) -> None:
        """Lo que hace la niebla de verdad, y que ningún tinte imita."""
        despejado = _matriz(color_ambiente=(255, 200, 150), visibilidad=1.0)
        niebla = _matriz(color_ambiente=(255, 200, 150), visibilidad=0.1)
        # Fuera de la diagonal: cuanto más mezcla entre canales, más gris.
        assert abs(niebla[1]) > abs(despejado[1])

    def test_la_niebla_no_deja_el_juego_en_blanco_y_negro(self) -> None:
        """La legibilidad manda sobre el efecto.

        Con desaturación total no se distingue un enemigo venenoso de uno
        normal, que es la misma regla por la que la luz ambiente tiene suelo.
        """
        m = _matriz(color_ambiente=(255, 60, 60), visibilidad=0.0)
        gris = _matriz(color_ambiente=(255, 255, 255), visibilidad=0.0)
        assert m != pytest.approx(gris, abs=1e-6)


class TestElCanal:
    def test_publicar_y_leer(self) -> None:
        from src.engine.core import gpu_effects

        gpu_effects.publish_color_matrix((1, 0, 0, 0, 1, 0, 0, 0, 1))
        assert gpu_effects.published_color_matrix() == (1, 0, 0, 0, 1, 0, 0, 0, 1)
        gpu_effects.publish_color_matrix(None)
        assert gpu_effects.published_color_matrix() is None

    def test_sin_publicar_no_hay_matriz(self) -> None:
        """Un menú no hereda el tinte del nivel del que vienes."""
        from src.engine.core import gpu_effects

        gpu_effects.publish_color_matrix(None)
        assert gpu_effects.published_color_matrix() is None


def test_la_escena_publica_la_matriz_del_ambiente() -> None:
    """El cable trampa: que `_aplicar_hora` llegue a publicar.

    Por AST, y mirando **llamadas**: sin esto la matriz sería un derivado
    correcto que nadie pide, que es exactamente lo que el propio GAP-051
    registra que pasó con la mitad productora de `world/`.
    """
    import ast
    import inspect

    from src.framework.scenes.stage_parts import simulacion

    arbol = ast.parse(inspect.getsource(simulacion))
    llamadas = [
        n for n in ast.walk(arbol)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "publish_color_matrix"
    ]
    assert llamadas, (
        "la simulación calcula la matriz y no la publica: el color grading "
        "seguiría multiplicando por la identidad"
    )
