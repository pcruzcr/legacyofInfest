# Las tres fases, terminadas

**Fecha:** 27 de julio de 2026 · **Commit final:** `f6c005f`
**Punto de partida:** `6f19291` (auditoría de medición)

---

## Lo que pasó, en una frase

Las tres fases eran «encender lo que ya existe», y encender las cosas destapó
**once defectos** que llevaban ahí desde siempre, invisibles porque nadie había
mirado los píxeles.

El más caro: **el sistema de iluminación no había iluminado un solo píxel en
toda la vida del proyecto.** Estaba instanciado, cableado, actualizándose cada
fotograma y con focos activos. Y cada foco era un disco completamente negro,
porque `216 * 255` en `uint8` da 40.

---

## Fase 1 — Encender lo que ya existe

| Tarea | Qué se hizo | Defectos encontrados |
|---|---|---|
| F1.1 | Iluminación: focos desde Tiled, ambiente por TMX | **4** |
| F1.2 | Bloom y viñeta | **3** |
| F1.3 | Clima y partículas de ambiente | **5** |
| F1.4 | Estelas del jugador y de los jefes | **3** |
| F1.5 | Verificación, guía del estudiante, README | — |

### Los que más importan

**AUD-086 — la luz nunca iluminó.** `build_gradient` calculaba el color así:

```python
val = (intensidad * caída * 255).astype(np.uint8)
arr[:, :, 0] = (val * color[0] / 255).astype(np.uint8)
```

`val` es `uint8` y `color[0]` llega a 255, que **también cabe en un uint8**.
NumPy conserva el tipo pequeño: `216 * 255 mod 256 = 40`, dividido entre 255
da 0,157, convertido a entero da **0**. Medido: el centro de un foco daba
exactamente el mismo valor que la esquina de la pantalla.

**F1.2a — el bloom aclaraba las sombras más que las luces.** El halo se sumaba
tras un `set_alpha`, y `set_alpha` no tiene efecto con `BLEND_RGB_ADD`. Medido:
un fondo de valor 43 subía a 239 y una zona brillante de 208 subía a 234.

**AUD-088 — 2,3 segundos de congelación dentro de la partida.** `squad_brain`
importa scikit-learn la primera vez que un enemigo consulta al predictor, en el
fotograma 16. Se precalienta ahora en la pantalla de inicio.

**AUD-089 — un aula sin tarjeta de sonido tumbaba el juego.** `stop_music` y
compañía llamaban a `pygame.mixer` sin comprobar que existiera.

**F1.3d — el viento de la tormenta era una sentencia sin efecto:**
`random.choice([-1, 1]) * random.uniform(50, 100)`, calculada y asignada a
nada.

### Coste medido, antes y después

| | Referencia (inicio de sesión) | Con todo encendido |
|---|---|---|
| Stage 0, mediana | 8,11 ms | **8,40 ms** |
| Arena del jefe, mediana | 3,36 ms | 7,70 ms |
| Peor fotograma del título | 376 ms | **5,6 ms** |

Encender la atmósfera entera cuesta menos que el tirón de sklearn que se
eliminó.

---

## Fase 2 — Lo que faltaba de verdad

| Tarea | Qué se hizo |
|---|---|
| F2.1 | Ciclo día/noche desde el TMX (`start_hour`, `day_length`) |
| F2.2 | Estaciones (`season`) |
| F2.3 | **Sobel y Canny escritos a mano**, junto a los de OpenCV |
| F2.4 | El calificador puntúa **diseño**, no sólo estructura |
| F2.5 | Pruebas para los sistemas huérfanos |

### El límite que hace jugable el ciclo

El factor horario multiplica el `ambient_light` del mapa, así que los dos se
componen. Con el factor nocturno inicial de 0,35 sobre el 0,70 de Stage 0, el
brillo medio de pantalla a medianoche caía a **12,7 sobre 255**: sólo el 31 %
de los píxeles superaba el umbral de legibilidad y el jugador no veía a los
enemigos.

Una noche realista que impide jugar es un defecto, no una decisión artística.
La hora se comunica ahora sobre todo por el **color**.

| Hora | Ambiente | Tinte | Brillo | Legible |
|---|---|---|---|---|
| 12:00 | 0,70 | (255, 252, 245) | 44,9 | 89 % |
| 20:00 | 0,46 | (235, 165, 175) | 24,2 | 40 % |
| 00:00 | 0,45 | (165, 180, 235) | 25,2 | 44 % |
| 08:00 | 0,57 | (255, 210, 180) | 31,8 | 73 % |

### Sobel y Canny: de demostración a lección

Las Unidades VII y VIII llamaban a `cv2.Sobel` y `cv2.Canny`. Quien sólo ve
`cv2.Canny(gray, 50, 150)` aprende una API, no un algoritmo.

Ahora hay dos versiones de cada uno, y **conviven a propósito**:

| | Coincidencia con OpenCV | Propio | OpenCV | Factor |
|---|---|---|---|---|
| Sobel | 100 % | 1,72 ms | 0,10 ms | 17× |
| Canny | 98,3 % | 3,73 ms | 0,074 ms | 50× |

Hay una prueba que verifica que la versión propia **sea más lenta**. Si dejara
de serlo, o está mal o alguien cambió la referencia.

### Dos defectos en el modo Boss Rush

Nadie lo había probado nunca.

1. **No se podía terminar.** `is_complete()` exigía `_active and índice >=
   total`, y el código nunca pasaba el índice del último jefe y además apagaba
   `_active` al llegar al final. Las dos condiciones eran incompatibles: un
   modo de juego sin final.
2. **El último jefe no contaba.** Sólo se acreditaba al jefe si quedaba otro
   después. Derrotar al final no daba puntos y lo dejaba marcado como vivo.

Los dos se anulaban lo justo para que nada crujiera: nadie llegaba al final
porque el final no existía.

### El calificador

Antes se podía sacar más del 90 % colocando objetos en un rectángulo vacío.
Ahora 30 de 130 puntos miden diseño real:

| Mapa | Nota | Qué le pasa |
|---|---|---|
| stage0 | 86,2 % | 2 plataformas sin ruta; ningún salto exigente |
| plantilla | 63,8 % | Trivial geométricamente: un rectángulo plano |
| arena del jefe | 44,6 % | La rúbrica no aplica — y el informe lo dice |

---

## Fase 3 — Producción docente

| Tarea | Qué se hizo |
|---|---|
| F3.1 | Internacionalización, español por defecto |
| F3.2 | Previsualizador de TMX |
| F3.3 | Modelo desanclado de sklearn + ejecutable |

**La traducción se hace dentro del kit de interfaz**, no en cada escena. Las
treinta pantallas pasan por `draw_screen`, así que se cubren todas sin tocar
treinta archivos — y sin que un estudiante que escriba una escena nueva tenga
que acordarse de nada.

**El previsualizador cierra el ciclo del estudiante.** Antes, ajustar el radio
de una antorcha costaba una partida entera por intento: en Tiled un `Light` es
un cuadrado de 16 px. Ahora `preview_tmx.py` dibuja el mapa entero con la
iluminación aplicada, el radio real de cada foco y un resumen de lo que
encontró.

**El modelo de la Unidad IX ya no depende de tu versión de scikit-learn.** El
`.pkl` comprometido se entrenó con 1.9.0; con otra versión la biblioteca avisa
de «invalid results» y dos estudiantes obtenían resultados distintos sin
señal alguna. Ahora se entrena desde el dataset y se cachea localmente: 189 ms
la primera vez, 9 ms después, cero avisos.

---

## Estado final — MEDIDO

| | Antes de las fases | Ahora |
|---|---|---|
| Pruebas | 1.333 | **1.503** |
| Archivos de prueba | 63 | 70 |
| ruff | limpio | limpio |
| Validador TMX | 2/2 | 2/2 |
| Catálogos de idioma | — | en orden |

Todo verde, verificado por lotes.

**Propiedades nuevas que un estudiante puede usar desde Tiled, sin escribir
Python:** `ambient_light`, `bloom`, `vignette`, `climate`, `ambient_fx`,
`ambient_fx_rate`, `start_hour`, `day_length`, `season`, y el objeto `Light`
con seis propiedades propias. Todas documentadas en `docs/STAGE_CREATION.md`,
con una prueba que impide que la guía se desincronice del motor.

---

## La lección, otra vez

Cada fase de este trabajo consistía en encender algo que «ya estaba hecho», y
cada una destapó defectos. El patrón se repitió once veces con la misma forma:

**Código correcto, probado en aislamiento, que no llegaba a la pantalla.**

- La luz: gradientes negros por un desbordamiento de un byte.
- Las partículas de ambiente: `set_effect` que nadie llamaba.
- El bloom: `set_alpha` ignorado por el modo de mezcla.
- Las estelas: un intervalo declarado y nunca comparado.
- El viento: una expresión calculada y asignada a nada.
- El modo Boss Rush: un final inalcanzable.

Ninguno se veía leyendo el código. Todos aparecieron al **mirar los píxeles y
cronometrar fotogramas**.

Y una advertencia que me aplico a mí mismo: durante estas fases escribí varias
pruebas que **no podían fallar** —una que reimplementaba la regla que decía
comprobar, otra que buscaba una cadena en todo el archivo en vez de en su
tabla, otra que medía el estado final de un efecto transitorio y por tanto
medía el silencio posterior—. Las tres pasaron con el código roto. Las cacé
mutando el código a propósito y comprobando que la suite se pusiera roja.

Esa disciplina —romper a mano cada corrección y verificar que algo se queja— es
lo único que separa una suite de 1.503 pruebas de una sensación de seguridad.
