# Entregables — Deliverables Guide

**Course:** Legacy of InFest
**Reference:** `docs/36_STUDENT_MANUAL.md`, `docs/26_STUDENT_TEMPLATE_SPEC.md`, `docs/14_PROFESSOR_DELIVERABLE_MATRIX.md`

## General Structure

Each deliverable must include a `README.md` placed in `src/stages/<student_id>/` with:

```yaml
---
assignment_type: stage | boss
assignment_name: "Your Title"
assignment_id: "stage1_2_name"
zone: 1 | 2 | 3 | final
student_name: "Your Name"
units_demonstrated: [II, III, IV, V]
evaluation_milestone: "Evaluación Práctica I" | "Evaluación Práctica II" | "Evaluación Práctica III"
---
```

### Required README Sections

1. **Narrative Context** — Describe the academic scenario
2. **Academic Concepts Demonstrated** — One subsection per unit
3. **How to Run** — Instructions to launch the deliverable
4. **Screenshots** — Before/after for FilterTools/VisionTools operations

## Deliverables by Evaluation

### Evaluación Práctica I (Class 5)
- [ ] `<assignment>.tmx` with all 8 required layers
- [ ] `<assignment>.py` — `BaseScene` or `BossBase` subclass
- [ ] Custom entity using vector math
- [ ] Entity following a curve path
- [ ] Color space operation on a surface
- [ ] `README.md` with academic concepts documented

### Evaluación Práctica II (Class 8)
- [ ] All Eval I deliverables maintained
- [ ] Easing function used in movement or animation
- [ ] `FilterTools.compute_histogram()` drives game logic
- [ ] `adjust_brightness()` or `adjust_contrast()` applied
- [ ] `apply_kernel()` or `gaussian_blur()` applied
- [ ] Edge detection result (Sobel or Canny)
- [ ] README: kernel matrix, before/after screenshots

### Evaluación Práctica III (Class 11)
- [ ] All Eval I + II deliverables maintained
- [ ] `threshold_binary()` or `threshold_otsu()` applied
- [ ] Morphological operation applied
- [ ] `connected_components()` or `analyze_regions()` used
- [ ] `extract_features()` produces training features
- [ ] Labeled dataset in `assets/datasets/`
- [ ] Trained model (`.pkl`) in assignment folder
- [ ] `EvaluationResult` with accuracy ≥70% in README
- [ ] Classifier runs at runtime; output changes game behavior in ≥2 ways
- [ ] README: full training pipeline documentation

## Templates

- **Stage template:** `student_templates/stage_template/stage_template.py` + `stage_template.tmx`
- **Boss template:** `student_templates/boss_template/boss_template.py` + README template

## Submission Rules

- All files in a single folder: `src/stages/<student_id>/`
- TMX files must be valid against `docs/06_TMX_SPEC.md`
- Python files must not produce console errors on load
- Screenshots referenced in README must exist in the same folder
