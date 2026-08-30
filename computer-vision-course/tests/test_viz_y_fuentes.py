"""
Pruebas de `viz` y `acquisition`.

Las figuras no se comparan píxel a píxel —eso ataría la suite a la versión de
Matplotlib y fallaría en cada actualización sin que nada estuviera roto—, sino
por su estructura: cuántos ejes hay, qué se dibujó, y que los errores de uso
se rechacen con un mensaje que sirva para algo.
"""
from __future__ import annotations

import numpy as np
import pytest

from cvcourse import acquisition, synthetic, viz

# ── viz ───────────────────────────────────────────────────────────────────


@pytest.fixture
def imagen_gris() -> np.ndarray:
    return synthetic.pieza_individual(semilla=0)[0]


@pytest.fixture
def imagen_color() -> np.ndarray:
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, size=(48, 64, 3), dtype=np.uint8)


def test_la_rejilla_crea_un_eje_por_imagen(imagen_gris):
    figura = viz.rejilla([imagen_gris] * 6, columnas=3)
    assert len(figura.axes) == 6      # 2 filas × 3 columnas, todas ocupadas


def test_la_rejilla_apaga_las_celdas_sobrantes(imagen_gris):
    """5 imágenes en 3 columnas dejan una celda vacía en la última fila."""
    figura = viz.rejilla([imagen_gris] * 5, columnas=3)
    assert len(figura.axes) == 6
    assert not figura.axes[-1].axison


def test_la_rejilla_exige_tantos_titulos_como_imagenes(imagen_gris):
    with pytest.raises(ValueError, match="tienen que coincidir"):
        viz.rejilla([imagen_gris, imagen_gris], titulos=["sólo uno"])


def test_la_rejilla_se_queja_si_no_hay_imagenes():
    with pytest.raises(ValueError, match="no hay imágenes"):
        viz.rejilla([])


def test_las_imagenes_en_gris_se_dibujan_con_escala_fija(imagen_gris):
    """`vmin=0, vmax=255`.

    Sin fijarlo, Matplotlib normaliza cada imagen a su propio rango: una
    imagen oscura y una clara salen idénticas en pantalla y la comparación
    'antes/después' —que es el ejercicio— deja de mostrar nada.
    """
    figura = viz.rejilla([imagen_gris])
    assert figura.axes[0].images[0].get_clim() == (0, 255)


def test_el_histograma_en_color_dibuja_los_tres_canales(imagen_color):
    figura = viz.histograma(imagen_color, con_imagen=False)
    leyenda = [t.get_text() for t in figura.axes[0].get_legend().get_texts()]
    assert leyenda == ["red", "green", "blue"]


def test_el_histograma_con_imagen_tiene_dos_ejes(imagen_gris):
    assert len(viz.histograma(imagen_gris, con_imagen=True).axes) == 2


def test_la_matriz_de_confusion_escribe_los_numeros_dentro():
    matriz = np.array([[5, 1], [2, 7]])
    figura = viz.matriz_de_confusion(matriz, ["OK", "NO_OK"])
    textos = {t.get_text() for t in figura.axes[0].texts}
    assert {"5", "1", "2", "7"}.issubset(textos)


def test_la_matriz_normalizada_no_produce_nan_con_una_clase_vacia():
    """Una clase sin ejemplos en el test daría 0/0 y se dibujaría como un hueco."""
    matriz = np.array([[4, 0], [0, 0]])
    figura = viz.matriz_de_confusion(matriz, ["OK", "NO_OK"], normalizar=True)
    textos = [t.get_text() for t in figura.axes[0].texts]
    assert "nan" not in textos


def test_la_matriz_de_confusion_exige_ser_cuadrada():
    with pytest.raises(ValueError, match="cuadrada"):
        viz.matriz_de_confusion(np.zeros((2, 3)), ["a", "b"])


def test_la_matriz_de_confusion_exige_tantas_clases_como_filas():
    with pytest.raises(ValueError, match="clases"):
        viz.matriz_de_confusion(np.zeros((2, 2)), ["a", "b", "c"])


def test_la_nube_de_caracteristicas_pinta_una_serie_por_clase():
    X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], dtype=np.float32)
    y = np.array(["OK", "NO_OK", "OK"], dtype=object)
    figura = viz.nube_de_caracteristicas(X, y, ("area", "circularity"), "area", "circularity")
    assert len(figura.axes[0].collections) == 2


def test_la_nube_rechaza_un_eje_que_no_existe():
    X = np.zeros((2, 2), dtype=np.float32)
    y = np.array(["a", "b"], dtype=object)
    with pytest.raises(ValueError, match="no están en"):
        viz.nube_de_caracteristicas(X, y, ("area", "circularity"), "area", "brillo")


def test_guardar_escribe_el_fichero_y_cierra_la_figura(tmp_path, imagen_gris):
    """Cerrarla no es cosmética: cuarenta figuras abiertas se comen un portátil."""
    import matplotlib.pyplot as plt

    figura = viz.rejilla([imagen_gris])
    ruta = viz.guardar(figura, tmp_path / "sub" / "figura.png")
    assert ruta.exists() and ruta.stat().st_size > 0
    assert figura.number not in plt.get_fignums()


# ── acquisition ───────────────────────────────────────────────────────────


def test_la_fuente_sintetica_entrega_rgb_uint8():
    """Contrato de `Fuente`: RGB, (alto, ancho, 3), uint8. Sin excepciones."""
    with acquisition.FuenteSintetica(n=3, tamano=64) as fuente:
        imagen = fuente.leer()
    assert imagen is not None
    assert imagen.shape == (64, 64, 3)
    assert imagen.dtype == np.uint8


def test_la_fuente_se_agota_y_devuelve_none():
    fuente = acquisition.FuenteSintetica(n=2)
    assert fuente.leer() is not None
    assert fuente.leer() is not None
    assert fuente.leer() is None


def test_la_fuente_es_iterable():
    """El patrón `for imagen in fuente` es el que usa todo el material."""
    with acquisition.FuenteSintetica(n=4) as fuente:
        assert len(list(fuente)) == 4


def test_leer_devuelve_copias_y_no_la_imagen_interna():
    """Si devolviera la interna, un ejemplo que la modifica in situ
    contaminaría la siguiente lectura y el fallo aparecería a tres celdas."""
    fuente = acquisition.FuenteSintetica(n=2)
    primera = fuente.leer()
    primera[:] = 0
    assert fuente._imagenes[0].any()


def test_la_fuente_archivo_se_queja_de_una_ruta_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        acquisition.FuenteArchivo(tmp_path / "no_existe.png")


def test_la_fuente_carpeta_ordena_las_rutas(tmp_path):
    """`glob` no garantiza orden; 'la tercera imagen' tiene que ser la misma
    en las treinta máquinas del aula o el laboratorio no se puede corregir."""
    import cv2

    for nombre in ("c.png", "a.png", "b.png"):
        cv2.imwrite(str(tmp_path / nombre), np.zeros((8, 8, 3), dtype=np.uint8))
    fuente = acquisition.FuenteCarpeta(tmp_path)
    assert [r.name for r in fuente.rutas] == ["a.png", "b.png", "c.png"]


def test_la_fuente_carpeta_ignora_lo_que_no_sea_imagen(tmp_path):
    import cv2

    cv2.imwrite(str(tmp_path / "a.png"), np.zeros((8, 8, 3), dtype=np.uint8))
    (tmp_path / "notas.txt").write_text("esto no es una imagen", encoding="utf-8")
    assert len(acquisition.FuenteCarpeta(tmp_path).rutas) == 1


def test_la_fuente_carpeta_lee_en_rgb(tmp_path):
    """OpenCV lee BGR. Si la conversión faltara, el rojo saldría azul —y un
    histograma con los canales cambiados no falla: miente."""
    import cv2

    azul_en_bgr = np.zeros((8, 8, 3), dtype=np.uint8)
    azul_en_bgr[:, :, 0] = 255                     # canal B de OpenCV
    cv2.imwrite(str(tmp_path / "a.png"), azul_en_bgr)

    imagen = acquisition.FuenteCarpeta(tmp_path).leer()
    assert imagen is not None
    assert imagen[0, 0, 2] == 255 and imagen[0, 0, 0] == 0   # azul en RGB


def test_la_fuente_carpeta_rechaza_lo_que_no_es_carpeta(tmp_path):
    fichero = tmp_path / "x.png"
    fichero.write_bytes(b"")
    with pytest.raises(NotADirectoryError):
        acquisition.FuenteCarpeta(fichero)


def test_mejor_fuente_disponible_siempre_encuentra_la_sintetica():
    """La red de seguridad: Colab sin cámara, sin motor y sin datos."""
    with acquisition.mejor_fuente_disponible(("sintetica",)) as fuente:
        assert fuente.leer() is not None


def test_mejor_fuente_disponible_deja_constancia_de_cual_uso():
    """Degradar en silencio sería peor que fallar: el estudiante creería
    estar analizando su webcam mientras mira piezas sintéticas."""
    with acquisition.mejor_fuente_disponible(("camara", "sintetica")) as fuente:
        assert "camara" in fuente.nombre or "sintetica" in fuente.nombre


def test_mejor_fuente_disponible_rechaza_preferencias_inventadas():
    with pytest.raises(ValueError, match="preferencias desconocidas"):
        acquisition.mejor_fuente_disponible(("telepatia",))


def test_mejor_fuente_disponible_avisa_si_no_queda_ninguna(monkeypatch):
    monkeypatch.setattr(acquisition.FuenteCamara, "disponible", classmethod(lambda cls, i=0: False))
    with pytest.raises(RuntimeError, match="ninguna de las fuentes"):
        acquisition.mejor_fuente_disponible(("camara",))
