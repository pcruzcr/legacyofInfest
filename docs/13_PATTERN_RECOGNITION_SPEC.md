---
document_id: "LOI-PATTERN-013"
title: "Legacy of InFest — Especificación de PatternRecognitionTools"
aliases: ["Especificación de PatternRecognitionTools", "Pattern Recognition Spec"]
tags: ["pattern", "reconocimiento", "ml"]
description: "Subsistema de aprendizaje automático de la Unidad IX"
source: "docs/13_PATTERN_RECOGNITION_SPEC.md"
date_processed: "2026-08-13"
---

# Legacy of InFest — Especificación de PatternRecognitionTools

**ID del documento:** LOI-PATTERN-013
**Versión:** 1.1.0
**Estado:** Oficial
**Compatibilidad:** Requiere `12_VISION_TOOLS_SPEC.md`, `11_FILTER_TOOLS_SPEC.md`, `03_ARCHITECTURE.md`, `10_LIBRARIES_AND_DEPENDENCIES.md`
**Audiencia:** Profesor, ayudantes de cátedra, asistentes de programación con IA

> **AUD-455.** Traduce el documento (cuerpo en inglés, resumen condensado en
> español al final). Corrige tres discrepancias reales contra
> `src/framework/processing/pattern_recognition_tools.py` (verificado por AST):
> - **§7 completo era falso.** Documentaba `PatternRecognitionTools.extract_hog()`,
>   `extract_lbp()`, `extract_color_histogram()` y `extract_combined()` como
>   métodos de paso a través hacia `VisionTools`. **Ninguno de los cuatro
>   existe en la clase real.** Un estudiante que siguiera este documento
>   escribiría `PatternRecognitionTools.extract_hog(surface)` y obtendría
>   `AttributeError`. La extracción de características vive únicamente en
>   `VisionTools` (`12_VISION_TOOLS_SPEC.md` §13) — se corrige la sección para
>   decir eso.
> - **`train()` tiene un parámetro `feature_method` que el documento no
>   mencionaba** (por defecto `"hog"`), y se usa para poblar
>   `TrainedModel.feature_method`.
> - **`predict()` no tiene `method='hog'` por defecto**: el valor real por
>   defecto es `None`, y si no se pasa nada cae a `model.feature_method`.
> - Añade una mención de `generate_training_report()`, un método real con
>   salida matplotlib (histograma de confusión, precisión por clase,
>   importancia de características) que no estaba documentado en ninguna
>   parte de este fichero.

---

## 1. Visión general

`PatternRecognitionTools` es el subsistema de aprendizaje automático del framework académico de Legacy of InFest. Encapsula todas las operaciones de clasificación y reconocimiento de patrones que enseña la **Unidad IX** del programa del curso: clasificación basada en características, entrenamiento de modelos, serialización de modelos, inferencia en tiempo de ejecución, e integración del aprendizaje automático en una aplicación interactiva.

Este módulo es la capa final de la tubería académica:

```
FilterTools (Unidad VII) → VisionTools (Unidad VIII) → PatternRecognitionTools (Unidad IX)
```

`PatternRecognitionTools` recibe vectores de características producidos por `VisionTools.extract_features()` y devuelve etiquetas de clase que dirigen un comportamiento de juego observable. Toda la complejidad del clasificador — k-NN, árboles de decisión, bosques aleatorios, SVM — queda oculta detrás de una API unificada.

El módulo está en:

```
src/framework/processing/pattern_recognition_tools.py
```

---

## 2. Propósito académico

`PatternRecognitionTools` hace que los conceptos de la Unidad IX sean **ejecutables dentro de una aplicación interactiva en tiempo real**. Los estudiantes entrenan clasificadores fuera de línea, los cargan en su escenario, y observan cómo el resultado de la clasificación cambia el comportamiento del juego a medida que evoluciona el estado visual del escenario.

Esto responde a la pregunta clave de la unidad de cierre: *¿puede una computadora reconocer patrones en datos visuales y responder inteligentemente?*

### 2.1 Objetivos de aprendizaje que soporta

| Objetivo | Mecanismo de PatternRecognitionTools |
|---|---|
| Entender los espacios de características | `extract_features()` (de VisionTools) produce el espacio de características |
| Aplicar clasificación k-NN | `PatternRecognitionTools.classify(features, model='knn')` |
| Aplicar clasificación por árbol de decisión | `classify(features, model='tree')` |
| Aplicar clasificación por bosque aleatorio | `classify(features, model='forest')` |
| Aplicar clasificación SVM | `classify(features, model='svm')` |
| Entrenar un clasificador a partir de un dataset | `PatternRecognitionTools.train(X, y, model_type)` |
| Evaluar el rendimiento del clasificador | `PatternRecognitionTools.evaluate(model, X_test, y_test)` |
| Serializar un modelo para uso en tiempo de ejecución | `PatternRecognitionTools.save_model(model, path)` |
| Cargar un modelo en tiempo de ejecución | `PatternRecognitionTools.load_model(path)` |
| Ejecutar inferencia en un bucle de juego | `PatternRecognitionTools.predict(model, surface)` |

---

## 3. Ubicación en el framework

```
src/framework/
└── processing/
    ├── filter_tools.py
    ├── vision_tools.py
    └── pattern_recognition_tools.py    ← Este módulo
```

### 3.1 Posición en la jerarquía de dependencias

```
Escenarios (código de estudiante)
    ↓
src/framework/processing/pattern_recognition_tools.py   ← Los estudiantes llaman a esto
    ↓
src/framework/processing/vision_tools.py                ← Para extracción de características
    ↓
scikit-learn, scikit-image, numpy, joblib, opencv-python
```

---

## 4. Integración con la arquitectura

### 4.1 Conexiones con el framework

| Punto de integración | Descripción |
|---|---|
| `VisionTools.extract_features()` | Fuente principal de vectores de características |
| `VisionTools.extract_hog()`, `extract_lbp()`, `extract_color_histogram()` | Fuentes directas alternativas de características |
| Escenas de escenario (código de estudiante) | Los estudiantes cargan modelos en `on_enter()`, ejecutan inferencia en `update()` |
| `student_assets/models/` | Directorio para ficheros de modelo serializados |
| Suite de pruebas unitarias (`tests/test_pattern_recognition_tools.py`) | Prueba el entrenamiento, la inferencia y los ciclos de serialización |

### 4.2 Lo que PatternRecognitionTools NO hace

| Acción prohibida | Razón |
|---|---|
| No llama a `EventBus` | Módulo de cómputo puro |
| No modifica el estado de entidades | Los resultados se devuelven; los estudiantes deciden qué hacer |
| No entrena en tiempo de ejecución | El entrenamiento siempre es fuera de línea |
| No lee el estado del juego | Toda la entrada es vía parámetros explícitos |
| No mantiene estado singleton | Métodos de clase sin estado (salvo el Registro de Modelos) |

---

## 5. Dependencias

| Biblioteca | Importación | Se usa para |
|---|---|---|
| `numpy` | `import numpy as np` | Manejo de arreglos de características |
| `scikit-learn` | `from sklearn.neighbors import KNeighborsClassifier`, etc. | Todos los clasificadores |
| `joblib` | `import joblib` | Serialización y carga de modelos |
| `src.framework.processing.vision_tools` | `from src.framework.processing.vision_tools import VisionTools` | Extracción de características interna (para `predict()`) |

**Los estudiantes nunca importan scikit-learn ni joblib directamente.**

---

## 6. Diagrama de clase

```
PatternRecognitionTools
│
├── [Tubería de entrenamiento]
│   ├── train(X, y, model_type, feature_method='hog', **kwargs) → TrainedModel
│   └── evaluate(model, X_test, y_test) → EvaluationResult
│
├── [Serialización de modelos]
│   ├── save_model(model, path) → None
│   └── load_model(path) → TrainedModel
│
├── [Registro de modelos]
│   ├── register_model(name, model) → None
│   ├── get_model(name) → TrainedModel
│   └── list_models() → list[str]
│
├── [Tubería de inferencia]
│   ├── classify(features, model) → str
│   ├── classify_proba(features, model) → dict[str, float]
│   └── predict(model, surface, method=None) → str
│
├── [Informe de entrenamiento]
│   └── generate_training_report(model, result, ...) → salida matplotlib
│       (histograma de confusión, precisión por clase, importancia de
│       características — ver §11.3)
│
└── [Utilidades internas — privadas]
    ├── _build_model(model_type, **kwargs) → sklearn estimator
    ├── _validate_features(features) → None
    ├── _validate_model(model) → None
    └── _validate_dataset(X, y) → None
```

**Nota:** a diferencia de lo que documentaba una versión anterior de este
fichero, `PatternRecognitionTools` **no tiene** métodos `extract_hog`,
`extract_lbp`, `extract_color_histogram` ni `extract_combined`. La
extracción de características vive únicamente en `VisionTools`
(`12_VISION_TOOLS_SPEC.md` §13) — ver §7 más abajo.

### 6.1 Definiciones de tipo de retorno

#### `TrainedModel` (dataclass)

| Campo | Tipo | Descripción |
|---|---|---|
| `model_type` | `str` | `'knn'`, `'tree'`, `'forest'`, `'svm'` |
| `estimator` | sklearn `Pipeline` | El objeto de modelo scikit-learn ya entrenado |
| `classes` | `list[str]` | Lista ordenada de cadenas de etiqueta de clase |
| `feature_method` | `str` | Método de extracción de características usado en el entrenamiento |
| `feature_length` | `int` | Longitud esperada del vector de entrada |
| `training_accuracy` | `float` | Precisión sobre el conjunto de entrenamiento |
| `metadata` | `dict` | Metadatos arbitrarios (hiperparámetros, notas) |

#### `EvaluationResult` (dataclass)

| Campo | Tipo | Descripción |
|---|---|---|
| `accuracy` | `float` | Precisión global sobre el conjunto de prueba |
| `per_class_accuracy` | `dict[str, float]` | Precisión por clase |
| `confusion_matrix` | `np.ndarray` | Matriz de confusión de forma `(n_classes, n_classes)` |
| `report` | `str` | Cadena de `classification_report` de scikit-learn |

---

## 7. Extracción de características — vive en VisionTools

`PatternRecognitionTools` **no** expone métodos propios de extracción de
características. Los estudiantes importan `VisionTools` directamente para
esa parte de la tubería y le pasan el vector resultante a `classify()` o
usan `predict()` (§13.3), que hace la extracción internamente.

| Necesita | Llame a |
|---|---|
| Vector HOG | `VisionTools.extract_hog(surface)` — ver `12_VISION_TOOLS_SPEC.md` §13.2 |
| Vector LBP | `VisionTools.extract_lbp(surface)` — ver `12_VISION_TOOLS_SPEC.md` §13.3 |
| Histograma de color | `VisionTools.extract_color_histogram(surface, bins)` — ver `12_VISION_TOOLS_SPEC.md` §13.4 |
| HOG + LBP + histograma de color concatenados | `VisionTools.extract_features(surface, method='combined')` — ver `12_VISION_TOOLS_SPEC.md` §13.1 |

**Ejemplo:**

```python
from src.framework.processing.vision_tools import VisionTools
from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

features = VisionTools.extract_hog(region_surface)
label = PatternRecognitionTools.classify(features, self.classifier)
```

O, de forma equivalente y más corta, usando `predict()` (§13.3), que hace
`extract_features()` + `classify()` en una sola llamada.

---

## 8. Estándares de dataset

### 8.1 Formato del dataset

Todos los datasets de entrenamiento usados en Legacy of InFest deben cumplir estos estándares:

| Propiedad | Estándar |
|---|---|
| Matriz de características `X` | `np.ndarray`, forma `(n_samples, n_features)`, dtype `float32` |
| Vector de etiquetas `y` | `np.ndarray`, forma `(n_samples,)`, dtype `str` o `int` |
| Mínimo de muestras por clase | 10 |
| Clases equilibradas | Recomendado. Los datasets desequilibrados deben documentarse en el README. |
| Escalado de características | Se aplica automáticamente dentro de `train()` usando `StandardScaler` |

### 8.2 Fuentes del dataset

Los estudiantes recopilan su dataset de entrenamiento a partir de **recursos de juego y capturas de pantalla**. Fuentes aceptables:

| Fuente | Método |
|---|---|
| Fondos de escenario | Guardar capturas en distintos estados del escenario; etiquetar a mano |
| Hojas de sprites | Extraer fotogramas; etiquetar por estado de animación |
| Generado sintéticamente | Generar superficies programáticamente con propiedades conocidas |
| Provisto por el profesorado | El profesorado puede proveer datasets pre-etiquetados para la Unidad IX |

### 8.3 Formato de fichero del dataset

Los datasets se serializan como ficheros `.npz` (archivo comprimido de NumPy):

```python
# Guardar un dataset (script de entrenamiento del estudiante):
np.savez('student_assets/datasets/my_dataset.npz', X=X, y=y)

# Cargar un dataset:
data = np.load('student_assets/datasets/my_dataset.npz')
X, y = data['X'], data['y']
```

---

## 9. Tubería de entrenamiento

### 9.1 `PatternRecognitionTools.train(X, y, model_type, feature_method='hog', **kwargs)`

**Propósito:** ajusta un clasificador a la matriz de características y el vector de etiquetas dados. Devuelve un objeto `TrainedModel` listo para serializar o usar de inmediato. Este método se llama desde un **script de entrenamiento**, no desde el juego mismo.

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `X` | `np.ndarray` | Forma `(n_samples, n_features)`, float32 | Matriz de características |
| `y` | `np.ndarray` | Forma `(n_samples,)` | Vector de etiquetas |
| `model_type` | `str` | `'knn'`, `'tree'`, `'forest'`, `'svm'` | Tipo de clasificador |
| `feature_method` | `str` | Por defecto `'hog'` | Se guarda en `TrainedModel.feature_method`; lo usa `predict()` cuando no se le pasa un `method` explícito |
| `**kwargs` | — | Específico del modelo | Hiperparámetros (ver §14) |

**Salidas:** objeto `TrainedModel`.

**Tubería interna:**

```
Entradas: X (n_samples, n_features), y (n_samples,)
    ↓
_validate_dataset(X, y)
    ↓
StandardScaler().fit_transform(X) → X_scaled
    ↓
_build_model(model_type, **kwargs) → sklearn_estimator
    ↓
sklearn_estimator.fit(X_scaled, y)
    ↓
training_accuracy = sklearn_estimator.score(X_scaled, y)
    ↓
return TrainedModel(
    model_type=model_type,
    estimator=Pipeline([('scaler', scaler), ('classifier', estimator)]),
    classes=list(unique_labels),
    feature_method=feature_method,
    feature_length=X.shape[1],
    training_accuracy=training_accuracy,
    metadata={'kwargs': kwargs}
)
```

**Importante:** el `StandardScaler` está embebido dentro del objeto `Pipeline` del modelo. Esto significa que el escalado se aplica automáticamente tanto en el entrenamiento como en la inferencia — los estudiantes no necesitan escalar las características a mano antes de llamar a `classify()`.

**Restricciones:**

- Mínimo 2 clases distintas en `y`.
- Mínimo 10 muestras en total.
- `model_type` debe ser uno de los valores registrados.
- Lanza `ValueError` si falla la validación.

**Dependencias:** `scikit-learn`, `numpy`

**Ejemplo de uso (script de entrenamiento — no es código del juego):**

```python
import numpy as np
from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

# Cargar el dataset
data = np.load('student_assets/datasets/stage3_regions.npz')
X, y = data['X'].astype(np.float32), data['y']

# Entrenar un bosque aleatorio
model = PatternRecognitionTools.train(X, y, model_type='forest', n_estimators=50)
print(f"Precisión de entrenamiento: {model.training_accuracy:.3f}")

# Guardar para uso en tiempo de ejecución
PatternRecognitionTools.save_model(model, 'student_assets/models/stage3_classifier.pkl')
```

---

### 9.2 `PatternRecognitionTools.evaluate(model, X_test, y_test)`

**Propósito:** evalúa un modelo entrenado sobre un conjunto de prueba reservado. Devuelve un `EvaluationResult` con precisión, precisión por clase, matriz de confusión, y un informe de clasificación. Se llama desde el script de entrenamiento — no en tiempo de ejecución.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `model` | `TrainedModel` | Un modelo ya entrenado de `train()` |
| `X_test` | `np.ndarray` | Matriz de características de prueba, forma `(n_test, n_features)` |
| `y_test` | `np.ndarray` | Etiquetas de prueba, forma `(n_test,)` |

**Salidas:** `EvaluationResult` (ver Sección 6.1).

**Restricciones:**

- `X_test.shape[1]` debe ser igual a `model.feature_length`.
- Al menos 1 muestra por clase en el conjunto de prueba.

**Dependencias:** `scikit-learn` (`classification_report`, `confusion_matrix`)

**Ejemplo de uso:**

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = PatternRecognitionTools.train(X_train, y_train, model_type='knn', n_neighbors=5)
result = PatternRecognitionTools.evaluate(model, X_test, y_test)

print(f"Precisión de prueba: {result.accuracy:.3f}")
print(result.report)
# → Incluir esta salida en el README del escenario como documentación obligatoria
```

---

## 10. Tubería de validación

La tubería de validación documenta cómo deben probar y documentar los estudiantes sus clasificadores antes de integrarlos en su escenario.

### 10.1 Pasos de validación obligatorios

| Paso | Acción | Documentación requerida |
|---|---|---|
| 1. Dividir el dataset | Usar `train_test_split` con `test_size=0.2`, `random_state=42` | Indicar la proporción de división en el README |
| 2. Entrenar el modelo | Llamar a `PatternRecognitionTools.train()` | Indicar el tipo de modelo y los hiperparámetros |
| 3. Evaluar | Llamar a `PatternRecognitionTools.evaluate()` | Incluir el `EvaluationResult.report` completo en el README |
| 4. Verificar la longitud de características | Confirmar que `model.feature_length` coincide con la extracción en tiempo de ejecución | Indicarlo en el README |
| 5. Prueba de cordura | Ejecutar `classify()` sobre 3 ejemplos conocidos a mano | Mostrar predicciones frente a lo esperado en el README |

### 10.2 Rendimiento mínimo aceptable

| Métrica | Umbral | Acción si está por debajo |
|---|---|---|
| Precisión de prueba | ≥ 0.70 (70%) | Recolectar más muestras, ajustar hiperparámetros, o cambiar el tipo de modelo |
| Precisión por clase | ≥ 0.60 para cada clase | Revisar el equilibrio de clases, recolectar más muestras para la clase débil |

Se puede entregar un clasificador por debajo de estos umbrales, pero debe incluir un análisis documentado de por qué el rendimiento es limitado y qué haría falta para mejorarlo.

---

## 11. Serialización de modelos

### 11.1 `PatternRecognitionTools.save_model(model, path)`

**Propósito:** serializa un `TrainedModel` a disco usando `joblib`. Todo el dataclass `TrainedModel` — incluyendo el Pipeline de scikit-learn ya entrenado (con el escalador), las etiquetas de clase, la longitud de características y los metadatos — se serializa en un único fichero `.pkl`.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `model` | `TrainedModel` | Un modelo ya entrenado de `train()` |
| `path` | `str` o `pathlib.Path` | Ruta del fichero de salida (debe terminar en `.pkl`) |

**Salidas:** ninguna. El fichero se escribe en `path`.

**Convención de ubicación de ficheros:** todos los ficheros de modelo de estudiante deben guardarse en `student_assets/models/`.

**Restricciones:**

- `path` debe tener extensión `.pkl`. Lanza `ValueError` en caso contrario.
- El directorio padre se crea si no existe.

**Dependencias:** `joblib`

---

### 11.2 `PatternRecognitionTools.load_model(path)`

**Propósito:** deserializa un `TrainedModel` desde disco. Verifica que el objeto cargado es un `TrainedModel` válido antes de devolverlo.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `path` | `str` o `pathlib.Path` | Ruta a un fichero `.pkl` creado por `save_model()` |

**Salidas:** `TrainedModel` — listo para usar con `classify()` y `predict()`.

**Restricciones:**

- El fichero debe existir. Lanza `FileNotFoundError` si no se encuentra.
- El objeto cargado debe ser un `TrainedModel`. Lanza `TypeError` si no lo es.
- No cargar modelos de fuentes no confiables (`joblib.load` puede ejecutar código arbitrario — sólo datasets provistos por el profesorado en el contexto académico).

**Dependencias:** `joblib`

**Ejemplo de uso (en `on_enter()` del escenario):**

```python
from pathlib import Path

from src.framework.processing.pattern_recognition_tools import PatternRecognitionTools

class Stage3Scene(BaseScene):
    def on_enter(self):
        # AUD-455: `STUDENT_ASSETS_DIR` no existe como constante en el motor
        # (a diferencia de `STUDENT_TEMPLATES_DIR`, ver 22_API_CONTRACTS.md
        # §2.1) — el estudiante construye la ruta directamente.
        model_path = Path("student_assets") / "models" / "stage3_classifier.pkl"
        self.classifier = PatternRecognitionTools.load_model(model_path)
```

---

## 12. Registro de modelos

El Registro de Modelos da un almacén con nombre, en memoria, para modelos cargados. Permite que un escenario cargue varios modelos al arrancar y los recupere por nombre sin pasar objetos de modelo a través de múltiples llamadas.

### 12.1 `PatternRecognitionTools.register_model(name, model)`

**Propósito:** guarda un `TrainedModel` cargado en el registro bajo un nombre de cadena.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `name` | `str` | Clave única de registro para este modelo |
| `model` | `TrainedModel` | Modelo ya entrenado a registrar |

**Salidas:** ninguna.

**Restricciones:** si `name` ya existe, el modelo anterior se reemplaza y se registra un aviso.

---

### 12.2 `PatternRecognitionTools.get_model(name)`

**Propósito:** recupera un modelo registrado por nombre.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `name` | `str` | Clave de registro |

**Salidas:** `TrainedModel`.

**Restricciones:** lanza `KeyError` si `name` no se encuentra. El mensaje incluye la salida de `list_models()`.

---

### 12.3 `PatternRecognitionTools.list_models()`

**Propósito:** devuelve la lista de todos los nombres de modelo actualmente registrados.

**Salidas:** `list[str]`.

---

## 13. Tubería de inferencia

### 13.1 `PatternRecognitionTools.classify(features, model)`

**Propósito:** clasifica un vector de características ya calculado usando un `TrainedModel`. Es el método de inferencia central. Aplica automáticamente el `StandardScaler` interno del modelo (vía el Pipeline) y devuelve la etiqueta de clase predicha como cadena.

**Es el método principal en tiempo de ejecución.** Está pensado para usarse dentro de bucles `update()`.

**Entradas:**

| Parámetro | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `features` | `np.ndarray` | Forma `(n_features,)`, float32 | Vector de características de `VisionTools.extract_features()` |
| `model` | `TrainedModel` | Debe ser un modelo ya entrenado | El clasificador a usar |

**Salidas:** `str` — la etiqueta de clase predicha.

**Restricciones:**

- `features.shape[0]` debe ser igual a `model.feature_length`. Lanza `ValueError` si no.
- Debe completarse en < 2ms para uso seguro en un bucle de juego a 60 FPS.
- No modifica el estado del modelo.

**Dependencias:** `scikit-learn` (vía el Pipeline interno del modelo)

**Ejemplo de uso:**

```python
# En Stage3Scene.update(dt):
from src.framework.processing.vision_tools import VisionTools

region_surface = self.stage_surface.subsurface(self.analysis_rect)
features = VisionTools.extract_hog(region_surface)
label = PatternRecognitionTools.classify(features, self.classifier)

if label == 'dark_zone':
    self.spawn_dark_enemy()
elif label == 'light_zone':
    self.spawn_light_enemy()
```

---

### 13.2 `PatternRecognitionTools.classify_proba(features, model)`

**Propósito:** devuelve la distribución de probabilidad de clase para un vector de características. En vez de una sola etiqueta, devuelve la confianza del modelo para cada clase. Disponible sólo para modelos que soportan estimación de probabilidad (`knn`, `forest`, `svm` con `probability=True`).

**Entradas:** igual que `classify()`.

**Salidas:** `dict[str, float]` — etiqueta de clase mapeada a probabilidad. Las probabilidades suman 1.0.

**Restricciones:**

- El árbol de decisión (`'tree'`) no soporta estimación de probabilidad — lanza `NotImplementedError`.
- No se aplica calibración de probabilidad (salida cruda de `predict_proba()`).

**Ejemplo de uso:**

```python
proba = PatternRecognitionTools.classify_proba(features, self.classifier)
# {'dark_zone': 0.72, 'light_zone': 0.18, 'neutral': 0.10}

if proba.get('dark_zone', 0) > 0.6:
    self.activate_dark_mode()
```

---

### 13.3 `PatternRecognitionTools.predict(model, surface, method=None)`

**Propósito:** método de conveniencia. Combina la extracción de características y la clasificación en una sola llamada. Internamente llama a `VisionTools.extract_features(surface, method)` y luego a `classify(features, model)`.

**Entradas:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `model` | `TrainedModel` | Modelo ya entrenado |
| `surface` | `pygame.Surface` | Superficie a clasificar |
| `method` | `str \| None` | Método de extracción de características (`'hog'`, `'lbp'`, `'color_hist'`, `'combined'`). Si se omite (`None`, el valor por defecto real), usa `model.feature_method` |

**Salidas:** `str` — etiqueta de clase predicha.

**Restricciones:**

- El tiempo de inferencia = extracción de características + clasificación; debe mantenerse por debajo de 2ms en total.

**Ejemplo de uso:**

```python
# Clasificación en una línea, usando el método de extracción con el que se entrenó el modelo:
label = PatternRecognitionTools.predict(self.classifier, region_surface)

# O forzando un método distinto al de entrenamiento:
label = PatternRecognitionTools.predict(self.classifier, region_surface, method='hog')
```

---

## 14. API de clasificación — especificaciones de clasificador

### 14.1 K vecinos más cercanos (`'knn'`)

| Parámetro | Por defecto | Descripción |
|---|---|---|
| `n_neighbors` | 5 | Número de vecinos a considerar |
| `weights` | `'uniform'` | `'uniform'` o `'distance'` |
| `metric` | `'euclidean'` | Métrica de distancia |

**Características:**
- Simple, interpretable — los estudiantes pueden explicar "los 5 ejemplos de entrenamiento más parecidos"
- Sin fase de entrenamiento (aprendizaje perezoso) — `train()` es rápido
- El tiempo de inferencia crece con el tamaño del dataset — mantener el conjunto de entrenamiento pequeño (< 500 muestras) para inferencia < 2ms

**Ejemplo de uso:**

```python
model = PatternRecognitionTools.train(X, y, 'knn', n_neighbors=3, weights='distance')
```

---

### 14.2 Árbol de decisión (`'tree'`)

| Parámetro | Por defecto | Descripción |
|---|---|---|
| `max_depth` | `None` (ilimitada) | Profundidad máxima del árbol |
| `min_samples_split` | 2 | Muestras mínimas para dividir un nodo |
| `criterion` | `'gini'` | Criterio de división: `'gini'` o `'entropy'` |
| `random_state` | 42 | Semilla de reproducibilidad |

**Características:**
- Altamente interpretable — los estudiantes pueden inspeccionar la estructura del árbol de decisión
- Propenso al sobreajuste sin `max_depth` — los estudiantes deben fijarlo
- Inferencia rápida: O(log n_nodos)
- No soporta salida de probabilidad

**Ejemplo de uso:**

```python
model = PatternRecognitionTools.train(X, y, 'tree', max_depth=5, criterion='entropy')
```

---

### 14.3 Bosque aleatorio (`'forest'`)

| Parámetro | Por defecto | Descripción |
|---|---|---|
| `n_estimators` | 50 | Número de árboles en el bosque |
| `max_depth` | `None` | Profundidad máxima del árbol |
| `max_features` | `'sqrt'` | Características por división de árbol |
| `random_state` | 42 | Semilla de reproducibilidad |

**Características:**
- Robusto al sobreajuste — buena elección por defecto para estudiantes
- Entrenamiento más lento que un solo árbol, pero aún rápido para datasets pequeños
- Importancia de características accesible vía `model.estimator.named_steps['classifier'].feature_importances_`

**Ejemplo de uso:**

```python
model = PatternRecognitionTools.train(X, y, 'forest', n_estimators=100, max_depth=8)
```

---

### 14.4 Máquina de vectores de soporte (`'svm'`)

| Parámetro | Por defecto | Descripción |
|---|---|---|
| `kernel` | `'rbf'` | Tipo de kernel: `'linear'`, `'rbf'`, `'poly'` |
| `C` | 1.0 | Parámetro de regularización |
| `gamma` | `'scale'` | Coeficiente del kernel |
| `probability` | `True` | Activa la estimación de probabilidad (necesaria para `classify_proba`) |
| `random_state` | 42 | Semilla de reproducibilidad |

**Características:**
- Buen rendimiento en datasets pequeños con características de alta dimensión
- Entrenamiento más lento que los métodos de árbol en datasets grandes
- La estimación de probabilidad con `probability=True` necesita escalado de Platt adicional (entrenamiento más lento)

**Ejemplo de uso:**

```python
model = PatternRecognitionTools.train(X, y, 'svm', kernel='rbf', C=2.0)
```

---

## 15. Patrón de uso del registro de modelos

El patrón recomendado para un escenario de estudiante que usa varios clasificadores:

```python
# En Stage3Scene.on_enter():
models_dir = Path("student_assets") / "models"
PatternRecognitionTools.register_model(
    'region_classifier',
    PatternRecognitionTools.load_model(models_dir / 'regions.pkl')
)
PatternRecognitionTools.register_model(
    'sprite_classifier',
    PatternRecognitionTools.load_model(models_dir / 'sprites.pkl')
)

# En Stage3Scene.update(dt):
region_label = PatternRecognitionTools.predict(
    PatternRecognitionTools.get_model('region_classifier'),
    self.background_region,
    method='hog'
)
sprite_label = PatternRecognitionTools.predict(
    PatternRecognitionTools.get_model('sprite_classifier'),
    self.sprite_region,
    method='lbp'
)
```

---

## 16. Flujo de predicción

### 16.1 Flujo completo de inferencia en tiempo de ejecución

```
[update() del escenario — cada N fotogramas]
    ↓
1. Capturar la región de superficie
   region = screen_surface.subsurface(analysis_rect)
    ↓
2. Preprocesar (opcional — si el entrenamiento usó entrada filtrada)
   preprocessed = FilterTools.gaussian_blur(region, sigma=1.0)
    ↓
3. Extraer características
   features = VisionTools.extract_hog(preprocessed)
    ↓
4. Clasificar
   label = PatternRecognitionTools.classify(features, self.classifier)
    ↓
5. Actuar sobre el resultado
   if label == 'class_A': → comportamiento de juego A
   if label == 'class_B': → comportamiento de juego B
```

### 16.2 Limitación por fotograma para la inferencia

La clasificación no se hace cada fotograma. Los estudiantes usan un contador de fotogramas:

| Tipo de clasificador | Frecuencia de inferencia recomendada |
|---|---|
| k-NN (dataset < 100) | Cada 3 fotogramas |
| k-NN (dataset 100–500) | Cada 5 fotogramas |
| Árbol de decisión | Cada 2 fotogramas |
| Bosque aleatorio (50 árboles) | Cada 3 fotogramas |
| SVM (kernel RBF) | Cada 3 fotogramas |

---

## 17. Restricciones de rendimiento

### 17.1 Presupuesto de tiempo de inferencia

Presupuesto total de inferencia por llamada: **< 2ms** (para mantenerse dentro del presupuesto de fotograma de 16.67ms junto con la extracción de características).

| Clasificador | Tamaño de dataset | Tiempo de inferencia típico |
|---|---|---|
| k-NN (k=5) | 100 muestras | < 0.5ms |
| k-NN (k=5) | 500 muestras | ~1ms |
| k-NN (k=5) | 1000+ muestras | > 2ms ⚠ |
| Árbol de decisión (profundidad 5) | Cualquiera | < 0.1ms |
| Bosque aleatorio (50 árboles) | Cualquiera | ~0.5ms |
| SVM (RBF) | Cualquiera | < 1ms |

### 17.2 Tiempo de entrenamiento (sólo fuera de línea)

| Clasificador | Dataset 100 | Dataset 500 | Dataset 1000 |
|---|---|---|---|
| k-NN | ~0ms (perezoso) | ~0ms (perezoso) | ~0ms (perezoso) |
| Árbol de decisión | < 100ms | < 500ms | ~1s |
| Bosque aleatorio (50) | ~500ms | ~2s | ~5s |
| SVM (RBF) | ~100ms | ~2s | ~10s |

---

## 18. Correspondencia con la Unidad IX

| Tema de la Unidad IX | Componente de PatternRecognitionTools | Observable en el juego |
|---|---|---|
| Descriptores (HOG, LBP) | `VisionTools.extract_hog()`, `extract_lbp()` | Vector de características impreso en el README |
| Características basadas en color | `VisionTools.extract_color_histogram()` | La distribución de color dirige la clase |
| Descriptores combinados | `VisionTools.extract_features(method='combined')` | Vector de características multi-modal |
| Clasificación KNN | `train(..., 'knn')` + `classify()` | El juego cambia de comportamiento según la clase |
| Árbol de decisión | `train(..., 'tree')` | El estudiante inspecciona la estructura del árbol |
| Bosque aleatorio | `train(..., 'forest')` | Clasificador robusto para el proyecto de cierre |
| SVM | `train(..., 'svm')` | Clasificador avanzado opcional |
| Tubería de entrenamiento de modelo | `train()` + `evaluate()` | Precisión documentada en el README |
| Serialización de modelo | `save_model()` / `load_model()` | Fichero `.pkl` en student_assets/ |
| Bucle de inferencia | `predict()` en `update()` | Resultado de clasificación en tiempo real |
| Integración de visión por computadora | Tubería completa (Filter→Vision→Pattern) | Demo de extremo a extremo en Stage 3 |

---

## 19. Correspondencia con la evaluación

| Evaluación | Unidad | Entregable requerido | Evidencia |
|---|---|---|---|
| Examen práctico III | IX | Tubería completa: dataset → entrenar → evaluar → integrar | Demo en vivo + EvaluationResult en el README |
| Final de Stage 3 | IX | Clasificador funcionando en tiempo de ejecución, cambiando el comportamiento del juego | Revisión de código + explicación oral |
| Presentación final | IX | Explicar un clasificador matemáticamente (frontera de decisión, espacio de características) | Oral + notebook |

---

## 20. Entregables del profesorado

1. **`src/framework/processing/pattern_recognition_tools.py`** — Implementación completa, documentada y probada.
2. **`tests/test_pattern_recognition_tools.py`** — Pruebas de entrenamiento, serialización, inferencia y la tubería completa.
3. **`tools/build_dataset.py`** — Un script de ayuda que los estudiantes usan para extraer características de directorios de imágenes etiquetadas y construir un fichero de dataset `.npz`.
4. **`student_assets/datasets/sample_dataset.npz`** — Un dataset de muestra pequeño (50 muestras, 3 clases) para que los estudiantes verifiquen su tubería antes de construir la propia.
5. **Escena demo (ver Documento 15)** — Demo interactiva de la Unidad IX donde se muestra un clasificador entrenado clasificando regiones de pantalla en tiempo real.
6. **Plantilla de notebook de entrenamiento** — `notebooks/train_stage3_classifier.ipynb` — una plantilla de Jupyter notebook con todos los pasos requeridos ya preparados.

---

## 21. Reutilización por parte de los estudiantes

Los estudiantes reutilizan `PatternRecognitionTools` al:

1. Ejecutar `tools/build_dataset.py` para construir su dataset a partir de capturas de superficie etiquetadas.
2. Usar la plantilla de notebook de entrenamiento para entrenar y evaluar su clasificador.
3. Llamar a `save_model()` para guardar el modelo entrenado.
4. Cargar el modelo en `Stage3Scene.on_enter()`.
5. Llamar a `predict()` en `Stage3Scene.update()` cada N fotogramas.
6. Usar la etiqueta predicha para cambiar el comportamiento del juego.

Los estudiantes no escriben **ningún código de aprendizaje automático**. Escriben **comportamiento de juego condicionado por los resultados de la clasificación**.

---

## 22. Evidencia de aprendizaje

Un estudiante ha demostrado el aprendizaje de la Unidad IX cuando puede:

1. **Mostrar** su dataset: número de muestras, clases, método de características y equilibrio de clases.
2. **Presentar** su `EvaluationResult`: precisión, matriz de confusión, e informe por clase.
3. **Explicar** por qué eligió su tipo de clasificador (interpretabilidad, precisión, velocidad).
4. **Demostrar en vivo** el clasificador cambiando el comportamiento del juego en al menos dos clases distintas.
5. **Explicar** matemáticamente cómo es la frontera de decisión de su clasificador (lineal para SVM lineal, divisiones de árbol para árbol de decisión, etc.).
6. **Comparar** dos tipos de clasificador sobre su dataset y explicar el compromiso.

---

## 23. Restricciones

| Restricción | Alcance |
|---|---|
| Los estudiantes nunca importan `sklearn` directamente | Todos los ficheros de escenario de estudiante |
| Los estudiantes nunca importan `joblib` directamente | Todos los ficheros de escenario de estudiante |
| El entrenamiento de modelos nunca ocurre en tiempo de ejecución | El entrenamiento siempre es fuera de línea |
| Los ficheros de modelo se guardan sólo en `student_assets/models/` | Restricción del sistema de ficheros |
| `PatternRecognitionTools` nunca llama a `EventBus` | Aislamiento de procesamiento |
| El método de extracción de características usado en la inferencia por defecto es el de entrenamiento | `predict()` cae a `model.feature_method` cuando no se pasa `method` explícito |

---

## 24. Extensiones futuras

| Extensión | Descripción | Objetivo |
|---|---|---|
| `cross_validate(X, y, model_type, folds)` | Validación cruzada de k iteraciones | Unidad IX avanzada |
| `hyperparameter_search(X, y, model_type, param_grid)` | Búsqueda en cuadrícula | Unidad IX avanzada |
| `explain_prediction(features, model)` | Explicación local LIME/SHAP | Fuera del alcance |
| `online_learning(model, new_X, new_y)` | Actualización incremental del modelo en tiempo de ejecución | Fuera del alcance |
| `neural_net(X, y, layers)` | MLP simple vía scikit-learn | Extensión de la Unidad IX |

---
## 🔗 Documentos relacionados

- [[11_FILTER_TOOLS_SPEC.md|Especificación de FilterTools]]
- [[12_VISION_TOOLS_SPEC.md|Especificación de VisionTools]]
