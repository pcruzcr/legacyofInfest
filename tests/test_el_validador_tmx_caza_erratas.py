"""AUD-392 — el validador tenía la lista de propiedades y no la miraba.

El defecto
==========
`scripts/validate_tmx.py` declaraba desde su primera versión::

    KNOWN_TILESETS = ["tileset_stage0", "tileset_zone1", ...]
    KNOWN_TMX_PROPERTIES = {
        "stage_id", "stage_name", "bgm_track", "time_limit",
        "climate", "background_zone", "gravity_multiplier",
    }

Ninguna de las dos se usaba en ninguna parte del repositorio. Eran una
comprobación que alguien pensó, escribió y no llegó a conectar.

Y estaban podridas además de muertas: declaraban **7** propiedades mientras
`StageLoader` lee **40**. Revivirlas tal cual habría avisado en falso sobre
`bloom`, `vignette`, `season`, `water_effect` y treinta más — que es
probablemente el motivo por el que nunca se conectaron.

La consecuencia medible: un mapa con `gravty_multiplier` en vez de
`gravity_multiplier` pasaba la validación en verde. El cargador no encuentra la
propiedad, aplica el valor por defecto y el nivel se juega con la gravedad
equivocada sin que nada lo diga. Es exactamente el fallo que `GAP-048` quería
comprar con el versionado de esquema —«un TMX viejo con una propiedad
renombrada falla como dato malo en vez de como versión antigua»—: el mecanismo
para detectarlo ya estaba escrito, sin enchufar.

Por qué avisa y no suspende
===========================
Una propiedad que el motor no lee **no** es necesariamente un error: un
estudiante puede declarar la suya en el TMX y leerla desde su propia
`StageScene`, que es un uso legítimo del framework y bastante razonable.
Suspender por eso repetiría AUD-106, donde el validador reprobaba a quien usaba
bien el framework. Avisa, nombra la más parecida, y deja la decisión a quien
lee.
"""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parent.parent


def _mapa_con_propiedad(tmp_path: Path, nombre: str, valor: str = "1") -> Path:
    """Copia de `stage0` con una propiedad de mapa añadida."""
    origen = _RAIZ / "assets" / "maps" / "stage0" / "stage0.tmx"
    destino = tmp_path / "conprop.tmx"
    shutil.copy(origen, destino)

    arbol = ET.parse(destino)
    props = arbol.getroot().find("properties")
    assert props is not None
    ET.SubElement(props, "property", {"name": nombre, "value": valor})
    arbol.write(destino, encoding="utf-8", xml_declaration=True)
    return destino


def _avisos_de(ruta: Path) -> list[str]:
    from scripts import validate_tmx as v

    v.validate_tmx(ruta)
    return list(v._warnings)


class TestLaErrataSeCaza:
    def test_una_propiedad_mal_escrita_produce_aviso(self, tmp_path: Path) -> None:
        """El defecto: `gravty_multiplier` pasaba en verde."""
        mapa = _mapa_con_propiedad(tmp_path, "gravty_multiplier", "2.0")
        avisos = [a for a in _avisos_de(mapa) if "gravty_multiplier" in a]
        assert avisos, (
            "un mapa con 'gravty_multiplier' no produjo ningún aviso; el "
            "cargador usará la gravedad por defecto sin decir nada"
        )

    def test_el_aviso_nombra_la_propiedad_correcta(self, tmp_path: Path) -> None:
        """Sin la sugerencia el aviso obliga a ir a buscar la grafía buena."""
        mapa = _mapa_con_propiedad(tmp_path, "gravty_multiplier", "2.0")
        avisos = [a for a in _avisos_de(mapa) if "gravty_multiplier" in a]
        assert any("gravity_multiplier" in a for a in avisos), (
            f"el aviso no sugiere la grafía correcta: {avisos}"
        )


class TestLoQueNoDebeAvisar:
    """El otro lado. Un validador que avisa de todo se ignora entero."""

    def test_los_mapas_del_motor_no_avisan_de_propiedades(self) -> None:
        """Los 17 mapas + la plantilla están limpios hoy, y deben seguirlo.

        Es el cable trampa de verdad: si alguien añade una propiedad al
        cargador y no la declara donde toca, o al revés, esto se pone rojo.
        """
        from scripts import validate_tmx as v

        sucios: dict[str, list[str]] = {}
        mapas = list((_RAIZ / "assets" / "maps").rglob("*.tmx"))
        mapas += list((_RAIZ / "student_templates").rglob("*.tmx"))
        assert mapas, "no se encontró ningún TMX que comprobar"

        for mapa in mapas:
            v.validate_tmx(mapa)
            # AUD-416 — se filtra por «el motor no la lee», que es la frase
            # exclusiva de ESTE aviso, y no por «propiedad de mapa».
            #
            # Con el filtro genérico, el aviso nuevo de AUD-416 —que termina
            # «Añádela como propiedad de mapa en Tiled»— se colaba aquí y ponía
            # roja una prueba que no tenía nada que ver. Filtrar avisos por una
            # subcadena que otro aviso puede contener es la misma trampa que
            # buscar código por texto: funciona hasta que alguien escribe una
            # frase parecida.
            propios = [a for a in v._warnings if "el motor no la lee" in a]
            if propios:
                sucios[mapa.parent.name] = propios
        assert not sucios, f"mapas con propiedades desconocidas: {sucios}"

    def test_author_no_avisa_aunque_el_motor_no_la_lea(self, tmp_path: Path) -> None:
        """`author` la declaran diez mapas y no la lee nadie. Es metadato."""
        mapa = _mapa_con_propiedad(tmp_path, "author", "quien sea")
        assert not [a for a in _avisos_de(mapa) if "author" in a]

    @pytest.mark.parametrize("alias", ["camera", "view"])
    def test_los_alias_en_ingles_no_avisan(self, tmp_path: Path, alias: str) -> None:
        """`camera`/`view` son grafía alternativa aceptada (AUD-129)."""
        mapa = _mapa_con_propiedad(tmp_path, alias, "seguir")
        assert not [a for a in _avisos_de(mapa) if alias in a]


def test_la_lista_muerta_no_vuelve() -> None:
    """`KNOWN_TMX_PROPERTIES` se borró; que no reaparezca a mano.

    El inventario vive en `check_tmx_coverage.PROPIEDADES_DEL_MOTOR`, que
    `test_el_guardian_de_tmx_lo_mira_todo.py` contrasta en los dos sentidos
    contra el AST del cargador. Una segunda lista escrita a mano volvería a
    desincronizarse igual que la primera.
    """
    from scripts import validate_tmx as v

    assert not hasattr(v, "KNOWN_TMX_PROPERTIES")
