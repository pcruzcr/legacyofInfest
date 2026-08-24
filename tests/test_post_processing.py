"""
Module: test_post_processing
System: tests
Academic Unit: VII

El bloom aclaraba las sombras más que las luces, y costaba 12 ms.

Dos defectos independientes en el mismo efecto:

* **F1.2a** — el halo se sumaba con `BLEND_RGB_ADD` tras un `set_alpha`, y
  `set_alpha` **no tiene efecto con ese modo de mezcla**. La escena reducida
  completa se sumaba al 100 %: medido, un fondo de valor 43 subía a 239 y una
  zona brillante de 208 subía a 234. El efecto aclaraba más lo oscuro que lo
  iluminado, que es exactamente lo contrario de un bloom.
* **F1.2b** — la capa de realce recorría los 480.000 píxeles de la pantalla con
  numpy: **12,08 ms**, el 72 % del presupuesto de fotograma. Como sólo se
  activaba en ráfagas de 0,15 a 0,6 s, recoger un objeto tiraba la tasa de
  refresco a la mitad justo en el momento más vistoso.

Y un tercero que apareció al corregirlos: difuminar el halo reduciendo y
volviendo a ampliar **no ensancha nada**, porque el remuestreo bilineal
interpola entre téxeles y devuelve la misma silueta con los bordes suaves.
Medido: aporte de +0,0 a 5, 20, 50, 90 y 150 px del borde del foco.

Estas pruebas miran píxeles concretos a distancias concretas. Una prueba que
sólo comprobara "la imagen cambió" habría pasado con el bloom invertido.
"""
from __future__ import annotations

import time

import numpy as np
import pygame
import pytest

from src.framework.vfx.post_processing import PostProcessing

ANCHO, ALTO = 800, 600
CENTRO_FOCO = (300, 300)
RADIO_FOCO = 90
CENTRO_ESPORAS = (600, 250)
FONDO = (40, 40, 50)


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((ANCHO, ALTO))
    yield pygame.display.get_surface()


@pytest.fixture
def escena(display) -> pygame.Surface:
    """Un lienzo con dos fuentes de luz de colores distintos sobre fondo oscuro.

    Es la situación que produce la iluminación de F1.1: charcos brillantes
    sobre penumbra. Un lienzo de color uniforme no distinguiría un bloom
    correcto de uno invertido.
    """
    s = pygame.Surface((ANCHO, ALTO))
    s.fill(FONDO)
    pygame.draw.circle(s, (230, 215, 180), CENTRO_FOCO, RADIO_FOCO)
    pygame.draw.circle(s, (120, 255, 110), CENTRO_ESPORAS, 60)
    return s


def _aplicar(escena, vineta: float, bloom: float, fotogramas: int = 4) -> np.ndarray:
    """Aplica el post-procesado y devuelve los píxeles resultantes.

    Se corren varios fotogramas porque el halo se recalcula cada dos: con uno
    solo se mediría el estado inicial y no el de régimen.
    """
    p = PostProcessing()
    p.set_vignette(vineta)
    p.set_base_bloom(bloom)
    for _ in range(fotogramas):
        c = escena.copy()
        p.apply(c)
    return pygame.surfarray.array3d(c).astype(float)


class TestElBloomAclaraLasLucesYNoLasSombras:
    """F1.2a — estaba invertido, y ninguna prueba lo veía."""

    def test_el_centro_del_foco_se_aclara(self, escena):
        sin = _aplicar(escena, 0.0, 0.0)
        con = _aplicar(escena, 0.0, 0.22)
        antes = sin[CENTRO_FOCO].mean()
        despues = con[CENTRO_FOCO].mean()
        assert despues > antes + 10, (
            f"el foco pasa de {antes:.0f} a {despues:.0f}: el bloom no lo realza"
        )

    def test_el_fondo_oscuro_no_se_toca(self, escena):
        """La prueba que cazaba el defecto: el fondo subía de 43 a 239."""
        sin = _aplicar(escena, 0.0, 0.0)
        con = _aplicar(escena, 0.0, 0.22)
        lejos = (60, 500)
        antes = sin[lejos].mean()
        despues = con[lejos].mean()
        assert despues < antes + 3, (
            f"el fondo pasa de {antes:.0f} a {despues:.0f}: el bloom está "
            "sumando la escena entera en vez de sólo lo que brilla"
        )

    def test_las_luces_ganan_mas_que_las_sombras(self, escena):
        sin = _aplicar(escena, 0.0, 0.0)
        con = _aplicar(escena, 0.0, 0.22)
        gana_luz = con[CENTRO_FOCO].mean() - sin[CENTRO_FOCO].mean()
        gana_sombra = con[(60, 500)].mean() - sin[(60, 500)].mean()
        assert gana_luz > gana_sombra, (
            f"la luz gana {gana_luz:+.1f} y la sombra {gana_sombra:+.1f}: "
            "el efecto está invertido"
        )

    def test_mas_intensidad_da_mas_halo(self, escena):
        suave = _aplicar(escena, 0.0, 0.10)[CENTRO_FOCO].mean()
        fuerte = _aplicar(escena, 0.0, 0.40)[CENTRO_FOCO].mean()
        assert fuerte > suave

    def test_el_halo_conserva_el_color_de_lo_que_brilla(self, escena):
        """Unas esporas verdes tienen que irradiar verde, no gris."""
        sin = _aplicar(escena, 0.0, 0.0)
        con = _aplicar(escena, 0.0, 0.30)
        junto = (CENTRO_ESPORAS[0], CENTRO_ESPORAS[1] + 70)
        delta = con[junto] - sin[junto]
        assert delta[1] > delta[2], (
            f"el aporte del halo es {delta}: el verde debería dominar sobre el azul"
        )


class TestElHaloDesbordaLaSilueta:
    """Un halo con la forma exacta de la fuente no es un halo."""

    def test_la_luz_se_derrama_fuera_del_circulo(self, escena):
        sin = _aplicar(escena, 0.0, 0.0)
        con = _aplicar(escena, 0.0, 0.25)
        aportes = {}
        for fuera in (5, 20, 35):
            punto = (CENTRO_FOCO[0] + RADIO_FOCO + fuera, CENTRO_FOCO[1])
            aportes[fuera] = con[punto].mean() - sin[punto].mean()
        assert aportes[5] > 3.0, (
            f"a 5 px del borde el halo aporta {aportes[5]:+.1f}: no se derrama. "
            "Reducir y volver a ampliar no difumina; hace falta un desenfoque real"
        )
        assert aportes[5] >= aportes[35], (
            f"el halo no decae con la distancia: {aportes}"
        )

    def test_el_desenfoque_de_caja_ensancha_una_mancha(self):
        """El contrato del ayudante, aislado del resto del efecto."""
        mancha = np.zeros((40, 40, 3), dtype=np.float32)
        mancha[20, 20] = 255.0
        difuminada = PostProcessing._difuminar(mancha, 4).astype(float)
        assert difuminada[20, 20].max() > 0
        assert difuminada[24, 20].max() > 0, "la mancha no se ensanchó a 4 px"
        assert difuminada[35, 20].max() == 0, "se ensanchó más allá del radio pedido"

    def test_el_desenfoque_conserva_el_brillo_total(self):
        """Un desenfoque redistribuye la luz; no la crea ni la destruye."""
        imagen = np.zeros((60, 60, 3), dtype=np.float32)
        imagen[25:35, 25:35] = 200.0
        difuminada = PostProcessing._difuminar(imagen, 5).astype(np.float32)
        assert 0.7 < difuminada.sum() / imagen.sum() < 1.3, (
            f"el brillo total pasó de {imagen.sum():.0f} a {difuminada.sum():.0f}"
        )

    def test_el_desenfoque_no_oscurece_los_bordes(self):
        """Rellenar con ceros produciría un marco oscuro alrededor."""
        plano = np.full((40, 40, 3), 120.0, dtype=np.float32)
        difuminada = PostProcessing._difuminar(plano, 6)
        assert abs(int(difuminada[0, 0].mean()) - 120) <= 2, (
            f"la esquina vale {difuminada[0, 0].mean():.0f} y debería seguir en 120"
        )


class TestLaVinetaCierraElEncuadre:
    def test_las_esquinas_quedan_mas_oscuras_que_el_centro(self, escena):
        con = _aplicar(escena, 0.35, 0.0)
        centro = con[(400, 300)].mean()
        esquina = con[(8, 8)].mean()
        assert esquina < centro * 0.9, (
            f"esquina {esquina:.0f} frente a centro {centro:.0f}: no hay viñeta"
        )

    def test_a_cero_no_toca_la_imagen(self, escena):
        original = pygame.surfarray.array3d(escena).astype(float)
        con = _aplicar(escena, 0.0, 0.0)
        np.testing.assert_allclose(con, original, atol=1)

    def test_se_recorta_al_maximo_admitido(self):
        p = PostProcessing()
        p.set_vignette(10.0)
        assert p._vignette_strength <= 0.6
        p.set_vignette(-1.0)
        assert p._vignette_strength == 0.0


class TestElPostProcesadoCabeEnUnFotograma:
    """12 ms de 16,67 no es un efecto, es un problema."""

    PRESUPUESTO_MS = 1000.0 / 60.0

    def test_bloom_y_vineta_juntos_caben_holgadamente(self, escena):
        p = PostProcessing()
        p.set_vignette(0.35)
        p.set_base_bloom(0.25)
        for _ in range(4):                     # calentar cachés
            c = escena.copy()
            p.apply(c)
        t0 = time.perf_counter()
        for _ in range(120):
            c = escena.copy()
            p.apply(c)
        ms = (time.perf_counter() - t0) / 120 * 1000
        assert ms < self.PRESUPUESTO_MS * 0.5, (
            f"{ms:.2f} ms por fotograma, o el {ms / self.PRESUPUESTO_MS * 100:.0f} % "
            "del presupuesto, sólo en post-procesado"
        )

    def test_el_halo_se_reutiliza_entre_fotogramas(self, escena):
        """Recalcularlo a 60 Hz costaba el doble y no se distingue."""
        p = PostProcessing()
        p.set_base_bloom(0.25)
        c = escena.copy()
        p.apply(c)
        assert p._bloom_age == 0
        c = escena.copy()
        p.apply(c)
        assert p._bloom_age == 1, "el halo se recalculó en el segundo fotograma"

    def test_un_cambio_grande_de_intensidad_fuerza_el_recalculo(self, escena):
        """Reutilizar el halo de una intensidad distinta se vería como un salto."""
        p = PostProcessing()
        p.set_base_bloom(0.10)
        c = escena.copy()
        p.apply(c)
        p.set_base_bloom(0.60)
        c = escena.copy()
        p.apply(c)
        assert p._bloom_age == 0, "el halo no se actualizó al subir la intensidad"


class TestElEscenarioConfiguraElPostProcesadoDesdeElTmx:
    """F1.2 — como la luz: propiedad de mapa, tabla por zona, valor por defecto."""

    def test_el_cargador_lee_bloom_y_vineta(self):
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_unit_prop({}, "bloom", 0.0, 1.0) is None
        assert StageLoader._parse_unit_prop({"bloom": 0.4}, "bloom", 0.0, 1.0) == 0.4
        # Fuera de rango se recorta: quien escribe 5 quiere "mucho".
        assert StageLoader._parse_unit_prop({"bloom": 5}, "bloom", 0.0, 1.0) == 1.0
        assert StageLoader._parse_unit_prop({"vignette": 9}, "vignette", 0.0, 0.6) == 0.6
        assert StageLoader._parse_unit_prop({"bloom": -3}, "bloom", 0.0, 1.0) == 0.0

    def test_las_tablas_por_zona_cubren_las_cuatro_zonas(self):
        from src.framework.scenes.stage_scene import StageScene

        for zona in (0, 1, 2, 3):
            assert zona in StageScene.BLOOM_BY_ZONE
            assert zona in StageScene.VIGNETTE_BY_ZONE
        # La oscuridad y la viñeta tienen que crecer juntas: un nivel más
        # oscuro con un encuadre más abierto se ve incoherente.
        luces = [StageScene.AMBIENT_BY_ZONE[z] for z in (0, 1, 2, 3)]
        vinetas = [StageScene.VIGNETTE_BY_ZONE[z] for z in (0, 1, 2, 3)]
        assert luces == sorted(luces, reverse=True)
        assert vinetas == sorted(vinetas)
