# Reporte de defectos — Stage 1-1 «La Entrada»

**Estudiante:** Fabrizio Espinoza Arce · **Entrega:** Evaluación Práctica II — Vertical Slice
**Fecha:** 2026-08-26

Formato según §25 del documento *«Claude Code + MCP para desarrollo de niveles»*.

---

## Regla de trabajo

> **Un defecto del motor, del framework o de las herramientas NO se corrige
> desde la carpeta del escenario: se reporta.** Y no se toca hasta tenerlo
> capturado en video, porque la evidencia es parte del entregable.

Por eso los hallazgos van separados en dos bloques, y los del motor están en
`REPORTADO`, no en `FIXED`.

**Estado de la evidencia.** Las capturas de esta tabla salen del bot de
playtest del profesor (`tests/playtest/bot.py`) ejecutado con
`herramientas/jugar_y_capturar.py`. **Falta el video de la sesión
humana**, que es lo que cierra el reporte.

---

## Bloque A — Motor, framework y herramientas · **NO TOCAR**

### F-001 · `moderngl` está documentado como opcional pero es obligatorio

| | |
|---|---|
| **Tipo** | TECHNICAL |
| **Severidad** | **ALTA** |
| **Estado** | REPORTADO — pendiente de video |

**Problema.** `pyproject.toml` declara `ModernGL` dentro del extra opcional
`accel`, y el comentario promete que «el juego detecta cada uno al importar y
cae a un camino de software cuando falta». No es cierto: se importa **sin
proteger** en dos sitios.

**Evidencia.**
```
src/engine/render/gl_pipeline.py:8       import moderngl
src/engine/render/gpu_sprite_batch.py:42 import moderngl
src/engine/core/app.py:180               import moderngl   <- el unico protegido
```
Sin él, `stage1_1` no carga: el calificador cae de **130/130 a 100/130** y
tres pruebas fallan con `ModuleNotFoundError`.

**Agravante.** No hay rueda de `moderngl` para **Python 3.14**: `pip` baja el
`.tar.gz` e intenta compilarlo, y falla con *«Unable to find a compatible
Visual Studio installation»*. La matriz de CI declara 3.11/3.12/3.13, así que
el problema no salta en CI — sólo en la máquina de quien use 3.14, que es la
versión del `.venv` que venía en el `.zip`.

**Causa probable.** Los dos módulos nuevos de GPU se añadieron sin envolver el
import como sí hace `app.py`.

**Solución propuesta.** Envolver los dos imports igual que en `app.py:180`, o
mover `ModernGL` de `accel` a las dependencias base.

---

### F-002 · El minimapa es cuadrado y el nivel es 6:1 — se desperdicia el 83 %

| | |
|---|---|
| **Tipo** | UX |
| **Severidad** | MEDIA |
| **Estado** | REPORTADO — pendiente de video |

**Problema.** El recuadro del minimapa es **44 × 44** en la maqueta de 320
(`hud.py:247`, `RECUADRO_MINIMAPA_DISENO`), o sea 110 × 110 px en pantalla.
Stage 1-1 mide 240 × 40 tiles = 3840 × 640 px, proporción **6:1**.

**Evidencia.** `capturas/playtest_contactos.png` (recorte ×5 del
fotograma `jugado_06.png`). Todo el contenido —jugador, enemigos, puntos de
control, zona explorada— vive en una franja de 18 px en el borde superior; el
resto es negro.

```
nivel  3840 x 640 px   proporcion 6,0:1
panel   110 x 110 px   proporcion 1,0:1
-> el nivel ocupa 110 x 18 px  ->  83 % del panel queda vacio
```

**Causa.** `_world_to_minimap_local` (`minimap.py:112`) aplica **la misma
escala a los dos ejes**, que es lo correcto para no deformar el mapa. El
problema no es la fórmula: es que el panel sea cuadrado. Un panel cuadrado
sirve para un nivel tipo *metroidvania*; para un lateral ancho no.

**Solución propuesta.** Que el recuadro tome la proporción del mapa cargado,
con un alto mínimo. Afecta a los 15 mapas del curso, no sólo a éste.

---

### F-003 · `apply_kernel` recorta a [0, 255] y pierde la mitad del gradiente

| | |
|---|---|
| **Tipo** | TECHNICAL |
| **Severidad** | MEDIA |
| **Estado** | REPORTADO — pendiente de video |

**Problema.** `FilterTools.apply_kernel` termina con
`result.clip(0, 255).astype(np.uint8)`. Para un kernel **con signo** como
Sobel, eso borra toda la respuesta negativa.

**Evidencia.** Sobre un borde de oscuro a claro (96 × 96, mitad a 10 y mitad
a 245):

```
convolucion cruda con sobel_y : min = -940   max = 0
apply_kernel(sobel_y)         : min =    0   max = 0     <- todo cero
sobel_edge (misma imagen)     : max =  255   media 5,31
```

**Por qué importa.** La rúbrica de la Práctica II pide usar `apply_kernel`
para la Unidad VII. Quien lo use tal cual para Sobel obtiene una imagen negra
y no sabrá por qué.

**Vuelta encontrada.** Aplicar el kernel **y su negado** y sumarlos reconstruye
|G| sin salir de la API: `|G| = apply_kernel(k) + apply_kernel(-k)`.
Verificado — el resultado coincide **píxel a píxel** con `sobel_edge`
(`tests/test_enfoque_bordes.py::test_la_referencia_coincide_con_sobel_edge_del_framework`).

**Solución propuesta.** Documentarlo en el docstring, u ofrecer un
`apply_kernel_signed` que devuelva el array sin recortar.

---

### F-004 · Los ejes de `apply_kernel` están transpuestos respecto del kernel

| | |
|---|---|
| **Tipo** | TECHNICAL (documentación) |
| **Severidad** | BAJA |
| **Estado** | REPORTADO — pendiente de video |

**Problema.** `pygame.surfarray.array3d` entrega la imagen como `[x][y]`,
pero un kernel se escribe como `[fila][columna]` = `[y][x]`. El resultado es
que `sobel_x` responde a los bordes **horizontales** y `sobel_y` a los
verticales — al revés de lo que sugiere el nombre.

**Evidencia.** Sobre un borde vertical, `apply_kernel(sobel_x)` da `max = 0`;
`sobel_y` es el que responde.

**Impacto.** Ninguno en el resultado final si se combina la magnitud de los
dos. Pero cuesta media hora de desconcierto la primera vez.

**Solución propuesta.** Una línea en el docstring de `apply_kernel`.

---

### F-005 · El calificador premia un salto que el propio movimiento apenas puede hacer

| | |
|---|---|
| **Tipo** | BALANCE (herramienta) |
| **Severidad** | MEDIA |
| **Estado** | REPORTADO — pendiente de video |

**Problema.** `grade_stage.py` da 3 puntos de `design_pacing` sólo si el nivel
tiene al menos un hueco **exigente**, que `classify_gap` define como
`> 0,80 · max_gap` = **34,2 px**. Pero el alcance natural del salto son
**42,8 px**, y los tiles miden 16, así que el primer hueco que califica como
exigente es de 48 px.

**Evidencia.** El propio banco del profesor,
`python -m tests.playtest.jump_bench`:

```
HUECOS            natural            experta
tiles  px    despegues  margen   despegues  margen
    2   32     19/49     39%      49/49    100%
    3   48      4/49      8%      46/49     94%
```

Un hueco de 3 tiles se cruza desde **4 de 49 posiciones de despegue** con la
técnica natural. Es un salto de precisión.

**Consecuencia.** La rúbrica empuja a meter en un nivel de tutorial un salto
que exige soltar la dirección al despegar — una técnica que el juego no
enseña en ninguna parte.

**Solución propuesta.** Bajar el umbral de «exigente» a la franja
34,2–42,8 px, o avisar en el informe de que el hueco exige técnica experta.

---

### F-006 · `CONTRIBUTING.md` y `CODEOWNERS` describen un acceso que ya no existe

| | |
|---|---|
| **Tipo** | TECHNICAL (documentación) |
| **Severidad** | BAJA |
| **Estado** | REPORTADO |

**Problema.** Los dos documentos dicen que el repositorio es **privado** y que
cada estudiante tiene rol **`Read`**, por lo que «no pueden empujar una rama
aquí directamente» y deben hacer *fork*.

**Evidencia.** `GET /repos/pcruzcr/legacyofInfest` devuelve hoy:

```json
{"permisos": {"push": true, "pull": true, "triage": true},
 "privado": false, "rama_default": "dev"}
```

**Impacto.** Un estudiante que siga el documento hará un fork innecesario.

---

### F-010 · `walk_right_bot` no puede saltar: da falsos «nivel infranqueable»

| | |
|---|---|
| **Tipo** | TECHNICAL (herramienta de pruebas) |
| **Severidad** | **ALTA** — afecta a los 15 niveles del curso |
| **Estado** | REPORTADO — pendiente de video |

**Problema.** El salto del motor es de **altura variable**: mantener el botón
sube más, soltarlo corta el impulso. `walk_right_bot`
(`tests/playtest/bot.py:77`), que es el bot de referencia para «¿se puede
avanzar por este nivel?», mantiene `JUMP` **dos fotogramas**.

Resultado: nunca da un salto entero. Se eleva **53 px de los 96** que da el
salto completo, y por tanto **no puede subir escalones de más de ~50 px** que
una persona sube sin pensarlo.

**Evidencia.** Trazando la velocidad vertical fotograma a fotograma
(`herramientas/trazar_salto.py`):

```
dy:  -6,1  -5,9  -5,7     subiendo a plena fuerza
     -2,6  -2,4  -2,2     cortado de golpe en el fotograma 4
```

Y el mismo escalón de 48 px medido con los dos estilos de salto
(`herramientas/probar_escalon.py`):

```
estilo de salto                        altura    suben
toque, 2 fotogramas (walk_right_bot)    53 px    2/49
mantenido, 18 fotogramas (persona)      96 px   15/49
```

Y el nivel entero:

```
bot                        avance   llega a la salida
walk_right_bot              45 %    NO  (clavado en x=1773)
mantiene el salto 12 fot.   99 %    SI  (140 s, 0 muertes)
```

**Por qué importa.** El comentario de `walk_right_bot` dice que un nivel donde
el bot no progresa «tiene un problema de geometría, no de habilidad». Con el
salto cortado eso deja de ser cierto, y el bot acusa de infranqueables niveles
que están bien. A mí me costó revertir un cambio de nivel que ya había hecho
sobre esa acusación falsa.

Hay un precedente en el propio repo: la cabecera del bot cuenta que en AUD-070
ya hubo que subir la frecuencia de salto porque «una prueba que pasaba **por la
avería** deja de pasar». Es el mismo tipo de problema, un escalón más arriba.

**Solución propuesta.** Que `walk_right_bot` mantenga `JUMP` una docena de
fotogramas, o que acepte la duración como parámetro. Tres líneas:

```python
def walk_right_bot(seconds=30.0, jump_every=24, jump_hold=12):
    ...
    script.append((max(1, run - jump_hold), {Action.MOVE_RIGHT}))
    script.append((jump_hold, {Action.MOVE_RIGHT, Action.JUMP}))
```

**Nota sobre `stuck_frames`.** De paso: `run_playthrough` cuenta atasco cuando
el avance horizontal baja de 1 px por fotograma, y en el aire el jugador se
desplaza a 0,8 px/fotograma. Un bot que salta a menudo marca atasco sin estar
atascado. Conviene medir el atasco sólo cuando el jugador está en el suelo.

---

### F-011 · El juego sólo arranca si te paras en la carpeta del repositorio

| | |
|---|---|
| **Tipo** | TECHNICAL (usabilidad) |
| **Severidad** | MEDIA |
| **Estado** | REPORTADO — pendiente de video |

**Problema.** `python <ruta_completa>/main.py --stage stage1_1` falla si el
directorio actual no es la raíz del repositorio, aunque la ruta a `main.py`
sea absoluta y el intérprete sea el correcto.

**Evidencia.** Mismo comando, mismo Python, sólo cambia el directorio actual:

```
cwd = C:\           ->  FrameworkUsageError: TMX file not found:
                        assets\maps\stage1_1\stage1_1.tmx
cwd = <repo>        ->  carga bien
```

**Causa.** Los escenarios declaran su mapa con una ruta **relativa**
(`TMX_PATH = "assets/maps/stage1_1/stage1_1.tmx"`, y lo mismo en `stage0` y en
la plantilla de estudiante), y `StageLoader` la resuelve con
`tmx_path.resolve()` (`stage_loader.py:175`), que en una ruta relativa resuelve
contra el **directorio actual**.

**Lo llamativo:** el motor ya sabe dónde vive. `settings.py:31` calcula
`PROJECT_ROOT` desde `__file__` justamente para que el directorio actual no
importe, y `ASSETS_DIR` sale de ahí. El propio `stage_loader.py` usa
`settings.PROJECT_ROOT` unas líneas más abajo (`_bajo(tmx_path,
settings.PROJECT_ROOT)`) para el control de mapas hostiles. Sólo falta usarlo
también para resolver.

**Impacto.** Le pasa a cualquiera que haga doble clic en `main.py`, lo lance
desde un acceso directo, o lo arranque desde un IDE con otro directorio de
trabajo. El mensaje de error (*«TMX file not found»*) señala al mapa, que está
perfectamente bien, en vez de al directorio — así que se busca el fallo donde
no está.

**Solución propuesta.** En `StageLoader.load()`, resolver las rutas relativas
contra `PROJECT_ROOT` antes que contra el directorio actual:

```python
if not tmx_path.is_absolute():
    tmx_path = settings.PROJECT_ROOT / tmx_path
```

---

### F-012 · `ESC` no pausa: abre y cierra el menú en el mismo gesto

| | |
|---|---|
| **Tipo** | UX / entrada |
| **Severidad** | **ALTA** — la pausa es inservible con la tecla que todo el mundo usa |
| **Estado** | REPORTADO — pendiente de video |

**Problema.** Pulsar `ESC` durante la partida no pausa: la pantalla parpadea en
negro un fotograma y el juego sigue.

**Encontrado** por una persona jugando el nivel, no por una prueba.

**Causa.** `ESC` está asignada a **dos acciones a la vez**
(`src/engine/input/action_map.py:77-78`):

```python
Action.CANCEL: [pygame.K_ESCAPE, pygame.K_x],
Action.PAUSE:  [pygame.K_ESCAPE, pygame.K_p],
```

Y las dos se consumen en el mismo fotograma:

```
src/framework/scenes/stage_scene.py:817   PAUSE  -> abre la pausa
src/framework/scenes/stage_parts/pausa.py:125   CANCEL -> la cierra
```

La pausa se abre y se cierra sola. El parpadeo negro es el único fotograma en
que llegó a dibujarse.

**Vuelta encontrada.** `P` pausa correctamente: está sólo en `PAUSE`.

**Solución propuesta.** Quitar `K_ESCAPE` de `Action.CANCEL` —`X` ya cubre
cancelar— o hacer que el menú de pausa ignore `CANCEL` en el fotograma en que
se abrió.

---

### F-013 · Los ocho enemigos de suelo estaban enterrados *(mío — corregido)*

| | |
|---|---|
| **Tipo** | LEVEL DESIGN |
| **Severidad** | ALTA |
| **Estado** | **CORREGIDO** |

**Problema.** «Hay un bicho que sale por debajo del piso.» No era uno: eran los
ocho enemigos de suelo del nivel.

**Causa.** En Tiled un objeto rectángulo se ancla por su esquina **superior**
izquierda. Escribí la `y` de la cara del suelo creyendo que era donde se apoyan
los pies, así que un enemigo de 32 px en `y=544` con el suelo en 544 ocupaba de
544 a 576: entero bajo tierra.

**La convención buena**, medida en dos mapas del profesor:

```
stage_mecanicas  Walker_173  y=292  base=320  suelo=320   dif +0
stage0           Walker_206  y=452  base=480  suelo=480   dif +0
```

**Corrección.** Restar el alto a la `y` de los 8. Verificado: los 8 en `dif +0`.
Las aves no se tocan — vuelan, y su `y` es altura de vuelo a propósito.

---

### F-014 · Lianas colgando del cielo *(mío — corregido)*

| | |
|---|---|
| **Tipo** | ARTE |
| **Severidad** | MEDIA |
| **Estado** | **CORREGIDO** |

**Problema.** «Hay lianas en el cielo, no tiene nada de sentido eso.»
`FG_Overlay` llevaba más de 200 tiles de dosel y liana repartidos por las filas
0-6, que es cielo abierto. Fuera del túnel no hay nada de lo que colgar.

**Corrección, en dos intentos.** El primero borraba las filas de cielo «fuera
de las columnas del túnel», y funcionó hasta que le puse cima en ladera a la
roca (F-015): al bajar la cima, los tiles de esas mismas columnas se quedaron
sin nada encima y volvieron a colgar. **Una regla escrita en columnas no
sobrevive a un cambio de forma.**

La regla definitiva mira el terreno: un tile de dosel se queda sólo si hay
terreno en su columna a su altura o por encima. Verificado: **0 tiles de primer
plano colgando del cielo** en todo el mapa.

---

### F-015 · Almenas en el cielo y roca cortada en vertical *(mío — corregido)*

| | |
|---|---|
| **Tipo** | ARTE |
| **Severidad** | MEDIA |
| **Estado** | **CORREGIDO** |

**Problema.** «En el cielo hay como un fondo gris tipo roca flotando, eso está
muy raro.» Eran dos cosas distintas:

**(a) Una franja de almenas azules y moradas en el borde superior.** Al final
del nivel la mezcla día→atardecer llega a 1, así que `frente = R * 0 = 0` y la
costura difuminada cae en la **fila 0** — el borde de la pantalla. Un
difuminado de Bayer a 16 px por celda, visto como una tira aislada contra el
marco, no se lee como degradado sino como almenas de castillo.
*Corrección:* sin difuminado. La frontera es dura, pero `frente` cambia con la
columna, así que baja en diagonal y se lee como un frente de nubes.

**(b) La masa de roca del túnel arrancaba en la fila 0 con el borde izquierdo
en vertical perfecta.** Tenía un borde inferior irregular bonito, pero ninguna
cima: sky a un lado, roca a plena altura al otro, sin transición.
*Corrección:* la roca ahora tiene cima en ladera — cerca de las bocas arranca
varias filas más abajo y sólo llega al borde en el centro del túnel.

**Lo que NO se hizo, y por qué.** Bajar el techo a altura de túnel de verdad
costaba 3 puntos del calificador: `level_metrics.py` sólo excluye una caja del
recuento de plataformas si mide `alto >= 426 px` **y** `alto > ancho`, y el
techo es 752 × 368 — demasiado ancho, y el mapa sólo tiene 640 de alto, así que
no hay forma de que califique como muro. Con la cima en ladera el problema
visual se resuelve sin tocar la colisión y **sin perder los 3 puntos**.

---

### F-016 · El cartel «STAGE COMPLETE» nunca se ve: el final son 2,9 s en blanco

| | |
|---|---|
| **Tipo** | TECHNICAL (lógica de actualización) |
| **Severidad** | **ALTA** — el nivel no da ninguna señal de haberse completado |
| **Estado** | REPORTADO (motor) · **sorteado desde el escenario** |

> **Corrección de este informe.** En la primera versión archivé esto como «no
> es un defecto»: había medido que el temporizador de 2,9 s es deliberado y que
> el motor lanza el cartel, y di por hecho que se veía. Dejé escrito que
> faltaba confirmarlo jugando. **Se confirmó jugando, y no se ve.** Medir la
> mitad de la cadena y suponer el resto no es medir.

**Problema.** «Al llegar al final del stage dura unos cuantos segundos en
finalizar, está raro.» No es sólo raro: son **2,9 segundos sin ninguna señal en
pantalla**. El cartel de nivel completado no aparece nunca.

**Causa.** Al tocar la salida, el escenario hace dos cosas en el mismo
fotograma (`stage_scene.py:1188-1191`): pone `stage_complete = True` y lanza el
cartel. Pero el bloque que actualiza la interfaz está guardado por **esa misma
bandera** (`stage_scene.py:797`):

```python
if not self._game_over and not self._progression.stage_complete:
    self._update_audio(dt)
    self._update_hud_ui(dt)      # unico sitio que anima el cartel
    ...
    self._update_timers(dt)      # y el otro
```

Los dos únicos sitios que llaman a `ScreenBanner.update` quedan fuera justo
cuando hay que animar el cartel del final.

**Evidencia.** Con el jugador colocado en la salida:

```
  f      t       completo  timer  estado     offset
  0    0.00s     True      2.88   slide_in   1600.0
  90   1.50s     True      1.38   slide_in   1600.0
  180  3.00s     True     -0.02   slide_in   1600.0
```

Congelado en `slide_in` con desplazamiento 1600 los tres segundos.
`ScreenBanner.draw` pinta en `bx = offset - 800 = 800`: **una pantalla entera a
la derecha**. Se dibuja los 174 fotogramas y no se ve ni uno.

**El sistema de carteles está sano.** El del *nombre* del nivel funciona
perfecto, porque en el arranque la bandera es falsa:

```
  f      t       estado     offset   bx    en pantalla?
  0    0.00s     slide_in   1547.6   748   si
  50   0.83s     hold        800.0     0   si
  175  2.92s     slide_out  1600.0   800   si
```

**Y hay una pista de que es un descuido, no una decisión.** Dentro de
`_update_timers` hay un `if self._progression.stage_complete:` que es **código
inalcanzable**: sólo se llama cuando la bandera es falsa, y su cuerpo exige que
sea verdadera. Alguien escribió el manejo del final y la condición de fuera lo
dejó muerto. Las duraciones del cartel —0,5 + 2,0 + 0,4— suman exactamente los
2,9 s del temporizador: la espera existe **para** que el cartel se lea.

**Solución propuesta.** Sacar `_update_hud_ui` y `_update_timers` de la
condición, o cambiarla por `not self._game_over` a secas. La interfaz tiene que
seguir viva mientras el nivel se cierra.

**Vuelta aplicada.** `Stage1_1_LaEntrada._animar_cartel_final` llama al
`update` que el motor se salta. No toca el motor: vive en la carpeta del
escenario. Si algún día se corrige aguas arriba, la llamada se vuelve
inofensiva. Cubierta por
`src/stages/stage1_1/tests/test_cartel_final.py` — 3 pruebas, 2 de las cuales
fallan si se quita la llamada.

---

### F-017 · El mixer se abre en 7.1 y suena ruido blanco sobre la música

| | |
|---|---|
| **Tipo** | TECHNICAL (audio) |
| **Severidad** | **ALTA** — afecta a todo el juego, en cualquier máquina con tarjeta estéreo |
| **Estado** | REPORTADO — pendiente de video |

**Problema.** Jugando se oye la música **más un ruido blanco de fondo**.

**Encontrado** por una persona jugando, no por una prueba: ninguna prueba
escucha.

**Causa.** `src/engine/core/app.py:209`:

```python
pygame.mixer.init(frequency=44100, size=-16, channels=8, buffer=512)
```

En `pygame.mixer.init`, `channels` **no** son «canales de sonido» —esos se
piden con `pygame.mixer.set_num_channels()`—: son los canales de **salida del
dispositivo**. `8` pide 7.1 envolvente. En una tarjeta estéreo SDL tiene que
remezclar ocho canales a dos, y ese remapeo es lo que se oye como ruido.

**Y explica un segundo síntoma que ya arrastrábamos.** El driver por defecto de
Windows rechazaba el arranque, y por eso los lanzadores fuerzan
`SDL_AUDIODRIVER=directsound`. El driver tenía razón: se le estaba pidiendo un
formato que la tarjeta no puede dar. Forzar el driver hizo que arrancara, pero
el formato imposible seguía ahí — y de ahí el ruido.

**Vuelta encontrada.** `pygame.mixer.init()` no cambia el formato si el mixer ya
está abierto (para cambiarlo hay que llamar antes a `mixer.quit()`). Así que
basta con abrirlo primero en estéreo y la llamada del motor queda inofensiva:

```
tras pre_init estereo  : (44100, -16, 2)
tras el init del motor : (44100, -16, 2)   <- sigue en 2
```

Implementado en `herramientas/jugar.py`, que es lo que usan ahora los
lanzadores `.bat`. No toca el repositorio.

**Solución propuesta.** `channels=2` en `app.py:209`. Si de verdad se querían
más voces simultáneas, la llamada es `pygame.mixer.set_num_channels(8)`, que es
otra cosa y sí hace lo que el nombre sugiere.

---

### F-018 · Tajo vertical entre el cielo y el túnel *(mío — corregido)*

| | |
|---|---|
| **Tipo** | ARTE |
| **Severidad** | ALTA |
| **Estado** | **CORREGIDO** |

**Problema.** «La división del túnel con el cielo se ve muy falsa, un corte
todo irreal.» En la columna 124 el fondo pasaba de cielo abierto a una pared
verde oscura de golpe, sin transición.

**Causa — y me la hice yo al arreglar F-015.** `componer_fondo.py` buscaba el
suelo escaneando desde la fila 0:

```python
techo_suelo = [next((f for f in range(H) if terreno[f][c]), H) ...]
```

Mientras el único terreno alto fue el techo macizo del túnel, funcionó. Pero al
darle cima en ladera a la roca apareció una astilla de roca a media altura en
la columna 124, y ese `next()` la tomó por suelo: `techo_suelo[124] = 8`.

A partir de ahí se derrumba en cadena: `tope = techo_suelo - 2` deja los planos
de colina aplastados en la fila 6, y el relleno de bosque —que va desde `R2+1`
hasta abajo— pinta la columna entera de verde oscuro.

**Medido:** columna 123, primera fila con contenido = 28. Columna 124 = 8. Un
salto de **320 px en una sola columna**.

**Corrección.** Buscar el suelo por debajo de la fila 21. El suelo de este nivel
nunca sube de la fila 22 (`Floor_09` en y=352) y el techo nunca baja de la 19:
la franja entre las dos separa una cosa de otra sin ambigüedad.

**La lección, que es la misma de F-014.** Dos veces seguidas, un cambio de
forma rompió una regla que daba por supuesta la forma anterior. Cuando la
geometría es variable, las reglas tienen que leerla, no asumirla.

---

### F-019 · El rectángulo azul que se mueve solo *(no es un defecto: es el fantasma de tu mejor carrera)*

| | |
|---|---|
| **Tipo** | — |
| **Severidad** | — |
| **Estado** | **DESCARTADO — es una función del motor, funcionando bien** |

> **Este hallazgo me costó cuatro conclusiones equivocadas seguidas**, y queda
> escrito con todas ellas porque el error tiene más valor didáctico que el
> resultado. Lo que lo resolvió no fue una medición nueva: fue que quien jugaba
> lo describiera bien. Dijo *«se mueve solo, yo no lo controlo; es como un
> shadow de mi anterior vida»*. Es exactamente eso, y con esa frase el módulo
> aparece a la primera búsqueda.

**Qué es.** `src/framework/scenes/stage_parts/fantasma.py` (AUD-142) — «El
fantasma de tu mejor carrera». El motor graba tus recorridos y reproduce la
silueta del más rápido para que compitas contra vos mismo.

```python
_COLOR_FANTASMA = (140, 210, 255)
silueta = pygame.Surface((ancho, alto), pygame.SRCALPHA)
silueta.fill((*self._COLOR_FANTASMA, 90))
surface.blit(silueta, (int(x - offset.x), int(y - offset.y)))
```

Encaja en todo:

- **Rectángulo** del tamaño exacto del jugador (`ancho`/`alto` salen de
  `self._player.rect`): 20 × 32 px.
- **Azul claro translúcido** — alfa 90 de 255.
- **Se mueve solo** porque su posición sale de
  `previo.posicion_en(self._speedrun.global_time)`: reproduce dónde estabas en
  tu mejor carrera.
- **Sin sprite a propósito.** Lo dice su propio comentario: «un fantasma opaco
  con la animación del jugador se confunde con el jugador, y en un salto
  difícil eso es peor que no tenerlo».
- **Aparece tras morir** porque al reaparecer se recarga la escena y
  `_preparar_fantasma()` vuelve a leer la carrera guardada.

**Prueba dura.** El fichero existe en esta máquina:

```
C:\Users\andre\AppData\Roaming\legacyofinfest\saves\fantasmas\
    stage0.json      16.529 bytes
    stage1_1.json    58.443 bytes
```

Esos 58 KB son la grabación de la mejor carrera de este nivel.

**Las cuatro conclusiones equivocadas, y por qué fallaron:**

1. *Un punto de control.* `Checkpoint.draw` sólo pinta un degradado radial.
2. *La textura de normal plana del camino de GPU.* El color encajaba, pero el
   cuadro seguía saliendo con GPU activo.
3. *Un tile de cielo suelto.* Se reprodujo el bug sobre una copia del mapa: los
   47 tiles azules de más están en la fila 1, tapados por la roca.
4. *El rectángulo de respaldo del jugador* (`player.py:988`, `(0,120,255)` con
   borde blanco). La más cercana, y aun así falsa: ese respaldo se dibuja donde
   está **tu** personaje, y quien jugaba dijo que el cuadro se movía solo. El
   color tampoco es el mismo — el respaldo es opaco con borde; el fantasma es
   translúcido y sin borde.

**La lección.** Las cuatro veces intenté deducir la causa desde el código hacia
el síntoma. La quinta partió del síntoma **bien descrito** y llegó en un paso.
Cuando alguien que juega dice algo raro, la descripción exacta vale más que
otra ronda de mediciones — y «no lo controlo» era el dato que descartaba de un
plumazo las cuatro hipótesis anteriores.

**Para el video:** enseñarlo. Es una función del motor que casi nadie descubre,
y explicar qué es demuestra que se investigó en serio.

**Pero el hecho de que nadie lo entienda es un defecto aparte** — va como
F-022.

---

### F-022 · El fantasma de la mejor carrera es un rectángulo liso: nadie entiende qué es

| | |
|---|---|
| **Tipo** | UX |
| **Severidad** | MEDIA |
| **Estado** | REPORTADO — es del motor |

**Problema.** La función de F-019 está bien programada, pero **es ilegible**.
En pantalla sólo se ve *un rectángulo celeste que se mueve solo*. No tiene
forma, ni contorno, ni rótulo, ni nada que diga que es una silueta de una
carrera anterior.

**La evidencia es la propia investigación.** Quien jugaba lo reportó **dos
veces como defecto** —«hay un cuadro azul dando vueltas por el mapa, eso no
debería estar»— y siguió sin convencerse después de la primera explicación. Y a
mí me costó **cuatro hipótesis equivocadas**. Si ni quien juega ni quien tiene
el código delante lo reconocen, la función no se está comunicando.

**Causa.** `fantasma.py:86-88` pinta un rectángulo relleno del tamaño del
`rect` del jugador:

```python
silueta = pygame.Surface((ancho, alto), pygame.SRCALPHA)
silueta.fill((*self._COLOR_FANTASMA, 90))
```

La variable se llama `silueta`, pero no lo es: es un `fill` de la caja entera.
El comentario justifica no usar el sprite —«un fantasma opaco con la animación
del jugador se confunde con el jugador»— y el razonamiento es bueno; el
problema es la conclusión. Entre «copia opaca del jugador» y «caja de color»
hay un punto medio que es lo que hace todo el mundo: **la silueta de verdad**,
o sea la máscara alfa del sprite, teñida y translúcida. Se distingue del
jugador y a la vez se reconoce como una figura.

**Solución propuesta.** Dos, y la primera sola ya bastaría:

1. Usar la máscara del sprite actual del jugador en vez de `fill` sobre la caja.
   `pygame.mask.from_surface(frame).to_surface(...)` da la silueta hecha.
2. La primera vez que aparece en una partida, un rótulo de dos segundos:
   «fantasma de tu mejor carrera». El motor ya tiene `ScreenBanner` y
   `_subtitles` para eso.

**Nota de alcance.** Esto no es del escenario: afecta a los 15 niveles del
curso, y a cualquier estudiante que muera dos veces y crea que rompió el juego.

---

### F-020 · El deslizamiento siempre empuja a la DERECHA

| | |
|---|---|
| **Tipo** | TECHNICAL (movimiento) |
| **Severidad** | **ALTA** — corriendo a la izquierda, el jugador sale disparado hacia atrás |
| **Estado** | REPORTADO — es del motor |

**Cómo apareció.** Grabando: «al moverme con la tecla D y presionar S, como que
hay un boost». El impulso es real y es una mecánica: agacharse en movimiento
entra en `SlideState`, que corre a **300 px/s** frente a los 90 de andar —
3,3 veces más rápido, durante 0,4 s. Eso está bien.

Lo que está mal es la dirección. `states/grounded.py:252`:

```python
self._slide_dir = 1.0 if abs(player.velocity.x) > 0 else float(player.facing_direction)
```

Si el jugador **se está moviendo**, la dirección es siempre `1.0`, o sea
derecha, sin mirar hacia dónde va. Sólo se consulta `facing_direction` cuando
está quieto — justo el caso en que da igual.

**Evidencia medida** (terreno llano, 30 fotogramas de carrera y luego agacharse
sin soltar la dirección):

```
corriendo a la DERECHA  + S   velocidad antes  +99 px/s   avanza  +80 px  -> derecha
corriendo a la IZQUIERDA + S   velocidad antes  -99 px/s   avanza +125 px  -> DERECHA
```

Corriendo hacia la izquierda, el deslizamiento lo lanza 125 px hacia la
derecha: al revés de donde iba, y más lejos que en el caso correcto.

**Solución propuesta.** Tomar el signo de la velocidad:

```python
self._slide_dir = (math.copysign(1.0, player.velocity.x)
                   if player.velocity.x else float(player.facing_direction))
```

---

### F-021 · El deslizamiento no tiene ninguna señal visual

| | |
|---|---|
| **Tipo** | UX |
| **Severidad** | MEDIA |
| **Estado** | REPORTADO — es del motor |

**Problema.** Dicho por quien grababa: «es como un boost sin mostrar colores ni
nada, solo avanza rápido», y lo comparó con el dash, que **sí** tiene su color
azul característico.

Una mecánica que triplica la velocidad durante 0,4 s y no se anuncia con nada
no se lee como mecánica: se lee como un fallo. Quien la descubre sin querer
—que es lo que pasó— cree que el juego se rompió.

`SLIDE` tiene entrada propia en la tabla de sprites (`player.py:93`,
`player_crouch.png` con 4 fotogramas) y su propia velocidad de animación
(`player.py:136`), así que el estado está reconocido. Lo que falta es que se
distinga de agacharse quieto.

**Solución propuesta.** Darle al deslizamiento el mismo tratamiento que al
dash: estela, tinte o partículas de polvo. Con el polvo bastaría, y encaja con
un sendero de tierra.

**Problema.** Durante la partida aparece un rectángulo azul claro, de unos
16 × 32 px, que **se desplaza como si fuera un bicho**.

**Encontrado** por una persona jugando. Y no aparecía antes de que los ocho
enemigos de suelo se desenterraran (F-013): mientras estaban bajo tierra no se
veían, y al subirlos a su sitio empezaron a dibujarse.

**Por qué costó tanto localizarlo.** No se reproduce en ninguna captura
automática. Se barrió el nivel entero —17 posiciones, buscando manchas azules
compactas por debajo del horizonte— y salieron **cero**. También se muestreó el
color medio de las 11 entidades de la escena, una por una: ninguna azul. Y
ninguno de los siete sprites de enemigo de la zona 1 es azul.

La diferencia está en el **camino de dibujo**. Las capturas automáticas corren
sin pantalla, o sea **por software**; el juego real corre por **OpenGL**. Y en
el camino de GPU, y sólo ahí, existe esto
(`src/engine/render/gpu_sprite_batch.py:118-119`):

```python
plano = pygame.Surface((1, 1), pygame.SRCALPHA)
plano.fill((128, 128, 255))
```

Es la textura de respaldo del sampler de normales — `(128,128,255)` es la
codificación estándar de una normal plana `(0,0,1)`, y se ata a la unidad de
textura 1. Si una entidad acaba dibujándose con **esa** textura en vez de con
su sprite, se ve un rectángulo azul sólido del tamaño del sprite, moviéndose
con el bicho. Es exactamente lo observado, y explica por qué el color no está
en ningún sprite ni en ningún tile del mapa.

**Cómo confirmarlo en 10 segundos.** El lanzador
`herramientas/jugar.py` admite `--sin-gpu`, que desactiva OpenGL:

```bash
python herramientas/jugar.py --stage stage1_1 --sin-gpu
```

Si el rectángulo azul desaparece, queda probado que es el camino de GPU.

**Honestidad sobre el alcance.** Esto es una hipótesis con evidencia fuerte —
el color coincide exacto, el camino coincide, y descarta todo lo demás— pero
**no está medida directamente**, porque este entorno no tiene contexto OpenGL.
Falta la confirmación con `--sin-gpu` o una captura de la partida real.

**Nota sobre `App.use_gl`.** `App.__init__` acepta `use_gl`, pero `main.py`
nunca se lo pasa: no hay forma de pedir software desde la línea de órdenes. Eso
es lo que obliga a parchear la clase desde fuera para poder diagnosticar. Un
`--sin-gpu` en `main.py` sería útil por sí solo.

---

### F-023 · Se podía salir del mapa trepando el muro izquierdo *(mío — corregido)*

| | |
|---|---|
| **Tipo** | LEVEL DESIGN |
| **Severidad** | **ALTA** — se rompe la partida |
| **Estado** | **CORREGIDO** |

**Problema.** Dicho por quien jugaba: «si pude salirme del mapa, dándole al
espacio muchas veces pegado a la pared de la izquierda del principio del stage,
hasta que subí todo lo que pude y me salí del mapa».

**Causa.** El motor tiene **salto de pared** (`PlayerState.WALL_SLIDE`). Los
muros laterales de mi mapa van de `y=0` a `y=640` —toda la altura— así que dan
superficie para trepar hasta el borde. Y el mapa **no tiene techo**.

**Evidencia medida** (machacando salto contra el muro izquierdo):

```
ciclo  0    y =  478.7
ciclo  8    y =  229.6
ciclo 16    y =  -18.6      <- ya fuera del mapa
ciclo 17    y =  -49.6      FUERA
```

**Y mi verificador no lo detectaba.** `verificar_recorrido.py` daba por «fuera
del mapa» un `y < -64`, puesto a ojo. El jugador llegaba a **−49,6**: fuera de
verdad, pero 14 px por encima de mi umbral, así que la comprobación decía
«nunca salió del mapa». Un margen inventado convirtió una fuga real en un OK.
Corregido a `y < 0`, que es donde está el borde.

**Corrección.** Un techo de 3840 × 16 en `y=0` costaba **seis puntos**
(130 → 124): el analizador lo cuenta como plataforma aislada y encima le sale
un repecho imposible. Lo medí antes de descartarlo.

Lo que sí funciona: `level_metrics.py:641` excluye del recuento de plataformas
todo objeto con `alto >= 426` **y** `alto > ancho` — son los muros de cierre.
Un **tapón vertical de 16 × 432** pegado a la cara interior de cada muro cumple
las dos condiciones, así que no cuenta como plataforma, y ocupa justo el aire
por el que se trepaba.

**Resultado medido:** el jugador topa en `y = 432` en vez de salirse, y el
calificador sigue en **130/130** con `design_geometry: 10/10`.

Los tapones acaban en `y=432` y el suelo de arranque está en `y=544`, así que
no estorban a quien camina: sólo existen en la franja alta, donde no hay nada
que hacer.

**Nota sobre el proceso.** Durante esta corrección llegué a revertir los
tapones creyendo que provocaban un `pygame.error: Out of memory`. No era así:
el error venía del entorno de pruebas, que llevaba decenas de procesos
acumulados, y aparecía igual con el mapa sin tapones. Se repuso el arreglo tras
comprobarlo. Queda anotado porque es el mismo error de método que el del bot
(F-010): culpar al cambio antes de descartar el instrumento.

---

### F-007 · La ficha del nivel exige propiedades que ninguna herramienta comprueba

| | |
|---|---|
| **Tipo** | LEVEL DESIGN (documentación) |
| **Severidad** | BAJA |
| **Estado** | REPORTADO |

**Problema.** `docs/niveles/01_STAGE_1_1.md` marca como **obligatorio**
`start_hour = "morning"` y `day_length = 900`. El mapa entregado no las lleva,
`grade_stage.py` da **10/10 en metadatos** igualmente y `validate_tmx.py` no
dice nada.

**Impacto.** Una exigencia escrita que nada verifica acaba ignorada. O la
comprueba el validador, o deja de ser obligatoria.

---

## Bloque B — Del escenario · **mío, pero pendiente de video**

### ~~F-008 · El bot se atasca 74 fotogramas justo en el tramo de parkour~~ *(Resuelto)*

| | |
|---|---|
| **Tipo** | LEVEL DESIGN |
| **Severidad** | — |
| **Estado** | **RESUELTO — no era un defecto del nivel, era el instrumento** |

**Problema.** En el recorrido automático, el bot registraba **74 fotogramas sin
avanzar** alrededor de `x ≈ 848 px`, y al recorrer el nivel entero se quedaba
clavado del todo en `x = 1773` sin pasar del 45 %.

**Resolution:** No hay defecto de nivel. El bot de referencia
`walk_right_bot` mantiene `JUMP` **dos fotogramas**, y el salto de este motor
es de **altura variable**: soltar el botón corta el impulso. El bot se eleva
53 px de los 96 que da el salto entero, así que no puede subir escalones que
una persona sube sin pensar. Los detalles y la medida están en **F-010**.

Con un bot que mantiene el salto 12 fotogramas —lo que hace cualquiera— el
nivel **se completa: 99 % del recorrido, sin atascos, 0 muertes, 140 s**.

```
python herramientas/verificar_recorrido.py . --recorrido --bot humano
```

**Lo que costó llegar aquí, porque la lección vale.** La primera hipótesis fue
que la plataforma `Plat_02` colgaba sobre la subida y le pegaba en la cabeza al
jugador. Se acortó y **el número no se movió**: seguía en 1/49. Se revirtió el
cambio — y menos mal, porque al mirarla bien esa plataforma sobrepasa la
hondonada 32 px y *es el puente para cruzarla por arriba*: acortarla borraba
una ruta y hacía el nivel más difícil.

La causa sólo apareció trazando el salto fotograma a fotograma
(`herramientas/trazar_salto.py`):

```
dy:  -6,1  -5,9  -5,7     subiendo a plena fuerza
     -2,6  -2,4  -2,2     cortado de golpe en el fotograma 4
```

---

### F-009 · El bot muere contra el segundo caminante

| | |
|---|---|
| **Tipo** | GAMEPLAY |
| **Severidad** | BAJA |
| **Estado** | ABIERTO — probablemente no es defecto |

**Problema.** A los 33 s, en `x ≈ 1059 px`, el bot muere. Ahí está
`WalkerInsect_02` (columna 62).

**Matiz.** El bot no esquiva ni ataca: camina en línea recta hacia el enemigo.
Morir es lo esperado. Se anota por completitud del registro.

---

## Lo que falta para cerrar este reporte

1. **Grabar el video de la sesión humana.** Es la evidencia que exige el
   entregable.
2. Anotar los defectos que aparezcan jugando y que el bot no puede ver:
   ritmo, legibilidad, si algo se entiende mal, si algún tramo aburre.
3. **Confirmar con dedos humanos que los escalones se suben cómodos.** El bot
   arreglado los sube, pero el bot no se frustra. Los sitios a mirar son la
   hondonada del medio (`x ≈ 1792`) y el escalón de `x = 768`.
4. Comprobar si se tocan los 7 puntos de control andando. El bot activó 5 de 7
   porque iba saltando y les pasó por encima.

---

## Cómo se reproduce lo de aquí

```bash
python herramientas/verificar_recorrido.py . --recorrido --bot humano
python herramientas/verificar_recorrido.py . --recorrido --bot profesor
python herramientas/trazar_salto.py .
python herramientas/probar_escalon.py .
python herramientas/jugar_y_capturar.py . --segundos 36
python -m tests.playtest.jump_bench
python scripts/grade_stage.py assets/maps/stage1_1/stage1_1.tmx
```

**Aviso sobre `probar_escalon.py`.** Es la herramienta menos fiable de las
cuatro: se le corrigieron cuatro errores de medición (el flanco del salto, el
criterio de éxito, la altura variable, y mirar el fotograma final en vez de la
trayectoria) y su modo «con carrerilla» sigue devolviendo 0 y no se ha
depurado. Sus números valen para comparar estilos de salto entre sí, **no**
como veredicto absoluto. El veredicto lo da `verificar_recorrido.py`, que
recorre el nivel de verdad.
