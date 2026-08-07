"""
Module: test_los_ejemplos_de_la_doc_existen
System: tests
Academic Unit: N/A

AUD-311 — tres documentos ponían `bgm_stage1` de ejemplo, y esa pista no existe.

El caso
=======
`06_TMX_SPEC.md`, `60_GUIA_COMPLETA_DEL_MOTOR.md` y `STAGE_CREATION.md` daban
`bgm_stage1` (o `bgm_stage1_tense`) como valor de ejemplo de `bgm_track`. En
`assets/music/` hay `bgm_stage0`, `bgm_zone1`, `bgm_zone1_boss`… y ninguna que
se llame así.

Lo que le pasa a quien lo copia: `AudioManager.play_music` **no lanza**. Escribe
una línea en el registro —«no se pudo cargar música bgm_stage1»— y sigue. El
nivel se juega en silencio, el estudiante no mira el registro, y concluye que la
música «no funciona» o que su mapa está mal.

Es el mismo patrón que AUD-310 con las propiedades TMX inexistentes: el
documento promete algo, el motor calla, y el coste lo paga quien siguió las
instrucciones.

Qué fija esta prueba
====================
Que todo valor de `bgm_track` que aparezca como ejemplo en la documentación
corresponda a un fichero real de `assets/music/`. Se listan los ficheros del
disco, no una lista escrita a mano aquí — si mañana se añade una pista, la
prueba la acepta sola.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
MUSICA = RAIZ / "assets" / "music"

#: Los que enseñan a rellenar `bgm_track`.
DOCUMENTOS = (
    "docs/06_TMX_SPEC.md",
    "docs/60_GUIA_COMPLETA_DEL_MOTOR.md",
    "docs/STAGE_CREATION.md",
    "docs/23_DATA_SCHEMAS.md",
)


@pytest.fixture(scope="module")
def pistas() -> set[str]:
    disponibles = {p.stem for p in MUSICA.glob("*.wav")}
    disponibles |= {p.stem for p in MUSICA.glob("*.ogg")}
    assert disponibles, f"no hay ninguna pista en {MUSICA}"
    return disponibles


@pytest.mark.parametrize("ruta", DOCUMENTOS)
def test_los_bgm_de_ejemplo_existen(ruta: str, pistas: set[str]) -> None:
    fichero = RAIZ / ruta
    if not fichero.exists():
        pytest.skip(f"{ruta} ya no existe")

    texto = fichero.read_text(encoding="utf-8", errors="replace")

    # Cualquier `bgm_*` citado, venga en una tabla, en un XML de ejemplo o en
    # prosa. El prefijo es la convención del proyecto y no hay pistas sin él.
    # `bgm_track` es el nombre de la propiedad de mapa, no una pista, y
    # aparece en cada tabla que la documenta.
    NO_SON_PISTAS = {"bgm_track"}
    citadas = set(re.findall(r"\b(bgm_[a-z0-9_]+)\b", texto)) - NO_SON_PISTAS
    fantasma = sorted(c for c in citadas if c not in pistas)

    assert not fantasma, (
        f"{ruta} pone de ejemplo pistas que no están en assets/music/: "
        f"{fantasma}. Quien copie el ejemplo juega en silencio, porque "
        f"`play_music` no lanza: sólo lo anota en el registro.\n"
        f"Disponibles: {sorted(pistas)}"
    )
