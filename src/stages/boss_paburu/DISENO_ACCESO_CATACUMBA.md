# D-01 · El acceso a la catacumba — propuesta de rediseño

> **Estado:** **fase A aplicada y verificada** (2026-08-16). B, C y D pendientes.
> **Origen:** playtest de Alejandro — «no se puede disfrutar el nivel porque
> lo manda directamente a Paburu», «la tirolesa no la vi», «esas monedas se
> ven como cuadros».
> Las tres frases describen **un solo problema**.

---

## 1. Lo que está roto, medido

### 1.1 El sorteo se come el nivel

El camposanto mide 4160 px. El sorteo elige uno de cuatro círculos y, al
pisarlo, la tierra se abre y bajás. El disparador del círculo mide **416 px de
ancho y va pegado al suelo**: es imposible cruzarlo a pie sin tocarlo.

| Si sale sorteado | Ves hasta x | % del camposanto |
|---|---|---|
| Círculo I | 1360 | **33 %** |
| Círculo II | 1936 | 47 % |
| Círculo III | 2736 | 66 % |
| Círculo IV | 3536 | 85 % |

**Media: 57 %.** Una de cada cuatro partidas termina el recorrido en el
primer tercio.

### 1.2 El tramo final es contenido muerto

| Pieza | x | ¿Se alcanza? |
|---|---|---|
| Tirolesa_01 | 3840 | **Nunca.** Queda detrás del corte en las cuatro partidas posibles |
| Resorte_01 | 3952 | Nunca |
| Puerta_Final | 4000 | Sólo por la ruta acrobática de one-ways a y=400 |

La tirolesa no se perdió ni se rompió: **está intacta y es inalcanzable**. Es
además la única mecánica del nivel que quita el control al jugador, o sea la
más memorable, y nadie la ha visto nunca.

### 1.3 Los cuencos de fuego florecían con el bloom (resuelto en la fase B)

Tile 26 del tileset: un cuenco de piedra con **tres píxeles de oro**. El tile
es diminuto; el problema estaba en la pasada de **bloom** de la ruta de GPU,
que coge los píxeles más brillantes del fotograma y los derrama. En un nivel
nocturno, tres píxeles de oro sobre piedra oscura SON el punto más brillante,
así que cada cuenco florecía en un disco cálido de ~11 px. Cuatro por círculo
y dos en el pozo: una retícula de monedas.

Y sólo se veía **con tarjeta**. En el camino software esos tres píxeles no se
notan — por eso ninguna captura de arnés lo delató en meses.

Cerrado en la fase B: el cuenco apagado lleva ceniza, no rescoldo. El fuego
llega con la ofrenda (fase C) y lo dibuja la escena, que es donde puede vivir
y apagarse. Guardián: `test_niebla_y_cuencos_paburu` incluye una prueba que
**raciona el oro de todo el tileset** — ningún tile nuevo puede volver a meter
oro sin declararlo y decir por qué.

---

## 2. El diagnóstico de diseño

El sorteo defiende una tesis buena: *«un disparador fijo se aprende en la
segunda partida»*. El problema no es la tesis, es el **precio**: para comprar
sorpresa, el nivel paga con la mitad de su contenido. Y la paga en la moneda
más cara, porque lo que queda del otro lado del corte es lo mejor que tiene —
la cripta, la tirolesa y la catacumba, que es «lo mejor del stage» por
decisión propia.

Hay otro coste más silencioso: **el jugador no eligió bajar**. Paburu se lo
lleva. El momento se lee como un castigo por caminar, no como una llegada.

> El nivel está diciendo «explorá» con la mano izquierda y castigando la
> exploración con la derecha.

---

## 3. La propuesta: LAS CUATRO OFRENDAS

> Paburu no es un cazador: es un **juez**. Un juez no te embosca — **te cita**.
> Y ante el juez tilawa nadie se presenta con las manos vacías: al muerto se
> le acompaña con **fuego**.

### 3.1 La regla, en una frase

**Encendé los cuatro círculos y la boca de la catacumba se abre.**

### 3.2 Cómo funciona

1. **La pavesa.** Cuatro brasas vivas repartidas por el camposanto, una por
   tramo. Cada una está donde vive la mecánica de ese tramo:

   | Ofrenda | Dónde | Qué te obliga a hacer |
   |---|---|---|
   | I | fondo del pozo (x≈600) | nadar y aguantar el aire, con el ahogado |
   | II | alto del columbario (x≈1700) | plataformeo vertical |
   | III | tras la cripta (x≈2600) | bloques rítmicos y el bloque destructible |
   | IV | al final de la tirolesa (x≈4060) | **soltarse en la tirolesa** |

2. **El círculo.** Al pisar un círculo llevando una pavesa, la ofrenda se
   deja sola: sus cuatro cuencos se encienden, el emblema arde y **el tramo se
   ilumina de verdad**. En un nivel tan oscuro, la recompensa por explorar es
   literalmente *poder ver*.

3. **La boca.** Con los cuatro círculos encendidos, al final del camino la
   losa se abre. Y no es un hueco donde te caés: baja **una escala de mecate**
   —la que usan los sepultureros— por la que descendés vos. El motor ya tiene
   la pieza: `Vine`, la misma liana que ya usa el mapa en x=432, probada y
   funcionando.

### 3.3 Qué compra cada cosa

| Problema | Cómo lo paga |
|---|---|
| 57 % del nivel | Recorrés el 100 %, siempre |
| Tirolesa muerta | Es la **última ofrenda**: por fin existe, y en el clímax |
| Monedas feas | Los dieciocho cuencos pasan de decoración muerta a **el objetivo**, y encendidos se ven bien |
| «Me manda directo a Paburu» | Bajás **cuando vos decidís**. Con las cuatro encendidas podés seguir explorando |
| El hueco de la catacumba | Escala de mecate: descenso diegético, no una caída |
| El sorteo aprendido | Se sustituye por otra rejugabilidad: la ruta óptima entre las cuatro ofrendas, que sí premia jugar mejor |

### 3.4 Lo que NO se toca

- La catacumba, el jefe, sus cuatro formas, el ofrecimiento y el epílogo:
  **intactos**.
- Los cuatro círculos siguen donde están, con sus perfiles distintos
  (AUD-466) y sus muebles (AUD-472).
- Cero líneas de `src/engine` y `src/framework`.

---

## 4. Riesgos, y cómo se tapan

| Riesgo | Cura |
|---|---|
| «Me falta una y no sé cuál» | Contador diegético: cuatro brasas en el HUD; los círculos apagados humean y los encendidos arden — se ve de lejos cuál falta |
| Backtracking castigador | Cada ofrenda está **antes** de su círculo, en el mismo tramo. El camposanto es horizontal y sin puertas de un solo sentido: volver siempre se puede |
| Softlock | Ninguna ofrenda depende de un enemigo, un recurso agotable ni un objeto que se pierda al morir. Al reaparecer, las ya entregadas siguen entregadas |
| La nota (130/130) | La cadena de checkpoints y el análisis de saltos no cambian: no se mueve una sola plataforma. Guardián `test_nota_paburu` en cada paso |
| Alcance | Se puede entregar por fases (§5) y cada fase deja el nivel jugable |

---

## 5. Plan por fases

| Fase | Qué | Deja el nivel |
|---|---|---|
| **A ✔** | Quitar el sorteo. El descenso pasa a la Puerta_Final (x=4000). Mecate de 736 px por el foso; el disparador se mudó al fondo; `descender()` deja de teleportar a quien ya está dentro; la señal de brasas se reapunta a la boca. **De regalo: las lianas del motor no las dibujaba nadie** — ahora tienen cuerda | Jugable y completo: se recorre el 100 % · 130/130 · 100/100 · 186 tests |
| **B ✔** | Rediseñar el tile del cuenco: apagado con ceniza (piedra, no oro) / encendido con llama y luz | El camposanto deja de parecer sembrado de monedas |
| **C ✔** | Las cuatro pavesas + encender los círculos + el contador en el HUD (Ronda 16: pavesas en pozo/columbario/galería III/**bolsillo de la tirolesa**; cuatro luces reales por círculo; los apagados humean; braseritos bajo el retrato y las pavesas orbitando al portador; `una_vez` de los disparadores a falso con dedupe en escena) | La mecánica completa |
| **D ✔** | La boca sellada hasta las cuatro ofrendas + los avisos (Ronda 16: la LOSA DEL JUICIO — `Cerradura` del motor a ras de piso, marcas de progreso en la propia losa, aviso «ARDEN N DE 4», cede con polvo y sacudida; reentrante ante la muerte) | El bucle cerrado |

**D-01 COMPLETO (2026-08-26).** Tests: `test_ofrendas_paburu` (10) +
`test_acceso_catacumba_paburu` (7). La única diferencia con el §3.2
original: la pavesa II vive SOBRE la cornisa alta del columbario y no
flotando en el vano (el vano mide 128 px —incruzable— y el agarre al
vuelo pasaba a ~20 px del radio: premio roto, medido).

**La fase A sola ya arregla las tres quejas del playtest.** B, C y D convierten
el arreglo en diseño.

---

## 6. Alternativas consideradas y descartadas

- **Sortear sólo entre el círculo IV y la puerta.** Sube el recorrido mínimo
  al 85 % y cuesta media hora. Pero deja la tirolesa en la mitad de las
  partidas y no arregla que el jugador no elija bajar. Es un parche, no un
  diseño.
- **Círculos como recompensa suelta** (curación, reliquia). Barato, pero no
  da razón para llegar al final: el jugador coge lo que le queda de camino y
  sigue.
- **Sortear la ofrenda, no el círculo.** Mantiene la aleatoriedad, pero hace
  irrepetible la ruta óptima: se pierde lo único que el sorteo compraba bien.

---

*Última actualización: 2026-08-16. Ver también `DISENO_NIVEL_Y_JEFE.md` §2
(diseño de nivel) y `PENDIENTES.md` (tablero D-01).*
