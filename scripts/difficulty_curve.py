"""
difficulty_curve.py — la curva de dificultad, medida en vez de opinada.

AUD-151. Por qué hacía falta
=============================
El juego tiene quince escenarios de catorce autores distintos, y nadie los ha
jugado seguidos. La pregunta «¿está bien ordenado?» se venía respondiendo por
intuición, y la intuición del que escribió un nivel no sirve para juzgar ese
nivel: quien lo diseñó sabe dónde están las cosas.

Esto no dice si un nivel es *divertido*. Dice cuánto **exige**, con cinco
números que se pueden contar sin jugar:

* **enemigos por pantalla** — la presión de combate;
* **peligros por pantalla** — pinchos, láseres, fosos;
* **huecos exigentes** — saltos cerca del límite de lo posible, medidos contra
  la envolvente de salto real del jugador (`level_metrics`);
* **tramo sin checkpoint** — cuánto se pierde al morir, que es lo que decide
  si un error frustra o no;
* **densidad de mecánicas** — cuántos sistemas distintos hay que entender.

Y los combina en un índice de 0 a 100. **El índice no es una nota**: un 70 no
es peor que un 30. Lo único que importa es que la serie **suba**, y que no lo
haga a saltos.

Uso::

    python scripts/difficulty_curve.py             # tabla en consola
    python scripts/difficulty_curve.py --md        # markdown para el informe
    python scripts/difficulty_curve.py --ci        # falla si hay un salto brusco

Qué es un salto brusco
-----------------------
Que un nivel exija **más del doble** que el anterior. Ahí es donde un jugador
deja el juego: no en el nivel difícil, sino en el que se vuelve difícil de
golpe sin haber enseñado nada nuevo.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

# AUD-177: imprime `→` y la consola de Windows usa cp1252, que no lo tiene.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

#: El orden en que el jugador los encuentra. Sale del registro de escenarios,
#: no de ordenar por nombre: `hall` y `lobby_datacenter` son intermedios y
#: `stage_mecanicas` es un laboratorio, no una parada del recorrido.
ORDEN: tuple[str, ...] = (
    "stage0",
    "stage1_1", "stage1_2_la_soda", "stage1_3_las_aulas",
    "boss_venado",
    "stage2_1_oficinas", "stage2_2",
    "boss_rey",
    "stage3_1_la_entrada_de_piedra", "stage3_3_el_patio",
    "stage4_1",
    "boss_paburu",
)

#: Escenarios que existen y **no** están en la curva, con su motivo.
FUERA_DE_LA_CURVA: dict[str, str] = {
    "hall": "vestíbulo sin combate",
    "lobby_datacenter": "zona de tránsito",
    "stage_mecanicas": "laboratorio del profesor, no una parada del juego",
    "stage3_4_boss_gavilan": "el jefe no existe (ver 17_BOSS_SPEC §0)",
}

#: Una pantalla son 800 px. Medir «por pantalla» y no en absoluto es lo que
#: permite comparar un nivel de 100 baldosas con uno de 220: lo que cansa es
#: la densidad, no el total.
ANCHO_PANTALLA = 800.0


@dataclass
class Medida:
    stage_id: str
    ancho_px: float
    enemigos: int
    peligros: int
    huecos_exigentes: int
    tramo_sin_checkpoint: float
    mecanicas: int

    @property
    def pantallas(self) -> float:
        return max(1.0, self.ancho_px / ANCHO_PANTALLA)

    @property
    def enemigos_por_pantalla(self) -> float:
        return self.enemigos / self.pantallas

    @property
    def peligros_por_pantalla(self) -> float:
        return self.peligros / self.pantallas

    @property
    def indice(self) -> float:
        """0–100. Cada término está acotado para que ninguno domine.

        Los pesos no salen de un ajuste: salen de qué mata más al jugador.
        El combate y los peligros pesan lo mismo (30 cada uno); los saltos
        exigentes menos (20) porque se reintentan sin coste; el castigo por
        morir lejos de un checkpoint, 15; y la variedad de mecánicas 5, porque
        entender un sistema nuevo cuesta una vez, no todo el nivel.
        """
        combate = min(1.0, self.enemigos_por_pantalla / 4.0) * 30.0
        peligro = min(1.0, self.peligros_por_pantalla / 3.0) * 30.0
        saltos = min(1.0, self.huecos_exigentes / 6.0) * 20.0
        castigo = min(1.0, self.tramo_sin_checkpoint / 2400.0) * 15.0
        variedad = min(1.0, self.mecanicas / 8.0) * 5.0
        return round(combate + peligro + saltos + castigo + variedad, 1)


def _importar_paquete_del_escenario(stage_id: str) -> None:
    """Importa `src.stages.<id>` si existe, para que registre sus tipos."""
    import importlib

    # El registro del tipo vive en la ESCENA, no en la clase del jefe: es
    # `boss_rey_scene.py` quien llama a `StageLoader.register_entity`. Importar
    # sólo el módulo del jefe carga la clase y no registra nada, que es por lo
    # que los dos mapas de jefe fallaban al medirlos.
    for modulo in (f"src.stages.{stage_id}.{stage_id}_scene",
                   f"src.stages.{stage_id}.{stage_id}",
                   f"src.stages.{stage_id}"):
        try:
            importlib.import_module(modulo)
        except ImportError:
            continue


def medir(stage_id: str) -> Medida | None:
    import pygame

    from src.engine.core import settings
    from src.framework.entities import entity_factory
    from src.framework.stage import level_metrics
    from src.framework.stage.stage_loader import StageLoader

    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    entity_factory.ensure_registered()

    ruta = settings.ASSETS_DIR / "maps" / stage_id / f"{stage_id}.tmx"
    if not ruta.exists():
        return None
    # Los jefes registran su propio tipo desde su paquete, y el cargador sólo
    # lo intenta cuando el mapa ya falló. Importarlos aquí evita que medir un
    # mapa de jefe muera con «tipo desconocido» — el mismo detalle que AUD-106
    # tuvo que arreglar en el validador y el calificador.
    _importar_paquete_del_escenario(stage_id)
    try:
        stage = StageLoader.load(ruta)
    except Exception as exc:      # un mapa roto no debe parar la medición
        print(f"  · {stage_id}: no se pudo cargar ({type(exc).__name__})",
              file=sys.stderr)
        return None

    informe = level_metrics.analyse_geometry(stage.collision_rects)
    # `analyse_checkpoints` quiere el spawn y la salida, no sólo los puntos:
    # el tramo que importa es también el primero —del inicio al primer
    # checkpoint— y el último —del último a la meta—.
    tramos = level_metrics.analyse_checkpoints(
        list(stage.checkpoints or []),
        stage.spawn_point,
        stage.next_trigger,
    )
    peor_tramo = max(tramos) if tramos else float(stage.map_pixel_size[0])

    peligros = len(stage.hazard_zones) + len(stage.death_pits)
    mecanicas = len({type(c).__name__
                     for grupo in stage.componentes for c in grupo})

    return Medida(
        stage_id=stage_id,
        ancho_px=float(stage.map_pixel_size[0]),
        enemigos=len(stage.entity_list),
        peligros=peligros,
        huecos_exigentes=len(getattr(informe, "demanding_gaps", []) or []),
        tramo_sin_checkpoint=float(peor_tramo),
        mecanicas=mecanicas,
    )


def _saltos_bruscos(medidas: list[Medida]) -> list[tuple[str, str, float, float]]:
    """Dónde la exigencia más que se dobla de un nivel al siguiente."""
    bruscos = []
    for anterior, actual in pairwise(medidas):
        # Los jefes se saltan en la comparación: un jefe DEBE ser un pico.
        # Compararlo con el nivel anterior sólo produce ruido.
        if "boss" in actual.stage_id:
            continue
        if anterior.indice > 5.0 and actual.indice > anterior.indice * 2.0:
            bruscos.append((anterior.stage_id, actual.stage_id,
                            anterior.indice, actual.indice))
    return bruscos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--md", action="store_true", help="salida markdown")
    parser.add_argument("--ci", action="store_true",
                        help="devuelve 1 si hay un salto brusco")
    args = parser.parse_args()

    medidas = [m for m in (medir(s) for s in ORDEN) if m is not None]
    if not medidas:
        print("no se pudo medir ningún escenario", file=sys.stderr)
        return 2

    if args.md:
        print("| # | Escenario | Pantallas | Enem./pant. | Pelig./pant. | "
              "Saltos exigentes | Sin checkpoint | Mecánicas | Índice |")
        print("|---|---|---|---|---|---|---|---|---|")
        for i, m in enumerate(medidas, 1):
            print(f"| {i} | `{m.stage_id}` | {m.pantallas:.1f} | "
                  f"{m.enemigos_por_pantalla:.1f} | {m.peligros_por_pantalla:.1f} | "
                  f"{m.huecos_exigentes} | {m.tramo_sin_checkpoint:.0f} px | "
                  f"{m.mecanicas} | **{m.indice}** |")
    else:
        print(f"{'escenario':32s} {'pant.':>6s} {'enem/p':>7s} {'pel/p':>6s} "
              f"{'saltos':>7s} {'índice':>7s}")
        for m in medidas:
            print(f"{m.stage_id:32s} {m.pantallas:6.1f} "
                  f"{m.enemigos_por_pantalla:7.1f} {m.peligros_por_pantalla:6.1f} "
                  f"{m.huecos_exigentes:7d} {m.indice:7.1f}")

    bruscos = _saltos_bruscos(medidas)
    if bruscos:
        print("\nSaltos bruscos (más del doble de exigencia):")
        for antes, despues, ia, ib in bruscos:
            print(f"  · {antes} ({ia}) → {despues} ({ib})")
    else:
        print("\nSin saltos bruscos: la curva sube sin escalones.")

    return 1 if (args.ci and bruscos) else 0


if __name__ == "__main__":
    raise SystemExit(main())
