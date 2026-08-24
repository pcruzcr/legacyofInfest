"""AUD-282 — la sacudida decía «ha pasado algo», no «de dónde».

El defecto
----------
`Camera.apply_shake` sacudía con ruido isótropo: dos `random.uniform` sin
relación entre sí. Un golpe recibido por la izquierda y otro por la derecha se
sentían idénticos, así que la sacudida sólo transmitía intensidad. La mitad de
la información que un jugador necesita —de qué lado viene— se perdía.

Lo que se fija aquí
-------------------
1. **Que sin dirección no cambie nada.** Es la condición para que las 26 clases
   de escenario y los dieciséis mapas sigan comportándose igual: todos llaman
   sin el parámetro nuevo.
2. **Que con dirección el desplazamiento vaya por su eje**, y que sea una
   oscilación coherente y no ruido — el ruido en un eje se percibe igual que el
   ruido en dos.
3. **Que la dirección viaje con la amplitud.** Dos sistemas discutiendo el eje
   en el mismo fotograma es cómo esto acabaría pareciendo un fallo de vídeo.
4. **Que «movimiento reducido» siga mandando.**
"""
from __future__ import annotations

from itertools import pairwise

import pygame
import pytest

from src.framework.stage.camera import Camera


@pytest.fixture
def camara() -> Camera:
    c = Camera()
    c.set_map_size(10000, 10000)
    return c


def _muestrear(camara: Camera, pasos: int = 12) -> list[pygame.Vector2]:
    """Los desplazamientos de sacudida de unos cuantos fotogramas."""
    desplazamientos = []
    for _ in range(pasos):
        camara._aplicar_sacudida(1.0 / 60.0)
        desplazamientos.append(pygame.Vector2(camara._shake_offset))
    return desplazamientos


class TestSinDireccionTodoSigueIgual:
    def test_el_valor_por_defecto_no_fija_eje(self, camara) -> None:
        camara.apply_shake(amplitude=5.0, duration=0.5)
        assert camara._shake_dir is None

    def test_y_sacude_en_los_dos_ejes(self, camara) -> None:
        camara.apply_shake(amplitude=5.0, duration=1.0)
        muestras = _muestrear(camara, 30)
        assert any(abs(m.x) > 0.01 for m in muestras)
        assert any(abs(m.y) > 0.01 for m in muestras)


class TestConDireccion:
    def test_el_desplazamiento_va_por_su_eje(self, camara) -> None:
        """Un golpe horizontal mueve la pantalla en horizontal."""
        camara.apply_shake(amplitude=6.0, duration=1.0, direccion=(1.0, 0.0))
        muestras = _muestrear(camara, 30)
        eje = max(abs(m.x) for m in muestras)
        cruzado = max(abs(m.y) for m in muestras)
        assert eje > cruzado * 2.0, (
            f"eje {eje:.2f} contra cruzado {cruzado:.2f}: el desplazamiento no "
            "sigue la dirección del golpe"
        )

    def test_queda_temblor_cruzado(self, camara) -> None:
        """Una oscilación puramente rectilínea se ve mecánica, como un motor."""
        camara.apply_shake(amplitude=6.0, duration=1.0, direccion=(1.0, 0.0))
        muestras = _muestrear(camara, 40)
        assert any(abs(m.y) > 0.01 for m in muestras)

    def test_es_una_onda_y_no_ruido(self, camara) -> None:
        """Ruido limitado a un eje se percibe igual que ruido en dos: como
        vibración. Lo que se lee como empujón es ir y volver de forma coherente,
        así que el signo tiene que cambiar pocas veces, no en cada fotograma.
        """
        camara.apply_shake(amplitude=6.0, duration=1.0, direccion=(1.0, 0.0))
        muestras = _muestrear(camara, 24)
        signos = [1 if m.x >= 0 else -1 for m in muestras]
        cambios = sum(1 for a, b in pairwise(signos) if a != b)
        assert cambios <= len(signos) // 3, (
            f"{cambios} cambios de signo en {len(signos)} fotogramas: eso es "
            "ruido con eje, no una oscilación"
        )

    def test_la_vertical_tambien(self, camara) -> None:
        camara.apply_shake(amplitude=6.0, duration=1.0, direccion=(0.0, 1.0))
        muestras = _muestrear(camara, 30)
        assert max(abs(m.y) for m in muestras) > max(abs(m.x) for m in muestras)

    def test_un_vector_nulo_es_como_no_dar_direccion(self, camara) -> None:
        """Dos entidades exactamente superpuestas pasa más de lo que parece, y
        normalizar un vector cero es una división por cero."""
        camara.apply_shake(amplitude=4.0, duration=0.3, direccion=(0.0, 0.0))
        assert camara._shake_dir is None

    def test_una_direccion_ilegible_no_revienta(self, camara) -> None:
        camara.apply_shake(amplitude=4.0, duration=0.3, direccion="izquierda")
        assert camara._shake_dir is None


class TestLaDireccionViajaConLaAmplitud:
    def test_un_golpe_mas_flojo_no_pisa_el_eje(self, camara) -> None:
        camara.apply_shake(amplitude=8.0, duration=0.5, direccion=(1.0, 0.0))
        camara.apply_shake(amplitude=1.0, duration=0.5, direccion=(0.0, 1.0))
        assert camara._shake_dir == pygame.Vector2(1.0, 0.0)

    def test_uno_mas_fuerte_si(self, camara) -> None:
        camara.apply_shake(amplitude=2.0, duration=0.5, direccion=(1.0, 0.0))
        camara.apply_shake(amplitude=9.0, duration=0.5, direccion=(0.0, 1.0))
        assert camara._shake_dir == pygame.Vector2(0.0, 1.0)

    def test_al_acabar_se_olvida(self, camara) -> None:
        """Un eje que sobrevive a su sacudida orientaría la siguiente."""
        camara.apply_shake(amplitude=5.0, duration=0.05, direccion=(1.0, 0.0))
        _muestrear(camara, 20)
        assert camara._shake_dir is None


class TestAccesibilidad:
    def test_movimiento_reducido_atenua_tambien_la_direccional(
        self, camara, monkeypatch,
    ) -> None:
        """El filtro está en el disparador justamente para que ninguna variante
        nueva se lo salte."""
        from src.engine.core import user_settings
        from src.engine.core.user_settings import MOVIMIENTO_REDUCIDO_FACTOR

        monkeypatch.setattr(
            user_settings, "preferencia",
            lambda clave, defecto=None: True if clave == "reduced_motion" else defecto,
        )
        camara.apply_shake(amplitude=8.0, duration=0.5, direccion=(1.0, 0.0))
        assert camara._shake_amplitude == pytest.approx(8.0 * MOVIMIENTO_REDUCIDO_FACTOR)


class TestQuienLaUsa:
    """Un parámetro que nadie pasa es código muerto con documentación."""

    def test_el_dano_al_jugador_manda_direccion(self) -> None:
        import inspect

        from src.framework.scenes.stage_parts import senales

        fuente = inspect.getsource(senales)
        assert "direccion=direccion" in fuente, (
            "el daño al jugador sigue sacudiendo en isótropo: la dirección "
            "existe y nadie la usa"
        )

    def test_el_pisoton_va_hacia_abajo(self) -> None:
        import inspect

        from src.framework.scenes.stage_parts import senales

        assert "direccion=(0.0, 1.0)" in inspect.getsource(senales)
