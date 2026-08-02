"""
Las flechas del arquero y la puñalada del asesino — AUD-149.

El fallo, y por qué nadie lo vio
=================================
`EnemyArcher` y `EnemyAssassin` sobreescribían `check_player_contact` — el
nombre **público**. El motor llama al privado: `StageScene` hace
`enemy._check_player_contact(player)`, y el público es sólo un alias obsoleto
que `EnemyBase` conserva para no romper las entregas de los estudiantes.

Resultado, comprobado antes de tocar nada:

* las **flechas del arquero no hacían daño** y **no se podían parar con el
  parry**: todo eso vivía en el método que nunca se llamaba;
* el **asesino hacía daño de contacto estando invisible**, porque la salida
  temprana que lo impedía estaba en el mismo sitio;
* y su **puñalada al abalanzarse no hacía daño** por lo mismo.

Las tres clases estaban completas y probadas por su nombre. Lo que fallaba era
un guion bajo, y el `_check_player_contact` de la clase base respondía en su
lugar sin quejarse — que es exactamente lo que hace una herencia bien formada
cuando el nombre no coincide.

Por eso estas pruebas llaman por **el camino del motor**, no por el nombre que
más se parece al que uno quiere probar.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


def _jugador(x: float = 200, y: float = 100):
    from src.framework.entities.player import Player

    jugador = Player(pygame.Vector2(x, y))
    jugador._invincibility_timer = 0.0
    return jugador


class _Bus:
    def __init__(self) -> None:
        self.emitidos: list[str] = []

    def emit(self, evento: str, **_datos) -> None:
        self.emitidos.append(evento)

    def subscribe(self, *_a, **_k) -> None:
        pass


class TestLasFlechasLleganAlJugador:
    def _arquero_con_flecha_encima(self, jugador):
        from src.framework.entities.enemy_archer import EnemyArcher

        arquero = EnemyArcher(pygame.Vector2(100, 100))
        arquero._event_bus = _Bus()
        arquero._active_projectiles.clear()
        # Una flecha justo sobre el jugador: es lo que se quiere comprobar,
        # no la puntería del arquero.
        arquero._shoot_cooldown = 0.0
        arquero._player_ref = jugador.rect   # el arquero apunta a un rect
        arquero._fire_arc()
        for proyectil in arquero._active_projectiles:
            proyectil.rect.center = jugador.rect.center
            proyectil.position.update(jugador.position)
        return arquero

    def test_una_flecha_encima_hace_dano(self) -> None:
        jugador = _jugador()
        arquero = self._arquero_con_flecha_encima(jugador)
        if not arquero._active_projectiles:
            pytest.skip("el arquero no llegó a disparar en este montaje")

        vida = jugador.current_health
        # EL CAMINO DEL MOTOR: `StageScene` llama al privado.
        arquero._check_player_contact(jugador)
        assert jugador.current_health < vida, (
            "la flecha atravesó al jugador sin hacerle nada: la comprobación "
            "de proyectiles vive en un método que el motor no llama"
        )

    def test_el_parry_desvia_la_flecha(self) -> None:
        jugador = _jugador()
        arquero = self._arquero_con_flecha_encima(jugador)
        if not arquero._active_projectiles:
            pytest.skip("el arquero no llegó a disparar en este montaje")

        jugador._parry_active = True
        jugador._parry_window = 0.2
        vida = jugador.current_health
        arquero._check_player_contact(jugador)
        assert jugador.current_health == vida, "el parry no protegió"
        assert jugador._parry_success is True

    def test_el_metodo_que_el_motor_llama_es_el_del_arquero(self) -> None:
        """La comprobación que habría evitado todo esto."""
        from src.framework.entities.enemy_archer import EnemyArcher

        assert EnemyArcher._check_player_contact.__qualname__.startswith(
            "EnemyArcher"), (
            "el motor acabaría en la implementación de la clase base y la del "
            "arquero no correría nunca"
        )


class TestLaPunaladaDelAsesino:
    def _asesino(self):
        from src.framework.entities.enemy_assassin import EnemyAssassin

        asesino = EnemyAssassin(pygame.Vector2(200, 100))
        asesino._event_bus = _Bus()
        return asesino

    def test_invisible_no_hace_dano_de_contacto(self) -> None:
        """Un asesino que hace daño estando invisible convierte el sigilo en
        una trampa: el jugador recibe golpes de algo que no ve."""
        jugador = _jugador()
        asesino = self._asesino()
        asesino.rect.center = jugador.rect.center
        asesino._is_cloaked = True
        asesino._is_lunging = False

        vida = jugador.current_health
        asesino._check_player_contact(jugador)
        assert jugador.current_health == vida

    def test_al_abalanzarse_si_hace_dano(self) -> None:
        jugador = _jugador()
        asesino = self._asesino()
        asesino.position.update(jugador.position)
        asesino.rect.center = jugador.rect.center
        asesino._update_rects()
        asesino._is_cloaked = False
        asesino._is_lunging = True
        asesino._lunge_has_hit = False

        vida = jugador.current_health
        asesino._check_player_contact(jugador)
        assert jugador.current_health < vida, (
            "la puñalada no hizo daño: su código estaba en el método que el "
            "motor no llama"
        )

    def test_la_punalada_solo_acierta_una_vez(self) -> None:
        jugador = _jugador()
        asesino = self._asesino()
        asesino.position.update(jugador.position)
        asesino.rect.center = jugador.rect.center
        asesino._update_rects()
        asesino._is_cloaked = False
        asesino._is_lunging = True
        asesino._lunge_has_hit = False

        asesino._check_player_contact(jugador)
        jugador._invincibility_timer = 0.0
        vida = jugador.current_health
        asesino._check_player_contact(jugador)
        assert jugador.current_health == vida, (
            "la misma embestida hizo daño dos veces"
        )

    def test_el_metodo_que_el_motor_llama_es_el_del_asesino(self) -> None:
        from src.framework.entities.enemy_assassin import EnemyAssassin

        assert EnemyAssassin._check_player_contact.__qualname__.startswith(
            "EnemyAssassin")


class TestElAliasObsoletoSigueAhi:
    """Y tiene que seguir: lo llaman entregas de estudiantes.

    Lo que no puede es que una subclase lo sobreescriba creyendo que es el
    camino real, que es justo lo que pasó.
    """

    def test_la_base_conserva_el_alias(self) -> None:
        from src.framework.entities.enemy_base import EnemyBase

        assert hasattr(EnemyBase, "check_player_contact")

    def test_el_alias_avisa_de_que_esta_obsoleto(self) -> None:
        from src.framework.entities.enemy_walker import EnemyWalker

        enemigo = EnemyWalker(pygame.Vector2(0, 0))
        enemigo._event_bus = _Bus()
        with pytest.warns(DeprecationWarning):
            enemigo.check_player_contact(_jugador(x=9000))

    def test_ninguna_subclase_vuelve_a_sobreescribir_el_publico(self) -> None:
        """La prueba que impide que esto se repita.

        Sobreescribir el público es escribir código que el motor no ejecuta, y
        no falla: se queda callado, que es la peor forma de fallar.
        """
        import importlib
        import pkgutil

        from src.framework import entities
        from src.framework.entities.enemy_base import EnemyBase

        culpables = []
        for info in pkgutil.iter_modules(entities.__path__):
            modulo = importlib.import_module(
                f"src.framework.entities.{info.name}")
            for nombre in dir(modulo):
                clase = getattr(modulo, nombre)
                if (isinstance(clase, type) and issubclass(clase, EnemyBase)
                        and clase is not EnemyBase
                        and "check_player_contact" in clase.__dict__):
                    culpables.append(f"{modulo.__name__}.{nombre}")
        assert culpables == [], (
            f"estas clases sobreescriben el alias obsoleto y su código no "
            f"correrá nunca: {culpables}"
        )
