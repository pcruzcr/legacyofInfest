# Lab 3: Vision & Pattern Recognition (Unit VIII)

**Objective:** Apply image processing and pattern recognition techniques using VisionDemoScene and PatternDemoScene.

## Tasks

### Task 1 — Thresholding & Morphology (30 min)
1. Open **VisionDemoScene** (Unit VIII from the demo menu)
2. Cycle to THRESHOLD mode and adjust the threshold value
3. Observe how binary masks change
4. Cycle to ERODE and DILATE modes — what's the effect of kernel size?
5. Record the optimal threshold for isolating the player sprite from the background

### Task 2 — Connected Components (30 min)
1. In **VisionDemoScene**, switch to COMPONENTS mode
2. Count the number of connected regions detected
3. Switch to REGIONS mode and analyze the largest region's properties (area, centroid, eccentricity)
4. Explain: why does connected component labeling assign different colors to different regions?

### Task 3 — Classification Pipeline (30 min)
1. Open **PatternDemoScene** (Unit IX from the demo menu)
2. Observe the INFERENCE mode — what class is predicted?
3. Switch to FEATURE_COMPARE mode and move the analysis rectangle
4. How does the nearest training sample change as you move over different parts of the source image?
5. Switch to PIPELINE mode and trace the full classification pipeline

## Deliverables
- Screenshots showing thresholded masks, connected components, and inference results
- The optimal threshold value found in Task 1
- A short explanation of the classification pipeline (source → preprocessing → feature extraction → classification)


--- Traducción al Español ---

## Laboratorio 3: Visión y Reconocimiento de Patrones (Unidad VIII)

**Objetivo:** Aplicar técnicas de procesamiento de imágenes y reconocimiento de patrones.

### Tareas
1. **Umbralizado y Morfología** — Ajustar umbral, observar efectos de erosión/dilatación
2. **Componentes Conectados** — Contar regiones conectadas, analizar propiedades
3. **Pipeline de Clasificación** — Observar inferencia, comparar características

### Entregables
- Capturas de máscaras umbralizadas, componentes conectados e inferencia
- Valor óptimo de umbral encontrado
- Explicación del pipeline de clasificación
