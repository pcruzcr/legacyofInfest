# Documentación breve — Entrega 2 (Versión intermedia funcional)

**Estudiante:** Yariel Andrey Elizondo Jiménez
**Nivel:** Stage 1-3 — "Las Aulas" (Zona 1, Universidad)
**Fecha:** 24 de agosto de 2026

Esta es la documentación breve que pide la consigna oficial de la Entrega 2
(§8). El detalle académico completo — fórmulas, tablas de verificación,
capturas antes/después — está en [`README.md`](README.md); este documento
sigue la estructura exacta que pidió el profesor, sin repetir lo que ya está
ahí.

---

## 1. Descripción

| Campo | Valor |
|---|---|
| Nombre del nivel | Stage 1-3 — "Las Aulas" |
| Objetivo | Recorrer el aula universitaria infestada de punta a punta, esquivando estudiantes infectados y cuadernos voladores, hasta llegar al portal de salida |
| Concepto / ambientación | Universidad moderna infestada — paleta blanco/hueso, gris carbón/concreto y azul eléctrico como acento tecnológico |
| Mecánica principal | Plataformeo 2D: caminar, saltar 4 huecos con muerte instantánea (sin ruta segura alternativa) y subir 3 tramos de escalada con formas distintas entre sí |
| Interacción propia | Un casillero (`Door`) que se abre con el botón de usar y dispara una animación por easing vía `EventBus` |
| Inicio / final | `PlayerSpawn` a la izquierda (x=64) → `NextTrigger` (portal) a la derecha (x=3040) |
| Progresión | Lineal por el piso; los 3 entrepisos (con pizarra, enemigos y coleccionables) son **rutas opcionales**, no obligatorias para completar el nivel |
| Dificultad | Los 4 huecos exigen saltar de verdad (sin tablón de por medio); las 3 escaleras varían el reto de navegación sin exigir saltos fuera del alcance físico del jugador |

---

## 2. Computación Gráfica I — dónde y cómo se aplicó cada tema

### Curvas y modelado
- **`cuaderno_volador.py`**: 4 instancias de `CuadernoVolador` recorren una
  **curva de Bézier cúbica** (`CurveTools.bezier()`, base de Bernstein) sobre
  cada uno de los 4 huecos, con puntos de control documentados en el README
  (§3) y verificados contra la fórmula calculada a mano.
- **`generar_mapa.py`**: la geometría del terreno (escaleras, entrepisos,
  huecos) se genera por código a partir de la física real del salto del
  jugador (`settings.py`: gravedad, impulso, velocidad), no a mano en Tiled —
  cada transición se valida y reporta "SALTOS INVALIDOS: 0".

### Representación de escenas
- Mapa de **8 capas** (`BG_Far`, `BG_Mid`, `BG_Near`, `Terrain`,
  `Terrain_Detail`, `Objects`, `Collision`, `FG_Overlay`), 3200×608 px (4
  pantallas), organizado en 3 tramos con progresión de dificultad y
  **3 patrones de escalada distintos** (clásica, zigzag con retroceso, ritmo
  quebrado con un salto de compromiso) para que la composición no se repita
  pantalla a pantalla — ver README §4 para el detalle de cada uno.
- Profundidad simulada con parallax de 3 velocidades (0.15×/0.35×/0.70×) y
  z-order por `rect.centery` para el primer plano.

### Color y transparencia
- Paleta "aula moderna" intencional: blanco/hueso para paredes (máxima luz),
  gris carbón/concreto para estructura, azul eléctrico como único acento —
  aplicada de forma consistente en tileset y fondo, no decorativa al azar.
- **Transparencia**: `ColorTools.alpha_blend()` mezcla las 3 capas de fondo
  contra un lienzo oscuro (Unidad V); el renderer de `pyscroll` se reconstruye
  con `alpha=True` para que las celdas sin azulejo dejen ver el parallax
  detrás (workaround documentado en README §9.3, sin tocar el framework).
- **Unidad VII**: `FilterTools.compute_histogram()` mide la luminancia real
  del fondo lejano y esa medición **decide** qué filtro de convolución
  aplicar (ver abajo) — no es un valor fijo de antemano.

### Texturas
- Tileset propio (`tileset_aulas_yariel.png`), 64 celdas de 16×16 px, 26 en
  uso: piso, paredes, pizarra, ventanas, casilleros, mobiliario y 2 celdas de
  animación (panel LED encendido/apagado).
- Escala y resolución coherentes con el resto del motor (16×16 px, misma
  rejilla que todos los niveles); cada textura corresponde a su objeto
  (pizarra = superficie de escritura, casillero = almacenamiento, ventana =
  vidrio con marco).
- El fondo parallax se deriva de **ilustraciones propias** (no fotos —
  cambio pedido por el profesor, ver §3 de Testing) procesadas con el mismo
  pipeline HSV de la Unidad V.

### Animación
- **Casillero interactivo** (Unidad VI): al abrirlo, un panel se encoge según
  `ease_out_bounce(t)` en 0.6 s — no un movimiento lineal, sino uno que gana
  velocidad y rebota antes de asentarse.
- **Panel LED de techo**: alterna dos fotogramas (encendido/tenue) vía la
  `<animation>` nativa de Tiled, con temporización irregular (700 ms / 120 ms)
  para simular parpadeo, no un pulso parejo.
- Ambas están sincronizadas con la interacción real del jugador (el casillero
  no anima hasta que se abre) y no son cosméticas sueltas.

---

## 3. Testing

### Problemas encontrados (y de dónde salieron)

| # | Problema | Cómo se encontró |
|---|---|---|
| 1 | Tramo de 640 px sin checkpoint (penaliza `design_pacing`) | `grade_stage.py` |
| 2 | Checkpoints pegados al borde de cada hueco (16 px de margen) | Revisión propia jugando |
| 3 | Puente de plataforma sobre los 4 huecos quitaba el desafío de saltar | Feedback de diseño propio |
| 4 | Las 3 escaleras eran el mismo patrón copiado 3 veces (repetitivo) | Feedback jugando |
| 5 | Segunda versión de las escaleras variaba número/ancho de escalón pero seguía siendo "subir en línea recta" | Feedback jugando |
| 6 | La escalera C (un solo salto grande a una plataforma larga) se sentía "dos pasos largos", no distinta de verdad | Feedback jugando |
| 7 | El afiche decorativo se pintó casi todo azul por accidente al recolorear la paleta (reutilizaba las mismas letras que los casilleros) | Reporte de un cuadro azul "que se movía por el mapa" — aislado por eliminación (fondo, notebook, casillero, hasta llegar al UI) |
| 8 | El fondo parallax tenía ventanas y casilleros con bordes duros que se confundían con objetos reales al verse a través de huecos del primer plano | Mismo reporte anterior |
| 9 | `pytmx` interpreta `value=""` como `None`, no como cadena vacía — una puerta declarada "sin llave" quedaba bloqueada sin aviso | Prueba dirigida del casillero interactivo tras implementarlo |
| 10 | El fondo original usaba fotografías reales del aula, incompatibles con la estética pixel art del motor (`docs/20_ASSET_BIBLE.md`) | Indicación directa del profesor |

### Pruebas realizadas
- `scripts/validate_tmx.py` — estructura del TMX, metadatos obligatorios.
- `scripts/grade_stage.py` — rúbrica automática de diseño (checkpoints,
  geometría, ritmo, alcanzabilidad).
- Validador propio de saltos (`generar_mapa.py`), que recalcula cada
  transición contra la física real del jugador.
- Ejecución headless del `StageScene` real (sin ventana) durante 60+ frames,
  simulando: apertura del casillero por el jugador, recolección de un
  coleccionable, cálculo del histograma del fondo antes/después.
- Aislamiento por eliminación del bug del "cuadro azul": se quitaron uno a
  uno el fondo, los `CuadernoVolador` y el panel del casillero hasta
  confirmar que la causa era ajena a estos cambios (el fantasma de speedrun
  del propio motor).

### Correcciones aplicadas
1. Checkpoints reducidos de 8 a 3, reposicionados a ≥300 px de cualquier
   `DeathPit` (antes 16 px).
2. Tablón quitado de los 4 huecos: hay que saltarlos de verdad.
3. Las 3 escaleras rediseñadas dos veces hasta lograr formas realmente
   distintas entre sí (clásica / zigzag con retroceso / ritmo quebrado).
4. Colores del afiche desacoplados de los de los casilleros
   (`crear_tileset.py`).
5. Ilustraciones de fondo simplificadas a gradientes y franjas de luz
   difusas — sin bordes duros que se confundan con objetos.
6. `generar_mapa.py` corregido para no declarar `key_id=""` (se omite la
   propiedad en vez de ponerla vacía).
7. Fondo regenerado desde 3 ilustraciones pixel-art propias en vez de
   fotografías, manteniendo intacto el pipeline HSV de la Unidad V.
8. Se agregaron 3 coleccionables (antes 0) usando el sistema de
   interactuables del framework, sin tocarlo.

### Resultado obtenido
- `validate_tmx.py`: **`[OK]`**, sin avisos.
- `scripts/grade_stage.py`: **90,8 % (118/130)**, frente al 81,5 % de la
  Evaluación Práctica I.
- **16/16** transiciones de salto válidas.
- 60+ fotogramas de ejecución real sin excepciones.
- Los 12 puntos que faltan para el máximo no son un descuido: 6 son un falso
  positivo documentado del calificador (no de este nivel) y 6 son la
  decisión deliberada de solo 3 checkpoints — ver README §10.

---

## 4. Notas sobre el uso de IA

Este proyecto se desarrolló con apoyo de un asistente de IA (Claude Code)
para programación, depuración y generación de assets por código. Todas las
decisiones de diseño —qué escalera va dónde, cuántos checkpoints, qué colores
usar, cuándo un fondo se sentía mal— fueron dirigidas y aprobadas por la
estudiante en conversación directa, iterando sobre resultados reales
(headless y capturas) antes de aceptarlos. La estudiante puede explicar y
defender cada decisión tomada en este documento.
