"""AUD-338 — el velo de niebla de guerra respira (animación lenta).

El velo de `fog_of_war.py` estaba congelado: la máscara se construía una vez y
cada fotograma era idéntico al anterior. Con `animado=True` (por defecto) el
radio de los agujeros y el alfa del velo oscilan despacio en antifase.

Las pruebas pintan sobre lienzo, como las de `test_orphan_systems.py`, y
comprueban tres cosas: que el respiro cambia de verdad lo que se ve, que
`animado=False` es exactamente el velo de siempre, y que en fase cero —una
prueba que no llama a `update()`— el dibujo es idéntico al estático.
"""
import numpy as np
import pygame
import pytest


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


def _lienzo(color=(120, 120, 120)) -> pygame.Surface:
    s = pygame.Surface((320, 180))
    s.fill(color)
    return s


def _brillo(s: pygame.Surface) -> np.ndarray:
    return pygame.surfarray.array3d(s).astype(float)


def _fog(**kwargs):
    from src.framework.vfx.fog_of_war import FogOfWar

    return FogOfWar(320, 180, radius=40, **kwargs)


class TestElVeloRespira:
    def test_el_dibujo_cambia_con_el_tiempo(self, display) -> None:
        """Un cuarto de ciclo después, la misma escena pinta distinto."""
        niebla = _fog(velocidad=0.25, pulso=4)
        niebla.reveal(160, 90)

        a = _lienzo()
        niebla.draw(a, pygame.Vector2(0, 0))
        niebla.update(1.0)  # un cuarto de ciclo: radio máximo, alfa mínimo
        b = _lienzo()
        niebla.draw(b, pygame.Vector2(0, 0))

        assert not np.array_equal(_brillo(a), _brillo(b))

    def test_el_agujero_crece_y_el_velo_se_aclara_en_antifase(self, display) -> None:
        """En el máximo del respiro el hueco es más grande y el velo más claro.

        Proyecto el velo contra un fondo blanco: donde hay velo el brillo cae,
        donde hay agujero se mantiene. Sonda fuera del radio base (42 px) —
        al encoger el agujero queda velada, al crecer queda revelada.
        """
        niebla = _fog(velocidad=0.25, pulso=4, pulso_del_velo=8)
        niebla.reveal(160, 90)

        lienzo = _lienzo((255, 255, 255))
        niebla.draw(lienzo, pygame.Vector2(0, 0))
        fuera = float(_brillo(lienzo)[202, 90].mean())  # 42 px del centro

        niebla.update(1.0)  # radio máximo (44), velo más claro (212)
        lienzo = _lienzo((255, 255, 255))
        niebla.draw(lienzo, pygame.Vector2(0, 0))
        dentro = float(_brillo(lienzo)[202, 90].mean())

        assert dentro > fuera + 5.0, (
            f"el respiro no se nota en el borde: fuera={fuera:.0f} dentro={dentro:.0f}"
        )

    def test_el_radio_oscila_acotado_y_nunca_apaga_el_hueco(self, display) -> None:
        niebla = _fog(velocidad=0.25, pulso=4, pulso_del_velo=8)
        radios = []
        alfas = []
        for _ in range(80):
            niebla.update(0.05)
            niebla.draw(_lienzo(), pygame.Vector2(0, 0))
            radios.append(niebla._radio_actual)
            alfas.append(niebla._alfa_actual)
        assert min(radios) >= 40 - 4 and max(radios) <= 40 + 4, radios
        assert min(radios) >= 1, "el agujero llegó a desaparecer"
        assert max(alfas) <= 255 and min(alfas) >= 0, alfas
        assert max(alfas) - min(alfas) > 0, "el alfa no osciló"
        assert max(radios) - min(radios) > 0, "el radio no osciló"

    def test_la_mascara_solo_se_reconstruye_al_cambiar(self, display) -> None:
        """La caché de AUD-213 se respeta: misma fase, misma máscara."""
        niebla = _fog(velocidad=0.25, pulso=4)
        niebla.draw(_lienzo(), pygame.Vector2(0, 0))
        primera = niebla._hole_mask
        niebla.draw(_lienzo(), pygame.Vector2(0, 0))
        assert niebla._hole_mask is primera, "se reconstruyó sin cambiar la fase"

        niebla.update(1.0)
        niebla.draw(_lienzo(), pygame.Vector2(0, 0))
        assert niebla._hole_mask is not primera, "el respiro no reconstruyó la máscara"


class TestElVeloEstaticoNoCambia:
    def test_sin_animacion_dos_fases_dibujan_igual(self, display) -> None:
        niebla = _fog(animado=False)
        niebla.reveal(160, 90)
        niebla.update(2.5)

        a = _lienzo()
        niebla.draw(a, pygame.Vector2(0, 0))
        niebla.update(2.5)
        b = _lienzo()
        niebla.draw(b, pygame.Vector2(0, 0))

        assert np.array_equal(_brillo(a), _brillo(b))

    def test_en_fase_cero_la_animacion_es_el_comportamiento_anterior(self, display) -> None:
        """Sin `update()`, el velo animado dibuja exactamente el estático."""
        animado = _fog(animado=True, velocidad=0.25, pulso=4, pulso_del_velo=8)
        estatico = _fog(animado=False)
        for niebla in (animado, estatico):
            niebla.reveal(160, 90)

        a = _lienzo()
        animado.draw(a, pygame.Vector2(0, 0))
        b = _lienzo()
        estatico.draw(b, pygame.Vector2(0, 0))

        assert np.array_equal(_brillo(a), _brillo(b))

    def test_el_pulso_no_puede_comerse_el_radio(self, display) -> None:
        from src.framework.vfx.fog_of_war import FogOfWar

        niebla = FogOfWar(320, 180, radius=2, pulso=50)
        assert niebla._pulso <= 1, "un agujero que respira no debe desaparecer"
