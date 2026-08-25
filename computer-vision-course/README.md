# Curso de Visión por Computadora — 5 clases

Material docente de **Procesamiento Digital de Imágenes**, **Segmentación y
Análisis** y **Aplicaciones Integradoras** (Unidades VII, VIII y IX), en cinco
sesiones de cuatro horas.

Es un **módulo intensivo independiente**. No sustituye al curso de once clases
de `docs/21_COURSE_SCHEDULE.md`, que sigue vigente sin cambios. Se apoya en el
mismo motor —*Legacy of InFest*— como laboratorio.

| | |
|---|---|
| Arquitectura y decisiones | [`COURSE_ARCHITECTURE.md`](COURSE_ARCHITECTURE.md) |
| Estado | **Clases 1–5 terminadas y verificadas** |
| Guía de la Clase 1 | [`docs/clase01_guia.md`](docs/clase01_guia.md) |
| Guía de la Clase 2 | [`docs/clase02_guia.md`](docs/clase02_guia.md) |
| Guía de la Clase 3 | [`docs/clase03_guia.md`](docs/clase03_guia.md) |
| Guía de la Clase 4 | [`docs/clase04_guia.md`](docs/clase04_guia.md) |
| Guía de la Clase 5 | [`docs/clase05_guia.md`](docs/clase05_guia.md) |

---

## Empezar

```bash
pip install -r computer-vision-course/requirements.txt
```

Ya tienes casi todo si el `.venv` del motor está instalado: NumPy, OpenCV,
scikit-image, scikit-learn, SciPy, Matplotlib y Pillow vienen con él. Lo único
nuevo es `pandas`.

Comprobar que la instalación sirve:

```bash
python -m pytest computer-vision-course/tests -q
```

---

## Qué hay aquí

```
cvcourse/          la capa puente: el único código que sabe que el motor existe
docs/              guía por clase, con laboratorio y rúbrica
examples/          ejemplos .py ejecutables, por clase y por contexto
notebooks/         el laboratorio experimental (Colab)
solutions/         soluciones de referencia, para el profesor
scripts/           generador de datasets, reproducible por hash
datasets/          generados, no versionados (ver datasets/README.md)
tests/             238 pruebas: la capa, el contrato con el motor y que el material EJECUTA
requirements.txt   dependencias del curso (ninguna entra en el motor)
```

### Clase 1 — Adquisición, histogramas y mejoramiento

```bash
python examples/class01_acquisition/comparar_fuentes.py
python examples/class01_acquisition/game/histograma_de_sprites.py
python examples/class01_acquisition/mechatronics/aceptacion_de_toma.py
python examples/class01_acquisition/industrial/realce_de_pieza.py
```

Los datasets se generan una vez:

```bash
python scripts/build_datasets.py
```

### Clase 2 — Filtrado, convolución, ruido y bordes

```bash
python examples/class02_processing/comparar_implementaciones.py
python examples/class02_processing/game/bordes_de_escena.py
python examples/class02_processing/industrial/superficie_con_defectos.py
python examples/class02_processing/mechatronics/preproceso_para_contorno.py
python examples/class02_processing/rendimiento_convolucion.py
```

Cuaderno: `notebooks/class02.ipynb`. Solución: `solutions/clase02_solucion.py`.

### Clase 3 — Segmentación y extracción de características

```bash
python examples/class03_segmentation/game/separar_entidades.py
python examples/class03_segmentation/manufacturing/watershed_piezas.py
python examples/class03_segmentation/mechatronics/contorno_y_centroide.py
python examples/class03_segmentation/data_analysis/features_csv.py
```

Cuaderno: `notebooks/class03.ipynb`. Solución: `solutions/clase03_solucion.py`.
El producto de la clase es `features.csv`, y hay que **mirarlo sin entrenar**:
el modelo llega en la Clase 4.

### Clase 4 — Reconocimiento de patrones: de características a decisiones

```bash
python examples/class04_ml_dl/industrial/clasificar_piezas.py
python examples/class04_ml_dl/game/clasificar_entidades.py
python examples/class04_ml_dl/mechatronics/detectar_y_localizar.py
python examples/class04_ml_dl/data_analysis/comparar_modelos.py
```

Cuaderno: `notebooks/class04.ipynb`. Solución: `solutions/clase04_solucion.py`.
La regla de la clase: ninguna *accuracy* se lee sola — se lee contra la línea
base y con la matriz de confusión por celdas (FN vs. FP). PyTorch y YOLO
(partes C/D) se usan sólo en Colab: `notebooks/class04_colab.ipynb` (en local
degradan con mensaje y la suite las verifica igual).

### Clase 5 — Integración: de ocho etapas a un sistema que decide

```bash
python examples/class05_integration/industrial/estacion_de_inspeccion.py
python examples/class05_integration/game/analizador_de_fotogramas.py
python examples/class05_integration/mechatronics/percepcion_pick_and_place.py
python examples/class05_integration/manufacturing/linea_de_conteo.py
python examples/class05_integration/data_analysis/panel_de_resultados.py
```

Guía: [`docs/clase05_guia.md`](docs/clase05_guia.md). Plantilla del proyecto de
grupos: `notebooks/class05_template.ipynb`. Solución de referencia:
`solutions/clase05_solucion.py`. Cada sistema recorre la
cadena completa —adquisición → preprocesamiento → segmentación/detección →
extracción → ML/DL → análisis → visualización → interacción— y de cada uno la
salida se entiende sola: el coste del turno de la estación, la alerta por
fotograma del analizador, las coordenadas en milímetros del orden de agarre,
el conteo con expulsión de la línea y la tabla de modelos con su reporte de
despliegue. Sobre la mesa, la lección de la clase: si la segmentación
entrega tres regiones donde había una, las etapas de abajo no se caen — miden
tres piezas y las clasifican, mal o bien, pero sin avisar.

### `cvcourse`, módulo a módulo

**Funcionan en cualquier parte**, incluido Google Colab sin clonar el
repositorio del motor:

| Módulo | Para qué |
|---|---|
| `synthetic` | Piezas industriales sintéticas, deterministas, con verdad-terreno exacta |
| `features` | De una máscara a `features.csv`: área, perímetro, ancho, alto, relación de aspecto, circularidad |
| `viz` | Rejillas antes/después, histogramas, matrices de confusión, nubes de características |

**Necesitan el repositorio del motor:**

| Módulo | Para qué |
|---|---|
| `engine_bridge` | `Surface` ⇄ `ndarray`, recursos de `assets/`, captura de fotogramas reales de las escenas-laboratorio |
| `acquisition` | Fuentes de imagen: cámara, fichero, carpeta, vídeo, motor, sintética |
| `course_mode` | Abre las Unidades VII–IX en un perfil de progreso aislado |

`engine_bridge.hay_motor()` responde a esa pregunta **antes** de importar nada.
Es lo que permite que un notebook degrade a datos sintéticos en vez de fallar
en la tercera celda.

---

## Tres cosas que conviene saber antes de tocar el código

**1. Las imágenes van en RGB, `(alto, ancho, 3)`, `uint8`. Siempre.**
OpenCV lee BGR y `pygame.surfarray` entrega `(ancho, alto, 3)`. Las dos
conversiones se hacen una sola vez, en `acquisition` y en `engine_bridge`, y el
resto del curso no vuelve a pensar en ello. Ninguno de los dos errores lanza
excepción: el primero da imágenes azuladas, el segundo da bordes girados 90°.
Fallos que mienten en vez de romperse son los que cuestan una clase entera.

**2. El curso no escribe fuera de esta carpeta.**
Ni `src/`, ni `assets/`, ni `docs/`, ni `pyproject.toml`. Si un ejemplo necesita
algo del motor que no existe, se añade a `cvcourse`, no al motor.

**3. El modo taller usa un perfil de progreso aparte.**
El temario del motor es una cadena lineal: para abrir la Unidad VII hay que
haber aprobado siete unidades anteriores. `course_mode` siembra esos
prerrequisitos en `profiles/`, que **no** es el directorio del curso normal. El
expediente de nadie se toca.

---

## Uso rápido

```python
from cvcourse import acquisition, features, synthetic, viz

# Una fuente que funciona en el aula, en Colab y en CI.
with acquisition.mejor_fuente_disponible(("camara", "motor", "sintetica")) as fuente:
    print("usando:", fuente.nombre)      # deja constancia de a qué degradó
    imagen = fuente.leer()

# De una máscara a la tabla de la Clase 3.
piezas, verdad = synthetic.lote_de_piezas(n=30, semilla=0)
filas = features.caracteristicas_de_mascara(piezas[0] > 130, etiqueta_de_clase="OK")
features.guardar_csv(filas, "datasets/features/features.csv")

# El puente a la Clase 4.
X, y, nombres = features.a_matriz(filas)
```

Fotogramas reales del motor, sin abrir ninguna ventana:

```python
from cvcourse import engine_bridge

fotogramas = engine_bridge.capturar_escena("filter", fotogramas=5)   # (600, 800, 3)
```

Abrir el laboratorio del motor el día 1:

```python
from cvcourse import course_mode

course_mode.activar()          # Clase 1 → Unidad VII
course_mode.abrir("vision")    # Clase 3 → Unidad VIII
course_mode.abrir("patrones")  # Clase 4 → Unidad IX
```

---

## Requisitos

- Python 3.11 o superior.
- El repositorio de *Legacy of InFest* instalado (`pip install -e ".[dev]"`)
  para todo lo que use el motor.
- Sin pantalla (CI, servidor), exporta antes:

```bash
export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYGAME_HIDE_SUPPORT_PROMPT=1
```

PyTorch y YOLO (Clase 4, partes C y D) se usan **sólo en Google Colab**. No se
instalan en local a propósito: el motivo está en `COURSE_ARCHITECTURE.md` §5.2.
