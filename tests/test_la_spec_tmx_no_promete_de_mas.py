"""
Module: test_la_spec_tmx_no_promete_de_mas
System: tests
Academic Unit: N/A

AUD-310 — `06_TMX_SPEC.md` documentaba cinco propiedades que nadie implementa.

Lo que había
============
La especificación de TMX es lo que lee un estudiante mientras monta su mapa en
Tiled. Documentaba estas cinco como si funcionaran:

* `background_color` — color de fondo del cielo
* `debug_mode` — activar el overlay de depuración desde el mapa
* `use_tile_collision` — sacar la colisión de las propiedades del tileset
* `damage_type` — tipo de daño de una `HazardZone`
* `trigger_once` — que un mensaje sólo salga la primera vez

Ninguna de las cinco la lee un solo módulo de `src/`. Y no es teórico:
**`stage1_2_la_soda.tmx` usa `trigger_once`**, así que alguien la escribió
creyendo que su mensaje saldría una vez. Lo que de verdad hace eso es el
**tipo** `MessageTrigger_Once`, que es otra cosa: no una propiedad, otro `type`.

De regalo, el ejemplo XML de mensajes usaba `type="Message"`, que tampoco existe
—el cargador conoce `MessageTrigger` y `MessageTrigger_Once`—, así que copiarlo
tal cual producía un objeto que el cargador rechaza.

Por qué esto es peor que un documento incompleto
=================================================
Un documento al que le falta algo hace que el estudiante pregunte. Un documento
que promete de más hace que el estudiante escriba la propiedad, no vea ningún
efecto y concluya que **el motor está roto** o que él lo hizo mal. El coste no
lo paga quien escribió el documento.

Qué fija esta prueba
====================
Que las cinco sigan marcadas como no implementadas mientras no existan, y que
los tipos de objeto que aparecen en los ejemplos de la especificación sean tipos
que el cargador reconoce de verdad.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SPEC = RAIZ / "docs" / "06_TMX_SPEC.md"
SRC = RAIZ / "src"

#: Las cinco de AUD-310. Si alguna se implementa, quítala de aquí **y** quítale
#: el aviso al documento: la prueba fallará hasta que se haga lo segundo.
NO_IMPLEMENTADAS = (
    "background_color",
    "debug_mode",
    "use_tile_collision",
    # AUD-387 — `damage_type` sale de esta lista: ya está implementada. Llevaba
    # aquí desde AUD-310 y no por descuido, sino porque el motor no tenía
    # canales de daño — prometer un *tipo* cuando sólo sabes restar un número
    # es prometer nada. Con el catálogo de `data/damage_types.json`, una
    # `HazardZone` puede declarar `damage_type="veneno"` y la resistencia de
    # cada enemigo empieza a significar algo.
    "trigger_once",
)


@pytest.fixture(scope="module")
def spec() -> str:
    return SPEC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def fuente() -> str:
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in SRC.rglob("*.py")
    )


class TestLasCincoSiguenSinImplementar:
    @pytest.mark.parametrize("propiedad", NO_IMPLEMENTADAS)
    def test_ningun_modulo_la_lee(self, propiedad: str, fuente: str) -> None:
        """Si esto falla, alguien la implementó: enhorabuena, y hay que
        quitarle el aviso al documento y sacarla de la lista de arriba."""
        assert propiedad not in fuente, (
            f"`{propiedad}` ya existe en src/: el aviso de "
            f"«NO IMPLEMENTADA» de 06_TMX_SPEC.md ha dejado de ser cierto"
        )

    @pytest.mark.parametrize("propiedad", NO_IMPLEMENTADAS)
    def test_el_documento_avisa(self, propiedad: str, spec: str) -> None:
        """Y si esto falla, alguien volvió a documentarla como si funcionara."""
        for linea in spec.splitlines():
            if propiedad not in linea:
                continue
            bajo = linea.lower()
            # AUD-454 — el tachado cuenta como aviso.
            #
            # El documento las agrupa bajo «2.2 Propiedades que **no** existen»
            # y las tacha: `~~`background_color`~~`. Eso avisa mejor que
            # repetir la frase en cada fila —lo dice una vez, para toda la
            # tabla, y con una notación que se ve de un vistazo—, pero esta
            # prueba miraba línea a línea y no veía ni la cabecera ni el
            # tachado, así que exigía una redacción concreta.
            #
            # Una fila sin tachar y sin la frase sigue fallando, que es lo que
            # esta prueba existe para cazar: documentar como si funcionara algo
            # que no funciona.
            tachada = f"~~`{propiedad}`~~" in linea
            assert tachada or "no está implementada" in bajo \
                or "no implementad" in bajo, (
                f"06_TMX_SPEC.md menciona `{propiedad}` sin avisar de que "
                f"no está implementada:\n    {linea.strip()[:160]}"
            )


class TestLosEjemplosCargarian:
    def test_los_tipos_de_los_ejemplos_existen(self, spec: str) -> None:
        """El ejemplo usaba `type="Message"`, que el cargador no conoce.

        Copiar y pegar de la especificación tiene que producir un mapa que
        cargue; si no, la especificación es peor que no tenerla.
        """
        # La misma lista que el cargador usa para decidir si un `type` es
        # válido, y que aparece en su mensaje de error cuando no lo es. Usar
        # otra fuente sería medir contra una copia.
        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader
        from src.framework.stage.tmx_diagnostics import known_object_types

        # `ensure_registered()` y no confiar en el import: los arquetipos se
        # registran en esa llamada, no al importar el módulo. Sin ella el
        # registro sale vacío y `Walker` parece un tipo inventado — que es lo
        # que le pasó a la primera versión de esta prueba.
        entity_factory.ensure_registered()
        conocidos = set(known_object_types(list(StageLoader._entity_registry)))
        conocidos |= set(StageLoader._registro_historico)
        # AUD-454 — los tipos de la capa `Collision` también cuentan.
        #
        # `Platform` y `Solid` no están en el vocabulario de la capa `Objects`
        # —que es lo que devuelve `known_object_types`— pero el cargador **sí**
        # los reconoce: `stage_loader` los reparte entre `one_way_rects` y
        # `collision_rects` según el tipo. Sin esto, un ejemplo correcto de la
        # capa de colisión se denunciaba como tipo inventado, que es la misma
        # clase de falso positivo que AUD-096 y AUD-112: la herramienta
        # castigando trabajo bien hecho.
        from src.framework.stage.tmx_diagnostics import COLLISION_OBJECT_TYPES

        conocidos |= set(COLLISION_OBJECT_TYPES)

        usados = set(re.findall(r'<object[^>]*\stype="(\w+)"', spec))
        desconocidos = sorted(t for t in usados if t not in conocidos)

        assert not desconocidos, (
            f"los ejemplos de 06_TMX_SPEC.md usan tipos que el cargador no "
            f"reconoce: {desconocidos}. Copiarlos produce objetos que el "
            f"cargador rechaza"
        )
