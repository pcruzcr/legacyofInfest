# Stage 4-2 «El Gran Shaman Paburu» — Lista maestra de pendientes

> Escrito para retomar el trabajo en un chat nuevo sin perder el hilo.
> Estado al 2026-08-16. La referencia completa de diseño vive en
> `DISENO_NIVEL_Y_JEFE.md` (leerlo primero; su §7 lleva el detalle de todo
> lo cerrado). Regla viva: **cada cambio actualiza ese documento.**

---

# ▣ TABLERO — qué está hecho y qué falta

*Se actualiza en cada ronda. Debajo del tablero está el registro histórico
completo, ronda por ronda, con el porqué de cada decisión.*

**Salud del stage hoy:** `grade_stage` **130/130** · `grade_boss` **100/100** ·
256 tests de paburu en verde · ruff limpio · **corriendo sobre el MOTOR v2
del profesor**. Última ronda: la **22** (la barra ya no tapa a los
custodios, el retablo dejó de ser una sierra, el cuadro de la tirolesa
con pilares de columbario, y los dos archivos que a su copia le
faltaban para pytest). Antes, la **21** (los hallazgos del VIDEO:
enemigos que no volvían a su puesto, Paburu empujable fuera de la sala,
la Forma 4 inalcanzable, el combo de aire, la trampa de la catacumba y
las pavesas apagadas). **BUGS DEL MOTOR nº 12 y nº 13** escritos como
adendas de `BUGS_DEL_MOTOR.md`, pendientes de mandar al profesor. **BUG DEL MOTOR nº 12**: `TirolesaState` no anula la gravedad
durante el viaje — reporte completo YA ESCRITO como adenda de
`BUGS_DEL_MOTOR.md` (formato de seis apartados, parche de 1 línea);
solo falta que Alejandro se lo mande al profesor.

**2026-08-27 — el profesor actualizó la asignación (Evaluación
Práctica II)**: pide una documentación breve (§8: descripción + dónde
se aplicó cada contenido de CG + testing) → creada en
`DOCUMENTACION_ENTREGA_II.md`; y el video cambió a 10 puntos donde el
5-9 son los contenidos de CG en pantalla (§9) →
`PLAYTEST_GUION.md` re-mapeado. Código: nada nuevo que hacer — la
asignación no pide ninguna mecánica que no exista ya.

## ▶ EN CURSO

| # | Qué | Estado |
|---|---|---|
| **D-01** | **Rediseño del acceso a la catacumba** — *Las Cuatro Ofrendas* (`DISENO_ACCESO_CATACUMBA.md`) | **Fase A ✔ · faltan B, C y D** |
| D-01·B | ✔ **CERRADO**: cuencos sin oro + niebla propia. Y el misterio de los discos lo resolvió **Alejandro jugando el stage del profesor**: son los **sprites de checkpoint del motor** (grises → dorados al activarse). Mi disección no los encontró porque `DrawingSystem` guarda su PROPIA lista de checkpoints capturada al arrancar — yo vaciaba la de `stage_data` y el dibujo ni se enteraba. El playtest ve lo que la disección no | ✔ |
| D-01·E | ✔ **EL MAUSOLEO v2** — la primera versión se armó de piezas repetidas y Alejandro la rechazó con razón («hiciste un tileset»; lo del profesor «se ve como dibujado»). Rehecho con la técnica correcta: UN dibujo de 80×128 (gradas, pilares, entablamento con inscripción, frontón, pináculos de llama, cruz patriarcal, arco con dovelas y clave, verja de forja con volutas a contraluz del fuego, contorno oscuro en toda la silueta) rebanado en 40 tiles (GID 105-144). La retícula deja de existir para el ojo | ✔ |
| D-01·F | ✔ **VELADORAS** — los checkpoints ya no son «palos con círculos»: la escena les inyecta `_sprite`/`_grey_sprite` (el motor los prefiere si existen — mismo truco que la piel de mecánicas, cero líneas de motor). Encendida con llama y halo para el activado; apagada con hilo de humo para el que espera. Y el décimo checkpoint se retiró de la puerta del mausoleo (3960 → 3880): el mobiliario del motor no se planta delante de los momentos del nivel | ✔ |
| D-01·G | ✔ **EL PORTÓN v2** — la v1 (dos postes y un alambre) la rechazó Alejandro: «le falta gracia, siento es tileset regado». Ahora es un ARCO DE MEDIO PUNTO entero de 112×144: sillería almohadillada, enjutas que abrazan el arco, clave con la espiral tilawa, placa de inscripción, parapeto almenado y DOS FAROLITOS de forja encendidos (el eco del fuego: farolitos al entrar, la boca ardiendo al final — deliberado y declarado en el racionador). 63 tiles (GID 145-207) | ✔ |
| — | **Notas del playtest del 4-1 (Alejandro)**: el motor tiene MONEDAS reales (contador ¤ del HUD, `coins_for`) — candidatas para la fase C si las ofrendas quieren economía; «ULTI CARGADO tras golpear» — la idea de Alejandro ya se contó y se construyó: es **LA FORMA DEL ÁNIMA** (#49, Ronda 13); el knockback del motor DESPLAZA el ancla de patrulla de los enemigos y no vuelven a su puesto — vigilar en los nuestros (los murciélagos tienen `_casa`; máscaras y sukias usan el caminante del motor) | anotado |
| D-01·H | ✔ **LAS ÁNIMAS** (idea de Alejandro): nueve tumbas habitadas. Ciclo de cada una: silencio largo → una CARA de ojos espectrales se enciende en la lápida → el espíritu se alza con su velo de jirones y ojos huecos, se mece y se deshace. Nueve relojes distintos (periodo 11-17 s): el camposanto nunca repite el mismo segundo. Alfa normal, no aditivo — un blit aditivo no sabe dibujar ojos oscuros | ✔ |
| D-01·I | ✔ **EL DESCENSO SE VE — segunda vuelta**. La v1 (recorte a 150 px/s) no bastó: «sigue bajando y no pasa por la liana, solo cae» — cambiaba la velocidad, no el ESTADO, y el sprite seguía en FALLING. Ahora el mecate **agarra de verdad**: al caer al foso la escena mete al jugador en `TrepandoState` (el estado de lianas del motor, que pide la tecla G — nadie descubre una tecla en plena caída). Colgado manda él: ARRIBA sube, ABAJO baja al paso del motor, SALTO suelta (sin re-agarre en la visita), y sin tocar nada el mecate resbala a 70 px/s. A 36 px del suelo las manos sueltan solas (el rect de la cuerda llega al piso y el motor jamás soltaría). Si la pelea se arma a media cuerda, el descenso TERMINA (antes lo dejaba colgado con Paburu emergiendo debajo — medido) | ✔ |
| D-01·K | ✔ **LAS NUBES DERIVAN** (pedido de Alejandro sobre el concept: «¿será que se pueden poner nubes moviendo?»): siete nubes nocturnas, cada una un pincel propio de 12 panzas translúcidas desenfocado (bajar y subir de resolución — la v1 de elipses duras parecían platillos, se vio en la captura), base plana y filo de luna, parallax 0.28-0.44 entre las estrellas y el fondo, deriva propia de 2.5-7.5 px/s aunque el jugador esté quieto. Pueden cruzar la luna: es su mejor momento | ✔ |
| D-01·J | ✔ **LAS ESTRELLAS TITILAN** (lo que más le gustó del 4-1, y el profesor dio permiso de revisar su código — implementación propia): 46 estrellas con fase y ritmo individuales, ~1 de cada 5 titila fuerte con cruz de destello, el resto late suave. Parallax propio (más lento que el fondo: son lo más lejano) y se callan ante la luna. Medido: 42 px del cielo cambian entre dos instantes | ✔ |
| — | **Musgo flotante arreglado**: `moss_patch` pintaba donde el ruido dijera INCLUYENDO el aire alrededor de las siluetas — pegotes verdes flotando junto a cruces y obeliscos («se sale, no cuadra»). Ahora el musgo sólo crece sobre piedra (alfa > 0). Cero píxeles fuera del mástil, medido | ✔ |
| D-01·C | ✔ **LAS PAVESAS Y LOS CÍRCULOS QUE ARDEN** (Ronda 16). Cuatro pavesas vivas, una por tramo y siempre ANTES de su círculo (fondo del pozo / alto del columbario / galería del III / **el bolsillo de la tirolesa** — la pieza muerta vuelta clímax del rito). Pisar un círculo llevando fuego lo enciende: gasta la pavesa y prende CUATRO LUCES REALES en sus cuencos («la recompensa por explorar es poder ver»). Los apagados humean — se ve de lejos cuál falta. Contador diegético: cuatro braseritos bajo el retrato + las pavesas en mano ORBITAN al portador. `una_vez` de los disparadores pasó a falso (el cruce en vacío consumía el círculo para siempre = nivel incompletable) con dedupe en escena | ✔ |
| D-01·D | ✔ **LA LOSA DEL JUICIO** (Ronda 16). La boca nace sellada por una losa a RAS de piso — una `Cerradura` del MOTOR (F4.1, cero framework): su rect es sólido mientras cierra, el camino final se camina de largo, y tocarla con G avisa «ARDEN N DE 4 CIRCULOS». Sus cuatro marcas muestran el progreso EN el destino. Con la cuarta ofrenda cede: polvo, sacudida, y el foso vuelve a tragar (v1 medida y corregida: 16 px arriba era un escalón que clavaba al caminante en x=3990; enrasada se cruza de largo). REENTRANTE: morir re-llama `on_enter` (la trampa del sorteo) — el progreso vive en el constructor y sólo se reconstruye su mundo; lo cazó `test_morir_no_apaga_nada` | ✔ |

## ○ FALTA

| # | Qué | Bloqueado por | Tamaño |
|---|---|---|---|
| **#46** | Playtest humano + rendimiento: timing del parry del Juicio, FURIA de la Perla en esquinas, dificultad del arco a mano, FPS con F11 | Sólo lo puede hacer Alejandro | — |
| **#49** | ✔ **CERRADO como LA FORMA DEL ÁNIMA** (fusión con la idea del ulti de Alejandro — ver Ronda 13). Queda abierto lo OPCIONAL: si algún día se quiere arte dibujado a mano (del concept generado) en vez del re-teñido procedimental, son las mismas ~30 líneas con otra hoja de sprites | ✔ (v1) |
| **P-01** | ✔ La mitad de la catacumba CERRADA en Ronda 21 (repisas re-escalonadas a salto simple; el salto doble del motor está desconectado — hallazgo 12.3). QUEDA: los ocho repechos de superficie a 80 px (apex 91: llegan pero justo) y el «cuesta pasar por el tileset» del video — falta que Alejandro diga DÓNDE | Su próximo reporte | S |
| **P-02** | ✔ Veredicto humano recibido y aplicado (Ronda 21): la Forma 4 bajó al alcance y persigue. Falta su re-jugada para confirmar que ahora se siente justa | Su próximo reporte | S |
| **P-03** | Optimizaciones anotadas y no aplicadas: caché del aura del jefe (−88 %), pre-hornear las brasas, teclas de depuración detrás de variable de entorno | — | S |
| **#47** | EP2 (Clase 8) · Unidad VII: histograma dirigiendo lógica + brillo/contraste + un kernel justificado | Hito futuro de la rúbrica | L |
| **#48** | EP3 (Clase 11) · Unidades VIII-IX: segmentación + clasificador con dataset y accuracy ≥0.70 | Hito futuro de la rúbrica | L |

## ✔ HECHO (por ronda, lo más reciente arriba)

| Ronda | Qué se cerró | Detalle |
|---|---|---|
| **22** | **LA SEGUNDA TANDA DEL VIDEO.** (1) **«La vida debería estar en otro lugar: los espíritus de la Forma 2 no se ven bien»** — las celdas de los custodios miden 120 px y se dibujan centradas: con la base a cielo+108, la cabeza del espíritu quedaba a ~28 px de pantalla, DETRÁS de la barra del jefe y del medidor. La barra es del motor y no se muda; los espíritus bajaron 80 px a la franja vacía entre el HUD y las repisas — capturado: los tres visibles enteros bajo la barra. (2) **«El tileset de la catacumba está mal diseñado, hay cosas raras»** — cazado con zoom: el arco del retablo eran DIECISIETE dovelas-cuña en línea recta = una SIERRA suspendida sobre la pelea (nadie salta con ganas bajo pinchos); ahora es un DINTEL con arranques, sillería tejida y tres cuñas al centro con su clave. Las ménsulas de la sala perdieron los dientes de cornisa (dovela+losa, como el puente), los capiteles son losa grabada, y cada repisa lleva arranque bajo la PUNTA además del de la pared — se acabaron las «letras flotantes». (3) **«El cuadro de la tirolesa se ve feo, cuadros por ponerlos»** — el frontón flotante bajo el CENTRO de cada plataforma del camino final (un triángulo levitando) ahora CORONA cada pilar de apoyo, pegado a la panza de la losa: pilar+capitel+losa se leen como obra; y a los pilares se les tejen NICHOS TAPIADOS — el camino final camina por encima de los muertos ricos. (4) A su copia le faltaban `tools/hoja_a_tileset.py` y `tools/__init__.py` (pytest no arrancaba) — entregados. Capturas `r22_*` | ↓ Ronda 22 |
| **21** | **LOS HALLAZGOS DEL VIDEO (2026-08-28), enteros.** Alejandro grabó y reportó siete cosas; seis cerradas: (1) **Los enemigos golpeados no volvían a su puesto** — causa en el motor: el knockback desplaza `position` pero el ancla de patrulla queda fija, y la patrulla del Charger invierte la dirección CADA fotograma al estar a >48 px del ancla: la máscara desplazada vibraba en el sitio («se quedan ahí raros»). La máscara y el sukia ahora CAMINAN de vuelta a su puesto (override de `_patrol_behavior`, cero motor). Medido: 4 golpes seguidos → a 4 px de casa. (2) **Paburu se podía sacar de la sala a golpes** («ya no vuelve») — `apply_hit` del motor carga knockback y la Cabeza/Máscara anclan el rect a `position`: el empuje se ACUMULABA. `_apply_knockback` del jefe ahora descarta el impulso: al juez de piedra no lo empujan (el golpe ya tiene destello y hit-stop). 10 golpes → 0 px. (3) **La Forma 4 inalcanzable** («muy alto, no baja, no sigue, pero ataca») — el Espíritu flotaba clavado a 170±32 px. Ahora PERSIGUE la x del portador (55 px/s) y su vaivén BAJA al alcance (112±46: ventana de castigo abajo, de esquive arriba); en ofrecimiento/epílogo vuelve al estrado. Es el veredicto humano de P-02 hecho regla (test: punto más bajo ≤45 px del suelo). (4) **El combo subía pegando al aire** — BUG DEL MOTOR nº 13 (suma al APRETAR, no al conectar; y es multiplicador de daño). Mitigación de escena: `SFX_ENEMY_HIT`/`ENEMY_DIED` marcan «conectó»; un ataque que termina sin marca apaga el combo (el juicio corre al fotograma siguiente, con los eventos ya despachados). Adenda nº 13 escrita en `BUGS_DEL_MOTOR.md`. (5) **La catacumba atrapaba** — dos culpas: la Repisa_1 a 96 px (¡y el salto doble del motor está DESCONECTADO — hallazgo 12.3!) y el brinco MensulaSur→Capitel_2 de 80 px de subida con 72 de vano. Regla nueva medida con walker (~40 px de alcance en llano, ~25 subiendo): todos los peldaños re-escalonados (80/0, 64/8, 48/24, 32/16) y TODOS one-way salvo la Repisa_1 (sólida a propósito: el analizador de repechos del calificador solo ve sólidos — con todo one-way la pared oeste puntuaba como acantilado, 130→127 medido y recuperado). Las repisas nacen a ras de la pared (fuera la chimenea de 16 px). Walker: 6/6 brincos en verde. (6) **Las pavesas apagadas** («las bolitas están muy poco visibles») — segundo halo ×1.9 respirando a destiempo + chispitas que SUBEN + latido más alto. Queda ABIERTO: «lugares donde cuesta pasar por el tileset» en superficie — falta que Alejandro diga DÓNDE (¿los repechos de 80 px? ¿pasos bajos?). Tests `TestLaRonda21` (6). Capturas `r21_*` | ↓ Ronda 21 |
| **20** | **EL PLAYTEST DEL 2026-08-27, entero.** (1) **Las «cosas dibujadas» cazadas por capas**: se rindió el frame con cada capa del TMX vaciada — los pegotes eran los DOS ESCOMBROS FLOTANTES del círculo III, decoración anclada a un trazado que R13/R17 ya habían movido. Auditor sistemático: **33 tiles de decor sin apoyo**, por dos causas — `cruz()` y `obelisco()` dejaban su tile más hondo una fila arriba que `tomb()` (toda cruz y obelisco del mapa flotaba 16 px), y los emblemas de los círculos se clavaban a PLAT_LOW/HIGH_Y viejas. Arreglo: convención unificada (la pieza más honda EN `y_base`), emblemas anclados a `muebles_del_circulo` reales, y el escombro de cornisas sustituido por basa caída (motas sueltas sobre one-way negra = píxeles flotando al ojo). **Test permanente** `test_decor_apoyado_paburu` (CON_PERMISO: la corona de la boca sobre el foso). De rebote las bases robaban las ranuras de las MÁSCARAS de la verja (quedaron 3 de 5 — lo cazó `test_mascaras_altar_y_caracola`) → las ranuras son sagradas (`en_ranura_de_mascara`). (2) **LAS MONTAÑAS SE VEN** («si en el fondo se vieran las montañas estaría bien»): estaban dibujadas a 16 valores del cielo — franja negra. Tres cordilleras con perspectiva aérea nocturna, filo de luna en las crestas y nieve de altura; picos y no colinas (amp 185/150/105, escala corta). (3) **UNA SOLA LUNA**: al aclarar el cielo se vio que el fondo de 800 px se REPITE en la vista de 960 — dos lunas. El cielo lejano ahora mide 1600 y `_ensanchar_el_cielo()` lo repone tras el cargador del motor (que aplasta todo a 800), cero motor. (4) **TORRES SIN FOTOCOPIA** («control C control V, no hay originalidad»): los pilares bajo las plataformas apilaban EL MISMO tile 6-11 veces — seis tiles nuevos (99-104: lápida lisa/agrietada/desportillada, pared con junta/humedad/grieta) tejidos por ruido determinista. (5) **LA FORMA DEL ÁNIMA v2**: fuera la espiral de la boca («ese círculo raro»), mitad baja de madera lisa con dos ranuras; y el fuego nace de TODO el cuerpo («el ánima sale de todo el cuerpo, no solo de la cabeza») — jirones repartidos por la silueta entera a 38/s, los bajos viven menos. (6) **EL RESORTE DE LA SUBIDA**: `Resorte_02` (3792, entre los pilares de la última repisa) sube de un brinco a la repisa de la tirolesa (medido: apex 249, se planta en y=368); el del bolsillo NO se mueve (única salida del otro lado del foso, R13). Tests nuevos: `TestLaRonda20` (3) + `test_decor_apoyado` (2). Capturas `r20_*` | ↓ Ronda 20 |
| **19** | **LA TECLA 8 CARGA EL ULTI** (pedido de Alejandro: «déjame un botón para activar la ulti aunque no esté cargada, para verlo y apreciarlo»). Decisión de diseño: la tecla NO dispara la transformación — **llena la barra** por la vía del motor (`gain_special`, la misma de los golpes) y deja la activación en Z+X, así lo que se ve y se graba es el ulti REAL (estado `ULTIMATE`, daño y física del motor, máscara del ánima), no una imitación de escena. Un aviso «ULTI LISTO — Z+X» flota 3 s sobre el portador (mismo lenguaje que el letrero de la tirolesa) — sin él, quien pulsa 8 se queda mirando una pantalla muda; el aviso muere en el acto al estallar el ulti (la primera captura lo mostró mintiendo «listo» sobre la barra ya vacía) y se mantiene dentro de pantalla (el spawn está pegado al borde). Se une a la familia de teclas de depuración (0 intro, 1-4 formas, 9 descenso). Verificado con arnés: 8 → `ultimate_listo` · Z+X → `PlayerState.ULTIMATE` + transformación 6 s + barra a 0. Tests `TestLaTeclaDelUlti` (3). Capturas `r19_*` | ↓ Ronda 19 |
| **18** | **LA TIROLESA FUNCIONA DE VERDAD** («eso nunca ha funcionado», y tenía tres culpas apiladas). (1) Nadie decía la tecla G — el letrero de R13 la enseña, pero él aún no lo había visto. (2) El radio de enganche de 18 px no perdonaba nada: saltar hacia el cable con G era imposible (medido: NO engancha ni machacando) — subido a 30, engancha parado un par de pasos antes del borde Y saltando con G sostenida. (3) **EL BUG DEL MOTOR**: `TirolesaState` anula la velocidad al entrar pero no cada fotograma, y la integración sigue sumando gravedad — el jinete se HUNDÍA ~80 px bajo el cable a media bajada. En este mapa la consecuencia era gravísima: el cuerpo hundido entraba al FOSO por debajo de la losa sellada y ahí el auto-agarre del mecate (D-01·I) lo secuestraba del cable — **el rito entero bypasseado por física**, directo al juicio sin ofrendas. Doble arreglo del stage: `_sujetar_la_tirolesa` re-proyecta el cuerpo al punto más cercano del segmento cada fotograma (la misma `punto_mas_cercano` del motor) y apaga la velocidad vertical; y el auto-agarre del mecate IGNORA a quien va en `TirolesaState`. Verificado: el viaje va clavado a la línea, suelta al final, REBOTA EN EL RESORTE y aterriza en el bolsillo junto a la pavesa IV — el clímax del rito encadenado como se diseñó. Saltar del cable a mitad sigue intacto (el salto cambia de estado antes de la sujeción). Bug del motor ANOTADO para reportar al profesor con su reproducción. Tests `TestLaTirolesaDeVerdad` (4) | ↓ Ronda 18 |
| **17** | **EL RESPIRO DEL MAPA.** Alejandro seguía viendo «plataformas que no cuadran… otras que se sobreponen» y las veníamos cazando de a una por captura. Se acabó la cacería: un AUDITOR SISTEMÁTICO recorre el TMX real (sólidos, one-ways y las móviles POR SU CARRIL BARRIDO) y busca solapes y roces. Veredicto: cero solapes de rectángulos (el validador tenía razón)… y **NUEVE costuras a 0 px** — piezas tocándose borde con borde, que en pantalla se leen exactamente como «incrustadas»: el cúmulo del pozo era el peor (orilla|B1|B3|hundible|B2, cuatro costuras en 384 px, la balsa vertical ROZANDO a sus tres vecinas en cada pasada), más el andén del ascensor contra su carril, la cornisa del círculo II clavada en la cara del pedestal, y dos empalmes alero|cornisa de materiales distintos en la misma fila. Todo espaciado a ≥8 px de aire (huecos siguen ≤42 del salto simple; bot del pozo re-verificado). El único empalme que queda es DELIBERADO y declarado: los aleros de los círculos I y II, misma fila y mismo material («se tocan muro con muro», §2.1). El auditor quedó de TEST permanente (`test_respiro_del_mapa_paburu`, con guardián anti-regex-viejo) — la próxima pieza sin aire no llega a una captura. AUD-490 actualizado a los orígenes nuevos. Capturas `r17_*` | ↓ Ronda 17 |
| **16** | **LA CÁMARA BAJA CON ÉL + D-01 COMPLETO.** (1) Reporte de Alejandro: «no se veía el personaje bajando… se queda un rato ahí y luego aparece abajo» — el tope plano de la banda de superficie (y≤72) dejaba 560 px de descenso FUERA de pantalla y el corte al encuadre remataba el teleport. Ahora, dentro del foso, un travelling con memoria propia (`_cam_descenso`) persigue al portador a 300 px/s y lo lleva a un tercio de pantalla; el suelo de la persecución es EXACTAMENTE el encuadre de la pelea, así que al armarse la trampa la cámara YA está ahí — medido: pantalla_y=380 constante, 0 fotogramas fuera de vista, empalme sin corte. (Suavizar contra `offset` era pelear contra `Camera.update`, que lo recalcula entero cada fotograma: la x quedaba clavada a 61 px del encuadre y la y saltaba 125 px al entrar — por eso la memoria propia.) (2) **D-01·C y D-01·D cerrados** — el rediseño del acceso queda COMPLETO: ver sus filas en EN CURSO. `test_ofrendas_paburu` (10) + los 3 del mecate actualizados (la boca ahora nace sellada: el arnés la abre a mano). Capturas `r16_*` | ↓ Ronda 16 |
| **15** | **#49b — LA FORMA DEL ÁNIMA, TALLADA DEL CONCEPT.** Alejandro pidió que el ulti «se vea exactamente igual» a su concept de la transformación. El muñeco de partes lo hizo barato: `heroe(forma_anima=True)` compone LAS MISMAS poses con la MÁSCARA en vez de cabeza+bufanda (madera con luz propia, los TRES GLIFOS de hueso en la frente —venado/serpiente/gavilán—, ojos de almendra encendidos con rabillo caído, la espiral tallada en la boca), el cuerpo ennegrecido a cuero conservando el sombreado, el filo verde HORNEADO en el contorno (0.32 y no 0.5: con medio filo las extremidades de 2 px se volvían un esqueleto de neón — se vio en el zoom), y LEVITA: la figura sube 2 px y deja su charco de luz bajo los pies, como el concept. Nueve hojas `anima_player_*.png` con los mismos conteos; la escena las prefiere y el re-teñido queda de red de seguridad; la corona de jirones sube de 16/s a 26/s sesgada a la cabeza. El tajo de los ataques también se enciende (se pinta antes del filo, a propósito). Nota del profesor incorporada al canon: el héroe no distingue género a propósito — y la Forma, con la máscara puesta, menos todavía. Tests: `test_la_forma_del_anima_usa_las_hojas_talladas` + los 3 de #49 revalidados sobre las hojas nuevas (sin oro ✓, filo ✓, préstamo expira ✓). Capturas `r14_forma_tallada_*` | ↓ Ronda 15 |
| **14** | **#50 — EL PORTADOR CON ROSTRO.** Alejandro generó el concept del portador (con el prompt del diseño de la Forma del Ánima) y pidió el cambio de personaje. Restricciones que decidieron el cómo: `assets/sprites/player` los REGENERA `generate_all_assets.py` del profesor (reemplazar ahí = perder el trabajo, la lección del tileset) → hojas propias en `assets/sprites/heroe_tilawa/` + swap de `_sprite_frames` en la escena (el truco del #49, cero motor, sólo este stage); y el motor dibuja 32×32 → «exactamente igual» es la lectura del concept a esa escala. `tools/gen_heroe_tilawa.py` construye al héroe como MUÑECO DE PARTES (capa rasgada hasta el muslo, piernas con botas, torso con correaje/hebilla, brazos con vendas, melena azabache con flequillo, bufanda parda con punta colgante) y compone las 9 hojas con los mismos archivos que el motor: idle respira, walk de 8 con brazos en oposición y capa flameando, salto/caída con capa alzada, cuclillas cumpliendo el contrato `offset_y=0` del motor (pies en fila ~24, medido de SUS hojas — sin eso se hundía 6 px), ataques con tajo, y el caído APOYADO en la losa (la v1 flotaba, se vio en el contact-sheet). La Forma del Ánima se talla sobre el héroe (el ulti lo transforma a ÉL) y el respawn lo reviste. 3 iteraciones revisadas a ojo con zoom (cara v1 enorme → melena del concept; brazo invisible a 1 px → 2 px). **Y LA COSTURA DEL HUD**: el motor carga `assets/ui/portrait_*.png` aparte de las hojas, así que la esquina seguía enseñando la cara del personaje viejo — auditado al preguntar Alejandro «¿todo está acorde o hay que adaptar más?». Cuatro retratos del héroe (normal/herido/crítico/muerto: ojos apretados, gota de sudor, piel gris) inyectados en `HUD._portraits` (atributo plano, cero motor). Alejandro generó su propia hoja completa con espada; decisión conjunta: se queda la nuestra — el portador no lleva arma en ninguna mecánica del motor y una espada solo dibujada mentiría. Al profesor le gustó («ahora se lo tendré que pasar a todos»). Tests `test_heroe_tilawa_paburu` (8). Capturas `r14_*` | ↓ Ronda 14 |
| **13** | **EL PLAYTEST DEL 2026-08-17, entero.** (1) **El mecate agarra de verdad** (D-01·I segunda vuelta, ver arriba). (2) **La liana huérfana de la entrada, fuera**: pedía la tecla G que nadie conoce y el hueco que salvaba se salta a pie — «ni se usa para nada», correcto. (3) **El resorte al bolsillo** (3952 → 4048, impulso -700): el bolsillo del otro lado del foso era una trampa medida — el salto simple no cruza los 48 px de vuelta y el bot acabó CAYENDO al foso; ahora un brinco sobre el resorte te devuelve por encima de la boca (aterriza en ~3990, medido). (4) **Los peldaños del brocal**: el nadador que TOCA el salto no salía nunca del pozo (el bot murió ahí a los 25 s — sólo salía SOSTENIÉNDOLO, y eso no lo descubre nadie); un escalón de escombro sumergido a 592 en cada orilla y el pozo se sale con el brinco corto (primera versión a 576 EMPUJABA al nadador — medido y corregido). (5) **Los solapes visuales** («se ve que chocan aunque no chocan»): `Camino_04`+`Camino_05` eran dos sarcófagos incrustados 48 px (→ una pieza de 96) y la `Losa_Hundible_02` invadía 16 px el carril del ascensor (→ 2968). (6) **Las ofrendas se ven como monedas**: pila dibujada en la piel (tres tumbadas, dos encima, una parada con la espiral), el «cuadro» del catálogo fuera — eran LA queja repetida de los coins. (7) **El letrero de la tirolesa** («G AGARRARSE», flotando junto al cable cuando el portador se acerca): la tirolesa era contenido muerto sin la tecla. **(8) LAS NUBES** (D-01·K). **(9) LA FORMA DEL ÁNIMA (#49 + la idea del ulti)**: al estallar el ulti (Z+X con la barra llena) el portador viste la máscara 6 s — fotogramas re-teñidos píxel a píxel (hierro azulado conservando el sombreado, madera de máscara en la cabeza, rendijas de ojos verdes en la primera fila con carne — a altura fija caían en píxeles transparentes, se vio en el zoom—, filo de luz ánima en todo el contorno) + corona y goteo de jirones verdes que suben y se deshacen. JAMÁS dorada: el oro es del juez. Cero mecánica: el daño del ulti es del motor; la muerte desviste. Verificación: bot geométrico de 900→boca sin un solo atasco de 4 s, 18 tests nuevos (`test_ronda_de_playtest_paburu.py`), capturas `r13_*` en `capturas_sesion/` | ↓ Ronda 13 |
| **12** | **MIGRACIÓN AL MOTOR v2** — el profesor arregló los 11 bugs del reporte (su `App.run` cita AUD-498 literal). Verificado con nuestras reproducciones medidas: reloj ✓ (el mundo vuelve solo), HUD de fases ✓ ([1,2,3,4]), envolvente del salto ✓ (87.1/42.8/85.5 — nuestros números exactos, renombrada `max_gap_expert`), coyote ✓, hundibles ✓, atravesables ✓ (`rects_atravesables_desde_abajo`), lianas ✓, respawn ✓. **Choque cazado y resuelto**: nuestros tres guardianes del hit-stop (AUD-467/479/498) duplicaban el drenaje del motor v2 — medido, el hit-stop caía de 4 a 2 fotogramas. Ahora ceden ante la huella `aplicar_escala_de_hitstop` y siguen enteros sobre un motor v1. Arneses actualizados al bucle nuevo (`actualizar_en_tiempo_real`). **La migración fue COMPLETA y en un solo sentido** — a `legacyofInfest` entraron, byte a byte desde la v2: `src/engine`, `src/framework`, `scripts`, **`tests/` del profesor** (18 cambiados + ~10 nuevos, incluido el trinquete del salto que ahora afirma lo contrario), **`tools/` del profesor** (su `generate_all_assets` trae el arreglo del ambiente en bucle — nuestro bug nº 10), el **stage4_1 nuevo** con sus fases, diálogos (`data/dialogues/stage4_1.json`), mapa y tilesets, y los retoques de `boss_venado` (fuera su apaño H-02 del HUD) y `stage0`. `legacyofInfestv2` queda INTACTA como referencia para la próxima entrega; su copia vieja de nuestro stage se ignora. Suite completa: 5.494 en verde, 0 fallos de paburu | ↓ Ronda 12 |
| **11** | **D-01 fase B (parcial)** — el cuenco de fuego apagado llevaba 3 px de oro y la pasada de bloom de la ruta de GPU los derramaba: cada cuenco florecía en un disco cálido de ~11 px, cuatro por círculo. Sólo se ve con tarjeta, por eso ninguna captura de arnés lo delató. Ceniza en su lugar. Y niebla propia del camposanto (baja, horizontal, azul) sustituyendo el velo liso y cálido del clima `fog`, que le comía el tinte a la noche | ↓ Ronda 11 |
| **10** | **D-01 fase A** — fuera el sorteo: el camposanto se recorre entero (era el 57 % de media), la tirolesa y el resorte por fin se alcanzan, y se baja a la catacumba por el **mecate del sepulturero**. De paso: las lianas del motor **no las dibuja nadie** — la del primer minuto llevaba invisible desde siempre | ↓ Ronda 10 |
| **9** | **AUD-498 — EL CUELGUE DEL MURCIÉLAGO**, cazado y verificado en GL. Es del motor: `pasos_fijos()` acumula el delta escalado, el hit-stop lo pone a 0 y el bucle deja de llamar a la escena. Abrazo mortal | ↓ Ronda 9 |
| **8** | AUD-479 perro guardián del hit-stop · AUD-479b el murciélago no baja al ras · AUD-496 tope de marcas del sello · AUD-497 los custodios sólo en la Forma 2 | ↓ Ronda 8 |
| **Auditoría** | AUD-480…495 — auditoría integral del stage como producto: bugs funcionales, físicas, visuales, game feel, código, optimización, casos extremos. Informe en `INFORME_AUDITORIA.md` | ↓ Auditoría |
| **7** | AUD-478 la cripta tejida con ruido determinista · **AUD-478c** el `tilecount` codificado a mano hacía INVISIBLES todos los tiles nuevos (por eso «las plataformas siguen feas») | ↓ Ronda 7 |
| **6** | AUD-475 el aviso de lore no baja con el jugador · AUD-476 los murciélagos recorren el mapa · AUD-477 el jefe avisa con el cuerpo | ↓ Ronda 6 |
| **5** | AUD-471/474 dirección de arte de los ecos de los guardianes · AUD-472 muebles de los círculos · AUD-473 población 12 → 8 | ↓ Ronda 5 |
| **4** | AUD-467 el cuelgue golpe + cinemática · AUD-468 el ahogado confinado al pozo · AUD-469 fuera la luz pegada al personaje · AUD-470 población 19 → 12 | ↓ Ronda 4 |
| **3** | AUD-462 los moradores estaban enterrados (la `y` del TMX cambió de sentido) · AUD-463 «color caca»: la hora y la luz robada · AUD-464 dos avisos de lore menos · AUD-465 el «poder azul raro» eran los marcadores del motor · AUD-466 los cuatro círculos dejan de ser la misma pieza | ↓ Ronda 3 |
| **2** | **AUD-461** la capa del jefe moría entera en la ruta de GPU (la causa raíz de «todo horrible») · R2-8 señal del círculo sorteado | ↓ Ronda 2 |
| **1** | Plataformas invisibles · murciélagos invisibles · máscaras de la verja invisibles · el «chorro» cada segundo (bug del clima del motor) | ↓ Ronda 1 |

## ⚑ REPORTADO AL PROFESOR

`BUGS_DEL_MOTOR.md` **v2** — 11 bugs de `src/engine` y `src/framework`,
ordenados por gravedad y cada uno con **el parche completo** (código exacto
antes/después), reproducción medida y riesgos. Más 4 hallazgos colaterales.

Los tres que más importan:

| # | Gravedad | Qué |
|---|---|---|
| 1 | 🔴 BLOQUEANTE | El primer golpe que conecta congela el juego **para siempre**. Arreglo: 1 línea en `App.run` |
| 2 | 🔴 CRÍTICO | El respawn te expulsa fuera del mapa y caés eternamente **sin morir**: partida perdida. Estaba enmascarado en 10 de mis 12 checkpoints por un error de dibujo del mapa |
| 5 | 🟠 ALTO | **El calificador sobreestima el salto ×4** y da puntos de ritmo por saltos imposibles. Medido: 4 de los 17 mapas del curso bajarían de nota al corregirlo |

En tres de ellos mi diagnóstico inicial (leyendo el código) era **falso**, y
quedó escrito en el documento: lo que los encontró fue medir.

---

## Contexto mínimo para retomar

- Nivel completo y funcional: cementerio + catacumba (Sala del Juicio) +
  jefe de 4 formas + EL OFRECIMIENTO + Epílogo + SFX propios + compás de
  la canción + poses por forma + skin de mecánicas + intro auditada.
  Nota del calificador: **130/130 (100 %)** en stage y **100/100** en boss. Batería propia:
  `pytest -k "paburu or guardianes or forma3 or ritmo or poses or skins or intro or ritual"`
  → 108 en verde.
- **Nunca se toca `src/engine` ni `src/framework`** (solo tests-guardián
  de documentación cuando cambian conteos). Todo vive en
  `src/stages/boss_paburu/` + `tools/gen_paburu_*.py` + `tests/`.
- Lore intocable: guardianes = venado / serpiente / gavilán (los tres
  jefes previos); cultura ficticia Tilawa — jamás nombrar culturas
  reales en el juego. La canción del jugador es `bgm_paburu.ogg`
  («Judgment of the Ancestors», compuesta por Alejandro, 136 BPM).
- Verificar siempre con capturas reales del juego, no con preview_tmx.
- Cerradas con detalle en `DISENO_NIVEL_Y_JEFE.md` §7: mejoras A (epílogo),
  B (SFX), C (BPM), D (poses), #43 (intro) y #44 (skin de mecánicas).

## PENDIENTE

| Tarea | Trabajo | Detalle clave |
|---|---|---|
| #46 — Playtest humano + rendimiento | Alejandro juega: timing del parry del Juicio, FURIA de la Perla en esquinas, dificultad del arco completo a mano, FPS con F11 (si baja: `bloom` 0.55→0.4 en el TMX). Ahora también: la entrada + avisos de lore + vigilante del camino final en partida real. | Único punto que el código no puede validar solo. |
| #49 — La máscara Tilawa (aspecto del jugador) | **Anotado, sin empezar.** El sprite del héroe no gusta. Una tecla intercambia el diccionario de frames del jugador por otro juego de hojas: ~30 líneas en el stage, CERO framework (mismo truco que `_agrandar_frames` y que la piel de las mecánicas). Alcance elegido: **estético con un poco de diegético** — el jugador se PONE una máscara tilawa y cambia de aspecto. Sin cambios mecánicos: misma vida, mismo daño, mismos estados. Encaja con el lore (las máscaras de la verja son los guardianes que bajan a pelear en la F2) y no toca balance. Falta: decidir el aspecto y si la máscara es un recogible del mapa o una tecla libre. | Pendiente de decisión de Alejandro |
| #47 — EP2 (Clase 8): Unidad VII | `compute_histogram` dirigiendo LÓGICA de juego + brillo/contraste documentado + un kernel (`apply_kernel`/`gaussian_blur`/`sobel`/`canny`) justificado. README: secciones U-VI/U-VII con capturas antes/después. | Rúbrica §5 — hito futuro, no de la entrega actual. |
| #48 — EP3 (Clase 11): Unidades VIII-IX | Segmentación (otsu + morfológica, `connected_components` con efecto observable) + clasificador (`extract_features` → PatternRecognitionTools, salida cambia el juego de ≥2 formas, dataset ≥10/clase, accuracy ≥0.70). README: pipeline completo. | Rúbrica §6 — hito futuro. |

**Auditoría contra los enunciados (2026-08-14):** `grade_boss.py` 100/100;
`grade_stage.py` **130/130** (se arregló el ritmo: NextTrigger enterrado en la losa de la antecámara —antes su posición en el cielo metía 1.353 px fantasma en la cadena de checkpoints—, 12 checkpoints con hueco máximo 480 px incluido el del foso a media caída, y los dos pedestales del círculo II como el salto exigente que faltaba; guardián `test_nota_paburu.py`, 3); propiedades obligatorias completas (se agregó
`zone=4`, la pedía el enunciado y el motor la lee); README del stage con la
cabecera YAML obligatoria (`23_DATA_SCHEMAS.md` §7 — la leen los scripts) y
sin afirmaciones de la era EP1 («solo Forma 1»).

Al terminar #46: **re-auditoría integral** (pedida explícitamente).
`#45 (ritual sembrado)` cerrado — detalle en `DISENO_NIVEL_Y_JEFE.md` §7,
incluida la fuga «brunca» sellada (cultura real → Tilawa en todo lo visible).

**Bug de playtest cazado (2026-08-15):** el «chorro raro cada segundo» era
el clima `fog` del motor loopeando `sfx_environment_wind_indoor.wav` (2,0 s,
loop infinito). Solo lo oyen los mapas con `fog`/`snow` — por eso al profesor
no le pasaba. Arreglo del lado del stage: ambiente propio de 12 s con loop
perfecto por construcción (`gen_paburu_sfx.ambiente_camposanto`), fundido
encima del clima en `on_enter` por la API pública. Tests en
`test_sfx_paburu` (empalme sin salto + reemplazo cableado). Vale la pena
CONTARLE al profesor: es un bug real del motor para cualquier entrega que
use esos dos climas.

**Ronda 1 del playtest de Alejandro (2026-08-15) — 4 hallazgos, 4 arreglos:**
1. *Plataformas invisibles*: las 24 cornisas/aleros de los círculos tenían
   colisión sin tiles (`muebles_del_circulo` perdió el dibujo en la
   migración). Ahora el generador dibuja DESDE los mismos rects; guardián
   colisión↔tiles en `test_nota_paburu`.
2. *Murciélagos invisibles*: sprite ×2 (28×20, vecino más cercano) y
   población 8→6.
3. *Máscaras de la verja invisibles*: v2 — madera clara, ojos espectrales
   encendidos con halo, firma en oro por guardián.
4. *«Chorro» cada segundo*: loop de 2 s del clima `fog` del motor
   (reportable al profesor); ambiente propio de 12 s en loop perfecto.
Además: `validate_assets` a 0 errores (`bgm_paburu.wav` = TU canción
convertida — el motor prefiere .wav; el placeholder renombrado quedó como
`bgm_paburu_placeholder_original.wav`).

## RONDA 2 — LO RESUELTO EL 2026-08-16 (AUD-461, la causa raíz)

**R2-1 CERRADO — la luz era inocente; el culpable era `draw()`.** Se
reprodujo el flujo completo en un contexto OpenGL real (Mesa/llvmpipe,
GL 4.5) instrumentando la tubería pasada a pasada: el mapa de luz SÍ
viaja a la tarjeta y el sombreador SÍ multiplica, en cualquier máquina.
Lo roto era otra cosa: **`App` no llama a `draw()` en una escena con
ruta de GPU** (AUD-343/371: llama a `dibujar_mundo` y `dibujar_ui` por
separado), y TODA la capa propia del stage vivía en un override de
`draw()`. Consecuencias medidas, cada una un síntoma de la ronda:

- la intro corría INVISIBLE (sin fundidos, sin texto, sin actores):
  ~25 s de sala quieta que se leyeron como **congelamiento (R2-3
  explicado — no hay cuelgue; la corrida `--debug` limpia ya lo
  sugería)**;
- los guardianes y **los ataques de la ronda de la F2 golpeaban sin
  dibujarse** (una parte de R2-9 era esto, no balance);
- las picadas del vigilante castigaban desde la nada (superficie);
- el «héroe invisible» (R2-2): nunca se ocultó — con la intro invisible
  y el encuadre fijo de la sala, no había nada que dijera dónde mirar.

Arreglo en `boss_paburu_scene.py` (AUD-461): la capa se reparte entre
`dibujar_ui` (ruta GPU — el overlay se compone tras la luz, mismo punto
del orden de pintado) y `dibujar_mundo` (software/arneses). Guardián:
`tests/test_capa_gl_paburu.py` (4) — las cuatro fallan contra el código
anterior. Verificado con capturas del juego corriendo por la tubería GL
real: la intro muestra texto y bandas, los tres espíritus se ven en la
F2, y la nota se mantiene (130/130, 100/100, batería propia en verde).

**Y el «marrón fullbright» no es un bug de luz: es `AMBIENT_BY_PHASE =
(0.80…1.00)`**, la decisión que subió la penumbra porque a 0.62 el
jugador se perdía contra la pared. La captura «headless donde la
penumbra funciona» era OTRO momento (la rampa de LUZ_TRAMPA 0.16 del
descenso). Con la intro por fin visible hay que juzgar R2-6 de nuevo —
esa decisión de dirección de color sigue abierta.

**R2-8 CERRADO — el círculo sorteado ya se anuncia.** Brasas
deterministas (sembradas con el nombre del círculo) + un halo que
respira sobre el emblema del círculo elegido, y SOLO el elegido; se
apagan al descender. Blits aditivos en el mundo (en el overlay GL un
blit aditivo no toca el alfa y la tarjeta lo compondría invisible —
documentado en el código). Guardián: `tests/test_senal_circulo_paburu.py`
(5). Verificado en captura GL: se leen desde fuera del círculo, antes
de pisarlo.

**REPORTABLE AL PROFESOR (bug del motor, como el del clima `fog`):** en
el camino enteramente software (sin ModernGL o con el contexto caído),
`App._draw` llama solo a `dibujar_mundo` y nunca a `dibujar_ui` ni a
`draw()` — toda escena `StageScene` pierde HUD, cinemáticas, minimapa y
subtítulos. Verificado con capturas (SDL dummy): el mundo sale, la
interfaz no. En máquinas con GL nadie lo nota porque la ruta GPU sí
compone el overlay. Afecta a cualquier entrega que se corra sin tarjeta.

## AUDITORÍA INTEGRAL (2026-08-16) — AUD-480…495

Informe completo en `INFORME_AUDITORIA.md` (mismo directorio). Cuatro auditorías
paralelas —física/plataformas, bugs funcionales, código/rendimiento y el jefe—
con la escena ejecutada, no leída. **16 correcciones aplicadas, cada una con una
prueba que falla sin ella** (`tests/test_auditoria_paburu.py`).

Los cinco que impedían jugar: los **10 checkpoints de superficie no existían**
(escritos con la convención vieja de `y`, la misma trampa de AUD-462); **morir
en la catacumba expulsaba del mapa** y la partida se perdía; **el mapa no tenía
muros de borde**; **la embestida del venado pasaba 17 px por encima del jugador**
(y sólo pegaba si saltabas, invirtiendo su propia lección); y **el Juicio final
podía matar**, contra el «se gana siempre» del diseño.

La curva de dificultad iba al revés —10,2 → 21,3 → 19,7 → **12,8** de daño/min—
porque dos de los cuatro patrones de la Forma 4 no podían tocar a un jugador de
pie. Corregido; **falta volver a medirla** (objetivo: que el acto final vuelva a
ser el pico, ≥24/min).

PENDIENTE, con su porqué en el informe: cinco decisiones de plataformas que
cambian el recorrido (los pedestales del círculo II apuntan a plataformas
inalcanzables; ocho repechos están a 80 px, justo EN el límite del salto), las
teclas de depuración que siguen activas en la build normal, y **tres bugs del
motor** que vale la pena contarle al profesor: el coyote time no funciona desde
el aire, las `SinkingPlatform` nunca se hunden (nadie llama a `marcar_pisada`) y
`atravesable_desde_abajo` se ignora en las plataformas móviles.

## RONDA 10 — D-01 FASE A: FUERA EL SORTEO (2026-08-16)

**El playtest, en una frase:** «no se puede disfrutar el nivel porque lo manda
directamente a Paburu», y «la tirolesa no la vi». Son **el mismo problema**.

Medido: el disparador de un círculo mide 416 px de ancho y va pegado al suelo,
así que es imposible cruzarlo a pie. El sorteo no elegía dónde te atrapaban —
elegía **dónde terminaba el nivel**:

    círculo I → x=1360 (33 %) · II → 1936 (47 %) · III → 2736 (66 %)
    círculo IV → 3536 (85 %)                        media: 57 %

Y detrás del corte quedaban siempre la tirolesa (x=3840), el resorte (3952) y
la Puerta_Final (4000): **inalcanzables en las cuatro partidas posibles**. La
tirolesa nunca se perdió ni se rompió; estaba intacta y muerta.

**Lo aplicado (fase A, ver `DISENO_ACCESO_CATACUMBA.md`):**

- `Cementerio.leer` ya no sortea: `elegido` es siempre la boca. Los cuatro
  círculos siguen emitiendo su evento —lo van a necesitar las ofrendas— pero
  ninguno baja. Un mapa de la era del sorteo (sin boca) conserva el
  comportamiento viejo en vez de quedarse sin jefe.
- **El mecate del sepulturero**: un `Vine` de 736 px por el foso, del borde de
  la losa al suelo de la antecámara. Bajar deja de ser algo que te pasa y pasa
  a ser algo que hacés — y repite, invertido, el primer gesto del nivel (la
  liana de x=432).
- El disparador de la boca se mudó de la garganta del foso al FONDO. Con el
  teleport daba igual dónde se cruzara; con el mecate, armar la pelea en el
  primer metro de cuerda deja al jugador colgado a 560 px del suelo con el
  jefe emergiendo debajo.
- `descender()` sólo teleporta si el jugador NO está ya dentro: pasa de ser el
  camino a ser la red.
- La señal de brasas (R2-8) se reapunta del círculo sorteado a **la boca**:
  en 4160 px oscuros, un faro al final del camino.

**Y un bug del motor de propina.** `Liana` es un componente puramente físico y
**ningún sistema del framework lo dibuja**: `Liana_01`, la del primer minuto
del nivel, llevaba desde siempre siendo una escalera invisible en el aire. Se
le dibuja cuerda —dos hebras torcidas, nudos cada 40 px y su estaca— con el
resto de las pieles de mecánicas (AUD-465). Reportado como nº 3 del motor.

**Postmortem del arnés:** la primera pasada del playtest automático daba verde
sin despachar el bus. El bus del motor es diferido (`emit` encola, `App.run`
despacha), así que se veían los disparadores marcarse como disparados y
**nunca** su consecuencia. Un arnés que sólo llama a `update` miente. Es el
mismo error que dejó vivo el cuelgue de AUD-498 dos rondas.

Tests: `test_acceso_catacumba_paburu.py` (7, caminan el mapa de verdad) y
`test_cementerio_paburu` reescrito para defender lo contrario de lo que
defendía. Verificado con capturas del framebuffer de GL —no de
`internal_surface`, que en la ruta de GPU no lleva el overlay—: 130/130,
100/100, 186 en verde.

## RONDA 9 — EL CUELGUE, CAZADO DE VERDAD (2026-08-16)

**AUD-498 — el murciélago no tenía la culpa: el bucle del motor deja de llamar
a la escena.** Tercer reporte del mismo cuelgue («ataqué un murciélago y se
congeló todo; la música siguió sonando»). AUD-467 y AUD-479 no lo arreglaron, y
la razón es simple y fea: **los dos viven en `update()`, que es precisamente el
método que deja de correr**. Mis pruebas llamaban a `escena.update(dt)` a mano,
así que daban verde con el juego colgándose de verdad.

La cadena, reproducida con el bucle real (180 fotogramas → **cero** pasos de
simulación):

1. Un golpe conecta → `update_hitstop` registra `escalar(FUENTE_HITSTOP, 0.0)`
   → `clock.time_scale == 0`.
2. `DeltaClock.tick` → `self._dt = raw_dt * 0.0` = **0.0**.
3. `DeltaClock.pasos_fijos` acumula el delta **escalado**: `_acumulado += 0.0`.
   El `while _acumulado >= FIXED_DT` no entra nunca → **cero pasos**.
4. `App.run`: `for paso in clock.pasos_fijos(): scene_manager.update(paso)` →
   la escena no se actualiza.
5. El drenaje del hit-stop vive en `StageScene.update`. Que no corre. Ir a 2.

La música sigue sonando porque `audio_manager.update` va con `unscaled_dt` y
**fuera** del bucle de pasos, igual que `_process_events` y `_draw`. Es AUD-001
por la otra puerta: aquel arreglo garantizó drenar con tiempo real, y AUD-390
(el paso fijo) quitó la garantía de que el drenaje llegue a ejecutarse. El aviso
del motor sigue escrito en `clock.py`, apuntando a la puerta equivocada.

**Del lado del stage** —sin tocar el motor— el latido se toma prestado del
dibujo: `_reanimar_el_reloj()` es lo primero de `dibujar_ui`, que sí corre cada
fotograma en los dos caminos (GPU y software). Sólo actúa cuando `clock.dt` es
exactamente 0 —la firma inequívoca de la trampa— y drena con tiempo **real**,
así que el golpe conserva sus 0,05 s de peso. Techo de `TOPE_HITSTOP` como
cinturón y tirantes.

Tests: `test_reloj_atascado_paburu.py` (3), con el arnés replicando `App.run`
línea por línea. Verificado que **falla sin el arreglo** («180 fotogramas y
CERO pasos de simulación»). Reportado como bug BLOQUEANTE nº 1 del motor en
`BUGS_DEL_MOTOR.md`: afecta a cualquier entrega del curso, no sólo a ésta.

## RONDA 8 — EL CUELGUE, CERRADO POR ARRIBA (2026-08-16)

**AUD-479 — un perro guardián sobre el hit-stop.** El playtest volvió a
colgarse: «golpeé un murciélago apenas iniciando y se quedó pegado», con la
pantalla partida a medio redibujar — que es exactamente cómo se ve un
`time_scale` en cero. AUD-467 había tapado el camino que sabíamos reproducir
(golpe + escena bloqueante); éste era otro.

La lección es la que enseña el segundo cuelgue y no el primero: **enumerar
casos no sirve**. `_update_gameplay` es quien drena el contador, y hay varios
caminos por los que ese método no corre en un fotograma (una escena que
bloquea, la entrada del jefe, el juego terminado, una pausa que llega en el
peor momento); cada uno, si coincide con un golpe recién conectado, deja el
reloj parado PARA SIEMPRE. Una condición que liste los conocidos siempre se
queda corta ante el siguiente.

Así que ahora hay un TECHO, no una lista: si el hit-stop lleva vivo más de
0,5 s reales —diez veces el peor caso legítimo (0,05 s)— se acaba, venga de
donde venga, y queda un aviso en el registro. En juego normal no se alcanza
nunca, así que el golpe conserva su peso; y si aparece un camino nuevo que no
drena, el jugador pierde medio segundo en vez de la partida. Guardián:
`test_cuelgue_y_pozo_paburu` (el que rompe el drenaje normal a propósito y
exige que el mundo vuelva igual).

**AUD-479b — el murciélago ya no baja al ras del suelo.** «Aparte está súper
abajo»: persiguiendo a un jugador que camina, el descenso de AUD-476 lo
dejaba casi rozando la losa, y un murciélago a esa altura deja de ser el
enemigo que obliga a mirar ARRIBA — que es su único trabajo. Ahora el tope
son 64 px por encima del centro del jugador.

## RONDA 7 — LA CRIPTA, Y EL BUG QUE LA ESCONDÍA (2026-08-16)

«Siguen viéndose las plataformas feas, no hay originalidad; la catacumba se
supone que es lo mejor y se ve horrible.» Las dos quejas tenían la MISMA
causa, y no era de arte.

**AUD-478c — EL TILECOUNT ESCRITO A MANO: los tiles nuevos NO EXISTÍAN.** El
generador declaraba el tileset así, a pelo:

    tilecount="72" ... <image ... width="128" height="144"/>

y ese número se quedó atrás dos veces seguidas: con los muebles del camposanto
(AUD-472, 88 tiles) y con la cripta (AUD-478, 104). **pytmx no da error**: los
GIDs por encima del `tilecount` declarado simplemente no existen, así que se
dibujaban como huecos. O sea:

  · los sarcófagos, vigas, costillares y plañideras de AUD-472 llevaban toda
    una ronda siendo INVISIBLES — por eso «siguen viéndose feas»: lo que se
    veía era la cornisa vieja donde el mueble no llegó a dibujarse;
  · la pared de la catacumba tenía agujeros, y por ellos se veía el cielo del
    camposanto — **luna incluida, dentro de la cripta**. De ahí «se ve
    horrible»: no era el arte, era que faltaba media pared.

Arreglo: el generador MIDE el PNG (cabecera IHDR, sin montar pygame) en vez de
escribir su tamaño. Un generador que declara a mano las medidas de un fichero
que él mismo produce está esperando a desincronizarse.

**AUD-478 — LA CRIPTA, rehecha.** Y ahora que se ve, se rehízo de verdad. La
pared era una línea del generador:

    for ty in ...:
        for tx in ...:
            bg_near[ty][tx] = G_SIL_COL_SHAFT

UN tile en cientos de casillas — y encima un FUSTE DE COLUMNA, de ahí las
rayas verticales que recorrían la sala de arriba abajo. Da igual lo bien
dibujado que esté un tile: repetido en cuadrícula, el ojo ve la cuadrícula.

Dieciséis tiles nuevos (filas 12-13) y un tejido con ruido determinista:
cuatro sillerías con las juntas corridas y de alturas desiguales, más los
accidentes que tiene una cripta —la grieta que cruza dos hiladas, la humedad
que baja de una junta, la raíz que entró por arriba—, colocados donde el ruido
dice y no «cada N».

El columbario dejó de ser una estantería: las filas ONDULAN (±1 tile según el
sitio), el paso alterna 64 y 80 px, y los nichos salen de una bolsa —tapiado
(el más común, como en un columbario real), abierto con su cráneo al fondo,
roto con la losa caída— más UNO con una vela todavía encendida: alguien vino,
y no hace tanto. Algunos llevan su epitafio ilegible debajo y alguna cadena
colgando del dintel. Dos telarañas en las esquinas altas, no doce.

El retablo tiene DOVELAS: un arco de piedra son cuñas, y verlas es la
diferencia entre «hay un arco» y «alguien construyó esto».

Y la jerarquía, que es lo que hacía que todo pesara igual: la pared bajó dos
escalones de tono. Es FONDO. Lo tallado sube solo, sin tocar el mapa — la
misma lección del rediseño de la sala: el cuarto se lee por contraste.

## RONDA 6 — LOS PENDIENTES ABIERTOS, CERRADOS (2026-08-16)

Se aplicaron los tres que quedaban vivos de la ronda 2. Con esto la lista de
la RONDA 2 queda entera en verde.

**AUD-475 (R2-4) — el aviso de lore ya no baja con el jugador.** La caja del
motor mide 70 px de alto y se cierra sola por tiempo, pero el descenso no
espera a nadie: el cartel del camposanto seguía en pantalla DENTRO de la
catacumba, encima de la entrada del jefe — el momento que el nivel entero
prepara, compartido con un letrero de arriba. `_descender_a_la_catacumba`
llama a `MessageBox.hide()` antes de apagar la luz, por la API pública.

**AUD-476 (R2-5) — los murciélagos por fin recorren el camposanto.** El
reporte («no bajan, se mueven pero no por el mapa») describía exactamente lo
que hace `SineFlight`: avanza en horizontal y **rebota a ±96 px de su origen**
(está fijo en el motor). En un mapa de 4160 px eso es un bicho colgado de un
clavo. Clase propia `MurcielagoDelCamposanto`, sin tocar el motor y sin el
picado que ya se probó y se rechazó (inesquivable en pasillo):
  · RONDA LARGA — al llegar al tope de los 96 px se le corre el ANCLA en vez
    de rebotar, así que el vaivén es el mismo pero el centro viaja. Medido:
    305 px de recorrido contra los 192 de antes, y sin escaparse (tope 240 px
    a cada lado de su casa).
  · BAJA A MIRAR — al detectar al jugador el ancla desciende a 30 px/s con
    tope de 96. No es una picada: es que el murciélago se acerca. Era la otra
    mitad de la queja.

**AUD-477 (R2-9, la mitad que es legibilidad) — el jefe avisa con el cuerpo.**
De las dos cosas del reporte —«cómo están hechos» y «cuándo atacan, sobre todo
en la última fase»— la segunda es legibilidad y se puede arreglar sin tocar un
número de balance. Cada patrón ya traía su telegraph (el rayo avisa, el sello
avisa, el orbe avisa), pero en la Forma 4 hay cuatro patrones que pueden
solaparse y el ojo no sabe dónde mirar: faltaba el aviso del CUERPO, uno solo
y común a las cuatro formas. Se reutiliza `_pose_cast_t`, que el planificador
ya arma para TODO patrón (mejora D): mientras vive, el jefe lleva un anillo
que COLAPSA hacia él —la dirección que dice «se está cargando»— con cuatro
marcas girando en los ejes. Un solo tell, el mismo siempre: así se aprende.
Se calla en el epílogo, donde no hay ataque que anunciar.

**Sigue pendiente y es TUYO:** el balance de los ataques del jefe (la primera
mitad de R2-9, «cómo están hechos»). Hace falta jugar la Forma 4 con todo lo
de estas rondas puesto —los ecos visibles, el aviso del cuerpo, la sala en
penumbra real— y decir qué ataque concreto se siente mal y en qué. Tocar
números sin eso es adivinar.

## RONDA 5 — DIRECCIÓN DE ARTE (2026-08-16, cuarta tanda)

Pedido: «dibujá bien los poderes de los guardianes», «reducí MÁS los enemigos
(cantidad, no tamaño)» y «las plataformas se ven demasiado genéricas, quiero
que seas auténtico». El log de `--debug` salió limpio: sólo `pyscroll buffer
redraw` y `scrolling too quickly`, que son mensajes normales del scroller.

**AUD-472 — LAS PLATAFORMAS SON MUEBLES, NO CORNISAS.** Ésta era la crítica
buena: el nivel entero se apoyaba en UNA pieza —la cornisa de tres tiles
(borde, relleno, borde)— estampada cuarenta veces. Variar su ancho y su altura
(AUD-466) arregló el ritmo del recorrido, pero no el fondo del asunto: **en un
cementerio no hay cornisas; hay cosas que quedaron ahí.** Cuatro familias
nuevas en el tileset (12 tiles, filas 10-11 del atlas), cada una con su
izquierda / centro / derecha para componerse a cualquier ancho:

  · **SARCÓFAGO** — tapa corrida con greca de oro; alguien lo abrió.
  · **VIGA** — madera del techo hundido de un mausoleo, con clavos de hierro
    y su chorreón de óxido.
  · **COSTILLAR** — el hueso grande de algo enorme, con las costillas
    colgando y medio enterrado.
  · **PLAÑIDERA** — una estatua caída boca arriba; se camina sobre su costado
    y la cara mira al cielo.

Repartidas con criterio, no al azar: las pasarelas del pozo son VIGAS (es lo
que alguien pondría de verdad para cruzar agua, y explica que crujan); la
entrada se cruza por sarcófagos; el tramo medio alterna viga y hueso; el
camino final es de plañideras (las estatuas que un mausoleo rico tenía en la
puerta). Y cada círculo se amuebla con SU familia, alternando con la vecina
dentro del círculo — dos muebles iguales pegados vuelven a leerse como una
repetición. Los aleros del refugio conservan la sillería porque son
ARQUITECTURA (parte del muro), y mezclarlos borraría esa diferencia.

**AUD-473 — segundo recorte: 12 → 8.** A doce ya no había filas de bichos,
pero seguía habiendo relleno: dos murciélagos que enseñaban lo mismo, una
máscara de más en el tramo que ya tiene al vigilante. El camposanto no es un
nivel de matar — es un recorrido hasta un juicio, y su tensión la ponen el
pozo, el sorteo y la espera. Cada especie conserva su mejor momento y pierde
los ecos: ocho encuentros con nombre («el del pozo», «la pareja del círculo
II») en cuatro minutos de camino.

**AUD-474 — los ecos se MUEVEN, no sólo se dibujan.** AUD-471 les dio cuerpo;
esto les da vida: el venado **galopa** (el cuerpo sube y baja con la zancada y
se estira y encoge — un animal corriendo no es un óvalo que se traslada), el
gavilán **bate las alas** mientras cae (un ave en picada las ajusta, y eso es
lo que la separa de un proyectil), y el orbe **late** con los rombos girando
alrededor del núcleo — es el único parable de los tres, así que pide atención
por su pulso y no por su trayectoria.

## RONDA 4 — LO RESUELTO EL 2026-08-16 (tercera tanda)

Reporte de Alejandro: «después del combo se queda pegado», «los ataques de
los guardianes se ven muy toscos», «habíamos reducido los enemigos», «el
enemigo del agua lo sigue fuera del agua», «se ve como una luz en el
personaje, lo hace verse raro». Cinco, cinco cerrados.

**AUD-467 — EL CUELGUE. No era el combo: era el hit-stop.** Cada golpe que
conecta congela la simulación 0,05 s poniendo `time_scale` a 0, y quien la
descongela es `CollisionSystem.update_hitstop`, que vive DENTRO de
`_update_gameplay`. Y `_update_gameplay` no corre mientras una cinemática
bloquea (`StageScene.update`: `if not en_escena`) ni cuando esta escena se
salta `super().update()` durante la entrada del jefe. O sea: si el jugador
está pegando cuando arranca una cinemática —y aquí arranca al pisar el
círculo, que es cuando uno viene peleando— el contador se queda a medias con
el reloj en cero, **y no vuelve nunca**. Medido: 10 s después, `time_scale`
seguía en 0,0. Arreglo: la escena drena el contador cuando sabe que el padre
no lo va a hacer, con el `dt` real. `test_cuelgue_y_pozo_paburu` (2).
REPORTABLE AL PROFESOR: le pasa a cualquier entrega que combine golpes y
cinemáticas — el motor ya tiene el aviso escrito desde AUD-001 para el caso
hermano.

**AUD-468 — el ahogado sale del pozo a perseguir.** En patrulla ya no asomaba
(se corrigió la amplitud en la ronda 2), pero en ALERTA `EnemyFlying` persigue
en X y sigue la Y del jugador: en cuanto salías del agua, salía detrás. Ahora
la escena le inyecta el rect de SU pozo y el ahogado vuelve dentro después de
cada movimiento — sigue cazando en el agua, que es lo que lo hace temible, y
salir del pozo por fin sirve de algo. `test_cuelgue_y_pozo_paburu` (3).

**AUD-469 — la luz pegada al personaje. Había DOS.** Una era el farol de este
stage; la otra la pone el MOTOR (`_update_lighting` crea un foco de radio 100
sobre el jugador en cuanto hay un enemigo vivo). Con la noche real de AUD-463
ese disco cálido viajando con el sprite era lo primero que veía el ojo, y no
tenía explicación dentro del mundo. Las dos apagadas; `LUZ_CAMINO` 0.50→0.58
para compensar, y los charcos los ponen los catorce cuencos de fuego, que SE
VEN y por eso se entienden.

**AUD-470 — la población, bajada de verdad: 19 → 12.** Se había recortado dos
veces… contando los que se veían, con once enterrados (AUD-462). Al
desenterrarlos apareció la población real. El criterio no es «menos por
menos»: cada tramo conserva UNA pregunta y pierde las repeticiones (un segundo
murciélago en la entrada no enseña nada que no enseñe el primero). ~1 cada
350 px, con tramos limpios entre medias.

**AUD-471 — los ecos de los guardianes dejan de ser figuras geométricas.**
Se dibujaban con primitivas opacas: una elipse (venado), un círculo (orbe), un
rombo (gavilán). «Toscos» era exacto — y se juzga ahora porque hasta AUD-461
no se dibujaban en absoluto en la máquina del jugador. Misma trayectoria,
misma ventana, misma respuesta; cambia la técnica: superficies con alfa
compuestas sumando luz, tres capas (halo, cuerpo, núcleo) y silueta
reconocible — cornamenta de tres puntas curvadas, cuerpo serpenteante con los
rombos de la Terciopelo, alas de cinco plumas con la máscara ceremonial como
lo más brillante. Los telegrafiados también: el carril del venado dice la
ALTURA (que es lo que decide el salto) y el aro del orbe —el único parable—
avisa dónde va a nacer.

## RONDA 3 — LO RESUELTO EL 2026-08-16 (segunda tanda del mismo día)

Reporte de Alejandro sobre capturas: «ese poder azul raro», «el TMX parece
control C control V», «esas leyendas que salen a cada rato», «hay enemigos
bajo tierra», «el color parece caca, quiero que sea la noche». Cinco, y
cuatro tenían una causa concreta y medible:

**AUD-462 — los enemigos ESTABAN enterrados, literalmente.** Las 11 máscaras
y sukias tenían el `rect.top` en el suelo, o sea el cuerpo entero (24 px) bajo
tierra. Causa: el motor cambió la convención del TMX en AUD-455 —la `y` es el
borde SUPERIOR, no los pies— y este generador seguía escribiendo `FLOOR_Y`.
Se corrige en el generador (`SOBRE_EL_SUELO()`), no en el motor: los mapas del
profesor ya usaban la convención nueva. Guardián: `test_moradores_paburu` (2),
medido sobre la escena viva y no sobre el XML (leer el mismo número que
escribió el generador habría dado verde con los bichos enterrados).

**AUD-463 — el «color caca» era la HORA, y la penumbra no se aplicaba.** Dos
cosas a la vez, y por eso resistió dos rondas:
1. el mapa pedía `start_hour = dusk`, y el motor tiñe la imagen entera de
   (245,170,152) —ocre rosado— por el color grading. El nivel nocturno del
   juego se dibujaba a las siete de la tarde. Ahora `night`: (170,185,238),
   azul lunar;
2. `_aplicar_hora` (el reloj del mundo) **sobrescribía cada fotograma** el
   `ambient_brightness` que fijaba la escena, con `max(0.45, base × factor)`.
   O sea: las rampas de este stage —el negro del descenso (0.16), la luz por
   forma, las dos luces del veredicto— nunca llegaban a la pantalla. Por eso
   subir `AMBIENT_BY_PHASE` a 0.80 «no se notó»: no era ese número el que
   mandaba. Ahora la escena sobrescribe `_aplicar_hora`, conserva del reloj lo
   que sí quiere (tinte, bloom, clima, sombra solar, el latido del compás) y
   se queda con SU luz. `MIN_AMBIENTE` baja a 0.12 para este escenario, con su
   motivo escrito: aquí hay farol y catorce cuencos de fuego.
   Valores nuevos: camino 0.50, formas (0.42, 0.50, 0.58, 0.68).
   Guardián: `test_moradores_paburu` (3).

**AUD-465 — el «poder azul raro» era el marcador de posición del motor.** Los
tres rectángulos lila de la Galería I son cómo `dibujo_mecanicas.py` pinta un
`BloqueRitmico` («formas planas… el estudiante lo sustituye por su arte cuando
lo tenga»). Igual las balsas (gris) y el resorte (amarillo). `skins.py` decía
que no se podía sustituir sin forkear el framework; AUD-461 cambió el trato —la
escena ya sobrescribe `dibujar_ui`—, así que ahora la piel se dibuja DESPUÉS
del padre y lo tapa. Losa de piedra con grabado en oro, madera atada para las
balsas, losa de bronce con cuñas para el resorte. Tests
`test_piel_mecanicas_paburu` (4).

**AUD-466 — los cuatro círculos eran la misma pieza cuatro veces.** Y lo eran
de verdad: `muebles_del_circulo` devolvía las mismas seis medidas para los
cuatro. La simetría venía de cuando la pelea ocurría DENTRO del círculo
pisado; desde la catacumba los círculos son recorrido, y un recorrido premia
lo contrario. Ahora cada uno tiene perfil propio (`PERFILES_DE_CIRCULO`):
I cornisas largas y bajas, II pedestales estrechos, III galería corrida con
un apoyo alto descentrado, IV tejados escalonados hacia la salida. Se
conservan las tres reglas que sostienen el nivel (franja del sello libre, los
dos aleros, la banda jugable) — y con ellas la nota: **130/130**. Postmortem:
el primer intento subía también los aleros y el analizador perdió la cadena
hasta la catacumba (2 plataformas huérfanas, 124/130); los aleros se nivelan y
la variedad vive en las cornisas.

**AUD-464 — cuatro avisos de lore eran dos de más.** La caja del motor ocupa
el ancho entero y ~70 px de alto: cuatro en cuatro minutos son cuatro
interrupciones. Quedan dos, de una línea, en los dos sitios donde el jugador
ya está parado mirando algo (la entrada y el altar del llamado). El techo lo
vigila `test_ritual_paburu`.

**Lo que NO se tocó y sigue abierto:** R2-4 (el aviso de lore que se queda en
pantalla al descender), R2-5 (murciélagos sin picado) y R2-9 (los ataques del
jefe: pendiente de re-jugar la Forma 2 ahora que sus ataques se VEN).

## RONDA 2 DEL PLAYTEST — ABIERTA (2026-08-15, PRIORIDAD MÁXIMA)

Reporte de Alejandro jugando el flujo real (pisó el círculo sorteado, SIN
teclas de debug). Captura clave: la intro del jefe en la catacumba con
TODO a plena luz marrón («color caca»), braseros apagados, héroe
invisible, y el juego se congeló y se cerró.

| # | Síntoma | Hipótesis de trabajo |
|---|---|---|
| R2-1 | **La catacumba se ve marrón fullbright, no sombría** | La penumbra (ambient 0.18→rampas de la intro) NO aplica en el camino GL de su máquina (RTX 4060, moderngl activo). En captura headless (camino software) la penumbra SÍ funciona. Revisar `dibujar_mundo`: con `usar_gl` la luz va por `render_map()`/App y quizá la escena-jefe no publica su mapa de luz, o las luces de los braseros no viajan al sombreador. COMPARAR con un stage del profesor en la misma máquina. |
| R2-2 | **El héroe desapareció durante la intro** | Posible mismo camino GL (¿lote de sprites no dibuja al player durante cutscene?) o el encuadre lo deja fuera. Pedir captura post-intro. |
| R2-3 | **Congelamiento + cierre** | SIN TRAZA AÚN. Pedida: `--debug` en consola o `%APPDATA%\legacyofinfest\legacy_of_infest.log` (últimas 30 líneas). No tocar nada hasta tenerla. |
| R2-4 | **El aviso de lore de la superficie seguía en pantalla dentro de la catacumba, tapando la intro** | Bajar el mensaje activo al descender (la escena puede limpiar `_msg_box` en `_descender_a_la_catacumba`). |
| R2-5 | **«Los murciélagos no bajan, se mueven pero no por el mapa»** | Deliberado (sin picado, documentado) pero no satisface. Opción: activar `alert_flight_mode="dive"` con parámetros suaves solo lejos del pozo. |
| R2-6 | **Dirección de color: «todo café, antes se veía mejor»** | Si R2-1 se arregla, la penumbra + braseros ya cambia TODO. Después juzgar de nuevo; si sigue marrón: pasada de color real (sombras frías, menos saturación del ladrillo, quizá `start_hour=night`). |

**Avance (mismo día):**
- **R2-7 RESUELTO** — sprites ×2 hundidos («máscaras bajo tierra», «el del
  agua se sale»): `EnemyBase.draw` ancla los pies con `_sprite_fw/fh`
  GUARDADAS y el escalado no las actualizaba. Arreglado en
  `_agrandar_frames` (+ ahogado: amplitud 22→14, spawn 590→600 — nunca
  rompe la superficie). Verificado en captura.
- **R2-3 sin reproducir**: la corrida con `--debug` fue limpia (GL_RENDERER
  = RTX 4060 ✓); el «cierre» anterior fue Ctrl+C tras el congelón. Si
  vuelve a congelarse: guardar las últimas líneas de
  `%APPDATA%\legacyofinfest\legacy_of_infest.log`.
- **R2-8 NUEVO** — «me volvió a tirar a Paburu»: el sorteo funcionó (pisó
  el círculo elegido) pero SIN anticipación se siente arbitrario.
  Candidato: señal visual en el círculo sorteado (brasas del emblema
  encendidas / partículas) para que se LEA antes de pisarlo.
- **R2-9 NUEVO** — «los ataques del jefe mal diseñados, todo horrible»:
  falta ESPECIFICIDAD — pedir a Alejandro cuáles ataques y qué les falla
  (¿telegraph? ¿lectura? ¿feedback del golpe?) con capturas. No tocar el
  balance a ciegas.

Método: primero R2-1 (la luz en SU máquina: comparar con un stage del
profesor — si los suyos también se ven planos, es el camino GL global);
no rediseñar nada visual hasta que la luz funcione — juzgar el arte sin
su iluminación es juzgar otro juego.

**Estado tras la ronda 6: TODA la lista de la RONDA 2 está cerrada.**
R2-4 (AUD-475), R2-5 (AUD-476) y la legibilidad de R2-9 (AUD-477) fueron las
últimas. Lo único que queda de esta ronda es el BALANCE de los ataques del
jefe, y ése necesita una partida tuya.

**Estado anterior (AUD-461):** R2-1, R2-3 y R2-8 cerrados arriba;
R2-2 explicado. Quedan VIVOS: **R2-4** (bajar el aviso de lore al
descender — un `_msg_box` que limpiar en `_descender_a_la_catacumba`),
**R2-5** (murciélagos sin picado), **R2-6** (dirección de color /
`AMBIENT_BY_PHASE` — juzgar de nuevo AHORA que la intro y los espíritus
se ven; hay captura comparativa) y **R2-9** (esperando la especificidad
de Alejandro — ojo: los ataques invisibles de la ronda eran parte del
«todo horrible»; volver a jugar la F2 con el arreglo antes de tocar
ningún número de balance).

## Aceptado con motivo (NO son tareas)

- HUD «PHASE 4»: muestra el TOTAL de fases; rareza del motor (`hud.py:772`), igual en los demás jefes.
- `sombras_proyectadas` apagado: polígonos negros gigantes por los rects de colisión de 4000 px (postmortem en `tools/gen_paburu_tmx.py`).
- «Plataformas inalcanzables» del analizador en la catacumba: artefactos del análisis, no del nivel.
- Mecánicas del ECS (balsas, bloques rítmicos) con dibujo del motor: skinearlas exige fork del framework (`skins.py` documenta el porqué).
