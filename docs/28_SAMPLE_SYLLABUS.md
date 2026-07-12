# Sample Syllabus — Legacy of InFest: Game Development Practicum

**Course:** CS 4XXX / GDD 4XXX — Game Development & Digital Image Processing  
**Instructor:** [Name]  
**Term:** [Semester]  
**Prerequisites:** CS 2XXX (Object-Oriented Programming) or equivalent  
**Credits:** 3-4 (varies by institution)

---

## Course Description

Students build a complete 2D action-platformer game using the Legacy of InFest framework, applying concepts from linear algebra, computer graphics, digital image processing, and pattern recognition. The course is project-based: students design levels, program enemy AI, create bosses, and integrate processing pipelines for visual effects.

---

## Learning Objectives

By the end of this course, students will be able to:

1. Apply vector mathematics to game movement and collision
2. Implement Bézier curves and interpolation for animation
3. Manipulate color spaces and alpha blending
4. Use AABB collision detection and resolution
5. Apply convolution kernels (blur, sharpen, edge detection)
6. Implement image segmentation and feature extraction
7. Build pattern recognition pipelines (K-means, PCA, template matching)
8. Design and implement a multi-phase boss encounter
9. Create a complete, playable game stage with enemies and collectibles
10. Use TMX-based level design tools

---

## Required Materials

- Python 3.12+
- Legacy of InFest framework (GitHub Classroom)
- Tiled Map Editor (https://www.mapeditor.org/)
- Git + GitHub account

---

## Weekly Schedule

### Unit I: Foundations (Weeks 1-2)

| Week | Topic | Lab | Assignment |
|------|-------|-----|------------|
| 1 | Course intro, Python, Pygame, framework setup | Tour of Legacy engine | Fork repo, run Stage 0 |
| 2 | Game loop, input handling, scene management | Explore demo menu | Create a test scene |

### Unit II: Vectors & Transformations (Weeks 3-4)

| Week | Topic | Lab | Assignment |
|------|-------|-----|------------|
| 3 | Vector arithmetic, normalization, dot product | VectorLabScene | Stage 1 TMX layout |
| 4 | 2D transformations (translation, rotation, scale) | TransformLabScene | Place enemies in TMX |

### Unit III: Curves & Interpolation (Weeks 5-6)

| Week | Topic | Lab | Assignment |
|------|-------|-----|------------|
| 5 | Bézier curves, de Casteljau algorithm | CurveEditorScene | Enemy patrol paths |
| 6 | Interpolation, easing functions | InterpolationLabScene | Camera movement |

### Unit IV: Collision (Week 7)

| Week | Topic | Lab | Assignment |
|------|-------|-----|------------|
| 7 | AABB collision detection & resolution | CollisionLabScene | Hazards and triggers |

### Unit V: Color & Noise (Weeks 8-9)

| Week | Topic | Lab | Assignment |
|------|-------|-----|------------|
| 8 | RGB/HSV/HSL/CMYK color spaces | ColorTheoryScene | Color-coded damage |
| 9 | Procedural noise generation | NoiseLabScene | Terrain decoration |

### Unit VI: Digital Image Processing (Weeks 10-11)

| Week | Topic | Lab | Assignment |
|------|-------|-----|------------|
| 10 | Histograms, brightness, contrast | FilterDemoScene | Post-processing effects |
| 11 | Convolution, Sobel, Canny edge detection | FilterDemoScene | Edge glow, painterly |

### Unit VII: Vision & Segmentation (Week 12)

| Week | Topic | Lab | Assignment |
|------|-------|-----|------------|
| 12 | Hough transform, Harris corners, thresholding | VisionDemoScene | Boss telegraph detection |

### Unit VIII: Pattern Recognition (Week 13)

| Week | Topic | Lab | Assignment |
|------|-------|-----|------------|
| 13 | K-means, PCA, template matching | PatternDemoScene | Color quantization |

### Unit IX: Boss Design (Weeks 14-15)

| Week | Topic | Lab | Assignment |
|------|-------|-----|------------|
| 14 | Boss state machines, phases, telegraphs | Boss Venado analysis | Boss prototype |
| 15 | Boss polish, events, achievements | Playtesting | Final boss submission |

### Finals Week

| Week | Topic |
|------|-------|
| 16 | Project showcase, peer review, final deliverables |

---

## Grading Rubric

| Component | Weight | Details |
|-----------|--------|---------|
| Stage 1 (TMX) | 15% | Terrain, enemies, collectibles, checkpoints |
| Stage 2 (TMX) | 15% | Advanced terrain, hazards, weather |
| Boss Enemy | 25% | 2+ phases, 2+ attack patterns, telegraphs |
| Labs (10) | 20% | 2% each, completion-based |
| Processing Project | 15% | Pipeline using FilterTools/VisionTools |
| Participation | 10% | Peer review, playtesting, code review |

**Scale:** 90-100% A, 80-89% B, 70-79% C, 60-69% D, <60% F

---

## Late Policy

- Assignments submitted within 24h of deadline: -10%
- 24-48h: -25%
- 48h+: not accepted without prior arrangement

---

## Academic Integrity

All work must be your own. You may discuss concepts with classmates but may not share code or TMX files. Plagiarism detection scripts compare student submissions for structural similarity.

---

## Deliverable Checklist

- [ ] Stage 0 playthrough (comprehension check)
- [ ] Stage 1 TMX (terrain + enemies)
- [ ] Stage 2 TMX (hazards + weather)
- [ ] Boss Python file (class inheriting BossBase)
- [ ] Boss TMX (arena map)
- [ ] 10 lab checkpoints (F2-F10 screenshots)
- [ ] Processing pipeline demo (PipelineBuilder or script)
- [ ] Peer review (2 classmates)
- [ ] Final repository submission
