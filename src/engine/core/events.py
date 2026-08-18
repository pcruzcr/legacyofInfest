"""
Module: events
System: engine.core
Academic Unit: N/A
Description: Centralized declaration of all EventBus event names.
Using string constants instead of raw literals prevents typos and makes
it easy to discover all events in the system.

OBSERVER PATTERN (Fase 5): EventBus is the sole notification mechanism.
These constants are the contract between emitters and subscribers.
"""
from __future__ import annotations


class Events:
    """Canonical event names used across the codebase.
    Every event is defined here — never use raw strings for emit/subscribe."""

    # ── Player lifecycle ──────────────────────────────────────────
    PLAYER_DAMAGED: str = "PLAYER_DAMAGED"
    """Emitted by Player.apply_damage(). Payload: amount, source."""
    PLAYER_HEALED: str = "PLAYER_HEALED"
    """Reserved — not yet emitted. Payload: amount."""
    PLAYER_DIED: str = "PLAYER_DIED"
    """Emitted by Player.apply_damage() or StageScene._kill_player()."""

    # ── Enemy lifecycle ───────────────────────────────────────────
    ENEMY_DIED: str = "ENEMY_DIED"
    """Emitted by EnemyBase._die(). Payload: entity_id, position."""
    BOSS_PHASE_CHANGED: str = "BOSS_PHASE_CHANGED"
    """Emitted by BossBase._finish_phase_transition(). Payload: boss_name, phase, ..."""
    BOSS_ATTACK: str = "BOSS_ATTACK"
    """Emitted by BossVenado._do_stomp(). Payload: pattern, rect."""

    # ── UI / messaging ────────────────────────────────────────────
    SHOW_MESSAGE: str = "SHOW_MESSAGE"
    """Emitted by StageScene on trigger overlap. Payload: text, duration."""
    HIDE_MESSAGE: str = "HIDE_MESSAGE"
    """Emitted by MessageBox.hide(). Payload: none."""

    # ── Stage / progression ───────────────────────────────────────
    CHECKPOINT_REACHED: str = "CHECKPOINT_REACHED"
    """Emitted by Checkpoint.activate(). Payload: checkpoint_id."""
    STAGE_COMPLETE: str = "STAGE_COMPLETE"
    """Emitted by StageScene (next trigger) or BossVenado.on_defeated(). Payload: stage_id."""

    # ── SFX events (emitted by entities, played by StageScene) ────
    SFX_PLAYER_JUMP: str = "SFX_PLAYER_JUMP"
    SFX_PLAYER_LAND: str = "SFX_PLAYER_LAND"
    SFX_PLAYER_FOOTSTEP: str = "SFX_PLAYER_FOOTSTEP"
    SFX_PLAYER_FOOTSTEP_MUSGO: str = "SFX_PLAYER_FOOTSTEP_MUSGO"
    """AUD-522 — pisada distinta al andar sobre musgo (`material="musgo"`
    en una `FrictionZone`): el musgo resbala y hasta ahora no se oía ni se
    veía, sólo se calculaba."""
    SFX_MENU_HOVER: str = "SFX_MENU_HOVER"
    SFX_MENU_CONFIRM: str = "SFX_MENU_CONFIRM"
    SFX_MENU_CANCEL: str = "SFX_MENU_CANCEL"
    MUSIC_STINGER: str = "MUSIC_STINGER"

    # ── VFX events (emitted by entities, consumed by StageScene) ─
    VFX_PARRY: str = "VFX_PARRY"
    """Emitted by ParryState. Payload: pos."""
    VFX_CHARGE: str = "VFX_CHARGE"
    """Emitted by ChargingState. Payload: pos, level."""
    VFX_SLAM: str = "VFX_SLAM"
    """Emitted on slam attack. Payload: pos."""
    VFX_ULTIMATE: str = "VFX_ULTIMATE"
    """Emitted on ultimate attack. Payload: pos."""
    VFX_BUBBLE: str = "VFX_BUBBLE"
    """Emitted by SwimmingState. Payload: pos."""
    VFX_MUSGO_STEP: str = "VFX_MUSGO_STEP"
    """AUD-522 — emitted by WalkingState while on `material="musgo"`.
    Payload: pos."""
    SFX_PLAYER_SHORT_ATTACK: str = "SFX_PLAYER_SHORT_ATTACK"
    SFX_PLAYER_LONG_ATTACK: str = "SFX_PLAYER_LONG_ATTACK"
    SFX_PLAYER_HURT: str = "SFX_PLAYER_HURT"
    SFX_PLAYER_DIE: str = "SFX_PLAYER_DIE"
    SFX_HIT_CONNECT: str = "SFX_HIT_CONNECT"
    SFX_ENEMY_HIT: str = "SFX_ENEMY_HIT"
    SFX_ENEMY_DIE_SMALL: str = "SFX_ENEMY_DIE_SMALL"
    SFX_ENEMY_DIE_LARGE: str = "SFX_ENEMY_DIE_LARGE"
    SFX_PROJECTILE_FIRE: str = "SFX_PROJECTILE_FIRE"
    SFX_CHECKPOINT: str = "SFX_CHECKPOINT"
    SFX_STAGE_BANNER: str = "SFX_STAGE_BANNER"
    SFX_STAGE_COMPLETE: str = "SFX_STAGE_COMPLETE"
    SFX_HAZARD_ZONE: str = "SFX_HAZARD_ZONE"
    #: AUD-443 — la risa de Paburu al confirmar el personaje.
    #:
    #: Es un evento y no una llamada directa al audio por lo mismo que el
    #: resto de los SFX de menú (AUD-345): quien decide *cuándo* suena es la
    #: pantalla, y quién lo reproduce es cosa del motor. Así la pantalla no
    #: necesita conocer el gestor de audio ni la ruta del fichero.
    SFX_VOZ_PABURU: str = "SFX_VOZ_PABURU"
    SFX_PLAYER_PARRY: str = "SFX_PLAYER_PARRY"
    SFX_PLAYER_CROUCH: str = "SFX_PLAYER_CROUCH"
    SFX_PLAYER_HEAL: str = "SFX_PLAYER_HEAL"
    SFX_BOSS_HIT: str = "SFX_BOSS_HIT"
    SFX_UI_GAME_OVER: str = "SFX_UI_GAME_OVER"
    SFX_ENVIRONMENT_SCREEN_SHAKE: str = "SFX_ENVIRONMENT_SCREEN_SHAKE"
    SFX_ENVIRONMENT_ONE_WAY_PLATFORM: str = "SFX_ENVIRONMENT_ONE_WAY_PLATFORM"
    SFX_BOSS_PHASE_CHANGE: str = "SFX_BOSS_PHASE_CHANGE"
    SFX_ENEMIES_PROJECTILE_HIT_WALL: str = "SFX_ENEMIES_PROJECTILE_HIT_WALL"
    #: AUD-529 — «se oye antes de verse»: el pez abismal emite este creado
    #: bajo justo al aparecer (fuera de cámara, GAP-065), un segundo o dos
    #: antes de que la silueta entre en cuadro nadando.
    SFX_ENEMIES_PEZ_ABISMAL_ACERCARSE: str = "SFX_ENEMIES_PEZ_ABISMAL_ACERCARSE"
    SFX_BOSSES_GAVILAN_DIVE: str = "SFX_BOSSES_GAVILAN_DIVE"
    SFX_BOSSES_GAVILAN_MASK_BEAM: str = "SFX_BOSSES_GAVILAN_MASK_BEAM"
    SFX_BOSSES_PABURU_EYE_BEAM: str = "SFX_BOSSES_PABURU_EYE_BEAM"
    SFX_BOSSES_PABURU_WAVE: str = "SFX_BOSSES_PABURU_WAVE"
    SFX_BOSSES_RELIC_APPEAR: str = "SFX_BOSSES_RELIC_APPEAR"
    SFX_BOSSES_REY_SPIT: str = "SFX_BOSSES_REY_SPIT"
    SFX_BOSSES_REY_SPLIT: str = "SFX_BOSSES_REY_SPLIT"
    SFX_BOSSES_VENADO_CHARGE: str = "SFX_BOSSES_VENADO_CHARGE"
    SFX_BOSSES_VENADO_STOMP: str = "SFX_BOSSES_VENADO_STOMP"
    SFX_BOSSES_VENADO_VINE: str = "SFX_BOSSES_VENADO_VINE"

    # ── Achievement events ─────────────────────────────────────────
    ACHIEVEMENT_UNLOCKED: str = "ACHIEVEMENT_UNLOCKED"
    """Emitted when an achievement is unlocked. Payload: achievement_id, name."""
    ACHIEVEMENT_PROGRESS: str = "ACHIEVEMENT_PROGRESS"
    """Emitted on progress toward achievement. Payload: achievement_id, progress, target."""

    # ── Dialogue events ─────────────────────────────────────────
    SHOW_DIALOGUE: str = "SHOW_DIALOGUE"
    """Pide abrir un árbol de diálogo. Carga: tree_id.

    AUD-244 — el eslabón que faltaba entre el mapa y el sistema de diálogo.
    `StageLoader` lee `dialogue_tree_id` de los `MessageTrigger` de **los
    diecisiete mapas**, pero el único sitio que consumía esos disparadores
    —`HazardSystem`— sólo emitía `SHOW_MESSAGE` con el texto plano. Un mapa que
    declarara una conversación no obtenía nada, sin aviso: la misma forma de
    fallo que AUD-127, un nivel más arriba.

    Va por evento y no por llamada directa porque `HazardSystem` sólo tiene el
    bus: quien sabe de árboles es la escena, que es la que los carga.
    """
    ITEM_COLLECTED: str = "ITEM_COLLECTED"
    """Emitted by DialogueSystem on dialogue action. Payload: item_id."""
    FLAG_SET: str = "FLAG_SET"
    """Emitted by DialogueSystem on dialogue action. Payload: flag."""
    DIALOGUE_FINISHED: str = "DIALOGUE_FINISHED"
    """Emitido al cerrarse un árbol de diálogo. Carga: tree_id.

    AUD-127 — antes el diálogo terminaba en silencio, así que nada podía
    reaccionar a una conversación acabada: ni abrir una puerta, ni encadenar
    una cutscene, ni marcar un objetivo. Una conversación que no deja rastro
    en el juego es una pantalla de texto, no una mecánica.
    """

    # ── Objetivos (AUD-400, GAP-047) ────────────────────────────────
    OBJECTIVE_REQUESTED: str = "OBJECTIVE_REQUESTED"
    """Alguien pide dar por cumplido un objetivo. Carga: objective_id.

    Lo emite `complete_objective:` desde un árbol de diálogo. Es la **entrada**
    del sistema de objetivos, al revés que los dos de abajo, que son su salida:
    hay cosas que no se pueden contar con los eventos del juego —«habla con el
    vigía», donde a veces sólo cuenta una rama concreta de la conversación— y
    esto es cómo se dan por hechas sin fingir un recuento.
    """
    OBJECTIVE_COMPLETED: str = "OBJECTIVE_COMPLETED"
    """Un objetivo del mapa se ha cumplido. Carga: objective_id, text.

    Es lo que permite que el HUD lo tache y que suene algo sin que el sistema
    de objetivos sepa que existen un HUD y un mezclador.
    """
    OBJECTIVES_COMPLETED: str = "OBJECTIVES_COMPLETED"
    """Están hechos todos los objetivos **obligatorios** del escenario.

    Los opcionales no cuentan: si contaran, cada coleccionable del mapa
    bloquearía este aviso y con él lo que dependa de él. Se emite **una sola
    vez** por escenario — sin ese pestillo, cada objetivo opcional cumplido
    después volvería a anunciar el final.
    """

    # ── Save / persist ──────────────────────────────────────────────
    SAVE_REQUESTED: str = "SAVE_REQUESTED"
    """Emitted when a save should be persisted. Payload: stage_id, stage_index,
    checkpoint_x, checkpoint_y, health, max_health."""
