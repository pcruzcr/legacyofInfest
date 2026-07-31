"""
El planificador: qué sistema corre, en qué orden y por qué ése.

F5.1 — el orden no es un detalle
================================
En una arquitectura de herencia el orden está escondido dentro de `update()`:
primero la física, luego la colisión, luego la animación, porque así se
escribió. Es implícito y por eso nadie lo discute.

En ECS el orden **es** el diseño, y ponerlo mal produce fallos que no parecen de
orden. Tres reales de este motor:

* Si el arrastre de las plataformas corre **después** de la colisión, el
  jugador se hunde medio cuerpo en la plataforma que lo lleva y sale despedido
  al fotograma siguiente.
* Si las zonas de viento corren **después** de integrar la velocidad, el
  empujón se aplica al fotograma siguiente y el viento se siente «con retraso»
  sin que nadie sepa decir por qué.
* Si las bajas se aplican **dentro** del recorrido de un sistema, otro sistema
  del mismo fotograma opera sobre entidades muertas.

Por eso el orden vive aquí, en una lista con nombre y comentario, y no repartido
por veinte ficheros. Se lee en diez segundos y se discute en una reunión.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from src.framework.ecs.world import World

logger = logging.getLogger(__name__)

#: Un sistema es una función. No una clase con `update`: una función que recibe
#: el mundo y el tiempo. Si necesita estado, se guarda en un componente, que es
#: exactamente para lo que están.
Sistema = Callable[[World, float], None]


class Fase:
    """Las etapas de un fotograma, en el orden en que ocurren.

    Los números dejan hueco a propósito. Insertar un sistema entre dos etapas
    sin renumerar todo es la diferencia entre añadir una mecánica en una tarde
    y tener que revisar el orden entero.
    """

    ENTRADA = 100        # leer mandos y teclado
    IA = 200             # decidir: conos de visión, alerta, elección de ataque
    FUERZAS = 300        # viento, gravedad, corrientes: modifican la velocidad
    MOVIMIENTO = 400     # integrar velocidad -> posición
    ESCENARIO = 450      # plataformas móviles y bloques rítmicos SE MUEVEN aquí
    ARRASTRE = 460       # ...y aquí arrastran a su pasajero, antes de colisionar
    COLISION = 500       # resolver contra sólidos
    ZONAS = 600          # daño, agua, fricción: reaccionan a la posición final
    COMBATE = 700        # golpes, proyectiles, puntos débiles
    ANIMACION = 800      # elegir fotograma según el estado ya resuelto
    CAMARA = 850         # la cámara sigue a lo que ya se movió
    BAJAS = 900          # y sólo entonces se retira lo muerto


@dataclass(slots=True)
class _Entrada:
    fase: int
    nombre: str
    fn: Sistema
    activo: bool = True
    #: Milisegundos del último fotograma. Lo lee el panel de rendimiento.
    ms: float = 0.0


@dataclass(slots=True)
class Planificador:
    """Guarda los sistemas ordenados y los ejecuta.

    Mide cada uno por separado. Es barato —un `perf_counter` por sistema— y
    responde a la única pregunta que importa cuando el juego va lento: *cuál*
    va lento. Sin esto se acaba optimizando a ojo, que es como se llegó a tener
    una escena de demos a 10,24 ms por fotograma sin que nadie lo notara.
    """

    _sistemas: list[_Entrada] = field(default_factory=list)
    _ordenado: bool = True

    def registrar(self, fase: int, nombre: str, fn: Sistema) -> None:
        if any(e.nombre == nombre for e in self._sistemas):
            raise ValueError(
                f"ya hay un sistema llamado '{nombre}'. Los nombres se usan para "
                f"activarlos, desactivarlos y leer sus tiempos: repetirlos haría "
                f"que apagar uno apagara el otro.",
            )
        self._sistemas.append(_Entrada(fase=fase, nombre=nombre, fn=fn))
        self._ordenado = False

    def activar(self, nombre: str, valor: bool = True) -> None:
        """Enciende o apaga un sistema. Para depurar y para las pruebas.

        Apagar uno y ver qué se rompe es la forma más rápida de comprobar que
        una prueba mide lo que dice medir.
        """
        for e in self._sistemas:
            if e.nombre == nombre:
                e.activo = valor
                return
        raise KeyError(f"no hay ningún sistema llamado '{nombre}'")

    def ejecutar(self, mundo: World, dt: float) -> None:
        if not self._ordenado:
            # Estable: dos sistemas en la misma fase conservan el orden de
            # registro. Sin estabilidad, el orden dependería del de inserción
            # en la tabla y cambiaría entre versiones de Python.
            self._sistemas.sort(key=lambda e: e.fase)
            self._ordenado = True

        for e in self._sistemas:
            if not e.activo:
                continue
            t0 = time.perf_counter()
            try:
                e.fn(mundo, dt)
            except Exception:
                # Un sistema de un escenario de estudiante puede lanzar. Que
                # tumbe la partida entera sería desproporcionado; que falle en
                # silencio sería peor. Se registra con traza y se sigue.
                logger.exception("sistema '%s' lanzó; se continúa", e.nombre)
            e.ms = (time.perf_counter() - t0) * 1000.0

        mundo.aplicar_bajas()

    # -- diagnóstico -----------------------------------------------
    def tiempos(self) -> list[tuple[str, float]]:
        """Sistemas ordenados por lo que costaron, de peor a mejor."""
        return sorted(
            ((e.nombre, e.ms) for e in self._sistemas if e.activo),
            key=lambda p: p[1],
            reverse=True,
        )

    @property
    def nombres(self) -> list[str]:
        return [e.nombre for e in self._sistemas]

    def total_ms(self) -> float:
        return sum(e.ms for e in self._sistemas if e.activo)
