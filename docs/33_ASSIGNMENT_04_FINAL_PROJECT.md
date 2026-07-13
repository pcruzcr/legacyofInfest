# Assignment 4: Final Project — Complete Zone

**Due:** Week 16 | **Points:** 200 | **Units:** II-VIII (Comprehensive)

## Objective

Design and implement a complete game zone consisting of 3 stages, 1 boss stage, and 1 hub area. This is a capstone assessment covering all skills learned in the course.

## Deliverables

| Item | Points | Description |
|---|---|---|
| Stage 1 | 40 | Entry level for zone |
| Stage 2 | 40 | Mid-zone challenge |
| Boss Stage | 50 | Boss encounter |
| Hub Area | 30 | Safe zone connecting stages |
| Integration | 40 | All stages connect, save/load works |

## Requirements

### Zone Theme
Choose one:
- **Forest** — Green tileset, tree enemies, nature collectibles
- **Cemetery** — Dark tileset, undead enemies, spirit collectibles
- **Factory** — Industrial tileset, mechanical enemies, gear collectibles
- **Ice** — Blue tileset, ice physics, crystal collectibles
- **Lava** — Red tileset, fire hazards, magma collectibles

### Stage Requirements (per stage)
- TMX map: 40x23-80x60 tiles, 32x32 tile size
- Player spawn + 2+ checkpoints
- 3-8 enemies (valid types)
- 5+ collectibles
- Climate property matches zone theme
- Metadata: author, zone, stage_id, stage_name

### Boss Requirements
- Inherits `BossBase`
- 2+ phases with HP thresholds
- 2+ attack patterns
- Telegraph before attacks
- Event wiring (phase/death/hurt)
- Proper class structure (5+ methods)

### Hub Area
- Safe zone (no enemies)
- Connects to all 3 stages
- Contains visual narrative elements
- Portal/exit objects for stage transitions

### Integration
- Stage queue advances correctly (hub→stage1→hub→stage2→hub→boss→complete)
- Save/load works between stages
- Player state persists through zone
- No softlocks (all paths reachable)

## Grading Rubric

| Category | Points | Criteria |
|---|---|---|
| Stage Design (x3) | 30 | Each stage passes grade_stage.py rubrics |
| Boss Design | 30 | Passes grade_boss.py rubric |
| Hub Area | 15 | Connects all stages, safe zone |
| Map Quality | 20 | Coherent layout, visible effort |
| Enemies | 15 | Appropriate placement and types |
| Collectibles | 15 | Sufficient and well-placed |
| Navigation | 15 | Stage queue works, no softlocks |
| Save/Load | 15 | Progress persists across sessions |
| Polish | 15 | Visual quality, performance |
| Integration | 15 | All pieces work together |
| Metadata | 5 | Properties set correctly |
| Documentation | 10 | README for the zone |

## Submission

```bash
# All files in your repo
git add assets/maps/zoneX/
git add src/stages/zoneX/
git commit -m "feat: final project zone X complete"
git push
```

The CI pipeline will run auto-grading on all TMX and boss files.


--- Traducción al Español ---

## Asignación 04: Proyecto Final

### Proyecto Integrador Invenio Fest (Clase 12)
**Valor:** 20% de la nota final

### Requisitos
- Integración completa de todas las unidades
- Presentación interdisciplinaria
- Demostración funcional del proyecto

Para la rúbrica completa y criterios de evaluación, consultar el documento original en inglés.
