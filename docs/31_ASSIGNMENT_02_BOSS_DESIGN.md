# Assignment 2: Boss Design (Python)

**Due:** Week 8 | **Points:** 100 | **Unit:** IV (Polymorphism & State Machines)

## Objective

Design and implement a boss enemy by subclassing `BossBase`. Your boss must have multiple phases, distinct attack patterns, proper event connections, and visual feedback.

## Deliverables

| Item | Points | Location |
|---|---|---|
| Boss subclass | 40 | `src/stages/stageX/boss_your_boss.py` |
| Phase transitions | 15 | At least 2 phases |
| Attack patterns | 15 | At least 2 distinct attacks |
| HP thresholds | 10 | Phase transitions at HP milestones |
| Event connections | 10 | Death/hurt/phase events emit |
| Class structure | 10 | At least 5 methods, proper imports |

## Requirements

### Boss Class Structure

```python
from src.framework.entities.boss_base import BossBase

class YourBoss(BossBase):
    def __init__(self, x, y):
        super().__init__(x, y)
        self._phase = 1
        self._max_hp = 100
        self._hp = 100
        self._attack_cooldown = 0.0

    def update(self, dt):
        # Check phase transitions
        if self._hp <= 50 and self._phase == 1:
            self._transition_to_phase(2)
        super().update(dt)
```

### Phases

- **Phase 1:** Basic attack pattern, slower movement
- **Phase 2:** Enhanced attack(s), faster, new visual effect
- Optional Phase 3 for bonus points

### Attack Patterns

Each attack must be a separate method:

| Pattern | Description | Phase |
|---|---|---|
| `_attack_projectile()` | Fires aimed projectile | 1+ |
| `_attack_spread()` | Fires spread of projectiles | 2+ |
| `_attack_charge()` | Charges player position | 1+ |
| `_attack_summon()` | Summons minions | 2+ |

### Events

Wire these events in your boss:
- `on_phase_change(phase)` — triggered when phase transitions
- `on_death()` — triggered when HP reaches 0
- `on_hurt(amount)` — triggered when taking damage

### Visual Feedback

- Phase change should show telegraph (color flash, screen shake)
- Attacks must have telegraph state (warning before damage)
- Hurt animation / damage flash required

## Grading Rubric

| Category | Points | Criteria |
|---|---|---|
| Inherits BossBase | 10 | Class extends `BossBase` |
| Phase transitions | 15 | At least 2 phases |
| Attack patterns | 15 | At least 2 attack methods |
| HP thresholds | 10 | Phase triggers at HP cutoffs |
| Telegraph state | 10 | Warning before attack hits |
| Hurt/damage states | 10 | Proper damage response |
| Event connections | 10 | Emits phase/death/hurt events |
| Boss name config | 5 | Has config with name, hp, etc. |
| Imports | 5 | Clean imports from framework |
| Class structure | 10 | 5+ methods, proper init |

## Submission

```bash
git add src/stages/stageX/boss_your_boss.py
git add assets/maps/boss_your_boss.tmx
git commit -m "feat: complete boss design"
git push
```

## Bonus

- +5: Third phase with unique attack
- +5: Screen shake on phase transition
- +5: Custom sprite/animation for boss


--- Traducción al Español ---

## Asignación 02: Diseño de Jefe

### Evaluación Práctica II — Vertical Slice (Clase 8)
**Valor:** 15% de la nota final

### Requisitos
- Todos los entregables de Eval I mantenidos
- Función de easing usada en animación
- FilterTools.compute_histogram() impulsa lógica
- adjust_brightness() o adjust_contrast() aplicado
- apply_kernel() o gaussian_blur() aplicado
- Detección de bordes (Sobel o Canny)
- README con matriz de kernel y capturas de pantalla

Para la rúbrica detallada, consultar el documento original en inglés.
