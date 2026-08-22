---
document_id: "LOI-LVL-4-1B"
title: "Nivel 4-1b — La Mina Inundada"
aliases: ["Stage 4-1b", "La Mina Inundada", "variante acuática de 4-1"]
tags: ["level", "zona-final", "atmospheric", "variante"]
description: "Ficha de nivel: la variante acuática del sorteo de 4-1 (AUD-518/519/575)"
source: "docs/niveles/13b_STAGE_4_1B.md"
---

# NIVEL 4-1b — LA MINA INUNDADA

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
([[13c_STAGE_4_1C.md]]). **AUD-575 (2026-08-19) lo rediseñó entero**: dejó de
ser una fosa abisal para ser una mina abandonada e inundada, con superficie
de agua real, estalactitas, luces de seguridad y un ecosistema que estorba
sin dañar.

## 1. Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★☆☆☆ (2/5) — atmosférica, como el cementerio |
| Forma | Horizontal, un único TMX, seis secciones de 150 baldosas — **misma geometría que 4-1** (900×38 baldosas) |
| Ambientación | **Mina inundada** (AUD-575): el agua llega a la **fila 11 de 38** — once filas de aire con estalactitas sobre veintiuna de agua, como el SMB 2-2 «encerrados bajo una gran cantidad de agua». Paleta café/óxido (roca, tablones, rieles), estalactitas en el techo y en el fondo pintado, luces de tres temperaturas — cálidas (refugio), blancas (focos de trabajo) y rojas de peligro (maleza, esclusa, pozo). Agua azul `#1a5c6e` con alpha 150 que se lee en toda la columna (AUD-574) |
| Enemigos | **1 + fauna** — el pez abismal (`EnemyPezAbismal`, regla: no daña ni se puede dañar) y la fauna fija de la mina (2 cangrejos y 4 medusas, presencia: estorban, nunca dañan). 4-1 (cementerio) sigue en cero; ésta es la variante que los introduce |
| Checkpoints | 7, por evento y no por distancia (AUD-576): uno tras cada dominio nuevo y cada set piece — islote, refugios, patio, esclusa, tras la sombra del pez, antes del clímax y en el tramo final — el haz de luz de siempre (AUD-523) |
| Día/noche | Congelado (`day_length=0`, `ambient_light=0.45` — **AUD-574**: 0.28 dejaba el lecho y al jugador en negro ilegible) — la mina no tiene cielo |
| Límite de tiempo | Sin límite — el reloj que castiga es el del **aire**: 30 s bajo el agua, se respira al emerger (AUD-575, GAP-071 resuelto: el HUD avisa) |
| Música | `music/4_1_b.mp3` (material de autor, AUD-575), declarada en el TMX como `bgm_track` |

## 2. El rediseño de la mina inundada (AUD-575, 2026-08-19)

Pedido del dueño, en una sola pieza: *«mina inundada... que el agua NO
llegue al techo... luces rojas y blancas... estalactitas... pez abismal que
persigue... bloques destructibles... flora y fauna como obstáculos...
ecosistema vivo... alternancia de agua y áreas secas»*. La geometría vive
en `trazado.py` (una constante por pieza, verificable en pruebas):

- **Superficie real.** `FILA_SUPERFICIE_AGUA = 11`: el agua ya no cubre la
  columna. Arriba, aire con estalactitas colgando (capa `BG_Near`, GIDs
  65/66, y siluetas en el fondo pintado); abajo, la `WaterZone` de la fila
  11 al lecho. Emerger es de verdad salir del agua: `ControlDeNado._salir`
  expulsa a la superficie y el aire se recupera a 8×/s fuera del agua.
- **El oxígeno vuelve a castigar (GAP-071 resuelto).** El AUD-572 apagó
  `dano_por_segundo` porque no había superficie a la que emerger. Con
  superficie real, `Stage4_1B.__init__` lo reactiva a 1.0: 30 s de aire, y
  al agotarse, daño. El aviso que `ControlDeNado.avisando` declaraba desde
  siempre y nadie mostraba ya tiene consumidor: una **barra de oxígeno**
  bajo la estamina en el HUD (se dibuja sólo bajo el agua) que parpadea y
  pulsa `SFX_TIMER_ALERT_PULSE` en el tramo bajo — el mismo lenguaje del
  cronómetro (AUD-553). Ver `docs/45_SWIMMING_SPEC.md` §4.
- **Fauna que estorba sin dañar.** `enemy_cangrejo.py` (hereda de
  `EnemyWalker`: patrulla andenes y lecho, no embiste) y `enemy_medusa.py`
  (hereda de `EnemyFlying`: deriva en senoide por la columna). Ambas con
  `damage_on_contact=0.0` **y** `contact_knockback=0.0` — el knockback de
  un daño 0 aún metía `HurtState`, y eso es agresión de facto. La escena
  los instancia en `on_enter` (después de `super().on_enter()`, que es
  quien carga el mapa y crea al jugador), no el TMX: son fauna del nivel,
  no arquetipos que el resto del motor deba conocer.
- **Bloques de mineral.** Nueve `BreakableBlock` de `golpes=1` repartidos
  por las seis secciones (lecho, andén seco del patio —se rompen con el
  ataque de tierra— y sobre las vigas del pozo de la sección 5, donde abren
  el hueco para emerger bajo el techo cortado). El ataque acuático
  (`SwimAttackState`, AUD-557/GAP-069) los rompe igual que los de la
  fosa.
- **Luces de tres temperaturas.** Veinte `Light` en `trazado.LUCES`:
  `warm` (faroles de refugio, radio 230, parpadeo lento), `blood` (alarma
  de peligro: maleza, esclusa, pozo; radio 180, parpadeo rápido) y
  `white` (focos de trabajo del patio y el desagüe, radio 200, estables).
  Los colores son los nombres de `ObjetosDeTiled.LIGHT_COLORS`.
- **Música propia.** `assets/music/4_1_b.mp3`, registrada en
  `scripts/validate_assets.py` y declarada como `bgm_track` en el TMX —
  `resolver_pista_de_musica` la encuentra por el sufijo `.mp3`.

## 3. El pez abismal

`src/framework/entities/enemy_pez_abismal.py`. Pedido explícito del dueño:
*"que no lo mate ni lo toque"*. Se cumple en los dos sentidos:

- **No puede tocar al jugador:** `damage_on_contact=0.0`.
- **El jugador no puede tocarlo:** `apply_hit()` es un no-op deliberado
  (documentado en el propio módulo por qué rompe la convención "no
  sobreescribir" de `EnemyBase`).

Hereda de `EnemyFlying` entero — "nadar en agua abierta sin gravedad" es
exactamente lo que esa clase ya resuelve, y `ChaseFlight` (AUD-046) ya es
persecución real con inercia, no velocidad fija. `Stage4_1B` (la escena)
controla el ciclo completo **por fases** (AUD-576, el pez como «monstruo
psicológico» del blueprint 10/10 §17-19): antes de `COL_PRIMER_EVENTO`
(col 553) no hay pez en absoluto — la mina se juega sin persecución;
el primer evento es una **sombra** que cruza el fondo con su gemido, sin
persecución; la persecución de verdad sólo llega en el abismo (col ≥
`COL_PERSECUCIONES`, 581), aparece justo fuera de cámara en la dirección
de avance, persigue 5-9 s y se retira sin dejar fugas en `entity_list` —
nunca queda un pez huérfano si el jugador muere a mitad de la persecución.
**AUD-575:** en el pozo del drenaje (sección 5) la espera entre apariciones
baja de 12-22 s a 6-10 s — la sección más cerrada es donde el pez deja de
sorprender y se vuelve presencia constante. **AUD-576:** en el clímax
(col ≥ `COL_CLIMAX`, 778) la persecución dura 10-14 s — la revelación, no
un susto.

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

## 3.1 Corrientes, fauna y bloques (AUD-543/557)

`ZonaDeAgua.corriente` (`src/framework/ecs/components.py`) ya existía en el
motor —lo aplica `sistema_corriente_de_agua`— y ningún escenario de
referencia lo declaraba nunca. `trazado.ZONAS_DE_CORRIENTE` define **ocho** franjas superpuestas a la
`WaterZone` grande (AUD-576 amplió las cinco de AUD-543): la maleza de la
sección 2 y la sección 4 empujan en contra, la cola de la sección 6 a
favor. La
magnitud está verificada por simulación, no a ojo (`tests/test_stage4_1b.
py::TestLasCorrientesDeAgua`): nadando a fondo contra la corriente en
contra la velocidad converge a 90 px/s (25% más lenta que los 120 px/s sin
corriente) — se nota, no bloquea.

Fauna nueva (calamares, peces de colores) y "coral que cae" — pedidos en
el mismo reporte — se resolvieron como un solo tipo de partícula de
ambiente, `"vida_abisal"` (`AmbientParticleSystem`, ver la nota junto a
`TIPOS`): un mapa sólo declara un `ambient_fx` a la vez, así que en vez de
tres tipos que compitieran por ese único slot, éste mezcla tres
comportamientos —peces rápidos y de colores, calamares grandes y lentos
casi silueta, y coral desprendido que cae en vez de flotar— con
proporciones fijas por `_spawn`.

**AUD-557 (GAP-069):** `SwimAttackState` (`states/swim.py`) le dio al
jugador un golpe real bajo el agua con su `_active_hitbox` propio (mismo
tamaño que el ataque corto de tierra), y el nivel declara `BreakableBlock`
de `golpes=1` — antes seis, ahora nueve (AUD-575) — ver
`tests/test_el_ataque_acuatico_rompe_bloques.py`.

## 4. Historia del nivel (lo que fue, para no volver a ser)

- **AUD-572 (2026-08-19):** reporte del dueño — *«esta mal hecho no nada
  sigue saltando... los enemigos hacen daño y la idea es que no hagan
  daño»*. El salto de tierra ganaba al nado (resuelto en AUD-573); el daño
  real era el límite de aire de fábrica de `ControlDeNado` en un nivel sin
  ningún punto donde `en_agua()` diera `None`: el ahogamiento era sólo
  cuestión de tiempo. En aquel momento se apagó `dano_por_segundo`.
- **AUD-573/574:** el nado de verdad (autoridad continua de `ControlDeNado`,
  sin salto de tierra ni WALKING sumergido, sin gravedad completa) y el
  agua legible (tinte `#1a5c6e`/alpha 150, `ambient_light=0.45`, faroles de
  radio 230, fondo pintado).
- **AUD-575 (2026-08-19):** el rediseño. La decisión de AUD-572 se revierte
  **con el cambio de diseño que la hacía correcta**: la superficie real da
  aire al que emerger, y el ahogamiento vuelve a ser el contrapeso del
  buceo — la tensión que una mina inundada necesita.

## 5. Reglas obligatorias

Las mismas del cementerio (`13_STAGE_4_1.md` §3), salvo la de cero
enemigos — ésta es, a propósito, la variante que la rompe.

1. **Ninguna trampa mortal.** Cero `DeathPit`, cero `HazardZone` fija.
2. **Nada daña.** El pez, los cangrejos y las medusas son presencia:
   obstruyen, estresan, pero nunca quitan vida ni empujan
   (`damage_on_contact=0.0`, `contact_knockback=0.0`). El único reloj que
   castiga es el del aire.
3. **`validate_tmx.py --ci` en verde** para las tres variantes a la vez.

## 6. Estado real — construido (AUD-519/543/557/573/574/575/576)

- [x] Misma geometría que 4-1 (900×38, seis secciones)
- [x] Mina inundada: superficie en la fila 11, estalactitas, vigas,
      óxido, alternancia agua/áreas secas (AUD-575)
- [x] Oxígeno activo (30 s, daño al agotarse) + barra de oxígeno en el
      HUD con pulso sonoro — GAP-071 resuelto (AUD-575)
- [x] Siete checkpoints por evento y no por distancia (AUD-576); el haz
      de luz de siempre (AUD-523)
- [x] El pez abismal por fases (AUD-576): sin pez antes del primer evento
      (col 553), sombra que cruza el fondo en los dos eventos, persecución
      de verdad sólo en el abismo (col ≥ 581), revelación en el clímax (col
      778); espera reducida en el pozo (AUD-575); sin fugas
- [x] Beats del blueprint 10/10 (AUD-576): la travesía se lee como
      mina → primera inmersión → corrientes → profundidad → abismo →
      clímax; tres fondos pintados elegidos por la columna (mina →
      caverna → abismo) y luz que se apaga por tramo (LUCES decrecientes)
- [x] Fauna fija: cangrejos y medusas que estorban sin dañar (AUD-575),
      densidad decreciente y ninguna en la zona del pez (AUD-576)
- [x] Nueve bloques de mineral destructibles (AUD-557 + AUD-575)
- [x] Tileset propio de la mina (9 filas: estalactitas, algas, viga,
      óxido, soporte con riel) y sprites de cangrejo/medusa (AUD-575)
- [x] Veinte luces en tres temperaturas — warm/blood/white (AUD-575)
- [x] Música `4_1_b.mp3` declarada y registrada (AUD-575)
- [x] Corrientes de agua, ocho franjas, magnitud verificada por
      simulación (AUD-543 + AUD-575/576)
- [x] Partícula de ambiente `"vida_abisal"` (AUD-543)
- [x] Registrado en el sorteo (`selector.VARIANTES_DISPONIBLES["acuatico"]`)
- [x] El nado de verdad: sin salto de tierra bajo el agua, sin WALKING
      sumergido, sin hundirse con gravedad completa (AUD-573)
- [x] Agua legible y límite marcado: tinte `#1a5c6e`/alpha 150,
      `ambient_light=0.45`, faroles de radio 230 — la lectura de SMB 2-2
      (AUD-574)
- [x] `tests/test_stage4_1b.py`, `tests/test_enemy_pez_abismal.py`,
      `tests/test_oxigeno_del_hud.py`

**Sigue pendiente** (no bloquea el sorteo, es pulido futuro):

- Variedad narrativa por sección — el cementerio tiene seis identidades de
  fase propias (`fases.py`); 4-1b ya no es una sola ambientación: los tres
  fondos y los beats de AUD-576 cuentan la transformación mina → abismo,
  pero cada sección interior (entrada, galería, patio, esclusa, pozo,
  desagüe) aún no tiene marcador de identidad propio de la escala del
  cementerio.