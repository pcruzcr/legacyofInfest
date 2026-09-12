# Changelog

> A partir de la 1.1.0 este registro se escribe en castellano, que es el
> idioma del curso y el que ya usan la interfaz por defecto, los comentarios
> del código nuevo y la documentación de auditoría. La entrada de la 1.0.0 se
> conserva en inglés tal y como se publicó.

## [1.3.1] - 2026-09-12

Segunda tanda del cierre de la lista 103.

- **Toda la cadena de guardado en verde (83/83):** `Stage21Oficinas` tiene
  identidad (recupera su checkpoint guardado), y un `WarpZone` con destino
  cuenta como salida del nivel — el portal a Paburu, con su llave, es la
  salida legítima del 4.1.
- **Los jefes aguantan una pelea de verdad:** Venado 36, Rey 45, Gavilán 42
  y Paburu 60 de vida (triple), con los umbrales de fase escalados; la
  batería de jefes pasa 69/69 con las simulaciones escaladas.
- **Paridad generador↔TMX byte a byte** en `stage_mecanicas` y `stage0`
  (las colas del track privado se emiten verbatim); `stage0` recupera sus
  dos obstáculos saltables en el trinquete y el doc declara el tamaño real.
- **La plantilla del estudiante vuelve a demostrar todo:** los seis tipos
  que no enseñaba, dos checkpoints, coleccionables, hueco exigente y nota
  92.3 (antes 82.3).
- **Juice del jugador:** recibir daño pide hit-stop, destello rojo y
  sacudida; curarse suelta partículas; descubrir secreto tiene ceremonia;
  el progreso de logros llega a los subtítulos de accesibilidad.
- **Combo:** los escalones 8-10 ya no son planos (×3.2/×3.6/×4.0).
- **Luz:** `ambient_light` ≥ 0.8 en paburu, 3-1, aulas, stage0 y 4.1.
- **El descenso de la loma 408 del 4.1 funciona** (costura realineada y
  cima fantasma retirada) — D-72.

## [1.3.0] - 2026-09-11

Cierre de la lista 103 (gaps, errores y bugs): los defectos que se podían
cerrar con prueba quedaron cerrados; los que exigen decisión de diseño o
re-trabajo de contenido quedaron clasificados en `docs/103` (§H) con su
motivo.

### Campaña

- **El Rey Terciopelo de tres fases es el jefe real del juego:** el paquete
  fantasma `stage2_4` (que apuntaba a un mapa inexistente) se retiró y su
  Rey completo —división en mitades y frenesí incluidos— vive en
  `src/stages/boss_rey/`, con los sprites que ya estaban en el árbol.
- **El árbol de habilidades se puede terminar:** coste total 58 de los 59
  puntos que otorga el nivel máximo (era 64).
- **El embestidor se lee antes de golpear:** contacto 1,0 y embestida a
  210 px/s (antes 1,5 y 250, por encima del dash).
- **Los cofres dicen algo:** abrir uno suena el tono de recompensa y suelta
  chispas donde está.
- **El tutorial es el hub** y el mapa del mundo (30 nodos) distingue la
  progresión bloqueada en orden de las demos académicas libres.
- **Los créditos firman con el nombre completo** de quien entregó cada
  nivel, y el equipo docente se reconoce por prefijo.

### Motor

- **La suite no hereda tu partida:** el `SaveManager` vivo se resetea entre
  pruebas; un NG+ del disco ya no multiplica la vida enemiga del siguiente
  test (raíz de ~30 falsos rojos).
- **El predictor de IA persiste en `.npz`** y re-entrena al cargar: el motor
  ya no deserializa pickle en ninguna ruta.
- Trinquete de salto re-medido a la marcha 120 (natural 4 baldosas, experta
  7); i-frames de Normal a 1,0 s; `stage4_1` recupera su exención de
  habilidades.

### Documentación

- Las 16 rutas rotas de la documentación corregidas o declaradas historia;
  `crafting.py` en el árbol de arquitectura; la región de la puntuación del
  HUD y la ficha del nombre en el diálogo descritas como las dibuja el motor
  a 1280×720.

## [1.2.0] - 2026-09-10

Cierre de release de la línea 1.x: el estado certificado RC (B2/B3/B4/Zone4,
save v6, HUD, TMX) se consolida, se integra el stage 4.1 y se dejan por
escrito los informes de cierre. Sin features nuevas: lo que estaba
declarado se verificó, y lo que estaba roto se reparó con prueba.

### Campaña

- **Stage 4.1, respiro narrativo:** nivel, tilesets, fondos, seis pistas de
  música, efectos de ambiente y diálogos (`data/dialogues/stage4_1.json`)
  integrados, con su spec, diseño y auditoría en `docs/`.
- **Exámenes que faltaban:** parry con examen real en la sala Defensa del hub
  (profesor que aturde 2 s al devolver) y chimenea de muro en
  `stage_mecanicas` coronable por cadena de saltos + agarrarse, con bot
  que lo demuestra.
- **Verdad de jefes:** el Gavilán picado con telegraph, plumas proyectiles
  y órbita que se cierra; las fases del Rey F1→F3 y las cuatro formas de
  Paburu verificadas por transiciones, no declaradas.
- **Reparaciones:** el escudo del blindado protegía la espalda (invertido),
  las habilidades `skill_ground_pound` y `skill_coraza` tenían candado sin
  entrada en el catálogo, y la luz apagaba las barras de vida enemigas.

### Motor y datos

- Mapas con `schema_version` y el tileset de datacenter ampliado en
  `stage2_2`; validadores de assets/TMX y la guía de seguridad de cambios
  actualizados a la ola final.

### Cierre

- Informes de cierre y finalización en la raíz, auditoría documental total,
  rayos X del repositorio (AUD-836) y guía de juego con handoff al
  estudiante.

## [1.1.0] - 2026-07-28

Primera versión pensada para que **treinta estudiantes la usen a la vez sin
que nadie apague incendios**. La 2.0.0 sigue siendo la versión futura descrita
en `docs/50_IMPROVEMENT_ROADMAP.md`; no confundir con la versión de ese
documento, que va por su cuenta.

### Lo que un estudiante nota

- **Temario separado por unidades, con desbloqueo.** Las diez demos
  académicas ya no están todas abiertas desde el primer minuto: cada unidad se
  abre al aprobar la anterior con 4 aciertos de 5. Cada una trae **3 bloques
  de teoría** —enunciado, fórmula y el fichero del motor que la implementa— y
  **5 preguntas** con la razón de la respuesta correcta. Son 30 bloques y 50
  preguntas escritas, no plantillas.
- **El progreso se guarda de verdad.** Identificación por correo de la
  universidad (tecla `I` en el menú del temario), un JSON por estudiante, y
  reanudación automática al arrancar.
- **Las trece demos dibujan en la pantalla entera.** Estaban escritas para
  320x224 y nunca se migraron a los 800x600 actuales: el elemento que se
  manipula vivía en el cuadrante superior izquierdo.
- **Atmósfera encendida:** luz ambiente y focos desde el TMX, bloom, viñeta,
  clima, partículas de ambiente, ciclo día/noche y estaciones.
- **Interfaz en castellano por defecto**, con catálogo inglés completo.

### Lo que un profesor nota

- **El calificador de jefes ya no penaliza usar bien el framework.** Exigía un
  método `take_damage` o `hurt`, nombres que no existen en el motor —la API es
  `apply_hit`—. El jefe de referencia sacaba 63/100; ahora saca 100/100 y uno
  vacío sigue sacando 0.
- **El calificador de escenarios ya no castiga cerrar bien un mapa.** Contaba
  los muros laterales como «plataformas sin ruta desde el spawn». Stage 0 pasó
  de 86,2 % a 93,1 %.
- Previsualizador de TMX, exportador de notas, detector de plagio, generador
  de exámenes y realimentación automática.

### Corregido — los que se veían jugando

- La interfaz se dibujaba **antes** que la luz, así que el sistema de
  iluminación la oscurecía: el HUD conservaba el 42 % de su brillo y el
  indicador de combo pasaba de 406 píxeles a 0.
- Los enemigos normales no tenían barra de vida; sólo los jefes.
- El bestiario con `Esc` volvía al menú equivocado.
- Tres de cinco nodos del mapa del mundo se dibujaban encima del título.

### Corregido — los que no se veían

- **La iluminación no había iluminado un solo píxel** en la vida del proyecto:
  desbordamiento de `uint8` en el gradiente.
- El bloom estaba invertido: `BLEND_RGB_ADD` ignora `set_alpha`.
- `FilterDemoScene` recalculaba seis histogramas por fotograma sobre imágenes
  que no cambiaban. De 10,24 ms de mediana a **0,73 ms**, con el resultado
  idéntico barra por barra.
- Bestiario, logros e inventario se comían un fichero corrupto en silencio.
- Dos módulos duplicados y muertos retirados (`spritesheet.py`,
  `bitmap_font.py`), junto con las tres afirmaciones falsas que los sostenían
  en la documentación —incluida una fuente, `PixeloidSans.ttf`, que **nunca
  existió en el repositorio**; todo el texto sale de `assets/fonts/game.ttf`—.

### Cambiado

- `pyproject.toml` declaraba `2.0.0`. El producto está en la línea 1.x. La
  versión vive ahora en un solo sitio y hay una prueba que lo vigila.
- La regla de capas de `03_ARCHITECTURE.md` §3.1 se incumplía 27 veces, todas
  legítimas. Reescrita a las tres que sí son ciertas y convertida en
  `tests/test_layering.py`.
- CI ejecuta ahora los validadores de traducción y de cobertura TMX, que
  existían y nadie corría, y califica el jefe de referencia en vez de la clase
  base abstracta.

### Estado medido

| Medida | Valor |
|---|---|
| Pruebas | 1.715, todas en verde |
| ruff sobre `src/`, `tests/`, `scripts/`, `tools/` | limpio |
| Validador TMX / de recursos | 2/2 · 0 errores |
| Cobertura de propiedades TMX en el mapa de ejemplo | 100 % |
| Stage 0, mediana por fotograma | 7,2–9,0 ms (presupuesto 16,67) |

### Conocido y no resuelto

- 12 documentos del estudiante siguen en inglés.
- Dos escenarios jugables y un jefe: es un motor con un prólogo, no un juego
  terminado.
- `test_gameplay_integration` tarda unos 50 s.
- Falta una rúbrica propia para arenas de jefe; hoy se les aplica la de nivel.

## [1.0.0] - 2025-07-10

### Added

- **Initial release** of Legacy of InFest — an educational game engine for Computer Graphics, Image Processing, Computer Vision, and Pattern Recognition.
- **10 interactive labs** spanning Units II–IX for visual theory learning.
- **Demo scenes** covering filters, segmentation, ML, transformations, interpolation, and procedural noise.
- **DI Container (SceneRegistry)** for lazy-loading scenes with a reusable ParamPanel widget.
- **Complete 2D stage system** with physics, collisions, camera, HUD, and boss encounters.
- **Processing framework:** `ColorTools`, `CurveTools`, `FilterTools`, `VisionTools`, `PatternRecognitionTools`.
- **Debug overlay** (F3 key) showing FPS, event queue snapshot, and module tree.
- **8 enemy types:** Walker, Shooter, Flying (Bezier/patrol), Charger, Brute, Archer, Assassin, Caster.
- **Boss system** (`BossBase`) with `boss_venado` implementation.
- **Dynamic music system** (`DynamicMusic`) with zone-based audio transitions.
- **Sound effects pipeline** via EventBus: 15 SFX events wired to `SoundBank` + `AudioManager`.
- **VFX system:** particle system, lighting, post-processing, fog of war, water effects, trail system, hit effects, damage numbers, ambient particles.
- **Stage systems:** camera with parallax, checkpoints, collision system (axis-separated), drawing system, hazard system, progression system.
- **UI components:** HUD, message box, minimap, tutorial overlay, screen banner, bitmap font.
- **Asset pipeline:** `AssetLoader`, `Spritesheet`, TMX loader via `StageLoader`, parallax backgrounds.
- **Input system:** `ActionMap` + `InputManager` with configurable keyboard bindings.
- **Save/load system:** `SaveManager` with checkpoint persistence, inventory, achievements.
- **Student template system** for lab exercises.
- **369 automated tests** with pytest.
- **Exam generation and asset validation scripts** (`scripts/generate_exam.py`, `scripts/validate_assets.py`).
- **Tooling:** `generate_stage0_tmx.py`, `pixel_asset_generator.py`, `build_dataset.py`, `convert_audio.py`, `validate_stage.py`.

### Fixed

- **Collision system** — rewired to axis-separated resolution (X → resolve X → Y → resolve Y), fixing wall-climb/teleport bug.
- **One-way platform collision** — corrected via `_prev_foot_y` + straddle detection; Stage 0 zones A/C now use Solid tiles instead of Platform tiles.
- **Player spawn point** — TMX Y coordinate now correctly treated as feet position (adjusted by 32px).
- **Player states** — `_pending_jump` / `_pending_jump_timer` attributes added to `Player.__init__` with 8-frame buffer to prevent bounce-off on one-way platforms.
- **Collision rect depth** — X-skip heuristic uses `tile.top >= player_rect.centery` for reliable platform detection with merged collision rects.
- **14 crash bugs** resolved across 3 commits, plus 3 gameplay bugs (one-way platforms, floor/health/completion of Venado boss).
- **Text rendering** — font sizes adjusted (7→12, 9→15, 11→18), anti-aliasing enabled, `SDL_HINT_RENDER_SCALE_QUALITY=0` for crisp text.

### Changed

- **HUD timer** — migrated from spritesheet (`fonts/hud_digits.png`) to TTF font (`PixeloidSans.ttf`) for higher quality.
- **Message box** — repositioned from Y=196 (bottom) to Y=0 (top) to avoid overlap with health/timer HUD.
- **SoundBank** — integrated via EventBus; `SoundBank.load_all()` scans `assets/sfx/` recursively; 15 SFX events defined and wired to stage scenes.
- **API contracts** — updated `Action` enum, `SoundBank`, and `AssetLoader` documentation to match implementation signatures.
- **EventBus** — exposed read-only `queue_snapshot` and `subscribers_snapshot` properties for debug overlay.

### Known Issues

- **GAP-002 — Collision rect depth heuristic:** `tile.top >= player_rect.centery` may fail with abnormally tall merged collision rects. No known cases currently trigger this.
- **GAP-004 — Background zone missing in Stage 0 TMX:** `background_zone` property absent; stage runs without parallax backgrounds. StageLoader support exists — requires TMX update.
- **GAP-014 — Collision rect runtime visualization:** Debug overlay (F1) draws collision rects but no tooltip shows `prev_bottom`, `tile.top`, or `velocity.y` on hover/pause.

For full gap tracking, see `KNOWN_GAPS.md`.



--- Traducción al Español ---

*Este documento está disponible en inglés. Para una traducción completa al español, contacte al profesor.*
