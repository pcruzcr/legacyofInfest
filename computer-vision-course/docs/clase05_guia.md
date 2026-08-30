# Clase 5 — Integración: de ocho etapas a un sistema que decide

**Duración:** 4 h · **Proyecto de integración** · **Grupos de 3**

> **Pregunta que responde esta clase:**
> *¿Cómo se arma un sistema de visión completo —de la cámara a la decisión—
> encadenando lo de las clases 1 a 4, sin introducir nada nuevo?*

---

## 1. Objetivos

Al terminar, el estudiante debe ser capaz de:

1. **Recorrer la cadena completa** —ADQUISICIÓN → PREPROCESAMIENTO →
   SEGMENTACIÓN/DETECCIÓN → EXTRACCIÓN → ML/DL → ANÁLISIS → VISUALIZACIÓN →
   INTERACCIÓN— con un sistema que ejecuta de principio a fin, no con diapositivas.
2. **Explicar qué recibe y qué devuelve cada etapa** (el contrato entre etapas):
   la salida de la segmentación es la entrada de la extracción, y si la primera
   cambia, las siguientes se reentrenan o se reajustan.
3. **Medir el sistema como sistema**: el tiempo por etapa, el coste de cada
   error (FN vs. FP) y la cifra que decide — el número con el que el sistema
   justifica su propia existencia.
4. **Elegir un dominio y sostener la elección**: videojuego, mecatrónica,
   industrial, manufactura o análisis de datos; el material de las clases 1–4
   aporta la pieza que cada dominio necesita.
5. **Documentar decisiones de diseño con evidencia**: qué se cambió en una
   etapa y qué se midió en consecuencia — el mismo criterio que la Clase 4
   exigió a los modelos.
6. **Presentar el sistema en 5 minutos**: una figura y una cifra que la
   respalden, sin leer código en voz alta.

## 2. Competencias

| Competencia | Cómo se evidencia |
|---|---|
| Integración | Las ocho etapas ejecutan encadenadas en un solo programa, con datos que no entrenaron |
| Contrato entre etapas | Cada etapa declara su entrada y su salida, y el cambio de una etapa se propaga mediblemente a las demás |
| Medición de sistema | Una tabla de tiempos por etapa y una cifra de decisión (tasa de rechazo, piezas por minuto, acierto sobre fotograma) |
| Decisión por dominio | La elección del dominio se sostiene con el material de las clases anteriores, no con «es lo que tocaba» |
| Comunicación técnica | La presentación de cierre: una figura, una cifra, 5 minutos |

## 3. Prerrequisitos

Clases 1 a 4 terminadas. El material de esta clase **no introduce contenido
nuevo**: las ocho etapas ya se vieron, cada una en su clase. Lo nuevo es
encadenarlas y hacerlas trabajar juntas sobre un problema propio.

Comprobación de entorno (2 minutos, al principio de la clase):

```bash
python -m pytest computer-vision-course/tests -q
```

Deben existir los datasets generados (`scripts/build_datasets.py`) y el modelo
desplegado de la Clase 4 (`outputs/clase04/modelo_entidades.pkl`); el ejemplo
de videojuego lo usa si está, y si no lo reentrena con el mismo método.

---

## 4. Guion de la sesión

### Bloque 1 — Teoría aplicada · 30 min

| min | Contenido | Apoyo |
|---|---|---|
| 0–10 | La cadena como arquitectura: qué recibe y qué devuelve cada etapa. El contrato entre etapas | pizarra |
| 10–20 | Qué cambia al integrar: latencia por etapa, propagación de errores, decisiones con probabilidad y no con certeza | pizarra |
| 20–30 | Los cinco dominios y la pieza de cada uno: qué pregunta responde cada sistema y qué cifra lo decide | pizarra |

La idea que tiene que quedar:

1. **Integrar no es sumar bibliotecas: es encadenar contratos.** La salida de
   una etapa es la entrada de la siguiente. Si la segmentación empieza a
   entregar tres regiones donde había una, las etapas de abajo no se caen:
   miden tres piezas y las clasifican — mal o bien, pero sin avisar. El
   sistema entero se valida con la cifra final, y por eso cada etapa se mide.

### Bloque 2 — Demostración del profesor · 45 min

Se ejecutan los cinco sistemas de referencia, en este orden, comentando la
cadena de etapas de cada uno:

```bash
python examples/class05_integration/industrial/estacion_de_inspeccion.py
python examples/class05_integration/game/analizador_de_fotogramas.py
python examples/class05_integration/mechatronics/percepcion_pick_and_place.py
python examples/class05_integration/manufacturing/linea_de_conteo.py
python examples/class05_integration/data_analysis/panel_de_resultados.py
```

**Momentos que no hay que dejar pasar:**

- En `estacion_de_inspeccion.py`, la estación decide pieza por pieza con
  probabilidad, y la cifra de cierre es el coste del turno — la misma idea de
  FN/FP de la Clase 4, ahora acumulada en un reporte.
- En `analizador_de_fotogramas.py`, el sistema **captura un fotograma real del
  motor** (escena `vision`, headless) y lo clasifica con el modelo desplegado
  de la Clase 4: es la Clase 4 reutilizada como pieza, sin reentrenar el método.
- En `percepcion_pick_and_place.py`, la cadena termina en una **acción**: un
  orden de agarre con coordenadas en milímetros. El pipeline no clasifica para
  informar: clasifica para agarrar.
- En `linea_de_conteo.py`, el watershed de la Clase 3 hace de etapa de
  segmentación dentro de un sistema que además cuenta y clasifica: la pieza de
  la Clase 3 insertada donde le toca.
- En `panel_de_resultados.py`, el sistema «adquiere» del CSV de la Clase 3 y
  de los lotes, y su interacción es el reporte escrito: las cifras que deciden.

### Bloque 3 — Laboratorio · 135 min

Ver §5. Grupos de 3, roles rotatorios cada 40 min: **teclado**, **notas**,
**verificación**. Cada grupo elige UN dominio y construye SU sistema.

### Bloque 4 — Cierre · 30 min

- Cada grupo corre su sistema delante de todos (sin pantalla, salida de
  consola) y presenta **una figura y una cifra** (3 min + 2 de preguntas).
- Puesta en común: qué etapa fue la más cara de integrar y qué se midió al
  cambiarla.

---

## 5. Proyecto

### 5.1 Entregable

Una carpeta `proyecto_clase05_<apellidos>/` con:

| Fichero | Contenido |
|---|---|
| `main.py` | El sistema completo, de la adquisición a la interacción, ejecutable de principio a fin |
| `figuras/` | Las figuras del sistema (etapas intermedias + la figura que se presenta) |
| `resultados.txt` | La salida de una ejecución completa, sin editar |
| `analisis.md` | Máximo 2 páginas. Respuestas de §5.4, con cifras |

### 5.2 Arquitectura obligatoria

El sistema **recorre la cadena completa**, en este orden y con estas
responsabilidades:

```
ADQUISICIÓN → PREPROCESAMIENTO → SEGMENTACIÓN/DETECCIÓN → EXTRACCIÓN
            → ML/DL → ANÁLISIS → VISUALIZACIÓN → INTERACCIÓN
```

| Etapa | Recibe | Devuelve | Medición mínima |
|---|---|---|---|
| 1. Adquisición | fuente (cámara, fichero, motor, generador) | imagen | resolución, tiempo de captura |
| 2. Preprocesamiento | imagen | imagen limpia | tiempo de etapa |
| 3. Segmentación/detección | imagen limpia | máscara / regiones | nº de regiones vs. esperado |
| 4. Extracción | regiones | tabla de características | nº de filas, columnas usadas |
| 5. ML/DL | características | predicción + probabilidad | accuracy contra línea base |
| 6. Análisis | predicciones | decisión + su coste | FN/FP del sistema, cifra que decide |
| 7. Visualización | etapas | figuras | las figuras existen y dicen qué son |
| 8. Interacción | decisión | acción o reporte | la acción es reproducible |

### 5.3 Tareas

**T1 — Dominio y fuente (10 min).** Elegir dominio de la tabla de §7 (o
proponer uno propio con la misma arquitectura) y justificar la fuente: por qué
los datos de ese dominio entran por esa puerta.

**T2 — Esqueleto de 8 etapas (25 min).** Escribir las ocho funciones con sus
contratos (entrada/salida) y un `main()` que las encadene. **Antes de llenar
nada**, correrlo con datos mínimos: debe imprimir las ocho etapas y terminar.

**T3 — Adquisición + preprocesamiento (20 min).** Implementar las dos primeras
etapas con el material de las Clases 1 y 2, y medir: qué tamaño tiene la
imagen que entra, qué tiempo cuesta, por qué ese preprocesamiento (cita una
figura o un número de la Clase 2).

**T4 — Segmentación/detección + extracción (25 min).** Implementar con el
material de la Clase 3 (umbral, morfología, componentes conexas, watershed,
características geométricas) y medir: cuántas regiones salen, cuántas se
descartan por área mínima, cuántas filas entran a la tabla.

**T5 — Modelo (25 min).** Entrenar con el material de la Clase 4: partición
honesta con semilla fija, línea base, accuracy sobre datos que no entrenaron.
El modelo se justifica por sus celdas (FN/FP), no por su *accuracy*.

**T6 — Análisis y decisión (10 min).** Convertir las predicciones en una
decisión con coste: aceptar/rechazar, agarrar/saltar, liberar/parar línea,
alertar/ignorar. La cifra que decide se reporta con su coste.

**T7 — Visualización (10 min).** Guardar al menos una figura por etapa que
tenga trabajo que mostrar, y la figura final del sistema.

**T8 — Interacción (10 min).** El sistema termina en una acción o un reporte
reproducible: el orden de agarre del robot, el resumen del turno, la decisión
de la línea, la alerta del juego, la recomendación de la planta.

### 5.4 Preguntas de análisis

Se responden en `analisis.md`, cada una con una cifra o una figura detrás.

1. ¿Cuál es la cifra que decide en su sistema y cómo se midió? ¿Qué costaría
   equivocarse en cada dirección (la pareja FN/FP de su dominio)?
2. ¿Qué etapa es la más lenta y cuánto pesa en el tiempo total? ¿Qué pasaría
   en su dominio si esa etapa costara el doble (fotogramas por segundo,
   piezas por minuto)?
3. ¿Qué etapa fue la más difícil de integrar y por qué? ¿Qué contrato entre
   etapas tuvieron que aclarar?
4. ¿Qué pasaría si la adquisición cambiara (otra cámara, otro fondo, otro
   nivel del juego)? ¿Qué etapa del sistema absorbería el cambio y cuál se
   rompería primero?
5. ¿Qué pieza de las clases 1–4 usa cada etapa de su sistema? Cite el ejemplo
   concreto que tomaron (ruta del ejemplo, no «lo visto en clase»).

### 5.5 Reto (opcional, para quien termine)

Insertar una variación en UNA etapa y medir la consecuencia en la cifra
final: subir el ruido de la adquisición, cambiar el umbral de Otsu por uno
fijo, quitar la morfología, o cambiar el modelo por el peor de la tabla de la
Clase 4. El sistema debe seguir ejecutando y el análisis debe reportar la
diferencia medida.

---

## 6. Criterios de evaluación

Sobre 100. Rúbrica del proyecto de integración, alineada con
`docs/27_ACADEMIC_RUBRICS.md` del repositorio del motor.

| Criterio | Puntos | Se consigue si… |
|---|---|---|
| **Comprensión conceptual** | 10 | Cada etapa se explica con su contrato (qué recibe, qué devuelve), no con su biblioteca |
| **Implementación** | 15 | El sistema ejecuta de principio a fin, con datos que no entrenaron, y `main.py` es el único punto de entrada |
| **Procesamiento** | 15 | Las etapas 1–4 producen lo que dicen producir y cada una reporta su medición mínima de §5.2 |
| **ML/DL** | 15 | Partición honesta, línea base al lado de la *accuracy*, y el modelo se elige por las celdas de su matriz |
| **Integración** | 15 | Las ocho etapas están encadenadas y el cambio de una se propaga: la cadena se ve en la salida, no en el diagrama |
| **Análisis** | 15 | La cifra que decide está medida, con su coste de error y su justificación por dominio |
| **Ingeniería** | 10 | Semillas fijas, rutas relativas, ASCII en consola, `resultados.txt` coincide con lo que imprime `main.py` |
| **Presentación** | 5 | La figura y la cifra de cierre se entienden sin preguntar, en 3 minutos |

**Penalizaciones:**

- −10 si `analisis.md` afirma algo que la salida de `main.py` contradice.
- −10 si el modelo «elegido» no es el que su propia tabla sostiene.
- −10 si las figuras no llevan título o no se sabe qué etapa es cuál.
- −5 por cada ruta absoluta (`C:\Users\...`) en el código entregado.
- −10 si el sistema «funciona» sólo con datos que ya vio (fuga de
  información: la prueba de §5.2 es que los datos de la ejecución no
  entrenaron).

**Lo que NO se evalúa:** la sofisticación del modelo, ni que la *accuracy*
sea alta, ni el dominio elegido. Se evalúa que el sistema **ejecute encadenado
y mienta menos que su cifra final**: cada número medido en su propia ejecución
y cada decisión sostenida por un número.

---

## 7. Material

| Recurso | Ruta |
|---|---|
| Plantilla de proyecto (notebook) | `notebooks/class05_template.ipynb` |
| Industrial (estación de inspección) | `examples/class05_integration/industrial/estacion_de_inspeccion.py` |
| Videojuego (analizador de fotogramas) | `examples/class05_integration/game/analizador_de_fotogramas.py` |
| Mecatrónica (percepción pick-and-place) | `examples/class05_integration/mechatronics/percepcion_pick_and_place.py` |
| Manufactura (línea de conteo) | `examples/class05_integration/manufacturing/linea_de_conteo.py` |
| Análisis de datos (panel de resultados) | `examples/class05_integration/data_analysis/panel_de_resultados.py` |
| Solución de referencia | `solutions/clase05_solucion.py` |
| Material de las clases 1–4 | `examples/class0{1..4}_*/` (cada etapa toma su pieza de ahí) |
| Datasets y modelo desplegado | `datasets/`, `outputs/clase04/modelo_entidades.pkl` |

**Dominios disponibles (la fuente de cada uno, para T1):**

| Dominio | Pregunta del sistema | Fuente posible | Pieza de clases anteriores |
|---|---|---|---|
| **Videojuego** | *¿Qué ve este fotograma?* | `engine_bridge.capturar_escena`, composición con sprites del motor | Clase 4, `clasificar_entidades.py` |
| **Mecatrónica** | *¿Qué agarro y dónde?* | escena de mesa compuesta, cámara | Clase 3, `contorno_y_centroide.py`; Clase 4, `detectar_y_localizar.py` |
| **Industrial** | *¿Esta pieza pasa?* | `synthetic.lote_de_piezas`, cámara sobre banda | Clase 1, `realce_de_pieza.py`; Clase 4, `clasificar_piezas.py` |
| **Manufactura** | *¿Cuántas hay y cuántas salen bien?* | `synthetic.piezas_en_contacto` | Clase 3, `watershed_piezas.py` |
| **Análisis de datos** | *¿Qué dicen los datos de todos los sistemas?* | `datasets/features/`, CSVs de lotes | Clase 3, `features_csv.py`; Clase 4, `comparar_modelos.py` |

---

## 8. Notas para el profesor

**Si el aula usa Windows.** La consola es cp1252. Que nadie imprima flechas
Unicode ni emoji: `UnicodeEncodeError` a mitad de la presentación cuesta diez
minutos y toda la atención. Los ejemplos y la solución están verificados en
ASCII puro, y la rúbrica penaliza la consola rota por ASCII no puro.

**El error de bulto que hay que provocar.** Un grupo que «integra» pegando el
código de los cuatro ejemplos sin definir los contratos entre etapas: la
extracción recibe máscaras de distinto tamaño, el modelo recibe columnas en
otro orden, y el sistema corre pero miente. La pregunta que tienen que poder
responder es *¿qué recibe tu segmentación y qué le entregas a tu modelo?* — y
la respuesta está en la salida de su propio `main.py`.

**El otro error de bulto.** Declarar el sistema «funcionando» con la salida
de una sola ejecución, sin `resultados.txt`. La regla del curso es la de
siempre: se entrega lo que se ejecutó, y la presentación de cierre corre el
sistema delante de todos.

**El puente al final del bloque.** La Clase 5 cierra las tres unidades del
bloque —procesamiento, segmentación y aplicaciones integradoras— con el mismo
método de todo el curso: cada número medido en su propia ejecución, cada
decisión sostenida por un número. Un estudiante que termina este proyecto
tiene un sistema que decide con visión artificial; lo que le falta del temario
oficial (redes profundas, YOLO, PyTorch) está documentado como ampliación en
Colab, y el proyecto de integración es exactamente el andamiaje sobre el que
cae bien.

**Ritmo.** Si el tiempo aprieta, el recorte es T7 (visualización se queda con
una figura) y la puesta en común se hace en el pasillo, no en el aula. Lo que
no se recorta es T2 (el esqueleto de 8 etapas corriendo con datos mínimos
antes de llenar nada): sin él, los grupos se atascan en la primera etapa y el
sistema no llega a existir.
