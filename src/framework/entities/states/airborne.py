from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core.events import Events
from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot
from src.framework.entities.states.helpers import (
    _can_dash,
    _handle_aerial_attack_input,
    _handle_grounded_jump_input,
    _handle_ultimate_input,
    _handle_wall_jump,
    _tiene_habilidad,
)

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player


class AirborneState(PlayerStateBase):
    def _airborne_update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        if _handle_ultimate_input(player, inp):
            return

        if inp.move_x != 0:
            player.facing_direction = inp.move_x

        if inp.dash_pressed and _can_dash(player, inp):
            from src.framework.entities.states import DashingState
            player._change_state_instance(DashingState())
            return

        # AUD-619 — el pisotón aéreo: abajo mantenido + ataque corto en el
        # aire. Va ANTES del ataque aéreo porque ambos leen `short_attack`,
        # y sin abajo el ataque corto aéreo de siempre sigue intacto. La
        # habilidad se consulta como el dash y el doble salto (AUD-238): es
        # progresión, no un adorno. En tierra nunca llega aquí — esto es
        # `AirborneState` —, así que el ataque agachado de suelo no cambia.
        if (inp.crouch_held and inp.short_attack
                and _tiene_habilidad("skill_ground_pound", player)):
            from src.framework.entities.states import GroundPoundState
            player._change_state_instance(GroundPoundState())
            return

        if _handle_aerial_attack_input(player, inp):
            return

        if _handle_wall_jump(player, inp):
            return

        # AUD-503 — el coyote se gasta AQUÍ o no se gasta nunca. `_can_jump`
        # ya autorizaba la ventana de gracia (`_coyote_counter <
        # perfil.coyote_frames`) desde que existe, pero `_handle_grounded_jump_input`
        # —el único método que la consulta— sólo lo llamaban los estados de
        # SUELO (`grounded.py`), donde ya se está pisando algo. El único
        # motivo por el que el coyote parecía funcionar un fotograma es que
        # `IdleState`/`WalkingState` siguen activos el fotograma exacto en
        # que se pierde el suelo (la transición a `FallingState` va al final
        # de su propio `update`); del segundo fotograma en adelante manda
        # `AirborneState`, que nunca preguntaba. Va antes de reescribir
        # `velocity.x` para que nada pise el impulso recién puesto, y
        # `_do_jump` ya distingue un salto de coyote de uno aéreo por sí
        # solo (`was_truly_airborne`), así que esto no toca el salto aéreo.
        #
        # AUD-618 (GAP-024) — aquí había una guardia más:
        #
        #     if (inp.jump_pressed
        #             and player._coyote_counter < perfil.coyote_frames
        #             and _handle_grounded_jump_input(...)):
        #
        # Esa condición extra hacía que la pulsación de salto en el aire
        # sólo se atendiera DENTRO de la ventana de coyote. Pasada ella,
        # `jump_pressed` caía al vacío aunque `_can_jump` tuviera su rama
        # aérea completa (saltos restantes + habilidad concedida): el doble
        # salto estaba escrito, probado por su nombre, e inalcanzable — el
        # mismo modo de fallo del nado (AUD-573) o del AIR_CHASE (AUD-109).
        # Sin la guardia, `_can_jump` decide sola los dos casos: dentro del
        # coyote devuelve el salto normal sin gastar nada, fuera exige la
        # habilidad y consume un salto aéreo (`_do_jump.was_truly_airborne`).
        if inp.jump_pressed and _handle_grounded_jump_input(player, inp):
            return

        # AUD-373 — aquí se armaba el buffer del salto a mano:
        #
        #     if inp.jump_pressed:
        #         player._pending_jump = True
        #         player._pending_jump_timer = 8.0 / 60.0
        #
        # Ya no hace falta. `InputManager` sella cada pulsación al recibirla,
        # así que la de saltar sigue estando disponible unos fotogramas sin que
        # ningún estado tenga que acordarse de guardarla — que es justo lo que
        # ninguno hacía para el dash ni para el ataque (GAP-040).

        if inp.move_x != 0:
            player.velocity.x = float(inp.move_x) * player.walk_speed * 0.5

        if player._wall_side != 0 and player.velocity.y > 0 and inp.move_x == player._wall_side:
            from src.framework.entities.states import WallSlideState
            player._change_state_instance(WallSlideState())
            return

        if player.is_grounded:
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            return

        if player.velocity.y >= 0 and self.state_enum.value == "JUMPING":
            from src.framework.entities.states import FallingState
            player._change_state_instance(FallingState())
            return

        if player.velocity.y < 0 and self.state_enum.value == "FALLING":
            from src.framework.entities.states import JumpingState
            player._change_state_instance(JumpingState())
            return

        if not inp.jump_held and player.velocity.y < 0 and not player._jump_cut_applied:
            player.velocity.y *= 0.5 ** (dt * 60.0)
            player._jump_cut_applied = True


class JumpingState(AirborneState):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.JUMPING)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._airborne_update(player, dt, input_manager)


class FallingState(AirborneState):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.FALLING)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._airborne_update(player, dt, input_manager)


class AirChaseState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.AIR_CHASE)

    def enter(self, player: Player) -> None:
        super().enter(player)
        player.velocity.x = float(player.facing_direction) * 120.0
        player.velocity.y = -200.0
        player._combo_air_hits = getattr(player, "_combo_air_hits", 0) + 1

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        if inp.short_attack or inp.long_attack:
            from src.framework.entities.states import AerialAttackState, AerialSlamState
            target = AerialSlamState if player._combo_air_hits >= 2 else AerialAttackState
            player._change_state_instance(target())
            return

        if player.is_grounded:
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            return

        if inp.move_x != 0:
            player.facing_direction = inp.move_x
            player.velocity.x = float(inp.move_x) * 100.0

        if player.velocity.y >= 0:
            from src.framework.entities.states import FallingState
            player._change_state_instance(FallingState())


class AerialAttackState(PlayerStateBase):
    def __init__(self, short: bool = True) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.AERIAL_ATTACK)
        self._short = short
        self._timer: float = 0.0
        self._frames: int = 6 if short else 10
        self._has_hit: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        if player.velocity.y < 50:
            player.velocity.y = 80.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt
        frame_duration = 1.0 / 18.0
        current_frame = int(self._timer / frame_duration) + 1

        active = [2, 3, 4] if self._short else [4, 5, 6, 7]
        if current_frame in active and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = (36, 24) if self._short else (40, 28)
            offset_x = 6 if self._short else 10
            hx = cx + (offset_x * player.facing_direction) - (w // 2)
            hy = cy + 4 - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        if player._hitbox_consumed and not self._has_hit:
            self._has_hit = True
            if not player.is_grounded:
                # AUD-109 — el primer golpe aéreo **lanza**; el segundo remata.
                #
                # `AirChaseState` estaba escrito entero —sprite propio
                # (`player_jump.png`), velocidad de animación propia (12.0),
                # valor en el enum `PlayerState.AIR_CHASE`, y una lógica que
                # impulsa al jugador hacia arriba y adelante para seguir al
                # enemigo levantado— y **no había una sola transición que
                # entrara en él**. Comprobado por análisis del árbol de
                # sintaxis sobre todo `src/`: cero.
                #
                # Es el quinto sistema de esta forma en un mes: la iluminación
                # que no iluminaba, las trece demos en una esquina, el ultimate
                # cuyo medidor nadie subía, el nado inalcanzable, y esto.
                #
                # La forma del código decía para qué era: `enter()` pone
                # `velocity.y = -200` y suma un golpe al combo, y este bloque ya
                # mandaba al remate a partir del segundo. Faltaba el primero.
                if player._combo_air_hits == 0:
                    from src.framework.entities.states import AirChaseState
                    player._change_state_instance(AirChaseState())
                    return
                player._combo_air_hits += 1
                if player._combo_air_hits >= 2:
                    from src.framework.entities.states import AerialSlamState
                    player._change_state_instance(AerialSlamState())
                    return

        if player.is_grounded and self._timer > 0.05:
            player._active_hitbox = None
            if self._timer > 0.2:
                from src.framework.entities.states import IdleState
                player._change_state_instance(IdleState())

        if current_frame >= self._frames:
            player._active_hitbox = None
            from src.framework.entities.states import FallingState, IdleState
            target = IdleState if player.is_grounded else FallingState
            player._change_state_instance(target())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


#: AUD-619 — velocidad vertical FIJA del pisotón, en px/s.
#:
#: Por encima de la caída normal que el jugador suele llevar (el tope del
#: perfil es 500) pero por debajo de ella como constante: fijar la velocidad
#: y no acelerar es lo que hace la caída legible como compromiso — el
#: jugador soltó el control a cambio de un impacto con área. Que no dependa
#: de desde qué altura se activó es lo mismo que `Resorte.impulso` impone
#: en vez de sumar (AUD-131): la altura deja de ser una variable.
_PISOTON_CAIDA: float = 420.0
#: La onda de aterrizaje: ancho total y vida, en px y s. El ancho cubre a
#: ambos lados del cuerpo con margen — un pisotón que sólo daña debajo es
#: un ataque corto agachado caro.
_ONDA_ANCHO: float = 72.0
_ONDA_ALTO: float = 16.0
_ONDA_DURACION: float = 0.12
#: Multiplicador durante la onda. Un pisotón que pega lo mismo que un
#: ataque corto no justifica perder el control aéreo.
_ONDA_DANO_MULT: float = 1.5


class GroundPoundState(PlayerStateBase):
    """AUD-619 — el pisotón aéreo: abajo + ataque corto en el aire.

    Tres fases en una sola máquina mínima:

    1. **Caída** — momentum horizontal anulado al entrar y velocidad
       vertical fija hasta tocar suelo. Es la mitad "compromiso" del
       movimiento: mientras dura, el jugador no dirige.
    2. **Onda** — al aterrizar, una caja de golpe ancha y baja a AMBOS
       lados durante `_ONDA_DURACION`, más un `VFX_SLAM` para el polvo y
       el temblor. La caja pasa por el pipeline de combate existente
       (`_active_hitbox` → `CollisionSystem`), así que el daño, el
       knockback y el hit-stop salen gratis.
    3. **Reposo** — la onda expira y el jugador queda en pie.

    No sustituye a `AerialSlamState`: aquél es el remate de combo aéreo
    con pogo; éste es una herramienta deliberada de posicionamiento y de
    daño de área accesible desde cualquier caída.
    """

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.GROUND_POUND)
        self._aterrizo: bool = False
        self._onda_restante: float = 0.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        # Cancelar el momentum horizontal ES el pisotón: conservarlo lo
        # convierte en un ataque diagonal y deja de leerse.
        player.velocity.x = 0.0
        player.velocity.y = _PISOTON_CAIDA
        self._aterrizo = False
        self._onda_restante = 0.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        if not self._aterrizo:
            player.velocity.x = 0.0
            player.velocity.y = _PISOTON_CAIDA
            if player.is_grounded:
                self._aterrizo = True
                self._onda_restante = _ONDA_DURACION
                player._event_bus.emit(
                    Events.VFX_SLAM,
                    pos=(player.position.x, player.position.y),
                )
            return

        # Fase de onda: caja viva mientras dure, luego reposo.
        self._onda_restante -= dt
        if self._onda_restante > 0.0:
            pies = player.rect.bottom
            centro_x = player.rect.centerx
            player._active_hitbox = pygame.Rect(
                int(centro_x - _ONDA_ANCHO / 2),
                int(pies - _ONDA_ALTO),
                int(_ONDA_ANCHO),
                int(_ONDA_ALTO),
            )
            player._damage_mult = _ONDA_DANO_MULT
            return

        player._active_hitbox = None
        player._damage_mult = 1.0
        from src.framework.entities.states import IdleState
        player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


#: Velocidad vertical que devuelve el pogo al acertar (AUD-134).
#:
#: Menor que el salto (-380) a propósito: el pogo **no** debe ser una forma
#: mejor de ganar altura que saltar, o el jugador deja de saltar. Basta con que
#: dé tiempo a alinearse con el siguiente enemigo.
POGO_IMPULSO: float = -300.0


class AerialSlamState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.AERIAL_SLAM)
        self._timer: float = 0.0
        self._has_hit: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        player.velocity.x = 0.0
        player.velocity.y = 300.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt

        if self._timer < 0.12 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 44, 32
            hx = cx + (8 * player.facing_direction) - (w // 2)
            hy = cy + 6 - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        # AUD-134 — el pogo: acertar en el aire devuelve impulso.
        #
        # El estado ya existía y ya tenía caja de golpe; lo que faltaba era
        # que **acertar significara algo**. Sin esto, el ataque aéreo hacia
        # abajo es un ataque normal con animación distinta: se cae igual
        # tanto si conecta como si no.
        #
        # Con el rebote, el jugador que encadena golpes sobre enemigos se
        # mantiene en el aire, y eso convierte una fila de enemigos en un
        # camino. Es la mecánica entera de Ducktales, Shovel Knight y Hollow
        # Knight, y sale de una condición.
        #
        # `_hitbox_consumed` es la señal correcta porque lo pone
        # `Player._on_hit_landed`, que es donde se sabe que el golpe
        # **acertó** — no donde se lanzó. Premiar el lanzamiento enseñaría a
        # dar palos al aire.
        if player._hitbox_consumed and not self._has_hit:
            self._has_hit = True
            player.velocity.y = POGO_IMPULSO
            player._combo_air_hits += 1
            # Recuperar el dash al rebotar es lo que hace la cadena posible:
            # sin ello, el segundo enemigo de la fila queda fuera de alcance.
            player._air_dash_count = 0
            player._event_bus.emit(
                Events.VFX_SLAM, pos=(player.position.x, player.position.y))
            from src.framework.entities.states import FallingState
            player._change_state_instance(FallingState())
            return

        player.velocity.y = 300.0

        if player.is_grounded:
            player._active_hitbox = None
            player._combo_air_hits = 0
            player._event_bus.emit(Events.VFX_SLAM, pos=(player.position.x, player.position.y))
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            return

        if self._timer >= 0.3:
            player._active_hitbox = None
            from src.framework.entities.states import FallingState
            player._change_state_instance(FallingState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None
