"""
Las demos académicas dibujan en la pantalla entera, no en una esquina.

AUD-094
=======
Las trece demos se escribieron cuando la resolución interna era 320x224 y
nunca se migraron a los 800x600 actuales. El resultado, medido: el elemento
que el estudiante manipula —la figura del laboratorio de transformaciones, el
vector, el nivel de colisiones, el mapa de ruido, el tarjetón de color— vivía
en el cuadrante superior izquierdo y tres cuartas partes de la pantalla
estaban en negro.

Cómo se mide aquí
-----------------
No se comprueban coordenadas concretas: eso ataría la prueba a un diseño y
la rompería en cuanto alguien moviera una etiqueta. Se comprueban dos
propiedades que sí describen la queja:

1. **Hay contenido en el centro.** Se parte el área útil en una rejilla de
   3x3 y se exige que la celda central tenga píxeles dibujados. Una escena
   que amontone todo arriba a la izquierda falla.
2. **El contenido no cabe en un cuadrante.** Se exige que la caja envolvente
   del contenido ocupe al menos la mitad del ancho útil.

Ambas fallaban antes de AUD-094 en ocho de las trece escenas, y las cuatro
que usan dos paneles daban el patrón `#.#`: contenido en los bordes y
columna central muerta, porque cada panel medía el 32 % del ancho y el hueco
entre ellos el 36 %.
"""
from __future__ import annotations

import importlib

import numpy as np
import pygame
import pytest

from src.engine.core import settings
from src.engine.scenes import demo_layout as DL

#: Las trece demos académicas, por módulo y clase.
DEMOS: list[tuple[str, str]] = [
    ("transform_lab_scene", "TransformLabScene"),
    ("vector_lab_scene", "VectorLabScene"),
    ("collision_lab_scene", "CollisionLabScene"),
    ("interpolation_lab_scene", "InterpolationLabScene"),
    ("curve_editor_scene", "CurveEditorScene"),
    ("noise_lab_scene", "NoiseLabScene"),
    ("color_theory_scene", "ColorTheoryScene"),
    ("pattern_demo_scene", "PatternDemoScene"),
    ("combo_demo_scene", "ComboDemoScene"),
    ("pipeline_builder_scene", "PipelineBuilderScene"),
    ("filter_demo_scene", "FilterDemoScene"),
    ("vision_demo_scene", "VisionDemoScene"),
    ("sandbox_scene", "SandboxScene"),
]

#: Un píxel cuenta como dibujado si se separa del fondo más que esto sumando
#: los tres canales. Deja fuera la rejilla tenue de fondo, que no es
#: contenido.
_UMBRAL_PIXEL = 24
#: Fracción mínima de una celda para considerarla ocupada.
_UMBRAL_CELDA = 0.002


@pytest.fixture(scope="module")
def pantalla():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    return pygame.display.get_surface()


@pytest.fixture
def contexto(pantalla):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(),
        audio_manager=AudioManager(),
        scene_manager=None,
        event_bus=EventBus(),
        clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


def _mascara_de_contenido(superficie: pygame.Surface) -> np.ndarray:
    """Píxeles del área útil que difieren del fondo."""
    fondo = np.array(DL.COLOR_BG, dtype=np.int16)
    entero = pygame.surfarray.array3d(superficie).transpose(1, 0, 2).astype(np.int16)
    area = DL.area_de_contenido()
    recorte = entero[area.top:area.bottom, area.left:area.right]
    return np.abs(recorte - fondo).sum(axis=2) > _UMBRAL_PIXEL


def _pintar(modulo: str, clase: str, contexto, pantalla) -> np.ndarray:
    mod = importlib.import_module(f"src.engine.scenes.{modulo}")
    escena = getattr(mod, clase)(contexto)
    escena.awake()
    escena.start()
    escena.on_enter()
    try:
        for _ in range(6):
            escena.process_events([])
            escena.update(1.0 / 60.0)
            escena.draw(pantalla)
        return _mascara_de_contenido(pantalla)
    finally:
        escena.on_exit()
        escena.destroy()


class TestLasDemosDibujanEnElCentro:
    """La queja literal: «la imagen o elemento que uno mueve no está centrado»."""

    @pytest.mark.parametrize(("modulo", "clase"), DEMOS, ids=[c for _, c in DEMOS])
    def test_la_celda_central_tiene_contenido(self, modulo, clase, contexto, pantalla):
        mascara = _pintar(modulo, clase, contexto, pantalla)
        alto, ancho = mascara.shape
        central = mascara[alto // 3:2 * alto // 3, ancho // 3:2 * ancho // 3]
        ocupacion = float(central.mean())
        assert ocupacion > _UMBRAL_CELDA, (
            f"{clase}: la celda central del área útil está vacía "
            f"(ocupación {ocupacion:.5f}). El contenido se dibuja fuera del "
            f"centro, que es el defecto AUD-094."
        )

    @pytest.mark.parametrize(("modulo", "clase"), DEMOS, ids=[c for _, c in DEMOS])
    def test_el_contenido_no_cabe_en_un_cuadrante(self, modulo, clase, contexto, pantalla):
        mascara = _pintar(modulo, clase, contexto, pantalla)
        columnas = np.nonzero(mascara.any(axis=0))[0]
        assert columnas.size > 0, f"{clase}: no dibujó nada"
        extension = (columnas.max() - columnas.min()) / mascara.shape[1]
        assert extension >= 0.5, (
            f"{clase}: el contenido abarca sólo el {extension:.0%} del ancho "
            f"útil. Antes de AUD-094 ocho escenas quedaban por debajo del 40 % "
            f"porque estaban escritas para una pantalla de 320 px."
        )


#: Demos que declaran dónde vive su elemento principal. No están las trece:
#: las que se construyen sobre dos paneles ya quedan cubiertas por la prueba
#: de la celda central, y las que son sólo texto no tienen un «elemento».
CON_ELEMENTO: list[tuple[str, str]] = [
    ("transform_lab_scene", "TransformLabScene"),
    ("vector_lab_scene", "VectorLabScene"),
    ("collision_lab_scene", "CollisionLabScene"),
    ("interpolation_lab_scene", "InterpolationLabScene"),
    ("curve_editor_scene", "CurveEditorScene"),
    ("noise_lab_scene", "NoiseLabScene"),
]


class TestElElementoPrincipalEstaCentradoYEsGrande:
    """«especialmente la imagen o elemento que uno mueve».

    Cada una de estas escenas declara con `rect_principal()` dónde vive lo
    que el estudiante manipula. Que la caja envolvente del dibujo entero
    parezca razonable no basta: el mapa de ruido podía estar en (0, 40) a
    tamaño original y la caja seguía saliendo ancha por culpa de una línea de
    texto larga. Esto mira el elemento, no el conjunto.
    """

    @pytest.mark.parametrize(("modulo", "clase"), CON_ELEMENTO, ids=[c for _, c in CON_ELEMENTO])
    def test_el_elemento_esta_centrado(self, modulo, clase, contexto, pantalla):
        mod = importlib.import_module(f"src.engine.scenes.{modulo}")
        escena = getattr(mod, clase)(contexto)
        rect = escena.rect_principal()
        area = DL.area_de_contenido()
        desvio = abs(rect.centerx - area.centerx) / area.w
        assert DL.esta_centrado(rect), (
            f"{clase}: su elemento principal está desviado del centro un "
            f"{desvio:.0%} del ancho útil (máximo {DL.TOLERANCIA_CENTRADO:.0%}). "
            f"Antes de AUD-094 las desviaciones iban del 22 % al 34 %."
        )

    @pytest.mark.parametrize(("modulo", "clase"), CON_ELEMENTO, ids=[c for _, c in CON_ELEMENTO])
    def test_el_elemento_llena_la_pantalla(self, modulo, clase, contexto, pantalla):
        mod = importlib.import_module(f"src.engine.scenes.{modulo}")
        escena = getattr(mod, clase)(contexto)
        rect = escena.rect_principal()
        area = DL.area_de_contenido()
        ocupacion = (rect.w * rect.h) / (area.w * area.h)
        assert ocupacion >= DL.OCUPACION_MINIMA, (
            f"{clase}: su elemento principal ocupa el {ocupacion:.0%} del área "
            f"útil (mínimo {DL.OCUPACION_MINIMA:.0%}). El mapa de ruido, por "
            f"ejemplo, se pegaba a tamaño original —320x180 sobre 800x600— y "
            f"ocupaba el 13 %."
        )


class TestElLienzoDeAutoria:
    """El mecanismo que hizo posible la migración sin reescribir a mano."""

    def test_el_centro_de_autoria_cae_en_el_centro_de_la_pantalla(self, pantalla):
        lienzo = DL.Lienzo(DL.AUTHORED_W, DL.AUTHORED_H)
        area = DL.area_de_contenido()
        x, y = lienzo.p(DL.AUTHORED_W / 2, DL.AUTHORED_H / 2)
        assert abs(x - area.centerx) <= 2
        assert abs(y - area.centery) <= 2

    def test_la_escala_es_uniforme(self, pantalla):
        """Un círculo tiene que seguir siendo un círculo.

        Estas escenas enseñan geometría; un escalado distinto por eje
        convertiría una rotación en algo que ya no conserva los ángulos.
        """
        lienzo = DL.Lienzo(DL.AUTHORED_W, DL.AUTHORED_H)
        # Un cuadrado de autoría tiene que salir cuadrado en pantalla. Se
        # compara con tolerancia de un píxel porque las coordenadas se
        # redondean a entero al dibujar.
        lado = 100
        ancho = lienzo.x(lado) - lienzo.x(0)
        alto = lienzo.y(lado) - lienzo.y(0)
        assert abs(ancho - alto) <= 1, (
            f"un cuadrado de {lado} unidades sale de {ancho}x{alto} px"
        )
        assert abs(ancho - lado * lienzo.escala) <= 1

    def test_el_inverso_deshace_la_traduccion(self, pantalla):
        """Hace falta para el ratón: de píxel de pantalla a unidad de autoría."""
        lienzo = DL.Lienzo(DL.AUTHORED_W, DL.AUTHORED_H)
        for punto in ((0, 0), (37, 91), (DL.AUTHORED_W, DL.AUTHORED_H)):
            vuelta = lienzo.inverso(*lienzo.p(*punto))
            assert abs(vuelta[0] - punto[0]) < 1.0
            assert abs(vuelta[1] - punto[1]) < 1.0

    def test_el_lienzo_cabe_dentro_del_area(self, pantalla):
        lienzo = DL.Lienzo(DL.AUTHORED_W, DL.AUTHORED_H)
        assert DL.area_de_contenido().contains(lienzo.rect())

    def test_los_dos_paneles_dejan_una_canaleta_estrecha(self, pantalla):
        """El defecto `#.#`: el hueco central era más ancho que cada panel.

        Con el 32 % de antes, sobre 800 px, cada panel medía 256 y el hueco
        288. Cuatro demos —filtros, visión, patrones y tuberías— dibujaban
        en los bordes y dejaban muerta la columna central.
        """
        hueco = DL.RIGHT_PANEL_X - DL.LEFT_PANEL_W
        assert 0 <= hueco < DL.PANEL_W, (
            f"El hueco entre paneles ({hueco} px) no puede acercarse al ancho "
            f"de un panel ({DL.PANEL_W} px)."
        )
