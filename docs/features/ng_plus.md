# NG+ — Nueva Partida Plus — Especificación de Feature

**ID:** LOI-FEAT-B2 · **Versión:** 1.0.0 · **Estado:** COMPLETE
**Baseline:** `df16c614 AUD-805` — `feature/master-plan` — renderer `FROZEN 1280×720`
**Dependencias:** `SaveData.ng_plus`, `difficulty.get_config`, `SaveManager`, `SceneManager`

---

## 1. Propósito

Permitir al jugador saber de forma clara cuándo está jugando una partida normal
y cuándo una Nueva Partida Plus, y en qué vuelta va. El sistema de dificultad
ya escalaba por vuelta (+10 % daño/HP por NG+, AUD-760), pero la UI no lo
mostraba: el jugador completaba el juego, veía créditos y volvía al título sin
saber que su partida ya era NG+1.

## 2. Activación

```
COMPLETE GAME (agotar cola de escenarios → hub_backtracking/boss_paburu → créditos)
→ SceneManager._incrementar_ng_plus() : SaveData.ng_plus += 1, stage_index = 0
→ volver al título
→ al cargar la partida, get_config() escala dificultad con ng_plus
```

Sin partida activa no hay incremento (demo sin slot). El NG+ se elige
cargando esa partida desde el menú, igual que cualquier continuación.

## 3. Fuente de Verdad

```
SaveData.ng_plus: int = 0 (ge=0)  — src/engine/core/save_data.py:160
```

Única fuente. Toda UI deriva de ahí. No existe `title.ng_plus`,
`hud.ng_plus` persistente ni `worldmap.ng_plus` independiente.

Lectura: `SaveManager.ranura_activa` si existe, si no `newest_slot()`,
si no `pending_load.ng_plus` (primer frame tras cargar). Escritura:
`SceneManager._incrementar_ng_plus()` y `SaveManager.save()`.

Consumidores actuales:

| Consumidor | Lectura | Archivo |
|---|---|---|
| `difficulty.get_config` | `_gestor_activo.ranura_activa / newest_slot → load → ng_plus` | `difficulty.py:94` |
| `EnemyBase` / `Player` | vía `get_config().enemy_health_mult / incoming_damage_mult` | `enemy_base.py`, `player.py` |
| `TitleScene` | `save_manager.ranura_activa or newest_slot → load` | `title_scene.py:329` |
| `LoadGameScene` | cada `SaveData` de su `_slots[i]` | `load_game_scene.py:284` |
| `HUD` (vía stage) | `ActualizacionesDeEscenario._update_hud_ui` empuja al HUD | `actualizaciones.py:185` |

## 4. Regla de Dificultad (no modificada en B2)

`difficulty.get_config(ng_plus)` sobre el preset activo (NORMAL por defecto):

```
incoming_damage_mult = min(3.0, base*1.10*ng_plus)
enemy_health_mult    = min(3.0, base*1.10*ng_plus)
heal_mult            = max(0.1, base*0.95*ng_plus)
knockback_mult       = min(3.0, base*1.03*ng_plus)
parry_window         = max(0.05, base*0.96*ng_plus)
invincibility        = max(0.5,  base*0.97*ng_plus)
combo_window         = max(0.2,  base*0.98*ng_plus)
label                = f"{base.label} NG+{ng_plus}" si ng_plus>0
```

Topes evitan escalados imposibles. B2 no toca estos multiplicadores.

## 5. TITLE Display

`src/engine/scenes/title_scene.py:329 _update_options()` + `_ng_plus_para_continue()`

- Lee el save que `CONTINUE` reanudaría (activa → newest).
- Si `ng_plus==0` → `CONTINUE` sin trailing, UI normal.
- Si `ng_plus==N` → `CONTINUE` con `trailing = f"NG+{N}"` (renderizado a la
  derecha del menú vía `MenuItem.trailing`, sin tocar label/traducción,
  navegación, orden ni layout).

Ejemplos:

```
ng_plus 0 → CONTINUE
ng_plus 1 → CONTINUE — NG+1  (trailing NG+1)
ng_plus 2 → CONTINUE — NG+2
ng_plus 5 → CONTINUE — NG+5
```

No hardcodea `NG+1`. Dinámico. Usa el mismo patrón que el resto del menú
(`_()` traduce el label, el trailing es literal NG+ universal).

## 6. LOAD Display

`src/engine/scenes/load_game_scene.py:283 draw()`

Cada fila `i` deriva su indicador de su propio `SaveData`:

```python
ng = int(getattr(data, "ng_plus", 0) or 0)
ng_str = f"  |  NG+{ng}" if ng>0 else ""
info = f"  {nombre}  |  {stage}  |  {h}h {m}m  |  {hp}/{max}{ng_str}"
```

- Slot 1 NG+1 y Slot 2 NG+3 coexisten correctamente, cada uno con su nivel.
- `ng_plus==0` → sin badge, fila idéntica a antes.
- No altera lógica de selección/carga (`_cargar_partida` intacta).

## 7. HUD Display

`src/engine/ui/hud.py:1005 set_ng_plus_level()` + `HUD._draw_ng_plus()` +
`src/framework/scenes/stage_parts/actualizaciones.py:185`

- `HUD.set_ng_plus_level(level)` guarda `_ng_plus_level` transiente (0=oculto).
- `ActualizacionesDeEscenario._update_hud_ui` empuja cada frame el nivel
  leído del SaveManager (misma resolución que `get_config`).
- `_draw_ng_plus()` dibuja un pill compacto dorado `NG+X` si `level>0`,
  a la derecha del retrato (`portrait.right+6, portrait.top`), con fondo
  `(40,32,12,210)` y borde `(255,220,100)`, fuente `_e(10)`, padding `_e(4)`,
  clamp dentro de `INTERNAL`. No toca `portrait`, barras, márgenes, reflow,
  escala ni arquitectura de render.

Medidas: 1280 → badge 60×20 en (138,24), no solapa `vida (24,134)` ni
`score (360,24)` ni `portrait (24,24)`. 1920 análogo (168,32).

## 8. SAVE / LOAD

- Creación: `LoadGameScene._crear_partida()` → `SaveData(ng_plus=0)` (nueva).
- Persistencia: `SaveData.ng_plus` viaja en `slot_{n}.json` con firma
  `orjson` + `volcar()`, migración `migrate()` v5 `setdefault(ng_plus,0)`.
- Ciclo: `SAVE NG+1 → EXIT → TITLE (trailing NG+1) → LOAD (fila NG+1) →
  STAGE (HUD pill NG+1)` conservado. Ver `tests/test_ng_plus_ui.py`
  `test_ng_plus_ui_survives_save_load`.
- World Map: no se añade badge; obligación `WORLD PROGRESS PRESERVED`
  (completed_stages, zona unlocks) intacta, auditado en `RELEASE_READINESS`.

## 9. World Map

No se añade UI nueva. La progresión del mundo se preserva porque B2 no toca
`world_map_scene.py`, `stage_registry.py` ni `completed_stages`. El nodo
`stage4_1` canónico sigue siendo único (AUD-813).

## 10. Edge Cases

| Caso | Title | Load (por slot) | HUD |
|---|---|---|---|
| `ng_plus=0` | normal (sin trailing) | fila sin NG+ | `level=0`, `_draw_ng_plus` early return |
| `ng_plus=1` | `NG+1` | `NG+1` | `NG+1` pill |
| `ng_plus=2` | `NG+2` (no hardcode NG+1) | `NG+2` | `NG+2` |
| `ng_plus=5,10` | `NG+5`, `NG+10` | ídem | ídem, clamp 3.0 en dificultad pero badge muestra N real |
| multi-slot | activa manda (no newest si hay activa) | cada slot su propio N | active/newest resolution |
| sin saves | no CONTINUE | todas vacías | HUD 0 (stage sin save) |

Todos validados en `tests/test_ng_plus_ui.py` (14 tests) y headless playtest
NORMAL/NG+1/NG+2.

## 11. Tests

`tests/test_ng_plus_ui.py` — 14 tests, observable behavior:

```
test_title_shows_ng_plus_level
test_title_shows_ng_plus_level_dynamic
test_title_ng_plus_uses_correct_slot  (activa vs newest vs multi-slot)
test_ng_plus_zero_hides_title
test_no_saves_no_continue
test_load_scene_shows_ng_plus_level
test_load_slots_show_their_own_ng_plus
test_load_draw_includes_ng_plus_text_for_ng1_and_not_for_zero
test_hud_shows_ng_plus_level
test_hud_ng_plus_two_is_dynamic
test_ng_plus_zero_hides_hud
test_hud_ng_plus_via_stage_update      (integración actualizaciones.py)
test_ng_plus_ui_survives_save_load
test_ng_plus_three_survives_and_is_not_hardcoded
```

Regression:

```
tests/test_ng_plus_escalado.py 13 PASS (core intacto)
tests/test_ng_plus_ui.py       14 PASS (UI)
→ 27 PASS combinados
FAST 46 PASS (hud/save/worldmap)
```

## 12. Playtest

Headless `SDL_VIDEODRIVER=dummy` (sin ventana):

- NORMAL: `NEW GAME → TITLE (no CONTINUE) → crear slot 1 → TITLE CONTINUE sin NG+ → LOAD fila sin NG+ → STAGE HUD 0` PASS
- NG+1: `COMPLETE hub_backtracking → ng_plus 1 → TITLE trailing NG+1 → LOAD NG+1 → STAGE HUD NG+1 + difficulty 1.10x` PASS
- NG+2: `ng_plus 2 → TITLE NG+2 (no NG+1 hardcode) → HUD NG+2` PASS
- Visual 1280/1920: pill en (138,24) / (168,32), no clip/overlap/shift, dentro de INTERNAL, renderer intacto

## 13. Localización

`NG+X` es universal, no requiere entrada en `locale/es.json`/`en.json`.
`CONTINUE` ya está traducido (`CONTINUE→CONTINUAR` es), el trailing se
concatena. `python scripts/check_translations.py --ci` → `Catálogos en orden.`
(0 orphans).

## 14. Acceptance

```
CORE 13/13 PASS
TITLE PASS (ng0 hide, ng1/2/3 dinámico, slot correcto)
LOAD PASS (per-slot, ng0 hide, multi-slot)
HUD PASS (0 hide, 1/2/3 dinámico, vía stage, save/load)
NG+0/1/2/3 PASS
SAVE/LOAD PASS
MULTI-SLOT PASS
WORLD MAP PASS (preserved, no regression)
LOCALIZATION PASS
1280×720 PASS (badge no solapa)
1920×1080 PASS (análogo)
FAST PASS
REGRESSION PASS (core intacto)
PLAYTEST PASS
→ B2 COMPLETE
```

## 15. Archivos

Modificados (UI delta):

```
src/engine/scenes/title_scene.py        (+ trailing NG+ en CONTINUE)
src/engine/scenes/load_game_scene.py    (+ NG+ por slot en fila)
src/engine/ui/hud.py                    (+ set/get NG+ + _draw_ng_plus pill)
src/framework/scenes/stage_parts/actualizaciones.py (+ push NG+ al HUD)
```

Añadidos:

```
tests/test_ng_plus_ui.py
docs/features/ng_plus.md (este fichero)
```

Protegidos (no tocados):

```
src/engine/core/difficulty.py
src/engine/core/save_data.py (ng_plus source)
src/engine/core/save_manager.py
src/engine/scene/scene_manager.py
src/framework/entities/enemy_base.py / player.py
src/engine/render/*, src/stages/stage4_1/*, Zona4
```

## 16. Renderer / Zona4

```
RENDERER FROZEN (INTERNAL 1280 TILE 16 uniforms+letterbox)
ZONA4 CERTIFIED / DESIGN HOLD (no tocada)
```

## 17. Próximo

```
B3 ITEM COMPLETION — requiere ITEM SEMANTICS CONTRACT antes de tocar SaveData
```
