"""
Module: stage4_1
System: src.stages.stage4_1
Academic Unit: V (color y gradación) + VII (clima y partículas)

NIVEL 4-1 — EL CEMENTERIO SAGRADO

La idea, en una frase: **Jhon y Jin atraviesan seis espacios distintos**, y el
cementerio cambia de piel —terreno, color, clima, sonido— en cada uno.
Reconstruido desde cero (AUD-467…470: ver `docs/niveles/13_STAGE_4_1.md` §0)
después de que el primer intento (AUD-462…466) heredara el pozo vertical del
diseño de La Cegua y el dueño del proyecto lo rechazara jugado: una repisa
que ocupa casi todo el ancho de pantalla se lee como una plataforma
horizontal genérica, no como un pozo. Esta versión es un **pasillo
horizontal** de verdad, con terreno propio por sección
(`tools/generate_all_assets.py::_gen_tileset_stage4_1`) — no el mismo suelo
con un filtro de color encima.

Lo que este escenario NO tiene, y por qué
==========================================
**Cero enemigos.** Las siluetas de Venado, Rey Terciopelo y Gavilán —ver
`siluetas.py`— son contornos sin colisión, sin IA y sin salud: testifican,
no atacan.

Lo que sí tiene
================
* **Seis fases** (`fases.py`), leídas de la **columna** del jugador — el
  4-1 se atraviesa de izquierda a derecha, no se desciende.
* **Gradación de color interpolada** por avance dentro de la sección
  (`PostProcessing.set_color_grading`, una matriz 3×3 real).
* **Un relámpago-linterna en la Fase 3**, una serpiente de fondo reptando
  entre los huesos, y una loma real (`Slope`, AUD-297) que se sube de
  verdad, no un parche decorativo.
* **Un camera shake único en la Fase 4** tras un silencio súbito, y una
  sombra de ave que cruza el cielo de vez en cuando después.
* **Un ciclo de luna en la Fase 5**: la luz ambiente oscila.
* **Grietas que se iluminan al paso en la Fase 6**: un rastro, no una
  barra de progreso acumulada.
* **Una cutscene de introducción** y **diálogo real** de los tres
  espíritus (`data/dialogues/stage4_1.json`), disparados por el TMX sin
  código nuevo — `CutsceneSystem` y `DialogueSystem` ya estaban completos.
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.framework.audio.dynamic_music import resolver_pista_de_musica
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.atencion import Atencion
from src.stages.stage4_1 import presencias, siluetas, trazado
from src.stages.stage4_1.fases import FASES, Fase, Gradacion, fase_en

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.framework.ecs import ZonaDeViento
    from src.framework.vfx.lighting import LightSource


#: La matriz identidad: cada canal de salida es el mismo canal de entrada.
#: Es lo que representa `gradacion=None` — "color pleno" — cuando hace falta
#: interpolar hacia o desde ella. Pública (sin `_`) porque las pruebas la
#: necesitan para comparar contra el objetivo de cada fase.
IDENTIDAD: tuple[int, ...] = (255, 0, 0, 0, 255, 0, 0, 0, 255)


class Stage4_1(StageScene):
    """4-1 — El Cementerio Sagrado."""

    STAGE_ID: str = "stage4_1"
    STAGE_NAME: str = "4-1  EL CEMENTERIO SAGRADO"
    ZONE: int = 4
    BGM_TRACK: str = "bgm_final_approach"
    TMX_PATH = "assets/maps/stage4_1/stage4_1.tmx"

    # ── Relámpagos (Fase 3) ───────────────────────────────────
    DURACION_DEL_RAYO = 0.35
    FUERZA_DEL_RAYO = 0.5
    #: AUD-551 — GAP-070 punto 3: "cuando el renderizado GPU genere un
    #: flash... se calcula un retraso de 0.2 a 1.5 segundos antes de
    #: disparar el sonido del trueno, simulando la distancia real" — la
    #: luz llega antes que el sonido. Antes el trueno sonaba en el mismo
    #: fotograma que el flash, instantáneo.
    ESPERA_DEL_TRUENO: tuple[float, float] = (0.2, 1.5)

    # ── El silencio y el shake (Fase 4) ────────────────────────
    #: A qué fracción del tramo ocurre el silencio. A mitad: ni al entrar
    #: (se leería como parte de la transición) ni al salir (se confundiría
    #: con la Fase 5).
    AVANCE_DEL_SILENCIO = 0.5
    DURACION_DEL_SHAKE = 0.45
    AMPLITUD_DEL_SHAKE = 14.0
    #: Cada cuánto puede sonar el grito aislado del Gavilán tras el silencio.
    #: Un rango, no un número fijo: un grito cada N segundos exactos se
    #: vuelve previsible a la tercera vez — el mismo motivo que ya usa
    #: `_espera_entre_rayos` para la tormenta de la Fase 3.
    ESPERA_ENTRE_GRITOS: tuple[float, float] = (4.0, 10.0)
    #: A qué distancia del jugador, en píxeles de mundo, puede sonar el
    #: grito — a la izquierda o a la derecha por igual (AUD-481). Ni tan
    #: cerca que se confunda con estar encima del jugador, ni tan lejos
    #: que el desvanecimiento por distancia (AUD-348) lo deje casi mudo.
    DISTANCIA_DEL_GRITO: tuple[float, float] = (150.0, 420.0)
    #: Cada cuánto cruza la sombra del Gavilán el cielo, y cuánto tarda en
    #: cruzar. La pieza que el primer intento (AUD-462…466) dejó fuera —
    #: hasta ahora la presencia del Gavilán era sólo sonora.
    ESPERA_ENTRE_SOMBRAS: tuple[float, float] = (6.0, 14.0)
    DURACION_DEL_CRUCE = 3.5

    # ── La luna de la Fase 4 (AUD-563) ──────────────────────────
    #: Posición y radio fijos en pantalla — como `_dibujar_sombra_de_ave`,
    #: no lleva paralaje: es el cielo, casi inmóvil. Dentro de la banda de
    #: `ALTURAS_DE_CRUCE` (60-110) para que la sombra, cuando cruza, pase
    #: cerca de verdad, no en otra franja del cielo.
    POSICION_LUNA_FASE4: tuple[int, int] = (600, 78)
    RADIO_LUNA_FASE4 = 22
    COLOR_LUNA_FASE4: tuple[int, int, int] = (225, 217, 195)
    ALFA_LUNA_FASE4 = 130

    # ── El escenario observa (AUD-492, GAP-065 §13 eslabón F4) ──
    #: Cuánto tiene que llevar quieto el jugador para que la Fase 4 le
    #: responda. Cuatro segundos es mucho más de lo que dura una pausa
    #: involuntaria y bastante menos de lo que aguanta quien no espera
    #: nada: quien se detiene a mirar lo consigue, quien atraviesa la fase
    #: caminando no lo ve nunca — que es exactamente el punto 24-25 de la
    #: crítica de diseño, *«detenerse también es jugar»*.
    QUIETUD_QUE_REVELA = 4.0
    #: Qué proporción de los gritos suena a la espalda del jugador. No 1.0:
    #: ver el docstring de `_posicion_del_grito`.
    PROPORCION_DE_GRITOS_A_LA_ESPALDA = 0.75
    #: Tras responder a una quietud, cuánto tarda en poder volver a
    #: hacerlo. Sin esta espera, quedarse parado dispararía una sombra tras
    #: otra y la recompensa por detenerse se convertiría en una fuente
    #: continua — se aprende a explotar, no a mirar.
    ESPERA_TRAS_REVELAR = 12.0

    # ── Sonidos aislados y direccionales (AUD-546) ──────────────
    #: Cada cuánto puede sonar un crujido/ráfaga de `Fase.sonidos_aislados`.
    #: Mismo rango que el pedido original: *«cada 8-15 segundos»*. Un
    #: rango, no un número fijo — mismo motivo que `ESPERA_ENTRE_GRITOS`.
    ESPERA_ENTRE_SONIDOS_AISLADOS: tuple[float, float] = (8.0, 15.0)
    #: A qué distancia del jugador, en píxeles de mundo — fuera del cuadro
    #: visible la mayoría de las veces, que es el punto: *«en los bordes
    #: de la pantalla»*.
    DISTANCIA_DEL_SONIDO_AISLADO: tuple[float, float] = (250.0, 500.0)

    # ── La música por fase (AUD-493, ampliado en AUD-546) ───────
    #: Cuánto tarda en entrar la pista de cada fase. Se aplica en las seis
    #: fronteras, no sólo en la Fase 6: un corte seco entre pistas se oye
    #: como un fallo de reproducción, no como una transición de escena.
    FUNDIDO_DE_LA_MUSICA_MS = 2500

    # ── La Bruja: percepción falsa de la Fase 3 (AUD-475) ──────
    #: En qué relámpagos —contados desde que se entra a la Fase 3— aparece,
    #: una fracción de segundo, «en la rama de un árbol». Dos, no más: la
    #: crítica de diseño pide sembrar duda, no un patrón nuevo que aprender
    #: («si veo la bruja, no pasa nada» sería tan previsible como al revés).
    #: No hay sonido, no hay diálogo, no cambia nada del estado del nivel —
    #: es exactamente lo que la vuelve una percepción falsa y no un evento.
    RAYOS_CON_BRUJA: frozenset[int] = frozenset({2, 4})

    # ── La anomalía ambigua de la Fase 1 (AUD-478, GAP-059) ─────
    #: Cada cuánto puede aparecer la figura entre las tumbas. Un rango
    #: amplio y no un número fijo, igual que `ESPERA_ENTRE_GRITOS`: si
    #: apareciera con reloj, el jugador aprendería el patrón en vez de
    #: dudar de lo que vio — y podría no aparecer en absoluto en un
    #: recorrido rápido, que es exactamente el punto («si no la viste, no
    #: pasa nada»).
    ESPERA_ENTRE_ANOMALIA_FASE1: tuple[float, float] = (20.0, 40.0)
    #: Menos de un segundo (punto 7 de la crítica de diseño): lo bastante
    #: breve para que quien parpadee no la vea.
    DURACION_ANOMALIA_FASE1 = 0.4

    # ── Las apariciones previas del Venado (Fase 2, AUD-479) ─────
    #: A qué fracción del tramo llega `DESVIO_COLUMNA_DIALOGO` — de ahí en
    #: adelante el Venado vuelve al fundido continuo normal, porque ya
    #: habló y dejó de tener sentido que sólo se le vea a destellos.
    AVANCE_ANTES_DEL_DIALOGO = trazado.DESVIO_COLUMNA_DIALOGO / trazado.ANCHO_SECCION
    #: Cada cuánto puede asomar, y cuánto dura cada destello. Más largo que
    #: la anomalía de la Fase 1 (1,5-3 s, no «menos de un segundo»): aquí
    #: el jugador sí se supone que reconoce que era un ciervo, sólo que
    #: fuera de alcance — no que dude si lo vio.
    ESPERA_ENTRE_APARICIONES_VENADO: tuple[float, float] = (4.0, 9.0)
    DURACION_APARICION_VENADO: tuple[float, float] = (1.5, 3.0)

    # ── La pausa antes del diálogo de la Serpiente (Fase 3, AUD-480) ─
    #: A qué fracción del tramo, antes y después de
    #: `AVANCE_ANTES_DEL_DIALOGO`, el viento está reducido — una ventana
    #: alrededor del punto donde habla el Rey Terciopelo, no un instante.
    MARGEN_PAUSA_VIENTO_ANTES = 0.03
    MARGEN_PAUSA_VIENTO_DESPUES = 0.05
    #: A qué fracción de su fuerza normal baja el viento durante la pausa.
    #: No a cero: sigue siendo el mismo bosque ventoso, sólo que respira.
    FRACCION_VIENTO_EN_PAUSA = 0.1

    # ── El ciclo de luna (Fase 5) ──────────────────────────────
    PERIODO_DE_LA_LUNA = 6.0
    #: AUD-476 — 0.06 era casi negro de verdad, sostenido cada ciclo, no un
    #: instante. La crítica de diseño (2026-08-14, puntos 9-10) lo señaló:
    #: *«no puedo ver bien» ≠ «no puedo jugar»* — y el propio proyecto ya
    #: tiene una referencia de cuánto es «casi negro» para un momento
    #: dramático: la introducción de Paburu baja hasta 0,18 y lo sostiene
    #: **un instante** (`boss_paburu/intro.py`, comentario junto a
    #: `Penumbra`). El mínimo de la luna se sostiene medio ciclo cada
    #: 6 s, no un instante — así que va por encima de esa referencia, no
    #: igual, para que siga siendo navegable el rato más largo que dura.
    AMBIENTE_MIN_LUNA = 0.20
    AMBIENTE_MAX_LUNA = 0.48

    # ── El canto que orienta (Fase 5, AUD-488) ──────────────────
    #: Cada cuánto llama el canto desde `trazado.COLUMNA_DEL_CANTO`. Un
    #: rango estrecho, al revés que el grito del Gavilán: éste tiene que
    #: ser **fiable** para servir de brújula. Un intervalo impredecible
    #: valdría para inquietar, no para orientarse.
    ESPERA_ENTRE_CANTOS: tuple[float, float] = (5.0, 7.0)
    #: Volumen del canto con la luna alta y con la luna oculta. GAP-063
    #: pide que *algo* dependa del ciclo lunar —hoy no depende nada— y que
    #: el oído sustituya a la vista: cuanto menos se ve, más claro llama.
    VOLUMEN_DEL_CANTO: tuple[float, float] = (0.30, 0.75)

    # ── Las grietas que se iluminan al paso (Fase 6) ───────────
    DISTANCIA_DE_GRIETA = 40.0
    SUBIDA_DE_GRIETA = 0.25
    BAJADA_DE_GRIETA = 1.6
    INTENSIDAD_MAX_GRIETA = 0.9

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        #: Índice de la fase actual, 0 a 5. Empieza fuera de rango para que
        #: el primer `update` **siempre** aplique la Fase 1 — con 0 aquí, la
        #: Fase 1 nunca se aplicaría (el fallo de «se inicializa a lo mismo
        #: que se compara», invisible sin comentarlo).
        self._fase_actual: int = -1
        self._tiempo: float = 0.0
        #: La gradación y el tinte de la fase anterior: de aquí interpola la
        #: gradación de la fase actual a lo largo del tramo.
        self._gradacion_previa: Gradacion = None
        self._tinte_previo: tuple[tuple[int, int, int], float] | None = None
        self._rayo: float = 0.0
        self._proximo_rayo: float = 0.0
        #: AUD-551 — cuenta atrás hasta que suene el trueno de este
        #: relámpago; `<= 0.0` y sin `math.inf` significa "no hay
        #: ninguno pendiente" (`_actualizar_rayos` lo consulta cada
        #: fotograma con `> 0.0`, así que un valor en reposo de 0.0 no
        #: dispara nada por accidente).
        self._trueno_pendiente: float = 0.0
        #: AUD-551 — GAP-070 "Diálogo de la Serpiente"/"del Halcón": qué
        #: índices de espíritu (`Fase.espiritu`, 0=Venado/1=Rey
        #: Terciopelo/2=Gavilán) ya reprodujeron su línea de voz, para
        #: que suene una sola vez por partida y no en cada fotograma que
        #: `_espiritu_liberado` sigue devolviendo `True`.
        self._espiritus_con_voz: set[int] = set()
        #: AUD-551 — GAP-070 "Pisadas de Energía Verde": qué grietas
        #: (por índice) ya sonaron su campanilla al terminar de
        #: encenderse, para no repetirla mientras el jugador se queda
        #: parado encima con la grieta ya a intensidad máxima.
        self._grietas_con_campanilla: set[int] = set()
        self._shake_disparado: bool = False
        #: Cuándo suena el próximo grito aislado del Gavilán (Fase 4, sólo
        #: tras el silencio — ver `_actualizar_grito_del_gavilan`).
        self._proximo_grito: float = 0.0
        #: AUD-546 — cuándo suena el próximo crujido/ráfaga de
        #: `Fase.sonidos_aislados` (ver `_actualizar_sonidos_aislados`).
        self._proximo_sonido_aislado: float = 0.0
        #: Cuándo cruza la próxima sombra del Gavilán, y en qué punto de su
        #: cruce va (-1 = no está cruzando ahora mismo).
        self._proxima_sombra: float = 0.0
        self._sombra_progreso: float = -1.0
        #: La variante de este cruce (AUD-513, GAP-062 punto 10): si se ve
        #: la silueta reconocible o una mancha difusa, a qué altura, y en
        #: qué dirección. Se fija una vez al empezar el cruce
        #: (`_iniciar_cruce_de_sombra`), no en cada fotograma.
        self._sombra_es_identificable: bool = False
        self._sombra_altura: int = 80
        self._sombra_izquierda_a_derecha: bool = True
        #: Cuántos relámpagos han caído desde que se entró a la Fase 3, y si
        #: el que está cayendo ahora mismo trae a la Bruja (AUD-475).
        self._rayos_en_fase3: int = 0
        self._bruja_este_rayo: bool = False
        #: La anomalía ambigua de la Fase 1 (AUD-478): cuánto le queda de
        #: visible (0 = apagada) y cuándo puede aparecer la próxima vez.
        self._anomalia_fase1: float = 0.0
        self._proxima_anomalia_fase1: float = 0.0
        #: Las apariciones previas del Venado (Fase 2, AUD-479): cuánto le
        #: queda visible al destello actual, y cuándo asoma el próximo.
        self._venado_visible: float = 0.0
        self._proxima_aparicion_venado: float = 0.0
        #: La pausa del viento antes del diálogo del Rey Terciopelo
        #: (Fase 3, AUD-480): la `ZonaDeViento` real del mapa (encontrada
        #: la primera vez que hace falta, no en `__init__` — el ECS del
        #: escenario todavía no existe aquí), su fuerza original, y si
        #: está reducida ahora mismo.
        self._viento_zona: ZonaDeViento | None = None
        self._viento_fuerza_original: pygame.Vector2 | None = None
        self._viento_reducido: bool = False
        #: La fricción escala con la lluvia (Fase 2, AUD-513): el
        #: Qué material de fábrica es cada `ZonaDeFriccion` de la Fase 2
        #: ("musgo" o "lodo"), recordado por id de entidad la primera vez
        #: que se ve — AUD-522: desde que el musgo resbala (`inercia`) y el
        #: lodo frena (`multiplicador`), hace falta saber cuál es cada una
        #: para escalar el campo correcto, no sólo un número de fábrica.
        self._frenos_de_fabrica: dict[int, str] = {}
        #: Las luces de las grietas de la Fase 6 — apagadas de fábrica en el
        #: TMX, encendidas por proximidad y no permanentes.
        self._grietas: list[LightSource] = []
        self._intensidad_grieta: dict[int, float] = {}
        #: Lo que el escenario sabe del jugador (AUD-492): cuánto lleva
        #: quieto y hacia dónde mira. Es la medida; la decisión de qué
        #: hacer con ella vive en `_actualizar_quietud_del_gavilan` y en
        #: `_posicion_del_grito`, no dentro de `Atencion`.
        self._atencion = Atencion()
        #: Cuánto falta para que la quietud pueda volver a revelar algo.
        self._proxima_revelacion: float = 0.0
        #: Qué pista está sonando ahora mismo (AUD-493). No se puede saber
        #: todavía —el TMX no está cargado en `__init__`—, así que lo fija
        #: `on_stage_start`, que corre **después** de que `StageScene`
        #: arranque la música del mapa. Si aquí se dejara `None` y no se
        #: corrigiera allí, la primera comparación contra la Fase 1 (que
        #: pide silencio) daría `None == None` y la música del TMX seguiría
        #: sonando el nivel entero: el defecto exacto que esto arregla,
        #: reintroducido por la puerta de atrás.
        self._musica_sonando: str | None = None
        #: Cuándo vuelve a llamar el canto de la Fase 5 (AUD-488).
        self._proximo_canto: float = 0.0
        #: La secuencia de despertar antes del corte a la Fase 4-2
        #: (AUD-513, GAP-064 punto 25): una sola vez por visita a la Fase 6.
        self._despertar_disparado: bool = False
        #: La tumba que susurra (Fase 1, AUD-513): si el próximo
        #: acercamiento puede volver a sonar.
        self._susurro_armado: bool = True
        #: La memoria espacial (Fase 1, AUD-513): cuánto avanzó el jugador
        #: dentro de la Fase 1, y si volvió atrás lo bastante como para que
        #: el fantasma deje de comportarse como la primera vez.
        self._columna_maxima_fase1: float = 0.0
        self._regreso_a_la_tumba: bool = False
        #: Las presencias errantes de fondo (Fase 2/3/5, AUD-562): cuánto
        #: le queda visible a cada una (por `PresenciaErrante.id`) y
        #: cuándo puede volver a aparecer. Perezoso a propósito — todas
        #: arrancan "aún no le tocó" la primera vez que se lee su entrada
        #: en el diccionario, no aquí.
        self._presencia_visible: dict[str, float] = {}
        self._presencia_proxima: dict[str, float] = {}

    # ── Ciclo de vida ─────────────────────────────────────────

    def _setup_lighting(self) -> None:
        """Captura las luces de las grietas de la Fase 6.

        Se engancha aquí y no en `on_stage_start` por el mismo motivo que ya
        documentó el diseño anterior: `_stage_lights` todavía está vacía
        cuando corre `on_stage_start`, y `_setup_lighting` es el método que
        **crea** esa lista.

        Todas las luces del mapa son grietas —este TMX no tiene ninguna
        otra—, así que la lista entera vale tal cual, en el mismo orden en
        que las escribió `trazado.grietas_de_pisada()` y el generador.
        """
        super()._setup_lighting()
        self._grietas = list(self._stage_lights)
        self._intensidad_grieta.clear()

    def on_stage_start(self) -> None:
        """Anota qué música dejó puesta el motor, para no reponerla de más.

        AUD-493 — `StageScene` ya arrancó `bgm_track` del TMX unas líneas
        antes de llamar aquí. La tabla de fases (`fases.FASES`) es la que
        decide qué suena en cada tramo (`_actualizar_musica_de_fase`), y
        necesita saber qué ya está sonando para no reiniciar la pista si
        coincide con la que pide la fase.

        AUD-546 — antes esto existía para **parar** la música del mapa,
        porque la Fase 1 pedía silencio (`fases.MUSICA_DEL_DESPERTAR`
        sólo sonaba en la Fase 6). Ahora `bgm_track` del TMX ya es la
        pista de la Fase 1 (`bgm_stage4_1_fase1`), así que en el caso
        normal esto sólo confirma que coinciden — no hay nada que parar.
        """
        super().on_stage_start()
        if self._stage_data is not None:
            self._musica_sonando = self._stage_data.bgm_track or None

    # ── Actualización ─────────────────────────────────────────

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._player is None or self._stage_data is None:
            return
        self._tiempo += dt
        # Se mide **antes** que nada: los sistemas que reaccionan a la
        # atención (el grito y la quietud de la Fase 4) leen el estado de
        # este fotograma, no el del anterior.
        self._atencion.observar(self._player, dt)
        self._actualizar_fase()
        self._actualizar_gradacion()
        self._actualizar_ambiente_de_fase()
        self._actualizar_canto_ancestral(dt)
        self._actualizar_anomalia_fase1(dt)
        self._actualizar_tumba_susurrante()
        self._actualizar_memoria_espacial()
        self._actualizar_apariciones_previas_del_venado(dt)
        self._actualizar_friccion_de_la_lluvia()
        self._actualizar_pausa_de_la_serpiente()
        self._actualizar_rayos(dt)
        self._actualizar_silencio_y_shake()
        self._actualizar_sonidos_aislados(dt)
        self._actualizar_grito_del_gavilan(dt)
        self._actualizar_quietud_del_gavilan(dt)
        self._actualizar_sombra_del_gavilan(dt)
        self._actualizar_grietas(dt)
        self._actualizar_presencias_errantes(dt)
        self._actualizar_mensaje_final()
        self._actualizar_secuencia_de_despertar()
        self._actualizar_voz_del_espiritu()
        self._actualizar_pasos_de_luz()

    @property
    def fase(self) -> Fase:
        """La fase en la que está el jugador ahora mismo.

        Se mira la **columna**, no la fila: el 4-1 es un pasillo, se
        atraviesa de izquierda a derecha (AUD-467).
        """
        if self._player is None:
            return FASES[0]
        return fase_en(self._player.rect.centerx / settings.TILE_SIZE)

    def _avance_en_fase(self, fase: Fase) -> float:
        """0 al entrar en la fase, 1 al salir. Para interpolar."""
        if self._player is None:
            return 0.0
        recorrido = (self._player.rect.centerx / settings.TILE_SIZE
                     - fase.desde_columna)
        return max(0.0, min(1.0, recorrido / trazado.ANCHO_SECCION))

    def _actualizar_fase(self) -> None:
        """Aplica la fase nueva, si el jugador cambió de tramo.

        Sólo se aplica **al cambiar**: llamar a `set_climate` en cada
        fotograma vaciaría el emisor de la tormenta sesenta veces por
        segundo y no se vería llover.
        """
        fase = self.fase
        if fase.numero - 1 == self._fase_actual:
            return
        # Si ya veníamos de una fase, se interpola desde su gradación. Si
        # ésta es la primera vez que corre `update` —incluido un arranque
        # en frío que cae directo en una fase avanzada, como al cargar una
        # partida guardada— no hay «fase anterior» real: se interpola desde
        # el color pleno, no desde la fase en la que se aterriza. El defecto
        # que esto reemplaza usaba `fase` (la actual) como si fuera la
        # anterior, y la gradación aparecía de golpe en vez de interpolar —
        # invisible arrancando siempre en la Fase 1, donde no hay nada de lo
        # que venir, y sólo visible saltando a mitad de nivel.
        if self._fase_actual >= 0:
            anterior = FASES[self._fase_actual]
            self._gradacion_previa = anterior.gradacion
            self._tinte_previo = anterior.tinte
        else:
            self._gradacion_previa = None
            self._tinte_previo = None
        self._fase_actual = fase.numero - 1

        self._cambiar_clima(fase.clima)
        self._ambient_particles.set_effect(*fase.particulas)
        # El ambiente de la fase pasa a ser la base sobre la que el ciclo
        # día/noche modula. Se escribe en `_ambiente_base` y no en el
        # sistema de luz directamente: si se escribiera directo,
        # `_aplicar_hora` lo pisaría en el siguiente fotograma.
        self._ambiente_base = fase.ambiente
        self._aplicar_hora()
        self._proximo_rayo = self._espera_entre_rayos()
        self._actualizar_sonido_de_fase(fase)
        self._actualizar_musica_de_fase(fase)
        # AUD-546 — se reinicia en cada frontera, tenga o no sonidos
        # aislados esta fase: sin esto, entrar a una fase silenciosa tras
        # una fase con crujidos frecuentes heredaría un temporizador ya
        # casi agotado y el primer crujido de la fase nueva sonaría
        # sospechosamente rápido.
        self._proximo_sonido_aislado = (
            self._espera_entre_sonidos_aislados() if fase.sonidos_aislados else 0.0
        )
        if fase.numero == 1:
            self._anomalia_fase1 = 0.0
            self._proxima_anomalia_fase1 = self._espera_anomalia_fase1()
        if fase.numero == 2:
            self._venado_visible = 0.0
            self._proxima_aparicion_venado = self._espera_aparicion_venado()
        if fase.numero == 3:
            self._rayos_en_fase3 = 0
            self._bruja_este_rayo = False
        if fase.numero == 5:
            self._proximo_canto = random.uniform(*self.ESPERA_ENTRE_CANTOS)
        if fase.numero == 4:
            self._shake_disparado = False
            self._proximo_grito = self._espera_entre_gritos()
            self._sombra_progreso = -1.0
            self._proxima_sombra = self._espera_entre_sombras()
            self._proxima_revelacion = 0.0
        if fase.numero == 6:
            self._despertar_disparado = False
        # La racha de quietud no cruza de una fase a otra (AUD-492): quien
        # llegó parado al borde de la sección no ha estado observando
        # *ésta*, y darle la revelación en el primer fotograma la volvería
        # gratis.
        self._atencion.reiniciar()
        if self._banner is not None and fase.numero > 1:
            self._banner.play(f"FASE {fase.numero}", fase.nombre)

    def _actualizar_sonido_de_fase(self, fase: Fase) -> None:
        """Cruza al ambiente propio de la fase, si tiene uno (AUD-465).

        `WeatherSystem.get_ambient_audio_key()` sólo se consulta una vez, al
        entrar al escenario — nunca cuando cambia el clima acto a acto o fase
        a fase. Sin esto, la tormenta de la Fase 3 se ve pero no se oye. Un
        solo canal de ambiente: cruzar es reemplazar, no apilar, así que una
        fase sin `sonido_ambiente` (la Fase 1) deja sonando lo que ya sonaba
        — que para la Fase 1 es nada, el silencio con el que arranca el
        nivel.
        """
        audio = self.audio
        if audio is None or fase.sonido_ambiente is None:
            return
        ruta = settings.ASSETS_DIR / fase.sonido_ambiente
        if not ruta.exists():
            return
        if getattr(audio, "_ambient_active", False):
            audio.crossfade_ambient(ruta, duration=1.5, volume=0.3)
        else:
            audio.play_ambient(ruta, volume=0.3)

    def _actualizar_musica_de_fase(self, fase: Fase) -> None:
        """Pone —o quita— la música que pide esta fase (AUD-493, AUD-546).

        GAP-059 punto 5, GAP-064 puntos 13-14 y GAP-065 §12 describen el
        defecto original: una sola pista (`bgm_final_approach`) para las
        seis fases, así que la aproximación a Paburu —la carta emocional
        más fuerte del nivel— sonaba desde el primer paso del cementerio.
        AUD-493 lo resolvió reservando esa pista para la Fase 6 y dejando
        las otras cinco en silencio de música (apoyadas en su
        `sonido_ambiente`).

        AUD-546 — decisión del dueño: llegó material de autor, una pista
        distinta por fase (`fases.MUSICA_POR_FASE`). El problema que
        resolvía AUD-493 ya no existe —no hay una sola pista que se
        desgaste—, así que las seis fases suenan, cada una con la suya;
        `Fase.musica` sigue siendo `None` sólo si algún día una fase
        vuelve a pedir silencio explícito.

        Sólo actúa cuando la pista pedida cambia. Llamar a `play_music`
        cada vez que se cruza una frontera reiniciaría el tema desde el
        principio aunque fuera el mismo, que es el defecto que
        `_actualizar_fase` ya evita para el clima y las partículas.

        El fundido de entrada no es decorativo: entre pistas distintas, un
        corte seco se oye como un fallo de reproducción, no como una
        transición de escena.
        """
        if fase.musica == self._musica_sonando:
            return
        self._musica_sonando = fase.musica
        audio = self.audio
        if audio is None:
            return
        if fase.musica is None:
            audio.stop_music()
            return
        pista = resolver_pista_de_musica(fase.musica)
        if pista is not None:
            audio.play_music(pista, fundido_ms=self.FUNDIDO_DE_LA_MUSICA_MS)

    # ── Gradación de color (Unidad V) ──────────────────────────

    @staticmethod
    def _lerp_gradacion(a: Gradacion, b: Gradacion, t: float) -> tuple[int, ...]:
        ga = a if a is not None else IDENTIDAD
        gb = b if b is not None else IDENTIDAD
        return tuple(round(ga[i] + (gb[i] - ga[i]) * t) for i in range(9))

    def _actualizar_gradacion(self) -> None:
        """Interpola de la gradación anterior a la de esta fase.

        Se interpola por **avance dentro del tramo**, no por tiempo — igual
        que el diseño anterior interpolaba la posición de la luna entre
        actos: el cambio se ve al caminar, no al esperar quieto.
        """
        fase = self.fase
        t = self._avance_en_fase(fase)
        if self._gradacion_previa is None and fase.gradacion is None:
            self._post_processing.clear_color_grading()
        else:
            self._post_processing.set_color_grading(
                *self._lerp_gradacion(self._gradacion_previa, fase.gradacion, t))

        # El tinte vintage de la Fase 4, entrando y saliendo con la misma
        # curva que la gradación — son dos sistemas separados en
        # `PostProcessing` y cada uno se interpola con su propio alfa.
        alfa_previa = self._tinte_previo[1] if self._tinte_previo is not None else 0.0
        if fase.tinte is not None:
            color, alfa_objetivo = fase.tinte
            alfa = alfa_previa + (alfa_objetivo - alfa_previa) * t
        else:
            color = self._tinte_previo[0] if self._tinte_previo is not None else (0, 0, 0)
            alfa = alfa_previa * (1.0 - t)
        if alfa <= 0.001:
            self._post_processing.clear_tint()
        else:
            self._post_processing.set_tint(color, alfa)

    def _actualizar_ambiente_de_fase(self) -> None:
        """El ciclo de luna de la Fase 5: la luz ambiente oscila.

        Las demás fases dejan `_ambiente_base` tal como lo puso
        `_actualizar_fase` — sólo la Planicie de los Muertos lo mueve cada
        fotograma.
        """
        fase = self.fase
        if not fase.luna_intermitente:
            return
        ciclo = 0.5 + 0.5 * math.sin(self._tiempo * (math.tau / self.PERIODO_DE_LA_LUNA))
        self._ambiente_base = (self.AMBIENTE_MIN_LUNA
                                + (self.AMBIENTE_MAX_LUNA - self.AMBIENTE_MIN_LUNA) * ciclo)
        self._aplicar_hora()
        # AUD-551 — GAP-070 punto 8: el bucle de ambiente (el canto de
        # fondo, no la voz espacial que ya modula `_actualizar_canto_
        # ancestral`) también respira con la luna. Antes sólo la voz
        # extra lo hacía; el colchón sonoro sonaba a volumen fijo todo
        # el tramo. Mismo rango que la voz (`VOLUMEN_DEL_CANTO`), para
        # que las dos capas suban y bajen juntas.
        audio = self.audio
        if audio is not None:
            flojo, fuerte = self.VOLUMEN_DEL_CANTO
            audio.set_ambient_volume(flojo + (fuerte - flojo) * self.luna_oculta)

    @property
    def luna_oculta(self) -> float:
        """Cuánto está escondida la luna ahora mismo: 0 alta, 1 oculta.

        AUD-488 — se deriva de `_ambiente_base`, que es donde
        `_actualizar_ambiente_de_fase` escribe el ciclo, para que no haya
        dos senoidales que puedan desincronizarse. Fuera de la Fase 5 no
        significa nada y devuelve 0.
        """
        if not self.fase.luna_intermitente:
            return 0.0
        recorrido = self.AMBIENTE_MAX_LUNA - self.AMBIENTE_MIN_LUNA
        if recorrido <= 0.0:
            return 0.0
        alto = (self._ambiente_base - self.AMBIENTE_MIN_LUNA) / recorrido
        return max(0.0, min(1.0, 1.0 - alto))

    def _actualizar_canto_ancestral(self, dt: float) -> None:
        """El canto llama desde un punto fijo, y llama más fuerte a oscuras.

        GAP-063: en la Planicie de los Muertos *«el sonido no es
        navegación, es un solo bucle ambiental»* —volumen constante, sin
        dirección— y *«nada depende de si la luna está arriba o abajo»*.
        Las dos cosas se arreglan con el mismo mecanismo: un canto
        espacial (`_play_sfx_spatial`, que el motor ya tenía y que hasta
        AUD-481 no usaba nadie) desde `trazado.COLUMNA_DEL_CANTO`, con el
        volumen atado al ciclo lunar.

        El bucle de ambiente de la fase no se toca: sigue siendo la cama
        sonora. Esto es una voz *encima*, que sí tiene sitio en el mundo.
        """
        fase = self.fase
        if not fase.luna_intermitente or self._player is None:
            return
        self._proximo_canto -= dt
        if self._proximo_canto > 0.0:
            return
        self._proximo_canto = random.uniform(*self.ESPERA_ENTRE_CANTOS)
        flojo, fuerte = self.VOLUMEN_DEL_CANTO
        volumen = flojo + (fuerte - flojo) * self.luna_oculta
        self._play_sfx_spatial(
            "sfx_environment_canto_ancestral",
            trazado.COLUMNA_DEL_CANTO * settings.TILE_SIZE,
            volume=volumen,
        )

    # ── La anomalía ambigua de la Fase 1 (AUD-478, GAP-059) ──────

    def _espera_anomalia_fase1(self) -> float:
        return random.uniform(*self.ESPERA_ENTRE_ANOMALIA_FASE1)

    def _actualizar_anomalia_fase1(self, dt: float) -> None:
        """Cuenta hacia la próxima aparición de la figura, o hacia que se
        apague la que ya está visible.

        Sólo corre dentro de la Fase 1 — fuera de ella se apaga sin dejar
        el contador a medias, igual que `_bruja_este_rayo` se reinicia al
        salir de la Fase 3. No toca sonido, disparadores ni diálogo: es
        exactamente lo que la vuelve ambigua y no un evento (mismo
        principio que la Bruja, AUD-475).
        """
        if self.fase.numero != 1:
            self._anomalia_fase1 = 0.0
            return
        if self._anomalia_fase1 > 0.0:
            self._anomalia_fase1 = max(0.0, self._anomalia_fase1 - dt)
            return
        self._proxima_anomalia_fase1 -= dt
        if self._proxima_anomalia_fase1 <= 0.0:
            self._anomalia_fase1 = self.DURACION_ANOMALIA_FASE1
            self._proxima_anomalia_fase1 = self._espera_anomalia_fase1()

    # ── La tumba que susurra (Fase 1, AUD-513, GAP-059 punto 2) ──
    #
    # *«Tumbas con reacciones distintas: una con sonido al acercarse»*.
    # Se dispara una vez por acercamiento —no un bucle mientras el jugador
    # esté cerca, que se leería como una zona de ambiente más— y vuelve a
    # armarse en cuanto el jugador se aleja lo bastante, para que un
    # segundo acercamiento (a pie, sin recargar el nivel) también lo oiga.
    DISTANCIA_TUMBA_SUSURRO = 48.0
    DISTANCIA_REARME_SUSURRO = 100.0

    def _actualizar_tumba_susurrante(self) -> None:
        if self.fase.numero != 1 or self._player is None:
            self._susurro_armado = True
            return
        distancia = abs(self._player.rect.centerx
                        - trazado.COLUMNA_TUMBA_SUSURRO * settings.TILE_SIZE)
        if distancia <= self.DISTANCIA_TUMBA_SUSURRO and self._susurro_armado:
            self._susurro_armado = False
            self._play_sfx_spatial(
                "sfx_environment_cemetery_silence",
                trazado.COLUMNA_TUMBA_SUSURRO * settings.TILE_SIZE, volume=0.3,
            )
        elif distancia > self.DISTANCIA_REARME_SUSURRO:
            self._susurro_armado = True

    # ── La memoria espacial (Fase 1, AUD-513, GAP-059 punto 10) ──
    #
    # *«El jugador piensa: estoy seguro de que antes estaba diferente»*.
    # Se mide cuánto avanzó el jugador dentro de la Fase 1 —no todo el
    # nivel: retroceder desde la Fase 2 para volver a la 1 ya es, de por
    # sí, la acción que el punto describe— y si vuelve a pasar por la
    # tumba de Teresa después de haber llegado bastante más lejos, el
    # fantasma deja de comportarse como la primera vez: no desaparece, se
    # queda a medio desvanecer. Nada de texto nuevo ni de estado que
    # guardar entre partidas: sólo la lectura visual cambia.
    UMBRAL_MEMORIA_ESPACIAL = 40

    def _actualizar_memoria_espacial(self) -> None:
        if self.fase.numero != 1 or self._player is None:
            return
        columna = self._player.rect.centerx / settings.TILE_SIZE
        self._columna_maxima_fase1 = max(self._columna_maxima_fase1, columna)
        self._regreso_a_la_tumba = (
            self._columna_maxima_fase1 - columna >= self.UMBRAL_MEMORIA_ESPACIAL
        )

    # ── Las apariciones previas del Venado (Fase 2, AUD-479) ─────

    def _espera_aparicion_venado(self) -> float:
        return random.uniform(*self.ESPERA_ENTRE_APARICIONES_VENADO)

    def _actualizar_apariciones_previas_del_venado(self, dt: float) -> None:
        """Antes de su diálogo, el Venado se deja ver y desaparece —no es
        un letrero encendido todo el tramo (GAP-060, puntos 6 y 9-12:
        *«se detiene, mira, desaparece»*). Deja de aplicar en cuanto el
        jugador cruza `AVANCE_ANTES_DEL_DIALOGO`: de ahí en adelante
        `_dibujar_espiritu` vuelve al fundido continuo normal por su
        cuenta, así que aquí basta con apagar el destello."""
        fase = self.fase
        if fase.numero != 2 or not fase.apariciones_previas:
            self._venado_visible = 0.0
            return
        if self._avance_en_fase(fase) >= self.AVANCE_ANTES_DEL_DIALOGO:
            self._venado_visible = 0.0
            return
        if self._venado_visible > 0.0:
            self._venado_visible = max(0.0, self._venado_visible - dt)
            return
        self._proxima_aparicion_venado -= dt
        if self._proxima_aparicion_venado <= 0.0:
            self._venado_visible = random.uniform(*self.DURACION_APARICION_VENADO)
            self._proxima_aparicion_venado = self._espera_aparicion_venado()

    # ── La fricción escala con la lluvia (Fase 2, AUD-513, GAP-060) ──
    #
    # Punto 14 del diseño: *«al principio, musgo = ligeramente resbaladizo;
    # después de lluvia intensa, mucho más»*. `SEGMENTOS_FASE2` declaraba
    # una constante por material —fija en toda la sección— así que la
    # lluvia se veía y se oía, pero no tocaba la física.
    #
    # AUD-522 — desde que el musgo resbala (`inercia`) y el lodo frena
    # (`multiplicador`, sin cambios), son dos campos distintos y hace falta
    # saber cuál es cada zona para escalar el correcto.
    #
    # No se identifica la zona por `ZonaDeFriccion.material`: el TMX ya
    # comprometido (`assets/maps/stage4_1/stage4_1.tmx`) trae `BG_Far` y
    # `BG_Mid` con arte pintado a mano —`tools/generate_stage4_1.py` se negó
    # a regenerar el mapa al comprobarlo (`tiene_arte_pintado()`), y forzarlo
    # habría borrado ese trabajo para añadir una sola propiedad— así que el
    # generador declara `material=` para el día que el mapa se regenere de
    # verdad, pero esta escena no puede depender de que ya esté ahí. En su
    # lugar, cada `ZonaDeFriccion` de la Fase 2 se reconoce por su propio
    # valor de fábrica la primera vez que se ve —`RESBALON_DEL_MUSGO` en
    # `inercia` o `FRENO_DEL_LODO` en `multiplicador`, los dos únicos pares
    # que coloca el generador— igual que `_actualizar_pausa_de_la_serpiente`
    # recuerda la fuerza original del viento antes de tocarla.
    #
    # AUD-474 le añade la otra mitad del diseño (punto 21, «la física vuelve
    # a la normalidad» tras liberar al espíritu): en cuanto el jugador
    # libera al Venado de verdad, la intensidad deja de subir con el avance
    # y cae a un valor bajo y fijo — el bosque se calma porque el Venado ya
    # no está atrapado, no porque el jugador haya caminado más.
    INTENSIDAD_LLUVIA_INICIAL = 0.35
    INTENSIDAD_LLUVIA_FINAL = 1.25
    INTENSIDAD_LLUVIA_TRAS_LIBERAR = 0.15
    #: Tolerancia para reconocer `RESBALON_DEL_MUSGO`/`FRENO_DEL_LODO` de
    #: fábrica: basta con no confundirlos entre sí ni con otra `FrictionZone`
    #: (hielo, goma) que este nivel no usa.
    TOLERANCIA_FRENO_DE_FABRICA = 0.01

    def _intensidad_de_lluvia(self, fase: Fase) -> float:
        if self._espiritu_liberado(fase):
            return self.INTENSIDAD_LLUVIA_TRAS_LIBERAR
        avance = self._avance_en_fase(fase)
        return (self.INTENSIDAD_LLUVIA_INICIAL
                + avance * (self.INTENSIDAD_LLUVIA_FINAL - self.INTENSIDAD_LLUVIA_INICIAL))

    def _actualizar_friccion_de_la_lluvia(self) -> None:
        fase = self.fase
        if fase.numero != 2:
            return
        from src.framework.ecs import ZonaDeFriccion

        intensidad = self._intensidad_de_lluvia(fase)
        for eid, zona in self._mundo.cada(ZonaDeFriccion):
            tipo = self._frenos_de_fabrica.get(eid)
            if tipo is None:
                if abs(zona.inercia - trazado.RESBALON_DEL_MUSGO) <= self.TOLERANCIA_FRENO_DE_FABRICA:
                    tipo = "musgo"
                elif abs(zona.multiplicador - trazado.FRENO_DEL_LODO) <= self.TOLERANCIA_FRENO_DE_FABRICA:
                    tipo = "lodo"
                else:
                    continue  # no es musgo ni lodo: otra ZonaDeFriccion, no se toca
                self._frenos_de_fabrica[eid] = tipo
            if tipo == "musgo":
                # Sin lluvia, sin resbalón (0); a intensidad de referencia
                # (1,0), exactamente `RESBALON_DEL_MUSGO` — con lluvia
                # intensa (hasta 1,25) resbala más que la referencia.
                zona.inercia = trazado.RESBALON_DEL_MUSGO * intensidad
            else:
                # `FRENO_DEL_LODO` frena hacia 1,0 tanto como haga falta
                # para llegar a la intensidad de hoy: con intensidad 1,0 el
                # resultado es el freno de fábrica tal cual; menos que eso
                # frena menos, más frena más.
                zona.multiplicador = 1.0 - (1.0 - trazado.FRENO_DEL_LODO) * intensidad

    # ── La pausa antes del diálogo de la Serpiente (Fase 3, AUD-480) ─

    #: AUD-513, GAP-061 punto 5 — el viento leía una única intensidad en
    #: toda la Fase 3 (*"una sola intensidad, no la progresión leve → fuerte
    #: → intermitente → combinado con pendientes → combinado con salto"*).
    #: `_factor_de_viento` da esa curva multiplicando la fuerza declarada en
    #: el TMX: leve al entrar, en plena fuerza a partir del 60 % del tramo
    #: —bastante antes de llegar a la segunda loma (`LOMAS_FASE3`, la más
    #: alta), para que «combinado con pendiente» sí sea cierto cuando el
    #: jugador la suba— y se queda fuerte el resto. El `periodo` que ya trae
    #: `ZonaDeViento` sigue dando el pulso intermitente encima de esto, sin
    #: que haga falta tocarlo.
    VIENTO_FACTOR_LEVE = 0.35
    VIENTO_FACTOR_FUERTE = 1.35
    VIENTO_AVANCE_A_PLENA_FUERZA = 0.6

    def _factor_de_viento(self, avance: float) -> float:
        t = min(1.0, avance / self.VIENTO_AVANCE_A_PLENA_FUERZA)
        return self.VIENTO_FACTOR_LEVE + t * (self.VIENTO_FACTOR_FUERTE - self.VIENTO_FACTOR_LEVE)

    def _actualizar_pausa_de_la_serpiente(self) -> None:
        """La fuerza del viento de la Fase 3, fotograma a fotograma: la
        escalada progresiva (arriba) multiplicada por la pausa alrededor
        del diálogo del Rey Terciopelo (GAP-061, punto 19): *«el jugador
        alcanza un descanso. El viento se detiene... la Serpiente habla.
        Después: el viento vuelve.»*

        La pausa no es el silencio total de la Fase 4 —eso apaga el clima
        entero y dispara un shake una sola vez—; aquí sólo baja la fuerza de
        la `ZonaDeViento` real del mapa a una fracción, y sube de vuelta en
        cuanto el jugador se aleja del punto del diálogo, tantas veces como
        haga falta (a diferencia del shake, esto no es «una vez por
        visita»: el jugador puede ir y volver).
        """
        if self.fase.numero != 3:
            if self._viento_reducido and self._viento_zona is not None:
                assert self._viento_fuerza_original is not None
                self._viento_zona.fuerza = self._viento_fuerza_original
                self._viento_reducido = False
            return
        if self._viento_zona is None:
            from src.framework.ecs import ZonaDeViento

            for _eid, zona in self._mundo.cada(ZonaDeViento):
                self._viento_zona = zona
                self._viento_fuerza_original = pygame.Vector2(zona.fuerza)
                break
        if self._viento_zona is None or self._viento_fuerza_original is None:
            return  # el mapa no trae ninguna zona de viento — nada que pausar

        avance = self._avance_en_fase(self.fase)
        en_pausa = (self.AVANCE_ANTES_DEL_DIALOGO - self.MARGEN_PAUSA_VIENTO_ANTES
                    <= avance
                    <= self.AVANCE_ANTES_DEL_DIALOGO + self.MARGEN_PAUSA_VIENTO_DESPUES)
        factor = self._factor_de_viento(avance)
        if en_pausa:
            factor *= self.FRACCION_VIENTO_EN_PAUSA
        self._viento_zona.fuerza = self._viento_fuerza_original * factor
        self._viento_reducido = en_pausa

    # ── El relámpago de la Fase 3 ──────────────────────────────

    def _espera_entre_rayos(self) -> float:
        por_minuto = self.fase.rayos_por_minuto
        if por_minuto <= 0.0:
            return math.inf
        return random.uniform(0.5, 1.5) * (60.0 / por_minuto)

    def _actualizar_rayos(self, dt: float) -> None:
        # AUD-551 — el trueno pendiente cuenta atrás siempre, no sólo
        # mientras dura el flash: `DURACION_DEL_RAYO` es 0.35s y la
        # espera del trueno llega hasta 1.5s, así que el `return`
        # temprano de abajo (mientras `self._rayo > 0.0`) lo habría
        # dejado congelado la mayor parte de su cuenta atrás.
        if self._trueno_pendiente > 0.0:
            self._trueno_pendiente -= dt
            if self._trueno_pendiente <= 0.0:
                self._trueno_pendiente = 0.0
                self._play_sfx_named("sfx_environment_thunder", volume=0.5)
        if self._rayo > 0.0:
            self._rayo = max(0.0, self._rayo - dt)
            fuerza = (self._rayo / self.DURACION_DEL_RAYO) ** 2
            self._lighting.ambient_brightness = min(
                1.0, self.fase.ambiente + self.FUERZA_DEL_RAYO * fuerza)
            return
        if self.fase.rayos_por_minuto <= 0.0:
            return
        self._proximo_rayo -= dt
        if self._proximo_rayo <= 0.0:
            self._rayo = self.DURACION_DEL_RAYO
            self._proximo_rayo = self._espera_entre_rayos()
            self._play_sfx_named("sfx_environment_screen_shake", volume=0.4)
            # AUD-551 — GAP-070 punto 3: el trueno de verdad llega
            # después, no en el mismo fotograma que el flash.
            self._trueno_pendiente = random.uniform(*self.ESPERA_DEL_TRUENO)
            if self.fase.numero == 3:
                self._rayos_en_fase3 += 1
                self._bruja_este_rayo = self._rayos_en_fase3 in self.RAYOS_CON_BRUJA
            else:
                self._bruja_este_rayo = False

    # ── El silencio súbito y el shake (Fase 4) ─────────────────

    def _actualizar_silencio_y_shake(self) -> None:
        """A mitad de la Fase 4, el clima calla de golpe y sacude la cámara.

        Una sola vez por visita a la fase (`_shake_disparado`, que
        `_actualizar_fase` reinicia al entrar). Sin causa visible: es la
        sensación de que algo acaba de pasar sin que el jugador lo viera.
        """
        fase = self.fase
        if not fase.shake_de_silencio or self._shake_disparado:
            return
        if self._avance_en_fase(fase) < self.AVANCE_DEL_SILENCIO:
            return
        self._shake_disparado = True
        self._cambiar_clima("clear")
        self._ambient_particles.set_effect("", 0.0)
        # El silencio es también sonoro: la lluvia de fondo corta en seco.
        # `stop_ambient` no tiene fundido — y aquí es lo que toca: es un
        # silencio *súbito*, no un fundido a negro.
        audio = self.audio
        if audio is not None and getattr(audio, "_ambient_active", False):
            audio.stop_ambient()
        self._camera.apply_shake(amplitude=self.AMPLITUD_DEL_SHAKE,
                                 duration=self.DURACION_DEL_SHAKE)
        self._play_sfx_named("sfx_environment_cemetery_silence", volume=0.5)
        # AUD-546 — «impacto de tensión»: el golpe de sub-graves que se
        # siente, no sólo se oye, justo cuando la cámara sacude. No
        # reemplaza a `cemetery_silence` (el hush con reverberación de
        # fondo): son dos capas del mismo instante, el silencio que se
        # abre y el golpe que lo rompe.
        self._play_sfx_named("sfx_environment_impacto_tension", volume=0.7)

    # ── El grito aislado del Gavilán ────────────────────────────

    def _espera_entre_gritos(self) -> float:
        return random.uniform(*self.ESPERA_ENTRE_GRITOS)

    def _posicion_del_grito(self) -> float:
        """Una coordenada de mundo a un lado del jugador — AUD-481,
        GAP-062 puntos 4-5 y 23: *«pájaro → izquierda... ahora desde otra
        dirección»*. Sin esto, el grito sonaría siempre desde el mismo
        sitio relativo (centrado, sin paneo), que es exactamente lo que
        vuelve inútil al oído como herramienta de orientación.

        AUD-492 — el lado ya no es una moneda al aire: la mayoría de las
        veces suena **a la espalda** del jugador, hacia donde no está
        mirando (`Atencion.a_su_espalda`). Ése es el eslabón F4 del
        GAP-065, «el escenario parece observar al jugador»: un grito que
        cae al azar y uno que evita tu campo de visión producen el mismo
        histograma de posiciones, pero sólo el segundo hace que el jugador
        se gire.

        No siempre, sin embargo: una regla sin excepción se aprende y deja
        de inquietar («si me giro, ahí estará»). Una de cada cuatro veces
        suena de frente, que es lo que impide leerlo como mecanismo.
        """
        if self._player is None:
            return 0.0
        distancia = random.uniform(*self.DISTANCIA_DEL_GRITO)
        if random.random() < self.PROPORCION_DE_GRITOS_A_LA_ESPALDA:
            return self._atencion.a_su_espalda(distancia)
        return self._player.rect.centerx + self._atencion.direccion * distancia

    # ── Sonidos aislados y direccionales (AUD-546) ──────────────
    #
    # Crujidos de ramas (Fase 2) u osamentas (Fase 3), ráfagas de viento
    # (Fase 3 y 4): mismo mecanismo que el grito del Gavilán —temporizador
    # aleatorio, posición de mundo a un lado del jugador, `_play_sfx_spatial`
    # para el paneo— generalizado a cualquier fase que declare
    # `Fase.sonidos_aislados`, con más de un sonido posible por fase.

    def _espera_entre_sonidos_aislados(self) -> float:
        return random.uniform(*self.ESPERA_ENTRE_SONIDOS_AISLADOS)

    def _posicion_del_sonido_aislado(self) -> float:
        """Una coordenada de mundo a un lado del jugador, casi siempre
        fuera del cuadro visible — pedido explícito: *«en los bordes de
        la pantalla... para generar la sensación de ser observado o
        seguido»*. A diferencia del grito del Gavilán (AUD-492, que
        prefiere la espalda del jugador), aquí no hay preferencia de
        lado: la premisa es "algo se mueve cerca", no "el escenario evita
        tu mirada" — ese eslabón ya lo cubre el Gavilán en su propia fase.
        """
        if self._player is None:
            return 0.0
        distancia = random.uniform(*self.DISTANCIA_DEL_SONIDO_AISLADO)
        lado = -1 if random.random() < 0.5 else 1
        return self._player.rect.centerx + lado * distancia

    def _actualizar_sonidos_aislados(self, dt: float) -> None:
        fase = self.fase
        if not fase.sonidos_aislados:
            return
        self._proximo_sonido_aislado -= dt
        if self._proximo_sonido_aislado <= 0.0:
            self._proximo_sonido_aislado = self._espera_entre_sonidos_aislados()
            sonido = random.choice(fase.sonidos_aislados)
            self._play_sfx_spatial(
                sonido, self._posicion_del_sonido_aislado(), volume=0.5)

    #: AUD-513, GAP-062 puntos 21-22 — *«un sonido tenue que la lluvia
    #: esconde y luego deja oír»*: antes la lluvia era un canal de clima y
    #: un canal de audio ambiente completamente independientes, sin ningún
    #: acoplamiento entre los dos. `_intensidad_de_lluvia_fase4` es una
    #: marea lenta —no ligada a ningún dato de clima real, que este motor
    #: no expone como intensidad— que sube y baja con el tiempo; cuando
    #: sube, el grito se escucha más bajo (la lluvia lo tapa), y cuando
    #: baja, más alto (hay un claro para oírlo).
    PERIODO_DE_LLUVIA_FASE4 = 9.0
    VOLUMEN_GRITO: tuple[float, float] = (0.25, 0.75)

    def _intensidad_de_lluvia_fase4(self) -> float:
        """0 = lluvia en su punto más fuerte (tapa el sonido), 1 = un claro."""
        fraccion = (math.sin(self._tiempo * math.tau / self.PERIODO_DE_LLUVIA_FASE4) + 1.0) / 2.0
        return fraccion

    def _actualizar_grito_del_gavilan(self, dt: float) -> None:
        """Tras el silencio, el Gavilán se deja oír de vez en cuando.

        Sin bucle y sin patrón: el guion (§4) pide *«sonidos que pueden
        reaparecer de forma aislada y aleatoria»*, no un segundo ambiente. Se
        activa sólo después de `_shake_disparado` — antes del silencio no
        hay nada que «reaparecer».

        AUD-481 — usa `_play_sfx_spatial` (paneo estéreo real,
        `AudioManager.play_sfx_at`) en vez del canal ciego
        `_play_sfx_named` que usaba antes: el motor ya sabía hacer esto,
        sólo que el Gavilán no se lo pedía.

        AUD-563 — pedido del dueño: *«que aparezca el Gavilán por la luna
        cuando suena»*. Antes el grito y la sombra corrían en
        temporizadores independientes —podían coincidir por azar o no—;
        ahora el propio grito dispara el cruce (`_iniciar_cruce_de_sombra`)
        en el mismo instante, siempre que la luna nueva de la Fase 4
        (`_dibujar_luna_de_fase4`) esté en el cielo y no haya ya una
        sombra cruzando (mismo guardián que ya usa
        `_actualizar_quietud_del_gavilan`, para no solapar dos cruces). El
        temporizador propio de la sombra (`_actualizar_sombra_del_gavilan`)
        se queda intacto para la actividad ambiental *entre* gritos —el
        guion también pide sombras «de vez en cuando», no sólo con el
        grito.
        """
        fase = self.fase
        if fase.grito_aislado is None or not self._shake_disparado:
            return
        self._proximo_grito -= dt
        if self._proximo_grito <= 0.0:
            self._proximo_grito = self._espera_entre_gritos()
            claro = self._intensidad_de_lluvia_fase4()
            volumen = (self.VOLUMEN_GRITO[0]
                       + claro * (self.VOLUMEN_GRITO[1] - self.VOLUMEN_GRITO[0]))
            self._play_sfx_spatial(
                fase.grito_aislado, self._posicion_del_grito(), volume=volumen)
            if fase.sombra_de_ave and self._sombra_progreso < 0.0:
                self._iniciar_cruce_de_sombra()

    # ── La quietud que revela (AUD-492) ─────────────────────────

    def _actualizar_quietud_del_gavilan(self, dt: float) -> None:
        """Detenerse en la Fase 4 hace que el Gavilán se deje ver.

        GAP-062 puntos 24-25 (*«detenerse también es jugar»*) y GAP-065
        §13, eslabón F4. Es la contrapartida exacta del comentario que
        `_actualizar_gradacion` dejó escrito como declaración de
        principios —*«el cambio se ve al caminar, no al esperar quieto»*—
        y que la crítica de diseño señaló como justamente lo contrario de
        lo que esta fase necesita: en las otras cinco el mundo se revela
        avanzando, y en la del bosque que observa se revela parándose.

        Qué hace, en concreto: adelanta el cruce de la sombra que ya
        existía. No inventa un evento nuevo ni enseña nada que el jugador
        no pudiera ver de todos modos — cambia **quién** decide cuándo
        ocurre, que era todo el problema del eslabón F4: los
        temporizadores corrían ciegos a lo que hacía el jugador.

        Sólo después del silencio, igual que el grito: antes de que algo
        haya pasado no hay nada a lo que el bosque pueda estar
        respondiendo.
        """
        fase = self.fase
        if not fase.sombra_de_ave or not self._shake_disparado:
            return
        if self._proxima_revelacion > 0.0:
            self._proxima_revelacion -= dt
            return
        if not self._atencion.esta_quieto(self.QUIETUD_QUE_REVELA):
            return
        self._proxima_revelacion = self.ESPERA_TRAS_REVELAR
        # Si ya hay una sombra cruzando, no se pisa con otra: la
        # recompensa por detenerse es que la próxima llegue ya, no que se
        # solapen dos.
        if self._sombra_progreso < 0.0:
            self._iniciar_cruce_de_sombra()
        self._atencion.reiniciar()

    # ── La sombra del Gavilán ────────────────────────────────────

    def _espera_entre_sombras(self) -> float:
        return random.uniform(*self.ESPERA_ENTRE_SOMBRAS)

    #: AUD-513, GAP-062 punto 10 — *«no debería aparecer como un sprite
    #: claramente identificable cada vez... queremos presencia, no
    #: exposición»*. Antes cada cruce era el mismo `_gavilan` reconocible, a
    #: la misma altura, siempre de izquierda a derecha. Las variantes:
    #: la silueta reconocible (menos de la mitad de las veces) y una forma
    #: difusa que no se lee como ningún pájaro en concreto —una mancha, no
    #: un retrato—, a alturas distintas y en las dos direcciones.
    ALTURAS_DE_CRUCE: tuple[int, int] = (60, 110)

    def _iniciar_cruce_de_sombra(self) -> None:
        self._sombra_progreso = 0.0
        self._sombra_es_identificable = random.random() < 0.4
        self._sombra_altura = random.randint(*self.ALTURAS_DE_CRUCE)
        self._sombra_izquierda_a_derecha = random.random() < 0.5

    def _actualizar_sombra_del_gavilan(self, dt: float) -> None:
        """Cruza el cielo de vez en cuando — la pieza visual que el primer
        intento dejó fuera (`GAP-058`): hasta ahora el Gavilán sólo se oía."""
        fase = self.fase
        if not fase.sombra_de_ave:
            self._sombra_progreso = -1.0
            return
        if self._sombra_progreso >= 0.0:
            self._sombra_progreso += dt / self.DURACION_DEL_CRUCE
            if self._sombra_progreso >= 1.0:
                self._sombra_progreso = -1.0
                self._proxima_sombra = self._espera_entre_sombras()
            return
        self._proxima_sombra -= dt
        if self._proxima_sombra <= 0.0:
            self._iniciar_cruce_de_sombra()

    # ── Las grietas de la Fase 6 ────────────────────────────────

    #: AUD-513, GAP-064 punto 6 — *«empiezan pocas y aumentan... el entorno
    #: completo parece estar conectado por ellas»*: con `GRIETAS_FASE6` ya
    #: colocadas en el TMX (`tools/generate_stage4_1.py`, que no se puede
    #: regenerar sin borrar el arte de `BG_Far`/`BG_Mid` ya pintado a mano —
    #: ver el comentario de `_actualizar_friccion_de_la_lluvia`, mismo
    #: motivo), añadir más luces exigiría tocar el mapa comprometido. Se
    #: consigue el mismo efecto sin luces nuevas: cuanto más avanza el
    #: jugador en la Fase 6, más lejos se encienden (`DISTANCIA_DE_GRIETA`
    #: crece) y más tardan en apagarse (`BAJADA_DE_GRIETA` crece) — las
    #: mismas grietas de siempre, pero más de ellas encendidas a la vez
    #: cerca del final, que es justo la lectura de «cada vez más conectado».
    DISTANCIA_DE_GRIETA_FINAL = 90.0
    BAJADA_DE_GRIETA_FINAL = 4.0

    def _actualizar_grietas(self, dt: float) -> None:
        """Se encienden por proximidad y se apagan solas: un rastro, no una
        barra de progreso acumulada (a diferencia de los braseros del diseño
        anterior)."""
        if self._player is None or not self._grietas:
            return
        avance = self._avance_en_fase(self.fase) if self.fase.numero == 6 else 0.0
        distancia = (self.DISTANCIA_DE_GRIETA
                     + avance * (self.DISTANCIA_DE_GRIETA_FINAL - self.DISTANCIA_DE_GRIETA))
        bajada = (self.BAJADA_DE_GRIETA
                  + avance * (self.BAJADA_DE_GRIETA_FINAL - self.BAJADA_DE_GRIETA))
        centro = pygame.Vector2(self._player.rect.center)
        for i, luz in enumerate(self._grietas):
            actual = self._intensidad_grieta.get(i, 0.0)
            if centro.distance_to(luz.position) <= distancia:
                actual = min(1.0, actual + dt / self.SUBIDA_DE_GRIETA)
            else:
                actual = max(0.0, actual - dt / bajada)
            self._intensidad_grieta[i] = actual
            luz.intensity = actual * self.INTENSIDAD_MAX_GRIETA

    #: AUD-551 — GAP-070 "Pisadas de Energía Verde": las tres notas de
    #: la tríada de Re menor, una por variante de la campanilla.
    NOTAS_DEL_PASO_DE_LUZ: tuple[str, ...] = (
        "sfx_environment_paso_de_luz_re",
        "sfx_environment_paso_de_luz_fa",
        "sfx_environment_paso_de_luz_la",
    )

    def _actualizar_pasos_de_luz(self) -> None:
        """Una campanilla de cristal cuando una grieta termina de
        encenderse del todo — GAP-070: *"cada vez que el pie... enciende
        una baldosa o grieta"*.

        No es literalmente "cada pisada": las grietas se encienden por
        proximidad continua (`_actualizar_grietas`), no por contacto
        discreto, así que lo más fiel a esa mecánica real es sonar
        cuando una grieta cruza a intensidad máxima — el instante en que
        termina de "encenderse" para quien la ve. Si se apaga del todo y
        el jugador vuelve a acercarse, puede volver a sonar.
        """
        if self.fase.numero != 6:
            return
        for i, intensidad in self._intensidad_grieta.items():
            if intensidad >= 1.0 and i not in self._grietas_con_campanilla:
                self._grietas_con_campanilla.add(i)
                self._play_sfx_named(random.choice(self.NOTAS_DEL_PASO_DE_LUZ),
                                     volume=0.5)
            elif intensidad < 1.0 and i in self._grietas_con_campanilla:
                self._grietas_con_campanilla.discard(i)

    # ── Las presencias errantes de fondo (AUD-562) ──────────────

    def _actualizar_presencias_errantes(self, dt: float) -> None:
        """Cuenta hacia la próxima aparición de cada presencia de
        `presencias.PRESENCIAS`, o hacia que se apague la que ya está
        visible — mismo mecanismo que `_actualizar_anomalia_fase1`, una
        vez por presencia en vez de una sola figura fija."""
        fase_actual = self.fase.numero
        for p in presencias.PRESENCIAS:
            if p.fase != fase_actual:
                continue
            visible = self._presencia_visible.get(p.id, 0.0)
            if visible > 0.0:
                self._presencia_visible[p.id] = max(0.0, visible - dt)
                continue
            proxima = self._presencia_proxima.get(p.id)
            if proxima is None:
                proxima = random.uniform(*p.espera)
            proxima -= dt
            if proxima <= 0.0:
                self._presencia_visible[p.id] = random.uniform(*p.duracion)
                proxima = random.uniform(*p.espera)
            self._presencia_proxima[p.id] = proxima

    def _dibujar_presencias_errantes(self, surface: pygame.Surface,
                                     offset: pygame.Vector2) -> None:
        """Patrulla de ida y vuelta alrededor de `columna_centro`, con la
        misma lectura de terreno que ya usa `_dibujar_huellas_del_venado`
        —`trazado.altura_del_suelo`— para que la Fase 3 (con loma de
        verdad) no deje a nadie flotando sobre el aire ni hundido bajo
        tierra."""
        fase_actual = self.fase.numero
        ts = settings.TILE_SIZE
        ruta_infestado = "sprites/enemies/enemy_walker_walk.png"
        for p in presencias.PRESENCIAS:
            if p.fase != fase_actual:
                continue
            if self._presencia_visible.get(p.id, 0.0) <= 0.0:
                continue
            avance = (self._tiempo % p.periodo_patrullaje) / p.periodo_patrullaje
            vaiven = math.sin(avance * math.tau)
            columna = p.columna_centro + vaiven * p.rango_columnas
            ancho = int(p.alto * 0.55)
            x = int(columna * ts - offset.x)
            if x < -ancho - 20 or x > settings.INTERNAL_WIDTH + 20:
                continue
            fila_suelo = trazado.altura_del_suelo(int(columna))
            y = int(fila_suelo * ts - p.alto) - int(offset.y)
            dibujado = False
            if p.tipo == "infestado":
                # AUD-562 — el sprite real de `WalkerEstudiante`: no es un
                # monstruo inventado, es otro infectado más, que encaja
                # con el lore de la infestación mejor que una silueta
                # genérica de "enemigo".
                dibujado = siluetas.dibujar_silueta_de_sprite(
                    surface, ruta_infestado, 20, 16, x, y, ancho, p.alto,
                    p.color, p.alfa,
                )
            if not dibujado:
                siluetas.dibujar_contorno(
                    surface, siluetas._fantasma, x, y, ancho, p.alto,
                    p.color, p.alfa,
                )

    # ── La secuencia de despertar antes del corte (Fase 6) ──────
    #
    # AUD-513, GAP-064 punto 25 — el diseño pide una secuencia completa
    # (vibración, shake, parpadeo de las grietas, la música se detiene,
    # silencio, un sonido profundo) antes del corte a
    # `stage4_2_boss_paburu`; hoy `_actualizar_mensaje_final` sólo
    # reescribe el texto del cartel y el `NextTrigger` está a un par de
    # baldosas, sin ningún aviso. Esto no bloquea la entrada del jugador
    # —el shake y el sonido grave, una sola vez, cerca del final del
    # tramo—; el mirador y la pausa contemplativa que sí necesitan
    # detener al jugador un instante los da un `Cutscene` aparte
    # (AUD-515, ver `_dibujar_...` no aplica aquí — el guión vive en el
    # TMX, columna cerca de `AVANCE_DEL_DESPERTAR`), no este método.
    AVANCE_DEL_DESPERTAR = 0.92
    DURACION_SHAKE_DESPERTAR = 0.6
    AMPLITUD_SHAKE_DESPERTAR = 8.0

    def _actualizar_secuencia_de_despertar(self) -> None:
        fase = self.fase
        if fase.numero != 6 or self._despertar_disparado:
            return
        if self._avance_en_fase(fase) < self.AVANCE_DEL_DESPERTAR:
            return
        self._despertar_disparado = True
        # AUD-493 detiene la música con `stop_music`; aquí se corta también
        # el ambiente, la otra mitad del *«la música se detiene»* del punto
        # 25 — el mismo `stop_ambient` sin fundido que usa el silencio
        # súbito de la Fase 4, porque el efecto que se busca es el mismo:
        # un corte, no un fundido.
        audio = self.audio
        if audio is not None and getattr(audio, "_ambient_active", False):
            audio.stop_ambient()
        self._camera.apply_shake(amplitude=self.AMPLITUD_SHAKE_DESPERTAR,
                                 duration=self.DURACION_SHAKE_DESPERTAR)
        # AUD-515 — antes tomaba prestado `sfx_bosses_phase_change`, un cue
        # de combate sin relación; ahora un retumbar propio con
        # reverberación horneada (`_aplicar_reverberacion`,
        # `tools/generate_all_assets.py`), la misma idea que el silencio de
        # la Fase 4: un espacio sagrado que resuena.
        self._play_sfx_named("sfx_environment_despertar_profundo", volume=0.7)

    def _actualizar_mensaje_final(self) -> None:
        """AUD-474 — el umbral cuenta cuántos espíritus se liberaron de
        verdad, no sólo que el jugador llegó hasta ahí.

        Se reescribe cada fotograma, no una sola vez: es barato (una
        comparación de texto y, como mucho, tres booleanos) y así no importa
        en qué orden corra frente al sistema que dispara el `MessageTrigger`
        — cuando el jugador por fin lo toque, el texto ya lleva rato al día.
        Busca el disparador por su texto **base** (`TEXTO_FINAL_BASE`) y no
        lo vuelve a tocar una vez que ya se disparó, para no cambiarle el
        mensaje a media lectura.
        """
        if self._stage_data is None:
            return
        liberados = sum(
            1 for fase in FASES
            if fase.espiritu is not None and self._espiritu_liberado(fase)
        )
        total = sum(1 for fase in FASES if fase.espiritu is not None)
        if liberados == total:
            texto = (f"{trazado.TEXTO_FINAL_BASE} Los tres espíritus "
                     f"descansan por fin.")
        elif liberados == 0:
            texto = (f"{trazado.TEXTO_FINAL_BASE} Ninguno de los espíritus "
                     f"encontró descanso.")
        else:
            texto = (f"{trazado.TEXTO_FINAL_BASE} Sólo {liberados} de "
                     f"{total} espíritus descansan.")
        for mt in self._stage_data.message_triggers:
            if mt.triggered:
                continue
            if mt.text == trazado.TEXTO_FINAL_BASE or mt.text.startswith(
                trazado.TEXTO_FINAL_BASE,
            ):
                mt.text = texto

    # ── Dibujo ────────────────────────────────────────────────

    def dibujar_fondo(self, surface: pygame.Surface,
                      offset: pygame.Vector2) -> None:
        """El espíritu de la fase y su decoración, detrás del mapa — igual
        que el diseño anterior pintaba sus siluetas: son recuerdos y
        escenario, no primer plano."""
        self._dibujar_horizonte(surface, offset)
        self._dibujar_luna_de_fase4(surface, offset)
        self._dibujar_espiritu(surface, offset)
        self._dibujar_presencias_errantes(surface, offset)
        self._dibujar_decoracion(surface, offset)
        self._dibujar_huellas_del_venado(surface, offset)
        self._dibujar_serpiente_de_fondo(surface, offset)
        self._dibujar_columna_de_huesos(surface, offset)
        self._dibujar_sombra_de_ave(surface, offset)
        self._dibujar_bruja(surface, offset)
        self._dibujar_anomalia_fase1(surface, offset)
        self._dibujar_figura_de_la_luna(surface, offset)
        self._dibujar_paburu(surface, offset)
        self._dibujar_despedida_de_los_espiritus(surface, offset)

    # ── Las huellas del Venado (Fase 2, AUD-513, GAP-060 punto 28) ─
    def _dibujar_huellas_del_venado(self, surface: pygame.Surface,
                                    offset: pygame.Vector2) -> None:
        """Marcas de pisada en el suelo, antes de que el Venado hable —
        *«herramienta de navegación... a veces desaparecen o terminan
        abruptamente»*. Elipses directas, sin lienzo aparte: son pequeñas y
        muchas, y crear una superficie por huella costaría más de lo que
        vale el detalle (ver AUD-514, la misma lección con el horizonte)."""
        fase = self.fase
        if fase.numero != 2:
            return
        avance = self._avance_en_fase(fase)
        if avance >= self.AVANCE_ANTES_DEL_DIALOGO:
            return  # ya habló: de aquí en adelante no queda nada que rastrear
        ts = settings.TILE_SIZE
        for i, columna_relativa in enumerate(trazado.HUELLAS_FASE2):
            columna = fase.desde_columna + columna_relativa
            x = int(columna * ts - offset.x)
            if x < -20 or x > settings.INTERNAL_WIDTH + 20:
                continue
            fila_suelo = trazado.altura_del_suelo(columna)
            y = int(fila_suelo * ts - 4) - int(offset.y)
            desplazado = 3 if i % 2 else -3  # dos patas, no una línea recta
            pygame.draw.ellipse(
                surface, siluetas.SILUETA_OSCURA,
                pygame.Rect(x + desplazado, y, 6, 4),
            )

    # ── El horizonte lejano: BG_Far (AUD-513, GAP-058/059/065) ───
    #
    # `color, base_y (fracción de pantalla), amplitud, frecuencia` por fase.
    # Frecuencias e intensidades distintas para que las seis crestas no se
    # lean como la misma silueta repintada: la Fase 3 (tormenta) es la más
    # alta y quebrada, la Fase 5 (planicie en calma) la más baja y suave.
    HORIZONTE_POR_FASE: dict[int, tuple[tuple[int, int, int], float, float, float]] = {
        1: ((40, 34, 46), 0.62, 26.0, 0.010),
        2: ((28, 34, 26), 0.58, 34.0, 0.014),
        3: ((22, 22, 30), 0.50, 54.0, 0.018),
        4: ((46, 32, 24), 0.60, 30.0, 0.012),
        5: ((24, 26, 40), 0.66, 20.0, 0.008),
        6: ((30, 40, 34), 0.60, 34.0, 0.011),
    }

    def _dibujar_horizonte(self, surface: pygame.Surface,
                           offset: pygame.Vector2) -> None:
        """La cresta lejana de esta fase — plano `BG_Far`, casi inmóvil."""
        color, base_frac, amplitud, frecuencia = self.HORIZONTE_POR_FASE[self.fase.numero]
        siluetas.dibujar_horizonte(
            surface, settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT,
            offset.x * 0.15, color, 200,
            settings.INTERNAL_HEIGHT * base_frac, amplitud, frecuencia,
        )

    # ── Las osamentas como arquitectura, versión visual (GAP-061) ─
    #
    # No es la plataforma navegable que pide el punto 4 del diseño —eso
    # exige geometría sólida nueva en el generador, fuera del alcance de
    # este lote— pero sí cierra la mitad visual: en vez de una calavera
    # suelta cada 12 columnas, una columna vertebral gigantesca se alza
    # sobre el paisaje cada tramo largo, la progresión «vértebra → columna
    # → estructura gigantesca» del punto 15, vista desde lejos.
    COLUMNAS_DE_HUESOS_FASE3: tuple[int, ...] = (320, 400, 430)

    #: AUD-513, GAP-061 — «el rayo sube el brillo, no revela nada» era el
    #: defecto exacto: `_actualizar_rayos` sólo escalaba `ambient_brightness`
    #: un instante. Las osamentas gigantes son casi invisibles en la
    #: penumbra normal de la tormenta (alfa 60) y saltan a plena visibilidad
    #: durante el relámpago — el rayo revela la arquitectura del paisaje en
    #: vez de sólo iluminar lo que ya se veía.
    ALFA_HUESOS_NORMAL = 60
    ALFA_HUESOS_CON_RAYO = 190

    def _dibujar_columna_de_huesos(self, surface: pygame.Surface,
                                   offset: pygame.Vector2) -> None:
        if self.fase.numero != 3:
            return
        ts = settings.TILE_SIZE
        fuerza_rayo = self._rayo / self.DURACION_DEL_RAYO if self._rayo > 0.0 else 0.0
        alfa = round(
            self.ALFA_HUESOS_NORMAL
            + (self.ALFA_HUESOS_CON_RAYO - self.ALFA_HUESOS_NORMAL) * fuerza_rayo)
        for columna in self.COLUMNAS_DE_HUESOS_FASE3:
            x = int(columna * ts - offset.x * 0.4)
            if x < -260 or x > settings.INTERNAL_WIDTH + 260:
                continue
            alto = 220
            y = settings.INTERNAL_HEIGHT - alto - 30
            siluetas.dibujar_contorno(
                surface, siluetas._vertebra_gigante, x, y,
                int(alto * 0.55), alto, siluetas.PIEDRA_FRIA, alfa,
            )

    # ── La silueta de Paburu (Fase 6, GAP-064 puntos 7-8, 22-23) ──
    #: A partir de qué avance en la Fase 6 empieza a insinuarse. No desde
    #: el primer paso: el guion pide que la escala *crezca*, y algo visible
    #: de entrada no tiene dónde crecer.
    AVANCE_PARA_PABURU = 0.35

    def _dibujar_paburu(self, surface: pygame.Surface,
                        offset: pygame.Vector2) -> None:
        fase = self.fase
        if fase.numero != 6:
            return
        avance = self._avance_en_fase(fase)
        if avance < self.AVANCE_PARA_PABURU:
            return
        # Crece con el avance, nunca revela el todo: el alto tope (0.55 del
        # ancho de pantalla) sigue dejando la figura cortada por los bordes
        # y por la niebla del clima de la fase, no un retrato completo.
        progreso = (avance - self.AVANCE_PARA_PABURU) / (1.0 - self.AVANCE_PARA_PABURU)
        ancho = int(settings.INTERNAL_WIDTH * (0.30 + 0.25 * progreso))
        alto = int(ancho * 0.72)
        x = int(settings.INTERNAL_WIDTH * 0.60 - offset.x * 0.10) - ancho // 2
        y = settings.INTERNAL_HEIGHT - alto - 10
        alfa = int(70 * min(1.0, progreso * 1.4))
        siluetas.dibujar_contorno(
            surface, siluetas._paburu, x, y, ancho, alto,
            siluetas.SILUETA_OSCURA, alfa, grosor=3,
        )

    # ── La despedida de los espíritus (Fase 6, GAP-064 puntos 15-16) ─
    #: A qué avance dentro de la Fase 6 se deja ver, un instante, cada
    #: espíritu que el jugador liberó de verdad — en el mismo orden en que
    #: se liberan (Venado, Rey Terciopelo, Gavilán), repartidos a lo largo
    #: del tramo para que no aparezcan los tres a la vez.
    AVANCES_DESPEDIDA: tuple[float, float, float] = (0.15, 0.45, 0.75)
    DURACION_DESPEDIDA = 0.12

    def _dibujar_despedida_de_los_espiritus(
        self, surface: pygame.Surface, offset: pygame.Vector2,
    ) -> None:
        """*"Venado en la distancia, Serpiente como energía, Halcón en el
        cielo... una vez cada uno, como despedida"* — sólo los que el
        jugador liberó de verdad (AUD-474): a quien no se liberó no le
        queda nada que despedirse."""
        fase = self.fase
        if fase.numero != 6:
            return
        avance = self._avance_en_fase(fase)
        for indice_espiritu, avance_despedida in enumerate(self.AVANCES_DESPEDIDA):
            if abs(avance - avance_despedida) > self.DURACION_DESPEDIDA:
                continue
            fase_del_espiritu = next(
                f for f in FASES if f.espiritu == indice_espiritu)
            if not self._espiritu_liberado(fase_del_espiritu):
                continue
            _nombre, forma = siluetas.ESPIRITUS[indice_espiritu]
            cercania = 1.0 - abs(avance - avance_despedida) / self.DURACION_DESPEDIDA
            x = int(settings.INTERNAL_WIDTH * (0.25 + 0.25 * indice_espiritu))
            y = 140
            alfa = int(130 * cercania)
            siluetas.dibujar_contorno(
                surface, forma, x, y, 90, 70, siluetas.VERDE_ESPECTRAL, alfa,
            )

    @staticmethod
    def _fundido_del_espiritu(avance: float, liberado: bool) -> float:
        """0 al entrar y al salir de la fase, 1 en medio.

        Entra en el primer 15 % del tramo. Si el jugador **liberó** al
        espíritu de verdad —AUD-474, pulsando el botón de usar junto a él,
        no sólo caminando cerca— se desvanece en el último 15 % igual que
        antes. Si no lo liberó, se queda a la vista hasta el borde mismo de
        la sección: no asciende nadie a quien nadie liberó. Es la diferencia
        entre observar y hacer que la crítica de diseño (2026-08-14) pedía.
        """
        entra = min(1.0, avance / 0.15)
        sale = min(1.0, (1.0 - avance) / 0.15) if liberado else 1.0
        return min(entra, sale)

    def _espiritu_liberado(self, fase: Fase) -> bool:
        """AUD-474 — ¿el jugador pulsó usar junto al espíritu de esta fase?

        `EventTrigger` con `automatico=False` (`tools/generate_stage4_1.py`)
        sólo se dispara si alguien pulsa el botón de usar estando cerca —
        caminar por encima no basta. `evento_de_liberacion` es la misma
        función que usa el generador para nombrar el evento, así que el
        nombre no puede desincronizarse entre los dos ficheros.
        """
        if self._stage_data is None or fase.espiritu is None:
            return False
        evento = trazado.evento_de_liberacion(fase.numero)
        return any(
            d.evento == evento and d.disparado
            for d in self._stage_data.disparadores
        )

    #: AUD-551 — GAP-070 "Diálogo del Venado/de la Serpiente/del
    #: Halcón": `Fase.espiritu` (0/1/2) a la línea de voz que le
    #: corresponde. AUD-551 hizo sonar por primera vez al Venado con
    #: `sfx_voz_venado_fase1` — ya existía (AUD-263) pero nadie lo
    #: reproducía nunca, el mismo patrón de "sistema completo, camino real
    #: inexistente" que ya cazaron `SwimmingState` y `WaterEffect` — como
    #: solución de paso, porque el Rey Terciopelo y el Gavilán no tenían
    #: voz en absoluto. AUD-554 le da al Venado su propia receta
    #: ("La Voz del Bosque": diente de sierra+seno 60Hz, vibrato de pitch
    #: a 12Hz, pasa-banda barriendo 150→400Hz, reverberación masiva — ver
    #: `_gen_sfx` en `tools/generate_all_assets.py`), la misma clase de
    #: recurso que ya tienen los otros dos.
    _VOZ_POR_ESPIRITU: dict[int, str] = {
        0: "sfx_voz_venado_ancestral",
        1: "sfx_voz_rey_terciopelo",
        2: "sfx_voz_gavilan",
    }

    def _actualizar_voz_del_espiritu(self) -> None:
        """Una línea de voz, una vez por espíritu y partida, en el mismo
        instante en que `_espiritu_liberado` pasa a `True` — el punto
        donde el guion ya dice que el espíritu habla."""
        fase = self.fase
        if fase.espiritu is None or fase.espiritu in self._espiritus_con_voz:
            return
        if not self._espiritu_liberado(fase):
            return
        self._espiritus_con_voz.add(fase.espiritu)
        linea = self._VOZ_POR_ESPIRITU.get(fase.espiritu)
        if linea is None:
            return
        audio = self.audio
        if audio is not None and hasattr(audio, "play_voz"):
            audio.play_voz(linea)

    def _dibujar_espiritu(self, surface: pygame.Surface,
                          offset: pygame.Vector2) -> None:
        fase = self.fase
        if fase.espiritu is None:
            return
        _nombre, forma = siluetas.ESPIRITUS[fase.espiritu]
        archivo, ancho_fotograma, alto_fotograma = siluetas.SPRITE_DE_ESPIRITU[fase.espiritu]
        avance = self._avance_en_fase(fase)
        liberado = self._espiritu_liberado(fase)
        # Antes del diálogo, el Venado (Fase 2, AUD-479) sólo se ve
        # durante sus destellos — `_venado_visible`, que lleva
        # `_actualizar_apariciones_previas_del_venado`—, no con el fundido
        # continuo normal. Pasado ese punto vuelve al mismo cálculo que ya
        # usan el Rey Terciopelo y el Gavilán.
        antes_del_dialogo = fase.apariciones_previas and avance < self.AVANCE_ANTES_DEL_DIALOGO
        if antes_del_dialogo:
            if self._venado_visible <= 0.0:
                return
            fundido = 1.0
        else:
            fundido = self._fundido_del_espiritu(avance, liberado)
        if fundido <= 0.0:
            return
        # Asciende de verdad en el último tramo —pero sólo si se liberó—:
        # sube por la pantalla en vez de sólo desvanecerse en el sitio.
        ascenso = max(0.0, (avance - 0.85) / 0.15) * 90.0 if liberado else 0.0
        vaiven = math.sin(self._tiempo * 0.35) * 6.0
        x = int(settings.INTERNAL_WIDTH * 0.62
                - offset.x * 0.12) % (settings.INTERNAL_WIDTH + 260) - 130
        alto = 120
        ancho = int(alto * 0.9)
        y = int(230 + vaiven - ascenso)
        alfa = int(150 * fundido)
        # AUD-561 — el arte real del jefe (ver `siluetas.SPRITE_DE_ESPIRITU`)
        # sustituye al contorno de polígono: jugado, «se veía raro», no se
        # leía como venado/serpiente/gavilán. El contorno se queda como red
        # de seguridad si el sprite no está.
        dibujado = siluetas.dibujar_silueta_de_sprite(
            surface, archivo, ancho_fotograma, alto_fotograma,
            x, y, ancho, alto, siluetas.VERDE_ESPECTRAL, alfa,
        )
        if not dibujado:
            siluetas.dibujar_contorno(
                surface, forma, x, y, ancho, alto,
                siluetas.VERDE_ESPECTRAL, alfa,
            )

    # ── La decoración propia por fase (AUD-465, AUD-467) ────────
    #
    # Posiciones en **columna de mundo** (no fracción de pantalla): con
    # secciones de 150 columnas —cuatro pantallas— una silueta anclada a la
    # pantalla se leería flotando junto a la cámara en vez de plantada en un
    # sitio. `trazado.py` es la fuente de verdad de dónde va cada una — el
    # mismo objeto del que lee el generador del mapa.

    #: AUD-513, GAP-062 punto 13 — qué árbol de `ARBOLES_FASE4` cae tras el
    #: silencio súbito. El último de la fila y no el primero: el jugador ya
    #: cruzó los anteriores antes de que el silencio ocurriera a mitad de
    #: tramo (`AVANCE_DEL_SILENCIO`), así que sólo el último queda por
    #: delante para poder verlo cambiado en vez de recordarlo cambiado.
    INDICE_ARBOL_QUE_CAE = -1

    def _dibujar_decoracion(self, surface: pygame.Surface,
                            offset: pygame.Vector2) -> None:
        fase = self.fase
        if fase.decoracion == "bosque_cortado":
            excepcion = None
            if self._shake_disparado:
                indice = self.INDICE_ARBOL_QUE_CAE % len(trazado.ARBOLES_FASE4)
                excepcion = (indice, siluetas._arbol_caido)
            self._dibujar_siluetas_de_fondo(
                surface, offset, siluetas._arbol_cortado,
                trazado.ARBOLES_FASE4, alto=88,
                color=siluetas.SILUETA_OSCURA, alfa=140, paralaje=0.85,
                forma_excepcion=excepcion,
            )
        elif fase.decoracion == "tumbas_conquistador":
            # AUD-513, GAP-063 punto 21 — landmarks distintos entre sí, no
            # la misma cruz cada 30 columnas: cicla entre las tres formas
            # de `LANDMARKS_DE_LA_PLANICIE`.
            self._dibujar_siluetas_de_fondo(
                surface, offset, siluetas._cruz_conquistador,
                trazado.TUMBAS_FASE5, alto=46,
                color=siluetas.PIEDRA_FRIA, alfa=110, paralaje=0.85,
                formas_por_indice=siluetas.LANDMARKS_DE_LA_PLANICIE,
            )
        elif fase.decoracion == "lapidas_personales":
            self._dibujar_fantasma_personal(surface, offset)

    def _dibujar_siluetas_de_fondo(
        self, surface: pygame.Surface, offset: pygame.Vector2, forma: object,
        columnas: tuple[int, ...], alto: int, color: tuple[int, int, int],
        alfa: int, paralaje: float,
        forma_excepcion: tuple[int, object] | None = None,
        formas_por_indice: tuple[object, ...] | None = None,
    ) -> None:
        """El dibujo genérico que comparten el bosque cortado y las tumbas:
        una silueta por columna de mundo, con un parallax casi 1:1 —están
        junto al camino, no en un horizonte lejano— para que se vean
        plantadas en su sitio al pasar por delante, no flotando con la
        cámara.

        `formas_por_indice` cicla una silueta distinta por columna (AUD-513,
        GAP-063 punto 21: landmarks variados); `forma_excepcion` sustituye
        una sola columna concreta (AUD-513, GAP-062 punto 13: el árbol que
        cae). Los dos existen porque piden cosas distintas —una progresión
        fija por posición contra un cambio puntual de estado— y forzarlos al
        mismo mecanismo confundiría las dos razones de ser distinto.
        """
        ts = settings.TILE_SIZE
        ancho_pantalla = settings.INTERNAL_WIDTH
        for indice, columna in enumerate(columnas):
            x = int(columna * ts - offset.x * paralaje)
            if x < -200 or x > ancho_pantalla + 200:
                continue
            forma_de_esta = forma
            if formas_por_indice:
                forma_de_esta = formas_por_indice[indice % len(formas_por_indice)]
            if forma_excepcion is not None and forma_excepcion[0] == indice:
                forma_de_esta = forma_excepcion[1]
            siluetas.dibujar_contorno(
                surface, forma_de_esta, x, settings.INTERNAL_HEIGHT - alto - 40,
                int(alto * 0.75), alto, color, alfa,
            )

    #: AUD-513, GAP-059 punto 10 — cuánto más intenso se ve el fantasma la
    #: segunda vez, si el jugador volvió tras avanzar bastante. No
    #: desaparece del todo ni se dobla: lo bastante para notarse sin
    #: convertirse en un fantasma distinto.
    ALFA_EXTRA_AL_REGRESAR = 40

    def _dibujar_fantasma_personal(self, surface: pygame.Surface,
                                   offset: pygame.Vector2) -> None:
        """El easter egg de la Fase 1 (§7 del diseño): un fantasma sobrio
        rondando la tumba de Teresa Murillo, junto a la de Hugo Salazar
        Castillo. Distinto de los tres espíritus de jefe —color propio,
        sin ascender, sin fundido de entrada— porque no es uno de ellos:
        es un recuerdo de familia.

        AUD-513 — la memoria espacial (GAP-059 punto 10, *«estoy seguro de
        que antes estaba diferente»*): si el jugador avanzó bastante y
        volvió, `_regreso_a_la_tumba` sube el suelo del vaivén de alfa en
        vez de dejarlo apagarse tan bajo como la primera vez. No es un
        fantasma nuevo ni un texto nuevo — es el mismo, un poco más
        presente, y eso es lo único que hace falta para la duda.
        """
        ts = settings.TILE_SIZE
        col = trazado.COLUMNA_LAPIDA_TERESA
        x = int(col * ts - offset.x)
        if x < -100 or x > settings.INTERNAL_WIDTH + 100:
            return
        fila_suelo = trazado.altura_del_suelo(col)
        alto = 40
        vaiven = math.sin(self._tiempo * 0.5) * 4.0
        y = int(fila_suelo * ts - alto - 20 + vaiven) - int(offset.y)
        piso = 90 + (self.ALFA_EXTRA_AL_REGRESAR if self._regreso_a_la_tumba else 0)
        alfa = piso + int(30 * math.sin(self._tiempo * 0.8))
        siluetas.dibujar_contorno(
            surface, siluetas._fantasma, x, y, int(alto * 0.7), alto,
            siluetas.BLANCO_RECUERDO, alfa,
        )

    # ── La serpiente de fondo (Fase 3) ──────────────────────────

    def _dibujar_serpiente_de_fondo(self, surface: pygame.Surface,
                                    offset: pygame.Vector2) -> None:
        """Una presencia aparte de la que asciende: el guion pide
        *«movimientos de serpientes... en el fondo»*, no sólo el espíritu
        que testifica. Más pequeña, más tenue, repta despacio."""
        fase = self.fase
        if not fase.serpiente_de_fondo:
            return
        x = int(settings.INTERNAL_WIDTH * 0.30
                - offset.x * 0.15) % (settings.INTERNAL_WIDTH + 200) - 100
        vaiven = math.sin(self._tiempo * 0.6) * 10.0
        y = int(420 + vaiven)
        siluetas.dibujar_contorno(
            surface, siluetas._serpiente, x, y, 46, 30,
            siluetas.VERDE_ESPECTRAL, 70,
        )

    # ── La sombra del Gavilán, dibujo (Fase 4) ──────────────────

    def _dibujar_luna_de_fase4(self, surface: pygame.Surface,
                              offset: pygame.Vector2) -> None:
        """Una luna nueva en el cielo de la Fase 4 (AUD-563) — el nivel ya
        va de atardecer a noche cerrada (`13_STAGE_4_1.md` §2, "Empieza al
        atardecer, termina de noche"), así que una luna pálida en el
        bosque cortado no desentona, y le da a `_actualizar_grito_del_
        gavilan` algo real contra lo que sincronizar la sombra: *«que
        aparezca el Gavilán por la luna cuando suena»*. Se queda fija toda
        la fase, no intermitente como el ciclo de la Fase 5 — esa
        intermitencia significa algo distinto allá (la luz que se pierde);
        aquí sólo hace falta que esté."""
        if self.fase.numero != 4:
            return
        x, y = self.POSICION_LUNA_FASE4
        lienzo = pygame.Surface(
            (self.RADIO_LUNA_FASE4 * 2 + 2, self.RADIO_LUNA_FASE4 * 2 + 2),
            pygame.SRCALPHA,
        )
        centro = (self.RADIO_LUNA_FASE4 + 1, self.RADIO_LUNA_FASE4 + 1)
        pygame.draw.circle(
            lienzo, (*self.COLOR_LUNA_FASE4, self.ALFA_LUNA_FASE4),
            centro, self.RADIO_LUNA_FASE4,
        )
        surface.blit(lienzo, (x - centro[0], y - centro[1]))

    def _dibujar_sombra_de_ave(self, surface: pygame.Surface,
                               offset: pygame.Vector2) -> None:
        if self._sombra_progreso < 0.0:
            return
        margen = 150
        recorrido = settings.INTERNAL_WIDTH + margen * 2
        avance = self._sombra_progreso if self._sombra_izquierda_a_derecha \
            else 1.0 - self._sombra_progreso
        x = int(-margen + avance * recorrido)
        y = self._sombra_altura
        # Se desvanece en los dos extremos del cruce: aparecer y
        # desaparecer de golpe en el borde de la pantalla se lee como un
        # error de dibujo, no como un ave que llega de lejos.
        alfa = int(150 * math.sin(self._sombra_progreso * math.pi))
        if alfa <= 0:
            return
        forma = siluetas._gavilan if self._sombra_es_identificable else siluetas._sombra_difusa
        siluetas.dibujar_contorno(
            surface, forma, x, y, 70, 30,
            siluetas.SILUETA_OSCURA, alfa,
        )

    # ── La Bruja: percepción falsa (Fase 3, AUD-475) ────────────

    def _dibujar_bruja(self, surface: pygame.Surface,
                       offset: pygame.Vector2) -> None:
        """Se queda «en la rama de un árbol» un instante, sólo en dos de los
        relámpagos de la Fase 3 — sin sonido, sin diálogo, sin tocar ningún
        estado del nivel. Es a propósito indistinguible de un efecto de luz:
        quien la vea no tiene manera de confirmar que era algo."""
        if self._rayo <= 0.0 or not self._bruja_este_rayo:
            return
        x = int(settings.INTERNAL_WIDTH * 0.72)
        y = 70
        alfa = int(120 * (self._rayo / self.DURACION_DEL_RAYO))
        # Silueta oscura, no el blanco frío de la Cegua: a contraluz de un
        # relámpago se recorta en negro, y son dos presencias distintas —
        # confundirlas visualmente sería tan malo como caricaturizarlas.
        siluetas.dibujar_contorno(
            surface, siluetas._bruja, x, y, 40, 46,
            siluetas.SILUETA_OSCURA, alfa,
        )

    # ── La anomalía ambigua de la Fase 1, dibujo (AUD-478) ──────

    def _dibujar_anomalia_fase1(self, surface: pygame.Surface,
                                offset: pygame.Vector2) -> None:
        """La figura entre las tumbas, visible sólo mientras
        `_anomalia_fase1` cuenta hacia cero — nunca más de
        `DURACION_ANOMALIA_FASE1` segundos. El alfa cae con el tiempo que
        queda, así que ni siquiera aparece de golpe: se desvanece desde
        que se enciende, para que quien mire un instante tarde ya la vea
        más débil que quien miraba de frente."""
        if self._anomalia_fase1 <= 0.0:
            return
        ts = settings.TILE_SIZE
        col = trazado.COLUMNA_ANOMALIA_FASE1
        x = int(col * ts - offset.x)
        if x < -100 or x > settings.INTERNAL_WIDTH + 100:
            return
        fila_suelo = trazado.altura_del_suelo(col)
        alto = 44
        y = int(fila_suelo * ts - alto - 10) - int(offset.y)
        alfa = int(90 * (self._anomalia_fase1 / self.DURACION_ANOMALIA_FASE1))
        siluetas.dibujar_contorno(
            surface, siluetas._figura_lejana, x, y, int(alto * 0.6), alto,
            siluetas.SILUETA_OSCURA, alfa,
        )

    # ── La figura junto a la tumba, sólo con la luna oculta ─────
    #
    # AUD-513, GAP-063 punto 7 — *«cuando la luna está oculta pueden
    # ocurrir cosas: una figura aparece»*: antes nada en la Fase 5 leía
    # `luna_oculta` salvo el canto ancestral (AUD-488). Junto a una de las
    # cruces —no en medio del camino— para que se lea «algo cerca de la
    # tumba», no «algo en tu camino».
    UMBRAL_LUNA_OCULTA = 0.75

    def _dibujar_figura_de_la_luna(self, surface: pygame.Surface,
                                   offset: pygame.Vector2) -> None:
        fase = self.fase
        if not fase.luna_intermitente or self.luna_oculta < self.UMBRAL_LUNA_OCULTA:
            return
        ts = settings.TILE_SIZE
        col = trazado.TUMBAS_FASE5[len(trazado.TUMBAS_FASE5) // 2] + 3
        x = int(col * ts - offset.x)
        if x < -100 or x > settings.INTERNAL_WIDTH + 100:
            return
        fila_suelo = trazado.altura_del_suelo(col)
        alto = 40
        y = int(fila_suelo * ts - alto) - int(offset.y)
        # Se desvanece cerca del umbral en vez de encenderse de golpe: la
        # misma razón por la que `_dibujar_anomalia_fase1` no salta a
        # alfa máximo — que aparezca y desaparezca en seco se lee como un
        # error de dibujo, no como una presencia.
        margen = 1.0 - self.UMBRAL_LUNA_OCULTA
        progreso = min(1.0, (self.luna_oculta - self.UMBRAL_LUNA_OCULTA) / margen) if margen > 0 else 1.0
        alfa = int(100 * progreso)
        siluetas.dibujar_contorno(
            surface, siluetas._figura_lejana, x, y, int(alto * 0.6), alto,
            siluetas.BLANCO_CEGUA, alfa,
        )
