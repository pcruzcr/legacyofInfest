"""
Módulo: boss_venado
Sistema: Boss de la Etapa 1-4 — El Venado Sagrado (reescritura del estudiante, Evaluación Práctica I)
Unidad Académica: II, III, IV, V, VI, VII — ver el front-matter de README.md para units_demonstrated
Descripción: Diseño oficial de 17_BOSS_SPEC §3 reimplementado a partir de
    student_templates/boss_template.py. Unidad II: matemática vec2_* para esporas/embestida;
    Unidad III: CurveTools.bezier para el arco de la liana y el vuelo en forma de ocho;
    Unidad IV: orden de dibujo explícito tipo painter's order; Unidad V: efectos de brillo/HSV de ColorTools.
"""
from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np
import pygame

from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.math_utils import vec2_distance, vec2_normalize
from src.framework.ecs.bullet_swarm import EnjambreDeBalas
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.boss_kit import WeakPoint
from src.framework.entities.enemy_base import EnemyState
from src.framework.processing.color_tools import ColorTools
from src.framework.processing.curve_tools import CurveTools
from src.framework.processing.filter_tools import FilterTools
from src.stages.boss_venado.efectos_venado import (
    AnilloDeCaida,
    CoronaDeEsporas,
    CrestaDePisoton,
    EfectosDelEscenario,
    EfectosNulos,
    ESCOMBROS,
    EstelaDeFantasmas,
    EstrellasDeAturdimiento,
    HOJAS,
    MOTAS,
    NUBE_ESPORA,
    OleadaDeLianas,
    OLEADA_SEPARACION,
    POLEN,
    POLVO_ASENTANDOSE,
    POLVO_ATERRIZAJE,
    POLVO_PEZUNAS,
    POLVO_PISOTON,
    POLVO_RASPADO,
    SenalDeCastigo,
    TIERRA_OLEADA,
    cada_n_frames,
)

# Nueva arena (mapa "Residencias al Crepúsculo", 205x38 tiles)
ARENA_X0 = 2480.0        # borde izquierdo de CameraLock_01; mantener sincronizado con boss_venado_scene.ARENA_X0
ARENA_X1 = 3264.0        # RightWall_Arena
ARENA_CX = (ARENA_X0 + ARENA_X1) / 2.0
FLOOR_Y = 560.0          # parte superior del piso de colisión (Floor)
BASE_Y = 460.0           # centro de la senoidal: rect.bottom alcanza su pico en 548 (alcanzable cuerpo a cuerpo)

# H-19 (adopción V3): la arena real como rectángulo, para los límites del
# enjambre de esporas y para acotar el destino del teletransporte de fase.
#
# El motor (stage_scene.py ~L454-461) le pasa a TODO BossBase
# ``set_arena_bounds(Rect(0, 0, *map_pixel_size))`` -- correcto para un mapa
# que ES una arena, FALSO para el nuestro, que es un corredor de 3280px con la
# arena al final: ese rect da ``centerx == 1640``, en mitad del pasillo. El
# teletransporte del jefe de referencia usa exactamente ``arena_bounds.centerx``
# y copiarlo tal cual lanzaría al venado fuera de su terreno (rompiendo los
# candados boss_in_arena / no_damage_outside_arena del arnés de QA). Aquí se
# usan SIEMPRE nuestras propias constantes; la escena además re-declara estos
# mismos límites vía set_arena_bounds (doble candado, mismo patrón que la
# compensación de H-02).
ARENA_RECT = pygame.Rect(int(ARENA_X0), 0, int(ARENA_X1 - ARENA_X0), 608)
TELEPORT_MARGIN = 32.0   # separación mínima a las paredes al reaparecer tras el cambio de fase

# Cambio 5 de la campaña de fairness (dictamen doc-guardian AMARILLO,
# feedback UX del usuario 2026-08-18): el salto de fase deja de ser
# instantáneo. 17_BOSS_SPEC §3.3 ya describe que "el jefe deja de moverse
# (0.5s)" al cambiar de forma -- FADE_TELETRANSPORTE lee ese medio segundo
# como la duración del desvanecimiento en la posición VIEJA, redondeado a
# 0.55s para dejarle un fotograma extra de margen al anillo implosivo de
# _draw_teletransporte antes de que expire. MATERIALIZACION_TELETRANSPORTE es
# el destello breve que confirma la llegada al destino -- deliberadamente
# corto (menos de la mitad del desvanecimiento) porque es una confirmación,
# no un segundo aviso que el jugador tenga que leer.
FADE_TELETRANSPORTE = 0.55
MATERIALIZACION_TELETRANSPORTE = 0.25

# Hallazgo menor m-5: el enjambre de esporas no puede vivir bajo el terreno.
# ARENA_RECT baja hasta y=608 porque describe la COLUMNA completa de la arena
# (alto del mapa), y el motor sólo retira una bala cuando cruza ese borde: las
# esporas que caían seguían simulándose -- y pintándose -- unos 0,7 s por debajo
# de la línea de piso, es decir dentro del suelo dibujado. Este recorte comparte
# los bordes laterales con la arena y baja el techo inferior hasta el piso, así
# que una espora muere justo al tocarlo, que es donde el jugador espera verla
# apagarse. No sustituye a ARENA_RECT: aquél sigue siendo el contrato de "dónde
# pelea el venado" que comparten la escena y las pruebas.
ESPORAS_RECT = pygame.Rect(ARENA_RECT.left, ARENA_RECT.top,
                           ARENA_RECT.width, int(FLOOR_Y))

SINE_AMPLITUDE = 40.0    # 17_BOSS_SPEC §3.3 (oficial)
SINE_FREQ = 0.4
DRIFT_SPEED = 60.0
CHARGE_SPEED_P1 = 220.0
CHARGE_SPEED_P2 = 280.0
CHARGE_TELEGRAPH = 0.35
CHARGE_WALL_PAUSE = 1.0  # aturdimiento por choque con la pared: debe durar más que un salto de esquiva de ida y vuelta a altura completa (~0.95s) para que los jugadores hábiles puedan aterrizar y castigar (FINDINGS H-12/E)
STOMP_TELEGRAPH = 0.4
STOMP_WINDOW = 0.35
STOMP_RECOVER = 0.6      # corrección del Hallazgo C: ventana de castigo en el suelo después de que la onda de choque se disipa
FLASH_PISOTON_FRAMES = 2   # duración del destello blanco del impacto de STOMP (§2.2 del diseño AAA fase 2)
COLOR_FLASH = (255, 255, 255)
SWEEP_TELEGRAPH = 0.6
SWEEP_ROOTED = 1.6      # pulido AAA (spec 2026-08-21 §2.1): plantado en el suelo tras
                         # el disparo de la oleada doble -- sustituye a SWEEP_WINDOW
                         # (retirada: la ventana de daño ahora la dan las propias
                         # OleadaDeLianas viajeras, no un rect estático de ancho
                         # completo). B-039 opción C (REGISTRO-DE-BUGS.md, decisión
                         # del usuario 2026-08-23): subido de 1.2s a 1.6s junto con
                         # el picado de aterrizaje de ATERRIZAJE_BARRIDO/VEL_PICADO
                         # más abajo -- con el gap ya cerrado durante el propio
                         # aviso, esta ventana de castigo posterior por fin es
                         # alcanzable a pie, y necesita margen real para que valga
                         # la pena castigarla.

# B-039 opción C (REGISTRO-DE-BUGS.md, decisión del usuario 2026-08-23,
# playtest humano #2 en reports/aaa_parte2_playtest_humano): en fase 2 el
# jefe nunca se acercaba lo bastante durante el aviso de VINE_SWEEP como para
# que SWEEP_ROOTED fuera un castigo alcanzable -- PLAYER_WALK_SPEED = 90 px/s
# recorre apenas ~108px en 1.2s, y el gap real medido en pelea llegaba a
# ~555px. La sección "picado de aterrizaje" de _update_movement (ver
# _actualizar_picado_de_barrido) usa estas dos constantes para que el jefe
# PIQUE en diagonal hacia el jugador durante el propio aviso, en vez de
# quedarse plantado y dejar que el barrido aterrice lejos.
#
# ATERRIZAJE_BARRIDO: separación horizontal objetivo, centro a centro, entre
# el jefe y el jugador al terminar el picado -- suficiente para que el
# barrido siga leyéndose como un ataque, no un abrazo.
ATERRIZAJE_BARRIDO = 110.0
# VEL_PICADO: velocidad horizontal del descenso. El peor gap medido en pelea
# real fue ~555px con un aviso de SWEEP_TELEGRAPH=0.6s (INTACTO, no se toca).
# B-043 (REGISTRO-DE-BUGS.md, addendum 2026-08-23, dictamen doc-guardian
# AMARILLO): bajado de 1500 a 950 px/s por legibilidad -- descontando ya el
# destino de ATERRIZAJE_BARRIDO, el peor caso real recorre 555-110=445px, que
# a 950 px/s se cierra en ~0.47s, todavía con margen dentro del presupuesto
# de 0.6s del aviso: el picado sigue llegando SIEMPRE, sólo más lento y
# legible. El paso está acotado por fotograma (mismo patrón que
# _approach_y): jamás teletransporta.
VEL_PICADO = 950.0
# SWEEP_DESPEGUE: B-043 (REGISTRO-DE-BUGS.md, addendum 2026-08-23) -- rampa
# de arranque ease-in del vuelo bezier tras el enraizado del barrido
# (SWEEP_ROOTED). Causa raíz: B-041 ya evita que el PRIMER fotograma de
# vuelo reanudado teletransporte (_reanclar_bezier_al_reanudar), pero no
# tocaba la VELOCIDAD a la que arranca ese vuelo reanudado -- a plena marcha
# desde el frame 1 (~450 px/s medidos), el jefe salía disparado y atropellaba
# al jugador que acababa de castigar la ventana plantada, justo la jugada
# que el diseño quiere premiar. Mientras self._sweep_despegue > 0,
# _update_movement escala el avance de _bezier_t con un factor ease-in
# cuadrático (0 al arrancar la rampa, 1 al cerrarla) -- ver
# test_despegue_barrido.py.
# Iteración 2 de verificación (2026-08-23): subido de 0.45s a 0.5s (el
# máximo sugerido por el diseño) -- la canónica competent seed=1 seguía
# muriendo por acumulación de contactos de CHARGE/vuelo normal (ajenos al
# alcance de este paquete) incluso con la gracia ya extendida al enraizado;
# una rampa más larga desplaza ligeramente CUÁNDO cruza el jefe el centro
# de la arena tras cada barrido (la condición que arma CHARGE en
# _try_attack), lo bastante para evitar el mismo cúmulo de choques en esta
# semilla. Candado (a) de test_despegue_barrido.py sigue midiendo <250 px/s
# de sobra con este valor (una rampa más larga sólo reduce más la
# velocidad media del arranque).
SWEEP_DESPEGUE = 0.5
TOSS_TELEGRAPH = 0.4     # aviso previo del ataque a distancia (doc 86 §2.4 regla 5:
                         # "si algo dispara, se ve disparar") -- hasta ahora disparaba sin aviso visual
SPORE_TELEGRAPH = 0.35   # mismo motivo que TOSS_TELEGRAPH, para el abanico de esporas
SPORE_SPEED = 80.0
SPORE_RANGE = 420.0      # expira por vec2_distance (Unidad II)
SPORE_LIFETIME = 6.0     # generoso: la expiración por distancia (5.25 s) se activa primero
PROJECTILE_HIT_RADIUS = 5.0  # mitad del tamaño de la caja de contacto de liana/espora (arrastrado de la revisión de la Tarea 8)
VINE_PREDICT = 0.5       # segundos de anticipación según la velocidad del jugador (oficial §3.5)
VINE_SPEED = 0.9         # proyectil de liana: progreso de la trayectoria en t/s
VINE_ARC_HEIGHT = 80.0   # proyectil de liana: desplazamiento del vértice del arco, oficial §3.5
FIGURE8_DIP = 45.0       # amplitud vertical NOMINAL de la figura en ocho; el valor
                         # efectivo lo recorta _caida_de_figura8() según la altura viva

# corrección de diseño H-04/H-08: verticalidad de ataque (completitud de 17_BOSS_SPEC §5).
# Ambas constantes son los valores CANÓNICOS, medidos con la altura de sprite de
# 48px de la fase 1. Desde la adopción de `escala` (H-20) el cuerpo puede crecer,
# así que el código no las usa crudas: llama a _y_de_suelo() /
# _y_de_banda_de_embestida(), que las re-derivan de la altura viva del rect. Se
# conservan como constantes porque los tests y la documentación del diseño se
# refieren a estos números concretos.
BOSS_SPRITE_SIZE = 48        # lienzo del sprite en disco; base de todo el escalado de fase
GROUND_Y = FLOOR_Y - float(BOSS_SPRITE_SIZE)  # y superior al golpear el suelo: rect.bottom == floor (ventana de castigo H-04)
CHARGE_BAND_Y = 500.0        # y superior durante la embestida: rect.bottom 548 == valle de la senoidal (banda cuerpo a cuerpo H-08)
CHARGE_BAND_GAP = FLOOR_Y - CHARGE_BAND_Y - float(BOSS_SPRITE_SIZE)  # 12px de aire bajo las pezuñas durante la embestida
VERTICAL_ATTACK_SPEED = 200.0  # px/s de descenso/ascenso para la verticalidad del ataque

AGGRO_X = ARENA_X0 - 96.0  # el venado solo pelea en su terreno sagrado: aggro en cuanto el jugador se acerca a la entrada de la arena

GRACIA_DE_AGGRO = 0.6   # H-26/B-031: 2x el ease de cámara de 0.3s del fix H-17 -- al
                         # aggro, la cámara del corredor todavía viaja al encuadre de
                         # la arena: sin esta gracia el PRIMER ataque (VINE_TOSS, sin
                         # compuerta de distancia) se telegrafía FUERA de pantalla
                         # (evidencia: filmstrip 20260819_155557, disparo a 561px con
                         # el boss todavía fuera de cámara); de paso, la línea de voz
                         # de aggro (m-4) gana su momento antes del primer golpe.

# Puntos débiles (Característica C, adoptados del boss_kit.WeakPoint del boss
# de referencia -- spec 2026-07-29-adopcion-v2-sfx-luces-weakpoints-design.md §3).
# Solo enriquecimiento: no forma parte de la rúbrica oficial de 17_BOSS_SPEC §3.
#
# Los offsets se declaran en espacio CANÓNICO: el frame del sprite sin voltear
# tal como está en disco (facing_direction >= 0, sin pygame.transform.flip
# aplicado -- ver BossVenado._mirror_weak_point más abajo para el caso
# facing_direction < 0).
#
# Una traducción ingenua de los propios números del boss de referencia (offset
# + (6,4), para pasar de su rect de 36x44 a nuestro lienzo de 48x48 -- ver la
# spec) NO cae sobre las astas de este sprite: se verificó píxel por píxel
# contra assets/sprites/bosses/boss_venado_drift.png (y se cruzó con
# _charge.png/_frenzy_drift.png, misma pose) con una cuadrícula de referencia
# de 4px. En ese frame de 48x48 el venado mira a la derecha: las puntas de las
# astas se agrupan en x 34-42/y 0-6, difuminándose hacia la corona del cráneo
# hasta aproximadamente y 9; el objetivo legible de "cuernos" es x 32-46/y
# 0-10. El anca trasera (opuesta a la cabeza, el flanco que un jugador rodea
# para alcanzar) se ubica aproximadamente en x 9-21/y 18-34 -- la traducción
# ingenua (x 2-12/y 24-42) fallaba mayormente el cuerpo, cayendo en el
# fondo/las patas.
CUERNOS_OFFSET = (32, 0)
CUERNOS_SIZE = (14, 10)
CUERNOS_MULTIPLIER = 2.5
FLANCO_OFFSET = (9, 18)
FLANCO_SIZE = (12, 16)
FLANCO_MULTIPLIER = 1.8
WEAK_POINT_FLASH_DURATION = 0.12  # confirmación breve de golpe crítico, no un VFX persistente

# "Fragmento de Reliquia 1" (adopción V3, D10): botín ANUNCIADO, no botín
# jugable. Verificado antes de escribir una línea: no existe ninguna reliquia en
# `inventory._ITEM_DEFS`, `Inventory.add()` rechaza ids fuera del catálogo
# (inventory.py:178-179) y el HUD no expone NINGUNA API para añadir iconos.
# Meterla al catálogo exigiría editar el motor -- prohibido. Y reutilizar un id
# existente (p. ej. `ancients_rib`) para fingir persistencia daría un objeto que
# no es el que dice el HUD, más un bonus de vida que ninguna ficha pide.
#
# Así que la reliquia se declara por lo que SÍ hace: al terminar la secuencia de
# derrota se levanta una sola vez la bandera `reliquia_anunciada`, y la escena la
# lee para pintar un icono procedural de cornamenta con el nombre. Lo que NO
# hace, por escrito: no entra al inventario, no da bonus, no persiste entre
# partidas y NO SUENA -- el anuncio es mudo a propósito (H-21, ver
# `_anunciar_reliquia`).
RELIQUIA_ID = "fragmento_reliquia_1"
RELIQUIA_NOMBRE = "Fragmento de Reliquia 1"


class BossVenado(BossBase):
    """Dos fases oficiales: El Bosque Duerme (senoidal) / El Bosque Despierta (bezier)."""

    # Habilidades que suelta al morir (adopción V3, D1). ATRIBUTO DE CLASE, no de
    # instancia: el test de contrato del profesor
    # (tests/test_habilidades_que_sueltan_los_jefes.py::
    # test_hay_un_jefe_para_cada_habilidad_condicionada) recorre las subclases de
    # BossBase y lee `getattr(cls, "skill_drop")` SIN instanciar -- construir un
    # BossVenado carga sprites de disco, así que declararlo en __init__ lo
    # dejaría invisible para ese test y `skill_dash`/`skill_parry` volverían a
    # ser contenido inalcanzable con PLAYER_SKILLS_REQUIRE_UNLOCK encendido.
    #
    # No hace falta nada más de nuestro lado: `EnemyBase._die`
    # (enemy_base.py:576-591) publica `skill_drop=",".join(habilidades_que_suelta())`
    # dentro de ENEMY_DIED, y `senales.py:68-82` lo convierte en un Recogible.
    # Ambos ids existen en `inventory._ITEM_DEFS` (verificado).
    skill_drop = ["skill_dash", "skill_parry"]

    # Adopción del drop #6 del motor (AUD-606, H-20 Opción A). Con esto en
    # True es EL MOTOR quien escala hitbox/hurtbox ancladas abajo-centro
    # (`BossBase._escalar_local`, boss_base.py:338-360) cada vez que
    # `_update_rects()` las recalcula -- misma aritmética `round()` que este
    # archivo hacía a mano en el `_escalar_rect_local` retirado, rects
    # bit-idénticos (verificado: fase 2 sigue dando (8,5,45,55)/(11,5,38,50)).
    # La resolución de puntos débiles, en cambio, NO se delega: activar esta
    # bandera también habilita la rama `sigue=True` de
    # `boss_kit.resolve_weak_point_damage` (línea 409), y esa rama llama
    # `WeakPoint.rect_for(..., escala=..., facing=...)` con una fórmula que es
    # errónea a escala≠1 (B-050: espeja el offset CANÓNICO contra el ancho YA
    # escalado y multiplica por `escala` DESPUÉS, en vez de escalar primero).
    # Por eso `apply_hit` sigue llamando a nuestro propio
    # `_resolver_punto_debil` en vez de la función del motor -- ver ese
    # método y `_escalar_weak_point`/`_mirror_weak_point` más abajo. Retirar
    # la compensación en cuanto el motor corrija el orden de `rect_for`: el
    # test canario de B-050 (test_adopcion_v3.py) avisará.
    cajas_siguen_al_cuerpo = True

    _TELEGRAPH_WARN_COLOR = (230, 90, 60)   # tinte de advertencia de STOMP/CHARGE/VINE_SWEEP/VINE_TOSS/MUSHROOM_SPORE
    _WEAK_POINT_FLASH_HUE = 48.0            # confirmación de crítico ámbar/dorada, distinta
                                             # del color de advertencia de arriba y del
                                             # pulso verde de transición de fase de abajo

    # Parámetros del anillo de esporas del cambio de fase (adopción V3, D9).
    # Ninguna cifra es libre: el daño por espora sale de 17_BOSS_SPEC §3.3, el
    # mismo 0.25 que ya reparten las tres esporas dirigidas de MUSHROOM_SPORE,
    # y el resto (una docena de proyectiles, lentos y de vida corta) está
    # elegido para que el anillo se lea como un patrón con huecos por donde
    # pasar: subir la cantidad lo convertiría en una pared y el cambio de fase
    # dejaría de ser esquivable.
    _ESPORAS_DE_LA_CORONA = 12
    _VELOCIDAD_ESPORA_ENJAMBRE = 70.0
    _DANO_ESPORA_ENJAMBRE = 0.25
    _VIDA_ESPORA_ENJAMBRE = 3.0
    _RADIO_ESPORA_ENJAMBRE = 3.0
    _COLOR_ESPORA_ENJAMBRE = (200, 230, 150)   # verde pálido de hongo, no el rosa por defecto del enjambre

    # Anuncio visual de esa misma corona (Cambio 2 de la campaña de fairness,
    # doc 86 §2.4 regla 5: "si algo se activa, se anuncia"). Hasta ahora
    # _soltar_abanico_de_esporas() se disparaba al CERRAR la ventana de
    # transición sin ningún aviso previo -- el mismo vacío que TOSS_TELEGRAPH/
    # SPORE_TELEGRAPH cerraron para VINE_TOSS/MUSHROOM_SPORE en el Cambio 1.
    # Reutiliza el tinte de advertencia ya establecido: el enjambre es otro
    # golpe por venir, no un color nuevo que el jugador tenga que aprender.
    _COLOR_ANUNCIO_ENJAMBRE = _TELEGRAPH_WARN_COLOR
    # Eco nombrado del valor que BossBase._start_phase_transition hardcodea en
    # transition_timer (boss_base.py:380): no existe ninguna API para leerlo
    # de vuelta, así que se declara aquí para derivar un progreso 0..1 sin un
    # número mágico suelto dentro de _draw_anuncio_del_enjambre.
    _VENTANA_TRANSICION_SEGUNDOS = 2.5

    # B-048 (veredicto de la parada de la Tarea 14, 2026-08-25): tono
    # frío/plateado-verdoso del aura de bordes Sobel -- deliberadamente
    # distinto del dorado de SenalDeCastigo (250, 220, 120, exclusivo de la
    # señal universal de ventana de castigo) y del verde liana de
    # EstelaDeFantasmas (120, 200, 140, exclusivo de la estela de la
    # embestida) para que las tres señales se lean como cosas DISTINTAS.
    _AURA_COLOR_BORDES = (150, 230, 210)

    # Eco nombrado de BossBase._APPLY_FILTER_EVERY_N_FRAMES (boss_base.py:70)
    # -- mismo criterio que _VENTANA_TRANSICION_SEGUNDOS arriba: no existe
    # ninguna API pública para leerlo de vuelta, así que se declara aquí
    # para que la cadencia de recómputo del aura de bordes (B-048, cara
    # cara al usuario) coincida con el throttle de rendimiento del motor
    # (evitar invocar FilterTools.sobel_edge/cv2 en cada fotograma) sin un
    # número mágico suelto en _construir_aura_de_bordes/_dibujar_aura_de_bordes.
    _CADENCIA_RECOMPUTO_AURA = 5

    def __init__(self, spawn_position: pygame.Vector2) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=12.0,
            damage_on_contact=0.75,
        )
        self.set_boss_name("VENADO SAGRADO")
        # Depósito de proyectiles del anillo de fase 2. Se apoya en la
        # estructura de arreglos paralelos del framework porque el anillo entero
        # se simula con unas pocas operaciones sobre vectores, en lugar de con
        # una docena de objetos actualizándose uno a uno. Es una vía de esporas
        # INDEPENDIENTE del ataque MUSHROOM_SPORE de §3.3, que puntúa en la
        # rúbrica y conserva intactos sus propios diccionarios de proyectil.
        self.esporas = EnjambreDeBalas(capacidad=256)
        # Enganche opcional con el mezclador de audio; lo rellena la escena
        # durante on_enter. Mientras valga None, cada intento de hablar se
        # descarta sin lanzar nada (ver _decir), de modo que un jefe levantado
        # desde una prueba o desde el arnés sin sonido se comporta igual.
        self.audio_de_voz: object | None = None
        # Puerto de efectos visuales (pulido AAA 2026-08-21): lo rellena la escena en
        # on_enter con EfectosDeLaEscena. Mientras valga el nulo por defecto (tests sin
        # escena, grade_boss.py, arnés headless), cada petición de VFX se descarta sin
        # lanzar nada -- mismo criterio que audio_de_voz arriba.
        self.efectos: EfectosDelEscenario = EfectosNulos()
        self.reliquia_anunciada = False   # una sola vez por pelea (ver _update_defeat)
        self._voz_de_aggro_dicha = False  # m-4: la línea de fase 1 suena al primer avistamiento
        self._load_boss_sprites("boss_venado", 48, 48)
        self._load_extra_sprites()

        # Patrón universal del motor (enemy_walker.py:54-57): la Y de spawn del TMX es
        # la línea de los pies; position es la esquina superior izquierda, así que se
        # desplaza hacia arriba la altura del sprite.
        self.rect.width = 48
        self.rect.height = 48
        self.position.y -= self.rect.height
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

        self._elapsed = 0.0
        self._frames_vfx = 0     # contador de fotogramas de update(), para cadencias (cada_n_frames)
        self._t_vfx = 0.0        # reloj acumulado de update(), para oscilaciones (oleada, futuras piezas del pulido)
        self._base_y = BASE_Y
        self._attack_cooldowns = {
            "STOMP": 3.0, "CHARGE": 6.0, "VINE_TOSS": 8.0,
            "VINE_SWEEP": 5.0, "MUSHROOM_SPORE": 10.0,
        }
        self._attack_timers = {k: 0.0 for k in self._attack_cooldowns}
        # VINE_TOSS/MUSHROOM_SPORE empiezan en cooldown: la pelea abre con
        # presión cuerpo a cuerpo, no con proyectiles.
        self._attack_timers["VINE_TOSS"] = self._attack_cooldowns["VINE_TOSS"]
        self._attack_timers["MUSHROOM_SPORE"] = self._attack_cooldowns["MUSHROOM_SPORE"]
        self._gracia_de_aggro = 0.0      # H-26/B-031: se arma a GRACIA_DE_AGGRO la primera vez que se ve al jugador (ver _alert_behavior)

        self._telegraph = ""             # "" | "STOMP" | "CHARGE" | "VINE_SWEEP" | "VINE_TOSS" | "MUSHROOM_SPORE"
        self._telegraph_timer = 0.0
        self._charge_active = False
        self._charge_direction = 1
        self._charge_recover = 0.0       # corrección del Hallazgo C: ventana de castigo estacionaria después de detenerse en la pared
        self._stomp_rect: pygame.Rect | None = None
        self._stomp_window = 0.0
        self._stomp_recover = 0.0        # corrección del Hallazgo C: ventana de castigo en el suelo después de que la onda de choque se disipa
        self._y_recovering = False       # H-04/H-08: recuperación fluida de la y después de que termina un ataque
        # Pulido AAA fase 2 (diseño 2026-08-21, §2.2/§2.5): cresta de tierra
        # del pisotón, destello blanco del impacto, señal universal de
        # ventana de castigo y la caché de frames vivos escalados que
        # SenalDeCastigo necesita (BossBase.draw crea una Surface NUEVA por
        # fotograma en fase 2 -- ver _frame_vivo más abajo).
        self._cresta_pisoton: CrestaDePisoton | None = None
        self._flash_frames: int = 0
        self._senal = SenalDeCastigo()
        self._cache_frames_vivos: dict[tuple[str, int, int, float], pygame.Surface] = {}
        # Corrección visual del coordinador (Task 14, 2026-08-22): (B)
        # fantasmas de sprite de la embestida de fase 2 (reemplaza al
        # rectángulo verde de self.efectos.estela()) y (C) caché del tinte
        # amarillo de transición, compensación de B-038 -- ver
        # _dibujar_cuerpo_en_transicion.
        self._fantasmas = EstelaDeFantasmas()
        self._cache_tinte_transicion: dict[tuple[str, int, int, float], pygame.Surface] = {}
        # B-048 (veredicto de la parada de la Tarea 14, 2026-08-25): aura
        # espectral de bordes Sobel -- reemplaza el flash negro opaco de
        # BossBase._apply_filter (ver el override del mismo nombre más
        # abajo). self._aura_base es la Surface premultiplicada de
        # intensidad plena, recalculada cada _CADENCIA_RECOMPUTO_AURA
        # fotogramas (ver _dibujar_aura_de_bordes); self._aura_clave guarda
        # la clave de _frame_vivo() con la que se construyó, para forzar un
        # recómputo inmediato si la animación cambia de frame/dirección/
        # escala antes de que le toque su siguiente tick (evitar un aura
        # con la silueta desalineada del cuerpo real, aunque sea 1 cuadro).
        self._aura_base: pygame.Surface | None = None
        self._aura_clave: tuple[str, int, int, float] | None = None
        self._aura_contador = 0
        self._oleadas: list[OleadaDeLianas] = []
        self._sweep_rooted = 0.0
        self._sweep_aterrizo = False   # True desde que la oleada aterriza en el suelo durante el aviso -- evita repetir el polvo de aterrizaje cada frame
        self._sweep_lado_picado = 1    # B-039-C: lado (+1 derecha/-1 izquierda) del picado de aterrizaje, fijado en _try_attack al armar el aviso
        self._sweep_despegue = 0.0     # B-043: rampa ease-in tras el enraizado -- ver SWEEP_DESPEGUE
        self._projectiles: list[dict[str, Any]] = []
        self._last_player_velocity = pygame.Vector2(0.0, 0.0)

        self._bezier_path: list[tuple[float, float]] = []
        self._bezier_t = 0.0
        self._bezier_dir = 1             # recorrido de ida y vuelta (ping-pong) de la figura en ocho

        # Cambio 5 de la campaña de fairness (UX del teletransporte de fase,
        # feedback del usuario 2026-08-18). Los dos relojes viven en 0.0 en
        # reposo y sólo se arman dentro de _start_phase_transition() /
        # nuestro update() -- ver esos dos métodos para el porqué de cada uno.
        self._desvanecimiento_restante = 0.0   # cuenta atrás del desvanecimiento en la posición vieja
        self._materializacion_restante = 0.0   # cuenta atrás del destello de llegada al destino

        self._defeat_stage = 0
        self._defeated = False
        self._spore_glow = self._build_spore_glow()

        # Puntos débiles (Característica C, enriquecimiento -- ver el comentario a
        # nivel de módulo arriba de CUERNOS_OFFSET para saber cómo se midieron).
        # BossBase.__init__ ya inicializó self.weak_points=[] /
        # self.last_weak_point=None; esto solo llena la lista. Declarados en
        # espacio canónico (mirando a la derecha) -- _mirror_weak_point() los
        # refleja cuando el sprite se dibuja volteado (facing_direction < 0).
        self.weak_points = [
            WeakPoint(offset=CUERNOS_OFFSET, size=CUERNOS_SIZE,
                      multiplier=CUERNOS_MULTIPLIER, label="cuernos"),
            # Solo se expone en el índice de fase 1 (la fase de figura en ocho/bezier)
            # -- refleja el propio diseño del boss de referencia (spec de adopción §3.1).
            WeakPoint(offset=FLANCO_OFFSET, size=FLANCO_SIZE,
                      multiplier=FLANCO_MULTIPLIER, phases=(1,), label="flanco"),
        ]
        self._weak_point_flash_timer = 0.0
        self._weak_point_flash_point: WeakPoint | None = None

        self.set_phases()

    def set_phases(self, phases: list[BossPhase] | None = None) -> None:
        if phases is not None:
            super().set_phases(phases)
            return
        super().set_phases([
            BossPhase(phase_index=0, health_threshold=12.0,
                      attack_patterns=["STOMP", "CHARGE", "VINE_TOSS"],
                      movement_type="sine", speed_multiplier=1.0),
            # Adopción V3 (D4): el crecimiento del cuerpo se DECLARA aquí, en el
            # dataclass, en lugar de redimensionar a mano. El contrato del profesor
            # (test_boss_venado_declara_una_fase_con_escala) lee
            # `getattr(f, "escala", 1.0)` sobre `venado.phases`, y es
            # `BossBase._aplicar_escala_de_fase` quien redimensiona anclando
            # pies+centro y sincroniza `position`. El factor es moderado a
            # propósito: un cuerpo del doble de tamaño taparía media arena y
            # dejaría al jugador sin huecos por donde pasar, mientras que un
            # cuarto más basta para que la silueta cambie de un vistazo. Las
            # cajas de daño las escala el motor (`cajas_siguen_al_cuerpo`,
            # AUD-606) y los puntos débiles crecen con él por compensación
            # propia (H-20/B-050, ver _factor_de_escala más abajo).
            BossPhase(phase_index=1, health_threshold=6.0,
                      attack_patterns=["VINE_SWEEP", "MUSHROOM_SPORE", "CHARGE"],
                      movement_type="bezier", speed_multiplier=1.5,
                      escala=1.25, filter_effect="sobel"),
        ])

    def _load_extra_sprites(self) -> None:
        """frenzy_drift/skull no están entre las 6 claves fijas de BossBase — se cargan manualmente."""
        from pathlib import Path
        base = Path("assets/sprites/bosses")
        for key in ("frenzy_drift", "skull"):
            path = base / f"boss_venado_{key}.png"
            try:
                self._sprite_frames[key] = AssetLoader.load_sprite_sheet(path, 48, 48)
            except (pygame.error, FileNotFoundError, PermissionError):
                logging.warning("boss_venado: failed to load sprite %s", path)

    def _check_detection_range(self) -> bool:
        """Corrección de diseño: protege toda la ARENA, no todo el mapa. El
        loader/CollisionSystem asignan player_ref desde el frame 1 (mucho antes
        de que el jugador llegue siquiera a la arena), así que una simple
        verificación `player_ref is not None` mantenía al boss permanentemente en
        ALERT y dejaba que VINE_TOSS sin límite de alcance (un arco Bezier de
        ~2500px) francotirara al jugador a lo largo de todo el corredor. Ahora
        el aggro solo se activa cuando el jugador se acerca a la entrada de la
        arena."""
        return self._player_ref is not None and self._player_ref.centerx >= AGGRO_X

    def _should_retreat(self) -> bool:
        """Corrección de compatibilidad con el MOTOR V2: EnemyBase._should_retreat
        (enemy_base.py ~L841-843) fuerza state=RETREAT en cuanto current_health
        cae a RETREAT_HEALTH_FRACTION (25%) de max_health -- con max_health=12.0
        eso es current_health<=3.0, bien entrada la fase 2 -- y le entrega el
        control al _retreat_behavior genérico (~L882-890), que aleja al boss del
        jugador sin ninguna noción de ARENA_X0/X1 y puede empujarlo fuera de la
        arena por completo. El diseño oficial del Venado (17_BOSS_SPEC §3) no
        tiene estado de retirada: el patrón de figura en ocho de la fase 2 y el
        límite de la arena deben seguir mandando de principio a fin del
        combate, así que este override excluye al boss por completo de ese
        comportamiento."""
        return False

    def conectar_efectos(self, puerto: EfectosDelEscenario) -> None:
        """Inyectado por la escena en on_enter() (sobrevive al reintento del motor
        V3, que reconstruye el jefe en cada respawn -- ver el docstring de
        BossVenadoScene.on_enter). Sin conectar, self.efectos sigue siendo el
        EfectosNulos por defecto."""
        self.efectos = puerto

    def oleadas_activas(self) -> list[pygame.Rect]:
        """Contrato público para bots/arnés (co-calibración, spec §5): los rects de
        las oleadas de lianas VIVAS en este instante, en coordenadas de mundo."""
        return [o.rect for o in self._oleadas if o.viva]

    # ──────────────────────────────────────────────
    # Contrato del template (5 métodos)
    # ──────────────────────────────────────────────
    def _patrol_behavior(self, dt: float) -> None:
        self._update_movement(dt)

    def _alert_behavior(self, dt: float) -> None:
        # m-4: el clip de voz de la fase 1 existía en disco pero era inalcanzable
        # -- su único disparador estaba en el cambio de fase, que por definición
        # ya estrena la fase 2 y pide el clip de la 2. El momento que le
        # corresponde es este: el venado reclama su terreno la primera vez que
        # ve al jugador entrar en la arena. La bandera impide que lo repita cada
        # vez que el motor reentra en ALERT/CHASE al perder y recuperar el rastro.
        if not self._voz_de_aggro_dicha:
            self._voz_de_aggro_dicha = True
            self._decir("sfx_voz_venado_fase1")
            # H-26/B-031: arma la gracia UNA sola vez -- la propia bandera de
            # voz ya garantiza que esto corre solo en el primer avistamiento.
            self._gracia_de_aggro = GRACIA_DE_AGGRO
        self._update_movement(dt)
        # H-26/B-031: mientras la gracia sigue viva el venado ya se mueve (la
        # línea de arriba), pero no arma ningún ataque -- le da tiempo a la
        # cámara (ease H-17 de 0.3s) a terminar de encuadrar la arena antes
        # de que el primer ataque pueda telegrafiarse fuera de pantalla.
        if self._gracia_de_aggro > 0:
            self._gracia_de_aggro -= dt
            return
        # corrección del Hallazgo C: ninguna recuperación de castigo (STOMP en
        # el suelo, pausa de pared de CHARGE) puede ser interrumpida por un
        # nuevo ataque que empiece a mitad de la ventana.
        if (self.is_transitioning or self._telegraph or self._charge_active
                or self._stomp_recover > 0 or self._charge_recover > 0):
            return
        phase = self.phases[self.current_phase]
        for pattern in phase.attack_patterns:
            if self._attack_timers.get(pattern, 0.0) <= 0.0:
                self._try_attack(pattern)
                if self._telegraph:
                    # B-030 (observación menor H-23): un solo ataque por
                    # fotograma -- sin este corte, dos patrones listos el
                    # mismo frame hacían que el segundo _try_attack pisara
                    # el telegraph que el primero acababa de armar, quemando
                    # el cooldown de ambos y perdiendo el turno entero.
                    break

    def _search_behavior(self, dt: float) -> None:
        """Task 9 (revisión final 2026-08-21, B-035): el venado JAMÁS abandona
        su arena para buscar al jugador.

        ``EnemyBase._search_behavior`` (enemy_base.py ~L1060) camina en línea
        RECTA hacia ``_last_seen`` sumando directo a ``position.x`` -- sin
        pasar por ``_update_movement`` ni por ninguno de sus clamps de arena.
        Evidencia (canónica competent, seed 1, 14400f): tras retroceder bajo
        AGGRO_X baiteando un CHARGE, el venado pierde el aggro, EnemyBase
        enruta a ``EnemyState.SEARCH`` y ese método genérico lo saca de
        ARENA_X0 durante 32 fotogramas seguidos (gate ``boss_in_arena`` roto,
        0 ``BOSS_ATTACK``/``PLAYER_DAMAGED`` el resto de la corrida).

        La transición SEARCH -> PATROL/IDLE (el temporizador ``_search_timer``
        y el cambio de estado al expirar) sigue viviendo en
        ``EnemyBase._run_state_machine`` -- este override solo reemplaza el
        MOVIMIENTO de cada fotograma de SEARCH por el mismo patrón de deriva
        que ya usa PATROL (``_patrol_behavior`` -> ``_update_movement``, con
        sus propios clamps de ARENA_X0/X1), nunca el avance ciego hacia
        ``_last_seen``."""
        self._patrol_behavior(dt)

    def _get_animation_key(self) -> str:
        if self._charge_active or self._telegraph == "CHARGE" or self._charge_recover > 0:
            return "charge"
        if self._telegraph == "STOMP" or self._stomp_window > 0 or self._stomp_recover > 0:
            return "stomp"
        if self._telegraph == "VINE_SWEEP" or self._sweep_rooted > 0 or self._sweep_despegue > 0:
            return "vine"   # B-043: la rampa de despegue mantiene la animación del barrido
        if self.current_phase >= 1 and "frenzy_drift" in self._sprite_frames:
            return "frenzy_drift"
        return "drift"

    # ──────────────────────────────────────────────
    # Escalado de fase (H-20/AUD-606): el motor escala hitbox/hurtbox; los
    # puntos débiles siguen compensados a mano (B-050)
    # ──────────────────────────────────────────────
    def _factor_de_escala(self) -> float:
        """Cuánto ha crecido el cuerpo respecto al lienzo del sprite en disco.

        Adopción AUD-606: desde que la clase declara `cajas_siguen_al_cuerpo =
        True`, hitbox/hurtbox YA NO pasan por este método -- las escala el
        motor (`BossBase._escalar_local`, boss_base.py:338-360, la misma
        aritmética `round()` que este archivo usaba a mano en el
        `_escalar_rect_local` retirado; rects bit-idénticos). Lo que SÍ sigue
        necesitando el factor propio son los puntos débiles
        (`_escalar_weak_point` más abajo, compensación B-050 de
        `WeakPoint.rect_for`) y la calavera de la secuencia de derrota
        (`_draw_skull`).

        Se mide del rect VIVO, no de `escala_de_fase`. La diferencia importa:
        media docena de pruebas existentes fuerzan `current_phase = 1` a mano
        sin pasar por `_aplicar_escala_de_fase`, así que el cuerpo sigue midiendo
        48px mientras la fase declara 1.25. Derivando del hecho y no de la
        declaración, los puntos débiles nunca pueden desincronizarse del
        sprite que el jugador realmente ve.

        m-6: el tamaño de referencia se pide con getattr y no como atributo
        directo. `_tam_base` es estado PRIVADO del motor (lo crea BossBase la
        primera vez que aplica una escala) y nada nos garantiza que siga
        existiendo con ese nombre tras una actualización del RAR; si
        desapareciera, este método debe degradar al lienzo canónico de 48px --
        puntos débiles sin escalar -- y no reventar el jefe entero con AttributeError.
        """
        tam_base = getattr(self, "_tam_base", None)
        base = tam_base[0] if tam_base else BOSS_SPRITE_SIZE
        return float(self.rect.width) / float(base or BOSS_SPRITE_SIZE)

    def _escalar_weak_point(self, point: WeakPoint) -> WeakPoint:
        """Compensación B-050: escala un punto débil a mano en vez de dejar
        que `boss_kit.resolve_weak_point_damage` (boss_kit.py:391-428) se lo
        pase como `escala` a `WeakPoint.rect_for` -- la rama que activaría
        `cajas_siguen_al_cuerpo = True` si llamáramos a esa función.

        `rect_for` (boss_kit.py:141-163) espeja el offset CANÓNICO contra el
        ancho YA escalado y multiplica por `escala` DESPUÉS -- da
        `(W·s − ox − w)·s` en vez de la fórmula correcta `s·(W − ox − w)` que
        hace esta ruta (escalar aquí, espejar después en
        `_mirror_weak_point`). Ambas sólo coinciden con `s == 1`; a
        `escala=1.25` (fase 2) difieren en `W_vivo·(s−1)` px sin importar el
        punto débil -- ver el test canario de B-050 en test_adopcion_v3.py.
        Retirar esta compensación (y `_resolver_punto_debil`) en cuanto el
        motor corrija el orden de `rect_for` -- ese test avisará.
        """
        factor = self._factor_de_escala()
        if factor == 1.0:
            return point
        return WeakPoint(
            offset=(int(round(point.offset[0] * factor)),
                    int(round(point.offset[1] * factor))),
            size=(int(round(point.size[0] * factor)),
                  int(round(point.size[1] * factor))),
            multiplier=point.multiplier,
            phases=point.phases,
            label=point.label,
        )

    def _y_de_suelo(self) -> float:
        """GROUND_Y re-derivada de la altura viva: los pies siempre en FLOOR_Y.

        GROUND_Y está calculada con la altura canónica de 48px; usarla cruda con
        el cuerpo escalado a 60px hundiría las pezuñas 12px dentro del piso
        durante toda la ventana de castigo de STOMP."""
        return FLOOR_Y - float(self.rect.height)

    def _y_de_banda_de_embestida(self) -> float:
        """CHARGE_BAND_Y re-derivada igual que _y_de_suelo, conservando los 12px
        de aire bajo las pezuñas que hacen que rect.bottom caiga en el valle de
        la senoidal (banda alcanzable cuerpo a cuerpo, H-08)."""
        return FLOOR_Y - float(self.rect.height) - CHARGE_BAND_GAP

    def _build_hitbox(self) -> pygame.Rect:
        # 17_BOSS_SPEC §3.2, espacio local CRUDO. Adopción AUD-606: ya NO se
        # escala aquí -- `cajas_siguen_al_cuerpo = True` (constante de clase)
        # le deja el escalado a `BossBase._escalar_local`, que con factor
        # 1.25 produce Rect(8, 5, 45, 55) sobre este mismo rect (misma
        # aritmética round() que el `_escalar_rect_local` retirado).
        return pygame.Rect(6, 4, 36, 44)

    def _build_hurtbox(self) -> pygame.Rect:
        # 30x40 centrado en 48x48 (local), CRUDO -- ver _build_hitbox. Con
        # factor 1.25 el motor produce Rect(11, 5, 38, 50).
        return pygame.Rect(9, 4, 30, 40)

    def _mirror_weak_point(self, point: WeakPoint) -> WeakPoint:
        """Refleja un WeakPoint canónico (mirando a la derecha) según la orientación actual.

        boss_kit.WeakPoint.rect_for() no tiene ninguna noción de
        facing_direction -- verificado contra el boss de referencia
        (reference/v2_boss_profesor/src/boss_venado.py), que tampoco refleja
        nunca sus propios puntos débiles. Pero NUESTRO sprite SÍ se voltea
        horizontalmente cuando facing_direction < 0 (boss_base.py draw(),
        pygame.transform.flip(frame, True, False) dentro del mismo lienzo de
        48px de ancho que self.rect.width, sin ningún desplazamiento extra de
        blit ya que self.rect coincide exactamente con el lienzo del sprite --
        ver boss_base.py draw(), ox=(rect.width-sprite_fw)//2==0 para este
        boss). Sin esto, un golpe sobre los cuernos visualmente reflejados se
        resolvería silenciosamente contra el rect del flanco (o contra nada)
        en su lugar. Refleja offset.x de la misma manera que lo hace
        pygame.transform.flip: mirrored_x = width - offset.x - size.x.
        offset.y queda intacto -- el volteo es solo horizontal.

        Adopción V3 (H-20): `self.rect.width` ya no es siempre 48 -- la fase 2
        declara `escala=1.25` y el cuerpo pasa a 60px. Esto sigue siendo
        correcto porque lee el ancho VIVO, pero exige que quien llame ya haya
        pasado el punto por `_escalar_weak_point`: espejar un offset canónico
        contra un ancho escalado daría un reflejo desplazado.

        Compensación B-050 (adopción AUD-606, ver `_escalar_weak_point`):
        este espejado sigue viviendo aquí -- y no delegado en el parámetro
        `facing` de `WeakPoint.rect_for` -- porque ese parámetro espeja
        contra el ancho YA escalado y compone con `escala` en el orden
        equivocado. Retirar junto con `_escalar_weak_point` cuando el motor
        lo corrija.
        """
        if self.facing_direction >= 0:
            return point
        mirrored_x = self.rect.width - point.offset[0] - point.size[0]
        return WeakPoint(
            offset=(mirrored_x, point.offset[1]),
            size=point.size,
            multiplier=point.multiplier,
            phases=point.phases,
            label=point.label,
        )

    # ──────────────────────────────────────────────
    # Movimiento
    # ──────────────────────────────────────────────
    def _approach_y(self, target: float, dt: float) -> bool:
        """Corrección de diseño H-04/H-08: mueve position.y hacia el objetivo,
        limitado a VERTICAL_ATTACK_SPEED*dt por frame. Reutilizado por el
        plantado en el suelo de STOMP, el barrido de la banda cuerpo a cuerpo
        de CHARGE, y la recuperación de y posterior al ataque más abajo -- sin
        teletransporte instantáneo en ninguno de los tres casos. Devuelve True
        en cuanto position.y aterriza exactamente en el objetivo (la
        diferencia restante cupo dentro del presupuesto de paso de este
        frame) para que quienes llaman puedan saber que la recuperación
        terminó SIN un segundo ajuste con umbral propio encima de este --
        una versión anterior volvía a comprobar la distancia después del
        paso contra su propia tolerancia de ~2px y ajustaba de nuevo cuando
        estaba por debajo, lo que podía sumar hasta ~2px encima del paso ya
        limitado en el mismo frame (detectado por
        test_y_recovery_after_attack_is_bounded_no_teleport)."""
        delta = target - self.position.y
        step = VERTICAL_ATTACK_SPEED * dt
        if abs(delta) <= step:
            self.position.y = target
            return True
        self.position.y += step if delta > 0 else -step
        return False

    def _actualizar_picado_de_barrido(self, dt: float) -> None:
        """B-039 opción C (REGISTRO-DE-BUGS.md, decisión del usuario
        2026-08-23): mientras dura el AVISO de VINE_SWEEP en fase 2
        (``self._telegraph == "VINE_SWEEP"``, antes de que la oleada se
        dispare), desplaza ``position.x`` en línea recta hacia un punto a
        ``ATERRIZAJE_BARRIDO`` px del centro del jugador, por el mismo LADO
        en que el jefe ya estaba al armar el ataque (``_sweep_lado_picado``,
        fijado en ``_try_attack`` -- nunca se recalcula a mitad de camino,
        así que el picado jamás cruza por encima del jugador). El paso está
        acotado a ``VEL_PICADO * dt`` por fotograma, mismo patrón que
        ``_approach_y``: nunca teletransporta. Como quien llama a este
        método ya movió ``position.y`` hacia ``_y_de_suelo()`` en el mismo
        fotograma, el resultado se lee como un picado diagonal, no como un
        salto seguido de una caída recta.

        El destino se recorta SIEMPRE al mismo margen de pared que usa el
        resto del movimiento en el suelo (``ARENA_X0+32`` /
        ``ARENA_X1-32-ancho``, riesgo 4 del dictamen doc-guardian) para que
        un jugador pegado a cualquier pared no empuje el aterrizaje fuera de
        la arena."""
        pr = self._player_ref
        if pr is None:
            return
        destino_centro = pr.centerx + self._sweep_lado_picado * ATERRIZAJE_BARRIDO
        destino_x = destino_centro - float(self.rect.width) / 2.0
        minimo = ARENA_X0 + 32.0
        maximo = ARENA_X1 - 32.0 - float(self.rect.width)
        destino_x = max(minimo, min(destino_x, maximo))
        delta = destino_x - self.position.x
        paso = VEL_PICADO * dt
        if abs(delta) <= paso:
            self.position.x = destino_x
        else:
            self.position.x += paso if delta > 0 else -paso

    def _update_movement(self, dt: float) -> None:
        if not self.phases or self.current_phase >= len(self.phases):
            return
        if self._charge_active:
            return                        # la embestida sobrescribe el patrón base (_update_charge también controla y)
        # corrección del Hallazgo C: congela X durante todo el ciclo de
        # telegraph+window+recover de STOMP y durante la pausa de pared de
        # CHARGE -- el antiguo desplazamiento senoidal seguía moviendo
        # position.x durante todo STOMP, socavando la suposición de los bots
        # de un objetivo de castigo cuasi-estático (FINDINGS.md Hallazgo C,
        # punto 1). STOMP sigue plantándose en el suelo vía _approach_y
        # (que ahora también cubre el recover, no solo el telegraph+window)
        # para que la ventana de castigo se mantenga en el suelo; la pausa de
        # pared de CHARGE no necesita manejo extra de Y -- _update_charge ya
        # la barrió hacia la banda cuerpo a cuerpo justo antes de que la
        # embestida se detuviera, y este return anticipado simplemente deja
        # esa posición tal cual. _y_recovering se activa más adelante, por
        # _update_attack_state, una vez que expira el temporizador de recover
        # correspondiente -- ya no aquí (ver ese método).
        #
        # B-039 opción C (REGISTRO-DE-BUGS.md): el AVISO de VINE_SWEEP es la
        # ÚNICA excepción a "grounded_punish congela X" -- mientras dura
        # (self._telegraph == "VINE_SWEEP", antes de que la oleada se
        # dispare y arranque el enraizado real) la X SÍ se mueve, picando en
        # diagonal hacia el jugador vía _actualizar_picado_de_barrido más
        # abajo. Una vez disparada la oleada (self._sweep_rooted > 0) vuelve
        # a valer el criterio de arriba: X congelada, mismo trato que STOMP.
        grounded_punish = (self._telegraph == "STOMP" or self._stomp_window > 0
                            or self._stomp_recover > 0
                            or self._telegraph == "VINE_SWEEP" or self._sweep_rooted > 0)
        if grounded_punish or self._charge_recover > 0:
            if grounded_punish:
                aterrizo = self._approach_y(self._y_de_suelo(), dt)   # H-20: altura viva, no GROUND_Y cruda
                # pulido AAA (spec §2.1): polvo dirigido hacia arriba en el instante
                # exacto del aterrizaje (primer frame en que _approach_y llega al
                # suelo durante el aviso de VINE_SWEEP) -- _sweep_aterrizo evita
                # repetirlo cada frame mientras el jefe se queda plantado.
                if self._telegraph == "VINE_SWEEP" and aterrizo and not self._sweep_aterrizo:
                    self._sweep_aterrizo = True
                    self.efectos.particulas_dirigidas(
                        float(self.rect.centerx), FLOOR_Y, -90.0, POLVO_ATERRIZAJE)
                # B-039-C: picado diagonal -- SOLO durante el aviso (no
                # durante el enraizado posterior) y solo en fase 2 (guardia
                # explícita por claridad de diseño: VINE_SWEEP hoy sólo vive
                # en phases[1].attack_patterns, así que en la práctica esta
                # condición coincide siempre con self._telegraph == "VINE_SWEEP").
                if self._telegraph == "VINE_SWEEP" and self.current_phase >= 1:
                    self._actualizar_picado_de_barrido(dt)
            return
        phase = self.phases[self.current_phase]
        speed = DRIFT_SPEED * phase.speed_multiplier

        if phase.movement_type == "sine":
            self._elapsed += dt
            self.position.x += speed * dt * self.facing_direction
            target_y = self._base_y + SINE_AMPLITUDE * math.sin(
                2 * math.pi * SINE_FREQ * self._elapsed)
            if self._y_recovering:
                # recuperación H-04/H-08: sin salto de vuelta a la fórmula
                # senoidal -- suaviza hacia ella al mismo ritmo limitado, y
                # se re-bloquea en el instante en que _approach_y aterriza
                # exactamente en target_y.
                if self._approach_y(target_y, dt):
                    self._y_recovering = False
            else:
                self.position.y = target_y
            # m-1: el tope derecho se calcula con el ancho VIVO del cuerpo, no
            # con el 80 (=48+32) que salía de dar por sentado el sprite de fase
            # 1. `position.x` es la esquina izquierda, así que lo que hay que
            # dejar libre es el ancho actual más los 32px de hueco cuerpo a
            # cuerpo; con el venado agrandado por `escala`, el número fijo
            # metía 12px de anca dentro de la pared. El tope izquierdo no
            # depende del ancho -- ahí la esquina izquierda ES el borde.
            tope_derecho = ARENA_X1 - 32.0 - float(self.rect.width)
            if self.position.x < ARENA_X0 + 32:   # el margen de límite izquierdo mantiene al boss alejado de la pared
                self.position.x = ARENA_X0 + 32
                self.facing_direction = 1
            elif self.position.x > tope_derecho:
                self.position.x = tope_derecho
                self.facing_direction = -1
        elif phase.movement_type == "bezier" and self._bezier_path:
            avance = 0.12 * dt * phase.speed_multiplier * self._bezier_dir  # ~8.3 s por tramo de la figura en ocho a velocidad 1x
            if self._sweep_despegue > 0:
                # B-043: rampa ease-in de arranque tras el enraizado del
                # barrido (ver SWEEP_DESPEGUE) -- restante ya viene
                # decrementado por _update_attack_state en este mismo
                # fotograma (corre antes que _update_movement dentro de
                # update()), así que factor_despegue pasa de ~0 (recién
                # expirado el enraizado) a 1 (rampa cerrada) de forma
                # continua, cuadrática, nunca de golpe.
                restante = min(self._sweep_despegue, SWEEP_DESPEGUE)
                factor_despegue = (1.0 - restante / SWEEP_DESPEGUE) ** 2
                avance *= factor_despegue
            self._bezier_t += avance
            # Ping-pong en los extremos: invierte la dirección en lugar de saltar
            # de vuelta a t=0, lo que evita un teletransporte visual a través
            # de toda la figura en ocho.
            if self._bezier_t >= 1.0:
                self._bezier_t, self._bezier_dir = 1.0, -1
            elif self._bezier_t <= 0.0:
                self._bezier_t, self._bezier_dir = 0.0, 1
            px, py = CurveTools.sample_path(self._bezier_path, self._bezier_t)
            self.position.x = px
            if self._y_recovering:
                # Misma técnica de recuperación H-08 que la rama senoidal, pero
                # suavizando hacia la y de la trayectoria de la figura en ocho
                # en lugar de la fórmula senoidal.
                if self._approach_y(py, dt):
                    self._y_recovering = False
            else:
                self.position.y = py

    def _caida_de_figura8(self) -> float:
        """Amplitud vertical efectiva de la figura en ocho, acotada por el suelo.

        m-2: la curva pasa EXACTAMENTE por sus extremos (P0 y P5), y P5 es el
        que lleva la caída, así que el punto más bajo del vuelo es
        `_base_y + caída` y los pies quedan una altura de cuerpo por debajo.
        Con la amplitud nominal de FIGURE8_DIP y el cuerpo agrandado de la fase
        2 esa cuenta da 505+60=565, cinco píxeles por dentro del piso: el venado
        se hundía en el terreno en cada pasada por el vértice inferior. Aquí la
        amplitud se recorta a lo que quepa entre el centro del ocho y FLOOR_Y
        descontando la altura viva, de modo que las pezuñas rozan el suelo como
        mucho. En fase 1 (48px) la holgura es de 52 y no recorta nada: se
        conserva la amplitud de diseño."""
        holgura = FLOOR_Y - float(self.rect.height) - self._base_y
        return min(FIGURE8_DIP, max(0.0, holgura))

    def _build_figure8_path(self) -> list[tuple[float, float]]:
        """Oficial §3.5: figura en ocho precalculada, 6 puntos de control, Bezier de grado 5.

        La amplitud vertical no es una constante suelta sino lo que devuelve
        `_caida_de_figura8()`: 45 con el cuerpo canónico de 48px (extremo en
        y=505, pies en 553) y 40 con el cuerpo de 60px de la fase 2 (extremo en
        y=500, pies justo en FLOOR_Y). Los cuatro puntos interiores solo tiran
        de la curva y nunca se alcanzan, así que basta con acotar el extremo
        para garantizar que el vuelo entero se queda sobre el suelo y dentro de
        la banda alcanzable cuerpo a cuerpo.

        Se reconstruye en cada entrada a una fase bezier, DESPUÉS de que el
        motor haya aplicado la escala: si se cacheara una sola vez, el recorte
        de arriba se calcularía con la altura equivocada.
        """
        cy = self._base_y
        dip = self._caida_de_figura8()
        pts = [
            (ARENA_X0 + 60.0,  cy),
            (ARENA_CX - 120.0, cy - dip),
            (ARENA_CX + 120.0, cy + dip),
            (ARENA_X1 - 110.0, cy),
            (ARENA_CX + 120.0, cy - dip),
            (ARENA_CX - 120.0, cy + dip),
        ]
        return CurveTools.bezier(pts, 64)              # Unidad III

    def _t_mas_cercano_en_ruta(self, ruta: list[tuple[float, float]]) -> float:
        """H-24/B-028 (FINDINGS.md, zona H-24): al reanudar el vuelo bezier de
        la fase 2, fijar `_bezier_t = 0.0` a secas apuntaba siempre a
        `ruta[0]` -- la pared izquierda de la arena -- sin importar dónde
        había quedado el cuerpo tras el teletransporte al centro (adopción
        V3, Cambio 5). Resultado medido: un salto de ~272-307px en el primer
        fotograma de vuelo. Esta proyección busca, en cambio, el punto de la
        propia polilínea de 64 muestras MÁS CERCANO a `self.position` y
        devuelve su t en la MISMA parametrización que usa
        `CurveTools.sample_path` (`t = (i + frac) / (n - 1)`), así que
        retomar el vuelo desde ahí no mueve el cuerpo de golpe -- solo lo
        re-engancha a la curva que ya tenía encima.

        Decisión consciente de desempate: la figura en ocho se auto-cruza en
        el centro, así que dos segmentos de ramas distintas pueden quedar
        casi empatados en distancia. El argmin usa `<` estricto, así que
        ante un empate se queda con el de ÍNDICE MENOR (la rama temprana de
        la polilínea) -- cualquiera de las dos ramas elimina el salto por
        igual; esta elección solo decide la dirección estética con la que
        arranca el vuelo, y FINDINGS (zona H-24) la deja registrada como
        decisión de implementación, no como un segundo bug.
        """
        if len(ruta) < 2:
            return 0.0
        pos = pygame.Vector2(self.position)
        n = len(ruta)
        mejor_dist2: float | None = None
        mejor_t = 0.0
        for i in range(n - 1):
            p0 = pygame.Vector2(ruta[i])
            p1 = pygame.Vector2(ruta[i + 1])
            d = p1 - p0
            largo2 = d.length_squared()
            if largo2 > 0.0:
                frac = (pos - p0).dot(d) / largo2
                frac = max(0.0, min(1.0, frac))
            else:
                frac = 0.0
            punto = p0 + d * frac
            dist2 = (pos - punto).length_squared()
            if mejor_dist2 is None or dist2 < mejor_dist2:
                mejor_dist2 = dist2
                mejor_t = (i + frac) / (n - 1)
        return mejor_t

    def _reanclar_bezier_al_reanudar(self) -> None:
        """B-041 (REGISTRO-DE-BUGS.md): re-engancha `_bezier_t` a la posición
        real justo cuando el jefe SALE de una ventana plantada de fase 2
        (recuperación de la pared de CHARGE, enraizado de VINE_SWEEP).

        Mientras el cuerpo está plantado, `_update_movement` retorna antes
        de avanzar `_bezier_t` (ver el `return` anticipado más arriba), así
        que el parámetro queda CONGELADO apuntando a donde iba la curva
        cuando arrancó la ventana -- mientras el cuerpo real se movió a la
        pared o al suelo. Al reanudar, la asignación directa
        `self.position.x = px` de la rama bezier saltaba de golpe al punto
        viejo de la curva sin importar cuán lejos quedara del cuerpo real
        (medido: hasta 501px, 18 veces por pelea). Mismo remedio que
        H-24/B-028 (que ya resuelve el caso análogo al ENTRAR a fase 2, en
        `_finish_phase_transition`): buscar el punto de la polilínea MÁS
        CERCANO a `self.position` y retomar el vuelo desde ahí.

        Guardia de fase: sólo tiene sentido si la fase activa declara
        movimiento bezier y ya calculó su ruta -- llamarlo en cualquier otro
        momento (p. ej. si algún día una ventana plantada existiera también
        en fase 1, de movimiento senoidal) sería un no-op silencioso."""
        if not self.phases or self.current_phase >= len(self.phases):
            return
        fase = self.phases[self.current_phase]
        if fase.movement_type == "bezier" and self._bezier_path:
            self._bezier_t = self._t_mas_cercano_en_ruta(self._bezier_path)

    # ──────────────────────────────────────────────
    # Ataques
    # ──────────────────────────────────────────────
    def _try_attack(self, pattern: str) -> None:
        pr = self._player_ref
        if pr is None:
            return
        if pattern == "STOMP":
            if abs(pr.centerx - self.rect.centerx) <= 96:
                self._telegraph, self._telegraph_timer = "STOMP", STOMP_TELEGRAPH
                self._attack_timers[pattern] = self._attack_cooldowns[pattern]
        elif pattern == "CHARGE":
            if (pr.centerx < ARENA_CX) != (self.rect.centerx < ARENA_CX):
                self._telegraph, self._telegraph_timer = "CHARGE", CHARGE_TELEGRAPH
                self._attack_timers[pattern] = self._attack_cooldowns[pattern]
        elif pattern == "VINE_TOSS":
            self._telegraph, self._telegraph_timer = "VINE_TOSS", TOSS_TELEGRAPH
            self._attack_timers[pattern] = self._attack_cooldowns[pattern]
            # B-040 (REGISTRO-DE-BUGS.md): el contrato del profesor
            # (test_boss_encounter.py::test_every_attack_produces_something_observable)
            # espera un proyectil ya en _projectiles en el MISMO fotograma en que
            # se arma el ataque -- desde H-23 el disparo real no ocurre hasta que
            # expira el telegraph. Se deja aquí un marcador INERTE: sin "pos" (por
            # lo que el bucle de colisión de _check_player_contact y el de
            # _draw_projectiles lo saltan de largo por sí solos, ya que ambos
            # exigen "pos" in proj) y con inert=True sin ambigüedad para quien
            # necesite filtrarlo explícitamente. Su vida es exactamente la
            # duración del telegraph: se retira en _update_attack_state al
            # resolverse (dispare o no el real) o en _cancelar_ataques_en_vuelo
            # si el windup se corta antes.
            self._projectiles.append({"type": "vine", "inert": True, "alive": True, "damage": 0.0})
        elif pattern == "VINE_SWEEP":
            self._telegraph, self._telegraph_timer = "VINE_SWEEP", SWEEP_TELEGRAPH
            self._sweep_aterrizo = False   # nuevo windup: todavía no aterrizó (ver _update_movement)
            # B-039-C: el lado del picado se fija UNA sola vez, al armar el
            # aviso, según el lado en que el jefe YA está respecto al jugador
            # en ese instante -- ver _actualizar_picado_de_barrido/
            # _sweep_lado_picado. `pr` ya viene garantizado no-None por el
            # guard de arriba de este método.
            self._sweep_lado_picado = 1 if self.rect.centerx >= pr.centerx else -1
            self._attack_timers[pattern] = self._attack_cooldowns[pattern]
        elif pattern == "MUSHROOM_SPORE":
            self._telegraph, self._telegraph_timer = "MUSHROOM_SPORE", SPORE_TELEGRAPH
            self._attack_timers[pattern] = self._attack_cooldowns[pattern]
            # B-040: mismo marcador inerte que VINE_TOSS arriba, por triplicado --
            # el contrato del profesor cuenta 3 esporas ("spore") de inmediato.
            for _ in range(3):
                self._projectiles.append({"type": "spore", "inert": True, "alive": True, "damage": 0.0})

    def _update_attack_state(self, dt: float) -> None:
        # Reloj/contador de VFX del pulido AAA (spec 2026-08-21 §2.1): avanza en
        # cada tick real de ataque -- tanto desde update() como desde los tests
        # que llaman a este método directamente -- para que cada_n_frames() y las
        # oscilaciones basadas en self._t_vfx (p. ej. dibujar_mundo de la oleada)
        # tengan un reloj con el que trabajar.
        self._frames_vfx += 1
        self._t_vfx += dt
        if self.is_transitioning:
            return
        for k in self._attack_timers:
            if self._attack_timers[k] > 0:
                self._attack_timers[k] -= dt
        if self._telegraph:
            self._telegraph_timer -= dt
            if self._telegraph_timer <= 0:
                pattern, self._telegraph = self._telegraph, ""
                # B-040: el marcador inerte armado en _try_attack (si lo hay --
                # sólo VINE_TOSS/MUSHROOM_SPORE lo dejan) ya cumplió su función
                # de dejar algo observable durante el windup; se retira aquí
                # tanto si el ataque real sale (ramas de abajo) como si no
                # (jugador ausente, ver los "if pr is not None" siguientes): su
                # vida nunca excede la del telegraph que lo armó. No-op para
                # STOMP/CHARGE/VINE_SWEEP, que nunca dejan marcadores inertes.
                self._projectiles = [p for p in self._projectiles if not p.get("inert")]
                if pattern == "STOMP":
                    self._do_stomp()
                elif pattern == "CHARGE":
                    self._do_charge()
                elif pattern == "VINE_TOSS":
                    # riesgo 2 del dictamen de la campaña de fairness: se relee
                    # self._player_ref FRESCO en el instante del disparo -- NO la
                    # posición capturada al armar el windup -- para que la
                    # predicción de la liana apunte a donde el jugador está
                    # AHORA. Si ya no hay jugador (None), guarda silenciosa: no dispara.
                    pr = self._player_ref
                    if pr is not None:
                        self._do_vine_toss(pr)
                elif pattern == "VINE_SWEEP":
                    # pulido AAA (spec 2026-08-21 §2.1): dos oleadas viajeras en vez
                    # de una franja estática de ancho completo -- nacen a los lados
                    # del centro del jefe y recorren la arena hasta la pared o hasta
                    # golpear (ver _check_player_contact/OleadaDeLianas).
                    cx = float(self.rect.centerx)
                    izq = OleadaDeLianas(cx - OLEADA_SEPARACION, -1, FLOOR_Y, ARENA_X0, ARENA_X1)
                    der = OleadaDeLianas(cx + OLEADA_SEPARACION, 1, FLOOR_Y, ARENA_X0, ARENA_X1)
                    self._oleadas.append(izq)
                    self._oleadas.append(der)
                    self._sweep_rooted = SWEEP_ROOTED
                    if self._event_bus is not None:
                        # decisión del usuario 2026-08-21: la oleada doble SÍ emite
                        # Events.BOSS_ATTACK -- retira el candado del Hallazgo D
                        # (FINDINGS.md), que protegía al dodger viejo cuando este
                        # ataque no emitía ninguna señal. Los bots se co-calibran a
                        # esta emisión en la misma iteración (playtest/bots.py):
                        # _decide_sweep_dodge ya no depende de este evento (lee
                        # oleadas_activas() directo), pero _on_attack sí necesita
                        # ignorarlo explícitamente para no disparar la huida
                        # reactiva genérica encima de la esquiva dedicada.
                        self._event_bus.emit(Events.BOSS_ATTACK, pattern="VINE_SWEEP",
                                             rect=izq.rect.union(der.rect))
                        self._event_bus.emit(Events.SFX_BOSSES_VENADO_VINE)
                elif pattern == "MUSHROOM_SPORE":
                    # mismo criterio que VINE_TOSS arriba: posición fresca en el
                    # instante del disparo, guarda silenciosa si no hay jugador.
                    pr = self._player_ref
                    if pr is not None:
                        self._do_mushroom_spore(pr)
                # las ventanas recién abiertas no deben decaer en el mismo tick (saltos de dt sin acotar)
                return
        if self._stomp_window > 0:
            self._stomp_window -= dt
            if self._stomp_window <= 0:
                self._stomp_rect = None
                # corrección del Hallazgo C: entrega el control a un recover de castigo
                # en el suelo, inofensivo, en lugar de activar _y_recovering
                # directamente aquí (ver test_stomp_has_grounded_punish_recover).
                # El `elif` de abajo no puede dispararse en esta misma
                # llamada -- solo entramos a este `if` porque _stomp_window ya
                # era >0 antes del decremento -- así que el recover recién
                # activado no pierde un tick, en el mismo espíritu que el
                # `return` anticipado del propio telegraph más arriba.
                self._stomp_recover = STOMP_RECOVER
        elif self._stomp_recover > 0:
            self._stomp_recover -= dt
            if self._stomp_recover <= 0:
                self._y_recovering = True
        if self._charge_recover > 0:
            # corrección del Hallazgo C: la propia ventana de castigo de pausa
            # estacionaria en la pared de CHARGE (activada por _update_charge
            # al detenerse en la pared).
            self._charge_recover -= dt
            if self._charge_recover <= 0:
                self._y_recovering = True
                self._reanclar_bezier_al_reanudar()   # B-041: ver docstring del método
        # B-043: decrementa la rampa de despegue ANTES del bloque de abajo --
        # así, en el propio fotograma en que _sweep_rooted expira y arma
        # self._sweep_despegue = SWEEP_DESPEGUE, ese valor recién armado NO
        # se descuenta todavía en este mismo tick (llega intacto a
        # _update_movement); el primer descuento real le toca al fotograma
        # SIGUIENTE, dándole a la rampa su ventana completa de SWEEP_DESPEGUE
        # segundos.
        if self._sweep_despegue > 0:
            self._sweep_despegue = max(0.0, self._sweep_despegue - dt)
        if self._sweep_rooted > 0:
            self._sweep_rooted -= dt
            if self._sweep_rooted <= 0:
                self._sweep_rooted = 0.0
                self._y_recovering = True
                self._reanclar_bezier_al_reanudar()   # B-041: mismo remedio que arriba
                self._sweep_despegue = SWEEP_DESPEGUE  # B-043: arranca la rampa DESPUÉS del reanclaje, desde ese t
        for oleada in self._oleadas:
            oleada.update(dt)
            if oleada.viva:
                if cada_n_frames(self._frames_vfx, 4):
                    self.efectos.particulas(float(oleada.rect.centerx), FLOOR_Y, TIERRA_OLEADA)
            elif oleada.murio_en_pared:
                pared_x = oleada.x_min if oleada.direccion < 0 else oleada.x_max
                self.efectos.particulas(pared_x, FLOOR_Y, TIERRA_OLEADA)
                self.efectos.particulas(pared_x, FLOOR_Y, TIERRA_OLEADA)
        self._oleadas = [o for o in self._oleadas if o.viva]

    def _update_vfx(self, dt: float) -> None:
        """Piezas puramente cosméticas del pulido AAA de fase 2 (§2.2-2.4):
        avance de la cresta de tierra del pisotón y todas las ráfagas de
        partículas de CADENCIA (estela/polvo que se repiten cada N
        fotogramas mientras dura un estado, a diferencia de las ráfagas de
        un solo disparo que ya arman _do_stomp/_do_mushroom_spore/
        _update_charge). Se llama una sola vez por fotograma desde update(),
        INMEDIATAMENTE DESPUÉS de _update_attack_state (Duda 4 resuelta en
        la addenda del revisor: ahí mismo deja la Parte 1 el update() de las
        oleadas) y ANTES de _update_projectiles -- el polen de las esporas
        (más abajo) lee entonces la posición del proyectil del fotograma
        ANTERIOR, un frame de rezago cosmético e imperceptible a 60fps.

        Las cadencias se expresan en fotogramas de update() (cada_n_frames
        sobre self._frames_vfx), no en tiempo real -- el arnés QA corre a dt
        fijo y determinista; expresarlas en segundos de reloj de pared haría
        que dos corridas idénticas emitieran partículas en instantes
        distintos según la carga de la máquina."""
        if self._cresta_pisoton is not None:
            self._cresta_pisoton.update(dt)
            if not self._cresta_pisoton.viva:
                self._cresta_pisoton = None
        self._fantasmas.update(dt)
        cx = float(self.rect.centerx)
        # (B) del coordinador, Task 14 (2026-08-22): el aviso de STOMP ya NO
        # pide estela() -- ese rectángulo verde del motor se quedaba encima
        # del ciervo casi entero mientras apenas se movía (zoom_stomp.png
        # f1800-f1826). Sin reemplazo: el jefe no se desplaza lo suficiente
        # durante el aviso como para necesitar un rastro.
        if self._stomp_recover > 0 and cada_n_frames(self._frames_vfx, 10):
            self.efectos.particulas(cx, FLOOR_Y, POLVO_ASENTANDOSE)
        if self._telegraph == "MUSHROOM_SPORE" and cada_n_frames(self._frames_vfx, 4):
            self.efectos.particulas_dirigidas(cx, float(self.rect.top), -90.0, MOTAS)
        for proj in self._projectiles:
            # B-040: el marcador inerte de MUSHROOM_SPORE también es
            # type="spore" y alive=True mientras dura el windup -- sin este
            # guard, "pos" in proj revienta con KeyError la primera vez que
            # la cadencia de 5 fotogramas cae dentro de un telegraph todavía
            # armado (detectado por playtest/tests/test_bots.py::
            # test_el_dodger_esquiva_oleadas_reales_en_fase_2, vía la
            # simulación real que arma session.reset()).
            if (not proj.get("inert") and proj.get("type") == "spore" and proj.get("alive")
                    and cada_n_frames(self._frames_vfx, 5)):
                pos = proj["pos"]
                self.efectos.particulas(pos.x, pos.y, POLEN)
        if self.current_phase >= 1:
            # §2.4: la embestida solo lleva este pulido en fase 2 -- en fase
            # 1 el spec la deja fuera (el frenazo de la animación "charge" ya
            # se siente sin VFX adicional).
            if self._telegraph == "CHARGE" and cada_n_frames(self._frames_vfx, 4):
                signo = self._sign_to_player()
                self.efectos.particulas_dirigidas(
                    cx - signo * 16.0, FLOOR_Y - 4.0,
                    180.0 if signo > 0 else 0.0, POLVO_RASPADO)
            if self._charge_active:
                if cada_n_frames(self._frames_vfx, 3):
                    # (B) del coordinador, Task 14: fantasma de SPRITE (no
                    # el rectángulo verde de estela()) -- _frame_vivo()
                    # devuelve None si la animación actual no tiene frames
                    # cargados (grader/arnés headless sin sprites reales).
                    vivo = self._frame_vivo()
                    if vivo is not None:
                        frame, destino, _clave = vivo
                        self._fantasmas.agregar(frame, destino)
                if cada_n_frames(self._frames_vfx, 4):
                    self.efectos.particulas_dirigidas(
                        cx - self._charge_direction * 16.0, float(self.rect.bottom),
                        180.0 if self._charge_direction > 0 else 0.0, POLVO_PEZUNAS)
            # B-043 (REGISTRO-DE-BUGS.md, addendum 2026-08-23): mismo rastro
            # de sprite que la embestida de arriba, esta vez durante el
            # picado de barrido (self._telegraph == "VINE_SWEEP", el jefe
            # avanza de verdad hacia el jugador) y la rampa de despegue
            # posterior (self._sweep_despegue > 0) -- ambas fases mueven el
            # cuerpo lo suficiente como para merecer el mismo rastro visual.
            if self._telegraph == "VINE_SWEEP" or self._sweep_despegue > 0:
                if cada_n_frames(self._frames_vfx, 3):
                    vivo = self._frame_vivo()
                    if vivo is not None:
                        frame, destino, _clave = vivo
                        self._fantasmas.agregar(frame, destino)

    def _do_stomp(self) -> None:
        self._stomp_rect = pygame.Rect(
            self.rect.centerx - 48, int(FLOOR_Y) - 8, 96, 8)
        self._stomp_window = STOMP_WINDOW
        # §2.2: peso del impacto -- sacudida vertical, polvo hacia arriba
        # desde el punto de impacto, hojas sueltas, destello blanco del
        # sprite y la cresta de tierra que se separa del centro. Ninguno de
        # estos cinco toca _stomp_rect/_stomp_window (arriba): el rect de
        # daño y los tiempos oficiales no cambian.
        cx = float(self.rect.centerx)
        self.efectos.sacudir(4.0, 0.2, (0.0, 1.0))
        self.efectos.particulas_dirigidas(cx, FLOOR_Y, -90.0, POLVO_PISOTON)
        self.efectos.particulas(cx, FLOOR_Y - 20.0, HOJAS)
        self._flash_frames = FLASH_PISOTON_FRAMES
        self._cresta_pisoton = CrestaDePisoton(cx, FLOOR_Y)
        if self._event_bus is not None:
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="STOMP", rect=self._stomp_rect)
            self._event_bus.emit(Events.SFX_BOSSES_VENADO_STOMP)

    def _do_charge(self) -> None:
        pr = self._player_ref
        if pr is None:
            return
        to_player = pygame.Vector2(pr.centerx - self.rect.centerx, 0.0)
        if to_player.length_squared() == 0:
            to_player = pygame.Vector2(float(self.facing_direction), 0.0)
        direction = vec2_normalize(to_player)               # Unidad II: vec2_normalize
        self._charge_direction = 1 if direction.x >= 0 else -1
        self.facing_direction = self._charge_direction
        self._charge_active = True
        if self._event_bus is not None:
            # paridad H-08 con _do_stomp: sin esto, CHARGE se ejecuta (el boss
            # embiste) pero nada observable lo anuncia nunca.
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="CHARGE", rect=self.rect)
            self._event_bus.emit(Events.SFX_BOSSES_VENADO_CHARGE)

    def _update_charge(self, dt: float) -> None:
        if not self.phases or self.current_phase >= len(self.phases):
            return
        # la embestida se detiene más cerca de la pared que los márgenes de la
        # senoidal (32/80) de arriba -- mantener 16<32 y 64<80 o
        # facing_direction puede terminar apuntando hacia la pared después de
        # detenerse en ella (el re-clamp de la senoidal se autocorrige en 1 frame)
        speed = CHARGE_SPEED_P1 if self.current_phase == 0 else CHARGE_SPEED_P2
        self.position.x += self._charge_direction * speed * dt
        # H-08: barre hacia abajo hasta la banda cuerpo a cuerpo mientras embiste.
        # H-20: la banda se re-deriva de la altura viva (ver _y_de_banda_de_embestida).
        self._approach_y(self._y_de_banda_de_embestida(), dt)
        # m-1: mismo criterio que el tope de la senoidal, con el hueco reducido a
        # 16px -- la embestida SÍ debe terminar pegada a la pared. Derivarlo del
        # ancho vivo mantiene además la relación 16<32 que exige el comentario de
        # arriba cuando el cuerpo crece: con los números fijos, en fase 2 el tope
        # de la embestida caía POR DENTRO del de la senoidal y el reajuste del
        # fotograma siguiente empujaba al venado de vuelta.
        tope_derecho = ARENA_X1 - 16.0 - float(self.rect.width)
        if self.position.x <= ARENA_X0 + 16 or self.position.x >= tope_derecho:
            # §2.4: capturado ANTES del clamp de la línea siguiente -- una
            # vez clamped, position.x ya está pegado a la pared y pierde la
            # distinción de cuál de las dos lo detuvo.
            choco_contra_pared_derecha = self.position.x >= tope_derecho
            self.position.x = max(ARENA_X0 + 16, min(self.position.x, tope_derecho))
            self._charge_active = False
            # corrección del Hallazgo C: pausa en la pared durante
            # CHARGE_WALL_PAUSE segundos (una ventana de castigo estacionaria
            # -- ver test_charge_wall_pause_is_stationary_punish_window) en
            # lugar de pasar directamente a _y_recovering; _update_attack_state
            # activa eso una vez que la propia pausa expira.
            self._charge_recover = CHARGE_WALL_PAUSE
            if self.current_phase >= 1:
                # §2.4: el choque solo lleva VFX en fase 2 -- ver el mismo
                # gate en _update_vfx para el resto de la embestida.
                self.efectos.sacudir(3.0, 0.15, (float(self._charge_direction), 0.0))
                angulo_escombros = 180.0 if choco_contra_pared_derecha else 0.0
                x_pared = (float(self.rect.right) if choco_contra_pared_derecha
                           else float(self.rect.left))
                self.efectos.particulas_dirigidas(
                    x_pared, float(self.rect.centery), angulo_escombros, ESCOMBROS)

    def _do_vine_toss(self, pr: pygame.Rect) -> None:
        # 18.0/-6.0: elección visual del estudiante, posición aproximada del
        # hocico del venado (un poco adelante del centro, un poco por encima
        # de la línea vertical media).
        muzzle = (self.rect.centerx + 18.0 * self.facing_direction,
                  self.rect.centery - 6.0)
        predicted_vec = (pygame.Vector2(pr.centerx, pr.centery)
                         + self._last_player_velocity * VINE_PREDICT)   # Unidad II
        # 16.0: la mitad de la altura del jugador -- mantiene el objetivo en el
        # centro del jugador (no en sus pies) cuando está en el suelo.
        predicted = (predicted_vec.x, min(predicted_vec.y, FLOOR_Y - 16.0))
        midpoint = ((muzzle[0] + predicted[0]) / 2.0,
                    min(muzzle[1], predicted[1]) - VINE_ARC_HEIGHT)     # arco §3.5
        path = CurveTools.bezier([muzzle, midpoint, predicted], 32)     # Unidad III
        self._projectiles.append({
            "type": "vine", "path": path, "t": 0.0, "speed": VINE_SPEED,
            "pos": pygame.Vector2(muzzle), "damage": 0.5, "alive": True,
        })
        if self._event_bus is not None:
            # corrección del Hallazgo D: STOMP/CHARGE ya se anunciaban solos --
            # los proyectiles no, dejando al dodger estructuralmente ciego
            # ante este ataque (medido: 0 frames de advertencia, FINDINGS.md
            # Hallazgo D). Rect del tamaño del hocico, en paridad con el
            # propio rect con forma de ataque de _do_stomp (no el cuerpo
            # completo del boss).
            muzzle_rect = pygame.Rect(int(muzzle[0] - 5), int(muzzle[1] - 5), 10, 10)
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="VINE_TOSS", rect=muzzle_rect)
            self._event_bus.emit(Events.SFX_BOSSES_VENADO_VINE)

    def _do_mushroom_spore(self, pr: pygame.Rect) -> None:
        origin = pygame.Vector2(self.rect.centerx, self.rect.centery)
        to_player = pygame.Vector2(pr.centerx, pr.centery) - origin
        if to_player.length_squared() == 0:
            to_player = pygame.Vector2(0.0, 1.0)
        center_dir = vec2_normalize(to_player)          # Unidad II: apunta al momento de lanzar
        for angle in (-15.0, 0.0, 15.0):                # dispersión oficial izquierda/centro/derecha
            self._projectiles.append({
                "type": "spore",
                "pos": pygame.Vector2(origin),
                "origin": pygame.Vector2(origin),
                "vel": center_dir.rotate(angle) * SPORE_SPEED,
                "damage": 0.25, "alive": True, "age": 0.0,
            })
        if self._event_bus is not None:
            # corrección del Hallazgo D: misma paridad que _do_vine_toss arriba.
            # Usa el propio rect del boss (el punto de lanzamiento, no una
            # sola espora) ya que el ataque es un abanico de 3 vías, no un
            # único proyectil de punto de origen.
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="MUSHROOM_SPORE", rect=self.rect)
            # Solo existen 3 wavs del Venado (no hay sonido dedicado de
            # espora) -- reutiliza VINE. Desviación deliberada del boss de
            # referencia, que deja este ataque en silencio (spec
            # 2026-07-29-adopcion-v2-sfx-luces-weakpoints-design.md §1.1).
            self._event_bus.emit(Events.SFX_BOSSES_VENADO_VINE)

    # ──────────────────────────────────────────────
    # Proyectiles
    # ──────────────────────────────────────────────
    def _update_projectiles(self, dt: float) -> None:
        for proj in self._projectiles:
            if proj.get("inert"):
                # B-040: el marcador inerte no lleva "path"/"speed" (vine) ni
                # "vel"/"origin"/"age" (spore) -- no tiene trayectoria que
                # avanzar. Se retira en _update_attack_state/_cancelar_ataques_en_vuelo,
                # nunca aquí.
                continue
            if not proj["alive"]:
                continue
            if proj["type"] == "vine":
                proj["t"] += proj["speed"] * dt
                if proj["t"] >= 1.0:
                    proj["alive"] = False
                    continue
                px, py = CurveTools.sample_path(proj["path"], proj["t"])
                proj["pos"] = pygame.Vector2(px, py)
            elif proj["type"] == "spore":
                proj["age"] += dt
                proj["pos"] += proj["vel"] * dt
                if (proj["age"] >= SPORE_LIFETIME
                        or vec2_distance(proj["pos"], proj["origin"]) > SPORE_RANGE):
                    proj["alive"] = False                               # Unidad II
                    # §2.3: la nube de esporas también marca la expiración
                    # (el impacto se marca aparte, en _check_player_contact).
                    self.efectos.particulas(proj["pos"].x, proj["pos"].y, NUBE_ESPORA)
        self._projectiles = [p for p in self._projectiles if p["alive"]]

    # ──────────────────────────────────────────────
    # Interacción con el jugador
    # ──────────────────────────────────────────────
    def _check_player_contact(self, player) -> None:
        """Hook del motor (CollisionSystem.update_enemies llama esto cada frame
        antes de entity.update()): agrega daño de proyectil/stomp/sweep encima
        de la verificación de contacto corporal de EnemyBase, y luego delega
        en super() para esta última.

        Cambio 4 de la campaña de fairness -- gracia de contacto durante la
        transición de fase: mientras ``self.is_transitioning`` es True, este
        método retorna de inmediato, ANTES de tocar ninguna caja de daño
        (proyectil, stomp, esporas, barrido) y antes de delegar en
        ``super()._check_player_contact()`` (el contacto de cuerpo).

        Causa raíz: al cruzar el umbral de fase, ``_start_phase_transition``
        pone al venado invulnerable y arma el desvanecimiento que termina en
        el salto al centro de la arena (Cambio 5 de la campaña de fairness,
        feedback UX del usuario 2026-08-18, más arriba en este archivo: el
        jefe se desvanece en su posición VIEJA durante
        ``FADE_TELETRANSPORTE`` antes de saltar -- ya no en el mismo instante
        en que se abre la ventana), pero el motor NUNCA vuelve a sincronizar
        ``hurtbox`` con la posición del cuerpo -- vieja o nueva -- mientras
        dura la ventana completa de 2.5s: ``BossBase._pre_update`` corta
        ``EnemyBase.update()`` antes de llegar a ``_update_rects()`` en
        cuanto ``is_transitioning`` es True (boss_base.py ~L430-436), así
        que ``hurtbox`` queda CONGELADA en el punto donde el venado estaba
        peleando un instante antes del golpe que abrió la transición -- justo
        donde sigue de pie el jugador que acaba de aterrizarlo -- durante
        TODO el desvanecimiento y lo que sigue, incluido el salto real,
        mientras el cuerpo visible se desvanece y reaparece en el gazebo.
        Sin este guard, ese jugador se comía ``damage_on_contact`` (0.75) de
        una caja invisible en un punto donde ya no hay venado (evidencia:
        corrida v4_recert_competent, teleport f5717 -> golpe de contacto
        -0.75 exacto f5739 -- capturada cuando el salto todavía era
        instantáneo; el razonamiento de la hurtbox congelada no cambia con
        el Cambio 5, sólo el instante exacto en que el cuerpo visible se
        mueve).

        La ficha del jefe es explícita en que este es "el primer jefe: perdona",
        y doc 86 §2.4 regla 5 pide que la fase 2 castigue la esquiva pasiva del
        jugador, no el hecho de estar de pie cuando el venado cambia de forma
        a mitad de combate. El destino del teletransporte no cambia -- sigue
        siendo el centro de la arena, como describe la Biblia Técnica para el
        jefe de referencia -- y los proyectiles ya en vuelo quedan fuera de
        este alcance (decisión documentada del dictamen de fairness).

        Patrón de compensación del proyecto: si el motor alguna vez ofrece de
        fábrica gracia de contacto durante las transiciones de sus jefes
        (paralelo a H-02), este guard se retira.

        B-043 (REGISTRO-DE-BUGS.md, addendum del paquete B-039-C, dictamen
        doc-guardian AMARILLO 2026-08-23) -- gracia de contacto ACOTADA a
        TODA la ventana de VINE_SWEEP: el picado de barrido, el propio
        enraizado (``SWEEP_ROOTED``) y la rampa de despegue posterior.
        Mismo mecanismo que el Cambio 4 de arriba, pero MÁS ANGOSTO. El
        picado (``_actualizar_picado_de_barrido``) hace que el cuerpo
        avance activamente hacia el jugador durante todo el aviso de
        VINE_SWEEP; la rampa de despegue (``_sweep_despegue``, ver
        SWEEP_DESPEGUE) sale disparada desde donde el jugador acaba de
        castigar el enraizado; y el propio enraizado (``_sweep_rooted``,
        iteración 1 de verificación de este cambio -- ver
        ``diag_ventana_muerte.py`` en
        ``reports\\bughunt_20260823\\fixes_verify\\b043_despegue\\``) es
        justamente la ventana en la que el diseño INVITA al cuerpo a
        cuerpo: un jugador que se acerca a golpear a un jefe plantado no
        debe llevarse, de regalo, un golpe de contacto por la
        superposición accidental de hurtboxes. En los tres casos, dejar
        que el contacto de CUERPO siga doliendo castigaría la persecución
        que el propio diseño obliga, o la jugada correcta de quedarse a
        golpear. A diferencia del guard de
        ``is_transitioning`` (que corta el método entero al principio, ver
        arriba), este NO retorna temprano: envuelve únicamente la llamada a
        ``super()._check_player_contact(player)`` al final. Proyectiles,
        stomp, esporas y las crestas de ``OleadaDeLianas`` (el daño oficial
        de 0.5 del propio barrido) siguen aplicándose SIEMPRE -- perdonar
        el contacto de cuerpo durante un ataque que dispara sus propias
        cajas de daño no perdona esas cajas.
        """
        if self.is_transitioning:
            return
        self._last_player_velocity = pygame.Vector2(player.velocity)  # alimenta la predicción de VINE_TOSS
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for proj in self._projectiles:
            # B-040: "pos" not in proj ya basta para saltar el marcador inerte
            # (nunca lo lleva) -- el chequeo explícito de "inert" queda además
            # como candado inequívoco, documentado, ante cualquier cambio futuro.
            if proj.get("inert") or not proj.get("alive") or "pos" not in proj:
                continue
            r = pygame.Rect(int(proj["pos"].x - PROJECTILE_HIT_RADIUS),
                            int(proj["pos"].y - PROJECTILE_HIT_RADIUS),
                            int(PROJECTILE_HIT_RADIUS * 2), int(PROJECTILE_HIT_RADIUS * 2))
            if r.colliderect(player_hurtbox):
                player.apply_damage(proj["damage"], self.rect.center)
                if proj.get("type") == "spore":
                    # §2.3: el impacto también marca la nube (la expiración
                    # por vida/distancia vive en _update_projectiles).
                    self.efectos.particulas(proj["pos"].x, proj["pos"].y, NUBE_ESPORA)
                proj["alive"] = False
        if self._stomp_rect is not None and self._stomp_rect.colliderect(player_hurtbox):
            # codificado a mano igual que el boss de referencia del profesor (liana/espora en cambio llevan el daño en sus propios dicts)
            player.apply_damage(1.0, self.rect.center)          # daño oficial de STOMP
            self._stomp_rect = None
            # H-25/B-029 (FINDINGS.md línea 4216): _stomp_window NO se apaga
            # aquí. El anti multi-hit ya queda garantizado por
            # `self._stomp_rect = None` de arriba (el propio `if` de esta
            # rama y el guard de dibujo en ~L1411 exigen rect no-None para
            # volver a cobrar/dibujar la onda) -- la ventana debe seguir
            # viva y morir por su PROPIO decremento en _update_attack_state,
            # que es el ÚNICO punto que arma self._stomp_recover =
            # STOMP_RECOVER al cerrarla (líneas ~735-747). Apagarla aquí de
            # un tirón se saltaba ese flip ventana->recover y le robaba al
            # boss el recover plantado de 0.6s cuando la onda SÍ conectaba:
            # saltaba de golpe a la altura de vuelo de la senoidal (pop de
            # ~75px en 1 fotograma) en vez de quedarse plantado en el suelo.
        # Nube de esporas (adopción V3, D9). Se agrega el daño de TODAS las
        # esporas que tocan al jugador este fotograma y se aplica en UNA sola
        # llamada: llamar apply_damage por bala perdería N-1 golpes contra el
        # cooldown de invulnerabilidad del jugador y haría que el daño real
        # dependiera del orden del arreglo. La guarda de arena va ANTES de
        # dano_total_contra porque esa función consume las balas que acierta:
        # comprobarla después se las tragaría en silencio fuera de la arena.
        if player.rect.centerx >= ARENA_X0:
            dano_esporas = self.esporas.dano_total_contra(player_hurtbox)
            if dano_esporas > 0.0:
                player.apply_damage(dano_esporas, self.rect.center)
        # Task 9 (revisión final 2026-08-21): misma guarda de arena que ya
        # lleva la rama de esporas de arriba -- gate no_damage_outside_arena.
        # El bucle de oleadas no la llevaba: una cresta viajera podía tocar al
        # jugador ya fuera de la arena (p. ej. durante el tramo en que el
        # venado, empujado fuera por el bug de SEARCH de B-035, seguía
        # disparando oleadas contra un jugador en pleno corredor).
        if player.rect.centerx >= ARENA_X0:
            for oleada in self._oleadas:
                if oleada.viva and oleada.rect.colliderect(player_hurtbox):
                    # codificado a mano igual que el boss de referencia del profesor (liana/espora en cambio llevan el daño en sus propios dicts)
                    player.apply_damage(0.5, self.rect.center)      # daño oficial de SWEEP
                    oleada.golpeada()
                    break
        # B-043: gracia de contacto ACOTADA a toda la ventana de VINE_SWEEP
        # -- picado (aviso), el propio enraizado (SWEEP_ROOTED) y la rampa
        # de despegue posterior -- ver el docstring de este método.
        # Iteración 1 de verificación (diag_ventana_muerte.py): la canónica
        # competent seed=1 moría por un golpe de contacto EN PLENO
        # SWEEP_ROOTED (el jugador castigando la ventana como debía), así
        # que el enraizado se sumó al picado/despegue originales. Envuelve
        # SÓLO el contacto de cuerpo; todo lo de arriba (proyectil/stomp/
        # esporas/oleadas) ya se aplicó sin condicionarse a esto.
        en_ventana_de_barrido = (
            (self._telegraph == "VINE_SWEEP" and self.current_phase >= 1)
            or self._sweep_rooted > 0
            or self._sweep_despegue > 0
        )
        if not en_ventana_de_barrido:
            super()._check_player_contact(player)

    # ──────────────────────────────────────────────
    # Ciclo de vida / conexión con el motor
    # ──────────────────────────────────────────────
    def _destino_de_teletransporte(self) -> float:
        """X (esquina izquierda) donde reaparece el venado al cambiar de fase.

        H-19: se calcula con NUESTRAS constantes de arena y NUNCA con
        `arena_bounds.centerx`. El motor le entrega a todo BossBase el mapa
        entero como arena (stage_scene.py ~L454-461), y en este mapa-corredor
        ese centro cae en x=1640, a media pradera: copiar el patrón del jefe de
        referencia tal cual sacaría al venado de su terreno sagrado.
        """
        destino = ARENA_CX - self.rect.width / 2.0
        izquierda = ARENA_X0 + TELEPORT_MARGIN
        derecha = ARENA_X1 - TELEPORT_MARGIN - float(self.rect.width)
        return max(izquierda, min(destino, derecha))

    def _cancelar_ataques_en_vuelo(self) -> None:
        """Desarma todo lo que pueda seguir haciendo daño en la posición vieja.

        M-1: las cajas de daño de STOMP y del barrido de lianas se fijan en
        coordenadas de MUNDO en el instante en que se abren, y ahí se quedan
        hasta que su ventana expira. El reposicionamiento del cambio de fase
        mueve el cuerpo cientos de píxeles, así que sin este barrido esas cajas
        seguían cobrando daño durante toda la ventana de quietud en un punto
        donde ya no hay venado: el jugador veía al jefe al otro lado de la arena
        y recibía el golpe igual. Se apagan también el telegraph a medio contar
        y la embestida en curso, porque ambos describen una geometría (dirección
        y pared de destino) que el salto acaba de invalidar.
        """
        self._telegraph = ""
        self._telegraph_timer = 0.0
        # B-040: el marcador inerte de un VINE_TOSS/MUSHROOM_SPORE que
        # todavía estuviera armando su telegraph describe, igual que el resto
        # de esta función, una geometría vieja que el salto de fase acaba de
        # invalidar -- su vida tampoco debe sobrevivir a la cancelación.
        self._projectiles = [p for p in self._projectiles if not p.get("inert")]
        self._stomp_rect = None
        self._stomp_window = 0.0
        self._stomp_recover = 0.0
        self._oleadas.clear()
        self._sweep_rooted = 0.0
        self._sweep_aterrizo = False
        self._sweep_despegue = 0.0   # B-043: la rampa también describe una geometría (el t reanclado) que el salto invalida
        self._charge_active = False
        self._charge_recover = 0.0
        self._fantasmas.limpiar()   # (B) Task 14: la geometría vieja invalida sus fantasmas

    def _start_phase_transition(self) -> None:
        """Hook del motor: congela la máquina de estados y arma el
        desvanecimiento que termina en el reposicionamiento del cuerpo en
        mitad del gazebo (adopción V3, D6; UX del salto ampliada por el
        Cambio 5 de la campaña de fairness -- dictamen doc-guardian AMARILLO,
        feedback del usuario 2026-08-18).

        Sobre las duraciones que se citan en la documentación: manda el
        motor. La ventana de quietud dura los 2.5 s que fija BossBase; los
        0.5 s de §3.3 ("el jefe deja de moverse") describen el sub-paso
        narrativo en que el venado muda de forma -- ahí vive
        ``FADE_TELETRANSPORTE`` (0.55 s, constante de módulo) -- y ninguna de
        las dos es el bloqueo completo de la máquina de estados.

        El SALTO REAL sigue yendo dentro del primer tramo de la ventana,
        nunca al cerrarla -- la garantía ANTI-TIRÓN de H-18/D6 no cambia:
        §3.3 describe un cambio de forma dentro de la ventana y no dice
        nada, ni a favor ni en contra, sobre CUÁNDO mover al jefe; que
        ocurra bien entrado el primer segundo (jamás cerca del cierre) es lo
        que mantiene legible la secuencia para quien juega: el venado se
        esfuma de la esquina en la que estaba atrapado, aparece en mitad del
        terreno y se queda ahí, quieto y a la vista, el resto de la
        transición. Que el salto cayera cerca del cierre produciría lo
        contrario -- dos segundos y medio casi inmóvil y un tirón brusco en
        el instante en que el jefe recupera el control.

        Lo que SÍ cambia con el Cambio 5: en vez de teletransportar aquí
        mismo de forma síncrona (como hacía antes de este cambio), este
        método sólo ARMA ``self._desvanecimiento_restante =
        FADE_TELETRANSPORTE`` -- el cuerpo se queda visible en su posición
        VIEJA, desvaneciéndose (``_draw_teletransporte``, más abajo) -- y es
        nuestro ``update()`` (que corre ENTERO antes de delegar en
        ``super().update()``, ver ese método) quien decrementa ese reloj y
        ejecuta el ``teletransportar()`` real al cruzar cero, más un destello
        breve de materialización. El feedback UX del usuario pidió que el
        cambio de forma se SINTIERA como una desaparición y reaparición, no
        como un salto sin transición.

        Compone con `escala`: el destino se centra con el ancho actual y
        `_aplicar_escala_de_fase` (que corre en `_finish`) crece anclando
        pies+centro, así que el venado agrandado sigue centrado. La `y` se
        conserva -- el venado flota, no se planta. `BOSS_PHASE_CHANGED` lo
        sigue emitiendo el motor en `_finish`: aquí no se adelanta ni se
        duplica ningún evento.
        """
        super()._start_phase_transition()
        # M-1: primero se apaga lo que quedara en vuelo. El orden importa
        # poco para el resultado final, pero deja explícito que ninguna caja
        # de daño sobrevive al reposicionamiento -- se cancela de inmediato,
        # no cuando expire el desvanecimiento, porque esas cajas describen
        # una geometría (la posición VIEJA) que deja de ser de fiar en
        # cuanto el cuerpo empieza a desvanecerse.
        self._cancelar_ataques_en_vuelo()
        self._desvanecimiento_restante = FADE_TELETRANSPORTE

    def _finish_phase_transition(self) -> None:
        """Cierre de la ventana de cambio de fase, ampliado con lo propio.

        Del avance de fase, el evento, el VFX y el redimensionado del cuerpo se
        encarga la cadena base. Encima se encadenan tres añadidos nuestros: la
        línea de voz de la fase entrante, el anillo de esporas que la anuncia en
        pantalla y, cuando la fase declara movimiento bezier, el recálculo de la
        trayectoria en ocho -- que se hace aquí y no antes precisamente porque
        depende de la altura del cuerpo YA escalado (ver _caida_de_figura8).

        Orden de temporizadores (Cambio 5, riesgo 6 del dictamen doc-guardian
        AMARILLO): para cuando este método corre, el salto real
        (desvanecimiento de ``FADE_TELETRANSPORTE``=0.55s) siempre ya
        ocurrió -- lo conduce nuestro ``update()`` ENTERO, ANTES de que
        ``super().update()`` llegue a decrementar ``transition_timer`` y
        termine llamando a este método (ver ``update()`` más abajo), incluso
        dentro de un único ``update(dt)`` con ``dt`` gigante que cubra los
        dos relojes de golpe. Así que ``self.rect.center`` YA es la posición
        final cuando el anillo de esporas se abre unas líneas más abajo.
        """
        super()._finish_phase_transition()
        # Línea de voz de la fase recién estrenada. El índice interno arranca en
        # 0 y la numeración que ve el jugador en 1, de ahí el desplazamiento al
        # componer el nombre del clip.
        self._decir(f"sfx_voz_venado_fase{self.current_phase + 1}")
        # Refuerzo visual del mismo instante: estrenar la segunda fase abre de
        # golpe el anillo de esporas. Nace ya en mitad del gazebo -- el
        # reposicionamiento real se resolvió bien antes, dentro del primer
        # tramo de la ventana de quietud (ver _start_phase_transition/
        # update()), nunca aquí al cerrarla.
        if self.current_phase >= 1:
            self._soltar_abanico_de_esporas()
        if self.phases[self.current_phase].movement_type == "bezier":
            self._bezier_path = self._build_figure8_path()
            # H-24/B-028: en vez de saltar siempre a ruta[0] (la pared
            # izquierda), reengancha el vuelo en el punto de la curva más
            # cercano a donde el teletransporte dejó el cuerpo -- ver
            # _t_mas_cercano_en_ruta.
            self._bezier_t = self._t_mas_cercano_en_ruta(self._bezier_path)
            self._bezier_dir = 1
            # La y residual (el teletransporte no aterriza EXACTAMENTE sobre
            # la ruta) se suaviza con el mecanismo H-08 ya existente en la
            # rama bezier de _update_movement, en lugar de asignarse de
            # golpe -- mismo criterio que el recover plantado de STOMP/CHARGE.
            self._y_recovering = True
            # Impulso rancio acumulado en la posición VIEJA, previa al
            # reposicionamiento: FINDINGS (zona H-24) midió su drenaje a
            # razón 0.85 en f5706-5714 (deltas de ~6.5px decayendo) --
            # momentum que describe una geometría que ya no existe y que no
            # debe descargarse después del salto.
            self._knockback_velocity.update(0.0, 0.0)

    # ──────────────────────────────────────────────
    # Voz y nube de esporas (adopción V3)
    # ──────────────────────────────────────────────
    def _decir(self, linea: str) -> None:
        """Lanza un clip de voz del jefe, si hay mezclador conectado.

        Todo el trabajo de reproducción queda del lado del gestor de audio del
        motor, incluido bajarle el volumen a la música mientras suena la línea.
        Este envoltorio no toca ningún canal: repartir el control del volumen
        entre dos capas acabaría dando mezclas distintas según por dónde se
        pidiera la línea.

        La comprobación es en dos pasos y con salida temprana porque
        `audio_de_voz` puede valer tres cosas distintas: el gestor real que
        inyecta la escena, None (arnés headless, pruebas unitarias) o un doble
        parcial que no implemente esa llamada. En los dos últimos casos el
        venado se queda callado y el combate sigue; un asset de sonido nunca
        debe poder tumbar la pelea.
        """
        audio = self.audio_de_voz
        if audio is None or not callable(getattr(audio, "play_voz", None)):
            return
        audio.play_voz(linea)

    def _soltar_abanico_de_esporas(self) -> None:
        """Abre de golpe el anillo de esporas que marca el paso a la fase 2.

        El reparto cubre la vuelta completa alrededor del jefe, de manera que
        estar a un lado u otro no salva a nadie: lo que decide si el jugador
        sale ileso es moverse a tiempo, no dónde le pilló el cambio. Los
        parámetros del disparo (cantidad, rapidez, duración, tamaño y daño)
        viven en las constantes de clase de arriba, donde está razonado por qué
        vale cada uno.

        No lleva ninguna comprobación de fase ni de posición, y eso es
        deliberado: este método es sólo el gatillo, y quién y cuándo lo aprieta
        se decide en `_finish_phase_transition`. El contrato ejecutable del
        motor cuenta con ello -- lo invoca sobre un jefe recién construido,
        todavía en fase 0 y fuera de la arena.
        """
        centro_x = float(self.rect.centerx)
        centro_y = float(self.rect.centery)
        self.esporas.abanico(
            centro_x, centro_y,
            cuantas=self._ESPORAS_DE_LA_CORONA,
            velocidad=self._VELOCIDAD_ESPORA_ENJAMBRE,
            dano=self._DANO_ESPORA_ENJAMBRE,
            vida=self._VIDA_ESPORA_ENJAMBRE,
            radio=self._RADIO_ESPORA_ENJAMBRE,
        )

    def _resolver_punto_debil(
        self, puntos: list[WeakPoint], damage: float,
    ) -> tuple[float, WeakPoint | None]:
        """Compensación B-050 de `boss_kit.resolve_weak_point_damage`
        (boss_kit.py:391-428): calca su semántica EXACTA -- gana el
        multiplicador ESTRICTAMENTE mayor (no la suma; el primer empate se
        queda con el puesto), sin acierto devuelve `(damage, None)` -- pero
        sobre `puntos` que YA vienen escalados y espejados por nuestra propia
        composición (`_escalar_weak_point` + `_mirror_weak_point`, en ese
        orden), llamando `punto.rect_for(self.rect)` CRUDO: sin pasarle
        `escala` ni `facing`, porque ya están aplicados a mano.

        Existe porque la clase declara `cajas_siguen_al_cuerpo = True`
        (adopción AUD-606, ver esa constante): llamar directamente a
        `resolve_weak_point_damage` activaría su rama `sigue=True`
        (boss_kit.py:409) y volvería a escalar y espejar estos mismos puntos
        -- doble transformación -- con la fórmula de `WeakPoint.rect_for` que
        además es errónea a escala≠1 (B-050: espeja el offset canónico
        contra el ancho YA escalado y multiplica por `escala` DESPUÉS, en vez
        de escalar primero). Quitar este método -- y volver a llamar
        directamente a la función del motor -- en cuanto `rect_for` corrija
        ese orden: el test canario de B-050 (test_adopcion_v3.py) avisará.
        """
        hit_rect = self._player_ref
        mejor: WeakPoint | None = None
        for punto in puntos:
            if not punto.exposed_in(self.current_phase):
                continue
            rect_punto = punto.rect_for(self.rect)
            if hit_rect.colliderect(rect_punto) and (
                mejor is None or punto.multiplier > mejor.multiplier
            ):
                mejor = punto
        if mejor is None:
            return damage, None
        return damage * mejor.multiplier, mejor

    def apply_hit(self, damage: float, source_position: tuple[float, float]) -> None:
        """EnemyBase.apply_hit (enemy_base.py:390-391) llama a _die()
        sincrónicamente cuando la salud llega a 0, y _die()
        (enemy_base.py:402-418) ya pone state=DYING antes de que el control
        regrese aquí -- así que una guarda `state != DYING` sería
        inalcanzable (verificado: ya está en DYING en este punto). is_alive
        queda intacto por _die() (comentario en enemy_base.py:410-411:
        permanece True hasta que termina la secuencia de muerte guionada),
        así que la guarda refleja al boss de referencia del profesor
        (backups/boss_venado_original_src/boss_venado.py:388-391): solo
        current_health<=0 e is_alive, sin verificación de state.

        Los puntos débiles (Característica C, spec
        2026-07-29-adopcion-v2-sfx-luces-weakpoints-design.md §3.3) se
        resuelven AQUÍ, antes de delegar en super(), llamando a
        `_resolver_punto_debil()` propio -- deliberadamente NO
        `boss_kit.resolve_weak_point_damage()` ni `apply_hit_at()`.

        Adopción AUD-606 (H-20): esta clase declara `cajas_siguen_al_cuerpo =
        True` para heredar el escalado de hitbox/hurtbox del motor (ver el
        bloque "Escalado de fase" más arriba), pero esa misma bandera activa
        la rama `sigue=True` de `resolve_weak_point_damage`
        (boss_kit.py:409), que volvería a escalar y espejar `facing_points`
        -- que YA vienen escalados y espejados por
        `_escalar_weak_point`/`_mirror_weak_point` -- con la fórmula de
        `WeakPoint.rect_for` que además es errónea a escala≠1 (B-050, ver
        esos dos métodos). Llamar a la función del motor aquí sería una doble
        transformación con una fórmula equivocada; `_resolver_punto_debil`
        calca su semántica sobre nuestra composición, ya correcta.

        apply_hit_at() (boss_base.py) es la API "oficial" para esto, pero
        nada en el flujo de daño real la llama jamás: el único sitio real de
        llamada cuerpo a cuerpo (collision_system.py process_attack)
        descarta la hitbox del golpe del jugador y llama al simple
        apply_hit(damage, source_position) -- verificado por grep, cero
        sitios de llamada fuera de boss_base.py/boss_kit.py mismos.
        self._player_ref (el propio rect del jugador, mantenido vivo cada
        frame por StageScene._update_gameplay -> enemy.set_player_ref, el
        mismo objeto, no una copia) es el mejor proxy disponible de "dónde
        aterrizó el golpe" sin tocar ese archivo del motor. Llamar a
        super().apply_hit() después (no apply_hit_at()) mantiene esto como
        una única cadena no recursiva y preserva cada verificación existente
        de i-frames/invulnerabilidad-en-transición que ya vive en esa cadena
        -- el multiplicador solo cambia el argumento `damage`, nunca se salta
        cómo se aplica.
        """
        final_damage = damage
        hit_point: WeakPoint | None = None
        if self._player_ref is not None and self.weak_points:
            # H-20/B-050: escalar PRIMERO, espejar DESPUÉS -- ver _escalar_weak_point.
            facing_points = [self._mirror_weak_point(self._escalar_weak_point(wp))
                             for wp in self.weak_points]
            final_damage, hit_point = self._resolver_punto_debil(facing_points, damage)
        self.last_weak_point = hit_point
        if hit_point is not None:
            self._weak_point_flash_timer = WEAK_POINT_FLASH_DURATION
            self._weak_point_flash_point = hit_point

        super().apply_hit(final_damage, source_position)
        # de una sola vez: el boss de referencia reinicia su secuencia de muerte
        # cuando lo golpean mientras muere; la bandera mantiene la línea de
        # tiempo de derrota monótona (el gate de QA stage_complete_on_death
        # depende de esto)
        if self.current_health <= 0 and self.is_alive and not self._defeated:
            self.on_defeated()

    def update(self, dt: float) -> None:
        """DYING corta el flujo antes de tocar cualquier maquinaria del motor: la
        secuencia de muerte (_update_defeat de la Tarea 9) está guionada a
        mano, igual que el boss de referencia del profesor, así que no debe
        competir con la propia rama DYING de la máquina de estados/
        tick_cooldowns de EnemyBase. La embestida se omite mientras
        is_transitioning (BossBase._pre_update congela la máquina de estados
        para la superposición de cambio de fase) para que el dash no pueda
        reposicionar al boss durante un frame que el jugador ve congelado.
        _filter_frame es el contador que BossBase._apply_filter lee para
        limitar el filter_effect de fase a una vez cada 5 frames
        (_APPLY_FILTER_EVERY_N_FRAMES). update() se sobrescribe por completo
        -- en lugar de los hooks habituales _pre_update/_post_update -- por
        la misma razón: paridad con cómo el boss de referencia conecta su
        propio pipeline de ataque/proyectiles alrededor de la rama DYING.
        """
        if self.state == EnemyState.DYING:
            self._update_defeat(dt)
            return
        self._update_teletransporte(dt)   # Cambio 5: desvanecimiento + salto + materialización
        if self._charge_active and not self.is_transitioning:
            self._update_charge(dt)
        self._update_attack_state(dt)
        self._update_vfx(dt)
        self._update_projectiles(dt)
        # Anillo de esporas, acotado por ESPORAS_RECT: los lados impiden que una
        # espora salga a volar por el corredor (candado no_damage_outside_arena)
        # y el borde inferior la apaga al tocar el piso en vez de dejarla caer
        # por dentro del terreno dibujado (m-5).
        self.esporas.update(dt, ESPORAS_RECT)
        if self._weak_point_flash_timer > 0:
            self._weak_point_flash_timer = max(0.0, self._weak_point_flash_timer - dt)
        # MOTOR V2: BossBase._apply_filter ahora incrementa self._filter_frame
        # por sí mismo (boss_base.py ~L426); incrementarlo también aquí
        # duplicaba la cadencia del filter_effect de la fase 2.
        super().update(dt)
        # Task 9 (revisión final 2026-08-21, B-035): candado de ÚLTIMO RECURSO,
        # después de TODO lo demás (incluido super().update()) -- complementa
        # el override de _search_behavior de arriba, que ya cierra la ruta
        # conocida (SEARCH). Este clamp no depende de CÓMO se movió X: si
        # cualquier ruta del motor (presente o futura -- knockback, launch,
        # un SEARCH que algún día vuelva a cambiar) deja al venado fuera de
        # [ARENA_X0, ARENA_X1], se corrige aquí mismo, en el mismo fotograma.
        # Excluido mientras el cuerpo no está vivo/visible en su posición
        # normal (secuencia de derrota) o a mitad del teletransporte de fase
        # (self._desvanecimiento_restante > 0): interferiría con el
        # desvanecimiento en la posición VIEJA y con el salto real al centro.
        # También excluido durante el dash de CHARGE y su pausa de pared
        # (self._charge_active / self._charge_recover > 0): ese ataque tiene
        # su PROPIO margen, más ajustado a propósito (16px, _update_charge más
        # arriba) que el de patrulla (32px) -- sin esta exclusión, este
        # candado genérico pisaba la parada legítima contra la pared a
        # mitad de dash y durante toda la ventana de castigo estacionaria
        # (test_charge_wall_pause_is_stationary_punish_window, detectado
        # corriendo la suite completa tras implementar este Step).
        if (self.is_alive and self._desvanecimiento_restante <= 0
                and not self._charge_active and self._charge_recover <= 0):
            minimo = ARENA_X0 + 32.0
            maximo = ARENA_X1 - 32.0 - float(self.rect.width)
            if self.position.x < minimo or self.position.x > maximo:
                self.position.x = max(minimo, min(maximo, self.position.x))
                self.rect.x = int(self.position.x)

    def _update_teletransporte(self, dt: float) -> None:
        """Cambio 5 de la campaña de fairness (dictamen doc-guardian
        AMARILLO, feedback UX del usuario 2026-08-18): conduce el
        desvanecimiento y el destello de materialización del teletransporte
        de fase.

        Corre dentro de NUESTRO ``update()``, que se ejecuta ENTERO antes de
        delegar en ``super().update()`` -- y es precisamente eso lo que
        garantiza el orden de temporizadores del riesgo 6 del dictamen: el
        salto real de este método siempre ocurre ANTES de que
        ``super().update()`` (``EnemyBase.update`` -> ``BossBase._pre_update``)
        decremente ``transition_timer`` y dispare
        ``_finish_phase_transition()``, incluso dentro de un único
        ``update(dt)`` con ``dt`` gigante que cubra los dos relojes de golpe.
        Con ``FADE_TELETRANSPORTE`` (0.55s) << 2.5s de ventana un ``dt``
        normal jamás los hace vencer en el mismo fotograma, pero nada
        impide que un ``dt`` enorme sí -- de ahí que el orden se garantice
        por CONSTRUCCIÓN (este método corre primero) y no por casualidad de
        magnitudes.

        Los dos relojes son independientes: ``_materializacion_restante``
        decrece sin condicionarse a ``is_transitioning`` -- el destello debe
        poder apagarse aunque, por lo que sea, la ventana ya haya cerrado
        (defensivo; no se espera que ocurra con 2.5s de ventana >>
        ``FADE_TELETRANSPORTE`` + ``MATERIALIZACION_TELETRANSPORTE``)."""
        if self.is_transitioning and self._desvanecimiento_restante > 0:
            self._desvanecimiento_restante -= dt
            if self._desvanecimiento_restante <= 0:
                self._desvanecimiento_restante = 0.0
                self.teletransportar(self._destino_de_teletransporte(), self.position.y)
                self._materializacion_restante = MATERIALIZACION_TELETRANSPORTE
        if self._materializacion_restante > 0:
            self._materializacion_restante = max(0.0, self._materializacion_restante - dt)

    # ── Secuencia de derrota ──
    def on_defeated(self) -> None:
        self._decir("sfx_voz_venado_muerte")     # adopción V3, D2
        self._defeated = True
        self.esporas.limpiar()                   # la nube muere con él (adopción V3, D9)
        # state ya está en DYING aquí -- _die() (enemy_base.py) lo puso antes de que apply_hit() retornara.
        self._death_timer = 1.5                       # animación de muerte (12f @ 8fps)
        self._defeat_stage = 0
        self._projectiles.clear()
        self._charge_active = False
        self._charge_recover = 0.0
        self._telegraph = ""
        self._stomp_rect = None
        self._stomp_window = 0.0
        self._stomp_recover = 0.0
        self._y_recovering = False
        self._oleadas.clear()
        self._sweep_rooted = 0.0
        self._sweep_aterrizo = False
        self._sweep_despegue = 0.0   # B-043: ídem -- ninguna rampa debe sobrevivir a la muerte
        self._weak_point_flash_timer = 0.0
        self._weak_point_flash_point = None
        self._fantasmas.limpiar()   # (B) Task 14: no dejar fantasmas huérfanos tras la muerte

    def _update_defeat(self, dt: float) -> None:
        self._death_timer -= dt
        self._advance_animation(dt)
        if self._death_timer <= 0:
            if self._defeat_stage == 0:
                self._defeat_stage, self._death_timer = 1, 2.0   # cráneo 2s (§3.6)
            elif self._defeat_stage == 1:
                self._defeat_stage = 2
                self._death_timer = 0.0
                self.is_alive = False
                self.is_active = False
                self._anunciar_reliquia()

    def _anunciar_reliquia(self) -> None:
        """"Fragmento de Reliquia 1" (adopción V3, D10): el anuncio, una sola vez.

        Va en la ÚLTIMA etapa de la secuencia de derrota -- cuando la calavera
        de §3.6 termina de desvanecerse -- porque la reliquia es lo que queda
        del venado, no algo que suelte mientras aún se está muriendo.

        El anuncio es SILENCIOSO a propósito (H-21). El efecto de sonido
        SFX_BOSSES_RELIC_APPEAR está cableado de punta a punta por el motor (wav
        en disco, mapeo en sonido.py:99, subtítulo en subtitle_overlay.py:61),
        pero el profesor lo mantiene RESERVADO en la lista `AWAITING_THEIR_BOSS`
        de `tests/test_audio_wiring.py:80-82`, donde deja escrito que la
        recompensa del Venado "se resuelve por la escena de créditos". O sea que
        no es un sonido huérfano por descuido: es una decisión suya sobre dónde
        suena la reliquia. Emitirlo desde el jefe pone en rojo esa prueba de
        cableado de audio y se mete en terreno que no es del jefe, así que el
        sonido queda reservado a la escena de créditos.

        Lo que sí queda es esta bandera: impide repetir el anuncio si algo vuelve
        a pisar esta rama, y es lo que lee la escena para armar el banner y el
        icono de la reliquia (`boss_venado_scene._update_relic_banner`).
        """
        if self.reliquia_anunciada:
            return
        self.reliquia_anunciada = True

    # ── Renderizado (Unidad IV: orden de dibujo explícito, painter's order) ──
    def _build_spore_glow(self) -> pygame.Surface:
        """Cacheado UNA SOLA VEZ: ColorTools.alpha_blend halo+núcleo (Unidad V, seguro para el rendimiento)."""
        core = pygame.Surface((16, 16))
        halo = pygame.Surface((16, 16))
        pygame.draw.circle(core, (240, 250, 200), (8, 8), 4)
        pygame.draw.circle(halo, (120, 220, 140), (8, 8), 8)
        glow = ColorTools.alpha_blend(halo, core, 0.55)          # Unidad V
        glow.set_colorkey((0, 0, 0))
        return glow

    def _apply_filter(self, frame: pygame.Surface) -> pygame.Surface:
        """B-048 (REGISTRO-DE-BUGS.md; veredicto de la parada de la Tarea
        14, 2026-08-25): neutraliza por completo el reemplazo opaco de
        ``BossBase._apply_filter`` (``boss_base.py:615-633``).

        El mecanismo del motor recalcula el filtro de fase cada
        ``_APPLY_FILTER_EVERY_N_FRAMES`` fotogramas (throttle de
        rendimiento, ``boss_base.py:70``) y en ESE fotograma sustituye el
        sprite por ``FilterTools.sobel_edge(frame)`` -- una Surface
        construida con ``pygame.surfarray.make_surface(rgb)``
        (``filter_tools.py``), que NO tiene canal alfa. El sprite original
        sí lo tiene (margen transparente alrededor de la silueta del
        venado), así que ese recómputo pierde la transparencia por
        completo: ``BossBase.draw`` la pinta con ``surface.blit(frame,
        ...)`` SIN flags ni colorkey (``boss_base.py:677``), y el tile
        entero (no solo la silueta) se vuelve opaco negro con bordes
        blancos durante ese único fotograma -- un flash de ~16ms cada
        ~83ms (12Hz a 60fps) mientras dura la fase, tapando lo que hubiera
        detrás (terreno, ``EstelaDeFantasmas``). Verificado con 3 pruebas
        independientes en la parada de la Tarea 14: (1) llamada aislada a
        ``_apply_filter`` 5 veces seguidas -- la 5.ª difiere byte a byte de
        las otras 4; (2) parche de ``FilterTools.sobel_edge`` en una
        sesión jugada real -- se invoca exactamente en
        ``_filter_frame`` ∈ {5, 10, 15, ...}; (3) recorte alineado a
        ``boss.rect`` comparando ``_filter_frame``=4 contra 5 -- el
        fotograma 5 muestra un bloque rectangular de bordes duros ausente
        en el 4 (``reports\\t14_antes_despues_recompute.png`` del lab).

        ``filter_effect="sobel"`` SIGUE declarado en la ``BossPhase`` de
        fase 2 (``set_phases()`` más arriba) -- lo exige el contrato/la
        rúbrica del profesor, que lo consulta como DATO -- pero desde este
        override nunca vuelve a llegar a ``BossBase.draw`` ni a
        ``FilterTools.sobel_edge`` por ESTA vía: se convierte en una señal
        pura que solo lee nuestro propio pipeline (``_aura_activa``/
        ``_dibujar_aura_de_bordes`` más abajo), que reconstruye el efecto
        como un aura de bordes real enmascarada por el alfa original."""
        return frame

    def _aura_activa(self) -> bool:
        """B-048, condición de activación del aura de bordes: la fase
        ACTUAL debe declarar ``filter_effect == "sobel"`` (hoy, solo la
        fase 2) Y la vida debe estar en 3 corazones o menos
        (``current_health <= 3.0``, el mismo umbral leído en el comentario
        de ``update()`` sobre el auto-RETREAT de ``EnemyBase`` más abajo en
        este archivo) -- fiel a la ficha de nivel
        (``66_GUIA_DE_LEVEL_DESIGN.md:451``: "parpadeo sobel al bajar de 3
        corazones"), decisión (i) de la parada de la Tarea 14."""
        if not self.phases or self.current_phase >= len(self.phases):
            return False
        fase = self.phases[self.current_phase]
        return fase.filter_effect == "sobel" and self.current_health <= 3.0

    def _intensidad_pulso_aura(self) -> float:
        """Pulso de intensidad del aura de bordes en [0.4, 1.0] a 3Hz sobre
        el reloj de simulación ``self._t_vfx`` -- mismo patrón que
        ``SenalDeCastigo.brillo`` (``efectos_venado.py``), con el rango
        ampliado a 0.4-1.0 (en vez de 0.2-1.0) por pedido explícito del
        veredicto de la parada: "alfa entre ~40% y 100% del pico -- nunca a
        0, que el aura respire, no parpadee en seco". Determinista: dos
        jefes con la misma secuencia de ``dt`` producen el mismo
        ``_t_vfx`` y por tanto la misma intensidad en el mismo fotograma."""
        return 0.7 + 0.3 * math.sin(2.0 * math.pi * 3.0 * self._t_vfx)

    def _construir_aura_de_bordes(self, frame: pygame.Surface) -> pygame.Surface:
        """B-048: bordes Sobel REALES de ``frame`` (``FilterTools.
        sobel_edge``, Unidad VII), reconstruidos como overlay con alfa
        propio -- ``sobel_edge`` devuelve una Surface SIN canal alfa
        (magnitud en escala de grises, R=G=B), el mismo problema de origen
        que B-037/B-042 (``_dibujar_destello`` más abajo): hay que
        reconstruir la transparencia a mano o el "aura" pintaría un
        rectángulo entero en vez de solo los bordes.

        ``fraccion`` combina la magnitud del borde (0..1) CON el alfa
        original de ``frame`` (0..1): cero píxeles fuera de la silueta,
        sin importar qué magnitud calculó Sobel ahí (el fondo del tile es
        uniforme, Sobel debería dar 0 de todas formas, pero enmascarar por
        el alfa real es la garantía dura, no una esperanza). RGB y alfa de
        salida se derivan AMBOS de ``fraccion`` -- resultado premultiplicado
        (RGB = color * fraccion, alfa = 255 * fraccion), listo para
        ``BLEND_RGBA_ADD`` sin fantasma de color fuera de la silueta.

        ``frame`` es la Surface COMPARTIDA de ``_sprite_frames``/
        ``_flip_cache``/``_cache_frames_vivos`` (viene de
        ``_frame_vivo()``) -- igual que ``_dibujar_cuerpo_en_transicion``
        (B-038) advierte, JAMÁS se muta: solo se lee (``pixels_alpha`` en
        modo lectura, liberado con ``del`` antes de construir la salida) y
        se le pasa una COPIA implícita a ``FilterTools.sobel_edge`` (que
        internamente hace ``array3d``, sin escribir sobre el original)."""
        bordes = FilterTools.sobel_edge(frame)
        magnitud = pygame.surfarray.array3d(bordes)[:, :, 0].astype(np.float32)
        vista_alfa = pygame.surfarray.pixels_alpha(frame)
        fraccion = (magnitud / 255.0) * (vista_alfa.astype(np.float32) / 255.0)
        del vista_alfa  # soltar el lock de `frame` cuanto antes -- Surface compartida, jamás se muta

        salida = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
        rgb = pygame.surfarray.pixels3d(salida)
        alfa_out = pygame.surfarray.pixels_alpha(salida)
        try:
            for canal, valor in enumerate(self._AURA_COLOR_BORDES):
                rgb[:, :, canal] = (fraccion * valor).astype(np.uint8)
            alfa_out[:, :] = (fraccion * 255.0).astype(np.uint8)
        finally:
            del rgb
            del alfa_out
        return salida

    def _dibujar_aura_de_bordes(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """B-048: dibuja el aura de bordes sobre el cuerpo ya pintado
        (llamado desde ``draw()`` justo después del sprite). Recalcula
        ``_construir_aura_de_bordes`` (la parte cara: invoca cv2 vía
        ``FilterTools.sobel_edge``) solo cuando hace falta -- nunca en cada
        fotograma -- y cachea el resultado en ``self._aura_base`` entre
        recómputos, igual que el propio motor throttlea su filtro
        (``_CADENCIA_RECOMPUTO_AURA``, eco de ``_APPLY_FILTER_EVERY_N_
        FRAMES``). Dispara un recómputo cuando: (a) todavía no hay caché
        (primera activación -- el aura aparece de inmediato, sin esperar
        hasta 5 fotogramas para su primer dibujo), (b) la clave de
        ``_frame_vivo()`` cambió (animación/dirección/escala distintas --
        evita un aura con la silueta desalineada del cuerpo real), o (c)
        toca el tick de la cadencia (``cada_n_frames``).

        La intensidad del pulso (``_intensidad_pulso_aura``, 3Hz) se
        aplica SIEMPRE, en cada fotograma, sobre una copia barata de la
        base cacheada -- vía ``BLEND_RGB_MULT`` (NO ``BLEND_RGBA_MULT``):
        mismo criterio que ``_dibujar_destello``/B-042 documenta más abajo
        -- ``BLEND_RGBA_ADD`` sobre la Surface de mundo (sin alfa propio)
        ignora el alfa de origen, así que atenuar sólo el alfa no
        atenuaría nada visible; lo que sí atenúa es bajar el RGB que se
        suma, exactamente lo que hace ``SenalDeCastigo._cache_brillo`` para
        su propio pulso."""
        if not self._aura_activa():
            # se apaga del todo -- el próximo recómputo parte de cero, sin arrastrar una silueta vieja
            self._aura_base = None
            return
        vivo = self._frame_vivo()
        if vivo is None:
            return
        frame, destino, clave = vivo
        self._aura_contador += 1
        if (self._aura_base is None or clave != self._aura_clave
                or cada_n_frames(self._aura_contador, self._CADENCIA_RECOMPUTO_AURA)):
            self._aura_base = self._construir_aura_de_bordes(frame)
            self._aura_clave = clave
        canal = max(0, min(255, round(255 * self._intensidad_pulso_aura())))
        pulsado = self._aura_base.copy()
        pulsado.fill((canal, canal, canal), special_flags=pygame.BLEND_RGB_MULT)
        dx = int(destino[0] - camera_offset.x)
        dy = int(destino[1] - camera_offset.y)
        surface.blit(pulsado, (dx, dy), special_flags=pygame.BLEND_RGBA_ADD)

    def _frame_vivo(self) -> tuple[pygame.Surface, tuple[int, int], tuple[str, int, int, float]] | None:
        """Replica la selección de frame de BossBase.draw (boss_base.py
        ~646-676) SIN el filtro de fase ni el tinte de transición -- lo usa
        SenalDeCastigo (§2.5) para construir su silueta dorada sobre el
        MISMO sprite que el jugador ve, escalado por escala_de_fase igual
        que el motor. Devuelve (frame, destino_en_mundo, clave) o None si la
        animación actual no tiene frames cargados.

        destino se calcula en enteros de mundo (no de pantalla -- este
        método no conoce la cámara); el llamante resta camera_offset y
        vuelve a int() al pintar, el mismo doble-redondeo que ya tolera el
        resto del render de este archivo (a lo sumo 1px de jitter en un
        efecto de brillo de 1px de fleco, irrelevante)."""
        anim_key = self._get_animation_state()
        frames = self._sprite_frames.get(anim_key)
        if not frames:
            return None
        frame_idx = min(self._animation_frame, len(frames) - 1)
        frame = frames[frame_idx]
        if self.facing_direction < 0:
            cached = self._flip_cache.get((anim_key, frame_idx))
            if cached is None:
                cached = pygame.transform.flip(frame, True, False)
                self._flip_cache[(anim_key, frame_idx)] = cached
            frame = cached
        escala = self.escala_de_fase
        clave = (anim_key, frame_idx, self.facing_direction, escala)
        if escala != 1.0:
            escalado = self._cache_frames_vivos.get(clave)
            if escalado is None:
                escalado = pygame.transform.scale(
                    frame,
                    (max(1, int(frame.get_width() * escala)),
                     max(1, int(frame.get_height() * escala))))
                self._cache_frames_vivos[clave] = escalado
            frame = escalado
        destino = (
            int(self.position.x) + (self.rect.width - frame.get_width()) // 2,
            int(self.position.y) + self.rect.height - frame.get_height(),
        )
        return frame, destino, clave

    def _dibujar_destello(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Destello blanco del impacto de STOMP (§2.2): silueta blanca del
        frame vivo al 70% de intensidad, aditiva, encima del propio cuerpo
        ya dibujado. Sin caché propia -- dura como mucho FLASH_PISOTON_
        FRAMES fotogramas por pisotón (cooldown mínimo de 3s entre pisotones),
        reconstruirla es más barato que otra estructura que acotar.

        B-042 (fix, 2026-08-23): la versión anterior componía
        `BLEND_RGB_MAX` (sube el RGB a blanco IGNORANDO el alfa -- también
        en los píxeles totalmente transparentes del fondo del PNG) seguido
        de un blit `BLEND_RGBA_ADD` (que tampoco pondera por alfa -- no hay
        premultiplicación en ese modo de mezcla). El RGB "fantasma" de los
        píxeles de fondo se sumaba igual que el del cuerpo: el resultado era
        un bloque gris parejo sobre TODO el rect del sprite en vez de una
        silueta (evidencia:
        reports\\bughunt_20260823\\ocular\\1_stomp_fase1\\zoom_boss\\frames\\001816.png).
        Mismo diagnóstico y mismo remedio que B-037/H-28 (el halo de luna
        del jugador, `src\\framework\\vfx\\lighting.py`): premultiplicar el
        RGB por la fracción de alfa ORIGINAL del sprite (antes de subirlo a
        blanco) hace que `BLEND_RGB_MAX` deje de importar en los píxeles de
        fondo -- quedan en RGB (0,0,0), y sumarles 0 es un no-op exacto --
        y aplica el 70% de intensidad multiplicando solo el RGB (la ganancia
        real del efecto: `BLEND_RGBA_ADD` no usa el alfa de destino de un
        Surface opaco como el `surface` de mundo, así que reducir el alfa
        del origen -- como hacía la versión vieja -- no atenuaba nada; lo
        que sí atenúa es bajar el propio RGB que se suma)."""
        vivo = self._frame_vivo()
        if vivo is None:
            return
        frame, destino, _clave = vivo
        silueta = frame.copy()
        silueta.fill(COLOR_FLASH, special_flags=pygame.BLEND_RGB_MAX)
        intensidad = 0.7
        rgb = pygame.surfarray.pixels3d(silueta)
        alfa_original = pygame.surfarray.pixels_alpha(frame)
        fraccion = alfa_original.astype(np.float32) / 255.0
        for canal in range(3):
            rgb[:, :, canal] = (rgb[:, :, canal].astype(np.float32) * fraccion * intensidad).astype(np.uint8)
        del rgb
        alfa_out = pygame.surfarray.pixels_alpha(silueta)
        alfa_out[:, :] = (alfa_original.astype(np.float32) * intensidad).astype(np.uint8)
        del alfa_out, alfa_original
        dx = int(destino[0] - camera_offset.x)
        dy = int(destino[1] - camera_offset.y)
        surface.blit(silueta, (dx, dy), special_flags=pygame.BLEND_RGBA_ADD)

    def _ventana_de_castigo_abierta(self) -> bool:
        """§2.5: condición única que activa SenalDeCastigo -- las tres
        ventanas de castigo estacionario del boss (recover del pisotón,
        pausa de pared de la embestida, enraizado del barrido de fase 2)."""
        return self._stomp_recover > 0 or self._charge_recover > 0 or self._sweep_rooted > 0

    def _dibujar_cuerpo_en_transicion(self, surface: pygame.Surface,
                                       camera_offset: pygame.Vector2) -> None:
        """B-038 (bug del MOTOR, compensado aquí -- boss_base.py ~L657-661):
        mientras ``is_transitioning``, ``BossBase.draw()`` tiñe el frame con
        ``frame.blit(overlay, (0,0), special_flags=BLEND_RGBA_ADD)`` donde
        ``overlay.fill((200,200,0,80))`` -- suma alfa 80 y RGB amarillo a
        TODOS los píxeles del frame, incluidos los transparentes, así que el
        rect ENTERO se ve como un cuadrado amarillo semitransparente
        (zoom_sweep.png f5808; visible también en el playtest humano
        ``copiloto_0821_01`` f3007 como "rectángulo rosado" bajo luz
        nocturna). Peor aún: ``frame`` ahí es la Surface CACHEADA de
        ``self._sprite_frames``/``self._flip_cache`` (nunca una copia), así
        que ese blit MUTA el sprite compartido de forma permanente.

        Reemplaza por completo a ``super().draw()`` mientras dura la
        transición -- replicando SOLO el tinte, sobre una COPIA cacheada de
        ``_frame_vivo()`` (nunca la Surface real del motor): ``fill((200,
        200, 0, 0), special_flags=BLEND_RGBA_ADD)`` con alfa 0 en el color
        de relleno no suma nada al canal alfa, así que un píxel transparente
        (alfa 0) sigue transparente al componerse con un blit normal después
        -- el cuerpo opaco sí recibe el mismo tinte amarillo que pretendía
        el motor, sin el cuadrado de fondo ni la mutación."""
        vivo = self._frame_vivo()
        if vivo is None:
            return
        frame, destino, clave = vivo
        tenido = self._cache_tinte_transicion.get(clave)
        if tenido is None:
            tenido = frame.copy()
            tenido.fill((200, 200, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self._cache_tinte_transicion[clave] = tenido
        dx = int(destino[0] - camera_offset.x)
        dy = int(destino[1] - camera_offset.y)
        surface.blit(tenido, (dx, dy))

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        self._fantasmas.dibujar_mundo(surface, camera_offset)  # (B) Task 14: detrás del cuerpo
        if self.is_transitioning and self.is_alive and self.is_visible:
            self._dibujar_cuerpo_en_transicion(surface, camera_offset)  # (C) Task 14: B-038
        else:
            super().draw(surface, camera_offset)      # 1) cuerpo (sprite de BossBase)
        self._dibujar_aura_de_bordes(surface, camera_offset)  # 1a) B-048: aura de bordes Sobel real (Unidad VII)
        if self._flash_frames > 0:                    # 1b) destello blanco del impacto de STOMP (§2.2)
            self._dibujar_destello(surface, camera_offset)
            self._flash_frames -= 1
        if self._cresta_pisoton is not None:           # 1c) cresta de tierra del pisotón (mundo)
            self._cresta_pisoton.dibujar_mundo(surface, camera_offset)
        # 2) los avisos (_draw_telegraphs / _draw_anuncio_del_enjambre) YA NO
        # se pintan aquí -- Cambio 3 de la campaña de fairness (doc 86 §2.4
        # regla 5, "si algo se activa, se anuncia"): este pase de entidades
        # corre ANTES de que la escena aplique la capa de luz, y de noche el
        # multiplicador nocturno dejaba el aviso a ~40% de su brillo real.
        # BossVenadoScene.dibujar_ui() los pinta ahora DESPUÉS de super().draw(),
        # con el offset de cámara, para que se vean también de noche.
        # _draw_teletransporte (Cambio 5) nace ya siguiendo esa misma regla:
        # jamás se añadió aquí, la escena lo pinta junto a los otros dos.
        for oleada in self._oleadas:
            # pulido AAA 2026-08-21 (§2.1): cresta de la oleada -- pase de mundo,
            # bajo la luz, igual que el resto de entidades (painter's order).
            oleada.dibujar_mundo(surface, camera_offset, self._t_vfx)
        self._draw_projectiles(surface, camera_offset)# 3) proyectiles
        self.esporas.draw(surface, camera_offset,
                          self._COLOR_ESPORA_ENJAMBRE)  # 3b) nube de esporas
        self._draw_transition_pulse(surface, camera_offset)  # 4) VFX de color
        self._draw_weak_point_flash(surface, camera_offset)  # 5) confirmación de crítico
        if self._defeat_stage == 1:
            self._draw_skull(surface, camera_offset)

    def _draw_telegraphs(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        ox, oy = camera_offset.x, camera_offset.y
        if self._telegraph == "STOMP":
            progreso = 1.0 - max(0.0, self._telegraph_timer) / STOMP_TELEGRAPH
            centro = (int(self.rect.centerx - ox), int(FLOOR_Y - oy))
            AnilloDeCaida.dibujar_overlay(surface, centro, progreso, self._TELEGRAPH_WARN_COLOR)
        elif self._telegraph == "CHARGE":
            cx = int(self.rect.centerx - ox)
            cy = int(self.rect.centery - oy)
            tip = cx + self._sign_to_player() * 34
            pygame.draw.polygon(surface, self._TELEGRAPH_WARN_COLOR,
                                [(tip, cy), (tip - 10 * self._sign_to_player(), cy - 6),
                                 (tip - 10 * self._sign_to_player(), cy + 6)])
        elif self._telegraph == "VINE_SWEEP":
            # pulido AAA 2026-08-21 (§2.1): astas + grietas que crecen desde las
            # pezuñas -- anticipan DE DÓNDE viene el barrido y CUÁNDO va a salir,
            # sustituye a la franja de ancho completo (ilegible, feedback del
            # usuario "es solo una línea", ver el spec §0).
            progreso = 1.0 - self._telegraph_timer / SWEEP_TELEGRAPH
            progreso = max(0.0, min(1.0, progreso))
            cx = int(self.rect.centerx - ox)
            top = int(self.rect.top - 4 - oy)
            pygame.draw.line(surface, self._TELEGRAPH_WARN_COLOR, (cx - 6, top), (cx - 6, top - 10), 2)
            pygame.draw.line(surface, self._TELEGRAPH_WARN_COLOR, (cx + 6, top), (cx + 6, top - 10), 2)
            pezunas_y = int(FLOOR_Y - 2 - oy)
            largo = int(48.0 * progreso)
            pygame.draw.line(surface, self._TELEGRAPH_WARN_COLOR, (cx, pezunas_y), (cx - largo, pezunas_y), 2)
            pygame.draw.line(surface, self._TELEGRAPH_WARN_COLOR, (cx, pezunas_y), (cx + largo, pezunas_y), 2)
        elif self._telegraph == "MUSHROOM_SPORE":
            # tres marcas cortas en abanico sobre la corona: insinúan el
            # abanico de esporas de _do_mushroom_spore (ángulos -15/0/15).
            cx = int(self.rect.centerx - ox)
            top = int(self.rect.top - 4 - oy)
            for angle in (-15.0, 0.0, 15.0):
                rad = math.radians(angle - 90.0)   # -90: "arriba" en coordenadas de pantalla
                punta = (cx + math.cos(rad) * 10.0, top + math.sin(rad) * 10.0)
                pygame.draw.line(surface, self._TELEGRAPH_WARN_COLOR, (cx, top), punta, 2)
        elif self._telegraph == "VINE_TOSS":
            # marca de arco/gancho sobre la corona: insinúa el latigazo de
            # _do_vine_toss.
            cx = int(self.rect.centerx - ox)
            top = int(self.rect.top - 6 - oy)
            arco = pygame.Rect(cx - 10, top - 10, 20, 16)
            pygame.draw.arc(surface, self._TELEGRAPH_WARN_COLOR, arco, 0.0, math.pi, 2)
        if self._stomp_window > 0 and self._stomp_rect is not None and self._cresta_pisoton is not None:
            self._cresta_pisoton.dibujar_overlay(surface, camera_offset, (250, 220, 120))
        if self._charge_recover > 0:
            centro_cabeza = (int(self.rect.centerx - ox), int(self.rect.top - oy))
            EstrellasDeAturdimiento.dibujar_overlay(surface, centro_cabeza, self._t_vfx,
                                                     self._TELEGRAPH_WARN_COLOR)
        if self._ventana_de_castigo_abierta():
            vivo = self._frame_vivo()
            if vivo is not None:
                frame, destino, clave = vivo
                dx = int(destino[0] - ox)
                dy = int(destino[1] - oy)
                self._senal.dibujar_overlay(surface, frame, clave, (dx, dy), self._t_vfx)
        for oleada in self._oleadas:
            # pulido AAA 2026-08-21 (§2.1): filo + grieta por delante de cada
            # cresta viva -- pase de overlay (post-luz), igual que el resto
            # de avisos de este método desde la campaña de fairness.
            oleada.dibujar_overlay(surface, camera_offset, self._TELEGRAPH_WARN_COLOR)

    def _sign_to_player(self) -> int:
        pr = self._player_ref
        if pr is None:
            return self.facing_direction
        return 1 if pr.centerx >= self.rect.centerx else -1

    def _draw_projectiles(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        ox, oy = camera_offset.x, camera_offset.y
        for proj in self._projectiles:
            # B-040: mismo doble candado que _check_player_contact -- el
            # marcador inerte no debe agregar ruido visual nuevo.
            if proj.get("inert") or not proj.get("alive") or "pos" not in proj:
                continue
            sx, sy = int(proj["pos"].x - ox), int(proj["pos"].y - oy)
            surface.blit(self._spore_glow, (sx - 8, sy - 8))     # Unidad V visible
            if proj["type"] == "vine":
                pygame.draw.circle(surface, (110, 170, 90), (sx, sy), int(PROJECTILE_HIT_RADIUS))
                pygame.draw.circle(surface, (230, 245, 210), (sx, sy), int(PROJECTILE_HIT_RADIUS), 1)
            else:
                pygame.draw.circle(surface, (200, 180, 120), (sx, sy), 4)

    def _draw_transition_pulse(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if not self.is_transitioning:
            return
        # ColorTools.rgb_to_hsv devuelve h en [0, 360] (color_tools.py:18-35),
        # no en [0, 1] como podría asumirse leyendo la spec de forma ingenua
        # -- así que el incremento por segundo se expresa en grados (0.4 *
        # 360 = 144.0) y se envuelve mod 360, no mod 1.0.
        h, s, v = ColorTools.rgb_to_hsv(120, 220, 140)           # Unidad V: pulso HSV
        h = (h + (2.5 - self.transition_timer) * 144.0) % 360.0
        color = ColorTools.hsv_to_rgb(h, s, v)
        cx = int(self.rect.centerx - camera_offset.x)
        cy = int(self.rect.centery - camera_offset.y)
        radius = 30 + int(8 * math.sin(self.transition_timer * 12.0))
        pygame.draw.circle(surface, color, (cx, cy), radius, 3)

    def _draw_anuncio_del_enjambre(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Aviso del enjambre de esporas que _soltar_abanico_de_esporas()
        dispara al CERRAR la ventana de transición de fase.

        Cambio 2 de la campaña de fairness (doc 86 §2.4 regla 5: "si algo se
        activa, se anuncia"): hasta ahora la corona de _ESPORAS_DE_LA_CORONA
        esporas aparecía ya en vuelo, sin ningún aviso previo -- el mismo
        vacío que TOSS_TELEGRAPH/SPORE_TELEGRAPH cerraron para VINE_TOSS/
        MUSHROOM_SPORE en el Cambio 1.

        El progreso NUNCA sale de self._telegraph/self._telegraph_timer
        (candado M-1: esos dos campos deben quedar en ""/0.0 durante TODA la
        transición, ver _cancelar_ataques_en_vuelo) -- sale de
        self.transition_timer, el reloj que BossBase arranca en
        _VENTANA_TRANSICION_SEGUNDOS y decrementa en _pre_update
        (boss_base.py:380,432-436). Se clampa a [0,1] por robustez ante un
        transition_timer fuera de rango (p. ej. una prueba que lo fuerce a
        mano).

        Ancla a self.rect.center. Cambio 5 de la campaña de fairness
        (dictamen doc-guardian AMARILLO, feedback UX del usuario
        2026-08-18): el teletransporte real ya NO ocurre al abrir la
        ventana -- el venado se desvanece en su posición VIEJA durante
        ``FADE_TELETRANSPORTE`` antes de saltar (ver ``_update_teletransporte``)
        -- así que este método sólo empieza a dibujar DESPUÉS de ese salto
        real (ver el gate de ``_desvanecimiento_restante`` más abajo): antes
        de eso ``self.rect.center`` todavía sería la posición VIEJA, y
        anclar el anuncio ahí anunciaría un enjambre que va a nacer en un
        punto donde el cuerpo ya no está.
        """
        if not self.is_transitioning:
            return
        if self._desvanecimiento_restante > 0:
            # Cambio 5: mientras el cuerpo se desvanece, el aviso de esa
            # transición lo cubre _draw_teletransporte (anillo implosivo en
            # la posición vieja + marcador en el destino) -- este método
            # sólo anuncia el enjambre sobre la posición FINAL, ya saltada.
            return
        progreso = 1.0 - self.transition_timer / self._VENTANA_TRANSICION_SEGUNDOS
        progreso = max(0.0, min(1.0, progreso))
        cx = int(self.rect.centerx - camera_offset.x)
        cy = int(self.rect.centery - camera_offset.y)
        # el anillo arranca pegado al cuerpo y se separa hasta 40px más allá
        # según se acerca el estallido -- crece hacia afuera, no hacia
        # adentro, porque es el enjambre el que se aleja del cuerpo al soltarse.
        radio_base = float(max(self.rect.width, self.rect.height)) * 0.5 + 6.0
        radio = int(radio_base + 40.0 * progreso)
        pygame.draw.circle(surface, self._COLOR_ANUNCIO_ENJAMBRE, (cx, cy), radio, 2)
        # doce marcas radiales, una por cada espora de la corona que se va a
        # soltar -- mismo reparto angular completo que EnjambreDeBalas.abanico(),
        # no un subconjunto arbitrario elegido a mano.
        largo_marca = 4 + int(6 * progreso)
        for i in range(self._ESPORAS_DE_LA_CORONA):
            angulo = (2.0 * math.pi * i) / self._ESPORAS_DE_LA_CORONA
            dx, dy = math.cos(angulo), math.sin(angulo)
            inicio = (int(cx + dx * radio), int(cy + dy * radio))
            fin = (int(cx + dx * (radio + largo_marca)), int(cy + dy * (radio + largo_marca)))
            pygame.draw.line(surface, self._COLOR_ANUNCIO_ENJAMBRE, inicio, fin, 2)

    def _draw_teletransporte(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """UX del teletransporte de fase (Cambio 5 de la campaña de fairness,
        dictamen doc-guardian AMARILLO, feedback del usuario 2026-08-18).

        Dos tramos, mutuamente excluyentes porque ``_update_teletransporte``
        nunca deja ambos relojes vivos a la vez:

        * Mientras ``self._desvanecimiento_restante > 0`` -- el cuerpo
          TODAVÍA no saltó, ``self.rect`` sigue en la posición VIEJA -- se
          pinta un anillo IMPLOSIVO ahí mismo (se cierra sobre el cuerpo
          según se acerca el salto, lo contrario del anillo CRECIENTE del
          Cambio 2) más un marcador CRECIENTE en el DESTINO calculado por
          ``_destino_de_teletransporte()`` -- una diana simple que anticipa
          dónde va a reaparecer.
        * Mientras ``self._materializacion_restante > 0`` -- el salto real
          ya ocurrió, ``self.rect`` ya es la posición NUEVA -- se pinta un
          destello expansivo breve encima del cuerpo que confirma la
          llegada; ya no ancla nada, no queda ninguna posición vieja que
          señalar.

        Mismo tinte que el resto de avisos del jefe (``_TELEGRAPH_WARN_COLOR``,
        el mismo patrón de reutilización que ``_COLOR_ANUNCIO_ENJAMBRE``: un
        color nuevo que aprender no ayuda a leer el aviso más rápido) y
        formas planas sin antialias (``pygame.draw.circle`` con ancho de
        trazo explícito, igual que el resto de este archivo)."""
        if not self.is_transitioning:
            return
        ox, oy = camera_offset.x, camera_offset.y
        color = self._TELEGRAPH_WARN_COLOR
        radio_base = float(max(self.rect.width, self.rect.height)) * 0.5 + 6.0
        if self._desvanecimiento_restante > 0:
            # progreso 0..1: 0 recién abierta la ventana (desvanecimiento
            # completo por delante), 1 en el instante justo antes del salto.
            progreso = 1.0 - self._desvanecimiento_restante / FADE_TELETRANSPORTE
            progreso = max(0.0, min(1.0, progreso))

            # Anillo IMPLOSIVO sobre la posición VIEJA (self.rect: el salto
            # real todavía no ocurrió, ver _update_teletransporte).
            cx_viejo = int(self.rect.centerx - ox)
            cy_viejo = int(self.rect.centery - oy)
            radio_viejo = int(radio_base * (1.0 - progreso)) + 2
            pygame.draw.circle(surface, color, (cx_viejo, cy_viejo), radio_viejo, 2)

            # Marcador CRECIENTE sobre el DESTINO -- misma fórmula que usa el
            # propio salto (_destino_de_teletransporte); la Y no cambia
            # porque el venado flota, nunca se planta.
            destino_x = self._destino_de_teletransporte() + self.rect.width / 2.0
            cx_destino = int(destino_x - ox)
            cy_destino = int(self.rect.centery - oy)
            radio_destino = 4 + int(radio_base * progreso)
            pygame.draw.circle(surface, color, (cx_destino, cy_destino), radio_destino, 2)
            pygame.draw.circle(surface, color, (cx_destino, cy_destino), max(2, radio_destino // 3), 1)
        elif self._materializacion_restante > 0:
            # Destello expansivo breve sobre la posición NUEVA: confirma la
            # llegada, ya no anuncia nada por delante.
            progreso = 1.0 - self._materializacion_restante / MATERIALIZACION_TELETRANSPORTE
            progreso = max(0.0, min(1.0, progreso))
            cx = int(self.rect.centerx - ox)
            cy = int(self.rect.centery - oy)
            radio = int(radio_base * (0.4 + 0.8 * progreso))
            pygame.draw.circle(surface, color, (cx, cy), radio, 3)

    def _draw_weak_point_flash(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Retroalimentación de crítico de la Característica C: NO
        Events.VFX_PARRY -- ese evento ya está conectado (stage_scene.py)
        pero semánticamente significa "parry", reutilizarlo aquí le
        enseñaría al jugador que un golpe en cuerno/flanco es un parry (spec
        §3.1). Usa ColorTools directamente, igual que el resto del VFX
        propio de este boss (_build_spore_glow / _draw_transition_pulse) en
        lugar de depender de un evento de VFX del motor.
        """
        if self._weak_point_flash_timer <= 0 or self._weak_point_flash_point is None:
            return
        # rect_for() se recalcula cada frame contra el self.rect EN VIVO (no
        # cacheado en el momento del golpe) para que el destello siga al boss
        # en lugar de quedarse fijo en el mundo mientras este sigue
        # desplazándose/volando durante el destello de ~0.12s.
        rect = self._weak_point_flash_point.rect_for(self.rect)
        ox, oy = camera_offset.x, camera_offset.y
        r = rect.move(int(-ox), int(-oy))
        # Unidad V: pulso HSV, misma técnica que _draw_transition_pulse -- el
        # brillo desciende con el temporizador en lugar de un parpadeo
        # abrupto de encendido/apagado, así que un crítico se lee como un
        # destello corto, no como una calcomanía estática.
        fade = max(0.0, min(1.0, self._weak_point_flash_timer / WEAK_POINT_FLASH_DURATION))
        color = ColorTools.hsv_to_rgb(self._WEAK_POINT_FLASH_HUE, 0.9, 0.55 + 0.45 * fade)
        tint = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        tint.fill((*color, int(190 * fade)))
        surface.blit(tint, r.topleft)
        pygame.draw.rect(surface, color, r, 2)

    def _draw_skull(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """H-20: la calavera se escala con el mismo factor que el cuerpo.

        `BossBase.draw` ya redimensiona el frame vivo según `escala_de_fase`,
        pero la calavera la pintamos nosotros: sin escalarla, el venado muere en
        fase 2 a 60x60 y deja un cráneo de 48x48 descentrado dentro de su
        propio rect."""
        frames = self._sprite_frames.get("skull")
        x = int(self.rect.x - camera_offset.x); y = int(self.rect.y - camera_offset.y)
        if frames:
            frame = frames[0]
            if frame.get_size() != self.rect.size:
                frame = pygame.transform.scale(frame, self.rect.size)
            surface.blit(frame, (x, y))
        else:
            cx, cy = x + self.rect.width // 2, y + self.rect.height // 2
            radio = max(1, int(round(10 * self._factor_de_escala())))
            pygame.draw.circle(surface, (235, 235, 220), (cx, cy), radio)
