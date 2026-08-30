# Evaluación Práctica II — Vertical Slice

**Stage 3-1 "La Entrada de Piedra"** · Zona 3, Heredia · Avril Madrigal
Proyecto *Legacy of InFest* · Computación Gráfica I

---

## 1. Descripción

**Nombre del nivel.** Stage 3-1, "La Entrada de Piedra" (`stage_id = "3-1"`).

**Objetivo.** Recorrer el camino de entrada al campus INVENIO Heredia desde
la puerta exterior hasta el acceso al patio interno, sobreviviendo a la fauna
infestada que ocupó los jardines. El nivel termina al alcanzar el
`NextTrigger` situado en x = 1536.

**Concepto.** Es el primer nivel de la Zona 3 y su trabajo dramático es
presentar el campus: se juega al atardecer, con el edificio principal
todavía reconocible al fondo y las luces encendidas, mientras la vegetación
y la niebla empiezan a comérselo. La referencia visual no es un castillo
genérico sino la entrada real de la sede: fachada de dos pisos gris grafito
con un bloque terracota, planta baja de vidrio, pasillo techado de columnas
a la derecha, césped con camino de adoquín y jardineras bordeándolo.

**Mecánica principal.** Avance horizontal con lectura de amenaza a tres
alturas distintas: enemigos que caminan por el suelo (`WalkerGarza`), que
vuelan en trayectoria senoidal (`FlyingHalcon`) y que disparan desde lo alto
de los arcos sin moverse (`ShooterQuetzal`). Las jardineras funcionan como
plataformas de un solo sentido y por tanto como cobertura contra los
tiradores: la decisión de gameplay del nivel es cuándo subirse a cubierto y
cuándo seguir avanzando.

**Inicio y final.** `PlayerSpawn` en x = 32, sobre el camino de adoquín, con
la fachada de INVENIO a la espalda. `NextTrigger` en x = 1536, al final del
camino. Cuatro checkpoints intermedios (x = 336, 736, 1072 y 1408) reparten
el recorrido en tramos de menos de 400 px. El mapa mide 100 × 38 baldosas,
es decir 1600 × 608 px.

**Progresión y dificultad.** La densidad de amenaza crece de izquierda a
derecha: el primer tercio solo tiene un caminante, el segundo introduce el
tirador de los arcos, y el último combina los tres tipos. El único salto
exigente —el pozo de 40 px en x = 872–912— está deliberadamente en el
segundo tercio, ya con un checkpoint cerca, para que fallarlo cueste poco.

---

## 2. Computación Gráfica aplicada

### 2.1 Curvas y modelado

Se usan **dos familias de curvas distintas**, y cada una tiene una función
dentro del juego.

**Bézier cuadrática — guía de salto.** Al acercarse al pozo, el nivel dibuja
punteado el arco del salto que hay que hacer. Los puntos de control no son
estéticos: se derivan de la física real del motor. Con
`PLAYER_JUMP_FORCE = -380` y `GRAVITY = 800`, la altura de ápice es

    h = v² / (2g) = 380² / (2 · 800) = 90,25 px

y una Bézier cuadrática cuyo punto de control intermedio está a media
distancia horizontal y a `2h` de altura reproduce exactamente esa parábola
—una parábola *es* una Bézier cuadrática, no una aproximación de ella—.
Implementado en `_update_jump_guide()` con `CurveTools.bezier()`.

Decisiones de dibujado, en `_draw_jump_guide()`: la guía va punteada porque
una línea continua flotando se lee como plataforma sólida, y se desvanece
hacia los extremos para que la atención vaya al centro del arco, que es la
información útil. Solo aparece con el jugador a menos de 110 px del borde:
una guía permanente sería ruido, una que aparece cuando hace falta es
señalización.

**Catmull-Rom — farol sobre el pozo.** Un farol de piedra oscila sobre el
hueco siguiendo una spline Catmull-Rom que pasa por cuatro puntos de control
(`CurveTools.build_bezier_path`), con avance triangular de ida y vuelta en
lugar de reinicio brusco. Su función es de composición: es el elemento
luminoso que hace que el hueco se vea antes de llegar a él.

**Modelado.** Toda la geometría del escenario se genera por script
(`gen_tileset5.py`, `gen_tmx5.py`), nunca a mano en el editor. Las
plataformas y jardineras visuales se posicionan calculando fila y columna
desde sus rectángulos de colisión reales (`x // 16`, `y // 16`), de modo que
lo que se ve y lo que colisiona no pueden divergir. La escala es uniforme:
todo el nivel está construido en baldosas de 16 × 16 px sobre una retícula
de 100 × 20 (1600 × 320 px), de las cuales las seis filas inferiores son
subsuelo.

### 2.2 Representación de escenas

**Profundidad.** Cinco planos de lejano a cercano: el parallax real del
motor (montañas de `assets/backgrounds/zone3/`, con factores de velocidad
0,15 / 0,35 / 0,60), luego `BG_Far` con las nubes, `BG_Mid` con la fachada de
INVENIO y la pérgola, `BG_Near` con árboles, farolas y jardineras, `Terrain`
con el camino, y por último `FG_Overlay` con vegetación que cruza por
delante del jugador.

**Composición.** La fachada ocupa el tercio izquierdo (donde arranca el
jugador, para establecer el lugar), la pérgola con los arcos marca los dos
puntos donde están los tiradores, y el pozo rompe la horizontal justo en el
segundo tercio. La línea del suelo es constante salvo en el pozo, que es
precisamente por lo que el pozo se lee.

**Jerarquía visual.** Lo que puede matarte es lo más contrastado: los
enemigos y la línea roja de telegrafía de los `ShooterQuetzal` son lo único
saturado de la paleta. El fondo se desatura y se aclara con la distancia
(perspectiva aérea), y las bandas de niebla y calima refuerzan la separación
entre planos.

**Navegación.** Camino continuo de izquierda a derecha, sin bifurcaciones ni
callejones. El único punto donde la ruta podría no ser obvia —el pozo— tiene
la guía de salto y el farol.

### 2.3 Color y transparencia

**Paleta.** Rampas de cinco tonos por material (piedra, grafito, terracota,
césped, follaje, tronco, vidrio, metal), más rampas propias para flores
(violeta/rosa) y nubes. No hay ningún color plano en el nivel: cada
superficie usa al menos tres tonos de su rampa. El registro general es de
atardecer oscuro —violetas y magentas fríos— con los acentos cálidos
reservados para las fuentes de luz: farolas, ventanas iluminadas, calima del
horizonte.

**Contraste dirigido.** Los cálidos aparecen solo donde hay luz, de modo que
el ojo va automáticamente a las farolas y ventanas, que son los puntos de
referencia del recorrido.

**Transparencia.** Se usa en cuatro sitios y en todos con intención:

- Bandas de niebla entre planos, con alpha creciente de 0 arriba a 80 abajo,
  que es lo que hace que el plano medio parezca estar detrás.
- Calima cálida del horizonte: alpha en campana senoidal de pico 28 que cae a
  cero en los dos bordes de la banda, para perspectiva aérea sin cantos duros.
- Sombra de nube en tiempo real (`_draw_cloud_shadow`), una capa `SRCALPHA`
  cuyo alpha va de 6 a 61 según la distancia entre la nube y el jugador, y
  cuyo color se interpola en HSL con `ColorTools.hsl_to_rgb` entre un tono
  de sol (H 45°, L 0,80) y uno de sombra (H 215°, L 0,40).
- Guía de salto, con alpha variable por punto.

También están activas las propiedades de mapa `ambient_light = 0.55`,
`bloom = 0.30` y `vignette = 0.35`, que el motor aplica sobre la escena
compuesta.

### 2.4 Texturas

**Aplicación.** Todo el tileset (`tileset_invenio_gothic_v5.png`, 80
sprites, 8 × 17 baldosas) se genera por código desde las rampas de paleta, con cuatro
técnicas: dithering ordenado de Bayer 2×2 únicamente en las fronteras entre
tonos —nunca sobre el relleno, porque ruido por píxel no es sombreado—;
oclusión ambiental de 1–2 px en la base de cada baldosa de terreno; luz
direccional coherente desde la derecha (el horizonte del atardecer) en todos
los sprites; y variantes deterministas por hash de `(x, y)`, seis de
adoquín, seis de césped, cuatro de muro de piedra, cuatro de grafito, tres
de terracota y cuatro de subsuelo, de forma que no hay ninguna baldosa repetida idénticamente
dentro de un área de 4 × 4.

**Escala y resolución.** Uniforme, 16 × 16 px, sin ninguna textura reescalada
ni estirada. Los sprites grandes (árboles 2 × 3, nubes 6 × 3 y 5 × 2) se
construyen como bloques de baldosas del mismo módulo.

**Correspondencia textura–objeto.** Cada material tiene su propia
construcción, no un mismo ruido tintado: el terreno son bloques irregulares
con junta de mortero de 1 px, esquinas descascaradas y musgo esporádico en
la junta horizontal; el césped son estratos de tierra con piedritas y
briznas de 3–6 px de altura variable, de modo que el borde césped/aire no es
una línea recta; el vidrio de las ventanas góticas lleva marco de piedra
propio.

### 2.5 Animación

Cinco elementos animados, todos declarados como animaciones de baldosa en el
propio TMX (`<tile id="N"><animation><frame .../></animation></tile>`).
**No se modificó el motor:** se verificó que `pyscroll` ya sustituye
baldosas animadas en caliente (`pyscroll/orthographic.py:414`,
`pyscroll/data.py:150`), así que los fotogramas son baldosas normales del
mismo atlas y la animación vive declarada en el mapa.

| Elemento | Fotogramas | Duración | Razón del ritmo elegido |
|---|---|---|---|
| Llama de farola | 4 | 150 ms | Ciclo corto y nervioso: es fuego |
| Ventana iluminada | 4 | 220 ms | Vela temblando; amplitud baja a propósito |
| Hiedra | 4 | 320/340 ms | Ciclo lento, vegetal |
| Flores | 4 | 300/360 ms | Desfasadas respecto a la hiedra |
| Niebla | 4 | 500 ms | Muy lento; es ambiente, no evento |

**Coherencia con la acción.** La hiedra se ancla arriba porque cuelga del
muro y la punta es la que se dobla; las flores se anclan abajo porque nacen
del suelo. El desplazamiento es proporcional a la distancia al ancla, que es
lo que hace que se lea como flexión y no como traslación.

**Sincronización.** Los ciclos tienen duraciones distintas y primas entre sí
a propósito, para que el conjunto nunca lata al unísono. La ventana usa
modulación de brillo, no de forma: la carpintería de piedra no se mueve.

**Integración con el gameplay.** Las farolas animadas son los hitos de
orientación del recorrido; el farol de curva sobre el pozo señala el único
salto exigente. Además hay dos animaciones de código: la nube que cruza el
mapa proyectando sombra, y la línea de telegrafía de los `ShooterQuetzal`,
que se recalcula cada frame con `vec2_distance` y `vec2_normalize` y avisa
una sola vez, en el flanco de subida, cuando el jugador entra en rango.

### 2.6 Animación por easing e interacción propia (Unidad VI)

**Las losas del camino.** Cinco losas de piedra marcadas en el suelo, entre
el pozo y el ascenso final, en x = 944, 992, 1040, 1088 y 1136. Se encienden
**al pisarlas y en orden**. Pisar una fuera de turno no hace nada: no
castiga y no reinicia. Castigar un error de lectura en la primera mecánica
que el jugador ve sería enseñarle a no tocar nada.

**Easing, no interpolación lineal.** Cada losa tiene su propio reloj de
encendido y dos curvas distintas, tomadas de
`src/engine/utils/math_utils.py`:

| Qué | Curva | Por qué esa |
|---|---|---|
| Subida de la luz de la losa | `ease_out_cubic` | Arranca rápido y frena: la piedra "acusa" el paso de inmediato y luego se asienta |
| Rebote del halo que marca la siguiente | `ease_out_elastic` | Sobrepasa y vuelve; es lo que hace que el halo se lea como una llamada de atención y no como un adorno |

Una rampa lineal en el mismo sitio se lee como un fundido de vídeo. El
easing es lo que le da peso al encendido.

**Interacción propia sobre el EventBus.** Al encenderse la quinta, el
escenario **emite un evento suyo**, no uno del motor:

```python
EVENTO_LOSAS: str = "STAGE31_LOSAS_COMPLETAS"
```

El propio escenario está suscrito a ese nombre, y el suscriptor es el que
lanza el mensaje en pantalla ("Las 5 losas responden. El camino reconoce el
paso.") y sube el brillo del tramo. El ida y vuelta completo —emitir,
recibir, responder— es de este nivel: el bus acepta cualquier nombre y no
hizo falta tocar `src/engine/`.

La captura `03_losas_completas.png` es la prueba de ese ida y vuelta: el
mensaje en pantalla sólo puede estar ahí si el evento se emitió y su
suscriptor respondió.

**Evidencia:** `evidencia/capturas/01_losas_apagadas.png` (antes),
`02_losas_a_medias.png` (durante, con el easing a media curva) y
`03_losas_completas.png` (después, con el mensaje del evento).

---

### 2.7 Procesamiento de imagen (Unidad VII)

Tres operaciones, todas sobre la pantalla ya compuesta y todas con su
propio reloj para no pagarlas cada fotograma. Van en `draw()` y no en
`update()` por una razón concreta: leen píxeles, y en `update()` todavía
no hay nada dibujado que medir.

**1. Histograma que dirige lógica.** Cada cierto intervalo se recorta la
ventana de pantalla alrededor del jugador y se calcula su histograma con
`FilterTools.compute_histogram`. De ahí sale la luminancia media —la media
ponderada `sum(nivel × cuenta) / total`— y de ella un único número,
`_refuerzo_luz`, entre 0 y 1.

El histograma no se dibuja: **decide**. `_refuerzo_luz` sube el brillo de
las losas y del halo. Por qué medir y no consultar un reloj: el nivel
arranca de noche y además tiene la sombra de una nube cruzando el mapa. La
luz que hay en pantalla en un instante dado no la sabe ningún temporizador
— hay que medirla. Con el histograma, entrar en la sombra de la nube
enciende las losas igual que lo hace la noche cerrada, sin haber escrito
una sola línea sobre nubes.

**2. Brillo y convolución gaussiana.** El halo que marca la losa siguiente
se construye subiendo el brillo con `adjust_brightness(factor)`, con
`factor = 1 + 1.4 × _refuerzo_luz`, y difuminando después con
`gaussian_blur(sigma = 1.6)`. El desenfoque es una convolución; con σ = 1.6
el núcleo separable de radio 2 es

```
1D:  0.1286  0.2310  0.2808  0.2310  0.1286

2D (el producto exterior, ya normalizado):

    0.0165  0.0297  0.0361  0.0297  0.0165
    0.0297  0.0534  0.0649  0.0534  0.0297
    0.0361  0.0649  0.0789  0.0649  0.0361
    0.0297  0.0534  0.0649  0.0534  0.0297
    0.0165  0.0297  0.0361  0.0297  0.0165
```

Sin el desenfoque el halo tiene borde duro y se lee como un rectángulo
pegado encima, no como luz. El halo se regenera **sólo cuando
`_refuerzo_luz` cambia de tramo**, no cada fotograma: es una convolución,
y pagarla 60 veces por segundo para un resultado que casi nunca cambia
sería tirar tiempo de CPU.

**3. Detección de bordes por Sobel.** Cuando un `ShooterQuetzal` tiene al
jugador en su línea de tiro, se recorta esa misma ventana, se le pasa
`FilterTools.sobel_edge`, se realza con `adjust_contrast(1.8)` y el
resultado se tiñe de rojo y se dibuja encima. Lo que se ve es el contorno
del jugador y de lo que le rodea, marcado: es lo que el quetzal "ve".

Sobel y no Canny a propósito. Canny binariza y devuelve un contorno de un
píxel, limpio pero frío. Sobel conserva la magnitud del gradiente, así que
los bordes fuertes salen más brillantes que los débiles y el resultado
tiene la textura de un visor, que es lo que se quiere comunicar.

El realce de contraste no es cosmético: sobre una escena nocturna la
magnitud del gradiente sale muy por debajo del rango útil, y sin el
`adjust_contrast` previo el contorno no llega a verse. En la captura
`04_sobel_quetzal.png` se ve el aviso de rango y el contorno sobre la
jugadora; en una escena tan oscura el realce sigue siendo justo, y es el
primer punto que subiría si tuviera otra iteración.

---

### 2.8 Identidad de la jugadora por intercambio de paleta

El sprite del jugador son seis colores: cinco azules de capucha y tela más
un dorado para los ojos. Con una paleta tan corta, un **intercambio
explícito color por color** da un control exacto que una rotación de tono
en HSL no daría: sobre seis colores, rotar el matiz arrastra también los
grises azulados del contorno y ensucia la silueta.

Lo que **no** cambia, y es deliberado: la silueta, la escala, el número de
fotogramas, la animación y el rectángulo de colisión. Sólo cambia el color.
Un cambio de identidad que toque la silueta rompe la legibilidad a
distancia, que es lo primero que tiene que funcionar. Los ojos se quedan
dorados: son el único cálido del personaje y lo que impide que el rosa se
confunda con las flores del escenario.

El recoloreado se hace sobre las superficies ya cargadas en memoria, **no**
sobre los PNG del disco: `assets/` es del profesor y no se toca. Ver
`evidencia/capturas/11_jugadora.png`.

---

## 2.9 Evidencia

| Captura | Qué demuestra |
|---|---|
| `01_losas_apagadas.png` | Unidad VI, estado inicial: las cinco losas sin encender |
| `02_losas_a_medias.png` | Unidad VI, el encendido a media curva de easing |
| `03_losas_completas.png` | Unidad VI, el mensaje del evento propio del EventBus |
| `04_sobel_quetzal.png` | Unidad VII, Sobel sobre la ventana del jugador |
| `09_gran_arco.png` | Representación de escenas: el arco apuntado y el hito final |
| `10_verticalidad.png` | Diseño de nivel: varios niveles de suelo en pantalla |
| `11_jugadora.png` | Intercambio de paleta |
| `12_enemigos.png` | Legibilidad con varios enemigos en pantalla |

El vídeo `evidencia/recorrido_stage3_1.mp4` es el recorrido completo, de una
sola toma, de principio a fin (46 s). Las capturas están extraídas de ese
mismo vídeo, sin retoque, sin recorte y sin reescalado: son fotogramas tal
cual, con el HUD incluido.

**Lo que el vídeo no muestra, dicho de frente.** En esa toma no aparecen ni
el relámpago de la tormenta ni la guía de salto punteada sobre el pozo. La
guía tenía una causa concreta y está corregida (ver 3.1). El relámpago no
la tiene identificada: el código está y la fase de tormenta debería haberlo
disparado en el último tercio, pero no se ve un solo destello en los 1337
fotogramas de la grabación. Se declara aquí en vez de dejarlo implícito.

---

---

## 3. Testing

### 3.1 Problemas encontrados y corregidos

**El nivel estaba a oscuras y nadie lo notaba mirando el código.** La
primera grabación de recorrido tenía una luminancia mediana de 14 sobre
255. Todo el arte estaba ahí —los muros, las farolas, los bosquecillos— y
no se veía nada. *Diagnóstico:* se midió sobre los fotogramas del vídeo,
no a ojo. *Corrección:* `ambient_light` a 0.95, `bloom` a 0.40, `vignette`
a 0.15 y el doble de farolas en el recorrido (de siete a catorce).
*Resultado:* mediana de 17 y la escena legible de punta a punta. La lección
es que un nivel se puede calificar 130/130 y aun así ser injugable, porque
la rúbrica mide estructura y la oscuridad es una propiedad de la pantalla.

**La guía de salto se dibujaba fuera de la pantalla.** `PIT_LEFT_EDGE`,
`PIT_RIGHT_EDGE` y `PIT_TOP` valían 884, 924 y 208: números heredados del
mapa antiguo, de 224 px de alto. Con el mapa actual de 608 px, el `DeathPit`
está en x = 872 con 40 px de ancho y la superficie de las dos columnas que
lo flanquean está en y = 592. La Bézier se estaba trazando 384 px por
encima del suelo, o sea en el cielo. *Cómo se encontró:* buscando la curva
punteada en el vídeo de recorrido y no encontrándola en ningún fotograma.
*Corrección:* los tres valores salen ahora del TMX y no de la memoria.
*Lección:* un efecto que no falla y tampoco se ve no da ningún error — sólo
se descubre mirando la pantalla.

**Nubes que se leían como manchas de piel.** El primer tileset mapeaba el
tono de la nube según el alpha de la máscara, y el alpha no correlaciona con
la altura real del volumen, así que casi toda la nube tomaba el tono más
claro y cálido de la rampa. *Corrección:* se recalculó el tono por posición
Y real dentro del bounding-box del contenido y se cambió a una rampa fría
propia para nubes. *Resultado:* las nubes leen como nubes, con banda oscura
abajo y clara arriba.

**Dithering usado como ruido.** El segundo intento de las nubes aplicaba
dithering periódico cada 3 columnas, lo que cubría toda la nube de puntitos
—ruido, no sombreado—. *Corrección:* banda de tono por score continuo (luz +
altura), con dithering limitado a la franja donde el score cruza el límite
entre dos bandas (~30 % del paso), base inferior plana y oscura sin
dithering, y rim light solo en el borde iluminado. Lo mismo se aplicó al
terreno, que pasó de ruido por píxel a bloques con junta de mortero.

**Preview con fondo negro.** El primer render sin ventana salió con fondo
negro sólido, porque el parallax real lo dibuja `StageScene` y no `pyscroll`
por sí solo. *Corrección:* se arregló el script de preview —no el TMX— para
componer a mano las tres capas de fondo a los factores oficiales del motor
antes de dibujar el mapa, y poder así criticar el resultado con honestidad.

**Nivel sin ningún salto exigente.** Al leer la rúbrica del calificador se
descubrió que penaliza explícitamente el nivel que "se recorre solo". El
suelo era una plancha sólida continua de 1600 px. *Corrección:* pozo de
40 px en x = 884–924. El ancho no es arbitrario: el alcance horizontal
natural del salto es `90 px/s · 0,5 · 0,95 s = 42,75 px` (el controlador
aplica media velocidad en el aire), y el clasificador del motor considera
"exigente" un hueco de entre 34 y 85 px. 40 px cae en esa franja y sigue
siendo cruzable sin técnica de experto.

**Checkpoints demasiado separados.** Había un solo checkpoint, a 785 px del
siguiente punto de referencia, por encima del máximo recomendado de 500 px.
*Corrección:* tres checkpoints en x = 416, 784 y 1168, dejando el peor tramo
en 384 px.

**Nivel sin coleccionables.** *Corrección:* cinco `Pickup` repartidos por el
recorrido, uno de ellos al otro lado del pozo como recompensa del salto.

**Franja muerta bajo el suelo.** Al jugarlo por primera vez se vio que la
ventana del juego es más alta que el mapa: bajo el camino quedaba una banda
negra vacía de unos 200 px. *Corrección:* el mapa pasó de 14 a 20 filas,
añadiendo las seis nuevas **por debajo**, de modo que ningún índice de fila
existente cambia y por tanto ningún objeto ni rectángulo de colisión se
mueve. Las filas nuevas son subsuelo de roca, oscurecido por profundidad
(factor 0,52 hasta la fila 16 y 0,34 de ahí abajo) para que quede al fondo
de la jerarquía visual en vez de convertirse en lo más contrastado de la
pantalla. Efecto secundario buscado: el pozo pasó de ser un bache a leerse
como un tiro vertical.

**Edificio flotando.** La fachada terminaba en un canto recto suspendido
sobre el césped — se leía como cartel, no como arquitectura. *Corrección:*
se prolongó hasta el suelo con tres filas de muro en sombra (factor 0,62) y
una fila de zócalo, y la puerta bajó al nivel del camino.

**Bandas de niebla y calima como franjas duras.** En la captura del juego
real las dos bandas cruzaban la pantalla de lado a lado con bordes netos y
parecían un fallo de dibujado. *Corrección:* la calima pasó de alpha
uniforme 55 a una campana senoidal de pico 28, que cae a cero en ambos
extremos; la niebla bajó de alpha 130 a 80.

**Tinte de nube lavando la escena.** El overlay de la sombra de nube iba de
alpha 10 a 130 y teñía de magenta la pantalla entera, comiéndose el
contraste entre el jugador y el fondo. *Corrección:* 6 a 61. La sombra de
una nube oscurece; no tiñe la imagen completa.

### 3.2 Pruebas realizadas

- `python scripts/validate_tmx.py assets/maps/` → `[OK]` para el escenario.
- `python scripts/grade_stage.py assets/maps/stage3_1_la_entrada_de_piedra`
  → **130/130 (100,0 %)**, las quince categorías en `[PASS]`. Se destacan
  `design_pacing: 8/8 — checkpoints bien repartidos, 1 salto(s) exigente(s)`
  y `design_geometry: 10/10 — sin saltos imposibles ni zonas aisladas`,
  que son las dos que miden diseño y no estructura. Entrega I: 100/130.
- `tools/validate_stage.py` → `ALL CHECKS PASSED`, 0 errores, 0 warnings,
  después de cada cambio.
- Renders sin ventana con `pytmx` + `pyscroll` en seis posiciones de cámara,
  más un render ampliado del pozo, revisados uno por uno.
- Verificación de que el XML parsea y de que `Objects` y `Collision` se
  preservan verbatim entre reconstrucciones del TMX.
- Playtest manual: *(completar tras jugar — ver checklist de la sección 5 de
  la consigna)*.

### 3.3 Resultado

El calificador automático del curso da **130/130 (100 %)** frente a los
100/130 de la Entrega I. Las cinco correcciones que aportan la diferencia
—cuatro checkpoints en lugar de uno, cinco coleccionables donde no había
ninguno, el pozo que introduce el único salto exigente, y las propiedades
`author` y `climate`— salieron de leer la rúbrica del propio calificador,
no de suponer qué pedía.

La ronda 7 de la tabla de iteración es la más importante de todas y conviene
decir por qué: **son los defectos que solo aparecieron al jugar el nivel de
verdad**. Ninguno de los cuatro lo detectó el validador, ni el calificador,
ni los renders sin ventana. El nivel puntuaba 130/130 con la franja negra,
el edificio flotando y el tinte magenta puestos.

---

## 4. Iteración respecto a la Entrega I

| # | Versión | Problema detectado | Corrección | Mejora |
|---|---|---|---|---|
| 1 | Entrega I | Escenario plano: suelo de un solo tile, cielo estampado, nubes diminutas, sin sombras ni parallax | Tileset regenerado con rampas, dithering, AO y variantes; parallax real del motor vía `background_zone` | Profundidad legible |
| 2 | Iteración 1 | Nubes color piel; sin separación entre planos | Rampa fría propia; niebla entre planos y calima de horizonte | Perspectiva aérea |
| 3 | Iteración 2 | Dithering usado como ruido sobre el relleno | Dithering solo en fronteras; terreno con junta de mortero | Textura, no grano |
| 4 | Entrega II | Nivel sin salto exigente, sin coleccionables, un solo checkpoint | Pozo de 40 px, cinco `Pickup`, cuatro checkpoints | Ritmo y progresión |
| 5 | Entrega II | Sin ninguna animación propia | Cinco animaciones de baldosa declaradas en el TMX | Escena viva |
| 6 | Entrega II | La curva Catmull-Rom era decorativa | Reubicada sobre el pozo; añadida Bézier de guía de salto derivada de la física del motor | Curvas con finalidad |
| 7 | Entrega II | Al jugarlo: franja muerta bajo el suelo, edificio flotando, bandas duras, tinte magenta | Mapa a 20 filas con subsuelo, fachada apoyada, calima con caída senoidal, overlay de nube a un tercio | Escena legible |
| 8 | Entrega II | Nivel plano: repisas flotantes sobre un suelo de una sola altura | `ruta.py` reescrito como **perfil de alturas** con tramos tipados (camino, muro, escalones, descenso, pozo). Colisión, terreno y validación de saltos salen todos de la misma fuente | Verticalidad real, imposible de desincronizar |
| 9 | Entrega II | Mapa de 224 px de alto: no cabía nada encima del suelo | Mapa a 100 × 38 (1600 × 608), tras verificar que el stage de referencia del profesor es exactamente 100 × 38 | Sitio para arquitectura y cielo |
| 10 | Entrega II | Al grabarlo: el nivel se veía negro (luminancia mediana 14/255) | `ambient_light` 0.95, `bloom` 0.40, `vignette` 0.15 y catorce farolas | Mediana 17 y escena legible |
| 11 | Entrega II | Al grabarlo: la guía de salto no aparecía nunca | Constantes del pozo corregidas contra el TMX (872 / 912 / 592) | La Bézier se dibuja donde está el hueco |

---

## 5. Uso de Inteligencia Artificial

Se usó IA como herramienta de apoyo para auditar el motor (localizar los
hooks de parallax, animación y física antes de tocar nada), generar los
scripts de pixel-art procedural, y revisar la rúbrica del calificador
automático. Las decisiones de diseño —qué se construye, dónde va el pozo,
qué se anima y por qué, qué se descarta por falta de tiempo— son propias y
están justificadas una por una en este documento y en `PROGRESS.md`.

---

## 6. Alcance no cubierto (declarado a propósito)

Para que quede escrito y no parezca omisión.

**No implementado:** el ciclo día → noche → amanecer dirigido por la
posición de la cámara. Estaba en el brief original como fase futura y se
descartó por tiempo.

**Implementado pero no evidenciado en el vídeo:** la tormenta eléctrica
—destello lavanda detrás de las cordilleras y tinte rosa sobre la escena,
con la probabilidad creciendo con el avance del jugador— está en el código
(`_update_tormenta`, `_draw_relampago_lejano`, `_draw_tinte_tormenta`) y su
fase debería haberla disparado en el último tercio del recorrido. En la
grabación entregada no aparece ni un destello. No tengo identificada la
causa y prefiero declararlo a dejar que parezca que el efecto no existe.

**Sí implementado, contra lo que decía la versión anterior de este
documento:** las cordilleras por desplazamiento del punto medio con
perspectiva aérea, el skyline gótico de campanarios y las ventanas
iluminadas con parpadeo por baldosa animada. Se corrige aquí porque el
documento se había quedado atrás respecto al código.
