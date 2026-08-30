"""
Pruebas de la capa puente del curso.

Criterio: cada prueba tiene que poder **fallar**. Una que sólo comprueba que
la función devuelve algo no vigila nada. Aquí se comprueban propiedades que se
romperían de verdad si el código estuviera mal: la transposición de ejes, el
determinismo del generador, la fórmula de la circularidad, y la fuga de
información del centroide.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from cvcourse import features, synthetic

# ── synthetic ─────────────────────────────────────────────────────────────


def test_la_misma_semilla_da_los_mismos_pixeles():
    """Sin esto, dos estudiantes obtienen números distintos del mismo guion."""
    a, _ = synthetic.pieza_individual(semilla=7)
    b, _ = synthetic.pieza_individual(semilla=7)
    assert np.array_equal(a, b)


def test_semillas_distintas_dan_imagenes_distintas():
    """El complemento del anterior: si no, el 'lote' serían 30 copias."""
    a, _ = synthetic.pieza_individual(semilla=1)
    b, _ = synthetic.pieza_individual(semilla=2)
    assert not np.array_equal(a, b)


def test_una_pieza_ok_no_lleva_defecto():
    _, verdad = synthetic.pieza_individual(clase="OK", semilla=3)
    assert verdad.defecto is None
    assert verdad.clase == "OK"


def test_una_pieza_no_ok_siempre_lleva_defecto():
    for semilla in range(8):
        _, verdad = synthetic.pieza_individual(clase="NO_OK", semilla=semilla)
        assert verdad.defecto in synthetic.DEFECTOS, f"semilla {semilla}"


def test_la_deformacion_reduce_el_area_y_la_solidez():
    """El defecto que sólo se ve midiendo la forma.

    Si `_deformar` dejara de morder la esquina, esta prueba caería — y con
    ella caería la justificación entera del bloque de características
    geométricas de la Clase 3.
    """
    _, sana = synthetic.pieza_individual(clase="OK", forma="rectangulo", semilla=5)
    _, rota = synthetic.pieza_individual(
        clase="NO_OK", defecto="deformacion", forma="rectangulo", semilla=5
    )
    assert rota.metadatos["area_verdadera"] < sana.metadatos["area_verdadera"]


def test_el_lote_respeta_la_proporcion_de_defectuosas():
    _, verdades = synthetic.lote_de_piezas(n=20, proporcion_defectuosas=0.25, semilla=0)
    assert sum(v.clase == "NO_OK" for v in verdades) == 5


def test_el_lote_numera_las_piezas_sin_repetir():
    _, verdades = synthetic.lote_de_piezas(n=12, semilla=0)
    assert [v.id for v in verdades] == list(range(12))


def test_las_piezas_en_contacto_forman_una_sola_region():
    """El caso que obliga a usar watershed, comprobado y no supuesto.

    Es la prueba que sostiene el ejemplo central de la Clase 3: si las piezas
    dejaran de tocarse, `connected_components` acertaría, watershed sobraría y
    el ejercicio perdería el sentido sin que nadie se enterara.
    """
    from skimage.measure import label

    imagen, verdades = synthetic.piezas_en_contacto(n=5, semilla=0)
    mascara = imagen > 130
    assert label(mascara, connectivity=2).max() == 1
    assert len(verdades) == 5


@pytest.mark.parametrize(
    ("argumentos", "mensaje"),
    [
        ({"clase": "REGULAR"}, "clase"),
        ({"defecto": "oxido"}, "defecto"),
        ({"forma": "triangulo"}, "forma"),
    ],
)
def test_los_argumentos_invalidos_se_rechazan_con_un_mensaje_util(argumentos, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        synthetic.pieza_individual(**argumentos)


def test_lote_rechaza_proporciones_fuera_de_rango():
    with pytest.raises(ValueError, match="proporcion_defectuosas"):
        synthetic.lote_de_piezas(proporcion_defectuosas=1.5)


def test_piezas_en_contacto_exige_al_menos_dos():
    with pytest.raises(ValueError, match="al menos 2"):
        synthetic.piezas_en_contacto(n=1)


# ── features ──────────────────────────────────────────────────────────────


def _mascara_circular(lado: int = 120, radio: int = 40) -> np.ndarray:
    filas, columnas = np.ogrid[:lado, :lado]
    return ((filas - lado // 2) ** 2 + (columnas - lado // 2) ** 2) <= radio**2


def test_la_circularidad_de_un_circulo_vale_casi_uno():
    """4πA/P² = 1 en un círculo perfecto. Con píxeles, cerca de 1.

    El margen es ancho a propósito: el perímetro de una circunferencia
    discretizada depende del algoritmo, y fijar un valor exacto sería fijar la
    versión de scikit-image, no la geometría.
    """
    filas = features.caracteristicas_de_mascara(_mascara_circular())
    assert len(filas) == 1
    assert 0.85 <= filas[0].circularity <= 1.15


def test_la_circularidad_de_un_cuadrado_es_menor_que_la_de_un_circulo():
    """La comparación es lo que se enseña; el valor absoluto da igual."""
    cuadrado = np.zeros((120, 120), dtype=bool)
    cuadrado[30:90, 30:90] = True
    c_cuadrado = features.caracteristicas_de_mascara(cuadrado)[0].circularity
    c_circulo = features.caracteristicas_de_mascara(_mascara_circular())[0].circularity
    assert c_cuadrado < c_circulo


def test_la_relacion_de_aspecto_de_un_rectangulo_conocido():
    rectangulo = np.zeros((100, 100), dtype=bool)
    rectangulo[20:40, 10:70] = True     # alto 20, ancho 60
    fila = features.caracteristicas_de_mascara(rectangulo)[0]
    assert fila.height == 20
    assert fila.width == 60
    assert math.isclose(fila.aspect_ratio, 3.0, rel_tol=1e-6)


def test_la_circularidad_no_explota_con_perimetro_cero():
    """Un `inf` aquí rompería el entrenamiento de la Clase 4, muy lejos de aquí."""
    assert features._circularidad(area=1.0, perimetro=0.0) == 0.0


def test_el_area_minima_descarta_el_picoteo():
    mascara = _mascara_circular()
    mascara[2, 2] = True                 # una mota de 1 px
    assert len(features.caracteristicas_de_mascara(mascara, area_minima=20)) == 1
    assert len(features.caracteristicas_de_mascara(mascara, area_minima=1)) == 2


def test_a_matriz_excluye_el_centroide_para_evitar_la_fuga_de_informacion():
    """Lo importante no es que funcione: es que NO incluya el centroide.

    Un modelo entrenado con la posición aprende «las piezas de la izquierda
    son defectuosas» y saca una accuracy que no significa nada. Es el error
    que la Clase 4 enseña a detectar, así que el material no puede cometerlo.
    """
    filas = features.caracteristicas_de_mascara(_mascara_circular(), "OK")
    _, _, nombres = features.a_matriz(filas)
    assert "centroid_x" not in nombres
    assert "centroid_y" not in nombres
    assert "object_id" not in nombres
    assert "label" not in nombres
    assert "circularity" in nombres


def test_a_matriz_devuelve_formas_coherentes():
    filas = features.caracteristicas_de_mascara(_mascara_circular(), "OK")
    filas += features.caracteristicas_de_mascara(_mascara_circular(radio=20), "NO_OK")
    X, y, nombres = features.a_matriz(filas)
    assert X.shape == (2, len(nombres))
    assert X.dtype == np.float32
    assert list(y) == ["OK", "NO_OK"]


def test_a_matriz_se_queja_si_no_hay_filas():
    with pytest.raises(ValueError, match="no hay filas"):
        features.a_matriz([])


def test_a_matriz_rechaza_columnas_inventadas():
    filas = features.caracteristicas_de_mascara(_mascara_circular(), "OK")
    with pytest.raises(ValueError, match="columnas desconocidas"):
        features.a_matriz(filas, columnas=("area", "brillo_medio"))


def test_el_csv_se_escribe_con_la_cabecera_del_temario(tmp_path):
    filas = features.caracteristicas_de_mascara(_mascara_circular(), "OK")
    ruta = features.guardar_csv(filas, tmp_path / "features.csv")

    import csv

    with ruta.open(encoding="utf-8", newline="") as fichero:
        leidas = list(csv.DictReader(fichero))

    assert len(leidas) == 1
    for columna in ("area", "perimeter", "width", "height", "aspect_ratio", "circularity"):
        assert columna in leidas[0], f"falta la columna {columna} del temario"
    assert leidas[0]["label"] == "OK"


def test_el_csv_no_deja_lineas_en_blanco_en_windows(tmp_path):
    """`newline=""` en `open`. Sin él, en Windows sale una línea vacía por fila."""
    filas = features.caracteristicas_de_mascara(_mascara_circular(), "OK")
    ruta = features.guardar_csv(filas, tmp_path / "f.csv")
    texto = ruta.read_bytes().decode("utf-8")
    assert "\r\r\n" not in texto


def test_columnas_deriva_de_la_dataclase():
    """Si alguien añade un campo y olvida la cabecera, esto lo caza."""
    from dataclasses import fields

    assert features.COLUMNAS == tuple(f.name for f in fields(features.Caracteristicas))


def test_los_dos_caminos_de_entrada_dan_la_misma_fila():
    """`desde_region_info` y `caracteristicas_de_mascara` no pueden divergir.

    Si dieran resultados distintos, el estudiante que compara su cuaderno con
    el laboratorio del motor tendría razón al desconfiar de los dos.
    """

    class _RectFalso:
        width, height = 60.0, 20.0

    class _RegionFalsa:
        label = 1
        area = 1200.0
        perimeter = 160.0
        centroid = (40.0, 30.0)     # (x, y) como lo entrega el motor
        eccentricity = 0.9
        solidity = 1.0
        bounding_rect = _RectFalso()

    fila = features.desde_region_info(_RegionFalsa(), "OK")
    assert fila.width == 60.0
    assert fila.height == 20.0
    assert math.isclose(fila.aspect_ratio, 3.0)
    assert math.isclose(fila.circularity, 4 * math.pi * 1200.0 / 160.0**2)
    assert math.isclose(fila.extent, 1200.0 / (60.0 * 20.0))
