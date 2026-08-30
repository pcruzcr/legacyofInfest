"""
Módulo: entities
Sistema: stages.stage1_2_la_soda
Unidad académica: Unidad II (Vectores) / Unidad III (Curvas)
Descripción: subclases de enemigos propias para La Soda. Ambas extienden
las clases base de enemigos del framework (EnemyWalker, EnemyFlying) según
la regla de CLAUDE.md de "llamar al framework, nunca editarlo". Se
registran con StageLoader.register_entity() desde stage1_2_la_soda.py para
que el .tmx pueda referenciarlas por nombre de tipo. Ver README.md para
los conceptos académicos que demuestra cada una.
"""
from __future__ import annotations

import logging
import math
import random

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.surface_pool import get_pool
from src.engine.utils.math_utils import (
    ease_in_out_quad,
    ease_out_quad,
    vec2_distance,
    vec2_dot,
    vec2_normalize,
)
from src.framework.entities.enemy_base import EnemyState
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import EnemyShooter, Projectile
from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.processing.curve_tools import CurveTools

logger = logging.getLogger(__name__)

# Los sprites viven en la carpeta de assets propia y editable de la stage,
# no en el árbol compartido assets/sprites/enemies/zone*/ que usan por
# defecto esas clases base — mismo llamado a
# AssetLoader.load_sprite_sheet(), mismo contrato fw/fh, solo que la
# carpeta de origen es del estudiante.
_SPRITE_DIR = settings.ASSETS_DIR / "maps" / "stage1_2_la_soda"


# ──────────────────────────────────────────────────────────────
# AUD-649 — feedback visual de golpe y muerte, compartido por las 5 plagas
# ──────────────────────────────────────────────────────────────

_MUERTE_PARTICULA_GRAVEDAD: float = 300.0
_MUERTE_PARTICULA_VELOCIDAD_MIN: float = 60.0
_MUERTE_PARTICULA_VELOCIDAD_MAX: float = 120.0
#: El roster pide 0.4-0.6s de vida por partícula, pero `EnemyBase._die()`
#: (enemy_base.py:566-569) sólo mantiene `is_alive=True` 0.5s
#: (`_death_timer`) antes de que `_tick_cooldowns` (enemy_base.py:850-853)
#: lo apague, y `DrawingSystem.dibujar_mundo` (drawing_system.py:639) deja
#: de llamar a `draw()` en cuanto eso pasa -- nada vuelve a dibujar la
#: entidad después, ni sus partículas. Con vida de hasta 0.6s una partícula
#: se congelaría a medio camino en vez de desaparecer con el resto de la
#: escena. Se acota el máximo a 0.45s (0.05s de margen sobre los 0.5s
#: reales, para el fotograma en el que `is_alive` cambia a mitad de
#: `update()` y ya no se llega a dibujar -- ver el docstring de
#: `_GolpeYMuerteVisibles`) para que toda partícula termine su vida DENTRO
#: de la ventana en la que la entidad todavía se dibuja.
_MUERTE_PARTICULA_VIDA_MIN: float = 0.4
_MUERTE_PARTICULA_VIDA_MAX: float = 0.45
_MUERTE_PARTICULAS_MIN: int = 6
_MUERTE_PARTICULAS_MAX: int = 8
_MUERTE_PARTICULA_TAM_MIN: int = 2
_MUERTE_PARTICULA_TAM_MAX: int = 3
#: Mismos 0.3s del roster -- caben de sobra en los 0.5s de `_death_timer`
#: (ver el comentario de arriba), así que a diferencia de la vida de las
#: partículas esta duración no necesitó recortarse.
_MUERTE_FADE_DURATION: float = 0.3


def _muestrear_colores_de_sprite(
    cuadro: pygame.Surface | None, n: int = 3,
) -> list[tuple[int, int, int]]:
    """Toma hasta `n` colores de píxeles opacos del cuadro dado, para que
    las partículas de muerte salgan de la propia paleta del sprite en vez
    de un color inventado a mano (AUD-649).

    Puntos fijos (no aleatorios) sobre el cuadro: deterministas -- mismo
    cuadro, mismos colores siempre, sin que un test dependa de la semilla
    de `random` -- y las cinco hojas de AUD-648 centran el cuerpo del
    bicho en el cuadro con margen alrededor, así que estas fracciones caen
    dentro del cuerpo en las cinco. Los píxeles casi transparentes (borde
    antialiaseado) se descartan con el mismo umbral alfa (>10) que ya usa
    `test_la_soda_sprites.py` para lo mismo.
    """
    if cuadro is None:
        return [(200, 200, 200)] * n
    w, h = cuadro.get_size()
    puntos = [(0.35, 0.35), (0.6, 0.5), (0.45, 0.7), (0.7, 0.35), (0.3, 0.6)]
    colores: list[tuple[int, int, int]] = []
    for fx, fy in puntos:
        x = min(w - 1, max(0, int(w * fx)))
        y = min(h - 1, max(0, int(h * fy)))
        color = cuadro.get_at((x, y))
        if color.a > 10:
            colores.append((color.r, color.g, color.b))
        if len(colores) >= n:
            break
    if not colores:
        colores = [(200, 200, 200)]
    while len(colores) < n:
        colores.append(colores[-1])
    return colores[:n]


class _ParticulaMuerte:
    """Un cuadradito de 2-3px con física propia (radial + gravedad) para el
    estallido de muerte de AUD-649 -- ver
    `_GolpeYMuerteVisibles._generar_particulas_de_muerte` para el porqué de
    cada número."""

    __slots__ = ("x", "y", "vx", "vy", "vida", "color", "tam")

    def __init__(
        self, x: float, y: float, vx: float, vy: float,
        vida: float, color: tuple[int, int, int], tam: int,
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.vida = vida
        self.color = color
        self.tam = tam

    def actualizar(self, dt: float) -> bool:
        """Avanza `dt` de física. Devuelve False cuando la partícula ya
        agotó su vida (el llamante la descarta de la lista)."""
        self.vida -= dt
        if self.vida <= 0.0:
            return False
        self.vy += _MUERTE_PARTICULA_GRAVEDAD * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return True

    def dibujar(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        screen_x = int(self.x - camera_offset.x)
        screen_y = int(self.y - camera_offset.y)
        pygame.draw.rect(surface, self.color, (screen_x, screen_y, self.tam, self.tam))


class _GolpeYMuerteVisibles:
    """Mixin de feedback visual de combate para las cinco plagas de La Soda
    (AUD-649).

    Por qué existe: el motor sólo da dos señales de que un golpe conectó
    -- el estado `HURT` (que no cambia el sprite: `_get_animation_state`,
    enemy_base.py:673-682, sólo elige el cuadro "hurt", igual para
    cualquier golpe) y un parpadeo de invencibilidad de 4/60s
    (`_flash_visible`, enemy_base.py:736-746) que además hoy tiene el bug
    de hitstop que reportó el dueño (el enemigo puede quedar flotando tras
    un golpe no-letal, ver el docstring de `ShooterCocinero` un poco más
    abajo en este archivo) y que NUNCA se activa en un golpe letal, porque
    `apply_hit` sólo arma la invencibilidad "si no murió"
    (enemy_base.py:556-558). Y al morir, la entidad se queda con un único
    cuadro estático de "muerte" durante los 0.5s de `_death_timer`
    (enemy_base.py:566-569) y después simplemente deja de dibujarse en
    cuanto `_tick_cooldowns` (enemy_base.py:850-853) apaga `is_alive` --
    `DrawingSystem.dibujar_mundo` (drawing_system.py:639) filtra por
    `is_alive` antes de llamar a `draw()`, así que no hay ninguna
    transición: un fotograma está, al siguiente no está.

    Este mixin envuelve `apply_hit`, `update` y `draw` de las cinco
    subclases para agregar, en código propio del estudiante y sin tocar
    una línea de `enemy_base.py`/`enemy_walker.py`/`enemy_flying.py`/
    `enemy_shooter.py`: (1) un destello blanco + 2px de retroceso VISUAL
    los 4 fotogramas DIBUJADOS siguientes a cualquier golpe que de verdad
    conecte, y (2) al entrar en DYING, 6-8 partículas con la paleta del
    propio sprite y un desvanecido con `ease_out_quad` en vez del corte
    abrupto.

    Orden en la lista de bases -- SIEMPRE antes de la clase base del
    motor, nunca al revés (`class WalkerRaton(_GolpeYMuerteVisibles,
    EnemyWalker)`): así sus `apply_hit`/`update`/`draw` quedan ANTES que
    los del motor en la cadena de `super()` y pueden envolverlos sin
    reescribirlos. `FlyingCucaracha`/`FlyingZancudo`/`ShooterCocinero` ya
    sobreescriben `draw()` ellos mismos (proyectiles propios, y en el
    cocinero el destello de telegrafiado de AUD-648) -- como los tres YA
    empiezan su propio `draw()` llamando a `super().draw(...)`, ese
    `super()` pasa por este mixin antes de llegar al motor sin que haga
    falta tocar esos tres métodos. El orden de dibujado que resulta es
    cuerpo del motor -> destello/partículas de este mixin -> extras
    propios de cada clase (proyectiles, destello de telegrafiado) -- que
    es exactamente "conservar" lo que esas tres clases ya dibujaban.
    """

    _GOLPE_FLASH_FRAMES: int = 4
    _GOLPE_RETROCESO_PX: int = 2

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        #: Fotogramas DIBUJADOS restantes de destello -- contador de
        #: draw(), no de dt: "4 fotogramas dibujados" es lo que pide la
        #: entrega (parpadeo de sprite clásico, cuadro a cuadro), no una
        #: duración en segundos aproximada por dt.
        self._golpe_flash_restante: int = 0
        #: +1/-1 -- misma convención que ya usa `apply_hit` para el
        #: knockback real (`dir_x`, enemy_base.py:541-542): lejos de la
        #: posición de origen del golpe.
        self._golpe_retroceso_dir: int = 1
        self._muerte_particulas: list[_ParticulaMuerte] = []
        self._muerte_particulas_generadas: bool = False
        self._muerte_fade_timer: float = 0.0

    # ── Golpe: destello + retroceso visual ──────────────────

    def apply_hit(
        self, damage: float, source_position, canal: str | None = None,
    ) -> None:
        """Arma el destello+retroceso sólo cuando el golpe de verdad
        conecta.

        `EnemyBase.apply_hit` (enemy_base.py:483-564) es un no-op
        silencioso durante la invencibilidad post-golpe o si ya está en
        DYING (líneas 507-510) -- comparar `current_health` antes/después
        es la forma de distinguir "conectó" de "no-op" sin duplicar esa
        condición acá (y sin que se desincronice si el motor le agrega una
        tercera razón para el no-op el día de mañana).
        """
        vida_antes = self.current_health
        super().apply_hit(damage, source_position, canal)
        if self.current_health == vida_antes:
            return
        dx = self.rect.centerx - source_position[0]
        self._golpe_retroceso_dir = 1 if dx >= 0 else -1
        self._golpe_flash_restante = self._GOLPE_FLASH_FRAMES

    def _dibujar_destello_de_golpe(
        self, surface: pygame.Surface, camera_offset: pygame.Vector2,
    ) -> None:
        """El cuadro activo, aclarado a blanco (mismo `BLEND_RGB_ADD` que
        el destello de telegrafiado de `ShooterCocinero.draw` más abajo en
        este archivo -- ver ese docstring para el porqué del modo de
        mezcla) y desplazado `_GOLPE_RETROCESO_PX` en
        `_golpe_retroceso_dir` -- SÓLO en el destino del blit, nunca en
        `self.position`/`self.rect`, que ya calculó `_update_rects()` del
        motor y a los que un método de dibujado no le corresponde tocar.
        """
        if self._golpe_flash_restante <= 0:
            return
        self._golpe_flash_restante -= 1
        anim_key = self._get_animation_state()
        frames = self._sprite_frames.get(anim_key)
        if not frames:
            return
        frame_idx = min(self._animation_frame, len(frames) - 1)
        if self.facing_direction < 0:
            base_frame = get_pool().get_flipped_frames(frames)[frame_idx]
        else:
            base_frame = frames[frame_idx]
        flash = base_frame.copy()
        flash.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
        screen_x = (
            int(self.position.x - camera_offset.x)
            + self._golpe_retroceso_dir * self._GOLPE_RETROCESO_PX
        )
        screen_y = int(self.position.y - camera_offset.y)
        ox = (self.rect.width - self._sprite_fw) // 2
        oy = self.rect.height - self._sprite_fh
        surface.blit(flash, (screen_x + ox, screen_y + oy))

    # ── Muerte: partículas + desvanecido ────────────────────

    def _generar_particulas_de_muerte(self) -> None:
        """6-8 partículas al entrar en DYING, con la paleta del cuadro
        "die" actual -- ver el docstring de la clase para el porqué (el
        motor no da ninguna señal de muerte más que ese cuadro estático).

        El ángulo se restringe a `[0, pi]`, con el eje `+y` apuntando
        hacia abajo (medio círculo hacia abajo, no la vuelta completa de
        `[0, 2*pi]`): así la velocidad vertical inicial es siempre >= 0 y
        sólo crece con la gravedad, así que la `y` de cada partícula sube
        de forma monótona durante TODA su vida -- ninguna sale disparada
        hacia arriba a esperar el giro que la propia ventana de vida
        (recortada más arriba, `_MUERTE_PARTICULA_VIDA_MAX`) podría no
        darle tiempo a completar. Es además la lectura visual correcta
        para un bicho que se desarma en pedazos: salpica hacia abajo y a
        los costados, no hacia el techo.
        """
        cuadro = None
        cuadros_die = self._sprite_frames.get("die")
        if cuadros_die:
            cuadro = cuadros_die[min(self._animation_frame, len(cuadros_die) - 1)]
        colores = _muestrear_colores_de_sprite(cuadro, 3)
        origen_x = float(self.rect.centerx)
        origen_y = float(self.rect.centery)
        n = random.randint(_MUERTE_PARTICULAS_MIN, _MUERTE_PARTICULAS_MAX)
        particulas = []
        for i in range(n):
            angulo = random.uniform(0.0, math.pi)
            rapidez = random.uniform(
                _MUERTE_PARTICULA_VELOCIDAD_MIN, _MUERTE_PARTICULA_VELOCIDAD_MAX,
            )
            vx = math.cos(angulo) * rapidez
            vy = math.sin(angulo) * rapidez
            vida = random.uniform(_MUERTE_PARTICULA_VIDA_MIN, _MUERTE_PARTICULA_VIDA_MAX)
            tam = random.randint(_MUERTE_PARTICULA_TAM_MIN, _MUERTE_PARTICULA_TAM_MAX)
            particulas.append(
                _ParticulaMuerte(
                    origen_x, origen_y, vx, vy, vida, colores[i % len(colores)], tam,
                )
            )
        self._muerte_particulas = particulas

    def _alpha_de_muerte(self) -> int:
        """`255 * (1 - ease_out_quad(t))`, el desvanecido del roster --
        factorizado aparte de `_dibujar_muerte` para que
        `test_la_soda_sprites.py` lo compruebe con valores de `t` exactos
        sin tener que leer píxeles de una `Surface`."""
        t = min(self._muerte_fade_timer / _MUERTE_FADE_DURATION, 1.0)
        return int(255 * (1.0 - ease_out_quad(t)))

    def _dibujar_muerte(
        self, surface: pygame.Surface, camera_offset: pygame.Vector2,
    ) -> None:
        """Reemplaza el blit opaco de `EnemyBase.draw()`
        (enemy_base.py:373-405) -- o el de `EnemyShooter.draw()`
        (enemy_shooter.py:395-423) en el caso del cocinero, que no llama a
        `EnemyBase.draw()` y reimplementa su propio blit -- por uno con
        alpha propio mientras la entidad está en DYING. Ninguno de los dos
        blits del motor tiene parámetro de alpha, así que la única forma
        de desvanecerlos sin tocarlos es dibujar el cuadro "die" a mano
        acá, con la misma fórmula de posición (`ox`/`oy`/`screen_x`/
        `screen_y`) que usan los dos.
        """
        frames = self._sprite_frames.get("die")
        if frames:
            frame_idx = min(self._animation_frame, len(frames) - 1)
            if self.facing_direction < 0:
                base_frame = get_pool().get_flipped_frames(frames)[frame_idx]
            else:
                base_frame = frames[frame_idx]
            cuadro = base_frame.copy()
            cuadro.set_alpha(self._alpha_de_muerte())
            screen_x = int(self.position.x - camera_offset.x)
            screen_y = int(self.position.y - camera_offset.y)
            ox = (self.rect.width - self._sprite_fw) // 2
            oy = self.rect.height - self._sprite_fh
            surface.blit(cuadro, (screen_x + ox, screen_y + oy))
        for particula in self._muerte_particulas:
            particula.dibujar(surface, camera_offset)

    # ── Ciclo de vida: enganche de update()/draw() ──────────

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.state == EnemyState.DYING and not self._muerte_particulas_generadas:
            self._generar_particulas_de_muerte()
            self._muerte_particulas_generadas = True
        if not self._muerte_particulas_generadas:
            return
        self._muerte_fade_timer = min(self._muerte_fade_timer + dt, _MUERTE_FADE_DURATION)
        self._muerte_particulas = [p for p in self._muerte_particulas if p.actualizar(dt)]

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if not self.is_visible:
            return
        if self.state == EnemyState.DYING:
            if self.is_alive:
                self._dibujar_muerte(surface, camera_offset)
            return
        super().draw(surface, camera_offset)
        self._dibujar_destello_de_golpe(surface, camera_offset)


class WalkerRaton(_GolpeYMuerteVisibles, EnemyWalker):
    """Rata de cafetería (docs/18_ENEMY_ROSTER.md #2.4).

    Los stats coinciden con la spec del roster. Nunca abandona su franja de
    patrulla — incluso al notar al jugador, sigue la misma patrulla de lado
    a lado (movimiento clásico de enemigo de plataformas, ej. los Goombas
    de Mario) en vez de perseguir. La persecución heredada
    (EnemyWalker._alert_behavior) fue justo lo que en un principio le
    permitía atravesar paredes (ver _clamp_to_walls más abajo), y una
    patrulla que nunca sale de su franja elimina toda esa clase de bug en
    vez de solo parchearla.

    Igual conserva un empujón de velocidad "scent lock" como matemática
    vectorial explícita (normalize, producto punto, length) viviendo en
    código propio del estudiante: cuando la dirección normalizada hacia el
    jugador queda casi de frente con el encare actual de la rata (producto
    punto > 0.8), recibe un pequeño impulso de velocidad en la dirección en
    la que ya está patrullando — una lectura de sabor "la presa está justo
    enfrente mío", no una persecución, ya que `_patrol_behavior` la sigue
    dando vuelta en los mismos límites de patrol_length cada frame de todas
    formas.
    """

    SCENT_LOCK_DOT: float = 0.8
    SCENT_LOCK_BURST: float = 14.0

    def __init__(self, spawn_position: pygame.Vector2, **kwargs) -> None:
        kwargs.setdefault("patrol_length", 128.0)
        kwargs.setdefault("patrol_speed", 55.0)
        kwargs.setdefault("alert_speed", 90.0)
        kwargs.setdefault("damage_on_contact", 0.25)
        kwargs.setdefault("max_health", 1.0)
        # EnemyWalker.__init__ (framework) hardcodea detection_range_x/y al
        # llamar a EnemyBase.__init__ en vez de reenviarlos, así que
        # pasarlos como kwargs acá se perdería en silencio — en cambio, se
        # asignan directamente como atributos de instancia después de
        # construir.
        kwargs.pop("detection_range_x", None)
        super().__init__(spawn_position, **kwargs)
        self.detection_range_x = 96.0

    #: AUD-648 — tamaño de cuadro de la hoja PROPIA, mayor que el `fw`/`fh`
    #: de zona (16x12) que este hook recibe. Investigación: `_sprite_fw`/
    #: `_sprite_fh` (enemy_base.py:186-187) son atributos de INSTANCIA que
    #: `EnemyBase.draw()` vuelve a leer cada fotograma para centrar el
    #: sprite en X (`ox = (rect.width - _sprite_fw)//2`) y apoyar los pies
    #: en `rect.bottom` (`oy = rect.height - _sprite_fh`, líneas 383-384)
    #: — el motor no exige que el sprite quepa dentro del `rect` de
    #: colisión, sólo usa esa fórmula, así que basta con reasignarlos aquí
    #: para dibujar un sprite de 24x24 centrado y con los pies en el suelo
    #: sobre el `rect` de 24x28 sin tocarlo (ni el hitbox/hurtbox, que se
    #: siguen calculando aparte en `caja_ajustada`). A 16x12 —el tamaño de
    #: zona— el roster pedía "gris, ojos rojos, animación de carrera" y el
    #: resultado era una mancha de un puñado de píxeles indistinguible del
    #: piso (AUD-648, playtest del dueño).
    _SPRITE_FW: int = 24
    _SPRITE_FH: int = 24

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Sobreescribe el arte genérico del walker de zona1 con la hoja
        propia de la rata — mismo hook documentado por el framework para
        cargar sprites extra (ver EnemyBase._load_extra_sprites), pero a un
        tamaño de cuadro mayor que `fw`/`fh` (ver `_SPRITE_FW`/`_SPRITE_FH`
        arriba) en vez de intentar que el arte entre en el molde de 16x12
        de zona.

        `sprite_raton.png` (`Claude - Uso General/playtest/
        dibujar_sprites_plagas.py`) es UNA tira de 4 cuadros de 24x24:
        caminar x2, mordida x1, herido x1 — orden fijo del generador. La
        rata nunca ataca con animación propia (sólo contacto, ver
        `_alert_behavior` de esta clase), así que "mordida" no tiene clave
        de estado en la máquina y queda sin usar en el juego; se conserva
        en la hoja porque el roster la pide como pose de referencia y
        porque las pruebas de la hoja (`test_la_soda_sprites.py`)
        verifican las 4, no sólo las cableadas.

        Sin cuadro de "muerte" propio en el roster, se reutiliza "herido"
        para `die`: misma paleta y tamaño que el resto de la hoja, así la
        rata no vuelve a la mancha genérica de zona1 en el único momento
        —morir— en que más se la mira.
        """
        super()._load_extra_sprites(zone, fw, fh)
        path = _SPRITE_DIR / "sprite_raton.png"
        try:
            cuadros = AssetLoader.load_sprite_sheet(path, self._SPRITE_FW, self._SPRITE_FH)
            self._sprite_fw = self._SPRITE_FW
            self._sprite_fh = self._SPRITE_FH
            self._sprite_frames["walk"] = [cuadros[0], cuadros[1]]
            self._sprite_frames["hurt"] = [cuadros[3]]
            self._sprite_frames["die"] = [cuadros[3]]
        except (pygame.error, FileNotFoundError, PermissionError, IndexError):
            logger.warning("WalkerRaton: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        """Misma patrulla que EnemyWalker, más un clamp contra paredes en
        absolutamente todos los frames — no solo dentro de la rama del
        empujón scent-lock. Una segunda pasada de revisión encontró que el
        clamp contra paredes antes solo corría cuando se cumplía el cono
        del producto punto, así que una pared en cualquier punto de
        PATROL o SEARCH (o en ALERT con el jugador no más o menos al
        frente) no tenía ninguna protección. La franja de patrulla actual
        de este mapa no tiene ninguna pared adentro, así que nunca se
        manifestó, pero centralizar el clamp acá cubre todo camino de
        movimiento de manera uniforme en vez de depender de que eso sea
        cierto para siempre.

        Encontrado jugando de verdad (golpes reales, no sintéticos): un
        ataque real aplica knockback DOS VECES — una dentro del propio
        tier de EnemyBase.apply_hit, y otra vez vía el
        KNOCKBACK_IMPULSE_X/Y separado que suma
        CollisionSystem.process_attack (ambos en collision_system.py, de
        solo lectura) — juntos pueden arrastrar a la rata muy por fuera de
        patrol_length/2 (medido: un solo golpe leve cerca de una pared la
        empujó hasta x=16, ~240px de su franja de patrulla). Una vez tan
        lejos, el _patrol_behavior heredado de EnemyWalker chequea la
        distancia al origen *antes* de moverse y da vuelta
        facing_direction en absolutamente todos los frames en que sigue
        afuera — progreso neto cero, un deadlock permanente oscilando en
        el lugar (confirmado: 300 frames simulados, nunca se movió). Se
        detecta estar fuera de la franja y primero se camina derecho de
        vuelta a casa, saltándose la lógica heredada propensa a dar
        vueltas hasta volver a estar dentro de los límites.

        Una ronda de revisión posterior encontró que el fix de "caminar a
        casa" de arriba seguía haciendo deadlock, por una razón
        completamente distinta: el hitstun leve/pesado (a diferencia de
        LAUNCHED) aplica knockback en Y pero después ninguna gravedad la
        vuelve a bajar (los tiers no-LAUNCHED de enemy_base.py, de solo
        lectura) — la rata queda flotando unos pixeles sobre su altura de
        reposo indefinidamente. La sonda de borde heredada (EnemyWalker)
        lee ese flotante residual como "no hay piso adelante" y da vuelta
        facing_direction cada frame, el mismo síntoma de deadlock por un
        camino distinto. Como esta es una unidad terrestre cuya altura de
        reposo nunca cambia, directamente se la vuelve a apoyar en el piso
        en vez de confiar en la sonda mientras sigue en el aire por un
        golpe — `_patrol_origin` guarda el punto de spawn tal cual viene
        del `.tmx`.

        AUD-455 cambió la convención del motor: la `y` de un objeto de
        Tiled es su esquina superior, no sus pies, y `EnemyWalker.__init__`
        ya no le resta `rect.height`. Por eso la altura de reposo correcta
        es directamente `_patrol_origin.y`; restar de nuevo aquí dejaría a
        la rata flotando justo la altura de su caja.
        """
        resting_y = self._patrol_origin.y
        if abs(self.position.y - resting_y) > 0.5:
            self.position.y = resting_y
            self.rect.y = int(self.position.y)

        half_width = self.patrol_length / 2.0
        min_x = self._patrol_origin.x - half_width
        max_x = self._patrol_origin.x + half_width
        if self.position.x < min_x or self.position.x > max_x:
            self.facing_direction = 1 if self.position.x < self._patrol_origin.x else -1
            self.position.x += self.facing_direction * self.patrol_speed * dt
            self._clamp_to_walls()
            return
        super()._patrol_behavior(dt)
        self._clamp_to_walls()

    def _alert_behavior(self, dt: float) -> None:
        """Patrulla como siempre — deliberadamente NO llama a
        super()._alert_behavior(dt) (la IA de persecución/carga del
        framework), así que notar al jugador nunca saca a la rata de su
        franja de patrulla."""
        self._patrol_behavior(dt)
        if self._player_ref is None:
            return
        player_pos = pygame.Vector2(self._player_ref.center)
        self_pos = pygame.Vector2(self.rect.center)
        to_player = player_pos - self_pos
        distance = vec2_distance(player_pos, self_pos)
        if distance <= 0:
            return
        direction = vec2_normalize(to_player)
        facing = pygame.Vector2(self.facing_direction, 0.0)
        if vec2_dot(direction, facing) > self.SCENT_LOCK_DOT:
            prev_x = self.position.x
            self.position.x += direction.x * self.SCENT_LOCK_BURST * dt
            # El code review detectó que el empujón acumulaba una deriva
            # neta más allá de la franja (hasta 81px contra un half-width
            # de 24px) sin ningún clamp — pero un segundo bug, encontrado
            # jugando, estaba en el primer fix para eso: clampear sin
            # condición hacía que la posición de la rata saltara de golpe
            # cada vez que ya estaba fuera de los límites por una razón no
            # relacionada (recuperándose del knockback de un golpe real,
            # que puede arrastrarla ~240px+ por la doble aplicación de
            # knockback del framework — el propio tier de apply_hit MÁS el
            # KNOCKBACK_IMPULSE_X separado que suma
            # CollisionSystem.process_attack, ambos en collision_system.py,
            # de solo lectura). La rata quedaba pegada a una pared en un
            # frame y reaparecía de golpe cerca de su franja de patrulla
            # al siguiente — exactamente el "se pierde en el mapa" que el
            # estudiante seguía reportando, solo que como un
            # teletransporte *de vuelta* en vez de *hacia afuera*. Solo se
            # clampea cuando el empujón es lo que la sacó (es decir, ya
            # estaba dentro de los límites antes de este empujón) — una
            # desviación grande genuina se deja para que la camine normal
            # por frame (_patrol_behavior, llamada cada frame sin importar
            # el estado) la cierre gradualmente en cambio.
            half_width = self.patrol_length / 2.0
            min_x = self._patrol_origin.x - half_width
            max_x = self._patrol_origin.x + half_width
            if min_x <= prev_x <= max_x:
                self.position.x = max(min_x, min(max_x, self.position.x))
            self._clamp_to_walls()

    def _search_behavior(self, dt: float) -> None:
        """Misma política de "nunca abandona la patrulla" que
        _alert_behavior.

        El code review también detectó esto: el _search_behavior por
        defecto de EnemyBase (enemy_base.py) camina derecho hacia
        `_last_seen.x` a `patrol_speed` sin ningún límite, y — como
        detection_range_x (96) es mucho mayor que patrol_length/2 (24) —
        SEARCH se dispara en prácticamente cada ciclo de
        detectar-y-perder-de-vista. Peor aún, podía dejar a la rata varada
        permanentemente fuera de su franja: una vez atascada más allá del
        límite, el chequeo de dar vuelta de _patrol_behavior se dispara en
        absolutamente todos los frames (la distancia nunca baja de
        patrol_length/2 si el movimiento neto es ~0), dando vuelta
        facing_direction para adelante y atrás para siempre en vez de
        caminar de vuelta a casa. Delegar acá a _patrol_behavior — igual
        que en _alert_behavior — cierra ambos huecos a la vez.
        """
        self._patrol_behavior(dt)

    def _should_retreat(self) -> bool:
        """La rata no huye con poca vida (AUD-644, playtest del dueño del
        26/8: caminaba hacia atrás hasta clavarse en la esquina de la
        sala).

        No alcanza con anular sólo _retreat_behavior más abajo:
        EnemyBase._run_state_machine (enemy_base.py:923-931) entra en
        RETREAT en cuanto _should_retreat() da True y NO vuelve a salir
        mientras siga dando True -- con la vida ya baja y sin regenerar,
        eso deja a la rata congelada en RETREAT para siempre, sin atacar
        ni patrullar, en vez de sólo quieta en el sitio donde ya estaba
        (comprobado en headless: con sólo el no-op de _retreat_behavior
        la rata pasa 150 fotogramas sin salir de RETREAT). Anular acá, en
        cambio, hace que ni siquiera entre: sigue en ALERT/PATROL como si
        tuviera la vida llena -- coherente con _alert_behavior/
        _search_behavior de arriba, que ya ignoran la vida del framework
        para todo lo demás. El roster (docs/18_ENEMY_ROSTER.md #2.4) no
        menciona que la rata huya.
        """
        return False

    def _retreat_behavior(self, dt: float) -> None:
        """No-op -- con _should_retreat anulado arriba nunca debería
        llamarse, pero se anula igual por si algún llamante futuro entra
        en RETREAT por otra vía: el repliegue heredado de EnemyBase
        (enemy_base.py:1091-1099) aleja al enemigo del jugador sin
        chequear paredes ni bordes, y en un pasillo con esquinas como el
        de La Soda eso la deja atascada e inalcanzable."""

    def _clamp_to_walls(self) -> None:
        """Frena a la rata contra geometría sólida — el movimiento de
        persecución del framework no lo hace.

        Bug encontrado jugando: atacar a la rata podía mandarla volando
        fuera del mapa por completo. Causa raíz rastreada de forma
        headless: el `_alert_behavior` heredado de EnemyWalker (framework,
        enemy_walker.py) solo chequea un borde (sin piso adelante) antes
        de moverse — nunca chequea una *pared* sólida, porque el
        movimiento normal de patrulla/persecución de este framework no
        tiene ninguna colisión horizontal; solo `_apply_knockback`
        (enemy_base.py) resuelve contra `_collision_rects`, y solo
        mientras la velocidad de knockback es distinta de cero. Con el
        empujón scent-lock persiguiendo al jugador justo contra una
        pared, la rata podía atravesarla sin chequeo durante varios
        frames; después, la corrección de knockback de un golpe asume
        que la entidad se está acercando desde el lado del cuarto y la
        empujaba para el lado equivocado, expulsándola hacia afuera en
        vez de hacia adentro (reproducido: un ataque cerca de la pared
        izquierda la mandó a x=-7). El código de movimiento del framework
        es de solo lectura, así que el fix vive acá: se vuelve a correr
        la misma resolución de solapamiento que ya usa `_apply_knockback`,
        en cada frame, para que la rata nunca esté a más de un frame de
        movimiento adentro de una pared (lo suficientemente poco como
        para que "de qué lado se está acercando" sea siempre inequívoco).

        Una ronda de revisión posterior encontró que esto dejaba a la
        rata permanentemente encajada dentro de la plataforma-mostrador
        flotante (id 218, x=320-448) después de un knockback grande:
        `_collision_rects` contiene cada rect Solid del nivel — paredes,
        piso, Y esa plataforma — pero este método siempre empujaba
        horizontalmente sin importar con cuál había chocado, a
        diferencia del propio `_apply_knockback` del framework
        (enemy_base.py), que compara overlap_x contra overlap_y y
        resuelve el que sea menor. En vez de reimplementar esa
        comparación genérica de ejes, esto se queda acotado a lo que
        realmente busca frenar: solo se tratan como paredes acá los
        rects lo suficientemente angostos como para ser una de las
        columnas reales de pared lateral de este mapa (16px de ancho) —
        el piso (768px) y la plataforma (128px) son ambos mucho más
        anchos y nunca calzan, así que quedan para el manejo normal en Y
        (el snap-al-piso de _post_update / el re-apoyo propio de
        _patrol_behavior) en vez de ser expulsados hacia el costado.

        La verificación también encontró un deadlock de punto fijo
        posible en teoría (no alcanzable por ningún golpe real con la
        geometría actual de este mapa, pero barato de cerrar): empujar
        exactamente a `tile.left - rect.width` con truncamiento `int()`
        tanto acá como en el rect usado para el chequeo del siguiente
        frame puede dejar a la entidad re-colisionando con el mismo tile
        en la misma posición flotante cada frame, sin nada para escapar
        por el lado incorrecto ya que el paso por frame de patrol_speed
        es más chico que el propio truncamiento. Un empujón de 1px más
        allá del borde del tile (no solo a ras de él) garantiza que cada
        corrección realmente libere el tile en vez de volver a caer justo
        en su límite.
        """
        rect = pygame.Rect(
            int(self.position.x), int(self.position.y),
            self.rect.width, self.rect.height,
        )
        for tile in self._collision_rects:
            if tile.width > 16:
                continue
            if rect.colliderect(tile):
                if rect.centerx < tile.centerx:
                    self.position.x = tile.left - rect.width - 1
                else:
                    self.position.x = tile.right + 1
                rect.x = int(self.position.x)


class FlyingCucaracha(_GolpeYMuerteVisibles, EnemyFlying):
    """Cucaracha voladora (docs/18_ENEMY_ROSTER.md #2.5).

    El camino de patrulla es una spline de Catmull-Rom explícita de
    CurveTools a través de 4 puntos de control documentados (un arco poco
    profundo sobre el mostrador), muestreada de ida y vuelta con una onda
    triangular para que la cucaracha planee suave en vez de saltar en los
    extremos. Se eligió por sobre la estrategia de patrulla "sine"
    incorporada del framework para que la matemática de la curva
    (CurveTools.build_bezier_path) quede explícita e inspeccionable en
    código propio del estudiante.

    Nunca persigue: detectar al jugador no interrumpe la curva — solo
    agrega un ataque a distancia encima (misma idea que WalkerRaton
    descartando la persecución heredada). `_alert_behavior` sigue llamando
    a `_patrol_behavior` cada frame y dispara un proyectil hacia el
    jugador con cooldown, reutilizando la propia clase `Projectile` del
    framework (`enemy_shooter.py`) en vez de inventar una nueva.
    """

    # Puntos de control relativos a la posición de spawn (px). Forman un
    # arco poco profundo de baja-planea-baja: abajo, arriba, arriba, abajo
    # — una patrulla perezosa sobre el mostrador de la cocina.
    CONTROL_POINTS: list[tuple[float, float]] = [
        (-40.0, 10.0),
        (-14.0, -18.0),
        (14.0, -18.0),
        (40.0, 10.0),
    ]
    CURVE_PERIOD: float = 3.2  # segundos para un pasaje completo de ida y vuelta

    PROJECTILE_SPEED: float = 110.0
    PROJECTILE_DAMAGE: float = 0.25
    FIRE_COOLDOWN: float = 1.8  # segundos entre disparos mientras se detecta al jugador

    def __init__(self, spawn_position: pygame.Vector2, **kwargs) -> None:
        kwargs.setdefault("flight_speed", 45.0)
        kwargs.setdefault("sine_amplitude", 16.0)
        kwargs.setdefault("sine_frequency", 2.0)
        kwargs.setdefault("damage_on_contact", 0.25)
        kwargs.setdefault("max_health", 1.0)
        super().__init__(spawn_position, **kwargs)
        self._curve_points: list[pygame.Vector2] = [
            pygame.Vector2(spawn_position.x + dx, spawn_position.y + dy)
            for dx, dy in self.CONTROL_POINTS
        ]
        self._curve_t: float = 0.0
        self._active_projectiles: list[Projectile] = []
        self._shoot_cooldown: float = 0.0

    #: AUD-648 — mismo razonamiento que `WalkerRaton._SPRITE_FW/_FH`: mayor
    #: que el 14x10 de zona que EnemyFlying pasa a este hook, reasignado a
    #: `_sprite_fw`/`_sprite_fh` de instancia porque `draw()` los relee
    #: cada fotograma (ver el docstring de WalkerRaton para el porqué
    #: completo con líneas de enemy_base.py).
    _SPRITE_FW: int = 24
    _SPRITE_FH: int = 24

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Sobreescribe el arte genérico del volador de zona1 con la hoja
        propia de la cucaracha (`sprite_cucaracha.png`, 3 cuadros de 24x24:
        volar x2, herido x1). Llama a super() primero para que la clave
        genérica "fly" (el propio override de EnemyFlying) siga cargando
        como fallback al tamaño de zona si la hoja propia falla — el mismo
        patrón que ya usaba esta clase, sólo que ahora el tamaño de cuadro
        final es el propio (ver `_SPRITE_FW`/`_SPRITE_FH`), no el de zona.

        Sin cuadro de "muerte" en el roster: se reutiliza "herido" para
        `die`, igual que en `WalkerRaton` y por el mismo motivo.
        """
        super()._load_extra_sprites(zone, fw, fh)
        path = _SPRITE_DIR / "sprite_cucaracha.png"
        try:
            cuadros = AssetLoader.load_sprite_sheet(path, self._SPRITE_FW, self._SPRITE_FH)
            self._sprite_fw = self._SPRITE_FW
            self._sprite_fh = self._SPRITE_FH
            self._sprite_frames["fly"] = [cuadros[0], cuadros[1]]
            self._sprite_frames["hurt"] = [cuadros[2]]
            self._sprite_frames["die"] = [cuadros[2]]
        except (pygame.error, FileNotFoundError, PermissionError, IndexError):
            logger.warning("FlyingCucaracha: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        self._curve_t = (self._curve_t + dt / self.CURVE_PERIOD) % 2.0
        t = self._curve_t if self._curve_t <= 1.0 else 2.0 - self._curve_t
        target = CurveTools.build_bezier_path(self._curve_points, t)
        prev_x = self.position.x
        self.position.x, self.position.y = target.x, target.y
        if abs(self.position.x - prev_x) > 0.01:
            self.facing_direction = 1 if self.position.x >= prev_x else -1

    def _alert_behavior(self, dt: float) -> None:
        """Sigue volando la misma curva — deliberadamente NO llama a
        super()._alert_behavior(dt) (la persecución sine/dive-bomb del
        framework) — y dispara al jugador con cooldown en vez de
        perseguir."""
        self._patrol_behavior(dt)
        self._shoot_cooldown -= dt
        if self._shoot_cooldown <= 0:
            self._fire_at_player()
            self._shoot_cooldown = self.FIRE_COOLDOWN

    def _search_behavior(self, dt: float) -> None:
        """Misma política de "nunca abandona la curva" que
        _alert_behavior.

        El code review detectó esto: el _search_behavior por defecto de
        EnemyBase (enemy_base.py) camina derecho hacia `_last_seen.x` sin
        ninguna noción de la curva, lo que — porque SEARCH también se
        dispara acá en cada ciclo de detectar-y-perder-de-vista — hacía
        que la cucaracha se saliera del arco en línea recta hasta por 3
        segundos y después se teletransportara de vuelta al reanudarse
        PATROL. Delegar a _patrol_behavior la mantiene en la curva todo
        el tiempo en cambio.
        """
        self._patrol_behavior(dt)

    def _should_retreat(self) -> bool:
        """La cucaracha no huye con poca vida (AUD-644, playtest del dueño
        del 26/8: abandonaba su curva Catmull-Rom).

        Mismo motivo que WalkerRaton._should_retreat de más arriba, con un
        agravante propio de esta clase: _retreat_behavior heredado de
        EnemyBase mueve position.x/y en línea recta lejos del jugador, sin
        ninguna noción de _curve_points -- exactamente el mismo tipo de
        "se sale del arco" que _search_behavior de arriba ya evita para
        SEARCH. Anular sólo _retreat_behavior no alcanza: EnemyBase._run_
        state_machine (enemy_base.py:923-931) entra en RETREAT en cuanto
        _should_retreat() da True y no vuelve a salir mientras la vida no
        se regenere, así que un no-op ahí la dejaría congelada en RETREAT
        para siempre en vez de seguir su curva y disparando (comprobado
        en headless con WalkerRaton, mismo mecanismo). Anular acá evita
        que entre siquiera. El roster (docs/18_ENEMY_ROSTER.md #2.5) no
        menciona que la cucaracha huya.
        """
        return False

    def _retreat_behavior(self, dt: float) -> None:
        """No-op -- ver _should_retreat de arriba. El repliegue heredado
        de EnemyBase (enemy_base.py:1091-1099) rompería la curva propia
        además de no chequear paredes ni bordes."""

    def _fire_at_player(self) -> None:
        """Lanza un proyectil hacia la posición actual del jugador.

        Mismo apuntado con atan2 + construcción de Projectile que usa
        EnemyShooter._fire() (enemy_shooter.py) — importado y
        reutilizado, no reimplementado, porque una segunda clase de
        proyectil ligeramente distinta viviendo acá sería exactamente el
        tipo de código que se ve ajeno que las propias convenciones del
        profe evitan.
        """
        if self._player_ref is None:
            return
        dx = self._player_ref.centerx - self.rect.centerx
        dy = self._player_ref.centery - self.rect.centery
        angle = math.atan2(dy, dx)
        velocity = pygame.Vector2(
            math.cos(angle) * self.PROJECTILE_SPEED,
            math.sin(angle) * self.PROJECTILE_SPEED,
        )
        projectile = Projectile(
            spawn_position=pygame.Vector2(self.rect.centerx, self.rect.centery),
            velocity=velocity,
            damage=self.PROJECTILE_DAMAGE,
            lifetime=3.0,
        )
        self._active_projectiles.append(projectile)
        # AUD-489 — mismo patrón que VFX_PARRY más abajo: sin `pos`,
        # `sonido.py._make_sfx_handler` cae al canal ciego (`_play_sfx_named`)
        # en vez del posicional (`_play_sfx_spatial`). Mismo punto que
        # spawn_position del Projectile de arriba, no uno inventado.
        self._event_bus.emit(
            Events.SFX_PROJECTILE_FIRE,
            pos=(self.rect.centerx, self.rect.centery),
        )

    def _post_update(self, dt: float) -> None:
        """Avanza/expira los proyectiles — el mismo punto de extensión
        que EnemyBase documenta como "Used by EnemyShooter to update
        projectiles" (enemy_base.py), reutilizado acá para el mismo
        propósito."""
        for projectile in self._active_projectiles:
            projectile.update(dt)
            if projectile.is_active and self._collision_rects:
                for rect in self._collision_rects:
                    if projectile.rect.colliderect(rect):
                        projectile.on_collision()
                        break
        self._active_projectiles = [p for p in self._active_projectiles if p.is_active]

    def _check_player_contact(self, player) -> None:
        """Contacto de cuerpo (heredado) más contacto proyectil-vs-jugador
        — misma estructura que EnemyShooter._check_player_contact,
        incluyendo soporte de parry."""
        super()._check_player_contact(player)
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for projectile in list(self._active_projectiles):
            if projectile.is_active and projectile.rect.colliderect(player_hurtbox):
                if getattr(player, "_parry_active", False) and getattr(player, "_parry_window", 0) > 0:
                    projectile._expired = True
                    projectile.is_active = False
                    # AUD-206: mismo canónico que el parry cuerpo a cuerpo de
                    # enemy_base.py — sin stun(), parar la bandeja/proyectil
                    # no aturdía a quien la lanzó, así que no había ninguna
                    # recompensa por leer un ataque a distancia en vez de
                    # esquivarlo.
                    self.stun(self._aturdimiento_por_parry())
                    player._parry_success = True
                    player._parry_active = False
                    player._parry_window = 0.0
                    self._event_bus.emit(Events.VFX_PARRY, pos=(projectile.position.x, projectile.position.y))
                    # AUD-064 / AUD-489: parar es la acción más difícil del
                    # juego y el parry a distancia era mudo. Mismo `pos` que
                    # VFX_PARRY en la línea de arriba, para que el sonido
                    # venga del mismo sitio que el destello.
                    self._event_bus.emit(Events.SFX_PLAYER_PARRY, pos=(projectile.position.x, projectile.position.y))
                else:
                    player.apply_damage(projectile.damage, (self.position.x, self.position.y))
                    projectile.on_collision()

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        for projectile in self._active_projectiles:
            projectile.draw(surface, camera_offset)


class WalkerCulebra(_GolpeYMuerteVisibles, EnemyWalker):
    """Serpiente del camino exterior a La Soda.

    Copia literal del comportamiento de `WalkerRaton` — misma patrulla que
    nunca persigue, mismo scent-lock vectorial explícito, mismo
    `_clamp_to_walls` y mismo re-anclado al piso tras un golpe (ver esa
    clase para el porqué de cada uno: son fixes de bugs reales encontrados
    jugando, no cosmética). Solo cambian los sprites.

    AUD-637 — el prefijo `Walker` es lo que hace que
    `ScoreSystem._tipo_de` (score_system.py:83-97, subcadena del nombre de
    clase en minúsculas) reconozca a este enemigo como "walker". Antes se
    llamaba `Culebra` a secas: sin "walker" ni "flying" en el nombre, caía
    al valor por defecto (50 puntos / 1 moneda) en vez de cobrar 100/2
    como su clon `WalkerRaton`. El nombre "de juego" (culebra, en el .tmx,
    los sprites, la clave de registro) no cambia.
    """

    SCENT_LOCK_DOT: float = 0.8
    SCENT_LOCK_BURST: float = 14.0

    def __init__(self, spawn_position: pygame.Vector2, **kwargs) -> None:
        kwargs.setdefault("patrol_length", 128.0)
        kwargs.setdefault("patrol_speed", 55.0)
        kwargs.setdefault("alert_speed", 90.0)
        kwargs.setdefault("damage_on_contact", 0.25)
        kwargs.setdefault("max_health", 1.0)
        kwargs.pop("detection_range_x", None)
        super().__init__(spawn_position, **kwargs)
        self.detection_range_x = 96.0
        self._deactivated: bool = False

    #: AUD-648 — 32x16, no cuadrado: la culebra es "ancha y baja" (roster,
    #: clon de terciopelo). Mismo mecanismo de reasignación de
    #: `_sprite_fw`/`_sprite_fh` que `WalkerRaton` (ver ese docstring).
    _SPRITE_FW: int = 32
    _SPRITE_FH: int = 16

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Hoja propia de la culebra (`sprite_culebra.png`, 4 cuadros de
        32x16: ondular x2, ataque x1 con la cabeza alzada, herido x1) — el
        "ataque" no tiene clave de estado propia (esta clase nunca llama a
        `EnemyWalker._alert_behavior`, así que la carga heredada nunca se
        dispara) y queda sin cablear, igual que "mordida" en `WalkerRaton`.
        `die` reutiliza "herido" por el mismo motivo que las otras cuatro
        plagas: el roster no pide un cuadro de muerte distinto.
        """
        super()._load_extra_sprites(zone, fw, fh)
        path = _SPRITE_DIR / "sprite_culebra.png"
        try:
            cuadros = AssetLoader.load_sprite_sheet(path, self._SPRITE_FW, self._SPRITE_FH)
            self._sprite_fw = self._SPRITE_FW
            self._sprite_fh = self._SPRITE_FH
            self._sprite_frames["walk"] = [cuadros[0], cuadros[1]]
            self._sprite_frames["hurt"] = [cuadros[3]]
            self._sprite_frames["die"] = [cuadros[3]]
        except (pygame.error, FileNotFoundError, PermissionError, IndexError):
            logger.warning("WalkerCulebra: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        if self._deactivated:
            return
        # AUD-455: la `y` del `.tmx` es la esquina superior y el framework ya
        # no le resta `rect.height`, así que `_patrol_origin.y` ya es la
        # altura de reposo. Mismo razonamiento que en `WalkerRaton`.
        resting_y = self._patrol_origin.y
        if abs(self.position.y - resting_y) > 0.5:
            self.position.y = resting_y
            self.rect.y = int(self.position.y)

        half_width = self.patrol_length / 2.0
        min_x = self._patrol_origin.x - half_width
        max_x = self._patrol_origin.x + half_width
        if self.position.x < min_x or self.position.x > max_x:
            self.facing_direction = 1 if self.position.x < self._patrol_origin.x else -1
            self.position.x += self.facing_direction * self.patrol_speed * dt
            self._clamp_to_walls()
            return
        super()._patrol_behavior(dt)
        self._clamp_to_walls()

    def _alert_behavior(self, dt: float) -> None:
        if self._deactivated:
            return
        self._patrol_behavior(dt)
        if self._player_ref is None:
            return
        player_pos = pygame.Vector2(self._player_ref.center)
        self_pos = pygame.Vector2(self.rect.center)
        to_player = player_pos - self_pos
        distance = vec2_distance(player_pos, self_pos)
        if distance <= 0:
            return
        direction = vec2_normalize(to_player)
        facing = pygame.Vector2(self.facing_direction, 0.0)
        if vec2_dot(direction, facing) > self.SCENT_LOCK_DOT:
            prev_x = self.position.x
            self.position.x += direction.x * self.SCENT_LOCK_BURST * dt
            half_width = self.patrol_length / 2.0
            min_x = self._patrol_origin.x - half_width
            max_x = self._patrol_origin.x + half_width
            if min_x <= prev_x <= max_x:
                self.position.x = max(min_x, min(max_x, self.position.x))
            self._clamp_to_walls()

    def _search_behavior(self, dt: float) -> None:
        if self._deactivated:
            return
        self._patrol_behavior(dt)

    def _should_retreat(self) -> bool:
        """No huye con poca vida -- mismo motivo que WalkerRaton._should_
        retreat (AUD-644): anular sólo _retreat_behavior dejaría a la
        serpiente congelada en RETREAT en vez de seguir patrullando/
        atacando, porque EnemyBase._run_state_machine no sale de RETREAT
        mientras _should_retreat() siga dando True (enemy_base.py:923-931)
        y la vida no se regenera. El roster (docs/18_ENEMY_ROSTER.md,
        clon de WalkerRaton #2.4) no menciona que huya.
        """
        return False

    def _retreat_behavior(self, dt: float) -> None:
        """No-op -- ver _should_retreat de arriba. El repliegue heredado
        de EnemyBase (enemy_base.py:1091-1099) no chequea paredes ni
        bordes, y el camino exterior tiene esquinas igual que la sala."""

    def deactivate(self) -> None:
        """Se llama una sola vez al cruzar la puerta hacia el interior —
        esta entidad vive en el camino exterior, ya inalcanzable e
        invisible tras la transición de cuarto, pero seguía viva y
        podía seguir detectando/dañando al jugador (no hay pared física
        en la puerta, solo un marcador de cámara). Congela patrulla,
        alerta y búsqueda de una sola vez."""
        self._deactivated = True

    def _clamp_to_walls(self) -> None:
        rect = pygame.Rect(
            int(self.position.x), int(self.position.y),
            self.rect.width, self.rect.height,
        )
        for tile in self._collision_rects:
            if tile.width > 16:
                continue
            if rect.colliderect(tile):
                if rect.centerx < tile.centerx:
                    self.position.x = tile.left - rect.width - 1
                else:
                    self.position.x = tile.right + 1
                rect.x = int(self.position.x)


class FlyingZancudo(_GolpeYMuerteVisibles, EnemyFlying):
    """Mosquito del camino exterior a La Soda.

    Copia literal del comportamiento de `FlyingCucaracha`: patrulla una
    curva Catmull-Rom explícita y dispara un `Projectile` del framework en
    ALERT — `FlyingCucaracha` ya es "vuela en curva + dispara", así que no
    hace falta mecánica nueva. Solo cambian sprites y algunos números.

    AUD-637 — el prefijo `Flying` es lo que hace que
    `ScoreSystem._tipo_de` (score_system.py:83-97, subcadena del nombre de
    clase en minúsculas) reconozca a este enemigo como "flying". Antes se
    llamaba `Zancudo` a secas: sin "walker" ni "flying" en el nombre, caía
    al valor por defecto (50 puntos / 1 moneda) en vez de cobrar 150/2
    como su clon `FlyingCucaracha`. El nombre "de juego" (zancudo, en el
    .tmx, los sprites, la clave de registro) no cambia.
    """

    CONTROL_POINTS: list[tuple[float, float]] = [
        (-40.0, 10.0),
        (-14.0, -18.0),
        (14.0, -18.0),
        (40.0, 10.0),
    ]
    CURVE_PERIOD: float = 2.6

    PROJECTILE_SPEED: float = 130.0
    PROJECTILE_DAMAGE: float = 0.25
    FIRE_COOLDOWN: float = 1.5

    def __init__(self, spawn_position: pygame.Vector2, **kwargs) -> None:
        kwargs.setdefault("flight_speed", 50.0)
        kwargs.setdefault("sine_amplitude", 16.0)
        kwargs.setdefault("sine_frequency", 2.0)
        kwargs.setdefault("damage_on_contact", 0.25)
        kwargs.setdefault("max_health", 1.0)
        super().__init__(spawn_position, **kwargs)
        self._curve_points: list[pygame.Vector2] = [
            pygame.Vector2(spawn_position.x + dx, spawn_position.y + dy)
            for dx, dy in self.CONTROL_POINTS
        ]
        # Rango vertical que ya cubría la spline Catmull-Rom de la
        # flotación: el punto más bajo es el primer punto de control (t=0)
        # y el más alto es el valor de la curva a mitad de parámetro
        # (t=0.5, el tope del arco). Se recortan de la curva para que el
        # easing de _patrol_behavior cambie la CURVA temporal de la `y`
        # pero no su RANGO — la Tarea 3 pide explícitamente no mover la
        # altura de la patrulla.
        self._float_bottom_y = self._curve_points[0].y
        self._float_top_y = CurveTools.build_bezier_path(self._curve_points, 0.5).y
        self._curve_t: float = 0.0
        self._active_projectiles: list[Projectile] = []
        self._shoot_cooldown: float = 0.0
        self._deactivated: bool = False

    #: AUD-648 — mismo mecanismo que `FlyingCucaracha._SPRITE_FW/_FH`.
    _SPRITE_FW: int = 24
    _SPRITE_FH: int = 24

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Hoja propia del zancudo (`sprite_zancudo.png`, 3 cuadros de
        24x24: volar x2, herido x1) — mismo patrón que
        `FlyingCucaracha._load_extra_sprites` (esta clase es su clon,
        AUD-637)."""
        super()._load_extra_sprites(zone, fw, fh)
        path = _SPRITE_DIR / "sprite_zancudo.png"
        try:
            cuadros = AssetLoader.load_sprite_sheet(path, self._SPRITE_FW, self._SPRITE_FH)
            self._sprite_fw = self._SPRITE_FW
            self._sprite_fh = self._SPRITE_FH
            self._sprite_frames["fly"] = [cuadros[0], cuadros[1]]
            self._sprite_frames["hurt"] = [cuadros[2]]
            self._sprite_frames["die"] = [cuadros[2]]
        except (pygame.error, FileNotFoundError, PermissionError, IndexError):
            logger.warning("FlyingZancudo: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        if self._deactivated:
            return
        self._curve_t = (self._curve_t + dt / self.CURVE_PERIOD) % 2.0
        t = self._curve_t if self._curve_t <= 1.0 else 2.0 - self._curve_t
        target = CurveTools.build_bezier_path(self._curve_points, t)
        prev_x = self.position.x
        self.position.x = target.x
        # Evaluación Práctica II (Unidad VI): la flotación vertical usa
        # ease_in_out_quad (engine/utils/math_utils.py) compuesto en una
        # campana 4u(1-u). La `y` de la spline muestreada con `t` lineal
        # baja y sube a ~21 px/s justo en el giro del fondo (medido); la
        # campana anula la velocidad ahí y la deja máxima a mitad de
        # altura — la forma de una flotación. El rango vertical queda
        # idéntico al de la curva (_float_bottom_y/_float_top_y, ver
        # __init__): esto cambia la curva temporal de la `y`, no su altura.
        u = ease_in_out_quad(t)
        campana = 4.0 * u * (1.0 - u)
        self.position.y = self._float_bottom_y + (
            self._float_top_y - self._float_bottom_y
        ) * campana
        if abs(self.position.x - prev_x) > 0.01:
            self.facing_direction = 1 if self.position.x >= prev_x else -1

    def _alert_behavior(self, dt: float) -> None:
        if self._deactivated:
            return
        self._patrol_behavior(dt)
        self._shoot_cooldown -= dt
        if self._shoot_cooldown <= 0:
            self._fire_at_player()
            self._shoot_cooldown = self.FIRE_COOLDOWN

    def _search_behavior(self, dt: float) -> None:
        if self._deactivated:
            return
        self._patrol_behavior(dt)

    def _should_retreat(self) -> bool:
        """No huye con poca vida -- mismo motivo que FlyingCucaracha.
        _should_retreat (AUD-644): _retreat_behavior heredado de
        EnemyBase movería position.x/y en línea recta lejos del jugador
        sin ninguna noción de _curve_points, rompiendo la flotación
        propia (el rango _float_bottom_y/_float_top_y de _patrol_
        behavior). Anular sólo _retreat_behavior no alcanza: EnemyBase.
        _run_state_machine no sale de RETREAT mientras _should_retreat()
        siga dando True (enemy_base.py:923-931) y la vida no se regenera,
        así que un no-op ahí dejaría al mosquito congelado en vez de
        seguir su curva y disparando. El roster (docs/18_ENEMY_ROSTER.md,
        clon de FlyingCucaracha #2.5) no menciona que huya.
        """
        return False

    def _retreat_behavior(self, dt: float) -> None:
        """No-op -- ver _should_retreat de arriba."""

    def deactivate(self) -> None:
        """Igual que WalkerCulebra.deactivate, más vaciar los proyectiles ya
        en vuelo — sin esto, un proyectil lanzado justo antes de cruzar
        la puerta seguiría viajando y podría golpear al jugador ya en
        el interior."""
        self._deactivated = True
        self._active_projectiles = []

    def _fire_at_player(self) -> None:
        if self._player_ref is None:
            return
        dx = self._player_ref.centerx - self.rect.centerx
        dy = self._player_ref.centery - self.rect.centery
        angle = math.atan2(dy, dx)
        velocity = pygame.Vector2(
            math.cos(angle) * self.PROJECTILE_SPEED,
            math.sin(angle) * self.PROJECTILE_SPEED,
        )
        projectile = Projectile(
            spawn_position=pygame.Vector2(self.rect.centerx, self.rect.centery),
            velocity=velocity,
            damage=self.PROJECTILE_DAMAGE,
            lifetime=3.0,
        )
        self._active_projectiles.append(projectile)
        # AUD-489 — mismo patrón que VFX_PARRY más abajo (y que
        # FlyingCucaracha._fire_at_player): sin `pos`,
        # `sonido.py._make_sfx_handler` cae al canal ciego en vez del
        # posicional. Mismo punto que spawn_position del Projectile de
        # arriba, no uno inventado.
        self._event_bus.emit(
            Events.SFX_PROJECTILE_FIRE,
            pos=(self.rect.centerx, self.rect.centery),
        )

    def _post_update(self, dt: float) -> None:
        for projectile in self._active_projectiles:
            projectile.update(dt)
            if projectile.is_active and self._collision_rects:
                for rect in self._collision_rects:
                    if projectile.rect.colliderect(rect):
                        projectile.on_collision()
                        break
        self._active_projectiles = [p for p in self._active_projectiles if p.is_active]

    def _check_player_contact(self, player) -> None:
        super()._check_player_contact(player)
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for projectile in list(self._active_projectiles):
            if projectile.is_active and projectile.rect.colliderect(player_hurtbox):
                if getattr(player, "_parry_active", False) and getattr(player, "_parry_window", 0) > 0:
                    projectile._expired = True
                    projectile.is_active = False
                    # AUD-206: mismo canónico que el parry cuerpo a cuerpo de
                    # enemy_base.py (y que FlyingCucaracha._check_player_contact)
                    # — sin stun(), parar el proyectil no aturdía a quien lo
                    # lanzó, así que no había ninguna recompensa por leer un
                    # ataque a distancia en vez de esquivarlo.
                    self.stun(self._aturdimiento_por_parry())
                    player._parry_success = True
                    player._parry_active = False
                    player._parry_window = 0.0
                    self._event_bus.emit(Events.VFX_PARRY, pos=(projectile.position.x, projectile.position.y))
                    # AUD-064 / AUD-489: parar es la acción más difícil del
                    # juego y el parry a distancia era mudo. Mismo `pos` que
                    # VFX_PARRY en la línea de arriba, para que el sonido
                    # venga del mismo sitio que el destello.
                    self._event_bus.emit(Events.SFX_PLAYER_PARRY, pos=(projectile.position.x, projectile.position.y))
                else:
                    player.apply_damage(projectile.damage, (self.position.x, self.position.y))
                    projectile.on_collision()

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        for projectile in self._active_projectiles:
            projectile.draw(surface, camera_offset)


class ShooterCocinero(_GolpeYMuerteVisibles, EnemyShooter):
    """Cocinero fijo detrás del mostrador (docs/18_ENEMY_ROSTER.md #2.6).

    A diferencia de WalkerCulebra/FlyingZancudo, EnemyShooter ya implementa
    exactamente lo que pide el roster: estacionario por defecto
    (patrol_length=0.0 no mueve nada, ver enemy_shooter.py línea 238) y
    una máquina de estados de apuntar-y-disparar ya armada
    (_alert_behavior → TELEGRAPHING → _firing_behavior, con atan2 hacia
    el jugador). Solo fijar los stats del roster y cargar sprites propios.

    Code review encontró que patrol_length=0.0 solo desactiva
    EnemyShooter._patrol_behavior — _search_behavior y _retreat_behavior,
    heredados de EnemyBase, siguen moviendo a la entidad (caminan hacia
    _last_seen.x o se alejan del jugador con poca vida) y no tienen
    chequeo de piso propio, así que caminar fuera de la repisa lo dejaría
    flotando en el aire. Mismo patrón que WalkerRaton/FlyingCucaracha:
    ambos se sobreescriben como no-op más abajo.

    AUD-643 — se queda flotando tras recibir golpes (reporte del dueño:
    "lo intenté matar pero en una quedó como flotando y no le llegaba a
    pegar"). Diagnosticado en headless llamando a `apply_hit` directo y
    registrando `position.y`/`_knockback_velocity.y` fotograma a
    fotograma (sin pasar por el jugador ni por Tiled, mismo patrón que ya
    usan las pruebas de sonido/parry de este archivo, ver el comentario
    de más arriba): la causa NO es la IA (`_search_behavior`/
    `_retreat_behavior` ya son no-op, ver arriba) sino
    `EnemyBase.apply_hit`/`_run_state_machine` (`enemy_base.py:526-552,
    870-881`), que sólo aplica gravedad y sólo comprueba el aterrizaje
    mientras `state == EnemyState.LAUNCHED` (golpes >=1.5 de daño). Un
    golpe "heavy" (0.8-1.49, el rango del ataque normal del jugador) o
    "light" (<0.8) deja `state = HURT` con `_knockback_velocity.y` en
    -100/-30 **sin** pasar nunca por LAUNCHED: nada vuelve a sumar
    gravedad ni comprueba el suelo, así que ese impulso hacia arriba sólo
    decae por fricción (`_apply_knockback`, factor 0.85 por fotograma) y
    se queda en 0 con el cocinero suspendido en el aire para siempre.
    Medido con tres `apply_hit(1.0, ...)` seguidos (daño "heavy", el que
    dispara este caso): -11px por golpe, -22px acumulados al segundo
    golpe, nunca vuelve a bajar. (El golpe "launch", >=1.5, tiene además
    su propio bug de encuadre —`_ground_y` se fija al `position.y`
    *anterior* al primer fotograma de física del lanzamiento, así que el
    chequeo de aterrizaje lo encuentra trivialmente cumplido y cancela el
    salto entero en el mismo fotograma— pero ninguno de los dos casos es
    arreglable sin tocar `enemy_base.py`, fuera de alcance de esta
    entrega.)

    Arreglo en código propio: el roster dice "cocinero fijo detrás del
    mostrador", así que `update()` se sobreescribe para anclarlo de
    verdad tras cada fotograma —`position.y`/`rect.y` de vuelta a la
    altura de la repisa, `position.x` recortado a su ancho (2944-3072,
    `Cocina_Repisa` en el .tmx) por si el empuje horizontal del golpe lo
    saca del tablón— salvo mientras `state == LAUNCHED`, para no pelear
    con la única rama del motor que sí sabe hacer aterrizar a un
    enemigo. `EnemyState` no estaba importado en este módulo; se agrega
    sólo para esta comprobación.

    AUD-651 — segunda fase "enfurecido" al <=50% de vida. Playtest del
    dueño: con 3.0 de vida (el valor original) lo mató en ~20s tras
    aprender el patrón, y ahora que `Door_Trasera` exige vencerlo
    (AUD-641) eso es poco para un "mini-jefe" que traba la salida. Se
    sube `max_health` a 5.0 y se agrega una fase de rabia con tres
    señales — más veloz, telegrafía menos, tira doble — más una cuarta
    puramente informativa (tinte + cartel), medida en
    `Claude - Uso General/playtest/medir_cocinero_aud651.py` (ver ese
    script para las cifras de justicia antes/después).

    Mecanismo de la fase 2 (`_entrar_en_fase2`, más abajo): se dispara
    UNA vez desde `update()` cuando `current_health` cruza el 50% de
    `max_health`, y modifica sólo ATRIBUTOS DE INSTANCIA que el motor ya
    expone —`fire_rate` (`EnemyShooter.__init__`, gobierna el cooldown
    real vía `1.0/fire_rate` en `_firing_behavior`,
    `enemy_shooter.py:332`) y `_telegraph_duration`
    (`EnemyBase.__init__`, `enemy_base.py:137`)— nunca la clase: como
    ambos ya son de instancia, una instancia NUEVA tras el respawn
    (`_construir_escena_la_soda` recrea el `ShooterCocinero` entero, ver
    `TestPuertaDelCocinero.test_respawn_...` en `test_la_soda.py`) los
    repone a sus valores originales sin arrastrar memoria de la fase
    anterior. El lanzamiento doble (`_fire`/`_post_update` más abajo)
    envuelve el `_fire()` real del motor con `super()` en vez de
    reimplementar el disparo, y agenda el segundo proyectil con un
    temporizador propio porque el roster pide una SEGUNDA sartén con
    0.2s de demora, no dos sartenes simultáneas. El tinte
    (`_dibujar_tinte_fase2`, en `draw()` más abajo) reordena la cadena
    de `super()` en vez de llamarla entera de un tirón, para que el
    destello de golpe del mixin (blanco) pueda dibujarse ENCIMA del
    tinte (rojo) en vez de que uno tape al otro — ver el comentario
    dentro de `draw()` para el porqué completo.
    """

    #: `Cocina_Repisa` en el .tmx: x=2944, ancho=128 -> jamba derecha en
    #: 3072. Se resta el ancho del cocinero (16px) para que el CUERPO
    #: entero quede dentro del tablón, no sólo su esquina izquierda.
    X_MIN_REPISA: float = 2944.0
    X_MAX_REPISA: float = 3072.0 - 16.0

    #: AUD-651 — fase 2 ("enfurecido") al cruzar este umbral de vida.
    FASE2_UMBRAL_VIDA: float = 0.5
    #: Cooldown entre lanzamientos en fase 2 = éste × el normal. Se
    #: implementa subiendo `fire_rate` (disparos/seg) a `fire_rate /
    #: FASE2_COOLDOWN_MULT`, no multiplicándolo, porque el cooldown real
    #: es `1.0/fire_rate` (inverso) — ver el docstring de la clase.
    FASE2_COOLDOWN_MULT: float = 0.6
    #: Duración del telegrafiado en fase 2 = ésta × la normal.
    FASE2_TELEGRAPH_MULT: float = 0.75
    #: `BLEND_RGB_MULT` contra este color = tinte rojizo del roster.
    FASE2_TINTE_COLOR: tuple[int, int, int] = (255, 150, 150)
    #: Demora entre el primer y el segundo proyectil del lanzamiento doble.
    SEGUNDO_DISPARO_RETRASO: float = 0.2
    #: Ángulo (grados) del segundo proyectil respecto al primero. El signo
    #: alterna en cada disparo doble (`_signo_angulo_doble`, ver `_fire`)
    #: para que la dispersión sea a ambos lados a lo largo de la pelea, no
    #: siempre hacia el mismo costado.
    SEGUNDO_DISPARO_ANGULO: float = 12.0
    MENSAJE_ENFURECIDO: str = "¡El cocinero se enfurece!"
    #: Mismo orden de magnitud que `_RecompensaDePickup.DURACION_MENSAJE`
    #: (`stage1_2_la_soda.py`, 1.5s) pero un poco más largo: un aviso de
    #: mini-jefe cambiando de fase es más importante que un cartel de
    #: pickup y vale la pena que se lea completo.
    DURACION_MENSAJE_ENFURECIDO: float = 2.0

    #: AUD-648 — mismo mecanismo de reasignación de `_sprite_fw`/
    #: `_sprite_fh` que las otras cuatro plagas (ver el docstring de
    #: `WalkerRaton` para el porqué completo). 32x32: el roster pide un
    #: cocinero de 16x24 y a ese tamaño de zona (12x12 para EnemyShooter)
    #: la escena ya mostraba una mancha morada sin gorro ni sartén
    #: reconocibles.
    _SPRITE_FW: int = 32
    _SPRITE_FH: int = 32

    #: Añade la clave "telegraph" (ver `_get_animation_key` más abajo) al
    #: mapa de FPS por estado de `EnemyShooter` (enemy_shooter.py:154-157).
    #: Un solo cuadro por hoja hace que el número en sí no cambie nada
    #: visible, pero sin esta entrada `_advance_animation`
    #: (enemy_base.py:314-327) caería al 10.0 por defecto sin que quedara
    #: escrito en ningún sitio que es a propósito.
    _ANIM_FPS = {**EnemyShooter._ANIM_FPS, "telegraph": 8.0}

    def __init__(self, spawn_position: pygame.Vector2, **kwargs) -> None:
        kwargs.setdefault("fire_rate", 0.5)
        kwargs.setdefault("projectile_speed", 110.0)
        kwargs.setdefault("projectile_damage", 0.50)
        kwargs.setdefault("max_health", 5.0)
        kwargs.setdefault("damage_on_contact", 0.25)
        kwargs.setdefault("patrol_length", 0.0)
        super().__init__(spawn_position, **kwargs)
        #: Altura de anclaje — la de spawn, no `_ground_y` (que el propio
        #: motor reescribe en cada golpe "launch" y puede quedar fijada a
        #: una altura ya en el aire, ver el docstring de la clase).
        self._y_repisa: float = float(spawn_position.y)
        #: AUD-648 — cuenta fotogramas DIBUJADOS (no de simulación) para el
        #: destello de telegrafiado de `draw()`. Fotogramas de dibujo y no
        #: un temporizador en segundos porque "2 de cada 6" es una cadencia
        #: de parpadeo clásica de sprite (2 visibles, 4 apagados) y tiene
        #: que ser literal cuadro a cuadro, no aproximada por dt.
        self._telegraph_flash_frame: int = 0
        #: AUD-651 — estado de la fase 2, todo de instancia (ver el
        #: docstring de la clase sobre por qué el respawn lo resetea solo).
        self._fase2: bool = False
        #: Lanzamiento doble en vuelo: demora restante hasta crear el
        #: segundo proyectil, y los datos ya calculados (posición/
        #: velocidad/daño/bash) para crearlo tal cual sin volver a leer
        #: `self._player_ref` (que pudo moverse en esos 0.2s -- el segundo
        #: tiro sale del MISMO punto que el primero, sólo rotado, no
        #: vuelve a apuntar).
        self._segundo_disparo_retraso: float = 0.0
        self._segundo_disparo_spawn: pygame.Vector2 | None = None
        self._segundo_disparo_velocidad: pygame.Vector2 | None = None
        self._segundo_disparo_damage: float = 0.0
        self._segundo_disparo_bash: bool = False
        #: +1/-1, alterna en cada disparo doble (ver `SEGUNDO_DISPARO_ANGULO`).
        self._signo_angulo_doble: int = 1

    def update(self, dt: float) -> None:
        super().update(dt)
        if not self.is_alive:
            return
        if not self._fase2 and self.current_health <= self.max_health * self.FASE2_UMBRAL_VIDA:
            self._entrar_en_fase2()
        if self.state == EnemyState.LAUNCHED:
            # Fotograma de un lanzamiento en curso: se deja que
            # EnemyBase intente aterrizarlo por su cuenta (ver el
            # docstring de la clase sobre por qué hoy no lo consigue) en
            # vez de pelear con esa rama del motor.
            return
        self.position.y = self._y_repisa
        self.rect.y = int(self.position.y)
        self.position.x = max(self.X_MIN_REPISA, min(self.position.x, self.X_MAX_REPISA))
        self.rect.x = int(self.position.x)
        self._knockback_velocity.x = 0.0
        self._knockback_velocity.y = 0.0
        self._update_rects()

    def _entrar_en_fase2(self) -> None:
        """Activa la fase "enfurecido" (AUD-651) al cruzar el umbral de
        vida: sube la cadencia de disparo, acorta el telegrafiado y avisa
        una única vez por instancia — `self._fase2` hace de guardia contra
        re-entradas (una vez True nunca vuelve a False salvo respawn, así
        que `update()` sólo llama a este método una vez en la vida de la
        instancia) y a la vez de bandera que lee `_fire()`/`draw()` para
        el resto de las señales (lanzamiento doble, tinte).

        `fire_rate` es disparos/segundo; el cooldown real que arma
        `_firing_behavior` tras cada tiro es `1.0/fire_rate`
        (`enemy_shooter.py:332`) — por eso se divide, no se multiplica:
        con `fire_rate' = fire_rate/0.6`, `1/fire_rate' = 0.6 * (1/fire_rate)`,
        el cooldown real queda en 0.6× el original.
        """
        self._fase2 = True
        self.fire_rate = self.fire_rate / self.FASE2_COOLDOWN_MULT
        self._telegraph_duration *= self.FASE2_TELEGRAPH_MULT
        self._event_bus.emit(
            Events.SHOW_MESSAGE, text=self.MENSAJE_ENFURECIDO,
            duration=self.DURACION_MENSAJE_ENFURECIDO,
        )

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Hoja propia del cocinero (`sprite_cocinero.png`, 5 cuadros de
        32x32: idle x2, telegrafiar x1 con el brazo atrás, lanzar x1,
        herido x1) — "walk" (patrulla/reposo, el cocinero no camina) y
        "aim" (ALERT, apenas visible: el tirador genérico pasa a
        TELEGRAPHING en el mismo fotograma en que el cooldown está listo,
        `enemy_shooter.py:300-302`) reutilizan las dos poses de idle;
        "telegraph" y "fire" tienen cuadro propio cada una — ver
        `_get_animation_key` más abajo, que es lo que hace que el motor
        pida "telegraph" en vez de compartir "fire" con el disparo.

        Sin cuadro de "muerte" en el roster: se reutiliza "herido" para
        `die`, igual que las otras cuatro plagas.
        """
        super()._load_extra_sprites(zone, fw, fh)
        path = _SPRITE_DIR / "sprite_cocinero.png"
        try:
            cuadros = AssetLoader.load_sprite_sheet(path, self._SPRITE_FW, self._SPRITE_FH)
            self._sprite_fw = self._SPRITE_FW
            self._sprite_fh = self._SPRITE_FH
            self._sprite_frames["walk"] = [cuadros[0], cuadros[1]]
            self._sprite_frames["aim"] = [cuadros[0], cuadros[1]]
            self._sprite_frames["telegraph"] = [cuadros[2]]
            self._sprite_frames["fire"] = [cuadros[3]]
            self._sprite_frames["hurt"] = [cuadros[4]]
            self._sprite_frames["die"] = [cuadros[4]]
        except (pygame.error, FileNotFoundError, PermissionError, IndexError):
            logger.warning("ShooterCocinero: failed to load sprite %s", path)

    def _fire(self) -> bool:
        """Envuelve `EnemyShooter._fire` (motor) para, en fase 2, agendar
        un segundo proyectil 0.2s después con el mismo origen que el
        primero pero rotado ±12° (AUD-651) — "lanzamiento doble" de la
        fase de rabia. Se agenda con un temporizador propio
        (`_post_update`/`_lanzar_segundo_proyectil` más abajo) en vez de
        crearse en el acto porque el roster pide una SEGUNDA sartén CON
        demora, no dos sartenes simultáneas saliendo del mismo punto.

        El ángulo se aplica rotando el `velocity` (`pygame.Vector2`) del
        proyectil que el motor acaba de crear y agregar a
        `_active_projectiles` — `Projectile.velocity` ya es vectorial
        (`enemy_shooter.py:60`), así que rotarlo con `Vector2.rotate()` es
        directo, sin reimplementar el cálculo de `atan2` que hace
        `EnemyShooter._fire()`.
        """
        disparo_hecho = super()._fire()
        if disparo_hecho and self._fase2 and self._active_projectiles:
            original = self._active_projectiles[-1]
            self._segundo_disparo_retraso = self.SEGUNDO_DISPARO_RETRASO
            self._segundo_disparo_spawn = pygame.Vector2(original.position)
            self._segundo_disparo_velocidad = original.velocity.rotate(
                self._signo_angulo_doble * self.SEGUNDO_DISPARO_ANGULO
            )
            self._segundo_disparo_damage = original.damage
            self._segundo_disparo_bash = original.admite_bash
            self._signo_angulo_doble *= -1
        return disparo_hecho

    def _post_update(self, dt: float) -> None:
        """Adelanta el temporizador del segundo proyectil del lanzamiento
        doble (AUD-651), sobre el mismo punto de extensión que
        `EnemyShooter._post_update` ya usa para las actualizaciones
        propias de proyectiles (`enemy_shooter.py:444-454`)."""
        super()._post_update(dt)
        if self._segundo_disparo_retraso <= 0.0:
            return
        self._segundo_disparo_retraso -= dt
        if self._segundo_disparo_retraso <= 0.0:
            self._lanzar_segundo_proyectil()

    def _lanzar_segundo_proyectil(self) -> None:
        """Crea el segundo proyectil agendado por `_fire()`, con los datos
        (posición/velocidad/daño/bash) ya calculados en ese momento — no
        vuelve a apuntar al jugador, sale del mismo punto que el primero,
        sólo rotado.

        Mismo tope `_max_projectiles` que respeta `EnemyShooter._fire()`
        (`enemy_shooter.py:337-338`): si la cola ya está llena se descarta
        en silencio, igual que haría el motor con un tercer disparo.
        """
        spawn = self._segundo_disparo_spawn
        velocidad = self._segundo_disparo_velocidad
        self._segundo_disparo_spawn = None
        self._segundo_disparo_velocidad = None
        if spawn is None or velocidad is None:
            return
        if len(self._active_projectiles) >= self._max_projectiles:
            return
        proyectil = Projectile(
            spawn_position=spawn,
            velocity=velocidad,
            damage=self._segundo_disparo_damage,
            lifetime=3.0,
            admite_bash=self._segundo_disparo_bash,
        )
        self._active_projectiles.append(proyectil)
        # AUD-489 — mismo criterio que el disparo original: sonido posicional,
        # no el canal ciego (ver `EnemyShooter._fire`, enemy_shooter.py:367-370).
        self._event_bus.emit(
            Events.SFX_PROJECTILE_FIRE, pos=(proyectil.position.x, proyectil.position.y),
        )

    def _get_animation_key(self) -> str:
        """Separa TELEGRAPHING de FIRING con cuadros propios (AUD-648).

        `EnemyShooter._get_animation_key` (enemy_shooter.py:376-382, motor,
        de sólo lectura) devuelve la misma clave "fire" para los dos
        estados — en el tirador genérico son una sola animación de apuntar
        y soltar. El roster pide que el cocinero telegrafíe con un cuadro
        de "brazo atrás" reconocible ANTES de lanzar la sartén: sin una
        clave separada aquí, `_sprite_frames["fire"]` sería lo único que se
        dibuja durante todo el medio segundo de telegrafiado + disparo, y
        el jugador vería el cuadro de "ya lanzó" mientras el cocinero
        todavía está preparando el golpe — el telegrafiado dejaría de
        avisar nada.
        """
        if self.state == EnemyState.TELEGRAPHING:
            return "telegraph"
        return super()._get_animation_key()

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Dibuja al cocinero y, sólo durante TELEGRAPHING, un destello
        blanco del propio sprite 2 de cada 6 fotogramas dibujados
        (AUD-648).

        Los sprites por zona del motor son manchas de 16x12 que no se
        distinguen del piso de la cocina; con la hoja propia (32x32) el
        cuadro de "brazo atrás" ya es legible por sí solo, pero un ataque
        que va a doler se avisa mejor con una segunda señal que ENCIMA se
        pueda perder entre el mostrador, las cazuelas y el resto de
        plagas. `EnemyShooter.draw()` (enemy_shooter.py:425-438, motor) ya
        dibuja un anillo naranja en espacio de mundo alrededor del cuerpo
        durante este mismo estado — se conserva sin tocarlo (super()
        primero) y este destello es una señal adicional, sobre el propio
        sprite, con el mismo lenguaje visual que ya usa la invencibilidad
        tras un golpe (`_flash_visible`, enemy_base.py:736-746). Se
        implementa aparte porque esa invencibilidad no está activa durante
        el telegrafiado — no hay parpadeo que reutilizar.

        BLEND_RGB_ADD dejar el canal alfa intacto: cada píxel visible del
        sprite se aclara hacia blanco sin tocar la silueta transparente,
        así el destello no se ve como un cuadrado sino como el cocinero
        mismo brillando.

        AUD-651 — en fase 2 se intercala además el tinte rojizo
        (`_dibujar_tinte_fase2`) ENTRE el cuerpo y el destello de golpe
        del mixin (`_dibujar_destello_de_golpe`), en vez de llamar a
        `super().draw()` de un tirón como en fase 1. Motivo: los tres
        —cuerpo, tinte, destello— blitean una copia OPACA del cuadro
        activo sobre el mismo rect, así que el último en dibujarse
        reemplaza por completo a los anteriores ahí. `super().draw()`
        (`_GolpeYMuerteVisibles.draw`) ya encadena cuerpo+destello en ese
        orden sin dejar ningún hueco para meter el tinte en el medio, así
        que hace falta separar esa cadena: se llama directo a
        `EnemyShooter.draw()` (motor, cuerpo+anillo+proyectiles), después
        el tinte, y por último `_dibujar_destello_de_golpe` (mismo método
        del mixin, sólo que invocado en otro punto de la secuencia) —
        así un golpe durante la fase 2 se sigue viendo (destello encima
        de todo), y el resto del tiempo el tinte queda visible sin que el
        cuerpo sin teñir lo tape.
        """
        if not self.is_visible:
            return
        if self._fase2 and self.is_alive and self.state != EnemyState.DYING:
            EnemyShooter.draw(self, surface, camera_offset)
            self._dibujar_tinte_fase2(surface, camera_offset)
            self._dibujar_destello_de_golpe(surface, camera_offset)
        else:
            super().draw(surface, camera_offset)
        if not self.is_alive:
            return
        if self.state != EnemyState.TELEGRAPHING:
            self._telegraph_flash_frame = 0
            return
        self._telegraph_flash_frame = (self._telegraph_flash_frame + 1) % 6
        if self._telegraph_flash_frame >= 2:
            return
        frames = self._sprite_frames.get(self._get_animation_state())
        if not frames:
            return
        frame_idx = min(self._animation_frame, len(frames) - 1)
        if self.facing_direction < 0:
            base_frame = get_pool().get_flipped_frames(frames)[frame_idx]
        else:
            base_frame = frames[frame_idx]
        flash = base_frame.copy()
        flash.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)
        ox = (self.rect.width - self._sprite_fw) // 2
        oy = self.rect.height - self._sprite_fh
        surface.blit(flash, (screen_x + ox, screen_y + oy))

    def _dibujar_tinte_fase2(
        self, surface: pygame.Surface, camera_offset: pygame.Vector2,
    ) -> None:
        """Tiñe el cuadro activo de rojizo mientras dura la fase 2
        (AUD-651) — señal visible de "enfurecido", además del cartel de
        `_entrar_en_fase2` y el propio ritmo de disparo más rápido.

        Mismo patrón que `_dibujar_destello_de_golpe`/el destello de
        telegrafiado de `draw()`: copia del cuadro activo (respeta
        flip/frame igual que esos dos) en vez de un rectángulo aparte,
        para que sólo se tiña la silueta opaca del sprite y no un cuadrado
        de fondo — `BLEND_RGB_MULT` multiplica cada canal por
        `FASE2_TINTE_COLOR` respetando el alfa del cuadro original (los
        píxeles transparentes del sprite siguen transparentes).
        """
        frames = self._sprite_frames.get(self._get_animation_state())
        if not frames:
            return
        frame_idx = min(self._animation_frame, len(frames) - 1)
        if self.facing_direction < 0:
            base_frame = get_pool().get_flipped_frames(frames)[frame_idx]
        else:
            base_frame = frames[frame_idx]
        tinte = base_frame.copy()
        tinte.fill(self.FASE2_TINTE_COLOR, special_flags=pygame.BLEND_RGB_MULT)
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)
        ox = (self.rect.width - self._sprite_fw) // 2
        oy = self.rect.height - self._sprite_fh
        surface.blit(tinte, (screen_x + ox, screen_y + oy))

    def _search_behavior(self, dt: float) -> None:
        """Nunca abandona la repisa — mismo motivo que WalkerRaton/FlyingCucaracha:
        el _search_behavior heredado de EnemyBase camina hacia _last_seen.x sin
        límite, y como este enemigo no tiene chequeo de piso/gravedad propio
        (EnemyShooter no lo implementa), caminar fuera de la repisa lo dejaría
        flotando en el aire en vez de caer."""

    def _retreat_behavior(self, dt: float) -> None:
        """El cocinero está acorralado detrás de su repisa: no huye al quedar
        con poca vida, se queda a pelear — mismo motivo que _search_behavior
        de arriba (sin chequeo de piso propio, huir lo dejaría flotando)."""
