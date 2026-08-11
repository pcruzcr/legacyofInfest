"""AUD-388 — efectos temporales con duración. Cierra GAP-044.

El hueco
========
Había efectos temporales sueltos, cada uno con su temporizador a mano dentro de
`PlayerStateData` —`damage_mult`, `invincibility_timer`, `flash_timer`— y nada
que los agrupara. Consecuencias: no se podía envenenar a un enemigo, ni
ralentizar a nadie, ni escribir un potenciador sin añadir otro campo y otro
temporizador al jugador.

El diseño, decidido por el dueño
================================
Componente ECS con los efectos declarados en datos, y cuatro cosas
modificables: **daño infligido**, **daño recibido**, **velocidad** y **daño por
segundo**.

Por qué nace con consumidor
===========================
Porque un sistema sin consumidor es la especie de defecto que esta sesión lleva
diez lotes cazando. El consumidor es el canal `veneno` de AUD-387: una
`HazardZone` con `damage_type="veneno"` deja de restar vida de golpe y **aplica
veneno**, que sigue restando cuando ya has salido de la charca. Sin eso, el
canal veneno sería daño físico con otro nombre — que es lo que su propia ficha
del catálogo dice que no debe ser.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.combate import efectos
from src.framework.ecs.components import Efectos, Salud, Transform
from src.framework.ecs.world import World


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    yield


class TestElCatalogo:
    def test_trae_los_efectos_de_salida(self):
        assert {"veneno", "lentitud", "fuerza", "escudo"} <= set(efectos.CATALOGO)

    def test_cada_efecto_declara_que_modifica(self):
        for clave, ficha in efectos.CATALOGO.items():
            assert ficha.get("modifica") in efectos.MODIFICABLES, (
                f"«{clave}» modifica {ficha.get('modifica')!r}, que no está en "
                f"{sorted(efectos.MODIFICABLES)}"
            )

    def test_un_efecto_inventado_no_revienta(self):
        assert efectos.existe("veneno")
        assert not efectos.existe("maldicion_lunar")


class TestElComponente:
    def test_nace_vacio(self):
        assert Efectos().activos == []

    def test_aplicar_lo_anota_con_su_duracion(self):
        e = Efectos()
        efectos.aplicar(e, "lentitud", duracion=2.0)
        assert len(e.activos) == 1
        assert e.activos[0].restante == pytest.approx(2.0)

    def test_reaplicar_refresca_en_vez_de_acumular(self):
        """Dos charcas de veneno no envenenan el doble; renuevan el reloj.

        Acumular sin tope es como se acaba con un jugador con veinte capas de
        veneno tras cruzar una sala. Refrescar es la regla más simple que se
        comporta bien, y el dueño eligió el modelo sin acumulación.
        """
        e = Efectos()
        efectos.aplicar(e, "veneno", duracion=3.0)
        efectos.aplicar(e, "veneno", duracion=5.0)
        assert len(e.activos) == 1
        assert e.activos[0].restante == pytest.approx(5.0)

    def test_uno_desconocido_se_ignora(self):
        e = Efectos()
        efectos.aplicar(e, "maldicion_lunar", duracion=1.0)
        assert e.activos == []


class TestLosModificadores:
    def test_sin_efectos_todo_vale_uno(self):
        e = Efectos()
        for que in efectos.MODIFICABLES:
            assert efectos.modificador(e, que) == pytest.approx(1.0)

    def test_la_lentitud_reduce_la_velocidad(self):
        e = Efectos()
        efectos.aplicar(e, "lentitud", duracion=1.0)
        assert efectos.modificador(e, "velocidad") < 1.0

    def test_la_fuerza_aumenta_el_dano(self):
        e = Efectos()
        efectos.aplicar(e, "fuerza", duracion=1.0)
        assert efectos.modificador(e, "dano_infligido") > 1.0

    def test_el_escudo_reduce_el_dano_recibido(self):
        e = Efectos()
        efectos.aplicar(e, "escudo", duracion=1.0)
        assert efectos.modificador(e, "dano_recibido") < 1.0

    def test_dos_efectos_del_mismo_tipo_se_multiplican(self):
        """Distintos efectos sobre la misma estadística componen.

        Se multiplican y no se suman por el mismo motivo que las resistencias
        de AUD-387: multiplicar no puede dar un valor negativo por acumulación,
        y sumar penalizaciones sí.
        """
        e = Efectos()
        efectos.aplicar(e, "lentitud", duracion=1.0)
        uno = efectos.modificador(e, "velocidad")
        efectos.aplicar(e, "atolladero", duracion=1.0)
        assert efectos.modificador(e, "velocidad") < uno


class TestElSistema:
    def _mundo(self) -> tuple[World, int, Efectos, Salud]:
        m = World()
        ef = Efectos()
        sal = Salud(actual=20.0, maxima=20.0)
        e = m.crear(Transform(pygame.Vector2(0, 0), pygame.Rect(0, 0, 16, 16)),
                    ef, sal)
        return m, e, ef, sal

    def test_la_duracion_baja_con_el_tiempo(self):
        from src.framework.ecs import systems as S

        m, _, ef, _ = self._mundo()
        efectos.aplicar(ef, "lentitud", duracion=1.0)
        S.sistema_efectos(m, 0.25)
        assert ef.activos[0].restante == pytest.approx(0.75)

    def test_al_agotarse_desaparece(self):
        from src.framework.ecs import systems as S

        m, _, ef, _ = self._mundo()
        efectos.aplicar(ef, "lentitud", duracion=0.2)
        S.sistema_efectos(m, 0.5)
        assert ef.activos == []

    def test_el_veneno_resta_vida_con_el_tiempo(self):
        """Lo que hace que el canal veneno signifique algo."""
        from src.framework.ecs import systems as S

        m, _, ef, sal = self._mundo()
        efectos.aplicar(ef, "veneno", duracion=2.0)
        S.sistema_efectos(m, 1.0)
        assert sal.actual < 20.0

    def test_el_veneno_no_mata_por_debajo_de_cero(self):
        from src.framework.ecs import systems as S

        m, _, ef, sal = self._mundo()
        sal.actual = 0.3
        efectos.aplicar(ef, "veneno", duracion=10.0)
        S.sistema_efectos(m, 5.0)
        assert sal.actual >= 0.0

    def test_sin_componente_no_hace_nada(self):
        """La mayoría de entidades no tienen efectos; el sistema no puede
        costar por ellas ni reventar."""
        from src.framework.ecs import systems as S

        m = World()
        m.crear(Transform(pygame.Vector2(0, 0), pygame.Rect(0, 0, 8, 8)))
        S.sistema_efectos(m, 1.0)


class TestElVenenoLlegaDesdeElMapa:
    """El cable trampa: sin esto el sistema es correcto y no lo usa nadie.

    Es la lección de AUD-050, AUD-347 y AUD-381, todas de esta misma fase.
    """

    def test_la_zona_de_veneno_envenena(self):
        """Se comprueba **el comportamiento**, no que la palabra aparezca.

        La primera versión de esta prueba buscaba la subcadena «veneno» en el
        código de `HazardSystem` y pasó estando el método **fuera de la
        clase** — la palabra estaba en un comentario del sitio que lo llamaba,
        y la suite completa cazó el `AttributeError` en cinco pruebas ajenas.

        Una prueba que busca texto no comprueba que el código funcione:
        comprueba que alguien escribió la palabra.
        """
        from src.framework.combate import efectos as reglas
        from src.framework.ecs.components import Efectos
        from src.framework.stage.hazard_system import HazardSystem

        class JugadorFalso:
            efectos = Efectos()

        jugador = JugadorFalso()
        HazardSystem._envenenar(jugador, "veneno")
        assert [a.id for a in jugador.efectos.activos] == ["veneno"]

        # Y el canal por defecto no envenena, que es lo que mantiene iguales
        # las zonas de los dieciséis mapas entregados.
        otro = JugadorFalso()
        otro.efectos = Efectos()
        HazardSystem._envenenar(otro, "fisico")
        assert otro.efectos.activos == []
        assert not reglas.existe("fisico")

    def test_la_zona_lo_pide_al_recibir_dano(self):
        """Y que `update` lo llame de verdad, no sólo que el método exista."""
        import inspect

        from src.framework.stage.hazard_system import HazardSystem

        assert "_envenenar" in inspect.getsource(HazardSystem.update), (
            "`update` no aplica el efecto del canal: una charca de veneno "
            "vuelve a ser una zona de daño con otro nombre"
        )

    def test_el_sistema_esta_registrado_en_el_planificador(self):
        import inspect

        from src.framework.scenes.stage_parts import mundo_ecs

        fuente = inspect.getsource(mundo_ecs)
        assert "sistema_efectos" in fuente, (
            "el planificador no ejecuta `sistema_efectos`: las duraciones no "
            "bajarían nunca y el veneno duraría para siempre"
        )
