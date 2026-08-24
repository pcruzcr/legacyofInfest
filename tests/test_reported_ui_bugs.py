"""Los fallos que el usuario vio jugando, no leyendo el código."""
from __future__ import annotations

import pygame
import pytest

RAIZ = __import__("pathlib").Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


@pytest.fixture
def contexto(display):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    return ctx


class TestLaInterfazNoLaOscureceLaLuzDelMundo:
    """AUD-090 — un defecto que introduje al encender la iluminación.

    El HUD se dibujaba dentro de `DrawingSystem.draw`, es decir **antes** de
    `LightSystem.render`. Mientras el ambiente valía 1,0 daba igual. Al bajarlo
    a 0,59 en la fase 1, la luz del nivel empezó a multiplicar también la
    interfaz: medido, el HUD perdía el **58 %** de su brillo y el indicador de
    combo pasaba de 406 píxeles amarillos a **cero**.

    El jugador veía bajar la vida del enemigo y no veía el «COMBO x3». Su
    informe decía «no se ve la cadena de combos», y tenía razón: el contador
    funcionaba, el valor llegaba al HUD, y el orden de dibujado lo borraba.
    """

    def _escena(self, contexto):
        from src.stages.stage0.stage0 import Stage0

        s = Stage0(contexto)
        s.awake()
        s.start()
        s.on_enter()
        lienzo = pygame.Surface((800, 600))
        for _ in range(60):
            s.update(1 / 60)
            s.draw(lienzo)
        return s

    def test_el_hud_conserva_su_brillo(self, contexto):
        escena = self._escena(contexto)
        completa = pygame.Surface((800, 600))
        escena.draw(completa)
        solo_hud = pygame.Surface((800, 600))
        solo_hud.fill((0, 0, 0))
        escena._hud.draw(solo_hud)

        a = pygame.surfarray.array3d(completa).astype(float)
        b = pygame.surfarray.array3d(solo_hud).astype(float)
        mascara = b.max(axis=2) > 30
        assert mascara.any(), "el HUD no pinta nada"
        ratio = a[mascara].mean() / b[mascara].mean()
        assert ratio > 0.85, (
            f"el HUD conserva sólo el {ratio:.0%} de su brillo: la luz del "
            "mundo lo está multiplicando"
        )

    def test_el_indicador_de_combo_se_ve(self, contexto):
        escena = self._escena(contexto)
        escena._hud.set_combo_count(3)
        completa = pygame.Surface((800, 600))
        escena.draw(completa)
        a = pygame.surfarray.array3d(completa)
        amarillos = ((a[..., 0] > 200) & (a[..., 1] > 170)
                     & (a[..., 2] < 160)).sum()
        assert amarillos > 100, (
            f"sólo {amarillos} píxeles del indicador de combo llegan a la "
            "pantalla"
        )

    def test_la_interfaz_se_dibuja_despues_del_post_procesado(self, contexto):
        """El orden es el arreglo; esta prueba lo fija.

        AUD-343 — `draw` se partió en `dibujar_mundo` (el post-procesado
        cierra el mundo) y `dibujar_ui` (la interfaz), así que el orden se
        mira entre los dos métodos del mixin: la UI siempre después.
        """
        import inspect

        from src.framework.scenes.stage_parts import dibujo

        fuente = inspect.getsource(dibujo)
        pos_mundo = fuente.find("dibujar_mundo")
        pos_post = fuente.find("_post_processing.apply")
        pos_ui = fuente.find("def dibujar_ui")
        assert pos_post != -1 and pos_ui != -1
        assert pos_post > pos_mundo and pos_ui > pos_post, (
            "la interfaz vuelve a dibujarse antes del post-procesado"
        )


class TestLaRutaSoftwareTambienDibujaLaInterfaz:
    """AUD-501 — sin tarjeta, `dibujar_ui` no la llamaba nadie.

    `App._draw` parte el dibujo de una escena con ruta de GPU en
    `dibujar_mundo`/`dibujar_ui` (AUD-343), pero sólo componía la segunda
    mitad dentro de `if self._use_gl and self._gl_renderer`. En la rama
    software (`else`, sin tarjeta o con el contexto de GL caído) sólo se
    llamaba a `dibujar_mundo` y se publicaba esa superficie: el HUD, el
    diálogo, el minimapa y los subtítulos de cualquier `StageScene` no
    llegaban nunca a la pantalla. No es un caso de laboratorio: es el camino
    que corre siempre que el proyecto se abre en una máquina sin ModernGL.

    Se construye la `App` con `__new__` (no `App()`), igual que
    `test_el_fotograma_sin_escena.py`: lo que se prueba es la ligadura real
    de `_draw`, no el arranque completo del motor.
    """

    def _app_sin_gpu(self):
        from unittest.mock import MagicMock

        from src.engine.core import settings
        from src.engine.core.app import App

        app = App.__new__(App)
        tam = (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        app.internal_surface = pygame.Surface(tam)
        app._ui_overlay_surface = pygame.Surface(tam, pygame.SRCALPHA)

        escena = MagicMock()
        escena.dibujar_mundo = MagicMock()
        escena.dibujar_ui = MagicMock()
        gestor = MagicMock()
        gestor.stack_size = 1
        gestor.current = escena
        gestor.transition.draw = MagicMock()
        app.scene_manager = gestor

        app.debug_overlay = MagicMock()
        app.debug_overlay.visible = False
        app.clock = MagicMock()
        app.clock.fps = 60.0
        # Lo que hoy es siempre cierto en CI y en cualquier máquina sin
        # ModernGL: es la rama que este bug dejaba muda.
        app._use_gl = False
        app._gl_renderer = None
        return app, escena

    def test_dibujar_ui_se_llama_sin_tarjeta(self) -> None:
        app, escena = self._app_sin_gpu()
        app._draw(1 / 60)
        assert escena.dibujar_ui.called, (
            "la interfaz no se dibujó en la ruta software: HUD, diálogo, "
            "minimapa y subtítulos se pierden sin GPU"
        )

    def test_dibujar_mundo_tambien_se_llama(self) -> None:
        """La mitad que ya funcionaba no se debe romper al arreglar la otra."""
        app, escena = self._app_sin_gpu()
        app._draw(1 / 60)
        assert escena.dibujar_mundo.called


class TestLosEnemigosMuestranSuVida:
    """AUD-091 — sólo los jefes tenían barra.

    Un Walker tiene 3 puntos de vida y un ataque corto quita 0,5: hacen falta
    seis impactos. Durante los cinco primeros la única señal era un destello de
    0,09 s, así que el jugador no podía saber si estaba avanzando o pegando al
    aire. Su informe decía «no se le baja la barra»: no había barra.
    """

    def _enemigo_y_escena(self, contexto):
        from src.framework.entities.enemy_base import EnemyBase
        from src.stages.stage0.stage0 import Stage0

        s = Stage0(contexto)
        s.awake()
        s.start()
        s.on_enter()
        lienzo = pygame.Surface((800, 600))
        for _ in range(60):
            s.update(1 / 60)
            s.draw(lienzo)
        enemigo = next(e for e in s._stage_data.entity_list
                       if isinstance(e, EnemyBase))
        return s, enemigo

    def _fila_de_la_barra(self, escena, enemigo) -> list[tuple]:
        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)
        off = escena._camera.offset
        x = int(enemigo.position.x - off.x)
        y = int(enemigo.position.y - off.y) - 5
        px = pygame.surfarray.array3d(lienzo)
        return [tuple(int(v) for v in px[x + i, y])
                for i in range(0, enemigo.rect.width, 2)]

    def test_a_plena_vida_no_hay_barra(self, contexto):
        """Barras sobre enemigos intactos sólo llenarían la pantalla."""
        escena, enemigo = self._enemigo_y_escena(contexto)
        assert enemigo.current_health == enemigo.max_health
        fila = self._fila_de_la_barra(escena, enemigo)
        rojos = sum(1 for r, g, b in fila if r > 120 and r > g * 1.5)
        assert rojos == 0, "hay barra sobre un enemigo sin tocar"

    def test_tras_el_primer_golpe_aparece(self, contexto):
        escena, enemigo = self._enemigo_y_escena(contexto)
        enemigo.current_health = enemigo.max_health * 0.6
        fila = self._fila_de_la_barra(escena, enemigo)
        coloreados = sum(1 for r, g, b in fila if max(r, g) > 90)
        assert coloreados > 0, "el enemigo dañado no muestra barra"

    def test_la_barra_encoge_con_la_vida(self, contexto):
        escena, enemigo = self._enemigo_y_escena(contexto)

        def ancho_pintado(fraccion):
            enemigo.current_health = enemigo.max_health * fraccion
            fila = self._fila_de_la_barra(escena, enemigo)
            return sum(1 for r, g, b in fila if max(r, g) > 90)

        mucha = ancho_pintado(0.8)
        poca = ancho_pintado(0.2)
        assert poca < mucha, (
            f"con el 20 % de vida la barra mide {poca} y con el 80 % mide "
            f"{mucha}: no refleja la vida"
        )

    def test_un_enemigo_muerto_no_deja_barra(self, contexto):
        escena, enemigo = self._enemigo_y_escena(contexto)
        enemigo.current_health = 0.0
        enemigo.is_alive = False
        fila = self._fila_de_la_barra(escena, enemigo)
        rojos = sum(1 for r, g, b in fila if r > 150 and r > g * 2)
        assert rojos == 0, "queda barra sobre un enemigo muerto"


class TestElBestiarioVuelveAlTitulo:
    """AUD-092 — Esc dejaba al jugador en la pantalla equivocada."""

    def test_esc_lleva_al_titulo_y_no_vacia_la_pila(self, contexto):
        from src.engine.scenes.bestiary_scene import BestiaryScene
        from src.engine.scenes.demo_menu_scene import DemoMenuScene
        from src.engine.scenes.title_scene import TitleScene

        sm = contexto.scene_manager
        sm.push(TitleScene(contexto))
        sm.replace(DemoMenuScene(contexto))
        sm.replace(TitleScene(contexto))

        bestiario = BestiaryScene(contexto)
        sm.replace(bestiario)
        bestiario._volver()
        assert isinstance(sm.current, TitleScene), (
            f"Esc en el bestiario lleva a {type(sm.current).__name__}"
        )

    def test_usa_el_mismo_patron_que_sus_hermanas(self):
        """Logros y bestiario sólo se alcanzan desde el título — `replace`
        de ida y vuelta es correcto para las dos.

        AUD-533 — `inventory_scene` salió deliberadamente de este grupo:
        ahora se abre también desde el menú de pausa de una partida en
        curso (AUD-555: embebida como pestaña "Equipo" del panel de
        pausa, `PausaDeEscenario`), así que su salida usa `pop()` (vuelve
        a quien la empujó, título o partida) en vez de
        `replace(TitleScene(...))` (que siempre manda al título, aunque
        se haya abierto a mitad de partida). Ver los comentarios de
        `inventory_scene.py` y `stage_parts/pausa.py`.
        """
        import inspect

        from src.engine.scenes import achievement_scene, bestiary_scene

        for modulo in (achievement_scene, bestiary_scene):
            fuente = inspect.getsource(modulo)
            assert "replace(TitleScene" in fuente, (
                f"{modulo.__name__} no vuelve al título con `replace`"
            )


class TestElMapaDelMundoCabeEnSuSitio:
    """AUD-093 — tres de los cinco nodos se dibujaban sobre el título.

    Las coordenadas eran píxeles absolutos escritos para la resolución de
    referencia de 320x224. La interna es 800x600, y `draw_screen` devuelve
    y = 105 como inicio del contenido: los nodos a y = 50, 60 y 80 caían dentro
    de la cabecera.
    """

    def test_ningun_nodo_invade_la_cabecera_ni_los_atajos(self, display):
        from src.engine.core import settings
        from src.engine.scenes.world_map_scene import STAGE_NODES, WorldMapScene
        from src.engine.ui.widgets import draw_screen

        lienzo = pygame.Surface((800, 600))
        top = draw_screen(lienzo, "MAPA DEL MUNDO", "Elige tu destino")
        for nodo in STAGE_NODES:
            _x, y = WorldMapScene._posicion(WorldMapScene, nodo, top)
            assert y >= top, (
                f"'{nodo['name']}' se dibuja en y={y}, sobre la cabecera "
                f"que termina en {top}"
            )
            assert y <= settings.INTERNAL_HEIGHT - 40, (
                f"'{nodo['name']}' se dibuja en y={y}, sobre la barra de atajos"
            )

    def test_los_nodos_se_reparten_por_el_area(self, display):
        """Si todos cayeran juntos, el mapa dejaría de leerse como mapa."""
        from src.engine.scenes.world_map_scene import STAGE_NODES, WorldMapScene
        from src.engine.ui.widgets import draw_screen

        lienzo = pygame.Surface((800, 600))
        top = draw_screen(lienzo, "MAPA DEL MUNDO", "")
        ys = [WorldMapScene._posicion(WorldMapScene, n, top)[1]
              for n in STAGE_NODES]
        assert max(ys) - min(ys) > 200, f"los nodos se apelotonan: {ys}"

    def test_las_posiciones_son_normalizadas(self):
        """Píxeles absolutos vuelven a romperse al cambiar de resolución."""
        from src.engine.scenes.world_map_scene import STAGE_NODES

        for nodo in STAGE_NODES:
            assert "nx" in nodo and "ny" in nodo, (
                f"'{nodo['name']}' usa coordenadas absolutas otra vez"
            )
            assert 0.0 <= nodo["nx"] <= 1.0 and 0.0 <= nodo["ny"] <= 1.0

    def test_la_escena_se_dibuja_sin_lanzar(self, contexto):
        from src.engine.scenes.world_map_scene import WorldMapScene

        escena = WorldMapScene(contexto)
        escena.on_enter()
        lienzo = pygame.Surface((800, 600))
        for _ in range(10):
            escena.update(1 / 60)
            escena.draw(lienzo)
        pintados = (pygame.surfarray.array3d(lienzo).max(axis=2) > 40).sum()
        assert pintados > 1000, "el mapa del mundo apenas pinta nada"
