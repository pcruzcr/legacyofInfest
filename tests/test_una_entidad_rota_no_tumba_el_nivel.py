"""AUD-289 — un fallo en una entrega tumbaba la clase entera.

El hueco
--------
Este motor **ejecuta código de veintiséis estudiantes** y hasta hoy no había
ninguna red en el bucle de juego. Un `IndexError` en el `update` de un enemigo
de una entrega tumbaba el fotograma, `App` lo cazaba arriba del todo y devolvía
al menú de título. Desde el asiento del estudiante eso se ve como «el juego se
cierra», y la explicación queda en un fichero de registro que nadie mira
mientras juega.

Al **cargar** sí había red desde AUD-055: un `.tmx` mal formado enseña su
diagnóstico en pantalla y `R` recarga. Faltaba la mitad de ejecución.

Lo que este fichero defiende
----------------------------
1. Que el nivel siga vivo cuando una entidad revienta.
2. Que la entidad se **retire**, y no que se le siga llamando sesenta veces por
   segundo al mismo error.
3. Que **no se silencie**: registro con traza y aviso en la consola de F11.
4. Que retirarla no le regale puntuación al jugador — un fallo de programación
   no es una baja.
5. Que se pueda apagar, porque quien depura el motor quiere la traza donde
   ocurre.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings
from src.engine.core.event_bus import EventBus


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture
def escena():
    from src.engine.audio.audio_manager import AudioManager
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
    escena._cutscenes = None
    yield escena
    escena.on_exit()


def _romper(escena, cerca_de_la_camara: bool = True):
    """Deja un enemigo del nivel con un `update` que lanza.

    Se rompe uno de verdad y no se inyecta un doble: lo que hay que comprobar es
    el camino que recorre una entrega, y una entrega es una subclase de
    `EnemyBase` colocada por el cargador.
    """
    from src.framework.entities.enemy_base import EnemyBase

    victima = next(e for e in escena._stage_data.entity_list
                   if isinstance(e, EnemyBase) and e.is_alive)
    if cerca_de_la_camara:
        victima.position.update(escena._player.position)
        victima.rect.topleft = (int(victima.position.x), int(victima.position.y))

    def _revienta(_dt):
        raise IndexError("list index out of range")

    victima.update = _revienta  # type: ignore[method-assign]
    return victima


class TestElNivelSigueVivo:
    def test_el_fotograma_no_se_cae(self, escena) -> None:
        _romper(escena)
        escena.update(1.0 / 60.0)   # sin AUD-289 esto lanzaba IndexError

    def test_la_entidad_se_retira(self, escena) -> None:
        victima = _romper(escena)
        escena.update(1.0 / 60.0)
        assert victima not in escena._stage_data.entity_list
        assert victima.is_alive is False

    def test_no_se_le_vuelve_a_llamar(self, escena) -> None:
        """Sesenta veces por segundo al mismo error llena el registro de
        cuarenta mil líneas iguales y esconde el resto."""
        victima = _romper(escena)
        veces = []
        original = victima.update

        def _contando(dt):
            veces.append(1)
            original(dt)

        victima.update = _contando  # type: ignore[method-assign]
        for _ in range(10):
            escena.update(1.0 / 60.0)
        assert len(veces) == 1

    def test_los_demas_enemigos_siguen_vivos(self, escena) -> None:
        from src.framework.entities.enemy_base import EnemyBase

        antes = len([e for e in escena._stage_data.entity_list
                     if isinstance(e, EnemyBase)])
        _romper(escena)
        escena.update(1.0 / 60.0)
        despues = len([e for e in escena._stage_data.entity_list
                       if isinstance(e, EnemyBase)])
        assert despues == antes - 1


class TestNoSeSilencia:
    def test_queda_en_el_registro_con_su_traza(self, escena, caplog) -> None:
        import logging

        _romper(escena)
        with caplog.at_level(logging.ERROR):
            escena.update(1.0 / 60.0)
        assert any("IndexError" in r.getMessage() or r.exc_info
                   for r in caplog.records), "el fallo se tragó sin registrar"

    def test_la_consola_de_f11_lo_ensena(self, escena) -> None:
        _romper(escena)
        escena.update(1.0 / 60.0)
        medidas = escena.medidas_de_depuracion()
        clave = next((k for k in medidas if "retirada" in k.lower()), None)
        assert clave is not None, (
            "la consola no dice nada de la entidad retirada: el fallo pasa a "
            "ser invisible, que es peor que el problema original"
        )

    def test_sin_fallos_la_consola_no_lleva_esa_fila(self, escena) -> None:
        """Una fila «retiradas: 0» permanente enseña a ignorarla."""
        medidas = escena.medidas_de_depuracion()
        assert not any("retirada" in k.lower() for k in medidas)


class TestNoRegalaPuntuacion:
    def test_retirar_no_cuenta_como_baja(self, escena) -> None:
        """`on_enemy_died` da monedas y puntos. Un fallo de programación no es
        una baja del jugador."""
        bajas = []
        escena.on_enemy_died = lambda entidad: bajas.append(entidad)
        _romper(escena)
        for _ in range(3):
            escena.update(1.0 / 60.0)
        assert bajas == []


class TestElInterruptor:
    def test_apagado_la_excepcion_se_propaga(self, escena, monkeypatch) -> None:
        """Quien depura el motor quiere la traza donde ocurre."""
        monkeypatch.setattr(settings, "AISLAR_FALLOS_DE_ENTIDAD", False)
        _romper(escena)
        with pytest.raises(IndexError):
            escena.update(1.0 / 60.0)

    def test_por_defecto_esta_encendido(self) -> None:
        assert settings.AISLAR_FALLOS_DE_ENTIDAD is True


class TestElDibujadoTambien:
    def test_una_entidad_que_falla_al_dibujarse_no_corta_el_fotograma(
        self, escena,
    ) -> None:
        """Aquí el daño sería peor que en el update: media escena ya está
        pintada, y el resultado no parece un error sino un fallo de vídeo."""
        from src.framework.entities.enemy_base import EnemyBase

        victima = next(e for e in escena._stage_data.entity_list
                       if isinstance(e, EnemyBase) and e.is_alive)
        victima.position.update(escena._player.position)
        victima.rect.topleft = (int(victima.position.x), int(victima.position.y))

        def _revienta(*_a, **_k):
            raise ValueError("sprite sin cargar")

        victima.draw = _revienta  # type: ignore[method-assign]
        escena.draw(pygame.Surface((800, 600)))
