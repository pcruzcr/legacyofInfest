"""
El núcleo ECS: entidades, componentes y el mundo que los guarda.

F5.1 — por qué se añade esto y por qué NO se reescribe el motor
===============================================================
La jerarquía actual —`BaseEntity` → `EnemyBase` → `EnemyWalker`— funciona y
está probada, pero tiene el problema clásico de la herencia en videojuegos: **una
capacidad nueva no tiene dónde vivir**. Un enemigo que además flota, además
recibe viento y además se agarra a una plataforma móvil obliga a elegir entre
duplicar código en cinco clases o inflar la clase base hasta que todo el mundo
carga con todo.

El motor ya tiene la cicatriz. `BaseEntity` arrastra `layer`, `is_visible` y un
bus de eventos que la mayoría de entidades no usa, y `EnemyBase` acumula estados
de vuelo, de disparo y de embestida que sólo interesan a un tercio de sus hijos.

ECS resuelve eso: una capacidad es **un componente**, y quien la tenga la
recibe. `Viento` no pregunta si eres un enemigo o una caja; pregunta si tienes
`Transform` y `Velocidad`.

Lo que NO se hace, y es deliberado
-----------------------------------
**No se migra el código de los estudiantes.** Hay 26 clases suyas heredando de
`StageScene`, `BossBase`, `EnemyBase` y `BaseEntity`, sobre 18.054 líneas que
acaban de entregar, presentar y ser calificadas. Reescribirlas para que encajen
en una arquitectura nueva convertiría su trabajo en otro trabajo, y ninguna
mejora arquitectónica vale eso.

Así que el ECS va **por debajo**: `BaseEntity.position` y `BaseEntity.rect`
pasan a leer y escribir componentes, y su código sigue funcionando sin tocar una
línea. Es el patrón de la higuera estranguladora: la estructura nueva crece
alrededor de la vieja y la sostiene, en vez de talarla.

Por qué este ECS y no uno «de verdad»
--------------------------------------
Los ECS de producción guardan los componentes en arreglos contiguos por
arquetipo, porque a cien mil entidades la localidad de caché domina el
rendimiento. Aquí hay **cientos** de entidades, no cien mil, y este motor es
material de clase antes que un producto.

Así que el almacén es un diccionario de diccionarios: `tipo → {entidad:
componente}`. Se lee de un vistazo, se depura con un `print`, y a esta escala
la diferencia no se mide. Lo que **sí** necesita arreglos contiguos —los miles
de proyectiles de un *bullet hell*— vive en `bullet_swarm.py` con NumPy, y ahí
la razón se explica con números.

Tener las dos cosas, y saber por qué cada una está donde está, es mejor lección
que fingir que una sola sirve para todo.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import TypeVar

#: Una entidad es un número. No una clase, no un objeto: un identificador.
#:
#: Cuesta aceptarlo viniendo de la herencia, y es la idea central: la entidad no
#: *tiene* comportamiento ni datos. Es la clave con la que los componentes se
#: encuentran entre sí.
EntityId = int

C = TypeVar("C")


class World:
    """El almacén de componentes y el registro de entidades vivas.

    Invariantes que se mantienen a mano y conviene conocer:

    * Un identificador **nunca se reutiliza**. Reciclarlos ahorra memoria y
      produce el peor error de esta arquitectura: un sistema guarda el id 7,
      el 7 muere, nace otro 7 distinto y el sistema opera sobre el nuevo
      creyendo que es el viejo. A cientos de entidades por partida no hay
      ningún motivo para arriesgarse.
    * `borrar` es diferido. Un sistema que borra mientras otro recorre dejaría
      el recorrido a medias; las bajas se aplican en `aplicar_bajas()`, entre
      sistemas y no dentro de uno.
    """

    __slots__ = ("_almacen", "_pendientes_de_baja", "_recursos", "_siguiente",
                 "_vivas")

    def __init__(self) -> None:
        #: tipo de componente -> {entidad: componente}
        self._almacen: dict[type, dict[EntityId, object]] = {}
        self._siguiente: EntityId = 1
        self._vivas: set[EntityId] = set()
        self._pendientes_de_baja: set[EntityId] = set()
        #: AUD-137 — cosas que son del mundo entero y no de una entidad: el
        #: reloj musical, por ejemplo.
        #:
        #: Un sistema recibe `(mundo, dt)` y nada más, a propósito: es lo que
        #: hace que se puedan probar sueltos. Pero hay datos que no son de
        #: ninguna entidad en particular y que un sistema necesita, y sin un
        #: sitio para ellos aparecen como variables globales — que es peor.
        self._recursos: dict[str, object] = {}

    # -- recursos del mundo ----------------------------------------
    def poner_recurso(self, clave: str, valor: object) -> None:
        self._recursos[clave] = valor

    def recurso(self, clave: str, por_defecto: object = None) -> object:
        return self._recursos.get(clave, por_defecto)

    # -- ciclo de vida ---------------------------------------------
    def crear(self, *componentes: object) -> EntityId:
        """Nueva entidad, opcionalmente con sus componentes de partida."""
        entidad = self._siguiente
        self._siguiente += 1
        self._vivas.add(entidad)
        for componente in componentes:
            self.poner(entidad, componente)
        return entidad

    def adoptar(self, entidad: EntityId) -> None:
        """Marca como viva una entidad creada en otro mundo.

        Lo usa el puente con `BaseEntity`: una entidad puede nacer suelta —en
        una prueba, o en el `__init__` de un enemigo antes de que exista la
        escena— y mudarse después al mundo del escenario.
        """
        self._vivas.add(entidad)
        self._siguiente = max(self._siguiente, entidad + 1)

    def existe(self, entidad: EntityId) -> bool:
        return entidad in self._vivas

    def marcar_baja(self, entidad: EntityId) -> None:
        """Pide la baja. No se ejecuta hasta `aplicar_bajas()`."""
        self._pendientes_de_baja.add(entidad)

    def aplicar_bajas(self) -> int:
        """Retira de verdad lo marcado. Devuelve cuántas entidades cayeron."""
        if not self._pendientes_de_baja:
            return 0
        cuantas = 0
        for entidad in self._pendientes_de_baja:
            if entidad not in self._vivas:
                continue
            self._vivas.discard(entidad)
            for tabla in self._almacen.values():
                tabla.pop(entidad, None)
            cuantas += 1
        self._pendientes_de_baja.clear()
        return cuantas

    # -- componentes -----------------------------------------------
    def poner(self, entidad: EntityId, componente: object) -> None:
        """Añade o reemplaza un componente. Se indexa por su clase exacta.

        Por clase exacta y no por jerarquía: si `Viento(Zona)` se indexara
        también como `Zona`, consultar `Zona` devolvería vientos y un sistema
        de fricción los trataría como suyos. Los componentes son datos, y los
        datos no se heredan aquí.
        """
        self._vivas.add(entidad)
        self._almacen.setdefault(type(componente), {})[entidad] = componente

    def quitar(self, entidad: EntityId, tipo: type) -> None:
        tabla = self._almacen.get(tipo)
        if tabla is not None:
            tabla.pop(entidad, None)

    def obtener(self, entidad: EntityId, tipo: type[C]) -> C | None:
        tabla = self._almacen.get(tipo)
        return tabla.get(entidad) if tabla else None  # type: ignore[return-value]

    def tiene(self, entidad: EntityId, tipo: type) -> bool:
        tabla = self._almacen.get(tipo)
        return bool(tabla) and entidad in tabla

    # -- consultas -------------------------------------------------
    def cada(self, tipo: type[C]) -> Iterator[tuple[EntityId, C]]:
        """Todas las entidades con ese componente.

        Se copia la lista de pares antes de ceder el control. Un sistema que
        añada o quite componentes mientras recorre reventaría con
        «dictionary changed size during iteration», y eso pasa en cuanto
        alguien escribe un sistema que crea entidades —que es la mitad de
        ellos—.
        """
        tabla = self._almacen.get(tipo)
        if not tabla:
            return iter(())
        return iter(list(tabla.items()))  # type: ignore[arg-type]

    def con(self, *tipos: type) -> Iterator[EntityId]:
        """Entidades que tienen **todos** esos componentes.

        Se empieza por el componente más raro y se filtra con el resto. Con dos
        tablas de 500 y 3 elementos, recorrer la pequeña hace 3 comprobaciones
        y recorrer la grande hace 500 para el mismo resultado. Es la única
        optimización de este fichero y se paga sola.
        """
        if not tipos:
            return iter(())
        tablas = [self._almacen.get(t) or {} for t in tipos]
        if any(not t for t in tablas):
            return iter(())
        tablas.sort(key=len)
        base, resto = tablas[0], tablas[1:]
        return iter([e for e in list(base) if all(e in t for t in resto)])

    # -- diagnóstico -----------------------------------------------
    @property
    def total_entidades(self) -> int:
        return len(self._vivas)

    def censo(self) -> dict[str, int]:
        """Cuántas entidades tiene cada componente. Para el panel de depuración."""
        return {t.__name__: len(tabla) for t, tabla in self._almacen.items() if tabla}

    def censo_tipos(self) -> list[type]:
        """Los tipos de componente que este mundo conoce.

        Lo usa `adoptar_en` del puente para mudar una entidad entera sin tener
        que saber de antemano qué componentes lleva puestos.
        """
        return [t for t, tabla in self._almacen.items() if tabla]
