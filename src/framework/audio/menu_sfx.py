"""
El sonido de los menús: SFX_MENU_* suena donde sea que se emita.

AUD-345 — los menús eran los únicos mudos del juego
===================================================
Los 38 eventos de AUD-290 se suscribían dentro de `StageScene` con
`SonidoDeEscenario`, y eso dejaba una isla de silencio fuera del escenario:
una pantalla de título, un menú de pausa o la pantalla de opciones emiten
`SFX_MENU_HOVER` desde `docs/52_EVENT_MAP.md` sin que **nadie** las escuche.
El documento lo admitía en su propio mapa: «un sonido emitido desde un menú
no suena».

Aquí vive el suscriptor global de esos tres eventos (hover, confirmar,
cancelar). Lo monta `App` en el arranque, una vez, porque el gestor de audio
y el bus viven en `App` y no en ninguna escena — igual que la consola de F11:
un sonido de menú es del motor, no del escenario, y un menú de estudiante no
debe tener que cablear nada para que suene.

Sigue siendo el mismo patrón que el del escenario: un mapa evento → muestra
compartido con `SonidoDeEscenario` para que el mismo gesto suene igual en un
menú y dentro de un nivel, el *handler* se guarda en la lista que devuelve
porque el bus guarda referencias débiles, y quien lo invoca no sabe dónde
está el altavoz.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.engine.core.events import Events

#: Muestra que suena para cada gesto de menú — las mismas que `sonido.py`
#: usa dentro del escenario, para que el oído no note el cambio de escena.
SONIDOS_DE_MENU: dict[str, str] = {
    Events.SFX_MENU_HOVER: "sfx_select",
    Events.SFX_MENU_CONFIRM: "sfx_select",
    Events.SFX_MENU_CANCEL: "sfx_ui_menu_cancel",
    # AUD-443 — la risa del paburu se emitía desde `LoadGameScene` sin que
    # nadie la escuchara: faltaba el fichero y este mapeo. El guardián
    # `test_las_muestras_existen_en_el_banco_real` tiene razón: una muestra
    # declarada y ausente es un menú que enmudece en silencio. El `.wav`
    # actual es un placeholder sintetizado (ver `KNOWN_GAPS.md`, AUD-541);
    # cuando exista la grabación de autor, basta con sustituir el fichero.
    Events.SFX_VOZ_PABURU: "sfx_voz_paburu_risa",
}


def conectar_menu_al_audio(event_bus, audio) -> list[Callable[..., None]]:
    """Suscribe los tres gestos de menú al gestor de audio y los retiene.

    Devuelve la lista de manejadores para que la guarde quien llama — el bus
    del motor usa referencias débiles y un manejador recogido por el
    recolector hace que el menú vuelva a quedarse mudo en silencio.
    """
    manejadores: list[Callable[..., None]] = []
    for evento, muestra in SONIDOS_DE_MENU.items():
        def manejador(*_args: Any, _muestra: str = muestra, **_: Any) -> None:
            audio.play_sfx(_muestra)
        event_bus.subscribe(evento, manejador)
        manejadores.append(manejador)
    return manejadores