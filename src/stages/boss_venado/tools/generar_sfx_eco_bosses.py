"""Módulo: generar_sfx_eco_bosses
Sistema: tools (generación de assets)
Descripción: genera las variantes ``*_con_eco.wav`` de los SFX propios del
    Venado (Tarea 6, revisión de spec 2026-08-25, punto 4 -- "el espacio
    suena distinto"). ``AudioManager._nombre_con_eco`` (audio_manager.py:
    186-191) enruta CUALQUIER SFX a ``"<nombre>_con_eco"`` cuando
    ``activar_eco(True)`` está encendido (Tarea 6:
    ``boss_venado_scene.py::_actualizar_silencio_y_shake_de_arena``, activo
    SOLO dentro del gazebo/arena) *si esa variante existe en el
    SoundBank* -- si no existe, toca el sonido seco de siempre, silenciosa
    y correctamente (fallback, no error). Hasta esta tarea NINGÚN SFX del
    jefe tenía variante ``_con_eco``, así que el eco de la arena nunca
    afectaba a los sonidos dominantes del combate (STOMP/CHARGE/VINE,
    ``sonido.py:107-109``): solo cambiaba la textura de fondo del
    mezclador, sin efecto audible en lo que el jugador más escucha.

    Alcance: SOLO ``sfx_bosses_venado_*.wav`` (los SFX propios de este
    jefe -- jamás los de otros bosses del curso, `sfx_bosses_rey_*`/
    `sfx_bosses_gavilan_*`/`sfx_bosses_paburu_*`, que no son zona editable
    de este proyecto), EXCEPTO el bramido lejano
    (``sfx_bosses_venado_bramido_lejano.wav``, generado por
    ``generar_sfx_bramido.py``): ese sonido se dispara con el jugador
    TODAVÍA en el Acto 3 (``presencias_venado.SOMBRA_X0``=2200,
    ``SOMBRA_X1``=2480 == ``ARENA_X0``), es decir SIEMPRE fuera de la
    arena, así que jamás iba a sonar con el eco activo -- generarle una
    variante sería un archivo muerto.

    DSP: eco por retardo (delay), NO síntesis con ruido -- a diferencia de
    ``generar_sfx_bramido.py`` (que sintetiza un sonido nuevo desde cero y
    sí necesita una textura de ruido, con semilla fija para
    reproducibilidad), aquí se TRANSFORMA un .wav ya existente con una
    suma de copias retardadas y decrecientes de la señal original -- un
    algoritmo puramente determinista que no necesita ningún generador
    aleatorio: las mismas muestras de entrada producen SIEMPRE el mismo
    .wav de salida, byte a byte (ver
    ``test_generar_sfx_eco_bosses.py::test_es_determinista_byte_a_byte``).
    Wav mono 16-bit PCM vía el módulo stdlib ``wave`` + ``numpy`` para la
    mezcla vectorizada, sin pygame (headless, mismo patrón que
    ``generar_sfx_bramido.py``). Los tres SFX del venado son mono
    (verificado con el módulo `wave` antes de escribir este generador), así
    que el generador solo soporta mono -- lanza ``ValueError`` explícito si
    algún candidato futuro no lo fuera, en vez de mezclar canales
    silenciosamente mal.

    ``SoundBank.load_all()`` (sound_bank.py:34-46) registra CUALQUIER .wav
    bajo assets/sfx/ por su STEM de archivo -- el sufijo ``_con_eco`` de la
    ruta de salida ES literalmente el sufijo que
    ``AudioManager._nombre_con_eco`` (``variante = f"{name}_con_eco"``)
    construye para buscar la variante; no hace falta ningún registro ni
    manifiesto aparte."""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

_AQUI = Path(__file__).resolve()
DIRECTORIO_SFX = _AQUI.parents[4] / "assets" / "sfx" / "bosses"

#: Solo los SFX propios de este jefe -- ver el docstring del módulo.
PREFIJO = "sfx_bosses_venado_"

#: Stems (sin extensión) que nunca reciben variante con eco, aunque
#: coincidan con el prefijo -- ver el docstring del módulo (el bramido
#: suena siempre fuera de la arena).
EXCLUIDOS: frozenset[str] = frozenset({"sfx_bosses_venado_bramido_lejano"})

#: Retardo de la primera repetición, en segundos -- spec: "delay ~90ms".
RETARDO_S = 0.09

#: (múltiplo del retardo, ganancia) de cada repetición -- "2-3 repeticiones
#: decrecientes": tres ecos a 90/180/270 ms, cada uno más débil que el
#: anterior (~×0.6 por paso), como el gazebo devolviendo el sonido cada vez
#: más apagado.
REPETICIONES: tuple[tuple[int, float], ...] = ((1, 0.50), (2, 0.30), (3, 0.16))

#: Pico objetivo tras normalizar, como fracción del rango de int16 -- deja
#: un margen de cabeza (mismo criterio que generar_sfx_bramido.py, que usa
#: 0.85) para que la suma de las repeticiones jamás recorte (clipping).
PICO_OBJETIVO = 0.92


def _aplicar_eco_mono(muestras: np.ndarray, frecuencia: int) -> np.ndarray:
    """Suma la señal original con copias retardadas y decrecientes de sí
    misma (``REPETICIONES``). Función PURA: sin E/S, sin generador
    aleatorio -- ``muestras`` (float64) y ``frecuencia`` determinan la
    salida por completo. Devuelve la señal SIN normalizar (la cola es más
    larga que la entrada, para que el eco no se corte de golpe)."""
    retardo = round(frecuencia * RETARDO_S)
    cola = retardo * REPETICIONES[-1][0]
    salida = np.zeros(muestras.shape[0] + cola, dtype=np.float64)
    salida[:muestras.shape[0]] += muestras
    for multiplo, ganancia in REPETICIONES:
        desplazamiento = retardo * multiplo
        salida[desplazamiento:desplazamiento + muestras.shape[0]] += muestras * ganancia
    return salida


def _normalizar_a_int16(señal: np.ndarray) -> np.ndarray:
    """Escala ``señal`` (float64) para que su pico caiga exactamente en
    ``PICO_OBJETIVO`` del rango de int16 -- así la mezcla de las
    repeticiones NUNCA recorta, sin importar cuántos ecos se sumen ni cuán
    fuerte sea la señal original. Silencio (pico 0) se queda en silencio."""
    pico = float(np.max(np.abs(señal))) if señal.size else 0.0
    if pico > 0.0:
        señal = señal / pico * PICO_OBJETIVO * 32767.0
    return np.clip(señal, -32768.0, 32767.0).astype("<i2")


def generar_variante_con_eco(origen: Path, destino: Path) -> None:
    """Lee ``origen`` (.wav mono PCM 16-bit), le aplica el eco de
    ``_aplicar_eco_mono`` y escribe ``destino`` -- SIEMPRE un archivo
    NUEVO, nunca sobrescribe (la política de "jamás sobrescribir" la
    aplica el llamante, ``generar_faltantes``, comprobando
    ``destino.exists()`` ANTES de llamar aquí; esta función en sí escribe
    incondicionalmente, igual que ``generar_sfx_bramido.generar``)."""
    with wave.open(str(origen), "rb") as w:
        canales = w.getnchannels()
        ancho = w.getsampwidth()
        frecuencia = w.getframerate()
        crudo = w.readframes(w.getnframes())
    if ancho != 2:
        raise ValueError(
            f"{origen.name}: se esperaba PCM de 16 bits, sampwidth={ancho}")
    if canales != 1:
        raise ValueError(
            f"{origen.name}: se esperaba mono (1 canal), canales={canales}")
    muestras = np.frombuffer(crudo, dtype="<i2").astype(np.float64)
    salida = _aplicar_eco_mono(muestras, frecuencia)
    pcm = _normalizar_a_int16(salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(frecuencia)
        w.writeframes(pcm.tobytes())


def _candidatos(directorio: Path = DIRECTORIO_SFX) -> list[Path]:
    """Cada ``sfx_bosses_venado_*.wav`` de ``directorio``, EXCEPTO
    ``EXCLUIDOS`` y cualquier ``*_con_eco.wav`` ya generado -- este segundo
    filtro es lo que hace segura una segunda corrida (sin él, una corrida
    posterior intentaría generarle un eco a un eco)."""
    return sorted(
        p for p in directorio.glob(f"{PREFIJO}*.wav")
        if p.stem not in EXCLUIDOS and not p.stem.endswith("_con_eco")
    )


def generar_faltantes(directorio: Path = DIRECTORIO_SFX) -> list[Path]:
    """Genera la variante ``_con_eco.wav`` de cada candidato que todavía no
    la tenga. JAMÁS sobrescribe un archivo existente (política de la zona
    de creación permitida, CLAUDE.md): si el destino ya existe, se salta
    sin tocarlo. Devuelve la lista de archivos NUEVOS escritos en esta
    corrida (vacía si ya estaba todo generado -- idempotente)."""
    escritos: list[Path] = []
    for origen in _candidatos(directorio):
        destino = origen.with_name(f"{origen.stem}_con_eco.wav")
        if destino.exists():
            continue
        generar_variante_con_eco(origen, destino)
        escritos.append(destino)
    return escritos


def main() -> None:
    escritos = generar_faltantes()
    if not escritos:
        print("generar_sfx_eco_bosses: nada que generar (ya existían todas las variantes)")
        return
    for ruta in escritos:
        print(f"eco -> {ruta}")


if __name__ == "__main__":
    main()
