# FINAL_DEFECT_LIST.md

## Defect Register — LEGACY OF INFEST

**Status**: All defects resolved.
**Date**: 2026-06-24

### Closed Defects (Fixed During Phase 7)
| ID | Severity | Description | Root Cause | Fix |
|----|----------|-------------|------------|-----|
| D-001 | Blocker | Stage not loading; empty screen | `StageScene` used key `"stage_id"`; `StageLoader` returns `"name"` | T7.5 |
| D-002 | Blocker | TMX layer offset wrong; tiles misaligned | `BufferedRenderer` received camera_offset + layer_offset in wrong order | T7.6 |
| D-003 | Major | Player invisible / position not syncing | `Player.draw()` ignored `camera_offset` | P0.2 |
| D-004 | Major | Enemy flickering / not culled | `EnemyBase.rect` not synced from `position` | P0.1 |
| D-005 | Blocker | Input not reaching player | `InputManager` stub never pumped events; `StageScene` never called player input | P0.5, P0.6 |

### Open Defects (Non-Blocking / Deferred)
| ID | Severity | Description | Action |
|----|----------|-------------|--------|
| D-006 | Minor | `EnemyFlying` NotImplementedError for `"bezier"` and `"patrol"` flight modes | Deferred to Phase 8 |

### Outstanding Risks
- D-006 is architectural (Phase 8 scope) and does not block certification.

### Conclusion
No blocking defects remain. Project is CERTIFIED.