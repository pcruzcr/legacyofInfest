"""
Module: canopy_bird
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: III (Curvas paramétricas básicas)
Description: Ave que planea por el dosel siguiendo una curva de Bézier
cúbica cuyos puntos de control se definen EN TILED, no en código.

Se registra en el TMX con type="FlyingBird", una de las 21 especies con
nombre de `bestiary_registry.SPECIES` («ave de selva»); el atributo name
del objeto lleva "CanopyBird_NN". La escena sustituye esa especie por esta
clase con StageLoader.register_entity antes de que se cargue el mapa.

═══════════════════════════════════════════════════════════════════════
CURVAS DE BÉZIER — UNIDAD III
═══════════════════════════════════════════════════════════════════════

1) FORMA GENERAL (base de Bernstein), grado n = nº de puntos − 1

       B(t) = Σ_{i=0}^{n}  C(n,i) · (1 − t)^(n−i) · tⁱ · Pᵢ ,   t ∈ [0, 1]

       con el coeficiente binomial   C(n,i) = n! / ( i! · (n−i)! )

2) GRADO 3 — el usado aquí, con cuatro puntos de control P₀ P₁ P₂ P₃

       B(t) = (1−t)³·P₀ + 3(1−t)²t·P₁ + 3(1−t)t²·P₂ + t³·P₃

   Implementación del profesor: curve_tools.py:143-150 (`_eval_bernstein`,
   que evalúa los binomios con math.comb).

3) PROPIEDADES QUE IMPORTAN AL DISEÑO DEL NIVEL

   · Interpolación de extremos:  B(0) = P₀  y  B(1) = P₃
   · P₁ y P₂ NO se tocan: solo "tiran" de la curva
   · Envolvente convexa: toda la curva vive dentro del casco convexo de
     {P₀..P₃}. Gracias a esto, el vuelo del ave nunca se sale del área
     que se dibujó en Tiled — el recorrido es predecible para el diseño.

4) QUÉ ES `t`

   Progreso NORMALIZADO a lo largo del recorrido; **no** es tiempo ni
   longitud de arco. t = 0 es P₀ y t = 1 es P₃.

   La Bézier no está parametrizada por longitud de arco, así que la
   rapidez lineal del ave varía: es mayor donde los puntos de control
   están más separados. Es un efecto conocido y aquí se ACENTÚA a
   propósito con easing (punto 5).

5) EASING SOBRE t  →  ease_in_out_quad

       u = 2t²                    si t < 0,5
       u = −1 + (4 − 2t)·t        si t ≥ 0,5

   Se aplica sobre t, no sobre el tiempo. Frena en lo alto del arco y
   acelera al caer: el "swoop" que pide docs/16_WORLD_DESIGN.md §3.2.
   En los extremos u(0) = 0 y u(1) = 1, así que no rompe la interpolación.

6) MUESTREO  →  CurveTools.sample_path

   La curva se evalúa UNA vez en __init__ produciendo `n_samples` puntos.
   Por frame solo se interpola LINEALMENTE entre muestras vecinas:

       i = ⌊u·(N−1)⌋ ,  f = u·(N−1) − i
       p = p_i + (p_{i+1} − p_i)·f

   La curvatura viene del muestreo Bézier previo, no de sample_path.

7) PUNTOS DE CONTROL DESDE TILED

   stage_loader.py:445-452 (`_build_waypoints`) recolecta los objetos
   type="Waypoint" agrupados por su propiedad owner_id, y la linea 552 los
   inyecta al constructor como kwarg `waypoints`. Un objeto Bat llamado "CanopyBird_01" más cuatro Waypoint
   con owner_id="CanopyBird_01" ⇒ el ave recibe sus 4 puntos de control
   desde el editor, sin tocar código.
═══════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import pygame

from src.engine.utils.math_utils import clamp, ease_in_out_quad
from src.framework.entities.enemy_base import EnemyBase, EnemyState
from src.framework.processing.curve_tools import CurveTools

_COLOR_CUERPO = (36, 80, 38)
_COLOR_ALA = (68, 120, 52)
_COLOR_PICO = (232, 160, 80)
_COLOR_OJO = (232, 224, 160)


class CanopyBird(EnemyBase):
    """Ave que recorre en ping-pong una Bézier cúbica definida en Tiled."""

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        waypoints: list[tuple[float, float]] | None = None,
        flight_speed: float = 0.22,
        n_samples: int = 64,
        max_health: float = 1.0,
        damage_on_contact: float = 0.5,
        **_ignorados,
    ) -> None:
        # NO se pasa event_bus: existe en el árbol entregado pero no en HEAD.
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
        )

        self.control_points: list[tuple[float, float]] = self._resolve_control_points(
            spawn_position, waypoints,
        )

        # ── (1)(2)(3)(6) Evaluación de la curva de Bézier (Bases de Bernstein) ────────
        # La curva paramétrica B(t) de grado 3 se compone sumando los cuatro puntos 
        # de control multiplicados por sus polinomios base de Bernstein: 
        # B(t) = (1-t)³P₀ + 3(1-t)²t P₁ + 3(1-t)t² P₂ + t³P₃.
        # Las bases de Bernstein son siempre no negativas y suman 1 para cualquier t,
        # lo que significa que la curva siempre es una combinación convexa de los puntos.
        # Esta PROPIEDAD DE LA ENVOLVENTE CONVEXA garantiza matemáticamente que el ave
        # nunca se saldrá del polígono o "casco" formado por los 4 puntos de control,
        # asegurando que el diseño de nivel se respete (el ave no se meterá en la roca).
        # 
        # Se evalúa la curva UNA SOLA VEZ aquí en el constructor para obtener 64 muestras.
        # Como la trayectoria es estática (los puntos de control no se mueven), 
        # recalcular los polinomios de Bernstein y obtener las 64 muestras 60 veces por 
        # segundo (cada fotograma) en el método update sería un desperdicio enorme de CPU.
        self.n_samples: int = int(n_samples)
        self.path: list[tuple[float, float]] = CurveTools.bezier(
            self.control_points, self.n_samples,
        )

        # ── (4) Parámetro 't' ────────
        # 't' es un escalar normalizado [0, 1] que indica el PROGRESO en la curva. 
        # NO es el tiempo transcurrido ni la longitud de arco. Al no estar parametrizada
        # por longitud de arco, avanzar pasos constantes en 't' produce una rapidez 
        # lineal variable en el espacio (más rápido donde los puntos están más alejados).
        self.t: float = 0.0
        self.direction: int = 1          # +1 hacia P₃, −1 de vuelta a P₀
        self.flight_speed: float = float(flight_speed)

        self.rect = pygame.Rect(int(spawn_position.x), int(spawn_position.y), 16, 12)
        self._sync_position()

    # ── (7) puntos de control ───────────────────────────────────────

    @staticmethod
    def _resolve_control_points(
        spawn: pygame.Vector2,
        waypoints: list[tuple[float, float]] | None,
    ) -> list[tuple[float, float]]:
        """Usa los Waypoint del TMX; si faltan, genera un arco por defecto.

        Sin este resguardo un ave sin waypoints quedaría estática e
        invisible para el jugador, que es el peor fallo posible: silencioso.
        """
        if waypoints and len(waypoints) >= 2:
            return [(float(x), float(y)) for x, y in waypoints]
        sx, sy = float(spawn.x), float(spawn.y)
        return [(sx, sy), (sx + 48, sy - 32), (sx + 96, sy + 24), (sx + 144, sy)]

    # ── (5) easing sobre el parámetro ───────────────────────────────

    def eased_t(self) -> float:
        # ── (5) Easing sobre el parámetro 't' ────────
        # Aplica una función cuadrática de aceleración y desaceleración sobre `t` 
        # para darle al ave un movimiento orgánico (el swooping, que acelera al caer). 
        # Es clave que esta función preserve los extremos absolutos: u(0) = 0 y u(1) = 1. 
        # Si u(0) o u(1) dieran valores distintos, la curva interpolada ya no 
        # conectaría exactamente con el punto de inicio (P₀) o de fin (P₃), rompiendo 
        # el planeo.
        return ease_in_out_quad(self.t)

    # ── Recorrido ───────────────────────────────────────────────────

    def advance_along_path(self, dt: float) -> None:
        # ── Avance en Ping-Pong ────────
        # Avanza el progreso `t`. Si llega a los extremos (0.0 o 1.0), invierte su 
        # dirección (de 1 a -1 o viceversa) para que el ave vaya y vuelva en bucle 
        # por la curva, rebotando infinitamente entre P₀ y P₃.
        self.t += self.direction * self.flight_speed * dt

        if self.t >= 1.0:
            self.t = 1.0
            self.direction = -1
        elif self.t <= 0.0:
            self.t = 0.0
            self.direction = 1

        # ── Clamp de seguridad ────────
        # Aunque el bloque if-elif anterior repara los desbordamientos que lo 
        # disparan, problemas de precisión de punto flotante al sumar dt 
        # o manipulaciones en otros métodos (como en alert_behavior) podrían dejar 
        # `t` microscópicamente fuera de [0, 1]. El clamp garantiza un valor legal 
        # antes de muestrear la curva, evitando excepciones de índice en sample_path.
        self.t = clamp(self.t, 0.0, 1.0)
        self._sync_position()

    def _sync_position(self) -> None:
        # ── (6) Muestreo e Interpolación Lineal ────────
        # En lugar de recalcular la cúbica de Bézier cada fotograma, extrae un par de 
        # puntos de la polilínea cacheada (self.path) según el valor de `t` deformado, 
        # y realiza una simple interpolación lineal entre esas dos muestras contiguas.
        x, y = CurveTools.sample_path(self.path, self.eased_t())
        self.position.update(x, y)
        self.rect.x = int(x)
        self.rect.y = int(y)
        self.facing_direction = 1 if self.direction > 0 else -1

    # ── Hooks del framework ─────────────────────────────────────────

    def _patrol_behavior(self, dt: float) -> None:
        self.advance_along_path(dt)

    def _alert_behavior(self, dt: float) -> None:
        """Al detectar al jugador acelera el planeo, pero NO abandona la
        curva: el recorrido sigue siendo el definido en Tiled."""
        self.t += self.direction * self.flight_speed * 1.6 * dt
        if self.t >= 1.0:
            self.t, self.direction = 1.0, -1
        elif self.t <= 0.0:
            self.t, self.direction = 0.0, 1
        self.t = clamp(self.t, 0.0, 1.0)
        self._sync_position()

    def _get_animation_key(self) -> str:
        return "alert" if self.state == EnemyState.ALERT else "drift"

    def _build_hitbox(self) -> pygame.Rect:
        """Espacio LOCAL — el motor lo traslada con (tx, ty) = position."""
        return pygame.Rect(2, 2, 12, 8)

    def _build_hurtbox(self) -> pygame.Rect:
        """Espacio LOCAL. Cubre el cuerpo ENTERO más un margen de 2 px.

        El ataque del motor solo llega 16 px más allá del cuerpo del jugador
        (26 px el largo) — ver `_build_attack_hitbox` en
        entities/states/helpers.py:177-210. Contra un ave que además se mueve por
        una curva, un hurtbox con margen muerto la haría casi imposible de
        tocar. Se le da el cuerpo entero con 2 px de holgura.
        """
        return pygame.Rect(-2, -2, self.rect.width + 4, self.rect.height + 4)

    # ── Dibujo ──────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface,
             camera_offset: pygame.Vector2) -> None:
        if not self.is_visible:
            return
        x = int(self.position.x - camera_offset.x)
        y = int(self.position.y - camera_offset.y)
        mira = self.facing_direction

        pygame.draw.ellipse(surface, _COLOR_CUERPO, (x + 3, y + 3, 11, 7))

        # las alas baten según el tramo del recorrido
        arriba = (int(self.t * 12) % 2) == 0
        dy = -3 if arriba else 2
        pygame.draw.line(surface, _COLOR_ALA, (x + 5, y + 5), (x + 1, y + 5 + dy), 2)
        pygame.draw.line(surface, _COLOR_ALA, (x + 10, y + 5), (x + 14, y + 5 + dy), 2)

        px = x + (14 if mira > 0 else 1)
        pygame.draw.rect(surface, _COLOR_PICO, (px, y + 5, 2, 2))
        pygame.draw.rect(surface, _COLOR_OJO, (x + (11 if mira > 0 else 4), y + 4, 1, 1))
