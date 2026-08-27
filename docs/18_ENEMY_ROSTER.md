---
document_id: "LOI-ENEMIES-018"
title: "Legacy of InFest — Elenco de enemigos"
aliases: ["Elenco de enemigos", "Enemy Roster"]
tags: ["enemigos", "elenco", "entidades"]
description: "Cada enemigo estándar, por zona"
source: "docs/18_ENEMY_ROSTER.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Elenco de enemigos

**ID del documento:** LOI-ROSTER-018
**Versión:** 1.1.0
**Estado:** Oficial
**Requiere:** `05_ENEMY_SPEC.md`
**Audiencia:** Profesor, estudiantes, artistas, asistentes de código

> **AUD-455.** Traduce el documento completo (antes en inglés). Verificado
> con una muestra de 5 especies (`WalkerInsect`, `FlyingBird`, `ShooterFrog`,
> `WalkerRaton`, `WalkerEstudiante`) contra `src/framework/entities/bestiary_registry.py`:
> las 21 especies y todas las estadísticas de la muestra coinciden
> exactamente con el código real.

---

## 1. Visión general

Este documento define cada enemigo estándar (no jefe) que aparece en Legacy of InFest. Cada enemigo es una subclase de una de las tres plantillas base: `EnemyWalker`, `EnemyFlying` o `EnemyShooter` (ver `05_ENEMY_SPEC.md`).

Los enemigos se organizan por zona. Cada zona tiene su propio conjunto temático de enemigos que refleja el ambiente y el espíritu que la gobierna. Los estudiantes que construyen escenarios de travesía dentro de una zona usan los enemigos definidos para esa zona — no crean nuevos tipos base de enemigo, pero pueden heredar y configurar los enemigos de zona con propiedades TMX personalizadas.

---

## 2. Zona 1 — Enemigos de la Universidad Invenio

Los enemigos de la Zona 1 reflejan el campus de selva: insectos, animales pequeños y criaturas desplazadas del bosque por el despertar de El Venado Sagrado.

### 2.1 `WalkerInsect` — Insecto de suelo

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyWalker` |
| Aparece en | Stage 1-1, 1-2 |
| Vida | 1.0 corazón |
| Daño de contacto | 0.25 corazones |
| Velocidad de patrulla | 35 px/s |
| Velocidad de alerta | 55 px/s |
| Rango de detección X | 120 px |
| Longitud de patrulla (por defecto) | 64 px |

**Visual:** un escarabajo grande de selva — caparazón marrón oscuro, seis patas animadas. Sprite: `enemy_insecto_walk.png` (6 fotogramas, 10 FPS). Tamaño: 16×12 px.

**Nota de comportamiento:** lento, predecible. El primer enemigo que encuentra el jugador. Diseñado para enseñar la respuesta básica de ataque sin peligro significativo.

**Nota académica (Unidad II):** la detección de repisa usa una sonda `vec2_distance`. Documentado en el código fuente.

---

### 2.2 `FlyingBird` — Ave de selva

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyFlying` |
| Aparece en | Stage 1-1, 1-3 |
| Vida | 1.0 corazón |
| Daño de contacto | 0.25 corazones |
| Modo de vuelo | Seno |
| Amplitud senoidal | 24 px |
| Frecuencia senoidal | 1.4 Hz |
| Velocidad de vuelo | 55 px/s |
| Rango de detección X | 160 px |

**Visual:** un ave tropical pequeña (coloración inspirada en el momoto — verde azulado y naranja). Sprite: `enemy_pajaro_fly.png` (4 fotogramas, 12 FPS). Tamaño: 14×10 px.

**Nota de comportamiento:** baja en picado sobre el camino. La onda senoidal hace difícil saltarla. Los jugadores aprenden a agacharse a tiempo bajo ella.

---

### 2.3 `ShooterFrog` — Rana dardo venenosa

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyShooter` |
| Aparece en | Stage 1-1, 1-3 |
| Vida | 2.0 corazones |
| Daño de contacto | 0.25 corazones |
| Daño de proyectil | 0.25 corazones |
| Cadencia de disparo | 0.4 disparos/s |
| Velocidad de proyectil | 90 px/s |
| Rango de detección X | 180 px |
| Longitud de patrulla | 0 (estacionaria) |

**Visual:** una rana dardo venenosa roja y azul (Oophaga pumilio — la rana dardo fresa, nativa de Costa Rica). Sprite: `enemy_rana_idle.png` (4 fotogramas, 6 FPS). Tamaño: 12×12 px. **Proyectil:** gotita tóxica pequeña, `enemy_rana_proyectil.png` (2 fotogramas, 8 FPS, 4×4 px).

**Nota de comportamiento:** estacionaria — se posa en rocas y superficies elevadas. Amenaza de largo alcance que obliga al jugador a acortar distancia.

---

### 2.4 `WalkerRaton` — Rata de laboratorio

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyWalker` |
| Aparece en | Stage 1-2 |
| Vida | 1.0 corazón |
| Daño de contacto | 0.25 corazones |
| Velocidad de patrulla | 55 px/s |
| Velocidad de alerta | 90 px/s |
| Rango de detección X | 96 px |
| Longitud de patrulla | 48 px |

**Visual:** una rata grande — gris, ojos rojos. Animación de carrera. Sprite: `sprite_walker_raton_walk.png` (en `assets/maps/stage1_2_la_soda/`). Tamaño: 14×10 px.

**Nota de comportamiento:** más rápida que WalkerInsect. Su estado de alerta es notablemente veloz — los jugadores desatentos se ven sorprendidos. Enseña la importancia de prestar atención a los rangos de detección.

---

### 2.5 `FlyingCucaracha` — Cucaracha voladora

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyFlying` |
| Aparece en | Stage 1-2 |
| Vida | 1.0 corazón |
| Daño de contacto | 0.25 corazones |
| Modo de vuelo | Seno |
| Amplitud senoidal | 16 px |
| Frecuencia senoidal | 2.0 Hz |
| Velocidad de vuelo | 45 px/s |

**Visual:** una cucaracha con las alas desplegadas — caparazón marrón, brillante. Sprite: `sprite_flying_cucaracha_fly.png` (en `assets/maps/stage1_2_la_soda/`). Tamaño: 12×8 px. Animación de aleteo de alta frecuencia.

**Nota de comportamiento:** la alta frecuencia senoidal hace su movimiento errático de cerca. Llena el espacio medio vertical de la cafetería.

---

### 2.6 `ShooterCocinero` — Cocinero rebelde

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyShooter` |
| Aparece en | Stage 1-2 (único — 1 por escenario) |
| Vida | 3.0 corazones |
| Daño de contacto | 0.25 corazones |
| Daño de proyectil | 0.50 corazones |
| Cadencia de disparo | 0.5 disparos/s |
| Velocidad de proyectil | 110 px/s |

**Visual:** un cocinero de cafetería con uniforme manchado, lanzando comida. Sprites: `enemy_cocinero_idle.png` y `enemy_cocinero_throw.png`. Tamaño: 16×24 px. **Proyectil:** bandeja de comida, `enemy_cocinero_tray.png` (2 fotogramas, 8 FPS, 12×6 px, rotación tambaleante).

**Nota de comportamiento:** apostado tras el mostrador de la cafetería (lo usa como cobertura — la hurtbox queda parcialmente oculta por la geometría del mostrador). El jugador debe saltar el mostrador para acortar distancia.

---

### 2.7 `WalkerEstudiante` — Estudiante infestado

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyWalker` |
| Aparece en | Stage 1-3 |
| Vida | 1.5 corazones |
| Daño de contacto | 0.50 corazones |
| Velocidad de patrulla | 40 px/s |
| Velocidad de alerta | 70 px/s |
| Rango de detección X | 144 px |
| Longitud de patrulla | 80 px |

**Visual:** un estudiante universitario — mochila, teléfono en mano (usado como arma). Sprite: `enemy_estudiante_walk.png` (8 fotogramas, 10 FPS). Tamaño: 16×24 px. El proyectil de teléfono (en la variante ShooterEstudiante) es un pequeño brillo de pantalla.

**Nota de comportamiento:** algo más de vida que los caminantes de la Zona 1 — representa la escalada hacia la zona de las aulas. Su movimiento de alerta es de velocidad humana creíble.

---

### 2.8 `FlyingNotebook` — Hojas de cuaderno animadas

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyFlying` |
| Aparece en | Stage 1-3 |
| Vida | 0.5 corazones |
| Daño de contacto | 0.25 corazones |
| Modo de vuelo | Seno |
| Amplitud senoidal | 32 px |
| Frecuencia senoidal | 1.0 Hz |
| Velocidad de vuelo | 50 px/s |

**Visual:** hojas de cuaderno sueltas animadas, volando por el aire — girando despacio. Sprite: `enemy_hoja_fly.png` (4 fotogramas, 8 FPS). Tamaño: 10×14 px.

**Nota de comportamiento:** muy poca vida — un ataque corto la mata. Pero vienen en parejas o tríos. Enseña la distinción entre amenaza individual y de grupo.

---

### 2.9 `ShooterTiza` — Lanzador de tiza

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyShooter` |
| Aparece en | Stage 1-3 |
| Vida | 2.5 corazones |
| Daño de proyectil | 0.25 corazones |
| Cadencia de disparo | 1.0 disparos/s |
| Velocidad de proyectil | 130 px/s |
| Longitud de patrulla | 0 (estacionario) |

**Visual:** un borrador de pizarra animado (antropomórfico — el espíritu del aula). Sprite: `enemy_tiza_idle.png`. Tamaño: 14×14 px. **Proyectil:** tiza, `enemy_tiza_proyectil.png` (1 fotograma, 4×4 px, giro rápido).

**Nota de comportamiento:** cadencia alta. Estacionario en los extremos de la pizarra. Largo alcance. Crea una zona de fuego que el jugador debe atravesar con carreras cronometradas entre disparos de tiza.

---

## 3. Zona 2 — Enemigos de El Datacenter

Los enemigos de la Zona 2 son a base de serpientes. Todos los caminantes son serpientes. Todos los voladores son variantes aéreas de serpiente. El tirador representa la capacidad de escupir a distancia de la terciopelo.

### 3.1 `WalkerSerpientePequena` — Terciopelo pequeña

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyWalker` |
| Aparece en | Stage 2-1, 2-2, 2-3, 2-4 (como invocación de jefe) |
| Vida | 1.0 corazón |
| Daño de contacto | 0.50 corazones |
| Velocidad de patrulla | 55 px/s |
| Velocidad de alerta | 100 px/s |
| Rango de detección X | 96 px |

**Visual:** una terciopelo pequeña — patrón marrón y bronceado. Animación reptante. Sprite: `enemy_terciopelo_small_walk.png` (6 fotogramas, 12 FPS). Tamaño: 20×8 px (ancha, baja).

**Nota de comportamiento:** hitbox baja — hacen falta ataques agachados. Alto daño de contacto para su nivel de vida — son peligrosas pese a su tamaño.

---

### 3.2 `FlyingBoa` — Boa aérea

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyFlying` |
| Aparece en | Stage 2-1, 2-2 |
| Vida | 2.0 corazones |
| Daño de contacto | 0.50 corazones |
| Modo de vuelo | Seno |
| Amplitud senoidal | 30 px |
| Frecuencia senoidal | 0.8 Hz |
| Velocidad de vuelo | 45 px/s |

**Visual:** una boa constrictora grande — aérea, ondulando por el aire. Sprite: `enemy_boa_fly.png` (6 fotogramas, 10 FPS). Tamaño: 32×12 px. Hitbox grande — más difícil de esquivar.

---

### 3.3 `ShooterSerpienteArbol` — Víbora arborícola tiradora

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyShooter` |
| Aparece en | Stage 2-1, 2-2, 2-3 |
| Vida | 2.0 corazones |
| Daño de proyectil | 0.50 corazones (veneno) |
| Cadencia de disparo | 0.6 disparos/s |
| Velocidad de proyectil | 100 px/s |
| Longitud de patrulla | 0 (estacionaria) |

**Visual:** una víbora arborícola verde — enroscada en un objeto elevado (poste de cerca, soporte de antena, parte superior de un separador de oficina). Sprite: `enemy_serpiente_arbol_idle.png`. Tamaño: 14×16 px. **Proyectil:** grumo de veneno verde, `enemy_venom_proyectil.png` (2 fotogramas, 8 FPS, 5×5 px).

---

### 3.4 `WalkerTerciopelo` — Terciopelo grande

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyWalker` |
| Aparece en | Stage 2-3 |
| Vida | 2.5 corazones |
| Daño de contacto | 0.75 corazones |
| Velocidad de patrulla | 40 px/s |
| Velocidad de alerta | 80 px/s |
| Rango de detección X | 160 px |

**Visual:** una terciopelo grande, adulta. Cuerpo más grueso, más lenta pero más pesada. Sprite: `enemy_terciopelo_large_walk.png` (6 fotogramas, 8 FPS). Tamaño: 28×12 px.

---

### 3.5 `ShooterVenomoLargo` — Tirador de veneno de largo alcance

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyShooter` |
| Aparece en | Stage 2-3 |
| Vida | 3.0 corazones |
| Daño de proyectil | 0.50 corazones |
| Cadencia de disparo | 0.4 disparos/s |
| Velocidad de proyectil | 150 px/s |
| Rango de detección X | 220 px |

**Visual:** una variante de cobra escupidora — elevada, balanceándose. Sprite: `enemy_cobra_idle.png`. Tamaño: 16×20 px. **Proyectil:** chorro de veneno de largo alcance, `enemy_venom_stream.png` (4 fotogramas, 12 FPS, 8×4 px).

---

### 3.6 `FlyingTerciovolador` — Serpiente alada

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyFlying` |
| Aparece en | Stage 2-3 |
| Vida | 1.5 corazones |
| Daño de contacto | 0.50 corazones |
| Modo de vuelo | Bézier (caminos cortos de 3 puntos) |
| Velocidad de vuelo | 70 px/s |
| Rango de detección X | 180 px |

**Visual:** una pequeña serpiente alada — diseño mitológico, dos alas pequeñas. Sprite: `enemy_terciovolador_fly.png` (6 fotogramas, 12 FPS). Tamaño: 18×14 px.

---

### 3.7 `WalkerGuardia` — Guardia de seguridad del Datacenter

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyWalker` |
| Aparece en | Stage 2-2 (estacionamiento) |
| Vida | 3.0 corazones |
| Daño de contacto | 0.50 corazones |
| Velocidad de patrulla | 45 px/s |
| Velocidad de alerta | 65 px/s |

**Visual:** un guardia de seguridad — uniforme, linterna. Bajo la influencia de las serpientes (ojos con un leve brillo verde). Sprite: `enemy_guardia_walk.png` (8 fotogramas, 10 FPS). Tamaño: 16×24 px.

---

## 4. Zona 3 — Enemigos de la Sede Heredia

Los enemigos de la Zona 3 son a base de aves — el dominio de El Gavilán. Todos los caminantes son aves terrestres. Los voladores son rapaces. Los tiradores son aves posadas que disparan proyectiles de plumas o pico.

### 4.1 `WalkerGarza` — Garza

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyWalker` |
| Aparece en | Stage 3-1 |
| Vida | 2.0 corazones |
| Daño de contacto | 0.50 corazones |
| Velocidad de patrulla | 35 px/s |
| Velocidad de alerta | 60 px/s |

**Visual:** una garza grande (variante de Ardea herodias — garza azulada). Pasos lentos y deliberados. Sprite: `enemy_garza_walk.png` (6 fotogramas, 7 FPS). Tamaño: 18×28 px (alta).

**Nota de comportamiento:** hitbox alta — el barrido bajo del ataque largo es efectivo. El ataque corto puede fallar si el jugador no está agachado.

---

### 4.2 `FlyingHalcon` — Gavilán caminero (estándar)

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyFlying` |
| Aparece en | Stage 3-1, 3-2, 3-3 |
| Vida | 2.0 corazones |
| Daño de contacto | 0.75 corazones |
| Modo de vuelo | Seno + picado de alerta |
| Amplitud senoidal | 20 px |
| Frecuencia senoidal | 0.6 Hz |
| Comportamiento de alerta | Se lanza en picado directo a la X del jugador, luego vuelve a subir |
| Velocidad de vuelo | 65 px/s / 200 px/s (picado) |

**Visual:** un gavilán caminero en vuelo — parte inferior marrón y blanca. Sprites: `enemy_halcon_fly.png` (6 fotogramas, 12 FPS) y `enemy_halcon_dive.png` (4 fotogramas, 18 FPS). Tamaño: 20×14 px.

**Comportamiento personalizado — picado de alerta:**
Cuando el jugador entra en el rango de detección, el gavilán pasa a un picado: se mueve horizontalmente hasta la posición X del jugador (50px/s), luego se lanza en picado a 200px/s. Al llegar a Y=200 o tocar una plataforma, vuelve a subir a su altitud de patrulla. Esto sobreescribe el comportamiento de alerta estándar de `EnemyFlying`.

---

### 4.3 `ShooterQuetzal` — Quetzal francotirador

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyShooter` |
| Aparece en | Stage 3-1, 3-2, 3-3 |
| Vida | 2.5 corazones |
| Daño de proyectil | 0.25 corazones (pluma) |
| Cadencia de disparo | 0.8 disparos/s |
| Velocidad de proyectil | 120 px/s |
| Longitud de patrulla | 0 (estacionario) |

**Visual:** un quetzal resplandeciente (Pharomachrus mocinno — ave sagrada de Costa Rica). Posado en repisas y remates de arcos. Sprite: `enemy_quetzal_idle.png` (4 fotogramas, 6 FPS). Tamaño: 12×20 px (erguido). **Proyectil:** pluma larga de la cola, `enemy_quetzal_feather.png` (2 fotogramas, con giro, 3×10 px).

**Nota cultural:** el quetzal es una de las aves más veneradas de la cultura centroamericana. Su representación aquí es respetuosa — está bajo la influencia de la máscara maleku, no es agresivo por naturaleza.

---

### 4.4 `WalkerPalom` — Paloma doméstica (corrompida)

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyWalker` |
| Aparece en | Stage 3-2, 3-3 |
| Vida | 2.5 corazones |
| Daño de contacto | 0.50 corazones |
| Velocidad de patrulla | 30 px/s |
| Velocidad de alerta | 55 px/s |
| Rango de detección X | 128 px |

**Visual:** una paloma grande y agresiva — ojos rojos por la influencia del gavilán. Envalentonada. Sprite: `enemy_palom_walk.png` (6 fotogramas, 8 FPS). Tamaño: 16×16 px.

**Nota de comportamiento:** lenta pero resistente. Llena la amenaza a nivel de suelo en el amplio escenario del Hall. Su gran reserva de vida hace que persistan como peligro incluso mientras el jugador lidia con amenazas aéreas.

---

### 4.5 `ShooterBuitre` — Zopilote negro (posado)

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyShooter` |
| Aparece en | Stage 3-2 |
| Vida | 3.5 corazones |
| Daño de proyectil | 0.50 corazones |
| Cadencia de disparo | 0.35 disparos/s |
| Velocidad de proyectil | 100 px/s |
| Rango de detección X | 240 px |

**Visual:** un zopilote negro grande (Coragyps atratus — común en zonas urbanas de Costa Rica). Posado en barandillas de balcón, encorvado. Sprite: `enemy_buitre_idle.png` (4 fotogramas, 5 FPS). Tamaño: 18×22 px. **Proyectil:** fragmento de hueso, `enemy_buitre_proyectil.png` (2 fotogramas, tambaleante, 8×6 px).

**Nota de comportamiento:** rango de detección muy largo — 240px significa que puede enganchar al jugador desde fuera de pantalla al principio del Hall. Combinado con los picados del gavilán, crea situaciones de fuego cruzado.

### 2.8 `Shielded` — Guardia con escudo (Datacenter)

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyShielded` |
| Aparece en | Stage 2-1, 2-2 |
| Vida | 3.0 corazones |
| Daño de contacto | 0.50 corazones |
| Vida de escudo | 3.0 |
| Velocidad de patrulla | 35 px/s |
| Longitud de patrulla | 80 px |

**Visual:** guardia con escudo frontal metálico. Sprite: `Shielded_walk.png` 16×24 (placeholder). El escudo bloquea daño frontal.

---

### 2.9 `Swimmer` — Nadador de esclusa

| Propiedad | Valor |
|---|---|
| Clase base | `EnemySwimmer` |
| Aparece en | Stage 2-2, 4-1b |
| Vida | 2.0 corazones |
| Daño de contacto | 0.50 corazones |
| Velocidad de nado | 70 px/s |

**Visual:** nadador con aletas, deriva con corriente. Sprite: `Swimmer_walk.png` 16×24.

---

### 2.10 `FlyingBomber` — Bombardero de datacenter

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyFlyingBomber` |
| Aparece en | Stage 2-1, 2-2 |
| Vida | 2.0 corazones |
| Daño de contacto | 0.50 corazones |
| Modo de vuelo | Seno |
| Amplitud senoidal | 30 px |
| Frecuencia senoidal | 1.0 Hz |

**Visual:** dron bombardero. Sprite: `FlyingBomber_walk.png` 16×24.

---

### 2.11 `BruteGolemHielo` — Gólem de hielo (Datacenter)

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyBrute` |
| Aparece en | Stage 2-1 |
| Vida | 3.5 corazones |
| Daño de contacto | 0.75 corazones |

**Visual:** gólem de hielo que ejecuta ground slam. Sprite: `BruteGolemHielo_walk.png` 16×24.

---

### 2.12 `ChargerWolf` — Lobo de planicie

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyCharger` |
| Aparece en | Stage 2-1, 2-2 |
| Vida | 3.5 corazones |
| Daño de contacto | 1.00 corazones |
| Velocidad de carga | 250 px/s |

**Visual:** lobo que carga con telegraph. Sprite: `ChargerWolf_walk.png` 16×24.

---

### 1.10 `Climber` — Trepador de lianas

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyClimber` |
| Aparece en | Stage 1-1, stage_mecanicas |
| Vida | 2.0 corazones |
| Daño de contacto | 0.50 corazones |
| Velocidad de trepa | 70 px/s |

**Visual:** trepador que usa Liana y Tirolesa. Sprite: `Climber_walk.png` 16×24.

---

### 3.6 `ArcherQuetzal` — Arquero quetzal

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyArcher` |
| Aparece en | Stage 3-1, 3-2 |
| Vida | 2.5 corazones |
| Daño de contacto | 0.25 corazones |
| Cadencia de disparo | 0.5 disparos/s |
| Velocidad de proyectil | 110 px/s |
| Daño de proyectil | 0.50 corazones |

**Visual:** quetzal arquero con tiro en arco. Sprite: `ArcherQuetzal_walk.png` 16×24.

---

### 3.7 `CasterHealer` — Curandero de Heredia

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyCaster` |
| Aparece en | Stage 3-2, 3-3 |
| Vida | 2.5 corazones |
| Daño de contacto | 0.25 corazones |

**Visual:** curandero con orbe perseguidor. Sprite: `CasterHealer_walk.png` 16×24.

---

### 3.8 `TerrainShaper` — Modelador de terreno

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyTerrainShaper` |
| Aparece en | Stage 3-3 |
| Vida | 3.0 corazones |
| Daño de contacto | 0.50 corazones |
| Longitud de patrulla | 80 px |

**Visual:** modelador que crea bloques y hazards. Sprite: `TerrainShaper_walk.png` 16×24.

---

### 3.9 `Summoner` — Invocador de Heredia

| Propiedad | Valor |
|---|---|
| Clase base | `EnemySummoner` |
| Aparece en | Stage 3-2, 3-3 |
| Vida | 4.0 corazones |
| Daño de contacto | 0.50 corazones |
| Longitud de patrulla | 60 px |

**Visual:** invocador que genera esbirros. Sprite: `Summoner_walk.png` 16×24.

---

### 4.6 `Cangrejo` — Cangrejo de mina (presencia)

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyCangrejo` |
| Aparece en | Stage 4-1b (S3) |
| Vida | 1.0 corazón |
| Daño de contacto | 0.00 corazones |
| Velocidad de patrulla | 22 px/s |
| Longitud de patrulla | 80 px |

**Visual:** cangrejo de la mina, no daña. Sprite: `Cangrejo_walk.png` 16×24.

---

### 4.7 `Medusa` — Medusa de pozo (presencia)

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyMedusa` |
| Aparece en | Stage 4-1b (S4/S5) |
| Vida | 1.0 corazón |
| Daño de contacto | 0.00 corazones |
| Modo de vuelo | Seno |
| Amplitud senoidal | 14 px |
| Frecuencia senoidal | 0.4 Hz |

**Visual:** medusa translúcida que deriva. Sprite: `Medusa_walk.png` 16×24.

---

### 4.8 `PezAbismal` — Pez abismal (presencia)

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyPezAbismal` |
| Aparece en | Stage 4-1b (S2) |
| Vida | 1.0 corazón |
| Daño de contacto | 0.00 corazones |
| Modo de vuelo | Seno + chase |
| Velocidad de vuelo | 85 px/s |

**Visual:** pez oscuro con luz pulsante. Sprite: `PezAbismal_walk.png` 16×24.

---

### 4.9 `AssassinSombra` — Sombra del cementerio

| Propiedad | Valor |
|---|---|
| Clase base | `EnemyAssassin` |
| Aparece en | Stage 4-1b, 4-1c |
| Vida | 2.0 corazones |
| Daño de contacto | 0.50 corazones |

**Visual:** sombra sigilosa del cementerio. Sprite: `AssassinSombra_walk.png` 16×24.

---

## 5. Zona final — Enemigos del cementerio

El cementerio no tiene enemigos estándar durante el Stage 4-1 (vacío a propósito — ver el diseño del mundo). Los únicos encuentros de enemigo son con el jefe final en el Stage 4-2.

Sin embargo, pueden aparecer **Ecos espirituales** — versiones espectrales de enemigos de zona ya derrotados — durante el ataque `ANCIENT_CALL` de El Gran Shamán Paburu:

| Eco | Origen | Vida | Daño |
|---|---|---|---|
| `EchoVenado` | Fase 1 de El Venado Sagrado | N/D (un solo ataque, luego se disipa) | 50% del original |
| `EchoRey` | Fase 1 de El Rey Terciopelo | N/D (un solo ataque) | 50% |
| `EchoGavilán` | Fase 1 de El Gavilán | N/D (un solo ataque) | 50% |

Los Ecos espirituales se implementan como instancias de entidad temporales que usan los sprites del jefe con `set_alpha(120)`. No tienen barra de vida. Un ataque y se autodestruyen.

---

## 6. Tabla resumen del elenco de enemigos

| ID | Nombre | Zona | Escenarios | Base | Vida | Contacto | Proyectil |
|---|---|---|---|---|---|---|---|
| E-101 | WalkerInsect | 1 | 1-1, 1-2 | Walker | 1.0 | 0.25 | — |
| E-102 | FlyingBird | 1 | 1-1, 1-3 | Flying | 1.0 | 0.25 | — |
| E-103 | ShooterFrog | 1 | 1-1, 1-3 | Shooter | 2.0 | 0.25 | 0.25 |
| E-104 | WalkerRaton | 1 | 1-2 | Walker | 1.0 | 0.25 | — |
| E-105 | FlyingCucaracha | 1 | 1-2 | Flying | 1.0 | 0.25 | — |
| E-106 | ShooterCocinero | 1 | 1-2 | Shooter | 3.0 | 0.25 | 0.50 |
| E-107 | WalkerEstudiante | 1 | 1-3 | Walker | 1.5 | 0.50 | — |
| E-108 | FlyingNotebook | 1 | 1-3 | Flying | 0.5 | 0.25 | — |
| E-109 | ShooterTiza | 1 | 1-3 | Shooter | 2.5 | — | 0.25 |
| E-201 | WalkerSerpientePequena | 2 | 2-1 a 2-4 | Walker | 1.0 | 0.50 | — |
| E-202 | FlyingBoa | 2 | 2-1, 2-2 | Flying | 2.0 | 0.50 | — |
| E-203 | ShooterSerpienteArbol | 2 | 2-1 a 2-3 | Shooter | 2.0 | — | 0.50 |
| E-204 | WalkerTerciopelo | 2 | 2-3 | Walker | 2.5 | 0.75 | — |
| E-205 | ShooterVenomoLargo | 2 | 2-3 | Shooter | 3.0 | — | 0.50 |
| E-206 | FlyingTerciovolador | 2 | 2-3 | Flying | 1.5 | 0.50 | — |
| E-207 | WalkerGuardia | 2 | 2-2 | Walker | 3.0 | 0.50 | — |
| E-301 | WalkerGarza | 3 | 3-1 | Walker | 2.0 | 0.50 | — |
| E-302 | FlyingHalcon | 3 | 3-1 a 3-3 | Flying | 2.0 | 0.75 | — |
| E-303 | ShooterQuetzal | 3 | 3-1 a 3-3 | Shooter | 2.5 | — | 0.25 |
| E-304 | WalkerPalom | 3 | 3-2, 3-3 | Walker | 2.5 | 0.50 | — |
| E-305 | ShooterBuitre | 3 | 3-2 | Shooter | 3.5 | — | 0.50 |
| E-208 | Shielded | 2 | 2-1, 2-2 | Shielded | 3.0 | 0.50 | — |
| E-209 | Swimmer | 2 | 2-2, 4-1b | Swimmer | 2.0 | 0.50 | — |
| E-210 | FlyingBomber | 2 | 2-1, 2-2 | FlyingBomber | 2.0 | 0.50 | — |
| E-211 | BruteGolemHielo | 2 | 2-1 | Brute | 3.5 | 0.75 | — |
| E-212 | ChargerWolf | 2 | 2-1, 2-2 | Charger | 3.5 | 1.00 | — |
| E-110 | Climber | 1 | 1-1, mecánicas | Climber | 2.0 | 0.50 | — |
| E-306 | ArcherQuetzal | 3 | 3-1, 3-2 | Archer | 2.5 | 0.25 | 0.50 |
| E-307 | CasterHealer | 3 | 3-2, 3-3 | Caster | 2.5 | 0.25 | 0.50 |
| E-308 | TerrainShaper | 3 | 3-3 | TerrainShaper | 3.0 | 0.50 | — |
| E-309 | Summoner | 3 | 3-2, 3-3 | Summoner | 4.0 | 0.50 | — |
| E-401 | Cangrejo | 4 | 4-1b | Cangrejo | 1.0 | 0.00 | — |
| E-402 | Medusa | 4 | 4-1b | Medusa | 1.0 | 0.00 | — |
| E-403 | PezAbismal | 4 | 4-1b | PezAbismal | 1.0 | 0.00 | — |
| E-404 | AssassinSombra | 4 | 4-1b, 4-1c | Assassin | 2.0 | 0.50 | — |

---

## 7. Restricciones de diseño de enemigos para estudiantes

Los estudiantes que construyen escenarios de travesía (1-1 a 1-3, 2-1 a 2-3, 3-1 a 3-3) deben seguir estas reglas al colocar enemigos:

| Regla | Descripción |
|---|---|
| Usar sólo enemigos apropiados de la zona | Enemigos de la Zona 1 sólo en escenarios de la Zona 1, etc. |
| Máximo 3 tipos de enemigo distintos por escenario | Profundidad antes que amplitud |
| No mezclar elencos de zonas | Sin serpientes de la Zona 2 en escenarios de selva de la Zona 1 |
| Las propiedades de enemigo se pueden sobreescribir vía TMX | `patrol_length`, `damage_on_contact`, las velocidades se pueden ajustar |
| Las subclases de enemigo nuevas necesitan aprobación del profesor | Los enemigos personalizados deben extender una plantilla base |
| Los recuentos de enemigo deben ser manejables | No más de 12 enemigos activos simultáneos en un mismo escenario |

---

## 8. Progresión de enemigos

La dificultad escala deliberadamente entre zonas y dentro de cada zona:

| Zona | Rango de vida | Rango de daño | Perfil de velocidad |
|---|---|---|---|
| 1 — Campus | 0.5–3.0 corazones | 0.25–0.50 corazones | Lento a moderado |
| 2 — Datacenter | 1.0–3.5 corazones | 0.50–0.75 corazones | Moderado a rápido |
| 3 — Heredia | 2.0–3.5 corazones | 0.50–0.75 corazones | Moderado + aéreo |
| Final — Cementerio | Sólo ecos de jefe | 50% de los valores de jefe | Variable |

Esta progresión garantiza que el Stage 0 (que usa enemigos neutrales a la zona) se sienta accesible, mientras que los escenarios de estudiante llevan una escalada de amenaza apropiada.
