# Datasets del curso

Nada de esto está versionado. Todo se **genera**:

```bash
python computer-vision-course/scripts/build_datasets.py
```

y se comprueba que la generación es reproducible:

```bash
python computer-vision-course/scripts/build_datasets.py --check
```

Es el mismo criterio que `scripts/train_reference_model.py` del motor: se
distribuyen el guion y la fuente, no el resultado. Un dataset commiteado pesa,
se desincroniza del código que lo produjo, y nadie puede reconstruir cómo se
hizo.

`MANIFIESTO.json` guarda el hash SHA-256 (16 hex) de cada fichero. `--check`
regenera todo en un directorio temporal y compara. Medido: **519 ficheros,
hashes idénticos**.

---

## Qué hay

### `engine_sprites/` — D2a · 385 imágenes, 3 clases

Fotogramas recortados de las hojas de animación de `assets/sprites/`,
etiquetados por la carpeta de la que salen.

| Clase | Ejemplos |
|---|---|
| `player` | 50 |
| `enemies` | 116 |
| `bosses` | 219 |

**Procedencia:** recursos del propio repositorio. **Licencia:** la del
repositorio.

Es el dataset del contexto *videojuego* de las Clases 3 y 4. Tres cosas que hay
que saber antes de usarlo, y que el material aprovecha en vez de esconder:

1. **Está desbalanceado** (219 contra 50). Un clasificador que diga siempre
   «boss» acierta el 57 % sin haber aprendido nada. Es el ejemplo de la Clase 4
   sobre por qué la *accuracy* sola no vale.
2. **Los PNG son RGBA con transparencia.** `cv2.imread(..., IMREAD_COLOR)`
   descarta el canal alfa y convierte lo transparente en **negro**, lo cual
   desplaza el histograma y mete un pico enorme en 0. Es el experimento de la
   Clase 1 («¿por qué el histograma de un sprite miente?»), y en la Clase 4 hay
   que componer sobre un fondo conocido antes de extraer características.
3. **El tamaño del fotograma se deduce de la altura de la hoja**, no de la
   tabla `FRAME_SIZES` de `tools/export_individual_frames.py`, que está
   desactualizada — dice 48 px para los jefes y las hojas del Gavilán miden 40.
   Las 9 hojas cuyo ancho no es múltiplo exacto de la altura pierden el resto
   del último fotograma; siempre menos de un fotograma.
4. **Dos hojas comparten nombre**: `enemies/enemy_fly_zone1.png` (96×24) y
   `enemies/zone1/enemy_fly_zone1.png` (56×10). Sin desambiguar, la hoja
   anidada pisaría a la otra —medido: el manifiesto contaba 116 fotogramas de
   enemigo y enumeraba 112—. El generador marca la segunda con el nombre de
   su carpeta delante: `zone1_enemy_fly_zone1_*.png`, y las 116 quedan.

Los fotogramas con menos del 2 % de píxeles opacos se descartan: las hojas de
animación traen huecos, y un ejemplo vacío etiquetado como «boss» le enseña al
modelo que un rectángulo transparente es un jefe.

### `engine_frames/` — D2b · 12 capturas

Cuatro fotogramas de cada una de las tres escenas-laboratorio del motor,
tomadas con el juego realmente en marcha y sin abrir ninguna ventana
(`SDL_VIDEODRIVER=dummy`).

| Fichero | Unidad | Escena |
|---|---|---|
| `unidadVII_filter_*.png` | VII | `FilterDemoScene` |
| `unidadVIII_vision_*.png` | VIII | `VisionDemoScene` |
| `unidadIX_pattern_*.png` | IX | `PatternDemoScene` |

800×600 RGB, que es la resolución interna real del motor (`settings.INTERNAL_WIDTH/HEIGHT`).

> **Nota sobre `PYTHONHASHSEED`.** El guion se rearranca con `PYTHONHASHSEED=0`.
> No es manía: `pattern_demo_scene._class_color` usa `hash(label)` para elegir
> el color de cada clase, y Python aleatoriza el hash de cadenas por proceso,
> así que sin fijarlo las capturas de la Unidad IX cambian de color en cada
> ejecución. Está anotado como defecto del motor, aparte de este curso.

### `synthetic_parts/` — D3 · 120 piezas + 1 imagen de watershed

Piezas industriales generadas con semilla fija (`20260805`), con verdad-terreno
exacta en `verdad_terreno.csv`.

| Clase | Ejemplos |
|---|---|
| `OK` | 72 |
| `NO_OK` | 48 |

`verdad_terreno.csv` trae por pieza: `fichero`, `clase`, `defecto`, `forma`,
la caja `bbox_f0/c0/f1/c1` y `area_verdadera`.

Los tres modos de fallo se eligieron porque cada uno cae con una técnica
distinta, y esa es la lección:

| Defecto | Se detecta con | Clase |
|---|---|---|
| `mota` | umbral simple | 3 |
| `grieta` | detección de bordes | 2 |
| `deformacion` | **características geométricas** (solidez, circularidad) | 3 y 4 |

La deformación no cambia el histograma: la pieza sigue igual de clara. Sólo se
ve midiendo la forma, y es lo que justifica todo el bloque de extracción de
características.

`piezas_en_contacto.png` son cinco círculos que se solapan. Un umbral —por
bueno que sea— produce **una sola región conexa**, así que
`connected_components` cuenta 1 donde hay 5. Es el ejemplo central del
watershed de la Clase 3, y hay una prueba que verifica que efectivamente se
tocan: si dejaran de tocarse, el ejercicio perdería el sentido sin que nadie se
enterara.

**Procedencia:** generado. **Licencia:** sin restricción.

---

## Lo que hay que decirle al estudiante

Un dataset sintético **no sustituye** a imágenes reales. Aquí el ruido es
gaussiano y homogéneo, la iluminación es uniforme y los defectos tienen tres
formas. Un sistema entrenado sólo con esto se estrella el primer día en una
planta.

Sirve para aprender el método y para tres cosas que ninguna descarga da:
verdad-terreno exacta, reproducibilidad bit a bit en las treinta máquinas del
aula, y control del eje de dificultad — se sube el ruido y se ve caer la
*accuracy*, que es el experimento de la Clase 4.
