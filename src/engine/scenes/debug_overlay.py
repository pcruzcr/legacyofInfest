"""
Module: debug_overlay
System: engine.scenes
Description: Consola de depuración (F11). FPS, coste del fotograma, cuentas de
la escena, cola de eventos y árbol de módulos.

Dos cosas que arregla AUD-283
=============================
**Esto no lo abría nadie.** El módulo estaba entero —consola, cola de eventos,
árbol de módulos— y no tenía **un solo llamante en `src/engine`**. Ni una
prueba. `docs/87` §15.7 llegó a describirlo como si funcionara («F3 abre la
consola…»), que es el error de leer el código y no ejecutarlo: la décima vez
este mes que aparece código correcto que no llega al jugador.

Tampoco lo detectaba `check_orphan_systems.py`, y por una razón interesante:
ese barrido busca símbolos que **las pruebas ejercitan y el juego no invoca**.
Lo que no prueba nadie **y** no usa nadie le resulta invisible. Queda anotado
por si vuelve a hacer falta buscar en ese hueco.

**Y la tecla estaba ocupada.** Se abría con F3, que desde el mapa de acciones
es `LEARN_PHYSICS`. Aunque alguien lo hubiera conectado, pulsarla habría abierto
la lección de física. Ahora es **F11**, que estaba libre, y el nivel del árbol
se cambia con F12.

Qué mide, y qué no
==================
Lo que se puede medir barato y en cualquier equipo: FPS, milisegundos de
fotograma, y las cuentas que la escena quiera publicar —entidades, partículas,
decisiones del escuadrón—.

**La RAM del proceso no está**, y no por olvido: medirla en Windows y en Linux
sin dependencias nuevas obliga a `ctypes` por plataforma, y `psutil` no está
instalado. Lo que sí se enseña es el número de objetos vivos que Python conoce,
que es gratis y responde a la pregunta que de verdad se hace uno mirando esto:
«¿esto está creciendo?».
"""
from __future__ import annotations

import gc
import logging
from typing import Any

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.engine.ui.theme import font

logger = logging.getLogger(__name__)

#: Tecla que abre y cierra la consola. F11 porque F1 son los gizmos del
#: escenario y F2–F10 son las lecciones del curso (`action_map`).
TECLA_CONSOLA = pygame.K_F11

#: Tecla que rota el nivel del árbol de módulos.
TECLA_ARBOL = pygame.K_F12

TREE_LEVELS = [
    "Engine / Core",
    "Engine / IO",
    "Framework / Scenes",
    "Framework / Entities",
    "Framework / Processing",
]


class DebugOverlay:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        """AUD-019: the bus is injected rather than pulled from a global."""
        self._event_bus: EventBus | None = event_bus
        self._visible: bool = False
        self._tree_level: int = 0
        self._font: pygame.font.Font | None = None
        self._overlay: pygame.Surface | None = None
        self._line_cache: dict[int, tuple[str, pygame.Surface]] = {}
        self._hint_surf: pygame.Surface | None = None
        # AUD-754 — diagnóstico de presentación nativa (F9)
        self._display_diag: bool = False
        self._display_diag_surf: pygame.Surface | None = None
        # AUD-806 — Visual Forensics Mode (F8) — runtime frame truth
        self._forensics: bool = False
        self._forensics_state: dict[str, object] | None = None

    def _ensure_font(self) -> None:
        if self._font is not None:
            return
        self._font = font(7)

    @property
    def visible(self) -> bool:
        return self._visible

    def toggle_display_diagnostics(self) -> None:
        """AUD-754 — alterna overlay de diagnóstico de presentación (F9)."""
        self._display_diag = not self._display_diag
        self._visible = True  # al activar diagnóstico, mostrar consola

    def toggle_forensics(self) -> None:
        """AUD-806 — Visual Forensics Mode (F8) — runtime frame truth.

        No altera gameplay ni renderer: sólo observa y describe la cadena
        WORLD → CAMERA → SCREEN → INTERNAL → VIEWPORT → DISPLAY para cada píxel.
        Activable/desactivable sin recrear FBOs ni tocar lógica.
        """
        self._forensics = not self._forensics
        self._visible = True

    def set_forensics_state(self, state: dict[str, object] | None) -> None:
        """Inyecta el estado forense recolectado por App/drawing (camera, player, etc)."""
        self._forensics_state = state

    def handle_input(self, input_manager: Any) -> None:
        """Lee las dos teclas de la consola. Lo llama `App`, cada fotograma.

        AUD-283 — antes recibía la tupla de `pygame.key.get_pressed()` y llevaba
        su propio sistema de enfriamientos de 0,3 s para no dispararse en cada
        fotograma con la tecla pulsada. Sobra: `is_raw_key_pressed` ya es por
        flanco. Un temporizador que replica algo que el gestor de entrada hace
        mejor es una segunda verdad sobre cuándo se pulsó una tecla, y las dos
        acaban discrepando.
        """
        if input_manager is None:
            return
        if input_manager.is_raw_key_pressed(TECLA_CONSOLA):
            self._visible = not self._visible
        if self._visible and input_manager.is_raw_key_pressed(TECLA_ARBOL):
            # Una tecla que rota, en vez de tres que eligen. F4, F5 y F6 son
            # `LEARN_COLLISION`, `LEARN_FSM` y `LEARN_RENDER`: elegir el nivel
            # del árbol abría además tres lecciones del curso.
            self._tree_level = (self._tree_level + 1) % len(TREE_LEVELS)
        # AUD-754 — F9 diagnóstico de display (independiente de F11, pero muestra overlay)
        if input_manager.is_raw_key_pressed(pygame.K_F9):
            self.toggle_display_diagnostics()
        # AUD-806 — F8 Visual Forensics Mode
        if input_manager.is_raw_key_pressed(pygame.K_F8):
            self.toggle_forensics()

    def draw(self, surface: pygame.Surface, fps: float,
             medidas: dict[str, Any] | None = None,
             estadisticas: dict[str, float] | None = None) -> None:
        """Pinta la consola. `medidas` es lo que la escena quiera publicar.

        Un diccionario y no una estructura fija a propósito: cada escena mide
        cosas distintas —un escenario tiene enemigos y partículas, un menú no—
        y una estructura con campos obligatorios obligaría a los menús a
        rellenar ceros que no significan nada.

        `estadisticas` son los cuantiles de AUD-346 —P50/P95/P99/media/peor
        del historial de fotogramas— y los enseña `App` al lado del FPS
        instantáneo, porque el número de un segundo no cuenta los tropezones.
        """
        if not self._visible:
            return
        self._ensure_font()

        if self._hint_surf is None:
            self._hint_surf = self._font.render(
                "  Consola de depuración  |  [F11] cerrar  |  [F12] árbol",
                True, (80, 200, 255))

        # Semi-transparent overlay
        if self._overlay is None or self._overlay.get_size() != (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT):
            self._overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        overlay = self._overlay
        overlay.set_alpha(180)
        overlay.fill((5, 5, 15))
        surface.blit(overlay, (0, 0))

        y = 4
        lines: list[str] = []
        # AUD-283 — los milisegundos, no sólo los FPS. Un contador de FPS
        # redondeado a entero no distingue 16,6 ms de 12,0: los dos dicen «60».
        # El presupuesto de este motor está escrito en milisegundos y es en
        # milisegundos como hay que poder leerlo.
        ms = 1000.0 / fps if fps > 0 else 0.0
        lines.append(f"FPS: {fps:.0f}   ({ms:.2f} ms de 16,67)")
        # AUD-346 — el FPS instantáneo es un promedio de un segundo; los
        # cuantiles cuentan la estabilidad real. «60» puede ocultar 59
        # fotogramas de 16 ms y uno de 250: aquí se ve el troyano.
        if estadisticas:
            q = estadisticas
            lines.append(
                "P50 {p50:.2f} | P95 {p95:.2f} | P99 {p99:.2f} | "
                "peor {peor:.2f} ms".format(**q))
        lines.append(f"Objetos vivos: {len(gc.get_objects())}")
        # AUD-754 — diagnóstico de presentación nativa (F9)
        if self._display_diag:
            try:
                from src.engine.core import display as _display
                pipe = _display.describe_pipeline()
                for k, v in pipe.items():
                    lines.append(f"{k}: {v}")
            except Exception:
                lines.append("Display diag: error")
        # AUD-806 — Visual Forensics (F8) — cadena completa si hay estado
        if self._forensics:
            try:
                from src.engine.render import visual_forensics as _vf
                # Si App inyectó estado, úsalo; si no, recolectar mínimo (dummy)
                st = self._forensics_state
                if st is None:
                    st = _vf.collect_forensics()
                for fl in _vf.format_forensics(st):
                    lines.append(fl)
                # Distribución de píxeles para escala actual
                try:
                    dw, dh = st.get("DRAWABLE", (1280, 720))  # type: ignore[union-attr]
                    iw, ih = st.get("INTERNAL", (1280, 720))  # type: ignore[union-attr]
                    vp = st.get("VIEWPORT", (0, 0, 1280, 720))  # type: ignore[union-attr]
                    if isinstance(vp, tuple) and len(vp) == 4:
                        dist = _vf.pixel_distribution(int(iw[0]) if isinstance(iw, tuple) else int(iw), int(vp[2]))  # type: ignore[index]
                        lines.append(f"PIXEL DIST (src 0..7 -> disp width): {dist[:8]}")
                except Exception:
                    pass
            except Exception:
                lines.append("Forensics: error")
        for etiqueta, valor in (medidas or {}).items():
            lines.append(f"{etiqueta}: {valor}")
        lines.append(
            f"Árbol: {TREE_LEVELS[self._tree_level]}  |  [F11] cerrar  "
            "[F12] rotar  [F9] display diag  [F8] forensics  [F10] fullscreen",
        )
        lines.append("")

        # Event queue snapshot
        try:
            bus = self._event_bus
            snap = bus.queue_snapshot if bus is not None else []
            lines.append(f"Event Queue: {len(snap)} pending")
            for evt_name, evt_data in snap[:5]:
                lines.append(f"  {evt_name}: {evt_data}")
        except (RuntimeError, AttributeError) as e:
            logger.warning("debug_overlay: event bus snapshot failed: %s", e)
            lines.append("Event Bus: N/A")

        lines.append("")
        lines.append("Module Tree:")

        # Module tree based on level
        tree_items: list[str] = []
        if self._tree_level == 0:
            tree_items = [
                "engine/",
                "  core/",
                "    app.py",
                "    clock.py",
                "    event_bus.py",
                "    settings.py",
                "    game_context.py",
                "  input/",
                "    input_manager.py",
                "    action_map.py",
                "  scenes/",
                "    base_scene.py",
                "    scene_manager.py",
                "  utils/",
                "    asset_loader.py",
                "    math_utils.py",
            ]
        elif self._tree_level == 1:
            tree_items = [
                "framework/",
                "  entities/",
                "    entity_factory.py",
                "    entity.py",
                "    boss_base.py",
                "  processing/",
                "    filter_tools.py",
                "    vision_tools.py",
                "    pattern_recognition_tools.py",
                "    curve_tools.py",
                "  scenes/",
                "    stage_scene.py",
                "  stage/",
                "    camera.py",
            ]
        elif self._tree_level == 2:
            tree_items = [
                "student_templates/",
                "  stage_template/",
                "    stage_template.py",
                "  boss_template/",
                "    boss_template.py",
                "tests/",
                "  test_engine_core.py",
                "  test_demo_scenes.py",
                "  test_filter_tools.py",
                "  test_vision_tools.py",
                "  test_pattern_recognition_tools.py",
            ]

        lines.extend(tree_items)

        for idx, line in enumerate(lines):
            cached = self._line_cache.get(idx)
            if cached is None or cached[0] != line:
                txt = self._font.render(line, True, (80, 200, 255))
                self._line_cache[idx] = (line, txt)
            else:
                txt = cached[1]
            surface.blit(txt, (4, y))
            y += 10

        # AUD-754 — grid de depuración de presentación (solo con F9)
        if self._display_diag:
            try:
                pygame.draw.rect(surface, (0, 255, 255), surface.get_rect(), 1)
                cx, cy = settings.INTERNAL_WIDTH // 2, settings.INTERNAL_HEIGHT // 2
                pygame.draw.line(surface, (255, 255, 0), (cx - 10, cy), (cx + 10, cy), 1)
                pygame.draw.line(surface, (255, 255, 0), (cx, cy - 10), (cx, cy + 10), 1)
                safe = pygame.Rect(32, 32, settings.INTERNAL_WIDTH - 64, settings.INTERNAL_HEIGHT - 64)
                pygame.draw.rect(surface, (255, 0, 255), safe, 1)
                if medidas and "CAMERA" in medidas:
                    pass
                self._ensure_font()
                tag = self._font.render("DEBUG GRID: VIEWPORT | SAFE AREA | CENTER", True, (0, 255, 255))
                surface.blit(tag, (settings.INTERNAL_WIDTH - tag.get_width() - 4, 4))
            except Exception:
                pass
        # AUD-806 — forensics grid + ground + player highlight (solo con F8)
        if self._forensics:
            try:
                from src.engine.render import visual_forensics as _vf2
                st2 = self._forensics_state if self._forensics_state is not None else _vf2.collect_forensics()
                # Reusar la lógica de dibujo forense pero sin duplicar texto
                # (el texto ya está en lines); aquí sólo los marcos guía extra
                # Ground line y player rect
                cam = st2.get("CAMERA", (0.0, 0.0))
                gy = st2.get("GROUND_Y", 608)
                if isinstance(gy, int) and isinstance(cam, tuple) and len(cam) == 2:
                    sy = int(gy - cam[1])  # type: ignore[index]
                    if 0 <= sy < settings.INTERNAL_HEIGHT:
                        pygame.draw.line(surface, (255, 255, 255), (0, sy), (settings.INTERNAL_WIDTH, sy), 1)
                ps = st2.get("PLAYER_SCREEN", (0.0, 0.0))
                pr = st2.get("PLAYER_RECT", (0, 0, 40, 64))
                if isinstance(ps, tuple) and len(ps) == 2 and isinstance(pr, tuple) and len(pr) == 4:
                    r = pygame.Rect(int(ps[0]), int(ps[1]), int(pr[2]), int(pr[3]))  # type: ignore[index]
                    if -100 < r.x < 1380 and -100 < r.y < 820:
                        pygame.draw.rect(surface, (0, 255, 0), r, 1)
                        pygame.draw.circle(surface, (255, 0, 0), (int(r.centerx), int(r.bottom)), 3, 1)
                # Etiqueta forense
                self._ensure_font()
                tag2 = self._font.render("FORENSICS: WORLD->CAMERA->SCREEN->INTERNAL->VIEWPORT->DISPLAY", True, (0, 255, 200))
                surface.blit(tag2, (8, 8))
            except Exception:
                pass

        if y < settings.INTERNAL_HEIGHT - 20:
            surface.blit(self._hint_surf, (4, settings.INTERNAL_HEIGHT - 14))
