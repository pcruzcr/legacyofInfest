"""
Las tres filas que quedaban del registro — AUD-146/148 y el clima mudo.

* **`ParamPanel`** llevaba meses escrito sin que ninguna demo lo instanciara.
  Ahora lo usa la vista de árbol de la demo de patrones.
* **Post-procesado en GPU**: medido, y en esta máquina sale PEOR. Lo que se
  entrega es la medición y una pieza opcional, no una promesa.
* **El clima sonaba en silencio**: el código pedía
  `assets/sfx/ambient/{rain,wind,storm}.wav` y esa carpeta no existe.

Lo que une a los tres
----------------------
Los tres eran silencios. Un widget que nadie construye, una fila de tabla que
nadie mide y un `if ruta.exists()` que devuelve falso desde hace meses no
fallan nunca: simplemente no hacen nada, y nadie se entera.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class TestElPanelDeParametrosEstaEnchufado:
    """AUD-146. La clase funcionaba; lo que faltaba era alguien que la usara."""

    def test_alguna_demo_lo_construye(self) -> None:
        import inspect

        from src.engine.scenes import pattern_demo_scene

        fuente = inspect.getsource(pattern_demo_scene)
        assert "ParamPanel()" in fuente, (
            "ninguna demo instancia el panel: sigue siendo un huérfano"
        )

    def test_el_panel_de_la_demo_tiene_su_parametro(self) -> None:
        from src.engine.scenes.param_panel import ParamPanel

        panel = ParamPanel()
        panel.add_int("Max Depth", 2, 0, 6)
        assert panel["Max Depth"] == 2

    def test_ajustar_respeta_los_limites(self) -> None:
        """Lo que cada demo se hacía a mano, cuatro veces, cada una con sus
        propios límites escritos otra vez."""
        from src.engine.scenes.param_panel import ParamPanel

        panel = ParamPanel()
        panel.add_int("Max Depth", 0, 0, 6)
        panel.adjust_selected(-1)
        assert panel["Max Depth"] == 0, "se pasó por debajo del mínimo"
        for _ in range(20):
            panel.adjust_selected(1)
        assert panel["Max Depth"] == 6, "se pasó por encima del máximo"

    def test_avisa_del_cambio(self) -> None:
        from src.engine.scenes.param_panel import ParamPanel

        vistos = []
        panel = ParamPanel()
        panel.add_int("X", 1, 0, 9, on_change=vistos.append)
        panel.adjust_selected(1)
        assert vistos == [2]

    def test_la_demo_sigue_leyendo_su_propio_campo(self) -> None:
        """El panel edita; `_tree_depth` sigue siendo el dato que se dibuja.
        Así el resto de la escena no se entera de que hay un panel."""
        import inspect

        from src.engine.scenes.pattern_demo_scene import PatternDemoScene

        fuente = inspect.getsource(PatternDemoScene)
        assert "_al_cambiar_profundidad" in fuente
        assert "self._tree_depth = int(valor)" in fuente


class TestElClimaYaNoSuenaEnSilencio:
    """El `.exists()` que convertía un fallo de integración en silencio."""

    def _clima(self, nombre: str):
        from src.framework.vfx.weather_system import WeatherSystem

        sistema = WeatherSystem()
        sistema.set_climate(nombre)
        return sistema

    def test_la_ruta_que_devuelve_existe_de_verdad(self) -> None:
        from src.engine.core import settings
        from src.framework.vfx.weather_system import WeatherSystem

        for clima, ruta in WeatherSystem.AMBIENTES.items():
            if ruta is None:
                continue
            assert (settings.ASSETS_DIR / ruta).exists(), (
                f"el clima {clima!r} apunta a {ruta}, que no está en el disco: "
                f"volvería a sonar en silencio"
            )

    def test_despejado_no_suena_y_es_correcto(self) -> None:
        assert self._clima("clear").get_ambient_audio_key() is None
        assert self._clima("clear").falta_su_ambiente() is False

    def test_la_niebla_suena(self) -> None:
        assert self._clima("fog").get_ambient_audio_key() is not None

    def test_la_lluvia_declara_que_le_falta_el_fichero(self) -> None:
        """`None` significa dos cosas y hay que poder distinguirlas: «no debe
        sonar» y «debería sonar y falta el asset». Lo segundo se avisa."""
        lluvia = self._clima("rain")
        assert lluvia.get_ambient_audio_key() is None
        assert lluvia.falta_su_ambiente() is True

    def test_la_escena_avisa_en_vez_de_callarse(self) -> None:
        import inspect

        from src.framework.scenes import stage_scene

        fuente = inspect.getsource(stage_scene)
        assert "falta_su_ambiente" in fuente, (
            "la escena no consulta la carencia: el clima volvería a ser mudo "
            "sin que nadie se entere"
        )


class TestLaGpuSeMideAntesDePrometer:
    """AUD-148 — la fila del registro daba por hecho que la GPU aceleraría."""

    def test_el_banco_de_pruebas_existe(self) -> None:
        from pathlib import Path

        raiz = Path(__file__).resolve().parent.parent
        assert (raiz / "scripts" / "bench_gpu_postproc.py").exists(), (
            "sin banco de pruebas, «la GPU es más rápida» es una creencia"
        )

    def test_el_modulo_dice_lo_que_midio(self) -> None:
        from src.engine.render import gpu_present

        doc = gpu_present.__doc__ or ""
        assert "más lento" in doc, (
            "el módulo no cuenta que en la máquina de medida la GPU salió "
            "peor, y alguien lo enchufará esperando lo contrario"
        )

    def test_y_dice_lo_que_no_se_puede(self) -> None:
        from src.engine.render import gpu_present

        assert "daltonismo" in (gpu_present.__doc__ or "")

    def test_presentar_funciona_donde_hay_sdl2(self) -> None:
        """Sin `skipif` a nivel de módulo.

        La primera versión llevaba `@pytest.mark.skipif(not pygame.get_init())`,
        y esa condición se evalúa al RECOGER las pruebas —antes de que la
        fixture inicialice pygame—, así que la prueba se saltaba siempre. Una
        prueba que nunca corre es peor que no tenerla: ocupa sitio y da
        confianza.
        """
        from src.engine.render.gpu_present import PresentadorGPU, hay_soporte

        if not hay_soporte():
            pytest.skip("esta instalación no trae pygame._sdl2")
        presentador = PresentadorGPU((160, 120), titulo="prueba")
        try:
            lienzo = pygame.Surface((160, 120))
            lienzo.fill((30, 90, 150))
            presentador.presentar(lienzo)      # no debe lanzar
            assert presentador.tamano == (160, 120)
        finally:
            presentador.cerrar()

    def test_no_esta_enchufado_en_el_bucle(self) -> None:
        """Y es deliberado: un `_sdl2.Window` y el display clásico no conviven
        en la misma ventana, así que enchufarlo obliga a reescribir el
        escalado, las transiciones y el volcado de las quince entregas."""
        import inspect

        from src.engine.core import app

        assert "PresentadorGPU" not in inspect.getsource(app)
