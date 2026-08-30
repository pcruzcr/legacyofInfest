"""Pruebas del nivel 1-2 «La Soda».

Viven dentro del paquete del nivel a propósito: `tests/` es del profesor y no
se toca (`CLAUDE.md`, alcance editable). Como no heredan el `conftest.py` de
`tests/`, este módulo fija los controladores de vídeo y audio a `dummy` antes
de importar pygame, igual que hace `tests/conftest.py`.

Se corren con:
    python -m pytest src/stages/stage1_2_la_soda/test_la_soda.py -q
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pygame
import pytest

from src.stages.stage1_2_la_soda.entities import (
    FlyingCucaracha,
    FlyingZancudo,
    ShooterCocinero,
    WalkerCulebra,
    WalkerRaton,
)

RAIZ = Path(__file__).resolve().parents[3]
TMX = RAIZ / "assets" / "maps" / "stage1_2_la_soda" / "stage1_2_la_soda.tmx"

# Enemigos que se apoyan sobre una superficie sólida. Los voladores
# (FlyingCucaracha, FlyingZancudo) quedan fuera: su altura de vuelo es parte
# del diseño, no un apoyo.
APOYADOS = ("WalkerRaton", "WalkerCulebra", "ShooterCocinero")

# Los dos voladores que disparan proyectiles — misma mecánica de
# parry-a-distancia, copiada literal de una a otra (ver sus docstrings).
ENEMIGOS_QUE_DISPARAN = (FlyingCucaracha, FlyingZancudo)


@pytest.fixture(scope="module")
def datos_del_nivel():
    """Carga el `.tmx` una sola vez con el cargador real del motor.

    Importar el módulo del nivel es lo que registra los tipos `LaSoda*` en
    `StageLoader`; sin eso el cargador no sabe instanciar los enemigos.
    """
    pygame.init()
    pygame.display.set_mode((800, 600))

    from src.framework.stage.stage_loader import StageLoader

    import src.stages.stage1_2_la_soda.stage1_2_la_soda  # noqa: F401

    datos = StageLoader.load(str(TMX))
    yield datos
    pygame.quit()


def _superficie_bajo(entidad, solidos):
    """Borde superior del sólido que sostiene a `entidad`, o None.

    Busca hacia abajo desde los pies con margen, para detectar tanto el apoyo
    correcto como el caso en que la entidad quedó hundida dentro del sólido.
    """
    r = entidad.rect
    candidatos = [
        s.top
        for s in solidos
        if s.left < r.centerx < s.right and s.top >= r.bottom - 48
    ]
    return min(candidatos) if candidatos else None


def test_el_nivel_carga_y_puebla_sus_entidades(datos_del_nivel):
    """Red de seguridad: si el mapa deja de cargar, todo lo demás miente."""
    # El mapa creció a 216x38 tiles (16 px/tile) al alargar el camino
    # exterior para repartir checkpoints y enemigos: 216*16=3456, 38*16=608.
    assert datos_del_nivel.map_pixel_size == (3456, 608)
    # Bajó de 16 a 13: se quitaron 1 rata y 2 cucarachas de la soda (estaban
    # apelotonadas) al repartir el camino exterior extendido. Sigue muy por
    # encima del mínimo de 6 que exige el spec (`enemies_placed` en grade_stage.py).
    assert len(datos_del_nivel.entity_list) >= 13


def test_los_enemigos_de_suelo_apoyan_los_pies_en_su_superficie(datos_del_nivel):
    """AUD-455 cambió la convención: la `y` del TMX es la esquina superior.

    Antes el framework restaba `rect.height` al spawn, así que la `y` del TMX
    eran los pies. Al quitar esa resta, todo objeto colocado con la vieja
    convención queda hundido justo la altura de su caja. Esta prueba fija el
    contrato: los pies de un enemigo apoyado coinciden con el borde superior
    del sólido que lo sostiene.
    """
    solidos = list(datos_del_nivel.collision_rects)
    assert solidos, "el mapa tiene que traer sólidos para poder apoyar nada"

    hundidos = []
    for entidad in datos_del_nivel.entity_list:
        nombre = type(entidad).__name__
        if nombre not in APOYADOS:
            continue
        superficie = _superficie_bajo(entidad, solidos)
        if superficie is None:
            continue
        desfase = entidad.rect.bottom - superficie
        if desfase != 0:
            hundidos.append((nombre, entidad.rect.bottom, superficie, desfase))

    assert not hundidos, (
        "enemigos mal apoyados (entidad, pies, superficie, desfase): "
        f"{hundidos}"
    )


# ──────────────────────────────────────────────────────────────────────────
# AUD-489 (audio direccional) / AUD-206 (la parada aturde) — mejoras del
# profesor (rango de commits 87bcf72..aadf917) adoptadas a mano acá porque
# `src/stages/` es código de estudiante y el profesor no lo toca.
#
# El patrón canónico de `pos=` vive en
# `src/framework/entities/enemy_base.py:591-600` (muerte del enemigo) y el
# de "parar aturde a quien atacó" en la misma clase, líneas 770-795 (parry
# de golpe cuerpo a cuerpo). Estas pruebas construyen los enemigos
# directamente — sin pasar por el `.tmx` — igual que hacen
# `tests/test_audio_direccional_por_entidad.py` y
# `tests/test_parada_que_aturde.py` del profesor con los suyos.
# ──────────────────────────────────────────────────────────────────────────


class _BusEspiaConDatos:
    """Espía de `EventBus` que además guarda los kwargs de cada emisión.

    No hace falta un motor de audio real: `sonido.py._make_sfx_handler` sólo
    decide el canal (posicional o ciego) mirando si `pos` viene entre los
    datos del evento, así que basta con espiar lo que `emit` recibe. Mismo
    patrón que `_BusEspiaConDatos` de
    `tests/test_audio_direccional_por_entidad.py` (profesor).
    """

    def __init__(self) -> None:
        self.emitidos: list[tuple[str, dict]] = []

    def emit(self, nombre: str, **datos) -> None:
        self.emitidos.append((nombre, datos))

    def subscribe(self, *_a, **_k) -> None:
        pass

    def unsubscribe(self, *_a, **_k) -> None:
        pass

    def datos_de(self, nombre: str) -> dict:
        for n, d in self.emitidos:
            if n == nombre:
                return d
        raise AssertionError(
            f"nunca se emitió {nombre}; emitidos: {[n for n, _ in self.emitidos]}"
        )


@pytest.fixture(autouse=True)
def _video():
    """`pygame.init()` con una superficie liviana.

    No reutiliza `datos_del_nivel` (module-scoped, carga el `.tmx` entero):
    las pruebas de esta sección construyen los enemigos a mano y sólo
    necesitan pygame inicializado, igual que hacen las pruebas del framework
    citadas arriba.
    """
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


def _con_proyectil_sobre_el_jugador(Enemigo, jugador, bus):
    """Dispara un proyectil y lo coloca encima del jugador.

    Mismo montaje que `_arquero_con_flecha_encima` de
    `tests/test_parada_que_aturde.py` (profesor): dispara de verdad —para
    ejercitar el mismo camino que corre en el juego— y después mueve el
    proyectil ya en vuelo hasta la hurtbox del jugador, en vez de fingir la
    colisión.
    """
    enemigo = Enemigo(pygame.Vector2(50.0, 40.0))
    enemigo._event_bus = bus
    enemigo.set_player_ref(jugador.rect)
    enemigo._fire_at_player()
    assert enemigo._active_projectiles, "el montaje no llegó a disparar nada"
    proyectil = enemigo._active_projectiles[0]
    proyectil.rect.center = jugador.hurtbox.center
    proyectil.position.update(jugador.position)
    return enemigo, proyectil


@pytest.mark.parametrize("Enemigo", ENEMIGOS_QUE_DISPARAN)
def test_disparar_manda_la_posicion_del_proyectil(Enemigo) -> None:
    """AUD-489: sin `pos`, `sonido.py._make_sfx_handler` cae al canal ciego
    (`_play_sfx_named`) en vez del posicional (`_play_sfx_spatial`) — un
    disparo fuera de cámara sonaría igual de fuerte que uno encima del
    jugador. `VFX_PARRY` ya mandaba `pos`; `SFX_PROJECTILE_FIRE` no.
    """
    enemigo = Enemigo(pygame.Vector2(50.0, 40.0))
    bus = _BusEspiaConDatos()
    enemigo._event_bus = bus
    enemigo.set_player_ref(pygame.Rect(200, 0, 20, 32))

    enemigo._fire_at_player()

    datos = bus.datos_de("SFX_PROJECTILE_FIRE")
    assert datos.get("pos") == enemigo.rect.center, (
        "SFX_PROJECTILE_FIRE debe salir desde el mismo punto que se usa "
        "como spawn_position del Projectile, no a ciegas"
    )


@pytest.mark.parametrize("Enemigo", ENEMIGOS_QUE_DISPARAN)
def test_parar_un_proyectil_aturde_y_suena(Enemigo) -> None:
    """AUD-206 / AUD-064: al canónico de `enemy_base.py` (parry cuerpo a
    cuerpo) le faltaban dos cosas en el parry de proyectil de estas dos
    clases: sin `stun()` parar una bandeja/proyectil no aturdía a quien la
    lanzó (cero recompensa por leer el ataque a distancia en vez de
    esquivarlo) y sin `SFX_PLAYER_PARRY` ese parry era mudo.
    """
    from src.framework.entities.enemy_base import EnemyState
    from src.framework.entities.player import Player

    jugador = Player(pygame.Vector2(200.0, 16.0))
    bus = _BusEspiaConDatos()
    enemigo, proyectil = _con_proyectil_sobre_el_jugador(Enemigo, jugador, bus)
    jugador._parry_active = True
    jugador._parry_window = 0.2
    jugador._parry_success = False

    enemigo._check_player_contact(jugador)

    assert jugador._parry_success is True, "el parry ni siquiera se registró"
    assert enemigo.state == EnemyState.STUNNED, (
        "parar el proyectil no aturdía a quien lo disparó: parar a "
        "distancia no daba ninguna recompensa"
    )
    datos = bus.datos_de("SFX_PLAYER_PARRY")
    assert datos.get("pos") == (proyectil.position.x, proyectil.position.y), (
        "mismo pos que VFX_PARRY, para que el sonido venga del mismo sitio "
        "que el destello"
    )


# ──────────────────────────────────────────────────────────────────────────
# AUD-613 — el cartel de bienvenida se repetía en cada respawn.
#
# Causa verificada de forma determinista: `StageScene.respawn()` llama a
# `on_enter()`, que reconstruye `_stage_data` entero (StageLoader vuelve a
# leer el .tmx). El `MessageTrigger` del cartel (MSG_01) nace como objeto
# NUEVO con `triggered=False`, así que `hazard_system.py:96-98` lo vuelve a
# disparar cada vez que el jugador muere y reaparece sin checkpoint.
#
# El montaje del escenario completo (GameContext + SceneManager.push) sigue
# el mismo patrón que `tests/ayudantes_stage4_1.py::construir_escena` usa
# para el 4-1 (profesor); vive aquí y no allá porque `tests/` es del
# profesor y este nivel es de este estudiante.
# ──────────────────────────────────────────────────────────────────────────


def _construir_escena_la_soda():
    """Un `Stage1_2_LaSoda` cargado, con jugador, listo para `update`/`respawn`."""
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    from src.stages.stage1_2_la_soda.stage1_2_la_soda import Stage1_2_LaSoda

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    sc = Stage1_2_LaSoda(ctx)
    ctx.scene_manager.push(sc)
    return sc


def test_el_cartel_de_bienvenida_no_se_repite_tras_un_respawn():
    """Dispara el cartel de bienvenida por el camino real —
    `HazardSystem.update()`, exactamente `hazard_system.py:93-98` — y
    comprueba que sobrevive a un `respawn()`.

    El disparo se hace llamando a `sc._hazards.update(...)` directamente en
    vez de correr un fotograma completo con el jugador reposicionado a mano:
    `sc.update()` incluye la resolución de colisiones del framework, y forzar
    a mano la posición del jugador exactamente sobre un objeto de disparo (no
    pensado para tener un sólido debajo en esa Y exacta) lo embebía en la
    geometría y lo expulsaba del mapa — un artefacto del montaje de la
    prueba, no el bug que se está reproduciendo. Llamar a `HazardSystem`
    directamente ejercita la única línea que de verdad importa
    (`mt.triggered = True`) sin arrastrar la física.

    Para que la bandera persista hace falta un fotograma real de
    `Stage1_2_LaSoda.update()` (ahí vive el arreglo, siguiendo el patrón de
    `_room_transition`), así que se corre uno — con el jugador en un sitio
    seguro, la posición no le importa a esa lógica.
    """
    from src.engine.core.events import Events

    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))

    sc = _construir_escena_la_soda()
    # AUD-640 — el mapa ahora trae MSG_01 (bienvenida) más los tres carteles
    # de guía nuevos; MSG_01 sigue siendo el primero en el .tmx, así que
    # `message_triggers[0]` sigue siendo el cartel de esta prueba.
    assert len(sc._stage_data.message_triggers) == 4, (
        "el mapa trae MSG_01 (bienvenida) y los tres carteles de guía de "
        "AUD-640 (MSG_02_RutaAlta/MSG_03_Fachada/MSG_04_Cocina); si este "
        "número cambió, hay que revisar esta prueba"
    )
    cartel = sc._stage_data.message_triggers[0]
    assert cartel.triggered is False, "arranca sin haberse mostrado todavía"

    # Dispara el cartel por el camino real del framework.
    sc._player.rect.center = cartel.rect.center
    sc._hazards.update(1 / 60, sc._player, sc._stage_data)
    assert cartel.triggered is True, "el montaje no llegó a disparar el cartel"

    # Un fotograma de la escena del estudiante para que la persistencia (si
    # existe) tenga ocasión de registrar el disparo. Jugador en su spawn:
    # a esta lógica no le importa dónde está parado.
    sc._player.set_spawn(pygame.Vector2(sc._stage_data.spawn_point))
    sc.update(1 / 60)

    sc.respawn()

    cartel_tras_respawn = sc._stage_data.message_triggers[0]
    assert cartel_tras_respawn is not cartel, (
        "si esto empieza a fallar, StageScene ya no reconstruye "
        "message_triggers en cada respawn y el resto de la prueba no aplica"
    )
    assert cartel_tras_respawn.triggered is True, (
        "el cartel de bienvenida se volvió a mostrar tras un respawn: su "
        "bandera 'triggered' nació en False otra vez en el objeto "
        "reconstruido por on_enter()"
    )

    # Y de verdad no se vuelve a disparar: parado otra vez sobre el
    # disparador nuevo, HazardSystem no debe encolar un SHOW_MESSAGE más.
    sc._player.rect.center = cartel_tras_respawn.rect.center
    marca = len(sc.context.event_bus._queue)
    sc._hazards.update(1 / 60, sc._player, sc._stage_data)
    nuevos = sc.context.event_bus._queue[marca:]
    assert not any(nombre == Events.SHOW_MESSAGE for nombre, _ in nuevos), (
        "el cartel volvió a encolar SHOW_MESSAGE después del respawn"
    )


# ──────────────────────────────────────────────────────────────────────────
# AUD-619 — al elegir CONTINUAR en la pantalla de fin de partida (o cargar
# una partida) el jugador reaparecía hundido en el piso y el resolutor lo
# eyectaba al borde del mapa, cayendo fuera de cámara: "solo se ve su sombra".
#
# Causa (verificada de forma determinista con la escena real): los 6
# checkpoints viven en y=576 con altura 32, así que su `bottom` es 608 — 16px
# POR DEBAJO del tope del suelo sólido (y=592, el Solid que recorre todo el
# mapa). `progression_system.process_checkpoints` deriva el punto de respawn
# como esquina superior-izquierda de la caja del jugador
# `(cp.centerx - ANCHO/2, cp.bottom - ALTO)` → los pies caen en 608, incrustados
# 16px dentro del suelo. `resolver_eje_x` (`resolucion.py`) corre antes que el
# eje Y y, con el cuerpo incrustado y `velocity.x == 0`, lo eyecta al borde
# horizontal más cercano del sólido gigante: x=3456 (o x=-20 en los del lado
# izquierdo). El jugador cae entonces por fuera del mapa; en el interior la
# transición de la puerta lo recoloca en ROOM_LIMIT_X+32 pero con la `y` de la caída
# ya acumulada, así que sigue cayendo por debajo del piso — la sombra (que el
# sistema de dibujado pinta aparte) queda visible sobre el suelo, el sprite no.
#
# No era iluminación: cp6 (x=2940) cae en la zona de la cocina (brillo 0.68,
# medido con `_aplicar_hora`), no en la sala de 0.48. A 0.48 el sprite se
# dibuja igual; la causa es geométrica.
# ──────────────────────────────────────────────────────────────────────────


def test_el_respawn_en_cada_checkpoint_deja_al_jugador_apoyado():
    """CONTINUAR desde cualquiera de los 6 checkpoints tiene que devolver al
    jugador apoyado y cerca del punto de control, nunca eyectado al borde del
    mapa cayendo por fuera de la cámara.

    Se ejercita el camino real del botón CONTINUE de la pantalla de fin de
    partida (`GameOverScene._activate` → `StageScene.respawn()`): se fija
    `_checkpoint_position` al valor exacto que `process_checkpoints` derivaría
    de cada rect y se llama a `respawn()` de verdad. El interior tiene un
    caso extra: el jugador reaparece pasado `TRIGGER_X`, así que
    `maybe_trigger` dispara la transición de la puerta y lo deja en
    `ROOM_LIMIT_X + ENTRY_OFFSET` (2592) — es el comportamiento correcto, no
    una eyección.

    AUD-629 — Checkpoint_05 (x≈2457) cambia de lado con la separación de
    constantes: antes, con una sola `DOOR_X=2560` haciendo de límite y de
    disparador a la vez, ese checkpoint quedaba del lado "exterior"
    (2457 < 2560) y CONTINUAR ahí no cruzaba la puerta. Con `TRIGGER_X=2416`
    (el centro del vano movido, ver AUD-629 en `_RoomTransition`), ese mismo
    checkpoint queda a la derecha del disparador (2457 >= 2416) — tiene
    sentido: está pintado físicamente pasado el vano de la fachada nueva,
    así que reaparecer ahí completa la entrada en vez de dejar al jugador
    "flotando" en la mitad de una puerta ya cruzada.

    `_room_transition` se reconstruye a mano antes de cada CONTINUAR (en vez
    de dejar que el None-guard de `on_stage_start` lo preserve, que es lo
    que hace en el juego real). Es deliberado y sólo afecta a esta prueba:
    `_triggered` es de un solo disparo por diseño (un jugador real sólo
    "continúa" una vez por sesión de sala), así que si dos checkpoints
    seguidos cruzan `TRIGGER_X` en el mismo bucle -- ahora ocurre con
    Checkpoint_05 (2457) antes de llegar a Checkpoint_06 (2942) -- el
    segundo hereda el `_triggered=True` del primero y su propio
    `maybe_trigger` nunca llega a correr. Cada iteración de este bucle
    simula un CONTINUAR independiente (una partida distinta, no una cadena
    de teletransportes), así que cada una necesita su propia transición sin
    usar.
    """
    from src.framework.entities.player import Player
    from src.stages.stage1_2_la_soda.stage1_2_la_soda import _RoomTransition

    sc = _construir_escena_la_soda()
    for cp in sc._stage_data.checkpoints:
        px = cp.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = cp.rect.bottom - Player.ALTO_DE_PIE
        sc._checkpoint_position = pygame.Vector2(px, py)
        sc._room_transition = None
        sc.respawn()
        for _ in range(15):
            sc.update(1 / 60)
        p = sc._player
        assert p.is_grounded, (
            f"cp{cp.checkpoint_id}: tras CONTINUAR el jugador no quedó "
            f"apoyado (pos={p.position}, grounded={p.is_grounded})"
        )
        # Prohibido terminar en un borde del mapa (la eyección del respawn
        # hundido va a x=3456 o x=-20).
        assert 16.0 < p.position.x < 3456.0 - 16.0, (
            f"cp{cp.checkpoint_id}: tras CONTINUAR el jugador quedó en "
            f"x={p.position.x:.0f} — borde del mapa"
        )
        esperado = (
            px if px < _RoomTransition.TRIGGER_X
            else _RoomTransition.ROOM_LIMIT_X + _RoomTransition.ENTRY_OFFSET
        )
        assert abs(p.position.x - esperado) < 300, (
            f"cp{cp.checkpoint_id}: esperado x≈{esperado:.0f} (el checkpoint, "
            f"o la puerta si está dentro del interior), quedó en "
            f"x={p.position.x:.0f}"
        )


# ──────────────────────────────────────────────────────────────────────────
# AUD-614 — iluminación por color (regla 4 de docs/niveles/02_STAGE_1_2.md:
# cocina cálida vs sala fría), FrictionZone del piso trapeado de la cocina
# y CameraZoomZone sobre el salto exigente (Bloque_Alto_01/02).
#
# Tarea 1 midió estado.factor_ambiente a las 14:00 con day_length=900:
# 1.08 (verano, factor_luz=1.08, sobre un factor de reloj puro de 1.00
# exacto en la parada "mediodía"/"tarde" de day_night.py). El reloj NO
# atenúa a esa hora -- si acaso suma un poco -- así que no se declaró una
# AmbientLightZone en el camino exterior: sólo hacen falta las dos del
# interior, que es donde vive el contraste de la Unidad V que pide la
# ficha del nivel.
# ──────────────────────────────────────────────────────────────────────────


def _rect_tmx(nombre: str) -> pygame.Rect:
    """Rect de un objeto del .tmx por nombre, leído del XML crudo.

    Deliberado: no se fija la coordenada de memoria (el aviso de la
    consigna es real -- un mapa editado en Tiled puede mover un objeto y
    dejar viejo un número escrito a mano). Esto lee el archivo en cada
    corrida, igual que hace `TestElTmxDeclaraElMaterial` del profesor en
    `tests/test_el_musgo_resbala.py` con las zonas de musgo del 4-1.
    """
    root = ET.parse(TMX).getroot()
    for obj in root.iter("object"):
        if obj.get("name") == nombre:
            return pygame.Rect(
                int(float(obj.get("x"))), int(float(obj.get("y"))),
                int(float(obj.get("width"))), int(float(obj.get("height"))),
            )
    raise AssertionError(f"no se encontró el objeto {nombre!r} en el .tmx")


def _zonas_de_friccion(datos) -> list:
    """Las `ZonaDeFriccion` que trae el mapa, vía `stage.componentes`.

    A diferencia de `zonas_luz_ambiente`/`zonas_zoom` (listas propias en
    `StageData`), `FrictionZone` se resuelve como componente ECS suelto
    (`stage_objetos.py`, "la escena hace `mundo.crear(*grupo)`") y vive en
    `stage.componentes: list[list[object]]`.
    """
    from src.framework.ecs import ZonaDeFriccion

    return [
        c for grupo in datos.componentes for c in grupo
        if isinstance(c, ZonaDeFriccion)
    ]


class TestIluminacionCocinaYSala:
    """GAP-072.4 / AUD-598 aplicado a La Soda: dos `AmbientLightZone` en el
    interior, cocina más cálida que sala."""

    def test_declara_exactamente_dos_zonas_el_interior_sin_el_exterior(
        self, datos_del_nivel,
    ) -> None:
        zonas = datos_del_nivel.zonas_luz_ambiente
        assert len(zonas) == 2, (
            "se esperan sólo las dos del interior (cocina y sala); la del "
            "camino exterior se descartó a propósito -- ver Tarea 1 en el "
            f"informe. Encontradas: {len(zonas)}"
        )
        for z in zonas:
            assert z.rect.left >= 2560, (
                "ninguna AmbientLightZone debería vivir en el camino "
                "exterior (x < ROOM_LIMIT_X=2560)"
            )

    def test_la_cocina_es_estrictamente_mas_calida_que_la_sala(
        self, datos_del_nivel,
    ) -> None:
        """AUD-615: se dejó de fijar 0.7/0.9 a pelo -- esos números eran los
        que invertían la jerarquía de luz del nivel (ver clase
        `TestJerarquiaDeLuzDelNivel` más abajo). Lo que importa acá es la
        RELACIÓN, no los números sueltos: por eso la prueba ya no ancla
        valores concretos, sólo el contraste mínimo que exige la regla 4 de
        `02_STAGE_1_2.md` (tiene que leerse a primera vista).
        """
        zonas = sorted(datos_del_nivel.zonas_luz_ambiente, key=lambda z: z.valor)
        sala, cocina = zonas[0], zonas[1]
        assert cocina.valor > sala.valor, (
            "el contraste es el requisito de diseño (regla 4 de "
            "02_STAGE_1_2.md), no sólo los números sueltos por separado"
        )
        # El contraste del commit anterior (0.9 vs 0.7) era de 0.20 -- se
        # conserva ese orden de magnitud como piso: por debajo de eso el
        # contraste deja de leerse "a primera vista" y se vuelve simbólico.
        assert cocina.valor - sala.valor >= 0.15, (
            "el contraste cocina/sala se aplastó -- regla 4 de "
            "02_STAGE_1_2.md pide que se lea a primera vista, no que sea "
            "simbólico"
        )
        # AUD-598: `valor` se satura duro a [0, 1] -- ninguna de las dos
        # debería acercarse al tope de forma que un futuro cambio la
        # recorte en silencio.
        assert 0.0 < sala.valor < 1.0
        assert 0.0 < cocina.valor < 1.0

    def test_la_cocina_cubre_el_mostrador_y_al_cocinero(self, datos_del_nivel) -> None:
        """Si la zona cálida no llega hasta el `HazardZone`/el
        `ShooterCocinero`, el contraste no coincide con la amenaza que se
        supone que ilumina."""
        cocina = max(datos_del_nivel.zonas_luz_ambiente, key=lambda z: z.valor)
        hazards = datos_del_nivel.hazard_zones
        assert hazards, "el nivel debe traer su HazardZone del mostrador"
        for hz in hazards:
            assert cocina.rect.contains(hz.rect), (
                "la zona cálida de la cocina no cubre el HazardZone del "
                "mostrador"
            )
        cocineros = [
            e for e in datos_del_nivel.entity_list
            if type(e).__name__ == "ShooterCocinero"
        ]
        assert cocineros, "no se encontró ningún ShooterCocinero en el mapa"
        for c in cocineros:
            assert cocina.rect.collidepoint(c.rect.center), (
                "el ShooterCocinero debería quedar dentro de la zona "
                "cálida de la cocina"
            )

    def test_la_sala_y_la_cocina_se_solapan_y_la_cocina_gana(
        self, datos_del_nivel,
    ) -> None:
        """Punto 4 del mecanismo (`simulacion.py::_ambiente_base_del_fotograma`):
        con zonas solapadas manda la ÚLTIMA declarada en el .tmx. Acá el
        solape es a propósito -- evita que el `fundido` de la última zona
        atenúe hacia el brillo base del mapa (más oscuro que las dos)
        justo en el borde compartido en vez de hacia la zona vecina.
        """
        zonas = datos_del_nivel.zonas_luz_ambiente
        sala = min(zonas, key=lambda z: z.valor)
        cocina = max(zonas, key=lambda z: z.valor)
        assert sala.rect.colliderect(cocina.rect), (
            "sala y cocina deberían solaparse un poco en el borde común, "
            "a propósito (ver docstring)"
        )
        # `_zonas_luz_ambiente` (la escena) preserva el orden de lectura
        # del .tmx (AUD-598); la cocina tiene que ser la ÚLTIMA de las dos
        # para que gane sobre el fundido de la sala en el solape.
        assert zonas.index(cocina) > zonas.index(sala), (
            "la cocina tiene que estar declarada DESPUÉS de la sala en el "
            ".tmx para ganar el solapamiento (punto 4 del mecanismo)"
        )


class TestFrictionZoneDelPisoTrapeado:
    """Tarea 3 -- AUD-522 (`inercia`), piso recién trapeado de la cocina."""

    def test_usa_inercia_no_multiplicador(self, datos_del_nivel) -> None:
        zonas = _zonas_de_friccion(datos_del_nivel)
        assert len(zonas) == 1, (
            f"se esperaba una sola FrictionZone nueva; halladas: {len(zonas)}"
        )
        zona = zonas[0]
        assert zona.material == "hielo"
        # AUD-236: multiplicador > 1 "se dispara sin tope"; inercia nunca
        # se aleja del objetivo, sólo tarda en llegar -- por eso es la
        # elegida para un resbalón real y no sólo un frenado.
        assert 0.0 < zona.inercia < 1.0
        assert zona.multiplicador == 1.0, (
            "inercia y multiplicador son mutuamente excluyentes "
            "(components.py, AUD-522) -- no declarar multiplicador y "
            "dejarlo en su default es la forma correcta de asegurar que "
            "gane inercia"
        )
        assert zona.arrastre == 0.0, (
            "el piso trapeado resbala, no arrastra como una cinta"
        )

    def test_no_toca_el_hazard_ni_el_borde_de_la_platform_del_entrepiso(
        self, datos_del_nivel,
    ) -> None:
        """Restricción de diseño dura de la Tarea 3: el resbalón es un
        detalle de sabor, no puede empujar al jugador hacia el
        `HazardZone` del mostrador ni cerca del borde de
        `Plataforma_Entrepiso_01` (la plataforma de un sentido)."""
        zona = _zonas_de_friccion(datos_del_nivel)[0]
        for hz in datos_del_nivel.hazard_zones:
            assert not zona.rect.colliderect(hz.rect), (
                "la FrictionZone no debe solapar el HazardZone del "
                "mostrador"
            )
        MARGEN_MINIMO_AL_BORDE = 32
        for plataforma in datos_del_nivel.one_way_rects:
            distancia_x = max(
                plataforma.left - zona.rect.right,
                zona.rect.left - plataforma.right,
                0,
            )
            assert not zona.rect.colliderect(plataforma)
            assert distancia_x >= MARGEN_MINIMO_AL_BORDE or zona.rect.top >= plataforma.bottom, (
                "la FrictionZone queda demasiado cerca del borde de una "
                "plataforma de un sentido"
            )

    def test_no_toca_la_franja_de_patrulla_de_ningun_enemigo(
        self, datos_del_nivel,
    ) -> None:
        """Otro nivel ya tuvo un enemigo cuya franja de patrulla tapaba un
        punto de aparición; acá se comprueba lo equivalente para el
        resbalón: que no quede dentro del vaivén de ningún caminante."""
        zona = _zonas_de_friccion(datos_del_nivel)[0]
        for entidad in datos_del_nivel.entity_list:
            origen = getattr(entidad, "_patrol_origin", None)
            largo = getattr(entidad, "patrol_length", None)
            if origen is None or not largo:
                continue
            franja = pygame.Rect(
                int(origen.x - largo / 2), int(entidad.rect.top),
                int(largo), int(entidad.rect.height),
            )
            assert not zona.rect.colliderect(franja), (
                f"la FrictionZone se solapa con la franja de patrulla de "
                f"{type(entidad).__name__}"
            )


# ──────────────────────────────────────────────────────────────────────────
# AUD-620 — la FrictionZone de la cocina no se sentía: "no lo sentí
# honestamente". Medido con la escena real (entrar/salir de la zona, andar y
# soltar): `sistema_friccion` corre ANTES que `player.update` y los estados
# `IdleState`/`WalkingState` sobreescriben `velocity.x` cada fotograma
# (grounded.py:78/175/179), revirtiendo el mezclado de `inercia` antes de la
# integración — con y sin zona el jugador frena de 90 px/s a 0 en un solo
# fotograma (resbalón medido: 0.0 px en los dos casos).
#
# El arreglo no puede ser "más inercia" (sigue sobreescrita): la única
# palanca que el jugador lee DENTRO de su update es `perfil.friccion` (lo
# consume `_aplicar_friccion_y_aceleracion` antes de integrar el eje X, y es
# el mismo mecanismo que el motor usa para el suelo mojado en
# `_aplicar_agarre`). La stage fija `friccion > 0` mientras el jugador toca
# la zona: soltar la tecla decelera de walk_speed a 0 a ritmo acotado — el
# resbalón — y fuera de la zona se restaura 0 (frenado instantáneo de
# siempre).
# ──────────────────────────────────────────────────────────────────────────


def test_el_piso_trapeado_resbala_al_soltar_la_tecla():
    """Soltar la tecla DENTRO de la FrictionZone de la cocina tiene que
    producir un deslizamiento medible; fuera de la zona, el frenado sigue
    siendo instantáneo (0 px). Mide velocidad y posición fotograma a
    fotograma con la escena real, igual que el reporte de la tarea."""
    from src.engine.input.action_map import Action
    from tests.playtest.bot import _StubInput

    sc = _construir_escena_la_soda()
    zona = _zonas_de_friccion(sc._stage_data)[0]
    # Partida "ya dentro del interior" para que la transición de la puerta
    # no teletransporte al jugador durante la medición.
    sc._room_transition.disarm_to_interior()
    # Neutraliza enemigos cercanos: el montaje mide fricción, no combate
    # (un contacto re-armaría el parpadeo y ensuciaría la velocidad).
    for entidad in sc._stage_data.entity_list:
        if abs(entidad.position.x - zona.rect.left) < 500:
            entidad.position.x = -500.0
            entidad.rect.x = -500
    stub = _StubInput()
    sc.context.input_manager = stub
    sc._player.set_spawn(pygame.Vector2(zona.rect.left + 5, zona.rect.top))
    for _ in range(6):
        sc.update(1 / 60)

    stub.set_actions({Action.MOVE_RIGHT})
    for _ in range(30):
        sc.update(1 / 60)
    v0 = sc._player.velocity.x
    x0 = sc._player.position.x
    assert v0 > 0, "el montaje no llegó a andar dentro de la zona"
    assert zona.rect.colliderect(sc._player.rect), (
        "el montaje no puso al jugador dentro de la FrictionZone"
    )

    stub.set_actions(set())
    velocidades: list[float] = []
    for _ in range(90):
        sc.update(1 / 60)
        velocidades.append(sc._player.velocity.x)
    resbalon = sc._player.position.x - x0

    assert resbalon > 20, (
        f"el piso trapeado no resbaló: al soltar dentro de la zona el "
        f"jugador se deslizó {resbalon:.1f}px (antes del arreglo: 0.0px "
        f"— la zona no tenía ningún efecto en el jugador en suelo)"
    )
    assert max(velocidades[6:]) > 0.2 * v0, (
        "la velocidad tiene que decaer gradualmente (resbalón real), no "
        "cortarse a cero en el primer fotograma tras soltar"
    )


def test_fuera_de_la_zona_el_frenado_sigue_siendo_instantaneo():
    """El resbalón es un detalle del piso trapeado: un paso fuera de la zona
    tiene que frenar al instante como siempre, sin arrastrar inercia."""
    from src.engine.input.action_map import Action
    from tests.playtest.bot import _StubInput

    sc = _construir_escena_la_soda()
    zona = _zonas_de_friccion(sc._stage_data)[0]
    sc._room_transition.disarm_to_interior()
    for entidad in sc._stage_data.entity_list:
        if abs(entidad.position.x - zona.rect.left) < 500:
            entidad.position.x = -500.0
            entidad.rect.x = -500
    stub = _StubInput()
    sc.context.input_manager = stub
    # Fuera de la zona, con margen de sobra: el piso normal de la cocina, a
    # la izquierda del rect (caminar 30 frames ≈ 45 px no alcanza a tocarlo).
    sc._player.set_spawn(pygame.Vector2(zona.rect.left - 120, zona.rect.top))
    for _ in range(6):
        sc.update(1 / 60)

    stub.set_actions({Action.MOVE_RIGHT})
    for _ in range(30):
        sc.update(1 / 60)
    assert not zona.rect.colliderect(sc._player.rect), (
        "el montaje no debería tocar la FrictionZone en esta prueba"
    )
    x0 = sc._player.position.x
    stub.set_actions(set())
    for _ in range(30):
        sc.update(1 / 60)
    resbalon = sc._player.position.x - x0
    assert resbalon < 1.0, (
        f"fuera de la zona el frenado tiene que ser instantáneo; se midió "
        f"un deslizamiento de {resbalon:.1f}px"
    )


class TestCameraZoomZoneDelSaltoExigente:
    """Tarea 4 -- AUD-601, sobre el hueco entre Bloque_Alto_01 y
    Bloque_Alto_02. Respondía a la nota de la Evaluación I: "ningún salto
    pone a prueba al jugador".

    AUD-635 -- la `CameraZoomZone_SaltoExigente` (id=262, factor=1.25)
    que declaraba esta clase se retiró del `.tmx`: es un defecto del
    motor (GAP-072.3, ver docstring de
    `test_ninguna_camera_zoom_zone_declara_un_factor_riesgoso` más abajo),
    no algo corregible desde este nivel de estudiante, y el dueño decidió
    quitarla en vez de esperar el arreglo. `test_la_zona_cubre_el_hueco_
    completo_con_margen` y `test_el_factor_acerca_un_poco_sin_cerrar_la_
    lectura` (las dos dependían de que la zona existiera) se retiraron
    con ella; el hueco de 64px entre los bloques sigue siendo real (ver
    la primera prueba) y las dos de abajo dejan el guardarraíl.
    """

    def test_el_hueco_medido_en_el_tmx_sigue_siendo_de_64px(self) -> None:
        """Ancla de la prueba siguiente: si esto deja de ser 64, el resto
        de esta clase puede estar validando un hueco que ya no existe."""
        b1 = _rect_tmx("Bloque_Alto_01")
        b2 = _rect_tmx("Bloque_Alto_02")
        assert b1.right < b2.left, "se asume Bloque_Alto_01 a la izquierda"
        assert b2.left - b1.right == 64

    def test_ninguna_camera_zoom_zone_declara_un_factor_riesgoso(
        self, datos_del_nivel,
    ) -> None:
        """AUD-635 -- el zoom cinematográfico del motor
        (`dibujo.py:46-62`, AUD-601/GAP-072.3) dibuja el mundo en un
        lienzo de `800/zoom × 600/zoom` recortado desde la esquina
        superior izquierda de la cámara y lo reescala después. El
        problema: `camera.offset` (`camera.py`) y el dibujo de las
        entidades (`player.py:967-968`: `screen_x = position.x -
        camera_offset.x`, sin dividir ni multiplicar por `zoom`) no saben
        que el lienzo es más chico -- proyectan como si siguiera siendo
        de 800×600. Con el suelo de este mapa en y=592 de un viewport de
        600px, cualquier `factor` > ~1.09 empuja al jugador de pie fuera
        del lienzo recortado antes de reescalar. Medido con la escena
        real: jugador quieto sobre `Bloque_Alto_01` (x=780,y=496) dentro
        de la extinta `CameraZoomZone_SaltoExigente` con factor=1.25 —
        0 píxeles del jugador visibles, desaparece por completo (capturas
        en `Claude - Uso General/previews/ZOOM_*.png`).

        Es un defecto del motor (GAP-072.3), fuera del alcance de este
        nivel de estudiante: el dueño decidió quitar la zona en vez de
        esperar el arreglo. Esta prueba deja el guardarraíl permanente —
        ninguna `CameraZoomZone` futura de este mapa puede declarar un
        factor que reproduzca el problema.
        """
        for zona in datos_del_nivel.zonas_zoom:
            assert zona.factor <= 1.09, (
                f"CameraZoomZone con factor={zona.factor} saca al jugador "
                "del cuadro (AUD-635, dibujo.py:46-62): el lienzo "
                "recortado del zoom no coincide con lo que proyectan "
                "camera.offset y las entidades"
            )

    def test_ya_no_queda_ninguna_camera_zoom_zone_en_el_hueco(
        self, datos_del_nivel,
    ) -> None:
        """AUD-635 -- reemplaza a `test_la_zona_cubre_el_hueco_completo_
        con_margen`: la `CameraZoomZone_SaltoExigente` (id=262) que esa
        prueba verificaba se eliminó del `.tmx` junto con el resto del
        feature (ver docstring de la clase); ya no hay ninguna zona que
        deba cubrir el hueco."""
        assert datos_del_nivel.zonas_zoom == [], (
            "se esperaba que no quedara ninguna CameraZoomZone en el "
            f"mapa tras AUD-635; halladas: {datos_del_nivel.zonas_zoom}"
        )


# ──────────────────────────────────────────────────────────────────────────
# AUD-615 — la jerarquía de luz quedó invertida en AUD-614: el .tmx no
# declaraba `ambient_light`, así que el camino exterior caía al default de
# zona `AMBIENT_BY_ZONE[0] = 0.62` (comentario original: "prólogo: exterior
# nublado", `ambiente.py:41-47`) y encima **sin** la banda horaria de las
# 14:00 sumando -- eso sólo se aplica FUERA de una `AmbientLightZone`.
# Resultado medido con la fórmula real (`simulacion.py:171-181`):
#
#   camino exterior (sin zona) = max(0.45, 0.62*1.08) = 0.6696  <- el más oscuro
#   sala   (AmbientLightZone, valor=0.7)               = 0.70
#   cocina (AmbientLightZone, valor=0.9)                = 0.90  <- el más claro
#
# El sol tropical de las 2pm quedaba como el sitio MÁS OSCURO del nivel. La
# corrección declara `ambient_light` explícito en el mapa (arreglo idiomático
# -- lo hacen `stage0`=0.70 y `stage4_1`=0.6, y el de acá tiene que ser más
# alto que los dos porque es el único de sol directo) y baja los `valor` de
# las dos zonas del interior para que ninguna le gane al exterior. Ver el
# informe del commit para la tabla completa y la justificación de cada
# número.
# ──────────────────────────────────────────────────────────────────────────


def _brillo_ambiente_con_jugador_en(sc, punto: tuple[float, float]) -> float:
    """El `ambient_brightness` real que aplicaría el motor con el jugador
    parado en `punto`, vía el camino real (`_aplicar_hora`, que lee la
    posición del jugador en `_ambiente_base_del_fotograma`).

    No se reimplementa la fórmula: se llama al método real de
    `SimulacionDeEscenario` sobre una escena montada de verdad, para que
    esta prueba se rompa si el motor cambia la cuenta y no sólo si alguien
    vuelve a desordenar los `valor` del .tmx.
    """
    sc._player.rect.center = punto
    sc._aplicar_hora()
    return sc._lighting.ambient_brightness


class TestJerarquiaDeLuzDelNivel:
    """AUD-615 -- GAP-072.4 corregido: el camino exterior (sol tropical de
    las 2pm) tiene que ser el tramo más brillante del nivel, y cruzar la
    puerta (`ROOM_LIMIT_X = 2560`) tiene que producir una CAÍDA de
    luminancia -- es el insumo de la mecánica de "adaptación a la penumbra"
    de la Evaluación Práctica II (`FilterTools.compute_histogram()` mide la
    caída real de luminancia al cruzar `ROOM_LIMIT_X`).
    """

    def test_el_exterior_es_mas_brillante_que_la_cocina_y_esta_mas_que_la_sala(
        self,
    ) -> None:
        sc = _construir_escena_la_soda()

        # Punto bien dentro del camino exterior, lejos de cualquier
        # AmbientLightZone (las dos viven en x >= 2560) y de su `fundido`.
        exterior = _brillo_ambiente_con_jugador_en(sc, (200.0, 500.0))
        sala_rect = _rect_tmx("AmbientLightZone_Sala")
        cocina_rect = _rect_tmx("AmbientLightZone_Cocina")
        # Los centros de sala y cocina caen fuera del rect de la otra zona
        # (el solape de 48px es sólo en el borde común), así que cada
        # medición queda limpia -- ninguna arrastra el `valor` de la vecina.
        sala = _brillo_ambiente_con_jugador_en(sc, sala_rect.center)
        cocina = _brillo_ambiente_con_jugador_en(sc, cocina_rect.center)

        assert exterior > cocina > sala, (
            "la jerarquía de luz del nivel está invertida o aplastada: se "
            f"midió exterior={exterior:.4f}, cocina={cocina:.4f}, "
            f"sala={sala:.4f}; se espera exterior > cocina > sala (sol "
            "tropical > fluorescente de cocina > rincón fresco de sala)"
        )

    def test_cruzar_la_puerta_produce_una_caida_de_luminancia(self) -> None:
        """Requisito duro de la Evaluación Práctica II: el brillo tiene que
        CAER al cruzar `ROOM_LIMIT_X = 2560`, no subir. Se mide justo a un
        lado y al otro de la puerta (no en los extremos del nivel) porque
        es literalmente el punto que cruza el jugador.
        """
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _RoomTransition

        sc = _construir_escena_la_soda()
        door_x = _RoomTransition.ROOM_LIMIT_X
        antes_de_la_puerta = _brillo_ambiente_con_jugador_en(
            sc, (door_x - 8.0, 500.0))
        despues_de_la_puerta = _brillo_ambiente_con_jugador_en(
            sc, (door_x + 8.0, 500.0))

        assert despues_de_la_puerta < antes_de_la_puerta, (
            "cruzar la puerta tiene que producir una CAÍDA de luminancia "
            f"medible: antes={antes_de_la_puerta:.4f}, "
            f"después={despues_de_la_puerta:.4f}"
        )

    def test_la_sala_es_lo_bastante_clara_para_ver_al_jugador(self) -> None:
        """AUD-633 -- en ventana real, al entrar a la sala el sprite azul
        oscuro del jugador casi no se distinguía del fondo (capturado en
        `Claude - Uso General/playtest/sesion_20260826_0157/frame_015852.png`).
        AUD-615 dejó `valor=0.48` para la sala porque en ese momento sólo
        importaba la RELACIÓN cocina>sala (ver
        `test_la_cocina_es_estrictamente_mas_calida_que_la_sala`), no el piso
        absoluto de legibilidad del sprite -- 0.48 cumple ese contraste pero
        es demasiado oscuro para el sprite en la práctica.

        Se mide en x=2616 (bien adentro del rect de `AmbientLightZone_Sala`,
        fuera de la banda de `fundido` de 48px de cualquiera de los dos
        bordes, así que el número medido es el `valor` de la zona sin
        diluir) con el mismo método que usa el resto de esta clase
        (`_brillo_ambiente_con_jugador_en`, que llama a `_aplicar_hora` de
        verdad en vez de reimplementar la fórmula).

        El piso de 0.55 conserva la jerarquía exterior(0.864) > cocina >
        sala y el contraste mínimo de 0.15 con la cocina (ver el resto de
        esta clase) -- ver el informe de AUD-633 para la tabla completa.
        """
        sc = _construir_escena_la_soda()
        sala = _brillo_ambiente_con_jugador_en(sc, (2616.0, 500.0))
        assert sala >= 0.55, (
            "la sala sigue demasiado oscura para distinguir al jugador: "
            f"brillo medido={sala:.4f}, piso exigido=0.55"
        )


# ──────────────────────────────────────────────────────────────────────────
# Evaluación Práctica II (Unidad VI) — easing en la flotación del
# `FlyingZancudo` (AUD-637: renombrado desde `Zancudo`).
#
# La spline Catmull-Rom muestreada con `t` lineal (antes) NO es un
# movimiento de velocidad constante: su punto más lento ya es el tope del
# vaivén y el centro es justo el más rápido (medido: ~40 px/s). Por eso el
# rasgo que distingue el easing no es «lento en los extremos vs rápido en
# el centro» en general, sino el punto de retorno del FONDO: la spline
# lineal baja y sube a ~21 px/s justo en el giro, mientras que con
# `ease_in_out_quad` compuesto en una campana `4u(1-u)` la velocidad ahí se
# anula (cae a ~0) y el pico se mantiene a mitad de altura.
#
# Esta prueba mide la velocidad en el giro del fondo (ventanas de `t` en
# los extremos del recorrido) contra el pico de la flotación, y además fija
# el contrato de que el rango vertical (mín/máx de `y`) no cambió —
# requisito duro de la Tarea 3: el easing es de curva, no de rango.
# ──────────────────────────────────────────────────────────────────────────


def test_la_flotacion_del_zancudo_es_suave_en_los_extremos():
    """La flotación vertical del FlyingZancudo usa easing: la velocidad se
    anula en el punto de retorno del fondo (el «extremo del recorrido») y
    el rango vertical no cambia.

    Medido sobre el FlyingZancudo real (sin pasar por el `.tmx`), igual que
    las pruebas de AUD-489/AUD-206 de este archivo.
    """
    from src.framework.processing.curve_tools import CurveTools

    z = FlyingZancudo(pygame.Vector2(1000.0, 500.0))
    dt = 0.02
    # Descartar el primer paso: la posición nace en el spawn y la curva
    # arranca en su primer punto de control — un salto de montaje, no el
    # movimiento de la flotación.
    z._patrol_behavior(dt)

    ys: list[float] = []
    vs: list[float] = []
    tris: list[float] = []
    for _ in range(int(2 * FlyingZancudo.CURVE_PERIOD / dt)):
        y0 = z.position.y
        z._patrol_behavior(dt)
        ys.append(z.position.y)
        vs.append(abs(z.position.y - y0) / dt)
        t = z._curve_t if z._curve_t <= 1.0 else 2.0 - z._curve_t
        tris.append(t)

    tope = CurveTools.build_bezier_path(z._curve_points, 0.5).y
    fondo = z._curve_points[0].y
    assert abs(min(ys) - tope) < 0.5, (
        "el easing no debe elevar al FlyingZancudo más alto que la curva original "
        f"(medido min_y={min(ys):.2f}, tope esperado={tope:.2f})"
    )
    assert abs(max(ys) - fondo) < 0.5, (
        "el easing no debe hundir al FlyingZancudo más bajo que la curva original "
        f"(medido max_y={max(ys):.2f}, fondo esperado={fondo:.2f})"
    )

    v_pico = max(vs)
    # Velocidad justo en el punto de retorno del fondo (`t` ≈ 0 o 1). Un
    # easing anula la velocidad ahí; el muestreo lineal de la spline la
    # mantiene alta (medido: ~21 px/s). Se pide que el giro sea mucho más
    # lento que el pico de la flotación, no meramente menor.
    v_fondo = max(v for v, t in zip(vs, tris) if t < 0.03 or t > 0.97)
    assert v_fondo < 0.4 * v_pico, (
        "el giro del fondo debe ir suave (velocidad ~0) si el easing se "
        f"aplica; se midió v_fondo={v_fondo:.2f} px/s contra un pico de "
        f"v_pico={v_pico:.2f} px/s"
    )


# ──────────────────────────────────────────────────────────────────────────
# AUD-627 — el "hueco azul" que reportó el dueño: `settings.BG_COLOR =
# (15,15,40)` asoma en `drawing_system.py:142` (`surface.fill(BG_COLOR)`,
# lo primero que pinta el frame) donde las 5 capas de fondo (`BG_Far`,
# `BG_Mid`, `BG_Near`, `Terrain`, `Terrain_Detail`) tienen gid 0 a la vez.
# Diagnóstico completo, con el inventario de los 44 rectángulos / 572
# celdas y el render con overlay magenta, en
# `Claude - Uso General/DIAGNOSTICO_AUD627.md` (fuera del repo, por
# convención del proyecto). Todos viven en el exterior (columnas 0-159); el
# interior (columna >= 160) no tiene ninguno. El más grande es la huella
# que dejó AUD-626 al borrar "el kiosco/letrero de columnas 120-131...
# completo" sin rellenar -- a diferencia de AUD-622, que sí rellenó su
# propia remoción con el patrón de tierra del camino.
#
# El mismo diagnóstico encontró un tercer remanente de "Invenio" que ni
# AUD-622 (columnas 68-86) ni AUD-626 (columnas 120-131) tocaron: un cartel
# de dos líneas ("INVENIO"/"CONTINUUM") pintado directamente dentro de
# `tileset_campus.png` (gids 381-387, fila 3 de la hoja), parado sobre un
# poste en `BG_Near` columnas 60-63, filas 33-36 -- intacto desde el
# trasplante al motor nuevo y sin relación con ningún objeto ni texto de
# código.
# ──────────────────────────────────────────────────────────────────────────

_CAPAS_DE_FONDO = ("BG_Far", "BG_Mid", "BG_Near", "Terrain", "Terrain_Detail")
_COLUMNA_MAXIMA_DEL_EXTERIOR = 160  # el interior (col >= 160) no tiene huecos
_GIDS_DEL_CARTEL_INVENIO = frozenset(range(381, 388))  # tileset_campus, fila 3


def _grids_de_capas_crudos() -> dict[str, list[list[int]]]:
    """Gid crudo por capa de tiles, leído del XML del `.tmx` sin pasar por
    pytmx (que remapea internamente los gid para manejar flips y por lo
    tanto no corresponde al gid real de Tiled -- misma nota metodológica
    del diagnóstico AUD-627).

    Lee el archivo en cada corrida, igual que `_rect_tmx`: un mapa editado
    en Tiled puede mover cosas y dejar viejo un número escrito a mano.
    """
    root = ET.parse(TMX).getroot()
    ancho = int(root.get("width"))
    alto = int(root.get("height"))
    grids: dict[str, list[list[int]]] = {}
    for layer in root.findall("layer"):
        nombre = layer.get("name")
        data_el = layer.find("data")
        texto = data_el.text.strip()
        valores = [int(v) for v in texto.replace("\n", "").split(",") if v.strip()]
        assert len(valores) == ancho * alto, (
            f"{nombre}: {len(valores)} valores, se esperaban {ancho * alto}"
        )
        grids[nombre] = [valores[y * ancho:(y + 1) * ancho] for y in range(alto)]
    return grids


def test_no_quedan_celdas_vacias_en_las_5_capas_de_fondo_del_exterior():
    """Ninguna celda del exterior (columnas 0-159) puede tener las 5 capas
    de fondo en gid 0 a la vez -- eso es el `BG_COLOR` del motor asomando
    como un "hueco azul" detrás del camino."""
    grids = _grids_de_capas_crudos()
    huecos = []
    for y in range(len(grids["BG_Near"])):
        for x in range(_COLUMNA_MAXIMA_DEL_EXTERIOR):
            if all(grids[capa][y][x] == 0 for capa in _CAPAS_DE_FONDO):
                huecos.append((y, x))

    assert not huecos, (
        f"{len(huecos)} celdas del exterior sin ninguna capa de fondo "
        f"(fila, columna) -- primeras 10: {huecos[:10]}"
    )


def test_no_queda_ningun_gid_del_cartel_de_invenio_en_el_mapa():
    """Los gids 381-387 (el cartel "INVENIO"/"CONTINUUM" pintado dentro de
    `tileset_campus.png`) no son parte de la stage del alumno y tienen que
    desaparecer por completo, en cualquier capa del mapa."""
    grids = _grids_de_capas_crudos()
    hallazgos = []
    for nombre, grid in grids.items():
        for y, fila in enumerate(grid):
            for x, gid in enumerate(fila):
                if gid in _GIDS_DEL_CARTEL_INVENIO:
                    hallazgos.append((nombre, y, x, gid))

    assert not hallazgos, (
        "quedan gids del cartel de Invenio (capa, fila, columna, gid): "
        f"{hallazgos}"
    )


# ──────────────────────────────────────────────────────────────────────────
# AUD-629 — cruzar la puerta se leía como atravesar una pared en el borde de
# pantalla, no como cruzar un vano. Causa (diagnóstico completo en
# `Claude - Uso General/DIAGNOSTICO_AUD627.md` §3): `DOOR_X=2560` hacía de
# límite del cuarto Y de disparador a la vez, y con `screen_w=800` el clamp
# del exterior (`hi = DOOR_X - screen_w = 1760`) deja el borde derecho de
# pantalla exactamente en `DOOR_X` — el jugador se salía de cuadro y recién
# ahí arrancaba el fundido. Encima el vano pintado (columnas 155-158) quedaba
# 16-80px a la izquierda del disparador, así que el jugador ya había cruzado
# el hueco visual de la puerta un tile antes de que pasara nada.
#
# El arreglo separa las dos responsabilidades en dos constantes:
# `ROOM_LIMIT_X` (el límite real del cuarto — cámara, clamp de un sentido,
# destino del teletransporte — sin mover) y `TRIGGER_X` (el centro del vano,
# movido a columnas 149-152 junto con la fachada). Como FG_Overlay no puede
# tapar al jugador (se dibuja con el resto de capas de tiles, antes que las
# entidades), `_MarcoDeLaPuerta` repinta el vano DESPUÉS de `super().draw()`
# — mismo hook que ya usa la barra de vida del enemigo — para que el marco
# quede al frente y el jugador se pierda detrás de él al cruzar.
# ──────────────────────────────────────────────────────────────────────────

_GID_PUERTA_OSCURA = 500  # tileset_soda_real (firstgid 485), local id 15


def _columnas_de_la_puerta_en_bg_near() -> list[int]:
    """Columnas donde `BG_Near` pinta el gid de la puerta oscura, leído del
    `.tmx` crudo -- así el disparador se verifica contra el mapa real, no
    contra un número escrito a mano dos veces (acá y en la stage)."""
    grids = _grids_de_capas_crudos()
    columnas = set()
    for fila in grids["BG_Near"]:
        for x, gid in enumerate(fila):
            if gid == _GID_PUERTA_OSCURA:
                columnas.add(x)
    return sorted(columnas)


class TestElVanoSeLeeComoPuerta:
    """AUD-629 -- el disparador tiene que caer dentro del vano pintado y
    estrictamente antes del límite del cuarto, y ese vano tiene que caber
    entero en pantalla con la cámara en su tope del exterior."""

    def test_el_disparador_queda_a_la_izquierda_del_limite_y_dentro_del_vano(
        self,
    ) -> None:
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _RoomTransition

        columnas = _columnas_de_la_puerta_en_bg_near()
        assert columnas, "no se encontró ningún tile de puerta (gid 500) en BG_Near"
        # El gid de la puerta aparece dos veces en el mapa (la fachada
        # exterior, parte A, y el marco del interior, parte D) -- el vano de
        # la fachada es el bloque contiguo más ANCHO de los dos (4 columnas
        # contra 1 sola en el marco del interior).
        bloques: list[list[int]] = []
        for col in columnas:
            if bloques and col == bloques[-1][-1] + 1:
                bloques[-1].append(col)
            else:
                bloques.append([col])
        vano = max(bloques, key=len)
        assert len(vano) >= 2, (
            f"el vano de la fachada debería ser el bloque contiguo más "
            f"ancho, no {vano} -- bloques encontrados: {bloques}"
        )

        x_izq = vano[0] * 16
        x_der = (vano[-1] + 1) * 16
        centro_esperado = (x_izq + x_der) / 2.0

        assert _RoomTransition.TRIGGER_X == centro_esperado, (
            f"TRIGGER_X ({_RoomTransition.TRIGGER_X}) debería ser el centro "
            f"exacto del vano que pinta el .tmx ({centro_esperado}, "
            f"columnas {vano[0]}-{vano[-1]})"
        )
        assert _RoomTransition.TRIGGER_X < _RoomTransition.ROOM_LIMIT_X, (
            "el disparador tiene que quedar ESTRICTAMENTE a la izquierda "
            "del límite del cuarto -- si coinciden, vuelve el bug original "
            "(el jugador se sale de cuadro antes de que arranque el fundido)"
        )
        assert x_izq <= _RoomTransition.TRIGGER_X <= x_der, (
            "el disparador tiene que caer DENTRO del vano pintado, ni antes "
            "ni después"
        )

    def test_con_la_camara_en_su_tope_el_vano_completo_entra_en_pantalla(
        self,
    ) -> None:
        """Restricción dura del dueño: con la cámara clamped a su tope del
        exterior (`apply_camera_box`, `hi = ROOM_LIMIT_X - screen_w`), el
        vano pintado tiene que caer completo dentro de la pantalla y dejar
        >=96px de fachada de la soda a su derecha (el vano no puede pasar
        de la columna 153 / x=2464)."""
        from src.engine.core import settings
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import (
            _MarcoDeLaPuerta,
            _RoomTransition,
        )

        screen_w = settings.INTERNAL_WIDTH
        offset_x_tope = _RoomTransition.ROOM_LIMIT_X - screen_w

        vano = _MarcoDeLaPuerta.RECT
        x_pantalla_izq = vano.left - offset_x_tope
        x_pantalla_der = vano.right - offset_x_tope

        assert 0 <= x_pantalla_izq, (
            f"el borde izquierdo del vano ({x_pantalla_izq}) quedó fuera de "
            "pantalla con la cámara en su tope"
        )
        assert x_pantalla_der <= screen_w, (
            f"el borde derecho del vano ({x_pantalla_der}) quedó fuera de "
            f"pantalla (ancho={screen_w}) con la cámara en su tope"
        )

        margen_a_la_derecha = _RoomTransition.ROOM_LIMIT_X - vano.right
        assert margen_a_la_derecha >= 96, (
            f"quedan sólo {margen_a_la_derecha:.0f}px de fachada a la "
            "derecha del vano con la cámara en su tope -- el dueño pidió "
            ">=96"
        )


def test_el_marco_de_la_puerta_se_dibuja_encima_del_jugador_en_el_umbral() -> None:
    """FG_Overlay no puede tapar al jugador -- `drawing_system.py` dibuja
    TODAS las capas de tiles de una sola pasada, antes que las entidades
    (confirmado en el diagnóstico AUD-627 §3, y en el comentario ya
    existente de `stage1_1.py`). El marco tiene que dibujarse desde
    `Stage1_2_LaSoda.dibujar_mundo()`, DESPUÉS de `super().dibujar_mundo()`
    -- mismo patrón que ya usa la barra de vida del enemigo unas líneas más
    abajo.

    AUD-643 -- por qué ya no es `Stage1_2_LaSoda.draw()`/`StageScene.draw`.
    `App._draw()` nunca llama a `escena.draw()` para una `StageScene`: llama
    a `dibujar_mundo()`/`dibujar_ui()` por separado (ver el docstring de
    `Stage1_2_LaSoda.dibujar_mundo` para la evidencia completa), así que el
    marco se movió ahí. La composición `draw()` heredada (`self.
    dibujar_mundo(surface); self.dibujar_ui(surface)`) sigue resolviendo
    por polimorfismo contra ESTA clase, así que `sc.draw(...)` (que sigue
    usando el bot de playtest y `render_real.py`) sigue mostrando el marco
    sin cambios -- lo que deja de servir para "aislar el motor base" es
    llamar a `StageScene.draw(sc, ...)`: como `self` sigue siendo un
    `Stage1_2_LaSoda`, esa llamada también reenvía a `sc.dibujar_mundo`
    (el override) por el mismo despacho dinámico. Aislar de verdad exige
    llamar al método SIN pasar por el override: `DibujoDeEscenario.
    dibujar_mundo(sc, ...)` (la función del mixin, no la de la subclase).

    Se verifica a nivel de píxel: con el jugador centrado en el vano, el
    punto central de su caja tiene que salir con el color exacto del
    umbral del marco, no con lo que sea que el jugador dibuje ahí. Y ese
    mismo punto, renderizado sólo con el `dibujar_mundo` base (sin la
    extensión de la stage), NO puede ser ese color -- si lo fuera, la
    prueba no estaría aislando nada y pasaría por accidente.
    """
    from src.engine.core import settings
    from src.framework.scenes.stage_parts.dibujo import DibujoDeEscenario
    from src.stages.stage1_2_la_soda.stage1_2_la_soda import _MarcoDeLaPuerta

    sc = _construir_escena_la_soda()
    # AUD-643 — mismo motivo que en `TestIconosDeLlaveYCofre` más abajo: el
    # overlay de tutorial arranca activo (duration=6.0) y rellena la
    # pantalla ENTERA con negro a alfa 200 (`tutorial_overlay.py:99-100`)
    # DESPUÉS de `dibujar_mundo` (donde vive el marco); sin apagarlo, la
    # comparación de color exacto de esta prueba se rompe por el
    # oscurecido, no por el marco.
    if hasattr(sc, "_tutorial"):
        sc._tutorial._active = False
    vano = _MarcoDeLaPuerta.RECT
    punto_mundo = pygame.Vector2(vano.centerx, vano.centery)

    # Jugador centrado en el vano -- alcanza con `rect`/`position` (lo único
    # que lee Player.draw), no hace falta un fotograma de física real.
    sc._player.position.x = punto_mundo.x - sc._player.rect.width / 2.0
    sc._player.position.y = punto_mundo.y - sc._player.rect.height / 2.0
    sc._player.rect.x = int(sc._player.position.x)
    sc._player.rect.y = int(sc._player.position.y)

    ancho, alto = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
    sc._camera.offset.x = punto_mundo.x - ancho / 2.0
    sc._camera.offset.y = punto_mundo.y - alto / 2.0
    punto_pantalla = (int(ancho / 2), int(alto / 2))

    superficie_con_marco = pygame.Surface((ancho, alto))
    sc.draw(superficie_con_marco)
    color_con_marco = tuple(superficie_con_marco.get_at(punto_pantalla))[:3]
    assert color_con_marco == _MarcoDeLaPuerta.COLOR_UMBRAL, (
        f"el punto central del jugador en el umbral debería salir con el "
        f"color del marco {_MarcoDeLaPuerta.COLOR_UMBRAL}; salió "
        f"{color_con_marco} -- el marco no está tapando al jugador"
    )

    superficie_sin_marco = pygame.Surface((ancho, alto))
    DibujoDeEscenario.dibujar_mundo(sc, superficie_sin_marco)
    color_sin_marco = tuple(superficie_sin_marco.get_at(punto_pantalla))[:3]
    assert color_sin_marco != _MarcoDeLaPuerta.COLOR_UMBRAL, (
        "el motor base (sin la extensión de la stage) ya mostraba el color "
        "del umbral en ese punto -- el montaje de la prueba no aísla nada"
    )


def test_la_ruta_real_de_app_dibuja_las_extensiones_de_la_stage() -> None:
    """AUD-643 -- el bug del letrero invisible en el juego real.

    Diagnosticado con evidencia (`Claude - Uso General/playtest/
    repro_app_real.py`, capturas `AUD643_objetivo_real_antes.png` /
    `_despues.png`): en el juego real, `App._draw()` NUNCA llama a
    `escena.draw()` para una `StageScene` -- llama a
    `escena.dibujar_mundo(...)` y `escena.dibujar_ui(...)` **por
    separado** (`app.py:578-588,692-717`, el "camino de GPU" de AUD-343,
    activo con o sin tarjeta: `_soporta(escena, "dibujar_mundo")` no
    depende de `usar_gl`). Antes de este cambio, `Stage1_2_LaSoda`
    agregaba todas sus extensiones (barras de vida, íconos propios,
    luciérnagas, la puerta trasera de madera, el letrero de objetivo, el
    marco de la puerta) sobreescribiendo `draw()` -- un método que ese
    camino real jamás invoca. El resultado: todo lo que esta stage agrega
    encima del motor era invisible en `main.py --stage
    stage1_2_la_soda`, aunque `render_real.py`/el bot de playtest (que sí
    llaman `scene.draw()` directo) lo mostraran sin problema.

    Esta prueba reproduce el despacho de `App._draw()` sin la `App`
    entera: llama a `dibujar_mundo()` y `dibujar_ui()` por separado, tal
    como hace `app.py`, y verifica que el letrero de objetivo (la parte
    más visible del bug reportado) aparece por esa ruta.

    No compara byte a byte contra `sc.draw(...)`: los focos con
    `flicker=true` del .tmx (`Light_263`/`Light_267`) recalculan su
    parpadeo en cada llamada a dibujar, así que dos dibujados separados
    del MISMO fotograma de juego difieren en un puñado de píxeles por
    diseño -- no es una señal de que algo esté mal."""
    from src.engine.core import settings
    from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ObjetivoCocinero

    sc = _construir_escena_la_soda()
    sc._room_transition.disarm_to_interior()
    if hasattr(sc, "_tutorial"):
        sc._tutorial._active = False
    sc._msg_box.hide()

    # Jugador en la cocina, cocinero vivo -- las condiciones exactas del
    # playtest real donde el letrero nunca apareció.
    sc._player.set_spawn(pygame.Vector2(_ObjetivoCocinero.X_ENTRADA_COCINA + 20.0, 560.0))
    for _ in range(40):  # tiempo de sobra para pasar "apareciendo" -> "visible"
        sc.context.event_bus.dispatch()
        sc.update(1 / 60)
    assert sc._objetivo_cocinero.fase in ("apareciendo", "visible"), (
        "el montaje no llegó a activar el letrero -- revisar el spawn"
    )

    ancho, alto = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT

    # Ruta real de App: dibujar_mundo() y dibujar_ui() por separado.
    superficie_app = pygame.Surface((ancho, alto))
    sc.dibujar_mundo(superficie_app)
    sc.dibujar_ui(superficie_app)

    fuente_encontrada = False
    for y in range(60, 140):
        for x in range(200, 600):
            if tuple(superficie_app.get_at((x, y)))[:3] == (255, 255, 255):
                fuente_encontrada = True
                break
        if fuente_encontrada:
            break
    assert fuente_encontrada, (
        "no se encontró texto blanco (el letrero de objetivo) en la banda "
        "y=60-140 tras dibujar_mundo()+dibujar_ui() -- el letrero sigue "
        "sin aparecer por la ruta real de App"
    )


# ──────────────────────────────────────────────────────────────────────────
# AUD-630 -- `Bloque_Alto_01`, `Bloque_Alto_02` y `Plataforma_Entrepiso_01`
# (objectgroup `Collision`) tenían rect de colisión pero ningún gid pintado
# en `Terrain` ni `Terrain_Detail` en las columnas que cubren: el jugador se
# podía parar ahí, pero la pantalla mostraba aire. Se detecta comparando
# cada objeto `Bloque_Alto_*`/`Plataforma_*` del .tmx crudo contra las capas
# de tiles crudas -- no contra pytmx, por la misma razón metodológica que
# `_grids_de_capas_crudos` ya documenta (pytmx remapea gids por los flips).
# ──────────────────────────────────────────────────────────────────────────


def _objetos_de_plataforma_en_collision() -> list[tuple[str, dict]]:
    """Objetos de `Collision` que el jugador pisa por encima y por lo tanto
    necesitan tile visible en su fila superior: todo `Bloque_Alto_*` y
    `Plataforma_*`, más el mostrador (`Platform` id 218) como control
    positivo -- si ese alguna vez se queda sin arte, es la misma prueba la
    que tiene que fallar, no una excepción a la regla."""
    root = ET.parse(TMX).getroot()
    collision = None
    for og in root.iter("objectgroup"):
        if og.get("name") == "Collision":
            collision = og
            break
    assert collision is not None, "no se encontró el objectgroup Collision"

    objetos = []
    for obj in collision.findall("object"):
        nombre = obj.get("name") or ""
        es_objetivo = (
            nombre.startswith("Bloque_Alto")
            or nombre.startswith("Plataforma")
            or obj.get("id") == "218"
        )
        if es_objetivo:
            objetos.append((
                nombre,
                {
                    "x": int(float(obj.get("x"))),
                    "y": int(float(obj.get("y"))),
                    "width": int(float(obj.get("width"))),
                },
            ))
    return objetos


def test_toda_plataforma_de_colision_tiene_tile_visible_en_su_fila_superior():
    """AUD-630 -- un rect de colisión sin ningún gid pintado encima es
    suelo invisible: el jugador puede pararse ahí pero no hay forma de
    saberlo mirando la pantalla. Para cada `Bloque_Alto_*`/`Plataforma_*`
    (y el mostrador `Platform` id 218 como control positivo) la fila
    superior del rect tiene que tener gid != 0 en `Terrain` o en
    `Terrain_Detail`, en TODAS las columnas que cubre -- alcanza con
    cualquiera de las dos capas porque el mostrador pinta en `Terrain` y el
    diseño de la pasarela reparte tablón en `Terrain` y postes en
    `Terrain_Detail`."""
    grids = _grids_de_capas_crudos()
    objetos = _objetos_de_plataforma_en_collision()
    assert objetos, (
        "no se encontró ningún objeto Bloque_Alto_*/Plataforma_*/Platform "
        "en Collision -- el filtro de nombres dejó de coincidir con algo"
    )

    huecos = []
    for nombre, rect in objetos:
        fila = rect["y"] // 16
        col_inicio = rect["x"] // 16
        col_fin = math.ceil((rect["x"] + rect["width"]) / 16)
        for col in range(col_inicio, col_fin):
            if grids["Terrain"][fila][col] == 0 and grids["Terrain_Detail"][fila][col] == 0:
                huecos.append((nombre, fila, col))

    assert not huecos, (
        "plataformas/bloques de colisión sin tile visible en su fila "
        f"superior (nombre, fila, columna): {huecos}"
    )


# ──────────────────────────────────────────────────────────────────────────
# AUD-632 — los 5 `Pickup` del mapa se recogían y "no pasaba nada": el HUD
# ("0 🟡 0") seguía en cero y no aparecía ningún texto. Diagnóstico completo
# en `LA_SODA_PROGRESO.md` (dueño): `InteractableSystem._recoger()` SÍ marca
# `recogido=True` y emite `INTERACT_ITEM_PICKED`
# (`interactable_system.py:127-138`) con `item_id`/`cantidad`/`pos`, pero el
# único suscriptor del framework —`_on_item_picked` en
# `framework/scenes/stage_parts/senales.py:52-88`— sólo sabe hablar con
# `Inventory`: ninguno de los 5 `item_id` de este mapa está en su catálogo
# (`engine/core/inventory.py:_ITEM_DEFS`), así que `collect()` devuelve
# `False`, el objeto termina en el llavero (una bolsa de llaves que nadie
# mira) y ni el `mensaje` de la propiedad de Tiled ni ningún número suben.
# Es comportamiento del motor, no un bug de este nivel — los `fragmento_N`
# del `stage0` del profe se comportan igual.
#
# `_RecompensaDePickup` (en `stage1_2_la_soda.py`) es la "interacción propia
# vía EventBus" de la Unidad VI (Evaluación Práctica II) que cierra ese
# hueco: suma puntos y muestra el mensaje del pickup sin tocar el motor.
# ──────────────────────────────────────────────────────────────────────────


@pytest.fixture
def _puntuacion_aislada(tmp_path, monkeypatch):
    """`ScoreSystem` es un singleton que persiste en disco (AUD-219, ver
    `score_system.py`). Sin aislar `_SCORE_PATH`, esta prueba leería y
    escribiría el `score.json` real del usuario que corre la suite. Mismo
    patrón que usa `tests/test_puntuacion_que_se_ve.py:60-65` (del profe,
    sólo lectura -- se copia el patrón, no se importa el archivo).
    """
    from src.engine.core import score_system as score_mod
    from src.engine.core.score_system import ScoreSystem

    monkeypatch.setattr(score_mod, "_SCORE_PATH", tmp_path / "score.json")
    ScoreSystem._reset_instance()
    yield
    ScoreSystem._reset_instance()


def test_recoger_un_pickup_suma_puntos_y_muestra_su_mensaje(_puntuacion_aislada):
    """Parado sobre `Pickup_254` (`item_id="vaso_soda"`, rect
    696..712 × 512..528 en el .tmx, apoyado sobre `Bloque_Alto_01` cuyo
    tope está en y=528) un fotograma real tiene que: subir el marcador de
    puntos en 50 (AUD-636) y mostrar el `mensaje` del pickup por `Events.SHOW_MESSAGE`
    -- la misma vía que usa `MessageTrigger` (`hazard_system.py:109-111`,
    consumida por `MessageBox._on_show_message`,
    `engine/ui/message_box.py:72,82-88`).

    El bucle simula el orden real de un fotograma (`app.py:466`):
    `event_bus.dispatch()` ANTES de `scene.update()`. `EventBus.emit()`
    sólo encola -- sin el `dispatch()` explícito el evento nunca llega al
    suscriptor, y como el propio manejador emite `SHOW_MESSAGE` durante un
    `dispatch()` en curso, ese segundo evento se reencola para el `dispatch()`
    siguiente (reentrancia, `event_bus.py:174-183`): hacen falta varias
    vueltas del bucle, no una sola.
    """
    sc = _construir_escena_la_soda()
    from src.engine.core.inventory import get_inventory

    monedas_antes = get_inventory().coins

    sc._player.set_spawn(pygame.Vector2(694, 496))

    for _ in range(10):
        sc.context.event_bus.dispatch()
        sc.update(1 / 60)

    assert sc._score.score == 50, (
        f"el marcador de puntos no subió al recoger el pickup "
        f"(score={sc._score.score})"
    )
    assert sc._msg_box._visible is True, (
        "no se mostró ningún cartel al recoger el pickup"
    )
    assert sc._msg_box._full_text == (
        "Un vaso de soda a medio terminar. Alguien lo dejó camino a clases."
    ), f"el cartel no mostró el mensaje del pickup (texto={sc._msg_box._full_text!r})"

    # Decisión del dueño: la recompensa es puntos, nunca el contador de
    # monedas ni el inventario -- el llavero del motor (F4.1) absorbe el
    # item_id por su cuenta y esto no lo toca.
    assert get_inventory().coins == monedas_antes, (
        "recoger un pickup del mapa no debería tocar el contador de monedas"
    )


def test_recoger_el_mismo_pickup_tras_un_respawn_no_vuelve_a_sumar(_puntuacion_aislada):
    """`StageScene.on_enter()` reconstruye `_stage_data` en cada respawn --
    los 5 `Recogible` renacen con `recogido=False` (mismo mecanismo que
    documenta AUD-613 para el cartel de bienvenida, ver
    `stage1_2_la_soda.py:_maybe_persist_welcome_message`). Sin un registro
    propio, morir y reaparecer sobre el mismo pickup pagaría dos veces.
    """
    sc = _construir_escena_la_soda()
    sc._player.set_spawn(pygame.Vector2(694, 496))
    for _ in range(10):
        sc.context.event_bus.dispatch()
        sc.update(1 / 60)
    assert sc._score.score == 50, "no llegó a cobrar la primera vez"

    sc.respawn()
    recogibles_tras_respawn = sc._stage_data.recogibles
    assert any(
        r.item_id == "vaso_soda" and not r.recogido
        for r in recogibles_tras_respawn
    ), (
        "si esto empieza a fallar, StageScene ya no reconstruye recogibles "
        "en cada respawn y el resto de la prueba no aplica"
    )

    sc._player.set_spawn(pygame.Vector2(694, 496))
    for _ in range(10):
        sc.context.event_bus.dispatch()
        sc.update(1 / 60)

    assert sc._score.score == 50, (
        f"el mismo pickup volvió a sumar puntos tras un respawn "
        f"(score={sc._score.score})"
    )


def test_recoger_una_moneda_de_botin_no_suma_puntos_de_pickup(_puntuacion_aislada):
    """`_RecompensaDePickup` sólo tiene que premiar los 5 `Pickup` que trae
    el `.tmx` (buscando el `item_id` en `stage_data.recogibles`, el
    snapshot que arma `StageLoader` una vez por carga), no cualquier
    `INTERACT_ITEM_PICKED`: una moneda que suelta un enemigo al morir
    (`framework/scenes/stage_parts/economia.py:_soltar_botin`,
    `item_id="coin"`) se anexa sólo a `InteractableSystem.recogibles` (la
    copia viva que arranca de ese mismo snapshot y después crece), nunca a
    `stage_data.recogibles`. Sin ese filtro, cada moneda del juego normal
    también pagaría 100 puntos de pickup.
    """
    sc = _construir_escena_la_soda()
    sc._player.set_spawn(pygame.Vector2(sc._stage_data.spawn_point))
    for _ in range(3):
        sc.context.event_bus.dispatch()
        sc.update(1 / 60)
    assert sc._score.score == 0, "el montaje ya arrancó con puntos"

    from src.framework.stage.interactables import Recogible

    moneda = Recogible(
        rect=pygame.Rect(
            int(sc._player.rect.centerx - 8), int(sc._player.rect.centery - 8),
            16, 16,
        ),
        item_id="coin", automatico=True, cantidad=1,
    )
    sc._interactables.recogibles.append(moneda)

    for _ in range(10):
        sc.context.event_bus.dispatch()
        sc.update(1 / 60)

    assert sc._score.score == 0, (
        f"recoger una moneda de botín sumó puntos de pickup "
        f"(score={sc._score.score}) -- el filtro por stage_data.recogibles "
        f"no está funcionando"
    )


# ──────────────────────────────────────────────────────────────────────────
# AUD-637 — `ScoreSystem._tipo_de` (score_system.py:83-97) deduce el tipo de
# un enemigo buscando "walker"/"flying"/... como subcadena del nombre de su
# clase (el `entity_id` que arma `EnemyBase._die()`, `enemy_base.py:589`, es
# `f"{type(self).__name__}_{id(self)}"`). Las dos subclases propias de
# `EnemyWalker`/`EnemyFlying` que patrullan el camino exterior no llevaban
# ese prefijo -- se llamaban `Culebra`/`Zancudo`, sin "walker"/"flying" en
# ningún lado -- así que caían al valor por defecto (50 puntos / 1 moneda,
# el mismo que un tipo totalmente desconocido) en vez de cobrar como sus
# clones `WalkerRaton` (100/2) y `FlyingCucaracha` (150/2). Se renombran a
# `WalkerCulebra`/`FlyingZancudo`: sólo el identificador Python -- ni la
# clave de registro de `StageLoader` ("LaSodaCulebra"/"LaSodaZancudo"), ni
# los `type=` del `.tmx`, ni los nombres de objeto
# (`Culebra_01..03`/`Zancudo_01..03`), ni los sprites
# (`sprite_culebra_*`/`sprite_zancudo_*`) cambian -- el nombre "de juego"
# sigue siendo culebra/zancudo.
# ──────────────────────────────────────────────────────────────────────────


def test_los_5_enemigos_propios_cobran_por_su_familia_walker_o_flying():
    """Cada uno de los 5 tipos de enemigo propios de este nivel, buscado en
    la escena real, tiene que cobrar según la familia que anuncia su nombre
    de clase: `WalkerRaton` y la culebra (subclase de `EnemyWalker` que no
    es `WalkerRaton`) valen 100 puntos / 2 monedas; `FlyingCucaracha` y el
    zancudo (subclase de `EnemyFlying` que no es `FlyingCucaracha`) valen
    150/2; `ShooterCocinero` vale 200/3.

    La culebra y el zancudo se seleccionan por `isinstance` contra la base
    (`EnemyWalker`/`EnemyFlying`), nunca por su nombre de clase -- así esta
    prueba mide exactamente lo mismo antes y después del rename de AUD-637:
    antes falla (culebra/zancudo dan 50/1, el valor de un tipo
    desconocido), después pasa (100/2 y 150/2).
    """
    from src.engine.core import score_system as score_mod
    from src.framework.entities.enemy_flying import EnemyFlying
    from src.framework.entities.enemy_walker import EnemyWalker

    sc = _construir_escena_la_soda()
    entidades = sc._stage_data.entity_list

    walker_raton = next(
        (e for e in entidades if type(e).__name__ == "WalkerRaton"), None,
    )
    culebra = next(
        (
            e for e in entidades
            if isinstance(e, EnemyWalker) and type(e).__name__ != "WalkerRaton"
        ),
        None,
    )
    cucaracha = next(
        (e for e in entidades if type(e).__name__ == "FlyingCucaracha"), None,
    )
    zancudo = next(
        (
            e for e in entidades
            if isinstance(e, EnemyFlying) and type(e).__name__ != "FlyingCucaracha"
        ),
        None,
    )
    cocinero = next(
        (e for e in entidades if type(e).__name__ == "ShooterCocinero"), None,
    )

    casos = {
        "WalkerRaton": (walker_raton, "walker", 100, 2),
        "culebra (WalkerCulebra tras AUD-637)": (culebra, "walker", 100, 2),
        "FlyingCucaracha": (cucaracha, "flying", 150, 2),
        "zancudo (FlyingZancudo tras AUD-637)": (zancudo, "flying", 150, 2),
        "ShooterCocinero": (cocinero, "shooter", 200, 3),
    }
    faltantes = [etiqueta for etiqueta, (e, *_r) in casos.items() if e is None]
    assert not faltantes, f"el mapa no trae ninguna instancia de: {faltantes}"

    for etiqueta, (entidad, tipo_esperado, puntos, monedas) in casos.items():
        entity_id = f"{type(entidad).__name__}_1"
        assert score_mod._tipo_de(entity_id) == tipo_esperado, (
            f"{etiqueta} (clase real {type(entidad).__name__!r}) debería "
            f"clasificar como {tipo_esperado!r}, dio "
            f"{score_mod._tipo_de(entity_id)!r}"
        )
        # `_points_for` es privado -- no hay forma pública de leer los
        # PUNTOS sin matar al enemigo de verdad; se usa igual, con este
        # comentario como justificación (`coins_for` sí es pública, AUD-218,
        # y se usa tal cual). No se toca score_system.py.
        assert score_mod._points_for(entity_id) == puntos, (
            f"{etiqueta} (clase real {type(entidad).__name__!r}) debería "
            f"valer {puntos} puntos, dio {score_mod._points_for(entity_id)}"
        )
        assert score_mod.coins_for(entity_id) == monedas, (
            f"{etiqueta} (clase real {type(entidad).__name__!r}) debería "
            f"soltar {monedas} monedas, dio {score_mod.coins_for(entity_id)}"
        )


# ──────────────────────────────────────────────────────────────────────────
# AUD-638 — el mapa de La Soda no traía ningún objeto `Light` (0 en todo el
# .tmx): a diferencia de `stage0` (12 luces del profesor), el nivel caminaba
# completamente a oscuras en lo que al sistema de focos puntuales respecta
# -- la iluminación existente eran sólo las dos `AmbientLightZone` de
# AUD-614/615 (brillo de zona, no focos).
#
# Cada foco nuevo se ancla a un elemento que YA está dibujado en el mapa,
# verificado a mano contra los tilesets (`tileset_campus.png`,
# `tileset_soda_decor.png`) y contra las capas CSV del .tmx, no supuesto:
#   - el único farolito real del camino exterior es el gid 396 de
#     `tileset_campus` (fila 4, columna 7 de la hoja) -- aparece UNA sola
#     vez en todo el mapa, en la fachada junto a la primera pasarela alta
#     (x=704). Los gid 318/319 de `tileset_arboles` que a primera vista
#     parecían "postes de farol" repetidos son en realidad el tronco de un
#     conífero decorativo (confirmado recortando la hoja con PIL): no se
#     usan para ninguna luz.
#   - la guirnalda de luces de feria (gid 67, bombilla encendida, alternada
#     con el gid 68 sin encender) corre por el techo en y=128 desde x=2624
#     hasta x=3376, cruzando sala y cocina.
#   - la lámpara colgante (gid 72) y los dos apliques de pared redondos
#     (gid 79, uno por cuarto) y el letrero ovalado rosa tipo neón (gid 73)
#     son objetos únicos de `tileset_soda_decor`.
#   - no existe ningún sprite de estufa/cocina en `tileset_cafeteria` (sólo
#     texturas de piso/pared repetidas) ni en `tileset_soda_real` (texturas
#     de tierra/vegetación): el foco "fire" de la cocina se ancla al centro
#     de `HazardZone_250` (el mostrador caliente que ya amenaza al jugador)
#     como sustituto razonado, no a un sprite de estufa que no existe.
# ──────────────────────────────────────────────────────────────────────────


class TestLucesDelNivel:
    """AUD-638 -- diez `Light` nuevas: una en el camino exterior (el único
    farolito real del mapa), tres en la sala y seis en la cocina (una de
    ellas, la lámpara colgante del mostrador, cae justo en el límite entre
    los dos cuartos)."""

    def test_hay_al_menos_ocho_luces_declaradas(self, datos_del_nivel) -> None:
        assert len(datos_del_nivel.lights) >= 8, (
            "se esperaban al menos 8 luces (`Light`) declaradas en el "
            f".tmx; encontradas: {len(datos_del_nivel.lights)}"
        )

    def test_hay_una_luz_fire_con_flicker_dentro_de_la_cocina(
        self, datos_del_nivel,
    ) -> None:
        from src.framework.stage.stage_objetos import ObjetosDeTiled

        color_fuego = ObjetosDeTiled.LIGHT_COLORS["fire"]
        candidatas = [
            luz for luz in datos_del_nivel.lights
            if luz.position[0] > 2880 and luz.color == color_fuego and luz.flicker
        ]
        assert candidatas, (
            "no se encontró ninguna luz color 'fire' con flicker=True "
            "dentro de la cocina (x > 2880) -- se esperaba una sobre el "
            "mostrador (HazardZone_250), sustituto de la estufa"
        )

    def test_hay_al_menos_dos_luces_dentro_de_la_sala(self, datos_del_nivel) -> None:
        en_sala = [
            luz for luz in datos_del_nivel.lights
            if 2560 <= luz.position[0] < 2928
        ]
        assert len(en_sala) >= 2, (
            "se esperaban al menos 2 luces dentro de la sala "
            f"(2560<=x<2928); encontradas: {len(en_sala)}"
        )

    def test_todas_las_luces_caen_dentro_del_mapa_con_radio_positivo(
        self, datos_del_nivel,
    ) -> None:
        ancho, alto = datos_del_nivel.map_pixel_size
        fuera_de_mapa = []
        radios_invalidos = []
        for luz in datos_del_nivel.lights:
            x, y = luz.position
            if not (0 <= x <= ancho and 0 <= y <= alto):
                fuera_de_mapa.append((x, y))
            if luz.radius <= 0:
                radios_invalidos.append(luz.radius)

        assert not fuera_de_mapa, (
            f"luces con el punto de luz fuera de los límites del mapa "
            f"({ancho}x{alto}): {fuera_de_mapa}"
        )
        assert not radios_invalidos, (
            f"luces con radio no positivo: {radios_invalidos}"
        )


# ──────────────────────────────────────────────────────────────────────────
# AUD-639 — llave en la ruta alta + cofre cerrado en el
# depósito de la cocina. Puzle de llave y puerta con las piezas de F4.1 que
# ya trae el motor (`Key`/`Chest`, `stage_objetos.py:_handle_recogible` /
# `_handle_cofre`, `InteractableSystem._abrir_cofres`): la llave vive sobre
# `Bloque_Alto_02` (la segunda pasarela alta del camino exterior, junto a
# `Pickup_255`) y el cofre en el entrepiso de la cocina
# (`Plataforma_Entrepiso_01`, junto a `Pickup_258`).
#
# El cofre se abre con el botón de agarrar (`Action.GRAB`, el mismo camino
# real que usa el jugador: `stage_scene.py:1028-1031`,
# `usar=is_action_just_pressed(Action.GRAB)`) a `ALCANCE_DE_USO=24`px
# (`interactables.py:45,230-236`). El bot de referencia (`walk_right_bot`)
# sólo camina y salta —nunca pulsa GRAB— así que no abre el cofre por su
# cuenta aunque pase cerca; SÍ puede recoger la llave de paso, porque
# `automatico=true` la coge al tocarla, sin botón.
#
# Ojo con la recompensa: la llave es un `Recogible` más en
# `stage_data.recogibles` (el motor no distingue `Pickup` de `Key`), así que
# recogerla dispara `INTERACT_ITEM_PICKED` y TAMBIÉN premia
# `_RecompensaDePickup` (+50 puntos y su cartel, `stage1_2_la_soda.py:441-463`)
# igual que cualquier otro `Pickup` del mapa. El contenido del cofre, en
# cambio, se entrega por `_abrir_cofres` (`interactable_system.py:219-237`),
# que emite `INTERACT_CHEST_OPENED` — NO `INTERACT_ITEM_PICKED` —, así que
# abrir el cofre NO pasa por `_RecompensaDePickup` y no suma puntos.
# ──────────────────────────────────────────────────────────────────────────


class TestLlaveYCofreDelDeposito:
    """Futuro AUD-639 — `Key_273` sobre `Bloque_Alto_02` y `Chest_274` en el
    entrepiso de la cocina, unidas por `key_id="llave_deposito"`."""

    # -- datos: lo que declara el .tmx --------------------------------

    def test_hay_una_llave_del_deposito_sobre_bloque_alto_02(
        self, datos_del_nivel,
    ) -> None:
        llave = next(
            (r for r in datos_del_nivel.recogibles if r.item_id == "llave_deposito"),
            None,
        )
        assert llave is not None, (
            "no se encontró ningún Recogible con item_id='llave_deposito'"
        )
        assert 832 <= llave.rect.x < 960, (
            f"la llave del depósito debería caer sobre Bloque_Alto_02 "
            f"(832<=x<960); está en x={llave.rect.x}"
        )
        assert llave.rect.y < 528, (
            f"la llave del depósito debería estar sobre la superficie de "
            f"Bloque_Alto_02 (y<528, el tope del bloque); está en "
            f"y={llave.rect.y}"
        )

    def test_hay_un_cofre_del_deposito_en_la_cocina_con_el_souvenir(
        self, datos_del_nivel,
    ) -> None:
        cofre = next(
            (c for c in datos_del_nivel.cofres if c.key_id == "llave_deposito"),
            None,
        )
        assert cofre is not None, (
            "no se encontró ningún Cofre con key_id='llave_deposito'"
        )
        assert cofre.contenido == "souvenir_soda", (
            f"el cofre del depósito debería entregar 'souvenir_soda'; "
            f"entrega {cofre.contenido!r}"
        )
        assert cofre.rect.x > 3072, (
            f"el cofre del depósito debería estar dentro de la cocina "
            f"(x>3072); está en x={cofre.rect.x}"
        )

    # -- integración: la escena real, con el jugador de verdad ---------

    def test_abrir_el_cofre_sin_la_llave_lo_deja_cerrado_y_emite_bloqueo(
        self,
    ) -> None:
        """Negativa: parado sobre el cofre SIN la llave, pulsar el botón de
        agarrar no debe abrirlo, y el bus tiene que recibir
        `INTERACT_LOCK_BLOCKED` (`_abrir_cofres`, `interactable_system.py:
        219-226`)."""
        from src.engine.input.action_map import Action
        from src.framework.entities.player import Player
        from src.framework.stage.interactable_system import EVENTO_BLOQUEADA
        from tests.playtest.bot import _StubInput

        sc = _construir_escena_la_soda()
        # El cofre vive en la cocina (x>3072, interior): se desarma la
        # transición de la puerta para poder colocar al jugador ahí
        # directamente, mismo patrón que usan las pruebas de FrictionZone y
        # `render_real.py`.
        sc._room_transition.disarm_to_interior()

        cofre = next(
            c for c in sc._stage_data.cofres if c.key_id == "llave_deposito"
        )
        assert not sc._interactables.llavero.tiene("llave_deposito"), (
            "el montaje no debería arrancar con la llave ya en el llavero"
        )

        # El bus guarda una referencia DÉBIL al callback (docstring de
        # `EventBus.subscribe`): una lambda desechable moriría antes del
        # `dispatch()`. `_escuchar` se mantiene viva por ser una variable
        # local de esta función durante toda la prueba.
        bloqueos: list[dict] = []

        def _escuchar(**datos: object) -> None:
            bloqueos.append(datos)

        sc.context.event_bus.subscribe(EVENTO_BLOQUEADA, _escuchar)

        stub = _StubInput()
        sc.context.input_manager = stub
        px = cofre.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = cofre.rect.bottom - Player.ALTO_DE_PIE
        sc._player.set_spawn(pygame.Vector2(px, py))
        for _ in range(6):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        stub.set_actions({Action.GRAB})
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert cofre.abierto is False, (
            "el cofre se abrió sin tener la llave 'llave_deposito'"
        )
        assert bloqueos, (
            "el bus nunca recibió INTERACT_LOCK_BLOCKED al intentar abrir "
            "el cofre sin la llave"
        )
        assert any(
            b.get("key_id") == "llave_deposito" for b in bloqueos
        ), (
            f"INTERACT_LOCK_BLOCKED se emitió sin el key_id esperado: "
            f"{bloqueos}"
        )

    def test_recoger_la_llave_y_abrir_el_cofre_entrega_el_souvenir(
        self,
    ) -> None:
        """Positiva: llevar al jugador a la llave (se recoge sola al
        colisionar, `automatico=true`), después al cofre y abrirlo con el
        botón de agarrar tiene que dejar el cofre abierto y el souvenir en
        el llavero."""
        from src.engine.input.action_map import Action
        from src.framework.entities.player import Player
        from tests.playtest.bot import _StubInput

        sc = _construir_escena_la_soda()

        llave = next(
            r for r in sc._stage_data.recogibles if r.item_id == "llave_deposito"
        )
        cofre = next(
            c for c in sc._stage_data.cofres if c.key_id == "llave_deposito"
        )

        # Paso 1 — ir a la llave. Está en el camino exterior (x=832..960,
        # muy por debajo de TRIGGER_X=2416): no hace falta tocar
        # `_room_transition` todavía.
        px = llave.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = llave.rect.bottom - Player.ALTO_DE_PIE
        sc._player.set_spawn(pygame.Vector2(px, py))
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert sc._interactables.llavero.tiene("llave_deposito"), (
            "el montaje no llegó a recoger la llave del depósito"
        )

        # Paso 2 — ir al cofre, ya en la cocina (interior). Se desarma la
        # transición de la puerta DESPUÉS de pasar por la llave: si se
        # desarmara antes, `clamp_one_way` (activo apenas `room=="interior"`)
        # empujaría al jugador de vuelta hacia ROOM_LIMIT_X mientras todavía
        # está sobre la pasarela exterior.
        sc._room_transition.disarm_to_interior()

        stub = _StubInput()
        sc.context.input_manager = stub
        px = cofre.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = cofre.rect.bottom - Player.ALTO_DE_PIE
        sc._player.set_spawn(pygame.Vector2(px, py))
        for _ in range(6):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        stub.set_actions({Action.GRAB})
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert cofre.abierto is True, (
            "el cofre no se abrió aun teniendo la llave 'llave_deposito'"
        )
        assert sc._interactables.llavero.tiene("souvenir_soda"), (
            "el cofre se abrió pero 'souvenir_soda' no llegó al llavero"
        )


class TestLaLlaveSobreviveAUnRespawn:
    """AUD-643, punto 2 — "la llave se pierde al morir" (reporte del
    dueño: la recogió, murió en la cocina, y el cofre le repitió "Necesitas
    llave_deposito" diez veces).

    Causa (`_LlavesPersistentes`, ver su docstring en `stage1_2_la_soda.py`
    para el detalle completo): `StageScene.respawn()` -> `on_enter()`
    reconstruye `_stage_data` (recogibles con `recogido=False` de nuevo) e
    `_interactables` (un `Llavero` NUEVO, vacío) enteros. Se verifica por
    el camino real: `sc.respawn()`, no un atajo de prueba."""

    def test_llavero_y_recogible_sobreviven_a_respawn_y_el_cofre_se_abre(
        self,
    ) -> None:
        from src.engine.input.action_map import Action
        from src.framework.entities.player import Player
        from tests.playtest.bot import _StubInput

        sc = _construir_escena_la_soda()
        llave = next(
            r for r in sc._stage_data.recogibles if r.item_id == "llave_deposito"
        )

        # Paso 1 — recoger la llave, en el camino exterior.
        px = llave.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = llave.rect.bottom - Player.ALTO_DE_PIE
        sc._player.set_spawn(pygame.Vector2(px, py))
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        assert sc._interactables.llavero.tiene("llave_deposito"), (
            "el montaje no llegó a recoger la llave del depósito"
        )

        # Paso 2 — morir/respawnear por el camino real. Un fotograma en
        # sitio seguro antes, mismo patrón que
        # `test_el_cartel_de_bienvenida_no_se_repite_tras_un_respawn`.
        sc._player.set_spawn(pygame.Vector2(sc._stage_data.spawn_point))
        sc.update(1 / 60)
        sc.respawn()

        llave_tras_respawn = next(
            r for r in sc._stage_data.recogibles if r.item_id == "llave_deposito"
        )
        assert llave_tras_respawn is not llave, (
            "si esto empieza a fallar, StageScene ya no reconstruye "
            "_stage_data.recogibles en cada respawn y el resto de esta "
            "prueba no aplica"
        )
        assert sc._interactables.llavero.tiene("llave_deposito"), (
            "la llave desapareció del Llavero nuevo tras el respawn"
        )
        assert llave_tras_respawn.recogido is True, (
            "el Recogible de la llave, reconstruido por el respawn, "
            "debería nacer marcado como ya recogido (para no volver a "
            "dibujarse ni poder recogerse otra vez)"
        )
        llaves_sin_recoger = [
            r for r in sc._stage_data.recogibles
            if r.item_id.startswith("llave_") and not r.recogido
        ]
        assert llaves_sin_recoger == [], (
            f"quedan llaves sin recoger tras el respawn: {llaves_sin_recoger}"
        )

        # Paso 3 — el cofre se abre con GRAB sin volver a caminar hasta
        # donde estaba la llave (ya la tiene, tras el respawn).
        sc._room_transition.disarm_to_interior()
        cofre = next(
            c for c in sc._stage_data.cofres if c.key_id == "llave_deposito"
        )
        stub = _StubInput()
        sc.context.input_manager = stub
        px = cofre.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = cofre.rect.bottom - Player.ALTO_DE_PIE
        sc._player.set_spawn(pygame.Vector2(px, py))
        for _ in range(6):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        stub.set_actions({Action.GRAB})
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert cofre.abierto is True, (
            "el cofre siguió cerrado tras el respawn aunque la llave ya "
            "estaba en el llavero"
        )

    def test_una_llave_no_recogida_no_se_reaplica(self) -> None:
        """Negativa de `_LlavesPersistentes`: si el jugador NUNCA recogió
        la llave, un respawn no debe inventarle una."""
        sc = _construir_escena_la_soda()
        sc._player.set_spawn(pygame.Vector2(sc._stage_data.spawn_point))
        sc.update(1 / 60)
        sc.respawn()

        assert not sc._interactables.llavero.tiene("llave_deposito")
        llave = next(
            r for r in sc._stage_data.recogibles if r.item_id == "llave_deposito"
        )
        assert llave.recogido is False


# ──────────────────────────────────────────────────────────────────────────
# AUD-639 — íconos propios para Key/Chest.
#
# `DrawingSystem._draw_interactables` (drawing_system.py:330-395) no conoce
# el concepto "esto es una llave": todo `Recogible` sin entrada en el
# catálogo de `Inventory` se pinta con el mismo `_COLOR_RECOGIBLE`
# (240,210,90), el mismo cuadrado que un vaso de soda o una moneda -- la
# llave del depósito (item_id="llave_deposito") es indistinguible de
# `Pickup_255` a simple vista. El cofre es un rectángulo marrón con una
# línea de tapa que sólo cambia a gris al abrirse.
#
# `Stage1_2_LaSoda._dibujar_iconos_interactivos` repinta encima con un
# glifo propio, mismo mecanismo que `_draw_enemy_health_bars`: lee
# `self._interactables` (recogibles/cofres) y convierte a espacio de
# pantalla con `self._camera.offset`.
# ──────────────────────────────────────────────────────────────────────────


class TestIconosDeLlaveYCofre:
    """AUD-639 -- `_dibujar_llave`/`_dibujar_cofre` propios de la
    stage, en vez de los placeholders indistinguibles del framework."""

    def test_dibujar_llave_pinta_dorado_dentro_del_rect_y_no_toca_el_exterior(
        self,
    ) -> None:
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import Stage1_2_LaSoda

        sc = _construir_escena_la_soda()
        centinela = (12, 34, 56)
        superficie = pygame.Surface((40, 40))
        superficie.fill(centinela)

        rect = pygame.Rect(10, 10, 16, 16)
        sc._dibujar_llave(superficie, rect)

        # Cabeza: 3px por encima del centro (radio 4, sin tocar el "ojo"
        # perforado en el centro exacto) -- tiene que quedar dorado macizo.
        assert tuple(superficie.get_at((rect.x + 4, rect.y + 5)))[:3] == (
            Stage1_2_LaSoda._COLOR_LLAVE_DORADO
        ), "la cabeza de la llave no salió dorada"

        # Vástago: fila central del rectángulo (7,7,8,3), lejos de su borde
        # de 1px -- interior dorado.
        assert tuple(superficie.get_at((rect.x + 9, rect.y + 8)))[:3] == (
            Stage1_2_LaSoda._COLOR_LLAVE_DORADO
        ), "el vástago de la llave no salió dorado"

        # El exterior del rect (la esquina de la superficie, lejos de
        # cualquier trazo del glifo) no se tiene que haber tocado.
        assert tuple(superficie.get_at((0, 0)))[:3] == centinela, (
            "_dibujar_llave pintó fuera de su propio rect"
        )

    def test_dibujar_cofre_cerrado_y_abierto_producen_imagenes_distintas(
        self,
    ) -> None:
        sc = _construir_escena_la_soda()
        rect = pygame.Rect(10, 10, 16, 16)
        fondo = (12, 34, 56)

        cerrado = pygame.Surface((40, 40))
        cerrado.fill(fondo)
        sc._dibujar_cofre(cerrado, rect, abierto=False)

        abierto = pygame.Surface((40, 40))
        abierto.fill(fondo)
        sc._dibujar_cofre(abierto, rect, abierto=True)

        assert pygame.image.tobytes(cerrado, "RGB") != pygame.image.tobytes(
            abierto, "RGB",
        ), "el cofre cerrado y el abierto se dibujaron exactamente igual"

        # Punto concreto de la tapa/interior: fila 11 del cuerpo (9..14),
        # lejos de los dos listones (filas 10 y 13) -- cerrado es el color
        # macizo del cuerpo, abierto es el interior aclarado que deja ver
        # la tapa levantada.
        punto = (rect.x + 8, rect.y + 11)
        color_cerrado = tuple(cerrado.get_at(punto))[:3]
        color_abierto = tuple(abierto.get_at(punto))[:3]
        assert color_cerrado != color_abierto, (
            f"el punto {punto} del cuerpo del cofre no cambió entre cerrado "
            f"({color_cerrado}) y abierto ({color_abierto})"
        )

    def test_la_llave_del_deposito_ya_no_se_ve_igual_que_un_pickup_en_pantalla(
        self,
    ) -> None:
        """Integración con la escena real: jugador cerca de la llave del
        depósito (x=936) sin pisarla -- no hace falta correr física, sólo
        posicionar como hace `test_el_marco_de_la_puerta_se_dibuja_encima_
        del_jugador_en_el_umbral` más arriba -- y comparar, en la MISMA
        posición relativa dentro de cada ícono de 16x16, el píxel de la
        llave contra el de `Pickup_255` (item_id="vaso_soda", x=888, un
        `Recogible` cualquiera que sigue dibujándose con el placeholder de
        siempre porque no empieza con "llave_")."""
        from src.engine.core import settings
        from src.framework.entities.player import Player
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import Stage1_2_LaSoda

        sc = _construir_escena_la_soda()
        llave = next(
            r for r in sc._stage_data.recogibles if r.item_id == "llave_deposito"
        )
        pickup = next(
            r for r in sc._stage_data.recogibles if r.item_id == "vaso_soda"
        )
        assert not llave.recogido and not pickup.recogido

        # Jugador cerca de la llave, SIN pisarla (40px a la izquierda del
        # rect, fuera de su colisión) -- sólo se fija posición/rect, sin
        # física, mismo patrón que el test del marco de la puerta.
        sc._player.position.x = llave.rect.x - 40.0
        sc._player.position.y = llave.rect.y
        sc._player.rect.x = int(sc._player.position.x)
        sc._player.rect.y = int(sc._player.position.y)
        assert not sc._player.rect.colliderect(llave.rect), (
            "el montaje pisó la llave -- no debe recogerse en esta prueba"
        )

        # Cámara fija a mano para que los dos íconos (llave x=936, pickup
        # x=888) caigan en un punto conocido de la pantalla.
        ancho, alto = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        sc._camera.offset.x = 900.0 - ancho / 2.0
        sc._camera.offset.y = float(llave.rect.y) - alto / 2.0 + 8.0

        # AUD-643 — el overlay de tutorial arranca activo en on_enter()
        # (duration=6.0, `TutorialOverlay.draw` rellena la pantalla ENTERA
        # con negro a alfa 200, `tutorial_overlay.py:99-100`) y, desde que
        # `_dibujar_iconos_interactivos` se mudó de `draw()` a
        # `dibujar_mundo()` (ver el docstring de `Stage1_2_LaSoda.
        # dibujar_mundo`), ese oscurecido de pantalla completa ahora se
        # aplica DESPUÉS de que el glifo se dibuja (`dibujar_ui` corre tras
        # `dibujar_mundo`), y lo apaga (40,30,10) -> (11,8,2), rompiendo la
        # comparación de color de esta prueba. Antes "colaba" sin querer:
        # los glifos se pintaban al final de un `draw()` monolítico, después
        # del propio tutorial. Se apaga a mano, mismo patrón que ya usa
        # `render_real.py` para las mismas capturas.
        if hasattr(sc, "_tutorial"):
            sc._tutorial._active = False

        superficie = pygame.Surface((ancho, alto))
        sc.draw(superficie)

        llave_x_pantalla = int(llave.rect.x - sc._camera.offset.x)
        llave_y_pantalla = int(llave.rect.y - sc._camera.offset.y)
        pickup_x_pantalla = int(pickup.rect.x - sc._camera.offset.x)
        pickup_y_pantalla = int(pickup.rect.y - sc._camera.offset.y)

        # El "ojo" perforado en el centro de la cabeza del glifo: un píxel
        # con el color de contorno oscuro, en la misma posición relativa
        # (+4,+8) dentro de cada ícono de 16x16.
        color_en_llave = tuple(
            superficie.get_at((llave_x_pantalla + 4, llave_y_pantalla + 8)),
        )[:3]
        color_en_pickup = tuple(
            superficie.get_at((pickup_x_pantalla + 4, pickup_y_pantalla + 8)),
        )[:3]

        assert color_en_llave == Stage1_2_LaSoda._COLOR_LLAVE_CONTORNO, (
            f"la llave no muestra el contorno oscuro del glifo propio en "
            f"({llave_x_pantalla + 4},{llave_y_pantalla + 8}); salió "
            f"{color_en_llave}"
        )
        assert color_en_pickup != Stage1_2_LaSoda._COLOR_LLAVE_CONTORNO, (
            "Pickup_255 (un Recogible cualquiera, no una llave) salió con "
            "el mismo color de contorno que el glifo de la llave -- ya no "
            "se distinguirían en pantalla"
        )


# ──────────────────────────────────────────────────────────────────────────
# AUD-640 — tres carteles `MessageTrigger_Once` que guían al jugador donde
# el mapa no dice nada por sí solo: que la ruta alta (sobre `Bloque_Alto_01`,
# camino exterior) es opcional y más adelante guarda una llave, que la
# fachada de La Soda se cruza caminando por la puerta, y que el depósito
# con el cofre de AUD-639 está en el entrepiso de la cocina. Mismo formato
# que MSG_01 (`text` + `duration` float, 32x32 a ras de piso en y=576) y
# mismo camino real de disparo -- `HazardSystem.update()`
# (`hazard_system.py:96-111`), consumido por `MessageBox._on_show_message`
# (`engine/ui/message_box.py:72,82-88`) -- así que no hace falta ningún
# código nuevo en esta stage para que se disparen o se muestren.
#
# `_carteles_disparados` (antes `_welcome_message_shown`, un solo `bool`)
# se generalizó para esto -- ver su comentario en `Stage1_2_LaSoda.__init__`
# y en `_maybe_persist_carteles_disparados`: con un único MessageTrigger_Once
# en el mapa un booleano "¿se disparó ALGUNO?" alcanzaba, pero con cuatro
# marcaba a los cuatro como "ya mostrados" apenas UNO se disparaba, y un
# jugador que muriera después de ver sólo el cartel de bienvenida perdía
# los otros tres para siempre sin haberlos visto. `test_el_estado_de_cada_
# cartel_persiste_su_propio_indice_tras_un_respawn` de más abajo es la
# prueba roja→verde de ese arreglo.
# ──────────────────────────────────────────────────────────────────────────


class TestCartelesDeGuia:
    """AUD-640 -- MSG_02_RutaAlta, MSG_03_Fachada y MSG_04_Cocina, los tres
    `MessageTrigger_Once` nuevos que guían al jugador por La Soda."""

    # -- datos: lo que declara el .tmx --------------------------------

    def test_hay_al_menos_cuatro_carteles_con_texto(self, datos_del_nivel) -> None:
        carteles = datos_del_nivel.message_triggers
        assert len(carteles) >= 4, (
            f"esperaba MSG_01 (bienvenida) más los tres carteles de guía "
            f"de AUD-640 (>=4 en total); hay {len(carteles)}"
        )
        for cartel in carteles:
            assert cartel.text.strip(), (
                f"un MessageTrigger sin texto no sirve de guía: {cartel!r}"
            )

    def test_hay_un_cartel_en_la_ruta_alta(self, datos_del_nivel) -> None:
        assert any(
            560 <= mt.rect.x < 640 for mt in datos_del_nivel.message_triggers
        ), (
            "no hay ningún cartel con 560<=x<640 (la ruta alta, sobre "
            "Bloque_Alto_01 -- MSG_02_RutaAlta)"
        )

    def test_hay_un_cartel_en_la_fachada_antes_del_vano(
        self, datos_del_nivel,
    ) -> None:
        assert any(
            2200 <= mt.rect.x < 2384 for mt in datos_del_nivel.message_triggers
        ), (
            "no hay ningún cartel con 2200<=x<2384 (la fachada, ANTES del "
            "vano de la puerta en x=2384-2432 -- MSG_03_Fachada)"
        )

    def test_hay_un_cartel_en_la_entrada_de_la_cocina(
        self, datos_del_nivel,
    ) -> None:
        assert any(
            3008 <= mt.rect.x < 3072 for mt in datos_del_nivel.message_triggers
        ), (
            "no hay ningún cartel con 3008<=x<3072 (la entrada de la "
            "cocina -- MSG_04_Cocina)"
        )

    # -- integración: la escena real, con el jugador de verdad ---------

    def test_pisar_el_cartel_de_la_ruta_alta_muestra_su_texto(self) -> None:
        """Caminar hasta MSG_02_RutaAlta tiene que dejar el `MessageBox` de
        la escena visible con su texto -- mismo camino real que ya prueba
        `test_recoger_un_pickup_suma_puntos_y_muestra_su_mensaje` para el
        mensaje de un Pickup: `event_bus.dispatch()` antes de `update()`,
        varias vueltas por la reentrancia de `SHOW_MESSAGE`
        (`event_bus.py:174-183`)."""
        from src.framework.entities.player import Player

        sc = _construir_escena_la_soda()
        cartel = next(
            mt for mt in sc._stage_data.message_triggers
            if 560 <= mt.rect.x < 640
        )
        px = cartel.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = 592.0 - Player.ALTO_DE_PIE  # tope del piso principal (y=592)
        sc._player.set_spawn(pygame.Vector2(px, py))

        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert sc._msg_box._visible is True, (
            "no se mostró ningún cartel al pisar la zona de la ruta alta"
        )
        assert sc._msg_box._full_text == cartel.text, (
            f"el texto mostrado no coincide con el de MSG_02_RutaAlta "
            f"(texto={sc._msg_box._full_text!r})"
        )

    def test_el_cartel_de_la_ruta_alta_no_se_repite_al_volver_a_pisarlo(
        self,
    ) -> None:
        """Es un `_Once`: `mt.triggered` pasa a `True` la primera vez que
        el jugador lo pisa (`hazard_system.py:96-98`) y de ahí en más
        `HazardSystem.update()` lo salta -- mismo contrato que ya prueba
        `test_el_cartel_de_bienvenida_no_se_repite_tras_un_respawn` para
        MSG_01, aquí sin necesidad de un respawn: basta con alejarse y
        volver a pisar el mismo disparador."""
        from src.engine.core.events import Events
        from src.framework.entities.player import Player

        sc = _construir_escena_la_soda()
        cartel = next(
            mt for mt in sc._stage_data.message_triggers
            if 560 <= mt.rect.x < 640
        )
        px = cartel.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = 592.0 - Player.ALTO_DE_PIE
        sc._player.set_spawn(pygame.Vector2(px, py))
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        assert cartel.triggered is True, (
            "el montaje no llegó a disparar el cartel de la ruta alta"
        )

        # Se aleja y vuelve a pisar el mismo disparador.
        sc._player.set_spawn(pygame.Vector2(px - 200.0, py))
        for _ in range(4):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        sc._player.set_spawn(pygame.Vector2(px, py))
        marca = len(sc.context.event_bus._queue)
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        nuevos = sc.context.event_bus._queue[marca:]
        assert not any(nombre == Events.SHOW_MESSAGE for nombre, _ in nuevos), (
            "el cartel de la ruta alta volvió a encolar SHOW_MESSAGE tras "
            "haberse mostrado una vez -- rompe el contrato de "
            "MessageTrigger_Once"
        )

    def test_el_estado_de_cada_cartel_persiste_su_propio_indice_tras_un_respawn(
        self,
    ) -> None:
        """Regresión del arreglo de `_carteles_disparados` (ver el
        comentario de más arriba y el de `Stage1_2_LaSoda.__init__`):
        dispara SÓLO el cartel de la ruta alta, fuerza un respawn, y
        comprueba que los otros tres -- incluida la propia bienvenida,
        nunca pisada en esta prueba -- siguen sin marcarse como ya
        mostrados. Antes de este cambio, `_welcome_message_shown` (un
        único `bool`) los marcaba a los cuatro."""
        from src.framework.entities.player import Player

        sc = _construir_escena_la_soda()
        ruta_alta = next(
            mt for mt in sc._stage_data.message_triggers
            if 560 <= mt.rect.x < 640
        )
        px = ruta_alta.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = 592.0 - Player.ALTO_DE_PIE
        sc._player.set_spawn(pygame.Vector2(px, py))
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert ruta_alta.triggered is True, (
            "el montaje no llegó a disparar el cartel de la ruta alta"
        )
        otros_antes = [
            mt for mt in sc._stage_data.message_triggers if mt is not ruta_alta
        ]
        assert all(not mt.triggered for mt in otros_antes), (
            "el montaje disparó de más antes de llegar al respawn -- "
            "revisar las posiciones de los carteles"
        )

        # Un fotograma en un sitio seguro para que _maybe_persist_carteles_
        # disparados registre el índice antes del respawn (mismo patrón que
        # test_el_cartel_de_bienvenida_no_se_repite_tras_un_respawn).
        sc._player.set_spawn(pygame.Vector2(sc._stage_data.spawn_point))
        sc.update(1 / 60)
        sc.respawn()

        triggers_tras_respawn = sc._stage_data.message_triggers
        ruta_alta_tras_respawn = next(
            mt for mt in triggers_tras_respawn if 560 <= mt.rect.x < 640
        )
        assert ruta_alta_tras_respawn.triggered is True, (
            "el cartel de la ruta alta perdió su estado 'ya mostrado' tras "
            "el respawn"
        )
        otros_tras_respawn = [
            mt for mt in triggers_tras_respawn
            if mt is not ruta_alta_tras_respawn
        ]
        assert all(not mt.triggered for mt in otros_tras_respawn), (
            "un respawn después de ver UN SOLO cartel marcó a los demás "
            "carteles (incluida la bienvenida, nunca pisada) como ya "
            "mostrados -- _carteles_disparados dejó de ser por índice"
        )


class TestColaDeMensajes:
    """AUD-643, punto 3 — "los carteles llegan tarde". Ver el reporte
    final para la medición completa (`Claude - Uso General/playtest/
    medicion_cola_mensajes.py`) y el hallazgo de que `hazard_system.py`
    (motor, fuera de alcance) ignora `duration` de `MessageTrigger_Once` y
    siempre muestra 8s -- estas pruebas cubren lo que SÍ está en código
    propio de esta stage: el cartel de pickup más corto y el rate-limit +
    nombres legibles de `_AvisoDeBloqueo`."""

    def test_la_duracion_del_cartel_de_pickup_bajo_a_1_5s(self) -> None:
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _RecompensaDePickup

        assert _RecompensaDePickup.DURACION_MENSAJE == 1.5

    def test_el_aviso_de_bloqueo_no_reencola_el_mismo_texto_dentro_de_la_ventana(
        self,
    ) -> None:
        """Simula lo que el dueño hizo de verdad: pulsar GRAB varias veces
        seguidas junto al cofre cerrado. Sin el rate-limit, cada pulsación
        encolaba OTRO `SHOW_MESSAGE` idéntico detrás del anterior."""
        from src.engine.core.events import Events
        from src.engine.input.action_map import Action
        from src.framework.entities.player import Player
        from tests.playtest.bot import _StubInput

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        cofre = next(
            c for c in sc._stage_data.cofres if c.key_id == "llave_deposito"
        )

        avisos: list[dict] = []

        def _escuchar(**datos: object) -> None:
            avisos.append(datos)

        sc.context.event_bus.subscribe(Events.SHOW_MESSAGE, _escuchar)

        stub = _StubInput()
        sc.context.input_manager = stub
        px = cofre.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = cofre.rect.bottom - Player.ALTO_DE_PIE
        sc._player.set_spawn(pygame.Vector2(px, py))
        for _ in range(6):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        # GRAB, soltar, GRAB otra vez -- varias veces seguidas, bien dentro
        # de VENTANA_REPETICION=2.0s (unos 0.5s en total).
        for _ in range(5):
            stub.set_actions({Action.GRAB})
            for _ in range(3):
                sc.context.event_bus.dispatch()
                sc.update(1 / 60)
            stub.set_actions(set())
            for _ in range(3):
                sc.context.event_bus.dispatch()
                sc.update(1 / 60)

        avisos_de_bloqueo = [
            a for a in avisos if "cerrado" in str(a.get("text", ""))
        ]
        assert len(avisos_de_bloqueo) == 1, (
            f"se reencoló el mismo aviso de bloqueo más de una vez dentro "
            f"de la ventana de repetición: {avisos_de_bloqueo}"
        )

    def test_el_aviso_de_bloqueo_reemplaza_el_key_id_crudo_por_un_nombre_legible(
        self,
    ) -> None:
        """`_on_bloqueada` se llama directo -- el disparo real (GRAB junto
        al cofre sin la llave) ya está cubierto por
        `TestLlaveYCofreDelDeposito.test_abrir_el_cofre_sin_la_llave_lo_
        deja_cerrado_y_emite_bloqueo`; esta prueba sólo aísla la
        sustitución de texto."""
        from src.engine.core.events import Events

        sc = _construir_escena_la_soda()
        sc._interactables.mensaje = "El cofre está cerrado. Necesitas «llave_deposito»."

        # Función local, no una lambda desechable: el bus guarda una
        # referencia DÉBIL (docstring de `EventBus.subscribe`) y una
        # lambda pasada directo muere antes del `dispatch()`.
        capturado: dict = {}

        def _escuchar(**datos: object) -> None:
            capturado.update(datos)

        sc.context.event_bus.subscribe(Events.SHOW_MESSAGE, _escuchar)

        sc._aviso_bloqueo._on_bloqueada()
        sc.context.event_bus.dispatch()

        assert "llave_deposito" not in str(capturado.get("text", "")), (
            f"el key_id crudo sigue apareciendo tal cual: {capturado!r}"
        )
        assert "la llave del depósito" in str(capturado.get("text", "")), (
            f"no se ve el nombre legible esperado: {capturado!r}"
        )

    def test_la_ventana_de_repeticion_deja_pasar_un_texto_distinto_de_inmediato(
        self,
    ) -> None:
        """El límite es "no te repitas a vos mismo", no "cállate un
        rato": un aviso con texto DISTINTO no debería esperar la ventana."""
        from src.engine.core.events import Events

        sc = _construir_escena_la_soda()
        avisos: list[str] = []

        def _escuchar(**datos: object) -> None:
            avisos.append(str(datos.get("text", "")))

        sc.context.event_bus.subscribe(Events.SHOW_MESSAGE, _escuchar)

        sc._interactables.mensaje = "Primer aviso."
        sc._aviso_bloqueo._on_bloqueada()
        sc._interactables.mensaje = "Segundo aviso, distinto."
        sc._aviso_bloqueo._on_bloqueada()
        sc.context.event_bus.dispatch()

        assert avisos == ["Primer aviso.", "Segundo aviso, distinto."], (
            f"un texto distinto no debería quedar retenido por la ventana "
            f"de repetición del anterior: {avisos}"
        )


# ──────────────────────────────────────────────────────────────────────────
# AUD-641 — la salida de La Soda exige vencer al cocinero (decisión del
# dueño, 26/8). `Door_Trasera` (`abre_con_evento="cocinero_muerto"`,
# `key_id="cocinero_vencido"` imposible de conseguir -- ver el docstring de
# `_PuertaDelCocinero` en `stage1_2_la_soda.py`) bloquea el corredor entre la
# `FrictionZone` del piso trapeado (x=3240) y el `NextTrigger` (x=3392) hasta
# que `_PuertaDelCocinero` recibe `Events.ENEMY_DIED` de un `ShooterCocinero`
# y llama a `InteractableSystem.abrir_por_evento("cocinero_muerto")`.
# ──────────────────────────────────────────────────────────────────────────


def _matar_al_cocinero(sc):
    """Encuentra al `ShooterCocinero` de la escena y lo mata con la API real
    de daño (`EnemyBase.apply_hit`), como el resto de este archivo hace con
    `_con_proyectil_sobre_el_jugador` más arriba -- nunca se fuerza
    `is_alive = False` ni se llama a `_die()` directamente.

    Un solo golpe con `damage=10.0` (mayor que `max_health=3.0`) basta para
    matarlo de una vez -- `apply_hit` sólo arma la invencibilidad temporal
    (`_invincibility_timer`) cuando el golpe NO mata (`enemy_base.py:
    552-556`), así que encadenar varios golpes más chicos exigiría
    esquivarla; con uno solo no hace falta.

    Un `dispatch()` + un `update()` bastan para que el bus procese
    `Events.ENEMY_DIED` y `_PuertaDelCocinero._on_enemy_died` corra.
    """
    cocinero = next(
        e for e in sc._stage_data.entity_list if isinstance(e, ShooterCocinero)
    )
    cocinero.apply_hit(10.0, (0.0, 0.0))
    sc.context.event_bus.dispatch()
    sc.update(1 / 60)
    return cocinero


class TestPuertaDelCocinero:
    """AUD-641 -- `Door_Trasera`, `_PuertaDelCocinero`, `_ObjetivoCocinero`
    y `_PuertaTraseraVisual` (todas en `stage1_2_la_soda.py`)."""

    # -- datos: lo que declara el .tmx --------------------------------

    def test_hay_una_cerradura_puerta_trasera_entre_el_trapeado_y_la_salida(
        self, datos_del_nivel,
    ) -> None:
        cerradura = next(
            (c for c in datos_del_nivel.cerraduras
             if c.abre_con_evento == "cocinero_muerto"),
            None,
        )
        assert cerradura is not None, (
            "no se encontró ninguna Cerradura con "
            "abre_con_evento='cocinero_muerto'"
        )
        assert cerradura.clase == "puerta"
        assert 3240 <= cerradura.rect.x < 3392, (
            "Door_Trasera debería quedar entre la FrictionZone del "
            f"trapeado (x=3240) y el NextTrigger (x=3392); "
            f"x={cerradura.rect.x}"
        )

    # -- la puerta cerrada bloquea de verdad ---------------------------

    def test_la_puerta_cerrada_bloquea_correr_y_saltar_contra_ella(self) -> None:
        """Jugador corriendo y saltando hacia la derecha desde x≈3300
        durante 3s no supera `cerradura.rect.x` (3360), y no llega al
        `NextTrigger` -- prueba el requisito duro de la Tarea 1 (96px de
        alto, mucho más que cualquier salto, no se puede saltar por
        encima)."""
        from src.engine.input.action_map import Action
        from tests.playtest.bot import _StubInput

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        cerradura = next(
            c for c in sc._stage_data.cerraduras
            if c.abre_con_evento == "cocinero_muerto"
        )
        stub = _StubInput()
        sc.context.input_manager = stub
        sc._player.set_spawn(pygame.Vector2(cerradura.rect.x - 60.0, 560.0))
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        stub.set_actions({Action.MOVE_RIGHT, Action.JUMP})
        for _ in range(int(3 * 60)):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert sc._player.position.x < cerradura.rect.x, (
            f"el jugador atravesó la puerta cerrada: "
            f"x={sc._player.position.x:.1f} contra "
            f"cerradura.rect.x={cerradura.rect.x}"
        )
        assert not sc._player.rect.colliderect(sc._stage_data.next_trigger), (
            "el jugador llegó al NextTrigger sin haber vencido al cocinero"
        )
        assert cerradura.abierta is False

    def test_grab_junto_a_la_puerta_sin_vencer_al_cocinero_no_la_abre_y_avisa(
        self,
    ) -> None:
        """Negativa, mismo patrón que
        `TestLlaveYCofreDelDeposito.test_abrir_el_cofre_sin_la_llave_lo_deja_
        cerrado_y_emite_bloqueo`: parado junto a la puerta SIN haber vencido
        al cocinero, pulsar GRAB no debe abrirla, y el bus tiene que recibir
        `INTERACT_LOCK_BLOCKED` -- el "cartel de bloqueo" que pide la Tarea 1
        (`_abrir_cerraduras`, `interactable_system.py:199-217`, usa
        `cerradura.mensaje_bloqueado`, la propiedad `mensaje` del .tmx, NO
        `mensaje_bloqueado` como nombre de propiedad -- ver CLAUDE.md de
        este AUD)."""
        from src.engine.input.action_map import Action
        from src.framework.entities.player import Player
        from src.framework.stage.interactable_system import EVENTO_BLOQUEADA
        from tests.playtest.bot import _StubInput

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        cerradura = next(
            c for c in sc._stage_data.cerraduras
            if c.abre_con_evento == "cocinero_muerto"
        )
        assert not sc._interactables.llavero.tiene("cocinero_vencido"), (
            "el montaje no debería arrancar con la llave imposible ya en "
            "el llavero -- si esto falla, key_id='' en el .tmx (o algo "
            "más) está dejando pasar por Llavero.tiene() vacío"
        )

        bloqueos: list[dict] = []

        def _escuchar(**datos: object) -> None:
            bloqueos.append(datos)

        sc.context.event_bus.subscribe(EVENTO_BLOQUEADA, _escuchar)

        stub = _StubInput()
        sc.context.input_manager = stub
        # Justo a la izquierda de la puerta, sin solaparla (colocar al
        # jugador DENTRO de un sólido cerrado lo eyecta, ver AUD-619) pero
        # dentro de ALCANCE_DE_USO=24px.
        px = cerradura.rect.left - Player.ANCHO_DE_PIE - 4.0
        py = 592.0 - Player.ALTO_DE_PIE
        sc._player.set_spawn(pygame.Vector2(px, py))
        for _ in range(6):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        stub.set_actions({Action.GRAB})
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert cerradura.abierta is False, (
            "la puerta se abrió sin haber vencido al cocinero"
        )
        assert bloqueos, (
            "el bus nunca recibió INTERACT_LOCK_BLOCKED al pulsar GRAB "
            "junto a la puerta"
        )
        assert any(b.get("key_id") == "cocinero_vencido" for b in bloqueos), (
            f"INTERACT_LOCK_BLOCKED se emitió sin el key_id esperado: "
            f"{bloqueos}"
        )
        assert "trabada" in sc._interactables.mensaje, (
            "el cartel de bloqueo no trae el mensaje del .tmx "
            f"('La puerta trasera está trabada...'): "
            f"{sc._interactables.mensaje!r}"
        )

        # AUD-641 — el cartel tiene que verse de verdad: _AvisoDeBloqueo
        # reemite EVENTO_BLOQUEADA como Events.SHOW_MESSAGE, que MessageBox
        # ya sabe mostrar. Unos fotogramas más para que se procese (mismo
        # motivo que _matar_al_cocinero documenta para el aviso de
        # destrabado: se encola DENTRO del propio dispatch()).
        for _ in range(5):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        assert "trabada" in sc._msg_box._full_text, (
            "el cartel de bloqueo no llegó a MessageBox -- "
            f"_full_text={sc._msg_box._full_text!r}"
        )

    # -- vencer al cocinero destraba la puerta -------------------------

    def test_matar_al_cocinero_abre_la_puerta_marca_vencido_y_avisa_por_messagebox(
        self,
    ) -> None:
        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        cerradura = next(
            c for c in sc._stage_data.cerraduras
            if c.abre_con_evento == "cocinero_muerto"
        )
        assert sc._cocinero_vencido is False
        assert cerradura.abierta is False

        _matar_al_cocinero(sc)

        assert sc._cocinero_vencido is True, (
            "_PuertaDelCocinero no marcó _cocinero_vencido al morir el "
            "ShooterCocinero"
        )
        assert cerradura.abierta is True, (
            "abrir_por_evento('cocinero_muerto') no abrió la Cerradura"
        )

        # SHOW_MESSAGE se encola DENTRO del propio dispatch() de
        # ENEMY_DIED (el manejador de _PuertaDelCocinero lo emite mientras
        # el bus todavía está despachando ENEMY_DIED) -- hace falta otro
        # ciclo de dispatch()+update() para que MessageBox lo procese,
        # mismo motivo que documenta _matar_al_cocinero más arriba.
        for _ in range(5):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        assert "destraba" in sc._msg_box._full_text, (
            "MessageBox no muestra el aviso de destrabado esperado "
            f"('...la puerta trasera se destraba.'): "
            f"{sc._msg_box._full_text!r}"
        )

    def test_tras_vencer_al_cocinero_el_jugador_llega_al_next_trigger(self) -> None:
        from src.engine.input.action_map import Action
        from tests.playtest.bot import _StubInput

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        stub = _StubInput()
        sc.context.input_manager = stub
        sc._player.set_spawn(pygame.Vector2(3300.0, 560.0))
        for _ in range(6):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        _matar_al_cocinero(sc)

        stub.set_actions({Action.MOVE_RIGHT})
        llego = False
        for _ in range(int(3 * 60)):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
            if sc._player.rect.colliderect(sc._stage_data.next_trigger):
                llego = True
                break
        assert llego, (
            "el jugador no llegó al NextTrigger incluso con la puerta ya "
            "abierta"
        )

    # -- el letrero de objetivo (con easing) ---------------------------

    def test_el_objetivo_no_aparece_antes_de_entrar_a_la_cocina(self) -> None:
        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        # x=2600: dentro de la sala (interior), a la izquierda de
        # X_ENTRADA_COCINA=2880 -- todavía no es "la cocina".
        sc._player.set_spawn(pygame.Vector2(2600.0, 560.0))
        for _ in range(30):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert sc._objetivo_cocinero.fase == "oculto"
        assert sc._objetivo_cocinero.texto_actual is None

    def test_el_objetivo_pasa_de_pendiente_a_cumplido_y_se_apaga_a_los_cinco_segundos(
        self,
    ) -> None:
        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        sc._player.set_spawn(pygame.Vector2(2900.0, 560.0))  # ya en la cocina
        for _ in range(6):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert sc._objetivo_cocinero.fase in ("apareciendo", "visible"), (
            f"el objetivo no apareció al entrar a la cocina con el "
            f"cocinero vivo: fase={sc._objetivo_cocinero.fase!r}"
        )
        assert sc._objetivo_cocinero.texto_actual is not None
        assert "OBJETIVO:" in sc._objetivo_cocinero.texto_actual
        assert "CUMPLIDO" not in sc._objetivo_cocinero.texto_actual

        _matar_al_cocinero(sc)

        assert sc._objetivo_cocinero.fase == "cumplido"
        assert "CUMPLIDO" in sc._objetivo_cocinero.texto_actual
        assert sc._objetivo_cocinero.alpha == 255

        # DURACION_QUEDARSE (4s) + DURACION_DESVANECIMIENTO (0.6s) = 4.6s;
        # 5.5s de sobra deja margen y cumple el "tras >5s ya no" pedido.
        for _ in range(int(5.5 * 60)):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert sc._objetivo_cocinero.fase == "oculto", (
            f"el objetivo debería haberse apagado tras >5s del "
            f"'cumplido': fase={sc._objetivo_cocinero.fase!r}"
        )
        assert sc._objetivo_cocinero.texto_actual is None
        assert sc._objetivo_cocinero.alpha == 0

    # -- respawn: el cocinero reaparece vivo, la puerta vuelve a cerrarse --

    def test_respawn_con_el_cocinero_vencido_repone_al_cocinero_y_recierra_la_puerta(
        self,
    ) -> None:
        """`respawn()` (`StageScene.on_enter()`) reconstruye
        `_stage_data.entity_list` leyendo el .tmx de nuevo: el
        `ShooterCocinero` vencido reaparece vivo como instancia NUEVA, y
        `_stage_data.cerraduras`/`_interactables` también se reconstruyen,
        así que `Door_Trasera` vuelve a nacer cerrada. Con las dos cosas
        reponiéndose juntas el jugador NO queda encerrado -- sólo tiene
        que volver a vencerlo -- así que `on_stage_start()` resetea
        `_cocinero_vencido` y `_objetivo_cocinero` en cada respawn (a
        diferencia de `_carteles_disparados`, que sí sobrevive: ver el
        docstring de `_cocinero_vencido` en `Stage1_2_LaSoda.__init__`)."""
        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        cerradura_antes = next(
            c for c in sc._stage_data.cerraduras
            if c.abre_con_evento == "cocinero_muerto"
        )

        _matar_al_cocinero(sc)
        assert sc._cocinero_vencido is True
        assert cerradura_antes.abierta is True

        # Un fotograma en sitio seguro antes del respawn -- mismo patrón
        # que `test_el_cartel_de_bienvenida_no_se_repite_tras_un_respawn`.
        sc._player.set_spawn(pygame.Vector2(sc._stage_data.spawn_point))
        sc.update(1 / 60)
        sc.respawn()

        assert sc._cocinero_vencido is False, (
            "tras el respawn el cocinero reaparece vivo -- "
            "_cocinero_vencido tiene que resetearse, si no la puerta "
            "quedaría cerrada para siempre (el jugador encerrado)"
        )
        cocineros_tras_respawn = [
            e for e in sc._stage_data.entity_list
            if isinstance(e, ShooterCocinero)
        ]
        assert cocineros_tras_respawn, (
            "el respawn no repuso ningún ShooterCocinero en entity_list"
        )
        assert all(c.is_alive for c in cocineros_tras_respawn), (
            "el ShooterCocinero repuesto por el respawn debería nacer vivo"
        )

        cerradura_tras_respawn = next(
            c for c in sc._stage_data.cerraduras
            if c.abre_con_evento == "cocinero_muerto"
        )
        assert cerradura_tras_respawn is not cerradura_antes, (
            "si esto empieza a fallar, StageScene ya no reconstruye "
            "_stage_data.cerraduras en cada respawn y el resto de esta "
            "prueba no aplica"
        )
        assert cerradura_tras_respawn.abierta is False, (
            "la puerta debería volver a estar cerrada tras el respawn, ya "
            "que el cocinero también reapareció vivo"
        )
        assert sc._objetivo_cocinero.fase == "oculto", (
            "el letrero de objetivo debería reiniciarse a 'oculto' tras "
            "el respawn, listo para deslizarse de nuevo"
        )


class TestAvisosDelMotorSilenciados:
    """AUD-656 — blindaje defensivo ante `feature/master-plan`.

    En `origin/feature/master-plan` (reporte propio, "Fix reporte
    Guillermo 7b") `InteractableSystem._avisar()` deja de ser un simple
    setter de `mensaje`/`mensaje_timer` y pasa ADEMÁS a emitir
    `Events.SHOW_MESSAGE` directo al bus — publicando el texto crudo
    (`key_id` sin traducir, ver `_AvisoDeBloqueo`) sin ningún rate-limit, y
    ANTES de que esta stage llegue a mostrar su propio cartel
    (`abrir_por_evento` llama a `_avisar` antes de que
    `_PuertaDelCocinero._on_enemy_died` emita el suyo). Esta clase
    reproduce esa versión con un `monkeypatch` de la CLASE
    `InteractableSystem` (no depende de esa rama, sólo replica su diff) y
    comprueba que `_silenciar_avisos_genericos_del_motor`
    (`stage1_2_la_soda.py`) evita la duplicación sin tocar
    `_AvisoDeBloqueo` ni `_PuertaDelCocinero`.

    Corrida ANTES de implementar el arreglo (con el `monkeypatch` puesto,
    `git stash` de `_silenciar_avisos_genericos_del_motor`): (a) y (b) en
    rojo — se cuelan avisos crudos del motor / el orden se invierte. Sin
    el `monkeypatch` (el resto de la suite, `InteractableSystem._avisar`
    intacto), nada cambia: en `dev` ya era un no-op hacia el bus.
    """

    @staticmethod
    def _avisar_como_master_plan(self, texto: str, duracion: float = 2.0) -> None:
        """Réplica de `InteractableSystem._avisar` en
        `feature/master-plan`: además de fijar `mensaje`/`mensaje_timer`
        (lo único que hace en `dev`, `interactable_system.py:297-299`),
        publica `Events.SHOW_MESSAGE` directo al bus. Se usa para
        monkeypatchear la CLASE entera y simular ese motor sin depender de
        esa rama."""
        from src.engine.core.events import Events

        self.mensaje = texto
        self.mensaje_timer = duracion
        if self._bus is not None:
            self._bus.emit(Events.SHOW_MESSAGE, text=texto, duration=duracion)

    def test_con_el_avisar_del_motor_nuevo_el_cofre_no_duplica_el_aviso(
        self, monkeypatch,
    ) -> None:
        """(a) — jugador frente al cofre sin llave, sosteniendo GRAB ~30
        fotogramas: el aviso traducido de `_AvisoDeBloqueo` aparece UNA
        sola vez en la cola/texto visible de `MessageBox`, y ninguna copia
        cruda con `llave_deposito` se cuela (la que el `_avisar` del motor
        nuevo publicaría directo, sin traducir ni rate-limitar)."""
        from src.engine.input.action_map import Action
        from src.framework.entities.player import Player
        from src.framework.stage.interactable_system import InteractableSystem
        from tests.playtest.bot import _StubInput

        monkeypatch.setattr(
            InteractableSystem, "_avisar", self._avisar_como_master_plan,
        )

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        cofre = next(
            c for c in sc._stage_data.cofres if c.key_id == "llave_deposito"
        )
        stub = _StubInput()
        sc.context.input_manager = stub
        px = cofre.rect.centerx - Player.ANCHO_DE_PIE / 2.0
        py = cofre.rect.bottom - Player.ALTO_DE_PIE
        sc._player.set_spawn(pygame.Vector2(px, py))
        for _ in range(6):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        # Sostiene GRAB sin volver a llamar set_actions: el flanco de
        # `_StubInput.is_action_just_pressed` (ver docstring de esa clase,
        # `tests/playtest/bot.py`) queda "recién pulsado" en todos los
        # fotogramas siguientes porque `_prev` nunca se actualiza -- el
        # peor caso real que el dueño reportó (GRAB sostenido contra el
        # cofre cerrado), no sólo un toque suelto.
        stub.set_actions({Action.GRAB})
        for _ in range(30):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        textos = [str(d.get("text", "")) for d in sc._msg_box._queue]
        if sc._msg_box._visible:
            textos.insert(0, sc._msg_box._full_text)

        traducidos = [t for t in textos if "la llave del depósito" in t]
        crudos = [t for t in textos if "llave_deposito" in t]

        assert len(traducidos) == 1, (
            f"debería aparecer UNA sola vez el aviso traducido de "
            f"_AvisoDeBloqueo, aunque el _avisar() del motor también "
            f"publique al bus: {textos!r}"
        )
        assert not crudos, (
            f"se coló una copia cruda (key_id sin traducir) del "
            f"_avisar() del motor nuevo: {textos!r}"
        )

    def test_con_el_avisar_del_motor_nuevo_el_cartel_del_cocinero_sale_primero(
        self, monkeypatch,
    ) -> None:
        """(b) — al vencer al cocinero, el primer mensaje que muestra
        `MessageBox` tiene que ser el cartel propio de `_PuertaDelCocinero`
        ("El cocinero cayó..."), no el aviso genérico "Se ha abierto algo"
        que `abrir_por_evento` dispara primero, internamente, al abrir la
        cerradura."""
        from src.framework.stage.interactable_system import InteractableSystem

        monkeypatch.setattr(
            InteractableSystem, "_avisar", self._avisar_como_master_plan,
        )

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()

        _matar_al_cocinero(sc)
        # SHOW_MESSAGE se encola DENTRO del propio dispatch() de
        # ENEMY_DIED -- mismo motivo documentado en _matar_al_cocinero y en
        # TestPuertaDelCocinero: hace falta otro ciclo de dispatch()+
        # update() para que MessageBox lo procese.
        for _ in range(5):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert sc._msg_box._visible is True, (
            "MessageBox no muestra ningún mensaje tras matar al cocinero"
        )
        assert "El cocinero cayó" in sc._msg_box._full_text, (
            f"el primer mensaje visible debería ser el cartel propio del "
            f"cocinero, no uno genérico del motor: "
            f"_full_text={sc._msg_box._full_text!r}"
        )
        textos_en_cola = [str(d.get("text", "")) for d in sc._msg_box._queue]
        assert not any("Se ha abierto algo" in t for t in textos_en_cola), (
            f"se coló el aviso genérico del motor detrás del cartel "
            f"propio: {textos_en_cola!r}"
        )

    def test_el_silenciador_se_reaplica_tras_un_respawn(self, monkeypatch) -> None:
        """(c) — `respawn()` reconstruye `_interactables` como una
        instancia NUEVA (`StageScene.on_enter`); el silenciador tiene que
        reaplicarse ahí también, no sólo la primera vez que carga el
        nivel."""
        from src.engine.core.events import Events
        from src.framework.stage.interactable_system import InteractableSystem

        monkeypatch.setattr(
            InteractableSystem, "_avisar", self._avisar_como_master_plan,
        )

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        interactables_antes = sc._interactables
        assert "_avisar" in interactables_antes.__dict__, (
            "el silenciador no se aplicó en el primer on_enter() -- "
            "debería quedar como atributo de INSTANCIA, no de clase"
        )

        sc._player.set_spawn(pygame.Vector2(sc._stage_data.spawn_point))
        sc.update(1 / 60)
        sc.respawn()

        interactables_despues = sc._interactables
        assert interactables_despues is not interactables_antes, (
            "si esto falla, StageScene ya no reconstruye _interactables en "
            "cada respawn y el resto de esta prueba no aplica"
        )
        assert "_avisar" in interactables_despues.__dict__, (
            "el silenciador no se reaplicó tras el respawn -- la instancia "
            "nueva de InteractableSystem sigue usando el _avisar() del "
            "motor (monkeypatcheado acá para simular feature/master-plan)"
        )

        avisos: list[dict] = []

        def _escuchar(**datos: object) -> None:
            avisos.append(datos)

        sc.context.event_bus.subscribe(Events.SHOW_MESSAGE, _escuchar)
        interactables_despues._avisar("texto de prueba")
        sc.context.event_bus.dispatch()
        assert not avisos, (
            f"la instancia nueva sigue emitiendo al bus tras el respawn: "
            f"{avisos!r}"
        )


# ──────────────────────────────────────────────────────────────────────────
# AUD-643 — "lo intenté matar pero en una quedó como flotando y no le
# llegaba a pegar" (reporte del dueño, prioridad alta junto con el punto 1).
#
# Diagnosticado en headless golpeando al `ShooterCocinero` directo con
# `apply_hit` (la misma API que usa `_matar_al_cocinero` arriba, y la que
# de verdad llama `CollisionSystem.process_attack`,
# `collision_system.py:249-257` — que ADEMÁS suma su propio impulso
# vertical, `KNOCKBACK_IMPULSE_Y=-100`, encima del de `apply_hit`, así que
# la magnitud real en juego es mayor que la de estas pruebas) y registrando
# `position.y`/`_knockback_velocity.y`/`state` fotograma a fotograma:
#
#   * un golpe "heavy" o "light" (daño < 1.5, el rango del ataque normal
#     del jugador — `player.current_attack_damage`, 0.5 liviano / 1.0
#     pesado) deja `state = EnemyState.HURT` con `_knockback_velocity.y`
#     en -100/-30 (`enemy_base.py:526-552`); la gravedad SÓLO se vuelve a
#     sumar dentro de la rama `EnemyState.LAUNCHED` de `_run_state_machine`
#     (`enemy_base.py:870-881`), así que en HURT ese impulso hacia arriba
#     nunca se contrarresta — sólo decae por fricción
#     (`_apply_knockback`, factor 0.85/fotograma) y el cocinero se queda
#     flotando en el aire para siempre, ~11px más arriba por cada golpe;
#   * un golpe "launch" (daño >= 1.5) tiene además su propio bug de
#     encuadre: `_ground_y` se fija a `position.y` ANTES de que ese mismo
#     fotograma mueva nada, así que el chequeo de aterrizaje de
#     `_run_state_machine` lo encuentra trivialmente cumplido y cancela el
#     salto entero sin que el cocinero llegue a despegar.
#
# Ninguno de los dos es arreglable sin tocar `enemy_base.py` (fuera de
# alcance: `src/framework/` no se toca). El arreglo, en código propio de
# `entities.py` (`ShooterCocinero.update`, AUD-643): ancla `position.y` a
# la altura de spawn y recorta `position.x` al ancho de `Cocina_Repisa`
# (x=2944-3072 en el `.tmx`) al final de cada fotograma, salvo mientras
# `state == LAUNCHED` (se le deja intentar aterrizar solo, sin pelear con
# esa rama del motor).
# ──────────────────────────────────────────────────────────────────────────


class TestElCocineroNoQuedaFlotando:
    """AUD-643 — `ShooterCocinero.update` ancla la posición tras cada golpe."""

    def _cocinero(self, sc):
        return next(
            e for e in sc._stage_data.entity_list if isinstance(e, ShooterCocinero)
        )

    def test_golpes_no_letales_repetidos_no_lo_suben_permanentemente(self) -> None:
        """Reproduce el reporte del dueño: golpear varias veces sin matarlo
        de un solo golpe. Antes de AUD-643 esto lo subía ~11px por golpe y
        se quedaba ahí para siempre (medido con el código viejo, ver el
        comentario de la sección); tras el arreglo, la `y` vuelve a la de
        spawn en el mismo fotograma del golpe."""
        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        cocinero = self._cocinero(sc)
        y_repisa = cocinero.position.y
        # AUD-650 — no asume `max_health == 3` (otra entrega de este
        # mismo AUD la subió a 5 en `entities.py`, con una segunda fase):
        # golpea `max_health - 1` veces con daño 1.0 cada vez, así SIEMPRE
        # queda con 1.0 de vida al final del bucle (>0, sigue vivo) sin
        # importar cuál sea la vida máxima real de la instancia.
        golpes_no_letales = max(1, int(cocinero.max_health) - 1)

        for golpe in range(1, golpes_no_letales + 1):
            cocinero.apply_hit(1.0, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
            for _ in range(40):
                sc.context.event_bus.dispatch()
                sc.update(1 / 60)
            assert cocinero.is_alive, f"murió antes de tiempo en el golpe {golpe}"
            assert cocinero.position.y == y_repisa, (
                f"tras el golpe {golpe} el cocinero quedó flotando: "
                f"y={cocinero.position.y:.2f} (repisa={y_repisa:.2f})"
            )

    def test_el_empuje_horizontal_no_lo_saca_de_la_repisa(self) -> None:
        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        cocinero = self._cocinero(sc)

        # Golpe desde bien a la izquierda -> empuje hacia la derecha, fuera
        # de la repisa si nada lo recorta.
        cocinero.apply_hit(0.5, (cocinero.rect.centerx - 400.0, cocinero.rect.centery))
        for _ in range(40):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert cocinero.position.x <= ShooterCocinero.X_MAX_REPISA, (
            f"el cocinero salió de la repisa por la derecha: "
            f"x={cocinero.position.x:.2f} > {ShooterCocinero.X_MAX_REPISA}"
        )
        assert cocinero.position.x >= ShooterCocinero.X_MIN_REPISA, (
            f"el cocinero salió de la repisa por la izquierda: "
            f"x={cocinero.position.x:.2f} < {ShooterCocinero.X_MIN_REPISA}"
        )

    def test_se_lo_puede_matar_tras_flotar_y_la_puerta_se_abre(self) -> None:
        """Extremo a extremo: varios golpes no letales (que antes lo
        dejaban flotando e inalcanzable) y por último uno letal -- tiene
        que poder matarse, emitir `ENEMY_DIED` con el `entity_id` correcto,
        y abrir `Door_Trasera` -- igual que ya prueba `TestPuertaDelCocinero`,
        pero pasando primero por el escenario del bug reportado."""
        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        cocinero = self._cocinero(sc)
        cerradura = next(
            c for c in sc._stage_data.cerraduras
            if c.abre_con_evento == "cocinero_muerto"
        )

        muertes: list[dict] = []

        def _escuchar(**datos: object) -> None:
            muertes.append(datos)

        sc.context.event_bus.subscribe("ENEMY_DIED", _escuchar)

        for _ in range(2):
            cocinero.apply_hit(1.0, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
            for _ in range(40):
                sc.context.event_bus.dispatch()
                sc.update(1 / 60)

        # Golpe final, letal (vida ya en 1.0). `is_alive` sigue en True
        # hasta que `_death_timer` (0.5s = 30 fotogramas, BUG-031 FIX en
        # `enemy_base.py`) se agota -- 10 fotogramas no alcanzan, mismo
        # margen que el resto de esta prueba (40).
        cocinero.apply_hit(10.0, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
        for _ in range(40):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        assert not cocinero.is_alive
        assert muertes, "nunca se emitió ENEMY_DIED"
        assert muertes[0]["entity_id"].startswith("ShooterCocinero"), (
            f"entity_id inesperado: {muertes[0]['entity_id']!r}"
        )
        assert cerradura.abierta is True, (
            "la puerta trasera no se abrió tras matar al cocinero"
        )
        assert sc._cocinero_vencido is True


# ──────────────────────────────────────────────────────────────────────────
# AUD-644 — "una rata herida caminaba hacia atrás hasta clavarse en la
# esquina de la sala y la cucaracha abandonaba su curva" (playtest del
# dueño, 26/8).
#
# `EnemyBase` entra en `RETREAT` con `current_health/max_health <=
# RETREAT_HEALTH_FRACTION` (0.25, `enemy_base.py:986`) y el jugador cerca
# (`_should_retreat`, `enemy_base.py:1016-1018`), y `_retreat_behavior`
# (`enemy_base.py:1091-1099`) aleja al enemigo del jugador al 80% de
# `alert_speed` SIN chequear paredes ni bordes. `WalkerRaton`,
# `FlyingCucaracha`, `WalkerCulebra` y `FlyingZancudo` ya anulaban
# `_search_behavior` (ver sus docstrings) pero no `_retreat_behavior` --
# sólo `ShooterCocinero` lo hacía (AUD-643).
#
# El arreglo NO puede ser sólo anular `_retreat_behavior`: el estado
# `RETREAT` (`enemy_base.py:923-931`) vuelve a evaluar `_should_retreat()`
# cada fotograma y no sale de él mientras siga siendo `True` -- con SÓLO el
# no-op el enemigo queda **congelado** en `RETREAT` (comprobado en headless,
# fuera de esta prueba: 150 fotogramas con `_retreat_behavior` anulado y
# `_should_retreat` intacto dejan al bicho en `RETREAT` todo el tiempo, sin
# atacar ni patrullar, la posición sin cambiar más de un par de centésimas
# de píxel de ruido de punto flotante). Por eso las cuatro clases anulan
# TAMBIÉN `_should_retreat()` -> `False`, para que ni siquiera entren en
# `RETREAT` y sigan en ALERT/CHASE (o su patrulla/curva propia, según la
# clase) -- exactamente lo mismo que ya hace `ShooterCocinero` desde
# AUD-643. `docs/18_ENEMY_ROSTER.md` no menciona que ninguna de las cuatro
# plagas de La Soda huya con poca vida.
# ──────────────────────────────────────────────────────────────────────────


class TestLasPlagasNoSeRetiran:
    """AUD-644 — las cuatro plagas propias de La Soda no huyen con poca vida.

    Montaje sobre la escena real (`_construir_escena_la_soda()`), mismo
    patrón que `TestElCocineroNoQuedaFlotando`: se busca la instancia en
    `sc._stage_data.entity_list`, se le baja la vida con `apply_hit` (la API
    real, la misma que usa `CollisionSystem.process_attack`) y se corren
    fotogramas de verdad con `sc.update()` + `event_bus.dispatch()`.
    """

    PLAGAS = (WalkerRaton, FlyingCucaracha, WalkerCulebra, FlyingZancudo)

    def _buscar(self, sc, Clase):
        return next(e for e in sc._stage_data.entity_list if isinstance(e, Clase))

    def _caja_de_ruta(self, enemigo):
        """Los límites que el enemigo NUNCA debería cruzar si no huye: la
        franja de patrulla propia (terrestres, `_patrol_origin` +
        `patrol_length`, ver `WalkerRaton`/`WalkerCulebra` más arriba) o la
        caja de la curva Catmull-Rom propia (voladoras, `_curve_points`, ver
        `FlyingCucaracha`/`FlyingZancudo`). Devuelve `(min_x, max_x)`.
        """
        if hasattr(enemigo, "_curve_points"):
            xs = [p.x for p in enemigo._curve_points]
            return min(xs), max(xs)
        mitad = enemigo.patrol_length / 2.0
        return (
            enemigo._patrol_origin.x - mitad,
            enemigo._patrol_origin.x + mitad,
        )

    @pytest.mark.parametrize("Clase", PLAGAS)
    def test_con_poca_vida_y_el_jugador_cerca_no_huye(self, Clase) -> None:
        from src.framework.entities.enemy_base import EnemyState

        sc = _construir_escena_la_soda()
        enemigo = self._buscar(sc, Clase)

        # `WalkerRaton`/`FlyingCucaracha` están más allá de `ROOM_LIMIT_X`
        # (adentro de La Soda): si el cuarto sigue "exterior", posicionar al
        # jugador cerca de ellos cruza `TRIGGER_X` y el fundido/teletransporte
        # de `_RoomTransition.maybe_trigger` secuestra al jugador a mitad de
        # la prueba -- termina en `ROOM_LIMIT_X + ENTRY_OFFSET`, lejos de
        # donde se lo colocó y fuera de rango de detección. Mismo
        # `disarm_to_interior()` que ya usa `TestElCocineroNoQuedaFlotando`.
        if enemigo.position.x >= sc._room_transition.ROOM_LIMIT_X:
            sc._room_transition.disarm_to_interior()

        # Bajar la vida al 20% (<= RETREAT_HEALTH_FRACTION=0.25) con la API
        # real de daño.
        objetivo = enemigo.max_health * 0.20
        dano = enemigo.current_health - objetivo
        enemigo.apply_hit(dano, (enemigo.rect.centerx - 40.0, enemigo.rect.centery))
        assert enemigo.current_health / enemigo.max_health <= 0.25, (
            "el montaje de la prueba no dejó al enemigo por debajo del "
            "umbral de repliegue"
        )

        # Asentar el golpe (HURT + knockback) con el jugador lejos, para no
        # mezclar el impulso del propio golpe con la medición de huida.
        sc._player.set_spawn(
            pygame.Vector2(enemigo.position.x - 2000.0, enemigo.position.y)
        )
        for _ in range(30):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        # Jugador cerca, dentro del rango de detección propio de la clase.
        # El pie del jugador se alinea con el pie del enemigo -- no su Y
        # cruda -- porque el jugador mide 32px de alto contra los 28px de un
        # enemigo terrestre: igualar las Y lo embebe 4px en el piso y
        # dispara una rareza de la resolución de colisiones del framework
        # que empuja al jugador horizontalmente hasta el borde del mapa en
        # vez de sólo reflotarlo (encontrado armando esta prueba).
        px = enemigo.position.x + min(40.0, enemigo.detection_range_x - 10.0)
        py = enemigo.rect.bottom - sc._player.rect.height
        sc._player.set_spawn(pygame.Vector2(px, py))

        # Calienta la cámara antes de medir: un enemigo lejos de ella no se
        # simula (`framework/stage/culling.py`, AUD-279 -- 800px de margen a
        # cada lado del encuadre) y el teletransporte recién colocó al
        # jugador lejos de donde estaba la cámara.
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        min_x, max_x = self._caja_de_ruta(enemigo)
        MARGEN_PX = 5.0  # cubre el "scent lock"/curva propios; ver el
        # diagnóstico del AUD: arreglado, la peor desviación medida fue
        # 0.7px; roto, la menor fue 28.2px -- 5px separa limpio los dos.

        pos_inicial = pygame.Vector2(enemigo.position)
        estado_inicial = enemigo.state
        se_movio = False
        vio_retreat = False
        peor_desvio = 0.0
        for _ in range(120):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
            if enemigo.state == EnemyState.RETREAT:
                vio_retreat = True
            if enemigo.position != pos_inicial or enemigo.state != estado_inicial:
                se_movio = True
            desvio = max(min_x - enemigo.position.x, enemigo.position.x - max_x, 0.0)
            peor_desvio = max(peor_desvio, desvio)

        assert not vio_retreat, (
            f"{Clase.__name__} entró en RETREAT con poca vida: el repliegue "
            "heredado de EnemyBase no chequea paredes ni bordes"
        )
        assert peor_desvio <= MARGEN_PX, (
            f"{Clase.__name__} se alejó {peor_desvio:.1f}px más allá de su "
            f"franja/curva propia ({min_x:.1f}, {max_x:.1f}) -- eso es huir, "
            "no patrullar/volar su ruta"
        )
        assert se_movio, (
            f"{Clase.__name__} quedó congelado en vez de seguir "
            "patrullando/atacando"
        )


# ──────────────────────────────────────────────────────────────────────────
# AUD-641 — verificación con el bot real de playtest, tras bloquear la
# salida detrás de la puerta del cocinero.
#
# Hasta este cambio la verificación con `walk_right_bot`/`run_playthrough`
# (`tests/playtest/bot.py`, del profesor) se hacía a mano en cada commit --
# `LA_SODA_PROGRESO.md` (fuera del repo) registra "Bot determinista: 98.5%
# de avance, 0 muertes" en más de una decena de entradas -- pero nunca
# quedó como una prueba de este archivo. Se formaliza acá porque el diseño
# de la salida cambió (AUD-641, decisión del dueño 26/8): antes el bot de
# referencia --camina y salta, nunca combate ni pulsa GRAB-- llegaba hasta
# la salida real (`reached_exit=True`, ~98.5% de avance, `max_x≈3373`);
# ahora se topa con `Door_Trasera` mucho antes y se queda ahí, porque no
# sabe pelear. Es el comportamiento CORRECTO del nuevo diseño, no una
# regresión: la salida ahora exige vencer al cocinero, y un bot que sólo
# camina/salta no puede hacerlo por definición.
# ──────────────────────────────────────────────────────────────────────────


class TestBotDeVerificacionConLaPuertaDelCocinero:
    """Medido con el bot real (`run_playthrough` + `walk_right_bot`, no una
    partida jugada a mano) sobre `_construir_escena_la_soda()`."""

    def test_el_bot_de_solo_caminar_y_saltar_ya_no_llega_a_la_salida(self) -> None:
        """Sin combatir, el bot se topa con la puerta cerrada y se queda
        ahí durante los 90s completos: `reached_exit=False`, sin muertes
        (la puerta lo detiene, no lo mata) y con un avance casi tan alto
        como antes -- llega hasta la puerta, no se queda a mitad de
        camino. Medido de verdad (`run_playthrough`):
        `progress_ratio≈0.976`, `max_x≈3341` (contra `max_x≈3373` de antes
        del cambio -- la diferencia son los ~32px del jugador parado
        contra el borde de `Door_Trasera`, x=3360), `deaths=[]`."""
        from tests.playtest.bot import run_playthrough, walk_right_bot

        sc = _construir_escena_la_soda()
        log = run_playthrough(sc, walk_right_bot(seconds=90))

        assert log.reached_exit is False, (
            "el bot llegó a la salida sin haber vencido al cocinero -- la "
            "puerta no está bloqueando de verdad"
        )
        assert log.deaths == [], (
            f"el bot murió contra la puerta cerrada, no debería: "
            f"{log.deaths}"
        )
        assert log.progress_ratio >= 0.96, (
            f"el bot no llegó ni siquiera hasta la puerta: "
            f"progress_ratio={log.progress_ratio:.4f}"
        )

    def test_matando_al_cocinero_antes_el_bot_llega_a_la_salida_como_siempre(
        self,
    ) -> None:
        """Con el cocinero ya vencido (con la API real de daño, igual que
        `_matar_al_cocinero`) antes de soltar al bot, la puerta ya está
        abierta y el resto del recorrido es idéntico al de siempre: el bot
        llega a la salida sin morir. Medido de verdad: `reached_exit=True`,
        `progress_ratio≈0.985`, `elapsed≈66.3s`.

        AUD-643 — el límite de tiempo del mapa subió de 240s a 360s (el
        dueño terminó una pasada normal, con una muerte, en 00:54 sin
        vencer al cocinero); ~66s es de sobra incluso con el límite viejo,
        así que el bot de referencia sigue completando el nivel de sobra
        con el nuevo."""
        from tests.playtest.bot import run_playthrough, walk_right_bot

        sc = _construir_escena_la_soda()
        _matar_al_cocinero(sc)

        log = run_playthrough(sc, walk_right_bot(seconds=90))

        assert log.reached_exit is True, (
            "con el cocinero ya vencido el bot debería llegar a la salida "
            "igual que antes de AUD-641"
        )
        assert log.deaths == []
        assert log.elapsed < sc._stage_data.time_limit, (
            f"el bot tardó {log.elapsed:.1f}s, más que el límite de tiempo "
            f"del mapa ({sc._stage_data.time_limit}s)"
        )


class TestTimeLimitDelMapa:
    """AUD-643, punto 4 — el dueño terminó una pasada normal (una muerte,
    sin vencer al cocinero) con 00:54 en el reloj. `time_limit` sube de
    240 a 360 en el `.tmx` (única fuente de verdad para el reloj real: el
    `HUD` lo arranca con `_stage_data.time_limit`, que `StageLoader` lee de
    esta propiedad — `stage_scene.py:616-617`, `stage_loader.py:440` — la
    constante `Stage1_2_LaSoda.TIME_LIMIT` es sólo metadato de
    documentación, ningún otro módulo la lee)."""

    def test_time_limit_del_tmx_es_360(self, datos_del_nivel) -> None:
        assert datos_del_nivel.time_limit == 360

    def test_time_limit_de_la_escena_real_es_360(self) -> None:
        sc = _construir_escena_la_soda()
        assert sc._stage_data.time_limit == 360
        assert sc._hud.time_limit == 360


# ──────────────────────────────────────────────────────────────────────────
# AUD-645 — Unidad VII (Evaluación Práctica II): histograma + brillo/
# contraste, convolución y detección de bordes de `FilterTools`, cada uno
# dirigiendo una decisión real de juego (no sólo decoración) en La Soda.
# Ver `stage1_2_la_soda.py`: `_LecturaDeLuz`, `_ObjetivoCocinero._fondo_para`,
# `_ContornoDeAlerta`.
# ──────────────────────────────────────────────────────────────────────────


def _superficie_de_color(color, ancho=100, alto=75):
    """Superficie sintética de un solo color -- luminancia conocida de
    antemano, para probar `_LecturaDeLuz` sin depender del .tmx real."""
    superficie = pygame.Surface((ancho, alto))
    superficie.fill(color)
    return superficie


class TestLecturaDeLuz:
    """AUD-645 -- Unidad VII, ítem 1: `FilterTools.compute_histogram()` +
    `adjust_brightness()` deciden la "adaptación a la penumbra"
    (`_LecturaDeLuz` en `stage1_2_la_soda.py`)."""

    def test_luminancia_media_de_una_superficie_de_color_conocido(self) -> None:
        """`_luminancia_media` es el promedio ponderado del histograma de
        luminancia -- sobre una superficie de un solo color (128,128,128)
        la fórmula BT.601 que ya usa `compute_histogram`
        (0.299 R + 0.587 G + 0.114 B, filter_tools.py:46) da 128 exacto
        (los tres coeficientes suman 1)."""
        from src.framework.processing.filter_tools import FilterTools
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _LecturaDeLuz

        gris = _superficie_de_color((128, 128, 128))
        histograma = FilterTools.compute_histogram(gris)
        luminancia = _LecturaDeLuz._luminancia_media(histograma)
        # Tolerancia de 2, no 0: `compute_histogram` trunca con
        # `.astype(np.uint8)` (filter_tools.py:46), y
        # 0.299+0.587+0.114 no cae en exactamente 1.0 en float32 -- el
        # redondeo hacia abajo de esa suma constante da 127, no 128.
        assert abs(luminancia - 128.0) < 2.0, (
            f"luminancia media de un gris uniforme (128,128,128) debería "
            f"dar ~128, dio {luminancia}"
        )

    def test_una_sala_oscura_dispara_el_aviso_y_el_ajuste_de_brillo(self) -> None:
        """Superficie sintética oscura (luminancia bien por debajo de
        `UMBRAL_LUMINANCIA=90`): el histograma decide subir el brillo con
        `adjust_brightness` y avisar por `EventBus` -- las dos acciones de
        juego que pide la Unidad VII."""
        from src.engine.core.event_bus import EventBus
        from src.engine.core.events import Events
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _LecturaDeLuz

        oscura = _superficie_de_color((20, 20, 20))
        lectura = _LecturaDeLuz()
        bus = EventBus()

        lectura.analizar_si_hace_falta(oscura, "interior", bus)

        assert lectura.luminancia_antes is not None
        assert lectura.luminancia_antes < _LecturaDeLuz.UMBRAL_LUMINANCIA
        assert lectura.luminancia_despues is not None
        assert lectura.luminancia_despues > lectura.luminancia_antes, (
            "adjust_brightness debería subir la luminancia medida, no bajarla"
        )
        assert 1.0 < lectura.factor_aplicado <= _LecturaDeLuz.FACTOR_MAXIMO
        assert lectura._overlay is not None, (
            "una sala oscura debería armar el overlay de brillo"
        )
        nombres = [nombre for nombre, _ in bus._queue]
        assert Events.SHOW_MESSAGE in nombres, (
            "una sala oscura debería avisar al jugador por SHOW_MESSAGE"
        )

    def test_una_sala_ya_brillante_no_toca_nada(self) -> None:
        """Sobre el umbral, no hay ajuste de brillo ni aviso -- el
        histograma también decide cuándo NO actuar."""
        from src.engine.core.event_bus import EventBus
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _LecturaDeLuz

        clara = _superficie_de_color((200, 200, 200))
        lectura = _LecturaDeLuz()
        bus = EventBus()

        lectura.analizar_si_hace_falta(clara, "interior", bus)

        assert lectura.luminancia_antes is not None
        assert lectura.luminancia_antes >= _LecturaDeLuz.UMBRAL_LUMINANCIA
        assert lectura.factor_aplicado == 1.0
        assert lectura._overlay is None
        assert bus._queue == []

    def test_solo_mide_una_vez_por_vida_de_la_escena(self) -> None:
        """Segunda llamada en adelante con `room="interior"` no vuelve a
        tocar `FilterTools.compute_histogram` -- el costo de la Unidad VII
        es del instante del cruce, no de cada fotograma."""
        from unittest.mock import patch

        from src.engine.core.event_bus import EventBus
        from src.framework.processing.filter_tools import FilterTools
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _LecturaDeLuz

        oscura = _superficie_de_color((20, 20, 20))
        lectura = _LecturaDeLuz()
        bus = EventBus()

        with patch.object(
            FilterTools, "compute_histogram", wraps=FilterTools.compute_histogram,
        ) as espia:
            lectura.analizar_si_hace_falta(oscura, "interior", bus)
            primero = espia.call_count
            assert primero >= 1
            for _ in range(120):
                lectura.analizar_si_hace_falta(oscura, "interior", bus)
            assert espia.call_count == primero, (
                "compute_histogram se volvió a llamar en fotogramas "
                "posteriores al cruce -- el costo ya no es 'una sola vez'"
            )

    def test_no_mide_mientras_el_cuarto_sigue_siendo_exterior(self) -> None:
        from src.engine.core.event_bus import EventBus
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _LecturaDeLuz

        oscura = _superficie_de_color((20, 20, 20))
        lectura = _LecturaDeLuz()
        bus = EventBus()

        lectura.analizar_si_hace_falta(oscura, "exterior", bus)

        assert lectura.luminancia_antes is None
        assert lectura._overlay is None

    def test_la_escena_real_al_cruzar_a_la_sala_mide_una_luminancia_baja_y_la_corrige(
        self,
    ) -> None:
        """Contra el mapa real: parado justo pasando `ROOM_LIMIT_X` (dentro
        de la sala, antes de llegar a la cocina) mide una luminancia baja
        de verdad -- no un número inventado -- y la corrige hacia
        `LUMINANCIA_OBJETIVO`. Calibrado con el juego real: ~55 antes,
        ~88 después, factor 1.6 (el tope) -- ver README, Unidad VII.
        AUD-646 bajó estas cifras de referencia (antes ~58/~93 con
        UMBRAL_LUMINANCIA=90/LUMINANCIA_OBJETIVO=115): el umbral subió a
        70 y el objetivo a 90 en la misma proporción (ver el docstring de
        `_LecturaDeLuz`), pero la sala real sigue midiendo oscura y
        `adjust_brightness` sigue topando en `FACTOR_MAXIMO`."""
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _RoomTransition

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        sc._player.set_spawn(
            pygame.Vector2(_RoomTransition.ROOM_LIMIT_X + 40.0, 560.0),
        )
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        superficie = pygame.Surface((800, 600))
        sc.draw(superficie)

        assert sc._lectura_de_luz.luminancia_antes is not None
        assert sc._lectura_de_luz.luminancia_antes < sc._lectura_de_luz.UMBRAL_LUMINANCIA, (
            f"se esperaba que la sala real midiera oscura, dio "
            f"{sc._lectura_de_luz.luminancia_antes}"
        )
        assert sc._lectura_de_luz.luminancia_despues > sc._lectura_de_luz.luminancia_antes
        assert sc._lectura_de_luz._overlay is not None
        assert sc._lectura_de_luz.factor_aplicado > 1.0

    def test_alpha_del_overlay_nunca_supera_el_tope(self) -> None:
        """AUD-646 -- Regresión 1: AUD-645 dejaba alpha hasta 132/255
        (~52%), un velo blanco lavando la pantalla entera. El tope ahora
        es duro (`ALPHA_MAXIMO=36`, ~14%) y el color es cálido, no
        blanco -- probado con el peor caso posible (una sala casi negra,
        que pide el factor máximo)."""
        from src.engine.core.event_bus import EventBus
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _LecturaDeLuz

        muy_oscura = _superficie_de_color((5, 5, 5))
        lectura = _LecturaDeLuz()
        bus = EventBus()

        lectura.analizar_si_hace_falta(muy_oscura, "interior", bus)

        assert lectura._overlay is not None
        color = lectura._overlay.get_at((0, 0))
        assert color[3] <= _LecturaDeLuz.ALPHA_MAXIMO, (
            f"alpha del overlay de brillo no debería superar "
            f"{_LecturaDeLuz.ALPHA_MAXIMO} (~14%), dio {color[3]}"
        )
        assert tuple(color[:3]) == (255, 230, 190), (
            "el overlay de AUD-646 tiene que ser cálido (255,230,190), no "
            f"blanco -- dio {tuple(color[:3])}"
        )

    def test_el_overlay_no_se_aplica_desde_dibujar_ui(self) -> None:
        """AUD-646 -- Regresión 1: el overlay vivía en `dibujar_ui`
        (`Stage1_2_LaSoda.dibujar_ui`), lavando HUD y letreros por igual
        junto con el mundo. Ahora vive al final de `dibujar_mundo` -- este
        test comprueba que `dibujar_ui`, por sí sola, ya no toca
        `_lectura_de_luz` en absoluto (ni mide ni blitea el overlay)."""
        from unittest.mock import patch

        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _RoomTransition

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        sc._player.set_spawn(
            pygame.Vector2(_RoomTransition.ROOM_LIMIT_X + 40.0, 560.0),
        )
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        superficie = pygame.Surface((800, 600))

        with patch.object(
            sc._lectura_de_luz, "analizar_si_hace_falta",
        ) as espia_medir, patch.object(
            sc._lectura_de_luz, "dibujar_overlay",
        ) as espia_dibujar:
            sc.dibujar_ui(superficie)

        espia_medir.assert_not_called()
        espia_dibujar.assert_not_called()

    def test_dibujar_mundo_mide_y_aplica_el_overlay_por_su_cuenta(self) -> None:
        """Complemento del test anterior: `dibujar_mundo`, llamada SOLA
        (sin `dibujar_ui`), sí tiene que medir y aplicar el overlay -- es
        la responsable exclusiva ahora (AUD-646)."""
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _RoomTransition

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        sc._player.set_spawn(
            pygame.Vector2(_RoomTransition.ROOM_LIMIT_X + 40.0, 560.0),
        )
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        superficie = pygame.Surface((800, 600))

        sc.dibujar_mundo(superficie)

        assert sc._lectura_de_luz.luminancia_antes is not None
        assert sc._lectura_de_luz._overlay is not None


class TestUmbralLuminanciaSalaYCocina:
    """AUD-646 -- Regresión 1: subir `UMBRAL_LUMINANCIA` de 90 a 70 (y
    bajar `LUMINANCIA_OBJETIVO` de 115 a 90 en la misma proporción) no
    puede tocar el disparo real -- la sala sigue teniendo que activar el
    overlay, y la cocina (ya iluminada para trabajar, `valor=0.78` en el
    .tmx) nunca. Mide con `FilterTools.compute_histogram()` sobre el
    fotograma real, igual que `_LecturaDeLuz`, no con el `valor` crudo de
    `AmbientLightZone` que ya cubre `TestJerarquiaDeLuzDelNivel`."""

    @staticmethod
    def _luminancia_en(x: float, y: float) -> float:
        """Lee `sc._lectura_de_luz.luminancia_antes` -- la medición REAL
        que hace la propia escena dentro de `dibujar_mundo` (camino de
        producción, AUD-646) -- en vez de armar una `_LecturaDeLuz`
        aparte: una segunda instancia mediría sobre `superficie` DESPUÉS
        de que la escena ya haya horneado su propio overlay encima (ahora
        que `dibujar_mundo` lo aplica siempre que corresponda, ver el
        docstring de esa clase), inflando la lectura -- comprobado: sin
        este ajuste el punto cerca de la puerta media ~80 en vez de ~55.
        """
        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        sc._player.set_spawn(pygame.Vector2(x, y))
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        superficie = pygame.Surface((800, 600))
        sc.dibujar_mundo(superficie)
        assert sc._lectura_de_luz.luminancia_antes is not None
        return sc._lectura_de_luz.luminancia_antes

    def test_la_sala_mide_bajo_el_nuevo_umbral(self) -> None:
        """Cerca de la puerta (`ROOM_LIMIT_X + 40`, el punto donde de
        verdad se dispara la lectura al cruzar) y en el centro de la
        zona -- los dos puntos siguen midiendo oscuro bajo 70."""
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import (
            _LecturaDeLuz,
            _RoomTransition,
        )

        cerca_de_la_puerta = self._luminancia_en(
            _RoomTransition.ROOM_LIMIT_X + 40.0, 560.0,
        )
        centro_zona = self._luminancia_en(*_rect_tmx("AmbientLightZone_Sala").center)
        for etiqueta, luminancia in (
            ("cerca de la puerta", cerca_de_la_puerta),
            ("centro de la zona", centro_zona),
        ):
            assert luminancia < _LecturaDeLuz.UMBRAL_LUMINANCIA, (
                f"la sala real ({etiqueta}) debería seguir midiendo oscura "
                f"bajo el umbral nuevo (70), dio {luminancia:.2f}"
            )

    def test_la_cocina_mide_sobre_el_nuevo_umbral(self) -> None:
        """Centro de la zona y justo pasando el borde compartido con la
        sala (el punto más oscuro posible dentro de la cocina) -- ninguno
        de los dos debería disparar el overlay."""
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _LecturaDeLuz

        cocina_rect = _rect_tmx("AmbientLightZone_Cocina")
        centro_zona = self._luminancia_en(*cocina_rect.center)
        borde_con_sala = self._luminancia_en(cocina_rect.left + 70.0, 560.0)
        for etiqueta, luminancia in (
            ("centro de la zona", centro_zona),
            ("borde con la sala", borde_con_sala),
        ):
            assert luminancia >= _LecturaDeLuz.UMBRAL_LUMINANCIA, (
                f"la cocina real ({etiqueta}, valor=0.78 en el .tmx, ya "
                f"iluminada para trabajar) no debería disparar el "
                f"overlay -- midió {luminancia:.2f}, umbral 70"
            )


class TestFondoBorrosoDelObjetivo:
    """AUD-645 -- Unidad VII, ítem 2: `FilterTools.apply_kernel()` con el
    kernel `box_blur` real desenfoca el fondo del letrero de OBJETIVO
    (`_ObjetivoCocinero._fondo_para`, matriz en el README)."""

    @staticmethod
    def _fondo_de_mundo():
        superficie = pygame.Surface((800, 600))
        superficie.fill((80, 60, 40))
        return superficie

    def test_usa_el_kernel_box_blur_real_del_catalogo(self) -> None:
        from unittest.mock import patch

        import numpy as np

        from src.framework.processing.filter_tools import FilterTools
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ObjetivoCocinero

        objetivo = _ObjetivoCocinero()

        with patch.object(
            FilterTools, "apply_kernel", wraps=FilterTools.apply_kernel,
        ) as espia:
            resultado = objetivo._fondo_para(self._fondo_de_mundo(), x=100, ancho=200, alto=30)

        assert resultado is not None
        assert resultado.get_size() == (200, 30)
        espia.assert_called_once()
        _surface_arg, kernel_arg = espia.call_args[0]
        assert np.array_equal(kernel_arg, FilterTools.get_standard_kernel("box_blur")), (
            "el fondo del letrero de OBJETIVO debería usar el kernel "
            "box_blur precargado, no uno inventado a mano"
        )

    def test_se_cachea_por_tamaño_y_no_recalcula_la_convolucion(self) -> None:
        from unittest.mock import patch

        from src.framework.processing.filter_tools import FilterTools
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ObjetivoCocinero

        objetivo = _ObjetivoCocinero()
        mundo = self._fondo_de_mundo()

        with patch.object(
            FilterTools, "apply_kernel", wraps=FilterTools.apply_kernel,
        ) as espia:
            objetivo._fondo_para(mundo, x=100, ancho=200, alto=30)
            objetivo._fondo_para(mundo, x=100, ancho=200, alto=30)
            objetivo._fondo_para(mundo, x=100, ancho=200, alto=30)

        espia.assert_called_once()

    def test_un_tamaño_de_panel_distinto_vuelve_a_calcular(self) -> None:
        """El panel mide distinto con TEXTO_PENDIENTE que con
        TEXTO_CUMPLIDO -- la convolución vuelve a correr esa segunda vez
        (y sólo esa), nunca más de dos veces en toda la vida del letrero."""
        from unittest.mock import patch

        from src.framework.processing.filter_tools import FilterTools
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ObjetivoCocinero

        objetivo = _ObjetivoCocinero()
        mundo = self._fondo_de_mundo()

        with patch.object(
            FilterTools, "apply_kernel", wraps=FilterTools.apply_kernel,
        ) as espia:
            objetivo._fondo_para(mundo, x=100, ancho=200, alto=30)
            objetivo._fondo_para(mundo, x=90, ancho=260, alto=30)

        assert espia.call_count == 2

    def test_el_panel_real_del_letrero_trae_el_fondo_borroso_cacheado(self) -> None:
        """Integración: al cruzar a la cocina de verdad, el letrero de
        objetivo termina con un fondo borroso cacheado del tamaño del
        panel -- no un rectángulo de color plano."""
        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        sc._player.set_spawn(pygame.Vector2(2940.0, 560.0))
        for _ in range(20):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)

        superficie = pygame.Surface((800, 600))
        sc.draw(superficie)

        assert sc._objetivo_cocinero.fase != "oculto"
        assert sc._objetivo_cocinero._fondo_borroso is not None
        assert (
            sc._objetivo_cocinero._fondo_tam
            == sc._objetivo_cocinero._fondo_borroso.get_size()
        )


class TestContornoDeAlerta:
    """AUD-645 -- Unidad VII, ítem 3: `FilterTools.sobel_edge()` decide el
    contorno de alerta de un enemigo a punto de morir (`_ContornoDeAlerta`
    en `stage1_2_la_soda.py`)."""

    @staticmethod
    def _superficie_con_silueta():
        """24x28 con un rectángulo claro sobre fondo oscuro -- Sobel tiene
        que encontrar sus cuatro bordes sin ambigüedad."""
        s = pygame.Surface((24, 28))
        s.fill((10, 10, 10))
        pygame.draw.rect(s, (230, 230, 230), (4, 4, 16, 20))
        return s

    def test_una_silueta_real_produce_pixeles_de_borde_por_encima_del_minimo(
        self,
    ) -> None:
        import numpy as np

        from src.framework.processing.filter_tools import FilterTools
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ContornoDeAlerta

        bordes = FilterTools.sobel_edge(self._superficie_con_silueta())
        magnitud = pygame.surfarray.array3d(bordes)[:, :, 0]
        pixeles = int(np.count_nonzero(magnitud > _ContornoDeAlerta.UMBRAL_MAGNITUD))
        assert pixeles >= _ContornoDeAlerta.MIN_PIXELES_BORDE, (
            f"un rectángulo claro sobre fondo oscuro debería producir "
            f"bordes claros de sobra, dio {pixeles} píxeles"
        )

    def test_no_procesa_un_enemigo_por_encima_del_umbral_de_vida(self) -> None:
        from unittest.mock import patch

        from src.framework.processing.filter_tools import FilterTools
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ContornoDeAlerta

        sc = _construir_escena_la_soda()
        contorno = _ContornoDeAlerta()
        superficie = pygame.Surface((800, 600))
        sc._camera.offset.x = 0.0
        sc._camera.offset.y = 0.0

        with patch.object(
            FilterTools, "sobel_edge", wraps=FilterTools.sobel_edge,
        ) as espia:
            contorno.actualizar_y_dibujar(superficie, sc._stage_data, sc._camera.offset)

        espia.assert_not_called()
        assert contorno._cache == {}

    def test_un_enemigo_al_20pct_de_vida_dispara_sobel_y_cachea_una_sola_vez(
        self,
    ) -> None:
        """Usa un `_ContornoDeAlerta` propio (no `sc._contorno_alerta`) para
        poder espiar `FilterTools.sobel_edge` de forma aislada, pero contra
        una `surface` con el sprite real del enemigo ya dibujado --
        `sc.draw(superficie)` la puebla antes de que arranque el espía, así
        que lo que se mide es la silueta de verdad, no una superficie en
        blanco."""
        from unittest.mock import patch

        from src.framework.processing.filter_tools import FilterTools
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ContornoDeAlerta

        sc = _construir_escena_la_soda()
        enemigo = next(
            e for e in sc._stage_data.entity_list if isinstance(e, WalkerRaton)
        )
        enemigo.current_health = enemigo.max_health * 0.20
        superficie = pygame.Surface((800, 600))
        # Cámara centrada en el enemigo para que su recorte caiga entero
        # dentro de pantalla.
        sc._camera.offset.x = max(0.0, enemigo.rect.centerx - 400.0)
        sc._camera.offset.y = enemigo.rect.centery - 300.0
        sc.draw(superficie)  # puebla la superficie con el sprite real

        contorno = _ContornoDeAlerta()
        with patch.object(
            FilterTools, "sobel_edge", wraps=FilterTools.sobel_edge,
        ) as espia:
            contorno.actualizar_y_dibujar(superficie, sc._stage_data, sc._camera.offset)
            contorno.actualizar_y_dibujar(superficie, sc._stage_data, sc._camera.offset)
            contorno.actualizar_y_dibujar(superficie, sc._stage_data, sc._camera.offset)

        espia.assert_called_once()
        eid = id(enemigo)
        assert eid in contorno._cache
        contorno_surf, pixeles_borde, topleft = contorno._cache[eid]
        assert contorno_surf is not None
        assert topleft is not None
        assert pixeles_borde >= _ContornoDeAlerta.MIN_PIXELES_BORDE, (
            f"el sprite real del ratón (o su placeholder) debería producir "
            f"una silueta reconocible, dio {pixeles_borde} píxeles de borde"
        )

    def test_el_cache_se_limpia_cuando_el_enemigo_ya_no_califica(self) -> None:
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ContornoDeAlerta

        sc = _construir_escena_la_soda()
        enemigo = next(
            e for e in sc._stage_data.entity_list if isinstance(e, WalkerRaton)
        )
        enemigo.current_health = enemigo.max_health * 0.20
        contorno = _ContornoDeAlerta()
        superficie = pygame.Surface((800, 600))
        sc._camera.offset.x = max(0.0, enemigo.rect.centerx - 400.0)
        sc._camera.offset.y = enemigo.rect.centery - 300.0

        contorno.actualizar_y_dibujar(superficie, sc._stage_data, sc._camera.offset)
        assert id(enemigo) in contorno._cache

        enemigo.current_health = enemigo.max_health  # se curó por encima del umbral
        contorno.actualizar_y_dibujar(superficie, sc._stage_data, sc._camera.offset)
        assert id(enemigo) not in contorno._cache

    def test_contorno_de_alerta_real_dentro_de_dibujar_mundo(self) -> None:
        """Integración: `Stage1_2_LaSoda.dibujar_mundo` de verdad activa el
        contorno para un enemigo a ≤25% de vida dentro de cámara -- no un
        montaje aislado de `_ContornoDeAlerta`."""
        sc = _construir_escena_la_soda()
        enemigo = next(
            e for e in sc._stage_data.entity_list if isinstance(e, WalkerRaton)
        )
        enemigo.current_health = enemigo.max_health * 0.20
        sc._camera.offset.x = max(0.0, enemigo.rect.centerx - 400.0)
        sc._camera.offset.y = enemigo.rect.centery - 300.0

        superficie = pygame.Surface((800, 600))
        sc.draw(superficie)

        assert id(enemigo) in sc._contorno_alerta._cache
        contorno_surf, pixeles, _ = sc._contorno_alerta._cache[id(enemigo)]
        assert contorno_surf is not None
        assert pixeles >= sc._contorno_alerta.MIN_PIXELES_BORDE
        # AUD-646 -- ni siquiera el sprite propio del ratón, con su
        # detalle interno denso a 16x12, puede terminar ocupando más del
        # tope de área tras el umbral adaptativo (ver
        # test_umbral_adaptativo_recorta_un_sprite_denso_a_30pct_o_menos).
        assert sc._contorno_alerta.ultimo_porcentaje_area <= sc._contorno_alerta.AREA_MAXIMA_CONTORNO

    def test_recorta_el_sprite_propio_no_la_pantalla(self) -> None:
        """AUD-646 -- Regresión 2, diagnóstico: `_medir` (AUD-645) recortaba
        `surface.subsurface(entity.rect)` -- el fotograma YA dibujado. El
        rect de colisión del ratón (24x28) es más grande que su sprite
        real (16x12, `EnemyBase.draw()` lo centra y apoya abajo), así que
        ese recorte traía piso/pared de regalo alrededor del sprite. Ahora
        `_recorte_de_la_entidad` usa `entity._sprite_frames` -- el mismo
        frame que `EnemyBase.draw()` ya pintó -- así que el tamaño del
        recorte tiene que coincidir con el tamaño del SPRITE
        (`_sprite_fw`/`_sprite_fh`), no con el rect de colisión más
        grande."""
        sc = _construir_escena_la_soda()
        enemigo = next(
            e for e in sc._stage_data.entity_list if isinstance(e, WalkerRaton)
        )
        enemigo.current_health = enemigo.max_health * 0.20
        sc._camera.offset.x = max(0.0, enemigo.rect.centerx - 400.0)
        sc._camera.offset.y = enemigo.rect.centery - 300.0

        superficie = pygame.Surface((800, 600))
        sc.dibujar_mundo(superficie)

        anim_key = enemigo._get_animation_state()
        frame_esperado = enemigo._sprite_frames[anim_key][
            min(enemigo._animation_frame, len(enemigo._sprite_frames[anim_key]) - 1)
        ]
        contorno_surf, _, _ = sc._contorno_alerta._cache[id(enemigo)]
        assert contorno_surf is not None
        assert contorno_surf.get_size() == frame_esperado.get_size(), (
            f"el contorno debería medir lo mismo que el sprite propio del "
            f"ratón ({frame_esperado.get_size()}), no el rect de colisión "
            f"({enemigo.rect.size}) -- dio {contorno_surf.get_size()}"
        )
        assert contorno_surf.get_size() != enemigo.rect.size

    def test_actualizar_y_dibujar_no_pinta_fuera_del_sprite(self) -> None:
        """AUD-646 -- Regresión 2, causa raíz del "bloque sólido" que
        reportó el dueño: `actualizar_y_dibujar` (AUD-645) bliteaba con
        `special_flags=pygame.BLEND_RGBA_ADD`, que SUMA los canales R,G,B
        del origen al destino SIN pesarlos por alpha -- comprobado a
        mano: un píxel con alpha=0 sumaba exactamente el mismo color que
        uno con alpha=255. Con el color del recorte fijo en rojo/rosa y
        sólo el alpha variando, el resultado pintaba el recorte ENTERO,
        no un contorno. Un blit normal (ahora) sí respeta el alpha, y el
        recorte sale del sprite propio del enemigo (no de la pantalla) --
        entre las dos cosas, un punto lejos del enemigo (la esquina de la
        pantalla) tiene que quedar completamente intacto."""
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ContornoDeAlerta

        sc = _construir_escena_la_soda()
        enemigo = next(
            e for e in sc._stage_data.entity_list if isinstance(e, WalkerRaton)
        )
        enemigo.current_health = enemigo.max_health * 0.20
        sc._camera.offset.x = max(0.0, enemigo.rect.centerx - 400.0)
        sc._camera.offset.y = enemigo.rect.centery - 300.0

        superficie = pygame.Surface((800, 600))
        color_referencia = (12, 34, 56)
        superficie.fill(color_referencia)
        contorno = _ContornoDeAlerta()

        contorno.actualizar_y_dibujar(superficie, sc._stage_data, sc._camera.offset)

        assert superficie.get_at((0, 0))[:3] == color_referencia, (
            "el contorno de alerta no debería tocar píxeles lejos del "
            "sprite del enemigo -- si esto falla, algo volvió a pintar "
            "todo el recorte/pantalla del mismo color"
        )

    def test_umbral_adaptativo_recorta_un_sprite_denso_a_30pct_o_menos(self) -> None:
        """AUD-646 -- Regresión 2, causa 3: incluso aislado del fondo, el
        propio sprite del ratón (16x12) es denso -- `UMBRAL_MAGNITUD=40`
        solo deja más de la mitad del recorte "opaco" (medido: 103/192 =
        53.6%). `_umbral_adaptativo` tiene que subir el umbral hasta bajar
        eso a `AREA_MAXIMA_CONTORNO` (30%) o menos."""
        import numpy as np

        from src.framework.processing.filter_tools import FilterTools
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ContornoDeAlerta

        sc = _construir_escena_la_soda()
        enemigo = next(
            e for e in sc._stage_data.entity_list if isinstance(e, WalkerRaton)
        )
        anim_key = enemigo._get_animation_state()
        frame = enemigo._sprite_frames[anim_key][
            min(enemigo._animation_frame, len(enemigo._sprite_frames[anim_key]) - 1)
        ]
        negro = _ContornoDeAlerta._componer_sobre_negro(frame)
        bordes = FilterTools.sobel_edge(negro)
        magnitud = pygame.surfarray.array3d(bordes)[:, :, 0]

        pixeles_umbral_base = int(
            np.count_nonzero(magnitud > _ContornoDeAlerta.UMBRAL_MAGNITUD),
        )
        assert pixeles_umbral_base / magnitud.size > _ContornoDeAlerta.AREA_DISPARA_ADAPTATIVO, (
            "este test asume que el sprite del ratón es denso a UMBRAL_"
            f"MAGNITUD -- dio {pixeles_umbral_base}/{magnitud.size}, "
            "ajustar la premisa si el sprite cambió"
        )

        umbral, pixeles_borde, porcentaje = _ContornoDeAlerta._umbral_adaptativo(magnitud)

        assert umbral > _ContornoDeAlerta.UMBRAL_MAGNITUD, (
            "el umbral debería haber subido -- el base deja más del 50% "
            "del recorte opaco"
        )
        assert porcentaje <= _ContornoDeAlerta.AREA_MAXIMA_CONTORNO, (
            f"tras subir el umbral, el contorno debería ocupar "
            f"{_ContornoDeAlerta.AREA_MAXIMA_CONTORNO*100:.0f}% o menos "
            f"del recorte, dio {porcentaje*100:.1f}%"
        )
        assert pixeles_borde >= _ContornoDeAlerta.MIN_PIXELES_BORDE

    def test_superficie_sintetica_alpha_solo_en_el_borde_interior_en_cero(
        self,
    ) -> None:
        """AUD-646 -- pipeline completo (componer sobre negro + Sobel +
        umbral adaptativo) sobre un caso sintético controlado: un cuadrado
        opaco 16x16 sobre fondo TRANSPARENTE en un frame de 24x24. El
        interior del cuadrado es una región plana sin gradiente -- tiene
        que dar magnitud 0 (por lo tanto alpha=0 en el contorno real), y
        el área total del contorno no puede superar el tope."""
        from src.framework.processing.filter_tools import FilterTools
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ContornoDeAlerta

        frame = pygame.Surface((24, 24), pygame.SRCALPHA)
        frame.fill((0, 0, 0, 0))
        pygame.draw.rect(frame, (230, 230, 230, 255), (4, 4, 16, 16))

        negro = _ContornoDeAlerta._componer_sobre_negro(frame)
        bordes = FilterTools.sobel_edge(negro)
        magnitud = pygame.surfarray.array3d(bordes)[:, :, 0]
        umbral, pixeles_borde, porcentaje = _ContornoDeAlerta._umbral_adaptativo(magnitud)

        assert pixeles_borde >= _ContornoDeAlerta.MIN_PIXELES_BORDE
        assert porcentaje <= _ContornoDeAlerta.AREA_MAXIMA_CONTORNO, (
            f"el contorno de un cuadrado sintético no debería ocupar más "
            f"del {_ContornoDeAlerta.AREA_MAXIMA_CONTORNO*100:.0f}% del "
            f"recorte, dio {porcentaje*100:.1f}%"
        )
        # El interior del cuadrado -- varios píxeles adentro de cualquier
        # borde -- es plano: sin gradiente, por lo tanto sin alpha en el
        # contorno resultante (alpha_view sólo se llena donde magnitud
        # supera el umbral, ver _medir).
        interior = magnitud[9:15, 9:15]
        assert int(interior.max()) == 0, (
            f"el interior del cuadrado sintético debería medir magnitud "
            f"0 (sin bordes), el máximo del recorte interior dio "
            f"{interior.max()}"
        )
        assert bool((interior <= umbral).all())


# ──────────────────────────────────────────────────────────────────────────
# AUD-647 — el minimapa cuadrado por defecto del HUD (AUD-560/AUD-499,
# 44x44 de maqueta) comprime La Soda (3456x608 px, proporción 5.7:1) en una
# tira de ~19 px pegada al borde superior del recuadro, con el resto vacío
# ("se ve como una parte de arriba y tanto vacío", captura del dueño).
# `Stage1_2_LaSoda._ajustar_minimapa_al_nivel` reemplaza ese recuadro por
# uno con la proporción real del nivel, a la derecha del cronómetro.
# ──────────────────────────────────────────────────────────────────────────


class TestMinimapaProporcional:
    """AUD-647 — el minimapa de La Soda usa un recuadro con la proporción
    real del nivel (200 px de ancho, alto proporcional a 3456x608), no el
    cuadrado 110x110 por defecto del HUD general."""

    def _proporcion_del_mapa(self, sc) -> float:
        map_w, map_h = sc._stage_data.map_pixel_size
        return map_w / map_h

    def test_proporcion_del_recuadro_dentro_del_10_por_ciento_del_mapa(self) -> None:
        sc = _construir_escena_la_soda()
        proporcion_mapa = self._proporcion_del_mapa(sc)
        proporcion_recuadro = sc._minimap._minimap_w / sc._minimap._minimap_h
        diferencia = abs(proporcion_recuadro - proporcion_mapa) / proporcion_mapa
        assert diferencia <= 0.10, (
            f"proporción del recuadro ({proporcion_recuadro:.2f}) se aleja "
            f"más del 10% de la proporción real del mapa "
            f"({proporcion_mapa:.2f})"
        )

    def test_no_colisiona_con_el_cronometro_ni_otras_regiones_del_hud(self) -> None:
        sc = _construir_escena_la_soda()
        rect_minimapa = pygame.Rect(
            sc._minimap._minimap_x, sc._minimap._minimap_y,
            sc._minimap._minimap_w, sc._minimap._minimap_h,
        )
        regiones = sc._hud.regiones()
        assert rect_minimapa.colliderect(regiones["cronometro"]) is False, (
            "el minimapa reubicado se solapa con el cronómetro"
        )
        for nombre, rect in regiones.items():
            if nombre == "minimapa":
                continue
            assert rect_minimapa.colliderect(rect) is False, (
                f"el minimapa reubicado se solapa con la región "
                f"'{nombre}' del HUD"
            )

    def test_la_escala_llena_al_menos_90_por_ciento_de_ancho_y_alto(self) -> None:
        sc = _construir_escena_la_soda()
        map_w, map_h = sc._stage_data.map_pixel_size
        minimapa = sc._minimap
        assert minimapa._scale * map_w >= 0.9 * minimapa._minimap_w, (
            "el nivel no llena al menos el 90% del ancho del recuadro"
        )
        assert minimapa._scale * map_h >= 0.9 * minimapa._minimap_h, (
            "el nivel no llena al menos el 90% del alto del recuadro"
        )

    def test_se_reaplica_tras_un_respawn(self) -> None:
        """`respawn()` vuelve a llamar `on_enter()` (`StageScene.respawn()`),
        que reconstruye `_hud`/`_minimap` desde cero: el recuadro
        proporcional tiene que reaplicarse solo, no perderse tras morir."""
        sc = _construir_escena_la_soda()
        antes = (
            sc._minimap._minimap_x, sc._minimap._minimap_y,
            sc._minimap._minimap_w, sc._minimap._minimap_h,
        )

        sc.respawn()

        despues = (
            sc._minimap._minimap_x, sc._minimap._minimap_y,
            sc._minimap._minimap_w, sc._minimap._minimap_h,
        )
        assert despues == antes, (
            "el recuadro del minimapa cambió tras un respawn -- debería "
            "reaplicarse idéntico"
        )
        map_w, map_h = sc._stage_data.map_pixel_size
        assert sc._minimap._scale * map_w >= 0.9 * sc._minimap._minimap_w
        assert sc._minimap._scale * map_h >= 0.9 * sc._minimap._minimap_h


# ──────────────────────────────────────────────────────────────────────────
# AUD-650 — barra de jefe del cocinero (`_BarraDeJefe`) y sacudida de
# cámara (`_SacudidaDeCamara`), las dos en `stage1_2_la_soda.py`. La barra
# sigue `current_health`/`max_health` LEÍDOS de la instancia del
# `ShooterCocinero` en cada fotograma -- nunca asume que la vida máxima es
# 3 (`_CocineroFalso` de abajo arranca en 5.0 a propósito, un valor
# distinto del legado, justo para probar eso). La sacudida es una fachada
# sobre `Camera.apply_shake` (AUD-282/AUD-398, ya en el motor) -- ver el
# docstring de `_SacudidaDeCamara` para por qué no hay un sistema de
# sacudida escrito a mano acá.
# ──────────────────────────────────────────────────────────────────────────


def _camara_con_objetivo():
    """Una `Camera` real, siguiendo un objetivo mínimo -- `Camera.update()`
    corta sin `_target` (`camera.py:339-340`), así que hace falta uno para
    poder probar `apply_shake`/`_aplicar_sacudida` de verdad."""
    from src.framework.stage.camera import Camera

    class _ObjetivoFalso:
        def __init__(self) -> None:
            self.rect = pygame.Rect(400, 300, 16, 16)
            self.velocity = pygame.Vector2(0.0, 0.0)

    camara = Camera()
    camara.set_map_size(4000, 4000)
    camara.follow(_ObjetivoFalso())
    camara.snap_to_target()
    return camara


class TestBarraDeJefeYSacudida:
    """AUD-650 -- `_BarraDeJefe` (barra de vida del jefe con daño diferido,
    entrada/salida con easing) y `_SacudidaDeCamara` (fachada sobre
    `Camera.apply_shake`)."""

    class _CocineroFalso:
        """Doble mínimo -- sólo los tres atributos que `_BarraDeJefe` lee
        (`is_alive`/`current_health`/`max_health`), sin cargar el .tmx ni
        construir un `ShooterCocinero` real. Arranca con `max_health=5.0`
        a propósito (distinto del valor legado, 3.0) para probar que
        `_BarraDeJefe` de verdad lo lee de la instancia y no asume 3."""

        def __init__(self, max_health: float = 5.0) -> None:
            self.max_health = max_health
            self.current_health = max_health
            self.is_alive = True

    @staticmethod
    def _x_cocina():
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _ObjetivoCocinero

        return _ObjetivoCocinero.X_ENTRADA_COCINA

    def _dentro(self) -> float:
        return self._x_cocina() + 20.0

    def _fuera(self) -> float:
        return self._x_cocina() - 20.0

    # -- visibilidad: sólo en la cocina, con el cocinero vivo -----------

    def test_invisible_fuera_de_la_cocina_visible_adentro_con_el_cocinero_vivo(
        self,
    ) -> None:
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _BarraDeJefe

        barra = _BarraDeJefe()
        cocinero = self._CocineroFalso()

        barra.update(1 / 60, self._fuera(), cocinero, False)
        assert barra.fase == "oculto"
        assert barra.visible is False

        barra.update(1 / 60, self._dentro(), cocinero, False)
        assert barra.fase == "apareciendo"
        assert barra.visible is True

    def test_sin_cocinero_o_ya_muerto_queda_oculta(self) -> None:
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _BarraDeJefe

        barra = _BarraDeJefe()
        barra.update(1 / 60, self._dentro(), None, False)
        assert barra.fase == "oculto"

        cocinero = self._CocineroFalso()
        cocinero.is_alive = False
        barra.update(1 / 60, self._dentro(), cocinero, False)
        assert barra.fase == "oculto"

    def test_salir_de_la_cocina_la_oculta_de_nuevo(self) -> None:
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _BarraDeJefe

        barra = _BarraDeJefe()
        cocinero = self._CocineroFalso()
        for _ in range(40):
            barra.update(1 / 60, self._dentro(), cocinero, False)
        assert barra.visible is True

        barra.update(1 / 60, self._fuera(), cocinero, False)
        assert barra.fase == "oculto"
        assert barra.visible is False

    # -- entrada: 0 -> vida actual en 0.6s con ease_out_cubic ------------

    def test_la_entrada_llena_de_0_a_la_vida_actual_en_0_6s_con_ease_out_cubic(
        self,
    ) -> None:
        from src.engine.utils.math_utils import ease_out_cubic
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _BarraDeJefe

        barra = _BarraDeJefe()
        cocinero = self._CocineroFalso()

        barra.update(0.0, self._dentro(), cocinero, False)
        assert barra.fase == "apareciendo"
        assert barra.fraccion_visible == pytest.approx(0.0, abs=1e-6)

        barra.update(0.3, self._dentro(), cocinero, False)
        t = 0.3 / _BarraDeJefe.DURACION_ENTRADA
        assert barra.fraccion_visible == pytest.approx(
            1.0 * ease_out_cubic(t), abs=1e-6,
        )
        assert barra.fase == "apareciendo"

        barra.update(_BarraDeJefe.DURACION_ENTRADA, self._dentro(), cocinero, False)
        assert barra.fase == "visible"
        assert barra.fraccion_visible == pytest.approx(1.0, abs=1e-6)

    def test_reaparecer_tras_salir_de_la_cocina_no_repite_la_entrada(self) -> None:
        """"La primera vez que aparece" -- una segunda entrada a la
        cocina en la misma vida de la escena no vuelve a animar el
        llenado desde 0."""
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _BarraDeJefe

        barra = _BarraDeJefe()
        cocinero = self._CocineroFalso()
        for _ in range(40):
            barra.update(1 / 60, self._dentro(), cocinero, False)
        assert barra.fase == "visible"

        barra.update(1 / 60, self._fuera(), cocinero, False)
        assert barra.fase == "oculto"

        barra.update(1 / 60, self._dentro(), cocinero, False)
        assert barra.fase == "visible", (
            f"debería reaparecer directo en 'visible', sin pasar por "
            f"'apareciendo' de nuevo: fase={barra.fase!r}"
        )
        assert barra.fraccion_visible == pytest.approx(1.0, abs=1e-6)

    # -- fracción real, sin asumir max_health=3 --------------------------

    def test_la_fraccion_es_vida_actual_sobre_vida_maxima_tras_un_golpe(self) -> None:
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _BarraDeJefe

        barra = _BarraDeJefe()
        cocinero = self._CocineroFalso(max_health=5.0)
        for _ in range(40):
            barra.update(1 / 60, self._dentro(), cocinero, False)

        cocinero.current_health = 3.0
        barra.update(1 / 60, self._dentro(), cocinero, True)
        assert barra._fraccion_actual == pytest.approx(3.0 / 5.0)
        assert barra.fraccion_visible == pytest.approx(3.0 / 5.0)

    # -- daño diferido: hold de 0.25s y retracción con ease_out_quad ----

    def test_el_tramo_diferido_se_retrae_con_ease_out_quad(self) -> None:
        from src.engine.utils.math_utils import ease_out_quad
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _BarraDeJefe

        barra = _BarraDeJefe()
        cocinero = self._CocineroFalso(max_health=5.0)
        for _ in range(40):
            barra.update(1 / 60, self._dentro(), cocinero, False)
        assert barra.fraccion_diferida == pytest.approx(1.0)

        cocinero.current_health = 4.0  # 5.0 -> 4.0, fracción real 0.8
        barra.update(1 / 60, self._dentro(), cocinero, True)
        # Dentro de la demora (0.25s): el fantasma se queda clavado en 1.0
        assert barra.fraccion_diferida == pytest.approx(1.0, abs=1e-6)

        # Agota la demora EXACTA en su propio update() -- update() reparte
        # un `dt` que cruce el límite entre demora y retracción dentro de
        # la misma llamada (ver el comentario de esa rama en
        # stage1_2_la_soda.py), así que agotar la demora en un paso propio
        # deja el siguiente paso íntegro para la retracción, sin mezclar
        # los dos en la cuenta de `t1` de abajo.
        barra.update(_BarraDeJefe.DEMORA_DIFERIDA, self._dentro(), cocinero, False)
        assert barra.fraccion_diferida == pytest.approx(1.0, abs=1e-6)

        barra.update(0.10, self._dentro(), cocinero, False)
        t1 = 0.10 / _BarraDeJefe.DURACION_RETRACCION
        esperado1 = 1.0 + (0.8 - 1.0) * ease_out_quad(t1)
        muestra1 = barra.fraccion_diferida
        assert muestra1 == pytest.approx(esperado1, abs=1e-3)

        barra.update(0.10, self._dentro(), cocinero, False)
        muestra2 = barra.fraccion_diferida
        assert muestra2 < muestra1, (
            "el tramo diferido tiene que seguir retrayéndose entre las "
            "dos muestras"
        )
        assert muestra2 >= 0.8 - 1e-6

        barra.update(_BarraDeJefe.DURACION_RETRACCION, self._dentro(), cocinero, False)
        assert barra.fraccion_diferida == pytest.approx(0.8, abs=1e-6)

    def test_un_segundo_golpe_a_mitad_de_retraccion_no_salta_hacia_atras(self) -> None:
        """Un golpe nuevo mientras el fantasma ya se está retrayendo lo
        congela donde esté en ese instante, no lo repone al 100%."""
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _BarraDeJefe

        barra = _BarraDeJefe()
        cocinero = self._CocineroFalso(max_health=5.0)
        for _ in range(40):
            barra.update(1 / 60, self._dentro(), cocinero, False)

        cocinero.current_health = 4.0
        barra.update(1 / 60, self._dentro(), cocinero, True)
        barra.update(_BarraDeJefe.DEMORA_DIFERIDA + 0.15, self._dentro(), cocinero, False)
        fantasma_a_mitad_de_camino = barra.fraccion_diferida
        assert fantasma_a_mitad_de_camino < 1.0

        cocinero.current_health = 2.0
        barra.update(1 / 60, self._dentro(), cocinero, True)
        assert barra.fraccion_diferida == pytest.approx(
            fantasma_a_mitad_de_camino, abs=1e-6,
        ), (
            "el segundo golpe tiene que arrancar la nueva retracción "
            "desde donde estaba el fantasma, no desde 1.0"
        )

    # -- muerte: vaciado + desvanecido con ease_out_cubic ----------------

    def test_al_morir_se_desvanece_y_a_los_0_6s_ya_no_se_dibuja(self) -> None:
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _BarraDeJefe

        barra = _BarraDeJefe()
        cocinero = self._CocineroFalso()
        for _ in range(40):
            barra.update(1 / 60, self._dentro(), cocinero, False)
        assert barra.visible is True

        barra.marcar_muerte()
        assert barra.fase == "muriendo"

        barra.update(_BarraDeJefe.DURACION_MUERTE / 2, self._dentro(), cocinero, False)
        assert 0.0 < barra.alpha < 255
        assert 0.0 < barra.fraccion_visible < 1.0

        barra.update(0.6, self._dentro(), cocinero, False)
        assert barra.fase == "terminado"
        assert barra.visible is False
        assert barra.alpha == 0

        # No vuelve a aparecer aunque el jugador siga en la cocina y el
        # doble siga marcado como vivo -- sólo una `_BarraDeJefe` nueva
        # (la que arma `on_stage_start()` en cada respawn) la reactiva.
        barra.update(1 / 60, self._dentro(), cocinero, False)
        assert barra.fase == "terminado"

    # -- sacudida de cámara -----------------------------------------------

    def test_sacudida_decae_a_0_en_su_duracion_y_no_deja_offset_neto(self) -> None:
        """Dos afirmaciones distintas, medidas por separado:

        1. La AMPLITUD de la sacudida decae a 0 exactamente en su
           duración (`Camera._shake_amplitude`/`_shake_timer`) -- eso es
           lo que `Camera.apply_shake`/`_aplicar_sacudida` garantizan por
           contrato (`camera.py:443-472`).
        2. El OFFSET neto vuelve a la base del LERP-follow -- pero no
           instantáneo: `Camera.update()` calcula el error de LERP con
           el offset TAL COMO QUEDÓ el fotograma anterior (shake
           incluido, `camera.py:394-395`) antes de que `_aplicar_
           sacudida` lo retire ese mismo fotograma -- así que mientras
           la sacudida está activa, el LERP la persigue un poco cada
           fotograma. Medido (`Claude - Uso General/playtest/` -- ver el
           reporte del AUD): con `lerp_speed=8.0` por defecto eso deja
           un remanente sub-píxel que el propio LERP termina de corregir
           por convergencia geométrica en ~1-2s después, NO un offset
           que quede pegado ahí para siempre. 150 fotogramas (2.5s) le
           sobra margen de sobra a esa convergencia.
        """
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _SacudidaDeCamara

        camara = _camara_con_objetivo()
        offset_base = pygame.Vector2(camara.offset)

        # Con dirección -- la misma rama que de verdad usa
        # `_SacudidaDeCamara._disparar` (ver su docstring: SIN
        # dirección la sacudida del motor es ruido isótropo de
        # amplitud CONSTANTE, sin decaer, hasta un corte abrupto).
        camara.apply_shake(
            _SacudidaDeCamara.AMPLITUD_MUERTE, _SacudidaDeCamara.DURACION_MUERTE,
            pygame.Vector2(1.0, 0.0),
        )
        dt = 1 / 60
        # +3, no +1: el fotograma exacto en que `_shake_timer` cruza a
        # <=0 depende del residuo de punto flotante de `dt` acumulado
        # (medido: con `duracion=0.35` y `dt=1/60`, `_shake_amplitude`
        # sigue en 6.0 todavía en el fotograma 22 y recién baja a 0.0 en
        # el 23 -- un margen de +1 no alcanza).
        pasos_duracion = math.ceil(_SacudidaDeCamara.DURACION_MUERTE / dt) + 3
        hubo_desplazamiento = False
        for _ in range(pasos_duracion):
            camara.update(dt)
            if camara.offset != offset_base:
                hubo_desplazamiento = True
        assert hubo_desplazamiento, "la sacudida nunca desplazó la cámara"
        assert camara._shake_amplitude == 0.0, (
            "la amplitud debería decaer a 0 exactamente en su duración"
        )
        assert camara._shake_offset == pygame.Vector2(0.0, 0.0)

        for _ in range(150 - pasos_duracion):
            camara.update(dt)
        assert camara.offset.x == pytest.approx(offset_base.x, abs=1e-4), (
            f"el offset neto de la sacudida debería volver a la base del "
            f"LERP-follow: quedó en {camara.offset}, esperado {offset_base}"
        )
        assert camara.offset.y == pytest.approx(offset_base.y, abs=1e-4)

    def test_sacudida_dispara_camera_apply_shake_con_los_valores_de_cada_gatillo(
        self,
    ) -> None:
        """`_SacudidaDeCamara` en aislado, contra una cámara espía —
        confirma que `golpe()`/`apertura_de_puerta()`/`muerte_del_
        cocinero()` llaman a `Camera.apply_shake` con exactamente las
        constantes declaradas, sin depender de la escena completa.

        No se espía `Camera.apply_shake` de una escena real: el motor
        YA suscribe su propio shake genérico a `Events.SFX_ENEMY_HIT`
        (`stage_parts/senales.py:212`, `self._camera.apply_shake(
        amplitude=1.5, duration=0.06)`, disparado por CUALQUIER golpe a
        CUALQUIER enemigo) — parchear el método en una escena real
        interceptaría también esa llamada del motor, que no es lo que
        esta prueba quiere medir."""
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import _SacudidaDeCamara

        class _CamaraEspia:
            def __init__(self) -> None:
                self.llamadas: list[tuple[float, float]] = []

            def apply_shake(
                self, amplitude: float = 2.0, duration: float = 0.1, direccion=None,
            ) -> None:
                self.llamadas.append((amplitude, duration))

        class _StageFalso:
            def __init__(self, camara) -> None:
                self._camera = camara

        camara = _CamaraEspia()
        sacudida = _SacudidaDeCamara(_StageFalso(camara))

        sacudida.golpe()
        assert camara.llamadas[-1] == (
            _SacudidaDeCamara.AMPLITUD_GOLPE, _SacudidaDeCamara.DURACION_GOLPE,
        )

        sacudida.apertura_de_puerta()
        assert camara.llamadas[-1] == (
            _SacudidaDeCamara.AMPLITUD_PUERTA, _SacudidaDeCamara.DURACION_PUERTA,
        )

        sacudida.muerte_del_cocinero()
        assert camara.llamadas[-1] == (
            _SacudidaDeCamara.AMPLITUD_MUERTE, _SacudidaDeCamara.DURACION_MUERTE,
        )

        assert len(camara.llamadas) == 3

    def test_los_tres_disparadores_de_juego_llaman_a_sacudida_camara(self) -> None:
        """Integración con la escena real: `Stage1_2_LaSoda.update()`
        (el golpe) y `_PuertaDelCocinero._on_enemy_died` (muerte +
        apertura de puerta) de verdad invocan `_sacudida_camara` en los
        tres momentos -- espiando `sc._sacudida_camara` en vez de
        `Camera.apply_shake` para no chocar con el shake genérico del
        motor (ver el docstring de la prueba de arriba)."""

        class _EspiaSacudida:
            def __init__(self) -> None:
                self.golpes = 0
                self.aperturas = 0
                self.muertes = 0

            def golpe(self) -> None:
                self.golpes += 1

            def apertura_de_puerta(self) -> None:
                self.aperturas += 1

            def muerte_del_cocinero(self) -> None:
                self.muertes += 1

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        espia = _EspiaSacudida()
        sc._sacudida_camara = espia
        # Un fotograma de línea base ANTES del golpe: _detectar_golpe_al_
        # cocinero necesita un muestreo previo de current_health para que
        # el golpe cuente como tal (ver el docstring de ese método).
        sc.context.event_bus.dispatch()
        sc.update(1 / 60)
        assert espia.golpes == 0 and espia.muertes == 0 and espia.aperturas == 0

        cocinero = next(
            e for e in sc._stage_data.entity_list if isinstance(e, ShooterCocinero)
        )

        # (c) golpe que conecta, no letal.
        cocinero.apply_hit(1.0, (cocinero.rect.centerx - 40.0, cocinero.rect.centery))
        sc.context.event_bus.dispatch()
        sc.update(1 / 60)
        assert espia.golpes == 1, "el golpe no letal no disparó la sacudida de golpe"
        assert espia.muertes == 0 and espia.aperturas == 0

        # El primer golpe deja al cocinero invencible por
        # `_invincibility_duration` (0.5s por defecto, `enemy_base.py:96`)
        # -- hay que dejarla vencer o el segundo `apply_hit` es un no-op
        # silencioso (`enemy_base.py:507-508`) y nunca muere.
        for _ in range(40):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        espia.golpes = 0  # el muestreo de vida no debería marcar más golpes en reposo

        # (a)+(b) muerte del cocinero y apertura de la puerta trasera --
        # en este nivel las dos las dispara el mismo ENEMY_DIED (ver el
        # docstring de _SacudidaDeCamara).
        cocinero.apply_hit(10.0, (0.0, 0.0))
        sc.context.event_bus.dispatch()
        sc.update(1 / 60)
        assert espia.muertes == 1, "la muerte del cocinero no disparó su sacudida"
        assert espia.aperturas == 1, "la apertura de la puerta no disparó su sacudida"

    # -- integración con la escena real: colisiones y respawn -----------

    def test_la_barra_no_pisa_hud_letrero_ni_messagebox(self) -> None:
        """AUD-650 -- compara contra los rects REALES de dibujo, no contra
        el rect de diseño.

        `MessageBox.caja_rect()` (`message_box.py:157-173`) siempre
        devuelve `Rect(0, 160, 800, 140)`, visible o no: es la banda que
        el layout RESERVA como máximo, no lo que `MessageBox.draw()`
        pinta. `draw()` (`message_box.py:194-216`) en realidad blitea
        `rect_del_panel()` (`message_box.py:175-192`) -- angosto,
        centrado, del alto exacto del texto envuelto, con la `y` SIEMPRE
        igual a `caja_rect().y=160` (constante, no depende del contenido
        ni de la visibilidad; sólo la ALTURA crece hacia abajo con más
        líneas). Contra `caja_rect()` la barra "chocaba" con cualquier
        `Y_BARRA` cercano al letrero aunque nunca hubiera un solo píxel
        de `MessageBox` en pantalla -- de ahí que el intento anterior
        (AUD-650 original) la mandara a `Y_BARRA=320`, a media pantalla.
        Medido y documentado en el docstring de `_BarraDeJefe`.
        """
        from src.engine.core import settings as _settings
        from src.engine.core.events import Events
        from src.engine.ui.theme import Theme as _Theme
        from src.engine.ui.theme import font as _fuente
        from src.stages.stage1_2_la_soda.stage1_2_la_soda import (
            _BarraDeJefe,
            _ObjetivoCocinero,
        )

        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        sc._player.set_spawn(pygame.Vector2(2950.0, 560.0))
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        assert sc._barra_jefe.visible is True, (
            "el montaje debería dejar la barra visible para que la "
            "prueba de colisión tenga algo real que medir"
        )

        # AUD-650 -- tope explícito: si esto vuelve a subir, la barra
        # vuelve a caer a media pantalla como con `Y_BARRA=320`.
        assert _BarraDeJefe.Y_BARRA <= 152, (
            f"Y_BARRA={_BarraDeJefe.Y_BARRA} se fue de la franja superior "
            "(debe quedar por debajo del letrero y por encima -o tocando- "
            "el panel real de MessageBox, nunca a media pantalla)"
        )

        rect_barra = sc._barra_jefe.rect_total()

        for nombre, rect in sc._hud.regiones().items():
            assert not rect_barra.colliderect(rect), (
                f"la barra de jefe ({rect_barra}) se solapa con la "
                f"región '{nombre}' del HUD ({rect})"
            )

        alto_letrero = _fuente(_Theme.FONT_SMALL).get_height() + 2 * 6
        rect_letrero = pygame.Rect(
            0, _ObjetivoCocinero.Y_DESTINO, _settings.INTERNAL_WIDTH, alto_letrero,
        )
        assert not rect_barra.colliderect(rect_letrero), (
            f"la barra de jefe ({rect_barra}) se solapa con el letrero "
            f"de objetivo ({rect_letrero})"
        )

        # -- MessageBox: contra el rect REAL, no contra caja_rect() ----
        # Con el mensaje oculto `draw()` no pinta nada (sale temprano en
        # `not self._visible or not self._text`), así que no hay nada
        # con qué chocar todavía. Se fuerza el cartel real de la cocina
        # (MSG_04_Cocina) por el mismo camino que usa el juego de verdad
        # (`hazard_system.py:110`, `Events.SHOW_MESSAGE`) para medir el
        # caso que de verdad importa: la barra y el MessageBox visibles
        # al mismo tiempo.
        cartel_cocina = next(
            mt for mt in sc._stage_data.message_triggers
            if 3008 <= mt.rect.x < 3072
        )
        sc.context.event_bus.emit(
            Events.SHOW_MESSAGE, text=cartel_cocina.text, duration=8.0,
        )
        sc.context.event_bus.dispatch()
        sc.update(1 / 60)
        assert sc._msg_box.is_visible is True, (
            "el montaje no dejó el MessageBox visible -- la prueba de "
            "colisión contra el rect real necesita que esté mostrando algo"
        )
        rect_msg_real = sc._msg_box.rect_del_panel()
        assert not rect_barra.colliderect(rect_msg_real), (
            f"la barra de jefe ({rect_barra}) se solapa con el panel REAL "
            f"del MessageBox ({rect_msg_real}) -- caja_rect() "
            f"({sc._msg_box.caja_rect()}) es la banda de diseño, no lo "
            f"que de verdad se dibuja"
        )

    def test_tras_respawn_la_barra_se_resetea(self) -> None:
        sc = _construir_escena_la_soda()
        sc._room_transition.disarm_to_interior()
        sc._player.set_spawn(pygame.Vector2(2950.0, 560.0))
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        assert sc._barra_jefe.visible is True

        _matar_al_cocinero(sc)
        for _ in range(int(0.6 * 60)):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        assert sc._barra_jefe.fase == "terminado"

        sc._player.set_spawn(pygame.Vector2(sc._stage_data.spawn_point))
        sc.update(1 / 60)
        sc.respawn()

        assert sc._barra_jefe.fase == "oculto", (
            "tras el respawn la barra tiene que resetearse -- el "
            "cocinero repuesto vuelve a estar vivo"
        )

        sc._player.set_spawn(pygame.Vector2(2950.0, 560.0))
        for _ in range(10):
            sc.context.event_bus.dispatch()
            sc.update(1 / 60)
        assert sc._barra_jefe.visible is True, (
            "tras el respawn, entrar de nuevo a la cocina con el "
            "cocinero repuesto (vivo) tiene que volver a mostrar la barra"
        )


class TestMapaAutocontenido:
    """AUD-655 — el mapa no depende de ningún asset compartido del motor.

    `tileset_cafeteria` era el único tileset del `.tmx` que apuntaba fuera
    de esta carpeta (`../../tilesets/tileset_cafeteria.png`, 128x128, el PNG
    compartido del profesor). En `origin/feature/master-plan` ese mismo PNG
    pasa a 256x256 (16 columnas en vez de 8): si el profesor corre este
    nivel parado en esa rama, los gids 1-64 (`firstgid=1`, `columns=8`) se
    releen contra una hoja con el doble de columnas y la sala/cocina salen
    con los tiles equivocados -- el mapa sigue siendo válido XML, solo que
    dibuja mal. La corrección copia el PNG byte a byte a
    `tileset_cafeteria_soda.png`, dentro de esta misma carpeta, y el `.tmx`
    apunta ahí en vez de a `../../tilesets/`.

    Antes de AUD-655 esta clase falla en `test_ningun_tileset_sale_de_la_carpeta_del_nivel`
    (el `source` de `tileset_cafeteria` es `../../tilesets/tileset_cafeteria.png`);
    después, pasa completa.
    """

    def _tilesets_del_tmx(self) -> list[ET.Element]:
        arbol = ET.parse(TMX)
        return list(arbol.getroot().findall("tileset"))

    def test_ningun_tileset_sale_de_la_carpeta_del_nivel(self) -> None:
        carpeta_nivel = TMX.parent
        fuera_de_carpeta = []
        for tileset in self._tilesets_del_tmx():
            imagen = tileset.find("image")
            assert imagen is not None, (
                f"tileset {tileset.get('name')!r} sin <image>"
            )
            source = imagen.get("source", "")
            # Un source relativo que no vive dentro de `carpeta_nivel` sube
            # de nivel con "..": ../../tilesets/tileset_cafeteria.png es
            # exactamente ese caso -- el que rompe con master-plan.
            resuelto = (carpeta_nivel / source).resolve()
            if carpeta_nivel.resolve() not in resuelto.parents and resuelto != carpeta_nivel.resolve():
                fuera_de_carpeta.append((tileset.get("name"), source))
        assert not fuera_de_carpeta, (
            "estos tilesets dependen de una carpeta compartida del motor "
            f"en vez de vivir autocontenidos en {carpeta_nivel}: "
            f"{fuera_de_carpeta} -- un cambio en esos assets compartidos "
            "(como el PNG de cafetería pasando a 256x256 en master-plan) "
            "descuadra los gids de este nivel sin tocar el .tmx"
        )

    def test_cada_source_existe_y_su_tamano_coincide_con_lo_declarado(self) -> None:
        carpeta_nivel = TMX.parent
        for tileset in self._tilesets_del_tmx():
            nombre = tileset.get("name")
            tw = int(tileset.get("tilewidth"))
            th = int(tileset.get("tileheight"))
            tilecount = int(tileset.get("tilecount"))
            columns = int(tileset.get("columns"))
            imagen = tileset.find("image")
            source = imagen.get("source")
            w_tmx = int(imagen.get("width"))
            h_tmx = int(imagen.get("height"))

            ruta = (carpeta_nivel / source).resolve()
            assert ruta.is_file(), (
                f"tileset {nombre!r} declara source={source!r} pero el "
                f"archivo no existe en {ruta}"
            )

            superficie = pygame.image.load(str(ruta))
            w_real, h_real = superficie.get_size()
            assert (w_real, h_real) == (w_tmx, h_tmx), (
                f"tileset {nombre!r}: el .tmx declara {w_tmx}x{h_tmx} pero "
                f"{ruta.name} mide {w_real}x{h_real} de verdad -- con un "
                "tamaño distinto al declarado los gids se leen mal"
            )

            columnas_esperadas = w_tmx // tw
            filas_esperadas = h_tmx // th
            assert columns == columnas_esperadas, (
                f"tileset {nombre!r}: columns={columns} pero "
                f"{w_tmx}/{tw}={columnas_esperadas}"
            )
            assert tilecount == columnas_esperadas * filas_esperadas, (
                f"tileset {nombre!r}: tilecount={tilecount} pero "
                f"({w_tmx}/{tw})*({h_tmx}/{th})={columnas_esperadas * filas_esperadas}"
            )

    def test_las_hojas_de_sprites_y_tilesets_propios_existen(self) -> None:
        carpeta_nivel = TMX.parent
        faltantes = [
            p.name for p in carpeta_nivel.glob("sprite_*.png")
            if not p.is_file()
        ]
        hojas_sprite = list(carpeta_nivel.glob("sprite_*.png"))
        hojas_tileset = list(carpeta_nivel.glob("tileset_*.png"))
        assert hojas_sprite, (
            f"no se encontró ninguna hoja sprite_*.png propia en {carpeta_nivel}"
        )
        assert hojas_tileset, (
            f"no se encontró ningún tileset_*.png propio en {carpeta_nivel}"
        )
        assert not faltantes
        # tileset_cafeteria_soda.png es la copia byte a byte del PNG
        # compartido del profesor (AUD-655) -- tiene que estar en esta
        # lista de tilesets propios de la carpeta del nivel.
        nombres_tileset = {p.name for p in hojas_tileset}
        assert "tileset_cafeteria_soda.png" in nombres_tileset, (
            "falta la copia autocontenida del tileset de cafetería "
            f"(tileset_cafeteria_soda.png) en {carpeta_nivel}"
        )
