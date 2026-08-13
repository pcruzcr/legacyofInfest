---
document_id: "LOI-ASGN02-031B"
title: "Entrega 2: diseño de jefe (Python)"
aliases: ["Entrega 2: diseño de jefe", "Assignment 2: Boss Design"]
tags: ["entrega", "jefe", "diseno", "academico"]
description: "Entrega de diseño de jefe"
source: "docs/31_ASSIGNMENT_02_BOSS_DESIGN.md"
date_processed: "2026-08-13"
---

# Entrega 2: diseño de jefe (Python)

**Entrega:** aplica cuando la entrega individual asignada es un Jefe (ver `21_COURSE_SCHEDULE.md`) | **Instrumento:** Evaluación Práctica I — Prototipo Funcional (arena y fases básicas) y II — Vertical Slice (ataques y pulido)

> **AUD-455.** Traduce y corrige el documento: el cuerpo en inglés describía
> una API de `BossBase` inventada (`__init__(self, x, y)`, `self._hp`,
> `_transition_to_phase()`, eventos `on_phase_change`/`on_death`/`on_hurt`)
> que no existe en el código — verificado por AST contra
> `src/framework/entities/boss_base.py`, ya documentado con precisión en
> `22_API_CONTRACTS.md` §10.5. Además, el resumen en español del final no
> hablaba de jefes en absoluto: era el contenido de la Entrega de Filtros
> pegado por error. Se sustituyen ambos por una descripción fiel a la API
> real (`BossPhase`, `set_phases()`, `_patrol_behavior`/`_alert_behavior`,
> `habilidades_que_suelta()`). También quita un import de `EnemyState`
> heredado del `boss_template.py` viejo (AUD-455, 2026-08-13) — el fichero
> real no lo tiene y no se usa en el cuerpo de la clase.

## Objetivo

Diseñar e implementar un jefe enemigo heredando de `BossBase`. El jefe debe tener varias fases, patrones de ataque distintos, conexiones de evento correctas, y retroalimentación visual — ver `17_BOSS_SPEC.md` para el contrato de diseño completo del jefe asignado.

## Estructura real de la clase de jefe

Contenido exacto que produce `student_templates/boss_template/boss_template.py` (ver `26_STUDENT_TEMPLATE_SPEC.md` §5 para el fichero completo):

```python
from src.framework.entities.boss_base import BossBase, BossPhase

class TuJefe(BossBase):
    def __init__(self, spawn_position: pygame.Vector2) -> None:
        phases = [
            BossPhase(
                phase_index=0,
                health_threshold=6.0,       # umbral de salud en el que empieza esta fase
                attack_patterns=["ATAQUE_A", "ATAQUE_B"],
                movement_type="sine",
                speed_multiplier=1.0,
            ),
            BossPhase(
                phase_index=1,
                health_threshold=0.0,
                attack_patterns=["ATAQUE_C", "ATAQUE_A"],
                movement_type="bezier",
                speed_multiplier=1.5,
            ),
        ]
        super().__init__(
            spawn_position=spawn_position,
            max_health=12.0,
            damage_on_contact=0.75,
        )
        self.set_boss_name("TU JEFE")
        self.set_phases(phases)

    def _patrol_behavior(self, dt: float) -> None: ...
    def _alert_behavior(self, dt: float) -> None: ...
    def _get_animation_key(self) -> str: ...
    def _build_hitbox(self) -> pygame.Rect: ...
    def _build_hurtbox(self) -> pygame.Rect: ...
```

La transición de fase la lleva `BossBase` automáticamente comparando `current_health` contra los `health_threshold` de `phases` — **no** se comprueba a mano en `update()`, y no hace falta sobrescribir `update()`.

## Fases

- **Fase 1:** patrón de ataque básico, movimiento más lento
- **Fase 2:** ataque(s) mejorados, más rápido, nuevo efecto visual (`sprite_override`/`filter_effect` en el `BossPhase`)
- Fase 3 opcional para puntos adicionales

## Patrones de ataque

Cada ataque debe ser un método separado, listado en `attack_patterns` del `BossPhase` correspondiente. Ejemplos reales del jefe de referencia (`boss_venado`): `STOMP`, `CHARGE`, `VINE_TOSS`, `VINE_SWEEP`, `MUSHROOM_SPORE`.

## Ganchos y estado provistos por `BossBase`

| Gancho/propiedad | Cuándo se usa |
|---|---|
| `habilidades_que_suelta()` | Habilidad(es) que el jefe deja al morir — se controla con el atributo `skill_drop` |
| `fase_invulnerable` | Propiedad de sólo lectura: si la fase actual declara `invulnerable=True` |
| `escala_de_fase` | Multiplicador de tamaño de la fase actual (atributo `escala` del `BossPhase`) |
| `recibir_parry()` | Se llama cuando el jugador para (parry) un ataque del jefe |
| `on_attack_fired(attack_name)` / `on_summon(species_id, count)` | Ganchos para telemetría/efectos al disparar un ataque o invocar esbirros |

Ver `22_API_CONTRACTS.md` §10.5 para la firma completa de `BossBase`.

## Retroalimentación visual

- El cambio de fase debe mostrar telegrafiado (destello de color, sacudida de pantalla)
- Los ataques deben tener un estado de telegrafiado (aviso antes de hacer daño)
- Se requiere animación de dolor / destello de daño

## Rúbrica de calificación

Este entregable corresponde a los criterios de escena/objeto, animación e interacción, y ataques/fases de las rúbricas de Evaluación Práctica I y II — ver `27_ACADEMIC_RUBRICS.md` §4–§5 para los 100 puntos completos de cada una. No se repite aquí para no desincronizarse.

`scripts/grade_boss.py src/stages/tu_jefe/tu_jefe.py --json` da la calificación automática.

## Entrega

```bash
git add src/stages/tu_jefe/tu_jefe.py
git add assets/maps/tu_jefe.tmx
git commit -m "feat: diseño de jefe completo"
git push
```

## Puntos adicionales

- Tercera fase con ataque único
- Sacudida de pantalla en la transición de fase
- Sprite/animación propia para el jefe

---
## 🔗 Documentos relacionados

- [[17_BOSS_SPEC.md|Especificación de jefes]]
- [[22_API_CONTRACTS.md|Contratos de API]]
- [[27_ACADEMIC_RUBRICS.md|Rúbricas académicas]]
