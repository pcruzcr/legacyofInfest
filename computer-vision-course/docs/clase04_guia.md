# Clase 4 — Reconocimiento de patrones: de características a decisiones

**Duración:** 4 h · **Unidad IX** · **Grupos de 3** en el laboratorio

> **Pregunta que responde esta clase:**
> *¿Cómo convierto una tabla de medidas en una decisión?*

---

## 1. Objetivos

Al terminar, el estudiante debe ser capaz de:

1. Leer la *accuracy* **junto con la línea base**: un modelo que da 0,60 sobre
   un dataset donde «decir siempre OK» acierta 0,58 está aprendiendo; uno que
   da 0,50 no lo está.
2. Entrenar y comparar cinco modelos (kNN, árbol, bosque, SVM, regresión
   logística) con una partición **honesta**: train/test estratificada, semilla
   fija, nunca los mismos datos para entrenar y medir.
3. Leer la **matriz de confusión por celdas**, no por diagonal: en inspección
   industrial un falso negativo (pieza mala que pasa) cuesta más que un falso
   positivo (pieza buena rechazada), y el modelo se elige con esas dos celdas.
4. Distinguir **qué entra** al modelo: 9 características medidas contra 1.024
   píxeles crudos, y por qué en este dataset las primeras ganan — y saber que
   en otro dataset puede ser al revés.
5. Reconocer el **sobreajuste** por la curva train/test, no por intuición:
   cuando train acierta 1.000 y test cae, el modelo memorizó.
6. **Desplegar** un modelo: guardarlo a fichero, cargarlo en otro proceso y
   clasificar sin reentrenar.

## 2. Competencias

| Competencia | Cómo se evidencia |
|---|---|
| Validación honesta | La partición está estratificada, con semilla fija, y la *accuracy* se reporta con la línea base al lado |
| Comparación de modelos | Cinco modelos, una tabla con una métrica por columna, y una frase de elección que cita la tabla |
| Lectura de la matriz | El modelo elegido se justifica por las celdas que importan (FN vs. FP), no por la diagonal |
| Entrada vs. modelo | Distingue «qué números entran» de «qué modelo los consume», y explica la diferencia con cifras |
| Sobreajuste medido | La curva train/test demuestra la memorización con números, no «a ojo» |
| Despliegue | El modelo guardado y recargado clasifica datos que no entrenaron |

## 3. Prerrequisitos

Clase 3 terminada: la entrada de esta clase es `features.csv` (o un lote
medido con `cvcourse.features`). Las columnas ya tienen significado antes de
que exista modelo alguno — esa lectura previa es lo que permite interpretar
los resultados.

scikit-learn viene instalado con el entorno del motor; no hace falta nada
nuevo para las partes A/B. PyTorch y YOLO (partes C/D, `COURSE_ARCHITECTURE.md`
§5.2) se usan sólo en Google Colab a propósito.

Comprobación de entorno (2 minutos, al principio de la clase):

```bash
python -m pytest computer-vision-course/tests -q
```

---

## 4. Guion de la sesión

### Bloque 1 — Teoría aplicada · 50 min

| min | Contenido | Apoyo |
|---|---|---|
| 0–10 | De la tabla a la decisión: qué es un clasificador. La línea base como cota mínima | pizarra |
| 10–20 | Partición train/test estratificada y semilla: por qué medir sobre los datos de entrenamiento miente | pizarra |
| 20–30 | *Accuracy*, precisión, recall, f1: qué responde cada una. La matriz de confusión por celdas | pizarra |
| 30–40 | El coste de cada error según el contexto: FN vs. FP en inspección industrial | pizarra |
| 40–50 | Sobreajuste: por qué un árbol con 10 ejemplos da train 1.000. Qué es desplegar un modelo | pizarra |

Las tres ideas que tienen que quedar, en este orden:

1. **La *accuracy* sola no dice nada: se lee contra la línea base.** «Decir
   siempre la clase mayoritaria» es un modelo; todo modelo se compara con él.
2. **El número que vale es el que se midió con datos que el modelo no vio.**
   Entrenar y medir con lo mismo es un error de método: el árbol con las 9
   características da 1.000 sobre los datos que ya vio y 0,72 sobre los que
   no. Esa pareja es el sobreajuste, y se cita con esos dos números.
3. **La matriz se lee por celdas y el coste lo pone el problema, no la
   métrica.** El modelo que se lleva a la planta se elige con las dos celdas
   que importan, y la *accuracy* se queda para el resumen.

### Bloque 2 — Demostración del profesor · 40 min

Se ejecutan los cuatro ejemplos, en este orden, comentando la salida:

```bash
python examples/class04_ml_dl/industrial/clasificar_piezas.py
python examples/class04_ml_dl/game/clasificar_entidades.py
python examples/class04_ml_dl/mechatronics/detectar_y_localizar.py
python examples/class04_ml_dl/data_analysis/comparar_modelos.py
```

**Momentos que no hay que dejar pasar:**

- En `clasificar_piezas.py`, la línea base «siempre OK» es 0,576 y el peor
  modelo de la tabla da 0,921: **ningún número de la tabla significa nada sin
  la primera línea**. El bosque da 1.000 pero el KNN deja escapar una `mota`
  sobre círculo — el único defecto que no deja huella en las 9 medidas — y
  eso es exactamente lo que la matriz muestra y la *accuracy* esconde.
- En `clasificar_entidades.py`, 385 sprites del motor se clasifican con acc
  1.000 (árbol, bosque, SVM) y el KNN falla en los enemigos más pequeños: los
  fotogramas de 10 px de alto de la zona 1 (acc de enemigos 0,972). El tamaño
  separa las clases, y el problema es fácil *para este dataset*; la clase
  consiste en verlo medido y en no esperarse otro dataset igual. El modelo
  elegido para desplegar es el más rápido entre los que aciertan todo (árbol,
  0,37 ms por clasificación), se guarda a `.pkl` y se recarga en el mismo
  ejemplo para clasificar **sprites que no entrenaron**.
- En `detectar_y_localizar.py`, el pipeline entero encadena visión (umbral y
  regiones), patrones (el KNN entrenado sobre 125 filas de piezas, acc 0,974
  en test) y metrología (82 px = 60 mm → 0,7317 mm/px): 4/4 piezas
  clasificadas bien y localizadas dentro del píxel de su centroide. El modelo
  solo no agarra piezas; el modelo + la calibración sí.
- En `comparar_modelos.py`, el mismo problema con dos entradas: con las 9
  características de la Clase 3 todos los modelos dan 1.000; con los píxeles
  crudos (1.024 números) el mejor da 0,861. **Más números no es más
  información.** Y la curva de sobreajuste del árbol lo muestra con 84
  ejemplos: train 1.000, test 0,722.

### Bloque 3 — Laboratorio · 110 min

Ver §5. Grupos de 3, roles rotatorios cada 35 min: **teclado**, **notas**,
**verificación**.

### Bloque 4 — Cierre · 40 min

- Cada grupo enseña una figura y **una cifra** que la respalde (10 min).
- Puesta en común de las preguntas de análisis (§5.4).
- Anticipo de la Clase 5: *¿qué pasa cuando el tamaño ya no separa — piezas
  del mismo tamaño con defectos distintos — o cuando el fondo es ruidoso?*
  Eso ya no lo responde scikit-learn con 120 piezas; para eso están las redes
  y los datos grandes, en Colab (partes C/D).

---

## 5. Laboratorio

### 5.1 Entregable

Una carpeta `entrega_clase04_<apellidos>/` con:

| Fichero | Contenido |
|---|---|
| `lab04.ipynb` o `lab04.py` | El código que produce todo lo demás |
| `figuras/` | Las figuras generadas |
| `tabla_modelos.csv` | La comparativa: una fila por modelo, con partición y semilla en el nombre o en el encabezado |
| `analisis.md` | Máximo 2 páginas. Respuestas de §5.4, con cifras |

### 5.2 Tareas

**T1 — Línea base y partición honesta (20 min).**
Sobre el lote de `synthetic_parts` (o `features.csv` si se reutiliza el de la
Clase 3): calcular la línea base «siempre la clase mayoritaria» y partir
70/30 estratificado con semilla fija. Reportar cuántos ejemplos quedan en
cada parte y por clase. **Antes de entrenar nada**, escribir una frase sobre
qué significaría un modelo con *accuracy* por debajo de esa línea base.

**T2 — Cinco modelos, una tabla (30 min).**
Entrenar kNN, árbol, bosque, SVM y regresión logística con las 9
características de la Clase 3 y la misma partición de T1. Guardar
`tabla_modelos.csv` con `accuracy`, `precision`, `recall`, `f1` y tiempos
(entrenamiento e inferencia). Elegir un modelo con una frase que cite la
tabla —no el que «se ve mejor», el que la tabla sostiene—.
**T3 — La matriz por celdas (25 min).**
Para el modelo elegido en T2 y para el KNN, imprimir la matriz de confusión
(y guardarla como figura). Marcar la celda FN y la celda FP y escribir qué
cuesta cada una en una línea de inspección industrial: pieza mala que pasa vs.
pieza buena rechazada. ¿Cambiaría la elección del modelo si la planta dijera
«prefiero parar la línea dos veces al día antes que dejar pasar una pieza»?
Responder con las celdas de sus matrices, no con la *accuracy*.

**T4 — La misma decisión con otra entrada: píxeles crudos (20 min).**
Repetir T1+T2 sobre los mismos 120 ejemplos pero con la imagen reshapeada a
32×32 gris aplanada (1.024 números). Comparar la mejor *accuracy* de las dos
entradas y escribir la frase de la elección con las dos cifras.

**T5 — Sobreajuste con tren (15 min).**
Sobre las 9 características: entrenar el árbol con 10, 20, 40 y 84 ejemplos
(un subconjunto creciente del train con la misma semilla) y reportar
`acc_train` y `acc_test` en cada fila. Buscar la fila donde más se separan y
explicar qué le pasó al modelo en esa fila.

### 5.3 Reto (opcional, para quien termine)

Reproducir el despliegue del ejemplo del motor: guardar el modelo elegido en
T2 con `PatternRecognitionTools.save_model`, abrir **otro proceso Python**,
cargarlo con `load_model` y clasificar los sprites `player_short_attack_02`,
`enemy_shoot_zone3_03` y `enemy_zone3_die_05` del dataset — que no entrenaron.
Reportar las tres predicciones y las tres probabilidades.

### 5.4 Preguntas de análisis

Se responden en `analisis.md`, cada una con una cifra o una figura detrás.

1. En T1, ¿cuánto da la línea base y qué significaría un modelo con 0,50?
   ¿Y uno con la misma *accuracy* pero por debajo en recall de la clase
   minoritaria?
2. En T2, ¿por qué todos los modelos dan resultados parecidos sobre las 9
   características de las piezas? ¿Qué columna de la Clase 3 sospechan que
   separa sola, y cómo lo comprueban sin entrenar?
3. En T3, ¿qué defecto se escapó (si alguno) y por qué? ¿En qué medida está
   la huella que faltó? Cítenla con números.
4. En T4, ¿por qué empeoraron los modelos al darles 1.024 números en vez de
   9? ¿Qué información tenían los 9 y no tenían los 1.024?
5. En T5, ¿en qué fila está el sobreajuste y cómo se ve en la pareja
   `acc_train`/`acc_test`? ¿Qué cambiarían para que el árbol de esa fila
   generalizara?

---

## 6. Criterios de evaluación

Sobre 100. Es la rúbrica de laboratorio, alineada con
`docs/27_ACADEMIC_RUBRICS.md` §3 del repositorio del motor.

| Criterio | Puntos | Se consigue si… |
|---|---|---|
| **Validación honesta** | 15 | La partición es estratificada, con semilla fija, y la línea base aparece junto a la *accuracy* |
| **Comparativa** | 20 | Cinco modelos, `tabla_modelos.csv` completo y la elección se justifica citando la tabla |
| **Matriz por celdas** | 25 | FN y FP están identificados con su coste industrial y la elección final se argumenta con esas celdas |
| **Entrada vs. modelo** | 15 | Las dos entradas (9 vs. 1.024) se comparan con cifras y la diferencia se explica |
| **Sobreajuste** | 10 | La fila de la curva train/test donde más se separan está identificada y explicada |
| **Reproducibilidad** | 10 | Semillas fijas, rutas relativas, se ejecuta de principio a fin |
| **Comunicación** | 5 | `analisis.md` cabe en 2 páginas y se entiende |

**Penalizaciones:**

- −10 si `analisis.md` afirma algo que su propio código contradice.
- −10 si el modelo «elegido» no es el que su propia tabla sostiene.
- −10 si las figuras no llevan título o no se sabe qué imagen es cuál.
- −5 por cada ruta absoluta (`C:\Users\...`) en el código entregado.

**Lo que NO se evalúa:** que la *accuracy* sea 1.000, ni que el modelo sea
«el mejor». Se evalúa que cada número esté **medido en su propia ejecución**
y que cada decisión esté **sostenida por un número**.

---

## 7. Material

| Recurso | Ruta |
|---|---|
| Notebook de laboratorio | `notebooks/class04.ipynb` |
| Partes C y D (PyTorch, YOLO, Colab) | `notebooks/class04_colab.ipynb` |
| Industrial (matriz y línea base) | `examples/class04_ml_dl/industrial/clasificar_piezas.py` |
| Videojuego (despliegue) | `examples/class04_ml_dl/game/clasificar_entidades.py` |
| Mecatrónica (pipeline completo) | `examples/class04_ml_dl/mechatronics/detectar_y_localizar.py` |
| Data analytics (entradas y sobreajuste) | `examples/class04_ml_dl/data_analysis/comparar_modelos.py` |
| Solución del laboratorio | `solutions/clase04_solucion.py` |
| Modelos y métricas (framework) | `src/framework/processing/pattern_recognition_tools.py` del motor |
| Datasets | `datasets/` (generar con `scripts/build_datasets.py`) |

---

## 8. Notas para el profesor

**Si el aula usa Windows.** La consola es cp1252. Que nadie imprima flechas
Unicode ni emoji: `UnicodeEncodeError` a mitad de la demostración cuesta diez
minutos y toda la atención. Los ejemplos y la solución están verificados en
ASCII puro.

**El error de bulto que hay que provocar.** Que un grupo declare «el mejor
modelo» mirando sólo la *accuracy* de la tabla. La pregunta correcta que
tienen que poder responder es *¿y si en la planta una pieza mala que pasa
cuesta 20 veces más que una buena rechazada?* — la respuesta está en las
celdas de la matriz, y eso es lo que se califica, no la diagonal.

**El otro error de bulto.** Cambiar la semilla «hasta que salga mejor».
La partición con semilla fija existe para que la comparación sea honesta
entre grupos y entre modelos. Si un grupo mueve la semilla, su tabla miente
sobre los demás.

**El puente a la Clase 5.** Todo lo de esta clase funciona porque el tamaño
separa las clases con 120 piezas limpias. Cuando los objetos se parezcan en
tamaño y forma (el mismo tornillo con dos texturas) o el fondo tenga
desorden, las 9 características se caen y los píxeles no suben ni con
1.024 números: ahí entran las redes (parte C, Colab) y los detectores
(parte D, YOLO). Lo que la Clase 4 deja instalado es el método: línea base,
partición, matriz y sobreajuste se exigen igual delante de una CNN.

**Ritmo.** Si el tiempo aprieta, el recorte es T4, no T3. La matriz por
celdas (T3) es donde está la idea que sostiene la decisión industrial; la
comparación con píxeles crudos (T4) se puede dejar como lectura del ejemplo
`comparar_modelos.py`.
