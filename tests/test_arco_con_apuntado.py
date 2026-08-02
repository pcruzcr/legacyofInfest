"""
Module: test_arco_con_apuntado
System: tests
Academic Unit: N/A

AUD-193 — el arco apunta libre y la flecha cae.

Qué cambia
----------
`ArcoDelJugador.disparar` admitía sólo `-1` o `+1`, y el motivo estaba escrito:

    «No se admite disparar en diagonal: el juego es de plataformas con
    movimiento horizontal, y apuntar en ocho direcciones exigiría un control
    que no existe.»

El argumento no era que apuntar libre estuviera mal: era que **no había con
qué**. Con el ratón o el stick derecho ese control existe, así que la razón
deja de sostenerse — y sólo por eso se cambia. Es la única forma legítima de
tocar una decisión razonada en este repositorio: rebatiendo su argumento, no
ignorándolo.

Las dos formas conviven a propósito. Un `int` dispara horizontal exactamente
como antes, que es lo que hacen los 17 mapas ya calibrados y las entregas de
estudiantes; un `Vector2` apunta libre. Nadie tiene que migrar nada.

Por qué la flecha cae
---------------------
Con trayectoria recta, dibujar la previsualización sobra —sería una línea— y
apuntar no es una habilidad. La caída es lo que convierte el tiro en una
lectura del terreno, y lo que hace que valga la pena dibujar la parábola.
"""
from __future__ import annotations

from itertools import pairwise

import pygame
import pytest

from src.framework.entities.enemy_shooter import Projectile
from src.framework.entities.ranged_weapon import (
    GRAVEDAD_FLECHA,
    POTENCIA_MAXIMA,
    POTENCIA_MINIMA,
    TIEMPO_DE_TENSADO,
    VELOCIDAD,
    ArcoDelJugador,
    trayectoria,
    velocidad_inicial,
)


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


ORIGEN = pygame.Vector2(100.0, 300.0)


class TestLoQueYaFuncionabaSigueIgual:
    """La compatibilidad no es un detalle: hay 26 entregas de estudiantes."""

    @pytest.mark.parametrize(("direccion", "signo"), [(1, 1), (-1, -1), (0, 1)])
    def test_un_entero_dispara_horizontal(self, direccion: int, signo: int) -> None:
        v = velocidad_inicial(direccion)
        assert v.x == pytest.approx(VELOCIDAD * signo)
        assert v.y == 0.0

    def test_los_proyectiles_de_los_enemigos_no_caen(self) -> None:
        """`gravity` es cero por defecto, y tiene que seguir siéndolo.

        Los disparos enemigos son telegrafiados que el jugador aprende a leer;
        una parábola los volvería impredecibles y recalibraría de golpe a las
        21 especies.
        """
        bala = Projectile(pygame.Vector2(0, 0), pygame.Vector2(100.0, 0.0), 1.0)
        for _ in range(60):
            bala.update(1 / 60)

        assert bala.position.y == pytest.approx(0.0), (
            "un proyectil de enemigo ha empezado a caer"
        )


class TestApuntarLibre:
    def test_un_vector_dispara_en_esa_direccion(self) -> None:
        v = velocidad_inicial(pygame.Vector2(1, -1))

        assert v.x > 0 and v.y < 0
        assert v.x == pytest.approx(-v.y)

    def test_apuntar_lejos_no_dispara_mas_fuerte(self) -> None:
        """El vector se normaliza: quien apunta dice **hacia dónde**, no a qué
        velocidad. Sin esto, alejar el cursor del jugador aumentaría el alcance
        y el arma dependería de la resolución de pantalla."""
        cerca = velocidad_inicial(pygame.Vector2(1, -1))
        lejos = velocidad_inicial(pygame.Vector2(700, -700))

        assert cerca.length() == pytest.approx(lejos.length())
        assert lejos.length() == pytest.approx(VELOCIDAD)

    def test_un_vector_nulo_no_desperdicia_la_flecha(self) -> None:
        """Stick en reposo o cursor justo encima del jugador: se dispara a la
        derecha en vez de no salir nada. Gastar munición sin que salga la
        flecha es peor que gastarla en una dirección discutible."""
        v = velocidad_inicial(pygame.Vector2(0, 0))

        assert v.length() == pytest.approx(VELOCIDAD)

    def test_el_arco_acepta_las_dos_formas(self) -> None:
        recto = ArcoDelJugador().disparar(ORIGEN, 1)
        diagonal = ArcoDelJugador().disparar(ORIGEN, pygame.Vector2(1, -1))

        assert recto is not None and diagonal is not None
        assert recto.velocity.y == 0.0
        assert diagonal.velocity.y < 0.0


class TestLaTrayectoriaDibujadaNoMiente:
    def test_la_prevision_coincide_con_el_vuelo_real(self) -> None:
        """La comprobación que da sentido a todo lo demás.

        La curva se integra con el mismo paso y en el mismo orden que
        `Projectile.update` —gravedad sobre la velocidad, luego posición—. Una
        fórmula cerrada sería más elegante y estaría mal: la línea dibujada y
        la flecha se separarían, y el jugador nota enseguida que la
        previsualización le miente.
        """
        pasos = 28
        puntos = trayectoria(ORIGEN, 1, pasos=pasos)

        flecha = ArcoDelJugador().disparar(ORIGEN, 1)
        assert flecha is not None
        for _ in range(pasos):
            flecha.update(1 / 30)

        assert flecha.position.x == pytest.approx(puntos[-1].x, abs=0.5)
        assert flecha.position.y == pytest.approx(puntos[-1].y, abs=0.5)

    def test_la_prevision_tambien_acierta_apuntando_en_diagonal(self) -> None:
        pasos = 20
        direccion = pygame.Vector2(1, -0.6)
        puntos = trayectoria(ORIGEN, direccion, pasos=pasos)

        flecha = ArcoDelJugador().disparar(ORIGEN, direccion)
        assert flecha is not None
        for _ in range(pasos):
            flecha.update(1 / 30)

        assert flecha.position.x == pytest.approx(puntos[-1].x, abs=0.5)
        assert flecha.position.y == pytest.approx(puntos[-1].y, abs=0.5)

    def test_la_trayectoria_describe_una_parabola(self) -> None:
        """Cae, y cada vez más deprisa. Si fuera una recta, dibujarla sobraría."""
        puntos = trayectoria(ORIGEN, 1, pasos=12)
        caidas = [b.y - a.y for a, b in pairwise(puntos)]

        assert all(c > 0 for c in caidas), "la flecha no cae"
        assert caidas[-1] > caidas[0] * 2, "la caída no se acelera: no es una parábola"


class TestElRatonNoSecuestraElApuntado:
    """El defecto que apareció al cablearlo a la escena.

    La primera versión preguntaba sólo por `mouse.get_focused()`. Con eso, un
    jugador de teclado disparaba hacia donde el cursor se hubiera quedado
    olvidado —medido en stage0: en diagonal hacia arriba y a la izquierda, sin
    haber tocado el ratón—. El apuntado con ratón tiene que activarse porque el
    jugador lo mueva, no porque exista.
    """

    @pytest.fixture
    def escena(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))
        from src.engine.core.app import App
        from src.stages.stage0.stage0 import Stage0

        app = App()
        escena = Stage0(app.context)
        app.context.scene_manager.push(escena)
        escena.on_enter()
        return escena

    class _SinEntrada:
        def is_action_just_pressed(self, accion: object) -> bool:
            return False

    def test_sin_mover_el_raton_se_dispara_de_frente(self, escena) -> None:
        direccion = escena._direccion_de_tiro(escena._player, self._SinEntrada())

        assert not isinstance(direccion, pygame.Vector2), (
            f"el ratón ha secuestrado el apuntado sin que nadie lo mueva: "
            f"{direccion}"
        )

    def test_con_el_temporizador_agotado_vuelve_al_frente(self, escena) -> None:
        """Soltar el ratón un rato devuelve el control al teclado."""
        escena._raton_ultimo_movimiento = 0.0

        direccion = escena._direccion_de_tiro(escena._player, self._SinEntrada())

        assert not isinstance(direccion, pygame.Vector2)

    def test_con_el_raton_recien_movido_se_apunta_libre(self, escena) -> None:
        # La referencia de posición tiene que existir ya: la primera lectura
        # siempre se toma como referencia y nunca como movimiento.
        escena._raton_posicion_previa = pygame.mouse.get_pos()
        escena._raton_ultimo_movimiento = 1.5

        direccion = escena._direccion_de_tiro(escena._player, self._SinEntrada())

        assert isinstance(direccion, pygame.Vector2)

    def test_el_stick_manda_sobre_el_raton(self, escena) -> None:
        """Si el jugador está usando el mando, el cursor no pinta nada."""
        class ConStick:
            def aim_axis(self) -> pygame.Vector2:
                return pygame.Vector2(0.6, -0.8)

            def is_action_just_pressed(self, accion: object) -> bool:
                return False

        escena._raton_posicion_previa = pygame.mouse.get_pos()
        escena._raton_ultimo_movimiento = 1.5
        direccion = escena._direccion_de_tiro(escena._player, ConStick())

        assert direccion == pygame.Vector2(0.6, -0.8)

    def test_un_doble_de_entrada_raro_no_tumba_la_escena(self, escena) -> None:
        """`getattr` sobre un doble con `__getattr__` genérico devuelve un
        invocable para cualquier nombre. Llamar a `length_squared()` sobre lo
        que conteste reventaba la escena en mitad del combate."""
        class Raro:
            def is_action_just_pressed(self, accion: object) -> bool:
                return False

            def __getattr__(self, nombre: str):
                return lambda *a, **k: False

        escena._direccion_de_tiro(escena._player, Raro())


class TestLaPrevisualizacionEnPantalla:
    """AUD-194 — la parábola punteada mientras se apunta.

    Se cuenta la tinta del color de la trayectoria sobre la superficie
    dibujada. Comprobar «no lanza excepción» no serviría: el defecto real que
    apareció fue que **se dibujaba y la iluminación la apagaba**, con la escena
    funcionando perfectamente y cero píxeles en pantalla.
    """

    @pytest.fixture
    def escena(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))
        from src.engine.core.app import App
        from src.stages.stage0.stage0 import Stage0

        app = App()
        escena = Stage0(app.context)
        app.context.scene_manager.push(escena)
        escena.on_enter()
        for _ in range(30):
            escena.update(1 / 60)
            app.context.event_bus.dispatch()
        return escena

    @staticmethod
    def _tinta(superficie: pygame.Surface) -> int:
        from src.framework.scenes.stage_scene import TINTA_DE_LA_TRAYECTORIA

        r, g, b = TINTA_DE_LA_TRAYECTORIA
        pixeles = pygame.surfarray.array3d(superficie)
        return int((
            (pixeles[..., 0] >= r - 6)
            & (pixeles[..., 1] >= g - 6)
            & (pixeles[..., 2] >= b - 6)
        ).sum())

    def _dibujar(self, escena) -> int:
        superficie = pygame.Surface((800, 600))
        escena.draw(superficie)
        return self._tinta(superficie)

    def test_apuntando_se_dibuja_la_parabola(self, escena) -> None:
        base = self._dibujar(escena)
        escena._direccion_de_tiro = lambda p, im: pygame.Vector2(0.85, -0.5)

        assert self._dibujar(escena) > base, (
            "apuntando no aparece ningún punto de trayectoria en pantalla"
        )

    def test_la_ilumincaion_no_se_la_come(self, escena) -> None:
        """El defecto que costó encontrar: dibujada antes de la iluminación,
        stage0 —doce focos— la apagaba entera. Es una ayuda de interfaz, no un
        objeto del mundo, así que va después del post-procesado."""
        escena._direccion_de_tiro = lambda p, im: pygame.Vector2(0.85, -0.5)

        assert self._dibujar(escena) > 0

    def test_sin_apuntar_no_se_dibuja_nada(self, escena) -> None:
        """Con el disparo horizontal de teclado la curva no aporta nada y
        sería ruido permanente en pantalla."""
        base = self._dibujar(escena)
        escena._direccion_de_tiro = lambda p, im: 1

        assert self._dibujar(escena) == base

    def test_sin_flechas_no_se_dibuja_nada(self, escena) -> None:
        """Prometer un tiro que no se puede hacer es peor que no dibujar."""
        escena._direccion_de_tiro = lambda p, im: pygame.Vector2(0.85, -0.5)
        con_flechas = self._dibujar(escena)

        escena._player.arco.municion = 0
        sin_flechas = self._dibujar(escena)

        assert sin_flechas < con_flechas


class TestElTensado:
    """AUD-195 — mantener pulsado carga el tiro.

    La regla que ordena todo lo demás: **añadir el tensado no puede empeorar
    el disparo de quien no tense**. Un toque rápido tiene que salir exactamente
    igual que antes de que esta mecánica existiera, o los enemigos colocados en
    los 17 mapas ya calibrados se quedan fuera de alcance (invariante 2).
    """

    def test_un_toque_rapido_dispara_como_siempre(self) -> None:
        """La primera versión puso el suelo en 0,6 y el tiro sin cargar salía a
        252 px/s en vez de a 420: quien no tensara disparaba peor que antes."""
        flecha = ArcoDelJugador().disparar(ORIGEN, 1)

        assert flecha is not None
        assert flecha.velocity.length() == pytest.approx(VELOCIDAD)

    def test_tensar_premia(self) -> None:
        arco = ArcoDelJugador()
        arco.tensar(TIEMPO_DE_TENSADO)
        flecha = arco.disparar(ORIGEN, 1)

        assert flecha is not None
        assert flecha.velocity.length() > VELOCIDAD

    def test_la_potencia_crece_con_el_tiempo_y_topa(self) -> None:
        arco = ArcoDelJugador()
        assert arco.potencia == pytest.approx(POTENCIA_MINIMA)

        arco.tensar(TIEMPO_DE_TENSADO / 2)
        media = arco.potencia
        assert POTENCIA_MINIMA < media < POTENCIA_MAXIMA

        arco.tensar(TIEMPO_DE_TENSADO * 3)
        assert arco.potencia == pytest.approx(POTENCIA_MAXIMA), "la carga no topa"

    def test_disparar_suelta_la_tension(self) -> None:
        """Si no, el siguiente tiro saldría cargado sin que nadie lo pidiera."""
        arco = ArcoDelJugador()
        arco.tensar(TIEMPO_DE_TENSADO)
        arco.disparar(ORIGEN, 1)

        assert not arco.tensando
        assert arco.potencia == pytest.approx(POTENCIA_MINIMA)

    def test_un_arco_vacio_no_acumula_tension(self) -> None:
        """Tensar sin flechas dejaría el arco cargado esperando a la recarga, y
        el primer tiro tras recuperar munición saldría con una potencia que el
        jugador no eligió."""
        arco = ArcoDelJugador()
        arco.municion = 0
        arco.tensar(TIEMPO_DE_TENSADO)

        assert not arco.tensando

    def test_la_trayectoria_se_estira_al_tensar(self) -> None:
        """Es la mitad del valor del tensado: sin verlo, cargar sería una
        espera a ciegas."""
        direccion = pygame.Vector2(1, -0.4)
        floja = trayectoria(ORIGEN, direccion, potencia=POTENCIA_MINIMA)
        cargada = trayectoria(ORIGEN, direccion, potencia=POTENCIA_MAXIMA)

        assert cargada[-1].x - ORIGEN.x > (floja[-1].x - ORIGEN.x) * 1.3


class TestLaCalibracionDeLaCaida:
    """Los números del comentario de `GRAVEDAD_FLECHA`, comprobados.

    Están escritos en el código como justificación de por qué 180 y no 340. Si
    alguien cambia la constante, esta prueba dice qué se rompe.
    """

    def _caida_a(self, baldosas: int) -> float:
        puntos = trayectoria(ORIGEN, 1, pasos=40)
        objetivo = baldosas * 16
        for p in puntos:
            if p.x - ORIGEN.x >= objetivo:
                return p.y - ORIGEN.y
        pytest.fail(f"la flecha no llega a {baldosas} baldosas")

    def test_de_cerca_se_apunta_de_frente(self) -> None:
        """A diez baldosas la caída es menor que la altura del jugador (32 px),
        así que el combate cercano no cambia para nadie."""
        assert self._caida_a(10) < 32.0

    def test_de_lejos_hay_que_compensar(self) -> None:
        """A veinte baldosas la caída es más de un cuerpo: ahí apuntar es una
        habilidad, que es lo que hace útil la previsualización."""
        assert self._caida_a(20) > 32.0

    def test_la_gravedad_de_la_flecha_es_menor_que_la_del_jugador(self) -> None:
        from src.engine.core import settings

        assert GRAVEDAD_FLECHA < settings.GRAVITY / 2, (
            "una flecha que cae como un cuerpo es inservible a media distancia"
        )
