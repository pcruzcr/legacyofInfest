"""
Las rutas que cita la documentación existen, y el índice maestro las lista todas.

AUD-168 — el hallazgo
=====================
La documentación de este repositorio cita rutas de fichero constantemente: la
guía del estudiante dice dónde poner su nivel, `22_API_CONTRACTS.md` dice en qué
módulo vive cada clase, `20_ASSET_BIBLE.md` dice qué script valida los sprites.
Ninguna de esas citas estaba comprobada por nada, y **veinticuatro habían dejado
de apuntar a algo**:

============================================  ==============================
Lo que decía el documento                     Dónde está de verdad
============================================  ==============================
`tools/validate_assets.py`  (en 3 documentos) `scripts/validate_assets.py`
`src/stages/boss_gavilan/boss_gavilan.py`     `src/stages/stage3_4_boss_gavilan/`
`src/framework/core/game_context.py`          `src/engine/core/game_context.py`
`assets/maps/stage0.tmx`                      `assets/maps/stage0/stage0.tmx`
`tests/fixtures/reference_sprite_32x32.png`   no existe: son superficies
                                              generadas en `conftest.py`
============================================  ==============================

Un estudiante que sigue `20_ASSET_BIBLE.md` al pie de la letra ejecuta
`python tools/validate_assets.py` y recibe un *No such file or directory*. La
documentación no le mintió sobre nada complicado — le mintió sobre dónde está
un fichero, que es la clase de error que nadie revisa porque parece imposible.

Por qué una prueba y no una revisión
------------------------------------
Porque las rutas se rompen por movimientos legítimos. `validate_assets.py` se
movió de `tools/` a `scripts/` por una razón buena, y los cuatro documentos que
lo citaban se quedaron atrás en silencio. Ninguna revisión humana repetida cada
mes va a atrapar eso; una prueba que recorre los 93 documentos, sí.

Los marcadores de posición
--------------------------
El material docente enseña con ejemplos: «pon tu mapa en
`assets/maps/tu_stage.tmx`». Esos ficheros no existen ni deben existir. Están
listados uno a uno en `MARCADORES_DE_POSICION`, con la regla de que añadir uno
es declarar que es un ejemplo y no un descuido. La lista es explícita a
propósito: un patrón comodín del tipo `*your*` acabaría tapando una ruta rota
de verdad el día que alguien llame `your_config.py` a algo real.
"""
from __future__ import annotations

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent

#: Documentos que se revisan. Todo `docs/*.md` más los ficheros de raíz que
#: describen el repositorio a alguien que llega de fuera.
DOCUMENTOS: list[pathlib.Path] = [
    *sorted((RAIZ / "docs").glob("*.md")),
    RAIZ / "README.md",
    RAIZ / "CONTRIBUTING.md",
    RAIZ / "KNOWN_GAPS.md",
    RAIZ / "CLAUDE.md",
    # AUD-179: no es markdown, pero son 30 líneas de comentario que explican el
    # trinquete de tipos y citan rutas. Una de ellas —la prueba que impide que
    # la lista encoja— nombraba un fichero que no existe, y este guardián no
    # miraba aquí. Un fichero de configuración con prosa dentro envejece igual
    # que un documento.
    RAIZ / "mypy_scope.txt",
]

#: Raíces de primer nivel que son rutas del repositorio y no prosa.
#:
#: `docs` entró en AUD-322: el borrado deliberado de 36 documentos dejó quince
#: citas vivas a documentos retirados —tablas de "documentos relacionados",
#: registros históricos y listas de fuentes— y el guardián, que sólo miraba
#: rutas de código y recursos, no las veía. Un documento que cita a otro que
#: ya no existe envejece exactamente igual que un documento que cita un
#: módulo movido: el lector concluye que el enlace roto es culpa suya.
_RAICES = "docs|src|scripts|tools|tests|assets|locale|data|colab|exams|web"

#: El `(?<![\w/.-])` importa: sin él, `loi-tools/editor/stage_wizard.py` —una
#: propuesta de un repositorio que aún no existe, en 50_IMPROVEMENT_ROADMAP—
#: se leería como `tools/editor/stage_wizard.py` y saldría como ruta rota.
_PATRON = re.compile(
    rf"(?<![\w/.-])((?:{_RAICES})/[A-Za-z0-9_./-]+"
    r"\.(?:py|md|json|tmx|tsx|png|ogg|wav|pkl|csv|toml|txt|yml|ipynb))"
)

#: Ejemplos didácticos. No existen y no deben existir: son el hueco que el
#: estudiante rellena con el nombre de su nivel, su jefe o su escena.
#:
#: Añadir una entrada aquí es afirmar «esto es un ejemplo». Si no lo es, la
#: respuesta correcta es arreglar la ruta en el documento.
MARCADORES_DE_POSICION: frozenset[str] = frozenset({
    # AUD-457: los ejemplos de las dos entregas se renombraron al español
    # (AUD-428) — `your_stage`→`tu_escenario`, `boss_your_boss`→`tu_jefe` — y
    # los viejos en inglés salieron de aquí con la misma migración.
    "assets/maps/tu_escenario.tmx",
    "assets/maps/tu_jefe.tmx",
    "assets/maps/mi_nivel/mi_nivel.tmx",
    # AUD-431: el ejemplo de `validate_tmx.py` en la especificación traducida.
    "assets/maps/mi_mapa/mi_mapa.tmx",
    "assets/maps/tu_stage.tmx",
    "src/stages/tu_jefe/tu_jefe.py",
    "src/stages/mi_nivel/mi_nivel.py",
    # AUD-429: el ejemplo de registro de la guía de enemigos traducida.
    "src/stages/mi_nivel/mi_enemigo.py",
    "tests/test_stageN_smoke.py",
    # AUD-XXX: M7 planificado — tests aún no existen, citados como objetivo.
    "tests/test_world_simulation.py",
    "tests/test_environment_state.py",
    # AUD-839 — referencias hacia adelante y ejemplos, con la misma lógica que
    # los dos de arriba: el día que materialicen, `test_ningun_marcador_existe_
    # ya` obliga a sacarlos de aquí.
    # 45_SWIMMING_SPEC cita su verificación prevista (el HUD de oxígeno de
    # AUD-553 existe; la prueba dedicada, todavía no).
    "tests/test_oxigeno_del_hud.py",
    # Stage 4.1b/4.1c en construcción (docs 13b/13c): los docs ya los citan.
    "tests/test_stage4_1b.py",
    "tests/test_stage4_1c.py",
    "src/stages/stage4_1b/stage4_1b.py",
    "src/stages/stage4_1b/trazado.py",
    "tools/generate_stage4_1b.py",
    # 95_GUIA_ENTREGA_3: el TMX que el estudiante sustituye por el suyo.
    "assets/maps/tu_stage/tu_stage.tmx",
})

#: Módulos retirados que la documentación cita **como historia**: «esto existía
#: y se quitó por esta razón». Borrar la mención sería borrar el porqué, y el
#: porqué es lo que impide que alguien vuelva a crearlos.
#:
#: La diferencia con un marcador de posición: éstos existieron. Si vuelven a
#: existir, `test_ningun_retirado_ha_vuelto` avisa — porque entonces la nota
#: histórica pasa a ser falsa.
MODULOS_RETIRADOS: frozenset[str] = frozenset({
    # AUD-111: cinco clases de transición con cero usos en todo el árbol.
    "src/engine/scene/transitions.py",
    # AUD-308: borrado deliberado de la documentación de julio de 2026. El
    # reporte 87 §21.2 explica la decisión y cita el `git show` para recuperar
    # el fichero: la mención es historia, no una ruta que deba existir.
    "docs/VERIFICACION_FINAL.md",
    # AUD-428: el proyecto pasa a español como lengua única y la política
    # bilingüe se retira. Los tres se citan como historia —el porqué de la
    # decisión anterior sigue siendo interesante— y ya no existen.
    "tests/test_documentacion_bilingue.py",
    "docs/AUDIT_2026-07.en.md",
    # AUD-523: el sprite de checkpoint se retira por completo — el haz de luz
    # (AUD-522/523) es ahora el checkpoint en los 26 escenarios, sin sprite
    # ni fallback. La mención queda como historia de por qué ya no existe.
    "assets/sprites/shared/checkpoint.png",
    # AUD-168: el recorte de hojas de sprites lo hace `AssetLoader`; el
    # empaquetado, `SpriteAtlas`. `docs/22_API_CONTRACTS.md` §5.3 lo cita como
    # historia del retiro (la cita-histórica explica el porqué, y el porqué es
    # lo que impide que alguien vuelva a crearlo).
    "src/engine/utils/spritesheet.py",
    # AUD-587: el modelo pickle del profesorado se retira — el runtime entrena
    # el modelo de referencia desde `assets/datasets/sample_dataset.npz` y lo
    # cachea fuera del repositorio, así que distribuir el binario sólo servía
    # para que alguien lo deserializara por error. `docs/93` lo cita como
    # evidencia del hallazgo F2: historia, no una ruta que deba existir.
    "assets/models/professor_sample.pkl",
    # AUD-237: el tileset del cementerio genérico se retiró al rehacer stage4_1
    # con tilesets por fase; KNOWN_GAPS GAP-026 lo cita como historia.
    "assets/tilesets/tileset_cemetery.png",
    # AUD-839 — historia del cleanup AUD-800 y de tracks retirados: los docs de
    # auditoría los citan como registro de lo que había y por qué se fue.
    # Borrados en el propio AUD-800 (manifiesto e inventario los documentan):
    "docs/CERTIFICATION_CONSISTENCY_REPORT.md",
    "docs/PLAYER_CONTACT_SURFACE_AUDIT.md",
    "scripts/audit_certification_consistency.py",
    # Duplicado del tileset del Gavilán: AUD-800 lo clasificó P3 y se archivó
    # después; el canónico es assets/tilesets/tileset_gavilan_ciudad.tsx.
    "assets/tileset_gavilan_ciudad.tsx",
    # Playtest humano 001: sus resultados vivieron en este doc hasta que se
    # plegaron en RELEASE_READINESS y PROJECT_IMPROVEMENT_REGISTER.
    "docs/HUMAN_PLAYTEST_001.md",
    # Pruebas de tracks cerrados cuyos resultados quedaron por escrito en los
    # docs que las citan (94, STAGE_SPATIAL_INTEGRITY_AUDIT):
    "tests/test_el_mirador_de_la_fase_6.py",
    "tests/test_stage_spatial_integrity.py",
    # Pruebas por-fase del track privado del stage 4.1 original: salieron del
    # árbol con la desvinculación del track y sus resultados quedaron
    # registrados en KNOWN_GAPS. El 4.1 entregado se verifica hoy con
    # tests/test_stage4_1.py y tests/test_stage41_recorrido.py.
    "tests/test_aud_554_pasos_de_grava_ahogado_y_voz_del_venado.py",
    "tests/test_el_bosque_observa_en_la_fase_2.py",
    "tests/test_el_bus_de_reverberacion_de_la_fase_6.py",
    "tests/test_el_canto_orienta_en_la_planicie.py",
    "tests/test_el_despertar_de_la_fase_6.py",
    "tests/test_el_escenario_observa.py",
    "tests/test_el_horizonte_y_la_despedida.py",
    "tests/test_el_menu_de_pausa_abre_inventario.py",
    "tests/test_el_musgo_resbala.py",
    "tests/test_el_repiso_que_termina_en_musgo.py",
    "tests/test_el_secreto_de_los_tres_espiritus.py",
    "tests/test_el_silencio_poblado_de_la_fase_1.py",
    "tests/test_gap_070_audio_del_4_1.py",
    "tests/test_la_lluvia_no_se_queda_pegada.py",
    "tests/test_la_lluvia_vintage_de_la_fase_4.py",
    "tests/test_la_luna_esconde_cosas.py",
    "tests/test_la_musica_del_4_1_entra_tarde.py",
    "tests/test_la_procesion_y_la_multitud.py",
    "tests/test_la_sombra_varia_y_el_bosque_cambia.py",
    "tests/test_la_tormenta_paneada_de_la_fase_3.py",
    "tests/test_la_tumba_que_nadie_reclama.py",
    "tests/test_la_tumba_susurra_y_el_fantasma_recuerda.py",
    "tests/test_las_costillas_son_navegables.py",
    # AUD-839 — D-04/AV-29: el paquete fantasma `src/stages/stage2_4/` (una
    # BossReyScene de prototipo cuyo TMX nunca existió) se retiró; el Rey
    # completo de tres fases vive ahora en `src/stages/boss_rey/` y es el que
    # el registro carga. La fila AV-29 del doc 102 conserva la cita como
    # historia del hallazgo.
    "assets/maps/stage2_4/stage2_4.tmx",
    "src/stages/stage2_4/stage2_4.py",
})

#: Estado del jugador: ficheros que el juego **escribe al jugarse** y que
#: `.gitignore` mantiene fuera del control de versiones — AUD-444.
#:
#: No son ejemplos didácticos (existen de verdad, en cuanto alguien juega) ni
#: módulos retirados (no se han quitado). Son la tercera cosa: rutas que un
#: documento cita con razón y que en un árbol limpio no están.
#:
#: Se descubrió al borrar los datos de partida para empezar de cero: tres
#: documentos citaban `data/inventory.json` y la prueba se puso roja. Pero el
#: fichero está en `.gitignore` desde AUD-197, así que **un clon recién hecho
#: falla igual**: esta prueba llevaba tiempo dependiendo de que quien la
#: ejecutara hubiera jugado antes en esa máquina.
#:
#: La diferencia con un marcador de posición importa al leer la lista: un
#: marcador dice «esto nunca existirá»; esto dice «esto existe cuando se
#: juega». Confundirlos invitaría a borrar el fichero del `.gitignore` para
#: «arreglar» la prueba, que es exactamente lo que AUD-157 deshizo.
ESTADO_DE_EJECUCION: frozenset[str] = frozenset({
    "data/inventory.json",
    "data/score.json",
    # AUD-839 — lo escribe `tools/build_dataset.py` al entrenar; 95 lo cita
    # como salida del comando, no como fichero del árbol.
    "data/dataset.json",
})

_EXENTAS = MARCADORES_DE_POSICION | MODULOS_RETIRADOS | ESTADO_DE_EJECUCION


#: Bloques cercados que son **volcados**, no afirmaciones: salida de un
#: validador, de un `pytest`, de un `git log`. Un volcado cita la ruta que había
#: el día que se ejecutó, y reescribirlo para que la prueba pase sería falsear
#: una medición. Los bloques con lenguaje —```python, ```powershell— sí se
#: revisan: eso es código que alguien va a copiar.
#:
#: Es la misma distinción que hace `test_documentacion_bilingue.py` cuando
#: excluye los bloques cercados antes de comparar cifras entre idiomas.
_FENCE = re.compile(r"^```([A-Za-z0-9_+-]*)\s*$", re.M)
_INDENTADO = re.compile(r"^(?: {4,}|\t).*$", re.M)

_LENGUAJES_DE_CODIGO = {
    "python", "py", "powershell", "ps1", "bash", "sh", "shell",
    "yaml", "yml", "toml", "json", "xml", "ini", "make",
}


def _sin_volcados(texto: str) -> str:
    """Quita volcados de consola: bloques sin lenguaje y bloques indentados."""
    salida: list[str] = []
    dentro = False
    es_codigo = False
    for linea in texto.splitlines():
        cerca = _FENCE.match(linea)
        if cerca:
            if not dentro:
                dentro, es_codigo = True, cerca.group(1).lower() in _LENGUAJES_DE_CODIGO
            else:
                dentro, es_codigo = False, False
            continue
        if dentro and not es_codigo:
            continue
        salida.append(linea)
    return _INDENTADO.sub("", "\n".join(salida))


def _rutas_citadas(documento: pathlib.Path) -> set[str]:
    texto = _sin_volcados(documento.read_text(encoding="utf-8", errors="replace"))
    return set(_PATRON.findall(texto))


class TestLasRutasCitadasExisten:
    @pytest.mark.parametrize(
        "documento", DOCUMENTOS, ids=[d.name for d in DOCUMENTOS]
    )
    def test_el_documento_no_apunta_a_ficheros_inexistentes(
        self, documento: pathlib.Path
    ) -> None:
        if not documento.exists():  # pragma: no cover - red de seguridad
            pytest.skip(f"{documento.name} no está en el árbol")

        rotas = sorted(
            ruta
            for ruta in _rutas_citadas(documento)
            if ruta not in _EXENTAS and not (RAIZ / ruta).exists()
        )

        assert not rotas, (
            f"{documento.name} cita rutas que no existen: {rotas}. "
            f"Si son ejemplos didácticos, decláralos en "
            f"MARCADORES_DE_POSICION; si son módulos retirados citados como "
            f"historia, en MODULOS_RETIRADOS; si no, corrige la ruta."
        )


class TestLosMarcadoresSiguenSiendoMarcadores:
    def test_ningun_marcador_existe_ya(self) -> None:
        """Un marcador que se convierte en fichero real deja de ser marcador.

        Si alguien crea `assets/maps/tu_stage.tmx` de verdad, la exención deja
        de proteger un ejemplo y pasa a ocultar la ruta de un fichero real.
        """
        materializados = sorted(
            m for m in MARCADORES_DE_POSICION if (RAIZ / m).exists()
        )
        assert not materializados, (
            f"estos marcadores ya existen en el árbol y deben salir de "
            f"MARCADORES_DE_POSICION: {materializados}"
        )

    def test_ningun_marcador_sobra(self) -> None:
        """Una exención que ya nadie usa es ruido que tapa el siguiente fallo."""
        citadas: set[str] = set()
        for documento in DOCUMENTOS:
            if documento.exists():
                citadas |= _rutas_citadas(documento)
        huerfanos = sorted(_EXENTAS - citadas)
        assert not huerfanos, (
            f"ningún documento cita ya estas exenciones; retíralas de "
            f"MARCADORES_DE_POSICION / MODULOS_RETIRADOS: {huerfanos}"
        )

    def test_ningun_retirado_ha_vuelto(self) -> None:
        """Si el módulo retirado reaparece, la nota histórica pasa a mentir."""
        resucitados = sorted(m for m in MODULOS_RETIRADOS if (RAIZ / m).exists())
        assert not resucitados, (
            f"la documentación dice que estos módulos se retiraron y vuelven a "
            f"existir: {resucitados}. O se actualiza la nota, o se retira el "
            f"módulo otra vez"
        )


class TestElIndiceMaestroEstaCompleto:
    """AUD-169 — trece documentos no aparecían en el índice.

    `docs/00_MASTER_INDEX.md` se declara a sí mismo «la lista autoritativa».
    Una lista autoritativa incompleta es peor que no tenerla: quien la consulta
    concluye que el documento que falta no existe. Faltaban `52_EVENT_MAP.md`,
    `67_CURVA_DE_DIFICULTAD.md`, `68_AUDITORIA_DE_INGENIERIA.md` y diez más.
    """

    #: El propio índice, y los ficheros de Obsidian que no son documentación
    #: del proyecto sino configuración de la herramienta de notas.
    FUERA_DEL_INDICE: frozenset[str] = frozenset({
        "00_MASTER_INDEX.md",
        "Obsidian_Home.md",
        "README.md",
    })

    def test_todos_los_documentos_estan_indexados(self) -> None:
        indice = (RAIZ / "docs" / "00_MASTER_INDEX.md").read_text(encoding="utf-8")
        ausentes = sorted(
            p.name
            for p in (RAIZ / "docs").glob("*.md")
            if p.name not in self.FUERA_DEL_INDICE and p.name not in indice
        )
        assert not ausentes, (
            f"docs/00_MASTER_INDEX.md se declara la lista autoritativa y no "
            f"menciona estos documentos: {ausentes}"
        )
