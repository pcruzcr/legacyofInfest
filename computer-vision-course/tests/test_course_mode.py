"""
Pruebas del modo taller.

Lo que hay que vigilar aquí no es que «funcione»: es que **no toque nada del
curso normal**. Un fallo en este módulo no se vería como una excepción, se
vería como notas sembradas en el expediente de un estudiante o como el juego
recordando el correo del taller al arrancar. Las dos cosas tienen su prueba.

Ninguna prueba escribe en el directorio de perfiles real: usan `tmp_path`.
"""
from __future__ import annotations

import pytest

from cvcourse import course_mode, engine_bridge

pytestmark = pytest.mark.skipif(
    not engine_bridge.hay_motor(),
    reason="sin el repositorio del motor (Colab)",
)


@pytest.fixture(autouse=True)
def _sesion_limpia():
    """Devuelve el singleton de sesión a su estado inicial después de cada prueba.

    `SesionAcademica` es un singleton de proceso: sin esto, la sesión del
    taller sobreviviría a la prueba y contaminaría a las siguientes — y, peor,
    a cualquier prueba del motor que corriera después en el mismo proceso.
    """
    yield
    from src.framework.academic.sesion import SesionAcademica

    SesionAcademica._instancia = None


def test_activar_abre_la_unidad_de_la_clase_1(perfil_temporal):
    course_mode.activar(directorio=perfil_temporal)
    assert "imagen" in course_mode.unidades_abiertas()


def test_activar_no_abre_de_golpe_las_unidades_de_las_clases_siguientes(perfil_temporal):
    """El fallo de diseño que destapó la primera versión de estas pruebas.

    La cadena de desbloqueo es transitiva: abrir la IX exige dar por aprobadas
    la VII y la VIII, que son **dos de las tres unidades que este taller
    evalúa**. Abrirlas el día 1 convertiría sus cuestionarios en decorado.
    """
    course_mode.activar(directorio=perfil_temporal)
    abiertas = set(course_mode.unidades_abiertas())
    assert "vision" not in abiertas
    assert "patrones" not in abiertas


def test_abrir_avanza_al_tramo_siguiente(perfil_temporal):
    """Lo que hace el profesor al empezar la Clase 3 y la Clase 4."""
    course_mode.activar(directorio=perfil_temporal)
    course_mode.abrir("vision")
    assert "vision" in course_mode.unidades_abiertas()

    course_mode.abrir("patrones")
    assert "patrones" in course_mode.unidades_abiertas()


def test_abrir_sin_sesion_activa_lo_dice(perfil_temporal):
    from src.framework.academic.sesion import SesionAcademica

    SesionAcademica._instancia = None
    with pytest.raises(RuntimeError, match="activar"):
        course_mode.abrir("vision")


def test_abrir_una_unidad_inventada_se_rechaza(perfil_temporal):
    course_mode.activar(directorio=perfil_temporal)
    with pytest.raises(ValueError, match="no está en el temario"):
        course_mode.abrir("unidad_x")


def test_sin_activar_las_unidades_del_taller_estan_cerradas(perfil_temporal):
    """El hueco H5, comprobado: si esta prueba dejara de fallar sin `activar`,
    el módulo entero sobraría."""
    from src.framework.academic.sesion import SesionAcademica

    sesion = SesionAcademica.reiniciar(perfil_temporal)
    sesion.entrar("nuevo@estudiante.edu", recordar=False)
    abiertas = set(sesion.progreso.unidades_desbloqueadas())
    assert "imagen" not in abiertas
    assert "vision" not in abiertas
    assert "patrones" not in abiertas


def test_esta_activo_lo_confirma(perfil_temporal):
    course_mode.activar(directorio=perfil_temporal)
    assert course_mode.esta_activo()


def test_activar_dos_veces_no_rompe_nada(perfil_temporal):
    """El progreso guarda el mejor intento, no el último: es idempotente."""
    course_mode.activar(directorio=perfil_temporal)
    course_mode.activar(directorio=perfil_temporal)
    assert course_mode.esta_activo()


def test_no_se_aprueba_la_unidad_que_se_esta_abriendo(perfil_temporal):
    """Se abre la puerta; no se pone la nota.

    El cuestionario de la unidad que toca lo contesta el estudiante: es la
    evaluación de estas cinco clases.
    """
    sesion = course_mode.activar(directorio=perfil_temporal)
    assert "imagen" not in set(sesion.progreso.unidades_aprobadas())

    course_mode.abrir("vision")
    assert "vision" not in set(sesion.progreso.unidades_aprobadas())


def test_las_unidades_previas_si_quedan_sembradas(perfil_temporal):
    sesion = course_mode.activar(directorio=perfil_temporal)
    from src.framework.academic.curriculum import ids_de_unidades

    todas = ids_de_unidades()
    previas = todas[: todas.index("imagen")]
    aprobadas = set(sesion.progreso.unidades_aprobadas())
    assert set(previas) == aprobadas


def test_el_perfil_del_taller_no_escribe_en_el_directorio_del_curso(perfil_temporal):
    """El aislamiento del que depende todo el módulo.

    Si esto fallara, hacer el taller alteraría el expediente del curso de once
    clases del estudiante que estuviera en esa máquina.
    """
    from src.framework.academic.sesion import DIRECTORIO_PROGRESO

    antes = (
        {p.name for p in DIRECTORIO_PROGRESO.glob("*.json")}
        if DIRECTORIO_PROGRESO.is_dir()
        else set()
    )
    course_mode.activar(directorio=perfil_temporal)
    despues = (
        {p.name for p in DIRECTORIO_PROGRESO.glob("*.json")}
        if DIRECTORIO_PROGRESO.is_dir()
        else set()
    )

    assert antes == despues
    assert list(perfil_temporal.glob("*.json")), "el taller no guardó en su propio perfil"


def test_activar_no_deja_el_correo_del_taller_recordado(perfil_temporal):
    """`entrar(..., recordar=False)`.

    Con el valor por defecto, el juego reanudaría la siguiente partida
    identificado como el perfil del taller, y el aislamiento se perdería justo
    por ahí.
    """
    from src.engine.core import user_settings

    antes = getattr(user_settings.get(), "student_email", None)
    course_mode.activar(directorio=perfil_temporal)
    assert getattr(user_settings.get(), "student_email", None) == antes


def test_un_correo_mal_formado_se_rechaza(perfil_temporal):
    with pytest.raises(ValueError, match="correo"):
        course_mode.activar(correo="esto no es un correo", directorio=perfil_temporal)


def test_las_claves_de_escena_del_taller_existen_en_el_registro():
    """Si alguien renombrara una escena, el taller apuntaría al vacío."""
    engine_bridge.iniciar_pygame_headless()
    from src.engine.scenes.scene_registry import get_registry, register_demo_scenes

    register_demo_scenes()
    claves = get_registry().keys
    for unidad, escena in course_mode.UNIDADES_DEL_TALLER.items():
        assert escena in claves, f"la unidad {unidad} apunta a la escena inexistente {escena}"


def test_las_unidades_del_taller_existen_en_el_temario():
    from src.framework.academic.curriculum import ids_de_unidades

    todas = set(ids_de_unidades())
    for unidad in course_mode.UNIDADES_DEL_TALLER:
        assert unidad in todas, f"{unidad} no está en el temario del motor"
