"""AUD-498 — un golpe que acertaba congelaba el juego para siempre.

El síntoma, reportado jugando el Stage 0: *«el enemy ataca y toca, o el
player hace un ataque corto, y el juego se freezea»*. Las dos cosas tienen
en común una sola: el golpe **conecta**.

La cadena
=========
1. Un golpe que acierta llama a `CollisionSystem.trigger_hitstop`, que pone
   `time_scale` a **0.0** para vender el impacto.
2. `App` simula con pasos fijos (AUD-390)::

       for paso in self.clock.pasos_fijos():
           self.scene_manager.update(paso)

3. `pasos_fijos()` acumula el delta **escalado** (`clock.py:208`). Con
   `time_scale` a 0.0 el acumulado no crece nunca, así que no emite ni un
   paso y `scene_manager.update()` **no se llama**.
4. Y `update_hitstop()` —lo único que vuelve a poner el reloj en marcha—
   vive dentro de ese `update`.

Nadie queda para soltar el freno. El juego no se cuelga: sigue dibujando y
respondiendo a eventos, simplemente no vuelve a simular jamás.

Por qué las defensas existentes no bastaron
===========================================
`update_hitstop` recibe el delta **sin escalar** justo para que esto no
pase — AUD-001 lo documenta con estas palabras: *«pasar el delta escalado
reintroduce AUD-001... el juego se congela permanentemente al primer golpe
que acierta»*. Esa defensa es correcta y sigue estándo. Sólo que da igual
recibir un delta bueno si a la función no la llama nadie.

Y la cámara lenta no lo destapó: con `time_scale` a 0,35 los pasos siguen
llegando, sólo que menos. **0.0 es el único valor que rompe el bucle**, y es
exactamente el que usa el hit-stop.

La forma correcta ya estaba en el mismo fichero
===============================================
Tres líneas más abajo, `App` ya trata las transiciones como lo que son::

    # Las transiciones van con el tiempo del fotograma y **no** en pasos
    # fijos: son presentación, no simulación.
    self.scene_manager.transition.update(dt)

El hit-stop es de esa familia: no es simulación, es la contabilidad que
decide cuánto dura la pausa. Va con el reloj real, fuera del acumulador.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from src.engine.core.clock import DeltaClock


class TestElAcumuladorSeQuedaSeco:
    """La mecánica del atasco, aislada del juego."""

    def test_a_escala_cero_no_sale_ni_un_paso(self) -> None:
        reloj = DeltaClock()
        reloj.escalar("hitstop", 0.0)
        for _ in range(10):
            assert list(reloj.pasos_fijos(0.0)) == []

    def test_a_camara_lenta_si_salen_pasos(self) -> None:
        """Por esto no se detectó antes: 0,35 funciona, 0.0 no."""
        reloj = DeltaClock()
        reloj.escalar("bala", 0.35)
        dados = 0
        for _ in range(60):
            dados += len(list(reloj.pasos_fijos(1 / 60 * 0.35)))
        assert dados > 0, "la cámara lenta tampoco simula: el fallo sería otro"


class TestElHitstopSeSueltaSolo:
    """Lo que de verdad importa: que el juego vuelva."""

    def _escena_con_hitstop(self):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.stage0.stage0 import Stage0

        import pygame

        pygame.init()
        pygame.font.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))

        entity_factory.ensure_registered()
        reloj = DeltaClock()
        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=reloj,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        escena = Stage0(ctx)
        ctx.scene_manager.push(escena)
        return ctx, escena, reloj

    def test_el_juego_vuelve_despues_de_un_golpe(self) -> None:
        """Reproduce el bucle de `App`: pasos fijos con el delta escalado,
        que es donde se pierde el hit-stop."""
        ctx, escena, reloj = self._escena_con_hitstop()
        try:
            escena._collision.trigger_hitstop(0.08)
            assert reloj.time_scale in (1.0, 0.0)

            for _ in range(120):  # dos segundos de juego real
                # Exactamente lo que hace `App`, en el mismo orden.
                ctx.scene_manager.actualizar_en_tiempo_real(1 / 60)
                for paso in reloj.pasos_fijos(reloj.time_scale * (1 / 60)):
                    ctx.scene_manager.update(paso)

            assert not escena._collision.is_hitstopped, (
                "el hit-stop no se soltó en dos segundos: el juego se quedó "
                "congelado en el primer golpe que acertó"
            )
            assert reloj.time_scale == pytest.approx(1.0), (
                f"el reloj se quedó en {reloj.time_scale}"
            )
        finally:
            escena.on_exit()

    def test_la_pausa_dura_de_verdad(self) -> None:
        """Soltarlo enseguida seria la otra forma de romperlo: el impacto
        dejaria de notarse."""
        ctx, escena, reloj = self._escena_con_hitstop()
        try:
            escena._collision.trigger_hitstop(0.08)
            ctx.scene_manager.actualizar_en_tiempo_real(1 / 120)
            assert escena._collision.is_hitstopped, (
                "el hit-stop se solto en el primer fotograma: no hay impacto "
                "que vender"
            )
        finally:
            escena.on_exit()


class TestElGanchoDeTiempoRealExiste:
    """La pieza que faltaba, comprobada por separado para que un fallo diga
    dónde está."""

    def test_el_gestor_de_escenas_lo_ofrece(self) -> None:
        from src.engine.scene.scene_manager import SceneManager

        assert hasattr(SceneManager, "actualizar_en_tiempo_real")

    def test_toda_escena_lo_acepta(self) -> None:
        """Las 26 entregas heredan de `BaseScene`: si el gancho no tuviera
        una implementación por defecto, el bucle reventaría en cualquiera que
        no lo sobreescriba."""
        from src.engine.scene.base_scene import BaseScene

        assert hasattr(BaseScene, "actualizar_en_tiempo_real")

    def test_el_bucle_del_juego_lo_llama_fuera_de_los_pasos_fijos(self) -> None:
        """Dentro del `for` no serviría de nada: es justo el bucle que no se
        ejecuta."""
        import inspect

        from src.engine.core.app import App

        fuente = inspect.getsource(App.run)
        assert "actualizar_en_tiempo_real" in fuente, (
            "el bucle no llama al gancho de tiempo real"
        )
        # Se comparan las **llamadas**, no la primera vez que aparece el
        # nombre: el comentario que explica el arreglo menciona
        # `pasos_fijos()` antes de que el bucle lo use.
        pos_gancho = fuente.index("self.scene_manager.actualizar_en_tiempo_real")
        pos_pasos = fuente.index("for paso in self.clock.pasos_fijos()")
        assert pos_gancho < pos_pasos, (
            "el gancho se llama después de los pasos fijos; tiene que correr "
            "aunque no haya ni un paso"
        )
