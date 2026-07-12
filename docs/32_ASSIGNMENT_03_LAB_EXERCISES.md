# Assignment 3: Lab Exercise Completion

**Due:** Ongoing (Week 2-15) | **Points:** 100 total | **Units:** II-VIII

## Objective

Complete the interactive lab exercises embedded in the game. Each lab tests a core concept from the course units.

## Lab Schedule

| Week | Lab | Unit | Points |
|---|---|---|---|
| 2 | Vector Lab | II — Vectors | 15 |
| 3 | Transform Lab | II — Transforms | 10 |
| 4 | Curve Editor | III — Curves | 15 |
| 5 | Interpolation Lab | III/IV — Interpolation | 10 |
| 6 | Color Theory | V — Color Spaces | 15 |
| 7 | Noise Lab | V/VIII — Noise | 5 |
| 8 | Collision Lab | VI — Collision | 10 |
| 9 | Filter Lab | VII — Filters | 10 |
| 10 | Vision Lab | VIII — Vision | 10 |

## Requirements

For each lab, you must:

1. **Open the lab** via the Demo Menu in the game
2. **Explore all modes** — cycle through with TAB
3. **Answer quiz questions** — press Q to open quiz mode, answer all questions
4. **Demonstrate understanding** — each lab tracks completion when all questions answered

### Completion Criteria

A lab is marked complete when:
- The student has cycled through all modes at least once
- Quiz questions are answered (50%+ correct)
- Screenshot is saved (press S in any mode)

## Grading

- Each lab is graded independently
- Labs completed = points earned (no partial credit for incomplete labs)
- Late labs: -20% per week

## Quiz Questions by Lab

### Vector Lab
1. What does `Vector2.normalize()` return?
2. What is the dot product of perpendicular vectors?
3. What interpolation curve uses 4 control points?
4. What does `distance()` return?

### Color Theory  
1. What are the 3 channels of HSV?
2. What does alpha blending combine?
3. What is grayscale conversion formula?

### Filter Lab
1. What convolution kernel detects edges?
2. What does a box blur kernel do?
3. What is the Sobel operator computing?

### Curve Editor
1. What curve interpolates through all control points?
2. What algorithm evaluates Bezier curves?
3. What is a NURBS weight?

## Running the Auto-Grader

```bash
# Check your progress in-game
# Open the Progress Dashboard from Demo Menu

# Or run from CLI
python -c "from src.engine.scenes.progress_scene import ProgressScene; print('Progress checked')"
```
