"""AUD-458 — el kernel JIT de numba se compilaba en mitad de la partida.

`_update_particles_njit` se compila en la primera llamada con partículas
vivas. En el flujo normal lo paga la splash (AUD-082); en `--stage` y `--boss`
no hay splash, y el primer golpe —o las partículas ambientales del primer
fotograma— pagaban la compilación: medido, 1,1 s de fotograma congelado en la
máquina de auditoría con la caché fría, 0,3-0,5 s en la de estudiante.

App debe precalentar el kernel al arrancar, **antes** de su primer uso, para
que ningún flujo de entrada pueda reintroducir el cuelgue: si el calentador
vive en cada flujo, un tercer flujo lo vuelve a perder; si vive en App, no.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def test_app_precalienta_particulas_al_arrancar(monkeypatch) -> None:
    from src.engine.core.app import App
    from src.framework.vfx import particle_system

    llamadas: list[int] = []

    def falso() -> float:
        llamadas.append(1)
        return 0.0

    monkeypatch.setattr(particle_system, "warmup", falso)
    App(use_gl=False)
    assert llamadas, (
        "App arranca sin precalentar el kernel de partículas: el primer "
        "golpe seguirá pagando la compilación de numba"
    )