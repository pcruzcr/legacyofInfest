"""
El único módulo del curso que sabe que el motor existe.

Por qué está aislado
--------------------
El curso consume el motor; no lo modifica. Si cada ejemplo tuviera su propia
copia de «cómo convierto una Surface en un ndarray», la primera vez que el
motor cambiara algo se romperían veinte ficheros a la vez y en silencio —
en silencio porque una conversión mal hecha no lanza excepción: devuelve una
imagen girada y el laboratorio sigue «funcionando» con resultados absurdos.

Todo lo que el curso necesita del motor pasa por aquí. Si el motor cambia, se
arregla en este fichero.

El detalle que rompe a todo el mundo
------------------------------------
``pygame.surfarray.array3d`` devuelve la matriz en **(ancho, alto, 3)**, no en
(alto, ancho, 3). El resto del mundo — NumPy, OpenCV, scikit-image,
Matplotlib — trabaja en (filas, columnas), es decir (alto, ancho). Mezclar los
dos convenios no da error: da una imagen transpuesta, y con imágenes cuadradas
—que es justo el caso de los sprites de 32×32— **ni siquiera se nota a simple
vista**. Lo que se nota es que Sobel encuentra los bordes verticales donde
estaban los horizontales, y nadie entiende por qué.

`superficie_a_array` y `array_a_superficie` hacen esa transposición y son la
razón principal de que este módulo exista.
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

__all__ = [
    "CATEGORIAS_DE_RECURSO",
    "array_a_superficie",
    "capturar_escena",
    "cargar_imagen",
    "hay_motor",
    "iniciar_pygame_headless",
    "raiz_del_repositorio",
    "recursos",
    "superficie_a_array",
]


# ── Localizar el repositorio ──────────────────────────────────────────────

@lru_cache(maxsize=1)
def raiz_del_repositorio() -> Path:
    """La raíz del repositorio del motor, subiendo desde este fichero.

    Se busca por marcadores en lugar de contar directorios con `parent.parent`
    porque el curso se ejecuta desde sitios muy distintos —la raíz, la carpeta
    del notebook, un `pytest` lanzado desde cualquier parte— y un número fijo
    de saltos sólo acierta desde uno de ellos.
    """
    aqui = Path(__file__).resolve()
    for candidato in aqui.parents:
        if (candidato / "src" / "engine").is_dir() and (candidato / "assets").is_dir():
            return candidato
    # Sin motor (por ejemplo, en Colab con sólo el paquete copiado). Se
    # devuelve algo coherente en lugar de reventar: los módulos que no
    # necesitan el motor —synthetic, features, viz— tienen que seguir
    # funcionando.
    return aqui.parents[2]


def hay_motor() -> bool:
    """¿Está disponible el repositorio del motor?

    Los notebooks se ejecutan en Colab sin el repositorio clonado. Preguntar
    antes de importar permite que el material degrade a datos sintéticos en
    vez de fallar en la tercera celda.
    """
    raiz = raiz_del_repositorio()
    return (raiz / "src" / "engine").is_dir() and (raiz / "assets").is_dir()


def _asegurar_importable() -> None:
    """Pone la raíz del repositorio en `sys.path` si no estaba."""
    raiz = str(raiz_del_repositorio())
    if raiz not in sys.path:
        sys.path.insert(0, raiz)


# ── Arranque sin pantalla ─────────────────────────────────────────────────

_pygame_listo = False


def iniciar_pygame_headless() -> None:
    """Inicializa pygame sin ventana. Idempotente.

    Las variables de entorno se fijan **antes** de importar pygame porque SDL
    elige el controlador de vídeo al inicializarse y luego no lo cambia. Puesto
    después, el `dummy` no tiene ningún efecto y el proceso intenta abrir una
    ventana real: en CI eso es un fallo, y en la máquina del estudiante es una
    ventana negra que aparece y desaparece en cada celda del notebook.
    """
    global _pygame_listo
    if _pygame_listo:
        return

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

    import pygame

    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()
    if pygame.display.get_surface() is None:
        # Varias utilidades del motor llaman a `convert_alpha()`, que exige un
        # modo de vídeo activo aunque no se vaya a mostrar nada.
        pygame.display.set_mode((800, 600))

    _pygame_listo = True


# ── Conversión Surface ⇄ ndarray ──────────────────────────────────────────

def superficie_a_array(superficie) -> np.ndarray:
    """`pygame.Surface` → `ndarray` RGB de forma **(alto, ancho, 3)**, uint8.

    La transposición del eje 0 con el 1 es obligatoria: ver la cabecera del
    módulo. El resultado sigue el convenio de NumPy/OpenCV/scikit-image, que es
    el que usan todas las bibliotecas del curso.
    """
    import pygame.surfarray

    arreglo = pygame.surfarray.array3d(superficie)   # (ancho, alto, 3)
    return np.ascontiguousarray(arreglo.transpose(1, 0, 2))  # (alto, ancho, 3)


def array_a_superficie(imagen: np.ndarray):
    """`ndarray` RGB (alto, ancho, 3) → `pygame.Surface`. Inversa de la anterior."""
    import pygame.surfarray

    imagen = np.asarray(imagen)
    if imagen.ndim == 2:
        # Una imagen en gris se replica a tres canales: pygame no tiene
        # superficies de un solo canal, y devolver algo que el resto del curso
        # no puede dibujar sería peor que gastar la memoria.
        imagen = np.repeat(imagen[:, :, None], 3, axis=2)
    if imagen.dtype != np.uint8:
        imagen = np.clip(imagen, 0, 255).astype(np.uint8)
    return pygame.surfarray.make_surface(imagen.transpose(1, 0, 2))


# ── Recursos del motor ────────────────────────────────────────────────────

#: Categorías de recurso que el curso usa como imágenes de partida.
CATEGORIAS_DE_RECURSO: dict[str, str] = {
    "sprites": "assets/sprites",
    "fondos": "assets/backgrounds",
    "tilesets": "assets/tilesets",
    "interfaz": "assets/ui",
}


def recursos(categoria: str = "sprites") -> list[Path]:
    """Los PNG del motor de una categoría, ordenados.

    Ordenados a propósito: `glob` no garantiza orden, y un laboratorio en el
    que «la imagen 3» es distinta en cada máquina no se puede corregir.
    """
    if categoria not in CATEGORIAS_DE_RECURSO:
        opciones = ", ".join(sorted(CATEGORIAS_DE_RECURSO))
        raise ValueError(f"categoría desconocida: {categoria!r}. Usa una de: {opciones}")
    carpeta = raiz_del_repositorio() / CATEGORIAS_DE_RECURSO[categoria]
    if not carpeta.is_dir():
        return []
    return sorted(carpeta.rglob("*.png"))


def cargar_imagen(ruta: str | Path, tamano: tuple[int, int] | None = None) -> np.ndarray:
    """Carga un PNG del motor como `ndarray` RGB (alto, ancho, 3).

    Se carga con pygame y no con OpenCV a propósito: es la misma ruta de código
    que usa el juego, así que lo que ve el estudiante en el laboratorio es
    exactamente lo que ve el motor al dibujar. Cargar con `cv2.imread` daría
    además BGR, y esa confusión merece explicarse una vez (`acquisition.py`),
    no arrastrarse por todo el curso.
    """
    iniciar_pygame_headless()
    import pygame

    ruta = Path(ruta)
    if not ruta.is_absolute():
        ruta = raiz_del_repositorio() / ruta
    if not ruta.exists():
        raise FileNotFoundError(f"no existe el recurso: {ruta}")

    superficie = pygame.image.load(str(ruta)).convert_alpha()
    if tamano is not None:
        superficie = pygame.transform.smoothscale(superficie, tamano)
    return superficie_a_array(superficie)


# ── Captura de fotogramas de una escena del motor ─────────────────────────

class _EntradaInerte:
    """Gestor de entrada que **no pulsa nada**.

    Deliberadamente explícito en lugar de un `MagicMock`: un doble permisivo
    devuelve un objeto verdadero para cualquier método que no se haya
    configurado, así que una escena que pregunte `is_action_just_pressed(...)`
    recibiría «sí» sin que nadie haya pulsado nada, y la captura saldría con la
    escena en un modo aleatorio. Es la misma trampa que documenta
    `tests/test_demo_scenes.py`.
    """

    def is_action_just_pressed(self, *_a: object, **_k: object) -> bool:
        return False

    is_action_pressed = is_action_just_pressed
    is_action_held = is_action_just_pressed
    is_raw_key_pressed = is_action_just_pressed

    def get_axis(self, *_a: object, **_k: object) -> float:
        return 0.0

    def update(self, *_a: object, **_k: object) -> None:
        return None


class _AudioMudo:
    """Audio que no suena. La captura es headless; el sonido sólo estorbaría."""

    def __getattr__(self, _nombre: str):
        def _nada(*_a: object, **_k: object) -> None:
            return None
        return _nada


class _PilaDeEscenasInmovil:
    """Pila que ignora los cambios de escena.

    Si la escena capturada decidiera volver al menú a mitad de la captura, sin
    esto se llevaría por delante el resto de fotogramas.
    """

    def push(self, *_a: object, **_k: object) -> None:
        return None

    replace = push
    pop = push


def capturar_escena(
    clave: str,
    fotogramas: int = 1,
    dt: float = 1.0 / 60.0,
    fotogramas_de_asentamiento: int = 3,
) -> list[np.ndarray]:
    """Ejecuta una escena-laboratorio del motor y devuelve sus fotogramas.

    `clave` es la del registro de escenas: ``"filter"`` (Unidad VII),
    ``"vision"`` (VIII), ``"pattern"`` (IX), y las demás de
    `src/engine/scenes/scene_registry.py`.

    Esto es lo que cierra el hueco H2 del análisis: el gestor de fuentes de las
    escenas de demostración ofrece una fuente llamada «Live Capture
    (unavailable)» que es un rectángulo gris. Aquí los fotogramas del motor son
    reales, y sirven para construir el dataset del videojuego de las Clases 3
    y 4.

    No se arranca `App`: se construye la escena con un contexto mínimo y se la
    hace avanzar por su bucle público `update()`/`draw()`. Es el mismo patrón
    que ya usa `tests/test_demo_scenes.py`, y evita abrir contexto GL, mezclador
    de audio y bucle de eventos para tomar una foto.

    Los `fotogramas_de_asentamiento` iniciales se descartan porque casi todas
    las escenas colocan la interfaz en el primer `update()`: el fotograma 0
    suele salir a medio dibujar.
    """
    if fotogramas < 1:
        raise ValueError(f"fotogramas debe ser >= 1, no {fotogramas}")
    if not hay_motor():
        raise RuntimeError(
            "capturar_escena necesita el repositorio del motor. "
            "En Colab sin repositorio, usa cvcourse.synthetic."
        )

    _asegurar_importable()
    iniciar_pygame_headless()

    import pygame
    from src.engine.core import settings
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.scenes.scene_registry import get_registry, register_demo_scenes

    register_demo_scenes()
    registro = get_registry()
    if clave not in registro.keys:
        disponibles = ", ".join(sorted(registro.keys))
        raise ValueError(f"escena desconocida: {clave!r}. Disponibles: {disponibles}")

    contexto = GameContext(
        input_manager=_EntradaInerte(),      # type: ignore[arg-type]
        audio_manager=_AudioMudo(),          # type: ignore[arg-type]
        scene_manager=_PilaDeEscenasInmovil(),  # type: ignore[arg-type]
        event_bus=EventBus(),
    )

    escena = registro.build(clave, contexto)
    if escena is None:
        raise RuntimeError(f"el registro no pudo construir la escena {clave!r}")

    # Mismo orden que `SceneManager.push`: awake → start → on_enter.
    escena.awake()
    escena.start()
    escena.on_enter()

    lienzo = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    capturas: list[np.ndarray] = []
    try:
        for _ in range(fotogramas_de_asentamiento):
            escena.update(dt)
        for _ in range(fotogramas):
            escena.update(dt)
            lienzo.fill(settings.BG_COLOR)
            escena.draw(lienzo)
            capturas.append(superficie_a_array(lienzo))
    finally:
        escena.on_exit()

    return capturas
