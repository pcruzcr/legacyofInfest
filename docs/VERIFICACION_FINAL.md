# Verificación final: qué está, qué falta, y qué nota

**Fecha:** 27 de julio de 2026 · **Método:** medición, no lectura
Cada número sale de un comando ejecutado hoy.

---

## 1. ¿Está todo implementado? — SÍ, y se puede comprobar

Se construyó `scripts/check_tmx_coverage.py` para responder a esta pregunta sin
opinar. Cruza tres cosas: las propiedades que el motor lee, los tipos de objeto
que reconoce, y lo que los mapas declaran de verdad.

```
El motor reconoce 16 propiedades de mapa y 42 tipos de objeto.

  assets/maps/stage0/stage0.tmx
    propiedades declaradas : 16/16  (100 %)
    tipos de objeto usados : 18
    propiedades de Light   : 6/6

  assets/maps/boss_venado/boss_venado.tmx
    propiedades declaradas : 14/16  (88 %)
    propiedades de Light   : 6/6

Todas las propiedades de mapa están demostradas en algún mapa.
```

### Lo que se corrigió al verificar

Stage 0 declaraba **11 de 16**. Las cinco que faltaban —`bloom`, `vignette`,
`ambient_fx`, `ambient_fx_rate`, `zone`— funcionaban por la tabla de respaldo
por zona, así que el juego se veía bien y **nadie lo habría notado**.

Y eso es exactamente el problema: el estudiante aprende abriendo `stage0.tmx`
en Tiled y copiando lo que ve. Una característica que el mapa de ejemplo no
declara existe sólo en la documentación, que es justo lo que no se lee.

Ahora hay una prueba que lo impide. Verificada por mutación: quitarle `bloom`
a stage0 pone la suite en rojo.

---

## 2. Cada característica, comprobada en ejecución

No basta con que la propiedad esté en el XML. Esto es lo que se midió cargando
Stage 0 de verdad y corriendo 180 fotogramas:

| Propiedad TMX | Valor declarado | Lo que hace el juego |
|---|---|---|
| `ambient_light` | 0.70 | ambiente aplicado **0,59** (modulado por hora y estación) |
| `bloom` | 0.18 | base **0,21** (+0,03 del tramo horario) |
| `vignette` | 0.30 | **0,30** |
| `climate` | `clear` | 0 partículas — decisión de diseño, no fallo |
| `ambient_fx` | `spores` ×14 | **27 partículas vivas** |
| `season` | `autumn` | tinte **(255, 209, 159)** |
| `start_hour` | 16.0 | reloj marca **16:06** y avanzando |
| `day_length` | 420 s | reloj **no congelado** |
| `zone` | 0 | — |
| `gravity_multiplier` | 1.0 | jugador a **1.0** |
| objetos `Light` | 9 | **10 focos activos** (los 9 + el del jugador) |
| `CameraLock` | 1 | cargado |
| `Checkpoint` | 4 | cargados |
| enemigos | 9 | cargados |
| `MessageTrigger_Once` | 6 | cargados |
| `HazardZone` / `DeathPit` | 1 / 1 | cargados |
| `NextTrigger` | sí | cargado |

Hay una prueba de cableado que verifica todo esto en cada ejecución de la
suite. No es una tabla que se pueda desfasar.

---

## 3. Estado medido del proyecto

| Medida | Valor |
|---|---|
| Pruebas | **1.507**, todas en verde |
| Archivos de prueba | 70 |
| ruff | limpio |
| Validador TMX | 2/2 |
| Validador de recursos | 0 errores, 0 avisos |
| Catálogos de idioma | en orden |
| Sincronía de dependencias | 15/15 |
| Stage 0, mediana por fotograma | **7,98 ms** (presupuesto 16,67) |
| p95 | 12,11 ms |
| Fotogramas fuera de presupuesto | **1 de 360** |

Con toda la atmósfera encendida —luz, bloom, viñeta, clima, partículas,
estelas, ciclo día/noche, estaciones— Stage 0 usa el **48 %** del presupuesto
de fotograma. La referencia del inicio de la sesión, sin nada de esto, era
8,11 ms.

---

## 4. Qué falta

Ordenado por lo que de verdad importa.

### Falta de contenido, no de motor

| Qué | Estado | Coste |
|---|---|---|
| **24 de 42 tipos de objeto no se usan en ningún mapa** | 18 son variantes de enemigo del bestiario (`WalkerGarza`, `FlyingBoa`...) que existen en código y no tienen escenario donde aparecer | contenido |
| **2 escenarios jugables** | Stage 0 y la arena del jefe | contenido |
| `MessageTrigger` y `Waypoint` | Los tipos existen; ningún mapa los usa (stage0 usa `MessageTrigger_Once`) | 1 hora |
| Stage 0 no demuestra el clima visualmente | Usa `clear`. La arena sí (`storm`) | decisión de diseño |

### Deuda técnica real

| Qué | Medido | Coste |
|---|---|---|
| `FilterDemoScene` a 7,8 ms de mediana | 47 % del presupuesto en una demo | 1 día |
| Traducción de los 12 documentos del estudiante | La maquinaria está; faltan las horas | 1–2 semanas |
| 25 cadenas de interfaz sin traducir al español, 34 al inglés | Se muestran tal cual, legibles | 2 horas |
| Stage 0: 2 plataformas sin ruta desde el spawn | Lo detecta el calificador | 30 min |
| Stage 0 sin `author` en los metadatos | Aviso del calificador | 1 min |
| `test_gameplay_integration` tarda ~50 s | 26 pruebas que construyen escenas completas | factura que crecerá |

### Lo que decidí no hacer, y por qué

- **No tocar el renderizador para hacer 3D.** Lo que hay es post-procesado
  sobre un quad, igual que Hollow Knight u Ori. Sustituirlo rompería lo único
  que hace valioso este proyecto: que el estudiante pueda leer el código de
  dibujado.
- **No usar `gettext`.** Exige herramientas externas, sus catálogos son
  binarios y no se revisan, y el caso de uso son dos idiomas.
- **No construir el `.exe` en la suite.** Tarda minutos. Sí se vigila la receta.

---

## 5. La nota

Contra el objetivo declarado —**un semestre con 30 estudiantes sin apagar
incendios**— y no contra un producto comercial.

| Área | Nota | Por qué |
|---|---|---|
| **Motor y framework** | 9 / 10 | 1.507 pruebas, ruff limpio, arquitectura legible. Baja de 10 por `FilterDemoScene` y porque quedan sistemas cuya cobertura es funcional pero no exhaustiva. |
| **Herramientas del profesor** | 9 / 10 | Calificar, exportar notas, detectar plagio, generar exámenes y realimentación. El calificador ya puntúa diseño. Falta rúbrica propia para arenas. |
| **Herramientas del estudiante** | 8,5 / 10 | Validador, previsualizador y plantilla honesta. El ciclo está cerrado. Falta un editor visual propio, pero Tiled es la decisión correcta. |
| **Configurable desde TMX** | **10 / 10** | 16 de 16 propiedades demostradas en el mapa de ejemplo, con prueba que lo vigila. |
| **Valor pedagógico** | 8,5 / 10 | Sobel y Canny a mano, ruido procedural propio, patrones de diseño visibles. Sube de 7 tras la Fase 2. Baja de 10 porque el pipeline gráfico moderno sigue fuera del temario práctico. |
| **Documentación** | 7 / 10 | 73 documentos, guías sincronizadas con el motor por pruebas. Penalizado porque la mayoría sigue en inglés para un curso en español. |
| **Contenido de juego** | 5 / 10 | 2 escenarios, 1 jefe, 8 clases de enemigo. Es lo que es: un motor con un prólogo, no un juego terminado. |
| **Producción** | 8 / 10 | Arranca, se empaqueta, se instala, no se cae sin tarjeta de sonido. Falta probar el `.exe` en una máquina limpia. |

### **Nota global: 8,4 / 10**

Ponderada hacia lo que usted va a usar este trimestre: motor, herramientas y
valor pedagógico pesan más que el contenido de juego.

---

## 6. Lo que significa esa nota

**Puede impartir el curso con esto.** El motor está sano, las herramientas
funcionan, un estudiante puede construir un escenario completo sin escribir
Python, y usted puede calificarlo automáticamente por estructura **y por
diseño**.

**Lo que baja la nota no es técnico.** Es contenido —dos escenarios— e idioma
—documentación en inglés—. Las dos cosas son horas de trabajo, no problemas
que resolver.

**Y una advertencia que me aplico:** esta sesión encontró **once defectos** en
sistemas que llevaban meses «terminados», todos con la misma forma —código
correcto, probado en aislamiento, que no llegaba a la pantalla—. La
iluminación no había iluminado un solo píxel en la vida del proyecto. Ninguno
se veía leyendo el código.

Las 1.507 pruebas de hoy son mejores que las 1.162 de ayer no por ser más
sino porque preguntan otra cosa: **miran los píxeles y cronometran
fotogramas**, en lugar de preguntar si algo se cae.

Si el próximo semestre alguien añade una característica, la pregunta que
merece la pena hacerle no es «¿pasan las pruebas?» sino **«¿la has visto en
pantalla?»**.
