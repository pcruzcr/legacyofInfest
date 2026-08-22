"""AUD-586 — F3 de `93_AUDITORIA_ESTRATEGICA_Y_FODA.md` §6: `grade_stage`
reporta «no hay ruta al NextTrigger» como **error** en los mapas que por
diseño no declaran `NextTrigger` — las cuatro arenas de jefe y
`stage_cenital` — y además les cobra los 12 puntos de `design_completable`.

La herramienta ya sabía decirlo («si el escenario es una arena donde la
salida se abre al derrotar a un jefe, esta métrica no aplica») pero lo
decía **después** de suspender el nivel. Aplicar la rúbrica equivocada y
suspender por ella es peor que no medir — el mismo principio de AUD-192 y
AUD-472, tercera vez con la misma causa.

Lo que cambia: sin `NextTrigger` declarado la métrica no aplica — puntos
completos en la categoría, aviso explícito de que hay que comprobarlo por
otra vía, y cero errores. El dato crudo (`exit_reachable`) se conserva tal
cual, igual que en AUD-192.

AUD-595 — `hall` salió de esta lista: su NextTrigger no era un fantasma.
El hook de la escena era un `pass`, pero quien completa el nivel es
`ProgressionSystem.check_next_trigger` al tocar el rectángulo, y `hall` es
la ranura lineal 3-2 de STAGE_ORDER — sin salida, la campaña queda
bloqueada ahí (lo gritan `test_guardado_y_cadena` y
`test_los_next_trigger`). El trigger volvió al TMX tal estaba.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


def _calificar(ruta: str) -> dict:
    # Entorno completo + los tres valores obligatorios del repo: con un
    # entorno mínimo (`PATH=""`, sin SYSTEMROOT/TEMP) la importación de los
    # paquetes de jefe que hace `ensure_registered()` se cae y el mapa no
    # llega ni a cargarse — ruido del arnés, no del mapa.
    entorno = dict(os.environ)
    entorno.update({
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "PYGAME_HIDE_SUPPORT_PROMPT": "1",
    })
    salida = subprocess.run(
        [sys.executable, "scripts/grade_stage.py", ruta, "--json"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
        env=entorno, check=False,
    ).stdout
    datos = json.loads(salida[salida.index("["):salida.rindex("]") + 1])
    return datos[0]


SIN_SALIDA = [
    "assets/maps/boss_venado/boss_venado.tmx",
    "assets/maps/boss_rey/boss_rey.tmx",
    "assets/maps/boss_paburu/boss_paburu.tmx",
    "assets/maps/stage3_4_boss_gavilan/stage3_4_boss_gavilan.tmx",
    "assets/maps/stage_cenital/stage_cenital.tmx",
]


@pytest.fixture(scope="module", params=SIN_SALIDA)
def informe(request) -> dict:
    return _calificar(request.param)


class TestSinNextTriggerLaMetricaNoAplica:
    def test_no_pierde_los_puntos_de_completable(self, informe) -> None:
        categoria = informe["categories"]["design_completable"]
        assert categoria["score"] == categoria["max"], (
            f"un mapa sin NextTrigger declarado salió con "
            f"{categoria['score']}/{categoria['max']}: {categoria['msg']}")

    def test_ningun_error_de_ruta(self, informe) -> None:
        errores = " ".join(informe["errors"]).lower()
        assert "nexttrigger" not in errores and "ruta" not in errores, (
            f"se reportó como error lo que es un mapa sin salida por "
            f"diseño: {informe['errors']}")

    def test_avisa_que_la_metrica_no_aplica(self, informe) -> None:
        avisos = " ".join(informe["warnings"]).lower()
        assert "no aplica" in avisos, (
            f"no se avisa de que la métrica de ruta no aplica: "
            f"{informe['warnings']}")

    def test_el_dato_crudo_se_conserva(self, informe) -> None:
        """Igual que AUD-192: la nota cambia, el dato no se maquilla."""
        assert informe["design"]["exit_reachable"] is False
