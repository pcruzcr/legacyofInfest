---
document_id: "LOI-GPU-74"
title: "La tubería de GPU: qué hace, qué cuesta y cómo se enciende"
tags: ["render", "gpu", "moderngl", "shaders", "rendimiento", "vfx"]
source: "docs/74_TUBERIA_DE_GPU.md"
date_processed: "2026-08-03"
---

# La tubería de GPU

**Documento único de referencia del renderizado y su rendimiento.** Recoge lo que hace
cada pasada, el reparto entre CPU y tarjeta, lo que cuesta cada cosa medido en
hardware, y cómo un escenario enciende un efecto.

Todos los números de este documento se midieron en la máquina de auditoría —
**Intel HD Graphics 530, OpenGL 4.6, 800×600, Python 3.14, pygame-ce 2.5.7**—
con contexto OpenGL real. Ninguno viene de `SDL_VIDEODRIVER=dummy`, que no da
GPU y donde cualquier medida de tarjeta es ficción (es el error que documenta
`src/engine/render/gpu_present.py`, y que dejó cinco meses de conclusiones
falsas en el registro).

---

## 1. El punto de partida: no hacía nada

Antes de agosto de 2026 la tubería estaba escrita, probada y **no ejecutaba
ningún efecto**. `_create_quad` construía un solo `VertexArray` atado al
programa de copia:

```python
self._quad_vao = ctx.vertex_array(self._passthrough_prog, ...)
```

y `_run_shader_pass(program, ...)` fijaba los uniformes del programa correcto
para después dibujar ese VAO. En moderngl **el programa vive dentro del
VertexArray**: es el que se ejecuta, y el argumento `program` no influía en
nada. Ocho pasadas, un único sombreador ejecutado, y era el que copia.

Medido: encendiendo bloom, iluminación, viñeta, aberración cromática,
refracción o rayos, la imagen final salía **byte a byte idéntica** a no
encender ninguno. Diferencia media 0,000, pico 0.

No se notó porque los mismos efectos existen por CPU en
`framework/vfx/post_processing.py` y ésos sí se dibujaban. La pantalla se veía
bien; lo que la tarjeta aportaba era exactamente nada, cobrando una pasada de
pantalla completa por efecto.

Está arreglado (AUD-223, un VAO por programa) y sujeto por
`tests/test_cada_pasada_ejecuta_su_shader.py`, que comprueba la causa —cada
pasada dibuja con el VAO de su propio programa— y no el síntoma, porque el
síntoma necesita GPU y en CI no la hay.

---

## 2. La cadena, en orden

`GLRenderer.render()` encadena pasadas sobre dos FBOs que se intercambian. El
orden no es arbitrario y cada posición está razonada en el código:

| # | Pasada | Cuándo corre | Por qué ahí |
|---|---|---|---|
| 1 | **Subida** (`upload_frag`) | siempre | Coloca la escena: voltea, ordena canales y fuerza el alfa |
| 1.5 | **Refracción** | si hay región de agua | Deforma la escena *antes* de post-procesarla |
| 2a | **Bloom: extracción** | si `bloom_active()` | A media resolución, en `_bloom_fbo` |
| 2b | **Bloom: composición** | ídem | Suma el halo, que vuelve a tamaño completo por filtrado bilineal |
| 3 | **Subida del mapa de luz** | si hay luz o rayos | Una sola vez, compartida por las dos pasadas siguientes |
| 3a | **Iluminación** | si `lighting_enabled` | Multiplicativa |
| 3b | **Rayos volumétricos** | si `godray_enabled` | *Después* de la luz: lo que se sume antes queda aniquilado justo en la sombra, que es donde un rayo tiene que verse |
| 4 | **Corrección de color** | si `color_grading_enabled` | — |
| 5 | **Aberración cromática** | si `strength > 0` | Después del bloom (el halo se separa en canales) y antes de la viñeta (la aberración es máxima en los bordes) |
| 6 | **Viñeta** | si `vignette_enabled` | Apagada por defecto, ver §3 |
| 7 | **Daltonismo** | si `colorblind_mode > 0` | Escrito y **nunca ejecutado**, ver §6 |
| 8 | **Desenfoque de movimiento** | si `motion_blur_enabled` | Acumula el fotograma ya compuesto |
| 9 | **Volcado a pantalla** | siempre | — |

---

## 3. El reparto entre CPU y GPU

Hay **dos** tuberías de post-procesado escritas por separado, y `App` arranca
con `use_gl=True`. Antes de AUD-222, `StageScene.draw` llamaba a
`PostProcessing.apply()` sin mirar si había GL: la viñeta se dibujaba dos veces
y el bloom se calculaba por CPU para que el sombreador lo repitiera.

El reparto vive en `src/engine/core/gpu_effects.py` y lo fija **la raíz de
composición**, que es la única que sabe si el contexto GL se creó de verdad.
`PostProcessing` está en `framework/` y no puede preguntar por `App` ni
importar `moderngl` sin romper las reglas de capas que vigila
`tests/test_layering.py`.

| Efecto | Quién lo hace con GL | Por qué |
|---|---|---|
| **Bloom** | GPU | 1,70 ms en tarjeta frente a 2,26 ms en CPU, con el mismo aspecto |
| **Agua** | GPU | No son el mismo efecto: la CPU superpone ondas, el sombreador refracta. Se sustituye, no se suma |
| **Viñeta** | CPU | La de CPU **crece cuando al jugador le queda poca vida**; la configuración de GL es estática y no puede enterarse |
| **Destello y tinte** | CPU | No tienen sombreador equivalente |
| **Corrección de color** | CPU | El sombreador multiplica por una matriz fija de la configuración; la de CPU la pone cada escenario. No son el mismo efecto |
| **Desenfoque de movimiento** | CPU | El sombreador mezcla con el fotograma anterior de forma incondicional; el de CPU lo enciende el juego |
| **Daltonismo** | CPU | Ver §6 |

Ampliar `gpu_effects.DELEGABLES` exige comprobar que la pasada de GL hace *lo
mismo* que la de CPU —o que la sustituye a conciencia, como el agua—, no algo
parecido por accidente.

---

## 4. Lo que cuesta, medido

> **Aviso de 2026-08-06 (AUD-301): los números de esta sección son de la Intel.**
> Este equipo tiene **dos** tarjetas —una Intel HD 530 integrada y una Quadro
> M2200— y ni SDL ni ModernGL eligen la dedicada por su cuenta: hay que dar de
> alta `python.exe` como «alto rendimiento» en Windows o en el panel de NVIDIA.
> Hecho eso y vuelto a medir, **el camino GL completo pasa de 3,76 ms a
> 1,46 ms**, 2,6×. Todo lo que sigue vale como cota superior; en la dedicada
> sobra fotograma.
>
> Lo que **no** cambia es el veredicto de `PresentadorGPU` (AUD-148): el camino
> de `pygame._sdl2` sigue saliendo peor. Lo que sí cambia es la explicación que
> se daba —«SDL cae a software»—, que AUD-301 comprobó falsa: sus seis drivers
> de render salen como acelerados. Lo caro es subir el fotograma entero a una
> textura nueva en cada pasada, y eso no lo arregla una tarjeta mejor.


Con la configuración real del juego (bloom e iluminación encendidos, el resto
apagado):

```
subir el fotograma y presentarlo        1,19 ms
iluminación                             0,62 ms
bloom (extracción + composición)        1,70 ms
                                       ────────
total del camino GL                     3,76 ms   de 16,67 disponibles
```

Y lo que cuesta **cada pasada por separado**, encendiéndolas de una en una
sobre una escena sin efectos (1,40 ms de base):

| Pasada | Coste |
|---|---|
| Desenfoque de movimiento (antes de AUD-236) | 5,45 ms |
| Rayos volumétricos (32 muestras/píxel) | 0,77 ms |
| Viñeta | 0,13 ms |
| **Desenfoque de movimiento (después)** | **0,12 ms** |
| Daltonismo | 0,07 ms |
| Corrección de color | 0,05 ms |

Esa tabla corrigió una suposición: los rayos *parecían* la pasada cara por
tener 32 muestras por píxel, y no lo eran ni de lejos. Lo caro era el
desenfoque de movimiento, y no por calcular nada —su sombreador mezcla dos
texturas— sino por **cómo guardaba el fotograma para el siguiente**:

```python
prev_data = write_fbo.color_attachments[0].read()   # GPU -> CPU
self._prev_fbo.color_attachments[0].write(prev_data)  # CPU -> GPU
```

1,9 MB bajando y subiendo por el bus cada fotograma. Y `read()` además
**sincroniza**: obliga a la CPU a esperar a que la tarjeta vacíe todo lo
pendiente, así que no sólo cuesta la copia — tira por tierra el trabajo en
paralelo de los dos procesadores, que es la razón de tener una GPU. Con
`copy_framebuffer`, la misma copia dentro de la tarjeta: **5,45 → 0,12 ms**,
45 veces menos.

La lección general, y vale para cualquier efecto futuro: en esta tubería
**mover píxeles cuesta mucho más que calcularlos**. Los dos hallazgos grandes
de rendimiento —la subida (AUD-229) y éste— son el mismo error con distinta
ropa.

### Lo que se ganó, y de dónde

| | antes | después | |
|---|---|---|---|
| Subir el fotograma | 10,98 ms | **0,20 ms** | AUD-229 |
| Bloom en GPU | 3,39 ms | **1,70 ms** | AUD-230 |
| Camino GL completo | 7,96 ms | **3,76 ms** | 2,1× |
| Todas las pasadas | 25,80 ms | **15,32 ms** | 1,7× |

**La subida era el mayor coste de todo el renderizado.** Cada fotograma se
hacía `pygame.image.tostring(superficie, "RGBA", True)` —una pasada por los
480.000 píxeles en Python para reordenar canales y voltear— y el `bytes`
resultante obligaba a moderngl a copiarlo otra vez:

```
pygame.image.tostring(RGBA, flip=True)    3,458 ms
texture.write(bytes)                      7,517 ms
texture.write(memoryview de la surface)   0,200 ms
```

Escribir el búfer de la superficie no convierte ni copia. A cambio, los píxeles
llegan como los guarda pygame, y el sombreador de subida arregla las tres
diferencias: el volteo, el orden de canales y —la que costó encontrar— **el
alfa**.

> Una `Surface` creada sin `SRCALPHA` tiene la máscara de alfa a cero, así que
> su cuarto byte vale 0. `tostring` lo repone a 255 al convertir; el búfer
> crudo no. Con `GL_BLEND` activo y `SRC_ALPHA, ONE_MINUS_SRC_ALPHA`, un
> fragmento con alfa 0 **no escribe nada**: la pantalla salía entera del color
> de limpieza, sin un solo error en consola.

El orden de canales **se detecta**, no se supone: `GLRenderer._swizzle_de()`
lee las máscaras de la superficie, y si el formato no es uno de los dos
conocidos se vuelve al camino de `tostring`, que funciona en cualquier parte.
Equivocarse aquí no da un error, da los colores cambiados.

El bloom, por su parte, se hace en el FBO de media resolución que la tubería
**ya reservaba y nunca usó** (`_bloom_fbo`, creado desde el primer día). A un
cuarto de píxeles el mismo kernel cuesta un cuarto, y el halo sale más suave
gratis: al recomponer, el filtrado bilineal lo interpola de vuelta.

---

## 5. Cómo un escenario enciende un efecto

Ninguna escena alcanza el `GLRenderer` —eso acoplaría `framework/` a que exista
contexto GL—. Todo viaja por `gpu_effects`, que `App` lee una vez por
fotograma. `begin_frame()` lo borra todo al empezar, para que un menú no herede
el estanque ni los rayos del nivel del que se acaba de salir.

| Efecto | Se enciende con | Quién lo dispara |
|---|---|---|
| **Bloom** | propiedad de TMX + `set_bloom()` en el juego | `PostProcessing` publica la intensidad cada fotograma |
| **Aberración cromática** | `gpu_effects.request_chromatic_aberration(f)` | `stage_parts/senales.py` al recibir daño; la fuerza sube cuanta menos vida queda |
| **Refracción** | propiedad de mapa `water_effect` | `StageScene` publica la región; con GL sustituye a `WaterEffect` |
| **Rayos** | propiedad de mapa `god_rays` | `StageScene` publica el foco: la luz **más fuerte que esté en pantalla**, ponderando intensidad y radio |

El foco de los rayos lo elige la escena y no la tubería porque ésta sólo ve una
textura de luz ya compuesta, con los focos mezclados. Si el escenario pide
rayos y no hay ninguna luz visible, se apagan: un abanico saliendo de la nada
es peor que ninguno.

---

## 6. Límites conocidos

- **El filtro de daltonismo de GL no se ejecuta jamás.** `colorblind_frag`
  existe, pero `GLRenderConfig.colorblind_mode` vale 0 y `App` no lo toca
  nunca. Sus matrices además no son las de la CPU (AUD-138). Enchufarlo
  cambiaría lo que ve un jugador daltónico sin que nadie lo haya mirado en una
  pantalla: es trabajo aparte, no parte de quitar una duplicación.
- **Ninguna pasada tiene prueba de píxeles en CI.** `SDL_VIDEODRIVER=dummy` no
  da contexto OpenGL. Lo que se prueba sin tarjeta es el plumbing, el orden de
  la cadena, la conversión de coordenadas y que las pasadas se salten cuando
  están apagadas. El aspecto hay que verlo lanzando el juego.
- **La región de agua es la pantalla entera**, porque eso es lo que cubre hoy
  `WaterEffect` y `water_effect` es un booleano de escenario. Cuando las zonas
  de agua del ECS expongan su rect en pantalla, se estrecha en
  `StageScene._publicar_o_dibujar_el_agua` — la tubería ya acepta cualquier
  rectángulo.
- **Los rayos no tienen equivalente por CPU.** Un escenario que los pida se ve
  igual que siempre en una máquina sin ModernGL.
- **`destroy()` no libera todos los programas.** Se sueltan los añadidos en
  esta línea de trabajo; el resto sigue sin liberarse, y queda anotado.

---

## 7. Dónde está cada cosa

| Fichero | Qué |
|---|---|
| `src/engine/render/gl_pipeline.py` | `GLRenderConfig`, `GLRenderer`, la cadena de pasadas y `region_to_gl_uv` |
| `src/engine/render/shaders.py` | Todo el GLSL. `upload_frag` y `godray_frag` son funciones porque su fuente depende de la configuración |
| `src/engine/core/gpu_effects.py` | El reparto CPU/GPU y el canal escena → tubería |
| `src/engine/core/app.py` | Raíz de composición: declara el reparto y conduce los efectos por fotograma |
| `src/framework/vfx/post_processing.py` | La tubería de CPU, que se calla en lo que la GPU asume |

Pruebas: `test_cada_pasada_ejecuta_su_shader.py`, `test_subida_de_la_escena.py`,
`test_postprocesado_no_se_duplica.py`, `test_aberracion_cromatica.py`,
`test_refraccion_bajo_el_agua.py`, `test_rayos_de_luz.py`.

---

## 8. Alrededor de la tubería: qué más se midió

Todo lo de esta sección salió de perfilar **stage0 en marcha**, 240 fotogramas
de `update` + `draw` con `cProfile`, no de suposiciones.

### Dónde se va el fotograma en el camino software

```
blit de superficies (66 por fotograma)   3,10 ms
smoothscale (bloom de CPU)               0,85 ms
PostProcessing._apply_bloom              2,10 ms
LightSource.build_gradient               0,35 ms
partículas (update + draw)               0,23 ms
enemigos: update de 9 entidades          0,42 ms
```

Con el camino GL, los 2,95 ms de bloom y `smoothscale` desaparecen de la CPU y
se convierten en 1,70 ms de tarjeta (§4).

### Físicas: no son el cuello, y sobraba una librería

El benchmark `test_physics_500_entities` marca 14,2 ms, y ese número asusta sin
leerlo: mide **60 fotogramas**, así que son 0,24 ms por fotograma con 500
entidades. En stage0 real, la actualización de los nueve enemigos cuesta
**0,42 ms**. La física no aparece en ninguna de las diez primeras posiciones
del perfil.

Lo que sí apareció es una dependencia obligatoria que **nadie importa**:
`pymunk`. La pedía `collision_system.py`, que construía un `pymunk.Space` con
cero cuerpos y llamaba a `step()` cada fotograma para integrar un mundo vacío;
esa simulación se retiró y la dependencia se quedó (AUD-235). Importa porque
pymunk es una extensión en C y este proyecto ya se quedó sin poder instalarse
en Python 3.13 por una rueda que faltaba: cada dependencia obligatoria de más
es otra forma de que `pip install -e .` falle el día de la entrega. Lo vigila
ahora `tests/test_dependencias_que_se_usan.py`, que comprueba que **todo** lo
declarado en `[project].dependencies` se importe en algún sitio de `src/`.

**Conclusión sobre físicas: no hay nada que optimizar ahí todavía.** Meter un
motor de cuerpos rígidos hoy añadiría coste y una librería, para resolver un
problema que no existe. El día que un escenario necesite pilas de cajas o
cuerdas, la conversación cambia — y entonces será pymunk, bien enchufado.

### VFX de partículas y clima: viable, y ya casi está

Medido tras AUD-214, sobre el emisor real:

| partículas vivas | update | draw | total | del presupuesto |
|---|---|---|---|---|
| 332 | 0,14 ms | 0,40 ms | 0,53 ms | 3 % |
| 2.012 | 0,49 ms | 2,30 ms | 2,78 ms | 17 % |
| 4.050 | 0,97 ms | 4,72 ms | 5,69 ms | 34 % |
| 8.100 | 1,61 ms | 8,87 ms | 10,47 ms | 63 % |
| 13.500 | 2,17 ms | 14,29 ms | 16,46 ms | 99 % |

**Las «miles de partículas» de la propuesta ya caben sin tocar nada más.**
2.000 cuestan el 17 % del fotograma y 4.000 el 34 %; en un escenario real las
partículas consumen hoy 0,23 ms porque nadie pide tantas. El techo práctico,
dejando sitio al resto del juego, está entre **4.000 y 6.000**.

El clima (`WeatherSystem`) usa el mismo emisor, así que hereda esas cifras; su
capa de color ya está cacheada desde F1.3 y cuesta un `blit`.

Lo que gobierna el coste es el **dibujado** (4,72 de los 5,69 ms con 4.050), no
la simulación. O sea que el siguiente paso, si algún día hace falta pasar de
6.000, es dibujarlas en GPU — y **eso sí es viable aquí**, a diferencia del
sprite batching: el sistema de partículas es del motor, no de las entregas, y
se dibuja sobre el mundo ya compuesto. Una pasada instanciada sobre la textura
de escena no tocaría el API que usan los 26 escenarios. Es la única de las
propuestas de «acelerar por GPU» que no choca con la invariante 2.

> **Nota de fiabilidad de la medición (2026-08-08).** La prueba del presupuesto
> de `stage4_1` —`TestCabeEnElPresupuestoDeFotograma`, 12 ms, visión a 1/4 de
> resolución— es sensible a la carga de la máquina y queda justo en el borde:
> en este portátil (Quadro M2200) la visión mide ~7-8 ms con la máquina fría y
> 13-16 ms bajo carga térmica o procesos en segundo plano (el 2026-08-08 dos
> `_val.py` de VS Code consumían dos núcleos enteros durante horas). Verificado
> que **no** es dependiente del orden de pruebas (falla también aislada bajo
> carga) y que es preexistente: con `git stash` sobre un estado commiteado sin
> cambios de AUD-340 falla igual. No se toca el umbral de 12 ms: el docstring
> del nivel documenta el razonamiento del 1/4 de resolución y sus 4,6 ms.

### Iluminación y sombras en los sprites

**La luz ya llega a los sprites**: `lighting_frag` multiplica la escena por el
mapa de luz, así que un sprite dentro de un foco se ve iluminado y fuera, no.
Lo que no hay es **volumen**: la luz no distingue el relieve del sprite porque
no hay información de relieve que consultar.

| Técnica | Viabilidad | Por qué |
|---|---|---|
| **Sombras arrojadas bajo la entidad** | **Alta** | Una elipse oscura achatada bajo cada entidad, escalada por la altura sobre el suelo. Sin assets nuevos, coste de un `blit` por entidad, y es lo que más asienta a un personaje en el suelo |
| **Sombras proyectadas por geometría** | Media | Polígonos de sombra 2D desde cada foco contra las colisiones. Es geometría por CPU y hay que medirla antes |
| **Normal mapping** | **Baja** | Exige un mapa de normales **por sprite** (el pipeline de assets es procedural: no existe ninguno) y sombreado por sprite, que esta tubería no puede hacer porque sólo ve el fotograma ya compuesto. Rompería además el dibujado que usan las entregas |

El orden sensato es el de la tabla: las sombras bajo la entidad dan la mayor
parte de la sensación de volumen por una fracción del coste, y no piden ni un
asset ni tocar cómo dibujan las 26 entregas.

> **Actualización de la fila de normal mapping (AUD-340, fase 5 lote 1).** La
> tabla de arriba se escribió antes de la petición del dueño de 2026-08-07 y
> de la suspensión de las invariantes 1-2 que la acompañó. Las dos objeciones
> que la anclaban en «Baja» han cambiado:
>
> * «no existe ningún mapa de normales» — resuelto, y sin pipeline de assets:
>   `src/engine/render/normales.py` **deriva** la normal del alfa del sprite
>   (tratar lo opaco como altura y tomar su gradiente), y quien quiera una
>   normal hecha a mano la pasa como segundo atlas.
> * «rompería el dibujado que usan las entregas» — la restricción que lo
>   prohibía quedó suspendida el mismo día.
>
> Lo que el lote 1 entrega es el renderizador aislado
> (`SpriteBatchGPU`, `src/engine/render/gpu_sprite_batch.py`): quads
> instanciados contra el atlas, tinte, cámara y luz ambiental + direccional +
> focos puntuales, con una rama plana que dibuja los sprites sin luz
> EXACTAMENTE como un blit. Lo que **no** entrega todavía es la composición
> dentro de esta tubería —dibujar el lote en un FBO y mezclarlo con la escena
> como una pasada más—, que es el lote 2 y el que de verdad decide el aspecto
> final. El estado vivo de la fase 5 está en `docs/87` §27.

---

## Documentos relacionados

- `docs/70_INFORME_DE_AUDITORIA_VIVO.md` — iteración 12, con el detalle de cada hallazgo
- la propuesta `72_VIABILIDAD_PROPUESTA_V2` (retirada) originó este trabajo
- `docs/03_ARCHITECTURE.md` — capas y reglas que acotan dónde puede vivir el reparto
- `CLAUDE.md` — las invariantes
