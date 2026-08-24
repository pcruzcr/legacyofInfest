"""
Las tres ayudas de accesibilidad hacen algo, y se puede comprobar.

AUD-126 — el hallazgo
======================
El proyecto tenía `colorblind_mode` conectado de punta a punta —opciones,
preferencias, post-procesado, sombreador— y ahí se paró. Faltaban las tres
barreras que más gente encuentra en un plataformas, y ninguna existía ni como
preferencia:

* **Texto pequeño.** La resolución interna es 800 × 600 y la tipografía base
  mide 14 px. En cualquier estudio de accesibilidad de videojuegos, «texto más
  grande» es la petición número uno, por delante del daltonismo.
* **Movimiento.** Sacudida de pantalla, estelas y destellos provocan náusea a
  quien tiene sensibilidad vestibular.
* **Mantener pulsado.** Correr y cargar exigen el dedo puesto. Con temblor,
  artritis o un conmutador adaptado, eso es la diferencia entre jugar y no.

Por qué estas pruebas y no otras
---------------------------------
Una opción de accesibilidad que se guarda y no cambia nada es peor que no
tenerla: le dice al jugador que el problema es suyo. Así que aquí **no** se
comprueba que la preferencia se persista —eso ya lo cubre la suite de
ajustes— sino que **cambia el comportamiento observable**: el tamaño real de
la fuente, la amplitud real de la sacudida, y lo que devuelve el gestor de
entrada.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import user_settings
from src.engine.core.user_settings import (
    ESCALAS_DE_TEXTO,
    MOVIMIENTO_REDUCIDO_FACTOR,
    UserSettings,
)
from src.engine.input.action_map import Action
from src.engine.input.input_manager import InputManager
from src.engine.ui import theme
from src.framework.stage.camera import Camera


@pytest.fixture
def preferencias(monkeypatch):
    """Preferencias aisladas: escribir en las del usuario contaminaría el resto."""
    prefs = UserSettings()
    monkeypatch.setattr(user_settings, "get", lambda: prefs)
    theme.clear_font_cache()
    yield prefs
    theme.clear_font_cache()


class TestLaEscalaDeTexto:
    def test_por_defecto_no_cambia_nada(self, preferencias) -> None:
        """Quien no toca la opción no debe notar ninguna diferencia."""
        assert theme.escalar_texto(18) == 18

    @pytest.mark.parametrize("escala", ESCALAS_DE_TEXTO)
    def test_cada_escala_ofrecida_produce_una_fuente_mayor(
        self, preferencias, escala,
    ) -> None:
        pygame.init()
        base = theme.font(18).get_height()
        preferencias.text_scale = escala
        theme.clear_font_cache()
        con_escala = theme.font(18).get_height()
        if escala > 1.0:
            assert con_escala > base, (
                f"la escala {escala}× no agrandó el texto: {base} px → "
                f"{con_escala} px"
            )
        else:
            assert con_escala == base

    def test_el_texto_al_doble_sigue_cabiendo_en_la_pantalla(
        self, preferencias,
    ) -> None:
        """2,0× es el máximo ofrecido porque es el que aún cabe.

        Una línea de diálogo típica al doble de tamaño tiene que caber en los
        800 px de ancho de la resolución interna. Si no cupiera, la ayuda
        recortaría el texto y dejaría al jugador peor que antes.
        """
        from src.engine.core import settings

        pygame.init()
        preferencias.text_scale = ESCALAS_DE_TEXTO[-1]
        theme.clear_font_cache()
        fuente = theme.font(theme.Theme.FONT_BODY)
        ancho = fuente.size("Flechas para moverte. Espacio para saltar.")[0]
        assert ancho <= settings.INTERNAL_WIDTH - 2 * theme.Theme.MARGIN, (
            f"al doble de tamaño una línea de tutorial mide {ancho} px y no "
            f"cabe en {settings.INTERNAL_WIDTH}"
        )

    def test_una_escala_absurda_del_fichero_se_recorta(self) -> None:
        """`config.json` editado a mano no debe dejar el juego inservible."""
        prefs = UserSettings(text_scale=40.0)
        assert prefs.text_scale == ESCALAS_DE_TEXTO[-1]
        prefs = UserSettings(text_scale=-5.0)
        assert prefs.text_scale == ESCALAS_DE_TEXTO[0]

    def test_un_valor_no_numerico_no_tumba_el_arranque(self) -> None:
        prefs = UserSettings(text_scale="grande")  # type: ignore[arg-type]
        assert prefs.text_scale == 1.0

    def test_nunca_se_baja_de_lo_legible(self, preferencias) -> None:
        """Con la fuente más pequeña del tema, la escala mínima sigue leyéndose."""
        preferencias.text_scale = ESCALAS_DE_TEXTO[0]
        assert theme.escalar_texto(theme.Theme.FONT_TINY) >= theme._TAMANO_MINIMO


class TestElMovimientoReducido:
    def test_por_defecto_la_sacudida_es_la_de_siempre(self, preferencias) -> None:
        camara = Camera()
        camara.apply_shake(amplitude=8.0, duration=0.2)
        assert camara._shake_amplitude == pytest.approx(8.0)

    def test_activado_la_sacudida_se_atenua(self, preferencias) -> None:
        preferencias.reduced_motion = True
        camara = Camera()
        camara.apply_shake(amplitude=8.0, duration=0.2)
        assert camara._shake_amplitude == pytest.approx(
            8.0 * MOVIMIENTO_REDUCIDO_FACTOR)

    def test_atenua_pero_no_borra(self, preferencias) -> None:
        """Quitar la sacudida del todo borra la única señal de que hubo golpe.

        La accesibilidad es reducir la barrera, no la información. Un impacto
        sin ninguna respuesta se lee como que el ataque no conectó.
        """
        preferencias.reduced_motion = True
        camara = Camera()
        camara.apply_shake(amplitude=8.0, duration=0.2)
        assert camara._shake_amplitude > 0.0

    def test_el_ajuste_se_lee_en_cada_golpe(self, preferencias) -> None:
        """Cambiarlo desde la pausa surte efecto sin reiniciar el nivel."""
        camara = Camera()
        camara.apply_shake(amplitude=4.0, duration=0.1)
        primera = camara._shake_amplitude

        preferencias.reduced_motion = True
        otra = Camera()
        otra.apply_shake(amplitude=4.0, duration=0.1)
        assert otra._shake_amplitude < primera


class TestPulsarEnVezDeMantener:
    @staticmethod
    def _pulsar(im: InputManager, accion: Action) -> None:
        """Un fotograma completo con la tecla bajando.

        Se pasa por `pump` con eventos de verdad en vez de escribir los
        conjuntos internos. La primera versión de estas pruebas los escribía a
        mano y por eso no habría cazado el defecto que sí cazó: la conmutación
        vivía en `is_action_held` y se aplicaba una vez por consulta, no una
        vez por fotograma. Recorrer el camino real es lo que distingue una
        prueba de una repetición del código.
        """
        tecla = im._bindings[accion][0]
        im.pump([pygame.event.Event(pygame.KEYDOWN, key=tecla)])

    @staticmethod
    def _soltar(im: InputManager, accion: Action) -> None:
        tecla = im._bindings[accion][0]
        im.pump([pygame.event.Event(pygame.KEYUP, key=tecla)])

    @staticmethod
    def _consultar_varias_veces(im: InputManager, accion: Action) -> bool:
        """Lo que hace el juego: varios sistemas preguntan por el mismo botón.

        La máquina de estados del jugador, el HUD y el sistema de combate
        consultan cada uno por su cuenta. Si la consulta tuviera efectos, el
        resultado dependería de cuántos preguntaran.
        """
        primera = im.is_action_held(accion)
        for _ in range(4):
            assert im.is_action_held(accion) == primera, (
                "consultar dos veces en el mismo fotograma da respuestas "
                "distintas: la consulta tiene efectos"
            )
        return primera

    def test_por_defecto_hay_que_mantener(self, preferencias) -> None:
        im = InputManager()
        self._pulsar(im, Action.DASH)
        assert self._consultar_varias_veces(im, Action.DASH)
        self._soltar(im, Action.DASH)
        assert not self._consultar_varias_veces(im, Action.DASH), (
            "sin la ayuda activada, soltar la tecla debe soltar la acción"
        )

    def test_activado_una_pulsacion_deja_la_accion_encendida(
        self, preferencias,
    ) -> None:
        preferencias.hold_to_press = True
        im = InputManager()
        self._pulsar(im, Action.DASH)
        assert self._consultar_varias_veces(im, Action.DASH)
        self._soltar(im, Action.DASH)
        assert self._consultar_varias_veces(im, Action.DASH), (
            "con la ayuda activada, soltar la tecla no debe apagar la acción"
        )

    def test_la_segunda_pulsacion_la_apaga(self, preferencias) -> None:
        preferencias.hold_to_press = True
        im = InputManager()
        self._pulsar(im, Action.DASH)
        self._soltar(im, Action.DASH)
        self._pulsar(im, Action.DASH)
        assert not im.is_action_held(Action.DASH)

    @pytest.mark.parametrize(
        "direccion",
        [Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP],
    )
    def test_las_direcciones_no_se_conmutan(self, preferencias, direccion) -> None:
        """Un jugador andando para siempre está peor que antes de la ayuda."""
        preferencias.hold_to_press = True
        im = InputManager()
        self._pulsar(im, direccion)
        self._soltar(im, direccion)
        assert not im.is_action_held(direccion), (
            f"{direccion.name} quedó conmutada: el jugador no puede parar"
        )

    def test_apagar_la_ayuda_no_deja_acciones_pegadas(self, preferencias) -> None:
        """El caso que rompe la partida de quien prueba la opción y la quita.

        Si al desactivar la ayuda quedara una acción conmutada a «activa», el
        jugador se quedaría corriendo sin tocar nada y sin forma de pararlo.
        """
        preferencias.hold_to_press = True
        im = InputManager()
        self._pulsar(im, Action.DASH)
        self._soltar(im, Action.DASH)
        assert im.is_action_held(Action.DASH)

        preferencias.hold_to_press = False
        im.pump([])
        assert not im.is_action_held(Action.DASH)


class TestLaPantallaDeOpcionesLasOfrece:
    """Una preferencia sin interfaz la usa quien sabe editar `config.json`."""

    def test_las_tres_aparecen_en_la_pantalla_de_opciones(self) -> None:
        import inspect

        from src.engine.scenes import options_scene

        fuente = inspect.getsource(options_scene)
        for campo in ("text_scale", "reduced_motion", "hold_to_press"):
            assert campo in fuente, (
                f"«{campo}» se guarda en las preferencias y no se puede "
                f"cambiar desde el juego"
            )

    def test_cambiar_la_escala_vacia_la_cache_de_fuentes(self) -> None:
        """Sin esto, el texto seguiría pequeño hasta reiniciar.

        Y ese es exactamente el momento en que alguien concluye que la opción
        de accesibilidad no funciona y deja de buscar ayuda en el menú.

        AUD-452 — se comprueba el efecto y no el texto del método.

        Antes se leía el fuente de `_save_config` buscando la llamada a
        `clear_font_cache`. Eso ataba la prueba al nombre de un método: al
        migrar la pantalla al kit del juego, el método pasó a llamarse
        `_aplicar`, la garantía se seguía cumpliendo y la prueba se ponía roja
        igual. Mirar si la fuente devuelta cambia de tamaño cubre lo mismo y
        no se rompe al renombrar nada.
        """
        from src.engine.core import user_settings
        from src.engine.scenes.options_scene import OptionsScene
        from src.engine.ui.theme import Theme, clear_font_cache, font

        class _ContextoMinimo:
            """Lo único que `_aplicar` le pide al contexto."""

            audio_manager = None
            event_bus = None

        user_settings.get().text_scale = 1.0
        clear_font_cache()
        escena = OptionsScene(_ContextoMinimo())   # type: ignore[arg-type]
        antes = font(Theme.FONT_BODY).get_height()

        try:
            escena._aplicar("text_scale", 2.0)
            assert font(Theme.FONT_BODY).get_height() > antes, (
                "la caché sigue devolviendo la fuente del tamaño anterior: el "
                "texto no crecería hasta reiniciar"
            )
        finally:
            user_settings.get().text_scale = 1.0
            clear_font_cache()
