---
document_id: "LOI-LVL-4-1D"
title: "Diseño 4-1 — El Cementerio y La Cegua"
aliases: ["Diseño del Cementerio", "4-1 Design", "La Cegua"]
tags: ["level", "zona-final", "design", "folklore", "cegua"]
description: "Propuesta de diseño del 4-1: progresión ambiental estilo Magus, luna descendente, braseros, tormenta, La Cegua y lápidas de estudiantes"
source: "docs/niveles/15_DISENO_4_1_EL_CEMENTERIO.md"
---

# DISEÑO 4-1 — EL CEMENTERIO Y LA CEGUA

**Nivel:** 4-1 La Entrada al Cementerio · **Tipo:** Travesía atmosférica (sin enemigos) · **Referencia:** pelea contra Magus (Chrono Trigger)

> **La idea en una frase.** Que el fondo **pelee junto al jugador**: cada tramo
> que se avanza enciende braseros, baja la luna, sube la tormenta y acerca a las
> figuras — como el escenario de Magus que se transforma por fases mientras la
> pelea avanza. El 4-1 no es un pasillo con decoración: es **un reloj de fondo**
> donde el jugador siente que el cementerio se está despertando con él.
>
> Este documento es una **propuesta**: todo lo de aquí cabe dentro de las reglas
> obligatorias de `13_STAGE_4_1.md` (sin enemigos, visión espectral, cuencos de
> fuego, día 19:00 → 23:00) y usa solo sistemas que el motor ya tiene: clima
> (`fog`, `storm`, `rain`), partículas (`embers`, `ash`, `spores`), ciclo
> día/noche (`start_hour`/`day_length`), luz por focos, capas parallax
> (BG_Far/BG_Mid) y `HazardZone`.

---

## 1. El arco en cinco actos

El nivel se divide en **cinco actos ambientales**. Cada acto cambia cinco
cosas: los **braseros encendidos**, la **luna** (posición y tamaño), el
**clima**, el **fondo** (quién se ve) y los **peligros activos**. El jugador
lee su progreso por el fondo, no por un contador.

| Acto | Tramo | Braseros | Luna | Clima | Fondo | Peligros |
|---|---|---|---|---|---|---|
| I | La Entrada | 0/12 apagados | Alta y pequeña (~30 px) | `fog` bajo | Lápidas primeras, ecos lejanos (venado) | Ninguno |
| II | El Sendero de los Nombres | Se encienden 1–6 en secuencia | Baja un tramo (~60 px) | `fog` medio | Lápidas con nombres de estudiantes | Grietas visibles (no activas) |
| III | La Niebla que Respira | 7–9 | Baja otro tramo (~90 px) | `fog` denso + truenos lejanos | Árboles en la niebla | **Primer tramo de saltos** (grietas pulsantes) |
| IV | La Tormenta | 10–11 | Casi en el horizonte (~120 px) | `storm` + relámpagos | **La Cegua y las brujas** (aparecen con cada rayo) | Saltos exigentes, losas que ceden |
| V | El Umbral | 12/12 (el central, grande) | En el suelo del fondo, enorme (~160 px) | Silencio súbito | Cegua inmóvil y lejana; círculo de piedra al fondo | Ninguno (el silencio es el jefe) |

**La regla del acto:** entre actos solo cambia el fondo, el clima y la luz —
**no cambia el esquema de control ni se introduce una mecánica nueva**. Lo que
cambia es la **sensación de avance**: el cementerio se despierta, y el jugador
es el que lo despierta.

---

## 2. La luna como reloj (mecánica central)

La luna es la barra de vida del nivel.

- **Posición y tamaño por acto** (tabla del §1): alta-pequeña al empezar,
  abajo-enorme al terminar. Se implementa como un sprite en la capa `BG_Far`
  con dos parámetros: `offset_y` (baja con el avance) y `scale` (crece).
  Entre actos se interpola suavemente (lerp) — el cambio se ve, no se salta.
- **La luna es el día**: el nivel arranca a las 19:00 (`start_hour = "dusk"`)
  y termina a las 23:00 (`day_length = 900`). La luna **materializa** lo que el
  reloj del mundo ya está haciendo: al terminar el nivel, la luna ocupa el
  lugar donde el día estaba.
- **La luna es el guiño a Magus**: en la pelea original el fondo se transforma
  por fases con la barra del jefe; aquí la luna se transforma con el avance.
  No hace falta que baje en cada píxel — basta con que en los **cinco puntos
  de acto** esté donde el diseño dice.

Valores sugeridos (a calibrar en playtest):

| Acto | offset_y (px desde el tope) | tamaño (px) |
|---|---|---|
| I | 60 | 30 |
| II | 110 | 60 |
| III | 170 | 90 |
| IV | 230 | 120 |
| V | 300 (al borde del suelo del fondo) | 160 |

---

## 3. Los braseros que se encienden (el primer guiño Magus)

- **12 braseros** a lo largo del nivel (canónico: cuencos de fuego). El
  primero está **apagado y frío**; el último —el del umbral— es **grande y
  central**.
- Cada brasero se enciende **por proximidad y en secuencia**: al pasar junto a
  uno, se enciende y **se queda encendido** (no se apaga al retroceder). El
  sendero queda marcado de luz detrás del jugador — nunca adelante.
- Al encenderse: llama + partículas `embers` (ascuas) + una **luz puntual**
  (point light de `lighting.py`). El jugador "compra visión" con avance: la luz
  que deja detrás es la que le permite ver los peligros cuando regresa (tras
  morir).
- **Regla de diseño:** el número de braseros encendidos es la **barra de
  progreso visual** del nivel. Si un jugador pregunta "¿cuánto falta?", la
  respuesta es "cuenta los apagados".

---

## 4. La Cegua y las brujas (folklore costarricense, con respeto)

**Nota cultural.** La Cegua es una de las leyendas más conocidas de Costa Rica:
una mujer hermosa que se revela de noche en los caminos con cabeza de caballo,
apareciendo a los viajeros. Es parte del patrimonio popular del país — el mismo
espíritu con el que el juego ya usa al terciopelo o al gavilán camionero. **No
es un enemigo de combate: es una presencia.** Nunca se dibuja como caricatura,
nunca se burla de ella, y no recibe daño ni se derrota. La regla del canon:
tratar lo folclórico con la misma dignidad que lo sagrado.

**Cómo aparece (progresión por acto):**

| Acto | La Cegua | Las brujas |
|---|---|---|
| I–II | No visible (solo un susurro opcional lejano, audio bajo) | No visible |
| III | Silueta entre dos árboles de niebla (BG_Mid, a media distancia) | 1 silueta cruza el fondo en vuelo (BG_Mid, lenta) |
| IV | **Se ve con cada relámpago**: la silueta aparece un instante, más cerca que en el III, montada, mirando al sendero | 2–3 cruzan con el relámpago; se quedan un segundo en la rama de un árbol |
| V | Inmóvil y lejana, al borde del círculo de piedra; mira hacia el portal. Al cruzar al 4-2, **no la vemos más** | Siluetas posadas en los árboles, quietas |

- **Implementación:** sprites estáticos en `BG_Mid` (como los ecos canónicos
  de los espíritus) — **no son entidades, no tienen colisión ni IA**. El
  motor ya pinta capas de fondo con parallax: el trabajo es de timing, no de
  código de enemigos.
- **El relámpago como linterna:** la Cegua solo se ve en el destello del rayo
  (ver §5). El jugador **elige mirar** el rayo para verla — o no mirarlo para
  no verla. Esa elección es la tensión.
- **Opción de tensión (sin daño):** si el jugador se queda quieto en un tramo
  sin braseros encendidos (oscuridad) más de ~4 s, un susurro suena y los ojos
  de la Cegua brillan en el fondo. **No hay daño ni castigo:** es recordatorio
  de seguir. La regla del nivel es que el miedo nunca cobra vida.

---

## 5. Lluvia, truenos y relámpagos (clima)

El clima cambia por acto usando el sistema que ya existe (`WeatherSystem` +
propiedad `climate` del TMX):

| Acto | climate | Partículas | Sonido |
|---|---|---|---|
| I | `fog` (bajo) | `ash` (ceniza cayendo, lenta) | Silencio + brisa |
| II | `fog` | `ash` + `spores` (esporas verdes sutiles) | Crujido de lápidas, viento |
| III | `fog` (denso) | `ash` + niebla más opaca | **Truenos lejanos** (anuncian el IV) |
| IV | `storm` | lluvia inclinada (el viento del sistema, ±50–100 px/s) | Truenos cercanos + lluvia |
| V | `clear` (silencio súbito) | sin partículas | Nada — el silencio es el jefe |

**El relámpago como mecánica de legibilidad:**

- Cada relámpago es un **destello que ilumina todo el nivel un instante**
  (subir el brillo/ambiente con un flash de ~0.4 s — el motor ya interpola
  luz; aquí se pide un pico momentáneo).
- El destello **revela**: la Cegua, las brujas, y sobre todo **los peligros del
  tramo siguiente** (grietas, losas que ceden). El jugador memoriza el tramo
  con cada rayo: es una **linterna de anticipación**.
- **Regla de diseño:** ningún peligro aparece sin que un relámpago anterior lo
  haya mostrado. Si el jugador muere en un tramo de saltos, la culpa es del
  diseño, no de la oscuridad.
- El trueno suena con **retardo** tras el destello (efecto clásico): el diseño
  usa ese retardo como metrónomo de la tensión.

---

## 6. Hazards y tramos de salto (los "hazard tiles")

El nivel tiene **dos tramos de salto obligatorios** (Acto III y Acto IV), todos
construidos con el vocabulario del TMX + una propuesta nueva:

1. **Grietas pulsantes (canónicas):** `HazardZone` de 0.25 con pulso visible —
   se salta cuando el pulso "respira" hacia afuera. En el Acto III son la
   presentación; en el IV están combinadas con lluvia.
2. **Losas que ceden (propuesta nueva):** losas de piedra que aguantan ~1 s
   cuando se pisan y luego se hunden (hazard temporal — reutiliza `HazardZone`
   activado por pisada o un objeto `OneWay` con temporizador). El jugador debe
   **correr sin pararse** — es el único "reflejo" del nivel.
3. **Lápidas derrumbadas como plataformas:** saltos entre bloques de lápida
   rota; son `Solid`/`OneWay` normales. El diseño de salto usa las lápidas como
   peldaños — el terreno del cementerio es el terreno de juego.
4. **Regla de los dos peligros:** nunca dos peligros simultáneos sin que el
   relámpago los haya mostrado (§5). En el Acto IV, la lluvia y el viento
   "empujan" el salto (el viento de la tormenta desplaza al jugador: los
   saltos se calculan con el viento a favor del diseño — pequeño, nunca contra
   la jugabilidad).

**Mapa de saltos sugerido (Actos III–IV):**

```
   [ÁRBOL DE NIEBLA]      [ÁRBOL DE NIEBLA]
     │ silueta Cegua         │
 ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐   ← losas que ceden (pisar y seguir)
 SPAWN ── grieta ── grieta ── grieta ── grieta ── PORTAL
        (salto simple)   (salto doble, se ve con el rayo)
```

---

## 7. Las lápidas con los nombres de los estudiantes

- **Qué:** las lápidas del sendero llevan **inscritos los nombres de los
  estudiantes del curso**. El profesor carga la lista real (los nombres van en
  el TMX como texto de las lápidas o en un JSON del stage; se dejan
  `[NOMBRE]` de placeholder en la entrega).
- **Reglas de respeto (obligatorias):**
  - Inscripciones dignas: nombre + (opcional) un descriptor neutral del
    proyecto ("Cómputo Gráfico", "Procesamiento de Imágenes", curso/año).
  - **Sin humor cruel**: nada de "aquí yace el que no compiló". El humor
    académico solo si el profesor lo autoriza explícitamente y es amable.
  - Los nombres son **todos** los estudiantes, sin distinción de nota — la
    inscripción es un honor, no un ranking.
- **Interacción opcional:** al acercarse a una lápida, un `MessageTrigger`
  muestra un **epitafio corto** (1 línea). Opciones de tono:
  - Neutral: «Estudiante de la promoción 2026.»
  - Juego de palabras del curso: «Aprobó el examen final.» / «Su pelea duró
    más que el compilado.»
  - Misterioso (coherente con el nivel): «No fue el último en despertar.»
- **La lápida central** (la más grande, en el Acto V) no lleva nombre: lleva
  la inscripción **«LA PRUEBA»** — es la puerta del 4-2.

---

## 8. La visión espectral (integración con la mecánica existente)

El 4-1 ya tiene visión de umbral (Unidad VIII): al presionar el ataque largo,
la pantalla se filtra y se revelan **marcas ocultas**. Propuesta de uso en
este diseño:

- Las marcas ocultas son **huellas de pezuña** — las dejó La Cegua.
- En el Acto III y IV, las marcas revelan **dónde están las losas que ceden**
  y **por dónde saltar las grietas** (la visión espectral es la "segunda
  linterna" del nivel, complementaria al relámpago).
- **Regla:** con visión espectral, el tramo de saltos del Acto IV se vuelve
  trivial — es la recompensa de la observación (el jugador que mira, no sufre).

---

## 9. El guion ambiental completo (la sensación buscada)

```
ACTO I — ENTRADA (19:00)          Sin música. Ceniza. La luna alta, fría.
                                   Un susurro lejano. Nada más.
ACTO II — LOS NOMBRES             Los braseros se encienden a tu paso.
                                   Ves tu nombre y los de tus compañeros.
                                   La luna bajó un tramo. Viento.
ACTO III — LA NIEBLA QUE RESPIRA  Truenos lejanos. Árboles con siluetas.
                                   Las grietas respiran. Primeros saltos.
                                   Una figura entre dos árboles: no te ha
                                   visto — todavía.
ACTO IV — LA TORMENTA             Lluvia y relámpagos. Cada rayo te muestra
                                   el peligro siguiente... y a la Cegua,
                                   más cerca que antes. Las brujas cruzan.
                                   Los saltos: corriendo, sin pararse.
ACTO V — EL UMBRAL                La tormenta cesa. Silencio. La luna toca
                                   el suelo del fondo, enorme.
                                   Los 12 braseros arden. La Cegua mira
                                   desde lejos, inmóvil. La lápida central
                                   dice «LA PRUEBA».
                                   Los ecos del venado, el Rey y el Gavilán
                                   se detienen. El 4-2 comienza.
```

---

## 10. Implementación con los sistemas del motor (resumen)

| Idea | Cómo se hace |
|---|---|
| Clima por acto | Propiedad `climate` del TMX + `WeatherSystem.set_climate()` al cruzar los umbrales de acto (`fog` → `storm` → `clear`) |
| Partículas | `AmbientParticles`: `ash` (actos I–III), `spores` (II), `embers` en cada brasero encendido |
| Luna descendente | Sprite en `BG_Far` con offset_y + scale interpolados por acto (lerp) |
| Braseros | `OneWay`/decorativo + luz puntual (`lighting.py`) + `embers`; secuencia por proximidad en el código del stage |
| Relámpago | Flash de brillo de ~0.4 s (subida momentánea de ambiente) + trueno con retardo; activa la visibilidad de las siluetas |
| La Cegua y brujas | Sprites estáticos en `BG_Mid` con visibilidad por acto y por relámpago (sin colisión, sin IA) |
| Lápidas | Capa `Terrain_Detail` + texto en TMX (nombres reales del profesor); `MessageTrigger` opcional en las grandes |
| Grietas y losas | `HazardZone` (grietas pulsantes) + losas que ceden (OneWay con temporizador o HazardZone por pisada — propuesta nueva) |
| Visión espectral | Ya existe (ataque largo): revela huellas de pezuña y la ruta de saltos |
| Día/noche | `start_hour = "dusk"` (19:00), `day_length = 900` → 23:00 (la luna lo materializa) |
| Checkpoints | 1 obligatorio (mitad, tras el Acto II) — los braseros ya cumplen de marcadores |

---

## 11. Checklist de la propuesta

Construida entera. Cada casilla la defiende una prueba de `tests/test_stage4_1.py`
(84 en total); lo que se cambió respecto a esta propuesta está en el §0 de la
ficha, `13_STAGE_4_1.md`.

> **El nivel es vertical (AUD-225).** Esta propuesta lo describe como un corredor
> horizontal de cinco actos. Jugado no funcionaba —siete fosos mortales y cinco
> zonas de daño invisibles en una «travesía atmosférica»— y se rehízo como un
> **descenso**: un pozo de 60 × 240 con 44 repisas que alternan lado. Todo lo
> demás de este documento se mantiene y sólo cambia de eje: los cinco actos son
> cinco tramos de profundidad, la luna se queda arriba en el brocal en vez de
> bajar al horizonte, y los tramos de salto son tramos de caída. Lo que
> sustituye al peligro son superficies que se ven —musgo que arrastra, lodo que
> frena—, con la regla de que nada cambia el movimiento del jugador sin que se
> vea por qué.

- [x] 5 actos con sus cinco parámetros (braseros / luna / clima / fondo / peligros)
- [x] La luna en las 5 posiciones del §2 (lerp entre actos)
- [x] 12 braseros en secuencia; luz + ascuas; el último grande y central
- [x] La Cegua en siluetas de fondo, nunca en combate; visibilidad con relámpagos
- [x] Brujas cruzando el fondo en el Acto IV *(AUD-210; quietas en el V)*
- [x] Tramo exigente III (musgo que arrastra) y IV (lodo que frena + viento) —
      **sin peligro no revelado, y sin peligro mortal**: ninguno hace daño
- [x] Lápidas con nombres (placeholder `[NOMBRE]`) + lápida central «LA PRUEBA»
- [x] Clima por acto (`fog` → `storm` → silencio)
- [x] Visión espectral revelando huellas de pezuña y ruta segura
- [x] Sin enemigos (regla de oro), portal al 4-2 *(y 12 checkpoints, uno por
      brasero: el §10 dice que los braseros son los marcadores — AUD-208)*
- [x] `start_hour` = 19 y `day_length = 900` *(como número: el motor no entiende
      la cadena `dusk`)*
- [x] La opción de tensión del §4: quieto y a oscuras, susurro y ojos — **sin
      daño** *(AUD-211)*

El suelo también es del cementerio desde AUD-237. `tileset_cemetery.png` existía
y eran ocho baldosas de relleno genéricas —piedra lisa, tablones, ladrillo
rojo—, así que el nivel pintaba con el tileset del prólogo porque el suyo era
peor. Ahora la hoja se dibuja de verdad: losa de cripta, muro del pozo, lápida
en dos mitades, cruz, y el musgo y el lodo como **la misma losa con otra
superficie encima**, que es lo que hace que el jugador entienda por qué resbala.

---

## 🔗 Documentos Relacionados

- [[13_STAGE_4_1.md|Ficha 4-1]] — las reglas obligatorias que esta propuesta cumple
- [[14_BOSS_4_2.md|Jefe final 4-2]] — la puerta al otro lado del umbral
- [[67_ESPECIFICACION_DE_NIVELES_Y_JEFES.md|Especificación de Niveles]] — reglas globales
- [[65_EL_LORE_EXTENSO.md|El Lore Extenso]] — el cementerio en el canon
