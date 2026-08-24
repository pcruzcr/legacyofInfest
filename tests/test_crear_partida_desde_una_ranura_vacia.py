"""AUD-443 — una ranura vacía no se podía usar para empezar.

Lo que había
-----------
`LoadGameScene` listaba las cinco ranuras y, al confirmar sobre una vacía,
respondía «Slot vacío — elige un slot con datos». O sea: la pantalla que
existe para elegir partida no dejaba **crear** ninguna. La partida nacía por
el otro camino —el menú de título— y sin nombre, sin personaje y sin decidir
en qué ranura vivía.

Lo que hace ahora
-----------------
Confirmar sobre una ranura vacía entra en modo creación: se escribe un
nombre, se confirma, y ahí es donde el perfil **existe por primera vez** —con
su ranura declarada como la activa, para que el autoguardado siguiente vaya
donde debe (AUD-441).

La risa de Paburu
-----------------
Suena al confirmar el personaje, y suena **una vez**. El encargo pedía
explícitamente vigilar que no se repitiera por fotograma, que es lo que pasa
cuando el disparo cuelga de un estado («¿está seleccionado?») en vez de de
una transición («¿acaba de seleccionarse?»). Aquí cuelga del flanco de
confirmación, y estas pruebas lo fijan corriendo muchos fotogramas seguidos.

El fichero de sonido no existe todavía en `assets/sfx/voz/`. El cableado sí,
y el reproductor ya tolera una muestra ausente sin romper el fotograma: en
cuanto se suelte el `.wav`, suena.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.engine.core.events import Events
from src.engine.core.save_manager import SaveManager


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield


@pytest.fixture
def contexto(_video, tmp_path, monkeypatch):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager

    monkeypatch.setattr(SaveManager, "SAVES_DIR", tmp_path)
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


@pytest.fixture
def pantalla(contexto):
    from src.engine.scenes.load_game_scene import LoadGameScene

    escena = LoadGameScene(contexto)
    escena.awake()
    escena.start()
    escena.on_enter()
    return escena


def _tecla(key: int, unicode: str = "") -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode, mod=0)


def _fotograma(escena, eventos: list[pygame.event.Event] | None = None) -> None:
    """Un fotograma como el del juego: bombear entrada, eventos, actualizar.

    Bombear **siempre**, también sin eventos, no es un detalle del arnés: es
    lo que hace `App._process_events` cada vuelta y es lo que cierra el flanco
    de una tecla. Sin ello `is_action_just_pressed` se queda en `True` para
    siempre y la escena reacciona en bucle a una pulsación que ya pasó — que
    es justo el fallo contra el que existe la prueba de la risa repetida.
    """
    eventos = eventos or []
    escena.context.input_manager.pump(eventos)
    escena.process_events(eventos)
    escena.update(1 / 60)


def _escribir(escena, texto: str) -> None:
    for caracter in texto:
        _fotograma(escena, [_tecla(pygame.K_a, caracter)])


def _confirmar(escena) -> None:
    """Pulsa y **suelta** confirmar, como el jugador.

    Una pulsación real es un KEYDOWN y después fotogramas sin ese evento; el
    segundo fotograma comprueba que la escena no vuelve a reaccionar.
    """
    from src.engine.input.action_map import Action

    im = escena.context.input_manager
    im.pump([_tecla(pygame.K_RETURN)])
    assert im.is_action_just_pressed(Action.CONFIRM), (
        "la prueba no está simulando bien el flanco de confirmación"
    )
    escena.process_events([])
    escena.update(1 / 60)
    # Soltar. Sin el KEYUP la tecla se queda pulsada y una segunda
    # confirmación no genera flanco: el jugador no puede confirmar dos veces
    # seguidas sin levantar el dedo, y la prueba tampoco.
    _fotograma(escena, [pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN, mod=0)])


class TestEntrarEnCreacion:
    def test_confirmar_sobre_una_vacia_abre_la_creacion(self, pantalla) -> None:
        assert not pantalla.creando
        _confirmar(pantalla)
        assert pantalla.creando, (
            "confirmar sobre una ranura vacía seguía diciendo «elige un slot "
            "con datos»: la pantalla de elegir partida no dejaba crear ninguna"
        )

    def test_cancelar_vuelve_a_la_lista_sin_crear_nada(self, pantalla, contexto) -> None:
        _confirmar(pantalla)
        _escribir(pantalla, "Ana")
        _fotograma(pantalla, [_tecla(pygame.K_ESCAPE)])

        assert not pantalla.creando
        assert contexto.save_manager.list_slots() == [], (
            "se creó una partida al cancelar"
        )


class TestEscribirElNombre:
    def test_las_letras_se_acumulan(self, pantalla) -> None:
        _confirmar(pantalla)
        _escribir(pantalla, "Pablo")
        assert pantalla.nombre_en_curso == "Pablo"

    def test_borrar_quita_la_ultima(self, pantalla) -> None:
        _confirmar(pantalla)
        _escribir(pantalla, "Pab")
        _fotograma(pantalla, [_tecla(pygame.K_BACKSPACE)])
        assert pantalla.nombre_en_curso == "Pa"

    def test_el_nombre_tiene_tope(self, pantalla) -> None:
        from src.engine.core.save_data import SaveData

        _confirmar(pantalla)
        _escribir(pantalla, "x" * 200)
        assert len(pantalla.nombre_en_curso) <= SaveData.LARGO_MAXIMO_DEL_NOMBRE

    def test_no_entran_caracteres_de_control(self, pantalla) -> None:
        """`unicode` trae también tabuladores y retornos."""
        _confirmar(pantalla)
        _escribir(pantalla, "A\tB\nC")
        assert pantalla.nombre_en_curso == "ABC"


class TestCrearLaPartida:
    def test_se_crea_en_la_ranura_elegida_y_queda_activa(self, pantalla, contexto) -> None:
        pantalla.seleccionar(2)                 # tercera fila -> ranura 3
        _confirmar(pantalla)
        _escribir(pantalla, "Pablo")
        _confirmar(pantalla)

        gestor = contexto.save_manager
        guardada = gestor.load(3)
        assert guardada is not None, "no se escribió la partida en la ranura 3"
        assert guardada.profile_name == "Pablo"
        assert guardada.character == "paburu"
        assert gestor.ranura_activa == 3, (
            "la partida recién creada no quedó declarada como la que se juega, "
            "así que el autoguardado siguiente iría a otra ranura"
        )

    def test_sin_nombre_no_se_crea(self, pantalla, contexto) -> None:
        """Una partida sin nombre deja la pantalla igual de indistinguible."""
        _confirmar(pantalla)
        _confirmar(pantalla)
        assert pantalla.creando, "se creó una partida con el nombre vacío"
        assert contexto.save_manager.list_slots() == []


class TestLaRisaDePaburu:
    @pytest.fixture
    def risas(self, contexto):
        cuenta = {"n": 0}

        def _oir(**_: object) -> None:
            cuenta["n"] += 1

        contexto.event_bus.subscribe(Events.SFX_VOZ_PABURU, _oir)
        contexto._oir_risa = _oir          # el bus guarda referencias débiles
        return cuenta

    def test_suena_al_confirmar_el_personaje(self, pantalla, contexto, risas) -> None:
        pantalla.seleccionar(0)
        _confirmar(pantalla)
        _escribir(pantalla, "Pablo")
        _confirmar(pantalla)
        contexto.event_bus.dispatch()
        assert risas["n"] == 1

    def test_no_se_repite_fotograma_a_fotograma(self, pantalla, contexto, risas) -> None:
        """La garantía que pedía el encargo.

        Se deja correr un segundo entero **manteniendo** la tecla: si el
        disparo colgara del estado y no del flanco, aquí se oirían sesenta
        risas superpuestas.
        """
        _confirmar(pantalla)
        _escribir(pantalla, "Pablo")
        _confirmar(pantalla)
        for _ in range(60):
            _fotograma(pantalla)
            contexto.event_bus.dispatch()
        assert risas["n"] == 1, f"la risa sonó {risas['n']} veces"

    def test_no_suena_al_navegar_ni_al_escribir(self, pantalla, contexto, risas) -> None:
        _confirmar(pantalla)
        _escribir(pantalla, "Pablo")
        for _ in range(30):
            _fotograma(pantalla)
        contexto.event_bus.dispatch()
        assert risas["n"] == 0
