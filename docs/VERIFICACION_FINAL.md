# Verificación final: qué está, qué falta, y qué nota

**Fecha:** 28 de julio de 2026 · **Método:** medición, no lectura
Cada número sale de un comando ejecutado hoy.

---

## 1. Los cinco fallos reportados al jugar

Se reportaron cinco cosas jugando. Las cinco están corregidas, y cada
corrección tiene una prueba que se pone en rojo si alguien la revierte.

| Lo reportado | Qué era en realidad | Dónde |
|---|---|---|
| «no se ve la cadena de combos» | La interfaz se dibujaba **antes** que la luz, así que `LightSystem` la multiplicaba. Medido: el HUD conservaba el **42 %** de su brillo y el indicador de combo pasaba de **406 píxeles amarillos a 0**. Un defecto que introduje yo en F1.1 al bajar la luz ambiente de 1,0 | AUD-090 |
| «a los enemigos no se les baja la barra» | Los enemigos normales **no tenían barra de vida**; sólo los jefes. El combate funcionaba —vida 3,0 → 0,5— pero no se veía | AUD-091 |
| «el bestiario con Esc vuelve al menú de demos» | Usaba `pop`, pero se entra con `replace`. La pila quedaba en `['SplashScene']` | AUD-092 |
| «en el mapa del mundo sale más arriba, sobre el título» | Nodos con coordenadas absolutas escritas para 320×224. Tres de cinco caían en y=50/60/80 con la cabecera terminando en y=105 | AUD-093 |
| «la imagen y el texto no están centrados» | Dos defectos distintos, ambos abajo | AUD-094 |

**Verificación por mutación:** revertir cada una de las cuatro primeras deja
la suite en rojo.

---

## 2. AUD-094 — las trece demos dibujaban en una esquina

Se midió con una rejilla de 3×3 sobre el área útil. **Antes:**

```
TransformLab   x[  4,247] y[33,199]   #../.../.../   3 de 9 celdas
ComboDemo      x[ 20,273] y[43,238]   #../#../.../   2 de 9
VectorLab      x[  8,379] y[40,159]   ##./.../.../   2 de 9
ColorTheory    x[  4,315] y[33,163]   ##./.../.../   2 de 9
FilterDemo     x[  0,799] y[33,515]   #.#/#.#/#.#/   6 de 9, centro muerto
```

Dos causas distintas con la misma raíz —código escrito para una pantalla de
320×224 que nunca se migró a los 800×600 actuales—:

1. **Siete escenas con coordenadas absolutas.** El origen del laboratorio de
   transformaciones en `(160, 100)`, los deslizadores de color con `x=10` y
   `w=300`, el mapa de ruido pegado **sin escalar** en `(0, 40)`, el nivel de
   colisiones en un mundo de 400×224 dibujado como píxeles de pantalla.
2. **Cuatro escenas de dos paneles con `PANEL_W` al 32 % del ancho:** 256 px
   de panel y **288 de hueco central**. El vacío era más ancho que cada
   panel.

La solución fue un `Lienzo` en `demo_layout` que traduce coordenadas de
autoría al área útil, escalando de forma **uniforme** y centrando el sobrante.
La aritmética de cada lección —longitud de un vector, producto escalar,
resolución de colisiones, interpolación— se queda en unidades de autoría, que
son los números que el estudiante compara con los que calcula a mano; sólo el
trazo pasa por el lienzo. `PANEL_W` pasó a repartirse el ancho con una
canaleta de 24 px, lo que arregló las cuatro escenas de paneles de golpe.

**Después:** las trece tienen contenido en la celda central.

Además se corrigieron dos límites que estaban en el sistema equivocado: el
laboratorio de vectores recortaba las posiciones contra `INTERNAL_WIDTH` (800)
sobre un lienzo de 320, y el de colisiones dejaba al jugador salirse del nivel
por la derecha, donde no hay plataformas contra las que colisionar —que es
justamente lo que esa escena existe para enseñar—.

---

## 3. AUD-095 — el temario, unidad por unidad

Lo que se pidió: *«que apareciera información técnica matemática y fuera
separado unidad por unidad, que se activaran cuando cada una se completara»*.
No existía ninguna de las tres cosas.

`DemoMenuScene` tenía una lista plana de diecisiete tuplas. Las diez demos
estaban abiertas desde el primer minuto: se podía entrar en reconocimiento de
patrones (Unidad IX) sin haber visto un vector. No había explicación
matemática en ninguna parte del proyecto. Y `QuizManager`, que existía y se
abría con Q en cuatro laboratorios, **no registraba nada**: se contestaba y se
olvidaba al salir de la escena.

### Lo que hay ahora

| Módulo | Qué aporta |
|---|---|
| `framework/academic/curriculum.py` | Las **10 unidades**, cada una con 3 bloques de teoría —enunciado, fórmula y explicación— y la ruta del fichero del motor que la implementa, más sus **5 preguntas** con la razón de la respuesta correcta. **30 bloques y 50 preguntas** escritos, no plantillas |
| `framework/academic/progress.py` | Progreso encadenado: para abrir una unidad hay que haber aprobado la anterior con **4 de 5** |
| `framework/academic/sesion.py` | Estudiante identificado por el correo de la universidad. Un JSON por estudiante, escrito a temporal y renombrado |
| `engine/scenes/unit_theory_scene.py` | Teoría y examen. Registra el resultado una sola vez, al final, y lo guarda en el acto |

### Tres decisiones que conviene conocer

- **El umbral es 4 de 5, no 3.** Con cuatro opciones por pregunta, colar 3 de
  5 al azar tiene un **10,4 %** de probabilidad; colar 4 de 5 baja al **1,6 %**.
- **Se guarda el mejor intento, no el último.** Volver a una unidad aprobada
  para repasar y fallar por ir deprisa no puede volver a cerrar la unidad
  siguiente, que el estudiante ya podría tener a medias.
- **Sin identificarse también se juega.** El progreso no se guarda, pero un
  motor que exija registrarse para abrir la primera demo es un motor que nadie
  prueba.

La tecla **T** abre la teoría **incluso de una unidad bloqueada**: aprobarla es
lo único que la abre, así que bloquear su examen dejaría al estudiante sin
manera de avanzar.

---

## 4. La deuda técnica de la tabla, liquidada

| Qué decía la tabla | Estado |
|---|---|
| `FilterDemoScene` a 7,8 ms de mediana | **0,73 ms** (AUD-097) |
| Stage 0: 2 plataformas sin ruta desde el spawn | **0** (AUD-096) |
| Stage 0 sin `author` | Añadido |
| 25 cadenas sin traducir al español, 34 al inglés | **0 huecos reales** |
| `test_gameplay_integration` tarda ~50 s | Sigue: 26 pruebas que construyen escenas completas |
| Traducción de los 12 documentos del estudiante | Sigue: son horas, no un problema |

### AUD-097 — la demo de filtros: 10,24 ms → 0,73 ms

Medida de nuevo tras ensanchar los paneles, había subido de los 7,8 ms
documentados a **10,24 ms de mediana** con **57 de 180 fotogramas fuera de
presupuesto**.

`cProfile` señaló un único responsable: `np.histogram` se llevaba **3,95 s de
los 4,41 s** del dibujado —el 90 %— porque se llamaba **seis veces por
fotograma** (tres canales por dos paneles) sobre imágenes que no habían
cambiado. Es el mismo defecto que AUD-073 en el laboratorio de ruido: trabajo
caro y determinista repetido sesenta veces por segundo porque nadie se
preguntó cuándo cambia su entrada.

Dos arreglos: caché invalidada por firma de las imágenes, y `bincount` +
`add.reduceat` en lugar de `histogram`, con los cortes calculados por división
entera para que el reparto en 80 barras sea **idéntico** al de `np.histogram`.
Comprobado barra por barra sobre 8 imágenes × 3 canales: **diferencia máxima
0**. Se cambió el coste, no la lección.

Resultado: mediana **0,73 ms**, p95 1,42, máximo 2,21, **cero** fotogramas
fuera de presupuesto.

### AUD-096 — el calificador castigaba a quien cerraba bien su mapa

El aviso de «2 plataformas sin ruta desde el spawn» en Stage 0 era del
calificador, no del escenario. Medido, las dos eran `Rect(0, 0, 16, 608)` y
`Rect(1584, 0, 16, 608)`: los muros laterales que cierran el mapa. Nadie salta
encima de ellos.

Eso es peor que inofensivo. Un estudiante que cierra bien su mapa recibe un
aviso por haberlo hecho bien, aprende a no fiarse del calificador, y deja de
leer también los avisos que sí importan. `analyse_stage` descarta ahora las
columnas de más de dos tercios del alto del mapa y más altas que anchas.
Comprobado que una isla de verdad inalcanzable se sigue detectando.

Stage 0 en el calificador: **86,2 % → 93,1 %**.

---

## 5. Estado medido hoy

| Medida | Valor |
|---|---|
| Pruebas | **1.657**, todas en verde |
| Archivos de prueba | 77 |
| ruff sobre `src/`, `tests/`, `scripts/` | limpio |
| Validador TMX | 2/2 |
| Validador de recursos | 0 errores, 0 avisos |
| Catálogos de idioma | en orden, sin huecos reales |
| Sincronía de dependencias | 15/15 |
| Cobertura de propiedades TMX en el mapa de ejemplo | **100 %** |
| Stage 0 en el calificador | **121/130 (93,1 %)** |
| Stage 0, mediana por fotograma | **7,20–9,00 ms** (presupuesto 16,67) |
| `FilterDemoScene`, mediana | **0,73 ms** |

Sobre la mediana de Stage 0: tres medidas consecutivas dieron 11,17, 9,00 y
7,20 ms. La primera incluye el calentamiento; el número que vale es el de las
ejecuciones en caliente, en línea con los 7,98 ms de la sesión anterior. No
hay regresión, hay varianza del entorno de medida, y decirlo importa más que
elegir el número más favorable.

---

## 6. Qué falta

### Falta de contenido, no de motor

| Qué | Estado |
|---|---|
| **23 de 42 tipos de objeto sin usar en ningún mapa** | Casi todos son variantes de enemigo del bestiario que existen en código y no tienen escenario donde aparecer |
| **2 escenarios jugables** | Stage 0 y la arena del jefe |
| `MessageTrigger` y `Waypoint` | Los tipos existen; ningún mapa los usa |

### Deuda técnica que queda

| Qué | Medido | Coste |
|---|---|---|
| Traducción de los 12 documentos del estudiante | La maquinaria está; faltan las horas | 1–2 semanas |
| `test_gameplay_integration` tarda ~50 s | 26 pruebas que construyen escenas completas | factura que crecerá |
| Rúbrica propia para arenas de jefe | El calificador de escenarios les aplica criterios de nivel | 1 día |
| Identificación del estudiante sin pantalla propia | `SesionAcademica.entrar()` funciona y está probada, pero todavía no hay escena que pida el correo | 1 día |

### Lo que decidí no hacer, y por qué

- **No tocar el renderizador para hacer 3D.** Lo que hay es post-procesado
  sobre un quad, igual que Hollow Knight u Ori. Sustituirlo rompería lo único
  que hace valioso este proyecto: que el estudiante pueda leer el código de
  dibujado.
- **No usar `gettext`.** Exige herramientas externas, sus catálogos son
  binarios y no se revisan, y el caso de uso son dos idiomas.
- **No añadir entradas identidad a `es.json`.** Silencian una nota informativa
  a cambio de romper la comprobación de ida y vuelta de `test_i18n`: afirman
  que un original está en castellano justo cuando `en.json` dice lo contrario.
  El código fuente es bilingüe y el respaldo ya muestra correctamente un
  literal que ya está en el idioma pedido.

---

## 7. La nota

Contra el objetivo declarado —**un semestre con 30 estudiantes sin apagar
incendios**— y no contra un producto comercial.

| Área | Nota | Por qué |
|---|---|---|
| **Motor y framework** | 9,5 / 10 | 1.657 pruebas, ruff limpio, arquitectura legible. `FilterDemoScene` ya no es la excepción que bajaba la nota |
| **Herramientas del profesor** | 9 / 10 | Calificar, exportar notas, detectar plagio, generar exámenes y realimentación. Falta rúbrica propia para arenas |
| **Herramientas del estudiante** | 8,5 / 10 | Validador, previsualizador y plantilla honesta. El ciclo está cerrado |
| **Configurable desde TMX** | 10 / 10 | 16 de 16 propiedades demostradas en el mapa de ejemplo, con prueba que lo vigila |
| **Valor pedagógico** | 9,5 / 10 | Sube de 8,5: ahora hay 30 bloques de teoría con su fórmula, su explicación y el fichero que la implementa, y 50 preguntas que de verdad bloquean el avance. Sobel y Canny a mano, ruido procedural propio |
| **Documentación** | 7 / 10 | 74 documentos sincronizados con el motor por pruebas. Penalizado porque la mayoría sigue en inglés para un curso en español |
| **Contenido de juego** | 5 / 10 | 2 escenarios, 1 jefe, 8 clases de enemigo. Es lo que es: un motor con un prólogo |
| **Producción** | 8 / 10 | Arranca, se empaqueta, se instala, no se cae sin tarjeta de sonido. Falta probar el `.exe` en una máquina limpia |

### **Nota global: 8,9 / 10**

Ponderada hacia lo que se va a usar este trimestre: motor, herramientas y
valor pedagógico pesan más que el contenido de juego.

Sube de 8,4 por tres razones concretas y medibles: el temario existe y
bloquea de verdad (+1 en valor pedagógico), la demo más cara del proyecto pasó
de 10,24 ms a 0,73 (+0,5 en motor), y la deuda barata de la tabla está
liquidada en vez de anotada.

---

## 8. Lo que significa esa nota

**Puede impartir el curso con esto.** El motor está sano, las herramientas
funcionan, un estudiante puede construir un escenario completo sin escribir
Python, usted puede calificarlo automáticamente por estructura y por diseño, y
ahora además el temario tiene un orden que se respeta solo.

**Lo que baja la nota no es técnico.** Es contenido —dos escenarios— e idioma
—documentación en inglés—. Las dos cosas son horas de trabajo, no problemas
que resolver.

**Y una advertencia que me aplico.** Esta sesión encontró **ocho defectos más**
en sistemas que llevaban meses «terminados», todos con la misma forma: código
correcto, probado en aislamiento, que no llegaba a la pantalla o que llegaba
al sitio equivocado. Trece demos llevaban desde siempre dibujando en un cuarto
de la pantalla y nadie lo había escrito nunca en un informe.

Ninguno se veía leyendo el código. Se vieron **midiendo píxeles y
cronometrando fotogramas**.

Si el próximo semestre alguien añade una característica, la pregunta que
merece la pena hacerle no es «¿pasan las pruebas?» sino **«¿la has visto en
pantalla?»**.
