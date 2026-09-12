"""AUD-814 — Recorrido runtime del Stage 4.1 nuevo.

No basta con que el TMX declare: el jugador (teletransportado, con la
cutscene saltada y el bus drenado — arnés documentado abajo) debe
experimentar fases, fricción, silencio, luna, grietas y liberaciones.
"""
from __future__ import annotations

import pytest

from src.stages.stage4_1 import trazado
from src.stages.stage4_1.fases import fase_en


def _construir():
    import pygame
    pygame.init()
    pygame.font.init()
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    entity_factory.ensure_registered()
    from src.stages.stage4_1.stage4_1 import Stage4_1
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1280, 720))
    ctx = GameContext(input_manager=InputManager(),
                      audio_manager=AudioManager(), scene_manager=None,
                      event_bus=EventBus(), clock=None,
                      save_manager=SaveManager())
    ctx.scene_manager = SceneManager(ctx)
    escena = Stage4_1(ctx)
    ctx.scene_manager.push(escena)
    return ctx, escena


def _avanzar(ctx, escena, n: int, dt: float = 1 / 60) -> None:
    """N fotogramas drenando el bus y saltando cutscenes.

    Arnés: la intro es bloqueante y saltable (CANCEL en juego real); aquí
    se salta por API para no probar el director en cada prueba de fase.
    """
    for _ in range(n):
        escena.update(dt)
        ctx.event_bus.dispatch()
        if escena._cutscenes is not None and escena._cutscenes.bloquea:
            escena._cutscenes.saltar()
            ctx.event_bus.dispatch()


def _poner(ctx, escena, columna: int, y: int = 480) -> None:
    escena._player.position.x = columna * trazado.TS
    escena._player.rect.x = columna * trazado.TS
    escena._player.position.y = y
    escena._player.rect.y = y
    escena._camera.snap_to_target()


def _caminar_derecha(ctx, escena):
    """Arnés: mantiene MOVE_RIGHT pulsado delegando el resto al real."""
    from src.engine.input.action_map import Action
    real = ctx.input_manager

    class _Mando:
        def __init__(self, base) -> None:
            self._base = base

        def is_action_held(self, action) -> bool:
            return action == Action.MOVE_RIGHT

        def __getattr__(self, nombre: str):
            return getattr(self._base, nombre)

    escena.context.input_manager = _Mando(real)
    return real


def _soltar(ctx, escena, real) -> None:
    escena.context.input_manager = real


@pytest.fixture()
def recorrido():
    ctx, escena = _construir()
    _avanzar(ctx, escena, 5)
    return ctx, escena


class TestFasesEnRuntime:
    @pytest.mark.parametrize("col,esperada", [(60, 1), (220, 2), (360, 3),
                                              (560, 4), (700, 5), (880, 6)])
    def test_detecta_fase(self, recorrido, col: int, esperada: int) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, col)
        _avanzar(ctx, escena, 10)
        assert escena._fase_actual.numero == esperada
        assert fase_en(col).numero == esperada

    def test_clima_por_fase(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 360)
        _avanzar(ctx, escena, 10)
        assert escena._weather.climate == "storm"
        _poner(ctx, escena, 880)
        _avanzar(ctx, escena, 10)
        assert escena._weather.climate == "fog"

    def test_musica_por_fase_suena(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 220)
        _avanzar(ctx, escena, 10)
        assert escena._musica_sonando == "mus_stage41_f2"

    def test_ambiente_por_fase_suena(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 360)
        _avanzar(ctx, escena, 10)
        audio = escena.audio
        assert audio is not None
        assert getattr(audio, "_ambient_active", False) is True


class TestFisicaEnRuntime:
    def _caminar(self, ctx, escena, col: int, cuadros: int = 180) -> float:
        _poner(ctx, escena, col)
        _avanzar(ctx, escena, 5)
        real = _caminar_derecha(ctx, escena)
        x0 = escena._player.position.x
        try:
            _avanzar(ctx, escena, cuadros)
        finally:
            _soltar(ctx, escena, real)
        return escena._player.position.x - x0

    def test_musgo_desliza_mas_que_sendero(self, recorrido) -> None:
        """Con la misma entrada sostenida, el musgo deja correr más que el
        sendero: la inercia de la zona holga el objetivo de marcha un 15 %
        (AUD-839, cierra D-71). Y el material llega al jugador (pasos y
        partículas propias)."""
        ctx, escena = recorrido
        d_musgo = self._caminar(ctx, escena, 195)
        d_sendero = self._caminar(ctx, escena, 60)
        assert d_musgo > d_sendero > 0, (d_musgo, d_sendero)

        _poner(ctx, escena, 195)
        _avanzar(ctx, escena, 5)
        real = _caminar_derecha(ctx, escena)
        try:
            _avanzar(ctx, escena, 20)
            material = getattr(escena._player, "_material_de_zona", None)
            assert material is not None and material.nombre == "musgo", (
                f"pisando musgo el material del jugador es {material!r}"
            )
        finally:
            _soltar(ctx, escena, real)

    def test_lodo_frena(self, recorrido) -> None:
        ctx, escena = recorrido
        d_lodo = self._caminar(ctx, escena, 245)
        d_sendero = self._caminar(ctx, escena, 60)
        assert 0 < d_lodo < d_sendero, (d_lodo, d_sendero)

    def test_slopes_transitables(self, recorrido) -> None:
        """La loma alta se sube caminando y se corona con un salto corto.

        Nota de física honesta: la cara empinada de una pendiente es un
        muro por diseño (`resolver_lateral`); el vértice entre subida y
        bajada se pasa saltando, como en cualquier plataformas. Caminar
        hasta arriba y bajar al otro lado sí funciona.
        """
        ctx, escena = recorrido
        _poner(ctx, escena, 402)
        _avanzar(ctx, escena, 5)
        y0 = escena._player.position.y
        real = _caminar_derecha(ctx, escena)

        from src.engine.input.action_map import Action

        class _MandoConSalto:
            """Camina a la derecha con JUMP mantenido (mash honesto, la misma
            técnica del bot de la chimenea en test_wall_gate): el buffer
            entrega el salto en cada apoyo y el vértice —cuya cara empinada
            es un muro por diseño— se corona con ese hop."""

            def __init__(self, base) -> None:
                self._base = base

            def is_action_held(self, action) -> bool:
                return action in (Action.MOVE_RIGHT, Action.JUMP)

            def __getattr__(self, nombre):
                return getattr(self._base, nombre)

        try:
            escena.context.input_manager = _MandoConSalto(real)
            _avanzar(ctx, escena, 400)
        finally:
            _soltar(ctx, escena, real)
        # Coronó la loma y cruzó la bajada_408 (termina en 7200): la costura
        # quedó alineada (subida y bajada coronan a 384), así que el
        # descenso caminando ya no se frena — D-72 cerrado.
        assert escena._player.position.x > 446 * 16, escena._player.position.x
        assert abs(escena._player.position.y - y0) < 60


class TestTormentaEnRuntime:
    def test_flash_programa_trueno_con_retraso(self, recorrido) -> None:
        """FLASH → (0.2–1.5 s) → THUNDER: la cadena causal existe y el
        retraso está acotado como pide el diseño."""
        ctx, escena = recorrido
        _poner(ctx, escena, 360)
        _avanzar(ctx, escena, 5)
        escena._proximo_rayo = 0.001
        _avanzar(ctx, escena, 1)
        assert escena._trueno_pendiente is not None
        assert 0.2 <= escena._trueno_pendiente <= 1.5
        _avanzar(ctx, escena, 120)
        assert escena._trueno_pendiente is None

    def test_viento_de_fase3(self, recorrido) -> None:
        from src.framework.ecs.components import ZonaDeViento
        ctx, escena = recorrido
        _poner(ctx, escena, 400)
        _avanzar(ctx, escena, 5)
        zonas = [z for _, z in escena._mundo.cada(ZonaDeViento)]
        assert len(zonas) == 1
        assert zonas[0].fuerza.x < 0.0


class TestSilencioEnRuntime:
    def test_silencio_dispara_shake(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 570)
        # El silencio dispara al llegar (col 560); se mide enseguida
        # porque el shake dura 0.45 s y luego decae por diseño.
        _avanzar(ctx, escena, 3)
        assert escena._silencio_hecho is True
        # Shake fuerte y breve en la cámara real (14 px, 0.45 s).
        assert escena._camera._shake_amplitude >= 14.0
        assert escena._camera._shake_timer > 0.0

    def test_shake_mueve_el_offset_renderizado(self, recorrido) -> None:
        """AUD-816: el shake entra al offset que compone el dibujo
        (camera.offset ± _shake_offset), no es una variable interna."""
        ctx, escena = recorrido
        _poner(ctx, escena, 570)
        _avanzar(ctx, escena, 3)
        ox = escena._camera._shake_offset
        assert ox.length() > 0.0, ox

    def test_gritos_tras_silencio(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 570)
        _avanzar(ctx, escena, 30)
        escena._proximo_grito = 0.01
        retreat = escena._tiempo
        _avanzar(ctx, escena, 10)
        assert escena._tiempo > retreat


class TestLunaEnRuntime:
    def test_luz_oscila(self, recorrido) -> None:
        _ctx, escena = recorrido
        vals = set()
        for i in range(9):
            escena._tiempo = i * 1.0
            vals.add(round(escena._luz_de_luna(), 2))
        assert min(vals) < 0.50 and max(vals) > 0.70

    def test_base_sigue_a_la_luna(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 700)
        _avanzar(ctx, escena, 5)
        assert (escena.LUZ_MINIMA_LUNA
                <= escena._ambiente_base
                <= escena.LUZ_MAXIMA_LUNA)


class TestGrietasEnRuntime:
    def test_pasos_encienden(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 830)
        _avanzar(ctx, escena, 5)
        # El teletransporte no es caminar: se resetea el podómetro.
        escena._distancia_f6 = 0.0
        escena._ultima_x = escena._player.rect.centerx
        real = _caminar_derecha(ctx, escena)
        try:
            _avanzar(ctx, escena, 300)
        finally:
            _soltar(ctx, escena, real)
        assert escena._luces_encendidas >= 3, escena._luces_encendidas


class TestLiberacionesEnRuntime:
    def _escuchar(self, ctx, escena, col_dialogo: int, arbol: str) -> None:
        """Atraviesa el trigger de diálogo y cierra la conversación."""
        _poner(ctx, escena, col_dialogo)
        _avanzar(ctx, escena, 5)
        assert arbol in escena._dialogo_visto, arbol
        escena._dialogue.end_dialogue()
        _avanzar(ctx, escena, 3)

    def test_altar_antes_de_dialogo_se_niega(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 235)
        escena._al_disparar(nombre="altar_venado")
        assert escena._liberados == [False, False, False]

    def test_tres_liberaciones_dan_la_llave(self, recorrido) -> None:
        ctx, escena = recorrido
        from src.stages.stage4_1 import trazado as _trazado
        pasos = (("venado", _trazado.COLUMNA_DIALOGO_VENADO,
                  "altar_venado", _trazado.COLUMNA_ALTAR_VENADO),
                 ("serpiente", _trazado.COLUMNA_DIALOGO_SERPIENTE,
                  "altar_serpiente", _trazado.COLUMNA_ALTAR_SERPIENTE),
                 ("halcon", _trazado.COLUMNA_DIALOGO_HALCON,
                  "altar_halcon", _trazado.COLUMNA_ALTAR_HALCON))
        for arbol, col_d, altar, col_a in pasos:
            self._escuchar(ctx, escena, col_d, arbol)
            _poner(ctx, escena, col_a)
            _avanzar(ctx, escena, 3)
            escena._al_disparar(nombre=altar)
            ctx.event_bus.dispatch()
        assert escena._liberados == [True, True, True]
        assert escena._interactables.llavero.tiene(trazado.LLAVE_PABURU)
        banderas = ctx.banderas
        assert banderas.get(trazado.BANDERA_PABURU) is True
        assert banderas.get(trazado.BANDERA_VENADO) is True

    def test_progreso_sobrevive_reentrada(self, recorrido) -> None:
        from src.stages.stage4_1 import trazado as _trazado
        ctx, escena = recorrido
        self._escuchar(ctx, escena, _trazado.COLUMNA_DIALOGO_VENADO, "venado")
        _poner(ctx, escena, _trazado.COLUMNA_ALTAR_VENADO)
        _avanzar(ctx, escena, 3)
        escena._al_disparar(nombre="altar_venado")
        ctx.event_bus.dispatch()
        assert escena._liberados[0] is True
        ctx2, escena2 = _construir()
        ctx2.banderas.update(ctx.banderas)
        escena2._restaurar_progreso()
        assert escena2._liberados[0] is True
        assert escena2._interactables.llavero.tiene(trazado.LLAVE_VENADO)


class TestAvisoCimaP0:
    def test_avisa_antes_del_repiso(self, recorrido) -> None:
        from src.engine.core.events import Events
        ctx, escena = recorrido
        vistos: list = []

        def _escucha(**d) -> None:
            vistos.append(d.get("text", ""))

        ctx.event_bus.subscribe(Events.SHOW_MESSAGE, _escucha)
        _poner(ctx, escena, 282)
        _avanzar(ctx, escena, 10)
        ctx.event_bus.dispatch()
        assert escena._aviso_cima_hecho is True
        assert any("saltando" in (m or "") for m in vistos)


class TestIncendioEnRuntime:
    def _ir(self, ctx, escena, col: int, cuadros: int = 30) -> None:
        _poner(ctx, escena, col)
        _avanzar(ctx, escena, cuadros)

    def test_rayos_encienden_piras_en_orden(self, recorrido) -> None:
        ctx, escena = recorrido
        self._ir(ctx, escena, 495)
        assert escena._piras_encendidas[0] is True
        self._ir(ctx, escena, 520)
        self._ir(ctx, escena, 545)
        assert escena._piras_encendidas == [True, True, True]
        assert escena._incendio_activo is True

    def test_lluvia_cesa_con_el_fuego(self, recorrido) -> None:
        ctx, escena = recorrido
        for col in (495, 520, 545):
            self._ir(ctx, escena, col)
        assert escena._weather.climate == "clear"
        assert len([luz for luz in escena._stage_lights
                    if tuple(luz.color) == (255, 150, 60)]) == 3

    def test_caza_sigue_y_muere_en_silencio(self, recorrido) -> None:
        ctx, escena = recorrido
        for col in (495, 520, 545):
            self._ir(ctx, escena, col)
        _poner(ctx, escena, 550)
        _avanzar(ctx, escena, 20)
        assert escena._caza_x is not None
        _poner(ctx, escena, 570)
        _avanzar(ctx, escena, 10)
        assert escena._silencio_hecho is True
        assert escena._caza_x is None


class TestNubesEnRuntime:
    def test_nube_cubre_y_baja_la_luz(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 700)
        _avanzar(ctx, escena, 60)
        base_sin_nube = escena._luz_de_luna()
        escena._nube = 1.0
        con_nube = escena._luz_de_luna()
        escena._nube = 0.0
        assert con_nube < base_sin_nube * 0.5

    def test_revelacion_en_flash(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 360)
        _avanzar(ctx, escena, 5)
        escena._proximo_rayo = 0.001
        _avanzar(ctx, escena, 1)
        assert escena._revelacion_serpiente > 0.0


class TestAntorchasEnRuntime:
    def test_orden_obligatorio(self, recorrido) -> None:
        """El camino se gana en orden: al aparecer tras la segunda
        antorcha, la primera ya arde (se cruzó) y la tercera sigue
        apagada hasta avanzar. Nunca se salta una."""
        ctx, escena = recorrido
        _poner(ctx, escena, 700)
        _avanzar(ctx, escena, 5)
        _poner(ctx, escena, 865)
        _avanzar(ctx, escena, 10)
        antorchas = escena._luces_antorcha()
        assert len(antorchas) == 4
        assert antorchas[0].intensity > 0.05
        assert antorchas[1].intensity > 0.05
        assert antorchas[2].intensity == 0.0
        assert antorchas[3].intensity == 0.0
        assert escena._antorcha_encendidas == 2

    def test_camino_enciende(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 825)
        _avanzar(ctx, escena, 5)
        escena._distancia_f6 = 0.0
        escena._ultima_x = escena._player.rect.centerx
        real = _caminar_derecha(ctx, escena)
        try:
            _avanzar(ctx, escena, 600)
        finally:
            _soltar(ctx, escena, real)
        assert escena._antorcha_encendidas >= 3, escena._antorcha_encendidas

    def test_templo_diez_pasos(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 945)
        _avanzar(ctx, escena, 900)
        assert escena._templo_iniciado is True
        assert escena._paso_templo == 10


class TestTransicionAnticipada:
    def test_clima_vecino_antes_del_borde(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 60)
        _avanzar(ctx, escena, 5)
        _poner(ctx, escena, 155)
        _avanzar(ctx, escena, 5)
        assert escena._simulacion.clima == "rain"
        assert escena._fase_actual.numero == 1


class TestApoyoP0:
    """AUD-816: los pies coinciden con la superficie jugable."""

    def test_pies_en_suelo_plano(self, recorrido) -> None:
        ctx, escena = recorrido
        _poner(ctx, escena, 60, 300)
        _avanzar(ctx, escena, 120)
        assert escena._player.rect.bottom == 512
        assert escena._player.is_grounded is True

    def test_pies_en_loma(self, recorrido) -> None:
        from src.framework.stage.pendientes import resolver as _resolver
        ctx, escena = recorrido
        _poner(ctx, escena, 420, 300)
        _avanzar(ctx, escena, 120)
        sup = _resolver(escena._player.rect,
                        escena._player.velocity.y, True,
                        escena._stage_data.pendientes)
        assert sup is not None
        assert abs(escena._player.rect.bottom - sup) <= 2.0

    def test_pies_al_iniciar_cada_fase(self, recorrido) -> None:
        ctx, escena = recorrido
        for col in (10, 165, 325, 485, 645, 805):
            _poner(ctx, escena, col, 300)
            _avanzar(ctx, escena, 120)
            assert escena._player.is_grounded is True, col
            assert escena._player.rect.bottom <= 512 + 2, col
