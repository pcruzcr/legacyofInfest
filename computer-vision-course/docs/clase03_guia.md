# Clase 3 — Segmentación y extracción de características

**Duración:** 4 h · **Unidad VIII** · **Grupos de 3** en el laboratorio

> **Pregunta que responde esta clase:**
> *¿Cómo paso de píxeles a objetos medidos?*

---

## 1. Objetivos

Al terminar, el estudiante debe ser capaz de:

1. Decidir **cuándo** un umbral fijo alcanza, cuándo hace falta Otsu y cuándo
   ninguno de los dos basta (el caso de las piezas que se tocan).
2. Usar erosión, dilatación, apertura y cierre para limpiar una máscara, y
   **medir** el efecto con la cuenta de objetos y no a ojo.
3. Contar objetos con componentes conexas y distinguir contorno, centroide y
   bounding box, sabiendo qué pregunta responde cada uno.
4. Aplicar watershed para separar objetos que se tocan, y validar el resultado
   contra una verdad-terreno.
5. Convertir una máscara en una tabla de números (`features.csv`) con área,
   perímetro, ancho, alto, relación de aspecto y circularidad, y **leer esas
   distribuciones** —sin entrenar nada.

## 2. Competencias

| Competencia | Cómo se evidencia |
|---|---|
| Selección de técnica | Elige umbral fijo, Otsu o watershed con la justificación de qué falla en cada caso |
| Medición de morfología | La apertura «funcionó» porque la cuenta de objetos bajó, no porque se vea más limpio |
| Conteo y localización | Separa «cuántos objetos hay» (componentes conexas) de «dónde está cada uno» (centroide/bbox) |
| Validación contra verdad | El watershed acertó porque sus centroides coinciden con la verdad dentro de un margen, no porque «se vea bien» |
| Puente a datos | Produce un CSV reproducible y describe sus distribuciones con números |

## 3. Prerrequisitos

Clase 2 terminada: el material de entrada de esta clase son los bordes y
máscaras que allí se limpiaron. La cuenta de **islas** de la Clase 2 era ya
una segmentación primitiva; esta clase la completa.

Comprobación de entorno (2 minutos, al principio de la clase):

```bash
python -m pytest computer-vision-course/tests -q
```

---

## 4. Guion de la sesión

### Bloque 1 — Teoría aplicada · 50 min

| min | Contenido | Apoyo |
|---|---|---|
| 0–10 | De la máscara al objeto: umbral fijo, Otsu, umbral adaptativo. Qué falla en cada caso | pizarra |
| 10–20 | Morfología: erosión, dilatación, apertura, cierre. Para qué sirve cada una | pizarra |
| 20–30 | Componentes conexas: qué significa la conectividad. Contorno vs. centroide vs. bbox | pizarra |
| 30–40 | El caso que rompe todo: objetos que se tocan. Watershed y la transformada de distancia | pizarra |
| 40–50 | De objetos a números: área, perímetro, relación de aspecto, circularidad. Por qué importan | pizarra |

Las tres ideas que tienen que quedar, en este orden:

1. **Contar objetos y separarlos son problemas distintos.** El umbral responde
   «¿dónde hay objeto?»; las componentes conexas responden «¿cuántos?»; y
   cuando dos objetos se tocan, las componentes conexas mienten: cuenta 1
   donde hay 5. Por eso existe el watershed.
2. **La morfología se mide con la tarea.** «Cuántas componentes quedan» es la
   medida; «se ve mejor» no lo es.
3. **La Clase 3 no entrena.** Produce una tabla y la mira. El modelo llega en
   la Clase 4, y necesita saber qué significan las columnas antes de tocar
   una.

### Bloque 2 — Demostración del profesor · 40 min

Se ejecutan los cuatro ejemplos, en este orden, comentando la salida:

```bash
python examples/class03_segmentation/game/separar_entidades.py
python examples/class03_segmentation/manufacturing/watershed_piezas.py
python examples/class03_segmentation/mechatronics/contorno_y_centroide.py
python examples/class03_segmentation/data_analysis/features_csv.py
```

**Momentos que no hay que dejar pasar:**

- En `separar_entidades.py`, tres sprites reales del motor sobre fondo claro
  se convierten en **3 entidades** con umbral + componentes conexas, y la
  cuenta coincide con lo que se colocó. El sprite se separa del fondo usando
  lo aprendido: el fondo es el que no satisface el umbral. Y la morfología
  «por si acaso» se mide antes de usarse: aquí no hay motas que limpiar (0
  componentes pequeñas) y la apertura 3×3 **fragmenta** al jefe (3 → 7
  componentes). El momento es deliberado: la morfología se decide mirando la
  máscara, y su coste va en la misma tabla que su beneficio.
- En `watershed_piezas.py`, el umbral —Otsu incluido— produce **una** mancha
  de 10.657 px donde hay 5 piezas. Es la demostración central: counting y
  separación no son lo mismo. El watershed vuelve a encontrar las 5, con un
  error medio de centroide de 3 px y un máximo de 6.
- En `contorno_y_centroide.py`, contorno, centroide y bbox son **tres
  respuestas distintas**: 322 px de contorno, 0,7 px de error de centroide y
  una caja de 82×82. La calibración píxel→mm convierte (63,5, 63,5) px en
  (46,5, 46,5) mm con una referencia de 60 mm.
- En `features_csv.py`, la máscara de cada pieza termina como una **fila** de
  la tabla: `features.csv` se produce y se mira. No hay modelo aquí, y que no
  lo haya es el punto.

### Bloque 3 — Laboratorio · 110 min

Ver §5. Grupos de 3, roles rotatorios cada 35 min: **teclado**, **notas**,
**verificación**.

### Bloque 4 — Cierre · 40 min

- Cada grupo enseña una figura y **una cifra** que la respalde (10 min).
- Puesta en común de las preguntas de análisis (§5.4).
- Anticipo de la Clase 4: *estas columnas son la entrada de un modelo — ¿cuál
  de ellas sirve para distinguir una pieza mala de una buena?* — eso ya no lo
  responde la vista.

---

## 5. Laboratorio

### 5.1 Entregable

Una carpeta `entrega_clase03_<apellidos>/` con:

| Fichero | Contenido |
|---|---|
| `lab03.ipynb` o `lab03.py` | El código que produce todo lo demás |
| `figuras/` | Las figuras generadas |
| `features.csv` | El CSV producido: 13 columnas, ninguna fila vacía |
| `analisis.md` | Máximo 2 páginas. Respuestas de §5.4, con cifras |

### 5.2 Tareas

**T1 — Umbral y Otsu sobre una pieza individual (25 min).**
Tomar `pieza_individual` (rectángulo y círculo) y comparar: umbral fijo,
umbral elegido a ojo, y Otsu. Medir contra la máscara de la verdad-terreno
(IoU o área). El círculo debe salir con exactitud esperable: el área medida
de un círculo de radio 41 px es 5.261 px frente a los 5.281 teóricos:
el 0,4 % de diferencia lo pone la discretización, no el algoritmo.

**T2 — Morfología medida (30 min).**
Añadir sal y pimienta a una pieza y umbralizar: la máscara sale picoteada.
Aplicar apertura y cierre con discos de radio 1, 2 y 3, y reportar **cuántas
componentes conexas** quedan en cada caso y qué fracción del área de la pieza
se conserva. Elegir el radio con una frase que cite esas cifras.

**T3 — Watershed sobre piezas que se tocan (30 min).**
Cargar `piezas_en_contacto` (5 piezas, radio 27 px, en cadena vertical).
Demostrar primero que el umbral miente: una sola componente conexa de 10.657
px. Después, el watershed: suavizar → Otsu → distancia → marcadores (umbral
sobre la distancia) → watershed. Reportar cuántas regiones salen y el error
del centroide de cada una contra la verdad (en el dataset de referencia, el
error medio queda en 3 px y el máximo en 6). La clave que hay que explicar:
el umbral de marcadores tiene que **pasar el valle del eje medio**
(√(r² − (paso/2)²) ≈ 15 px en este dataset), o las 5 piezas vuelven a
fundirse en una.

**T4 — De la máscara a `features.csv` (25 min).**
Con `cvcourse.features` (o `regionprops`), construir `features.csv` para un
lote de piezas (p. ej. 30). Reportar: distribución de `area`,
`aspect_ratio` y `circularity`, separando por clase. **No entrenar nada.**
El objetivo es poder decir qué separa una clase de otra con un número antes
de que exista modelo alguno.

### 5.3 Reto (opcional, para quien termine)

`VisionDemoScene` del motor demuestra los modos THRESHOLD → ERODE/DILATE →
COMPONENTS → REGIONS en vivo. Reproducir la misma cadena sobre un fotograma
capturado del motor (`engine_bridge.capturar_escena("vision")`), con el
mismo orden de modos, y reportar cómo cambia la cuenta de componentes al
pasar de una máscara recién umbralizada a la versión limpiada.

### 5.4 Preguntas de análisis

Se responden en `analisis.md`, cada una con una cifra o una figura detrás.

1. En T1, ¿por qué Otsu no da exactamente la máscara de la verdad? ¿Es un
   error del umbral o de la discretización? Cítenlo con números.
2. En T2, la apertura quitó motas. ¿Qué motas le son imposibles de quitar sin
   comerse la pieza? ¿Cómo lo saben con las cifras de las componentes?
3. En T3, ¿qué le pasaría al watershed si el umbral de marcadores fuera la
   mitad? Expliquen el porqué con el valle del eje medio.
4. En T4, ¿qué columna separa mejor las clases que ven? ¿Cómo lo medirían
   sin entrenar un modelo?
5. Cuenten, con cifras de su laboratorio, una escena en la que el umbral solo
   fue suficiente y una en la que no. ¿Qué decidió la diferencia?

---

## 6. Criterios de evaluación

Sobre 100. Es la rúbrica de laboratorio, alineada con
`docs/27_ACADEMIC_RUBRICS.md` §3 del repositorio del motor.

| Criterio | Puntos | Se consigue si… |
|---|---|---|
| **Umbral selectivo** | 15 | Eligen fijo/Otsu/adaptativo con justificación de qué falla en cada caso |
| **Morfología medida** | 20 | El radio de T2 está elegido con cifras de componentes y de área conservada |
| **Watershed validado** | 25 | El error de centroide contra la verdad está reportado y el valle del eje medio explicado |
| **Características** | 20 | `features.csv` tiene las 13 columnas, ninguna fila vacía, y las distribuciones están comentadas con números |
| **Reproducibilidad** | 10 | Semillas fijas, rutas relativas, se ejecuta de principio a fin |
| **Comunicación** | 10 | `analisis.md` cabe en 2 páginas y se entiende |

**Penalizaciones:**

- −10 si `analisis.md` afirma algo que su propio código contradice.
- −10 si `features.csv` contiene filas vacías o columnas renombradas sin
  aviso (la Clase 4 las consume por nombre).
- −10 si las figuras no llevan título o no se sabe qué imagen es cuál.
- −5 por cada ruta absoluta (`C:\Users\...`) en el código entregado.

**Lo que NO se evalúa:** que las máscaras «queden perfectas», ni que el
watershed sea «el mejor algoritmo». Se evalúa que cada elección esté
**medida y validada** contra una verdad.

---

## 7. Material

| Recurso | Ruta |
|---|---|
| Notebook de laboratorio | `notebooks/class03.ipynb` |
| Videojuego | `examples/class03_segmentation/game/separar_entidades.py` |
| Manufactura (watershed) | `examples/class03_segmentation/manufacturing/watershed_piezas.py` |
| Mecatrónica (contorno y calibración) | `examples/class03_segmentation/mechatronics/contorno_y_centroide.py` |
| Data analytics | `examples/class03_segmentation/data_analysis/features_csv.py` |
| Solución del laboratorio | `solutions/clase03_solucion.py` |
| Generador sintético (verdad-terreno) | `cvcourse/synthetic.py` |
| `features.csv` (clase) | `cvcourse/features.py` |
| Datasets | `datasets/` (generar con `scripts/build_datasets.py`) |

---

## 8. Notas para el profesor

**Si el aula usa Windows.** La consola es cp1252. Que nadie imprima flechas
Unicode ni emoji: `UnicodeEncodeError` a mitad de la demostración cuesta diez
minutos y toda la atención. Los ejemplos y la solución están verificados en
ASCII puro.

**El error de bulto que hay que provocar.** Casi todos los grupos van a
concluir en T3 que «el umbral no sirvió» y que el watershed «hace magia».
Ninguna de las dos frases es la clase: el umbral respondió bien a su pregunta
(dónde hay objeto) y el watershed respondió la suya (cuántos objetos hay).
La pregunta que nadie se hace en serio la primera vez es *¿por qué 5
marcadores y no 4?* — la respuesta es el valle del eje medio, y está en la
tabla de 15 px.

**El puente a la Clase 4.** El `features.csv` de T4 se lee con pandas, se
grafica y **no se entrena**. Si algún grupo «prueba un KNN rápido», cortarlo
amablemente: la Clase 4 tiene su propio material sobre por qué eso engaña
(validación, sobreajuste). Que la tentación aparezca es buena señal — es la
pregunta de la siguiente clase.

**Ritmo.** Si el tiempo aprieta, el recorte es T1, no T3. T3 (y su medición
contra la verdad) es donde está la idea que sostiene la Clase 4: sin
verdad-terreno, ningún número del pipeline significa nada.