# Etapa 7 — Guion de playtesting humano y del video (Stage 4-2)

> Para grabar la evidencia que pide la **Evaluación Práctica II
> actualizada (2026-08-27)**: su §5 (playtesting) y su §9 (video de 10
> puntos). Escrito contra NUESTRO mapa: cada pregunta trae dónde
> intentar romperlo aquí y qué debería pasar (con la ronda que lo dejó
> así). Lo que el video encuentre roto vuelve al tablero de
> `PENDIENTES.md` como ronda nueva — ese circuito ES el §6 (iteración).
> La documentación que acompaña la entrega: `DOCUMENTACION_ENTREGA_II.md`.

**El diseño quedó congelado el 2026-08-26**: D-01·C y D-01·D están
CERRADOS (Ronda 16) — el nivel ahora es el rito completo de las Cuatro
Ofrendas. El video se graba sobre esta versión. Puntos NUEVOS que el
video debe cubrir: recoger las cuatro pavesas (pozo, columbario,
galería III y el bolsillo de la tirolesa), encender los cuatro
círculos, la losa sellada (pisarla, tocarla con G para el aviso, ver
sus marcas de progreso), la apertura con polvo, y el descenso con la
cámara siguiéndote (R16).

---

## Las preguntas del playtesting (§5), en este mapa

*La asignación nueva pregunta: atrapado · atravesar zonas · saltarse
secciones · romper progresión · colisiones · animaciones · texturas ·
navegación · dificultad · completar el nivel. Las 12 de abajo las
cubren todas (la 2 responde «atrapado» y «atravesar»; colisiones,
animaciones y texturas se evidencian en los puntos 5-9 del video).*

**1. ¿Puedo saltarme una sección?**
El caso grave ya murió en diseño: el sorteo viejo cortaba el nivel al
57 % de media (D-01·A lo eliminó — hoy nada te baja antes de tiempo).
Intentos que valen para el video: cruzar el pozo por arriba sin tocar
el agua (válido: es la ruta de riesgo diseñada), correr los cuatro
círculos sin detenerse (válido: ya no atrapan), tomar la tirolesa
directo a la boca. *Esperado: se puede «saltar» contenido opcional,
nunca la boca ni el juicio.*

**2. ¿Puedo quedar atrapado?**
Los cuatro atrapaderos que encontramos ya tienen salida — enseñarlos
en cámara ES la evidencia: (a) caer al agua del pozo y salir POR LAS
DOS orillas tocando el salto, no sosteniéndolo (peldaños del brocal,
R13 — antes el bot moría ahí); (b) cruzar al bolsillo tras el foso y
volver brincando sobre el resorte (R13 — antes era trampa medida);
(c) morir contra Paburu y renacer DENTRO de la sala (AUD-481 — antes
te escupía fuera del mapa); (d) guardar dentro de la catacumba, salir
del juego y cargar (PAB-01 — antes softlock). Extra: colgarse del
mecate y bajarlo entero — a 36 px del suelo suelta solo (R13).

**3. ¿Puedo romper la progresión?**
Intentar: pisar un círculo, dejar que se encienda y volver a pisarlo;
bajar a la catacumba y buscar cómo re-subir (no se puede: decisión de
diseño, el juicio no se abandona — `test_una_vez_sellado`); saltar del
mecate a media caída (caída elegida, aterrizás en el escombro);
morir durante la intro de Paburu (skippeable con CANCEL).

**4. ¿Puedo llegar antes de conseguir una habilidad?**
Este stage no depende de habilidades desbloqueables: todo se cruza con
salto y salto doble de serie (envolvente medida 91/104 px). El dash es
del árbol pero nada lo exige. El ulti se CARGA golpeando — llegar a
Paburu sin barra es posible y válido (se carga en la pelea). *Esperado:
no hay secuencia rompible por orden de habilidades.*

**5. ¿Puedo regresar?**
En superficie, todo el camposanto es ida y vuelta (mostrarlo:
devolverse desde la boca hasta el spawn). La única puerta de un solo
sentido es EL DESCENSO, y es la tesis del nivel: presentarse ante el
juez es una decisión. Documentado en `DISENO_ACCESO_CATACUMBA.md`.

**6. ¿Los checkpoints funcionan?**
Doce veladoras (D-01·F). En cámara: activar una (se enciende), morir
lejos, renacer en ella; morir en la catacumba y renacer en la
antecámara con la pelea rearmada y la barra llena (la cura del juez).

**7. ¿Los enemigos generan el desafío esperado?**
La población se calibró en dos recortes (19→12→8, AUD-470/473) para
que cada tramo pregunte una cosa. El primer video ya rindió aquí:
la Forma 4 «muy alta e inalcanzable» se corrigió en la Ronda 21 (ahora
baja al alcance y persigue). En la re-jugada: confirmar que el duelo
final ya se siente justo.

**8. ¿La navegación es clara?**
Señales puestas a propósito, mostrarlas: el faro de brasas sobre la
boca (única señal cálida al fondo del camino), el letrero «G
AGARRARSE» de la tirolesa, las mecánicas distintas por tramo que hacen
de brújula, los checkpoints como migas de pan.

**9. ¿El pacing funciona?**
La regla del ritmo está escrita (`DISENO_NIVEL_Y_JEFE.md` §2.6):
ningún tramo repite la mecánica del anterior. El video la evidencia
recorriendo de corrido: entrada → pozo (decisión agua/parkour) →
círculo I → galería rítmica → círculo III → ascensor → camino final →
tirolesa → boca. Tu sensación en voz alta vale más que el doc.

**10. ¿Los secretos son legibles?**
El circuito del mausoleo: lápida falsa (2 golpes) → Llave del Juicio →
puerta sellada → cofre con la vasija de corazón; más las dos ofrendas
de monedas (pedestales y ascensor). PROBAR EN SERIO: ¿la lápida falsa
se distingue de una normal sin saberlo de antemano? Si no la
encontrás «a ciegas», hallazgo legítimo → tablero.

**11. ¿Hay zonas aburridas?**
Tu juicio. Candidato a vigilar: los tramos de galería entre círculos
III y IV si vas sin pelear.

**12. ¿Hay zonas excesivamente difíciles?**
Candidatos conocidos: los ocho repechos de superficie a exactamente
80 px (apex medido 91 — llegan pero justos: decir en cámara si
frustran). La catacumba y la Forma 4 ya se corrigieron con lo que
encontraste (Ronda 21) — confirmá que ahora fluyen.

---

## El guion del video (los 10 puntos del §9 nuevo, en orden grabable)

La asignación actualizada cambió la lista: ahora los puntos 5-9 piden
enseñar **los contenidos de Computación Gráfica** en pantalla. La
buena noticia: todo eso ya está en el juego — el guion solo dice DÓNDE
pararse y QUÉ decir (la chuleta con los porqués es
`DOCUMENTACION_ENTREGA_II.md` §2). Una sola toma continua o cortes
mínimos, con narración; que se vean también los tropiezos. Grabar con
OBS o la barra de juegos de Windows (Win+G). Arco sugerido (~12-18 min):

1. **Inicio del proyecto** — terminal en pantalla: `jugar_paburu.bat`
   (o `.venv\Scripts\python.exe main.py --boss boss_paburu`). Que se
   vea arrancar de cero. Bonus §5: correr antes
   `pytest tests/ -k paburu` y que se vean los 256 en verde («si
   existen pruebas automatizadas, deben ejecutarse»).
2. **Acceso al nivel o jefe** — spawn bajo el portón, placa del
   título, la intro de Paburu (tecla 0 si querés re-lanzarla).
3. **Recorrido** — la ruta entera de corrido comentando el ritmo:
   entrada → pozo POR LAS DOS RUTAS (nadar y salir por los peldaños;
   volver y cruzarlo por las balsas) → círculo I → galería rítmica al
   compás → círculo III → ascensor con el sukia → camino final →
   TIROLESA (el resorte nuevo al pie de la última repisa te sube de un
   brinco, R20; mostrar el letrero «G AGARRARSE» y el enganche
   saltando) → resorte del bolsillo → bolsillo. Aquí mismo los **intentos de romper** (§5):
   ambas orillas del pozo tocando salto · saltar del mecate a mitad ·
   re-pisar círculos encendidos · guardar/cargar dentro de la
   catacumba · pegarse a pedestales y aleros buscando huecos.
4. **Elementos principales** — el rito completo: recoger las cuatro
   pavesas (brasas orbitando al portador + braseritos del HUD),
   encender los círculos (las cuatro luces reales), la losa sellada
   (pisarla, G para el aviso, sus marcas de progreso), la apertura con
   polvo. El circuito del mausoleo (lápida falsa → llave → puerta →
   cofre), las ofrendas de monedas, y una veladora: activarla, morir a
   propósito, renacer.
5. **Modelado y/o curvas** — narrar mientras se ve: las **ánimas del
   sello** en la Forma 1 (spline de Catmull-Rom — «pasa por sus puntos
   de control, por eso nace en la marca y muere en el centro»), los
   **guardianes** volando en curvas de Lissajous que nunca se cierran,
   las piedras de `STONE_SPIT` en **tiro parabólico**, y el modelado:
   el héroe como muñeco de partes, el portón con sus dovelas, el
   mausoleo dibujado entero y rebanado en tiles.
6. **Representación de la escena** — quedarse quieto y mover la
   cámara con una caminata: estrellas → luna → LAS MONTAÑAS (R20, se
   ven de verdad, con filo de luna) → nubes a la deriva
   (parallax distinto por capa) → niebla baja. El faro de brasas como
   única señal cálida al fondo. Y el **travelling del descenso**: la
   cámara baja contigo y empalma sin corte con el encuadre de la pelea.
7. **Color y transparencia** — decir la regla («noche fría, el fuego
   racionado como único acento») y enseñar la transparencia real:
   nubes, niebla, halos de pavesas, los velos de las ánimas de las
   tumbas, el polvo de la losa, los jirones verdes del ulti.
8. **Texturas** — un plano cerca de la sillería del portón, el musgo
   que solo crece sobre piedra, las pilas de ofrenda (monedas
   vestidas), la losa de sillería, y el HUD con los retratos del héroe
   (herido/crítico para verlos cambiar).
9. **Animaciones** — los estados del héroe (caminar, saltar,
   cuclillas, ataques, muerte), el ULTI con Z+X: la **Forma del
   Ánima** en cámara (máscara, levitación, jirones, latido de 6 s) —
   si la barra no está llena, la **tecla 8** la llena al instante
   (atajo de demostración, R19: aparece «ULTI LISTO — Z+X»), la
   galería rítmica al compás, las llamas y el humo de los cuencos, las
   nueve tumbas despertando a destiempo.
10. **Finalización / demostración del jefe** — el descenso completo
    por el mecate, el juicio: la pelea entera (4 formas + epílogo) y
    el veredicto. Morir al menos una vez contra Paburu para enseñar el
    renacer curado en la antecámara.

Cerrar el video con 60 segundos de veredicto propio: las preguntas del
§5 respondidas en una frase cada una. El §9 lo dice explícito: «el
funcionamiento real y no únicamente las partes visualmente atractivas»
— los tropiezos se quedan en el corte. Todo hallazgo → `PENDIENTES.md`.

---

## El CRITERIO FINAL de la asignación nueva contra lo que ya existe

| Criterio | Evidencia que ya tenemos | Hueco |
|---|---|---|
| Integración de los conceptos de CG I | Curvas (Catmull-Rom, Lissajous, parábolas), modelado, escena por capas, color racionado, transparencia real, texturas, animación — todo mapeado con archivo y porqué en `DOCUMENTACION_ENTREGA_II.md` §2 | Enseñarlo EN el video (puntos 5-9) |
| Calidad visual | Mausoleo v2, portón v2, veladoras, ánimas, estrellas, nubes, niebla, héroe #50 + Forma del Ánima, retratos del HUD | Pasada de arte gorda anotada es opcional |
| Funcionalidad y corrección técnica | `grade_stage` 130/130 · `grade_boss` 100/100 · bot de punta a punta sin atascos · motor v2 intacto byte a byte | Tu pasada humana (aún no jugás desde R14-R18) |
| Pruebas realizadas | 256 tests propios + arneses que caminan el mapa real + capturas por ronda en `capturas_sesion/` | Que se vean correr en el video (punto 1) |
| Detección y corrección de problemas | 21 rondas playtest→arreglo en `PENDIENTES.md`; `BUGS_DEL_MOTOR.md` (13 bugs, 11 adoptados en el motor v2) | **#46: EL VIDEO — sólo vos podés** · reportar el bug nº 12 |
| Evolución respecto a la primera entrega | El registro entero de rondas ES esa evidencia: qué se probó, qué falló, qué se corrigió, qué mejoró | Mantenerlo al día hasta la entrega |
| Documentación (§8) | `DOCUMENTACION_ENTREGA_II.md` (descripción + CG + testing + defensa de IA) | Leerla antes de defender |

## Pendientes nuestros, estado al 2026-08-27

| # | Qué | Estado |
|---|---|---|
| D-01·C | Pavesas + círculos que se encienden + contador HUD | ✔ Ronda 16 |
| D-01·D | Boca sellada hasta las cuatro ofrendas (Losa del Juicio) | ✔ Ronda 16 |
| §8 | Documentación breve de entrega (`DOCUMENTACION_ENTREGA_II.md`) | ✔ 2026-08-27 |
| §9 | Guion del video re-mapeado a los 10 puntos nuevos | ✔ este doc |
| #46 | Playtest humano + video (este guion) | **pendiente — tuyo** |
| P-02 | Balance Forma 4 (≥24 daño/min) | pendiente — medir tras tu pelea |
| P-01 | Repechos de 80 px y repisas de catacumba a 96 px | decisión de diseño abierta |
| P-03 | Optimizaciones anotadas (caché del aura −88 %, brasas pre-horneadas) | opcional, si el FPS del video lo pide |
| — | Voz de Paburu (tu voz + distorsionador) | idea anotada, opcional |
| #47/#48 | EP2 (Unidad VII) / EP3 (Unidades VIII-IX) | hitos futuros de la rúbrica |
