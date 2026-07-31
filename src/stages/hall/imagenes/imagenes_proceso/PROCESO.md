# Proceso de desarrollo — Stage 3-2 "El Hall"

Jose Pablo Monestel Cruz

Registro de las iteraciones reales del diseño, en orden. Se documenta aquí
porque varias capturas intermedias de depuración se generaron y se
enviaron directo en el chat durante el proceso, y no todas quedaron
guardadas como archivo — este documento reconstruye esa historia en texto
con el detalle técnico exacto de cada cambio, en vez de imágenes que ya no
se pueden recuperar tal cual se vieron en su momento.

## 1. Andamiaje inicial

Copiado desde `student_templates/stage_template/` a `src/stages/hall/`:
`hall.py` (heredando de `StageScene`), `hall.tmx` inicial (40×14 tiles, el
tamaño por defecto de la plantilla). Tileset placeholder (bloques de color
planos) mientras se conseguía el arte real.

## 2. Diseño de la estética y el tileset real

A partir de una imagen de referencia (paleta azul-morada oscura, luces
cálidas) y el archivo `tileset_gavilan_ciudad.tsx` (60 tiles con nombre
semántico ya definidos: `suelo_sup`, `muro`, `columna`, `plat_izq/med/der`,
marcos de ventana, elementos de parallax, etc.), se generó
`tileset_gavilan_ciudad.png` por código (`tools/generate_tileset_gavilan_ciudad.py`),
siguiendo el mismo enfoque procedural que ya usa el proyecto en
`tools/pixel_asset_generator.py` para `tileset_stage0.png` — paleta fija de
16 colores, un dibujo por tile.

## 3. Bug — cámara pegada a una esquina (mapa demasiado pequeño)

El mapa inicial (640×224px, heredado del template) era más chico que la
resolución interna de la cámara (800×600px, `settings.py`). `Camera.update()`
calcula su offset de scroll como `clamp(offset, 0, map_size - screen_size)`
— cuando el mapa es más chico que la pantalla en cualquier eje, ese clamp
se fuerza a exactamente 0 siempre, así que el mapa se dibuja pegado a una
esquina de un lienzo mucho más grande, con las entidades apareciendo
"flotando" en el resto del lienzo negro sin usar.

**Corrección:** el mapa se agrandó a 1024×608px (64×38 tiles), siguiendo la
misma convención que ya usa `stage0.tmx` (1600×608px) — el único stage que
ya funcionaba en el proyecto.

## 4. Ajustes de diseño solicitados (iterativos)

- Hueco central en el balcón (3 tiles) para partir el recorrido en dos
  tramos, saltable u opcional para caer al piso.
- Caja obstáculo sólida cerca del spawn, entre las dos primeras
  plataformas de la escalera — sin esto el piso era una línea recta
  caminable de punta a punta y el balcón resultaba opcional.
- Fondo (parallax): de un patrón repetitivo simple a un skyline
  irregular con alturas variables por columna (semilla fija,
  reproducible) y una luna (cluster de tiles `brillo`/`brillo_suave`),
  combinando la paleta de referencia con lo ya construido.

## 5. Bug — muerte falsa al cruzar el pozo (primera aparición)

Se agregó un pozo (`DeathPit`) bajo el hueco del balcón, cruzado con una
caja de impulso + una plataforma flotante de 1 tile (16px) en el medio. El
jugador reportó morir incluso saltando "exitosamente". Causa real: el
hitbox del jugador mide 20px de ancho — más ancho que la plataforma de
16px — así que aun "parado correctamente" una esquina del rect seguía
tocando el `DeathPit` (`HazardSystem` compara el rect completo del
jugador, no solo sus pies). **Corrección temporal:** se quitó la
plataforma intermedia; cruce directo de 32px (2 tiles de pozo).

## 6. Bug — salto imposible en la escalada final

Al pedir una salida más lejana y compleja (un gauntlet de plataformas), la
primera versión resultó imposible de cruzar. Causa real: el estimador de
alcance de salto del propio proyecto (`level_metrics.py`) usa la velocidad
de suelo completa (~85px), pero el controlador real del jugador
(`src/framework/entities/states/airborne.py`) aplica **la mitad** de esa
velocidad en el aire — el alcance horizontal real de un salto sencillo es
**~43px**, no ~85px. Verificado leyendo el código del controlador, no solo
el estimador. **Corrección:** toda la geometría se recalculó con saltos
horizontales ≤32px (margen real bajo el máximo verificado).

## 7. Bug — golpe con el techo

Con la escalada corregida en distancia horizontal, las plataformas más
altas (a solo 16-48px del techo sólido) seguían fallando: el salto del
jugador es un arco balístico fijo (~90px) que el juego no acorta a
propósito — si el techo cae dentro de ese arco, el jugador se golpea la
cabeza, pierde la velocidad vertical restante Y el tiempo de aire que
necesitaba para el salto horizontal, y cae aunque el salto se viera bien
ejecutado. **Corrección:** ninguna plataforma de una ruta queda a menos de
112px del techo (fila ≥13 en el grid de 16px).

## 8. Rediseño — util both sides + puerta central

Se pidió que el lado derecho del mapa (antes un tramo "opcional" separado)
tuviera utilidad real, y que la puerta final fuera accesible desde ambos
lados en vez de al final de un solo camino largo. **Rediseño:** dos rutas
de plataformas — una desde el balcón (oeste) y otra desde un pedestal
cerca del checkpoint (este) — que convergen en una sola repisa compartida
cerca de la mitad horizontal del hall, donde está la puerta.

## 9. Bug — recurrencia de la muerte falsa en el pozo

El pozo de 32px (paso 5) todavía dejaba solo ~11px de margen entre el
hitbox del jugador (20px) y el borde lejano del `DeathPit` — suficiente
para que un salto "exitoso" siguiera tocando el pozo en el aterrizaje.
**Corrección final:** pozo reducido a 1 tile (16px), margen real de ~27px.
Verificado esta vez con una prueba directa sobre el motor (no solo
cálculo): se posicionó al jugador dentro del pozo (muere, correcto) y 1px
pasado el borde (sobrevive, correcto).

## 10. Entrega

Documentación (`README.md` con fórmulas exactas), limpieza de nombres de
archivos internos (`Jose Pablo Monestel Cruz`), pruebas finales sobre el
motor real (recorrido, salto, colisión, daño de combate — sin errores), y
empaquetado del `.zip`.

## 11. Bug — la lámpara colgante nunca se movía

Después de entregado, se reportó que la lámpara (`SwingingLamp`, la
entidad que demuestra el requisito de vectores) no se veía balancearse.
Verificado directamente contra el motor: la entidad existía, estaba viva
y visible, pero su posición no cambiaba nunca, ni después de 30 frames de
`scene.update()`.

**Causa real:** el bucle de actualización propio de `StageScene` solo
llama `.update(dt)` sobre las entidades que son instancias de `EnemyBase`
— construye su lista de "enemigos" del frame filtrando `entity_list` con
`isinstance(entity, EnemyBase)` antes de tocar nada más
(`stage_scene.py`, actualización de gameplay). `SwingingLamp` es una
`BaseEntity` simple (correctamente — no es un enemigo, no tiene vida), así
que quedaba fuera de ese filtro y nunca avanzaba: se dibujaba porque
`DrawingSystem._draw_entities` sí recorre `entity_list` completo sin ese
filtro, pero congelada en su posición de aparición.

**Corrección (solo en `src/stages/hall/hall.py`, sin tocar el motor):** se
guardan las lámparas en `self._lamps` al crearlas, y se sobrescribe
`Hall.update(dt)` (llamando primero a `super().update(dt)` para preservar
todo el comportamiento normal del stage) para avanzar manualmente cada
lámpara cada frame. Verificado de nuevo contra el motor real: la posición
X ahora oscila genuinamente entre ~410 y ~430px a lo largo del tiempo, en
vez de quedarse fija.
