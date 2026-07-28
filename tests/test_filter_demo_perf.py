"""
El histograma de la demo de filtros: mismo resultado, una fracción del coste.

AUD-097
=======
`FilterDemoScene` figuraba en la tabla de deuda técnica con «7,8 ms de
mediana, el 47 % del presupuesto de fotograma en una demo». Medido de nuevo
tras ensanchar los paneles en AUD-094, había subido a **10,24 ms de mediana**
y **57 de 180 fotogramas fuera de presupuesto**.

cProfile sobre esos 180 fotogramas señaló un único responsable:
`np.histogram` se llevaba 3,95 s de los 4,41 s del dibujado —el 90 %— porque
se llamaba **seis veces por fotograma** (tres canales por dos paneles) sobre
imágenes que no habían cambiado. Es el mismo defecto que AUD-073 en el
laboratorio de ruido: trabajo caro y determinista repetido sesenta veces por
segundo porque nadie se preguntó cuándo cambia su entrada.

Dos arreglos, y esta prueba vigila los dos:

1. **Caché.** Se recalcula al cambiar de imagen o de filtro, no por fotograma.
2. **`bincount` en vez de `histogram`.** Los datos ya son enteros de 0 a 255;
   no hace falta buscar el hueco de cada valor. El reparto en 80 barras se
   hace con `add.reduceat` sobre cortes calculados con división entera, de
   modo que el resultado es **idéntico** al de `np.histogram` barra por
   barra. Se cambió el coste, no la lección.
"""
from __future__ import annotations

import statistics
import time

import numpy as np
import pygame
import pytest

from src.engine.core import settings

#: Presupuesto de fotograma a 60 fps.
_PRESUPUESTO_MS = 1000.0 / 60.0
#: Techo que se le exige a esta escena. Holgado respecto a lo medido (0,73 ms)
#: para que la prueba no se vuelva ruidosa en una máquina cargada, y aun así
#: muy por debajo de los 10,24 ms de antes.
_TECHO_MS = 6.0


@pytest.fixture(scope="module")
def pantalla():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    return pygame.display.get_surface()


@pytest.fixture
def escena(pantalla):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.engine.scenes.filter_demo_scene import FilterDemoScene

    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    e = FilterDemoScene(ctx)
    e.awake()
    e.start()
    e.on_enter()
    return e


class TestElHistogramaNoCambioDeResultado:
    """Lo primero: que siga siendo el mismo histograma."""

    @pytest.mark.parametrize("semilla", [3, 11, 29])
    def test_coincide_barra_por_barra_con_numpy(self, pantalla, semilla):
        from src.engine.scenes.filter_demo_scene import FilterDemoScene

        rng = np.random.RandomState(semilla)
        datos = rng.randint(0, 256, (41, 59, 3)).astype(np.uint8)
        superficie = pygame.surfarray.make_surface(datos)

        nuevo = FilterDemoScene._histograma(superficie)
        arr = pygame.surfarray.pixels3d(superficie)
        try:
            esperado = [
                np.histogram(arr[:, :, c], bins=80, range=(0, 256))[0].tolist()
                for c in range(3)
            ]
        finally:
            del arr

        for canal in range(3):
            assert nuevo[canal] == esperado[canal], (
                f"canal {canal}: el histograma rápido no coincide con "
                f"np.histogram. Se cambió el coste, no la lección."
            )

    def test_conserva_el_numero_de_barras(self, pantalla):
        from src.engine.scenes.filter_demo_scene import FilterDemoScene

        datos = np.zeros((8, 8, 3), dtype=np.uint8)
        canales = FilterDemoScene._histograma(pygame.surfarray.make_surface(datos))
        assert all(len(c) == 80 for c in canales)

    def test_cuenta_todos_los_pixeles(self, pantalla):
        from src.engine.scenes.filter_demo_scene import FilterDemoScene

        alto, ancho = 13, 17
        datos = np.full((ancho, alto, 3), 200, dtype=np.uint8)
        canales = FilterDemoScene._histograma(pygame.surfarray.make_surface(datos))
        for canal in canales:
            assert sum(canal) == ancho * alto

    def test_los_extremos_caen_en_la_primera_y_la_ultima_barra(self, pantalla):
        from src.engine.scenes.filter_demo_scene import FilterDemoScene

        datos = np.zeros((4, 4, 3), dtype=np.uint8)
        datos[0, 0] = 0
        datos[1, 1] = 255
        canales = FilterDemoScene._histograma(pygame.surfarray.make_surface(datos))
        assert canales[0][0] > 0, "el nivel 0 no cayó en la primera barra"
        assert canales[0][-1] > 0, "el nivel 255 no cayó en la última barra"


class TestElHistogramaSeCachea:
    def test_no_se_recalcula_si_nada_cambio(self, escena, pantalla):
        """El defecto medido: seis histogramas por fotograma."""
        from src.engine.scenes import filter_demo_scene as mod

        escena.update(1.0 / 60.0)
        escena.draw(pantalla)

        llamadas = {"n": 0}
        original = mod.FilterDemoScene._histograma

        def espia(superficie):
            llamadas["n"] += 1
            return original(superficie)

        mod.FilterDemoScene._histograma = staticmethod(espia)
        try:
            for _ in range(30):
                escena.draw(pantalla)
        finally:
            mod.FilterDemoScene._histograma = staticmethod(original)

        assert llamadas["n"] == 0, (
            f"se recalculó el histograma {llamadas['n']} veces en 30 fotogramas "
            f"sin que cambiara nada. Antes de AUD-097 eran 180."
        )

    def test_se_recalcula_cuando_cambia_la_imagen(self, escena, pantalla):
        escena.update(1.0 / 60.0)
        escena.draw(pantalla)
        antes = escena._hist_firma
        escena._sources.cycle()
        escena._cached_result = None
        escena.update(1.0 / 60.0)
        escena.draw(pantalla)
        assert escena._hist_firma != antes, (
            "la caché no se invalidó al cambiar de imagen: se mostraría el "
            "histograma de la anterior, que es peor que ir lento."
        )


class TestElPresupuestoDeFotograma:
    def test_la_escena_cabe_holgadamente_en_un_fotograma(self, escena, pantalla):
        """10,24 ms de mediana y 57/180 fotogramas fuera, antes de AUD-097."""
        for _ in range(10):
            escena.update(1.0 / 60.0)
            escena.draw(pantalla)

        muestras = []
        for _ in range(120):
            inicio = time.perf_counter()
            escena.update(1.0 / 60.0)
            escena.draw(pantalla)
            muestras.append((time.perf_counter() - inicio) * 1000.0)

        mediana = statistics.median(muestras)
        fuera = sum(1 for m in muestras if m > _PRESUPUESTO_MS)
        assert mediana < _TECHO_MS, (
            f"mediana {mediana:.2f} ms (techo {_TECHO_MS}). Medido antes de "
            f"AUD-097: 10,24 ms."
        )
        assert fuera <= 6, (
            f"{fuera} de 120 fotogramas fuera del presupuesto de "
            f"{_PRESUPUESTO_MS:.2f} ms. Antes eran 57 de 180."
        )
