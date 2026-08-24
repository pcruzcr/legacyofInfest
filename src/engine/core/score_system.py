"""
Module: score_system
System: engine.core
Academic Unit: N/A
Description: Puntos por derrotar enemigos. Escucha `ENEMY_DIED` y acumula
una puntuación según el tipo de enemigo. Persistencia en el directorio del
usuario (`score.json`; AUD-337 lo sacó de `data/score.json`, migrando el
fichero viejo una vez).

Por qué existe
--------------
El juego no tenía ningún conteo de puntos por matar enemigos. Escucha el
evento `ENEMY_DIED` que ya emite `EnemyBase._die()` y no toca el combate.

Aquí decía que «el HUD documentaba un slot de "score" en `09_HUD_SPEC.md`».
**Era falso** y se corrigió en AUD-219: la especificación no tenía ninguna
región de puntuación —comprobado con `grep`, cero apariciones— así que el
sistema no cerraba ningún hueco documentado, cerraba uno real y sin declarar.
AUD-219 añadió la región al contrato y la ató al HUD; el orden importa, porque
el doc es lo que los estudiantes leen para colocar su propia interfaz.

Además de la puntuación, el módulo decide el **botín**: `coins_for()` comparte
la lectura del `entity_id` con los puntos para que no haya dos maneras
distintas de decir «esto es un jefe» (AUD-218).
"""
from __future__ import annotations

import logging
from typing import Any

import orjson

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.engine.core.save_manager import migrar_desde_el_arbol
from src.engine.core.user_settings import user_data_dir

logger = logging.getLogger(__name__)

#: Dónde vive la puntuación del jugador. AUD-337 — nació en
#: `data/score.json`, dentro del árbol del proyecto; una instalación
#: empaquetada puede tener ese árbol en un sitio de sólo lectura, así que
#: el estado del jugador va al directorio del usuario, como las partidas
#: (AUD-157) y los logros. El fichero viejo se migra una vez (no se borra).
_RUTA_POR_DEFECTO = user_data_dir() / "score.json"
_SCORE_PATH = _RUTA_POR_DEFECTO
#: De dónde se migra: el sitio histórico, sólo lectura en empaquetado.
_RUTA_ANTIGUA = settings.PROJECT_ROOT / "data/score.json"

#: Puntos por tipo de enemigo. Los jefes valen mucho más.
#: Se deduce del nombre de la clase (`EnemyWalker` → `walker`).
_SCORE_BY_TYPE: dict[str, int] = {
    "walker": 100,
    "flying": 150,
    "shooter": 200,
    "charger": 250,
    "archer": 250,
    "brute": 300,
    "caster": 300,
    "assassin": 350,
    "boss": 1000,
}


#: Monedas que suelta cada tipo al morir (AUD-218). Son mucho más pequeñas que
#: los puntos porque compran de verdad: con la ropa entre 30 y 50, un peón a 2
#: pone la primera prenda a una docena de enemigos. La puntuación mide la
#: partida; las monedas son el ritmo de la tienda, y no es el mismo número.
_COINS_BY_TYPE: dict[str, int] = {
    "walker": 2,
    "flying": 2,
    "shooter": 3,
    "charger": 3,
    "archer": 3,
    "brute": 4,
    "caster": 4,
    "assassin": 5,
    "boss": 25,
}


def _tipo_de(entity_id: str) -> str:
    """`"EnemyWalker_12345"` → `"walker"`. Cadena vacía si no se reconoce.

    `entity_id` es lo que compone `EnemyBase._die()`: el nombre de la clase y
    el `id()` de la instancia. Se resuelve el tipo una sola vez y las dos
    tablas —puntos y monedas— lo consultan; antes esta lectura vivía dentro de
    `_points_for` y habría que haberla copiado para el botín.
    """
    lower = entity_id.lower()
    if "boss" in lower:
        return "boss"
    for key in _SCORE_BY_TYPE:
        if key in lower:
            return key
    return ""


def _points_for(entity_id: str) -> int:
    """Puntos según el tipo. Un tipo desconocido da un mínimo, no cero."""
    return _SCORE_BY_TYPE.get(_tipo_de(entity_id), 50)


def coins_for(entity_id: str) -> int:
    """Monedas que suelta este enemigo al morir.

    Pública a propósito: la escena la consulta para saber cuánto vale la
    moneda que deja en el suelo, y una entrega puede llamarla para su propio
    enemigo. Un tipo que no está en la tabla —los de las entregas: `LaSoda*`,
    `CuadernoVolador`, `EstudianteInfectado`— da 1: poco, pero nunca cero, o
    un nivel hecho sólo con enemigos propios no daría para comprar nada.
    """
    return _COINS_BY_TYPE.get(_tipo_de(entity_id), 1)


def _migrar_score() -> None:
    """Migra el fichero viejo una vez, y sólo con la ruta de producción.

    Las pruebas redirigen `_SCORE_PATH` a un directorio temporal: ahí no se
    migra nada, el fichero viejo del repositorio es de desarrollo y no tiene
    por qué colarse en una prueba.
    """
    if _SCORE_PATH == _RUTA_POR_DEFECTO:
        migrar_desde_el_arbol(_SCORE_PATH, _RUTA_ANTIGUA)


class ScoreSystem:
    """Acumula puntos por derrotar enemigos y los persiste.

    AUD-219 — instancia compartida y `bind_bus()`.

    El módulo estaba escrito entero y **nadie lo construía**: cero referencias
    a `ScoreSystem` fuera de este fichero. Un sistema que nadie instancia no se
    suscribe a nada, así que matar enemigos no sumaba un punto.

    Se sigue el patrón de `AchievementSystem` y `Bestiary` —los otros dos
    sistemas de progreso— porque el problema es el mismo: la puntuación es una
    sola aunque la escena cambie, y cada escena trae su propio `EventBus`.
    """

    _instance: ScoreSystem | None = None

    @classmethod
    def get_instance(cls) -> ScoreSystem:
        if cls._instance is None:
            cls._instance = ScoreSystem()
        return cls._instance

    @classmethod
    def _reset_instance(cls) -> None:
        """Sólo para pruebas: devuelve el singleton a su estado inicial."""
        if cls._instance is not None:
            cls._instance.bind_bus(None)
        cls._instance = None

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._score: int = 0
        self._bus: EventBus | None = None
        self.load()
        self.bind_bus(event_bus)

    def bind_bus(self, bus: EventBus | None) -> None:
        """Escucha las muertes en `bus`, y deja de escucharlas en el anterior.

        Rebindear al cambiar de escena tiene que **mudar** la suscripción, no
        añadirla: quedándose en los dos buses, cada muerte sumaría el doble en
        cuanto el jugador pasara de un nivel al siguiente.
        """
        if bus is self._bus:
            return
        if self._bus is not None:
            self._bus.unsubscribe(Events.ENEMY_DIED, self._on_enemy_died)
        self._bus = bus
        if bus is not None:
            # El bus guarda referencias **débiles**; un método enlazado vive
            # mientras viva su objeto, y este es el singleton de la clase.
            bus.subscribe(Events.ENEMY_DIED, self._on_enemy_died)

    def _on_enemy_died(self, **data: Any) -> None:
        entity_id = str(data.get("entity_id", ""))
        self._score += _points_for(entity_id)
        self.save()

    @property
    def score(self) -> int:
        return self._score

    def reset(self) -> None:
        """Pone la puntuación a cero (nueva partida)."""
        self._score = 0
        self.save()

    def set_score(self, puntos: int) -> None:
        """Deja la puntuación que traía una partida guardada — AUD-292.

        Sin esto, cargar un slot dejaba la puntuación del anterior: el marcador
        vivía en un fichero global que no sabía de partidas.
        """
        self._score = max(0, int(puntos))
        self.save()

    def save(self) -> None:
        _migrar_score()
        _SCORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SCORE_PATH.write_bytes(orjson.dumps({"score": self._score}))

    def load(self) -> None:
        _migrar_score()
        try:
            raw = _SCORE_PATH.read_bytes()
            data = orjson.loads(raw)
            self._score = int(data.get("score", 0))
        except FileNotFoundError:
            self._score = 0
        except (ValueError, TypeError, OSError):
            logger.warning("score: %s ilegible; se empieza de cero", _SCORE_PATH)
            self._score = 0
