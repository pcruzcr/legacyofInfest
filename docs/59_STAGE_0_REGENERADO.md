# 59 — Stage 0 regenerado, y tres defectos más del calificador

**Fecha:** 31 de julio de 2026
**Alcance:** cerrar las cuatro recomendaciones de `58_VALIDACION_DE_SISTEMAS.md`
y volver a generar el escenario de referencia.

---

## Resumen

| | Antes | Ahora |
|---|---|---|
| Stage 0 en el calificador | 121/130 (93,1 %) | **130/130 (100 %)** |
| Objetos en el mapa | 100, de 22 tipos | **122, de 29 tipos** |
| Mecánicas de la fase 5 usadas en stage 0 | 0 de 11 | **4** |
| Objetos interactivos de F4.1 usados | 0 de 4 | **4 de 4** |
| Coleccionables | 0 | **5** |
| Obstáculos sólidos interiores | 0 | **2** |
| Módulos con cero usos en el repositorio | 1 (`transitions.py`) | **0** |
| Pruebas de diálogo y cutscenes | 0 | **16** |

Cuatro defectos nuevos, tres de ellos en mis propias herramientas de calificar.

---

## 1. El generador de stage 0 y stage 0 llevaban meses divorciados

`tools/generate_stage0_tmx.py` declaraba un mapa de **240 × 14** baldosas. El
fichero que el juego carga mide **100 × 38**. Nadie recordaba cuál era el bueno,
y quien hubiera ejecutado el generador —lo obvio al leer «genera stage0.tmx»—
habría borrado el escenario de referencia del curso sin un aviso.

Esto ya lo habíamos previsto **para otro mapa**: `stage_mecanicas` tiene desde
la fase 5 una prueba que compara el `.tmx` del repositorio con lo que produce su
generador. Stage 0, que es el mapa que más importa, no la tenía.

El generador se reescribió **desde el fichero en producción** —sus ocho capas,
sus tipos de objeto, sus propiedades de mapa— y ahora hay dos pruebas:

```python
assert modulo.generar() == en_disco
assert (modulo.MW * modulo.TS, modulo.MH * modulo.TS) == stage.map_pixel_size
```

La segunda habría cazado los 240 × 14 sin leer una línea de código.

---

## 2. Lo que le faltaba a stage 0

El calificador señalaba dos cosas, ambas reales:

* **`design_pacing: 5/8`** — «el recorrido no tiene ningún salto exigente». El
  escenario del profesor **se recorría solo**, y es la misma métrica con la que
  se califica a los estudiantes. Predicar lo contrario de lo que se exige
  cuesta autoridad y se nota.
* **`collectibles: 5/10`** — ninguno. Tolerable en un tutorial, pero `Pickup`
  existe desde F4.1 y stage 0 es donde un estudiante va a mirar cómo se usa.

Y una carencia que el calificador no mide y que era la peor: de las **once
mecánicas** de la fase 5 y de los **cuatro objetos interactivos** de F4.1, el
prólogo no usaba **ninguno**. El escenario que enseña el motor no enseñaba la
mitad del motor.

### El trazado nuevo: siete zonas

```
A  moverse y saltar          sin peligro, y el primer obstáculo sólido
B  el primer enemigo         Walker en el camino, no a un lado
C  plataformas               + liana, y el primer salto exigente
D  combate variado           + llave, puerta cerrada y un muro de 3 baldosas
E  el foso                   + bloques rítmicos y pasarela: dos formas de cruzar
F  enemigos a distancia      + zona de viento
G  todo junto                + tirolesa y cofre
```

Nueve enemigos de seis tipos, cinco checkpoints, cinco coleccionables, cuatro
mensajes de tutorial. El foso tiene **dos soluciones** —saltarlo o cruzar por la
pasarela de arriba—, que es lo que separa un nivel de un pasillo.

### Los obstáculos, y una prueba que se saltaba en silencio

Stage 0 no tenía **ni una sola caja sólida interior**. Sus únicas colisiones
eran el suelo y los dos muros de cierre del mapa. Un escenario sin nada contra
lo que chocar no enseña la mitad más básica de la colisión —el eje horizontal—.

Lo delató la propia suite: `test_andar_contra_un_solido_detiene_al_jugador`
terminaba en `pytest.skip("no hay muros interiores contra los que chocar")`.
Verde en el informe, sin haber probado nada. Una prueba que se salta es una
prueba que no existe, y esa se saltaba desde que se escribió.

Ahora hay dos obstáculos, de 2 y 3 baldosas: el primero se salta desde parado,
el segundo obliga a aprovechar el impulso y guarda la llave de la zona D. Con
una prueba parametrizada que **conduce al jugador por encima de cada uno**,
porque poner cajas sólidas en el camino sin comprobar que se superan es la forma
de dejar un callejón sin salida en el escenario de referencia. La altura de
salto medida son 72 px; si alguien la baja, la prueba se pone roja aquí y no en
la partida de un estudiante.

---

## 3. AUD-113 — el 10/10 en metadatos era inalcanzable

```python
result["categories"]["metadata"] = {"score": meta_score * 3, "max": 10, ...}
```

Tres propiedades exigidas × 3 puntos = **9 sobre 10**. Nadie, en todo el curso,
podía completar esa casilla. El informe salía en amarillo —`[WARN] metadata:
9/10 — 3/3 props found`, que se contradice a sí mismo en la misma línea— y le
decía a cada estudiante que le faltaba algo cuando no le faltaba nada.

Corregido repartiendo el peso completo entre las propiedades que de verdad se
exigen, sea cual sea su número:

```python
puntos = round(RUBRIC["metadata"] * meta_score / total_props)
```

**Es el tercer defecto de este tipo este mes** (AUD-104, AUD-106, AUD-107,
AUD-110, AUD-112 y ahora AUD-113: seis en total). Todos en la misma dirección
—restar puntos por trabajo correcto— y todos con la misma causa: una constante
escrita a mano en la herramienta que no se derivaba de nada. La cura es siempre
la misma, preguntarle al motor en vez de recordar, y sigue habiendo sitios donde
no lo hago.

Las notas subieron; ninguna bajó. Están actualizadas en
`docs/entregables/NOTAS_EVALUACION_PRACTICA_I.md`.

---

## 4. AUD-111 — el sexto huérfano del mes

`src/engine/scene/transitions.py`: cinco clases (`FadeTransition`,
`WipeTransition`, `SlideTransition`, `CircleTransition` y su base), **cero usos**
en todo el repositorio, ni siquiera en pruebas. Competía por el nombre con
`scenes/transition_manager.py`, que es el que `SceneManager` instancia de verdad,
así que un estudiante que buscara «cómo hago una transición» encontraba el
muerto la mitad de las veces.

Retirado. El árbol de `03_ARCHITECTURE.md` seguía prometiéndolo, y quien lo
cazó fue `test_architecture_doc_matches_tree.py` —escrito en su día justo para
esto—. Funcionó.

Van seis huérfanos este mes: la iluminación que no iluminaba nada, las trece
demos que dibujaban en una esquina, el ataque definitivo cuyo medidor nadie
incrementaba, `SwimmingState`, `AirChaseState` y ahora este. El patrón no es
«código roto»: es **código correcto, probado en aislamiento, que nunca llega al
jugador**. La prueba unitaria no distingue entre un sistema conectado y uno que
no lo está; sólo la alcanzabilidad lo hace.

`FogOfWar`, `WaterEffect` y `BossRushMode` estaban en ese mismo estado y se
enchufaron por propiedades del TMX en vez de retirarse, porque los tres tienen
sitio en el curso.

---

## 5. Diálogo y cutscenes: 16 pruebas, y un defecto real

Ninguno de los dos sistemas tenía pruebas. Escribirlas encontró un fallo de
verdad en `FadeAction.draw`: al completarse, la acción **retornaba antes** de
dibujar el velo, de modo que un fundido a negro terminaba **des**fundido —un
fotograma de destello justo antes del corte, exactamente donde no se quiere—.

Corregido: un fundido de salida ahora termina opaco.

Dos de mis propias pruebas estaban mal antes de que lo estuviera el código: una
usaba un lienzo de 320 × 224 cuando `INTERNAL_HEIGHT` son 600, así que el
diálogo se dibujaba fuera de la superficie y yo acusaba al sistema. Conviene
recordarlo cuando una prueba nueva falla a la primera.

---

## 6. Verificación

| Comprobación | Resultado |
|---|---|
| `ruff check` sobre lo que mantiene el equipo docente | limpio |
| Validador de TMX | 15/16 (el fallo es `stage2_1_oficinas`, la entrega de Saúl) |
| Sincronía de dependencias | 15/15 |
| Stage 0 en el calificador | 130/130 |
| Los 16 mapas recalificados | ninguna nota bajó |
| Documentación ↔ árbol de ficheros | de acuerdo |

Nota sobre el 15/16: es la nota de un estudiante, no un fallo del motor. Su mapa
no declara las tres propiedades obligatorias. Está en su informe.

---

## 7. Lo que queda

* Traducir los 12 documentos de estudiantes que siguen en inglés.
* Colocar los **15 tipos de objeto que ningún mapa usa** —entre ellos diez
  enemigos del bestiario oficial—. Existir en el registro y no aparecer en
  ningún mapa es el mismo huérfano de la sección 4, con otra ropa.
* `stage_mecanicas` saca 98/130 con la rúbrica de niveles. Es un laboratorio y
  no un nivel, pero la diferencia conviene explicarla o corregirla.
