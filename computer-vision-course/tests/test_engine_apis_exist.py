"""
El contrato del curso con el motor.

La regla «no inventes APIs del motor» sólo vale si se puede comprobar. Este
fichero enumera **todo** lo que el material docente usa del motor y verifica
que sigue existiendo con la firma esperada.

Sin esto, renombrar `VisionTools.analyze_regions` rompería cinco ejemplos y un
notebook, y el fallo aparecería delante de treinta estudiantes en mitad de la
Clase 3. Con esto, aparece en la integración continua.

No se comprueba **qué** hacen las funciones: eso ya lo cubren los 196 ficheros
de prueba del motor. Aquí sólo se comprueba que existen y se pueden llamar,
que es lo que el curso necesita saber.
"""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from cvcourse import engine_bridge

pytestmark = pytest.mark.skipif(
    not engine_bridge.hay_motor(),
    reason="sin el repositorio del motor (Colab)",
)


# ── Lo que el curso usa, clase por clase ──────────────────────────────────

#: Unidad VII — Clases 1 y 2.
API_FILTER_TOOLS = (
    "compute_histogram",
    "histogram_equalize",
    "adjust_brightness",
    "adjust_contrast",
    "stretch_contrast",
    "apply_kernel",
    "get_standard_kernel",
    "gaussian_blur",
    "sobel_edge",
    "canny_edge",
    # El par «propio» es el ejercicio biblioteca-contra-implementación de la
    # Clase 2. Si desapareciera, esa comparación se quedaría sin la mitad.
    "sobel_edge_propio",
    "canny_edge_propio",
)

#: Unidad VII — Clase 2, la implementación paso a paso de Canny.
API_EDGE_DETECTION = (
    "a_gris",
    "convolucionar",
    "gradiente",
    "sobel",
    "suavizar",
    "supresion_no_maxima",
    "histeresis",
    "canny",
)

#: Unidad VIII — Clase 3.
API_VISION_TOOLS = (
    "threshold_binary",
    "threshold_otsu",
    "morphological_erode",
    "morphological_dilate",
    "morphological_open",
    "morphological_close",
    "connected_components",
    "filter_components_by_area",
    "analyze_regions",
    "largest_region",
    "watershed_segment",
    "extract_features",
    "extract_hog",
    "extract_lbp",
    "extract_color_histogram",
    "find_contours",
    "bounding_boxes_from_mask",
)

#: Unidad IX — Clase 4, parte A.
API_PATTERN_TOOLS = (
    "train",
    "evaluate",
    "save_model",
    "load_model",
    "classify",
    "classify_proba",
    "predict",
    "generate_training_report",
)

#: Campos de `RegionInfo` de los que `features.desde_region_info` depende.
CAMPOS_REGION_INFO = (
    "label", "area", "centroid", "bounding_rect",
    "eccentricity", "solidity", "perimeter",
)


@pytest.mark.parametrize("nombre", API_FILTER_TOOLS)
def test_filter_tools_expone_lo_que_usa_el_curso(nombre):
    from src.framework.processing.filter_tools import FilterTools

    assert callable(getattr(FilterTools, nombre, None)), f"FilterTools.{nombre} ya no existe"


@pytest.mark.parametrize("nombre", API_EDGE_DETECTION)
def test_edge_detection_expone_lo_que_usa_el_curso(nombre):
    from src.framework.processing import edge_detection

    assert callable(getattr(edge_detection, nombre, None)), f"edge_detection.{nombre} ya no existe"


@pytest.mark.parametrize("nombre", API_VISION_TOOLS)
def test_vision_tools_expone_lo_que_usa_el_curso(nombre):
    from src.framework.processing.vision_tools import VisionTools

    assert callable(getattr(VisionTools, nombre, None)), f"VisionTools.{nombre} ya no existe"


@pytest.mark.parametrize("nombre", API_PATTERN_TOOLS)
def test_pattern_recognition_expone_lo_que_usa_el_curso(nombre):
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    assert callable(getattr(PatternRecognitionTools, nombre, None)), (
        f"PatternRecognitionTools.{nombre} ya no existe"
    )


@pytest.mark.parametrize("campo", CAMPOS_REGION_INFO)
def test_region_info_conserva_sus_campos(campo):
    """`features.desde_region_info` lee estos atributos por nombre."""
    from src.framework.processing.vision_tools import RegionInfo

    assert campo in RegionInfo.__dataclass_fields__, f"RegionInfo.{campo} ya no existe"


def test_evaluation_result_trae_la_matriz_de_confusion():
    """La Clase 4 la dibuja con `viz.matriz_de_confusion`."""
    from src.framework.processing.pattern_recognition_tools import EvaluationResult

    campos = EvaluationResult.__dataclass_fields__
    for campo in ("accuracy", "per_class_accuracy", "confusion_matrix", "report"):
        assert campo in campos, f"EvaluationResult.{campo} ya no existe"


def test_los_modelos_que_compara_la_clase_4_siguen_aceptandose():
    """Cuatro de los cinco salen del framework.

    El quinto —Regresión Logística— se instancia con sklearn directamente
    porque `_build_model` no lo contempla (decisión D3 de la arquitectura).
    Si algún día se añadiera, esta prueba seguiría pasando y bastaría con
    cambiar el notebook.
    """
    from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

    for tipo in ("knn", "tree", "forest", "svm"):
        assert PatternRecognitionTools._build_model(tipo) is not None

    with pytest.raises(ValueError, match=r"unknown model_type"):
        PatternRecognitionTools._build_model("logreg")


def test_el_dataset_de_referencia_sigue_donde_estaba():
    """La Clase 4 lo usa como ejemplo ya preparado."""
    ruta = engine_bridge.raiz_del_repositorio() / "assets/datasets/sample_dataset.npz"
    assert ruta.exists(), "assets/datasets/sample_dataset.npz ha desaparecido"

    datos = np.load(ruta, allow_pickle=True)
    assert {"X", "y"}.issubset(set(datos.keys()))
    assert datos["X"].shape[0] == datos["y"].shape[0]


def test_las_escenas_del_taller_siguen_registradas():
    engine_bridge.iniciar_pygame_headless()
    from src.engine.scenes.scene_registry import get_registry, register_demo_scenes

    register_demo_scenes()
    claves = get_registry().keys
    for clave in ("filter", "vision", "pattern"):
        assert clave in claves, f"la escena '{clave}' ya no está registrada"


def test_la_resolucion_interna_es_la_que_espera_el_curso():
    """El material dice 800×600 al explicar los fotogramas capturados.

    `docs/08_SYLLABUS_MAPPING.md` todavía dice 320×224, que es de una versión
    anterior del motor. El curso se fía de `settings`, que es lo que se
    ejecuta, y esta prueba avisa si vuelve a cambiar.
    """
    engine_bridge.iniciar_pygame_headless()
    from src.engine.core import settings

    assert (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT) == (800, 600)


def test_las_herramientas_de_dataset_del_motor_siguen_ahi():
    """`tools/build_dataset.py` es lo que la Clase 4 usa para etiquetar carpetas."""
    raiz = engine_bridge.raiz_del_repositorio()
    assert (raiz / "tools" / "build_dataset.py").exists()
    assert (raiz / "scripts" / "train_reference_model.py").exists()


def test_la_sesion_academica_conserva_la_api_del_modo_taller():
    """`course_mode` depende de estas tres, y sólo de estas tres."""
    from src.framework.academic.sesion import SesionAcademica

    assert callable(SesionAcademica.reiniciar)
    assert callable(SesionAcademica.instancia)
    assert callable(SesionAcademica.registrar_examen)

    # `recordar` es el parámetro que mantiene aislado el perfil del taller.
    firma = inspect.signature(SesionAcademica.entrar)
    assert "recordar" in firma.parameters
