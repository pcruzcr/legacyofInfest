"""AUD-259 — `BossSpawn`: el tipo que la especificación pedía y el motor no aceptaba.

El defecto
==========
`17_BOSS_SPEC.md` §8.2 dice, como requisito de todo mapa de jefe:

    Each boss stage TMX must contain:
    - `BossSpawn` object at the boss entry point

El cargador **no conocía ese tipo**. Un estudiante que siguiera su propia
especificación al pie de la letra recibía un aviso de «tipo desconocido»
(AUD-055) y su jefe no aparecía. La §0 del documento lo avisaba desde AUD-150 y
lo dejaba abierto; esto lo cierra.

Cómo se resuelve, y por qué así
-------------------------------
`BossSpawn` no construye «un jefe» —el motor no sabe cuál—: **declara dónde
entra el jefe que el mapa nombra**, con la propiedad `boss`. Se resuelve por el
mismo registro de entidades que ya usan `BossVenado` y compañía, así que un
`BossSpawn` con `boss="BossVenado"` produce exactamente la misma entidad que
escribir `BossVenado` como tipo.

Es **aditivo**: ningún TMX entregado declara `BossSpawn`, así que ningún nivel
ya calificado cambia (invariante 2 de `CLAUDE.md`). Los tres jefes existentes
siguen colocándose con su tipo propio y no se toca ni uno.

Un `BossSpawn` sin `boss`, o con un nombre que no está registrado, **avisa**
por el mismo camino de diagnóstico que cualquier otra errata de Tiled. Callarse
sería reproducir el defecto que se está arreglando: el estudiante escribe algo
razonable y no pasa nada, sin explicación.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.stage_loader import StageLoader


class _JefeDeMentira:
    """Sustituto registrable: el registro sólo necesita algo construible."""

    def __init__(self, spawn_position: pygame.Vector2, **kwargs: object) -> None:
        self.position = spawn_position
        self.kwargs = kwargs


class _ObjetoTiled:
    def __init__(self, tipo: str, x: float = 100.0, y: float = 200.0,
                 **props: object) -> None:
        self.type = tipo
        self.name = f"{tipo}_1"
        self.id = 7
        self.x, self.y = x, y
        self.width = self.height = 32
        self.properties = props


@pytest.fixture
def registro():
    StageLoader.register_entity("JefeDeMentira", _JefeDeMentira)  # type: ignore[arg-type]
    yield
    StageLoader._entity_registry.pop("JefeDeMentira", None)
    StageLoader._registro_historico.pop("JefeDeMentira", None)


class TestElTipoExiste:
    def test_el_cargador_lo_reconoce(self) -> None:
        """Antes de esto, `BossSpawn` no estaba entre los tipos conocidos."""
        from src.framework.stage.tmx_diagnostics import known_object_types

        assert "BossSpawn" in known_object_types(list(StageLoader._entity_registry))

    def test_la_especificacion_deja_de_mentir(self) -> None:
        """§8.2 lo exige en todo mapa de jefe; ahora el motor lo acepta."""
        from pathlib import Path

        spec = (Path(__file__).resolve().parents[1] / "docs"
                / "17_BOSS_SPEC.md").read_text(encoding="utf-8")
        assert "BossSpawn" in spec
        assert "el motor no lo\nacepta" not in spec, (
            "la §0 sigue diciendo que el motor no acepta BossSpawn"
        )


class TestLoQueConstruye:
    def test_declara_el_jefe_que_nombra(self, registro) -> None:
        entidades: list[object] = []
        obj = _ObjetoTiled("BossSpawn", boss="JefeDeMentira")

        StageLoader._handle_boss_spawn_para_pruebas(obj, entidades)

        assert len(entidades) == 1
        assert isinstance(entidades[0], _JefeDeMentira)

    def test_la_posicion_es_la_del_objeto(self, registro) -> None:
        entidades: list[object] = []
        obj = _ObjetoTiled("BossSpawn", x=640.0, y=320.0, boss="JefeDeMentira")

        StageLoader._handle_boss_spawn_para_pruebas(obj, entidades)

        assert entidades[0].position.x == pytest.approx(640.0)
        assert entidades[0].position.y == pytest.approx(320.0)

    def test_sin_boss_no_construye_nada(self, registro) -> None:
        entidades: list[object] = []

        problema = StageLoader._handle_boss_spawn_para_pruebas(
            _ObjetoTiled("BossSpawn"), entidades)

        assert entidades == []
        assert problema is not None, "un BossSpawn sin `boss` tiene que avisar"

    def test_un_jefe_que_no_existe_avisa(self, registro) -> None:
        entidades: list[object] = []

        problema = StageLoader._handle_boss_spawn_para_pruebas(
            _ObjetoTiled("BossSpawn", boss="BossQueNoExiste"), entidades)

        assert entidades == []
        assert problema is not None


class TestLoQueNoCambia:
    def test_ningun_mapa_entregado_lo_declara_como_tipo(self) -> None:
        """Si alguno ya lo usara **como `type`**, esto no sería aditivo.

        Se mira el atributo, no el texto del fichero: `stage3_4_boss_gavilan`
        llama `BossSpawn_01` a su objeto y le pone `type="BossGavilan"`, que es
        precisamente lo que un estudiante hace cuando la especificación pide un
        nombre que el motor no acepta. Buscar la cadena a secas daba ese mapa
        como falso positivo.
        """
        import re
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[1]
        con_spawn = []
        for p in (raiz / "assets" / "maps").rglob("*.tmx"):
            texto = p.read_text(encoding="utf-8", errors="replace")
            for trozo in re.finditer(r"<object\b[^>]*", texto):
                tipo = re.search(r'\s(?:type|class)="([^"]+)"', trozo.group(0))
                if tipo and tipo.group(1) == "BossSpawn":
                    con_spawn.append(p.name)
        assert not con_spawn, f"ya lo usaban: {con_spawn}"
