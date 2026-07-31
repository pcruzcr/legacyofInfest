---
assignment_type: stage
assignment_name: "La Soda"
assignment_id: "stage1_2_la_soda"
zone: 1
student_name: "Guillermo Morice Diaz"
units_demonstrated: [II, III, IV, V]
evaluation_milestone: "Evaluación Práctica I"
---

# Stage 1-2 — La Soda

## Contexto narrativo

Cafetería de la universidad, a mitad del caos. Traversal básico + dos
enemigos: un ratón que patrulla el piso y una cucaracha voladora que planea
sobre el mostrador.

## Alcance de esta entrega (Evaluación Práctica I)

La instrucción oficial de la evaluación pide 4 cosas: **representación
gráfica**, **sistemas de coordenadas**, **transformaciones geométricas** y
**curvas básicas**. Estas cuatro caen dentro de las Unidades I, II, III y IV
del temario (`docs/08_SYLLABUS_MAPPING.md`). Además, por el ítem de rúbrica
de `docs/27_ACADEMIC_RUBRICS.md` §4 ("Color/transparency — Unit V", 15
puntos), esta entrega también incluye una operación de **Unidad V** (espacio
de color) aplicada y visible en juego — ver sección dedicada más abajo.

## Unidad I — Representación gráfica (game loop, dt)

No se implementa directamente (es responsabilidad del framework), pero se
documenta acá: el juego corre a resolución interna 320×224 a 60 FPS
(`engine/core/app.py`, `engine/core/clock.py`), escalada a la ventana. Todo
movimiento en esta stage usa el patrón `posición += velocidad * dt`
(delta time), visible en `WalkerRaton._alert_behavior` y
`FlyingCucaracha._patrol_behavior` (`src/stages/stage1_2_la_soda/entities.py`).

## Unidad II — Sistemas de coordenadas y transformaciones (`WalkerRaton`)

**Dónde:** `src/stages/stage1_2_la_soda/entities.py`, clase `WalkerRaton`
(subclase de `EnemyWalker` del framework, sin tocar `enemy_walker.py`).

**Sistema de coordenadas:** el ratón vive en coordenadas de mundo
(`self.position`, `self.rect`); la cámara lo transforma a espacio de
pantalla (`world_to_screen`, mismo patrón que usa
`Stage1_2_LaSoda._draw_enemy_health_bars` al dibujar la barra de vida:
`screen_x = rect.x - camera.offset.x`).

**Transformación local → mundo:** el hitbox/hurtbox de todo enemigo (heredado
de `EnemyBase._update_rects`) se calcula como
`hitbox_mundo = posición_entidad + offset_local`, es decir, una traslación
del rect local del enemigo al espacio de mundo — se aplica automáticamente
a `WalkerRaton` y a `FlyingCucaracha` sin código adicional.

**Vectores explícitos (lo nuevo de esta entrega):** `WalkerRaton` agrega un
"scent lock" — un empujón extra de velocidad cuando corre directo hacia el
jugador — usando aritmética vectorial explícita en vez de solo la lógica
heredada del framework:

```
distancia             = vec2_distance(P_jugador, P_ratón)                      (math_utils.vec2_distance)
dirección_al_jugador  = vec2_normalize(P_jugador - P_ratón)                    (math_utils.vec2_normalize)
alineación            = vec2_dot(dirección_al_jugador, (facing_direction, 0))  (math_utils.vec2_dot)
si alineación > 0.8:  posición.x += dirección_al_jugador.x * 14.0 * dt         (escalado)
```

`alineación` va de -1 (huyendo) a 1 (corriendo directo hacia el jugador);
0.8 ≈ un cono de 37° respecto a la dirección de encare. `> 0.8` dispara el
empujón, siempre acotado a la franja de patrulla (`_patrol_origin.x ±
patrol_length/2`) — ver nota de diseño abajo. A diferencia de una versión
anterior que usaba los métodos propios de `pygame.Vector2` (`.length()`,
`.normalize()`, `.dot()`), el código ahora importa y llama directamente a
`vec2_distance`, `vec2_normalize` y `vec2_dot` de `engine/utils/math_utils.py`
— no reimplementa la matemática, *usa* la utilidad del módulo, tal como pide
esta unidad.

**Nota de diseño — nunca persigue:** `WalkerRaton._alert_behavior` no llama
a `super()._alert_behavior()` (la IA de persecución/carga heredada de
`EnemyWalker`). El ratón patrulla de lado a lado igual en PATROL, ALERT y
SEARCH (estilo Goomba de Mario) — perder la persecución fue justo lo que
causó un bug real durante el desarrollo (el ratón podía atravesar paredes y
salir del mapa al recibir un golpe mientras perseguía; ver
`LA_SODA_PROGRESO.md`). El burst de "scent lock" sigue siendo matemática
vectorial real, solo que ahora es un empujón de velocidad *dentro* de la
franja de patrulla en vez de una persecución sin límite.

**Demo en juego:** `WalkerRaton_01` en el `.tmx` (antes un `Walker`
genérico), cerca del checkpoint. Con el jugador cerca y alineado de frente,
se ve una aceleración notable dentro de su ida y vuelta normal — no te
sigue fuera de su franja.

## Unidad III — Curvas básicas (`FlyingCucaracha`)

**Dónde:** `src/stages/stage1_2_la_soda/entities.py`, clase
`FlyingCucaracha` (subclase de `EnemyFlying`).

**Tipo de curva:** spline de Catmull-Rom cúbica, evaluada con
`CurveTools.build_bezier_path()` (`framework/processing/curve_tools.py`,
método provisto por el framework — no se reimplementa la matemática de la
curva, se *usa* la utilidad como indica la unidad).

**Puntos de control** (relativos a la posición de spawn `(520, 480)` en el
`.tmx`, formando un arco bajo sobre el mostrador):

| Punto | Offset (px) | Posición absoluta |
|---|---|---|
| P0 | (-40, 10) | (480, 490) |
| P1 | (-14, -18) | (506, 462) |
| P2 | (14, -18) | (534, 462) |
| P3 | (40, 10) | (560, 490) |

**Qué representa `t`:** parámetro de la curva en `[0, 1]`, de P0 a P3. En
vez de que la cucaracha "salte" de vuelta a P0 al llegar a P3, `t` sigue una
onda triangular en el tiempo (`_curve_t % 2.0`, reflejada si `> 1.0`) con
período de 3.2s — así la cucaracha se desliza hacia adelante y hacia atrás
por el mismo arco, suave en ambos extremos.

**Por qué Catmull-Rom y no el modo "sine" del roster:** el diseño oficial
(`docs/18_ENEMY_ROSTER.md` #2.5) especifica vuelo sinusoidal para
`FlyingCucaracha`. El patrullaje se reescribió para usar `CurveTools`
explícitamente — así la matemática de la curva queda visible e
inspeccionable en código propio del estudiante, en vez de vivir enterrada
en la estrategia interna del framework.

**Nota de diseño — nunca interrumpe la curva:** `_alert_behavior` y
`_search_behavior` llaman a `_patrol_behavior` en vez de a la persecución
sinusoidal/dive-bomb heredada de `EnemyFlying` — la cucaracha nunca
abandona su arco, ni siquiera al detectar al jugador. En vez de perseguir,
dispara un proyectil hacia el jugador cada ~1.8s mientras lo detecta,
reutilizando la clase `Projectile` del framework (`enemy_shooter.py`) sin
reimplementarla — mismo cálculo de ángulo (`atan2`), misma detección de
colisión contra paredes, mismo soporte de parry que ya tiene ese enemigo.

**Demo en juego:** `FlyingCucaracha_01` en el `.tmx`, flotando sobre el
mostrador entre el ratón y el `NextTrigger`. Acercate y quedate cerca: sigue
planeando por su arco de siempre, pero empieza a lanzarte proyectiles.

## Unidad IV — Representación de escena

El `.tmx` tiene las 8 capas requeridas: `BG_Far`, `BG_Mid`, `BG_Near`,
`Terrain`, `Terrain_Detail`, `FG_Overlay` (tile layers) + `Collision` +
`Objects` (object groups). Dos tilesets: `tileset_cafeteria` (del profesor)
y `tileset_soda_decor` (dibujado por el estudiante para la zona decorativa
agregada — ver `LA_SODA_PROGRESO.md` en la raíz del proyecto real para el
historial). Ambos enemigos usan sprites animados por ciclo de frames
(`walk`/`hurt`/`die`, `fly`) provistos por el framework para Zona 1.
`BG_Far` y `BG_Mid` están rellenas con el tile de pared de ladrillo de la
cafetería (gid 7, `tileset_cafeteria` — el mismo que forma los pilares
visibles en `Terrain_Detail`), como pared sólida de fondo detrás del resto
de la escena, en vez de quedar vacías.

**Piso y cocina (realismo, a partir de fotos reales de la soda real):** el
piso de `BG_Near` usa dos tiles de terracota propios (`tileset_soda_decor`,
gid 81/82) con variación sutil de tono y textura, en vez del checker
rojo/blanco liso — más fiel a las fotos de referencia del lugar real
(piso de barro cocido). Junto al mostrador de madera se agregaron un
refrigerador de gaseosas rojo y una nevera de acero (gid 83/84, mismo
tileset), inspirados directamente en la cocina real de la soda.

## Unidad V — Color/transparencia (`_draw_enemy_health_bars`)

**Dónde:** `src/stages/stage1_2_la_soda/stage1_2_la_soda.py`, método
`Stage1_2_LaSoda._draw_enemy_health_bars` (llamado desde `draw()`, que ya
extiende el render del framework sin tocarlo).

**Espacio de color usado y por qué:** HSV (Hue-Saturation-Value), vía
`ColorTools.hsv_to_rgb()` (`framework/processing/color_tools.py`). HSV se
eligió porque el efecto necesita recorrer un arco de matiz (hue) —
verde → amarillo → rojo — manteniendo saturación y brillo constantes al
máximo; en RGB directo ese recorrido de matiz requeriría interpolar los tres
canales a mano sin garantía de mantener el color "puro" (saturación 1) en
todo el camino. HSV expone el matiz como un solo parámetro angular, que es
exactamente lo que se necesita interpolar.

**Fórmula aplicada:** con `pct` la fracción de vida restante del enemigo
(`current_health / max_health`, en `[0, 1]`):

```
hue   = 120.0 * pct     (grados; 120° = verde puro, 0° = rojo puro en HSV)
color = ColorTools.hsv_to_rgb(hue, s=1.0, v=1.0)
```

A vida llena (`pct = 1.0`) la barra no se dibuja (mismo comportamiento que
antes: solo aparece una vez que el enemigo ya recibió daño). Apenas baja de
100%, `hue` empieza justo debajo de 120° (verde) y decrece linealmente hacia
0° (rojo) a medida que `pct → 0`, pasando por amarillo (~60°) a media vida.

**Aplicación a una superficie real:** el color calculado no se usa para
"pintar un pixel y ya" — se hornea en una `pygame.Surface` real con una
segunda llamada a `ColorTools`:

```
fill_surf = pygame.Surface((fill_w, 3))
fill_surf.fill((255, 255, 255))          # blanco puro
fill_surf = ColorTools.apply_tint(fill_surf, color)   # Surface -> Surface
surface.blit(fill_surf, (x, y))
```

`ColorTools.apply_tint` multiplica cada canal de la superficie por
`color/255` (aquí, partiendo de blanco puro, el resultado es el `color`
exacto calculado). Esto cumple el requisito de que la operación de Unidad V
se aplique a una `pygame.Surface` real, no solo a una tupla de enteros.

**Demo en juego:** ataca a `WalkerRaton_01` o `FlyingCucaracha_01` sin
matarlo de un solo golpe — la barra de vida sobre el enemigo aparece verde
apenas recibe el primer golpe y se desliza hacia amarillo y luego rojo a
medida que su vida baja, antes de morir.

**Screenshots (antes/después del tinte de color):**

![Vista completa del stage 1-2 La Soda, HUD y tip de controles visibles, con WalkerRaton_01 mostrando su barra de vida ya teñida naranja/amarillo tras recibir daño](screenshots/unit5_health_tint_full.png)

*Antes:* a vida llena (`pct = 1.0`) no se dibuja ninguna barra sobre el
enemigo (comportamiento sin la operación de Unidad V visible).
*Después:* `WalkerRaton_01` al ~35% de vida — `ColorTools.hsv_to_rgb()`
calculó un matiz cercano a 40° (naranja/amarillo) y `ColorTools.apply_tint()`
lo horneó sobre la `pygame.Surface` de la barra, visible en detalle abajo.

![Detalle recortado de WalkerRaton al 35% de vida, barra de vida naranja/amarilla sobre su cabeza](screenshots/unit5_health_tint_detail.png)

## Cómo probar

```
python main.py --stage stage1_2_la_soda
```

Bugs de framework encontrados durante el desarrollo (documentados, no
tocados — son de solo lectura): ver `LA_SODA_PROGRESO.md`.
