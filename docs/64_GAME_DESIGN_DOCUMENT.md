---
document_id: "LOI-GDD-064"
title: "Legacy of InFest — Documento de Diseño del Juego"
aliases: ["Game Design Document", "GDD", "Documento de Diseño del Juego"]
tags: ["gdd", "design", "gameplay", "narrative", "world"]
description: "Referencia completa de diseño del juego: visión, narrativa, mundo, jugabilidad, enemigos, jefes, audio, modos"
source: "docs/64_GAME_DESIGN_DOCUMENT.md"
date_processed: "2026-08-01"
---

# Legacy of InFest — Game Design Document

**Document ID:** LOI-GDD-064
**Version:** 1.0.0
**Status:** Official — Game Design Reference
**Compatibility:** Requires `01_PROJECT_CHARTER.md`, `16_WORLD_DESIGN.md`, `17_BOSS_SPEC.md`, `18_ENEMY_ROSTER.md`, `19_NARRATIVE_AND_LORE.md`, `20_ASSET_BIBLE.md`
**Audience:** Professor, Teaching Assistants, Students, Artists, AI coding assistants

> **AUD-455 (2026-08-13).** Verificado contra el código real: exigía Python
> 3.14+ (el mínimo real del proyecto es 3.11, CI corre 3.11/3.12/3.13);
> `§5.3` decía 19 estados de jugador y listaba 18 — el enum `PlayerState` real
> tiene **26** (ver `04_PLAYER_SPEC.md` §8.1, recontado dos veces); `§6.1`
> listaba sólo 4 estados de `EnemyBase` (`PATROL`/`ALERT`/`HURT`/`DYING`)
> cuando el enum real tiene **13** (ver `05_ENEMY_SPEC.md`); y `§7` mezclaba
> patrones de ataque entre jefes distintos — `PEARL_VOLLEY` y `GOLD_RUSH` son
> patrones de diseño de **Paburu** (Formas 3B/3A), no de El Rey Terciopelo, y
> `SUMMON_ECHOES` es de El Rey (Fase 2), no de Paburu; `RAPID_DIVE` es de El
> Gavilán (Fase 3), no de Paburu. La tabla de `§7` no se reescribe aquí
> entera para no introducir un segundo error por prisa — `17_BOSS_SPEC.md` es
> la fuente autoritativa de patrones por jefe y ya distingue con cuidado lo
> implementado de lo sólo diseñado.

---

## 1. Vision

Legacy of InFest es un juego de plataformas y acción 2D de estética SNES ambientado en la Costa Rica contemporánea, construido sobre un motor educativo propio (Python 3.11+ / Pygame CE). Su propósito es pedagógico: ser el laboratorio semestral en el que los estudiantes de Gráficas por Computadora, Procesamiento de Imágenes, Visión por Computadora y Reconocimiento de Patrones aplican la teoría del curso dentro de un mundo de juego coherente.

**Filosofía de diseño:** el juego existe para que la teoría sea visible. Cada sistema —de las curvas de Bézier al filtrado de convolución— tiene una manifestación concreta dentro del mundo jugable.

---

## 2. Historia

### 2.1 Premisa

John y Jill, dos estudiantes de intercambio, llegan a la Universidad Invenio en Costa Rica. Cada uno trae consigo una reliquia antigua: **La Pepita** (una pepita de oro de Crucitas) y **La Perla** (una extraña perla nacida en un raro coral marino). Sin saberlo, estas reliquias despiertan a los espíritus ancestrales de la tierra —guardianes de la cultura ficticia **Tilawa**— que buscan recuperar las reliquias para restaurar el equilibrio natural.

### 2.2 Archos narrativos

| Acto | Contenido |
|---|---|
| Introducción | 3 pantallas de historia antes del Stage 0 |
| Acto 1 | El campus — La Universidad Invenio reclamada por la selva |
| Acto 2 | El Datacenter — la tecnología despierta al Rey Terciopelo |
| Acto 3 | Sede Heredia — el Gavilán Camionero Mascarero |
| Final | El Cementerio Sagrado — el Gran Shaman Paburu |

### 2.3 Tono

La narrativa es intencionalmente sobria. Se cuenta a través del entorno, el diseño de sprites, la identidad de los jefes y las pantallas de historia. Los jefes **no son malvados**: son guardianes que responden a la presencia de las reliquias. Paburu no es un villano: es una prueba.

---

## 3. Protagonistas

### 3.1 John

Hijo de un empresario vinculado a la explotación minera. Porta **La Pepita**. Directo, impaciente, físico. En combate favorece el ataque corto.

### 3.2 Jill

Hija de una familia relacionada con la industria pesquera. Porta **La Perla**. Metódica, observadora, cautelosa. Favorece el alcance.

### 3.3 El protagonista encapuchado

El framework usa **una única entidad de jugador unificada**. En el Stage 0 la capucha oculta qué protagonista controla el jugador —narrativamente intencional: es el "antes" de que los espíritus los noten. Las diferencias entre John y Jill se expresan en pantallas de historia y en el storytelling ambiental.

---

## 4. Mundo

### 4.1 Estructura general

```
ZONA 1 — Universidad Invenio (Campus Selvático)
    Stage 1-1  La Entrada
    Stage 1-2  La Soda
    Stage 1-3  Las Aulas
    Stage 1-4  La Residencia       [BOSS: El Venado Sagrado]

ZONA 2 — El Datacenter
    Stage 2-1  La Planicie
    Stage 2-2  Entrada y Antenas
    Stage 2-3  Las Oficinas
    Stage 2-4  El Datacenter       [BOSS: El Rey Terciopelo]

ZONA 3 — Sede Heredia
    Stage 3-1  La Entrada de Piedra
    Stage 3-2  El Hall
    Stage 3-3  El Patio
    Stage 3-4  El Bungaló          [BOSS: El Gavilán Camionero Mascarero]

ZONA FINAL — El Cementerio Sagrado
    Stage 4-1  La Entrada al Cementerio
    Stage 4-2  [FINAL BOSS: El Gran Shaman Paburu]
```

### 4.2 Identidad por zona

| Zona | Ambientación | Paleta | Tema BGM | Tema de enemigos |
|---|---|---|---|---|
| Universidad Invenio | Campus universitario rodeado de selva de montaña | Verdes profundos, marrones tierra, ámbar cálido | Percusión tensa + ambiente selvático | Insectos, animales pequeños, estudiantes desorientados |
| El Datacenter | Infraestructura tecnológica fría | Azules, cianes, grises metálicos | Sintetizadores fríos | Terciopelos y criaturas digitales, cucarachas |
| Sede Heredia | Recinto universitario urbano | Rojos, ocres, luz de atardecer | Ritmos urbanos | Aves rapaces, estudiantes mascareros |
| Cementerio Sagrado | Espacio ceremonial Tilawa | Dorados, verdes oscuros, luz de luna | Coros ceremoniales | Espíritus ancestrales, animales guardianes |

### 4.3 Telón de fondo cultural

Todo enemigo y jefe se ancla en la ecología costarricense real: venado cola blanca, terciopelo (*Bothrops asper*), gavilán camionero (*Buteo magnirostris*), rana dardo venenosa, quetzal, garza azulada y zopilote negro. La cultura ancestral es la **Tilawa** —ficcional, creada para el juego— y debe tratarse con el mismo respeto que se exigiría a una cultura viva.

---

## 5. Jugabilidad — Pilar Central

### 5.1 Controles

| Acción | Teclado por defecto | Control por defecto |
|---|---|---|
| Moverse izquierda/derecha | Flechas / A-D | Palanca izquierda / cruceta |
| Saltar | Espacio / W / ↑ | A (Xbox) / Cruz (PS) |
| Agacharse | ↓ / S | Cruceta abajo |
| Ataque corto | Z / J | X (Xbox) / Cuadrado (PS) |
| Ataque largo | X / K | Y (Xbox) / Triángulo (PS) |
| Pausa | Escape / P | Start |

### 5.2 Movimiento y física

| Propiedad | Valor |
|---|---|
| Velocidad de caminar | 90 px/s |
| Gravedad | 800 px/s² |
| Velocidad inicial de salto | -380 px/s |
| Velocidad máxima de caída | 500 px/s |
| Coyote time | 6 frames |
| Saltos aéreos | 1 |
| Dash aéreo | 1 |
| Buffer de salto | 8 frames |

Colisión **axis-separada**: resolución en X seguida de resolución en Y. Plataformas one-way con reconstrucción de `prev_bottom`. Sin rampa de aceleración — movimiento SNES constante.

### 5.3 Estados del jugador

El jugador implementa una máquina de estados de 30 estados (ver `04_PLAYER_SPEC.md` §8.1 para la tabla completa): IDLE, WALKING, JUMPING, FALLING, CROUCHING, SHORT_ATTACK, LONG_ATTACK, HURT, DYING, DASHING, PARRY, CHARGE_ATTACK, CHARGE_RELEASE, DASH_ATTACK, WALL_SLIDE, LEDGE_GRAB, GRAB, THROW, SLIDE, SWIMMING, SWIM_ATTACK, CLIMBING, ZIPLINE, ULTIMATE, AERIAL_ATTACK, AERIAL_SLAM, GROUND_POUND, AIR_CHASE, STAGGER, POSSESSED. El estado SWIMMING se introduce cuando el jugador entra en agua.

### 5.4 Combate

- **Ataque corto:** 0.50 de daño, hitbox 24×20, duración 0.15 s.
- **Ataque largo:** 1.00 de daño, duración 0.4 s. Agochado realiza sweep bajo.
- **Combo:** ventana de 0.5 s; multiplicadores `(1.0, 1.5, 2.0)` hasta combo 3.
- **Parry:** bloqueo con ventana de precisión — emite `VFX_PARRY`.
- **I-frames:** 1.5 s de invencibilidad tras recibir daño.
- **Contacto con enemigo:** daño 0.25–0.5 según enemigo, con knockback 120–150.

### 5.5 Vida y daño

- **Vida máxima:** 5 corazones.
- Cada corazón = 1 HP. El daño se aplica como valor fraccionario (0.25/0.5/1.0).
- La muerte emite `PLAYER_DIED` → Game Over → reintento desde checkpoint.

---

## 6. Enemigos

### 6.1 Clase base `EnemyBase`

15 estados (ver `05_ENEMY_SPEC.md`): `IDLE`, `PATROL`, `SEARCH`, `ALERT`, `CHASE`, `TELEGRAPHING`, `FIRING`, `RECOVER`, `RETREAT`, `STUNNED`, `HURT`, `LAUNCHED`, `DYING`. Todos los enemigos heredan de esta clase y **no sobreescriben `update()`** — implementan `_patrol_behavior`, `_alert_behavior`, `_get_animation_key`, `_build_hitbox`, `_build_hurtbox`.

### 6.2 Roster de enemigos (8 tipos)

| Tipo | Comportamiento | Daño contacto | Vida |
|---|---|---|---|
| **Walker** | Patrulla horizontal, revierte en bordes | 0.5 | 2.0 |
| **Flying** | Vuelo sine, Bézier o waypoint | 0.5 | 1.5 |
| **Shooter** | Dispara proyectiles en rango | 0.25 | 3.0 |
| **Charger** | Carga con viento previo | 0.5 | 4.0 |
| **Archer** | Fuego en arco con trayectoria | 0.5 | 2.0 |
| **Brute** | Melee pesado + golpe de suelo | 1.0 | 6.0 |
| **Caster** | Magia con orbe buscadora | 0.5 | 3.0 |
| **Assassin** | Sigilo + embestida | 0.75 | 2.5 |

### 6.3 Bestiario / Códex

El sistema `bestiary.py` registra encuentros y derrotas por tipo. El Códex (Bestiary Codex) permite al jugador consultar enemigos descubiertos.

---

## 7. Jefes

Todos los jefes heredan de `BossBase` (que extiende `EnemyBase` con gestión de fases, barra de vida de jefe y evento `BOSS_PHASE_CHANGED`). Transiciones de fase: el jefe se vuelve invulnerable, suena la transición, el HUD rellena la nueva fase, `current_phase += 1`.

| Jefe | Zona | Fases | Patrones destacados | Estado |
|---|---|---|---|---|
| **El Venado Sagrado** | 1 | 2 | STOMP, CHARGE, VINE_TOSS / VINE_SWEEP, MUSHROOM_SPORE | ✅ Implementado (`BossVenado`) |
| **El Rey Terciopelo** | 2 | 3 | PEARL_VOLLEY, SERPENT_WAVE, GOLD_RUSH | Planeado (asignación estudiante) |
| **El Gavilán Camionero Mascarero** | 3 | 3 | DIVE_BOMB, MASK_BEAM, FEATHER_STORM | Planeado (confirmado final) |
| **Gran Shaman Paburu** | Final | 4 | SUMMON_ECHOES, RAPID_DIVE, DARK_FIELD | Planeado (reservado profesor) |

Los jefes aplican el pipeline académico completo: movimiento por curvas de la Unidad III, efectos de color y filtros de las Unidades V/VII, y clasificación de fase de la Unidad IX (cuando aplica).

---

## 8. Progresión y Checkpoints

- **Checkpoints:** zonas activadas que fijan el punto de reaparición. Emiten `CHECKPOINT_REACHED`.
- **NextTrigger:** zona que completa el stage → `STAGE_COMPLETE`.
- **Persistencia:** sistema de guardado JSON de 5 slots (SaveManager); preferencias de accesibilidad persistidas en `config.json` (volúmenes, idioma, dificultad, modo daltonismo).
- **Reaparición:** el mapa parseado se cachea — morir no re-parsea el TMX (AUD-027).

---

## 9. HUD e Interfaz

| Elemento | Descripción |
|---|---|
| Retrato | Icono del protagonista |
| Corazones | 5 corazones, animación de daño |
| Temporizador | Cuenta atrás o ascendente según stage (Stage 0 usa ascendente) |
| Puntuación | Puntos por derrotas y recolección |
| Banner de stage | Título animado de entrada con deslizamiento |
| Message Box | Mensajes tutoriales (posición superior) |
| Minimapa | Niebla de guerra explorada |
| Barra de jefe | Nombre, vida, fase cuando hay Boss activo |
| Combo counter | Contador de combo con multiplicador visible |

---

## 10. Mecánicas Expandidas

| Sistema | Descripción | Documento |
|---|---|---|
| **Diálogo ramificado** | Diálogo emergente con retratos y elecciones | `40_DIALOGUE_SYSTEM.md` |
| **Cutscenes** | Escenas guionizadas (sprites, sin cajas de texto) | `42_CUTSCENE_SYSTEM.md` |
| **Natación (SWIMMING)** | Mecánicas de movimiento en agua | `45_SWIMMING_SPEC.md` |
| **Niebla de guerra** | Overlay negro con agujeros revelados | `46_FOG_OF_WAR.md` |
| **Efecto de agua** | Ondas animadas por seno | `47_WATER_EFFECT.md` |
| **Transiciones de pantalla** | Fade, wipe, slide, circle | `48_SCREEN_TRANSITIONS.md` |
| **Audio ambiental** | Capas ambientales por clima | `49_AMBIENT_AUDIO.md` |
| **Speedrun** | Cronómetro global y datos fantasma | `43_SPEEDRUN_MODE.md` |
| **Boss Rush** | Maratón de jefes consecutivos | `44_BOSS_RUSH_MODE.md` |
| **Logros** | Sistema de logros con progreso | `Achievements` |
| **Inventario** | Recolección de objetos | `Inventory` |
| **Modo daltonismo** | Filtros protanopia/deuteranopia/tritanopia | `user_settings` |

---

## 11. Estética y Arte

### 11.1 Dirección de arte

- Resolución interna: **800×600**.
- Tile size: **16 px**.
- Estética SNES: paleta limitada, silueta legible, 16×16 a 32×32 para sprites.
- Fondos parallax en 3–4 planos (cielo, cresta montañosa, dosel, sotobosque).

### 11.2 Paleta por zona (resumen)

| Zona | Color base | Esquinas | Acentos |
|---|---|---|---|
| Universidad Invenio | Verde selva | Marrón tierra | Ámbar |
| Datacenter | Azul oscuro | Gris metálico | Cian |
| Sede Heredia | Rojo óxido | Ocre | Dorado |
| Cementerio | Verde oscuro | Negro azulado | Dorado ceremonial |

### 11.3 Protagonista

Capucha como dispositivo narrativo — nunca se revela el rostro durante el juego. Silueta ágil, paleta limitada, animaciones fluidas.

---

## 12. Audio

### 12.1 Música

Música dinámica por capas: calma → combate → jefe, con crossfade (`DynamicMusicSystem`). Un track por zona.

### 12.2 Efectos

15+ eventos SFX definidos centralmente en `Events` (salto, aterrizaje, pasos, ataques, daño, muerte, hit, proyectiles, checkpoints, banner, stage complete, hazards, parry, boss, UI, ambiente). Disparados por EventBus y reproducidos vía `AudioManager`.

### 12.3 Ambiental

Capas ambientales por clima (lluvia, viento, tormenta). **Caveat conocido:** los assets ambientales buscan `assets/sfx/ambient/{rain,wind,storm}.wav` que no existe — pendiente mapear clima → archivo real (GAP-019).

---

## 13. Modos de Juego

| Modo | Descripción |
|---|---|
| Historia | Progresión lineal por zonas (estándar) |
| Demos Académicas | 10+ laboratorios interactivos (Unidades II–IX) |
| Speedrun | Temporizador global + datos fantasma |
| Boss Rush | Gabinete de jefes consecutivos |
| Sandbox | Zona de pruebas mecánicas |

---

## 14. Sistemas Académicos

| Unidad | Sistema del juego que la demuestra |
|---|---|
| II — Vectores | Lab de vectores, dirección de proyectiles, normalización |
| III — Curvas | Bézier, B-Spline, NURBS, Catmull-Rom (patrones de vuelo, caminos de jefes) |
| IV — Interpolación | Lab de interpolación, easing, animación por keyframes |
| V — Color | ColorTools RGB↔HSV↔HSL↔CMYK, tintes por zona, alpha blend |
| VI — Colisiones | Lab de colisiones, resolución axis-separada, one-way |
| VII — Filtros | FilterTools convolución, Sobel, Canny, brillo, contraste |
| VIII — Visión | Segmentation, umbral, morfología, componentes conectados |
| IX — Reconocimiento | PatternRecognitionTools entrenamiento, HOG/LBP, clasificación |

---

## 15. Motor y Tecnología

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.14+ |
| Framework gráfico | Pygame CE |
| Numpy/SciPy | Cálculo numérico y científico |
| OpenCV / scikit-image | Visión y procesamiento de imágenes |
| scikit-learn | Aprendizaje automático |
| pytmx / pyscroll | Carga y render de mapas TMX |
| pydantic / orjson | Validación y datos |
| ModernGL (optativo) | Post-procesamiento GL con fallback software |
| numba (optativo) | JIT para integrador de partículas |

El motor se organiza en tres capas: `engine/` (núcleo agnóstico), `framework/` (sistemas del juego, incluyendo ECS F5) y `stages/` (contenido). Las reglas de capas L1/L2/L3 están verificadas por la suite en cada ejecución.

---

## 16. Contenido por Zona — Resumen de Diseño

### 16.1 Zona 1 — La Entrada (1-1)

- Tipo: traversal. Sin pits — castigo por contacto únicamente.
- Enemigos: 6 WalkerInsect, 3 FlyingBird, 2 ShooterFrog.
- Parallax: 3 planos. Checkpoint a la mitad. Banner "1-1 LA ENTRADA". Límite 180 s.

### 16.2 Zona 1 — La Soda (1-2)

- Tipo: traversal + combate. Interior ancho de dos pisos.
- Iluminación por color: luz cálida de cocina vs. comedor frío (tinte HSL).

### 16.3 Zona 1 — Las Aulas (1-3)

- Tipo: traversal vertical. Aulas de la universidad.

### 16.4 Zona 1 — La Residencia (1-4)

- **Boss:** El Venado Sagrado. Dos fases: STOMP/CHARGE/VINE_TOSS y VINE_SWEEP/MUSHROOM_SPORE/CHARGE.

### 16.5 Zona 2 — El Datacenter

- **2-1 La Planicie:** zonas planas entre campus y datacenter.
- **2-2 Entrada y Antenas:** exterior con conjuntos de antenas.
- **2-3 Las Oficinas:** interior con oficinas.
- **2-4 El Datacenter:** **Boss: El Rey Terciopelo** — 3 fases.

### 16.6 Zona 3 — Sede Heredia

- **3-1 La Entrada de Piedra:** camino de piedra.
- **3-2 El Hall:** enorme hall universitario.
- **3-3 El Patio:** patio exterior.
- **3-4 El Bungaló:** **Boss: El Gavilán Camionero Mascarero** (3 fases, máscara ceremonial Tilawa).

### 16.7 Zona Final — El Cementerio Sagrado

- **4-1:** entrada al cementerio.
- **4-2:** **Boss final: Gran Shaman Paburu** — 4 formas, guardián ancestral.

---

## 17. Referencias Cruzadas

| Tema | Documento |
|---|---|
| Alcance y visión | `01_PROJECT_CHARTER.md` |
| Arquitectura y estructura | `03_ARCHITECTURE.md` |
| Especificación del jugador | `04_PLAYER_SPEC.md` |
| Especificación de enemigos | `05_ENEMY_SPEC.md` |
| Formato de mapas | `06_TMX_SPEC.md` |
| Stage 0 de referencia | `07_STAGE0_DESIGN.md` |
| HUD | `09_HUD_SPEC.md` |
| Herramientas de procesamiento | `11/12/13_FILTER/VISION/PATTERN_.md` |
| Mundo y zonas | `16_WORLD_DESIGN.md` |
| Jefes | `17_BOSS_SPEC.md` |
| Roster de enemigos | `18_ENEMY_ROSTER.md` |
| Narrativa y lore | `19_NARRATIVE_AND_LORE.md` |
| Biblia de assets | `20_ASSET_BIBLE.md` |
| Contratos API | `22_API_CONTRACTS.md` |
| Mecánicas expandidas | `40–49_*.md` |
| Registro de no implementado | `63_REGISTRO_DE_LO_NO_IMPLEMENTADO.md` |