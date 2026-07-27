# Qué falta, quién puede usarlo, y hasta dónde se puede llegar

**Fecha:** 27 de julio de 2026 · **Commit:** `272160c`
**Método:** medición sobre el código de hoy. Cada afirmación va marcada
**MEDIDO** (hay un comando detrás) o **JUZGADO** (es mi opinión, puede fallar).

---

## Resumen en una página

El motor está **más sano de lo que el juego demuestra**. Ése es el hallazgo
central y condiciona todo lo demás.

Los sistemas de atmósfera —luz, clima, partículas, post-procesado, estelas—
existen, están cableados y se actualizan cada fotograma. Pero en Stage 0 no
producen **nada**: brillo ambiente en 1.0 (luz invisible), clima `clear` (cero
partículas), cero efectos de post-procesado activos, cero partículas ambientales,
cero estelas. **MEDIDO.**

Eso significa dos cosas a la vez, y conviene no mezclarlas:

1. **La mala:** un estudiante que abra el juego no ve ninguna de esas
   capacidades, así que para él no existen. No puede aprender de lo que no ve.
2. **La buena:** encender la atmósfera es trabajo de *contenido*, no de
   ingeniería. Es barato. La distancia entre lo que hay y algo que impresione
   es mucho menor de lo que parece jugando.

Sobre la pregunta directa —*¿podemos hacer un Castlevania mejor que Symphony
of the Night?*— la respuesta honesta está en la sección 6. Adelanto: no con
este equipo y este calendario, y las razones no son técnicas. Pero hay un
objetivo cercano que sí es alcanzable y que probablemente vale más para lo que
estás haciendo.

---

## 1. Qué falta para llamarlo "listo para producción"

Producción significa cosas distintas según a qué te dediques. Aquí uso la
definición que aplica a tu caso: **un semestre con 30 estudiantes sin que tú
tengas que apagar incendios**.

### Bloqueantes reales — MEDIDO

| # | Qué | Por qué bloquea | Coste estimado |
|---|---|---|---|
| 1 | **Sin internacionalización.** 348 cadenas fijas en las escenas, 0 módulos con `gettext`. La interfaz mezcla `"INVENTARIO"` con `"UNIT V/VIII"`. | Curso en español, interfaz a medias en inglés. Es lo primero que ve el estudiante. | 3–5 días |
| 2 | **Documentación en el idioma equivocado.** ~52 documentos en inglés, ~20 en español, de 71 totales. | El manual del estudiante, la especificación TMX y las guías de creación son el material de clase. | 1–2 semanas (traducir sólo los 12 que el estudiante lee) |
| 3 | **12 sistemas sin pruebas propias:** `audio_manager`, `dynamic_music`, `sound_bank`, `lighting`, `fog_of_war`, `water_effect`, `trail_system`, `hit_effects`, `progression_system`, `speedrun_mode`, `boss_rush_mode`, `cutscene_system`. | Es el hueco exacto por donde se coló `PatternDemoScene`, que mostraba un error en bucle y pasaba todas las pruebas. | 1 semana |
| 4 | **El modelo `.pkl` atado a una versión de scikit-learn.** Entrenado con 1.9.0; con 1.7.2 la librería avisa de "invalid results". | Estudiantes con distinta versión obtienen predicciones distintas y silenciosas. Un laboratorio que da resultados distintos según la máquina no es un laboratorio. | 1 día (reentrenar en el arranque o fijar versión) |
| 5 | **README desfasado.** Dice "369 pruebas automatizadas"; hay 1.228. | Síntoma, no causa: nadie lo actualiza porque nada lo comprueba. | 1 hora + una prueba que lo vigile |

### Ya no bloquean (corregido hoy)

- **AUD-084** — `validate_tmx.py` y `grade_stage.py` reventaban con un
  traceback ante una ruta relativa. Es decir: la herramienta para que el
  estudiante revise su mapa antes de entregarlo, y el calificador del profesor,
  fallaban en el primer intento. La CI no lo veía porque `--ci` pasa rutas ya
  resueltas. **Era el defecto más caro del proyecto** medido en confianza
  perdida por alumno.
- **AUD-085** — el mismo validador volcaba ocho líneas de pila si faltaba
  pygame, exactamente en el minuto en que el estudiante aún no sabe si el
  problema es suyo.

### Lo que NO falta (y conviene saberlo)

- Arquitectura: patrones bien aplicados y visibles —Estado (27 clases),
  Plantilla, Fábrica, Registro, Bus de eventos con referencias débiles. **Es
  material didáctico legible, no sólo código que funciona.** *JUZGADO.*
- Rendimiento: Stage 0 a 8,11 ms/fotograma, arena del jefe a 3,36 ms, sobre un
  presupuesto de 16,67. **MEDIDO.**
- Validación automática: TMX, recursos, sincronía de dependencias, todos en CI.
- 1.228 pruebas en verde, ruff limpio.

---

## 2. Las cuatro rutas de uso

### 2.1 El programador de juegos

**Lo que se encuentra — MEDIDO:** 166 archivos, 31.034 líneas, separación
`engine/` (genérico) ↔ `framework/` (específico del juego) ↔ `stages/`
(contenido). API de escenario declarada por herencia: heredas `StageScene`,
declaras `TMX_PATH`, y tienes cámara, colisiones, HUD, minimapa, guardado,
logros y música dinámica.

**Fricción real:** para añadir un tipo de entidad hay que tocar el registro de
`StageLoader`, la fábrica y el validador. Tres sitios. *JUZGADO: debería ser
un decorador, `@register_entity("MiEnemigo")`.*

**Veredicto:** usable hoy para un prototipo 2D serio. Lo que no tiene es
`pip install legacy-of-infest` — es un repositorio del que se parte, no una
librería que se importa. *JUZGADO.*

### 2.2 El estudiante universitario

**Lo que tiene que hacer para su primer escenario:** copiar
`student_templates/stage_template/`, editar el `.tmx` en Tiled, cambiar tres
atributos de clase y rellenar los `TODO(student)`. **71 líneas de plantilla,
de las cuales sólo cinco son obligatorias.** MEDIDO. La estructura es buena.

**Los tres problemas:**

1. **No hay editor visual propio.** Usan Tiled, que es correcto —es la
   herramienta estándar de la industria— pero significa que el estudiante
   trabaja a ciegas: coloca objetos en Tiled y sólo ve el resultado al lanzar
   el juego. **MEDIDO:** no existe ninguna herramienta de previsualización.
2. **El validador les fallaba.** Corregido hoy. Era el único mecanismo que
   tenían para saber si iban bien antes de entregar.
3. **La interfaz está a medias en inglés** y la documentación mayoritariamente
   también.

**Veredicto:** el modelo Lego funciona. La plantilla es honesta y el `--stage`
para probar sin tocar el menú es acertado. *JUZGADO: el eslabón débil no es el
código, es el ciclo de realimentación.*

### 2.3 El profesor universitario

**Lo que existe — MEDIDO:** seis herramientas de calificación
(`grade_stage`, `grade_boss`, `generate_exam`, `plagiarism_detector`,
`feedback_generator`, `grade_exporter`), 71 documentos incluyendo rúbricas,
banco de exámenes, guía de auxiliar docente, calendario de curso y cuatro
tareas especificadas.

Comprobé que el calificador **discrimina de verdad**: Stage 0 saca 91 % y la
plantilla vacía saca mucho menos. Una rúbrica que puntúa igual todo no informa
de nada; ésta no lo hace. Hay una prueba que lo vigila.

**Lo que falta:** los calificadores puntúan **estructura**, no **diseño**. Un
estudiante puede sacar 91 % con un escenario injugable —basta poner los
objetos correctos en un mapa aburrido—. `level_metrics.py` (376 líneas) y el
arnés de playtest automático ya calculan métricas de diseño real; **no están
conectados al calificador**. *JUZGADO: es la mejora de mayor retorno para ti,
y es cuestión de días, no de semanas.*

**Veredicto:** sí, un profesor universitario puede usarlo. Corregido el fallo
de rutas, el flujo *recibir → calificar → exportar notas → generar
realimentación* está completo y funciona desde la terminal.

### 2.4 La persona que no sabe nada

**MEDIDO:** el README son 22 líneas, en español, con `pip install -r
requirements.txt` y `python main.py`. `main.py` comprueba las dependencias y
avisa por nombre de paquete. Eso está bien resuelto.

**Lo que falla:** el README es una lista de características y de correcciones
recientes —menciona "14 bugs de crash corregidos en 3 commits"— en lugar de un
camino. Alguien que llega no necesita saber cuántos bugs se arreglaron;
necesita saber qué va a ver y qué teclas tocar.

*JUZGADO: no hay ejecutable. Para un no-programador, "instala Python" ya es
una barrera. Un `.exe` con PyInstaller costaría un día y cambiaría quién puede
abrir esto.*

---

## 3. Cuánto puede aprender de verdad un estudiante

Ésta es la pregunta más importante que me hiciste, así que la respondo con lo
que medí, separando lo que enseña de lo que sólo demuestra.

### Lo que enseña de verdad — MEDIDO

| Tema | Dónde | Por qué cuenta |
|---|---|---|
| Máquinas de estado | 27 clases de estado del jugador | El estudiante lee un patrón real, no un diagrama |
| Ruido procedural | `noise_lab_scene.py` | Valor, Perlin y fractal implementados a mano, con octavas, persistencia y lacunaridad manipulables en vivo |
| Convolución | `filter_tools.apply_kernel` | Núcleo explícito, `scipy.ndimage.convolve` como motor |
| Histogramas, contraste, ecualización | `filter_tools` | Implementados a mano sobre numpy |
| Curvas de interpolación | `curve_tools.py`, 230 líneas | Bézier y splines propios |
| Detección de colisiones | `collision_system.py`, 257 líneas | AABB, plataformas de un sentido, `coyote time` |
| Bus de eventos y arquitectura | `event_bus.py` | Referencias débiles, un tema que casi nadie enseña |

### Lo que sólo demuestra — MEDIDO

`sobel_edge` y `canny_edge` llaman a `cv2.Sobel` y `cv2.Canny`.
`gaussian_blur` llama a `scipy.ndimage.gaussian_filter`. El estudiante ve el
**efecto** y aprende la **API**, no el algoritmo.

*JUZGADO: esto no está mal per se —en la industria se llama a OpenCV—, pero
para las Unidades VII y VIII, donde Sobel y Canny son el contenido, es una
oportunidad perdida. La corrección es barata y de altísimo valor: implementar
Sobel a mano (son dos convoluciones que ya tienes) y Canny paso a paso
(supresión no-máxima e histéresis), y dejar la versión de OpenCV al lado como
comparación de rendimiento. **Eso convierte un laboratorio en una lección.***

### Mi valoración honesta

Un estudiante que complete el curso completo sale sabiendo, de verdad:
arquitectura de software aplicada, máquinas de estado, convolución, ruido
procedural, interpolación, detección de colisiones y ciclo de vida de un
proyecto con pruebas y CI. **Eso es más de lo que sale sabiendo de la mayoría
de asignaturas de gráficas.** *JUZGADO.*

Lo que **no** aprende: rasterización, pipeline gráfico moderno, matemática 3D,
shaders escritos por él. La `gl_pipeline` existe pero es post-procesado sobre
un quad de pantalla completa; el estudiante no la toca.

---

## 4. Lo que pides: gráficos, sonido, física, VFX, 3D, clima, día/noche, estaciones

Estado real de cada cosa, medido, con lo que costaría.

| Sistema | Estado medido | Falta |
|---|---|---|
| **Iluminación 2D** | `LightSystem` con 3 focos activos en Stage 0, gradientes cacheados, color e intensidad por foco | **Ambiente en 1.0: la luz no se ve.** Bajarlo a 0.35 la enciende. Coste: una línea + ajuste artístico |
| **Clima** | 5 climas (`clear`, `rain`, `snow`, `fog`, `storm`), leídos del TMX | Stage 0 usa `clear`. El sistema funciona; el contenido no lo usa |
| **Ciclo día/noche** | **No existe.** Cero coincidencias en todo el código | Es la pieza que más impacto visual daría por menos código: interpolar el color ambiente y el tinte del post-procesado sobre un reloj. ~200 líneas |
| **Estaciones** | **No existe** | Encima del ciclo día/noche es casi gratis: paleta + clima por defecto + partículas ambientales por estación |
| **Post-procesado / "3D"** | 7 shaders GLSL reales: bloom, corrección de color, viñeta, desenfoque de movimiento, iluminación, daltonismo, passthrough | **Cero activos en juego.** Encender bloom y viñeta cambia radicalmente el aspecto. Coste: horas |
| **Partículas** | Sistema vectorizado con núcleo numba, precalentado | 0 emisores en Stage 0 |
| **Audio** | 19 pistas, 49 efectos, música dinámica por capas, sonido posicional, crossfade de ambiente | Sin pruebas propias. Sin reverberación por zona |
| **Física** | Gravedad, `coyote time`, buffer de salto, salto de pared, dash, multiplicador de gravedad por escenario | Sólida para un plataformas. Sin ragdoll ni cuerpos rígidos, y *JUZGADO:* no los necesita |

### Sobre el 3D — la conversación que hay que tener

Aquí tengo que ser directo porque es una decisión que puede costarte el
proyecto.

Lo que tienes se llama "pipeline GL" pero **no es un motor 3D**. Es una cadena
de shaders de post-procesado sobre un quad de pantalla completa: dibuja el
juego 2D a una textura y le aplica efectos. Eso es exactamente lo que hacen
Hollow Knight u Ori, y es la razón de que se vean como se ven.

Hacer 3D real —geometría, cámara con perspectiva, iluminación por vértice o
por píxel— significa **sustituir el renderizador**. Y ahí es donde se rompe
todo lo demás: el valor pedagógico de este proyecto es que el estudiante
**puede leer el código de dibujado y entenderlo**. Un renderizador 3D en
Python o bien es lento o bien es una capa fina sobre ModernGL que el
estudiante no puede leer.

*JUZGADO, y con convicción:* el "2.5D" que quieres —profundidad, parallax,
iluminación volumétrica, niebla, capas— **se consigue en 2D con el pipeline
que ya tienes**. SOTN es 2D puro. Ori es 2D. Hollow Knight es 2D. Lo que hace
que se vean tridimensionales es el arte y las capas, no la geometría.

**Mi recomendación:** no toques el renderizador. Enciende lo que ya tienes.

---

## 5. Plan concreto, ordenado por retorno

### Fase 1 — Encender lo que ya existe (1–2 semanas)

Nada de esto es ingeniería nueva. Es configuración y contenido.

1. Bajar el brillo ambiente a ~0,35 y colocar focos en el TMX. La iluminación
   se enciende de golpe.
2. Activar bloom + viñeta en el post-procesado. Coste: horas. Impacto visual:
   el mayor de toda la lista.
3. Poner `climate` distinto de `clear` en al menos una zona de Stage 0.
4. Emisores de partículas ambientales por zona (polvo, esporas, ceniza).
5. Estelas en el dash y en los ataques del jefe.

*JUZGADO: al terminar la fase 1, el juego se ve como otro juego, y el
estudiante por fin ve las capacidades que estudia.*

### Fase 2 — Lo que falta de verdad (3–4 semanas)

6. **Ciclo día/noche** como propiedad de TMX + reloj de juego. Interpola color
   ambiente, intensidad de focos y tinte del post-procesado.
7. **Estaciones** encima del ciclo: paleta, clima por defecto, partículas.
8. **Sobel y Canny a mano** junto a la versión de OpenCV, con comparación de
   tiempos en pantalla. Convierte dos laboratorios en dos lecciones.
9. **Conectar `level_metrics` al calificador** para que puntúe diseño y no sólo
   estructura.
10. Pruebas para los 12 sistemas huérfanos.

### Fase 3 — Producción docente (2–3 semanas)

11. i18n con `gettext`, español por defecto.
12. Traducir los 12 documentos que el estudiante lee.
13. Ejecutable con PyInstaller.
14. Previsualizador de TMX: renderiza el mapa sin lanzar el juego. Cierra el
    ciclo de realimentación del estudiante, que hoy está abierto.

---

## 6. ¿Podemos hacer un Castlevania mejor que Symphony of the Night?

Te debo una respuesta directa, no diplomática.

**No. No con este equipo, este calendario y este propósito.** Y las razones no
son técnicas, que es justo lo que hace la respuesta útil.

### Los números — MEDIDO frente a datos públicos de SOTN

| | Legacy of InFest | Symphony of the Night |
|---|---|---|
| Escenarios jugables | **2** | ~20 áreas interconectadas |
| Jefes | **1** | 20+ |
| Clases de enemigo | **8** | ~140 |
| Sprites PNG | **78** | miles de fotogramas dibujados a mano |
| Pistas musicales | **19** | 40+, de Michiru Yamane, con orquesta |
| Equipo | tú + estudiantes | ~20–30 personas, ~2 años |

La distancia no está en el motor. **Está en el arte.** Lo que hace a SOTN
memorable treinta años después es el trabajo de Ayami Kojima, la animación
cuadro a cuadro y la banda sonora de Yamane. Eso no se compensa con
arquitectura: se compensa con años-persona de artistas.

### Lo que sí es alcanzable, y creo que vale más

**Un metroidvania de 6–8 zonas, visualmente coherente, con iluminación
dinámica, clima, ciclo día/noche y post-procesado, construido íntegramente por
estudiantes a lo largo de varios semestres.** Eso está a tu alcance con el
motor que ya tienes, y es un objetivo que:

- se puede terminar,
- acumula: cada promoción añade zonas al mismo mundo,
- y produce algo que un estudiante puede enseñar en una entrevista.

*JUZGADO:* comparar tu proyecto con SOTN es comparar un programa docente con
el producto de un estudio. Tu ventaja competitiva no es superar a Konami. Es
que **casi ningún curso universitario de gráficas produce un juego jugable de
verdad**, y el tuyo puede. Eso ya es raro, y es defendible.

### Lo que sí puedes superar a SOTN

- **Accesibilidad:** ya tienes un shader de daltonismo y subtítulos. SOTN no
  tenía nada.
- **Claridad de código:** SOTN era ensamblador de PlayStation. El tuyo se lee.
- **Herramientas:** validación automática, calificación, métricas de diseño.

---

## 7. Lo que yo haría el lunes

Por orden, y con la razón:

1. **Encender la iluminación y el bloom.** Media jornada. Es lo único de esta
   lista que cambia cómo se siente el proyecto para todos —estudiantes,
   profesor, y tú— y hace visible todo lo que ya construiste.
2. **Conectar `level_metrics` al calificador.** Dos días. Es lo que separa
   "califico si pusieron los objetos" de "califico si diseñaron un nivel".
3. **Sobel y Canny a mano.** Dos días. Convierte la Unidad VII de demostración
   en enseñanza.
4. **i18n.** Una semana. Después de esto ya no hay excusa de idioma.

Lo demás puede esperar al siguiente semestre.
