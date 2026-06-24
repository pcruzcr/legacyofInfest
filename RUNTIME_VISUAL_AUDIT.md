# RUNTIME_VISUAL_AUDIT

Generated: read-only runtime visual inspection

## 1. Screens Currently Visible

When running `python main.py` the user sees:
- A scaled 320×224 window (title: "Legacy of InFest")
- Solid black background (StageScene clears to black)
- Flat-colour tile blocks (from stub tileset)
- Player: 16×24 rectangle RGB (180, 60, 60) at world X=32, Y=192
- Enemy Walker: 16×16 rectangle RGB (120, 160, 120) at world X=120, Y=192
- Checkpoint marker: 16×32 rectangle (defined in Checkpoint.draw)
- No parallax backgrounds (images absent)
- No HUD (hearts, timer, messages absent)

## 2. Verified Runtime Values

- **Map collision rects:** 2 (floor at Y=208..224)
- **Player spawn:** (32, 192) — bottom-left area of map
- **Player initial rect:** (32, 168, 16, 24)
- **Camera offset:** (0, 0) at spawn (lerp requires dozens of frames to move)
- **Enemy walker pos:** (120, 192), state=PATROL
- **Next trigger:** present at stage right edge
- **Checkpoints:** 1 registered (fixture provides one)
- **Stage metadata:** stage_id="minimal", name="Minimal Stage", time_limit=120, bgm="bgm_test"

## 3. Missing Assets (blocking visual fidelity)

- `assets/player/*.png` — 9 sprite sheets
- `assets/enemies/*.png` — enemy sprite sheets
- `assets/backgrounds/stage0/*.png` — 3 parallax layers
- `assets/sprites/shared/checkpoint.png`
- `assets/ui/heart_*.png` — HUD elements
- `assets/fonts/*.png` — bitmap fonts
- `assets/music/*.ogg` — BGM tracks
- `assets/sfx/**/*.wav` — SFX bank
- `assets/tilesets/tileset_stage0.png` (stub is at root only)

## 4. Placeholder Assets

- `assets/tileset_stage0.png` — valid PNG but not a real tileset graphic
- `assets/tileset_stage0.tsx` — valid TSX but not a real tileset definition
- `tests/assets/tileset_stage0.*` — test copies of the stubs

## 5. Missing Animations

- Player: idle/walk/jump/fall/crouch/short_attack/long_attack/hurt/die — all missing
- Enemy Walker: walk/hurt/die — missing
- Shared: checkpoint glow, torch — missing

## 6. Missing Gameplay Loops

- No player input processing (InputManager is a stub)
- No gravity/coyote/jump-cut interaction visible (player sits at spawn)
- No enemy contact damage interaction
- No checkpoint activation visual/sound
- No stage transition on NextTrigger
- No Game Over / continue flow
- No HUD update (hearts, timer, messages)

## 7. Missing UI

- No HUD hearts
- No timer display
- No tutorial message overlay
- No stage banner
- No pause/menu system

## 8. Missing Combat Interactions

- Player cannot attack (no input)
- Enemies do not patrol (no patrol_length wired in StageScene for Walker)
- No hitstop
- No invincibility flash
- No enemy death sequence

## 9. Scene Boundaries

- Floor collision rect at Y=208..224
- No ceiling, no walls in fixture
- Player can walk off edges (no side bounds)
- NextTrigger placed at stage right edge

## 10. Camera Behavior

- Camera created and attached to player
- Update runs each frame
- Smooth lerp follow present
- Parallax offset exist but backgrounds absent so invisible
- Clamp prevents camera from scrolling above Y=0

## 11. Runtime FPS

- DeltaClock targets 60 FPS
- No frame cap enforcement visible in probe; actual FPS depends on host system

## 12. Recommendations Before Phase 8

1. **Replace test fixture with real Stage0 TMX**
   - Path: `src/stages/stage0/stage0.tmx`
   - Requires full tileset and background assets

2. **Create minimal placeholder assets**
   - 16×16 coloured tiles (even 1-colour per tile type is enough to see layout)
   - Single-colour player/enemy sprites larger than current rectangles (e.g. 32×32)

3. **Wire InputManager**
   - At minimum map arrow keys/Space/Z/X so movement and attack are testable

4. **Register all enemy types in StageScene**
   - Flying and Shooter should be instantiated from entity_list

5. **Add HUD overlay**
   - Even a placeholder text/timer proves the system works

6. **Fix checkpoint draw contract**
   - StageScene references `_trigger_rect`; confirm all checkpoint visuals use current API

7. **Add visual debug mode**
   - Toggle to render collision rects, hitboxes, camera bounds

8. **Profile FPS**
   - Confirm 60 FPS with pyscroll rendering on target hardware