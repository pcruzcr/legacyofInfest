"""
Module: test_tips
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: N/A
Description: Pruebas del cartelito de controles que sale al empezar.

Ejecutar toda la suite con:
   python -m pytest src/stages/stage1_1/tests/ -v
"""
from __future__ import annotations

import pytest

from src.engine.ui.message_box import MessageBox
from src.stages.stage1_1.stage1_1 import Stage1_1_LaEntrada


def test_hay_tips_de_inicio() -> None:
    assert len(Stage1_1_LaEntrada.tips_de_inicio()) >= 1


def test_cada_tip_entra_en_una_sola_linea() -> None:
    """`MessageBox._wrap_text` parte por CARACTERES, no por palabras
    (message_box.py:99-118): corta en el carácter 58 exacto aunque quede a
    mitad de palabra. Y si el texto no cabe en 3 líneas, descarta el resto
    en silencio.

    La forma limpia de evitar las dos cosas es que cada tip quepa en una
    sola línea. Así nunca se parte una palabra ni se pierde el final.
    """
    for texto, _duracion in Stage1_1_LaEntrada.tips_de_inicio():
        assert len(texto) <= 58, (
            f"{len(texto)} caracteres, se partiria a mitad de palabra: {texto!r}"
        )
        assert len(MessageBox._wrap_text(texto)) == 1


def test_ningun_tip_pierde_texto_al_mostrarse() -> None:
    """Comprobación de respaldo con el propio partidor del motor: los
    caracteres visibles deben ser los mismos que los del original."""
    for texto, _duracion in Stage1_1_LaEntrada.tips_de_inicio():
        mostrado = "".join(MessageBox._wrap_text(texto))
        assert mostrado.replace(" ", "") == texto.replace(" ", "")


def test_las_duraciones_son_razonables() -> None:
    """Ni tan corto que no dé tiempo a leer, ni tan largo que estorbe."""
    for texto, duracion in Stage1_1_LaEntrada.tips_de_inicio():
        assert 2.0 <= duracion <= 12.0, f"duracion rara en {texto!r}"


def test_los_tips_explican_la_guardia() -> None:
    """Es el control nuevo: si no se explica, nadie lo va a descubrir."""
    todo = " ".join(t for t, _ in Stage1_1_LaEntrada.tips_de_inicio()).upper()

    assert "CTRL" in todo or "Q" in todo
    assert "DEFEN" in todo or "GUARDIA" in todo


def test_los_tips_avisan_que_la_guardia_inmoviliza() -> None:
    """Sin ese aviso, el jugador va a creer que se trabó."""
    todo = " ".join(t for t, _ in Stage1_1_LaEntrada.tips_de_inicio()).upper()

    assert "MOVER" in todo or "MUEV" in todo or "QUIETO" in todo


# ── Los tips esperan 4 s desde el comienzo ──────────────────────────

def test_el_retardo_de_los_tips_es_de_cuatro_segundos() -> None:
    """El banner "1-1 LA ENTRADA" ocupa el centro de la pantalla durante
    2,9 s (screen_banner.py:18-20) y la caja de mensajes se dibuja en la
    misma zona. Con 4 s de espera el banner ya salió y queda margen."""
    assert Stage1_1_LaEntrada.RETARDO_TIPS == pytest.approx(4.0)


def test_antes_del_retardo_no_se_muestran_tips() -> None:
    assert not Stage1_1_LaEntrada.puede_mostrar_tips(0.0)
    assert not Stage1_1_LaEntrada.puede_mostrar_tips(2.5)
    assert not Stage1_1_LaEntrada.puede_mostrar_tips(3.99)


def test_al_cumplirse_el_retardo_se_muestran() -> None:
    assert Stage1_1_LaEntrada.puede_mostrar_tips(4.0)
    assert Stage1_1_LaEntrada.puede_mostrar_tips(9.0)
