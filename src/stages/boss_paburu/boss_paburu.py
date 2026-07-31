"""
El Gran Shaman Paburu — Boss Final de Legacy of InFest.

Estado: EP1. Las 4 formas están declaradas sobre BossBase con visuales
placeholder y transiciones funcionando; la **Forma 1 está completa** con
sus tres patrones (`STONE_SPIT`, `EYE_BEAM`, `EL SELLO`). Las formas 2-4
llegan en EP2/EP3 según GDD §7.

Diseño y lore: `GDD.md` (canon: 17_BOSS_SPEC §6, 19_NARRATIVE_AND_LORE).
Este archivo NO modifica engine/ ni framework/ — solo los usa.

Mapeo académico de esta versión (ver README.md del stage):
  - Unidad II: tiro parabólico + rotación de vectores en `STONE_SPIT`;
               polar→cartesiano con escorzo en la geometría de `EL SELLO`.
  - Unidad V:  tinte espectral verde de la piedra (`ColorTools.apply_tint`).
  - Unidad VI: easings de `math_utils` en las columnas de `EL SELLO`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

import pygame

from src.engine.core.events import Events
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.enemy_base import EnemyState
from src.framework.processing.color_tools import ColorTools
from src.stages.boss_paburu import arena
from src.stages.boss_paburu.form1_attacks import (
    EyeBeam,
    SealAnima,
    SealCast,
    SealColumn,
    SealMemory,
    StoneProjectile,
    seal_vertices,
    spit_velocities,
)

if TYPE_CHECKING:
    from src.framework.entities.player import Player


# ── Identidad de las formas (GDD §4) ─────────────────────────────
FORM_STONE = 0    # "La Cabeza de Piedra"  — juzga sin mirar
FORM_MASK = 1     # "La Máscara Espectral" — juzga con la tradición
FORM_RELIC = 2    # "La Reliquia"          — delega en las reliquias (3A/3B)
FORM_SPIRIT = 3   # "El Espíritu"          — juzga cara a cara

FORM_NAMES = {
    FORM_STONE: "LA CABEZA DE PIEDRA",
    FORM_MASK: "LA MÁSCARA ESPECTRAL",
    FORM_RELIC: "LA RELIQUIA",
    FORM_SPIRIT: "EL ESPÍRITU DEL SHAMAN",
}

# Tamaño del sprite por forma (canon 17_BOSS_SPEC §6.2)
FORM_SIZES = {
    FORM_STONE: (64, 64),
    FORM_MASK: (56, 72),
    FORM_RELIC: (32, 32),
    FORM_SPIRIT: (64, 80),
}

# Paleta del cementerio (GDD §3.1) para los placeholders
_COL_STONE = (70, 110, 70)      # piedra con tinte verde
_COL_MASK = (0, 200, 100)       # verde espectral
_COL_GOLD = (232, 177, 44)      # La Pepita
_COL_PEARL = (13, 13, 20)       # La Perla
_COL_SPIRIT = (200, 230, 210)   # luz del espíritu

# Cadencias de la Forma 1 (GDD §4). Segundos.
COOLDOWNS_FORM1 = {
    "STONE_SPIT": 4.0,
    "EYE_BEAM": 8.0,
    "EL_SELLO": 10.0,
}

# Anatomía de la cabeza, en coordenadas locales al rect (64×64).
# La cabeza está "semienterrada" (GDD §4): los ojos y la boca quedan en el
# tercio inferior, cerca del suelo. No es solo estética — es lo que hace que
# el EYE_BEAM alcance al jugador de pie. Ver EyeBeam en form1_attacks.py.
EYE_DY = 38     # línea de los ojos: de aquí sale el EYE_BEAM
MOUTH_DY = 52   # boca: de aquí salen las piedras
MOUTH_DX = 20   # separación horizontal de la boca respecto del centro

# Las dos cuencas dentro del sprite de 64×64. Deben coincidir con
# `EYE_PIXELS` de `tools/gen_paburu_art.py`: sobre estos rects se pinta el
# encendido del telegraph del EYE_BEAM, para no necesitar una hoja aparte
# solo por los ojos.
EYE_BOXES = ((11, 38, 9, 4), (45, 38, 9, 4))

# Hojas de sprites: nombre → (ancho, alto) de frame.
# Los tamaños son los del canon 17_BOSS_SPEC §6.2 y cambian por forma. Este
# dict se le pasa tal cual a `_load_boss_sprites(sheets=...)`.
FORM_SHEETS = {
    # Forma 1 — implementada
    "stone": (64, 64),        # idle, 4f
    "hurt": (64, 64),         # reacción al golpe, 4f
    "stone_slam": (64, 64),   # pose de EL SELLO, 8f
    "stone_crack": (64, 64),  # transición 1→2, 8f
    # Formas 2-4 — solo idle. Las mecánicas son EP2/EP3 (GDD §7).
    "mask": (56, 72),         # Forma 2, 6f
    "gold": (32, 32),         # Forma 3A — La Pepita, 6f
    "black": (32, 32),        # Forma 3B — La Perla, 6f
    "spirit": (64, 80),       # Forma 4, 8f
}


class BossPaburu(BossBase):
    """El examinador. 20 corazones, 4 formas, una pregunta por ataque."""

    # FPS por animación. `EnemyBase._advance_animation` lee este dict;
    # los valores son los del canon 17_BOSS_SPEC §6.2.
    _ANIM_FPS: ClassVar[dict[str, float]] = {
        "stone": 6.0, "hurt": 12.0, "death": 8.0,
        "mask": 10.0, "gold": 14.0, "black": 14.0, "spirit": 10.0,
    }

    def __init__(self, spawn_position: pygame.Vector2, **props: object) -> None:
        max_health = float(props.get("max_health", 20.0))
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            # Forma 1 SIN daño por contacto.
            #
            # Estaba en 0.5 y hacía la pelea imposible de ganar. La cabeza
            # está semienterrada y no se mueve: la única forma de dañarla es
            # acercarse a golpearla cuerpo a cuerpo. Con daño por contacto,
            # *acercarse* costaba vida, así que el ataque cuerpo a cuerpo se
            # castigaba a sí mismo. Las cuentas: 20 de vida del boss a 1.0
            # por golpe largo son 20 aproximaciones; a 0.5 de contacto cada
            # una son 10 de daño recibido, y el jugador tiene 5. Ni jugando
            # perfecto alcanzaba.
            #
            # El GDD ya lo decía en palabras —"la piedra no embiste"—; el
            # número no acompañaba. Paburu amenaza con sus TRES ataques, que
            # es de lo que se trata un jefe de patrones: el peligro está en
            # leer el telegraph, no en rozarle la piedra.
            damage_on_contact=0.0,
        )
        self.set_boss_name("EL GRAN SHAMAN PABURU")

        # La arena entera es el campo de batalla. Desde el fix de BUG-078,
        # `BossBase` ya trae un default de boss (640×480) en vez del rango de
        # patrulla de `EnemyBase` (160×64), pero acá se declara explícito
        # porque esta arena mide 800×608 y el boss tiene que estar en combate
        # aunque el jugador se meta en el refugio más lejano.
        self.detection_range_x = float(arena.ARENA_W)
        self.detection_range_y = float(arena.ARENA_H)

        # Posición ancla: la cabeza de piedra vive apoyada aquí (Forma 1).
        self._anchor = pygame.Vector2(spawn_position)
        self._elapsed = 0.0

        # Apertura de ojos durante la entrada, de 0 (cerrados) a 1 (abiertos).
        # El GDD §4 dice que Paburu aparece con los ojos CERRADOS y que se
        # abren al empezar el combate: es su único gesto en la Forma 1, y
        # sin él la cabeza entra ya "encendida" y se pierde el momento.
        # Lo maneja `intro.py`; en el resto de la pelea vale 1.0.
        self.intro_eyes = 1.0

        # Forma 3: la selección Pepita/Perla se decide al ENTRAR a la forma
        # (aleatoria por sesión — GDD §4). None hasta entonces.
        self.relic_variant: str | None = None   # "gold" | "black"

        # ── Estado de los ataques de la Forma 1 ──────────────────
        self._projectiles: list[StoneProjectile] = []
        self._beams: list[EyeBeam] = []
        self._seal_casts: list[SealCast] = []
        self._animas: list[SealAnima] = []
        self._seal = SealMemory()
        self._seal_rotation = 0.0
        # Los tres patrones arrancan escalonados para que el combate no
        # empiece con los tres sincronizados en el mismo frame.
        self._attack_timers: dict[str, float] = {
            "STONE_SPIT": 1.5,
            "EYE_BEAM": 5.0,
            "EL_SELLO": 7.5,
        }

        # Arte propio. Si una hoja falta, draw() cae a los placeholders
        # grises — el juego corre igual con arte a medio hacer.
        #
        # Esto antes no se podía hacer con el helper del framework: solo
        # buscaba seis claves fijas heredadas del Venado y un único tamaño de
        # frame, así que ninguna hoja de Paburu cargaba. Con el fix de BUG-077
        # acepta un mapa {clave: (ancho, alto)} y una subcarpeta propia, que es
        # justo lo que hace falta para formas de 64×64, 56×72, 32×32 y 64×80.
        self._load_boss_sprites(
            "boss_paburu", 64, 64,
            sheets=FORM_SHEETS, base_dir="boss_paburu",
        )

        self._sync_rect_to_form()
        self.set_phases()

    # ── Fases ────────────────────────────────────────────────────
    def set_phases(self, phases: list[BossPhase] | None = None) -> None:
        """Las 4 formas del canon. Umbral = vida máxima de esa forma."""
        if phases is None:
            phases = [
                BossPhase(
                    phase_index=FORM_STONE, health_threshold=20.0,
                    attack_patterns=["STONE_SPIT", "EYE_BEAM", "EL_SELLO"],
                    movement_type="stationary",
                ),
                BossPhase(
                    phase_index=FORM_MASK, health_threshold=15.0,
                    attack_patterns=["SPIRIT_WAVE", "DUELO_DE_ECOS", "MASK_PULSE"],
                    movement_type="sine_drift",
                ),
                BossPhase(
                    phase_index=FORM_RELIC, health_threshold=10.0,
                    attack_patterns=[],  # se llenan al elegir 3A/3B
                    movement_type="relic",
                ),
                BossPhase(
                    phase_index=FORM_SPIRIT, health_threshold=5.0,
                    attack_patterns=[
                        "RELIC_SURGE", "SPIRIT_FORM", "ANCIENT_CALL",
                        "CONVERGENCE", "EL_OFRECIMIENTO",
                    ],
                    movement_type="spirit_float",
                ),
            ]
        super().set_phases(phases)

    def _finish_phase_transition(self) -> None:
        """Al cambiar de forma: ajustar tamaño y decidir la reliquia."""
        super()._finish_phase_transition()
        self._sync_rect_to_form()
        # Las columnas y el rayo en vuelo no sobreviven a la transición: el
        # boss es invulnerable durante ella, el jugador debería poder mirar.
        # Las MARCAS grabadas sí persisten — son la memoria de la arena.
        self._seal_casts.clear()
        self._beams.clear()
        if self.current_phase == FORM_RELIC and self.relic_variant is None:
            import random
            self.relic_variant = random.choice(["gold", "black"])
            # Los patrones de 3A/3B se implementan en EP3 (GDD §4 Forma 3).
        self._event_bus.emit(
            Events.SHOW_MESSAGE,
            text=f"FORMA {self.current_phase + 1}: {FORM_NAMES[self.current_phase]}",
            duration=3.0,
        )

    def _sync_rect_to_form(self) -> None:
        w, h = FORM_SIZES[self.current_phase]
        bottom = self._anchor.y + FORM_SIZES[FORM_STONE][1]
        self.rect.size = (w, h)
        # Todas las formas mantienen los "pies" al nivel de la piedra.
        self.position.update(self._anchor.x + (64 - w) // 2, bottom - h)
        self.rect.topleft = (int(self.position.x), int(self.position.y))

    # ── Hooks obligatorios de EnemyBase ─────────────────────────
    def _patrol_behavior(self, dt: float) -> None:
        self._update_movement(dt)

    def _alert_behavior(self, dt: float) -> None:
        self._update_movement(dt)
        self._face_player()

    def _update_movement(self, dt: float) -> None:
        """Movimiento por forma. EP1: solo la piedra (estática, tilt visual).
        Los movimientos de las formas 2-4 se implementan en sus EPs."""
        self._elapsed += dt
        if self.current_phase == FORM_STONE:
            # La piedra no se mueve (canon §6.3): posición anclada.
            self.rect.topleft = (int(self.position.x), int(self.position.y))
            return
        # FORM_MASK (EP2): deriva senoidal 20px @0.3Hz + 40px/s horizontal
        # FORM_RELIC (EP3): persecución (3A) u órbita (3B)
        # FORM_SPIRIT (EP3): flotación senoidal 32px @0.2Hz

    def _get_animation_key(self) -> str:
        keys = {FORM_STONE: "stone", FORM_MASK: "mask",
                FORM_RELIC: "gold" if self.relic_variant == "gold" else "black",
                FORM_SPIRIT: "spirit"}
        return keys[self.current_phase]

    def _build_hurtbox(self) -> pygame.Rect:
        # EP2: en FORM_MASK el hurtbox será SOLO la máscara (40×40, canon §6.4).
        return pygame.Rect(0, 0, self.rect.width, self.rect.height)

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.rect.width, self.rect.height)

    # ══════════════════════════════════════════════════════════════
    #  Ciclo de ataque de la Forma 1
    # ══════════════════════════════════════════════════════════════

    def _post_update(self, dt: float) -> None:
        """Reloj de ataques. Corre siempre que el boss esté vivo y activo.

        Va acá y no en `_alert_behavior` a propósito: `_run_state_machine`
        corta antes de llamar a los behaviors cuando el boss está en HURT o
        LAUNCHED, y ahí los proyectiles ya en vuelo se congelarían en el
        aire. `_post_update` es el único hook que corre en todos los estados
        vivos — y `_pre_update` ya lo saltea durante la transición de fase,
        que es justo lo que queremos.
        """
        if self.state == EnemyState.DYING:
            return

        self._advance_projectiles(dt)
        # El sello late aunque el boss cambie de forma: las marcas siguen
        # ahí toda la pelea.
        self._seal.update(dt)

        if self.current_phase != FORM_STONE or self._player_ref is None:
            return
        # Un ataque telegrafiado a la vez.
        #
        # Los tres relojes corrían sueltos y se pisaban: con los cooldowns
        # de 4 / 8 / 10 s, el rayo (que tarda 0.5 s de telegraph más casi
        # un segundo de viaje) llegaba SIEMPRE dentro de la ventana de
        # invulnerabilidad que la piedra acababa de regalar. Medido en 60 s
        # con el jugador quieto: al llegar el rayo quedaban 0.87-0.97 s de
        # invulnerabilidad, las siete veces. No fallaba a veces: no conectaba
        # nunca. El ataque estaba implementado y era decorativo.
        #
        # Además de arreglar el daño, esto ordena la lectura del combate:
        # el jugador reacciona a un telegraph por vez, que es de lo que se
        # trata un jefe de patrones.
        # La compuerta es ESTRECHA: solo se retiene la piedra mientras hay un
        # rayo en vuelo.
        #
        # El primer intento bloqueaba todo contra todo ("un ataque a la vez")
        # y arreglaba el rayo, pero de paso ahogaba al resto: medido, el
        # STONE_SPIT bajaba de 15 disparos por minuto a 4, con intervalos
        # irregulares de 4.5 a 8.8 s. El jefe quedaba pasivo y el ritmo que
        # define el GDD —4 / 8 / 10 s— dejaba de existir.
        #
        # El conflicto real es uno solo: el rayo tarda 0.5 s de telegraph más
        # casi un segundo de viaje, y la invulnerabilidad que regala una
        # piedra dura 1.5 s. Si la piedra pega en ese lapso, se come el rayo
        # entero. `EL SELLO` no compite: sus columnas salen del piso, en otro
        # espacio y con su propio telegraph.
        hay_rayo = bool(self._beams)
        for pattern in ("STONE_SPIT", "EYE_BEAM", "EL_SELLO"):
            self._attack_timers[pattern] -= dt
            if self._attack_timers[pattern] <= 0.0:
                if pattern == "STONE_SPIT" and hay_rayo:
                    # No pierde su turno: reintenta apenas el rayo se apaga.
                    self._attack_timers[pattern] = 0.25
                    continue
                self._attack_timers[pattern] = self._pattern_cooldown(pattern)
                getattr(self, f"_attack_{pattern.lower()}")()
                if pattern == "EYE_BEAM":
                    hay_rayo = True

    # ── Vida de la forma actual ─────────────────────────────────

    @property
    def hp_fraction(self) -> float:
        """Vida restante DE ESTA FORMA, entre 0 y 1.

        No es la vida total: `_phase_max_health` es el umbral de la forma
        en curso, así que la Forma 1 va de 1.0 (20♥) a 0.0 (15♥). Es la
        medida que interesa para leer cuán cerca está de transformarse.
        """
        return max(0.0, min(1.0, self.current_health / max(self._phase_max_health, 0.01)))

    def _pattern_cooldown(self, pattern: str) -> float:
        """Cadencia del patrón, acelerada a medida que la forma cae.

        Umbrales de vida de la Forma 1 (GDD §4: los números son punto de
        partida y se ajustan con playtesting):
          - por encima del 60 % de la forma → cadencia nominal
          - entre 60 % y 30 %               → 15 % más rápido
          - por debajo del 30 %             → 30 % más rápido
        La piedra no aprende ni cambia de patrón: solo insiste más. Es
        coherente con "juzga sin mirar" (GDD §2.1) y le da al jugador una
        señal legible de que la forma se está acabando.
        """
        base = COOLDOWNS_FORM1[pattern]
        hp = self.hp_fraction
        if hp <= 0.30:
            return base * 0.70
        if hp <= 0.60:
            return base * 0.85
        return base

    def _advance_projectiles(self, dt: float) -> None:
        """Avanza y recolecta todo lo que el boss tenga en vuelo."""
        for p in self._projectiles:
            p.update(dt)
        self._projectiles = [p for p in self._projectiles if p.alive]

        for b in self._beams:
            b.update(dt)
        self._beams = [b for b in self._beams if b.alive]

        for cast in self._seal_casts:
            cast.update(dt)
        for cast in self._seal_casts:
            if not cast.alive:
                # Al retraerse, la invocación queda grabada: la arena
                # recuerda. Y cada marca despierta un nombre por un instante.
                self._seal.engrave(cast.rotation)
                marks = seal_vertices(cast.rotation)
                for i, mark in enumerate(marks):
                    self._animas.append(SealAnima(mark, i, len(marks)))
        self._seal_casts = [c for c in self._seal_casts if c.alive]

        for a in self._animas:
            a.update(dt)
        self._animas = [a for a in self._animas if a.alive]

    # ── Los tres patrones (GDD §4 Forma 1) ──────────────────────

    def _attack_stone_spit(self) -> None:
        """3 proyectiles en arco, separación 15°, 0.5 de daño c/u."""
        player = self._player_ref
        if player is None:
            return
        self._face_player()
        muzzle = pygame.Vector2(
            self.rect.centerx + self.facing_direction * MOUTH_DX,
            self.rect.top + MOUTH_DY,
        )
        target = pygame.Vector2(player.centerx, player.bottom)
        for vel in spit_velocities(muzzle, target):
            self._projectiles.append(StoneProjectile(muzzle, vel))
        self._event_bus.emit(
            Events.SFX_PROJECTILE_FIRE, pos=(muzzle.x, muzzle.y),
        )

    def _attack_eye_beam(self) -> None:
        """Rayo horizontal de 8px con telegraph de 0.5 s. 1.0 de daño."""
        if self._player_ref is None:
            return
        self._face_player()
        eye = pygame.Vector2(self.rect.centerx, self.rect.top + EYE_DY)
        self._beams.append(EyeBeam(eye, self.facing_direction))
        self._event_bus.emit(
            Events.SFX_BOSSES_PABURU_EYE_BEAM, pos=(eye.x, eye.y),
        )

    def _attack_el_sello(self) -> None:
        """5 columnas que graban un fragmento del sello. 0.5 de daño.

        Cada invocación gira el pentágono 30°, así las columnas nunca
        emergen dos veces en las mismas X (el jugador no memoriza un patrón
        fijo) y las marcas van tejiendo el sello completo.
        """
        self._seal_casts.append(SealCast(self._seal_rotation))
        self._seal_rotation += 30.0
        # Sonido propio pendiente: por ahora, el rumble del entorno.
        self._event_bus.emit(Events.SFX_ENVIRONMENT_SCREEN_SHAKE)
        self._event_bus.emit(
            Events.VFX_SLAM, pos=(float(self.rect.centerx), float(arena.FLOOR_Y)),
        )
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="EL_SELLO", rect=self.rect)

    # ── Daño recibido ───────────────────────────────────────────

    def take_damage(self, amount: float,
                    source_position: tuple[float, float]) -> None:
        """Recibir daño. Entrada pública del boss.

        Delega en `BossBase.apply_hit`, que es la API real del framework:
        aplica invulnerabilidad, knockback, hitstun y dispara la revisión
        de umbrales de fase. Existe como método propio porque `apply_hit`
        es un nombre heredado de `EnemyBase` y no dice nada sobre quién
        recibe el golpe; acá el punto de entrada del boss se llama como lo
        que hace.

        La piedra no reacciona igual en toda la forma: al cruzar el 30 %
        de vida de la forma, los ojos quedan encendidos de manera
        permanente (ver `_draw_body`) y los ataques se aceleran (ver
        `_pattern_cooldown`).
        """
        self.apply_hit(amount, source_position)

    # ── Daño al jugador ─────────────────────────────────────────

    def _check_player_contact(self, player: Player) -> None:
        """Aplica el daño de los ataques y después el de contacto.

        `CollisionSystem.update_enemies` llama a esto una vez por frame,
        antes de `update()`. El jugador tiene 1.5 s de invulnerabilidad tras
        recibir daño, así que no hace falta consumir cada ataque al
        impactar: no hay multi-hit posible.
        """
        if not self.is_alive or self.state == EnemyState.DYING:
            return
        target = player.hurtbox if hasattr(player, "hurtbox") else player.rect

        # El RAYO se evalúa primero, y una sola vez por rayo.
        #
        # Antes iba último y sin marca de impacto. Como el rayo vive casi
        # 2 s barriendo la arena y la invulnerabilidad del jugador dura 1.5,
        # bastaba que una piedra —evaluada antes— conectara en cualquier
        # momento del barrido para que el rayo entero quedara anulado.
        # Medido en 60 s de combate con el jugador de pie y quieto: el rayo
        # llamaba a `apply_damage` 231 veces y causaba daño CERO. En la
        # práctica el ataque no existía.
        #
        # `_ya_golpeo` evita además que el mismo rayo pida daño una vez por
        # frame mientras lo cubre: pide una sola vez, cuando su frente lo
        # alcanza.
        for b in self._beams:
            if getattr(b, "_ya_golpeo", False):
                continue
            r = b.rect
            if r is not None and r.colliderect(target):
                b._ya_golpeo = True
                player.apply_damage(b.DAMAGE, self.rect.center)

        for p in self._projectiles:
            if p.rect.colliderect(target):
                player.apply_damage(p.DAMAGE, (p.pos.x, p.pos.y))
                p.alive = False

        for cast in self._seal_casts:
            for r in cast.damage_rects():
                if r.colliderect(target):
                    player.apply_damage(cast.columns[0].DAMAGE, r.center)
                    break

        super()._check_player_contact(player)

    # ── Dibujo ──────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Z-order interno del boss, de atrás hacia adelante:

            1. sello grabado — está en el piso, todo lo tapa
            2. columnas de EL SELLO — emergen del piso, delante del sello
            3. cuerpo de Paburu
            4. ánimas, proyectiles y rayo — en vuelo, delante de todo

        El orden entre entidades lo resuelve `DrawingSystem`, que ordena
        por `rect.centery`: el jugador (544) queda delante del boss (528).
        Acá solo se ordena lo que dibuja el boss.
        """
        self._seal.draw(surface, camera_offset)
        for cast in self._seal_casts:
            cast.draw(surface, camera_offset)

        self._draw_body(surface, camera_offset)

        for a in self._animas:
            a.draw(surface, camera_offset)
        for p in self._projectiles:
            p.draw(surface, camera_offset)
        for b in self._beams:
            b.draw(surface, camera_offset)

    def _pick_frame(self) -> pygame.Surface | None:
        """Elige la hoja y el frame según lo que esté pasando.

        Prioridad: transición (la piedra se agrieta) > golpe > EL SELLO >
        idle. Las dos primeras son de una sola pasada y se sincronizan con
        el reloj del evento, no con `_animation_frame`: así el último frame
        de la grieta cae exactamente cuando termina la transición.
        """
        # 1. Transición 1→2: la piedra se agrieta (GDD §4).
        crack = self._sprite_frames.get("stone_crack")
        if self.is_transitioning and self.current_phase == FORM_STONE and crack:
            done = 1.0 - max(self.transition_timer, 0.0) / 2.5
            return crack[min(int(done * len(crack)), len(crack) - 1)]

        # 2. Golpe. Solo en la Forma 1: la hoja `hurt` es de 64×64 y las
        #    Formas 3 miden 32×32 — blitearla ahí dibujaría la cabeza de
        #    piedra encima de la esfera, desbordando el rect.
        hurt = self._sprite_frames.get("hurt")
        if self.state == EnemyState.HURT and hurt and self.current_phase == FORM_STONE:
            done = 1.0 - max(self._hurt_timer, 0.0) / max(self._hurt_duration, 0.01)
            return hurt[min(int(done * len(hurt)), len(hurt) - 1)]

        # 3. EL SELLO en curso: los glifos del tocado se encienden.
        slam = self._sprite_frames.get("stone_slam")
        if self._seal_casts and slam:
            cast = self._seal_casts[-1]
            t = cast.columns[0].elapsed / SealColumn.TOTAL
            return slam[min(int(t * len(slam)), len(slam) - 1)]

        # 4. Idle, ciclado por `EnemyBase._advance_animation`.
        idle = self._sprite_frames.get(self._get_animation_key())
        if idle:
            return idle[min(self._animation_frame, len(idle) - 1)]
        return None

    # Aura espectral por forma. El verde es el mismo `SPECTRAL` del tinte
    # de la piedra, para que halo y cuerpo lean como una sola cosa.
    # La Forma 3 es la excepción: un halo verde sobre la Pepita dorada
    # ensuciaría el oro, y sobre La Perla contradiría su idea —una reliquia
    # que ABSORBE la luz en vez de emitirla—. Por eso la Pepita irradia su
    # propio dorado y La Perla lleva un halo violáceo, apenas visible.
    AURA_COLOR = (0, 200, 100)
    AURA_POR_FORMA = {
        FORM_RELIC: {"gold": (232, 177, 44), "pearl": (86, 60, 140)},
    }
    AURA_MARGEN = 22        # px que el halo desborda del sprite

    def _aura_color(self) -> tuple[int, int, int]:
        por_forma = self.AURA_POR_FORMA.get(self.current_phase)
        if por_forma is None:
            return self.AURA_COLOR
        return por_forma["gold" if self.relic_variant == "gold" else "pearl"]

    def _draw_aura(
        self, surface: pygame.Surface, frame: pygame.Surface, x: int, y: int,
    ) -> None:
        """Resplandor espectral alrededor del cuerpo.

        Paburu se dibujaba como una cabeza de piedra opaca, sin una sola
        fuente de luz propia: los cuencos de fuego de la arena y hasta los
        guardianes del fondo emitían resplandor, y EL ESPÍRITU no. Por eso
        se leía como una estatua puesta en el mapa y no como la aparición
        que describe el GDD §4.

        El halo se construye a partir de la SILUETA del frame, no de una
        imagen aparte: así sigue automáticamente cualquier pose —idle,
        golpe, grieta— sin necesidad de pintar un aura por hoja.

        Técnica: se tiñe la silueta de verde, se reduce a 1/5 y se vuelve a
        ampliar. El remuestreo bilineal difumina los bordes; es un
        desenfoque barato, determinista y sin dependencias, el mismo que
        usan los guardianes del fondo en `tools/gen_paburu_fondos.py`.

        Unidad V — color y composición aditiva.
        Unidad VI — interpolación bilineal del remuestreo y la respiración.
        """
        w, h = frame.get_size()
        m = self.AURA_MARGEN
        gw, gh = w + m * 2, h + m * 2

        # Silueta teñida: se copia el frame y se multiplica su RGB por el
        # verde espectral, conservando el canal alfa (la forma).
        silueta = pygame.Surface((w, h), pygame.SRCALPHA)
        silueta.blit(frame, (0, 0))
        silueta.fill((*self._aura_color(), 255), special_flags=pygame.BLEND_RGBA_MULT)

        lienzo = pygame.Surface((gw, gh), pygame.SRCALPHA)
        lienzo.blit(silueta, (m, m))
        chico = pygame.transform.smoothscale(lienzo, (max(1, gw // 5), max(1, gh // 5)))
        halo = pygame.transform.smoothscale(chico, (gw, gh))

        # Respiración: el aura late despacio. Se intensifica al bajar la
        # vida de la forma —la piedra ya no contiene lo que hay adentro— y
        # se dispara mientras carga el EYE_BEAM, donde funciona de aviso.
        import math
        pulso = 0.5 + 0.5 * math.sin(self._elapsed * 2.2)
        base = 46 + 34 * (1.0 - self.hp_fraction)
        if any(b.is_telegraphing for b in self._beams):
            base += 70
        # Durante la entrada el aura nace con los ojos: mientras la cabeza
        # duerme es piedra muerta, sin resplandor.
        base *= self.intro_eyes
        halo.set_alpha(int(max(0, min(255, base + 18 * pulso * self.intro_eyes))))
        surface.blit(halo, (x - m, y - m), special_flags=pygame.BLEND_ADD)

    def _draw_body(
        self, surface: pygame.Surface, camera_offset: pygame.Vector2,
    ) -> None:
        """Arte si existe; si no, placeholder gris por forma."""
        frame = self._pick_frame()
        if frame is not None:
            fx = int(self.position.x - camera_offset.x)
            fy = int(self.position.y - camera_offset.y)
            ox = (self.rect.width - frame.get_width()) // 2
            oy = self.rect.height - frame.get_height()

            # Retroceso al recibir un golpe.
            #
            # La cabeza no se movía NADA al ser golpeada: el jugador pegaba
            # y la piedra quedaba inerte, sin manera de saber si el ataque
            # había entrado. El GDD §4 le concede "inclinación ±8px como
            # única animación de movimiento", así que ese es el presupuesto:
            # se hunde un poco y se sacude en el eje del golpe, y vuelve.
            # No es adorno — es la única retroalimentación de impacto que
            # tiene un enemigo que ni se desplaza ni cambia de pose.
            import math

            # Balanceo de reposo. El GDD §4 le concede "inclinación ±8px
            # como única animación de movimiento": no camina ni salta, pero
            # tampoco es una estatua. Sin esto la cabeza queda clavada al
            # píxel y el jugador no distingue si el juego sigue corriendo.
            #
            # Dos senos de período distinto —uno horizontal lento y otro
            # vertical más lento todavía— evitan que el vaivén se lea como
            # un metrónomo. Se acelera al bajar la vida de la forma: la
            # piedra ya no aguanta lo que tiene adentro.
            agitacion = 1.0 + 1.4 * (1.0 - self.hp_fraction)
            ox += int(math.sin(self._elapsed * 0.85 * agitacion) * 4.0)
            oy += int(math.sin(self._elapsed * 0.55 * agitacion + 1.2) * 2.0)

            if self._hurt_timer > 0.0:
                k = max(0.0, min(1.0, self._hurt_timer / max(self._hurt_duration, 0.01)))
                sacudida = math.sin(self._hurt_timer * 46.0) * 6.0 * k
                ox += int(sacudida)
                oy += int(2.0 * k)

            self._draw_aura(surface, frame, fx + ox, fy + oy)
            surface.blit(frame, (fx + ox, fy + oy))
            # Los ojos se encienden al cargar el EYE_BEAM. Va como overlay
            # y no como hoja aparte: es un tell de gameplay, tiene que
            # poder aparecer sobre cualquier pose.
            # Por debajo del 30 % de vida de la forma los ojos ya no se
            # apagan: la piedra está a punto de romperse y se nota.
            encendidos = (any(b.is_telegraphing for b in self._beams)
                          or self.hp_fraction <= 0.30)
            # Durante la entrada los ojos se abren progresivamente, así que
            # el brillo se interpola en vez de encenderse de golpe.
            k = self.intro_eyes if self.intro_eyes < 1.0 else (
                1.0 if encendidos else 0.0)
            if k > 0.02:
                capa = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                for (ex, ey, ew, eh) in EYE_BOXES:
                    pygame.draw.rect(capa, (40, 255, 150), (ex, ey, ew, eh))
                    pygame.draw.rect(capa, (215, 255, 232), (ex + 3, ey + 1, 3, 2))
                capa.set_alpha(int(255 * k))
                surface.blit(capa, (fx + ox, fy + oy))
            return

        x = int(self.position.x - camera_offset.x)
        y = int(self.position.y - camera_offset.y)
        w, h = self.rect.size
        if self.current_phase == FORM_STONE:
            # Cabeza de piedra con tinte espectral (Unidad V — apply_tint)
            head = pygame.Surface((w, h))
            head.fill((110, 110, 110))
            pygame.draw.rect(head, (60, 60, 60), (8, 8, w - 16, h - 16), 3)
            tinted = ColorTools.apply_tint(head, (0, 120, 40))
            surface.blit(tinted, (x, y))
            # Ojos: se encienden al cargar el EYE_BEAM y en las transiciones.
            charging = any(b.is_telegraphing for b in self._beams)
            lit = charging or self.is_transitioning
            eye = (0, 255, 120) if lit else (20, 40, 20)
            pygame.draw.rect(surface, eye, (x + 12, y + EYE_DY - 3, 12, 6))
            pygame.draw.rect(surface, eye, (x + w - 24, y + EYE_DY - 3, 12, 6))
        elif self.current_phase == FORM_MASK:
            pygame.draw.rect(surface, _COL_MASK, (x, y, w, h), 2)
            pygame.draw.rect(surface, _COL_MASK, (x + 8, y + 8, 40, 40))
        elif self.current_phase == FORM_RELIC:
            col = _COL_GOLD if self.relic_variant == "gold" else _COL_PEARL
            pygame.draw.circle(surface, col, (x + w // 2, y + h // 2), w // 2)
            pygame.draw.circle(surface, (255, 255, 255),
                               (x + w // 2 - 4, y + h // 2 - 4), 3)
        else:  # FORM_SPIRIT
            pygame.draw.rect(surface, _COL_SPIRIT, (x, y, w, h), 2)
            pygame.draw.circle(surface, _COL_SPIRIT, (x + w // 2, y + 12), 8)

    # ── Introspección para los smoke tests ──────────────────────
    def debug_state(self) -> dict[str, Any]:
        """Snapshot del estado de combate. Solo lectura."""
        return {
            "phase": self.current_phase,
            "health": self.current_health,
            "projectiles": len(self._projectiles),
            "beams": len(self._beams),
            "seal_casts": len(self._seal_casts),
            "seal_marks": self._seal.count,
            "timers": dict(self._attack_timers),
        }
