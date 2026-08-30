"""
`cvcourse` — la capa puente entre el curso de visión y el motor Legacy of InFest.

El curso **consume** el motor; no lo modifica. Este paquete es el único sitio
donde el material sabe que el motor existe, para que un cambio en el motor se
arregle en un fichero y no en veinte ejemplos.

Los módulos están en dos grupos, y la diferencia importa:

**Funcionan en cualquier parte** (NumPy, OpenCV, scikit-image, Matplotlib), por
lo que los notebooks de Colab siguen siendo ejecutables sin clonar el
repositorio:

* `synthetic` — piezas industriales sintéticas, deterministas, con verdad-terreno.
* `features`  — de una máscara a `features.csv` (Clase 3).
* `viz`       — figuras: rejillas, histogramas, matrices de confusión.

**Necesitan el repositorio del motor:**

* `engine_bridge` — Surface ⇄ ndarray, recursos de `assets/`, captura de
  fotogramas reales de las escenas-laboratorio.
* `acquisition`   — fuentes de imagen; `FuenteMotor` cae en este grupo, el
  resto no.
* `course_mode`   — abre las Unidades VII–IX en un perfil de progreso aislado.

`engine_bridge.hay_motor()` responde a esa pregunta antes de importar nada, que
es lo que permite al material degradar en vez de fallar en la tercera celda.

Los submódulos no se importan aquí a propósito: importar `cvcourse` no debe
arrastrar pygame ni Matplotlib. Un notebook que sólo usa `synthetic` no tiene
por qué pagar el arranque de pygame ni fallar si no está.
"""
from __future__ import annotations

__all__ = [
    "acquisition",
    "course_mode",
    "engine_bridge",
    "features",
    "synthetic",
    "viz",
]

__version__ = "0.1.0"
