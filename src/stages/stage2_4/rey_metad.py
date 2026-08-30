"""
ReyMetad — cada una de las dos mitades de El Rey Terciopelo.

Spec §4.3, Fase 2 «La División»: el cuerpo se parte en dos sub-jefes de 3
corazones cada uno que **coordinan: uno ataca mientras el otro se reposiciona**.
Cuando las dos caen, empieza la Fase 3.

Por qué es una clase y no un enemigo más
----------------------------------------
Podría haberse resuelto invocando dos `EnemyWalker` con más vida, que es lo que
sugiere el spec al decir «se comporta como un EnemyWalker agrandado». Pero la
coordinación es el corazón de la fase —`66_GUIA §4.2`: «la fase 2 enseña la
gestión de dos frentes»— y eso ningún enemigo genérico lo hace: hace falta que
las dos mitades se hablen. Hereda de `BossBase` porque es lo que es, un
sub-jefe, y así trae gratis el telegrafiado, las cajas de golpe y la barra.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.math_utils import lerp, vec2_distance, vec2_normalize
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.boss_kit import (
    AttackScheduler,
    AttackTiming,
    BossAttack,
)

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class CoordinadorDeMitades:
    """El turno compartido por las dos mitades.

    Vive fuera de las mitades a propósito: si cada una llevara su propio
    temporizador, ambas podrían acabar atacando a la vez —justo lo que el spec
    prohíbe— en cuanto se desincronizaran por un aturdimiento. Con un único
    reloj el turno es indivisible por construcción.
    """

    #: Cuánto dura el turno de cada mitad antes de cederlo.
    TURNO = 3.0

    def __init__(self) -> None:
        #: Lado que tiene permiso de atacar: -1 izquierda, +1 derecha.
        self.turno: int = random.choice((-1, 1))
        self._restante: float = self.TURNO

    def update(self, dt: float) -> None:
        self._restante -= dt
        if self._restante <= 0.0:
            self.turno = -self.turno
            self._restante = self.TURNO

    def le_toca(self, lado: int) -> bool:
        return self.turno == lado


class ReyMetad(BossBase):
    """Media marioneta: la mitad izquierda o la derecha del Rey."""

    #: Spec §4.3: «3 corazones cada uno», contacto 0.5.
    VIDA = 3.0
    DANO_CONTACTO = 0.5

    # ── Fase 2: «La Furia» ─────────────────────────────────────────────
    #
    # No está en el spec, y la razón para añadirla es mecánica, no decorativa.
    # Toda la fase se sostiene en que las mitades SE TURNAN: una ataca
    # mientras la otra rodea. Ese diseño tiene un agujero — en cuanto cae una,
    # la superviviente sigue respetando un turno que ya no compite con nadie
    # y se queda pasiva la mitad del tiempo, justo cuando la pelea debería
    # apretar. El resultado jugado es un anticlímax: matás una y la otra se
    # vuelve más fácil.
    #
    # La furia lo cierra por dos vías: por heridas (mitad de vida) y por
    # soledad (su compañera cayó). Cualquiera de las dos la dispara.
    #: Vida a la que se enfurece por heridas.
    UMBRAL_FURIA = 1.5
    #: Cuánto acelera y cuánto acorta su enfriamiento al enfurecerse.
    FURIA_VELOCIDAD = 1.45
    FURIA_CADENCIA = 0.6

    #: Reutiliza los números del escupitajo del Rey: es el mismo veneno.
    SPIT_RANGE = 200.0
    SPIT_SPEED = 90.0
    SPIT_DAMAGE = 0.5
    SPIT_COOLDOWN = 2.6

    #: Velocidad al acercarse y al reposicionarse. Reposicionar es más rápido:
    #: la mitad que no ataca busca ángulo, no pasea.
    VELOCIDAD_ATAQUE = 70.0
    VELOCIDAD_REPOSICION = 105.0
    #: Distancia a la que la mitad atacante quiere quedarse del jugador.
    DISTANCIA_PREFERIDA = 150.0
    #: Margen contra las paredes de su media arena.
    MARGEN = 20

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        lado: int = -1,
        coordinador: CoordinadorDeMitades | None = None,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=self.VIDA,
            damage_on_contact=self.DANO_CONTACTO,
        )
        #: -1 = mitad izquierda, +1 = mitad derecha.
        self.lado = lado
        self.coordinador = coordinador or CoordinadorDeMitades()
        self.set_boss_name("REY TERCIOPELO" if lado < 0 else "")

        self.rect.width = 26
        self.rect.height = 42
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        # Mismos sprites que el Rey: las mitades están hechas de las mismas
        # serpientes. Se dibujan más pequeñas por el rect, no por otro arte.
        self._load_boss_sprites(
            "boss_rey", 40, 56,
            sheets={"walk": (40, 56), "spit": (40, 56),
                    "hurt": (40, 56), "death": (40, 56)},
            base_dir=str(settings.ASSETS_DIR / "maps/stage2_4"),
        )
        # Dos fases: entera y enfurecida. `health_threshold[i]` es la vida
        # MÁXIMA de la fase i, así que la primera vale lo mismo que `VIDA`.
        self.set_phases([
            BossPhase(
                phase_index=0,
                health_threshold=self.VIDA,
                attack_patterns=["VENOM_SPIT"],
                movement_type="pursuit",
                speed_multiplier=1.0,
            ),
            BossPhase(
                phase_index=1,
                health_threshold=self.UMBRAL_FURIA,
                attack_patterns=["VENOM_SPIT"],
                movement_type="pursuit",
                speed_multiplier=self.FURIA_VELOCIDAD,
            ),
        ])
        self.attacks = AttackScheduler([
            BossAttack(
                "VENOM_SPIT", windup=0.5, active=0.2, recover=0.6,
                damage=self.SPIT_DAMAGE, reach=self.SPIT_RANGE,
                max_range=self.SPIT_RANGE, cooldown=self.SPIT_COOLDOWN,
            ),
        ])

        #: Suelo real, que fija el Rey al invocarla (ver `BossRey.take_summons`).
        self.floor_surface_y: float | None = None
        self._projectiles: list[dict[str, Any]] = []
        self._caida: float = 0.0
        #: ¿Cayó ya su compañera? Ver `quedarse_sola`.
        self._sola: bool = False
        #: Clave de animación del fotograma anterior; ver `_advance_animation`.
        self._animacion_previa: str = "walk"
        #: Última fase vista, para detectar el flanco en `_al_cambiar_de_phase`.
        self._ultima_phase: int = 0

    # ── Contrato de BossBase ───────────────────────────────────────────

    #: Mismo criterio que el Rey entero: la hoja `spit` es para el veneno.
    #: La mitad solo tiene ese ataque, pero se declara igual para que se vea
    #: de dónde sale la decisión y no parezca que siempre escupe.
    ATAQUES_DE_ESCUPIR: frozenset[str] = frozenset({"VENOM_SPIT"})

    _ANIM_FPS: dict[str, float] = {
        "walk": 10.0, "fly": 12.0, "shoot": 16.0,
        "hurt": 12.0, "die": 10.0, "death": 8.0,
    }

    def _get_animation_key(self) -> str:
        """Caminar o escupir. `HURT` y `DYING` los resuelve `BossBase`.

        Cada mitad carga las mismas cuatro hojas que el Rey entero, y antes
        devolvía `"walk"` siempre: escupía con pose de caminar. Como en la
        Fase 2 hay **dos** mitades en pantalla y solo una tiene el turno, la
        pose es justamente lo que deja ver cuál de las dos va a atacar.
        """
        actual = self.attacks.current
        if (
            actual is not None
            and actual.name in self.ATAQUES_DE_ESCUPIR
            and self.attack_timing in (AttackTiming.WINDUP, AttackTiming.ACTIVE)
        ):
            return "spit"
        return "walk"

    def _advance_animation(self, dt: float) -> None:
        """Igual que en `BossRey`: reiniciar al cambiar de hoja, no repetir la
        muerte en bucle y sincronizar el escupitajo con el aviso. El porqué de
        cada una está documentado en `BossRey._advance_animation`.
        """
        clave = self._get_animation_state()
        if clave != self._animacion_previa:
            self._animacion_previa = clave
            self._animation_frame = 0
            self._animation_timer = 0.0

        fotogramas = self._sprite_frames.get(clave)
        if not fotogramas:
            super()._advance_animation(dt)
            return

        if clave == "death":
            if self._animation_frame >= len(fotogramas) - 1:
                self._animation_frame = len(fotogramas) - 1
                return
            super()._advance_animation(dt)
            return

        if clave == "spit":
            total = len(fotogramas)
            if self.attack_timing == AttackTiming.WINDUP:
                avance = min(max(self.telegraph_progress, 0.0), 1.0)
                self._animation_frame = min(
                    int(avance * (total - 1)), total - 2)
            else:
                self._animation_frame = total - 1
            return

        super()._advance_animation(dt)

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(2, 2, self.rect.width - 4, self.rect.height - 4)

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(2, 2, self.rect.width - 4, self.rect.height - 4)

    def _patrol_behavior(self, dt: float) -> None:
        self._mover(dt)

    def _alert_behavior(self, dt: float) -> None:
        self._mover(dt)

    # ── Coordinación: uno ataca, el otro reposiciona ───────────────────

    @property
    def ataca_ahora(self) -> bool:
        """¿Le toca a esta mitad ser la agresiva?

        Enfurecida ya no cede el turno: sin compañera con quien alternar, el
        turno no reparte nada y solo la volvería pasiva media pelea.
        """
        if self.enfurecida:
            return True
        return self.coordinador.le_toca(self.lado)

    @property
    def enfurecida(self) -> bool:
        """¿Está en «La Furia»?

        Dos caminos llevan a lo mismo: haber bajado del umbral de vida —lo que
        el framework refleja avanzando `current_phase` a 1— o haberse quedado
        sola. Se consultan los dos aquí para que el resto de la clase no tenga
        que saber por cuál de las dos vías llegó.
        """
        return self.current_phase >= 1 or self._sola

    def quedarse_sola(self) -> None:
        """La compañera cayó: esta mitad pasa a pelear sin turnos.

        Lo llama el Rey desde `_vigilar_mitades`, que es quien sabe cuántas
        quedan. La mitad no vigila a su hermana por sí misma a propósito: dos
        entidades observándose mutuamente es un ciclo de referencias que
        complica el recolector sin ganar nada.
        """
        if self._sola:
            return
        self._sola = True
        self._aplicar_furia()

    def _al_cambiar_de_phase(self) -> None:
        """Detecta el flanco de fase y aplica la furia por heridas.

        `BossBase` gestiona la transición (invencibilidad, temporizador,
        `speed_multiplier`); aquí solo se ajusta lo que es propio de esta
        mitad, que es la cadencia de su escupitajo.
        """
        if self.current_phase == self._ultima_phase:
            return
        self._ultima_phase = self.current_phase
        self._aplicar_furia()

    def _aplicar_furia(self) -> None:
        """Acorta el enfriamiento del escupitajo si está enfurecida.

        Se parte SIEMPRE del valor base y no del actual: aplicar el factor
        sobre el valor ya reducido lo encogería otra vez en cada llamada, y
        entre la furia por heridas y la de soledad esto se invoca dos veces.
        """
        factor = self.FURIA_CADENCIA if self.enfurecida else 1.0
        for ataque in self.attacks._attacks:
            if ataque.name == "VENOM_SPIT":
                ataque.cooldown = self.SPIT_COOLDOWN * factor

    @property
    def _suelo(self) -> float:
        if self.floor_surface_y is not None:
            return float(self.floor_surface_y - self.rect.height)
        return self.position.y

    def _mover(self, dt: float) -> None:
        """Acercarse si es su turno; buscar el flanco contrario si no.

        La mitad que reposiciona no huye: se va al lado OPUESTO del jugador
        respecto a su compañera. Así el jugador queda entre las dos y tiene
        que decidir a cuál da la espalda — que es exactamente la lectura que
        la fase quiere enseñar.
        """
        if self._player_ref is None:
            return
        mi = pygame.Vector2(self.rect.centerx, self.rect.centery)
        suyo = pygame.Vector2(self._player_ref.centerx, self._player_ref.centery)
        hacia = vec2_normalize(suyo - mi)
        distancia = vec2_distance(mi, suyo)

        veloc = self.VELOCIDAD_ATAQUE * (
            self.FURIA_VELOCIDAD if self.enfurecida else 1.0)
        if self.ataca_ahora:
            # Acercarse hasta la distancia de tiro y mantenerla.
            if distancia > self.DISTANCIA_PREFERIDA:
                self.position.x += hacia.x * veloc * dt
            elif distancia < self.DISTANCIA_PREFERIDA * 0.6:
                self.position.x -= hacia.x * veloc * dt
        else:
            # Rodear: ponerse en el flanco de este lado del jugador.
            destino = suyo.x + self.lado * self.DISTANCIA_PREFERIDA
            paso = self.VELOCIDAD_REPOSICION * dt
            if abs(destino - self.position.x) > paso:
                self.position.x += paso * (1 if destino > self.position.x else -1)

        self.position.y = self._suelo
        self.clamp_to_arena(margin=self.MARGEN)

    # ── VENOM_SPIT (el mismo veneno del Rey) ───────────────────────────

    def on_attack_fired(self, attack_name: str) -> None:
        """Solo escupe la mitad a la que le toca el turno."""
        if attack_name != "VENOM_SPIT" or not self.ataca_ahora:
            return
        self._do_venom_spit()

    def _do_venom_spit(self) -> None:
        if self._player_ref is None:
            return
        mi = pygame.Vector2(self.rect.centerx, self.rect.centery)
        suyo = pygame.Vector2(self._player_ref.centerx, self._player_ref.centery)
        if vec2_distance(mi, suyo) > self.SPIT_RANGE:
            return
        direccion = vec2_normalize(suyo - mi)
        if direccion.length_squared() == 0.0:
            return
        self._projectiles.append({
            "pos": pygame.Vector2(mi),
            "vel": direccion * self.SPIT_SPEED,
            "damage": self.SPIT_DAMAGE,
            "alive": True,
        })
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="VENOM_SPIT", rect=self.rect)
        self._event_bus.emit(Events.SFX_BOSSES_REY_SPIT)

    # ── Ciclo ──────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        # El turno lo adelanta solo la mitad izquierda: si lo hicieran las dos
        # el reloj correría al doble de velocidad y los turnos durarían la
        # mitad de lo declarado.
        if self.lado < 0:
            self.coordinador.update(dt)
        super().update(dt)
        self._al_cambiar_de_phase()
        self.clamp_to_arena(margin=self.MARGEN)
        self._asentar(dt)

    def _asentar(self, dt: float) -> None:
        """Devuelve la mitad al suelo tras un golpe.

        Mismo defecto del motor que sufren el Rey y sus serpientes: el
        retroceso de `HURT` empuja hacia arriba y nada lo baja. Ver
        `BossRey._asentar_rey`.
        """
        if self.floor_surface_y is None or self.state.name in ("LAUNCHED", "DYING"):
            self._caida = 0.0
            return
        suelo = self._suelo
        if self.position.y >= suelo:
            self._caida = 0.0
            return
        self._caida += 600.0 * dt
        self.position.y = min(suelo, self.position.y + self._caida * dt)
        self.rect.y = int(self.position.y)

    def _post_update(self, dt: float) -> None:
        bordes = self.arena_bounds.inflate(64, 64) if self.arena_bounds else None
        for p in self._projectiles[:]:
            if not p["alive"]:
                self._projectiles.remove(p)
                continue
            p["pos"] += p["vel"] * dt
            if bordes is not None and not bordes.collidepoint(p["pos"]):
                p["alive"] = False

    def _check_player_contact(self, player: Player) -> None:
        blanco = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for p in self._projectiles:
            if not p["alive"]:
                continue
            r = pygame.Rect(int(p["pos"].x - 4), int(p["pos"].y - 4), 8, 8)
            if r.colliderect(blanco):
                player.apply_damage(p["damage"], self.rect.center)
                p["alive"] = False
        super()._check_player_contact(player)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        for p in self._projectiles:
            if not p["alive"]:
                continue
            sx = int(p["pos"].x - camera_offset.x)
            sy = int(p["pos"].y - camera_offset.y)
            pygame.draw.circle(surface, (60, 140, 40), (sx, sy), 4)
            pygame.draw.circle(surface, (200, 255, 180), (sx, sy), 4, 1)
