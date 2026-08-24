# Análisis de niveles (level design / play / feel)

Cada nivel se midió con `analyse_stage`; el texto cualitativo se escribió
con lo que la batería y la inspección de los TMX muestran.

## Tabla resumen (orden de campaña)

| nivel | tamaño | terreno | plataformas | salida alcanzable |
| salida (rect) | checkpoints | gaps | componentes (top) | enemigos (top) |
|---|---|---|---|---|---|---|---|---|---|
| stage0 | 1600×608 | 25.5% | 30/30 | sí | Rect(1552, 432, 32, 48) | 5 | 144, 160, 215, 308, 349, 384 | BloqueRitmico=3, Liana=1, Tirolesa=1, Transform=3, ZonaDeFriccion=2, ZonaDeViento=1 | EnemyArcher×1, EnemyAssassin×1, EnemyBrute×1, EnemyCaster×1, EnemyCharger×1, EnemyFlying×1 |
| stage_mecanicas | 4960×384 | 16.9% | 4/1 | no | Rect(4896, 272, 32, 48) | 8 | 387, 480, 480, 480, 480, 496, 560, 576, 944 | Acosador=1, Alerta=2, BloqueRitmico=4, ConoDeVision=2, PlataformaHundible=1, PlataformaMovil=3 | EnemyFlying×4, EnemyShooter×3, EnemyWalker×5 |
| stage_cenital | 928×256 | 100.0% | 54/54 | no | sin NextTrigger | 0 | — | — | — |
| stage1_1 | 3840×640 | 39.3% | 10/9 | sí | Rect(3744, 288, 32, 64) | 7 | 240, 480, 480, 480, 481, 481, 484, 484 | — | EnemyFlying×3, EnemyShooter×2, EnemyWalker×6 |
| stage1_2_la_soda | 768×608 | 7.1% | 27/27 | sí | Rect(736, 496, 32, 112) | 1 | 328, 393 | — | FlyingCucaracha×1, WalkerRaton×1 |
| stage1_3_las_aulas | 3200×608 | 13.6% | 6/5 | sí | Rect(3040, 512, 32, 64) | 7 | 160, 192, 224, 416, 416, 432, 512, 640 | — | CuadernoVolador×4, EstudianteInfectado×8 |
| stage2_1_oficinas | 3200×608 | 10.5% | 1/1 | sí | Rect(3120, 416, 48, 128) | 7 | 256, 376, 400, 400, 400, 400, 401, 424 | — | EnemyBrute×3, EnemyCharger×2, EnemyWalker×3 |
| stage2_2 | 1920×800 | 32.1% | 12/11 | sí | Rect(1696, 192, 32, 64) | 5 | 198, 352, 400, 400, 429, 455 | — | EnemyFlying×2, EnemyShooter×1, EnemyWalker×4 |
| lobby_datacenter | 640×224 | 28.6% | 2/2 | sí | Rect(635, 160, 5, 64) | 1 | 272, 319 | — | EnemyFlying×1, EnemyShooter×1, EnemyWalker×1 |
| stage3_1_la_entrada_de_piedra | 1600×224 | 14.3% | 1/1 | sí | Rect(1560, 160, 16, 64) | 1 | 736, 785 | — | EnemyFlying×4, EnemyShooter×2, EnemyWalker×4 |
| hall | 1088×608 | 20.9% | 6/5 | no | Rect(720, 192, 16, 64) | 1 | 320, 747 | — | EnemyFlying×6, EnemyShooter×2, EnemyWalker×5 |
| stage3_3_el_patio | 960×608 | 8.6% | 7/5 | sí | Rect(928, 512, 16, 64) | 1 | 409, 489 | — | EnemyFlying×5, EnemyShooter×3, EnemyWalker×3 |
| boss_gavilan | 1632×608 | 11.1% | 20/10 | no | sin NextTrigger | 2 | 416, 600 | — | BossGavilan×1, EnemyFlying×3 |
| stage4_1 | 14400×608 | 23.1% | 3/3 | sí | Rect(14304, 432, 32, 48) | 6 | 245, 2160, 2160, 2240, 2352, 2400, 2688 | ZonaDeFriccion=5, ZonaDeViento=1 | — |
| stage4_1b | 14400×608 | 15.8% | 1/1 | sí | Rect(14240, 448, 32, 96) | 6 | 163, 1936, 2400, 2400, 2400, 2400, 2400 | ZonaDeAgua=1 | — |
| stage4_1c_a | 14400×608 | 2.8% | 9/3 | no | Rect(14304, 320, 32, 96) | 6 | 80, 2148, 2224, 2320, 2401, 2464, 2528 | BloqueRitmico=90, Transform=90, ZonaDeViento=1 | — |
| stage4_1c_b | 14400×608 | 2.8% | 9/3 | no | Rect(14304, 304, 32, 96) | 6 | 129, 2192, 2288, 2304, 2371, 2432, 2451 | BloqueRitmico=87, Transform=87, ZonaDeViento=1 | — |
| stage4_1c_c | 14400×608 | 2.8% | 9/3 | no | Rect(14304, 272, 32, 96) | 6 | 86, 2225, 2273, 2289, 2336, 2451, 2496 | BloqueRitmico=90, Transform=90, ZonaDeViento=1 | — |
| boss_venado | 3280×608 | 9.1% | 1/1 | no | sin NextTrigger | 0 | — | — | BossVenado×1 |
| boss_rey | 1120×592 | 50.0% | 4/1 | no | sin NextTrigger | 0 | — | — | BossRey×1 |
| boss_paburu | 800×608 | 16.8% | 4/3 | no | sin NextTrigger | 1 | 32 | — | BossPaburu×1 |

## Nivel por nivel

### stage0

Escaparate del motor y tutorial de la universidad: 30 plataformas con enemigos arquetípicos (arquero, asesino, bruto, lanzador, cargador, volador, tirador, caminante) en secciones legibles. La salida se alcanza por una plataforma one-way sobre el vacío: el analizador estático la marca inalcanzable porque no modela one-ways, pero el salto cabe en el envolvente del jugador.

**Fortalezas.** Buen ritmo de enseñanza (una mecánica por sala), cierre con reto de precisión. 29 de 30 plataformas alcanzables.

**Debilidades.** El final en one-way sobre vacío castiga al jugador novel: caer ahí supone repetir la última sección sin checkpoint cercano (gap de 384 px).

**Métricas.** 30 plataformas (30 alcanzables) · densidad de terreno 25.5% · checkpoints 5 · one-way 2 · empujables 0 · destructibles 0 · salida Rect(1552, 432, 32, 48) (dentro) · repechos 0.
### stage_mecanicas

Laboratorio de mecánicas de movimiento: resorte, viento, fricción, plataformas móviles, bloques rítmicos, zonas letales temporizadas, plataforma hundible, agua y una sección de sigilo (cono de visión + alertas + acosador) sobre 4960 px de pasillo.

**Fortalezas.** Cobertura de mecánicas única en el proyecto; el tramo de sigilo aporta variedad de ritmo. Gaps de checkpoint hasta 944 px: duros pero perdonables.

**Debilidades.** El tramo largo sin checkpoint (944 px ≈ 10 s) tras la sección rítmica junta dos castigos: timing y reinicio lejano.

**Métricas.** 4 plataformas (1 alcanzables) · densidad de terreno 16.9% · checkpoints 8 · one-way 9 · empujables 1 · destructibles 2 · salida Rect(4896, 272, 32, 48) (dentro) · repechos 0.
### stage_cenital

Laboratorio cenital (vista desde arriba): demuestra que el motor tiene modo cenital, pero no entra en campaña.

**Fortalezas.** Prueba de concepto valiosa para modos alternativos.

**Debilidades.** Fuera de la campaña: su audiencia real es la demo.

**Métricas.** 54 plataformas (54 alcanzables) · densidad de terreno 100.0% · checkpoints 0 · one-way 0 · empujables 0 · destructibles 0 · salida sin NextTrigger (dentro) · repechos 0.
### stage1_1

Entrada de la facultad, primera entrega de estudiante: plataformas básicas y enemigos propios. Gaps de checkpoint que la batería sigue midiendo (hasta 1200 px).

**Fortalezas.** Nivel completo y jugable, con salida y sin bloqueos.

**Debilidades.** Sin datos finos de la batería (no declara mecánicas dinámicas): revisar a mano el confort de los saltos.

**Métricas.** 10 plataformas (9 alcanzables) · densidad de terreno 39.3% · checkpoints 7 · one-way 3 · empujables 0 · destructibles 0 · salida Rect(3744, 288, 32, 64) (dentro) · repechos 0.
### stage1_2_la_soda

La soda: segunda entrega. Enemigos y plataformas propias.

**Fortalezas.** Jugable y con salida.

**Debilidades.** Ídem stage1_1: auditoría fina manual pendiente.

**Métricas.** 27 plataformas (27 alcanzables) · densidad de terreno 7.1% · checkpoints 1 · one-way 0 · empujables 0 · destructibles 0 · salida Rect(736, 496, 32, 112) (dentro) · repechos 0.
### stage1_3_las_aulas

Las aulas: tercera entrega, cierre del bloque 1.

**Fortalezas.** Jugable y con salida.

**Debilidades.** Ídem stage1_1.

**Métricas.** 6 plataformas (5 alcanzables) · densidad de terreno 13.6% · checkpoints 7 · one-way 22 · empujables 0 · destructibles 0 · salida Rect(3040, 512, 32, 64) (dentro) · repechos 1.
### stage2_1_oficinas

Oficinas, apertura del bloque 2. La batería destapa un hallazgo real: CERO checkpoints en 3200 px. Morir reinicia el nivel entero, y el peor tramo sin red de seguridad mide 3048 px (≈ 33 s).

**Fortalezas.** Nivel largo con identidad propia (oficinas).

**Debilidades.** Hallazgo AUD (pendiente de decisión del dueño): falta al menos un checkpoint a mitad de nivel. Ver xfail en la batería.

**Métricas.** 1 plataformas (1 alcanzables) · densidad de terreno 10.5% · checkpoints 7 · one-way 0 · empujables 0 · destructibles 0 · salida Rect(3120, 416, 48, 128) (dentro) · repechos 0.
### stage2_2

Segunda entrega del bloque 2.

**Fortalezas.** Jugable, con salida y checkpoints.

**Debilidades.** Revisión fina manual pendiente.

**Métricas.** 12 plataformas (11 alcanzables) · densidad de terreno 32.1% · checkpoints 5 · one-way 2 · empujables 0 · destructibles 0 · salida Rect(1696, 192, 32, 64) (dentro) · repechos 0.
### lobby_datacenter

Transición/pasillo entre niveles del bloque 2.

**Fortalezas.** Corta y directa, cumple su función.

**Debilidades.** ¿Aporta algo al gameplay o es puro pasillo? Decisión de diseño.

**Métricas.** 2 plataformas (2 alcanzables) · densidad de terreno 28.6% · checkpoints 1 · one-way 0 · empujables 0 · destructibles 0 · salida Rect(635, 160, 5, 64) (dentro) · repechos 0.
### stage3_1_la_entrada_de_piedra

Apertura del bloque 3.

**Fortalezas.** Jugable y con salida.

**Debilidades.** Revisión fina manual pendiente.

**Métricas.** 1 plataformas (1 alcanzables) · densidad de terreno 14.3% · checkpoints 1 · one-way 6 · empujables 0 · destructibles 0 · salida Rect(1560, 160, 16, 64) (dentro) · repechos 0.
### hall

Salón de piedra: la salida se alcanza por una escalera de plataformas one-way bajo el techo. El analizador no las modela y marca la salida inalcanzable: falso negativo documentado.

**Fortalezas.** Escaleras one-way bien leídas por el jugador (dirección clara).

**Debilidades.** Sección corta; el interés depende del combate, no del nivel.

**Métricas.** 6 plataformas (5 alcanzables) · densidad de terreno 20.9% · checkpoints 1 · one-way 19 · empujables 0 · destructibles 0 · salida Rect(720, 192, 16, 64) (dentro) · repechos 1.
### stage3_3_el_patio

El patio, cierre del bloque 3 antes del jefe.

**Fortalezas.** Jugable y con salida.

**Debilidades.** Revisión fina manual pendiente.

**Métricas.** 7 plataformas (5 alcanzables) · densidad de terreno 8.6% · checkpoints 1 · one-way 4 · empujables 0 · destructibles 0 · salida Rect(928, 512, 16, 64) (dentro) · repechos 0.
### boss_gavilan

Jefe Gavilán: la entrega está incompleta (~45 % de la rúbrica, sólo Fase 1, sin patrones de ataque). El escenario de batalla existe y carga, pero el jefe no tiene ciclo de combate.

**Fortalezas.** El escenario y la fase 1 sentaron la arquitectura que el plan 87-§27 reconstruirá.

**Debilidades.** Es el hueco de contenido más grande del juego: ver GAP-058..065 en KNOWN_GAPS.md y docs/87_REPORTE_DE_LO_QUE_FALTA.md.

**Métricas.** 20 plataformas (10 alcanzables) · densidad de terreno 11.1% · checkpoints 2 · one-way 0 · empujables 0 · destructibles 0 · salida sin NextTrigger (dentro) · repechos 1.
### stage4_1

Cementerio sagrado, entrega del bloque 4. Los gaps de checkpoint superan 1200 px (hasta ~2500 px) por decisión documentada AUD-516 (32 checkpoints -> 6): el reinicio es deliberadamente más duro.

**Fortalezas.** Identidad visual fuerte (cementerio, fosa azul).

**Debilidades.** La dureza es una decisión, pero el reporte la deja registrada para que el dueño la confirme con datos de jugadores.

**Métricas.** 3 plataformas (3 alcanzables) · densidad de terreno 23.1% · checkpoints 6 · one-way 0 · empujables 0 · destructibles 0 · salida Rect(14304, 432, 32, 48) (dentro) · repechos 0.
### stage4_1b

Variante b del cementerio (fosa azul, AUD-531).

**Fortalezas.** Variación barata del mismo nivel: más densidad por menos coste.

**Debilidades.** Gaps grandes igual que stage4_1.

**Métricas.** 1 plataformas (1 alcanzables) · densidad de terreno 15.8% · checkpoints 6 · one-way 0 · empujables 0 · destructibles 0 · salida Rect(14240, 448, 32, 96) (dentro) · repechos 0.
### stage4_1c_a

Sección rítmica: 61 bloques rítmicos sobre 14400 px con terreno estático del 2.8 %. La salida depende de bloques que aparecen a compás: el analizador la marca inalcanzable (falso negativo documentado).

**Fortalezas.** Nivel de plataformeo puro, el más 'nivel de juego' del motor.

**Debilidades.** Sin enemigos: el reto es 100 % timing. El gap de checkpoints de 2480 px es muy duro para un nivel de precisión.

**Métricas.** 9 plataformas (3 alcanzables) · densidad de terreno 2.8% · checkpoints 6 · one-way 0 · empujables 0 · destructibles 0 · salida Rect(14304, 320, 32, 96) (dentro) · repechos 1.
### stage4_1c_b

Variante b de la sección rítmica.

**Fortalezas.** Misma calidad de construcción que la a.

**Debilidades.** Ídem a: sin enemigos, checkpoints lejanos.

**Métricas.** 9 plataformas (3 alcanzables) · densidad de terreno 2.8% · checkpoints 6 · one-way 0 · empujables 0 · destructibles 0 · salida Rect(14304, 304, 32, 96) (dentro) · repechos 2.
### stage4_1c_c

Variante c de la sección rítmica.

**Fortalezas.** Ídem.

**Debilidades.** Ídem.

**Métricas.** 9 plataformas (3 alcanzables) · densidad de terreno 2.8% · checkpoints 6 · one-way 0 · empujables 0 · destructibles 0 · salida Rect(14304, 272, 32, 96) (dentro) · repechos 2.
### boss_venado

Jefe de referencia del bloque 1 (el material que los estudiantes copian): batalla con fases completa y salida real.

**Fortalezas.** Referencia ejemplar: fases, patrones y transiciones documentadas.

**Debilidades.** Gap de checkpoint de 941 px dentro de la arena: morir en la fase 2 repite mucho recorrido.

**Métricas.** 1 plataformas (1 alcanzables) · densidad de terreno 9.1% · checkpoints 0 · one-way 5 · empujables 0 · destructibles 0 · salida sin NextTrigger (dentro) · repechos 0.
### boss_rey

Jefe Rey Terciopelo, bloque 2: completo.

**Fortalezas.** Completo y jugable.

**Debilidades.** Revisión fina manual pendiente.

**Métricas.** 4 plataformas (1 alcanzables) · densidad de terreno 50.0% · checkpoints 0 · one-way 0 · empujables 0 · destructibles 0 · salida sin NextTrigger (dentro) · repechos 3.
### boss_paburu

Gran Shaman Paburu, jefe final. La batería destapa un hallazgo real: un NextTrigger fantasma en y=-64 (fuera del mapa). El nivel se completa por el jefe, así que el trigger sobra, pero su presencia denuncia que el mapa se editó a mano (AUD-259: BossSpawn por entidad).

**Fortalezas.** Arena cerrada y completa.

**Debilidades.** Hallazgo AUD (pendiente de decisión): borrar el NextTrigger fantasma o documentar por qué está. Ver xfail en la batería.

**Métricas.** 4 plataformas (3 alcanzables) · densidad de terreno 16.8% · checkpoints 1 · one-way 4 · empujables 0 · destructibles 0 · salida sin NextTrigger (dentro) · repechos 1.

## Notas del analizador

El analizador (AUD-049) no modela plataformas one-way ni mecánicas
dinámicas (resortes, bloques rítmicos, viento...): cuando un nivel las usa
cerca de la salida, la marca inalcanzable. La batería documenta cada falso
negativo con su excusa. Los niveles con salida "no" y **sin** excusa son
hallazgos reales.
