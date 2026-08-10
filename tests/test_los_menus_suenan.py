"""AUD-345 — los menús suenan.

El hueco
--------
Los suscriptores de los 38 eventos SFX de AUD-290 vivían dentro de
`StageScene` (mixin `SonidoDeEscenario`). Una pantalla de título, un menú de
pausa o las opciones emiten `SFX_MENU_HOVER`, `SFX_MENU_CONFIRM` y
`SFX_MENU_CANCEL` sin que nadie los escuche: `docs/52_EVENT_MAP.md` lo
admitía por escrito — «un sonido emitido desde un menú no suena».

Qué fija
--------
* Los tres gestos de menú se suscriben una sola vez, al arrancar `App`,
  por `conectar_menu_al_audio` (que vive en `App`, como el audio y el bus).
* Las muestras son las mismas que el escenario usa para el mismo gesto.
* `App` retiene los manejadores: el bus guarda referencias débiles.
* La muestra existe en el banco de sonidos real (no es un nombre inventado).
"""
from __future__ import annotations

from src.engine.core.event_bus import EventBus
from src.engine.core.events import Events
from src.framework.audio.menu_sfx import SONIDOS_DE_MENU, conectar_menu_al_audio


class _AudioQueGraban:
    """Suplanta al gestor de audio: sólo registra qué reprodujo."""

    def __init__(self) -> None:
        self.reproducidos: list[str] = []

    def play_sfx(self, nombre: str, volume: float = 1.0) -> None:
        self.reproducidos.append(nombre)


class TestLosTresGestos:
    def test_hover_suena(self) -> None:
        bus = EventBus()
        audio = _AudioQueGraban()
        _ = conectar_menu_al_audio(bus, audio)
        bus.emit(Events.SFX_MENU_HOVER)
        bus.dispatch()
        assert audio.reproducidos[0] == "sfx_select"

    def test_hover_confirmar_y_cancelar_tienen_muestra(self) -> None:
        assert set(SONIDOS_DE_MENU) == {
            Events.SFX_MENU_HOVER, Events.SFX_MENU_CONFIRM,
            Events.SFX_MENU_CANCEL,
        }

    def test_las_muestras_son_las_del_escenario(self) -> None:
        import inspect

        from src.framework.scenes.stage_parts.sonido import (
            SonidoDeEscenario,
        )
        fuente = inspect.getsource(SonidoDeEscenario)
        assert "sfx_select" in SONIDOS_DE_MENU.values()
        assert "sfx_ui_menu_cancel" in SONIDOS_DE_MENU.values()
        assert "sfx_select" in fuente, (
            "la muestra del escenario y la del menú ya no coinciden"
        )


class TestSuscripcionGlobal:
    def test_el_bus_real_reparte_al_gestor(self) -> None:
        bus = EventBus()
        audio = _AudioQueGraban()
        manejadores = conectar_menu_al_audio(bus, audio)
        assert len(manejadores) == len(SONIDOS_DE_MENU)
        bus.emit(Events.SFX_MENU_HOVER)
        bus.emit(Events.SFX_MENU_CONFIRM)
        bus.emit(Events.SFX_MENU_CANCEL)
        bus.dispatch()
        assert audio.reproducidos == ["sfx_select", "sfx_select",
                                      "sfx_ui_menu_cancel"]

    def test_sin_retener_al_manejador_el_bus_se_queda_mudo(self) -> None:
        """El bus usa referencias débiles: la función de App los retiene."""
        bus = EventBus()
        audio = _AudioQueGraban()
        conectar_menu_al_audio(bus, audio)  # nadie guarda la lista
        import gc
        gc.collect()
        bus.emit(Events.SFX_MENU_CONFIRM)
        bus.dispatch()
        assert audio.reproducidos == [], (
            "el manejador fue recogido y el bus lo perdió: debe retenerse"
        )

    def test_las_muestras_existen_en_el_banco_real(self) -> None:
        import pygame

        from src.engine.audio.sound_bank import SoundBank
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
        banco = SoundBank()
        banco.load_all()
        for muestra in SONIDOS_DE_MENU.values():
            assert muestra in banco._sounds, f"falta {muestra} en assets/"

    def test_el_arranque_lo_cableda(self) -> None:
        import inspect

        from src.engine.core import app
        fuente = inspect.getsource(app)
        assert "conectar_menu_al_audio" in fuente
        assert "_sfx_de_menu" in fuente