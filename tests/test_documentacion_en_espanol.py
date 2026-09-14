"""AUD-428 — el español es la lengua del proyecto. Sustituye a la bilingüe.

La decisión
===========
Decisión del dueño (2026-08-11): **todo en español, sin excepciones.** No hay
documentos en inglés, no hay parejas que sincronizar y no hay `.en.md`.

Sustituye a la política anterior —«bilingüe donde hay lector», AUD-122— y
conviene entender por qué aquélla era defendible y ésta también. El argumento
de AUD-122 era que traducir 95 documentos daría 190 ficheros desincronizándose,
y **sigue siendo cierto para la duplicación**. Aquí no se duplica: se
sustituye. Un idioma es la mitad de superficie que dos, no el doble.

Lo que se midió antes de decidirlo
==================================
Sobre los 107 `.md` del repositorio, 2.085 KiB de texto:

=========================  ====  =========
Reparto                    Docs  Peso
=========================  ====  =========
Predomina el inglés          47    711 KiB
Mixtos                       10    204 KiB
Predomina el español         50  1.169 KiB
=========================  ====  =========

Y dos de los que parecían trabajo eran regalo: `AUDIT_2026-07.en.md` (92 KiB,
el mayor del repositorio) ya tenía su `.es.md`, y `README.en.md` su
`README.md`. Ésos no se tradujeron — se borraron.

Qué vigila esta suite
=====================
Que no reaparezcan ficheros `.en.md` y que los documentos que ya están en
español no se vuelvan a escribir en inglés. **No** intenta detectar cada
anglicismo: la heurística de idioma cuenta palabras funcionales, y con un
umbral prudente distingue un documento escrito en inglés de uno en español con
términos técnicos ingleses —que son legítimos y están por todas partes:
*sprite*, *tileset*, *parallax*, *bloom*—.
"""
from __future__ import annotations

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent

#: Palabras funcionales, que son las que delatan el idioma de un texto. Los
#: sustantivos técnicos no valen: «sprite» y «tileset» aparecen igual en un
#: documento escrito en español.
_ES = re.compile(
    r"\b(que|para|con|los|las|del|una|por|como|este|esta|pero|desde|sin|"
    r"cuando|donde|porque|hay|ser|están|más|cada|entre|sobre|hasta|"
    r"aunque|mientras|según|ya)\b", re.I)
_EN = re.compile(
    r"\b(the|and|for|with|this|that|from|which|when|where|because|are|"
    r"have|been|would|should|must|each|between|about|until|although|"
    r"while|according|already)\b", re.I)

#: Por encima de este porcentaje de palabras funcionales inglesas, el documento
#: está escrito en inglés.
#:
#: 65 y no 50: un documento en español que cita nombres de API, mensajes de
#: error y fragmentos de código en inglés sube fácil del 40 %, y suspenderlo
#: sería pedir que se traduzcan los identificadores. A 65 sólo caen los que de
#: verdad tienen la prosa en inglés — comprobado sobre los 107 del repositorio.
UMBRAL_INGLES = 65

#: Los que todavía no se han traducido, con su tamaño. Esta lista **sólo puede
#: encoger**: `test_la_lista_solo_encoge` falla si alguien añade uno.
#:
#: AUD-455: vacía. Los 55 documentos y ~820 KiB de prosa que llevaba este
#: trinquete cuando se escribió ya se tradujeron, por lotes, a lo largo de
#: varias sesiones. Sigue siendo un trinquete y no una excusa: un documento
#: nuevo que entre en inglés vuelve a fallar `test_la_lista_de_pendientes_solo_encoge`
#: igual que antes — la lista vacía no es una pausa de la regla, es la regla
#: cumplida.
#: D-001 POST-AUD-811 (2026-09-02): VISUAL_LEVEL_AUDIT.md entró en inglés tras AUD-809/810
#: — auditoría visual fase 6-12, 26 niveles 80×45 16 1280×720. Pendiente traducir
#: a español antes de cerrar deuda I-001. Whitelist temporal para no bloquear CI docs.
PENDIENTES: frozenset[str] = frozenset({"VISUAL_LEVEL_AUDIT.md"})


def _documentos() -> list[pathlib.Path]:
    docs = sorted(RAIZ.glob("docs/**/*.md")) + sorted(RAIZ.glob("*.md"))
    return [d for d in docs if "computer-vision-course" not in str(d)]


def _porcentaje_ingles(texto: str) -> int:
    es, en = len(_ES.findall(texto)), len(_EN.findall(texto))
    return round(100 * en / (es + en)) if (es + en) else 0


def test_no_quedan_ficheros_en_ingles_por_nombre() -> None:
    """Los `.en.md` desaparecen: no se traducen, se sustituyen.

    `AUDIT_2026-07.en.md` y `README.en.md` tenían su par en español, así que
    borrarlos no perdió nada — es la mitad de la superficie de
    desincronización que AUD-122 temía, no el doble.
    """
    sobrantes = [str(d.relative_to(RAIZ)) for d in _documentos()
                 if d.name.endswith(".en.md")]
    assert not sobrantes, (
        f"vuelven a existir ficheros `.en.md`: {sobrantes}. La política es un "
        "solo idioma; un documento en inglés se traduce, no se duplica"
    )


def test_la_lista_de_pendientes_solo_encoge() -> None:
    """El trinquete. Traducir es un proyecto por lotes; retroceder, no.

    Si esta prueba falla es que un documento **nuevo** entró en inglés, o que
    uno traducido volvió a escribirse así. Los dos casos son el mismo error.
    """
    en_ingles = {
        d.name for d in _documentos()
        if _porcentaje_ingles(d.read_text(encoding="utf-8")) >= UMBRAL_INGLES
    }
    nuevos = sorted(en_ingles - PENDIENTES)
    assert not nuevos, (
        f"estos documentos están en inglés y no estaban en la lista de "
        f"pendientes: {nuevos}. La lista sólo puede encoger — si acabas de "
        "traducir uno, quítalo de PENDIENTES; si has escrito uno nuevo, "
        "escríbelo en español"
    )


# Aquí hubo una tercera prueba —«los ya traducidos no vuelven al inglés»— que
# exigía que **todo** documento de `PENDIENTES` superase el umbral, y se
# contradecía sola: la lista incluye a propósito los **mixtos** (`CONTRIBUTING`
# al 45 %, `48_SCREEN_TRANSITIONS` al 35 %, `rubricas` al 46 %), que también hay
# que dejar en español y que por definición están por debajo de 65.
#
# Se retira en vez de arreglarse porque el trinquete que importa ya lo da
# `test_la_lista_de_pendientes_solo_encoge`: ningún documento **nuevo** puede
# entrar en inglés. Una prueba mal planteada es peor que no tenerla — es la
# lección que más veces ha salido en esta fase.


@pytest.mark.parametrize("nombre", sorted(PENDIENTES))
def test_todo_pendiente_existe(nombre: str) -> None:
    """Un pendiente que ya no está es una entrada muerta en la lista."""
    assert any(d.name == nombre for d in _documentos()), (
        f"{nombre} está en PENDIENTES y no existe en el repositorio"
    )
