"""
Module: test_referencia_tmx
System: tests
Academic Unit: N/A

AUD-182 — la guía de creación de escenarios no puede publicar un tipo vacío.

Qué falló
---------
`scripts/generate_tmx_reference.py` genera la tabla de tipos de objeto de
`docs/STAGE_CREATION.md` y el CI la vigila con `--check`. Aun así, **22 de los
35 tipos estructurales salían publicados como `| — | — |`**: sin geometría y
sin propiedades. Entre ellos `Conveyor`, `Spring`, `MovingPlatform`,
`WaterZone`, `Guard`, `Zipline` y las dos puertas — es decir, casi todo lo que
convierte un mapa en un nivel.

El estudiante veía que el tipo existe y no tenía forma de averiguar qué
propiedades acepta. Peor: al salir en blanco, lo razonable era deducir que no
acepta ninguna, cuando `MovingPlatform` tiene cuatro y `Guard` cinco. Las
propiedades estaban documentadas en los docstrings del cargador, que es
justamente donde un alumno de segundo año no va a mirar.

Por qué el gate no lo detectaba
-------------------------------
`--check` compara el documento contra la salida del generador. Si el generador
emite `—`, el documento con `—` está «al día». El gate verificaba coherencia
entre el doc y una tabla incompleta, no que la tabla estuviera completa. Es el
modo de fallo que este repositorio ya conoce: una comprobación que se cumple
sola.

Lo que fija esta prueba
-----------------------
Que todo tipo que el cargador acepta esté documentado con datos de verdad. Al
añadir la mecánica número doce, esta prueba falla y nombra el tipo que falta,
en vez de publicarlo en blanco y que se entere el estudiante.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.framework.stage.tmx_diagnostics import BUILTIN_OBJECT_TYPES

RAIZ = Path(__file__).resolve().parent.parent
DOC = RAIZ / "docs" / "STAGE_CREATION.md"

#: Tipos cuya columna de propiedades puede empezar por «—» con razón: no
#: aceptan ninguna, y decirlo es información, no un hueco. Cada uno lleva por
#: qué. Si un tipo entra aquí sin motivo, la revisión lo verá.
SIN_PROPIEDADES: dict[str, str] = {
    "PlayerSpawn": "sólo su posición; la Y son los pies del jugador",
    "NextTrigger": "sólo su área: entrar completa el escenario",
    "DeathPit": "sólo su área: caer dentro mata",
}


def _tabla_estructural() -> dict[str, tuple[str, str]]:
    """Las filas de la tabla publicada, por tipo."""
    texto = DOC.read_text(encoding="utf-8")
    inicio = texto.index("### Tipos estructurales")
    fin = texto.index("### Arquetipos de enemigo")
    filas = {}
    for linea in texto[inicio:fin].splitlines():
        m = re.match(r"\|\s*`([A-Za-z_]+)`\s*\|([^|]*)\|([^|]*)\|", linea)
        if m:
            filas[m.group(1)] = (m.group(2).strip(), m.group(3).strip())
    return filas


class TestTodoTipoAceptadoEstaDocumentado:
    def test_la_tabla_publica_todos_los_tipos(self) -> None:
        publicados = _tabla_estructural()
        faltan = [t for t in BUILTIN_OBJECT_TYPES if t not in publicados]
        assert not faltan, (
            f"el cargador acepta estos tipos y la guía no los menciona: "
            f"{faltan}. Ejecuta scripts/generate_tmx_reference.py"
        )

    @pytest.mark.parametrize("tipo", BUILTIN_OBJECT_TYPES)
    def test_ningun_tipo_se_publica_sin_geometria(self, tipo: str) -> None:
        """Sin geometría, el estudiante no sabe si dibujar un punto o un área.

        Es la diferencia entre que la puerta funcione o se ignore en silencio:
        `Door` sin tamaño no bloquea nada y el cargador sólo deja un aviso en
        el log.
        """
        geometria, _ = _tabla_estructural()[tipo]
        assert geometria and geometria != "—", (
            f"`{tipo}` se publica sin decir qué hay que dibujar en Tiled"
        )

    @pytest.mark.parametrize("tipo", BUILTIN_OBJECT_TYPES)
    def test_ningun_tipo_se_publica_sin_propiedades(self, tipo: str) -> None:
        _, propiedades = _tabla_estructural()[tipo]
        if tipo in SIN_PROPIEDADES:
            assert propiedades.startswith("—"), (
                f"`{tipo}` está declarado como «sin propiedades» en "
                f"SIN_PROPIEDADES ({SIN_PROPIEDADES[tipo]}) pero la tabla le "
                f"da algunas: {propiedades!r}. Sácalo de la lista"
            )
            return
        assert propiedades and propiedades != "—", (
            f"`{tipo}` se publica sin una sola propiedad. O acepta alguna y "
            f"hay que documentarla en `structural` de "
            f"scripts/generate_tmx_reference.py, o no acepta ninguna y va a "
            f"SIN_PROPIEDADES con su motivo"
        )

    def test_la_lista_de_excepciones_no_se_pudre(self) -> None:
        """Si alguien le añade propiedades a un tipo de la lista, o lo retira
        del cargador, la excepción deja de tener sentido y hay que revisarla."""
        sobran = [t for t in SIN_PROPIEDADES if t not in BUILTIN_OBJECT_TYPES]
        assert not sobran, (
            f"SIN_PROPIEDADES nombra tipos que el cargador ya no acepta: "
            f"{sobran}"
        )


class TestLaGuiaSigueAlCargador:
    def test_el_total_declarado_es_el_real(self) -> None:
        """El documento cierra con «Total aceptado en `Objects`: N tipos».

        El registro de entidades es estado global y hay pruebas que lo vacían
        o le añaden tipos de mentira, así que leerlo tal cual hace que este
        caso pase o falle según el orden en que pytest sortee la suite. Aquí
        se reconstruye el registro canónico, se mide, y se deja como estaba.
        """
        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        anterior = dict(StageLoader._entity_registry)
        try:
            StageLoader._entity_registry.clear()
            entity_factory._registered = False
            entity_factory.ensure_registered()
            esperado = len(StageLoader._entity_registry) + len(BUILTIN_OBJECT_TYPES)
        finally:
            StageLoader._entity_registry.clear()
            StageLoader._entity_registry.update(anterior)

        texto = DOC.read_text(encoding="utf-8")
        m = re.search(r"Total aceptado en `Objects`: \*\*(\d+)\*\*", texto)
        assert m, "la guía ya no declara el total de tipos aceptados"
        assert int(m.group(1)) == esperado, (
            f"la guía dice {m.group(1)} tipos y el registro tiene {esperado}"
        )
