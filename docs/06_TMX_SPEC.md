---
document_id: "LOI-TMX-006"
title: "Legacy of InFest — Especificación TMX"
aliases: ["Especificación TMX", "Formato de mapa", "TMX Specification"]
tags: ["tmx", "tiled", "mapa", "formato"]
description: "El formato del fichero de mapa: capas, objetos y reglas de colocación"
source: "docs/06_TMX_SPEC.md"
date_processed: "2026-08-11"
---

# Legacy of InFest — Especificación TMX

**Identificador:** LOI-TMX-006
**Versión:** 2.0.0
**Estado:** Oficial
**Público:** profesorado, personal de apoyo, estudiantes y asistentes de código

---

## 1. Panorama

Los mapas se diseñan en **Tiled Map Editor** y se exportan como `.tmx` (XML).
`StageLoader` los lee con `pytmx` y `pyscroll` y monta el escenario completo:
capas de baldosas, puntos de aparición, zonas de colisión, puntos de control,
portales y disparadores.

Este documento define **la estructura del fichero**: qué capas hacen falta,
cómo se nombran las cosas y dónde se pone cada objeto. Un TMX que no la cumpla
hace que `StageLoader` lance un `FrameworkUsageError` con el motivo.

> **Dónde está cada cosa, para no buscar de más:**
>
> | Si buscas… | Míralo en |
> |---|---|
> | Las **propiedades de mapa** y qué hace cada una | [[60_GUIA_COMPLETA_DEL_MOTOR.md]] |
> | Los **tipos de objeto** con sus propiedades | [[60_GUIA_COMPLETA_DEL_MOTOR.md]] y `docs/STAGE_CREATION.md` |
> | **La estructura del fichero** y las reglas de colocación | este documento |
>
> Esta separación es deliberada (AUD-430). Aquí había una tabla de propiedades
> que citaba **23** de las **39** que el motor lee, y llevaba desactualizada
> quién sabe cuánto. La guía 60 tiene veintidós pruebas que la atan al código;
> una segunda lista aquí volvería a desincronizarse, que es exactamente lo que
> AUD-392 desmontó. **La lista viva manda.**
>
> Y la respuesta definitiva no está en ningún documento, sino en el validador:
>
> ```bash
> python scripts/validate_tmx.py assets/maps/mi_mapa/mi_mapa.tmx
> ```
>
> Lee el registro, no este texto, así que no puede envejecer.

---

## 2. Propiedades del fichero

Todo TMX tiene que estar configurado así en Tiled:

| Propiedad | Valor | Notas |
|---|---|---|
| Orientación | Ortogonal | Ni isométrica ni hexagonal |
| Ancho de baldosa | 16 | píxeles |
| Alto de baldosa | 16 | píxeles |
| Infinito | No | Los mapas tienen dimensiones fijas |
| Orden de dibujado | Derecha-abajo | El estándar |
| Ancho mínimo | 20 baldosas (320 px) | Tiene que llenar una pantalla |
| Alto mínimo | 14 baldosas (224 px) | Tiene que llenar una pantalla |
| Ancho máximo | 512 baldosas (8192 px) | Límite de rendimiento |

### 2.1 Las cuatro propiedades obligatorias

Sin estas cuatro el mapa no carga:

| Propiedad | Tipo | Qué es |
|---|---|---|
| `stage_id` | cadena | Identificador único (`stage0`, `stage1`…) |
| `stage_name` | cadena | El nombre que sale en el cartel del HUD |
| `time_limit` | entero | Segundos de límite. `0` = sin límite |
| `bgm_track` | cadena | Nombre del fichero de música, sin extensión |

Y una quinta que **cuenta para la nota** aunque el motor no la lea:

| Propiedad | Tipo | Qué es |
|---|---|---|
| `author` | cadena | Tu nombre. `scripts/grade_stage.py` la puntúa en metadatos |

Las otras treinta y cinco —atmósfera, clima, hora, cámara, agua, profundidad,
ritmo…— están en la guía del motor. `validate_tmx.py` avisa de las que faltan y
de las que están mal escritas.

### 2.2 Propiedades que **no** existen

Se documentaron alguna vez y ningún módulo las lee. Escribirlas no hace nada:

| Propiedad | Qué usar en su lugar |
|---|---|
| ~~`background_color`~~ | `background_zone` |
| ~~`debug_mode`~~ | En el juego: **F11** abre la consola, **F1** las cajas de colisión |
| ~~`use_tile_collision`~~ | La colisión sale **siempre** de la capa `Collision` |
| ~~`trigger_once`~~ | No es una propiedad: es otro **tipo**, `MessageTrigger_Once` |

---

## 3. Las capas

Todo TMX contiene estas ocho capas, en este orden de abajo arriba, y **con
estos nombres exactos**:

| Orden | Nombre | Tipo | Qué es |
|---|---|---|---|
| 1 | `BG_Far` | Baldosas | Fondo lejano (cielo, montañas) |
| 2 | `BG_Mid` | Baldosas | Fondo medio (árboles, arquitectura) |
| 3 | `BG_Near` | Baldosas | Fondo cercano |
| 4 | `Terrain` | Baldosas | El terreno sólido |
| 5 | `Terrain_Detail` | Baldosas | Decoración sin colisión |
| 6 | `Objects` | Objetos | Apariciones, disparadores, puntos de control |
| 7 | `Collision` | Objetos | Rectángulos de colisión (invisibles al jugar) |
| 8 | `FG_Overlay` | Baldosas | Primer plano, por delante de las entidades |

### 3.1 El parallax

Cada capa de fondo se mueve a distinta velocidad respecto de la cámara. El
factor sale **del nombre del fichero**, no del orden de carga:

| Capa | Factor |
|---|---|
| `sky` | 0,06 |
| `deep` | 0,10 |
| `far` | 0,15 |
| `mid` | 0,35 |
| `near` | 0,60 |

> **Corregido el 2026-08-11 (AUD-431).** Esta tabla decía que había **tres**
> capas y que `mid` era 0,40 y `near` 0,70. Son **cinco** —`sky` y `deep` son
> opcionales, las otras tres avisan si faltan— y los factores reales son 0,35 y
> 0,60. También listaba un «factor de parallax Y» por capa que no existe: el
> desplazamiento vertical es el mismo factor **multiplicado por 0,5**.
>
> Que el factor salga del nombre y no del índice es deliberado: antes salía de
> la posición de carga, así que un mapa que añadiera una capa por delante hacía
> que `far` pasara de 0,15 a 0,35 y el mismo fondo se moviera distinto en dos
> escenarios.

Los ficheros van en `assets/backgrounds/{background_zone}/` y se llaman
`bg_{zona}_{nombre}.png`.

### 3.2 Qué se ve al jugar

| Capa | ¿Se ve? |
|---|---|
| `BG_Far`, `BG_Mid`, `BG_Near` | Sí |
| `Terrain`, `Terrain_Detail` | Sí |
| `FG_Overlay` | Sí, por delante de las entidades |
| `Objects` | No: crea las entidades y desaparece |
| `Collision` | No: se convierte en una lista de rectángulos |

### 3.3 Capas de más

Puedes añadir capas de baldosas para decorar:

- fondo: prefijo `BG_` y un nombre propio (`BG_Clouds`);
- primer plano: prefijo `FG_`.

**No se admiten capas de objetos ni de colisión adicionales.** Todo tiene que
estar en `Objects` y en `Collision`.

---

## 4. Los objetos

La capa `Objects` lleva todo lo que no son baldosas: cada objeto es un
rectángulo o un punto de Tiled con un `type` y sus propiedades.

### 4.1 El sistema de coordenadas

Las posiciones son píxeles con el origen arriba a la izquierda del mapa.

**Convención de la Y en las apariciones:** la coordenada Y de un `PlayerSpawn`
es la de los **pies**, no la de la esquina superior: colocas el punto donde
quieres que se apoye el personaje y `StageLoader` convierte restando la altura
(`spawn_point.y = obj.y - 32`). Los **enemigos** no: su Y es la esquina
superior del objeto, la semántica nativa de Tiled — se coloca el rectángulo
con la base sobre el suelo y el motor lo respeta tal cual (AUD-455).

### 4.2 Los tipos de objeto

En ejecución el motor acepta **78**: 39 integrados del framework y 37 del
registro de entidades una vez descubiertos los escenarios, más `Solid` y
`Platform` en la capa `Collision`.

La lista completa, con las propiedades de cada uno, está en
[[60_GUIA_COMPLETA_DEL_MOTOR.md]]. Los imprescindibles para que un mapa cargue:

| Tipo | Forma | Qué es |
|---|---|---|
| `PlayerSpawn` | Punto | Dónde empieza el jugador. **Exactamente uno** |
| `NextTrigger` | Rectángulo | El final del escenario. **Exactamente uno** |
| `Checkpoint` | Rectángulo | Punto de control. `checkpoint_id` obligatorio |

`Platform` **no** va en `Objects`: pertenece a `Collision`, donde un rectángulo
con ese tipo se convierte en plataforma de un sentido. En `Objects` no es un
tipo válido y el cargador lo dice.

---

## 5. Cómo se nombran las cosas

### 5.1 Los objetos

Nombre único, con el formato `<tipo>_<número>`:

`PlayerSpawn_01` · `Walker_01` · `Checkpoint_02` · `Waypoint_01`

El nombre importa de verdad en dos casos: los `Waypoint`, que se enlazan por
nombre, y los `Pickup`, que lo usan como `item_id` si no declaras uno.

### 5.2 Los tilesets

`tileset_<entorno>.png`, en `assets/tilesets/` si lo da el profesorado o en
`student_assets/tilesets/` si lo haces tú.

### 5.3 Las propiedades

`snake_case`. Sin espacios ni guiones. Los nombres tienen que coincidir
**exactamente** con los que espera el motor: `validate_tmx.py` avisa de los que
no reconoce y sugiere el parecido, porque `gravty_multiplier` no da error — el
cargador usa el valor por defecto y el nivel se juega con la gravedad
equivocada en silencio (AUD-392).

---

## 6. Apariciones

### 6.1 El jugador

- **Exactamente un** `PlayerSpawn` por mapa.
- Es un punto, colocado sobre suelo sólido.
- Su Y son los **pies**, no la esquina superior.
- Sin él, `StageLoader` lanza `FrameworkUsageError("No PlayerSpawn found in TMX")`.

### 6.2 Los enemigos

- Son objetos rectangulares, colocados donde aparecen.
- La Y es la de la **esquina superior** del rectángulo de Tiled (igual que
  cualquier objeto): se dibuja la caja con la base sobre el suelo y esa misma
  base es donde quedan los pies en juego (AUD-455).
- Las propiedades del objeto **sustituyen** a los valores por defecto de la clase.
- Si falta una propiedad se usa el valor por defecto y se avisa por consola.

#### `Walker`

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `patrol_length` | entero | 96 | Distancia de patrulla en píxeles |
| `facing` | cadena | `right` | Hacia dónde empieza mirando |
| `patrol_speed` | flotante | 45,0 | Velocidad patrullando |
| `alert_speed` | flotante | 75,0 | Velocidad persiguiendo |
| `damage_on_contact` | flotante | 0,5 | Daño al tocarlo |

#### `Flying`

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `flight_mode` | cadena | `sine` | `sine`, `bezier` o `patrol` |
| `flight_speed` | flotante | 60,0 | Velocidad de recorrido |
| `sine_amplitude` | flotante | 28,0 | Amplitud vertical (sólo en `sine`) |
| `sine_frequency` | flotante | 1,5 | Frecuencia en Hz (sólo en `sine`) |

#### `Shooter`

| Propiedad | Tipo | Por defecto | Qué hace |
|---|---|---|---|
| `fire_rate` | flotante | 0,5 | Disparos por segundo |
| `projectile_speed` | flotante | 120,0 | Velocidad del proyectil, px/s |
| `projectile_damage` | flotante | 0,5 | Daño por impacto |
| `patrol_length` | entero | 0 | `0` = quieto; mayor = patrulla lenta |

### 6.3 Los puntos de ruta

Un `Flying` con `flight_mode=bezier` o `patrol` lee sus puntos de la capa
`Objects`. Se enlazan haciendo coincidir el `owner_id` del `Waypoint` con el
**nombre** del objeto volador, y se ordenan por `waypoint_index` (entero, desde
0). La secuencia resultante va a `CurveTools.bezier()`.

```
Flying_01   (type: Flying)   → flight_mode=bezier, flight_speed=55.0
Waypoint_01 (type: Waypoint) → owner_id=Flying_01, waypoint_index=0
Waypoint_02 (type: Waypoint) → owner_id=Flying_01, waypoint_index=1
Waypoint_03 (type: Waypoint) → owner_id=Flying_01, waypoint_index=2
```

---

## 7. Puntos de control

Un `Checkpoint` es un rectángulo de la capa `Objects`. Se activa cuando el
rectángulo del jugador lo toca.

| Propiedad | Tipo | Qué es |
|---|---|---|
| `checkpoint_id` | entero | Único dentro del escenario, empezando en 0 |

**Comportamiento:**

- Se activan **una sola vez**; después quedan consumidos.
- Al activarse emiten `CHECKPOINT_REACHED` por el bus de eventos.
- La posición de reaparición pasa a ser el centro X y la base Y del rectángulo.
- Al morir, el jugador reaparece ahí con la vida llena.
- Activar el 2 antes que el 1 es válido, pero el 1 ya no se activará después.

**Dónde ponerlos:**

- **Al menos uno** en todo escenario de estudiante.
- No pueden solaparse entre sí.
- Sobre suelo sólido: su base tiene que coincidir con el borde de una baldosa.
- Mínimo 16×32 píxeles.
- El calificador recomienda **no pasar de 500 px** entre uno y otro. Morir y
  rehacer medio nivel es la forma más rápida de que alguien deje de jugar.
  Una excepción deliberada y documentada no es un defecto: el 4-1 la rompe
  a propósito (`KNOWN_GAPS.md`, [GAP-061] nota AUD-516) porque es un
  escenario psicológico de terror.

El aspecto sale de `assets/sprites/shared/checkpoint.png` y no se sustituye.

---

## 8. El final del escenario

Un `NextTrigger` marca la salida.

- **Exactamente uno** por mapa.
- Suele ir al extremo derecho, cubriendo el alto de una puerta.
- El jugador tiene que estar **apoyado** para dispararlo, y no saltando: así no
  se activa por accidente al pasar por encima.
- Mínimo 16×32 píxeles.

Al tocarlo: se emite `STAGE_COMPLETE`, `SceneManager` prepara la transición, el
audio se funde en 500 ms, la pantalla en 800 ms, y entra la escena siguiente.

---

## 9. Colisión

### 9.1 La capa

Toda la geometría sólida vive en la capa de objetos `Collision`, como
rectángulos. Son invisibles al jugar: `StageLoader` los convierte en una lista
de `pygame.Rect` para la física.

### 9.2 Los dos tipos

| `type` | Qué hace |
|---|---|
| `Solid` | Sólido por los cuatro lados |
| `Platform` | Plataforma de un sentido: se atraviesa desde abajo |

Cualquier otro tipo —o ninguno— se trata como `Solid`. Poner ahí un
`HazardZone` no lo convierte en zona de daño: lo convierte en **suelo**, y el
validador avisa de ello.

Las zonas de peligro, los fosos y los bloqueos de cámara van en `Objects`.

Los rectángulos deberían alinearse a la rejilla de 16 px. Se admite más
precisión si está justificada —una rampa aproximada con rectángulos finos—,
aunque para eso existe el tipo `Slope`.

### 9.3 El orden de resolución

Se resuelve **por ejes separados**, X y luego Y:

1. **Integrar X** — `posicion.x += velocidad.x * dt`
2. **Resolver X** — para cada sólido solapado, deshacer la penetración. Los
   roces de 2 px o menos se ignoran, o el suelo bloquearía el avance lateral.
3. **Integrar Y** — `posicion.y += velocidad.y * dt`
4. **Resolver Y** — según de dónde venía:
   - **desde arriba** (`velocidad.y >= 0` y el borde inferior anterior estaba
     sobre la baldosa): aterriza;
   - **desde abajo** (`velocidad.y < 0` y el borde superior anterior estaba
     bajo la baldosa): se golpea la cabeza.

Las plataformas de un sentido se resuelven aparte, y sólo al caer.

**Prioridad cuando varias cosas se solapan:** muerte → sólido → plataforma →
peligro.

### 9.4 Terreno y colisión son cosas distintas

Las capas `Terrain` y `Terrain_Detail` **no** producen colisión. Sale
exclusivamente de la capa `Collision`.

La separación es a propósito: permite dibujar terreno libremente sin que la
forma condicione la física, y permite muros invisibles o fosos sin baldosa que
los dibuje.

---

## 10. Mensajes

Un `MessageTrigger` es un rectángulo que, al entrar el jugador, muestra un
texto en la caja del HUD.

| Propiedad | Tipo | Qué es |
|---|---|---|
| `text` | cadena | El mensaje |
| `duration` | flotante | Segundos hasta que se va. `0` = hasta que lo cierren |

Para que salga **una sola vez**, el objeto tiene que ser del tipo
`MessageTrigger_Once`. No es una propiedad; es otro tipo.

**Reglas del texto:** 80 caracteres por línea como mucho, tres líneas como
mucho, `\n` para separarlas y texto plano sin códigos de formato.

---

## 11. Ejemplos

### 11.1 La estructura mínima

```xml
<map version="1.10" orientation="orthogonal" renderorder="right-down"
     width="80" height="14" tilewidth="16" tileheight="16">

  <properties>
    <property name="schema_version" value="1"/>
    <property name="stage_id" value="stage1"/>
    <property name="stage_name" value="El Descenso"/>
    <property name="author" value="TU NOMBRE AQUI"/>
    <property name="time_limit" type="int" value="180"/>
    <property name="bgm_track" value="bgm_zone1"/>
  </properties>

  <tileset firstgid="1" source="../assets/tilesets/tileset_dungeon.tsx"/>

  <layer name="BG_Far" .../>
  <layer name="BG_Mid" .../>
  <layer name="BG_Near" .../>
  <layer name="Terrain" .../>
  <layer name="Terrain_Detail" .../>

  <objectgroup name="Objects">
    <!-- La Y del PlayerSpawn son los PIES: el cargador resta 32 -->
    <object id="1" type="PlayerSpawn" name="PlayerSpawn_01" x="48" y="192"/>
    <object id="2" type="Walker" name="Walker_01" x="256" y="164">
      <properties>
        <property name="patrol_length" type="int" value="128"/>
        <property name="facing" value="left"/>
      </properties>
    </object>
    <object id="3" type="Checkpoint" name="Checkpoint_01" x="640" y="160" width="24" height="32">
      <properties>
        <property name="checkpoint_id" type="int" value="0"/>
      </properties>
    </object>
    <object id="4" type="MessageTrigger_Once" name="Message_01" x="144" y="160" width="48" height="32">
      <properties>
        <property name="text" value="Camina a la derecha.\nPulsa Z para atacar."/>
        <property name="duration" type="float" value="5.0"/>
      </properties>
    </object>
    <object id="5" type="NextTrigger" name="NextTrigger_01" x="1248" y="160" width="16" height="64"/>
  </objectgroup>

  <objectgroup name="Collision">
    <object id="10" type="Solid" name="Solid_Floor" x="0" y="192" width="1280" height="32"/>
    <object id="11" type="Platform" name="Platform_01" x="256" y="160" width="80" height="8"/>
  </objectgroup>

  <layer name="FG_Overlay" .../>

</map>
```

### 11.2 Un volador con recorrido de Bézier

```xml
<object id="20" type="Flying" name="Flying_01" x="400" y="96">
  <properties>
    <property name="flight_mode" value="bezier"/>
    <property name="flight_speed" type="float" value="55.0"/>
  </properties>
</object>

<object id="21" type="Waypoint" name="Waypoint_01" x="400" y="96">
  <properties>
    <property name="owner_id" value="Flying_01"/>
    <property name="waypoint_index" type="int" value="0"/>
  </properties>
</object>

<object id="22" type="Waypoint" name="Waypoint_02" x="560" y="60">
  <properties>
    <property name="owner_id" value="Flying_01"/>
    <property name="waypoint_index" type="int" value="1"/>
  </properties>
</object>
```

### 11.3 Una zona de daño

Va en `Objects`, **nunca** en `Collision`:

```xml
<object id="30" type="HazardZone" name="Hazard_Spikes01" x="512" y="176" width="48" height="16">
  <properties>
    <property name="damage" type="float" value="1.0"/>
  </properties>
</object>
```

### 11.4 Un bloqueo de cámara

```xml
<object id="40" type="CameraLock" name="CameraLock_Room01" x="800" y="0" width="320" height="224">
  <properties>
    <property name="lock_x" type="bool" value="true"/>
    <property name="lock_y" type="bool" value="false"/>
  </properties>
</object>
```

Con el jugador dentro, la cámara deja de moverse en X. Sirve para salas de
desplazamiento vertical y para arenas de jefe.

---

## 🔗 Documentos relacionados

- [[60_GUIA_COMPLETA_DEL_MOTOR.md|Guía completa del motor — todas las propiedades y tipos]]
- [[STAGE_CREATION.md|Guía de creación de escenarios]]
- [[07_STAGE0_DESIGN.md|Diseño del escenario 0]]
