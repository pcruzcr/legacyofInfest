from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class DifficultyConfig(BaseModel):
    label: str
    incoming_damage_mult: float = Field(default=1.0, ge=0.0, le=3.0)
    outgoing_damage_mult: float = Field(default=1.0, ge=0.0, le=3.0)
    enemy_health_mult: float = Field(default=1.0, ge=0.0, le=3.0)
    heal_mult: float = Field(default=1.0, ge=0.0, le=3.0)
    knockback_mult: float = Field(default=1.0, ge=0.0, le=3.0)
    parry_window: float = Field(default=0.25, ge=0.0, le=1.0)
    invincibility_duration: float = Field(default=1.5, ge=0.0, le=5.0)
    combo_window: float = Field(default=0.5, ge=0.0, le=2.0)


DIFFICULTY_PRESETS: dict[Difficulty, DifficultyConfig] = {
    Difficulty.EASY: DifficultyConfig(
        label="Easy",
        incoming_damage_mult=0.5,
        outgoing_damage_mult=1.5,
        enemy_health_mult=0.7,
        heal_mult=1.5,
        knockback_mult=0.7,
        parry_window=0.3,
        invincibility_duration=2.0,
        combo_window=0.6,
    ),
    Difficulty.NORMAL: DifficultyConfig(
        label="Normal",
        incoming_damage_mult=1.0,
        outgoing_damage_mult=1.0,
        enemy_health_mult=1.0,
        heal_mult=1.0,
        knockback_mult=1.0,
        parry_window=0.25,
        invincibility_duration=1.5,
        combo_window=0.5,
    ),
    Difficulty.HARD: DifficultyConfig(
        label="Hard",
        incoming_damage_mult=1.5,
        outgoing_damage_mult=0.75,
        enemy_health_mult=1.5,
        heal_mult=0.5,
        knockback_mult=1.3,
        parry_window=0.15,
        invincibility_duration=1.0,
        combo_window=0.35,
    ),
}


_current_difficulty: Difficulty = Difficulty.NORMAL


def get_difficulty() -> Difficulty:
    return _current_difficulty


def set_difficulty(d: Difficulty) -> None:
    global _current_difficulty
    _current_difficulty = d


def get_config(
    d: Difficulty | None = None, ng_plus: int | None = None
) -> DifficultyConfig:
    """Config de dificultad con escalado NG+ por vuelta.

    AUD-760: cada NG+ suma +10% daño recibido y vida enemiga, -5% curación
    sobre la base elegida (EASY/NORMAL/HARD). Si `ng_plus` es None se intenta
    leer del slot más reciente vía SaveManager (sin ciclo de importación).
    """
    base = DIFFICULTY_PRESETS[d or _current_difficulty]
    # Resolver ng_plus: parámetro explícito gana; si no, intentar del guardado
    # Se prefiere la ranura activa (AUD-441) al más reciente: con dos partidas,
    # `newest_slot` puede apuntar a otra distinta de la que se está jugando.
    # Se lee `_gestor_activo` sin crear uno nuevo: `SaveManager()` pisaría el
    # gestor vivo y perdería `ranura_activa` (ver test prefere_activa).
    if ng_plus is None:
        try:
            from src.engine.core.save_manager import SaveManager, _candado_gestor, _gestor_activo

            mgr = None
            with _candado_gestor:
                mgr = _gestor_activo
            if mgr is not None:
                slot = mgr.ranura_activa
                if slot is None:
                    slot = mgr.newest_slot()
                if slot is not None:
                    data = mgr.load(slot)
                    if data is not None:
                        ng_plus = int(getattr(data, "ng_plus", 0) or 0)
                    else:
                        ng_plus = 0
                else:
                    ng_plus = 0
            else:
                # Sin gestor vivo (tests sin App): leer el disco sin crear un
                # SaveManager vivo que pisaría _gestor_activo. Si no hay
                # ficheros, es 0 de todas formas.
                saves_dir = SaveManager.SAVES_DIR
                best = None
                best_time = ""
                for s in range(1, 6):
                    p = saves_dir / f"slot_{s}.json"
                    if not p.exists():
                        continue
                    try:
                        from src.engine.core.save_data import SaveData as _SD

                        raw = p.read_bytes()
                        sd = _SD.from_json(raw)
                        if sd.timestamp > best_time:
                            best_time = sd.timestamp
                            best = sd
                    except Exception:
                        continue
                ng_plus = int(getattr(best, "ng_plus", 0) or 0) if best else 0
        except Exception:
            ng_plus = 0
    ng_plus = max(0, int(ng_plus or 0))
    if ng_plus == 0:
        return base
    # Escalar: copiar para no mutar el preset
    # AUD-760: NG_PLUS_BASE es referencia, pero el escalado real es por vuelta
    cfg = base.model_copy(deep=True)
    cfg.label = f"{base.label} NG+{ng_plus}" if ng_plus else base.label
    cfg.incoming_damage_mult = min(3.0, round(base.incoming_damage_mult * (1 + 0.10 * ng_plus), 3))
    cfg.enemy_health_mult = min(3.0, round(base.enemy_health_mult * (1 + 0.10 * ng_plus), 3))
    cfg.heal_mult = max(0.1, round(base.heal_mult * (1 - 0.05 * ng_plus), 3))
    cfg.knockback_mult = min(3.0, round(base.knockback_mult * (1 + 0.03 * ng_plus), 3))
    # Ventanas se estrechan levemente por vuelta
    cfg.parry_window = max(0.05, round(base.parry_window * (1 - 0.04 * ng_plus), 3))
    cfg.invincibility_duration = max(0.5, round(base.invincibility_duration * (1 - 0.03 * ng_plus), 3))
    cfg.combo_window = max(0.2, round(base.combo_window * (1 - 0.02 * ng_plus), 3))
    return cfg


# B1 — NG+ preset: HARD + 10% por vuelta (se compone en save_manager)
NG_PLUS_BASE = DifficultyConfig(
    label="NG+",
    incoming_damage_mult=1.65,
    outgoing_damage_mult=0.70,
    enemy_health_mult=1.65,
    heal_mult=0.45,
    knockback_mult=1.35,
    parry_window=0.13,
    invincibility_duration=0.9,
    combo_window=0.32,
)
