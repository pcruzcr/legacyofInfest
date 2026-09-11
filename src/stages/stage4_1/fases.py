"""AUD-814 — Las seis fases del Stage 4.1 nuevo.

Cada fase declara a la vez terreno, gradación, clima, sonido, música,
diálogo y eventos: el diseño y el código son el mismo objeto. Entre fases
no cambia el esquema de control; sólo cambia lo que se ve, se oye y se
cuenta.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.stages.stage4_1.trazado import ANCHO_SECCION

#: Matriz de color 3x3 para PostProcessing.set_color_grading, o None (pleno).
Gradacion = tuple[int, int, int, int, int, int, int, int, int] | None

COLOR_PLENO: Gradacion = None
BLANCO_Y_NEGRO: Gradacion = (87, 172, 33, 87, 172, 33, 87, 172, 33)
#: AUD-816: F2 ya no es B&N puro (era indistinguible de F3). Duotono
#: verde-gris apagado: humedad de bosque, no tormenta.
DUOTONO_VERDE_GRIS: Gradacion = (70, 130, 50, 60, 140, 60, 70, 130, 100)
GRISES_NEUTROS: Gradacion = (76, 150, 29, 76, 150, 29, 76, 150, 29)
SEPIA_VINTAGE: Gradacion = (100, 196, 48, 89, 175, 43, 69, 136, 33)
NOCTURNO_AZULADO: Gradacion = (71, 140, 26, 56, 110, 26, 51, 89, 140)

TINTE_VINTAGE: tuple[int, int, int] = (200, 120, 60)
ALFA_TINTE_VINTAGE: float = 0.12
TINTE_DESPERTAR: tuple[int, int, int] = (110, 255, 150)
ALFA_TINTE_DESPERTAR: float = 0.10

#: Prefijo de las camas ambientales del nivel (ficheros reales generados
#: por tools/generar_stage41_audio.py; ver S41-AUD).
_AMB41 = "sfx/environment/amb_stage41_"


@dataclass(frozen=True)
class Fase:
    """Lo que el jugador ve y oye al atravesar esta sección."""

    numero: int
    nombre: str
    desde_columna: int
    clima: str
    particulas: tuple[str, float]
    gradacion: Gradacion
    tinte: tuple[tuple[int, int, int], float] | None
    espiritu: int | None = None
    rayos_por_minuto: float = 0.0
    ambiente: float = 0.5
    tiene_slopes: bool = False
    shake_de_silencio: bool = False
    luna_intermitente: bool = False
    grietas_por_pisada: bool = False
    #: Ruta relativa a assets/ del bucle ambiental (p.ej.
    #: "sfx/environment/amb_stage41_f1.wav"). Ruta completa, no nombre:
    #: el ambiente se reproduce por canal dedicado con crossfade.
    sonido_ambiente: str | None = None
    musica: str | None = None
    dialogo_id: str | None = None
    decoracion: str | None = None
    grito_aislado: str | None = None
    sonidos_aislados: tuple[str, ...] = ()
    serpiente_de_fondo: bool = False
    sombra_de_ave: bool = False


FASES: tuple[Fase, ...] = (
    Fase(1, "LA ENTRADA AL CEMENTERIO", 0 * ANCHO_SECCION,
         "clear", ("dust", 6.0), COLOR_PLENO, None,
         ambiente=0.70, sonido_ambiente=_AMB41 + "f1.wav",
         musica="mus_stage41_f1", decoracion="cementerio_tilaran"),
    Fase(2, "EL VENADO", 1 * ANCHO_SECCION,
         "rain", ("ash", 14.0), DUOTONO_VERDE_GRIS, None, espiritu=0,
         ambiente=0.55, sonido_ambiente=_AMB41 + "f2.wav",
         musica="mus_stage41_f2", dialogo_id="venado",
         decoracion="bosque_gris",
         sonidos_aislados=("sfx_environment_crujido_seco",)),
    Fase(3, "LA SERPIENTE", 2 * ANCHO_SECCION,
         "storm", ("spores", 16.0), GRISES_NEUTROS, None, espiritu=1,
         rayos_por_minuto=12.0, ambiente=0.42, tiene_slopes=True,
         sonido_ambiente=_AMB41 + "f3.wav", musica="mus_stage41_f3",
         dialogo_id="serpiente", decoracion="osamentas",
         serpiente_de_fondo=True,
         sonidos_aislados=("sfx_environment_crujido_seco",
                           "sfx_environment_rafaga_viento")),
    Fase(4, "EL HALCÓN", 3 * ANCHO_SECCION,
         "rain", ("ash", 10.0), SEPIA_VINTAGE,
         (TINTE_VINTAGE, ALFA_TINTE_VINTAGE), espiritu=2,
         ambiente=0.52, shake_de_silencio=True,
         sonido_ambiente=_AMB41 + "f4.wav", musica="mus_stage41_f4",
         dialogo_id="halcon", decoracion="bosque_talado",
         grito_aislado="s41_grito_halcon", sombra_de_ave=True,
         sonidos_aislados=("sfx_environment_rafaga_viento",)),
    Fase(5, "LA PLANICIE DE LOS MUERTOS", 4 * ANCHO_SECCION,
         "clear", ("", 0.0), NOCTURNO_AZULADO, None,
         ambiente=0.22, luna_intermitente=True,
         sonido_ambiente=_AMB41 + "f5.wav", musica="mus_stage41_f5",
         decoracion="tumbas_conquistador",
         sonidos_aislados=("sfx_environment_grillo",)),
    Fase(6, "EL CAMINO HACIA PABURU", 5 * ANCHO_SECCION,
         "fog", ("spores", 26.0), COLOR_PLENO,
         (TINTE_DESPERTAR, ALFA_TINTE_DESPERTAR),
         ambiente=0.62, grietas_por_pisada=True,
         sonido_ambiente=_AMB41 + "f6.wav", musica="mus_stage41_f6",
         decoracion="piedra_verde"),
)


def fase_en(columna: float) -> Fase:
    """La fase de esa columna del mapa."""
    for fase in reversed(FASES):
        if columna >= fase.desde_columna:
            return fase
    return FASES[0]
