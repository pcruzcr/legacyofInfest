# Legacy of InFest

Motor de videojuegos educativo para Gráficas por Computadora, Procesamiento de Imágenes,
Visión por Computadora y Reconocimiento de Patrones.

- 10 laboratorios interactivos (Unidades II–IX) para aprendizaje visual de teoría
- Escenas demo de filtros, segmentación, ML, transformaciones, interpolación y ruido procedural
- DI Container (SceneRegistry) para lazy-loading de escenas, ParamPanel widget reutilizable
- Sistema completo de stages 2D con físicas, colisiones, cámara, HUD y jefes
- Framework de procesamiento: ColorTools, CurveTools, FilterTools, VisionTools, PatternRecognitionTools
- Debug overlay (F3) con FPS, event queue snapshot y árbol de módulos
- Atmósfera configurable desde Tiled: iluminación por focos, clima, partículas
  de ambiente, bloom y viñeta — sin escribir una línea de Python
- 1.333 pruebas automatizadas + validadores de TMX, assets y dependencias en CI

```
pip install -r requirements.txt
python main.py
```

Documentación completa en `docs/00_MASTER_INDEX.md`.
