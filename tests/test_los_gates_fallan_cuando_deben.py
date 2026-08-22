"""AUD-497 — que los validadores se comprueben a sí mismos.

El problema que esto cubre
==========================
Los siete validadores de `scripts/` son la red que sostiene el repositorio:
CI los ejecuta y un `0` significa «todo bien». Pero **nadie comprobaba que
supieran devolver algo distinto de `0`**. Un `except Exception` de más, un
`problemas += 1` que se pierde en una rama, o un `return` que se adelanta, y
el gate seguiría diciendo que todo está bien mientras el repositorio se
rompe — y el fallo sería invisible justo porque la señal de alarma es la que
está rota.

Auditado el 2026-08-15 rompiendo cada entrada a mano: los siete **sí**
devuelven `1` hoy. Esto no arregla un defecto, cierra la puerta: convierte
esa auditoría manual en una que se repite sola.

Por qué se rompe una copia y no el repositorio
----------------------------------------------
Un `git worktree` desechable de `HEAD`. Los validadores calculan su raíz
desde `__file__`, así que ejecutarlos dentro de la copia hace que lean los
ficheros de la copia; y así una prueba que se interrumpa a medias no deja el
repositorio de verdad con una traducción vacía o un mapa mutilado.

Por qué sólo se prueba el camino rojo
-------------------------------------
El verde ya lo prueba CI en cada ejecución: si un gate fallara sobre el
árbol limpio, el repositorio entero estaría rojo y se sabría enseguida. Lo
que nadie ejercita nunca es el camino de error, que es exactamente el que
tiene que funcionar el día que haga falta.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

#: Huella de los ficheros TOCADOS al empezar el módulo. La toma la fixture
#: `copia`, que corre antes de ninguna avería; el seguro del final compara
#: contra esto y no contra git (ver el docstring de la clase).
_HUELLA_INICIAL: dict[str, bytes] = {}


@pytest.fixture(scope="module")
def copia(tmp_path_factory) -> Iterator[Path]:
    """Un árbol de trabajo desechable en `HEAD`."""
    destino = tmp_path_factory.mktemp("gates") / "repo"
    hecho = subprocess.run(
        ["git", "worktree", "add", str(destino), "HEAD", "--detach"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    if hecho.returncode != 0:
        pytest.skip(f"no se pudo crear el árbol de prueba: {hecho.stderr[:200]}")
    # AUD-588 — se fotografía el repositorio real ANTES de romper nada. El
    # seguro de abajo comparaba contra `git show HEAD`, y eso confundía dos
    # cosas: una avería escapada y trabajo legítimo sin commitear en un
    # fichero de la lista TOCADOS (pasó de verdad en la rama 4-1, donde
    # STAGE_CREATION.md documenta los ambient_fx nuevos). Contra la foto no
    # hay falso positivo posible: lo que valía antes de las averías vale
    # después, commiteado o no.
    for relativo in TestLaAveriaEsDeVerdad.TOCADOS:
        _HUELLA_INICIAL[relativo] = (RAIZ / relativo).read_bytes()
    try:
        yield destino
    finally:
        subprocess.run(
            ["git", "worktree", "remove", str(destino), "--force"],
            cwd=RAIZ, capture_output=True,
        )


def _correr(copia: Path, guion: str, *args: str) -> int:
    """Ejecuta un validador dentro de la copia y devuelve su código."""
    return subprocess.run(
        [sys.executable, f"scripts/{guion}", *args],
        cwd=copia, capture_output=True, text=True, timeout=300,
    ).returncode


class TestCadaGateSabeDecirQueNo:
    """Un gate que no sabe fallar no es un gate, es un adorno."""

    def _probar(self, copia: Path, relativo: str, romper, guion: str,
                *args: str) -> None:
        objetivo = copia / relativo
        respaldo = objetivo.read_bytes()
        try:
            romper(objetivo)
            codigo = _correr(copia, guion, *args)
        finally:
            objetivo.write_bytes(respaldo)
        assert codigo != 0, (
            f"{guion} devolvió 0 con {relativo} roto a propósito: el gate "
            f"no protege nada"
        )

    def test_validate_tmx_caza_una_propiedad_obligatoria_ausente(self, copia) -> None:
        def romper(p: Path) -> None:
            s = p.read_text(encoding="utf-8")
            s2 = re.sub(r'<property name="stage_name"[^/]*/>', "", s, count=1)
            assert s2 != s, "la avería no se aplicó"
            p.write_text(s2, encoding="utf-8")

        self._probar(copia, "assets/maps/stage0/stage0.tmx", romper,
                     "validate_tmx.py", "--ci")

    def test_validate_assets_caza_un_recurso_que_falta(self, copia) -> None:
        objetivo = copia / "assets/tilesets/tileset_stage0.png"
        respaldo = objetivo.read_bytes()
        try:
            objetivo.unlink()
            codigo = _correr(copia, "validate_assets.py")
        finally:
            objetivo.write_bytes(respaldo)
        assert codigo != 0, "validate_assets dio por bueno un tileset ausente"

    def test_check_translations_caza_una_entrada_vacia(self, copia) -> None:
        def romper(p: Path) -> None:
            catalogo = json.loads(p.read_text(encoding="utf-8"))
            catalogo[next(iter(catalogo))] = "   "
            p.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2),
                         encoding="utf-8")

        self._probar(copia, "locale/es.json", romper,
                     "check_translations.py", "--ci")

    def test_check_dependency_sync_caza_una_dependencia_perdida(self, copia) -> None:
        def romper(p: Path) -> None:
            lineas = p.read_text(encoding="utf-8").splitlines()
            quedan = [x for x in lineas if not x.lower().startswith("pygame")]
            assert len(quedan) < len(lineas), "la avería no se aplicó"
            p.write_text("\n".join(quedan) + "\n", encoding="utf-8")

        self._probar(copia, "requirements.txt", romper,
                     "check_dependency_sync.py")

    def test_generate_tmx_reference_caza_el_bloque_desfasado(self, copia) -> None:
        """Sólo compara lo que hay entre marcadores: la avería tiene que ir
        **dentro**, o se estaría midiendo que el gate ignora lo de fuera —
        que es lo correcto."""
        marca = "<!-- BEGIN GENERATED: tipos de objeto -->"

        def romper(p: Path) -> None:
            s = p.read_text(encoding="utf-8")
            i = s.index(marca) + len(marca)
            p.write_text(s[:i] + "\n\n| FilaInventada | no sale del generador |\n"
                         + s[i:], encoding="utf-8")

        self._probar(copia, "docs/STAGE_CREATION.md", romper,
                     "generate_tmx_reference.py", "--check")


class TestLaAveriaEsDeVerdad:
    """Si la avería no llega a aplicarse, la prueba de arriba mediría el
    árbol limpio y pasaría por el motivo equivocado."""

    def test_el_arbol_de_prueba_es_una_copia_aparte(self, copia) -> None:
        assert copia.is_dir()
        assert (copia / "scripts" / "validate_tmx.py").exists()
        assert copia.resolve() != RAIZ.resolve()

    def test_restaurar_deja_el_fichero_como_estaba(self, copia) -> None:
        objetivo = copia / "locale/es.json"
        antes = objetivo.read_bytes()
        respaldo = objetivo.read_bytes()
        try:
            objetivo.write_bytes(b"{}")
            assert objetivo.read_bytes() != antes
        finally:
            objetivo.write_bytes(respaldo)
        assert objetivo.read_bytes() == antes

    #: Los ficheros exactos que rompen las pruebas de arriba. Si una avería
    #: se escapara de la copia, se notaría en éstos.
    TOCADOS = (
        "assets/maps/stage0/stage0.tmx",
        "assets/tilesets/tileset_stage0.png",
        "locale/es.json",
        "requirements.txt",
        "docs/STAGE_CREATION.md",
    )

    def test_el_repositorio_de_verdad_no_se_toca(self, copia) -> None:
        """El seguro que hace inofensivo todo lo anterior.

        Compara los ficheros TOCADOS contra la foto que tomó la fixture
        `copia` al empezar, no contra git: en Windows el árbol de trabajo
        tiene CRLF y el objeto guardado LF, así que un `git show` contra el
        disco difiere siempre aunque nadie lo haya tocado; y un árbol con
        trabajo legítimo sin commitear (lo normal mientras se desarrolla)
        hacía fallar la versión antigua aunque ninguna avería se hubiera
        escapado. AUD-588 tiene el detalle.
        """
        escapados = [
            relativo for relativo, antes in _HUELLA_INICIAL.items()
            if (RAIZ / relativo).read_bytes() != antes
        ]
        assert not escapados, f"una avería se escapó al repositorio real: {escapados}"
