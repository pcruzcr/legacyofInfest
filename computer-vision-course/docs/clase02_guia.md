# Clase 2 — Filtrado, convolución, ruido y bordes

**Duración:** 4 h · **Unidad VII** (segunda parte) · **Grupos de 3** en el laboratorio

> **Pregunta que responde esta clase:**
> *¿Cómo limpio una imagen y cómo encuentro su estructura?*

---

## 1. Objetivos

Al terminar, el estudiante debe ser capaz de:

1. Distinguir ruido gaussiano de sal y pimienta, y **elegir el filtro** con un
   criterio medible, no por fama.
2. Explicar qué es un kernel y qué hace la convolución, y escribir un kernel
   propio en NumPy.
3. Calcular el gradiente de una imagen y aplicar Sobel y Canny, explicando qué
   hace cada una de las cuatro etapas de Canny.
4. **Romper un pipeline a propósito** (subir el umbral de Canny) y explicar con
   cifras por qué el resultado dejó de servir.
5. Medir el rendimiento de una convolución en NumPy puro, OpenCV y Numba, y
   decir cuándo importa.

## 2. Competencias

| Competencia | Cómo se evidencia |
|---|---|
| Modelado del ruido | Predice qué filtro va a ganar en cada columna de ruido **antes** de medir, y la medición le da la razón o se la quita con explicación |
| Implementación propia | Su `convolucionar` (NumPy puro) produce resultados indistinguibles de `cv2.filter2D` |
| Diagnóstico de resultado | Justifica «este kernel detectó la grieta» con una correlación, no con la impresión visual |
| Ingeniería de pipeline | Explica el *trade-off* de cada umbral de Canny con cifras (islas, píxeles, coherencia) |
| Rendimiento | Cronometra las implementaciones sobre la misma imagen y explica la diferencia en términos de operaciones por píxel |

## 3. Prerrequisitos

Clase 1 terminada (histograma como criterio). NumPy a nivel de *slicing*.

Comprobación de entorno (2 minutos, al principio de la clase):

```bash
python -m pytest computer-vision-course/tests -q
```

---

## 4. Guion de la sesión

### Bloque 1 — Teoría aplicada · 50 min

| min | Contenido | Apoyo |
|---|---|---|
| 0–10 | Ruido gaussiano vs. sal y pimienta. Por qué la mediana gana con sal y pimienta (teoría de estadística de orden) | pizarra |
| 10–20 | Kernel, vecindario, convolución vs. correlación. Coste por píxel | pizarra |
| 20–30 | Derivada discreta, gradiente, Sobel. La dirección del gradiente | pizarra |
| 30–40 | Canny etapa por etapa: suavizar → gradiente → supresión de no-máximos → histéresis | `edge_detection.py` en vivo |
| 40–50 | El papel de los dos umbrales de histéresis. Qué pasa si subes el alto | pizarra |

Las tres ideas que tienen que quedar, en este orden:

1. **El ruido decide el filtro, no la fama del filtro.** La mediana no es «el
   mejor filtro»: es el que sobrevive a los píxeles que son radicalmente
   distintos de sus vecinos. Si el ruido es gaussiano, el promedio o el
   gaussiano rinden igual de bien y son más baratos.
2. **La convolución es un producto por vecindario.** Todo lo demás —filtros,
   bordes, y más adelante capas convolucionales— son esa operación con otros
   números.
3. **Los umbrales son decisiones de ingeniería, no de estética.** Se eligen
   mirando qué pasa con la siguiente etapa, y se justifican con cifras.

### Bloque 2 — Demostración del profesor · 40 min

Se ejecutan los cinco ejemplos, en este orden, comentando la salida:

```bash
python examples/class02_processing/comparar_implementaciones.py
python examples/class02_processing/game/bordes_de_escena.py
python examples/class02_processing/industrial/superficie_con_defectos.py
python examples/class02_processing/mechatronics/preproceso_para_contorno.py
python examples/class02_processing/rendimiento_convolucion.py
```

**Momentos que no hay que dejar pasar:**

- En `comparar_implementaciones.py`, la mediana gana **también** en la columna
  de ruido gaussiano (3.6 vs. 6.8). La pieza es casi plana y el gaussiano no
  tiene a nadie a quien invocar; preguntar por qué antes de contarlo.
- En `bordes_de_escena.py`, el pipeline entero cabe en un fotograma de 16,6 ms
  y aún así no es el cuello de botella del juego. La visión barata deja
  presupuesto para la visión cara.
- En `preproceso_para_contorno.py`, «componentes» es la cuenta que va a
  heredar la Clase 3: con la mediana 5×5 son ~1-3; sin preprocesado, una por
  mota de ruido.
- En `rendimiento_convolucion.py`, la ganancia de Numba (≈27×) se mide con la
  misma imagen y el mismo kernel; la tabla lo dice y se puede repetir.

### Bloque 3 — Laboratorio · 110 min

Ver §5. Grupos de 3, roles rotatorios cada 35 min: **teclado**, **notas**,
**verificación**.

### Bloque 4 — Cierre · 40 min

- Cada grupo enseña una figura y **una cifra** que la respalde (10 min).
- Puesta en común de las preguntas de análisis (§5.4).
- Anticipo de la Clase 3: *estos bordes están limpios, pero ¿cuántos objetos
  hay en la imagen?* — el umbral solo no lo sabe; ahí entra la segmentación.

---

## 5. Laboratorio

### 5.1 Entregable

Una carpeta `entrega_clase02_<apellidos>/` con:

| Fichero | Contenido |
|---|---|
| `lab02.ipynb` o `lab02.py` | El código que produce todo lo demás |
| `figuras/` | Las figuras generadas |
| `analisis.md` | Máximo 2 páginas. Respuestas de §5.4, con cifras |

### 5.2 Tareas

**T1 — Ruido y filtros (25 min).**
Tomar una pieza sintética (`pieza_individual`) y añadirle ruido gaussiano y
sal y pimienta. Aplicar promedio, gaussiano y mediana. **Predecir el ganador
en cada columna antes de medir** y anotar la predicción. Medir con error
cuadrático medio contra la pieza limpia (o contra la verdad-terreno, si se
usan los `datasets`).

**T2 — Kernel propio (30 min).**
Escribir `convolucionar` en NumPy puro y verificar contra `cv2.filter2D`.
Diseñar un kernel direccional (p. ej. el de Sobel) y demostrar, con un número,
qué es lo que detecta: la correlación entre su respuesta y la grieta diagonal
de la pieza es alta para una dirección y baja para la otra. La referencia
«detecta todo» es el laplaciano.

**T3 — Canny, los dos umbrales (30 min).**
Sobre una pieza con grieta, correr Canny con cuatro parejas de umbrales.
Contar **islas** con componentes conexas (8-vecindad) y reportar el cambio:
con umbrales altos la banda queda vacía (0 bordes), con bajos el ruido
reventa la imagen (miles de islas), y con un alto demasiado bajo el ruido se
le engancha al borde (los píxeles del contorno crecen sin que el contorno
sea mejor). Buscar una configuración que deje **una** isla y medir cuánto
coincide con el borde de la verdad-terreno.

**T4 — Rendimiento (25 min).**
Sobre la misma imagen y el mismo kernel, cronometrar NumPy puro,
`cv2.filter2D` y Numba (si está instalado). Reportar la tabla de tiempos y la
aceleración relativa. Explicar la diferencia con una frase que mencione
operaciones por píxel y capas de optimización.

### 5.3 Reto (opcional, para quien termine)

El motor suaviza con `suavizar` (gaussiano separable: dos pasadas 1D). Medir
cuánto cuesta su convolución 2D equivalente frente a la separable, con kernels
de 3, 5, 7 y 9 de ancho, y reportar la razón. ¿En qué tamaño empieza a
compensar la separabilidad?

### 5.4 Preguntas de análisis

Se responden en `analisis.md`, cada una con una cifra o una figura detrás.

1. En T1, ¿acertaron la predicción? Si la mediana ganó también en la columna
   gaussiana, ¿por qué creen que pasó?
2. Su kernel direccional de T2: ¿qué dirección detecta, y cómo lo saben sin
   mirar la imagen?
3. En T3, ¿qué pareja de umbrales dejó la banda vacía y cuál reventó la
   imagen? ¿Qué le diría ese resultado a un sistema que elige umbrales a
   ciegas?
4. El rendimiento de T4: ¿por qué no es el cuello de botella de un juego a 60
   fps con una sola pieza, y en qué condiciones sí lo sería?
5. ¿Qué etapa de Canny se cargaría si subieran el umbral alto al máximo?
   ¿Cómo se nota en la cuenta de islas?

---

## 6. Criterios de evaluación

Sobre 100. Es la rúbrica de laboratorio, alineada con
`docs/27_ACADEMIC_RUBRICS.md` §3 del repositorio del motor.

| Criterio | Puntos | Se consigue si… |
|---|---|---|
| **Modelado del ruido** | 15 | Predicción anotada antes de medir; el análisis explica el acierto o el fallo |
| **Implementación propia** | 20 | `convolucionar` coincide con `cv2.filter2D` dentro de un umbral numérico explícito |
| **Kernel propio** | 20 | La dirección del kernel está demostrada con una correlación o métrica, no con una imagen |
| **Canny medido** | 20 | Reportan las cuatro parejas con su cuenta de islas y su coherencia contra la verdad |
| **Rendimiento** | 10 | Tabla de tiempos reproducible sobre la misma imagen |
| **Reproducibilidad** | 10 | Semillas fijas, rutas relativas, se ejecuta de principio a fin |
| **Comunicación** | 5 | `analisis.md` cabe en 2 páginas y se entiende |

**Penalizaciones:**

- −10 si `analisis.md` afirma algo que su propio código contradice.
- −10 si las figuras no llevan título o no se sabe qué imagen es cuál.
- −5 por cada ruta absoluta (`C:\Users\...`) en el código entregado.

**Lo que NO se evalúa:** que los bordes «se vean bonitos», ni que el filtro
elegido sea «el mejor». Se evalúa que la elección esté **medida y justificada**.

---

## 7. Material

| Recurso | Ruta |
|---|---|
| Notebook de laboratorio | `notebooks/class02.ipynb` |
| Implementaciones (Sobel/Canny propias) | `src/engine/edge_detection.py` |
| Demostración etapa por etapa | `examples/class02_processing/comparar_implementaciones.py` |
| Videojuego | `examples/class02_processing/game/bordes_de_escena.py` |
| Industrial | `examples/class02_processing/industrial/superficie_con_defectos.py` |
| Mecatrónica | `examples/class02_processing/mechatronics/preproceso_para_contorno.py` |
| Rendimiento | `examples/class02_processing/rendimiento_convolucion.py` |
| Solución del laboratorio | `solutions/clase02_solucion.py` |
| Datasets | `datasets/` (generar con `scripts/build_datasets.py`) |

---

## 8. Notas para el profesor

**Si el aula usa Windows.** La consola es cp1252. Que nadie imprima flechas
Unicode ni emoji: `UnicodeEncodeError` a mitad de la demostración cuesta diez
minutos y toda la atención. Los ejemplos y la solución están verificados en
ASCII puro.

**El error de bulto que hay que provocar.** Casi todos los grupos van a
concluir en T1 que «el gaussiano es el mejor filtro». En la pieza sintética
medida aquí la mediana le gana también en ruido gaussiano (3.6 vs. 6.8). Dejar
que lo escriban y que la medición les corrija es la mitad de la clase — la
otra mitad es explicar por qué: la mediana no es mejor, es **más robusta**, y
sobre una pieza casi plana no hay textura que el gaussiano pueda usar a favor.

**La tentación de «subir el umbral hasta que se vea bien».** Es exactamente lo
contrario de la clase: cada pareja de umbrales de T3 está documentada con su
cuenta de islas y su coherencia. Un sistema que elige umbrales a ciegas
produce la «banda vacía» del reto sin que nadie se dé cuenta.

**Ritmo.** Si el tiempo aprieta, el recorte es T4, no T3. T3 es donde está la
idea que sostiene la Clase 3: el resultado de la segmentación depende de las
decisiones tomadas aquí.
