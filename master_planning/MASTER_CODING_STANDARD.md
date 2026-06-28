# MASTER CODING STANDARD (v3 - Full Alignment)

## 1. App.run() FRAME ORDER (NO NEGOCIABLE)
1. events = pygame.event.get()
2. for event in events: if QUIT -> app.quit()
3. input_manager.pump(events)
4. event_bus.dispatch()  # BEFORE scene update
5. dt = clock.tick()
6. scene_manager.current.update(dt)
7. internal_surface.fill((15, 15, 40))  # DARK NAVY, nunca negro
8. scene_manager.current.draw(internal_surface)
9. scaled = pygame.transform.scale(internal_surface, window_surface.get_size())
10. window_surface.blit(scaled, (0, 0))  # REQUERIDO
11. pygame.display.flip()

## 2. BACKGROUND (NO NEGOCIABLE)
internal_surface.fill((15, 15, 40)) antes de cada draw.
Pantalla negra = draw loop roto. Full stop.

## 3. CAMERA OFFSET (REQUERIDO)
Screen pos = world_position - camera.offset
Todo entity.draw(surface, camera_offset) usa el offset. Sin excepcion.

## 4. PLACEHOLDER COLORS
| Entity | Size | RGB |
|---|---|---|
| Player | 20x32 | (0, 120, 255) blue |
| WalkerEnemy | 24x28 | (200, 0, 0) red |
| FlyingEnemy | 20x14 | (255, 150, 0) orange |
| ShooterEnemy | 16x24 | (150, 0, 200) purple |
| Checkpoint inactive | 16x32 | (120, 120, 120) gray |
| Checkpoint active | 16x32 | (255, 215, 0) gold |
| Floor tile | 16x16 | (60, 60, 60) dark gray + border |

## 5. ASSET LOADING FALLBACK
Missing image -> colored pygame.Surface(placeholder_size) + log WARNING.
Missing sound -> silent Sound().
Missing font -> pygame.font.Font(None, size).

## 6. COMMIT FORMAT
[SCOPE] type: description - T#.#
SCOPE: ENGINE, FRAMEWORK, STAGE0, STAGE1_1..STAGE4_2, DOCS, TESTS, TOOLS
Type: feat, fix, test, docs, refactor, perf, chore

## 7. TYPE HINTS
Python 3.14+. Todos los metodos publicos.
Sin bare Any sin comentario.

## 8. ERROR HANDLING
FrameworkUsageError, EngineError.
NO bare except.

## 9. STAGE API CONTRACT
Todo BaseScene subclass debe tener:
STAGE_ID: str, STAGE_NAME: str, ZONE: int, TIME_LIMIT: int, BGM_TRACK: str

## 10. TEST STRATEGY
pytest. Headless (SDL_VIDEODRIVER=dummy).

## 11. NO GLOBAL STATE
No globals excepto settings.py constantes.
No pygame.* directo en stages. Todo via framework APIs.
