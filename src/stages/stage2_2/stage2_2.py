"""
Module: stage2_2
System: stage (student assignment)
Assignment: entrada_antenas — César Ubáu Calvo
Academic Unit: ver README.md (front-matter: units_demonstrated)

Stage 2-2 — Entrada y Antenas.

La puerta de entrada al complejo del datacenter. Viene después de Stage 2-1
(La Planicie) y desemboca en el Lobby (Alejandro Luna).

Tres secciones apiladas en un plano de 64 × 50 tiles (1024 × 800 px):

  1. Suelo    — parqueo exterior y caseta de seguridad.
  2. Escalada — cadena de repechos por el costado del edificio.
                Un objeto CameraLock (lock_x=true, lock_y=false) fija el
                encuadre horizontal aquí, de modo que la cámara solo sigue
                el movimiento vertical (Unidad IV).
  3. Azotea   — arreglo de antenas, plataformas angostas entre postes.

El nombre del módulo es `stage2_2` y no `entrada_antenas` porque
`src/engine/core/stage_registry.py` declara el orden canónico de escenarios en
`STAGE_ORDER`, y ese registro nombra esta ranura `stage2_2`. Un módulo con otro
nombre arranca con `--stage`, pero `discover_stages()` nunca lo encuentra y el
escenario queda fuera del flujo normal del juego. El nombre legible vive en
`STAGE_NAME`.

Extensión sin tocar el framework
--------------------------------
`StageScene` no expone ningún hook para entidades propias. Se sobreescriben
`update()` y `draw()` llamando a `super()` en cada uno: es herencia normal, y
no se modifica una sola línea de `src/engine/` ni de `src/framework/`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.utils.math_utils import vec2_distance
from src.framework.scenes.stage_scene import StageScene

from .atmosfera import AtmosferaAntenas
from .camara_seguridad import CamaraSeguridad
from .patrulla_bspline import PatrullaBSpline

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.framework.entities.enemy_base import EnemyBase


class Stage2_2(StageScene):
    """Stage 2-2 — Entrada y Antenas (Zona 2, El Datacenter)."""

    STAGE_ID: str = "stage2_2"
    STAGE_NAME: str = "ENTRADA Y ANTENAS"
    ZONE: int = 2

    # Declarados para documentación. La fuente de verdad en tiempo de ejecución
    # son las propiedades del TMX, que StageLoader deja en `self._stage_data`:
    # el motor nunca consulta estos atributos de clase.
    TIME_LIMIT: int = 170
    BGM_TRACK: str = "bgm_zone2_traverse"
    TILE: int = 16

    # Ruta absoluta derivada de settings.ASSETS_DIR, no relativa. Una ruta
    # relativa se resuelve contra el directorio de trabajo, así que lanzar el
    # juego desde otra carpeta rompería la carga del mapa.
    TMX_PATH = settings.ASSETS_DIR / "maps/stage2_2/stage2_2.tmx"

    #: Radio en píxeles dentro del cual una cámara que detecta al jugador
    #: despierta a los enemigos. Se mide con `vec2_distance`.
    #:
    #: Bajado de 260 a 150 tras probar el nivel: con 260 px una sola detección
    #: en la caseta despertaba a todos los enemigos del parqueo a la vez y el
    #: tramo se volvía intransitable. La alerta debe avisar al guardia de al
    #: lado, no a la sección entera.
    RADIO_ALERTA: float = 150.0

    #: Nombre del objeto Flying del TMX que recorre la curva. Los objetos
    #: Waypoint lo referencian con su propiedad `owner_id`.
    DUENO_CURVA: str = "FlyingBoa_01"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._camaras: list[CamaraSeguridad] = []
        self._patrulla: PatrullaBSpline | None = None
        self._entidad_curva: EnemyBase | None = None
        self._atmosfera: AtmosferaAntenas | None = None

    # ── Hooks del ciclo de vida ─────────────────────────────────────

    def on_stage_start(self) -> None:
        """Se ejecuta después de que el TMX cargó y el setup terminó."""
        super().on_stage_start()
        self._colocar_camaras()
        self._montar_patrulla_bspline()
        self._montar_atmosfera()
        self._aplicar_modo_pruebas()

    # ── Unidad V — color y transparencia ────────────────────────────

    def _montar_atmosfera(self) -> None:
        """Prepara las luces de antena y el velo atmosférico.

        Las tres puntas de antena están en las columnas 86, 94 y 102, fila 8,
        o sea en x = 1376, 1504 y 1632 con y = 128. Se toma el centro del
        tile: (1384, 136), (1512, 136) y (1640, 136).

        Los extremos del degradado son el asfalto del parqueo (y = 704) y la
        superficie de la azotea (y = 256), las dos alturas que el jugador
        recorre de punta a punta.
        """
        self._atmosfera = AtmosferaAntenas(
            posiciones_luces=[(1384.0, 136.0), (1512.0, 136.0), (1640.0, 136.0)],
            y_suelo=704.0,
            y_azotea=256.0,
        )

    # ── Modo de pruebas ─────────────────────────────────────────────

    @staticmethod
    def _modo_pruebas_activo() -> bool:
        """¿Está pedido el modo inofensivo?

        Se lee de la variable de entorno ``LOI_SIN_ENEMIGOS`` y no de una
        constante en el código, para que activarlo no requiera editar y
        volver a editar el archivo. Un interruptor que hay que recordar
        apagar antes de entregar es un interruptor que se olvida encendido.
        """
        import os
        return os.environ.get("LOI_SIN_ENEMIGOS", "").strip() not in ("", "0")

    def _aplicar_modo_pruebas(self) -> None:
        """Deja a los enemigos visibles pero incapaces de hacer daño.

        Se anula el daño en vez de borrar las entidades a propósito: la boa
        que recorre la B-Spline **es** la demostración de la Unidad III, y
        borrarla para poder recorrer el nivel apagaría justo lo que hay que
        mirar. Siguen animándose, patrullando y volando su curva; solo dejan
        de restar vida.
        """
        if not self._modo_pruebas_activo():
            return

        from src.framework.entities.enemy_base import EnemyBase

        anulados = 0
        for entidad in self._stage_data.entity_list:
            if not isinstance(entidad, EnemyBase):
                continue
            for atributo in ("damage_on_contact", "projectile_damage", "contact_damage"):
                if hasattr(entidad, atributo):
                    setattr(entidad, atributo, 0.0)
            anulados += 1

        print(f"[stage2_2] MODO PRUEBAS: {anulados} enemigos sin daño "
              f"(LOI_SIN_ENEMIGOS activo)")

    def on_next_trigger_entered(self) -> None:
        """El jugador tocó el NextTrigger: entrada al Lobby."""
        super().on_next_trigger_entered()

    # ── Unidad II — cámaras de vigilancia (matemática vectorial) ────

    def _colocar_camaras(self) -> None:
        """Instancia las cámaras de seguridad del nivel.

        Las posiciones son de mundo, en píxeles, y coinciden con la geometría
        del TMX:

        * Caseta de seguridad: el kiosco ocupa x 1072–1168 con su techo en
          y = 640. La cámara va en la esquina superior derecha, apuntando a
          la izquierda (180°) para barrer la aproximación del parqueo. Con
          alcance 190 px cubre x de 976 a 1166: el jugador entra en su campo
          al acercarse al pie de la escalada.
        * Azotea: sobre la superficie del edificio (y = 256), mirando a la
          derecha (0°) hacia el campo de antenas.
        """
        self._camaras = [
            CamaraSeguridad(
                x=1166.0, y=634.0,
                angulo_base=180.0, amplitud_barrido=38.0, periodo=4.2,
                fov=70.0, alcance=190.0,
            ),
            CamaraSeguridad(
                x=1332.0, y=248.0,
                angulo_base=0.0, amplitud_barrido=30.0, periodo=5.6,
                fov=64.0, alcance=150.0,
            ),
        ]

    def _alertar_enemigos_cercanos(self, centro_jugador: pygame.Vector2) -> None:
        """Despierta a los enemigos en patrulla dentro de `RADIO_ALERTA`.

        Es el efecto observable de la detección: una cámara que te ve no solo
        cambia de color, comunica tu posición. La distancia se mide otra vez
        con `vec2_distance`, la norma euclidiana del vector diferencia.
        """
        from src.framework.entities.enemy_base import EnemyBase, EnemyState

        for entidad in self._stage_data.entity_list:
            if not isinstance(entidad, EnemyBase) or not entidad.is_alive:
                continue
            if entidad.state not in (EnemyState.PATROL, EnemyState.IDLE):
                continue
            distancia = vec2_distance(
                pygame.Vector2(entidad.rect.center), centro_jugador
            )
            if distancia <= self.RADIO_ALERTA:
                entidad.state = EnemyState.ALERT

    # ── Unidad III — patrulla sobre curva B-Spline ──────────────────

    def _leer_waypoints(self, owner_id: str) -> list[tuple[float, float]]:
        """Lee los Waypoint del TMX de `owner_id`, **ordenados por índice**.

        No se usa `entity.waypoints`, que es lo que entrega `StageLoader`,
        porque `StageLoader._build_waypoints` los acumula en el orden en que
        aparecen en el XML y **nunca los ordena por `waypoint_index`**, pese a
        que `docs/06_TMX_SPEC.md` §6.3 afirma que sí. Hoy el orden del archivo
        coincide con el de los índices, así que funcionaría; sería una
        casualidad, y reordenar dos objetos en Tiled la rompería sin ningún
        error visible: la curva simplemente pasaría por otro lado.
        """
        import xml.etree.ElementTree as ET

        encontrados: list[tuple[int, tuple[float, float]]] = []
        raiz = ET.parse(self.TMX_PATH).getroot()
        for grupo in raiz.findall("objectgroup"):
            if grupo.get("name") != "Objects":
                continue
            for obj in grupo.findall("object"):
                if obj.get("type") != "Waypoint":
                    continue
                props = {
                    p.get("name"): p.get("value")
                    for p in obj.findall("properties/property")
                }
                if props.get("owner_id") != owner_id:
                    continue
                encontrados.append((
                    int(props.get("waypoint_index", 0)),
                    (float(obj.get("x", 0.0)), float(obj.get("y", 0.0))),
                ))

        encontrados.sort(key=lambda par: par[0])
        return [punto for _, punto in encontrados]

    def _montar_patrulla_bspline(self) -> None:
        """Construye la curva y engancha la entidad que la recorre.

        La entidad se localiza por tener waypoints asignados, no por su
        nombre: `StageLoader._handle_entity_spawn` construye la entidad con
        `entity_class(pygame.Vector2(obj.x, obj.y), **cleaned)` y **descarta
        el nombre del objeto TMX**, así que buscar por nombre en
        `entity_list` no es posible.
        """
        from src.framework.entities.enemy_base import EnemyBase

        puntos = self._leer_waypoints(self.DUENO_CURVA)
        if len(puntos) < PatrullaBSpline.GRADO + 1:
            return

        self._patrulla = PatrullaBSpline(puntos, velocidad=45.0)

        for entidad in self._stage_data.entity_list:
            if isinstance(entidad, EnemyBase) and getattr(entidad, "waypoints", None):
                self._entidad_curva = entidad
                break

    def _mover_sobre_curva(self, dt: float) -> None:
        """Coloca la entidad en la curva, sobreescribiendo su estrategia.

        Se escribe después de `super().update(dt)`, así que pisa el resultado
        de la estrategia de vuelo propia de `EnemyFlying` (`sine`, `bezier` o
        `patrol`). Ninguna de las tres evalúa una B-Spline —`bezier` llama a
        `CurveTools.bezier`— y el requisito de la Unidad III es explícitamente
        una B-Spline, así que la trayectoria se controla desde aquí.

        Hay que actualizar `position` **y** `rect`: `position` es el vector en
        coma flotante que usa la física, y `rect` la caja entera que usan las
        colisiones y el dibujado. Si solo se toca uno, el enemigo se ve en un
        sitio y golpea en otro.
        """
        if self._patrulla is None or self._entidad_curva is None:
            return
        if not self._entidad_curva.is_alive:
            return

        posicion = self._patrulla.update(dt)
        self._entidad_curva.position.update(posicion)
        self._entidad_curva.rect.topleft = (int(posicion.x), int(posicion.y))

    # ── Unidad IV — bloqueo de cámara por zona ──────────────────────

    def _corregir_bloqueo_camara(self) -> None:
        """Activa el `CameraLock` solo mientras el jugador está dentro.

        Rodea un defecto de `src/framework/stage/camera.py`. Su método
        `set_camera_locks` es::

            def set_camera_locks(self, locks):
                if locks is not None:
                    self._is_locked_x = any(line.lock_x for line in locks)
                    self._is_locked_y = any(line.lock_y for line in locks)

        `_CameraLock` guarda un `rect`, pero **ese rect no se consulta jamás**:
        basta con que exista un lock con ``lock_x=True`` en cualquier parte del
        mapa para que el eje X quede congelado durante todo el nivel, desde el
        primer fotograma. El resultado es una cámara que nunca sigue al
        jugador en horizontal, ni en el parqueo ni en la azotea.

        La corrección no toca el framework. `StageScene._update_camera_map`
        llama primero a ``camera.update(dt)`` y **después** a
        ``camera.set_camera_locks(stage.camera_locks)``, así que las banderas
        que se escriben en un fotograma se aplican en el siguiente. Al volver a
        llamar a `set_camera_locks` desde aquí —después de `super().update()`—
        la última escritura es la filtrada. El coste es un fotograma de
        latencia al entrar y salir de la zona: 16 ms, imperceptible.

        Pasar una lista vacía sí desbloquea: ``any([])`` es ``False``. Lo que
        no funcionaría es pasar ``None``, porque la guarda ``if locks is not
        None`` dejaría las banderas como estaban.
        """
        bloqueos = getattr(self._stage_data, "camera_locks", None)
        if not bloqueos:
            return

        rect_jugador = self._player.rect
        activos = [
            bloqueo for bloqueo in bloqueos
            if bloqueo.rect.colliderect(rect_jugador)
        ]
        self._camera.set_camera_locks(activos)

    # ── update / draw ───────────────────────────────────────────────

    def update(self, dt: float) -> None:
        super().update(dt)

        # Las mismas guardas que usa StageScene.update: sin ellas esto correría
        # durante la transición de entrada, cuando `_stage_data` aún es None.
        if self._stage_data is None or self._player is None:
            return
        if self._paused or self._game_over:
            return

        centro_jugador = pygame.Vector2(self._player.rect.center)
        alguna_detecta = False
        for camara in self._camaras:
            if camara.update(dt, centro_jugador):
                alguna_detecta = True

        if alguna_detecta:
            self._alertar_enemigos_cercanos(centro_jugador)

        self._mover_sobre_curva(dt)
        self._corregir_bloqueo_camara()

        if self._atmosfera is not None:
            self._atmosfera.update(dt, float(self._player.rect.centery))

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)

        if self._stage_data is None or self._player is None:
            return

        # Los conos se dibujan después de `super().draw()`, que ya pintó el
        # mundo, la iluminación, el post-procesado y la interfaz. Es la única
        # opción sin tocar `DrawingSystem`: la consecuencia es que un cono
        # queda por encima del HUD si el jugador está en la esquina superior
        # izquierda. Se acepta a cambio de no modificar el framework.
        # Orden deliberado: el velo atmosférico va primero, para que tiña la
        # escena; los halos de las antenas después, porque son fuentes de luz
        # y la luz emitida no debe quedar detrás del aire que atraviesa.
        if self._atmosfera is not None:
            self._atmosfera.draw_velo(surface)
            self._atmosfera.draw_luces(surface, self._camera.offset)

        if self._patrulla is not None:
            # Con F1 se añaden el polígono de control y sus vértices: la
            # B-Spline queda dentro de su envolvente convexa, y verlos juntos
            # hace la propiedad evidente sin explicarla.
            self._patrulla.draw(
                surface, self._camera.offset, mostrar_control=self._debug
            )

        for camara in self._camaras:
            camara.draw(surface, self._camera.offset)
