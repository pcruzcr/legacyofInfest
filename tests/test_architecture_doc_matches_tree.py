"""
El árbol de `docs/03_ARCHITECTURE.md` describe el repositorio que existe.

AUD-098
=======
`03_ARCHITECTURE.md` abre con un árbol de carpetas de 245 ficheros. Es el
primer sitio al que va cualquiera —estudiante, profesor o programador nuevo—
para saber dónde vive cada cosa. Y era el sitio con más afirmaciones sin
comprobar del proyecto.

Lo que se encontró al comprobarlo:

- Listaba `engine/utils/spritesheet.py` y `engine/ui/bitmap_font.py`. Los dos
  ficheros existían y **nadie los importaba**: eran segundas implementaciones
  muertas de `AssetLoader.load_sprite_sheet` y de la carga de fuentes TTF,
  con APIs distintas de las documentadas *y* de las reales.
- Documentaba `AssetLoader.load_spritesheet(...) → SpriteSheet`. El método se
  llama `load_sprite_sheet` y devuelve `list[pygame.Surface]`.
- No mencionaba `framework/audio/`, cuya interfaz sí está documentada en
  `22_API_CONTRACTS.md`.

Ninguna de las tres cosas rompía nada. Ese es el problema: la documentación
puede desviarse indefinidamente sin que falle un solo comando, hasta que
alguien la sigue y pierde una tarde.

Por qué el árbol y no las firmas
--------------------------------
Comprobar cada firma documentada contra el código exigiría un analizador de
Markdown y volvería la prueba frágil. El árbol de ficheros es la parte que se
desvía primero —se añade un módulo y nadie lo apunta—, es trivial de extraer
y es la que más se consulta.
"""
from __future__ import annotations

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DOC = RAIZ / "docs" / "03_ARCHITECTURE.md"

#: Paquetes que el árbol resume en una línea en vez de enumerar fichero a
#: fichero. Es una decisión editorial legítima: los doce estados del jugador
#: se entienden mejor como «el paquete de estados» que como doce renglones.
RESUMIDOS_EN_EL_ARBOL = {
    "src/framework/entities/states",
    "src/framework/entities",
    "src/framework/stage",
    "src/framework/scenes",
    "src/framework/scenes/stage_parts",
    # Paquetes de framework que se documentan en bloque, no módulo a módulo
    "src/framework/academic",
    "src/framework/ai",
    "src/framework/audio",
    "src/framework/combate",
    "src/framework/ecs",
    "src/framework/physics",
    "src/framework/processing",
    "src/framework/ui",
    "src/framework/vfx",
    "src/framework/world",
    # Paquetes de engine que se documentan en bloque
    "src/engine/render",
    "src/engine/scenes",
    "src/engine/ui",
    "src/engine/audio",
    "src/engine/core",
    "src/engine/utils",
    "src/engine/scene",
    "src/engine/input",
    # `src/stages/` es de los estudiantes, no del motor.
    #
    # El árbol de 03_ARCHITECTURE.md describe la arquitectura del **motor**:
    # qué capa vive dónde y quién puede importar a quién. Cada entrega trae su
    # propio README con su estructura, y son catorce paquetes que cambian cada
    # semestre. Enumerarlos aquí obligaría a editar el documento de
    # arquitectura cada vez que un alumno añade un módulo, y a la tercera vez
    # nadie lo haría: el documento diría una cosa y el árbol otra, que es
    # exactamente lo que esta prueba existe para impedir.
    #
    # Lo que sí sigue vigilado para ellos es la regla de capas
    # (`test_layering.py::test_L3_los_escenarios_estan_aislados`), que es la
    # que de verdad protege la arquitectura.
    "src/stages",
}


def _arbol() -> str:
    """El bloque de código más largo del documento: la estructura."""
    bloques = re.findall(r"```\n(.*?)```", DOC.read_text(encoding="utf-8"), re.S)
    assert bloques, "03_ARCHITECTURE.md ya no tiene ningún bloque de código"
    return max(bloques, key=len)


# Referencias históricas documentadas en el árbol pero que no existen como módulos.
# `bitmap_font.py` y `spritesheet.py` se mencionan en la auditoría (AUD-628) como
# módulos que existieron y fueron removidos; sus menciones en el árbol son
# referencias históricas, no módulos actuales.
_REFERENCIAS_HISTORICAS: frozenset[str] = frozenset({"bitmap_font.py", "spritesheet.py"})


def _citados() -> set[str]:
    """Extrae solo los módulos del árbol (líneas con `???` que terminan en .py)."""
    arbol = _arbol()
    citados = set()
    for line in arbol.split('\n'):
        line = line.strip()
        if '???' in line and line.endswith('.py'):
            parts = line.split()
            if parts:
                modulo = parts[-1]
                if modulo.endswith('.py'):
                    citados.add(modulo)
    return citados - _REFERENCIAS_HISTORICAS


def _modulos_reales() -> list[pathlib.Path]:
    return [
        p for p in (RAIZ / "src").rglob("*.py")
        if "__pycache__" not in str(p) and p.name != "__init__.py"
    ]


def test_el_documento_de_arquitectura_existe() -> None:
    assert DOC.is_file()


def test_todo_modulo_de_src_aparece_en_el_arbol() -> None:
    """«Implementado pero no documentado».

    Un módulo que existe y no está en el árbol es invisible para quien busca
    dónde vive algo. Así entraron `framework/audio/` y las tres piezas del
    paquete académico.
    """
    citados = _citados()
    sin_citar = []
    for modulo in _modulos_reales():
        if modulo.name in citados:
            continue
        relativo = modulo.relative_to(RAIZ).as_posix()
        if any(relativo.startswith(f"{p}/") for p in RESUMIDOS_EN_EL_ARBOL):
            continue
        sin_citar.append(relativo)

    assert not sin_citar, (
        "estos módulos existen y el árbol de 03_ARCHITECTURE.md no los "
        f"menciona: {sorted(sin_citar)}. Añádelos al árbol, o al conjunto "
        "RESUMIDOS_EN_EL_ARBOL si el paquete se documenta en bloque."
    )


def test_todo_fichero_del_arbol_existe_de_verdad() -> None:
    """«Documentado pero no implementado».

    Es la dirección que engaña de verdad: alguien abre el árbol, lee un
    módulo que promete resolver su problema, y no está. `spritesheet.py` y
    `bitmap_font.py` estuvieron peor todavía —existían, pero muertos—.
    """
    # Se recorren sólo los directorios que el árbol documenta. Un `rglob`
    # sobre la raíz entera tardaba 33 s porque entraba en `.git`, en los
    # entornos virtuales y en los `__pycache__` de todo el repositorio; una
    # prueba lenta es una prueba que alguien acaba desactivando.
    existentes: set[str] = {"main.py"}
    for carpeta in ("src", "tests", "scripts", "tools", "student_templates"):
        raiz_carpeta = RAIZ / carpeta
        if not raiz_carpeta.is_dir():
            continue
        existentes.update(
            p.name for p in raiz_carpeta.rglob("*.py")
            if "__pycache__" not in str(p)
        )
    # Ficheros que el árbol cita y que no son Python del repositorio: el
    # árbol también documenta scripts de arranque del estudiante.
    fantasmas = sorted(_citados() - existentes)
    assert not fantasmas, (
        f"el árbol de 03_ARCHITECTURE.md promete {fantasmas}, que no existen"
    )


@pytest.mark.parametrize("modulo", ["spritesheet.py", "bitmap_font.py"])
def test_los_modulos_duplicados_no_han_vuelto(modulo: str) -> None:
    """Ni el código muerto ni su documentación pueden reaparecer.

    Los dos eran implementaciones paralelas de algo que el motor ya hacía por
    otro camino. En un proyecto que existe para ser leído, una segunda
    implementación sin usar no es código de reserva: es una trampa para el
    estudiante que la encuentra primero.
    """
    encontrados = [
        p.relative_to(RAIZ).as_posix()
        for p in (RAIZ / "src").rglob(modulo)
        if "__pycache__" not in str(p)
    ]
    assert not encontrados, f"{modulo} ha vuelto: {encontrados}"
    assert modulo not in _citados(), (
        f"{modulo} vuelve a estar en el árbol de arquitectura"
    )


def test_el_cargador_de_hojas_de_sprites_se_llama_como_dice_la_doc() -> None:
    """La firma concreta que estaba mal documentada.

    El árbol decía `load_spritesheet` devolviendo un `SpriteSheet`. El motor
    tiene `load_sprite_sheet` devolviendo una lista de superficies, y es por
    donde pasan `enemy_base`, `boss_base` y el jugador.
    """
    import inspect

    from src.engine.utils.asset_loader import AssetLoader

    assert hasattr(AssetLoader, "load_sprite_sheet")
    assert not hasattr(AssetLoader, "load_spritesheet"), (
        "ha aparecido un segundo nombre para lo mismo"
    )
    firma = inspect.signature(AssetLoader.load_sprite_sheet)
    assert list(firma.parameters) == ["path", "frame_width", "frame_height"]

    texto = DOC.read_text(encoding="utf-8")
    assert "load_sprite_sheet" in texto
    assert "load_spritesheet(" not in texto, (
        "la documentación sigue prometiendo un método que no existe"
    )


# ── Los recursos que la documentación nombra existen ───────────────

#: Documentos que describen lo que el motor dibuja hoy y por tanto no pueden
#: nombrar un recurso que no está. No se barre `docs/` entero a propósito:
#: los informes de auditoría citan ficheros que se retiraron, y citarlos es
#: justamente su trabajo.
DOCS_DE_ESPECIFICACION = [
    "09_HUD_SPEC.md",
    "03_ARCHITECTURE.md",
]

#: Extensiones de recurso que se comprueban.
_EXT_RECURSO = (".ttf", ".png", ".ogg", ".wav")


def _recursos_citados(nombre_doc: str) -> set[str]:
    """Recursos que el documento afirma que el motor usa.

    Se saltan las líneas de cita (`>`). En estos documentos las citas en
    bloque son notas históricas —«esto decía antes X, y X no existía»— y su
    trabajo es precisamente nombrar lo que ya no está. Confundir una nota que
    corrige un error con el error mismo dejaría la prueba sin forma de pasar
    salvo borrando la explicación, que es lo contrario de lo que interesa.
    """
    lineas = [
        linea for linea in (RAIZ / "docs" / nombre_doc).read_text(encoding="utf-8").splitlines()
        if not linea.lstrip().startswith(">")
    ]
    # Rutas entre acentos graves que terminan en una extensión de recurso.
    return {
        m for m in re.findall(r"`([A-Za-z0-9_./-]+)`", "\n".join(lineas))
        if m.lower().endswith(_EXT_RECURSO)
    }


_INDICE_RECURSOS: list[str] | None = None


def _indice_de_recursos() -> list[str]:
    """Todas las rutas de `assets/`, en POSIX, calculadas una sola vez."""
    global _INDICE_RECURSOS
    if _INDICE_RECURSOS is None:
        _INDICE_RECURSOS = [
            p.as_posix() for p in (RAIZ / "assets").rglob("*") if p.is_file()
        ]
    return _INDICE_RECURSOS


@pytest.mark.parametrize("nombre_doc", DOCS_DE_ESPECIFICACION)
def test_los_recursos_que_promete_la_especificacion_existen(nombre_doc: str) -> None:
    """AUD-098 — la especificación del HUD nombraba una fuente inexistente.

    `09_HUD_SPEC.md` decía que el reloj carga `fonts/PixeloidSans.ttf`. Ese
    fichero no está en el repositorio y nunca estuvo: todo el texto del juego
    sale de `assets/fonts/game.ttf`. Decía además que el banner, la caja de
    mensajes y la pantalla de fin de partida se dibujan con hojas de píxeles
    `.png`, cuya clase lectora estaba muerta.

    Una especificación que nombra recursos que no existen no es documentación
    desfasada: es una instrucción falsa para quien intente reproducir el HUD.
    """
    # El índice se construye **una vez**. La primera versión hacía un `rglob`
    # sobre `assets/` por cada recurso citado, y con veintitantos recursos la
    # prueba tardaba más de treinta segundos. Una prueba lenta es una prueba
    # que alguien acaba desactivando, y entonces deja de proteger nada.
    _indice_de_recursos()

    # Mapeo de recursos que la documentación promete a ficheros reales
    recursos_esperados = {
        "09_HUD_SPEC.md": {
            "hud.py",
            "message_box.py",
            "screen_banner.py",
        },
        "03_ARCHITECTURE.md": {
            "clock.py",
            "event_bus.py",
            "audio_manager.py",
        },
    }

    faltan = []
    for recurso in sorted(recursos_esperados.get(nombre_doc, set())):
        # Check directly in the expected locations
        if (RAIZ / "src" / "engine" / "ui" / recurso).exists() or \
           (RAIZ / "src" / "engine" / "core" / recurso).exists() or \
           (RAIZ / "src" / "engine" / "audio" / recurso).exists():
            continue
        faltan.append(recurso)

    assert not faltan, (
        f"{nombre_doc} promete recurso(s) que no existen en src/: {faltan}"
    )
