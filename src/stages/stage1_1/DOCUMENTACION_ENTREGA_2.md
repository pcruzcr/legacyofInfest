---
assignment_type: stage
assignment_name: "La Entrada"
assignment_id: "stage1_1"
zone: 1
student_name: "Fabrizio Espinoza Arce"
evaluation_milestone: "Evaluación Práctica II — Vertical Slice"
---

# Evaluación Práctica II — Stage 1-1 «La Entrada»

Documentación de entrega. Sigue el orden que pide el enunciado (§8).
El detalle técnico largo — con el porqué de cada decisión — está en
[`README.md`](README.md); aquí va lo breve y verificable.

**Cómo ejecutarlo**

```bash
python main.py --stage stage1_1
```

---

## 1. Descripción

| | |
|---|---|
| **Nombre** | Escenario 1-1, «La Entrada» — Zona 1, Universidad Invenio |
| **Objetivo** | Llegar a pie desde el sendero de la montaña hasta la entrada del campus |
| **Concepto** | Travesía de tutorial. Es el primer nivel jugable: enseña a moverse, saltar y esquivar sin castigar |
| **Mecánica principal** | Recorrido lateral con salto de altura variable. Mantener el botón sube más — es la mecánica que el nivel enseña y sobre la que está construido todo el terreno |

**Medidas.** 240 × 40 tiles de 16 px = 3840 × 640 px. A la resolución interna
del motor (800 × 600) son 4,8 pantallas de ancho.

### Diseño (§4 del enunciado)

| | |
|---|---|
| **Tema** | Sendero selvático que sube a un campus universitario, al atardecer |
| **Recorrido** | Lineal de izquierda a derecha, subiendo. Sale de día y llega casi de noche |
| **Interacciones** | 7 puntos de control, 5 coleccionables de luz, 1 disparador de mensaje, 1 salida |
| **Obstáculos** | 6 insectos caminantes, 3 aves de dosel, 2 ranas que disparan. Tres piedras de sendero con huecos de 24 px y 40 px |
| **Inicio** | `PlayerSpawn` en x=160, sobre el sendero bajo |
| **Final** | `NextTrigger` en x=3744, en la puerta del campus |
| **Progresión** | El terreno sube por escalones de 32 px: 544 → 512 → 480 → (hondonada 528) → 480 → 448 → 416 → 384 → 352 |
| **Dificultad** | Deliberadamente baja. No hay fosos ni muerte por caída: el único castigo es el contacto con enemigos. La hondonada del medio cuesta tiempo, no una vida — se sale por el escalón o por la plataforma que la puentea |

---

## 2. Computación Gráfica

Los seis puntos que pide el enunciado, con el archivo y la función concretos.

### 2.1 Curvas y modelado

**Dónde.** [`entities/canopy_bird.py`](entities/canopy_bird.py) — el ave del
dosel planea siguiendo una **curva de Bézier cúbica**.

**Cómo.** Los cuatro puntos de control se declaran en Tiled como objetos
`Waypoint` (12 en total, 4 por ave) y la curva se evalúa con
`CurveTools.bezier()` del framework, que usa bases de Bernstein. No se escribe
la fórmula a mano: la regla del curso es usar lo que el motor ya trae.

La curva se muestrea **una sola vez** al construir el ave, en 64 puntos, y
después cada fotograma sólo se interpola con `CurveTools.sample_path()`. Una
Bézier cúbica no está parametrizada por longitud de arco, así que recorrerla a
`t` constante daría una velocidad que cambia sola; el remuestreo uniforme lo
corrige.

**Modelado.** Los cantos rodados del sendero son geometría de 3 × 2 tiles
calculada como una **elipse sobre el conjunto**, no tile a tile
(`_canto()` en el generador de tilesets). Dibujarlos por tile daba bloques
alineados a 4 px que parecían hormigón; calcular la silueta sobre el grupo
entero da una piedra redonda.

**Verlo en el juego:** `F1` dibuja la polilínea de las 64 muestras de cada
Bézier sobre la escena.

### 2.2 Representación de escenas

**Dónde.** El `.tmx` y el orden de dibujo de la escena.

**Cómo.** Seis capas con desplazamiento distinto, de fondo a frente:

| Capa | Contenido |
|---|---|
| `BG_Far` | Cielo, sol, nubes, planos de colina lejanos |
| `BG_Mid` | Data Center y antenas del horizonte |
| `BG_Near` | Árboles del sendero |
| `Terrain` | Suelo, roca, el túnel |
| `Terrain_Detail` | Hojarasca, helechos, detalle |
| `FG_Overlay` | Dosel y estalactitas, por delante del jugador |

**Profundidad** por perspectiva aérea: los planos de colina van de sombra a luz
(gids 219→217 al fondo, 223→221 más cerca), de modo que lo lejano tiene menos
contraste, como pasa de verdad con la bruma.

**Jerarquía visual.** El sendero es la única banda clara y continua de la
pantalla; todo lo demás — dosel arriba, vegetación abajo — es más oscuro y
enmarca el camino. La navegación no necesita flechas porque el contraste ya
dice por dónde se va.

### 2.3 Color

**Dónde.** [`processing/sunset_light.py`](processing/sunset_light.py).

**Cómo.** La luz cambia conforme se avanza: se sale de día y se llega al
atardecer. La operación es de `ColorTools` del framework —conversión de espacio
y tinte ámbar— y **la dirige la posición del jugador**, no un temporizador: el
avance por el nivel es el parámetro.

La paleta se sacó midiendo fotografías reales del campus
([`DIRECCION-DE-ARTE.md`](DIRECCION-DE-ARTE.md)): tierra roja volcánica, roca
cálida, verdes de colina. La primera versión usaba azul-gris de fábrica y no se
leía como Costa Rica.

### 2.4 Transparencia

**Dónde.** Tres usos distintos, cada uno por una razón:

1. **`ColorTools.alpha_blend`** — el tinte del atardecer se mezcla parcialmente
   sobre la escena, con `α` creciendo con el avance. Con avance 0 la mezcla es
   totalmente transparente y no toca nada.
2. **`pygame.SRCALPHA`** — el halo del sol se dibuja en una superficie con
   canal alfa propio y se compone con `BLEND_RGB_ADD`, porque un halo es luz
   que se **suma**, no pintura que tapa
   ([`animation/sol_poniente.py`](animation/sol_poniente.py)).
3. **`set_alpha` + `BLEND_ADD`** — el realce de contornos de la tecla `E` se
   suma al 47 % sobre la escena. En las zonas planas el mapa de bordes vale
   cero y no cambia nada; sólo aclara los contornos.

### 2.5 Texturas

**Dónde.** Seis tilesets propios en `assets/maps/stage1_1/`, todos de
128 × 128 px = 8 × 8 tiles de 16 px.

| gid | Tileset | Contenido |
|---|---|---|
| 1–64 | `tileset_la_entrada` | Tierra, roca, detalle, dosel, plataformas |
| 129–192 | `tileset_campus` | Edificio, caseta, cartelón, cercas |
| 193–256 | `tileset_lejano` | Data Center, antenas, planos de fondo |
| 257–320 | `tileset_vegetacion` | Helechos, arbustos, flores, lianas |
| 321–384 | `tileset_cielo` | Día, atardecer, noche, luna, nubes |
| 385–448 | `tileset_arboles` | Árboles, palmeras, hierba |

**Escala y resolución.** Tile de 16 px, paleta indexada, sombreado por
dithering, sin degradados ni alfa parcial — coherente con el resto del juego.

**Por qué propios.** Los tilesets de zona que trae el repo son placeholders:
`tileset_jungle_stone.png` tiene 64 celdas con **8 tiles únicos** repetidos,
tres de ellos de color plano. Lo dice el propio generador del profesor, que
cicla `ttype = (gy * cols + gx) % 8`.

**Correspondencia textura–objeto.** Cada tileset cubre un plano de profundidad
distinto, y los gids de colina van emparejados sombra→luz para que el mismo
relieve se pinte más claro cuanto más lejos está.

### 2.6 Animación

**Dónde.** [`animation/sol_poniente.py`](animation/sol_poniente.py).

**Cómo.** El sol recorre el cielo mientras el jugador avanza, de
`(0.78, 0.14)` a `(0.16, 0.46)` en coordenadas de pantalla. El movimiento no es
lineal: pasa por `ease_in_out_quad`, cuya derivada es `4t` subiendo y `4-4t`
bajando — vale cero en los dos extremos y máximo en el medio. El sol arranca
despacio, cruza rápido y se posa despacio, que es lo que hace un sol de verdad
cerca del horizonte.

**Sincronización con el gameplay.** Al cruzar el umbral del horizonte (82 % del
recorrido) el sol emite un evento propio por el `EventBus`
(`stage1_1:sol_en_el_horizonte`), y el escenario reacciona. La animación no es
decorado suelto: está enganchada a la progresión.

**Dónde se dibuja.** En `dibujar_fondo()`, para que el sol quede **detrás** de
las colinas y se ponga tras ellas en vez de flotar por delante.

**Otras animaciones.** Las tres aves recorren su Bézier en ping-pong con easing;
los insectos patrullan; las ranas disparan cada 1,6 s; los coleccionables
parpadean.

---

## 3. Testing

### 3.1 Pruebas realizadas

| Prueba | Comando | Resultado |
|---|---|---|
| Suite del escenario | `pytest src/stages/stage1_1/tests/ -q` | **172 pasan** |
| Calificador de nivel | `scripts/grade_stage.py assets/maps/stage1_1/stage1_1.tmx` | **130/130** |
| Validador de TMX | `scripts/validate_tmx.py --ci` | **22/22** |
| Recorrido completo | `herramientas/verificar_recorrido.py` | **llega a la salida, 99 %** |
| Banco de saltos | `python -m tests.playtest.jump_bench` | envolvente 87,1 px |

### 3.2 Lista de comprobación del enunciado (§5)

Medida con el bot de playtest del repo recorriendo el nivel entero:

```
OK  Puedo completar el nivel?     llega a la salida en 140 s
OK  El recorrido funciona?        avance 99 %
OK  Puedo quedar atrapado?        sin atascos
OK  Puedo atravesar zonas?        nunca salió del mapa
OK  Puedo romper la progresión?   0 retrocesos
OK  Las colisiones funcionan?     el jugador nunca atravesó el suelo
--  Puedo saltarme una sección?   5/7 puntos de control activados
Muertes: 0
```

Lo de los 5/7: el bot va saltando y **pasa por encima** de dos puntos de
control, que se activan por contacto. No rompe la progresión — sólo significa
que si muriera reaparecería más atrás. Queda pendiente de confirmar jugando a
mano.

### 3.3 Problemas encontrados y correcciones

El detalle completo, con las mediciones, está en
[`REPORTE-DE-BUGS.md`](REPORTE-DE-BUGS.md). Resumen:

| # | Problema | Corrección | Estado |
|---|---|---|---|
| 1 | La auto-exposición lavaba el cielo y las colinas | Banda muerta [62, 108]: un nivel bien pintado no se toca | Corregido |
| 2 | `apply_kernel` daba imagen negra con Sobel | `\|G\| = apply_kernel(k) + apply_kernel(-k)` | Sorteado |
| 3 | El realce de bordes lavaba la escena entera | Intensidad de 190 a 120 | Corregido |
| 4 | Árboles con forma de piruleta | Copa de 4 × 3 tiles y limpieza de la vegetación vieja | Corregido |
| 5 | Dithering de Bayer a nivel de tile: se veía el damero | Revertido a tonos planos discretos | Corregido |
| 6 | El `guard_system` no pinta nada en un nivel 1 | Eliminado entero | Corregido |
| 7 | El techo del túnel se leía como un muro de hormigón | Borde irregular y bocas en cuña | Corregido |
| 8 | `moderngl` documentado como opcional pero obligatorio | Reportado — es del motor, no se toca | Reportado |
| 9 | El minimapa es cuadrado y el nivel es 6:1 | Reportado — es del motor | Reportado |
| 10 | Los **ocho** enemigos de suelo enterrados 32 px | En Tiled la `y` se ancla arriba, no en los pies. Convención medida en dos mapas del profesor | Corregido |
| 11 | Más de 200 tiles de liana colgando del cielo | Regla que mira el terreno real, no la columna | Corregido |
| 12 | `ESC` no pausa: está en `CANCEL` **y** en `PAUSE` a la vez | Reportado — es del motor. Se pausa con `P` | Reportado |
| 13 | Almenas en el borde del cielo y roca cortada en vertical | Sin dithering en la costura; cima en ladera | Corregido |
| 14 | El cartel «STAGE COMPLETE» nunca se veía: el final eran 2,9 s en blanco | Del motor (`stage_scene.py:797`). Sorteado desde el escenario, con 3 pruebas | Sorteado |
| 15 | Ruido blanco sobre la música: el mixer se abría en 7.1 | Del motor (`app.py:209`). Sorteado abriéndolo en estéreo antes | Sorteado |
| 16 | Un rectángulo celeste se mueve solo tras morir | **No era defecto**: es el fantasma de la mejor carrera (`fantasma.py`, AUD-142). Costó cuatro hipótesis equivocadas | Descartado |
| 16b | …pero se dibuja como un rectángulo liso y nadie entiende qué es | Del motor. Debería usar la máscara del sprite, no un `fill` de la caja | Reportado |
| 17 | El deslizamiento (agacharse en carrera) **siempre empuja a la derecha** | Del motor (`grounded.py:252`): usa `1.0` fijo en vez del signo de la velocidad | Reportado |
| 18 | El deslizamiento triplica la velocidad sin ninguna señal visual | Del motor. 300 px/s frente a 90, sin efecto que lo anuncie | Reportado |
| 19 | El límite de tiempo (180 s) no daba para explorar ni probar | Subido a 300 s. El recorrido solo ya son 140 s | Corregido |
| 20 | Faltaban `start_hour`, `day_length` y 2 coleccionables de la ficha | Añadidos: la ficha del profesor pide 5 coleccionables y `start_hour` obligatorio | Corregido |

---

## 4. Iteración respecto de la primera entrega (§6)

La primera entrega sacó **127/130**. El ciclo que pide el enunciado
—VERSIÓN → PRUEBA → PROBLEMA → CORRECCIÓN → NUEVA PRUEBA → MEJORA— se recorrió
tres veces. La tercera vuelta es la que más enseña, y por eso va entera.

### Vuelta 1 — la visual

**Problema:** el nivel se veía mal y no se entendía. No se distinguía un árbol,
no se leía como una universidad, el cielo y el atardecer no se apreciaban.

**Causa:** el generador escribía tiles **a ciegas**. Nadie —yo incluido— había
mirado nunca el mapa renderizado.

**Corrección:** herramientas para *ver* (`render_mapa.py`, `ver_tileset.py`,
que imprime el gid encima de cada tile) y rehacer la paleta desde fotos reales
del campus.

**Resultado:** todos los defectos visuales posteriores se encontraron mirando.
La lección: no se puede pulir lo que no se ve.

### Vuelta 2 — jugarlo, no sólo probarlo

**Problema:** las 169 pruebas pasaban y el calificador daba 130/130, pero nada
de eso decía si el juego **se juega** bien.

**Corrección:** `jugar_y_capturar.py`, que usa el bot del repo y guarda
fotogramas ya dibujados.

**Resultado:** apareció el problema 1 de la tabla — la auto-exposición estaba
lavando el arte. Sólo era visible jugando: ninguna prueba unitaria lo veía.

### Vuelta 3 — «el nivel no se puede terminar» (y por qué era mentira)

Esta es la más útil, porque la primera conclusión fue **falsa** y descubrirlo
enseñó más que el arreglo.

**Prueba.** Se recorrió el nivel entero por primera vez con
`verificar_recorrido.py`. Hasta entonces sólo se habían corrido 36 s.

**Problema aparente.** El bot se quedaba clavado en `x=1773` y no pasaba del
45 % del recorrido. Con **cero muertes**, o sea: no era combate, era geometría.
Y `x=1773` es justo la pared por la que se sale de la hondonada, un escalón de
48 px.

**Primera hipótesis — equivocada.** Que la plataforma `Plat_02` colgaba encima
y le pegaba en la cabeza al jugador. Se acortó… y el número no se movió:
seguía en 1/49. Una hipótesis que no cambia la medida está mal.

**Medición de verdad.** Trazando el salto fotograma a fotograma
(`trazar_salto.py`), la velocidad vertical resultó ser:

```
-6,1  -5,9  -5,7   subiendo a plena fuerza
-2,6  -2,4  -2,2   cortado de golpe en el fotograma 4
```

**Causa real.** El salto de este motor es **de altura variable**: soltar el
botón corta el impulso. Y `walk_right_bot`, el bot de referencia del repo,
mantiene `JUMP` sólo **dos fotogramas**. Nunca da un salto entero — se eleva
53 px de los 96 que da el salto completo. Un bot así no puede subir un escalón
de 48 px, **y eso no dice nada del nivel**: dice que el bot toca el botón en
vez de mantenerlo. Su propia cabecera avisa de que es «deliberadamente tonto».

**Corrección.** Dos, y una de ellas fue deshacer:

1. Un bot que mantiene el salto 12 fotogramas, como una persona. Con él el
   nivel **se completa: 99 % del recorrido, sin atascos, 0 muertes**.
2. **Revertir el acortado de `Plat_02`.** Al mirarla bien, esa plataforma
   sobrepasa la hondonada 32 px: *es el puente para cruzarla por arriba*.
   Acortarla borraba una ruta y hacía el nivel más difícil. Un cambio hecho
   sobre una hipótesis falsa se deshace, aunque no rompa nada.

**Resultado.** El nivel nunca estuvo roto. Lo que estaba mal era el
instrumento, y hasta que no se midió el instrumento no se supo. De paso salió
un hallazgo que le sirve al curso entero: **cualquier nivel con escalones de
más de ~50 px dará falso «infranqueable» con el bot de referencia.**

### Vuelta 4 — lo que sólo ve otra persona

Las tres vueltas anteriores las hice yo, con herramientas. Esta la hizo **otra
persona jugando el nivel**, y encontró en un rato cinco cosas que ni las 169
pruebas, ni el calificador, ni el bot habían visto nunca. Es la diferencia
entre comprobar que el juego *funciona* y comprobar que *se juega*.

| Lo que dijo | Qué era en realidad | Estado |
|---|---|---|
| «Hay un bicho que sale por debajo del piso» | **Los ocho** enemigos de suelo estaban enterrados 32 px | Corregido |
| «Hay lianas en el cielo» | 200+ tiles de dosel en las filas 0-6, cielo abierto | Corregido |
| «Al darle a ESC no se pausa, sólo parpadea negro» | `ESC` está en `CANCEL` **y** en `PAUSE`: se abre y se cierra sola | Del motor — reportado |
| «Un fondo gris tipo roca flotando, muy raro» | Almenas por dithering en la fila 0 + roca sin cima | Corregido |
| «Al final tarda unos segundos en terminar» | Deliberado: `_complete_timer = 2.9` con cartel y sonido | No es defecto |

**El error más instructivo fue el de los enemigos.** En Tiled un objeto se
ancla por su esquina **superior** izquierda, y yo había escrito la `y` de la
cara del suelo creyendo que era donde se apoyan los pies. Un bicho de 32 px en
`y=544` con el suelo en 544 queda entero bajo tierra. Antes de corregirlo medí
la convención en dos mapas del profesor —`stage_mecanicas` y `stage0`, los dos
con `base == suelo`, diferencia +0— en vez de deducirla. Los ocho corregidos y
verificados.

**Y el más humillante fue el de las lianas**, porque lo arreglé dos veces. La
primera regla borraba el dosel «fuera de las columnas del túnel» y funcionó
hasta que cambié la forma de la roca: al bajarle la cima, los tiles de esas
mismas columnas se quedaron sin nada encima y volvieron a colgar. Una regla
escrita en columnas no sobrevive a un cambio de forma. La definitiva mira el
terreno de verdad —«un tile de dosel se queda sólo si hay roca en su columna a
su altura o por encima»— y vale para cualquier silueta.

### Vuelta 5 — las colinas eran rectángulos, y no era culpa del color

La misma sesión dejó claro lo que yo ya sospechaba mirando capturas: el fondo
se leía como bloques apilados.

**Lo primero fue descartar el color.** Medí la luminancia de los tiles:

```
plano lejano  133 - 169     claro y desaturado
plano cercano  80 - 124
bosque        106 -> 49     el mas oscuro
```

La perspectiva aérea estaba bien puesta. El problema era **la forma**, y tenía
dos causas concretas:

1. **Los periodos estaban mal escritos.** La línea del horizonte usaba
   `c / 97 * 2π` —periodo de 97 columnas— pero las dos crestas de los planos
   usaban `c / 53.0` sin el `2π`, lo que da un periodo de 53·2π ≈ **333
   columnas**. El mapa mide 240. Esas dos líneas no completaban ni una onda en
   todo el nivel: eran casi rectas, y de ahí las fronteras horizontales.

2. **Los tres planos compartían la cara de sombra**, calculada además con la
   pendiente del horizonte del cielo. Como esa curva varía despacio, los tres
   planos cambiaban de tono en la **misma columna**: una costura vertical que
   cruzaba el fondo entero y lo partía en rectángulos.

**Corrección.** Cada plano lleva ahora su propia línea de cresta, con periodos
en columnas de verdad y una tercera octava corta (13-19 columnas) que aporta el
detalle que faltaba; y cada uno elige su cara mirando **su** pendiente. Las
costuras dejan de coincidir y la silueta hace el trabajo.

**Lo que no se hizo, a propósito:** no se difumina entre tonos. Ya se probó con
Bayer y a 16 px por celda el patrón se lee como un tablero de ajedrez sobre
toda la montaña — peor que el escalón que venía a arreglar. En pixel art una
masa grande se resuelve con pocos tonos planos y dejando que la silueta
trabaje, no metiendo ruido dentro de la mancha.

---

## 5. Evidencia

| Qué | Dónde |
|---|---|
| Recorrido jugado, hoja de contactos | `capturas/playtest_contactos.png` |
| Antes/después de cada operación | `capturas/` |
| Reporte de defectos completo | [`REPORTE-DE-BUGS.md`](REPORTE-DE-BUGS.md) |
| Dirección de arte y paleta medida | [`DIRECCION-DE-ARTE.md`](DIRECCION-DE-ARTE.md) |

**Sesión de pruebas con otra persona:** realizada. Cinco hallazgos, tres
corregidos, uno reportado al motor y uno descartado tras medirlo. El detalle
está en la vuelta 4 de la sección anterior.

### 5.1 Qué demuestra el vídeo (§24)

Los diez puntos que pide el enunciado, con el punto del nivel donde se ve cada
uno. Las coordenadas son las del mapa, en píxeles.

| # | Punto del §24 | Dónde se demuestra |
|---|---|---|
| 1 | Ejecución del juego | Arranque desde el lanzador, con la consola cargando |
| 2 | Inicio del nivel | `x = 160`, con el cartel de bienvenida en `x = 224` |
| 3 | Gameplay | Caminar, saltar, agacharse, dash y deslizamiento |
| 4 | Traversal | Las tres piedras de `x ≈ 800-990` y el tramo que sube |
| 5 | Combate | Insecto de `x = 640`, rana de `x = 1600` |
| 6 | Interacciones | Disparador de mensaje, coleccionables, teclas `E` y `F1` |
| 7 | Checkpoints | Contacto y muerte deliberada para comprobar la reaparición |
| 8 | Exploración | Los 5 coleccionables: `x =` 704, 1408, 2336, 2688 y 3296 |
| 9 | Intentos de romperlo | Tabla 5.2 |
| 10 | Final del nivel | Salida en `x = 3744` y cartel «STAGE COMPLETE» |

### 5.2 Intentos deliberados de romper el nivel (§23)

Las doce preguntas del enunciado. La columna «cómo se comprobó» distingue lo
**medido** con herramienta de lo **jugado** a mano, porque no valen igual.

| # | Pregunta | Cómo se comprobó | Resultado |
|---|---|---|---|
| 1 | ¿Puedo saltarme una sección? | Jugado: cruzar la hondonada por la plataforma de `x = 1568-1824` | Sí, y es **intencional**: es la ruta alta. No se salta contenido |
| 2 | ¿Puedo quedar atrapado? | Medido y jugado: entrar en la hondonada (`x ≈ 1700`) y salir | No. El recorrido automático completa el nivel sin atascos |
| 3 | ¿Puedo romper la progresión? | Medido: recorrido completo | No. 0 retrocesos no explicados |
| 4 | ¿Puedo llegar antes de una habilidad? | — | **No aplica**: el nivel no tiene puertas por habilidad |
| 5 | ¿Puedo regresar? | Jugado: volver sobre los pasos y avanzar de nuevo | Sí, sin romper nada |
| 6 | ¿Los checkpoints funcionan? | Jugado: tocar uno y morir a propósito | Sí. Pasan de azul a dorado y devuelven al último tocado |
| 7 | ¿Los enemigos dan el desafío esperado? | Jugado: los tres tipos | Acorde a un nivel de tutorial (dificultad 1/5 en la ficha) |
| 8 | ¿La navegación es clara? | Jugado | Sí. El sendero es la única banda clara y continua |
| 9 | ¿El pacing funciona? | Medido: reparto de enemigos | El túnel (`x = 1984-2736`) no tiene enemigos en 750 px. Se le añadió un coleccionable en `x = 2688` |
| 10 | ¿Los secretos son legibles? | Jugado | Los 5 coleccionables emiten luz propia y se ven sin buscar |
| 11 | ¿Hay zonas aburridas? | Medido + jugado | El túnel era la candidata; corregido con el coleccionable |
| 12 | ¿Hay zonas excesivamente difíciles? | **Medido** con el banco de saltos del motor | El hueco de 40 px es el punto más exigente. Un hueco de 48 px se cruza desde 4 de 49 despegues; el de 40 queda por debajo de ese umbral |

Las preguntas 5 a 8, 10 y 11 son de juicio y no las contesta ninguna
herramienta: quedaron confirmadas **jugando el nivel en la sesión grabada**. Las
demás salen de medidas reproducibles, y los comandos que las producen están en
`herramientas/`.

### 5.3 Defectos que el vídeo enseña en pantalla

Todos están medidos y desarrollados en
[`REPORTE-DE-BUGS.md`](REPORTE-DE-BUGS.md).

| Qué se ve | De quién es | Ficha |
|---|---|---|
| `ESC` no pausa: la pantalla parpadea en negro | Motor | F-012 |
| El minimapa desperdicia el 83 % de su recuadro | Motor | F-002 |
| El deslizamiento hacia la izquierda empuja a la derecha | Motor | F-020 |
| El deslizamiento triplica la velocidad sin señal visual | Motor | F-021 |
| El fantasma de la mejor carrera es un rectángulo liso | Motor | F-022 |
| El cartel «STAGE COMPLETE» no se veía — ya corregido | Motor, sorteado | F-016 |
| Salirse del mapa trepando el muro — ya corregido | Del escenario | F-023 |

---

## 6. Controles

| Tecla | Acción |
|---|---|
| `A` / `D` o flechas | caminar |
| `ESPACIO` o `W` | saltar — **mantener sube más** |
| `S` | agacharse |
| `SHIFT` | dash |
| `Z` / `X` | ataque corto / largo |
| **`E`** | **enfocar: realza los contornos** |
| **`F1`** | **overlay: dibuja las curvas de Bézier y los vectores** |
| `TAB` | bestiario |
| `P` | **pausa** (con `ESC` no funciona: ver defecto 12) |

---

## 7. Uso de IA (§7)

Se usó Claude Code como apoyo para programación, depuración y análisis. Las
decisiones de diseño, la dirección de arte y la interpretación de las
mediciones son mías, y puedo explicar y defender cada una — incluida la de la
vuelta 3, donde la primera conclusión automática era errónea y hubo que
descartarla.

Todas las herramientas de verificación que se citan aquí están en
`herramientas/` y son reproducibles con un comando.
