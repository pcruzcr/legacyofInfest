# Custom Stage Design — Student Worksheet

**Student Name:** Jose Pablo Monestel Cruz
**Stage ID:** hall

---

## 0. Cómo ejecutar

Desde la raíz del proyecto (`legacyofInfest/`), con el entorno virtual ya
instalado (`.venv/`):

**Juego completo (menú principal, todos los stages):**
```bash
.\.venv\Scripts\python.exe main.py
```

**Directo al escenario Hall (sin pasar por el menú):**
```bash
.\.venv\Scripts\python.exe main.py --stage hall
```

En Linux/macOS, reemplazar `.\.venv\Scripts\python.exe` por
`.venv/bin/python`. También puede ejecutarse `python main.py` a secas si el
entorno virtual ya está activado (`.\.venv\Scripts\Activate.ps1`).

---

## 1. Descripción

**Nombre:** 3-2 — El Hall (Zona 3, Sede Heredia).

**Objetivo:** cruzar el vestíbulo colapsado e inundado de la Sede Heredia,
desde la entrada hasta la salida al fondo del edificio, usando solo
movimiento aéreo — el piso original ya no es una ruta segura.

**Concepto:** el Gavilán Camionero Mascarero ha reclamado el Hall como
territorio de caza. Su dominio sobre el edificio ha ido más allá de las
aves que lo patrullan: el peso de la infestación y los picados constantes
contra el piso de piedra agrietaron el mosaico original, que colapsó hacia
el sótano de servicio en varios tramos, y las tuberías rotas por el mismo
colapso inundaron el corredor que sigue. La puerta principal del fondo del
vestíbulo (visible como la reja sellada, tile `42`) quedó bloqueada por los
escombros — la ruta real ahora sigue por lo que queda del piso, no por
donde el hall fue diseñado originalmente para salir. No contradice el canon
de la Zona 3: `65_EL_LORE_EXTENSO.md` ya describe la Sede Heredia como "el
edificio donde el aire es de los que vuelan" y "no hay refugio: el cielo es
el techo y el techo observa".

**Mecánica principal:** parkour aéreo de riesgo — todos los enemigos son
aéreos, caer es letal (`DeathPit`), y el avance depende de leer el patrón de
vuelo de los halcones, cronometrar mecanismos del entorno (resortes,
bloques rítmicos, plataformas móviles, viento) y, en un tramo, nadar.

**Tamaño:** 2432×608px (152×38 tiles) — de los 1088px originales a esto, en
varias iteraciones (ver §4, Testing).

---

## 2. Estructura del recorrido

Verificado directamente contra el `.tmx` (no reconstruido de memoria) —
lista completa de objetos ordenada por X:

| Tramo | X | Qué exige |
|---|---|---|
| Entrada | 0–416 | Piso original, enemigos aéreos establecidos (`FlyingHalcon`, `ShooterBuitre`, `WalkerPalom`) |
| Corredor de Resortes | 416–624 | Salto normal → `Spring_hall_01` (impulso −520 px/s) → vacío que solo el resorte cruza |
| Piso largo + resorte bonus | 624–1120 | Piso continuo de 496px con 2 `WalkerPalom` y un desvío opcional: `Spring_hall_03` (x=1030) sube a `Platform_ResorteBonus` (y=390) con una moneda — no bloquea el paso, es recompensa por explorar |
| El Aljibe (agua) | 1120–1424 | Nadar (`WaterZone_hall` + `WaterZone_hall_2`, `SwimmingState`) — dos piscinas contiguas, 304px |
| Salida del agua | 1424–1600 | Dos vacíos de salto normal (`DeathPit_hall_C`, `_D`) con una plataforma-coleccionable entre ambos |
| Gauntlet de resortes | 1600–1984 | Dos resortes más (`Spring_hall_02` x=1648, otro en x=1728) sobre dos vacíos (`DeathPit_hall_E`, `_F`), más un tercer vacío (`_G`) — el tramo más denso en resortes del nivel |
| El Vestíbulo Roto | 1984–2432 | `RhythmBlock` en cascada (x3) → `MovingPlatform` oscilante → `ZonaDeViento` (empuja la mitad del tiempo; la solución es esperar la calma) → salida (`NextTrigger_04`, x=2384) |

**Checkpoints: 5** (verificados, x=448, 670, 1060, 1596, 2000), siempre antes
del tramo difícil que protegen, no antes del tramo fácil (tabla completa,
con qué protege cada uno, en §7).

---

## 3. Computación Gráfica I — dónde y cómo se aplicó cada concepto

### 3.1 Curvas y modelado (Unidad III)

Los `FlyingHalcon` (10 en total, verificado por conteo directo del `.tmx` —
5 originales tras la corrección de densidad de §4 + 5 agregados en las
extensiones) recorren un lazo cerrado construido a partir
de 4 `Waypoint` propios por halcón (`owner_id`), evaluado con
`CurveTools.build_bezier_path` — Catmull-Rom real, no una aproximación:

```
P(t) = 0.5 · [ 2·P1 + (−P0+P2)·t + (2·P0−5·P1+4·P2−P3)·t² + (−P0+3·P1−3·P2+P3)·t³ ]
```

La curva pasa exactamente por los 4 puntos declarados en el TMX, no solo
por sus extremos — es la misma mecánica que el motor ya usa para vuelo
Bézier en otros enemigos del juego, aplicada aquí con trayectorias propias
por sección (ver §3.2 más abajo) para que ningún tramo repita el patrón del
anterior.

"Modelado" en este proyecto es geometría de colisión + tiles, no mallas 3D:
la organización de plataformas, fosos y paredes (§2) es el modelado del
nivel, y su proporción/escala está verificada contra la física real de
salto del jugador (§3.2 de las notas técnicas, más abajo) — no a ojo.

### 3.2 Representación de escenas (Unidad IV)

8 capas obligatorias (`BG_Far`, `BG_Mid`, `BG_Near`, `Terrain`,
`Terrain_Detail`, `Objects`, `Collision`, `FG_Overlay`), extendidas de 68 a
152 columnas manteniendo la consistencia tile a tile en las tres
extensiones. La profundidad viene del piso original (balcón a dos alturas,
techo indestructible) más la progresión horizontal de las cuatro zonas de
§2 — cada una introduce **una** mecánica nueva antes de dejar la anterior
atrás, así que la jerarquía visual (qué mirar primero) cambia con la
mecánica: el resorte se lee solo, el agua ocupa toda la franja vertical
media, los bloques rítmicos/plataforma móvil están alineados con el piso.

### 3.3 Color y transparencia (Unidad V)

`LightPoolShimmer` (`light_shimmer.py`, nuevo) — tres charcos de luz sobre
la zona inundada (x=1170/1240/1310), uno de los cuales sigue narrativamente
del propio "charco de luz" que ya proyectan los tragaluces de la ficha
oficial de Hall (tile `15`, `luz_suelo`), ahora reflejado en el agua.

- **HSL, no RGB directo:** el matiz interpola entre 45° (ámbar cálido, la
  luz directa del tragaluz) y 200° (azul-verde frío, el agua profunda) con
  `ColorTools.hsl_to_rgb` — la misma función que ya usa `stage3_1` para su
  sombra de nube. Verificado en código (no a ojo): en ciclo=0.0 da
  `(203,172,77)` ámbar, en ciclo=0.5 da `(77,203,82)` verde, en ciclo=1.0 da
  `(77,161,203)` azul — el punto medio cae en verde porque la banda verde
  (90°-150°) está en el camino corto entre 45° y 200° en la rueda de color;
  no es un error, es exactamente cómo se ve luz cálida disolviéndose en
  agua fría.
- **Transparencia real:** cada charco se dibuja en una `Surface` con
  `pygame.SRCALPHA` propia (no un `blend_mode` global ni un color sólido
  que aparenta transparencia), con alfa oscilando entre 28 y 90 de 255 en
  una onda triangular — "respira" en vez de parpadear.

### 3.4 Texturas (Unidad VI/VII)

Un solo tileset, `tileset_gavilan_ciudad` (60 tiles, 16×16px, paleta fija de
16 colores, `assets/tilesets/tileset_gavilan_ciudad.png` + `.tsx`). El script
que lo generó (`tools/generate_tileset_gavilan_ciudad.py`) **no está en esta
copia del proyecto** — solo existe en la carpeta antigua no extraída del
`.rar` (verificado con `ls`, no asumido); el `.png`/`.tsx` sí están y son
los que carga `hall.tmx`, así que el tileset en sí funciona igual, pero no
se puede regenerar ni editar el script desde aquí. Las tres extensiones
reutilizan exactamente los mismos IDs de
tile del piso original (`1`=suelo, `6`=zócalo, `3`=muro) para que el piso
nuevo sea visualmente indistinguible del original — ninguna textura nueva,
coherencia total del material. Tabla completa de tiles en §5.

### 3.5 Animación (Unidad VI)

| Animación | Dónde | Cómo |
|---|---|---|
| Vuelo Bézier | 10 `FlyingHalcon` | Curva evaluada cada frame (§3.1) |
| Péndulo | `SwingingLamp` ×2 | `lerp` + `ease_in_out_quad` entre dos anclas (`decor_lamp.py`) |
| Charco de luz | `LightPoolShimmer` ×3 | Color HSL + alfa oscilando en onda triangular (§3.3) |
| Bloques rítmicos | `RhythmBlock` ×3 | Aparecen/desaparecen en cascada (offsets 0/0.6/1.2s) |
| Plataforma móvil | `MovingPlatform` ×1 | Oscila 64px entre dos puntos |
| Resorte | `Spring` ×4 | Anima el rebote al pisarlo (motor) — 1 en el corredor inicial, 1 en el desvío opcional del piso largo, 2 en el gauntlet de resortes (§2) |
| Sprites de jugador/enemigos | Todo el nivel | Animación de fotogramas del framework (`EnemyBase`/`EnemyFlying`/`Player`), automática |

Conteo verificado por búsqueda directa en el `.tmx` (`grep -c`), no de
memoria — es el mismo método que destapó el error de la tabla de §6.

Ninguna es puramente decorativa sin razón de ser: el péndulo y el charco de
luz están narrativamente anclados a los tragaluces reales del hall; el
resto son la mecánica de juego en sí, no un adorno aparte.

---

## 4. Testing — versión, prueba, problema, corrección

Historial real de iteración de esta entrega (no reconstruido después):

| # | Versión | Prueba | Problema encontrado | Corrección | Resultado |
|---|---|---|---|---|---|
| 1 | Corredor de resortes (416–1072) | Playtest del estudiante | Morían cerca del borde de los fosos, no solo al caer | `DeathPit` con margen horizontal de 8px respecto a cada plataforma sólida | Corregido, verificado con `StageLoader.load` |
| 2 | Igual | Playtest | Seguían muriendo al primer roce con la parte de arriba del vacío, no al llegar al fondo | `DeathPit` reducido a los 32px inferiores (`y=576`) en vez de los 80px completos desde el piso | Corregido en los 3 fosos del corredor |
| 3 | Igual | Playtest | El mismo problema en el foso *original* del mapa (preexistente, no creado en esta entrega) | Mismo ajuste aplicado por consistencia | Corregido |
| 4 | Extensión 1 (agua) | Carga con `main.py --stage hall` | El jugador abrió el archivo equivocado (carpeta antigua del proyecto, no la extraída del `.rar`) y vio una versión vieja | No era un bug del nivel — se verificó cuál `hall.tmx` cargaba cada copia y se confirmó la ruta correcta | Confirmado con `Get-Location` |
| 5 | Extensión 2 (vestíbulo roto) | `grade_stage.py` | El calificador no podía analizar el diseño (`ModuleNotFoundError`) | Faltaba `pydantic` en el entorno — instalado | El calificador corrió de verdad por primera vez, y de paso reveló un bug **preexistente** (repecho de 416px en (496,96)) ajeno a esta entrega, documentado y no corregido (fuera de alcance) |
| 6 | Todas | `grade_stage.py` | Aviso de ritmo: 642px sin checkpoint entre x=448 y x=1090 (máximo recomendado 500) | Checkpoint intermedio nuevo en x=650, justo tras cruzar el resorte | Peor tramo bajó a 530px (el agua completa sigue siendo un solo tramo largo, aceptado a propósito) |
| 7 | Todas | Playtest del estudiante | 3 de los 5 checkpoints estaban a solo 12-14px del borde de su plataforma — visualmente colgando sobre el vacío | Reubicados con margen real (mínimo 32px a cada lado, verificado calculando el tramo de piso fusionado bajo cada uno) | Los 5 checkpoints con margen ≥32px, confirmado por script |
| 8 | Todas | Playtest del estudiante | El tramo 1360-1424 (justo al salir del agua principal) era piso seco sin ningún desafío, entre dos huecos que sí matan | Convertido a una segunda `WaterZone` — nadas de nuevo antes de los huecos letales, en vez de caminar | Verificado: ya no aparece en la lista de pisos sólidos, la piscina principal y la nueva quedaron separadas por el aterrizaje de 1424-1456... 1456-1520 sigue seco (la plataforma del coleccionable) |
| 9 | Todas | `validate_tmx.py` + `grade_stage.py --json` + carga headless (`StageLoader.load`) tras cada cambio | Al mover el piso de seguridad del segundo tramo de agua a la capa `Objects` en vez de `Collision`, el validador lo rechazó (`type='Solid' no existe` — ese tipo solo es válido en `Collision`) | Movido a la capa correcta | `validate_tmx.py` en verde otra vez |
| 10 | Todas | Playtest del estudiante | Al bucear cerca del borde de la piscina (agachado, buceo), el jugador moría "en el aire sin haber caído" — el `DeathPit` de Gap1 estaba a solo 8px del borde del agua, y `SwimmingState` no se siente como "caer" | Margen del lado del agua duplicado (8→16px); además, nuevo `DeathPit` en el fondo de la piscina principal (x=1200-1232, el centro real del mapa) — bucear a fondo ahí mata, nadar normal no | Verificado con `StageLoader.load`: 12 fosos en total, ninguno a menos de 16px de una `WaterZone` |
| 11 | Todas | Playtest del estudiante | Los enemigos de la entrada (13 en 704px, ~54px de separación promedio) se sentían amontonados | Primera pasada: -2 enemigos. No bastó (seguía en ~54px). Segunda pasada: cada `FlyingHalcon` Bézier se movió junto con sus 4 `Waypoint` (mismo delta, para no romper el lazo de la curva) y los `WalkerPalom` se redistribuyeron en todo el tramo | Separación real ahora entre 40 y 280px (antes ~54px fijo); 16 enemigos totales, mismas 5 curvas Bézier intactas |
| 12 | Todas | Playtest del estudiante | La grieta de la Prueba 10 (fondo de la piscina) seguía matando sin que el jugador buceara a propósito | Causa real: en `SwimmingState` la gravedad reducida sigue empujando hacia abajo todo el tiempo — sin pulsar salto de nado repetidamente, **cualquiera** se hunde al fondo tarde o temprano, no solo quien bucea a propósito. La premisa de la Prueba 10 era incorrecta | `DeathPit_hall_Grieta` retirado por completo; el fondo de la piscina vuelve a ser un solo `Solid` continuo, sin trampa a mitad del agua |
| 13 | Todas | Playtest del estudiante | Pidió un resorte para subir a "la siguiente plataforma" cerca del checkpoint del agua | Coloqué `Spring_hall_03` + `Platform_ResorteBonus` + una moneda en x=980, cerca de un peldaño de la escalera original — pero el jugador nunca para ahí; siempre está junto al checkpoint (x≈1060) | El estudiante confirmó por captura de pantalla que estaba mal ubicado |
| 14 | Todas | Playtest del estudiante (con captura) | Resorte en el lugar equivocado (x=980, Prueba 13) | Reubicado el resorte + plataforma + moneda a x=1030-1060, junto al checkpoint real. De paso, se descubrió que el nombre `Spring_hall_03` ya lo usaba **otro** resorte existente en x=1728 (parte del gauntlet de resortes, §2) — renombrado para no confundirlos, sin tocar el que ya estaba | Verificado con `StageLoader.load`: plataforma bonus en (1030, 390, 48×16), sin colisión con la escalera original |
| 15 | Todas | Auditoría de documentación a pedido del estudiante | La tabla de checkpoints (§7) y de enemigos (§6) del README tenían **datos obsoletos** — 4 de los 5 checkpoints se habían movido en la Prueba 7 sin actualizar la tabla; `WalkerPalom` mostraba 5 posiciones viejas en vez de las 4 actuales; `ShooterBuitre` tenía un `352` que nunca existió; el conteo de `Spring` decía 1 cuando hay 4 (2 de ellos en un tramo —el "gauntlet de resortes"— que nunca se había documentado en §2) | Reconteo completo por `grep`/carga real del `.tmx` (no de memoria) y reescritura de §2, §3.5, §6 y §7 con los números verificados | Cada número de este documento ahora sale de una consulta ejecutada contra el archivo actual, no de lo que se recordaba haber hecho |
| 16 | Todas | Misma auditoría de documentación | §3.4 y §5 atribuían el tileset a `tools/generate_tileset_gavilan_ciudad.py` — pre-existente desde la Práctica I, no introducido en esta entrega | Verificado con `ls`: ese script no existe en esta copia del proyecto (solo en la carpeta antigua sin extraer del `.rar`); el `.png`/`.tsx` sí están y funcionan | §3.4 y §5 corregidas para no afirmar la existencia de un archivo que no está |
| 17 | Todas | `validate_tmx.py` + `grade_stage.py --json` + carga headless (`StageLoader.load`) tras cada cambio | — | — | Todas en verde en la versión actual (ver salida real abajo) |

**Resultado de las pruebas automatizadas en la versión actual:**

```
$ python scripts/validate_tmx.py assets/maps/hall/hall.tmx
  [OK] assets\maps\hall\hall.tmx
  1/1 passed

$ python scripts/grade_stage.py assets/maps/hall/hall.tmx --json
  score: 87.7% (ver desglose completo por categoría en el historial de
  la conversación de desarrollo; design_completable en 12/12 porque el
  nivel usa mecánicas de movilidad — resortes, agua, plataforma móvil —
  que el analizador de rutas no modela y no penaliza)
```

**Números actuales, verificados por consulta directa al `.tmx` (27 de agosto,
tras la Prueba 15):** tamaño 2432×608px · 5 checkpoints · 11 `DeathPit` · 4
`Spring` · 2 `WaterZone` · 3 `RhythmBlock` · 1 `MovingPlatform` · 1
`WindZone` · 4 `Pickup` · 16 enemigos (4 `WalkerPalom`, 2 `ShooterBuitre`, 10
`FlyingHalcon`) · 2 `SwingingLamp` · 3 `LightPoolShimmer`.

**Lo que falta probar y no puede verificarse sin pantalla real** (ver §6):
el estudiante debe jugar el recorrido completo, intentar romperlo a
propósito (§6) y grabar la evidencia — ninguna herramienta automatizada
puede confirmar que el nivel "se siente" bien, solo que es físicamente
posible.

---

## 5. Tileset Requirements

Tileset: `tileset_gavilan_ciudad` (60 tiles, 16×16px,
`assets/tilesets/tileset_gavilan_ciudad.png` + `.tsx`). Arte propio con
paleta fija de 16 colores. El script generador
(`tools/generate_tileset_gavilan_ciudad.py`) no está presente en esta copia
del proyecto — ver nota en §3.4 — pero el tileset resultante sí, y es el que
carga el `.tmx` sin problema.

| Tile ID | Description | Collision? |
|---|---|---|
| 1 (suelo_sup) | Piso — reutilizado en las 3 extensiones | Sí |
| 6 (zocalo) | Relleno/zócalo bajo el piso — reutilizado en las 3 extensiones | Sí |
| techo (objeto `Solid`, no tile) | Techo indestructible, extendido a 2432px de ancho | Sí |
| 8-10 (plat_izq/med/der) | Balcón y peldaños de escalera/plataformas | Sí (one-way) |
| 3 (muro) | Muros laterales — el muro derecho se movió 3 veces, siempre reutilizando el mismo tile | Sí |
| 7 (columna) | Columnas decorativas | No (visual, Terrain_Detail) |
| 12 (reja) | Barandal del balcón | No (visual) |
| 43-46 (marco_izq/der/sup, alfeizar) | Marcos de tragaluz y de la puerta | No (visual, FG_Overlay) |
| 54-55 (cortina_izq/der) | Cortinas de tragaluz | No (visual) |
| 15 (luz_suelo) | Charco de luz bajo cada tragaluz — origen narrativo de `LightPoolShimmer` (§3.3) | No (visual) |
| 16-39 (lej_*/med_*/cer_*) | Skyline de Heredia en parallax (3 profundidades) | No (fondo) |
| 48-51 (grieta_1/2, mancha) | Desgaste | No (visual) |
| 57-58 (cuadro, caja) | Props decorativos / obstáculos sólidos | No / Sí (caja cuando es obstáculo) |
| 42 (cruce) | Reja/tranca de la puerta sellada — ahora decorativa (§1), la salida real está más adelante | No (visual) |

## 6. Enemy / Entity Placements

Tabla verificada por conteo directo del `.tmx` en la versión actual — la
versión anterior de esta tabla tenía datos obsoletos (contaba 5 `WalkerPalom`
donde hoy hay 4, y un `352` en `ShooterBuitre` que nunca existió; ver §4,
Prueba 14).

| X | Y | Type | Properties |
|---|---|---|---|
| 176, 420, 660, 900 | piso | `WalkerPalom` (4) | Roster oficial del escenario (ficha `10_STAGE_3_2.md`); redistribuidos en la Prueba 11 de §4 |
| 224, 544 | balcón | `ShooterBuitre` (2) | Valores por defecto de la especie, sin cambios desde el original |
| 10 posiciones (160 a 2190) | banda de vuelo | `FlyingHalcon` (10) | `flight_mode` variado por tramo — `bezier` (original y gauntlet de resortes), `sine`, `dive`, `chase`, `patrol` (extensiones) |
| 420, 700 | y=96 (techo) | `SwingingLamp` (2) | No es objeto TMX — `Hall.on_stage_start()` |
| 1170, 1240, 1310 | y≈500-520 (sobre el agua) | `LightPoolShimmer` (3) | No es objeto TMX — `Hall.on_stage_start()` |

Total de enemigos: 16 (4 + 2 + 10).

## 7. Checkpoints

Posiciones verificadas contra el `.tmx` actual (se movieron 4 de los 5 en la
Prueba 7 de §4 — esta tabla ya refleja esa corrección, no la posición
original):

| ID | X | Protege |
|---|---|---|
| 0 | 448 | El corredor de resortes |
| 4 | 670 | Justo tras cruzar el resorte inicial (agregado en la Prueba 6 de §4 — cerraba un tramo de 642px sin checkpoint; reubicado en la Prueba 7 por margen de borde) |
| 1 | 1060 | El desvío del resorte bonus y el tramo de agua |
| 2 | 1596 | El gauntlet de resortes tras el agua |
| 3 | 2000 | El vestíbulo roto (bloques, plataforma móvil, viento) |

---

## 8. Notas técnicas heredadas (geometría original, sin cambios)

- **Hueco central en el balcón (3 tiles, x=304-352):** el balcón corrido se
  parte en dos tramos con un vacío en el medio — el jugador puede saltarlo
  (48px, salto cómodo) o dejarse caer de vuelta al piso. Lee como daño
  causado por El Gavilán. Bordes marcados con `grieta_1`/`grieta_2`.
- Columnas y barandal del balcón son solo visuales (capa `Terrain_Detail`),
  sin colisión.
- **Envolvente de salto real (verificada con el mismo integrador físico del
  juego, no estimada):** gravedad 800px/s², impulso de salto −380px/s →
  alcance natural (sujetando dirección) **42.75px**, alcance experto
  (soltando dirección al despegar) **85.5px**. Con el `Spring`
  (impulso −520px/s): alcance natural **58.5px**, experto **117px**. Toda
  la geometría de fosos de esta entrega está calibrada contra estos números
  reales, no contra la estimación por defecto del analizador.
- **Caja obstáculo cerca del spawn (col 6):** sólida, entre las dos
  primeras plataformas de la escalera.
- **Nota técnica — por qué `SwingingLamp` y `LightPoolShimmer` no son
  objetos TMX:** `scripts/grade_stage.py` analiza el TMX sin importar el
  módulo Python del stage, así que nunca puede conocer un tipo de entidad
  registrado solo por el propio stage — un objeto de tipo desconocido en la
  capa `Objects` dispara `FrameworkUsageError` en su análisis y pone en
  cero varias categorías de la rúbrica automática para todo el archivo.
  `Hall.on_stage_start()` las instancia directamente en Python, el mismo
  patrón que usa el propio motor para los esbirros que invoca un jefe.

## 9. Reflection

Lo más difícil de esta entrega no fue el arte ni la geometría: fue calibrar
mecánicas nuevas (resorte, viento, agua) contra la física **real** y
verificada del jugador en vez de contra la intuición — el viento, por
ejemplo, se calculó leyendo directamente `sistema_viento` en
`src/framework/ecs/systems.py` para confirmar que la fuerza es aceleración
periódica (sopla la mitad del tiempo) y no velocidad fija, antes de decidir
el ancho del vacío que cruza. El entorno de desarrollo también dio su
propia lección: el `.venv` que traía el `.rar` apuntaba a un Python de otra
máquina y no funcionaba aquí, y `grade_stage.py` llevaba fallando en
silencio por falta de `pydantic` — ambos se arreglaron antes de poder
confiar en cualquier resultado de prueba. Con más tiempo, grabaría el
video de evidencia con varias corridas fallidas incluidas a propósito (caer
en cada foso, perder el resorte, cruzar el viento en el momento
equivocado), porque son esas fallas — no solo el recorrido exitoso — las
que demuestran que la dificultad es intencional y no accidental.
