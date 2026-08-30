"""Módulo: test_generar_sfx_bramido
Sistema: tests
Descripción: sintetizador procedural del bramido lejano del venado."""
from __future__ import annotations

import wave
from pathlib import Path

from src.stages.boss_venado.tools.generar_sfx_bramido import RUTA_SALIDA, generar


def test_generar_escribe_un_wav_valido(tmp_path: Path):
    destino = tmp_path / "bramido.wav"
    generar(destino)
    assert destino.exists()
    with wave.open(str(destino), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getframerate() == 44100
        assert w.getsampwidth() == 2
        duracion = w.getnframes() / w.getframerate()
        assert 1.2 <= duracion <= 2.5


def test_ruta_de_salida_esta_en_la_zona_de_creacion_permitida():
    # CORRECCIÓN frente al Paso 1 tal como está escrito en el plan: el
    # borrador comparaba ``RUTA_SALIDA.parts[-3:]`` (que incluye el propio
    # nombre de archivo, el último elemento de .parts) contra
    # ("assets", "sfx", "bosses") -- eso nunca puede ser cierto para la ruta
    # de un ARCHIVO. Lo que en realidad hay que verificar es que el
    # DIRECTORIO padre son esos tres componentes -- de ahí ``.parent``.
    assert RUTA_SALIDA.parent.parts[-3:] == ("assets", "sfx", "bosses")
    assert RUTA_SALIDA.name == "sfx_bosses_venado_bramido_lejano.wav"
