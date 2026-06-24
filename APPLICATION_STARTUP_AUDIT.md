# APPLICATION STARTUP AUDIT

**Date:** 2026-06-22  
**Auditor:** Cline  
**Scope:** Application bootstrap and main-loop verification  
**Status:** AUDIT COMPLETE

---

## 1. Files Analyzed

| File | Status |
|---|---|
| `main.py` | Read ✅ |
| `src/engine/core/app.py` | Read ✅ |

---

## 2. Startup Flow Diagram

```
main.py
  └─> import App from src.engine.core.app
  └─> main()
        └─> App.__init__()
              ├─> pygame.init()
              ├─> pygame.mixer.init()
              ├─> Create internal_surface (320×224)
              ├─> Create window_surface (scaled)
              ├─> DeltaClock()
              ├─> AssetLoader() [PLACEHOLDER STUB]
              ├─> InputManager() [PLACEHOLDER STUB]
              ├─> AudioManager() [PLACEHOLDER STUB]
              ├─> SceneManager()
              └─> scene_manager.push(SplashScene())
  └─> sys.exit(0)

❌ App.run() is NEVER CALLED
❌ Main loop NEVER EXECUTES
❌ pygame.display.flip() NEVER CALLED
❌ Window opens briefly then closes immediately
```

---

## 3. Verification Results

| # | Question | Expected (per Phase 1 DoD / Phase 3 DoD) | Actual | Result |
|---|---|---|---|---|
| 1 | Is `App.run()` implemented? | Yes — `src/engine/core/app.py` lines 123–166 | Yes, method exists | ✅ PASS |
| 2 | Is `App.run()` called from `main.py`? | Yes — per `25_IMPLEMENTATION_ROADMAP.md` Phase 3 DoD item 3: "`App.run()` is now wired to call `SceneManager.current.update(dt)` and `.draw(surface)` every frame" | **NO** — `main.py` line 20 constructs `App()` but never calls `.run()` | ❌ **FAIL** |
| 3 | Does the application open a pygame window? | Yes — `pygame.display.set_mode()` in `App.__init__` | Yes, window created | ✅ PASS |
| 4 | Does the main loop execute? | Yes — `App.run()` contains the `while running:` loop | **NO** — `run()` is never invoked | ❌ **FAIL** |
| 5 | Does SceneManager initialize correctly? | Yes — non-empty stack with SplashScene | Yes — `push(SplashScene())` in `__init__` | ✅ PASS |
| 6 | Can the application be started by running `python main.py`? | Yes — should enter main loop, render frames, respond to input | **NO** — app constructs, prints message, and exits immediately | ❌ **FAIL** |

---

## 4. Missing Startup Functionality

| Missing Item | Severity | Location | Required Fix |
|---|---|---|---|
| `App.run()` not called from `main.py` | **CRITICAL** | `main.py` line 20 | Change `_app = App()` → `_app = App(); _app.run()` |
| Placeholder stubs still active | MEDIUM | `src/engine/core/app.py` lines 33–77 | Replace `AssetLoader`, `InputManager`, `AudioManager` stubs with real implementations from Phase 2 (already done in separate modules) |

---

## 5. Missing Game Loop Functionality

The `App.run()` method itself is correctly implemented (lines 123–166). It contains:
- Event processing (`pygame.event.get()`)
- Frame timing (`self.clock.tick()`)
- EventBus dispatch
- Input pumping
- Scene update/draw
- Surface scaling and blit
- `pygame.display.flip()`

The game loop **exists but is unreachable** because `main.py` never calls `App.run()`.

---

## 6. Missing Scene Initialization

Scene initialization is **correct**:
- `SceneManager` is instantiated
- `SplashScene` is pushed during `App.__init__`
- Scene stack is non-empty

No issues found here.

---

## 7. Required Fixes

### Fix 1 — Wire `App.run()` in `main.py` (CRITICAL)

```python
def main() -> None:
    print("Legacy of InFest — starting")
    _app = App()
    _app.run()  # Enter main loop
```

### Fix 2 — Replace placeholder stubs in `app.py` (MEDIUM, deferred)

The placeholder `AssetLoader`, `InputManager`, and `AudioManager` classes in `app.py` (lines 33–77) should be replaced with imports from their real modules:

```python
from src.engine.utils.asset_loader import AssetLoader
from src.engine.input.input_manager import InputManager
from src.engine.audio.audio_manager import AudioManager
```

This is deferred because the real implementations already exist in Phase 2 modules; `app.py` is simply using outdated stubs instead of importing the real ones.

---

## 8. Audit Discrepancy Note

`PROJECT_AUDIT_REPORT.md` marks T3.4 ("Wire App.run()") as COMPLETE (commit `ace4918`). However, the current `main.py` does not call `App.run()`. This indicates either:
- The audit was incorrect, or
- The change was reverted/lost after the audit, or
- `ace4918` modified a different file (e.g., `src/engine/core/app.py`) but did not update `main.py`

**This is an AUDIT MISMATCH** — the implementation does not match the audit claim.

---

## 9. Conclusion

The application **cannot start its main loop** because `main.py` does not call `App.run()`. This blocks all downstream smoke testing and integration. The fix is a one-line change to `main.py`.

**Status:** AUDIT COMPLETE — BLOCKER FOUND