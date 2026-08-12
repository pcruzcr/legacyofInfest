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
#: Es un trinquete, no una excusa. Son 55 documentos y ~820 KiB de prosa: el
#: trabajo es real y se hace por lotes, pero mientras tanto ninguno nuevo puede
#: entrar en inglés.
PENDIENTES: frozenset[str] = frozenset({
    "03_ARCHITECTURE.md", "04_PLAYER_SPEC.md", "05_ENEMY_SPEC.md",
    "06_TMX_SPEC.md", "08_SYLLABUS_MAPPING.md", "09_HUD_SPEC.md",
    "10_LIBRARIES_AND_DEPENDENCIES.md", "11_FILTER_TOOLS_SPEC.md",
    "12_VISION_TOOLS_SPEC.md", "13_PATTERN_RECOGNITION_SPEC.md",
    "14_PROFESSOR_DELIVERABLE_MATRIX.md", "15_ACADEMIC_DEMO_SCENES.md",
    "16_WORLD_DESIGN.md", "17_BOSS_SPEC.md", "18_ENEMY_ROSTER.md",
    "19_NARRATIVE_AND_LORE.md", "20_ASSET_BIBLE.md", "21_COURSE_SCHEDULE.md",
    "22_API_CONTRACTS.md", "23_DATA_SCHEMAS.md", "26_STUDENT_TEMPLATE_SPEC.md",
    "27_ACADEMIC_RUBRICS.md", "30_ASSIGNMENT_01_STAGE_DESIGN.md",
    "31_ASSIGNMENT_02_BOSS_DESIGN.md", "32_ASSIGNMENT_03_LAB_EXERCISES.md",
    "33_ASSIGNMENT_04_FINAL_PROJECT.md", "34_CLASS_MATERIALS.md",
    "40_DIALOGUE_SYSTEM.md", "41_BESTIARY_CODEX.md", "42_CUTSCENE_SYSTEM.md",
    "43_SPEEDRUN_MODE.md", "44_BOSS_RUSH_MODE.md", "45_SWIMMING_SPEC.md",
    "46_FOG_OF_WAR.md", "48_SCREEN_TRANSITIONS.md", "49_AMBIENT_AUDIO.md",
    "52_EVENT_MAP.md", "78_SAMPLE_SYLLABUS.md", "79_TA_GUIDE.md",
    "82_ENVIRONMENT_SETUP_GUIDE.md", "BOSS_CREATION.md", "CONTRIBUTING.md",
    "ENEMY_CREATION.md", "SCENE_CREATION.md",
    "entregables.md", "eval_practica.md", "rubricas.md", "exam_bank.md",
    "lab01.md", "lab02.md", "lab03.md",
    "quiz_unit02.md", "quiz_unit04.md", "quiz_unit06.md", "quiz_unit09.md",
})


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
