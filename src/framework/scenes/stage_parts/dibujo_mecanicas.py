"""Cómo se dibujan las mecánicas del ECS.

Extraído de `stage_scene.py` en AUD-248 sin cambiar una línea de lógica, por la
razón que la propia prueba del presupuesto obliga a dar: *«toca extraer otro
grupo cohesivo a `stage_parts/`, no subir el número»*. `_dibujar_mecanicas_ecs`
había llegado ahí en AUD-242 y engordó el fichero 85 líneas cuando ya iba 338
por encima de su presupuesto.

Y es un grupo cohesivo de verdad: cinco componentes del mundo ECS que comparten
un único motivo para existir aquí, que es el que `_dibujar_bloques` lleva meses
enunciando dos métodos más arriba —«los bloques se dibujan, y no es opcional: si
el motor no los pinta, el jugador ve un muro invisible que a veces cede, que es
como se lee un fallo»— y que se aplicaba a la familia de `bloques.py` y no a la
del ECS.

Lo que estaba invisible, medido antes de arreglarlo (AUD-242)
--------------------------------------------------------------
De `BloqueRitmico`, `ZonaLetalTemporizada`, `Resorte` y `PlataformaMovil` no
había **ni un solo sitio** en el árbol que los dibujara; sólo la tirolesa se
pintaba. Y están puestos en los mapas: 7 bloques rítmicos —tres de ellos en
`stage0`, el nivel que copian los estudiantes— y 7 zonas letales con `dano=99`,
o sea que matan de un golpe desde un rectángulo que no se ve.

Formas planas y no sprites, como el resto de lo que el motor dibuja por su
cuenta: un rectángulo del color correcto siempre se ve, y el estudiante lo
sustituye por su arte cuando lo tenga.

AUD-509 — la misma auditoría, dos mecánicas más tarde
-------------------------------------------------------
`Liana` y `PlataformaHundible` se quedaron fuera del barrido de AUD-242: la
primera tiene sistema de agarre (`liana_alcanzable`) y estado propio
(`TrepandoState`) desde F5.14, y la segunda ganó colisión de verdad en
AUD-507/AUD-508 — las dos seguían siendo un rectángulo invisible por el que
el jugador subía o se hundía sin ver nada ahí.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from src.framework.ecs.world import World

#: Bloque rítmico presente y ausente. El ausente se dibuja **en contorno** en
#: vez de no dibujarse: es lo que convierte «desapareció el suelo» en «vuelve
#: dentro de un momento», que es la diferencia entre un obstáculo y una trampa.
COLOR_RITMICO = (150, 140, 190)
COLOR_RITMICO_AUSENTE = (110, 100, 150)
#: Zona letal encendida y apagada. Apagada se marca el carril y no el rayo: hay
#: que poder ver por dónde va a pasar **antes** de que pase.
COLOR_LASER = (255, 90, 70)
COLOR_LASER_APAGADO = (120, 60, 55)
COLOR_RESORTE = (230, 190, 70)
COLOR_MOVIL = (140, 130, 120)
#: AUD-509 — `Liana` y `PlataformaHundible` no estaban en la lista de «cinco
#: componentes» del docstring de arriba, ni en ningún otro sitio del árbol:
#: `liana_alcanzable`/`TrepandoState` mueven al jugador por una cuerda que
#: nunca se pintaba, y una hundible recién arreglada (AUD-507, AUD-508) para
#: que se hunda y bloquee de verdad seguía siendo un rectángulo invisible.
COLOR_LIANA = (90, 140, 60)
COLOR_LIANA_HOJA = (120, 170, 80)
COLOR_HUNDIBLE = (120, 100, 80)
COLOR_HUNDIBLE_PISADA = (170, 90, 70)


def dibujar_mecanicas_ecs(surface: pygame.Surface, mundo: World | None,
                          offset: pygame.Vector2) -> None:
    """Pinta los componentes del ECS que el jugador tiene que ver."""
    from src.framework.ecs import (
        BloqueRitmico,
        PlataformaHundible,
        PlataformaMovil,
        Resorte,
        Transform,
        ZonaLetalTemporizada,
    )
    from src.framework.ecs.components import Liana

    if mundo is None:
        return
    dx, dy = -int(offset.x), -int(offset.y)

    def _rect_de(entidad: Any) -> pygame.Rect | None:
        t = mundo.obtener(entidad, Transform)
        return None if t is None else t.rect.move(dx, dy)

    for entidad, bloque in mundo.cada(BloqueRitmico):
        r = _rect_de(entidad)
        if r is None:
            continue
        if bloque.presente:
            pygame.draw.rect(surface, COLOR_RITMICO, r)
            pygame.draw.rect(surface, (90, 84, 120), r, 1)
        else:
            pygame.draw.rect(surface, COLOR_RITMICO_AUSENTE, r, 1)

    for _entidad, zona in mundo.cada(ZonaLetalTemporizada):
        r = zona.rect.move(dx, dy)
        if zona.activa:
            pygame.draw.rect(surface, COLOR_LASER, r)
        else:
            pygame.draw.rect(surface, COLOR_LASER_APAGADO, r, 1)

    for _entidad, resorte in mundo.cada(Resorte):
        r = resorte.rect.move(dx, dy)
        pygame.draw.rect(surface, COLOR_RESORTE, r)
        for i in range(1, 4):          # las espiras, para que se lea muelle
            y = r.top + i * r.height // 4
            pygame.draw.line(surface, (150, 120, 40),
                             (r.left + 1, y), (r.right - 2, y), 1)

    for entidad, _movil in mundo.cada(PlataformaMovil):
        r = _rect_de(entidad)
        if r is None:
            continue
        pygame.draw.rect(surface, COLOR_MOVIL, r)
        pygame.draw.line(surface, (190, 180, 170), r.topleft, r.topright)

    for _entidad, liana in mundo.cada(Liana):
        r = liana.rect.move(dx, dy)
        cx = r.centerx
        pygame.draw.line(surface, COLOR_LIANA, (cx, r.top), (cx, r.bottom), 3)
        for y in range(r.top + 6, r.bottom, 14):    # las hojas, para que se lea planta
            pygame.draw.line(surface, COLOR_LIANA_HOJA, (cx - 5, y), (cx + 5, y), 2)

    for entidad, hund in mundo.cada(PlataformaHundible):
        if hund._ausente > 0.0:
            continue    # sumergida del todo: nada que pintar hasta que vuelva
        r = _rect_de(entidad)
        if r is None:
            continue
        color = COLOR_HUNDIBLE_PISADA if hund._pisada > 0.0 else COLOR_HUNDIBLE
        pygame.draw.rect(surface, color, r)
        pygame.draw.rect(surface, (60, 48, 36), r, 1)
