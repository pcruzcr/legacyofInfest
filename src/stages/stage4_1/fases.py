"""Las seis fases del 4-1: la tabla que hace que el cementerio cambie de piel.

Por qué es una tabla y no seis `if`
====================================
El diseño (`docs/niveles/15_DISENO_4_1_EL_CEMENTERIO.md` §2) define cada fase
por **tres parámetros a la vez**: gradación de color, clima y geometría.
Escrito como condicionales, cambiar «la gradación de la fase III» obliga a
buscar en varios sitios y a acertar en todos. Escrito como tabla, el diseño y
el código son el mismo objeto: se lee de arriba abajo como la tabla del
documento, y una prueba puede recorrerla y comprobar que sube monótonamente.

La regla de la fase (mismo principio que el diseño anterior heredaba de su
§1): entre fases **no cambia el esquema de control ni se introduce una
mecánica nueva que no esté anunciada**. Sólo cambia lo que se ve y se oye.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.stages.stage4_1.trazado import ALTO_FASE

#: Una matriz de color 3x3 para `PostProcessing.set_color_grading()`, o
#: `None` para «sin gradación» (color de la imagen sin tocar). Ver §2 del
#: diseño para de dónde sale cada matriz.
Gradacion = tuple[int, int, int, int, int, int, int, int, int] | None

#: Color pleno: la imagen tal cual, sin gradación.
COLOR_PLENO: Gradacion = None
#: Luminancia estándar (ITU-R BT.601: 0.299/0.587/0.114, escalada a 255) con
#: +15 % de ganancia — blanco y negro marcado, no un gris suave.
BLANCO_Y_NEGRO: Gradacion = (87, 172, 33, 87, 172, 33, 87, 172, 33)
#: La misma luminancia, sin ganancia — un gris plano y uniforme.
GRISES_NEUTROS: Gradacion = (76, 150, 29, 76, 150, 29, 76, 150, 29)
#: Matriz sepia clásica (0.393/0.769/0.189 …), escalada a 255. El tono
#: naranja del "vintage" se completa con `set_tint`, no aquí — son dos
#: sistemas separados en `PostProcessing` y cada uno hace su parte.
SEPIA_VINTAGE: Gradacion = (100, 196, 48, 89, 175, 43, 69, 136, 33)
#: "Day-for-night": el rojo y el verde de salida son luminancia atenuada: el
#: azul de salida conserva más entrada. El truco clásico de cine para
#: simular noche sin apagar del todo la imagen.
NOCTURNO_AZULADO: Gradacion = (71, 140, 26, 56, 110, 26, 51, 89, 140)

#: El tinte naranja de la Fase 4, por encima de `SEPIA_VINTAGE`. Alfa bajo:
#: es un empujón de color, no un filtro que tape la escena.
TINTE_VINTAGE: tuple[int, int, int] = (200, 120, 60)
ALFA_TINTE_VINTAGE: float = 0.12


@dataclass(frozen=True)
class Fase:
    """Una fase: lo que el jugador ve y oye cuando llega a este tramo."""

    numero: int
    nombre: str
    #: Primera **fila** del tramo. Se compara la `y` del jugador, no la `x`:
    #: el 4-1 es un pozo, se desciende (ver `trazado.py`).
    desde_fila: int
    #: Clima del `WeatherSystem`. Los valores que el motor conoce:
    #: `clear`, `rain`, `snow`, `fog`, `storm`.
    clima: str
    #: Partículas de ambiente: `(tipo, ritmo)`.
    particulas: tuple[str, float]
    #: La matriz de gradación objetivo de esta fase. Se interpola desde la
    #: gradación de la fase anterior a lo largo de este tramo, para que el
    #: cambio se vea progresivo — igual que el diseño anterior interpolaba
    #: la posición de la luna entre actos.
    gradacion: Gradacion
    #: Tinte adicional (color, alfa) por encima de la gradación, o `None`.
    tinte: tuple[tuple[int, int, int], float] | None
    #: Índice del espíritu que testifica en esta fase (0=Venado, 1=Rey
    #: Terciopelo, 2=Gavilán), o `None` si ninguno. Aparece al entrar en la
    #: fase y se desvanece hacia arriba al salir de ella: asciende.
    espiritu: int | None
    #: Relámpagos por minuto. Cero fuera de la tormenta.
    rayos_por_minuto: float
    #: Luz ambiente base de la fase. La Fase 5 la modula con un ciclo de
    #: luna; las demás la usan tal cual.
    ambiente: float
    #: Si esta fase tiene un tramo de slopes (Fase 3, "ascender por lomas").
    tiene_slopes: bool = False
    #: Si esta fase dispara el camera shake puntual del silencio súbito
    #: (Fase 4) — una sola vez, a mitad de tramo.
    shake_de_silencio: bool = False
    #: Si la luz ambiente de esta fase oscila con un ciclo de luna en vez de
    #: quedarse fija (Fase 5).
    luna_intermitente: bool = False
    #: Si las repisas de esta fase encienden una luz corta al pisarlas, sin
    #: quedar encendidas (Fase 6 — un rastro, no un progreso acumulado).
    grietas_por_pisada: bool = False
    #: Ruta (relativa a `assets/`) del ambiente sonoro de esta fase, o `None`.
    #:
    #: `WeatherSystem.get_ambient_audio_key()` sólo se consulta **una vez**,
    #: al entrar al escenario (`stage_scene.py` en `on_stage_start`) — nunca
    #: se vuelve a llamar cuando `_actualizar_fase` cambia de clima, así que
    #: sin este campo la tormenta de la Fase 3 nunca sonaba a tormenta, ni en
    #: este diseño ni en el anterior. Aquí cada fase pide su propio
    #: `crossfade_ambient` (AUD-465): la Fase 3 reusa `storm_ambient` —el
    #: mismo fichero que ya existía, sólo que ahora suena cuando toca— y las
    #: Fases 2, 5 y 6 usan los tres ambientes nuevos de esa auditoría.
    sonido_ambiente: str | None = None
    #: Nombre del grito aislado y aleatorio de esta fase (para
    #: `_play_sfx_named`), o `None`. Sólo la Fase 4, y sólo después del
    #: silencio súbito — ver `shake_de_silencio` y §4 del diseño: «los
    #: sonidos del Halcón pueden reaparecer de forma aislada y aleatoria».
    grito_aislado: str | None = None
    #: Qué decoración de fondo dibuja `dibujar_fondo` en esta fase, o `None`.
    #: `"bosque_cortado"` (Fase 4) y `"tumbas_conquistador"` (Fase 5) — ver
    #: `siluetas.py`. Contornos dibujados, no PNG: el mismo principio que ya
    #: usan los espíritus.
    decoracion: str | None = None


#: Las seis fases, en el orden en que se **bajan**. Cada tramo mide
#: `ALTO_FASE` filas — la misma partición que usa el generador, leída del
#: mismo sitio — y los umbrales se calculan en vez de escribirse.
#: Prefijo común de los cuatro ambientes nuevos (AUD-465).
_AMB = "sfx/environment/sfx_environment_"

FASES: tuple[Fase, ...] = (
    Fase(1, "EL CEMENTERIO DE TILARÁN", 0 * ALTO_FASE, "clear", ("ash", 5.0),
         gradacion=COLOR_PLENO, tinte=None, espiritu=None,
         rayos_por_minuto=0.0, ambiente=0.62),
    Fase(2, "EL VENADO", 1 * ALTO_FASE, "rain", ("ash", 14.0),
         gradacion=BLANCO_Y_NEGRO, tinte=None, espiritu=0,
         rayos_por_minuto=0.0, ambiente=0.50,
         sonido_ambiente=f"{_AMB}viento_de_bosque.wav"),
    Fase(3, "EL REY TERCIOPELO", 2 * ALTO_FASE, "storm", ("spores", 16.0),
         gradacion=GRISES_NEUTROS, tinte=None, espiritu=1,
         rayos_por_minuto=10.0, ambiente=0.44, tiene_slopes=True,
         # Reusa el `storm_ambient` que ya existía: lo nuevo no es el
         # fichero, es que por fin suena cuando el clima es tormenta.
         sonido_ambiente="sfx/environment/sfx_environment_storm_ambient.wav"),
    Fase(4, "EL GAVILÁN", 3 * ALTO_FASE, "rain", ("ash", 10.0),
         gradacion=SEPIA_VINTAGE, tinte=(TINTE_VINTAGE, ALFA_TINTE_VINTAGE),
         espiritu=2, rayos_por_minuto=0.0, ambiente=0.48,
         shake_de_silencio=True,
         sonido_ambiente="sfx/environment/sfx_environment_rain_ambient.wav",
         grito_aislado="sfx_environment_grito_de_gavilan",
         decoracion="bosque_cortado"),
    Fase(5, "LA PLANICIE DE LOS MUERTOS", 4 * ALTO_FASE, "clear", ("", 0.0),
         gradacion=NOCTURNO_AZULADO, tinte=None, espiritu=None,
         rayos_por_minuto=0.0, ambiente=0.16, luna_intermitente=True,
         sonido_ambiente=f"{_AMB}canto_ancestral.wav",
         decoracion="tumbas_conquistador"),
    Fase(6, "EL CAMINO HACIA PABURU", 5 * ALTO_FASE, "fog", ("spores", 26.0),
         gradacion=COLOR_PLENO, tinte=None, espiritu=None,
         rayos_por_minuto=0.0, ambiente=0.60, grietas_por_pisada=True,
         sonido_ambiente=f"{_AMB}resonancia_solemne.wav"),
)


def fase_en(baldosa_y: float) -> Fase:
    """La fase que corresponde a esa **fila** del mapa.

    Se recorre al revés y se devuelve la primera que ya empezó. Así añadir
    una fase es añadir una fila a la tabla, y ningún umbral se escribe dos
    veces.
    """
    for fase in reversed(FASES):
        if baldosa_y >= fase.desde_fila:
            return fase
    return FASES[0]
