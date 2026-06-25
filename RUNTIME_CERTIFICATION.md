# RUNTIME_CERTIFICATION.md

## Certification: Runtime Verification

**Status**: PASS
**Date**: 2026-06-24
**Reviewer**: Senior QA Engineer / Integration Engineer

### Verified Runtime Behaviors
| Behavior | Status |
|----------|--------|
| Window opens | ✅ |
| No exceptions at startup | ✅ |
| Game loop runs | ✅ |
| FPS stable | ✅ |
| TMX visible | ✅ |
| Player visible | ✅ |
| Enemy visible | ✅ |
| Checkpoint visible | ✅ |
| Camera follows player | ✅ |
| Input works | ✅ |
| Player moves | ✅ |
| Collision works | ✅ |
| Rendering order correct | ✅ |
| No invisible entities | ✅ |
| Clean shutdown | ✅ |

### Known Runtime Issues (Fixed in Phase 7)
| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Stage not loading / empty screen | `StageScene` used key `"stage_id"`; `StageLoader` returns `"name"` | T7.5 |
| TMX layer offset swapped | `BufferedRenderer` received camera_offset + layer_offset in wrong order | T7.6 |
| Player not syncing position to camera | `Player.draw()` ignored `camera_offset` | P0.2 |
| Enemy flickering / not culled | `EnemyBase.rect` not synced from `position` after `position.set` | P0.1 |
| Input not reaching player | `InputManager` stub never pumped events; `StageScene` never called player input | P0.5, P0.6 |
| Checkpoint invisible | Camera offset was subtracted twice | P0.4 (confirmed correct) |

### Conclusion
RUNTIME_CERTIFIED. All observable behaviors verified.