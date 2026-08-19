"""AUD-554 — GAP-070, las tres piezas que quedaban con chokepoint
disponible sin tocar DSP en tiempo real:

1. Pasos sobre Tierra/Grava (Fase 1) — la Fase 1 no declaraba ninguna
   `ZonaDeFriccion` propia y sonaba con el `sfx_step` genérico que
   comparten los otros 25 escenarios.
2. Pasos Ahogados (Fase 5) — mismo problema, terreno distinto.
3. La Voz del Bosque — el Venado reusaba el timbre de marcador de
   posición de AUD-263 (`sfx_voz_venado_fase1`) mientras el Rey
   Terciopelo y el Gavilán ya tenían receta propia desde AUD-551.

Ver KNOWN_GAPS.md GAP-070 para lo que sigue sin construir (necesita DSP
en tiempo real que el motor no tiene).
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame


class TestLosMaterialesNuevosExisten:
    def test_grava_y_ahogado_estan_en_el_catalogo(self) -> None:
        from src.framework.physics.perfil import AHOGADO, GRAVA, MATERIALES

        assert MATERIALES["grava"] is GRAVA
        assert MATERIALES["ahogado"] is AHOGADO

    def test_ninguno_cambia_la_fisica(self) -> None:
        """Igual que `lodo`: nombran la zona, no la tocan — el freno real
        sigue viniendo de `ZonaDeFriccion.multiplicador`, sin cambios."""
        from src.framework.physics.perfil import AHOGADO, GRAVA, ROCA

        assert GRAVA.restitucion == ROCA.restitucion == 0.0
        assert AHOGADO.restitucion == ROCA.restitucion == 0.0


class TestLosEventosDePisadaExisten:
    def test_grava_y_ahogado(self) -> None:
        from src.engine.core.events import Events

        assert hasattr(Events, "SFX_PLAYER_FOOTSTEP_GRAVA")
        assert hasattr(Events, "SFX_PLAYER_FOOTSTEP_AHOGADO")


class TestCaminarSobreCadaTerrenoEmiteSuPropioEvento:
    def _emitido_al_caminar(self, nombre_material: str) -> set[str]:
        from src.engine.core.event_bus import EventBus
        from src.engine.core.events import Events
        from src.engine.input.input_manager import InputManager
        from src.framework.entities.player import Player
        from src.framework.entities.states import WalkingState
        from src.framework.physics.perfil import MATERIALES

        bus = EventBus()
        recibidos: list[str] = []

        # El bus guarda referencias débiles (AUD-152) — los manejadores
        # necesitan un nombre que los mantenga vivos hasta `dispatch()`.
        def _al_grava(**_k):
            recibidos.append("grava")

        def _al_ahogado(**_k):
            recibidos.append("ahogado")

        def _al_lodo(**_k):
            recibidos.append("lodo")

        def _al_musgo(**_k):
            recibidos.append("musgo")

        def _al_generico(**_k):
            recibidos.append("generico")

        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP_GRAVA, _al_grava)
        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP_AHOGADO, _al_ahogado)
        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP_LODO, _al_lodo)
        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP_MUSGO, _al_musgo)
        bus.subscribe(Events.SFX_PLAYER_FOOTSTEP, _al_generico)

        jugador = Player(pygame.Vector2(0.0, 0.0), event_bus=bus)
        jugador._material_de_zona = MATERIALES.get(nombre_material)
        estado = WalkingState()
        estado._footstep_timer = 1.0

        estado.update(jugador, 0.016, InputManager())
        bus.dispatch()
        return set(recibidos)

    def test_grava(self) -> None:
        assert self._emitido_al_caminar("grava") == {"grava"}

    def test_ahogado(self) -> None:
        assert self._emitido_al_caminar("ahogado") == {"ahogado"}


class TestLaVozDelVenadoTieneRecetaPropia:
    def test_ya_no_reusa_el_marcador_de_posicion(self) -> None:
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert Stage4_1._VOZ_POR_ESPIRITU[0] != "sfx_voz_venado_fase1"
        assert Stage4_1._VOZ_POR_ESPIRITU[0] == "sfx_voz_venado_ancestral"

    def test_las_tres_voces_siguen_siendo_distintas(self) -> None:
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert len(set(Stage4_1._VOZ_POR_ESPIRITU.values())) == 3


class TestLasDosFasesNuevasNoInvadenLaFase2:
    """`tools/generate_stage4_1.py::_objetos` gana dos `FrictionZone` que
    cubren toda la Fase 1 (`material="grava"`) y toda la Fase 5
    (`material="ahogado"`) — coordenadas verificadas a mano en terminal
    (x=48/w=2352 y x=9600/w=2400, exactas contra `ANCHO_SECCION`/`TS`).

    `assets/maps/stage4_1/stage4_1.tmx` no se regenera entero sin
    `--forzar` (tiene arte pintado a mano), así que la capa `Objects`
    entera se reescribió quirúrgicamente con la salida fresca de
    `_objetos()` — no sólo se añadieron los dos objetos nuevos al final,
    porque `TestElMapaSigueAtadoASuGenerador` (`test_stage4_1.py`)
    compara la capa completa **con id incluido**, y una zona nueva
    insertada a mitad de la función desplaza el id de todo lo que viene
    después. Esa prueba (ya existente, AUD-495) es la que de verdad
    protege que el TMX comprometido siga siendo el que produce el
    generador; aquí sólo se comprueba que las columnas de las dos zonas
    nuevas no invadan la Fase 2."""

    def test_las_dos_zonas_no_se_solapan_con_musgo_o_lodo(self) -> None:
        """La Fase 1 (grava) y la Fase 5 (ahogado) no comparten columnas
        con la Fase 2 (musgo/lodo) — si se solaparan, "la última zona que
        toca manda" (`sistema_friccion.py`) apagaría el material de la
        fase que perdiera la carrera."""
        from src.stages.stage4_1.fases import FASES
        from src.stages.stage4_1.trazado import SEGMENTOS_FASE2

        fase1, fase2 = FASES[0], FASES[1]
        fin_fase1 = fase2.desde_columna
        assert fase1.desde_columna < fin_fase1 <= fase2.desde_columna
        for inicio, _ancho, _material in SEGMENTOS_FASE2:
            assert inicio >= fin_fase1, "un segmento de la Fase 2 invade la Fase 1"
