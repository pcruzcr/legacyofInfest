# Autor: Alejandro Josué Rodríguez Zamora
# Stage 4-2 «El Gran Shamán Paburu» — Legacy of InFest
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

import math
from typing import TYPE_CHECKING, Any, ClassVar

import pygame

from src.engine.core import azar, settings
from src.engine.core.events import Events
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.boss_kit import WeakPoint, resolve_weak_point_damage
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
from src.stages.boss_paburu.form2_attacks import Eco, MaskPulse, SpiritWave
from src.stages.boss_paburu.form3_attacks import (
    EsquirlaDeOro,
    LagrimaNegra,
    MotorPepita,
    MotorPerla,
)
from src.stages.boss_paburu.form4_attacks import (
    EspejoEspectral,
    HazDelCirculo,
    JuicioFinal,
    SateliteReliquia,
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

# Cadencias de la Forma 2 — La Máscara Espectral.
#
# Toda la forma va más rápida que la Forma 1 porque el jefe ya no está
# semienterrado: se mueve, y un enemigo que se mueve y ataca despacio se lee
# como indeciso. Pero el duelo de ecos es el más lento de los tres a
# propósito: es el que pide parar, y parar necesita que el jugador vea venir
# el momento con tiempo.
COOLDOWNS_FORM2 = {
    "SPIRIT_WAVE": 3.4,
    "MASK_PULSE": 5.5,
    "DUELO_DE_ECOS": 7.5,
}

#: Todas las cadencias, en un solo sitio. `_pattern_cooldown` mira aquí, así
#: que añadir una forma es añadir su tabla y no tocar el planificador.
# Forma 3: cadencias por VARIANTE. La embestida y el cierre son los platos
# fuertes (el motor entero se reorganiza al lanzarlos); esquirlas y lágrima
# son la guarnición del parry.
COOLDOWNS_FORM3 = {
    "EMBESTIDA_TRIPLE": 7.5,
    "ESQUIRLAS_DE_ORO": 5.5,
    "ORBITA_CERRADA": 9.0,
    "LAGRIMA_NEGRA": 6.0,
}
# Forma 4: cadencias largas — cada patrón es un ACTO, no un golpe.
# EL_OFRECIMIENTO no lleva cadencia: no está en la rotación (es la
# ceremonia de muerte; ver `_iniciar_ofrecimiento`).
COOLDOWNS_FORM4 = {
    "RELIC_SURGE": 11.0,
    "SPIRIT_FORM": 8.5,
    "ANCIENT_CALL": 14.0,
    "CONVERGENCE": 10.0,
}
COOLDOWNS = {**COOLDOWNS_FORM1, **COOLDOWNS_FORM2, **COOLDOWNS_FORM3,
             **COOLDOWNS_FORM4}

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
    # Formas 2-4 — idle + poses (mejora D). Antes eran solo idle y el
    # framework mapea HURT a la clave literal «hurt»: golpear a la Máscara
    # mostraba los frames de la cabeza de piedra (64×64 sobre un cuerpo de
    # 56×72). Cada pose conserva el conteo de frames de su idle para que
    # el índice de animación siga siendo válido si la clave cambia a mitad
    # de ciclo.
    "mask": (56, 72),         # Forma 2, 6f
    "mask_hurt": (56, 72),    # retroceso + destello, 6f
    "mask_cast": (56, 72),    # ojos al blanco, boca goteando luz, 6f
    "gold": (32, 32),         # Forma 3A — La Pepita, 6f
    "gold_open": (32, 32),    # la ventana: apagada y agrietada, 6f
    "black": (32, 32),        # Forma 3B — La Perla, 6f
    "black_open": (32, 32),   # la ventana: la luz escapa por grietas, 6f
    "spirit": (64, 80),       # Forma 4, 8f
    "spirit_hurt": (64, 80),  # retroceso + destello, 8f
    "spirit_cast": (64, 80),  # el oro ritual encendido, 8f
}


class BossPaburu(BossBase):
    """El examinador. 20 corazones, 4 formas, una pregunta por ataque."""

    # FPS por animación. `EnemyBase._advance_animation` lee este dict;
    # los valores son los del canon 17_BOSS_SPEC §6.2.
    _ANIM_FPS: ClassVar[dict[str, float]] = {
        "stone": 6.0, "hurt": 12.0, "death": 8.0,
        "mask": 10.0, "gold": 14.0, "black": 14.0, "spirit": 10.0,
        # Las poses (mejora D): el daño rápido (el destello decae), el
        # casteo al ritmo del idle, y la ventana LENTA — es la única que
        # el jugador tiene que poder leer con calma para decidir entrar.
        "mask_hurt": 12.0, "mask_cast": 10.0,
        "gold_open": 6.0, "black_open": 6.0,
        "spirit_hurt": 12.0, "spirit_cast": 10.0,
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

        # Punto débil de la Forma 2. `BossBase` ya tiene la lista y la
        # resolución escritas (`weak_points`, `apply_hit_at`); lo único que
        # falta en el motor es que alguien le pase el rect del golpe, y eso
        # se resuelve en `apply_hit` más abajo.
        self.weak_points = [self.MASK_WEAK_POINT]

        # Referencia al Player completo. `EnemyBase` solo guarda un `Rect`
        # (`_player_ref`), que no alcanza: para saber si el golpe acertó la
        # máscara hace falta el `active_hitbox`, que es dónde pegó y no dónde
        # está parado. La escena la inyecta en su `on_enter`.
        self.player_obj: Player | None = None

        # Apertura de ojos durante la entrada, de 0 (cerrados) a 1 (abiertos).
        # El GDD §4 dice que Paburu aparece con los ojos CERRADOS y que se
        # abren al empezar el combate: es su único gesto en la Forma 1, y
        # sin él la cabeza entra ya "encendida" y se pierde el momento.
        # Lo maneja `intro.py`; en el resto de la pelea vale 1.0.
        self.intro_eyes = 1.0

        # Forma 3: la selección Pepita/Perla se decide al ENTRAR a la forma
        # (aleatoria por sesión — GDD §4). None hasta entonces.
        self.relic_variant: str | None = None   # "gold" | "black"

        #: AUD-487 — el azar del jefe, propio y aislado (GAP-042 / AUD-398).
        #:
        #: No se tira del `random` de módulo: compartir el global hace que el
        #: patrón de CONVERGENCE dependa de cuántas partículas de ambiente
        #: sorteó el clima ese fotograma, y entonces una prueba que quiera
        #: fijar el patrón tendría que fijar el azar del juego entero. Con
        #: generador propio se siembra sólo esto.
        self._azar = azar.generador()

        # ── Estado de los ataques de la Forma 1 ──────────────────
        self._projectiles: list[StoneProjectile] = []
        self._beams: list[EyeBeam] = []
        # Forma 2. Van en listas propias y no mezcladas con las de la Forma 1
        # porque el parry, el dibujo y el contacto las recorren por separado y
        # cada una tiene su geometría: la ola es un rect rasante, el pulso es
        # un anillo y el eco es un círculo.
        self._olas: list = []
        # Forma 3 — la Reliquia. El motor (Pepita o Perla) gobierna el
        # MOVIMIENTO del propio jefe; se crea al entrar en la forma, cuando
        # ya se sorteó la variante.
        self._motor_reliquia: MotorPepita | MotorPerla | None = None
        self._esquirlas: list = []
        self._lagrimas: list = []
        # Forma 4 — el Espíritu.
        self._satelites: list = []
        self._espejos: list = []
        self._haces: list = []
        # EL OFRECIMIENTO: la ceremonia de muerte. `None` = no empezó;
        # un JuicioFinal en vuelo = está preguntando; `absuelto` guarda
        # CÓMO terminó — la marca del final del jugador.
        self._juicio: JuicioFinal | None = None
        self._ofrecimiento_t: float | None = None
        self.absuelto: bool = False
        # El EPÍLOGO (GDD §204): tras el veredicto, la despedida. `None` =
        # no empezó. Las ánimas son las motas en que el Espíritu se
        # disuelve al ascender: (pos, vel, edad).
        self._epilogo_t: float | None = None
        self._animas_del_adios: list[list] = []
        self._cuerpo_visible: bool = True
        # Pose de casteo (mejora D): los ataques de la Máscara y del
        # Espíritu la arman a 0.6 s y decae en `_post_update`. Mientras
        # dura, `_get_animation_key` muestra la hoja «cast»: el cuerpo
        # dice que el ataque salió de él, no de la nada.
        self._pose_cast_t = 0.0
        # SFX propios (mejora B): la escena inyecta aquí su reproductor
        # (`BossPaburuScene._sfx_propio`) al invocarlo. Los momentos únicos
        # de la pelea —el llamado, el juicio, el veredicto, el sello— tienen
        # voz propia en `assets/sfx/bosses/` en vez de reciclar tres
        # muestras genéricas. Es un atributo y no un evento porque los
        # `Events` son del motor y no se tocan; el `SoundBank` carga por
        # nombre de archivo y `play_sfx` respeta mute y volúmenes.
        self.reproducir_sfx = None
        self._pulsos: list = []
        self._ecos: list = []
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
            # MIGRACIÓN v2: `base_dir` cambió de significado. En el motor
            # anterior era el nombre de una subcarpeta y el framework la
            # colgaba de `assets/sprites/`; ahora es la **ruta completa** y se
            # usa tal cual. Pasar `"boss_paburu"` la resolvía contra el
            # directorio de trabajo, no existía, y las cuatro formas caían al
            # placeholder gris sin ningún error visible — el juego arrancaba
            # igual. Se pasa la ruta armada desde `settings.ASSETS_DIR`.
            sheets=FORM_SHEETS,
            base_dir=settings.ASSETS_DIR / "sprites" / "boss_paburu",
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
                    # AUD-257 hizo real la escala de fase: el Espíritu es un
                    # quinto más grande que la máscara — el shamán entero,
                    # ya sin cáscaras. EL_OFRECIMIENTO queda declarado en la
                    # lista por contrato de diseño, pero no tiene método de
                    # rotación a propósito: `_patrones_de_la_fase` lo filtra
                    # y la ceremonia lo dispara al llegar a cero.
                    escala=1.2,
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
        self._olas.clear()
        self._pulsos.clear()
        self._ecos.clear()
        self._esquirlas.clear()
        self._lagrimas.clear()
        self._satelites.clear()
        self._espejos.clear()
        self._haces.clear()
        # AUD-485 — DOS LISTAS SE QUEDARON FUERA DEL BARRIDO.
        #
        # `_projectiles` (las piedras de la Forma 1) y `_animas` (Forma 2)
        # sobrevivían a la transición y seguían dañando MIENTRAS el jefe es
        # invulnerable y la cámara está en el cambio de forma: 1,0 de daño
        # medido, recibido sin nadie a quien responder. Que la lista se
        # llamara distinto no la hace distinta — es la misma regla que ya
        # justifica las nueve de arriba: lo que estaba en vuelo cuando la
        # forma murió no le pertenece a la siguiente.
        self._projectiles.clear()
        self._animas.clear()
        if self.current_phase == FORM_RELIC:
            if self.relic_variant is None:
                import random
                self.relic_variant = random.choice(["gold", "black"])
            # LA INYECCIÓN. `attack_patterns` de la fase 3 nace VACÍA en
            # `set_phases` a propósito: los patrones dependen del sorteo, y
            # declararlos antes de sortear obligaría al planificador a saber
            # de variantes. Se llenan aquí y `_patrones_de_la_fase` los
            # recoge sin tocar una línea del planificador — exactamente el
            # mecanismo de extensión que ya usaron las Formas 1 y 2.
            fase = self.phases[FORM_RELIC]
            if self.relic_variant == "gold":
                fase.attack_patterns = ["EMBESTIDA_TRIPLE", "ESQUIRLAS_DE_ORO"]
            else:
                fase.attack_patterns = ["ORBITA_CERRADA", "LAGRIMA_NEGRA"]
            # El motor de la variante. La arena real la puso la escena vía
            # `set_arena_bounds`; sin ella (arneses viejos) se cae a un
            # rectángulo alrededor del ancla.
            arena_r = self.arena_bounds or pygame.Rect(
                int(self._anchor.x) - 368, int(self._anchor.y) - 480, 800, 560)
            suelo = self._anchor.y + FORM_SIZES[FORM_STONE][1]
            if self.relic_variant == "gold":
                self._motor_reliquia = MotorPepita(arena_r, suelo)
            else:
                self._motor_reliquia = MotorPerla(
                    arena_r, suelo, pygame.Vector2(self.rect.center))
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

    # ── R21 — al juez no lo empujan ─────────────────────────────
    def _apply_knockback(self, dt: float) -> None:
        """El golpe del portador no desplaza a Paburu. Descubierto en el
        video: «puedo pegarle a Paburu y sacarlo del mapa y ya no vuelve».

        La cadena: `EnemyBase.apply_hit` carga `_knockback_velocity` con
        cada golpe y `_apply_knockback` la integra a `position`; la Cabeza
        y la Máscara anclan su rect a esa `position` y `_sync_rect_to_form`
        solo re-ancla en los cambios de forma — así que el empuje se
        ACUMULABA golpe a golpe hasta sacar al jefe de la sala, sin camino
        de vuelta. (La Reliquia y el Espíritu no lo sufrían: sus motores
        recalculan la posición entera cada fotograma.)

        Un shamán juez hecho de piedra no retrocede porque lo golpeen: el
        golpe ya tiene su feedback (destello, hit-stop, la barra). Se
        descarta el impulso en vez de taparlo con un clamp — el clamp
        habría dejado al jefe VIBRANDO contra el borde de la sala.
        """
        self._knockback_velocity.update(0.0, 0.0)

    # ── Hooks obligatorios de EnemyBase ─────────────────────────
    def _patrol_behavior(self, dt: float) -> None:
        self._update_movement(dt)

    def _alert_behavior(self, dt: float) -> None:
        self._update_movement(dt)
        self._face_player()

    def _update_movement(self, dt: float) -> None:
        """Movimiento por forma. EP1: solo la piedra (estática, tilt visual).
        Los movimientos de las formas 2-4 se implementan en sus EPs.

        `_elapsed` ya NO avanza acá: lo hace `_post_update`, que corre en
        todos los estados — acá se duplicaba cuando los behaviors corrían."""
        if self.current_phase == FORM_STONE:
            # La piedra no se mueve (canon §6.3): posición anclada.
            self.rect.topleft = (int(self.position.x), int(self.position.y))
            return
        # FORM_MASK (EP2): deriva senoidal 20px @0.3Hz + 40px/s horizontal
        # Las formas 3 y 4 NO se mueven acá: ver `_mover_formas_libres` en
        # `_post_update`. Los behaviors solo corren en PATROL/ALERT, y la
        # máquina de estados heredada mete al jefe en RETREAT/HURT con el
        # jugador cerca — medido: la Reliquia y el Espíritu se quedaban
        # pegados al suelo caminando de espaldas, porque el estado base les
        # robaba el cuerpo. Su movimiento ES la forma, así que vive donde
        # el reloj de ataques: en el único hook que corre en todos los
        # estados vivos.

    def _get_animation_state(self) -> str:
        """Anula el mapeo del framework SOLO para HURT (mejora D).

        `BossBase._get_animation_state` devuelve la clave literal «hurt»
        para el estado HURT, y la única hoja con ese nombre es la de la
        cabeza de piedra: recibir daño en las Formas 2-4 mostraba 64×64 de
        piedra sobre cuerpos de otra forma y tamaño. Cada forma tiene
        ahora su reacción; la Reliquia conserva su idle a propósito — su
        señal de daño es la VENTANA (abajo), no el retroceso.
        """
        if self.state == EnemyState.HURT:
            reacciones = {FORM_MASK: "mask_hurt", FORM_SPIRIT: "spirit_hurt"}
            reaccion = reacciones.get(self.current_phase)
            if reaccion is not None:
                return reaccion
        return super()._get_animation_state()

    def _get_animation_key(self) -> str:
        # La Reliquia dice su ventana con el cuerpo (mejora D): mientras
        # `ventana_abierta` el golpe entra ×4, y la esfera se agrieta para
        # que la invitación se VEA — regla de oro de los jefes de patrón:
        # el estado interno que cambia las reglas no puede ser secreto.
        if self.current_phase == FORM_RELIC:
            clave = "gold" if self.relic_variant == "gold" else "black"
            if (self._motor_reliquia is not None
                    and self._motor_reliquia.ventana_abierta):
                return clave + "_open"
            return clave
        # La Máscara y el Espíritu castean: `_pose_cast_t` lo arman los
        # ataques y decae en `_post_update`. No es el telegraph del
        # proyectil (ese vive en cada ataque): es el CUERPO diciendo que
        # el ataque salió de él y no de la nada.
        if self.current_phase == FORM_MASK:
            return "mask_cast" if self._pose_cast_t > 0.0 else "mask"
        if self.current_phase == FORM_SPIRIT:
            return "spirit_cast" if self._pose_cast_t > 0.0 else "spirit"
        return "stone"

    # ── Punto débil de la Forma 2 ───────────────────────────────
    # GDD §4: "Solo la máscara recibe daño (40×40 px)". El motor nuevo trae
    # `WeakPoint` en `boss_kit`, que es exactamente esta idea: una zona con
    # multiplicador, expuesta solo en ciertas fases.
    #
    # La máscara mide 56×72; el punto va centrado en su tercio superior, que
    # es donde está la cara. Se declara acá y se registra en `__init__`.
    MASK_WEAK_POINT = WeakPoint(
        offset=(8, 6), size=(40, 40),
        multiplier=2.5,
        phases=(FORM_MASK,),
        label="máscara",
    )

    def _build_hurtbox(self) -> pygame.Rect:
        # El hurtbox sigue siendo el cuerpo entero: es lo que decide si el
        # golpe conecta. Que la máscara valga más —y el resto nada— lo
        # resuelve `apply_hit`, porque el hurtbox no sabe *dónde* le pegaron.
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

        # `_elapsed` avanzaba solo dentro de `_update_movement` (behaviors):
        # con el jefe en RETREAT el reloj del vaivén se congelaba junto con
        # el cuerpo. El tiempo de la coreografía corre acá, siempre.
        self._elapsed += dt
        if self._pose_cast_t > 0.0:
            self._pose_cast_t = max(0.0, self._pose_cast_t - dt)
        self._mover_formas_libres(dt)
        self._advance_projectiles(dt)
        self._revisar_devueltos()
        self._avanzar_ofrecimiento(dt)
        self._avanzar_epilogo(dt)
        if self.ofrecimiento_activo:
            # Durante la ceremonia no hay rotación de ataques: la sala está
            # en silencio y la única pregunta en vuelo es el juicio.
            self._seal.update(dt)
            return
        # El sello late aunque el boss cambie de forma: las marcas siguen
        # ahí toda la pelea.
        self._seal.update(dt)

        # Antes decía `if self.current_phase != FORM_STONE: return`, y era el
        # verdadero motivo de que las formas 2-4 no atacaran: el planificador
        # se cortaba entero salvo en la Forma 1. Se escribió así cuando la
        # Forma 1 era lo único implementado —era correcto entonces— y quedó
        # como un techo invisible: se podían añadir ataques nuevos, declararlos
        # en la fase y escribir sus métodos, y no se lanzaba ninguno.
        #
        # Ahora la condición es la que corresponde: se ataca si la forma actual
        # DECLARA ataques implementados. Una fase sin patrones —la 3 y la 4 hoy
        # mismo— sigue quedándose quieta, pero por no tener nada que lanzar, no
        # por un número escrito a mano.
        if self._player_ref is None or not self._patrones_de_la_fase():
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
        # Los patrones salen de la FASE ACTUAL, no de una tupla fija.
        #
        # Estaba escrito `for pattern in ("STONE_SPIT", "EYE_BEAM",
        # "EL_SELLO")`, o sea los tres de la Forma 1 y nada más. Las otras tres
        # formas tenían sus ataques declarados en `set_phases` y ese bucle no
        # los miraba nunca: al bajar de fase, Paburu cambiaba de sprite, de
        # tamaño y de luz, y se quedaba quieto. Las formas existían; lo que no
        # existía era qué hacen.
        #
        # `_patrones_de_la_fase` devuelve lo que declara la fase, así que
        # añadir un ataque nuevo es declararlo en `set_phases` y escribir su
        # `_attack_<nombre>`: el planificador no hay que volver a tocarlo.
        for pattern in self._patrones_de_la_fase():
            # `setdefault` y no acceso directo: `_attack_timers` se siembra con
            # los patrones de la Forma 1 y nada más. Al cambiar de forma, el
            # primer patrón nuevo daba KeyError, la excepción abortaba el
            # planificador entero —y con él los temporizadores de TODOS los
            # ataques— y Paburu se quedaba quieto para siempre. Se veía como
            # "la Forma 2 no ataca"; en realidad se había roto el reloj.
            #
            # El valor inicial es la mitad de la cadencia: al entrar en una
            # forma nueva el jefe ataca pronto, pero no en el mismo fotograma
            # en que termina la transformación.
            if pattern not in self._attack_timers:
                self._attack_timers[pattern] = self._pattern_cooldown(pattern) * 0.5
            self._attack_timers[pattern] -= dt
            if self._attack_timers[pattern] <= 0.0:
                if pattern == "STONE_SPIT" and hay_rayo:
                    # No pierde su turno: reintenta apenas el rayo se apaga.
                    self._attack_timers[pattern] = 0.25
                    continue
                self._attack_timers[pattern] = self._pattern_cooldown(pattern)
                getattr(self, f"_attack_{pattern.lower()}")()
                # La pose de casteo (mejora D) se arma AQUÍ y no dentro de
                # cada `_attack_*`: el planificador es el único sitio por
                # el que pasan todos los ataques de todas las formas, así
                # que un patrón nuevo la hereda sin acordarse de pedirla.
                # 0.6 s ≈ un ciclo corto de la hoja «cast»; en la Forma 1 y
                # la Reliquia el atributo existe pero ninguna clave lo lee.
                self._pose_cast_t = 0.6
                if pattern == "EYE_BEAM":
                    hay_rayo = True


    def _mover_formas_libres(self, dt: float) -> None:
        """El cuerpo de la Reliquia y del Espíritu, en todos los estados.

        Vive en `_post_update` y no en los behaviors por la misma razón que
        el reloj de ataques: `_run_state_machine` corta los behaviors en
        HURT, LAUNCHED y RETREAT, y estas dos formas SON su movimiento — una
        Reliquia que deja de perseguir porque el estado base decidió
        retirarse no es una pausa: es el jefe rompiéndose en pantalla.
        """
        if self.is_transitioning:
            return
        if self.current_phase == FORM_RELIC and self._motor_reliquia is not None:
            # La Reliquia ES movimiento: el motor de la variante gobierna la
            # posición del cuerpo, que es el arma principal de esta forma.
            self._motor_reliquia.update(self, self._player_ref, dt)
            # El contacto solo daña cuando el motor dice que va lanzada; una
            # reliquia agotada o abierta es la ventana, no una trampa.
            self.damage_on_contact = (
                1.0 if self._motor_reliquia.peligrosa else 0.0)
        elif self.current_phase == FORM_SPIRIT:
            # R21 — EL ESPÍRITU BAJA A PREGUNTAR. La v1 flotaba clavado en
            # el centro a 170±32 px del suelo: «está muy alto, no se le
            # puede llegar, no baja, no sigue al oponente pero ataca
            # mucho» (playtest del video). Un juez que interroga desde el
            # palco no es un duelo. Ahora: (1) PERSIGUE — el cuerpo deriva
            # despacio hacia la x del portador (55 px/s, con margen de
            # arena); (2) SU VAIVÉN LO BAJA AL ALCANCE — 112±46 px del
            # suelo: en la parte baja del ciclo el cuerpo queda a la
            # altura de un salto normal (ventana de castigo), en la alta
            # se escapa (ventana de esquivar). El ritmo del duelo ES el
            # seno. Durante EL OFRECIMIENTO y el epílogo vuelve a alzarse
            # al centro: ahí es juez, no blanco.
            arena_r = self.arena_bounds or pygame.Rect(
                int(self._anchor.x) - 368, int(self._anchor.y) - 480, 800, 560)
            suelo = self._anchor.y + FORM_SIZES[FORM_STONE][1]
            alza = 46.0 if self._ofrecimiento_t is not None else 0.0
            if self._epilogo_t is not None:
                # El ascenso: desde EPILOGO_ASCENSO sube 90 px con el
                # smoothstep de siempre — el juez se retira hacia arriba.
                p_asc = max(0.0, (self._epilogo_t - self.EPILOGO_ASCENSO)
                            / (self.EPILOGO_FIN - self.EPILOGO_ASCENSO))
                alza = 46.0 + 90.0 * (p_asc * p_asc * (3 - 2 * p_asc))
            en_ceremonia = alza > 0.0
            cx_actual = getattr(self, "_esp_cx", None)
            if cx_actual is None:
                cx_actual = float(arena_r.centerx - 80)
            if en_ceremonia:
                # La ceremonia lo devuelve al estrado, suave.
                objetivo = float(arena_r.centerx - 80)
                paso = 90.0 * dt
                base_y = 170.0
            else:
                jugador = self._player_ref
                objetivo = (float(jugador.centerx) if jugador is not None
                            else cx_actual)
                paso = 55.0 * dt
                base_y = 112.0
            delta = objetivo - cx_actual
            if abs(delta) > paso:
                cx_actual += paso if delta > 0 else -paso
            else:
                cx_actual = objetivo
            cx_actual = float(max(arena_r.left + 70,
                                  min(arena_r.right - 70, cx_actual)))
            self._esp_cx = cx_actual
            cy = (suelo - base_y - alza
                  + math.sin(self._elapsed * 2 * math.pi * 0.22) * 46.0)
            self.rect.center = (int(cx_actual), int(cy))
            self.position.update(float(self.rect.x), float(self.rect.y))
            self.damage_on_contact = 0.0    # el Espíritu no es una trampa

    def _patrones_de_la_fase(self) -> tuple[str, ...]:
        """Los ataques que puede lanzar la forma actual.

        Se filtran los que todavía no tienen método: durante el desarrollo una
        fase puede declarar cinco ataques y tener escritos dos, y sin este
        filtro el planificador reventaría con `AttributeError` en mitad de la
        pelea en vez de simplemente usar los que hay.
        """
        fases = getattr(self, "phases", None) or []
        if not (0 <= self.current_phase < len(fases)):
            return ()
        declarados = getattr(fases[self.current_phase], "attack_patterns", ()) or ()
        return tuple(
            p for p in declarados if hasattr(self, f"_attack_{p.lower()}")
        )

    def _revisar_devueltos(self) -> None:
        """Lo que el jugador devolvió y ahora vuela hacia Paburu.

        Un ataque devuelto cambia de dueño: deja de dañar al jugador y pasa
        a dañar al jefe. Se resuelve acá y no en `_check_player_contact`
        porque ese método responde la pregunta contraria — qué le pega al
        jugador — y meter el caso inverso ahí lo volvería ilegible.
        """
        cuerpo = self.hurtbox
        for p in self._projectiles:
            if not p.devuelta or not p.alive:
                continue
            if p.rect.colliderect(cuerpo):
                p.alive = False
                self.apply_hit(p.DAMAGE_DEVUELTA, (p.pos.x, p.pos.y))
                self._event_bus.emit(
                    Events.VFX_PARRY, pos=(p.pos.x, p.pos.y),
                )
        for e in (*self._esquirlas, *self._lagrimas):
            if not e.devuelta or not e.alive:
                continue
            if e.rect is not None and e.rect.colliderect(cuerpo):
                e.alive = False
                self.apply_hit(e.DANIO_DEVUELTA, (e.pos.x, e.pos.y))
                # La lágrima devuelta hace lo que ningún otro golpe: fuerza
                # la ventana de la Perla fuera de turno. El parry fabrica lo
                # que normalmente hay que esperar.
                if (isinstance(e, LagrimaNegra)
                        and isinstance(self._motor_reliquia, MotorPerla)):
                    self._motor_reliquia.abrir()
                self._event_bus.emit(
                    Events.VFX_PARRY, pos=(e.pos.x, e.pos.y))

        for b in self._beams:
            if not b.devuelto or getattr(b, "_golpeo_jefe", False):
                continue
            if b.hits(cuerpo):
                b._golpeo_jefe = True
                self.apply_hit(b.DAMAGE_DEVUELTO, (b.origin.x, b.origin.y))
                self._event_bus.emit(
                    Events.VFX_PARRY, pos=(self.position.x, self.position.y),
                )

    # ── Vida de la forma actual ─────────────────────────────────

    @property
    def hp_fraction(self) -> float:
        """Vida restante DE ESTA FORMA, entre 1.0 (recién entrada) y 0.0
        (a punto de transformarse).

        AUD-493 — ANTES NUNCA LLEGABA A CERO, Y POR ESO NADA SE ACELERABA.
        ------------------------------------------------------------------
        La fórmula vieja era `current_health / _phase_max_health`, o sea la
        vida contra el umbral de ENTRADA de la forma. Con los umbrales del
        canon (20/15/10/5) eso da recorridos que ni se acercan a los tramos
        que el resto del código consulta:

            Forma 1: 20♥→15♥  ⇒  1.00 → 0.75
            Forma 2: 15♥→10♥  ⇒  1.00 → 0.67
            Forma 3: 10♥→ 5♥  ⇒  1.00 → 0.50
            Forma 4:  5♥→ 0♥  ⇒  1.00 → 0.00

        `_pattern_cooldown` acelera bajo el 60 % y bajo el 30 %, la máscara
        se agita bajo el 30 %, el ojo se abre bajo el 30 %: en las Formas 1 y
        2 NINGUNO de esos tramos se alcanzaba jamás, y en la 3 sólo el
        primero. El docstring del propio `_pattern_cooldown` describía tres
        escalones de presión de los que dos no existían. Sólo la Forma 4
        —la única cuyo umbral siguiente es 0— se comportaba como estaba
        escrito, que es justo por qué el defecto pasó desapercibido.

        Ahora se mide contra el TRAMO real de la forma: cuánto le queda de su
        propia barra, no cuánto le queda de la barra total del jefe.
        """
        techo = float(self._phase_max_health)
        siguiente = self.current_phase + 1
        piso = (float(self.phase_health_thresholds[siguiente])
                if 0 <= siguiente < len(self.phase_health_thresholds)
                else 0.0)
        tramo = techo - piso
        if tramo <= 0.01:
            # Sin tramo declarado (arneses con una sola fase, umbrales
            # iguales): se cae a la lectura vieja en vez de dividir por cero.
            return max(0.0, min(1.0, self.current_health / max(techo, 0.01)))
        return max(0.0, min(1.0, (self.current_health - piso) / tramo))

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
        # `COOLDOWNS` y no `COOLDOWNS_FORM1`: con la tabla de la Forma 1, el
        # primer ataque de la Forma 2 reventaba con KeyError.
        base = COOLDOWNS.get(pattern, 5.0)
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

        for grupo in (self._olas, self._pulsos, self._ecos,
                      self._esquirlas, self._lagrimas):
            for a in grupo:
                a.update(dt)
        self._olas = [a for a in self._olas if a.alive]
        self._pulsos = [a for a in self._pulsos if a.alive]
        self._ecos = [a for a in self._ecos if a.alive]
        self._esquirlas = [a for a in self._esquirlas if a.alive]
        self._lagrimas = [a for a in self._lagrimas if a.alive]

        # Forma 4: los satélites siguen al Espíritu; el espejo suelta su ola
        # exactamente cuando su telegraph termina.
        for sat in self._satelites:
            sat.reanclar(pygame.Vector2(self.rect.center))
            sat.update(dt)
        self._satelites = [a for a in self._satelites if a.alive]
        for esp in self._espejos:
            antes = esp.is_telegraphing
            esp.update(dt)
            if antes and not esp.is_telegraphing and not esp.disparo:
                esp.disparo = True
                jugador = self._player_ref
                hacia = (1 if jugador is not None
                         and jugador.centerx >= esp.pos.x else -1)
                suelo = self._anchor.y + FORM_SIZES[FORM_STONE][1]
                self._olas.append(SpiritWave(
                    pygame.Vector2(esp.pos.x, suelo), hacia, suelo_y=suelo))
        self._espejos = [a for a in self._espejos if a.alive]
        for haz in self._haces:
            haz.update(dt)
        self._haces = [a for a in self._haces if a.alive]

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

    # ── FORMA 2 — La Máscara Espectral ──────────────────────────
    def _attack_spirit_wave(self) -> None:
        """Una ola rasante hacia el jugador. Se salta.

        Sale del suelo bajo la máscara, no de la máscara: la máscara flota, y
        una ola que naciera en el aire para correr por el piso no se
        entendería. El ancla (`_anchor`) es el suelo del círculo.
        """
        player = self._player_ref
        if player is None:
            return
        self._face_player()
        origen = pygame.Vector2(self.rect.centerx, self._anchor.y + 64)
        hacia = 1 if player.centerx >= self.rect.centerx else -1
        self._olas.append(
            SpiritWave(origen, hacia, suelo_y=self._anchor.y + 64))
        self._event_bus.emit(
            Events.SFX_BOSSES_PABURU_WAVE, pos=(origen.x, origen.y))

    def _attack_mask_pulse(self) -> None:
        """Onda radial desde la máscara. Castiga quedarse pegado a ella.

        Existe por el punto débil: la máscara da x2.5 de daño y eso invita a
        vivir debajo del jefe. Sin un ataque que cobre la cercanía, el punto
        débil sería un regalo en vez de una decisión.
        """
        centro = pygame.Vector2(self.rect.center)
        self._pulsos.append(MaskPulse(centro))
        self._event_bus.emit(
            Events.SFX_BOSS_PHASE_CHANGE, pos=(centro.x, centro.y))

    def _attack_duelo_de_ecos(self) -> None:
        """Tres ecos escalonados. Se paran.

        Escalonados y no simultáneos: tres a la vez sólo se pueden esquivar,
        y este ataque existe para que se paren. Con 0.35 s entre uno y otro el
        jugador puede parar el primero, comerse el segundo y volver a parar el
        tercero — que es una conversación, no un examen.
        """
        player = self._player_ref
        if player is None:
            return
        self._face_player()
        origen = pygame.Vector2(self.rect.centerx, self.rect.centery)
        destino = pygame.Vector2(player.centerx, player.centery)
        for i in range(3):
            self._ecos.append(Eco(origen, destino, retraso=i * 0.35))
        self._event_bus.emit(
            Events.SFX_BOSSES_PABURU_EYE_BEAM, pos=(origen.x, origen.y))

    # ── FORMA 3 — La Reliquia (3A/3B) ───────────────────────────
    def _attack_embestida_triple(self) -> None:
        """3A. La orden de la triple embestida. El motor hace el resto.

        Si el motor está a mitad de otra cosa (agotada, embistiendo), la
        orden no vale y el turno se reintenta pronto: el planificador manda
        CUÁNDO, el motor manda CÓMO.
        """
        motor = self._motor_reliquia
        if not isinstance(motor, MotorPepita) or not motor.ordenar_embestida():
            self._attack_timers["EMBESTIDA_TRIPLE"] = 0.5
            return
        self._event_bus.emit(
            Events.SFX_BOSS_PHASE_CHANGE, pos=(self.rect.centerx, self.rect.centery))

    def _attack_esquirlas_de_oro(self) -> None:
        """3A. Abanico de 4 esquirlas hacia el lado del jugador. Se paran."""
        player = self._player_ref
        motor = self._motor_reliquia
        if player is None or not isinstance(motor, MotorPepita):
            return
        if motor.estado != motor.ACECHO:
            # En plena embestida no se escupe: un solo peligro por vez.
            self._attack_timers["ESQUIRLAS_DE_ORO"] = 0.5
            return
        origen = pygame.Vector2(self.rect.center)
        hacia = pygame.Vector2(player.center) - origen
        base = math.atan2(hacia.y, hacia.x) if hacia.length() > 1 else 0.0
        for i in range(4):
            ang = base + math.radians(-24 + 16 * i)
            vel = pygame.Vector2(math.cos(ang), math.sin(ang)) * 190.0
            vel.y -= 60.0        # un pelo hacia arriba: caen en arco, no en línea
            self._esquirlas.append(EsquirlaDeOro(origen, vel))
        self._event_bus.emit(
            Events.SFX_PROJECTILE_FIRE, pos=(origen.x, origen.y))

    def _attack_orbita_cerrada(self) -> None:
        """3B. La órbita se cierra, se enfurece, y al abrirse queda la ventana."""
        motor = self._motor_reliquia
        if not isinstance(motor, MotorPerla) or not motor.ordenar_cierre():
            self._attack_timers["ORBITA_CERRADA"] = 0.5
            return
        self._event_bus.emit(
            Events.SFX_BOSS_PHASE_CHANGE, pos=(self.rect.centerx, self.rect.centery))

    def _attack_lagrima_negra(self) -> None:
        """3B. Una gota lenta y sinuosa. Devuelta con parry, ABRE a la Perla."""
        player = self._player_ref
        motor = self._motor_reliquia
        if player is None or not isinstance(motor, MotorPerla):
            return
        if motor.estado in (motor.FURIA, motor.ABIERTA):
            self._attack_timers["LAGRIMA_NEGRA"] = 0.5
            return
        origen = pygame.Vector2(self.rect.center)
        self._lagrimas.append(
            LagrimaNegra(origen, pygame.Vector2(player.center)))
        self._event_bus.emit(
            Events.SFX_PROJECTILE_FIRE, pos=(origen.x, origen.y))

    # ── FORMA 4 — El Espíritu del Shamán ────────────────────────
    def _attack_relic_surge(self) -> None:
        """Las DOS reliquias vuelven como satélites del Espíritu.

        La que el sorteo no mostró en la Forma 3 debuta aquí: nadie ve todo
        en una partida, todos lo ven todo en dos. Órbitas de radio y sentido
        distintos para que se lean como dos peligros, no como un anillo.
        """
        centro = pygame.Vector2(self.rect.center)
        self._satelites.append(SateliteReliquia(
            centro, "gold", radio=86.0, omega=2.6, fase=0.0))
        self._satelites.append(SateliteReliquia(
            centro, "black", radio=132.0, omega=-1.7, fase=math.pi))
        self._event_bus.emit(
            Events.SFX_BOSS_PHASE_CHANGE, pos=(centro.x, centro.y))

    def _attack_spirit_form(self) -> None:
        """El gemelo espejo: aparece al otro lado y repite la ola.

        Dos olas convergentes obligan al salto sincronizado — la lección de
        la Forma 2 con el doble de lectura. La ola del gemelo la suelta
        `_advance_projectiles` cuando su telegraph termina.
        """
        arena_r = self.arena_bounds
        if arena_r is None or self._player_ref is None:
            return
        # El espejo nace reflejado respecto del centro de la sala.
        eco_x = arena_r.centerx * 2 - self.rect.centerx
        eco_x = max(arena_r.left + 40, min(arena_r.right - 40, eco_x))
        suelo = self._anchor.y + FORM_SIZES[FORM_STONE][1]
        self._espejos.append(EspejoEspectral(
            pygame.Vector2(eco_x, suelo), FORM_SIZES[FORM_SPIRIT]))
        self._event_bus.emit(
            Events.SFX_BOSSES_PABURU_WAVE, pos=(eco_x, suelo))

    def _attack_ancient_call(self) -> None:
        """El llamado. Levanta a los guardianes caídos y ordena la procesión.

        La coreografía es de la ESCENA (los guardianes son suyos): acá solo
        se emite el evento. Es la misma caracola de la ronda, ahora explícita
        — el jefe llama y los custodios cruzan la sala.
        """
        self._event_bus.emit(
            Events.BOSS_ATTACK, pattern="ANCIENT_CALL", rect=self.rect)
        self._event_bus.emit(Events.SFX_ENVIRONMENT_SCREEN_SHAKE)
        self._sfx("sfx_bosses_paburu_llamado")

    def _attack_convergence(self) -> None:
        """Los cuatro círculos del camposanto disparan a través de la tierra.

        Cuatro haces secuenciales (0.55 s entre uno y otro), uno por círculo
        de arriba, repartidos en los cuartos de la sala: siempre queda
        pasillo. El nivel entero era el arma — visto desde abajo.

        AUD-487 — EL PATRÓN ERA EL MISMO SIEMPRE, ASÍ QUE NO PREGUNTABA NADA.
        --------------------------------------------------------------------
        Los cuatro haces caían en los octavos 1/8, 3/8, 5/8 y 7/8 de la sala,
        invocación tras invocación, partida tras partida. Medido: 48 haces, 0
        impactos. El docstring dice «castiga quedarse quieto» y el ataque
        premiaba exactamente eso: encontrado un pasillo, quedarse en él era
        la respuesta óptima para siempre — no había nada que leer.

        El arreglo mantiene la geometría (cuatro haces, 200 px entre centros,
        pasillos de 144 px libres) y sortea DÓNDE cae la rejilla entera en
        cada invocación. Ahora el jugador tiene que mirar las grietas del
        techo —el telegrafiado de 0,9 s existe justamente para eso— en vez de
        memorizar cuatro coordenadas.

        El desplazamiento se acota a ±`width/8 − 4` y no a ±`width/8` porque
        el contrato del ataque es que los cuatro haces caigan DENTRO de la
        sala: en el extremo exacto el primero (o el último) aterrizaría sobre
        el borde y el pasillo de ese lado dejaría de ser jugable. Con 800 px
        de sala son ±96, casi el periodo completo de la rejilla: cualquier
        posición fija recibe haz en ~40 % de las invocaciones.
        """
        arena_r = self.arena_bounds
        if arena_r is None:
            return
        suelo = self._anchor.y + FORM_SIZES[FORM_STONE][1]
        techo = float(arena_r.top)
        margen = arena_r.width / 8.0 - 4.0
        corrimiento = self._azar.uniform(-margen, margen)
        for i in range(4):
            x = (arena_r.left + arena_r.width * (1 + 2 * i) / 8.0
                 + corrimiento)
            self._haces.append(HazDelCirculo(
                x, techo, suelo, retraso=i * 0.55))
        self._event_bus.emit(
            Events.SFX_BOSSES_PABURU_EYE_BEAM,
            pos=(arena_r.centerx, techo))

    # ── EL OFRECIMIENTO — la ceremonia de muerte ────────────────
    @property
    def ofrecimiento_activo(self) -> bool:
        """Verdadero desde que el Espíritu se alza hasta que termina el
        EPÍLOGO: toda la ceremonia es zona sin rotación y sin ronda."""
        return ((self._ofrecimiento_t is not None
                 or self._epilogo_t is not None) and self.is_alive)

    @property
    def en_epilogo(self) -> bool:
        return self._epilogo_t is not None and self.is_alive

    def _sfx(self, nombre: str, volumen: float = 1.0) -> None:
        """Reproduce un SFX propio si la escena inyectó su reproductor.

        En los arneses de prueba nadie lo inyecta y el silencio es
        correcto: el sonido es presentación, nunca lógica de combate.
        """
        if self.reproducir_sfx is not None:
            self.reproducir_sfx(nombre, volumen)

    def _iniciar_ofrecimiento(self) -> None:
        """A cero de vida, el Espíritu no muere: pregunta.

        Sin fase oculta ni vida sorpresa — la investigación de diseño es
        clara en que eso frustra. Es un cierre ceremonial CORTO: el juez se
        alza invulnerable, la sala se detiene, y ofrece un único juicio
        parable. Se gana siempre; CÓMO se gana es la firma de la pelea.
        """
        self._ofrecimiento_t = 0.0
        self.current_health = 0.01          # en pie, pero ya juzgado
        self._invincibility_timer = float("inf")
        # La sala se despeja: la última pregunta se hace en silencio.
        for grupo in (self._satelites, self._espejos, self._haces,
                      self._olas, self._pulsos, self._ecos):
            grupo.clear()
        self._event_bus.emit(
            Events.SHOW_MESSAGE, text="EL OFRECIMIENTO", duration=3.0)
        self._event_bus.emit(Events.SFX_BOSS_PHASE_CHANGE)

    def _avanzar_ofrecimiento(self, dt: float) -> None:
        if self._ofrecimiento_t is None:
            return
        self._ofrecimiento_t += dt
        # 1.6 s de alzarse en silencio; después, la pregunta.
        if self._juicio is None and self._ofrecimiento_t >= 1.6:
            arena_r = self.arena_bounds or pygame.Rect(0, 0, 800, 560)
            alcance = math.hypot(arena_r.width, arena_r.height) / 2 + 40
            self._juicio = JuicioFinal(
                pygame.Vector2(self.rect.center), alcance)
            # Sonaba al rayo ocular de la Forma 1 — la pregunta FINAL de la
            # pelea con la muestra del primer ataque. Ahora tiene la suya:
            # un sub-grave que baja mientras crece, con un batido encima.
            self._sfx("sfx_bosses_paburu_juicio")
        if self._juicio is not None:
            self._juicio.update(dt)
            if not self._juicio.alive:
                self._concluir_juicio(absuelto=self._juicio.devuelto)

    def _concluir_juicio(self, absuelto: bool) -> None:
        """El veredicto abre el EPÍLOGO — ya no mata en seco.

        La primera versión mataba aquí mismo: muerte genérica del motor y
        banner a los 2,9 s. El final del JUEGO merecía más que eso, y el
        GDD §204 lo pedía explícito: los custodios se despiden. Ahora el
        veredicto abre seis segundos coreografiados (`_avanzar_epilogo`) y
        la muerte real llega al final, cuando ya no queda nadie en el aire.
        """
        self.absuelto = absuelto
        self._juicio = None
        self._ofrecimiento_t = None
        self._epilogo_t = 0.0
        self._event_bus.emit(
            Events.SHOW_MESSAGE,
            text=("EL CAMPOSANTO TE ABSUELVE" if absuelto
                  else "JUZGADO — Y AUN ASI, EN PIE"),
            duration=3.0,
        )
        # El veredicto se OYE distinto según cómo terminó: la absolución
        # es una floración mayor que amanece; el juicio recibido es la
        # campana de piedra del sello — la marca queda grabada.
        self._sfx("sfx_bosses_paburu_absolucion" if absuelto
                  else "sfx_bosses_paburu_sello")

    #: Los tiempos del epílogo, en segundos desde el veredicto.
    EPILOGO_DESPEDIDA = 0.8      # arrancan las reverencias (escalonadas)
    EPILOGO_ASCENSO = 2.6        # el Espíritu empieza a subir
    EPILOGO_DISOLUCION = 4.4     # el cuerpo se vuelve ánimas
    EPILOGO_FIN = 6.2            # la muerte real y el cierre del motor

    def _avanzar_epilogo(self, dt: float) -> None:
        if self._epilogo_t is None or not self.is_alive:
            return
        t_antes = self._epilogo_t
        self._epilogo_t += dt

        # La disolución: el cuerpo estalla en ánimas UNA vez, al cruzar la
        # marca — doce motas que suben con deriva propia, como las del
        # sello pero del propio juez.
        if t_antes < self.EPILOGO_DISOLUCION <= self._epilogo_t:
            self._cuerpo_visible = False
            cx, cy = self.rect.center
            for i in range(12):
                ang = i * math.tau / 12.0
                self._animas_del_adios.append([
                    pygame.Vector2(cx + math.cos(ang) * 10,
                                   cy + math.sin(ang) * 14),
                    pygame.Vector2(math.cos(ang) * 26.0,
                                   -46.0 - (i % 4) * 14.0),
                    0.0,
                ])
            self._event_bus.emit(
                Events.VFX_PARRY, pos=(float(cx), float(cy)))

        for anima in self._animas_del_adios:
            anima[0] += anima[1] * dt
            anima[1].y -= 12.0 * dt          # cada vez más liviana
            anima[2] += dt
        self._animas_del_adios = [a for a in self._animas_del_adios
                                  if a[2] < 2.2]

        if self._epilogo_t >= self.EPILOGO_FIN:
            self._event_bus.emit(
                Events.SHOW_MESSAGE,
                text=("LA MASCARA DESCANSA" if self.absuelto
                      else "EL JUICIO QUEDO GRABADO"),
                duration=3.0,
            )
            self._epilogo_t = None
            self._invincibility_timer = 0.0
            self.current_health = 0.0
            super().apply_hit(1.0, (self.rect.centerx, self.rect.centery))

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
        # Apunta al CENTRO del hurtbox del jugador, no a sus pies ni a su
        # rect: el hurtbox es lo que el rayo tiene que tocar, así que es a
        # lo que hay que apuntar. La dirección queda fijada acá, al empezar
        # el telegraph — el rayo no persigue.
        objetivo = pygame.Vector2(self._player_ref.center)
        self._beams.append(EyeBeam(eye, objetivo, self.facing_direction))
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
        self._event_bus.emit(Events.SFX_ENVIRONMENT_SCREEN_SHAKE)
        self._sfx("sfx_bosses_paburu_sello", volumen=0.7)
        self._event_bus.emit(
            Events.VFX_SLAM, pos=(float(self.rect.centerx), float(arena.FLOOR_Y)),
        )
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="EL_SELLO", rect=self.rect)

    # ── Daño recibido ───────────────────────────────────────────

    def apply_hit(self, damage: float,
                  source_position: tuple[float, float]) -> None:
        """Recibe el golpe resolviendo antes el punto débil.

        POR QUÉ HAY QUE HACER ESTO ACÁ
        El motor trae todo lo necesario —`WeakPoint`, `resolve_weak_point_damage`
        y `BossBase.apply_hit_at(damage, source, hit_rect)`— pero el sistema de
        colisión golpea así (`collision_system.py`, en `process_attack`):

            entity.apply_hit(self._calculate_damage(player, entity),
                             (player.position.x, player.position.y))

        Llama a `apply_hit`, **no** a `apply_hit_at`, así que nunca pasa el
        rect del golpe. Y sin rect no hay forma de saber *dónde* pegó el
        jugador, solo que pegó. El resultado es que un jefe puede declarar
        puntos débiles y no dispararse ninguno: el sistema está completo y es
        inalcanzable desde el juego normal.

        Interceptar acá lo resuelve sin tocar el framework. En el momento de
        esta llamada el `active_hitbox` del jugador **todavía existe** —
        `process_attack` lo consume recién al terminar el bucle—, así que se
        puede leer y comparar contra la máscara.

        GDD §4 para la Forma 2: "Solo la máscara recibe daño". Se implementa
        literal: acertarla multiplica ×2.5, fallarla no hace nada. En las
        otras formas el cuerpo entero recibe daño normal.
        """
        golpe = getattr(self.player_obj, "active_hitbox", None)

        # Forma 3: la reliquia en movimiento es un borrón — daño de roce
        # (x0.25). En su ventana (agotada / abierta) el golpe entra
        # completo. La forma entera pregunta si sabés CUÁNDO pegar, no si
        # podés alcanzarla a base de insistir.
        if (self.current_phase == FORM_RELIC
                and self._motor_reliquia is not None
                and not self._motor_reliquia.ventana_abierta):
            damage *= 0.25

        if self.current_phase == FORM_MASK and golpe is not None:
            zona = self.MASK_WEAK_POINT.rect_for(self.rect)
            if not golpe.colliderect(zona):
                # Le pegó al cuerpo, no a la máscara: la Forma 2 lo ignora.
                self._event_bus.emit(
                    Events.SFX_ENEMY_HIT,
                    pos=(self.position.x, self.position.y), damage=0.0,
                )
                return

        # OJO con `apply_hit_at`: internamente termina llamando a `apply_hit`,
        # así que invocarlo desde acá crea recursión infinita. Se usa
        # directamente la función pura del kit y después se sube al padre.
        # EL OFRECIMIENTO intercepta la muerte del Espíritu: a cero de
        # vida no se muere — se pregunta. Y durante la ceremonia el jefe es
        # de piedra otra vez: la única respuesta válida es al juicio.
        if self.current_phase == FORM_SPIRIT and self.is_alive:
            if self.ofrecimiento_activo:
                return
            if self.current_health - damage <= 0.0 and self._ofrecimiento_t is None:
                self._iniciar_ofrecimiento()
                return

        final = damage
        self.last_weak_point = None
        if golpe is not None and self.weak_points:
            final, punto = resolve_weak_point_damage(
                self, golpe, damage, self.weak_points, self.current_phase,
            )
            self.last_weak_point = punto
            if punto is not None:
                # Confirmación al jugador de que acertó AHÍ. Sin ella, un
                # punto débil es indistinguible de un golpe normal y nunca
                # se aprende que existe.
                self._event_bus.emit(
                    Events.VFX_PARRY,
                    pos=(self.position.x, self.position.y),
                )

        super().apply_hit(final, source_position)

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
        # ── Forma 2 ────────────────────────────────────────────
        # Cada uno pregunta por su propia geometría: la ola por su rect
        # rasante, el pulso por la distancia al borde del anillo, el eco por
        # su círculo. Usar el rect para los tres daría golpes fantasma —el
        # cuadrado de un anillo de 190 px de radio cubre media arena—.
        for ola in self._olas:
            if ola.devuelta or getattr(ola, "_ya_golpeo", False):
                continue
            r = ola.rect
            if r is not None and r.colliderect(target):
                ola._ya_golpeo = True
                player.apply_damage(ola.DANIO, r.center)

        for pulso in self._pulsos:
            if getattr(pulso, "_ya_golpeo", False):
                continue
            if pulso.toca(target):
                pulso._ya_golpeo = True
                player.apply_damage(pulso.DANIO, (pulso.centro.x, pulso.centro.y))

        for eco in self._ecos:
            if eco.devuelta or getattr(eco, "_ya_golpeo", False):
                continue
            r = eco.rect
            if r is not None and r.colliderect(target):
                eco._ya_golpeo = True
                eco.alive = False       # el eco se gasta al pegar
                player.apply_damage(eco.DANIO, r.center)

        # ── Forma 4 ────────────────────────────────────────────
        for sat in self._satelites:
            if getattr(sat, "ya_golpeo", False):
                continue
            r = sat.rect
            if r is not None and r.colliderect(target):
                sat.ya_golpeo = True
                player.apply_damage(sat.DANIO, r.center)

        for haz in self._haces:
            if getattr(haz, "ya_golpeo", False):
                continue
            r = haz.rect
            if r is not None and r.colliderect(target):
                haz.ya_golpeo = True
                player.apply_damage(haz.DANIO, (haz.x, target.centery))

        # AUD-489 — LA VENTANA DE PARRY DEL JUICIO DURABA 0,067 s, NO 0,2 s.
        #
        # `_check_player_contact` corre desde `update()` del jefe y
        # `_revisar_parry` desde la escena, DESPUÉS. En cuanto el frente del
        # anillo entra en el hurtbox, esta rama lo marca `ya_golpeo` y lo
        # apaga (`alive = False`), así que cuando el parry de la escena mira
        # ya no hay juicio que parar. De los 0,2 s de ventana declarados sólo
        # servían los ~4 fotogramas en que el anillo estaba dentro de la zona
        # inflada del parry pero todavía no tocaba el cuerpo: 0,067 s medidos.
        # La firma de la pelea entera —la absolución— dependía de acertar una
        # ventana tres veces más corta que la que el juego enseña.
        #
        # Con la ventana abierta, el juicio NO se consume: se le deja llegar
        # al chequeo de parry de este mismo fotograma. Si la parada no era
        # buena (fuera de alcance, tarde), el anillo sigue vivo y el
        # fotograma siguiente lo cobra igual — no se regala inmunidad, se
        # respeta el orden de las dos comprobaciones.
        if (self._juicio is not None and not self._juicio.ya_golpeo
                and self._juicio.toca(target)
                and float(getattr(player, "_parry_window", 0.0)) <= 0.0):
            self._juicio.ya_golpeo = True
            self._juicio.alive = False      # pregunta hecha: se disipa
            # AUD-484 — el juicio marca, no mata: ver `JuicioFinal.VIDA_MINIMA`.
            player.apply_damage(self._juicio.danio_contra(player),
                                self.rect.center)

        # ── Forma 3 ────────────────────────────────────────────
        for e in (*self._esquirlas, *self._lagrimas):
            if e.devuelta or getattr(e, "_ya_golpeo", False):
                continue
            r = e.rect
            if r is not None and r.colliderect(target):
                e._ya_golpeo = True
                e.alive = False
                player.apply_damage(e.DANIO, r.center)

        for b in self._beams:
            if b.devuelto or getattr(b, "_ya_golpeo", False):
                continue
            # `hits()` y no `rect`: la envolvente de un rayo en diagonal
            # abarca zonas por las que el rayo no pasa, y daría golpes
            # fantasma a media pantalla del trazo real.
            if b.hits(target):
                b._ya_golpeo = True
                player.apply_damage(b.DAMAGE, self.rect.center)

        for p in self._projectiles:
            if p.devuelta:
                continue          # ya no es de Paburu: es del jugador
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

        if self._cuerpo_visible:
            self._draw_body(surface, camera_offset)
        # Las ánimas del adiós: las motas en que el Espíritu se disuelve.
        for pos, _vel, edad in self._animas_del_adios:
            a = max(0.0, 1.0 - edad / 2.2)
            r = max(1, int(4 * a))
            sx = int(pos.x - camera_offset.x)
            sy = int(pos.y - camera_offset.y)
            pygame.draw.circle(surface, (220, 255, 240), (sx, sy), r)
            pygame.draw.circle(surface, (150, 255, 210), (sx, sy), r + 2, 1)

        for a in self._animas:
            a.draw(surface, camera_offset)
        for p in self._projectiles:
            p.draw(surface, camera_offset)
        for b in self._beams:
            b.draw(surface, camera_offset)
        # Forma 2. Van DESPUÉS de piedras y rayos porque en la práctica nunca
        # coinciden —son de formas distintas— y así el orden de dibujo sigue
        # el orden de la pelea, que es más fácil de seguir al leer.
        for grupo in (self._olas, self._pulsos, self._ecos):
            for a in grupo:
                a.draw(surface, camera_offset)
        # Forma 3: primero el motor (estelas, líneas de mira, órbita — van
        # detrás del cuerpo), después sus proyectiles.
        if self.current_phase == FORM_RELIC and self._motor_reliquia is not None:
            self._motor_reliquia.draw(surface, camera_offset, self.rect)
        for grupo in (self._esquirlas, self._lagrimas):
            for a in grupo:
                a.draw(surface, camera_offset)
        # Forma 4: espejo y haces detrás del cuerpo ya quedaron arriba en
        # z-order de lectura; satélites y juicio, delante de todo.
        for grupo in (self._espejos, self._haces, self._satelites):
            for a in grupo:
                a.draw(surface, camera_offset)
        if self._juicio is not None:
            self._juicio.draw(surface, camera_offset)

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
