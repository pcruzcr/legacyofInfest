---
assignment_type: stage
assignment_name: "La Entrada de Piedra"
assignment_id: "stage3_1_la_entrada_de_piedra"
zone: 3
student_name: "Avril"
units_demonstrated: [II, III, IV, V, VI, VII]
evaluation_milestone: "Evaluación Práctica II"
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

**Dirección de arte — Atardecer Oscuro (reskin gótico):** la geometría,
colisiones, enemigos y posiciones descritos en este documento no
cambiaron; sí cambió por completo el aspecto visual, reconstruido sobre
una paleta gótica de atardecer (violeta/rosa/azul oscuro, rampas de 5
tonos por material, dithering ordenado, sombras de contacto, luz
direccional desde el horizonte). Ver sección 2 (tileset actual) y
"Créditos de assets" al final.

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

**Tileset actual:** `student_assets/tilesets/tileset_invenio_gothic_v5.png`
(128×192px, grilla de 8×12 tiles de 16×16). Generado por script
(`art/gen_tileset5.py` + `art/pixelart.py` + `art/palette.py`, todos con
semilla fija — reproducibles) siguiendo un sistema de rampas de 5 tonos
por material, dithering ordenado (Bayer 2×2) en toda transición de tono,
oclusión ambiental (línea oscura de contacto), ruido de superficie
determinístico y variantes por hash de posición `(x, y)` — nunca aleatorio
en runtime. La colisión (sección 3/5) no depende del tile visual: el
`Collision` del TMX no cambió un solo valor al re-pintar el escenario.

| Grupo de tiles | Cantidad | Capa(s) donde aparece | ¿Colisión? |
|---|---|---|---|
| `adoquin_0..5` | 6 variantes | `Terrain` (piso completo) | Sí (vía objeto `Solid_Floor`) |
| `cesped_0..5` | 6 variantes | `Terrain_Detail` (franja sobre el piso) | No |
| `muro_grafito_0..3` | 4 variantes | `BG_Mid` (fachada INVENIO) | No |
| `muro_piedra_0..3` | 4 variantes | `BG_Mid` (dintel puerta) | No |
| `terracota_0..2` | 3 variantes | `BG_Mid` (acento de techo) | No |
| `ventana_lit` / `ventana_dark` | 2 | `BG_Mid` (fachada y pérgola) | No |
| `columna_fuste` / `columna_capitel` / `viga_0` | 3 | `BG_Mid` (pérgola, sobre los dos `ShooterQuetzal`) | No |
| `jardinera_top` | 1 | `BG_Near`, alineado exacto con el objeto `Platform` de cada jardinera | Sí (jardineras, vía objeto `Platform`) |
| `plataforma_0` | 1 | `BG_Near`, alineado exacto con cada `Plataforma_0X` | Sí (vía objeto `Platform`) |
| `arbol_a/b/c` | 3 árboles únicos, 3 capas c/u (tronco, follaje en clusters, hojas sueltas + sombra de contacto) | `BG_Near` | No |
| `nube_a` / `nube_b` | 2 nubes grandes (96×32px, unión de elipses + dithering) | `BG_Far` | No |
| `arbusto_0/1`, `flor_0/1`, `farola_0`, `ivy_0/1` | detalle | `BG_Near` / `Terrain_Detail` / `FG_Overlay` | No |

**Cielo y montañas — parallax real del motor, no tiles:** el TMX declara
`background_zone="zone3"`, que `StageLoader._load_backgrounds` resuelve
contra `assets/backgrounds/zone3/bg_zone3_{far,mid,near}.png` (arte
oficial del profesor, no tocado) y dibuja a velocidades distintas
(`VELOCIDAD_DE_FONDO`: far=0.15, mid=0.35, near=0.60) **antes** de las
capas del TMX — el cielo/montañas violeta de atardecer que se ve detrás
del escenario viene de ahí, no de un tile pintado. Se comprobó primero
(sección "Auditoría F0" más abajo) que este hook existe en el framework
antes de intentar simular parallax a mano.

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

Además, el mapa declara `ambient_light=0.55`, `bloom=0.30` y
`vignette=0.35` en sus propiedades (ajustados junto con el reskin a
Atardecer Oscuro — más oscuros que un exterior diurno, coherentes con la
paleta violeta/rosa del cielo de parallax).

## 10. Reflexión

Lo más difícil fue descubrir que varias restricciones del motor (rango de
detección fijo, rebote de vuelo fijo, proyectiles que ignoran las
plataformas unidireccionales) no estaban documentadas donde se esperaría,
y solo se confirman leyendo el código fuente directamente. Verificar cada
supuesto contra `src/framework/` antes de dar una posición o un
comportamiento por bueno evitó varios errores de diseño que habrían sido
difíciles de detectar solo jugando. Si lo rehiciera, mediría estos límites
(rangos, rebotes) antes de la fase de diseño del nivel, no después.

## 11. Auditoría previa al reskin gótico (F0)

Antes de repintar el escenario se auditó `src/framework/stage/` para no
reinventar nada que ya existiera:

- `StageData.background_layers` / `background_factors` y
  `StageLoader._load_backgrounds` (AUD-272): el motor **sí** expone un
  hook de parallax real por capa (`sky/deep/far/mid/near`, velocidades
  fijas en `VELOCIDAD_DE_FONDO`), activado con la propiedad de mapa
  `background_zone`. `assets/backgrounds/zone3/` ya traía
  `bg_zone3_far/mid/near.png` en paleta violeta de atardecer — se
  activó ese hook (`background_zone="zone3"`) en vez de pintar cielo o
  montañas como tiles.
- `StageData.cielo` (AUD-426, cielo procedural por degradado): se dejó
  **desactivado** a propósito — el mapa ya tiene un fondo pintado
  (`bg_zone3_far`) y el propio comentario del framework advierte que un
  degradado detrás de un fondo ya pintado no se vería.
- `type="Platform"` en la capa `Collision` (no `"Solid_OneWay"`) para
  plataformas de un solo sentido: confirmado leyendo
  `StageLoader._load_collision` directamente (documentación aparte no es
  confiable en este punto).
- No se tocó `src/engine/`, `src/framework/`, `assets/` globales ni
  `Stage0`; ningún enemigo fue subclasificado ni se tocó
  `StageLoader._entity_registry`.

## 12. Créditos de assets

- **Fondos de parallax (`bg_zone3_far/mid/near.png`):** arte oficial del
  profesor, incluido en el repositorio base (`assets/backgrounds/zone3/`).
  No se modificó ni redistribuyó — solo se referencia vía
  `background_zone="zone3"`.
- **Tileset `tileset_invenio_gothic_v5.png`, todos los props (árboles,
  nubes, columnas, ventanas, farola, flores, ivy) y el resto de las
  capas visuales del TMX:** generados por código (Python + Pillow) por
  la estudiante, con semilla fija y reproducibles desde
  `src/stages/stage3_1_la_entrada_de_piedra/art/`. No se usaron assets de
  terceros (OpenGameArt/itch.io/Kenney): la sesión de trabajo no tuvo
  acceso de red a esos sitios, así que se optó por generar todo por
  código y subir el nivel de detalle (rampas, dithering, sombras,
  variantes) en vez de mezclar con arte externo.
