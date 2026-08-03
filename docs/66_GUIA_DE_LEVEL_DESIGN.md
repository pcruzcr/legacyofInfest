---
document_id: "LOI-LEVELDESIGN-066"
title: "Legacy of InFest — Guía de Level Design"
aliases: ["Level Design Guide", "Guía de Diseño de Niveles"]
tags: ["level-design", "difficulty", "design", "guide"]
description: "Dificultad, dimensiones y composición de enemigos sugerida para cada nivel y jefe"
source: "docs/66_GUIA_DE_LEVEL_DESIGN.md"
date_processed: "2026-08-01"
---

# Legacy of InFest — Guía de Level Design

**ID del documento:** LOI-LEVELDESIGN-066
**Versión:** 1.0.0
**Estado:** Oficial
**Compatibilidad:** Requiere `16_WORLD_DESIGN.md` (LOI-WORLD-016), `17_BOSS_SPEC.md` (LOI-BOSS-017), `05_ENEMY_SPEC.md` (LOI-ENEMY-005), `06_TMX_SPEC.md`, `07_STAGE0_DESIGN.md`, `18_ENEMY_ROSTER.md`
**Público:** estudiantes, profesorado, asistentes de código

> **Qué es esta guía.** Para cada nivel y cada jefe del juego propone la
> **dificultad recomendada**, las **dimensiones del mapa**, la **composición de
> enemigos** (tipos y cantidades), los **peligros de entorno** y las **reglas de
> ritmo** que deben cumplirse. Es una guía de diseño: ninguna cifra sustituye al
> playtest, pero todas las cifras son un punto de partida probado.
>
> **Fidelidad a la realidad (lección AUD-114).** Las dimensiones de cada ficha
> son las de los **`.tmx` implementados en `assets/maps/`**, no las del papel.
> Cuando un nivel solo existe como diseño de referencia (aún no implementado),
> la ficha lo dice con la etiqueta **[REFERENCIA]** y usa las cifras de
> `16_WORLD_DESIGN.md`. El calificador (`scripts/grade_stage.py`) y el validador
> (`scripts/validate_tmx.py`) comprueban los mapas reales; un diseño que no
> coincida con su mapa es ficción.

---

## 1. Principios de diseño de niveles

### 1.1 La dificultad enseña, no castiga

Los niveles de Legacy of InFest existen para que un estudiante **vea funcionar
un concepto del curso** (una curva de Bézier, un filtro, un umbral) dentro de un
juego. Cada nivel tiene **un concepto académico protagonista** y la dificultad
se construye alrededor de hacer visible ese concepto. Reglas:

1. **Un concepto por zona de nivel.** Si el nivel enseña curvas, los enemigos
   vuelan en curvas y el jefe lanza proyectiles en arcos. No mezclar tres
   lecciones en el mismo tramo.
2. **Máximo 3 tipos de enemigo por nivel de estudiante** (constraint de
   `05_ENEMY_SPEC.md`). La profundidad gana a la lista.
3. **Paleta de sprites ≤ 16 colores** (constraint SNES). También aplica a los
   niveles: el color es lenguaje — la soda es cálida, el datacenter es azul
   acero, Heredia es piedra beige, el cementerio es verde espectral.
4. **Ningún sistema oculto** (principio del Stage 0): si un enemigo dispara,
   debe verse disparar; si una plataforma es de un solo sentido, debe leerse.
5. **Dos soluciones donde se pueda.** Un foso que solo se puede saltar es un
   pasillo con examen en medio. Cuando el espacio lo permita, ofrecer ruta
   alternativa (por arriba o por abajo).

### 1.2 La curva de dificultad del juego completo

| Zona | Niveles | Dificultad (1–10) | Subida por nivel |
|---|---|---|---|
| Umbral (Stage 0) | 0 | 1 | +0.5 |
| Zona 1 — Campus | 1-1, 1-2, 1-3 | 1, 2, 3 | +1 |
| Jefe 1 — Venado | 1-4 | 4 | +1 |
| Zona 2 — Datacenter | 2-1, 2-2, 2-3 | 4, 5, 6 | +1 |
| Jefe 2 — Rey | 2-4 | 7 | +1 |
| Zona 3 — Sede Heredia | 3-1, 3-2, 3-3 | 6, 7, 8 | +1 (re-baseline tras el Rey) |
| Jefe 3 — Gavilán | 3-4 | 8 | +0 |
| Cementerio | 4-1 | 7 (atmosférico, sin enemigos) | −1 |
| Jefe final — Paburu | 4-2 | 9–10 | +2 |

Reglas de la curva:

- La subida **nunca supera +1** entre niveles consecutivos, salvo el jefe final.
- Tras cada jefe hay un **descanso**: la primera mitad del nivel siguiente es
  más amable que el final del nivel anterior (el jugador recupera el aliento).
- El 4-1 baja la dificultad a propósito: la atmósfera ES el desafío. No se
  compensa con enemigos — se compensa con tensión.

### 1.3 Métricas de tamaño y ritmo

- **Baldosa base: 16×16 px.** El suelo de los niveles horizontales está en la
  fila 30 (y = 480 px) salvo indicación contraria (estándar de `07_STAGE0_DESIGN.md`).
- **Anchura de una pantalla de juego: 800 px** (resolución interna 800×600).
  Un nivel de 1600 px son ~2 pantallas de scroll; 3200 px, ~4; 3840 px, ~5.
- **Límite de tiempo = 2× el tiempo de limpieza estimado.** Si el recorrido
  despejado se cruza en ~75 s, el límite es ~150 s. Esto da aire para explorar
  y para las dos soluciones, pero penaliza la deambulación.
- **Checkpoint cada 700–1200 px de avance** (una pantalla o pantalla y media):
  un jugador no debería repetir más de una pantalla de trabajo tras morir.
  Salvo que el tramo sea deliberadamente duro (el foso del Stage 0 tiene
  checkpoint justo antes).
- **Enemigos en pantalla simultáneos ≤ 8** en niveles de travesía. Por encima
  de eso, el rendimiento y la legibilidad se degradan juntos.
- **Los jefes no tienen límite de tiempo.** El reloj se oculta al entrar en la
  arena (protocolo de `17_BOSS_SPEC.md` §8.3).

#### Cuánto salta el jugador de verdad

Estas cifras están **medidas** ejecutando al jugador real sobre huecos
sintéticos, no calculadas con la fórmula del tiro parabólico. Reprodúcelas con:

```
python -m tests.playtest.jump_bench
```

| Hueco | Manteniendo la dirección | Soltando la dirección |
|---|---|---|
| 1 baldosa (16 px) | sí, holgado | sí, holgado |
| 2 baldosas (32 px) | sí, 39 % de los despegues | sí, holgado |
| 3 baldosas (48 px) | **sí, sólo 8 %** | sí, 94 % |
| 4 baldosas (64 px) | **no** | sí, 61 % |
| 5 baldosas (80 px) | **no** | sí, 27 % |
| 6 baldosas (96 px) o más | no | no |

Repechos (escalones que hay que subir de un salto): hasta **5 baldosas**
(80 px). La sexta no se sube.

Tres reglas salen de esa tabla:

1. **Diseña con 2 baldosas.** Es el hueco que cualquiera cruza sin pensar.
2. **3 baldosas es un obstáculo, no un tránsito.** Sale de menos de uno de cada
   diez despegues manteniendo la dirección. Úsalo cuando quieras que cueste, con
   checkpoint cerca, y nunca como único camino a la salida.
3. **4 baldosas o más exige una técnica que el jugador no tiene por qué
   conocer** (la de abajo). Si pones una, pon también otra ruta.

**La técnica: soltar la dirección en el aire.** El motor sólo reescribe la
velocidad horizontal mientras haya una dirección pulsada. En el aire esa
reescritura vale la mitad (45 px/s en lugar de 90). Por tanto, **soltar** la
tecla de dirección justo después de despegar conserva los 90 px/s de la carrera
y llega casi el doble de lejos. Manteniéndola pulsada se avanza más despacio.

Es contraintuitivo y no está señalizado en ninguna parte del juego. Cuenta con
que un alumno que juegue tu nivel por primera vez **no** la conoce.

> **Aviso sobre `grade_stage.py`.** El calificador usa la fórmula analítica, que
> describe la técnica de soltar la dirección, no la natural. Etiqueta «cómodo»
> un hueco de 4 baldosas que con entrada natural es imposible, y su grafo de
> transitabilidad supone además un salto aéreo que el motor no tiene. Aprobar
> geometría no garantiza que el nivel se pueda pasar: **hay que jugarlo**.
> Detalle y medición en `KNOWN_GAPS.md`, GAP-024.

### 1.4 Reglas de colocación de enemigos

1. **Presentar antes de exigir.** El primer encuentro con un tipo de enemigo
   debe ocurrir en un tramo sin otras amenazas: el jugador lo ve actuar antes
   de tener que esquivarlo.
2. **Un peligro a la vez.** Si hay un tirador estático, el tramo no tiene
   también foso y caminante agresivo. Dos amenazas simultáneas solo al final
   del nivel, como examen.
3. **El caminante patrulla el suelo, el volador ocupa el aire, el tirador
   cubre el fondo.** Si las tres alturas están pobladas, el jugador no tiene
   dónde estar. Dejar siempre un carril razonablemente seguro.
4. **Distancias de detección coherentes con la unidad del curso.** Un nivel
   que enseña la Unidad II usa distancias visibles: el cono de detección se
   nota. Un nivel de la Unidad IX usa clasificación: la conducta cambia en
   patrones legibles.
5. **Los enemigos no bloquean checkpoints ni portales.** Nunca colocar un
   spawn que obligue a pelear para alcanzar un descanso: el jugador debe poder
   elegir pelear o pasar.

### 1.5 Vocabulario de objetos disponible (resumen de `06_TMX_SPEC.md`)

`PlayerSpawn`, `EnemySpawn` (con `enemy_type`, `waypoints`), `Checkpoint`,
`Portal`/`NextTrigger`, `HazardZone` (daño 0.25), `CameraLock` (lock_x / lock_y),
`OneWay` (plataformas de un sentido), `Solid`/`Platform` (colisión),
`MessageTrigger` (mensajes didácticos), `BossSpawn`, decoración en capas
`Terrain_Detail` y `FG_Overlay`. Los niveles de jefe requieren además
`BossSpawn` + `CameraLock` total y **no** llevan `NextTrigger` (la salida la
emite la secuencia de derrota del jefe).

---

## 2. Plantilla de diseño de un nivel

Antes de abrir Tiled, completar esta ficha (es el mínimo que debe quedar por
escrito en el README del stage):

```text
NIVEL:        [id y nombre]
CONCEPTO:     [unidad del curso que enseña]
DIFICULTAD:   [1-10] — y respecto a qué nivel vecino
DIMENSIONES:  [ancho × alto en tiles] = [px]
DURACIÓN:     [tiempo límite] — y justificación (2× limpieza)
ENEMIGOS:     [tipo] × [cantidad] — [qué rol juega cada uno en el tramo]
PELIGROS:     [zonas de daño, fosos, elementos de una sola solución]
CHECKPOINTS:  [posiciones aproximadas, en px de avance]
SOLUCIONES:   [qué tramo ofrece dos rutas y cuáles son]
ACADÉMICO:    [qué API del framework lo implementa y dónde]
```

---

## 3. Fichas de niveles de travesía

### 3.0 Stage 0 — El umbral (campo de calibración)

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`stage0.tmx`) |
| Concepto | Todo el framework a la vez, en orden de temario |
| Dificultad | 1/10 (referencia del calificador: 130/130) |
| Dimensiones | 100 × 38 tiles = **1600 × 608 px** (suelo en y=480) |
| Duración | Sin límite (didáctico); ~3–4 min de lectura natural |
| Enemigos | 1 caminante (primer encuentro, tramo B); el resto son obstáculos: liana, plataformas de un sentido, llave/puerta, foso con dos rutas, bloques rítmicos, viento, tirolesa |
| Checkpoints | Uno antes de cada bloque difícil (zonas C, D/E, F/G) |
| Reglas de la casa | Mensaje didáctico por cada sistema; modo depuración F1; dos soluciones en el foso |

**Lección:** el 0 es la plantilla de todo lo demás. Todo nivel de estudiante
debería copiar su esqueleto: presentar cada mecánica con un mensaje, crecer en
complejidad, y reintentar sin castigo.

### 3.1 Stage 1-1 — La Entrada

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`stage1_1.tmx`) |
| Concepto | Unidad III (patrullas en Bézier) + Unidad VI (parallax) |
| Dificultad | 1/10 — el salón de llegada |
| Dimensiones | 240 × 40 tiles = **3840 × 640 px** (el más largo del juego, ~5 pantallas) |
| Duración | 180 s |
| Enemigos | `WalkerInsect` × 6 (patrulla del sendero), `FlyingBird` × 3 (ondas senoidales), `ShooterFrog` × 2 (en rocas, alcance medio) |
| Peligros | Ningún foso — el castigo es el contacto. Pendientes suaves escalonadas |
| Checkpoints | 1, a la mitad (tras el tramo más angosto) |
| Reglas | Caídas de un solo sentido (no se puede volver); canopea como FG_Overlay |

**Composición recomendada:** insectos en tramos pares, pájaros en los cruces
de pantalla, ranas en los dos únicos tramos anchos. La primera rana debe estar
en un tramo sin caminantes (regla 1.4.1).

### 3.2 Stage 1-2 — La Soda

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`stage1_2_la_soda.tmx`) |
| Concepto | Unidad V (iluminación por color: cocina cálida vs. sala fría) |
| Dificultad | 2/10 |
| Dimensiones | 48 × 38 tiles = **768 × 608 px** (el más corto: una pantalla y media) |
| Duración | 150 s |
| Enemigos | `WalkerRaton` × 4 (rápidos, patrulla), `FlyingCucaracha` × 5 (vuelo errático en senoide, ocupan el aire), `ShooterCocinero` × 1 (detrás del mostrador) |
| Peligros | HazardZone de bandejas en el mostrador (0.25); media puerta hacia la cocina |
| Checkpoints | 1, tras la sala principal |
| Reglas | Dos pisos: nivel bajo (mesas) y entrepiso (estantería de cocina) conectados por plataforma de un sentido; piso ajedrezado |

**Composición recomendada:** el volumen está en el aire (cucarachas), el ritmo
en el suelo (ratones), el miedo en el fondo (cocinero). El cocinero es la
primera amenaza de "tercer carril": su tramo debe estar despejado de ratones.

### 3.3 Stage 1-3 — Las Aulas

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`stage1_3_las_aulas.tmx`) |
| Concepto | Unidad VIII (umbral: polvo de tiza brillante vs. sombra de raíces) + Unidad VI (puertas con ease_out_bounce) |
| Dificultad | 3/10 — examen de la Zona 1 |
| Dimensiones | 200 × 38 tiles = **3200 × 608 px** (~4 pantallas) |
| Duración | 150 s |
| Enemigos | `WalkerEstudiante` × 5 (corredor y salones), `FlyingNotebook` × 3 (Bézier), `ShooterTiza` × 2 (extremos de pizarrones) |
| Peligros | Púas embebidas en las raíces (solo visibles con atención); pizarrón checkpoint |
| Checkpoints | 1 — el pizarrón checkpoint (animación de tiza) |
| Reglas | Tres salones laterales accesibles con ítems/peligros; el salón 2 tiene el easter egg del pizarrón |

**Composición recomendada:** estudiantes en el corredor (ritmo constante),
cuadernos dentro de los salones (curvas que "corrigen"), tiza en los dos
extremos del corredor (amenaza de fondo). El tramo final combina los tres por
primera vez — es el examen que prepara el jefe del venado.

### 3.4 Stage 2-1 — Las Oficinas (implementado) / La Planicie (referencia)

> **Nota de realidad.** El mapa implementado en la ranura 2-1 es el de las
> oficinas del datacenter (`stage2_1_oficinas.tmx`, `STAGE 2-1 - OFICINAS`).
> El diseño de referencia `16_WORLD_DESIGN.md` coloca la planicie abierta en
> esta ranura y las oficinas en 2-3. La ficha de abajo describe lo implementado;
> la composición de la planicie canónica se incluye al pie para quien reconstruya
> la zona.

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`stage2_1_oficinas.tmx`) |
| Concepto | Unidad VII (Canny como "visión de cableado") + Unidad VIII (conteo de servidores) |
| Dificultad | 4/10 — primer nivel de la Zona 2, re-baseline post-jefe |
| Dimensiones | 200 × 38 tiles = **3200 × 608 px** |
| Duración | 150 s |
| Enemigos | `WalkerTerciopelo` × 7 (patrulla agresiva entre cubículos), `ShooterVenomoLargo` × 3 (largo alcance tras particiones), `FlyingTerciovolador` × 2 (sobre la altura de las particiones) |
| Peligros | HazardZone donde se agrupan las serpientes (0.25); particiones de vidrio (visuales, sin colisión — atraviesan) |
| Checkpoints | 2: mitad del mar de cubículos y puerta de la sala de servidores |
| Reglas | Los LED rojos parpadean sincronizados (lenguaje de peligro); el cableado es FG_Overlay |

**Composición recomendada:** terciopelos como "empleados del turno": 2 en cada
calle de cubículos, 1 en el cruce central. Los venomolargo definen "no te
quedes quieto"; los terciovoladores solo en el último tercio. La combinación
total se reserva para el tramo previo al segundo checkpoint.

**[REFERENCIA] Si se reconstruye la Planicie (2-1 canónico):** 480 px planos,
`WalkerSerpientePequena` × 6 (rápidos), `ShooterSerpienteArbol` × 3 (en postes
de la cerca), `FlyingBoa` × 2; alambre de púas a la altura de la rodilla (hay
que agacharse); calima térmica como tint animado (Unidad V); 160 s; 1
checkpoint tras la cerca.

### 3.5 Stage 2-2 — Entrada y Antenas

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`stage2_2.tmx`) |
| Concepto | Unidad III (patrullas B-Spline alrededor de las antenas) + Unidad IV (scroll vertical con CameraLock) |
| Dificultad | 5/10 |
| Dimensiones | 120 × 50 tiles = **1920 × 800 px** (el único con scroll vertical real) |
| Duración | 170 s |
| Enemigos | `WalkerGuardia` × 2 (garita), `FlyingAntena` × 4 (patrulla orbital de antenas), `ShooterSerpiente` × 3 (plataformas de azotea) |
| Peligros | Caída libre en la sección vertical (un error de salto es caro); escalera de plataformas |
| Checkpoints | 1, al pie de la escalera (antes del bloque vertical) |
| Reglas | CameraLock con lock_x=true, lock_y=false al llegar a la escalera; la sección horizontal es ancha (320 px), la vertical es una cadena de plataformas |

**Composición recomendada:** la sección baja (estacionamiento) es despejada —
solo los 2 guardias — porque el castigo de la sección vertical ya es alto. Las
antenas concentran los voladores: 2 en la base, 2 en la azotea. Los tiradores
cubren los dos saltos más largos de la escalera.

### 3.6 Stage 3-1 — La Entrada de Piedra

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`stage3_1_la_entrada_de_piedra.tmx`) |
| Concepto | Unidad VI (losas que se encienden en secuencia al pisarlas) + Unidad V (cambio HSL de piedra con las nubes) |
| Dificultad | 6/10 — el cielo es el techo |
| Dimensiones | 100 × 14 tiles = **1600 × 224 px** (bajo y expuesto: un pasillo al aire libre) |
| Duración | 160 s |
| Enemigos | `WalkerGarza` × 4 (a pie, dignas), `FlyingHalcon` × 4 (rápidos, picado), `ShooterQuetzal` × 2 (sobre los arcos) |
| Peligros | Sin cobertura: los picados llegan de cualquier parte; jardineras como cubierta (plataformas de un sentido) |
| Checkpoints | 1, tras el primer tercio |
| Reglas | Los arcos son FG_Overlay; la altura total es mínima (224 px) para forzar la lectura de los picados |

**Composición recomendada:** este nivel enseña a mirar el cielo. Garzas en el
suelo como falsa calma, halcones que anuncian el picado con su sombra, quetzales
en los dos arcos centrales. La regla de oro: **los halcones nunca picotean en
el mismo tramo que las garzas** — el jugador aprende a distinguir las dos
amenazas antes de enfrentarlas juntas.

### 3.7 Stage 3-2 — El Hall

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`hall.tmx`) |
| Concepto | Unidad VIII (watershed: tres zonas del hall con spawns distintos) + Unidad IV (5 capas: la pila más compleja del juego) |
| Dificultad | 7/10 |
| Dimensiones | 68 × 38 tiles = **1088 × 608 px** (~1.4 pantallas pero con balcones: más metros que los que anuncia el ancho) |
| Duración | 170 s |
| Enemigos | `WalkerPalom` × 5 (suelo, lentas, hitbox grande), `FlyingHalcon` × 6 (aéreas, desde la altura del techo), `ShooterBuitre` × 2 (en balcones) |
| Peligros | Claraboyas que marcan la posición (luz sobre el jugador); techos indestructibles (los proyectiles rebotan) |
| Checkpoints | 1, en el centro (cambio de zona del watershed) |
| Reglas | Dos escaleras a los balcones; los balcones son plataformas sólidas |

**Composición recomendada:** por zonas del watershed: zona de entrada (2
palomas + 2 halcones), zona central (1 paloma + 2 halcones + 1 buitre), zona de
balcones (2 palomas + 2 halcones + 1 buitre). El jugador debe leer la zona para
saber qué va a venir — ese es el concepto de la Unidad VIII.

### 3.8 Stage 3-3 — El Patio

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`stage3_3_el_patio.tmx`) |
| Concepto | Unidad VII (gaussian_blur del cielo: nublado reduce agresión aérea) + Unidad III (fuente en Catmull-Rom) |
| Dificultad | 8/10 — el examen de la Zona 3 |
| Dimensiones | 60 × 38 tiles = **960 × 608 px** (corto pero denso) |
| Duración | 145 s (el límite más ajustado del juego) |
| Enemigos | `WalkerPalom` × 3, `FlyingHalcon` × 5 (detectan a ancho completo de patio), `ShooterQuetzal` × 3 (desde alféizares) |
| Peligros | Es un claustro: tres muros; jardineras para agacharse; la fuente cura 0.25 (una vez por activación) |
| Checkpoints | 1, a la entrada |
| Reglas | El cielo nublado baja la agresividad de los halcones (mecánica viva de la Unidad VII) |

**Composición recomendada:** la fuente es el centro del diseño: el jugador
debe ganarse el camino hasta ella (curar) y salir (ser perseguido). Los
quetzales en los alféizares convierten el centro del patio en zona de fuego
cruzado; las jardineras son el único refugio. Es el primer nivel donde el
jugador decide **cuándo** curar — la tensión es de decisión, no de reflejos.

---

## 4. Fichas de jefes

### 4.0 Protocolo común de arena (todos los jefes)

| Elemento | Regla |
|---|---|
| Arena | `BossSpawn` + `CameraLock` (lock_x=true, lock_y=true) |
| Reloj | Oculto al entrar; sin límite de tiempo |
| Salida | Sin `NextTrigger`: la derrota del jefe emite `STAGE_COMPLETE` |
| HUD | Barra de vida del jefe + nombre + indicador de fase `[P1]`… |
| Transición de fase | Invulnerable durante 2–3 s, `BOSS_PHASE_CHANGED`, barra recargada |
| Dejado al morir | Icono de **Fragmento de Reliquia** (asta, espiral, máscara, llama) |

### 4.1 Stage 1-4 — El Venado Sagrado (La Residencia)

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`boss_venado.tmx`) |
| Dificultad | 4/10 (12 corazones, 2 fases) — primer jefe: perdona |
| Dimensiones | 205 × 38 tiles = **3280 × 608 px** (mapa amplio; la arena de diseño de referencia es fija 320×224) |
| Arena de referencia | 3 plataformas de un sentido (X=48/Y=160, X=136/Y=144, X=224/Y=160); arco de lianas por donde entra |

**Fase 1 — "El Bosque Duerme" (12→6 corazones).** Deriva en senoide (amplitud
40 px, 0.4 Hz, 60 px/s). Patrones: `STOMP` (si jugador < 96 px; onda 96 px en
suelo, 1.0), `CHARGE` (220 px/s, 0.75), `VINE_TOSS` (cada 8 s, Bézier a
posición predicha, 0.5). Cooldowns: 3 s / 6 s / 8 s.

**Fase 2 — "El Bosque Despierta" (6→0).** Ruta figura-8 en Bézier, ×1.5 de
velocidad. Patrones nuevos: `VINE_SWEEP` (cada 5 s, hitbox de piso completo
320×24, saltar), `MUSHROOM_SPORE` (cada 10 s, 3 proyectiles en abanico, 0.25),
`CHARGE` más rápido (280 px/s). Efecto: parpadeo sobel al bajar de 3 corazones.

**Consejos de diseño:**
- El jefe **nunca esquiva hacia la plataforma central**: el jugador que usa las
  plataformas debe sentirse recompensado (el CHARGE no llega a la plataforma alta).
- La fase 2 castiga la esquiva pasiva: el VINE_SWEEP obliga a saltar, los
  spores obligan a moverse lateralmente, la figura-8 impide predecir por
  posición fija. La dificultad sube por **decisión**, no por daño.
- **Errores típicos:** poner el STOMP sin telegrafiar; hacer la figura-8
  demasiado rápida (el jugador no puede acercarse a atacar). Ajuste: si la fase
  2 mata más de 3 veces al jugador medio, bajar el multiplicador a 1.3×.

### 4.2 Stage 2-4 — El Rey Terciopelo (El Datacenter)

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`boss_rey.tmx`) — diseño **[REFERENCIA]** en `17_BOSS_SPEC.md` |
| Dificultad | 7/10 (15 corazones, 3 fases) |
| Dimensiones | 70 × 37 tiles = **1120 × 592 px**; arena de referencia 320×224 con racks como paredes, 3 rejillas (HazardZone 0.25, 2 s cada 5 s) y una plataforma baja |

**Fase 1 — "La Marioneta" (15→10).** Caminata errática (Catmull-Rom por 4
puntos, 50 px/s). Patrones: `VENOM_SPIT` (si jugador < 200 px, 0.5), `SERPENT_CARPET`
(cada 10 s: 6 serpientes pequeñas, 0.25), `BODY_SLAM` (si jugador < 64 px,
lurge 80 px, 1.0).

**Fase 2 — "La División" (10→4).** El cuerpo se parte en dos sub-jefes
`ReyMetad` (3 corazones cada uno) que coordinan: uno ataca mientras el otro se
reposiciona. Contacto 0.5.

**Fase 3 — "El Frenesí" (4→0).** Se reensambla ×1.25 de tamaño, persecución
directa a 130 px/s. Patrones: `VENOM_BURST` (cada 6 s, 5 globos en abanico de
30°, 0.25), `SERPENT_WAVE` (cada 12 s, 12 serpientes por el suelo, 3 s),
`LUNGE` (350 px/s, 160 px, 1.25, cooldown 8 s). Subtipos AGGRESSIVE / DISPERSED
/ DEFENSIVE que alternan cada 8–15 s (mecánica de clasificación de la Unidad IX).

**Consejos de diseño:**
- La fase 2 enseña la gestión de dos frentes: **nunca** dejar que ambos
  ReyMetad tengan VENOM_SPIT a la vez en el mismo bando — si el jugador puede
  separarlos (uno a cada lado), gana lectura y merece ganar.
- El SERPENT_WAVE debe llegar cuando el jugador ya ha aprendido a leer los
  subtipos: es el examen de la Unidad IX.
- **Errores típicos:** carpet con demasiadas serpientes en fase 1 (más de 6
  satura el rendimiento y el jugador); LUNGE sin telegrafía (a 350 px/s no se
  esquiva por reflejo — necesita el aviso). Ajuste: subir el intervalo de
  subtipo de 8 a 10 s si la lectura resulta imposible.

### 4.3 Stage 3-4 — El Gavilán Camionero Mascarero (El Bungaló)

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`stage3_4_boss_gavilan.tmx`) |
| Dificultad | 8/10 (14 corazones, 3 fases) |
| Dimensiones | 102 × 38 tiles = **1632 × 608 px**; arena de referencia 320×224 con vigas de madera a 3 alturas (baja y=192, media y=152, alta y=112) y claraboya por donde entra/sale |

**Fase 1 — "El Vuelo Circular" (14→9).** Órbita circular (radio 80 px, 0.6 rad/s,
~10 s/vuelta). Patrones: `DIVE_BOMB` (cada 6 s, 300 px/s, 0.75), `FEATHER_TOSS`
(cada 8 s, 4 plumas cardinales, 0.25), `ORBIT_SHRINK` (a 11 corazones: radio 48 px).
Efecto: iridiscencia HSV (rotación de tono +5°/s).

**Fase 2 — "El Ojo de la Máscara" (9→4).** Hover fijo en (160, 48); todo es
descendente. Patrones: `FEATHER_STORM` (cada 7 s, 8 plumas en abanico hacia
abajo, 3 s de duración, 0.25), `MASK_BEAM` (cada 10 s, rayo vertical de 24 px,
instántaneo, 1.0, con flash de aviso de 0.5 s), `WIND_BLAST` (cada 12 s,
empuja 96 px, sin daño). Efecto: gaussian_blur creciente sobre la máscara.

**Fase 3 — "La Máscara Sin Control" (4→0).** Catmull-Rom errático por 6 puntos.
Patrones: `MASK_FRAGMENT_STORM` (cada 8 s, 6 fragmentos que rebotan una vez en
las paredes, 0.5), `RAPID_DIVE` (cada 4 s, dos picados seguidos con 0.5 s de
separación), `FULL_FEATHER_STORM` (cada 15 s, 16 plumas en 5 s). Efecto: canny
alpha=100 — la máscara rota dibuja bordes erráticos.

**Consejos de diseño:**
- Las vigas son el refugio natural del DIVE_BOMB: el picado no atraviesa
  plataformas. El jugador que lee el patrón se sube; el que esquiva en el suelo
  sufre. Ese es el diseño de la fase 1.
- La fase 2 es un jefe estático que gana por **acumulación**: el MASK_BEAM es
  el único castigo duro (1.0) y está telegrafiado con 0.5 s — el resto es
  desgaste. La dificultad real está en el suelo cubierto de plumas.
- **Errores típicos:** MASK_BEAM sin aviso (mata sin lectura); viento en la
  dirección equivocada (empujar contra el balcón es castigo doble — el viento
  debe empujar hacia el centro). Ajuste: si la fase 2 aburre, acortar el ciclo
  de storm a 6 s en vez de subir el daño.

### 4.4 Stage 4-2 — El Gran Shaman Paburu (El Cementerio Sagrado)

| Campo | Valor |
|---|---|
| Estado | **IMPLEMENTADO** (`boss_paburu.tmx`) — diseño **[REFERENCIA]** en `17_BOSS_SPEC.md` |
| Dificultad | 9–10/10 (20 corazones, 4 formas) |
| Dimensiones | 50 × 38 tiles = **800 × 608 px** (una pantalla: la arena más contenida del juego); arena de referencia 320×224 plana con 4 pilares de llama (HazardZone 0.25 en la base) y caras rituales grabadas |

**Forma 1 — "La Cabeza de Piedra" (20→15).** Estacionaria, inclinación ±8 px.
Patrones: `STONE_SPIT` (cada 4 s, 3 proyectiles en arco 15°, 0.5), `EYE_BEAM`
(cada 8 s, rayo horizontal de 8 px a 200 px/s, 1.0), `GROUND_SLAM` (cada 10 s,
screen shake + 3 fisuras de 24 px en posiciones aleatorias, 0.5, 2 s).
Transición: la cabeza se agrieta y los tres espíritus fluyen hacia la Forma 2.

**Forma 2 — "La Máscara Espectral" (15→10).** Deriva senoidal (amplitud 20 px,
0.3 Hz) a 40 px/s. **Punto de daño: solo la máscara** (hurtbox 40×40) — el
cuerpo es invulnerable. Patrones: `SPIRIT_WAVE` (cada 5 s, onda por el suelo o
por el techo, alterna; agacharse o saltar, 0.5), `SUMMON_ECHOES` (cada 12 s,
ecos de los tres jefes al 50% de daño, un ataque cada uno), `MASK_PULSE`
(cada 7 s, onda circular < 80 px, 0.75).

**Forma 3 — "La Reliquia" (10→5).** La pepita y la perla vuelan hacia Paburu;
**se elige al azar 3A o 3B** (semilla por partida).
- **3A — La Pepita (esfera dorada, ofensiva):** persecución a 120 px/s con
  jitter de ±30° cada 0.5 s; contacto 1.0. `GOLD_RUSH` (240 px/s por 0.8 s cada
  5 s), `GOLD_BURST` (8 orbes radiales a múltiplos de 1 corazón, 0.25),
  `RICOCHET` (rebote vectorial en paredes — la ilustración viva de la Unidad II).
- **3B — La Perla (esfera negra, defensiva):** órbita de radio 64 px a 0.3 rad/s;
  contacto 0.5. `DARK_FIELD` (zonas lentas 48×48, velocidad a la mitad, hasta 3
  a la vez, 8 s), `PEARL_VOLLEY` (3 orbes lentos en abanico, 0.5, persisten 6 s),
  `PULL` (cada 10 s, gravedad hacia la esfera por 1 s — la ilustración de la
  Unidad II).

**Forma 4 — "El Espíritu del Shaman" (5→0).** Flota senoidal (amplitud 32 px,
0.2 Hz) a 20 px/s; manos alternando oro y perla. Patrones: `RELIC_SURGE`
(cada 6 s, orbes de oro rápidos + orbes negros lentos a la vez, 0.5/0.25),
`SPIRIT_FORM` (cada 10 s, intangible 1.5 s **mientras sigue atacando**),
`ANCIENT_CALL` (cada 15 s, los tres ecos a la vez por 3 s), `CONVERGENCE`
(a 2 corazones, una vez: las reliquias convergen con 2 s de telegrafía, 2.0 —
esquivable en los bordes extremos).

**Consejos de diseño:**
- La Forma 2 castiga la memoria (los ecos repiten lo aprendido) y la Forma 3
  castiga el estilo (3A castiga al pasivo, 3B castiga al agresivo). Eso es
  deliberado: el jugador debe adaptar su estilo, no solo sus reflejos.
- El CONVERGENCE es el único golpe de 2.0 corazones del juego: debe sentirse
  inevitable la primera vez y esquivable la segunda.
- **Errores típicos:** dar a la Forma 2 un daño alto en el cuerpo (mata la
  lección del punto de daño); hacer 3B más corta de lo que es (la perla es la
  forma de "paciencia": si el jugador se aburre, es que el diseño está bien).

---

## 5. El cementerio sin jefe: Stage 4-1 — La Entrada al Cementerio

| Campo | Valor |
|---|---|
| Estado | **[REFERENCIA]** (sin mapa en `assets/maps/`) |
| Dificultad | 7/10 **atmosférica** — no hay enemigos, y no debe haberlos |
| Dimensiones | ~400 px (referencia); sin límite de tiempo |
| Elementos | Cuencos de fuego (plataformas + luz por proximidad), grietas pulsantes (HazardZone 0.25 periódico), visión espectral (ataque largo: umbral 3 s que revela marcas ocultas), ecos de los tres espíritus en BG_Mid |
| Regla de oro | **No añadir enemigos.** Si el nivel aburre, se arregla con más marcas
  ocultas, no con serpientes. La tensión ya está: es el silencio antes del juez |

---

## 6. Tabla resumen de composición

| Nivel | Dificultad | Dim. reales (px) | Enemigos (tipo × cantidad) | Límite |
|---|---|---|---|---|
| 0 Umbral | 1 | 1600×608 | walker × 1 + obstáculos | — |
| 1-1 Entrada | 1 | 3840×640 | insecto×6, pájaro×3, rana×2 | 180 s |
| 1-2 Soda | 2 | 768×608 | ratón×4, cucaracha×5, cocinero×1 | 150 s |
| 1-3 Aulas | 3 | 3200×608 | estudiante×5, cuaderno×3, tiza×2 | 150 s |
| 1-4 Venado | 4 | 3280×608 | — (jefe 12 corazones, 2 fases) | — |
| 2-1 Oficinas | 4 | 3200×608 | terciopelo×7, venomolargo×3, terciovolador×2 | 150 s |
| 2-2 Antenas | 5 | 1920×800 | guardia×2, antena×4, serpiente×3 | 170 s |
| 2-3 Oficinas [REF] | 6 | 480 | — (canon: 7/3/2 sobre 2-1) | 150 s |
| 2-4 Rey | 7 | 1120×592 | — (jefe 15 corazones, 3 fases) | — |
| 3-1 Piedra | 6 | 1600×224 | garza×4, halcón×4, quetzal×2 | 160 s |
| 3-2 Hall | 7 | 1088×608 | paloma×5, halcón×6, buitre×2 | 170 s |
| 3-3 Patio | 8 | 960×608 | paloma×3, halcón×5, quetzal×3 | 145 s |
| 3-4 Gavilán | 8 | 1632×608 | — (jefe 14 corazones, 3 fases) | — |
| 4-1 Cementerio | 7 atm | ~400 [REF] | ninguno (regla de oro) | — |
| 4-2 Paburu | 9–10 | 800×608 | — (jefe 20 corazones, 4 formas) | — |

---

## 7. Composición de enemigos: guía rápida de arquetipos

| Arquetipo | HP / Daño | Rol en el nivel | Cuándo usarlo |
|---|---|---|---|
| `Walker` | 2 / 0.5 | Ritmo del suelo, empuje constante | Primer nivel de cada zona |
| `Flying` | 1 / 0.5 | Ocupar el aire, forzar movimiento vertical | En tramos anchos o con doble altura |
| `Shooter` | 2 / 1.0 | Amenaza de fondo, control de zonas | En tramos con cubierta disponible |
| `Charger` | 3 / 1.5 | Aceleración, castigo a la quietud | Desde el nivel 2 de cada zona |
| `Archer` | 2 / 1.0 | Precisa, disparo punzante | Examen de esquiva lateral |
| `Brute` | 5 / 2.0 | Muro, lentitud con daño alto | Máximo 1 por nivel, siempre presentado antes |
| `Caster` | 3 / 1.5 | Patrones radiales, área | Niveles de las Unidades V–VII |
| `Assassin` | 2 / 2.0 | Sorpasso, ataque súbito | Solo en la Zona 3, como examen |

Regla de composición: **un arquetipo nuevo por nivel, uno de los tres tipos
máximo por escenario de estudiante**, y el tercer tipo debe ser una variante
temática del escenario (el ratón de la soda, el cuaderno del aula, el guardia
del datacenter).

---

## 8. Checklist de cierre de nivel

- [ ] Dificultad declarada y acorde al vecino (±1)
- [ ] Dimensiones del TMX escritas en el README (y verificadas con `validate_tmx.py --ci`)
- [ ] Máximo 3 tipos de enemigo; primer encuentro presentado sin otras amenazas
- [ ] Checkpoint cada 700–1200 px; nunca bloqueado por enemigos
- [ ] Ningún hueco obligatorio de más de 3 baldosas (§1.3); los de 3, con ruta alternativa o checkpoint pegado
- [ ] Ningún repecho obligatorio de más de 5 baldosas (§1.3)
- [ ] El nivel se ha **jugado** de principio a fin, no sólo calificado
- [ ] Dos soluciones en al menos un tramo
- [ ] Límite de tiempo ≈ 2× limpieza estimada
- [ ] Conteo de enemigos en pantalla ≤ 8 simultáneos
- [ ] Jefes: BossSpawn + CameraLock total + sin NextTrigger + reloj oculto
- [ ] `grade_stage.py` ≥ objetivo; paletas ≤ 16 colores

---

## 9. Documentos relacionados

- [[16_WORLD_DESIGN.md|World Design]] — la geografía y los conteos canónicos
- [[17_BOSS_SPEC.md|Boss Specification]] — el diseño fase a fase de los jefes
- [[05_ENEMY_SPEC.md|Enemy Specification]] — los arquetipos y sus reglas
- [[06_TMX_SPEC.md|TMX Specification]] — el vocabulario de objetos del mapa
- [[07_STAGE0_DESIGN.md|Diseño del Escenario 0]] — la plantilla de referencia
- [[18_ENEMY_ROSTER.md|Enemy Roster]] — el catálogo de enemigos
- [[38_STAGE_BOSS_GUIDE.md|Guía Rápida de Stages y Bosses]] — cómo construir, esta guía dice qué construir
- [[65_EL_LORE_EXTENSO.md|El Lore Extenso]] — el porqué narrativo de cada zona
