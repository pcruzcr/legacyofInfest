"""AUD-279 — el culling: qué se simula y qué se dibuja.

Qué defiende este fichero
-------------------------
Un culling mal puesto no se ve como lentitud: se ve como un enemigo que no se
mueve, y eso tarda semanas en diagnosticarse porque nadie sospecha de una
optimización. Así que aquí no se comprueba que sea rápido —eso es la última
prueba, y sale de medir—, sino que **congela exactamente a quien debe**:

* lo que está en pantalla sigue vivo;
* lo que está lejos se para;
* los jefes no se paran nunca;
* quien tiene un proyectil en vuelo no se para;
* el interruptor de `settings` apaga las dos mitades, la de simular y la de
  dibujar.

La última es la que más importa a medio plazo. Un interruptor que apaga la
mitad de lo que dice apagar es peor que no tenerlo.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings
from src.framework.stage import culling


@pytest.fixture
def zona() -> pygame.Rect:
    """Encuadre en el origen, con el margen de producción."""
    return culling.zona_activa(pygame.Vector2(0, 0))


class _EnemigoFalso:
    """Lo mínimo que `culling` mira: un `rect` y las dos exenciones."""

    siempre_activo = False

    def __init__(self, x: int, y: int = 0) -> None:
        self.rect = pygame.Rect(x, y, 16, 16)
        self._active_projectiles: list[object] = []


class TestLaZonaActiva:
    def test_el_margen_de_produccion_supera_el_alcance_de_un_proyectil(self) -> None:
        """La razón de que el margen sea 400 y no 100, fijada por prueba.

        Un `Projectile` vuela a 120 px/s con 3 s de vida: 360 px. Si el margen
        cayera por debajo, un enemigo congelado podría tener un proyectil suyo
        dentro del encuadre y el congelado se vería.
        """
        assert settings.CULLING_MARGEN > 120.0 * 3.0

    def test_el_mapa_de_referencia_cabe_entero_en_la_zona(self) -> None:
        """El margen que rompió stage 0, fijado para que no vuelva a pasar.

        Con 400 px, cuatro de los nueve enemigos de stage 0 quedaban fuera de
        la zona con la cámara en el arranque y `test_every_enemy_in_stage0_moves`
        los encontró convertidos en estatuas. Stage 0 es **el mapa que copian
        los estudiantes**: tiene que comportarse igual que antes de AUD-279.

        1.600 px de mapa, 800 de encuadre: hace falta que el margen cubra los
        800 que sobran.
        """
        ancho_de_stage0 = 1600
        assert settings.CULLING_MARGEN >= ancho_de_stage0 - settings.INTERNAL_WIDTH

    def test_cero_devuelve_none_y_no_un_rectangulo_vacio(self) -> None:
        """La distinción que evita una pantalla en negro.

        Un `Rect` de área cero no contiene nada, así que apagaría el juego
        entero en vez de apagar el culling.
        """
        assert culling.zona_activa(pygame.Vector2(0, 0), 0) is None

    def test_sin_zona_todo_esta_dentro(self) -> None:
        assert culling.dentro(pygame.Rect(99999, 99999, 8, 8), None) is True

    def test_sin_rectangulo_se_simula(self, zona) -> None:
        """Ante la duda, se simula: equivocarse por exceso cuesta décimas de
        milisegundo; por defecto, congela a alguien que se está mirando."""
        assert culling.dentro(None, zona) is True


class TestQuienSeSimula:
    def test_lo_que_esta_en_pantalla(self, zona) -> None:
        assert culling.se_simula(_EnemigoFalso(400), zona) is True

    def test_lo_que_esta_lejos_no(self, zona) -> None:
        assert culling.se_simula(_EnemigoFalso(5000), zona) is False

    def test_justo_dentro_del_margen(self, zona) -> None:
        """El borde exacto pertenece a la zona: `colliderect` es inclusivo."""
        assert culling.se_simula(_EnemigoFalso(-settings.CULLING_MARGEN + 1), zona) is True

    def test_quien_lo_declara_se_simula_lejos(self, zona) -> None:
        lejano = _EnemigoFalso(5000)
        lejano.siempre_activo = True
        assert culling.se_simula(lejano, zona) is True

    def test_con_un_proyectil_en_vuelo_se_simula_lejos(self, zona) -> None:
        """Sin esto, el proyectil se queda clavado en el aire."""
        lejano = _EnemigoFalso(5000)
        lejano._active_projectiles.append(object())
        assert culling.se_simula(lejano, zona) is True

    def test_con_el_culling_apagado_se_simula_todo(self) -> None:
        assert culling.se_simula(_EnemigoFalso(999999), None) is True


class TestLasClasesDelMotorLoDeclaranBien:
    """Que el mecanismo funcione no basta: hay que mirar quién lo usa."""

    def test_un_enemigo_normal_no_esta_exento(self) -> None:
        from src.framework.entities.enemy_base import EnemyBase

        assert EnemyBase.siempre_activo is False

    def test_un_jefe_si(self) -> None:
        """La arena de `boss_venado` mide 3.280 px: no cabe en pantalla."""
        from src.framework.entities.boss_base import BossBase

        assert BossBase.siempre_activo is True

    def test_el_jefe_de_referencia_hereda_la_exencion(self) -> None:
        from src.stages.boss_venado.boss_venado import BossVenado

        assert BossVenado.siempre_activo is True


class TestElInterruptorApagaLasDosMitades:
    def test_apagado_no_hay_zona_de_dibujado(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "CULLING_MARGEN", 0)
        assert culling.zona_de_dibujado(pygame.Vector2(0, 0), 64) is None

    def test_encendido_si(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "CULLING_MARGEN", 400)
        assert culling.zona_de_dibujado(pygame.Vector2(0, 0), 64) is not None


class TestEnUnaEscenaDeVerdad:
    """Un doble comprobaría que llamo bien a mi propia función.

    Lo que hay que ver es el bucle real de `StageScene`: que un enemigo lejano
    deje de moverse y uno cercano no.
    """

    @pytest.fixture(autouse=True)
    def _video(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))

    @pytest.fixture
    def escena(self):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.stage0.stage0 import Stage0

        entity_factory.ensure_registered()
        ctx = GameContext(
            input_manager=InputManager(),
            audio_manager=AudioManager(),
            scene_manager=None,
            event_bus=EventBus(),
            clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        escena = Stage0(ctx)
        escena.awake()
        escena.start()
        escena.on_enter()
        # Stage 0 abre con una cutscene, y mientras el director bloquea no
        # corre nada del juego: sin esto la prueba mediría el silencio de una
        # escena parada y pasaría por las razones equivocadas.
        escena._cutscenes = None
        yield escena
        escena.on_exit()

    @staticmethod
    def _enemigos(escena):
        from src.framework.entities.enemy_base import EnemyBase

        return [e for e in escena._stage_data.entity_list
                if isinstance(e, EnemyBase) and e.is_alive]

    def test_el_lejano_se_congela_y_el_cercano_no(self, escena) -> None:
        enemigos = self._enemigos(escena)
        assert len(enemigos) >= 2, "stage0 debería traer enemigos"

        cerca, lejos = enemigos[0], enemigos[1]
        cerca.position.update(escena._camera.offset.x + 100,
                              escena._camera.offset.y + 100)
        cerca.rect.topleft = (int(cerca.position.x), int(cerca.position.y))
        lejos.position.update(escena._camera.offset.x + 9000,
                              escena._camera.offset.y)
        lejos.rect.topleft = (int(lejos.position.x), int(lejos.position.y))

        marcas = []
        for enemigo, nombre in ((cerca, "cerca"), (lejos, "lejos")):
            original = enemigo.update

            def espia(dt, _n=nombre, _o=original):
                marcas.append(_n)
                return _o(dt)

            enemigo.update = espia  # type: ignore[method-assign]

        for _ in range(3):
            escena.update(1.0 / 60.0)

        assert "cerca" in marcas, "el enemigo visible dejó de actualizarse"
        assert "lejos" not in marcas, (
            "un enemigo a 9.000 px de la cámara se sigue simulando: el culling "
            "no está puesto en el bucle de la escena"
        )

    def test_apagarlo_devuelve_el_comportamiento_anterior(self, escena, monkeypatch) -> None:
        """La garantía para la invariante 2: con el interruptor a cero, el
        motor hace exactamente lo que hacía antes de AUD-279."""
        monkeypatch.setattr(settings, "CULLING_MARGEN", 0)
        enemigos = self._enemigos(escena)
        lejos = enemigos[-1]
        lejos.position.update(escena._camera.offset.x + 9000, escena._camera.offset.y)
        lejos.rect.topleft = (int(lejos.position.x), int(lejos.position.y))

        visto = []
        original = lejos.update
        lejos.update = lambda dt: (visto.append(1), original(dt))[1]  # type: ignore[method-assign]

        escena.update(1.0 / 60.0)
        assert visto, "con CULLING_MARGEN = 0 no debe congelarse nada"


class TestLoQueEstoCompra:
    """La medición, y por qué no dice lo que `docs/87` §15.4 suponía.

    §15.4 llamó al culling «lo más rentable que queda», y eso salía de que no
    existiera, no de haberlo medido. Medido:

    * stage 0, 9 enemigos en 1.600 px: **5,007 ms con culling, 4,931 sin él**.
      El mapa entero cabe en la zona activa: se paga la comprobación y no se
      congela a nadie.
    * 200 enemigos en 10.000 px: **10,292 → 6,753 ms, 1,52×**.

    Lo que compra no es velocidad hoy: es que el coste deje de crecer con el
    tamaño del mapa. Y eso sólo importa por el escenario que un estudiante
    puede construir, que es exactamente el que este proyecto tiene que aguantar.
    """

    def test_el_coste_deja_de_crecer_con_el_mapa(self) -> None:
        import time

        zona = culling.zona_activa(pygame.Vector2(0, 0))
        # 200 enemigos repartidos por un mapa de 10.000 px: el caso del
        # estudiante que llena el nivel. Sólo los primeros ~30 caen en la zona.
        enemigos = [_EnemigoFalso(i * 50) for i in range(200)]

        simulados = [e for e in enemigos if culling.se_simula(e, zona)]
        assert len(simulados) < len(enemigos) / 4, (
            f"con la cámara en el origen se simulan {len(simulados)} de 200: "
            "la zona activa es demasiado grande para servir de algo"
        )

        # Y decidirlo tiene que ser mucho más barato que el update que evita.
        inicio = time.perf_counter()
        for _ in range(100):
            for e in enemigos:
                culling.se_simula(e, zona)
        por_fotograma = (time.perf_counter() - inicio) / 100.0
        assert por_fotograma < 0.001, (
            f"decidir el culling de 200 enemigos cuesta {por_fotograma * 1000:.3f} ms; "
            "si decidir cuesta como simular, el culling sobra"
        )
