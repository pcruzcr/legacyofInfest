"""Módulo: test_generar_sfx_eco_bosses
Sistema: tests
Descripción: candados de formato, determinismo (SIN RNG), alcance
    (``sfx_bosses_venado_*`` menos el bramido) y política de "jamás
    sobrescribir" del generador de variantes ``*_con_eco.wav``
    (Tarea 6, revisión de spec 2026-08-25, punto 4)."""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pytest

from src.stages.boss_venado.tools.generar_sfx_eco_bosses import (
    DIRECTORIO_SFX,
    PICO_OBJETIVO,
    generar_faltantes,
    generar_variante_con_eco,
)


def _escribir_wav_de_prueba(ruta: Path, frecuencia: int = 22050,
                            duracion_s: float = 0.05) -> None:
    """Un .wav mono 16-bit PCM corto y determinista (tono puro), solo para
    ejercitar el generador -- no pretende sonar a nada del jefe real."""
    n = int(frecuencia * duracion_s)
    t = np.linspace(0.0, duracion_s, n, endpoint=False)
    señal = (np.sin(2.0 * np.pi * 440.0 * t) * 0.6 * 32767.0).astype("<i2")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(frecuencia)
        w.writeframes(señal.tobytes())


def test_genera_un_wav_valido_mono_16bit_con_cola_mas_larga(tmp_path: Path):
    origen = tmp_path / "sfx_bosses_venado_prueba.wav"
    destino = tmp_path / "sfx_bosses_venado_prueba_con_eco.wav"
    _escribir_wav_de_prueba(origen)
    generar_variante_con_eco(origen, destino)

    assert destino.exists()
    with wave.open(str(origen), "rb") as w_origen, wave.open(str(destino), "rb") as w_destino:
        assert w_destino.getnchannels() == w_origen.getnchannels() == 1
        assert w_destino.getsampwidth() == w_origen.getsampwidth() == 2
        assert w_destino.getframerate() == w_origen.getframerate()
        # la cola del eco (3 repeticiones, la última a 3x el retardo) alarga
        # la señal -- si no fuera más larga, el eco se estaría cortando de
        # golpe en vez de apagarse.
        assert w_destino.getnframes() > w_origen.getnframes()


def test_no_recorta_el_pico_normaliza_al_objetivo(tmp_path: Path):
    """Con 3 repeticiones sumadas sobre una señal ya casi a tope (0.6 de
    escala), sin normalizar el pico se saldría del rango de int16 -- el
    candado real es que NINGUNA muestra llega a +-32768 y que el pico SÍ se
    acerca al objetivo (no un normalizador que devuelve silencio)."""
    origen = tmp_path / "sfx_bosses_venado_prueba.wav"
    destino = tmp_path / "sfx_bosses_venado_prueba_con_eco.wav"
    _escribir_wav_de_prueba(origen)
    generar_variante_con_eco(origen, destino)

    with wave.open(str(destino), "rb") as w:
        crudo = w.readframes(w.getnframes())
    muestras = np.frombuffer(crudo, dtype="<i2").astype(np.int64)
    pico = int(np.max(np.abs(muestras)))
    assert pico <= 32767
    objetivo = int(PICO_OBJETIVO * 32767)
    assert objetivo - 200 <= pico <= objetivo, (
        f"pico={pico} lejos del objetivo esperado {objetivo}")


def test_es_determinista_byte_a_byte(tmp_path: Path):
    """DSP determinista, sin generador aleatorio: la MISMA entrada produce
    SIEMPRE la misma salida, byte a byte -- ver el docstring del módulo del
    generador (a diferencia de generar_sfx_bramido.py, que sintetiza ruido
    con semilla fija; aquí no hace falta ninguna semilla porque no hay
    ningún sorteo)."""
    origen = tmp_path / "sfx_bosses_venado_prueba.wav"
    _escribir_wav_de_prueba(origen)
    destino_a = tmp_path / "a_con_eco.wav"
    destino_b = tmp_path / "b_con_eco.wav"
    generar_variante_con_eco(origen, destino_a)
    generar_variante_con_eco(origen, destino_b)
    assert destino_a.read_bytes() == destino_b.read_bytes()


def test_generar_faltantes_respeta_el_alcance_y_las_exclusiones(tmp_path: Path):
    """`generar_faltantes` solo debe tocar `sfx_bosses_venado_*.wav` --
    nunca otros bosses, nunca el bramido (suena fuera de la arena), y nunca
    intenta generarle un eco a un `_con_eco.wav` que ya exista."""
    _escribir_wav_de_prueba(tmp_path / "sfx_bosses_venado_stomp.wav")
    _escribir_wav_de_prueba(tmp_path / "sfx_bosses_venado_bramido_lejano.wav")
    _escribir_wav_de_prueba(tmp_path / "sfx_bosses_rey_spit.wav")   # otro boss -- NUNCA tocar
    _escribir_wav_de_prueba(tmp_path / "sfx_bosses_venado_charge_con_eco.wav")   # ya es un eco

    escritos = generar_faltantes(tmp_path)

    assert [p.name for p in escritos] == ["sfx_bosses_venado_stomp_con_eco.wav"]
    assert not (tmp_path / "sfx_bosses_venado_bramido_lejano_con_eco.wav").exists()
    assert not (tmp_path / "sfx_bosses_rey_spit_con_eco.wav").exists()
    # el "eco de un eco" jamas se genera:
    assert not (tmp_path / "sfx_bosses_venado_charge_con_eco_con_eco.wav").exists()


def test_generar_faltantes_jamas_sobrescribe_un_destino_existente(tmp_path: Path):
    """Política de la zona de creación permitida (CLAUDE.md): archivos
    NUEVOS, jamás sobrescribir uno existente -- se simula un destino ya
    presente con contenido centinela (ni siquiera un .wav válido) y se
    confirma que `generar_faltantes` lo deja intacto en vez de
    regenerarlo."""
    _escribir_wav_de_prueba(tmp_path / "sfx_bosses_venado_vine.wav")
    destino = tmp_path / "sfx_bosses_venado_vine_con_eco.wav"
    destino.write_bytes(b"CENTINELA-NO-TOCAR")

    escritos = generar_faltantes(tmp_path)

    assert escritos == []
    assert destino.read_bytes() == b"CENTINELA-NO-TOCAR"


def test_generar_faltantes_es_idempotente_en_una_segunda_corrida(tmp_path: Path):
    _escribir_wav_de_prueba(tmp_path / "sfx_bosses_venado_stomp.wav")
    primera = generar_faltantes(tmp_path)
    assert len(primera) == 1
    segunda = generar_faltantes(tmp_path)
    assert segunda == []


def test_rechaza_un_origen_que_no_es_mono_16bit(tmp_path: Path):
    """El guardián de formato: preferible un error explícito a mezclar mal
    un estéreo o un ancho de muestra distinto en silencio."""
    origen = tmp_path / "sfx_bosses_venado_estereo.wav"
    n = 100
    señal = np.zeros((n, 2), dtype="<i2")
    with wave.open(str(origen), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(señal.tobytes())
    with pytest.raises(ValueError, match="mono"):
        generar_variante_con_eco(origen, tmp_path / "destino.wav")


def test_rechaza_un_origen_que_no_es_16bit(tmp_path: Path):
    """Simétrico al de estéreo de arriba, pero para el ancho de muestra:
    un .wav de 8 bits (sampwidth=1) también debe rechazarse con un error
    explícito -- ``np.frombuffer(..., dtype="<i2")`` sobre bytes de 8 bits
    interpretaría la mitad de las muestras mal (cada par de bytes de 8 bits
    se leería como una sola muestra de 16 bits), así que dejarlo pasar en
    silencio produciría un .wav con eco pero con ruido/velocidad
    incorrectos, no un error visible."""
    origen = tmp_path / "sfx_bosses_venado_8bit.wav"
    n = 100
    señal = (np.full(n, 128, dtype=np.uint8))   # PCM de 8 bits es sin signo, centrado en 128
    with wave.open(str(origen), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(22050)
        w.writeframes(señal.tobytes())
    with pytest.raises(ValueError, match="16 bits"):
        generar_variante_con_eco(origen, tmp_path / "destino.wav")


def test_directorio_por_defecto_apunta_a_la_zona_de_creacion_permitida():
    assert DIRECTORIO_SFX.parts[-3:] == ("assets", "sfx", "bosses")
