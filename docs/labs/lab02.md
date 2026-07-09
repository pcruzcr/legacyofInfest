# Lab 2: Interpolation & Animation (Unit V)

**Objective:** Master easing functions and keyframe animation using the InterpolationLabScene.

## Tasks

### Task 1 — Easing Functions (20 min)
1. Open **InterpolationLabScene** (Unit III/IV from the demo menu)
2. Cycle through each of the 10 easing functions using UP/DOWN
3. For each function, note:
   - Where does it accelerate (beginning, end, both)?
   - Does it overshoot the target?
   - Does it bounce?

### Task 2 — Keyframe Animation (30 min)
1. Switch to KEYFRAME_ANIM mode
2. Set 3 keyframes with different positions
3. Toggle auto-animation with SPACE
4. Change the easing function between keyframes and observe the result

### Task 3 — Custom Easing (40 min)
1. Review the math_utils.py implementations in `src/engine/utils/math_utils.py`
2. Implement an `ease_in_out_back` function that overshoots slightly at both ends
3. Test it in the InterpolationLabScene using the custom slot

## Deliverables
- Screenshots of 3 different easing functions in action
- Your custom easing function code
- A comparison of ease_in_quad vs ease_out_elastic (when is each appropriate?)
