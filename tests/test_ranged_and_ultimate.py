"""
El arco del jugador, y el ultimate que era inalcanzable.

F4.2
====
Dos peticiones de los estudiantes en la misma frase: *«si el player puede
tener más ataques ya sea con un arco o un arma hacer disparos y revisar el
ultimate o el especial»*.

El ultimate: medido, no supuesto
---------------------------------
`UltimateState` estaba completo —animación propia, hitbox de 96×64,
multiplicador de daño ×3— y `helpers.py` exigía `special_meter >=
special_meter_max` (100) para entrar. **Nada en todo el proyecto subía el
medidor**: se inicializaba a 0, se ponía a 0 al gastarlo, y no había un solo
`+=` en ninguna parte. Comprobado con 300 golpes simulados: seguía en 0,0.

El HUD sí lo dibujaba, así que el jugador veía una barra que no se llenaba
nunca. Es la misma forma que la iluminación que no iluminaba y las trece demos
que dibujaban en una esquina: un sistema correcto que no llegaba al jugador.

El arco
-------
Los tres ataques eran cuerpo a cuerpo. Contra un enemigo volador o al otro
lado de un foso no había nada que hacer salvo esperar.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.entities.ranged_weapon import (
    CADENCIA,
    MUNICION_MAXIMA,
    ArcoDelJugador,
)

DT = 1.0 / 60.0


@pytest.fixture(autouse=True)
def _pygame():
    from src.engine.core import settings

    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))


@pytest.fixture
def jugador():
    from src.framework.entities.player import Player

    return Player(pygame.Vector2(0, 0))


class _Blanco:
    """Lo mínimo que el arco necesita de un objetivo."""

    def __init__(self, x: int, y: int) -> None:
        self.rect = pygame.Rect(x, y, 24, 32)
        self.is_alive = True
        self.golpes: list[float] = []

    def apply_hit(self, dano: float, origen: tuple[int, int]) -> None:
        self.golpes.append(dano)


class TestElUltimateSePuedeAlcanzar:
    """El defecto principal: la barra no subía nunca."""

    def test_al_empezar_no_esta_listo(self, jugador):
        assert jugador.special_meter == 0.0
        assert not jugador.ultimate_listo

    def test_golpear_llena_el_medidor(self, jugador):
        """Antes de F4.2 esto se quedaba en 0,0 para siempre."""
        jugador.consume_hitbox()
        assert jugador.special_meter > 0.0, (
            "conectar un golpe no sube el medidor: el ultimate vuelve a ser "
            "inalcanzable"
        )

    def test_doce_golpes_lo_llenan(self, jugador):
        for _ in range(12):
            jugador.consume_hitbox()
        assert jugador.ultimate_listo

    def test_once_no_bastan(self, jugador):
        """Que sea alcanzable no significa que sea gratis."""
        for _ in range(11):
            jugador.consume_hitbox()
        assert not jugador.ultimate_listo

    def test_el_medidor_no_pasa_de_su_tope(self, jugador):
        for _ in range(60):
            jugador.consume_hitbox()
        assert jugador.special_meter == jugador.special_meter_max

    def test_el_redondeo_no_deja_la_barra_llena_sin_activarse(self, jugador):
        """Doce sumas de 100/12 dan 99,99999999999999, no 100.

        Sin margen en la comparación, el jugador ve la barra llena y el
        ultimate no entra: el mismo defecto de F4.2, reintroducido por una
        comparación de flotantes.
        """
        for _ in range(12):
            jugador.consume_hitbox()
        assert jugador.special_meter < 100.0 + 1e-9
        assert jugador.ultimate_listo, (
            f"medidor a {jugador.special_meter!r} y el ultimate sigue bloqueado"
        )

    def test_la_transicion_consulta_ultimate_listo(self):
        """La regla vive en un solo sitio.

        `helpers.py` comparaba el medidor a pelo con un `>=`. Duplicar la
        comparación es cómo se reintroduce el fallo del redondeo.
        """
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent
        texto = (raiz / "src/framework/entities/states/helpers.py").read_text(encoding="utf-8")
        assert "player.ultimate_listo" in texto
        assert "special_meter >= player.special_meter_max" not in texto

    def test_usarlo_vacia_el_medidor(self, jugador):
        """No cobrarlo lo convertiría en el ataque por defecto."""
        import inspect

        from src.framework.entities.states import ability

        fuente = inspect.getsource(ability.UltimateState.enter)
        assert "special_meter = 0.0" in fuente


class TestElArcoDispara:
    def test_dispara_una_flecha(self):
        arco = ArcoDelJugador()
        flecha = arco.disparar(pygame.Vector2(0, 0), direccion=1)
        assert flecha is not None
        assert arco.flechas == [flecha]

    def test_la_flecha_va_hacia_donde_mira_el_jugador(self):
        arco = ArcoDelJugador()
        derecha = arco.disparar(pygame.Vector2(0, 0), direccion=1)
        arco._espera = 0.0
        izquierda = arco.disparar(pygame.Vector2(0, 0), direccion=-1)
        assert derecha.velocity.x > 0
        assert izquierda.velocity.x < 0

    def test_gasta_municion(self):
        arco = ArcoDelJugador()
        arco.disparar(pygame.Vector2(0, 0), 1)
        assert arco.municion == MUNICION_MAXIMA - 1

    def test_sin_municion_no_dispara(self):
        arco = ArcoDelJugador()
        for _ in range(MUNICION_MAXIMA):
            arco._espera = 0.0
            assert arco.disparar(pygame.Vector2(0, 0), 1) is not None
        arco._espera = 0.0
        assert arco.vacio
        assert arco.disparar(pygame.Vector2(0, 0), 1) is None

    def test_la_cadencia_impide_vaciar_el_carcaj_de_golpe(self):
        """Sin cadencia, mantener pulsado gasta las cinco en un fotograma."""
        arco = ArcoDelJugador()
        arco.disparar(pygame.Vector2(0, 0), 1)
        assert arco.disparar(pygame.Vector2(0, 0), 1) is None
        for _ in range(int(CADENCIA / DT) + 2):
            arco.update(DT)
        assert arco.disparar(pygame.Vector2(0, 0), 1) is not None

    def test_la_flecha_caduca_y_se_retira(self):
        """Si no se retiraran, la lista crecería toda la partida."""
        arco = ArcoDelJugador()
        arco.disparar(pygame.Vector2(0, 0), 1)
        for _ in range(300):
            arco.update(DT)
        assert arco.flechas == []


class TestElArcoGolpea:
    def test_informa_del_impacto(self):
        arco = ArcoDelJugador()
        blanco = _Blanco(4, 0)
        arco.disparar(pygame.Vector2(0, 0), 1)
        impactos = arco.impactos_contra([blanco])
        assert len(impactos) == 1

    def test_una_flecha_golpea_a_un_solo_objetivo(self):
        arco = ArcoDelJugador()
        a, b = _Blanco(4, 0), _Blanco(6, 0)
        arco.disparar(pygame.Vector2(0, 0), 1)
        impactos = arco.impactos_contra([a, b])
        assert len(impactos) == 1, "una flecha atravesó a dos enemigos"

    def test_no_golpea_a_los_muertos(self):
        arco = ArcoDelJugador()
        blanco = _Blanco(4, 0)
        blanco.is_alive = False
        arco.disparar(pygame.Vector2(0, 0), 1)
        assert arco.impactos_contra([blanco]) == []

    def test_no_aplica_el_dano_por_su_cuenta(self):
        """Quién puede dañar a quién es regla del escenario, no del arma."""
        arco = ArcoDelJugador()
        blanco = _Blanco(4, 0)
        arco.disparar(pygame.Vector2(0, 0), 1)
        arco.impactos_contra([blanco])
        assert blanco.golpes == []

    def test_una_flecha_se_para_contra_un_muro(self):
        arco = ArcoDelJugador()
        arco.disparar(pygame.Vector2(0, 0), 1)
        arco.choca_con_muros([pygame.Rect(-8, -8, 32, 32)])
        arco.update(DT)
        assert arco.flechas == []

    def test_sin_muro_la_flecha_sigue(self):
        arco = ArcoDelJugador()
        arco.disparar(pygame.Vector2(0, 0), 1)
        arco.choca_con_muros([pygame.Rect(900, 900, 8, 8)])
        arco.update(DT)
        assert len(arco.flechas) == 1


class TestElArcoSeRecarga:
    def test_golpear_cuerpo_a_cuerpo_devuelve_una_flecha(self, jugador):
        """Recompensa acercarse en vez de premiar la paciencia."""
        jugador.arco.municion = 0
        jugador.consume_hitbox()
        assert jugador.arco.municion == 1

    def test_no_pasa_del_maximo(self):
        arco = ArcoDelJugador()
        arco.recargar(50)
        assert arco.municion == MUNICION_MAXIMA

    def test_dice_cuantas_entraron_de_verdad(self):
        arco = ArcoDelJugador()
        assert arco.recargar(3) == 0  # ya estaba lleno
        arco.municion = MUNICION_MAXIMA - 2
        assert arco.recargar(5) == 2

    def test_llenar_deja_el_carcaj_completo(self):
        arco = ArcoDelJugador()
        arco.municion = 0
        arco.llenar()
        assert arco.municion == MUNICION_MAXIMA


class TestElJugadorLlevaElArco:
    def test_lo_tiene_desde_el_principio(self, jugador):
        assert isinstance(jugador.arco, ArcoDelJugador)
        assert jugador.arco.municion == MUNICION_MAXIMA

    def test_existe_la_accion_de_disparar(self):
        """Sin acción propia habría que robarle el botón a otro ataque."""
        from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action

        assert hasattr(Action, "RANGED_ATTACK")
        assert DEFAULT_KEY_BINDINGS.get(Action.RANGED_ATTACK)

    def test_la_escena_lo_actualiza(self):
        from src.framework.scenes.stage_scene import StageScene

        assert hasattr(StageScene, "_actualizar_arco")


class TestNoReutilizaUnSegundoProyectil:
    """AUD-099 acaba de retirar dos implementaciones duplicadas del motor.

    Escribir una segunda clase de proyectil habría repetido ese error y
    obligado al estudiante a aprender dos.
    """

    def test_usa_el_projectile_que_ya_existia(self):
        from src.framework.entities.enemy_shooter import Projectile

        arco = ArcoDelJugador()
        flecha = arco.disparar(pygame.Vector2(0, 0), 1)
        assert isinstance(flecha, Projectile)


class TestLaFlechaNoAtraviesaAlEnemigo:
    """El fallo clásico del proyectil rápido, medido antes de arreglarlo.

    La flecha mide **4 px** y viaja a 420 px/s: a 60 fotogramas por segundo
    avanza **7 px por fotograma**. Comprobar sólo dónde acaba se salta a
    cualquier objetivo más estrecho que 3 px, y deja pasar una flecha que en
    un fotograma está delante del enemigo y en el siguiente detrás.

    Pasa una vez de cada muchas y parece «mala suerte», que es lo que lo hace
    difícil de encontrar jugando.
    """

    def test_un_enemigo_estrecho_recibe_el_flechazo(self):
        arco = ArcoDelJugador()
        # Un poste de 2 px: más estrecho que el avance por fotograma.
        poste = _Blanco(6, 0)
        poste.rect = pygame.Rect(6, 0, 2, 32)
        arco.disparar(pygame.Vector2(0, 0), 1)
        assert arco.impactos_contra([poste]), (
            "la flecha atravesó un objetivo más estrecho que su avance por "
            "fotograma"
        )

    def test_lo_que_queda_lejos_sigue_sin_recibir_nada(self):
        """El barrido amplía el alcance de un fotograma, no lo vuelve infinito."""
        arco = ArcoDelJugador()
        arco.disparar(pygame.Vector2(0, 0), 1)
        assert arco.impactos_contra([_Blanco(400, 0)]) == []

    def test_una_pared_fina_para_la_flecha(self):
        arco = ArcoDelJugador()
        arco.disparar(pygame.Vector2(0, 0), 1)
        arco.choca_con_muros([pygame.Rect(6, -16, 2, 64)])
        arco.update(DT)
        assert arco.flechas == []
