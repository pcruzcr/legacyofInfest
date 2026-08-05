"""AUD-280 — cinco muertes a la vez sonaban cinco veces.

Qué se fija aquí
----------------
La lógica de `ControlDeVoces`, que es donde está la decisión, y el cableado
mínimo de `SoundBank`, que es donde suele perderse. El reparto sigue al de
`mixer_buses`: la decisión es pura y se prueba sin altavoces; lo que habla con
pygame se comprueba con un doble.

El caso que motivó todo esto es el primero: **cinco enemigos que mueren en el
mismo fotograma**. Antes producía cinco `Sound.play()` en fase — saturación y
cinco canales de los ocho gastados. Debe producir una voz y cuatro refuerzos.
"""
from __future__ import annotations

import pytest

from src.engine.audio.polifonia import (
    MAX_VOCES_POR_SONIDO,
    REFUERZO_MAXIMO,
    VENTANA_DE_REFUERZO,
    ControlDeVoces,
)


@pytest.fixture
def control() -> ControlDeVoces:
    return ControlDeVoces()


class TestElCasoQueLoMotivo:
    def test_cinco_muertes_en_el_mismo_fotograma_dan_una_voz(self, control) -> None:
        acciones = [control.pedir("enemy_die", 0.0, 0.5).accion for _ in range(5)]
        assert acciones[0] == "suena"
        assert acciones[1:] == ["refuerza"] * 4, (
            f"cinco muertes simultáneas produjeron {acciones}: se vuelven a "
            "sumar cinco copias en fase del mismo fichero"
        )

    def test_y_la_voz_que_suena_sube(self, control) -> None:
        control.pedir("enemy_die", 0.0, 0.5)
        ganancias = [control.pedir("enemy_die", 0.0, 0.5).ganancia for _ in range(4)]
        assert ganancias == sorted(ganancias), "el refuerzo tiene que acumularse"
        assert ganancias[-1] > 1.0, (
            "callar las repeticiones sin subir la que queda pierde la "
            "sensación de multitud"
        )

    def test_el_refuerzo_tiene_techo(self, control) -> None:
        """Sin techo, una lluvia de proyectiles dejaría un solo sonido audible."""
        control.pedir("hit", 0.0, 0.5)
        for _ in range(50):
            ultima = control.pedir("hit", 0.0, 0.5)
        assert ultima.ganancia == pytest.approx(REFUERZO_MAXIMO)


class TestPasadaLaVentana:
    def test_dos_eventos_separados_suenan_los_dos(self, control) -> None:
        assert control.pedir("hit", 0.0, 0.5).accion == "suena"
        assert control.pedir("hit", VENTANA_DE_REFUERZO * 2, 0.5).accion == "suena"

    def test_el_tope_de_voces_se_respeta(self, control) -> None:
        """Tres vivas es densidad; veinte es un bus saturado."""
        t = 0.0
        for _ in range(MAX_VOCES_POR_SONIDO):
            t += VENTANA_DE_REFUERZO * 2
            assert control.pedir("hit", t, 5.0).accion == "suena"
        t += VENTANA_DE_REFUERZO * 2
        assert control.pedir("hit", t, 5.0).accion == "calla"

    def test_las_voces_caducan_solas(self, control) -> None:
        """Sin caducidad haría falta que alguien avisara al acabar el canal, y
        ese aviso es el cabo suelto que silencia un sonido para siempre."""
        t = 0.0
        for _ in range(MAX_VOCES_POR_SONIDO):
            t += VENTANA_DE_REFUERZO * 2
            control.pedir("hit", t, 0.2)
        assert control.pedir("hit", t + 10.0, 0.2).accion == "suena"
        assert control.voces_vivas("hit", t + 10.0) == 1

    def test_sonidos_distintos_no_compiten(self, control) -> None:
        assert control.pedir("a", 0.0, 0.5).accion == "suena"
        assert control.pedir("b", 0.0, 0.5).accion == "suena"
        assert control.pedir("c", 0.0, 0.5).accion == "suena"
        assert control.pedir("d", 0.0, 0.5).accion == "suena"

    def test_una_duracion_desconocida_cuenta_como_una_ventana(self, control) -> None:
        """Sin mezclador `get_length` no está: la voz no puede caducar en el
        acto o el tope no contaría nada."""
        control.pedir("hit", 0.0, 0.0)
        assert control.voces_vivas("hit", VENTANA_DE_REFUERZO / 2) == 1


class TestElCableadoDeSoundBank:
    """Que la lógica sea correcta no basta: hay que ver que `play` la usa."""

    @pytest.fixture
    def banco(self):
        from src.engine.audio.sound_bank import SoundBank

        return SoundBank()

    @staticmethod
    def _sonido_falso(reproducciones: list):
        class _Canal:
            def __init__(self) -> None:
                self.volumen: tuple = ()

            def set_volume(self, *args) -> None:
                self.volumen = args

        class _Sonido:
            def __init__(self) -> None:
                self.canal = _Canal()

            def get_length(self) -> float:
                return 0.5

            def set_volume(self, v) -> None:
                pass

            def play(self, loops=0):
                reproducciones.append(loops)
                return self.canal

        return _Sonido()

    def test_cinco_llamadas_seguidas_reproducen_una_vez(self, banco) -> None:
        reproducciones: list = []
        banco._sounds["enemy_die"] = self._sonido_falso(reproducciones)
        for _ in range(5):
            banco.play("enemy_die")
        assert reproducciones == [0], (
            f"se reprodujo {len(reproducciones)} veces: la polifonía no está "
            "puesta en SoundBank.play"
        )

    def test_y_el_canal_sube_de_volumen(self, banco) -> None:
        sonido = self._sonido_falso([])
        banco._sounds["enemy_die"] = sonido
        banco.play("enemy_die", volume=0.5)
        banco.play("enemy_die", volume=0.5)
        assert sonido.canal.volumen, "no se reforzó la voz que ya sonaba"
        assert sonido.canal.volumen[0] > 0.5

    def test_el_refuerzo_conserva_el_pan(self, banco) -> None:
        """Reforzar con `set_volume(v)` a secas centraría un sonido que estaba
        a la izquierda: un fallo que sólo se oye con auriculares."""
        sonido = self._sonido_falso([])
        banco._sounds["paso"] = sonido
        banco.play("paso", pan=(1.0, 0.0))
        banco.play("paso", pan=(1.0, 0.0))
        izq, der = sonido.canal.volumen
        assert der == 0.0, "el refuerzo devolvió el sonido al centro"
        assert izq > 0.0

    def test_un_bucle_no_gasta_voz(self, banco) -> None:
        """Un `loops=-1` es un zumbido sostenido, no un evento: contarlo dejaría
        el tope ocupado para siempre."""
        reproducciones: list = []
        banco._sounds["zumbido"] = self._sonido_falso(reproducciones)
        for _ in range(4):
            banco.play("zumbido", loops=-1)
        assert reproducciones == [-1, -1, -1, -1]

    def test_clear_devuelve_el_banco_a_cero(self, banco) -> None:
        reproducciones: list = []
        banco._sounds["x"] = self._sonido_falso(reproducciones)
        banco.play("x")
        banco.clear()
        banco._sounds["x"] = self._sonido_falso(reproducciones)
        banco.play("x")
        assert len(reproducciones) == 2, (
            "un contador que sobrevive al banco silencia los primeros disparos "
            "del sonido recién cargado"
        )
