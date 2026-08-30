# GUION DEL VIDEO — para leer con tu voz mientras grabás

> Este es el guion ÚNICO de grabación. Todo lo que está en
> **"comillas y negrita"** lo LEÉS TAL CUAL con tu voz. Todo lo que
> está en `[corchetes]` es lo que HACÉS con las manos y no se dice.
> Sigue el orden exacto de los 10 puntos que pide la asignación (§9).
> Si te equivocás o te morís sin querer: NO cortés la grabación — la
> asignación pide ver «el funcionamiento real», y los tropiezos narrados
> suman en playtesting. Duración esperada: 12 a 16 minutos.

---

## ANTES DE GRABAR (no se lee)

- `[Cerrá lo que no sea el juego y la terminal. Volumen del juego al 50%.]`
- `[Abrí la carpeta del proyecto en una terminal, listo para escribir.]`
- `[Grabación: HERRAMIENTA DE RECORTES de Windows 11 (la Game Bar NO`
  `sirve aquí: solo graba juegos, y el video empieza en la terminal).`
  `Probá Win + Shift + R; si no, Inicio → «Recortes» → ícono de cámara`
  `de video → Nuevo → seleccioná toda la pantalla → Iniciar. ANTES de`
  `iniciar, activá el ícono del MICRÓFONO y hacé una prueba de 10 s`
  `hablando. Alternativa pro: OBS Studio (gratis).]`
- `[Teclas que vas a usar: flechas mover · Z golpe corto · X golpe largo · C/G agarrarse · 8 llena la barra del ulti · Z+X juntos el ulti · 9 baja directo al jefe · 0 repite la intro · 1-4 fuerzan las formas del jefe.]`
- `[Practicá una pasada en seco ANTES de grabar, con este guion al lado.]`
- `[UNA SOLA VEZ, antes del primer intento: si pytest no está instalado`
  `(sale «No module named pytest»), corré:`
  `.venv\Scripts\python.exe -m pip install pytest  — y ya queda.]`

---

## PUNTO 1 — INICIO DEL PROYECTO

`[Con la terminal en pantalla, grabando, decí:]`

> **"Hola, soy Alejandro Rodríguez. Este es mi proyecto para la
> Evaluación Práctica Dos: el Stage 4-2, El Gran Shamán Paburu, el
> jefe final de Legacy of InFest. Antes de abrir el juego voy a correr
> las pruebas automatizadas del nivel."**

`[Escribí y ejecutá:  .venv\Scripts\python.exe -m pytest tests/ -k paburu -q  y esperá el verde.]`

> **"Doscientas cincuenta pruebas en verde. Son pruebas que yo fui
> escribiendo en cada ronda de playtest: hay un bot que juega el nivel
> completo de punta a punta, auditores que revisan que ninguna
> plataforma se solape con otra y que ninguna decoración quede
> flotando en el aire, y pruebas de cada mecánica. Ahora sí, arranco
> el juego."**

`[Ejecutá:  jugar_paburu.bat  — que se vea arrancar de cero.]`

---

## PUNTO 2 — ACCESO AL NIVEL

`[Apareces bajo el portón de entrada. Quedate quieto un momento.]`

> **"Este es el Cementerio Sagrado de los tilawa, una cultura ficticia
> que inventé para el lore del juego. Entro por este portón de piedra:
> es un arco de medio punto con sus dovelas y su clave talladas, y dos
> farolitos encendidos. Ese fuego no es casualidad: en todo el nivel
> el fuego está racionado a propósito — lo vuelvo a ver hasta el final,
> y eso me va a servir de brújula."**

`[Tocá la tecla 0 para lanzar la intro de Paburu y dejala correr.]`

> **"Esta es la presentación del jefe. Paburu era el shamán juez de
> los tilawa: los muertos se presentaban ante él a rendir su prueba.
> El nivel entero es el camino hacia ese juicio."**

---

## PUNTO 3 — RECORRIDO

`[Caminá hacia la derecha, peleando lo que salga, y andá narrando.
Ruta: entrada → pozo → círculo I → galería rítmica → círculo III →
ascensor → camino final. SIN recoger pavesas todavía — eso es el
punto 4.]`

> **"Recorro el nivel de corrido para que se vea la estructura. La
> regla de diseño que seguí es que ningún tramo repite la mecánica del
> anterior: primero plataformas simples entre las tumbas..."**

`[Al llegar al POZO — metete al agua a propósito:]`

> **"...después el pozo, que tiene dos rutas: puedo nadar y salir por
> estos peldaños del brocal — con solo tocar el salto, sin mantenerlo —
> o cruzarlo por arriba, por las balsas, que es la ruta de riesgo."**

`[Salí del agua, volvé atrás y cruzá esta vez por las balsas de arriba.]`

`[En la GALERÍA RÍTMICA, cruzá al compás de los bloques:]`

> **"Esta galería va al ritmo de la música: los bloques aparecen al
> compás, ciento treinta y seis pulsos por minuto, los mismos del tema
> del nivel."**

`[En el ASCENSOR, subite y quedate quieto mientras sube:]`

> **"El ascensor me sube al nivel alto mientras el sukia de ceniza me
> dispara: quedarme quieto también es una decisión de riesgo."**

`[En el CAMINO FINAL, parate al pie de la última torre, donde el
resorte nuevo:]`

> **"Y aquí está la tirolesa. Para llegar puedo escalar las tres
> repisas... o usar este resorte, que me sube de un brinco."**

`[Saltá sobre el resorte, aterrizá en la repisa. Acercate al cable:
se ve el letrero «G AGARRARSE». Saltá hacia el cable MANTENIENDO G:]`

> **"El juego me dice la tecla: me agarro con G... y cruzo colgado
> sobre el foso. Al final del cable el impulso me suelta, reboto en el
> resorte del otro lado y caigo en el bolsillo. Todo este tramo lo
> arreglé en las últimas rondas de playtest: antes la tirolesa no
> enganchaba y este bolsillo era una trampa sin salida."**

`[INTENTOS DE ROMPER — hacelos aquí, narrando cada uno:]`

> **"Ahora intento romper el nivel, que es parte del playtesting."**

- `[Volvé del bolsillo brincando sobre su resorte:]` > **"¿Puedo quedar atrapado en el bolsillo? No: el resorte me devuelve por encima de la boca."**
- `[Volvé al pozo, tirate y salí por LA OTRA orilla:]` > **"¿Y en el pozo? Salgo por cualquiera de las dos orillas."**
- `[Pegate a pedestales y esquinas caminando contra ellos:]` > **"Busco huecos de colisión pegándome a las piedras... y no atravieso nada."**
- `[Caminá de vuelta hasta el spawn:]` > **"¿Puedo regresar? Sí: toda la superficie es ida y vuelta. La única puerta de un solo sentido es el descenso final, y es una decisión de diseño: presentarse ante el juez no se deshace."**

---

## PUNTO 4 — ELEMENTOS PRINCIPALES: EL RITO

> **"La mecánica principal del nivel es el rito de las Cuatro
> Ofrendas. La boca de la catacumba nace sellada por la Losa del
> Juicio, y para abrirla tengo que encontrar cuatro pavesas de fuego —
> una por tramo — y encender con ellas los cuatro círculos
> ceremoniales."**

`[Andá a la boca (el mausoleo grande del final) y PARATE SOBRE la losa,
tocá G:]`

> **"Si toco la losa me dice cuántos círculos arden: cero de cuatro.
> Vamos por las pavesas."**

`[Recorré las cuatro, en orden, narrando dónde está cada una:]`

1. `[Fondo del pozo:]` > **"La primera está en el fondo del pozo: hay que meterse al agua para encontrarla."**
2. `[Alto del columbario:]` > **"La segunda, en lo alto del columbario — el salto exigente entre los dos pedestales."**
3. `[Galería del círculo III:]` > **"La tercera, en la galería del tercer círculo."**
4. `[El bolsillo tras la tirolesa:]` > **"Y la cuarta está al final de la tirolesa, en el bolsillo: el nivel me obliga a dominar su mecánica más difícil antes del juicio."**

`[Cada vez que recojas una, mostrá las brasas orbitando y el contador:]`

> **"La pavesa me orbita el cuerpo, y aquí abajo del retrato se llevan
> la cuenta los braseritos."**

`[Cada vez que enciendas un círculo:]`

> **"Piso el círculo llevando fuego y se enciende: los cuatro cuencos
> prenden de verdad — son luces reales del motor. La recompensa por
> explorar es poder ver."**

`[De camino, mostrá el circuito secreto del mausoleo:]`

> **"Hay un secreto: esta lápida suena distinto — dos golpes y suelta
> la Llave del Juicio, que abre la puerta sellada del mausoleo, y
> adentro un cofre con una vasija de corazón."**

`[Y una veladora: activala, morite a propósito contra un enemigo:]`

> **"Los checkpoints son veladoras: la enciendo, y si muero...
> renazco en ella, con el mundo rearmado."**

`[Con las 4 ofrendas, andá a la losa: polvo, temblor, se abre:]`

> **"Cuarto círculo encendido... y la Losa del Juicio cede. La boca
> está abierta."**

---

## PUNTO 5 — MODELADO Y CURVAS

`[NO bajes todavía. Este punto se narra mostrando ejemplos concretos.]`

> **"Ahora quiero mostrar cómo apliqué los contenidos de Computación
> Gráfica, empezando por curvas y modelado."**

`[Señalá (parate junto a) un guardián espectral volando:]`

> **"Estos guardianes vuelan siguiendo curvas de Lissajous: un seno en
> equis y otro en ye con frecuencias que no son múltiplos entre sí,
> así la curva nunca se cierra y el vuelo nunca se memoriza."**

> **"Más adelante, en la pelea, se van a ver dos curvas más: las
> piedras que escupe Paburu siguen un tiro parabólico integrado con
> cinemática real, y las ánimas de su sello suben por una spline de
> Catmull-Rom — la elegí en vez de una Bézier porque la Catmull-Rom
> pasa exactamente por sus puntos de control: cada ánima nace en su
> marca y muere en el centro del sello."**

`[Parate frente al portón o al mausoleo:]`

> **"El modelado: el portón y el mausoleo no son tiles repetidos — son
> piezas dibujadas enteras y después rebanadas en tiles. Y mi personaje
> es un muñeco de partes: capa, torso, brazos, piernas y cabeza se
> componen por código para generar las nueve hojas de animación."**

---

## PUNTO 6 — REPRESENTACIÓN DE LA ESCENA

`[Quedate quieto en un claro y después caminá despacio, mirando el fondo:]`

> **"La escena está construida en planos de profundidad: al fondo las
> estrellas y la luna, después las montañas — con su filo de luz de
> luna en las crestas —, las nubes que derivan solas, las siluetas del
> cementerio lejano, el plano de juego, y la niebla baja por delante.
> Cada plano se mueve a su propia velocidad de parallax: al caminar se
> siente la profundidad."**

> **"La jerarquía visual también guía la navegación: el único punto
> cálido al fondo del camino es el faro de brasas sobre la boca — el
> fuego siempre me dice a dónde voy."**

---

## PUNTO 7 — COLOR Y TRANSPARENCIA

`[Buscá un encuadre con veladoras, niebla y algún círculo encendido:]`

> **"La paleta es intencional: una noche fría de azules y piedra,
> donde el fuego es el único acento cálido y está racionado — incluso
> hay una prueba automatizada que impide que el dorado se derrame,
> porque el oro es el idioma del juez."**

> **"La transparencia es alfa real: la niebla del suelo, las nubes,
> los halos de las velas, los velos de las ánimas de las tumbas — que
> van con alfa normal y no aditivo, porque un brillo aditivo no sabe
> dibujar ojos oscuros — y el polvo cuando la losa se abrió."**

---

## PUNTO 8 — TEXTURAS

`[Acercate a una torre de piedra del camino final o del columbario:]`

> **"Las texturas son un tileset propio generado por código: sillería,
> piedra de tumba, escombro. Cada pilar teje variantes distintas —
> piedra lisa, agrietada, con musgo, con humedad — elegidas con ruido
> determinista, para que ninguna torre sea una fotocopia de otra. Y el
> musgo solo crece sobre piedra: nunca en el aire."**

`[Mirá el HUD y dejate pegar una vez:]`

> **"Hasta el retrato del personaje es textura propia: cambia cuando
> estoy herido, crítico o muerto."**

---

## PUNTO 9 — ANIMACIONES

`[En un lugar seguro, mostrá los estados: caminá, saltá, agachate,
tirá golpes con Z y con X:]`

> **"El personaje tiene sus hojas de animación generadas por código:
> caminar con la capa flameando, salto, caída, cuclillas, dos ataques,
> daño y muerte — veintiséis estados del motor cubiertos."**

`[Ahora el ulti. Tocá la tecla 8 — aparece «ULTI LISTO — Z+X»:]`

> **"Y esta es la Forma del Ánima. Con la tecla ocho lleno la barra
> del especial — es mi tecla de demostración, en juego normal se carga
> golpeando — y con Z y X juntos..."**

`[Z+X. Dejá que se vea la transformación completa, caminá y saltá
transformado:]`

> **"...las ánimas me prestan su fuego. La máscara tilawa con los tres
> glifos de los guardianes, el cuerpo ennegrecido con el filo de luz
> verde, levito sobre mi charco de luz, y el fuego sale de todo el
> cuerpo. Dura seis segundos y jamás es dorada: el oro es del juez."**

`[Mostrá también una animación ambiental: una tumba despertando o las
llamas de los cuencos:]`

> **"El ambiente también está vivo: las nueve tumbas habitadas
> despiertan cada una con su propio reloj, las llamas y el humo de los
> cuencos, las estrellas que titilan... el camposanto nunca repite el
> mismo segundo."**

---

## PUNTO 10 — FINAL: EL DESCENSO Y EL JEFE

`[Andá a la boca abierta, caminá sobre ella y dejate caer. El mecate
te agarra solo; bajá con ABAJO, la cámara te sigue:]`

> **"Con el rito completo, desciendo. El mecate del sepulturero me
> agarra solo — abajo no se le pide a un muerto que camine — y la
> cámara baja conmigo hasta la catacumba."**

`[LA PELEA COMPLETA. Narrá poco y jugá; entre forma y forma decí una
frase. Si una forma te cuesta mucho, no pasa nada: morí, renacé
curado en la antecámara y decilo — es evidencia de playtesting.]`

> **"Forma uno: la Cabeza de Piedra. Aquí están el tiro parabólico de
> las piedras y el sello con sus ánimas en Catmull-Rom."**

> **"Forma dos: la Máscara Espectral, con los rostros que ya vi
> colgados en la verja."**

> **"Forma tres: la Reliquia — puede tocar la Pepita o la Perla, es
> aleatoria."**

> **"Forma cuatro: el Espíritu del Shamán. Su ataque parable es el más
> brillante de la sala: el color me dice qué mirar."**

`[Usá el ulti en la pelea cuando la barra se llene sola. Al ganar,
dejá correr el epílogo entero sin tocar nada:]`

> **"El juicio está rendido."**

---

## CIERRE — TU VEREDICTO (60 segundos, mirando la pantalla final)

`[Leé las frases y COMPLETALAS con tu opinión real de esta partida.
Esto es el playtesting que pide la asignación — tu juicio vale más
que el guion:]`

> **"Para cerrar, mi veredicto como playtester de mi propio nivel:"**
> **"No encontré forma de quedar atrapado ni de atravesar zonas: ..."**
> **"La progresión no se puede romper: el rito y la losa aguantaron mis intentos."**
> **"La navegación me pareció... [decilo vos]"**
> **"La dificultad de los saltos de ochenta píxeles me pareció... [decilo vos]"**
> **"La Forma Cuatro del jefe me pareció... [justa / injusta — decilo vos]"**
> **"Lo que encontré para corregir en la próxima iteración es... [si viste algo raro EN ESTA grabación, decilo aquí — va directo al tablero de pendientes]"**
> **"Este fue el Stage 4-2, El Gran Shamán Paburu. Gracias por ver."**

`[Win + Alt + R para cortar. Revisá el video antes de entregarlo: que
se oiga tu voz y se vea todo. Cualquier hallazgo raro → me lo contás
y lo convertimos en la Ronda 21.]`
