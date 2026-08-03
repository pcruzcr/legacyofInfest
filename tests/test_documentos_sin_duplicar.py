"""AUD-205 — ningún documento contiene su propio cuerpo dos veces.

El defecto
==========
La convención bilingüe de este repo añade el cuerpo traducido tras un separador
``--- Traducción al Español ---``. Sobre un documento **escrito ya en español**
esa pasada no tenía nada que traducir, así que emitió una copia casi idéntica:
mismo H1, mismas secciones, y como única diferencia las etiquetas de metadatos
(``Document ID:`` → ``ID del Documento:``).

Cinco documentos quedaron así — `35_USER_MANUAL`, `36_STUDENT_MANUAL`,
`37_DEMO_QUICK_GUIDE`, `38_STAGE_BOSS_GUIDE` y `Obsidian_Home`— con entre 88,6 %
y 96,2 % de similitud entre mitades. El daño no es el tamaño del fichero: es que
cualquier edición hay que espejarla a mano en las dos copias, y nadie se acuerda.
Se comprobó que ya había ocurrido: la mitad de abajo de `36` decía «Tus
assignments» y la de arriba «Tus assignment», y la de arriba de `37` tenía dos
ideogramas chinos —``método de特征``— donde la de abajo decía «características».
Las dos copias ya habían empezado a divergir.

Por qué no basta con mirar el H1 repetido
------------------------------------------
Es la comprobación obvia y se queda corta: en `Obsidian_Home` la pasada **sí**
tradujo el titular («Obsidian Knowledge Base» → «Base de Conocimiento
Obsidian»), así que los dos H1 eran distintos y el cuerpo seguía duplicado al
88,6 %. Aquí están las dos reglas porque cada una ve un fallo que la otra no.

Por qué el umbral está en 50 %
-------------------------------
Medido sobre los 54 documentos con separador, la separación entre los dos grupos
es enorme y no hay nada en medio:

* duplicados accidentales: del **88,6 %** al 96,2 % de similitud;
* bilingües legítimos: del 0 % al **24,8 %** (inglés arriba, español abajo).

Cualquier corte entre 25 % y 88 % da el mismo veredicto. 50 % está en mitad del
hueco, así que ni un bilingüe con mucho código compartido lo dispara ni un
duplicado se escapa.
"""
from __future__ import annotations

import difflib
import pathlib
import re
import unicodedata

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"

SEPARADOR = re.compile(r"^-{2,}\s*Traducci[oó]n al Espa[nñ]ol\s*-{2,}\s*$", re.I)

#: Por encima de esto, las dos mitades son la misma y una sobra.
SIMILITUD_MAXIMA = 0.50


def _documentos() -> list[pathlib.Path]:
    return sorted(DOCS.rglob("*.md"))


def _sin_bloques_de_codigo(texto: str) -> list[str]:
    """Líneas fuera de vallas ``` y ~~~.

    Hace falta: media docena de guías traen comentarios de shell (`# 2. Crear tu
    branch`) que son sintácticamente H1 y no lo son. Contarlos daba 24 «H1» en
    `38_STAGE_BOSS_GUIDE` y convertía la comprobación en ruido.
    """
    fuera: list[str] = []
    dentro = False
    cierre = ""
    for linea in texto.splitlines():
        marca = re.match(r"^\s*(`{3,}|~{3,})", linea)
        if marca:
            simbolo = marca.group(1)[0]
            if not dentro:
                dentro, cierre = True, simbolo
                continue
            if simbolo == cierre:
                dentro = False
                continue
        if not dentro:
            fuera.append(linea)
    return fuera


# Las tres reglas recorren los ~100 documentos dentro de una sola prueba en vez
# de parametrizarse por fichero. Parametrizar daba ~300 casos —un 10 % más de
# suite— por tres comprobaciones de documentación, y el README declara el
# recuento de pruebas (CLAUDE.md §3, invariante 6): un lint no debe mover esa
# cifra. El mensaje de fallo lista todos los infractores, así que no se pierde
# precisión de diagnóstico.


def test_ningun_titular_aparece_dos_veces() -> None:
    """Un H1 repetido es la firma de un cuerpo pegado dos veces."""
    infractores: list[str] = []
    for doc in _documentos():
        titulares = [
            ln[2:].strip()
            for ln in _sin_bloques_de_codigo(doc.read_text(encoding="utf-8"))
            if ln.startswith("# ")
        ]
        repetidos = sorted({t for t in titulares if titulares.count(t) > 1})
        if repetidos:
            infractores.append(
                f"  {doc.relative_to(RAIZ).as_posix()}: {repetidos}"
            )
    assert not infractores, (
        "estos documentos repiten un titular de nivel 1, que casi siempre "
        "significa que contienen su propio cuerpo dos veces. Comprueba si hay "
        "un separador '--- Traducción al Español ---' con español a los dos "
        "lados:\n" + "\n".join(infractores)
    )


def test_la_traduccion_no_es_una_copia_del_original() -> None:
    """Si hay separador bilingüe, los dos lados tienen que decir cosas distintas.

    No se comprueba el idioma —detectarlo a ojo es frágil— sino que el texto
    difiera. Una traducción real comparte tablas y nombres de fichero pero no
    la prosa; una copia comparte todo.
    """
    infractores: list[str] = []
    revisados = 0
    for doc in _documentos():
        lineas = doc.read_text(encoding="utf-8").splitlines()
        corte = next(
            (i for i, ln in enumerate(lineas) if SEPARADOR.match(ln)), None,
        )
        if corte is None:
            continue
        arriba = [ln.strip() for ln in lineas[:corte] if ln.strip()]
        abajo = [ln.strip() for ln in lineas[corte + 1:] if ln.strip()]
        if not abajo:
            continue
        revisados += 1
        similitud = difflib.SequenceMatcher(None, arriba, abajo).ratio()
        if similitud > SIMILITUD_MAXIMA:
            infractores.append(
                f"  {doc.relative_to(RAIZ).as_posix()}: {similitud:.1%} "
                f"({len(arriba)} líneas arriba, {len(abajo)} abajo)"
            )

    # Si el separador desaparece del repo, esta prueba dejaría de comprobar
    # nada sin que nadie se entere. Mejor que falle y se borre a conciencia.
    assert revisados >= 40, (
        f"sólo {revisados} documentos declaran traducción; eran 49. Si la "
        f"convención bilingüe cambió, esta prueba ya no vigila lo que cree"
    )
    assert not infractores, (
        "estas 'traducciones' son copias del original, no traducciones. "
        "Bórralas y quédate con una sola versión, en español si es material "
        "de curso (CLAUDE.md §3, invariante 5):\n" + "\n".join(infractores)
    )


def _es_cjk(caracter: str) -> bool:
    codigo = ord(caracter)
    return (
        0x4E00 <= codigo <= 0x9FFF     # han unificado
        or 0x3400 <= codigo <= 0x4DBF  # han, extensión A
        or 0x3040 <= codigo <= 0x30FF  # kana
        or 0xAC00 <= codigo <= 0xD7AF  # hangul
    )


def test_no_se_cuela_texto_en_otro_alfabeto() -> None:
    """Ni chino, ni japonés, ni coreano en documentación de un curso en español.

    Esto no es celo ortográfico. `37_DEMO_QUICK_GUIDE.md` decía «cambia método
    de特征» —«characteristics» en chino— en la línea que explica un control de
    teclado. Un estudiante que lea esa frase no entiende qué hace la tecla `M`.
    Se coló por una pasada de traducción automática y sobrevivió porque nadie
    volvió a leer el documento entero.
    """
    infractoras: list[str] = []
    for doc in _documentos():
        for numero, linea in enumerate(
            doc.read_text(encoding="utf-8").splitlines(), 1,
        ):
            malos = [c for c in linea if _es_cjk(c)]
            if not malos:
                continue
            nombres = ", ".join(
                f"{c!r} U+{ord(c):04X} ({unicodedata.name(c, 'sin nombre')})"
                for c in dict.fromkeys(malos)
            )
            infractoras.append(
                f"  {doc.relative_to(RAIZ).as_posix()}:{numero} — {nombres}\n"
                f"    {linea.strip()[:100]}"
            )
    assert not infractoras, (
        "hay caracteres CJK en la documentación:\n" + "\n".join(infractoras)
    )
