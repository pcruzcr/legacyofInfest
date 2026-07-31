---
assignment_type: stage
assignment_name: "El Lobby"
assignment_id: "lobby_datacenter"
zone: 2
student_name: "Alejandro Luna"
units_demonstrated: [II, III, IV, V]
evaluation_milestone: "Evaluación Práctica I"
---

# El Lobby — Zona 2 (El Datacenter)

Recepción del complejo de datacenter, ubicada entre la entrada/antenas y las oficinas. Mostrador, sillas de espera, piso metálico, y una cámara de seguridad y luz de alarma que refuerzan la atmósfera de vigilancia industrial descrita en el
documento de diseño de mundo de la Zona 2.

## Unidad II — Sistemas de coordenadas y vectores

**Archivo:** `src/stages/lobby_datacenter/security_camera.py`

Una cámara de seguridad fija (posición mundo `(300, 100)`) detecta al jugador combinando tres
operaciones  `src/engine/utils/math_utils.py`:

- **`vec2_distance(a, b)`** — distancia `√((x₂-x₁)² + (y₂-y₁)²)`. Se usa para saber si
  el jugador está dentro del rango de detección.
- **`vec2_normalize(v)`** — divide un vector entre su propia magnitud, dejando solo la dirección. Se aplica al vector `jugador − cámara` para obtener hacia dónde está el jugador,
  sin importar la distancia.
- **`vec2_dot(a, b)`** — producto punto de dos vectores unitarios, equivalente al coseno del
  ángulo entre ellos (1.0 = misma dirección, 0 = perpendicular, -1 = opuesto). Se compara contra
  un umbral (`0.85` ≈ 32°) para saber si el jugador cae dentro del cono de visión de la cámara.

Cuando `distancia ≤ rango` **y** `producto_punto ≥ umbral`, la cámara se marca como alertada y
cambia de azul a rojo (visualmente comprobado).

## Unidad III — Curvas

**Archivos:** `assets/maps/lobby_datacenter/lobby_datacenter.tmx` (objetos `Waypoint_01`–`04` y
`Flying_01`), motor: `src/framework/entities/flight_strategies.py::BezierFlight`

`Flying_01` tiene la propiedad `flight_mode=bezier`, que activa la estrategia `BezierFlight` ya
integrada en el motor. Cada cuadro, esta estrategia llama a `CurveTools.build_bezier_path(waypoints, t)`
para calcular la posición sobre una curva cerrada que pasa por los 4 puntos de control.

**Nota importante de precisión matemática:** a pesar de que la propiedad se llama `bezier`, el
método `CurveTools.build_bezier_path` implementa internamente una **spline Catmull-Rom**, no una
curva de Bézier clásica. La diferencia: una Catmull-Rom pasa *exactamente a través* de cada punto
de control (usando el punto anterior y el siguiente para estimar la tangente en cada uno), mientras
que una Bézier generalmente solo toca el primer y último punto, siendo "atraída" por los intermedios
sin tocarlos. Confirmé este comportamiento leyendo el código fuente del motor directamente.

**Puntos de control (`owner_id=Flying_01`), en el orden en que aparecen en el TMX:**

| Waypoint | X | Y | waypoint_index |
|---|---|---|---|
| Waypoint_01 | 483 | 118 | 0 |
| Waypoint_02 | 578 | 117 | 1 |
| Waypoint_03 | 580 | 165 | 2 |
| Waypoint_04 | 483 | 162 | 3 |

(`Flying_01` nace en `(502, 139)`, dentro de este lazo rectangular en el aire.)

## Unidad IV — Representación de escena

**Archivo:** `assets/maps/lobby_datacenter/lobby_datacenter.tmx`

Mapa ortogonal de 40×14 tiles de 16×16px
`(col, fila)`  `pixel = celda × 16`. Sistema de
píxeles absolutos para los objetos de `Objects`/`Collision`. Las 8 capas requeridas `BG_Far`, `BG_Mid`, `BG_Near`, `Terrain`,
`Terrain_Detail`, `Objects`, `Collision`, `FG_Overlay`.

El fondo atmosférico usa la propiedad de mapa `background_zone=zone2`, que carga automáticamente
`bg_zone2_far/mid/near.png` con parallax 
`BG_Far/Mid/Near` se dejaron vacías a propósito porque el motor las renderiza a la misma velocidad
que `Terrain` 

Objetos: `PlayerSpawn_01`, `Checkpoint_01` (`checkpoint_id=0`), `NextTrigger_01`, tres enemigos
(`Walker_01`, `Shooter_01`, `Flying_01`, todos con `zone=2`), y paredes 
(`Wall_Left`, `Wall_Right`) en `Collision` para evitar que el jugador salga del área de juego

## Unidad V — Color y transparencia

**Archivo:** `src/stages/lobby_datacenter/alarm_light.py`

Una luz roja `ColorTools.rgb_to_hsv()` / `ColorTools.hsv_to_rgb()` de
`src/framework/processing/color_tools.py`