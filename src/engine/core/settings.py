"""
Module: settings
System: engine.core
Academic Unit: N/A
Description: All global constants for the Legacy of InFest engine.
"""
import os
from pathlib import Path
from typing import Final

INTERNAL_WIDTH: int = 800
INTERNAL_HEIGHT: int = 600
TARGET_FPS: int = 60
# Window upscale factor. AUD-460: the window is really created at
# interior × DISPLAY_SCALE and the frame blit is scaled to it
# (`App._publicar_software`); before that the factor was only a promise.
# El camino GL (App._init_pygame) y el software (App._abrir_ventana_software)
# la aplican los dos.
_raw_scale = os.environ.get("LOI_DISPLAY_SCALE", "1")
try:
    _parsed_scale = int(_raw_scale) if _raw_scale and _raw_scale.lstrip("-").isdigit() else 1
except ValueError:
    _parsed_scale = 1
DISPLAY_SCALE: int = max(1, min(4, _parsed_scale))

# AUD-021: the reference-resolution auto-scale branch that used to live here was
# unreachable — it required INTERNAL_WIDTH == 320, and INTERNAL_WIDTH is 800.
# The constants are retained because asset tooling references them as the
# design resolution for legacy sprite work.
REFERENCE_WIDTH: int = 320
REFERENCE_HEIGHT: int = 224

TILE_SIZE: int = 16

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT: Path = _PROJECT_ROOT
ASSETS_DIR: Path = _PROJECT_ROOT / "assets"
STAGES_DIR: Path = _PROJECT_ROOT / "src/stages"
STUDENT_TEMPLATES_DIR: Path = _PROJECT_ROOT / "student_templates"

PLAYER_MAX_HEALTH: float = 5.0
GRAVITY: float = 800.0
PLAYER_WALK_SPEED: float = 90.0
#: Base del deslizamiento sostenido en cuesta (AUD-326): sin entrada
#: horizontal, la gravedad desliza al jugador cuesta abajo a
#: `PLAYER_SLOPE_SLIDE_SPEED * sin(fi) * cos(fi)` px/s — la componente
#: paralela de la gravedad a lo largo de la hipotenusa, como la proyección
#: de aterrizaje de AUD-324, pero acotada: velocidad constante, no una
#: aceleración en fuga. La mitad de `PLAYER_WALK_SPEED` como máximo (45°).
PLAYER_SLOPE_SLIDE_SPEED: float = 90.0
PLAYER_JUMP_FORCE: float = -380.0
PLAYER_MAX_FALL_SPEED: float = 500.0
PLAYER_COYOTE_FRAMES: int = 6
PLAYER_DASH_SPEED: float = 200.0
PLAYER_AIR_DASH_LIMIT: int = 1
PLAYER_AIR_JUMPS: int = 1
#: ¿Hay que ganarse el doble salto y el dash? (AUD-238, AUD-294)
#:
#: **Encendido desde AUD-294**, que es lo que convierte derrotar a un jefe en
#: progresión de verdad: la mecánica no está disponible hasta que la suelta.
#:
#: AUD-238 lo dejó apagado por una razón que sigue siendo cierta —las entregas
#: existentes diseñaron sus saltos contando con el doble salto desde el primer
#: fotograma— y por eso encenderlo no basta con cambiar este `False` por un
#: `True`: hace falta `ESCENARIOS_CON_HABILIDADES_LIBRES`, que exime uno por uno
#: a los mapas anteriores. Medido, sin esa lista se rompen seis de dieciséis.
#:
#: Nunca bloquea el salto desde el suelo ni el coyote: eso no es progresión, es
#: un juego roto.
PLAYER_SKILLS_REQUIRE_UNLOCK: bool = True

#: Los escenarios que arrancan con todas las mecánicas concedidas — AUD-294.
#:
#: Por qué existe esta lista, medido
#: ---------------------------------
#: Encender el candado a secas rompe seis de los dieciséis mapas entregados, y
#: **dos dejan de poder terminarse**: `stage0` —el mapa de referencia, el que
#: copian los estudiantes— y `stage3_4_boss_gavilan`. Comparado con
#: `grade_stage`, con y sin salto aéreo:
#:
#:     stage0                 salida alcanzable True -> False
#:     stage3_4_boss_gavilan  salida alcanzable True -> False
#:     stage1_1, stage2_2, stage3_3_el_patio, stage4_1
#:                            aparecen huecos imposibles
#:
#: La invariante 2 dice que esas entregas siguen funcionando sin tocar una
#: línea, y eso incluye no tocar sus `.tmx`. Así que la exención vive **aquí**,
#: en el motor, con la lista explícita de lo que se entregó antes del candado.
#: Un escenario nuevo no está en la lista y nace con la progresión encendida,
#: que es lo que se pedía.
#:
#: Un mapa nuevo que quiera lo mismo lo declara con la propiedad TMX
#: `habilidades_libres`, y así queda escrito en el mapa y no en el motor.
ESCENARIOS_CON_HABILIDADES_LIBRES: frozenset[str] = frozenset({
    "stage0", "stage1_1", "stage1_2_la_soda", "stage1_3_las_aulas",
    "stage2_1", "stage2_2", "3-1", "stage3_3_el_patio",
    "stage3_4_boss_gavilan", "stage4_1", "hall", "stage_template",
    "stage_mecanicas", "boss_venado", "boss_rey", "boss_paburu",
})
PLAYER_SHORT_ATTACK_DURATION: float = 0.15
PLAYER_LONG_ATTACK_DURATION: float = 0.4
PLAYER_COOLDOWN_SHORT: float = 0.0
PLAYER_COOLDOWN_LONG: float = 0.067
BG_COLOR: tuple[int, int, int] = (15, 15, 40)

#: Píxeles más allá del encuadre que se siguen simulando y dibujando (AUD-279).
#:
#: Una pantalla entera por lado. El primer valor que probé fue 400 —el doble de
#: los 360 px que recorre como mucho un `Projectile`, 120 px/s durante 3 s— y
#: **rompió stage 0**: el mapa mide 1.600 px y cuatro de sus nueve enemigos
#: quedaban fuera de la zona con la cámara en el arranque, así que
#: `test_every_enemy_in_stage0_moves` los encontró convertidos en estatuas.
#:
#: 800 mantiene el mapa de referencia —el que copian los estudiantes— con el
#: comportamiento exacto que tenía antes de AUD-279, y sigue sobrando sobre el
#: alcance de cualquier proyectil. Bajarlo hace visible el congelado; subirlo lo
#: vuelve inútil.
#:
#: **Cero lo apaga entero.** Está para cuando alguien sospeche que el culling le
#: está escondiendo un fallo, que es la primera pregunta razonable ante un
#: enemigo que no se mueve. El porqué completo, en `framework/stage/culling.py`.
CULLING_MARGEN: int = 800

#: ¿Una entidad que lanza en `update()` se lleva por delante el fotograma? (AUD-289)
#:
#: **No, por defecto.** Este motor ejecuta código de veintiséis estudiantes: un
#: `IndexError` en el `update` de un enemigo de una entrega tumbaba el fotograma
#: entero y `App` devolvía al menú de título, que desde el asiento del estudiante
#: se ve como «el juego se cierra». La entidad se retira, el nivel sigue, y el
#: fallo se registra con su traza.
#:
#: `False` vuelve a propagar la excepción. Es lo que quiere quien está depurando
#: **el motor** y necesita la traza donde ocurre, no un resumen en el registro.
AISLAR_FALLOS_DE_ENTIDAD: bool = True

COMBO_WINDOW: float = 0.5
# AUD-021: a tuple, not a list. As a mutable list this balance table could be
# reordered or appended to from anywhere in the process — including by a test
# that forgot to restore it — silently rebalancing combat. Indexing is
# unchanged, so no call site needed updating.
# AUD-COMBO: ampliado de 3 a 10 para que `combo_king` (10 hits) sea alcanzable;
# antes 10 era imposible con COMBO_MAX=3. Primeros 3 valores conservan 1.0/1.5/2.0
# para no romper tests ni balance existente; 4-10 escalan hasta 3.0.
COMBO_DAMAGE_MULT: Final[tuple[float, ...]] = (1.0, 1.5, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.0, 3.0)
COMBO_MAX: int = 10

# ── Accessibility and other player preferences ─────────────────
#
# AUD-021 / AUD-036: COLORBLIND_MODE and SUBTITLES_ENABLED used to live here as
# bare mutable globals. Nothing ever wrote to them, so the colourblind filter
# read a permanently-"off" value while the options screen persisted the player's
# real choice to a config file that nothing loaded — the setting could never
# take effect. Player preferences are now owned, validated and persisted by
# src.engine.core.user_settings; read them with:
#
#     from src.engine.core import user_settings
#     mode = user_settings.get().colorblind_mode
#
# This module is for engine constants that must never change at runtime.
