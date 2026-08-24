"""AUD-494 — de hoja de referencia dibujada a atlas que Tiled pueda cortar.

La hoja de la Fase 1 salió con el contenido correcto pero no es un atlas:
piezas de tamaños distintos flotando sobre fondo blanco, sin rejilla. Tiled
necesita celdas idénticas de 16x16, margen 0, espaciado 0 y transparencia.

Estas pruebas montan una hoja sintética con la misma forma del problema
—piezas de tamaños distintos, separadas, sobre blanco, alguna con blanco
*dentro* del dibujo— y comprueban que sale un atlas usable.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from tools.hoja_a_tileset import (
    COLUMNAS,
    TS,
    Pieza,
    escribir_tsx,
    montar,
    quitar_el_fondo,
    recortar_piezas,
)


def _pixeles(img: Image.Image) -> list[tuple[int, int, int, int]]:
    """Los píxeles como tuplas, sin `getdata()` (deprecado en Pillow 14)."""
    crudo = img.convert("RGBA").tobytes()
    return [tuple(crudo[i:i + 4]) for i in range(0, len(crudo), 4)]  # type: ignore[misc]


def _hoja(cajas: list[tuple[int, int, int, int, tuple[int, int, int]]]) -> Image.Image:
    hoja = Image.new("RGBA", (800, 400), (255, 255, 255, 255))
    d = ImageDraw.Draw(hoja)
    for x0, y0, x1, y1, color in cajas:
        d.rectangle((x0, y0, x1, y1), fill=(*color, 255))
    return hoja


class TestElFondoSeVaPeroElDibujoNo:
    def test_el_blanco_del_borde_queda_transparente(self) -> None:
        limpia = quitar_el_fondo(_hoja([(100, 100, 160, 160, (40, 90, 40))]))
        assert limpia.getpixel((2, 2))[3] == 0
        assert limpia.getpixel((130, 130))[3] == 255

    def test_el_blanco_de_dentro_se_conserva(self) -> None:
        """La calavera y las flores del arbusto son casi blancas. Un umbral
        a secas las agujerearía; por eso el vaciado va por inundación desde
        el borde y no por comparación píxel a píxel."""
        hoja = _hoja([(100, 100, 200, 200, (40, 90, 40))])
        ImageDraw.Draw(hoja).rectangle((130, 130, 170, 170), fill=(255, 255, 255, 255))
        limpia = quitar_el_fondo(hoja)
        assert limpia.getpixel((150, 150))[3] == 255, (
            "el blanco rodeado de dibujo se vació: la calavera saldría hueca"
        )


class TestLasPiezasSeLeenEnOrden:
    def test_orden_de_lectura_con_alturas_distintas(self) -> None:
        """El ángel y el banco están en la misma fila a alturas distintas.
        Ordenar sólo por `y` los mezclaría con la fila siguiente y toda la
        tabla de nombres quedaría corrida una posición."""
        hoja = _hoja([
            (30, 30, 90, 90, (200, 0, 0)),      # fila 1, izquierda
            (130, 20, 190, 110, (0, 200, 0)),   # fila 1, más alta
            (30, 200, 90, 260, (0, 0, 200)),    # fila 2
            (130, 200, 190, 260, (200, 200, 0)),
        ])
        cajas = recortar_piezas(quitar_el_fondo(hoja))
        assert len(cajas) == 4
        assert [c[0] for c in cajas] == [30, 130, 30, 130]
        assert cajas[0][1] < cajas[2][1]

    def test_las_motas_no_cuentan_como_pieza(self) -> None:
        hoja = _hoja([
            (30, 30, 90, 90, (200, 0, 0)),
            (200, 200, 202, 202, (10, 10, 10)),  # resto del suavizado
        ])
        assert len(recortar_piezas(quitar_el_fondo(hoja))) == 1


class TestElAtlasEsUnaRejillaDeVerdad:
    @pytest.fixture
    def montado(self):
        hoja = _hoja([
            (30, 30, 90, 90, (200, 0, 0)),
            (130, 30, 190, 150, (0, 200, 0)),
            (230, 30, 350, 150, (0, 0, 200)),
        ])
        piezas = (Pieza("suelo"), Pieza("poste", (1, 2)), Pieza("copa", (2, 2)))
        return montar(hoja, piezas, colores=16)

    def test_las_medidas_son_multiplos_de_la_baldosa(self, montado) -> None:
        atlas, _nombres = montado
        assert atlas.width == COLUMNAS * TS
        assert atlas.height % TS == 0

    def test_cada_pieza_ocupa_los_huecos_de_su_huella(self, montado) -> None:
        """Escalar una lápida de dos baldosas a una sola la vuelve
        ilegible; por eso la tabla declara la huella y aquí se comprueba."""
        _atlas, nombres = montado
        assert nombres[0] == "vacio"
        assert nombres.count("suelo") == 1
        assert len([n for n in nombres if n.startswith("poste")]) == 2
        assert len([n for n in nombres if n.startswith("copa")]) == 4

    def test_la_paleta_queda_corta(self, montado) -> None:
        """Los demás tilesets del juego viven entre 18 y 38 colores;
        `scripts/validate_assets.py` documenta (AUD-011) que una cuenta alta
        en un atlas delata un export reescalado."""
        atlas, _nombres = montado
        opacos = {px[:3] for px in _pixeles(atlas) if px[3] > 0}
        assert len(opacos) <= 16

    def test_el_alfa_es_binario(self, montado) -> None:
        """Un borde semitransparente se ve como halo sucio sobre el mapa."""
        atlas, _nombres = montado
        assert {px[3] for px in _pixeles(atlas)} <= {0, 255}

    def test_el_primer_hueco_esta_vacio(self, montado) -> None:
        atlas, _nombres = montado
        recorte = atlas.crop((0, 0, TS, TS))
        assert max(px[3] for px in _pixeles(recorte)) == 0

    def test_se_queja_si_faltan_piezas(self) -> None:
        """Si la hoja se regenera con menos piezas, callarse desplazaría
        todos los gid y repintaría el nivel con la baldosa equivocada — el
        defecto que AUD-115 ya documentó para el otro atlas."""
        hoja = _hoja([(30, 30, 90, 90, (200, 0, 0))])
        with pytest.raises(SystemExit):
            montar(hoja, (Pieza("a"), Pieza("b")), colores=8)


class TestElTsxSirveParaTiled:
    def test_declara_la_rejilla(self, tmp_path: Path) -> None:
        destino = tmp_path / "x.tsx"
        escribir_tsx(destino, tmp_path / "x.png", huecos=32, alto_px=64)
        texto = destino.read_text(encoding="utf-8")
        assert f'tilewidth="{TS}"' in texto
        assert f'tileheight="{TS}"' in texto
        assert 'margin="0" spacing="0"' in texto
        assert f'columns="{COLUMNAS}"' in texto
