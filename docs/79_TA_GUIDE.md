---
document_id: "LOI-TA-029B"
title: "Guía para ayudantes de cátedra — Legacy of InFest"
aliases: ["Guía para ayudantes de cátedra", "TA Guide"]
tags: ["ayudante", "docencia", "guia"]
description: "Guía del ayudante de cátedra"
source: "docs/79_TA_GUIDE.md"
date_processed: "2026-08-13"
---

# Guía para ayudantes de cátedra — Legacy of InFest

> **AUD-455.** Traduce el documento (tenía el cuerpo en inglés y un
> resumen condensado en español al final que remitía «al documento
> original en inglés»). Corrige varios datos verificados contra el código
> real: `Player` y `EnemyBase` viven en `src/framework/entities/`, no en
> `src/engine/entity/` (esa carpeta no existe); `math_utils.py` es un
> módulo de funciones sueltas, no una clase `MathUtils`; el módulo de
> reconocimiento de patrones es `pattern_recognition_tools.py`
> (`PatternRecognitionTools`), no "PatternTools"; `BossBase`/`EnemyBase`
> no tienen atributo `hp` — es `current_health`; los ficheros de guardado
> se llaman `slot_{N}.json`, no `save_*.json`; y el directorio de datos de
> usuario en Windows (el entorno real de este repo) es
> `%APPDATA%/legacyofinfest/`, no `~/.config/legacyofinfest/` (esa ruta es
> el respaldo para Linux — ver `user_data_dir()` en
> `src/engine/core/user_settings.py`).

## Visión general

Este documento ayuda a los ayudantes de cátedra a entender el framework, los problemas comunes de los estudiantes, las pautas de calificación, y cómo ayudar a los estudiantes de forma efectiva.

---

## 1. Arquitectura del framework (repaso de 30 minutos)

Muestre a los estudiantes estos directorios clave:

```
src/
  engine/        # Motor del juego central (no modificar)
    core/        # App, EventBus, Settings, Achievements
    input/       # InputManager, ActionMap
    scene/       # BaseScene, SceneManager
    scenes/      # Todas las pantallas del juego (modificar para laboratorios)
    utils/       # AssetLoader, math_utils
  framework/     # Sistemas de juego reutilizables
    entities/    # Player, EnemyBase, BossBase
    processing/  # ColorTools, FilterTools, VisionTools, PatternRecognitionTools
    scenes/      # StageScene
    stage/       # StageLoader, Camera, Collision
  stages/        # Código específico de escenario (área de trabajo del estudiante)
    stage0/      # Implementación de referencia
    boss_venado/ # Jefe de referencia
assets/
  maps/          # Ficheros de mapa TMX
  sprites/       # Jugador, enemigos, objetos
docs/            # Toda la documentación
scripts/         # validate_assets, validate_tmx, grade_stage, grade_boss
tests/           # Suite de pruebas pytest
```

---

## 2. Errores comunes de estudiantes y soluciones

### Errores de escenario TMX

| Error | Causa probable | Solución |
|-------|-------------|----------|
| «No terrain layer» | El estudiante olvidó añadir una capa Terrain | Añadir una capa de baldosas llamada "Terrain" |
| «Missing PlayerSpawn» | No se colocó el punto de aparición del jugador | Añadir un objeto con name="PlayerSpawn" |
| «Layer has 0 tiles» | Los datos CSV están vacíos | Volver a guardar el TMX en Tiled |
| «Climate: unknown» | Error tipográfico en la propiedad climate | Usar: rain, fog, wind, snow, clear, storm |
| Falta la propiedad author | Se olvidaron los metadatos | Añadir `<property name="author" value="nombre">` |
| Los checkpoints no se activan | No hay objetos Checkpoint | Añadir objetos Rectangle con type "Checkpoint" |
| No aparecen coleccionables | A la capa Items le faltan objetos | Colocar baldosas u objetos coleccionables |

### Errores de Python de jefe

| Error | Causa probable | Solución |
|-------|-------------|----------|
| «ModuleNotFoundError» | Ruta de importación incorrecta | Comprobar `from src.framework.entities.boss_base import BossBase` |
| El jefe no recibe daño | Falta el estado de daño | `apply_hit()` ya viene de `BossBase` — comprobar que no se sobrescribió sin llamar a `super()` |
| El jefe nunca cambia de fase | No se comprueba el umbral de salud | Comprobar que `set_phases()` recibió una lista de `BossPhase` con `health_threshold` correctos — la transición la hace `BossBase`, no código del estudiante |
| No hay ataques | El ataque no se llama en `update()` | Añadir llamadas de ataque por temporizador en el bucle `_alert_behavior` |
| `AttributeError: 'BossX' object has no attribute 'hp'` | El estudiante inventó un atributo `hp` propio | El atributo real es `self.current_health` (heredado de `EnemyBase`) |

### Errores de escena de laboratorio

| Error | Causa probable | Solución |
|-------|-------------|----------|
| La escena no carga | No está registrada en `scene_registry.py` | Añadir la llamada `reg.register()` |
| No se puede importar math_utils | Ruta de importación incorrecta | Usar `from src.engine.utils.math_utils import ...` |

---

## 3. Pautas de calificación

### Calificación de escenario (`grade_stage.py`)

Ejecutar: `python scripts/grade_stage.py ruta/al/escenario.tmx`

El script comprueba:
- **El fichero se parsea** (5 pts): el TMX es XML válido
- **Capas obligatorias** (10 pts): existe la capa Terrain
- **Punto de aparición del jugador** (10 pts): se colocó el objeto PlayerSpawn
- **Checkpoints** (15 pts): al menos 1 checkpoint
- **Tipos de enemigo válidos** (10 pts): usa tipos de enemigo conocidos
- **Enemigos colocados** (10 pts): enemigos en la capa de objetos
- **Coleccionables** (10 pts): 3+ objetos coleccionables
- **Metadatos** (10 pts): author, stage_id, stage_name
- **Tileset** (5 pts): la ruta de imagen del tileset es válida
- **Clima** (5 pts): valor de clima conocido
- **Límites del mapa** (5 pts): dimensiones razonables
- **Límite de tiempo** (5 pts): razonable o ninguno

**Aprobación:** ≥70% (ajustar según la entrega)

### Calificación de jefe (`grade_boss.py`)

Ejecutar: `python scripts/grade_boss.py ruta/al/jefe.py`

El script comprueba:
- **Hereda de BossBase** (10 pts)
- **Transiciones de fase** (15 pts): 2+ indicadores de fase
- **Patrones de ataque** (15 pts): 2+ métodos de ataque
- **Umbrales de salud** (10 pts): cambios de estado basados en salud
- **Estado de telegrafiado** (10 pts): preparación antes de los ataques
- **Estados de daño/dolor** (10 pts): método take_damage o hurt
- **Conexiones de eventos** (10 pts): integración con el bus de eventos
- **Configuración del nombre del jefe** (10 pts): atributo boss_name
- **Importaciones** (5 pts): BossBase importado correctamente
- **Estructura de la clase** (5 pts): 5+ métodos

**Aprobación:** ≥70%

---

## 4. Verificación de completitud de laboratorio

Cada laboratorio tiene un estado de completitud guardado en el sistema de guardado. Para verificar:

1. Ejecutar el juego
2. Navegar al Menú de Demos
3. Entrar a cada escena de laboratorio
4. Verificar al menos 30 segundos de interacción
5. Comprobar el fichero de guardado en busca de marcadores de completitud

Los estudiantes deben producir capturas o PNGs (tecla S en las escenas demo):

| Laboratorio | Criterio de captura |
|-----|-------------------|
| Vector | Ambos vectores visibles con todos los modos recorridos |
| Transform | Formas transformadas visibles |
| Curve | Curva visible con puntos de control |
| Interpolation | Curvas de easing visibles |
| Color | Todos los valores de espacio de color visibles |
| Noise | Patrón de ruido generado |
| Collision | Cajas de colisión visibles |
| Filter | Resultado filtrado visible |
| Vision | Resultado de segmentación visible |
| Pattern | Resultado de clasificación visible |

---

## 5. Consejos para horas de oficina

> Organizado por tema, no por número de clase — el calendario oficial de
> 11 clases está en `21_COURSE_SCHEDULE.md` §2; consúltelo para saber en
> qué clase corresponde cada tema.

**Configuración inicial:**
- Problema más común: `pygame` no instalado → `pip install -e ".[dev]"`
- El editor de mapas Tiled no crea la codificación CSV → comprobar "Map format: CSV" en Tiled

**Vectores:**
- Los estudiantes confunden `pygame.Vector2.normalize()` (in situ) con `normalize()` (devuelve una copia)
- Un producto punto < 0 significa que los vectores miran en direcciones opuestas

**Curvas:**
- Algoritmo de de Casteljau: interpolación lineal recursiva
- Los estudiantes olvidan hacer lerp en x Y en y por separado

**Colisión:**
- AABB: comprobar el solape en ambos ejes
- Los estudiantes olvidan separar la velocidad en componentes x/y

**Color:**
- El Matiz de HSV está en grados (0-360), no en 0-1
- CMYK: K es el componente negro; CMY sin K da un marrón sucio

**Filtros:**
- Convolución: el kernel debe voltearse (o no, según la convención)
- Los estudiantes se confunden con la normalización del kernel

**Diseño de jefe:**
- Los estudiantes intentan poner todo el código en un método → fomentar la separación de métodos
- Las transiciones de fase necesitan retroalimentación visual (cambio de color, aura, diálogo)

---

## 6. Referencia rápida

### Ejecutar el juego
```bash
python main.py
```

### Ejecutar las pruebas
```bash
python -m pytest tests/ -v
```

### Ejecutar los calificadores
```bash
python scripts/validate_tmx.py
python scripts/grade_stage.py assets/maps/stage0/stage0.tmx --json
python scripts/grade_boss.py src/stages/boss_venado/boss_venado.py --json
```

### Crear un escenario nuevo
1. Copiar `student_templates/stage_template/stage_template.py`
2. Crear el TMX en Tiled
3. Añadir las capas obligatorias (ver `06_TMX_SPEC.md` §3)
4. Colocar PlayerSpawn, enemigos, coleccionables
5. Añadir las propiedades del mapa (stage_id, stage_name, bgm_track, climate)

### Crear un jefe nuevo
1. Copiar `student_templates/boss_template/boss_template.py`
2. Heredar de BossBase
3. Implementar al menos 2 fases con umbrales de salud
4. Añadir 2+ patrones de ataque con estados de telegrafiado
5. Conectar al bus de eventos para daño/dolor

---

## 7. Integración con Canvas/Teams

El framework guarda los datos de completitud en:
- Ficheros de guardado: `%APPDATA%/legacyofinfest/saves/slot_{N}.json` (Windows); `~/.config/legacyofinfest/saves/` como respaldo en otras plataformas
- Datos de logros: `%APPDATA%/legacyofinfest/achievements.json`
- Capturas de pantalla: `screenshots/` en el directorio del proyecto

Para recolectar el progreso del estudiante, se puede:
1. Usar GitHub Actions para ejecutar los calificadores en cada push
2. Recolectar capturas vía artefactos de pull request
3. Usar `grade_stage.py --json` para calificación masiva
