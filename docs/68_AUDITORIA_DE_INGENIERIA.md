# 68 — Auditoría de ingeniería (AUD-154 a AUD-160)

Revisión por categorías —arquitectura, seguridad, memoria, rendimiento,
física, render, UI/UX, localización, activos, build y pruebas— sobre las
~62.000 líneas de `src/`, `scripts/` y `tools/`.

Todo lo que hay aquí está **reproducido ejecutándolo** antes de tocar nada, y
cada arreglo tiene una prueba que se comprobó en rojo sin él. Lo que no se
pudo reproducir está dicho como tal.

---

## Resumen

| # | Defecto | Categoría | Cómo se veía |
|---|---|---|---|
| AUD-154 | Ningún control de la pantalla de opciones funcionaba | UI/UX | Nada se guardaba; la pantalla de teclas, inalcanzable |
| AUD-154 | 2 de los 8 mandos de dificultad no llegaban al juego | Gameplay | Se jugaba con «normal» eligiera lo que eligiera |
| AUD-154 | El bestiario no registraba nada | Gameplay | Pantalla vacía siempre |
| AUD-155 | 4 de 5 nodos del mapa del mundo apuntaban a mapas inexistentes | UI/UX | Pulsar Enter no hacía nada ni avisaba |
| AUD-156 | Cargar una partida devolvía al principio del nivel | Gameplay | En los quince escenarios |
| AUD-156 | Dos identidades por escenario, sin coincidir | Arquitectura | Dos niveles imposibles de completar |
| AUD-157 | El estado del jugador se escribía en el árbol de instalación | Seguridad / Build | El ejecutable no puede guardar en Program Files |
| AUD-157 | Cinco lecturas de preferencias con captura muda | Clean Code | Un renombrado apagaría la opción en silencio |
| AUD-157 | `__init__` duplicado en `lobby_datacenter` | Clean Code | Inocuo hoy, ilegible mañana |
| AUD-158 | Los números de daño compartían superficie y alfa | Render / Memoria | Se desvanecían todos a la vez |
| AUD-159 | Siete `.ogg` que eran WAV | Activos | Cuatro escenarios sin música |
| AUD-160 | La escala de texto no llegaba a la pantalla de opciones | Accesibilidad | Y al forzarla, la maqueta se salía |

---

## 1. Lo que se buscó y **no** apareció

Decirlo importa tanto como lo encontrado: la ausencia de hallazgo también es
un resultado, y sin escribirla el siguiente que audite repetirá el trabajo.

* **Ejecución de código arbitrario.** Ni `eval`, ni `exec`, ni `pickle`, ni
  `shell=True`, ni `os.system` en todo el árbol. El único `__import__` es el
  del validador de TMX, sobre un nombre de módulo derivado del nombre de una
  carpeta del propio repositorio.
* **Partidas hostiles.** JSON roto, lista en vez de objeto, fichero vacío,
  campos con el tipo cambiado y listas anidadas: los cinco casos devuelven
  `None` con un aviso, ninguno lanza.
* **Argumentos por defecto mutables.** Cero en `src/`, `scripts/` y `tools/`.
* **Tunneling.** El jugador mide 32 px de alto y el paso máximo por fotograma
  es de 25 px —500 px/s de caída con el `dt` recortado a 0,05 s— así que la
  comprobación barrida no puede saltarse una baldosa. Medido contra suelos de
  16, 8 y **4** px a 60, 30 y 20 fps: aterriza en los nueve casos. Los
  proyectiles van a 90–150 px/s, 7,5 px por fotograma en el peor caso.
* **Cachés sin tope.** Los dieciséis que hay están acotados o son de instancia
  y mueren con la escena. El del TMX guarda **un** mapa: vacía y vuelve a
  poner. La única excepción era el de los números de daño (AUD-158).
* **Ficheros sin cerrar.** Las once llamadas a `open()` van con `with`, salvo
  la de `save_manager`, que usa `os.fdopen` sobre un descriptor de
  `mkstemp` y lo cierra en su `finally`.
* **Catálogos de traducción.** En orden; las cadenas sin entrada son las que
  ya están en el idioma de origen.
* **Presupuesto de fotograma.** Las cinco pruebas de rendimiento en verde.

---

## 2. Los defectos, uno a uno

### AUD-157 — El estado del jugador vivía dentro de la instalación

`user_data_dir()` existe desde AUD-032 y su propio docstring dice por qué:

> *una versión empaquetada puede estar instalada en un sitio de sólo lectura
> (Program Files, /Applications), y escribir el estado del jugador dentro del
> árbol de instalación es lo que metió `saves/slot_1.json` en el control de
> versiones.*

Esa corrección se aplicó a las preferencias y a los logros. **No** a las
partidas, ni al bestiario, ni al speedrun, ni al progreso académico: los
cuatro seguían en `PROJECT_ROOT / "saves"`. Con el ejecutable de PyInstaller
(F3.3) instalado en Program Files, guardar la partida falla.

El proyecto había escrito por qué eso estaba mal y siguió haciéndolo. Los
cuatro pasan al directorio del usuario, y `SaveManager` copia una vez lo que
haya en el sitio viejo —sin borrarlo, por si alguien vuelve a una versión
anterior—.

### AUD-157 — Cinco lecturas de preferencias que se tragaban cualquier error

Entrada, tema, cámara y dos del diálogo hacían
`try: user_settings.get().<campo> except Exception: return <defecto>`.

La intención era buena. El problema es qué puede fallar ahí: `get()` **no
lanza** —`UserSettings.load()` atrapa el fichero que falta, el JSON roto y los
valores inválidos—. Lo único que puede saltar es un `AttributeError` por un
campo renombrado, o sea un error del programador, y esos cinco bloques lo
convertían en «la opción deja de funcionar, en silencio, para todo el mundo».
Es la misma forma de fallo que dejó el sistema de diálogo inalcanzable durante
meses (AUD-127).

Ahora hay un `user_settings.preferencia(nombre, defecto)` que conserva la red
y le pone una alarma: un aviso por nombre, no uno por fotograma.

### AUD-158 — Los números de daño se desvanecían en bloque

La superficie del texto se cachea por `(texto, crítico)` y se comparte entre
todos los números iguales en pantalla. Sobre esa superficie compartida se
llamaba a `set_alpha()` en cada `draw`.

El alfa es estado de la superficie, no del blit, así que el último en dibujarse
imponía su transparencia a los demás: cuatro golpes de «5» seguidos se apagaban
de golpe. Medido: dibujar un número al 10 % de vida dejaba el alfa del otro,
recién creado, en 25 de 255.

No se dejó de cachear —renderizar texto por fotograma es caro—: se dejó de
**escribir** en lo cacheado. El alfa va sobre una copia del `SurfacePool`,
como el resto de los efectos.

### AUD-159 — Siete `.ogg` que eran WAV

`assets/music/` tenía siete ficheros con extensión `.ogg` y cabecera `RIFF`.
SDL se fía de la extensión, así que `pygame.mixer.music.load` los rechazaba con
«Not an Ogg Vorbis audio stream» y el escenario se jugaba **en silencio**:
`StageScene` sólo registra un aviso y sigue.

Costó verlo porque el motor prefiere `.wav` y sólo cae al `.ogg` si no hay
`.wav`. De los siete, cuatro no tenían gemelo —`bgm_boss`, `bgm_zone1`,
`bgm_zone2`, `bgm_zone3`— y ésos eran los mudos. Renombrados a `.wav`, que es
lo que son: 60 s, 44,1 kHz, estéreo.

Los otros tres —`bgm_splash`, `bgm_stage0`, `bgm_title`— tienen al lado un
`.wav` de 8 a 12 segundos que el generador de assets produce como marcador de
posición. **No se han tocado**: cambiarlos es una decisión de contenido, no de
ingeniería, y significaría sustituir el marcador por una pista de 60 s. Queda
señalado por el validador para que se decida:

    [AUDIO EXTENSION LIES] assets/music/bgm_stage0.ogg: la extensión dice
    «.ogg» y el contenido es .wav. SDL se fía de la extensión, así que este
    fichero NO se puede reproducir.

El validador antes pasaba en verde porque sólo miraba `REQUIRED_SOUNDS`, y los
cuatro mudos no estaban en esa lista. Ahora recorre todo el árbol de activos.

### AUD-160 — La escala de texto no llegaba a la pantalla de opciones

`text_scale` la aplica `engine.ui.theme.escalar_texto`, que usan el kit de
interfaz y el diálogo. La pantalla de opciones no usa ninguno de los dos: la
dibuja `pygame_gui`, con su propio tema. Así que elegir «2.0x» agrandaba el
texto de todo el juego **menos el de la pantalla donde se elige** — justo donde
lo necesita quien no puede leer el texto pequeño.

Dos detalles que costaron:

1. Un bloque `defaults` en el tema de pygame_gui **no** llega a los elementos.
   Con `defaults` el botón seguía midiendo 37 × 20 px; nombrando `button`,
   `label`, `drop_down_menu` y `horizontal_slider` pasó a 72 × 39.
2. Al aplicarla, la maqueta se rompía: estaba toda en píxeles literales
   —`Rect((200, y), (320, 28))`— escritos para 1×. A 2× pygame_gui avisaba de
   once etiquetas recortadas y las últimas filas caían fuera de la pantalla.

La pantalla mide 800 × 600 y no se puede estirar, así que la maqueta ya no
escala todo por igual: la tipografía y el alto de fila siguen al jugador, el
ancho se reparte sobre el disponible, y el paso vertical sale de dividir el
alto entre las filas que hay —de modo que añadir una opción no vuelve a tirar
la última fuera—. Comprobado a 1×, 1,25×, 1,5× y 2×: sin avisos y sin
desbordes.

---

## 3. Lo que queda abierto, y por qué

| Asunto | Por qué no se tocó |
|---|---|
| Tres `.ogg` mal etiquetados con gemelo `.wav` | Sustituir el marcador de posición por la pista de 60 s es una decisión de contenido |
| `src/stages/` fuera de ruff en CI | Deliberado: es código de estudiantes y se revisa al calificar |
| Alcance de mypy en dos paquetes | Trinquete a propósito (AUD-124); ampliarlo es trabajo aparte |
| Post-procesado en GPU | Medido 5× más lento sin tarjeta (AUD-148) |
| Reverberación por zona | No se puede sobre el mezclador de SDL |
