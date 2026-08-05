from __future__ import annotations

from src.framework.vfx.particle_system import BurstConfig


class HitEffects:
    """Pre-configured burst configs for common hit reactions."""

    SPARK = BurstConfig(
        count=8, speed=80.0, lifetime=0.3,
        size=(2, 4), color=(255, 255, 200), spread=180.0,
        friction=0.9, gravity=200.0,
    )

    SPARK_BIG = BurstConfig(
        count=16, speed=120.0, lifetime=0.5,
        size=(3, 6), color=(255, 220, 100), spread=180.0,
        friction=0.85, gravity=300.0,
    )

    BLOOD = BurstConfig(
        count=6, speed=60.0, lifetime=0.4,
        size=(2, 3), color=(200, 40, 40), spread=120.0,
        friction=0.8, gravity=400.0,
    )

    BLOOD_BIG = BurstConfig(
        count=12, speed=90.0, lifetime=0.6,
        size=(2, 5), color=(220, 30, 30), spread=120.0,
        friction=0.75, gravity=400.0,
    )

    PARRY = BurstConfig(
        count=20, speed=150.0, lifetime=0.4,
        size=(3, 5), color=(100, 200, 255), spread=360.0,
        friction=0.9,
    )

    HEAL = BurstConfig(
        count=10, speed=50.0, lifetime=0.6,
        size=(2, 4), color=(100, 255, 100), spread=360.0,
        friction=0.8, gravity=-100.0,
    )

    DEATH = BurstConfig(
        count=20, speed=100.0, lifetime=0.8,
        size=(3, 6), color=(200, 50, 50), spread=360.0,
        friction=0.8, gravity=200.0,
    )

    DASH_TRAIL = BurstConfig(
        count=2, speed=20.0, lifetime=0.15,
        size=(4, 6), color=(100, 150, 255), spread=30.0,
        friction=0.95,
    )

    BUBBLE = BurstConfig(
        count=3, speed=30.0, lifetime=0.6,
        size=(2, 3), color=(180, 220, 255), spread=30.0,
        friction=0.9, gravity=-30.0,
    )

    CHARGE_GLOW = BurstConfig(
        count=3, speed=30.0, lifetime=0.2,
        size=(2, 4), color=(255, 200, 50), spread=360.0,
        friction=0.9,
    )

    #: AUD-281 — recoger algo. Chispas doradas que **suben**.
    #:
    #: `gravity` negativa, como `HEAL` y al contrario que `SPARK`: una moneda
    #: recogida no cae al suelo, se va con el jugador. Es la diferencia entre
    #: leerlo como «algo se rompió aquí» y como «te has llevado algo».
    #:
    #: Ocho partículas y 0,4 s, no veinte y un segundo: esto ocurre cada vez
    #: que se toca una moneda, y en un pasillo con quince monedas una fiesta
    #: por cada una tapa el escenario.
    PICKUP = BurstConfig(
        count=8, speed=45.0, lifetime=0.4,
        size=(2, 4), color=(255, 215, 0), spread=360.0,
        friction=0.88, gravity=-120.0,
    )

    @staticmethod
    def get_for_damage(damage: float) -> BurstConfig:
        if damage >= 1.0:
            return HitEffects.SPARK_BIG
        return HitEffects.SPARK

    @staticmethod
    def get_blood_for_damage(damage: float) -> BurstConfig:
        if damage >= 1.0:
            return HitEffects.BLOOD_BIG
        return HitEffects.BLOOD
