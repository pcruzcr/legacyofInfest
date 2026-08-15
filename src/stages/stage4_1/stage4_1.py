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
from src.stages.stage4_1 import siluetas, trazado
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

    # ── La música por fase (AUD-493) ────────────────────────────
    #: Cuánto tarda en entrar `MUSICA_DEL_DESPERTAR` en la Fase 6. Largo a
    #: propósito: llega después de cinco fases sin música, y el guion la
    #: quiere naciendo del mundo, no arrancando de golpe.
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
        self._shake_disparado: bool = False
        #: Cuándo suena el próximo grito aislado del Gavilán (Fase 4, sólo
        #: tras el silencio — ver `_actualizar_grito_del_gavilan`).
        self._proximo_grito: float = 0.0
        #: Cuándo cruza la próxima sombra del Gavilán, y en qué punto de su
        #: cruce va (-1 = no está cruzando ahora mismo).
        self._proxima_sombra: float = 0.0
        self._sombra_progreso: float = -1.0
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
        """Anota qué música dejó puesta el motor, para poder quitarla.

        AUD-493 — `StageScene` ya arrancó `bgm_track` del TMX unas líneas
        antes de llamar aquí. La tabla de fases es la que decide cuándo
        suena (`fases.MUSICA_DEL_DESPERTAR`), y la Fase 1 pide silencio,
        así que el primer `update` la va a parar. Para pararla hay que
        saber que está.
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
        self._actualizar_apariciones_previas_del_venado(dt)
        self._actualizar_pausa_de_la_serpiente()
        self._actualizar_rayos(dt)
        self._actualizar_silencio_y_shake()
        self._actualizar_grito_del_gavilan(dt)
        self._actualizar_quietud_del_gavilan(dt)
        self._actualizar_sombra_del_gavilan(dt)
        self._actualizar_grietas(dt)
        self._actualizar_mensaje_final()

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
        """Pone —o quita— la música que pide esta fase (AUD-493).

        GAP-059 punto 5, GAP-064 puntos 13-14 y GAP-065 §12 describen el
        mismo defecto desde tres sitios: una sola pista para las seis
        fases. Aquí la fase manda, y cinco de las seis piden silencio, de
        modo que la aproximación a Paburu deja de sonar desde el primer
        paso del cementerio y pasa a **entrar** en la última sección.

        Sólo actúa cuando la pista pedida cambia. Llamar a `play_music`
        cada vez que se cruza una frontera reiniciaría el tema desde el
        principio aunque fuera el mismo, que es el defecto que
        `_actualizar_fase` ya evita para el clima y las partículas.

        El fundido de entrada no es decorativo: `MUSICA_DEL_DESPERTAR`
        aparece tras cinco fases de silencio, y sin fundido el corte se
        oiría como un fallo de reproducción, no como que algo despierta.
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

    # ── La pausa antes del diálogo de la Serpiente (Fase 3, AUD-480) ─

    def _actualizar_pausa_de_la_serpiente(self) -> None:
        """Un respiro alrededor del diálogo del Rey Terciopelo (GAP-061,
        punto 19): *«el jugador alcanza un descanso. El viento se
        detiene... la Serpiente habla. Después: el viento vuelve.»*

        No es el silencio total de la Fase 4 —eso apaga el clima entero y
        dispara un shake una sola vez—; aquí sólo baja la fuerza de la
        `ZonaDeViento` real del mapa a una fracción, y sube de vuelta en
        cuanto el jugador se aleja del punto del diálogo, tantas veces
        como haga falta (a diferencia del shake, esto no es «una vez por
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
        if en_pausa and not self._viento_reducido:
            self._viento_zona.fuerza = self._viento_fuerza_original * self.FRACCION_VIENTO_EN_PAUSA
            self._viento_reducido = True
        elif not en_pausa and self._viento_reducido:
            self._viento_zona.fuerza = self._viento_fuerza_original
            self._viento_reducido = False

    # ── El relámpago de la Fase 3 ──────────────────────────────

    def _espera_entre_rayos(self) -> float:
        por_minuto = self.fase.rayos_por_minuto
        if por_minuto <= 0.0:
            return math.inf
        return random.uniform(0.5, 1.5) * (60.0 / por_minuto)

    def _actualizar_rayos(self, dt: float) -> None:
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
        """
        fase = self.fase
        if fase.grito_aislado is None or not self._shake_disparado:
            return
        self._proximo_grito -= dt
        if self._proximo_grito <= 0.0:
            self._proximo_grito = self._espera_entre_gritos()
            self._play_sfx_spatial(fase.grito_aislado, self._posicion_del_grito(), volume=0.6)

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
            self._sombra_progreso = 0.0
        self._atencion.reiniciar()

    # ── La sombra del Gavilán ────────────────────────────────────

    def _espera_entre_sombras(self) -> float:
        return random.uniform(*self.ESPERA_ENTRE_SOMBRAS)

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
            self._sombra_progreso = 0.0

    # ── Las grietas de la Fase 6 ────────────────────────────────

    def _actualizar_grietas(self, dt: float) -> None:
        """Se encienden por proximidad y se apagan solas: un rastro, no una
        barra de progreso acumulada (a diferencia de los braseros del diseño
        anterior)."""
        if self._player is None or not self._grietas:
            return
        centro = pygame.Vector2(self._player.rect.center)
        for i, luz in enumerate(self._grietas):
            actual = self._intensidad_grieta.get(i, 0.0)
            if centro.distance_to(luz.position) <= self.DISTANCIA_DE_GRIETA:
                actual = min(1.0, actual + dt / self.SUBIDA_DE_GRIETA)
            else:
                actual = max(0.0, actual - dt / self.BAJADA_DE_GRIETA)
            self._intensidad_grieta[i] = actual
            luz.intensity = actual * self.INTENSIDAD_MAX_GRIETA

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
        self._dibujar_espiritu(surface, offset)
        self._dibujar_decoracion(surface, offset)
        self._dibujar_serpiente_de_fondo(surface, offset)
        self._dibujar_sombra_de_ave(surface, offset)
        self._dibujar_bruja(surface, offset)
        self._dibujar_anomalia_fase1(surface, offset)

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

    def _dibujar_espiritu(self, surface: pygame.Surface,
                          offset: pygame.Vector2) -> None:
        fase = self.fase
        if fase.espiritu is None:
            return
        _nombre, forma = siluetas.ESPIRITUS[fase.espiritu]
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
        y = int(230 + vaiven - ascenso)
        alfa = int(150 * fundido)
        siluetas.dibujar_contorno(
            surface, forma, x, y, int(alto * 0.9), alto,
            siluetas.VERDE_ESPECTRAL, alfa,
        )

    # ── La decoración propia por fase (AUD-465, AUD-467) ────────
    #
    # Posiciones en **columna de mundo** (no fracción de pantalla): con
    # secciones de 150 columnas —cuatro pantallas— una silueta anclada a la
    # pantalla se leería flotando junto a la cámara en vez de plantada en un
    # sitio. `trazado.py` es la fuente de verdad de dónde va cada una — el
    # mismo objeto del que lee el generador del mapa.

    def _dibujar_decoracion(self, surface: pygame.Surface,
                            offset: pygame.Vector2) -> None:
        fase = self.fase
        if fase.decoracion == "bosque_cortado":
            self._dibujar_siluetas_de_fondo(
                surface, offset, siluetas._arbol_cortado,
                trazado.ARBOLES_FASE4, alto=88,
                color=siluetas.SILUETA_OSCURA, alfa=140, paralaje=0.85,
            )
        elif fase.decoracion == "tumbas_conquistador":
            self._dibujar_siluetas_de_fondo(
                surface, offset, siluetas._cruz_conquistador,
                trazado.TUMBAS_FASE5, alto=46,
                color=siluetas.PIEDRA_FRIA, alfa=110, paralaje=0.85,
            )
        elif fase.decoracion == "lapidas_personales":
            self._dibujar_fantasma_personal(surface, offset)

    def _dibujar_siluetas_de_fondo(
        self, surface: pygame.Surface, offset: pygame.Vector2, forma: object,
        columnas: tuple[int, ...], alto: int, color: tuple[int, int, int],
        alfa: int, paralaje: float,
    ) -> None:
        """El dibujo genérico que comparten el bosque cortado y las tumbas:
        una silueta por columna de mundo, con un parallax casi 1:1 —están
        junto al camino, no en un horizonte lejano— para que se vean
        plantadas en su sitio al pasar por delante, no flotando con la
        cámara."""
        ts = settings.TILE_SIZE
        ancho_pantalla = settings.INTERNAL_WIDTH
        for columna in columnas:
            x = int(columna * ts - offset.x * paralaje)
            if x < -200 or x > ancho_pantalla + 200:
                continue
            siluetas.dibujar_contorno(
                surface, forma, x, settings.INTERNAL_HEIGHT - alto - 40,
                int(alto * 0.75), alto, color, alfa,
            )

    def _dibujar_fantasma_personal(self, surface: pygame.Surface,
                                   offset: pygame.Vector2) -> None:
        """El easter egg de la Fase 1 (§7 del diseño): un fantasma sobrio
        rondando la tumba de Teresa Murillo, junto a la de Hugo Salazar
        Castillo. Distinto de los tres espíritus de jefe —color propio,
        sin ascender, sin fundido de entrada— porque no es uno de ellos:
        es un recuerdo de familia."""
        ts = settings.TILE_SIZE
        col = trazado.COLUMNA_LAPIDA_TERESA
        x = int(col * ts - offset.x)
        if x < -100 or x > settings.INTERNAL_WIDTH + 100:
            return
        fila_suelo = trazado.altura_del_suelo(col)
        alto = 40
        vaiven = math.sin(self._tiempo * 0.5) * 4.0
        y = int(fila_suelo * ts - alto - 20 + vaiven) - int(offset.y)
        alfa = 90 + int(30 * math.sin(self._tiempo * 0.8))
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

    def _dibujar_sombra_de_ave(self, surface: pygame.Surface,
                               offset: pygame.Vector2) -> None:
        if self._sombra_progreso < 0.0:
            return
        margen = 150
        recorrido = settings.INTERNAL_WIDTH + margen * 2
        x = int(-margen + self._sombra_progreso * recorrido)
        y = 80
        # Se desvanece en los dos extremos del cruce: aparecer y
        # desaparecer de golpe en el borde de la pantalla se lee como un
        # error de dibujo, no como un ave que llega de lejos.
        alfa = int(150 * math.sin(self._sombra_progreso * math.pi))
        if alfa <= 0:
            return
        siluetas.dibujar_contorno(
            surface, siluetas._gavilan, x, y, 70, 30,
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
