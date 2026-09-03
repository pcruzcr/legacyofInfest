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

    # ── Secrets ───────────────────────────────────────────────────
    SECRET_FOUND: str = "SECRET_FOUND"
    """Emitted when a secret is discovered. Payload: secret_id, secret_type (exit/room)."""

    # ── SFX events (emitted by entities, played by StageScene) ────
    SFX_PLAYER_JUMP: str = "SFX_PLAYER_JUMP"
    SFX_PLAYER_LAND: str = "SFX_PLAYER_LAND"
    SFX_PLAYER_FOOTSTEP: str = "SFX_PLAYER_FOOTSTEP"
    SFX_PLAYER_FOOTSTEP_MUSGO: str = "SFX_PLAYER_FOOTSTEP_MUSGO"
    #: AUD-551 — GAP-070 punto 1: el lodo (`ZonaDeFriccion.material="lodo"`,
    #: declarado en Fase 2 del 4-1 desde AUD-522) frenaba de verdad pero
    #: sonaba igual que caminar en tierra firme — sólo el musgo tenía voz
    #: propia.
    SFX_PLAYER_FOOTSTEP_LODO: str = "SFX_PLAYER_FOOTSTEP_LODO"
    """AUD-522 — pisada distinta al andar sobre musgo (`material="musgo"`
    en una `FrictionZone`): el musgo resbala y hasta ahora no se oía ni se
    veía, sólo se calculaba."""
    #: AUD-554 — GAP-070 "Pasos sobre Tierra/Grava" (Fase 1 del 4-1): antes
    #: usaba el `SFX_PLAYER_FOOTSTEP` genérico que comparten los otros 25
    #: escenarios, sin ninguna zona propia que lo distinguiera.
    SFX_PLAYER_FOOTSTEP_GRAVA: str = "SFX_PLAYER_FOOTSTEP_GRAVA"
    #: AUD-554 — GAP-070 "Pasos Ahogados" (Fase 5 del 4-1): más grave y a
    #: menor volumen que el genérico, para ceder protagonismo al ambiente
    #: nocturno de esa fase.
    SFX_PLAYER_FOOTSTEP_AHOGADO: str = "SFX_PLAYER_FOOTSTEP_AHOGADO"
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
    #: AUD-636 — polvo de aterrizaje. Payload: pos, fuerza (0-1, proporcional
    #: a la velocidad de caída). El jugador emite; `senales.py` pinta.
    VFX_LAND_DUST: str = "VFX_LAND_DUST"
    #: AUD-636 — polvo de despegue al saltar. Payload: pos.
    VFX_JUMP_DUST: str = "VFX_JUMP_DUST"
    #: AUD-636 — destello blanco de muerte enemiga. Payload: pos.
    VFX_KILL_FLASH: str = "VFX_KILL_FLASH"
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
    SFX_POISON_TICK: str = "SFX_POISON_TICK"
    """Tick de daño por veneno — `efectos.py:148` `dano_por_segundo`."""
    VFX_POISON: str = "VFX_POISON"
    """Nube verde al recibir tick de veneno."""
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
    #: AUD-722 — arte propio para pared/liana/tirolesa
    SFX_PLAYER_WALL_SLIDE: str = "SFX_PLAYER_WALL_SLIDE"
    SFX_PLAYER_CLIMB: str = "SFX_PLAYER_CLIMB"
    SFX_PLAYER_ZIPLINE: str = "SFX_PLAYER_ZIPLINE"
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
    #: AUD-553 — "cuando resten 10 segundos... la música de fondo acelerará
    #: su tempo". `pygame.mixer.music` transmite el archivo y no expone
    #: control de tempo/velocidad (ni pygame ni SDL2_mixer lo dan sobre un
    #: canal en reproducción) — reescalar la pista en caliente exigiría un
    #: remuestreador propio, la misma clase de DSP en tiempo real que
    #: `KNOWN_GAPS.md` GAP-070 ya dejó fuera de alcance por el mismo motivo.
    #: Lo que sí se puede construir sin DSP nuevo: una capa de pulso rítmico
    #: que se ACELERA de verdad (el ritmo lo controla el bucle del juego,
    #: no el audio) y se superpone a la música sin tocarla — misma emoción
    #: ("elevar la tensión"), sin fingir una velocidad de reproducción que
    #: el motor no tiene.
    SFX_TIMER_ALERT_PULSE: str = "SFX_TIMER_ALERT_PULSE"

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
    #: AUD-559 — un objeto `consumible=True` (`Inventory.usar`) se usó.
    #: Payload: heal_hp. `InventoryScene` no conoce a ningún `Player` —
    #: es un singleton que también se abre desde el título, sin ningún
    #: escenario cargado— así que sólo gasta la unidad y emite; quien
    #: cure es `StageScene` (`stage_parts/senales.py`), que sí tiene un
    #: jugador vivo si hay uno. Sin listener (título, o cualquier otro
    #: contexto sin escenario) el evento no hace nada — no hace falta un
    #: caso especial en `InventoryScene` para "no hay a quién curar".
    ITEM_CONSUMED: str = "ITEM_CONSUMED"
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

    # ── Recharge station (B4.3) ───────────────────────────────────────
    RECHARGE_STATION_USED: str = "RECHARGE_STATION_USED"
    """Emitted by RechargeStation. Payload: pos, station_rect."""

    # ── Save / persist ──────────────────────────────────────────────
    SAVE_REQUESTED: str = "SAVE_REQUESTED"
    """Emitted when a save should be persisted. Payload: stage_id, stage_index,
    checkpoint_x, checkpoint_y, health, max_health."""
