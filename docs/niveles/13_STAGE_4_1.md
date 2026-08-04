---
document_id: "LOI-LVL-4-1"
title: "Nivel 4-1 — La Entrada al Cementerio"
aliases: ["Stage 4-1", "La Entrada al Cementerio"]
tags: ["level", "zona-final", "atmospheric"]
description: "Ficha de nivel: dificultad, tamaño, enemigos, objetos, día/noche y mapa sugerido"
source: "docs/niveles/13_STAGE_4_1.md"
---

# NIVEL 4-1 — LA ENTRADA AL CEMENTERIO

**Entregable:** profesorado (no se asigna a estudiantes) · **Zona:** Final — El Cementerio Sagrado · **Tipo:** Travesía atmosférica (sin enemigos)

## 0. Estado real — construido (AUD-163)

El nivel **existe y se juega**. Esta sección dice qué se construyó de verdad,
qué se cambió respecto a la ficha y por qué, para que nadie tenga que
adivinarlo leyendo el código.

| Pieza | Dónde vive |
|---|---|
| Mapa (60 × 240 — **un descenso**, generado) | `tools/generate_stage4_1.py` → `assets/maps/stage4_1/stage4_1.tmx` |
| Trazado: dónde está cada repisa, brasero y lápida | `src/stages/stage4_1/trazado.py` |
| Escena, actos, luna, rayos, brujas, oscuridad | `src/stages/stage4_1/stage4_1.py` |
| Tabla de los cinco actos | `src/stages/stage4_1/actos.py` |
| Contornos de venado, serpiente, gavilán, la Cegua y las brujas | `src/stages/stage4_1/siluetas.py` |
| Fondo del cementerio (3 capas) | `tools/generate_all_assets.py` → `assets/backgrounds/final/` |
| Pruebas (84) | `tests/test_stage4_1.py` |

**Lo que se cambió respecto a esta ficha, y por qué:**

1. **`Portal` no existe en el motor.** La ficha lo pide en «Objetos mínimos».
   La salida de un escenario es `NextTrigger`, que es lo que hay en el mapa.
   Es la misma cosa con otro nombre; lo que no se puede es escribir un tipo
   que el cargador rechaza. (La auditoría de documentación ya lo tenía
   señalado como inexistente.)
2. **`start_hour` va como número (19), no como la cadena `dusk`.** El motor
   lee la hora como `float`; `dusk` no es un valor que entienda.
3. **Las siluetas no están en la capa `BG_Mid` del TMX** sino dibujadas por el
   escenario, detrás del mapa, con el gancho `dibujar_fondo` que AUD-162 tuvo
   que añadir a `StageScene`. La capa `BG_Mid` de un TMX es de baldosas, y no
   hay arte de venado ni de gavilán en vista de fondo: un contorno dibujado es
   honesto —se lee como «una forma en la niebla», que es lo que el diseño
   pide— y no finge ser una ilustración terminada.
4. **Partículas verdes: `spores`.** Es el único efecto del motor que sale en
   verde —(150, 255, 130)— y es exactamente la «luz espectral verde» que el
   lore le pone al cementerio (§3.4). El ritmo sube con los actos.
5. **El acto V no tiene «silencio súbito» de audio**, sólo `climate = clear` y
   menos partículas. Silenciar la música por acto exigiría tocar el gestor de
   audio y no se hizo.
6. **Los nombres de las lápidas son `[NOMBRE]`.** El diseño (§7) exige que los
   cargue el profesor, que estén todos sin distinción de nota y que ninguna
   inscripción se burle de nadie. Inventar una lista sería lo contrario.

**Lo que se corrigió después (AUD-208 … AUD-211):**

> El punto 7 quedó **superado** por el rediseño de AUD-225, que aparece más
> abajo: el corredor horizontal de 300 baldosas que describe no llegó a
> entregarse, porque jugarlo destapó que el problema no era el largo sino la
> forma. Se deja escrito porque de ahí salió `trazado.py`, que sí sigue vivo, y
> porque el camino que lleva a una decisión explica la decisión.

7. **El nivel medía media pantalla por acto.** Los tramos eran de 20 baldosas
   sobre un mapa de 100, y la pantalla mide 50: en una sola vista cabían dos
   actos y medio, la luna «bajaba un tramo» dos veces sin que el jugador se
   moviera de sitio y los cinco actos se recorrían en unos diez segundos. Ahora
   son **60 baldosas por acto** (300 × 38, 4800 × 608 px) — pantalla y media
   cada uno. Las columnas de todo viven en `trazado.py`, que leen el generador
   **y** la escena: antes eran dos listas a mano y la huella de la visión
   espectral podía acabar flotando sobre una grieta sin que nada fallara.
8. **Doce puntos de reaparición, uno por brasero.** El §10 del diseño dice que
   «los braseros ya cumplen de marcadores»; ahora es literal, se vuelve al
   último fuego encendido. Con dos checkpoints sobre 300 baldosas el calificador
   avisaba de 688 px sin reaparecer (recomienda 500); ahora el tramo más largo
   es de 480 px.
9. **La música y el fondo eran de otro nivel.** El mapa pedía `bgm_zone3` y
   `background_zone = stage0`, o sea la música de la zona 3 y el castillo del
   prólogo. El Asset Bible (`docs/20_ASSET_BIBLE.md`) ya tenía asignadas las dos
   cosas a este nivel —`bgm_final_approach.wav` y `final/bg_final_*.png`— y
   estaban en el repositorio sin usar. Las tres capas del fondo, además, las
   dibujaba el generador genérico (un degradado con ruido): ahora son un
   cementerio de verdad —lápidas, cruces, verja, árboles secos y el círculo de
   piedra del acto V— con la paleta que fija el propio Asset Bible.
10. **Faltaban dos cosas de la checklist del diseño.** Las **brujas** que cruzan
    el fondo con el relámpago (§4) y el **susurro de la oscuridad**: quedarse
    quieto más de 4 s sin ningún brasero cerca enciende los ojos de la Cegua en
    el fondo y suena `sfx_environment_cemetery_silence`. Como manda el §4, no
    hay daño ni castigo — hay una prueba que lo comprueba.

**El rediseño: de pasillo a pozo (AUD-225).**

Jugado, el nivel horizontal no funcionaba. Tres defectos, y los tres se
arreglaron cambiando la forma del nivel:

11. **Tenía trampas, y la ficha las prohíbe.** Siete `DeathPit` y cinco
    `HazardZone` en un nivel que esta misma ficha llama «travesía atmosférica» y
    donde se prohíben los enemigos *«porque la tensión ya está»*. Memorizar
    caídas no es atmósfera. **No queda ni un foso ni una zona de daño**, y hay
    tres pruebas que lo comprueban —una de ellas leyendo el XML, por si el
    cargador algún día ignora un tipo por otro motivo—.
12. **El daño era invisible.** El motor sólo dibujaba las zonas de daño que
    **suben**; una fija esperaba a que el diseñador pintara pinchos en las
    baldosas y aquí no había ninguno. Este nivel ya no usa ninguna, pero el
    defecto era del motor y afectaba a cualquier entrega: se arregló aparte en
    **AUD-228**, y de paso apareció que la única `HazardZone` fija que quedaba
    en el proyecto estaba en `stage0`, el nivel que copian los estudiantes,
    haciendo daño invisible desde el primer día.
13. **Un cementerio se baja.** Ahora es un pozo de 60 × 240 (960 × 3840 px) y los
    cinco actos son cinco tramos de profundidad. Se desciende por 44 repisas que
    alternan lado —un zigzag— hasta el suelo del umbral. Como el motor **no tiene
    daño por caída**, caer es el movimiento y no el castigo: es lo que permite
    quitar los fosos sin poner nada en su lugar.

Lo que sustituye al peligro son **superficies que se ven** — la regla es que nada
cambie el movimiento del jugador sin que se vea por qué:

| Superficie | Qué hace | Cómo se ve |
|---|---|---|
| Musgo | Arrastra hacia el hueco de su repisa (`arrastre` 62 px/s) | La losa cubierta de musgo, con matas (GID 5) |
| Lodo | Frena: se camina despacio (`multiplicador` 0,88) | La losa cubierta de barro, con raíces (GID 7) |
| Viento | Empuja en el acto IV, con ciclo de 3,2 s | La tormenta, los rayos y la lluvia |

Las dos son **la misma losa con otra superficie encima**, y eso es la mitad del
diseño: tres materiales que no se parecen se leerían como «tres suelos
distintos», y piedra cubierta se lee como «esta losa está tomada», que es lo que
explica por qué resbala. El `multiplicador` del lodo **no depende de los
fotogramas por segundo** — medidos 79,20 px/s a 30, a 60 y a 120 (AUD-236).

**El tileset (AUD-237).** El suelo lo pintaba `tileset_stage0.png`, la piedra
del castillo del prólogo, mientras `tileset_cemetery.png` existía sin que lo
usara ningún mapa: eran ocho baldosas de relleno genéricas, así que usarlo
habría empeorado el nivel. Ahora la hoja se dibuja de verdad —losa de cripta,
muro del pozo, lápida en dos mitades, cruz, musgo y lodo— y el cementerio pisa
su propia piedra. Los GID son un contrato con `CEM_ORDEN` y hay una prueba que
compara las dos listas.

Las grietas siguen ahí y **ya no hacen daño**: son luz verde en el canto de cada
repisa, dibujada por la escena con el fondo, que marca el borde del que hay que
dejarse caer.

**Lo que da miedo, y no hace daño (AUD-246 y AUD-247).**

Cuatro cosas más, y ninguna quita salud. El terror aquí no puede ser perder vida
—la ficha prohíbe enemigos y el rediseño quitó las trampas—, así que es otra
cosa: **no poder fiarte de lo que ves**.

| Dónde | Qué | Por qué no castiga |
|---|---|---|
| Los doce braseros | Se **ven** arder: cuenco de piedra siempre, llama que crece al encenderse | Un brasero apagado se ve apagado: es la barra de progreso del §3 |
| Acto II | Losas de tumba que se rompen a golpes (`BreakableBlock`, 2 golpes) | Son atajos; el motor pinta grietas que cuentan lo que queda |
| Acto III | Cinco losas que aparecen y desaparecen **con el órgano** (`RhythmBlock`, `patron="x..."`, `bpm=60`) | Un pulso por segundo, cuatro por compás, y cuatro segundos es lo que dura cada acorde |
| Acto IV | Losas fantasma: sólidas siempre, visibles sólo con el relámpago o la visión espectral | Un pincho invisible es una trampa; un **suelo** invisible es una pregunta |

Las tres losas van en el hueco de su repisa y ninguna lo tapa: el hueco mide 17
o 18 columnas y la losa cuatro, así que siempre se baja por al lado. En un
descenso, una mecánica que pueda encerrarte es peor que un foso — el foso al
menos te devuelve al checkpoint. Hay una prueba que mide el margen libre.

Efecto medido: `design_pacing` pasó de 5/8 a **8/8**. El aviso era «ningún salto
pone a prueba al jugador» y ahora hay cuatro exigentes **sin un solo peligro
nuevo**.

**El órgano (AUD-227).** `bgm_final_approach.wav` lo generaba
`_gen_music_track`, el sintetizador genérico de los otros diez temas: onda
cuadrada, saw y un golpe de ruido blanco en cada pulso. La ficha pide órgano y
sonaba una caja de ritmos en un nivel donde «el silencio es el jefe».

Ahora lo genera `_gen_bgm_organo`, y no es una imitación: un registro de órgano
**es** un armónico —un tubo que suena a un múltiplo entero de la fundamental—,
así que la pista es síntesis aditiva con los seis registros del principal
(8', 4', 2⅔', 2', 1⅓', 1'), pedal de 16', trémolo al 6 % y **sin percusión**.
Cuatro acordes de re menor (i – VI – III – v), cuatro segundos cada uno.

Dos pruebas lo defienden, y ninguna comprueba «que el fichero exista» —eso ya
pasaba antes—: una exige que los picos del espectro caigan en múltiplos enteros
de las notas del acorde, y la otra cuenta ataques bruscos por segundo. Medido:
el órgano da 0,63/s y el chiptune que había daba 4,3/s.

**Medido, no supuesto:**

- Dibujar el nivel cuesta **4,6 ms** por fotograma; con la visión espectral
  puesta, **6,6 ms** de los 16,6 que hay a 60 fps. El umbral se aplica a 1/4 de
  resolución justamente por esto: a 1/2 costaba 4,6 ms de más y se salía del
  presupuesto.
- En la curva de dificultad sale con **25,5** (antes 36,8). Los peligros por
  pantalla bajaron de 6,0 a 2,0 no quitando peligros sino repartiéndolos por un
  nivel tres veces más largo, que es lo que un ★★☆☆☆ atmosférico debe puntuar.
  Sigue sin introducir ningún escalón brusco.
- `grade_stage.py` lo puntúa **105/130 (80,8 %)**, antes 94/130. Los 20 puntos
  que faltan son los dos criterios de enemigos: el calificador espera que un
  nivel tenga enemigos y éste tiene prohibido tenerlos. Es la única nota del
  proyecto donde bajar es lo correcto.

## Ficha rápida

| Campo | Valor |
|---|---|
| Dificultad | ★★☆☆☆ (2/5) — **atmosférica**: el miedo es el desafío |
| Tamaño mínimo | **1600 × 608 px** (100 × 38 tiles) — el construido son 4800 × 608 |
| Tamaño de referencia | ~400 px de recorrido en el diseño canónico |
| Tipos de enemigo | **0 — regla de oro: prohibido añadir** |
| Enemigos mínimos | 0 |
| Objetos mínimos | 1 `PlayerSpawn`, 1 `Checkpoint`, 1 `Portal`, 1 `HazardZone`, 1 visión especial |
| Día/noche | `dusk` 19:00 → 23:00, `day_length` 900 s *(sugerido)* |
| Clima | Libre (sugerencia: niebla baja que nunca tapa los peligros del suelo) |
| Concepto académico | Unidad V (tinte espectral) + Unidad VIII (visión de umbral) |
| Límite de tiempo | Sin límite (pacing atmosférico) |

## Reglas obligatorias

1. **Sin enemigos.** Si el nivel aburre, se arregla con más marcas ocultas, no
   con serpientes. La tensión ya está: es el silencio antes del juez.
2. **Visión espectral obligatoria** (Unidad VIII): con el botón de ataque largo
   se filtra la pantalla en umbral y se revelan marcas ocultas en las losas
   (3 s). Es la mecánica protagonista.
3. **Los cuencos de fuego son plataformas y luz**: cerca = más brillo; lejos =
   oscuridad. El brillo por proximidad es la mecánica de la Unidad V.
4. **Las grietas pulsantes** (HazardZone 0.25 periódico) son los únicos peligros
   y deben leerse con anticipación (pulso visible).
5. **Los ecos de los espíritus vencidos** (venado, Rey, Gavilán) aparecen como
   siluetas en BG_Mid: storytelling ambiental, no entidades.

## Día/noche (sugerido)

- `start_hour`: `dusk` (19:00) — el cementerio se ve por última vez de día agonizante.
- `day_length`: 900 s → termina a las **23:00** (noche) — prepara el clímax.
- *(Sugerido por la guía; el canon no lo fija: si el profesor decide otra hora,
  debe mantener la regla del reloj continuo con el 4-2.)*

## Enemigos

Ninguno. El único "contenido" son:

| Elemento | Cantidad | Nota |
|---|---|---|
| Cuencos de fuego | 3+ | Plataformas OneWay + luz por proximidad |
| Grietas pulsantes | 2+ | HazardZone 0.25 periódico |
| Marcas ocultas | 5+ | Solo visibles con la visión espectral |
| Ecos de espíritus | 3 | Siluetas BG_Mid (venado, Rey, Gavilán) |
| Coleccionables | 0 (o 3 discretos) | Mejor sin coleccionables: el silencio es el premio |

## Mapa sugerido

```
 19:00 ── OCASO → NOCHE ─────► 23:00
 SPAWN ─[fuego]──[fuego]──[grieta]──[fuego]──[grieta]──[fuego]── PORTAL
   │  ecos en BG_Mid: venado · serpiente · halcón
   │  las losas ocultan marcas: visión espectral (ataque largo)
   └── sin enemigos: la atmósfera ES el desafío
```

## Checklist de cierre

- [x] Sin enemigos (regla de oro) — comprobado contando `entity_list`, no el XML
- [x] Visión espectral funcionando con marcas ocultas — comprobada píxel a píxel
- [x] Cuencos con luz por proximidad; grietas pulsantes legibles
- [x] `start_hour = 19` y `day_length = 900` — como número, ver §0
- [x] `validate_tmx.py --ci` en verde (17/17)
- [x] Cinco actos de una pantalla y media cada uno (AUD-208)
- [x] Música y fondo de la zona final, no de la zona 3 ni del prólogo (AUD-209)
- [x] Brujas cruzando con el relámpago (AUD-210)
- [x] El susurro de la oscuridad, sin daño (AUD-211)

## Diseño propuesto

Una propuesta completa de cómo llenar este nivel — progresión ambiental estilo
Magus (Chrono Trigger), luna descendente, 12 braseros en secuencia, tormenta
con relámpagos que revelan peligros, La Cegua como presencia (nunca enemigo),
lápidas con los nombres de los estudiantes y tramos de salto — está en:

- [[15_DISENO_4_1_EL_CEMENTERIO.md|Diseño 4-1 — El Cementerio y La Cegua]]

*(Cumple todas las reglas obligatorias de esta ficha; no modifica ninguna.)*
