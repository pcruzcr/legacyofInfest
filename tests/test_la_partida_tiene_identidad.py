"""AUD-442 — una partida guardada no sabía de quién era.

`SaveData` tenía diecisiete campos de progreso —dónde estás, cuánta vida,
qué llevas— y ninguno de identidad. Para la pantalla de selección eso deja
cinco filas indistinguibles: sin nombre, sin personaje y sin cuánto se ha
jugado, elegir partida es elegir por la marca de tiempo.

Sin subir `SAVE_VERSION`
------------------------
Los tres campos son puramente aditivos y con valores por defecto sanos: una
partida escrita antes de que existieran se lee sin nombre, y la pantalla la
muestra como «Partida N». No hay comportamiento que dependa de la versión,
así que un escalón nuevo en la escalera de migración no haría nada — y un
escalón que no hace nada es ruido en el sitio donde luego hay que leer para
entender por qué una partida vieja no carga.

`play_time` se acumula, no se recalcula: el `SaveManager` marca cuándo empezó
la sesión de esta partida y suma lo transcurrido al guardar. Recalcularlo
desde la marca de tiempo del fichero contaría también las horas con el juego
cerrado.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from src.engine.core.save_data import SaveData
from src.engine.core.save_manager import SaveManager


@pytest.fixture
def gestor(tmp_path, monkeypatch):
    monkeypatch.setattr(SaveManager, "SAVES_DIR", tmp_path)
    return SaveManager()


class TestLosCamposDeIdentidad:
    def test_una_partida_nueva_los_trae_vacios(self) -> None:
        data = SaveData()
        assert data.profile_name == ""
        assert data.character == "paburu"
        assert data.play_time == 0.0

    def test_el_nombre_viaja_al_disco_y_vuelve(self, gestor) -> None:
        gestor.save(1, SaveData(slot_id=1, profile_name="Pablo",
                                character="paburu"))
        leida = gestor.load(1)
        assert leida is not None
        assert leida.profile_name == "Pablo"
        assert leida.character == "paburu"

    def test_una_partida_anterior_se_lee_sin_nombre(self) -> None:
        """Lo que hace innecesario subir la versión: por defecto, vacío."""
        vieja = SaveData.from_dict({"version": 3, "stage_id": "stage1_1"})
        assert vieja.profile_name == ""
        assert vieja.play_time == 0.0

    def test_el_nombre_no_puede_ser_infinito(self) -> None:
        """La pantalla tiene un ancho y el fichero, un lector humano.

        Sin tope, un nombre pegado desde el portapapeles desborda la fila y
        empuja la marca de tiempo fuera de la pantalla.
        """
        data = SaveData(profile_name="x" * 500)
        assert len(data.profile_name) <= 24

    def test_el_nombre_se_limpia_de_espacios(self) -> None:
        assert SaveData(profile_name="  Ana  ").profile_name == "Ana"


class TestElTiempoJugado:
    def test_se_acumula_entre_sesiones(self, gestor, monkeypatch) -> None:
        reloj = {"t": 1000.0}
        monkeypatch.setattr(
            "src.engine.core.save_manager._ahora", lambda: reloj["t"])

        gestor.ranura_activa = 1            # empieza a contar
        reloj["t"] += 90.0
        data = SaveData(slot_id=1)
        gestor.anotar_tiempo_jugado(data)
        assert data.play_time == pytest.approx(90.0)

        # Segunda sesión sobre la misma partida: suma, no reemplaza.
        reloj["t"] += 30.0
        gestor.anotar_tiempo_jugado(data)
        assert data.play_time == pytest.approx(120.0)

    def test_no_cuenta_el_tiempo_con_el_juego_cerrado(self, gestor, monkeypatch) -> None:
        """El control: si contara desde la marca del fichero, una partida
        abandonada un mes tendría un mes jugado."""
        reloj = {"t": 0.0}
        monkeypatch.setattr(
            "src.engine.core.save_manager._ahora", lambda: reloj["t"])

        gestor.ranura_activa = 1
        reloj["t"] += 10.0
        data = SaveData(slot_id=1)
        gestor.anotar_tiempo_jugado(data)

        # Se cambia de partida y vuelve mucho después: el hueco no cuenta.
        gestor.ranura_activa = 2
        reloj["t"] += 100_000.0
        gestor.ranura_activa = 1
        reloj["t"] += 5.0
        gestor.anotar_tiempo_jugado(data)

        assert data.play_time == pytest.approx(15.0)

    def test_sin_ranura_activa_no_se_inventa_tiempo(self, gestor) -> None:
        data = SaveData(slot_id=1, play_time=42.0)
        gestor.anotar_tiempo_jugado(data)
        assert data.play_time == pytest.approx(42.0)
