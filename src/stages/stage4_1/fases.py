"""Las seis fases del 4-1: la tabla que hace que el cementerio cambie de piel
según se atraviesa de sección en sección (AUD-467 — pasillo horizontal, no
pozo; ver `trazado.py` para el porqué).

Por qué es una tabla y no seis `if`
====================================
El diseño (`docs/niveles/15_DISENO_4_1_EL_CEMENTERIO.md`) define cada fase
por varios parámetros a la vez: terreno, gradación de color, clima, sonido,
diálogo y decoración. Escrito como tabla, el diseño y el código son el
mismo objeto.

La regla de la fase: entre fases **no cambia el esquema de control ni se
introduce una mecánica nueva que no esté anunciada**. Sólo cambia lo que se
ve, se oye y se cuenta.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.stages.stage4_1.trazado import ANCHO_SECCION

#: Una matriz de color 3x3 para `PostProcessing.set_color_grading()`, o
#: `None` para «sin gradación» (color de la imagen sin tocar).
Gradacion = tuple[int, int, int, int, int, int, int, int, int] | None

#: Color pleno: la imagen tal cual, sin gradación.
COLOR_PLENO: Gradacion = None
#: Luminancia estándar (ITU-R BT.601: 0.299/0.587/0.114, escalada a 255) con
#: +15 % de ganancia — blanco y negro marcado, no un gris suave.
BLANCO_Y_NEGRO: Gradacion = (87, 172, 33, 87, 172, 33, 87, 172, 33)
#: La misma luminancia, sin ganancia — un gris plano y uniforme.
GRISES_NEUTROS: Gradacion = (76, 150, 29, 76, 150, 29, 76, 150, 29)
#: Matriz sepia clásica, escalada a 255. El naranja "vintage" se completa
#: con `set_tint`, no aquí.
SEPIA_VINTAGE: Gradacion = (100, 196, 48, 89, 175, 43, 69, 136, 33)
#: "Day-for-night": el rojo y el verde de salida son luminancia atenuada;
#: el azul de salida conserva más entrada.
NOCTURNO_AZULADO: Gradacion = (71, 140, 26, 56, 110, 26, 51, 89, 140)

TINTE_VINTAGE: tuple[int, int, int] = (200, 120, 60)
ALFA_TINTE_VINTAGE: float = 0.12

#: Prefijo común de los cuatro ambientes generados en AUD-465.
_AMB = "sfx/environment/sfx_environment_"


@dataclass(frozen=True)
class Fase:
    """Una fase: lo que el jugador ve y oye al atravesar esta sección."""

    numero: int
    nombre: str
    #: Primera **columna** de la sección. Se compara la `x` del jugador: el
    #: 4-1 es un pasillo, se atraviesa de izquierda a derecha.
    desde_columna: int
    clima: str
    particulas: tuple[str, float]
    gradacion: Gradacion
    tinte: tuple[tuple[int, int, int], float] | None
    #: Índice del espíritu que testifica en esta fase (0=Venado, 1=Rey
    #: Terciopelo, 2=Gavilán), o `None`.
    espiritu: int | None
    rayos_por_minuto: float
    ambiente: float
    tiene_slopes: bool = False
    shake_de_silencio: bool = False
    luna_intermitente: bool = False
    grietas_por_pisada: bool = False
    sonido_ambiente: str | None = None
    grito_aislado: str | None = None
    #: Decoración de fondo: `"lapidas_personales"`, `"bosque_cortado"`,
    #: `"tumbas_conquistador"`, o `None`.
    decoracion: str | None = None
    #: Id del árbol de diálogo en `data/dialogues/stage4_1.json`, o `None`.
    dialogo_id: str | None = None
    #: Serpiente de fondo reptando (Fase 3) — presencia aparte de la que
    #: asciende, pide el guion: *«movimientos de serpientes... en el fondo»*.
    serpiente_de_fondo: bool = False
    #: Sombra de ave cruzando el cielo de vez en cuando (Fase 4).
    sombra_de_ave: bool = False


FASES: tuple[Fase, ...] = (
    Fase(1, "EL CEMENTERIO DE TILARÁN", 0 * ANCHO_SECCION, "clear", ("ash", 5.0),
         gradacion=COLOR_PLENO, tinte=None, espiritu=None,
         rayos_por_minuto=0.0, ambiente=0.62,
         decoracion="lapidas_personales"),
    Fase(2, "EL VENADO", 1 * ANCHO_SECCION, "rain", ("ash", 14.0),
         gradacion=BLANCO_Y_NEGRO, tinte=None, espiritu=0,
         rayos_por_minuto=0.0, ambiente=0.50,
         sonido_ambiente=f"{_AMB}viento_de_bosque.wav",
         dialogo_id="venado"),
    Fase(3, "EL REY TERCIOPELO", 2 * ANCHO_SECCION, "storm", ("spores", 16.0),
         gradacion=GRISES_NEUTROS, tinte=None, espiritu=1,
         rayos_por_minuto=10.0, ambiente=0.44, tiene_slopes=True,
         sonido_ambiente="sfx/environment/sfx_environment_storm_ambient.wav",
         dialogo_id="rey_terciopelo", serpiente_de_fondo=True),
    Fase(4, "EL GAVILÁN", 3 * ANCHO_SECCION, "rain", ("ash", 10.0),
         gradacion=SEPIA_VINTAGE, tinte=(TINTE_VINTAGE, ALFA_TINTE_VINTAGE),
         espiritu=2, rayos_por_minuto=0.0, ambiente=0.48,
         shake_de_silencio=True,
         sonido_ambiente="sfx/environment/sfx_environment_rain_ambient.wav",
         grito_aislado="sfx_environment_grito_de_gavilan",
         decoracion="bosque_cortado", dialogo_id="gavilan",
         sombra_de_ave=True),
    Fase(5, "LA PLANICIE DE LOS MUERTOS", 4 * ANCHO_SECCION, "clear", ("", 0.0),
         gradacion=NOCTURNO_AZULADO, tinte=None, espiritu=None,
         rayos_por_minuto=0.0, ambiente=0.16, luna_intermitente=True,
         sonido_ambiente=f"{_AMB}canto_ancestral.wav",
         decoracion="tumbas_conquistador"),
    Fase(6, "EL CAMINO HACIA PABURU", 5 * ANCHO_SECCION, "fog", ("spores", 26.0),
         gradacion=COLOR_PLENO, tinte=None, espiritu=None,
         rayos_por_minuto=0.0, ambiente=0.60, grietas_por_pisada=True,
         sonido_ambiente=f"{_AMB}resonancia_solemne.wav"),
)


def fase_en(columna: float) -> Fase:
    """La fase que corresponde a esa **columna** del mapa."""
    for fase in reversed(FASES):
        if columna >= fase.desde_columna:
            return fase
    return FASES[0]
