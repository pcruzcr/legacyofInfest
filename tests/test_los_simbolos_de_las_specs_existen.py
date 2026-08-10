"""AUD-365: lo que una especificación promete entre acentos graves, existe.

El hallazgo
===========

AUD-307 midió `docs/22_API_CONTRACTS.md` con un comprobador AST **de usar y
tirar**: de 381 símbolos citados, **50 no existían**. Corrigió trece entradas
y borró el comprobador. El defecto se arregló; el guardián que impedía que
volviera, no.

Es la tercera vez que esta auditoría encuentra la misma forma:

* AUD-353 — el gate de ruff se comprobaba por estar **escrito** en `ci.yml`,
  no por su resultado, y llevaba tiempo en rojo.
* AUD-356 — los calificadores emitían `--json` y nadie parseaba la salida, así
  que llevaban tiempo emitiendo algo que no era JSON.
* AUD-365 — una comprobación de documentación que ocurrió **una vez**.

Una verificación que ocurre una vez no es una verificación: es una foto.

Qué se arregló al ponerlo
=========================

Primera ejecución sobre las seis specs: **40 de 204 símbolos citados no
existían**. La inmensa mayoría eran falsos positivos del propio comprobador
—tipos de objeto de Tiled, símbolos de pygame y numpy, claves del banco de
sonidos— y afinarlo bajó la cifra a **7 promesas rotas de verdad**:

* `bind_player` (dos sitios) — retirada en AUD-307, el documento seguía
  citándola en fuente de código;
* `banner_medium` — una fuente que **nunca ha existido**; `hud.py:215` dibuja
  el nombre del jefe con la fuente por defecto de pygame a 12 px;
* `ReyMetad` (cuatro sitios) — nombre de diseño de una forma no implementada
  (las fases 2-3 del Rey son Práctica II del estudiante);
* `snake_case` / `PascalCase` — convenciones de nombres, no nombres.

Hoy: **173 símbolos citados, 0 rotos.**

Y una lección de paso, que está en el código del comprobador: su primera
versión envolvía los imports del motor en un `except ImportError` que devolvía
un conjunto vacío. El vocabulario de Tiled se perdía **en silencio** y el
informe daba siete falsos positivos con toda naturalidad. Un respaldo mudo que
convierte un fallo de entorno en un resultado plausible es peor que la
excepción que evita.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def test_ninguna_spec_promete_un_simbolo_que_no_existe() -> None:
    """Se ejecuta el comprobador de verdad, no se comprueba que exista.

    En un proceso aparte y por su interfaz de línea de órdenes: es la misma
    que corre CI, así que lo que se verifica aquí es exactamente lo que
    protege allí. Una prueba que importara la función y la llamara podría
    pasar con un `--ci` roto.
    """
    proceso = subprocess.run(
        [sys.executable, "scripts/check_doc_symbols.py", "--ci"],
        capture_output=True, text=True, cwd=str(RAIZ), timeout=300, check=False,
    )
    assert proceso.returncode == 0, proceso.stdout[-4000:]


def test_el_comprobador_sigue_mirando_las_seis_specs() -> None:
    """Vaciar la lista pondría el gate en verde sin comprobar nada.

    Es el mismo riesgo que `mypy_scope.txt` tiene con su trinquete y que
    `test_puertas_de_calidad` vigila allí: la forma más fácil de poner una
    puerta en verde es quitarle lo que vigilaba.
    """
    from scripts.check_doc_symbols import SPECS

    assert len(SPECS) >= 6, SPECS
    for nombre in SPECS:
        assert (RAIZ / "docs" / nombre).exists(), nombre


def test_el_comprobador_no_se_traga_un_fallo_de_entorno() -> None:
    """Sin vocabulario de Tiled el informe miente, así que no puede fallar mudo.

    La primera versión devolvía un conjunto vacío ante un `ImportError` y
    producía siete falsos positivos sin decir nada. Ahora el import es directo
    y revienta si el entorno está roto, que es lo que hay que saber.
    """
    from scripts.check_doc_symbols import vocabulario_de_tiled

    tipos = vocabulario_de_tiled()
    assert len(tipos) > 50, (
        f"sólo {len(tipos)} tipos de Tiled: el vocabulario no se cargó y el "
        f"informe daría falsos positivos"
    )
