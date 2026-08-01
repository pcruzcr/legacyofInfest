---
document_id: "LOI-AUDIT-AAA-61"
title: "Auditoría AAA — agosto 2026"
tags: ["auditoria", "calidad", "AAA"]
source: "docs/61_AUDITORIA_AAA_2026-08.md"
date_processed: "2026-08-01"
---

# Auditoría AAA — agosto de 2026

**Alcance:** el repositorio entero. Arquitectura, código, jugabilidad, UI/UX,
gráficos, audio, rendimiento, documentación, localización, QA y seguridad.
**Método:** medir antes de opinar. Toda afirmación de este informe tiene un
comando detrás.

---

## 1. Resumen ejecutivo

Seis defectos nuevos, dos de ellos con efecto visible en la partida. Todos
corregidos, todos con prueba que falla sin el arreglo.

| Ref | Sev. | Qué era |
|---|---|---|
| **AUD-118** | Alta | Dos sistemas escribían `time_scale` sin saber el uno del otro. Golpear a un enemigo durante la cámara lenta daba `0,35 → 0,0 → 1,0`: **un fotograma a velocidad completa en el instante del impacto** |
| **AUD-119** | Alta | El hit-stop congelaba también los bloques rítmicos, los láseres y las plataformas. Golpear junto a un láser lo **detenía** |
| **AUD-120** | Media | `pytest tests/test_clock.py` a secas daba cuatro errores; con cualquier otro fichero delante, pasaba |
| **AUD-121** | — | Auditoría de datos hostiles al guardado: **sin defectos**. Fijado con 27 pruebas |
| **AUD-122** | Media | La pareja bilingüe del README se había separado: 1.333 pruebas en español, 640 en inglés, 2.020 reales. Los dos mal |
| **AUD-123** | Baja | Tres componentes ECS que escribí en la fase 5 con **cero usos** en todo el árbol |

Lo que **no** se encontró, y también es un resultado: sin `eval`, sin `exec`,
sin `os.system`, sin `shell=True`. `pickle` sólo en la ruta del modelo de ML,
con aviso explícito y una prueba que lo vigila. Ningún TODO bloqueante en el
motor. Ninguna fuga de memoria.

---

## 2. Arquitectura — 88/100

### El hallazgo estructural: un número con dos dueños

`time_scale` era un `float` público. Lo escribían el hit-stop de
`CollisionSystem` y la cámara lenta de `TiempoBala`, y **cada uno restauraba
1,0 al terminar**. Ese 1,0 es la afirmación «nadie más ha tocado esto».

La señal estaba a la vista y no la había leído nadie: en el código había **dos
comentarios largos**, uno en cada sistema, explicando quién era el dueño del
número. Un invariante que necesita que dos módulos se pongan de acuerdo por
comentario no es disciplina pendiente: es un defecto de diseño esperando.

La cura no fue un tercer parche sino quitar el dueño. Ahora cada efecto
registra su factor **con su nombre** y la escala efectiva es el producto:

```python
reloj.escalar("hitstop", 0.0)      # el golpe congela
reloj.escalar("tiempo_bala", 0.35) # y la cámara lenta sigue pedida
reloj.restaurar("hitstop")         # -> 0.35, no 1.0
```

Componer es asociativo y conmutativo, así que ningún par de efectos futuros
podrá pisarse. Añadir un tercero —una ralentización de jefe, una pausa de
cinemática— ya no exige leer los otros dos.

### El corolario: tres relojes, no dos

El planificador ECS recibía el `dt` escalado, de modo que los 50 ms de hit-stop
de **cada golpe** paraban la maquinaria del nivel. Dos consecuencias:

* **Exploit reproducible:** golpear a un enemigo junto a un láser detiene el
  láser.
* **Desincronización acumulada:** en un nivel a compás, cada golpe atrasa los
  bloques respecto a la música y nada lo corrige nunca.

El hit-stop es *presentación*: congela a los implicados para dar peso al golpe.
La cámara lenta es *simulación*: cambia el tiempo del mundo. Confundirlas es el
error, y ahora el motor las distingue con un tercer delta:

| Delta | Escala con | Para |
|---|---|---|
| `dt` | todo | jugador, enemigos, proyectiles |
| `dt_mundo` | todo **menos** el hit-stop | bloques rítmicos, láseres, plataformas |
| `unscaled_dt` | nada | UI, transiciones, el propio contador de hit-stop |

### Compatibilidad: las 26 entregas siguen funcionando

Las clases de escenario de los estudiantes traen dobles de reloj con sólo el
atributo `time_scale`. Los dos sistemas comprueban con `getattr` si el reloj
sabe componer y, si no, escriben como antes. Romper las pruebas de un
estudiante con un cambio interno del motor es exactamente lo que este proyecto
lleva un mes evitando.

### AUD-123 — la vara de medir, aplicada a mí

Un análisis de alcanzabilidad sobre todo el árbol —el mismo que este mes
encontró seis huérfanos en código ajeno— dio **cero usos** a `Gravedad`,
`Renderizable` y `Etiqueta`, tres componentes que escribí en la fase 5 «porque
un ECS los tiene». Ni un sistema, ni una escena, ni una prueba; sólo estaban
exportados en `__init__.py`, que es la forma más fácil de que algo parezca
vivo.

Retirados. Conectarlos exigiría reescribir la física y el dibujado para
resolver un problema que nadie tiene. Es el criterio que apliqué a
`transitions.py` y al código de los estudiantes; aplicarlo sólo hacia fuera
sería una vara de medir doble.

**Quedan dos huérfanos, declarados y no resueltos:** `DialogueAction` del
sistema de cutscenes —un estudiante escribió literalmente «no se usa el
`DialogueAction` del motor» y se hizo el suyo, lo que sugiere que o no sirve o
no se encuentra— y `GhostData` del modo speedrun. Los dos necesitan una
decisión de producto antes que de código.

---

## 3. Revisión de código — 90/100

| Comprobación | Resultado |
|---|---|
| `ruff` sobre lo que mantiene el equipo docente | limpio |
| `eval` / `exec` / `os.system` / `shell=True` | **ninguno** |
| `pickle` | sólo en el modelo de ML, con aviso y prueba |
| TODO/FIXME bloqueantes en motor y framework | **ninguno** |
| Clases sin ningún uso | 3 retiradas, 2 declaradas |

Los 164 avisos de estilo restantes están **todos** en `src/stages/`, el código
de los estudiantes. No se corrigen —es su código y su nota— y el CI los excluye
a propósito: un equipo que se acostumbra a un CI en rojo deja de mirarlo.

---

## 4. Jugabilidad — 86/100

El defecto de esta pasada era de *game feel* puro: un tirón de un fotograma
justo en el impacto, que es el momento en que el jugador está mirando. Este
tipo de fallo no aparece en ninguna prueba de corrección porque nada estaba
«mal»; simplemente se sentía barato.

Sin cambios en el diseño. Lo pendiente sigue siendo lo declarado en
`docs/60`: de las once mecánicas de la fase 5, stage 0 usa cuatro; las otras
siete viven en `stage_mecanicas`.

---

## 5. UI/UX — 84/100

Sin hallazgos nuevos. El kit de tema y widgets, el contraste WCAG medido en
8,9:1 y las tres señales redundantes de foco siguen en su sitio y con pruebas.

---

## 6. Gráficos — 80/100

Del perfilado de 600 fotogramas de stage 0:

| Fase | Coste | % del fotograma |
|---|---|---|
| Dibujado total | 6,26 ms | **63 %** |
| `blit` (58 por fotograma) | 2,93 ms | 29 % |
| Post-procesado | 2,18 ms | 22 % |
| — de ellos, bloom | 1,55 ms | 15 % |
| Actualización total | 2,08 ms | 21 % |

El bloom cuesta el 15 % del fotograma. Es una decisión legítima —la atmósfera
es material de la Unidad V— pero conviene saber su precio antes de subirlo.

---

## 7. Audio — 78/100

Sin hallazgos nuevos. La degradación es correcta: si falta un `.ogg`, se
registra el aviso y ese sonido se calla en vez de tumbar el nivel.

**Deuda declarada:** no hay reloj musical. Todo lo «rítmico» acumula su propio
temporizador en segundos y nada está atado a la posición de la pista. AUD-119
era el primer obstáculo para arreglarlo, y ya no está.

---

## 8. Rendimiento — 82/100

Medido en el entorno de auditoría (2 núcleos, vídeo por software), que es
**pesimista** respecto a la máquina de un estudiante:

```
mediana  6,9 – 10,8 ms      p95  9,9 – 15,0 ms
p99     14,8 – 18,0 ms      presupuesto 16,67 ms
```

La horquilla no es imprecisión mía: dos ejecuciones idénticas del mismo código
dieron 6,87 y 10,81 ms de mediana. **En esta máquina no se puede atribuir el
p99 con honestidad**, y decirlo es más útil que inventar una causa. Ya me pasó
este mes con un benchmark que me hizo creer que el ECS costaba un 63 % cuando
lo que medía eran importaciones perezosas de scipy.

Lo que sí es estable son las **proporciones** del perfil (§6) y la memoria:

```
bloque 1:  53,4 KiB    bloque 2: 176,4 KiB (+123)    bloque 3: 186,2 KiB (+10)
```

El crecimiento se frena. Es caché caliente, no fuga.

Probé `gc.freeze()` con umbrales altos y **no mejoró** —salió peor dentro del
ruido—. Lo dejo escrito para que nadie repita el experimento creyendo que es
fruta al alcance de la mano.

---

## 9. Documentación — 87/100

95 documentos. La guía completa del motor (`docs/60`) tiene 22 pruebas que
comparan sus cifras con el código en cada ejecución.

**Hallazgo:** `README.md` decía 1.333 pruebas, `README.en.md` decía 640, y hay
**2.020**. Los dos mal, cada uno a su manera, y ninguno lo detectaba nadie.
Corregidos y vigilados: ahora una prueba recuenta con
`pytest --collect-only` y falla si el README se desvía más de un 5 %.

---

## 10. Localización — 72/100

### La medición

| Idioma | Documentos |
|---|---|
| Sólo español | 28 |
| Sólo inglés | 66 |
| Mixto | 1 |
| **Genuinamente bilingües** | **2** |

Los catálogos de interfaz están en orden: 2.148 literales, `es` y `en`
completos, sin huecos reales.

### Por qué no se han traducido los 95

El encargo pedía toda la documentación en ambos idiomas. Lo he considerado y
**recomiendo no hacerlo**, con el argumento que esta misma auditoría acaba de
demostrar: la pareja bilingüe que ya existía —el README— llevaba meses
mintiendo por los dos lados. Traducir 95 documentos da 190 ficheros que
mantener sincronizados, y el modo de fallo dominante de este proyecto, medido
cuatro veces este mes, es exactamente que un documento se separe de la
realidad. Duplicar la superficie duplica el riesgo, y una traducción rancia es
peor que ninguna porque hace creer que hay revisión donde no la hay.

La política que sí implemento:

* **Bilingüe obligatorio:** la puerta de entrada (README) y los informes de
  auditoría publicables. Es lo que lee alguien de fuera.
* **Español:** el material del curso. Los estudiantes son hispanohablantes.
* **Inglés:** las especificaciones heredadas, hasta que alguien las pida en
  español.

Y `tests/test_documentacion_bilingue.py` hace cumplir que **lo que está en dos
idiomas coincida**: los dos lados existen, se enlazan mutuamente y no afirman
cifras distintas. Los bloques de código quedan fuera de la comparación, porque
un volcado de consola del motor sale en español y exigir que el documento
inglés lo reprodujera sería documentar una mentira para satisfacer una prueba.

Aplicándolo se encontró un segundo desajuste: a `AUDIT_2026-07.en.md` le
faltaba la **sección 18 entera**. Traducida.

---

## 11. QA — 89/100

**2.020 pruebas.** 49 nuevas en esta pasada.

| Fichero | Pruebas | Qué cubre |
|---|---|---|
| `test_composicion_del_tiempo.py` | 15 | AUD-118, AUD-119, AUD-120 |
| `test_datos_hostiles.py` | 27 | 13 entradas hostiles, límites de ranura, travesía |
| `test_documentacion_bilingue.py` | 7 | AUD-122 |

Dos decisiones de método que conviene dejar escritas:

**Ninguna prueba vacía.** La comprobación de aislamiento de la suite se escribió
primero con `__wrapped__` sobre una fixture; si pytest dejara de exponer ese
atributo, la expresión evaluaría a `None` y la prueba pasaría **sin comprobar
nada**. Se cambió por ejecutar `pytest` de verdad en un subproceso. Cuesta un
segundo y no puede mentir.

**Se prueba lo que funciona, no sólo lo que falló.** Las 27 pruebas de datos
hostiles no corrigen ningún defecto: el guardado ya era correcto. Una suite que
sólo contiene regresiones de defectos pasados deja sin vigilancia justo el
código que alguien optimizará dentro de seis meses sin saber qué garantizaba.

---

## 12. Seguridad — 92/100

| Vector | Estado |
|---|---|
| Ejecución de código (`eval`, `exec`, `__import__`) | ninguno |
| Shell (`os.system`, `shell=True`) | ninguno |
| Deserialización | `pickle` sólo en el modelo ML, con aviso y prueba |
| Travesía de rutas desde el guardado | **no existe**: `stage_id` sólo se compara y se muestra; el que arma rutas de módulo sale de `STAGE_ORDER`, una lista fija en el código |
| Guardado corrupto | 13 entradas hostiles, ninguna rompe nada |

---

## 13. Puntuación

| Categoría | Nota |
|---|---|
| Arquitectura | 88 |
| Código | 90 |
| Jugabilidad | 86 |
| UI/UX | 84 |
| Gráficos | 80 |
| Audio | 78 |
| Rendimiento | 82 |
| Documentación | 87 |
| Localización | 72 |
| QA | 89 |
| Seguridad | 92 |
| **Global** | **84** |

**Madurez: producción para su propósito.** Es un motor docente que sostiene un
curso con 26 entregas integradas, 2.020 pruebas y validadores en CI. No es un
producto comercial y no pretende serlo; medido contra lo que dice ser, está
listo.

Las dos notas bajas son honestas. Localización (72) porque hay una decisión de
producto pendiente que no me corresponde tomar. Audio (78) porque falta el
reloj musical, que es una fase de trabajo, no un defecto.

---

## 14. Próximas prioridades

1. **Reloj musical (F6).** AUD-119 quitó el obstáculo. Ver el análisis de
   niveles rítmicos.
2. **Decidir sobre `DialogueAction` y `GhostData`.** O se enchufan o se van; un
   estudiante ya rodeó el primero.
3. **Los 15 tipos de objeto que ningún mapa usa**, diez de ellos enemigos.
4. **Traducir los 12 documentos de estudiantes**, deuda declarada de julio.
5. **`stage2_1_oficinas`** sigue sin validar: es la nota de Saúl, no un defecto
   del motor.
