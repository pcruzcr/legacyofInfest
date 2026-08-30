"""Módulo: tramos_venado
Sistema: stages.boss_venado
Descripción: los 4 actos narrativos del corredor pre-jefe (Residencias al
    Crepúsculo, x < ARENA_X0=2480) -- tabla de datos pura, patrón idéntico a
    src/stages/stage4_1/fases.py (Fase congelada + tabla + fase_en(x)),
    adaptada a PÍXELES de mundo (no columnas de tile) porque la escena ya
    compara self._player.rect.centerx contra ARENA_X0 en píxeles -- la
    comparación real vive en boss_venado_scene.py:528; las líneas 161-177
    solo DEFINEN ARENA_X0/ARENA_BOUNDS. x_inicio de cada tramo coincide con
    los límites REALES de zona del generador de mapa
    (tools/gen_level_residencias.py: PRADERA/CARPORT/ARCOS/ARENA, líneas
    96-99), no con los x aproximados del spec de diseño.

    Este módulo no usa pygame directamente; ease_in_out_quad (math_utils)
    trae pygame de forma transitiva sin usarlo en su cuerpo -- el módulo
    sigue siendo testeable sin display real (y sin lógica propia del motor:
    solo reutiliza esa única función matemática)."""
from __future__ import annotations

from dataclasses import dataclass

from src.engine.utils.math_utils import ease_in_out_quad

#: Matriz de color 3x3 para PostProcessing.set_color_grading(), o None para
#: "color pleno" (sin gradación) -- mismo contrato que Gradacion en fases.py.
Gradacion = tuple[int, int, int, int, int, int, int, int, int] | None

#: Identidad: cada canal de salida = el mismo canal de entrada, sin mezcla
#: (255 representa el coeficiente 1.0 -- ver post_processing.py:71-84,
#: gradacion.py:99). Hasta el RETUNE 2026-08-25 se usaba solo para los
#: tests de este módulo (en la escena, "sin gradación" se expresaba con
#: None -- ver interpolar_grading). Desde el retune también es el
#: matriz_grading EXPLÍCITO del Acto 4 en TABLA (más abajo) -- y a
#: propósito no es None: PostProcessing.set_color_grading() colapsa la
#: matriz identidad a None internamente por comparación bit a bit con
#: MATRIZ_IDENTIDAD (post_processing.py:84, mismo valor que esta
#: constante), así que el efecto EN PANTALLA en régimen permanente es
#: idéntico a None (cero procesamiento) -- pero pasar la matriz explícita
#: (en vez de None) es lo que deja que
#: ``_actualizar_tramo_narrativo`` (boss_venado_scene.py:934-946)
#: INTERPOLE hacia la identidad con el ease de siempre; con None el guard
#: ``self._tramo_grading_previo is None and tramo.matriz_grading is None``
#: solo se cumple cuando AMBOS extremos son None, así que si se dejara
#: None aquí el Acto 3 (AZUL_MISTERIO) no tendría hacia dónde interpolar
#: y el grading quedaría congelado en vez de resolver limpio.
IDENTIDAD: Gradacion = (255, 0, 0, 0, 255, 0, 0, 0, 255)

#: Acto 2 "El abandono" -- ámbar cálido, ganancia de rojo, resta de azul.
#: RETUNE 2026-08-25 (veredicto del playtest humano 2026-08-25: "me gusta
#: apagada pero se oscureció en exceso; las ideas no deben chocar"):
#: suavizado 30% hacia IDENTIDAD por canal --
#: ``round(viejo[i] + 0.30*(IDENTIDAD[i]-viejo[i]))`` -- mismo matiz
#: ámbar, menos saturado. Valor PRE-retune (spec Tarea 1, Acto 2
#: original): (215, 45, 10, 15, 175, 10, 5, 20, 130).
AMBAR: Gradacion = (227, 32, 7, 10, 199, 7, 4, 14, 168)
#: Acto 3 "El umbral" -- azulado de misterio (day-for-night suave).
#: RETUNE 2026-08-25 (mismo veredicto que AMBAR arriba): suavizado 50%
#: hacia IDENTIDAD por canal --
#: ``round(viejo[i] + 0.50*(IDENTIDAD[i]-viejo[i]))`` -- matiz frío sin
#: aplastar tanto la luminancia. Valor PRE-retune (spec Tarea 1, Acto 3
#: original): (65, 120, 25, 50, 100, 25, 45, 80, 150).
AZUL_MISTERIO: Gradacion = (160, 60, 12, 25, 178, 12, 22, 40, 202)
#: Acto 4 "Lo sagrado" -- RETUNE 2026-08-25: el índigo profundo original de
#: este tramo, "INDIGO_SAGRADO" = (70, 40, 90, 40, 70, 110, 60, 50, 150)
#: (spec Tarea 1), drenaba el look cálido de atardecer que el usuario
#: aprobó en el golden pre-campaña al resolver dentro de la arena; se
#: retira la matriz por completo (TABLA usa IDENTIDAD, definida arriba,
#: como matriz_grading de este tramo) y la única huella "sagrada" que
#: queda es el tinte índigo de abajo, con su alfa muy reducida.


@dataclass(frozen=True)
class Tramo:
    """Un acto del corredor: lo que el jugador ve/oye al atravesarlo."""

    numero: int
    nombre: str
    #: Primera columna de MUNDO en píxeles (no tile) del tramo.
    x_inicio: float
    matriz_grading: Gradacion
    tinte: tuple[tuple[int, int, int], float] | None
    vineta: float
    clima: str
    #: (tipo, partículas/segundo) para AmbientParticleSystem.set_effect().
    ambient_fx: tuple[str, float]
    #: Flags de eventos de este tramo -- NUNCA leídas por este módulo (que
    #: se queda puro), pero las dos categorías siguientes se comportan
    #: distinto del lado de la escena (corrección de docstring, revisión de
    #: spec T6, 2026-08-25 -- antes decía "leídas por la escena" para las
    #: tres por igual, que ya no es cierto para la primera):
    #:
    #: CONSUMIDAS en tiempo real por boss_venado_scene.py -- el código de la
    #: escena hace ``"<flag>" in tramo_en(x).eventos`` cada cuadro:
    #: "shake_al_entrar" -- temblor único de cámara la primera vez que se
    #: entra a este tramo (Acto 4, ver
    #: ``_actualizar_silencio_y_shake_de_arena``). "eco" -- ``activar_eco
    #: (True)`` mientras el jugador está DENTRO de este tramo, apagado al
    #: salir (Acto 4, mismo método).
    #:
    #: SOLO DESCRIPTIVA, no consumida por nadie -- documenta la intención del
    #: tramo para quien lea la tabla, pero el umbral real vive hardcodeado
    #: en otro módulo porque no coincide con el tramo completo: "sombra_cruza"
    #: (Acto 3) anuncia que este tramo dispara el aviso de la Tarea 5, pero la
    #: ventana real [2200, 2480) es una SUB-porción de este tramo (que
    #: arranca en 1520.0), no el tramo entero -- vive en
    #: ``presencias_venado.SOMBRA_X0``/``SOMBRA_X1``, no aquí. Si algún tramo
    #: futuro necesitara una flag cuya ventana SÍ coincide con el tramo
    #: completo, debería consumirse en tiempo real como "shake_al_entrar"/
    #: "eco" y no quedarse en esta segunda categoría.
    eventos: frozenset[str] = frozenset()


TABLA: tuple[Tramo, ...] = (
    Tramo(1, "El hogar", 0.0, None, None, 0.20, "clear",
          ("leaves", 14.0)),
    Tramo(2, "El abandono", 1040.0, AMBAR, ((220, 160, 90), 0.08), 0.26,
          "clear", ("leaves", 10.0)),
    Tramo(3, "El umbral", 1520.0, AZUL_MISTERIO, ((80, 110, 160), 0.10),
          0.38, "fog", ("leaves", 6.0), frozenset({"sombra_cruza"})),
    # RETUNE 2026-08-25: matriz_grading pasa de INDIGO_SAGRADO a IDENTIDAD
    # (ver comentario de IDENTIDAD arriba) y el tinte índigo baja su alfa
    # de 0.12 a 0.04 -- susurro de índigo que conserva el matiz "sagrado"
    # sin drenar el cálido del atardecer aprobado.
    Tramo(4, "Lo sagrado", 2480.0, IDENTIDAD, ((90, 60, 150), 0.04),
          0.32, "clear", ("leaves", 3.0),
          frozenset({"shake_al_entrar", "eco"})),
)


def tramo_en(x: float) -> Tramo:
    """El tramo que corresponde a esa columna de MUNDO (píxeles). Mismo
    patrón que fase_en() de stage4_1/fases.py: el último tramo cuyo
    x_inicio <= x."""
    for tramo in reversed(TABLA):
        if x >= tramo.x_inicio:
            return tramo
    return TABLA[0]


def avance_en_tramo(x: float) -> float:
    """0.0 al entrar al tramo de x, 1.0 al llegar al siguiente. A
    diferencia de stage4_1 (ANCHO_SECCION fijo para las 6 fases), nuestros
    4 actos tienen anchos distintos (1040/480/960/800 px) -- el ancho se
    deriva de la tabla, no de una constante."""
    tramo = tramo_en(x)
    idx = TABLA.index(tramo)
    fin = TABLA[idx + 1].x_inicio if idx + 1 < len(TABLA) else tramo.x_inicio + 1.0
    ancho = max(1.0, fin - tramo.x_inicio)
    return max(0.0, min(1.0, (x - tramo.x_inicio) / ancho))


def interpolar_grading(a: Gradacion, b: Gradacion, t: float) -> tuple[int, ...]:
    """Interpola entre dos matrices (None = IDENTIDAD), con ease-in-out-quad
    sobre t -- a diferencia de _lerp_gradacion de stage4_1.py (lineal), esta
    versión suaviza el arranque/cierre del cambio de color, decisión propia
    de este nivel (spec Tarea 1: "interpolar_grading(...) (+ ease)")."""
    ga = a if a is not None else IDENTIDAD
    gb = b if b is not None else IDENTIDAD
    te = ease_in_out_quad(max(0.0, min(1.0, t)))
    return tuple(round(ga[i] + (gb[i] - ga[i]) * te) for i in range(9))
