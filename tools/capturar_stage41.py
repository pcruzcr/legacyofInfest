#!/usr/bin/env python3
"""AUD-814 — Recorrido de certificación del Stage 4.1 con evidencia visual.

Ejecuta el walkthrough INTRO → F1 → … → F6 → PABURU sin saltarse fases,
fuerza los estados que el azar temporiza (rayo, sombra, luna, silencio) y
guarda las 26 capturas que pide el pliego. También mide ms/fotograma por
fase (performance) e imprime el manifiesto.

Uso:
    python tools/capturar_stage41.py [--salida DIR]

Las capturas son evidencia temporal (STEP 50): van fuera del repo.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

# AUD-839 — el manifiesto y los mensajes imprimen texto en español con acentos
# que la consola cp1252 de Windows no puede codificar: sin esto el proceso
# moría con UnicodeEncodeError a mitad del recorrido.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from src.stages.stage4_1 import trazado

SALIDA_POR_DEFECTO = (
    "C:/Users/pcruz/AppData/Local/Temp/opencode/evidencia41")


def _construir():
    import pygame as _pg
    _pg.init()
    _pg.font.init()
    if _pg.display.get_surface() is None:
        _pg.display.set_mode((1280, 720))
    try:
        _pg.mixer.init(frequency=22050)
    except Exception:
        pass
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    entity_factory.ensure_registered()
    from src.stages.stage4_1.stage4_1 import Stage4_1
    ctx = GameContext(input_manager=InputManager(),
                      audio_manager=AudioManager(), scene_manager=None,
                      event_bus=EventBus(), clock=None,
                      save_manager=SaveManager())
    ctx.scene_manager = SceneManager(ctx)
    escena = Stage4_1(ctx)
    ctx.scene_manager.push(escena)
    return ctx, escena


class Recorrido:
    def __init__(self, salida: str) -> None:
        self.ctx, self.escena = _construir()
        self.salida = salida
        os.makedirs(salida, exist_ok=True)
        self.manifiesto: list[str] = []
        self.tiempos: dict[str, list] = {}

    def avanzar(self, n: int, saltar_escenas: bool = True,
                cerrar_dialogos: bool = True) -> None:
        for _ in range(n):
            self.escena.update(1 / 60)
            self.ctx.event_bus.dispatch()
            if (saltar_escenas and self.escena._cutscenes is not None
                    and self.escena._cutscenes.bloquea):
                self.escena._cutscenes.saltar()
                self.ctx.event_bus.dispatch()
            if cerrar_dialogos and self.escena._dialogue.active:
                self.escena._dialogue.end_dialogue()
                self.ctx.event_bus.dispatch()

    def poner(self, columna: int) -> None:
        self.escena._player.position.x = columna * trazado.TS
        self.escena._player.rect.x = columna * trazado.TS
        self.escena._player.position.y = 480
        self.escena._player.rect.y = 480
        self.escena._camera.snap_to_target()

    def foto(self, nombre: str, nota: str = "",
             con_mensaje: bool = False) -> None:
        # Arnés: vacía la cola de MessageBox y oculta el cartel en curso
        # para que la toma muestre el mundo. Sólo 08/16/26 conservan su
        # mensaje: ahí el texto ES la evidencia del feedback.
        caja = getattr(self.escena, "_msg_box", None)
        if caja is not None and hasattr(caja, "_queue"):
            caja._queue.clear()
            if not con_mensaje and hasattr(caja, "hide"):
                try:
                    caja.hide()
                except Exception:
                    pass
        # Arnés: el tutorial contextual del motor ("Ataque corto...") puede
        # dispararse en recorridos largos; la toma muestra el mundo.
        tuto = getattr(self.escena, "_tutorial", None)
        if tuto is not None and hasattr(tuto, "_active"):
            tuto._active = False
        surf = pygame.display.get_surface()
        self.escena.draw(surf)
        ruta = os.path.join(self.salida, nombre + ".png")
        pygame.image.save(surf, ruta)
        fase = self.escena._fase_actual.numero
        linea = f"{nombre}: fase={fase} {nota}".rstrip()
        self.manifiesto.append(linea)
        print(linea, flush=True)

    def medir(self, nombre: str, columna: int, cuadros: int = 300) -> None:
        self.poner(columna)
        self.avanzar(30)
        tiempos = []
        for _ in range(cuadros):
            t0 = time.perf_counter()
            self.escena.update(1 / 60)
            self.ctx.event_bus.dispatch()
            tiempos.append((time.perf_counter() - t0) * 1000)
        tiempos.sort()
        n = len(tiempos)
        self.tiempos[nombre] = tiempos
        print(
            f"perf {nombre}: media={sum(tiempos) / n:.2f}ms "
            f"p50={tiempos[n // 2]:.2f} "
            f"p95={tiempos[int(n * 0.95)]:.2f} "
            f"p99={tiempos[int(n * 0.99)]:.2f}",
            flush=True,
        )

    def dialogo_y_altar(self, col_d: int, arbol: str, col_a: int,
                        altar: str) -> None:
        self.poner(col_d)
        self.avanzar(8)
        assert arbol in self.escena._dialogo_visto, arbol
        self.escena._dialogue.end_dialogue()
        self.avanzar(3)
        self.poner(col_a)
        self.avanzar(5)
        self.escena._al_disparar(nombre=altar)
        self.ctx.event_bus.dispatch()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--salida", default=SALIDA_POR_DEFECTO)
    args = parser.parse_args()
    rec = Recorrido(args.salida)

    # 01 — intro en curso (sin saltar).
    rec.avanzar(40, saltar_escenas=False)
    rec.foto("01_intro", "cutscene inicial")
    rec.avanzar(10)

    # 02/03 — F1 a color + easter egg.
    rec.poner(60)
    rec.avanzar(600)
    rec.foto("02_fase1_cementerio_color", "F1 a color")
    rec.poner(trazado.COLUMNA_LAPIDA_CAMPANERO)
    rec.avanzar(30, cerrar_dialogos=False)
    rec.foto("03_fase1_easter_egg", "lapida del campanero")
    rec.escena._dialogue.end_dialogue()
    rec.avanzar(30)

    # 04 — transición con lluvia al borde F1/F2.
    rec.poner(156)
    rec.avanzar(300)
    rec.foto("04_transicion_lluvia", "borde F1-F2")

    # 05–08 — F2.
    rec.poner(200)
    rec.avanzar(400)
    rec.foto("05_fase2_venado", "B&N + lluvia")
    rec.poner(210)
    rec.avanzar(200)
    rec.foto("06_fase2_musgo", "musgo")
    rec.poner(260)
    rec.avanzar(200)
    rec.foto("07_fase2_barro", "lodo")
    rec.dialogo_y_altar(trazado.COLUMNA_DIALOGO_VENADO, "venado",
                        trazado.COLUMNA_ALTAR_VENADO, "altar_venado")
    rec.avanzar(60)
    rec.foto("08_fase2_espiritu", "ascension del Venado", con_mensaje=True)

    # 09–12 — F3.
    rec.dialogo_y_altar(trazado.COLUMNA_DIALOGO_SERPIENTE, "serpiente",
                        trazado.COLUMNA_ALTAR_SERPIENTE, "altar_serpiente")
    rec.poner(360)
    rec.avanzar(300)
    rec.foto("09_fase3_serpiente", "osamentas + tormenta")
    rec.poner(420)
    rec.avanzar(200)
    rec.foto("10_fase3_slopes", "loma alta")
    rec.poner(380)
    rec.avanzar(400)
    rec.foto("11_fase3_tormenta", "tormenta")
    rec.escena._proximo_rayo = 0.01
    rec.avanzar(2)
    rec.foto("12_fase3_rayo", "flash del rayo")

    # 13–16 — F4.
    rec.poner(500)
    rec.avanzar(300)
    rec.foto("13_fase4_halcon", "vintage ambar")
    rec.poner(540)
    rec.avanzar(300)
    rec.foto("14_fase4_bosque_muerto", "bosque talado")
    rec.escena._sombra = {"x": rec.escena._player.rect.centerx - 100.0,
                          "vx": 400.0, "t": 0.0}
    rec.avanzar(5)
    rec.foto("15_fase4_sombras", "sombra del Halcon")
    rec.poner(565)
    rec.avanzar(30)
    assert rec.escena._silencio_hecho
    rec.foto("16_fase4_silencio_shake", "silencio + shake", con_mensaje=True)
    rec.dialogo_y_altar(trazado.COLUMNA_DIALOGO_HALCON, "halcon",
                        trazado.COLUMNA_ALTAR_HALCON, "altar_halcon")

    # 17–20 — F5 (a mitad de fase: la imagen ya se estableció).
    rec.poner(720)
    rec.avanzar(400)
    rec.foto("17_fase5_planicie", "planicie nocturna")
    rec.escena._tiempo = rec.escena.PERIODO_DE_LA_LUNA * 0.25
    rec.avanzar(30)
    rec.foto("18_fase5_luna_visible", "luz maxima")
    rec.escena._tiempo = rec.escena.PERIODO_DE_LA_LUNA * 0.75
    rec.avanzar(30)
    rec.foto("19_fase5_luna_oculta", "luz minima")
    rec.escena._tiempo = rec.escena.PERIODO_DE_LA_LUNA * 0.25
    rec.poner(730)
    rec.avanzar(120)
    rec.foto("20_fase5_muertos", "muertos con luz")

    # 21–26 — F6 y final.
    rec.poner(810)
    rec.avanzar(400)
    rec.foto("21_fase6_camino", "camino verde")
    from src.engine.input.action_map import Action

    class _Mando:
        def __init__(self, base) -> None:
            self._base = base

        def is_action_held(self, action) -> bool:
            return action == Action.MOVE_RIGHT

        def __getattr__(self, nombre: str):
            return getattr(self._base, nombre)

    real = rec.ctx.input_manager
    rec.poner(825)
    rec.avanzar(5)
    rec.ctx.input_manager = _Mando(real)
    try:
        rec.avanzar(400)
    finally:
        rec.ctx.input_manager = real
    rec.foto("22_fase6_luces", f"luces encendidas: {rec.escena._luces_encendidas}")
    rec.foto("23_fase6_grietas", "grietas verdes")
    rec.avanzar(200)
    rec.foto("24_fase6_particulas", "niebla + esporas")
    rec.poner(936)
    rec.avanzar(200)
    rec.foto("25_fase6_paburu", "silueta de Paburu")
    rec.poner(950)
    rec.avanzar(200)
    rec.foto("26_final_despertar", "portal + mensaje final",
             con_mensaje=True)

    # AUD-815 — transiciones entre fases (clima vecino anticipado).
    for nombre, col, nota in (
            ("27_transicion_f2_f3", 315, "lluvia->tormenta"),
            ("28_transicion_f3_f4", 475, "tormenta->lluvia ambar"),
            ("29_transicion_f4_f5", 635, "lluvia->noche"),
            ("30_transicion_f5_f6", 795, "noche->niebla verde")):
        rec.poner(col)
        rec.avanzar(250)
        rec.foto(nombre, nota)

    # AUD-815 — incendio en orden + caza.
    rec.poner(480)
    rec.avanzar(60)
    for col in (495, 520, 545):
        rec.poner(col)
        rec.avanzar(60)
    rec.foto("31_fase4_incendio", "piras ardiendo, lluvia cesada")
    rec.poner(552)
    rec.avanzar(15)
    rec.escena._caza_x = rec.escena._player.rect.centerx - 120.0
    rec.avanzar(3)
    rec.foto("32_fase4_caza", "sombra persiguiendo")

    # AUD-815 — nubes tapando la luna.
    rec.escena._reloj_nube = 8.0
    rec.poner(720)
    rec.avanzar(120)
    rec.foto("33_fase5_nubes", "nube sobre la luna")

    # AUD-815 — antorchas en orden + templo.
    rec.poner(825)
    rec.avanzar(5)
    rec.ctx.input_manager = _Mando(real)
    try:
        rec.avanzar(500)
    finally:
        rec.ctx.input_manager = real
    rec.foto("34_fase6_antorchas", f"antorchas: {rec.escena._antorcha_encendidas}")
    rec.poner(945)
    rec.avanzar(900)
    rec.foto("35_templo_portal", f"paso templo: {rec.escena._paso_templo}", con_mensaje=True)

    # AUD-816 — validación del apoyo (caída desde arriba, posado real).
    for nombre, col in (("36_pies_plano", 60), ("37_pies_loma", 420),
                        ("38_pies_f2", 200), ("39_pies_f3", 340),
                        ("40_pies_f5", 700), ("41_pies_f6", 860)):
        rec.poner(col)
        rec.escena._player.position.y = 300
        rec.escena._player.rect.y = 300
        rec.avanzar(120)
        rec.foto(nombre, f"pies={rec.escena._player.rect.bottom} "
                         f"fase={rec.escena._fase_actual.numero}")

    # Performance en los puntos exigentes.
    for nombre, col in (("f3_tormenta", 380), ("f4_lluvia", 540),
                        ("f5_luna", 700), ("f6_niebla", 880),
                        ("despertar", 940)):
        rec.medir(nombre, col)

    assert rec.escena._liberados == [True, True, True]
    assert rec.escena._interactables.llavero.tiene(trazado.LLAVE_PABURU)
    print("RECORRIDO COMPLETO: 26 shots + perf", flush=True)


if __name__ == "__main__":
    main()
