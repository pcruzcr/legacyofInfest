# STAGE 4-1 — ESPECIFICACIÓN TÉCNICA (AUD-814 + AUD-815)

Contrato exacto entre diseño, TMX, código y pruebas. Si algo aquí y el
mapa discrepan, uno de los dos está mal y `tests/test_stage4_1.py` dice
cuál.

## 1. Trazado (`src/stages/stage4_1/trazado.py`)

TS 16 · secciones 160 · MW 960 · MH 40 · suelo fila 32 (y 512) · muros 2.
Fases en columnas 0/160/320/480/640/800. Elevaciones (subida, cima 0,
bajada, fila cima): repiso (288,8,0,8,28), loma baja (350,26,0,14,27),
loma alta (408,24,0,18,24). Fricción: sendero 8–148, musgo 190–229 y
285–309 (inercia 0.15), lodo 240–279 (×0.88), polvo 650–790.

Columnas: spawn 8 · checkpoints 12/172/332/492/652/812/932 · lápidas
44/50 · diálogos 215/340/578 · altares 235/466/598 · silencio 560 ·
canto 700 · mirador 905 · portal 945 · luces 820–940 paso 10 (13) ·
piras 500/522/544 · antorchas 830/860/890/920 · aviso de cima 280.

## 2. Fases (`src/stages/stage4_1/fases.py`)

Seis `Fase` con clima, partículas, gradación 3×3, tinte, espíritu,
rayos/min, ambiente, flags (slopes, shake, luna, grietas), ambiente
(`sfx/environment/amb_stage41_fN.wav`), música (`mus_stage41_fN`),
diálogo y decoración. Gradación interpola por avance (×4: la fase se
establece en el primer cuarto); tinte funde en el primer tercio.

## 3. TMX (`assets/maps/stage4_1/stage4_1.tmx`, `tools/generar_stage41_tmx.py`)

8 capas requeridas, todas con contenido (prohibido el layer vacío).
Tilesets `tileset_stage41_f1..6` (firstgid 1/257/…/1281).
Propiedades: `stage_id`, `bgm_track=mus_stage41_f1`, `zone=4`,
`climate=clear`, `start_hour=10`, `day_length=3600`, `cielo=true`
(obligatoria: sin ella el motor anula el clima por “interior”),
`ambient_light=0.70`, `bloom=0.30`, `vignette=0.40`.

Objetos: PlayerSpawn 1 · Cutscene 2 (intro + mirador) · Checkpoint 7 ·
MessageTrigger_Once 9 (5 diálogos + canto + mensaje final + cuenta) ·
EventTrigger 3 (`altar_*`, no automáticos) · Slope 9 (6 rampas + 3 cimas
llanas) · FrictionZone 5 · WindZone 1 (F3, −50 px/s) · Light 13
(`#6EFF96`, intensidad 0) · WarpZone 1 (`boss_paburu`,
`key_id=paburu_despertado`, no automático). Sin `DeathPit`, sin
`NextTrigger` (decisión documentada en diseño §7).

## 4. Datos (`data/dialogues/stage4_1.json`)

Árboles `venado`, `serpiente`, `halcon` (2 nodos, cierre = ascender),
`campanero`, `maestra` (Jhon/Jin). Retrato (`sprites/portraits/*.png`) y
voz (`sfx/voz/sfx_voz_*`, con ducking del motor) por nodo donde existe
arte: venado, rey_terciopelo (la Serpiente), gavilán (el Halcón), jhon.
Jin va sin retrato (sin arte en el repo). Formato del
`DialogueTree.desde_datos` que carga `cinematicas.py`.

## 5. Escena (`src/stages/stage4_1/stage4_1.py` + `espiritus.py`)

`Stage4_1(StageScene)`, STAGE_ID `stage4_1`, ZONE 4. Usa sólo APIs del
motor: `_cambiar_clima`, `set_effect`, `_ambiente_base`, `set_color_grading`,
`set_tint`, `set_vignette`, `flash`, `apply_shake`, `play/crossfade/stop`
de ambiente y música, `_play_sfx_spatial`, `Llavero.coger/tiene`,
`FLAG_SET`→`context.banderas`, fondos en `background_layers` +
`background_factors`, `LightSource.intensity`, `SHOW_MESSAGE`.

Estado: `_fase_actual`, `_liberados[3]`, `_dialogo_visto`,
`_ascensiones`, silencio (6 s), luna (8 s, 0.45–0.75, ×(1−0.65·nube)),
grietas (90 px), trueno (0.2–1.5 s), piras [3], caza, antorchas (4 en
orden), templo (10 pasos), transiciones anticipadas (16 cols). Re-otorga
llaves desde banderas al reentrar.

## 6. Banderas y llaves

Llaves (`Llavero`, por sesión): `espiritu_venado/serpiente/halcon`,
`paburu_despertado` (derivada: las tres). Banderas (`context.banderas` →
save): `stage4_1.spirit_{venado,serpiente,halcon}_released`,
`stage4_1.paburu_awakened` (PABURU_AWAKENED real, no comentario).

## 7. Audio (`tools/generar_stage41_audio.py`)

PCM 16 bit mono 22050 Hz. 6 músicas (~15 s, bucle), 6 ambientes (~11 s,
bucle) + cama de fuego `amb_stage41_fuego.wav`, 6 efectos (`s41_trueno/
despertar/liberacion/paso_luz/golpe_silencio/grito_halcon`). Pico
~−6 dBFS. Voces de espíritus: las del motor (`sfx/voz/sfx_voz_*`).

## 8. Activos (`tools/generar_stage41_activos.py`)

6 tilesets 256×256 (índices §3 del generador; base negra = transparente)
+ 18 fondos 1280×720 (`stage41/f{N}_{far,mid,near}`). Paletas por fase;
techo de color muy por debajo de `validate_assets.py`.

## 9. Pruebas

`tests/test_stage4_1.py` (44: TMX, trazado, audio, diálogos) +
`tests/test_stage41_recorrido.py` (20: fases, física con entrada real,
silencio, luna, grietas, liberaciones, persistencia). Harness:
teletransporte + salto de cutscenes + drenado del bus + cierre de
diálogos + mando simulado (todo documentado en el fichero).
Evidencia: `tools/capturar_stage41.py` (26 shots + perf).
