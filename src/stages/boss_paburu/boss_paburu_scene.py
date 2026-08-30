# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
"""Escena del Stage 4-2 — EL CEMENTERIO DE PABURU.

Un solo mapa de 4160 px que el jugador recorre con la cámara siguiéndolo.
Registra la entidad BossPaburu y los cuatro moradores en el StageLoader (API
pública del framework — sin tocar código del profesor).

LA FORMA DEL NIVEL
El jugador camina el camposanto peleando con murciélagos y guardianes de
máscara tilawa, cruza el pozo —nadando o por arriba—, y en algún punto pisa
uno de los cuatro círculos ceremoniales. En **uno** de ellos, sorteado al
cargar el nivel, el suelo se cierra y Paburu emerge. En los otros tres no pasa
nada. Cuál es cambia cada partida, y ninguno está al final.

Toda esa lógica vive en `cementerio.py`; acá sólo se conecta.

Además maneja la iluminación ceremonial: los cuatro cuencos de fuego que se
van encendiendo forma tras forma (GDD §3.2 — "el escenario se ilumina a medida
que Paburu se revela"). Mientras se recorre el cementerio los cuencos están
apagados: son del círculo, no del camino.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.input.action_map import Action
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.interactable_system import EVENTO_DISPARADOR
from src.framework.stage.stage_loader import StageLoader
from src.framework.vfx.lighting import LightSource
from src.stages.boss_paburu import moradores  # noqa: F401  (registra especies)
from src.stages.boss_paburu.boss_paburu import FORM_MASK, FORM_SPIRIT, BossPaburu
from src.stages.boss_paburu.cementerio import (
    LUZ_CAMINO,
    LUZ_TRAMPA,
    SUPERFICIE,
    Cementerio,
)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


TMX = Path("assets/maps/boss_paburu/boss_paburu.tmx")

# Los cuencos de la catacumba, en el orden en que se encienden forma tras
# forma. Los desplazamientos X son relativos al borde izquierdo del interior y
# coinciden con `CAT_BRASEROS` de `tools/gen_paburu_tmx.py`, que es donde se
# dibuja el tile del cuenco; la Y es el pábilo, un tile por encima del suelo
# de la cámara. El orden no es de izquierda a derecha sino exterior→interior:
# la sala se enciende hacia el centro, donde está el jefe.
BRAZIER_OFFSETS = (48, 576, 144, 480)

# Fuego de ritual: naranja cálido contra el púrpura del cementerio.
BRAZIER_COLOR = (255, 176, 88)

# La arena arranca en penumbra y gana luz con cada forma (GDD §3.2).
# `LightSystem` MULTIPLICA la pantalla por este valor, así que 0.30 deja
# el escenario prácticamente negro.
#
# AUD-463 — ESTOS NÚMEROS NO SE APLICABAN, Y POR ESO «TODO ERA COLOR CACA».
#
# La historia larga, porque explica dos rondas de playtest: los valores
# estuvieron en (0.62, 0.72, 0.82, 0.93), se subieron a (0.80…1.00) mirando
# capturas —«a 0.62 el jugador se perdía dentro del muro»— y el jugador
# siguió viendo la sala plana y marrón. Los dos juicios eran correctos sobre
# lo mismo: la escena FIJABA su penumbra y `_aplicar_hora` (el reloj del
# mundo, AUD-362) la SOBRESCRIBÍA en el mismo fotograma con
# `max(MIN_AMBIENTE, _ambiente_base × factor_de_la_hora)`. La luz que se veía
# no salía de aquí; salía de un suelo de 0.45 y del factor de `dusk`.
#
# Y el marrón no era del arte: `start_hour = dusk` tiñe la imagen entera de
# (245, 170, 152) —el ocre del crepúsculo— por el color grading. El nivel
# nocturno del juego se estaba dibujando a las siete de la tarde.
#
# Ahora la sala manda sobre el reloj (`_aplicar_hora` abajo), el mapa declara
# `night` (tinte 170,185,238: azul lunar) y estos valores vuelven a ser lo que
# dicen ser. Se bajan en consecuencia: con el tinte frío y los braseros
# encendidos, 0.42 es penumbra legible y no oscuridad.
AMBIENT_BY_PHASE = (0.42, 0.50, 0.58, 0.68)


# AUD-151 — el tipo se registra al IMPORTAR el módulo, no dentro de un método.
#
# Estaba dentro de `__init__`, así que sólo existía cuando alguien construía la
# escena. Cualquier herramienta que abra el mapa sin ella —el validador, el
# calificador, el previsualizador, la curva de dificultad— se encontraba con
# «tipo desconocido: BossRey» y no podía medir el nivel.
#
# Es la misma familia que AUD-106: el motor y las herramientas del profesor
# tienen que ver el mismo mundo, o las herramientas castigan trabajo correcto.
# Registrar al importar cuesta una línea y hace que las cuatro rutas
# coincidan.
StageLoader.register_entity("BossPaburu", BossPaburu)


class BossPaburuScene(StageScene):
    STAGE_ID: str = "boss_paburu"
    STAGE_NAME: str = "4-2  EL GRAN SHAMAN PABURU"
    ZONE: int = 4

    def __init__(self, context: GameContext) -> None:
        self._braziers: list[LightSource] = []
        self._teclas_previas: dict[int, bool] = {}
        self._intro: Any | None = None
        self._intro_vista: bool = False
        self._guardianes: list = []
        self._presencia: float = 0.0
        # La ronda de los guardianes (DISENO §3.4): sus ecos en vuelo, el
        # reloj de cadencia de cada uno y el contador para el arnés de
        # pruebas. `_gua_turno` rota quién ataca para que la ronda cite a
        # los tres, no al que tenga el reloj más corto.
        self._ataques_guardianes: list = []
        # El vigilante del altar (#45): sus picadas van en lista propia y
        # no en `_ataques_guardianes` — aquella solo se actualiza con la
        # arena sellada, y el vigilante trabaja en la superficie.
        self._ecos_del_vigilante: list = []
        self._vigilante_cd = 0.0
        self._vigilante_avisado = False
        # AUD-497 — mientras dura el llamado de la Forma 4 los custodios
        # están en la sala; fuera de él, no. Es lo que hace del llamado un
        # MOMENTO y no un estado permanente.
        self._procesion_en_curso: bool = False
        self._gua_timers: list[float] = []
        self._gua_turno: int = 0
        self._gua_lanzados: int = 0
        self._farol: LightSource | None = None
        # El sorteo se hace acá, en el constructor, y no en `on_enter`: morir y
        # reaparecer vuelve a llamar a `on_enter`, y si el círculo se resorteara
        # ahí el jugador podría morir en el círculo 2, revivir, y encontrarse
        # con que ahora el bueno es el 4. Una partida, un círculo.
        self._cementerio = Cementerio.leer(TMX)
        self._nadando: bool = False
        # La señal del círculo sorteado (R2-8): brasas que solo arden sobre
        # el círculo elegido. Estado en `_armar_brasas`.
        self._reloj_brasas: float = 0.0
        #: AUD-498 — segundos reales que el mundo lleva sin dar un paso de
        #: simulación con un hit-stop en vuelo. Ver `_reanimar_el_reloj`.
        self._reloj_atascado: float = 0.0
        self._hitstop_vigilado: float = 0.0
        self._brasas: list[dict] = []
        self._disco_brasa: pygame.Surface | None = None
        self._disco_halo: pygame.Surface | None = None
        #: D-01·J — las estrellas del cielo. Ver `_armar_estrellas`.
        self._estrellas: list[dict] = []
        #: D-01·H — las ánimas del camposanto y su pincel. Ver `_armar_animas`.
        self._animas: list[dict] = []
        self._pincel_anima: pygame.Surface | None = None
        #: D-01·B — los jirones de niebla y su pincel. Ver `_armar_niebla`.
        #: El nombre lleva apellido a propósito: `_niebla` ya es del padre
        #: (`stage_parts/actualizaciones.py` le llama `update` cada fotograma)
        #: y pisárselo con una lista revienta el fotograma siguiente.
        self._jirones_de_niebla: list[dict] = []
        self._jiron: pygame.Surface | None = None
        #: D-01·K — las nubes que derivan. Ver `_armar_nubes`.
        self._nubes: list[dict] = []
        #: D-01·I — la memoria del agarre del mecate (una visita, un agarre).
        self._mecate = None
        self._mecate_cacheado = False
        self._mecate_agarrado = False
        self._mecate_soltado = False
        #: #49 — la Forma del Ánima: segundos que quedan de transformación
        #: y los fotogramas re-teñidos del portador. Ver `_vestir_la_mascara`.
        self._transformacion = 0.0
        self._frames_del_anima: dict | None = None
        self._frames_del_portador: dict | None = None
        #: #50 — las hojas del héroe del concept, cargadas una vez.
        self._frames_del_heroe: dict | None = None
        #: #49 — las hojas TALLADAS de la Forma del Ánima (anima_*.png).
        self._hojas_anima_cacheadas: dict | None = None
        #: R16 — la memoria del travelling del descenso (ver
        #: `_recorrer_cementerio`); `None` fuera del foso.
        self._cam_descenso: pygame.Vector2 | None = None
        #: R18 — la tirolesa cacheada (ver `_sujetar_la_tirolesa`).
        self._cable = None
        self._cable_cacheado = False
        #: D-01·C/D — el estado del rito de las Cuatro Ofrendas.
        self._pavesas: list[dict] = []
        self._pavesas_en_mano = 0
        self._circulos_encendidos: set[str] = set()
        self._luces_del_rito: list = []
        self._polvo_de_losa: list[dict] = []
        self._losa = None
        self._jirones_del_portador: list[dict] = []
        #: La pila de monedas que tapa el rectángulo plano del motor.
        self._pincel_ofrenda: pygame.Surface | None = None
        super().__init__(context, TMX)
        # Skin de las mecánicas del motor (tarea #44): `_drawing` es un
        # atributo de la escena, así que se instala una SUBCLASE del
        # `DrawingSystem` con las piezas del mausoleo talladas — mismo
        # patrón que la intro con `CutsceneAction`, cero framework. El
        # límite de esta técnica (las mecánicas del ECS no se pueden
        # skinear así) está documentado en `skins.py`.
        from src.stages.boss_paburu.skins import DibujoDelCamposanto
        self._drawing = DibujoDelCamposanto()

    # ── Iluminación ceremonial ──────────────────────────────────
    #: AUD-463 — el suelo de luz del motor, bajado PARA ESTE ESCENARIO.
    #:
    #: `MIN_AMBIENTE = 0.45` es del framework y su motivo está escrito allí:
    #: «una noche realista que impide jugar es un defecto». Vale para un
    #: escenario a cielo abierto sin focos propios. Aquí no: el camposanto
    #: lleva farol pegado al jugador y catorce cuencos de fuego, y la
    #: catacumba tiene sus cuatro braseros — hay luz local de sobra para leer
    #: el suelo. Con el suelo en 0.45 la rampa negra del descenso (0.16) era
    #: literalmente imposible: el instante de la trampa, que es el momento que
    #: el nivel entero prepara, no ocurría.
    MIN_AMBIENTE = 0.12

    def _aplicar_hora(self) -> None:
        """El reloj del mundo aporta tinte, bloom y clima; la luz la pone la sala.

        AUD-463 — `_aplicar_hora` corre cada fotograma y termina asignando
        `_lighting.ambient_brightness`, así que pisaba TODAS las rampas de este
        escenario: la penumbra por forma, el negro del descenso y las dos luces
        del veredicto del epílogo. La escena creía mandar en su propia luz y no
        mandaba; lo que se veía era el suelo del motor teñido de crepúsculo.

        Se sobrescribe aquí y no se toca el framework porque la decisión es de
        ESTE escenario: una sala de juicio bajo tierra no responde a la hora
        que sea arriba. Lo demás del reloj —el tinte azul de la noche, el bloom
        extra, el clima, la sombra solar, `self.ambiente`— se conserva llamando
        al padre; lo único que se recupera es el brillo.

        El latido del compás (AUD-425) sí se respeta: era una mejora de este
        stage (BPM de «Judgment of the Ancestors») y se vuelve a aplicar sobre
        la luz de la sala, que es sobre lo que tenía que latir.
        """
        from src.framework.vfx import pulso

        mia = self._lighting.ambient_brightness
        super()._aplicar_hora()
        self._lighting.ambient_brightness = min(
            1.0, mia * pulso.factor_de_luz(getattr(self, "_reloj_musical", None)))

    def on_enter(self) -> None:
        """Arma la escena y reemplaza la iluminación por defecto.

        `StageScene.on_enter` decide las luces según la zona, con
        posiciones pensadas para la resolución vieja de 320×224 — en una
        arena de 800×600 quedan amontonadas en la esquina superior
        izquierda. No se puede cambiar ese código porque es del profesor,
        así que se sobrescribe la lista después de que el padre termina.
        Solo se tocan atributos: no se modifica el framework.
        """
        # `super().on_enter()` consume `pending_load` al restaurar la partida.
        # Hay que mirar ANTES si venimos de un guardado: la vida extra de la
        # zona 4 llena la barra en una entrada fresca, pero pisar la vida
        # restaurada convertiría cada carga en una curación gratis
        # (el motor lo vigila en test_guardado_y_cadena).
        pendiente = getattr(self.context, "pending_load", None)
        self._venia_de_guardado = pendiente is not None
        # AUD-488 — CARGAR UNA PARTIDA RECORTABA LA VIDA DE 9 A 5.
        #
        # El orden es el problema y no se puede reordenar: `super().on_enter()`
        # llama a `set_health(pendiente.health)`, que acota contra
        # `max_health`, y en ese instante `max_health` todavía vale los 5 de
        # fábrica porque el bonus de zona 4 se concede DESPUÉS (no puede
        # concederse antes: el jugador aún no existe). Guardar con 9 corazones
        # y cargar con 5 es perder cuatro por usar el menú de guardado —
        # invisible, silencioso, y castiga justo a quien guarda.
        #
        # Se anota aquí el valor original, antes de que nadie lo toque, y
        # `_dar_vida_de_zona_4` lo devuelve una vez subido el techo.
        self._vida_pendiente = (float(getattr(pendiente, "health", 0.0))
                                if pendiente is not None else None)
        # AUD-492 — EL EPÍLOGO SÓLO SE JUGABA ENTERO LA PRIMERA VEZ.
        #
        # `_epilogo_arrancado` es un pestillo de «esto ya ocurrió» y nadie lo
        # abría: `respawn()` no construye una escena nueva, reejecuta
        # `on_enter` sobre ESTA, así que el pestillo sobrevivía a la muerte.
        # Quien ganaba en el segundo intento veía el final degradado — los
        # custodios no se despiden y el cuerno no suena— y no había forma de
        # saber que faltaba algo: el epílogo simplemente pasaba más callado.
        # Se abre aquí, que es por donde pasan las dos entradas (fresca y
        # reintento), y también en `_reanudar_pelea` por si alguien rearma la
        # pelea sin volver a entrar.
        self._epilogo_arrancado = False
        super().on_enter()

        # `StageScene` muestra el tip de "Move / Jump / Crouch" durante los
        # primeros 6 s de cualquier stage. Acá sobra por dos razones: esto es
        # el jefe FINAL —quien llega ya sabe caminar— y el cartel aparece
        # centrado, justo encima de la zona donde el boss telegrafía EL SELLO.
        # Marcarlos como ya vistos lo suprime sin tocar el framework.
        self._tutorial_shown.update({"move", "landed", "enemy_kill"})
        # `super().on_enter()` ya lo disparó unas líneas antes, así que además
        # de marcarlo como visto hay que bajar el que quedó en pantalla.
        self._tutorial._active = False

        # El aire del camposanto — bug cazado en el playtest de Alejandro y
        # confirmado contra el motor: el clima `fog` reproduce
        # `sfx_environment_wind_indoor.wav`, una muestra de 2,0 s en loop
        # infinito, y un soplido de dos segundos repetido eternamente se oye
        # como «un chorro raro cada segundo». A los stages del profesor no
        # les pasa: ninguno usa `fog` ni `snow`, los dos climas que comparten
        # esa muestra corta. En vez de tocar el motor, el stage trae su
        # propio ambiente (12 s, loop perfecto por construcción — ver
        # `gen_paburu_sfx.ambiente_camposanto`) y lo funde encima del que el
        # padre acaba de arrancar, por la misma API pública que usó él.
        audio = getattr(self.context, "audio", None)
        if audio is not None and hasattr(audio, "play_ambient"):
            ruta = (settings.ASSETS_DIR / "sfx" / "bosses"
                    / "sfx_bosses_paburu_ambiente.wav")
            if ruta.exists():
                if getattr(audio, "_ambient_active", False):
                    audio.crossfade_ambient(ruta, duration=1.2, volume=0.3)
                else:
                    audio.play_ambient(ruta, volume=0.3)

        # R20 — UNA SOLA LUNA. El cargador del motor escala TODO fondo a
        # 800×600 y el DrawingSystem lo repite en horizontal para cubrir
        # la vista: con 800 px de cielo en una pantalla de 960 caben DOS
        # copias — dos lunas (se vio en captura al aclarar las montañas).
        # El cielo lejano ahora se dibuja a 1600 px y la escena lo repone
        # a su ancho real después de que el cargador lo aplaste. Solo se
        # toca la lista de la escena, cero motor. Idempotente: el respawn
        # re-entra por aquí y el ancho ya está bien.
        self._ensanchar_el_cielo()

        self._lighting.clear()
        self._stage_lights = []
        self._player_light = None

        # Los cuencos se arman en la catacumba: la pelea ocurre ahí abajo,
        # llegue el jugador por el círculo que llegue.
        cat = self._cementerio.catacumba
        base_x = cat.interior.left if cat is not None else 0
        pabilo_y = cat.interior.bottom - 16 if cat is not None else 0
        self._braziers = [
            LightSource(
                pygame.Vector2(base_x + dx, pabilo_y),
                radius=132.0,
                color=BRAZIER_COLOR,
                intensity=0.0,          # apagados: se encienden por forma
                flicker=True,
                flicker_speed=5.5,
                flicker_amount=0.22,
            )
            for dx in BRAZIER_OFFSETS
        ]
        for light in self._braziers:
            self._lighting.add_light(light)
            self._stage_lights.append(light)

        # AUD-469 — EL FAROL SE APAGA. «¿Por qué se ve como una luz en el
        # personaje? Lo hace verse raro.»
        #
        # Era un `LightSource` de radio 110 pegado al jugador, y con la luz
        # de camino en 0.82 se notaba poco. Bajada a noche real (AUD-463) el
        # contraste lo delató: un disco claro que viaja con el sprite y que
        # el jugador no puede explicar —no lleva antorcha en el arte, no hay
        # objeto que la justifique— se lee como un halo pegado encima, no
        # como iluminación. La regla del stage es que todo lo que se ve tiene
        # una razón dentro del mundo, y esto no la tenía.
        #
        # Lo que ocupa su sitio: la luz de camino sube de 0.50 a 0.58 —lo
        # justo para leer el suelo— y los catorce cuencos de fuego del
        # camposanto pasan a ser LOS charcos de luz. Ahora el recorrido tiene
        # zonas claras y oscuras de verdad, con fuentes visibles, en vez de
        # una burbuja que acompaña al jugador a todas partes.
        self._farol = None

        # Penumbra de camino: no la de combate. La sube `_descender_a_la_catacumba`.
        self._lighting.ambient_brightness = LUZ_CAMINO

        # La señal de la boca (R2-8 · D-01).
        self._armar_brasas()
        # D-01·C/D — el rito de las Cuatro Ofrendas: pavesas y losa.
        self._preparar_el_rito()
        # D-01·B — la niebla del camposanto es NUESTRA (ver `_armar_niebla`).
        self._apagar_el_velo_del_motor()
        self._armar_niebla()
        # D-01·H — las ánimas que se levantan de las tumbas.
        self._armar_animas()
        # D-01·J — las estrellas que titilan.
        self._armar_estrellas()
        # D-01·K — las nubes que derivan.
        self._armar_nubes()
        # D-01·F — los checkpoints se visten de veladoras.
        self._encender_las_veladoras()
        # #50 — el portador se pone el rostro del concept.
        self._vestir_al_portador()
        # AUD-468 — el pozo, a quien vive en él: sin esto el ahogado sigue al
        # jugador fuera del agua (ver `AhogadoDelPozo.update`).
        self._encerrar_a_los_ahogados()

        self._dar_vida_de_zona_4()

        # EL REINTENTO. Si la pelea ya había empezado, esta reentrada viene de
        # morir contra Paburu: el checkpoint de la catacumba devuelve al
        # jugador ahí abajo, y lo que hay que rearmar es la pelea — jefe
        # fresco, sin cinemática (ya la vio), sala en su luz de combate y el
        # portador curado. Morir cuesta segundos de reintento, no medio
        # cementerio de caminata: era la mitad del argumento de la catacumba.
        if self._cementerio.sellado and self._boss_ref() is None:
            self._reanudar_pelea()

        # PAB-01 (auditoría final) — cargar una partida guardada EN la
        # catacumba dejaba al jugador sellado en la sala sin jefe: el sorteo
        # y `sellado` viven en la escena y no en el guardado, así que la
        # reconstrucción lo restauraba dentro de una caja de roca vacía. Un
        # softlock de los de reiniciar el juego. Si el guardado devuelve al
        # jugador dentro de la cámara, la pelea ES el estado válido: se
        # rearma entera (jefe fresco, cura del juez, sin cinemática).
        cat = self._cementerio.catacumba
        if (not self._cementerio.sellado and cat is not None
                and self._player is not None
                and cat.interior.colliderect(self._player.rect)):
            self._cementerio.sellado = True
            self._cementerio.encuadre.update(
                float(cat.interior.left),
                float(cat.interior.bottom + 16 - settings.INTERNAL_HEIGHT),
            )
            self._reanudar_pelea()

    # AUD-481 — MORIR EN LA CATACUMBA EXPULSABA AL JUGADOR DEL MAPA.
    #
    # El síntoma medido: morir contra Paburu y caer para siempre, partida
    # perdida. La cadena es de dos eslabones, ninguno del stage:
    #
    #   1. `ProgressionSystem` guarda el CENTRO del checkpoint (3984, 1280),
    #      y `StageScene.respawn` lo aplica como esquina superior izquierda
    #      (`position` es el topleft del rect). El jugador reaparece 16 px más
    #      abajo de lo que nadie quiso: sus pies (1312) quedan DENTRO de la
    #      losa `CatSuelo` (1296→1312).
    #   2. El resolutor de colisión ve una caja embebida en un sólido y la
    #      empuja por el eje de menor penetración, que ahí es el horizontal:
    #      lo escupe a x=4112, fuera de la pared este de la sala, donde no hay
    #      suelo. Y ya no hay retorno.
    #
    # Se arregla del lado del stage porque el motor es del profesor y porque
    # aquí SABEMOS dónde se debe reaparecer: `cat.spawn` es el punto de pies
    # de la antecámara, el mismo que usa el descenso. Se recoloca SIEMPRE que
    # la pelea esté en curso, no sólo «si quedó fuera»: la posición del motor
    # ya es incorrecta aunque el rect todavía toque el interior de la sala
    # —estar hundido en la losa cuenta como tocarla— y esa condición era
    # justamente la que dejaba pasar el caso.
    def respawn(self) -> None:
        """Reaparecer en la sala del juicio, de pie y dentro de la cámara."""
        # #49 — la máscara no sobrevive a la muerte: el préstamo era de
        # los velados y el portador acaba de estar entre ellos. ANTES del
        # padre, que puede reconstruir al jugador: hay que desvestir al
        # que muere, no al que nace.
        self._desvestir_la_mascara()
        self._jirones_del_portador.clear()
        super().respawn()
        self._desvestir_la_mascara()
        # #50 — si el respawn reconstruyó al jugador, que vuelva vestido.
        self._vestir_al_portador()
        if not self._cementerio.sellado:
            return
        self._recolocar_en_la_antecamara()

    def _recolocar_en_la_antecamara(self) -> None:
        """Deja al jugador de pie en `cat.spawn`, con rect y `position` en fase.

        `position` y `rect` son dos copias del mismo dato en el motor y el
        integrador de física lee `position`: escribir sólo el rect (o sólo
        `position`) hace que el siguiente fotograma revierta la mitad del
        arreglo. Por eso se fija el rect por `midbottom` —que es lo que
        significa `spawn`: los pies— y se copia de vuelta a `position`.
        `set_spawn` cierra el círculo para que la siguiente muerte no vuelva
        a leer el checkpoint envenenado.
        """
        cat = self._cementerio.catacumba
        jugador = self._player
        if cat is None or jugador is None:
            return
        jugador.rect.midbottom = (int(cat.spawn[0]), int(cat.spawn[1]))
        jugador.position.update(float(jugador.rect.x), float(jugador.rect.y))
        jugador.velocity.update(0, 0)
        if hasattr(jugador, "set_spawn"):
            jugador.set_spawn(pygame.Vector2(jugador.position))
        self._checkpoint_position = pygame.Vector2(
            float(jugador.rect.centerx), float(jugador.rect.centery))

    def _reanudar_pelea(self) -> None:
        """Rearma la pelea tras una muerte, sin repetir la presentación."""
        cat = self._cementerio.catacumba
        jugador = self._player
        if cat is None or jugador is None:
            return
        # AUD-481 — se recoloca SIEMPRE, no sólo «si quedó fuera de la sala».
        # La condición vieja (`if not cat.interior.colliderect(...)`) daba por
        # buena cualquier posición que TOCASE el interior, y la del respawn
        # roto lo tocaba: el jugador estaba hundido en la losa del suelo, que
        # está dentro del rect de la cámara. Colocar de nuevo en el punto de
        # pies conocido no cuesta nada cuando ya estaba bien y es la única
        # salida cuando estaba mal.
        self._recolocar_en_la_antecamara()
        jugador._state.health = jugador.max_health
        self._epilogo_arrancado = False     # AUD-492: la pelea empieza de cero
        self._sostener_encuadre()
        self._reubicar_guardianes(cat)
        self._invocar_a_paburu(cat, con_intro=False)

    # ── La vida del jugador en la zona 4 ────────────────────────
    #: Corazones extra en el último nivel del juego.
    #:
    #: `settings.PLAYER_MAX_HEALTH` son 5 y es del profesor: cambiarlo ahí
    #: reequilibraría los quince niveles anteriores, que están medidos con
    #: cinco. Pero el lore dice que el jugador llega al camposanto después de
    #: cruzar tres zonas, y un nivel de cuatro pantallas con jefe al final no
    #: se aguanta con la misma barra que el primer pasillo del juego.
    #:
    #: `Player.max_health` es `PLAYER_MAX_HEALTH + _bonus_max_health`, y ese
    #: bonus existe justamente para esto: los objetos de inventario lo suben.
    #: Aquí se usa el mismo canal, sin tocar el motor y sin afectar a ningún
    #: otro nivel.
    #:
    #: +4 y no +10: la pelea de Paburu está medida a 20 golpes suyos y hay que
    #: seguir pudiendo perderla. Cuatro corazones son el margen para llegar al
    #: círculo con algo de vida, no para ignorar a los enemigos.
    VIDA_EXTRA_ZONA_4 = 4.0

    def _dar_vida_de_zona_4(self) -> None:
        jugador = self._player
        if jugador is None:
            return
        jugador._bonus_max_health = max(
            float(getattr(jugador, "_bonus_max_health", 0.0)),
            self.VIDA_EXTRA_ZONA_4,
        )
        # Se llega al cementerio con la barra llena: el recorrido es lo que
        # tiene que gastarla, no lo que traías de antes. Pero SOLO en una
        # entrada fresca — al cargar una partida, la vida guardada manda:
        # el bonus sube el techo (max_health) sin regalar curación.
        vida_guardada = getattr(self, "_vida_pendiente", None)
        if not getattr(self, "_venia_de_guardado", False):
            jugador._state.health = jugador.max_health
        elif vida_guardada is not None:
            # AUD-488 — el techo ya subió: se devuelve la vida guardada, que
            # el motor había recortado contra el máximo VIEJO. Acotada al
            # máximo nuevo y no copiada a ciegas: una partida manipulada (o de
            # una versión con otro bonus) no puede empezar por encima de la
            # barra.
            jugador._state.health = max(
                0.0, min(float(jugador.max_health), float(vida_guardada)))

        # Los tres guardianes salieron del PNG de fondo para poder moverse.
        from src.stages.boss_paburu import guardianes
        self._guardianes = guardianes.cargar()

        def _on_phase(**data: Any) -> None:
            self._set_phase_light(int(data.get("phase", 0)))

        self.context.event_bus.subscribe(Events.BOSS_PHASE_CHANGED, _on_phase)

        def _on_boss_attack(**data: Any) -> None:
            if data.get("pattern") == "ANCIENT_CALL":
                self._procesion_de_guardianes()

        self.context.event_bus.subscribe(Events.BOSS_ATTACK, _on_boss_attack)
        self._vfx_handlers[Events.BOSS_ATTACK] = _on_boss_attack
        # Se guarda en el mismo dict que limpian `on_exit` y `respawn`, así
        # el handler se desuscribe solo y no se duplica al reaparecer.
        self._vfx_handlers[Events.BOSS_PHASE_CHANGED] = _on_phase

        # Los cuatro círculos avisan por el bus al pisarlos (son `EventTrigger`
        # del TMX; desde D-01·C suenan CADA cruce — la escena deduplica).
        def _on_trigger(**data: Any) -> None:
            # `InteractableSystem._disparar` lo emite como `nombre=`.
            nombre = str(data.get("nombre", ""))
            if self._cementerio.es_el_bueno(nombre):
                self._descender_a_la_catacumba()
                return
            # D-01·C — pisar un círculo llevando fuego lo enciende.
            self._encender_circulo(nombre)

        self.context.event_bus.subscribe(EVENTO_DISPARADOR, _on_trigger)
        self._vfx_handlers[EVENTO_DISPARADOR] = _on_trigger

        # #49 — el ULTI viste la máscara: al estallar el ultimate del motor
        # (Z+X con la barra llena), el portador queda transformado unos
        # segundos. Solo aspecto — el daño del ulti es el del motor.
        def _on_ultimate(**_data: Any) -> None:
            self._vestir_la_mascara()

        self.context.event_bus.subscribe(Events.VFX_ULTIMATE, _on_ultimate)
        self._vfx_handlers[Events.VFX_ULTIMATE] = _on_ultimate

        # R21 — EL COMBO HONESTO. Hallazgo del video: «ataco a la nada y
        # acumulo puntos de combo sin pegar». Es del motor (bug nº 13,
        # reportado): `_start_attack` suma el combo al APRETAR el botón,
        # no al conectar. La escena lo corrige sin tocar el motor: marca
        # si el ataque en curso conectó (los golpes emiten SFX_ENEMY_HIT
        # o ENEMY_DIED) y, al terminar un ataque que no tocó a nadie, el
        # combo vuelve a cero — abanicar el aire no encadena.
        def _on_conecta(**_data: Any) -> None:
            self._golpe_conecto = True

        for _ev in (Events.SFX_ENEMY_HIT, Events.ENEMY_DIED):
            self.context.event_bus.subscribe(_ev, _on_conecta)
            self._vfx_handlers[_ev] = _on_conecta

    def _ensanchar_el_cielo(self) -> None:
        """Repone la capa lejana a su ancho nativo (ver nota en on_enter)."""
        capas = getattr(self._stage_data, "background_layers", None)
        if not capas:
            return
        ruta = (settings.ASSETS_DIR / "backgrounds" / "paburu"
                / "bg_paburu_far.png")
        try:
            img = pygame.image.load(str(ruta)).convert()
        except Exception:
            return
        if img.get_width() <= capas[0].get_width():
            return                              # nada que reponer
        alto = capas[0].get_height()
        if img.get_height() != alto:
            ancho = int(img.get_width() * alto / img.get_height())
            img = pygame.transform.smoothscale(img, (ancho, alto))
        capas[0] = img

    # ── Tecla de debug: forzar forma ────────────────────────────
    # Teclas 1-4. Existe para la demostración: EP1 solo implementa la
    # Forma 1, así que en una partida normal el boss nunca baja de fase y
    # las otras tres —que YA están cargadas, con su hoja de sprites y su
    # iluminación— no se pueden mostrar. El GDD §7 la pide recién para EP3
    # junto a la selección aleatoria de la Forma 3; acá se adelanta solo la
    # parte de depuración, que no afecta al combate.
    _TECLAS_FORMA = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)

    #: Tecla 0 — rejugar la aparición de Paburu.
    #: La entrada ya no corre sola (`ENTRADA_AL_ENTRAR = False`), así que
    #: hace falta una forma de verla al iterar y al enseñarla.
    _TECLA_ENTRADA = pygame.K_0

    #: Tecla 9 — saltar directo al círculo sorteado y disparar la trampa.
    #: Iterar sobre el combate significaba caminar hasta tres mil píxeles de
    #: cementerio cada vez. Es depuración pura y no toca nada del combate.
    _TECLA_IR_AL_CIRCULO = pygame.K_9

    #: Tecla 8 — cargar el ulti al tope (pedido de Alejandro: «déjame un
    #: botón para activar la ulti aunque no esté cargada, para verlo y
    #: apreciarlo»). A propósito NO dispara nada por sí sola: llena la
    #: barra —los doce golpes de un plumazo— y la ACTIVACIÓN sigue siendo
    #: la de verdad (Z+X juntos), que es exactamente lo que hay que ver y
    #: grabar: el estallido del motor + la Forma del Ánima. El ulti gasta
    #: la barra como siempre; para verlo otra vez, otra vez 8. Un aviso de
    #: tres segundos sobre el portador recuerda las teclas.
    _TECLA_CARGAR_ULTI = pygame.K_8

    def _cobrar_el_combo(self) -> None:
        """Al terminar un ataque que no tocó a nadie, el combo se apaga.

        (R21, ver la nota de la suscripción en `_armar_vfx`.) El estado
        del jugador que se lee aquí es el del final del fotograma
        anterior, con sus eventos ya despachados: la respuesta a «¿ese
        ataque conectó?» es firme. El ulti no se toca — su combo es del
        motor y no pasa por esta caja.
        """
        jugador = self._player
        if jugador is None:
            return
        from src.framework.entities.states import (
            LongAttackState,
            ShortAttackState,
        )
        atacando = isinstance(getattr(jugador, "_state_instance", None),
                              (ShortAttackState, LongAttackState))
        antes = getattr(self, "_atacaba", False)
        if atacando and not antes:
            self._golpe_conecto = False          # arranca un ataque nuevo
        elif antes and not atacando:
            if not getattr(self, "_golpe_conecto", False):
                jugador.combo_count = 0
                jugador.combo_timer = 0.0
                jugador.combo_active = False
        self._atacaba = atacando

    def _cargar_el_ulti(self) -> None:
        """Llena la barra del especial (tecla 8, depuración/demostración).

        Usa `gain_special` del motor —la misma vía que los golpes— y no
        escribe el medidor a pelo: si mañana el motor cuelga efectos de
        la ganancia, esta tecla los hereda. El disparo queda en manos del
        jugador (Z+X): así lo que se ve y se graba es el ulti REAL, no
        una imitación de escena.
        """
        jugador = self._player
        if jugador is None:
            return
        jugador.gain_special(jugador.special_meter_max)
        #: Cuenta atrás del aviso «ULTI LISTO — Z+X» sobre el portador.
        self._aviso_ulti = 3.0

    def _ir_al_circulo(self) -> None:
        """Baja directo a la catacumba y arma la pelea (tecla de depuración).

        Conserva el nombre histórico —«ir al círculo»— porque los arneses de
        prueba lo llaman así; lo que hace hoy es lo que hace el círculo al
        pisarlo: descender. Para probar el jefe, es el mismo atajo de antes.
        """
        if (self._player is None or self._cementerio.sellado
                or self._cementerio.catacumba is None):
            return
        self._descender_a_la_catacumba()

    # ── Secuencia de entrada ────────────────────────────────────
    #: ¿Corre la entrada sola al pisar esta arena?
    #:
    #: **No**, y es una decisión de guion. La aparición de Paburu ocurre en el
    #: cementerio (4-1b): el jugador recorre el camposanto, cruza el punto de
    #: la trampa, se cierran los muros, y **ahí** emerge y habla. Si además
    #: hablara al entrar a la arena, el momento se contaría dos veces y el
    #: segundo llegaría sin tensión ninguna.
    #:
    #: La arena queda como lo que es —el sitio de la pelea— y el nivel que la
    #: precede se queda con la presentación. Para probar el jefe suelto,
    #: entrar acá directamente cae en combate desde el primer frame, que es lo
    #: que uno quiere cuando está iterando.
    ENTRADA_AL_ENTRAR: bool = False

    def on_stage_start(self) -> None:
        super().on_stage_start()
        if self.ENTRADA_AL_ENTRAR:
            self.lanzar_entrada()

    def lanzar_entrada(self) -> bool:
        """Dispara la aparición de Paburu. La llama el cementerio.

        Devuelve False si ya se vio o si no hay jefe, para que quien la
        dispare sepa si tiene que esperar o seguir.

        Se ve **una sola vez**: `respawn()` vuelve a llamar a `on_enter()`, y
        sin la bandera la cinemática se repetiría entera cada vez que el
        jugador muere — exactamente el momento en que menos ganas hay de
        mirarla.
        """
        if self._intro_vista:
            return False
        boss = self._boss_ref()
        if boss is None:
            return False
        from src.framework.stage.cutscene_system import CutsceneScript
        from src.stages.boss_paburu import intro

        self._intro_vista = True
        boss.intro_eyes = 0.0
        guion = CutsceneScript(intro.construir(self, boss, AMBIENT_BY_PHASE[0]))
        guion.start(callback=self._fin_intro)
        self._intro = guion
        return True

    def _fin_intro(self) -> None:
        """Devuelve el control con la sala exactamente en su estado normal.

        La forma se fuerza aquí y no se da por supuesta. La cinemática enseña
        a Paburu **como fue en vida** —la Forma 4, el Espíritu— y es
        `Transformacion` quien lo devuelve a la piedra al final. Pero esa
        acción está a mitad del guion, así que cualquier salida temprana
        —ESC, un salto de acción, la cinemática cortada— dejaba al jefe en la
        forma final: el combate empezaba por donde tenía que terminar, con los
        ataques de la Forma 4 y la vida de la 1.
        """
        self._intro = None
        boss = self._boss_ref()
        if boss is not None:
            boss.intro_eyes = 1.0
            from src.stages.boss_paburu.boss_paburu import FORM_STONE
            boss.current_phase = FORM_STONE
            boss.current_health = boss.phase_max_health
        self._set_phase_light(0)
        self._despejar_el_circulo()

    # ── Los moradores se apartan ────────────────────────────────
    #: Cuánto tarda un morador en desaparecer cuando Paburu emerge.
    RETIRADA = 0.9

    def _despejar_el_circulo(self) -> None:
        """Los moradores se van cuando el shamán aparece.

        Es de guion antes que de mecánica: las máscaras tilawa son guardianes
        del camposanto, no monstruos, y lo que guardan es a Paburu. Cuando él
        sale, ellas ya no pintan nada — se apartan, como quien deja pasar.

        Y hace falta jugablemente: la pelea está medida para uno contra uno.
        Tres máscaras embistiendo mientras el jefe telegrafía EL SELLO no es
        más difícil, es ilegible. El jugador no puede leer dos amenazas que
        piden respuestas opuestas —esquivar hacia los lados y no estar en el
        centro— al mismo tiempo.

        Se van todos, no sólo los del círculo: los de fuera están detrás de un
        muro que el jugador ya no puede cruzar, así que dejarlos vivos sólo
        gasta fotogramas.
        """
        if self._stage_data is None:
            return
        from src.stages.boss_paburu.boss_paburu import BossPaburu as _B
        for e in list(self._stage_data.entity_list):
            if isinstance(e, _B):
                continue
            # `is_visible` a False los saca del dibujo y del contacto sin
            # tener que quitarlos de la lista mientras se itera sobre ella.
            e.is_visible = False
            if hasattr(e, "is_alive"):
                e.is_alive = False
            self.context.event_bus.emit(
                Events.VFX_BUBBLE, pos=(e.rect.centerx, e.rect.centery),
            )

    def _update_lighting(self, dt: float) -> None:
        """La luz del camposanto la ponen los fuegos, no el jugador (AUD-469).

        «¿Por qué se ve como una luz en el personaje? Lo hace verse raro.» —
        y había DOS. Una era el farol de este stage, que se apaga arriba; la
        otra la pone el motor: `_update_lighting` crea y mantiene un
        `LightSource` pegado al jugador, radio 100 e intensidad 0,9 en cuanto
        hay un enemigo vivo. En un escenario diurno pasa desapercibido; en
        este, con la noche real de AUD-463, ese disco cálido viajando con el
        sprite era lo primero que veía el ojo.

        No es un fallo del motor —para un nivel sin fuentes propias es lo
        correcto— pero aquí sobra: el camposanto tiene catorce cuencos de
        fuego y la sala cuatro braseros, y el diseño quiere que la luz venga
        de sitios que se ven. Se sobrescribe el método y se conserva lo único
        que hacía falta: el `update` del sistema, que anima el parpadeo.
        """
        camara = getattr(self, "_camera", None)
        self._lighting.update(
            dt, camara.offset if camara is not None else pygame.Vector2())

    def _encerrar_a_los_ahogados(self) -> None:
        """Le da a cada ahogado el rect del agua en la que vive (AUD-468).

        La escena es quien sabe dónde está el agua (`Cementerio.agua`, leído
        del TMX) y el enemigo quien sabe qué hacer con ella. Se inyecta como
        el reproductor de SFX del jefe: un atributo público, sin herencia
        nueva y sin tocar el motor.
        """
        from src.stages.boss_paburu.moradores import AhogadoDelPozo

        if self._stage_data is None or not self._cementerio.agua:
            return
        for entidad in self._stage_data.entity_list:
            if not isinstance(entidad, AhogadoDelPozo):
                continue
            centro = entidad.rect.center
            suya = next((r for r in self._cementerio.agua
                         if r.collidepoint(centro)), None)
            entidad.pozo = suya or self._cementerio.agua[0]

    #: AUD-479 — cuánto puede durar un hit-stop antes de que lo demos por
    #: colgado. Uno normal dura 0,05 s; el del flechazo, 0,035. Medio segundo
    #: es diez veces el peor caso legítimo: imposible de alcanzar jugando, y
    #: corto de sobra para que un cuelgue se sienta como un tirón y no como el
    #: final de la partida.
    TOPE_HITSTOP = 0.5

    @staticmethod
    def _el_motor_ya_drena(colision) -> bool:
        """¿Este motor arregló AUD-498? Entonces nuestros parches sobran.

        El motor v2 del profesor (2026-08-17) adoptó el arreglo del reporte:
        `App.run` llama a `actualizar_en_tiempo_real(unscaled_dt)` cada
        fotograma, fuera del bucle de pasos, y la cuenta atrás del hit-stop
        vive ahí. La huella inequívoca es el método nuevo que ese cambio
        partió de `update_hitstop`: `aplicar_escala_de_hitstop`.

        Con el motor drenando, nuestros tres guardianes (AUD-467, AUD-479 y
        AUD-498) pasan de red de seguridad a SEGUNDA MANO sobre el mismo
        contador: medido en el bucle real de v2, el hit-stop duraba 2
        fotogramas con nuestro drenaje activo y 4 sin él — los golpes
        perdían la mitad de su peso. Por eso los tres ceden ante esta marca,
        y siguen funcionando enteros si el juego corre sobre un motor v1.
        """
        return hasattr(colision, "aplicar_escala_de_hitstop")

    def _vigilar_el_hitstop(self, dt: float) -> None:
        """Nadie deja el reloj del juego parado. Nadie.

        El contador de hit-stop lo drena `_update_gameplay`, y hay varios
        caminos por los que ese método no corre en un fotograma (una escena
        que bloquea, la entrada del jefe, el juego terminado, una pausa que
        llega en el peor momento). Cada uno de ellos, si coincide con un golpe
        recién conectado, deja `time_scale` en cero **para siempre**: el
        síntoma es un juego congelado con la pantalla partida a medio
        redibujar, que es exactamente la captura del playtest.

        AUD-467 tapó el camino que sabíamos reproducir. Éste no tapa caminos:
        pone un techo. Da igual por dónde se llegue — a los `TOPE_HITSTOP`
        segundos reales el mundo vuelve a correr.
        """
        colision = getattr(self, "_collision", None)
        if colision is None or self._el_motor_ya_drena(colision):
            return
        if not colision.is_hitstopped:
            self._hitstop_vigilado = 0.0
            return
        reloj = self.context.clock
        real = getattr(reloj, "unscaled_dt", dt) if reloj is not None else dt
        self._hitstop_vigilado = getattr(self, "_hitstop_vigilado", 0.0) + (
            real or dt)
        if self._hitstop_vigilado < self.TOPE_HITSTOP:
            return
        # Se acabó: se fuerza el fin y se devuelve el reloj a la vida.
        colision._hitstop_timer = 0.0
        colision.update_hitstop(real or dt, reloj)
        self._hitstop_vigilado = 0.0
        logging.getLogger(__name__).warning(
            "hit-stop colgado más de %.2f s: se fuerza su fin (AUD-479). Si "
            "esto sale en el registro, hay un camino que no drena el contador.",
            self.TOPE_HITSTOP)

    def _drenar_el_hitstop(self, dt: float) -> None:
        """AUD-467 — EL CUELGUE DE VERDAD: un golpe + una cinemática = juego muerto.

        Reportado como «después del combo se queda pegado», y es literal —
        pero no es el combo: es el **hit-stop**. Cada golpe que conecta
        congela la simulación 0,05 s poniendo `time_scale` a 0, y quien lo
        descongela es `CollisionSystem.update_hitstop`, que vive dentro de
        `_update_gameplay`. Y `_update_gameplay` no corre mientras una
        cinemática bloquea (`StageScene.update`: `if not en_escena`), ni
        cuando esta escena se salta `super().update()` para congelar el mundo
        durante la entrada del jefe.

        O sea: si el jugador está pegando cuando arranca una cinemática —y en
        este nivel arranca justo al pisar el círculo, que es cuando uno viene
        peleando— el contador se queda a medias con el reloj en cero. No es
        una pausa larga: **no vuelve nunca**. Medido: 10 s de juego después,
        `time_scale` seguía en 0,0.

        El motor tiene el aviso escrito desde AUD-001 («the game freezes
        permanently on the first landed hit») para el caso hermano: allí el
        peligro era alimentar el contador con el `dt` escalado; aquí es no
        alimentarlo en absoluto. Vale la pena CONTÁRSELO al profesor: le pasa
        a cualquier entrega que combine golpes y cinemáticas.

        Del lado del stage el arreglo es exacto: cuando ESTA escena sabe que
        el padre no va a drenar el contador, lo drena ella, con el `dt` real
        del reloj (nunca el escalado, que en hit-stop vale 0 — ése era el
        AUD-001 original).
        """
        colision = getattr(self, "_collision", None)
        if (colision is None or not colision.is_hitstopped
                or self._el_motor_ya_drena(colision)):
            return
        reloj = self.context.clock
        real = getattr(reloj, "unscaled_dt", dt) if reloj is not None else dt
        colision.update_hitstop(real or dt, reloj)

    def _reanimar_el_reloj(self) -> None:
        """AUD-498 — EL CUELGUE DEL MURCIÉLAGO, por fin cazado. Y es del motor.

        Reportado tres veces («golpeé un murciélago y se quedó pegado», «la
        música siguió sonando pero el juego en freeze»). AUD-467 y AUD-479 no
        lo arreglaron, y la razón es que los dos vivían en `update()` — que es
        **precisamente el método que deja de correr**. Reproducido con el
        bucle real del motor, no con un arnés: 180 fotogramas seguidos, CERO
        pasos de simulación.

        La cadena, entera::

            1. Un golpe conecta   → `update_hitstop` registra el factor 0.0
                                    y `clock.time_scale` vale 0.
            2. `DeltaClock.tick`  → `self._dt = raw_dt * 0.0` = **0.0**.
            3. `DeltaClock.pasos_fijos` acumula el delta ESCALADO:
                   `self._acumulado += self._dt`  → no crece nunca.
               El `while self._acumulado >= FIXED_DT` no entra: **cero pasos**.
            4. `App.run`: `for paso in clock.pasos_fijos(): scene_manager
               .update(paso)` → la escena NO se actualiza este fotograma.
            5. Quien drena el contador es `CollisionSystem.update_hitstop`,
               y vive dentro de `StageScene.update`. Que no corre. Ir al 2.

        Es AUD-001 otra vez, con otra cara. El motor lo tiene escrito palabra
        por palabra en `clock.py`: «*the hit-stop countdown decremented by 0.0
        and therefore never expired — the game freezes permanently on the
        first landed hit*». Aquel arreglo garantizó que el contador se drenara
        con tiempo REAL; AUD-390 (el paso fijo) quitó la garantía de que el
        drenaje **se ejecute**. El aviso sigue en el fichero, apuntando a una
        puerta que ya no es la que se abre.

        Por qué la música sigue sonando: `audio_manager.update` va con
        `unscaled_dt` y **fuera** del bucle de pasos, igual que `_process_events`
        y `_draw`. La ventana responde, el sonido corre, la imagen se repinta
        idéntica: un juego que parece vivo y tiene el mundo muerto.

        El arreglo, del lado del stage y sin tocar el motor: el dibujo SÍ
        corre cada fotograma, así que el latido se toma prestado de ahí. Sólo
        actúa cuando `clock.dt` es exactamente 0 — la firma inequívoca de la
        trampa, porque con cualquier escala viva el acumulador acaba dando su
        paso y el padre drena como siempre. Y se drena con el tiempo real, no
        de golpe: el hit-stop dura sus 0,05 s y el impacto conserva su peso.
        """
        colision = getattr(self, "_collision", None)
        reloj = getattr(self.context, "clock", None)
        if colision is None or reloj is None or not colision.is_hitstopped:
            self._reloj_atascado = 0.0
            return
        if self._el_motor_ya_drena(colision):
            return
        # Con el mundo simulando, el padre ya drena: no hay dos manos sobre el
        # mismo contador (el hit-stop se sentiría la mitad de largo).
        if getattr(reloj, "dt", 1.0) != 0.0:
            return
        real = float(getattr(reloj, "unscaled_dt", 0.0)) or (1.0 / 60.0)
        colision.update_hitstop(real, reloj)
        self._reloj_atascado += real
        if self._reloj_atascado < self.TOPE_HITSTOP:
            return
        # Cinturón y tirantes: si algo vuelve a rearmar el contador cada
        # fotograma, el drenaje honesto no bastaría. Aquí se corta.
        colision._hitstop_timer = 0.0
        colision.update_hitstop(0.0, reloj)
        self._reloj_atascado = 0.0
        logging.getLogger(__name__).warning(
            "el reloj llevaba %.2f s sin dar un paso de simulación: se fuerza "
            "el fin del hit-stop (AUD-498).", self.TOPE_HITSTOP)

    def update(self, dt: float) -> None:
        # El reloj de las brasas corre siempre: son decorado del camposanto
        # y no deben congelarse ni durante una cinemática (R2-8).
        self._reloj_brasas += dt
        # AUD-467 — antes que nada: si hay una cinemática por delante, el
        # hit-stop del último golpe se quedaría congelado para siempre. Se
        # drena aquí, donde se sabe que el padre no va a hacerlo.
        cinematica = (self._intro is not None and self._intro.active) or bool(
            getattr(getattr(self, "_cutscenes", None), "bloquea", False))
        if cinematica:
            self._drenar_el_hitstop(dt)
        # AUD-479 — Y EL PERRO GUARDIÁN, que corre pase lo que pase.
        #
        # AUD-467 arregló el cuelgue que sabíamos reproducir: golpe + escena
        # bloqueante. El playtest encontró otro («golpeé un murciélago y se
        # quedó pegado», con la pantalla partida a medio redibujar, que es
        # justo cómo se ve un `time_scale` en cero). No importa cuál sea el
        # camino: **ninguno puede dejar el reloj parado**, y una condición que
        # enumera los casos conocidos siempre se queda corta ante el siguiente.
        #
        # Así que en vez de adivinar más casos, se pone un tope: si el hit-stop
        # lleva vivo más de `TOPE_HITSTOP` segundos REALES —diez veces lo que
        # dura uno normal (0,05 s)— se acabó, venga de donde venga. En juego
        # normal no se alcanza nunca, así que el golpe conserva su peso; y si
        # alguien vuelve a encontrar un camino que no drena, el jugador pierde
        # medio segundo en vez de la partida.
        self._vigilar_el_hitstop(dt)
        # Mientras corre la entrada NO se llama a `super().update`: eso
        # congela al jugador, al boss y a los ataques sin necesidad de un
        # flag de "input bloqueado" en el motor. Es el mismo patrón que usa
        # `stages/stage0/stage0.py` para su cinemática.
        # Presencia de los guardianes: 0 en la Forma 1, sube al llegar a la
        # Máscara. La rampa es lenta a propósito —tardan casi dos segundos
        # en terminar de aparecer— para que se lea como una invocación y no
        # como un interruptor.
        # AUD-497 — LOS CUSTODIOS ESTÁN EN LA FORMA 2, COMO DICE EL LORE.
        #
        # El playtest: «el lore dice que los guardianes están únicamente en la
        # fase 2, pero en la 3 siguen ahí y en la 4 atacan muchísimo más, es
        # casi imposible». Las dos mitades eran ciertas y era el mismo
        # `>= 1`: una vez encendidos, no se apagaban nunca.
        #
        # Lo que el diseño dice (§3.4 y §3.6) y ahora hace el código:
        #   · FORMA 2 — su acto. Bajan a pelear con el eco de su firma.
        #   · FORMA 3 — se retiran. La Reliquia es un duelo de uno contra uno;
        #     ése es todo su argumento («moverse sin dejar de mirar»).
        #   · FORMA 4 — vuelven SÓLO cuando Paburu los llama (`ANCIENT_CALL`),
        #     que es lo que hace del llamado un momento y no un estado. Entre
        #     llamados, la sala es del Espíritu.
        #   · EPÍLOGO — vuelven a despedirse.
        #
        # `_presencia` es la rampa de aparición; ponerla a 0 los desvanece y
        # además apaga la ronda (que exige presencia completa).
        boss = self._boss_ref()
        fase = boss.current_phase if boss is not None else -1
        en_su_acto = fase == FORM_MASK
        convocados = (fase == FORM_SPIRIT and (
            self._procesion_en_curso or getattr(boss, "en_epilogo", False)
            or getattr(boss, "ofrecimiento_activo", False)))
        objetivo = 1.0 if (en_su_acto or convocados) else 0.0
        paso = dt / 1.8
        if self._presencia < objetivo:
            self._presencia = min(objetivo, self._presencia + paso)
        elif self._presencia > objetivo:
            self._presencia = max(objetivo, self._presencia - paso)
        for g in self._guardianes:
            g.update(dt)

        if self._intro is not None and self._intro.active:
            self._intro.update(dt)
            im = self.input
            if im is not None and im.is_action_just_pressed(Action.CANCEL):
                self._saltar_intro()
            return

        # R21 — el combo honesto se cobra ANTES del paso del motor: los
        # eventos del fotograma anterior ya se despacharon, así que a esta
        # altura «¿conectó el ataque que terminó?» tiene respuesta cierta;
        # y si el motor arranca otro ataque en este mismo paso, ya se
        # encuentra el combo cobrado.
        self._cobrar_el_combo()
        super().update(dt)
        # R18 — el jinete de la tirolesa no se hunde bajo el cable.
        self._sujetar_la_tirolesa()
        # D-01·I — el descenso se VE: en el foso, el mecate te agarra.
        self._guiar_el_descenso(dt)
        # #49 — el préstamo de los velados corre y sus jirones envejecen.
        self._latir_la_transformacion(dt)
        self._recorrer_cementerio(dt)
        self._revisar_parry()
        self._ronda_de_guardianes(dt)
        self._epilogo_de_la_sala(dt)
        self._actualizar_vigilante(dt)
        pulsadas = pygame.key.get_pressed()
        for fase, tecla in enumerate(self._TECLAS_FORMA):
            # Flanco de subida: sin esto la fase cambiaría 60 veces por
            # segundo mientras la tecla siga apretada.
            antes = self._teclas_previas.get(tecla, False)
            if pulsadas[tecla] and not antes:
                self._forzar_forma(fase)
            self._teclas_previas[tecla] = pulsadas[tecla]

        antes0 = self._teclas_previas.get(self._TECLA_ENTRADA, False)
        if pulsadas[self._TECLA_ENTRADA] and not antes0:
            self._intro_vista = False      # permite repetirla a voluntad
            self.lanzar_entrada()
        self._teclas_previas[self._TECLA_ENTRADA] = pulsadas[self._TECLA_ENTRADA]

        antes9 = self._teclas_previas.get(self._TECLA_IR_AL_CIRCULO, False)
        if pulsadas[self._TECLA_IR_AL_CIRCULO] and not antes9:
            self._ir_al_circulo()
        self._teclas_previas[self._TECLA_IR_AL_CIRCULO] = \
            pulsadas[self._TECLA_IR_AL_CIRCULO]

        antes8 = self._teclas_previas.get(self._TECLA_CARGAR_ULTI, False)
        if pulsadas[self._TECLA_CARGAR_ULTI] and not antes8:
            self._cargar_el_ulti()
        self._teclas_previas[self._TECLA_CARGAR_ULTI] = \
            pulsadas[self._TECLA_CARGAR_ULTI]
        if getattr(self, "_aviso_ulti", 0.0) > 0.0:
            self._aviso_ulti -= dt

    # ── El recorrido ────────────────────────────────────────────
    def _recorrer_cementerio(self, dt: float) -> None:
        """Todo lo que pasa mientras el jugador camina el camposanto."""
        jugador = self._player
        if jugador is None:
            return

        # La linterna sigue al jugador. `position` son los pies, así que se
        # sube media altura para que la luz salga del pecho y no del suelo.
        if self._farol is not None:
            self._farol.position.update(jugador.rect.centerx, jugador.rect.centery)

        if self._cementerio.sellado:
            self._sostener_encuadre()
            return

        # En superficie la cámara vive en la banda del camposanto (y 0..672).
        # El mapa ahora mide 1312 de alto por la catacumba, y sin este tope la
        # cámara seguía al jugador hacia el centro vertical del mapa: media
        # pantalla de tierra maciza y el cielo cortado. La banda tiene 72 px
        # de holgura vertical (672 − 600): se clava abajo y no se mueve — el
        # suelo queda a un tercio de pantalla y la luna arriba, siempre.
        #
        # …SALVO DURANTE EL DESCENSO (reporte de Alejandro, R16): con el
        # tope plano, el portador bajaba por el mecate y la CÁMARA SE
        # QUEDABA ARRIBA — «baja, se queda un rato ahí y luego aparece
        # abajo»: 560 px de descenso ocurrían fuera de pantalla y el corte
        # al encuadre remataba la sensación de teleport. Dentro del foso la
        # cámara lo persigue hacia abajo (a 300 px/s: alcanza el resbalón
        # de 70 sin dar tirones y no pierde de vista un salto de la cuerda)
        # y lo lleva a un tercio de pantalla; el suelo de la persecución es
        # EXACTAMENTE el `encuadre` de la pelea, así que cuando la trampa
        # se arma la cámara YA ESTÁ ahí y el empalme no corta. La x también
        # se desliza hacia la del encuadre durante la bajada: la sala se
        # revela conforme se baja, no de golpe.
        if self._camera is not None:
            cat = self._cementerio.catacumba
            foso = cat.foso if cat is not None else None
            en_descenso = (
                foso is not None and foso.width
                and foso.left - 40 <= jugador.rect.centerx <= foso.right + 40
                and jugador.rect.top > SUPERFICIE)
            o = self._camera.offset
            if en_descenso:
                # El destino es el MISMO marco que usará la pelea (los
                # números de `_descender_a_la_catacumba`): al llegar
                # abajo, el encuadre ya está puesto y no hay corte.
                #
                # El travelling lleva MEMORIA PROPIA (`_cam_descenso`):
                # `Camera.update` recalcula el desplazamiento entero cada
                # fotograma, así que suavizar contra `offset` era pelear
                # contra el motor — medido: la x se quedaba clavada a
                # 61 px del encuadre (el motor la devolvía y el suavizado
                # la retraía, tablas eternas) y la y daba un salto de
                # ~125 px al entrar al foso. Se suaviza contra lo nuestro
                # y se ASIGNA.
                if self._cam_descenso is None:
                    self._cam_descenso = pygame.Vector2(
                        o.x, min(o.y, 72.0))
                fondo_y = float(
                    cat.interior.bottom + 16 - settings.INTERNAL_HEIGHT)
                ideal_y = max(72.0, min(
                    fondo_y, jugador.rect.centery - 380.0))
                ideal_x = float(cat.interior.left)
                cam = self._cam_descenso
                paso_y = 300.0 * dt
                if abs(ideal_y - cam.y) <= paso_y:
                    cam.y = ideal_y
                else:
                    cam.y += paso_y if ideal_y > cam.y else -paso_y
                paso_x = 160.0 * dt
                if abs(ideal_x - cam.x) <= paso_x:
                    cam.x = ideal_x
                else:
                    cam.x += paso_x if ideal_x > cam.x else -paso_x
                o.x, o.y = cam.x, cam.y
            else:
                self._cam_descenso = None
                o.y = min(o.y, 72.0)

        # D-01·C — las pavesas se recogen y el polvo envejece.
        self._atender_el_rito(dt)

        self._revisar_el_pozo(dt)

    def _sostener_encuadre(self) -> None:
        """Mantiene la cámara sobre el círculo mientras dura la pelea.

        Se reafirma cada fotograma en vez de una sola vez al sellar. Es a
        propósito: `Camera.update` recalcula el desplazamiento al principio del
        frame y la sacudida de pantalla lo mueve al final, así que un valor
        puesto una vez se pierde en cuanto el jefe pega el primer golpe.
        """
        if self._camera is None:
            return
        self._camera.offset.x = self._cementerio.encuadre.x
        self._camera.offset.y = self._cementerio.encuadre.y

    # ── El pozo ─────────────────────────────────────────────────
    def _revisar_el_pozo(self, dt: float) -> None:
        """Deja que los ahogados tiren del jugador mientras esté en el agua.

        Nadar NO se resuelve acá: el pozo está declarado en el TMX como
        `WaterZone`, y el motor trae la mecánica entera —`MecanicaDeAgua` mete
        al jugador en `SwimmingState`, le cuenta el aire y lo ahoga si se
        queda—. La primera versión de este método reimplementaba esa parte
        porque `level_mechanics.py` dice en un comentario «Missing: No
        dedicated water zone detection»; el comentario está viejo y el sistema
        sí existe. Verificarlo antes de escribir habría ahorrado el trabajo.

        Lo único que el motor no sabe es que en ESTE pozo vive algo. Eso es lo
        que queda acá.
        """
        jugador = self._player
        agua = self._cementerio.en_agua(jugador)
        if agua is None:
            self._nadando = False
            return
        self._nadando = True
        self._flotar(jugador, agua, dt)

        # El arrastre es de los ahogados: se les pregunta a ellos y la escena
        # sólo los recorre.
        from src.stages.boss_paburu.moradores import AhogadoDelPozo
        if self._stage_data is not None:
            for e in self._stage_data.entity_list:
                if isinstance(e, AhogadoDelPozo) and e.tirar_de(jugador, dt):
                    self.context.event_bus.emit(
                        Events.VFX_BUBBLE,
                        pos=(jugador.position.x, jugador.position.y),
                    )

    #: Empuje de flotación, en px/s². Se compara con la gravedad que aplica
    #: `SwimmingState` (GRAVITY * 0.3 = 240): 260 la vence por poco, así que el
    #: jugador sube despacio en vez de salir disparado.
    FLOTACION = 260.0

    #: A qué profundidad se queda flotando si no toca nada.
    #:
    #: Estaba en 20 px y **dejaba al jugador encerrado en el pozo**. Con los
    #: pies a 580 y el brocal a 560 hay 52 px hasta poder pisar la orilla, y
    #: el impulso de nado del motor no llega: pone la velocidad en -120 pero
    #: el clamp del propio `SwimmingState` la recorta a -60 al fotograma
    #: siguiente, así que sube unos siete píxeles y vuelve a caer. Se entraba
    #: al agua y no se salía nunca. Lo encontró un recorrido automatizado que
    #: se quedó clavado en el borde derecho del pozo.
    #:
    #: Con 4 px flota prácticamente a ras del brocal: se ve que está en el
    #: agua y sale de un salto, que es como tiene que sentirse.
    CALADO = 4.0

    def _flotar(self, jugador: Any, agua: pygame.Rect, dt: float) -> None:
        """El jugador FLOTA: sube solo hasta quedarse en la superficie.

        POR QUÉ HACE FALTA
        `SwimmingState` del motor sólo hunde. Su bucle es:

            player.velocity.y += settings.GRAVITY * 0.3 * dt

        …y el único empuje hacia arriba es el impulso del salto, limitado a
        **uno por pulsación** (`player._swim_boosts < 1`). O sea: el jugador
        entra al agua, gastas el impulso, y a partir de ahí baja sin remedio
        hasta tocar el fondo. Eso no es nadar, es hundirse con animación de
        nado — y es exactamente lo que se veía al probarlo.

        Falta el empuje de Arquímedes, que es la mitad de la ecuación. Acá se
        añade sin tocar el framework: una aceleración hacia arriba mientras el
        cuerpo esté sumergido.

        POR QUÉ NO ES UNA FUERZA CONSTANTE
        Con empuje fijo el jugador rebota en la superficie: sale, cae, sale.
        El empuje se **atenúa con la profundidad** —fuerte en el fondo, nulo
        en la línea de flotación— y eso hace que se estabilice solo. Es la
        misma interpolación lineal que usa el tirón de los ahogados (Unidad
        VI), aplicada al revés.

        Agacharse sigue hundiendo: `SwimmingState` suma 200 px/s² al pulsar
        abajo, más que estos 260 menos la gravedad, así que bucear sigue
        funcionando y el jugador conserva el control de la profundidad.
        """
        from src.framework.entities.player import PlayerState
        from src.framework.entities.states import SwimmingState

        estado = getattr(jugador, "state", None)

        # ── Volver a nado si el motor lo sacó ──────────────────
        # `MecanicaDeAgua` mete al jugador en `SwimmingState` UNA sola vez: en
        # el fotograma en que entra al agua (`dentro and not estaba_dentro`).
        # Y `SwimmingState` se sale solo al tocar suelo. Juntando las dos
        # cosas: el jugador se hundía hasta el fondo del pozo, el estado
        # cambiaba a IDLE, y ya no volvía a nadar nunca — se quedaba
        # caminando por el fondo hasta ahogarse. Es lo que se veía al probar.
        #
        # No se fuerza desde HURT ni DYING: ahí el motor está contando un
        # golpe y pisarle el estado se lleva por delante la animación y la
        # invulnerabilidad.
        # Y NO se le devuelve a nado si ya está saliendo. `SwimmingState`
        # entrega el control a `JumpingState` con un impulso fuerte cuando el
        # jugador rompe la superficie: ése es el salto para salir del agua. Sin
        # esta condición, la reentrada lo cancelaba en el mismo fotograma y el
        # jugador quedaba atrapado en el pozo dando botes.
        saliendo = jugador.position.y <= float(agua.top)
        if not saliendo and estado in (
                PlayerState.IDLE, PlayerState.WALKING,
                PlayerState.FALLING, PlayerState.JUMPING,
                PlayerState.CROUCHING):
            nado = SwimmingState()
            jugador._change_state_instance(nado)
            # `SwimmingState.enter` fija la superficie en "donde entré menos
            # 16 px", que sólo vale si se entró justo por arriba. Con el borde
            # real del pozo, el salto para salir del agua ocurre donde tiene
            # que ocurrir y no a la profundidad a la que se hundió.
            nado._surface_y = float(agua.top) - 16.0
            estado = PlayerState.SWIMMING

        if estado != PlayerState.SWIMMING:
            return

        im = self.input

        # ── Nadar hacia arriba: mantener SALTO ─────────────────
        #
        # Va LO PRIMERO, y el orden es el fallo que tuvo esto.
        #
        # Estaba más abajo, después del `return` de «ya está en la superficie».
        # O sea: funcionaba mientras el jugador estuviera hundido, y dejaba de
        # funcionar exactamente donde hacía falta —flotando a ras del brocal—,
        # porque ahí la función ya había vuelto. El jugador flotaba en el agua
        # pudiendo bucear y sin poder salir. Es lo mismo que "no puedo salir
        # del agua" dos veces seguidas: la primera vez arreglé el cálculo y lo
        # puse en el sitio equivocado.
        #
        # HALLAZGO DEL MOTOR (el que hacía falta tapar)
        # Las cuentas de `SwimmingState` no cierran entre ellas. El impulso de
        # nado pone la velocidad en -120, pero el clamp del propio estado la
        # recorta a -60 al fotograma siguiente; y está limitado a UNO por
        # entrada al agua (`_swim_boosts < 1`). Con -60 y su gravedad reducida
        # (240 px/s²) el jugador sube 60²/(2·240) = 7,5 px. La condición para
        # salir es subir 24 px sobre donde entró. 7,5 nunca llega a 24: la
        # salida del agua es inalcanzable con los números del propio estado.
        #
        # No hay que vencer el clamp: basta con volver a pedir la subida cada
        # fotograma en vez de una sola vez.
        if im is not None and im.is_action_held(Action.JUMP):
            jugador.velocity.y = min(jugador.velocity.y, -70.0)
            return

        # Bucear sigue siendo del jugador: con abajo pulsado no hay flotación.
        if im is not None and im.is_action_held(Action.CROUCH):
            return

        linea = float(agua.top) + self.CALADO
        hundido = jugador.position.y - linea
        if hundido <= 0.0:
            return                      # ya está en la superficie: no empuja

        # 1 en el fondo del pozo, 0 en la línea de flotación.
        peso = min(1.0, hundido / max(1.0, float(agua.height)))

        # Se fija una VELOCIDAD de ascenso, no una aceleración. Con
        # aceleración esto no funcionaba y el motivo es de orden de
        # ejecución: este método corre después de `super().update()`, y al
        # fotograma siguiente `player.update()` resuelve la colisión ANTES de
        # mover, poniendo la velocidad vertical a cero en cuanto el jugador
        # toca el lecho. El empuje acumulado se perdía entero antes de llegar
        # a levantarlo. Midiéndolo: se quedaba clavado en y=624, el fondo.
        #
        # Fijando la velocidad de destino y acercándose a ella de forma suave
        # el resultado no depende de cuánta velocidad traía ni de si el suelo
        # se la borró: cada fotograma vuelve a apuntar hacia arriba.
        objetivo = -(20.0 + 55.0 * peso)        # 20 px/s arriba, 75 en el fondo

        # Bucear sigue siendo del jugador: con abajo pulsado no hay flotación y
        # `SwimmingState` lo hunde como siempre. Sin esta salida, el empuje le
        # quitaría el control de la profundidad y el pozo dejaría de tener
        # fondo al que bajar.

        # Se IMPONE la velocidad de ascenso en vez de acercarse a ella poco a
        # poco. La primera versión interpolaba y no servía, por orden de
        # ejecución: este método corre después de `super().update()`, y al
        # fotograma siguiente la resolución de colisión pone la velocidad
        # vertical a cero en cuanto el jugador toca el lecho. Cada acercamiento
        # gradual se borraba antes de acumular nada y el jugador se quedaba
        # clavado en y=624 —el fondo del pozo— rebotando un píxel.
        #
        # `min` y no asignación directa: si viene subiendo más rápido —por el
        # impulso de nado o por un rebote— se respeta su velocidad.
        jugador.velocity.y = min(jugador.velocity.y, objetivo)

        # Y apoyado en el lecho, además, se despega moviendo la posición: ahí
        # la velocidad no sobrevive al fotograma y lo único que el resolutor
        # respeta es dónde está.
        if jugador.is_grounded:
            jugador.position.y -= 90.0 * dt
            jugador.rect.y = int(jugador.position.y)

    # ── La trampa ───────────────────────────────────────────────
    def _descender_a_la_catacumba(self) -> None:
        """La tierra se abre, el juez cura al portador, y emerge Paburu.

        El orden importa y es de guion, no técnico: primero se apaga —el
        jugador pierde de vista lo que tiene alrededor—, después suena, la
        tierra lo traga, y recién entonces aparece. Si Paburu apareciera con
        la sala iluminada, el momento se gastaría antes de empezar.
        """
        stage = self._stage_data
        if stage is None:
            return

        # 0. Silencio de arriba (R2-4, AUD-475). El aviso de lore que el
        # jugador estaba leyendo en la superficie seguía en pantalla DENTRO de
        # la catacumba, con su caja de 70 px tapando la entrada del jefe: el
        # momento que el nivel entero prepara, con un cartel del camposanto
        # encima. La caja del motor se cierra sola por tiempo, pero el
        # descenso no espera a nadie.
        #
        # Se apaga con `hide()`, la API pública de `MessageBox`, y no tocando
        # su `_visible`: es lo mismo que hace el propio motor cuando el
        # jugador cierra un mensaje.
        if self._msg_box is not None:
            self._msg_box.hide()

        # 1. Negro.
        self._lighting.ambient_brightness = LUZ_TRAMPA
        if self._farol is not None:
            self._farol.intensity = 0.0

        # 2. El sonido raro y la sacudida.
        #
        # Dos sonidos y no uno: el cambio de fase da el golpe grave —la tierra
        # que se abre— y la ola de Paburu, que es la voz del jefe, entra
        # encima. Uno solo se lee como "pasó algo"; los dos juntos se leen
        # como "algo se abrió, y estaba esperando".
        self.context.event_bus.emit(Events.SFX_BOSS_PHASE_CHANGE)
        self.context.event_bus.emit(Events.SFX_BOSSES_PABURU_WAVE)
        if self._camera is not None:
            self._camera.apply_shake(amplitude=4.0, duration=0.6)

        # 3. El descenso y el encuadre.
        cat = self._cementerio.descender(
            jugador=self._player,
            mapa_ancho=self._camera._map_w if self._camera else 4160,
            mapa_alto=self._camera._map_h if self._camera else 1312,
            ancho_vista=settings.INTERNAL_WIDTH,
            alto_vista=settings.INTERNAL_HEIGHT,
        )
        self._sostener_encuadre()
        self._reubicar_guardianes(cat)

        # 4. El juez cura al portador. No es un regalo: es la condición del
        # juicio. La pelea de cuatro formas está calibrada contra la barra
        # llena, y un tribunal que remata heridos no prueba nada (lore §128:
        # Paburu quiere PROBAR a los portadores, no destruirlos). Con esto la
        # pelea es la misma llegue el jugador entero o arrastrándose.
        jugador = self._player
        if jugador is not None:
            jugador._state.health = jugador.max_health
            self.context.event_bus.emit(
                Events.SHOW_MESSAGE,
                text="EL JUEZ CURA AL PORTADOR", duration=2.5,
            )

        # 5. Y emerge.
        self._invocar_a_paburu(cat)

    # ── El vigilante del altar (#45) ────────────────────────────
    #: Segundos entre picadas: ser visto castiga, no acribilla. El cono
    #: tarda ~1,5 s en llenar la alerta, así que el ciclo completo deja
    #: respirar — el sigilo es opcional, no obligatorio.
    RESPIRO_VIGILANTE = 5.0

    def _actualizar_vigilante(self, dt: float) -> None:
        """El castigo del `Guard` del camino final.

        El motor solo SUBE el nivel de alerta del cono (AUD-285: los conos
        ven, la consecuencia es de cada escenario). Aquí la consecuencia
        habla el idioma del nivel: ser visto convoca una picada de gavilán
        —el eco del guardián que el jugador va a conocer en la Forma 2— y
        el aviso llega con la caracola, la misma del llamado. El vigilante
        no persigue ni bloquea: cobra el peaje y vuelve a su barrido.
        """
        from src.framework.ecs import Alerta, Transform
        from src.stages.boss_paburu.ataques_guardianes import PicadaDelGavilan

        jugador = self._player
        mundo = getattr(self, "_mundo", None)
        if jugador is None:
            return
        self._vigilante_cd = max(0.0, self._vigilante_cd - dt)
        if (mundo is not None and self._vigilante_cd <= 0.0
                and not self._cementerio.sellado):
            for entidad, alerta in mundo.cada(Alerta):
                if alerta.nivel < alerta.umbral_alerta:
                    continue
                t = mundo.obtener(entidad, Transform)
                origen = (pygame.Vector2(t.rect.center) if t is not None
                          else pygame.Vector2(jugador.rect.centerx,
                                              jugador.rect.top - 160))
                self._ecos_del_vigilante.append(PicadaDelGavilan(
                    origen, pygame.Vector2(jugador.hurtbox.center)))
                self._sfx_propio("sfx_bosses_paburu_llamado", 0.55)
                self._vigilante_cd = self.RESPIRO_VIGILANTE
                if not self._vigilante_avisado:
                    # Solo la primera vez: el segundo picotazo ya se
                    # explica solo, y repetir el cartel sería regaño.
                    self._vigilante_avisado = True
                    self.context.event_bus.emit(
                        Events.SHOW_MESSAGE,
                        text="EL VIGILANTE DEL CAMPOSANTO TE HA VISTO",
                        duration=2.2,
                    )
                break
        # Las picadas en vuelo: mismas reglas que los ecos de la ronda.
        vivos = []
        for eco in self._ecos_del_vigilante:
            eco.update(dt)
            if not eco.alive:
                continue
            r = eco.rect
            if (r is not None and not eco.ya_golpeo
                    and r.colliderect(jugador.hurtbox)):
                jugador.apply_damage(eco.DANIO, r.center)
                eco.ya_golpeo = True
            vivos.append(eco)
        self._ecos_del_vigilante = vivos

    def _sfx_propio(self, nombre: str, volumen: float = 1.0) -> None:
        """Reproduce una muestra propia del stage por su nombre de archivo.

        SFX propios (mejora B): el `SoundBank` del motor carga TODO lo que
        haya en `assets/sfx/` por nombre, así que basta con dejar los .wav
        en `assets/sfx/bosses/` y pedirlos aquí — sin eventos nuevos ni una
        línea de framework. `play_sfx` respeta el mute y los volúmenes del
        usuario; sin gestor de audio (arneses de prueba), silencio.
        """
        audio = getattr(self.context, "audio_manager", None)
        if audio is not None:
            audio.play_sfx(nombre, volume=volumen)

    def _invocar_a_paburu(self, circulo: Any, con_intro: bool = True) -> None:
        """Crea el jefe en la catacumba y lanza su aparición.

        El boss se construye acá y no se coloca en el TMX a propósito: si
        estuviera en el mapa existiría desde que carga el nivel —con su barra
        de vida en el HUD y sus ataques contando— mientras el jugador todavía
        camina por el primer tramo a tres mil píxeles de distancia. Y, sobre
        todo, estaría en un sitio fijo, que es justo lo que este nivel no
        quiere.
        """
        boss = BossPaburu(pygame.Vector2(circulo.boss_pos))
        # El boss necesita el Player COMPLETO, no el `Rect` que guarda
        # `EnemyBase`: para resolver el punto débil hace falta el
        # `active_hitbox`, que dice dónde pegó el jugador y no dónde está.
        boss.player_obj = self._player
        boss.set_event_bus(self.context.event_bus)
        # La arena real del combate: la Sala del Juicio. La leen el clamp
        # del motor y los motores de la Forma 3 (persecución y órbita
        # necesitan saber contra qué paredes rebotar y hasta dónde derivar).
        cat = self._cementerio.catacumba
        if cat is not None:
            boss.set_arena_bounds(cat.interior)
        # SFX propios (mejora B): el jefe recibe el reproductor de la
        # escena — sus momentos únicos (llamado, juicio, veredicto, sello)
        # suenan con sus propias muestras sin tocar los `Events` del motor.
        boss.reproducir_sfx = self._sfx_propio
        if self._stage_data is not None:
            self._stage_data.entity_list.append(boss)

        if not con_intro:
            # Reintento: la presentación ya se vio y volver a pasarla sería
            # castigo. `_fin_intro` deja la sala exactamente en estado de
            # combate — forma 1, vida llena, luz de fase, moradores fuera.
            self._fin_intro()
            return
        self._intro_vista = False
        self.lanzar_entrada()

    # ── Parry → devolver el ataque ──────────────────────────────
    #: Radio alrededor del jugador donde una parada alcanza un ataque.
    #: El parry dura 0.2 s, así que el margen espacial compensa que el
    #: temporal es durísimo.
    ALCANCE_PARRY = 34

    def _revisar_parry(self) -> None:
        """Una parada acertada **devuelve** el ataque contra Paburu.

        POR QUÉ HACE FALTA
        El motor trae todas las piezas y ninguna está conectada:

          · `ParryState` existe y funciona en el jugador.
          · Cuando una parada acierta, `EnemyBase._check_player_contact`
            marca `player._parry_success = True`.
          · `EnemyBase.stun(duración)` existe y es pública.
          · `EnemyState.STUNNED` tiene prioridad alta, y `BossBase` cancela
            el ataque en curso al entrar en ese estado — su propio comentario
            dice que "una parada acertada tiene que interrumpir al jefe o
            parar no sirve para nada".

        Pero **ninguna línea de todo `src/` llama a `stun()`**. La parada
        desvía al enemigo, enciende la bandera, y ahí se acaba: el jefe sigue
        su ataque como si nada. Verificado con `grep -rn "\\.stun(" src/`.

        QUÉ HACE EL MOTOR, Y QUÉ FALTABA
        Desde AUD-206 el motor **sí** aturde al parar: `enemy_base.py` llama
        a `stun(PARRY_STUN_DURATION)` y el jefe sale a RECOVER, su ventana de
        castigo. Eso ya no hay que resolverlo acá.
        Lo que el motor sigue sin hacer es **devolver** el ataque: contra un
        proyectil hace `p._expired = True` —la bala desaparece— y contra el
        contacto empuja. Parry significa desviar de vuelta, no borrar, y ésa
        es la diferencia entre defenderse y responder.

        Acá el ataque **cambia de dueño**: la piedra sale disparada hacia
        Paburu y el rayo se refleja desde el punto donde se paró. Los dos
        pasan a dañarlo a él.

        Los ataques de Paburu no van por el sistema de proyectiles del
        motor —son suyos, viven en `form1_attacks`—, así que el parry del
        framework nunca los ve. Esto se resuelve del lado del stage, sin
        tocar el framework.
        """
        jugador = self._player
        boss = self._boss_ref()
        if jugador is None or boss is None or not boss.is_alive:
            return
        if not getattr(jugador, "_parry_active", False):
            return
        if getattr(jugador, "_parry_window", 0.0) <= 0.0:
            return

        zona = jugador.hurtbox.inflate(self.ALCANCE_PARRY, self.ALCANCE_PARRY)
        centro = pygame.Vector2(boss.rect.center)
        devolvio = False

        for p in boss._projectiles:
            if p.alive and not p.devuelta and p.rect.colliderect(zona):
                p.devolver(centro)
                devolvio = True

        for b in boss._beams:
            if b.alive and not b.devuelto and not b.is_telegraphing and b.hits(zona):
                b.devolver(pygame.Vector2(jugador.hurtbox.center))
                devolvio = True

        # Forma 2: la ola y los ecos también se paran. El pulso NO —es un
        # anillo que nace del propio jefe y devolvérselo no significa nada—,
        # y por eso la respuesta a ese ataque es alejarse y no parar. Que no
        # todos los ataques se paren es lo que hace que parar sea una
        # decisión y no el botón que se pulsa siempre.
        for a in (*boss._olas, *boss._ecos):
            if not a.alive or a.devuelta or a.is_telegraphing:
                continue
            r = a.rect
            if r is not None and r.colliderect(zona):
                a.devolver(centro)
                devolvio = True

        # EL JUICIO (Forma 4, EL OFRECIMIENTO): la parada de la firma.
        # `toca` y no `rect`: el anillo cubre la sala entera y el rect daría
        # una parada válida a media pantalla del frente real de la onda.
        juicio = getattr(boss, "_juicio", None)
        if (juicio is not None and juicio.alive and not juicio.devuelto
                and not juicio.is_telegraphing and juicio.toca(zona)):
            juicio.devolver(centro)
            devolvio = True

        # Forma 3: las esquirlas de la Pepita y la lágrima de la Perla.
        # La lágrima es EL parry de 3B: devuelta, fuerza la ventana de la
        # Perla fuera de turno (lo resuelve `_revisar_devueltos` del jefe).
        for a in (*boss._esquirlas, *boss._lagrimas):
            if not a.alive or a.devuelta or a.is_telegraphing:
                continue
            r = a.rect
            if r is not None and r.colliderect(zona):
                a.devolver(centro)
                devolvio = True

        # Los guardianes: SOLO el orbe de la serpiente se para — es el único
        # proyectil de la ronda. La embestida es un cuerpo y la picada un
        # clavado: sus respuestas son saltar y esquivar. Devuelto, el orbe no
        # va contra Paburu sino contra su DUEÑA, y la tumba: parar bien acá
        # compra seis segundos de silencio en la ronda.
        for a in self._ataques_guardianes:
            if (hasattr(a, "devolver") and a.alive and not a.devuelta
                    and not a.is_telegraphing):
                r = a.rect
                if r is not None and r.colliderect(zona):
                    duena = self._guardianes[a.guardian_idx]
                    a.devolver(duena.pos())
                    devolvio = True

        if devolvio:
            # Se cierra la ventana para que una sola parada no devuelva
            # media pantalla de ataques, y se avisa como el motor avisa.
            jugador._parry_active = False
            jugador._parry_window = 0.0
            jugador._parry_success = True
            self.context.event_bus.emit(
                Events.VFX_PARRY, pos=(jugador.position.x, jugador.position.y),
            )

    # ── La ronda de los guardianes ──────────────────────────────
    #: Cadencia por guardián, en segundos. Largas a propósito: la restricción
    #: de diseño es «moderado, no imposible» — los guardianes suman presión,
    #: no la protagonizan. Con la rotación de turno, el jugador ve UN eco
    #: cada ~2,5 s como máximo, y nunca dos en vuelo a la vez.
    CADENCIA_GUARDIANES = {"venado": 8.5, "serpiente": 7.0, "gavilan": 9.5}
    #: Primer ataque de cada uno tras activarse la ronda: escalonados para
    #: que la Forma 2 no reciba tres avisos simultáneos en el segundo cero.
    ARRANQUE_GUARDIANES = (3.0, 6.0, 9.0)
    #: Cuánto queda tumbado un guardián al que le devuelven el orbe.
    CAIDA_GUARDIAN = 6.0
    #: En la Forma 3 la reliquia ya es intensa: la ronda respira más lento.
    FACTOR_FORMA_3 = 1.4
    #: Silencio mínimo entre un eco y el siguiente, además de las cadencias
    #: individuales. Sin él, tres relojes de 7-9,5 s rotando dan un eco cada
    #: ~3,5 s — sumado a los tres ataques propios de Paburu, la pantalla no
    #: descansaba nunca. El arnés lo midió: 11 ecos en 40 s; con el respiro
    #: quedan ~7, que es la banda del diseño.
    #:
    #: AUD-483 lo subió de 4,5 a 5,5. No es un retoque de gusto: el respiro
    #: viejo se calibró cuando la embestida del venado NO alcanzaba al
    #: jugador de pie —uno de los tres ecos hacía cero daño siempre—, así que
    #: el presupuesto medido era el de una ronda con dos ataques. Arreglada
    #: la altura, el mismo respiro le sacaba 5,5 de vida a un maniquí quieto
    #: en 40 s y rompía la regla declarada («moderado, no imposible», tope
    #: 5,0 en el arnés). Con 5,5 s el conteo de ecos no cambia (7 en 40 s,
    #: dentro de la banda 4-10) y el daño vuelve a 4,5: se paga el arreglo
    #: donde se rompió el equilibrio, no bajándole el daño al venado — que es
    #: lo que le da su peso a un ataque que hay que saltar.
    RESPIRO_RONDA = 5.5

    def _reubicar_guardianes(self, circulo: Any) -> None:
        """Reparte a los tres sobre el cielo de la arena sellada.

        Las bases de `cargar()` son de la vista de 800 px pegada al origen
        del mapa; en el cementerio la pelea puede caer a 3.000 px de ahí y
        los espíritus quedaban fuera de pantalla justo cuando el lore los
        hace aparecer. Se reparten asimétricos (22 %, 50 %, 78 % del ancho,
        alturas distintas) para no leerse como adorno repetido — la misma
        razón por la que sus frecuencias de deriva no coinciden.
        """
        arena = circulo.arena
        cielo = self._cementerio.encuadre.y
        posiciones = (
            # Sesgados hacia la SALA (el 80 % izquierdo del interior): la
            # antecámara es el zaguán de entrada y tiene el techo más bajo —
            # un espíritu derivando ahí quedaría metido en la roca.
            #
            # R22 — OCHENTA PÍXELES MÁS ABAJO. Del video: «la vida debería
            # estar en otro lugar porque los espíritus de la segunda forma
            # no se ven bien». Las celdas de los custodios miden 120 px de
            # alto y se dibujan centradas: con la base a cielo+108, la
            # cabeza del espíritu llegaba a ~28 px de pantalla — DETRÁS de
            # la barra del jefe y del medidor del ulti. La barra es del
            # motor y no se muda; los espíritus sí: su franja baja al
            # espacio vacío entre el HUD (~100) y las repisas (~424).
            (arena.left + arena.width * 0.16, cielo + 232),
            (arena.left + arena.width * 0.40, cielo + 188),
            (arena.left + arena.width * 0.64, cielo + 212),
        )
        for g, base in zip(self._guardianes, posiciones, strict=False):
            g.reubicar(base)
        self._ataques_guardianes.clear()
        self._gua_timers = list(self.ARRANQUE_GUARDIANES)
        self._gua_turno = 0
        self._gua_respiro = 0.0

    def _epilogo_de_la_sala(self, dt: float) -> None:
        """La sala responde al veredicto (GDD §204, el epílogo).

        Dos cosas, y las dos leen el resultado:

          · LOS CUSTODIOS SE DESPIDEN — uno a uno (venado, serpiente,
            gavilán, 0,6 s entre reverencias): se inclinan y se disuelven
            hacia ARRIBA. No es derrota: esperaron siglos este reencuentro.
          · LA LUZ DA EL VEREDICTO — absuelto, la sala amanece hasta plena
            luz y los braseros arden altos; juzgado, la penumbra vuelve y
            los fuegos se achican. El cuarto entero es el último mensaje,
            antes de que ningún texto lo diga.
        """
        boss = self._boss_ref()
        if boss is None or not getattr(boss, "en_epilogo", False):
            return
        if not getattr(self, "_epilogo_arrancado", False):
            self._epilogo_arrancado = True
            self._ataques_guardianes.clear()
            for i, g in enumerate(self._guardianes):
                g.despedirse(retraso=0.8 + i * 0.6)
            # El mismo cuerno que los convocaba a pelear ahora los despide:
            # la última vez que suena, y suena para dejarlos ir.
            self._sfx_propio("sfx_bosses_paburu_llamado", 0.8)
        # La rampa de luz: 1,2 s hacia el veredicto.
        objetivo = 1.0 if boss.absuelto else 0.55
        paso = dt / 1.2
        amb = self._lighting.ambient_brightness
        if abs(amb - objetivo) > 0.005:
            self._lighting.ambient_brightness = (
                min(objetivo, amb + paso) if amb < objetivo
                else max(objetivo, amb - paso))
        for luz in self._braziers:
            meta = 1.0 if boss.absuelto else 0.25
            luz.intensity += (meta - luz.intensity) * min(1.0, dt * 2.5)

    def _procesion_de_guardianes(self) -> None:
        """El llamado antiguo (ANCIENT_CALL, Forma 4).

        Paburu llama y los tres custodios responden: los caidos se levantan
        y la sala entera se cruza en procesion, tres pasadas a alturas
        DISTINTAS escalonadas 0,45 s, para que siempre haya pasillo. Es la
        ronda de la Forma 2 convertida en coreografia: el mismo eco del
        venado, ahora a tres voces.
        """
        from src.stages.boss_paburu.ataques_guardianes import EmbestidaDelVenado

        cat = self._cementerio.catacumba
        if cat is None or not self._guardianes:
            return
        # AUD-497 — el llamado los trae de vuelta a la sala; la bandera es lo
        # que hace que se VEAN (la rampa de presencia) mientras cruzan, y que
        # se desvanezcan cuando la procesión termina.
        self._procesion_en_curso = True
        for g in self._guardianes:
            g.levantar()
        # AUD-483 — las tres pasadas colgaban del mismo error que la embestida
        # suelta: con `suelo` un tile por encima del piso real y la más baja a
        # −58, NINGUNA tocaba al jugador de pie. La procesión era un espectáculo
        # sin consecuencias.
        #
        # `suelo` pasa a ser el piso de verdad (`interior.bottom`, la línea de
        # los pies) y la escalera arranca en −20, la altura que sí alcanza el
        # hurtbox de pie. Las otras dos suben de 50 en 50 px en vez de 64: con
        # bandas de 26 px de alto, [-33,-7] / [-83,-57] / [-133,-107] deja
        # pasillos de 24 px entre pasada y pasada y un techo libre por encima
        # de −133, o sea sigue habiendo por dónde esquivar saltando — que es
        # lo que exige el diseño de ANCIENT_CALL: coreografía, no muro.
        suelo = cat.interior.bottom
        alturas = (suelo - 20, suelo - 70, suelo - 120)
        for i, altura in enumerate(alturas):
            self._ataques_guardianes.append(EmbestidaDelVenado(
                pygame.Vector2(cat.interior.center), cat.interior,
                hacia_derecha=(i % 2 == 0), altura_y=altura,
                retraso=i * 0.45,
            ))
        self._gua_lanzados += 3

    def _ronda_de_guardianes(self, dt: float) -> None:
        """Los guardianes pelean desde la Forma 2 (DISENO §3.4).

        Cada uno ataca con el eco de su firma —embestida, orbe, picada— con
        cadencia larga y de a uno. El orbe devuelto con parry TUMBA a su
        dueña seis segundos: la única ventana que el jugador puede fabricar
        contra la ronda, y cuesta la maniobra más difícil que tiene.
        """
        from src.stages.boss_paburu.ataques_guardianes import (
            EmbestidaDelVenado,
            OrbeDeLaSerpiente,
            PicadaDelGavilan,
        )

        boss = self._boss_ref()
        jugador = self._player
        arena = self._cementerio.catacumba
        if (boss is None or jugador is None or arena is None
                or not self._cementerio.sellado):
            return
        if not boss.is_alive or boss.is_transitioning:
            # La transición de forma limpia la ronda igual que el jefe limpia
            # sus proyectiles: el jugador debe poder mirar el cambio.
            self._ataques_guardianes.clear()
            return
        if getattr(boss, "ofrecimiento_activo", False):
            # La ceremonia: los custodios se arrodillan (caen sin ataque, y
            # largo — los levanta el desenlace, no el reloj) y la ronda
            # guarda silencio. La única pregunta en vuelo es el juicio.
            self._ataques_guardianes.clear()
            if any(not g.esta_caido for g in self._guardianes):
                # Solo el primer fotograma: después ya están de rodillas
                # y `tumbar` únicamente les renueva el plazo.
                self._sfx_propio("sfx_bosses_paburu_custodio_cae", 0.6)
            for g in self._guardianes:
                g.tumbar(30.0)
            return
        if boss.current_phase < 1 or self._presencia < 0.55:
            return

        # AUD-497 — la ronda de ecos es de la FORMA 2 y de nadie más. En la 3
        # los custodios se han retirado (duelo de uno contra uno) y en la 4 el
        # Espíritu ya trae cuatro patrones propios: sumarles tres ecos era el
        # «atacan muchísimo más, es casi imposible» del playtest. Cuando en la
        # Forma 4 los llama `ANCIENT_CALL`, su ataque es la PROCESIÓN
        # coreografiada —pasillos de esquive, no muro—, que se arma aparte en
        # `_procesion_de_guardianes`.
        if boss.current_phase != FORM_MASK:
            # En la Forma 4 la procesión SÍ vive aquí (sus embestidas están en
            # la misma lista), así que no se limpia mientras quede alguna en
            # vuelo; cuando se acaban, los custodios se van.
            if self._procesion_en_curso:
                self._ataques_guardianes[:] = [
                    a for a in self._ataques_guardianes if a.alive]
                if not self._ataques_guardianes:
                    self._procesion_en_curso = False
                return
            self._ataques_guardianes.clear()
            return

        # 1. Los ecos en vuelo: avanzar, golpear, expirar.
        vivos = []
        for a in self._ataques_guardianes:
            a.update(dt)
            if not a.alive:
                continue
            if getattr(a, "devuelta", False):
                # El orbe devuelto persigue a su dueña, que deriva.
                g = self._guardianes[a.guardian_idx]
                a.retarget(g.pos())
                if a.pos.distance_to(g.pos()) < 30.0:
                    g.tumbar(self.CAIDA_GUARDIAN)
                    self.context.event_bus.emit(
                        Events.VFX_BUBBLE, pos=(a.pos.x, a.pos.y),
                    )
                    # La única ventana que el jugador puede fabricarse
                    # contra la ronda merece oírse: campanita menor
                    # descendente, casi un suspiro.
                    self._sfx_propio("sfx_bosses_paburu_custodio_cae")
                    continue
            else:
                r = a.rect
                if (r is not None and not getattr(a, "ya_golpeo", False)
                        and r.colliderect(jugador.hurtbox)):
                    jugador.apply_damage(a.DANIO, r.center)
                    if hasattr(a, "ya_golpeo"):
                        a.ya_golpeo = True      # la embestida sigue de largo
                    else:
                        continue                # el orbe se consume al pegar
            vivos.append(a)
        self._ataques_guardianes[:] = vivos

        # 2. La cadencia: rota el turno y lanza de a uno, con respiro global.
        factor = self.FACTOR_FORMA_3 if boss.current_phase >= 2 else 1.0
        for i in range(len(self._gua_timers)):
            self._gua_timers[i] = max(0.0, self._gua_timers[i] - dt)
        self._gua_respiro = max(0.0, getattr(self, "_gua_respiro", 0.0) - dt)
        if self._ataques_guardianes or not self._guardianes:
            return
        if self._gua_respiro > 0.0:
            return
        idx = self._gua_turno % len(self._guardianes)
        g = self._guardianes[idx]
        if self._gua_timers[idx] > 0.0 or g.esta_caido:
            # Si el del turno no está listo, no se le roba el turno: la
            # ronda espera. Es lo que la hace legible — y lo que hace que
            # tumbar a un guardián compre silencio de verdad.
            return
        origen = g.pos()
        centro_j = pygame.Vector2(jugador.hurtbox.center)
        if g.nombre == "venado":
            ataque = EmbestidaDelVenado(
                origen, arena.interior,
                hacia_derecha=centro_j.x >= arena.interior.centerx,
            )
        elif g.nombre == "serpiente":
            ataque = OrbeDeLaSerpiente(origen, centro_j, guardian_idx=idx)
        else:
            ataque = PicadaDelGavilan(origen, centro_j)
        self._ataques_guardianes.append(ataque)
        self._gua_lanzados += 1
        self._gua_timers[idx] = self.CADENCIA_GUARDIANES[g.nombre] * factor
        self._gua_respiro = self.RESPIRO_RONDA
        self._gua_turno += 1

    def _saltar_intro(self) -> None:
        """ESC salta la entrada. Deja la sala como si hubiera terminado."""
        if self._intro is not None:
            self._intro._active = False
        self._fin_intro()

    # ── La señal de la boca (R2-8, reapuntada por D-01) ─────────
    #: Cuántas brasas suben por la boca de la catacumba.
    BRASAS_DEL_CIRCULO = 12
    #: Cuánto suben antes de apagarse, en píxeles.
    ALTURA_BRASA = 56.0

    def _faro(self) -> pygame.Rect | None:
        """Sobre qué arden las brasas. D-01 cambió la respuesta.

        Nacieron en R2-8 para señalar el círculo sorteado: «me volvió a
        tirar a Paburu» — el sorteo funcionaba, pero sin anticipación se
        sentía arbitrario. Al quitarse el sorteo esa pregunta desapareció, y
        la señal se reapunta a la que ocupa su lugar: **dónde se baja**.

        En un camposanto de 4160 px a oscuras, un faro al final del camino
        es la diferencia entre caminar y caminar HACIA algo. Y sigue siendo
        diegético: por la boca sube el humo de los braseros de la sala.
        """
        boca = getattr(self._cementerio, "boca", None)
        if boca is not None and boca.width:
            return boca
        # Mapa de la era del sorteo: la señal vuelve a donde estaba.
        elegido = self._cementerio.elegido
        return elegido.arena if elegido is not None else None

    # ── Las estrellas que titilan (D-01·J) ──────────────────────
    #: Cuántas estrellas respiran sobre el camposanto.
    ESTRELLAS = 46

    def _armar_estrellas(self) -> None:
        """El cielo deja de ser una foto.

        Lo que más le gustó a Alejandro del 4-1 del profesor: «las
        estrellas que brillaban». La nuestra es una capa fina sobre el
        cielo del parallax: cada estrella tiene su fase y su ritmo, unas
        pocas titilan fuerte (las que uno mira) y el resto apenas late.
        Van con parallax propio, más lento que el fondo: son lo más lejano
        que hay.
        """
        import random as _random

        rng = _random.Random("cielo-del-camposanto")
        self._estrellas = [{
            "x": rng.uniform(0.0, 840.0),
            "y": rng.uniform(6.0, 235.0),
            "ritmo": rng.uniform(0.4, 1.7),
            "fase": rng.uniform(0.0, 6.28),
            "brillo": rng.uniform(0.35, 1.0),
            "viva": rng.random() < 0.22,     # las que titilan de verdad
        } for _ in range(self.ESTRELLAS)]

    def _dibujar_estrellas(self, surface: pygame.Surface,
                           off: pygame.Vector2) -> None:
        """Titileo aditivo sobre la franja del cielo. Se calla ante la luna."""
        if self._cementerio.sellado or not getattr(self, "_estrellas", None):
            return
        import math

        t = self._reloj_brasas
        ancho = surface.get_width()
        for e in self._estrellas:
            sx = int(e["x"] - off.x * 0.22) % (ancho + 40) - 20
            sy = int(e["y"])
            if not (0 <= sx < ancho and 0 <= sy < surface.get_height()):
                continue
            fondo = surface.get_at((sx, sy))
            if fondo[0] + fondo[1] + fondo[2] > 330:
                continue                     # la luna y las nubes claras mandan
            if e["viva"]:
                k = max(0.0, math.sin(t * e["ritmo"] * 2.6 + e["fase"]))
                k = k * k * k                # destello corto, apagón largo
            else:
                k = 0.55 + 0.45 * math.sin(t * e["ritmo"] + e["fase"])
            nivel = int(190 * e["brillo"] * k)
            if nivel < 12:
                continue
            surface.set_at((sx, sy), (min(255, fondo[0] + nivel),
                                      min(255, fondo[1] + nivel),
                                      min(255, fondo[2] + nivel + nivel // 6)))
            if e["viva"] and nivel > 120:    # la cruz de destello
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    px, py = sx + dx, sy + dy
                    if 0 <= px < ancho and 0 <= py < surface.get_height():
                        f2 = surface.get_at((px, py))
                        surface.set_at((px, py),
                                       (min(255, f2[0] + nivel // 3),
                                        min(255, f2[1] + nivel // 3),
                                        min(255, f2[2] + nivel // 3)))

    # ── La niebla del camposanto (D-01·B) ───────────────────────
    #: Cuántos jirones se arrastran por el suelo. Catorce en 4160 px es un
    #: jirón cada ~300: se cruzan sin formar una alfombra.
    JIRONES = 14
    #: Alto de la banda donde vive la niebla, medido desde la losa hacia
    #: arriba. 56 px es la cintura del jugador (32 px de alto): la niebla
    #: tiene que quedar POR DEBAJO de la cara o deja de ser suelo mojado y
    #: pasa a ser humo.
    BANDA_NIEBLA = 56
    #: Gris azulado de luna en agua. Nunca cálido: lo cálido son las brasas,
    #: y dos fuentes de calor compitiendo aplanan la escena.
    NIEBLA = (128, 138, 162)

    def _apagar_el_velo_del_motor(self) -> None:
        """Apaga el velo plano del clima `fog`. **Eran las «monedas».**

        Reportado como «esas monedas que pusimos se ven como cuadros». No
        eran monedas ni las pusimos nosotros: el clima `fog` del motor pinta
        un velo liso de (180,180,190) a alfa 80 sobre la pantalla entera,
        ANTES de que el mapa de luz multiplique. Donde la luz es más fuerte
        el velo sobrevive a la multiplicación y donde es débil se apaga, así
        que el velo deja de ser velo y **dibuja el mapa de luz**: una fila de
        discos claros y redondos flotando a la altura del pecho. Medido: con
        `_overlay_alpha` a 0 desaparecen los 786 px de la zona y no cambia
        nada más.

        Y como velo tampoco servía: un gris cálido y uniforme sobre un nivel
        que decidió ser noche azul (AUD-463) le come el tinte a toda la
        imagen — el mismo error del «color caca», por otra puerta.

        No se quita el clima del TMX: `fog` es lo que ESTE nivel es, el
        calificador lo lee de ahí y la maquinaria del motor sigue coherente.
        Lo que se apaga es su dibujo, y en su lugar va `_dibujar_niebla`.
        """
        clima = getattr(self, "_weather", None)
        if clima is not None:
            clima._overlay_alpha = 0

    def _armar_niebla(self) -> None:
        """Los jirones: forma, altura y deriva. Determinista.

        Niebla de cementerio, no niebla de pantalla: se arrastra **por el
        suelo**, entre las lápidas, y por eso es una banda baja de elipses
        muy anchas y muy chatas en vez de un velo. Cada jirón lleva su propia
        anchura, altura y velocidad: con la misma, catorce jirones son uno
        repetido catorce veces y el ojo lo caza al segundo.
        """
        import random as _random

        rng = _random.Random("niebla-del-camposanto")
        ancho = self._camera._map_w if self._camera is not None else 4160
        self._jirones_de_niebla = [{
            "x": ancho * i / self.JIRONES + rng.uniform(-60.0, 60.0),
            "y": SUPERFICIE - rng.uniform(4.0, float(self.BANDA_NIEBLA)),
            "w": rng.uniform(90.0, 220.0),
            "h": rng.uniform(9.0, 18.0),
            # Muy lenta y en los dos sentidos: una niebla que corre se lee
            # como humo, y el aire de un camposanto no va a ninguna parte.
            "v": rng.choice((-1.0, 1.0)) * rng.uniform(2.5, 7.0),
            "alfa": rng.uniform(0.22, 0.46),
            "fase": rng.uniform(0.0, 6.28),
        } for i in range(self.JIRONES)]
        if self._jiron is None:
            self._jiron = self._pincel_de_niebla(64, 16)

    @staticmethod
    def _pincel_de_niebla(w: int, h: int) -> pygame.Surface:
        """Una elipse con caída suave, para estirar por jirón.

        Se dibuja una sola vez y se escala: catorce elipses con degradado
        calculadas cada fotograma costarían más que todo el resto de la capa
        del stage junta.
        """
        pincel = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w / 2.0, h / 2.0
        for y in range(h):
            for x in range(w):
                dx = (x - cx) / cx
                dy = (y - cy) / cy
                d = dx * dx + dy * dy
                if d >= 1.0:
                    continue
                k = (1.0 - d) ** 1.6
                pincel.set_at((x, y), (255, 255, 255, int(255 * k)))
        return pincel

    def _dibujar_niebla(self, surface: pygame.Surface,
                        off: pygame.Vector2, dt_reloj: float) -> None:
        """La niebla, arrastrándose. Sólo arriba: la cripta tiene su aire.

        Va después de la luz a propósito. La niebla real es lo único de un
        camposanto de noche que **tiene luz propia** —dispersa la luna— y
        multiplicarla por la penumbra la haría desaparecer justo donde debe
        verse. Por eso el alfa es bajo: lo que no puede es brillar.
        """
        if self._cementerio.sellado or self._jiron is None or not self._jirones_de_niebla:
            return
        import math
        vista = surface.get_rect()
        ancho = float(self._camera._map_w if self._camera is not None else 4160)
        for j in self._jirones_de_niebla:
            # La deriva es de mundo, no de cámara: la niebla sigue moviéndose
            # aunque el jugador esté quieto, que es lo que la hace estar viva.
            j["x"] = (j["x"] + j["v"] * dt_reloj) % ancho
            # Y respira: el ancho late despacio, como el aire sobre el agua.
            pulso = 1.0 + 0.12 * math.sin(j["fase"] + self._reloj_brasas * 0.5)
            w = max(8, int(j["w"] * pulso))
            h = max(4, int(j["h"]))
            r = pygame.Rect(int(j["x"] - w / 2 - off.x),
                            int(j["y"] - h / 2 - off.y), w, h)
            if not vista.colliderect(r):
                continue
            jiron = pygame.transform.smoothscale(self._jiron, (w, h))
            jiron.fill((*self.NIEBLA, int(255 * j["alfa"])),
                       special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(jiron, r.topleft)

    # ── El descenso por el mecate (D-01·I, segunda vuelta) ──────
    #: Deslizamiento por defecto cuando el portador no toca nada, px/s.
    #: Más despacio que la `velocidad` del mecate (78, la que declara el
    #: TMX y usa el motor al sostener ABAJO): bajar sin tocar nada es
    #: contemplar el descenso; sostener ABAJO lo apura.
    DESLIZ_DEL_MECATE = 70.0

    def _cable_de_la_tirolesa(self):
        """La `Tirolesa` real del mapa, cacheada. `None` si no la trae."""
        if getattr(self, "_cable_cacheado", False):
            return self._cable
        from src.framework.ecs.components import Tirolesa
        cables = [c for grupo in getattr(self._stage_data, "componentes", ())
                  for c in grupo if isinstance(c, Tirolesa)]
        self._cable = cables[0] if cables else None
        self._cable_cacheado = True
        return self._cable

    def _sujetar_la_tirolesa(self) -> None:
        """R18 — el jinete NO se hunde: se re-engancha al cable cada paso.

        Bug del motor, medido con el arnés: `TirolesaState` anula la
        velocidad al ENTRAR pero no cada fotograma, y la posición la
        avanza él mismo mientras la integración de física sigue sumando
        gravedad — el jinete se hundía ~80 px por debajo del cable a
        media bajada (y en este mapa, eso lo metía al foso por debajo de
        la losa). El arreglo del stage: mientras dure el estado, el
        cuerpo se re-proyecta al punto más cercano del segmento (la
        misma `punto_mas_cercano` que usa el motor para enganchar) y la
        velocidad vertical se apaga. Saltar para soltarse sigue intacto:
        el salto CAMBIA de estado en su mismo fotograma y esto solo
        actúa sobre quien sigue colgado. Anotado para reportar al
        profesor con la reproducción.
        """
        jugador = self._player
        if jugador is None:
            return
        from src.framework.entities.states import TirolesaState
        if not isinstance(getattr(jugador, "_state_instance", None),
                          TirolesaState):
            return
        cable = self._cable_de_la_tirolesa()
        if cable is None:
            return
        punto = cable.punto_mas_cercano(pygame.Vector2(jugador.rect.center))
        jugador.rect.centerx = int(punto.x)
        jugador.rect.top = int(punto.y)
        jugador.position.update(float(jugador.rect.x), float(jugador.rect.y))
        jugador.velocity.y = 0.0

    def _mecate_del_foso(self):
        """La `Liana` real del mecate, cacheada. `None` si el mapa no la trae."""
        if getattr(self, "_mecate_cacheado", False):
            return self._mecate
        from src.framework.ecs.components import Liana
        lianas = [c for grupo in getattr(self._stage_data, "componentes", ())
                  for c in grupo if isinstance(c, Liana)]
        self._mecate = (max(lianas, key=lambda c: c.rect.height)
                        if lianas else None)
        self._mecate_cacheado = True
        return self._mecate

    def _guiar_el_descenso(self, dt: float) -> None:
        """En el foso, el portador se agarra del mecate — DE VERDAD.

        Historia en dos reportes de Alejandro. El primero («al bajar como
        que no baja, solo aparece abajo») se atendió recortando la caída
        a 150 px/s; el segundo enseñó que no bastaba: «sigue bajando y no
        pasa por la liana, solo cae». Y claro que caía: el recorte
        cambiaba la VELOCIDAD y no el ESTADO — el sprite seguía en
        FALLING, sin tocar la cuerda, y una caída lenta sigue leyéndose
        como caída.

        El motor ya trae el estado correcto —`TrepandoState`, el de las
        lianas— pero pide la tecla G, y nadie descubre una tecla en medio
        de una caída. Así que este mecate agarra solo. La advertencia del
        framework («una liana que te atrapa al pasar corriendo es una
        trampa») no aplica aquí: es la única liana del nivel y cuelga
        DENTRO de un pozo al que no se pasa por delante — se cae adentro
        a propósito. Una vez colgado manda el jugador: ARRIBA sube, ABAJO
        baja al paso del motor, SALTO se suelta — y la cuerda no lo
        vuelve a cazar en esta visita: la caída elegida se respeta. Sin
        tocar nada, el mecate resbala suave hacia el juicio: ~10 s de ver
        la luz de la boca quedarse arriba.
        """
        cat = self._cementerio.catacumba
        jugador = self._player
        if cat is None or jugador is None or not cat.foso.width:
            return
        from src.framework.entities.states import FallingState, TrepandoState

        foso = cat.foso
        r = jugador.rect
        actual = getattr(jugador, "_state_instance", None)
        colgado = isinstance(actual, TrepandoState)
        # R18 — EL MECATE NO CAZA AL QUE VA EN LA TIROLESA. El cable
        # cruza por encima del foso y el estado del motor deja crecer
        # `velocity.y` durante el viaje (la gravedad se acumula aunque
        # la posición la mande el cable): para este método eso parecía
        # «cayendo dentro del foso» y el agarre automático lo arrancaba
        # del cable — medido: el jinete acababa colgado del mecate POR
        # DEBAJO de la losa sellada, rito bypasseado.
        from src.framework.entities.states import TirolesaState
        if isinstance(actual, TirolesaState):
            return
        # Sellada la arena ya no se agarra a nadie — pero al que VIENE
        # colgado se le termina el descenso: la pelea se arma con el
        # portador a media cuerda (el disparador vive a 160 px del suelo)
        # y cortar aquí lo dejaba colgado en el aire con Paburu emergiendo
        # debajo. Medido: se quedaba a 94 px del piso, sin resbalar.
        if self._cementerio.sellado and not colgado:
            return

        # El último tramo se cae: el mecate llega al suelo de la antecámara
        # (el TMX lo exige sin tramo muerto), así que su rect COLISIONA con
        # el jugador incluso de pie en el fondo y el motor nunca soltaría
        # solo — quedarse colgado a ras de piso con la pelea por armar es
        # un casi-softlock. A 36 px del suelo las manos sueltan.
        if colgado and r.bottom >= cat.interior.bottom - 36:
            jugador._change_state_instance(FallingState())
            self._mecate_soltado = True
            return

        en_el_foso = (foso.left - 4 <= r.centerx <= foso.right + 4
                      and r.top > SUPERFICIE
                      and r.bottom < cat.interior.bottom - 12)
        if not en_el_foso:
            # Fuera del pozo la memoria del agarre se limpia: la próxima
            # visita vuelve a agarrar.
            self._mecate_soltado = False
            self._mecate_agarrado = False
            return

        if colgado:
            self._mecate_agarrado = True
            # El deslizamiento por defecto: sin ARRIBA ni ABAJO, el mecate
            # resbala — no es un andamio. Se pregunta al MANDO y no a la
            # velocidad (la primera versión miraba `velocity.y == 0.0` y el
            # orden interno del fotograma la dejaba en falso la mayoría de
            # las veces: medido, el resbalón salía a 13 px/s en vez de 70).
            # Y se empuja la posición, no la velocidad, porque el estado
            # del motor la pisa antes de la siguiente integración.
            im = self.input
            trepando = im is not None and (
                im.is_action_held(Action.MOVE_UP)
                or im.is_action_held(Action.MOVE_DOWN)
                or im.is_action_held(Action.CROUCH))
            if not trepando:
                jugador.position.y += self.DESLIZ_DEL_MECATE * dt
                jugador.rect.y = int(jugador.position.y)
            return

        if getattr(self, "_mecate_agarrado", False):
            # Estaba colgado y ya no lo está: saltó. Esta visita no re-agarra.
            self._mecate_soltado = True
            self._mecate_agarrado = False

        if getattr(self, "_mecate_soltado", False):
            return
        if getattr(jugador, "is_grounded", False) or jugador.velocity.y <= 0:
            return
        mecate = self._mecate_del_foso()
        if mecate is None:
            return
        jugador._change_state_instance(TrepandoState(mecate))

    # ── Las ánimas del camposanto (D-01·H, idea de Alejandro) ───
    #: Cuántas tumbas tienen huésped. Nueve en 4160 px: presencia, no plaga.
    ANIMAS = 9
    #: El verde espectral. Frío a propósito: lo cálido es del fuego del
    #: juez, y las ánimas no son de él — todavía.
    ANIMA = (168, 226, 204)

    def _armar_animas(self) -> None:
        """Las tumbas habitadas: dónde, con qué ritmo, con qué cara.

        Idea de Alejandro tras jugar el 4-1 del profesor: caras que asoman
        en las lápidas y espíritus que se levantan. El ciclo de cada ánima
        es casi todo silencio — primero DOS OJOS que se encienden sobre la
        lápida (la cara), y recién después el espíritu se alza y se
        deshace. Cada una con su periodo y su fase: nueve relojes
        distintos, para que el camposanto nunca repita el mismo segundo.
        """
        import random as _random

        rng = _random.Random("animas-del-camposanto")
        self._animas = [{
            "x": 130.0 + i * 430.0 + rng.uniform(-70.0, 70.0),
            "periodo": rng.uniform(11.0, 17.0),
            "fase": rng.uniform(0.0, 17.0),
            "vaiven": rng.uniform(1.5, 3.5),
            "alto": rng.uniform(58.0, 82.0),
        } for i in range(self.ANIMAS)]
        if self._pincel_anima is None:
            self._pincel_anima = self._tejer_anima()

    @staticmethod
    def _tejer_anima() -> pygame.Surface:
        """El espíritu: un velo con cara, no una bola de luz.

        Se dibuja con alfa normal (no aditivo) para poder tener OJOS
        oscuros — un blit aditivo sólo sabe sumar luz y la cara
        desaparecería. La cola se deshace en jirones desiguales.
        """
        import math

        w, h = 18, 26
        velo = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            for x in range(w):
                dx = (x - w / 2.0) / (w / 2.0)
                if y < 12:                       # la cabeza: casi redonda
                    dy = (y - 7.0) / 7.0
                    d = dx * dx + dy * dy
                    if d < 1.0:
                        a = int(150 * (1.0 - d) ** 1.3)
                        velo.set_at((x, y), (208, 236, 222, a))
                else:                            # la cola: velo que se abre
                    u = (y - 12.0) / (h - 12.0)
                    ancho = 1.0 - u * 0.55
                    ondul = 0.18 * math.sin(y * 1.1 + x * 0.4)
                    if abs(dx) < ancho + ondul:
                        a = int(120 * (1.0 - u) ** 1.6)
                        if (x * 7 + y * 3) % 5 == 0:
                            a = a // 3           # jirones
                        velo.set_at((x, y), (188, 224, 210, a))
        for ex in (6, 11):                       # los ojos, huecos
            for dy in (0, 1):
                velo.set_at((ex, 6 + dy), (10, 14, 12, 235))
                velo.set_at((ex + 1, 6 + dy), (10, 14, 12, 235))
        return velo

    def _dibujar_animas(self, surface: pygame.Surface,
                        off: pygame.Vector2) -> None:
        """El ciclo: silencio → la cara en la lápida → el espíritu se alza."""
        if self._cementerio.sellado or self._pincel_anima is None:
            return
        import math

        vista = surface.get_rect()
        t_global = self._reloj_brasas
        for a in self._animas:
            u = ((t_global + a["fase"]) % a["periodo"]) / a["periodo"]
            sx = int(a["x"] - off.x)
            if not (-40 <= sx <= vista.width + 40):
                continue
            if u < 0.72:
                continue
            if u < 0.80:                         # LA CARA en la lápida
                k = (u - 0.72) / 0.08
                brillo = int(220 * (k if k < 0.7 else 1.0))
                for ex in (-3, 2):
                    for dx in (0, 1):
                        surface.set_at(
                            (sx + ex + dx, int(536 - off.y)),
                            (min(255, brillo), 255, 230))
                        surface.set_at(
                            (sx + ex + dx, int(537 - off.y)),
                            (brillo // 2, brillo, brillo * 3 // 4))
                continue
            # EL ESPÍRITU se levanta y se deshace.
            v = (u - 0.80) / 0.20
            alza = a["alto"] * v
            sy = int(544 - alza - off.y)
            vaiven = math.sin(t_global * 1.8 + a["fase"]) * a["vaiven"]
            velo = self._pincel_anima.copy()
            velo.fill((255, 255, 255, int(255 * (1.0 - v))),
                      special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(velo, (int(sx - 9 + vaiven), sy))

    # ── Las nubes que derivan (D-01·K, pedido de Alejandro) ─────
    #: Pocas y grandes: siete nubes en pantalla son un cielo con clima;
    #: veinte son una textura.
    NUBES = 7

    def _armar_nubes(self) -> None:
        """Nubes bajas de noche, derivando solas sobre el camposanto.

        Vienen del concept que le encantó a Alejandro («me encantó ese
        remate, se ve salido, las nubes… ¿será que se pueden poner nubes
        moviendo?»). Cada una es un pincel propio —tres a cinco panzas de
        elipse, borde de luna arriba— y deriva a su paso aunque el
        jugador esté quieto, igual que la niebla del suelo: el cielo
        respira. Van con parallax entre las estrellas y el fondo: más
        cerca que lo más lejano, más lejos que las lápidas.
        """
        import random as _random

        rng = _random.Random("nubes-del-camposanto")
        self._nubes = []
        for _ in range(self.NUBES):
            w = rng.randint(110, 210)
            h = rng.randint(20, 34)
            pincel = pygame.Surface((w, h), pygame.SRCALPHA)
            # Muchas panzas chicas y translúcidas que se acumulan, con la
            # base plana (las nubes cargan el peso abajo) y el lomo
            # accidentado. La primera versión eran 3-5 elipses grandes a
            # alfa 26: en pantalla, platillos apilados — se vio en la
            # captura, no en el código.
            for k in range(12):
                pw = rng.randint(w // 5, w // 2)
                ph = rng.randint(max(3, h // 3), h - 2)
                px = rng.randint(0, max(1, w - pw))
                py = (h - ph) if k % 2 else rng.randint(0, max(1, h - ph))
                pygame.draw.ellipse(pincel, (46, 56, 84, 15),
                                    pygame.Rect(px, py, pw, ph))
            # El filo de luna sobre el lomo, antes del desenfoque.
            arriba = pincel.get_bounding_rect()
            if arriba.width:
                pygame.draw.ellipse(
                    pincel, (104, 120, 158, 22),
                    pygame.Rect(arriba.x + arriba.w // 4, arriba.y,
                                arriba.w // 2, max(3, arriba.h // 3)))
            # Bajar y volver a subir de resolución difumina los bordes:
            # una nube con el canto duro es un plato, no vapor.
            chica = pygame.transform.smoothscale(pincel, (w // 2, h // 2))
            pincel = pygame.transform.smoothscale(chica, (w, h))
            self._nubes.append({
                "pincel": pincel,
                "x": rng.uniform(0.0, 1100.0),
                "y": rng.uniform(18.0, 168.0),
                "v": rng.uniform(2.5, 7.5),
                "par": rng.uniform(0.28, 0.44),
                "w": w,
            })

    def _dibujar_nubes(self, surface: pygame.Surface, off: pygame.Vector2,
                       dt_reloj: float) -> None:
        """Sobre las estrellas y bajo todo lo demás. La luna puede taparse:
        una nube cruzando la luna es exactamente la clase de instante que
        este cielo existe para regalar."""
        if self._cementerio.sellado or not self._nubes:
            return
        ancho = surface.get_width()
        for n in self._nubes:
            n["x"] += n["v"] * dt_reloj
            campo = ancho + n["w"] * 2
            sx = int(n["x"] - off.x * n["par"]) % campo - n["w"]
            sy = int(n["y"])
            if sx > ancho:
                continue
            surface.blit(n["pincel"], (sx, sy))

    # ── #49 · LA FORMA DEL ÁNIMA: el ulti viste la máscara ──────
    #: Segundos que dura el préstamo de los velados tras el estallido.
    #: Seis: lo bastante para verse transformado peleando, lo bastante
    #: poco para que siga siendo un MOMENTO y no un segundo personaje.
    PRESTAMO_DEL_ANIMA = 6.0

    def _vestir_la_mascara(self) -> None:
        """El estallido del ulti pone la máscara tilawa al portador.

        El diseño (aprobado sobre el concept generado): el ulti se carga
        GOLPEANDO — cada golpe despierta a los que fueron velados — y al
        estallar no es el portador el que se vuelve fuerte: son las
        ánimas las que le prestan su fuego. Por eso la transformación es
        VERDE ÁNIMA y jamás dorada: el oro es el idioma del juez, y
        vestirse del juez sería vestirse del jefe. Solo aspecto — el
        daño, la duración y la física del ulti son los del motor, y el
        balance (P-02) no se toca.
        """
        if self._player is None:
            return
        self._transformacion = self.PRESTAMO_DEL_ANIMA
        self._asegurar_frames_del_anima()
        if self._frames_del_anima:
            self._player._sprite_frames = self._frames_del_anima
        # El estallido: el fuego envuelve el CUERPO ENTERO de golpe.
        # (R20 — «el ánima sale de todo el cuerpo, no solo de la
        # cabeza», con el concept al lado. La v1 nacía toda en r.top.)
        import random as _random
        r = self._player.rect
        rng = _random.Random(int(self._reloj_brasas * 997))
        for _ in range(22):
            self._jirones_del_portador.append({
                "dx": rng.uniform(-10.0, 10.0),
                "dy": rng.uniform(-6.0, float(r.height)),
                "vy": rng.uniform(-34.0, -58.0),
                "fase": rng.uniform(0.0, 6.28),
                "vida": rng.uniform(0.5, 1.0),
                "edad": 0.0,
                "x": float(r.centerx), "y": float(r.top),
            })

    def _asegurar_frames_del_anima(self) -> None:
        """Consigue (una vez por jugador) los fotogramas transformados.

        PRIMERO las hojas talladas (`anima_player_*.png`, del generador
        del héroe): son la Forma del concept aprobado — la máscara de
        madera con los tres glifos, los ojos de almendra encendidos, la
        espiral en la boca, el cuerpo a cuero con el filo horneado y la
        levitación con su charco de luz. El re-teñido píxel a píxel se
        conserva como RED DE SEGURIDAD: si las hojas faltan (o el que
        está puesto no es el héroe), la transformación sigue existiendo.
        """
        jugador = self._player
        base = getattr(jugador, "_sprite_frames", None)
        if not base or base is self._frames_del_anima:
            return
        if self._frames_del_portador is base and self._frames_del_anima:
            return                              # ya están tallados
        self._frames_del_portador = base
        talladas = self._cargar_hojas_del_anima()
        if talladas is not None:
            self._frames_del_anima = talladas
            return
        self._frames_del_anima = {
            estado: [self._tenir_de_anima(f) for f in cuadros]
            for estado, cuadros in base.items()
        }

    def _cargar_hojas_del_anima(self) -> dict | None:
        """Las hojas talladas de la Forma, si el disco las trae todas."""
        if getattr(self, "_hojas_anima_cacheadas", None) is not None:
            return self._hojas_anima_cacheadas
        carpeta = settings.ASSETS_DIR / "sprites" / "heroe_tilawa"
        if not carpeta.exists():
            return None
        from src.engine.utils.asset_loader import AssetLoader
        from src.framework.entities.player import (
            _PLAYER_SPRITE_MAP,
            SPRITE_H,
            SPRITE_W,
        )
        frames: dict = {}
        for estado, (archivo, _n) in _PLAYER_SPRITE_MAP.items():
            ruta = carpeta / f"anima_{archivo}"
            if not ruta.exists():
                return None     # hoja faltante: mejor el teñido completo
            frames[estado] = AssetLoader.load_sprite_sheet(
                str(ruta), SPRITE_W, SPRITE_H)
        self._hojas_anima_cacheadas = frames
        return frames

    #: El verde del filo y de los ojos. El mismo de las ánimas — es SU fuego.
    FILO_DEL_ANIMA = (168, 226, 204)

    @classmethod
    def _tenir_de_anima(cls, cuadro: pygame.Surface) -> pygame.Surface:
        """Talla un fotograma del portador transformado, píxel a píxel.

        Tres gestos, los del concept aprobado: la ropa se apaga a hierro
        azulado CONSERVANDO el sombreado (se escala la luminancia, no se
        pinta plano); la cabeza se vuelve la máscara de madera oscura con
        las rendijas verdes; y todo el contorno gana un filo de luz ánima
        — la luz que no está en la escena, porque viene de los muertos.
        Ni un píxel cálido: el racionador de oro también rige aquí.
        """
        s = cuadro.convert_alpha()
        w, h = s.get_size()
        mask = pygame.mask.from_surface(s, 8)
        if not mask.count():
            return s
        rects = mask.get_bounding_rects()
        caja = rects[0].unionall(rects[1:]) if rects else s.get_rect()
        techo = caja.top
        filo = cls.FILO_DEL_ANIMA
        for y in range(h):
            for x in range(w):
                c = s.get_at((x, y))
                if c[3] < 8:
                    continue
                lum = (c[0] + c[1] + c[2]) / 3.0
                en_cabeza = y - techo < 10
                if en_cabeza:
                    # La madera de la máscara: oscura, apenas tibia, lejos
                    # del umbral del oro (r<150 siempre).
                    nc = (int(46 + lum * 0.16), int(34 + lum * 0.12),
                          int(26 + lum * 0.08))
                else:
                    # Hierro azulado: la sombra manda, el azul respira.
                    nc = (int(14 + lum * 0.10), int(15 + lum * 0.13),
                          int(22 + lum * 0.22))
                # ¿Es borde? Un vecino transparente = filo de luz ánima.
                borde = False
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h) or \
                            s.get_at((nx, ny))[3] < 8:
                        borde = True
                        break
                if borde:
                    nc = (int(nc[0] * 0.45 + filo[0] * 0.55),
                          int(nc[1] * 0.45 + filo[1] * 0.55),
                          int(nc[2] * 0.45 + filo[2] * 0.55))
                s.set_at((x, y), (*nc, c[3]))
        # Las rendijas de los ojos, encendidas. No a una altura fija: la
        # silueta del portador REMATA EN PUNTA, y a `techo+4` los ojos
        # caían en píxeles transparentes y no se pintaban (se vio en el
        # zoom de la captura: quedaban los ojos pardos del sprite). Se
        # busca la primera fila de la cabeza con carne suficiente (≥8 px)
        # y ahí se abren las rendijas, simétricas al ancho REAL de esa
        # fila.
        for fila in range(techo, min(techo + 12, h)):
            xs = [x for x in range(w) if s.get_at((x, fila))[3] >= 8]
            if len(xs) >= 8:
                oy = fila + 2
                cx = (xs[0] + xs[-1]) // 2
                paso = max(2, (xs[-1] - xs[0]) // 4)
                for ex in (cx - paso - 1, cx + paso - 1):
                    for dx in range(2):
                        for p, col in (((ex + dx, oy), (196, 255, 226)),
                                       ((ex + dx, oy + 1), (120, 210, 178))):
                            if 0 <= p[0] < w and 0 <= p[1] < h and \
                                    s.get_at(p)[3] >= 8:
                                s.set_at(p, (*col, 255))
                break
        return s

    def _desvestir_la_mascara(self) -> None:
        """El préstamo se acaba: el portador vuelve a su ropa."""
        self._transformacion = 0.0
        jugador = self._player
        if jugador is not None and self._frames_del_portador and \
                getattr(jugador, "_sprite_frames", None) is self._frames_del_anima:
            jugador._sprite_frames = self._frames_del_portador

    def _latir_la_transformacion(self, dt: float) -> None:
        """El tiempo del préstamo y los jirones que lo visten."""
        jugador = self._player
        if self._transformacion > 0.0 and jugador is not None:
            self._transformacion -= dt
            if self._transformacion <= 0.0:
                self._desvestir_la_mascara()
            else:
                # Si el motor reconstruyó al jugador (p. ej. respawn), los
                # fotogramas tallados quedaron en el jugador viejo: se
                # vuelve a tallar sobre el nuevo en vez de vestirlo a
                # ciegas con los del muerto.
                if getattr(jugador, "_sprite_frames", None) is not \
                        self._frames_del_anima:
                    self._asegurar_frames_del_anima()
                    if self._frames_del_anima:
                        jugador._sprite_frames = self._frames_del_anima
                # El goteo de jirones: el aura del concept, viva.
                import random as _random
                rng = _random.Random(int(self._reloj_brasas * 1499))
                r = jugador.rect
                # R20 — el fuego nace de TODO el cuerpo («el ánima sale
                # de todo el cuerpo, no solo de la cabeza»): el punto de
                # partida se reparte por la silueta entera, con un poco
                # más de fuelle hacia los hombros/cabeza para que las
                # lenguas altas del concept sigan existiendo. 38/s: al
                # repartirse en el doble de cuerpo, con 26 quedaba ralo.
                if rng.random() < dt * 38.0:
                    dy = rng.uniform(-6.0, float(r.height))
                    self._jirones_del_portador.append({
                        "dx": rng.uniform(-9.0, 9.0),
                        "dy": dy,
                        "vy": rng.uniform(-30.0, -52.0),
                        "fase": rng.uniform(0.0, 6.28),
                        # Los que nacen bajos viven un poco menos: una
                        # llama del tobillo que subiera dos cuerpos se
                        # leería como columna de humo, no como aura.
                        "vida": rng.uniform(0.55, 1.05)
                                * (1.0 - 0.3 * max(0.0, dy) / max(1.0, float(r.height))),
                        "edad": 0.0,
                        "x": float(r.centerx), "y": float(r.top),
                    })
        # Los jirones envejecen aunque el préstamo haya acabado: el aura
        # no se corta a cuchillo, se apaga.
        vivos = []
        for p in self._jirones_del_portador:
            p["edad"] += dt
            if p["edad"] < p["vida"]:
                vivos.append(p)
        self._jirones_del_portador = vivos

    def _dibujar_el_anima_del_portador(self, surface: pygame.Surface,
                                       off: pygame.Vector2) -> None:
        """El aura: jirones verdes que suben del portador y se deshacen.

        Anclados al jugador AL DIBUJAR (no a donde nacieron): el aura
        viaja con él, como en el concept — llamas que le pertenecen, no
        humo que deja atrás. Aditivo, como las brasas: con GPU les toca
        el bloom, que a un fuego frío también le queda bien.
        """
        if not self._jirones_del_portador or self._player is None:
            return
        import math
        r = self._player.rect
        t = self._reloj_brasas
        for p in self._jirones_del_portador:
            u = p["edad"] / p["vida"]
            alza = -p["vy"] * p["edad"]
            vaiven = math.sin(t * 3.1 + p["fase"]) * 2.2
            sx = int(r.centerx + p["dx"] + vaiven - off.x)
            sy = int(r.top + p["dy"] - alza - off.y)
            k = (1.0 - u) ** 1.5
            base = (int(self.FILO_DEL_ANIMA[0] * k * 0.7),
                    int(self.FILO_DEL_ANIMA[1] * k * 0.85),
                    int(self.FILO_DEL_ANIMA[2] * k * 0.75))
            alto = max(1, int(6 * (1.0 - u * 0.6)))
            for dy in range(alto):
                fade = 1.0 - dy / (alto + 1)
                col = (int(base[0] * fade), int(base[1] * fade),
                       int(base[2] * fade))
                px, py = sx, sy + dy
                if 0 <= px < surface.get_width() and \
                        0 <= py < surface.get_height():
                    fondo = surface.get_at((px, py))
                    surface.set_at((px, py),
                                   (min(255, fondo[0] + col[0]),
                                    min(255, fondo[1] + col[1]),
                                    min(255, fondo[2] + col[2])))

    # ── El letrero de la tirolesa ───────────────────────────────
    def _dibujar_letrero_de_la_tirolesa(self, surface: pygame.Surface,
                                        off: pygame.Vector2) -> None:
        """«G — AGARRARSE», flotando junto al arranque del cable.

        La tirolesa era contenido muerto: agarra con la tecla G y nada en
        el juego lo dice — Alejandro llegó al final del nivel sin saber
        que existía la tecla. Se le quitó la liana-tutorial de la entrada
        (no enseñaba: se saltaba a pie), así que el letrero vive donde la
        duda ocurre: al lado del cable, solo cuando el portador está
        cerca, latiendo despacio. El mecate no lo necesita: agarra solo.
        """
        if self._cementerio.sellado or self._player is None:
            return
        try:
            from src.framework.ecs.components import Tirolesa
        except Exception:
            return
        if not hasattr(self, "_letrero_tirolesa"):
            cables = [c for grupo in getattr(self._stage_data, "componentes", ())
                      for c in grupo if isinstance(c, Tirolesa)]
            self._letrero_tirolesa = cables[0].origen if cables else None
            fuente = pygame.font.Font(None, 15)
            texto = fuente.render("G  AGARRARSE", False, self.FILO_DEL_ANIMA)
            sombra = fuente.render("G  AGARRARSE", False, (10, 10, 16))
            self._letrero_pincel = (texto, sombra)
        if self._letrero_tirolesa is None:
            return
        import math
        origen = self._letrero_tirolesa
        j = self._player.rect
        if (pygame.Vector2(j.centerx, j.centery) -
                pygame.Vector2(origen.x, origen.y)).length() > 150.0:
            return
        texto, sombra = self._letrero_pincel
        bob = math.sin(self._reloj_brasas * 2.2) * 2.0
        sx = int(origen.x - texto.get_width() / 2 - off.x)
        sy = int(origen.y - 30 + bob - off.y)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(sombra, (sx + dx, sy + dy))
        surface.blit(texto, (sx, sy))

    def _dibujar_aviso_del_ulti(self, surface: pygame.Surface,
                                off: pygame.Vector2) -> None:
        """«ULTI LISTO — Z+X», flotando sobre el portador tras pulsar 8.

        Mismo lenguaje que el letrero de la tirolesa (el color del ánima,
        la sombra de cuatro puntos, el vaivén lento): la tecla 8 llena la
        barra en silencio, y sin este aviso el que la pulsa se queda
        mirando la pantalla sin saber que ahora Z+X ya responde. Se
        desvanece en su último medio segundo.
        """
        restante = getattr(self, "_aviso_ulti", 0.0)
        if restante <= 0.0 or self._player is None:
            return
        # Si la barra ya no está llena es que el ulti ESTALLÓ: el aviso
        # mentiría («listo» sobre una barra vacía) — muere en el acto.
        # Verificado en captura: sin esto seguía en pantalla sobre el
        # portador ya transformado.
        if not self._player.ultimate_listo:
            self._aviso_ulti = 0.0
            return
        if not hasattr(self, "_aviso_ulti_pincel"):
            fuente = pygame.font.Font(None, 15)
            texto = fuente.render("ULTI LISTO — Z+X", False,
                                  self.FILO_DEL_ANIMA)
            sombra = fuente.render("ULTI LISTO — Z+X", False, (10, 10, 16))
            self._aviso_ulti_pincel = (texto, sombra)
        import math
        texto, sombra = self._aviso_ulti_pincel
        j = self._player.rect
        bob = math.sin(self._reloj_brasas * 2.2) * 2.0
        sx = int(j.centerx - texto.get_width() / 2 - off.x)
        sy = int(j.top - 22 + bob - off.y)
        # El spawn está pegado al borde izquierdo y ahí es donde más se
        # pulsa el 8: el aviso se queda dentro de la pantalla.
        sx = max(2, min(sx, surface.get_width() - texto.get_width() - 4))
        capa = pygame.Surface(
            (texto.get_width() + 2, texto.get_height() + 2), pygame.SRCALPHA)
        for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
            capa.blit(sombra, (dx, dy))
        capa.blit(texto, (1, 1))
        if restante < 0.5:
            capa.set_alpha(int(255 * restante / 0.5))
        surface.blit(capa, (sx - 1, sy - 1))

    # ── El portador con rostro (#50, pedido de Alejandro) ───────
    def _vestir_al_portador(self) -> None:
        """El héroe del concept como personaje jugable — SOLO en este stage.

        Alejandro generó el arte del portador (pelo azabache, bufanda
        parda, capa rasgada, correaje, vendas, botas) y pidió el cambio
        de forma. Dos restricciones deciden el cómo:

          · `assets/sprites/player/*` los REGENERA `generate_all_assets.py`
            (código del profesor): reemplazarlos ahí es perder el trabajo
            en la próxima regeneración — la lección del tileset. Las hojas
            del héroe viven en `assets/sprites/heroe_tilawa/` (las talla
            `tools/gen_heroe_tilawa.py`) y aquí sólo se cambia el dict
            `_sprite_frames`: el mismo truco de las veladoras y la Forma
            del Ánima, cero motor, y los demás stages conservan su sprite.
          · El motor dibuja al jugador en 32×32: el héroe es la lectura
            del concept a esa escala — misma silueta, mismas prendas,
            misma paleta.

        La Forma del Ánima (#49) talla su versión DEL QUE ESTÉ PUESTO:
        como este vestido ocurre antes, el ulti transforma al héroe.
        """
        jugador = self._player
        if jugador is None:
            return
        carpeta = settings.ASSETS_DIR / "sprites" / "heroe_tilawa"
        if not carpeta.exists():
            return
        from src.engine.utils.asset_loader import AssetLoader
        from src.framework.entities.player import (
            _PLAYER_SPRITE_MAP,
            SPRITE_H,
            SPRITE_W,
        )
        if getattr(self, "_frames_del_heroe", None) is None:
            frames = {}
            for estado, (archivo, _n) in _PLAYER_SPRITE_MAP.items():
                ruta = carpeta / archivo
                if not ruta.exists():
                    return          # hoja faltante: mejor el sprite del motor
                frames[estado] = AssetLoader.load_sprite_sheet(
                    str(ruta), SPRITE_W, SPRITE_H)
            self._frames_del_heroe = frames
        jugador._sprite_frames = self._frames_del_heroe
        # Los fotogramas del Ánima se tallaron (si se tallaron) sobre la
        # ropa vieja: invalidarlos para que el próximo ulti transforme
        # al héroe y no al sprite del motor.
        self._frames_del_portador = None
        self._frames_del_anima = None
        # Y EL RETRATO del HUD — la costura que quedaba: el motor carga
        # `assets/ui/portrait_*.png` aparte, así que con el héroe vestido
        # la esquina seguía enseñando la cara del personaje viejo. El
        # dict `_portraits` es un atributo plano del HUD: se le inyectan
        # los retratos del héroe (mismo trato que las veladoras).
        hud = getattr(self, "_hud", None)
        if hud is not None and getattr(hud, "_portraits", None) is not None:
            destino = getattr(hud, "_portrait_sprite_rect", None)
            for variante in ("normal", "hurt", "critical", "dead"):
                ruta = carpeta / f"portrait_{variante}.png"
                if not ruta.exists():
                    continue
                cara = pygame.image.load(str(ruta)).convert_alpha()
                if destino is not None:
                    cara = pygame.transform.scale(cara, destino.size)
                hud._portraits[variante] = cara

    # ── Las veladoras (D-01·F, pedido de Alejandro) ─────────────
    def _encender_las_veladoras(self) -> None:
        """Los checkpoints dejan de ser «palos con círculos».

        El sprite del checkpoint es del MOTOR y es genérico. Pero
        `Checkpoint.draw` prefiere `_sprite`/`_grey_sprite` si existen —
        así que la escena se los inyecta: una veladora encendida para el
        activado y una apagada para el que espera. Ni una línea de motor:
        es el mismo trato que la piel de las mecánicas (AUD-465).

        En un camposanto tilawa el punto de guardado ES una veladora: el
        fuego que alguien dejó por sus muertos. Encenderla al pasar es un
        gesto que ya significa lo que el guardado hace — «aquí se veló por
        vos».
        """
        stage = getattr(self, "_stage_data", None)
        if stage is None or not getattr(stage, "checkpoints", None):
            return
        encendida = self._moldear_veladora(con_llama=True)
        apagada = self._moldear_veladora(con_llama=False)
        for cp in stage.checkpoints:
            cp._sprite = encendida
            cp._grey_sprite = apagada

    @staticmethod
    def _moldear_veladora(con_llama: bool) -> pygame.Surface:
        """Una vela de cera sobre su platito de piedra, 16×32."""
        s = pygame.Surface((16, 32), pygame.SRCALPHA)
        CERA = (216, 208, 188) if con_llama else (164, 158, 148)
        CERA_SOMBRA = (176, 166, 146) if con_llama else (128, 122, 114)
        # El platito.
        for x in range(2, 14):
            s.set_at((x, 29), (94, 90, 100, 255))
            s.set_at((x, 30), (66, 63, 74, 255))
        for x in range(4, 12):
            s.set_at((x, 28), (126, 122, 130, 255))
        # El cuerpo de cera, con sus chorreones.
        for y in range(13, 28):
            for x in range(5, 11):
                s.set_at((x, y), (*CERA, 255) if x < 9 else (*CERA_SOMBRA, 255))
        for gx, gy in ((4, 17), (11, 20), (4, 24), (11, 26)):
            s.set_at((gx, gy), (*CERA, 255))
            s.set_at((gx, gy + 1), (*CERA_SOMBRA, 255))
        # El pabilo.
        s.set_at((7, 11), (30, 26, 34, 255))
        s.set_at((7, 12), (30, 26, 34, 255))
        if con_llama:
            # La llama: gota cálida con corazón claro y un halo tenue.
            llama = ((7, 4, (240, 170, 72)), (6, 5, (240, 170, 72)),
                     (7, 5, (255, 226, 148)), (8, 5, (240, 170, 72)),
                     (6, 6, (240, 170, 72)), (7, 6, (255, 226, 148)),
                     (8, 6, (240, 170, 72)), (6, 7, (208, 110, 40)),
                     (7, 7, (255, 226, 148)), (8, 7, (208, 110, 40)),
                     (7, 8, (240, 170, 72)), (7, 9, (208, 110, 40)),
                     (7, 3, (208, 110, 40)))
            for x, y, ccol in llama:
                s.set_at((x, y), (*ccol, 255))
            for dx, dy in ((-2, 1), (2, 1), (0, -2), (-1, 3), (1, 3)):
                s.set_at((7 + dx, 6 + dy), (240, 170, 72, 70))
        else:
            # Un hilo de humo frío.
            for k, (dx, dy) in enumerate(((0, -1), (1, -3), (0, -5), (-1, -7))):
                s.set_at((7 + dx, 11 + dy), (150, 150, 160, 90 - k * 18))
        return s

    def _armar_brasas(self) -> None:
        """Enciende las brasas de la boca (R2-8 · D-01).

        Determinista a propósito: la forma de cada brasa sale de un `Random`
        sembrado con la posición del faro, así una misma partida produce
        siempre la misma señal y las pruebas pueden mirar posiciones
        concretas.
        """
        import random as _random

        self._brasas = []
        faro = self._faro()
        if faro is None:
            return
        rng = _random.Random(f"boca-{faro.x}-{faro.width}")
        ancho = faro.width
        for _ in range(self.BRASAS_DEL_CIRCULO):
            self._brasas.append({
                # Concentradas hacia el centro: una campana burda con la
                # media de dos uniformes.
                "x": faro.left + ancho * (
                    (rng.random() + rng.random()) / 2.0),
                "retraso": rng.uniform(0.0, 6.0),
                "periodo": rng.uniform(2.6, 4.2),
                "amplitud": rng.uniform(2.0, 6.0),
                "tam": rng.choice((2, 2, 3)),
            })
        if self._disco_halo is None:
            self._disco_halo = self._disco_calido(48, (46, 22, 8))
        if self._disco_brasa is None:
            self._disco_brasa = self._disco_calido(5, (255, 168, 70))

    @staticmethod
    def _disco_calido(radio: int, color: tuple[int, int, int]) -> pygame.Surface:
        """Un disco con caída lineal, para sumar con `BLEND_RGB_ADD`.

        Sin canal alfa a propósito: la suma aditiva ignora el alfa y el
        negro suma cero, así que el borde del disco se funde solo.
        """
        lado = radio * 2
        disco = pygame.Surface((lado, lado))
        for r in range(radio, 0, -1):
            k = 1.0 - r / radio
            pygame.draw.circle(
                disco,
                (int(color[0] * k), int(color[1] * k), int(color[2] * k)),
                (radio, radio), r,
            )
        return disco

    def _posiciones_de_brasas(self) -> list[tuple[float, float, float]]:
        """(x, y, vida) de cada brasa en coordenadas de mundo, ahora mismo.

        `vida` va de 1.0 (recién nacida, al ras del emblema) a 0.0 (se
        apaga arriba). Separado del dibujo para poder probarlo sin pantalla.
        """
        faro = self._faro()
        if faro is None or not self._brasas:
            return []
        import math
        t = self._reloj_brasas
        suelo = float(faro.bottom) - 4.0
        posiciones = []
        for b in self._brasas:
            u = ((t + b["retraso"]) % b["periodo"]) / b["periodo"]
            x = b["x"] + math.sin(t * 1.7 + b["retraso"] * 7.0) * b["amplitud"]
            y = suelo - u * self.ALTURA_BRASA
            posiciones.append((x, y, 1.0 - u))
        return posiciones

    def _dibujar_brasas_del_circulo(
            self, surface: pygame.Surface, off: pygame.Vector2) -> None:
        """La señal, dibujada tras la luz: brasas y un halo que respira.

        Se apaga al descender (`sellado`): abajo la sala manda, y la boca de
        la superficie deja de tener a quién llamar.
        """
        import math
        if self._cementerio.sellado:
            return
        faro = self._faro()
        posiciones = self._posiciones_de_brasas()
        if faro is None or not posiciones:
            return
        # Fuera de pantalla no se paga nada (el mapa mide 4160 px).
        vista = surface.get_rect().move(int(off.x), int(off.y))
        if not vista.colliderect(faro.inflate(160, 160)):
            return
        if self._disco_halo is not None:
            # El halo respira: la mitad del mensaje es que la boca está
            # VIVA, y un brillo fijo se lee como un tile más del decorado.
            pulso = 0.62 + 0.38 * math.sin(self._reloj_brasas * 2.4)
            brillo = self._disco_halo.copy()
            brillo.fill((int(255 * pulso),) * 3,
                        special_flags=pygame.BLEND_RGB_MULT)
            cx = faro.centerx - off.x - brillo.get_width() // 2
            cy = faro.bottom - 6 - off.y - brillo.get_height() // 2
            surface.blit(brillo, (int(cx), int(cy)),
                         special_flags=pygame.BLEND_RGB_ADD)
        if self._disco_brasa is not None:
            for x, y, vida in posiciones:
                chispa = self._disco_brasa.copy()
                nivel = int(255 * (0.35 + 0.65 * vida))
                chispa.fill((nivel,) * 3, special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(
                    chispa,
                    (int(x - off.x) - 5, int(y - off.y) - 5),
                    special_flags=pygame.BLEND_RGB_ADD,
                )

    # ══ D-01·C/D — LAS CUATRO OFRENDAS ══════════════════════════
    # «Paburu no es un cazador: es un juez. Un juez no te embosca — te
    # cita. Y ante el juez tilawa nadie se presenta con las manos
    # vacías: al muerto se le acompaña con fuego.»
    # La regla en una frase: ENCENDÉ LOS CUATRO CÍRCULOS Y LA BOCA SE
    # ABRE. Diseño completo en `DISENO_ACCESO_CATACUMBA.md` §3.

    #: Dónde espera cada pavesa (centro, px). Una por tramo y SIEMPRE
    #: antes de su círculo, donde vive la mecánica del tramo (§3.2):
    #:   I  — el fondo del pozo: nadar con el ahogado.
    #:   II — el alto del círculo II, entre las dos cornisas altas:
    #:        plataformeo vertical (los pedestales del rito).
    #:   III— la galería corrida del círculo III, tras el ritmo.
    #:   IV — EL BOLSILLO tras el foso: la única forma cómoda de llegar
    #:        es soltarse de la tirolesa — la pieza muerta del nivel
    #:        pasa a ser el clímax del rito (y el bolsillo, que era una
    #:        trampa, ahora es un destino con resorte de vuelta).
    #: (La II está SOBRE la cornisa alta y no flotando en el vano entre
    #: las dos: el vano mide 128 px —incruzable hasta con salto doble— y
    #: el agarre al vuelo pasaba a ~20 px del radio: un premio que se
    #: roza y no se coge es un premio roto. Sobre la cornisa, el desafío
    #: es la escalada, que es lo que el tramo pregunta.)
    PAVESAS = ((600, 596), (1640, 380), (2660, 462), (4128, 538))
    #: Radio de recogida. Generoso: perseguir una brasa a pixel exacto
    #: bajo el agua no es dificultad, es fricción.
    ALCANCE_PAVESA = 22

    def _preparar_el_rito(self) -> None:
        """Arma las pavesas y SELLA la boca con la Losa del Juicio.

        La losa es una `Cerradura` del MOTOR (F4.1) apoyada a ras del
        suelo sobre la boca del foso: mientras está cerrada su rect es
        sólido (`rects_solidos`), así que el camino final se cruza por
        encima como piso — la boca no existe hasta que el rito la abre.
        Cero framework: el sistema de interactuables acepta cerraduras
        de quien sea, y `_abrir_cerraduras` del motor ya sabe avisar
        `mensaje_bloqueado` si el portador la toca con G. La llave que
        pide («cuatro_fuegos») no existe en ningún llavero a propósito:
        esta puerta no se abre con objeto, se abre con RITO.

        REENTRANTE a propósito: morir vuelve a llamar a `on_enter` (la
        misma trampa del sorteo, documentada en el constructor) y el
        padre reconstruye interactuables y luces. El PROGRESO —pavesas
        recogidas, en mano, círculos encendidos— vive en el estado del
        constructor y aquí sólo se RECONSTRUYE su mundo: la losa nueva
        en el sistema nuevo (ya abierta si el rito se cumplió) y las
        luces de los círculos que ya arden. Lo cazó
        `test_morir_no_apaga_nada`: la primera versión reseteaba todo y
        morir apagaba el camposanto entero.
        """
        if not self._pavesas:                  # primera entrada, no muerte
            import random as _random
            rng = _random.Random("las-cuatro-pavesas")
            self._pavesas = [{
                "x": float(x), "y": float(y),
                "fase": rng.uniform(0.0, 6.28),
                "recogida": False,
            } for x, y in self.PAVESAS]
        self._luces_del_rito = []
        self._polvo_de_losa = []
        self._losa = None
        for c in self._cementerio.circulos:
            if c.evento in self._circulos_encendidos:
                self._prender_luces_de(c)
        boca = self._cementerio.boca
        if (self._cementerio.sellado or self._interactables is None
                or boca is None or not boca.width
                or self._ofrendas_completas()):
            return      # pelea en curso o rito cumplido: sin losa
        from src.framework.stage.interactables import Cerradura
        # A RAS DE PISO (top = la losa del suelo, 560): la primera versión
        # la puso 16 px por encima y era un ESCALÓN — el caminante se
        # topaba con la cara lateral y no cruzaba (medido: clavado en
        # x=3990). Enrasada, el camino final se camina de largo y la boca
        # simplemente no existe hasta que el rito la abre.
        self._losa = Cerradura(
            rect=pygame.Rect(boca.left, boca.bottom, boca.width, 16),
            key_id="cuatro_fuegos",
            clase="puerta",
            mensaje_bloqueado=self._texto_de_la_losa(),
        )
        self._interactables.cerraduras.append(self._losa)

    def _prender_luces_de(self, circulo) -> None:
        """Las cuatro luces reales de un círculo encendido."""
        for cx in self._cuencos_de(circulo):
            luz = LightSource(
                pygame.Vector2(cx, 548.0),
                radius=120.0,
                color=BRAZIER_COLOR,
                intensity=0.85,
                flicker=True,
                flicker_speed=5.0,
                flicker_amount=0.2,
            )
            self._lighting.add_light(luz)
            self._stage_lights.append(luz)
            self._luces_del_rito.append(luz)

    def _texto_de_la_losa(self) -> str:
        n = len(getattr(self, "_circulos_encendidos", ()))
        return (f"LA LOSA DEL JUICIO NO CEDE - ARDEN {n} DE 4 CIRCULOS")

    def _ofrendas_completas(self) -> bool:
        return len(self._circulos_encendidos) >= 4

    def _atender_el_rito(self, dt: float) -> None:
        """La recogida de pavesas y los relojes del rito."""
        jugador = self._player
        if jugador is not None and not self._cementerio.sellado:
            for p in self._pavesas:
                if p["recogida"]:
                    continue
                dx = jugador.rect.centerx - p["x"]
                dy = jugador.rect.centery - p["y"]
                if dx * dx + dy * dy <= self.ALCANCE_PAVESA ** 2:
                    p["recogida"] = True
                    self._pavesas_en_mano += 1
                    if self._interactables is not None:
                        self._interactables._avisar(
                            "UNA PAVESA VIVA - LLEVALA A UN CIRCULO")
        vivos = []
        for grano in self._polvo_de_losa:
            grano["edad"] += dt
            if grano["edad"] < grano["vida"]:
                vivos.append(grano)
        self._polvo_de_losa = vivos

    def _encender_circulo(self, evento: str) -> None:
        """Un círculo recibe su ofrenda: los cuatro cuencos arden."""
        if evento in self._circulos_encendidos or self._pavesas_en_mano < 1:
            return
        circulo = next((c for c in self._cementerio.circulos
                        if c.evento == evento), None)
        if circulo is None:
            return
        self._pavesas_en_mano -= 1
        self._circulos_encendidos.add(evento)
        # La recompensa por explorar es literalmente PODER VER (§3.2):
        # cuatro fuegos reales en los cuencos del círculo.
        self._prender_luces_de(circulo)
        n = len(self._circulos_encendidos)
        if self._losa is not None:
            self._losa.mensaje_bloqueado = self._texto_de_la_losa()
        if self._interactables is not None:
            self._interactables._avisar(
                "LA LOSA DEL JUICIO CEDE" if n >= 4 else
                f"EL CIRCULO ARDE - {n} DE 4")
        if n >= 4:
            self._abrir_la_boca()

    @staticmethod
    def _cuencos_de(circulo) -> tuple[int, ...]:
        """Los centros de los cuatro cuencos de un círculo (x absoluta).

        Son los offsets de `cuencos_del_circulo` en `gen_paburu_tmx.py`
        (+8 al centro del tile). No se importa la herramienta: el juego
        no puede depender de `tools/`, y estos números son parte del
        plano del círculo tanto como sus muros.
        """
        x0 = circulo.arena.x
        return (x0 + 72, x0 + 184, x0 + 408, x0 + 520)

    def _abrir_la_boca(self) -> None:
        """La cuarta ofrenda: la losa cede y el foso queda abierto."""
        if self._losa is not None and not self._losa.abierta:
            self._losa.abrir(temporal=False)
            # El polvo del siglo que llevaba cerrada.
            import random as _random
            rng = _random.Random("el-polvo-de-la-losa")
            r = self._losa.rect
            for _ in range(26):
                self._polvo_de_losa.append({
                    "x": rng.uniform(r.left, r.right),
                    "y": float(r.top),
                    "vx": rng.uniform(-18.0, 18.0),
                    "vy": rng.uniform(-46.0, -12.0),
                    "vida": rng.uniform(0.6, 1.4),
                    "edad": 0.0,
                })
            if self._camera is not None:
                self._camera.apply_shake(amplitude=3.0, duration=0.5)

    # ── El dibujo del rito ──────────────────────────────────────
    def _dibujar_el_rito(self, surface: pygame.Surface,
                         off: pygame.Vector2) -> None:
        if self._cementerio.sellado:
            return
        import math
        t = self._reloj_brasas
        chispa = self._disco_brasa
        halo = self._disco_halo
        vista = surface.get_rect()
        # Las pavesas que esperan: una brasa viva que respira y flota.
        # R21 — MÁS PRESENTES: «las bolitas que agarramos están muy poco
        # visibles» (playtest del video). Tres refuerzos, todos de luz y
        # ninguno de tamaño de hitbox: (1) un SEGUNDO halo, más ancho y
        # respirando a destiempo — el charco de luz se ve desde el otro
        # lado del tramo; (2) chispitas que SUBEN de la brasa — el ojo va
        # al movimiento antes que al color; (3) el latido del halo cerca
        # del máximo, no del medio.
        for p in self._pavesas:
            if p["recogida"]:
                continue
            sx = int(p["x"] - off.x)
            sy = int(p["y"] - off.y + math.sin(t * 1.7 + p["fase"]) * 2.0)
            if not (-40 <= sx <= vista.width + 40):
                continue
            if halo is not None:
                ancho = pygame.transform.scale(
                    halo, (int(halo.get_width() * 1.9),
                           int(halo.get_height() * 1.9)))
                ka = 0.30 + 0.16 * math.sin(t * 1.3 + p["fase"] * 1.7)
                ancho.fill((int(255 * ka),) * 3,
                           special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(ancho, (sx - ancho.get_width() // 2,
                                     sy - ancho.get_height() // 2),
                             special_flags=pygame.BLEND_RGB_ADD)
                b = halo.copy()
                k = 0.72 + 0.24 * math.sin(t * 2.1 + p["fase"])
                b.fill((int(255 * k),) * 3, special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(b, (sx - b.get_width() // 2,
                                 sy - b.get_height() // 2),
                             special_flags=pygame.BLEND_RGB_ADD)
            if chispa is not None:
                surface.blit(chispa, (sx - 5, sy - 5),
                             special_flags=pygame.BLEND_RGB_ADD)
                # Las chispitas que suben: tres, en bucle, apagándose.
                for i in range(3):
                    ciclo = (t * 22.0 + i * 12.0 + p["fase"] * 9.0) % 34.0
                    kf = 1.0 - ciclo / 34.0
                    jx = int(math.sin(t * 3.0 + i * 2.1) * 3.0)
                    px_, py_ = sx + jx, sy - 6 - int(ciclo)
                    if 0 <= px_ < vista.width - 1 and 0 <= py_ < vista.height - 1:
                        col = (int(240 * kf), int(190 * kf), int(90 * kf))
                        for dx_, dy_ in ((0, 0), (1, 0), (0, 1)):
                            fondo = surface.get_at((px_ + dx_, py_ + dy_))
                            surface.set_at(
                                (px_ + dx_, py_ + dy_),
                                (min(255, fondo[0] + col[0]),
                                 min(255, fondo[1] + col[1]),
                                 min(255, fondo[2] + col[2])))
        # Las que van EN MANO: brasas orbitando al portador — el contador
        # diegético que se ve mientras se juega.
        if self._pavesas_en_mano and self._player is not None and \
                chispa is not None:
            r = self._player.rect
            for k in range(self._pavesas_en_mano):
                ang = t * 2.4 + k * (6.28 / max(1, self._pavesas_en_mano))
                sx = int(r.centerx + math.cos(ang) * 16 - off.x)
                sy = int(r.centery - 6 + math.sin(ang) * 8 - off.y)
                surface.blit(chispa, (sx - 5, sy - 5),
                             special_flags=pygame.BLEND_RGB_ADD)
        # Los círculos: encendidos arden, apagados humean — se ve de
        # lejos cuál falta (§4, el riesgo «no sé cuál me falta»).
        for c in self._cementerio.circulos:
            encendido = c.evento in self._circulos_encendidos
            for i, cx in enumerate(self._cuencos_de(c)):
                sx = int(cx - off.x)
                if not (-30 <= sx <= vista.width + 30):
                    continue
                if encendido and chispa is not None:
                    lengua = math.sin(t * 6.0 + i * 1.7) * 1.5
                    surface.blit(chispa, (sx - 5, int(541 - off.y + lengua)),
                                 special_flags=pygame.BLEND_RGB_ADD)
                    surface.blit(chispa, (sx - 5, int(545 - off.y)),
                                 special_flags=pygame.BLEND_RGB_ADD)
                elif not encendido:
                    # El hilo de humo frío del cuenco que espera.
                    u = (t * 0.35 + i * 0.25 + sx * 0.01) % 1.0
                    hy = int(546 - off.y - u * 14)
                    vaiven = int(math.sin(t * 1.3 + i) * 2)
                    a = int(70 * (1.0 - u))
                    if 0 <= hy < vista.height:
                        s = pygame.Surface((2, 2), pygame.SRCALPHA)
                        s.fill((150, 152, 162, a))
                        surface.blit(s, (sx + vaiven, hy))
        # La losa: sus cuatro marcas dicen el progreso EN el destino.
        if self._losa is not None and not self._losa.abierta:
            r = self._losa.rect
            for k in range(4):
                sx = int(r.left + 8 + k * 11 - off.x)
                sy = int(r.top + 6 - off.y)
                if k < len(self._circulos_encendidos):
                    pygame.draw.rect(surface, (240, 170, 72),
                                     (sx, sy, 3, 3))
                    pygame.draw.rect(surface, (255, 226, 148),
                                     (sx + 1, sy, 1, 1))
                else:
                    pygame.draw.rect(surface, (36, 34, 40), (sx, sy, 3, 3))
        # El polvo de la apertura.
        for g in self._polvo_de_losa:
            u = g["edad"] / g["vida"]
            sx = int(g["x"] + g["vx"] * g["edad"] - off.x)
            sy = int(g["y"] + g["vy"] * g["edad"] + 30.0 * g["edad"] ** 2
                     - off.y)
            if 0 <= sx < vista.width and 0 <= sy < vista.height:
                a = int(160 * (1.0 - u))
                s = pygame.Surface((2, 2), pygame.SRCALPHA)
                s.fill((168, 160, 150, a))
                surface.blit(s, (sx, sy))

    def _dibujar_contador_de_brasas(self, surface: pygame.Surface) -> None:
        """El contador diegético del HUD: cuatro braseritos bajo el
        retrato — arden los círculos encendidos, humean los que faltan."""
        if self._cementerio.sellado:
            return
        import math
        t = self._reloj_brasas
        n = len(self._circulos_encendidos)
        for k in range(4):
            x, y = 12 + k * 15, 68
            # El cuenco.
            pygame.draw.rect(surface, (94, 90, 100), (x, y + 5, 9, 3))
            pygame.draw.rect(surface, (66, 63, 74), (x + 1, y + 8, 7, 2))
            if k < n:
                lengua = int(math.sin(t * 5.0 + k) * 1.5)
                pygame.draw.rect(surface, (240, 170, 72),
                                 (x + 2, y + 1 + lengua, 5, 4))
                pygame.draw.rect(surface, (255, 226, 148),
                                 (x + 3, y + 2 + lengua, 3, 2))
            else:
                a = int(90 + 40 * math.sin(t * 1.5 + k))
                s = pygame.Surface((2, 5), pygame.SRCALPHA)
                s.fill((150, 152, 162, a))
                surface.blit(s, (x + 4, y - 2))

    # ── La piel de los bloques rítmicos (AUD-465) ───────────────
    #: La losa presente y la losa ida. Piedra del camposanto con el oro del
    #: rito, no el lila del motor.
    LOSA_CARA = (120, 104, 92)
    LOSA_SOMBRA = (74, 62, 54)
    LOSA_ORO = (196, 150, 62)
    LOSA_FANTASMA = (92, 76, 96)

    #: La balsa del pozo y el ascensor: tabla vieja atada, no un rectángulo.
    BALSA_TABLA = (104, 80, 56)
    BALSA_VETA = (72, 54, 38)
    BALSA_ATADURA = (150, 130, 96)
    #: El resorte del camino final: no es un muelle industrial, es una losa
    #: sobre tumba hueca que devuelve el peso. Bronce viejo.
    LOSA_SALTO = (126, 96, 48)
    LOSA_SALTO_BORDE = (72, 54, 30)

    def _dibujar_mecanicas_del_camposanto(self, surface: pygame.Surface) -> None:
        """Le pone piel de camposanto a las mecánicas que el motor pinta planas.

        AUD-465 — el motor dibuja `BloqueRitmico`, `PlataformaMovil` y
        `Resorte` como rectángulos de color (lila, gris, amarillo) y lo dice
        en su propio comentario: son marcadores para que nada quede invisible,
        «el estudiante lo sustituye por su arte cuando lo tenga». Este stage
        no lo había sustituido, y en el playtest esos rectángulos se leyeron
        como lo que parecen: piezas de otro juego pegadas encima del nuestro
        («ese poder azul raro»).

        `skins.py` explicaba por qué no se podía —las mecánicas del ECS se
        pintan dentro de `dibujar_ui`, sin hook, y duplicar ese método era un
        fork frágil— y AUD-461 cambió el trato: la escena ya sobrescribe
        `dibujar_ui`, así que basta con dibujar DESPUÉS del padre, encima y
        opaco. Ni una línea de framework.
        """
        self._dibujar_losas_del_ritmo(surface)
        self._dibujar_cuerdas_del_camposanto(surface)
        mundo = getattr(self, "_mundo", None)
        if mundo is None:
            return
        from src.framework.ecs import PlataformaMovil, Resorte, Transform

        off = self._camera.offset if self._camera is not None else pygame.Vector2()
        dx, dy = -int(off.x), -int(off.y)
        vista = surface.get_rect()

        for entidad, _movil in mundo.cada(PlataformaMovil):
            t = mundo.obtener(entidad, Transform)
            if t is None:
                continue
            r = t.rect.move(dx, dy)
            if not vista.colliderect(r):
                continue
            # Tabla con veta y dos ataduras: la balsa del pozo y el ascensor
            # de la galería son la misma madera del camposanto.
            pygame.draw.rect(surface, self.BALSA_TABLA, r)
            pygame.draw.rect(surface, self.BALSA_VETA, r, 1)
            pygame.draw.line(surface, self.BALSA_VETA,
                             (r.left + 1, r.centery), (r.right - 2, r.centery), 1)
            for cx in (r.left + 5, r.right - 6):
                pygame.draw.line(surface, self.BALSA_ATADURA,
                                 (cx, r.top + 1), (cx, r.bottom - 2), 1)

        for _entidad, resorte in mundo.cada(Resorte):
            r = resorte.rect.move(dx, dy)
            if not vista.colliderect(r):
                continue
            pygame.draw.rect(surface, self.LOSA_SALTO, r)
            pygame.draw.rect(surface, self.LOSA_SALTO_BORDE, r, 2)
            # Tres cuñas apuntando arriba: dicen «esto te lanza» sin texto.
            for i in range(3):
                cx = r.left + r.width * (i + 1) // 4
                pygame.draw.polygon(surface, self.LOSA_ORO, [
                    (cx, r.top + 3), (cx - 4, r.bottom - 4), (cx + 4, r.bottom - 4),
                ])

    #: La cuerda de maguey de los sepultureros. Fibra vieja, no soga nueva.
    SOGA_LUZ = (162, 138, 96)
    SOGA_FIBRA = (126, 104, 70)
    SOGA_SOMBRA = (78, 62, 40)
    #: La estaca de la que cuelga, clavada en la losa.
    ESTACA = (98, 74, 48)
    ESTACA_BORDE = (58, 44, 28)

    def _dibujar_cuerdas_del_camposanto(self, surface: pygame.Surface) -> None:
        """Le pone cuerda a las lianas. **El motor no las dibuja. Ninguna.**

        Hallazgo de D-01, y es de la misma familia que AUD-462, AUD-478c y
        AUD-461: cosas que funcionan y no se ven. `Liana` es un componente
        puramente físico —`liana_alcanzable` la busca, `TrepandoState` la
        usa— y no aparece en ningún sistema de dibujo del framework. O sea
        que `Liana_01`, la del primer minuto del nivel, lleva desde que se
        puso siendo **una escalera invisible en el aire**: el jugador subía
        agarrado a nada, y si no la encontraba por casualidad no había forma
        de saber que estaba ahí.

        Con el mecate de la boca (D-01) dejó de ser un detalle: la única
        entrada al juicio no puede ser invisible.

        La cuerda se dibuja aquí, con el resto de las pieles de mecánicas
        (AUD-465), y no con tiles: mide 736 px de una pieza, la fibra tiene
        que torcerse a lo largo —lo que la hace leerse como cuerda y no como
        un palo— y los nudos deben caer donde caen, no en la rejilla de 16.
        """
        mundo = getattr(self, "_mundo", None)
        if mundo is None:
            return
        import math

        from src.framework.ecs.components import Liana

        off = self._camera.offset if self._camera is not None else pygame.Vector2()
        dx, dy = -int(off.x), -int(off.y)
        vista = surface.get_rect()
        for _entidad, liana in mundo.cada(Liana):
            r = liana.rect.move(dx, dy)
            if not vista.colliderect(r.inflate(16, 16)):
                continue
            cx = r.centerx
            # Sólo la parte visible: una cuerda de 736 px en un mapa de 1312
            # no cabe en pantalla, y pintar los 736 cada fotograma es pagar
            # por píxeles que nadie ve.
            y0 = max(r.top, vista.top - 8)
            y1 = min(r.bottom, vista.bottom + 8)
            for y in range(int(y0), int(y1)):
                # Las dos hebras, torcidas en oposición. El desfase de medio
                # ciclo es lo que hace la trenza: en fase serían dos rayas.
                giro = math.sin((y - r.top) * 0.40)
                a = cx + round(giro * 2.0)
                b = cx + round(-giro * 2.0)
                surface.set_at((a, y), self.SOGA_LUZ if giro > 0
                               else self.SOGA_FIBRA)
                surface.set_at((b, y), self.SOGA_SOMBRA if giro > 0
                               else self.SOGA_FIBRA)
            # Los nudos: cada 40 px, y son lo que le da escala a la caída.
            # Sin ellos la cuerda es una línea y podría medir cualquier cosa.
            for k in range(0, r.height, 40):
                ny = r.top + k
                if not (y0 <= ny <= y1):
                    continue
                pygame.draw.line(surface, self.SOGA_LUZ,
                                 (cx - 3, ny), (cx + 3, ny), 2)
                pygame.draw.line(surface, self.SOGA_SOMBRA,
                                 (cx - 3, ny + 2), (cx + 3, ny + 2), 1)
            # La estaca: la cuerda tiene que estar atada a algo o flota.
            if vista.top - 8 <= r.top <= vista.bottom:
                estaca = pygame.Rect(cx - 9, r.top - 5, 18, 6)
                pygame.draw.rect(surface, self.ESTACA, estaca)
                pygame.draw.rect(surface, self.ESTACA_BORDE, estaca, 1)

    def _dibujar_losas_del_ritmo(self, surface: pygame.Surface) -> None:
        """Tapa los rectángulos lila del motor con losas grabadas.

        AUD-465 — el playtest lo llamó «ese poder azul raro»: tres rectángulos
        lila flotando en la Galería I, que es exactamente lo que el motor
        dibuja para un `BloqueRitmico` (`dibujo_mecanicas.py`: «formas planas y
        no sprites… el estudiante lo sustituye por su arte cuando lo tenga»).
        Nunca fue un poder ni un error: era el marcador de posición del motor,
        y este stage no lo había sustituido.

        `skins.py` documentó por qué no se podía: las mecánicas del ECS se
        pintan dentro de `dibujar_ui`, sin hook, y duplicar ese método era un
        fork frágil. AUD-461 cambió el trato — la escena ya sobrescribe
        `dibujar_ui` por otra razón —, así que ahora basta con dibujar DESPUÉS
        del padre, encima y opaco. Sin fork, sin tocar el framework.

        La losa presente es piedra con su grabado en oro; la ida es su huella
        —marco y nada dentro—, que conserva la lección del motor: hay que poder
        ver dónde VA a volver el suelo.
        """
        mundo = getattr(self, "_mundo", None)
        if mundo is None:
            return
        from src.framework.ecs import BloqueRitmico, Transform

        off = self._camera.offset if self._camera is not None else pygame.Vector2()
        dx, dy = -int(off.x), -int(off.y)
        for entidad, bloque in mundo.cada(BloqueRitmico):
            t = mundo.obtener(entidad, Transform)
            if t is None:
                continue
            r = t.rect.move(dx, dy)
            if not surface.get_rect().colliderect(r):
                continue
            if bloque.presente:
                pygame.draw.rect(surface, self.LOSA_CARA, r)
                pygame.draw.rect(surface, self.LOSA_SOMBRA, r, 2)
                # El grabado: dos surcos y el punto central, como las losas
                # del sello de la Sala. Es la misma familia visual.
                pygame.draw.line(surface, self.LOSA_ORO,
                                 (r.left + 4, r.centery), (r.right - 5, r.centery), 1)
                pygame.draw.circle(surface, self.LOSA_ORO, r.center, 2)
            else:
                # La huella: sólo el marco, en violeta apagado de ánima.
                pygame.draw.rect(surface, self.LOSA_FANTASMA, r, 1)

    # AUD-461 — la capa del jefe estaba en un override de `draw()`, y `App`
    # NO llama a `draw()` en una escena con la ruta de GPU: llama a
    # `dibujar_mundo` y `dibujar_ui` por separado (AUD-343/371). Resultado
    # medido en el playtest de la RONDA 2, reproducido fotograma a fotograma
    # en un contexto GL real: la intro del jefe corría INVISIBLE (~25 s de
    # pantalla quieta que se leyeron como congelamiento, R2-3), los
    # guardianes y sus ataques de la Forma 2 golpeaban sin dibujarse jamás
    # (parte de R2-9), y las picadas del vigilante castigaban desde la nada.
    # La luz, que era la sospechosa (R2-1), estaba inocente: el mapa de luz
    # sí viaja a la tarjeta y el sombreador sí multiplica — se comprobó
    # pasada a pasada.
    #
    # El arreglo reparte la capa entre las dos mitades del contrato:
    #   · con GPU, va en `dibujar_ui` (el overlay que la tarjeta compone
    #     DESPUÉS de la luz y el post-procesado) — el mismo punto del orden
    #     de pintado donde `draw()` la ponía en el camino software;
    #   · sin GPU (o en un arnés que llama a `draw()`, que sigue siendo
    #     `dibujar_mundo` + `dibujar_ui`), va al final de `dibujar_mundo`,
    #     después de que la luz ya se aplicó en CPU.
    # Espíritus y brasas son autoluminosos: no reciben la luz de la sala en
    # ningún camino, igual que antes.
    #: R2-9 / AUD-477 — el aviso de que el jefe VA A ATACAR.
    #:
    #: El reporte fue «los ataques del jefe, cómo están hechos y cuándo atacan,
    #: sobre todo en la última fase», y esa segunda mitad —el CUÁNDO— es un
    #: problema de legibilidad que sí se puede arreglar sin tocar el balance.
    #: Cada ataque trae su propio telegraph (el rayo avisa, el sello avisa, el
    #: orbe avisa), pero en la Forma 4 hay cuatro patrones que pueden solaparse
    #: y el ojo no sabe dónde mirar: falta el aviso del CUERPO, uno solo, común
    #: a todos, que diga «sale de aquí, ahora».
    #:
    #: `_pose_cast_t` ya existe y lo arma el planificador para TODO patrón
    #: (mejora D, las poses de casteo). Se reutiliza tal cual: mientras esté
    #: vivo, el jefe lleva un anillo que colapsa hacia él. Un solo tell, el
    #: mismo en las cuatro formas — que es lo que lo hace aprendible.
    AVISO_CAST = (255, 214, 120)

    def _dibujar_aviso_del_jefe(self, surface: pygame.Surface,
                                off: pygame.Vector2) -> None:
        boss = self._boss_ref()
        if boss is None or getattr(boss, "en_epilogo", False):
            return
        t = float(getattr(boss, "_pose_cast_t", 0.0) or 0.0)
        if t <= 0.0:
            return
        import math as _m

        from src.stages.boss_paburu.ataques_guardianes import _fundir, _halo, _lienzo

        # `_pose_cast_t` nace en 0.6 y decae: el anillo COLAPSA hacia el jefe,
        # que es la dirección que dice «se está cargando», no «se está
        # apagando». Al llegar a cero el ataque ya salió.
        p = max(0.0, min(1.0, t / 0.6))
        r = boss.rect
        radio = int(max(r.w, r.h) * (0.62 + 0.75 * p))
        lado = radio * 2 + 24
        capa = _lienzo(lado, lado)
        c = (lado // 2, lado // 2)
        grosor = 2 if p > 0.5 else 3
        pygame.draw.circle(capa, (*self.AVISO_CAST, int(70 + 120 * (1 - p))),
                           c, radio, grosor)
        # Cuatro marcas en los ejes: dan la orientación y hacen que el anillo
        # se lea como un cerco ritual y no como un halo cualquiera.
        for k in range(4):
            a = _m.pi / 2 * k + self._reloj_brasas * 1.6
            _halo(capa, (c[0] + _m.cos(a) * radio, c[1] + _m.sin(a) * radio),
                  5 * (1 - p) + 2, self.AVISO_CAST, 1.3)
        _fundir(surface, capa,
                (int(r.centerx - off.x) - lado // 2,
                 int(r.centery - off.y) - lado // 2))

    def _dibujar_capa_del_jefe(self, surface: pygame.Surface) -> None:
        """Guardianes y ecos: lo espectral, dibujado tras la luz."""
        off = self._camera.offset if self._camera is not None else pygame.Vector2()
        self._dibujar_aviso_del_jefe(surface, off)
        # Los guardianes están en el cielo, detrás de todo lo jugable, pero
        # la placa del título y la caja de diálogo quedan encima de ellos.
        for g in self._guardianes:
            g.draw(surface, off, self._presencia)
        # Los ecos de la ronda van encima de los guardianes (son lo jugable)
        # y debajo de la cinemática, como los proyectiles del jefe.
        for a in self._ataques_guardianes:
            a.draw(surface, off)
        for eco in self._ecos_del_vigilante:
            eco.draw(surface, off)

    def dibujar_mundo(self, surface: pygame.Surface) -> None:
        super().dibujar_mundo(surface)
        # Las brasas van en el MUNDO, no en el overlay: sus blits son
        # aditivos (`BLEND_RGB_ADD`), y un blit aditivo sobre el overlay
        # SRCALPHA de la ruta de GPU no toca el alfa — la tarjeta lo
        # compondría a alfa cero, o sea invisible. En el mundo funcionan en
        # los dos caminos; con GPU además les toca el bloom, que a una
        # brasa le queda bien.
        off = self._camera.offset if self._camera is not None else pygame.Vector2()
        # D-01·J — las estrellas, antes que nada: son lo más lejano del mundo.
        self._dibujar_estrellas(surface, off)
        # D-01·K — las nubes, sobre las estrellas: pueden taparlas, y taparse
        # la luna es su mejor momento.
        self._dibujar_nubes(surface, off, 1.0 / 60.0)
        # D-01·B — la niebla PRIMERO: se arrastra por el suelo y las brasas
        # de la boca tienen que arder por encima de ella, no debajo.
        self._dibujar_niebla(surface, off, 1.0 / 60.0)
        # D-01·H — las ánimas, sobre la niebla: se levantan a través de ella.
        self._dibujar_animas(surface, off)
        # #49 — el aura del portador transformado, encima de él (el jugador
        # ya quedó pintado por el `super()`). Corre también en la catacumba.
        self._dibujar_el_anima_del_portador(surface, off)
        # El letrero de la tirolesa, cuando el portador anda cerca.
        self._dibujar_letrero_de_la_tirolesa(surface, off)
        # La tecla 8 acaba de llenar la barra: decir qué sigue (Z+X).
        self._dibujar_aviso_del_ulti(surface, off)
        # D-01·C/D — pavesas, cuencos encendidos, humo y la losa.
        self._dibujar_el_rito(surface, off)
        self._dibujar_brasas_del_circulo(surface, off)
        # Sin GPU la luz ya se aplicó dentro del `super()`; la capa va aquí
        # para que exista también en el camino software y en los arneses.
        if not getattr(self.context, "usar_gl", False):
            self._dibujar_capa_del_jefe(surface)

    def dibujar_ui(self, surface: pygame.Surface) -> None:
        # AUD-498 — lo PRIMERO, antes de pintar nada: el corazón del reloj.
        # Va aquí y no en `update()` porque `update()` es exactamente lo que
        # deja de correr durante el cuelgue. Ver `_reanimar_el_reloj`.
        self._reanimar_el_reloj()
        # Con GPU la capa viaja en el overlay: es el único lienzo que la
        # tarjeta compone después de la luz. El `if` evita dibujarla dos
        # veces cuando `draw()` (arnés/software) encadena las dos mitades.
        if getattr(self.context, "usar_gl", False):
            self._dibujar_capa_del_jefe(surface)
        super().dibujar_ui(surface)
        # AUD-465 — la piel de las mecánicas va JUSTO después del padre: es él
        # quien pinta los rectángulos planos del motor, y esto los tapa. Antes
        # del padre no serviría de nada; después del HUD taparía el HUD.
        self._dibujar_mecanicas_del_camposanto(surface)
        # D-01·C — el contador de brasas, bajo el retrato.
        self._dibujar_contador_de_brasas(surface)
        # La intro, encima de TODO (bandas, texto y fundidos incluidos): era
        # la parte que en la ruta de GPU no se veía en absoluto.
        if self._intro is not None and self._intro.active:
            self._intro.draw(surface)

    def _forzar_forma(self, fase: int) -> None:
        """Salta a una forma sin pasar por el umbral de vida.

        La vida se pone en el UMBRAL DE ENTRADA de esa fase
        (`health_threshold`: 20/15/10/5), no en `phase_max_health`. Con la
        segunda, forzar la Forma 2 dejaba la vida en el TAMAÑO del segmento
        (5), que ya está por debajo del umbral de la Forma 4 — y el jefe
        caía en cascada hasta el Espíritu en el primer fotograma. Se vio en
        una captura del arnés: el sprite era el del Espíritu con la 2 recién
        forzada. (El «PHASE 4» del HUD es otra cosa: el motor muestra el
        TOTAL de fases, no la actual — quirk documentado en boss_venado.)
        """
        boss = self._boss_ref()
        if boss is None:
            return
        objetivo = max(0, min(boss.phase_count - 1, fase))
        # La transición COMPLETA, no solo el número: sin esto, saltar a la
        # Forma 3 con la tecla de depuración dejaba `relic_variant` sin
        # sortear y el motor sin crear — la reliquia flotaba muerta.
        #
        # OJO con el protocolo del motor: `_finish_phase_transition` hace
        # `current_phase += 1` porque está pensado para llamarse EN MEDIO de
        # la transición, con la fase vieja todavía puesta. Se apunta una
        # fase antes y se deja que el cierre dé el paso — el mismo camino
        # que recorre la transición real por umbral de vida.
        boss.current_phase = objetivo - 1
        boss._finish_phase_transition()
        boss.current_health = boss.phases[boss.current_phase].health_threshold
        self._set_phase_light(boss.current_phase)
        # AUD-495 — aquí había un `emit(BOSS_PHASE_CHANGED)` DE MÁS.
        #
        # `_finish_phase_transition` (motor, `BossBase`) ya emite el evento
        # con su carga completa —`boss_name`, `phase`, `new_max_health`—, así
        # que esta segunda emisión repetía el aviso con menos datos: medido,
        # 4 emisiones por una sola llamada a `_forzar_forma` (una del motor y
        # una de aquí, ×2 porque el bus las reparte a los dos suscriptores).
        # El síntoma visible eran el cartel de forma y el bloom dobles, y el
        # riesgo real es que quien escuche el evento cuente transiciones.
        # El evento es del motor: se emite donde el motor lo emite.

    def _boss_ref(self) -> BossPaburu | None:
        if self._stage_data is None:
            return None
        for e in self._stage_data.entity_list:
            if isinstance(e, BossPaburu):
                return e
        return None

    def _set_phase_light(self, phase: int) -> None:
        """Enciende un cuenco más y sube la luz ambiente.

        Forma 1 → un cuenco encendido y la arena casi a oscuras.
        Forma 4 → los cuatro, y el sello del piso ya es legible.
        """
        phase = max(0, min(len(AMBIENT_BY_PHASE) - 1, phase))
        self._lighting.ambient_brightness = AMBIENT_BY_PHASE[phase]
        for i, light in enumerate(self._braziers):
            light.intensity = 0.95 if i <= phase else 0.0
