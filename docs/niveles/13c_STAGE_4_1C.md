---
document_id: "LOI-LVL-4-1C"
title: "Nivel 4-1c — Lo Que Flota en la Niebla"
aliases: ["Stage 4-1c", "Lo que flota en la niebla", "variante aérea de 4-1"]
tags: ["level", "zona-final", "atmospheric", "variante", "musical"]
description: "Ficha de nivel: la variante aérea y musical del sorteo de 4-1 (AUD-518/520)"
source: "docs/niveles/13c_STAGE_4_1C.md"
---

# NIVEL 4-1c — LO QUE FLOTA EN LA NIEBLA

**Entregable:** profesorado (no se asigna a estudiantes) · **Zona:** Final —
El Cementerio Sagrado · **Tipo:** Travesía aérea, musical

## 0. Qué es, y qué no es

Como 4-1b ([[13b_STAGE_4_1B.md]]), 4-1c **no es un nivel aparte**: es la
tercera cara del slot `stage4_1`, sorteada una sola vez por partida
(AUD-518, `src/stages/stage4_1/selector.py`). Construida en AUD-520.

Tiene una segunda capa de variación que las otras dos no tienen: **el
propio nivel cambia de plantilla cada vez que se entra**, no una vez por
partida — pedido explícito del guion (*"que el level design cambie cada
vez que se ingrese"*). Decisión del dueño (2026-08-17, confirmada vía
`AskUserQuestion`): tres plantillas TMX pre-diseñadas elegidas al azar en
cada entrada, no generación procedural en tiempo real — sin precedente en
este motor y con riesgo real de romper la garantía de nivel completable
que sostienen los otros 25+ escenarios.

## 1. Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★★☆☆ (3/5) — el vacío bajo el jugador sube la tensión sobre el cementerio |
| Forma | Horizontal, **tres TMX** (`stage4_1c_a/b/c.tmx`), seis secciones — misma longitud que 4-1 |
| Ambientación | Sin suelo salvo un colchón de contención muy por debajo — caer cuesta tiempo, no la partida (misma filosofía "cero muerte instantánea" del cementerio) |
| Mecánica central | `RhythmBlock`/`BloqueRitmico` (F6, ya construido para `stage_mecanicas`) — las plataformas aparecen y desaparecen con la música real (`bpm`/`compas` → `RelojMusical`), cero física nueva |
| Enemigos | 0 — como el cementerio; el desafío es la travesía y el ritmo, no el combate |
| Checkpoints | 6, uno por sección — el haz de luz de siempre (AUD-523, universal en los 26 escenarios) |
| Plantillas | 3, semillas 1/2/3, cada una verificada contra `JumpEnvelope.from_settings()` — la envolvente de salto real del jugador, no un número inventado |

## 2. Por qué tres plantillas y no generación en vivo

`src/stages/stage4_1c/trazado.py::generar_ruta(semilla)` sortea una ruta
distinta por semilla, pero cada hueco entre plataformas se valida contra
la física real del salto (`tests/test_stage4_1c.py` lo comprueba con 9
semillas de muestra, no sólo las 3 congeladas). El generador
(`tools/generate_stage4_1c.py`) congela tres semillas en tres ficheros
TMX reales; `Stage4_1C.elegir_plantilla()` sortea con `azar.generador()`
en cada `__init__` cuál de los tres carga.

**Por qué no generar el TMX en tiempo real, si ya está el generador:**
regenerar sobre la marcha exigiría reconstruir todo el pipeline de carga
(`StageLoader`, colisión, ECS) sin el paso por disco que hoy valida cada
mapa (`validate_tmx.py`), y ningún otro nivel del juego carga así — sería
una segunda arquitectura de carga para un solo escenario.

## 3. Lo que se corrigió construyéndolo

La primera versión del generador daba pasos pequeños a plataformas
angostas y producía ~236 por travesía —seis veces más que el mapa más
poblado del juego (`stage_mecanicas`, 37 ids de ECS)—;
`tests/test_los_ids_del_ecs_no_crecen.py` lo cazó contra un techo
deliberado de 200. Se rediseñó con tablones más anchos (~11 baldosas) y
huecos que aprovechan el salto cómodo real: ahora ~68 plataformas por
travesía, misma seguridad de salto verificada.

`grade_stage.py` marca "repechos imposibles" y "plataformas aisladas"
contra estos mapas — verificado que es un falso positivo del analizador
(no modela `RhythmBlock`, y agrupa los muros límite y el colchón de
contención como si fueran parte de la ruta de salto). Documentado en el
generador; no hay nada que corregir en la geometría.

## 4. Reglas obligatorias

1. **Ninguna trampa mortal.** Caer no mata — el colchón de contención
   siempre atrapa.
2. **Cada plataforma, sólida o rítmica, está a un salto seguro de la
   anterior.** No se empalman tramos con una columna fija (el defecto de
   la primera versión).
3. **`bpm`/`compas` obligatorios en el TMX** — sin ellos `RhythmBlock` cae
   al modo por segundos y deja de ser "completamente musical".
4. **`validate_tmx.py --ci` en verde** para las tres plantillas.

## 5. Estado real — construido (AUD-520)

- [x] Tres plantillas TMX, cada una jugable de principio a fin
- [x] Ruta generada y verificada contra la envolvente de salto real
- [x] Plataformas `RhythmBlock` sincronizadas con `RelojMusical`
- [x] Seis checkpoints (el haz de luz universal, AUD-523)
- [x] Colchón de contención — caer no mata
- [x] Tileset propio (paleta de cielo/niebla)
- [x] Registrado en el sorteo (`selector.VARIANTES_DISPONIBLES["aereo"]`)
- [x] `tests/test_stage4_1c.py` (28 pruebas: seguridad de salto en 9
      semillas, sincronía TMX↔generador, jugabilidad, reloj musical)

**Sigue pendiente** (pulido futuro, no bloquea el sorteo): variedad visual
entre plantillas — hoy las tres comparten tileset y paleta; sólo cambia el
trazado de las plataformas.
