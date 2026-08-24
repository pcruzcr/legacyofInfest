"""Los puntos y las monedas llegan a la pantalla — AUD-219.

El hueco (GAP-029, conexión 2 de 4)
===================================
`engine.core.score_system` estaba escrito entero —tabla de puntos por tipo,
suscripción a `ENEMY_DIED`, persistencia en `data/score.json`— y **nadie lo
instanciaba**. Medido sobre `src/`: cero referencias a `ScoreSystem` fuera de
su propio módulo. Un sistema que nadie construye no se suscribe a nada, así
que matar enemigos no sumaba un solo punto.

Y no había dónde enseñarlos: `09_HUD_SPEC.md` §2.1 no tenía —hasta AUD-219—
ninguna región de puntuación. La docstring del módulo afirmaba que sí; era
falso, y se corrige junto con esto. El HUD tampoco mostraba el saldo de
monedas, que desde AUD-218 sí sube al jugar y sin verlo no se sabe cuándo se
puede comprar.

Se prueban las tres uniones por separado porque fallan por separado:

1. el sistema se suscribe al bus **de la escena** y cuenta;
2. el HUD dibuja puntos y monedas;
3. `StageScene` ata las dos cosas — que es el paso que faltaba en los nueve
   casos anteriores de este proyecto.
"""
from __future__ import annotations

import pathlib

import pygame
import pytest

from src.engine.core import score_system as score_mod
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.core.score_system import ScoreSystem

RAIZ = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


@pytest.fixture(scope="module")
def fuente() -> str:
    """El texto de `stage_scene.py` y su mixin de actualizaciones, para
    comprobar quién llama a qué. AUD-351 movió `_update_hud_ui` (el `set_score`
    del HUD) a `stage_parts/actualizaciones.py`, así que el texto se lee de
    los dos sitios."""
    return (
        RAIZ / "src/framework/scenes/stage_scene.py"
    ).read_text(encoding="utf-8") + (
        RAIZ / "src/framework/scenes/stage_parts/actualizaciones.py"
    ).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _puntuacion_aislada(tmp_path, monkeypatch):
    """El sistema persiste en disco y es singleton: cada prueba, de cero."""
    monkeypatch.setattr(score_mod, "_SCORE_PATH", tmp_path / "score.json")
    ScoreSystem._reset_instance()
    yield
    ScoreSystem._reset_instance()


class TestElSistemaCuentaEnElBusDeLaEscena:
    def test_hay_una_instancia_compartida(self) -> None:
        """Como `AchievementSystem` y `Bestiary`: el progreso es uno."""
        assert ScoreSystem.get_instance() is ScoreSystem.get_instance()

    def test_matar_a_un_enemigo_suma(self) -> None:
        bus = EventBus()
        sistema = ScoreSystem.get_instance()
        sistema.bind_bus(bus)
        assert sistema.score == 0

        bus.emit(Events.ENEMY_DIED, entity_id="EnemyWalker_1", position=(0, 0))
        bus.dispatch()

        assert sistema.score == 100

    def test_un_jefe_vale_mucho_mas(self) -> None:
        bus = EventBus()
        sistema = ScoreSystem.get_instance()
        sistema.bind_bus(bus)

        bus.emit(Events.ENEMY_DIED, entity_id="BossVenado_1", position=(0, 0))
        bus.dispatch()

        assert sistema.score == 1000

    def test_cambiar_de_bus_no_cuenta_dos_veces(self) -> None:
        """Una transición de escena cambia el bus; el manejador debe mudarse.

        Si se quedara suscrito al viejo *y* al nuevo, cada muerte sumaría el
        doble en cuanto el jugador pasara de un nivel a otro.
        """
        viejo, nuevo = EventBus(), EventBus()
        sistema = ScoreSystem.get_instance()
        sistema.bind_bus(viejo)
        sistema.bind_bus(nuevo)

        nuevo.emit(Events.ENEMY_DIED, entity_id="EnemyWalker_1", position=(0, 0))
        nuevo.dispatch()
        viejo.emit(Events.ENEMY_DIED, entity_id="EnemyWalker_1", position=(0, 0))
        viejo.dispatch()

        assert sistema.score == 100, "el sistema siguió escuchando el bus viejo"

    def test_el_manejador_sobrevive_al_recolector(self) -> None:
        """El bus guarda referencias **débiles**; un sistema vivo debe seguir
        recibiendo. Es el fallo que dejó el juego mudo en AUD-152."""
        import gc

        bus = EventBus()
        sistema = ScoreSystem.get_instance()
        sistema.bind_bus(bus)
        gc.collect()

        bus.emit(Events.ENEMY_DIED, entity_id="EnemyWalker_1", position=(0, 0))
        bus.dispatch()

        assert sistema.score == 100

    def test_una_partida_nueva_empieza_a_cero(self) -> None:
        bus = EventBus()
        sistema = ScoreSystem.get_instance()
        sistema.bind_bus(bus)
        bus.emit(Events.ENEMY_DIED, entity_id="EnemyWalker_1", position=(0, 0))
        bus.dispatch()

        sistema.reset()

        assert sistema.score == 0


class TestElHudLosDibuja:
    def _hud(self):
        from src.engine.ui.hud import HUD

        return HUD(EventBus())

    def _pinta(self, hud) -> pygame.Surface:
        # AUD-451 — la superficie es la resolución interna real. Con 320×224
        # el marcador cae fuera del lienzo desde que la maqueta se escala, y
        # la prueba mediría un recorte en vez del HUD.
        from src.engine.core import settings

        lienzo = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        lienzo.fill((0, 0, 0))
        hud.draw(lienzo)
        return lienzo

    def test_el_hud_acepta_puntos_y_monedas(self) -> None:
        hud = self._hud()
        hud.set_score(1250, 12)  # no debe estallar ni pedir nada más

    def test_con_puntos_se_pintan_pixeles(self) -> None:
        """Un marcador que no cambia un píxel no es un marcador."""
        import numpy as np

        hud = self._hud()
        hud.set_score(0, 0)
        vacio = np.asarray(pygame.surfarray.array3d(self._pinta(hud)), dtype=float)
        hud.set_score(987654, 42)
        lleno = np.asarray(pygame.surfarray.array3d(self._pinta(hud)), dtype=float)

        assert not np.array_equal(vacio, lleno), (
            "el HUD dibujó exactamente lo mismo con 0 puntos que con 987654"
        )

    def test_el_marcador_cabe_en_la_pantalla_interna(self) -> None:
        """Salirse de la pantalla es recortar el número.

        AUD-451 — el límite sale de `settings`, no de un 320×224 escrito a
        mano. Ese número era el de la resolución que el juego dejó atrás, y
        fijarlo aquí hacía que la prueba aprobara una maqueta que ocupaba el
        40 % de la pantalla real.
        """
        from src.engine.core import settings

        hud = self._hud()
        hud.set_score(999999, 999)
        r = hud.score_rect()

        assert r.right <= settings.INTERNAL_WIDTH
        assert r.bottom <= settings.INTERNAL_HEIGHT
        assert r.left >= 0 and r.top >= 0

    def test_no_pisa_ni_la_barra_de_vida_ni_el_cronometro(self) -> None:
        """Contra la geometría **real** del HUD, no contra la del documento.

        `09_HUD_SPEC.md` §2.1 y `hud.py` ya no coincidían antes de AUD-219 —el
        doc pone los corazones en Y=20 y el código los dibuja en Y=6—, así que
        comprobar el solape contra la tabla del doc no diría nada sobre lo que
        se ve en pantalla. Esa divergencia es anterior y queda anotada, no
        arreglada aquí.

        AUD-535 — la fila de corazones (`_hearts_x`/`_hearts_y`/
        `_heart_spacing`) ya no existe: se comprueba contra `vida_bar_rect()`,
        la región real que ocupa hoy la vida del jugador.
        """
        hud = self._hud()
        hud.set_score(123456, 99)
        r = hud.score_rect()

        vida = hud.vida_bar_rect()
        cronometro = hud._timer_bg_rect
        assert not r.colliderect(vida), f"{r} pisa la barra de vida {vida}"
        assert not r.colliderect(cronometro), f"{r} pisa el cronómetro {cronometro}"


class TestLaEscenaLosAta:
    """El paso que faltaba: que alguien construya el sistema y alimente el HUD.

    Se comprueba sobre el texto de `stage_scene.py` porque montar un
    `StageScene` real pide un mapa, audio y una ventana —ninguna prueba de
    este repositorio lo hace—. Es la misma comprobación que
    `test_audio_wiring.py` hace del «cuarto paso: alguien lo emite».
    """

    def test_la_escena_construye_el_sistema(self, fuente: str) -> None:
        assert "ScoreSystem.get_instance()" in fuente, (
            "nadie instancia ScoreSystem: sin eso no se suscribe a ENEMY_DIED "
            "y matar enemigos no suma nada"
        )

    def test_la_escena_le_da_su_bus(self, fuente: str) -> None:
        assert "_score.bind_bus(" in fuente, (
            "el sistema existiría escuchando un bus que no es el de la escena"
        )

    def test_la_escena_alimenta_el_hud_cada_fotograma(self, fuente: str) -> None:
        assert "set_score(" in fuente, (
            "el HUD sabe dibujar el marcador y nadie le pasa el número"
        )


class TestLaDocumentacionDiceLaVerdad:
    """Invariante 6 de `CLAUDE.md`: los números y los slots del doc son
    verificables o no se escriben. La docstring de `score_system` afirmaba que
    `09_HUD_SPEC.md` documentaba un slot de score. No lo documentaba."""

    def test_el_hud_spec_declara_la_region(self) -> None:
        spec = (RAIZ / "docs/09_HUD_SPEC.md").read_text(encoding="utf-8")
        assert "Puntuación" in spec, (
            "el HUD dibuja una región que su especificación no declara"
        )

    def test_la_region_del_doc_es_la_que_se_dibuja(self) -> None:
        """El doc da X, Y, ancho y alto; el código debe caber ahí."""
        from src.engine.ui.hud import HUD

        spec = (RAIZ / "docs/09_HUD_SPEC.md").read_text(encoding="utf-8")
        fila = [ln for ln in spec.splitlines() if ln.startswith("| Puntuación")]
        assert fila, "falta la fila `| Puntuación` en la tabla de regiones §2.1"
        campos = [c.strip() for c in fila[0].split("|")]
        x, y, w, h = (int(campos[i]) for i in range(2, 6))

        # AUD-451 — la tabla del doc está en espacio de **diseño** (320 de
        # ancho) porque es el espacio en el que se lee junto al dibujo del
        # layout, y el código se sigue escribiendo así. Para comparar con lo
        # que se dibuja hay que aplicarle la misma escala que aplica el HUD.
        from src.engine.ui.hud import ESCALA_DEL_HUD

        declarada = pygame.Rect(
            int(x * ESCALA_DEL_HUD), int(y * ESCALA_DEL_HUD),
            round(w * ESCALA_DEL_HUD), round(h * ESCALA_DEL_HUD),
        )
        hud = HUD(EventBus())
        hud.set_score(999999, 999)
        assert declarada.contains(hud.score_rect()), (
            f"el doc declara {declarada} (diseño {(x, y, w, h)} x"
            f"{ESCALA_DEL_HUD}) y el HUD dibuja {hud.score_rect()}"
        )
