---
document_id: "LOI-LVL-4-1B"
title: "Nivel 4-1b — La Fosa Abisal"
aliases: ["Stage 4-1b", "La Fosa Abisal", "variante acuática de 4-1"]
tags: ["level", "zona-final", "atmospheric", "variante"]
description: "Ficha de nivel: la variante acuática del sorteo de 4-1 (AUD-518/519)"
source: "docs/niveles/13b_STAGE_4_1B.md"
---

# NIVEL 4-1b — LA FOSA ABISAL

**Entregable:** profesorado (no se asigna a estudiantes) · **Zona:** Final —
El Cementerio Sagrado · **Tipo:** Travesía sumergida (un solo perseguidor)

## 0. Qué es, y qué no es

4-1b **no es un nivel aparte** con su propio hueco en `STAGE_ORDER`: es una
de las tres caras que puede tomar el slot `stage4_1` en una partida dada,
sorteada una sola vez por partida (AUD-518,
[[../03_ARCHITECTURE.md|arquitectura del motor]] §`stage_registry.py`,
`src/stages/stage4_1/selector.py`). Si a esta partida le tocó otra
variante, 4-1b no se juega nunca — no hay forma de elegirlo a mano fuera de
pruebas o `--stage stage4_1b`.

Construido en AUD-519, después de que el dueño pidiera —vía
`AskUserQuestion`, 2026-08-17— tres variantes del mismo slot: cementerio
(el 4-1 original, [[13_STAGE_4_1.md]]), acuática (ésta) y aérea
([[13c_STAGE_4_1C.md]]).

## 1. Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★☆☆☆ (2/5) — atmosférica, como el cementerio |
| Forma | Horizontal, un único TMX, seis secciones de 150 baldosas — **misma geometría que 4-1** (900×38 baldosas) |
| Ambientación | Sumergido de principio a fin (`WaterZone` cubre casi toda la columna de aire; `docs/45_SWIMMING_SPEC.md`), lecho marino como referencia de suelo. **AUD-531** — cueva, no fosa azul: paleta café/roca húmeda (antes abisal azul, AUD-519), faroles cálidos cerca del techo como límite visual inalcanzable, fondo pintado (`Stage4_1B.dibujar_fondo`) para que esa luz tenga algo que iluminar — el negro queda reservado a la ausencia de luz de verdad |
| Enemigos | **1** — el pez abismal (`EnemyPezAbismal`), no una regla de oro rota: 4-1 (cementerio) sigue en cero; ésta es la variante que lo introduce |
| Checkpoints | 6, uno por sección — el haz de luz de siempre (AUD-523, universal en los 26 escenarios) |
| Día/noche | Congelado, abisal (`day_length=0`, `ambient_light=0.28`) — no hay ciclo día/noche 900 baldosas bajo el agua |
| Límite de tiempo | Sin límite |

## 2. El pez abismal

`src/framework/entities/enemy_pez_abismal.py`. Pedido explícito del dueño:
*"que no lo mate ni lo toque"*. Se cumple en los dos sentidos:

- **No puede tocar al jugador:** `damage_on_contact=0.0`.
- **El jugador no puede tocarlo:** `apply_hit()` es un no-op deliberado
  (documentado en el propio módulo por qué rompe la convención "no
  sobreescribir" de `EnemyBase`).

Hereda de `EnemyFlying` entero — "nadar en agua abierta sin gravedad" es
exactamente lo que esa clase ya resuelve, y `ChaseFlight` (AUD-046) ya es
persecución real con inercia, no velocidad fija. `Stage4_1B` (la escena)
controla el ciclo completo: respiro inicial de 8 s, aparece justo fuera de
cámara en la dirección de avance, persigue 5-9 s, se retira sin dejar
fugas en `entity_list` — nunca queda un pez huérfano si el jugador muere a
mitad de la persecución.

**AUD-529 — se oye antes de verse.** Pedido tras jugarlo: *"debe ser mucho
más grande y amenazador... el jugador debe sentirlo y escucharlo antes de
poder verlo"*. El sprite pasó de 14×10 (lo que `EnemyFlying` fija para
todos sus subtipos) a 28×20 propio — `EnemyPezAbismal._load_extra_sprites`
lo sobreescribe junto con `_sprite_fw/_sprite_fh` y el `rect` de colisión
(56×32). `Stage4_1B._invocar_pez` emite
`Events.SFX_ENEMIES_PEZ_ABISMAL_ACERCARSE` —un gemido grave que se desliza,
registro abisal— en el mismo instante en que el pez nace fuera de cámara:
el aviso llega uno o dos segundos antes de que la silueta entre nadando en
cuadro.

**AUD-543 — corrientes de agua y fauna nueva, pedidas tras jugarlo.**
`ZonaDeAgua.corriente` (`src/framework/ecs/components.py`) ya existía en el
motor —lo aplica `sistema_corriente_de_agua`— y ningún escenario de
referencia lo declaraba nunca. `trazado.ZONAS_DE_CORRIENTE` define tres
franjas superpuestas a la `WaterZone` grande: sección 2 y la cola de la
sección 6 empujan a favor, la sección 4 empuja en contra. La magnitud está
verificada por simulación, no a ojo (`tests/test_stage4_1b.py::
TestLasCorrientesDeAgua`): nadando a fondo contra la corriente en contra la
velocidad converge a 90 px/s (25% más lenta que los 120 px/s sin
corriente) — se nota, no bloquea. Las corrientes a favor apenas cambian
nada mientras se nada a fondo (el tope de 120 px/s ya está saturado sin
ellas) — donde sí se notan es a la deriva, sin tecla pulsada.

Fauna nueva (calamares, peces de colores) y "coral que cae" — pedidos en
el mismo reporte — se resolvieron como un solo tipo de partícula de
ambiente, `"vida_abisal"` (`AmbientParticleSystem`, ver la nota junto a
`TIPOS`): un mapa sólo declara un `ambient_fx` a la vez, así que en vez de
tres tipos que compitieran por ese único slot, éste mezcla tres
comportamientos —peces rápidos y de colores, calamares grandes y lentos
casi silueta, y coral desprendido que cae en vez de flotar— con
proporciones fijas por `_spawn`.

**Lo que se investigó y no se construyó: tiles destructibles.** El motor
ya tiene un sistema genérico reutilizable (`BreakableBlock`/
`BloqueDestructible`, `src/framework/stage/bloques.py`), pero se rompe con
la caja de ataque del jugador, y `SwimmingState`
(`src/framework/entities/states/swim.py`) no tiene ninguna transición a un
estado de ataque — el jugador no puede atacar mientras nada. Reusar el
sistema tal cual dejaría un obstáculo irrompible; forzarlo con contacto
del cuerpo no funciona porque un `BreakableBlock` sin romper es sólido
(participa en `rects_solidos()`), así que la resolución de colisión aparta
al jugador antes de que su rect llegue a solaparse con el bloque. Añadir
combate bajo el agua es un cambio de diseño aparte, no un efecto colateral
de esta pasada — se deja documentado, no construido a medias.

## 3. Reglas obligatorias

Las mismas del cementerio (`13_STAGE_4_1.md` §3), salvo la de cero
enemigos — ésta es, a propósito, la variante que la rompe con exactamente
uno.

1. **Ninguna trampa mortal.** Cero `DeathPit`, cero `HazardZone` fija.
2. **El pez no daña ni se puede dañar** (§2 arriba) — no es un enemigo de
   combate, es una presencia.
3. **`validate_tmx.py --ci` en verde** para las tres variantes a la vez.

## 4. Estado real — construido (AUD-519)

- [x] Misma geometría que 4-1 (900×38, seis secciones)
- [x] `WaterZone` sumergiendo la columna de aire de principio a fin
- [x] Seis checkpoints (el haz de luz universal, AUD-523)
- [x] El pez abismal: aparece, persigue, se retira, sin fugas
- [x] Tileset propio (paleta abisal) y sprite propio (señuelo
      bioluminiscente que pulsa)
- [x] Registrado en el sorteo (`selector.VARIANTES_DISPONIBLES["acuatico"]`)
- [x] Corrientes de agua, tres franjas, magnitud verificada por simulación
      (AUD-543)
- [x] Fauna nueva y coral que cae — partícula de ambiente `"vida_abisal"`
      (AUD-543)
- [x] `tests/test_stage4_1b.py`, `tests/test_enemy_pez_abismal.py`

**Sigue pendiente** (no bloquea el sorteo, es pulido futuro):

- Variedad narrativa por sección — el cementerio tiene seis identidades de
  fase propias (`fases.py`); 4-1b hoy es una sola ambientación sostenida
  de principio a fin.
- Tiles destructibles — investigado en AUD-543, no construido: exige
  decidir primero si el jugador puede atacar bajo el agua (ver la nota
  arriba). [[../../KNOWN_GAPS.md|GAP-069]].
