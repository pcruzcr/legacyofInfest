"""
El puente: `BaseEntity` por encima, componentes por debajo.

F5.2 — el requisito que manda sobre todos los demás
====================================================
Veintiséis clases de estudiantes heredan hoy de `BaseEntity`, `EnemyBase`,
`BossBase` y `StageScene`, y su código hace esto **115 veces**::

    self.rect.centerx = pr.centerx          # muta el rect en el sitio
    self.position.x += self.speed * dt      # muta el vector en el sitio
    if self.facing < 0: ...

Ninguna de esas líneas puede cambiar. Así que el puente tiene una regla dura:

    **La propiedad devuelve el objeto de verdad, no una copia.**

`self.rect` devuelve el `pygame.Rect` que vive dentro del componente
`Transform`. Mutarlo muta el componente. Si devolviera una copia, todo
compilaría, todas las pruebas de construcción pasarían, y el juego se rompería
en silencio: los enemigos se moverían para su propio código y se quedarían
quietos para los sistemas. Es exactamente la familia de fallo —correcto en
aislamiento, invisible en conjunto— que este proyecto lleva un mes cazando.

El mundo privado, y por qué no hay un mundo global
---------------------------------------------------
Una entidad puede nacer sin escena: en una prueba unitaria, en el `__init__` de
un jefe, en el arnés de humo. Si el puente dependiera de un mundo global
compartido, esas entidades se acumularían entre pruebas y una prueba
contaminaría a la siguiente.

Ya pasó en este proyecto con el modo de vídeo de pygame, que es global al
proceso: una prueba llamaba a `set_mode((64,64))` y tumbaba nueve pruebas de
centrado en otro fichero. La lección salió cara y no se repite.

Aquí cada entidad nace en un **mundo propio de una sola entidad**, y
`adoptar_en()` la muda al mundo de la escena cuando ésta la carga. Sin estado
global, sin fugas entre pruebas, y una entidad suelta sigue funcionando.
"""
from __future__ import annotations

import pygame

from src.framework.ecs.components import Salud, Transform, Velocidad
from src.framework.ecs.world import EntityId, World


class ComponentesDeEntidad:
    """Mezcla que da a una clase de la jerarquía un cuerpo ECS.

    Se pensó como decorador y como metaclase antes de quedar en una mezcla. Las
    dos alternativas escondían el mecanismo, y este fichero lo lee un estudiante
    de segundo año: que `BaseEntity(ComponentesDeEntidad, ABC)` diga a la cara
    de dónde salen `position` y `rect` vale más que la elegancia.
    """

    __slots__ = ()

    # -- alta ------------------------------------------------------
    def _iniciar_componentes(
        self,
        position: pygame.Vector2,
        rect: pygame.Rect | None = None,
        facing: int = 1,
    ) -> None:
        """Crea el mundo privado y el `Transform`. Lo llama `BaseEntity.__init__`."""
        mundo = World()
        # `rect` y `position` son atributos normales del dueño: se leen a la
        # misma velocidad que antes de la fase 5. El componente es una **vista**
        # que lee de aquí, así que no hay copia que pueda quedarse vieja ni
        # indirección en el camino caliente. El porqué, con los tres números
        # medidos, está en `components.Transform`.
        object.__setattr__(self, "position", pygame.Vector2(position))
        object.__setattr__(
            self, "rect", rect if rect is not None else pygame.Rect(0, 0, 0, 0),
        )
        tf = Transform(facing=facing, duenio=self)
        entidad = mundo.crear(tf)
        # Por `object.__setattr__` y no por asignación normal: las propiedades
        # de abajo leen `_mundo`, así que asignarlas antes de que exista daría
        # una recursión infinita en el primer acceso.
        object.__setattr__(self, "_mundo", mundo)
        object.__setattr__(self, "_entidad", entidad)
        # Referencia directa al componente, y no una búsqueda en el mundo cada
        # vez. `adoptar_en` traslada esta misma instancia al mundo de la escena,
        # así que la caché sigue siendo válida después de la mudanza.
        object.__setattr__(self, "_tf", tf)

    # -- acceso al ECS ---------------------------------------------
    @property
    def mundo(self) -> World:
        """El mundo donde viven los componentes de esta entidad."""
        return self._mundo  # type: ignore[attr-defined]

    @property
    def entidad(self) -> EntityId:
        """Su identificador dentro de ese mundo."""
        return self._entidad  # type: ignore[attr-defined]

    def adoptar_en(self, destino: World) -> None:
        """Muda todos sus componentes al mundo de la escena.

        Se trasladan **las mismas instancias**, no copias, por la misma razón
        que `rect` devuelve el original: si se copiaran, la entidad seguiría
        escribiendo en su `Transform` viejo y los sistemas leerían el nuevo.
        Serían dos verdades y el juego elegiría la equivocada.
        """
        origen: World = self._mundo  # type: ignore[attr-defined]
        if origen is destino:
            return
        antigua: EntityId = self._entidad  # type: ignore[attr-defined]
        nueva = destino.crear()
        for tipo in list(origen.censo_tipos()):
            componente = origen.obtener(antigua, tipo)
            if componente is not None:
                destino.poner(nueva, componente)
        object.__setattr__(self, "_mundo", destino)
        object.__setattr__(self, "_entidad", nueva)

    def componente(self, tipo: type) -> object | None:
        return self._mundo.obtener(self._entidad, tipo)  # type: ignore[attr-defined]

    def poner_componente(self, componente: object) -> None:
        self._mundo.poner(self._entidad, componente)  # type: ignore[attr-defined]

    # -- las propiedades que sostienen el código existente ----------
    # -- lecturas rápidas, escrituras vigiladas -------------------
    #
    # `rect` y `position` son **atributos normales**, no propiedades, y apuntan
    # a los mismos objetos que guarda el `Transform`. Mutarlos en el sitio
    # —`self.rect.centerx = 40`— cambia el componente porque es el mismo objeto.
    #
    # Por qué no propiedades, que era la primera versión: medido, `.rect` como
    # propiedad costaba 404 ns contra los 66 de un atributo, y el motor lee
    # `rect` y `position` **255 veces** en su bucle de fotograma. Sobre el
    # prólogo completo eso fue de 18,36 ms a 21,36 ms por fotograma: un 16 % del
    # presupuesto gastado en indirección.
    #
    # Lo único que las propiedades protegían era la **reasignación**
    # —`self.rect = otro`—, que en las 26 clases entregadas ocurre 14 veces
    # frente a cientos de lecturas. Así que se paga donde es barato: las
    # lecturas van directas y `__setattr__` vigila las dos escrituras que
    # importan.

    @property
    def _transform(self) -> Transform:
        return self._tf  # type: ignore[attr-defined]

    @property
    def facing(self) -> int:
        return self._tf.facing  # type: ignore[attr-defined]

    @facing.setter
    def facing(self, valor: int) -> None:
        self._tf.facing = -1 if valor < 0 else 1  # type: ignore[attr-defined]

    @property
    def velocity(self) -> pygame.Vector2:
        """Se crea al primer acceso.

        Perezoso a propósito: una entidad que nunca lee ni escribe su velocidad
        —una plataforma fija, un cartel— no debería aparecer en las consultas
        del sistema de movimiento. Con la herencia todo el mundo tenía
        velocidad; con componentes, tenerla es una decisión.
        """
        v = getattr(self, "_vel", None)
        if v is None:
            v = self._mundo.obtener(self._entidad, Velocidad)  # type: ignore[attr-defined]
            if v is None:
                v = Velocidad(pygame.Vector2(0, 0))
                self._mundo.poner(self._entidad, v)  # type: ignore[attr-defined]
            object.__setattr__(self, "_vel", v)
        return v.v

    @velocity.setter
    def velocity(self, valor: pygame.Vector2) -> None:
        self.velocity.update(valor)


def sincronizar_salud(
    entidad_ecs: EntityId, mundo: World, actual: float, maxima: float,
) -> None:
    """Refleja la vida de un `EnemyBase` en un componente `Salud`.

    Los enemigos llevan su vida en atributos propios desde antes del ECS, y
    varias entregas la leen y la escriben directamente. En vez de moverla —lo
    que rompería su código— se refleja aquí, para que los sistemas puedan
    consultarla sin conocer la jerarquía.

    Duplicar un dato es una deuda declarada, no un descuido: el día que ninguna
    entrega dependa de `current_health` esta función desaparece y `Salud` pasa a
    ser la única verdad.
    """
    s = mundo.obtener(entidad_ecs, Salud)
    if s is None:
        mundo.poner(entidad_ecs, Salud(actual=actual, maxima=maxima))
    else:
        s.actual = actual
        s.maxima = maxima
