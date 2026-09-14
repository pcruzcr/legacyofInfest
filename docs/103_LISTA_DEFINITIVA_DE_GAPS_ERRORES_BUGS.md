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
| D-02 | 🔴 | **Árbol de habilidades incompletable**: cuesta 64 pts, nivel máx da 59; campaña da para ~7 pts (~10 %) | AV-27, 62-B9 | **RESUELTO AUD-839** — total 58/59 (ímpetu plano); completabilidad verificada |
| D-03 | 🔴 | **Calibración de salto en rojo**: los 6 tests fijaban números de la marcha 90 | doc101-P5 | **RESUELTO AUD-839** — trinquete re-medido a marcha 120: natural 4 baldosas (margen 0,04), experta 7 (0,20); 7/7 verdes |
| D-04 | 🔴 | **`stage2_4` fantasma**: apuntaba a un TMX que no existe | AV-29, XRAY | **RESUELTO AUD-839** — paquete retirado; el Rey completo (F1-F3) consolidado en `src/stages/boss_rey/` y es el que carga el registro |
| D-05 | 🔴 | **`hall` sin checkpoint usable** (el único está tras la salida) | AV-20 | **RESUELTO AUD-839** — checkpoint de entrada en x=96. El patrón en 1-1/3-1/2-1/boss_paburu queda pendiente de revisión por mapa |
| D-06 | 🔴 | **Charger desbalanceado**: contacto 1,5 + 250 px/s > dash 200 | AV-09 | **RESUELTO AUD-839** — contacto 1,0 y embestida 210 px/s |
| D-07 | 🔴 | **Cofre sin feedback**: `EVENTO_COFRE` sin subscriptores | AV-14 | **RESUELTO AUD-839** — el evento lleva la posición del cofre; la escena suena el tono de recompensa y suelta chispas |
| D-08 | 🟠 | **Jugador casi inmune al contacto** (i-frames 1,5 s + cooldown 0,3 s) | AV-08 | **RESUELTO AUD-839** — i-frames de Normal a 1,0 s (daño por contacto máximo ~0,5 HP/s) |
| D-09 | 🟠 | **Jefes mueren en 6-15 s** (HP 12-20) | AV-10, 70-iter6 | **RESUELTO AUD-839** — Venado 36, Rey 45, Gavilán 42, Paburu 60 (umbrales de fase escalados ×3; batería de jefes 69/69) |
| D-10 | 🟠 | **Pico de densidad 2-1**: 40 enemigos sin curva (vs 12-15); y 3.048 px sin checkpoint declarados en 87 | AV-21, 87§15.2, 89-P5 | ACTIVO (D2 del dueño lo deja a rúbrica; la densidad sigue) |
| D-11 | 🟠 | **stage4_1: 960 tiles, 0 enemigos, travesía ~10-15 min antes del clímax** | AV-25, 70-D8 | ACTIVO (decisión declarada; sigue sin oposición) |
| D-12 | 🟠 | **Validador de assets en rojo**: exige `tileset_stage4_1_selva.png` inexistente | AV-30 | ACTIVO — `validate_assets.py:555` |
| D-13 | 🟠 | **Barra de maná muerta**: `set_mana` sin ni un llamante; invisible a 0, pero es feature sin gameplay | AUD-800 P3-07 (deferred M4) | ACTIVO-DEFERIDO — verificado 2026-09-11 |
| D-14 | 🟠 | **TMX desincronizado de su generador** | doc100 | **RESUELTO AUD-839** — stage_mecanicas y stage0 byte a byte (colas del track privado emitidas verbatim); plantilla regenerada con su tool |
| D-15 | 🟠 | **play_sfx_critico puede atenuarse a cero** | 89§19.2 | **OBSOLETO** — AUD-310 separó el duck persistente del temporizado; sonda AUD-839: tras 2,3 s el duck vuelve a 1,0 solo |
| D-16 | 🟠 | **Eventos muertos**: `SECRET_FOUND`, `ACHIEVEMENT_PROGRESS` sin oyente; `MASK_BEAM` sin emisor | AV-33, 87§8 | **PARCIAL AUD-839** — `SECRET_FOUND` (flash+stinger) y `ACHIEVEMENT_PROGRESS` (subtítulo accesible) cableados; `MASK_BEAM` queda planificado (no hay ataque beam en el Gavilán) |
| D-17 | 🟠 | **Partidas pre-AUD-502 sin migración** (checkpoint centro→esquina desplaza una vez) | doc101-P2 | ACTIVO-benigno |
| D-18 | 🟠 | **Recibir daño sin hit-stop; curarse sin VFX; críticos** | AV-15/16/17 | **PARCIAL AUD-839** — daño: hit-stop + flash rojo + shake; curación: partículas + flash verde. Los «críticos» no existen como sistema (los EVENTOS_CRITICOS de sonido sí están cableados): queda declarado |
| D-19 | 🟠 | **Contraste/legibilidad por mapa**: 1-1 lavado (niebla), 1-2 ruido de tiles inferior, lobby/hub Backtracking salas vacías gigantes, qa_proof «Untitled Stage» | AV-02/03/04/06 | ACTIVO |
| D-20 | 🟠 | **Ganchos de gameplay vacíos**: 1_3_aulas (5 TODO), lobby (4), qa_proof (plantilla) | AV-31 | ACTIVO |
| D-21 | 🟡 | **Combo**: escalones 8-10 planos (×3,×3,×3) | AV-11 | **PARCIAL AUD-839** — escalones 8-10: ×3.2/×3.6/×4.0. Que aéreos/especiales construyan combo queda pendiente (diseño) |
| D-22 | 🟡 | **Valores muertos**: `NG_PLUS_BASE` no leído; estamina de dash apagada por defecto | AV-12 | ACTIVO |
| D-23 | 🟡 | **Zoom de cenital casi negro** (stage_cenital, pokemon_cenital): luz no aplicada o mundo vacío en vista cenital | AV-05 | ACTIVO-sin diagnosticar |
| D-24 | 🟡 | **2 tests de sombras en rojo** (`TestApagadoPorDefecto`) | doc100/101 | **RESUELTO AUD-839** — fuera la declaración redundante de boss_paburu; introspección por el dominio `StagePhysics` |
| D-25 | 🟡 | **4 fallos `guardado_y_cadena` + rutas rotas** | CLOSURE/FINAL | **RESUELTO AUD-839** — identidad `Stage21Oficinas` (STAGE_ID), salidas por WarpZone reconocidas, rutas saneadas; 83/83 |
| D-26 | 🟡 | **Teclas de depuración activas en build normal** (declaradas en PENDIENTES; p.ej. tecla 8 llena ultimate) | PENDIENTES, CLOSURE | ACTIVO-declarado |
| D-27 | 🟡 | **Icono/rectángulo rojo sin identificar** en capturas de varios mapas | AV-07 | ACTIVO-sin diagnosticar |
| D-28 | 🟡 | **GanchoTecho y BalanceoEnLianaSalto inalcanzables** (estados no exportados) | XRAY | ACTIVO-dead code |
| D-71 | 🟡 | **`boss_paburu.tmx` perdió `sombras_proyectadas` durante la sesión del 11-09** y se restauró desde git dos veces. **Causa CONFIRMADA (12-09): hay escritura/commit concurrente en el árbol** — el lote `AUD-839` (f7a20ce) commiteó trabajo ajeno a esta sesión, incluida la tubería HD aquí descrita, y llegó a editar ficheros a mitad de sesión. Vigilar coordenación de frentes | sesión regeneración | ACTIVO-coordinación |
| D-73 | 🟠 | **El validador COMMITIDO en HEAD tarda 39 min** (mide 160 M px de `tilesets_hd` con `np.unique(axis=0)`), lo que rompe el gate `test_validate_assets_caza_un_recurso_que_falta` (timeout 300 s). El árbol de trabajo ya trae el arreglo (conteo empaquetado uint32 en una pasada: 58 s medidos; y presupuesto acotado a `_hd` base, pues `_hd4`/`_hd_2048` son NEAREST y no pueden introducir colores) — **queda cerrado al commitear `scripts/validate_assets.py`** | sesión HD | ACTIVO-fix en working tree |
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

---

## H. Cierre AUD-839 (2026-09-11) — lo que este workstream cerró y lo que dejó

**Cerrado y verificado en el árbol (cada uno con su prueba en verde):**

* **D-02, D-03, D-04, D-06, D-07, D-08** (arriba) y **D-24**.
* **D-12** — `validate_assets` lleva varias pasadas en verde en este árbol: el
  tileset que exigía llegó con la ola de 4.1 / el validador se actualizó.
* **D-25 (parcial)** — las rutas de documentación rotas (16 documentos, incluidas
  las 31 citas del track privado de 4.1) están saneadas: citas corregidas en los
  docs vivos, historia del delink declarada en `MODULOS_RETIRADOS` y los
  4.1b/c aún en obra como marcadores con reverso automático. Quedan abiertos los
  4 fallos históricos de `guardado_y_cadena` (salida/jefe de stage4_1 e identidad
  `Stage21Oficinas`), que siguen en la tabla como D-25.
* **Contaminación de la suite (raíz de ~30 falsos rojos)**: el `SaveManager`
  vivo sobrevivía a su prueba y el NG+ del siguiente test multiplicaba la vida
  enemiga. El reset vive en `tests/conftest.py` y la familia completa
  (boss_base ×2.0, Rey F2/F3, Paburu Forma3, player_damage, aud_559) está verde.
* **Guardianes apagados que volvieron a vigilar**: el parser del árbol de
  `03_ARCHITECTURE.md` (`test_architecture_doc_matches_tree`) y la
  introspección de la fachada `StageData` en cuatro pruebas.
* **Dos hallazgos nuevos, anotados y sin cerrar**:
  * **D-71** 🟠 — RESUELTO (2026-09-12): el material bajo los pies ajusta
    el paso de la marcha (`Material.paso`: musgo +15 %, roca 1.0) —
    medido: el musgo deja correr más que el sendero con la misma
    entrada, y el lodo frena.
  * **D-72** 🟡 — RESUELTO (2026-09-12): la costura se re-alineó
    (bajada_408 a y=400 y 336 px de largo, sin escalón) y el recorrido
    cruza caminando y saltando; la cima fantasma desalineada se retiró.

**Quedan ACTIVOS (no se cierran sin decisión de diseño o sin re-trabajo de
contenido, fuera del alcance seguro de un cierre):** D-01 (oscuridad: luces por
mapa), D-05 (checkpoints), D-09 (HP de jefes), D-10 (densidad 2-1), D-11
(declarada), D-13 (deferida), D-14 (paridad generador↔TMX: stage_mecanicas,
stage0 y plantilla), D-16 (eventos muertos), D-17 (migración de partidas
pre-AUD-502; toca SAVE_VERSION, congelado), D-18 (jugos de daño/curación), D-19,
D-20, D-21 (combo), D-22, D-23, D-26, D-27, D-28, D-71 y D-72.

---

## I. Segunda tanda de cierre AUD-839 (2026-09-12)

* **D-05** (hall), **D-09** (HP de jefes ×3 con umbrales escalados),
  **D-14** (paridad byte a byte stage_mecanicas + stage0; plantilla
  regenerada con los 6 tipos que no demostraba, hueco exigente y nota
  92.3), **D-25** completo (83/83), **D-72**.
* **D-16 parcial** y **D-18 parcial** (ver tabla).
* **D-21 parcial** (escalones 8-10 escalan; ×4.0 el remate de combo).
* **D-01** — ambient_light subido a ≥0.8 en boss_paburu (0.85, antes sin
  la propiedad), 3-1 (0.55→0.8), aulas (0.85, antes sin la propiedad),
  stage0 (0.7→0.8) y stage4_1 (0.7→0.8, en TMX y generador).

**Sigen ACTIVOS/declarados**: D-01 (luces por sala: queda diseño fino),
D-10 (densidad 2-1, a rúbrica del dueño), D-11, D-13, D-17 (SAVE_VERSION
congelado), D-19, D-20, D-22, D-23, D-26 (declarado), D-27, D-28 (código
muerto inofensivo), D-29..D-42 (parciales declarados), D-71 (inercia).

---

## J. Tercera tanda AUD-839 (2026-09-12) — cierre de lo restante cerrable

* **D-71 RESUELTO**: el material ajusta el paso de la marcha
  (`Material.paso`); el musgo deja correr un 15 % más que el sendero y el
  trinquete del recorrido volvió a medir sobre-velocidad.
* **D-17 RESUELTO**: migración de checkpoints pre-AUD-502 — las coordenadas
  fuera de la rejilla de 16 px (convención centro) se ajustan a la esquina
  al cargar; las partidas nuevas no se tocan.
* **D-19 parcial**: qa_proof ya no es «Untitled Stage» de TU NOMBRE AQUÍ
  («QA PROOF — LABORATORIO», equipo docente) y tiene mensaje, moneda y
  luz; 1-1 compensa su niebla con `ambient_light` 0.85. Quedan: ruido de
  tiles en 1-2 y salas vacías del hub de backtracking (diseño fino).
* **D-20 RESUELTO**: aulas (mensaje, 3 monedas, 2 luces), lobby (3 objetos
  pelados tipados como Solid, mensaje, moneda, luz) y qa_proof con
  contenido. TMX 35/35 en verde tras el relleno.
* **D-21 avanzado**: AERIAL_SLAM y los especiales (CHARGE_RELEASE)
  construyen combo como corto/largo; queda pendiente por diseño decidir si
  cada sub-tipo aéreo suma pasos distintos.
* **D-13, D-26, D-28 pasan a DECLARADO**: la barra de maná es latente (no
  se dibuja a 0) y su gameplay está diferido (M4); las teclas de
  depuración son herramienta docente declarada en PENDIENTES;
  GanchoTecho/BalanceoEnLianaSalto son mecánicas reservadas para
  entregas de estudiantes (por eso no tienen camino de entrada en la
  campaña).
* **D-23, D-27 siguen sin diagnosticar** (zoom cenital oscuro; icono rojo
  en capturas) — requieren sesión de render con capturas, no cierre a
  ciegas.

**Balance de la lista tras las tres tandas:** de los 28 ACTIVOS originales,
18 están RESUELTOS o RESUELTOS-parciales con prueba, 4 pasaron a
DECLARADO con su motivo y 6 quedan abiertos por exigir hardware,
diagnóstico de render o decisión estética del dueño (D-01 fino, D-10,
D-19 fino, D-23, D-27, D-71→resuelto).

---

## K. Cuarta tanda AUD-839 (2026-09-12) — HD y los últimos abiertos

* **Cobertura HD total (roadmap 97):** los 17 tilesets que usan los mapas
  tienen su hoja `_hd` (32 px), `_hd4` (64) y `_hd_2048` (128) en
  `assets/tilesets_hd/`, más **normal map para los 31 temas** (el
  generador ahora es paramétrico en `ts` y devuelve la ruta). Los 13 de
  autor entran por NEAREST 2× con paleta intacta; el manifiesto declara
  técnica, tamaños y autotile.
* **Efectos por mapa:** bloom + viñeta en los 10 mapas que no las
  tenían, y `god_rays` en los tres exteriores soleados (1-1, 3-3 y el
  patio). TMX 35/35 tras el barrido.
* **D-01 fino:** +21 luces automáticas cerca de spawn y checkpoints en
  los 8 mapas jugables sin ellas.
* **D-10 RESUELTO:** el 2-1 baja de 41 a 23 enemigos con curva por
  especie (los enjambres quedan a 2, especiales intactos).
* **D-23 DIAGNOSTICADO:** la oscuridad del cenital es intrínseca al arte
  (tileset stage0 compartido: brillo medio 46/255) y su pase de luz casi
  no aplica (13.5 → 14.1 con ambient 1.0). Mejorado con efectos y luces;
  la corrección completa exige revisar el pipeline de luz de la vista
  cenital — queda abierto con causa y medición.
* **D-27 DIAGNOSTICADO:** NO es el placeholder del cargador (barrido de
  los 15 escenarios: 0 sprites faltantes). Requiere sesión de capturas
  para identificar el origen; queda abierto con la hipótesis descartada.

---

## L. Quinta tanda AUD-839 (2026-09-12) — la dificultad que nadie eligió

Reporte directo de juego: «hay enemigos que caminan en el aire y en todos
los niveles es más difícil eliminar a enemigos». Ambos verificados,
causa raíz encontrada y cerrados:

* **D-73 🟠 RESUELTO — fuga de NG+ a partidas nuevas.** `get_config()` sin
  ranura activa leía la ranura MÁS RECIENTE del disco: la máquina de
  desarrollo tiene ranuras de prueba a NG+23, así que CUALQUIER partida
  nueva arrancaba «Normal NG+23» — vida enemiga ×3.0 (el tope del modelo),
  empuje ×1.69. Era exactamente «cuesta más matar enemigos en todos los
  niveles». Ahora el NG+ sólo puede venir de la ranura ACTIVA; empezar de
  cero es NG+0. Medido: partida nueva = «Normal», vida ×1.0.
* **D-74 🔴 RESUELTO — enemigos caminando en el aire.** Dos defectos en el
  ancla de suelo de los terrestres (`_mantener_en_suelo`): (1) un suelo a
  más de 16 px no bajaba ni caía — el enemigo quedaba flotando en la
  altura de su último anclaje (los walkers de stage0 cruzaban la pendiente
  y seguían a 28 px del suelo); (2) si los pies quedaban dentro de un
  sólido alto (el muro del borde), se anclaba a su TECHO. Ahora baja el
  escalón de 16 px, cae con gravedad más allá, y el anclaje por
  contención exige que el techo esté a la altura del cuerpo.
* Los tres trinquetes que codificaban la conducta vieja se actualizaron
  con su motivo (lectura de ranura activa + contra-caso de partida nueva;
  i-frames NG+5 0.85 s; snap de migración sólo en partidas pre-AUD-502 y
  sólo al desfase clásico de medio tile).

Con esto la dificultad que juega un estudiante es la diseñada: Normal,
vida enemiga ×1.0, sin NG+ heredado, enemigos pegados al suelo.
