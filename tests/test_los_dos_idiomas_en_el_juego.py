"""
Module: test_los_dos_idiomas_en_el_juego
System: tests
Academic Unit: N/A

AUD-307 — seis cadenas se veían en español jugando en inglés.

Lo que pasaba
============
El código de interfaz de este proyecto es bilingüe a propósito: hay literales
escritos en inglés y literales escritos en castellano, y cada catálogo traduce
en un sentido. `es.json` lleva del inglés al castellano; `en.json`, al revés.

De ahí salía una comprobación que nadie hacía. `check_translations.py` avisaba
de entradas huérfanas —traducciones de cadenas que ya no existen— y de cadenas
sin entrada, pero lo segundo lo daba por bueno con una nota, porque un literal
ya castellano no necesita entrada en `es.json`. Cierto, y sin embargo:

    'ESTUDIANTE', 'EXPERIENCIA', 'Elegir', 'IDENTIFICACIÓN', 'Subir rango',
    'ÁRBOL DE HABILIDADES'

Esas seis están en castellano y **no tenían entrada en `en.json`**. Un jugador
con el idioma en inglés las veía en español. Dos de ellas son de AUD-293 y
AUD-267: el modo de fallo no es que alguien renombre una cadena, es que una
función nueva llega con sus textos y nadie se acuerda del catálogo.

La regla, que es exacta y no una heurística de idioma
=====================================================
No hace falta adivinar en qué idioma está un literal: lo dice el propio
catálogo. Una cadena visible que **no** está en `es.json` es que ya estaba en
castellano — por eso no necesita traducción al castellano. Y una cadena en
castellano tiene que tener su entrada en `en.json`.

Esa es toda la regla, y es la que este fichero fija.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
LOCALE = RAIZ / "locale"


@pytest.fixture(scope="module")
def visibles() -> set[str]:
    sys.path.insert(0, str(RAIZ / "scripts"))
    from check_translations import cadenas_visibles

    return cadenas_visibles()


def _catalogo(idioma: str) -> dict[str, str]:
    return json.loads((LOCALE / f"{idioma}.json").read_text(encoding="utf-8"))


class TestLosDosCatalogosExistenYSonUsables:
    @pytest.mark.parametrize("idioma", ["es", "en"])
    def test_carga_y_no_tiene_entradas_vacias(self, idioma: str) -> None:
        catalogo = _catalogo(idioma)

        assert catalogo, f"{idioma}.json está vacío"
        vacias = [k for k, v in catalogo.items()
                  if not str(k).strip() or not str(v).strip()]
        assert not vacias, (
            f"{idioma}.json tiene entradas sin clave o sin valor: {vacias}. "
            f"Una traducción vacía se muestra como una cadena vacía, que en "
            f"pantalla es un hueco donde debería haber una palabra"
        )


class TestNadaSeVeEnElIdiomaEquivocado:
    def test_toda_cadena_castellana_tiene_su_ingles(self, visibles) -> None:
        """La comprobación que faltaba. Ver el encabezado para la regla."""
        cat_es = _catalogo("es")
        cat_en = _catalogo("en")

        castellanas = {s for s in visibles if s not in cat_es}
        sin_ingles = sorted(castellanas - set(cat_en))

        assert not sin_ingles, (
            f"{len(sin_ingles)} cadena(s) en castellano sin traducción al "
            f"inglés: {sin_ingles}. Jugando en inglés se verían en español"
        )

    def test_las_seis_de_aud_307_siguen_traducidas(self) -> None:
        """Fijadas por nombre: son las que había, y sirven de ejemplo de qué
        se rompe si alguien vacía el catálogo sin mirar."""
        cat_en = _catalogo("en")

        for cadena in ("ESTUDIANTE", "EXPERIENCIA", "Elegir",
                       "IDENTIFICACIÓN", "Subir rango",
                       "ÁRBOL DE HABILIDADES"):
            assert cat_en.get(cadena), f"{cadena!r} volvió a quedarse sin inglés"


class TestElGateLoVigila:
    """De nada sirve arreglar las seis si el validador sigue dándolas por
    buenas: volverían con la próxima pantalla nueva."""

    def test_el_validador_pasa_con_los_catalogos_de_hoy(self) -> None:
        completado = subprocess.run(
            [sys.executable, "scripts/check_translations.py", "--ci", "--permitted-orphans", str(RAIZ / "locale" / "permitted_orphans.json")],
            cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
            # `errors="replace"` y no el modo estricto: el validador escribe
            # acentos y en una consola cp1252 �la de Windows por defecto� la
            # salida no es UTF-8 v�lido. Sin esto, la prueba reventaba al
            # *decodificar* el informe en vez de al comprobarlo, que es el
            # mismo defecto que AUD-303 corrigi� en el banco de sprites. Lo
            # que se juzga aqu� es el c�digo de salida; el texto s�lo sirve
            # para el mensaje de error.
            errors="replace",
            check=False,
        )

        assert completado.returncode == 0, completado.stdout[-2000:]

    def test_el_validador_falla_si_le_quitas_una_traduccion(
        self, tmp_path, monkeypatch,
    ) -> None:
        """La prueba de que el gate mide algo.

        Se copia el árbol de `locale/` a un temporal, se le quita una entrada y
        se ejecuta el validador apuntando ahí. El repositorio no se toca.
        """
        destino = tmp_path / "locale"
        destino.mkdir()
        (destino / "es.json").write_text(
            (LOCALE / "es.json").read_text(encoding="utf-8"), encoding="utf-8")

        mutado = _catalogo("en")
        del mutado["ÁRBOL DE HABILIDADES"]
        (destino / "en.json").write_text(
            json.dumps(mutado, ensure_ascii=False, indent=2), encoding="utf-8")

        sys.path.insert(0, str(RAIZ / "scripts"))
        import check_translations

        monkeypatch.setattr(check_translations, "_RAIZ", tmp_path)
        monkeypatch.setattr(sys, "argv", ["check_translations.py", "--ci", "--permitted-orphans", str(RAIZ / "locale" / "permitted_orphans.json")])

        assert check_translations.main() == 1, (
            "el validador da por buenos unos catálogos a los que les falta "
            "una traducción al inglés: no vigila nada"
        )
