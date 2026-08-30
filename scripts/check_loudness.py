"""
AUD-644 — check_loudness.py: verifica loudness de assets de audio.

Sin pyloudnorm instalado, el script hace skip con aviso.
Con pyloudnorm, mide cada fichero .wav y reporta desviaciones del target -23 LUFS.

Uso:
    python scripts/check_loudness.py
    python scripts/check_loudness.py --target=-16   # streaming
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Mide loudness de assets de audio")
    parser.add_argument("--target", type=float, default=-23.0,
                        help="Target LUFS (default: -23 EBU R128)")
    args = parser.parse_args()

    try:
        import pyloudnorm as pyln
    except ImportError:
        print("[SKIP] pyloudnorm no está instalado.")
        print("  Instalar con: pip install pyloudnorm")
        return 0

    import soundfile as sf

    carpetas = [RAIZ / "assets" / "music", RAIZ / "assets" / "sfx"]
    ficheros = []
    for carpeta in carpetas:
        if carpeta.exists():
            ficheros.extend(carpeta.rglob("*.wav"))

    if not ficheros:
        print("No se encontraron ficheros .wav en assets/music ni assets/sfx")
        return 0

    print(f"Midiendo {len(ficheros)} ficheros contra target {args.target} LUFS\n")

    problemas = 0
    meter = pyln.Meter(44100)  # sample rate por defecto

    for fichero in sorted(ficheros):
        rel = fichero.relative_to(RAIZ)
        try:
            data, sr = sf.read(str(fichero))
            if data.ndim > 1:
                data = data.mean(axis=1)
            meter = pyln.Meter(sr)
            lufs = meter.integrated_loudness(data)
            desviacion = lufs - args.target
            estado = "OK" if abs(desviacion) < 3.0 else "FUERA"
            print(f"  [{estado}] {rel}: {lufs:.1f} LUFS ({desviacion:+.1f})")
            if abs(desviacion) >= 3.0:
                problemas += 1
        except Exception as e:
            print(f"  [ERROR] {rel}: {e}")
            problemas += 1

    print(f"\n{problemas} fichero(s) fuera del rango ±3 LUFS del target")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())