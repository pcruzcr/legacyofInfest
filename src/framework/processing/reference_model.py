"""
Module: reference_model
System: framework.processing
Academic Unit: Unidad IX — Reconocimiento de patrones

El modelo de referencia, reentrenado en la máquina de quien juega.

F3.3 — el problema que esto resuelve
------------------------------------
`assets/models/professor_sample.pkl` se entrenó con scikit-learn 1.9.0. Al
cargarlo con cualquier otra versión, la propia biblioteca avisa:

    InconsistentVersionWarning: Trying to unpickle estimator KNeighborsClassifier
    from version 1.9.0 when using version 1.7.2. This might lead to breaking
    code or invalid results.

«Invalid results», no «puede fallar». Un estudiante con otra versión de
scikit-learn obtiene del laboratorio de la Unidad IX predicciones distintas de
las de su compañero, **sin ninguna señal en pantalla**. Un laboratorio que da
resultados distintos según la máquina no es un laboratorio.

Y hay un segundo problema, más grave y ya documentado en `load_model`:
`joblib.load` es `pickle` por debajo, y deserializar ejecuta código arbitrario.
En un aula ese archivo se copia entre máquinas, se manda por correo y se
entrega como práctica.

La solución es la que ya proponía `scripts/train_reference_model.py` y que
nadie había conectado al juego: **no distribuir el estimador, distribuir los
datos y el guion**. Este módulo entrena el modelo al vuelo desde
`assets/datasets/sample_dataset.npz` y lo guarda en la caché local del usuario.

Consecuencias, que conviene tener claras:

* La primera ejecución cuesta unos segundos más. Se paga una vez por máquina.
* El modelo que se carga lo generó **tu** scikit-learn, así que no hay aviso de
  versión ni resultados dudosos.
* Nadie deserializa un binario que no haya producido su propia máquina.
* Si el `.npz` cambia, la caché se invalida sola: la clave incluye su hash.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_RAIZ = Path(__file__).resolve().parent.parent.parent.parent
DATASET = _RAIZ / "assets" / "datasets" / "sample_dataset.npz"

#: Tipo de modelo y descriptor. Coinciden con los valores por defecto de
#: `scripts/train_reference_model.py`, para que entrenar a mano y entrenar
#: desde el juego den lo mismo.
TIPO_MODELO = "knn"
METODO_DESCRIPTOR = "hog"


def _directorio_cache() -> Path:
    """Dónde guardar el modelo entrenado en esta máquina.

    Va al directorio de datos del usuario y no al repositorio: es un artefacto
    derivado y específico de una versión de biblioteca, así que no debe
    versionarse ni compartirse. Ése era justo el problema original.
    """
    import os

    base = os.environ.get("XDG_CACHE_HOME") or os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "legacy_of_infest" / "models"
    return Path.home() / ".cache" / "legacy_of_infest" / "models"


def _clave_cache() -> str:
    """Identifica dataset + versión de sklearn + configuración.

    Si cambia cualquiera de los tres, el modelo cacheado deja de valer y se
    reentrena solo. Sin esto, actualizar scikit-learn devolvería el problema
    original por la puerta de atrás.
    """
    try:
        import sklearn
        version = sklearn.__version__
    except ImportError:
        version = "sin-sklearn"

    try:
        digest = hashlib.sha256(DATASET.read_bytes()).hexdigest()[:16]
    except OSError:
        digest = "sin-datos"

    return f"{TIPO_MODELO}-{METODO_DESCRIPTOR}-{version}-{digest}"


def ruta_cacheada() -> Path:
    return _directorio_cache() / f"referencia-{_clave_cache()}.pkl"


def obtener_modelo(forzar: bool = False):
    """Devuelve el modelo de referencia, entrenándolo si hace falta.

    Devuelve `None` si no se puede entrenar —sin scikit-learn, sin dataset— en
    lugar de lanzar: el laboratorio tiene que abrirse igual y decir que no hay
    modelo, que es lo que ya sabe hacer.
    """
    from src.framework.processing.pattern_recognition_tools import (
        PatternRecognitionTools,
    )

    destino = ruta_cacheada()
    if destino.exists() and not forzar:
        try:
            return PatternRecognitionTools.load_model(str(destino))
        except Exception as e:
            # Una caché ilegible se vuelve a generar. No es motivo para dejar
            # al estudiante sin laboratorio.
            logger.warning(
                "modelo cacheado ilegible (%s); se reentrena", type(e).__name__)

    modelo = entrenar()
    if modelo is None:
        return None
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        PatternRecognitionTools.save_model(modelo, destino)
    except OSError as e:
        # Sin permiso de escritura se entrena en cada arranque. Es lento pero
        # correcto, que es el orden de prioridades adecuado.
        logger.warning("no se pudo guardar el modelo en %s: %s", destino, e)
    return modelo


def entrenar():
    """Entrena el modelo de referencia desde el dataset del repositorio."""
    try:
        import numpy as np
    except ImportError:
        return None

    if not DATASET.exists():
        logger.warning(
            "no existe %s: el laboratorio de patrones se abrirá sin modelo",
            DATASET,
        )
        return None

    from src.framework.processing.pattern_recognition_tools import (
        PatternRecognitionTools,
    )

    try:
        with np.load(DATASET, allow_pickle=False) as datos:
            X, y = datos["X"], datos["y"]
        return PatternRecognitionTools.train(
            X, y, model_type=TIPO_MODELO, feature_method=METODO_DESCRIPTOR)
    except Exception as e:
        logger.warning("no se pudo entrenar el modelo de referencia: %s", e)
        return None
