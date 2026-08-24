"""
Module: estudiante_infectado
System: stage1_3_las_aulas (entidad propia del estudiante)
Academic Unit: Unidad II — Sistemas de coordenadas y transformaciones vectoriales

Autor: Yariel — nivel "Las Aulas"

Enemigo que patrulla el aula y persigue al jugador usando ARITMETICA VECTORIAL
EXPLICITA con las funciones de `src/engine/utils/math_utils.py`.

Las tres formulas que implementa (documentadas en el README):

  1) DISTANCIA EUCLIDIANA — vec2_distance(a, b)
         d = ||b - a|| = sqrt((bx - ax)^2 + (by - ay)^2)
     Reemplaza la deteccion por caja del motor (|dx| <= rx and |dy| <= ry),
     que mide un rectangulo.  Con la norma euclidiana el area de deteccion
     es un CIRCULO de radio `radio_vision`, geometricamente correcto: el
     enemigo reacciona igual a 100 px de distancia venga de donde venga.

  2) NORMALIZACION — vec2_normalize(v)
         v_gorro = v / ||v||        (vector unitario, ||v_gorro|| = 1)
     Da la DIRECCION hacia el jugador sin su magnitud.  Al multiplicarla por
     la rapidez se obtiene una velocidad de modulo constante:
         posicion += v_gorro * rapidez * dt
     Sin normalizar, el enemigo se moveria mas rapido cuanto mas lejos
     estuviera el jugador, que es el error clasico de esta mecanica.

  3) PRODUCTO PUNTO — vec2_dot(a, b)
         a . b = ax*bx + ay*by = ||a|| ||b|| cos(theta)
     Con dos vectores unitarios el producto punto ES el coseno del angulo
     entre ellos.  Se usa para el CONO DE VISION: el enemigo solo ve al
     jugador si
         d_gorro . f_gorro >= cos(mitad_del_angulo_de_vision)
     donde f_gorro es la direccion a la que mira.  Comparar cosenos evita
     calcular arcocosenos, que son caros y se evaluan 60 veces por segundo.
"""
from __future__ import annotations

import math

import pygame

from src.engine.utils.math_utils import vec2_distance, vec2_dot, vec2_normalize
from src.framework.entities.enemy_base import EnemyBase
from src.framework.stage.stage_loader import StageLoader


def _a_float(valor, por_defecto: float) -> float:
    """El TMX entrega las propiedades como texto salvo una lista fija de
    nombres conocidos por StageLoader.  Los nombres propios llegan como str,
    asi que se convierten aqui."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return por_defecto


class EstudianteInfectado(EnemyBase):
    """Estudiante infectado que patrulla entre los pupitres del aula.

    Patrulla un tramo horizontal.  Cuando el jugador entra en su CIRCULO de
    vision y ademas cae dentro de su CONO de vision, pasa a perseguirlo en
    linea recta usando el vector unitario hacia el.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        patrol_length: float = 96.0,
        patrol_speed: float = 40.0,
        alert_speed: float = 85.0,
        max_health: float = 2.0,
        damage_on_contact: float = 0.5,
        facing: str = "right",
        zone: int = 1,
        radio_vision=140.0,
        angulo_vision=120.0,
        radio_periferico=40.0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            # El motor exige estos rangos, pero la deteccion real la resuelve
            # _player_in_range() mas abajo con matematica vectorial.
            detection_range_x=radio_vision,
            detection_range_y=radio_vision,
        )

        self.patrol_length: float = patrol_length
        self.patrol_speed: float = patrol_speed
        self.alert_speed: float = alert_speed
        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self._collision_rects: list[pygame.Rect] = []
        self._one_way_rects: list[pygame.Rect] = []

        # --- Parametros del modelo de vision ---
        self.radio_vision: float = _a_float(radio_vision, 140.0)
        self.radio_periferico: float = _a_float(radio_periferico, 40.0)
        angulo = _a_float(angulo_vision, 120.0)
        # Se guarda el coseno de la MITAD del angulo: es con lo que se compara
        # el producto punto, y asi el coseno se calcula una sola vez.
        self._cos_media_apertura: float = math.cos(math.radians(angulo) / 2.0)

        self.facing_direction = 1 if facing == "right" else -1

        self.rect.width = 24
        self.rect.height = 28
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        self._load_zone_sprites(int(zone) if zone else 1, 16, 12)

    # ── Geometria vectorial ────────────────────────────────────────────

    @property
    def _centro(self) -> pygame.Vector2:
        """Centro del enemigo en coordenadas de mundo."""
        return pygame.Vector2(self.rect.centerx, self.rect.centery)

    @property
    def _mirada(self) -> pygame.Vector2:
        """Vector unitario hacia donde mira el enemigo (ya es unitario)."""
        return pygame.Vector2(float(self.facing_direction), 0.0)

    def _vector_al_jugador(self) -> pygame.Vector2 | None:
        """Vector que va del centro del enemigo al centro del jugador."""
        if self._player_ref is None:
            return None
        objetivo = pygame.Vector2(self._player_ref.centerx, self._player_ref.centery)
        return objetivo - self._centro

    def _player_in_range(
        self, player_rect: pygame.Rect | None = None, margin: float = 0.0
    ) -> bool:
        """Deteccion vectorial: circulo de vision + cono de vision.

            1. d = vec2_distance(centro_enemigo, centro_jugador)
               Si d > radio_vision + margen  ->  fuera de alcance.

            2. d_gorro = vec2_normalize(jugador - enemigo)
               cos(theta) = vec2_dot(d_gorro, f_gorro)
               Si cos(theta) < cos(apertura/2)  ->  esta fuera del cono.

        Extra: dentro de `radio_periferico` detecta sin importar el angulo
        (percepcion periferica), para que no sea posible pegarse a su espalda.
        """
        referencia = player_rect if player_rect is not None else self._player_ref
        if referencia is None:
            return False

        centro = self._centro
        objetivo = pygame.Vector2(referencia.centerx, referencia.centery)

        # (1) Circulo de vision — distancia euclidiana
        distancia = vec2_distance(centro, objetivo)
        if distancia > self.radio_vision + margin:
            return False

        # Percepcion periferica: demasiado cerca para no notarlo
        if distancia <= self.radio_periferico + margin:
            return True

        # (2) Cono de vision — producto punto de dos vectores unitarios
        hacia_jugador = objetivo - centro
        if hacia_jugador.length_squared() == 0.0:
            return True
        direccion = vec2_normalize(hacia_jugador)
        coseno = vec2_dot(direccion, self._mirada)
        return coseno >= self._cos_media_apertura

    # ── Comportamientos ────────────────────────────────────────────────

    def set_collision_rects(
        self, rects: list[pygame.Rect], one_way: list[pygame.Rect] | None = None
    ) -> None:
        self._collision_rects = rects
        self._one_way_rects = one_way or []

    @property
    def _suelo(self) -> list[pygame.Rect]:
        return self._collision_rects + self._one_way_rects

    def _hay_piso_adelante(self) -> bool:
        """Sondea un punto adelante y abajo para no caminar al vacio."""
        suelo = self._suelo
        if not suelo:
            return True
        sonda_x = self.position.x + self.facing_direction * (self.rect.width // 2 + 2)
        sonda_y = self.position.y + self.rect.height + 2
        return any(r.collidepoint(sonda_x, sonda_y) for r in suelo)

    def _patrol_behavior(self, dt: float) -> None:
        """Camina de ida y vuelta sobre su tramo, sin caerse por los bordes."""
        if not self._hay_piso_adelante():
            self.facing_direction *= -1
        elif abs(self.position.x - self._patrol_origin.x) >= self.patrol_length / 2:
            self.facing_direction *= -1

        self.position.x += self.facing_direction * self.patrol_speed * dt

    def _alert_behavior(self, dt: float) -> None:
        """Persecucion con vector unitario.

            d_gorro = vec2_normalize(jugador - enemigo)
            posicion += d_gorro * alert_speed * dt

        Al ser d_gorro unitario, el modulo del desplazamiento por frame es
        exactamente alert_speed * dt sin importar lo lejos que este el
        jugador: la rapidez es constante, solo cambia la direccion.
        """
        hacia_jugador = self._vector_al_jugador()
        if hacia_jugador is None or hacia_jugador.length_squared() == 0.0:
            return

        direccion = vec2_normalize(hacia_jugador)

        # Mirar hacia donde apunta la componente horizontal del vector
        if direccion.x != 0.0:
            self.facing_direction = 1 if direccion.x > 0 else -1

        # Solo avanza si hay piso: persigue, pero no se suicida
        if self._hay_piso_adelante():
            self.position.x += direccion.x * self.alert_speed * dt

    def _post_update(self, dt: float) -> None:
        """Apoya al enemigo sobre la superficie que tenga debajo."""
        for rect in self._suelo:
            pies = self.position.y + self.rect.height
            if rect.top <= pies < rect.bottom and rect.left < self.rect.centerx < rect.right:
                self.position.y = rect.top - self.rect.height
                break

    # ── Presentacion ───────────────────────────────────────────────────

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 24, 28)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()


# Registro en el motor: permite colocar objetos type="EstudianteInfectado"
# en la capa Objects del TMX.  Se ejecuta al importar el modulo, antes de
# que StageScene.on_enter() llame a StageLoader.load().
StageLoader.register_entity("EstudianteInfectado", EstudianteInfectado)
