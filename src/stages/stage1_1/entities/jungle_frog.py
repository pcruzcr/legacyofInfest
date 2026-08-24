"""
Module: jungle_frog
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: II (Sistemas de coordenadas y matemática vectorial)
Description: Rana estacionaria apostada en el sendero, y el escupitajo que
dispara. Detecta al jugador por DISTANCIA EUCLIDIANA y le lanza un proyectil
cuya velocidad se obtiene NORMALIZANDO el vector hacia él.

Se agrupan las dos clases en un mismo archivo siguiendo la convención del
profesor: src/framework/entities/enemy_shooter.py contiene `Projectile` y
`EnemyShooter`, y enemy_caster.py contiene `HomingOrb` y `EnemyCaster` —
proyectil primero, enemigo que lo dispara después.

Se registra en el TMX con type="ShooterFrog", una de las 21 especies con
nombre de `bestiary_registry.SPECIES` («rana dardo»); el atributo name del
objeto lleva "JungleFrog_NN", que es lo que imprime el reporte del grader.
La escena sustituye esa especie por esta clase con
StageLoader.register_entity antes de que se cargue el mapa.

═══════════════════════════════════════════════════════════════════════
MATEMÁTICA VECTORIAL — UNIDAD II
═══════════════════════════════════════════════════════════════════════

1) VECTOR DIFERENCIA
   Del origen del disparo al objetivo:

       v = p_objetivo − p_origen = (x_obj − x_ori , y_obj − y_ori)

2) MAGNITUD (norma euclidiana)

       ‖v‖ = √( vx² + vy² )

3) NORMALIZACIÓN  →  vec2_normalize

       v̂ = v / ‖v‖        con  ‖v̂‖ = 1  por construcción

   Caso degenerado: si ‖v‖ < 1e-10 la función devuelve el vector cero en
   lugar de dividir entre cero.

4) VELOCIDAD A RAPIDEZ CONSTANTE

       velocidad = v̂ · RAPIDEZ    ⇒   ‖velocidad‖ = RAPIDEZ  ∀ dirección

   Esta es la razón de normalizar. Sin normalizar, ‖v‖ dependería de la
   distancia al objetivo: un jugador lejano produciría un proyectil
   rapidísimo y uno cercano, uno lentísimo.

5) INTEGRACIÓN DEL MOVIMIENTO (Euler explícito, velocidad constante)

       p(t + Δt) = p(t) + velocidad · Δt

6) ÁNGULO DE ORIENTACIÓN

       θ = atan2(vy , vx)          [rad], rango (−π, π]

7) ALCANCE MÁXIMO  →  vec2_length

       descartar cuando   ‖p(t) − p(0)‖ > ALCANCE_MAX

8) DISTANCIA EUCLIDIANA  →  vec2_distance
   Dispara la IA por proximidad:

       d(a, b) = ‖b − a‖ = √( (bₓ − aₓ)² + (b_y − a_y)² )

       d ≤ R_deteccion   ⇒   PATROL → ALERT → FIRING

   NOTA IMPORTANTE PARA EL README:
   `EnemyBase._check_detection_range()` del framework usa una caja alineada
   a los ejes (|dx| ≤ range_x  Y  |dy| ≤ range_y). Aquí se SOBREESCRIBE ese
   hook por una prueba radial verdadera, que es lo que pide la unidad. La
   diferencia es observable: con R = 96 y caja 96×64, un jugador en
   (90, 60) está DENTRO de la caja pero FUERA del círculo, porque
   √(90² + 60²) ≈ 108,2 > 96.

9) PRODUCTO PUNTO  →  vec2_dot
   Resuelve hacia dónde mira el sprite:

       a · b = aₓbₓ + a_yb_y = ‖a‖‖b‖cos θ

       s = v · x̂   con  x̂ = (1, 0)   ⇒   s = vₓ
       facing = +1 si s ≥ 0 ,  −1 si s < 0

10) TRANSFORMACIÓN LOCAL → MUNDO (traslación pura, en homogéneas)

       ⎡ x_mundo ⎤   ⎡ 1  0  tx ⎤ ⎡ x_local ⎤
       ⎢ y_mundo ⎥ = ⎢ 0  1  ty ⎥ ⎢ y_local ⎥ ,   (tx, ty) = self.position
       ⎣    1    ⎦   ⎣ 0  0   1 ⎦ ⎣    1    ⎦

    El hitbox se define en espacio local (offset respecto a la entidad) y
    se lleva a espacio de mundo sumándole la posición. Sin rotación ni
    escala: la submatriz 2×2 es la identidad.
═══════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import math

import pygame

from src.engine.utils.math_utils import (
    vec2_distance,
    vec2_dot,
    vec2_length,
    vec2_normalize,
)
from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.enemy_base import EnemyBase, EnemyState

# ── Hitbox del proyectil en ESPACIO LOCAL (offset desde su position) ─
HITBOX_LOCAL = pygame.Rect(0, 0, 6, 6)

# Boca de la rana en ESPACIO LOCAL (offset desde su position)
BOCA_LOCAL = pygame.Vector2(12.0, 10.0)

_COLOR_NUCLEO = (196, 232, 140)
_COLOR_BORDE = (96, 152, 64)
_COLOR_CUERPO = (52, 104, 46)
_COLOR_LOMO = (96, 152, 64)
_COLOR_OJO = (232, 224, 160)
_COLOR_CARGA = (232, 160, 80)


class FrogProjectile(BaseEntity):
    """Proyectil rectilíneo a rapidez constante.

    No hereda de EnemyBase: no tiene vida, ni máquina de estados, ni
    recibe daño. Solo posición, velocidad y tiempo de vida.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        target: pygame.Vector2,
        speed: float = 90.0,
        damage: float = 0.5,
        max_range: float = 200.0,
    ) -> None:
        # NO se pasa event_bus: ese parámetro existe en el árbol entregado
        # pero no en HEAD. Omitirlo funciona idéntico en ambas versiones.
        super().__init__(spawn_position)

        self._origin = pygame.Vector2(spawn_position)
        self.damage = damage
        self.max_range = max_range
        self.layer = 5

        # ── (1) Vector diferencia ────────
        # v = p_objetivo - p_origen. Este vector apunta desde el origen hacia el 
        # jugador. Su longitud sin normalizar representa exactamente la distancia 
        # euclidiana entre ambos puntos.
        diferencia = pygame.Vector2(target) - pygame.Vector2(spawn_position)

        # ── (3)(4) Normalización y velocidad ────────
        # Se normaliza `diferencia` para separar la DIRECCIÓN de la RAPIDEZ.
        # Si se usara `diferencia` directamente como velocidad, un objetivo más 
        # lejano produciría un proyectil mucho más rápido. Al normalizarlo, 
        # obtenemos un vector unitario (longitud 1) al cual podemos multiplicarle 
        # el escalar `speed`, garantizando una rapidez constante sin importar 
        # la distancia al objetivo.
        direccion = vec2_normalize(diferencia)
        self.velocity: pygame.Vector2 = direccion * speed

        # ── (6) Ángulo para orientar el sprite ────────
        # Se usa `math.atan2(y, x)` en lugar de `math.atan(y / x)`. `atan2` 
        # toma ambos componentes por separado, lo que le permite distinguir 
        # correctamente los cuatro cuadrantes y evita el error de división 
        # por cero cuando x es 0 (tiro vertical).
        self.angle: float = math.atan2(diferencia.y, diferencia.x)

        self.rect = pygame.Rect(
            int(self.position.x) + HITBOX_LOCAL.x,
            int(self.position.y) + HITBOX_LOCAL.y,
            HITBOX_LOCAL.width,
            HITBOX_LOCAL.height,
        )

    def update(self, dt: float) -> None:
        if not self.is_active:
            return

        # ── (5) Integración explícita de Euler ────────
        # p(t + dt) = p(t) + v * dt
        # Se multiplica la velocidad por `dt` (tiempo transcurrido, delta time) 
        # para que el desplazamiento del proyectil sea constante respecto al tiempo 
        # real y no dependa de la tasa de fotogramas (FPS) del motor gráfico.
        self.position += self.velocity * dt

        # ── (10) Hitbox local → Mundo por traslación homogénea ────────
        # La posición local del hitbox se lleva a espacio de mundo mediante 
        # una traslación. En álgebra matricial, las traslaciones NO son 
        # transformaciones lineales y por tanto no pueden representarse con 
        # matrices 2x2. Al usar coordenadas homogéneas (agregando un tercer 
        # componente 1), la traslación se convierte en una operación lineal 
        # que permite sumar la posición del objeto (tx, ty) a la coordenada local.
        self.rect.x = int(self.position.x) + HITBOX_LOCAL.x
        self.rect.y = int(self.position.y) + HITBOX_LOCAL.y

        # (7) descarte por alcance máximo
        if vec2_length(self.position - self._origin) > self.max_range:
            self.is_active = False

    def draw(self, surface: pygame.Surface,
             camera_offset: pygame.Vector2) -> None:
        if not (self.is_active and self.is_visible):
            return
        centro = (
            int(self.position.x - camera_offset.x) + HITBOX_LOCAL.width // 2,
            int(self.position.y - camera_offset.y) + HITBOX_LOCAL.height // 2,
        )
        pygame.draw.circle(surface, _COLOR_BORDE, centro, 3)
        pygame.draw.circle(surface, _COLOR_NUCLEO, centro, 2)


class JungleFrog(EnemyBase):
    """Rana estacionaria que escupe al jugador cuando entra en su radio."""

    ALTO = 20

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        fire_rate: float = 1.6,
        projectile_speed: float = 90.0,
        projectile_damage: float = 0.5,
        detection_range_x: float = 96.0,
        detection_range_y: float = 64.0,
        max_health: float = 2.0,
        damage_on_contact: float = 0.5,
        **_ignorados,
    ) -> None:
        # NO se pasa event_bus: existe en el árbol entregado pero no en HEAD.
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=detection_range_x,
            detection_range_y=detection_range_y,
        )

        # ── Ajuste de posición vertical (Y) ────────
        # CONVENCIÓN DEL PROFESOR: la `y` del objeto en el TMX marca los PIES
        # de la entidad, no su esquina superior. EnemyWalker hace exactamente
        # esto en enemy_walker.py:56. Sin este ajuste (restar la altura a la 
        # coordenada Y), la rana aparecería enterrada su propia altura dentro 
        # del terreno sólido.
        self.position.y -= self.ALTO
        self.rect = pygame.Rect(
            int(self.position.x), int(self.position.y), 24, self.ALTO,
        )

        # El radio de detección radial reutiliza el valor horizontal del TMX,
        # que el StageLoader ya castea a float (stage_loader.py:550-553).
        self.detection_radius: float = float(detection_range_x)

        self.fire_rate: float = float(fire_rate)
        self.projectile_speed: float = float(projectile_speed)
        self.projectile_damage: float = float(projectile_damage)

        self.projectiles: list[FrogProjectile] = []
        self._fire_cooldown: float = 0.0

    # ── Unidad II · (8) detección radial ────────────────────────────

    def _center(self) -> pygame.Vector2:
        return pygame.Vector2(self.rect.center)

    def _player_center(self) -> pygame.Vector2 | None:
        if self._player_ref is None:
            return None
        return pygame.Vector2(self._player_ref.center)

    def distance_to_player(self) -> float:
        """d(rana, jugador) por la norma euclidiana. Infinito si no hay jugador."""
        objetivo = self._player_center()
        if objetivo is None:
            return float("inf")
        return vec2_distance(self._center(), objetivo)

    def _check_detection_range(self) -> bool:
        # ── Unidad II · (8) Detección radial ────────
        # Sobreescribe la lógica de detección en forma de caja del framework 
        # por una prueba radial (euclidiana) verdadera. La caja heredada 
        # evalúa |dx| <= range_x y |dy| <= range_y. Con R=96 y una caja de 
        # 96x64, un jugador en (90, 60) estaría dentro de la caja pero fuera 
        # del círculo porque la distancia real es √(90² + 60²) ≈ 108.2, lo 
        # que es mayor a 96.
        return self.distance_to_player() <= self.detection_radius

    # ── Unidad II · (9) orientación por producto punto ──────────────

    def aim_vector(self) -> pygame.Vector2:
        """Vector SIN normalizar de la boca al centro del jugador."""
        objetivo = self._player_center()
        if objetivo is None:
            return pygame.Vector2(0.0, 0.0)
        return objetivo - (self.position + BOCA_LOCAL)

    def aim_at_player(self) -> None:
        # ── Unidad II · (9) Orientación por producto punto ────────
        # Fija facing_direction evaluando el producto punto (dot product) 
        # del vector hacia el jugador contra el vector unitario del eje X x̂=(1,0). 
        # El signo del producto punto equivale matemáticamente al signo del coseno 
        # del ángulo entre los dos vectores. Por lo tanto, si s >= 0, el jugador 
        # está a la derecha (facing_direction = 1); si s < 0, a la izquierda 
        # (facing_direction = -1), sin requerir trigonometría ni divisiones.
        s = vec2_dot(self.aim_vector(), pygame.Vector2(1.0, 0.0))
        self.facing_direction = 1 if s >= 0.0 else -1

    # ── Unidad II · (3)(4) disparo con vector normalizado ───────────

    def fire(self) -> None:
        """Escupe un proyectil hacia el jugador a rapidez constante."""
        objetivo = self._player_center()
        if objetivo is None:
            return
        self.aim_at_player()
        self.projectiles.append(
            FrogProjectile(
                spawn_position=self.position + BOCA_LOCAL,
                target=objetivo,
                speed=self.projectile_speed,
                damage=self.projectile_damage,
            )
        )
        self._fire_cooldown = self.fire_rate

    def update_projectiles(self, dt: float) -> None:
        """Avanza los proyectiles vivos y descarta los agotados."""
        for p in self.projectiles:
            p.update(dt)
        self.projectiles = [p for p in self.projectiles if p.is_active]

    # ── Hooks del framework ─────────────────────────────────────────

    def _check_player_contact(self, player) -> None:
        """Contacto del cuerpo (lo hereda) más el impacto del escupitajo.

        EL PARRY DEL MOTOR
        ------------------
        El jugador puede parear pulsando ATAQUE CORTO + AGACHARSE a la vez
        (`_handle_parry_input`, entities/states/ability.py:67-77). Eso abre una ventana
        de 0,2 s (`_PARRY_DURATION`) durante la cual `_parry_active` está en
        True. Si un golpe llega dentro de esa ventana, se anula sin daño.

        Se replica el contrato de `EnemyShooter._check_player_contact`
        (enemy_shooter.py:193-207): mismo orden, mismas banderas, mismo
        evento de VFX. Así el escupitajo se comporta como cualquier otro
        proyectil del juego y el parry funciona igual contra él.
        """
        super()._check_player_contact(player)

        hurtbox = getattr(player, "hurtbox", None) or player.rect
        for p in list(self.projectiles):
            if not (p.is_active and p.rect.colliderect(hurtbox)):
                continue
            if (getattr(player, "_parry_active", False)
                    and getattr(player, "_parry_window", 0) > 0):
                p.is_active = False
                player._parry_success = True
                player._parry_active = False
                player._parry_window = 0.0
                self._emitir_vfx_parry(p)
            else:
                player.apply_damage(p.damage, (self.position.x, self.position.y))
                p.is_active = False

    def _emitir_vfx_parry(self, proyectil: FrogProjectile) -> None:
        """Emite el VFX de parry si hay bus de eventos disponible.

        Se consulta con getattr porque `_event_bus` solo existe en la
        versión de `BaseEntity` que vino en el .zip, no en la de HEAD
        (ver claude-workspace/00-REGLAS-Y-HALLAZGOS.md §2.1).
        """
        bus = getattr(self, "_event_bus", None)
        if bus is None:
            return
        from src.engine.core.events import Events
        bus.emit(Events.VFX_PARRY,
                 pos=(proyectil.position.x, proyectil.position.y))

    def _patrol_behavior(self, dt: float) -> None:
        """Estacionaria: solo enfría el disparo."""
        self._fire_cooldown = max(0.0, self._fire_cooldown - dt)

    def _alert_behavior(self, dt: float) -> None:
        """Encara al jugador y dispara respetando la cadencia."""
        self.aim_at_player()
        self._fire_cooldown = max(0.0, self._fire_cooldown - dt)
        if self._fire_cooldown <= 0.0:
            self.fire()

    def _post_update(self, dt: float) -> None:
        self.update_projectiles(dt)

    def _get_animation_key(self) -> str:
        return "alert" if self.state == EnemyState.ALERT else "idle"

    def _build_hitbox(self) -> pygame.Rect:
        """Espacio LOCAL — el motor lo traslada con (tx, ty) = position."""
        return pygame.Rect(4, 4, 16, 14)

    def _build_hurtbox(self) -> pygame.Rect:
        """Espacio LOCAL. Cubre el cuerpo ENTERO más un margen de 2 px.

        El ataque cuerpo a cuerpo del motor tiene un alcance minúsculo:
        `_build_attack_hitbox` (entities/states/helpers.py:177-210) construye un
        rect de 36 px de ancho centrado en el jugador con un desplazamiento
        de 8 px hacia el frente, así que solo llega **16 px** más allá de su
        cuerpo (26 px con el ataque largo). Hay que estar prácticamente
        pegado al enemigo para conectar.

        `entities/states/` es del profesor y no se toca. Lo que sí está en
        mi mano es que esta entidad sea lo más golpeable posible: hurtbox
        sin margen muerto, desbordando 2 px el cuerpo.
        """
        return pygame.Rect(-2, -2, self.rect.width + 4, self.ALTO + 4)

    # ── Dibujo ──────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface,
             camera_offset: pygame.Vector2) -> None:
        if not self.is_visible:
            return
        x = int(self.position.x - camera_offset.x)
        y = int(self.position.y - camera_offset.y)

        pygame.draw.ellipse(surface, _COLOR_CUERPO, (x + 2, y + 6, 20, 14))
        pygame.draw.ellipse(surface, _COLOR_LOMO, (x + 5, y + 4, 14, 8))

        ojo_x = x + (16 if self.facing_direction > 0 else 5)
        pygame.draw.rect(surface, _COLOR_OJO, (ojo_x, y + 4, 3, 3))

        if self.state == EnemyState.ALERT and self._fire_cooldown < 0.45:
            pygame.draw.circle(
                surface, _COLOR_CARGA,
                (x + int(BOCA_LOCAL.x), y + int(BOCA_LOCAL.y)), 2,
            )

        for p in self.projectiles:
            p.draw(surface, camera_offset)
