# Legacy of InFest

Motor de videojuegos educativo para Gráficas por Computadora, Procesamiento de Imágenes,
Visión por Computadora y Reconocimiento de Patrones.

- 10 laboratorios interactivos (Unidades II–IX) para aprendizaje visual de teoría
- Escenas demo de filtros, segmentación, ML, transformaciones, interpolación y ruido procedural
- DI Container (SceneRegistry) para lazy-loading de escenas, ParamPanel widget reutilizable
- Sistema completo de stages 2D con físicas, colisiones, cámara, HUD y jefes
- Framework de procesamiento: ColorTools, CurveTools, FilterTools, VisionTools, PatternRecognitionTools
- Debug overlay (F3) con FPS, event queue snapshot y árbol de módulos
- 369 pruebas automatizadas + scripts de validación de assets y generación de exámenes
- Sistema de colisión one-way corregido (`_prev_foot_y` vs straddle) — Zonas A/C de Stage 0 ahora usan tiles Solid (no Platform)
- 14 bugs de crash corregidos en 3 commits + 3 bugs de gameplay (plataformas one-way, piso/health/completion de Venado)
- Texto nítido: tamaños de fuente 7→12, 9→15, 11→18, antialiasing activado, `SDL_HINT_RENDER_SCALE_QUALITY=0`

```
pip install -r requirements.txt
python main.py
```

Documentación completa en `docs/00_MASTER_INDEX.md`.
