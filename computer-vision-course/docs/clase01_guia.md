# Clase 1 — Adquisición, histogramas y mejoramiento

**Duración:** 4 h · **Unidad VII** (primera parte) · **Grupos de 3** en el laboratorio

> **Pregunta que responde esta clase:**
> *¿De dónde sale una imagen digital, cómo sé si sirve, y qué puedo hacer si no sirve?*

---

## 1. Objetivos

Al terminar, el estudiante debe ser capaz de:

1. Obtener una imagen desde cuatro procedencias distintas —cámara, fichero,
   vídeo y el motor de videojuego— y explicar en qué se diferencian.
2. Describir una imagen como matriz NumPy: forma, tipo, canales, y qué
   significa cada eje.
3. Calcular e interpretar un histograma, y decir qué **no** puede medir.
4. Convertir el histograma en un **criterio de aceptación automático**.
5. Aplicar brillo, contraste, estiramiento y ecualización, y **medir** si
   sirvieron de algo para la tarea que venía después.

## 2. Competencias

| Competencia | Cómo se evidencia |
|---|---|
| Representación computacional de una imagen | El estudiante predice la forma del array antes de imprimirla, y acierta |
| Diagnóstico de calidad de una toma | Justifica aceptar o rechazar una imagen con cifras, no con «se ve mal» |
| Criterio de ingeniería | Distingue «se ve mejor» de «la siguiente etapa funciona mejor» |
| Reproducibilidad | Su laboratorio se puede volver a ejecutar y da lo mismo |

## 3. Prerrequisitos

Python básico, NumPy a nivel de *slicing*. **No** hace falta haber visto
procesamiento de imágenes antes.

Comprobación de entorno (2 minutos, al principio de la clase):

```bash
python -m pytest computer-vision-course/tests -q
```

---

## 4. Guion de la sesión

### Bloque 1 — Teoría aplicada · 50 min

| min | Contenido | Apoyo |
|---|---|---|
| 0–10 | Qué es un píxel. Resolución, canales, profundidad de color. La imagen **es** una matriz | pizarra + `numpy` en vivo |
| 10–20 | Adquisición: cámara, escáner, fichero, vídeo, fotograma sintético. Qué cambia en cada caso | `comparar_fuentes.py` |
| 20–25 | RGB, escala de grises, y por qué OpenCV entrega **BGR** | pizarra |
| 25–40 | El histograma: qué es, cómo se lee, qué diagnostica. Sobreexposición, subexposición, rango dinámico | pizarra + `viz.histograma` |
| 40–50 | Brillo, contraste, estiramiento, ecualización. Qué hace cada uno al histograma | pizarra |

Las tres ideas que tienen que quedar, en este orden:

1. **La imagen es una matriz.** Todo lo demás son operaciones sobre números.
2. **El histograma tira la posición.** Sabe *cuántos* píxeles hay de cada
   valor; no sabe *dónde*. Por eso diagnostica exposición y no puede
   diagnosticar enfoque, ruido ni geometría.
3. **Realzar no crea información.** Estira lo que hay. Lo que falta, falta.

### Bloque 2 — Demostración del profesor · 40 min

Se ejecutan los tres ejemplos, en este orden, comentando la salida:

```bash
python examples/class01_acquisition/comparar_fuentes.py
python examples/class01_acquisition/game/histograma_de_sprites.py
python examples/class01_acquisition/mechatronics/aceptacion_de_toma.py
python examples/class01_acquisition/industrial/realce_de_pieza.py
```

**Momentos que no hay que dejar pasar:**

- En `comparar_fuentes.py`, el sprite del motor sale con **57 % de píxeles
  negros**. Preguntar por qué antes de contarlo.
- En `histograma_de_sprites.py`, la media de brillo de `player_idle.png` se
  equivoca en un **75 %**. Es el momento de introducir el canal alfa.
- En `aceptacion_de_toma.py`, la toma con ruido **pasa los cuatro criterios**.
  Es la demostración de que el histograma tira la posición.
- En `realce_de_pieza.py`, los cuatro realces dejan el IoU **igual**. Ese es el
  contenido de la clase, no un accidente.

### Bloque 3 — Laboratorio · 110 min

Ver §5. Grupos de 3, roles rotatorios cada 35 min: **teclado**, **notas**,
**verificación**.

### Bloque 4 — Cierre · 40 min

- Cada grupo enseña una figura y **una cifra** que la respalde (10 min).
- Puesta en común de las preguntas de análisis (§5.4).
- Anticipo de la Clase 2: *si el histograma no ve el ruido, ¿qué lo ve?*

---

## 5. Laboratorio

### 5.1 Entregable

Una carpeta `entrega_clase01_<apellidos>/` con:

| Fichero | Contenido |
|---|---|
| `lab01.ipynb` o `lab01.py` | El código que produce todo lo demás |
| `figuras/` | Las figuras generadas |
| `analisis.md` | Máximo 2 páginas. Respuestas de §5.4, con cifras |

### 5.2 Tareas

**T1 — Adquisición (25 min).**
Obtener tres imágenes de tres procedencias distintas. Al menos una del motor
(`FuenteMotor`) y una sintética. Para cada una, reportar forma, tipo, media,
rango, % saturados y % negros. Predecir la forma del array **antes** de
imprimirla y anotar si acertaron.

**T2 — Diagnóstico (25 min).**
Dibujar el histograma de las tres. Clasificar cada una como *correcta*,
*subexpuesta*, *sobreexpuesta* o *sin contraste*, y **justificarlo con las
cifras de T1**, no con la impresión visual.

**T3 — Criterio automático (30 min).**
Adaptar `Criterios` de `aceptacion_de_toma.py` a sus imágenes. Encontrar unos
umbrales que acepten las buenas y rechacen las malas. Después, **romperlo**:
construir una imagen que sea evidentemente mala y que aun así pase.

**T4 — Realce medido (30 min).**
Tomar la peor de sus imágenes y aplicarle los cuatro realces. Medir con el
histograma (rango, desviación, ocupación) **y** con una tarea: umbralizar con
Otsu y comparar contra la verdad-terreno. Si usan una pieza sintética, la
verdad-terreno está en `datasets/synthetic_parts/verdad_terreno.csv`.

### 5.3 Reto (opcional, para quien termine)

El sprite del motor tiene canal alfa. Escriban una función
`histograma_con_alfa(ruta)` que devuelva el histograma **correcto** y
demuestren, con una cifra, cuánto se equivocaba el ingenuo. Comparen su
resultado con `FilterTools.compute_histogram` del motor y expliquen la
diferencia.

### 5.4 Preguntas de análisis

Se responden en `analisis.md`, cada una con una cifra o una figura detrás.

1. Sus tres imágenes tienen formas distintas. ¿Cuál de las dimensiones del
   array es el alto y cuál el ancho, y cómo lo comprobaron **sin** mirar la
   imagen?
2. ¿Por qué el histograma de un sprite con transparencia tiene un pico enorme
   en 0? ¿Es un defecto de la imagen, del cargador o de la pregunta?
3. Su criterio de T3 acepta una imagen mala. ¿Qué propiedad de esa imagen no
   puede ver un histograma, y por qué no puede verla?
4. Tras el realce de T4, ¿mejoró el histograma? ¿Mejoró la tarea? Si las dos
   respuestas no coinciden, expliquen por qué.
5. ¿Cuál de sus tres imágenes **no** podrían volver a obtener idéntica mañana?
   ¿Qué consecuencia tiene eso para poder corregir este laboratorio?

---

## 6. Criterios de evaluación

Sobre 100. Es la rúbrica de laboratorio, alineada con
`docs/27_ACADEMIC_RUBRICS.md` §3 del repositorio del motor.

| Criterio | Puntos | Se consigue si… |
|---|---|---|
| **Adquisición** | 15 | Tres procedencias distintas, funcionando, con su descripción completa |
| **Representación** | 15 | Explican correctamente forma, ejes, canales y tipo. La predicción de T1 está anotada, acierten o no |
| **Diagnóstico** | 20 | Cada clasificación va respaldada por una cifra concreta, no por «se ve oscura» |
| **Criterio automático** | 15 | Los umbrales funcionan sobre sus imágenes **y** encontraron el contraejemplo de T3 |
| **Realce medido** | 20 | Miden con histograma y con tarea. Si discrepan, lo explican |
| **Reproducibilidad** | 10 | El código se ejecuta de principio a fin en otra máquina. Semillas fijas, rutas relativas |
| **Comunicación** | 5 | `analisis.md` cabe en 2 páginas y se entiende |

**Penalizaciones:**

- −10 si `analisis.md` afirma algo que su propio código contradice.
- −10 si las figuras no llevan título o no se sabe qué imagen es cuál.
- −5 por cada ruta absoluta (`C:\Users\...`) en el código entregado.

**Lo que NO se evalúa:** que las imágenes queden bonitas, ni que el realce
elegido sea «el mejor». Se evalúa que la elección esté **medida y justificada**.

---

## 7. Material

| Recurso | Ruta |
|---|---|
| Notebook de laboratorio | `notebooks/class01.ipynb` |
| Demostración de fuentes | `examples/class01_acquisition/comparar_fuentes.py` |
| Videojuego | `examples/class01_acquisition/game/histograma_de_sprites.py` |
| Mecatrónica | `examples/class01_acquisition/mechatronics/aceptacion_de_toma.py` |
| Industrial | `examples/class01_acquisition/industrial/realce_de_pieza.py` |
| Solución del laboratorio | `solutions/clase01_solucion.py` |
| Datasets | `datasets/` (generar con `scripts/build_datasets.py`) |

---

## 8. Notas para el profesor

**Si no hay cámara en el aula.** No pasa nada y no hay que disimularlo:
`mejor_fuente_disponible` degrada a fuente del motor o sintética, y lo dice por
pantalla. Se aprovecha para señalar que un pipeline bien escrito no se entera
del cambio.

**Si el aula usa Windows.** La consola es cp1252. Que nadie imprima flechas
Unicode ni emoji: `UnicodeEncodeError` a mitad de la demostración cuesta diez
minutos y toda la atención.

**El error de bulto que hay que provocar.** Casi todos los grupos van a
concluir en T4 que «el estirado es el mejor» porque el histograma queda
precioso. La tabla de IoU dice que da igual. Dejar que lo escriban y que la
medición les corrija es la mitad de la clase — la otra mitad es explicar por
qué: **umbralizar es invariante a transformaciones monótonas**.

**Ritmo.** Si el tiempo aprieta, el recorte es T3, no T4. T4 es donde está la
idea que sostiene el resto del curso.
