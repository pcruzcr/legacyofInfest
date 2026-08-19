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

#: El verde del despertar de la Fase 6 (AUD-483, GAP-065 §11): el
#: documento de síntesis pide que la fase termine en «full color / verde
#: sobrenatural», no en color pleno sin más — *«el verde debe tener
#: significado... no lo usaría como simple iluminación decorativa»*. Se
#: interpola con el mismo mecanismo que ya usa el tinte vintage de la
#: Fase 4, así que se intensifica con el avance del jugador, no de golpe.
#: Más sutil que el vintage (0,10 contra 0,12): aquí no es decadencia, es
#: energía que apenas empieza a notarse.
TINTE_DESPERTAR: tuple[int, int, int] = (110, 255, 150)
ALFA_TINTE_DESPERTAR: float = 0.10

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
    #: ¿El espíritu se deja ver a destellos antes de su diálogo, en vez de
    #: quedar encendido todo el tramo? (Fase 2, AUD-479, GAP-060 puntos 6
    #: y 9-12: *«se detiene, mira, desaparece»* — el Venado como landmark
    #: móvil, no como letrero fijo.)
    apariciones_previas: bool = False
    #: Qué pista de música debe sonar en esta fase, o `None` para silencio
    #: (AUD-493). Ver `MUSICA_DEL_DESPERTAR` más abajo para el porqué de
    #: que cinco de las seis sean `None`.
    musica: str | None = None
    #: AUD-546 — sonidos ambientales aislados y direccionales: crujidos de
    #: ramas u osamentas, ráfagas de viento. Mismo mecanismo que
    #: `grito_aislado` (temporizador aleatorio, `_play_sfx_spatial` para
    #: el paneo), generalizado a una tupla porque una fase puede tener más
    #: de un tipo de sonido aislado (la Fase 3 pide crujido **y** viento) —
    #: y no se reusa `grito_aislado` porque ese campo ya tiene su propia
    #: lógica de volumen atada a la lluvia del Gavilán (Fase 4) que no
    #: aplica aquí. Vacía por defecto: ninguna fase suena así hasta que lo
    #: declara.
    sonidos_aislados: tuple[str, ...] = ()


#: La pista que sonaba sólo en la última fase, hasta AUD-546 — ver la nota
#: junto a `MUSICA_POR_FASE` de por qué dejó de ser la única.
MUSICA_DEL_DESPERTAR: str = "bgm_final_approach"

#: AUD-546 — decisión del dueño, reversión explícita de AUD-493: llegó
#: material de autor (`assets/music/bgm_stage4_1_fase1..6.mp3`), una pista
#: por fase, y el pedido fue «usa los mp3 para cada fase correspondiente
#: como música de fondo que cambie de acuerdo a cada fase». AUD-493 —cuyo
#: razonamiento sigue siendo válido para lo que resolvía— hizo que la
#: música naciera sólo en la Fase 6 porque la única pista disponible
#: (`bgm_final_approach`) era la del clímax, y sonar desde el minuto cero
#: la desgastaba. Con seis pistas propias, una por fase, ese problema no
#: existe: cada fase tiene la suya y el clímax sigue distinguiéndose por
#: ser la sexta, no por ser la única con música.
#:
#: La cama de `sonido_ambiente` (viento, tormenta, lluvia, canto
#: ancestral) no se toca: suena por el canal de ambiente
#: (`play_ambient`/`crossfade_ambient`, un `Channel` de mezcla), y la
#: música por el canal dedicado de `pygame.mixer.music` — son dos
#: canales distintos y conviven, no compiten.
MUSICA_POR_FASE: tuple[str, ...] = (
    "bgm_stage4_1_fase1", "bgm_stage4_1_fase2", "bgm_stage4_1_fase3",
    "bgm_stage4_1_fase4", "bgm_stage4_1_fase5", "bgm_stage4_1_fase6",
)


FASES: tuple[Fase, ...] = (
    Fase(1, "EL CEMENTERIO DE TILARÁN", 0 * ANCHO_SECCION, "clear", ("ash", 5.0),
         gradacion=COLOR_PLENO, tinte=None, espiritu=None,
         rayos_por_minuto=0.0, ambiente=0.62,
         decoracion="lapidas_personales",
         musica=MUSICA_POR_FASE[0]),
    Fase(2, "EL VENADO", 1 * ANCHO_SECCION, "rain", ("ash", 14.0),
         gradacion=BLANCO_Y_NEGRO, tinte=None, espiritu=0,
         rayos_por_minuto=0.0, ambiente=0.50,
         sonido_ambiente=f"{_AMB}viento_de_bosque.wav",
         dialogo_id="venado", apariciones_previas=True,
         musica=MUSICA_POR_FASE[1],
         # AUD-546 — «crujidos repentinos de madera y maleza rompiéndose
         # en los bordes de la pantalla... para generar la sensación de
         # ser observado o seguido».
         sonidos_aislados=("sfx_environment_crujido_seco",)),
    Fase(3, "EL REY TERCIOPELO", 2 * ANCHO_SECCION, "storm", ("spores", 16.0),
         gradacion=GRISES_NEUTROS, tinte=None, espiritu=1,
         rayos_por_minuto=10.0, ambiente=0.44, tiene_slopes=True,
         sonido_ambiente="sfx/environment/sfx_environment_storm_ambient.wav",
         dialogo_id="rey_terciopelo", serpiente_de_fondo=True,
         musica=MUSICA_POR_FASE[2],
         # AUD-546 — «cascabeleo y osamentas» (crujido óseo, el mismo
         # timbre que las ramas de la Fase 2) y «ráfagas de viento fuerte»
         # a la vez: la tormenta es la fase más agresiva del nivel.
         sonidos_aislados=("sfx_environment_crujido_seco",
                           "sfx_environment_rafaga_viento")),
    Fase(4, "EL GAVILÁN", 3 * ANCHO_SECCION, "rain", ("ash", 10.0),
         gradacion=SEPIA_VINTAGE, tinte=(TINTE_VINTAGE, ALFA_TINTE_VINTAGE),
         espiritu=2, rayos_por_minuto=0.0, ambiente=0.48,
         shake_de_silencio=True,
         sonido_ambiente="sfx/environment/sfx_environment_rain_ambient.wav",
         grito_aislado="sfx_environment_grito_de_gavilan",
         decoracion="bosque_cortado", dialogo_id="gavilan",
         sombra_de_ave=True,
         musica=MUSICA_POR_FASE[3],
         # AUD-546 — «ráfagas de viento direccional, aprovechando la
         # naturaleza ventosa de Tilarán».
         sonidos_aislados=("sfx_environment_rafaga_viento",)),
    Fase(5, "LA PLANICIE DE LOS MUERTOS", 4 * ANCHO_SECCION, "clear", ("", 0.0),
         gradacion=NOCTURNO_AZULADO, tinte=None, espiritu=None,
         rayos_por_minuto=0.0, ambiente=0.16, luna_intermitente=True,
         sonido_ambiente=f"{_AMB}canto_ancestral.wav",
         decoracion="tumbas_conquistador",
         musica=MUSICA_POR_FASE[4],
         # AUD-551 — GAP-070 "Ambiente de Bosque Nocturno": grillos
         # esporádicos que anclan la fase al entorno físico cuando la
         # luna se oculta y el canto calla — antes no había ningún
         # sonido de insecto, sólo el canto ancestral.
         sonidos_aislados=("sfx_environment_grillo",)),
    Fase(6, "EL CAMINO HACIA PABURU", 5 * ANCHO_SECCION, "fog", ("spores", 26.0),
         gradacion=COLOR_PLENO, tinte=(TINTE_DESPERTAR, ALFA_TINTE_DESPERTAR),
         espiritu=None, rayos_por_minuto=0.0, ambiente=0.60,
         grietas_por_pisada=True,
         sonido_ambiente=f"{_AMB}resonancia_solemne.wav",
         musica=MUSICA_POR_FASE[5]),
)


def fase_en(columna: float) -> Fase:
    """La fase que corresponde a esa **columna** del mapa."""
    for fase in reversed(FASES):
        if columna >= fase.desde_columna:
            return fase
    return FASES[0]
