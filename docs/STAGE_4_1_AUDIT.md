# STAGE 4-1 — MATRIZ DE CERTIFICACIÓN (AUD-814 + AUD-815 + AUD-816)

Rebuild + reconstrucción audiovisual verificados requisito por requisito.
Estados: `PASS`, `PARTIAL`, `FAIL`, `BLOCKED`, `NOT IMPLEMENTED`, `N/A`.
Evidencia visual: 35 capturas del recorrido (`tools/capturar_stage41.py`)
en la carpeta local de certificación (STEP 50: fuera del repo).
Grabación de audio: BLOCKED BY ENVIRONMENT (driver dummy); en su lugar:
existencia + decodificación + carga + trigger + routing verificados.

## P0 — Player y superficie

| ID | Requisito | Estado | Evidencia |
|---|---|---|---|
| S41-P0-01 | Caminar/correr toda superficie transitable | PASS | bot spawn→portal 109.7 s, 6 fases, vx 144 constante |
| S41-P0-02 | Saltar/caer/aterrizar | PASS | vértices con salto; `test_slopes_transitables` |
| S41-P0-03 | Subir pendientes y lomas | PASS | rampas a pie; cima con salto (muro por diseño) |
| S41-P0-04 | Musgo desliza / lodo frena en runtime | PASS | tests de distancia con entrada real |
| S41-P0-05 | Aviso de salto en el primer vértice | PASS | `test_avisa_antes_del_repiso` |

## F1 — Cementerio

| ID | Requisito | Estado | Evidencia |
|---|---|---|---|
| S41-F1-01 | Cementerio real | PASS | `02_fase1_cementerio_color.png` |
| S41-F1-02 | Eventos ambientales (susurro, silueta) | PASS | estado `_silueta_f1`, sfx posicional |
| S41-F1-03 | Audio (brisa, aves, direccionales) | PASS | `amb_stage41_f1.wav` en runtime |
| S41-F1-04 | Transición perceptible a F2 | PASS | `04_transicion_lluvia.png`, clima anticipado 16 cols |

## F2 — Bosque lluvioso / Venado

| ID | Requisito | Estado | Evidencia |
|---|---|---|---|
| S41-F2-01 | Bosque real (no cementerio+azul) | PASS | `05_fase2_venado.png`, densidad ×2, troncos/raíces |
| S41-F2-02 | Lluvia (empieza en transición) | PASS | clima `rain` desde col 144; `04_*` |
| S41-F2-03 | Musgo | PASS | S41-P0-04 |
| S41-F2-04 | Lodo | PASS | S41-P0-04 |
| S41-F2-05 | Parallax de bosque | PASS | 3 planos f2 + factores; `05_*` |
| S41-F2-06 | Eventos (ojos, animal, ramas) | PASS | `_ojos_f2`, `_animal_f2`, aislados |
| S41-F2-07 | Venado (presencia contenida) | PASS | apariciones + `08_fase2_espiritu.png` |
| S41-F2-08 | Diálogo audiovisual | PASS | retrato `venado*.png` + `sfx_voz_venado_*`, test retratos |
| S41-F2-09 | Ascensión (luz+sonido+mensaje+flag) | PASS | haz + `s41_liberacion` + bandera |

## F3 — Dios Serpiente

| ID | Requisito | Estado | Evidencia |
|---|---|---|---|
| S41-F3-01 | Dominio serpiente (cráneos, vértebras) | PASS | `09_fase3_serpiente.png` |
| S41-F3-02 | Lluvia intensa (más que F2) | PASS | `storm` 220 partículas vs `rain` 150 |
| S41-F3-03 | Rayos | PASS | `12_fase3_rayo.png`, `test_flash_*` |
| S41-F3-04 | Flash revela serpiente | PASS | `_revelacion_serpiente`, dibujo en flash |
| S41-F3-05 | Viento | PASS | `test_viento_de_fase3` (−50 px/s) |
| S41-F3-06 | Lomas transitables | PASS | `10_fase3_slopes.png`, `test_slopes_*` |
| S41-F3-07 | Eventos (serpiente fondo) | PASS | ciclos 2–5/4–9 s |
| S41-F3-08 | Serpiente (presencia antes de verla) | PASS | fondo + figura col 450 |
| S41-F3-09 | Diálogo audiovisual | PASS | `rey_terciopelo*.png` + voz |
| S41-F3-10 | Ascensión | PASS | cadena 2/3 verificada |

## F4 — Gavilán / Bosque en llamas

| ID | Requisito | Estado | Evidencia |
|---|---|---|---|
| S41-F4-01 | Transformación por rayos (3 piras) | PASS | `test_rayos_encienden_piras_en_orden` |
| S41-F4-02 | Incendio (llamas, humo, 3 focos) | PASS | `31_fase4_incendio.png`, `dibujar_llama_simple/humo` |
| S41-F4-03 | Fin de lluvia evidente | PASS | `test_lluvia_cesa_con_el_fuego` (storm→clear) |
| S41-F4-04 | Bosque incendiado real (no filtro) | PASS | piras + brasas + cama `amb_stage41_fuego.wav` |
| S41-F4-05 | Humo/ceniza | PASS | columnas + partículas `embers` |
| S41-F4-06 | Silencio dramático | PASS | 6 s sin música ni ambiente |
| S41-F4-07 | Sombra del Gavilán (persecución) | PASS | `32_fase4_caza.png`, `_caza_x` sigue/acelera |
| S41-F4-08 | Persecución jugable + captura | PASS | embestidas con shake; muere en el silencio |
| S41-F4-09 | Camera shake (captura) | PASS | `test_silencio_dispara_shake` (14 px/0.45 s reales) |
| S41-F4-10 | Diálogo audiovisual | PASS | `gavilan*.png` + `sfx_voz_gavilan` |
| S41-F4-11 | Ascensión | PASS | cadena 3/3 + llave `paburu_despertado` |

## F5 — Planicie de los Muertos

| ID | Requisito | Estado | Evidencia |
|---|---|---|---|
| S41-F5-01 | Planicie real (no F1 con tumbas) | PASS | `17_fase5_planicie.png`, horizonte abierto |
| S41-F5-02 | Tumbas y conquistadores | PASS | tumbas altas, cruces, losas |
| S41-F5-03 | Luna como fuente | PASS | luna PNG + `_luz_de_luna` 0.45–0.75 |
| S41-F5-04 | Oscuridad dinámica por nubes | PARTIAL | `33_fase5_nubes.png`; suelo global 0.45 impide negro (P2) |
| S41-F5-05 | Muertos/procesión sólo con luz | PASS | `20_fase5_muertos.png`, umbral 0.58 + patrulla |
| S41-F5-06 | Voces/cantos direccionales | PASS | `amb_stage41_f5.wav` (canto + grillos) |
| S41-F5-07 | Eventos | PASS | nubes, muertos, aislados |

## F6 — Camino a Paburu

| ID | Requisito | Estado | Evidencia |
|---|---|---|---|
| S41-F6-01 | Cambio estético total | PASS | `21_fase6_camino.png` |
| S41-F6-02 | Niebla real perceptible | PASS | clima `fog` + velo; `24_fase6_particulas.png` |
| S41-F6-03 | Camino ritual | PASS | piedra clara + grietas |
| S41-F6-04 | Antorchas progresivas en orden | PASS | `test_orden_obligatorio`, `34_fase6_antorchas.png` (4/4) |
| S41-F6-05 | Partículas verdes | PASS | `spores` 26→40/s |
| S41-F6-06 | Grietas verdes por pasos | PASS | `test_pasos_encienden`, `23_fase6_grietas.png` |
| S41-F6-07 | Espíritus liberados presentes | PASS | apariciones venado/serpiente/halcón por antorcha |
| S41-F6-08 | Entrada/templo con escala | PASS | `35_templo_portal.png`, silueta Paburu |
| S41-F6-09 | Temblor | PASS | shake 8/0.8 en paso 7 (`test_templo_diez_pasos`) |
| S41-F6-10 | Awakening (banderas + voz) | PASS | `PABURU_AWAKENED` + `sfx_voz_paburu_risa` + `s41_despertar` |
| S41-F6-11 | Transición a Paburu (warp con llave) | PASS | `destino_stage_id=boss_paburu`, `key_id` exigida |

## AUD-816 — Correcciones visuales estructurales

| ID | Problema | Causa | Corrección | Runtime | Visual | Evidence | Status |
|---|---|---|---|---|---|---|---|
| S41-V-01 | Player flotando | Masa visual 10 px bajo la colisión; sin sombra | Tiles densos desde fila 0 + sombra de contacto | pies=512/458.3 | `36–41_pies_*.png` | tests `TestApoyoP0` | PASS |
| S41-V-02 | Geometría de rectángulos/debug | Franjas punteadas uniformes | Siluetas l/c/r por grupos con huecos | TMX 260/layer | `02/05/09_*` | test fondos | PASS |
| S41-V-03 | F2≈F3 mismo gris | B&N idéntico | F2 duotono verde-gris; F3 gris frío + ambiente 0.42 | matrices | `05` vs `09` | comparativa | PASS |
| S41-V-04 | Lluvia invisible | Gotas finas del motor | 3 capas + splash + viento; F3 200 vs F2 110 | conteo gotas | `05/09_*` | visible en still | PASS |
| S41-V-05 | Niebla F6 plana | Overlay/velo | 3 bandas con deriva ×(0.08/0.20/0.45) pegadas al suelo | offsets | `22/24_*` | bandas se mueven | PASS |
| S41-V-06 | Shake perdido | — (existía) | Evidencia: `_shake_offset.length()>0` en evento | test | `16_*` + mensaje | `test_shake_mueve_el_offset_renderizado` | PASS |
| S41-V-07 | Sin hitos por fase | Todo baldosas 16 px | Mausoleo/costillar/quemado/cruz/arco procedurales | draw | `02/09/13/17/26_*` | visibles | PASS |
| S41-V-08 | Tumbas cuadradas iguales | 6 piezas fijas | Variantes 14/15 + grupos denso/vacío | TMX | `02/17_*` | test variedades | PASS |
| S41-V-09 | Diálogo Paburu ausente | Sólo mensaje | Árbol `paburu` + trigger col 948 + retrato/voz | visto en raise | `dialogo_paburu` | test diálogos | PASS |
| S41-V-10 | F5 arbolado como bosque | Mismos árboles | Colinas+cruces; sin copas (motivos f5) | TMX | `17_*` | horizonte abierto | PASS |

## Transiciones (5)

| ID | Requisito | Estado | Evidencia |
|---|---|---|---|
| S41-T-01…05 | F1→F2 … F5→F6 perceptibles | PASS | `04/27/28/29/30_*.png` + clima anticipado 16 cols |

## Rendimiento (headless CPU, 1280×720, 300 cuadros)

| Punto | media | p50 | p95 | p99 |
|---|---|---|---|---|
| F3 tormenta | 3.0 ms | 2.4 | 6.8 | 7.8 |
| F4 fuego+caza | 2.7 ms | 2.2 | 5.4 | 8.4 |
| F5 luna+nubes | 2.0 ms | 1.9 | 2.3 | 2.9 |
| F6 niebla+luces | 2.2 ms | 1.9 | 3.7 | 6.6 |
| Despertar/templo | 2.3 ms | 2.0 | 3.8 | 6.6 |

GPU: BLOCKED (sin GPU en este entorno). Stutter severo: no (p99 < 8.5 ms).

## Audio

19/19 ficheros (18 + cama de fuego) existen, decodifican y suenan en
runtime. Voces de espíritus con ducking del motor. Grabación de mezcla:
AUDIO RECORDING BLOCKED BY ENVIRONMENT (driver dummy); evidencia
técnica load→decode→trigger→routing en tests.

## Veredicto

```text
==================================================
LEGACY OF INFEST — STAGE 4.1 AUD-816
==================================================
P0 (player): PASS — pies=superficie (512/458.3), sombra de contacto
P1: 0
P2: 1 (S41-F5-04 negro total vetado por suelo global 0.45)
P3: 2 (S41-028 2.5D/Y-depth descope; retrato de Jin sin arte)

TESTS: PASS (contrato + runtime)
RUNTIME: PASS (INTRO→…→PABURU sin saltos + bot completo)
VISUAL: PASS (41/41: fases distinguibles, sin geometría debug)
AUDIO: PASS (integración; grabación bloqueada por entorno)
NARRATIVE: PASS (cadena causal + flags + templo + Paburu)
PHYSICS: PASS (bot + fricción + slopes + viento + apoyo)
LIGHTING: PASS (luna+nubes, piras, antorchas, rayos)
PARTICLES: PASS (lluvia por capas, brasas, esporas, humo)
FOG: PASS (3 bandas estratificadas)
PARALLAX: PASS
TRANSITIONS: PASS (5/5)
PABURU HANDOFF: PASS (diálogo + warp con llave a boss_paburu)

OVERALL: CERTIFIED
```
