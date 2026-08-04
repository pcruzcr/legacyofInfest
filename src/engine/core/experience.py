"""
Module: experience
System: engine.core
Academic Unit: N/A
Description: AUD-249 — la experiencia que deja cada enemigo, y los puntos de
habilidad que se ganan al subir de nivel.

Por qué existe, y por qué NO son monedas
-----------------------------------------
La economía de monedas ya funciona de punta a punta: `coins_for()` dice cuánto
suelta cada enemigo, `_soltar_botin` lo deja en el suelo y la tienda lo gasta.
Colgar de ahí también las habilidades daría **dos formas de comprar lo mismo** y
convertiría el árbol en una lista de la compra: quien farmee monedas para
consumibles se encuentra el árbol regalado, y quien las gaste en la tienda se
queda sin habilidades sin saber por qué.

Así que se reparten los papeles: **las monedas compran cosas que se consumen o
se equipan; la experiencia compra lo permanente**. La experiencia no se puede
farmear en la tienda ni perder al comprar, y sube sola jugando, que es lo que
un árbol de habilidades necesita para no bloquear a nadie.

De dónde sale la clasificación
-------------------------------
La tabla de experiencia por tipo **no existe**: se deriva de `_tipo_de()`, la
misma lectura de `entity_id` que ya usan la puntuación y las monedas. Una
tercera tabla escrita a mano sería una tercera cosa que se desincroniza, y este
repositorio ya tiene la cicatriz de eso (AUD-007, tres manifiestos de
dependencias que no coincidían).

Un tipo desconocido —los enemigos de las entregas de estudiantes: `LaSoda*`,
`CuadernoVolador`, `EstudianteInfectado`— da experiencia mínima pero **nunca
cero**, por la misma razón que las monedas: un nivel hecho sólo con enemigos
propios tiene que poder hacer progresar al jugador.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.engine.core.score_system import _tipo_de

if TYPE_CHECKING:
    from src.engine.core.event_bus import EventBus

logger = logging.getLogger(__name__)

#: Experiencia por tipo de enemigo. Proporcional a lo que cuesta matarlo, no a
#: lo que puntúa: la puntuación premia el estilo y esto premia el riesgo.
_EXP_BY_TYPE: dict[str, int] = {
    "walker": 10,
    "flying": 12,
    "shooter": 15,
    "charger": 18,
    "archer": 18,
    "brute": 25,
    "caster": 25,
    "assassin": 30,
    "boss": 200,
}

#: Lo que da un enemigo que no está en la tabla. Bajo, nunca cero.
_EXP_MINIMA = 5

#: Experiencia del primer nivel. Cada nivel siguiente cuesta este valor
#: multiplicado por el nivel, o sea una curva cuadrática acumulada: el nivel N
#: llega a los `_EXP_BASE * N * (N + 1) / 2` puntos totales.
#:
#: Cuadrática y no exponencial a propósito. Con exponencial, los últimos
#: niveles del árbol quedan fuera del alcance de una partida normal y el
#: contenido que cuelga de ellos no lo ve nadie; con lineal, el jugador termina
#: con más puntos que hojas que gastar. La cuadrática mantiene el ritmo.
_EXP_BASE = 100

#: Puntos de habilidad que da subir un nivel.
PUNTOS_POR_NIVEL = 1


def exp_for(entity_id: str) -> int:
    """Experiencia que deja este enemigo al morir.

    Pública como `coins_for`: una entrega puede consultarla para su propio
    enemigo, y la interfaz la usa para enseñar cuánto vale lo que acabas de
    matar.
    """
    return _EXP_BY_TYPE.get(_tipo_de(entity_id), _EXP_MINIMA)


def exp_para_nivel(nivel: int) -> int:
    """Experiencia **total** acumulada que hace falta para alcanzar `nivel`.

    El nivel 1 es el de salida y cuesta 0.
    """
    if nivel <= 1:
        return 0
    n = nivel - 1
    return _EXP_BASE * n * (n + 1) // 2


def nivel_de(exp_total: int) -> int:
    """El nivel que corresponde a esa experiencia acumulada."""
    nivel = 1
    while exp_para_nivel(nivel + 1) <= exp_total:
        nivel += 1
    return nivel


class ExperienceSystem:
    """Acumula experiencia por enemigo derrotado y reparte puntos de habilidad.

    Mismo patrón que `ScoreSystem`: instancia compartida, bus inyectado con
    `bind_bus()` y no buscado, y persistencia explícita. Se copia a conciencia
    —dos sistemas que escuchan el mismo suceso deberían montarse igual— y la
    razón de que el bus se inyecte está en `achievements.py`: buscarlo desde
    dentro acopla el núcleo al juego y hace imposible probarlo aislado.
    """

    _instance: ExperienceSystem | None = None

    @classmethod
    def get_instance(cls) -> ExperienceSystem:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def _reset_instance(cls) -> None:
        """Sólo para las pruebas: el estado es de proceso y contamina."""
        cls._instance = None

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._exp: int = 0
        #: Puntos ya concedidos por niveles. Se guarda aparte del nivel actual
        #: porque **gastar un punto no baja de nivel**: son dos contadores con
        #: vidas distintas, y derivar uno del otro haría que al comprar una
        #: habilidad el jugador pareciera haber retrocedido.
        self._puntos_disponibles: int = 0
        self._puntos_concedidos: int = 0
        self._bus: EventBus | None = None
        self._handler: Any = None
        if event_bus is not None:
            self.bind_bus(event_bus)

    def bind_bus(self, bus: EventBus | None) -> None:
        """Escucha la muerte de enemigos en este bus.

        Guarda el manejador en un atributo porque el bus mantiene las
        suscripciones **débilmente**: sin una referencia viva, el recolector se
        lleva el cierre y el sistema deja de contar sin un solo error, que es
        el fallo que documenta `stage_parts/senales.py`.
        """
        from src.engine.core.events import Events

        self._bus = bus
        if bus is None:
            return
        self._handler = self._on_enemy_died
        bus.subscribe(Events.ENEMY_DIED, self._handler)

    def _on_enemy_died(self, **data: Any) -> None:
        self.grant(exp_for(str(data.get("entity_id", ""))))

    def grant(self, cantidad: int) -> int:
        """Suma experiencia y devuelve los puntos de habilidad que ha generado.

        Devuelve los puntos —y no nada— para que quien lo llame pueda avisar al
        jugador en el momento. Un punto de habilidad que aparece en un menú sin
        que nadie lo anuncie es un punto que no se gasta.
        """
        if cantidad <= 0:
            return 0
        self._exp += cantidad
        objetivo = (nivel_de(self._exp) - 1) * PUNTOS_POR_NIVEL
        nuevos = objetivo - self._puntos_concedidos
        if nuevos > 0:
            self._puntos_concedidos = objetivo
            self._puntos_disponibles += nuevos
            return nuevos
        return 0

    @property
    def exp(self) -> int:
        return self._exp

    @property
    def nivel(self) -> int:
        return nivel_de(self._exp)

    @property
    def puntos(self) -> int:
        """Puntos de habilidad sin gastar."""
        return self._puntos_disponibles

    def progreso_del_nivel(self) -> tuple[int, int]:
        """(experiencia dentro del nivel, la que hace falta para el siguiente).

        Para la barra de la interfaz. Devolver los dos números en vez de una
        fracción evita que cada pantalla rehaga la resta y se equivoque en el
        último nivel.
        """
        n = self.nivel
        base = exp_para_nivel(n)
        siguiente = exp_para_nivel(n + 1)
        return self._exp - base, siguiente - base

    def spend(self, cantidad: int = 1) -> bool:
        """Gasta puntos. Devuelve False si no hay bastantes, sin gastar nada.

        Todo o nada: un gasto parcial dejaría al jugador sin puntos y sin la
        habilidad, que es la peor de las dos cosas.
        """
        if cantidad <= 0 or cantidad > self._puntos_disponibles:
            return False
        self._puntos_disponibles -= cantidad
        return True

    def reset(self) -> None:
        self._exp = 0
        self._puntos_disponibles = 0
        self._puntos_concedidos = 0

    def to_dict(self) -> dict[str, int]:
        """Estado serializable. Lo guarda quien lleve la partida.

        Se guardan los tres números y no sólo la experiencia: los puntos
        gastados no se pueden deducir de ella, y perderlos al cargar
        significaría devolverle al jugador habilidades que ya compró.
        """
        return {
            "exp": self._exp,
            "puntos": self._puntos_disponibles,
            "concedidos": self._puntos_concedidos,
        }

    def from_dict(self, datos: dict[str, Any]) -> None:
        """Restaura el estado. Un fichero roto deja el sistema a cero, no a
        medias: preferimos que el jugador rehaga progreso a que el juego cargue
        con puntos negativos."""
        try:
            self._exp = max(0, int(datos.get("exp", 0)))
            self._puntos_disponibles = max(0, int(datos.get("puntos", 0)))
            self._puntos_concedidos = max(0, int(datos.get("concedidos", 0)))
        except (TypeError, ValueError):
            logger.warning("progreso de experiencia ilegible; se empieza de cero")
            self.reset()


def get_experience() -> ExperienceSystem:
    """Atajo con el mismo nombre que `get_inventory()`."""
    return ExperienceSystem.get_instance()
