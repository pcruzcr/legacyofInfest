# Cajas de colisión, y las tres deudas de la fase 5

**Fecha:** 31 de julio de 2026
**Antecedente:** `56_FASE_5_ECS_Y_MECANICAS.md`, que dejó tres deudas escritas.

---

## AUD-108 — diez de doce enemigos tenían la caja de daño fuera del cuerpo

### Lo que se encontró midiendo

`EnemyBase._build_hurtbox` devuelve coordenadas locales que `_update_rects` suma
a la posición. Diez de los doce cuerpos distintos del bestiario declaraban un
**desplazamiento sin encoger el tamaño**:

```
EnemyWalker:  cuerpo 24 × 28   →   _build_hurtbox() = Rect(4, 2, 24, 28)
```

Eso no es una caja ajustada al cuerpo: es **el cuerpo entero movido 4 px a la
derecha y 2 hacia abajo**. Medido sobre el bestiario completo:

| enemigo | cuerpo | hurtbox en mundo | desalineación |
|---|---|---|---|
| Walker | (100, 72, 24, 28) | (104, 74, 24, 28) | izq +4, der +4 |
| Flying | (101, 104, 20, 14) | (107, 108, 20, 14) | izq +6, der +6 |
| Shooter | (100, 76, 16, 24) | (104, 78, **24, 30**) | izq +4, **der +12** |
| Charger | (100, 76, 28, 24) | (104, 78, 28, 24) | izq +4, der +4 |
| Archer | (100, 72, 16, 28) | (102, 76, 16, 28) | izq +2, arr +4 |

### Qué se sentía al jugar

En un `Flying` de 20 px de ancho la caja está 6 px a la derecha: **el 30 % de su
cuerpo visible no se podía golpear** por la izquierda, y había 6 px de aire a su
derecha que sí golpeaban. Contra un `Shooter` la caja sobresalía **12 px**:
recibías daño de un enemigo que no estaba ahí.

Y como **todos** los desplazamientos iban hacia la derecha, atacar por la
izquierda era sistemáticamente más difícil. En todo el bestiario. En los catorce
escenarios. Es la clase de cosa que un estudiante siente y no sabe nombrar.

### Cómo se supo cuál era la intención

El jugador lo hacía bien desde el principio:

```python
return pygame.Rect(self.rect.x, self.rect.y + off_y, self.rect.width, h)
#                  ↑ misma x       ↑ sólo recorte vertical  ↑ misma anchura
```

### El arreglo, y por qué en un solo sitio

`EnemyBase.caja_ajustada(margen_x, margen_y)` calcula el rectángulo **a partir
del cuerpo** en vez de escribirlo a mano, así que el margen es un margen de
verdad y no puede convertirse en un desplazamiento por descuido. Los siete
ficheros del bestiario declaran ahora su margen y el cuerpo decide dónde cae la
caja.

`tests/test_cajas_de_colision.py` fija la invariante: ninguna caja puede salirse
del cuerpo, ninguna puede estar vacía, ninguna puede cubrir menos del 40 % —un
enemigo que parece invulnerable— y todas tienen que estar centradas
horizontalmente. Vale para los 30 enemigos y para los que registren los
estudiantes.

### Lo que se midió y no hizo falta tocar

Conviene decirlo, porque «mejorar las colisiones» invita a tocar cosas que
funcionan:

* **Tunelado.** El reloj ya limita `dt` a 0,05 s (`MAX_FRAME_TIME`) y la
  velocidad máxima del jugador es 200 px/s en dash y 500 en caída. Son 25 px por
  fotograma en el peor caso, contra un cuerpo de 20 × 32: no atraviesa
  geometría. Se comprobó a 200, 600, 1200, 2400 y 4800 px/s; sólo tunela a
  partir de 2400, que es inalcanzable.
* **Broadphase.** El escenario con más geometría tiene **27 rectángulos** de
  colisión. Un índice espacial costaría más de lo que ahorra.
* **La hurtbox del jugador.** Ya era correcta.

---

## Deuda 1 — el jugador es ahora una entidad del mundo

### Lo que decía la deuda

> `StageScene._mundo_ecs_paso` llama a los sistemas a mano y en orden explícito
> en vez de usar el `Planificador`, porque el jugador es una fachada y tendría
> que entrar y salir del mundo cada fotograma.

### Por qué era así, y qué lo desbloqueó

Los dos sistemas de sigilo recibían el rectángulo del jugador por parámetro:

```python
sistema_conos_de_vision(mundo, dt, rect_del_jugador)
```

Con una firma distinta a `Sistema = Callable[[World, float], None]` no cabían en
el planificador, así que la escena tenía que llamar a los once a mano, en orden,
sin equivocarse.

La pieza que faltaba era un componente vacío: **`EsJugador`**. Con una marca, el
sistema lo busca él (`mundo.con(EsJugador, Transform)`), la firma vuelve a ser
uniforme, y `_mundo_ecs_paso` desaparece sustituida por
`planificador.ejecutar(mundo, dt)`.

### Lo que se arregló de paso

Al meter al jugador entraron también los enemigos, y eso corrigió una rareza
real: **el viento y las corrientes no los empujaban**, porque no estaban en el
mundo. Un nivel con viento tenía viento para uno y calma para todo lo demás.

---

## Deuda 2 — `Salud`, resuelta al revés de como estaba previsto

### Lo que decía la deuda

> `Salud` está duplicada con `current_health` de `EnemyBase`, y se sincroniza. El
> día que ninguna entrega dependa de `current_health`, el componente pasa a ser
> la única verdad.

**Ese día no iba a llegar.** Hay **48 referencias** a `current_health` y
`max_health` en el código de los estudiantes, con escrituras incluidas
(`boss.current_health = boss.phase_max_health` en Paburu). Esperar a que
desaparezcan es esperar a reescribir su trabajo.

### La solución

La misma que `Transform`: el componente es una **vista** sobre el dueño.
`current_health` sigue siendo el atributo normal de siempre —su código no cambia
y no paga indirección— y `Salud` lee de ahí. No hay dos copias porque no hay
copia: hay un dato y una ventana a él.

`sincronizar_salud` queda como función vacía, y no se borra: alguna entrega
podría llamarla, y romperles el código por una mejora interna nuestra sería
desproporcionado.

> La pregunta correcta no era «¿cuándo puedo borrar la otra copia?» sino «¿por
> qué hay dos?».

---

## Deuda 3 — el laboratorio de mecánicas

### Lo que decía la deuda

> Ninguna entrega usa todavía las mecánicas nuevas. Están en el motor y en la
> guía del estudiante; lo que falta es un escenario de referencia que las
> enseñe.

Es la misma forma de fallo que este proyecto lleva un mes cazando, un paso más
allá: aquí el camino existe, está abierto y documentado, y **no hay nadie
andándolo**. Nadie adopta una mecánica leyendo su tabla de propiedades; la
adopta viéndola funcionar y copiando el objeto en Tiled.

### `stage_mecanicas` — siete salas, once mecánicas

| Sala | Mecánica | Qué enseña |
|---|---|---|
| 1 | `WindZone` | el viento empuja mientras saltas |
| 2 | `Conveyor` | el suelo se mueve bajo los pies |
| 3 | `MovingPlatform` ×2 | la plataforma te lleva encima |
| 4 | `RhythmBlock` ×4 | aparecen a compás, con desfase |
| 5 | `LaserZone` ×5 + `SinkingPlatform` | cascada, no muro |
| 6 | `WaterZone` | bajo el agua se acaba el aire |
| 7 | `Guard` ×2 + `Stalker` | cono de visión, alerta y acoso |

Una mecánica por sala, en un sitio donde equivocarse no mata, y la siguiente
combina con la anterior. Entre sala y sala hay una repisa de descanso: son las
«válvulas de escape» que el dossier del Top 200 menciona en cada nivel bueno de
la historia, y sin ellas siete mecánicas seguidas se leen como una sola cuesta
arriba.

**La clase no tiene lógica propia.** No sobreescribe `update` ni `draw`, y hay
una prueba que lo vigila: si hiciera falta código para que las mecánicas
funcionen, no serían usables desde Tiled y el escenario no demostraría lo que
pretende. Un estudiante puede reproducir cualquier sala sin escribir una línea
de Python.

El TMX se genera con `tools/generate_stage_mecanicas.py`, igual que stage0: un
mapa escrito a mano son ocho mil números en CSV que nadie puede revisar. Hay una
prueba que comprueba que el fichero del repositorio coincide con lo que produce
su generador, para que nadie edite uno y deje el otro viejo.

### Un hallazgo del camino

`visible` es un **nombre reservado en Tiled**. Declarar una propiedad así hace
que pytmx rechace el mapa entero con «Reserved names and duplicate names are not
allowed» — sin decir cuál. Las propiedades del bloque rítmico se llaman
`visible_seg` y `oculto_seg` por eso, y queda anotado en el cargador para el
siguiente que lo intente.

---

## Verificación

```
las 15 escenas cargan y dibujan ......................... 15/15
validador TMX ........................................... 15/16
  (el que falla es la entrega de Saúl, y es su nota)
pruebas nuevas de esta tanda ............................ 21
  test_cajas_de_colision.py .............................  5
  test_ecs.py (deudas 1, 2 y 3) ......................... 16
ruff sobre motor, framework, pruebas, scripts y tools ... limpio
```

**Verificación por mutación:** devolver el margen como desplazamiento en vez de
centrar la caja deja roja la prueba de simetría izquierda/derecha.

---

## Lo que queda

Ninguna de las tres deudas de la fase 5 sigue abierta. Lo que hay ahora es
trabajo nuevo, no deuda:

1. **Ninguna entrega usa aún el laboratorio como referencia** — pero ahora
   existe algo que referenciar, que era el bloqueo.
2. **`stage2_1_oficinas` sigue sin pasar el validador** por tres propiedades de
   mapa. Es la nota de un estudiante, no un defecto del motor.
3. **La traducción de los 12 documentos del estudiante** sigue pendiente desde
   la conversación del jueves.
