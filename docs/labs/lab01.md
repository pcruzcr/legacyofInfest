# Lab 1: Vectors & Curves (Unit II)

**Objective:** Implement vector operations and Bézier curves in the VectorLabScene and CurveEditorScene.

## Tasks

### Task 1 — Vector Arithmetic (30 min)
1. Open **VectorLabScene** (Unit II from the demo menu)
2. Switch to CHASE mode using the TAB key
3. Observe how the pursuit vector is computed from player position to target
4. Modify the chase behavior to use a normalized direction vector multiplied by a fixed speed

### Task 2 — Bézier Curves (30 min)
1. Open **CurveEditorScene** (Unit III from the demo menu)
2. Create a quadratic Bézier curve with 3 control points
3. Toggle the de Casteljau visualization with the D key
4. Observe how the recursive linear interpolation produces the curve

### Task 3 — Catmull-Rom Path (30 min)
1. In **CurveEditorScene**, switch to CATMULL_ROM mode
2. Place 5+ control points to create a path through all of them
3. Note how Catmull-Rom interpolation passes through all control points (unlike Bézier)

## Deliverables
- Screenshots showing your vector chase behavior and Bézier curve
- A brief explanation (2-3 sentences) of how de Casteljau's algorithm works
