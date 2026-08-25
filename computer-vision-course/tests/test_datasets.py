"""
Pruebas del generador de datasets.

No se regenera el conjunto completo aquí —tarda y ya lo hace `--check`—, sino
las propiedades que, si se rompieran, arruinarían un laboratorio sin lanzar
ninguna excepción: el recorte de las hojas de animación, el descarte de
fotogramas vacíos y la coherencia del CSV de verdad-terreno.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

RAIZ_DEL_CURSO = Path(__file__).resolve().parent.parent
if str(RAIZ_DEL_CURSO / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ_DEL_CURSO / "scripts"))

import build_datasets

from cvcourse import engine_bridge


def _hoja(ancho: int, alto: int, ruta: Path, opaca: bool = True) -> Path:
    datos = np.zeros((alto, ancho, 4), dtype=np.uint8)
    if opaca:
        datos[..., :3] = 200
        datos[..., 3] = 255
    Image.fromarray(datos, mode="RGBA").save(ruta)
    return ruta


def test_una_hoja_se_recorta_en_fotogramas_cuadrados(tmp_path):
    """128×32 son cuatro fotogramas de 32×32, como `player_idle.png`."""
    fotogramas = build_datasets._fotogramas_de_hoja(_hoja(128, 32, tmp_path / "h.png"))
    assert len(fotogramas) == 4
    assert all(f.size == (32, 32) for f in fotogramas)


def test_el_tamano_del_fotograma_sale_de_la_altura_y_no_de_una_tabla():
    """`FRAME_SIZES` del motor dice 48 px para los jefes.

    Las hojas del Gavilán miden 40 de alto, así que recortar por tabla parte
    los fotogramas por la mitad. La altura de la hoja no puede equivocarse.
    """
    if not engine_bridge.hay_motor():
        pytest.skip("sin el repositorio del motor")

    hoja = engine_bridge.raiz_del_repositorio() / "assets/sprites/bosses/boss_gavilan_dive.png"
    if not hoja.exists():
        pytest.skip("la hoja del Gavilán ya no está donde estaba")

    fotogramas = build_datasets._fotogramas_de_hoja(hoja)
    assert fotogramas, "no se recortó ningún fotograma"
    _, alto = Image.open(hoja).size
    assert all(f.size == (alto, alto) for f in fotogramas)


def test_una_hoja_con_ancho_no_multiplo_pierde_solo_el_resto(tmp_path):
    """120×16 da 7 fotogramas de 16 y sobran 8 px. Se documenta, no se oculta."""
    fotogramas = build_datasets._fotogramas_de_hoja(_hoja(120, 16, tmp_path / "h.png"))
    assert len(fotogramas) == 7


def test_una_hoja_mas_estrecha_que_alta_no_da_nada(tmp_path):
    """Recortarla produciría fotogramas fuera del lienzo."""
    assert build_datasets._fotogramas_de_hoja(_hoja(10, 32, tmp_path / "h.png")) == []


def test_los_fotogramas_vacios_se_descartan(tmp_path):
    """Un ejemplo transparente etiquetado como «boss» le enseña al modelo que
    un rectángulo vacío es un jefe."""
    vacio = Image.open(_hoja(32, 32, tmp_path / "v.png", opaca=False))
    lleno = Image.open(_hoja(32, 32, tmp_path / "l.png", opaca=True))
    assert not build_datasets._tiene_contenido(vacio)
    assert build_datasets._tiene_contenido(lleno)


def test_las_piezas_sinteticas_y_su_csv_cuadran(tmp_path):
    """La verdad-terreno tiene que describir exactamente los ficheros escritos.

    Un CSV que apunta a una imagen que no existe —o al revés— hace que la
    Clase 4 entrene con etiquetas desplazadas, y el síntoma es una accuracy
    mediocre e inexplicable, no un error.
    """
    import csv

    conteo = build_datasets.construir_piezas(tmp_path)

    with (tmp_path / "verdad_terreno.csv").open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))

    assert len(filas) == build_datasets.PIEZAS_POR_LOTE
    assert conteo["OK"] + conteo["NO_OK"] == build_datasets.PIEZAS_POR_LOTE

    for fila in filas:
        assert (tmp_path / fila["fichero"]).exists(), f"el CSV cita {fila['fichero']}, que no existe"
        # Una pieza OK no puede traer defecto, y una NO_OK tiene que traerlo.
        if fila["clase"] == "OK":
            assert fila["defecto"] == ""
        else:
            assert fila["defecto"] in ("grieta", "mota", "deformacion")

    en_disco = {
        f"{c}/{p.name}" for c in ("OK", "NO_OK") for p in (tmp_path / c).glob("*.png")
    }
    assert en_disco == {fila["fichero"] for fila in filas}


def test_la_imagen_de_watershed_se_escribe_con_las_piezas(tmp_path):
    build_datasets.construir_piezas(tmp_path)
    assert (tmp_path / "piezas_en_contacto.png").exists()


def test_la_semilla_esta_fijada_en_un_solo_sitio():
    """Si cada cuaderno eligiera la suya, dos estudiantes compararían
    resultados de datasets distintos sin saberlo."""
    assert isinstance(build_datasets.SEMILLA, int)
    assert build_datasets.PIEZAS_POR_LOTE > 0


def test_las_escenas_que_se_capturan_son_las_del_taller():
    from cvcourse import course_mode

    assert set(build_datasets.ESCENAS) == set(course_mode.UNIDADES_DEL_TALLER.values())
