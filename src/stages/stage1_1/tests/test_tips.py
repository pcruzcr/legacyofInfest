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

from src.engine.core import user_settings
from src.engine.core.event_bus import EventBus
from src.engine.core.user_settings import ESCALAS_DE_TEXTO
from src.engine.ui.message_box import MessageBox
from src.engine.ui.text_panel import dividir_en_lineas
from src.engine.ui.theme import Theme, font
from src.stages.stage1_1.stage1_1 import Stage1_1_LaEntrada


def test_hay_tips_de_inicio() -> None:
    assert len(Stage1_1_LaEntrada.tips_de_inicio()) >= 1


@pytest.fixture
def caja():
    """Un `MessageBox` de verdad, para preguntarle SU ancho util.

    AUD-611 cambio el ajuste de linea de contar caracteres a medir pixeles, y
    de paso borro `MessageBox._wrap_text`, que es lo que llamaban estas dos
    pruebas. Rehacer aqui la cuenta del ancho
    —`INTERNAL_WIDTH - 2*(_MARGEN + _PAD_X + _FLECHA_HUECO)`— seria guardar una
    copia del calculo del motor que se quedaria vieja en cuanto alguien retoque
    el tema. Se le pregunta al propio cuadro.
    """
    c = MessageBox(EventBus())
    yield c
    c.destroy()


@pytest.fixture
def fuente_del_peor_caso(monkeypatch):
    """La fuente del cuadro a la MAYOR escala de accesibilidad admitida.

    Por que el peor caso y no el tamano de diseno
    ---------------------------------------------
    Medido: a escala 1.0x el cuadro tiene 692 px utiles y el tip mas largo
    ocupa 240. Ahi cabria un texto de unos 150 caracteres, o sea que afirmar
    «entra en una linea» no comprobaria nada — y una prueba que no puede
    fallar no es una prueba.

    A 2.0x —la mayor de `ESCALAS_DE_TEXTO`— ese mismo tip pasa a 558 px y el
    techo real baja a unos 64 caracteres. Ese si es un limite que un tip nuevo
    puede cruzar sin querer, y es justo el del jugador que necesita el texto
    grande: el que menos margen tiene y el que peor lo pasa si el aviso se
    corta.
    """
    escala = ESCALAS_DE_TEXTO[-1]
    original = user_settings.preferencia
    monkeypatch.setattr(
        user_settings, "preferencia",
        lambda clave, defecto=None: (
            escala if clave == "text_scale" else original(clave, defecto)
        ),
    )
    return font(Theme.FONT_SMALL)


def test_cada_tip_entra_en_una_sola_linea(caja, fuente_del_peor_caso) -> None:
    """Cada tip cabe en UNA linea, incluso con el texto al doble.

    El peligro viejo —cortar a mitad de palabra al caracter 58— lo resolvio el
    motor: `dividir_en_lineas` parte por palabras. El que queda es
    `_recorta_a_max_lineas`, que si el texto pide mas de `_MAX_LINES` lo trunca
    y le pega una elipsis. Un tip de una linea nunca se acerca a ese limite.

    Y hay una razon visual ademas de la tecnica: el cuadro crece hacia arriba,
    y un tip de dos lineas tapa mas pantalla justo mientras el jugador esta
    aprendiendo a moverse.
    """
    for texto, _duracion in Stage1_1_LaEntrada.tips_de_inicio():
        lineas = dividir_en_lineas(texto, fuente_del_peor_caso, caja._ancho_util())
        assert len(lineas) == 1, (
            f"a escala {ESCALAS_DE_TEXTO[-1]}x se parte en {len(lineas)} lineas: "
            f"{texto!r} -> {lineas}"
        )


def test_ningun_tip_pierde_texto_al_mostrarse(caja, fuente_del_peor_caso) -> None:
    """Respaldo con el partidor real del motor: ni se pierde un caracter, ni
    aparece la elipsis con la que `_recorta_a_max_lineas` avisa de que trunco."""
    for texto, _duracion in Stage1_1_LaEntrada.tips_de_inicio():
        mostrado = " ".join(
            dividir_en_lineas(texto, fuente_del_peor_caso, caja._ancho_util())
        )
        assert "…" not in mostrado, f"el motor truncaria este tip: {texto!r}"
        assert mostrado.replace(" ", "") == texto.replace(" ", "")


def test_las_duraciones_son_razonables() -> None:
    """Ni tan corto que no dé tiempo a leer, ni tan largo que estorbe."""
    for texto, duracion in Stage1_1_LaEntrada.tips_de_inicio():
        assert 2.0 <= duracion <= 12.0, f"duracion rara en {texto!r}"


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
