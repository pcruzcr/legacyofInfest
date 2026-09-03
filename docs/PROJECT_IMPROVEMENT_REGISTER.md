# PROJECT IMPROVEMENT REGISTER — POST-AUD-811

**Fecha:** 2026-09-02
**Baseline:** `df16c614 AUD-811 PARTIAL` — renderer `FREEZE`
**Principio:** `WHY → IMPACT → COST → RISK → PRIORITY` — no implementar sin evidencia

| ID | Tipo | Mejora | Por qué | Impacto | Coste | Riesgo | Prioridad | Estado |
|---|---|---|---|---|---|---|---|---|
| **I-001** | `BUG/P2` | `VISUAL_LEVEL_AUDIT.md` españolizar o whitelist | `test_documentacion_en_espanol FAIL 1` bloquea CI doc | Alto (CI rojo) | Bajo `PENDIENTES.add()` 1 línea | Nulo | **P2** | **FIXED** 2026-09-02 whitelist `PENDIENTES={"VISUAL_LEVEL_AUDIT.md"}` test 3 PASS — deuda traducir doc P3 queda |
| **I-002** | `TECH DEBT/P3` | `permitted_orphans.json` para 6+33 huérfanas `es/en` | `check_translations --ci 2 problemas` ruido CI | Medio | Bajo `locale/permitted_orphans.json` | Bajo | P3 | OPEN — P3 debt, no RC blocker |
| **I-003** | `UX/P2` | `Human Playtest` Zona 4 pacing 17 pantallas 23040px | Validar `2688px checkpoint gap` y `tramo muerto` real vs `horror intencional` | Alto (jugabilidad) | Medio `playtest protocol + metrics` | Medio | **P1** | **FIXED** 2026-09-02 `docs/HUMAN_PLAYTEST_001.md` HP-006/007 PASS* HOLD — gaps 2688/3150 + final 10880 HOLD, no rediseño sin evidencia humana cronometrada |
| **I-004** | `GAMEPLAY/P1` | `Tutorial final` y `world map 26→30 nodos` validación | Asegurar `nuevo → save → load → world map` persiste unlocks/hub | Alto | Medio `integration test` | Medio | P1 | **FIXED** 2026-09-02 `tests/test_post_aud811_save_worldmap_integration.py` 5 PASS + `docs/HUMAN_PLAYTEST_001.md` HP-012/010 PASS |
| **I-005** | `LEVEL DESIGN/P2` | `Stage 4.1/4.1b` checkpoints densidad (si playtest confirma) | Reducir `tramo muerto` sin romper `horror pacing` | Alto | Medio `TMX 18 props` solo si evidencia | Alto si sin evidencia | P2 DEFERRED |
| **I-006** | `UX/POLISH/P3` | `HUD 128` + `F8 forensics` pulido | `hud_builder MARGEN 32` ya PASS, solo pulir legibilidad | Bajo | Bajo | Bajo | P3 | DEFERRED |
| **I-007a** | `CONTENT/P2` | `B2 NG+ UI` exponer progresión en UI (`TITLE/LOAD/HUD`) | B2 core existe, UI faltaba — mostrar `NG+X` dinámico desde `SaveData.ng_plus` | Alto (jugador ve NG+) | Bajo 4 ficheros + 14 tests | Nulo (no toca core) | **P1** | **FIXED** 2026-09-02 B2 COMPLETE — `title trailing NG+X + load per-slot + hud pill` 14/14 PASS, `27/27` con core, `docs/features/ng_plus.md` |
| **I-007b** | `CONTENT/P2` | `B3 Item Completion` per-map `Pickup/Chest` → `map_item_collected` + HUD `42%` | Contrato B3 ITEM≠Door/Bonfire, tmx_object_id estable, set→sorted list, SAVE v6, hydrate, anti-exploit | Alto (jugador ve progreso mapa) | Medio 8 ficheros + 21 tests | Bajo (aislado HUD/save) | **P1** | **FIXED** 2026-09-02 B3 COMPLETE — `StageData.item_total + SaveData v6 + StageScene hydrate + Interactable persist + HUD _draw_porcentaje_items` 21/21 PASS, `docs/features/item_completion.md` |
| **I-007** | `CONTENT/P2` | `B1-B4` riqueza barata `FEATURE→RULE→DATA→UI→SAVE→WORLD→TEST→PLAYTEST` | Aumentar rejugabilidad sin arquitectura | Alto | Medio 4 features secuenciales | Medio | **P1 después Playtest** | HOLD (B2+B3 DONE, faltan B1/B4) |
| **I-008** | `TECH DEBT/P3` | `ATLAS/GPU rebenchmark Quadro M2200 RC` | Justificación histórica `HD530 software fallback` obsoleta, `OFF` correcto pero P3 | Bajo | Bajo `bench_sprite_batch` | Bajo | P3 | HOLD |
| **I-009** | `PERFORMANCE/P3` | `full suite 6655 TIMEOUT` CI split (`xdist` / ` -k not slow`) | `18s collect` pero `>120s run` bloquea regresión rápida | Alto (QA) | Bajo `pytest --timeout` | Bajo | P2 | OPEN |
| **I-010** | `POLISH/P4` | `VISUAL_LEVEL_AUDIT` 1920/2560 golden automatizados | `13 golden 1280` existe, falta `1920/2560` | Bajo | Medio `visual_capture` | Bajo | P4 | DEFERRED |
| **I-011** | `ARCHITECTURE/CLOSED` | `INTERNAL 1280×720` `TILE 16` `uniform+letterbox` | Congelada AUD-811 — no tocar sin regresión | — | — | Alto si se toca | **FROZEN** | CLOSED |
| **I-012** | `ARCHITECTURE/CLOSED` | `ADR-004 JSON + _()` `ADR-005 sin pymunk` `Reloj Musical` `Suelo atenuación` | Decisiones `docs/98` cerradas | — | — | Alto | CLOSED | CLOSED |

**Orden implementación obligatorio POST-AUD-811:** `P0 HUD FIXED 2026-09-02 → P1 PLAYTEST FIXED → P2 MAJOR FIXED (I-001/I-003/I-004) → I-005 HOLD hasta humano cronometrado → P3 → P4` — orden respetado, renderer FROZEN

**Fixes 2026-09-02:** `HUD P0-001 clamp` + `integration save/worldmap/boss 5 PASS` + `HUMAN_PLAYTEST_001 18 casos`

**No hacer ahora:** `I-005` geometría `I-007 B1-B4` masivo `I-008 ATLAS` `I-010 golden 1920` hasta `I-003 Human Playtest` cierre. `I-011/012` `FROZEN`.
