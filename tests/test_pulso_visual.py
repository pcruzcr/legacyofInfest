"""AUD-425 — el reloj musical no tenía ningún consumidor visual.

El defecto
==========
`docs/62` §C1 listaba seis piezas para el reloj musical. Cinco estaban hechas
desde AUD-137 —reloj alimentado por la posición de la pista, `bpm`/`compas`
como propiedades de mapa, objetos cuantizados a compás, compensación de
latencia— y AUD-414 dejó dicho que la sexta seguía viva: «pulso visual: cámara,
escala y luz al compás».

El motivo de que faltara es el de siempre aquí: `engine/audio/music_clock.py`
son 280 líneas que saben exactamente en qué punto del compás va la música, y
**ningún consumidor visual las miraba**. La información estaba; faltaba
enchufarla.

Lo que fija esta prueba
=======================
Sobre todo lo que **no** debe pasar. Un latido visual es fácil de hacer mal:

* que lata sin música —los diecisiete mapas sin `bpm` tienen que verse igual—;
* que no llegue a apagarse entre pulso y pulso, con lo que deja de ser una
  acentuación y se convierte en un temblor continuo;
* que el primer tiempo del compás pese lo mismo que los demás, con lo que un
  4/4 se siente como cuatro golpes iguales y se pierde el compás.
"""
from __future__ import annotations

import pytest

from src.framework.vfx import pulso


class _RelojFalso:
    """Lo mínimo que `pulso` consulta: en qué punto del pulso y del compás va."""

    def __init__(self, fraccion: float = 0.0, pulso_en_compas: int = 0) -> None:
        self.fraccion = fraccion
        self.pulso_en_compas = pulso_en_compas


class TestSinMusicaNoLate:
    """Lo primero que no se puede romper: los mapas que no son rítmicos."""

    def test_sin_reloj_la_intensidad_es_cero(self) -> None:
        assert pulso.intensidad(None) == 0.0

    def test_sin_reloj_la_camara_no_se_mueve(self) -> None:
        assert pulso.offset_de_camara(None) == 0.0

    def test_sin_reloj_la_luz_no_cambia(self) -> None:
        """1,0 exacto: multiplicar por esto tiene que ser no hacer nada."""
        assert pulso.factor_de_luz(None) == 1.0

    def test_un_reloj_incompleto_no_tumba_el_fotograma(self) -> None:
        """Un doble de prueba sin los campos no puede reventar el dibujado.

        Misma regla que el contador de texturas en AUD-413: lo que decora un
        fotograma no puede tirarlo.
        """
        assert pulso.intensidad(object()) == 0.0


class TestElGolpe:
    def test_es_maximo_al_entrar_el_pulso(self) -> None:
        assert pulso.intensidad(_RelojFalso(fraccion=0.0)) == pytest.approx(1.0)

    def test_decae(self) -> None:
        pronto = pulso.intensidad(_RelojFalso(fraccion=0.05))
        tarde = pulso.intensidad(_RelojFalso(fraccion=0.25))
        assert pronto > tarde > 0.0

    def test_se_apaga_antes_del_siguiente(self) -> None:
        """Si no llegara a cero, sería un temblor y no una acentuación."""
        assert pulso.intensidad(_RelojFalso(fraccion=0.6)) == 0.0
        assert pulso.intensidad(_RelojFalso(fraccion=0.99)) == 0.0

    def test_nunca_se_pasa_de_uno(self) -> None:
        """El acento multiplica; sin tope, el primer tiempo se saldría."""
        for f in (0.0, 0.01, 0.1, 0.2, 0.34):
            assert 0.0 <= pulso.intensidad(_RelojFalso(fraccion=f)) <= 1.0


class TestElCompas:
    def test_el_primer_tiempo_pesa_mas(self) -> None:
        """`pulso_en_compas == 0` es el que se acentúa, lo dice el reloj."""
        acentuado = pulso.intensidad(_RelojFalso(fraccion=0.1, pulso_en_compas=0))
        normal = pulso.intensidad(_RelojFalso(fraccion=0.1, pulso_en_compas=2))
        assert acentuado > normal, (
            "el primer tiempo del compás pesa lo mismo que los demás: un 4/4 "
            "se sentiría como cuatro golpes iguales"
        )

    @pytest.mark.parametrize("tiempo", [1, 2, 3])
    def test_los_demas_tiempos_pesan_igual_entre_si(self, tiempo: int) -> None:
        base = pulso.intensidad(_RelojFalso(fraccion=0.1, pulso_en_compas=1))
        assert pulso.intensidad(
            _RelojFalso(fraccion=0.1, pulso_en_compas=tiempo)) == pytest.approx(base)


class TestLasAmplitudes:
    """Se nota sin que nadie sepa por qué se nota. Al doble, marea."""

    def test_la_camara_se_mueve_poco(self) -> None:
        maximo = pulso.offset_de_camara(_RelojFalso(fraccion=0.0))
        assert 0.0 < maximo <= 3.0, (
            f"{maximo} px de latido sobre 180 de alto interno es un salto de "
            "imagen, no una acentuación"
        )

    def test_la_camara_baja_y_no_sube(self) -> None:
        """El golpe se lee como un impacto contra el suelo."""
        assert pulso.offset_de_camara(_RelojFalso(fraccion=0.0)) > 0

    def test_la_luz_sube_poco(self) -> None:
        maximo = pulso.factor_de_luz(_RelojFalso(fraccion=0.0))
        assert 1.0 < maximo <= 1.15


def test_esta_enchufado_a_la_camara_y_a_la_luz() -> None:
    """El cable trampa: sin consumidor esto sería otro sistema huérfano.

    Es el modo de fallo de esta casa y el motivo de que el hueco existiera —el
    reloj llevaba desde AUD-137 sin que nadie mirara su compás—. Se comprueba
    por AST que las dos llamadas están donde tienen que estar.
    """
    import ast
    import inspect

    from src.framework.scenes import stage_scene
    from src.framework.scenes.stage_parts import simulacion

    def _llama_a(modulo, nombre: str) -> bool:
        arbol = ast.parse(inspect.getsource(modulo))
        return any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == nombre
            and isinstance(n.func.value, ast.Name) and n.func.value.id == "pulso"
            for n in ast.walk(arbol)
        )

    assert _llama_a(stage_scene, "offset_de_camara"), (
        "la cámara no consulta el pulso: el latido no llega a la imagen"
    )
    assert _llama_a(simulacion, "factor_de_luz"), (
        "la iluminación no consulta el pulso: la luz no late"
    )
