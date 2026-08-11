---
document_id: "LOI-ESTADO-62"
title: "Estado del proyecto — qué hay, qué mejorar, qué falta"
tags: ["estado", "inventario", "hoja-de-ruta"]
source: "docs/62_ESTADO_DEL_PROYECTO.md"
date_processed: "2026-08-01"
---

# Estado del proyecto — qué hay, qué mejorar, qué falta

**Fecha:** 1 de agosto de 2026
**Método:** todo lo de aquí está medido o leído del código. Donde no he podido
medir, lo digo.

---

## Cómo leer este documento

Tres listas, y la diferencia entre ellas importa:

* **A — Implementado y verificado.** Existe, se alcanza desde el juego y hay
  una prueba que falla si se rompe. Las tres condiciones. Este mes se
  encontraron **siete sistemas** que cumplían la primera y no la segunda.
* **B — Implementado y mejorable.** Funciona, y hay un techo conocido.
* **C — No implementado.** Separado en lo que conviene hacer y lo que
  conviene **no** hacer, porque decidir no hacer algo también es una decisión
  de ingeniería y se olvida antes.

---

<a id="a"></a>
## A. Implementado y verificado

### Núcleo del motor

| Sistema | Estado |
|---|---|
| Bucle a 800 × 600 y 60 FPS | resolución interna fija, escalada a la ventana |
| **Tres relojes** | `dt` (escalado), `dt_mundo` (sin hit-stop), `unscaled_dt` (real) |
| Composición de escalas de tiempo | cada efecto registra su factor con su nombre; el resultado es el producto |
| Tope de fotograma | `MAX_FRAME_TIME = 0.05`: un tirón hace el juego lento, no roto |
| Bus de eventos | por inyección, sin global |
| Contenedor de escenas | `SceneRegistry` con carga perezosa |

### Arquitectura

* **ECS por debajo de la herencia.** `World`, componentes y sistemas con fases
  explícitas y borrado diferido. Los **17 escenarios y 4 jefes del árbol**
  funcionan sobre él. *(La anulación parcial de 2026-08-07 —CLAUDE.md, "26
  clases de escenario"— suspende la restricción histórica; el recuento actual
  del árbol es el que manda.)*
* **Componente-como-vista.** `Transform` y `Salud` leen del dueño en vez de
  guardar copias. Es la respuesta durable a «dos copias que hay que
  sincronizar».
* **Coste medido:** 9,07 ms frente a 9,42 ms por fotograma con y sin el puente.

### Jugador

26 estados: suelo, aire, ataque, defensa, agarre, nado y daño. Salto medido en
**72 px**, que es el número con el que se decide si un obstáculo cabe.

### Enemigos y jefes

* **30 tipos registrados** sobre ocho arquetipos, con **13 estados** incluido
  `TELEGRAPHING`.
* **Cerebro de escuadrón** con scikit-learn: predicción por lote, cadencia
  limitada y escalonada. Medido: 9 filas cuestan 1,82 ms en lote contra 11,87
  una por una.
* **Jefes:** fases, telegrafiado, puntos débiles, parry, invocaciones,
  teletransporte y límites de arena.
* **Bullet hell en NumPy:** 2000 balas, **12,94 ms → 0,072 ms** (180×).

### Escenarios y TMX

**78 tipos de objeto en runtime** (39 integrados del framework + 37 del
registro una vez descubiertos los escenarios, más `Solid` y `Platform` en
`Collision`; la referencia de estudiantes `STAGE_CREATION.md` cuenta el
registro base sin descubrir: 69, y `check_tmx_coverage.py` cuenta
base+collision: 71), **18 propiedades de mapa**, 8 capas. Incluye las once
mecánicas de la fase 5 —viento, fricción, cinta, láser, onda, agua, plataforma
móvil, hundible, bloque rítmico, liana, tirolesa— más sigilo con cono de visión
y perseguidor, y los cuatro interactivos de F4.1.

### Presentación

Iluminación por focos, bloom, viñeta, clima, partículas de ambiente, ciclo
día/noche, estaciones, niebla de guerra, efecto de agua, estelas, números de
daño y efectos de impacto. Todo configurable desde Tiled sin escribir Python.

### Persistencia y seguridad

* Guardado atómico con `fsync` y `os.replace`.
* **Trece entradas hostiles probadas**, ninguna rompe nada.
* Sin `eval`, `exec`, `os.system` ni `shell=True`. Sin travesía de rutas.
* `pip-audit` en cada push y Dependabot semanal.

### Accesibilidad

| Ayuda | Qué hace |
|---|---|
| Daltonismo | cuatro modos, aplicados en el post-procesado |
| Escala de texto | 1,0× a 2,0×, aplicada en el único embudo de fuentes |
| Movimiento reducido | atenúa al 25 %; **no elimina**, para no borrar información |
| Pulsar en vez de mantener | conmutador para las acciones sostenidas |
| Foco no dependiente del color | fila elevada + cursor + brillo, tres señales |
| Contraste | 8,9:1 medido, sobre el mínimo AA de 4,5:1 |

### Herramientas del profesor

`preview_tmx.py`, `validate_tmx.py`, `grade_stage.py` (130 puntos),
`grade_boss.py`, `check_tmx_coverage.py`, `check_dependency_sync.py`,
`check_translations.py`.

### Calidad

* **4.751 casos** recogidos (`pytest --collect-only -q`, 2026-08-11).
* 84 pruebas de humo que **arrancan, actualizan y dibujan** cada escena
  (`test_scene_smoke.py` y `test_stage0_smoke.py`).
* `ruff` limpio, `mypy` en CI con trinquete, validadores en CI.
* Stage 0: **130/130**. Los **17 escenarios del árbol**, integrados y
  calificados (media 79,0 % con `grade_stage.py`).

---

<a id="b"></a>
## B. Implementado y mejorable

Ordenado por lo que más sube la calidad percibida.

### B1. Dibujado — el 63 % del fotograma

Medido en 600 fotogramas de stage 0:

| Fase | Coste | % |
|---|---|---|
| Dibujado | 6,26 ms | **63 %** |
| `blit` (58 por fotograma) | 2,93 ms | 29 % |
| Post-procesado | 2,18 ms | 22 % |
| — bloom | 1,55 ms | 15 % |
| Actualización | 2,08 ms | 21 % |

Dos cosas concretas: **no hay atlas de sprites** —58 blits sueltos— y el
post-procesado se hace **en CPU sobre superficies**, con `gl_pipeline.py`
(1.100 líneas con sus sombreadores) ya escrito y sin usarse para esto.

### B2. `stage_scene.py` — 1.245 líneas

Carga, actualiza, dibuja, gestiona VFX, agarres, interactuables y cámara. Es un
objeto-dios y es donde se toca casi cualquier cambio, así que también es donde
más fácil es romper algo sin querer. Se parte en cuatro o cinco colaboradores.

### B3. Alcance del comprobador de tipos

`mypy` entró en CI con **2 paquetes de unos 15** y hoy el trinquete tiene
**6** (`mypy_scope.txt`, AUD-371): core, input, audio, ui, utils y
framework/physics. La lista existe justamente para ir subiendo; el trabajo es
real pero mecánico.

### B4. Cobertura de pruebas ~48 %

El número importa menos que **dónde** está el hueco. No hay medición reciente
por módulo porque el entorno de auditoría no aguanta `pytest-cov` sobre el
árbol entero.

### B5. Documentación atada al código: sólo una de 95

`docs/60` tiene 22 pruebas que comparan sus cifras con el motor. Las otras 94
no tienen nada, y este mes **tres documentos** resultaron describir cosas que
no existen. Extender el patrón a las especificaciones (05, 06, 17) es el
siguiente paso obvio.

### B6. Localización

| | Documentos |
|---|---|
| Sólo español | 28 |
| Sólo inglés | 66 |
| Genuinamente bilingües | **2** |

Los catálogos de interfaz sí están completos (2.767 literales medidos por
`check_translations.py`, `es` y `en`).

### B7. Stage 0 usa 4 de las 11 mecánicas

Liana, tirolesa, bloques rítmicos y viento. Las otras siete viven en
`stage_mecanicas`, que es un laboratorio y no un nivel.

### B8. Tipos de objeto que ningún mapa usa

Eran 15, y eran **17** (AUD-153): siete de escenario y diez especies del
bestiario. Se colocaron en las salas 8 y 9 del laboratorio
(`stage_mecanicas`). Hoy el único sin uso es `BossSpawn` en su forma
indirecta —los cuatro jefes se colocan con su tipo directo—, medido por
`check_tmx_coverage.py`.

### B9. La curva de dificultad de los 15 escenarios nunca se ha medido

El arnés de playtest existe. Falta que produzca un informe comparativo.

### B10. Dos huérfanos sin decidir

`DialogueAction` del sistema de cutscenes —un estudiante escribió literalmente
«no se usa el `DialogueAction` del motor» y se hizo el suyo, lo que sugiere que
o no sirve o no se encuentra— y `GhostData` del modo speedrun. Los dos
necesitan una decisión de producto antes que de código.

### B11. `pip-audit` no bloquea

Está en `continue-on-error` a propósito: un CVE en una transitiva no debe
bloquear la entrega de un estudiante a las once de la noche. Cuando el equipo
tenga costumbre de mirarlo, se sube a bloqueante.

---

<a id="c"></a>
## C. No implementado

### C1. Lo que conviene hacer

#### Reloj musical (la fase F6)

**Nada del motor está atado a la música.** Cada objeto rítmico acumula su
propio temporizador en segundos y no hay concepto de BPM, compás ni posición de
la pista. Falta:

| Pieza | Por qué |
|---|---|
| Reloj alimentado por la posición de la pista | acumular `dt` deriva del reloj de audio; ocho minutos de nivel acaban fuera de compás |
| `bpm` y `compas` como propiedades de mapa | a 128 BPM un tiempo son 0,46875 s y nadie escribe eso en cuarenta bloques |
| Objetos cuantizados a compás | `beats_visible` en vez de `visible_seg` |
| Compensación de latencia | 20–60 ms entre mezclador y altavoz; sin ella todo «a tiempo» se siente tarde |
| Línea de tiempo de coreografía | las cutscenes van en segundos y **bloquean** el juego |
| Pulso visual | cámara, escala y luz al compás |

AUD-119 quitó el obstáculo técnico: el hit-stop ya no desincroniza la
maquinaria del nivel.

#### Audio

Sin buses de mezcla, sin *ducking*, sin reverberación por zona. La música
dinámica cambia de pista por intensidad, no mezcla capas con precisión de
muestra.

#### Renderizado

Atlas de sprites, *batching*, y llevar el post-procesado a la tubería GL que ya
existe.

#### Calidad

Mutación en CI, prueba de resistencia larga, SBOM, y subir la cobertura donde
esté baja de verdad.

### C2. Lo que conviene NO hacer

Estas son decisiones, no olvidos.

#### 3D en pygame — **no**

Lo que hay son 1.100 líneas de tubería GL para post-procesado, **no un
renderizador 3D**: sin grafo de escena, sin sistema de materiales, sin
*culling*, sin sombras, sin animación esquelética, sin importador de mallas.
Construirlo son unos dos años de una persona y el resultado sería peor que
Godot gratis. Si el 3D llega a ser un requisito, el camino es portar a Godot o
Unity y quedarse con este motor como la herramienta con la que se enseña la
teoría.

**2.5D sí es alcanzable**: capas por profundidad, escalado en Z y mapas
normales sobre la superficie GL que ya existe.

#### Traducir los 95 documentos — **no**

Serían 190 ficheros que mantener sincronizados, y el modo de fallo dominante de
este proyecto —medido cuatro veces este mes— es exactamente que un documento se
separe de la realidad. La única pareja bilingüe que ya existía llevaba meses
mintiendo por los dos lados: el README decía **1.333** pruebas en español,
**640** en inglés, y había **2.020**.

La política implementada es bilingüe **donde hay lector**: la puerta de entrada
y los informes publicables; español para el material del curso.

#### Lintear el código de los estudiantes — **no**

Trae 164 avisos de estilo. Es su código y su nota; el CI los excluye a
propósito, porque un equipo que se acostumbra a un CI en rojo deja de mirarlo.

#### Perseguir el 100 en todas las categorías — **no**

Un 100 significaría «no queda ninguna mejora posible», y eso no es cierto de
ningún software vivo. El techo realista por categoría está en
`89_AUDITORIA_MULTIDISCIPLINAR.md`; la media alcanzable es **94**.

---

## Resumen en una tabla

| Área | Hay | Mejorable | Falta |
|---|---|---|---|
| Motor y arquitectura | ECS, 3 relojes, escalas componibles | `stage_scene` de 1.245 líneas | — |
| Jugador | 26 estados | — | — |
| Enemigos | 30 tipos, 13 estados, IA por lote | tipos sin usar en ningún mapa: sólo `BossSpawn` indirecto | — |
| Jefes | fases, telegrafiado, puntos débiles | variedad entre jefes | — |
| Escenarios | 78 tipos TMX en runtime (69 base), 11 mecánicas | stage 0 usa 4 de 11 | — |
| Gráficos | luz, clima, VFX, post-procesado | atlas, batching, post en GPU | 2.5D |
| Audio | música dinámica, ambiente, posicional | — | **reloj musical**, buses, ducking |
| Accesibilidad | 4 ayudas conectadas | — | — |
| Persistencia | atómica y endurecida | — | — |
| Calidad | 4.751 pruebas, CI con 5 puertas | cobertura, mypy, docs atadas | mutación, resistencia |
| Localización | catálogos completos | 66 documentos en un idioma | — |

---

## Las tres cosas que yo haría primero

1. **F6, el reloj musical.** Es lo único que bloquea una categoría entera
   (audio, 78) y abre un tipo de nivel que hoy no se puede hacer.
2. **Atlas y post-procesado en GPU.** Ataca las dos notas más bajas después de
   localización, y es lo que más cambia lo que se ve en pantalla.
3. **Extender las pruebas de documento↔código** a las tres especificaciones que
   los estudiantes leen. Este mes tres documentos resultaron ser ficción; el
   coste de que uno de ellos sea el que se estudia es alto.

---

## Documentos relacionados

- [[60_GUIA_COMPLETA_DEL_MOTOR.md|Manual del diseñador]]
