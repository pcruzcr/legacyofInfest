---
document_id: "LOI-HUD-009"
title: "Legacy of InFest — Especificación del HUD"
aliases: ["Especificación del HUD", "HUD Specification"]
tags: ["hud", "ui", "especificacion"]
description: "Maqueta del HUD, corazones, temporizador, mensajes, pantalla de fin de partida"
source: "docs/09_HUD_SPEC.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Especificación del HUD

**ID del documento:** LOI-HUD-009
**Versión:** 1.4.0
**Estado:** Oficial
**Audiencia:** Profesor, ayudantes, asistentes de código

> **AUD-455.** Traduce el documento completo (antes en inglés, con un
> resumen final que remitía de vuelta al inglés para la especificación
> completa). Verificado contra `src/engine/ui/hud.py::_get_portrait_state()`:
> la prioridad de estados del retrato (`dead` > `critical` > `hurt` >
> `normal`) coincide exactamente con el pseudocódigo de §3.4.

---

<!-- cita-historica -->
> **Corrección AUD-150 — nombres que este documento daba por existentes.**
> Comprobados uno por uno contra el código. Ninguno rompe nada al jugar; todos
> engañan a quien lea el documento para programar.
>
> * `hurt_display_timer` y `reveal_count` **no existen.** Son nombres de un pseudocódigo que nunca se escribió así: el HUD no lleva esos contadores.
> * `Message` **no es un tipo de objeto de Tiled.** El tipo se llama `MessageTrigger` (y `MessageTrigger_Once`). Un estudiante que escriba «Message» recibe un aviso de tipo desconocido.
<!-- /cita-historica -->


## 1. Visión general

El HUD (Heads-Up Display) es la capa persistente en pantalla que comunica al jugador su estado, la información del escenario y los eventos del juego. Todos los elementos del HUD se dibujan en espacio de pantalla — no se mueven con la cámara. Se dibujan encima de todo el contenido del escenario en cada fotograma.

El HUD está implementado en `src/engine/ui/hud.py` y es un sistema del profesorado. Los estudiantes no lo modifican. Pueden disparar elementos del HUD a través del EventBus (`SHOW_MESSAGE`, etc.).

> **AUD-527 (2026-08-18) — se revierte la convención SNES.** Hasta aquí, la
> regla era "sin antialiasing, sin degradados, sin sombras mezcladas por
> alfa". Decisión del dueño: modernizar el HUD de verdad, no dentro de esa
> restricción. Se mantiene todo lo demás de esta especificación —el
> maquetado sobre 320 px y su escala a la resolución real (§2), qué región
> ocupa cada elemento, la prioridad de estados del retrato— porque nada de
> eso depende del estilo de trazo; sólo cambia **cómo** se pinta cada
> región, no dónde ni cuándo.
>
> El panel de 9-slice (`hud_frame.png`) lleva un degradado y un halo
> exterior en vez de un relleno plano con borde de 1 px. Las barras
> (vida, estamina, medidor especial, tiempo bala, vida de jefe) usan
> `_dibujar_barra_moderna`: fondo translúcido con esquinas redondeadas,
> relleno con degradado horizontal, y un halo suave cuando el medidor llega
> al tope. La transparencia ya no se limita al fondo de la caja de mensajes
> de tutorial — es parte del lenguaje visual del HUD entero.

> **AUD-535 (2026-08-18) — rediseño espacial, no sólo de trazo.** AUD-527
> cambió *cómo* se pintaba cada región; esta auditoría cambia *dónde* vive
> cada una y qué elementos existen. Pedido explícito del dueño tras jugarlo:
> retrato circular, la fila de corazones desaparece a favor de tres barras
> apiladas (vida/estamina/carga) del mismo ancho que el retrato, el
> marcador se reubica junto al bloque retrato+barras, el cronómetro se
> centra arriba con un ícono de reloj en vez de la etiqueta "TIME" y baja
> su umbral de alerta de 30 a 10 segundos, y el minimapa gana bordes
> totalmente redondeados. Las secciones 2 y 4 de este documento describen
> el layout **de hoy**; donde el número cambió respecto de AUD-455/AUD-499
> se cita esta auditoría, no se borra la cifra anterior.

---

## 2. Layout

El HUD se diseñó sobre una pantalla de 320 px de ancho y se **escala** a la
resolución interna real (`settings.INTERNAL_WIDTH`), hoy 800×600. El factor sale
de dividir una por otra: 800/320 = **2,5**.

AUD-451 — hasta esa auditoría, las coordenadas estaban escritas en píxeles de
la pantalla de 320 y se dibujaban **sin escalar** sobre la de 800: el HUD
ocupaba el 40 % del ancho, arrinconado arriba a la izquierda, y el marcador de
puntos se veía diminuto. La tabla de abajo da las dos columnas —el número de
diseño y el que resulta en pantalla— porque el código sigue escribiéndose en
el primero: es el que se lee junto al dibujo del layout.

Todas las coordenadas son en píxeles, origen arriba a la izquierda.

**AUD-535** reubica el bloque de identidad (retrato circular + tres barras
apiladas) en la esquina superior izquierda, el marcador junto a él, y el
cronómetro al centro superior — ya no en la esquina derecha, que hoy sólo
ocupa el minimapa.

> **AUD-547 (2026-08-19) — márgenes de pantalla y minimapa circular.**
> Jugado, dos cosas del rediseño de AUD-535 seguían sin resolverse: el
> retrato vivía a 2px de maqueta del borde (5px reales) y el minimapa,
> pese al recorte redondeado, seguía siendo un rectángulo de 62×44 —
> **no** un círculo, sólo esquinas muy curvas. `MARGEN_DE_PANTALLA = 6`
> (constante en `hud.py`) es el margen mínimo que ahora respeta todo
> elemento junto a un borde real de la ventana (retrato, marcador,
> cronómetro, minimapa); el minimapa además pasó de 62×44 a **44×44**
> —cuadrado— para que `pygame.draw.circle` lo recorte en un círculo de
> verdad, no una aproximación. De paso, las tres barras del bloque de
> identidad dejaron de cambiar de color según el nivel (verde→ámbar en
> estamina, azul→dorado en carga, rojo→naranja en vida): ahora son
> **rojo/amarillo/azul fijos**, pedido explícito del dueño.

```
┌──────────────────────────────────────────────────────────────┐  Y=0
│  ═══════════════════════════════════════════════════════════  │
│  │   TUTORIAL / STORY MESSAGE BOX (if active)               │  Y=0
│  │   320×28 de diseño (800×70 en pantalla), arriba          ││
│  │                                                           │  Y=14
│  └─────────────────────────────────────────────────────────┘ │
│   (o)   [1234  🪙56]          [🕐 00:00]                       │  Y=16
│  ▬▬▬▬   puntuación             centrado arriba                │  Y=32
│  ▬▬▬▬   rojo/amarillo/azul                                     │  Y=38..44
│  ▬▬▬▬   bajo el retrato                          ( minimapa )  │  Y=50..56
│                                                     círculo     │  Y=26..70
└──────────────────────────────────────────────────────────────┘
```

### 2.1 Regiones del HUD

Las columnas X/Y/Ancho/Alto son de **diseño** (maqueta de 320). Entre
paréntesis, lo medido en pantalla a 800×600 (factor 2,5) — algunas barras
redondean su alto/paso a un píxel real de diferencia por el redondeo de
`theme.escalar`, así que la columna de pantalla es la que manda si las dos
no cuadran a la fracción exacta.

| Elemento | X | Y | Ancho | Alto | En pantalla (×2,5, medido) | Notas |
|---|---|---|---|---|---|---|
| Caja de mensajes | 0 | 0 | 320 | 28 | 0,0 800×70 | Capa superior (movida desde abajo en v1.1.0) |
| Marco del retrato | 6 | 6 | 24 | 24 | 15,15 60×60 | Círculo, no marco 9-slice (AUD-535); margen de pantalla (AUD-547) |
| Sprite del retrato | 7 | 7 | 22 | 22 | 18,18 55×55 | Recortado en círculo al cargar (`_recortar_circular`) |
| Barra de vida | 6 | 32 | 24 | 5 | 15,80 60×12 | Roja, fija (AUD-547) — reemplaza la fila de corazones (AUD-535) |
| Barra de estamina | 6 | 38 | 24 | 5 | 15,94 60×12 | Amarilla, fija (AUD-547) |
| Barra de carga | 6 | 43 | 24 | 5 | 15,108 60×12 | Azul, fija (AUD-547) — medidor especial |
| Puntuación | 36 | 6 | 92 | 24 | 90,15 230×60 | Junto al bloque de identidad, no en la esquina derecha (AUD-535) |
| Minimapa | 270 | 26 | 44 | 44 | 675,65 110×110 | **Circular de verdad** (AUD-547, antes 62×44 con esquinas redondeadas) |
| Caja del temporizador | 134 | 6 | 52 | 16 | 335,15 130×40 | Centrada arriba, no pegada al borde derecho (AUD-535) |
| Ícono del reloj | 137 | 7 | 12 | 12 | 342,18 30×30 | Reemplaza la etiqueta de texto "TIME" |
| Dígitos del temporizador | 151 | 6 | 34 | 14 | 378,15 85×35 | Formato `M:SS` |
| Rótulo de escenario | 0 | 88 | 320 | 48 | 0,220 800×120 | Centro de pantalla, entra deslizando |

Tiempo bala y la barra de vida del jefe no tienen fila fija: tiempo bala
sólo se dibuja si el escenario lo declara (bajo la barra de carga), y la
barra del jefe sólo mientras hay un jefe activo (arriba, centrada).

---

## 3. Retrato

### 3.1 Descripción

El retrato es un sprite de primer plano de 22×22 de maqueta (55×55 en pantalla) del personaje encapuchado, mostrado en la esquina superior izquierda. Es estático (no animado) en juego normal. Se anima en eventos concretos.

### 3.2 Estados del retrato

| Estado | Fichero de sprite | Disparador |
|---|---|---|
| Normal | `ui/portrait_normal.png` | Por defecto |
| Daño | `ui/portrait_hurt.png` | El jugador recibe daño — se muestra 0.8s |
| Crítico | `ui/portrait_critical.png` | Vida del jugador ≤ 1.0 corazón |
| Muerto | `ui/portrait_dead.png` | Vida del jugador == 0 |

### 3.3 Marco del retrato

**AUD-535** — el retrato ya no lleva el marco 9-slice rectangular
(`ui/hud_frame.png`, que sigue existiendo pero sólo la usa el fondo del
cronómetro, §5.2). En su lugar: un disco de fondo, el sprite del retrato
recortado en círculo una sola vez al cargar (`_recortar_circular`, no en
cada fotograma — mismo criterio de rendimiento que AUD-527 con el
degradado de las barras) y un anillo dibujado con `_anillo_del_retrato`,
cacheado por (diámetro, grosor, color). El color del anillo es el mismo
que antes tenía el marco: gris normal, rojo al recibir daño o crítico,
gris oscuro al morir.

### 3.4 Lógica de estado del retrato

```
if current_health == 0:
    portrait_state = "DEAD"
elif current_health <= 1.0:
    portrait_state = "CRITICAL"
elif temporizador_de_dolor > 0:
    portrait_state = "HURT"
    temporizador_de_dolor -= dt
else:
    portrait_state = "NORMAL"
```

Ese temporizador dura 0,8 s desde cada `PLAYER_DAMAGED`. **Es pseudocódigo**: el HUD real no lleva un campo con ese nombre (AUD-150).

---

## 4. Sistema de la barra de vida

> **AUD-535 — sustituye por completo la sección anterior.** Pedido
> explícito: "se eliminan los corazones clásicos para darle un aspecto
> más actual". No queda fila de iconos ni sprites `heart_*.png` que
> cargar — `tools/generate_all_assets.py` ya no los genera y
> `scripts/validate_assets.py` ya no los exige.

### 4.1 Maqueta de la barra de vida

La vida se dibuja como una única barra continua, del mismo ancho que el
marco del retrato, justo debajo de él (`HUD.vida_bar_rect()`, X=6, Y=32,
24×5 de maqueta — AUD-547 movió el bloque completo al margen de
pantalla). Es la primera de tres barras apiladas — vida, estamina,
carga — separadas por 1px de maqueta cada una (`_dibujar_barra_moderna`,
el mismo lenguaje visual de AUD-527: fondo translúcido redondeado,
relleno con degradado horizontal, sin halo al llenarse porque a tope de
vida no hay "logro" que celebrar, a diferencia del medidor especial).

**AUD-547** — las tres barras usan un color fijo cada una, sin variante
de urgencia: vida roja, estamina amarilla, carga azul. Antes vida y
estamina viraban a un segundo color al quedar poco (naranja/ámbar) y la
carga a dorado al llenarse; pedido explícito del dueño para que el color
identifique **qué** mide cada barra, no también **cuánto** le queda —
para eso ya está el propio relleno.

### 4.2 Algoritmo de dibujo

```python
pct = clamp(current_health / max_health, 0.0, 1.0)
color_fin = (230, 60, 60)  # rojo fijo (AUD-547)
dibujar_barra_moderna(vida_bar_rect, pct, color_inicio=(70, 15, 15), color_fin)
```

`ranuras_de_corazon` (la propiedad, no el dibujo) sigue existiendo:
devuelve `max_health` redondeada a entero, y el nombre es historia — lo
usan la lógica de mejoras permanentes y varias pruebas que preguntan
"a cuántas unidades de vida equivale esto", no un recuento de sprites.

### 4.3 Destello de daño y curación

Al recibir `PLAYER_DAMAGED`, la barra entera —no una ranura— destella en
blanco:

- Alterna cada 0.1 s durante 0.6 s (reemplaza el "corazón que baja
  destella" de la fila discreta: una barra continua no tiene ranuras que
  señalar una a una).

Al recibir `PLAYER_HEALED`, la barra recibe un destello verde aditivo que
se desvanece en 0.6 s (reemplaza el llenado de derecha a izquierda con
partícula de brillo por corazón — no hay corazones que llenar en
secuencia, sólo un porcentaje que sube).

---

## 5. Temporizador

### 5.1 Descripción

**AUD-535** — el temporizador se centra arriba de la pantalla (antes,
esquina superior derecha) y pierde la etiqueta de texto "TIME": un ícono
de reloj estilizado (`_icono_de_reloj`, dibujado y cacheado, no un
sprite) la reemplaza. Muestra el tiempo transcurrido en formato `M:SS`
(minutos y segundos). El Stage 0 usa un temporizador ascendente con
fines de demostración. Los escenarios de estudiante usan una cuenta
atrás descendente (configurable vía `HUD.start_timer(seconds)`).

### 5.2 Presentación del temporizador

| Propiedad | Valor |
|---|---|
| Posición | X=134, Y=2 de maqueta — centrado arriba (335,5 de 800 en pantalla; AUD-535, antes pegado al borde derecho) |
| Ancho | 52 px de maqueta (130 en pantalla) |
| Ícono | 12×12 de maqueta, borde izquierdo del marco — reemplaza la etiqueta "TIME" (AUD-535) |
| Formato | `M:SS` (p. ej., `2:34`) |
| Fuente | **TTF** — `assets/fonts/game.ttf` a tamaño 12, cargada con `theme.font()` |
| Color | Blanco sobre fondo oscuro; rojo en alerta (§5.3) |
| Fondo | Panel de 9-slice (`ui/hud_frame.png`) con degradado — el único lugar del HUD que sigue usando ese marco tras AUD-535 |

### 5.3 Comportamiento del temporizador

- **Ascendente (Stage 0):** cuenta desde `0:00` hacia arriba. No dispara fin de partida.
- **Descendente (Stage 1–3):** cuenta atrás desde `time_limit`. Al llegar a `0:00`, emite `PLAYER_DIED` (causa fin de partida).
- **Pausa:** `HUD.pause_timer()` congela la presentación. `HUD.resume_timer()` la reanuda.
- **Destello con poco tiempo:** cuando quedan ≤`HUD.UMBRAL_DE_ALERTA_S` segundos en una cuenta atrás, el ícono y los dígitos pasan a rojo y destellan. **AUD-535** bajó el umbral de 30 a 10 segundos — pedido explícito: "cuando resten exactamente 10 segundos, el contador cambiará de color".
- **Pulso sonoro acelerado (AUD-553):** cada destello emite `Events.SFX_TIMER_ALERT_PULSE` (`sfx_ui_timer_alert_pulse`), y el intervalo entre destellos ya no es fijo — baja de 0,25s a 10s restantes hasta un piso de 0,08s cerca de 0s, interpolado linealmente contra `self._timer`. Es la respuesta a "la música de fondo acelerará su tempo": `pygame.mixer.music` no expone control de tempo sobre un canal en reproducción, así que lo que se acelera de verdad es esta capa de pulso superpuesta — el ritmo lo decide `HUD.update()`, no un DSP que el motor no tiene.

### 5.4 Fuente del temporizador

El temporizador se dibuja con `AssetLoader.load_font` usando `assets/fonts/game.ttf` a tamaño 12 (`engine/ui/hud.py`).

> **AUD-098 — corregido contra el código.**
> Esta sección nombraba fuentes que el motor no usa. El reloj decía cargar
> `fonts/PixeloidSans.ttf`, **un fichero que no existe en el repositorio**;
> el banner, la caja de mensajes y la pantalla de fin de partida decían
> dibujarse con hojas de píxeles `.png`, que tampoco: la clase que sabía
> leerlas (`engine/ui/bitmap_font.py`) estaba muerta y se ha retirado.
>
> Todo el texto del juego pasa por `AssetLoader.load_font` sobre
> `assets/fonts/game.ttf`. Los `.png` de fuente siguen en `assets/fonts/`
> como material de referencia, pero ningún código los carga.


---

## 6. Rótulo de escenario

### 6.1 Descripción

El rótulo de escenario entra deslizándose desde ambos lados de la pantalla al empezar un escenario. Muestra el número y el nombre del escenario en texto pixelado grande. Después, sale deslizándose.

### 6.2 Maqueta del rótulo

```
        ┌────────────────────────────────────┐
        │         ESCENARIO  0                │   Y=88, alto=48
        │     EL  PASILLO  DE  LAS  VERDADES  │
        └────────────────────────────────────┘
```

El rótulo es un compuesto de dos tiras horizontales que entran deslizándose desde la izquierda y la derecha respectivamente:
- Tira superior (contiene el número de escenario): entra desde la izquierda
- Tira inferior (contiene el nombre del escenario): entra desde la derecha

### 6.3 Animación del rótulo

| Fase | Duración | Interpolación |
|---|---|---|
| Entrada | 0.5 segundos | `ease_out_quad` |
| Mantener | 2.0 segundos | Estático |
| Salida | 0.4 segundos | `ease_in_quad` |

Durante la animación del rótulo, el juego sigue corriendo (las entidades se actualizan, el jugador se puede mover). El rótulo es una capa puramente visual.

### 6.4 Sprites del rótulo

- Tira superior: `ui/banner_top.png` — rectángulo oscuro de 320×24 px con borde dorado
- Tira inferior: `ui/banner_bottom.png` — rectángulo oscuro de 320×24 px con borde dorado
- Fuente del número de escenario: `assets/fonts/game.ttf` a tamaño 22 (`engine/ui/screen_banner.py`)
- Fuente del nombre de escenario: `assets/fonts/game.ttf` a tamaño 20 (mismo módulo)

### 6.5 Disparo del rótulo

El rótulo se dispara automáticamente cuando se llama a `on_enter()` de un escenario. `ScreenBanner` lee `stage_name` y `stage_id` de las propiedades del mapa TMX del escenario.

```python
# Se llama automáticamente desde la inicialización del escenario:
self.screen_banner.play(stage_id="stage0", stage_name="El Pasillo de las Verdades")
```

---

## 7. Mensajes de tutorial

### 7.1 Descripción

Los mensajes de tutorial son cajas de texto que aparecen en la parte superior de la pantalla. Los disparan zonas `MessageTrigger` en el mapa TMX (ver `06_TMX_SPEC.md` §10). Comunican al jugador explicaciones del sistema del framework, pistas y matices narrativos.

### 7.2 Maqueta de la caja de mensajes

```
┌──────────────────────────────────────────────────────────────┐ Y=0
│  ▶  Camina a la derecha para continuar.                      │
│     Usa Z para atacar enemigos.                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘ Y=28
```

| Propiedad | Valor |
|---|---|
| Posición | X=0, Y=0 |
| Tamaño | 320×28 de diseño (800×70 en pantalla) |
| Fondo | Oscuro semitransparente (alfa 180/255) |
| Borde | 1px sólido dorado |
| Color de texto | Blanco |
| Fuente | `assets/fonts/game.ttf` a tamaño 12 (`engine/ui/message_box.py`) |
| Líneas máximas | 3 |
| Caracteres máx./línea | 58 (con relleno izquierdo/derecho de 6px) |
| Icono indicador | `ui/message_arrow.png` — flecha de 5×7, se anima esperando confirmación |

### 7.3 Animación de revelado del mensaje

El texto se revela carácter a carácter a razón de 30 caracteres por segundo (efecto máquina de escribir). Se implementa con un contador en coma flotante que sube `30 * dt` cada fotograma y del que se dibujan sólo los primeros `int(...)` caracteres. **El nombre del campo real está en `MessageBox`**; aquí se describe el algoritmo, no la variable (AUD-150).

### 7.4 Descarte de mensajes

Los mensajes se descartan de dos formas:

1. **Descarte automático:** si `duration > 0`, el mensaje se quita `duration` segundos después de que termina de revelarse el texto.
2. **Descarte manual:** si `duration == 0`, el jugador debe pulsar `CONFIRM` (Enter/Z/botón A) para descartarlo. La flecha animada se muestra mientras se espera la confirmación.

### 7.5 Cola de mensajes

Si se emite un segundo evento `SHOW_MESSAGE` mientras ya hay un mensaje mostrándose, el nuevo mensaje se encola. La cola procesa los mensajes en orden.

### 7.6 Interfaz de eventos

```python
# Disparar un mensaje desde un escenario (el emit a nivel de módulo también funciona):
from src.engine.core.event_bus import emit
emit("SHOW_MESSAGE", text="Camina a la derecha para continuar.\nUsa Z para atacar.", duration=5.0)

# Disparar un mensaje que exige confirmación:
emit("SHOW_MESSAGE", text="Pulsa Enter para continuar.", duration=0)

# Limpiar todos los mensajes:
emit("HIDE_MESSAGE")
```

---

## 8. Pantalla de fin de partida

### 8.1 Descripción

Cuando el jugador muere, se apila `GameOverScene` sobre el escenario actual. El escenario queda pausado debajo. La pantalla de fin de partida presenta dos opciones al jugador.

### 8.2 Maqueta

```
        ╔══════════════════════════════════╗
        ║                                  ║  (Capa oscura, alfa 200/255)
        ║        F I N   D E   L A         ║  Y=80, centrado
        ║           P A R T I D A          ║
        ║    ▶  CONTINUAR                  ║  Y=120, opción 1
        ║       SALIR AL TÍTULO            ║  Y=136, opción 2
        ║                                  ║
        ╚══════════════════════════════════╝
```

### 8.3 Animación

1. La pantalla se oscurece lentamente durante 1.0 segundo (el alfa de fondo interpola de 0 a 200).
2. El texto de fin de partida aparece con un efecto de barrido de línea de escaneo (de arriba a abajo, 0.5 segundos).
3. Las opciones aparecen tras revelarse el texto por completo (interpolación de alfa de 0.3 segundos).

### 8.4 Opciones

| Opción | Acción |
|---|---|
| CONTINUAR | Desapila `GameOverScene`. Reanuda el escenario desde el último checkpoint. Restaura la vida completa del jugador. |
| SALIR AL TÍTULO | Reemplaza la pila de escenas por `TitleScene`. Sin conservación de estado. |

### 8.5 Navegación de selección

- `MOVE_UP` / `MOVE_DOWN` navegan entre las opciones.
- `CONFIRM` selecciona la opción resaltada.
- La opción seleccionada se resalta con un color más brillante y el indicador `▶`.

### 8.6 Sprites

| Elemento | Fichero |
|---|---|
| Capa de fondo | `pygame.Surface` rellena con `set_alpha()` |
| Texto de fin de partida | `assets/fonts/game.ttf`, vía el kit de UI compartido |
| Texto de las opciones | `assets/fonts/game.ttf`, vía el kit de UI compartido |
| Flecha de selección | `ui/menu_arrow.png` — 5×8 px |

---

## 9. Pantalla de continuar

### 9.1 Descripción

Si el jugador elige CONTINUAR en la pantalla de fin de partida, se desapila `GameOverScene` y el escenario se reanuda. Se reproduce una breve confirmación visual:

1. La pantalla se ilumina desde el negro durante 0.5 segundos.
2. El jugador reaparece en la posición del checkpoint con una animación de "materialización" (el sprite del jugador se desvanece hacia adentro durante 0.4 segundos, aplicando `set_alpha()` de 0 a 255).
3. La barra de vida del HUD se rellena de 0 a completo, con el destello de curación de §4.3.
4. El temporizador del escenario se reanuda (si es cuenta atrás, no se reinicia — el tiempo restante se conserva).

### 9.2 Invencibilidad al reaparecer

El jugador recibe 2.0 segundos de invencibilidad inmediatamente al reaparecer (el doble de la duración estándar de invencibilidad). Esto evita una re-muerte instantánea por enemigos cercanos que puedan haber perseguido al jugador hasta el checkpoint.

---

## 10. Suscripciones a eventos del HUD

El HUD se suscribe a los siguientes eventos del EventBus:

| Evento | Manejador | Efecto |
|---|---|---|
| `PLAYER_DAMAGED` | `_on_player_damaged(amount, source)` | Baja la barra de vida, dispara el retrato de daño, arranca el destello rojo |
| `PLAYER_HEALED` | `_on_player_healed(amount)` | Sube la barra de vida, arranca el destello verde |
| `PLAYER_DIED` | `_on_player_died()` | Fija el retrato a MUERTO; congela el temporizador |
| `CHECKPOINT_REACHED` | `_on_checkpoint(checkpoint_id)` | Sin cambio de HUD (el checkpoint gestiona lo visual) |
| `SHOW_MESSAGE` | `_on_show_message(text, duration)` | Muestra la caja de mensajes |
| `HIDE_MESSAGE` | `_on_hide_message()` | Limpia la caja de mensajes al instante |
| `STAGE_COMPLETE` | `_on_stage_complete()` | Oculta los elementos del HUD, empieza el desvanecido |

---

## 11. Integración del HUD con los escenarios

El HUD lo instancia `App` una vez por sesión de la aplicación. Se pasa a cada escenario durante la inicialización, vía el `on_enter()` del escenario.

```python
# En la inicialización de App:
self.hud = HUD()

# En el on_enter() del escenario:
self.hud.start_timer(seconds=self.time_limit)  # 0 para ascendente (Stage 0)

# En el draw() del escenario:
# El HUD se dibuja al final — encima de todo
self.hud.update(dt)
self.hud.draw(self.internal_surface)
```

Los estudiantes no llaman a `HUD.draw()` directamente. La clase base de escenario lo llama automáticamente después de que termina el `draw()` propio del escenario.

---
## 🔗 Documentos relacionados

- [[40_DIALOGUE_SYSTEM.md|Sistema de diálogo]]
- [[04_PLAYER_SPEC.md|Especificación del jugador]]
