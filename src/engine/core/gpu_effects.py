"""
Module: gpu_effects
System: engine.core
Academic Unit: N/A
Description: AUD-222 — el reparto de efectos de pantalla completa entre la GPU
y la CPU, y los parámetros que la CPU le pasa a la GPU.

Por qué existe
--------------
El juego tiene **dos** tuberías de post-procesado escritas por separado:
`src/engine/render/gl_pipeline.py` (sombreadores, sólo si hay ModernGL, que es
un extra opcional) y `src/framework/vfx/post_processing.py` (superficies de
pygame, siempre). `App` arranca con `use_gl=True`, y `StageScene.draw` llamaba
a `PostProcessing.apply(surface)` sin mirar si había GL. En una máquina con
tarjeta se aplicaban **las dos**: la viñeta oscurecía las esquinas dos veces y
el halo del bloom se calculaba por CPU para que el sombreador lo repitiera.

Por qué el reparto vive aquí y no en ninguna de las dos tuberías
----------------------------------------------------------------
`PostProcessing` está en `framework/` y no puede preguntar por `App` ni
importar `moderngl`: `tests/test_layering.py` vigila que el motor no dependa
del juego, y acoplar el post-procesado a la existencia de un contexto GL
rompería además el camino software, que es el único que existe en CI y en
cualquier instalación sin el extra `accel`.

Así que el reparto es un dato de proceso que **la raíz de composición fija una
vez al arrancar** —es la única que sabe si el contexto GL se creó de verdad— y
que las dos tuberías consultan. Es el mismo patrón de `user_settings`: un
estado propietario con lectura y escritura explícitas, y no un global mutable
que cualquiera toca (AUD-021 / AUD-036).

Qué NO es delegable, y por qué
-------------------------------
Sólo están aquí los efectos que **las dos** tuberías saben hacer y que hacen lo
mismo. Se comprobó pasada por pasada:

* **destello y tinte** — no tienen sombreador. Se quedan en la CPU siempre.
* **corrección de color** — el sombreador multiplica por una matriz *fija de la
  configuración*; la de CPU la pone cada escenario. No son el mismo efecto, así
  que apagar una no sustituye a la otra.
* **desenfoque de movimiento** — el sombreador mezcla con el fotograma anterior
  de forma incondicional; el de CPU lo enciende el juego (`set_motion_blur`).
  Igual que el anterior: parecidos, no equivalentes.
* **daltonismo** — `colorblind_frag` existe y, desde AUD-252, `App` sí le pasa
  el modo del jugador (`modo_daltonico_gl()` en `app.py` traduce
  `UserSettings.colorblind_mode` al entero que espera `GLRenderConfig`). Antes
  de AUD-252 nadie escribía ese campo y el sombreador no se ejecutaba nunca;
  este comentario describía ese estado y quedó desactualizado cuando se
  corrigió. Sus matrices tampoco son las de la CPU (AUD-138) — eso sigue sin
  resolver, así que aunque el modo llega al sombreador, un jugador daltónico
  puede ver una corrección distinta según si su máquina usa GL o el camino de
  software.
* **iluminación** — la aplica `LightSystem`, no `PostProcessing`; se reparte en
  otro sitio.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Final

#: Halo de las zonas brillantes. `PostProcessing._apply_bloom` frente a
#: `bloom_frag`.
BLOOM: Final = "bloom"

#: Oscurecimiento de las esquinas. `PostProcessing.apply` frente a
#: `vignette_frag`.
VIGNETTE: Final = "vignette"

#: Los únicos dos efectos que hoy pueden cambiar de lado. Ampliar esta lista
#: exige comprobar que la pasada de GL hace *lo mismo* que la de CPU, no algo
#: parecido: el resto de la tabla de arriba explica por qué los demás no están.
#: Ondas de agua. `framework.vfx.water_effect.WaterEffect` frente a
#: `refraction_frag`. AUD-216 — y aquí los dos NO hacen lo mismo a propósito:
#: el de CPU superpone líneas senoidales encima de la escena, el sombreador
#: deforma lo que se ve a través del agua. Se delega igualmente porque el
#: segundo es el efecto que el primero intentaba imitar, no una variante.
WATER: Final = "water"

#: Los efectos que hoy pueden cambiar de lado. Ampliar esta lista exige
#: comprobar que la pasada de GL hace *lo mismo* que la de CPU —o, como con el
#: agua, que la sustituye a conciencia—, no algo parecido por accidente: el
#: resto de la tabla de arriba explica por qué los demás no están.
DELEGABLES: Final[frozenset[str]] = frozenset({BLOOM, VIGNETTE, WATER})

_en_la_gpu: frozenset[str] = frozenset()
_bloom_publicado: float = 0.0


def set_effects_on_gpu(names: Iterable[str]) -> None:
    """Declara qué efectos está haciendo ya la GPU. La llama `App`.

    Un nombre desconocido **lanza** en vez de ignorarse. Degradar en silencio
    aquí reproduciría AUD-036 al detalle: la duplicación seguiría ahí, nada
    fallaría, y quien lo escribió creería haberla quitado.
    """
    global _en_la_gpu
    pedidos = frozenset(names)
    desconocidos = pedidos - DELEGABLES
    if desconocidos:
        raise ValueError(
            f"efectos no delegables: {sorted(desconocidos)}. Sólo "
            f"{sorted(DELEGABLES)} existen en las dos tuberías y hacen lo "
            f"mismo; el destello, el tinte, la corrección de color, el "
            f"desenfoque de movimiento y el daltonismo no, y el porqué de cada "
            f"uno está en el docstring de este módulo",
        )
    _en_la_gpu = pedidos


def effects_on_gpu() -> frozenset[str]:
    """Los efectos que la CPU debe saltarse en este proceso."""
    return _en_la_gpu


def is_on_gpu(name: str) -> bool:
    return name in _en_la_gpu


def reset() -> None:
    """Vuelve al camino software puro. Existe para las pruebas: el reparto es
    estado de proceso y una prueba que lo deje puesto contamina a la siguiente.
    """
    global _en_la_gpu, _bloom_publicado, _aberracion_pedida, _agua_region, _rayos
    global _lote_de_sprites, _matriz_de_color
    _en_la_gpu = frozenset()
    _bloom_publicado = 0.0
    _aberracion_pedida = 0.0
    _agua_region = None
    _rayos = None
    _lote_de_sprites = None
    # AUD-413 — la matriz de color entra aquí, y no estaba: AUD-401 la publicó
    # sin engancharla a este borrón, así que una prueba que la dejaba puesta
    # encendía la pasada de grading para las siguientes y les cambiaba el
    # número de pasadas de la cadena. Es literalmente lo que avisa el docstring
    # de arriba, y aun así costó nueve pruebas rojas en
    # `test_aberracion_cromatica.py`.
    _matriz_de_color = None


def begin_frame() -> None:
    """Olvida los parámetros publicados en el fotograma anterior.

    Sin esto, un menú -que no ejecuta post-procesado- heredaría el bloom del
    nivel del que se acaba de salir y seguiría brillando hasta que otra escena
    publicara otro valor.
    """
    global _bloom_publicado, _agua_region, _rayos, _lote_de_sprites
    global _matriz_de_color
    _bloom_publicado = 0.0
    # AUD-216/217 - el agua y los rayos también se olvidan cada fotograma, y
    # por la misma razón que el bloom: los menús no dibujan escenario, así que
    # sin este borrón la pantalla de pausa heredaría el estanque y los rayos
    # del nivel del que se acaba de salir.
    _agua_region = None
    _rayos = None
    # AUD-342 - y el lote de sprites de GPU con ellos: un menú que se apoya
    # encima del nivel no debe re-componer las órdenes del fotograma anterior.
    _lote_de_sprites = None
    # AUD-413 - el tinte del ambiente, por lo mismo. `publish_color_matrix`
    # decía en su docstring que un menú no hereda el tinte del nivel anterior
    # y **no era verdad**: AUD-401 no lo enganchó a este borrón. La promesa
    # estaba escrita y el código no la cumplía.
    _matriz_de_color = None


def publish_bloom(intensity: float) -> None:
    """Cuánto bloom pide la escena en este fotograma, de 0 a 1.

    Delegar el bloom no puede ser apagarlo: el de la CPU es dinámico —una
    ráfaga al cambiar de fase el jefe, un valor base por escenario leído del
    TMX— y el del sombreador venía fijo en la configuración. Sin este canal,
    delegar cambiaría un efecto que responde al juego por un brillo constante
    encendido también en los menús.
    """
    global _bloom_publicado
    _bloom_publicado = max(0.0, min(1.0, intensity))


def published_bloom() -> float:
    return _bloom_publicado


#: AUD-401 — la matriz de corrección de color que pide la escena (GAP-051).
#:
#: `None` = nadie ha pedido nada y la pasada se queda como estaba. Es lo que
#: hace que un menú, o un escenario que no monta simulación de mundo, no herede
#: el tinte del nivel anterior.
_matriz_de_color: tuple[float, ...] | None = None


def publish_color_matrix(matriz: tuple[float, ...] | None) -> None:
    """El tinte y la desaturación que pide el ambiente de este escenario.

    Va por aquí y no tocando el renderer directamente porque una escena **no
    puede alcanzarlo**: el contexto expone `usar_gl` y no el objeto, a
    propósito, para que el framework no tenga que importar ModernGL. Es el
    mismo canal que `publish_bloom` y por el mismo motivo.

    La pasada de *color grading* llevaba compilada desde hace tiempo con una
    matriz fija en el config que no cambiaba nadie: encendida y multiplicando
    por la identidad. Esto es quien la alimenta.
    """
    global _matriz_de_color
    _matriz_de_color = tuple(matriz) if matriz is not None else None


def published_color_matrix() -> tuple[float, ...] | None:
    return _matriz_de_color


#: Golpe de aberración cromática pendiente de recoger. AUD-215/AUD-222.
_aberracion_pedida: float = 0.0


def request_chromatic_aberration(strength: float) -> None:
    """Pide un golpe de aberración cromática para un impacto fuerte.

    Lo llama el juego —`stage_parts/senales.py`, donde ya se disparan el
    destello y la sacudida de cámara— y lo recoge `App`, que es quien tiene el
    renderizador. Va por aquí y no por una llamada directa por la misma razón
    que el bloom: una escena de `framework/` no puede alcanzar el `GLRenderer`
    sin acoplarse a que exista un contexto GL, y en el camino software esto no
    tiene que hacer nada.

    Se queda con el máximo de lo pedido en el fotograma: dos golpes a la vez
    son un golpe fuerte, no dos que se pisan.
    """
    global _aberracion_pedida
    _aberracion_pedida = max(_aberracion_pedida, min(1.0, max(0.0, strength)))


#: Región de agua en píxeles de pantalla, y foco de los rayos. AUD-216/217.
_agua_region: tuple[int, int, int, int] | None = None
_rayos: tuple[tuple[float, float], float] | None = None


def publish_water_region(region: tuple[int, int, int, int] | None) -> None:
    """Dónde hay agua en pantalla este fotograma, en píxeles (x, y, ancho, alto).

    Origen arriba-izquierda, como todo en pygame; la conversión al sistema de
    OpenGL —que numera las filas al revés— la hace `region_to_gl_uv` en la
    tubería, que es la única que sabe cómo subió la textura.

    Se publica cada fotograma y no se recuerda: la región es consecuencia de
    dónde está la cámara, no un ajuste. Recordarla dejaría el agua pegada a la
    pantalla al cambiar de escenario.
    """
    global _agua_region
    _agua_region = region


def published_water_region() -> tuple[int, int, int, int] | None:
    return _agua_region


def publish_god_rays(origin_uv: tuple[float, float], strength: float) -> None:
    """Enciende los rayos volumétricos con su foco, en coordenadas 0..1.

    El foco va en UV y no en píxeles porque es lo que consume el sombreador, y
    porque así la escena decide *qué* luz manda —normalmente la más brillante
    en pantalla— sin que la tubería tenga que saber nada de focos ni de cámara.
    """
    global _rayos
    _rayos = (origin_uv, max(0.0, strength))


def published_god_rays() -> tuple[tuple[float, float], float] | None:
    return _rayos


#: El lote de sprites de GPU que la escena rellenó este fotograma. AUD-342.
_lote_de_sprites: Any = None


def publish_lote_de_sprites(lote: Any) -> None:
    """Publica el lote de sprites que la escena acaba de rellenar en la GPU.

    AUD-342, fase 5 lote 2 — el canal que activa la composición de sprites en
    la tarjeta **por contexto**: una escena que quiera dibujar sus sprites en
    la GPU rellena el lote que le da `GameContext.lote_de_sprites` —cámara,
    luces y órdenes— y lo publica aquí. `App` lo recoge y se lo pasa a la
    pasada de composición del `GLRenderer`, que lo mezcla sobre la escena
    entre la subida y la refracción. Una escena que no publica nada sigue
    dibujando por CPU, que es el camino de siempre, sin pagar una pasada.

    El lote se pasa sin tipo porque este módulo no puede importar la clase:
    vive en `engine.render`, que carga ModernGL, y este canal existe para
    que la CPU no dependa de que haya tarjeta. Es un dato opaco que viaja
    de la escena al renderer, como el agua o los rayos.
    """
    global _lote_de_sprites
    _lote_de_sprites = lote


def published_lote_de_sprites() -> Any:
    """El lote publicado este fotograma, o `None` si nadie dibujó en GPU."""
    return _lote_de_sprites


def consume_chromatic_aberration() -> float:
    """Recoge y borra el golpe pendiente. La llama `App` una vez por fotograma.

    Consume en vez de sólo leer porque es un **impulso**, no un estado: quien
    mantiene la intensidad viva mientras decae es el renderizador
    (`update_chromatic_aberration`). Si esto no se vaciara, un solo impacto
    reencendería el efecto en todos los fotogramas siguientes.
    """
    global _aberracion_pedida
    pedido = _aberracion_pedida
    _aberracion_pedida = 0.0
    return pedido
