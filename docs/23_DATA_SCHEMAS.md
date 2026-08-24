---
document_id: "LOI-SCHEMA-023"
title: "Legacy of InFest — Esquemas de datos"
aliases: ["Esquemas de datos", "Data Schemas"]
tags: ["datos", "esquemas", "tipos"]
description: "La forma exacta de los datos que cruzan los límites entre módulos"
source: "docs/23_DATA_SCHEMAS.md"
date_processed: "2026-08-12"
---

# Legacy of InFest — Esquemas de datos

**ID del documento:** LOI-SCHEMA-023
**Versión:** 1.1.0
**Estado:** Oficial
**Requiere:** `22_API_CONTRACTS.md`
**Audiencia:** Asistentes de programación con IA

> **AUD-455.** Esta versión traduce el documento completo y corrige: la
> tabla de `BOSS_PHASE_CHANGED` decía que lo emitía
> `BossBase._begin_phase_transition()`, método que no existe (coincide con
> la corrección AUD-307 de `22_API_CONTRACTS.md`) — el método real es
> `_finish_phase_transition()`, y el payload real trae más claves de las
> documentadas (`boss_name`, `phase_count`, `new_max_health`, no sólo
> `phase`); la tabla de fijado de versiones (§9) recomendaba `Pillow~=10.4`,
> una versión con diez vulnerabilidades públicas que el propio
> `pyproject.toml` corrigió a `>=12.3.0` (AUD-176) — es decir, este
> documento recomendaba instalar una dependencia insegura a propósito
> corregida en otro sitio; también le faltaban `pydantic` y `orjson`
> (dependencias reales) y sobraba `pytweening` (retirada, AUD-007); y
> citaba tres veces documentos que no existen en este repositorio:
> `25_IMPLEMENTATION_ROADMAP.md`, `77_SYLLABUS_ALIGNMENT_AUDIT.md` y
> `02_CODEX_CONTEXT.md`.

---

<!-- cita-historica -->
> **Corrección AUD-150 — nombres que este documento daba por existentes.**
> Comprobados uno por uno contra el código. Ninguno rompe nada al jugar; todos
> engañan a quien lea el documento para programar.
>
> * `Message` **no es un tipo de objeto**: es `MessageTrigger`.
> * `BossSpawn` **no lo acepta el motor.** Los tres jefes se colocan con su tipo propio.
> * `n_features` es una variable de ejemplo del pseudocódigo de scikit-learn, no un identificador del proyecto. Se deja porque el ejemplo se entiende mejor así.
<!-- /cita-historica -->


## 1. Propósito

`22_API_CONTRACTS.md` define las **firmas** de funciones y clases. Este documento define la forma exacta de los **datos** que fluyen por esas firmas y entre ficheros en disco — propiedades de objeto TMX, payloads de eventos, ficheros de dataset, modelos serializados y ficheros de configuración. Donde `22_API_CONTRACTS.md` dice `dict[str, Any]` o `**kwargs`, este documento dice exactamente qué claves son válidas y qué significan.

---

## 2. Esquemas de payload del EventBus

Cada evento del sistema, con sus claves exactas de `**data`, tipos y reglas de emisión/consumo. Esto amplía `22_API_CONTRACTS.md` §2.3 a una referencia completa.

| Evento | Esquema del payload | Lo emite | Lo consume |
|---|---|---|---|
| `PLAYER_DAMAGED` | `{amount: float, source: tuple[float, float]}` | `Player.apply_damage()` | `HUD`, `AudioManager` |
| `PLAYER_HEALED` | `{amount: float}` | `Checkpoint` (al restaurar en reaparición) | `Player`, `HUD` |
| `PLAYER_DIED` | `{}` | `Player.apply_damage()` (la vida llega a 0) | `SceneManager` (apila GameOverScene) |
| `CHECKPOINT_REACHED` | `{checkpoint_id: int}` | `Checkpoint.update()` | `StageLoader` (actualiza el ancla de reaparición) |
| `ENEMY_DIED` | `{entity_id: str, position: tuple[float, float]}` | `EnemyBase._die()` | El escenario (lógica de botín/puntuación), `AudioManager` |
| `STAGE_COMPLETE` | `{}` | Comprobación de colisión de `NextTrigger` (código de escenario) o secuencia de derrota de jefe | `SceneManager` (avanza de escena) |
| `BOSS_PHASE_CHANGED` | `{boss_name: str, phase: int, phase_count: int, new_max_health: float}` | `BossBase._finish_phase_transition()` | Elemento de HUD de jefe, código de escenario |
| `SHOW_MESSAGE` | `{text: str, duration: float}` | Código de escenario (zona de disparo de mensaje) | `MessageBox` |
| `HIDE_MESSAGE` | `{}` | Código de escenario | `MessageBox` |

**Regla:** `entity_id` en `ENEMY_DIED` es una cadena, no una referencia a objeto — típicamente `f"{type(self).__name__}_{id(self)}"` o el nombre del objeto TMX si está disponible. Nunca se pasa una entidad viva por el EventBus; los payloads deben ser datos planos (str, float, int, tuple) para no acoplar ciclos de vida.

---

## 3. Esquemas de propiedades de objeto TMX

Esto amplía `06_TMX_SPEC.md` §6 a los diccionarios de propiedades exactos que `StageLoader` recibe de `pytmx`. Todos los valores de propiedad llegan de `pytmx` ya convertidos según el atributo `type` fijado en Tiled (`int`, `float`, `bool`, `string`).

### 3.1 `PlayerSpawn`

```python
{
    # No requiere propiedades personalizadas.
}
```

### 3.2 `Walker`

```python
{
    "patrol_length": int,      # por defecto 96 si falta
    "facing": str,              # "left" | "right", por defecto "right"
    "patrol_speed": float,      # por defecto 45.0
    "alert_speed": float,       # por defecto 75.0
    "damage_on_contact": float, # por defecto 0.5
}
```

### 3.3 `Flying`

```python
{
    "flight_mode": str,         # "sine" | "bezier" | "patrol", por defecto "sine"
    "flight_speed": float,      # por defecto 60.0
    "sine_amplitude": float,    # por defecto 28.0, sólo se usa si flight_mode == "sine"
    "sine_frequency": float,    # por defecto 1.5, sólo se usa si flight_mode == "sine"
    # "owner_id" aparece en los objetos Waypoint enlazados, NO en el objeto Flying.
}
```

### 3.4 `Shooter`

```python
{
    "fire_rate": float,            # por defecto 0.5
    "projectile_speed": float,     # por defecto 120.0
    "projectile_damage": float,    # por defecto 0.5
    "patrol_length": int,          # por defecto 0 (estacionario)
}
```

### 3.5 `Checkpoint`

```python
{
    "checkpoint_id": int,   # OBLIGATORIO, sin valor por defecto — StageLoader lanza FrameworkUsageError si falta
}
```

### 3.6 `MessageTrigger`

```python
{
    "text": str,            # OBLIGATORIO. Puede contener "\n" literal para saltos de línea.
    "duration": float,      # OBLIGATORIO. 0.0 significa descarte manual (espera CONFIRM).
    "trigger_once": bool,   # por defecto True
}
```

### 3.7 `Waypoint`

```python
{
    "owner_id": str,            # OBLIGATORIO. Debe coincidir con el `name` de un objeto Flying del mismo mapa.
    "waypoint_index": int,      # OBLIGATORIO. Base 0; los waypoints se ordenan ascendentemente por este valor.
}
```

### 3.8 `HazardZone`

```python
{
    "damage": float,         # OBLIGATORIO
    "damage_type": str,      # etiqueta de texto libre, p. ej. "spike", "floor_spikes" — sólo pista cosmética/de sonido
}
```

### 3.9 `CameraLock`

```python
{
    "lock_x": bool,   # por defecto False
    "lock_y": bool,   # por defecto False
}
```

### 3.10 BossSpawn — implementado (AUD-259)

> **AUD-455 — esta sección decía "no implementado" (AUD-150).** Dejó de ser cierto en AUD-259:
> `StageObjetos._handle_boss_spawn()` (`src/framework/stage/stage_objetos.py`) sí reconoce este
> tipo. Se comprobó leyendo el código, no citando el aviso antiguo.

```python
{
    "boss": str,   # OBLIGATORIO. Debe coincidir con una clave del registro de entidades (el mismo que usan "BossVenado", etc. — ver §3.11).
}
```

Escribir `type="BossSpawn"` con `boss="BossVenado"` produce exactamente la misma entidad que
escribir `type="BossVenado"` directamente: los dos se resuelven contra el mismo registro. Si
falta la propiedad `boss`, o nombra una clave no registrada, `StageLoader` **avisa** (por el
camino de diagnóstico de AUD-055) en vez de fallar en silencio o lanzar una excepción.

### 3.11 Tabla de registro en la fábrica de entidades

Es la correspondencia canónica que las llamadas a `StageLoader.register_entity()` deben establecer antes de cargar cualquier TMX:

```python
StageLoader.register_entity("Walker", EnemyWalker)
StageLoader.register_entity("Flying", EnemyFlying)
StageLoader.register_entity("Shooter", EnemyShooter)
StageLoader.register_entity("Checkpoint", Checkpoint)
# Los jefes se registran por entrega, por ejemplo:
StageLoader.register_entity("BossVenado", BossVenado)
```

Las entidades personalizadas de los estudiantes registran nombres adicionales siguiendo el mismo patrón — ver `26_STUDENT_TEMPLATE_SPEC.md` §5.

---

## 4. Estructuras de datos de los módulos de procesamiento

### 4.1 `ComponentResult` (VisionTools)

Ya tipado en `22_API_CONTRACTS.md` §14.1. Semántica de los campos:

| Campo | Forma/Tipo | Notas |
|---|---|---|
| `label_array` | `np.ndarray`, `int32`, `(H, W)` | `0` = fondo; `1..N` = etiquetas de componente |
| `num_components` | `int` | Cuenta de etiquetas distintas no-cero |
| `component_sizes` | `dict[int, int]` | `{label_id: recuento_de_píxeles}`, todas las etiquetas 1..N presentes como claves |
| `label_surface` | `pygame.Surface` | RGB, misma `(W, H)` que la entrada; cada etiqueta recibe un tono distinto de una paleta de 8 colores, que se repite si `num_components > 8` |

### 4.2 `RegionInfo` (VisionTools)

| Campo | Tipo | Rango/Notas |
|---|---|---|
| `label` | `int` | Coincide con una clave de `ComponentResult.component_sizes` de origen |
| `area` | `int` | Recuento de píxeles, > 0 |
| `centroid` | `tuple[float, float]` | `(x, y)` en coordenadas de píxel, espacio de imagen (no espacio de mundo — quien llama debe desplazar) |
| `bounding_rect` | `pygame.Rect` | Alineado a los ejes, en el mismo espacio de coordenadas que la superficie de entrada |
| `eccentricity` | `float` | `[0.0, 1.0]`; 0 = círculo, cerca de 1 = línea |
| `solidity` | `float` | `(0.0, 1.0]`; área / área_del_casco_convexo |
| `perimeter` | `float` | Unidades de píxel, > 0 |

### 4.3 `TrainedModel` (PatternRecognitionTools)

| Campo | Tipo | Notas |
|---|---|---|
| `model_type` | `str` | Uno de `"knn"`, `"tree"`, `"forest"`, `"svm"` — ningún otro valor es válido |
| `estimator` | `sklearn.pipeline.Pipeline` | Siempre `Pipeline([("scaler", StandardScaler()), ("classifier", <estimador>)])` — nunca un estimador suelto |
| `classes` | `list[str]` | Valores únicos ordenados de la `y` de entrenamiento, convertidos a `str` |
| `feature_method` | `str` | Uno de `"hog"`, `"lbp"`, `"color_hist"`, `"combined"`, `"external"` |
| `feature_length` | `int` | Debe coincidir con la segunda dimensión de cualquier `X` que se pase a `classify()` |
| `training_accuracy` | `float` | `[0.0, 1.0]` |
| `metadata` | `dict[str, Any]` | Libre; **debe** incluir `"kwargs"` (el diccionario de hiperparámetros pasado a `train()`); **debería** incluir `"evaluation"` con el `EvaluationResult` serializado si se corrió `evaluate()` antes de guardar (ver §4.4 para el subesquema exacto, necesario para el Modo 3 — Confusión de `PatternDemoScene`) |

### 4.4 Convención de inserción de `EvaluationResult`

Cuando existe la clave `TrainedModel.metadata["evaluation"]`, debe seguir este subesquema exacto para que `PatternDemoScene` (ver `15_ACADEMIC_DEMO_SCENES.md` §5.7) lo pueda dibujar sin casos especiales:

```python
metadata["evaluation"] = {
    "accuracy": float,                      # refleja EvaluationResult.accuracy
    "per_class_accuracy": dict[str, float],
    "confusion_matrix": list[list[int]],    # lista anidada apta para JSON/pickle, NO np.ndarray
    "report": str,
    "test_set_size": int,                   # len(y_test) en el momento de la evaluación
}
```

**Nota:** `confusion_matrix` se guarda como `list[list[int]]` anidada dentro de `metadata` (apta para pickle e inspeccionable a mano) aunque `EvaluationResult.confusion_matrix` en sí sea un `np.ndarray` vivo en tiempo de ejecución. Convertir con `.tolist()` antes de guardar, y con `np.array(...)` tras cargar si hacen falta operaciones de matriz.

---

## 5. Formato del fichero de dataset (`.npz`)

### 5.1 Estructura

Según `13_PATTERN_RECOGNITION_SPEC.md` §8.3, todos los datasets son archivos comprimidos de NumPy con exactamente dos arreglos:

```python
np.savez(path, X=X, y=y)

# X.shape == (n_samples, n_caracteristicas), dtype == np.float32
# y.shape == (n_samples,), dtype == '<U...' (cadena unicode de numpy) u object
```

### 5.2 Convención de carga

```python
data = np.load(path)
X: np.ndarray = data["X"].astype(np.float32)   # siempre se reconvierte a la defensiva
y: np.ndarray = data["y"]
```

### 5.3 Especificación del dataset de muestra (provisto por el profesor)

`assets/datasets/sample_dataset.npz` — lo requiere el modelo que carga por defecto `PatternDemoScene`:

| Propiedad | Valor |
|---|---|
| `n_samples` | 90 |
| n_features (variable del ejemplo, no del proyecto) | 512 (HOG sobre un recorte canónico de 32×32) |
| Clases | `"dark_zone"`, `"neutral"`, `"light_zone"` — exactamente 30 muestras cada una |
| Origen | Recortes de superficie de 32×32 generados sintéticamente o derivados de capturas de pantalla, estratificados por las tres clases según el umbral de luminancia media |

### 5.4 Requisitos mínimos del dataset de un estudiante

Según `13_PATTERN_RECOGNITION_SPEC.md` §8.1, expresado aquí como la comprobación de esquema que `tools/build_dataset.py` debe exigir:

```python
assert X.shape[0] == y.shape[0]
assert X.shape[0] >= 10
assert X.dtype == np.float32
assert len(set(y.tolist())) >= 2
for class_label in set(y.tolist()):
    assert (y == class_label).sum() >= 10  # mínimo de muestras por clase
```

---

## 6. Formato del fichero de modelo (`.pkl`)

### 6.1 Serialización

```python
import joblib
joblib.dump(trained_model_dataclass_instance, path)  # path: *.pkl
```

Se serializa la instancia completa del dataclass `TrainedModel` — no sólo el estimador de scikit-learn. Por eso `load_model()` devuelve un `TrainedModel`, no un estimador suelto (ver `22_API_CONTRACTS.md` §15.1).

### 6.2 Convención de ubicación del fichero

| Contexto | Ruta |
|---|---|
| Modelo de referencia del profesorado | no se distribuye: se entrena en cada máquina desde `assets/datasets/sample_dataset.npz` y se cachea fuera del repositorio (AUD-587) |
| Modelo de la entrega de un estudiante | `src/stages/<entrega_del_estudiante>/models/<nombre>.pkl` |

**Nota:** el modelo de un estudiante vive dentro de su propia carpeta de entrega bajo `src/stages/`, no en un directorio de nivel superior aparte.

---

## 7. Esquema de la cabecera YAML del README de escenario

Todo `README.md` de escenario o jefe (ya sea `stage0/README.md` o el de una entrega de estudiante) debe empezar con exactamente este bloque de cabecera YAML, para que las herramientas (y los scripts de calificación) puedan leer los metadatos sin procesamiento de lenguaje natural:

```yaml
---
assignment_type: stage | boss
assignment_name: "La Soda"          # nombre legible
assignment_id: "stage1_2_la_soda"   # debe coincidir con el nombre de la carpeta en src/stages/
zone: 1 | 2 | 3 | final
student_name: "Jane Doe"             # se omite, o "professor" para el Stage 0 / jefes sin reclamar
units_demonstrated: [II, III, IV, V]  # unidades del programa, se actualiza según avanzan los hitos
evaluation_milestone: "Evaluación Práctica I" | "Evaluación Práctica II" | "Evaluación Práctica III"
---
```

Seguido de Markdown libre documentando los conceptos académicos que demuestra la entrega.

---

## 8. Esquema de entrada de `KNOWN_GAPS.md`

Cualquier `TODO`/`NotImplementedError` sin resolver debe registrarse en la raíz del repositorio, en `KNOWN_GAPS.md`, con este formato exacto de entrada, para que sea buscable por script:

```markdown
## [GAP-001] <título breve>

- **File:** `src/ruta/al/fichero.py`
- **Phase:** <contexto en que se aplazó — fase de implementación, iteración de auditoría, etc.>
- **Reason:** <por qué está intencionalmente incompleto>
- **Resolution plan:** <cuándo/cómo se resuelve, o "N/A — fuera de alcance">
```

### 8.1 Cómo se cierra una entrada (AUD-421)

La invariante 4 de `CLAUDE.md` remitía aquí para el formato de cierre y esta
sección **sólo describía el alta**. Remitir a un sitio que no contiene lo
prometido es la misma clase de defecto que persigue la fase entera: una
referencia que se lee como autoridad y no dice nada. Queda escrito:

```markdown
## ~~[GAP-001] <título>~~ *(Resuelto)*

  …el cuerpo original se conserva entero, y debajo…

- **Resolution (<fecha>, AUD-NNN):** <qué se hizo y con qué evidencia>
```

Tres reglas, y el motivo de cada una:

* **La entrada no se borra ni se reescribe.** Se tacha el encabezado y se
  añade la resolución debajo. El texto original es la única constancia de qué
  se creía que pasaba, y en esta fase se ha dado tres veces el caso de que el
  hueco describía mal su propio problema (`GAP-036`, `GAP-037`, `GAP-046`):
  borrarlo habría borrado también esa lección.
* **`**Resolution:**` es la etiqueta canónica.** Se acepta `**Decisión:**`
  cuando el hueco se cierra por criterio del dueño sin tocar código —`GAP-024`
  y `GAP-041` son de ese tipo— porque forzar la palabra «Resolution» ahí sería
  llamar arreglo a lo que fue un juicio. Lo que no vale es no poner ninguna.
* **La resolución dice *cómo se comprobó*, no sólo *que se hizo*.** Un hueco
  tachado sin evidencia obliga a la siguiente persona a rehacer la
  investigación entera para saber si se arregló, se midió y se descartó, o se
  decidió no hacerlo.

Lo vigila `tests/test_los_huecos_cerrados_dicen_como.py`, que existe porque
`GAP-034` estuvo meses tachado sin resolución escrita y se encontró a mano
(AUD-412).

---

## 9. Tabla de fijado de versiones de dependencias

`requirements.txt` y `[project.dependencies]` en `pyproject.toml` son la
fuente de verdad (`scripts/check_dependency_sync.py` comprueba que no
diverjan) — la tabla de aquí abajo es un espejo, no una copia independiente
que se pueda desactualizar por su cuenta:

```
pygame-ce>=2.5
numpy>=1.26              # AUD-173: sin tope superior — un tope <2 impedía instalar en Python 3.13
pydantic>=2.7
orjson>=3.10
scipy>=1.13
opencv-python>=4.10
scikit-image>=0.24
scikit-learn>=1.5
Pillow>=12.3.0           # AUD-176: suelo de seguridad — versiones anteriores tienen 10 CVE publicados
pytmx>=3.32
pyscroll>=2.31
joblib>=1.4
matplotlib>=3.10         # AUD-173: subido de 3.8/3.9 — versiones anteriores no conviven con numpy 2.x
```

**AUD-455 — qué decía esta tabla antes y por qué importaba corregirlo.**
Recomendaba `Pillow~=10.4`: una versión con diez vulnerabilidades publicadas
que `pyproject.toml` corrigió explícitamente a `>=12.3.0` (AUD-176, con su
propio suelo de seguridad vigilado por `tests/test_dependencias_coherentes.py`).
Recomendaba también `pytweening~=1.2`, una dependencia que ya no existe en el
proyecto (AUD-007: nada la importaba; `math_utils.py` implementa sus propias
funciones de easing, ver `10_LIBRARIES_AND_DEPENDENCIES.md` §11) y `matplotlib~=3.9`,
por debajo del `>=3.10` real. Le faltaban `pydantic` y `orjson`, que sí son
dependencias obligatorias reales. Una tabla de versiones que recomienda
instalar una dependencia insegura y una que no existe es peor que no tener
tabla — parece una fuente de verdad y no lo es.

Los extras opcionales (`numba`/`ModernGL` vía `[accel]`, `lupa` vía
`[scripting]`, `pydub` vía `[audiotools]`) no van en esta tabla: el juego
funciona sin ellos, con una ruta de repliegue documentada en
`10_LIBRARIES_AND_DEPENDENCIES.md` §15.

---

## 10. Convenciones de espacio de coordenadas

Una fuente recurrente de errores en código de juegos 2D son las suposiciones inconsistentes sobre el espacio de coordenadas. Esta tabla es la referencia única para desambiguar:

| Espacio | Origen | Lo usa | Conversión |
|---|---|---|---|
| **Espacio de mundo** | Esquina superior izquierda del mapa TMX (0,0) | `BaseEntity.position`, `StageData.collision_rects`, objetivo de `Camera.follow` | — |
| **Espacio de pantalla** | Esquina superior izquierda de la superficie interna de 800×600 (`settings.INTERNAL_WIDTH`/`INTERNAL_HEIGHT`) | `HUD`, `MessageBox`, `ScreenBanner`, cualquier cosa dibujada sin `camera_offset` | `pantalla = mundo - camera.offset` |
| **Espacio local de entidad** | Esquina superior izquierda del propio fotograma de sprite de la entidad | Valores devueltos por `EnemyBase._build_hitbox()`, `_build_hurtbox()` | `mundo = entity.position + desplazamiento_local` |
| **Espacio de píxel TMX** | Esquina superior izquierda del mapa de Tiled, en píxeles (coincide 1:1 con el espacio de mundo) | Valores `.x`/`.y` en crudo de un objeto `pytmx` | Idéntico al espacio de mundo — sin conversión |
| **Espacio de arreglo local a la superficie** | Esquina superior izquierda de un `pygame.Surface`/`np.ndarray` en proceso | Todas las entradas/salidas de `FilterTools`/`VisionTools` | Es responsabilidad de quien llama volcar en el desplazamiento correcto de mundo/pantalla tras procesar |

**Regla para `RegionInfo.centroid` y `.bounding_rect`:** siempre están en el espacio de coordenadas de la superficie que se pasó a `VisionTools.analyze_regions()` — si quien llama pasó un `subsurface()` recortado del espacio de mundo, debe volver a sumar el desplazamiento de la subsuperficie antes de tratar el resultado como una posición de espacio de mundo.

> **AUD-455.** La fila de «Espacio de pantalla» decía 320×224 — la resolución
> interna real es 800×600 (`settings.INTERNAL_WIDTH`/`INTERNAL_HEIGHT`), el
> mismo defecto de maqueta heredada corregido por AUD-451/452/453 en el HUD,
> Opciones y el cuadro de mensajes.

---

## 11. Componentes ECS (`src/framework/ecs/components.py`)

GAP-054 (resuelto). Veinte clases de componente — datos sin comportamiento (F5.1: ningún componente llama al bus de eventos ni mueve otra entidad). Todos son `@dataclass(slots=True)` salvo `Transform` y `Salud`, que usan `__slots__` a mano porque son **vistas**: no guardan copia propia cuando tienen dueño, leen/escriben directamente los atributos del dueño (`position`/`rect`/`facing_direction`, `current_health`/`max_health`) para no duplicar el dato que ya usan las 26 clases de estudiante (AUD-123, F5.12).

| Componente | Campos | Para qué |
|---|---|---|
| `Transform` | `posicion`, `rect`, `facing` (propiedades; vista sobre el dueño si se construye con `duenio=`) | Posición y orientación — casi todo lo tiene |
| `Velocidad` | `v: pygame.Vector2` | Velocidad lineal |
| `Solido` | `atravesable_desde_abajo: bool = False` | Bloquea el paso — geometría del escenario, puertas |
| `Salud` | `actual`, `maxima`, `invulnerable`, `fraccion` (propiedades; vista sobre `current_health`/`max_health` si tiene dueño) | Vida y su fracción |
| `EsJugador` | (vacío) | Marca: esta entidad es el jugador (F5.11) |
| `Resorte` | `rect`, `impulso: float = -520.0`, `rearme: float = 0.15`, `listo` (propiedad) | Rebote vertical al pisarlo — sólo si venías cayendo |
| `Navegante` | `ruta: list`, `proximo: float` (escalonado aleatorio, AUD-389) | Enemigos que rodean obstáculos en vez de ir recto |
| `Efectos` | `activos: list` | Efectos temporales (veneno, etc.) — catálogo en `combate/efectos.py` (AUD-388) |
| `ZonaDeViento` | `rect`, `fuerza: pygame.Vector2`, `periodo: float = 0.0`, `soplando` (propiedad) | Empuja a quien está dentro |
| `ZonaDeFriccion` | `rect`, `multiplicador: float = 1.0`, `arrastre: float = 0.0` | `multiplicador` **escala** la velocidad horizontal (AUD-236: <1 frena, >1 acelera — no es un coeficiente de rozamiento clásico) |
| `ZonaLetalTemporizada` | `rect`, `dano: float = 99.0`, `encendido`, `apagado`, `desfase`, `activa`/`aviso` (propiedades) | Mata sólo mientras está encendida — láseres, ondas de choque |
| `ZonaDeAgua` | `rect`, `corriente: pygame.Vector2` | Dispara `SwimmingState` (F5.6) |
| `PlataformaMovil` | `origen`, `destino`, `velocidad: float = 40.0`, `espera: float = 0.5`, `delta` | Va y viene arrastrando a quien lleva encima |
| `BloqueRitmico` | `visible_seg`, `oculto_seg`, `desfase`, `patron: str = ""`, `sigue_la_musica`/`presente` (propiedades) | Aparece/desaparece a compás; con `patron` sigue el reloj musical (F6) |
| `PlataformaHundible` | `retraso: float = 0.4`, `velocidad_caida: float = 90.0`, `reaparece_en: float = 3.0`, `y_original: float` | Se hunde al pisarla y reaparece |
| `Liana` | `rect`, `ancho_de_agarre: int = 10`, `velocidad: float = 70.0` | Trepable — dispara `TrepandoState` |
| `Tirolesa` | `origen`, `destino`, `velocidad: float = 190.0`, `radio_de_enganche: float = 14.0`, `solo_de_bajada: bool = True`, más `punto_mas_cercano()`/`progreso()` | Cable diagonal deslizante — declarado por dos puntos porque la pendiente es la mecánica |
| `ConoDeVision` | `mira: pygame.Vector2`, `alcance: float = 160.0`, `semiangulo: float = 30.0`, `barrido`, `ve_al_jugador: bool` | Detección de sigilo por ángulo/distancia |
| `Alerta` | `nivel`, `subida_por_segundo`, `bajada_por_segundo`, `umbral_sospecha`, `umbral_alerta`, `ultimo_visto`, `segundos_de_busqueda: float = 3.0`, `estado` (propiedad: `"tranquilo"`/`"sospecha"`/`"busqueda"`/`"alerta"`) | Máquina de estados de sigilo con memoria (AUD-286) |
| `Acosador` | `velocidad: float = 55.0`, `distancia_retirada: float = 480.0`, `reaparicion: float = 6.0` | Persigue, no se puede matar, se retira y reaparece (tipo Nemesis/SA-X) |

<!-- cita-historica -->
**Retirados (AUD-123):** `Gravedad`, `Renderizable` y `Etiqueta` se escribieron sin que ningún sistema, escena o prueba los usara nunca — cero alcanzabilidad. La gravedad la aplica cada entidad en su propia física, el dibujado lo hace `DrawingSystem` desde `entity_list`, y el filtrado por rol usa `isinstance`. No están en la tabla porque no existen en el código.
<!-- /cita-historica -->

Verificado contra `src/framework/ecs/components.py` (20 clases exactas vía `grep -cE "^class "`).

---
## 🔗 Documentos relacionados

- [[22_API_CONTRACTS.md|Contratos de API]]
