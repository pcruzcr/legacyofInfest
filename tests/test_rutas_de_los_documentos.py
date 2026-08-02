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
    RAIZ / "README.en.md",
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
_RAICES = "src|scripts|tools|tests|assets|locale|data|colab|exams|web"

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
    "assets/maps/boss_your_boss.tmx",
    "assets/maps/mi_nivel/mi_nivel.tmx",
    "assets/maps/tu_stage.tmx",
    "assets/maps/your_stage.tmx",
    "assets/maps/your_stage_name.tmx",
    "src/stages/mi_nivel/mi_nivel.py",
    "src/stages/stageX/boss_your_boss.py",
    "tests/test_stageN_smoke.py",
})

#: Módulos retirados que la documentación cita **como historia**: «esto existía
#: y se quitó por esta razón». Borrar la mención sería borrar el porqué, y el
#: porqué es lo que impide que alguien vuelva a crearlos.
#:
#: La diferencia con un marcador de posición: éstos existieron. Si vuelven a
#: existir, `test_ningun_retirado_ha_vuelto` avisa — porque entonces la nota
#: histórica pasa a ser falsa.
MODULOS_RETIRADOS: frozenset[str] = frozenset({
    # AUD-098: segunda implementación muerta de AssetLoader.load_sprite_sheet.
    "src/engine/utils/spritesheet.py",
    # AUD-111: cinco clases de transición con cero usos en todo el árbol.
    "src/engine/scene/transitions.py",
})

_EXENTAS = MARCADORES_DE_POSICION | MODULOS_RETIRADOS


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
