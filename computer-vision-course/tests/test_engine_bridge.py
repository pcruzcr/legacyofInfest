"""
Pruebas del puente al motor.

Todo lo de aquí necesita el repositorio del motor; en Colab se salta entero.
La prueba que más valor tiene es la de la transposición de ejes: es un fallo
que no lanza excepción, no se ve en imágenes cuadradas —que son casi todos los
sprites— y sólo se manifiesta en que Sobel encuentra los bordes girados 90°.
"""
from __future__ import annotations

import numpy as np
import pytest

from cvcourse import engine_bridge

pytestmark = pytest.mark.skipif(
    not engine_bridge.hay_motor(),
    reason="sin el repositorio del motor (Colab)",
)


def test_encuentra_la_raiz_del_repositorio():
    raiz = engine_bridge.raiz_del_repositorio()
    assert (raiz / "src" / "engine").is_dir()
    assert (raiz / "assets").is_dir()


def test_iniciar_pygame_headless_es_idempotente():
    engine_bridge.iniciar_pygame_headless()
    engine_bridge.iniciar_pygame_headless()

    import pygame

    assert pygame.get_init()
    assert pygame.display.get_surface() is not None


def test_superficie_a_array_devuelve_alto_ancho_y_no_ancho_alto():
    """El fallo silencioso que justifica este módulo entero.

    `pygame.surfarray.array3d` entrega (ancho, alto, 3); NumPy, OpenCV,
    scikit-image y Matplotlib trabajan en (alto, ancho). Con una superficie
    **rectangular** la diferencia es visible; con una cuadrada —el 90 % de los
    sprites— no se nota hasta que los bordes salen girados.
    """
    engine_bridge.iniciar_pygame_headless()
    import pygame

    superficie = pygame.Surface((64, 32))     # ancho 64, alto 32
    arreglo = engine_bridge.superficie_a_array(superficie)
    assert arreglo.shape == (32, 64, 3), "ejes transpuestos"


def test_superficie_a_array_conserva_el_color_en_su_sitio():
    """Comprueba la orientación, no sólo la forma.

    Una transposición mal hecha en una imagen cuadrada pasa el test de forma
    y falla este: el píxel pintado se movería a la posición espejo.
    """
    engine_bridge.iniciar_pygame_headless()
    import pygame

    superficie = pygame.Surface((32, 32))
    superficie.fill((0, 0, 0))
    superficie.set_at((10, 3), (255, 0, 0))    # pygame: (x=10, y=3)

    arreglo = engine_bridge.superficie_a_array(superficie)
    assert tuple(arreglo[3, 10]) == (255, 0, 0), "fila/columna intercambiadas"


def test_la_conversion_es_reversible():
    engine_bridge.iniciar_pygame_headless()
    rng = np.random.default_rng(0)
    original = rng.integers(0, 256, size=(24, 40, 3), dtype=np.uint8)
    ida_y_vuelta = engine_bridge.superficie_a_array(
        engine_bridge.array_a_superficie(original)
    )
    assert np.array_equal(original, ida_y_vuelta)


def test_array_a_superficie_acepta_una_imagen_en_gris():
    """Las máscaras y los resultados de Sobel salen en 2D; dibujarlos es
    la mitad de los laboratorios."""
    engine_bridge.iniciar_pygame_headless()
    gris = np.full((16, 24), 128, dtype=np.uint8)
    superficie = engine_bridge.array_a_superficie(gris)
    assert superficie.get_size() == (24, 16)     # pygame devuelve (ancho, alto)


def test_array_a_superficie_recorta_en_lugar_de_desbordar():
    """Un resultado de convolución sale en float y con valores fuera de [0,255].
    Sin recorte, el uint8 daría la vuelta y un borde brillante saldría negro."""
    engine_bridge.iniciar_pygame_headless()
    fuera_de_rango = np.array([[[300.0, -20.0, 128.0]]], dtype=np.float64)
    superficie = engine_bridge.array_a_superficie(fuera_de_rango)
    assert superficie.get_at((0, 0))[:3] == (255, 0, 128)


def test_recursos_encuentra_los_sprites_del_motor():
    rutas = engine_bridge.recursos("sprites")
    assert len(rutas) > 0
    assert all(r.suffix == ".png" for r in rutas)


def test_recursos_devuelve_las_rutas_ordenadas():
    rutas = engine_bridge.recursos("sprites")
    assert rutas == sorted(rutas)


def test_recursos_rechaza_una_categoria_inventada():
    with pytest.raises(ValueError, match="categoría desconocida"):
        engine_bridge.recursos("texturas_3d")


def test_cargar_imagen_devuelve_rgb_del_tamano_pedido():
    ruta = engine_bridge.raiz_del_repositorio() / "assets/sprites/player/player_idle.png"
    imagen = engine_bridge.cargar_imagen(ruta, tamano=(48, 32))
    assert imagen.shape == (32, 48, 3)          # (alto, ancho, 3)
    assert imagen.dtype == np.uint8


def test_cargar_imagen_acepta_una_ruta_relativa_al_repositorio():
    imagen = engine_bridge.cargar_imagen("assets/sprites/player/player_idle.png")
    assert imagen.ndim == 3


def test_cargar_imagen_dice_qué_fichero_falta(tmp_path):
    with pytest.raises(FileNotFoundError, match="no existe el recurso"):
        engine_bridge.cargar_imagen(tmp_path / "fantasma.png")


# ── captura de escenas reales ─────────────────────────────────────────────


@pytest.mark.parametrize("clave", ["filter", "vision", "pattern"])
def test_captura_las_tres_escenas_del_taller(clave):
    """Cierra el hueco H2: el motor tenía una fuente 'Live Capture
    (unavailable)' que era un rectángulo gris. Estos fotogramas son reales."""
    fotogramas = engine_bridge.capturar_escena(clave, fotogramas=1)
    assert len(fotogramas) == 1
    assert fotogramas[0].shape == (600, 800, 3)
    assert fotogramas[0].dtype == np.uint8


def test_el_fotograma_capturado_tiene_contenido_dibujado():
    """Si la escena no dibujara, saldría el color de fondo uniforme.

    Es la diferencia entre 'la captura no reventó' y 'la captura sirve': una
    imagen de un solo color pasaría cualquier comprobación de forma y no
    valdría para ningún laboratorio.
    """
    fotograma = engine_bridge.capturar_escena("filter", fotogramas=1)[0]
    assert len(np.unique(fotograma.reshape(-1, 3), axis=0)) > 8


def test_capturar_varios_fotogramas_devuelve_esa_cantidad():
    assert len(engine_bridge.capturar_escena("vision", fotogramas=3)) == 3


def test_capturar_una_escena_inexistente_lista_las_disponibles():
    with pytest.raises(ValueError, match="escena desconocida"):
        engine_bridge.capturar_escena("unidad_x")


def test_capturar_exige_al_menos_un_fotograma():
    with pytest.raises(ValueError, match="fotogramas debe ser"):
        engine_bridge.capturar_escena("filter", fotogramas=0)
