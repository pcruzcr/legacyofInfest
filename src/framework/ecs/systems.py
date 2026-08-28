"""
Los sistemas: todo el comportamiento de las mecánicas nuevas — re-export por Fase.

F5.3 a F5.9 — qué hay aquí y por qué está junto
================================================
Cada función de este fichero es un sistema: recibe el mundo y el `dt`, recorre
las entidades que tienen los componentes que le interesan, y les cambia los
datos. Ninguna sabe de `EnemyBase`, de `Player` ni de `StageScene`, y ésa es
exactamente la propiedad que hacía falta: **el viento empuja a lo que tenga
`Transform` y `Velocidad`**, sea el jugador, un enemigo, una caja o un
proyectil.

Estaban en un solo fichero, y no en uno por mecánica, por una razón concreta: el
orden entre ellos importa más que la separación. Un `Ctrl+F` sobre este fichero
enseña la secuencia completa de un fotograma; repartidos en nueve módulos habría
que abrirlos todos para saber quién corre antes que quién. El día que esto pasó
de 770 líneas se partió **por fases, no por mecánicas** (FUERZAS, ESCENARIO,
ZONAS): cada módulo agrupa lo que corre en la misma ventana del planificador y
el orden global sigue viviendo en `scheduler.py` y en `mundo_ecs.py`.

Este módulo queda como **re-export** para que `from src.framework.ecs import
systems` y `from src.framework.ecs.systems import X` sigan funcionando sin
tocar una línea fuera del ECS.

Las mecánicas que implementa, con su fuente:

* **Viento** — Mega Man 2 (Air Man), Celeste (Golden Ridge), Hollow Knight
  (Kingdom's Edge).
* **Fricción y arrastre** — Mega Man 2 (cintas), Hollow Knight (la miel).
* **Zonas letales temporizadas** — MGS (láseres), Mega Man 2 (Quick Man),
  Celeste (Templo de los Espejos), Inside (ondas de choque).
* **Agua** — Sonic (Labyrinth), SMB3 (Water Land), Inside (bosque sumergido).
* **Plataformas móviles y cintas** — Mega Man 2, Sonic, Donkey Kong Country.
* **Bloques rítmicos** — Mega Man 2 (Wily 1), Celeste (cassette).
* **Plataformas hundibles** — Cuphead (Perilous Piers).
* **Conos de visión y alerta** — MGS (Tank Hangar), Inside (la granja).
* **Acosador invulnerable** — RE3 (Nemesis), Celeste (el conserje), Metroid
  Dread (E.M.M.I.).
"""
from __future__ import annotations

# Re-export por Fase — el orden no importa aquí, el planificador manda.
from src.framework.ecs.systems_escenario import (
    MARGEN_PASAJERO,
    marcar_pisada,
    sistema_arrastre_de_plataformas,
    sistema_bloques_ritmicos,
    sistema_lianas_moviles,
    sistema_lianas_salto,
    sistema_plataformas_hundibles,
    sistema_plataformas_moviles,
)
from src.framework.ecs.systems_fuerzas import (
    sistema_corriente_de_agua,
    sistema_friccion,
    sistema_resortes,
    sistema_viento,
)
from src.framework.ecs.systems_zonas import (
    en_agua,
    liana_alcanzable,
    liana_salto_alcanzable,
    rect_del_jugador,
    rects_atravesables_desde_abajo,
    rects_solidos,
    sistema_acosador,
    sistema_alerta,
    sistema_conos_de_vision,
    sistema_efectos,
    sistema_zonas_letales,
    tirolesa_alcanzable,
)

__all__ = [
    "MARGEN_PASAJERO",
    "en_agua",
    "liana_alcanzable",
    "liana_salto_alcanzable",
    "marcar_pisada",
    "rect_del_jugador",
    "rects_atravesables_desde_abajo",
    "rects_solidos",
    "sistema_acosador",
    "sistema_alerta",
    "sistema_arrastre_de_plataformas",
    "sistema_bloques_ritmicos",
    "sistema_conos_de_vision",
    "sistema_corriente_de_agua",
    "sistema_efectos",
    "sistema_friccion",
    "sistema_lianas_moviles",
    "sistema_lianas_salto",
    "sistema_plataformas_hundibles",
    "sistema_plataformas_moviles",
    "sistema_resortes",
    "sistema_viento",
    "sistema_zonas_letales",
    "tirolesa_alcanzable",
]
