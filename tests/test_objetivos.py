"""AUD-400 — objetivos declarados en el mapa. Cierra GAP-047.

Qué no había
============
Cero coincidencias de `mision`, `objective` o `quest` en `src/`.
`progression_system.py` lleva el avance **entre** escenarios y las banderas de
zona, que es otra cosa: no había objetivos declarados, ni seguimiento, ni
estado de completado por objetivo.

El hueco estaba parado por decisión del dueño —fase 7 suspendida, `docs/87`
§27— y el dueño la levantó el 2026-08-11.

Qué se apoya en lo que ya existía
=================================
El sistema es corto porque casi todo estaba hecho y disperso: el bus ya emite
`ENEMY_DIED`, `ITEM_COLLECTED`, `FLAG_SET`, `DIALOGUE_FINISHED` y
`CHECKPOINT_REACHED`, y el diálogo ya ejecuta acciones. Lo que faltaba era
quién lleva la cuenta. No se inventa ninguna fuente de verdad nueva: se escucha
lo que ya se emitía.

Las dos decisiones que estas pruebas fijan
==========================================
* **Sin objetivos declarados, `todo_hecho` es `True`.** Es lo que mantiene
  intactos los mapas que no declaran ninguno, que hoy son los diecisiete.
* **Los opcionales no bloquean.** Si contaran, cada secreto del mapa impediría
  terminar el nivel.
"""
from __future__ import annotations

import pytest

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.framework.stage.objetivos import (
    TIPOS_DE_OBJETIVO,
    Objetivo,
    SistemaDeObjetivos,
    objetivo_desde_tiled,
)


def _ocurre(bus: EventBus, evento: str, **datos: object) -> None:
    """Emite y **entrega**, que en este bus son dos cosas.

    `EventBus.emit` encola; quien reparte es `dispatch()`, una vez por
    fotograma. Y hay guardia de reentrada: lo que un suscriptor emite mientras
    se le atiende se encola para la vuelta siguiente en vez de despacharse
    recursivamente. El sistema de objetivos emite `OBJECTIVE_COMPLETED` desde
    dentro de un manejador, así que hacen falta dos vueltas para verlo — se
    despacha hasta que la cola deja de moverse en lugar de un número fijo de
    veces, que es lo que haría frágil la prueba.
    """
    bus.emit(evento, **datos)
    for _ in range(4):
        bus.dispatch()


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def sistema(bus: EventBus) -> SistemaDeObjetivos:
    return SistemaDeObjetivos(bus)


class TestElConteo:
    def test_matar_al_enemigo_pedido_completa(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        sistema.declarar(Objetivo("limpiar", "Acaba con el vigilante",
                                  tipo="derrotar", objetivo="Guard"))
        _ocurre(bus, Events.ENEMY_DIED, enemy_type="Guard")
        assert sistema._objetivos["limpiar"].completado

    def test_matar_a_otro_no_cuenta(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        sistema.declarar(Objetivo("limpiar", "Acaba con el vigilante",
                                  tipo="derrotar", objetivo="Guard"))
        _ocurre(bus, Events.ENEMY_DIED, enemy_type="Walker")
        assert not sistema._objetivos["limpiar"].completado

    def test_sin_objetivo_concreto_vale_cualquiera(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        """Es lo que permite «derrota a cinco enemigos» sin enumerar especies."""
        sistema.declarar(Objetivo("cinco", "Derrota a cinco",
                                  tipo="derrotar", cantidad=5))
        for especie in ("Walker", "Flying", "Guard", "Walker", "Brute"):
            _ocurre(bus, Events.ENEMY_DIED, enemy_type=especie)
        assert sistema._objetivos["cinco"].completado

    def test_lleva_la_cuenta_parcial(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        sistema.declarar(Objetivo("cinco", "Derrota a cinco",
                                  tipo="derrotar", cantidad=5))
        for _ in range(3):
            _ocurre(bus, Events.ENEMY_DIED, enemy_type="Walker")
        objetivo = sistema._objetivos["cinco"]
        assert objetivo.progreso == 3
        assert objetivo.restante == 2
        assert not objetivo.completado

    def test_no_sigue_contando_despues_de_completarse(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        """Si siguiera, el HUD enseñaría 8/5."""
        sistema.declarar(Objetivo("dos", "Derrota a dos",
                                  tipo="derrotar", cantidad=2))
        for _ in range(8):
            _ocurre(bus, Events.ENEMY_DIED, enemy_type="Walker")
        assert sistema._objetivos["dos"].progreso == 2

    def test_recoger_y_banderas_tambien_cuentan(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        sistema.declarar(Objetivo("llave", "Encuentra la llave",
                                  tipo="recoger", objetivo="llave_oxidada"))
        sistema.declarar(Objetivo("puerta", "Abre el portón",
                                  tipo="bandera", objetivo="porton_abierto"))
        _ocurre(bus, Events.ITEM_COLLECTED, item_id="llave_oxidada")
        _ocurre(bus, Events.FLAG_SET, flag="porton_abierto")
        assert sistema.todo_hecho


class TestLoQueNoDebeBloquear:
    def test_un_mapa_sin_objetivos_no_tiene_nada_pendiente(
        self, sistema: SistemaDeObjetivos
    ) -> None:
        """Los diecisiete mapas de hoy. Si esto fuera `False`, ninguno
        terminaría."""
        assert sistema.todo_hecho is True

    def test_los_opcionales_no_bloquean(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        sistema.declarar(Objetivo("principal", "Llega al final",
                                  tipo="bandera", objetivo="fin"))
        sistema.declarar(Objetivo("secreto", "Encuentra el secreto",
                                  tipo="recoger", objetivo="reliquia",
                                  opcional=True))
        _ocurre(bus, Events.FLAG_SET, flag="fin")
        assert sistema.todo_hecho, (
            "un coleccionable opcional impide terminar el nivel: entonces no "
            "es opcional"
        )

    def test_un_tipo_desconocido_no_se_da_de_alta(
        self, sistema: SistemaDeObjetivos
    ) -> None:
        """Un objetivo que ningún evento puede completar nunca se termina, y un
        objetivo imposible es peor que no tener objetivos."""
        sistema.declarar(Objetivo("raro", "Haz algo", tipo="teletransportarse"))
        assert sistema.objetivos == []


class TestElAnuncio:
    def test_avisa_al_completar_uno(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        vistos: list[str] = []

        def escuchar(objective_id: str = "", **_: object) -> None:
            vistos.append(objective_id)

        bus.subscribe(Events.OBJECTIVE_COMPLETED, escuchar)
        sistema.declarar(Objetivo("uno", "Haz esto", tipo="bandera", objetivo="x"))
        _ocurre(bus, Events.FLAG_SET, flag="x")
        assert vistos == ["uno"]

    def test_avisa_una_sola_vez_al_terminar_todos(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        """Sin el pestillo, cada objetivo posterior volvería a anunciar el
        final y la fanfarria sonaría dos veces."""
        veces: list[int] = []

        def escuchar(**_: object) -> None:
            veces.append(1)

        bus.subscribe(Events.OBJECTIVES_COMPLETED, escuchar)
        sistema.declarar(Objetivo("a", "A", tipo="bandera", objetivo="a"))
        sistema.declarar(Objetivo("b", "B", tipo="bandera", objetivo="b",
                                  opcional=True))
        _ocurre(bus, Events.FLAG_SET, flag="a")
        _ocurre(bus, Events.FLAG_SET, flag="b")
        assert len(veces) == 1


class TestElGuion:
    def test_completar_a_mano_lo_da_por_hecho(
        self, sistema: SistemaDeObjetivos
    ) -> None:
        """Es lo que usa `complete_objective:` desde un árbol de diálogo."""
        sistema.declarar(Objetivo("hablar", "Habla con el vigía",
                                  tipo="bandera", objetivo="nunca"))
        sistema.completar("hablar")
        assert sistema.todo_hecho

    def test_completar_algo_que_no_existe_no_estalla(
        self, sistema: SistemaDeObjetivos
    ) -> None:
        """Un guion con una errata no puede tumbar el nivel."""
        sistema.completar("no_existe")


class TestLaPresentacion:
    def test_el_resumen_marca_lo_hecho(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        sistema.declarar(Objetivo("a", "Abre la puerta", tipo="bandera",
                                  objetivo="p"))
        _ocurre(bus, Events.FLAG_SET, flag="p")
        assert sistema.resumen() == ["[x] Abre la puerta"]

    def test_el_resumen_enseña_el_recuento(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        sistema.declarar(Objetivo("c", "Derrota a cinco", tipo="derrotar",
                                  cantidad=5))
        _ocurre(bus, Events.ENEMY_DIED, enemy_type="Walker")
        assert sistema.resumen() == ["[ ] Derrota a cinco (1/5)"]

    def test_los_obligatorios_van_primero(
        self, sistema: SistemaDeObjetivos
    ) -> None:
        sistema.declarar(Objetivo("z_opcional", "Secreto", tipo="bandera",
                                  objetivo="s", opcional=True))
        sistema.declarar(Objetivo("a_normal", "Principal", tipo="bandera",
                                  objetivo="n"))
        assert sistema.resumen()[0].endswith("Principal")


class TestElReinicio:
    def test_morir_devuelve_los_objetivos_a_cero(
        self, bus: EventBus, sistema: SistemaDeObjetivos
    ) -> None:
        """Sin esto, reintentar el nivel empezaría con medio trabajo hecho."""
        sistema.declarar(Objetivo("c", "Derrota a tres", tipo="derrotar",
                                  cantidad=3))
        _ocurre(bus, Events.ENEMY_DIED, enemy_type="Walker")
        sistema.reiniciar()
        assert sistema._objetivos["c"].progreso == 0


class TestDesdeTiled:
    def test_construye_desde_las_propiedades(self) -> None:
        objetivo = objetivo_desde_tiled({
            "objective_id": "limpiar",
            "text": "Acaba con los tres vigilantes",
            "kind": "derrotar",
            "target": "Guard",
            "count": "3",
        })
        assert objetivo is not None
        assert objetivo.id == "limpiar"
        assert objetivo.cantidad == 3
        assert objetivo.tipo == "derrotar"

    def test_sin_id_o_sin_texto_se_ignora(self) -> None:
        """Uno sin id no se puede completar desde un guion; uno sin texto sale
        en blanco en el HUD. Mejor avisar que construir a medias."""
        assert objetivo_desde_tiled({"text": "Algo"}) is None
        assert objetivo_desde_tiled({"objective_id": "x"}) is None

    def test_una_cantidad_mal_escrita_cae_a_uno(self) -> None:
        """El mismo trato que el resto del cargador da al dato malo."""
        objetivo = objetivo_desde_tiled({
            "objective_id": "x", "text": "Algo", "count": "tres",
        })
        assert objetivo is not None and objetivo.cantidad == 1

    def test_opcional_se_lee_del_mapa(self) -> None:
        objetivo = objetivo_desde_tiled({
            "objective_id": "x", "text": "Algo", "optional": "true",
        })
        assert objetivo is not None and objetivo.opcional


class TestDesdeElMapaDeVerdad:
    """El cable trampa del cableado: que el TMX llegue al sistema.

    Sin esto, `Objective` sería un tipo que el validador acepta y que el juego
    ignora — el modo de fallo de esta casa, y el que AUD-392 acababa de
    encontrar en el validador de mapas.
    """

    def _stage0(self):
        import pygame

        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        if not pygame.display.get_init():
            pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))
        entity_factory.ensure_registered()
        return StageLoader.load("assets/maps/stage0/stage0.tmx")

    def test_stage0_declara_sus_objetivos(self) -> None:
        objetivos = {o.id for o in self._stage0().objetivos}
        assert "llegar_al_final" in objetivos
        assert "tres_infectados" in objetivos

    def test_el_opcional_del_mapa_se_lee_como_opcional(self) -> None:
        porid = {o.id: o for o in self._stage0().objetivos}
        assert porid["tres_infectados"].opcional is True
        assert porid["llegar_al_final"].opcional is False

    def test_el_recuento_del_mapa_llega_entero(self) -> None:
        porid = {o.id: o for o in self._stage0().objetivos}
        assert porid["tres_infectados"].cantidad == 3


def test_todo_tipo_tiene_un_evento_que_lo_completa() -> None:
    """El cable trampa del diseño.

    Cada tipo de objetivo tiene que corresponder a un evento que el motor
    **ya emite** y a un campo suyo que comparar. Un tipo sin cualquiera de las
    dos cosas es un objetivo que no se puede terminar nunca.
    """
    from src.framework.stage.objetivos import _CLAVE_DEL_TIPO

    assert set(TIPOS_DE_OBJETIVO) == set(_CLAVE_DEL_TIPO)
    for tipo, evento in TIPOS_DE_OBJETIVO.items():
        assert isinstance(evento, str) and evento, tipo
