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

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.math_utils import vec2_distance, vec2_dot, vec2_normalize
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import Projectile
from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.processing.curve_tools import CurveTools

logger = logging.getLogger(__name__)

# Los sprites viven en la carpeta de assets propia y editable de la stage,
# no en el árbol compartido assets/sprites/enemies/zone*/ que usan por
# defecto esas clases base — mismo llamado a
# AssetLoader.load_sprite_sheet(), mismo contrato fw/fh, solo que la
# carpeta de origen es del estudiante.
_SPRITE_DIR = settings.ASSETS_DIR / "maps" / "stage1_2_la_soda"


class WalkerRaton(EnemyWalker):
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

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Sobreescribe el arte genérico del walker de zona1 con los
        sprites propios de la rata.

        Refleja el mismo patrón de carga de EnemyBase._load_zone_sprites
        (mismo llamado a AssetLoader, mismo try/except, mismas claves de
        diccionario) — este es el hook documentado del propio framework
        para que una subclase cargue sprites extra más allá de los
        genéricos walk/hurt/die (ver enemy_base.py), así la rata no se
        dibuja como el mismo mob genérico de zona1 que usa cualquier otro
        Walker.
        """
        super()._load_extra_sprites(zone, fw, fh)
        for key, fname in [
            ("walk", "sprite_walker_raton_walk.png"),
            ("hurt", "sprite_walker_raton_hurt.png"),
            ("die", "sprite_walker_raton_die.png"),
        ]:
            path = _SPRITE_DIR / fname
            try:
                self._sprite_frames[key] = AssetLoader.load_sprite_sheet(path, fw, fh)
            except (pygame.error, FileNotFoundError, PermissionError):
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
        golpe — `_patrol_origin` guarda el punto de spawn *antes del
        ajuste* (EnemyWalker.__init__ lo captura antes de restar
        rect.height para obtener la posición con los pies en el piso), así
        que la posición.y de reposo correcta es
        `_patrol_origin.y - rect.height`.
        """
        resting_y = self._patrol_origin.y - self.rect.height
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


class FlyingCucaracha(EnemyFlying):
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

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Sobreescribe el arte genérico del volador de zona1 con los
        sprites propios de la cucaracha.

        Llama a super() primero para que la clave genérica "fly" (el
        propio override de _load_extra_sprites de EnemyFlying) siga
        cargando como fallback, y después la sobreescribe junto con
        hurt/die con frames propios de la cucaracha — mismo llamado a
        AssetLoader.load_sprite_sheet, mismo patrón try/except usado en
        todo enemy_base.py/enemy_flying.py.
        """
        super()._load_extra_sprites(zone, fw, fh)
        for key, fname in [
            ("fly", "sprite_flying_cucaracha_fly.png"),
            ("hurt", "sprite_flying_cucaracha_hurt.png"),
            ("die", "sprite_flying_cucaracha_die.png"),
        ]:
            path = _SPRITE_DIR / fname
            try:
                self._sprite_frames[key] = AssetLoader.load_sprite_sheet(path, fw, fh)
            except (pygame.error, FileNotFoundError, PermissionError):
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
        self._event_bus.emit(Events.SFX_PROJECTILE_FIRE)

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
                    player._parry_success = True
                    player._parry_active = False
                    player._parry_window = 0.0
                    self._event_bus.emit(Events.VFX_PARRY, pos=(projectile.position.x, projectile.position.y))
                else:
                    player.apply_damage(projectile.damage, (self.position.x, self.position.y))
                    projectile.on_collision()

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        for projectile in self._active_projectiles:
            projectile.draw(surface, camera_offset)
