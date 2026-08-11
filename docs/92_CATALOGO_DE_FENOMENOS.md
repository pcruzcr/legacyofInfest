---
document_id: "LOI-CAT-92"
title: "Catálogo de fenómenos ambientales — qué se puede hacer, qué cuesta y qué no vale la pena"
tags: ["worldsimulation", "clima", "astronomia", "atmosfera", "plan"]
source: "docs/92_CATALOGO_DE_FENOMENOS.md"
date_processed: "2026-08-09"
---

# Catálogo de fenómenos ambientales

**Pregunta que contesta este documento:** ¿se puede implementar *toda* la
taxonomía propuesta —30 fenómenos atmosféricos, 25 tipos de clima, estaciones
configurables, sol, luna, estrellas, planetas, eclipses, auroras, fenómenos
ópticos y clima extremo— para dejar el motor cerrado?

**Respuesta corta: sí, y cuesta mucho menos de lo que la lista sugiere,
porque la lista colapsa.**

---

## 1. Por qué la lista colapsa

Los noventa y tantos elementos de la taxonomía **no son noventa sistemas**.
La inmensa mayoría son *consumidores* de los mismos quince números, y esos
quince números ya están calculados y probados:

```
EnvironmentState (src/framework/world/environment.py)
    hora · dia · estacion
    factor_ambiente · color_ambiente · bloom_extra
    clima · precipitacion · humedad · viento · visibilidad · cobertura_nubes
    altura_solar · fase_lunar · fase_del_dia
  derivados: es_de_noche · luz_lunar · suelo_mojado · factor_friccion
```

Un arcoíris no es un sistema: es *«dibuja un arco si `precipitacion > 0` y
`altura_solar` está entre 0 y 0,7 y el sol está a tu espalda»*. Un halo lunar
es *«dibuja un anillo si `luz_lunar > 0,6` y `cobertura_nubes` entre 0,3 y
0,7»*. Una ventisca es `snow` + `viento` alto + `visibilidad` baja: **ya se
puede declarar hoy**, sin una línea de código nueva.

Ésa es la razón por la que la infraestructura iba primero. Con el estado
puesto, el coste de cada fenómeno deja de ser «un sistema» y pasa a ser «una
condición y un dibujo», y el catálogo entero se vuelve abordable de uno en
uno, por cualquiera, sin tocar la simulación.

**La regla que hace que esto siga siendo verdad:** un fenómeno **lee** el
estado y nunca lo escribe. El día que un efecto de niebla ajuste
`visibilidad` por su cuenta, vuelve el problema que `WorldSimulation` vino a
cerrar.

---

## 2. Qué está construido hoy (AUD-357/358)

| Pieza | Dónde | Pruebas |
|---|---|---|
| `EnvironmentState` — el contrato inmutable | `framework/world/environment.py` | 22 |
| `WorldSimulation` — reloj, calendario, estación, astronomía, clima | `framework/world/simulation.py` | 26 |
| `RelojDeMundo` + curva de luz de 9 paradas | `framework/stage/day_night.py` | ya existía |
| `Estacion` ×4 con tinte, clima y partículas | `framework/stage/seasons.py` | ya existía |
| `WeatherSystem` ×5 climas, viento, relámpagos, audio | `framework/vfx/weather_system.py` | ya existía |
| Niebla, agua, sombras proyectadas, god rays, bloom, viñeta, aberración | `framework/vfx/`, `engine/render/` | ya existía |

Lo que la simulación **calcula** hoy: altura solar (armónico), las cinco
bandas del día (día + tres crepúsculos + noche), fase lunar por periodo
sinódico real (29,530588 d), calendario por vuelta del reloj, humedad,
viento, cobertura de nubes, precipitación y visibilidad por clima — y la
visibilidad sale de la capa que el sistema de clima ya pintaba, no de una
tabla nueva.

---

## 3. El catálogo, con coste real

**Leyenda:** ✅ ya se puede declarar hoy · 🟢 barato (lee el estado y dibuja)
· 🟡 medio (necesita un sistema propio) · 🔴 caro (cambia arquitectura) ·
⛔ no vale la pena, con razón

### 3.1 Precipitación y atmósfera

| Fenómeno | Estado | Cómo |
|---|---|---|
| Llovizna / lluvia / lluvia intensa / aguacero | ✅ | Son `rain` con `precipitacion` 0,2 / 0,6 / 0,85 / 1,0. Ya es un número continuo, no cuatro climas |
| Tormenta eléctrica | ✅ | `storm`, con relámpagos de AUD-270 |
| Niebla / bruma / calima | ✅ | `visibilidad` + `humedad`; ya se distinguen (la niebla moja el aire, no el suelo — probado) |
| Nieve | ✅ | `snow` |
| Ventisca | ✅ | `snow` + `viento` alto + `visibilidad` baja: **es una combinación, no un clima** |
| Granizo | 🟢 | Partículas con rebote; el emisor ya existe |
| Humo / polvo / vapor | 🟢 | Emisores de partículas + `visibilidad` |
| Rocío / escarcha | 🟢 | Tinte sobre tiles según `humedad` y hora |
| Hielo en superficie | ✅ | **Ya existe**: `ZonaDeFriccion` del TMX (AUD-236) + `factor_friccion` del estado |
| Torbellino | 🟡 | VFX con fuerza sobre partículas |
| Tornado / huracán | 🔴 | No es un efecto: es una mecánica de nivel con física propia |
| Aurora | 🟡 | Capa de cielo con gradiente animado; barata **si** el cielo procedural existe (§3.4) |

### 3.2 Estados de clima

La taxonomía de 25 tipos (`CLEAR`, `PARTLY_CLOUDY`, … `EXTREME`) **no hay que
implementarla como 25 tipos**, y hacerlo sería un error: son combinaciones de
`cobertura_nubes` × `precipitacion` × `viento` × `visibilidad`, que ya son
números continuos. Veinticinco constantes serían veinticinco sitios donde
olvidar actualizar uno.

| Pieza | Estado | Cómo |
|---|---|---|
| Los 25 tipos como *nombres* | ✅ | Se declaran en la tabla `CLIMAS` de `simulation.py` — cinco filas hoy, veinticinco es la misma estructura |
| Temperatura y presión | 🟢 | Dos campos más del estado; la estación los modula |
| **Transiciones** (`CLEAR → CLOUDY → RAIN → STORM`) | 🟡 | **Es lo que más aporta de toda esta sección.** Hoy el clima cambia de golpe. Una interpolación entre dos filas de `CLIMAS` con una curva de tiempo es ~60 líneas y hace que el mundo se sienta vivo |
| Probabilidad de clima por estación | 🟢 | `Estacion` ya declara `clima` por defecto; pasar a una distribución es una tabla |

### 3.3 Estaciones

| Pieza | Estado | Cómo |
|---|---|---|
| Las 4 tradicionales | ✅ | `seasons.ESTACIONES` |
| **Seca / lluviosa / transición** (Costa Rica) | 🟢 | `ESTACIONES` es un `dict`: añadir tres claves con su tinte, clima y partículas. **No hay nada en el motor que exija cuatro** |
| Progreso dentro de la estación | 🟢 | `dia_del_anio / duracion`; el calendario ya cuenta días |
| Transiciones graduales | 🟢 | Interpolar el tinte entre dos estaciones, como `_mezclar` hace con las horas |
| Solsticios y equinoccios | 🟢 | Días concretos del calendario; útiles como eventos |

### 3.4 Astronomía

| Pieza | Estado | Cómo |
|---|---|---|
| Altura solar, bandas del día, fase lunar | ✅ | Construido y probado |
| Azimut solar/lunar | 🟢 | Un campo más; la dirección de sombra sale de ahí |
| **Sombras que siguen al sol** | 🟡 | `sombras_proyectadas.py` ya proyecta siluetas; darle la dirección del estado es el cambio. **Alto valor visual por poco coste** |
| Ocaso/orto de luna | 🟢 | Mismo armónico desfasado por la fase |
| Estrellas | 🟡 | `StarField` procedural (no entidades ECS), visibilidad = `es_de_noche × (1−nubes) × (1−luz_lunar)` |
| Constelaciones propias de INfest | 🟢 | Tabla de puntos + líneas sobre el `StarField`. **Encaja con la mitología del juego** |
| Vía Láctea | 🟢 | Textura con `visibilidad` estelar |
| Meteoros / lluvia de meteoros | 🟢 | Partícula con trayectoria; evento del calendario |
| Cielo procedural (gradiente por hora) | 🟡 | Sustituye `sky_day.png` / `sky_night.png` por un degradado del estado. **Es la pieza que desbloquea auroras, halos y crepúsculo de verdad** |
| Eclipses solar/lunar | 🟢 | Como *evento del calendario* con un multiplicador sobre la luz. Barato — si se pretende que caigan en fechas astronómicamente correctas, es 🔴 |
| Superluna / microluna / luz cenicienta | 🟢 | Escala y brillo del disco |
| **Latitud/longitud reales** | 🔴 | Efemérides de verdad (declinación, ecuación del tiempo, refracción). Semanas de trabajo y un modelo que hay que validar contra tablas |
| Planetas visibles | ⛔ | Mecánica celeste. Nadie va a distinguir Saturno de una estrella en un juego 2D a 800×600 |

### 3.5 Fenómenos ópticos

| Fenómeno | Estado | Cómo |
|---|---|---|
| God rays / rayos crepusculares | ✅ | **Ya existe** (AUD-226), con foco y fuerza publicados por la escena |
| Dispersión atmosférica | 🟢 | Ya está el color grading; el estado le da el color |
| Arcoíris / doble arcoíris | 🟢 | Arco con la posición del sol; condición sobre `precipitacion` |
| Halo solar / lunar, corona | 🟢 | Anillo sobre el disco; condición sobre `cobertura_nubes` |
| Parhelio / paraselene | 🟢 | Dos manchas a ±22° del halo |
| Espejismo | 🟡 | Distorsión en el post-procesado; ya hay pasada de refracción (AUD-216) |

### 3.6 Lo que recomiendo NO hacer, y por qué

| Ítem | Razón |
|---|---|
| Planetas | Mecánica celeste para píxeles que nadie identificará |
| Efemérides reales por lat/long | Semanas de trabajo y validación; el mundo ya es coherente sin ello, que es lo que el jugador percibe |
| Huracán / tornado / inundación como *fenómenos* | Son **mecánicas de nivel**, no ambiente. Diseñarlas como clima produce un sistema que nadie puede jugar |
| Calidad del aire | No hay ningún consumidor en el juego. Un campo sin lector es deuda |
| Los 25 tipos de clima como constantes | Ya son combinaciones de cuatro números continuos; 25 constantes son 25 sitios donde olvidar uno |

---

## 4. Prioridad, con la aritmética delante

**Nivel 1 — lo imprescindible.** Sol, luna, fases, crepúsculo, estaciones,
nubes, viento, lluvia, tormenta, rayos, niebla, humedad, iluminación.
**Estado: ✅ construido o declarable hoy.** Lo que falta del Nivel 1 son dos
cosas, y son las dos de más valor por línea escrita:

1. **Cielo procedural** (🟡) — desbloquea el crepúsculo de verdad, las
   auroras, los halos y quita tres PNG de cielo.
2. **Sombras dirigidas por el sol** (🟡) — sombra larga al amanecer, corta a
   mediodía, blanda con nubes. El sistema de proyección ya existe.

Y una tercera de coste medio y efecto grande:

3. ~~**Transiciones de clima** (🟡) — que no se pase de despejado a tormenta en
   un fotograma.~~ **HECHO (2026-08-11, AUD-424).**
   `WorldSimulation.SEGUNDOS_DE_TRANSICION = 6.0` y los valores meteorológicos
   —precipitación, humedad, nubes, visibilidad y viento— se acercan al objetivo
   a ritmo constante. El **nombre** del clima sigue cambiando al instante:
   es la intención del diseñador, y quien pregunte «¿está lloviendo?» debe
   recibir la respuesta nueva enseguida; lo que llega tarde es el efecto.

   Tres decisiones que conviene no revertir sin leer esto:

   * **Se arranca ya en el objetivo.** Un mapa con `climate=storm` abre con
     tormenta. Sin eso, todo nivel de tormenta empezaría despejado y se
     ensuciaría durante los primeros segundos — peor que el salto que esto
     arregla.
   * **La transición avanza aunque el reloj esté congelado.**
     `RelojDeMundo.congelado` sale de `duracion_dia <= 0`, que es como se
     declara un mapa **sin ciclo de día y noche**: la mayoría. Meterla detrás
     de ese corte habría dejado la característica sin funcionar en casi todos
     los niveles.
   * **Interpolación lineal, no exponencial.** Una exponencial se acerca sin
     llegar nunca, así que la precipitación se quedaría en 0,98 para siempre y
     no se podría escribir una prueba de que la transición **termina**.

   `set_clima(nombre, inmediato=True)` salta la transición, para cargar un
   nivel o cortar en seco en una cutscene.

**Nivel 2 — alto valor visual, coste bajo.** Arcoíris, halos, coronas,
meteoros, polvo, humo, bruma, rocío, escarcha, constelaciones propias.
Todos 🟢: cada uno es una condición sobre el estado y un dibujo. **Se pueden
hacer de uno en uno, por personas distintas, sin coordinarse** — que es
exactamente lo que la infraestructura compró.

**Nivel 3 — eventos especiales.** Eclipses, auroras, lluvias de meteoros,
superlunas. 🟢 salvo el realismo de fechas.

---

## 5. La respuesta honesta a «¿se puede hacer todo?»

Sí, salvo los cinco de §3.6 — y ésos no se dejan fuera por coste, sino porque
no aportan nada que el jugador pueda percibir.

Pero conviene separar dos cosas que la pregunta junta:

- **La infraestructura que soporta el catálogo entero: hecha.** Es lo que
  entregan AUD-357 y AUD-358, y es la parte que no se puede hacer «de una en
  una» después.
- **Los fenómenos: son una cola larga**, y añadirlos todos de golpe es
  precisamente lo que el propio documento de diseño desaconseja («no
  implementaría todos esos fenómenos ahora; haría primero la infraestructura
  capaz de soportarlos»). Con el estado puesto, cada uno es autónomo.

Y una advertencia que vale más que el catálogo: **más sistemas no son más
madurez.** Un motor con noventa fenómenos y sin transiciones de clima se
siente peor que uno con doce fenómenos que transicionan bien. La lista de
arriba está ordenada por lo que el jugador nota, no por lo que suena
completo.

---

## Documentos relacionados

- `docs/91_PLAN_DE_CIERRE.md` — el plan de ocho lotes; esto es el lote 5
- `docs/03_ARCHITECTURE.md` — `framework/world/` en el árbol
- `docs/70_INFORME_DE_AUDITORIA_VIVO.md` — AUD-357 y AUD-358
- `docs/niveles/15_DISENO_4_1_EL_CEMENTERIO.md` — el 4-1 **que existe**, en cinco actos
