---
assignment_type: stage
assignment_name: "La Entrada de Piedra"
assignment_id: "stage3_1_la_entrada_de_piedra"
zone: 3
student_name: "Avril"
units_demonstrated: [II, III, IV, V]
evaluation_milestone: "Evaluación Práctica I"
---

# Stage 3-1 — La Entrada de Piedra

## 1. Concepto del escenario

El camino de entrada a la sede INVENIO Heredia: un tramo de piedra/adoquín
bordeado de césped que cruza por debajo de dos secciones de pasillo techado
(pérgola), inspirado directamente en una fotografía real de la entrada del
campus (edificio principal gris grafito con bloque de acento terracota,
ala secundaria más clara, césped y camino curvo). El jugador recorre el
camino de izquierda a derecha, enfrentando enemigos de la Zona 3 (aves
infestadas) mientras usa dos jardineras elevadas y cuatro plataformas
adicionales como cobertura y como recorrido de salto.

**Tamaño del mapa (1600×224px, 100×14 tiles):** el mapa se amplió más
allá del mínimo del enunciado (~560px) para que la cámara del motor
pudiera desplazarse de verdad. La ventana interna del juego mide 800×600
(`settings.INTERNAL_WIDTH/HEIGHT`), y `Camera.update()` fija el
desplazamiento (`offset`) en `max(0, min(offset, map_size - screen_size))`
— con un mapa más chico que la pantalla, ese cálculo colapsa siempre a 0 y
la cámara queda fija. Se verificó que este mismo comportamiento numérico
lo tienen también `boss_venado.tmx` (640×320) y la propia plantilla
oficial (640×224): ambos son más chicos que 800×600 y por lo tanto
tampoco haría scroll. Con 1600px de ancho, el offset de cámara sí varía
de verdad durante el recorrido.

## 1.1 Instrucciones de uso

**Ubicación requerida:** esta carpeta completa (`stage3_1_la_entrada_de_piedra/`,
con `__init__.py`, `stage3_1_la_entrada_de_piedra.py`,
`stage3_1_la_entrada_de_piedra.tmx` y este `README.md`) debe estar dentro de:
```
src/stages/stage3_1_la_entrada_de_piedra/
```
al mismo nivel que `stage0/` y `boss_venado/`. No requiere ningún otro
archivo ni recurso fuera de esta carpeta y de los ya existentes en el
repositorio (`assets/`, `src/engine/`, `src/framework/`).

**Cómo ejecutarlo:**
1. Abrir una terminal en la carpeta raíz del proyecto (la que contiene
   `main.py`).
2. Ejecutar:
   ```
   python main.py --stage stage3_1_la_entrada_de_piedra
   ```
3. El juego abre directamente en este escenario, listo para jugar.

**Controles:** los mismos del resto del proyecto (movimiento, salto,
ataque) — no se modificó el sistema de input.

**Recorrido esperado:** el jugador aparece en `PlayerSpawn_01`, camina
hacia la derecha con la cámara siguiéndolo, cruza dos secciones de
pérgola (cada una con un `ShooterQuetzal` encima), usa dos jardineras y
cuatro plataformas para saltar y tomar cobertura, pasa por un checkpoint
a mitad de camino, y termina el nivel al llegar a `NextTrigger_01`.

**Requisito de entorno:** el proyecto ya debe tener sus dependencias
instaladas (`pygame-ce`, `pytmx`, `pyscroll`, etc., según
`requirements`/`requirements.lock` del repositorio del profesor) — este
escenario no agrega ninguna dependencia nueva.

## 2. Requisitos del tileset

| Tile ID (gid) | Tileset | Descripción | ¿Colisión? |
|---|---|---|---|
| 0 | — | Vacío / aire | No |
| 1 | `tileset_heredia_stone` | Piedra base — superficie del camino (`Terrain`) | Sí (vía objeto `Solid_Floor`) |
| 3 | `tileset_heredia_stone` | Gris oscuro — fachada del edificio (`BG_Far`) y postes de la pérgola (`BG_Near`) | No |
| 2 | `tileset_heredia_stone` | Gris claro — ala secundaria del edificio (`BG_Mid`) | No |
| 6 | `tileset_heredia_stone` | Marrón — viga de la pérgola (`FG_Overlay`) y cuerpo de las jardineras (`Terrain_Detail`) | No |
| 7 | `tileset_heredia_stone` | Terracota — acento del edificio (`BG_Far`) y superficie de las jardineras (`Terrain_Detail`) | Sí (jardineras, vía objeto `Platform`) |
| 5 | `tileset_heredia_stone` | Azul — cielo (`BG_Far`) | No |
| 65 / 66 | `tileset_planicie` | Verde — césped que bordea el camino (`Terrain_Detail`) | No |
| 67 | `tileset_planicie` | Verde oscuro — copas de los árboles ornamentales (`BG_Near`) | No |

## 3. Enemigos y objetos

| X (aprox.) | Y | Tipo | Notas |
|---|---|---|---|
| 300 | suelo | `WalkerGarza_01` | Primer enemigo; margen amplio desde el spawn |
| 700 | suelo | `WalkerGarza_02` | Tras el primer arco, antes del checkpoint |
| 1160 | suelo | `WalkerGarza_03` | Tras el segundo arco |
| 1490 | suelo | `WalkerGarza_04` | Cierre, combina con el último Halcón |
| 420 | alto | `FlyingHalcon_01` | Patrulla senoidal, sola |
| 1000 | alto | `FlyingHalcon_02` | Cerca del segundo arco |
| 1350 | alto | `FlyingHalcon_03` | |
| 1480 | alto | `FlyingHalcon_04` | Cierre del nivel, combina con Garza 4 |
| 616 | viga arco 1 | `ShooterQuetzal_01` | Estacionario, sobre la pérgola |
| 1096 | viga arco 2 | `ShooterQuetzal_02` | Estacionario, sobre la pérgola |
| 140-172 | y=160 | `Plataforma_01` | Salto libre, sin enemigos cerca |
| 520-552 | y=160 | `Plataforma_02` | Lleva hacia la Jardinera 1 / Arco 1 |
| 930-962 | y=160 | `Plataforma_03` | Tramo abierto tras el checkpoint |
| 1280-1312 | y=160 | `Plataforma_04` | Lleva hacia el tramo final |

Con el mapa ampliado, los enemigos quedaron mucho más espaciados que en el
diseño original — solo hay una combinación real de dos tipos (Garza+Halcón
al final); el resto del recorrido presenta un enemigo a la vez, con tramos
limpios largos entre cada uno, para una dificultad más suave.

## 4. Checkpoints

| ID | X | Y |
|---|---|---|
| 0 | 784 | 160 |

## 5. Notas de lógica personalizada

- **Ningún enemigo fue subclasificado ni registrado manualmente.** Los tres
  usan las especies ya existentes en `bestiary_registry.py`
  (`WalkerGarza`, `FlyingHalcon`, `ShooterQuetzal`), colocadas por `type`
  en la capa `Objects`. `StageLoader._entity_registry` nunca se modifica,
  ni siquiera temporalmente.
- **`WalkerGarza_01`** está a x=300, muy por encima del umbral de
  `detection_range_x=160` de `EnemyWalker` respecto al spawn (x=48) — con
  el mapa ampliado hay margen de sobra antes del primer enemigo.
- **Jardineras (`Platform`, unidireccionales):** dan cobertura real contra
  la picada del `FlyingHalcon` (su picada fija el ángulo una sola vez;
  reposicionarse en la jardinera puede hacerla fallar). **No** bloquean
  físicamente los proyectiles del `ShooterQuetzal` — se confirmó en
  `enemy_shooter.py._post_update` que los proyectiles solo comprueban
  colisión contra `_collision_rects` (el suelo sólido), nunca contra
  `_one_way_rects`. Contra el Quetzal, la jardinera funciona como elemento
  de reposicionamiento fuera de la línea de tiro, no como escudo físico.
- **Vuelo de los `FlyingHalcon` a gran altura (origen y≈24):** el rebote
  horizontal de `SineFlight` está fijado en el código (`if abs(dx) > 96.0`,
  no configurable por especie), y las columnas de la pérgola ocupan casi
  todo el espacio vertical de vuelo disponible. Volando por encima de las
  columnas (que empiezan en y=48) se evita cualquier choque visual con la
  estructura sin tener que rediseñar la geometría ya construida.

## 6. Unidad II — Sistemas de coordenadas y vectores

Cada `ShooterQuetzal` vivo comprueba, cada fotograma, su distancia al
jugador con aritmética vectorial explícita (no con su propia lógica
interna de disparo, que se deja intacta):

```
d = vec2_distance(quetzal.position, player.position)
       = √((player.x − quetzal.x)² + (player.y − quetzal.y)²)

dir = vec2_normalize(player.position − quetzal.position)
       = (player.position − quetzal.position) / |player.position − quetzal.position|
```

El resultado de `d` no solo decide si se dibuja una línea de
telegrafiado: decide si el jugador **acaba de entrar** en rango de
disparo (≤180px) y, en ese caso —solo en el flanco de entrada, no en
cada fotograma que permanezca dentro—, dispara un aviso real en pantalla
vía `Events.SHOW_MESSAGE` (el mismo mecanismo de `MessageBox` que usa el
resto del juego). Es decir, el cálculo vectorial determina una decisión
observable (mostrar el aviso una vez), no solo un dato para dibujar.
`dir` se usa además para orientar la línea de telegrafiado. Implementado
en `_update_quetzal_telegraphs`, usando `vec2_distance` y
`vec2_normalize` de `src/engine/utils/math_utils.py`.

## 7. Unidad III — Curvas

Un farol decorativo oscila junto al primer arco siguiendo una curva
Catmull-Rom (`CurveTools.build_bezier_path`) sobre 4 puntos de control:

```
P0 = (592, 60)    P1 = (612, 92)    P2 = (628, 92)    P3 = (648, 60)
```

El parámetro `t ∈ [0,1]` avanza con una onda triangular (ida y vuelta) en
vez de reiniciarse de golpe, para que el movimiento se vea continuo. Con
el mapa ampliado, el farol quedó como un adorno local del primer arco (en
vez de abarcar la distancia mucho mayor entre los dos arcos). Esta curva
es independiente del vuelo senoidal del `FlyingHalcon` (que usa
`math.sin` directo, no `CurveTools`), por lo que la Unidad III queda
demostrada en un elemento propio y separado. Implementado en
`_update_curve_ornament` / `_draw_curve_ornament`.

## 8. Unidad IV — Representación gráfica, capas y animación

Las 8 capas obligatorias (`BG_Far`, `BG_Mid`, `BG_Near`, `Terrain`,
`Terrain_Detail`, `Objects`, `Collision`, `FG_Overlay`) están completas:
cielo y fachada del edificio en `BG_Far`, ala secundaria en `BG_Mid`,
postes de la pérgola y árboles en `BG_Near`, camino de piedra en
`Terrain`, césped y jardineras en `Terrain_Detail`, viga de la pérgola en
`FG_Overlay` (cruzando por delante, correctamente en primer plano). Los
tres enemigos usan sprites de la Zona 3 ya existentes en
`assets/sprites/enemies/zone3/`, con animación multi-fotograma manejada
automáticamente por `EnemyBase`/`EnemyFlying`/`EnemyShooter` — no hace
falta código de animación propio. El orden de dibujo (jugador, enemigos y
checkpoints por `rect.centery`) lo gestiona `DrawingSystem`, sin
modificaciones.

## 9. Unidad V — Color (HSL)

Una nube visible (dibujada como tal, no solo inferida por un cambio de
tinte) recorre el mapa de un extremo a otro y de vuelta. La sombra que
proyecta se calcula en función de la distancia real entre la nube y el
jugador —no de un cronómetro desacoplado—, así que la causa (la nube) y
el efecto (la sombra) están visiblemente conectados:

```
shade = max(0, 1 − |player.x − cloud.x| / 150)      (1 = nube justo encima)
hue   = 45° + (215° − 45°) · shade      (amarillo cálido → azul frío)
light = 0.80 + (0.40 − 0.80) · shade    (más luz → más sombra)
(r, g, b) = ColorTools.hsl_to_rgb(hue, 0.35, light)
```

El color resultante se aplica como una superposición semitransparente
sobre toda la escena (alpha entre 10 y 130 sobre 255 — claramente visible
cuando la nube está encima, casi imperceptible cuando está lejos).
Implementado en `_draw_cloud_shadow` / `_draw_cloud_shape`, usando
`ColorTools.hsl_to_rgb` de `src/framework/processing/color_tools.py`.

Además, se sobreescribieron `ambient_light=0.85`, `bloom=0.15` y
`vignette=0.20` en las propiedades del mapa: los valores por defecto de
Zona 3 (`AMBIENT_BY_ZONE`, `BLOOM_BY_ZONE`, `VIGNETTE_BY_ZONE` en
`StageScene`) están pensados para tramos oscuros de interior, y este
escenario es un exterior diurno y nublado.

## 10. Reflexión

Lo más difícil fue descubrir que varias restricciones del motor (rango de
detección fijo, rebote de vuelo fijo, proyectiles que ignoran las
plataformas unidireccionales) no estaban documentadas donde se esperaría,
y solo se confirman leyendo el código fuente directamente. Verificar cada
supuesto contra `src/framework/` antes de dar una posición o un
comportamiento por bueno evitó varios errores de diseño que habrían sido
difíciles de detectar solo jugando. Si lo rehiciera, mediría estos límites
(rangos, rebotes) antes de la fase de diseño del nivel, no después.
