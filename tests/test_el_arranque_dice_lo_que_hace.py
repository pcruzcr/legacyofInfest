"""AUD-449 — el arranque se quedaba en blanco y luego «pensando».

Dos cosas distintas, medidas las dos.

**La ventana en blanco.** `App.__init__` monta los subsistemas —plugins,
audio, GL, registro de entidades, escenas— y sólo al final empuja la primera
escena. Medido en la máquina de auditoría: 1.986 ms entre abrir la ventana y
tener algo que dibujar, más los imports. El jugador mira una ventana sin
pintar durante ese tiempo y no sabe si el juego arrancó.

**El congelado.** El precalentado de AUD-082 compila el núcleo de partículas y
carga scikit-learn durante la pantalla de inicio, un paso por fotograma. En el
registro del dueño: **1.890 ms y 3.005 ms**. El paso corre en `update()` y el
dibujo va **después**, así que durante esos segundos la pantalla enseña el
fotograma *anterior* — sin barra que avance, sin texto, sin nada. Se ve como
un cuelgue.

Lo que cambia
-------------
El paso se **anuncia un fotograma antes de ejecutarse**. Así, mientras el
proceso está bloqueado compilando, lo que hay en pantalla ya dice qué está
haciendo. No acelera nada: convierte una congelación muda en una espera
explicada, que es la diferencia entre «se colgó» y «está cargando».

Y `App` pinta un primer fotograma en cuanto existe la ventana, antes de
montar nada, para que no haya ningún instante sin imagen.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core import settings


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    yield


@pytest.fixture
def splash(_video):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.engine.scenes.splash_scene import SplashScene

    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    escena = SplashScene(ctx)
    escena.on_enter()
    return escena


class TestElPasoSeAnunciaAntes:
    def test_al_principio_no_hay_nada_que_anunciar(self, splash) -> None:
        assert splash.tarea_en_curso == ""

    def test_se_anuncia_antes_de_ejecutarse(self, splash) -> None:
        """El punto entero del arreglo.

        Si el anuncio llegara **después** del paso, se dibujaría cuando el
        bloqueo ya terminó: el jugador vería el texto justo cuando deja de
        hacer falta.
        """
        hechos: list[str] = []
        splash._precalentar_particulas = lambda: hechos.append("particulas")
        splash._precalentar_ia = lambda: hechos.append("ia")

        for _ in range(10):
            antes = list(hechos)
            splash.update(1 / 60)
            if splash.tarea_en_curso and not antes:
                # Se anunció algo y todavía no se ha ejecutado nada: correcto.
                assert hechos == [], (
                    "el paso se ejecutó en el mismo fotograma en que se "
                    "anunció: durante el bloqueo la pantalla no lo dirá"
                )
                break
        else:
            pytest.fail("nunca se anunció ninguna tarea")

    def test_todos_los_pasos_acaban_ejecutandose(self, splash) -> None:
        """Anunciar no puede convertirse en no hacer."""
        hechos: list[str] = []
        splash._precalentar_particulas = lambda: hechos.append("particulas")
        splash._precalentar_ia = lambda: hechos.append("ia")

        for _ in range(60):
            splash.update(1 / 60)
        assert hechos == ["particulas", "ia"], f"se ejecutaron {hechos}"

    def test_al_terminar_no_queda_anuncio_colgado(self, splash) -> None:
        splash._precalentar_particulas = lambda: None
        splash._precalentar_ia = lambda: None
        for _ in range(60):
            splash.update(1 / 60)
        assert splash.tarea_en_curso == ""


class TestLaPantallaLoDice:
    def test_el_anuncio_se_dibuja(self, splash) -> None:
        """Sin esto el anuncio sería una variable que nadie ve."""
        splash._precalentar_particulas = lambda: None
        splash._precalentar_ia = lambda: None

        superficie = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        for _ in range(10):
            splash.update(1 / 60)
            if splash.tarea_en_curso:
                break
        antes = superficie.copy()
        splash.draw(superficie)
        assert pygame.image.tobytes(superficie, "RGB") != pygame.image.tobytes(
            antes, "RGB"), "la pantalla de inicio no dibujó nada"

    def test_el_texto_esta_en_espanol(self, splash) -> None:
        for _ in range(10):
            splash.update(1 / 60)
            if splash.tarea_en_curso:
                break
        assert splash.tarea_en_curso, "no se anunció nada"
        bajo = splash.tarea_en_curso.lower()
        for ingles in ("loading", "warming", "compiling", "please wait"):
            assert ingles not in bajo, f"el anuncio está en inglés: {bajo!r}"
