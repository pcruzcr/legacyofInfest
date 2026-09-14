# Auditoría documental total — todo el proyecto (2026-09-09)

> Mismo método que `docs/AUD-832_AUDITORIA_DOCUMENTAL_TMX_AUDIO.md`: la fuente
> de verdad es código → tests → TMX/assets → scripts → auditorías verificadas
> → documentación. Etiquetas: VERIFIED / PARTIAL / DECLARED / DEBT /
> PREEXISTING / NOT IMPLEMENTED / OUT OF SCOPE / HISTORICAL.
>
> Este documento cubre **toda** la documentación y **todo** el proyecto. El
> detalle TMX/audio/enemigos vive en el doc AUD-832 y no se repite aquí.

## 1. Valores reales medidos (todos VERIFIED, con método)

| Dato | Valor | Método |
|---|---|---|
| Tests recogidos | 6378 | `pytest --collect-only -q` |
| Constantes `SFX_*` | 49 (+ `MUSIC_STINGER` aparte) | conteo en `src/engine/core/events.py` |
| Constantes `Events` totales | 83 | conteo en `events.py` |
| Tipos objeto base limpia | 106 en `Objects` (51 + 55) + 2 `Collision` = 108 declarables | `check_tmx_coverage.py --ci` («18 propiedades y 108 tipos») + `STAGE_CREATION.md` GENERATED («106») |
| Tipos objeto runtime descubierto | 120 en `Objects` (51 + 69), 122 con `Collision` | `StageLoader._entity_registry` (69 tras `discover_stages()`) |
| Entidades registradas base | 55 (54 en HEAD; el +1 es `ParryTeacher`, verificado por diff de claves contra worktree de HEAD) | `ensure_registered()` en intérprete limpio |
| Especies bestiario | 35 | `len(bestiary_registry.SPECIES)` |
| Estados jugador | 30 | `PlayerState` en `player.py` |
| Propiedades de mapa | 18 | `PROPIEDADES_MAPA` en `check_tmx_coverage.py` |
| TMX validados | 35/35 (`34` en `assets/maps` + plantilla) | `validate_tmx.py --ci` |
| Directorios `src/stages` | 35 (sin `__pycache__`; `stage2_4` sin mapa propio) | listado del árbol |
| Directorios `assets/maps` | 34 | listado del árbol |
| Resolución interna | 1280×720, TILE 16, viewport 80×45, FBO 1280×720, letterbox | `settings.py:19-20,52`, `display.py` |
| Paso fijo | 120 Hz (`FIXED_DT = 1/120`); meta 60 FPS estables | `settings.TARGET_FPS`, `clock.py:79`, comentario en `settings.py` |
| Gravedad | 800 px/s² | `settings.GRAVITY` |
| Jefes calificados | 4/4 al 100 % | `grade_boss.py --json` (venado, paburu, rey, gavilán) |
| Fondos stage0 | 1280×720 / 2560×720 / 3840×720 | `pygame.image.load().get_size()` |
| Items `_ITEM_DEFS` | incluye `heart_piece`, `pokeball`, `skill_coraza` (−25 %, botín del Gavilán), `subweapon_dagger`, `sun_song` | `inventory.py`, `player.py`, `crafting.py` |

## 2. Correcciones aplicadas en esta auditoría

### Resolución 800×600 → 1280×720 (AUD-754 supersedes AUD-455)

| Documento | Cambio |
|---|---|
| `08_SYLLABUS_MAPPING.md` | Búfer interno y entregable: 1280×720 (era 800×600) |
| `09_HUD_SPEC.md` | Factor 2,5 → 4,0 (1280/320); tabla medida pre-AUD-754 marcada como histórica; cabecera |
| `20_ASSET_BIBLE.md` | Nota AUD-455 + estándar + §8 (fondos stage0 con tamaños medidos) + tabla |
| `23_DATA_SCHEMAS.md` | Fila «Espacio de pantalla» + nota de supersede |
| `35_USER_MANUAL.md` | Nota de supersede + diagrama 1280×720 |
| `64_GAME_DESIGN_DOCUMENT.md` | Interna 1280×720 |
| `66_GUIA_DE_LEVEL_DESIGN.md` | Pantalla 1280 px; equivalencias de scroll recalculadas (÷1280) |
| `74_TUBERIA_DE_GPU.md` | Medidas Intel HD 530 marcadas HISTORICAL; referencia vigente: Quadro M2200 (`CLAUDE.md`) |
| `75_BIBLIA_TECNICA.md` §7.1 y §21.1 | 1280×720; núcleo «@60 FPS estables (paso fijo 120 Hz)» |
| `92_CATALOGO_DE_FENOMENOS.md` | 1280×720 |
| `60_GUIA_COMPLETA_DEL_MOTOR.md` §1 | 1280 × 720 a 120 FPS (con meta 60 estables); gravedad verificada |

### Conteos

| Documento | Cambio |
|---|---|
| `50_IMPROVEMENT_ROADMAP.md` | 65→55 tipos; `validate_tmx` 22/22→35/35 |
| `60_GUIA_COMPLETA_DEL_MOTOR.md` | §1/§4/§6/TOC: 122 tipos runtime (51+69+2), 69 enemigos, 18 props; `IndoorZone`, `BruteOficinas`/`ChargerOficinas`/`Dron04`, 5 items de inventario añadidos (los exigía `test_guia_del_motor.py`: **22/22 pasa**) |
| `75_BIBLIA_TECNICA.md` | SFX 39→49 + 10 emisores + nota de recontado; enemigos 65→55; TMX 120/122/108 |
| `73_CATALOGO_DE_RECURSOS_PARA_ESTUDIANTES.md` | Events 60→83; SFX 41→49 |
| `95_GUIA_ENTREGA_3_MADURA.md` | FSM 28→30 estados |
| `STAGE_CREATION.md` | 65→55 tipos (69 con descubiertos) |
| `62_ESTADO_DEL_PROYECTO.md` | 120/122/106/108 tipos; 55 enemigos; 35 dirs / 34 mapas; 6378 tests; tabla de dominios |
| `97_ROADMAP_PS4_HD_2D_2_5D.md` | 65→55 tipos (2×) |
| `87_REPORTE_DE_LO_QUE_FALTA.md` | Cinco→cuatro sonidos (2× restantes) |
| `17_BOSS_SPEC.md` | Nota: hoy 4/4 jefes al 100 % (la de 45 % queda histórica) |
| `README.md` | 108 tipos / 55 enemigos; quickstart `pip install -e ".[dev]"` (única recomendada) |
| `AUD-800_PACING_MATRIX.md` | stage2_2 120×50 (era «30×60»); DeathPit 53 en `Objects`; mecanicas 122 tipos |
| `09_STAGE_3_1.md` | Referencia 160×45 real (era «100×38»); contradicción de altura declarada abierta |

## 3. Deudas técnicas detectadas (estado 2026-09-09 tras AUD-837/AUD-838)

Resueltas en esta pasada:

1. ~~`test_el_inventario_cuenta_bien.py` exigía 119/54/105/107~~ — **RESUELTO
   (AUD-837):** test actualizado a 120/55/106/108/69 (el +1 es `ParryTeacher`).
2. ~~`tests/test_boss*.py`: change-safety 14/15~~ — **RESUELTO (AUD-837):**
   causa raíz: globs literales `test_boss*.py` que cmd.exe no expande (exit 4),
   mismo modo de fallo de AUD-832C. Lista explícita de los 7 ficheros;
   de paso, mismo arreglo en STATE/SAVE/VFX (`test_state_integration.py`,
   `test_persistence*.py` y `test_vfx*.py` no existen). Hoy **15/15 PASS**.
   Hallazgo adicional real: `test_boss_spawn_desde_tiled.py` fallaba también
   en HEAD limpio (objeto demo `BossSpawn_915` en `stage_mecanicas` desde
   AUD-753): el test permitía cero usos y el mapa demo trae uno a propósito —
   excepción documentada sólo para id 915/`BossVenado`, el guardarraíl sigue
   vigilando el resto. Verificado que falla en HEAD y pasa tras el arreglo.
3. ~~`test_doc_code_contract_post812.py` exigía «34/34»~~ — **RESUELTO
   (AUD-837):** 35/35 (`stage_qa_proof`).

Pendientes (no subsanables sin código/diseño/TMX):

4. **BUG-826-08** — **RESUELTO (AUD-838):** `tools/generate_stage_mecanicas.py`
   ya emite la sala del muro (2 `Solid` + 2 `Platform` + mensaje 919, misma
   geometría y texto del TMX; verificado generando a memoria: 18 entradas de
   `Collision`). El TMX entregado no se tocó.
5. **Aislamiento de combos**: DECLARED-sin-evidencia en el árbol.
6. **`09_STAGE_3_1.md` regla «altura 224 px» vs TMX 160×45 (720 px).**
   Contradicción diseño↔artefacto abierta; necesita decisión de diseño.

## 4. Clasificación histórica (no se toca)

- Auditorías y certificaciones fechadas (`AUD-757–760`, `AUD-800_*`, `AUD-803/804/805`, `HYBRID_RENDERER_RC_CERTIFICATION` con «6323», `AUDIT_2026-07`, `NATIVE_*`, `VISUAL_*`, `PIXEL_PERFECT_*`, `HISTORICAL_BUG_REGRESSION`): registros de su fecha; donde una cifra suya quedó superada se añadió nota de supersede en el documento **vivo** correspondiente, no en el registro.
- `93_AUDITORIA_ESTRATEGICA_Y_FODA.md` («trasladada a 800×600»): describe estilo histórico; se conserva.
- Citas `<!-- cita-historica -->` y notas AUD-455: se conservan y se les añade supersede, nunca se reescriben.
- `87_REPORTE_DE_LO_QUE_FALTA.md` §7/§19: la mención a 61 retirada ya estaba anotada con sucesor; OK.
- Único script citado inexistente: `scripts/audit_certification_consistency.py`, ya clasificado TEMPORAL en el inventario; OK.

## 5. Verificación ejecutada

- `generate_tmx_reference.py --check`: al día. `check_tmx_coverage.py --ci`: correcta (18 props, 108 tipos).
- `validate_tmx.py --ci`: 35/35. `check_translations.py --ci`: en orden.
- `pytest test_guia_del_motor.py`: **22/22** (antes 16/22: 6 fallos preexistentes corregidos vía docs).
- `pytest test_audio_wiring + test_el_indice_maestro_cuenta_bien + test_documentacion_en_espanol`: 19 passed.
- `test_el_inventario_cuenta_bien.py`: 3/3 (tras AUD-837).
- `grade_stage.py` 2_2/3_1/qa_proof + `grade_boss.py` ×4: ver §1.
- `check_change_safety.py --ci`: 15/15 PASS (tras AUD-837; antes 14/15 por el glob literal de BOSS en Windows).
- Greps finales: sin «65 tipos», sin «800×600» como vigente, sin DIVE huérfano, sin `Solid_OneWay` en checklist.

## 6. Certificación documental

`DOCUMENTATION VERIFIED WITH MINOR DEBT` — toda afirmación documental con evidencia queda alineada al árbol; las 2 deudas restantes (combos sin evidencia, altura 224 px de 09) no son subsanables sólo con documentos. Trazabilidad AUD preservada (supersede, nunca reescritura).

> **Deuda de coordinación (2026-09-09, fuera de este lote).** Un workstream
> paralelo añadió `docs/100_VERIFICACION_DE_BUGS_REPORTADOS.md` asignando
> AUD-826 a AUD-829 a otros temas (menús, lentitud, flotantes, ruido), mientras
> el encargo de esta auditoría usaba AUD-827–831 para TMX/audio. Los números
> corren riesgo de colisión al commitear; conviene pactar el reparto antes del
> merge. Este lote usa AUD-837/AUD-838, sin colisión con ninguno.
