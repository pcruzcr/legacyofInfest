"""
Module: test_edge_detection
System: tests
Academic Unit: VII

Sobel y Canny propios, contrastados contra OpenCV.

F2.3 — la auditoría de julio señaló que `FilterTools.sobel_edge` y
`canny_edge` llaman a `cv2`. Funcionan y son rápidas, pero en las Unidades VII
y VIII **el algoritmo es el contenido**: quien sólo ve `cv2.Canny(gray, 50,
150)` aprende una API. La implementación propia convierte el laboratorio de
demostración en lección.

Una implementación propia sin referencia contra la que medirla es un ejercicio
de fe. Aquí OpenCV es el oráculo: se le pide lo mismo y se compara. Y como los
dos pasos que la gente implementa mal —la supresión no máxima y la
histéresis— tienen propiedades comprobables por separado, cada uno tiene sus
pruebas además de la comparación global.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.framework.processing import edge_detection as ed

cv2 = pytest.importorskip("cv2", reason="OpenCV es el oráculo de estas pruebas")


def _imagen_de_prueba() -> np.ndarray:
    """Un cuadrado y un círculo sobre fondo liso, en (alto, ancho, 3).

    Formas geométricas y no ruido: los bordes esperados se conocen de
    antemano, así que un fallo se puede localizar mirando la imagen.
    """
    img = np.full((180, 240, 3), 40, np.uint8)
    img[40:140, 60:160] = 200
    yy, xx = np.mgrid[0:180, 0:240]
    img[((xx - 190) ** 2 + (yy - 60) ** 2) < 900] = 230
    return img


def _gris_cv(img: np.ndarray) -> np.ndarray:
    return (0.299 * img[..., 0] + 0.587 * img[..., 1]
            + 0.114 * img[..., 2]).astype(np.uint8)


class TestLosBloquesBasicos:
    def test_el_gris_usa_los_coeficientes_de_luma(self):
        blanco = np.full((4, 4, 3), 255, np.uint8)
        assert ed.a_gris(blanco).mean() == pytest.approx(255.0, abs=0.5)
        rojo = np.zeros((4, 4, 3), np.uint8)
        rojo[..., 0] = 255
        assert ed.a_gris(rojo).mean() == pytest.approx(255 * 0.299, abs=0.5)

    def test_el_gris_devuelve_flotantes(self):
        """En uint8 los pasos siguientes desbordarían en silencio (AUD-086)."""
        assert ed.a_gris(np.full((4, 4, 3), 200, np.uint8)).dtype == np.float32

    def test_la_convolucion_con_la_identidad_no_cambia_nada(self):
        imagen = np.arange(36, dtype=np.float32).reshape(6, 6)
        identidad = np.zeros((3, 3), np.float32)
        identidad[1, 1] = 1.0
        np.testing.assert_allclose(ed.convolucionar(imagen, identidad), imagen)

    def test_la_convolucion_replica_el_borde(self):
        """Rellenar con ceros inventaría un borde en el marco de la imagen."""
        plano = np.full((8, 8), 100.0, np.float32)
        bordes = ed.convolucionar(plano, ed.KERNEL_X)
        assert abs(bordes).max() < 1e-3, (
            "una imagen sin bordes produce bordes: el relleno está inventando "
            "un contorno artificial"
        )

    def test_la_convolucion_detecta_un_escalon_vertical(self):
        imagen = np.zeros((8, 8), np.float32)
        imagen[:, 4:] = 255.0
        respuesta = ed.convolucionar(imagen, ed.KERNEL_X)
        assert abs(respuesta[:, 3:5]).max() > 100, "no reacciona al escalón"
        assert abs(respuesta[:, 0]).max() < 1e-3, "reacciona lejos del escalón"

    def test_el_suavizado_conserva_el_brillo_medio(self):
        imagen = np.random.RandomState(0).rand(40, 40).astype(np.float32) * 255
        suave = ed.suavizar(imagen, 1.4)
        assert suave.mean() == pytest.approx(imagen.mean(), rel=0.02)
        assert suave.std() < imagen.std(), "suavizar tiene que reducir la varianza"

    def test_el_nucleo_gaussiano_suma_uno(self):
        for sigma in (0.5, 1.0, 1.4, 3.0):
            assert ed._gauss_1d(sigma).sum() == pytest.approx(1.0, abs=1e-5)


class TestSobelCoincideConOpenCV:
    def test_los_bordes_caen_en_los_mismos_pixeles(self):
        img = _imagen_de_prueba()
        propio = ed.sobel(img)
        gray = _gris_cv(img)
        referencia = cv2.convertScaleAbs(cv2.magnitude(
            cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3),
            cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)))
        coincidencia = ((propio > 60) == (referencia > 60)).mean()
        assert coincidencia > 0.99, (
            f"sólo coincide el {coincidencia:.1%} de los píxeles con OpenCV"
        )

    def test_una_imagen_lisa_no_tiene_bordes(self):
        assert ed.sobel(np.full((40, 40, 3), 128, np.uint8)).max() == 0

    def test_el_nucleo_x_responde_a_bordes_verticales(self):
        """El error de signo más frecuente al implementar Sobel."""
        vertical = np.zeros((16, 16, 3), np.uint8)
        vertical[:, 8:] = 255
        gris = ed.a_gris(vertical)
        gx = ed.convolucionar(gris, ed.KERNEL_X)
        gy = ed.convolucionar(gris, ed.KERNEL_Y)
        assert abs(gx).max() > abs(gy).max() * 10, (
            "un borde vertical tiene que responder sobre todo en X"
        )


class TestCannyHaceLoQuePrometeCadaPaso:
    def test_la_supresion_adelgaza_el_borde(self):
        """Sin este paso Canny daría manchas, no líneas."""
        img = _imagen_de_prueba()
        gris = ed.suavizar(ed.a_gris(img), 1.4)
        magnitud, angulo = ed.gradiente(gris)
        delgado = ed.supresion_no_maxima(magnitud, angulo)
        gruesos = (magnitud > 50).sum()
        finos = (delgado > 50).sum()
        assert finos < gruesos * 0.7, (
            f"el borde pasa de {gruesos} a {finos} píxeles: no se adelgazó"
        )

    def test_la_supresion_no_inventa_bordes(self):
        img = _imagen_de_prueba()
        gris = ed.suavizar(ed.a_gris(img), 1.4)
        magnitud, angulo = ed.gradiente(gris)
        delgado = ed.supresion_no_maxima(magnitud, angulo)
        assert (delgado <= magnitud + 1e-3).all(), (
            "la supresión devuelve valores mayores que la magnitud original"
        )

    def test_la_histeresis_conecta_lo_debil_con_lo_fuerte(self):
        """El punto entero del doble umbral.

        Se construye una línea con un tramo fuerte y otro débil pegado a él, y
        otro tramo débil aislado. El primero debe sobrevivir; el segundo, no.
        """
        delgado = np.zeros((20, 20), np.float32)
        delgado[10, 2:6] = 200.0    # tramo fuerte
        delgado[10, 6:10] = 80.0    # débil, pegado al fuerte
        delgado[10, 15:18] = 80.0   # débil, aislado
        salida = ed.histeresis(delgado, umbral_bajo=50, umbral_alto=150)
        assert salida[10, 3] > 0, "el tramo fuerte se perdió"
        assert salida[10, 7] > 0, "el tramo débil conectado no se propagó"
        assert salida[10, 16] == 0, (
            "el tramo débil aislado sobrevivió: la histéresis está aceptando "
            "cualquier cosa por encima del umbral bajo"
        )

    def test_la_histeresis_devuelve_una_imagen_binaria(self):
        delgado = np.random.RandomState(1).rand(30, 30).astype(np.float32) * 255
        salida = ed.histeresis(delgado, 50, 150)
        assert set(np.unique(salida)) <= {0, 255}

    def test_canny_coincide_con_opencv(self):
        img = _imagen_de_prueba()
        propio = ed.canny(img, 50, 150)
        referencia = cv2.Canny(_gris_cv(img), 50, 150)
        coincidencia = ((propio > 0) == (referencia > 0)).mean()
        assert coincidencia > 0.97, (
            f"sólo coincide el {coincidencia:.1%} de los píxeles con OpenCV"
        )

    def test_subir_los_umbrales_deja_menos_bordes(self):
        img = _imagen_de_prueba()
        permisivo = (ed.canny(img, 20, 60) > 0).sum()
        estricto = (ed.canny(img, 120, 220) > 0).sum()
        assert estricto < permisivo

    def test_una_imagen_lisa_no_da_bordes(self):
        assert ed.canny(np.full((40, 40, 3), 90, np.uint8)).max() == 0


class TestLaVersionPropiaConviveConLaDeOpenCV:
    """Las dos tienen que existir: comparar es parte de la lección."""

    @pytest.fixture
    def superficie(self):
        import pygame

        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 180))
        s = pygame.Surface((240, 180))
        s.fill((40, 40, 40))
        pygame.draw.rect(s, (200, 200, 200), (60, 40, 100, 100))
        return s

    def test_las_cuatro_funciones_existen(self):
        from src.framework.processing.filter_tools import FilterTools

        for nombre in ("sobel_edge", "canny_edge",
                       "sobel_edge_propio", "canny_edge_propio"):
            assert hasattr(FilterTools, nombre), f"falta {nombre}"

    def test_las_dos_versiones_dan_el_mismo_tamano_y_orientacion(self, superficie):
        """La transposición numpy/surfarray es un fallo silencioso clásico."""
        import pygame

        from src.framework.processing.filter_tools import FilterTools

        a = FilterTools.sobel_edge(superficie)
        b = FilterTools.sobel_edge_propio(superficie)
        assert a.get_size() == b.get_size() == superficie.get_size()
        ma = pygame.surfarray.array3d(a)[..., 0] > 60
        mb = pygame.surfarray.array3d(b)[..., 0] > 60
        assert (ma == mb).mean() > 0.99, (
            "las dos versiones no coinciden: probablemente una está girada 90 "
            "grados respecto a la otra"
        )

    def test_la_version_propia_valida_los_umbrales_igual(self, superficie):
        from src.framework.processing.filter_tools import FilterTools

        with pytest.raises(ValueError):
            FilterTools.canny_edge_propio(superficie, 200, 100)
        with pytest.raises(ValueError):
            FilterTools.canny_edge_propio(superficie, 0, 100)

    def test_la_version_propia_es_mas_lenta_y_eso_es_la_leccion(self):
        """No es un fallo: es el dato que hace útil la comparación.

        Si la implementación propia llegara a ser más rápida que OpenCV, o
        estaría mal, o alguien habría cambiado la de referencia por otra cosa.
        En los dos casos conviene enterarse.
        """
        import time

        img = _imagen_de_prueba()
        gris = _gris_cv(img)

        ed.canny(img)                      # calentar
        t0 = time.perf_counter()
        for _ in range(5):
            ed.canny(img)
        propio = (time.perf_counter() - t0) / 5

        t0 = time.perf_counter()
        for _ in range(5):
            cv2.Canny(gris, 50, 150)
        opencv = (time.perf_counter() - t0) / 5

        assert propio > opencv, (
            f"la versión propia ({propio * 1000:.2f} ms) no es más lenta que "
            f"OpenCV ({opencv * 1000:.3f} ms); algo no cuadra"
        )
        # Y no tanto como para que el laboratorio deje de ser interactivo.
        assert propio < 0.25, (
            f"{propio * 1000:.0f} ms por imagen: demasiado para enseñarlo en vivo"
        )
