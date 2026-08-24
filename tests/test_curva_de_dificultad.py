"""
La curva de dificultad — AUD-151.

Quince escenarios de catorce autores, y nadie los ha jugado seguidos. La
pregunta «¿está bien ordenado?» se venía respondiendo por intuición, y la
intuición del que escribió un nivel no sirve para juzgar ese nivel.

Lo que estas pruebas defienden
-------------------------------
1. **Que la medida sea comparable.** Todo va por pantalla: un nivel de dos
   pantallas y uno de cinco no se comparan en totales.
2. **Que el índice no se desboque.** Cada término está acotado, así que un
   nivel con doscientos enemigos no saca 400.
3. **Que los jefes no cuenten como escalón.** Un jefe *debe* ser un pico.
4. **Que el orden exista de verdad.** Un `ORDEN` con un escenario borrado
   convierte la herramienta en un adorno que siempre pasa.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import difficulty_curve as curva  # noqa: E402


def _medida(**kw) -> curva.Medida:
    base = {
        "stage_id": "prueba", "ancho_px": 1600.0, "enemigos": 0,
        "peligros": 0, "huecos_exigentes": 0,
        "tramo_sin_checkpoint": 0.0, "mecanicas": 0,
    }
    base.update(kw)
    return curva.Medida(**base)


class TestLaMedidaEsComparable:
    def test_todo_va_por_pantalla(self) -> None:
        """Dos niveles con los mismos enemigos y distinto tamaño no exigen lo
        mismo: lo que cansa es la densidad, no el total."""
        corto = _medida(ancho_px=800.0, enemigos=4)
        largo = _medida(ancho_px=4000.0, enemigos=4)
        assert corto.enemigos_por_pantalla > largo.enemigos_por_pantalla

    def test_un_mapa_diminuto_no_divide_entre_cero(self) -> None:
        assert _medida(ancho_px=10.0, enemigos=1).enemigos_por_pantalla == 1.0

    def test_un_nivel_vacio_saca_cero(self) -> None:
        assert _medida().indice == 0.0


class TestElIndiceEstaAcotado:
    def test_doscientos_enemigos_no_sacan_cuatrocientos(self) -> None:
        assert _medida(enemigos=200).indice <= 100.0

    def test_cada_termino_tiene_techo(self) -> None:
        """Sin techo, el combate solo se comería la escala y los otros cuatro
        números dejarían de decir nada."""
        todo = _medida(enemigos=999, peligros=999, huecos_exigentes=999,
                       tramo_sin_checkpoint=99999.0, mecanicas=999)
        assert todo.indice == 100.0

    def test_mas_enemigos_es_mas_indice(self) -> None:
        assert _medida(enemigos=8).indice > _medida(enemigos=2).indice

    def test_morir_lejos_del_checkpoint_cuenta(self) -> None:
        lejos = _medida(enemigos=2, tramo_sin_checkpoint=3000.0)
        cerca = _medida(enemigos=2, tramo_sin_checkpoint=200.0)
        assert lejos.indice > cerca.indice


class TestLosEscalones:
    def test_doblar_la_exigencia_es_un_escalon(self) -> None:
        serie = [_medida(stage_id="a", enemigos=2),
                 _medida(stage_id="b", enemigos=16)]
        assert curva._saltos_bruscos(serie)

    def test_subir_poco_a_poco_no_lo_es(self) -> None:
        serie = [_medida(stage_id="a", enemigos=4),
                 _medida(stage_id="b", enemigos=5),
                 _medida(stage_id="c", enemigos=6)]
        assert curva._saltos_bruscos(serie) == []

    def test_un_jefe_no_cuenta_como_escalon(self) -> None:
        """Un jefe DEBE ser un pico. Compararlo con el nivel anterior sólo
        produce ruido que hace que nadie mire el informe."""
        serie = [_medida(stage_id="stage1", enemigos=2),
                 _medida(stage_id="boss_venado", enemigos=40)]
        assert curva._saltos_bruscos(serie) == []

    def test_desde_un_nivel_casi_vacio_no_se_avisa(self) -> None:
        """Doblar 0,5 es doblar nada. Sin este umbral, cualquier nivel de
        descanso produciría un aviso y el informe se leería una vez."""
        serie = [_medida(stage_id="a"), _medida(stage_id="b", enemigos=3)]
        assert curva._saltos_bruscos(serie) == []


class TestElOrdenEsReal:
    @pytest.mark.parametrize("stage_id", curva.ORDEN)
    def test_cada_escenario_del_orden_tiene_su_mapa(self, stage_id) -> None:
        from src.engine.core import settings

        ruta = settings.ASSETS_DIR / "maps" / stage_id / f"{stage_id}.tmx"
        assert ruta.exists(), (
            f"«{stage_id}» está en la curva y su mapa no existe: la "
            f"herramienta lo saltaría en silencio"
        )

    def test_lo_que_queda_fuera_esta_justificado(self) -> None:
        """Un escenario fuera de la curva sin motivo escrito es un olvido
        disfrazado de decisión."""
        from src.engine.core import settings

        carpetas = {p.name for p in (settings.ASSETS_DIR / "maps").iterdir()
                    if p.is_dir()}
        sin_clasificar = carpetas - set(curva.ORDEN) - set(curva.FUERA_DE_LA_CURVA)
        assert sin_clasificar == set(), (
            f"escenarios que no están ni en la curva ni justificados fuera: "
            f"{sorted(sin_clasificar)}"
        )


class TestLaMedidaDeVerdad:
    """Que las cuentas funcionen no significa que un mapa real se pueda medir."""

    def test_stage0_se_puede_medir(self) -> None:
        medida = curva.medir("stage0")
        assert medida is not None, "el escenario de referencia no se pudo medir"
        assert medida.enemigos > 0
        assert medida.indice > 0

    def test_un_escenario_que_no_existe_devuelve_nada(self) -> None:
        assert curva.medir("stage_que_no_existe") is None

    def test_los_mapas_de_jefe_tambien_se_miden(self) -> None:
        """AUD-151 — los dos jefes registraban su tipo dentro de un método de
        su escena, así que cualquier herramienta que abriera el mapa sin
        construir la escena moría con «tipo desconocido»."""
        assert curva.medir("boss_rey") is not None
        assert curva.medir("boss_paburu") is not None
