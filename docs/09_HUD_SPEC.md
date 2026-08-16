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
**Versión:** 1.2.0
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

Todos los gráficos del HUD son sprites de pixel art acordes a la estética de la época SNES. Sin antialiasing. Sin degradados. Sin sombras mezcladas por alfa. La transparencia se usa sólo en el fondo de la caja de mensajes de tutorial.

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

```
┌──────────────────────────────────────────────────────────────┐  Y=0
│  ═══════════════════════════════════════════════════════════  │
│  │   TUTORIAL / STORY MESSAGE BOX (if active)               │  Y=0
│  │   320×28 de diseño (800×70 en pantalla), arriba          ││
│  │                                                           │  Y=14
│  └─────────────────────────────────────────────────────────┘ │
│  [PORTRAIT]  [♥♥♥♥♥]                          [TIMER: 0:00] │  Y=16
│   32×32       76×8                               54×12       │
│                                                               │  Y=28
│                                                               │
│                                                               │  Y=224 (diseño)
└──────────────────────────────────────────────────────────────┘
```

### 2.1 Regiones del HUD

Las columnas X/Y/Ancho/Alto son de **diseño** (pantalla de 320). Entre
paréntesis, lo que mide en pantalla al multiplicar por 2,5.

| Elemento | X | Y | Ancho | Alto | En pantalla (×2,5) | Notas |
|---|---|---|---|---|---|---|
| Caja de mensajes | 0 | 0 | 320 | 28 | 0,0 800×70 | Capa superior (movida desde abajo en v1.1.0) |
| Marco del retrato | 2 | 2 | 24 | 24 | 5,5 60×60 | Marco del retrato (AUD-499) |
| Sprite del retrato | 3 | 3 | 22 | 22 | 8,8 55×55 | Sprite interior, deriva del marco |
| Fila de corazones | 38 | 6 | 76 | 8 | 95,15 190×20 | Cinco corazones, separación 16 de diseño |
| Puntuación | 124 | 2 | 128 | 14 | 310,5 320×35 | Puntos y monedas, alineado a la derecha (AUD-219) |
| Medidor especial | 84 | 30 | 60 | 6 | 210,75 150×15 | Barra del ultimate; oro cuando está llena (AUD-455 rescata las tres barras sin escalar) |
| Minimapa | 258 | 20 | 62 | 44 | 645,50 155×110 | Debajo del cronómetro (AUD-499) |
| Estamina | 84 | 40 | 60 | 4 | 210,100 150×10 | Ámbar por debajo de 34 % (AUD-141, AUD-455) |
| Tiempo bala | 84 | 46 | 60 | 4 | 210,115 150×10 | Azul guardada, blanco en uso (AUD-260, AUD-455) |
| Caja del temporizador | 258 | 1 | 62 | 16 | 645,2 155×40 | Alineado a la derecha |
| Dígitos del temporizador | 288 | 2 | 32 | 14 | 720,5 80×35 | Formato `M:SS` |
| Rótulo de escenario | 0 | 88 | 320 | 48 | 0,220 800×120 | Centro de pantalla, entra deslizando |

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

El retrato está rodeado de un marco de borde de 1px dibujado del tileset `ui/hud_frame.png`. El marco es un sprite escalable de 9 recortes: las esquinas miden 2×2, los bordes 1px de grosor.

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

## 4. Sistema de corazones

### 4.1 Maqueta del medidor de corazones

El medidor de corazones muestra cinco iconos en una fila horizontal en X=38, Y=6. Cada icono de corazón mide 14×8 píxeles (formato ancho para claridad SNES). Los corazones se dibujan de izquierda a derecha. El corazón más a la izquierda representa el primer corazón completo; el de más a la derecha, la última fracción.

**Separación de corazones:** icono de 14px + 2px de hueco = 16px por espacio. Ancho total: 5×14 + 4×2 = 78px.

### 4.2 Sprites de icono de corazón

| Estado | Fichero | Descripción |
|---|---|---|
| Completo | `ui/heart_full.png` | Corazón sólido, 14×8 px |
| Tres cuartos | `ui/heart_three_quarter.png` | 25% derecho vacío |
| Mitad | `ui/heart_half.png` | Mitad derecha vacía |
| Cuarto | `ui/heart_quarter.png` | Sólo el cuarto izquierdo sólido |
| Vacío | `ui/heart_empty.png` | Sólo contorno |

### 4.3 Algoritmo de dibujo de corazones

Para cada uno de los cinco espacios de corazón (i = 0 a 4):

```python
heart_value = clamp(current_health - i, 0.0, 1.0)

if heart_value >= 1.0:
    sprite = "heart_full"
elif heart_value >= 0.75:
    sprite = "heart_three_quarter"
elif heart_value >= 0.50:
    sprite = "heart_half"
elif heart_value >= 0.25:
    sprite = "heart_quarter"
else:
    sprite = "heart_empty"

blit(sprite, x=(38 + i * 16), y=6)
```

### 4.4 Destello de daño en corazones

Al recibir `PLAYER_DAMAGED`, el medidor de corazones hace destellar el corazón perdido:

- El icono de corazón que bajó destella entre su nuevo estado y el anterior.
- Frecuencia del destello: alterna cada 4 fotogramas.
- Duración del destello: 0.6 segundos (unos 9 destellos a 60 FPS).

### 4.5 Efecto de curación de corazones

Al recibir `PLAYER_HEALED` (p. ej., tras restaurar vida en un checkpoint):

- Los corazones se llenan de derecha a izquierda, en secuencia.
- Cada corazón se llena con 0.1 segundos de retraso entre ellos.
- Se reproduce un pequeño efecto de partícula de brillo en cada corazón al llenarse (sprite: `ui/heart_sparkle.png`, 4 fotogramas, 12 FPS).

---

## 5. Temporizador

### 5.1 Descripción

El temporizador se muestra en la esquina superior derecha del HUD. Muestra el tiempo transcurrido en formato `M:SS` (minutos y segundos). El Stage 0 usa un temporizador ascendente con fines de demostración. Los escenarios de estudiante usan una cuenta atrás descendente (configurable vía `HUD.start_timer(seconds)`).

### 5.2 Presentación del temporizador

| Propiedad | Valor |
|---|---|
| Posición | X=264, Y=24 (ajustado en v1.1.0 por la caja de mensajes arriba) |
| Ancho | 54 px |
| Formato | `M:SS` (p. ej., `2:34`) |
| Fuente | **TTF** — `assets/fonts/game.ttf` a tamaño 12, cargada con `AssetLoader.load_font` |
| Color | Blanco sobre fondo oscuro |
| Fondo | Rectángulo oscuro sólido detrás de los dígitos |

### 5.3 Comportamiento del temporizador

- **Ascendente (Stage 0):** cuenta desde `0:00` hacia arriba. No dispara fin de partida.
- **Descendente (Stage 1–3):** cuenta atrás desde `time_limit`. Al llegar a `0:00`, emite `PLAYER_DIED` (causa fin de partida).
- **Pausa:** `HUD.pause_timer()` congela la presentación. `HUD.resume_timer()` la reanuda.
- **Destello con poco tiempo:** cuando quedan ≤30 segundos en una cuenta atrás, los dígitos destellan en rojo a 2 Hz.

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
3. El medidor de corazones del HUD se rellena de 0 a completo con la animación de curación (§4.5).
4. El temporizador del escenario se reanuda (si es cuenta atrás, no se reinicia — el tiempo restante se conserva).

### 9.2 Invencibilidad al reaparecer

El jugador recibe 2.0 segundos de invencibilidad inmediatamente al reaparecer (el doble de la duración estándar de invencibilidad). Esto evita una re-muerte instantánea por enemigos cercanos que puedan haber perseguido al jugador hasta el checkpoint.

---

## 10. Suscripciones a eventos del HUD

El HUD se suscribe a los siguientes eventos del EventBus:

| Evento | Manejador | Efecto |
|---|---|---|
| `PLAYER_DAMAGED` | `_on_player_damaged(amount, source)` | Actualiza corazones, dispara el retrato de daño, arranca el destello |
| `PLAYER_HEALED` | `_on_player_healed(amount)` | Anima el relleno de corazones |
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
