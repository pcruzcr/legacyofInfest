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
from src.framework.scenes.stage_scene import StageScene
from src.stages.stage4_1 import siluetas, trazado
from src.stages.stage4_1.fases import FASES, Fase, Gradacion, fase_en

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
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
    #: Cada cuánto cruza la sombra del Gavilán el cielo, y cuánto tarda en
    #: cruzar. La pieza que el primer intento (AUD-462…466) dejó fuera —
    #: hasta ahora la presencia del Gavilán era sólo sonora.
    ESPERA_ENTRE_SOMBRAS: tuple[float, float] = (6.0, 14.0)
    DURACION_DEL_CRUCE = 3.5

    # ── La Bruja: percepción falsa de la Fase 3 (AUD-475) ──────
    #: En qué relámpagos —contados desde que se entra a la Fase 3— aparece,
    #: una fracción de segundo, «en la rama de un árbol». Dos, no más: la
    #: crítica de diseño pide sembrar duda, no un patrón nuevo que aprender
    #: («si veo la bruja, no pasa nada» sería tan previsible como al revés).
    #: No hay sonido, no hay diálogo, no cambia nada del estado del nivel —
    #: es exactamente lo que la vuelve una percepción falsa y no un evento.
    RAYOS_CON_BRUJA: frozenset[int] = frozenset({2, 4})

    # ── El ciclo de luna (Fase 5) ──────────────────────────────
    PERIODO_DE_LA_LUNA = 6.0
    AMBIENTE_MIN_LUNA = 0.06
    AMBIENTE_MAX_LUNA = 0.48

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
        #: Las luces de las grietas de la Fase 6 — apagadas de fábrica en el
        #: TMX, encendidas por proximidad y no permanentes.
        self._grietas: list[LightSource] = []
        self._intensidad_grieta: dict[int, float] = {}

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

    # ── Actualización ─────────────────────────────────────────

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._player is None or self._stage_data is None:
            return
        self._tiempo += dt
        self._actualizar_fase()
        self._actualizar_gradacion()
        self._actualizar_ambiente_de_fase()
        self._actualizar_rayos(dt)
        self._actualizar_silencio_y_shake()
        self._actualizar_grito_del_gavilan(dt)
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
        if fase.numero == 3:
            self._rayos_en_fase3 = 0
            self._bruja_este_rayo = False
        if fase.numero == 4:
            self._shake_disparado = False
            self._proximo_grito = self._espera_entre_gritos()
            self._sombra_progreso = -1.0
            self._proxima_sombra = self._espera_entre_sombras()
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

    def _actualizar_grito_del_gavilan(self, dt: float) -> None:
        """Tras el silencio, el Gavilán se deja oír de vez en cuando.

        Sin bucle y sin patrón: el guion (§4) pide *«sonidos que pueden
        reaparecer de forma aislada y aleatoria»*, no un segundo ambiente. Se
        activa sólo después de `_shake_disparado` — antes del silencio no
        hay nada que «reaparecer».
        """
        fase = self.fase
        if fase.grito_aislado is None or not self._shake_disparado:
            return
        self._proximo_grito -= dt
        if self._proximo_grito <= 0.0:
            self._proximo_grito = self._espera_entre_gritos()
            self._play_sfx_named(fase.grito_aislado, volume=0.6)

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
