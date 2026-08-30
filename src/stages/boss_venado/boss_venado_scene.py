"""Módulo: boss_venado_scene
Sistema: stages.boss_venado — escena del estudiante para la arena del Venado (Práctica I)
Unidad Académica: IV — representación de escena y política de cámara
Descripción: El CameraLock del motor es un interruptor GLOBAL (camera.py:63-67 usa
    any() sobre toda la lista de locks e ignora el rect de cada lock). Esta escena
    compensa esto únicamente desde la zona editable: fuera de la arena la lista de
    locks se vacía para que la cámara siga al jugador; adentro (x >= 2480) se
    restauran los locks del TMX para que la cámara quede fija en la pelea del gazebo.

    Compensación (RETIRADA) del bug de motor H-10: introducida en el rewrite
    de fase 2 (2026-07-29), retirada aquí el 2026-08-26 por redundante — se
    deja la historia completa para quien audite el rastro (mismo criterio que
    la sección H-02 más abajo). StageScene.update() (stage_scene.py:605-610)
    escribe el offset de cámara del cuadro directamente en
    ``stage.map_layer._map_layer.view_rect`` — un campo pygame.Rect común que
    la ruta de blit real de pyscroll, ``BufferedRenderer._render_map()``, nunca
    lee (esta lee ``_x_offset``/``_y_offset``/``_tile_view``/``_buffer``,
    que solo cambian dentro de ``center()``). Entonces camera.offset avanza
    correctamente y cada entidad (cada una se dibuja a sí misma vía
    ``draw(surface, camera_offset)``) se mueve correctamente en relación con él, pero el
    FONDO de tiles de pyscroll podía quedar pegado a donde ``_initialize_buffers()``
    lo dejó al momento de cargar. Por eso esta escena llamaba, cada cuadro
    después de que ``super().update(dt)`` terminara el offset de cámara de
    ese cuadro, a la API pública real de pyscroll,
    ``stage.map_layer.center(...)`` (PyscrollGroup — ver stage_loader.py:138
    — reenvía al BufferedRenderer subyacente), vía el método
    ``_sync_map_render()`` (ya retirado, ver el historial de este archivo).
    Este mismo patrón de arreglo se probó primero en esta misma zona editable
    en tools/capture_map.py y tools/play_map.py (ver los docstrings de sus
    módulos, "COMPENSACION SOLO-DE-CAPTURA 2" / "COMPENSACION DE PREVIEW B")
    — esos dos visores independientes SÍ conservan su copia: no dependen de
    que ``BossVenadoScene.update()`` la dispare, cada uno la llama por su
    cuenta desde su propio bucle de conducción manual (fuera del alcance de
    este retiro, que fue solo de la escena; ver la nota abierta en el
    docstring de tools/capture_map.py sobre si esa copia también quedó
    redundante frente a AUD-039).

    Motivo del retiro: el motor centra el fondo por su cuenta, todos los
    cuadros, en tiempo de DIBUJO — ``DrawingSystem._draw_stage_layers``
    (drawing_system.py:573-579, AUD-039) calcula el mismo centro
    (``camera.offset + tamaño_de_superficie/2``) y llama a
    ``map_layer.center(...)`` justo antes de ``map_layer.draw(surface)``,
    en cada cuadro, para TODA ``StageScene`` — así que la llamada de esta
    escena en ``update()`` quedaba siempre sobrescrita por la del motor antes
    de que el cuadro llegara a pantalla; la compensación no aportaba nada
    desde que ese camino de dibujo existe, solo que nadie lo había medido
    hasta ahora. Evidencia: sonda A/B del 2026-08-25 (820 llamadas a
    ``_sync_map_render()`` suprimidas en una corrida completa del corredor,
    con la métrica del candado observable prácticamente idéntica con y sin
    la compensación: 7.346 vs 7.337, ambas muy por encima del umbral). El
    candado que prueba el observable en el arnés,
    ``playtest/tests/test_harness.py::test_corridor_background_scrolls_with_camera``
    (H-31: umbral recalibrado 8.0 → 4.0 el 2026-08-25 tras confirmar por
    mutación que mide la señal correcta), se diseñó explícitamente para
    sobrevivir este retiro — su propio docstring lo dice — y sigue en verde
    sin este método (ver V2 del reporte de esta tarea). Ver
    docs/superpowers/REGISTRO-DE-BUGS.md y reports/FINDINGS.md H-10/H-31
    para el rastro forense íntegro.

    Halo del jugador: hallazgo de playtest del usuario (2026-07-28) -- el sprite
    encapuchado del jugador (casi negro, RGB~15,20,35) se camufla contra el follaje
    oscuro de la paleta crepuscular, por lo que el héroe era difícil de ver en pantalla.
    Arreglo: un halo aditivo de luz de luna en espacio de pantalla dibujado alrededor
    del jugador cada cuadro (temático -- luz de luna, no un contorno genérico) vía
    pygame.BLEND_RGBA_ADD (hasta el fix de H-28/B-032 era BLEND_RGB_ADD -- ver el
    docstring de ``dibujar_ui``/``_build_player_halo`` más abajo para el porqué del
    canal alfa). El blending aditivo solo aclara los píxeles
    debajo de él, nunca oculta, así que no rompe el orden de dibujo tipo
    "painter's order" ya establecido en otras partes de este código base (el
    docstring explícito de orden de pintor de boss_venado.py) -- es un paso de
    iluminación, no otro sprite más en la pila.

    Refuerzo del halo por histograma (Tarea 12 del plan de peregrinación, fix del
    coordinador -- Unidad VII): el brillo del halo YA NO es fijo. Se multiplica por
    ``luciernagas_venado.GestorDeLuciernagas.factor_de_halo`` (∈ [1.0, 1.35],
    derivado de la MISMA lectura de intensidad de luminancia que decide cuántas
    luciérnagas se encienden) -- con la franja visible más oscura, el pico efectivo
    del halo sube hasta un 35% por encima del histórico, reforzando de verdad la
    legibilidad del héroe justo cuando más lo necesita. Con la franja clara el factor
    es 1.0 y el halo es byte-idéntico al de antes de este fix. Ver el docstring de
    ``_build_player_halo``/``dibujar_ui`` más abajo y el de ``luciernagas_venado.py``
    ("Refuerzo REAL del halo") para el mecanismo completo.

    Compensación (RETIRADA) del bug de motor H-02: el motor V4 lo cerró de
    raíz (AUD-512), así que esta escena ya no compensa nada -- se deja la
    historia completa aquí para quien audite el rastro. Hasta V3,
    ``HUD.set_boss_hud`` (hud.py) ignoraba su propio parámetro ``phase`` y
    solo guardaba/renderizaba ``phase_count``, mientras que
    ``ActualizacionesDeEscenario._update_hud_ui`` (actualizaciones.py
    ~L59-71, antes ``StageScene._update_hud_ui``) llamaba
    ``set_boss_hud(name, health, max_health, phase, phase_count)`` cada
    cuadro con ``phase_count = boss.phase_count`` (el conteo TOTAL de fases,
    constante 2 para este boss) -- la etiqueta mostraba "PHASE 2" durante
    toda la duración de la fase 0. Desde la fase 2 del proyecto, esta escena
    compensaba volviendo a llamar a ``set_boss_hud`` DESPUÉS de
    ``super().update(dt)`` (así corría después de la propia llamada del
    motor para este cuadro y ganaba), pasando la fase ACTUAL indexada desde
    1 en AMBOS argumentos, ``phase`` y ``phase_count`` -- el segundo era el
    único que el renderizador de entonces realmente leía.

    AUD-512 (motor V4) arregló el HUD de raíz: ``HUD.set_boss_hud`` ahora
    guarda ``_boss_phase`` y ``_boss_phase_count`` en slots separados
    (hud.py ~L435-441), ``HUD._on_boss_phase_changed`` hace lo mismo al
    escuchar ``Events.BOSS_PHASE_CHANGED`` (~L450-460, con el mismo ajuste
    0→1-indexado que ya usaba esta escena) y ``HUD._draw_boss_hud``
    (~L820-831) por fin lee ``self._boss_phase`` -- el slot correcto -- en
    vez de ``self._boss_phase_count``. Con el HUD ya corregido, la doble
    escritura de esta escena pasó de parche necesario a fuente de
    corrupción: seguía sobrescribiendo ``phase_count`` con la fase ACTUAL en
    vez del total, y ese slot es justo el que el HUD V4 sí usa
    correctamente por su cuenta. Por eso ``_compensate_boss_hud_phase`` se
    retiró por completo en esta actualización, junto con su llamada en
    ``update()``. Ver docs/superpowers/REGISTRO-DE-BUGS.md y
    reports/FINDINGS.md H-02 para el rastro forense íntegro (compensación
    aplicada desde la fase 2, retirada aquí tras AUD-512).

    Fijado de cámara de arena H-17 (bug de playtest humano, 2026-07-30): ``Camera``
    (camera.py, sin cambios entre motor V1 y V2 -- verificado byte a byte
    con lógica idéntica, solo dos renombres cosméticos) nunca lee el ``.rect``
    de un lock -- ``set_camera_locks()`` solo cambia ``_is_locked_x/y`` y
    ``update()`` simplemente deja de escribir ``offset`` en un eje bloqueado,
    congelándolo donde sea que ya estuviera (ver camera.py `update()`/
    `set_camera_locks()`). ``_locks_for_player_x`` de arriba restaura los locks
    del TMX en el instante en que ``player.centerx >= ARENA_X0``, pero la
    cámara de seguimiento todavía está a mitad de un lerp en ese instante exacto --
    una repro sin interfaz gráfica (caminando, no teletransportando, desde
    ``PLAYER_SPAWN``) midió que el congelamiento se da en
    ``offset.x == 2102.87`` en el cuadro en que el lock se activa (f1377,
    player.x=2482), es decir, el borde derecho se congelaba en ``2902.87``
    en vez del borde real del mapa en ``3280`` (``offset.x`` necesita ser
    exactamente ``ARENA_X0`` == ``map_w - INTERNAL_WIDTH`` == 2480 para que la
    arena llene el viewport) -- este es el bug de "la cámara no llega al final
    del gazebo". Este mismo problema (y esta misma forma de arreglo) ya se
    resolvió una vez, pre-reset -- ver el
    ``ARENA_RECT``/``_arena_engaged`` de
    ``backups/pre-reset-2026-07-21/src/boss_venado_scene.py`` y su docstring,
    que documenta haber probado primero un snap duro y haberlo rechazado: producía
    un salto de borde ("border-jump") de ~400px en screen_x en un solo cuadro.
    `_pin_camera_to_arena` de abajo reproduce esa forma ya probada adaptada a la
    política de locks basada en alternancia (toggle) actual de esta escena
    (sin latch permanente, sin muro de sellado de entrada -- ambas eran
    decisiones de diseño exclusivas de pre-reset que este rewrite
    intencionalmente no tiene, ver la puerta de regresión no_damage_outside_arena
    en playtest/invariants.py, que depende de que el jugador pueda caminar
    de vuelta hacia afuera de la arena a mitad de la pelea): en el instante en
    que ``player.centerx`` cruza ``ARENA_X0``, suaviza ``camera.offset`` desde
    donde sea que esté la cámara de seguimiento en ese momento hacia la vista
    objetivo exacta de la arena durante ``ARENA_SETTLE_DURATION`` segundos
    (ease-in-out), y luego lo fija explícitamente ahí en CADA cuadro mientras
    el jugador se quede adentro -- así el offset final siempre es exactamente
    correcto sin importar la velocidad de caminata, las alternancias de
    entrada/salida, o las rarezas de los locks del motor, y salir de la arena
    simplemente detiene la anulación y deja que el lerp de seguimiento heredado
    se reanude sin tocarlo.

    H-28/B-032 (código muerto bajo el despacho real del motor, detectado en
    playtest 2026-08-19): ``App._draw()`` (app.py 556-723) despacha por
    duck-typing (``_soporta``, app.py 57-66) a
    ``dibujar_mundo()``/``dibujar_ui()`` para CUALQUIER escena que las
    exponga -- y ``StageScene`` (vía el mixin ``DibujoDeEscenario``, ver
    ``src/framework/scenes/stage_parts/dibujo.py``) siempre las expone.
    ``App`` JAMÁS llama a ``escena.draw()`` en ese caso: la rama
    ``else: escena.draw(...)`` de app.py ni se evalúa (AUD-343). Esta escena
    solía sobrescribir sólo ``draw()`` -- el bloque de overlays (telegraphs
    del jefe, anuncio del enjambre, teletransporte, halo del jugador, icono
    de la Reliquia) era, por tanto, código MUERTO en el juego real: nunca
    corría ni en ``main.py --boss boss_venado`` ni en el arnés, pese a que
    la suite de pruebas de este módulo (que llama ``scene.draw(surface)``
    DIRECTO) seguía en verde -- un falso verde silencioso, porque probar el
    método no es lo mismo que probar el despacho.

    El fix (ver el docstring de ``dibujar_ui`` más abajo) migra ese bloque a
    un override de ``dibujar_ui()`` y elimina ``draw()`` de esta clase por
    completo. Precedente H-27: como ``DibujoDeEscenario.draw`` (heredado) es
    sólo ``dibujar_mundo(surface); dibujar_ui(surface)``, cualquier prueba
    que siga llamando ``scene.draw(surface)`` directo sigue ejerciendo
    exactamente este mismo código por herencia -- no hizo falta reescribir
    esas pruebas, sólo anotarlas (ver la lección H-28 en los docstrings de
    ``test_telegraphs_sobre_la_luz.py``/``test_teletransporte_ux.py``/
    ``test_anuncio_del_enjambre.py``). El candado que sí distingue "probé el
    método" de "probé el despacho real" vive aparte, en
    ``tests/test_despacho_real_overlays.py`` (llama ``App._draw()``, nunca
    ``scene.draw()``).
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.ui.theme import font
from src.engine.utils.math_utils import ease_in_out_quad, lerp
from src.framework.entities.boss_base import BossBase
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.atencion import Atencion
from src.stages.boss_venado.boss_venado import RELIQUIA_NOMBRE
from src.stages.boss_venado.efectos_venado import VELO_COLOR, alfa_de_niebla
from src.stages.boss_venado.luciernagas_venado import FACTOR_HALO_MINIMO, GestorDeLuciernagas
from src.stages.boss_venado.presencias_venado import (
    PRESENCIAS,
    SOMBRA_X0,
    EventoSombraQueCruza,
    GestorDePresencias,
    columna_de_patrullaje,
    fila_de_presencia,
)
from src.stages.boss_venado.tramos_venado import (
    TABLA,
    avance_en_tramo,
    interpolar_grading,
    tramo_en,
)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.framework.vfx.particle_system import BurstConfig
    from src.stages.boss_venado.tramos_venado import Gradacion, Tramo

ARENA_X0 = 2480.0  # mantener sincronizado con boss_venado.ARENA_X0 (borde izquierdo de CameraLock_01)
ARENA_X1 = 3264.0  # mantener sincronizado con boss_venado.ARENA_X1 (RightWall_Arena)

# H-19 (adopción V3): los límites de arena que esta escena le declara al jefe.
# StageScene.on_enter (stage_scene.py ~L454-461) le pasa a TODO BossBase el mapa
# ENTERO como arena -- correcto para un mapa que es una arena, falso para este,
# que es un corredor de 3280px con la arena al final: su centro cae en x=1640, a
# media pradera. `set_arena_bounds` está diseñado justo para que lo llame la
# escena (sólo ella conoce el mapa), así que aquí se corrige con el rect real.
#
# Es seguro estrecharlo: `clamp_to_arena` tiene UN ÚNICO llamante en todo el
# motor (`BossBase.teletransportar`, verificado por grep), así que esto no toca
# movimiento, embestida ni colisión -- sólo acota el destino del teletransporte
# de fase. Y no sustituye al clamp propio del boss
# (`_destino_de_teletransporte`): doble candado, mismo patrón que la
# compensación de H-02.
ARENA_BOUNDS = pygame.Rect(int(ARENA_X0), 0, int(ARENA_X1 - ARENA_X0), 608)

# H-17: cuánto tarda (en segundos) la cámara en suavizarse desde donde sea que
# esté la cámara de seguimiento hasta el cuadro fijado de la arena una vez que el
# jugador cruza ARENA_X0 -- ver _pin_camera_to_arena / la sección H-17 del
# docstring del módulo. Mismo valor que usaba la referencia pre-reset
# (backups/pre-reset-2026-07-21).
ARENA_SETTLE_DURATION = 0.3

# B-045: DEBE quedar < ARENA_SETTLE_DURATION -- ver
# _actualizar_silencio_y_shake_de_arena. Duración del shake único al entrar
# a la arena: si esto se acerca o supera ARENA_SETTLE_DURATION, el shake
# sigue activo cuando _pin_camera_to_arena deja de sobrescribir offset.x,
# y el candado H-17 vuelve a romperse de forma intermitente (offset final
# ~2474-2480 en vez de ARENA_X0 exacto; ver REGISTRO-DE-BUGS.md B-045 para
# el mecanismo completo).
ARENA_SHAKE_DURATION = 0.2

# Tarea 7 del plan de peregrinación: sistema "Atencion" (quietud revela).
# "Detenerse ~3s revela algo" (spec del nivel §3.6) -- ver
# _actualizar_quietud_revela más abajo. COOLDOWN_REVELACION evita que
# plantarse en el mismo sitio dispare la revelación en bucle: sin el
# cooldown, Atencion.esta_quieto() seguiría devolviendo True en todos los
# cuadros siguientes mientras el jugador no se mueva (la quietud es una
# racha que sólo crece, ver atencion.py).
QUIETUD_PARA_REVELAR = 3.0   # segundos
COOLDOWN_REVELACION = 20.0   # segundos antes de que la quietud pueda volver a revelar

PLAYER_HALO_RADIUS = 44   # px; la superficie del halo es (2*RADIUS, 2*RADIUS)
PLAYER_HALO_PEAK = 46     # brillo aditivo máximo en el centro del halo
PLAYER_HALO_TINT = (46, 52, 66)   # tinte frío de luz de luna en el brillo máximo (canal r == PLAYER_HALO_PEAK)

# "Fragmento de Reliquia 1" (adopción V3, D10): el icono que aparece cuando el
# venado termina de desvanecerse. Cornamenta procedural sobre una Surface
# cacheada -- misma técnica que _build_player_halo, cero assets nuevos.
RELIC_ICON_SIZE = 40          # lado de la Surface del icono, px
RELIC_ICON_MARGIN = 12        # separación a los bordes superior/derecho del viewport
RELIC_BANNER_DURATION = 4.0   # segundos que el icono permanece visible
RELIC_FADE_DURATION = 0.6     # fundido de entrada y de salida, dentro de esos segundos
RELIC_ICON_COLOR = (232, 216, 156)   # hueso dorado, el color de las astas del venado


class EfectosDeLaEscena:
    """Implementación real del puerto EfectosDelEscenario (ver efectos_venado.py):
    traduce las cuatro operaciones VFX puras del boss a las APIs concretas del motor
    -- partículas, cámara, estela. Se inyecta en on_enter() (ver ese método): un
    objeto nuevo por cada jefe nuevo, así que no arrastra estado entre reintentos
    del motor V3 (H-18, cada muerte del jugador reconstruye el jefe entero)."""

    def __init__(self, escena: "BossVenadoScene") -> None:
        self._escena = escena

    def particulas(self, x: float, y: float, config: "BurstConfig") -> None:
        self._escena._particle_system.get_emitter("venado").emit(x, y, config)

    def particulas_dirigidas(self, x: float, y: float, angulo: float,
                             config: "BurstConfig") -> None:
        # emit_directed toma spread como SEMI-ángulo (ver su docstring en
        # particle_system.py) -- BurstConfig.spread es el ángulo TOTAL del cono,
        # de ahí la división entre 2.
        self._escena._particle_system.get_emitter("venado").emit_directed(
            x, y, angulo, speed=config.speed, count=config.count,
            lifetime=config.lifetime, size=(config.size_min, config.size_max),
            color=config.color, spread=config.spread / 2.0,
            gravity=config.gravity, friction=config.friction)

    def sacudir(self, amplitud: float, duracion: float,
                direccion: tuple[float, float] | None) -> None:
        camara = getattr(self._escena, "_camera", None)
        if camara is None:
            return
        camara.apply_shake(amplitude=amplitud, duration=duracion, direccion=direccion)

    def estela(self, x: float, y: float, size: tuple[int, int],
               color: tuple[int, int, int, int]) -> None:
        self._escena._enemy_trail_system.capture_at(x, y, size, color)


class BossVenadoScene(StageScene):
    STAGE_ID: str = "boss_venado"
    STAGE_NAME: str = "VENADO"
    ZONE: int = 1  # Zona 1 (Stage 1-4) según 17_BOSS_SPEC §3.1; atributo no usado por el motor, se mantiene coherente con el front-matter del README

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path("assets/maps/boss_venado/boss_venado.tmx"))
        self._original_camera_locks: list = []
        self._player_halo: pygame.Surface | None = None   # cacheado de forma diferida, se construye en el primer dibujar_ui() (H-28)
        # Fix del coordinador (Tarea 12, refuerzo REAL del halo): factor con el que
        # se construyo la copia cacheada de _player_halo -- dibujar_ui invalida el
        # cache SOLO cuando GestorDeLuciernagas.factor_de_halo se aleja de este valor
        # (ver ese metodo), asi que la reconstruccion cara (pygame.draw.circle x
        # PLAYER_HALO_RADIUS) solo ocurre cuando el histograma de verdad cambio de
        # lectura -- a lo sumo cada FRECUENCIA_DE_MUESTREO cuadros (0.5s), nunca cada
        # cuadro.
        self._halo_factor_actual: float = FACTOR_HALO_MINIMO
        self._velo_de_niebla: pygame.Surface | None = None   # B-046: cacheado de forma diferida (primer dibujar_ui())
        # B-049: último alfa con el que se rellenó self._velo_de_niebla -- para
        # NO repetir el relleno por píxel si el jugador no cruzó de columna de
        # niebla entre cuadros (ver _dibujar_velo_de_niebla). getattr defensivo
        # en el punto de lectura (no acceso directo, a diferencia de
        # _halo_factor_actual) porque varios tests de test_boss_scene.py
        # instancian la escena vía BossVenadoScene.__new__ sin pasar por este
        # __init__ y solo fijan _velo_de_niebla -- ver el dictamen doc-guardian
        # de este fix.
        self._velo_alfa_actual: int | None = None
        # Fijado de cámara de arena H-17 (ver docstring del módulo): estado de
        # suavizado transitorio, NO un latch permanente -- se rearma cada vez que
        # player_x vuelve a cruzar por debajo de ARENA_X0, así que reentrar
        # vuelve a suavizar limpiamente en vez de hacer un corte duro.
        self._in_arena_prev: bool = False
        self._arena_ease_elapsed: float = ARENA_SETTLE_DURATION  # empieza "asentado"
        self._arena_ease_start: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        # Banner de la reliquia (adopción V3, D10): superficie cacheada de forma
        # diferida + temporizador de visibilidad.
        self._relic_icon: pygame.Surface | None = None
        self._relic_timer: float = 0.0
        self._relic_shown: bool = False
        # Ambientacion narrativa del corredor (Tarea 2 del plan de
        # peregrinacion): estado de interpolacion entre tramos, mismo
        # patron que _gradacion_previa/_tinte_previo de stage4_1.py.
        self._tramo_actual: Tramo | None = None
        self._tramo_grading_previo: Gradacion = None
        self._tramo_tinte_previo: tuple[tuple[int, int, int], float] | None = None
        # Semilla inicial tomada de TABLA[0] (Acto 1, donde spawnea el
        # jugador) -- irrelevante en la practica: la primera pasada de
        # _actualizar_tramo_narrativo siempre la sobreescribe (tramo_actual
        # arranca en None, así que esa primera pasada entra por la rama
        # "tramo is not self._tramo_actual" y la recalcula de cero).
        self._tramo_vineta_previa: float = TABLA[0].vineta
        # Fauna decorativa del corredor (Tarea 4 del plan de peregrinacion):
        # dano 0, sin ECS -- ver presencias_venado.py.
        self._gestor_presencias = GestorDePresencias()
        # "Sombra que cruza" (Tarea 5 del plan de peregrinacion): aviso ÚNICO
        # (sombra fuera de cámara + bramido espacial) justo antes de la
        # revelación del jefe -- ver presencias_venado.EventoSombraQueCruza.
        # _play_sfx_spatial (sonido.py:157-161, mixin de StageScene) toma un
        # nombre de sonido DIRECTO, no un Events.SFX_*: el stem del .wav
        # nuevo generado por tools/generar_sfx_bramido.py ya es el nombre
        # que SoundBank.load_all() registra (sound_bank.py:34-43).
        self._sombra_que_cruza = EventoSombraQueCruza(
            reproducir_sfx=lambda x: self._play_sfx_spatial(
                "sfx_bosses_venado_bramido_lejano", x, volume=0.8))
        # Silencio súbito + shake único + eco del gazebo (Tarea 6 del plan de
        # peregrinación): ver _actualizar_silencio_y_shake_de_arena más abajo.
        # _shake_de_arena_disparado es un disparo ÚNICO por episodio (H-18,
        # mismo patrón que _sombra_que_cruza._disparado); _eco_activo, en
        # cambio, refleja si el jugador está DENTRO del gazebo ahora mismo
        # (se enciende y apaga con cada cruce, nunca hace latch).
        self._shake_de_arena_disparado = False
        self._eco_activo = False
        # Sistema "Atencion" (Tarea 7 del plan de peregrinación): mide cuánto
        # lleva quieto el jugador -- si se planta más de
        # QUIETUD_PARA_REVELAR segundos, revela algo (ver
        # _actualizar_quietud_revela), con un enfriamiento
        # (_cooldown_revelacion) para que no sea explotable quedándose
        # quieto en bucle ("detenerse también es jugar").
        self._atencion = Atencion()
        self._cooldown_revelacion = 0.0
        # Unidad VII -- "La Hora de las Luciernagas" (Tarea 12 del plan de
        # peregrinacion): el histograma de luminancia (FilterTools.compute_histogram,
        # ver luciernagas_venado.py) dirige DOS salidas de logica real, desde la MISMA
        # lectura: cuantas luciernagas se encienden (cantidad_objetivo) Y cuanto se
        # refuerza el halo lunar del jugador (factor_de_halo, fix del coordinador --
        # ver el parrafo "Refuerzo del halo por histograma" del docstring del modulo
        # y _build_player_halo/dibujar_ui mas abajo para el mecanismo real). El
        # gestor vive aqui (no se reinicia en on_enter -- ver esa nota mas abajo:
        # a diferencia de _sombra_que_cruza/_atencion, este estado no representa
        # "algo ya visto una vez en este episodio", asi que sobrevivir a un
        # reintento H-18 es correcto, no un bug). _tiempo_luciernagas es un reloj
        # de SIMULACION propio (acumulado con el dt de update(), NUNCA
        # pygame.time.get_ticks()): el arnes corre a paso fijo y determinista, y
        # un parpadeo basado en reloj de pared produciria un resultado distinto
        # cada corrida, rompiendo cualquier golden/candado que compare cuadros
        # pixel a pixel (ver _dibujar_luciernagas mas abajo).
        self._gestor_luciernagas = GestorDeLuciernagas()
        self._tiempo_luciernagas: float = 0.0

    def on_enter(self) -> None:
        super().on_enter()
        if self._stage_data is not None:
            self._original_camera_locks = list(self._stage_data.camera_locks)
        # Adopción V3 (D3/D8): todo lo que el jefe necesita de la escena se
        # inyecta AQUÍ, después de super().on_enter(), y no en __init__.
        #
        # No es un detalle de estilo: `respawn()` (stage_scene.py:712-743)
        # reejecuta on_enter() y reconstruye StageData, o sea que tras cada
        # muerte del jugador el jefe es un OBJETO NUEVO (el reintento del motor
        # V3, hallazgo H-18). Inyectar en el constructor de la escena dejaría
        # mudo y sin arena a todo reintento.
        jefe = self._get_boss()
        if jefe is not None:
            # H-19 (histórico) / adopción post-drop #6 (2026-08-26): desde
            # que el TMX declara ``ArenaZone_01`` (2480,0,784,608, generador
            # gen_level_residencias.py), super().on_enter() ya entrega el
            # rect CORRECTO -- lee la primera ArenaZone que contiene al jefe
            # vía ``_arena_del_jefe`` (stage_scene.py:81-91, AUD-605), no el
            # mapa entero como en el H-19 original. Este override se
            # CONSERVA a propósito como doble candado (decisión del
            # dictamen 2026-08-26): sigue siendo la fuente de verdad si
            # ``ARENA_BOUNDS`` de esta escena y el rect del TMX alguna vez
            # divergen, y no cuesta nada mantenerlo -- ver ARENA_BOUNDS.
            jefe.set_arena_bounds(pygame.Rect(ARENA_BOUNDS))
            jefe.audio_de_voz = getattr(self.context, "audio_manager", None)
            jefe.conectar_efectos(EfectosDeLaEscena(self))   # pulido AAA 2026-08-21: puerto VFX del boss
        # Reintento del motor V3 (H-18): tras un respawn el jefe vuelve a estar
        # vivo, así que el banner de la reliquia se rearma con él.
        self._relic_timer = 0.0
        self._relic_shown = False
        # Tarea 5: cada episodio de vida (H-18) merece volver a ver/oír el
        # aviso de la sombra que cruza -- mismo motivo que el reinicio del
        # banner de la reliquia justo arriba.
        self._sombra_que_cruza.reiniciar()
        # Tarea 6: mismo motivo que la línea de arriba -- un episodio nuevo
        # (muerte + respawn, H-18) merece volver a temblar al entrar y a oír
        # el eco del gazebo, en vez de heredar el "ya disparado" del intento
        # anterior.
        self._shake_de_arena_disparado = False
        self._eco_activo = False
        # Tarea 7: mismo motivo que las dos líneas de arriba -- un episodio
        # nuevo empieza sin quietud acumulada y sin el enfriamiento del
        # intento anterior colgado (si no, un jugador que murió justo
        # después de revelar algo reaparecería con el cooldown ya corriendo,
        # o peor, con quietud heredada de la posición de muerte).
        self._atencion.reiniciar()
        self._cooldown_revelacion = 0.0
        # Reinicio al estilo H-06 (ver boss-venado FINDINGS H-06): on_enter() se
        # reproduce textualmente por respawn(), que reconstruye una Camera
        # nueva en el offset (0, 0) -- un True obsoleto aquí se saltaría el
        # suavizado y fijaría la cámara nueva a la arena en el cuadro 1 aunque
        # el jugador acabe de reaparecer de vuelta en el PlayerSpawn del nivel,
        # fuera de la arena.
        self._in_arena_prev = False
        self._arena_ease_elapsed = ARENA_SETTLE_DURATION
        self._arena_ease_start.update(0.0, 0.0)

    def on_exit(self) -> None:
        """Apaga el bus de reverberación al salir de la escena (Tarea 6).

        Mismo contrato que ``Stage4_1.on_exit`` (stage4_1.py:453-463,
        AUD-594): ``activar_eco`` es estado del MEZCLADOR, compartido por
        todas las escenas, no de ``self`` -- salir de esta escena (fin de
        partida, transición) con el eco encendido a mitad de la arena lo
        dejaría colado en lo que sea que se cargue después. Se apaga ANTES
        de delegar en ``super().on_exit()`` (StageScene.on_exit,
        stage_scene.py ~L694-714) porque ese método ya destruye HUD/subtítulos
        y suelta el scope del AssetLoader -- el orden entre ambas cosas no
        importa en la práctica (no comparten estado), pero apagarlo primero
        deja claro que esto es limpieza propia de la escena, no parte del
        cierre genérico heredado.

        ``getattr`` doble (no ``self.audio``) por el mismo motivo defensivo
        que el resto de este módulo (``_pin_camera_to_arena``,
        ``_update_relic_banner``): degrada a no-op en los dobles de prueba
        de ``BossVenadoScene.__new__(...)`` sin ``__init__`` real."""
        audio = getattr(getattr(self, "context", None), "audio", None)
        if audio is not None and self._eco_activo:
            audio.activar_eco(False)
        super().on_exit()

    @staticmethod
    def _locks_for_player_x(player_x: float, original_locks: list) -> list:
        """Política de zona pura: vacía fuera de la arena, los locks originales adentro."""
        return original_locks if player_x >= ARENA_X0 else []

    def _get_boss(self) -> BossBase | None:
        """Contrato del Playtest Recorder: expone la entidad boss viva."""
        if self._stage_data is None:
            return None
        for entity in self._stage_data.entity_list:
            if isinstance(entity, BossBase):
                return entity
        return None

    def _arena_target_offset(self) -> tuple[float, float]:
        """H-17 (ver docstring del módulo): el offset que encuadra la arena
        exactamente -- x = ARENA_X0 (la arena mide exactamente un INTERNAL_WIDTH
        de ancho de viewport, por diseño del mapa: map_w - ARENA_X0 == 800 ==
        INTERNAL_WIDTH), y = el propio clamp inferior del mapa (refleja el
        clamp ``max(0.0, min(offset.y, map_h - screen_h))`` del propio
        Camera.update(), así esto nunca entra en conflicto con ese clamp en los
        ejes que CameraLock_01 en realidad no necesita fijar)."""
        stage = self._stage_data
        map_h = stage.map_pixel_size[1] if stage is not None else settings.INTERNAL_HEIGHT
        target_y = max(0.0, float(map_h) - settings.INTERNAL_HEIGHT)
        return ARENA_X0, target_y

    def _pin_camera_to_arena(self, dt: float, in_arena: bool) -> None:
        """H-17 (ver docstring del módulo): lleva explícitamente camera.offset
        al encuadre exacto de la arena mientras el jugador está adentro, en
        vez de depender de la semántica de Camera de que los locks se congelan
        donde sea que estén. Debe correr DESPUÉS de super().update(dt) (así
        tiene la última palabra sobre camera.offset en este cuadro, la misma
        restricción de orden que en su momento exigía también la ya retirada
        compensación de HUD de H-02, ver la sección H-02 del docstring del
        módulo) -- así el motor centra el fondo de pyscroll (en tiempo de
        dibujo, ver la sección H-10 (RETIRADA) del docstring del módulo)
        sobre el offset ya fijado, no sobre el de antes del fijado. Usa
        ``getattr`` (no un ``self._camera`` directo) para que degrade a
        no-op en los dobles de prueba de ``BossVenadoScene.__new__(...)``
        sin inicializar que el módulo de pruebas unitarias hermano de este
        archivo conecta a mano sin un ``__init__`` real (ver
        ``_bare_scene_with_boss`` de test_boss_scene.py), el mismo estilo
        defensivo por ``getattr`` que usa el resto de este módulo (ver
        ``_update_relic_banner`` más abajo)."""
        if getattr(self, "_camera", None) is None:
            return
        if not in_arena:
            self._in_arena_prev = False
            return
        target_x, target_y = self._arena_target_offset()
        if not self._in_arena_prev:
            # Se acaba de cruzar ARENA_X0 en este cuadro (o se reingresó
            # después de haber salido): arranca un suavizado nuevo desde donde
            # sea que esté ahora la cámara de seguimiento -- hacer un snap
            # produce el corte duro de "border-jump" de ~400px que la
            # referencia pre-reset ya combatió y rechazó (ver
            # backups/pre-reset-2026-07-21/src/boss_venado_scene.py).
            self._arena_ease_elapsed = 0.0
            self._arena_ease_start.update(self._camera.offset)
            self._in_arena_prev = True
        if self._arena_ease_elapsed < ARENA_SETTLE_DURATION:
            self._arena_ease_elapsed += dt
            t = min(1.0, self._arena_ease_elapsed / ARENA_SETTLE_DURATION)
            eased_t = ease_in_out_quad(t)
            self._camera.offset.x = lerp(self._arena_ease_start.x, target_x, eased_t)
            self._camera.offset.y = lerp(self._arena_ease_start.y, target_y, eased_t)
            if t >= 1.0:
                # Cae exactamente en el objetivo (el lerp en punto flotante en
                # t==1.0 ya hace esto, pero se fija explícitamente para que nada
                # aguas abajo llegue a ver jamás un offset con un error de
                # epsilon).
                self._camera.offset.x = target_x
                self._camera.offset.y = target_y
        # si no: el suavizado ya terminó en un cuadro anterior -- deliberadamente
        # NO se reescribe offset aquí en cada cuadro. `stage.camera_locks` ya
        # es los locks (no vacíos) del TMX mientras in_arena es verdadero (ver
        # update()), así que el propio congelamiento de lock de Camera
        # (camera.py update()/set_camera_locks(), ver la sección H-17 del
        # docstring del módulo) ahora mantiene offset.x/y en exactamente
        # target_x/target_y por sí solo -- nada más escribe en un eje
        # bloqueado excepto el offset de screen-shake de apply_shake(), que
        # Camera.update() suma Y resta simétricamente cada cuadro
        # (`offset -= self._shake_offset` luego se recalcula y luego
        # `offset += self._shake_offset`), así que esto se cancela sin
        # ninguna deriva por sí solo. Sobrescribir offset aquí sin condición
        # en cada cuadro (el enfoque de la referencia pre-reset -- ver el
        # docstring del módulo) cancelaría silenciosamente ese shake durante
        # el resto entero de la pelea, por ejemplo, cada screen shake de
        # VFX_SLAM/VFX_ULTIMATE/golpe-al-jugador que StageScene aplica
        # mientras el jugador está en la arena.

    @staticmethod
    def _build_player_halo(factor: float = FACTOR_HALO_MINIMO) -> pygame.Surface:
        """Constructor puro (sin estado de escena) para el halo de luz de luna
        -- ver docstring del módulo. Círculos concéntricos desde el radio
        exterior hacia adentro, cada uno dibujado un poco más brillante que el
        anterior, producen un degradado radial barato: PLAYER_HALO_TINT
        (escalado a PLAYER_HALO_PEAK) en el centro, desvaneciéndose
        linealmente hacia transparente (no-op de RGBA_ADD) en el borde. Quien
        llame debería construir esto UNA vez por valor de ``factor`` y cachear
        el resultado (ver ``dibujar_ui`` más abajo, que invalida ese caché solo
        cuando el factor cambia) -- esta función en sí no hace ningún cacheo.

        ``factor`` (fix del coordinador, Tarea 12 -- "refuerzo REAL del halo"):
        multiplicador de brillo, normalmente
        ``luciernagas_venado.GestorDeLuciernagas.factor_de_halo`` (rango
        ``[FACTOR_HALO_MINIMO, FACTOR_HALO_MAXIMO]`` == ``[1.0, 1.35]``,
        derivado del MISMO histograma de luminancia que decide cuántas
        luciérnagas se encienden -- ver el docstring de luciernagas_venado.py,
        "Refuerzo REAL del halo"). El default ``FACTOR_HALO_MINIMO`` (1.0)
        preserva el comportamiento histórico EXACTO, byte a byte (multiplicar
        por 1.0 no cambia ningún resultado de ``int()`` -- ver el cálculo de
        ``color`` más abajo): ``_build_player_halo()`` sin argumento (como la
        llama ``test_player_halo_never_silently_disabled``, el candado de piso
        preexistente) sigue produciendo exactamente el mismo halo que antes de
        este fix. Con ``factor > 1.0`` el pico efectivo sube -- SIEMPRE por
        encima del piso que protege ese candado, nunca por debajo (el factor
        real nunca es menor que ``FACTOR_HALO_MINIMO``, ver
        ``GestorDeLuciernagas``).

        Superficie con alfa (H-28/B-032, riesgo 2 del dictamen doc-guardian):
        antes de este fix era una ``Surface`` opaca sin canal alfa, pintada
        con ``BLEND_RGB_ADD`` -- funcionaba en el camino de software porque
        ahí ``dibujar_ui`` pinta directo sobre ``internal_surface``, que
        tampoco tiene alfa (app.py 704-718). Pero bajo la ruta de GPU
        ``dibujar_ui`` pinta sobre ``_ui_overlay_surface``, un ``SRCALPHA``
        que nace en alfa 0 cada cuadro (app.py 230-233/696) y que
        ``App`` compone después con un blit normal que SÍ respeta el alfa
        por píxel del origen (app.py 700-703): un halo sin alfa propio
        quedaría con RGB correcto pero alfa 0 en esa composición, y esos
        píxeles se descartarían enteros -- el halo se pintaría y, acto
        seguido, se borraría solo. Por eso cada píxel se dibuja con un color
        RGBA explícito, no sólo RGB: el alfa se cocina del propio brillo del
        degradado (``max(color)``, el mismo criterio que ya usa el brillo en
        sí) para que el círculo más tenue -- que en RGB ya es casi un no-op
        de ``ADD`` -- también lo sea en alfa, y el centro, que sí debe
        notarse, lleve alfa suficiente para sobrevivir la composición.
        ``BLEND_RGBA_ADD`` (en vez de ``BLEND_RGB_ADD``, ver la llamada en
        ``dibujar_ui``) suma las cuatro bandas -- RGB Y alfa -- así que ese
        alfa cocinado sube al overlay junto con el color en el mismo blit."""
        size = PLAYER_HALO_RADIUS * 2
        halo = pygame.Surface((size, size), pygame.SRCALPHA)
        halo.fill((0, 0, 0, 0))   # transparente por defecto -- ver el razonamiento de arriba
        center = (PLAYER_HALO_RADIUS, PLAYER_HALO_RADIUS)
        for radius in range(PLAYER_HALO_RADIUS, 0, -1):
            # 0.0 en el borde (radius == PLAYER_HALO_RADIUS) -> ~1.0 cerca del centro.
            brightness = 1.0 - (radius / PLAYER_HALO_RADIUS)
            # factor multiplica DESPUES de brightness, no la sustituye: con
            # factor == FACTOR_HALO_MINIMO (1.0) esto es matematicamente
            # identico a `channel * brightness` (multiplicar por 1.0 no
            # cambia el resultado ni el truncamiento de int()) -- el
            # comportamiento historico queda intacto byte a byte. min(255, ..)
            # es una cota defensiva (FACTOR_HALO_MAXIMO=1.35 nunca la alcanza
            # con PLAYER_HALO_TINT=(46,52,66): 66*1.35≈89) para que un ajuste
            # futuro de las constantes no desborde el canal de color.
            color = tuple(min(255, int(channel * brightness * factor)) for channel in PLAYER_HALO_TINT)
            alpha = max(color)   # alfa coherente con el brillo -- ver el docstring de arriba
            pygame.draw.circle(halo, (*color, alpha), center, radius)
        return halo

    @staticmethod
    def _build_relic_icon() -> pygame.Surface:
        """Constructor puro del icono de "Fragmento de Reliquia 1" (D10).

        Cornamenta procedural sobre una Surface con alfa -- misma técnica
        cacheada que `_build_player_halo`, para no depender de ningún asset
        nuevo (crear archivos fuera de las zonas editables está prohibido) ni de
        ninguna API de iconos del HUD (verificado: no existe). Un asta es una
        línea troncal con tres candiles; la otra es su reflejo horizontal, así
        que la simetría sale de una sola descripción."""
        icono = pygame.Surface((RELIC_ICON_SIZE, RELIC_ICON_SIZE), pygame.SRCALPHA)
        medio = RELIC_ICON_SIZE // 2
        base_y = RELIC_ICON_SIZE - 4
        # Puntos en el semiplano derecho, relativos al eje central. Se dibuja
        # cada segmento dos veces, con dx y con -dx.
        tronco = [(1, 0), (4, -8), (7, -18), (6, -30)]
        candiles = [((4, -8), (12, -12)), ((7, -18), (15, -23)), ((7, -18), (11, -31))]
        for signo in (1, -1):
            puntos = [(medio + signo * dx, base_y + dy) for dx, dy in tronco]
            pygame.draw.lines(icono, RELIC_ICON_COLOR, False, puntos, 2)
            for (ax, ay), (bx, by) in candiles:
                pygame.draw.line(
                    icono, RELIC_ICON_COLOR,
                    (medio + signo * ax, base_y + ay),
                    (medio + signo * bx, base_y + by), 2,
                )
        # El cráneo del que nacen las astas: un punto de anclaje, no un dibujo.
        pygame.draw.circle(icono, RELIC_ICON_COLOR, (medio, base_y - 1), 3)
        return icono

    @staticmethod
    def _build_velo_de_niebla() -> pygame.Surface:
        """Constructor puro (B-046, re-fix B-049) del velo de niebla -- una
        superficie de pantalla completa, del color
        ``efectos_venado.VELO_COLOR``, CON canal alfa por píxel
        (``pygame.SRCALPHA`` -- misma técnica que ``_build_player_halo``/
        ``_build_relic_icon``). Arranca totalmente transparente
        (``(*VELO_COLOR, 0)``, nunca sin inicializar -- una ``Surface``
        recién creada no tiene contenido garantizado por la API de pygame,
        mismo motivo que ``_halo_neutro()`` documenta en el archivo de
        candados); quien llame rellena el alfa real por píxel antes de
        blitear (ver ``_dibujar_velo_de_niebla``).

        B-049 (REGISTRO-DE-BUGS.md, "mundo negro" en todo el Acto 3,
        playtest humano 2026-08-25) -- este método usaba antes una Surface
        SIN ``SRCALPHA``, modulada con ``Surface.set_alpha()`` (alfa POR
        SUPERFICIE) en vez de por píxel. Eso no fallaba en la ruta de
        software (ahí ``dibujar_ui`` pinta DIRECTO sobre
        ``internal_surface``, sin overlay ``SRCALPHA`` de por medio -- no
        hay composición de alfa que proteger). Pero bajo la ruta de GPU,
        ``dibujar_ui`` pinta sobre ``_ui_overlay_surface`` (``SRCALPHA``,
        nace en alfa 0 cada cuadro, app.py 230-233/696) que ``App``/
        ``GLRenderer`` componen DESPUÉS con el mismo contrato de alfa que un
        blit normal contra un destino ``SRCALPHA``: gotcha de SDL2/pygame
        verificado empíricamente (``reports\\peregrinacion_playtest_humano\\
        debug_negro\\exp_alpha_blit.py``, N=4..255) -- blitear un origen SIN
        canal alfa por píxel sobre un destino ``SRCALPHA`` deja el ALFA DE
        DESTINO en 255 (opaco) en TODA el área cubierta por el blit, sin
        importar el alfa por superficie del origen. El velo cubre la
        pantalla ENTERA, así que ese único blit dejaba el overlay COMPLETO
        marcado opaco con el tinte ya atenuado del velo -- y como este velo
        se pinta PRIMERO en ``dibujar_ui`` (ver su docstring), la
        composición final de la ruta GL (``base.blit(overlay, (0, 0))``,
        mismo contrato que
        ``test_despacho_real_overlays.py::_componer_dibujar_ui_por_alfa``)
        sustituía el MUNDO ENTERO por ese tinte -- confirmado con la escena
        real (``debug_negro\\repro_negro.py``: lum_gl~9-19 contra
        lum_sw~36-44 en x=1530/1550/1575; la ruta de software, sin overlay
        de por medio, no se veía afectada).

        El fix: una Surface ``SRCALPHA`` (este método) rellenada por PÍXEL
        cada vez que el alfa cambia (``surface.fill((*VELO_COLOR, alfa))``,
        ver ``_dibujar_velo_de_niebla``) en vez de una Surface opaca
        modulada con ``set_alpha()``. Un ``blit`` normal (sin flags
        especiales) de un origen ``SRCALPHA`` sobre un destino ``SRCALPHA``
        SÍ compone (y por tanto SÍ escribe) el alfa por píxel del origen --
        el mismo contrato que ``_draw_relic_icon``/``EstelaDeFantasmas.
        dibujar_mundo`` ya usan con éxito (ninguno de los dos cubre la
        pantalla ENTERA, así que el defecto de origen nunca los tocó a
        ellos). Candado de regresión:
        ``test_despacho_real_overlays.py::
        test_velo_de_niebla_sobrevive_la_composicion_por_alfa_de_la_ruta_gl``."""
        surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
        surface.fill((*VELO_COLOR, 0))
        return surface

    def _dibujar_velo_de_niebla(self, surface: pygame.Surface) -> None:
        """Compensación de B-046 (REGISTRO-DE-BUGS.md) -- el motor no puede
        transicionar clima en esta escena (reloj congelado por
        ``day_length=0``) ni interpolar el overlay de ``WeatherSystem`` en
        absoluto, así que el velo del corredor es enteramente de esta
        escena: el perfil PURO vive en
        ``efectos_venado.alfa_de_niebla(x)`` (léase su docstring para la
        narrativa completa); este método solo resuelve la x del jugador,
        cachea-construye la superficie una vez (``_build_velo_de_niebla``,
        nunca más de una vez por episodio) y rellena-blitea. Sin jugador
        (dobles de prueba mínimos) no hay nada que dibujar -- mismo patrón
        defensivo que el resto de overlays de ``dibujar_ui``.

        B-049 -- relleno por PÍXEL (``surface.fill((*VELO_COLOR, alfa))``,
        sobre la Surface ``SRCALPHA`` que ahora construye
        ``_build_velo_de_niebla``) en vez de ``Surface.set_alpha()``; ver el
        docstring de ese método para el porqué. ``self._velo_alfa_actual``
        cachea el último alfa con el que se rellenó, así que el ``fill`` de
        800×600 (barato, pero gratis es mejor) solo corre cuando el alfa
        realmente cambió entre cuadros -- el alfa solo cambia cuando el
        jugador se mueve en X, así que un jugador quieto (o fuera de la
        franja de niebla) no repite el relleno cuadro a cuadro."""
        if self._player is None:
            return
        alfa = alfa_de_niebla(float(self._player.rect.centerx))
        if alfa <= 0:
            return
        if self._velo_de_niebla is None:
            self._velo_de_niebla = self._build_velo_de_niebla()
        if alfa != getattr(self, "_velo_alfa_actual", None):
            self._velo_de_niebla.fill((*VELO_COLOR, alfa))
            self._velo_alfa_actual = alfa
        surface.blit(self._velo_de_niebla, (0, 0))

    def _dibujar_luciernagas(self, surface: pygame.Surface) -> None:
        """Tarea 12 (Unidad VII) -- dibuja
        ``self._gestor_luciernagas.cantidad_objetivo`` puntos de luz aditivos
        (ver el docstring de ``dibujar_ui`` para por qué el DIBUJO vive aquí y
        no en ``dibujar_mundo``, donde sí vive el MUESTREO del histograma que
        decide esta cantidad -- ``luciernagas_venado.GestorDeLuciernagas``).

        Posiciones deterministas por índice (ángulo dorado, sin RNG): una
        posición fija por índice evita el "pop" de reposicionar todas las
        luciérnagas cada vez que ``cantidad_objetivo`` cambia (cada
        FRECUENCIA_DE_MUESTREO cuadros) -- solo aparecen/desaparecen las de
        índice más alto, las demás no se mueven. El parpadeo usa
        ``self._tiempo_luciernagas`` (reloj de SIMULACIÓN acumulado en
        ``update()`` con el ``dt`` del motor), nunca
        ``pygame.time.get_ticks()`` -- un reloj de pared haría que el mismo
        seed/misma secuencia de input produjera un parpadeo distinto en cada
        corrida del arnés, rompiendo cualquier candado o golden que compare
        cuadros pixel a pixel entre corridas (mismo motivo, mismo patrón, que
        ``efectos_venado`` usa ``boss._t_vfx`` en vez de reloj de pared para
        sus propias oscilaciones).

        Alfa cocinado en el color de cada punto (``color = (..., int(120 *
        parpadeo))``) + ``special_flags=pygame.BLEND_RGBA_ADD`` -- mismo
        patrón "Riesgo 2 del dictamen doc-guardian" que ya resolvió el halo
        del jugador (ver ``_build_player_halo``): necesario porque
        ``dibujar_ui`` pinta sobre una superficie ``SRCALPHA`` que nace en
        alfa 0 bajo la ruta de GPU (``_ui_overlay_surface``, app.py:696) --
        ``BLEND_RGBA_ADD`` suma también el canal alfa, así que estos píxeles
        sí sobreviven la composición por alfa posterior
        (``base.blit(overlay, (0, 0))``, app.py:700-703) en vez de quedar con
        RGB correcto y alfa 0 (invisibles). Sin jugador/gestor (dobles de
        prueba mínimos) degrada a no-op -- mismo estilo defensivo que
        ``_dibujar_velo_de_niebla``.

        Decisión de rendimiento (revisión de calidad del coordinador, punto
        BAJA -- caché por radio en vez de una superficie nueva por luciérnaga
        y por cuadro, siguiendo la disciplina de caché del resto del archivo:
        halo/velo/icono de reliquia): NO se aplica aquí, con la misma
        disciplina de medir antes de decidir que ya usó el muestreo del
        histograma (ver el docstring de ``dibujar_mundo``/de
        ``luciernagas_venado.py``, "Muestreo reducido").

        (1) El pulso de alfa exige una superficie fresca de verdad, no solo
        una hipótesis: ``surface.blit(..., special_flags=pygame.BLEND_RGBA_ADD)``
        IGNORA por completo ``Surface.set_alpha()`` (el alfa POR SUPERFICIE,
        distinto del alfa POR PÍXEL ya cocinado en cada círculo) -- verificado
        empíricamente en esta revisión: blitear la MISMA superficie cacheada
        con ``set_alpha(255)``, ``set_alpha(50)`` y ``set_alpha(0)`` produce
        EL MISMO píxel de destino en los tres casos bajo ``BLEND_RGBA_ADD``
        (mismo hallazgo, mismo mecanismo, que ya documentó
        ``_build_player_halo`` para el halo del jugador). Cachear solo 3
        superficies por radio (``radio ∈ {2, 3, 4}``, ver el cálculo de
        ``radio`` más abajo) y reutilizarlas con ``set_alpha()`` para variar
        el brillo del pulso NO funcionaría -- el pulso se congelaría en el
        alfa con el que se cocinó cada superficie cacheada la primera vez.
        Lograr un caché que preserve el pulso exigiría precocinar una
        matriz de superficies por (radio, cubo de alfa cuantizado) -- una
        superficie nueva por cada combinación discreta, más la lógica de
        cuantizar ``parpadeo`` a un cubo y de invalidar/crecer el caché --
        bastante más código y una superficie de bugs nueva, a cambio de nada
        si el costo real ya es insignificante (ver (2)).

        (2) Medido, no asumido: microbenchmark de 2000 cuadros simulando el
        PEOR caso (``n=MAXIMO_LUCIERNAGAS=14``, el máximo posible) de este
        método completo -- crear las 14 superficies SRCALPHA, dibujar cada
        círculo y blitearlas con ``BLEND_RGBA_ADD`` -- en este mismo entorno:
        ``~0.03 ms/cuadro``, un 0.18% del presupuesto de un cuadro a 60fps
        (16.7 ms) -- tres órdenes de magnitud por debajo del costo de
        ``compute_histogram()`` (~37ms sin reducir, ~2ms reducido) que sí
        justificó bajar ``FRECUENCIA_DE_MUESTREO``. No hay ningún
        presupuesto real que este caché fuera a recuperar."""
        gestor = getattr(self, "_gestor_luciernagas", None)
        if gestor is None:
            return
        n = gestor.cantidad_objetivo
        if n <= 0:
            return
        t = self._tiempo_luciernagas
        for i in range(n):
            fase = i * 2.399963  # ángulo dorado -- distribución visualmente uniforme sin RNG
            x = (math.sin(fase) * 0.5 + 0.5) * settings.INTERNAL_WIDTH
            y = (math.cos(fase * 1.3) * 0.5 + 0.5) * settings.INTERNAL_HEIGHT
            parpadeo = 0.5 + 0.5 * math.sin(t * 2.0 + i)
            radio = 2 + int(parpadeo * 2)
            color = (200, 230, 140, int(120 * parpadeo))
            punto = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
            pygame.draw.circle(punto, color, (radio, radio), radio)
            surface.blit(punto, (int(x - radio), int(y - radio)), special_flags=pygame.BLEND_RGBA_ADD)

    def _update_relic_banner(self, dt: float) -> None:
        """Arma el banner cuando el jefe anuncia la reliquia y lo hace decaer.

        Se consulta la bandera del jefe en vez de suscribirse al evento porque
        el jefe deja de estar en `entity_list` poco después de morir: el
        temporizador local sobrevive a esa desaparición, y el banner no depende
        de que un handler siga vivo (el EventBus del motor guarda weakrefs).

        Usa ``getattr`` para degradar a no-op en los dobles de prueba de
        ``BossVenadoScene.__new__(...)`` sin ``__init__`` que el módulo de
        pruebas hermano conecta a mano -- mismo estilo defensivo que ya usa
        ``_pin_camera_to_arena`` más arriba."""
        if getattr(self, "_relic_timer", None) is None:
            return
        if self._relic_timer > 0.0:
            self._relic_timer = max(0.0, self._relic_timer - dt)
            return
        jefe = self._get_boss()
        if jefe is not None and getattr(jefe, "reliquia_anunciada", False):
            # Una sola vez: en cuanto arranca, el `if` de arriba se lleva los
            # fotogramas siguientes y esta rama no vuelve a entrar.
            if not self._relic_shown:
                self._relic_shown = True
                self._relic_timer = RELIC_BANNER_DURATION

    def _draw_relic_icon(self, surface: pygame.Surface) -> None:
        """Pinta el icono y el nombre de la reliquia arriba a la derecha (D10).

        Espacio de pantalla y encima de todo, como el halo: es una nota al
        jugador, no un objeto del mundo. Fundido de entrada y de salida para que
        no aparezca ni desaparezca de golpe. Mismo ``getattr`` defensivo que
        ``_update_relic_banner``, por los dobles de prueba sin ``__init__``."""
        if not getattr(self, "_relic_timer", 0.0) > 0.0:
            return
        if self._relic_icon is None:
            self._relic_icon = self._build_relic_icon()
        transcurrido = RELIC_BANNER_DURATION - self._relic_timer
        fade = min(1.0, transcurrido / RELIC_FADE_DURATION,
                   self._relic_timer / RELIC_FADE_DURATION)
        alpha = int(255 * max(0.0, fade))
        ancho = surface.get_width()
        x = ancho - RELIC_ICON_SIZE - RELIC_ICON_MARGIN
        icono = self._relic_icon.copy()
        icono.set_alpha(alpha)
        surface.blit(icono, (x, RELIC_ICON_MARGIN))
        if not pygame.font.get_init():
            return
        etiqueta = font(10).render(RELIQUIA_NOMBRE, True, RELIC_ICON_COLOR)
        etiqueta.set_alpha(alpha)
        surface.blit(etiqueta, (ancho - etiqueta.get_width() - RELIC_ICON_MARGIN,
                                RELIC_ICON_MARGIN + RELIC_ICON_SIZE + 2))

    def _actualizar_tramo_narrativo(self, dt: float) -> None:
        """Gradacion/tinte/vineta por avance espacial del corredor -- misma
        idea de interpolacion por tramos que stage4_1.py:680-708
        (_actualizar_gradacion), leyendo la tabla pura de tramos_venado.py.

        La firma con ``dt`` NO es un calco de esa referencia: la
        interpolacion es puramente ESPACIAL (depende solo de
        self._player.rect.centerx via tramo_en()/avance_en_tramo(), nunca de
        ``dt``); el parametro se mantiene reservado sin usar. Se llama una
        vez por cuadro desde update(), ANTES de _pin_camera_to_arena (el
        orden entre las dos no importa -- no comparten estado -- pero
        mantenerlo estable facilita leer el metodo update() de arriba a
        abajo).

        NO cablea clima (B-046, REGISTRO-DE-BUGS.md): la Tarea 8 intentó
        primero cablear ``tramo.clima`` a ``WorldSimulation``/
        ``WeatherSystem`` a través de la puerta del motor
        (``_cambiar_clima``, simulacion.py:264) y se retiró por completo tras
        un hallazgo de MOTOR en la revisión de spec 2026-08-25 -- ver el
        docstring de ``_dibujar_velo_de_niebla`` (más abajo, wireado desde
        ``dibujar_ui``) para el mecanismo real que sustituye esa idea: un
        velo puramente ESPACIAL (perfil de alfa según ``player.rect.centerx``
        vía ``efectos_venado.alfa_de_niebla``), que no depende de
        ``WorldSimulation.update()`` ni de ninguna interpolación del motor.
        El clima del motor (``self._simulacion``/``self._weather``) queda
        ``"clear"`` fijo durante toda la pelea (el valor por defecto de la
        estación sin ``climate``/``season`` en el TMX, sin que ningún código
        de esta escena lo cambie nunca) -- el hallazgo de la Tarea 8 sobre
        ese default sigue siendo válido y documentado (ver el reporte de la
        Tarea 8 en la sesión), solo que ahora no hay ninguna llamada a
        ``_cambiar_clima`` en absoluto."""
        if self._player is None:
            return
        x = float(self._player.rect.centerx)
        tramo = tramo_en(x)
        if tramo is not self._tramo_actual:
            anterior = self._tramo_actual
            self._tramo_grading_previo = anterior.matriz_grading if anterior else None
            self._tramo_tinte_previo = anterior.tinte if anterior else None
            self._tramo_vineta_previa = anterior.vineta if anterior else tramo.vineta
            self._tramo_actual = tramo
        t = avance_en_tramo(x)

        # Gradacion de color: interpola de la matriz del tramo anterior a la
        # de este, con ease-in-out (ver tramos_venado.interpolar_grading).
        if self._tramo_grading_previo is None and tramo.matriz_grading is None:
            self._post_processing.clear_color_grading()
        else:
            self._post_processing.set_color_grading(
                *interpolar_grading(self._tramo_grading_previo, tramo.matriz_grading, t))

        # Tinte de color plano -- sistema aparte de la gradacion en
        # PostProcessing (mismo patron que stage4_1._actualizar_gradacion),
        # con su propio alfa interpolado.
        alfa_previa = self._tramo_tinte_previo[1] if self._tramo_tinte_previo is not None else 0.0
        if tramo.tinte is not None:
            color, alfa_objetivo = tramo.tinte
            alfa = alfa_previa + (alfa_objetivo - alfa_previa) * ease_in_out_quad(t)
        else:
            color = self._tramo_tinte_previo[0] if self._tramo_tinte_previo is not None else (0, 0, 0)
            alfa = alfa_previa * (1.0 - ease_in_out_quad(t))
        if alfa <= 0.001:
            self._post_processing.clear_tint()
        else:
            self._post_processing.set_tint(color, alfa)

        # Vineta: respira entre el valor del tramo anterior y el de este.
        self._post_processing.set_vignette(
            self._tramo_vineta_previa + (tramo.vineta - self._tramo_vineta_previa) * ease_in_out_quad(t))

    # B-046 (REGISTRO-DE-BUGS.md, revisión de spec T8, 2026-08-25): esta
    # escena tuvo aquí un método ``_cambiar_clima`` propio que sombreaba la
    # puerta del motor (``SimulacionDeEscenario._cambiar_clima``,
    # simulacion.py:264) para poder pasarle el parámetro ``inmediato`` de
    # ``WorldSimulation.set_clima`` (simulation.py:261) que esa puerta omite
    # -- RETIRADO por completo (nunca llegaron a existir dos versiones en
    # producción, solo en esta sesión): dos defectos de MOTOR invalidan la
    # premisa completa de usar clima runtime en esta escena. (1)
    # ``ActualizacionesDeEscenario._update_vfx`` (stage_parts/
    # actualizaciones.py:148-150) envuelve TANTO
    # ``self._simulacion.update(dt)`` (el método que hace avanzar
    # ``WorldSimulation._avanzar_clima``, la interpolación de 6s) COMO
    # ``self._aplicar_hora()`` (el que reaplica luz/tinte/clima/audio cada
    # cuadro) dentro de un ``if not self._reloj.congelado:`` -- y este boss
    # declara ``day_length=0`` en el TMX (exigido por el doc 86 §3.2 para
    # jefes de Zona 1, ya en el TMX desde H-18), así que
    # ``self._reloj.congelado`` es PERMANENTEMENTE ``True`` en esta escena:
    # ese bloque entero NUNCA corre por cuadro. Una transición "suave"
    # (``inmediato=False``) jamás habría avanzado ni un solo paso -- el
    # nombre del clima cambiaría al instante pero los valores de humedad/
    # visibilidad quedarían congelados en los del clima ANTERIOR para
    # siempre. (2) Incluso si el reloj no estuviera congelado,
    # ``WeatherSystem.set_climate``/``_set_climate_params``
    # (weather_system.py:56-86) escribe ``_overlay_alpha`` de forma
    # SÍNCRONA e INSTANTÁNEA desde ``CLIMATE_PARAMS`` -- no existe ninguna
    # interpolación en ``WeatherSystem`` para ese campo, y ``draw()``
    # (weather_system.py:162-174) solo cachea-y-pinta ese valor ya fijo. La
    # capa visual de niebla que el jugador REALMENTE ve siempre aparece de
    # golpe en un cuadro, sin importar ``inmediato`` -- la distinción
    # "suave vs instantáneo" que esta tarea intentó cablear era invisible en
    # pantalla incluso antes de toparse con (1). Solución (ver
    # ``_dibujar_velo_de_niebla`` más abajo, wireado desde ``dibujar_ui``):
    # velo de niebla puramente ESPACIAL, con rampas propias que dependen
    # solo de ``player.rect.centerx`` -- suave en ambas direcciones por
    # construcción, sin depender de ``WorldSimulation.update()`` ni de
    # ninguna interpolación del motor. El clima real del motor
    # (``self._simulacion``/``self._weather``) queda ``"clear"`` fijo toda
    # la pelea (default de estación sin ``climate``/``season`` en el TMX) y
    # esta escena nunca lo cambia.

    def _actualizar_presencias(self, dt: float) -> None:
        """Fauna decorativa del corredor (Tarea 4): solo LEE la posición del
        jugador para saber en qué tramo filtrar -- nunca la escribe, y
        GestorDePresencias.actualizar() ni siquiera recibe el jugador como
        argumento (ver su firma en presencias_venado.py y el candado
        test_gestor_actualizar_no_recibe_ni_toca_al_jugador). Se llama una
        vez por cuadro desde update(), mismo punto de enganche que
        _actualizar_tramo_narrativo."""
        if self._player is None:
            return
        x = float(self._player.rect.centerx)
        self._gestor_presencias.tramo_actual = tramo_en(x).numero
        self._gestor_presencias.actualizar(dt)

    def _actualizar_silencio_y_shake_de_arena(self, x: float) -> None:
        """Silencio súbito + shake único + eco del gazebo -- Tarea 6. Patrón
        de stage4_1.py:1069-1092 (``_actualizar_silencio_y_shake``, disparado
        una sola vez por visita), gateado al cruce de un umbral puntual (no
        una fase completa con duración propia).

        Cableado a los datos (revisión de spec T6, 2026-08-25): consulta
        ``tramo_en(x).eventos`` en vez de comparar a mano contra
        ``ARENA_X0``. Las flags ``"shake_al_entrar"``/``"eco"`` que
        ``tramos_venado.TABLA[3]`` (Acto 4 "Lo sagrado") declara ahora SÍ son
        datos que este método consume, no solo documentación de intención --
        a diferencia de ``EventoSombraQueCruza``, que sigue hardcodeando
        ``SOMBRA_X0``/``SOMBRA_X1`` (presencias_venado.py) porque su ventana
        [2200, 2480) es una SUB-porción del Acto 3, no el tramo completo (ver
        el docstring corregido de ``Tramo.eventos`` en tramos_venado.py, que
        distingue ambos casos). Cero cambio de comportamiento: ``TABLA[3].
        x_inicio == ARENA_X0`` exactamente y ningún otro tramo declara estas
        flags, así que el rango de ``x`` que dispara cada rama es idéntico al
        de antes (``x >= ARENA_X0``).

        B-045 (REGISTRO-DE-BUGS.md, revisión de spec T6, 2026-08-25) -- DOS
        ajustes, no solo uno, hicieron falta para que el candado H-17 dejara
        de romperse de forma intermitente:

        (1) ``direccion=(0.0, 1.0)`` (vertical, mismo patrón que el STOMP del
        propio jefe, ``boss_venado.py:1245``: ``self.efectos.sacudir(4.0,
        0.2, (0.0, 1.0))``), NUNCA isotrópico (``direccion=None``, el valor
        por defecto). Sin dirección, ``apply_shake`` cae en la rama
        isotrópica de ``camera.py:409-411``: magnitud PLENA en X e Y por
        igual, sin ningún eje libre de ruido.

        (2) ``duration=ARENA_SHAKE_DURATION`` (0.2, no 0.4, el valor
        original del Paso 3 del plan; extraída a constante junto a
        ``ARENA_SETTLE_DURATION`` en la revisión de calidad de esta tarea)
        -- esto SOLO se descubrió corriendo la verificación anti-intermitencia
        con el fix (1) ya aplicado: seguía rompiendo, con una desviación
        menor (~0.06px) pero real. Causa raíz completa, verificada leyendo
        ``_aplicar_sacudida`` (camera.py:402-445) línea por línea: incluso
        CON dirección, la componente perpendicular/cruzada (``cruz``, líneas
        428-430) NO lleva la envolvente ``onda`` que sí decae a cero -- es
        ruido de magnitud ``amplitude * 0.25`` (``_SACUDIDA_CRUZADA``) con un
        ``self._rng.uniform(-1, 1)`` FRESCO cada cuadro, constante en
        magnitud durante toda la duración del shake y sólo cae a exactamente
        cero cuando ``_shake_timer`` llega a 0. Con ``direccion=(0.0, 1.0)``
        esa componente cruzada cae exactamente en X. Mientras
        ``_pin_camera_to_arena`` sigue en su ventana de ease (``_arena_ease_
        elapsed < ARENA_SETTLE_DURATION`` == 0.3 s), sobrescribe
        ``offset.x`` cada cuadro sin condición, así que ese ruido no se ve
        NUNCA -- pero ``_aplicar_sacudida`` sigue haciendo ``self.offset -=
        self._shake_offset`` (camera.py:404) cada cuadro asumiendo que el
        ``_shake_offset`` del cuadro anterior seguía reflejado en
        ``self.offset``, cosa que el ``pin`` acaba de invalidar con su
        sobrescritura directa. Mientras el ``pin`` sigue sobrescribiendo cada
        cuadro esta desincronización es invisible (se vuelve a sobrescribir
        de inmediato); se vuelve PERMANENTE en el primer cuadro en que el
        ``pin`` DEJA de escribir ``offset.x`` (``_arena_ease_elapsed >=
        ARENA_SETTLE_DURATION``, el ``if`` de ``_pin_camera_to_arena`` ya no
        entra) si el shake TODAVÍA sigue activo en ese cuadro -- el
        ``_aplicar_sacudida`` de ese cuadro resta un ``_shake_offset``
        obsoleto (que el ``pin`` ya había descartado) y suma uno nuevo,
        dejando un sesgo aditivo que NUNCA se corrige después (una vez el
        timer llega a 0, ``_shake_offset`` se congela en su último valor
        erróneo -- no hay ningún cuadro posterior que vuelva a escribir
        ``offset.x`` mientras la cámara siga bloqueada en la arena). Con
        ``duration=0.2`` (12 cuadros a 60 fps) el shake termina con margen de
        varios cuadros antes de que la ventana de ease (18 cuadros) se
        cierre -- el shake ya está en (0.0, 0.0) cuando el ``pin`` deja de
        escribir, así que no hay nada obsoleto que restar y el ``offset.x``
        final es el valor EXACTO (no un lerp con error de punto flotante)
        que el ``pin`` escribió en su último cuadro de ease
        (``_pin_camera_to_arena``: ``if t >= 1.0: self._camera.offset.x =
        target_x``). Mismo orden de magnitud que STOMP (0.2s)/CHARGE
        (0.15s) -- ningún shake de este boss se acerca a los 0.3s del ease,
        así que este ajuste tampoco cambia el "peso" percibido del golpe
        frente a los demás.

        Verificado con `pytest playtest/tests/test_harness.py -q` ×5 +
        `pytest playtest -q` ×3, todas verdes (ver REGISTRO-DE-BUGS.md B-045
        para las salidas exactas) -- una corrida sola no basta para un flaky
        de este tipo (la componente cruzada es ruido fresco cada cuadro, así
        que el desenlace exacto depende del cuadro concreto en que ocurre
        cada cruce).

        T8 (nota de acople RESUELTA -- REDISEÑO tras hallazgo de MOTOR,
        revisión de spec T8, 2026-08-25): el primer cierre de esta nota
        (misma fecha, misma sesión) proponía que ``_actualizar_tramo_
        narrativo`` cortara el clima del motor EN SECO al cruzar a
        ``tramo.numero == 4`` para golpear en el mismo cuadro que el
        shake/eco de este método. Esa vía completa fue RETIRADA: la revisión
        de spec encontró que ``WorldSimulation``/``WeatherSystem`` no pueden
        transicionar en absoluto en esta escena (reloj congelado por
        ``day_length=0``, gate en ``stage_parts/actualizaciones.py:148-150``)
        y que el overlay de ``WeatherSystem`` tampoco interpola nunca (salta
        instantáneo siempre, ``weather_system.py:56-86/162-174``) -- ver
        B-046 en REGISTRO-DE-BUGS.md y el comentario que reemplazó al método
        ``_cambiar_clima`` retirado (donde vivía antes, justo debajo de
        ``_actualizar_tramo_narrativo``). El corte en seco de la niebla al
        entrar a la arena ahora lo da la GEOMETRÍA propia del velo espacial
        (``efectos_venado.alfa_de_niebla``, wireado en ``dibujar_ui`` vía
        ``_dibujar_velo_de_niebla``): su rampa de salida ya llega a alfa=0
        exactamente en ``x=ARENA_X0`` (``TABLA[3].x_inicio``), así que el
        jugador ve la niebla desvanecerse justo al cruzar el umbral -- sin
        que este método ni ``_actualizar_tramo_narrativo`` necesiten
        coordinar nada entre sí. El shake/eco de este método siguen siendo
        el "golpe" dramático puntual del cruce (spec §"Silencio súbito");
        el velo aporta la lectura visual continua de "la niebla se disipa al
        acercarse al suelo sagrado" (ver el docstring de
        ``efectos_venado.alfa_de_niebla`` para la narrativa completa) -- dos
        piezas independientes que coinciden en el mismo tramo de mapa por
        diseño de datos (``TABLA``), no por ninguna llamada cruzada entre
        métodos.

        No hay "corte de ambiente" que apagar aparte del eco EN ESTE método:
        a diferencia de ``stage4_1._actualizar_silencio_y_shake`` (que sí
        llama ``_cambiar_clima("clear")``/``audio.stop_ambient()`` porque
        esa escena tiene un ciclo día/noche real -- ``day_length > 0`` -- y
        por tanto un ``WorldSimulation``/``WeatherSystem`` que sí avanza),
        esta escena NUNCA cambia el clima del motor (B-046: queda
        ``"clear"`` fijo toda la pelea). El "silencio súbito" de ESTE método
        sigue siendo, como siempre, el cambio de mezcla que trae
        ``activar_eco(True)`` (bus de reverberación del gazebo, ver
        audio_manager.py:173-191) más el golpe visual del shake -- ningún
        sistema de clima real compite con eso, ni falta que haga.

        Dos memorias de estado independientes, con semánticas distintas:
        ``_shake_de_arena_disparado`` es un latch de una sola vez por
        episodio (igual que ``EventoSombraQueCruza._disparado``, H-18);
        ``_eco_activo`` en cambio sigue la posición del jugador cuadro a
        cuadro (enciende al entrar, apaga al salir, se puede reencender si
        se reentra) -- el gazebo suena distinto DENTRO, no "la primera vez
        que se entró"."""
        eventos = tramo_en(x).eventos
        audio = getattr(getattr(self, "context", None), "audio", None)
        if "shake_al_entrar" in eventos and not self._shake_de_arena_disparado:
            self._shake_de_arena_disparado = True
            if self._camera is not None:
                # B-045: direccion vertical (NUNCA isotropico) +
                # ARENA_SHAKE_DURATION (DEBE quedar < ARENA_SETTLE_DURATION,
                # no los 0.4 originales del plan) -- ver el docstring de
                # arriba para el mecanismo completo de desincronizacion con
                # _pin_camera_to_arena.
                self._camera.apply_shake(amplitude=6.0, duration=ARENA_SHAKE_DURATION,
                                         direccion=(0.0, 1.0))
        if "eco" in eventos and not self._eco_activo:
            self._eco_activo = True
            if audio is not None:
                audio.activar_eco(True)
        elif "eco" not in eventos and self._eco_activo:
            self._eco_activo = False
            if audio is not None:
                audio.activar_eco(False)

    def _reproducir_revelacion(self) -> None:
        """El susurro/bramido que aparece cuando el jugador se queda quieto
        -- separado en su propio método (en vez de inline en
        ``_actualizar_quietud_revela``) para poder sustituirlo por un stub en
        tests (ver ``test_quietud_revela_con_cooldown_anti_farmeo`` en
        ``test_boss_scene.py``), mismo motivo por el que
        ``EventoSombraQueCruza`` recibe su ``reproducir_sfx`` como callback
        inyectado en vez de llamar a ``_play_sfx_spatial`` directo.

        Reutiliza el mismo SFX que ``_sombra_que_cruza``
        (``sfx_bosses_venado_bramido_lejano``, ya generado por
        ``tools/generar_sfx_bramido.py`` -- no hace falta un asset nuevo):
        ambos son el mismo bramido lejano del venado, uno disparado por
        cruzar un umbral espacial y este por quedarse quieto. Volumen más
        bajo (0.35 contra 0.8) porque esta revelación puede repetirse cada
        ``COOLDOWN_REVELACION`` segundos durante toda la pelea, mientras que
        la de la sombra es un aviso único por episodio."""
        if self._player is None:
            return
        self._play_sfx_spatial(
            "sfx_bosses_venado_bramido_lejano", float(self._player.rect.centerx), volume=0.35)

    def _actualizar_quietud_revela(self, dt: float) -> None:
        """Tarea 7 del plan de peregrinación: "detenerse también es jugar"
        -- si el jugador lleva ``QUIETUD_PARA_REVELAR`` segundos sin moverse
        (medido por ``self._atencion``, alimentado en ``update()`` justo
        después de ``super().update(dt)``, antes de esta llamada), se
        dispara una revelación (``_reproducir_revelacion``) y se arma un
        enfriamiento de ``COOLDOWN_REVELACION`` segundos.

        El cooldown es imprescindible, no cosmético: ``Atencion.quietud`` es
        una racha que sólo crece mientras el jugador no se mueva (ver
        ``atencion.py``), así que sin él ``esta_quieto()`` seguiría
        devolviendo ``True`` en absolutamente todos los cuadros siguientes y
        esto dispararía la revelación 60 veces por segundo -- explotable con
        sólo plantarse.

        Usa ``getattr`` (no un ``self._atencion`` directo) para que degrade
        a no-op en los dobles de prueba de ``BossVenadoScene.__new__(...)``
        sin ``__init__`` real que este módulo cablea a mano (ver
        ``_bare_scene_with_boss``) -- mismo estilo defensivo que ya usan
        ``_pin_camera_to_arena``/``_update_relic_banner`` más arriba, y por
        el mismo motivo: ``update()`` llama a este método sin condición.

        Acotada a ``player_x < SOMBRA_X0`` (revisión de calidad, 2026-08-25):
        esta revelación reutiliza el mismo bramido que
        ``EventoSombraQueCruza`` (ver ``_reproducir_revelacion``), así que
        dejarla sonar sin acotar en ``[SOMBRA_X0, ∞)`` competiría con el
        aviso ÚNICO de esa clase (Tarea 5, ventana ``[SOMBRA_X0,
        SOMBRA_X1)``) y seguiría sonando dentro de la arena, donde el jefe
        ya está revelado y en combate -- ambas cosas rompen la lectura de
        "esto anuncia algo que todavía no se vio". Por debajo de
        ``SOMBRA_X0`` (Actos 1-2) la revelación sigue funcionando igual que
        antes: ahí es exactamente donde tiene sentido premiar la quietud."""
        if getattr(self, "_atencion", None) is None:
            return
        if self._player is not None and float(self._player.rect.centerx) >= SOMBRA_X0:
            return
        if self._cooldown_revelacion > 0.0:
            self._cooldown_revelacion = max(0.0, self._cooldown_revelacion - dt)
            return
        if self._atencion.esta_quieto(QUIETUD_PARA_REVELAR):
            self._reproducir_revelacion()
            self._cooldown_revelacion = COOLDOWN_REVELACION

    def update(self, dt: float) -> None:
        in_arena = False
        if self._stage_data is not None and self._player is not None:
            in_arena = float(self._player.rect.centerx) >= ARENA_X0
            self._stage_data.camera_locks = (
                self._original_camera_locks if in_arena else [])
        super().update(dt)
        if self._player is not None:   # Tarea 7: se mide antes que nada (mismo orden que stage4_1)
            self._atencion.observar(self._player, dt)
        self._actualizar_tramo_narrativo(dt)   # Tarea 2: grading/tinte/vineta por avance
        self._actualizar_presencias(dt)   # Tarea 4: fauna decorativa dano 0
        if getattr(self, "_gestor_luciernagas", None) is not None:
            # Tarea 12: reloj propio del parpadeo, nunca wall-clock. getattr
            # (no un atributo directo) por el mismo motivo defensivo que
            # _pin_camera_to_arena/_update_relic_banner (ver sus docstrings):
            # degrada a no-op en los dobles de prueba de
            # BossVenadoScene.__new__(...) sin __init__ real que
            # test_boss_scene.py::_bare_scene_with_boss cablea a mano.
            self._tiempo_luciernagas += dt
        if self._player is not None:   # Tarea 5: aviso unico de la sombra que cruza
            self._sombra_que_cruza.actualizar(float(self._player.rect.centerx))
        if self._player is not None:   # Tarea 6: silencio subito + shake unico + eco
            self._actualizar_silencio_y_shake_de_arena(float(self._player.rect.centerx))
        # Tarea 7: al final, no pegado a observar() -- solo LEE la quietud ya medida este cuadro.
        self._actualizar_quietud_revela(dt)   # quietud revela, con cooldown anti-farmeo y acote a SOMBRA_X0
        # H-17 (ver docstring del módulo): debe correr DESPUÉS de
        # super().update(dt) (así tiene la última palabra sobre camera.offset
        # en este cuadro) -- el motor se encarga de centrar el fondo de
        # pyscroll sobre ese offset ya fijado en su propio paso de dibujo
        # (ver la sección H-10 (RETIRADA) del docstring del módulo), así que
        # ya no hace falta un tercer paso aquí en update().
        self._pin_camera_to_arena(dt, in_arena)
        self._update_relic_banner(dt)   # adopción V3, D10

    def dibujar_fondo(self, surface: pygame.Surface,
                      offset: pygame.Vector2) -> None:
        """Presencias decorativas del corredor (Tarea 4), DETRÁS del mapa de
        baldosas -- gancho ``dibujar_fondo`` (AUD-162, ver su docstring en
        ``StageScene``), mismo patrón real que ``Stage4_1.dibujar_fondo`` ->
        ``_dibujar_presencias_errantes`` (stage4_1.py:1611-1620), que es la
        referencia que la Tarea 4 del plan cita como "patrón exacto".

        CORRECCIÓN frente al Paso 5 tal como está escrito en el plan: el
        borrador ahí sobrescribía ``dibujar_mundo`` y pintaba las presencias
        ANTES de llamar a ``super().dibujar_mundo(surface)`` para que
        quedaran detrás de jefe/jugador. Eso no funciona: ``dibujar_mundo``
        delega en ``self._drawing.draw(...)``
        (``framework/stage/drawing_system.py::DrawingSystem.draw``), y esa
        función hace ``surface.fill(settings.BG_COLOR)`` como su primerísimo
        paso -- cualquier blit hecho antes de esa llamada se borra sin dejar
        rastro. ``dibujar_fondo`` es justo el gancho que ``AUD-162`` añadió
        para este caso exacto ("no se podía pintar detrás, solo encima"): se
        invoca desde dentro de ``DrawingSystem.draw`` -- después de
        ``surface.fill`` y del parallax, antes de las capas del TMX -- así
        que lo que se pinte aquí sí sobrevive y sí queda detrás del mapa y
        de las entidades. No es un ``draw()`` nuevo (precedente H-28): es
        una mitad más del pipeline real que ``DibujoDeEscenario`` ya
        despacha por contrato (ver su docstring: "`dibujar_fondo` y el
        contexto").

        Se llama solo cuando ``self._stage_data``/``self._player`` no son
        None (lo garantiza ``dibujar_mundo``, que corta antes de invocar a
        ``self._drawing.draw``), así que a diferencia del borrador del plan
        no hace falta comprobar ``self._player`` aquí de nuevo."""
        for p in PRESENCIAS:
            visible = self._gestor_presencias.visibles.get(p.id, 0.0)
            if visible <= 0.0:
                continue
            columna = columna_de_patrullaje(p, self._gestor_presencias.tiempo_total)
            x = int(columna - offset.x)
            if x < -60 or x > settings.INTERNAL_WIDTH + 60:
                continue
            y = int(fila_de_presencia(p) - offset.y)
            ancho = int(p.alto * 0.5)
            silueta = pygame.Surface((ancho, p.alto), pygame.SRCALPHA)
            pygame.draw.ellipse(silueta, (*p.color, p.alfa), silueta.get_rect())
            surface.blit(silueta, (x, y))

    def dibujar_mundo(self, surface: pygame.Surface) -> None:
        """Delega el mundo entero en la implementación heredada
        (``DibujoDeEscenario.dibujar_mundo``, ``dibujo.py:95-130`` -- mapa,
        entidades, niebla, agua y luz, en ese orden) y, DESPUÉS, muestrea el
        histograma de luminancia para la Unidad VII (Tarea 12 del plan de
        peregrinación, "La Hora de las Luciérnagas" -- ver
        ``luciernagas_venado.py``).

        Esta escena NO tenía override de ``dibujar_mundo`` antes de esta
        tarea -- ``dibujar_fondo`` (arriba) es un gancho DISTINTO (se invoca
        DENTRO de ``self._drawing.draw()``, antes de que las capas del TMX se
        pinten, precisamente para poder pintar DETRÁS del mapa -- ver su
        docstring). El borrador original del Paso 5 del plan asumía que la
        Tarea 4 ya había dejado un override de ``dibujar_mundo`` con las
        presencias decorativas y que este paso solo le añadía dos líneas al
        final; en la implementación real, la Tarea 4 se topó con que
        ``dibujar_mundo`` hace ``surface.fill(BG_COLOR)`` como primer paso
        (borraría cualquier blit anterior) y usó ``dibujar_fondo`` en su
        lugar (ver el docstring de ese método, "CORRECCIÓN frente al Paso 5
        tal como está escrito en el plan"). Este override es, por tanto,
        NUEVO de esta tarea, no una ampliación de uno ya existente -- pero
        cumple exactamente la misma intención textual del plan: muestrear
        "DESPUÉS de ``super().dibujar_mundo()``" con la escena "ya
        compuesta, luz incluida".

        SOLO el muestreo vive aquí -- el DIBUJO de las luciérnagas vive en
        ``dibujar_ui`` (ver ``_dibujar_luciernagas`` y el docstring de ese
        método), no en este mismo método como sugiere el fraseo literal del
        plan ("las luciérnagas se pintan encima de esa luz, antes de que
        dibujar_ui() pinte la UI"). Motivo (hallazgo de esta tarea, no
        documentado por el plan): ``App`` SIEMPRE llama ``dibujar_mundo``
        con ``self.internal_surface`` en las dos rutas del motor (app.py
        584-588), pero bajo la ruta de GPU esa superficie NO lleva la luz
        todavía en este punto -- el multiplicador de luz se calcula aparte
        (``self._lighting.render_map(...)``, ``dibujo.py:126-127``) y
        ``App`` lo sube a la tarjeta DESPUÉS, fuera del control de esta
        escena (AUD-343: "aplicarlo aquí [dibujar_mundo] y de nuevo en el
        sombreador lo multiplicaría dos veces"). Cualquier píxel que este
        método escribiera en ``surface`` tras ``super().dibujar_mundo()``
        seguiría, por tanto, sujeto a ese multiplicador de luz posterior en
        la ruta de GPU -- el efecto contrario al de "luces que brillan en la
        oscuridad" que unas luciérnagas aditivas deben tener. La ruta de
        software SÍ aplica la luz dentro de ``dibujar_mundo``
        (``dibujo.py:128-129``: ``self._lighting.render(surface, ...)``), así
        que en esa ruta muestrear aquí es exactamente correcto y sin ningún
        matiz -- la superficie ya está completamente compuesta. La lectura
        del histograma en la ruta de GPU queda, pues, tomada sobre la
        composición SIN el multiplicador de luz de la tarjeta (una señal
        algo menos precisa que en software, pero la única superficie de
        contenido real disponible dentro de la zona editable de esta
        escena -- ``dibujar_ui`` bajo GPU recibe una superficie de overlay
        vacía, ver el docstring de ``_dibujar_luciernagas`` -- así que
        muestrear ahí sería estrictamente peor, no solo distinto)."""
        super().dibujar_mundo(surface)
        # getattr (no un atributo directo) por el mismo motivo defensivo que
        # _pin_camera_to_arena/_update_relic_banner: degrada a no-op en los
        # dobles de prueba sin __init__ real (BossVenadoScene.__new__(...)).
        gestor = getattr(self, "_gestor_luciernagas", None)
        if gestor is not None:
            gestor.actualizar_desde_superficie(surface)

    def dibujar_ui(self, surface: pygame.Surface) -> None:
        """La mitad de interfaz de esta escena -- velo de niebla del
        corredor, overlays del jefe, halo del jugador e icono de la
        Reliquia, todos DESPUÉS de la luz.

        B-046 (REGISTRO-DE-BUGS.md, Tarea 8 del nivel "Peregrinación al
        Venado"): ``_dibujar_velo_de_niebla`` se pinta EN PRIMER LUGAR, antes
        incluso de ``super().dibujar_ui(surface)`` -- mismo precedente H-28
        que el resto de este método (el único punto de enganche que el
        motor SÍ despacha de verdad es ``dibujar_mundo``/``dibujar_ui``, no
        ``draw()``), aplicado aquí con el ORDEN invertido a propósito: el
        velo necesita cubrir el mundo y las entidades (ya pintados en el
        pase de ``dibujar_mundo``, anterior a este método) pero quedar POR
        DEBAJO de todo lo demás que pinta ``dibujar_ui`` -- el HUD que
        ``super()`` dibuja, y los cinco overlays de más abajo (telegraphs,
        halo, icono de reliquia) -- ninguno de los cuales debería leerse
        "a través" de niebla. Pintarlo primero logra exactamente eso: un
        blit translúcido de pantalla completa que cae encima del mundo pero
        debajo de cualquier otra cosa que este método pinte después.

        H-28/B-032 (ver la sección homónima del docstring del módulo): esta
        escena solía sobrescribir ``draw()`` en vez de ``dibujar_ui()``.
        ``App._draw()`` nunca llama a ``escena.draw()`` cuando la escena
        expone ``dibujar_mundo``/``dibujar_ui`` -- que ``StageScene`` expone
        siempre (AUD-343, ver app.py 556-723) -- así que todo este bloque
        era código MUERTO en el juego real. El fix es este override: mismo
        bloque, mismo orden interno (telegraphs del jefe -> anuncio del
        enjambre -> teletransporte -> halo del jugador -> icono de
        reliquia), sólo el punto de enganche cambió.

        La garantía de "después de la luz" que Cambio 3/5 necesitan (doc 86
        §2.4 regla 5) la da ``dibujar_ui`` por construcción, en las DOS
        tuberías del motor: en la de software, ``App._draw()`` llama
        ``dibujar_mundo`` (mundo+luz+post, ``dibujo.py`` líneas 82-117) y
        LUEGO ``dibujar_ui`` sobre la misma superficie (app.py 704-718); en
        la de GPU, ``dibujar_ui`` pinta en una superficie aparte que
        ``App``/``GLRenderer`` componen DESPUÉS de toda la cadena de pasadas
        (``dibujo.py`` líneas 119-127, app.py 687-703) -- en ambas, esta
        mitad corre después de la luz por definición del contrato de la
        escena, no por un truco de orden de llamada como antes (``super().
        draw(surface)`` seguido de este bloque en el mismo método).
        ``super().dibujar_ui(surface)`` primero reproduce ese mismo orden
        relativo (el resto de la interfaz heredada -- trayectoria, HUD,
        minimapa, subtítulos -- antes que los overlays propios de este
        boss), así que pintar aquí, en espacio de pantalla, con el offset
        de cámara actual, sigue cayendo encima de todo lo demás. Antes del
        Cambio 3, ``BossVenado.draw()`` pintaba los avisos en el pase de
        entidades (dentro de ``dibujar_mundo``), donde el multiplicador de
        luz nocturna los dejaba a ~40% de su brillo real -- ver el
        comentario retirado de ``boss_venado.py::draw()``. Los overlays del
        jefe van ANTES del halo/icono de reliquia para que esos dos, que son
        notas para el jugador y no geometría del mundo, queden encima si
        llegaran a solaparse.

        Precedente H-27: como ``DibujoDeEscenario.draw`` (heredado, no
        sobrescrito por esta clase) es sólo ``dibujar_mundo(surface);
        dibujar_ui(surface)``, cualquier prueba que llame ``scene.
        draw(surface)`` directo (``test_telegraphs_sobre_la_luz.py``,
        ``test_teletransporte_ux.py``) sigue ejerciendo este mismo código
        por herencia, sin cambios de lógica en esas pruebas. El candado que
        SÍ distingue "se llamó el método" de "el motor lo despachó de
        verdad" vive en ``tests/test_despacho_real_overlays.py`` (llama
        ``App._draw()``, nunca ``scene.draw()``).

        Riesgo 2 del dictamen doc-guardian (composición por alfa de la ruta
        de GPU): sólo el halo necesitó un cambio de blend
        (``BLEND_RGB_ADD`` -> ``BLEND_RGBA_ADD`` + alfa cocinado en
        ``_build_player_halo``, ver su docstring) porque es el único de
        estos cinco overlays que se pinta con un blend ADITIVO puro. Los
        otros cuatro ya escriben alfa correctamente sin tocarlos:
        ``_draw_telegraphs``/``_draw_anuncio_del_enjambre``/
        ``_draw_teletransporte`` (boss_venado.py) usan ``pygame.draw.*``
        directo -- una escritura de píxel, no un blend, que fija el alfa a
        255 en cada píxel dibujado cuando la superficie destino tiene canal
        alfa -- y ``_draw_relic_icon`` usa ``surface.blit`` SIN flags
        especiales, el blit estándar de pygame, que sí compone (y por tanto
        sí escribe) el alfa por píxel del origen sobre un destino con
        ``SRCALPHA``. ``BLEND_RGB_ADD``/``BLEND_RGBA_ADD`` son la única
        pareja de flags de este archivo que trata el alfa como una banda
        más a sumar en vez de como peso de composición -- de ahí que sólo
        el halo necesitara el ajuste. El candado que vigila que esto se
        sostenga es ``test_despacho_real_overlays.py::
        test_overlays_sobreviven_la_composicion_por_alfa_de_la_ruta_gl``.

        Tarea 12 (Unidad VII, "La Hora de las Luciérnagas"): ``_dibujar_luciernagas``
        se llama justo DESPUÉS del velo de niebla y ANTES de
        ``super().dibujar_ui(surface)`` -- encima del mundo/luz ya compuestos
        (``dibujar_mundo`` acaba de correr, ver su docstring para el
        muestreo del histograma que decide CUÁNTAS luciérnagas dibujar aquí),
        por encima de la niebla (para que se lean como luces que brillan A
        TRAVÉS de ella, no tapadas por ella) y por debajo del HUD/telegraphs/
        halo/icono de reliquia que pinta el resto de este método (son
        ambiente del mundo, no notas de interfaz). Deliberadamente NO se
        dibujan dentro de ``dibujar_mundo`` (donde el plan las colocaba en su
        fraseo literal) -- ver la sección correspondiente del docstring de
        ``dibujar_mundo`` para por qué: bajo la ruta de GPU cualquier píxel
        escrito ahí después de ``super().dibujar_mundo()`` todavía se
        multiplica por el mapa de luz de la tarjeta (AUD-343), mientras que
        ``dibujar_ui`` se compone DESPUÉS de esa multiplicación en las dos
        rutas del motor -- mismo mecanismo, y mismo motivo, que ya usa el
        halo del jugador un poco más abajo. ``_dibujar_luciernagas`` ya
        cocina el alfa de cada punto en su propio color (igual que el halo),
        así que sobrevive intacta la composición por alfa de la ruta de GPU
        sin necesitar ningún ajuste adicional -- ver el candado
        ``test_despacho_real_overlays.py::
        test_luciernagas_sobreviven_la_composicion_por_alfa_de_la_ruta_gl``."""
        self._dibujar_velo_de_niebla(surface)   # B-046: PRIMERO -- ver el párrafo de arriba
        self._dibujar_luciernagas(surface)   # Tarea 12: encima de la niebla, bajo el HUD
        super().dibujar_ui(surface)
        jefe = self._get_boss()
        if jefe is not None and jefe.is_alive and self._camera is not None:
            offset = self._camera.offset   # mismo mecanismo mundo->pantalla que usa el halo, ver abajo
            jefe._draw_telegraphs(surface, offset)
            jefe._draw_anuncio_del_enjambre(surface, offset)
            jefe._draw_teletransporte(surface, offset)
        if self._player is not None and self._camera is not None:
            # Fix del coordinador (Tarea 12, refuerzo REAL del halo): el
            # factor viene del MISMO histograma que decide cuántas
            # luciérnagas dibujar arriba -- ver
            # luciernagas_venado.GestorDeLuciernagas.factor_de_halo y el
            # docstring de _build_player_halo. getattr doble (no un atributo
            # directo) por el mismo motivo defensivo que el resto de este
            # método: degrada a FACTOR_HALO_MINIMO (comportamiento histórico)
            # en los dobles de prueba sin __init__ real.
            gestor = getattr(self, "_gestor_luciernagas", None)
            factor = getattr(gestor, "factor_de_halo", FACTOR_HALO_MINIMO) if gestor is not None else FACTOR_HALO_MINIMO
            if self._player_halo is None or factor != self._halo_factor_actual:
                # Reconstrucción cara (pygame.draw.circle × PLAYER_HALO_RADIUS)
                # solo cuando el factor CAMBIÓ -- factor_de_halo solo se
                # recalcula cada FRECUENCIA_DE_MUESTREO cuadros (0.5s), así
                # que esto nunca reconstruye cuadro a cuadro.
                self._player_halo = self._build_player_halo(factor)
                self._halo_factor_actual = factor
            offset = self._camera.offset
            top_left = (
                self._player.rect.centerx - offset.x - PLAYER_HALO_RADIUS,
                self._player.rect.centery - offset.y - PLAYER_HALO_RADIUS,
            )
            surface.blit(self._player_halo, top_left, special_flags=pygame.BLEND_RGBA_ADD)
        self._draw_relic_icon(surface)   # adopción V3, D10
