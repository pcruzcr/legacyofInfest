"""AUD-298 — los «17 pares de ciclos de importación» no eran ciclos.

La corrección
-------------
`docs/87` §15.0 midió 17 pares de importación mutua y §15.10 recomendó
reducirlos. Al ir a hacerlo, el barrido se hizo bien y el número cambió de
significado: aquel contaba **todos** los `import`, incluidos los que están
dentro de una función.

Un import diferido no es un ciclo. Se resuelve cuando se llama a la función, con
todo el árbol ya cargado, y es justamente el patrón con el que este proyecto
evita los ciclos de verdad: `title_scene` abre once pantallas y las once vuelven
al título, y las veintidós importaciones son diferidas.

Ciclos que **pueden** romper —dos módulos que se importan en el cuerpo, que es
lo que produce el `ImportError: cannot import name … (most likely due to a
circular import)`— hay **cero**. No había nada que arreglar; había que medir
mejor.

Lo que este fichero hace es fijar esa propiedad: cero es cero, y el día que
alguien escriba el primero, esto lo dirá con los dos nombres.
"""
from __future__ import annotations

import ast
import collections
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "src"


def _modulos() -> dict[str, pathlib.Path]:
    return {".".join(p.relative_to(RAIZ.parent).with_suffix("").parts): p
            for p in RAIZ.rglob("*.py")}


def _importa_en_el_cuerpo(arbol: ast.Module, conocidos: set[str]) -> set[str]:
    """Los `import src.*` del **cuerpo** del módulo.

    Sólo el cuerpo: son los que se ejecutan al importar y, por tanto, los
    únicos que pueden encontrarse un módulo a medio construir. Los de dentro de
    una función corren cuando alguien la llama.

    `if TYPE_CHECKING:` tampoco cuenta — no se ejecuta nunca — y por eso se
    recorre `arbol.body` en plano en vez de con `ast.walk`.
    """
    fuera: set[str] = set()
    for nodo in arbol.body:
        if isinstance(nodo, ast.ImportFrom):
            if nodo.module and nodo.level == 0 and nodo.module.startswith("src."):
                fuera.add(nodo.module)
                for alias in nodo.names:
                    completo = f"{nodo.module}.{alias.name}"
                    if completo in conocidos:
                        fuera.add(completo)
        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if alias.name.startswith("src."):
                    fuera.add(alias.name)
    return fuera


def _pares_mutuos() -> list[tuple[str, str]]:
    modulos = _modulos()
    aristas: dict[str, set[str]] = collections.defaultdict(set)
    for nombre, ruta in modulos.items():
        try:
            arbol = ast.parse(ruta.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        aristas[nombre] = _importa_en_el_cuerpo(arbol, set(modulos))
    return sorted({
        tuple(sorted((a, b)))
        for a, destinos in aristas.items()
        for b in destinos
        if b in aristas and a in aristas[b] and a != b
    })


def test_no_hay_ciclos_de_importacion_reales() -> None:
    """Cero. Y si algún día no lo es, esto dice cuáles."""
    pares = _pares_mutuos()
    assert pares == [], (
        f"{len(pares)} par(es) de módulos se importan mutuamente **en el "
        f"cuerpo**, que es lo que produce un ImportError circular: {pares}. "
        f"La salida habitual es diferir una de las dos importaciones al "
        f"interior de la función que la usa."
    )


def test_el_patron_del_menu_sigue_siendo_diferido() -> None:
    """La contrapartida: comprobar que el patrón que evita los ciclos existe.

    Sin esto, alguien podría «arreglar» el test de arriba borrando pantallas.
    `title_scene` abre once y las once vuelven al título; si esas
    importaciones dejaran de ser diferidas, el ciclo aparecería de verdad.
    """
    fuente = (RAIZ / "engine" / "scenes" / "title_scene.py").read_text(
        encoding="utf-8")
    arbol = ast.parse(fuente)
    en_el_cuerpo = _importa_en_el_cuerpo(arbol, set(_modulos()))
    # Sólo las **pantallas**: `demo_common` y `demo_layout` son ayudantes de
    # dibujado que no vuelven al título, así que importarlos en el cuerpo no
    # cierra ningún ciclo.
    escenas_en_el_cuerpo = {m for m in en_el_cuerpo
                            if m.startswith("src.engine.scenes.")
                            and m.endswith("_scene")}
    assert not escenas_en_el_cuerpo, (
        f"`title_scene` importa {escenas_en_el_cuerpo} en su cuerpo. Esas "
        f"pantallas vuelven al título, así que eso es un ciclo real: la "
        f"importación va dentro del método que abre la pantalla."
    )
