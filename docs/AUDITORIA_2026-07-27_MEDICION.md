# Auditoría de medición — Legacy of InFest

**Fecha:** 27 de julio de 2026
**Método:** ejecución y cronometraje, no lectura de código
**Commit:** `8c476c8`

---

## Advertencia sobre este documento

Pediste una auditoría desde cero. No la hice desde cero en el sentido de
olvidar lo aprendido —eso habría sido tirar evidencia medida—, sino en el
sentido que importa: **volví a medir todo hoy, con el código de hoy**, y cada
número de este informe sale de un comando que ejecuté, no de mi memoria ni de
mi juicio sobre el código.

Cada afirmación lleva una etiqueta:

- **MEDIDO** — hay un comando detrás y un número que salió de él.
- **JUZGADO** — es mi opinión. Puede estar equivocada.

No hay puntuaciones globales tipo "91/100". Rechacé firmar el informe externo
que las traía porque una puntuación agregada oculta exactamente lo que hay que
ver: que seis defectos graves convivían con 1.162 pruebas en verde.

---

## 1. Lo que encontré hoy

Diez defectos, agrupados en cuatro fallos reales. Ninguno era visible leyendo
el código. Los diez salieron al **cronometrar escenas fotograma a fotograma**.

| ID | Qué pasaba | Cómo se descubrió | Estado |
|---|---|---|---|
| AUD-073 | `NoiseLabScene` regeneraba el mapa de ruido en **cada** `update()` | la suite se colgó en esa escena | corregido |
| AUD-074 | generar un mapa costaba **295 ms** (bucles de Python sobre 57.600 píxeles) | `faulthandler` sobre el proceso colgado | corregido |
| AUD-075 | Perlin se recortaba contra [0,1] en vez de remapearse: media imagen en negro | inspección del rango tras corregir 074 | corregido |
| AUD-076 | tabla de 256 gradientes construida en cada `__init__` y jamás leída | búsqueda de referencias | corregido |
| AUD-077 | la caché de fuentes devolvía objetos muertos tras `pygame.quit()` | dos pruebas que fallaban sólo en ejecución combinada | corregido |
| AUD-079 | `PatternDemoScene`: el recuadro de análisis se recortaba contra el panel, no contra la imagen | avisos en consola durante el barrido de rendimiento | corregido |
| AUD-081 | el recuadro guía se dibujaba sin escalar al panel ni desplazar | prueba de píxeles sobre el dibujo real | corregido |
| AUD-082 | tirón de **376 ms** en la pantalla de título | percentiles por fotograma, no medias | corregido |
| AUD-078 | `test_student_template.py` apaga pygame tras cada prueba y contamina el proceso | bisección de la suite | mitigado por AUD-077 |
| AUD-083 | `FilterDemoScene`: mediana de 7,8 ms/fotograma (47 % del presupuesto) | barrido de rendimiento | **abierto** |

---

## 2. Los cuatro fallos, con sus números

### 2.1 El laboratorio de ruido corría a 3,4 FPS — MEDIDO

`NoiseLabScene` es una de las demos académicas de la Unidad V. Al abrirla,
generaba un mapa de 320×180 recorriendo los 57.600 píxeles con dos bucles
`for` de Python. Eso costaba **295 ms**. Y como `_param_changed` se ponía a
`True` en cinco sitios y **no volvía a `False` en ninguno**, se regeneraba en
cada fotograma. Para siempre.

```
antes:  295 ms por fotograma  →  3,4 FPS
ahora:    0,6 ms por fotograma
```

Cómo salió: al recorrer todas las teclas de `test_scene_survives_input`, la
suite se quedaba colgada. No fallaba: se colgaba. `faulthandler` apuntó a
`noise_lab_scene.py:211`, dentro del bucle de píxeles.

Los tres modos están ahora vectorizados con numpy. La equivalencia numérica no
se promete, se prueba: `tests/test_noise_lab.py` conserva una **copia literal
del código escalar antiguo** y compara ambos resultados, píxel a píxel, sobre
la imagen de 8 bits que es la que se ve.

De paso aparecieron dos cosas más en el mismo archivo. Perlin produce valores
en [-1, 1] y el código los recortaba contra [0, 1], lo que convertía toda la
mitad negativa en negro plano: **el modo Perlin del laboratorio mostraba media
imagen en negro** y eso se enseñaba como si fuera ruido de Perlin. Y había una
`_grad_table` de 256 gradientes construida en cada `__init__` que nadie leía
nunca — irrelevante por coste, grave por otra razón: un estudiante que abriera
ese archivo para entender Perlin habría estudiado una tabla que no participa
en el resultado.

### 2.2 La caché de fuentes servía cadáveres — MEDIDO

Un `pygame.font.Font` queda inservible en cuanto alguien llama a
`pygame.quit()`. No se recupera: volver a inicializar el módulo hace que
`pygame.font.get_init()` devuelva `True` otra vez, pero el objeto viejo sigue
lanzando `Invalid font (font module quit since font created)` para siempre.

La comprobación que había —`if not pygame.font.get_init(): pygame.font.init()`—
sólo se ejecutaba cuando la caché **fallaba**. Cuando acertaba, devolvía el
cadáver sin mirarlo. Resultado: cualquier pantalla que pasara por el kit de
interfaz reventaba.

Cómo salió: dos pruebas de `test_tmx_diagnostics.py` pasaban en solitario y
fallaban en ejecución combinada. La causa era `test_student_template.py`, que
apaga pygame después de cada una de sus 22 pruebas (AUD-078).

Esto no es sólo un problema de pruebas. Le pasaría al juego tras cualquier
reinicio del módulo de vídeo — y `clear_font_cache()`, la función que existe
justo para esto, **no la llamaba nadie**.

```
coste de validar en cada acierto : 0,080 µs
coste de la propia búsqueda      : 0,095 µs
```

Validar sale más barato que buscar. Se hace siempre.

### 2.3 La demo de reconocimiento de patrones no funcionaba — MEDIDO

`PatternDemoScene` (Unidad VIII) recortaba su recuadro de análisis contra
`RIGHT_PANEL_W` = 256 y `PANEL_H` = 483 — las medidas del **panel de dibujo**.
La imagen de origen mide **32×32**. El recuadro arrancaba en (64, 74) con lado
32: fuera de la imagen desde el primer fotograma.

`subsurface` lanzaba, el `except` lo convertía en `logger.warning`, y la escena
mostraba `Error: subsurface rectangle outside surface area` en bucle a
cualquiera que la abriera.

Pasó el arnés de humo porque el arnés comprueba que la escena **no se caiga**,
y ésta no se caía. Hacía exactamente lo que se le pidió: sobrevivir.

Segundo defecto en la misma pantalla: el recuadro guía amarillo se dibujaba en
coordenadas de la imagen original sobre un panel que muestra esa imagen
**escalada** de 32×32 a 256×483, y sin sumar el desplazamiento vertical del
`blit`. El estudiante no podía apuntar a lo que estaba analizando.

### 2.4 Tirón de 376 ms en la pantalla de título — MEDIDO

```
TitleScene, 120 fotogramas:
  mediana   0,70 ms
  p95       1,33 ms
  peor    376,52 ms   ← veintidós fotogramas perdidos de golpe
```

La media (11,9 ms) no delataba nada: cabía en el presupuesto. Sólo los
percentiles lo enseñan.

Causa: `@numba.njit` compila en la **primera llamada**, no al importar. Esa
primera llamada caía en el primer fotograma con partículas — en la primera
pantalla que ve el jugador.

Corrección: precalentar durante la pantalla de inicio, que dura 3 s, no es
interactiva y su `update` no hace nada más que contar el tiempo. No en
`on_enter`, a propósito: eso retrasaría el primer fotograma y el jugador vería
una ventana negra en vez del logo.

```
después:  mediana 0,56 ms | peor 5,59 ms | fotogramas perdidos: 0/120
```

---

## 3. Estado medido del proyecto

Todo lo de esta sección se ejecutó hoy.

| Medida | Valor | Comando |
|---|---|---|
| Archivos fuente | 166 | `find src -name '*.py'` |
| Líneas de código | 31.034 | `wc -l` |
| Archivos de prueba | 65 | `ls tests/*.py` |
| Pruebas recolectadas | **1.228** | `pytest --collect-only` |
| Pruebas en verde | 1.228 / 1.228 | por lotes (límite de 45 s) |
| ruff | limpio | `ruff check src tests scripts tools main.py` |
| Validador TMX | 2/2 | `scripts/validate_tmx.py --ci` |
| Validador de recursos | 0 errores, 0 avisos | `scripts/validate_assets.py` |
| Sincronía de dependencias | 15/15 de acuerdo | `scripts/check_dependency_sync.py` |

**Rendimiento en juego — MEDIDO**

| Escena | ms/fotograma | Presupuesto |
|---|---|---|
| Stage 0 (300 fotogramas) | 8,11 | 49 % |
| Arena del jefe (300 fotogramas) | 3,36 | 20 % |
| `FilterDemoScene` (mediana) | 7,83 | 47 % ← AUD-083, abierto |
| El resto de las 32 escenas | < 1,0 | < 6 % |

**Cadena de escenas — MEDIDO**

`Stage0 → BossVenadoScene → EndCreditsScene`, recorrida entera sin
intervención. Funciona.

**Subsistemas activos durante el juego — MEDIDO**

20 de 22 reciben `update()` cada fotograma. Los dos restantes son correctos:
`_cutscene` sólo se actualiza mientras está activa y `_learning` es una
superposición que sólo dibuja.

---

## 4. Lo que sigue abierto

**AUD-083 — `FilterDemoScene` a 7,8 ms de mediana.** No pierde el fotograma,
pero se come casi la mitad del presupuesto en una demo. No lo he tocado: no
tengo medido dónde se va el tiempo y prefiero no adivinar. *JUZGADO: baja
prioridad, alta probabilidad de que sea un filtro por píxel sin vectorizar,
igual que el ruido.*

**Sin i18n.** 348 cadenas fijas en las escenas y 0 módulos con `gettext`. Los
textos están mezclados: `"INVENTARIO"` junto a `"UNIT V/VIII"`. Para un curso
en español esto importa. *MEDIDO el recuento; JUZGADO que importa.*

**Doce sistemas sin ninguna prueba propia** — MEDIDO:
`audio_manager`, `dynamic_music`, `sound_bank`, `lighting`, `fog_of_war`,
`water_effect`, `trail_system`, `hit_effects`, `progression_system`,
`speedrun_mode`, `boss_rush_mode`, `cutscene_system`.

Se ejercitan indirectamente por el arnés de escenas, que es como se descubrió
que `NoiseLabScene` estaba rota — pero indirecto significa que sólo se detecta
lo que se cae, no lo que hace algo incorrecto. Es exactamente el hueco por el
que se coló `PatternDemoScene`.

**El modelo `.pkl` está atado a una versión de scikit-learn** — MEDIDO:
`professor_sample.pkl` se entrenó con 1.9.0 y al cargarlo con 1.7.2 sklearn
avisa de "invalid results". Un estudiante con otra versión obtiene predicciones
silenciosamente distintas.

**`test_gameplay_integration.py` tarda ~50 s** para 26 pruebas, porque cada una
construye una escena completa. No es un defecto; es una factura que crecerá.

---

## 5. La lección, otra vez

Mientras corregía AUD-082 rompí la transición de la pantalla de inicio: mi
edición insertó la definición de un método **dentro** de `update()`, dejando
huérfana la lógica de fundido. El juego se quedaba en el splash para siempre.

Lo cazó `test_menu_navigation.py::test_splash_to_title` en la siguiente
ejecución.

Es la sexta vez en esta auditoría que **yo** introduzco un defecto de cableado:
código correcto, probado en aislamiento, mal conectado. Vale la pena decirlo
claro porque es el patrón dominante de todo este trabajo, y no lo produce la
ignorancia sino la edición. Las pruebas de integración —las que ejecutan el
juego de verdad, no las que ejercitan una clase— son lo único que lo detecta.

El patrón de los defectos encontrados hoy es el mismo de siempre, con un giro:
los cuatro **sobrevivían a 1.162 pruebas en verde** porque todas preguntaban
"¿se cae?" y ninguna preguntaba "¿funciona?" ni "¿va rápido?". Una escena que
muestra un mensaje de error en bucle pasa el arnés de humo con nota.

Las 62 pruebas nuevas de hoy preguntan otras tres cosas: si el resultado es
correcto, si llega a los píxeles, y cuánto tarda.

---

## 6. Verificación por mutación

Ninguna corrección se da por buena sin comprobar que su prueba la vigila. Cada
una se revirtió a mano y se comprobó que la suite se pusiera roja:

| Mutación | Pruebas que fallan |
|---|---|
| no apagar `_param_changed` | 2 |
| volver a recortar Perlin sin remapear | 1 |
| quitar el recorte del recuadro de análisis | 8 |
| volver a dibujar el recuadro sin escalar | 3 |
| quitar la validación de la caché de fuentes | 3 |
| que la pantalla de inicio no precaliente | 2 |

Seis de seis detectadas.
