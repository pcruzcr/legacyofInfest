"""
Module: culling
System: framework.stage
Academic Unit: N/A
Description: AUD-279 — qué se simula y qué se dibuja cada fotograma: sólo lo
que está cerca de la cámara.

El hueco
--------
Hasta AUD-279 el motor actualizaba **todos** los enemigos del escenario cada
fotograma y encolaba **todos** para dibujar, mirase donde mirase la cámara.
`docs/87` §15.4 lo dio por «lo más rentable que queda» sin medirlo. Medido, la
verdad es más matizada y conviene dejarla escrita antes que el código:

**En los mapas que hay, esto no gana nada.** Stage 0 —9 enemigos en 1.600 px—
da 5,007 ms/fotograma con culling y 4,931 sin él. Con el margen de producción el
mapa entero cabe en la zona activa, así que se paga la comprobación y no se
congela a nadie: 0,08 ms sobre un presupuesto de 16,67, indistinguible del ruido.

**Lo que esto compra es que el coste deje de crecer con el tamaño del mapa.**
El escenario que importa en un motor del que copian veintiséis entregas no es
el que hay hoy, sino el que un estudiante construye el viernes por la noche.
Doscientos enemigos repartidos por diez mil píxeles: **10,292 → 6,753 ms,
1,52×**. Ahí la diferencia deja de ser decimal.

Medianas de cinco pares alternados dentro de la misma ejecución, `update` +
`draw`, 200 fotogramas cada uno. Se comparan entre sí y no contra los números
de otro día: el absoluto se mueve con la carga de la máquina, la razón no.

Por qué el margen es de 400 px y no de cero
-------------------------------------------
Congelar justo en el borde de la pantalla se ve. El margen tiene que ser mayor
que la distancia a la que un enemigo congelado todavía podría afectar a lo que
se ve, y esa distancia la fija su proyectil: `Projectile` vuela a 120 px/s con
tres segundos de vida, o sea **360 px como máximo**. Con 400 px de margen, un
enemigo congelado no puede tener nada suyo dentro del encuadre — ni ahora ni
dentro de tres segundos.

Las tres exenciones, y por qué existen
--------------------------------------
1. **Los jefes.** Un jefe tiene fases, temporizadores e invocaciones que corren
   aunque la cámara mire a otro lado; `boss_venado` mide 3.280 px de ancho y su
   arena entera no cabe en pantalla. `BossBase.siempre_activo = True`.
2. **Quien tiene algo volando.** Si un enemigo ya disparó, congelarlo dejaría su
   proyectil clavado en el aire. Se comprueba solo, sin que nadie lo declare.
3. **Quien lo pida.** `siempre_activo = True` en cualquier subclase. Es la
   salida para una entrega de estudiante que dependa de simular lejos, y existe
   porque la invariante 2 dice que las veintiséis clases de escenario tienen que
   seguir funcionando sin tocar una línea.

Y `settings.CULLING_MARGEN = 0` lo apaga entero, que es lo que hay que poder
hacer cuando alguien sospeche que el culling le está escondiendo un fallo.
"""
from __future__ import annotations

from typing import Any

import pygame

from src.engine.core import settings


def zona_activa(offset: pygame.Vector2, margen: int | None = None) -> pygame.Rect | None:
    """El encuadre de la cámara, crecido por el margen.

    Devuelve `None` cuando el culling está apagado (`margen <= 0`), y ese
    `None` es lo que el resto del módulo interpreta como «todo está activo».
    Se distingue a propósito de un rectángulo vacío: un rectángulo de área cero
    haría lo contrario —apagarlo todo— y ese es el error que convierte una
    optimización en una pantalla en negro.
    """
    if margen is None:
        margen = int(getattr(settings, "CULLING_MARGEN", 0))
    if margen <= 0:
        return None
    return pygame.Rect(
        int(offset.x) - margen,
        int(offset.y) - margen,
        settings.INTERNAL_WIDTH + margen * 2,
        settings.INTERNAL_HEIGHT + margen * 2,
    )


def zona_de_dibujado(offset: pygame.Vector2, margen: int) -> pygame.Rect | None:
    """Como `zona_activa`, pero con su propio margen y bajo el mismo interruptor.

    Existe para que `CULLING_MARGEN = 0` apague **las dos** mitades. Si el
    dibujado usara su margen sin mirar el interruptor, apagar el culling dejaría
    la mitad encendida y el fallo que alguien intentaba aislar seguiría ahí —
    que es la peor forma posible de tener un interruptor.
    """
    if int(getattr(settings, "CULLING_MARGEN", 0)) <= 0:
        return None
    return zona_activa(offset, margen)


def dentro(rect: pygame.Rect | None, zona: pygame.Rect | None) -> bool:
    """¿Toca este rectángulo la zona activa?

    Sin zona (culling apagado) o sin rectángulo, la respuesta es que sí: ante la
    duda se simula. Equivocarse por exceso cuesta unas décimas de milisegundo;
    equivocarse por defecto congela a un enemigo que el jugador está mirando.
    """
    if zona is None or rect is None:
        return True
    return zona.colliderect(rect)


def se_simula(entidad: Any, zona: pygame.Rect | None) -> bool:
    """¿Le toca `update()` a esta entidad en este fotograma?

    Las exenciones se comprueban **antes** que la posición porque son más
    baratas que un `colliderect` y porque leen mejor: primero quién está exento,
    después quién está cerca.
    """
    if zona is None:
        return True
    if getattr(entidad, "siempre_activo", False):
        return True
    if getattr(entidad, "_active_projectiles", None):
        return True
    return dentro(getattr(entidad, "rect", None), zona)
