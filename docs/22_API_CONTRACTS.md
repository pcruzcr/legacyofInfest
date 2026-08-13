---
document_id: "LOI-API-022"
title: "Legacy of InFest — Contratos de API"
aliases: ["Contratos de API", "API Contracts"]
tags: ["api", "contratos", "sintaxis"]
description: "Firmas exactas de funciones y clases"
source: "docs/22_API_CONTRACTS.md"
date_processed: "2026-08-13"
---

# Legacy of InFest — Contratos de API

**ID del documento:** LOI-API-022
**Versión:** 1.3.0
**Estado:** Oficial
**Compatibilidad:** Referencia autoritativa de firmas para todo `src/engine/` y `src/framework/` (§2–§20); `03_ARCHITECTURE.md` a `17_BOSS_SPEC.md` son las contrapartidas narrativas de comportamiento
**Audiencia:** Asistentes de programación con IA

> **AUD-455 (2026-08-12/13).** Esta versión traduce el documento completo
> (antes en inglés, con un resumen condensado en español duplicado al final —
> con su propia numeración de secciones repetida y sin la corrección AUD-307
> que sí tenía ya el original) y corrige: la afirmación de que las
> anotaciones de tipo usan "sintaxis de Python 3.14+" (el proyecto exige
> `>=3.11` y CI llega hasta 3.13 — nada de lo documentado aquí es sintaxis
> exclusiva de 3.14); las rutas de
> `ASSETS_DIR`/`STAGES_DIR`/`STUDENT_TEMPLATES_DIR`, que son absolutas en el
> código real (`_PROJECT_ROOT / "..."`), no relativas; la numeración
> duplicada `### 2.6` (dos secciones distintas con el mismo número); y una
> referencia a `02_CODEX_CONTEXT.md`, que no existe en este repositorio.
>
> Una revisión posterior, línea a línea contra el código real, encontró y
> corrigió al menos una discrepancia real en prácticamente cada sección
> preexistente (parámetros faltantes, valores por defecto equivocados,
> métodos enteros sin documentar, una propiedad documentada como método
> invocable) — cada corrección lleva su propia nota `AUD-455` en el sitio
> donde ocurre. La misma revisión añadió cobertura de API que no existía en
> absoluto: UI compartida (`Theme`, `MenuList`, minimapa, subtítulos — §7.4–7.7),
> 28 escenas de contenido/menú (§17.8), `StageScene` y sus mixins (§11.8), y
> la totalidad de `src/framework/physics/`, `combate/`, `ai/`, `world/`,
> `academic/` y `vfx/` (§20, 25 subsecciones). El documento pasó de
> cubrir un subconjunto de `src/engine/core/` y `src/framework/entities/` a
> cubrir la práctica totalidad del árbol no perteneciente a
> `src/stages/` (código de estudiante, fuera de alcance por invariante 1/2
> de `CLAUDE.md`).

---

## 1. Propósito y regla de precedencia

Este documento es la **única fuente de verdad para las firmas exactas de funciones y clases** de todo el código de Legacy of InFest. Cada descripción en prosa de los documentos 03–17 es autoritativa para el *comportamiento*; este documento es autoritativo para la *sintaxis* — nombres de parámetro, tipos, orden, valores por defecto y tipos de retorno.

**Regla de precedencia:** si este documento y un documento narrativo de especificación (p. ej. `04_PLAYER_SPEC.md`) parecen no coincidir en una firma, este documento gana para la sintaxis, y el documento narrativo gana para el comportamiento. Señala la discrepancia en `KNOWN_GAPS.md` en vez de adivinar.

Las anotaciones de tipo usan la sintaxis nativa de Python (`X | Y`, `list[int]`) disponible desde Python 3.10/3.9 — no hace falta `from __future__ import annotations`. El proyecto exige Python **3.11 o superior**; nada en este documento es sintaxis exclusiva de una versión más nueva.

---

## 2. Núcleo del motor

### 2.1 `src/engine/core/settings.py`

Sin clases. Sólo constantes a nivel de módulo — pero no las preferencias del
jugador (daltonismo, subtítulos): ésas viven en `user_settings.py` porque se
persisten y validan, y una constante de este módulo nunca cambia en caliente.

```python
from pathlib import Path
from typing import Final

INTERNAL_WIDTH: int = 800
INTERNAL_HEIGHT: int = 600
TARGET_FPS: int = 60
#: Factor de escala de ventana, aplicado por SDL (`pygame.SCALED`). Se lee de
#: la variable de entorno `LOI_DISPLAY_SCALE`; por defecto y si no es un
#: entero válido, 1.
DISPLAY_SCALE: int = 1
#: Resolución de referencia heredada (320x224) — el auto-escalado que la usaba
#: es inalcanzable desde que INTERNAL_WIDTH es 800 (AUD-021); se conserva
#: porque las herramientas de asset la citan como resolución de diseño.
REFERENCE_WIDTH: int = 320
REFERENCE_HEIGHT: int = 224
TILE_SIZE: int = 16

# Rutas absolutas: _PROJECT_ROOT / "..." en el código real, no Path("...") relativo
PROJECT_ROOT: Path
ASSETS_DIR: Path
STAGES_DIR: Path
STUDENT_TEMPLATES_DIR: Path

PLAYER_MAX_HEALTH: float = 5.0
GRAVITY: float = 800.0
PLAYER_WALK_SPEED: float = 90.0
#: Velocidad del deslizamiento sostenido en cuesta sin entrada horizontal
#: (AUD-326) — px/s, acotada, no una aceleración en fuga.
PLAYER_SLOPE_SLIDE_SPEED: float = 90.0
PLAYER_JUMP_FORCE: float = -380.0
PLAYER_MAX_FALL_SPEED: float = 500.0
PLAYER_COYOTE_FRAMES: int = 6
PLAYER_DASH_SPEED: float = 200.0
PLAYER_AIR_DASH_LIMIT: int = 1
PLAYER_AIR_JUMPS: int = 1
#: ¿Doble salto y dash requieren desbloqueo? (AUD-238/294). Encendido desde
#: AUD-294 — derrotar a un jefe concede la habilidad de verdad. Los mapas
#: anteriores a esta invariante se eximen uno a uno en
#: ESCENARIOS_CON_HABILIDADES_LIBRES (romperla sin la lista deja 2 de 16
#: mapas imposibles de terminar, medido con `grade_stage`).
PLAYER_SKILLS_REQUIRE_UNLOCK: bool = True
#: Los escenarios entregados antes del candado, exentos (AUD-294). Un mapa
#: nuevo se exime con la propiedad TMX `habilidades_libres`, no aquí.
ESCENARIOS_CON_HABILIDADES_LIBRES: frozenset[str] = frozenset({...})   # 16 claves
PLAYER_SHORT_ATTACK_DURATION: float = 0.15
PLAYER_LONG_ATTACK_DURATION: float = 0.4
PLAYER_COOLDOWN_SHORT: float = 0.0
PLAYER_COOLDOWN_LONG: float = 0.067
BG_COLOR: tuple[int, int, int] = (15, 15, 40)
#: Píxeles más allá del encuadre que se siguen simulando/dibujando (AUD-279).
#: 0 apaga el culling entero — útil para descartarlo como sospechoso ante un
#: enemigo que no se mueve.
CULLING_MARGEN: int = 800
#: ¿Una excepción en `update()` de una entidad se retira sola en vez de
#: tumbar el fotograma? (AUD-289). `True` por defecto: el motor ejecuta
#: código de 26 entregas de estudiante, y un `IndexError` ajeno no debe
#: devolver a todo el mundo al título. `False` para depurar el motor mismo.
AISLAR_FALLOS_DE_ENTIDAD: bool = True
COMBO_WINDOW: float = 0.5
#: Tupla, no lista (AUD-021) — mutable sería reescribible desde cualquier
#: punto del proceso, incluida una prueba que olvide restaurarla.
COMBO_DAMAGE_MULT: Final[tuple[float, ...]] = (1.0, 1.5, 2.0)
COMBO_MAX: int = 3
```

> **AUD-455 — reescritura completa.** Esta sección se autodeclaraba "lista
> completa" y le faltaba más o menos la mitad de las constantes reales:
> `REFERENCE_WIDTH/HEIGHT`, `PROJECT_ROOT`, `PLAYER_SLOPE_SLIDE_SPEED`,
> `PLAYER_AIR_JUMPS`, `PLAYER_SKILLS_REQUIRE_UNLOCK`,
> `ESCENARIOS_CON_HABILIDADES_LIBRES`, `BG_COLOR`, `CULLING_MARGEN`,
> `AISLAR_FALLOS_DE_ENTIDAD`, `COMBO_WINDOW`, `COMBO_DAMAGE_MULT`,
> `COMBO_MAX`. Además, `DISPLAY_SCALE` no es el literal `1` que mostraba:
> se lee de la variable de entorno `LOI_DISPLAY_SCALE`. Verificado contra
> `src/engine/core/settings.py`.

### 2.2 `src/engine/core/clock.py`

```python
MAX_FRAME_TIME: float = 0.05                        # tope de tirón, 20 FPS suelo
FIXED_DT: float = 1.0 / settings.TARGET_FPS          # AUD-390 — paso de simulación fijo
MAX_PASOS_POR_FOTOGRAMA: int = 5                     # contra la espiral de la muerte
FOTOGRAMAS_EN_EL_HISTORIAL: int = 180                # para los cuantiles de F11 (AUD-346)
FUENTE_HITSTOP: str = "hitstop"                      # dt_mundo la ignora a propósito
FUENTE_MANUAL: str = "manual"                        # la que usa `clock.time_scale = x`

class DeltaClock:
    """Tres deltas por fotograma, no uno (AUD-118/119):
    `dt` — escalado por TODOS los efectos, mueve la simulación de juego.
    `unscaled_dt` — tiempo real, mueve lo que debe seguir mientras el mundo
    está congelado (el propio hit-stop, transiciones, menú de pausa).
    `dt_mundo` — escalado por todo MENOS el hit-stop; mueve la maquinaria del
    nivel (bloques rítmicos, láseres, cintas) para que un golpe no la pare."""

    def __init__(self) -> None: ...

    def escalar(self, fuente: str, valor: float) -> None:
        """Registra el factor de tiempo que pide `fuente`. Varias fuentes se
        MULTIPLICAN (AUD-118) — antes cámara lenta y hit-stop competían por
        un único `time_scale` y uno pisaba al otro al soltarse."""
    def restaurar(self, fuente: str) -> None:
        """Retira el factor de `fuente`. Retirar lo que no está no es error."""
    def escalas_activas(self) -> dict[str, float]:
        """Copia de las fuentes activas ahora mismo — depuración y pruebas."""

    @property
    def time_scale(self) -> float:
        """La escala efectiva: producto de todas las fuentes activas."""
    @time_scale.setter
    def time_scale(self, valor: float) -> None:
        """Compatibilidad con `clock.time_scale = x` (lo escriben las 26
        clases de escenario de estudiante). `1.0` retira la fuente manual en
        vez de registrar un factor neutro."""

    def tick(self) -> float:
        """Avanza un fotograma; devuelve `dt` (el delta escalado)."""
    def pasos_fijos(self, dt: float | None = None) -> Iterator[float]:
        """Generador: cede `FIXED_DT` tantas veces como quepa en el tiempo
        acumulado desde el último fotograma, con acarreo (AUD-390) — a 120
        fps la mitad de los fotogramas no simularían sin el acarreo. `dt=None`
        usa el del último `tick()`. Tope `MAX_PASOS_POR_FOTOGRAMA`: por
        encima se tira el sobrante en vez de intentar alcanzarse (espiral de
        la muerte)."""
    def historial_ms(self) -> tuple[float, ...]:
        """Milisegundos REALES (no escalados) de los últimos fotogramas."""
    def estadisticas(self) -> dict[str, float]:
        """P50/P95/P99/media/peor del historial (F11, AUD-346)."""

    @property
    def dt(self) -> float: ...
    @property
    def unscaled_dt(self) -> float: ...
    @property
    def dt_mundo(self) -> float: ...
    @property
    def fps(self) -> float: ...
```

> **AUD-455 — reescritura completa.** `time_scale` documentaba "atributo
> público mutable" y es una `@property` calculada (producto de fuentes con
> nombre, AUD-118) con setter de compatibilidad. Faltaban por completo el
> paso fijo de simulación (`pasos_fijos`, `FIXED_DT`, AUD-390/GAP-036), las
> propiedades `unscaled_dt`/`dt_mundo` (AUD-119 — el hit-stop no debe parar
> la maquinaria del nivel) y las estadísticas de fotograma para F11
> (`historial_ms`, `estadisticas`, AUD-346). Verificado contra
> `src/engine/core/clock.py`.

### 2.3 `src/engine/core/event_bus.py`

```python
from typing import Callable, Any

class EventBus:
    """Bus de eventos publicación/suscripción de instancia (v1.1.0: antes era una clase estática).

    AUD-028 — referencias DÉBILES. `subscribe` no mantiene vivo al suscriptor:
    quien se suscribe (un método ligado, una clausura guardada en un atributo)
    tiene que seguir vivo por su cuenta. Una escena que se descarta sin
    desuscribirse es recolectable, y sus manejadores muertos se sueltan en el
    siguiente `dispatch()` con un aviso — no siguen disparándose para siempre
    sobre un objeto destruido."""

    def __init__(self) -> None: ...

    def subscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """Suscribirse dos veces es un no-op idempotente (una escena se
        rearma tras un respawn sin duplicar el manejador)."""
    def unsubscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """Desuscribir algo que no está suscrito es un no-op, no un aviso."""
    def unsubscribe_all(self, events: list[str], callback: Callable[..., None]) -> None: ...
    def subscriber_count(self) -> int:
        """Total de callbacks vivos en todos los eventos."""

    def emit(self, event_name: str, **data: Any) -> None:
        """Encola el evento; se despacha al principio del siguiente fotograma."""

    def dispatch(self) -> None:
        """La llama App una vez por fotograma, antes de update() de la escena.
        Vacía la cola. Reentrante a propósito: un evento emitido dentro de un
        manejador se encola para el fotograma siguiente, no se despacha en
        el momento — así un bucle emit→handler→emit no puede colgarse."""

    def clear(self) -> None:
        """Borra todos los suscriptores y eventos pendientes. Útil para pruebas."""

    @property
    def queue_snapshot(self) -> list[tuple[str, dict[str, object]]]:
        """Copia de sólo lectura de la cola pendiente. La usa `debug_overlay.py` (F11)."""
    @property
    def subscribers_snapshot(self) -> dict[str, list[str]]:
        """Nombre de evento → nombres de los callbacks vivos suscritos."""


# AUD-307: estas funciones de conveniencia a nivel de módulo **no existen** en
# el código (verificado con AST el 2026-08-06). El bus es de instancia: crea un
# EventBus y pásalo. `App` ya inyecta el suyo en los escenarios.
```

> **AUD-455.** Faltaban las propiedades `queue_snapshot` y
> `subscribers_snapshot` (públicas, usadas por el panel de depuración F11) y
> el diseño de referencias débiles (AUD-028) no se mencionaba en absoluto —
> es el comportamiento que explica por qué una lambda desechable suscrita
> sin guardar su referencia deja de disparar en silencio. Verificado contra
> `src/engine/core/event_bus.py`.

**Carga útil (payload) estándar de eventos** (claves exactas de `**data` — ver `23_DATA_SCHEMAS.md` §2 para la tabla completa):

| Evento | Claves |
|---|---|
| `PLAYER_DAMAGED` | `amount: float`, `source: tuple[float, float]` |
| `PLAYER_HEALED` | `amount: float` |
| `PLAYER_DIED` | *(no keys)* |
| `CHECKPOINT_REACHED` | `checkpoint_id: int` |
| `ENEMY_DIED` | `entity_id: str`, `position: tuple[float, float]` |
| `STAGE_COMPLETE` | *(no keys)* |
| `BOSS_PHASE_CHANGED` | `boss_name: str`, `phase: int`, `phase_count: int`, `new_max_health: float` |
| `SHOW_MESSAGE` | `text: str`, `duration: float` |
| `HIDE_MESSAGE` | *(no keys)* |

> **AUD-455.** `BOSS_PHASE_CHANGED` traía sólo `phase: int` aquí; el payload
> real tiene 4 claves (verificado contra `23_DATA_SCHEMAS.md` §2, que ya
> tenía la corrección — esta tabla se había quedado atrás de la de allí).

### 2.4 `src/engine/core/app.py`

```python
import pygame
from typing import Protocol

class EscenaConRutaDeGPU(Protocol):
    """Contrato escrito (AUD-371) para la escena que separa mundo/UI en su
    dibujado (AUD-343) — antes era duck typing sin declarar en ningún sitio.
    Sin `@runtime_checkable` a propósito: desde Python 3.12 `isinstance`
    contra un Protocol usa `getattr_static`, que no ve atributos dinámicos
    (rompía `MagicMock(spec=...)` y una escena de estudiante con `__getattr__`).
    La comprobación real sigue siendo por pato, vía `_soporta`."""
    def dibujar_mundo(self, destino: pygame.Surface) -> None: ...
    def dibujar_ui(self, destino: pygame.Surface) -> None: ...

def modo_daltonico_gl(ajustes: object | None) -> int:
    """Traduce `ajustes.colorblind_mode` al entero 0-3 que espera el
    sombreador (AUD-252 — el eslabón que le faltaba a `colorblind_frag` para
    activarse alguna vez). Un valor no reconocido devuelve 0 en vez de
    reventar."""

class App:
    def __init__(self, use_gl: bool = True, depurar: bool = False,
                semilla: int | None = None) -> None:
        """
        `depurar` activa el registro a consola además de a fichero. `semilla`
        fija el generador de azar del proceso (AUD-375/GAP-042) para poder
        repetir una partida — `None` inventa una y la anota en el registro.

        Inicializa pygame, pygame.mixer, crea internal_surface (settings.INTERNAL_WIDTH x settings.INTERNAL_HEIGHT)
        y window_surface, construye DeltaClock, EventBus, InputManager, AudioManager,
        SceneManager, GameContext. Opcionalmente inicializa el renderer de ModernGL.
        Carga UserSettings desde disco y lo aplica. Apila SplashScene en el SceneManager.
        """

    def run(self) -> None:
        """Entra al bucle principal. No retorna hasta que se cierra el juego."""

    def _shutdown(self) -> None:
        """Detiene la música, llama a pygame.quit()."""

    def _init_pygame(self) -> None: ...
    def _init_gl(self) -> None: ...
    def _init_subsystems(self) -> None: ...
    def _draw(self) -> None: ...

    internal_surface: pygame.Surface
    clock: "DeltaClock"
    scene_manager: "SceneManager"
    input_manager: "InputManager"
    audio_manager: "AudioManager"
    event_bus: "EventBus"
    context: "GameContext"
    user_settings: "UserSettings"
    debug_overlay: "DebugOverlay"    # AUD-283 — consola F11; vive en App, no en StageScene
    plugins: "GestorDePlugins"       # AUD-296 — descubiertos antes de montar el resto
    running: bool
```

> **AUD-455.** `__init__` tenía sólo `use_gl` — faltaban `depurar` y
> `semilla`. Faltaban por completo el Protocol `EscenaConRutaDeGPU` y la
> función `modo_daltonico_gl()` (ambos a nivel de módulo, ya citados desde
> `74_TUBERIA_DE_GPU.md`), y los atributos `debug_overlay`/`plugins`.
> Verificado contra `src/engine/core/app.py`.

### 2.5 `src/engine/core/game_context.py`

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Any

class GameContext:
    """Contenedor de inyección de dependencias. Contiene todos los subsistemas
    del motor compartidos. Se pasa a cada escena vía BaseScene.__init__(self, context)."""

    def __init__(
        self,
        input_manager: InputManager,
        audio_manager: AudioManager,
        scene_manager: SceneManager,
        event_bus: EventBus,
        clock: DeltaClock | None = None,
        save_manager: SaveManager | None = None,
    ) -> None: ...

    @property
    def audio(self) -> Any:
        """Shortcut to self.audio_manager."""

    def quit(self) -> None:
        """Señala al bucle principal que debe salir."""

    input_manager: InputManager
    audio_manager: AudioManager
    scene_manager: SceneManager
    event_bus: EventBus
    clock: DeltaClock | None
    save_manager: SaveManager
    pending_load: SaveData | None
    running: bool
    banderas: dict[str, bool]        # AUD-251: banderas de mundo de `set_flag:` en diálogo;
                                      # sobreviven al cambio de escena, bajan a SaveData.zone_flags
    lote_de_sprites: Any             # AUD-342: lote de sprites de GPU que la escena rellena
                                      # para el renderer; None si no hay ruta de GPU activa
    usar_gl: bool                    # AUD-343: True sólo si el contexto GL se montó de verdad;
                                      # False por defecto (CI nunca tiene GPU)
```

> **AUD-455.** `banderas`, `lote_de_sprites` y `usar_gl` no estaban
> documentados — verificado leyendo `src/engine/core/game_context.py`
> directamente (no sólo el docstring de la clase, que tampoco los menciona).

### 2.6 `src/engine/core/save_data.py`

```python
from pydantic import BaseModel, Field

SAVE_VERSION: int = 4
MAX_SLOTS: int = 5
VERSION_CON_INVENTARIO: int = 3   # AUD-292/438 — primera versión que guarda inventario en el slot
VERSION_CON_LOGROS: int = 4       # primera versión que guarda logros en el slot

class SaveData(BaseModel):
    """Modelo pydantic — validado, no un `@dataclass` sencillo. La partida se
    lleva TODO lo del jugador (AUD-292/438): antes vivía repartido en
    ficheros globales (score.json, inventory.json, achievements.json), uno
    por instalación, así que cargar el slot 2 dejaba el dinero del slot 1."""

    slot_id: int = 0
    timestamp: str = ""
    version: int = SAVE_VERSION
    stage_id: str = ""
    stage_index: int = 0
    checkpoint_x: float = 0.0      # redondeado a 1 decimal por validador
    checkpoint_y: float = 0.0
    health: float = 5.0            # redondeado a 1 decimal por validador
    max_health: float = 5.0
    zone_flags: dict[str, bool] = Field(default_factory=dict)
    completed_stages: list[str] = Field(default_factory=list)
    exp_total: int = 0                                    # AUD-267
    score: int = 0                                        # AUD-292
    inventory_items: dict[str, int] = Field(default_factory=dict)
    inventory_equipped: dict[str, str] = Field(default_factory=dict)
    exp_estado: dict[str, int] = Field(default_factory=dict)   # los 3 números de ExperienceSystem, no sólo el total
    arbol: dict[str, int] = Field(default_factory=dict)        # AUD-293 — rangos del árbol de habilidades
    profile_name: str = ""         # AUD-442, recortado a LARGO_MAXIMO_DEL_NOMBRE por validador
    character: str = "paburu"
    play_time: float = 0.0         # segundos acumulados; lo suma SaveManager.anotar_tiempo_jugado
    version_original: int = SAVE_VERSION   # AUD-438 — con qué versión se escribió, ANTES de migrar
    logros: dict[str, dict[str, Any]] = Field(default_factory=dict)   # AUD-438

    LARGO_MAXIMO_DEL_NOMBRE: ClassVar[int] = 24

    def to_dict(self) -> dict[str, Any]:
        """`model_dump()` + asigna `timestamp` UTC con zona si está vacío."""
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SaveData:
        """La vía real de lectura desde disco. Anota `version_original` antes
        de migrar — hacerlo dentro de `migrate()` marcaría una `SaveData()`
        nueva como versión 0 y le daría la indulgencia de las partidas antiguas."""
    @staticmethod
    def migrate(data: dict[str, Any]) -> dict[str, Any]:
        """Única fuente de verdad de la migración (AUD-031) — escalera de
        `if ver < N` hasta `SAVE_VERSION`."""
    def to_json(self) -> bytes:
        """Serializa a JSON **firmado** (AUD-295, vía `engine.core.integridad`)."""
    @classmethod
    def from_json(cls, raw: bytes | str) -> SaveData:
        """Lanza `ValueError` si la firma no cuadra. Los ficheros pre-AUD-295
        sin firma se aceptan igualmente."""
```

> **AUD-455 — reescritura completa.** `SaveData` dejó de ser un `@dataclass`
> de 10 campos hace varias fases: es un `BaseModel` de pydantic con 21 campos
> (`SAVE_VERSION` real es 4, no 1) que absorbió el inventario, la
> puntuación, la experiencia, el árbol de habilidades y los logros —antes
> ficheros globales por instalación, ahora parte de la partida. Faltaban
> `to_json`/`from_json` (firmados, AUD-295) por completo. Verificado contra
> `src/engine/core/save_data.py`.

### 2.7 `src/engine/core/save_manager.py`

```python
class SaveManager:
    """Las partidas guardadas, en el directorio del usuario (AUD-157 — no en
    el árbol del proyecto, que puede ser de sólo lectura empaquetado)."""

    SAVES_DIR: Path = user_data_dir() / "saves"

    def __init__(self) -> None:
        """Migra partidas del sitio antiguo si hacen falta; se registra como
        el gestor activo del proceso (lo consulta `ruta_del_perfil`)."""

    def save(self, slot: int, data: SaveData) -> str:
        """Persiste en slot_{slot}.json, escritura atómica. Lanza ValueError si slot ∉ [1, MAX_SLOTS]."""

    def load(self, slot: int, *, activar: bool = False) -> SaveData | None:
        """Devuelve None si falta o está corrupto. Con `activar=True` además
        declara este slot como el que se está jugando (AUD-441) — deliberadamente
        no es un efecto secundario de leer, porque la pantalla de selección
        carga las 5 ranuras sólo para pintarlas."""

    def delete(self, slot: int) -> None: ...

    def list_slots(self) -> list[dict[str, Any]]:
        """Resumen (slot, stage_id, timestamp, health, max_health) de cada
        ranura que existe."""
    def has_saves(self) -> bool: ...
    def newest_slot(self) -> int | None:
        """Por marca de tiempo. Ya no decide el autoguardado (ver `ranura_activa`, AUD-441)."""
    def anotar_tiempo_jugado(self, data: SaveData) -> None:
        """Acumula a `data.play_time` los segundos desde la última anotación
        (reloj monótono) y reinicia el contador."""
    def auto_save(
        self, stage_id: str, stage_index: int,
        checkpoint_x: float, checkpoint_y: float,
        health: float, max_health: float,
        zone_flags: dict[str, bool] | None = None,
        exp_total: int | None = None,
    ) -> str | None:
        """Lee-modifica-escribe sobre `ranura_activa` (o `newest_slot()` de
        respaldo) — nunca reconstruye la partida desde cero (AUD-005: eso
        borraba `completed_stages` en cada autoguardado). Las banderas se
        FUNDEN, no se sustituyen; la experiencia sólo sube."""

    @property
    def ranura_activa(self) -> int | None:
        """Qué partida se está jugando. La declara quien carga/crea, no se
        deduce de `newest_slot()` (AUD-441 — deducir rompía con dos partidas en disco)."""
    @ranura_activa.setter
    def ranura_activa(self, slot: int | None) -> None:
        """Lanza ValueError si `slot` está fuera de [1, MAX_SLOTS]."""


# ── funciones de módulo ──────────────────────────────────────────
def ruta_del_perfil(nombre: str) -> Path:
    """Ruta de un fichero de estado (bestiario, récords) aislado por partida
    activa (AUD-450) — dentro de `SAVES_DIR/slot_{ranura}/`, o la ruta
    compartida de siempre sin partida activa."""
def escribir_atomicamente(path: Path, datos: bytes) -> None:
    """Temporal + fsync + os.replace — la misma receta que `save()`, exportada (AUD-316)."""
def migrar_desde_el_arbol(nuevo: Path, antiguo: Path) -> None:
    """Copia una vez desde la ruta vieja del árbol si el destino no existe (AUD-337)."""
def volcar_estado_en(data: SaveData) -> None:
    """Copia inventario/puntuación/experiencia/árbol/logros VIVOS dentro de `data` (AUD-292/438). No lanza."""
def aplicar_estado_de(data: SaveData) -> None:
    """Lo contrario de `volcar_estado_en` — se llama al cargar. No lanza."""
```

> **AUD-455 — reescritura completa.** `SAVES_DIR` documentaba `Path("saves")`
> relativo; el real es `user_data_dir() / "saves"` (AUD-157 — el mismo
> patrón ya corregido en preferencias y logros, que se había quedado sin
> aplicar aquí, el estado más importante de todos). `load()` no tenía el
> parámetro `activar`. Faltaban por completo `ranura_activa`
> (propiedad+setter), `anotar_tiempo_jugado`, `list_slots`, `has_saves`,
> `newest_slot`, `auto_save`, y las cinco funciones de módulo
> (`ruta_del_perfil`, `escribir_atomicamente`, `migrar_desde_el_arbol`,
> `volcar_estado_en`, `aplicar_estado_de`). Verificado contra
> `src/engine/core/save_manager.py`.

    def list_slots(self) -> list[dict[str, Any]]:
        """Devuelve metadatos de las ranuras no vacías (slot, stage_id, timestamp, health, max_health)."""

    def has_saves(self) -> bool: ...

    def newest_slot(self) -> int | None: ...

    def auto_save(self, stage_id: str, stage_index: int,
                  checkpoint_x: float, checkpoint_y: float,
                  health: float, max_health: float) -> str | None: ...
```

---

## 3. Entrada del motor

### 3.1 `src/engine/input/action_map.py`

```python
from enum import Enum, auto

class Action(Enum):
    """Acciones abstractas del juego. Las asignaciones ligan teclas físicas a estas acciones."""
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    JUMP = auto()
    CROUCH = auto()
    SHORT_ATTACK = auto()
    LONG_ATTACK = auto()
    DASH = auto()
    GRAB = auto()
    RANGED_ATTACK = auto()          # F4.2 — ataque a distancia (arco)
    CONFIRM = auto()
    CANCEL = auto()
    PAUSE = auto()
    # Paneles de aprendizaje superpuestos (ARC-034)
    LEARN_MATH = auto()
    LEARN_PHYSICS = auto()
    LEARN_COLLISION = auto()
    LEARN_FSM = auto()
    LEARN_RENDER = auto()
    LEARN_AUDIO = auto()
    LEARN_PERF = auto()
    LEARN_CONTROLS = auto()
    LEARN_HELP = auto()
    OPEN_BESTIARY = auto()
    TOGGLE_MUTE = auto()            # AUD-022
    BULLET_TIME = auto()            # AUD-260 — se mantiene pulsada, no se conmuta

DEFAULT_KEY_BINDINGS: dict[Action, list[int]]   # constantes de tecla de pygame
CONTROLLER_DEADZONE: float = 0.25
CONTROLLER_AXIS_LEFT_X: int = 0
CONTROLLER_AXIS_LEFT_Y: int = 1
```

> **AUD-455.** El enum `Action` tenía 12 de sus 21 miembros reales — faltaban
> `GRAB`, `RANGED_ATTACK` y los 9 paneles de aprendizaje/mando
> (`LEARN_*`, `OPEN_BESTIARY`, `TOGGLE_MUTE`, `BULLET_TIME`). Verificado
> contra `src/engine/input/action_map.py`.

### 3.2 `src/engine/input/input_manager.py`

```python
class InputManager:
    VENTANA_DE_BUFFER: int = 8   # fotogramas (~133 ms a 60 Hz)

    def __init__(self) -> None: ...

    def pump(self, events: list[pygame.event.Event]) -> None:
        """La llama App una vez por fotograma con la lista de eventos actual."""

    def is_action_just_pressed(self, action: "Action") -> bool:
        """True sólo en el fotograma en que se activó la acción."""
    def is_action_pressed(self, action: "Action") -> bool:
        """Alias de `is_action_just_pressed`."""

    def is_action_held(self, action: "Action") -> bool:
        """True en cada fotograma mientras se mantiene la acción. Si la
        preferencia `hold_to_press` está activa (AUD-126), las acciones de
        `GRAB`/`DASH`/`CROUCH`/`LONG_ATTACK` se comportan como conmutador."""

    def is_action_released(self, action: "Action") -> bool:
        """True sólo en el fotograma en que se soltó la acción."""

    def pulsada_en_buffer(self, action: "Action", ventana: int | None = None) -> bool:
        """¿Se pulsó esta acción en los últimos `ventana` fotogramas? (AUD-373,
        cierra GAP-040). `ventana` por defecto es `VENTANA_DE_BUFFER`."""

    def consumir_buffer(self, action: "Action") -> None:
        """Da la pulsación bufferizada por gastada."""

    def consume(self, action: "Action") -> None:
        """Consume la acción: `is_action_just_pressed` devuelve False el resto
        del fotograma."""

    def rebind(self, action: "Action", keys: list[int]) -> None:
        """Reasigna una acción a una nueva lista de constantes de tecla."""

    def is_raw_key_pressed(self, key: int) -> bool:
        """True sólo en el fotograma en que esta tecla física se pulsó
        (incluye teclas sintetizadas desde el mando — AUD-320)."""

    @staticmethod
    def is_raw_key_held(key: int) -> bool:
        """True en cada fotograma mientras esta tecla física está pulsada."""
```

> **AUD-455.** Faltaban 7 métodos públicos reales: `is_action_just_pressed`
> (del que `is_action_pressed` es alias), `pulsada_en_buffer`,
> `consumir_buffer`, `consume`, `rebind`, `is_raw_key_pressed`,
> `is_raw_key_held`, y la constante `VENTANA_DE_BUFFER`. Verificado contra
> `src/engine/input/input_manager.py`.

---

## 4. Audio del motor

### 4.1 `src/engine/audio/sound_bank.py`

```python
class SoundBank:
    def __init__(self) -> None:
        """Explora assets/sfx/ en busca de ficheros .wav al construirse."""

    def load_all(self) -> None:
        """Explora assets/sfx/ recursivamente y registra cada fichero .wav."""

    def load(self, name: str, path: str | Path) -> None:
        """Registra un sonido por nombre, cargándolo desde la ruta dada."""

    def get(self, name: str) -> pygame.mixer.Sound | None:
        """Obtiene un sonido registrado por nombre. Devuelve None si no se encuentra."""

    def play(self, name: str, loops: int = 0, volume: float = 1.0,
             pitch: float = 1.0, pan: tuple[float, float] | None = None) -> None:
        """Reproduce un sonido registrado. `pitch` remuestrea con numpy (AUD-280);
        `pan` fija el volumen por canal L/R. Se salta en silencio si no se encuentra."""

    def contains(self, name: str) -> bool:
        """Indica si hay un sonido registrado con ese nombre."""

    def clear(self) -> None:
        """Vacía el banco y reinicia el control de polifonía (`ControlDeVoces`)."""
```


### 4.2 `src/engine/audio/audio_manager.py`

```python
class AudioManager:
    def __init__(self) -> None: ...

    def play_music(self, path: str | Path, loops: int = -1, fundido_ms: int = 0) -> None:
        """Reproduce música de fondo. -1 loops = infinito. `fundido_ms` funde la
        entrada (AUD-313; SDL_mixer no permite crossfade real entre pistas).
        Degrada en silencio si falla."""
    def posicion_musica(self) -> float | None:
        """Segundos reproducidos de la pista actual, o None si no hay música (AUD-137)."""
    def stop_music(self) -> None: ...
    def pause_music(self) -> None: ...
    def resume_music(self) -> None: ...
    def play_sfx(self, name: str, volume: float = 1.0) -> None:
        """Reproduce un efecto de sonido del banco de sonidos al volumen de SFX actual."""
    def play_stinger(self, name: str, volume: float = 0.8) -> None: ...
    def play_ambient(self, path: str | Path, volume: float = 0.5, loops: int = -1) -> None: ...
    def stop_ambient(self) -> None: ...
    def set_ambient_volume(self, volume: float) -> None: ...
    def crossfade_ambient(self, path: str | Path, duration: float = 2.0, volume: float = 0.5) -> None: ...
    def play_sfx_at(self, name: str, world_x: float, screen_center_x: float | None = None,
                    volume: float = 1.0, suelo: float = 0.0) -> None:
        """Paneo estéreo por posición X relativa al centro de cámara. AUD-348: el
        volumen se desvanece linealmente con la distancia hasta `RADIO_AUDIBLE_EFECTOS`
        (2000 px); `suelo` fija un volumen mínimo para efectos que no deben desaparecer."""

    # ── AUD-144: buses de mezcla (música/efectos/voz/ambiente) y ducking ──
    def play_voz(self, name: str, volume: float = 1.0, duracion_duck: float = 0.0) -> None:
        """Reproduce una línea de voz y agacha la música por su cuenta."""
    def play_sfx_critico(self, name: str, volume: float = 1.0,
                         world_x: float | None = None, screen_center_x: float | None = None) -> None:
        """Efecto que agacha la música un 30% un segundo (AUD-284): muerte de
        jefe, logro, final de escenario."""
    def agachar_musica(self, segundos: float = 0.0) -> None: ...
    def soltar_musica(self) -> None: ...
    def volumen_de_bus(self, bus: str) -> float: ...
    def ajustar_bus(self, bus: str, volumen: float) -> None:
        """Ajusta un bus (`BUS_MUSICA`/`BUS_EFECTOS`/`BUS_AMBIENTE`/`BUS_VOZ`, ver
        `mixer_buses.py`) y sincroniza los campos legados (`_music_volume`, etc.)."""
    def update(self, dt: float) -> None:
        """Avanza el temporizador de ducking. Debe recibir `dt` real, nunca escalado."""

    def set_music_volume(self, volume: float) -> None: ...
    def set_sfx_volume(self, volume: float) -> None: ...
    def toggle_mute(self) -> None: ...

    @property
    def music_volume(self) -> float: ...
    @music_volume.setter
    def music_volume(self, value: float) -> None: ...
    @property
    def sfx_volume(self) -> float: ...
    @sfx_volume.setter
    def sfx_volume(self, value: float) -> None: ...
    @property
    def is_muted(self) -> bool: ...
    @property
    def current_music(self) -> str | None: ...

# AUD-307: `DynamicMusicSystem` NO vive en este módulo — se documenta en §4.3
# (`src/framework/audio/dynamic_music.py`). Aquí termina `AudioManager`.
```

> **AUD-455.** Faltaban por completo los métodos y propiedades del sistema de
> buses de mezcla (AUD-144): `play_voz`, `play_sfx_critico`, `agachar_musica`,
> `soltar_musica`, `volumen_de_bus`, `ajustar_bus`, `update`, `set_ambient_volume`,
> `posicion_musica`, y las propiedades `sfx_volume`/`is_muted`/`current_music`.
> `play_music` y `play_sfx_at` tenían parámetros reales sin documentar
> (`fundido_ms`, `suelo`) y `play_sfx_at` documentaba un valor por defecto
> (`160`) que no es el real (`None`, resuelto internamente contra
> `settings.INTERNAL_WIDTH`). Verificado contra `src/engine/audio/audio_manager.py`.

<!-- cita-historica -->
> **AUD-022 / AUD-312 — la música dinámica no vive en `AudioManager`.** Los
> métodos `play_dynamic_music`, `stop_dynamic_music`, `set_music_intensity` y
> `update_dynamic_music` estuvieron documentados aquí y **no existen en la
> clase**: eran una segunda implementación completa de música por capas que no
> llamaba nadie, y AUD-022 la retiró. La viva es
> `framework.audio.DynamicMusicSystem`, y quien la conduce es `StageScene`.
<!-- /cita-historica -->

### 4.3 `src/framework/audio/dynamic_music.py`

```python
class DynamicMusicSystem:
    INTENSITY_CALM = 0
    INTENSITY_COMBAT = 1
    INTENSITY_BOSS = 2

    def __init__(self, audio_manager: AudioManager) -> None: ...
    def set_zone(self, zone: int, bgm_track: str) -> None:
        """Fija la zona actual y el nombre de la pista BGM base."""
    def set_intensity(self, level: int) -> None:
        """Cambia a un nuevo nivel de intensidad con cruce (crossfade)."""
    def detect_intensity_from_state(self, has_boss: bool, has_alive_enemies: bool) -> int:
        """Detecta automáticamente la intensidad a partir del estado del juego."""
    def _get_track_for_intensity(self, level: int) -> Path | None: ...
```

> **AUD-307.** La clase **no** expone volumen ni mute: `sfx_volume` e `is_muted`
> son de `AudioManager` (§4.2), no de la música dinámica.

---

## 5. Utilidades del motor

### 5.1 `src/engine/utils/math_utils.py`

```python
def lerp(a: float, b: float, t: float) -> float: ...
def clamp(value: float, min_v: float, max_v: float) -> float: ...

def ease_in_quad(t: float) -> float: ...
def ease_out_quad(t: float) -> float: ...
def ease_in_out_quad(t: float) -> float: ...
def ease_in_cubic(t: float) -> float: ...
def ease_out_cubic(t: float) -> float: ...
def ease_out_bounce(t: float) -> float: ...
def ease_out_elastic(t: float) -> float: ...
def ease_in_sine(t: float) -> float: ...
def ease_out_sine(t: float) -> float: ...
# Implementación propia (no envuelven pytweening — ver 10_LIBRARIES_AND_DEPENDENCIES.md);
# t debe estar en [0, 1]; comportamiento indefinido fuera de ese rango.

def vec2_normalize(v: pygame.Vector2) -> pygame.Vector2: ...
def vec2_length(v: pygame.Vector2) -> float: ...
def vec2_dot(a: pygame.Vector2, b: pygame.Vector2) -> float: ...
def vec2_distance(a: pygame.Vector2, b: pygame.Vector2) -> float: ...
```
> **AUD-455.** Los cuatro helpers de vectores toman `pygame.Vector2`, no
> `tuple[float, float]` — un `tuple` no tiene `.x`/`.y` y fallaría en tiempo de
> ejecución. Verificado contra `src/engine/utils/math_utils.py`.

### 5.2 `src/engine/utils/asset_loader.py`

```python
from pathlib import Path

class AssetLoader:
    """Todos los métodos son classmethods; la caché interna es un dict a nivel de clase, indexado por str(path)."""

    @classmethod
    def load_image(
        cls,
        path: str | Path,
        *,
        scale: float | None = None,
        size: tuple[int, int] | None = None,
        alpha: bool = True,
    ) -> pygame.Surface: ...

    @classmethod
    def load_sound(cls, path: str | Path) -> pygame.mixer.Sound | None: ...

    @classmethod
    def load_sprite_sheet(
        cls, path: str | Path, frame_width: int, frame_height: int,
    ) -> list[pygame.Surface]: ...

    @classmethod
    def load_font(cls, path: str | Path | None, size: int) -> pygame.font.Font: ...

    @classmethod
    def clear_cache(cls) -> None:
        """Vacía la caché incondicionalmente. Uso: teardown de pruebas y cierre."""

    @classmethod
    def enter_scope(cls) -> None:
        """Registra un consumidor (una escena) de la caché al entrar."""

    @classmethod
    def leave_scope(cls) -> None:
        """Libera un consumidor; sólo limpia la caché cuando el último se va
        (AUD-025 — antes una escena en pausa perdía sus superficies porque
        `on_exit` limpiaba la caché global sin contar referencias)."""
```

### 5.3 `src/engine/utils/sprite_atlas.py`

<!-- cita-historica -->
> **AUD-168.** Esta sección documentaba `src/engine/utils/spritesheet.py` y una
> clase `SpriteSheet` con `get_frame`/`get_frames`/`frame_count`. AUD-098 ya
> había retirado ese módulo por ser una segunda implementación muerta que nadie
> importaba, y corrigió `03_ARCHITECTURE.md` — pero este documento se quedó
> atrás. El recorte de hojas de sprites lo hace `AssetLoader.load_sprite_sheet`,
> que devuelve una lista de superficies; el empaquetado en atlas lo hace
> `SpriteAtlas`.
<!-- /cita-historica -->

```python
class SpriteAtlas:
    """Empaqueta superficies sueltas en una única imagen con índice de recortes.
    AUD-138 (G1): medido en este proyecto, un atlas NO acelera el dibujado en
    pygame (no hay cambios de textura que ahorrar sin GPU detrás); su valor
    real es cargar ~3x más rápido (menos ficheros que abrir/decodificar) y
    ordenar mejor los assets. La velocidad de dibujo la da `blits()`, no el
    atlas — de ahí `dibujar_lote`."""

    def __init__(self, hoja: pygame.Surface,
                indice: dict[str, pygame.Rect] | None = None) -> None: ...

    @classmethod
    def empaquetar(cls, sprites: dict[str, pygame.Surface],
                   ancho_max: int = 1024) -> SpriteAtlas:
        """Algoritmo de estanterías (shelf packing), no empaquetado óptimo."""

    @classmethod
    def cargar(cls, ruta_png: str | Path) -> SpriteAtlas:
        """Lee `algo.png` y su índice hermano `algo.json`."""

    def guardar(self, ruta_png: str | Path) -> None: ...
    def __contains__(self, nombre: str) -> bool: ...
    def __len__(self) -> int: ...

    @property
    def nombres(self) -> list[str]: ...

    def rect(self, nombre: str) -> pygame.Rect | None: ...
    def recorte(self, nombre: str) -> pygame.Surface | None:
        """Vista (`subsurface`) del recorte, no una copia; se cachea."""

    def dibujar_lote(self, destino: pygame.Surface,
                     ordenes: list[tuple[str, tuple[int, int]]]) -> int:
        """Dibuja muchos sprites con `Surface.blits`. Devuelve cuántos se
        dibujaron; los nombres que no existen se saltan en silencio."""
```

> **AUD-455.** La clase `SpriteAtlas` no tenía ninguna API documentada más
> allá de una frase — le faltaban los 9 métodos/propiedades públicos reales.
> Verificado contra `src/engine/utils/sprite_atlas.py`.

---

## 6. Escena del motor

### 6.1 `src/engine/scene/base_scene.py`

```python
from abc import ABC, abstractmethod

class BaseScene(ABC):
    def __init__(self, context: GameContext) -> None:
        self.context: GameContext = context
        self.params: dict[str, Any] = {}

    @property
    def input(self) -> Any:
        """Atajo a `context.input_manager`."""
    @property
    def audio(self) -> Any:
        """Atajo a `context.audio_manager`."""
    @property
    def events(self) -> Any:
        """Atajo a `context.event_bus`."""

    def awake(self) -> None:
        """Se llama una única vez al instanciar la escena, antes de `on_enter`."""

    def start(self) -> None:
        """Se llama después de `awake`, cuando la escena pasa a activa."""

    def process_events(self, events: list[pygame.event.Event]) -> None:
        """Se llama cada fotograma con la lista de eventos crudos de pygame."""

    @abstractmethod
    def on_enter(self) -> None: ...

    @abstractmethod
    def on_exit(self) -> None: ...

    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None: ...

    def medidas_de_depuracion(self) -> dict[str, object]:
        """Cuentas para la consola de depuración F11 (AUD-283). Vacío por
        defecto; sólo se llama con la consola abierta."""
        return {}

    def on_pause(self) -> None:
        """Sobrescritura opcional. Por defecto: no hace nada."""

    def on_resume(self) -> None:
        """Sobrescritura opcional. Por defecto: no hace nada."""

    def destroy(self) -> None:
        """Se llama una vez cuando la escena se elimina permanentemente, para limpieza final."""
```

> **AUD-455.** Faltaban las propiedades `input`/`audio`/`events` y los
> métodos `awake()`, `start()`, `process_events()`, `medidas_de_depuracion()`
> (AUD-283). Verificado contra `src/engine/scene/base_scene.py`.

### 6.2 `src/engine/scene/scene_manager.py`

```python
class SceneManager:
    def __init__(
        self, context: "GameContext", *,
        title_factory: Callable[["GameContext"], "BaseScene"] | None = None,
        credits_factory: Callable[["GameContext"], "BaseScene"] | None = None,
    ) -> None:
        """Crea el TransitionManager y se suscribe a los eventos STAGE_COMPLETE /
        PLAYER_DIED. `title_factory`/`credits_factory` son inyectables — por
        defecto construyen `TitleScene`/`EndCreditsScene` (AUD-018: el manager
        no importa ninguna escena concreta en el top-level del módulo)."""

    def update(self, dt: float) -> None:
        """Actualiza la escena activa (la cima de la pila)."""

    def cleanup(self) -> None:
        """Cancela la suscripción de todos los oyentes de eventos."""

    def push(self, scene: "BaseScene") -> None:
        """Llama a current.on_pause() si existe una escena, luego scene.awake() → start() → on_enter()."""

    def pop(self) -> None:
        """Llama a current.on_exit() → destroy(), luego al nuevo current.on_resume()."""

    def replace(self, scene: "BaseScene") -> None:
        """Llama a current.on_exit() → destroy(), luego scene.awake() → start() → on_enter()."""

    def set_stage_queue(self, stages: list[type["BaseScene"]]) -> None: ...

    def set_stage_index(self, index: int) -> None: ...

    @property
    def current(self) -> "BaseScene": ...

    @property
    def stack_size(self) -> int: ...

    @property
    def stage_index(self) -> int: ...

    @property
    def transition(self) -> "TransitionManager": ...
```

> **AUD-455.** Faltaban el método público `update(dt)` y los parámetros
> inyectables `title_factory`/`credits_factory` de `__init__`. Verificado
> contra `src/engine/scene/scene_manager.py`.

**Garantía de orden de llamadas (diagrama de secuencia):**

```
push(B) con A como actual:
    A.on_pause()
    B.on_enter()
    # la actual pasa a ser B

pop() con B como actual (A debajo):
    B.on_exit()
    A.on_resume()
    # la actual vuelve a ser A

replace(C) con A como actual:
    A.on_exit()
    C.on_enter()
    # la actual pasa a ser C; A se descarta (no queda en la pila)
```

### 6.2b Orden de llamada del ciclo de vida de `BaseScene`

```
awake()     → se llama una vez cuando la escena se apila por primera vez (antes de on_enter)
start()     → se llama una vez después de awake() (antes de on_enter)
on_enter()  → se llama cada vez que la escena pasa a ser la cima de la pila
update(dt)  → se llama cada fotograma mientras la escena está activa
draw(surf)  → se llama cada fotograma mientras la escena está activa
on_pause()  → se llama cuando se apila otra escena encima
on_resume() → se llama cuando se desapila la escena de encima, volviendo a ésta
on_exit()   → se llama cuando la escena se retira de la pila
destroy()   → se llama una vez después de on_exit() para la limpieza final
```

### 6.3 Transiciones — dónde están de verdad

<!-- cita-historica -->
> **AUD-168.** Aquí había una sección que documentaba
> `src/engine/scene/transitions.py` con cuatro clases —`FadeTransition`,
> `WipeTransition`, `SlideTransition`, `CircleTransition`—, y otros cuatro
> documentos la citaban, uno de ellos con recuento de líneas incluido
> («199 lines»). **Ese módulo no existe y esas clases no existen en ninguna
> parte del árbol.** Las cuatro transiciones son cuatro *modos* de un único
> objeto, `TransitionManager` (§6.4), seleccionados por el método que se llama:
> `start_fade_in`, `start_wipe`, `start_slide`, `start_circle`.
>
> Un contrato de API que describe clases inexistentes es peor que no tener
> contrato: quien lo lee escribe `from src.engine.scene.transitions import
> FadeTransition` y descubre el error en tiempo de importación.
<!-- /cita-historica -->

### 6.4 `src/engine/scenes/transition_manager.py`

```python
from __future__ import annotations

import pygame

FADE_DURATION: float = 0.35

class TransitionManager:
    """Controlador de superposición que soporta transiciones de fundido, barrido, deslizamiento y círculo."""

    def __init__(self) -> None: ...
    def start_fade_out(self, duration: float = FADE_DURATION) -> None: ...
    def start_fade_in(self, duration: float = FADE_DURATION) -> None: ...
    def start_wipe(self, direction: str = "left", duration: float = 0.4,
                   old_surface: pygame.Surface | None = None) -> None: ...
    def start_slide(self, direction: str = "left", duration: float = 0.4,
                    old_surface: pygame.Surface | None = None) -> None: ...
    def start_circle(self, expanding: bool = True, duration: float = 0.4,
                     old_surface: pygame.Surface | None = None) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...

    @property
    def active(self) -> bool: ...
    @property
    def finished(self) -> bool:
        """True si se inició una transición y ya se completó."""
```

---

## 7. UI del motor

### 7.1 `src/engine/ui/hud.py`

```python
class HUD:
    def __init__(self, event_bus: EventBus) -> None:
        """Se suscribe a PLAYER_DAMAGED, PLAYER_HEALED, PLAYER_DIED vía EventBus."""

    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...
    def set_salud_maxima(self, maxima: float) -> None: ...

    @property
    def timer_rect(self) -> pygame.Rect: ...
    @property
    def heart_row_rect(self) -> pygame.Rect: ...
    @property
    def score_rect(self) -> pygame.Rect: ...
    @property
    def regiones(self) -> dict[str, pygame.Rect]:
        """Todas las regiones nombradas del HUD, para pruebas de layout."""
    @property
    def ranuras_de_corazon(self) -> int: ...
    def destroy(self) -> None: ...

    def start_timer(self, time_limit: int = 0) -> None:
        """time_limit=0 significa cronómetro ascendente (modo Stage 0)."""

    def stop_timer(self) -> None: ...
    def pause_timer(self) -> None: ...
    def resume_timer(self) -> None: ...

    def set_combo_count(self, count: int) -> None:
        """Actualiza el contador de combo para mostrarlo."""

    def set_boss_hud(self, name: str, health: float, max_health: float,
                     phase: int, phase_count: int) -> None: ...

    def clear_boss_hud(self) -> None: ...
    def set_score(self, puntos: int, monedas: int = 0) -> None: ...
    def set_boss_rush(self, progreso: str, jefe: str, ...) -> None: ...
    def pulso_de_recogida(self) -> None: ...
    def trigger_save_notification(self) -> None:
        """Muestra un indicador de "Partida guardada" durante 2 segundos."""
    def set_special_meter(self, current: float, max_val: float) -> None: ...
    def set_estamina(self, current: float, max_val: float) -> None: ...
    def set_tiempo_bala(self, fraccion: float, activo: bool) -> None: ...

    @property
    def current_time(self) -> float: ...
    @current_time.setter
    def current_time(self, value: float) -> None: ...
    @property
    def time_limit(self) -> int: ...
    @property
    def is_countdown(self) -> bool: ...
    @is_countdown.setter
    def is_countdown(self, value: bool) -> None: ...
```

> **AUD-455.** Faltaban `set_salud_maxima()` y las propiedades `timer_rect`,
> `heart_row_rect`, `score_rect`, `regiones`, `ranuras_de_corazon` —
> verificado contra `src/engine/ui/hud.py`. El resto de la clase ya estaba
> completo y correcto.

<!-- cita-historica -->
> **AUD-307.** `bind_player` (daba un "retrato" del estado del jugador) **no
> existe en el HUD de hoy**: la escena de nivel le pasa cada fotograma lo que
> necesita vía `set_score`, `set_estamina`, `set_special_meter`,
> `set_tiempo_bala` y el retrato lo calcula internamente (`_get_portrait_state`).
<!-- /cita-historica -->

### 7.2 `src/engine/ui/message_box.py`

```python
class MessageBox:
    def __init__(self, event_bus: EventBus) -> None:
        """Se suscribe a SHOW_MESSAGE, HIDE_MESSAGE."""

    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...
    def hide(self) -> None: ...
    def destroy(self) -> None:
        """Cancela la suscripción a SHOW_MESSAGE/HIDE_MESSAGE."""
    def caja_rect(self) -> pygame.Rect:
        """Rectángulo del cuadro, ya escalado (AUD-453 — antes usaba la
        maqueta de 224 px fija)."""

    @property
    def is_visible(self) -> bool: ...
    @property
    def is_dismiss_on_confirm(self) -> bool: ...
```

> **AUD-307.** La propiedad se llama `is_visible` (antes `is_active`), y
> `MessageBox` además recibe el `event_bus` en `__init__`.
> **AUD-455.** Faltaban `destroy()` y `caja_rect()`. Verificado contra
> `src/engine/ui/message_box.py`.

### 7.3 `src/engine/ui/screen_banner.py`

```python
class ScreenBanner:
    def __init__(self) -> None: ...

    def play(self, stage_id: str, stage_name: str) -> None:
        """Dispara la secuencia de animación: entra deslizando / se sostiene / sale deslizando."""

    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...

    @property
    def is_active(self) -> bool: ...
    @property
    def alto(self) -> int:
        """Alto de la franja, ya escalado a la pantalla real."""
    @property
    def y_superior(self) -> int:
        """Dónde empieza la franja (AUD-453)."""
```

> **AUD-455.** Faltaban las propiedades `alto` y `y_superior`. Verificado
> contra `src/engine/ui/screen_banner.py`.

### 7.4 `src/engine/ui/theme.py`

```python
RGB = tuple[int, int, int]
RGBA = tuple[int, int, int, int]

class Theme:
    """Tokens de diseño (AUD-044) — la única fuente de verdad de color,
    espaciado y tipografía. Todo es constante; nada muta en tiempo de
    ejecución. Antes de este módulo había 6 colores de fondo distintos
    significando "fondo oscuro" repartidos por las escenas."""

    # Superficies (rampa de profundidad de 3 pasos)
    BG: RGB; SURFACE: RGB; SURFACE_RAISED: RGB; OVERLAY: RGBA
    # Líneas
    BORDER: RGB; BORDER_STRONG: RGB
    # Texto (3 niveles únicamente)
    TEXT: RGB; TEXT_MUTED: RGB; TEXT_DIM: RGB
    # Acento y estado — ámbar es el único color de foco; rojo sólo daño/peligro
    ACCENT: RGB; ACCENT_DIM: RGB; SUCCESS: RGB; WARNING: RGB; DANGER: RGB
    # Espaciado (escala base de 4px)
    SPACE_XS: int = 4; SPACE_S: int = 8; SPACE_M: int = 16
    SPACE_L: int = 24; SPACE_XL: int = 40
    MARGIN: int = 32
    # Escala tipográfica (AUD-187, subida para 800x600)
    FONT_TITLE: int = 38; FONT_HEADING: int = 27; FONT_BODY: int = 20
    FONT_SMALL: int = 17; FONT_TINY: int = 15
    # Movimiento
    FADE_FAST: float = 0.12; FADE: float = 0.22; CURSOR_PULSE_HZ: float = 1.6
    # Radios
    RADIUS: int = 4; RADIUS_L: int = 8

#: Ancho de la maqueta original (320) — AUD-453.
ANCHO_DE_DISENO: int = 320
#: settings.INTERNAL_WIDTH / ANCHO_DE_DISENO, resuelta al importar.
ESCALA_DE_INTERFAZ: float

def escalar(valor: int | float) -> int:
    """Un número de la maqueta 320px llevado a la pantalla actual."""

def escalar_texto(size: int) -> int:
    """El tamaño pedido por la preferencia de accesibilidad `text_scale`
    (AUD-126) — es el único punto por el que pasan todas las fuentes."""

def font(size: int, path: str | None = None) -> pygame.font.Font:
    """Búsqueda de fuente cacheada por (path, size). `path=None` usa
    `game.ttf` si existe (AUD-203), si no cae a la de pygame. Revalida la
    entrada de caché en cada acierto (AUD-077): un `pygame.font.quit()` dejaba
    cadáveres que la caché servía sin más."""

def clear_font_cache() -> None: ...

def pulse(elapsed: float, low: float = 0.55, high: float = 1.0) -> float:
    """Oscilación 0-1 suave (seno) para indicadores de foco que "respiran"."""

def with_alpha(color: RGB, alpha: int) -> RGBA: ...
```

### 7.5 `src/engine/ui/widgets.py`

```python
from dataclasses import dataclass, field

@dataclass
class MenuItem:
    """Una fila de un `MenuList`. `value` lleva la carga (clave de escena,
    enum) para no depender de una lista paralela que mapee índice→significado."""
    label: str
    value: object = None
    enabled: bool = True
    hint: str = ""
    trailing: str = ""   # renderizado a la derecha: valor actual, % de progreso, tecla

@dataclass
class MenuList:
    """Lista vertical con foco, navegación cíclica (envuelve, no acota) y
    filas deshabilitadas (se saltan en la navegación, no sólo se atenúan)."""

    items: list[MenuItem] = field(default_factory=list)
    index: int = 0
    #: Filas visibles a la vez (AUD-446). `None` las muestra todas.
    visible_rows: int | None = None
    ROW_HEIGHT: int = 30
    VELOCIDAD_DE_DESPLAZAMIENTO: float = 12.0   # filas/segundo, interpolación exponencial

    def move_down(self) -> None: ...
    def move_up(self) -> None: ...

    @property
    def current(self) -> MenuItem | None: ...
    @property
    def desplazamiento(self) -> float:
        """Filas deslizadas hacia arriba ahora mismo (para la ventana con `visible_rows`)."""

    def ensure_valid(self) -> None:
        """Acota `index` tras cambiar `items`; salta filas deshabilitadas."""
    def filas_visibles(self) -> list[int]:
        """Índices que se dibujan ahora mismo."""
    def update(self, dt: float) -> None:
        """Avanza la interpolación de la ventana deslizante."""
    def draw(self, surface: pygame.Surface, x: int, y: int, width: int,
             *, row_height: int | None = None) -> int:
        """Dibuja la lista; devuelve la y justo debajo de la última fila."""
    def draw_hint(self, surface: pygame.Surface, y: int) -> None:
        """Pinta la pista de la fila enfocada, si tiene."""


# ── mobiliario de pantalla ──────────────────────────────────────
def draw_screen(surface: pygame.Surface, title: str, subtitle: str = "") -> int:
    """Fondo y cabecera estándar; traduce título/subtítulo (F3.1) y devuelve
    la y donde debe empezar el contenido."""

def draw_panel(surface: pygame.Surface, rect: pygame.Rect, *,
               title: str = "", raised: bool = False) -> pygame.Rect:
    """Panel con título opcional; devuelve el rect interior disponible."""

def draw_key_hints(surface: pygame.Surface, hints: Sequence[tuple[str, str]]) -> None:
    """Pie de pantalla con las teclas activas, p.ej. `[("Enter", "Select")]`."""

def draw_modal_scrim(surface: pygame.Surface) -> None:
    """Atenúa lo que hay detrás de un modal."""

def draw_progress_bar(surface: pygame.Surface, rect: pygame.Rect, fraction: float,
                      *, color: tuple[int, int, int] | None = None,
                      label: str = "") -> None: ...

def draw_toast(surface: pygame.Surface, message: str, y: int, *,
              color: tuple[int, int, int] | None = None, alpha: int = 255) -> None: ...

def handle_menu_navigation(
    menu: MenuList, input_manager, *,
    on_confirm: Callable[[MenuItem], None] | None = None,
    on_cancel: Callable[[], None] | None = None,
) -> bool:
    """Aplica el esquema de control de menú común (ARRIBA/ABAJO/CONFIRM/CANCEL
    vía `Action`). Devuelve True si consumió la entrada."""
```

### 7.6 `src/engine/ui/minimap.py`

```python
class Minimap:
    def __init__(self, x: int | None = None, y: int | None = None) -> None:
        """Sin posición explícita, se ancla arriba a la derecha."""

    def set_map_size(self, world_w: int, world_h: int) -> None:
        """Recalcula la escala de píxel-mundo a píxel-minimapa."""
    def explore_rect(self, rect: pygame.Rect) -> None:
        """Marca un rectángulo como explorado (se ignora si ya lo cubre otro)."""
    def update(
        self, player_pos: tuple[float, float], player_dir: int,
        enemy_positions: Sequence[tuple[float, float]],
        boss_positions: Sequence[tuple[float, float]],
        checkpoint_positions: Sequence[tuple[float, float]],
        activated_checkpoints: set[int],
    ) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...
```

### 7.7 `src/engine/ui/subtitle_overlay.py`

```python
CAPTION_DURATION: float = 2.2
MAX_VISIBLE: int = 3
#: Sólo eventos con información se subtitulan (AUD-036/AUD-064) — pasos,
#: saltos y bucles ambientales quedan fuera a propósito.
CAPTIONS: dict[str, str]

class SubtitleOverlay:
    """Se suscribe siempre; la comprobación de `enabled` es al dibujar, así
    que cambiar la preferencia surte efecto sin re-conectar el bus."""

    def __init__(self, event_bus: EventBus) -> None: ...

    @property
    def enabled(self) -> bool:
        """Lee `user_settings.get().subtitles_enabled`."""

    def push(self, text: str) -> None:
        """Encola un subtítulo. Repetir el visible lo refresca en vez de apilarlo."""
    def update(self, dt: float) -> None: ...
    def rearm(self) -> None:
        """Restablece las suscripciones tras un `destroy()` (escenas re-entrantes)."""
    def destroy(self) -> None:
        """Cancela todas las suscripciones. Llamar desde `on_exit` de la escena."""
    def y_de_la_banda(self, cuantas: int) -> int:
        """Dónde empieza la banda de subtítulos, ya escalada (AUD-453)."""
    def draw(self, surface: pygame.Surface) -> None: ...
```

> **AUD-455 — GAP-053 resuelto.** `theme.py`, `widgets.py`, `minimap.py` y
> `subtitle_overlay.py` no tenían ninguna sección en este documento pese a
> que `theme.py` es la fuente de verdad de todo el color/tipografía del juego
> y `widgets.py` es el sistema de menús compartido por las ~30 pantallas.
> Verificado contra los cuatro ficheros de `src/engine/ui/`.

---

## 8. Entidades del framework — BaseEntity

### 8.1 `src/framework/entities/base_entity.py`

```python
from abc import ABC, abstractmethod

class BaseEntity(ComponentesDeEntidad, ABC):
    """Hereda de `ComponentesDeEntidad` (framework.ecs.bridge), no sólo de
    ABC (F5.2): `position`/`rect`/`facing`/`velocity` son PROPIEDADES que
    leen/escriben el componente ECS `Transform` — el objeto real, no una
    copia —, no atributos simples. Por fuera el comportamiento no cambia
    (`self.rect.centerx = 40` sigue funcionando); por dentro es lo que
    permite que cualquier sistema (viento, plataforma móvil, agua) mueva a
    cualquier entidad con `Transform` sin conocer su clase."""

    #: Contra qué clases de `Capa` (§20.1) choca esta entidad (AUD-395).
    #: Atributo DE CLASE — la respuesta es de la especie. Por defecto, el
    #: comportamiento de antes de que existieran las capas (sólidos +
    #: plataformas, no `Capa.TODO`).
    mascara_de_colision: Capa = MASCARA_POR_DEFECTO

    def __init__(self, position: pygame.Vector2, event_bus: EventBus | None = None) -> None:
        """Sin `event_bus`, la entidad recibe uno inerte propio (AUD-019) —
        nunca comparte un singleton global. `StageScene` inyecta el real a
        cada entidad que carga."""

    def set_event_bus(self, bus: EventBus) -> None:
        """Inyección tardía del bus."""

    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...

    position: pygame.Vector2   # propiedad — ver docstring de la clase
    rect: pygame.Rect          # propiedad
    is_active: bool       # por defecto True
    is_visible: bool      # por defecto True
    layer: int            # por defecto 4 (capa media; ver pyscroll default_layer)
```

> **AUD-455.** `__init__` no tenía `event_bus`; faltaban `set_event_bus()` y
> el atributo de clase `mascara_de_colision` (AUD-395, el enganche real de
> §20.1). La clase hereda de `ComponentesDeEntidad`, no sólo de `ABC` —
> `position`/`rect` son propiedades respaldadas por ECS, no atributos
> simples, aunque el docstring anterior no lo mencionaba. Verificado contra
> `src/framework/entities/base_entity.py`.

---

## 9. Entidades del framework — Player

### 9.1 `src/framework/entities/player.py`

```python
from enum import Enum

class PlayerState(str, Enum):
    IDLE = "IDLE"
    WALKING = "WALKING"
    JUMPING = "JUMPING"
    FALLING = "FALLING"
    CROUCHING = "CROUCHING"
    SHORT_ATTACK = "SHORT_ATTACK"
    LONG_ATTACK = "LONG_ATTACK"
    HURT = "HURT"
    DYING = "DYING"
    DASHING = "DASHING"
    PARRY = "PARRY"
    CHARGE_ATTACK = "CHARGE_ATTACK"
    DASH_ATTACK = "DASH_ATTACK"
    WALL_SLIDE = "WALL_SLIDE"
    LEDGE_GRAB = "LEDGE_GRAB"
    GRAB = "GRAB"
    THROW = "THROW"
    SLIDE = "SLIDE"
    SWIMMING = "SWIMMING"
    CLIMBING = "CLIMBING"
    ZIPLINE = "ZIPLINE"
    ULTIMATE = "ULTIMATE"
    AERIAL_ATTACK = "AERIAL_ATTACK"
    AERIAL_SLAM = "AERIAL_SLAM"
    AIR_CHASE = "AIR_CHASE"
    CHARGE_RELEASE = "CHARGE_RELEASE"

# AUD-455: esta lista tenía 19 de los 26 estados reales — faltaban CLIMBING,
# ZIPLINE, ULTIMATE, AERIAL_ATTACK, AERIAL_SLAM, AIR_CHASE, CHARGE_RELEASE.
# Verificado contra `src/framework/entities/player.py::PlayerState`.

class Player(BaseEntity):
    def __init__(self, spawn_position: pygame.Vector2) -> None: ...

    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...

    def apply_damage(self, amount: float, source_position: tuple[float, float], knockback_force: float = 150.0) -> None:
        """
        No hace nada si invincibility_timer > 0. En caso contrario: resta amount, satura a
        [0, PLAYER_MAX_HEALTH], fija invincibility_timer, emite PLAYER_DAMAGED,
        transiciona a HURT, aplica retroceso con la fuerza dada alejándose de la fuente.
        Emite PLAYER_DIED si la salud llega a 0.
        """

    def set_spawn(self, position: pygame.Vector2) -> None:
        """La ÚNICA forma sancionada de reposicionar al jugador (p. ej., reaparición en checkpoint)."""

    def consume_hitbox(self) -> None:
        """La llama el sistema de colisión del escenario tras conectar una hitbox de ataque,
        para evitar múltiples golpes en el mismo fotograma. También sube el
        medidor de especial (`gain_special`) y recarga el arco — el único
        sitio donde se sabe que el golpe ACERTÓ, para no premiar dar palos al aire."""

    @property
    def current_health(self) -> float:
        """Sólo lectura. El código de escenario/entidad nunca debe escribir _health directamente."""
    @property
    def max_health(self) -> float:
        """Base + bonos de reliquias + bonos del árbol, con tope de
        `CORAZONES_MAXIMOS` (AUD-293) — el único sitio por el que pasan todos los sumandos."""
    @property
    def walk_speed(self) -> float:
        """`perfil.velocidad_suelo` (AUD-333) multiplicado por el bono de reliquias."""
    @property
    def vista_cenital(self) -> bool:
        """Modo del PERFIL de física (AUD-333: `perfil.modo == CENITAL`), no
        una bandera propia — el contrato externo (leer/escribir esta
        propiedad) no cambia."""
    @vista_cenital.setter
    def vista_cenital(self, valor: bool) -> None: ...
    @property
    def damage_multiplier(self) -> float:
        """1.0 + bono de reliquias + bono del árbol de habilidades."""
    def apply_relic_bonuses(self, inventory: Any) -> None:
        """Recalcula los bonos de vida/velocidad/daño desde el inventario y
        el árbol de habilidades. La llama `StageScene` al entrar al nivel y
        al recoger un objeto. Sube `_health` de inmediato si `max_health` creció."""
    @property
    def hurtbox(self) -> pygame.Rect:
        """Más pequeña que el rect de colisión: de pie 20×28 (offset Y 4),
        agachado 20×18 (offset Y 14)."""
    @property
    def state(self) -> "PlayerState": ...

    @property
    def active_hitbox(self) -> pygame.Rect | None:
        """None salvo que esté actualmente en una ventana de fotogramas activos de ataque."""

    @property
    def current_attack_damage(self) -> float:
        """0.50 durante fotogramas activos de SHORT_ATTACK, 1.00 durante los de LONG_ATTACK,
        0.0 en el resto de casos."""

    def heal(self, amount: float) -> None:
        """Multiplicado por `difficulty.heal_mult`. Emite `SFX_PLAYER_HEAL`
        sólo si la vida realmente subió (curarse a vida llena no debe sonar)."""
    def set_health(self, amount: float) -> None:
        """Fija la vida directamente, saturada a [0, max_health] — sin sonido ni evento."""

    # ── AUD-141: estamina (apagada por defecto; la enciende el escenario) ──
    @property
    def estamina_activa(self) -> bool:
        """`estamina_max > 0` — False mientras el escenario no la pida."""
    @property
    def hay_estamina_para_correr(self) -> bool:
        """True si la estamina está apagada, o si hay suficiente para el coste del dash."""
    def gastar_estamina(self, cantidad: float | None = None) -> bool:
        """Cobra el gasto (`coste_dash` por defecto); False si no había
        bastante. Con la estamina apagada, siempre True sin tocar nada."""
    def recuperar_estamina(self, dt: float) -> None: ...
    def activar_estamina(self, maximo: float) -> None:
        """La enciende el escenario al cargar; `0` la deja apagada."""

    def gain_special(self, amount: float) -> None:
        """Sube el medidor de especial, con tope `special_meter_max`."""
    @property
    def ultimate_listo(self) -> bool:
        """¿Medidor de especial lleno? (con margen de epsilon para el redondeo flotante)."""

    facing_direction: int  # -1 or 1
```

> **AUD-455.** Faltaban 15 miembros públicos reales: `max_health`,
> `walk_speed`, `vista_cenital` (propiedad+setter), `damage_multiplier`,
> `apply_relic_bonuses`, `hurtbox`, `heal`, `set_health`, `estamina_activa`,
> `hay_estamina_para_correr`, `gastar_estamina`, `recuperar_estamina`,
> `activar_estamina`, `gain_special`, `ultimate_listo`. Verificado contra
> `src/framework/entities/player.py`.

---

## 10. Entidades del framework — Enemigos

### 10.1 `src/framework/entities/enemy_base.py`

```python
from abc import abstractmethod
from enum import Enum

class EnemyState(str, Enum):
    IDLE = "IDLE"
    PATROL = "PATROL"
    SEARCH = "SEARCH"
    ALERT = "ALERT"
    CHASE = "CHASE"
    TELEGRAPHING = "TELEGRAPHING"
    FIRING = "FIRING"
    RECOVER = "RECOVER"
    RETREAT = "RETREAT"
    STUNNED = "STUNNED"
    HURT = "HURT"
    LAUNCHED = "LAUNCHED"
    DYING = "DYING"

# AUD-455: esta lista tenía 4 de los 13 estados reales — faltaban IDLE,
# SEARCH, CHASE, TELEGRAPHING, FIRING, RECOVER, RETREAT, STUNNED, LAUNCHED.
# Verificado contra `src/framework/entities/enemy_base.py::EnemyState`. La
# clase misma (AUD-051) documenta por qué cada estado añadido importa — ver
# el docstring de `EnemyState` en el código.

class EnemyBase(BaseEntity):
    #: Exención del culling (AUD-279): `True` sigue simulando lejos de cámara
    #: (un perseguidor de largo alcance, un temporizador largo). Los
    #: proyectiles en vuelo no hace falta declararlos aquí.
    siempre_activo: bool = False

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float,
        damage_on_contact: float = 0.5,
        contact_knockback: float = 120.0,
        detection_range_x: float = 160.0,
        detection_range_y: float = 64.0,
        hurt_duration: float = 0.25,
        invincibility_duration: float = 0.5,
        deaggro_margin: float = 32.0,
        event_bus: EventBus | None = None,
    ) -> None: ...

    def update(self, dt: float) -> None:
        """Actualización maestra — llama a _update_invincibility, _run_state_machine,
        _update_rects, _check_player_contact. Las subclases NO deben sobrescribir update()."""

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...

    def apply_hit(self, damage: float, source_position: tuple[float, float],
                  canal: str | None = None) -> None:
        """Ya provisto. No sobrescribir. `canal` (AUD-387, §20.4) es el tipo de
        daño — al final y opcional porque tiene 32 llamantes, 26 en entregas
        de estudiante; sin canal se aplica el físico y sin `resistencias`
        declaradas la mitigación es 1.0 (comportamiento idéntico a antes de
        AUD-387). El aturdimiento se decide con el daño YA mitigado."""

    def stun(self, duration: float = 0.8) -> None:
        """Aturde al enemigo (parry o golpe pesado) — cancela el ataque en
        curso y entra en `STUNNED`. No hace nada si está `DYING` o `LAUNCHED`."""
    def begin_recovery(self, duration: float | None = None) -> None:
        """Entra en la ventana de castigo `RECOVER`. La llaman los estados de ataque propios."""
    def set_collision_rects(self, rects: list[pygame.Rect],
                            one_way: list[pygame.Rect] | None = None) -> None: ...
    def set_pendientes(self, pendientes: list) -> None:
        """Suelo inclinado que el enemigo respeta (AUD-325). Vacío por defecto."""
    def set_player_ref(self, player_rect: pygame.Rect) -> None: ...
    def caja_ajustada(self, margen_x: int = 0, margen_y: int = 0) -> pygame.Rect:
        """Caja LOCAL recortada hacia dentro del cuerpo y centrada — la forma
        correcta de construir `_build_hitbox`/`_build_hurtbox` (AUD-108: un
        desplazamiento sin recorte deja el 30% del cuerpo intocable por un
        lado y golpea aire por el otro)."""
    def check_player_contact(self, player: "Player") -> None:
        """OBSOLETO — alias de `_check_player_contact`, emite `DeprecationWarning`."""

    @property
    def death_timer(self) -> float: ...

    # --- Sobrescrituras obligatorias (abstractas) ---
    @abstractmethod
    def _patrol_behavior(self, dt: float) -> None: ...

    @abstractmethod
    def _alert_behavior(self, dt: float) -> None: ...

    @abstractmethod
    def _get_animation_key(self) -> str:
        """Devuelve la clave de animación base para el estado actual (que no sea DYING ni HURT)."""

    @abstractmethod
    def _build_hitbox(self) -> pygame.Rect:
        """Devuelve un rect en espacio LOCAL (desplazamiento desde la posición de la entidad)."""

    @abstractmethod
    def _build_hurtbox(self) -> pygame.Rect:
        """Devuelve un rect en espacio LOCAL (desplazamiento desde la posición de la entidad)."""

    # --- Método plantilla (sobrescribir sólo vía _get_animation_key) ---
    def _get_animation_state(self) -> str:
        """Método plantilla concreto — mapeo fijo para DYING/HURT;
        delega en _get_animation_key() para el resto."""

    # --- Ganchos provistos (se pueden sobrescribir para lógica de proyectiles a medida) ---
    def _check_player_contact(self, player: "Player") -> None: ...

    # --- Provistos, no sobrescribir ---
    def _die(self) -> None: ...
    def _update_invincibility(self, dt: float) -> None: ...
    def _update_rects(self) -> None: ...

    current_health: float
    max_health: float
    is_alive: bool
    facing_direction: int  # -1 o 1
    state: "EnemyState"
    hitbox: pygame.Rect    # en espacio de mundo, recalculado cada fotograma
    hurtbox: pygame.Rect   # en espacio de mundo, recalculado cada fotograma
    tactic: str             # AUD-050 — táctica que decide SquadBrain, "approach" por defecto
    resistencias: dict[str, float]   # AUD-387 — canal de daño -> multiplicador; vacío por defecto
```

> **AUD-455.** `__init__` no tenía `deaggro_margin` ni `event_bus`.
> `apply_hit` no tenía `canal` — el punto de entrada real al sistema de
> canales de daño de §20.4. Faltaban `siempre_activo`, `stun()`,
> `begin_recovery()`, `set_collision_rects()`, `set_pendientes()`,
> `set_player_ref()`, `caja_ajustada()`, `check_player_contact()` (obsoleto),
> `death_timer`, `max_health`, `tactic` y `resistencias`. Verificado contra
> `src/framework/entities/enemy_base.py`.

### 10.2 `src/framework/entities/enemy_walker.py`

```python
class EnemyWalker(EnemyBase):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        patrol_length: float = 96.0,
        facing: str = "right",
        patrol_speed: float = 45.0,
        alert_speed: float = 75.0,
        damage_on_contact: float = 0.5,
        max_health: float = 2.0,
        zone: int = 0,
        **kwargs,
    ) -> None: ...

    # Implementa los abstractos heredados; sin métodos públicos nuevos.
```
> **AUD-455.** Faltaba `**kwargs`. Verificado contra
> `src/framework/entities/enemy_walker.py`.

### 10.3 `src/framework/entities/enemy_flying.py`

```python
class EnemyFlying(EnemyBase):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        flight_mode: str = "sine",          # "sine" | "bezier" | "patrol"
        flight_speed: float = 60.0,
        sine_amplitude: float = 28.0,
        sine_frequency: float = 1.5,
        waypoints: list[tuple[float, float]] | None = None,  # obligatorio para "bezier"/"patrol"
        max_health: float = 1.5,
        damage_on_contact: float = 0.5,
        zone: int = 0,
        alert_flight_mode: str | None = None,
        **kwargs,
    ) -> None: ...

    # Implementa los abstractos heredados; sin métodos públicos nuevos.
```
> **AUD-455.** Faltaban `alert_flight_mode` y `**kwargs`. Verificado contra
> `src/framework/entities/enemy_flying.py`.

### 10.4 `src/framework/entities/enemy_shooter.py`

```python
class EnemyShooter(EnemyBase):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        fire_rate: float = 0.5,             # disparos por segundo
        projectile_speed: float = 120.0,
        projectile_damage: float = 0.5,
        patrol_length: float = 0.0,         # 0 = estacionario
        max_health: float = 3.0,
        damage_on_contact: float = 0.25,
        zone: int = 0,
        admite_bash: bool = False,
        **kwargs,
    ) -> None: ...

    def on_collision(self) -> None:
        """Marca el proyectil expirado y emite `SFX_ENEMIES_PROJECTILE_HIT_WALL` (AUD-255)."""


class Projectile(BaseEntity):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        velocity: pygame.Vector2,
        damage: float,
        lifetime: float = 3.0,
        gravity: float = 0.0,
        admite_bash: bool = False,
    ) -> None:
        """`gravity` en px/s², cero por defecto — los proyectiles vuelan
        rectos a propósito (son telegrafiados que el jugador aprende a leer)."""

    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...
```
> **AUD-455.** `EnemyShooter.__init__` no tenía `admite_bash`/`**kwargs`; le
> faltaba el método `on_collision()`. `Projectile.__init__` no tenía
> `gravity` ni `admite_bash`. Verificado contra
> `src/framework/entities/enemy_shooter.py`.

### 10.4b Los cinco arquetipos restantes

> **AUD-455.** Estos cinco no estaban documentados en absoluto — el README y
> `18_ENEMY_ROSTER.md` ya citaban los 8 arquetipos, pero esta sección sólo
> cubría 3 (walker, flying, shooter). Firmas verificadas contra el código.

```python
class EnemyArcher(EnemyBase):
    """Dispara proyectiles en arco, con puntería predictiva y altura de arco variable."""
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 2.5,
        damage_on_contact: float = 0.25,
        fire_rate: float = 0.4,
        projectile_speed: float = 90.0,
        projectile_damage: float = 0.75,
        zone: int = 0,
        **kwargs,
    ) -> None: ...


class EnemyBrute(EnemyBase):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 5.0,
        damage_on_contact: float = 0.5,
        zone: int = 0,
        **kwargs,
    ) -> None: ...


class EnemyCharger(EnemyBase):
    """Embiste al jugador a alta velocidad con preparación.
    Fases: WIND_UP (telegrafiado) -> CHARGE (rápido) -> STUN (recuperación)."""
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 4.0,
        damage_on_contact: float = 1.5,
        charge_speed: float = 250.0,
        zone: int = 0,
        **kwargs,
    ) -> None: ...


class EnemyCaster(EnemyBase):
    """Invoca `HomingOrb` — un proyectil autoguiado (`BaseEntity` propio, no un enemigo)."""
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 2.0,
        damage_on_contact: float = 0.25,
        zone: int = 0,
        **kwargs,
    ) -> None: ...


class EnemyAssassin(EnemyBase):
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 1.5,
        damage_on_contact: float = 0.25,
        zone: int = 0,
        **kwargs,
    ) -> None: ...
```

Los cinco heredan la interfaz completa de `EnemyBase` (§10.1) sin métodos
públicos nuevos, igual que `EnemyWalker`/`EnemyFlying` en §10.2–§10.3.

### 10.5 `src/framework/entities/boss_base.py`

> **AUD-455.** Esta sección no existía: §10.5 remitía a §17 ("Escenas del
> motor — infraestructura", que no menciona `BossBase` en ningún punto) y
> §19 remitía de vuelta a §10.5 — una referencia circular sin API real en
> ningún extremo. Lo que sigue es la firma real, verificada contra
> `src/framework/entities/boss_base.py` (no exhaustiva: se omiten métodos
> privados de bajo nivel que ningún jefe de estudiante necesita tocar).

```python
from dataclasses import dataclass, field

@dataclass
class BossPhase:
    """Definición de una fase de jefe."""
    phase_index: int
    health_threshold: float
    attack_patterns: list[str] = field(default_factory=list)
    movement_type: str = "stationary"
    speed_multiplier: float = 1.0
    sprite_override: str | None = None
    filter_effect: str | None = None
    combos: dict[str, list[str]] = field(default_factory=dict)
    invulnerable: bool = False   # inmune al daño durante toda la fase
    escala: float = 1.0          # multiplicador de tamaño de la fase


class BossBase(EnemyBase):
    """Clase base de todas las entidades de jefe. Extiende EnemyBase con
    gestión de fases, protocolo de transición de fase e integración con el
    HUD de jefe."""

    skill_drop: str = ""          # habilidad que suelta al morir (AUD-238); "" = ninguna
    siempre_activo: bool = True   # un jefe nunca se congela por salir del encuadre (AUD-279)

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 20.0,
        damage_on_contact: float = 1.0,
    ) -> None: ...

    def set_phases(self, phases: list[BossPhase]) -> None:
        """Fija la lista de fases y extrae los umbrales de salud."""

    def set_boss_name(self, name: str) -> None: ...

    def habilidades_que_suelta(self) -> list[str]:
        """Las habilidades que este jefe deja al morir (AUD-263, acepta
        `skill_drop` como str única o el atributo equivalente en lista)."""

    def apply_hit(self, damage: float, source_position: tuple[float, float]) -> None:
        """No hace nada si está muriendo, en transición, invencible o si la
        fase actual declara `invulnerable=True`. En caso contrario aplica el
        golpe y comprueba la transición de fase."""

    def on_attack_fired(self, attack_name: str) -> None: ...
    def on_summon(self, species_id: str, count: int) -> None: ...
    def take_summons(self) -> list["EnemyBase"]:
        """Vacía y devuelve `pending_summons`; lo llama StageScene cada fotograma."""

    def set_arena_bounds(self, bounds: pygame.Rect) -> None: ...
    def clamp_to_arena(self, margin: int = 16) -> None: ...
    def weak_point_at(self, hit_rect: pygame.Rect) -> "WeakPoint | None": ...
    def apply_hit_at(self, damage: float, source_position: tuple[float, float],
                     hit_rect: pygame.Rect | None = None) -> float:
        """Aplica daño resolviendo puntos débiles primero (multiplican el
        daño y avisan al VFX). Devuelve el daño REAL aplicado, no None."""
    def teletransportar(self, x: float, y: float) -> None: ...
    def recibir_parry(self) -> float:
        """Aplica el aturdimiento por parry y devuelve su duración."""

    @property
    def boss_name(self) -> str: ...
    @property
    def phase_count(self) -> int: ...
    @property
    def phase_max_health(self) -> float: ...
    @property
    def fase_invulnerable(self) -> bool:
        """¿La fase actual declara inmunidad al daño?"""
    @property
    def escala_de_fase(self) -> float:
        """Multiplicador de tamaño de la fase actual."""
    @property
    def aturdido(self) -> bool: ...
    @property
    def attack_timing(self) -> "AttackTiming": ...
    @property
    def is_vulnerable(self) -> bool: ...
    @property
    def telegraph_progress(self) -> float: ...
    @property
    def completion_fired(self) -> bool: ...
    @completion_fired.setter
    def completion_fired(self, value: bool) -> None: ...

    phases: list[BossPhase]
    current_phase: int
    is_transitioning: bool
    transition_timer: float
    attacks: "AttackScheduler"
    weak_points: list["WeakPoint"]
    summons: "SummonTracker"
    pending_summons: list["EnemyBase"]
    last_weak_point: "WeakPoint | None"
    arena_bounds: pygame.Rect | None
    speed_multiplier: float


# AUD-053: `_start_phase_transition` / `_finish_phase_transition` llevan el
# protocolo de transición y emiten BOSS_PHASE_CHANGED (ver 23_DATA_SCHEMAS.md
# §2). La documentación antigua de este repositorio decía
# `_begin_phase_transition`, un nombre que no existe en el código.
```

> **AUD-455.** `apply_hit_at` tenía el orden de parámetros invertido
> (`hit_rect` primero; el real lo recibe último y opcional) y el tipo de
> retorno equivocado (`None`; el real devuelve `float`, el daño ya resuelto
> contra los puntos débiles). Llamarlo con argumentos posicionales según la
> documentación anterior pasaría un `Rect` donde se espera un `float`.
> Verificado contra `src/framework/entities/boss_base.py`.

### 10.5b El kit de encuentro (`src/framework/entities/boss_kit.py`)

> **AUD-455.** Sin documentar en absoluto — `17_BOSS_SPEC.md` sólo lo
> mencionaba de pasada. `BossBase` expone instancias de estas clases en
> `self.attacks`, `self.weak_points` y `self.summons` (ver §10.5).

```python
class AttackTiming(str, Enum):
    """Tramo en el que está un ataque telegrafiado."""
    IDLE = "IDLE"
    WINDUP = "WINDUP"
    ACTIVE = "ACTIVE"
    RECOVER = "RECOVER"


@dataclass
class BossAttack:
    """Un ataque con aviso, golpe y ventana de castigo."""
    name: str
    windup: float = 0.6          # segundos de telegrafiado antes del golpe
    active: float = 0.2
    recover: float = 0.8
    damage: float = 1.0
    reach: float = 48.0          # alcance en px (rango de disparo si es a distancia)
    min_range: float = 0.0
    max_range: float = 9999.0
    cooldown: float = 1.5
    phases: tuple[int, ...] = ()          # vacío = disponible en todas
    parriable: bool = False               # F5.7: ¿se puede desviar con el parry?
    aturde_al_parry: float = 1.2          # segundos de aturdimiento si se desvía

    def available_in(self, phase: int) -> bool: ...
    def in_range(self, distance: float) -> bool: ...
    def is_readable(self) -> bool:
        """¿El windup da tiempo real a reaccionar? (windup >= MIN_READABLE_WINDUP = 0.35s)"""
    @property
    def total_duration(self) -> float: ...


@dataclass
class WeakPoint:
    """Zona que recibe daño aumentado, opcionalmente sólo en ciertas fases."""
    offset: tuple[int, int]      # desde la esquina superior izquierda del jefe
    size: tuple[int, int]
    multiplier: float = 2.5
    phases: tuple[int, ...] = ()
    label: str = "núcleo"

    def rect_for(self, boss_rect: pygame.Rect) -> pygame.Rect: ...
    def exposed_in(self, phase: int) -> bool: ...


@dataclass
class SummonWave:
    """Invocación de esbirros con tope de población."""
    species_id: str
    count: int = 2
    max_alive: int = 4           # tope de invocados vivos a la vez
    cooldown: float = 8.0
    phases: tuple[int, ...] = ()
    spawn_offsets: tuple[tuple[int, int], ...] = ((-64, -16), (64, -16))

    def available_in(self, phase: int) -> bool: ...


class AttackScheduler:
    """Elige qué ataque lanza el jefe y lleva sus tiempos (AUD-053)."""

    def __init__(self, attacks: list[BossAttack] | None = None) -> None: ...

    @property
    def current(self) -> BossAttack | None: ...
    @property
    def timing(self) -> AttackTiming: ...
    @property
    def is_active(self) -> bool: ...
    @property
    def is_vulnerable(self) -> bool: ...
    @property
    def telegraph_progress(self) -> float: ...

    def update(self, dt: float, distance: float, phase: int) -> str | None:
        """Avanza el temporizador; devuelve el nombre del ataque cuando entra en ACTIVE."""
    def interrupt(self) -> None: ...
    @property
    def se_puede_desviar(self) -> bool:
        """PROPIEDAD, no método — `scheduler.se_puede_desviar`, sin paréntesis.
        Sólo True durante WINDUP/ACTIVE de un ataque `parriable`."""
    def desviar(self) -> float:
        """Aplica el parry del jugador; devuelve la duración de aturdimiento (0 si no cuela)."""
    def reset(self) -> None: ...


@dataclass
class SummonTracker:
    waves: list[SummonWave] = field(default_factory=list)

    def update(self, dt: float) -> None: ...
    @property
    def alive_count(self) -> int: ...
    def ready_wave(self, phase: int) -> SummonWave | None: ...
    def spawn(self, wave: SummonWave, origin: pygame.Vector2) -> list[EnemyBase]:
        """Recortada al tope `max_alive` de la oleada."""
    def reset(self) -> None: ...


def resolve_weak_point_damage(
    boss: EnemyBase,
    hit_rect: pygame.Rect,
    base_damage: float,
    weak_points: list[WeakPoint],
    phase: int,
) -> tuple[float, WeakPoint | None]:
    """El orden real: `boss` (la entidad entera, no sólo su rect — se usa
    `boss.rect` internamente), `hit_rect`, `base_damage`, `weak_points`,
    `phase`. Devuelve el multiplicador del punto MÁS ALTO acertado si varios
    se solapan, no la suma."""
```

> **AUD-455.** `AttackScheduler.se_puede_desviar` no tenía `@property` —
> estaba documentado como método invocable cuando el real se lee sin
> paréntesis. `resolve_weak_point_damage` tenía los 5 parámetros
> reordenados y el segundo mal tipado (`boss_rect: pygame.Rect` en vez de
> `boss: EnemyBase`); llamarlo posicionalmente según la versión anterior
> habría pasado los argumentos a los sitios equivocados. Verificado contra
> `src/framework/entities/boss_kit.py`.

---

## 11. Framework Stage (escenario)

### 11.1 `src/framework/stage/camera.py`

```python
class Camera:
    def __init__(self, rng: random.Random | None = None) -> None: ...

    def follow(self, target: "BaseEntity") -> None: ...
    def update(self, dt: float) -> None: ...
    def set_map_size(self, width: int, height: int) -> None: ...
    def set_camera_locks(self, locks: list["_CameraLock"] | None) -> None: ...
    def apply_shake(self, amplitude: float = 2.0, duration: float = 0.1,
                    direccion: Any = None) -> None: ...
    def snap_to_target(self) -> None:
        """Salta al objetivo sin lerp — para teletransportes y reaparición en checkpoint."""

    def world_to_screen(self, world_pos: pygame.Vector2) -> pygame.Vector2: ...
    def screen_to_world(self, screen_pos: pygame.Vector2) -> pygame.Vector2: ...
    def layer_offset(self, layer_name: str) -> pygame.Vector2: ...
    def parallax_factor(self, layer_name: str) -> float: ...
    def set_parallax_factor(self, layer_name: str, factor: float) -> None: ...

    offset: pygame.Vector2   # atributo público mutable, no property; posición de cámara en mundo
    lerp_speed: float        # por defecto 8.0
    #: AUD-143 — modo de cámara: "seguir" (el de siempre, con suavizado),
    #: "zona_muerta" (no se mueve mientras el objetivo esté dentro de un
    #: rectángulo central — Celeste, Hollow Knight) o "sala" (salta de
    #: pantalla en pantalla, sin suavizar — Zelda, Metroid).
    modo: str
    zona_muerta: pygame.Vector2      # medio ancho/alto de la zona muerta en px
    anticipacion: float              # segundos de anticipación horizontal por velocidad
    anticipacion_caida: float        # anticipación vertical sólo al caer
```

> **AUD-455.** Corrige varias discrepancias verificadas contra
> `src/framework/stage/camera.py`: `__init__` acepta `rng` opcional (no está
> vacío); `apply_shake` tiene un tercer parámetro `direccion`; `offset` es un
> atributo público mutable, no una `@property` (no hay ninguna `@property` en
> toda la clase); faltaban `snap_to_target()`, `parallax_factor()`, y
> `set_parallax_factor()`. También faltaba el sistema de modos de cámara
> entero (AUD-143: `modo`, `zona_muerta`, `anticipacion`,
> `anticipacion_caida`) — no sólo el modo "seguir" de siempre.

### 11.2 `src/framework/stage/checkpoint.py`

```python
class Checkpoint(BaseEntity):
    def __init__(self, position: pygame.Vector2, rect: pygame.Rect, checkpoint_id: int,
                event_bus: EventBus | None = None) -> None: ...

    def update(self, dt: float) -> None:
        """No hace nada por fotograma — el estado lo dirige check_collision()."""

    def check_collision(self, player_rect: pygame.Rect) -> bool:
        """Comprueba el solape con el jugador. Devuelve True sólo en el fotograma que se activa."""

    def activate(self) -> None: ...
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...
    def set_event_bus(self, event_bus: EventBus) -> None: ...

    @property
    def is_activated(self) -> bool: ...
    @property
    def checkpoint_id(self) -> int: ...
```

> **AUD-307.** La propiedad se llama `is_activated` (antes `is_active`).
>
> **AUD-455.** `__init__` acepta también `event_bus` opcional; y faltaban
> `check_collision()`, `activate()`, `set_event_bus()`, y la propiedad
> `checkpoint_id` — verificado contra `src/framework/stage/checkpoint.py`. La
> activación real no es automática dentro de `update()` (que no hace nada);
> la dispara `check_collision()`, que llama a `activate()` internamente.

### 11.3 `src/framework/stage/stage_loader.py`

> **AUD-455.** `StageData` y las dataclasses que la acompañan se extrajeron a
> `src/framework/stage/stage_data.py` en AUD-350 (`stage_loader.py` tenía
> 1886 líneas). `StageData` creció de las 17 propiedades documentadas hasta
> aquí a las **~50 reales** — el resto de esta sección lista las que
> faltaban, agrupadas por para qué sirven. Cada una es una propiedad de mapa
> TMX real (ver también `06_TMX_SPEC.md`), con su valor por defecto que dice
> "apagado" cuando el mapa no la declara.

```python
VISTAS_VALIDAS: frozenset[str] = frozenset({"lateral", "cenital"})       # AUD-129
MODOS_DE_CAMARA: frozenset[str] = frozenset({"seguir", "zona_muerta", "sala"})  # AUD-143

@dataclass
class MessageTrigger:
    rect: pygame.Rect
    text: str
    triggered: bool = False
    dialogue_tree_id: str = ""    # árbol de diálogo que abre, si abre alguno (AUD-127)

@dataclass
class HazardZone:
    """Zona que hace daño; con `sube` crece hacia arriba (agua que inunda, AUD-135)."""
    rect: pygame.Rect
    damage: float = 0.25
    cooldown: float = 0.5
    timer: float = 0.5
    sube: float = 0.0                    # px/s que sube el borde superior; 0 = fija
    sube_hasta: float | None = None      # y donde se detiene; None = sin tope
    arranca_con: str = ""                # evento que la pone en marcha; vacío = ya
    avisar: bool = True                  # AUD-241 — el motor pinta el aviso visual
    damage_type: str = "fisico"          # AUD-387 — canal de daño (§20.4)
    activa: bool = True

    @property
    def sube_de_verdad(self) -> bool: ...
    def arrancar(self) -> None: ...
    def avanzar(self, dt: float) -> None: ...
    def reiniciar(self) -> None:
        """Devuelve el agua a su altura inicial — se llama al reaparecer."""

@dataclass
class EscenaGuionizada:
    """Cutscene declarada en el TMX, no en Python (AUD-136/D3)."""
    rect: pygame.Rect            # zona que la dispara; vacío (punto) = al empezar el escenario
    guion: str = ""
    bloquea: bool = True
    saltable: bool = True
    una_vez: bool = True
    arranca_con: str = ""        # evento del bus que la arranca, en vez de la posición
    disparada: bool = False

    @property
    def al_empezar(self) -> bool: ...

@dataclass
class DeathPit:
    rect: pygame.Rect

@dataclass
class CameraLock:
    rect: pygame.Rect
    lock_x: bool = False
    lock_y: bool = False

@dataclass
class LightSpec:
    """Foco declarado en el TMX, en coordenadas de mapa — dato puro, no
    construye `LightSource` (eso ataría el cargador al módulo de vfx)."""
    position: tuple[float, float]
    radius: float = 80.0
    color: tuple[int, int, int] = (255, 220, 180)
    intensity: float = 0.8
    flicker: bool = False
    flicker_speed: float = 4.0
    flicker_amount: float = 0.15

@dataclass
class StageData:
    map_layer: pyscroll.PyscrollGroup
    map_pixel_size: tuple[int, int] = (0, 0)
    collision_rects: list[pygame.Rect] = field(default_factory=list)
    one_way_rects: list[pygame.Rect] = field(default_factory=list)
    capas: MapaDeCapas = field(default_factory=MapaDeCapas)   # AUD-395 — mismas cajas por clase de sólido (§20.1)
    cielo: bool = False                          # AUD-426 — cielo procedural en vez de PNG
    objetivos: list["Objetivo"] = field(default_factory=list)      # AUD-400/GAP-047
    entity_list: list[BaseEntity] = field(default_factory=list)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    spawn_point: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    next_trigger: pygame.Rect | None = None
    background_layers: list[pygame.Surface] = field(default_factory=list)
    background_factors: list[float] = field(default_factory=list)  # AUD-272 — parallax por capa
    message_triggers: list[MessageTrigger] = field(default_factory=list)
    hazard_zones: list[HazardZone] = field(default_factory=list)
    death_pits: list[DeathPit] = field(default_factory=list)
    escenas: list[EscenaGuionizada] = field(default_factory=list)          # AUD-136
    empujables: list["BloqueEmpujable"] = field(default_factory=list)      # AUD-140
    destructibles: list["BloqueDestructible"] = field(default_factory=list)
    camera_locks: list[CameraLock] = field(default_factory=list)
    lights: list[LightSpec] = field(default_factory=list)
    recogibles: list["Recogible"] = field(default_factory=list)      # F4.1 — interactuables
    cerraduras: list["Cerradura"] = field(default_factory=list)
    cofres: list["Cofre"] = field(default_factory=list)
    disparadores: list["Disparador"] = field(default_factory=list)
    warps: list["ZonaDeWarp"] = field(default_factory=list)             # AUD-287
    pendientes: list["Pendiente"] = field(default_factory=list)         # AUD-297 — suelo inclinado
    habilidades_libres: bool = False                        # AUD-294 — regala mecánicas de jefe
    scroll_forzados: list["ScrollForzado"] = field(default_factory=list)  # AUD-249
    componentes: list[list[object]] = field(default_factory=list)   # F5.3-F5.6 — componentes ECS del TMX
    zone: int = 0
    stage_id: str = ""
    stage_name: str = ""
    time_limit: int = 0
    bgm_track: str = ""
    gravity_multiplier: float = 1.0
    vista: str = "lateral"                # AUD-129 — "lateral" | "cenital"
    bpm: float = 0.0                      # AUD-137/F6 — 0 = no rítmico, sin reloj musical
    compas: int = 4
    desfase_audio: float = 0.0
    camara: str = "seguir"                # AUD-143 — de MODOS_DE_CAMARA
    estamina: float = 0.0                 # AUD-141 — máximo del medidor; 0 = apagada
    tiempo_bala: float = 0.0              # AUD-260 — segundos de reserva; 0 = apagado
    profundidad_min: float = 1.0          # AUD-277 — 2.5D; iguales = apagado
    profundidad_max: float = 1.0
    profundidad_curva: float = 1.0        # AUD-339
    orden_por_y: bool = False             # AUD-339 — ordena por ancla de profundidad, no sólo rect.centery
    sombras_proyectadas: bool = False     # AUD-278 (§20.15) — apagadas por defecto, cuestan
    climate: str = ""
    ambient_light: float | None = None    # None = no declarado, cae a la tabla por zona
    bloom: float | None = None
    vignette: float | None = None
    ambient_fx: str = ""
    ambient_fx_rate: float | None = None
    start_hour: float | None = None       # None = mediodía
    day_length: float = 0.0               # 0 = reloj congelado (sin ciclo día/noche)
    season: str = ""
    fog_of_war: float = 0.0               # AUD-111 — radio en px; 0 = apagada
    water_effect: bool = False            # AUD-111
    water_speed: float = 1.5              # AUD-240 — los 5 mandos del agua
    water_amplitude: int = 4
    water_frequency: float = 0.04
    water_alpha: int = 100
    water_tint: tuple[int, int, int] = (40, 80, 160)
    god_rays: float = 0.0                 # AUD-226 — sólo ruta GL, 0 = apagados


REQUIRED_LAYERS: tuple[str, ...]   # 8 capas TMX obligatorias — ver 06_TMX_SPEC.md §3.1


class StageLoader(ObjetosDeTiled):
    SCHEMA_VERSION: int = 1        # AUD-393/GAP-048 — versión del contrato TMX que este cargador entiende
    _entity_registry: dict[str, type[BaseEntity]] = {}

    @classmethod
    def register_entity(cls, type_name: str, entity_class: type[BaseEntity]) -> None: ...

    @classmethod
    def load(cls, tmx_path: Path) -> StageData:
        """
        Lanza FrameworkUsageError si:
        - falta alguna capa obligatoria (06_TMX_SPEC.md §3.1)
        - no se encuentra ningún objeto PlayerSpawn
        - se encuentra más de un objeto PlayerSpawn
        """
```

> **AUD-307.** `FrameworkUsageError` está definido en
> `src/framework/__init__.py`, no en `stage_loader.py` (que lo importa).
> **AUD-455.** `StageLoader` hereda de `ObjetosDeTiled` (no documentado) y
> tiene `SCHEMA_VERSION`, sin mencionar antes. Verificado contra
> `src/framework/stage/stage_data.py` y `stage_loader.py`.

### 11.4 `src/framework/stage/collision_system.py`

```python
class CollisionSystem:
    """Gestiona las actualizaciones de enemigos, hitbox de ataque → hurtbox de enemigo, hitstop y sacudida de pantalla."""

    def __init__(self, context: Any = None) -> None: ...
    def reset(self) -> None: ...
    def trigger_hitstop(self, duration: float = HITSTOP_DURATION) -> None: ...
    def is_hitstopped(self) -> bool: ...
    def update_hitstop(self, unscaled_dt: float, clock: Any = None) -> None: ...
    def step(self, dt: float) -> None: ...
    def apply_knockback(self, entity: "BaseEntity", impulse_x: float, impulse_y: float) -> None: ...
    def update_enemies(self, dt: float, player: "Player", stage: "StageData") -> None: ...
    def process_attack(self, dt: float, player: "Player", stage: "StageData",
                       camera: "Camera | None" = None, clock: Any = None) -> None: ...
    def remove_entity(self, entity: "BaseEntity") -> None: ...
    def draw_debug(self, surface: pygame.Surface, camera_offset: pygame.Vector2, ...) -> None: ...
```

> **AUD-455.** `__init__` recibe `context: Any = None` (opcional, no
> `GameContext` obligatorio); `camera` y `clock` en `process_attack` son
> opcionales; faltaban `trigger_hitstop`, `is_hitstopped`, `step`,
> `apply_knockback`, `remove_entity`, `draw_debug` — verificado contra
> `src/framework/stage/collision_system.py`.

### 11.5 `src/framework/stage/hazard_system.py`

```python
class HazardSystem:
    """Procesa los disparadores de mensaje, zonas de peligro y fosos de muerte."""

    def __init__(self, context: "GameContext") -> None: ...
    def update(self, dt: float, player: "Player", stage: "StageData",
              camara: Any = None) -> None: ...
    def arrancar_por_evento(self, evento: str, stage: "StageData | None" = None) -> int:
        """Dispara un ScrollZone por nombre de evento en vez de por colisión. Devuelve cuántos arrancaron."""
    def reset(self, stage: "StageData | None" = None) -> None: ...
```

> **AUD-455.** `update` recibe también `camara` opcional (para el scroll
> forzado); `reset` acepta un `stage` opcional; faltaba `arrancar_por_evento()`
> — verificado contra `src/framework/stage/hazard_system.py`.

### 11.6 `src/framework/stage/progression_system.py`

```python
class ProgressionSystem:
    """Gestiona los checkpoints, el next-trigger, la derrota de jefe y el flujo de escenario completado."""

    def __init__(self, context: "GameContext") -> None: ...
    def process_checkpoints(self, player: "Player", stage: "StageData",
                            checkpoints: list, hud: "HUD | None",
                            stage_key: str = "") -> "pygame.Vector2 | None":
        """Devuelve la posición del checkpoint si se activó uno nuevo. `stage_key` (AUD-156) es la
        identidad de guardado del escenario cuando difiere de `stage_id` del TMX."""

    def check_next_trigger(self, player: "Player", stage: "StageData") -> bool: ...
    def check_boss_defeat(self, stage: "StageData") -> bool: ...
    def update_complete_timer(self, dt: float) -> bool:
        """Devuelve True cuando expira el cronómetro de escenario completado y debe emitirse STAGE_COMPLETE."""

    @property
    def stage_complete(self) -> bool: ...
    @stage_complete.setter
    def stage_complete(self, value: bool) -> None: ...
    @property
    def complete_timer(self) -> float: ...
    def reset(self) -> None: ...
```

> **AUD-455.** `process_checkpoints` tiene el parámetro `stage_key` (AUD-156);
> `stage_complete` tiene setter, no es de sólo lectura — verificado contra
> `src/framework/stage/progression_system.py`.

### 11.7 `src/framework/stage/drawing_system.py`

```python
class DrawingSystem(GizmosDeDepuracion):
    """Gestiona todo el renderizado: parallax de fondo, mapa, entidades ordenadas por Y, superposiciones de UI, depuración."""

    def __init__(self) -> None: ...
    def draw(self, ctx: "DrawContext") -> None: ...
    def draw_ui(self, ctx: "DrawContext") -> None: ...


@dataclass
class DrawContext:
    """Todo lo que `DrawingSystem.draw()`/`draw_ui()` necesitan, en un solo objeto."""
    surface: pygame.Surface
    stage: "StageData | None" = None
    player: "Player | None" = None
    checkpoints: list[Any] | None = None
    camera: "Camera | None" = None
    hud: "HUD | None" = None
    msg_box: "MessageBox | None" = None
    banner: "ScreenBanner | None" = None
    paused: bool = False
    pause_selected: int = 0
    pause_options: list[str] | None = None
    particle_system: Any | None = None
    damage_numbers: Any | None = None
    ambient_particles: Any | None = None
    weather_system: Any | None = None
    trail_system: Any | None = None
    enemy_trail_system: Any | None = None       # estela de enemigos, separada de la del jugador
    tutorial_overlay: Any | None = None
    learning_overlay: Any | None = None
    dialogue_system: Any | None = None
    interactables: Any | None = None            # F4.1: recogibles, cerraduras, cofres, disparadores
    debug: bool = False
    mundo: Any | None = None                    # AUD-285: mundo ECS, sólo para conos de visión en F1
    fondo_del_escenario: Any | None = None       # AUD-162: pintura propia DETRÁS del mapa, ver abajo
```

> **AUD-455.** `DrawingSystem` cambió de una firma de 10 parámetros
> posicionales a un único objeto `DrawContext` — verificado contra
> `src/framework/stage/drawing_system.py`; la documentación anterior no
> reflejaba el cambio. También ahora hereda de `GizmosDeDepuracion` y expone
> `draw_ui()` como método separado de `draw()`.
>
> `fondo_del_escenario` (AUD-162) es un gancho `(surface, offset) -> None`
> que un escenario puede fijar para pintar **detrás** del mapa de baldosas —
> `draw()` empieza con `surface.fill(BG_COLOR)`, así que nada pintado antes de
> llamar a `draw()` sobrevive; este gancho se ejecuta después del parallax y
> antes del mapa, dentro del propio `draw()`.

### 11.8 `src/framework/scenes/stage_scene.py` — `StageScene` (GAP-056)

La clase que orquesta cada nivel jugable: carga un TMX y lo hace jugar. Es una
composición de `BaseScene` (§6.1) más 12 mixins de `stage_parts/` (AUD-152);
casi todos sus métodos internos son privados (`_`-prefijados) — lo de abajo es
la superficie realmente pública, la que toca un escenario de estudiante
(`class Stage1(StageScene)`) o quien lee `medidas_de_depuracion`/`stage_key`
desde fuera.

```python
class StageScene(MezclaDeAmbiente, SimulacionDeEscenario,
                 SenalesDeEscenario, SonidoDeEscenario,
                 DiagnosticoDeEscenario, CinematicasDeEscenario,
                 ArcoDelJugador, MundoDelEscenario, ActualizacionesDeEscenario,
                 DibujoDeEscenario, FantasmaDeCarrera, ConduccionDelBossRush,
                 BaseScene):
    #: Ruta del TMX. Una subclase la fija como atributo de clase, o la pasa a
    #: __init__; si ninguna de las dos existe, __init__ lanza TypeError.
    TMX_PATH: Path | None = None

    def __init__(self, context: GameContext, tmx_path: Path | None = None) -> None: ...

    # ── ganchos que un escenario de estudiante puede sobreescribir ──
    def on_stage_start(self) -> None:
        """Se llama una vez al entrar. Por defecto dispara el tutorial de movimiento."""
    def on_player_landed(self) -> None:
        """Al aterrizar tras un salto con movimiento horizontal. Dispara el tutorial de ataque."""
    def on_enemy_died(self, enemy: EnemyBase) -> None:
        """Registra la muerte en el bestiario (`Bestiary.id_de`) y dispara el
        tutorial avanzado la primera vez."""
    def on_next_trigger_entered(self) -> None:
        """Dispara el tutorial de checkpoint la primera vez."""
    def on_debug_toggle(self, enabled: bool) -> None:
        """No hace nada por defecto — gancho para que un escenario reaccione
        al F11."""
    def dibujar_fondo(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Pintura propia DETRÁS del mapa de baldosas (AUD-162). No hace nada
        por defecto; se llama tras el parallax y antes del mapa. Sobreescribir
        `draw()` sólo permite pintar ENCIMA de todo."""

    @property
    def stage_key(self) -> str:
        """La identidad del escenario: `STAGE_ID` de la clase si existe
        (gana), si no `stage_id` del TMX (AUD-156 — antes divergían y un
        escenario terminado no se marcaba completado)."""

    # ── heredados de los mixins de stage_parts/ (públicos) ──
    def medidas_de_depuracion(self) -> dict[str, object]:
        """`DiagnosticoDeEscenario` — entidades simuladas tras culling,
        partículas vivas, estadísticas del escuadrón (F11, AUD-283)."""
    def draw(self, surface: pygame.Surface) -> None:
        """`DibujoDeEscenario` — implementa el abstracto de `BaseScene`."""
    def dibujar_mundo(self, surface: pygame.Surface) -> None: ...
    def dibujar_ui(self, surface: pygame.Surface) -> None: ...
    @property
    def light_surface(self) -> pygame.Surface | None:
        """El mapa de luz del fotograma para la ruta GPU (AUD-343); `None` en
        software, donde la luz ya se aplicó en `dibujar_mundo`."""

    # ── de BaseScene, con comportamiento real ──
    def on_enter(self) -> None: ...
    def on_exit(self) -> None: ...
    def update(self, dt: float) -> None: ...
    def respawn(self) -> None:
        """La implementa `StageScene` (protocolo `_SceneWithRespawn` de
        `SceneManager`, §6.2) — es lo que hace que morir en un escenario
        reaparezca en vez de volver al título."""
```

Los 12 mixins de `stage_parts/` — todos con métodos internos salvo los ya
listados arriba — por responsabilidad: `MezclaDeAmbiente` (audio ambiental por
clima/hora, expone `MIN_AMBIENTE = 0.45` vía `SimulacionDeEscenario`),
`SimulacionDeEscenario` (estaciones, ciclo día/noche, `HORA_POR_DEFECTO`),
`SenalesDeEscenario` (EventBus del escenario), `SonidoDeEscenario` (música
dinámica y ambiente), `DiagnosticoDeEscenario` (consola F11, retirada de
entidades fallidas), `CinematicasDeEscenario` (secuencias guionizadas),
`ArcoDelJugador` (progresión de habilidades del jugador dentro del nivel),
`MundoDelEscenario` (el `World` ECS embebido, AUD-285), `ActualizacionesDeEscenario`
(orquesta el `update` por sistema), `DibujoDeEscenario` (ver arriba),
`FantasmaDeCarrera` (grabación/reproducción para el modo contrarreloj) y
`ConduccionDelBossRush` (encadenar jefes en el modo boss rush).

> **AUD-455 — GAP-056.** `StageScene` no tenía ninguna sección de API pese a
> ser la clase que orquesta cada nivel jugable y a la que se conecta
> directamente cada entrega de estudiante. Se documentan aquí los ganchos y
> métodos públicos reales, verificados contra
> `src/framework/scenes/stage_scene.py` y los 12 ficheros de `stage_parts/`.
> No se detalla la API interna completa de cada mixin (son casi enteramente
> privados — decisión deliberada, no un hueco). El resto de `src/framework/`
> que GAP-056 dejaba pendiente (`physics/`, `combate/`, `ai/`, `world/`,
> `academic/`) se documentó después en §20; `vfx/` en §20.13–20.25
> (GAP-057) — los dos huecos están resueltos, no pendientes.

---

## 12. Framework Processing — ColorTools y CurveTools

### 12.1 `src/framework/processing/color_tools.py`

```python
class ColorTools:
    @classmethod
    def rgb_to_hsv(cls, r: int, g: int, b: int) -> tuple[float, float, float]:
        """Devuelve (h: 0-360, s: 0-1, v: 0-1)."""

    @classmethod
    def hsv_to_rgb(cls, h: float, s: float, v: float) -> tuple[int, int, int]:
        """Devuelve (r, g, b), cada uno 0-255."""

    @classmethod
    def rgb_to_hsl(cls, r: int, g: int, b: int) -> tuple[float, float, float]: ...

    @classmethod
    def hsl_to_rgb(cls, h: float, s: float, l: float) -> tuple[int, int, int]: ...

    @classmethod
    def rgb_to_cmyk(cls, r: int, g: int, b: int) -> tuple[float, float, float, float]:
        """Devuelve (c, m, y, k), cada uno 0-1."""

    @classmethod
    def cmyk_to_rgb(cls, c: float, m: float, y: float, k: float) -> tuple[int, int, int]: ...

    @classmethod
    def alpha_blend(cls, src: pygame.Surface, dst: pygame.Surface, alpha: float) -> pygame.Surface:
        """out = src*alpha + dst*(1-alpha). Las superficies deben tener el mismo tamaño."""

    @classmethod
    def apply_tint(cls, surface: pygame.Surface, color: tuple[int, int, int]) -> pygame.Surface: ...

    @classmethod
    def surface_to_array(cls, surface: pygame.Surface) -> "np.ndarray":
        """Devuelve forma (W, H, 3) uint8, vía pygame.surfarray.array3d."""

    @classmethod
    def array_to_surface(cls, array: "np.ndarray") -> pygame.Surface:
        """Espera forma (W, H, 3) uint8."""
```

### 12.2 `src/framework/processing/curve_tools.py`

```python
class CurveTools:
    @classmethod
    def bezier(
        cls,
        control_points: list[tuple[float, float]],
        n_samples: int,
    ) -> list[tuple[float, float]]:
        """Grado = len(control_points) - 1. Calculado vía base de Bernstein."""

    @classmethod
    def b_spline(
        cls,
        control_points: list[tuple[float, float]],
        degree: int,
        n_samples: int,
    ) -> list[tuple[float, float]]: ...

    @classmethod
    def nurbs(
        cls,
        control_points: list[tuple[float, float]],
        weights: list[float],
        knots: list[float],
        degree: int,
        n_samples: int,
    ) -> list[tuple[float, float]]: ...

    @classmethod
    def catmull_rom(
        cls,
        control_points: list[tuple[float, float]],
        n_samples: int,
    ) -> list[tuple[float, float]]: ...

    @classmethod
    def build_bezier_path(
        cls,
        waypoints: list[pygame.Vector2],
        t: float,
    ) -> pygame.Vector2:
        """Interpolación suave Catmull-Rom entre waypoints en el parámetro t [0, 1].
        Pese al nombre, usa splines Catmull-Rom, no Bézier real.
        Lo usa BezierStrategy en flight_strategies.py."""

    @classmethod
    def sample_path(
        cls,
        points: list[tuple[float, float]],
        t: float,
    ) -> tuple[float, float]:
        """t en [0, 1]. Interpola entre la lista de puntos pre-muestreados."""
```

---

## 13. Framework Processing — FilterTools

### 13.1 `src/framework/processing/filter_tools.py`

```python
class FilterTools:
    @classmethod
    def compute_histogram(cls, surface: pygame.Surface) -> dict[str, "np.ndarray | int"]:
        """Devuelve {'r': ndarray(256,), 'g': ndarray(256,), 'b': ndarray(256,),
        'luminance': ndarray(256,), 'total_pixels': int}."""

    @classmethod
    def histogram_equalize(cls, surface: pygame.Surface) -> pygame.Surface: ...

    @classmethod
    def adjust_brightness(cls, surface: pygame.Surface, factor: float) -> pygame.Surface:
        """factor en [0.0, 4.0]. Lanza ValueError si está fuera de rango."""

    @classmethod
    def adjust_contrast(cls, surface: pygame.Surface, factor: float) -> pygame.Surface:
        """factor en [0.0, 4.0]."""

    @classmethod
    def stretch_contrast(cls, surface: pygame.Surface) -> pygame.Surface: ...

    @classmethod
    def apply_kernel(cls, surface: pygame.Surface, kernel: "np.ndarray") -> pygame.Surface:
        """kernel debe ser cuadrado, de tamaño impar, de 3x3 a 15x15. Lanza ValueError si no."""

    @classmethod
    def get_standard_kernel(cls, name: str) -> "np.ndarray":
        """name en {'identity','sharpen','box_blur','box_blur_5','edge_laplacian',
        'emboss','ridge','sobel_x','sobel_y'}. Lanza KeyError listando los nombres válidos."""

    @classmethod
    def gaussian_blur(cls, surface: pygame.Surface, sigma: float) -> pygame.Surface:
        """sigma en (0.0, 10.0]."""

    @classmethod
    def sobel_edge(cls, surface: pygame.Surface) -> pygame.Surface:
        """Devuelve una superficie en escala de grises como RGB (sin alfa)."""

    @classmethod
    def canny_edge(
        cls,
        surface: pygame.Surface,
        low_threshold: int,
        high_threshold: int,
    ) -> pygame.Surface:
        """1 <= low_threshold < high_threshold <= 255. Devuelve una superficie RGB binaria."""

    @classmethod
    def sobel_edge_propio(cls, surface: pygame.Surface) -> pygame.Surface:
        """Sobel implementado a mano (F2.3), sin OpenCV — ver `edge_detection.sobel`."""

    @classmethod
    def canny_edge_propio(
        cls,
        surface: pygame.Surface,
        low_threshold: int,
        high_threshold: int,
        sigma: float = 1.4,
    ) -> pygame.Surface:
        """Canny implementado a mano en sus cinco pasos — ver `edge_detection.canny`.
        Mismos umbrales que `canny_edge` para poder intercambiarlas."""
```

> **AUD-455.** Faltaban `sobel_edge_propio()` y `canny_edge_propio()`: las
> versiones propias, paso a paso, que las Unidades VII y VIII usan porque en
> esos temas el algoritmo **es** el contenido — `cv2.Canny(...)` enseña una
> API, no un algoritmo. Conviven con las versiones de OpenCV a propósito (el
> laboratorio compara ambas); ver `src/framework/processing/edge_detection.py`
> — verificado contra `src/framework/processing/filter_tools.py`.

---

## 14. Framework Processing — VisionTools

### 14.1 `src/framework/processing/vision_tools.py`

```python
from dataclasses import dataclass

@dataclass
class ComponentResult:
    label_array: "np.ndarray"        # int32, forma (H, W)
    num_components: int
    component_sizes: dict[int, int]
    label_surface: pygame.Surface

@dataclass
class RegionInfo:
    label: int
    area: int
    centroid: tuple[float, float]
    bounding_rect: pygame.Rect
    eccentricity: float
    solidity: float
    perimeter: float


class VisionTools:
    @classmethod
    def threshold_binary(cls, surface: pygame.Surface, threshold: int) -> pygame.Surface:
        """0 <= threshold <= 255."""

    @classmethod
    def threshold_otsu(cls, surface: pygame.Surface) -> tuple[pygame.Surface, int]:
        """Devuelve (mask_surface, computed_threshold)."""

    @classmethod
    def morphological_erode(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface: ...

    @classmethod
    def morphological_dilate(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface: ...

    @classmethod
    def morphological_open(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface: ...

    @classmethod
    def morphological_close(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface: ...

    @classmethod
    def connected_components(cls, mask_surface: pygame.Surface) -> "ComponentResult": ...

    @classmethod
    def filter_components_by_area(
        cls,
        result: "ComponentResult",
        min_area: int,
        max_area: int,
    ) -> "ComponentResult": ...

    @classmethod
    def analyze_regions(cls, mask_surface: pygame.Surface) -> list["RegionInfo"]:
        """Ordenado por área descendente."""

    @classmethod
    def largest_region(cls, mask_surface: pygame.Surface) -> "RegionInfo | None": ...

    @classmethod
    def watershed_segment(
        cls,
        surface: pygame.Surface,
    ) -> tuple[pygame.Surface, "np.ndarray"]:
        """Devuelve (label_surface, label_array)."""

    @classmethod
    def extract_features(cls, surface: pygame.Surface, method: str = "hog") -> "np.ndarray":
        """method en {'hog','lbp','color_hist','combined'}."""

    @classmethod
    def extract_hog(cls, surface: pygame.Surface) -> "np.ndarray":
        """Devuelve forma (512,) para el redimensionado canónico de 32x32."""

    @classmethod
    def extract_lbp(cls, surface: pygame.Surface) -> "np.ndarray":
        """Devuelve forma (256,)."""

    @classmethod
    def extract_color_histogram(cls, surface: pygame.Surface, bins: int = 256) -> "np.ndarray":
        """Devuelve forma (bins*3,). 4 <= bins <= 256."""

    @classmethod
    def find_contours(cls, mask_surface: pygame.Surface) -> list["np.ndarray"]: ...

    @classmethod
    def bounding_boxes_from_mask(cls, mask_surface: pygame.Surface) -> list[pygame.Rect]: ...
```

---

## 15. Framework Processing — PatternRecognitionTools

### 15.1 `src/framework/processing/pattern_recognition_tools.py`

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class TrainedModel:
    model_type: str                  # 'knn' | 'tree' | 'forest' | 'svm'
    estimator: Any                   # Pipeline de sklearn ya entrenado (escalador + clasificador)
    classes: list[str]
    feature_method: str              # 'hog' | 'lbp' | 'color_hist' | 'combined' | 'external'
    feature_length: int
    training_accuracy: float
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class EvaluationResult:
    accuracy: float
    per_class_accuracy: dict[str, float]
    confusion_matrix: "np.ndarray"
    report: str


class PatternRecognitionTools:
    # AUD-307: los `extract_hog/lbp/color_histogram/combined` que documentaba
    # esta sección NO existen aquí. La extracción de rasgos vive en
    # `VisionTools` (§14.1): `extract_features/hog/lbp/color_histogram`.

    # --- Cadena de entrenamiento (sólo uso fuera de línea) ---
    @classmethod
    def train(
        cls,
        X: "np.ndarray",          # forma (n_samples, n_features), float32
        y: "np.ndarray",          # forma (n_samples,)
        model_type: str,          # 'knn' | 'tree' | 'forest' | 'svm'
        feature_method: str = "hog",
        **kwargs: Any,
    ) -> "TrainedModel": ...

    @classmethod
    def evaluate(
        cls,
        model: "TrainedModel",
        X_test: "np.ndarray",
        y_test: "np.ndarray",
    ) -> "EvaluationResult": ...

    # --- Serialización ---
    @classmethod
    def save_model(cls, model: "TrainedModel", path: str | Path) -> None:
        """path debe terminar en .pkl. Crea los directorios padre si hace falta."""

    @classmethod
    def load_model(cls, path: str | Path) -> "TrainedModel":
        """Lanza FileNotFoundError / TypeError según documenta 13_PATTERN_RECOGNITION_SPEC.md §11.2."""

    # --- Registro de modelos (sólo en memoria) ---
    @classmethod
    def register_model(cls, name: str, model: "TrainedModel") -> None: ...
    @classmethod
    def get_model(cls, name: str) -> "TrainedModel":
        """Lanza KeyError listando los nombres disponibles si no se encuentra."""
    @classmethod
    def list_models(cls) -> list[str]: ...

    # --- Inferencia (uso en tiempo de ejecución) ---
    @classmethod
    def classify(cls, features: "np.ndarray", model: "TrainedModel") -> str: ...

    @classmethod
    def classify_proba(cls, features: "np.ndarray", model: "TrainedModel") -> dict[str, float]:
        """Lanza NotImplementedError si model.model_type == 'tree'."""

    @classmethod
    def predict(
        cls,
        model: "TrainedModel",
        surface: pygame.Surface,
        method: str | None = None,
    ) -> str:
        """Combina extract_features(surface, method) + classify(). Con
        method=None (por defecto) usa model.feature_method, no 'hog'."""

    # --- Informe de entrenamiento (matplotlib, opcional) ---
    @classmethod
    def generate_training_report(
        cls,
        model: "TrainedModel",
        X_test: "np.ndarray | None" = None,
        y_test: "np.ndarray | None" = None,
        save_path: str | Path | None = None,
        figure_size: tuple[int, int] = (8, 6),
        dpi: int = 100,
    ) -> "pygame.Surface | None":
        """Matriz de confusión (si hay datos de prueba) + barras de precisión
        por clase, renderizadas a una Surface. Devuelve None si matplotlib no
        está instalado — igual que scikit-learn (invariante 7), es opcional en
        tiempo de ejecución."""
```

> **AUD-455.** `train()` le faltaba `feature_method: str = "hog"`; `predict()`
> tenía por defecto `method: str = "hog"` cuando el real es `method: str |
> None = None` (cae a `model.feature_method`, no siempre HOG); faltaba
> `generate_training_report()` entero — verificado contra
> `src/framework/processing/pattern_recognition_tools.py`.

---

## 16. Escenas de demostración académica

### 16.1 `src/engine/scenes/demo_menu_scene.py`

```python
class DemoMenuScene(BaseScene):
    def __init__(self, context: GameContext) -> None: ...
    # El menú de escenas demo/lab, derivado de framework.academic.curriculum
    # (AUD-095): consulta a SesionAcademica qué unidad tiene aprobada el
    # estudiante y bloquea las demos del temario que aún no le tocan.
    # Implementa los métodos abstractos de BaseScene. Sin API pública adicional.
```

### 16.2 `src/engine/scenes/filter_demo_scene.py`

```python
class FilterDemoScene(BaseScene):
    def __init__(self, context: GameContext) -> None: ...
    # Índice de modo interno 0-9 (10 modos, incluye CONV_STEP) según
    # 15_ACADEMIC_DEMO_SCENES.md §3.3.
    # Sin API pública más allá de BaseScene — toda la interacción es sondeo interno de InputManager.
```
> **AUD-455.** Eran 0-8 (9 modos); el real es 0-9 (10, falta `CONV_STEP`).
> `__init__` recibe `context: GameContext` obligatorio, no `() -> None`.
> Verificado contra `src/engine/scenes/filter_demo_scene.py`.

### 16.3 `src/engine/scenes/vision_demo_scene.py`

```python
class VisionDemoScene(BaseScene):
    def __init__(self, context: GameContext) -> None: ...
    # Índice de modo interno 0-9 según 15_ACADEMIC_DEMO_SCENES.md §4.3.
```
> **AUD-455.** `__init__` recibe `context: GameContext` obligatorio, no
> `() -> None`. Verificado contra `src/engine/scenes/vision_demo_scene.py`.

### 16.4 `src/engine/scenes/pattern_demo_scene.py`

```python
class PatternDemoScene(BaseScene):
    def __init__(self, context: GameContext) -> None: ...
    # Índice de modo interno 0-5 (6 modos, incluye TREE_VIEW) según
    # 15_ACADEMIC_DEMO_SCENES.md §5.3.
    # Carga PatternRecognitionTools.load_model(ASSETS_DIR / "models" / "professor_sample.pkl")
    # en on_enter() por defecto.
```
> **AUD-455.** Eran 0-4 (5 modos); el real es 0-5 (6, falta `TREE_VIEW`).
> `__init__` recibe `context: GameContext` obligatorio, no `() -> None`.
> Verificado contra `src/engine/scenes/pattern_demo_scene.py`.

### 16.5 Escenas de laboratorio teórico (Unidades II–VI/VIII)

Todas las escenas de laboratorio son subclases de `BaseScene` en `src/engine/scenes/`. Ciclo de modo interno con `TAB`, reinicio con `R`, retorno con `ESC`.

#### `src/engine/scenes/vector_lab_scene.py`
```python
class VectorLabScene(BaseScene):
    # Modos: FREE_MOVE, CHASE, ORBIT, DISTANCE_CHECK
    # Aritmética vectorial interactiva: normalización, producto punto, movimiento de persecución
    # Dos puntos arrastrables con una flecha del vector AB dibujada entre ellos
    # La tecla N alterna la visualización del vector normalizado
```

#### `src/engine/scenes/transform_lab_scene.py`
```python
class TransformLabScene(BaseScene):
    # Modos: TRANSLATE, ROTATE, SCALE, SHEAR, COMPOSITE
    # Transformaciones afines 2D con matriz 3x3 mostrada en vivo
    # Contorno fantasma de la forma original, forma transformada rellena
    # N alterna el panel de matriz
```

#### `src/engine/scenes/curve_editor_scene.py`
```python
class CurveEditorScene(BaseScene):
    # Modos: BEZIER_QUAD, BEZIER_CUBIC, BEZIER_HIGH, CATMULL_ROM, BSPLINE, DE_CASTELJAU
    # Puntos de control arrastrables con el ratón; D alterna la visualización de de Casteljau
    # +/- añaden/quitan puntos de control (modos BEZIER_HIGH, BSPLINE)
    # Las teclas 1-5 saltan directamente a los modos
```

#### `src/engine/scenes/interpolation_lab_scene.py`
```python
class InterpolationLabScene(BaseScene):
    # Modos: LERP, EASING_CURVES, KEYFRAME_ANIM
    # Funciones de easing: 10 funciones (Linear, Quad, Cubic, Bounce, Elastic, Sine)
    # ARRIBA/ABAJO ciclan la función de easing, IZQUIERDA/DERECHA ajustan t, ESPACIO alterna la auto-animación
```

#### `src/engine/scenes/color_theory_scene.py`
```python
class ColorTheoryScene(BaseScene):
    # Modos: RGB, HSV, HSL, CMYK, ALPHA_BLEND, CHALLENGE
    # Deslizadores por componente de color, muestra en vivo, lectura hexadecimal
    # SHIFT alterna la visualización paso a paso del algoritmo de conversión
    # ESPACIO envía el intento del desafío
```

#### `src/engine/scenes/noise_lab_scene.py`
```python
class NoiseLabScene(BaseScene):
    # Modos: VALUE_NOISE, PERLIN_NOISE, FRACTAL_NOISE
    # Parámetros: Octavas (1-8), Persistencia (0-1), Lacunaridad (1-8), Escala (0.005-0.5), Semilla (0-9999)
    # ESPACIO aleatoriza la semilla, R reinicia a los valores por defecto
```

#### `src/engine/scenes/collision_lab_scene.py`
```python
class CollisionLabScene(BaseScene):
    # Modos: NO_COLLISION, Y_FIRST, X_FIRST
    # Demuestra la resolución de colisión por eje separado frente al bug de escalar paredes en Y_FIRST
    # La tecla B demuestra automáticamente el bug de escalar paredes en modo Y_FIRST
    # Plataformas de un solo sentido, gravedad, salto, superposición de información de colisión
```

---

## 17. Escenas del motor — infraestructura

### 17.1 `src/engine/scenes/scene_registry.py`

```python
from typing import Callable

class SceneRegistry:
    """Contenedor de inyección de dependencias para la construcción perezosa de escenas."""

    def __init__(self) -> None: ...

    def register(self, key: str, factory: SceneFactory) -> None:
        """Registra un constructor de escena bajo una clave."""

    def build(self, key: str, ctx: GameContext) -> BaseScene | None:
        """Construye y devuelve una instancia de escena. Devuelve None si no está registrada."""

    @property
    def keys(self) -> frozenset[str]:
        """Todas las claves de escena registradas. Es una `@property`, no un
        método — se lee `registry.keys`, no `registry.keys()`."""


def register_demo_scenes() -> None:
    """Module-level function (no de SceneRegistry): registra las escenas demo/lab."""
```

<!-- cita-historica -->
> **AUD-307.** `list_scenes` no existe: usa `keys`. `register_demo_scenes` es
> función de módulo, no método de la clase. `GameContext` no vive aquí — se
> documenta en §2.5 (`src/engine/core/game_context.py`); `scene_registry.py`
> sólo lo importa.
<!-- /cita-historica -->
> **AUD-455.** `keys` es una `@property`, no un método — el ejemplo con
> `def keys(self)` invitaba a llamarla `registry.keys()`, que falla porque
> un `frozenset` no es invocable. Verificado contra
> `src/engine/scenes/scene_registry.py`.

### 17.2 `src/engine/scenes/debug_overlay.py`

```python
class DebugOverlay:
    """Consola de depuración conmutable con F11. Se renderiza por encima de todo el contenido de la escena."""

    def __init__(self, event_bus: EventBus | None = None) -> None: ...

    @property
    def visible(self) -> bool: ...

    def handle_input(self, input_manager: Any) -> None: ...

    def draw(self, surface: pygame.Surface, fps: float, ...) -> None: ...
    # F11: alterna la superposición
    # F4: instantánea de la cola de eventos
    # F5: lista de escenas registradas
    # F6: navegador del árbol de dependencias de módulos
```

> **AUD-307.** El overlay no expone `toggle()` ni `update(dt)`; alterna por
> entrada (`handle_input`) y su estado es la propiedad `visible` (antes
> `is_active`).

### 17.3 `src/engine/scenes/param_panel.py`

```python
class ParamPanel:
    """Panel de control de parámetros reutilizable para escenas de laboratorio/demo.
    No guarda posición ni fuente en el constructor: `x`/`y` se pasan en cada `draw()`."""

    def __init__(self) -> None: ...

    def add_int(self, name: str, default: int, vmin: int, vmax: int, step: int = 1,
                on_change: Callable[[int], None] | None = None,
                fmt: str | None = None) -> None: ...
    def add_float(self, name: str, default: float, vmin: float, vmax: float, step: float = 0.1,
                  on_change: Callable[[float], None] | None = None,
                  fmt: str | None = None) -> None: ...

    @property
    def values(self) -> dict[str, Any]:
        """Valor actual de cada parámetro, por nombre."""

    def __getitem__(self, name: str) -> Any: ...
    def __setitem__(self, name: str, value: Any) -> None: ...
    def reset_to_defaults(self) -> None: ...
    def select(self, name: str) -> None:
        """Da el foco a un parámetro por nombre."""
    def cycle_selected(self, direction: int = 1) -> None:
        """Cicla el parámetro con foco. ARRIBA/ABAJO en `handle_input`."""
    def adjust_selected(self, direction: int) -> None:
        """Ajusta el parámetro con foco un `step`. IZQUIERDA/DERECHA en `handle_input`."""

    def handle_input(self, im: "InputManager", dt: float) -> None:
        """Lee ARRIBA/ABAJO (ciclar) e IZQUIERDA/DERECHA (ajustar). `dt` no se usa hoy."""

    def draw(self, surface: pygame.Surface, x: int, y: int) -> None: ...
```

> **AUD-455.** El `__init__` documentado (`x, y, width, font`) no existe: el
> real es `__init__(self) -> None`, y la posición/fuente se resuelven en
> `draw(surface, x, y)`, no en el constructor. `add_int`/`add_float` tenían
> `on_change`/`fmt` sin documentar; `handle_input` usa ARRIBA/ABAJO/IZQUIERDA/
> DERECHA (no `TAB`, que el texto anterior decía) y toma un `dt` real, no sólo
> `input_manager`. Faltaban `values`, `__getitem__`, `__setitem__`,
> `reset_to_defaults`, `select`, `cycle_selected`, `adjust_selected`.
> Verificado contra `src/engine/scenes/param_panel.py`.
### 17.4 `src/engine/scenes/demo_layout.py`

```python
# Constantes de layout a nivel de módulo y funciones auxiliares de dibujo.
# Las usan todas las escenas académicas de demo/laboratorio.
#
# AUD-094 — todo lo de abajo se CALCULA de settings.INTERNAL_WIDTH/HEIGHT, no
# son literales fijos. Antes de AUD-094 eran literales heredados de la
# maqueta 320x224 original (TOP_BAR_H=22, paneles de 160x180…); sobre 800x600
# dejaban 3/4 de la pantalla vacías. No hay LEFT_PANEL_H/RIGHT_PANEL_H
# independientes: los dos paneles comparten PANEL_H.

TOP_BAR_H: int          # max(28, min(48, INTERNAL_HEIGHT * 0.055))
BOTTOM_BAR_H: int       # max(20, min(32, INTERNAL_HEIGHT * 0.04))
PANEL_GUTTER: int = 24  # canaleta fija en px entre los dos paneles
PANEL_W: int            # max(200, (INTERNAL_WIDTH - PANEL_GUTTER) // 2)
LEFT_PANEL_W: int        # = PANEL_W
RIGHT_PANEL_W: int       # = PANEL_W
PANEL_H: int            # área entre barras menos una reserva
PANEL_SIZE: tuple[int, int]   # (PANEL_W, PANEL_H)
TOP_BAR_Y: int = 0
LEFT_PANEL_X: int = 0
LEFT_PANEL_Y: int       # = TOP_BAR_H
RIGHT_PANEL_X: int      # = INTERNAL_WIDTH - RIGHT_PANEL_W
RIGHT_PANEL_Y: int      # = TOP_BAR_H
BOTTOM_BAR_Y: int       # = INTERNAL_HEIGHT - BOTTOM_BAR_H
CENTER_X: int           # = LEFT_PANEL_W + 8
CENTER_W: int           # hueco entre paneles, para lecturas/controles

# ── Área útil y lienzo de autoría (AUD-094) ─────────────────────────
CONTENT_X: int = 0
CONTENT_Y: int          # = TOP_BAR_H
CONTENT_W: int          # = INTERNAL_WIDTH
CONTENT_H: int          # = BOTTOM_BAR_Y - TOP_BAR_H
AUTHORED_W: int = 320   # tamaño para el que se escribieron las demos originalmente
AUTHORED_H: int = 224
TOLERANCIA_CENTRADO: float = 0.20
OCUPACION_MINIMA: float = 0.30

def area_de_contenido() -> pygame.Rect:
    """El rectángulo utilizable, sin las barras."""

def centrar_bloque(ancho: int, alto: int) -> tuple[int, int]:
    """Esquina superior izquierda para que un bloque quede centrado."""

def esta_centrado(rect: pygame.Rect, tolerancia: float = TOLERANCIA_CENTRADO) -> bool:
    """Sólo comprueba el eje horizontal — a propósito, ver docstring real."""

def area_con_columna(ancho_columna: int) -> tuple[pygame.Rect, pygame.Rect]:
    """Parte el área útil en (columna_de_texto, escenario)."""

class Lienzo:
    """Traduce coordenadas de autoría (320x224 por defecto) al área útil real,
    escaladas de forma UNIFORME (mismo factor en X e Y — geometría, no UI) y
    centradas. `Lienzo(320, 224)` sobre 800x600 da escala ~2.42."""

    def __init__(self, ancho: int = AUTHORED_W, alto: int = AUTHORED_H,
                margen: int = 8, escala_maxima: float = 4.0,
                area: pygame.Rect | None = None) -> None: ...

    def x(self, valor: float) -> int: ...
    def y(self, valor: float) -> int: ...
    def p(self, x: float, y: float) -> tuple[int, int]:
        """Un punto de autoría en coordenadas de pantalla."""
    def l(self, valor: float) -> int:
        """Una longitud (radio, grosor, ancho) escalada, mínimo 1."""
    def r(self, x: float, y: float, w: float, h: float) -> pygame.Rect: ...
    def rect(self) -> pygame.Rect:
        """El lienzo entero, ya en pantalla."""
    def inverso(self, sx: float, sy: float) -> tuple[float, float]:
        """De pantalla a autoría. Para el ratón."""

# ── Colores y fuentes (AUD-044: vienen de engine.ui.theme.Theme) ───
COLOR_BG = Theme.BG
COLOR_TOP_BAR_BG = Theme.SURFACE
COLOR_BOTTOM_BAR_BG = Theme.SURFACE
COLOR_DIVIDER = Theme.BORDER
COLOR_TEXT = Theme.TEXT
COLOR_HIGHLIGHT = Theme.ACCENT
COLOR_ACCENT: tuple[int, int, int] = (108, 172, 255)
COLOR_ERROR = Theme.DANGER
COLOR_GOLD = Theme.ACCENT
FONT_SMALL: int
FONT_MEDIUM: int
FONT_LARGE: int

def clear_demo_font_cache() -> None: ...

def draw_top_bar(surface: pygame.Surface, title: str, unit: str) -> None: ...
def draw_bottom_bar(surface: pygame.Surface, text: str) -> None: ...
def draw_bottom_bar_error(surface: pygame.Surface, error: str) -> None: ...
def draw_divider(surface: pygame.Surface) -> None: ...
def draw_panel_border(surface: pygame.Surface, panel_rect: pygame.Rect) -> None: ...
def draw_save_notification(surface: pygame.Surface, saved_path: str, font: pygame.font.Font) -> None: ...
def draw_histogram_bars(
    surface: pygame.Surface, rect: pygame.Rect,
    hist_r: list[int], hist_g: list[int], hist_b: list[int],
    bar_w: int = 2, max_h: int = 40,
) -> None: ...
```

<!-- cita-historica -->
> **AUD-307.** `draw_panel_label` no existe.
<!-- /cita-historica -->
> **AUD-455 — reescritura completa.** Los ocho literales de layout que
> documentaba esta sección (`LEFT_PANEL_W = 160`, `TOP_BAR_H = 22`, etc.) eran
> los de la maqueta 320x224 original; AUD-094 los sustituyó por fórmulas
> derivadas de `settings.INTERNAL_WIDTH/HEIGHT` y ninguno de los valores
> fijos documentados aquí sobrevivió a ese cambio. `draw_top_bar` y
> `draw_bottom_bar` ya no toman `font` (usan un caché interno,
> `_get_demo_font`). Faltaban por completo `PANEL_GUTTER`, `PANEL_W`,
> `PANEL_H`, `PANEL_SIZE`, `CENTER_X`/`CENTER_W`, la familia `CONTENT_*`,
> `AUTHORED_W/H`, `TOLERANCIA_CENTRADO`, `OCUPACION_MINIMA`,
> `area_de_contenido`, `centrar_bloque`, `esta_centrado`, `area_con_columna`,
> la clase `Lienzo` completa (7 métodos), los colores `COLOR_*`, las fuentes
> `FONT_*` y `clear_demo_font_cache`. Verificado contra
> `src/engine/scenes/demo_layout.py`.

### 17.5 `src/engine/scenes/demo_utils.py`

```python
class SourceSurfaceManager:
    """Gestiona las 5 opciones de superficie fuente que se ciclan con ESPACIO en las escenas demo."""

    def cycle(self) -> None:
        """Cicla a la siguiente fuente."""

    @property
    def current_source(self) -> pygame.Surface | None: ...
    @property
    def current_name(self) -> str: ...
    def freeze(self) -> None: ...
    def unfreeze(self) -> None: ...
    @property
    def is_frozen(self) -> bool: ...


class FrameThrottle:
    """Limita operaciones costosas a cada N fotogramas."""

    def __init__(self) -> None: ...
    def tick(self) -> int: ...
    def should_update(self, interval: int) -> bool:
        """Devuelve True una vez cada N fotogramas."""
    def reset(self) -> None: ...


class ErrorDisplay:
    """Muestra mensajes de error transitorios en la barra inferior."""

    def __init__(self, duration: float = 2.0) -> None: ...
    def set_error(self, message: str) -> None:
        """Trunca a 60 caracteres."""
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface, font: pygame.font.Font, x: int, y: int) -> None: ...

    @property
    def message(self) -> str: ...
    @property
    def active(self) -> bool: ...


def build_default_sources() -> SourceSurfaceManager:
    """Construye el `SourceSurfaceManager` por defecto de las escenas demo:
    sprite del jugador, fondo, tileset, una superficie "captura en vivo"
    (no disponible) y un enemigo — con superficie de color sólido de reserva
    para cada una si el asset real no carga."""


def save_png(scene_prefix: str, mode_name: str, surface: pygame.Surface | None) -> str:
    """Guarda en tests/output/demo/{prefix}_{mode}_{timestamp}.png. Devuelve
    la ruta como cadena, o "" si `surface` es None."""
```

> **AUD-455.** `ErrorDisplay.draw` tomaba `rect`, no `(x, y)` — el real recibe
> coordenadas sueltas. `save_png` tenía el orden de parámetros cambiado
> (`surface` primero; el real lo recibe último). Faltaban `__init__`, la
> propiedad `message` y la función `build_default_sources()`. Verificado
> contra `src/engine/scenes/demo_utils.py`.

### 17.6 `src/engine/scenes/options_scene.py`

```python
class OptionsScene(BaseScene):
    """Menú de opciones como una lista de teclado (`MenuList`), igual que el
    resto del juego (AUD-452 — antes era la única pantalla con otro lenguaje
    visual). Diez ajustes, no tres: música, efectos, dificultad, daltonismo,
    subtítulos, idioma, tamaño de texto, movimiento reducido, mantener
    pulsado y contorno de enemigos — más "CONTROLES" y "VOLVER". No hay
    ajuste de escala de pantalla."""

    FILAS_VISIBLES: int = 5

    def __init__(self, context: GameContext) -> None: ...
    def valor_de(self, clave: str) -> Any:
        """El valor vigente de un ajuste, leído de las preferencias vivas."""
    def cambiar_valor(self, direccion: int) -> None:
        """Mueve el ajuste enfocado un paso y lo aplica en el acto."""
    def on_enter(self) -> None: ...
    def on_exit(self) -> None: ...
    def update(self, dt: float) -> None:
        """ARRIBA/ABAJO navegan la lista, IZQUIERDA/DERECHA cambian el valor
        del ajuste enfocado, CONFIRM activa CONTROLES/VOLVER."""
    def draw(self, surface: pygame.Surface) -> None: ...
```

> **AUD-455.** La sección describía un menú de 3 ajustes con escala de
> pantalla, que no es el real desde AUD-452 (10 ajustes, lista `MenuList`,
> sin escala de pantalla). Faltaban los métodos públicos `valor_de` y
> `cambiar_valor`. Verificado contra `src/engine/scenes/options_scene.py`.

### 17.7 `src/engine/scenes/demo_common.py`

```python
# Módulo de compatibilidad heredado. Re-exporta todos los símbolos públicos de
# demo_layout y demo_utils para que las importaciones existentes en el código
# de escenas demo sigan funcionando sin modificación.
```

### 17.8 Las 28 escenas de contenido/menú restantes (GAP-055, resuelto)

16 de las 28 sólo implementan los 4 métodos abstractos de `BaseScene`
(§6.1) — `on_enter`/`on_exit`/`update`/`draw` — sin API pública adicional, y
su `__init__` toma únicamente `context: GameContext`:
`AchievementScene`, `BestiaryScene`, `ComboDemoScene`, `EndCreditsScene`,
`InventoryScene`, `KeybindingScene`, `LeaderboardScene`,
`PipelineBuilderScene`, `ProgressScene`, `SandboxScene`, `ShopScene`,
`SkillTreeScene`, `StageWizardScene`, `StoryScene` (y su
`EmptyFallbackStage` interno), `TutorialScene`, `WorldMapScene`.

Excepciones — `__init__` con parámetros propios:

```python
class GameOverScene(BaseScene):
    def __init__(self, context: GameContext, stage_scene: BaseScene) -> None: ...
    # Necesita la escena de escenario que falló para poder reintentarla.

class UnitTheoryScene(BaseScene):
    def __init__(self, context: GameContext, id_unidad: str) -> None: ...

class StageErrorScene(BaseScene):
    """Pantalla de error de carga de escenario. Recibe `retry` en vez de la
    escena a recrear porque la escena que falló puede necesitar argumentos
    que esta pantalla no conoce (desacopla el reintento del escenario)."""
    def __init__(
        self, context: GameContext, message: str, *,
        title: str = "NO SE PUDO CARGAR EL ESCENARIO",
        retry: Callable[[], None] | None = None,
    ) -> None: ...
    def process_events(self, events: list[pygame.event.Event]) -> None: ...

class LoadGameScene(BaseScene):
    def __init__(self, context: GameContext) -> None: ...
    @property
    def creando(self) -> bool: ...
    @property
    def nombre_en_curso(self) -> str: ...
    def seleccionar(self, indice: int) -> None:
        """Mueve la selección a una ranura concreta (0 = ranura 1)."""
    def process_events(self, events: list[pygame.event.Event]) -> None: ...

class StudentLoginScene(BaseScene):
    def __init__(self, context: GameContext) -> None: ...
    def process_events(self, events: list[pygame.event.Event]) -> None: ...

class TitleScene(BaseScene):
    OPCIONES_VISIBLES: int = 4   # AUD-446 — antes 14 a la vez, peleaban con el logo
    def __init__(self, context: GameContext) -> None: ...
    def logo_rect(self) -> pygame.Rect: ...
    def primera_fila_y(self) -> int:
        """Dónde empieza la primera opción visible del menú."""

class SplashScene(BaseScene):
    def __init__(self, context: GameContext) -> None: ...
    @property
    def tarea_en_curso(self) -> str:
        """Qué se está precalentando en segundo plano (partículas, IA), o
        vacío. Se anuncia antes de empezar para que el fotograma congelado no
        se lea como un cuelgue."""


# ── Clases auxiliares que no son BaseScene ──────────────────────

class CodePanel:
    """Overlay que muestra el código fuente de un algoritmo sobre una escena
    de laboratorio. Se activa con la tecla C."""
    def __init__(self, code_key: str = "normalize",
                custom_lines: list[str] | None = None) -> None: ...
    @property
    def active(self) -> bool: ...
    def toggle(self) -> None: ...
    def set_code(self, key: str, lines: list[str] | None = None) -> None: ...

class LoadTask:
    def __init__(self, name: str, fn: Callable[[], None], weight: float = 1.0) -> None: ...
    # Atributos públicos: name, fn, weight, done: bool

class LoadingScene(BaseScene):
    UMBRAL_PARA_MOSTRARSE: float = 0.25   # segundos; por debajo se lee como parpadeo, no como carga
    def __init__(
        self, context: GameContext, next_scene: BaseScene | None = None,
        tasks: list[LoadTask] | None = None,
        umbral_para_mostrarse: float = UMBRAL_PARA_MOSTRARSE,
    ) -> None: ...
    def set_next_scene(self, scene: BaseScene) -> None: ...
    def add_task(self, task: LoadTask) -> None: ...

class QuizManager:
    """No es una escena — la instancia y la lleva una escena de laboratorio."""
    def __init__(self, questions: list[dict[str, Any]]) -> None: ...
    @property
    def active(self) -> bool: ...
    def toggle(self) -> None: ...
    def handle_input(self, im: Any) -> None: ...
    def close(self) -> None: ...

class TutorialOverlay:
    """No es una escena. Se activa con T, navega con IZQUIERDA/DERECHA."""
    def __init__(self, lab_key: str = "vector_lab") -> None: ...
    @property
    def active(self) -> bool: ...
    def toggle(self) -> None: ...
    def set_lab(self, lab_key: str) -> None: ...
    def next_step(self) -> None: ...
    def prev_step(self) -> None: ...
```

`boss_rush_entry.py` **no es una escena**: es un módulo de funciones a nivel
de módulo (AUD-191) que compone `BossRushMode` con los jefes que
`stage_registry` conoce (reconocidos por `"boss"` en su `stage_id`, no por
una lista escrita a mano) y arranca la cola de escenarios:

```python
MARCA_DE_JEFE: str = "boss"

def escenarios_de_jefe() -> list[tuple[str, type[BaseScene]]]:
    """Los jefes del juego, en orden de campaña."""
def construir_modo(jefes: list[tuple[str, type[BaseScene]]]) -> BossRushMode: ...
def empezar_boss_rush(context: GameContext) -> BossRushMode | None:
    """Devuelve None si no hay jefes que componer — no revienta."""
```

> **AUD-455 — GAP-055 resuelto.** Ninguna de las 28 escenas listadas en
> `KNOWN_GAPS.md` tenía sección en este documento. Verificado contra los 28
> ficheros de `src/engine/scenes/`.

---

## 18. API de los scripts

### 18.1 `scripts/validate_assets.py`

```python
# Valida la carga de fuentes, la carga de modelos, la integridad de los ficheros
# de mapa y la paleta de sprites.
# Código de salida 0 si tiene éxito, distinto de cero si falla.
# Sin clases públicas — se ejecuta como `python scripts/validate_assets.py`.

# Definiciones de paleta a nivel de módulo (patrón glob → conjunto RGB permitido):
SPRITE_PALETTES: list[tuple[str, set[tuple[int, int, int]]]]

def check_palette(path: Path) -> None:
    """Verifica que todos los píxeles de un sprite usan sólo colores de la paleta permitida.
    Se salta los píxeles totalmente transparentes (0,0,0) en superficies SRCALPHA."""
```

### 18.2 `scripts/generate_exam.py`

```python
# Genera exámenes de práctica a partir de un banco de 16 preguntas (Unidades II–IX).
# Flags de CLI:
#   --unit UNIT        Filtra por unidad académica (p. ej., "VII", "IX")
#   --num-questions N  Número de preguntas a incluir (por defecto: 10)
# Se ejecuta como `python scripts/generate_exam.py`.
```

---

## 19. Boss Framework — subclase de referencia (API completa en §10.5)

La API de `BossBase` (fases, transiciones, kit de encuentro) vive en §10.5
(`src/framework/entities/boss_base.py`). Este bloque sólo documenta el ejemplo
de subclase que los estudiantes copian — AUD-307: antes duplicaba media API
aquí, y la copia envejeció.

<!-- cita-historica -->
La documentación antigua citaba `_begin_phase_transition`, un nombre que no
existe en el código: el protocolo real son `_start_phase_transition` /
`_finish_phase_transition` (AUD-053).
<!-- /cita-historica -->

### 19.1 `src/stages/boss_venado/boss_venado.py` — El Venado Sagrado

```python
class BossVenado(BossBase):
    #: AUD-238/AUD-263 — el primer jefe concede el dash y, desde AUD-263,
    #: también el parry: sin al menos un jefe que suelte cada habilidad
    #: condicionable, encender PLAYER_SKILLS_REQUIRE_UNLOCK las deja
    #: inalcanzables para siempre. Copiar esta línea es lo mínimo para que un
    #: jefe de estudiante también reparta progresión.
    skill_drop = ["skill_dash", "skill_parry"]

    def __init__(self, spawn_position: pygame.Vector2) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=12.0,
            damage_on_contact=0.75,
        )
        self.set_boss_name("VENADO SAGRADO")
        # ... carga de sprites, temporizadores de ataque, puntos débiles ...
        self.set_phases()

    def set_phases(self, phases: list[BossPhase] | None = None) -> None:
        """Override, no una llamada directa a `super().set_phases([...])` en
        `__init__`: permite que una prueba inyecte fases propias pasando
        `phases`, y que el flujo normal (sin argumento) reconstruya las de
        fábrica."""
        if phases is not None:
            super().set_phases(phases)
            return
        super().set_phases([
            BossPhase(
                phase_index=0, health_threshold=12.0,
                attack_patterns=["STOMP", "CHARGE", "VINE_TOSS"],
                movement_type="sine", speed_multiplier=1.0,
            ),
            # AUD-257 — `escala` existía en BossPhase desde F5.7 y ningún jefe
            # lo usaba (GAP-032); éste es el jefe de referencia, así que el
            # patrón tiene que estar aquí para que se pueda copiar.
            BossPhase(
                phase_index=1, health_threshold=6.0,
                attack_patterns=["VINE_SWEEP", "MUSHROOM_SPORE", "CHARGE"],
                movement_type="bezier", speed_multiplier=1.5,
                escala=1.25,
            ),
        ])
```

<!-- cita-historica -->
> **AUD-307.** `BossBase` no redefinió nunca `update` (lo hereda de
> `EnemyBase`); el chequeo de transición de fase ocurre dentro de
> `_pre_update` → `_check_phase_transition`, y la transición en sí la llevan
> `_start_phase_transition` / `_finish_phase_transition` (la documentación
> antigua decía `_begin_phase_transition`).
<!-- /cita-historica -->
> **AUD-455.** El ejemplo inventaba valores que el jefe de referencia no
> tiene: `health_threshold=6.0`/`0.0` (real: `12.0`/`6.0`) y
> `filter_effect="sobel"`/`sprite_override=...` en las dos fases (real: ningún
> campo opcional puesto — `BossPhase` los admite, pero `BossVenado` no los
> usa). También construía las fases en línea dentro de `__init__` y llamaba a
> `self.set_phases(phases)`; el real declara `set_phases` como método propio
> (override, admite `phases=None` para reconstruir las de fábrica o una lista
> para pruebas) y `__init__` lo llama sin argumentos. Faltaba el atributo de
> clase `skill_drop = ["skill_dash", "skill_parry"]` (AUD-238/AUD-263) y la
> fase 1 real declara `escala=1.25`, no `sprite_override`. Verificado contra
> `src/stages/boss_venado/boss_venado.py`.

---

## 20. Framework — física, combate, IA y mundo (GAP-056, resuelto)

### 20.1 `src/framework/physics/capas.py`

```python
from enum import IntFlag

class Capa(IntFlag):
    """Clases de sólido, combinables con `|` (bitmask, AUD-395)."""
    NADA = 0
    SOLIDO = 1        # pared/suelo/techo — frena a todos por defecto
    PLATAFORMA = 2    # atravesable desde abajo (Platform del TMX)
    DESTRUCTIBLE = 4  # muro que cede a golpes (bloques.py)
    PUERTA = 8        # sólida cerrada, aire abierta
    TODO = SOLIDO | PLATAFORMA | DESTRUCTIBLE | PUERTA

#: Lo que frena a una entidad que no declara `mascara_de_colision`.
MASCARA_POR_DEFECTO: Capa = Capa.SOLIDO | Capa.PLATAFORMA

class MapaDeCapas:
    """Rectángulos del escenario, indexados por clase de sólido."""

    def poner(self, capa: Capa, rects: list[pygame.Rect]) -> None:
        """Declara los rectángulos de una capa; reemplaza los anteriores."""
    def de(self, capa: Capa) -> list[pygame.Rect]:
        """Los rectángulos de una capa concreta."""
    def solidos_para(self, mascara: Capa = MASCARA_POR_DEFECTO) -> list[pygame.Rect]:
        """Los rectángulos que frenan a quien lleve esa máscara. Copia nueva,
        no vista — el resolutor la recorre varias veces por fotograma."""

    @property
    def capas_declaradas(self) -> list[Capa]:
        """Qué capas tienen algo, para depuración/pruebas."""
```

No resuelve colisión ni sustituye a `resolucion.py` — sólo responde "¿qué
rectángulos entran en el cálculo?"; el cálculo sigue en `resolucion.py`
(decisión del dueño 2026-08-11: capas propias sobre el resolutor AABB, no
reintroducir pymunk).

### 20.2 `src/framework/physics/perfil.py`

```python
PLATAFORMAS: str = "plataformas"   # el juego actual
CENITAL: str = "cenital"           # AUD-328 — sin gravedad, dos ejes
VUELO: str = "vuelo"               # AUD-335 — sin gravedad, velocidad libre

@dataclass(frozen=True)
class Material:
    """Superficie con nombre — AUD-396, cierra GAP-039."""
    nombre: str = "roca"
    friccion: float = 1.0      # multiplicador de la fricción del perfil
    restitucion: float = 0.0   # fracción de velocidad de impacto devuelta al chocar

ROCA: Material    # friccion=1.0, restitucion=0.0 — comportamiento de siempre
HIELO: Material   # friccion=0.15
MUSGO: Material   # friccion=2.5
GOMA: Material    # restitucion=0.6
MATERIALES: dict[str, Material]   # los cuatro, por nombre

@dataclass
class Muro:
    """Deslizamiento por pared en el aire."""
    factor_gravedad: float = 0.3
    factor_max_caida: float = 0.5

@dataclass
class Cuestas:
    margen_pegado: float = 8.0
    velocidad_deslizamiento: float = 90.0

@dataclass
class PhysicsProfile:
    """Toda la física de un contexto de juego, en un solo objeto (AUD-333).
    Los valores por defecto salen de `settings` en el momento de construir."""
    modo: str = PLATAFORMAS
    gravedad: float; max_caida: float; velocidad_suelo: float
    salto_impulso: float; coyote_frames: int; saltos_aereos: int
    muro: Muro; cuestas: Cuestas
    aceleracion: float = 0.0   # px/s² — 0 = velocidad instantánea del estado (AUD-336)
    friccion: float = 0.0      # px/s² — frenado sin entrada
    material: Material         # ROCA por defecto (AUD-396)

    @classmethod
    def plataformas(cls) -> PhysicsProfile: ...
    @classmethod
    def cenital(cls) -> PhysicsProfile:
        """Sin gravedad/caída/salto — el mismo contenido que la vieja bandera `vista_cenital`."""
    @classmethod
    def vuelo(cls) -> PhysicsProfile:
        """Misma integración que cenital; un contexto de vuelo fija su propia velocidad."""
```

### 20.3 `src/framework/physics/resolucion.py`

El resolutor de mundo compartido (AUD-334) — la colisión del jugador vivía
como métodos privados suyos; esto la expone como pasos puros para que
entidades y modos nuevos la usen sin heredar de `Player`.

```python
@dataclass
class EstadoDeMovimiento:
    """Lo que el resolutor necesita saber de la entidad este fotograma. Lo muta."""
    posicion: pygame.Vector2
    velocidad: pygame.Vector2
    ancho: float
    alto: float
    en_el_suelo: bool = False
    prev_foot_y: float = 0.0
    venia_del_suelo: bool = False
    restitucion: float = 0.0   # AUD-396 — de perfil.material.restitucion

@dataclass
class Contacto:
    """Los hechos del fotograma — sin reglas, la entidad decide qué hacer con ellos."""
    posicion: pygame.Vector2
    velocidad: pygame.Vector2
    en_el_suelo: bool = False
    aterrizo: bool = False
    aterrizo_en: str = ""   # "" | "suelo" | "cuesta" | "repisa"
    aterrizo_desde_el_aire: bool = False
    topo: bool = False
    lado_de_pared: int = 0
    pared_en_el_aire: bool = False
    repisa_libre: bool = False
    venia_del_suelo: bool = False

def resolver_eje_x(estado: EstadoDeMovimiento, dt: float,
                   solidos: list[pygame.Rect]) -> Contacto:
    """Integra y resuelve el eje X. Contrato: integrar siempre, resolver sólo
    si hay contra qué (AUD-130 — un escenario sin colisión no debe congelar
    la posición mientras la velocidad crece)."""

def resolver_paredes_de_pendientes(
    estado: EstadoDeMovimiento, pendientes: list["Pendiente"],
    margen: float = MARGEN_DE_PEGADO) -> None:
    """Frena la entrada lateral a una rampa (AUD-323)."""

def resolver_eje_y(estado: EstadoDeMovimiento, dt: float,
                   solidos: list[pygame.Rect]) -> Contacto:
    """Integra y resuelve el eje Y. Aplica la restitución del material
    (AUD-396) con un umbral de corte para que un bote no oscile para siempre."""

def resolver_cuestas(estado: EstadoDeMovimiento, dt: float,
                     pendientes: list["Pendiente"], cuestas: Cuestas) -> Contacto:
    """Coloca los pies sobre la cuesta pisada (AUD-297); proyecta la caída
    (AUD-324) y desliza sin entrada (AUD-326)."""

def resolver_repisas(estado: EstadoDeMovimiento,
                     repisas: list[pygame.Rect]) -> Contacto:
    """Plataformas de un solo sentido. Sólo atrapa cayendo y si los pies
    estaban a la altura del borde el fotograma anterior."""

def resolver_movimiento(
    estado: EstadoDeMovimiento, dt: float, solidos: list[pygame.Rect],
    repisas: list[pygame.Rect] | None = None,
    pendientes: list["Pendiente"] | None = None,
    perfil: PhysicsProfile | None = None,
) -> Contacto:
    """La resolución entera, orden auditado: X → paredes de cuestas → Y →
    cuestas → repisas. Sin perfil o con `modo=plataformas`: los cinco pasos.
    Con otro modo: sólo X e Y (cuestas/repisas son semántica de plataformas).
    Puerta de entrada para entidades/modos nuevos. AUD-344: dt/posición/
    velocidad no finitos se sanean en vez de propagar un `int(NaN)` que
    reventaría el fotograma."""

def acercarse_a(actual: float, objetivo: float, max_delta: float) -> float:
    """`move_toward`/`approach` — el paso del integrador por perfil (AUD-336)."""
```

### 20.4 `src/framework/combate/dano.py`

Canales de daño (AUD-387, cierra GAP-043) — catálogo en
`data/damage_types.json`, resistencias declaradas en Tiled
(`resistencias="veneno:0.5, fuego:2"`).

```python
CANALES: dict[str, dict[str, Any]]   # el catálogo, por id — leído una vez al importar
CANAL_POR_DEFECTO: str               # el que reciben los ~32 llamantes que no dicen nada

def canal_valido(nombre: object) -> bool: ...
def normalizar(nombre: object) -> str:
    """El canal pedido, o `CANAL_POR_DEFECTO` si no existe (con aviso)."""
def mitigar(cantidad: float, canal: object,
           resistencias: dict[str, float] | None) -> float:
    """Multiplicador, no resta: 0.5 = resistencia, 2.0 = debilidad, 0.0 =
    inmunidad. Recortado a cero por abajo (un factor negativo no debe curar)."""
```

### 20.5 `src/framework/combate/efectos.py`

Efectos temporales (AUD-388, cierra GAP-044) — catálogo en `data/effects.json`.
No conoce entidades ni el ECS: recibe un componente `Efectos` (§11 de
`23_DATA_SCHEMAS.md`) y devuelve números; quien aplica el daño por fotograma
es `sistema_efectos` en `ecs/systems.py`.

```python
MODIFICABLES: frozenset[str]   # {"dano_infligido", "dano_recibido", "velocidad", "por_segundo"}
CATALOGO: dict[str, dict[str, Any]]

@dataclass(slots=True)
class EfectoActivo:
    id: str
    restante: float

def existe(nombre: object) -> bool: ...
def aplicar(componente: Any, nombre: str, duracion: float | None = None) -> None:
    """Pone un efecto o refresca el que ya estuviera — reaplicar REFRESCA, no
    acumula (dos charcas de veneno no envenenan el doble)."""
def modificador(componente: Any, que: str) -> float:
    """Multiplicador acumulado de todos los efectos activos sobre `que`. 1.0
    si no hay ninguno — el llamante multiplica siempre, sin rama condicional."""
def dano_por_segundo(componente: Any) -> float: ...
```

### 20.6 `src/framework/ai/navegacion.py`

A* sobre la rejilla de tiles (AUD-389, cierra GAP-045; Unidad VI). Da
rodeo a `sistema_acosador` en vez de la línea recta que lo empotraba en
paredes. No se re-planifica cada fotograma: cadencia 4 Hz, escalonada por
navegante para no pensar treinta a la vez.

```python
CADENCIA: float = 0.25          # segundos entre replanificaciones
TOPE_DE_NODOS: int = 1_500      # nodos que A* expande antes de rendirse

@dataclass(slots=True)
class MallaDeNavegacion:
    """Qué celdas se pueden pisar. Se construye una vez por escenario."""
    ancho: int; alto: int; tile: int
    bloqueadas: set

    @classmethod
    def desde_rects(cls, solidos, ancho_px: int, alto_px: int,
                    tile: int = 16) -> MallaDeNavegacion:
        """Marca intransitable toda celda tocada, aunque sea a medias."""
    def transitable(self, cx: int, cy: int) -> bool: ...
    def celda_de(self, punto: pygame.Vector2) -> tuple[int, int]: ...
    def centro_de(self, celda: tuple[int, int]) -> pygame.Vector2: ...

def a_estrella(malla: MallaDeNavegacion, inicio: tuple[int, int],
              meta: tuple[int, int], tope: int = TOPE_DE_NODOS) -> list:
    """Ruta de inicio a meta sin incluir el origen. Lista vacía si no hay
    camino, si ya está en la meta, si la meta está en un muro o si se agota
    el tope — los cuatro casos se ven iguales a propósito. Heurística
    Manhattan (admisible sin diagonales)."""
```

> **Medido:** con el mapa más grande del repositorio (60×240 celdas) y
> `TOPE_DE_NODOS=1500`, ~3,6 ms por consulta con un 96% de rutas halladas;
> el envolvente utilizable son unos pocos navegantes simultáneos (30
> navegantes ≈ 43% del presupuesto de fotograma).

### 20.7 `src/framework/ai/lua_script.py`

> **NOT WIRED (AUD-022).** Completo y probado de forma aislada, pero **nada
> del juego lo construye ni lo llama** — sin entrada de menú, sin escena, sin
> gancho. Se conserva como base y material docente; no describir esta
> característica como entregada en ningún otro documento hasta que exista un
> punto de entrada real. Rastreado como R-11.

```python
class LuaScriptEnemy:
    """Envuelve un script Lua de IA para una instancia de enemigo, vía `lupa`."""

    def __init__(self, script_source: str, name: str = "") -> None: ...
    def call_patrol(self, enemy: "EnemyBase", player: "Player", dt: float) -> tuple[float, float]:
        """Llama a `patrol(ctx) -> dx, dy` si existe; (0,0) si no."""
    def call_alert(self, enemy: "EnemyBase", player: "Player", dt: float) -> str:
        """Llama a `alert(ctx) -> action`; "approach" si no hay función o falla."""
    def call_on_hit(self, enemy: "EnemyBase", player: "Player", dt: float) -> None: ...
    def call_on_death(self, enemy: "EnemyBase", player: "Player", dt: float) -> None: ...

def load_script(name: str) -> LuaScriptEnemy | None: ...
def register_script(name: str, source: str) -> LuaScriptEnemy: ...
```

### 20.8 `src/framework/world/environment.py`

`EnvironmentState` — la foto inmutable del ambiente del mundo en un
fotograma (AUD-358). La produce `WorldSimulation` (§20.9); render/audio/
jugabilidad la leen en vez de hablarse entre sí.

```python
@dataclass(frozen=True, slots=True)
class EnvironmentState:
    hora: float = 12.0                      # 0-24
    dia: int = 0
    estacion: str = "summer"
    factor_ambiente: float = 1.0            # multiplicador de ambient_light, 0-1
    color_ambiente: tuple[int, int, int] = (255, 255, 255)
    bloom_extra: float = 0.0
    clima: str = "clear"
    precipitacion: float = 0.0              # 0-1
    humedad: float = 0.0                    # 0-1 — lo que consulta la física, no `clima`
    viento: float = 0.0                     # px/s, con signo
    visibilidad: float = 1.0                # 1 nítido, 0 nada
    cobertura_nubes: float = 0.0
    altura_solar: float = 1.0               # -1 medianoche, 1 mediodía, 0 horizonte
    azimut_solar: float = 0.0               # -1 este, 1 oeste (AUD-399)
    fase_lunar: float = 0.0                 # 0/1 nueva, 0.5 llena
    fase_del_dia: str = "dia"               # de FASES_DEL_DIA (con los 2 crepúsculos)

    @property
    def es_de_noche(self) -> bool: ...
    @property
    def intensidad_sonora(self) -> float:
        """0-1, nunca cero (AUD-402) — lluvia pesa 65%, viento 35%."""
    @property
    def matriz_de_color(self) -> tuple[float, ...]:
        """Matriz 3×3 aplanada para `colorMatrix` del sombreador (AUD-401):
        tiñe con `color_ambiente`, desatura hacia gris con `visibilidad`."""
    @property
    def direccion_de_sombra(self) -> tuple[float, float]:
        """(dx, largo) — AUD-399. (0, 0) de noche; largo acotado a 4x."""
    @property
    def luz_lunar(self) -> float:
        """0 de día; de noche, fracción del disco visible."""
    @property
    def suelo_mojado(self) -> bool:
        """`humedad >= UMBRAL_SUELO_MOJADO` (0.55) — el único umbral, para
        física, audio y render."""
    @property
    def factor_friccion(self) -> float:
        """0.6-1.0 — el campo que hace que la lluvia sea jugabilidad y no
        decoración."""
    @property
    def frenado_del_suelo(self) -> float:
        """px/s² para `PhysicsProfile.friccion`. 0 en seco = instantáneo (los
        16 escenarios actuales); finito en mojado = derrape."""

    @classmethod
    def neutro(cls) -> EnvironmentState:
        """Mediodía de verano despejado — todos los derivados son la
        identidad. Lo que devuelve una escena sin `WorldSimulation`."""
```

### 20.9 `src/framework/world/simulation.py`

```python
CLIMAS: dict[str, dict[str, float]]  # humedad/viento/nubes/precipitación/visibilidad por clima

def viento_de(clima: str, rng: random.Random) -> float:
    """Viento con signo, px/s (AUD-374 — antes duplicado con `WeatherSystem`)."""

class WorldSimulation:
    """La autoridad del ambiente: un escenario la configura, ella calcula.
    El mapa declara `start_hour`/`season`/`climate`; el resto lo deriva."""

    SEGUNDOS_DE_TRANSICION: float = 6.0   # AUD-424 — cuánto tarda un cambio de clima

    def __init__(
        self, hora_inicial: float = 12.0, duracion_dia: float = 0.0,
        estacion: str = POR_DEFECTO, clima: str = "clear", dia_inicial: int = 0,
        desfase_lunar: float = 0.0, rng: random.Random | None = None,
    ) -> None:
        """`POR_DEFECTO` es de `framework.stage.seasons`, no un literal."""

    @property
    def reloj(self) -> "RelojDeMundo": ...
    @property
    def dia(self) -> int: ...
    @property
    def clima(self) -> str: ...

    def set_clima(self, nombre: str, inmediato: bool = False) -> None:
        """El nombre cambia ya; los valores (humedad/viento/...) se
        interpolan salvo `inmediato=True` (carga de nivel, cutscene, pruebas)."""
    def set_estacion(self, nombre: str) -> None: ...
    def forzar(self, **campos: object) -> None:
        """Sustituye campos del `EnvironmentState` calculado sin tocar la
        simulación — la válvula de diseño que el realismo no da.
        `forzar(fase_lunar=None)` suelta la sustitución."""
    def update(self, dt: float) -> None:
        """Lo caro (astronomía) sólo se recalcula al cambiar el día."""
    def estado(self) -> EnvironmentState:
        """La foto del fotograma — lo único que necesitan los consumidores."""
```

### 20.10 `src/framework/academic/curriculum.py`

El temario en datos (AUD-095): orden de las unidades, su teoría y sus
preguntas. Es dato, no lógica — el progreso vive en `progress.py` (§20.11).
**No es una copia del programa oficial** de `08_SYLLABUS_MAPPING.md` (9
unidades I–IX): son 10 módulos más granulares para el sistema de
aprendizaje del juego, algunos a caballo entre dos unidades del programa (p.
ej. `interpolacion` es "III/IV", `ruido` es "V/VIII") — no es una
contradicción, son dos vistas del mismo temario a distinto grano.

```python
@dataclass(frozen=True)
class BloqueTeorico:
    titulo: str
    formula: str
    explicacion: str
    codigo: str   # ruta al fichero del motor que implementa la fórmula

@dataclass(frozen=True)
class Pregunta:
    enunciado: str
    opciones: tuple[str, ...]
    correcta: int    # índice en opciones; ValueError en __post_init__ si está fuera de rango
    porque: str      # se muestra tras contestar, acierte o falle

@dataclass(frozen=True)
class Unidad:
    id: str                                    # estable — se guarda en el progreso
    numero: str                                 # numeración del programa, p.ej. "II/III"
    titulo: str
    resumen: str
    escena: str                                 # clave con la que scene_registry construye la demo
    teoria: tuple[BloqueTeorico, ...] = ()
    preguntas: tuple[Pregunta, ...] = ()

#: Las 10 unidades, en el orden del temario = la cadena de desbloqueo.
PLAN: tuple[Unidad, ...]
# ids: vectores, transformaciones, curvas, interpolacion, color, ruido,
#      colisiones, imagen, vision, patrones — 5 preguntas cada una.

def ids_de_unidades() -> tuple[str, ...]: ...
def unidad(id_unidad: str) -> Unidad | None: ...
def unidad_de_escena(clave_escena: str) -> Unidad | None:
    """None para las escenas fuera del temario (sandbox, pipeline builder,
    tablas de récords) — por eso están siempre disponibles."""
def siguiente_unidad(id_unidad: str) -> Unidad | None: ...
```

### 20.11 `src/framework/academic/progress.py`

Progreso académico de un estudiante — qué ha aprobado y qué puede abrir
(AUD-095). Un JSON por estudiante, no pickle: los ficheros los intercambian
30 personas y abrir un `.pkl` ajeno ejecuta código arbitrario.

```python
PREGUNTAS_POR_UNIDAD: int = 5
ACIERTOS_PARA_APROBAR: int = 4   # 80% — 3/5 al azar cuela un 10.4% de las veces
VERSION: int = 1
APODO_MAX: int = 16

def es_correo_valido(correo: str) -> bool: ...
def nombre_de_fichero(correo: str) -> str:
    """Transliterado a ASCII y saneado — no se puede salir del directorio."""

@dataclass(frozen=True)
class ResultadoIntento:
    unidad_id: str
    aciertos: int
    total: int
    aprobado: bool
    recien_aprobada: bool          # True si este intento aprobó por primera vez
    desbloqueada: str | None       # la unidad que se acaba de abrir, si la hay

class ProgresoAcademico:
    """Las notas de un estudiante y qué puede abrir con ellas. Identificado
    por correo (normalizado); se guarda el MEJOR intento, no el último."""

    def __init__(self, correo: str = "", apodo: str = "") -> None: ...

    def aciertos(self, id_unidad: str) -> int: ...
    def intentos(self, id_unidad: str) -> int: ...
    def esta_aprobada(self, id_unidad: str) -> bool: ...
    def esta_desbloqueada(self, id_unidad: str) -> bool:
        """La primera unidad siempre; el resto si la anterior está aprobada.
        Lo que no está en el temario nunca se bloquea."""
    def unidades_desbloqueadas(self) -> tuple[str, ...]: ...
    def unidades_aprobadas(self) -> tuple[str, ...]: ...
    def porcentaje(self) -> float: ...
    def unidad_actual(self) -> str | None:
        """La primera unidad sin aprobar."""

    def registrar_intento(self, id_unidad: str, aciertos: int,
                          total: int = PREGUNTAS_POR_UNIDAD) -> ResultadoIntento: ...

    def a_dict(self) -> dict[str, Any]: ...
    @classmethod
    def desde_dict(cls, datos: dict[str, Any]) -> ProgresoAcademico: ...
    def guardar(self, directorio: Path) -> Path:
        """Escribe a un `.tmp` y renombra — nunca deja un fichero truncado."""
    @classmethod
    def cargar(cls, directorio: Path, correo: str) -> ProgresoAcademico:
        """Fichero ilegible o ausente → progreso vacío, sin excepción."""
```

### 20.12 `src/framework/academic/sesion.py`

```python
DIRECTORIO_PROGRESO: Path   # user_data_dir() / "saves" / "academico"

class SesionAcademica:
    """Estudiante activo y su progreso — singleton por proceso, como `Bestiary`."""

    def __init__(self, directorio: Path | None = None) -> None:
        """Normalmente no se llama directamente — usar `instancia()`."""

    @classmethod
    def instancia(cls) -> SesionAcademica: ...
    @classmethod
    def reiniciar(cls, directorio: Path | None = None) -> SesionAcademica:
        """Descarta la sesión y empieza otra. Uso: pruebas."""

    @property
    def progreso(self) -> ProgresoAcademico: ...
    @property
    def correo(self) -> str: ...
    @property
    def apodo(self) -> str:
        """Cae al correo sin dominio, y a "Estudiante" si tampoco hay correo
        — nunca cadena vacía."""
    @property
    def identificado(self) -> bool: ...
    @property
    def directorio(self) -> Path: ...

    def poner_apodo(self, apodo: str) -> None:
        """No hace nada si no está identificado — sin correo no hay dónde
        persistirlo."""
    def entrar(self, correo: str, *, recordar: bool = True) -> bool:
        """False si el correo no tiene forma válida; no toca la sesión en
        ese caso."""
    def reanudar(self) -> bool:
        """Reentra con el último correo recordado en `user_settings`, si lo hay."""
    def salir(self) -> None:
        """Vuelve a anónimo. No borra nada del disco."""
    def guardar(self) -> Path | None:
        """None si nadie se ha identificado."""
    def registrar_examen(self, id_unidad: str, aciertos: int) -> ResultadoIntento:
        """Anota y guarda en el acto — en un aula el cierre limpio es la excepción."""
```

> Los logros siguen a la sesión académica, no al proceso (AUD-200): un
> estudiante identificado escribe en `achievements_<correo>.json`; anónimo,
> en la ruta histórica compartida. `achievements.py` (§2, `engine/core/`) no
> conoce `framework/` — la sesión se inyecta vía `bind_ruta_resolver`.

> **AUD-455 — GAP-056 resuelto.** `src/framework/physics/`, `combate/`,
> `ai/`, `world/` y `academic/` (12 ficheros) no tenían ninguna sección de
> API. Verificado contra los 12 ficheros fuente. El resto de
> `src/framework/vfx/` se documenta en §20.13–20.25 (GAP-057).

### 20.13 `src/framework/vfx/particle_system.py`

```python
def warmup() -> float:
    """Compila el núcleo JIT de numba (si está instalado) antes de que haga
    falta — llamar desde la pantalla de carga (AUD-082: sin esto, la primera
    partícula del juego cuesta un fotograma de ~376 ms). Idempotente."""

class BurstConfig:
    def __init__(self, count: int, speed: float, lifetime: float,
                size: tuple[int, int], color: tuple[int, int, int],
                spread: float = 360.0, gravity: float = 0.0,
                friction: float = 1.0) -> None: ...

class ParticleEmitter:
    """Partículas en arreglos NumPy paralelos (SoA) con capacidad reservada
    que dobla al crecer (AUD-275) — no reasigna arrays por fotograma."""

    CAPACIDAD_INICIAL: int = 256

    def __init__(self, capacidad: int = CAPACIDAD_INICIAL, rng: Any = None) -> None: ...
    def emit(self, x: float, y: float, config: BurstConfig) -> None: ...
    def emit_directed(
        self, x: float, y: float, angle: float, speed: float, count: int,
        lifetime: float, size: tuple[int, int], color: tuple[int, int, int],
        spread: float = 30.0, gravity: float = 0.0, friction: float = 1.0,
    ) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None: ...
    def clear(self) -> None:
        """Vacía sin soltar los arreglos reservados (AUD-275)."""

    @property
    def count(self) -> int: ...
    @property
    def capacidad(self) -> int: ...

class ParticleSystem:
    """Registro de `ParticleEmitter` con nombre."""
    def get_emitter(self, name: str = "_default") -> ParticleEmitter:
        """Crea el emisor si no existe."""
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None: ...
    def clear(self) -> None: ...
```

### 20.14 `src/framework/vfx/lighting.py`

```python
class LightSource:
    """Foco de luz 2D. `_gradient_cache` es de clase — compartida por todos
    los focos, con tope `_MAX_CACHED_GRADIENTS = 128` — y cuantiza radio (4px)
    e intensidad (0.05) para no crecer sin límite con el parpadeo."""

    def __init__(
        self, position: pygame.Vector2, radius: float = 80.0,
        color: tuple[int, int, int] = (255, 255, 200), intensity: float = 0.8,
        flicker: bool = False, flicker_speed: float = 4.0,
        flicker_amount: float = 0.15,
    ) -> None: ...
    def update(self, dt: float) -> None: ...
    def get_current_radius(self) -> float: ...
    def get_current_intensity(self) -> float: ...
    def build_gradient(self, radius: float, color: tuple[int, int, int],
                       intensity: float | None = None) -> pygame.Surface: ...
    def get_cached_gradient(self) -> pygame.Surface:
        """Reconstruye sólo si radio/intensidad/color cambiaron lo suficiente."""

class LightSystem:
    def __init__(self, ambient_brightness: float = 0.3) -> None: ...
    def set_sombra_solar(self, direccion_y_largo: tuple[float, float]) -> None:
        """De `EnvironmentState.direccion_de_sombra` (AUD-403) — sombras direccionales del sol."""
    def set_obstaculos(self, rects: list[pygame.Rect] | None) -> None:
        """Geometría que tapa la luz (AUD-278). None/vacío la apaga."""
    def add_light(self, light: LightSource) -> None: ...
    def remove_light(self, light: LightSource) -> None: ...
    def clear(self) -> None: ...
    def update(self, dt: float, camera_offset: pygame.Vector2) -> None: ...
    def render(self, target: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """`render_map` + `blit` con `BLEND_RGB_MULT` — ruta CPU."""
    def render_map(self, size: tuple[int, int],
                   camera_offset: pygame.Vector2) -> pygame.Surface:
        """Compone el multiplicador sin aplicarlo — ruta GPU (AUD-343): el
        sombreador lo multiplica; llamar a las dos rutas a la vez duplica la luz."""
    def mapa_de_luz(self) -> pygame.Surface | None:
        """El último mapa compuesto, o None antes del primer `render_map`."""
    def get_player_light(self, player_pos: pygame.Vector2, is_combat: bool) -> LightSource: ...

    ambient_brightness: float
    ambient_color: tuple[int, int, int]
    sombra_solar: tuple[float, float]
```

### 20.15 `src/framework/vfx/sombras_proyectadas.py`

Proyección de silueta desde un foco (Unidad II — vectores) y sombras
direccionales del sol (AUD-403). Apagado por defecto (`sombras_proyectadas`
en el TMX) — envolvente medido: 4-5 focos, más de 8 come el fotograma.

```python
MAX_SOMBRAS_POR_FOCO: int = 24   # recorta las más lejanas si hay más obstáculos

def silueta_de(foco: pygame.Vector2, rect: pygame.Rect) -> tuple[pygame.Vector2, pygame.Vector2] | None:
    """Las dos esquinas extremas del rectángulo vistas desde `foco`. None si
    el foco está dentro (no hay "detrás")."""

def sombra_direccional(rect: pygame.Rect, direccion: float, largo: float) -> tuple[pygame.Vector2, ...]:
    """Cuadrilátero de sombra con luz paralela (el sol) — AUD-403. `direccion`
    y `largo` vienen de `EnvironmentState.direccion_de_sombra`. Vacío de noche."""

class ProyectorDeSombras:
    """Indexa los obstáculos en una `RejillaEspacial` la primera vez que los ve."""
    def proyectar(self, mascara: pygame.Surface, foco: pygame.Vector2,
                  alcance: float, obstaculos: list[pygame.Rect],
                  camera_offset: pygame.Vector2) -> None:
        """Pinta negro (= "sin luz aquí") sobre la máscara de luz, no sobre la escena."""
```

### 20.16 `src/framework/vfx/cielo.py`

```python
class CieloProcedural:
    """Degradado cénit→horizonte derivado de `EnvironmentState` (AUD-426) —
    reemplaza los 3 PNG fijos por zona, que no podían mostrar el crepúsculo.
    Cachea por (tamaño, altura_solar redondeada a 0.01, nubes redondeadas a
    0.01) — sin el redondeo se recalcularía 60 veces por segundo."""

    def superficie(self, tamano: tuple[int, int], estado: Any) -> pygame.Surface:
        """`estado` sólo necesita `.altura_solar`/`.cobertura_nubes` — acepta dobles de prueba."""
    def dibujar(self, destino: pygame.Surface, estado: Any) -> None:
        """Va antes que el parallax."""
```

### 20.17 `src/framework/vfx/contorno.py`

Contorno de silueta de 1px para separar al jugador del decorado (AUD-190,
contraste medido 1.01-1.18 sin él). Ámbar para enemigos, tras la preferencia
`contorno_de_enemigos` (apagada por defecto — no cambia el aspecto de los 16
mapas entregados).

```python
COMPENSACIONES: tuple[tuple[int, int], ...]   # los 4 desplazamientos en cruz
COLOR_JUGADOR: tuple[int, int, int] = (236, 232, 220)
COLOR_ENEMIGO: tuple[int, int, int] = (240, 168, 64)

def silueta_de(frame: pygame.Surface,
              color: tuple[int, int, int] = COLOR_JUGADOR) -> pygame.Surface:
    """El fotograma teñido de un color plano, alfa conservado. Cacheada por (id(frame), color)."""

def dibujar_con_contorno(surface: pygame.Surface, frame: pygame.Surface,
                         destino: tuple[int, int],
                         color: tuple[int, int, int] = COLOR_JUGADOR) -> None: ...
```

### 20.18 `src/framework/vfx/sombras.py`

La sombra elíptica bajo los pies (AUD-273) — único indicador de aterrizaje
en el aire en un plataformas 2D. No conoce colisiones: el suelo se le pasa.

```python
ALTURA_DE_DESVANECIDO: float = 180.0
ALFA_MAXIMO: int = 110
ESCALA_MINIMA: float = 0.45

def suelo_bajo(cuerpo: pygame.Rect, solidos: list[pygame.Rect]) -> int | None:
    """La `y` del sólido más ALTO debajo del cuerpo (no el primero — importa
    con repisas suspendidas)."""

class Sombra:
    """Cachea la elipse por (ancho, alto, alfa) — AUD-302, no redibuja cada fotograma."""
    def medidas(self, cuerpo: pygame.Rect, suelo_y: int) -> tuple[int, int, int]:
        """(ancho, alto, alfa) — separado del dibujado para poder probarse sin píxeles."""
    def dibujar(self, surface: pygame.Surface, cuerpo: pygame.Rect,
               solidos: list[pygame.Rect], camera_offset: pygame.Vector2,
               lote: Any = None) -> None:
        """Con `lote` (un `SpriteBatch`), la encola en vez de dibujar directo."""
```

### 20.19 `src/framework/vfx/damage_numbers.py`

```python
class DamageNumber:
    """Un número de daño que sube y se desvanece. El alfa se aplica sobre una
    COPIA del `SurfacePool` (AUD-158) — la superficie de texto está cacheada
    y compartida, así que escribir el alfa en ella desincronizaba el
    desvanecimiento de golpes simultáneos."""

    _MAX_CACHE: int = 128   # tope del caché de texto renderizado, de clase

    @classmethod
    def clear_caches(cls) -> None: ...
    def __init__(self, x: float, y: float, amount_text: str, is_critical: bool = False) -> None: ...
    @property
    def alive(self) -> bool: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...

class DamageNumberManager:
    def add(self, x: float, y: float, text: str, is_critical: bool = False) -> None: ...
    def clear(self) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...
```

### 20.20 `src/framework/vfx/hit_effects.py`

```python
class HitEffects:
    """Catálogo de `BurstConfig` (§20.13) preconfigurados: SPARK, SPARK_BIG,
    BLOOD, BLOOD_BIG, PARRY, HEAL, DEATH, DASH_TRAIL, BUBBLE, CHARGE_GLOW,
    PICKUP — atributos de clase, no instancias."""

    @staticmethod
    def get_for_damage(damage: float) -> BurstConfig:
        """SPARK_BIG si damage >= 1.0, si no SPARK."""
    @staticmethod
    def get_blood_for_damage(damage: float) -> BurstConfig:
        """BLOOD_BIG si damage >= 1.0, si no BLOOD."""
```

### 20.21 `src/framework/vfx/post_processing.py`

```python
class PostProcessing:
    """Efectos de pantalla completa: viñeta, flash, tinte, bloom, motion
    blur, corrección de color, filtro de daltonismo. Algunos también los hace
    `gl_pipeline.py` por sombreador (AUD-222) — se consulta
    `engine.core.gpu_effects.effects_on_gpu()` para no aplicar ambos."""

    def set_motion_blur(self, strength: float = 0.3) -> None: ...
    def clear_motion_blur(self) -> None: ...
    def set_color_grading(self, r: int, g: int, b: int, rr: int, gg: int, bb: int,
                          rrr: int, ggg: int, bbb: int) -> None:
        """Matriz de color 3x3, un entero (0-255-ish) por celda."""
    def clear_color_grading(self) -> None: ...
    def set_bloom(self, intensity: float, duration: float = 0.3) -> None:
        """Ráfaga con decaimiento — distinta de `set_base_bloom`."""
    def flash(self, color: tuple[int, int, int], alpha: float = 200, duration: float = 0.1) -> None: ...
    def set_damage_vignette(self, strength: float) -> None: ...
    def set_tint(self, color: tuple[int, int, int], alpha: float) -> None: ...
    def clear_tint(self) -> None: ...
    def set_base_bloom(self, intensity: float) -> None:
        """Bloom permanente del escenario, sin decaimiento — se usa el mayor
        entre éste y el de `set_bloom`."""
    def set_vignette(self, strength: float) -> None:
        """Viñeta base del escenario, 0 a 0.6."""
    def update(self, dt: float) -> None: ...
    def apply(self, surface: pygame.Surface) -> None:
        """Aplica todos los efectos activos, en orden fijo — el filtro de
        daltonismo siempre va último, encima de todo."""
```

> El filtro de daltonismo (`_apply_colorblind_filter`) es privado, pero vale
> la pena anotar su optimización: hace la diagonal por canal en C vía
> `BLEND_RGB_MULT` y sólo el término cruzado en NumPy — 17.4 ms → 3.1 ms
> (AUD-138). Es la referencia de por qué esto no es una función de framework
> arbitraria: activar accesibilidad no puede costar la mitad del framerate.

### 20.22 `src/framework/vfx/pulso.py`

El pulso visual al compás de la música (AUD-425/AUD-414) — cámara, luz.
Decae, no oscila; el primer tiempo del compás pesa el doble.

```python
AMPLITUD_CAMARA_PX: float = 1.5
AMPLITUD_LUZ: float = 0.06

def intensidad(reloj: Any | None) -> float:
    """0 a 1. 0 sin reloj musical (mapa sin `bpm`) — no hay bandera que apagar."""
def offset_de_camara(reloj: Any | None) -> float:
    """Píxeles que baja la cámara este fotograma — el golpe se lee como impacto contra el suelo."""
def factor_de_luz(reloj: Any | None) -> float:
    """Multiplicador del brillo ambiental, 1.0 sin latido."""
```

### 20.23 `src/framework/vfx/trail_system.py`

```python
class TrailSystem:
    """Imágenes residuales tras una entidad rápida (dash, embestida de jefe)."""

    MAX_POINTS: int = 24

    def capture(self, player: "Player") -> None:
        """Residuo del jugador — azul intenso en dash, pálido en el aire.
        Respeta el intervalo de captura (F1.4: antes capturaba cada
        fotograma y se veía como un borrón sólido, no una estela)."""
    def capture_at(self, x: float, y: float, size: tuple[int, int],
                   color: tuple[int, int, int, int]) -> None:
        """Residuo para cualquier entidad, no sólo el jugador — jefes en su embestida."""
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None: ...
    def clear(self) -> None: ...
```

### 20.24 `src/framework/vfx/ambient_particles.py`

```python
class AmbientParticleSystem:
    """Partículas de ambiente: polvo, hojas, ascuas, esporas, ceniza — el
    tipo y el ritmo se declaran en el TMX (`ambient_fx`/`ambient_fx_rate`)."""

    TIPOS: tuple[str, ...] = ("dust", "leaves", "embers", "spores", "ash")

    def __init__(self, rng: random.Random | None = None) -> None: ...
    def set_effect(self, particle_type: str, rate: float = 10.0) -> None: ...
    @property
    def count(self) -> int: ...
    @property
    def rate(self) -> float: ...
    def update(self, dt: float, camera_offset: pygame.Vector2) -> None: ...
    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None: ...
    def clear(self) -> None: ...
```

### 20.25 `src/framework/vfx/weather_system.py`

```python
class WeatherSystem:
    """Clima de escenario (lluvia, nieve, niebla, tormenta) por propiedad TMX
    `climate`. El viento sale de `world.simulation.viento_de` (AUD-374, antes
    era una segunda tabla que se desincronizaba de la del mundo)."""

    CLIMATE_PARAMS: dict[str, dict]   # partículas/alfa de velo/color por clima: clear/rain/snow/fog/storm
    ESPERA_ENTRE_RAYOS: tuple[float, float] = (4.0, 11.0)
    DURACION_DESTELLO: float = 0.35
    ALFA_DESTELLO: int = 110
    AMBIENTES: dict[str, str | None]   # clave de clima -> ruta relativa a assets/, o None
    SIN_ASSET: frozenset[str] = frozenset()   # climas que deberían sonar y no tienen fichero — vacío desde AUD-271

    def __init__(self, climate: str = "clear", rng: random.Random | None = None) -> None: ...
    def set_climate(self, climate: str) -> None: ...
    def forzar_relampago(self) -> None:
        """Dispara un rayo ahora — cinemáticas y pruebas."""
    @property
    def brillo_del_relampago(self) -> float: ...
    @property
    def relampagos_contados(self) -> int: ...
    @property
    def climate(self) -> str: ...
    def aplicar_viento(self, viento: float) -> None:
        """Toma el viento de `EnvironmentState.viento` (AUD-374) — con signo."""
    def update(self, dt: float, camera_offset: pygame.Vector2) -> None: ...
    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None: ...
    def clear(self) -> None: ...
    def get_ambient_audio_key(self) -> str | None:
        """Ruta del sonido ambiente de este clima, o None."""
    def falta_su_ambiente(self) -> bool:
        """True si el clima debería sonar y no hay fichero — hoy siempre False (AUD-271)."""
```

> **AUD-455 — GAP-057 resuelto.** Los 13 módulos de `src/framework/vfx/` sin
> API previa (`particle_system.py`, `lighting.py`, `sombras_proyectadas.py`,
> `cielo.py`, `contorno.py`, `sombras.py`, `damage_numbers.py`,
> `hit_effects.py`, `post_processing.py`, `pulso.py`, `trail_system.py`,
> `ambient_particles.py`, `weather_system.py`) verificados y documentados.
> Con esto, `src/framework/vfx/` queda completo en `22_API_CONTRACTS.md`.

---

## 21. Referencia de tipos de excepción

Todo módulo del framework debe lanzar una de éstas — nunca un `Exception` a secas ni un builtin no relacionado cuando una de éstas es más específica:

```python
class FrameworkUsageError(Exception):
    """El código de estudiante/escenario usó mal la API del framework (p. ej., falta una capa TMX)."""

class EngineError(RuntimeError):
    """Fallo irrecuperable a nivel de motor."""
```

`FilterTools`/`VisionTools`/`PatternRecognitionTools` lanzan `TypeError`/`ValueError`/`KeyError`/`RuntimeError` estándar según se documenta por método en los documentos 11–13 — no lanzan `FrameworkUsageError` (reservado para uso indebido en la construcción de escenario/entidad, no en llamadas de procesamiento).

---

## 22. Referencia rápida de convenciones de nombres

(AUD-455: la versión anterior remitía a `02_CODEX_CONTEXT.md` §5.2, un documento que no existe en este repositorio. Esta tabla es autosuficiente.)

| Elemento | Convención | Ejemplo |
|---|---|---|
| Módulo | `snake_case` | `enemy_walker.py` |
| Clase | `PascalCase` | `EnemyWalker` |
| Método/función | `snake_case` | `apply_damage()` |
| Propiedad | `snake_case` | `current_health` |
| Constante | `UPPER_SNAKE_CASE` | `PLAYER_MAX_HEALTH` |
| Privado | guion bajo inicial | `_collision_rects` |
| Cadena de nombre de evento | `UPPER_SNAKE_CASE` | `"PLAYER_DAMAGED"` |
| Miembro de enum | `UPPER_SNAKE_CASE` | `PlayerState.IDLE` |


---
## 🔗 Documentos relacionados

- [[23_DATA_SCHEMAS.md|Esquemas de datos]]
- [[03_ARCHITECTURE.md|Arquitectura]]
