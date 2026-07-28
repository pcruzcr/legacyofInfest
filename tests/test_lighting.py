"""
Module: test_lighting
System: tests
Academic Unit: VI

El sistema de iluminación no había iluminado un solo píxel.

Estaba instanciado, cableado, actualizándose cada fotograma y con tres focos
activos en Stage 0. Y era completamente inerte: `build_gradient` calculaba el
color del disco así::

    val = (intensidad * caída * 255).astype(np.uint8)
    arr[:, :, 0] = (val * color[0] / 255).astype(np.uint8)

`val` es `uint8` y `color[0]` llega a 255, que **también cabe en un uint8**.
NumPy conserva el tipo pequeño y el producto desborda en silencio: para el
píxel central, ``216 * 255 mod 256 = 40``, dividido entre 255 da 0,157, y
convertido a entero da **0**. Todos los focos eran discos negros y
transparentes.

Ninguna prueba lo detectaba porque todas preguntaban por la *estructura* —¿se
añadió el foco a la lista?, ¿tiene el radio correcto?— y ninguna miraba los
píxeles. Las de aquí miran los píxeles.

* **AUD-086** — el gradiente tiene que ser más brillante en el centro.
* **AUD-087** — el parpadeo cambia radio *e intensidad*; sólo el radio contaba.
* **F1.1** — los focos vienen del TMX, no de una tabla escrita en el motor.
"""
from __future__ import annotations

import numpy as np
import pygame
import pytest

from src.framework.vfx.lighting import LightSource, LightSystem


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 180))
    yield pygame.display.get_surface()


def _rgb(superficie: pygame.Surface) -> np.ndarray:
    return pygame.surfarray.array3d(superficie).astype(float)


class TestElFocoIluminaDeVerdad:
    """AUD-086 — la prueba que faltaba: mirar los píxeles."""

    def test_el_centro_del_gradiente_no_es_negro(self, display):
        foco = LightSource(pygame.Vector2(0, 0), radius=64,
                           color=(255, 220, 180), intensity=0.85)
        g = foco.get_cached_gradient()
        centro = pygame.surfarray.array3d(g)[64, 64]
        assert centro.max() > 100, (
            f"el centro del foco es {tuple(centro)}: el disco de luz está negro"
        )

    def test_el_gradiente_decae_del_centro_al_borde(self, display):
        foco = LightSource(pygame.Vector2(0, 0), radius=64,
                           color=(255, 255, 255), intensity=1.0)
        g = pygame.surfarray.array3d(foco.get_cached_gradient()).astype(float)
        centro = g[64, 64].mean()
        medio = g[96, 64].mean()      # a media distancia
        borde = g[127, 64].mean()     # justo dentro del radio
        assert centro > medio > borde, (
            f"la caída no es monótona: centro={centro:.0f} medio={medio:.0f} "
            f"borde={borde:.0f}"
        )
        assert borde < 20, f"el borde del foco debería apagarse, vale {borde:.0f}"

    def test_el_color_del_foco_llega_al_gradiente(self, display):
        """Un foco tóxico tiene que salir verde, no gris."""
        foco = LightSource(pygame.Vector2(0, 0), radius=48,
                           color=(150, 255, 130), intensity=1.0)
        r, g, b = pygame.surfarray.array3d(foco.get_cached_gradient())[48, 48]
        assert g > r and g > b, f"el centro es ({r},{g},{b}); el verde no domina"

    @pytest.mark.parametrize("intensidad", [0.25, 0.5, 0.75, 1.0])
    def test_mas_intensidad_da_mas_brillo(self, display, intensidad):
        base = LightSource(pygame.Vector2(0, 0), radius=48,
                           color=(255, 255, 255), intensity=0.1)
        alto = LightSource(pygame.Vector2(0, 0), radius=48,
                           color=(255, 255, 255), intensity=intensidad)
        cb = pygame.surfarray.array3d(base.get_cached_gradient())[48, 48].mean()
        ca = pygame.surfarray.array3d(alto.get_cached_gradient())[48, 48].mean()
        assert ca > cb, f"intensidad {intensidad} no supera a 0.1 ({ca} vs {cb})"

    def test_la_aritmetica_no_desborda_en_ningun_color(self, display):
        """El fallo aparecía justo con los canales a 255. Se prueban los extremos."""
        for color in [(255, 255, 255), (255, 0, 0), (0, 255, 0),
                      (0, 0, 255), (255, 220, 180), (1, 1, 1)]:
            foco = LightSource(pygame.Vector2(0, 0), radius=32,
                               color=color, intensity=1.0)
            centro = pygame.surfarray.array3d(foco.get_cached_gradient())[32, 32]
            esperado = max(color)
            assert centro.max() >= esperado - 8, (
                f"color {color}: el centro da {tuple(centro)} y debería acercarse "
                f"a {esperado} — la multiplicación está desbordando"
            )


class TestLaEscenaQuedaConCharcosDeLuz:
    """Iluminar es crear diferencia. Oscurecer todo por igual no es iluminar."""

    @staticmethod
    def _escena_iluminada(ambiente: float, con_foco: bool) -> np.ndarray:
        sistema = LightSystem(ambient_brightness=ambiente)
        if con_foco:
            sistema.add_light(LightSource(
                pygame.Vector2(160, 90), radius=60,
                color=(255, 220, 180), intensity=0.9))
        lienzo = pygame.Surface((320, 180))
        lienzo.fill((200, 200, 200))
        sistema.render(lienzo, pygame.Vector2(0, 0))
        return _rgb(lienzo)

    def test_bajo_el_foco_hay_mas_luz_que_lejos(self, display):
        a = self._escena_iluminada(0.45, con_foco=True)
        centro = a[160, 90].mean()
        lejos = a[10, 10].mean()
        assert centro > lejos * 1.4, (
            f"bajo el foco hay {centro:.0f} y lejos {lejos:.0f}: no hay charco de luz"
        )

    def test_sin_focos_el_ambiente_oscurece_de_forma_uniforme(self, display):
        a = self._escena_iluminada(0.45, con_foco=False)
        assert a.std() < 1.0, "sin focos la imagen debería quedar plana"
        assert 85 < a.mean() < 95, f"200 x 0.45 ≈ 90, se obtuvo {a.mean():.0f}"

    def test_el_ambiente_a_uno_no_toca_la_imagen(self, display):
        sistema = LightSystem(ambient_brightness=1.0)
        lienzo = pygame.Surface((320, 180))
        lienzo.fill((200, 200, 200))
        antes = _rgb(lienzo).copy()
        sistema.render(lienzo, pygame.Vector2(0, 0))
        np.testing.assert_allclose(_rgb(lienzo), antes, atol=1)

    def test_el_foco_se_mueve_con_la_camara(self, display):
        sistema = LightSystem(ambient_brightness=0.4)
        sistema.add_light(LightSource(pygame.Vector2(160, 90), radius=50,
                                      color=(255, 255, 255), intensity=0.9))
        a = pygame.Surface((320, 180))
        a.fill((200, 200, 200))
        sistema.render(a, pygame.Vector2(0, 0))
        b = pygame.Surface((320, 180))
        b.fill((200, 200, 200))
        sistema.render(b, pygame.Vector2(80, 0))
        # Con la cámara desplazada 80 px, el charco cae 80 px a la izquierda.
        assert _rgb(b)[80, 90].mean() > _rgb(b)[160, 90].mean()


class TestElParpadeoSeNota:
    """AUD-087 — la intensidad parpadeaba y el gradiente no se enteraba."""

    def test_el_gradiente_cambia_a_lo_largo_del_parpadeo(self, display):
        foco = LightSource(pygame.Vector2(0, 0), radius=50,
                           color=(255, 255, 255), intensity=0.8,
                           flicker=True, flicker_speed=6.0, flicker_amount=0.4)
        brillos = []
        for _ in range(40):
            foco.update(1 / 60)
            g = foco.get_cached_gradient()
            centro = g.get_size()[0] // 2
            brillos.append(float(pygame.surfarray.array3d(g)[centro, centro].mean()))
        assert max(brillos) - min(brillos) > 5, (
            f"el brillo del centro apenas varía ({min(brillos):.0f}–"
            f"{max(brillos):.0f}): el parpadeo de intensidad no llega al dibujo"
        )

    def test_la_intensidad_sola_basta_para_reconstruir(self, display):
        """La prueba anterior pasaba por el camino equivocado.

        Un foco con parpadeo cambia radio **e** intensidad, y el radio ya
        bastaba para disparar la reconstrucción: al quitar la comprobación de
        intensidad, `test_el_gradiente_cambia_a_lo_largo_del_parpadeo` seguía
        en verde. Aquí se congela el radio para que la única causa posible de
        cambio sea la intensidad.
        """
        foco = LightSource(pygame.Vector2(0, 0), radius=50,
                           color=(255, 255, 255), intensity=0.8,
                           flicker=True, flicker_speed=6.0, flicker_amount=0.4)
        foco.get_current_radius = lambda: 50.0          # radio inmóvil

        brillos = []
        for _ in range(40):
            foco.update(1 / 60)
            g = foco.get_cached_gradient()
            brillos.append(float(pygame.surfarray.array3d(g)[50, 50].mean()))
        assert max(brillos) - min(brillos) > 5, (
            f"con el radio congelado el brillo no varía ({min(brillos):.0f}–"
            f"{max(brillos):.0f}): el cambio de intensidad no reconstruye el disco"
        )

    def test_sin_parpadeo_el_gradiente_es_estable(self, display):
        foco = LightSource(pygame.Vector2(0, 0), radius=50,
                           color=(255, 255, 255), intensity=0.8)
        primero = foco.get_cached_gradient()
        for _ in range(40):
            foco.update(1 / 60)
        assert foco.get_cached_gradient() is primero, (
            "sin parpadeo no hay motivo para reconstruir el disco cada fotograma"
        )


class TestLosFocosVienenDelMapa:
    """F1.1 — antes estaban escritos en el motor, con coordenadas fijas.

    La versión anterior decidía la iluminación con una cadena
    ``if zone == 0: ... elif zone == 1: ...`` que además **creaba los focos**
    en (80, 80) y (240, 80). Un estudiante que construyera su escenario en
    Tiled heredaba esos dos focos estuviera ahí su nivel o no, y no tenía
    ninguna forma de colocar uno propio.
    """

    def test_stage0_declara_sus_focos_en_el_tmx(self):
        import xml.etree.ElementTree as ET
        from pathlib import Path

        raiz = ET.parse(
            Path(__file__).resolve().parent.parent
            / "assets" / "maps" / "stage0" / "stage0.tmx").getroot()
        luces = [o for o in raiz.iter("object")
                 if (o.get("type") or o.get("class")) == "Light"]
        assert len(luces) >= 4, (
            f"stage0 declara {len(luces)} focos; el escenario de referencia "
            "tiene que enseñar a usar la característica"
        )

    def test_el_cargador_convierte_los_objetos_light_en_especificaciones(self):
        from src.framework.stage.stage_loader import StageData, StageLoader

        stage = StageData(map_layer=None)          # sólo se usa el acumulador

        class _Obj:
            x, y, width, height = 100.0, 200.0, 16.0, 16.0

        StageLoader._handle_light(stage, _Obj(), {
            "radius": 120.0, "color": "toxic", "intensity": 0.6,
            "flicker": True, "flicker_speed": 3.0, "flicker_amount": 0.2,
        })
        assert len(stage.lights) == 1
        spec = stage.lights[0]
        # El punto de luz es el centro del rectángulo, no su esquina.
        assert spec.position == (108.0, 208.0)
        assert spec.radius == 120.0
        assert spec.color == StageLoader.LIGHT_COLORS["toxic"]
        assert spec.flicker is True

    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("warm", (255, 220, 180)),
            ("FIRE", (255, 120, 50)),
            ("#ff8000", (255, 128, 0)),
            ("#ccff8000", (255, 128, 0)),   # formato #aarrggbb de Tiled
            ("no_existe", (255, 220, 180)),  # cae al cálido, no revienta
            (None, (255, 220, 180)),
        ],
    )
    def test_los_colores_se_interpretan_o_caen_al_calido(self, entrada, esperado):
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_light_color(entrada) == esperado

    def test_un_radio_absurdo_no_rompe_la_carga(self):
        from src.framework.stage.stage_loader import StageData, StageLoader

        class _Obj:
            x, y, width, height = 0.0, 0.0, 0.0, 0.0

        for radio in (0, -50):
            stage = StageData(map_layer=None)
            StageLoader._handle_light(stage, _Obj(), {"radius": radio})
            assert stage.lights[0].radius > 0

    def test_el_ambiente_del_tmx_manda_sobre_la_tabla_por_zona(self):
        from src.framework.stage.stage_loader import StageLoader

        assert StageLoader._parse_ambient_light({}) is None
        assert StageLoader._parse_ambient_light({"ambient_light": 0.3}) == 0.3
        # Fuera de rango se recorta en vez de rechazarse: el estudiante que
        # escribe 2 quiere "muy iluminado".
        assert StageLoader._parse_ambient_light({"ambient_light": 2.0}) == 1.0
        assert StageLoader._parse_ambient_light({"ambient_light": -1.0}) == 0.0
