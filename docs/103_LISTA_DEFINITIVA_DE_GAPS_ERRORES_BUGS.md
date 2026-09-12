# Lista definitiva de gaps, errores y bugs del proyecto

**Fecha:** 2026-09-11 · **Alcance:** TODA la documentación del proyecto, contrastada
con el código y las pruebas actuales. Esta lista sustituye como índice a cualquier
otra: cada entrada tiene un ID canónico `D-nn`, sus fuentes originales, severidad y
estado. Al cerrar una entrada, actualizar esta tabla y KNOWN_GAPS si procede.

## Fuentes barridas

`KNOWN_GAPS.md` (75 GAPs) · `docs/87_REPORTE_DE_LO_QUE_FALTA.md` ·
`docs/70_INFORME_DE_AUDITORIA_VIVO.md` · `docs/AUDIT_2026-07.es.md` ·
`docs/89_AUDITORIA_MULTIDISCIPLINAR.md` · `docs/AUD-800_*` (4) · `docs/AUD-805` ·
`docs/50_IMPROVEMENT_ROADMAP` · `docs/62_ESTADO_DEL_PROYECTO` ·
`docs/97_ROADMAP_PS4` · `docs/92_CATALOGO_DE_FENOMENOS` · `docs/95_GUIA_ENTREGA_3` ·
`docs/99_AUD836_PROJECT_XRAY` · `PROJECT_CLOSURE_REPORT` + `PROJECT_FINALIZATION_REPORT`
(raíz) · `CHANGELOG.md` · `src/stages/boss_paburu/PENDIENTES.md` ·
`docs/98_DECISIONES_DUENO` · más lo verificado en `docs/100` (AUD-826..834),
`docs/101` (bugs del profesor P1-P20) y `docs/102` (auditoría visual AV-01..36).

## Criterios de estado

- **ACTIVO** — defecto real en el árbol actual (verificado en código, tests o capturas).
- **PARCIAL** — existe con limitación declarada.
- **DECLARADO** — ausencia deliberada o diferida por decisión del dueño/temario (no es bug).
- **OBSOLETO** — el documento que lo declara quedó anticuado; código posterior lo cambió.
- **RESUELTO** — verificado cerrado (no se listan uno a uno: ver §G).

---

## A. ACTIVOS — bugs reales hoy (orden de impacto)

| ID | Sev | Qué es | Fuentes | Estado/evidencia |
|---|---|---|---|---|
| D-01 | 🔴 | **Oscuridad ilegible en media campaña** (boss_paburu, hall, 3-1, 3-3, 4-1, 1-3, tutorial_hub, stage0): 0 `LightSource` en esos TMX + ambiente bajo | AV-01 | ACTIVO — capturas 2026-09-11; `ambiente.py:60-95` |
| D-02 | 🔴 | **Árbol de habilidades incompletable**: cuesta 64 pts, nivel máx da 59; campaña da para ~7 pts (~10 %) | AV-27, 62-B9 | ACTIVO — `skill_tree.py:79-114`, `experience.py:90` |
| D-03 | 🔴 | **Calibración de salto en rojo**: los 6 tests de `test_calibracion_del_salto.py` fijan números de la marcha 90 y AUD-827 subió a 120 (envolvente 57/114 px vs 42,75/85,5) | doc101-P5 | ACTIVO — fallo medido 2026-09-10 |
| D-04 | 🔴 | **`stage2_4` fantasma**: `stage2_4.py:38` apunta a un TMX que no existe | AV-29, XRAY | ACTIVO |
| D-05 | 🔴 | **`hall` sin checkpoint usable** (el único está tras la salida); patrón repetido en 1-1, 3-1, 2-1, boss_paburu | AV-20 | ACTIVO — `hall.tmx` |
| D-06 | 🔴 | **Charger desbalanceado**: contacto 1,5 (30-54 % HP) + stagger 0,6 s + 250 px/s > dash 200 | AV-09 | ACTIVO — `enemy_charger.py:23-24` |
| D-07 | 🔴 | **Cofre sin feedback**: `EVENTO_COFRE` sin ningún subscriptor (ni SFX ni VFX) | AV-14 | ACTIVO — `interactable_system.py:445` |
| D-08 | 🟠 | **Jugador casi inmune al contacto** (i-frames 1,5 s + cooldown 0,3 s → 0,33 HP/s máx) | AV-08 | ACTIVO — `difficulty.py:47`, `enemy_base.py:1035` |
| D-09 | 🟠 | **Jefes mueren en 6-15 s** (HP 12-20 vs ~2 golpes/s efectivos); estándar 60-120 s | AV-10, 70-iter6 (12,4/13,4/16,8 vs 30,2) | ACTIVO |
| D-10 | 🟠 | **Pico de densidad 2-1**: 40 enemigos sin curva (vs 12-15); y 3.048 px sin checkpoint declarados en 87 | AV-21, 87§15.2, 89-P5 | ACTIVO (D2 del dueño lo deja a rúbrica; la densidad sigue) |
| D-11 | 🟠 | **stage4_1: 960 tiles, 0 enemigos, travesía ~10-15 min antes del clímax** | AV-25, 70-D8 | ACTIVO (decisión declarada; sigue sin oposición) |
| D-12 | 🟠 | **Validador de assets en rojo**: exige `tileset_stage4_1_selva.png` inexistente | AV-30 | ACTIVO — `validate_assets.py:555` |
| D-13 | 🟠 | **Barra de maná muerta**: `set_mana` sin ni un llamante; invisible a 0, pero es feature sin gameplay | AUD-800 P3-07 (deferred M4) | ACTIVO-DEFERIDO — verificado 2026-09-11 |
| D-14 | 🟠 | **TMX stage_mecanicas desincronizado de su generador** (`test_ecs::regenerar_igual` rojo) | doc100 | ACTIVO — `tools/generate_stage_mecanicas.py` |
| D-15 | 🟠 | **play_sfx_critico puede atenuarse a cero** dejando la música bajada | 89§19.2 | ACTIVO (fix propuesto, decisión humana D9 pendiente) — `audio_manager.py:289` |
| D-16 | 🟠 | **Eventos muertos**: `SECRET_FOUND` sin oyente; `SFX_BOSSES_MASK_BEAM`/`RELIC_APPEAR` sin emisor (87 añade PABURU_WAVE, REY_SPIT, REY_SPLIT); `ACHIEVEMENT_PROGRESS` sin oyente | AV-33, 87§8 | ACTIVO |
| D-17 | 🟠 | **Partidas pre-AUD-502 sin migración** (checkpoint centro→esquina desplaza una vez) | doc101-P2 | ACTIVO-benigno |
| D-18 | 🟠 | **Recibir daño sin hit-stop; curarse sin VFX; críticos nunca activos** (3 huecos de juice agrupados) | AV-15/16/17 | ACTIVO |
| D-19 | 🟠 | **Contraste/legibilidad por mapa**: 1-1 lavado (niebla), 1-2 ruido de tiles inferior, lobby/hub Backtracking salas vacías gigantes, qa_proof «Untitled Stage» | AV-02/03/04/06 | ACTIVO |
| D-20 | 🟠 | **Ganchos de gameplay vacíos**: 1_3_aulas (5 TODO), lobby (4), qa_proof (plantilla) | AV-31 | ACTIVO |
| D-21 | 🟡 | **Combo**: escalones 8-10 planos (×3,×3,×3) y aéreos/especiales no lo construyen | AV-11 | ACTIVO |
| D-22 | 🟡 | **Valores muertos**: `NG_PLUS_BASE` no leído; estamina de dash apagada por defecto | AV-12 | ACTIVO |
| D-23 | 🟡 | **Zoom de cenital casi negro** (stage_cenital, pokemon_cenital): luz no aplicada o mundo vacío en vista cenital | AV-05 | ACTIVO-sin diagnosticar |
| D-24 | 🟡 | **2 tests de sombras en rojo** (`TestApagadoPorDefecto`): boss_paburu declara sombras sin estar en la excepción | doc100/101 | ACTIVO-conocido |
| D-25 | 🟡 | **4 fallos preexistentes `test_guardado_y_cadena`** + 18 rutas de docs rotas (track ajeno) | CLOSURE/FINAL | ACTIVO-preexistente, atribuido |
| D-26 | 🟡 | **Teclas de depuración activas en build normal** (declaradas en PENDIENTES; p.ej. tecla 8 llena ultimate) | PENDIENTES, CLOSURE | ACTIVO-declarado |
| D-27 | 🟡 | **Icono/rectángulo rojo sin identificar** en capturas de varios mapas | AV-07 | ACTIVO-sin diagnosticar |
| D-28 | 🟡 | **GanchoTecho y BalanceoEnLianaSalto inalcanzables** (estados no exportados) | XRAY | ACTIVO-dead code |
| D-71 | 🟡 | **`boss_paburu.tmx` perdió `sombras_proyectadas` durante la sesión del 11-09** y se restauró desde git dos veces. **Corrección de atribución (12-09): NINGÚN fichero del repo escribe ese TMX** (verificado por grep en tools/ y tests/) — la causa queda sin identificar (¿editor externo/Tiled?). Vigilar si reaparece | sesión regeneración | ACTIVO-causa desconocida |
| D-72 | 🟡 | **Divergencia de paletas entre herramientas**: `quantize_to_palette.py` y `validate_assets.py` no comparten tabla para 7 ficheros (6 siluetas/presencias de jefe + cangrejo 4-1b); cuantizar ROMPE la validación | sesión regeneración | ACTIVO — unificar tablas de paleta |

## B. PARCIALES — existen con limitación declarada

| ID | Qué es | Fuente |
|---|---|---|
| D-29 | **GAP-074**: zoom sin uniform en ruta GPU (software arreglado, AUD-825); exige GPU física; fase R | KNOWN_GAPS, doc101 |
| D-30 | **GAP-075**: barra de vida enemiga PARTIAL en GPU (shader la atenúa) | KNOWN_GAPS |
| D-31 | **Sombras B-1 sin adoptar**: cuña dimensionada por el rect entero; puede apagar luz de focos vecinos (el negro absoluto sí resuelto, AUD-510) | doc101-P9 |
| D-32 | **Jefes 82/100: 27/47 patrones de la spec sin hacer** (Venado 20/47); Rey F2/F3 declaradas; Gavilán proyectiles sin VFX | AUD-800, XRAY |
| D-33 | **Jefe Gavilán al 45 % de rúbrica** (fases 2-3, telegrafía, sin asignar) | 87§7/8 |
| D-34 | **13 GAPs parciales del ledger**: F1 tooltip (014), boss rush sin UI (030), interpolación (036), material↔tileset (039), prioridad de acciones (040), armadura (043), ECS de efectos (044), árbol de comportamiento (045), objetivos sin HUD (047), streaming descartado (048), reparto CPU/GPU (049), ciclo lunar (063) | KNOWN_GAPS |
| D-35 | **Rebinding UI cubre solo 12 acciones**; las demás no reasignables desde menú | XRAY |
| D-36 | **Skill tree solo stats** (sin habilidades activas); world-map sin gating visible | XRAY |
| D-37 | **Grab/throw infrautilizados a propósito** (sin canal en combate ni examen) | FINAL |
| D-38 | **Brute-base placeholder; Hormiga/Oropel sin SpeciesSpec** | XRAY |
| D-39 | **Paburu F2-4 partial** (declaradas, verificadas en juego parcialmente) | XRAY→FINAL |
| D-40 | **stage2_2 sin schema_version; stage3_1 DeathPit en capa Collision; 9 props catacumba_* no validadas; tileset_gavilan_ciudad.tsx duplicado** (limpieza TMX agrupada P3-02/03/04) | AUD-800 |
| D-41 | **6 claves ES + 33 EN de locale sin uso** (labs no visibles) | AUD-800 P3-05 |
| D-42 | **Traducciones**: 12 docs de estudiante en inglés sin verificación de calidad | 62, CHANGELOG 1.1.0 |

## C. DECLARADAS — ausencias por decisión (no son bugs, están catalogadas)

| ID | Qué es | Fuente/decisión |
|---|---|---|
| D-43 | **Salto aéreo/doble salto sin conectar** (GAP-024): decisión del dueño P4 — conectar rompe 6 mapas | 98-P4, 87, 89 |
| D-44 | **GAP-018**: 13 stages/jefes como contenido de estudiantes | KNOWN_GAPS |
| D-45 | **5 mecánicas F5 escritas sin llamante** (tiempo bala, scroll forzado, bullet hell, escalado, teleport) — decisión de diseño | 87/70/89, GAP-032-nota |
| D-46 | **LuaScriptEnemy y predictor IA "NO CONECTADO" a propósito** | AUDIT-07§17.3.3 |
| D-47 | **Sin block/dodge dedicado, stomp-rebote, críticos/elementos, finishing, run, ledge-hang, ladder, NG+ procedimental, ECS sistémico, reverb DSP** (lista ABSENT del XRAY) | XRAY |
| D-48 | **Boss rush sin pantallas intermedias; voz sin ficheros de voz** | 87, GAP-031 |
| D-49 | **11 subsistemas sin escena que los demuestre; 30/34 escenas sin kit de UI** (lista AWAITING_MIGRATION) | AUDIT-07§18 |
| D-50 | **X-skip de colisión abierto a propósito** (GAP-002, sin caso que lo rompa) | 87, 89 |
| D-51 | **Autoguardado comparte ranura activa** — R-05 reformulado por AUD-441 (ranura activa explícita); ya no sobrescribe "a ciegas" | AUDIT-07→save_manager |
| D-52 | **Interpolación de render, prioridad de acciones, streaming, fuzz TMX, bench GPU local**: cada uno con su "no, porque" documentado | KNOWN_GAPS/87 |
| D-53 | **Roadmap 97 PS4** (stage showcase HD, tilesets HD, grapple 2.5D, dash 8-way) y **92 fenómenos N2/N3** (arcoíris, eclipses…) — cola futura; 3D/online: no factible | 97, 92 |
| D-54 | **Roadmap 50**: M4 polish incompleto (water refraction, fog of war, aberración CPU); M6 mutación 5/10 módulos; M7 WorldSimulation y M8 content pipeline no empezados | 50 |
| D-55 | **EP2/EP3 del curso** (Unidades V-IX de visión) y **#49 máscara Tilawa** — hitos futuros/anotados | PENDIENTES #47/48/49 |
| D-56 | **Playtest humano pendiente** (#46) y **re-medición del pico de la Forma 4** — lo único que el código no puede validar solo | PENDIENTES |
| D-57 | **Curva de dificultad de campaña nunca medida con playtest documentado** | 62-B9 |
| D-58 | **Fog of war / iluminación para guiar ruta crítica**: motor listo, mapas no lo usan | 87§15.2 |

## D. DEUDA DE PROCESO / DOCS / TESTS

| ID | Qué es | Fuente |
|---|---|---|
| D-59 | **Índice maestro desfasado** (118 vs docs reales) y `test_el_indice` fallando — único bloqueante RELEASE READY del AUD-800 | AUD-800 P3-01 |
| D-60 | **~90 ficheros modificados sin commit en el árbol** (riesgo de proceso nº1 de 89§18.7, sigue vigente hoy) | 89, git status |
| D-61 | **17 marcadores AUD-XXX sin rellenar** en ficheros clave (trazabilidad rota) | AV-35 |
| D-62 | **Doc drift**: 42_CUTSCENE documenta 4 acciones no instanciadas; 52_EVENT_MAP desfasado (SECRET_FOUND/ACHIEVEMENT_PROGRESS); events.py «not yet emitted» falso; stage_registry promete `selector.py` inexistente; 09_HUD_SPEC diverge de hud.py; «21 especies» y «26 escenarios» no verificables | AV-34, 87§22, 70 |
| D-63 | **Cobertura ~48 % sin medición por módulo; mypy trinquete 9/22; pip-audit no bloquea CVEs** | 62, 50 |
| D-64 | **Matriz CI 3.11-3.13 y GPU real nunca ejecutadas localmente** (local 3.14, CI dummy) — build no reproducible idéntico; fugas GPU UNKNOWN | 70, XRAY |
| D-65 | **Pruebas de milisegundos sin pytest-timeout** (test_stage4_1 9 s); suite completa no ejecutable en sesión (sin xdist, TIMEOUT 180 s) | 70, AUD-805 |
| D-66 | **Detector de huérfanos ciego ante re-exports de `__init__`** (reescritura ast.Call pendiente); anillo de sistemas muertos sin dar de baja (backtracking.py, prefab_loader, RoomTransition, MonedaFx…) | AV-32, GAP-035 |
| D-67 | **GAP-042 residual**: azar sembrado pero no aislado por módulo (20 usos np.random); replay bit-a-bit sin verificar | 87 |
| D-68 | **requirements.lock con pines caducos** (numpy 1.26.4, Pillow 12.2.0) sin regenerar | 70/GAP-022 |
| D-69 | **R-06**: balance de vida/daño enemigo calibrado contra el modelo de daño viejo, sin reequilibrio global desde julio | AUDIT-07 |
| D-70 | **Pruebas doc↔código de contenido**: solo 1 doc de ~95 con pruebas de contenido | 87§12 |

## E. Contradicciones entre documentos — resueltas para esta lista

Regla aplicada: manda el documento más reciente y, si es verificable, el código.

| Ítem contradictorio | Resolución |
|---|---|
| Combo al aire (BUG#13 de `95_GUIA_ENTREGA_3` "ABIERTO") | **RESUELTO** (AUD-818, doc 101) — el doc 95 quedó viejo |
| GAP-033 mutación 44 % (abierto en 87/89, cerrado en 70-iter14) | **RESUELTO** (70 manda por fecha) |
| GAP-034 ruff sin fijar (abierto en 89, cerrado AUD-408) | **RESUELTO** |
| Daltonismo GPU (HECHO AUD-252 en 87 vs deuda en 89) | **RESUELTO** (87 trae la evidencia) |
| GAP-024 salto aéreo (cerrado en 87, abierto en 89) | **DECLARADO** (decisión del dueño 98-P4 manda) |
| P2/P3/P6 de doc 89 (tachados §6, abiertos §12.2) | **RESUELTO** con AUD-363/365/368 (§6 manda) |
| AUD-033 (305 cambios sin commit en dev, julio) | **OBSOLETO** (el repo se committeó; el análogo vigente es D-60) |
| R-05 autoguardado sobrescribe ranura | **OBSOLETO-REFORMULADO** (AUD-441; queda la decisión D-51) |
| i18n inexistente (AUDIT-07) | **OBSOLETO** (implementado después) |
| GL sin conectar (89§17) | **OBSOLETO** (AUD-343/725) |
| "HUD PHASE muestra total" aceptado con motivo | **OBSOLETO** (AUD-512 lo arregló; PENDIENTES lo tenía como aceptado) |

## F. Verificación rápida de ítems nuevos incorporados hoy

- **D-13 (maná):** `grep -rn "set_mana" src/` → solo la definición `hud.py:1084`; cero llamantes. La barra no se dibuja a 0 (`hud.py:461`): el defecto es latente, no visible.
- **D-51 (autoguardado):** `save_manager.py:299-410` tiene `ranura_activa` explícita y guardas de ranura corrupta (AUD-441/251) — el mecanismo que describía R-05 ya no existe tal cual.

## G. El balance global (lo que SÍ está cerrado y verificado)

- **KNOWN_GAPS: 60/75 RESUELTOS** con evidencia; 13 parciales declarados; 1 abierto (GAP-074, fase R); 1 de estudiantes.
- **Los 20 bugs del profesor** (doc 101): 18 resueltos y verificados en runtime; #9 parcial (B-1 sombras); #5 resuelto con regresión de AUD-827 (D-03).
- **AUD-826..834** (doc 100): 9/9 VERIFIED con tests y runtime.
- **validate_tmx 35/35**; 0 assets rotos en los 34 TMX; 0 skips injustificados.
- **Decisiones del dueño 98**: backlog A1-A7/B7/C1/D2/P4/P5 — cierre 100 %.

**Conteo de esta lista:** 30 ACTIVOS (D-01..D-30, incluye D-71/72) · 12 PARCIALES
restantes (D-31..D-42) · 16 DECLARADAS (D-43..D-58) · 12 DE PROCESO (D-59..D-70) ·
11 contradicciones resueltas.
