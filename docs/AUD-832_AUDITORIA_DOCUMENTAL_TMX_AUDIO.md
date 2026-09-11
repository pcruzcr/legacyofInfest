# Auditoría documental TMX + audio + enemigos (AUD-827–831)

> Fuente de verdad: código, tests, TMX y assets reales. La documentación nunca
> demuestra existencia. Etiquetas: VERIFIED / PARTIAL / DECLARED / DEBT /
> PREEXISTING / NOT IMPLEMENTED / OUT OF SCOPE.

## 0. Nota de nomenclatura (trazabilidad honesta)

El encargo pedía documentar el cierre de AUD-826–831. En `git log` el último
AUD es AUD-825 y no existen commits AUD-826–831; los cambios reales viven en
el árbol de trabajo con etiquetas AUD-828, AUD-829A, AUD-830, AUD-831 y
AUD-832A/B/C en comentarios y tests. Este documento cubre el **contenido**
pedido (stage2_2, stage3_1, stage_qa_proof, assets opcionales, SFX del
Gavilán, pipeline de niveles, BUG-826-08, deuda de combos) y mapea cada punto
a su evidencia real, sin inventar números de auditoría.

## 1. Estado por punto (VERIFIED)

### AUD-827 — `stage2_2`: `datacenter_ext` + `firstgid` (VERIFIED)

- `assets/maps/stage2_2/stage2_2.tmx`: `tileset_datacenter_ext`
  `firstgid=193`, `tilewidth=16`, `tileheight=16`, `tilecount=256`,
  `columns=16`, imagen `../../tilesets/tileset_datacenter_ext.png`
  `width=256 height=256`; `schema_version=1`.
- `assets/tilesets/tileset_datacenter_ext.png`: 256×256 px medidos con
  `pygame.image.load().get_size()`.
- `tileset_parqueo`: `firstgid=65`, `tilecount=128`, `columns=16` (ocupa
  65–192). El `firstgid=193` elimina el solape histórico (`firstgid=1` en
  HEAD solapaba 65–192).
- Estado histórico (HEAD): `tilecount=64`, `columns=8`, `128×128`,
  `firstgid=1`. No mantener esos valores como actuales.
- Documentos actualizados: `docs/niveles/06_STAGE_2_2.md`,
  `docs/AUD-800_REPOSITORY_INVENTORY.md` §4, `docs/38_STAGE_BOSS_GUIDE.md`
  §2.2 (regla general de `firstgid`).

### AUD-828 — `stage3_1`: `invenio_gothic_v5` + `DeathPit id=53` (VERIFIED)

- `assets/maps/stage3_1_la_entrada_de_piedra/stage3_1_la_entrada_de_piedra.tmx`:
  `tileset_invenio_gothic_v5` `firstgid=1`, `tilecount=4096`, `columns=64`,
  imagen `width=1024 height=1024` (ruta de autor
  `../../../student_assets/tilesets/…`, conservada: es material de estudiante).
- `DeathPit id=53` (`DeathPit_01`, x=872 y=616, 40×24) está en el grupo
  `Objects` (id=6). En HEAD estaba en `Collision` (id=7): ahí se pisaba como
  suelo sólido en silencio. Función actual: foso letal.
- Estado histórico: `tilecount=464`, `columns=8`, `128×928`. No mantenerlos
  como actuales.
- Documentos actualizados: `docs/niveles/09_STAGE_3_1.md`,
  `docs/AUD-800_REPOSITORY_INVENTORY.md` §4 (el WARN «`DeathPit` en
  `Collision`» queda superseded), `docs/38_STAGE_BOSS_GUIDE.md` §2.2
  (peligros en `Objects`, `Collision` sólo `Solid`/`Platform`), checklist §4
  (se corrige `Solid_OneWay` → `Platform`, contradicción con §2.2 y AUD-455).

### AUD-829 — `stage_qa_proof`: ruta y metadata (VERIFIED)

- `assets/maps/stage_qa_proof/stage_qa_proof.tmx` (fichero nuevo en el árbol,
  no está en HEAD): `tileset_stage0` `firstgid=1`, `tilecount=4096`,
  `columns=64`, imagen `../../tilesets/tileset_stage0.png`
  `width=1024 height=1024`.
- `assets/tilesets/tileset_stage0.png`: 1024×1024 px medidos.
- No mantener como actuales: ruta `../../assets/tilesets/…`, `16×16`,
  1 columna ni metadata ficticia.
- Documentos actualizados: `docs/AUD-800_REPOSITORY_INVENTORY.md` §4 (fila
  nueva: prueba interna, no entregable).

### AUD-830 — assets opcionales de enemigos: fallback silencioso (VERIFIED)

- Código: `src/framework/entities/enemy_buddies.py`,
  `enemy_flying.py`, `enemy_shooter.py`, `enemy_shielded.py`,
  `enemy_pez_abismal.py`, `enemy_parry_teacher.py`: hojas de zona opcionales
  ausentes se capturan con `try/except (pygame.error, FileNotFoundError,
  PermissionError)` y se usa reemplazo; comentarios `AUD-830`.
- Regla documental: `OPTIONAL MISSING ASSET` (ausencia esperada → fallback
  válido, no es error) ≠ `CORRUPTED / INVALID ASSET` (`[LOAD FAIL]`,
  `[COLOR BUDGET]`, WAV ilegible → sí se arregla).
- Documentos actualizados: `docs/ENEMY_CREATION.md` §7,
  `docs/38_STAGE_BOSS_GUIDE.md` §2.7 (cómo leer el grader).

### AUD-831 — `SFX_BOSSES_GAVILAN_DIVE` emitido (VERIFIED)

- `src/stages/stage3_4_boss_gavilan/boss_gavilan.py::_do_dive` emite
  `Events.BOSS_ATTACK` (pattern `DIVE`) y `Events.SFX_BOSSES_GAVILAN_DIVE`
  (`src/engine/core/events.py:139` define la constante).
- Test: `tests/test_audio_wiring.py` — la entrada salió de
  `AWAITING_THEIR_BOSS` (lista que sólo puede encoger).
- Sigue pendiente (DECLARED, jefe de estudiante no implementado):
  `SFX_BOSSES_GAVILAN_MASK_BEAM` (+ `PABURU_WAVE`, `RELIC_APPEAR`,
  `REY_SPIT`, `REY_SPLIT`: 5 huérfanos, eran 6).
- Documentos actualizados: `docs/52_EVENT_MAP.md` §2 (prosa) y §3 (tabla:
  6→5, fila DIVE eliminada), `docs/17_BOSS_SPEC.md` (nota de estado actual
  tras la cita histórica, sin reescribir la foto de 2026-08-04),
  `docs/87_REPORTE_DE_LO_QUE_FALTA.md` §8 («cinco» → «cuatro… (eran cinco)»),
  `docs/BOSS_CREATION.md` §6 (patrón emitir-no-sólo-existir),
  `docs/38_STAGE_BOSS_GUIDE.md` §3.7.

## 2. Pipeline real de creación de niveles (CURRENT, VERIFIED)

Fuente: `docs/STAGE_CREATION.md` (tablas + bloque GENERATED de
`scripts/generate_tmx_reference.py`), `docs/38_STAGE_BOSS_GUIDE.md`,
`docs/06_TMX_SPEC.md`, plantilla `student_templates/stage_template/`
(+ `tools/generate_stage_template.py`, que añade ejemplos `Slope`),
validadores y graders.

1. Copiar plantilla (`student_templates/stage_template/` → `src/stages/<id>/`
   + TMX en `assets/maps/<id>/<id>.tmx`).
2. En Tiled: ortogonal, 16×16, right-down, no infinito; 8 capas
   (`BG_Far/Mid/Near`, `Terrain`, `Terrain_Detail`, `Objects`, `Collision`,
   `FG_Overlay`).
3. Propiedades de mapa: `schema_version=1`, `stage_id`, `stage_name`,
   `time_limit`, `bgm_track` (fichero real de `assets/music/`).
4. Tilesets: dimensiones/columnas/fichas = PNG real; `firstgid` encadenado
   sin solapes (§1, regla AUD-827); ruta relativa al TMX.
5. `Collision`: sólo `Solid`/`Platform`. `HazardZone`/`DeathPit` van en
   `Objects` (en `Collision` son suelo sólido silencioso).
6. `Objects`: `PlayerSpawn` (1, la Y son los pies), `Checkpoint`
   (`checkpoint_id`), `NextTrigger`, enemigos por `type` registrado,
   hazards, `CameraLock`, `Light`, etc. (tabla GENERATED en STAGE_CREATION).
7. Jefes: clase `BossBase` + cada ataque emite su SFX (§1 AUD-831).
8. Validar: `validate_tmx.py --ci`, `validate_assets.py`,
   `grade_stage.py … --json`, `grade_boss.py … --json`,
   `check_translations.py --ci` si hay textos.
9. Jugar: `python main.py --stage <id>` / `--boss <id>`; tests
   `pytest tests/ -k <id>`. Sin pantalla:
   `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYGAME_HIDE_SUPPORT_PROMPT=1`.
10. Leer el grader con la regla OPTIONAL vs CORRUPTED (§1 AUD-830).

Guía «desde cero hasta el TMX»: `docs/38_STAGE_BOSS_GUIDE.md` §§2.2–2.7 y
3.7 (ampliada en esta auditoría); referencia completa:
`docs/STAGE_CREATION.md`; formato: `docs/06_TMX_SPEC.md`.

## 3. Arquitectura y rendering (CURRENT, VERIFIED)

`src/engine/core/settings.py:19-20,52` (`INTERNAL_WIDTH=1280`,
`INTERNAL_HEIGHT=720`, `TILE_SIZE=16` → viewport 80×45),
`src/engine/core/display.py` (escala aspect-preserving + letterbox, FBO
1280×720). Sin cambios en esta auditoría: `AUD-800_MASTER_SPECIFICATION.md`,
`AUD-803/804/805` y `AUD-800_REPOSITORY_INVENTORY.md` §6 ya declaran esos
valores sin contradicción.

## 4. Deudas (estado 2026-09-09 tras AUD-837/AUD-838)

- **BUG-826-08 / `stage_mecanicas.tmx` vs generador — RESUELTO (AUD-838).**
  `tools/generate_stage_mecanicas.py` ya emite la sala del muro (2 `Solid` +
  2 `Platform` + mensaje 919, misma geometría y texto del TMX; verificado
  generando a memoria). El TMX entregado no se tocó.
- **Deuda de aislamiento de combos.** Mencionada en el encargo; no se encontró
  evidencia concreta en código/docs del árbol (sin símbolo, test ni GAP que la
  describa). Se registra como DECLARED-sin-evidencia: no se documenta como
  VERIFIED ni se inventa alcance. Si aparece evidencia (símbolo/test/GAP),
  ampliar este apartado.
- **Test con conteo TMX fijo — RESUELTO (AUD-837):** exige 35/35.
- **Regresión `tests/test_boss*.py` — RESUELTO (AUD-837):** era el glob
  literal en Windows (exit 4), no código roto; lista explícita + mismo arreglo
  en STATE/SAVE/VFX. `check_change_safety --ci`: 15/15 PASS. Extra:
  `test_boss_spawn_desde_tiled` fallaba hasta en HEAD limpio (`BossSpawn_915`
  demo desde AUD-753): excepción documentada sólo para ese objeto.

## 5. Contradicciones corregidas en esta auditoría

1. `AUD-800_REPOSITORY_INVENTORY.md`: `stage2_2` «falta `schema_version`» →
   PASS con metadata AUD-827 (el TMX declara `schema_version=1`).
2. Ídem: `stage3_1` WARN «`DeathPit` en `Collision`» → PASS (AUD-828, en
   `Objects`).
3. `52_EVENT_MAP.md` §2: «los otros seis siguen sin emisor» → cinco (DIVE
   emitido, AUD-831); §3: tabla 6→5 huérfanos.
4. `17_BOSS_SPEC.md`: cita histórica «DIVE y MASK_BEAM esperan su emisor» →
   nota de estado actual (DIVE emitido; MASK_BEAM pendiente).
5. `87_REPORTE_DE_LO_QUE_FALTA.md` §8: «cinco sonidos» → cuatro (+ nota).
6. `38_STAGE_BOSS_GUIDE.md` §4: checklist `Solid_OneWay` → `Platform`
   (contradecía §2.2 y AUD-455; `Collision` sólo admite `Solid`/`Platform`).

## 6. Referencias rotas / huérfanas revisadas

- `stage_qa_proof`: era fichero nuevo sin fila documental → fila añadida en
  inventario (no es referencia rota, era ausencia documental).
- `../../../student_assets/tilesets/tileset_parqueo.png` y
  `…/tileset_invenio_gothic_v5.png`: rutas de autor fuera del repo,
  conservadas a propósito (material de estudiante); el validador las trata
  como externas, no como rotas del motor.
- `docs/75_BIBLIA_TECNICA.md` §SFX: catálogo completo, no lista de huérfanos;
  no requería cambio (la lista de huérfanos vive en `52_EVENT_MAP.md` §3).
- Índices: este documento se indexa en `docs/00_MASTER_INDEX.md`; no se
  inventan rutas.

## 7. Evidencia por punto

| Punto | Archivo | Símbolo / valor |
|---|---|---|
| 827 | `assets/maps/stage2_2/stage2_2.tmx:22-27` | `datacenter_ext firstgid=193 tilecount=256 columns=16 256×256`; `parqueo firstgid=65 tilecount=128`; `schema_version=1` |
| 827 | `assets/tilesets/tileset_datacenter_ext.png` | 256×256 (`pygame.image.load().get_size()`) |
| 828 | `assets/maps/stage3_1…/stage3_1….tmx:20-21,324,429,431` | `invenio_gothic_v5 1024×1024 64 col 4096`; `id=53 DeathPit` en `Objects` (id=6), `Collision` es id=7 |
| 829 | `assets/maps/stage_qa_proof/stage_qa_proof.tmx:17-19` | `tileset_stage0 1024×1024 64 col 4096`, `source=../../tilesets/tileset_stage0.png` |
| 829 | `assets/tilesets/tileset_stage0.png` | 1024×1024 |
| 830 | `src/framework/entities/enemy_{buddies,flying,shooter,shielded,pez_abismal,parry_teacher}.py` | `try/except (pygame.error, FileNotFoundError, PermissionError)` + comentario `AUD-830` |
| 831 | `src/stages/stage3_4_boss_gavilan/boss_gavilan.py:161-163` | `emit(Events.SFX_BOSSES_GAVILAN_DIVE, …)` en `_do_dive` |
| 831 | `src/engine/core/events.py:139` | `SFX_BOSSES_GAVILAN_DIVE = "SFX_BOSSES_GAVILAN_DIVE"` |
| 831 | `tests/test_audio_wiring.py` (`AWAITING_THEIR_BOSS`) | DIVE fuera de la lista (sólo puede encoger) |
| BUG-826-08 | `assets/maps/stage_mecanicas/stage_mecanicas.tmx` vs `tools/generate_stage_mecanicas.py:471` | `nextobjectid=923` vs `"900"` fijo; objetos 916–921 manuales |
| Render | `src/engine/core/settings.py:19-20,52`, `src/engine/core/display.py` | 1280×720, TILE 16, 80×45, letterbox, FBO |
