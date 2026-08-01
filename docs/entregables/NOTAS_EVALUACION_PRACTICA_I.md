# Evaluación Práctica I — notas por estudiante

**Curso:** Computación Gráfica y Procesamiento Digital de Imágenes I
**Fecha del informe:** 31 de julio de 2026
**Entregas recibidas:** 14 (13 del lote inicial + la corrección de stage2_2)

Todas las entregas están instaladas en el repositorio, validadas y probadas.
Las 14 cargan y dibujan sin lanzar excepción.

---

## Antes de leer las notas: tres errores de las herramientas, no de ustedes

Estas cifras **no son las mismas** que las de la primera pasada, y conviene
decir por qué antes de dar ningún número. Al calificar la entrega de stage2_2
aparecieron tres defectos en mis propias herramientas. Los tres castigaban
trabajo correcto.

**1. El calificador de escenarios sólo conocía doce enemigos.**
`grade_stage.py` llevaba una lista escrita a mano:

```python
{"MushMom", "Bat", "Skitter", "Mantis", "Flying", "Shooter",
 "Charger", "Archer", "Brute", "Caster", "Assassin", "Walker"}
```

De esos doce nombres, **cuatro no existen** en el motor —son de un bestiario
anterior— y **faltaban veintidós** de los treinta que el registro tiene hoy. El
mapa de stage2_2 coloca siete enemigos y el informe decía «2 enemy(ies)
placed», porque `WalkerGuardia`, `FlyingBoa`, `ShooterSerpienteArbol` y
`WalkerSerpientePequena` —los cuatro del bestiario oficial de la Zona 2— no
estaban en la lista. Tampoco contaba los que ustedes registran por su cuenta:
La Soda coloca dos enemigos propios y el informe los ignoraba.

No costó puntos, porque esas dos casillas puntúan por presencia. Costó algo
peor: el informe que ustedes leen les decía que sus enemigos no contaban.

**2. El calificador no entendía los tilesets externos.**
Tiled permite declarar el tileset dentro del `.tmx` o en un `.tsx` aparte. La
segunda es la que Tiled recomienda y la que usó la entrega del Lobby. El
calificador sólo miraba la primera, daba «No valid tileset images» y restaba 5
puntos a un mapa cuyo tileset estaba perfectamente en su sitio. **El Lobby sube
de 98 a 103 por esto.**

**3. El calificador de jefes calificaba módulos que no son jefes.**
Apuntado a una carpeta, `grade_boss.py` puntuaba **todos** los `.py`. En
`boss_paburu` eso son siete módulos —la escena, la arena, los sprites, la
introducción, los guardianes— y a cada uno le ponía 0/100 por «no hereda de
BossBase». El jefe sacaba 100 y la media impresa al final era **14,3 %**. Con
`boss_venado`, que trae utilidades y pruebas, eran catorce ficheros y la media
**7,1 %** sobre un jefe que también saca 100.

Dicho de otro modo: quien organizó su código en varios módulos —que es lo que
el curso pide— salía peor calificado que quien lo metió todo en un fichero.

Los tres arreglos están en el repositorio con sus pruebas
(`tests/test_graders_match_the_engine.py`, 16 pruebas). Es la tercera vez esta
semana que una herramienta mía guarda su propia copia de algo que el motor ya
sabe y la copia se queda vieja. La cura es siempre la misma: preguntarle al
registro en vez de recordar.

---

## Notas — escenarios

Rúbrica `scripts/grade_stage.py`, sobre 130 puntos.

> **Notas revisadas al alza el 31/07.** Tres defectos del calificador quitaban
> puntos por trabajo correcto; están corregidos y estas son las notas buenas.
> Ninguna bajó. El detalle, más abajo en «Correcciones al calificador».

| # | Estudiante | Ranura | Carpeta | Nota | % | Antes |
|---|---|---|---|---|---|---|
| 1 | César Ubáu Calvo | 2-2 | `stage2_2` | 130/130 | **100 %** | 129 |
| 2 | Fabrizio E | 1-1 | `stage1_1` | 127/130 | **97,7 %** | 126 |
| 3 | Yariel Andrey Elizondo Jiménez | 1-3 | `stage1_3_las_aulas` | 110/130 | **84,6 %** | 106 |
| 4 | Rebeca | 3-3 | `stage3_3_el_patio` | 106/130 | **81,5 %** | 105 |
| 5 | Guillermo Morice Díaz | 1-2 | `stage1_2_la_soda` | 104/130 | **80,0 %** | 103 |
| 6 | Alejandro Luna | 2-3 | `lobby_datacenter` | 104/130 | **80,0 %** | 103 |
| 7 | Isaac Felipe Morún Moreira | 3-4 (arena) | `stage3_4_boss_gavilan` | 102/130 | **78,5 %** | 101 |
| 8 | Avril | 3-1 | `stage3_1_la_entrada_de_piedra` | 101/130 | **77,7 %** | 100 |
| 9 | José Pablo Monestel Cruz | 3-2 | `hall` | 91/130 | **70,0 %** | 90 |
| 10 | Saúl | 2-1 | `stage2_1_oficinas` | 89/130 | **68,5 %** | 83 |

*Referencia del profesor:* `stage0` sacaba **121/130 (93,1 %)** con la misma
rúbrica —por debajo de dos entregas— y se regeneró hasta **130/130**. El
detalle de qué le faltaba está en `docs/59_STAGE_0_REGENERADO.md`; lo resumido
es que el escenario que enseña el motor no usaba ni un coleccionable, ni un
obstáculo sólido, ni una sola de las once mecánicas de la fase 5.

### Correcciones al calificador

Tres defectos, todos en la misma dirección: castigar trabajo correcto.

| Ref | Qué hacía mal | A quién afectaba |
|---|---|---|
| AUD-110 | Avisaba de que faltaba la capa `Collision` aunque estuviera, si venía como grupo de objetos —que es como la hace Tiled | los 15 mapas |
| AUD-112 | Contaba los muros de cierre del mapa como repisas, y no reconocía `Pickup`, `Key` ni `Chest` como coleccionables | Yariel +4, Saúl +6 |
| AUD-113 | `meta_score * 3` sobre 10 puntos: con las tres propiedades exigidas daba **9/10**, así que el 10/10 era inalcanzable | todos +1 |

AUD-113 es el más incómodo de los tres. Nadie podía sacar la casilla completa
de metadatos, y la rúbrica llevaba todo el curso diciéndole a cada estudiante
que le faltaba algo cuando no le faltaba nada.

## Notas — jefes

Rúbrica `scripts/grade_boss.py`, sobre 100 puntos. Aplicada al fichero que
define la subclase de `BossBase`, no al paquete entero.

| # | Estudiante | Jefe | Nota | % |
|---|---|---|---|---|
| 1 | José Jahel Morales Briceño | El Venado | 100/100 | **100 %** |
| 2 | Alejandro Josué Rodríguez Zamora | El Gran Shamán Paburu | 100/100 | **100 %** |
| 3 | *(sin nombre en la plantilla)* | El Rey Terciopelo | 50/100 | **50 %** |
| 4 | Isaac Felipe Morún Moreira | El Gavilán Camionero Mascarero | 45/100 | **45 %** |

> **Las arenas de jefe no se califican con `grade_stage.py`.** Esa rúbrica mide
> si se llega andando a la salida, y en una arena la salida se abre al derrotar
> al jefe. Pasarla por ahí da 61,5 % a la arena de referencia del propio juego,
> que está bien hecha. El calificador ya lo avisa por escrito cuando ocurre.

---

## Qué le falta a cada uno

### César Ubáu Calvo — stage2_2 «Entrada y Antenas» — 100 %

La entrega más completa del lote. Mapa de 120 × 50 en tres secciones (parqueo,
escalada, azotea), 8 capas, 50 objetos, 5 checkpoints, 7 enemigos, tileset
propio de 128 tiles dibujado por él. Tres módulos con un concepto académico
cada uno: cono de visión por álgebra vectorial (Unidad II), patrulla sobre
B-Spline (Unidad III) y atmósfera por espacios de color (Unidad V). Usa
`CameraLock` con `lock_x`/`lock_y` separados, que casi nadie usó.

Nota perfecta. El punto que le faltaba era **AUD-113**, un defecto del
calificador y no suyo: la casilla `metadata` no podía dar más de 9/10.
Nada que corregir en la entrega.

**Una nota menor:** el docstring de `stage2_2.py` dice «64 × 50 tiles» y el mapa
mide 120 × 50; el README y `CONTENIDO.md` sí dicen 120. Es una línea desfasada
en un comentario, no afecta a nada.

### Fabrizio E — stage1_1 — 97,7 %

11 enemigos, geometría sólida. Dos cosas:

- Queda una plataforma sin ruta desde el spawn: o sobra, o falta el camino.
- Registra `FlyingBird` y `ShooterFrog` **dentro de una función**. Al jugar
  funciona, pero el previsualizador y las herramientas que abren el mapa suelto
  no pueden construir esos objetos. Muévelo al nivel del módulo, como en
  `stage1_3_las_aulas`.
- `stage1_1.RESPALDO.tmx` apunta a un `tileset_manual.png` que no está. Si es un
  respaldo, sácalo de la entrega.

### Yariel Andrey Elizondo Jiménez — stage1_3 «Las Aulas» — 84,6 %

12 enemigos, buen tamaño de mapa. Pierde por diseño:

- Dos repechos de 512 px. El jugador no salta tan alto: son muros, no subidas.
- Una plataforma inalcanzable desde el spawn.
- 640 px entre checkpoints en un tramo: morir ahí cuesta demasiado camino
  rehecho.
- Falta la propiedad de mapa `author`.

### Rebeca — stage3_3 «El Patio» — 81,5 %

11 enemigos bien repartidos. Tres cosas:

- Dos plataformas sin ruta desde el spawn.
- Un objeto `HazardZone` colocado en la capa `Collision`. Ahí no significa nada
  y se tratará como suelo sólido —el efecto contrario al que buscabas—. Va en
  la capa `Objects`.
- Falta `author`.

### Guillermo Morice Díaz — stage1_2 «La Soda» — 80,0 %

Registra dos enemigos propios (`LaSodaWalkerRaton`, `LaSodaFlyingCucaracha`) a
nivel de módulo, que es la forma correcta. Pierde por:

- Sin `climate` (−5). Los válidos son `clear`, `fog`, `rain`, `sandstorm`,
  `snow`, `storm`, `wind`.
- Falta `author`.
- Ningún salto pone a prueba al jugador: el nivel se recorre andando. Es el
  aviso de ritmo, y es el que más pesa aquí.
- Sólo 1 checkpoint y 2 enemigos en todo el mapa.

### Alejandro Luna — stage2_3 «El Lobby» — 80,0 %

Sube 5 puntos respecto a la primera pasada: su tileset externo `.tsx` era
correcto y el calificador no lo entendía. Queda:

- Sin `climate` (−5) y sin `author`.
- Ningún salto exigente: el recorrido no plantea ningún problema.
- 3 enemigos es poco para el tamaño del mapa.

### Isaac Felipe Morún Moreira — arena 3-4 y jefe Gavilán — 78,5 % / 45 %

**Corrección aplicada al integrar:** su TMX colocaba un `BossGavilan` y el
código definía la clase, pero **nadie la registraba**. El jefe no habría
aparecido en su propia arena. Se añadió la línea que faltaba siguiendo el patrón
de sus compañeros. Está anotado aquí para que cuente en la nota.

En el jefe (45/100) faltan cuatro cosas de la rúbrica:

- **Ningún método de ataque.** Hay `_patrol_behavior`, `_alert_behavior` y
  `_update_orbit`, pero nada que ataque. El propio README dice «aún por
  definir».
- Sin transiciones de fase y con un solo umbral de vida (se piden ≥2).
- Sin estado de telegrafiado (el aviso antes del golpe).
- Sin conexión a eventos.

En la arena: un repecho de 144 px que no se puede saltar, dos plataformas
huérfanas y 600 px entre checkpoints.

### Avril — stage3_1 «La Entrada de Piedra» — 77,7 %

10 enemigos, geometría correcta. Pierde por `climate` (−5), falta `author`, y
785 px entre checkpoints.

**Corrección aplicada al integrar:** su escenario buscaba el TMX junto al
código; se reapuntó a `assets/maps/`, que es donde miran el validador, el
calificador y el previsualizador.

### José Pablo Monestel Cruz — stage3_2 «El Hall» — 70,0 %

**Corrección aplicada hoy, y es culpa mía:** al integrar el lote lo puse en la
ranura `stage2_2`. Su propio código lo desmentía desde el principio —`ZONE = 3`
y `STAGE_NAME = "3-2  EL HALL"`— así que estaba ocupando la ranura de otro
compañero y se jugaba en la zona equivocada. Ya está en `stage3_2`, que es donde
él dijo que iba. No afecta a su nota.

Lo que sí afecta:

- **No se llega a la salida andando (−12).** No hay ruta de plataformas desde el
  spawn hasta el `NextTrigger`. Su README explica que el alcance real de un
  salto es ~43 px y que diseñó contra ese número, pero el análisis no encuentra
  el camino: hay un repecho de 416 px en (496, 96) por medio.
- Una plataforma huérfana y 747 px entre checkpoints.

Es la entrega con la documentación más cuidada del lote —tileset propio de 60
tiles generado por código, y una nota sobre la envolvente de salto real frente
a la estimada que es correcta y que ningún otro detectó—. El problema es de
geometría, no de comprensión.

### Saúl — stage2_1 «Oficinas» — 68,5 %

Es la única entrega que **no pasa la validación**. Cuatro cosas, todas rápidas:

- Faltan las tres propiedades de mapa obligatorias: `stage_id`, `stage_name`,
  `bgm_track`. Eso solo son −10 en `metadata`.
- **Ningún checkpoint (−15).** Con 3048 px entre el spawn y el final, morir
  manda al principio del nivel.
- Sin `climate` (−5).
- Dos repechos de 544 px que no se pueden saltar.

**Correcciones aplicadas al integrar:** igual que Avril, su TMX se buscaba junto
al código y se reapuntó a `assets/maps/`. Y su `stage2_1_oficinas.py` empezaba
con una marca BOM (U+FEFF) —la que escribe el Bloc de notas de Windows al
guardar como UTF-8—, que hacía que `ast.parse` lo rechazara y tumbaba de golpe
el validador de TMX, el calificador de jefes y una prueba del motor. Se retiró
la marca **y** se corrigieron las tres herramientas para que lean `utf-8-sig`:
el fichero era correcto; lo que no toleraba la marca eran mis herramientas.

El nivel en sí está bien planteado —200 × 38, 8 enemigos con dificultad
creciente, parallax e iluminación—. Casi todo lo que pierde son casillas de
metadatos y un checkpoint.

### José Jahel Morales Briceño — jefe Venado — 100 %

Perfecto en las diez casillas: 6 métodos de ataque, 5 indicadores de fase, 2
umbrales de vida, telegrafiado, puntos débiles, `apply_hit` y 9 interacciones
con eventos. **Sustituye a la implementación de referencia del profesor**, por
decisión tomada al revisar el lote.

### Alejandro Josué Rodríguez Zamora — jefe Paburu — 100 %

También perfecto: 4 ataques, 3 indicadores de fase, 7 umbrales de vida,
telegrafiado. Siete módulos bien separados —arena, sprites, intro, guardianes,
ataques de la forma 1— y las cuatro formas cargadas con sus teclas de depuración
para poder enseñarlas. Es el paquete cuyo desglose destapó el defecto 3 de
arriba.

Único apunte: registra `BossPaburu` dentro de una función. Al jugar funciona,
pero el previsualizador no puede abrir su arena suelta.

### Jefe El Rey Terciopelo — 50 %

La plantilla llegó **sin nombre de estudiante** (`Student Name: PABLO`, sin
rellenar). Hay que asignarlo antes de cerrar actas.

Lo que le falta:

- **Ningún ataque reconocido (−15).** Sí tiene uno implementado
  —`_update_venom_spit`, el escupitajo de veneno—, pero la rúbrica busca
  métodos con `attack` en el nombre o declarados en `BossPhase(attacks=[...])`.
  Renombrar el método, o declararlo en la fase, recupera los 15 puntos enteros.
- Sin transiciones de fase (−15) y con un solo umbral de vida (−5). El README
  dice que las fases 2 y 3 quedan para la Práctica II; la rúbrica de esta
  entrega pide al menos dos.
- Sin telegrafiado (−10).
- Una sola referencia a eventos (−5).

Igual que Paburu, registra `BossRey` dentro de una función.

---

## Patrones del grupo

Cosas que se repiten y que conviene corregir en clase antes de la Práctica II:

| Fallo | A cuántos afecta |
|---|---|
| Falta la propiedad de mapa `author` | 7 de 10 |
| Plataformas sin ruta desde el spawn | 5 de 10 |
| Demasiada distancia entre checkpoints | 5 de 10 |
| Falta `climate` (−5 automáticos) | 4 de 10 |
| Repechos más altos de lo que salta el jugador | 4 de 10 |
| `register_entity` dentro de una función | 3 de 14 |
| Sin estado de telegrafiado | 2 de 4 jefes |

Los dos primeros son dos campos en Tiled y valen hasta 15 puntos. Es lo más
barato que pueden recuperar.

Los repechos imposibles merecen media clase: el alcance real de un salto es
**~43 px horizontales**, no los ~85 que sugiere la velocidad de suelo, porque el
controlador aplica la mitad de la velocidad en el aire. Sólo una entrega lo
detectó y lo dejó escrito.

---

## Estado del repositorio

- 14 escenarios cargan y dibujan cinco fotogramas sin lanzar.
- 14 de 15 mapas pasan `validate_tmx.py`; el que falla es el de Saúl, por
  propiedades de mapa ausentes.
- El orden de juego queda: 1-1 → 1-2 → 1-3 → Venado → 2-1 → **2-2** → 2-3 → Rey
  → 3-1 → **3-2** → 3-3 → Gavilán → Paburu.

## Cómo reproducir estas notas

```bash
python scripts/validate_tmx.py assets/maps/
python scripts/grade_stage.py assets/maps/<escenario>/<escenario>.tmx
python scripts/grade_boss.py src/stages/<jefe>
```
